from __future__ import annotations

from playwright.sync_api import BrowserContext, Page, sync_playwright

from ..config import Settings
from ..safety.domain_allowlist import DomainAllowlist
from .tabs import TabManager


class BrowserSession:
    def __init__(self, settings: Settings, allowlist: DomainAllowlist | None = None):
        self.s = settings
        self.allowlist = allowlist or DomainAllowlist([])
        self._pw = None
        self.context: BrowserContext | None = None
        self.tabs: TabManager | None = None

    def start(self) -> "BrowserSession":
        self.s.profile_dir.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        self.context = self._pw.chromium.launch_persistent_context(
            str(self.s.profile_dir),
            headless=self.s.headless,
            viewport={"width": self.s.viewport_width, "height": self.s.viewport_height},
            device_scale_factor=1,  # keeps screenshot pixels == CSS pixels (needed for click_at)
        )
        self.context.set_default_timeout(self.s.action_timeout_ms)
        self.allowlist.install(self.context)
        self.tabs = TabManager(self.context)
        return self

    @property
    def page(self) -> Page:
        return self.tabs.ensure_page()

    def close(self) -> None:
        try:
            if self.context:
                self.context.close()
        finally:
            if self._pw:
                self._pw.stop()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.close()