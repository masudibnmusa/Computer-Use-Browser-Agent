from __future__ import annotations

from enum import Enum

from ..config import Settings
from ..utils.cost_tracker import CostTracker
from .state import AgentState


class StopReason(str, Enum):
    MAX_STEPS = "max_steps"
    COST_CAP = "cost_cap"
    LOOP = "loop_detected"
    FAILURES = "too_many_failures"


class StoppingCriteria:
    def __init__(self, settings: Settings):
        self.s = settings

    @staticmethod
    def repeat_count(state: AgentState) -> int:
        """How many identical (page, action) signatures at the end of history."""
        if not state.signatures:
            return 0
        last, n = state.signatures[-1], 0
        for sig in reversed(state.signatures):
            if sig != last:
                break
            n += 1
        return n

    def check(self, state: AgentState, cost: CostTracker) -> StopReason | None:
        if len(state.steps) >= self.s.max_steps:
            return StopReason.MAX_STEPS
        if cost.cost_usd >= self.s.max_cost_usd:
            return StopReason.COST_CAP
        if self.repeat_count(state) >= self.s.loop_repeat_limit:
            return StopReason.LOOP
        if state.consecutive_failures >= self.s.max_consecutive_failures:
            return StopReason.FAILURES
        return None