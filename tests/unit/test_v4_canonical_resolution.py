from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from northstar_credit_app import analyze_case, resolve_underwriting_financials
from northstar_credit_app.demo import load_demo_case
from northstar_credit_app.models import (
    AccountsReceivableBaseInput,
    BusinessRiskEvidenceInput,
    CaseInput,
    FinancialPeriodInput,
    FinancialSpreadInput,
    MoneyValue,
)


def m(value: int, currency: str = "USD") -> MoneyValue:
    return MoneyValue(amount_minor=value, currency=currency)


def period(
    case: CaseInput,
    *,
    period_id: str,
    label: str,
    period_type: str,
    fiscal_year: int,
    fiscal_quarter: int | None,
    start: date,
    end: date,
    revenue: int,
    ebitda: int,
    flow_type: str = "discrete",
) -> FinancialPeriodInput:
    f = case.financials
    return FinancialPeriodInput(
        id=period_id,
        label=label,
        period_type=period_type,  # type: ignore[arg-type]
        start_date=start,
        end_date=end,
        fiscal_year=fiscal_year,
        fiscal_quarter=fiscal_quarter,
        source_type="management",
        source_reference=f"synthetic/{period_id}",
        flow_type=flow_type,  # type: ignore[arg-type]
        income_statement={
            "revenue": m(revenue),
            "ebitda": m(ebitda),
            "ebit": m(ebitda - 10_000),
            "depreciation_amortization": m(10_000),
            "cash_interest": m(f.cash_interest.amount_minor // 4),
            "cash_taxes": m(f.cash_taxes.amount_minor // 4),
            "net_income": m(f.net_income.amount_minor // 4),
        },
        balance_sheet={
            "cash": m(f.unrestricted_cash.amount_minor),
            "current_assets": m(f.current_assets.amount_minor),
            "current_liabilities": m(f.current_liabilities.amount_minor),
            "accounts_receivable": m(f.accounts_receivable.amount_minor),
            "inventory": m(f.inventory.amount_minor),
            "short_term_debt": m(f.short_term_borrowings.amount_minor),
            "current_maturities": m(f.current_maturities.amount_minor),
            "long_term_debt": m(f.long_term_debt.amount_minor),
            "lease_liabilities": m(f.finance_leases.amount_minor),
            "equity": m(f.equity.amount_minor),
            "total_liabilities": m(f.total_liabilities.amount_minor),
            "total_assets": m(f.total_assets.amount_minor),
        },
        cash_flow={
            "operating_cash_flow": m(f.cfo.amount_minor // 4),
            "maintenance_capex": m(f.maintenance_capex.amount_minor // 4),
            "capital_expenditures": m(f.capex.amount_minor // 4),
            "working_capital_change": m(f.working_capital_increase.amount_minor // 4),
        },
    )


def with_spread(
    case: CaseInput, periods: list[FinancialPeriodInput], method: str
) -> CaseInput:
    return case.model_copy(
        update={
            "financial_spread": FinancialSpreadInput(
                periods=periods,
                selected_ltm_method=method,  # type: ignore[arg-type]
            )
        }
    )


def test_four_quarters_are_real_ltm_source_and_legacy_snapshot_is_not_used() -> None:
    case = load_demo_case("stable-manufacturer")
    quarters = [
        period(
            case,
            period_id=f"q{quarter}",
            label=f"Q{quarter} 2025",
            period_type="quarter",
            fiscal_year=2025,
            fiscal_quarter=quarter,
            start=date(2025, (quarter - 1) * 3 + 1, 1),
            end=date(2025, (quarter - 1) * 3 + 3, 28),
            revenue=quarter * 1_000_000,
            ebitda=quarter * 100_000,
        )
        for quarter in range(1, 5)
    ]
    resolved = resolve_underwriting_financials(
        with_spread(case, quarters, "latest_four_quarters")
    )
    assert resolved.snapshot.reconciliation_status == "pass"
    assert resolved.snapshot.source_period_ids == ["q1", "q2", "q3", "q4"]
    assert resolved.financials.revenue.amount_minor == 10_000_000
    assert (
        resolved.financials.ebit.amount_minor
        + resolved.financials.depreciation_amortization.amount_minor
        == 1_000_000
    )
    result = analyze_case(with_spread(case, quarters, "latest_four_quarters"))
    assert result.case.financials.revenue.amount_minor == 10_000_000
    assert result.financial_spreading.resolved_snapshot is not None


def test_ytd_formula_requires_cumulative_periods_and_reconciles() -> None:
    case = load_demo_case("stable-manufacturer")
    fy = period(
        case,
        period_id="fy24",
        label="FY 2024",
        period_type="historical_fiscal_year",
        fiscal_year=2024,
        fiscal_quarter=None,
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        revenue=12_000_000,
        ebitda=1_200_000,
    )
    prior = period(
        case,
        period_id="ytd24",
        label="YTD Jun 2024",
        period_type="ytd",
        fiscal_year=2024,
        fiscal_quarter=None,
        start=date(2024, 1, 1),
        end=date(2024, 6, 30),
        revenue=5_000_000,
        ebitda=500_000,
        flow_type="cumulative",
    )
    current = period(
        case,
        period_id="ytd25",
        label="YTD Jun 2025",
        period_type="ytd",
        fiscal_year=2025,
        fiscal_quarter=None,
        start=date(2025, 1, 1),
        end=date(2025, 6, 30),
        revenue=6_000_000,
        ebitda=600_000,
        flow_type="cumulative",
    )
    resolved = resolve_underwriting_financials(
        with_spread(
            case, [fy, prior, current], "fiscal_year_plus_current_ytd_minus_prior_ytd"
        )
    )
    assert resolved.snapshot.reconciliation_status == "pass"
    assert resolved.financials.revenue.amount_minor == 13_000_000
    discrete = current.model_copy(update={"flow_type": "discrete"})
    blocked = resolve_underwriting_financials(
        with_spread(
            case, [fy, prior, discrete], "fiscal_year_plus_current_ytd_minus_prior_ytd"
        )
    )
    assert blocked.snapshot.reconciliation_status == "blocked"
    assert any("cumulative" in issue for issue in blocked.snapshot.blocking_issues)


def test_gap_or_missing_core_never_falls_back_to_legacy_snapshot() -> None:
    case = load_demo_case("stable-manufacturer")
    q1 = period(
        case,
        period_id="q1",
        label="Q1 2025",
        period_type="quarter",
        fiscal_year=2025,
        fiscal_quarter=1,
        start=date(2025, 1, 1),
        end=date(2025, 3, 31),
        revenue=1_000_000,
        ebitda=100_000,
    )
    q2 = q1.model_copy(
        update={
            "id": "q2",
            "label": "Q2 2025",
            "fiscal_quarter": 2,
            "start_date": date(2025, 4, 1),
            "end_date": date(2025, 6, 30),
        }
    )
    q4 = q1.model_copy(
        update={
            "id": "q4",
            "label": "Q4 2025",
            "fiscal_quarter": 4,
            "start_date": date(2025, 10, 1),
            "end_date": date(2025, 12, 31),
        }
    )
    q5 = q1.model_copy(
        update={
            "id": "q5",
            "label": "Q1 2026",
            "fiscal_year": 2026,
            "fiscal_quarter": 1,
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 3, 31),
        }
    )
    unresolved = resolve_underwriting_financials(
        with_spread(case, [q1, q2, q4, q5], "latest_four_quarters")
    )
    assert unresolved.snapshot.reconciliation_status == "blocked"
    assert any("contiguous" in issue for issue in unresolved.snapshot.blocking_issues)
    result = analyze_case(with_spread(case, [q1, q2, q4, q5], "latest_four_quarters"))
    assert result.analysis_status == "blocked"
    assert result.pricing.status == "blocked"
    assert result.pricing.indicative_all_in_rate is None
    assert result.capacity.status == "blocked"
    assert result.capacity.underwritten_rate is None


def test_all_zero_canonical_spread_blocks_and_snapshot_hash_is_replayable() -> None:
    case = load_demo_case("stable-manufacturer")
    zero = period(
        case,
        period_id="zero",
        label="Q1 2025",
        period_type="quarter",
        fiscal_year=2025,
        fiscal_quarter=1,
        start=date(2025, 1, 1),
        end=date(2025, 3, 31),
        revenue=0,
        ebitda=0,
    )
    # Four identical zero periods are valid metadata but not valid underwriting data.
    periods = [
        zero.model_copy(
            update={
                "id": f"zero-{quarter}",
                "label": f"Q{quarter} 2025",
                "fiscal_quarter": quarter,
                "start_date": date(2025, (quarter - 1) * 3 + 1, 1),
                "end_date": date(2025, quarter * 3, 28),
            }
        )
        for quarter in range(1, 5)
    ]
    spread_case = with_spread(case, periods, "latest_four_quarters")
    first = resolve_underwriting_financials(spread_case)
    second = resolve_underwriting_financials(spread_case)
    assert first.snapshot.reconciliation_status == "blocked"
    assert any("positive revenue" in item for item in first.snapshot.blocking_issues)
    assert first.snapshot.snapshot_hash == second.snapshot.snapshot_hash
    assert case.financials.revenue.amount_minor != 0
    with pytest.raises((TypeError, ValueError)):
        first.snapshot.snapshot_hash = "mutated"  # type: ignore[misc]


def test_amended_period_wins_deterministically() -> None:
    case = load_demo_case("stable-manufacturer")
    original = period(
        case,
        period_id="q1-original",
        label="Q1 2025 original",
        period_type="quarter",
        fiscal_year=2025,
        fiscal_quarter=1,
        start=date(2025, 1, 1),
        end=date(2025, 3, 31),
        revenue=1_000_000,
        ebitda=100_000,
    )
    amended = original.model_copy(
        update={
            "id": "q1-amended",
            "label": "Q1 2025 amended",
            "amendment_flag": True,
            "restated": True,
            "filing_date": date(2026, 1, 1),
        }
    )
    # The period helper stores revenue under income_statement; update that nested value.
    amended = amended.model_copy(
        update={
            "income_statement": amended.income_statement.model_copy(
                update={"revenue": m(2_000_000)}
            )
        }
    )
    quarters = [
        original,
        amended,
        original.model_copy(
            update={
                "id": "q2",
                "label": "Q2",
                "fiscal_quarter": 2,
                "start_date": date(2025, 4, 1),
                "end_date": date(2025, 6, 30),
            }
        ),
        original.model_copy(
            update={
                "id": "q3",
                "label": "Q3",
                "fiscal_quarter": 3,
                "start_date": date(2025, 7, 1),
                "end_date": date(2025, 9, 30),
            }
        ),
        original.model_copy(
            update={
                "id": "q4",
                "label": "Q4",
                "fiscal_quarter": 4,
                "start_date": date(2025, 10, 1),
                "end_date": date(2025, 12, 31),
            }
        ),
    ]
    resolved = resolve_underwriting_financials(
        with_spread(case, quarters, "latest_four_quarters")
    )
    assert resolved.snapshot.source_period_ids == ["q1-amended", "q2", "q3", "q4"]
    assert resolved.financials.revenue.amount_minor == 5_000_000


def test_mechanics_distinguish_bullet_and_revolver_draws() -> None:
    case = load_demo_case("stable-manufacturer")
    bullet = case.model_copy(
        update={
            "request": case.request.model_copy(
                update={
                    "amortization_type": "bullet",
                    "bullet_percentage": Decimal("1"),
                }
            )
        }
    )
    bullet_year = next(
        item for item in analyze_case(bullet).scenarios if item.name == "base"
    ).years[0]
    assert (
        bullet_year.scheduled_amortization.amount_minor
        == case.financials.scheduled_principal.amount_minor
    )
    revolver = case.model_copy(
        update={
            "request": case.request.model_copy(
                update={
                    "facility_type": "revolver",
                    "amortization_type": "revolver",
                    "initial_drawn_amount": m(100_000_000),
                    "commitment_fee_bps": 50,
                }
            )
        }
    )
    revolver_year = next(
        item for item in analyze_case(revolver).scenarios if item.name == "base"
    ).years[0]
    assert revolver_year.new_facility.amount_minor == 100_000_000
    assert revolver_year.revolver_remaining.amount_minor >= 0


def test_invalid_collateral_and_qualitative_band_are_rejected() -> None:
    with pytest.raises(ValueError, match="deductions cannot exceed"):
        AccountsReceivableBaseInput(
            gross_receivables=m(10),
            ineligible_receivables=m(11),
            past_due_receivables=m(0),
            cross_aged_receivables=m(0),
            foreign_receivables=m(0),
            concentration_reserve=m(0),
            dilution_reserve=m(0),
            advance_rate=Decimal("0.8"),
        )
    case = load_demo_case("stable-manufacturer")
    with pytest.raises(ValueError, match="inconsistent"):
        BusinessRiskEvidenceInput.model_validate(
            case.business_risk.factor_evidence["industry"].model_dump(
                mode="python", exclude={"score", "band"}
            )
            | {"score": Decimal("90"), "band": "weak"}
        )
