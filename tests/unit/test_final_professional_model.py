from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from northstar_credit_app import analyze_case
from northstar_credit_app.demo import load_demo_case
from northstar_credit_app.models import (
    BusinessRiskEvidenceInput,
    CaseInput,
    FinancialPeriodInput,
    FinancialSpreadInput,
    MoneyValue,
    NormalizationAdjustmentInput,
)


def money(amount: int) -> MoneyValue:
    return MoneyValue(amount_minor=amount, currency="USD", minor_unit_exponent=2)


def quarter(number: int, *, start_month: int, end_month: int) -> FinancialPeriodInput:
    return FinancialPeriodInput(
        id=f"2025-q{number}",
        label=f"Q{number} 2025",
        period_type="quarter",
        start_date=date(2025, start_month, 1),
        end_date=date(2025, end_month, 28),
        fiscal_year=2025,
        fiscal_quarter=number,
        source_type="management",
        source_reference=f"Synthetic management accounts Q{number}",
        income_statement={
            "revenue": money(10_000_000 * number),
            "ebitda": money(2_000_000 * number),
        },
        balance_sheet={"cash": money(1_000_000 * number)},
    )


def test_four_nonoverlapping_quarters_produce_available_ltm_and_trend() -> None:
    case = load_demo_case("stable-manufacturer").model_copy(
        update={
            "financial_spread": FinancialSpreadInput(
                periods=[
                    quarter(1, start_month=1, end_month=3),
                    quarter(2, start_month=4, end_month=6),
                    quarter(3, start_month=7, end_month=9),
                    quarter(4, start_month=10, end_month=12),
                ],
                selected_ltm_method="latest_four_quarters",
            )
        }
    )
    result = analyze_case(case)
    assert result.financial_spreading.ltm_status == "available"
    assert result.financial_spreading.ltm_period_id == "derived-latest-four-quarters"
    assert result.financial_spreading.trend["labels"] == [
        "Q1 2025",
        "Q2 2025",
        "Q3 2025",
        "Q4 2025",
    ]


def test_overlapping_quarters_are_rejected_before_analysis() -> None:
    with pytest.raises(ValueError, match="must not overlap"):
        FinancialSpreadInput(
            periods=[
                quarter(1, start_month=1, end_month=3),
                quarter(2, start_month=3, end_month=6),
            ],
            selected_ltm_method="latest_four_quarters",
        )


def test_balance_sheet_mismatch_is_visible_and_incompatible_ltm_is_blocked() -> None:
    period = FinancialPeriodInput(
        id="fy-2025",
        label="FY 2025",
        period_type="historical_fiscal_year",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        fiscal_year=2025,
        audited=True,
        source_type="audited",
        source_reference="Synthetic audited statements",
        balance_sheet={
            "total_assets": money(10_000),
            "total_liabilities": money(7_000),
            "equity": money(2_000),
        },
    )
    case = load_demo_case("stable-manufacturer").model_copy(
        update={
            "financial_spread": FinancialSpreadInput(
                periods=[period], selected_ltm_method="latest_four_quarters"
            )
        }
    )
    spreading = analyze_case(case).financial_spreading
    assert spreading.ltm_status == "blocked"
    assert any("do not reconcile" in item for item in spreading.reconciliation_warnings)
    assert any(
        "compatible source periods" in item
        for item in spreading.reconciliation_warnings
    )


def adjustment(**updates: object) -> NormalizationAdjustmentInput:
    now = datetime.now(UTC)
    values: dict[str, object] = {
        "id": "adj-1",
        "name": "Synthetic restructuring cost",
        "period_id": "legacy-snapshot",
        "category": "restructuring",
        "amount": money(100_000_000),
        "direction": "positive",
        "cash_classification": "cash",
        "recurrence": "nonrecurring",
        "ebitda_impact": money(100_000_000),
        "ebit_impact": money(100_000_000),
        "cfads_impact": money(0),
        "supporting_evidence": "Synthetic ledger and closure plan",
        "source_reference": "Synthetic adjustment schedule",
        "analyst_rationale": "One-time plant closure program",
        "approval_status": "approved",
        "reviewer": "Synthetic reviewer",
        "created_at": now,
        "updated_at": now,
    }
    values.update(updates)
    return NormalizationAdjustmentInput.model_validate(values)


def test_adjustments_require_rationale_and_approved_evidence() -> None:
    with pytest.raises(ValueError, match="rationale"):
        adjustment(analyst_rationale="")
    with pytest.raises(ValueError, match="supporting evidence"):
        adjustment(supporting_evidence="")


def test_approved_adjustment_builds_bridge_and_changes_leverage() -> None:
    case = load_demo_case("stable-manufacturer").model_copy(
        update={"normalization_adjustments": [adjustment()]}
    )
    result = analyze_case(case)
    assert result.adjustments.approved_adjustment.amount_minor == 100_000_000
    assert Decimal(result.adjustments.leverage_after) < Decimal(
        result.adjustments.leverage_before
    )


