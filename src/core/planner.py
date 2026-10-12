"""Optional. Plans go stale quickly, so they are only passed to the LLM as a rough guide."""
from __future__ import annotations


def make_plan(llm, task: str) -> list[str]:
    text = llm.complete_text(
        "You split web tasks into 3-6 short subgoals. Output one subgoal per line, no numbering.",
        f"Task: {task}",
    )
    return [ln.strip("-• ").strip() for ln in text.splitlines() if ln.strip()][:6]