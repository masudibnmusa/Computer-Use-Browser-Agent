from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ..core.state import StepRecord


class TraceRecorder:
    """data/traces/<run_id>/{task.json, trace.jsonl, step_001.png, ...}"""

    def __init__(self, traces_dir: Path, run_id: str, task: str):
        self.dir = Path(traces_dir) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "task.json").write_text(json.dumps({"run_id": run_id, "task": task}, indent=2))
        self._file = self.dir / "trace.jsonl"

    def save_screenshot(self, step: int, png: bytes) -> str:
        name = f"step_{step:03d}.png"
        (self.dir / name).write_bytes(png)
        return name

    def write_step(self, rec: StepRecord, screenshot: str) -> None:
        with self._file.open("a") as f:
            f.write(json.dumps({**asdict(rec), "screenshot": screenshot}, default=str) + "\n")