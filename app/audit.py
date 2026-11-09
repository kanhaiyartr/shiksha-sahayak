"""Audit log writes and the retention deletion job.

Rows store who, when, which model, token counts, and redaction counts.
They do not store raw personal data.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.db import session
from app.models import Actor


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat()


def retention_deadline(days: int, moment: datetime | None = None) -> str:
    start = moment or utcnow()
    return iso(start + timedelta(days=days))


def write_audit(
    conn: sqlite3.Connection,
    *,
    actor: Actor,
    action: str,
    retention_until: str,
    resource_id: str | None = None,
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    redaction: dict | None = None,
    detail: str = "",
) -> str:
    audit_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO audit_log (
          id, created_at, retention_until, actor_id, actor_role, action, resource_id,
          model, input_tokens, output_tokens, redaction_json, detail
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            iso(utcnow()),
            retention_until,
            actor.id,
            actor.role,
            action,
            resource_id,
            model,
            input_tokens,
            output_tokens,
            json.dumps(redaction or {}, ensure_ascii=False, sort_keys=True),
            detail[:500],
        ),
    )
    return audit_id


def purge_expired(path: Path, *, now: datetime | None = None) -> dict[str, int]:
    from app.documents import delete_artifact

    moment = iso(now or utcnow())
    counts: dict[str, int] = {}
    with session(path) as conn:
        expired = conn.execute(
            "SELECT artifact_path FROM materials WHERE retention_until < ?",
            (moment,),
        ).fetchall()
        deleted_files = 0
        for row in expired:
            path_text = row["artifact_path"] if "artifact_path" in row.keys() else None
            if delete_artifact(path_text):
                deleted_files += 1
        counts["artifact_files"] = deleted_files
        for table in ("materials", "audit_log", "usage_ledger"):
            cursor = conn.execute(f"DELETE FROM {table} WHERE retention_until < ?", (moment,))
            counts[table] = cursor.rowcount
        deadline = retention_deadline(90)
        write_audit(
            conn,
            actor=Actor(id="system.retention", role="officer"),
            action="retention_purged",
            retention_until=deadline,
            redaction={},
            detail="Deleted expired rows and draft files. Counts only, no row contents.",
        )
    return counts
