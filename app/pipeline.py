"""Create a pending draft. Approval state is applied only in approval.py."""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.approval import approve, edit, reject
from app.audit import iso, retention_deadline, utcnow, write_audit
from app.config import Settings
from app.cost import (
    OUTPUT_TOKEN_ESTIMATE,
    BudgetError,
    billable_cost,
    cache_warm_for_model,
    cost_usd,
    estimated_local_this_month,
    month_key,
    remaining,
    render_monthly_report,
    spent_this_month,
    usage_by_model,
)
from app.db import session
from app.documents import media_type, write_artifact
from app.generate import (
    ClaudeGenerator,
    EmptyTopicError,
    LocalGenerator,
    ModelOutputError,
    prompt_token_split,
)  # LocalGenerator used for cache-aware local pricing
from app.models import Actor, Check, GeneratedMaterial, GenerateIn, Usage, ValidationReport
from app.redact import prepare_value
from app.validate import validate_material

_REDACTION_TOKENS = (
    "[REDACTED_EMAIL]",
    "[REDACTED_PHONE]",
    "[REDACTED_AADHAAR]",
    "[REDACTED_SCHOOL_ID]",
    "[REDACTED_NAME]",
    "[REMOVED_UNTRUSTED_INSTRUCTION]",
)


def substantive(text: str) -> str:
    cleaned = text
    for token in _REDACTION_TOKENS:
        cleaned = cleaned.replace(token, " ")
    return " ".join(cleaned.split())


def prepare_request(spec: GenerateIn) -> tuple[GenerateIn, dict[str, int], list[str]]:
    cleaned, counts, flags = prepare_value(spec.model_dump())
    prepared = GenerateIn.model_validate(cleaned)
    if len(substantive(prepared.topic)) < 2:
        raise EmptyTopicError("The topic was empty after personal data was removed. Rewrite it without personal data.")
    return prepared, counts, flags


def _generator(settings: Settings, model: str):
    if settings.generate_mode == "local":
        return LocalGenerator(model)
    from anthropic import Anthropic

    return ClaudeGenerator(Anthropic(), model)


def _store_redacted(material: GeneratedMaterial) -> tuple[GeneratedMaterial, dict[str, int]]:
    cleaned, counts, _flags = prepare_value(json.loads(material.model_dump_json()))
    return GeneratedMaterial.model_validate(cleaned), counts


def estimate(settings: Settings, spec: GenerateIn) -> dict[str, Any]:
    prepared, counts, flags = prepare_request(spec)
    model = settings.resolved_model(prepared.model)
    system_tokens, user_tokens = prompt_token_split(prepared, prepared.notes)
    output_tokens = OUTPUT_TOKEN_ESTIMATE[prepared.task_type]
    first = cost_usd(model, user_tokens, output_tokens, cache_write_tokens=system_tokens)
    cached = cost_usd(model, user_tokens, output_tokens, cache_read_tokens=system_tokens)
    provider = settings.generate_mode
    with session(settings.db_path) as conn:
        left = remaining(conn, settings.monthly_cap_usd)
        warm = cache_warm_for_model(conn, model)
    likely = cached if warm else first
    against_cap = billable_cost(provider, likely)
    return {
        "model": model,
        "provider": provider,
        "input_tokens": user_tokens,
        "cache_tokens": system_tokens,
        "output_tokens": output_tokens,
        "first_request_usd": first,
        "cached_request_usd": cached,
        "likely_request_usd": likely,
        "counts_against_cap_usd": against_cap,
        "remaining_usd": left,
        "within_cap": against_cap <= left + 1e-9,
        "cache_likely_hit": warm,
        "pii_counts": counts,
        "injection_flags": flags,
        "note": (
            "Local mode: Claude-equivalent estimate shown. $0 counts against the monthly cap."
            if provider == "local"
            else "Claude mode: this amount is billed and counts against the monthly cap after the call."
        ),
    }


