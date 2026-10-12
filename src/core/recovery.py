from __future__ import annotations

import logging
import re

from playwright.sync_api import Error as PlaywrightError

from .state import AgentState, StepRecord

log = logging.getLogger(__name__)

OVERLAY_ROOT = (
    "[role=dialog], [aria-modal='true'], [id*=cookie i], [class*=cookie i], "
    "[class*=consent i], [class*=modal i], [class*=popup i]"
)
DISMISS_BTN = re.compile(
    r"^(accept( all)?( cookies)?|i agree|agree|got it|ok(ay)?|no,? thanks|not now|maybe later|dismiss|close|×|x)$",
    re.I,
)


class Recovery:
    def __init__(self, session):
        self.session = session

    def dismiss_overlays(self) -> bool:
        page = self.session.page
        try:
            overlay = page.locator(OVERLAY_ROOT).first
            if overlay.count() == 0 or not overlay.is_visible():
                return False
            btn = overlay.get_by_role("button", name=DISMISS_BTN).first
            if btn.count():
                btn.click(timeout=2000)
            else:
                page.keyboard.press("Escape")
            return True
        except PlaywrightError as e:
            log.debug("dismiss_overlays failed: %s", e)
            return False

    def backtrack(self) -> bool:
        try:
            return self.session.page.go_back(wait_until="domcontentloaded", timeout=5000) is not None
        except PlaywrightError:
            return False

    def advice(self, state: AgentState, rec: StepRecord) -> tuple[str, bool]:
        """Returns (hint for the LLM, whether the page was modified)."""
        n = state.consecutive_failures
        if n <= 1:
            return ("The last action did not have the intended effect. Re-read the element list; "
                    "the page may have changed. Try another element or approach."), False
        if n == 2:
            acted = self.dismiss_overlays()
            return ("A popup/overlay may have been blocking the page; I tried to dismiss it. Re-check."
                    if acted else "Still no progress. Try a different element, scroll, or strategy."), acted
        acted = self.backtrack()
        return ("Several actions failed, so I navigated back to the previous page. Re-plan from here."
                if acted else "Several actions failed. Consider request_help, or done(success=false)."), acted