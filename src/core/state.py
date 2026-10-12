from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Observation:
    url: str = ""
    title: str = ""
    screenshot: bytes = b""
    elements: list[Any] = field(default_factory=list)
    elements_text: str = ""
    page_text: str = ""
    injection_flags: list[str] = field(default_factory=list)
    signature: str = ""
    truncated: int = 0


@dataclass
class StepRecord:
    step: int
    url: str
    action: str
    args: dict[str, Any]
    reasoning: str
    ok: bool
    message: str
    effect: str = ""
    changed: bool | None = None
    risk: str = "low"
    approved: bool | None = None


@dataclass
class AgentState:
    task: str
    run_id: str = field(
        default_factory=lambda: time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    )
    steps: list[StepRecord] = field(default_factory=list)
    progress_notes: str = ""
    current_url: str = ""
    plan: list[str] = field(default_factory=list)
    extracted: list[dict] = field(default_factory=list)
    signatures: list[str] = field(default_factory=list)
    consecutive_failures: int = 0
    recovery_hint: str = ""
    finished: bool = False
    success: bool = False
    final_summary: str = ""
    final_result: dict | None = None
    stop_reason: str = ""

    def history_text(self, window: int) -> str:
        lines: list[str] = []
        skipped = max(0, len(self.steps) - window)
        if skipped:
            lines.append(f"(... {skipped} earlier steps omitted)")
        for r in self.steps[-window:]:
            args = ", ".join(f"{k}={repr(v)[:80]}" for k, v in r.args.items())
            line = f"{r.step}. {r.action}({args}) -> {'ok' if r.ok else 'FAILED'}"
            if r.message:
                line += f": {r.message}"
            if r.effect:
                line += f" | effect: {r.effect}"
            lines.append(line)
        return "\n".join(lines) or "(none yet)"