def _view(row, left: float) -> dict[str, Any]:
    report = json.loads(row["validation_json"])
    artifact = row["artifact_path"] if "artifact_path" in row.keys() else None
    return {
        "id": row["id"],
        "status": row["status"],
        "official": row["status"] == "approved",
        "provider": row["provider"],
        "model": row["model"],
        "cost_usd": row["cost_usd"],
        "remaining_usd": left,
        "validation_passed": report["passed"],
        "checks": report["checks"],
        "material": json.loads(row["output_json"]) if row["output_json"] else None,
        "rejection_reason": row["rejection_reason"],
        "topic": row["topic"],
        "subject": row["subject"],
        "task_type": row["task_type"],
        "language": row["language"],
        "class_level": row["class_level"],
        "created_at": row["created_at"],
        "actor_id": row["actor_id"],
        "reviewer_id": row["reviewer_id"],
        "injection_flags": json.loads(row["injection_flags"]),
        "artifact_path": artifact,
        "has_file": bool(artifact),
        "file_media_type": media_type(row["task_type"]) if artifact else None,
    }


def _store_artifact(conn, material: GeneratedMaterial, material_id: str, status: str) -> str:
    path = write_artifact(material, material_id, status)
    conn.execute(
        "UPDATE materials SET artifact_path = ?, updated_at = datetime('now') WHERE id = ?",
        (str(path), material_id),
    )
    return str(path)


