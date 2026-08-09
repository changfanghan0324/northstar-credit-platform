from __future__ import annotations

from northstar_credit_app import analyze_case
from northstar_credit_app.demo import load_demo_case


def _zero_debt_and_service(slug: str = "stable-manufacturer"):
    case = load_demo_case(slug)
    financials = case.financials.model_copy(
        update={
            key: getattr(case.financials, key).model_copy(update={"amount_minor": 0})
            for key in (
                "short_term_borrowings",
                "current_maturities",
                "long_term_debt",
                "finance_leases",
                "secured_debt",
                "cash_interest",
                "scheduled_principal",
            )
        }
    )
    return case.model_copy(update={"financials": financials, "debt_instruments": []})


def test_zero_debt_receives_strong_not_adverse_leverage_score() -> None:
    result = analyze_case(_zero_debt_and_service())
    leverage = next(
        item for item in result.scorecard.components if item.key == "leverage"
    )

    assert result.metrics["gross_leverage"].value == "0.0000"
    assert leverage.score == "100.00"
    assert leverage.status == "valid"


def test_forecast_uses_typed_ratio_states_and_never_numeric_sentinels() -> None:
    case = load_demo_case("stable-manufacturer")
    financials = case.financials.model_copy(
        update={
            "ebit": case.financials.ebit.model_copy(update={"amount_minor": -1}),
            "depreciation_amortization": case.financials.depreciation_amortization.model_copy(
                update={"amount_minor": 0}
            ),
        }
    )
    result = analyze_case(case.model_copy(update={"financials": financials}))

    for scenario in result.scenarios:
        for year in scenario.years:
            assert year.leverage is None
            assert year.leverage_status == "not_meaningful"
            assert year.leverage_reason_code == "nm_negative_base"
            assert "999.9999" not in year.model_dump_json()


def test_zero_interest_and_service_are_not_reported_as_passing_dscr_covenant() -> None:
    case = _zero_debt_and_service()
    request = case.request.model_copy(
        update={
            "amount": case.request.amount.model_copy(update={"amount_minor": 0}),
        }
    )
    result = analyze_case(case.model_copy(update={"request": request}))
    first = result.scenarios[0].years[0]
    dscr = next(
        item
        for item in result.covenants
        if item.scenario == "base" and item.year == 1 and item.name == "Minimum DSCR"
    )

    assert first.dscr is None
    assert first.dscr_reason_code == "nm_no_obligation"
    assert dscr.status == "not_applicable"
    assert dscr.actual == "nm_no_obligation"


def test_nonconverged_reverse_stress_exposes_no_numeric_result() -> None:
    case = _zero_debt_and_service()
    request = case.request.model_copy(
        update={"amount": case.request.amount.model_copy(update={"amount_minor": 0})}
    )
    result = analyze_case(case.model_copy(update={"request": request}))

    assert result.reverse_stress.converged is False
    assert result.reverse_stress.dscr_minimum_revenue_decline is None
    assert result.reverse_stress.failure_reason
    memo = " ".join(result.memo_sections["reverse_stress"])
    assert "no converged result" in memo
    assert "None%" not in memo


def test_liquidity_and_refinancing_events_are_separate_from_covenant_status() -> None:
    result = analyze_case(load_demo_case("stable-manufacturer"))
    severe = next(item for item in result.scenarios if item.name == "severe")

    assert severe.first_breach_year == 1
    assert severe.first_stress_event_year == 1
    # Aggregate debt is conservatively treated as floating when no instrument
    # rate metadata exists, so the severe rate shock can exhaust liquidity in
    # year one rather than silently applying no shock.
    assert severe.liquidity_exhaustion_year == 1
    assert severe.years[0].liquidity_status == "shortfall"
    assert severe.years[0].refinancing_status == "none"
