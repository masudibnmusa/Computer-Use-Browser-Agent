from __future__ import annotations

from urllib.parse import urlparse

from playwright.sync_api import BrowserContext


class DomainNotAllowed(Exception):
    pass


class DomainAllowlist:
    """Empty list = allow everything. Otherwise only these domains (and subdomains) may be navigated to."""

    def __init__(self, domains: list[str]):
        self.domains = [d.lower().lstrip(".") for d in domains]

    def is_allowed(self, url: str) -> bool:
        if not self.domains:
            return True
        parsed = urlparse(url)
        if parsed.scheme in ("about", "blob"):
            return True
        host = (parsed.hostname or "").lower()
        return any(host == d or host.endswith("." + d) for d in self.domains)

    def assert_allowed(self, url: str) -> None:
        if not self.is_allowed(url):
            raise DomainNotAllowed(f"navigation to {url} is blocked by the domain allowlist")

    def install(self, context: BrowserContext) -> None:
        """Also blocks navigations triggered by clicks/redirects, not just goto."""
        if not self.domains:
            return

        def _route(route):
            req = route.request
            if req.is_navigation_request() and not self.is_allowed(req.url):
                route.abort("blockedbyclient")
            else:
                route.continue_()

        context.route("**/*", _route)