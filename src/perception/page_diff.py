from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass

from ..core.state import Observation


@dataclass
class Diff:
    changed: bool
    summary: str


def make_signature(url: str, page_text: str, elements_text: str) -> str:
    return hashlib.sha1(f"{url}\0{page_text}\0{elements_text}".encode()).hexdigest()[:12]


def compare(prev: Observation, cur: Observation) -> Diff:
    parts: list[str] = []
    url_changed = prev.url != cur.url
    if url_changed:
        parts.append(f"URL changed to {cur.url}")

    pk = Counter(e.key() for e in prev.elements)
    ck = Counter(e.key() for e in cur.elements)
    added, removed = list((ck - pk).elements()), list((pk - ck).elements())
    if added:
        sample = ", ".join((k.split("|")[1] or k.split("|")[0])[:25] for k in added[:3])
        parts.append(f"{len(added)} new/changed elements (e.g. {sample})")
    if removed:
        parts.append(f"{len(removed)} elements gone")

    text_changed = prev.page_text != cur.page_text
    if text_changed and not (added or removed or url_changed):
        parts.append("page text changed")

    changed = url_changed or bool(added) or bool(removed) or text_changed
    return Diff(changed, "; ".join(parts) or "no visible change")