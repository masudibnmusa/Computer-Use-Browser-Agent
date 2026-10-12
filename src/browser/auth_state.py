from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import BrowserContext


def save_auth_state(context: BrowserContext, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(path))


def load_auth_state(context: BrowserContext, path: str | Path) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    state = json.loads(p.read_text())
    context.add_cookies(state.get("cookies", []))
    return True