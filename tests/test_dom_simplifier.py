from browser_agent.perception.dom_simplifier import format_elements
from browser_agent.perception.element_registry import Element


def test_formats_button_input_and_link():
    els = [
        Element(id=1, tag="button", label="Search"),
        Element(id=2, tag="input", type="text", label="Name", placeholder="Your name", value="Ada"),
        Element(id=3, tag="a", label="Home", href="/home"),
        Element(id=4, tag="input", type="checkbox", label="Agree", checked=False, disabled=True),
    ]
    out = format_elements(els).splitlines()
    assert out[0] == '[1] button "Search"'
    assert 'input:text "Name"' in out[1] and 'value="Ada"' in out[1] and 'placeholder="Your name"' in out[1]
    assert out[2] == '[3] a "Home" -> /home'
    assert "unchecked" in out[3] and "(disabled)" in out[3]