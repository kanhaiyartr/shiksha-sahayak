"""Read-only queries over the synthetic school file. There is no write function."""

from __future__ import annotations

import csv
import re
from functools import lru_cache

from app.config import ROOT

CSV_PATH = ROOT / "data" / "synthetic_udise.csv"
FACILITIES = frozenset({"electricity", "drinking_water", "functional_toilet"})
READ_ONLY_TOOLS = frozenset({
    "list_states",
    "list_districts",
    "enrolment_summary",
    "schools_missing_facility",
    "schools_by_enrolment",
    "get_school",
})
ROW_LIMIT = 20
RANK_LIMIT = 10


class UnknownTool(PermissionError):
    pass


_ROWS_MTIME: float | None = None


@lru_cache(maxsize=1)
def _cached_rows(_mtime: float) -> tuple[dict[str, str], ...]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def load_rows() -> tuple[dict[str, str], ...]:
    """Reload when the CSV changes on disk."""

    global _ROWS_MTIME
    mtime = CSV_PATH.stat().st_mtime if CSV_PATH.is_file() else 0.0
    if _ROWS_MTIME is not None and mtime != _ROWS_MTIME:
        _cached_rows.cache_clear()
    _ROWS_MTIME = mtime
    return _cached_rows(mtime)


def file_bytes() -> bytes:
    return CSV_PATH.read_bytes()


def _cite(locator: str, quote: str) -> dict[str, str]:
    return {
        "title": "Synthetic school dataset",
        "locator": locator,
        "quote": quote[:300],
    }


def _match_rows(state: str | None = None, district: str | None = None) -> list[dict[str, str]]:
    rows = list(load_rows())
    if state:
        rows = [row for row in rows if row["state"].casefold() == state.casefold()]
    if district:
        rows = [row for row in rows if row["district"].casefold() == district.casefold()]
    return rows


def list_states() -> list[str]:
    return sorted({row["state"] for row in load_rows()})


def list_all_districts() -> list[str]:
    return sorted({row["district"] for row in load_rows()})


def list_districts(state: str) -> dict:
    rows = _match_rows(state=state or None)
    districts = sorted({row["district"] for row in rows})
    label = state or "all"
    return {
        "state": label,
        "districts": districts,
        "citations": [_cite(f"synthetic_udise.csv#state={label}&column=district", ", ".join(districts) or "No rows.")],
    }


def enrolment_summary(state: str | None = None, district: str | None = None) -> dict:
    rows = _match_rows(state=state, district=district)
    enrolment = sum(int(row["enrolment"]) for row in rows)
    teachers = sum(int(row["teachers"]) for row in rows)
    label = district or state or "all"
    quote = f"{len(rows)} synthetic schools. Listed enrolment {enrolment}. Teachers {teachers}."
    return {
        "state": state or "all",
        "district": district or "",
        "schools": len(rows),
        "enrolment": enrolment,
        "teachers": teachers,
        "citations": [_cite(f"synthetic_udise.csv#place={label}&column=enrolment", quote)],
    }


def schools_missing_facility(
    facility: str,
    state: str | None = None,
    district: str | None = None,
) -> dict:
    if facility not in FACILITIES:
        raise ValueError("Unknown facility.")
    rows = [row for row in _match_rows(state=state, district=district) if row[facility] == "no"]
    shown = rows[:ROW_LIMIT]
    citations = [
        _cite(
            f"synthetic_udise.csv#udise_code={row['udise_code']}&column={facility}",
            f"{row['school_name']} in {row['district']}: {facility}=no. Synthetic row.",
        )
        for row in shown[:5]
    ]
    return {
        "facility": facility,
        "state": state or "all",
        "district": district or "",
        "count": len(rows),
        "shown": [
            {
                "udise_code": row["udise_code"],
                "school_name": row["school_name"],
                "district": row["district"],
                "state": row["state"],
            }
            for row in shown
        ],
        "citations": citations,
    }


def get_school(udise_code: str) -> dict:
    if not re.fullmatch(r"99\d{9}", udise_code or ""):
        return {"found": False, "citations": []}
    for row in load_rows():
        if row["udise_code"] == udise_code:
            public = {key: row[key] for key in row if key != "record_type"}
            quote = f"{row['school_name']}, enrolment {row['enrolment']}. Synthetic row."
            return {
                "found": True,
                "school": public,
                "citations": [_cite(f"synthetic_udise.csv#udise_code={udise_code}", quote)],
            }
    return {"found": False, "citations": []}


def schools_by_enrolment(
    limit: int = 5,
    order: str = "asc",
    state: str | None = None,
    district: str | None = None,
) -> dict:
    """Rank synthetic schools by listed enrolment. This is not a pupil name list."""

    try:
        count = int(limit)
    except (TypeError, ValueError):
        count = 5
    count = max(1, min(count, RANK_LIMIT))
    direction = (order or "asc").strip().lower()
    if direction not in {"asc", "desc"}:
        direction = "asc"
    rows = sorted(
        _match_rows(state=state, district=district),
        key=lambda row: (int(row["enrolment"]), row["udise_code"]),
        reverse=direction == "desc",
    )
    shown = rows[:count]
    citations = [
        _cite(
            f"synthetic_udise.csv#udise_code={row['udise_code']}&column=enrolment",
            f"{row['school_name']} in {row['district']}: enrolment {row['enrolment']}. Synthetic row.",
        )
        for row in shown
    ]
    return {
        "order": direction,
        "limit": count,
        "state": state or "all",
        "district": district or "",
        "schools": [
            {
                "udise_code": row["udise_code"],
                "school_name": row["school_name"],
                "district": row["district"],
                "state": row["state"],
                "enrolment": int(row["enrolment"]),
            }
            for row in shown
        ],
        "citations": citations,
        "note": "Listed enrolment is a school total. There are no pupil names in this file.",
    }


def dispatch(name: str, arguments: dict | None = None) -> dict | list:
    if name not in READ_ONLY_TOOLS:
        raise UnknownTool(f"Tool not allowed: {name}")
    arguments = arguments or {}
    if name == "list_states":
        return list_states()
    if name == "list_districts":
        return list_districts(str(arguments.get("state", "")))
    if name == "enrolment_summary":
        return enrolment_summary(
            arguments.get("state") or None,
            arguments.get("district") or None,
        )
    if name == "schools_missing_facility":
        return schools_missing_facility(
            str(arguments.get("facility", "")),
            arguments.get("state") or None,
            arguments.get("district") or None,
        )
    if name == "schools_by_enrolment":
        return schools_by_enrolment(
            arguments.get("limit", 5),
            str(arguments.get("order", "asc")),
            arguments.get("state") or None,
            arguments.get("district") or None,
        )
    if name == "get_school":
        return get_school(str(arguments.get("udise_code", "")))
    raise UnknownTool(name)


def collect_citations(payload) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(payload, dict):
        citations = payload.get("citations")
        if isinstance(citations, list):
            found.extend(item for item in citations if isinstance(item, dict) and "locator" in item)
        for value in payload.values():
            found.extend(collect_citations(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(collect_citations(item))
    return found
