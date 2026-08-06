"""Multi-period spreading, reconciliation, and normalization summaries."""

from __future__ import annotations

from decimal import Decimal

from credit_engine import Money, debt_service_coverage, gross_debt, gross_debt_to_ebitda
from northstar_policy import CreditPolicy

from .models import (
    AdjustmentSummaryView,
    CaseInput,
    FinancialPeriodInput,
    FinancialSpreadingView,
    MoneyValue,
)


def _money(value: int, template: MoneyValue) -> MoneyValue:
    return MoneyValue(
        amount_minor=value,
        currency=template.currency,
        minor_unit_exponent=template.minor_unit_exponent,
    )


def _period_value(period: FinancialPeriodInput, field: str) -> str | None:
    for statement in (period.income_statement, period.balance_sheet, period.cash_flow):
        value = getattr(statement, field, None)
        if isinstance(value, MoneyValue):
            return str(value.amount_minor)
    return None


def analyze_spreading(case: CaseInput) -> FinancialSpreadingView:
    periods = sorted(case.financial_spread.periods, key=lambda item: item.end_date)
    if not periods:
        return FinancialSpreadingView(
            periods=[],
            historical_years=1,
            forecast_years=0,
            selected_ltm_method="reported_ltm",
            ltm_period_id="legacy-snapshot",
            ltm_status="legacy_snapshot",
            reconciliation_warnings=[
                "Legacy single-period snapshot; add at least three historical fiscal years for trend analysis."
            ],
            trend={
                "labels": ["Prior", "Current"],
                "revenue": [
                    str(case.financials.prior_revenue.amount_minor),
                    str(case.financials.revenue.amount_minor),
                ],
                "ebitda": [
                    str(case.financials.prior_adjusted_ebitda.amount_minor),
                    str(
                        case.financials.ebit.amount_minor
                        + case.financials.depreciation_amortization.amount_minor
                    ),
                ],
            },
        )

    warnings: list[str] = []
    currency = case.request.amount.currency
    for period in periods:
        if period.currency != currency:
            warnings.append(
                f"{period.label}: currency does not match the case currency"
            )
        balance = period.balance_sheet
        if (
            balance.total_assets is not None
            and balance.total_liabilities is not None
            and balance.equity is not None
        ):
            difference = balance.total_assets.amount_minor - (
                balance.total_liabilities.amount_minor + balance.equity.amount_minor
            )
            if abs(difference) > 1:
                warnings.append(
                    f"{period.label}: assets do not reconcile to liabilities plus equity ({difference} minor units)"
                )

    reported_ltm = [item for item in periods if item.period_type == "ltm"]
    quarters = [item for item in periods if item.period_type == "quarter"]
    ytd = [item for item in periods if item.period_type == "ytd"]
    historical = [
        item for item in periods if item.period_type == "historical_fiscal_year"
    ]
    method = case.financial_spread.selected_ltm_method
    ltm_id: str | None = None
    status = "blocked"
    if method == "reported_ltm" and reported_ltm:
        ltm_id = reported_ltm[-1].id
        status = "available"
    elif method == "latest_four_quarters" and len(quarters) >= 4:
        latest = sorted(quarters, key=lambda item: item.end_date)[-4:]
        if all(
            latest[index].end_date < latest[index + 1].start_date for index in range(3)
        ):
            ltm_id = "derived-latest-four-quarters"
            status = "available"
        else:
            warnings.append("Latest four quarters overlap; LTM is blocked")
    elif (
        method == "fiscal_year_plus_current_ytd_minus_prior_ytd"
        and historical
        and len(ytd) >= 2
    ):
        latest_ytd = sorted(ytd, key=lambda item: item.end_date)[-2:]
        comparable = (latest_ytd[0].end_date - latest_ytd[0].start_date).days == (
            latest_ytd[1].end_date - latest_ytd[1].start_date
        ).days
        if comparable:
            ltm_id = "derived-fy-plus-current-ytd-minus-prior-ytd"
            status = "available"
        else:
            warnings.append("YTD periods are not comparable; LTM is blocked")
    else:
        warnings.append("Selected LTM method does not have compatible source periods")

    return FinancialSpreadingView(
        periods=periods,
        historical_years=len(historical),
        forecast_years=len(
            [item for item in periods if item.period_type == "forecast"]
        ),
        selected_ltm_method=method,
        ltm_period_id=ltm_id,
        ltm_status=status,  # type: ignore[arg-type]
        reconciliation_warnings=warnings,
        trend={
            "labels": [item.label for item in periods],
            "revenue": [_period_value(item, "revenue") for item in periods],
            "ebitda": [_period_value(item, "ebitda") for item in periods],
            "cash": [_period_value(item, "cash") for item in periods],
            "debt": [
                str(
                    sum(
                        value.amount_minor
                        for value in (
                            item.balance_sheet.short_term_debt,
                            item.balance_sheet.current_maturities,
                            item.balance_sheet.long_term_debt,
                            item.balance_sheet.lease_liabilities,
                        )
                        if value is not None
                    )
                )
                for item in periods
            ],
        },
    )


