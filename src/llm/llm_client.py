from __future__ import annotations

import base64

import anthropic
from pydantic import ValidationError

from ..config import Settings
from ..core.action_schema import ACTIONS, tool_definitions
from ..core.state import AgentState, Observation
from ..utils.cost_tracker import CostTracker
from .prompts import SYSTEM_PROMPT, build_user_text


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, settings: Settings, cost: CostTracker):
        self.s = settings
        self.cost = cost
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None, max_retries=3)
        self.tools = tool_definitions()

    def decide(self, state: AgentState, obs: Observation):
        """One stateless call per step: only the latest screenshot is sent; history is text."""
        content = [
            {"type": "text", "text": build_user_text(state, obs, self.s)},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": base64.b64encode(obs.screenshot).decode()}},
        ]
        resp = self.client.messages.create(
            model=self.s.llm_model,
            max_tokens=self.s.max_tokens,
            system=SYSTEM_PROMPT,
            tools=self.tools,
            tool_choice={"type": "any"},
            messages=[{"role": "user", "content": content}],
        )
        self.cost.add_usage(resp.usage, images=1)

        reasoning = " ".join(b.text for b in resp.content if b.type == "text").strip()
        for block in resp.content:
            if block.type != "tool_use":
                continue
            cls = ACTIONS.get(block.name)
            if cls is None:
                raise LLMError(f"unknown tool '{block.name}'")
            try:
                action = cls.model_validate(block.input)
            except ValidationError as e:
                raise LLMError(f"bad arguments for {block.name}: {str(e).splitlines()[0]}") from e
            return action, reasoning or action.progress_note
        raise LLMError("model returned no tool call")

    def complete_text(self, system: str, prompt: str) -> str:
        resp = self.client.messages.create(
            model=self.s.llm_model, max_tokens=500, system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        self.cost.add_usage(resp.usage)
        return "".join(b.text for b in resp.content if b.type == "text")