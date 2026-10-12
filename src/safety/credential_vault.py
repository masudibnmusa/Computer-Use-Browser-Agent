"""Secrets live in env vars BA_SECRET_<NAME>. The LLM only ever sees {{secret:NAME}} placeholders."""
from __future__ import annotations

import os
import re
from typing import Mapping

PLACEHOLDER = re.compile(r"\{\{secret:([A-Za-z0-9_]+)\}\}")
PREFIX = "BA_SECRET_"


class CredentialVault:
    def __init__(self, environ: Mapping[str, str] | None = None):
        self._env = environ if environ is not None else os.environ

    def names(self) -> list[str]:
        return [k[len(PREFIX):] for k in self._env if k.startswith(PREFIX)]

    def resolve(self, text: str) -> str:
        """Replace placeholders with real values (called only inside the executor). Raises KeyError if missing."""
        def sub(m: re.Match) -> str:
            return self._env[PREFIX + m.group(1)]
        return PLACEHOLDER.sub(sub, text)

    def redact(self, text: str) -> str:
        """Scrub known secret values from anything headed to the LLM or logs."""
        for name in self.names():
            value = self._env[PREFIX + name]
            if len(value) >= 4:
                text = text.replace(value, f"{{{{secret:{name}}}}}")
        return text