import pytest

from app.config import FAST_MODEL, STANDARD_MODEL
from app.cost import BudgetError, billable_cost, cost_usd, render_monthly_report
from app.pipeline import budget, create_draft, estimate


def test_published_prices_and_batch_discount():
    assert cost_usd(STANDARD_MODEL, 1_000_000, 1_000_000) == 12.0
    assert cost_usd(STANDARD_MODEL, 1_000_000, 1_000_000, batch=True) == 6.0
    assert cost_usd(FAST_MODEL, 1_000_000, 1_000_000) == 0.6
    cached = cost_usd(STANDARD_MODEL, 0, 0, cache_read_tokens=1_000_000)
    write = cost_usd(STANDARD_MODEL, 0, 0, cache_write_tokens=1_000_000)
    assert cached == 0.1
    assert write == 2.5


def test_billable_cost_is_zero_for_local():
    assert billable_cost("local", 1.23) == 0.0
    assert billable_cost("claude", 1.23) == 1.23


def test_estimate_shows_a_cache_discount_before_the_call(settings, worksheet):
    quote = estimate(settings, worksheet)
    assert quote["first_request_usd"] > quote["cached_request_usd"]
    assert quote["within_cap"] is True
    assert quote["remaining_usd"] == 5
    assert quote["provider"] == "local"
    assert quote["counts_against_cap_usd"] == 0.0
    assert quote["likely_request_usd"] > 0


def test_local_drafts_do_not_reduce_the_cap(settings, teacher, worksheet):
    first = create_draft(settings, teacher, worksheet)
    second = create_draft(settings, teacher, worksheet)
    report = budget(settings)
    assert first["provider"] == "local"
    assert second["cost_usd"] > 0
    assert report["billable_usd"] == 0.0
    assert report["spent_usd"] == 0.0
    assert report["local_estimated_usd"] > 0
    assert report["remaining_usd"] == settings.monthly_cap_usd
    assert "not billed" in report["report_markdown"]


def test_second_local_draft_uses_cache_read_pricing(settings, teacher, worksheet):
    first = create_draft(settings, teacher, worksheet)
    second = create_draft(settings, teacher, worksheet)
    assert first["cost_usd"] > second["cost_usd"]
    report = budget(settings)
    rows = {row["model"]: row for row in report["by_model"]}
    sonnet = rows[STANDARD_MODEL]
    assert sonnet["cache_write_tokens"] > 0
    assert sonnet["cache_read_tokens"] > 0


def test_cap_stops_claude_before_generation(settings, teacher, worksheet):
    tight = settings.__class__(
        **{**settings.__dict__, "monthly_cap_usd": 0.0001, "generate_mode": "claude"}
    )

    class Boom:
        provider = "claude"

        def generate(self, spec, notes):
            raise AssertionError("The model must not be called once the cap is reached.")

    with pytest.raises(BudgetError):
        create_draft(tight, teacher, worksheet, generator=Boom())


def test_monthly_report_separates_local_from_billable(settings, teacher, worksheet):
    create_draft(settings, teacher, worksheet)
    create_draft(settings, teacher, worksheet.model_copy(update={"model": FAST_MODEL}))
    report = budget(settings)
    text = report["report_markdown"]
    assert STANDARD_MODEL in text
    assert FAST_MODEL in text
    assert report["spent_usd"] == 0.0
    assert report["local_estimated_usd"] > 0
    assert report["remaining_usd"] == settings.monthly_cap_usd
    assert "Counts to cap" in text
    assert render_monthly_report  # the same formatter the budget endpoint uses
