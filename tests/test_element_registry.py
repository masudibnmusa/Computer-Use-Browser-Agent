import pytest

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

from browser_agent.perception.element_registry import ElementNotFound, ElementRegistry

HTML = """
<button id="a">Save</button>
<button style="display:none">Hidden</button>
<label for="n">Name</label><input id="n">
<div style="position:fixed;inset:0;background:white;z-index:9;display:none" id="overlay"></div>
"""


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 800, "height": 600})
        yield pg
        browser.close()


def test_indexes_only_visible_interactive(page):
    page.set_content(HTML)
    reg = ElementRegistry()
    labels = [e.label for e in reg.refresh(page)]
    assert "Save" in labels and "Name" in labels and "Hidden" not in labels


def test_resolve_and_stale(page):
    page.set_content(HTML)
    reg = ElementRegistry()
    save = next(e for e in reg.refresh(page) if e.label == "Save")
    assert reg.resolve(save.id).count() == 1
    page.evaluate("document.getElementById('a').remove()")
    with pytest.raises(ElementNotFound):
        reg.resolve(save.id)


def test_overlay_hides_covered_elements(page):
    page.set_content(HTML)
    page.evaluate("document.getElementById('overlay').style.display='block'")
    labels = [e.label for e in ElementRegistry().refresh(page)]
    assert "Save" not in labels