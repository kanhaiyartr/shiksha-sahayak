"""Automatic checks. A draft can be approved only when every check passes."""

from __future__ import annotations

import re

from app.models import Check, GeneratedMaterial, GenerateIn, ValidationReport
from app.redact import output_breaks_rules, redact_text

HEADINGS: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "lesson_plan": [
        ("objectives", ("objectives", "उद्देश्य")),
        ("materials", ("materials", "सामग्री")),
        ("warm_up", ("warm-up", "warm up", "warmup", "शुरुआत")),
        ("teach", ("teach", "teaching", "शिक्षण")),
        ("practice", ("practice", "अभ्यास")),
        ("close", ("close", "closing", "समापन")),
        ("homework", ("homework", "गृहकार्य")),
    ],
    "worksheet": [("instructions", ("instructions", "निर्देश"))],
    "question_bank": [("how_to_use", ("how to use", "how to use this bank", "उपयोग"))],
}

UNSAFE = (
    re.compile(r"\bpornograph", re.I),
    re.compile(r"\bsexual intercourse\b", re.I),
    re.compile(r"\bkill yourself\b", re.I),
    re.compile(r"suicide method", re.I),
    re.compile(r"आत्महत्या का तरीका"),
    re.compile(r"अश्लील"),
)

READING_LIMIT = {
    "1": 10, "2": 12, "3": 14, "4": 15, "5": 16, "6": 18,
    "7": 20, "8": 22, "9": 24, "10": 24, "11": 26, "12": 26,
}


def _script_share(text: str) -> tuple[float, float]:
    devanagari = sum(1 for char in text if "\u0900" <= char <= "\u097f")
    latin = sum(1 for char in text if char.isascii() and char.isalpha())
    total = devanagari + latin
    if total == 0:
        return 0.0, 0.0
    return devanagari / total, latin / total


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[.!?।]+", text) if part.strip()]


def reading_stats(text: str) -> tuple[float, int]:
    parts = _sentences(text)
    if not parts:
        return 0.0, 0
    lengths = [len(part.split()) for part in parts]
    average = sum(lengths) / len(lengths)
    return average, max(lengths)


def _has_heading(material: GeneratedMaterial, aliases: tuple[str, ...]) -> bool:
    found = {section.heading.casefold().strip() for section in material.sections}
    return any(alias in found for alias in aliases)


def readable_text(material: GeneratedMaterial) -> str:
    parts = [material.title, material.subject, material.topic, material.teacher_notes]
    parts.extend(f"{section.heading}. {section.body}" for section in material.sections)
    parts.extend(question.prompt for question in material.questions)
    parts.extend(answer.answer for answer in material.answer_key)
    parts.extend(f"{source.title}. {source.quote}" for source in material.sources)
    finished = []
    for part in parts:
        text = part.strip()
        if not text:
            continue
        if text[-1] not in ".!?।":
            text += "."
        finished.append(text)
    return "\n".join(finished)


def validate_material(material: GeneratedMaterial, spec: GenerateIn) -> ValidationReport:
    checks: list[Check] = [Check(name="json_valid", passed=True, detail="The draft matches the schema.")]
    blob = material.model_dump_json()
    prose = readable_text(material)

    same = (
        material.language == spec.language
        and material.task_type == spec.task_type
        and material.class_level == spec.class_level
        and material.topic == spec.topic
        and material.subject == spec.subject
    )
    checks.append(Check(
        name="matches_request",
        passed=same,
        detail="Language, task, class, subject, and topic match the request." if same else "The draft does not match the request.",
    ))

    missing = [name for name, aliases in HEADINGS[spec.task_type] if not _has_heading(material, aliases)]
    checks.append(Check(
        name="sections",
        passed=not missing,
        detail="Required sections are present." if not missing else f"Missing sections: {', '.join(missing)}.",
    ))

    if spec.task_type == "lesson_plan":
        answers_ok = True
        answer_detail = "A lesson plan does not need an answer key."
        count_ok = True
        count_detail = "A lesson plan does not use a fixed question count."
    else:
        numbers = [question.number for question in material.questions]
        answers_ok = bool(material.questions) and {item.number for item in material.answer_key} >= set(numbers)
        answer_detail = (
            "An answer key covers the questions." if answers_ok else "The answer key is missing or incomplete."
        )
        count_ok = len(material.questions) == spec.n_questions and numbers == list(range(1, spec.n_questions + 1))
        count_detail = (
            f"{len(material.questions)} questions; {spec.n_questions} were requested."
        )
    checks.append(Check(name="question_count", passed=count_ok, detail=count_detail))
    checks.append(Check(
        name="answer_key",
        passed=answers_ok,
        detail=answer_detail,
    ))

    devanagari, latin = _script_share(prose)
    if spec.language == "hi":
        language_ok = devanagari >= 0.6
        language_detail = f"Devanagari share {devanagari:.2f}."
    else:
        language_ok = latin >= 0.75
        language_detail = f"Latin share {latin:.2f}."
    checks.append(Check(name="language", passed=language_ok, detail=language_detail))

    _, pii_counts = redact_text(blob)
    pii_ok = not pii_counts
    checks.append(Check(
        name="no_pii",
        passed=pii_ok,
        detail="No personal data found." if pii_ok else "Personal data was found in the draft.",
    ))

    banned = output_breaks_rules(blob)
    checks.append(Check(
        name="kept_rules",
        passed=not banned,
        detail="The draft stays inside the task." if not banned else "The draft repeats a blocked instruction.",
    ))

    unsafe = [pattern.pattern for pattern in UNSAFE if pattern.search(blob)]
    checks.append(Check(
        name="minor_safety",
        passed=not unsafe,
        detail="No blocked content found." if not unsafe else "Blocked content for a school draft.",
    ))

    average, longest = reading_stats(prose)
    limit = READING_LIMIT.get(spec.class_level, 18)
    reading_ok = average <= limit and longest <= limit + 6
    checks.append(Check(
        name="reading_level",
        passed=reading_ok,
        detail=f"Average sentence length {average:.1f} words. Longest {longest}. Limit {limit}.",
    ))

    cited = any(source.locator.strip() for source in material.sources)
    checks.append(Check(
        name="citation",
        passed=cited,
        detail="A source locator is present." if cited else "Add a source the teacher can check.",
    ))

    return ValidationReport(passed=all(check.passed for check in checks), checks=checks)
