from __future__ import annotations

import re

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

from .element_registry import Element


def _short(s: str, n: int = 60) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def format_elements(elements: list[Element]) -> str:
    lines = []
    for e in elements:
        kind = f"input:{e.type or 'text'}" if e.tag == "input" else (e.role or e.tag)
        parts = [f"[{e.id}]", kind]
        if e.label:
            parts.append(f'"{e.label}"')
        if e.placeholder and e.placeholder != e.label:
            parts.append(f'placeholder="{e.placeholder}"')
        if e.value and e.value != e.label and e.tag in ("input", "select", "textarea"):
            parts.append(f'value="{e.value}"')
        if e.options:
            parts.append("options=[" + " | ".join(e.options) + "]")
        if e.checked is not None:
            parts.append("checked" if e.checked else "unchecked")
        if e.disabled:
            parts.append("(disabled)")
        if e.href:
            parts.append("-> " + _short(e.href, 70))
        lines.append(" ".join(parts))
    return "\n".join(lines)


def visible_text(page: Page, limit: int = 2000) -> str:
    try:
        text = page.inner_text("body", timeout=2000)
    except PlaywrightError:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit] + " …[truncated]"