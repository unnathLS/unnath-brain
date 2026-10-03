from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    brain_root: Path
    db_path: Path
    api_tokens: dict[str, str]

    @classmethod
    def from_env(cls) -> "Settings":
        raw_tokens = os.getenv("BRAIN_API_TOKENS", "")
        if not raw_tokens:
            raise RuntimeError("BRAIN_API_TOKENS não configurado")
        try:
            tokens = json.loads(raw_tokens)
        except json.JSONDecodeError as exc:
            raise RuntimeError("BRAIN_API_TOKENS deve ser um objeto JSON") from exc
        if (
            not isinstance(tokens, dict)
            or not tokens
            or any(not isinstance(key, str) or not isinstance(value, str) or not value for key, value in tokens.items())
            or len(set(tokens.values())) != len(tokens)
        ):
            raise RuntimeError("BRAIN_API_TOKENS deve mapear identidades para tokens únicos")
        return cls(
            brain_root=Path(os.getenv("BRAIN_ROOT", "brain")),
            db_path=Path(os.getenv("BRAIN_DB_PATH", "data/brain.db")),
            api_tokens=tokens,
        )

