"""Run the eval sets and write a pass-rate report.

The default provider is the local drafter, so the harness can run without an
API key. Pass --provider claude to call a model. Subjective rubric scores stay
blank unless --grade is set. This file does not claim a SCERT review.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from app.config import FAST_MODEL, STANDARD_MODEL, Settings
from app.db import session
from app.models import Actor, GenerateIn
from app.pipeline import create_draft

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
TEACHER = Actor(id="eval.teacher", role="teacher")
RUBRIC_CRITERIA = (
    "factual correctness",
    "syllabus fit",
    "difficulty",
    "language quality",
    "child appropriateness",
)


def load_cases(*names: str) -> list[dict]:
    rows = []
    for name in names:
        path = ROOT / name
        with path.open(encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    return rows


def grade_prompt(case: dict, material: dict) -> str:
    criteria = ", ".join(RUBRIC_CRITERIA)
    return (
        "Score this school draft from 1 to 5 on each criterion: "
        f"{criteria}. Return JSON only. "
        f"Case {case['id']} class {case['class_level']} {case['subject']} {case['topic']}. "
        f"Draft title: {material.get('title', '')}"
    )


def run_cases(cases: list[dict], settings: Settings, model: str) -> dict:
    records = []
    for case in cases:
        spec = GenerateIn(
            topic=case["topic"],
            class_level=case["class_level"],
            language=case["language"],
            task_type=case["task_type"],
            subject=case["subject"],
            n_questions=case["n_questions"],
            notes=case.get("notes") or "",
            model=model,
        )
        draft = create_draft(settings, TEACHER, spec)
        with session(settings.db_path) as conn:
            stored = conn.execute(
                "SELECT input_json, output_json, audit_log.redaction_json FROM materials LEFT JOIN audit_log ON audit_log.resource_id = materials.id WHERE materials.id = ?",
                (draft["id"],),
            ).fetchone()
        blob = f"{stored['input_json']}\n{stored['output_json'] or ''}\n{stored['redaction_json'] or ''}"
        stored_clean = "9876543210" not in blob and "PriyaZZ" not in blob and "12345678901" not in blob and "priya.zz@example.com" not in blob
        failed = [check["name"] for check in draft["checks"] if not check["passed"]]
        passed = draft["status"] == "pending" and not draft["official"] and draft["validation_passed"] and stored_clean
        records.append({
            "id": case["id"],
            "language": case["language"],
            "task_type": case["task_type"],
            "passed": passed,
            "official": draft["official"],
            "status": draft["status"],
            "failed_checks": failed,
            "stored_clean": stored_clean,
            "cost_usd": draft["cost_usd"],
            "input_tokens": None,
            "rubric": {name: None for name in RUBRIC_CRITERIA},
        })
    spent = round(sum(row["cost_usd"] for row in records), 6)
    return {
        "provider": settings.generate_mode,
        "model": model,
        "cases": len(records),
        "passed": sum(1 for row in records if row["passed"]),
        "cost_usd": spent,
        "cost_per_100_usd": round(spent / max(len(records), 1) * 100, 6),
        "scert_review": "Not done. The people who wrote this harness are not SCERT experts.",
        "spot_check_ids": [row["id"] for row in records if int(row["id"].split("-")[1]) % 10 == 0],
        "records": records,
    }


def _rate(rows: list[dict]) -> str:
    if not rows:
        return "—"
    passed = sum(1 for row in rows if row["passed"])
    return f"{passed}/{len(rows)} ({passed / len(rows):.0%})"


def render_report(result: dict) -> str:
    lines = [
        f"# Eval report: {result['model']}",
        "",
        f"Provider: {result['provider']}.",
        "Automatic checks only. Rubric cells are empty until a model grader or a person scores them.",
        result["scert_review"],
        "",
        f"Passed: {result['passed']} / {result['cases']}.",
        f"Estimated cost: ${result['cost_usd']:.4f}.",
        f"Estimated cost per 100 items: ${result['cost_per_100_usd']:.4f}.",
        "",
        "Spot-check about 10 percent. These ids are not yet reviewed by a person:",
        ", ".join(result["spot_check_ids"]) or "none",
        "",
        "| Language | Task | Result |",
        "| --- | --- | --- |",
    ]
    groups: dict[tuple[str, str], list] = defaultdict(list)
    for row in result["records"]:
        groups[(row["language"], row["task_type"])].append(row)
    for key in sorted(groups):
        lines.append(f"| {key[0]} | {key[1]} | {_rate(groups[key])} |")
    failed = [row for row in result["records"] if not row["passed"]]
    if failed:
        lines.extend(["", "Failed cases:"])
        for row in failed[:20]:
            lines.append(f"- {row['id']}: {', '.join(row['failed_checks']) or 'stored input was not clean'}")
    lines.append("")
    return "\n".join(lines)


def render_comparison(results: list[dict]) -> str:
    lines = [
        "# Model comparison",
        "",
        "Same cases, automatic checks. Latency is included only when a result file has it.",
        "A local row is a template drafter, not a Claude model.",
        "",
        "| Model | Provider | Cases | Auto pass | Cost USD | Cost / 100 |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        rate = result["passed"] / max(result["cases"], 1)
        lines.append(
            f"| {result['model']} | {result['provider']} | {result['cases']} | {rate:.0%} | "
            f"{result['cost_usd']:.4f} | {result['cost_per_100_usd']:.4f} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=("local", "claude"), default="local")
    parser.add_argument("--model", default=STANDARD_MODEL)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--compare", nargs="*", default=[])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.compare:
        loaded = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.compare]
        text = render_comparison(loaded)
        destination = RESULTS / "comparison.md"
        destination.write_text(text, encoding="utf-8")
        print(text)
        return
    if args.model not in {FAST_MODEL, STANDARD_MODEL}:
        raise SystemExit("Choose claude-haiku-5-5 or claude-sonnet-5-5.")
    cases = load_cases("cases_en.jsonl", "cases_hi.jsonl")
    if args.limit:
        cases = cases[: args.limit]
    settings = Settings(
        db_path=RESULTS / f"{args.provider}-{args.model}.sqlite",
        offline_db_path=RESULTS / "offline.sqlite",
        monthly_cap_usd=25,
        generate_mode=args.provider,
        model=args.model,
    )
    result = run_cases(cases, settings, args.model)
    slug = f"{args.provider}-{args.model}"
    (RESULTS / f"{slug}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report = render_report(result)
    (RESULTS / f"{slug}.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
