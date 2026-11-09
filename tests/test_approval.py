import pytest

from app.approval import ApprovalError, approve, edit, reject
from app.db import session
from app.generate import local_material
from app.models import GenerateIn
from app.pipeline import create_draft


def _hindi() -> GenerateIn:
    return GenerateIn(
        topic="भिन्न",
        class_level="5",
        language="hi",
        task_type="lesson_plan",
        subject="गणित",
        n_questions=2,
    )


def test_teacher_cannot_approve_and_officer_can(settings, teacher, officer, worksheet):
    draft = create_draft(settings, teacher, worksheet)
    assert draft["status"] == "pending"
    assert draft["official"] is False
    with session(settings.db_path) as conn:
        with pytest.raises(ApprovalError):
            approve(conn, draft["id"], teacher)
        approved = approve(conn, draft["id"], officer)
    assert approved["status"] == "approved"
    with session(settings.db_path) as conn:
        with pytest.raises(ApprovalError):
            approve(conn, draft["id"], officer)


def test_rejection_keeps_a_reason(settings, teacher, officer, worksheet):
    draft = create_draft(settings, teacher, worksheet)
    with session(settings.db_path) as conn:
        rejected = reject(conn, draft["id"], officer, "Too hard for this class.")
    assert rejected["status"] == "rejected"
    assert rejected["rejection_reason"] == "Too hard for this class."
    with session(settings.db_path) as conn:
        with pytest.raises(ApprovalError):
            approve(conn, draft["id"], officer)


def test_failed_checks_block_approval_until_an_edit_fixes_them(settings, teacher, officer, worksheet):
    material, _hint = local_material(worksheet)
    broken = material.model_copy(update={"sections": []})

    class Broken:
        provider = "fake"

        def generate(self, spec, notes):
            from app.models import Usage
            return broken, Usage(), _hint

    draft = create_draft(settings, teacher, worksheet, generator=Broken())
    assert draft["validation_passed"] is False
    with session(settings.db_path) as conn:
        with pytest.raises(ApprovalError):
            approve(conn, draft["id"], officer)
        edit(conn, draft["id"], officer, material)
        approved = approve(conn, draft["id"], officer)
    assert approved["status"] == "approved"


def test_personal_data_never_lands_in_the_database(settings, teacher, worksheet):
    spec = worksheet.model_copy(update={
        "notes": "Student name: PriyaZZ SharmaZZ. Phone 9876543210. Email priya.zz@example.com. Aadhaar 111122223333. School 12345678901.",
    })
    create_draft(settings, teacher, spec)
    stored = settings.db_path.read_bytes().decode("utf-8", errors="ignore")
    for secret in ("PriyaZZ", "9876543210", "priya.zz@example.com", "111122223333", "12345678901"):
        assert secret not in stored


def test_hindi_lesson_plan_stays_pending(settings, teacher):
    draft = create_draft(settings, teacher, _hindi())
    assert draft["validation_passed"] is True
    assert draft["status"] == "pending"
    assert draft["language"] == "hi"
