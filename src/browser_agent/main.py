from __future__ import annotations

import argparse
import sys

from .browser.session_manager import BrowserSession
from .config import Settings
from .core.agent_loop import AgentLoop
from .llm.llm_client import LLMClient
from .safety.domain_allowlist import DomainAllowlist
from .utils.cost_tracker import CostTracker
from .utils.logging_setup import setup_logging
from .utils.trace_replayer import render_html


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="browser-agent")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run a task")
    r.add_argument("task")
    r.add_argument("--start-url")
    r.add_argument("--headed", action="store_true")
    r.add_argument("--max-steps", type=int)
    r.add_argument("--approval", choices=["ask", "deny", "auto"])
    r.add_argument("--allow-domain", action="append", default=[])
    r.add_argument("--set-of-marks", action="store_true")
    r.add_argument("--plan", action="store_true")

    rp = sub.add_parser("replay", help="render an HTML report for a trace dir")
    rp.add_argument("run_dir")
    return p


def cmd_run(args) -> int:
    overrides: dict = {}
    if args.headed:
        overrides["headless"] = False
    if args.max_steps:
        overrides["max_steps"] = args.max_steps
    if args.approval:
        overrides["approval_mode"] = args.approval
    if args.set_of_marks:
        overrides["use_set_of_marks"] = True
    if args.plan:
        overrides["use_planner"] = True
    settings = Settings().model_copy(update=overrides)
    if args.allow_domain:
        settings = settings.model_copy(
            update={"allowed_domains": ",".join([*settings.domains, *args.allow_domain])}
        )
    if not settings.anthropic_api_key:
        print("ANTHROPIC_API_KEY is not set (see .env.example).", file=sys.stderr)
        return 2

    setup_logging()
    cost = CostTracker(settings.price_in_per_mtok, settings.price_out_per_mtok)
    llm = LLMClient(settings, cost)
    allowlist = DomainAllowlist(settings.domains)

    with BrowserSession(settings, allowlist) as session:
        if args.start_url:
            allowlist.assert_allowed(args.start_url)
            session.page.goto(args.start_url, wait_until="domcontentloaded")
        state = AgentLoop(settings, session, llm, cost).run(args.task)

    print("\n=== RESULT ===")
    print(f"success : {state.success}")
    print(f"stopped : {state.stop_reason}")
    print(f"summary : {state.final_summary}")
    if state.final_result:
        print(f"result  : {state.final_result}")
    print(f"steps   : {len(state.steps)}   cost: ${cost.cost_usd:.4f}")
    print(f"trace   : {settings.traces_dir / state.run_id}")
    print(f"outputs : {settings.outputs_dir / state.run_id}")
    return 0 if state.success else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.cmd == "run":
        sys.exit(cmd_run(args))
    if args.cmd == "replay":
        print(render_html(args.run_dir))


if __name__ == "__main__":
    main()