def test_missing_qualitative_evidence_blocks_grade() -> None:
    case = load_demo_case("stable-manufacturer")
    result = analyze_case(
        case.model_copy(
            update={
                "business_risk": case.business_risk.model_copy(
                    update={"factor_evidence": {}}
                )
            }
        )
    )
    assert result.scorecard.grade is None
    assert result.analysis_status == "blocked"
    business_keys = {
        "industry",
        "competitive_position",
        "customer_concentration",
        "diversification",
        "management_policy",
        "governance_event",
    }
    assert all(
        component.status == "blocked"
        for component in result.scorecard.components
        if component.key in business_keys
    )
    assert all(
        component.score == "0.00" and component.contribution == "0.00"
        for component in result.scorecard.components
        if component.key in business_keys
    )


def test_business_risk_evidence_cannot_be_blank() -> None:
    with pytest.raises(ValueError, match="evidence and rationale"):
        BusinessRiskEvidenceInput(
            score=70,
            band="adequate",
            evidence="",
            source="Synthetic source",
            analyst_rationale="",
            confidence="medium",
            last_updated=datetime.now(UTC),
        )


def test_borrowing_base_is_policy_capped_and_binds_asset_based_capacity() -> None:
    case = load_demo_case("stable-manufacturer")
    raw = case.model_dump(mode="python")
    raw["request"].update(
        {
            "facility_type": "asset_based",
            "security_type": "asset_based",
            "amortization_type": "revolver",
            "amount": money(1_000_000_000).model_dump(),
            "initial_drawn_amount": money(200_000_000).model_dump(),
            "commitment_fee_bps": 100,
        }
    )
    raw["borrowing_base"] = {
        "accounts_receivable": {
            "gross_receivables": money(1_000_000_000),
            "ineligible_receivables": money(100_000_000),
            "past_due_receivables": money(50_000_000),
            "cross_aged_receivables": money(0),
            "foreign_receivables": money(0),
            "concentration_reserve": money(0),
            "dilution_reserve": money(0),
            "advance_rate": "0.99",
        },
        "inventory": {
            "gross_inventory": money(500_000_000),
            "ineligible_inventory": money(100_000_000),
            "obsolete_inventory": money(50_000_000),
            "advance_rate": "0.99",
            "inventory_cap": money(150_000_000),
        },
        "other_collateral": {
            "equipment": money(50_000_000),
            "real_estate": money(0),
            "cash": money(0),
            "other": money(0),
        },
        "additional_reserves": money(25_000_000),
        "prior_liens": money(10_000_000),
    }
    result = analyze_case(CaseInput.model_validate(raw))
    assert result.borrowing_base.borrowing_base is not None
    assert result.borrowing_base.borrowing_base.amount_minor == 887_500_000
    assert result.capacity.collateral is not None
    assert result.capacity.collateral.amount_minor == 887_500_000
    assert result.borrowing_base.binding_constraint == "borrowing_base"
    revolver_abl = result.revolver_abl
    assert revolver_abl.status == "calculated"
    assert revolver_abl.commitment.amount_minor == 1_000_000_000
    assert revolver_abl.drawn_amount.amount_minor == 200_000_000
    assert revolver_abl.borrowing_base is not None
    assert revolver_abl.borrowing_base.amount_minor == 887_500_000
    assert revolver_abl.availability is not None
    assert revolver_abl.availability.amount_minor == 687_500_000
    assert revolver_abl.commitment_fee is not None
    assert revolver_abl.commitment_fee.amount_minor == 8_000_000
    assert revolver_abl.cash_interest is not None
    assert revolver_abl.cash_interest.amount_minor == 16_000_000


def test_revolver_availability_is_commitment_limited_and_missing_abl_inputs_block() -> (
    None
):
    case = load_demo_case("stable-manufacturer")
    revolver = case.model_copy(
        update={
            "request": case.request.model_copy(
                update={
                    "facility_type": "revolver",
                    "security_type": "secured",
                    "amortization_type": "revolver",
                    "amount": money(1_000_000_000),
                    "initial_drawn_amount": money(250_000_000),
                    "commitment_fee_bps": 50,
                }
            )
        }
    )
    result = analyze_case(revolver)
    view = result.revolver_abl
    assert view.status == "calculated"
    assert view.borrowing_base is None
    assert view.availability is not None
    assert view.availability.amount_minor == 750_000_000
    assert view.commitment_fee is not None
    assert view.commitment_fee.amount_minor == 3_750_000

    missing_abl = revolver.model_copy(
        update={
            "request": revolver.request.model_copy(
                update={"facility_type": "asset_based", "security_type": "asset_based"}
            ),
            "borrowing_base": None,
        }
    )
    blocked = analyze_case(missing_abl)
    assert blocked.revolver_abl.status == "blocked"
    assert blocked.revolver_abl.availability is None
    assert blocked.capacity.recommended.amount_minor == 0


