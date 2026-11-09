# Platform comparison

The prototype calls the first-party Claude API. A department that already lives in AWS, Google Cloud, or Azure will ask why not Bedrock, Vertex AI, or Microsoft Foundry. This note is the comparison as of 8 November 2026. Feature lists move. Confirm them again before a procurement decision.

Sources used on that date:

- Claude pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Anthropic's own platform matrix: https://github.com/anthropics/skills/blob/main/skills/claude-api/shared/platform-availability.md
- Claude deployment overview: https://code.claude.com/docs/en/third-party-integrations
- Bedrock prompt caching: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html
- Vertex Claude prompt caching: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude/prompt-caching

| | First-party API | Amazon Bedrock | Vertex AI | Microsoft Foundry |
| --- | --- | --- | --- | --- |
| Where it runs | Anthropic | The AWS account | The Google Cloud project | Azure, or an Anthropic-hosted deployment billed through Microsoft |
| Identity | API key or Console | IAM | Google Cloud IAM | API key or Microsoft Entra ID |
| Audit trail the cloud already gives you | The Console usage page | CloudTrail | Cloud Audit Logs | Azure Monitor |
| Messages, tools, structured output | Yes | Yes | Yes | Yes |
| Prompt caching | Yes, including automatic caching | Yes on supported models. The older Bedrock path rejects a top-level `cache_control` and wants breakpoints on blocks. Caching is not available on Bedrock batch inference | Yes, 5-minute default, 1-hour optional | Yes |
| Token counting | Yes | Yes | Yes | Yes |
| Citations | Yes | Yes | Yes | Yes |
| Message Batches (50% off) | Yes | No | No | No |
| Managed agents | Beta on the first-party API | No | No | No |
| `inference_geo` for data residency | Yes | No (residency is the AWS region you pick) | No (residency is the Google Cloud region) | No (residency is the Azure region or the hosted deployment) |
| New models | First | Later | Later | Later |
| Why a department might still choose it | Fastest access to batches, caching, and new models | The account, the region, and the IAM rules already exist | Same, on Google Cloud | Same, on Azure, with Entra ID |

## What this means for the prototype

Batches, the cache measurement, and `messages.count_tokens` are first-party features. A move to Bedrock or Vertex would keep tool use, structured output, and prompt caching, and would drop the Batch API until that platform offers it. The approval queue, the redaction step, and the audit log would stay in this application either way. They are not provided by the model host.

Computer use is a beta tool on these platforms. This prototype does not turn it on. See `docs/risk-note.md`.

Prices in `app/cost.py` are first-party list prices. Bedrock, Vertex, and Foundry bill through their own price lists. Do not assume the same number.
