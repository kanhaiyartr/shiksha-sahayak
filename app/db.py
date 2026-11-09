"""SQLite access for drafts, the audit log, and the usage ledger."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS materials (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  retention_until TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  actor_role TEXT NOT NULL,
  status TEXT NOT NULL,
  task_type TEXT NOT NULL,
  class_level TEXT NOT NULL,
  language TEXT NOT NULL,
  subject TEXT NOT NULL,
  topic TEXT NOT NULL,
  n_questions INTEGER NOT NULL,
  input_json TEXT NOT NULL,
  output_json TEXT,
  validation_json TEXT NOT NULL,
  model TEXT NOT NULL,
  provider TEXT NOT NULL,
  input_tokens INTEGER NOT NULL,
  output_tokens INTEGER NOT NULL,
  cache_write_tokens INTEGER NOT NULL,
  cache_read_tokens INTEGER NOT NULL,
  cost_usd REAL NOT NULL,
  rejection_reason TEXT,
  reviewer_id TEXT,
  injection_flags TEXT NOT NULL,
  artifact_path TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  retention_until TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  actor_role TEXT NOT NULL,
  action TEXT NOT NULL,
  resource_id TEXT,
  model TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  redaction_json TEXT NOT NULL,
  detail TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_ledger (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  retention_until TEXT NOT NULL,
  request_id TEXT,
  model TEXT NOT NULL,
  provider TEXT NOT NULL,
  input_tokens INTEGER NOT NULL,
  output_tokens INTEGER NOT NULL,
  cache_write_tokens INTEGER NOT NULL,
  cache_read_tokens INTEGER NOT NULL,
  cost_usd REAL NOT NULL,
  released INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_ledger(created_at);
CREATE INDEX IF NOT EXISTS idx_materials_status ON materials(status);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(materials)").fetchall()}
    if "artifact_path" not in columns:
        conn.execute("ALTER TABLE materials ADD COLUMN artifact_path TEXT")


@contextmanager
def session(path: Path) -> Iterator[sqlite3.Connection]:
    conn = connect(path)
    try:
        migrate(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
