from __future__ import annotations

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

_STABLE_JS = """
({quiet, max}) => new Promise(resolve => {
  let timer;
  const done = () => { obs.disconnect(); resolve(true); };
  const obs = new MutationObserver(() => { clearTimeout(timer); timer = setTimeout(done, quiet); });
  obs.observe(document.documentElement,
    {childList: true, subtree: true, attributes: true, characterData: true});
  timer = setTimeout(done, quiet);
  setTimeout(done, max);
})
"""


def wait_dom_stable(page: Page, quiet_ms: int = 400, max_ms: int = 2500) -> None:
    try:
        page.evaluate(_STABLE_JS, {"quiet": quiet_ms, "max": max_ms})
    except PlaywrightError:
        pass  # navigation mid-evaluate etc.


def wait_for_settle(page: Page, timeout_ms: int = 5000) -> None:
    for state, t in (("domcontentloaded", timeout_ms), ("networkidle", 2500)):
        try:
            page.wait_for_load_state(state, timeout=t)
        except PlaywrightError:
            pass
    wait_dom_stable(page)