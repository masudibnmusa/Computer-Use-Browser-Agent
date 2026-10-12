from __future__ import annotations

import csv
import json
from pathlib import Path

from ..core.state import AgentState


def write_results(state: AgentState, outputs_dir: Path, cost=None) -> Path:
    out = Path(outputs_dir) / state.run_id
    out.mkdir(parents=True, exist_ok=True)

    payload = {
        "task": state.task,
        "success": state.success,
        "stop_reason": state.stop_reason,
        "summary": state.final_summary,
        "result": state.final_result,
        "records": state.extracted,
        "steps": len(state.steps),
        "cost": cost.as_dict() if cost else None,
    }
    (out / "result.json").write_text(json.dumps(payload, indent=2, default=str))

    if state.extracted:
        fields: list[str] = []
        for r in state.extracted:
            fields += [k for k in r if k not in fields]
        with (out / "records.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(state.extracted)

    lines = [
        f"# Run {state.run_id}", "",
        f"**Task:** {state.task}", f"**Success:** {state.success}",
        f"**Stopped because:** {state.stop_reason}", "", "## Summary", state.final_summary or "(none)", "",
        "## Steps",
    ]
    for r in state.steps:
        mark = "ok" if r.ok else "FAILED"
        lines.append(f"{r.step}. `{r.action}` {mark} - {r.message} {('(' + r.effect + ')') if r.effect else ''}")
    (out / "report.md").write_text("\n".join(lines))
    return out