from io import BytesIO
from zipfile import ZipFile

from pypdf import PdfReader

from app.documents import write_artifact
from app.generate import local_material
from app.models import GenerateIn
from app.validate import validate_material


def test_worksheet_pdf_contains_answer_key(tmp_path):
    spec = GenerateIn(
        topic="Fractions",
        class_level="5",
        language="en",
        task_type="worksheet",
        subject="Mathematics",
        n_questions=4,
    )
    material, _hint = local_material(spec)
    path = write_artifact(material, "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "pending", tmp_path)
    assert path.suffix == ".pdf"
    assert path.name.isascii()
    raw = path.read_bytes()
    assert raw.startswith(b"%PDF")
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(raw)).pages)
    assert "Answer key" in text
    assert "DRAFT" in text
    assert "Fractions" in text


def test_hindi_worksheet_pdf_uses_ascii_filename(tmp_path):
    spec = GenerateIn(
        topic="भिन्न",
        class_level="5",
        language="hi",
        task_type="worksheet",
        subject="गणित",
        n_questions=4,
    )
    material, _hint = local_material(spec)
    path = write_artifact(material, "bbbbbbbb-cccc-dddd-eeee-ffffffffffff", "pending", tmp_path)
    assert path.suffix == ".pdf"
    assert path.name.isascii()
    assert "hi" in path.name
    assert path.read_bytes().startswith(b"%PDF")


def test_lesson_plan_docx_has_no_answer_key(tmp_path):
    spec = GenerateIn(
        topic="Fractions",
        class_level="5",
        language="en",
        task_type="lesson_plan",
        subject="Mathematics",
        n_questions=2,
    )
    material, _hint = local_material(spec)
    assert material.answer_key == []
    report = validate_material(material, spec)
    assert report.passed
    path = write_artifact(material, "11111111-2222-3333-4444-555555555555", "pending", tmp_path)
    assert path.suffix == ".docx"
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    assert "Answer key" not in xml
    assert "DRAFT" in xml
    assert "Objectives" in xml


def test_question_bank_docx_includes_answer_key(tmp_path):
    spec = GenerateIn(
        topic="Light",
        class_level="6",
        language="en",
        task_type="question_bank",
        subject="Science",
        n_questions=3,
    )
    material, _hint = local_material(spec)
    path = write_artifact(material, "99999999-aaaa-bbbb-cccc-dddddddddddd", "pending", tmp_path)
    assert path.suffix == ".docx"
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    assert "Answer key" in xml


def test_worksheet_without_answer_key_fails_validation():
    spec = GenerateIn(
        topic="Fractions",
        class_level="5",
        language="en",
        task_type="worksheet",
        subject="Mathematics",
        n_questions=4,
    )
    material, _hint = local_material(spec)
    broken = material.model_copy(update={"answer_key": []})
    report = validate_material(broken, spec)
    assert not report.passed
    assert any(check.name == "answer_key" and not check.passed for check in report.checks)
