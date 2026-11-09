import json
from pathlib import Path

from evals.run_evals import load_cases, render_comparison
from scripts.batch_worksheets import build_batch_requests


def test_each_language_has_between_40_and_60_cases():
    english = load_cases("cases_en.jsonl")
    hindi = load_cases("cases_hi.jsonl")
    assert 40 <= len(english) <= 60
    assert 40 <= len(hindi) <= 60
    assert {row["language"] for row in english} == {"en"}
    assert {row["language"] for row in hindi} == {"hi"}


def test_batch_payload_is_structured_and_cached():
    case = {
        "id": "en-001",
        "topic": "Fractions",
        "class_level": "5",
        "language": "en",
        "task_type": "worksheet",
        "subject": "Mathematics",
        "n_questions": 4,
        "notes": "",
    }
    request = build_batch_requests([case])[0]
    assert request["custom_id"] == "en-001"
    assert request["params"]["system"][0]["cache_control"]["type"] == "ephemeral"
    assert request["params"]["output_config"]["format"]["type"] == "json_schema"
    assert "<syllabus_hint>" in request["params"]["messages"][0]["content"]
    assert "<untrusted_teacher_input>" in request["params"]["messages"][0]["content"]


def test_comparison_table_reads_two_result_files(tmp_path: Path):
    rows = []
    for model, provider in (("claude-haiku-5-5", "claude"), ("claude-sonnet-5-5", "claude")):
        payload = {"model": model, "provider": provider, "cases": 10, "passed": 8, "cost_usd": 0.2, "cost_per_100_usd": 2.0}
        path = tmp_path / f"{model}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        rows.append(payload)
    text = render_comparison(rows)
    assert "claude-haiku-5-5" in text
    assert "claude-sonnet-5-5" in text
    assert "80%" in text
