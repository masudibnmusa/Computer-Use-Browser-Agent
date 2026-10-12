from __future__ import annotations

import json

from ..core.state import AgentState


class DataExtractor:
    """Collects records the LLM saves via the `extract` action (deduplicated)."""

    def __init__(self, state: AgentState):
        self.state = state

    def add(self, record: dict) -> bool:
        key = json.dumps(record, sort_keys=True, default=str)
        if any(json.dumps(r, sort_keys=True, default=str) == key for r in self.state.extracted):
            return False
        self.state.extracted.append(record)
        return True