# Sample monthly progress and cost note

Sample only. This is the note a builder would attach to the two-week plan. It matches the repository as it stands. It is not a department status report.

## Progress

| Days | Planned | State |
| --- | --- | --- |
| 1 | Repo, README, compliance skeleton | Done. `README.md`, `docs/compliance-map.md` |
| 2 | Synthetic data and a structured draft | Done. Local drafter and a live Haiku call both return the schema |
| 3 | Redaction and tests | Done. `tests/test_redact.py` |
| 4 | Validation and approval | Done. `tests/test_approval.py` |
| 5 | Audit, retention, cost cap | Done. `tests/test_audit.py`, `tests/test_cost.py` |
| 6 | Request, review, and approve screens | Done. `app/ui.py` |
| 7–8 | Hindi and English evals, two price tiers | Harness done, 100 of 100 automatic checks on the local drafter. Full live model run not spent |
| 9 | Prompt-injection tests | Done. `tests/test_injection.py` |
| 10 | Read-only MCP server | Done. `mcp_server/server.py` |
| 11 | Lesson-plan skill and read-only agent | Done |
| 12 | Batch script and cache measurement | Batch dry-run done. Live Haiku cache read measured |
| 13 | Compliance, risk, platforms, cost sample, staff guide | Done, in `docs/` |
| 14 | Docker, README, demo script | Docker Compose file is in the repo. Demo script is the click-path in the README. No recording is stored |

## Cost

The $5 cap was not reached.

The local Sonnet-priced eval of 100 drafts is an estimate of $0.9830, not an invoice. The same cases priced as Haiku are $0.0491.

Live Haiku spend on 8 November 2026 was a handful of worksheet calls, about $0.0005 each after the cache was warm, plus one warm-up call. Details are in `docs/cost-report-sample.md`.

## Blockers

A full quality comparison still needs a live run of both models and a human spot-check. The command is in the README. Do not quote the local 100% pass rate as a model score.
