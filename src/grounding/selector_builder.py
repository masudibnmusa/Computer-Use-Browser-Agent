"""Resilient locators (role / label / text) used when the data-ba-id tag is gone after a re-render."""
from __future__ import annotations

from typing import TYPE_CHECKING

from playwright.sync_api import Frame, Locator

if TYPE_CHECKING:
    from ..perception.element_registry import Element

_TAG_ROLE = {"a": "link", "button": "button", "select": "combobox", "textarea": "textbox", "summary": "button"}
_INPUT_ROLE = {"checkbox": "checkbox", "radio": "radio", "submit": "button", "button": "button",
               "": "textbox", "text": "textbox", "email": "textbox", "search": "textbox",
               "tel": "textbox", "url": "textbox", "password": "textbox"}


def implicit_role(el: "Element") -> str:
    if el.role:
        return el.role
    if el.tag == "input":
        return _INPUT_ROLE.get(el.type, "")
    return _TAG_ROLE.get(el.tag, "")


def build_locator(scope: Frame, el: "Element") -> Locator:
    role = implicit_role(el)
    if role and el.label:
        return scope.get_by_role(role, name=el.label, exact=True)  # type: ignore[arg-type]
    if el.placeholder:
        return scope.get_by_placeholder(el.placeholder, exact=True)
    if el.label:
        return scope.get_by_text(el.label, exact=True)
    return scope.locator(el.tag)