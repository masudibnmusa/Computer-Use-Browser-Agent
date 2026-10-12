from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostTracker:
    price_in_per_mtok: float
    price_out_per_mtok: float
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0
    images: int = 0

    def add_usage(self, usage, images: int = 0) -> None:
        self.input_tokens += getattr(usage, "input_tokens", 0) or 0  # image tokens are included here
        self.output_tokens += getattr(usage, "output_tokens", 0) or 0
        self.calls += 1
        self.images += images

    @property
    def cost_usd(self) -> float:
        return (self.input_tokens * self.price_in_per_mtok
                + self.output_tokens * self.price_out_per_mtok) / 1_000_000

    def as_dict(self) -> dict:
        return {"calls": self.calls, "images": self.images, "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens, "cost_usd": round(self.cost_usd, 4)}