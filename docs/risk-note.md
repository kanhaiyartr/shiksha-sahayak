# Risk note: computer use, Chrome agents, managed agents

Checked against Anthropic's platform notes on 8 November 2026. This prototype enables none of the three.

## Computer use

Computer use lets a model click, type, and read a real desktop. A hostile line in a document or a web page can ask it to open mail, change a record, or copy a file. The damage is not limited to the text it returns.

Shiksha Sahayak does not request a computer-use tool. The generation path allows one tool, `lookup_syllabus_hint`, and then ignores the arguments the model sends. The data agent allows five read tools and rejects any other name in code.

## Chrome and other browser agents

A browser agent acts inside a logged-in session. If that session is a school portal or an officer's email, an instruction hidden on a page can ride the login. The agent cannot tell a page's text from an order.

This app has no browser tool and no page fetcher. The only external text it trusts is the syllabus hint file shipped in the repo, and the synthetic CSV. Teacher text is wrapped as untrusted input.

## Managed agents

A managed agent keeps credentials and can continue after the person has looked away. A long-running agent with a write tool can approve, email, or edit records on its own.

This prototype has no managed agent. A draft stops in `pending`. A person with the officer role has to approve it. The data agent stops after four tool rounds. There is no write tool for it to call on a later round.

## What would have to be true before any of these were turned on

A named officer would have to approve the exact action, the tool list would stay an allowlist in code, the agent would have no access to pupil records, and the run would have a step limit and a log. None of that is built here, because the safe default is not to give the model those tools.