def test_unsecured_borrowing_base_not_applicable_and_collateral_does_not_change_grade() -> (
    None
):
    case = load_demo_case("stable-manufacturer")
    unsecured = case.model_copy(
        update={
            "request": case.request.model_copy(update={"security_type": "unsecured"})
        }
    )
    first = analyze_case(unsecured)
    richer = unsecured.model_copy(
        update={
            "financials": unsecured.financials.model_copy(
                update={"collateral_capacity": money(9_000_000_000)}
            )
        }
    )
    second = analyze_case(richer)
    assert first.borrowing_base.status == "not_applicable"
    assert first.scorecard.grade == second.scorecard.grade
    assert first.scorecard.score == second.scorecard.score


def test_pricing_components_reconcile_and_are_versioned_policy_outputs() -> None:
    result = analyze_case(load_demo_case("stable-manufacturer"))
    pricing = result.pricing
    component_bps = sum(
        (
            pricing.risk_grade_spread_bps,
            pricing.tenor_adjustment_bps,
            pricing.security_adjustment_bps,
            pricing.amortization_adjustment_bps,
            pricing.covenant_adjustment_bps,
            pricing.concentration_adjustment_bps,
            pricing.relationship_adjustment_bps,
        )
    )
    expected = Decimal(pricing.reference_base_rate) + Decimal(component_bps) / Decimal(
        10_000
    )
    assert Decimal(pricing.indicative_all_in_rate) == expected
    assert "Educational" in pricing.disclaimer
    assert result.policy_version == "1.0.0"


def test_every_reverse_stress_output_has_solver_metadata_and_hides_failure_values() -> (
    None
):
    result = analyze_case(load_demo_case("stable-manufacturer"))
    assert len(result.reverse_stress.solvers) == 6
    assert {item.key for item in result.reverse_stress.solvers} == {
        "revenue_dscr",
        "margin_leverage",
        "rate_coverage",
        "working_capital_liquidity",
        "maximum_downside_loan",
        "maximum_severe_liquidity_loan",
    }
    for solver in result.reverse_stress.solvers:
        assert solver.iterations <= 60
        assert Decimal(solver.lower_bound) <= Decimal(solver.upper_bound)
        if not solver.converged:
            assert solver.result is None
            assert solver.result_money is None
            assert solver.failure_reason
    by_key = {item.key: item for item in result.reverse_stress.solvers}
    assert (
        result.reverse_stress.leverage_breach_margin_decline
        == by_key["margin_leverage"].result
    )
    assert (
        result.reverse_stress.maximum_downside_loan
        == by_key["maximum_downside_loan"].result_money
    )


def test_more_severe_assumptions_do_not_improve_forecast_metrics() -> None:
    case = load_demo_case("stable-manufacturer")
    scenario = case.scenarios["downside"]
    baseline = analyze_case(case).scenarios[1].years[0]

    lower_revenue = (
        analyze_case(
            case.model_copy(
                update={
                    "scenarios": {
                        **case.scenarios,
                        "downside": scenario.model_copy(
                            update={"revenue_growth": Decimal("-0.20")}
                        ),
                    }
                }
            )
        )
        .scenarios[1]
        .years[0]
    )
    assert Decimal(lower_revenue.dscr) <= Decimal(baseline.dscr)

    lower_margin = (
        analyze_case(
            case.model_copy(
                update={
                    "scenarios": {
                        **case.scenarios,
                        "downside": scenario.model_copy(
                            update={"ebitda_margin_change": Decimal("-0.08")}
                        ),
                    }
                }
            )
        )
        .scenarios[1]
        .years[0]
    )
    assert Decimal(lower_margin.leverage) >= Decimal(baseline.leverage)

    higher_rate = (
        analyze_case(
            case.model_copy(
                update={
                    "request": case.request.model_copy(
                        update={"rate_type": "floating"}
                    ),
                    "scenarios": {
                        **case.scenarios,
                        "downside": scenario.model_copy(
                            update={"rate_shock": Decimal("0.06")}
                        ),
                    },
                }
            )
        )
        .scenarios[1]
        .years[0]
    )
    assert Decimal(higher_rate.interest_coverage) <= Decimal(baseline.interest_coverage)

    higher_working_capital = (
        analyze_case(
            case.model_copy(
                update={
                    "scenarios": {
                        **case.scenarios,
                        "downside": scenario.model_copy(
                            update={"working_capital_pct_revenue": Decimal("0.20")}
                        ),
                    }
                }
            )
        )
        .scenarios[1]
        .years[0]
    )
    assert (
        higher_working_capital.ending_cash.amount_minor
        <= baseline.ending_cash.amount_minor
    )


def test_money_contract_enforces_exact_browser_range_currency_and_scale() -> None:
    assert MoneyValue(
        amount_minor=9_007_199_254_740_991,
        currency="USD",
        minor_unit_exponent=2,
    )
    with pytest.raises(ValueError):
        MoneyValue(
            amount_minor=9_007_199_254_740_992,
            currency="USD",
            minor_unit_exponent=2,
        )
    with pytest.raises(ValueError):
        MoneyValue(amount_minor=1, currency="usd", minor_unit_exponent=2)
    with pytest.raises(ValueError):
        MoneyValue(amount_minor=1, currency="USD", minor_unit_exponent=7)
