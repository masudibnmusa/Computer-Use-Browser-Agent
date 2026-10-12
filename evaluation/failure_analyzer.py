from __future__ import annotations


def categorize(success: bool, stop_reason: str, steps: list[dict]) -> str:
    if success:
        return "success"
    msgs = " ".join((s.get("message") or "") for s in steps)
    if stop_reason == "loop_detected":
        return "loop"
    if stop_reason in ("max_steps", "cost_cap"):
        return "budget_exhausted"
    if stop_reason == "needs_human":
        return "needs_human"
    if any(s.get("action") == "invalid_action" for s in steps):
        return "invalid_llm_output"
    if "no longer on the page" in msgs or "No element with ID" in msgs:
        return "grounding_stale_element"
    if "timed out" in msgs:
        return "timeout"
    if any(s.get("changed") is False for s in steps):
        return "actions_had_no_effect"
    if any(s.get("approved") is False for s in steps):
        return "blocked_by_safety"
    return "other"