"""Queue for requests the UI could not send because the network failed."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

from app.audit import iso, retention_deadline, utcnow
from app.models import GenerateIn
from app.redact import prepare_value

SCHEMA = """
CREATE TABLE IF NOT EXISTS offline_queue (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  retention_until TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL,
  last_error TEXT NOT NULL
);
"""


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def queue_request(path: Path, raw: dict, retention_days: int) -> dict:
    spec = GenerateIn.model_validate(raw)
    cleaned, counts, flags = prepare_value(spec.model_dump())
    prepared = GenerateIn.model_validate(cleaned)
    item_id = str(uuid.uuid4())
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT INTO offline_queue (id, created_at, retention_until, payload, status, last_error)
            VALUES (?, ?, ?, ?, 'waiting', '')
            """,
            (item_id, iso(utcnow()), retention_deadline(retention_days), prepared.model_dump_json()),
        )
    return {"id": item_id, "payload": prepared.model_dump(), "pii_counts": counts, "injection_flags": flags}


def list_waiting(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT * FROM offline_queue WHERE status = 'waiting' ORDER BY created_at"
        ).fetchall()
    return [dict(row) for row in rows]


def mark(path: Path, item_id: str, status: str, error: str = "") -> None:
    with _connect(path) as conn:
        conn.execute(
            "UPDATE offline_queue SET status = ?, last_error = ? WHERE id = ?",
            (status, error[:200], item_id),
        )


def purge_expired(path: Path) -> int:
    if not path.exists():
        return 0
    with _connect(path) as conn:
        cursor = conn.execute(
            "DELETE FROM offline_queue WHERE retention_until < ?",
            (iso(utcnow()),),
        )
        return cursor.rowcount
