from types import SimpleNamespace

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

from browser_agent.config import Settings
from browser_agent.core.action_schema import Click, Done, TypeText
from browser_agent.core.agent_loop import AgentLoop
from browser_agent.safety.domain_allowlist import DomainAllowlist
from browser_agent.utils.cost_tracker import CostTracker

HTML = """
<label for="name">Name</label><input id="name">
<button onclick="document.title='PLACED'">Place order</button>
"""


def find(obs, label):
    return next(e.id for e in obs.elements if e.label == label)


class FakeLLM:
    def __init__(self, script):
        self.script = list(script)

    def decide(self, state, obs):
        return self.script.pop(0)(obs), "scripted"


@pytest.fixture()
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 800, "height": 600})
        pg.set_content(HTML)
        yield pg
        browser.close()


def test_types_then_blocks_irreversible_click_then_finishes(page, tmp_path):
    settings = Settings(data_dir=tmp_path, approval_mode="deny", headless=True, max_steps=10)
    session = SimpleNamespace(page=page, allowlist=DomainAllowlist([]))
    llm = FakeLLM([
        lambda o: TypeText(element_id=find(o, "Name"), text="Ada"),
        lambda o: Click(element_id=find(o, "Place order")),
        lambda o: Done(success=True, summary="filled form, order blocked"),
    ])
    state = AgentLoop(settings, session, llm, CostTracker(3.0, 15.0)).run("fill the form")

    assert state.success and state.stop_reason == "done"
    assert page.input_value("#name") == "Ada"
    assert page.title() != "PLACED"  # the irreversible click never executed
    blocked = [s for s in state.steps if s.risk == "high"]
    assert blocked and blocked[0].approved is False
    assert (tmp_path / "outputs" / state.run_id / "result.json").exists()
    assert (tmp_path / "traces" / state.run_id / "trace.jsonl").exists()