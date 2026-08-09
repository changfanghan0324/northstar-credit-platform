from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from northstar_credit_app import analyze_case, resolve_underwriting_financials
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
    )
    result = analyze_case(case.model_copy(update={"debt_instruments": [instrument]}))
    assert result.debt_reconciliation is not None
    assert result.debt_reconciliation.status == "blocked"
    assert result.analysis_status == "blocked"
    assert result.pricing.status == "blocked"


def test_partial_schedule_labels_residual_and_abl_availability_is_net_of_drawn() -> (
    None
):
    case = load_demo_case("stable-manufacturer")
    instrument = DebtInstrumentInput(
        name="Long-term schedule only",
        principal=case.financials.long_term_debt,
        annual_rate=Decimal("0.06"),
        scheduled_amortization=money(100_000_000),
        maturity_year=5,
    )
    result = analyze_case(case.model_copy(update={"debt_instruments": [instrument]}))
    assert result.debt_reconciliation is not None
    assert result.debt_reconciliation.aggregate_mode is True
    assert result.debt_reconciliation.residual_debt is not None
    assert "residual" in result.debt_reconciliation.coverage_basis_notice

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
    base = calculate_borrowing_base(abl, load_policy()[0])
    assert base.borrowing_base is not None and base.availability is not None
    assert base.borrowing_base.amount_minor == 800_000_000
    assert base.availability.amount_minor == 300_000_000
    assert base.commitment is not None and base.outstanding is not None


def test_rate_decision_and_bullet_exit_are_explicit() -> None:
    case = load_demo_case("software-services")
    result = analyze_case(case)
    assert result.rate_decision is not None
    assert result.rate_decision.underwritten_rate == result.capacity.underwritten_rate
    assert result.facility_mechanics is not None
    assert result.facility_mechanics.amortization_type == "partial"
    assert result.scenarios[0].maturity_test_status in {"pass", "breach", "blocked"}
