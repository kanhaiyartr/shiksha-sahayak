"""Delete rows whose retention date has passed. The log records counts only."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.audit import purge_expired
from app.config import load_settings
from app.offline import purge_expired as purge_offline


def main() -> None:
    settings = load_settings()
    print("database", purge_expired(settings.db_path))
    print("waiting_queue", purge_offline(settings.offline_db_path))


if __name__ == "__main__":
    main()
