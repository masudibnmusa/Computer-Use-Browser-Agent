from __future__ import annotations

from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()  # makes BA_SECRET_* from .env visible to the credential vault


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="BA_", extra="ignore", populate_by_name=True
    )

    anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    llm_model: str = "claude-sonnet-5-5"
    max_tokens: int = 2048

    # browser
    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 800
    profile_name: str = "default"
    action_timeout_ms: int = 7000
    data_dir: Path = Path("data")

    # perception
    max_elements: int = 150
    page_text_chars: int = 2000
    use_set_of_marks: bool = False
    use_planner: bool = False

    # budgets / stopping
    max_steps: int = 40
    max_cost_usd: float = 2.0
    max_consecutive_failures: int = 4
    loop_repeat_limit: int = 3
    history_window: int = 8

    # safety
    allowed_domains: str = ""  # comma separated; empty = allow all
    approval_mode: Literal["ask", "deny", "auto"] = "ask"

    # pricing (USD per million tokens) - adjust to your model's real pricing
    price_in_per_mtok: float = 3.0
    price_out_per_mtok: float = 15.0

    @property
    def domains(self) -> list[str]:
        return [d.strip() for d in self.allowed_domains.split(",") if d.strip()]

    @property
    def traces_dir(self) -> Path:
        return self.data_dir / "traces"

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"

    @property
    def profile_dir(self) -> Path:
        return self.data_dir / "browser_profiles" / self.profile_name