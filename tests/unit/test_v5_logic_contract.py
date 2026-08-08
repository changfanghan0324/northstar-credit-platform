from __future__ import annotations

from datetime import date
from decimal import Decimal

from northstar_credit_app import analyze_case, resolve_underwriting_financials
from northstar_credit_app.demo import load_demo_case
from northstar_credit_app.models import (
    DebtInstrumentInput,
    FinancialPeriodInput,
    FinancialSpreadInput,
    MoneyValue,
)


def money(value: int) -> MoneyValue:
    return MoneyValue(amount_minor=value, currency="USD")


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
    base = case.financials

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
            income_statement={"revenue": money(value), "ebitda": money(value // 5)},
            balance_sheet={
                "cash": money(value),
                "current_assets": money(value * 2),
                "current_liabilities": money(value),
                "short_term_debt": base.short_term_borrowings,
                "current_maturities": base.current_maturities,
                "long_term_debt": base.long_term_debt,
                "lease_liabilities": base.finance_leases,
                "equity": money(value),
                "total_liabilities": money(value),
                "total_assets": money(value * 2),
            },
            cash_flow={"operating_cash_flow": money(value // 2)},
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
    assert resolved.financials.unrestricted_cash.amount_minor == 500_000
    assert resolved.snapshot.balance_sheet_source_period_id == "current"
    assert resolved.snapshot.source_lineage["unrestricted_cash"] == ["current"]


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
