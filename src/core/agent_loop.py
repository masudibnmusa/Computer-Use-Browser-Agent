"""observe -> decide -> resolve -> classify -> act -> verify -> (recover) -> repeat"""
from __future__ import annotations

import hashlib
import json
import logging

from ..browser.executor import Executor
from ..browser.waits import wait_for_settle
from ..config import Settings
from ..extraction.output_writer import write_results
from ..llm.llm_client import LLMError
from ..perception import dom_simplifier, page_diff, screenshotter, set_of_marks
from ..perception.element_registry import ElementRegistry
from ..safety import injection_guard
from ..safety.action_classifier import classify
from ..safety.approval_gate import ApprovalGate
from ..safety.credential_vault import CredentialVault
from ..utils.cost_tracker import CostTracker
from ..utils.trace_recorder import TraceRecorder
from .action_schema import Done, Extract, RequestHelp, action_args
from .planner import make_plan
from .recovery import Recovery
from .state import AgentState, Observation, StepRecord
from .stopping_criteria import StoppingCriteria

log = logging.getLogger(__name__)

# actions that are expected to visibly change the page
CHANGING = {"click", "click_at", "type_text", "select_option", "press_key", "goto"}


class AgentLoop:
    def __init__(self, settings: Settings, session, llm, cost: CostTracker,
                 vault: CredentialVault | None = None, gate: ApprovalGate | None = None):
        self.s = settings
        self.session = session
        self.llm = llm
        self.cost = cost
        self.vault = vault or CredentialVault()
        self.gate = gate or ApprovalGate(settings.approval_mode)
        self.registry = ElementRegistry(settings.max_elements)
        self.executor = Executor(session, self.registry, self.vault, settings)
        self.stopping = StoppingCriteria(settings)
        self.recovery = Recovery(session)

    # ---------------------------------------------------------------- observe
    def observe(self) -> Observation:
        self.session.page.wait_for_timeout(250)  # lets popup/new-tab events dispatch
        page = self.session.page
        wait_for_settle(page)
        elements = self.registry.refresh(page)
        shot = screenshotter.capture(page)
        if self.s.use_set_of_marks:
            shot = set_of_marks.annotate(shot, elements)
        elements_text = self.vault.redact(dom_simplifier.format_elements(elements))
        page_text = self.vault.redact(dom_simplifier.visible_text(page, self.s.page_text_chars))
        try:
            title = page.title()
        except Exception:
            title = ""
        return Observation(
            url=page.url,
            title=title,
            screenshot=shot,
            elements=elements,
            elements_text=elements_text,
            page_text=page_text,
            injection_flags=injection_guard.scan(page_text + "\n" + elements_text),
            signature=page_diff.make_signature(page.url, page_text, elements_text),
            truncated=self.registry.truncated,
        )

    # ----------------------------------------------------------------- verify
    def _verify(self, rec: StepRecord, prev: Observation, cur: Observation,
                state: AgentState) -> Observation:
        diff = page_diff.compare(prev, cur)
        rec.changed, rec.effect = diff.changed, diff.summary
        failed = (not rec.ok) or (rec.action in CHANGING and not diff.changed)
        if failed:
            state.consecutive_failures += 1
            hint, acted = self.recovery.advice(state, rec)
            state.recovery_hint = hint
            if acted:  # recovery touched the page, so the observation is stale
                return self.observe()
        else:
            state.consecutive_failures = 0
            state.recovery_hint = ""
        return cur

    # -------------------------------------------------------------------- run
    def run(self, task: str) -> AgentState:
        s = self.s
        state = AgentState(task=task)
        tracer = TraceRecorder(s.traces_dir, state.run_id, task)
        if s.use_planner:
            try:
                state.plan = make_plan(self.llm, task)
            except Exception as e:  # planning is optional
                log.warning("planner failed: %s", e)

        prev_obs: Observation | None = None
        pending: tuple[StepRecord, str] | None = None

        try:
            while True:
                obs = self.observe()
                state.current_url = obs.url

                if pending and prev_obs:
                    rec, shot = pending
                    obs = self._verify(rec, prev_obs, obs, state)
                    tracer.write_step(rec, shot)
                    pending = None

                reason = self.stopping.check(state, self.cost)
                if reason:
                    state.stop_reason = reason.value
                    state.final_summary = f"Stopped: {reason.value}"
                    break

                if s.loop_repeat_limit > 1 and \
                        self.stopping.repeat_count(state) == s.loop_repeat_limit - 1:
                    state.recovery_hint += " You are repeating the same action on the same page; try a different approach."

                step_no = len(state.steps) + 1
                shot_name = tracer.save_screenshot(step_no, obs.screenshot)

                # ------------------------------------------------ decide
                try:
                    action, reasoning = self.llm.decide(state, obs)
                except LLMError as e:
                    rec = StepRecord(step_no, obs.url, "invalid_action", {}, "", False, str(e))
                    state.steps.append(rec)
                    state.consecutive_failures += 1
                    state.recovery_hint = f"Your last output was invalid ({e}). Call exactly one valid tool."
                    tracer.write_step(rec, shot_name)
                    continue

                if action.progress_note:
                    state.progress_notes = action.progress_note
                args = action_args(action)
                rec = StepRecord(step_no, obs.url, action.tool_name, args, reasoning, True, "")
                state.steps.append(rec)
                sig = f"{obs.signature}|{action.tool_name}|{json.dumps(args, sort_keys=True, default=str)}"
                state.signatures.append(hashlib.sha1(sig.encode()).hexdigest()[:12])

                # ------------------------------------------- terminal actions
                if isinstance(action, Done):
                    state.finished, state.success = True, action.success
                    state.final_summary, state.final_result = action.summary, action.result
                    state.stop_reason = "done"
                    rec.message = action.summary
                    tracer.write_step(rec, shot_name)
                    break

                if isinstance(action, RequestHelp):
                    rec.message = f"asked human: {action.reason}"
                    if s.headless:
                        state.stop_reason = "needs_human"
                        state.final_summary = f"Needs human help: {action.reason}"
                        rec.ok = False
                        tracer.write_step(rec, shot_name)
                        break
                    print(f"\n[agent needs help] {action.reason}")
                    try:
                        input("Resolve it in the browser window, then press Enter... ")
                    except EOFError:
                        pass
                    pending, prev_obs = (rec, shot_name), obs
                    continue

                if isinstance(action, Extract):
                    state.extracted.append(action.data)
                    rec.message = f"saved record #{len(state.extracted)}"
                    tracer.write_step(rec, shot_name)
                    continue

                # ---------------------------------------- classify + approve
                element = self.registry.elements.get(getattr(action, "element_id", -1))
                risk = classify(action, element, obs)
                rec.risk = risk.level
                if risk.level == "high":
                    rec.approved = self.gate.request(action, risk, obs, element)
                    if not rec.approved:
                        rec.ok = False
                        rec.message = ("BLOCKED: the user declined this irreversible action. Do not retry it; "
                                       "choose another path or finish with done and explain.")
                        state.recovery_hint = rec.message
                        tracer.write_step(rec, shot_name)
                        continue

                # --------------------------------------------------- act
                result = self.executor.execute(action)
                rec.ok, rec.message = result.ok, result.message
                pending, prev_obs = (rec, shot_name), obs
        finally:
            if pending:
                tracer.write_step(*pending)
            if not state.stop_reason:
                state.stop_reason = "interrupted_or_error"
            write_results(state, s.outputs_dir, self.cost)
        return state