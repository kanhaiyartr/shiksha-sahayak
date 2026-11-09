# Sample Claude plan

This is a sample plan a team would file before a pilot. It describes this prototype. It is not an approved department plan.

## Problem

Teachers spend hours writing worksheets and lesson plans. A model can draft them. A draft that reaches a classroom without a person checking it, or that contains a pupil's name, is the failure this plan is written to avoid.

## Users

Teachers request drafts. Officers approve, edit, or reject them. Both use one task per screen, because the connection may be poor and the training may be short.

## Scope of a first pilot

One subject pair, Mathematics and Science, classes 3 to 8, Hindi and English. Worksheets, lesson plans, and question banks only. No pupil data. No marks. No messages to parents. The school-data question uses the synthetic file until a real, read-only extract is agreed in writing.

## Controls that are already in the prototype

Redaction before the call. A fixed system prompt. One syllabus tool, with the model's arguments ignored. Schema and content checks. Officer approval. An audit log without raw personal data. A 90-day retention date and a deletion job. A $5 monthly cap, shown on the screen. Read-only data tools.

## Models

Start on `claude-haiku-5-5` for drafts. Compare `claude-sonnet-5-5` on the same 100 cases before using it as the default. Keep Sonnet for the cases Haiku fails. Prices and the comparison method are in the README.

## Eval before a wider trial

Automatic checks must pass. A person spot-checks about 10 percent against `evals/rubric.md`. That person is not, by default, an SCERT reviewer. An SCERT review is a separate step with real reviewers and the template in `docs/scert-review.md`. Do not describe this prototype's authors as that review.

## Rollout limit

Local mode for training. Then Haiku, with the cap. Then a decision on Sonnet using the cost per 100 items. Stop the pilot if officers cannot keep up with the pending queue, or if personal data appears in a stored draft.

## Out of scope

Computer use, browser agents, managed agents, write access to any school database, and any claim that a draft is official before approval.
