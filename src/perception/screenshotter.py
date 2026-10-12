from __future__ import annotations

from playwright.sync_api import Page


def capture(page: Page, mask_sensitive: bool = True) -> bytes:
    """Viewport PNG. Password / card / OTP fields are masked so secrets never reach the LLM."""
    kwargs: dict = {"type": "png", "full_page": False, "timeout": 10000}
    if mask_sensitive:
        kwargs["mask"] = [
            page.locator("input[type=password]"),
            page.locator("input[autocomplete^='cc-']"),
            page.locator("input[autocomplete='one-time-code']"),
        ]
    return page.screenshot(**kwargs)