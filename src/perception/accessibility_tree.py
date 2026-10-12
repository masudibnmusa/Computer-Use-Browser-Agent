from __future__ import annotations

from playwright.sync_api import Page


def aria_snapshot(page: Page, limit: int = 4000) -> str:
    """YAML-ish accessibility snapshot (needs Playwright >= 1.49). Optional extra context."""
    try:
        return page.locator("body").aria_snapshot()[:limit]
    except Exception:
        return ""