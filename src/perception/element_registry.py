"""Indexes interactive elements (main frame, iframes, open shadow DOM) and resolves IDs back to locators.
IDs are only valid for the observation that produced them; re-index after every action."""
from __future__ import annotations

from dataclasses import dataclass, field

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Frame, Locator, Page

from ..grounding.selector_builder import build_locator

COLLECT_JS = r"""
(startId) => {
  const SEL = 'a[href],button,input,select,textarea,summary,[role=button],[role=link],[role=checkbox],' +
    '[role=radio],[role=tab],[role=menuitem],[role=switch],[role=combobox],[role=option],[onclick],' +
    '[contenteditable=""],[contenteditable="true"],[tabindex]:not([tabindex="-1"])';
  const out = [];
  let id = startId;
  const vw = window.innerWidth, vh = window.innerHeight;

  function labelOf(el) {
    const t = el.tagName;
    const btnInput = t === 'INPUT' && ['submit', 'button', 'reset'].includes(el.type) ? el.value : '';
    const lab = (el.labels && el.labels[0]) ? el.labels[0].innerText : '';
    return (el.getAttribute('aria-label') || lab || btnInput || el.innerText ||
            el.getAttribute('title') || el.getAttribute('alt') || '')
      .trim().replace(/\s+/g, ' ').slice(0, 80);
  }

  function walk(root) {
    for (const el of root.querySelectorAll('*')) {
      if (el.hasAttribute('data-ba-id')) el.removeAttribute('data-ba-id');
      if (el.shadowRoot) walk(el.shadowRoot);
      if (!el.matches(SEL)) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      if (r.bottom <= 0 || r.top >= vh || r.right <= 0 || r.left >= vw) continue;
      const cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) === 0) continue;
      const cx = Math.min(Math.max(r.left + r.width / 2, 0), vw - 1);
      const cy = Math.min(Math.max(r.top + r.height / 2, 0), vh - 1);
      const top = root.elementFromPoint ? root.elementFromPoint(cx, cy) : null;
      if (top && !(el === top || el.contains(top) || top.contains(el))) continue; // covered by overlay

      const tag = el.tagName.toLowerCase();
      const type = (el.getAttribute('type') || '').toLowerCase();
      const isField = ['input', 'select', 'textarea'].includes(tag);
      let value = '';
      if (type !== 'password') {
        if (tag === 'select') value = el.selectedOptions[0] ? el.selectedOptions[0].text : '';
        else if (isField) value = String(el.value ?? '');
      }
      const ariaChecked = el.getAttribute('aria-checked');
      el.setAttribute('data-ba-id', String(id));
      out.push({
        id, tag, type,
        role: el.getAttribute('role') || '',
        label: labelOf(el),
        placeholder: el.getAttribute('placeholder') || '',
        href: tag === 'a' ? (el.getAttribute('href') || '') : '',
        value: value.slice(0, 60),
        checked: (type === 'checkbox' || type === 'radio') ? !!el.checked
                 : (ariaChecked === null ? null : ariaChecked === 'true'),
        disabled: !!el.disabled || el.getAttribute('aria-disabled') === 'true',
        options: tag === 'select' ? Array.from(el.options).slice(0, 15).map(o => o.text.trim()) : [],
        x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height),
      });
      id++;
    }
  }
  walk(document);
  return out;
}
"""


class ElementNotFound(Exception):
    pass


@dataclass
class Element:
    id: int
    tag: str
    role: str = ""
    type: str = ""
    label: str = ""
    placeholder: str = ""
    href: str = ""
    value: str = ""
    checked: bool | None = None
    disabled: bool = False
    options: list[str] = field(default_factory=list)
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    frame_index: int = 0

    def key(self) -> str:
        """Identity ignoring the numeric ID (used for before/after diffs)."""
        return f"{self.role or self.tag}|{self.label}|{self.value}|{self.checked}"

    def describe(self) -> str:
        return f'{self.tag}{"[" + self.type + "]" if self.type else ""} "{self.label}"'


class ElementRegistry:
    def __init__(self, max_elements: int = 150):
        self.max_elements = max_elements
        self.elements: dict[int, Element] = {}
        self.truncated = 0
        self._frames: dict[int, Frame] = {}

    def refresh(self, page: Page) -> list[Element]:
        self.elements.clear()
        self._frames.clear()
        self.truncated = 0
        next_id = 1
        for fi, frame in enumerate(page.frames):
            if frame.is_detached():
                continue
            ox = oy = 0
            if frame != page.main_frame:
                try:
                    bb = frame.frame_element().bounding_box()
                except PlaywrightError:
                    bb = None
                if not bb:
                    continue
                ox, oy = round(bb["x"]), round(bb["y"])
            try:
                raw = frame.evaluate(COLLECT_JS, next_id)
            except PlaywrightError:
                continue
            for r in raw:
                if len(self.elements) >= self.max_elements:
                    self.truncated += 1
                    continue
                el = Element(frame_index=fi, **r)
                el.x += ox
                el.y += oy
                self.elements[el.id] = el
                self._frames[el.id] = frame
            next_id += len(raw)
        return list(self.elements.values())

    def resolve(self, element_id: int) -> Locator:
        el = self.elements.get(element_id)
        frame = self._frames.get(element_id)
        if el is None or frame is None:
            raise ElementNotFound(f"No element with ID {element_id} on the current page")
        try:
            loc = frame.locator(f'[data-ba-id="{element_id}"]')
            if loc.count() == 1:
                return loc
            fallback = build_locator(frame, el)  # DOM re-rendered: try role/label/text
            if fallback.count() == 1:
                return fallback
        except PlaywrightError:
            pass
        raise ElementNotFound(f"Element {element_id} ({el.describe()}) is no longer on the page")