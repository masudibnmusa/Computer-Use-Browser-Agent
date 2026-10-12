"""Contract between the LLM and the browser. Each action = one Claude tool."""
from __future__ import annotations

from typing import Any, ClassVar, Literal, Union

from pydantic import BaseModel, Field


class _Base(BaseModel):
    tool_name: ClassVar[str] = ""
    progress_note: str = Field(
        default="", description="One short sentence: what is done so far and what comes next."
    )


class Click(_Base):
    """Click an interactive element by its [ID] from the element list."""
    tool_name: ClassVar[str] = "click"
    element_id: int


class ClickAt(_Base):
    """Click at pixel coordinates of the screenshot. Only for targets with no element ID (canvas, custom widgets)."""
    tool_name: ClassVar[str] = "click_at"
    x: int
    y: int


class TypeText(_Base):
    """Type text into an input/textarea by element ID. Use {{secret:NAME}} for passwords or tokens."""
    tool_name: ClassVar[str] = "type_text"
    element_id: int
    text: str
    clear_first: bool = True
    press_enter: bool = False


class SelectOption(_Base):
    """Choose an option (by visible text or value) in a <select> element."""
    tool_name: ClassVar[str] = "select_option"
    element_id: int
    option: str


class Scroll(_Base):
    """Scroll the page vertically to reveal more elements."""
    tool_name: ClassVar[str] = "scroll"
    direction: Literal["down", "up"] = "down"
    amount: int = Field(default=600, ge=50, le=3000)


class PressKey(_Base):
    """Press a keyboard key, e.g. Enter, Escape, Tab, ArrowDown, Control+a."""
    tool_name: ClassVar[str] = "press_key"
    key: str


class GoTo(_Base):
    """Navigate the current tab to a URL."""
    tool_name: ClassVar[str] = "goto"
    url: str


class Wait(_Base):
    """Wait for the page to load or update."""
    tool_name: ClassVar[str] = "wait"
    seconds: float = Field(default=2.0, ge=0.5, le=10)


class Extract(_Base):
    """Save one structured record of data you found on the page (e.g. a product with name and price)."""
    tool_name: ClassVar[str] = "extract"
    data: dict[str, Any]


class RequestHelp(_Base):
    """Ask the human to take over: CAPTCHA, 2FA, login wall without credentials, or anything you must not bypass."""
    tool_name: ClassVar[str] = "request_help"
    reason: str


class Done(_Base):
    """Finish the task. Report success or failure honestly."""
    tool_name: ClassVar[str] = "done"
    success: bool
    summary: str
    result: dict[str, Any] | None = None


ALL_ACTIONS: list[type[_Base]] = [
    Click, ClickAt, TypeText, SelectOption, Scroll, PressKey, GoTo, Wait, Extract, RequestHelp, Done,
]
ACTIONS: dict[str, type[_Base]] = {c.tool_name: c for c in ALL_ACTIONS}
Action = Union[Click, ClickAt, TypeText, SelectOption, Scroll, PressKey, GoTo, Wait, Extract, RequestHelp, Done]


def tool_definitions() -> list[dict]:
    tools = []
    for cls in ALL_ACTIONS:
        schema = cls.model_json_schema()
        schema.pop("title", None)
        schema.pop("description", None)
        tools.append(
            {"name": cls.tool_name, "description": (cls.__doc__ or "").strip(), "input_schema": schema}
        )
    return tools


def action_args(action: _Base) -> dict[str, Any]:
    return action.model_dump(exclude={"progress_note"})