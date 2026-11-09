import json

from app.audit import purge_expired, write_audit
from app.db import session
from app.models import Actor
from app.pipeline import create_draft


def test_purge_deletes_expired_rows_and_logs_the_deletion(settings, teacher, worksheet):
    draft = create_draft(settings, teacher, worksheet)
    with session(settings.db_path) as conn:
        for table in ("materials", "audit_log", "usage_ledger"):
            conn.execute(f"UPDATE {table} SET retention_until = '2000-01-01T00:00:00+00:00'")
        conn.execute(
            "INSERT INTO audit_log (id, created_at, retention_until, actor_id, actor_role, action, resource_id, model, input_tokens, output_tokens, redaction_json, detail) VALUES ('keep', '2000-01-01T00:00:00+00:00', '2999-01-01T00:00:00+00:00', 'officer.anil', 'officer', 'note', NULL, NULL, NULL, NULL, '{}', 'kept')"
        )
    counts = purge_expired(settings.db_path)
    assert counts["materials"] >= 1
    with session(settings.db_path) as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM materials").fetchone()["n"] == 0
        actions = [row["action"] for row in conn.execute("SELECT action FROM audit_log ORDER BY action")]
    assert "retention_purged" in actions
    assert "note" in actions
    assert draft["id"] not in settings.db_path.read_text(encoding="utf-8", errors="ignore")


def test_audit_rows_have_actor_model_and_counts_without_raw_text(settings, teacher, worksheet):
    spec = worksheet.model_copy(update={"notes": "Phone 9876543210"})
    draft = create_draft(settings, teacher, spec)
    with session(settings.db_path) as conn:
        row = conn.execute(
            "SELECT * FROM audit_log WHERE action = 'draft_created' AND resource_id = ?",
            (draft["id"],),
        ).fetchone()
    assert row["actor_id"] == teacher.id
    assert row["actor_role"] == "teacher"
    assert row["model"]
    assert row["input_tokens"] > 0
    redaction = json.loads(row["redaction_json"])
    assert redaction["pii"]["phone"] == 1
    assert "9876543210" not in row["redaction_json"]
    assert "9876543210" not in row["detail"]
    Actor(id="system.retention", role="officer")
    assert write_audit
