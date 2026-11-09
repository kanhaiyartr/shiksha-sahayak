"""Runtime settings. Defaults keep the demo offline and under a small cap."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

FAST_MODEL = "claude-haiku-5-5"
STANDARD_MODEL = "claude-sonnet-5-5"
ALLOWED_MODELS = frozenset({FAST_MODEL, STANDARD_MODEL})


@dataclass(frozen=True)
class Settings:
    db_path: Path
    offline_db_path: Path
    monthly_cap_usd: float = 5.0
    retention_days: int = 90
    generate_mode: str = "local"  # local | claude
    model: str = STANDARD_MODEL
    api_base: str = "http://127.0.0.1:8000"

    def resolved_model(self, override: str | None) -> str:
        if override is None:
            return self.model
        if override not in ALLOWED_MODELS:
            raise ValueError(f"Unknown model. Choose one of: {', '.join(sorted(ALLOWED_MODELS))}")
        return override


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env", override=False)
    data = ROOT / "data"
    return Settings(
        db_path=Path(os.environ.get("SHIKSHA_DB", data / "shiksha.sqlite")),
        offline_db_path=Path(os.environ.get("SHIKSHA_OFFLINE_DB", data / "offline_queue.sqlite")),
        monthly_cap_usd=float(os.environ.get("SHIKSHA_MONTHLY_CAP_USD", "5")),
        retention_days=int(os.environ.get("SHIKSHA_RETENTION_DAYS", "90")),
        generate_mode=os.environ.get("SHIKSHA_GENERATE_MODE", "local"),
        model=os.environ.get("SHIKSHA_MODEL", STANDARD_MODEL),
        api_base=os.environ.get("SHIKSHA_API_BASE", "http://127.0.0.1:8000"),
    )
