"""Remove personal data and flag untrusted instructions before a model call.

The audit log stores counts and flag names only. It does not store the matched text.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from typing import Any

EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
AADHAAR = re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")
# 11-digit ids are treated as school ids, except the synthetic 99… codes this
# prototype uses so a read-only lookup can still cite a row.
SCHOOL_ID = re.compile(r"(?<!\d)(?!99)\d{11}(?!\d)")
PHONE = re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9](?:\d{9}|\d{4}[\s-]\d{5})(?!\d)")
NAME_EN = re.compile(
    r"(?i)\b(student(?:'s)? name|pupil name|child name|teacher name|parent name|"
    r"guardian name|name of (?:the )?(?:student|pupil|child))\s*[:\-]\s*([^,\n.]{2,60})"
)
NAME_HI = re.compile(
    r"(छात्र का नाम|विद्यार्थी का नाम|अभिभावक का नाम|शिक्षक का नाम|बच्चे का नाम)"
    r"\s*[:\-]\s*([^,\n।.]{2,60})"
)
MY_STUDENT = re.compile(r"(?i)\b(my (?:student|pupil|child))\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})")

INJECTION_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("ignore_previous", re.compile(r"ignore (?:all |any )?(?:previous|prior|above) (?:instructions|rules|prompts)", re.I)),
    ("disregard_rules", re.compile(r"disregard (?:all |the )?(?:above|previous|system|rules)", re.I)),
    ("reveal_system", re.compile(r"reveal (?:your |the )?(?:system prompt|hidden instructions)", re.I)),
    ("role_override", re.compile(r"you are now (?:a |an )?(?:system|admin|database|dan|jailbreak|unfiltered)", re.I)),
    ("student_list", re.compile(r"(?:output|print|reveal|show|dump) (?:the |all )?(?:full )?(?:student|pupil) (?:list|roster|data|names)", re.I)),
    ("hindi_ignore", re.compile(r"पिछले निर्देश")),
    ("hindi_students", re.compile(r"छात्र सूची|विद्यार्थी सूची")),
]

OUTPUT_BANS = (
    "ignore previous instructions",
    "leak_student_list",
    "here is the student list",
    "here is the full student list",
    "system prompt:",
)


@dataclass
class Prepared:
    text: str
    pii_counts: dict[str, int] = field(default_factory=dict)
    injection_flags: list[str] = field(default_factory=list)


def _count_sub(pattern: re.Pattern[str], text: str, token: str) -> tuple[str, int]:
    count = len(pattern.findall(text))
    if count == 0:
        return text, 0
    return pattern.sub(token, text), count


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    counts: dict[str, int] = {}
    updated = text
    steps: list[tuple[str, re.Pattern[str], str]] = [
        ("email", EMAIL, "[REDACTED_EMAIL]"),
        ("aadhaar", AADHAAR, "[REDACTED_AADHAAR]"),
        ("school_id", SCHOOL_ID, "[REDACTED_SCHOOL_ID]"),
        ("phone", PHONE, "[REDACTED_PHONE]"),
    ]
    for name, pattern, token in steps:
        updated, count = _count_sub(pattern, updated, token)
        if count:
            counts[name] = count

    def name_sub(match: re.Match[str]) -> str:
        return f"{match.group(1)}: [REDACTED_NAME]"

    for name, pattern in (("name", NAME_EN), ("name", NAME_HI)):
        found = pattern.findall(updated)
        if found:
            counts[name] = counts.get(name, 0) + len(found)
            updated = pattern.sub(name_sub, updated)

    mine = MY_STUDENT.findall(updated)
    if mine:
        counts["name"] = counts.get("name", 0) + len(mine)
        updated = MY_STUDENT.sub(r"\1 [REDACTED_NAME]", updated)
    return updated, counts


def _decode_line(line: str) -> str:
    compact = "".join(line.split())
    if not re.fullmatch(r"[A-Za-z0-9+/=]{16,}", compact):
        return ""
    try:
        raw = base64.b64decode(compact, validate=True)
    except Exception:
        return ""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return ""


def detect_injection(text: str) -> list[str]:
    flags: list[str] = []
    surfaces = [text]
    for line in text.splitlines():
        decoded = _decode_line(line)
        if decoded:
            surfaces.append(decoded)
    blob = "\n".join(surfaces)
    for name, pattern in INJECTION_RULES:
        if pattern.search(blob) and name not in flags:
            flags.append(name)
    return flags


def strip_injection(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        decoded = _decode_line(line)
        probe = f"{line}\n{decoded}"
        if any(pattern.search(probe) for _, pattern in INJECTION_RULES):
            kept.append("[REMOVED_UNTRUSTED_INSTRUCTION]")
        else:
            kept.append(line)
    return "\n".join(kept)


def prepare_text(text: str) -> Prepared:
    flags = detect_injection(text)
    redacted, counts = redact_text(text)
    stripped = strip_injection(redacted)
    return Prepared(text=stripped, pii_counts=counts, injection_flags=flags)


def prepare_value(value: Any) -> tuple[Any, dict[str, int], list[str]]:
    counts: dict[str, int] = {}
    flags: list[str] = []

    def walk(item: Any) -> Any:
        if isinstance(item, str):
            prepared = prepare_text(item)
            for key, count in prepared.pii_counts.items():
                counts[key] = counts.get(key, 0) + count
            for flag in prepared.injection_flags:
                if flag not in flags:
                    flags.append(flag)
            return prepared.text
        if isinstance(item, list):
            return [walk(part) for part in item]
        if isinstance(item, dict):
            return {key: walk(inner) if key != "model" else inner for key, inner in item.items()}
        return item

    return walk(value), counts, flags


def output_breaks_rules(text: str) -> list[str]:
    lowered = text.casefold()
    return [phrase for phrase in OUTPUT_BANS if phrase in lowered]
