from browser_agent.core.action_schema import Click, GoTo, PressKey, TypeText
from browser_agent.core.state import Observation
from browser_agent.perception.element_registry import Element
from browser_agent.safety.action_classifier import classify


def obs(url="https://shop.test/product", text="Some product page"):
    return Observation(url=url, title="", page_text=text)


def test_strong_label_is_high():
    el = Element(id=1, tag="button", label="Place order")
    assert classify(Click(element_id=1), el, obs()).level == "high"


def test_weak_label_depends_on_context():
    el = Element(id=1, tag="button", label="Submit")
    assert classify(Click(element_id=1), el, obs()).level == "low"
    assert classify(Click(element_id=1), el, obs(url="https://shop.test/checkout")).level == "high"


def test_navigation_is_low():
    assert classify(GoTo(url="https://a.com"), None, obs()).level == "low"


def test_typing_secret_placeholder_is_low_but_literal_password_is_high():
    el = Element(id=2, tag="input", type="password", label="Password")
    assert classify(TypeText(element_id=2, text="{{secret:PW}}"), el, obs()).level == "low"
    assert classify(TypeText(element_id=2, text="hunter2"), el, obs()).level == "high"


def test_enter_on_checkout_is_high():
    assert classify(PressKey(key="Enter"), None, obs(url="https://x.test/payment")).level == "high"