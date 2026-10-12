from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunMetrics:
    task: str
    success: bool
    steps: int
    cost_usd: float
    had_failures: bool
    failure_category: str
    seconds: float


def summarize(runs: list[RunMetrics]) -> dict:
    n = len(runs) or 1
    with_fail = [r for r in runs if r.had_failures]
    return {
        "runs": len(runs),
        "success_rate": sum(r.success for r in runs) / n,
        "avg_steps": sum(r.steps for r in runs) / n,
        "avg_cost_usd": round(sum(r.cost_usd for r in runs) / n, 4),
        # of runs that hit at least one failed step, how many still succeeded?
        "recovery_rate": (sum(r.success for r in with_fail) / len(with_fail)) if with_fail else None,
    }