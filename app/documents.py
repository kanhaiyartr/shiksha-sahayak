"""Render a validated draft to PDF (worksheet) or DOCX (lesson plan, question bank).

Uses the same libraries as Anthropic's published pdf and docx skills: reportlab and
python-docx. Typesetting is local. There is no second Claude call.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.config import ROOT
from app.models import GeneratedMaterial

LATIN_FONT_PATH = ROOT / "app" / "fonts" / "NotoSans-Regular.ttf"
DEVANAGARI_FONT_PATH = ROOT / "app" / "fonts" / "NotoSansDevanagari-Regular.ttf"
LATIN_FONT = "NotoSans"
DEVANAGARI_FONT = "NotoSansDevanagari"
OUTPUT_DIR = ROOT / "data" / "outputs"

_FONT_READY = False


def _ensure_font() -> None:
    global _FONT_READY
    if _FONT_READY:
        return
    if not LATIN_FONT_PATH.is_file():
        raise FileNotFoundError(f"Missing Latin font at {LATIN_FONT_PATH}")
    if not DEVANAGARI_FONT_PATH.is_file():
        raise FileNotFoundError(f"Missing Devanagari font at {DEVANAGARI_FONT_PATH}")
    pdfmetrics.registerFont(TTFont(LATIN_FONT, str(LATIN_FONT_PATH)))
    pdfmetrics.registerFont(TTFont(DEVANAGARI_FONT, str(DEVANAGARI_FONT_PATH)))
    _FONT_READY = True


def _font_for(language: str) -> str:
    return DEVANAGARI_FONT if language == "hi" else LATIN_FONT


def _safe_stem(text: str) -> str:
    """ASCII-only stem so paths and Content-Disposition headers stay latin-1 safe.

    Hindi topics use Devanagari; putting those characters in a download filename
    makes Starlette raise UnicodeEncodeError and the UI hides the download button.
    """

    cleaned = re.sub(r"[^A-Za-z0-9_\-]+", "_", text).strip("_")
    return (cleaned or "draft")[:60]


def download_filename(path_name: str) -> str:
    """Header-safe attachment name. Always ASCII; UTF-8 form is optional via RFC 5987."""

    return _safe_stem(Path(path_name).stem) + Path(path_name).suffix.lower()


def content_disposition(filename: str) -> str:
    from urllib.parse import quote

    safe = download_filename(filename)
    if safe == filename:
        return f'attachment; filename="{safe}"'
    return f"attachment; filename=\"{safe}\"; filename*=UTF-8''{quote(filename)}"


def banner(status: str) -> str:
    if status == "approved":
        return "Official after officer approval."
    if status == "rejected":
        return "Rejected draft. Not for classroom use."
    return "DRAFT — pending officer approval. Not official."


def artifact_filename(material: GeneratedMaterial, material_id: str) -> str:
    # Topic is omitted from the on-disk name when non-ASCII (Hindi chapters).
    topic_part = _safe_stem(material.topic)
    stem = _safe_stem(
        f"{material.task_type}_{material.class_level}_{material.language}_{topic_part}_{material_id[:8]}"
    )
    if material.task_type == "worksheet":
        return f"{stem}.pdf"
    return f"{stem}.docx"


def media_type(task_type: str) -> str:
    if task_type == "worksheet":
        return "application/pdf"
    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_pdf(material: GeneratedMaterial, path: Path, status: str) -> None:
    _ensure_font()
    font_name = _font_for(material.language)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleDraft",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=16,
        leading=20,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "BodyDraft",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=15,
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "HeadingDraft",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=12,
        leading=16,
        spaceBefore=8,
        spaceAfter=4,
    )
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    story = [
        Paragraph(_escape(banner(status)), body_style),
        Spacer(1, 4),
        Paragraph(_escape(material.title), title_style),
        Paragraph(
            _escape(f"Class {material.class_level} · {material.subject} · {material.topic}"),
            body_style,
        ),
    ]
    for section in material.sections:
        story.append(Paragraph(_escape(section.heading), heading_style))
        story.append(Paragraph(_escape(section.body), body_style))
    for question in material.questions:
        story.append(Paragraph(_escape(f"{question.number}. {question.prompt}"), body_style))
    if material.answer_key and material.task_type != "lesson_plan":
        story.append(Paragraph(_escape("Answer key"), heading_style))
        for answer in material.answer_key:
            story.append(Paragraph(_escape(f"{answer.number}. {answer.answer}"), body_style))
    if material.teacher_notes.strip():
        story.append(Paragraph(_escape("Teacher notes"), heading_style))
        story.append(Paragraph(_escape(material.teacher_notes), body_style))
    for source in material.sources:
        story.append(Paragraph(_escape(f"Source: {source.title} — {source.locator}"), body_style))
        if source.quote.strip():
            story.append(Paragraph(_escape(source.quote), body_style))
    doc.build(story)


def render_docx(material: GeneratedMaterial, path: Path, status: str) -> None:
    document = Document()
    style = document.styles["Normal"]
    style.font.name = _font_for(material.language)
    style.font.size = Pt(11)
    document.add_paragraph(banner(status))
    document.add_heading(material.title, level=1)
    document.add_paragraph(f"Class {material.class_level} · {material.subject} · {material.topic}")
    for section in material.sections:
        document.add_heading(section.heading, level=2)
        document.add_paragraph(section.body)
    for question in material.questions:
        document.add_paragraph(f"{question.number}. {question.prompt}")
    if material.answer_key and material.task_type != "lesson_plan":
        document.add_heading("Answer key", level=2)
        for answer in material.answer_key:
            document.add_paragraph(f"{answer.number}. {answer.answer}")
    if material.teacher_notes.strip():
        document.add_heading("Teacher notes", level=2)
        document.add_paragraph(material.teacher_notes)
    for source in material.sources:
        document.add_paragraph(f"Source: {source.title} — {source.locator}")
        if source.quote.strip():
            document.add_paragraph(source.quote)
    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(path))


def write_artifact(material: GeneratedMaterial, material_id: str, status: str, output_dir: Path | None = None) -> Path:
    """Write the draft file and return its absolute path."""

    folder = output_dir or OUTPUT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / artifact_filename(material, material_id)
    if material.task_type == "worksheet":
        render_pdf(material, path, status)
    else:
        render_docx(material, path, status)
    return path


def delete_artifact(path_text: str | None) -> bool:
    if not path_text:
        return False
    path = Path(path_text)
    if path.is_file():
        path.unlink()
        return True
    return False
