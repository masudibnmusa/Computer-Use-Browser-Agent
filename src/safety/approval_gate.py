from __future__ import annotations


class ApprovalGate:
    """mode: 'ask' = prompt in terminal, 'deny' = block all risky actions, 'auto' = allow (use with care)."""

    def __init__(self, mode: str = "ask"):
        self.mode = mode

    def request(self, action, risk, obs, element=None) -> bool:
        if self.mode == "auto":
            return True
        if self.mode == "deny":
            return False
        target = element.describe() if element else "(no element)"
        print("\n⚠  Approval needed")
        print(f"   action : {action.tool_name} {action.model_dump(exclude={'progress_note'})}")
        print(f"   target : {target}")
        print(f"   page   : {obs.url}")
        print(f"   reason : {risk.reason}")
        try:
            return input("   Approve? [y/N] ").strip().lower() in ("y", "yes")
        except EOFError:
            return False