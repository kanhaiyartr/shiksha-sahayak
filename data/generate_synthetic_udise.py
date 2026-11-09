"""Write data/synthetic_udise.csv. Every row is invented. There are no pupils.

The file covers one state name, Uttarakhand, and all of its districts.
"""

from __future__ import annotations

import csv
from pathlib import Path

COLUMNS = [
    "udise_code",
    "school_name",
    "state",
    "district",
    "block",
    "management",
    "category",
    "location",
    "enrolment",
    "teachers",
    "classrooms",
    "electricity",
    "drinking_water",
    "functional_toilet",
    "medium",
    "record_type",
]

STATE = "Uttarakhand"
DISTRICTS = [
    ("Almora", "Almora Block"),
    ("Bageshwar", "Bageshwar Block"),
    ("Chamoli", "Chamoli Block"),
    ("Champawat", "Champawat Block"),
    ("Dehradun", "Dehradun Block"),
    ("Haridwar", "Haridwar Block"),
    ("Nainital", "Nainital Block"),
    ("Pauri Garhwal", "Pauri Block"),
    ("Pithoragarh", "Pithoragarh Block"),
    ("Rudraprayag", "Rudraprayag Block"),
    ("Tehri Garhwal", "Tehri Block"),
    ("Udham Singh Nagar", "Rudrapur Block"),
    ("Uttarkashi", "Uttarkashi Block"),
]
TREES = ["Neem", "Peepal", "Banyan", "Sal", "Jamun", "Bamboo", "Kadam", "Arjun"]
CATEGORIES = ["Primary", "Upper Primary", "Secondary"]
MANAGEMENTS = ["Department of Education", "Aided"]
MEDIUMS = ["Hindi", "English", "Hindi and English"]


def build_rows(count: int = 78, seed: int = 20261109) -> list[dict[str, str]]:
    del seed  # The formula below is already fixed. The argument records the dataset version.
    rows = []
    for number in range(1, count + 1):
        district, block = DISTRICTS[(number - 1) % len(DISTRICTS)]
        category = CATEGORIES[(number - 1) % len(CATEGORIES)]
        rows.append({
            "udise_code": f"99{number:09d}",
            "school_name": f"{TREES[(number - 1) % len(TREES)]} {category} School {number}",
            "state": STATE,
            "district": district,
            "block": block,
            "management": MANAGEMENTS[number % len(MANAGEMENTS)],
            "category": category,
            "location": "rural" if number % 2 == 0 else "urban",
            "enrolment": str(40 + (number * 7) % 220),
            "teachers": str(2 + number % 9),
            "classrooms": str(2 + number % 12),
            "electricity": "no" if number % 5 == 0 else "yes",
            "drinking_water": "no" if number % 7 == 0 else "yes",
            "functional_toilet": "no" if number % 11 == 0 else "yes",
            "medium": MEDIUMS[number % len(MEDIUMS)],
            "record_type": "synthetic",
        })
    return rows


def main() -> None:
    path = Path(__file__).resolve().parent / "synthetic_udise.csv"
    rows = build_rows()
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic schools to {path}")


if __name__ == "__main__":
    main()
