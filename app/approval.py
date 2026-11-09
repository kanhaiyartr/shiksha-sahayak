"""Pending, approved, and rejected. Only an officer can approve."""

from __future__ import annotations

import json
import sqlite3

from app.audit import write_audit
from app.models import Actor, GeneratedMaterial, GenerateIn, ValidationReport
from app.validate import validate_material
from app.redact import prepare_value


class ApprovalError(PermissionError):
    pass


def _load(conn: sqlite3.Connection, material_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
    if row is None:
        raise KeyError(material_id)
    return row


def _require_officer(actor: Actor) -> None:
    if actor.role != "officer":
        raise ApprovalError("Only an officer can approve, reject, or edit a draft.")


def _require_pending(row: sqlite3.Row) -> None:
    if row["status"] != "pending":
        raise ApprovalError(f"This draft is already {row['status']}.")


def approve(conn: sqlite3.Connection, material_id: str, actor: Actor) -> sqlite3.Row:
    _require_officer(actor)
    row = _load(conn, material_id)
    _require_pending(row)
    report = ValidationReport.model_validate_json(row["validation_json"])
    if not report.passed:
        raise ApprovalError("Fix the failed checks before approval. This draft is not official.")
    conn.execute(
        """
        UPDATE materials
        SET status = 'approved', reviewer_id = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (actor.id, material_id),
    )
    write_audit(
        conn,
        actor=actor,
        action="draft_approved",
        retention_until=row["retention_until"],
        resource_id=material_id,
        model=row["model"],
        input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"],
        detail=f"Approved {row['task_type']} for class {row['class_level']}.",
    )
    return _load(conn, material_id)


def reject(conn: sqlite3.Connection, material_id: str, actor: Actor, reason: str) -> sqlite3.Row:
    _require_officer(actor)
    row = _load(conn, material_id)
    _require_pending(row)
    cleaned, counts, flags = prepare_value(reason.strip())
    if not str(cleaned).strip():
        raise ApprovalError("A rejection needs a reason.")
    conn.execute(
        """
        UPDATE materials
        SET status = 'rejected', reviewer_id = ?, rejection_reason = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (actor.id, str(cleaned)[:500], material_id),
    )
    write_audit(
        conn,
        actor=actor,
        action="draft_rejected",
        retention_until=row["retention_until"],
        resource_id=material_id,
        model=row["model"],
        redaction={"pii": counts, "injection_flags": flags},
        detail="Rejected. The reason is stored after redaction.",
    )
    return _load(conn, material_id)


def edit(conn: sqlite3.Connection, material_id: str, actor: Actor, material: GeneratedMaterial) -> sqlite3.Row:
    _require_officer(actor)
    row = _load(conn, material_id)
    _require_pending(row)
    cleaned, counts, flags = prepare_value(json.loads(material.model_dump_json()))
    edited = GeneratedMaterial.model_validate(cleaned)
    spec = GenerateIn(
        topic=row["topic"],
        class_level=row["class_level"],
        language=row["language"],
        task_type=row["task_type"],
        subject=row["subject"],
        n_questions=row["n_questions"],
    )
    report = validate_material(edited, spec)
    conn.execute(
        """
        UPDATE materials
        SET output_json = ?, validation_json = ?, reviewer_id = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (edited.model_dump_json(), report.model_dump_json(), actor.id, material_id),
    )
    write_audit(
        conn,
        actor=actor,
        action="draft_edited",
        retention_until=row["retention_until"],
        resource_id=material_id,
        model=row["model"],
        redaction={"pii": counts, "injection_flags": flags},
        detail="Officer edited the pending draft. It is still not official.",
    )
    return _load(conn, material_id)
