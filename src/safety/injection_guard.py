"""Page text is untrusted data. Wrap it and flag obvious attempts to instruct the agent."""
from __future__ import annotations

import re

_PATTERNS = {
    "override-instructions": r"ignore (all |any )?(previous|prior|above|earlier) (instructions|prompts|rules)",
    "disregard": r"disregard .{0,40}(instructions|rules|task)",
    "role-change": r"\byou are now\b|\bnew instructions\b|\bact as\b.{0,20}\b(assistant|agent)\b",
    "addresses-ai": r"\b(ai|llm|assistant|agent|claude)\b.{0,30}\b(must|should|now)\b",
    "exfiltration": r"(send|email|post|upload|reveal).{0,60}(password|credentials|cookies|token|api key|secret)",
    "secrecy": r"do not (tell|inform|mention).{0,30}(user|human)",
}
_COMPILED = {k: re.compile(v, re.I) for k, v in _PATTERNS.items()}


def scan(text: str) -> list[str]:
    return [name for name, rx in _COMPILED.items() if rx.search(text)]


def wrap_untrusted(text: str) -> str:
    safe = text.replace("</untrusted_page_content>", "")
    return f"<untrusted_page_content>\n{safe}\n</untrusted_page_content>"