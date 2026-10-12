from __future__ import annotations

from playwright.sync_api import Page


def click_at(page: Page, x: int, y: int) -> None:
    """Vision fallback. Screenshot pixels == CSS pixels because device_scale_factor=1 and no resizing."""
    vp = page.viewport_size or {"width": 1280, "height": 800}
    if not (0 <= x < vp["width"] and 0 <= y < vp["height"]):
        raise ValueError(f"coordinates ({x},{y}) are outside the {vp['width']}x{vp['height']} viewport")
    page.mouse.click(x, y)