from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from northstar_credit_app import analyze_case, resolve_underwriting_financials
from northstar_credit_app.analysis import _resolve_facility_mechanics
from northstar_credit_app.demo import load_demo_case
from northstar_credit_app.facility import calculate_borrowing_base
from northstar_credit_app.models import (
    DebtInstrumentInput,
    FinancialPeriodInput,
    FinancialSpreadInput,
    MoneyValue,
)
from northstar_policy import load_policy


def money(value: int) -> MoneyValue:
    return MoneyValue(amount_minor=value, currency="USD")


def test_money_scale_golden_vectors_are_canonical() -> None:
    vectors = json.loads(Path("tests/fixtures/money_scale_vectors.json").read_text())
    digits = {"whole": 0, "thousands": 3, "millions": 6}
    for vector in vectors:
        whole, _, fraction = vector["input"].partition(".")
        sign = -1 if whole.startswith("-") else 1
        unsigned = whole.lstrip("-").replace(",", "")
        exponent = 2 + digits[vector["scale"]]
        actual = sign * int(unsigned + fraction) * 10 ** (exponent - len(fraction))
        assert actual == vector["expected_amount_minor"]


def test_money_value_rejects_unsafe_json_integer() -> None:
    try:
        MoneyValue(amount_minor=9_007_199_254_740_992, currency="USD")
    except ValueError:
        return
    raise AssertionError("unsafe amount_minor must be rejected")


def test_display_scale_is_metadata_only_and_does_not_double_scale() -> None:
    case = load_demo_case("stable-manufacturer")
    base = case.financials
    period = FinancialPeriodInput(
        id="scaled",
        label="Q1 scaled",
        period_type="ltm",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        fiscal_year=2025,
        fiscal_quarter=None,
        source_type="management",
        source_reference="synthetic/scaled",
        scale="millions",
        income_statement={
            "revenue": money(125_000_000),
            "ebitda": money(25_000_000),
            "ebit": money(20_000_000),
            "depreciation_amortization": money(5_000_000),
        },
        balance_sheet={
            "cash": base.unrestricted_cash,
            "current_assets": base.current_assets,
            "current_liabilities": base.current_liabilities,
            "short_term_debt": base.short_term_borrowings,
            "current_maturities": base.current_maturities,
            "long_term_debt": base.long_term_debt,
            "lease_liabilities": base.finance_leases,
            "equity": base.equity,
            "total_liabilities": base.total_liabilities,
            "total_assets": base.total_assets,
        },
        cash_flow={
            "operating_cash_flow": base.cfo,
            "maintenance_capex": base.maintenance_capex,
            "working_capital_change": base.working_capital_increase,
        },
    )
    resolved = resolve_underwriting_financials(
        case.model_copy(
            update={
                "financial_spread": FinancialSpreadInput(
                    periods=[period], selected_ltm_method="reported_ltm"
                )
            }
        )
    )
    assert resolved.financials.revenue.amount_minor == 125_000_000


