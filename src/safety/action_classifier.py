"""Classify risk by action + element + page context, not by keywords alone. When unsure, ask."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..core.action_schema import Click, ClickAt, PressKey, TypeText
from ..core.state import Observation
from .credential_vault import PLACEHOLDER

STRONG = re.compile(
    r"\b(pay( now)?|place (your )?order|buy( now)?|purchase|complete (order|purchase|booking)|"
    r"confirm (order|purchase|booking|payment)|delete|remove account|send|publish|post|transfer|"
    r"withdraw|donate|unsubscribe|cancel (order|subscription|booking))\b", re.I)
WEAK = re.compile(r"\b(submit|confirm|book|reserve|apply|save|sign ?up|subscribe|agree)\b", re.I)
CONTEXT = re.compile(r"(checkout|payment|billing|order summary|card number|place order|confirm booking)", re.I)
SENSITIVE_FIELD = re.compile(r"(card|cvv|cvc|iban|routing|account.?number|ssn|social.?security|password|passcode|\bpin\b)", re.I)


@dataclass
class Risk:
    level: str  # "low" | "high"
    reason: str = ""


def classify(action, element, obs: Observation) -> Risk:
    context = bool(CONTEXT.search(f"{obs.url} {obs.title} {obs.page_text[:1500]}"))
    label = " ".join(x for x in (element.label, element.placeholder) if x) if element else ""

    if isinstance(action, Click) and element:
        if STRONG.search(label):
            return Risk("high", f"clicking '{element.label}' looks irreversible")
        if context and (WEAK.search(label) or element.type == "submit"):
            return Risk("high", f"clicking '{element.label}' on a checkout/payment-like page")

    elif isinstance(action, TypeText):
        sensitive = bool(element) and (element.type == "password" or bool(SENSITIVE_FIELD.search(label)))
        if sensitive and (context or not PLACEHOLDER.search(action.text)):
            return Risk("high", "typing into a sensitive field")
        if action.press_enter and context:
            return Risk("high", "pressing Enter submits a form on a checkout/payment-like page")

    elif isinstance(action, PressKey):
        if action.key.lower() in ("enter", "return") and context:
            return Risk("high", "Enter may submit a form on a checkout/payment-like page")

    elif isinstance(action, ClickAt):
        if context:
            return Risk("high", "coordinate click on a checkout/payment-like page (target unknown)")

    return Risk("low")