# Compliance map

The prototype brief asked for rules 3.1 to 3.7. It did not include a separate legal text, so the seven rules below are the safety rules in that brief. Each one is implemented in code and covered by a test.

This is not a DPDP opinion. The app is built so that a teacher does not have to send personal data to a model, and so that a pasted name or number is removed before the call.

## Data minimisation

A request collects a class, language, task type, subject, chapter, question count, and an optional note. It does not collect a pupil record. The synthetic school file covers Uttarakhand and its districts only, with school totals: a fake code starting with 99, a made-up name, and aggregate enrolment. There is no pupil table.

If a note contains a name, phone, email, Aadhaar-shaped number, or a non-synthetic school id, that text is replaced before the model call and is not written to the database. The log stores the type and the count.

| Rule | What it requires | Where it lives | Check |
| --- | --- | --- | --- |
| 3.1 | Remove personal data before every model call | `app/redact.py`, called from `app/pipeline.py` before `generate` | `tests/test_redact.py`, `tests/test_approval.py` |
| 3.2 | Keep the system rules when the input contains instructions, and still send the output to approval | `app/generate.py` system prompt and tool allowlist; `app/redact.py` flags and strips the instruction; status is always `pending` in `create_draft` | `tests/test_injection.py` |
| 3.3 | Only an officer can approve. A rejection keeps a reason. Failed checks cannot be approved | `app/approval.py` | `tests/test_approval.py`, `tests/test_api.py` |
| 3.4 | Audit who, when, which model, token counts, and redaction actions. Do not store the raw personal data | `app/audit.py` | `tests/test_audit.py` |
| 3.5 | A retention date on each row, and a job that deletes expired rows | `retention_until` on every table; `scripts/purge_expired.py` | `tests/test_audit.py` |
| 3.6 | School-data tools are read-only | `mcp_server/catalog.py`, `mcp_server/server.py`, `agent/readonly_agent.py` | `tests/test_mcp.py`, `tests/test_agent.py` |
| 3.7 | Stop when the monthly cap is reached, and show the remaining budget | `app/cost.py`, `app/pipeline.py`, the request screen in `app/ui.py` | `tests/test_cost.py` |

## What "official" means here

`official` is true only when `status` is `approved`. The model schema has no status field. `approve` is the only function that sets that status, and it refuses a teacher and refuses a draft whose checks failed.

## Retention default

`SHIKSHA_RETENTION_DAYS` defaults to 90. The purge job deletes drafts, audit rows, usage rows, and waiting-queue items whose date has passed, then writes one new audit row that says rows were deleted. It does not copy the deleted text into that row.
