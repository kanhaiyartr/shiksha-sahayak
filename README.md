# Shiksha Sahayak

A prototype for teachers and officers. A teacher asks for a worksheet, a lesson plan, or a question bank. The draft is redacted, checked, and stored as **pending**. An officer approves or rejects it. Nothing in this app is official until that approval.

The school-data feature answers a question from a synthetic file. It cannot change the file, and the file has no pupils.

Default mode does not call Claude. It builds the draft from a chapter knowledge pack for the selected class, subject, and chapter so you can demo without spending money. Set `SHIKSHA_GENERATE_MODE=claude` for a live model call; Claude still must ground answers in the syllabus tool result.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest
uvicorn app.api:app --port 8000
streamlit run app/ui.py
```

Open http://127.0.0.1:8501. The API is http://127.0.0.1:8000.

Docker:

```bash
docker compose up --build
```

The UI is on port 8501 and the API is on port 8000. Compose starts in local mode.

## What to click

1. Leave the role as teacher. Choose Class 5, English, Mathematics, and the Fractions chapter. Ask for a worksheet. The screen shows a cost estimate and the remaining monthly budget before you submit.
2. Submit. The draft is pending. The checks are listed. Download the PDF. It is not official.
3. Change the role to officer. The staff id switches to `officer.anil`. Open Review, edit if needed, approve the draft, or reject it with a reason.
4. Open School data and ask: `How many schools in Uttarakhand have no electricity?` The answer cites rows in `data/synthetic_udise.csv`. The file uses the Uttarakhand state name and all of its districts. Every school row is still invented.
5. Open Budget. Local rows are estimates, not an invoice.

To see the waiting queue, stop the API and submit again. The request is stored after redaction. Start the API and use Send waiting requests.

## Layout

```
Browser (Streamlit)
   │
   ▼
FastAPI ── redaction ── Claude (tool call, then structured JSON) or the local drafter
   │
   ├── approval queue (SQLite)     pending → approved or rejected
   ├── audit log                   counts and actions, not raw personal data
   ├── usage ledger                tokens, price, monthly cap
   │
   └── read-only MCP / agent  ←── data/synthetic_udise.csv
