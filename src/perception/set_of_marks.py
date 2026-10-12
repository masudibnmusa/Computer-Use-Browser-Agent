from __future__ import annotations

import io

from PIL import Image, ImageDraw

PALETTE = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#008080", "#9a6324", "#800000"]


def annotate(png: bytes, elements) -> bytes:
    img = Image.open(io.BytesIO(png)).convert("RGB")
    draw = ImageDraw.Draw(img)
    for e in elements:
        color = PALETTE[e.id % len(PALETTE)]
        draw.rectangle([e.x, e.y, e.x + e.w, e.y + e.h], outline=color, width=2)
        label = str(e.id)
        ty = max(0, e.y - 14)
        draw.rectangle([e.x, ty, e.x + 7 * len(label) + 6, ty + 14], fill=color)
        draw.text((e.x + 3, ty + 1), label, fill="white")
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()