def test_fy_ytd_uses_current_ytd_for_balance_sheet_lineage() -> None:
    case = load_demo_case("stable-manufacturer")

    def p(
        pid: str, year: int, kind: str, start: date, end: date, value: int, flow: str
    ):
        return FinancialPeriodInput(
            id=pid,
            label=pid,
            period_type=kind,  # type: ignore[arg-type]
            start_date=start,
            end_date=end,
            fiscal_year=year,
            source_type="management",
            source_reference=f"synthetic/{pid}",
            flow_type=flow,  # type: ignore[arg-type]
            income_statement={
                "revenue": money(value),
                "ebitda": money(value // 5),
                "ebit": money(value // 6),
                "depreciation_amortization": money(value // 30),
                "cash_interest": money(value // 50),
                "cash_taxes": money(value // 40),
                "net_income": money(value // 10),
            },
            balance_sheet={
                "cash": money(value),
                "current_assets": money(value * 2),
                "current_liabilities": money(value),
                "accounts_receivable": money(value // 2),
                "inventory": money(value // 4),
                "short_term_debt": money(value // 10),
                "current_maturities": money(value // 20),
                "long_term_debt": money(value // 5),
                "lease_liabilities": money(value // 25),
                "equity": money(value),
                "total_liabilities": money(value),
                "total_assets": money(value * 2),
            },
            cash_flow={
                "operating_cash_flow": money(value // 2),
                "maintenance_capex": money(value // 20),
                "working_capital_change": money(value // 30),
                "capital_expenditures": money(value // 15),
            },
        )

    fy = p(
        "fy24",
        2024,
        "historical_fiscal_year",
        date(2024, 1, 1),
        date(2024, 12, 31),
        1_000_000,
        "discrete",
    )
    prior = p(
        "prior", 2024, "ytd", date(2024, 1, 1), date(2024, 6, 30), 400_000, "cumulative"
    )
    current = p(
        "current",
        2025,
        "ytd",
        date(2025, 1, 1),
        date(2025, 6, 30),
        500_000,
        "cumulative",
    )
    spread = FinancialSpreadInput(
        periods=[fy, prior, current],
        selected_ltm_method="fiscal_year_plus_current_ytd_minus_prior_ytd",
    )
    resolved = resolve_underwriting_financials(
        case.model_copy(update={"financial_spread": spread})
    )
    assert resolved.financials.revenue.amount_minor == 1_100_000
    assert (
        resolved.financials.ebit.amount_minor
        + resolved.financials.depreciation_amortization.amount_minor
        == 220_000
    )
    assert resolved.financials.cfo.amount_minor == 550_000
    assert resolved.financials.unrestricted_cash.amount_minor == 500_000
    assert resolved.financials.current_assets.amount_minor == 1_000_000
    assert resolved.financials.current_liabilities.amount_minor == 500_000
    assert resolved.financials.accounts_receivable.amount_minor == 250_000
    assert resolved.financials.inventory.amount_minor == 125_000
    assert resolved.financials.short_term_borrowings.amount_minor == 50_000
    assert resolved.financials.current_maturities.amount_minor == 25_000
    assert resolved.financials.long_term_debt.amount_minor == 100_000
    assert resolved.financials.finance_leases.amount_minor == 20_000
    assert resolved.financials.total_assets.amount_minor == 1_000_000
    assert resolved.financials.total_liabilities.amount_minor == 500_000
    assert resolved.financials.equity.amount_minor == 500_000
    assert resolved.snapshot.balance_sheet_source_period_id == "current"
    assert resolved.snapshot.period_end == date(2025, 6, 30)
    assert resolved.snapshot.flow_source_period_ids == ["fy24", "current", "prior"]
    assert resolved.snapshot.source_lineage["unrestricted_cash"] == ["current"]
    assert resolved.snapshot.source_lineage["revenue"] == [
        "fy24",
        "current",
        "prior",
    ]
    assert resolved.snapshot.source_authority["cash_interest"] == "period_spread"
    assert resolved.snapshot.source_authority["scheduled_principal"] == "blocked"
    assert resolved.snapshot.blocked_authority_fields == ["scheduled_principal"]
    assert resolved.snapshot.source_window == {
        "fiscal_year": "fy24",
        "current_ytd": "current",
        "prior_ytd": "prior",
        "fiscal_year_end": "2024-12-31",
        "current_ytd_end": "2025-06-30",
        "prior_ytd_end": "2024-06-30",
    }
    assert resolved.snapshot.bridge_formula == "FY + Current YTD - Prior Comparable YTD"

    blocked_analysis = analyze_case(
        case.model_copy(update={"financial_spread": spread})
    )
    assert blocked_analysis.analysis_status == "blocked"
    assert blocked_analysis.metrics["dscr"].status == "blocked"
    assert blocked_analysis.capacity.recommended.amount_minor == 0
    assert blocked_analysis.reverse_stress.status == "blocked"


def test_fy_ytd_rejects_wrong_cut_and_degenerate_windows() -> None:
    case = load_demo_case("stable-manufacturer")
    # Same-duration YTD, but it starts in February rather than at the FY start.
    fy = FinancialPeriodInput(
        id="fy24",
        label="FY 2024",
        period_type="historical_fiscal_year",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        fiscal_year=2024,
        source_type="management",
        source_reference="synthetic/fy24",
        income_statement={"revenue": money(1_000_000)},
    )
    wrong_prior = FinancialPeriodInput(
        id="wrong-prior",
        label="YTD Jul 2024",
        period_type="ytd",
        start_date=date(2024, 2, 1),
        end_date=date(2024, 7, 30),
        fiscal_year=2024,
        source_type="management",
        source_reference="synthetic/wrong-prior",
        flow_type="cumulative",
        income_statement={"revenue": money(400_000)},
    )
    current = wrong_prior.model_copy(
        update={
            "id": "current",
            "label": "YTD Jul 2025",
            "start_date": date(2025, 2, 1),
            "end_date": date(2025, 7, 30),
            "fiscal_year": 2025,
        }
    )
    wrong = resolve_underwriting_financials(
        case.model_copy(
            update={
                "financial_spread": FinancialSpreadInput(
                    periods=[fy, wrong_prior, current],
                    selected_ltm_method="fiscal_year_plus_current_ytd_minus_prior_ytd",
                )
            }
        )
    )
    assert wrong.snapshot.reconciliation_status == "blocked"
    assert any("strict FY subset" in issue for issue in wrong.snapshot.blocking_issues)

    missing_prior = resolve_underwriting_financials(
        case.model_copy(
            update={
                "financial_spread": FinancialSpreadInput(
                    periods=[fy, current],
                    selected_ltm_method="fiscal_year_plus_current_ytd_minus_prior_ytd",
                )
            }
        )
    )
    assert missing_prior.snapshot.reconciliation_status == "blocked"
    assert any(
        "one FY and two YTD" in issue
        for issue in missing_prior.snapshot.blocking_issues
    )


def test_debt_mismatch_blocks_decision_and_itemized_cfads_flows_to_capacity() -> None:
    case = load_demo_case("stable-manufacturer")
    instrument = DebtInstrumentInput(
        name="Mismatched schedule",
        principal=money(1_000_000_000),
        annual_rate=Decimal("0.06"),
        scheduled_amortization=money(10_000_000),
        maturity_year=5,
        schedule_completeness="complete",
    )
    result = analyze_case(case.model_copy(update={"debt_instruments": [instrument]}))
    assert result.debt_reconciliation is not None
    assert result.debt_reconciliation.status == "blocked"
    assert result.analysis_status == "blocked"
    assert result.pricing.status == "blocked"


def test_reconciled_debt_source_drives_leverage_dscr_stress_and_memo() -> None:
    case = load_demo_case("stable-manufacturer")
    total_debt = sum(
        getattr(case.financials, field).amount_minor
        for field in (
            "short_term_borrowings",
            "current_maturities",
            "long_term_debt",
            "finance_leases",
        )
    )
    aggregate = analyze_case(case)
    assert aggregate.debt_reconciliation is not None
    assert aggregate.debt_reconciliation.status == "aggregate_mode"
    assert aggregate.debt_reconciliation.selected_source == "balance_sheet_aggregate"
    assert aggregate.debt_reconciliation.selected_debt.amount_minor == total_debt
    assert aggregate.debt_reconciliation.selected_scheduled_principal.amount_minor == (
        case.financials.scheduled_principal.amount_minor
    )
    schedule = DebtInstrumentInput(
        name="Reconciled aggregate instrument",
        principal=money(total_debt),
        annual_rate=Decimal("0.08"),
        scheduled_amortization=case.financials.scheduled_principal,
        maturity_year=3,
        schedule_completeness="complete",
    )
    result = analyze_case(case.model_copy(update={"debt_instruments": [schedule]}))
    reconciliation = result.debt_reconciliation
    assert reconciliation is not None
    assert reconciliation.status == "reconciled"
    assert reconciliation.selected_source == "instrument_schedule"
    assert reconciliation.selected_debt.amount_minor == total_debt
    assert (
        reconciliation.selected_scheduled_principal.amount_minor
        == case.financials.scheduled_principal.amount_minor
    )
    assert reconciliation.selected_interest.amount_minor == (total_debt * 8 // 100)
    assert reconciliation.leverage_source == reconciliation.stress_source
    assert reconciliation.stress_source == reconciliation.maturity_source
    assert result.metrics["dscr"].value == aggregate.metrics["dscr"].value
    assert (
        result.metrics["interest_coverage"].value
        == aggregate.metrics["interest_coverage"].value
    )
    assert reconciliation.coverage_basis_notice.endswith("instrument_schedule.")
    assert "Debt reconciliation: reconciled" in " ".join(
        result.memo_sections["capital_structure"]
    )


def test_material_debt_interest_mismatch_blocks_all_debt_service_outputs() -> None:
    case = load_demo_case("stable-manufacturer")
    total_debt = sum(
        getattr(case.financials, field).amount_minor
        for field in (
            "short_term_borrowings",
            "current_maturities",
            "long_term_debt",
            "finance_leases",
        )
    )
    schedule = DebtInstrumentInput(
        name="Interest mismatch",
        principal=money(total_debt),
        annual_rate=Decimal("0.10"),
        scheduled_amortization=case.financials.scheduled_principal,
        maturity_year=3,
        schedule_completeness="complete",
    )
    result = analyze_case(case.model_copy(update={"debt_instruments": [schedule]}))
    assert result.debt_reconciliation is not None
    assert result.debt_reconciliation.status == "blocked"
    assert result.analysis_status == "blocked"
    assert result.metrics["dscr"].status == "blocked"
    assert result.capacity.recommended.amount_minor == 0
    assert result.capacity.recommendation_state == "blocked"
    assert result.reverse_stress.status == "blocked"
    assert all(
        item.status == "blocked"
        for item in result.covenants
        if item.name == "Minimum DSCR"
    )


def test_partial_schedule_labels_residual_and_abl_availability_is_net_of_drawn() -> (
    None
):
    case = load_demo_case("stable-manufacturer")
    aggregate_result = analyze_case(case)
    instrument = DebtInstrumentInput(
        name="Long-term schedule only",
        principal=case.financials.long_term_debt,
        annual_rate=Decimal("0.06"),
        scheduled_amortization=money(100_000_000),
        maturity_year=5,
        schedule_completeness="partial",
    )
    result = analyze_case(case.model_copy(update={"debt_instruments": [instrument]}))
    assert result.debt_reconciliation is not None
    assert result.debt_reconciliation.aggregate_mode is True
    assert result.debt_reconciliation.status == "reconciled"
    assert (
        result.debt_reconciliation.selected_source == "partial_schedule_with_residual"
    )
    assert result.debt_reconciliation.selected_debt.amount_minor == (
        case.financials.short_term_borrowings.amount_minor
        + case.financials.current_maturities.amount_minor
        + case.financials.long_term_debt.amount_minor
        + case.financials.finance_leases.amount_minor
    )
    assert result.debt_reconciliation.residual_debt is not None
    assert result.debt_reconciliation.residual_debt.amount_minor == 1_500_000_000
    assert result.debt_reconciliation.residual_maturity_status == "unknown"
    assert result.debt_reconciliation.selected_scheduled_principal.amount_minor == (
        case.financials.scheduled_principal.amount_minor
    )
    assert result.metrics["dscr"].value == aggregate_result.metrics["dscr"].value
    assert "residual" in result.debt_reconciliation.coverage_basis_notice
    assert all(
        scenario.maturity_test_status == "blocked" for scenario in result.scenarios
    )
    assert any(
        "Unscheduled residual debt" in line
        for line in result.memo_sections["debt_maturity_schedule"]
    )

    raw = case.model_dump(mode="python")
    raw["request"].update(
        {
            "facility_type": "asset_based",
            "security_type": "asset_based",
            "amortization_type": "revolver",
            "initial_drawn_amount": money(500_000_000),
        }
    )
    raw["borrowing_base"] = {
        "accounts_receivable": {
            "gross_receivables": money(1_000_000_000),
            "ineligible_receivables": money(0),
            "past_due_receivables": money(0),
            "cross_aged_receivables": money(0),
            "foreign_receivables": money(0),
            "concentration_reserve": money(0),
            "dilution_reserve": money(0),
            "advance_rate": "0.80",
        },
        "inventory": {
            "gross_inventory": money(0),
            "ineligible_inventory": money(0),
            "obsolete_inventory": money(0),
            "advance_rate": "0.50",
            "inventory_cap": money(0),
        },
        "other_collateral": {
            "equipment": money(0),
            "real_estate": money(0),
            "cash": money(0),
            "other": money(0),
        },
        "additional_reserves": money(0),
        "prior_liens": money(0),
    }
    abl = case.model_validate(raw)
    mechanics = _resolve_facility_mechanics(abl)
    base = calculate_borrowing_base(abl, load_policy()[0], mechanics)
    assert base.borrowing_base is not None and base.availability is not None
    assert base.borrowing_base.amount_minor == 800_000_000
    assert base.availability.amount_minor == 300_000_000
    assert base.commitment is not None and base.outstanding is not None


def test_unspecified_or_overlarge_partial_schedule_blocks_instead_of_guessing() -> None:
    case = load_demo_case("stable-manufacturer")
    unspecified = DebtInstrumentInput(
        name="Unscoped debt",
        principal=case.financials.long_term_debt,
        annual_rate=Decimal("0.06"),
        scheduled_amortization=money(100_000_000),
        maturity_year=5,
    )
    unspecified_result = analyze_case(
        case.model_copy(update={"debt_instruments": [unspecified]})
    )
    assert unspecified_result.debt_reconciliation is not None
    assert unspecified_result.debt_reconciliation.status == "blocked"
    assert unspecified_result.debt_reconciliation.selected_source == "blocked_mismatch"

    overlarge = unspecified.model_copy(
        update={
            "schedule_completeness": "partial",
            "principal": case.financials.long_term_debt,
        }
    )
    overlarge_financials = case.financials.model_copy(
        update={
            "short_term_borrowings": money(2_500_000_000),
            "current_liabilities": money(3_000_000_000),
            "total_liabilities": money(8_500_000_000),
            "total_assets": money(9_000_000_000),
            "equity": money(500_000_000),
        }
    )
    overlarge_result = analyze_case(
        case.model_copy(
            update={
                "financials": overlarge_financials,
                "debt_instruments": [overlarge],
            }
        )
    )
    assert overlarge_result.debt_reconciliation is not None
    assert overlarge_result.debt_reconciliation.status == "blocked"
    assert "20%" in overlarge_result.debt_reconciliation.explanation


def test_debt_tolerance_boundary_is_explicit_and_asymmetric() -> None:
    case = load_demo_case("stable-manufacturer")
    total_debt = sum(
        getattr(case.financials, field).amount_minor
        for field in (
            "short_term_borrowings",
            "current_maturities",
            "long_term_debt",
            "finance_leases",
        )
    )
    # 0.25% of balance-sheet debt is the exact missing-debt tolerance.
    boundary_principal = total_debt - int(total_debt * Decimal("0.0025"))
    just_over = boundary_principal - 1

    def result_for(principal_minor: int):
        rate = Decimal(case.financials.cash_interest.amount_minor) / Decimal(
            principal_minor
        )
        instrument = DebtInstrumentInput(
            name="Tolerance test",
            principal=money(principal_minor),
            annual_rate=rate,
            scheduled_amortization=case.financials.scheduled_principal,
            maturity_year=3,
            schedule_completeness="complete",
        )
        return analyze_case(case.model_copy(update={"debt_instruments": [instrument]}))

    assert result_for(boundary_principal).debt_reconciliation.status == (
        "immaterial_difference"
    )
    assert result_for(just_over).debt_reconciliation.status == "blocked"


def test_fixed_rate_schedule_is_not_repriced_by_rate_shock() -> None:
    case = load_demo_case("stable-manufacturer")
    total_debt = sum(
        getattr(case.financials, field).amount_minor
        for field in (
            "short_term_borrowings",
            "current_maturities",
            "long_term_debt",
            "finance_leases",
        )
    )
    instrument = DebtInstrumentInput(
        name="Fixed debt",
        principal=money(total_debt),
        annual_rate=Decimal("0.08"),
        rate_type="fixed",
        scheduled_amortization=case.financials.scheduled_principal,
        maturity_year=3,
        schedule_completeness="complete",
    )
    shocked_scenarios = {
        key: value.model_copy(update={"rate_shock": Decimal("0.20")})
        for key, value in case.scenarios.items()
    }
    base_result = analyze_case(
        case.model_copy(update={"debt_instruments": [instrument]})
    )
    shocked_result = analyze_case(
        case.model_copy(
            update={
                "debt_instruments": [instrument],
                "scenarios": shocked_scenarios,
            }
        )
    )
    assert (
        shocked_result.debt_reconciliation.interest_shock_basis
        == "instrument_rate_type"
    )
    assert (
        shocked_result.scenarios[0].years[0].interest_coverage
        == base_result.scenarios[0].years[0].interest_coverage
    )


def test_rate_shock_is_non_vacuous_for_aggregate_and_partial_debt() -> None:
    case = load_demo_case("stable-manufacturer")
    shocked_scenarios = {
        key: value.model_copy(update={"rate_shock": Decimal("0.20")})
        for key, value in case.scenarios.items()
    }
    aggregate = analyze_case(case)
    aggregate_shocked = analyze_case(
        case.model_copy(update={"scenarios": shocked_scenarios})
    )
    assert aggregate.debt_reconciliation.interest_shock_basis == (
        "aggregate_conservative"
    )
    assert aggregate.debt_reconciliation.floating_principal.amount_minor == (
        aggregate.debt_reconciliation.selected_debt.amount_minor
    )
    assert (
        aggregate_shocked.scenarios[0].years[0].interest_coverage
        != aggregate.scenarios[0].years[0].interest_coverage
    )

    partial_instrument = DebtInstrumentInput(
        name="Floating long-term schedule",
        principal=money(case.financials.long_term_debt.amount_minor),
        annual_rate=Decimal("0.08"),
        rate_type="floating",
        scheduled_amortization=money(900_000_000),
        maturity_year=5,
        schedule_completeness="partial",
    )
    partial = analyze_case(
        case.model_copy(update={"debt_instruments": [partial_instrument]})
    )
    partial_shocked = analyze_case(
        case.model_copy(
            update={
                "debt_instruments": [partial_instrument],
                "scenarios": shocked_scenarios,
            }
        )
    )
    assert partial.debt_reconciliation.interest_shock_basis == (
        "partial_conservative_residual"
    )
    assert partial.debt_reconciliation.floating_principal.amount_minor == (
        partial.debt_reconciliation.selected_debt.amount_minor
    )
    assert partial.debt_reconciliation.selected_scheduled_principal.amount_minor == (
        900_000_000
    )
    assert (
        partial_shocked.scenarios[0].years[0].interest_coverage
        != partial.scenarios[0].years[0].interest_coverage
    )


def test_interest_tolerance_boundary_is_explicit() -> None:
    case = load_demo_case("stable-manufacturer")
    total_debt = sum(
        getattr(case.financials, field).amount_minor
        for field in (
            "short_term_borrowings",
            "current_maturities",
            "long_term_debt",
            "finance_leases",
        )
    )
    reported_interest = case.financials.cash_interest.amount_minor
    boundary_interest = reported_interest + int(reported_interest * Decimal("0.0025"))

    def result_for(implied_interest_minor: int):
        instrument = DebtInstrumentInput(
            name="Interest tolerance test",
            principal=money(total_debt),
            annual_rate=Decimal(implied_interest_minor) / Decimal(total_debt),
            scheduled_amortization=case.financials.scheduled_principal,
            maturity_year=3,
            schedule_completeness="complete",
        )
        return analyze_case(case.model_copy(update={"debt_instruments": [instrument]}))

    assert result_for(boundary_interest).debt_reconciliation.status == "reconciled"
    assert result_for(boundary_interest + 1).debt_reconciliation.status == "blocked"


def test_rate_decision_and_bullet_exit_are_explicit() -> None:
    case = load_demo_case("software-services")
    result = analyze_case(case)
    assert result.rate_decision is not None
    assert result.rate_decision.underwritten_rate == result.capacity.underwritten_rate
    assert result.facility_mechanics is not None
    assert result.facility_mechanics.amortization_type == "partial"
    assert result.scenarios[0].maturity_test_status in {"pass", "breach", "blocked"}


def test_five_year_bullet_rolls_through_exit_and_no_refinancing_case() -> None:
    case = load_demo_case("stable-manufacturer")
    request = case.request.model_copy(
        update={
            "amount": money(2_500_000_000),
            "amortization_type": "bullet",
            "amortization_years": None,
            "maturity_years": 5,
            "bullet_percentage": Decimal("1"),
        }
    )
    result = analyze_case(case.model_copy(update={"request": request}))

    base, downside, severe = result.scenarios
    for scenario in result.scenarios:
        assert len(scenario.years) == 3
        assert scenario.maturity_year == 5
        assert scenario.balloon_amount is not None
        assert scenario.balloon_amount.amount_minor == 2_500_000_000
        assert (
            scenario.exit_ebitda is not None and scenario.exit_ebitda.amount_minor > 0
        )
        assert scenario.exit_leverage is not None
        assert scenario.refinance_capacity is not None
        assert scenario.refinance_headroom is not None
        assert scenario.residual_debt is not None
        assert scenario.no_refinancing_status in {"pass", "breach"}

    assert base.maturity_test_status == "pass"
    assert base.no_refinancing_status == "pass"
    assert downside.maturity_test_status == "pass"
    assert severe.maturity_test_status == "breach"
    assert severe.no_refinancing_status == "breach"
    assert "no-refinancing" in severe.no_refinancing_reason.lower()
    assert any(
        "Maturity year 5" in line for line in result.memo_sections["severe_case"]
    )