```

Python 3.12 or newer. FastAPI, Pydantic v2, the Anthropic Python SDK, Streamlit, SQLite, pytest. The Docker image uses Python 3.12.

## Models and money

| | Input | Output | 5-minute cache write | Cache read | Batch input | Batch output |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| claude-sonnet-5-5 | $2 | $10 | $2.50 | $0.10 | $1 | $5 |
| claude-haiku-5-5 (under 100k tokens) | $0.10 | $0.50 | $0.125 | $0.01 | $0.05 | $0.25 |

USD per million tokens, from the [Claude pricing page](https://platform.claude.com/docs/en/about-claude/pricing) as of 8 November 2026. Haiku's higher rate above 100,000 tokens is not used here.

The monthly cap defaults to $5 and applies only to Claude API spend. Local drafts store a Claude-equivalent estimate for comparison and do not reduce the remaining budget. A Claude request that would cross the cap is not sent. The Budget screen shows billable spend and local estimates separately.

The pre-call quote treats the system prompt and the tool definition as a cache write of at least 2,731 tokens. That floor comes from a live Haiku call on 8 November 2026. A character count of the same text was much lower, and a low quote would let a request past the cap.

Two further live Haiku calls, after that warm-up, each read those 2,731 cached tokens and cost about $0.0005. Both drafts had four questions, an answer key, and the syllabus locator copied exactly. A short prompt with no tools did not cache, because it was under the cache minimum.

## Evals

Fifty English cases and fifty Hindi cases are in `evals/cases_en.jsonl` and `evals/cases_hi.jsonl`. The rubric is `evals/rubric.md`.

`python -m evals.run_evals` runs all 100 through the local drafter. That run is green on the automatic checks (schema, sections, answer key, language, reading length, citation, personal data, safety). It does not measure factual quality. The same template is used for both price tiers, so the pass rate does not compare the models. The cost column does, because each tier has its own price:

| Model | Provider | Cases | Automatic pass | Estimated USD | Per 100 |
| --- | --- | ---: | ---: | ---: | ---: |
| claude-sonnet-5-5 | local template | 100 | 100% | 0.9830 | 0.9830 |
| claude-haiku-5-5 | local template | 100 | 100% | 0.0491 | 0.0491 |

Reports: `evals/results/`. Ten case ids are listed for a human spot-check. They have not been reviewed. The authors are not SCERT experts. See `docs/scert-review.md`.

A live two-model run of the full sets:

```bash
export ANTHROPIC_API_KEY=...
python -m evals.run_evals --provider claude --model claude-haiku-5-5
python -m evals.run_evals --provider claude --model claude-sonnet-5-5
python -m evals.run_evals --compare evals/results/claude-claude-haiku-5-5.json evals/results/claude-claude-sonnet-5-5.json
```

That spends money. It was not run for all 100 cases. Subjective scores stay empty unless you add a grader. The automatic checks are the ones in `app/validate.py`.

## Safety, in the order they run

1. Personal data is removed before a model call, and again before a draft is stored. Tests cover email, Indian phone numbers, Aadhaar-shaped numbers, 11-digit school ids, and labeled names in English and Hindi. Synthetic school codes that start with `99` are kept so the data lookup can cite a row. Any other 11-digit id is removed.
2. Instructions inside the teacher's text are flagged and stripped. The system prompt does not contain that text. The model may call only `lookup_syllabus_hint`, and the lookup uses the teacher's topic, not the arguments the model sends.
3. The output must match the schema, include the required sections and an answer key, use the requested language, stay within a sentence-length limit, cite the syllabus hint, and avoid a short list of blocked content. A bad draft stays pending and cannot be approved.
4. Only the `officer` role can approve, reject, or edit. A rejection stores a reason. A teacher who calls approve gets a refusal.
5. The audit log stores the actor, role, action, model, token counts, and redaction counts. It does not store the matched personal data.
6. Each row has `retention_until`. `python scripts/purge_expired.py` deletes expired rows and writes a count, not the deleted text.
7. The MCP server and the agent expose the same five read tools. There is no write tool. Tests check that the CSV bytes do not change, and that a citation the model invents is dropped.

This is an engineering prototype. It is not a DPDP legal opinion, and the staff id header is not a login system.

## Other commands

```bash
python scripts/batch_worksheets.py --limit 4          # builds a Batch payload, does not send
python scripts/batch_worksheets.py --limit 4 --send   # sends it; needs ANTHROPIC_API_KEY
python scripts/measure_cache.py                       # prints the cache price difference
python scripts/measure_cache.py --live                # two short model calls
python scripts/purge_expired.py
python -m mcp_server.server                           # stdio MCP server
```

Claude Desktop or Claude Code can launch the MCP server with:

```json
{
  "mcpServers": {
    "shiksha-udise": {
      "command": ".venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/shiksha-sahayak"
    }
  }
}
```

Content skills: `skills/lesson-plan/SKILL.md`, `skills/worksheet/SKILL.md`, and `skills/question-bank/SKILL.md` shape accurate drafts. File skills: `skills/pdf/SKILL.md` and `skills/docx/SKILL.md` only typeset the finished object. The chapter packs live in `app/chapter_content.py`. The read-only agent is `agent/readonly_agent.py`.

## Documents

| File | What it is |
| --- | --- |
| `docs/compliance-map.md` | Rules 3.1–3.7 and the test that covers each one |
| `docs/risk-note.md` | Computer use, Chrome agents, managed agents |
| `docs/platform-comparison.md` | First-party API, Bedrock, Vertex AI, Microsoft Foundry |
| `docs/cost-report-sample.md` | Monthly report from the eval ledger, plus the live Haiku measurement |
| `docs/user-guide-staff.md` | Staff guide in English and Hindi |
| `docs/project-setup.md` | How to set up a Claude Project for staff |
| `docs/claude-plan-sample.md` | Sample plan |
| `docs/monthly-progress-sample.md` | Sample two-week progress note |
| `docs/workshop-outline.md` | 90-minute staff workshop |
| `docs/scert-review.md` | Simulated review procedure. Not a real SCERT review |

## Limits

- Unlabeled personal names in ordinary sentences are not reliably detected. The staff guide says not to type them at all.
- The local drafter repeats a short template. It is there so the queue, the checks, and the cap work without an API key.
- The keyword list for unsafe content is not a safety classifier. The officer is the control that matters.
- SQLite on one machine is not a department record system.
- Prices and platform features were checked on 8 November 2026 and will change.
- No video is included. The click-path above is the demo script.
