"""Token estimates, published prices, and the monthly cap.

Prices are the public first-party rates as of 2026-11-08 for prompts under
100,000 tokens. Haiku 5.5 is more expensive above that; this prototype stays
well under it.

Only provider=claude rows count against the monthly cap. Local rows store a
Claude-equivalent estimate for comparison and do not reduce remaining budget.
"""

from __future__ import annotations

import math
import sqlite3
from datetime import datetime, timezone

from app.config import FAST_MODEL, STANDARD_MODEL

PRICE_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
PRICE_AS_OF = "2026-11-08"
BILLABLE_PROVIDER = "claude"

# USD per million tokens.
PRICES: dict[str, dict[str, float]] = {
    STANDARD_MODEL: {
        "input": 2.0,
        "output": 10.0,
        "cache_write_5m": 2.5,
        "cache_read": 0.10,
        "batch_input": 1.0,
        "batch_output": 5.0,
    },
    FAST_MODEL: {
        "input": 0.10,
        "output": 0.50,
        "cache_write_5m": 0.125,
        "cache_read": 0.01,
        "batch_input": 0.05,
        "batch_output": 0.25,
    },
}

OUTPUT_TOKEN_ESTIMATE = {
    "worksheet": 700,
    "lesson_plan": 900,
    "question_bank": 800,
}


class BudgetError(RuntimeError):
    pass


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def price_for(model: str) -> dict[str, float]:
    return PRICES.get(model, PRICES[STANDARD_MODEL])


def cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_write_tokens: int = 0,
    cache_read_tokens: int = 0,
    *,
    batch: bool = False,
) -> float:
    """Price a token mix. Cache write/read are billed separately from input."""

    price = price_for(model)
    if batch:
        total = input_tokens * price["batch_input"] + output_tokens * price["batch_output"]
    else:
        total = (
            input_tokens * price["input"]
            + output_tokens * price["output"]
            + cache_write_tokens * price["cache_write_5m"]
            + cache_read_tokens * price["cache_read"]
        )
    return round(total / 1_000_000, 6)


def billable_cost(provider: str, estimated: float) -> float:
    """Local drafts are not invoices. Only Claude spend hits the cap."""

    if provider == BILLABLE_PROVIDER:
        return round(estimated, 6)
    return 0.0


def month_key(moment: datetime | None = None) -> str:
    current = moment or datetime.now(timezone.utc)
    return current.strftime("%Y-%m")


def spent_this_month(conn: sqlite3.Connection, moment: datetime | None = None) -> float:
    """Billable Claude spend only."""

    key = month_key(moment)
    row = conn.execute(
        """
        SELECT COALESCE(SUM(cost_usd), 0) AS spent
        FROM usage_ledger
        WHERE released = 0
          AND provider = ?
          AND substr(created_at, 1, 7) = ?
        """,
        (BILLABLE_PROVIDER, key),
    ).fetchone()
    return float(row["spent"])


def estimated_local_this_month(conn: sqlite3.Connection, moment: datetime | None = None) -> float:
    """Claude-equivalent estimate for local drafts. Not billable."""

    key = month_key(moment)
    row = conn.execute(
        """
        SELECT COALESCE(SUM(cost_usd), 0) AS spent
        FROM usage_ledger
        WHERE released = 0
          AND provider = 'local'
          AND substr(created_at, 1, 7) = ?
        """,
        (key,),
    ).fetchone()
    return float(row["spent"])


def remaining(conn: sqlite3.Connection, cap: float, moment: datetime | None = None) -> float:
    return round(cap - spent_this_month(conn, moment), 6)


def assert_within_cap(conn: sqlite3.Connection, cap: float, next_cost: float) -> float:
    left = remaining(conn, cap)
    if next_cost > left + 1e-9:
        raise BudgetError(
            f"Monthly cap reached. ${spent_this_month(conn):.4f} of ${cap:.2f} is already reserved. "
            "This request was not sent."
        )
    return left


def cache_warm_for_model(conn: sqlite3.Connection, model: str, moment: datetime | None = None) -> bool:
    """True when this month already recorded a cache write for the model."""

    key = month_key(moment)
    row = conn.execute(
        """
        SELECT 1 AS hit
        FROM usage_ledger
        WHERE released = 0
          AND model = ?
          AND cache_write_tokens > 0
          AND substr(created_at, 1, 7) = ?
        LIMIT 1
        """,
        (model, key),
    ).fetchone()
    return row is not None


def usage_by_model(conn: sqlite3.Connection, moment: datetime | None = None) -> list[dict]:
    key = month_key(moment)
    rows = conn.execute(
        """
        SELECT model, provider,
               COUNT(*) AS requests,
               COALESCE(SUM(input_tokens), 0) AS input_tokens,
               COALESCE(SUM(output_tokens), 0) AS output_tokens,
               COALESCE(SUM(cache_write_tokens), 0) AS cache_write_tokens,
               COALESCE(SUM(cache_read_tokens), 0) AS cache_read_tokens,
               COALESCE(SUM(cost_usd), 0) AS cost_usd
        FROM usage_ledger
        WHERE released = 0 AND substr(created_at, 1, 7) = ?
        GROUP BY model, provider
        ORDER BY provider DESC, model
        """,
        (key,),
    ).fetchall()
    return [dict(row) for row in rows]


def render_monthly_report(conn: sqlite3.Connection, cap: float, moment: datetime | None = None) -> str:
    key = month_key(moment)
    groups = usage_by_model(conn, moment)
    billable = spent_this_month(conn, moment)
    local_est = estimated_local_this_month(conn, moment)
    left = remaining(conn, cap, moment)
    lines = [
        f"# Monthly cost report {key}",
        "",
        f"Cap (billable Claude only): ${cap:.2f}",
        f"Billable Claude spend: ${billable:.6f}",
        f"Remaining under cap: ${left:.6f}",
        f"Local Claude-equivalent estimate (not billed): ${local_est:.6f}",
        "",
        "Only provider=claude rows reduce the remaining budget.",
        "Local rows are priced as if Claude ran, for comparison. They are not an invoice.",
        f"Prices: {PRICE_SOURCE} as of {PRICE_AS_OF}. Haiku 5.5 uses the under-100k rate.",
        "",
        "| Model | Provider | Requests | Input | Output | Cache write | Cache read | USD | Counts to cap |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if not groups:
        lines.append("| — | — | 0 | 0 | 0 | 0 | 0 | 0 | — |")
    for row in groups:
        counts = "yes" if row["provider"] == BILLABLE_PROVIDER else "no"
        lines.append(
            "| {model} | {provider} | {requests} | {input_tokens} | {output_tokens} | "
            "{cache_write_tokens} | {cache_read_tokens} | {cost_usd:.6f} | {counts} |".format(
                **row, counts=counts
            )
        )
    billable_requests = sum(row["requests"] for row in groups if row["provider"] == BILLABLE_PROVIDER)
    local_requests = sum(row["requests"] for row in groups if row["provider"] == "local")
    if billable_requests:
        per_hundred = (billable / billable_requests) * 100
        lines.extend(["", f"Billable cost per 100 Claude requests at this month's mix: ${per_hundred:.4f}."])
    if local_requests:
        per_hundred_local = (local_est / local_requests) * 100
        lines.extend(["", f"Local estimate per 100 local drafts: ${per_hundred_local:.4f} (not billed)."])
    return "\n".join(lines) + "\n"