def summarize_adjustments(
    case: CaseInput, policy: CreditPolicy, adjusted_ebitda_value: Money
) -> AdjustmentSummaryView:
    template = case.financials.ebit
    reported_minor = (
        case.financials.ebit.amount_minor
        + case.financials.depreciation_amortization.amount_minor
    )
    approved = [
        item
        for item in case.normalization_adjustments
        if item.approval_status == "approved"
    ]
    if approved:
        adjustment_minor = sum(
            abs(item.ebitda_impact.amount_minor)
            * (1 if item.direction == "positive" else -1)
            for item in approved
        )
    else:
        adjustment_minor = (
            case.financials.positive_ebitda_adjustments.amount_minor
            - case.financials.negative_ebitda_adjustments.amount_minor
        )
    positive_minor = sum(
        abs(item.ebitda_impact.amount_minor)
        for item in approved
        if item.direction == "positive"
    )
    if not approved:
        positive_minor = max(
            0, case.financials.positive_ebitda_adjustments.amount_minor
        )
    positive_pct = (
        Decimal(positive_minor) / Decimal(abs(reported_minor))
        if reported_minor
        else Decimal(1)
    )
    debt = gross_debt(
        short_term_borrowings=case.financials.short_term_borrowings.engine(),
        current_maturities=case.financials.current_maturities.engine(),
        long_term_debt=case.financials.long_term_debt.engine(),
        finance_lease_liabilities=case.financials.finance_leases.engine(),
    )
    before = gross_debt_to_ebitda(debt, _money(reported_minor, template).engine())
    after = gross_debt_to_ebitda(debt, adjusted_ebitda_value)
    reported_cfads = _money(
        reported_minor
        - case.financials.cash_taxes.amount_minor
        - case.financials.maintenance_capex.amount_minor
        - case.financials.working_capital_increase.amount_minor
        - case.financials.mandatory_pension.amount_minor,
        template,
    ).engine()
    adjusted_cfads = _money(
        adjusted_ebitda_value.amount_minor
        - case.financials.cash_taxes.amount_minor
        - case.financials.maintenance_capex.amount_minor
        - case.financials.working_capital_increase.amount_minor
        - case.financials.mandatory_pension.amount_minor,
        template,
    ).engine()
    service = _money(
        case.financials.cash_interest.amount_minor
        + case.financials.scheduled_principal.amount_minor,
        template,
    ).engine()
    dscr_before = debt_service_coverage(reported_cfads, service)
    dscr_after = debt_service_coverage(adjusted_cfads, service)
    return AdjustmentSummaryView(
        entries=case.normalization_adjustments,
        reported_ebitda=_money(reported_minor, template),
        approved_adjustment=_money(adjustment_minor, template),
        adjusted_ebitda=_money(adjusted_ebitda_value.amount_minor, template),
        positive_adjustment_pct=str(positive_pct.quantize(Decimal("0.0001"))),
        warning=(
            "Positive adjustments exceed the illustrative policy threshold."
            if positive_pct > policy.maximum_ebitda_adjustment_pct
            else None
        ),
        leverage_before=None if before.value is None else str(before.value),
        leverage_after=None if after.value is None else str(after.value),
        dscr_before=None if dscr_before.value is None else str(dscr_before.value),
        dscr_after=None if dscr_after.value is None else str(dscr_after.value),
    )