def create_draft(settings: Settings, actor: Actor, spec: GenerateIn, generator=None) -> dict[str, Any]:
    prepared, counts, flags = prepare_request(spec)
    model = settings.resolved_model(prepared.model)
    quote = estimate(settings, prepared)
    # Cap only blocks real Claude spend. Local drafts never consume the budget.
    if settings.generate_mode == "claude" and not quote["within_cap"]:
        with session(settings.db_path) as conn:
            write_audit(
                conn,
                actor=actor,
                action="draft_blocked_budget",
                retention_until=retention_deadline(settings.retention_days),
                model=model,
                redaction={"pii": counts, "injection_flags": flags},
                detail="Stopped before the Claude call because the monthly cap would be exceeded.",
            )
        raise BudgetError(
            f"Monthly cap reached. This request was not sent. Remaining ${quote['remaining_usd']:.4f}."
        )

    generator = generator or _generator(settings, model)
    hint: dict[str, str] | None = None
    try:
        if isinstance(generator, LocalGenerator):
            with session(settings.db_path) as conn:
                warm = cache_warm_for_model(conn, model)
            material, usage, hint = generator.generate(prepared, prepared.notes, cache_warm=warm)
        else:
            material, usage, hint = generator.generate(prepared, prepared.notes)
        material, output_counts = _store_redacted(material)
        for key, count in output_counts.items():
            counts[key] = counts.get(key, 0) + count
        report = validate_material(material, prepared)
        if hint is not None:
            grounded = any(source.locator == hint["locator"] for source in material.sources)
            report.checks.append(Check(
                name="grounded_citation",
                passed=grounded,
                detail="The citation matches the syllabus hint." if grounded else "The citation does not match the syllabus hint.",
            ))
            report.passed = report.passed and grounded
        output_json = material.model_dump_json()
        provider = generator.provider
    except (ModelOutputError, PermissionError):
        material = None
        usage = Usage()
        report = ValidationReport(passed=False, checks=[
            Check(name="json_valid", passed=False, detail="The model did not return a usable draft. Nothing was approved."),
            Check(name="kept_rules", passed=False, detail="The draft stays pending."),
        ])
        output_json = None
        provider = getattr(generator, "provider", settings.generate_mode)

    # Store the priced amount for both providers. Cap accounting only sums provider=claude.
    price = cost_usd(
        model,
        usage.input_tokens,
        usage.output_tokens,
        usage.cache_write_tokens,
        usage.cache_read_tokens,
    )
    draft_id = str(uuid.uuid4())
    created = iso(utcnow())
    deadline = retention_deadline(settings.retention_days)
    with session(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO materials (
              id, created_at, updated_at, retention_until, actor_id, actor_role, status,
              task_type, class_level, language, subject, topic, n_questions, input_json,
              output_json, validation_json, model, provider, input_tokens, output_tokens,
              cache_write_tokens, cache_read_tokens, cost_usd, rejection_reason, reviewer_id,
              injection_flags
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
            """,
            (
                draft_id, created, created, deadline, actor.id, actor.role,
                prepared.task_type, prepared.class_level, prepared.language, prepared.subject,
                prepared.topic, prepared.n_questions,
                json.dumps(prepared.model_dump(), ensure_ascii=False),
                output_json, report.model_dump_json(), model, provider,
                usage.input_tokens, usage.output_tokens, usage.cache_write_tokens,
                usage.cache_read_tokens, price, json.dumps(flags),
            ),
        )
        conn.execute(
            """
            INSERT INTO usage_ledger (
              id, created_at, retention_until, request_id, model, provider, input_tokens,
              output_tokens, cache_write_tokens, cache_read_tokens, cost_usd, released
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                str(uuid.uuid4()), created, deadline, draft_id, model, provider,
                usage.input_tokens, usage.output_tokens, usage.cache_write_tokens,
                usage.cache_read_tokens, price,
            ),
        )
        write_audit(
            conn,
            actor=actor,
            action="draft_created",
            retention_until=deadline,
            resource_id=draft_id,
            model=model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            redaction={"pii": counts, "injection_flags": flags},
            detail=f"Pending {prepared.task_type} in {prepared.language}, class {prepared.class_level}, provider {provider}.",
        )
        if material is not None:
            _store_artifact(conn, material, draft_id, "pending")
        row = conn.execute("SELECT * FROM materials WHERE id = ?", (draft_id,)).fetchone()
        left = remaining(conn, settings.monthly_cap_usd)
    return _view(row, left)


def list_drafts(settings: Settings, status: str | None = None) -> list[dict[str, Any]]:
    with session(settings.db_path) as conn:
        if status:
            rows = conn.execute("SELECT * FROM materials WHERE status = ? ORDER BY created_at", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM materials ORDER BY created_at").fetchall()
        left = remaining(conn, settings.monthly_cap_usd)
    return [_view(row, left) for row in rows]


def get_draft(settings: Settings, material_id: str) -> dict[str, Any]:
    with session(settings.db_path) as conn:
        row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        if row is None:
            raise KeyError(material_id)
        left = remaining(conn, settings.monthly_cap_usd)
    return _view(row, left)


def budget(settings: Settings) -> dict[str, Any]:
    with session(settings.db_path) as conn:
        billable = spent_this_month(conn)
        local_est = estimated_local_this_month(conn)
        left = remaining(conn, settings.monthly_cap_usd)
        return {
            "month": month_key(),
            "cap_usd": settings.monthly_cap_usd,
            "spent_usd": billable,
            "billable_usd": billable,
            "local_estimated_usd": local_est,
            "remaining_usd": left,
            "generate_mode": settings.generate_mode,
            "by_model": usage_by_model(conn),
            "report_markdown": render_monthly_report(conn, settings.monthly_cap_usd),
        }


def officer_approve(settings: Settings, actor: Actor, material_id: str) -> dict[str, Any]:
    with session(settings.db_path) as conn:
        approve(conn, material_id, actor)
        row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        if row["output_json"]:
            material = GeneratedMaterial.model_validate_json(row["output_json"])
            _store_artifact(conn, material, material_id, "approved")
            row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        left = remaining(conn, settings.monthly_cap_usd)
    return _view(row, left)


def officer_reject(settings: Settings, actor: Actor, material_id: str, reason: str) -> dict[str, Any]:
    with session(settings.db_path) as conn:
        reject(conn, material_id, actor, reason)
        row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        if row["output_json"]:
            material = GeneratedMaterial.model_validate_json(row["output_json"])
            _store_artifact(conn, material, material_id, "rejected")
            row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        left = remaining(conn, settings.monthly_cap_usd)
    return _view(row, left)


def officer_edit(settings: Settings, actor: Actor, material_id: str, material: GeneratedMaterial) -> dict[str, Any]:
    with session(settings.db_path) as conn:
        edit(conn, material_id, actor, material)
        row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        if row["output_json"]:
            edited = GeneratedMaterial.model_validate_json(row["output_json"])
            _store_artifact(conn, edited, material_id, row["status"])
            row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        left = remaining(conn, settings.monthly_cap_usd)
    return _view(row, left)


def read_artifact(settings: Settings, material_id: str) -> tuple[bytes, str, str]:
    with session(settings.db_path) as conn:
        row = conn.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
        if row is None:
            raise KeyError(material_id)
        path_text = row["artifact_path"] if "artifact_path" in row.keys() else None
        if not path_text:
            raise FileNotFoundError(material_id)
        from pathlib import Path

        path = Path(path_text)
        if not path.is_file():
            raise FileNotFoundError(material_id)
        name = path.name
        return path.read_bytes(), media_type(row["task_type"]), name
