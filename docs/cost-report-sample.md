# Monthly cost report — sample

Two different things are below. The table is the app's own report for the local eval run of 100 drafts, priced as Sonnet 5.5. Those rows did not call the API. The second section is a real Haiku measurement from 8 November 2026.

Cap for the sample: $5.00. The report text is what `render_monthly_report` produces after local vs billable accounting.

```
# Monthly cost report 2026-11

Cap (billable Claude only): $5.00
Billable Claude spend: $0.000000
Remaining under cap: $5.000000
Local Claude-equivalent estimate (not billed): $0.982952

Only provider=claude rows reduce the remaining budget.
Local rows are priced as if Claude ran, for comparison. They are not an invoice.
Prices: https://platform.claude.com/docs/en/about-claude/pricing as of 2026-11-08. Haiku 5.5 uses the under-100k rate.

| Model | Provider | Requests | Input | Output | Cache write | Cache read | USD | Counts to cap |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| claude-sonnet-5-5 | local | 100 | 8780 | 24866 | 286700 | 0 | 0.982952 | no |

Local estimate per 100 local drafts: $0.9830 (not billed).
```

The same 100 cases priced as Haiku 5.5 came to $0.0491, about $0.049 per 100. See `evals/results/comparison.md`. The pass rate is the same in both files because the drafter was the local template, not the two models.

## Live measurement, Haiku 5.5, 8 November 2026

One worksheet call (`Fractions`, class 5, four questions) returned a schema-valid draft and copied the syllabus locator exactly.

A warm-up call wrote the cache. The next two calls read it:

| Call | Input tokens | Output tokens | Cache write | Cache read | USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 734 | 735 | 0 | 2731 | 0.000468 |
| 2 | 734 | 819 | 0 | 2731 | 0.000510 |

At that rate, 100 cached Haiku worksheets are about $0.05. The $5 cap would allow on the order of 10,000 such calls. A Sonnet draft is priced at about twenty times the Haiku input and output rates, which is why the cap is there before anyone turns on the larger model for a full run.

A short call with no tools and a small system prompt did not cache. The cache minimum was not met. The worksheet path caches because the rules and the tool definition are large enough.

## How a real month would be filed

1. Export the Budget screen, or run the same renderer against the department database.
2. Split local estimates from API rows. Only Claude (`provider=claude`) rows are spend against the cap.
3. Note the cap, the remaining amount, and any request the cap refused.
4. Attach the price-page date. Do not treat last month's rate as permanent.
