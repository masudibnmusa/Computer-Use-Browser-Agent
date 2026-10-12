from __future__ import annotations

from playwright.sync_api import BrowserContext, Page


class TabManager:
    """Tracks the 'current' tab; a newly opened tab/popup becomes current."""

    def __init__(self, context: BrowserContext):
        self.context = context
        self.current: Page | None = context.pages[0] if context.pages else None
        context.on("page", self._on_new_page)

    def _on_new_page(self, page: Page) -> None:
        self.current = page
        page.on("close", lambda *_: self._on_close(page))

    def _on_close(self, page: Page) -> None:
        if self.current is page:
            alive = [p for p in self.context.pages if not p.is_closed()]
            self.current = alive[-1] if alive else None

    def ensure_page(self) -> Page:
        if self.current is None or self.current.is_closed():
            alive = [p for p in self.context.pages if not p.is_closed()]
            self.current = alive[-1] if alive else self.context.new_page()
        return self.current

    def list_tabs(self) -> list[str]:
        return [p.url for p in self.context.pages if not p.is_closed()]