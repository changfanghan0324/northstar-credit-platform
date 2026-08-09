"""Multi-period spreading, reconciliation, and normalization summaries."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from credit_engine import Money, debt_service_coverage, gross_debt_to_ebitda
from northstar_policy import CreditPolicy

from .models import (
    AdjustmentSummaryView,
    CaseInput,
    DebtReconciliationView,
    FinancialInput,
    FinancialPeriodInput,
    FinancialSpreadingView,
    MoneyValue,
    ResolvedFinancialSnapshot,
    SourceAuthority,
)


@dataclass(frozen=True, slots=True)
class FinancialResolution:
    """Resolution result shared by every downstream underwriting consumer."""

    financials: FinancialInput
    snapshot: ResolvedFinancialSnapshot


_DECISION_CRITICAL_FINANCIAL_FIELDS = (
    "revenue",
    "ebit",
    "ebitda",
    "depreciation_amortization",
    "cfo",
    "cash_taxes",
    "maintenance_capex",
    "working_capital_increase",
    "cash_interest",
    "scheduled_principal",
    "unrestricted_cash",
    "current_assets",
    "current_liabilities",
    "short_term_borrowings",
    "current_maturities",
    "long_term_debt",
    "finance_leases",
    "total_assets",
    "total_liabilities",
    "equity",
)
_PERIOD_SOURCE_FIELDS = {
    "revenue",
    "ebit",
    "ebitda",
    "depreciation_amortization",
    "cfo",
    "cash_taxes",
    "maintenance_capex",
    "working_capital_increase",
    "cash_interest",
    "unrestricted_cash",
    "current_assets",
    "current_liabilities",
    "accounts_receivable",
    "inventory",
    "short_term_borrowings",
    "current_maturities",
    "long_term_debt",
    "finance_leases",
    "total_assets",
    "total_liabilities",
    "equity",
    "net_income",
    "capex",
}


@dataclass(frozen=True, slots=True)
class _FiscalYtdWindow:
    """Named FY/current-YTD/prior-YTD sources for the canonical LTM method."""

    fiscal_year: FinancialPeriodInput
    current_ytd: FinancialPeriodInput
    prior_ytd: FinancialPeriodInput

    @property
    def periods(self) -> tuple[FinancialPeriodInput, ...]:
        return (self.fiscal_year, self.current_ytd, self.prior_ytd)


def _snapshot_hash(
    financials: FinancialInput, *, basis: str, source_period_ids: list[str]
) -> str:
    payload = {
        "resolver_version": "v6.2",
        "basis": basis,
        "source_period_ids": source_period_ids,
        "financials": financials.model_dump(mode="json"),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _period_money(
    period: FinancialPeriodInput,
    statement: str,
    field: str,
    template: MoneyValue,
) -> MoneyValue | None:
    value = getattr(getattr(period, statement), field, None)
    if value is None:
        return None
    if value.currency != period.currency:
        return None
    # FinancialPeriod.scale is display/import metadata. Values crossing the API
    # boundary are already normalized to exact minor units by the editor/importer;
    # multiplying here would double-scale thousands and millions.
    return MoneyValue(
        amount_minor=value.amount_minor,
        currency=template.currency,
        minor_unit_exponent=template.minor_unit_exponent,
    )


def _sum_period_money(
    periods: list[FinancialPeriodInput],
    statement: str,
    field: str,
    template: MoneyValue,
) -> MoneyValue | None:
    values = [_period_money(item, statement, field, template) for item in periods]
    if not values or any(value is None for value in values):
        return None
    return MoneyValue(
        amount_minor=sum(value.amount_minor for value in values if value is not None),
        currency=template.currency,
        minor_unit_exponent=template.minor_unit_exponent,
    )


def _fy_ytd_money(
    selected: list[FinancialPeriodInput],
    statement: str,
    field: str,
    template: MoneyValue,
) -> MoneyValue | None:
    if len(selected) != 3:
        return None
    fy, current, prior = selected
    values = [
        _period_money(item, statement, field, template) for item in (fy, current, prior)
    ]
    if any(value is None for value in values):
        return None
    fy_value, current_value, prior_value = (
        value for value in values if value is not None
    )
    return MoneyValue(
        amount_minor=fy_value.amount_minor
        + current_value.amount_minor
        - prior_value.amount_minor,
        currency=template.currency,
        minor_unit_exponent=template.minor_unit_exponent,
    )


def _quarter_key(period: FinancialPeriodInput) -> tuple[int, int]:
    if period.fiscal_quarter is None:
        raise ValueError(f"{period.label}: fiscal quarter metadata is required")
    return period.fiscal_year, period.fiscal_quarter


def _validate_common_periods(
    periods: list[FinancialPeriodInput], expected_currency: str
) -> list[str]:
    issues: list[str] = []
    scopes = {period.entity_scope for period in periods}
    bases = {period.accounting_basis for period in periods}
    calendars = {period.fiscal_calendar for period in periods}
    mappings = {period.mapping_version for period in periods}
    if len(scopes) > 1:
        issues.append("Selected periods must use one entity scope")
    if len(bases) > 1:
        issues.append("Selected periods must use one accounting basis")
    if len(calendars) > 1:
        issues.append("Selected periods must use one fiscal calendar")
    if len(mappings) > 1:
        issues.append("Selected periods must use one mapping version")
    for period in periods:
        if period.currency != expected_currency:
            issues.append(
                f"{period.label}: currency {period.currency} does not match {expected_currency}"
            )
        if period.start_date > period.end_date:
            issues.append(f"{period.label}: end date precedes start date")
        if not period.source_reference.strip():
            issues.append(f"{period.label}: source reference is missing")
    for index, first in enumerate(periods):
        for second in periods[index + 1 :]:
            if (
                max(first.start_date, second.start_date)
                <= min(first.end_date, second.end_date)
                and first.period_type == second.period_type
            ):
                issues.append(
                    f"{first.label} overlaps {second.label}; same-type periods must not overlap"
                )
    return issues


def _apply_period_precedence(
    periods: list[FinancialPeriodInput],
) -> list[FinancialPeriodInput]:
    """Choose one deterministic filing when an amended/restated period repeats."""
    grouped: dict[tuple[str, int, int | None], list[FinancialPeriodInput]] = {}
    for period in periods:
        key = (period.period_type, period.fiscal_year, period.fiscal_quarter)
        grouped.setdefault(key, []).append(period)
    selected: list[FinancialPeriodInput] = []
    source_priority = {
        "audited": 3,
        "reviewed": 2,
        "management": 1,
        "derived": 0,
        "forecast": 0,
    }
    for candidates in grouped.values():
        selected.append(
            max(
                candidates,
                key=lambda item: (
                    item.restated or item.amendment_flag,
                    item.filing_date or date.min,
                    item.audited,
                    source_priority[item.source_type],
                    item.id,
                ),
            )
        )
    return sorted(selected, key=lambda item: item.end_date)


def _valid_four_quarters(
    periods: list[FinancialPeriodInput], expected_currency: str
) -> tuple[list[FinancialPeriodInput] | None, list[str]]:
    quarters = sorted(
        (item for item in periods if item.period_type == "quarter"),
        key=lambda item: item.end_date,
    )
    issues = _validate_common_periods(quarters, expected_currency)
    if len(quarters) < 4:
        return None, [*issues, "Four contiguous quarters are required for LTM"]
    latest = quarters[-4:]
    try:
        keys = [_quarter_key(item) for item in latest]
    except ValueError as error:
        return None, [*issues, str(error)]
    expected = []
    year, quarter = keys[0]
    for _ in latest:
        expected.append((year, quarter))
        quarter += 1
        if quarter == 5:
            year += 1
            quarter = 1
    if keys != expected:
        issues.append("Latest four quarters are not contiguous")
    if any(item.source_type == "forecast" for item in latest):
        issues.append("Forecast periods cannot be used as historical LTM quarters")
    if any(item.flow_type != "discrete" for item in latest):
        issues.append(
            "LTM quarters must be discrete periods; cumulative quarters cannot be summed"
        )
    return (latest if not issues else None), issues


def _valid_ytd_window(
    periods: list[FinancialPeriodInput], expected_currency: str
) -> tuple[
    _FiscalYtdWindow | None,
    list[str],
]:
    issues: list[str] = []
    fiscal_years = sorted(
        (item for item in periods if item.period_type == "historical_fiscal_year"),
        key=lambda item: item.end_date,
    )
    ytd = sorted(
        (item for item in periods if item.period_type == "ytd"),
        key=lambda item: item.end_date,
    )
    if not fiscal_years or len(ytd) < 2:
        return None, [
            "FY plus current YTD minus prior YTD requires one FY and two YTD periods"
        ]
    # Select a named comparable pair by fiscal-year relationship. Do not use
    # positional ``[-1]``/``[-2]`` selection: a spread may contain several YTD
    # cuts, and the latest two rows are not necessarily comparable.
    candidates: list[
        tuple[FinancialPeriodInput, FinancialPeriodInput, FinancialPeriodInput]
    ] = []
    for current in sorted(ytd, key=lambda item: item.end_date, reverse=True):
        for prior in sorted(ytd, key=lambda item: item.end_date, reverse=True):
            if prior.id == current.id or prior.end_date >= current.end_date:
                continue
            fy = max(
                (
                    item
                    for item in fiscal_years
                    if item.fiscal_year == prior.fiscal_year
                ),
                key=lambda item: item.end_date,
                default=None,
            )
            if fy is None:
                continue
            # The prior YTD must be a strict subset of the named FY, and the
            # current/prior cuts must describe the same fiscal stub. Equal
            # duration alone is insufficient (e.g. Mar vs Jun YTD).
            same_fiscal_cut = (
                prior.start_date.month == fy.start_date.month
                and prior.start_date.day == fy.start_date.day
                and current.start_date.month == fy.start_date.month
                and current.start_date.day == fy.start_date.day
                and prior.end_date.month == current.end_date.month
                and prior.end_date.day == current.end_date.day
                and fy.start_date <= prior.start_date
                and prior.end_date < fy.end_date
                and current.fiscal_year == fy.fiscal_year + 1
            )
            if same_fiscal_cut:
                candidates.append((fy, current, prior))
    if not candidates:
        return None, [
            "No comparable YTD pair: prior YTD must be a strict FY subset with the same fiscal start and period-end cut"
        ]
    # Use the latest current cut, then its latest matching prior cut. This is
    # deterministic while keeping the selected sources named and auditable.
    fy, current, prior = max(
        candidates, key=lambda item: (item[1].end_date, item[2].end_date)
    )
    current_days = (current.end_date - current.start_date).days
    prior_days = (prior.end_date - prior.start_date).days
    comparable_cutoff = abs(current_days - prior_days) <= 3
    same_currency = all(
        item.currency == expected_currency for item in (fy, current, prior)
    )
    valid_year_relation = (
        current.fiscal_year == fy.fiscal_year + 1
        and prior.fiscal_year == fy.fiscal_year
    )
    if current.flow_type != "cumulative" or prior.flow_type != "cumulative":
        issues.append(
            "Current and prior YTD periods must be explicitly marked cumulative"
        )
    if not comparable_cutoff:
        issues.append("Current and prior YTD periods are not comparable in duration")
    if not same_currency:
        issues.append("FY and YTD periods must use the case currency")
    if not valid_year_relation:
        issues.append("FY and YTD fiscal-year metadata is not contiguous")
    return (
        _FiscalYtdWindow(
            fiscal_year=fy,
            current_ytd=current,
            prior_ytd=prior,
        )
        if not issues
        else None
    ), issues


def _derived_financials(
    case: CaseInput,
    selected: list[FinancialPeriodInput],
    *,
    flow_mode: str,
    ytd_window: _FiscalYtdWindow | None = None,
) -> tuple[FinancialInput, dict[str, list[str]], set[str]]:
    """Materialize period values into the legacy-compatible input contract.

    Missing optional lines inherit the legacy value for compatibility, but their
    lineage is retained and the resolver marks the snapshot with a warning. Core
    earnings and revenue lines must be present in the selected source.
    """

    base = case.financials
    template = case.request.amount
    lineage: dict[str, list[str]] = {}
    calculated_fields: set[str] = set()
    updates: dict[str, MoneyValue] = {}
    latest_source = max(selected, key=lambda item: item.end_date)
    if flow_mode == "fy_ytd":
        if ytd_window is None:
            raise ValueError("FY/YTD resolution requires a named YTD window")
        balance_source = ytd_window.current_ytd
    else:
        balance_source = latest_source
    flow_fields = {
        "revenue": ("income_statement", "revenue"),
        "ebit": ("income_statement", "ebit"),
        "depreciation_amortization": ("income_statement", "depreciation_amortization"),
        "cash_interest": ("income_statement", "cash_interest"),
        "cash_taxes": ("income_statement", "cash_taxes"),
        "net_income": ("income_statement", "net_income"),
        "cfo": ("cash_flow", "operating_cash_flow"),
        "maintenance_capex": ("cash_flow", "maintenance_capex"),
        "working_capital_increase": ("cash_flow", "working_capital_change"),
        "capex": ("cash_flow", "capital_expenditures"),
    }
    balance_fields = {
        "unrestricted_cash": ("balance_sheet", "cash"),
        "current_assets": ("balance_sheet", "current_assets"),
        "current_liabilities": ("balance_sheet", "current_liabilities"),
        "accounts_receivable": ("balance_sheet", "accounts_receivable"),
        "inventory": ("balance_sheet", "inventory"),
        "short_term_borrowings": ("balance_sheet", "short_term_debt"),
        "current_maturities": ("balance_sheet", "current_maturities"),
        "long_term_debt": ("balance_sheet", "long_term_debt"),
        "finance_leases": ("balance_sheet", "lease_liabilities"),
        "equity": ("balance_sheet", "equity"),
        "total_liabilities": ("balance_sheet", "total_liabilities"),
        "total_assets": ("balance_sheet", "total_assets"),
    }
    for field, (statement, source_field) in flow_fields.items():
        if flow_mode == "sum":
            value = _sum_period_money(selected, statement, source_field, template)
        elif flow_mode == "fy_ytd":
            value = _fy_ytd_money(selected, statement, source_field, template)
        else:
            value = _period_money(latest_source, statement, source_field, template)
        if value is not None:
            updates[field] = value
            lineage[field] = [item.id for item in selected]
        else:
            lineage[field] = ["legacy_snapshot"]
    for field, (statement, source_field) in balance_fields.items():
        value = _period_money(balance_source, statement, source_field, template)
        if value is not None:
            updates[field] = value
            lineage[field] = [balance_source.id]
        else:
            lineage[field] = ["legacy_snapshot"]
    # EBITDA may be directly reported or derived from EBIT + D&A. Never inherit
    # stale EBIT/D&A when the selected period supplies a direct EBITDA line.
    if flow_mode == "sum":
        ebitda = _sum_period_money(selected, "income_statement", "ebitda", template)
    elif flow_mode == "fy_ytd":
        ebitda = _fy_ytd_money(selected, "income_statement", "ebitda", template)
    else:
        ebitda = _period_money(latest_source, "income_statement", "ebitda", template)
    if ebitda is not None:
        source_ids = [item.id for item in selected]
        source_ebit = updates.get("ebit")
        source_da = updates.get("depreciation_amortization")
        if source_ebit is None and source_da is None:
            updates["ebit"] = ebitda
            updates["depreciation_amortization"] = MoneyValue(
                amount_minor=0,
                currency=template.currency,
                minor_unit_exponent=template.minor_unit_exponent,
            )
            calculated_fields.update({"ebit", "depreciation_amortization"})
        elif source_ebit is None and source_da is not None:
            updates["ebit"] = MoneyValue(
                amount_minor=ebitda.amount_minor - source_da.amount_minor,
                currency=template.currency,
                minor_unit_exponent=template.minor_unit_exponent,
            )
            calculated_fields.add("ebit")
        elif source_ebit is not None and source_da is None:
            updates["depreciation_amortization"] = MoneyValue(
                amount_minor=ebitda.amount_minor - source_ebit.amount_minor,
                currency=template.currency,
                minor_unit_exponent=template.minor_unit_exponent,
            )
            calculated_fields.add("depreciation_amortization")
        lineage["ebitda"] = source_ids
        lineage["ebit"] = source_ids
        lineage["depreciation_amortization"] = source_ids
    elif "ebit" in updates and "depreciation_amortization" in updates:
        ebitda = MoneyValue(
            amount_minor=updates["ebit"].amount_minor
            + updates["depreciation_amortization"].amount_minor,
            currency=template.currency,
            minor_unit_exponent=template.minor_unit_exponent,
        )
        calculated_fields.add("ebitda")
        lineage["ebitda"] = lineage.get("ebit", []) + lineage.get(
            "depreciation_amortization", []
        )
    # Keep the FinancialInput contract's EBITDA represented by EBIT + D&A.
    if ebitda is not None and ebitda.amount_minor != (
        updates["ebit"].amount_minor + updates["depreciation_amortization"].amount_minor
    ):
        updates["ebit"] = MoneyValue(
            amount_minor=ebitda.amount_minor
            - updates["depreciation_amortization"].amount_minor,
            currency=template.currency,
            minor_unit_exponent=template.minor_unit_exponent,
        )
        calculated_fields.add("ebit")
    for field in FinancialInput.model_fields:
        lineage.setdefault(field, ["legacy_snapshot"])
    return base.model_copy(update=updates), lineage, calculated_fields


def resolve_underwriting_financials(case: CaseInput) -> FinancialResolution:
    """Select and materialize the one financial basis used by underwriting.

    A failed non-empty spread never silently falls back to the legacy snapshot. That
    behavior is intentional: fallback would hide a broken analyst submission behind
    plausible-looking old numbers. Legacy cases are supported only when no spread was
    supplied at all.
    """

    periods = _apply_period_precedence(case.financial_spread.periods)
    if not periods:
        snapshot = ResolvedFinancialSnapshot(
            snapshot_hash=_snapshot_hash(
                case.financials, basis="legacy_snapshot", source_period_ids=[]
            ),
            basis="legacy_snapshot",
            period_id="legacy-snapshot",
            period_end=None,
            source_period_ids=[],
            source_lineage={
                field: ["legacy_snapshot"] for field in FinancialInput.model_fields
            },
            source_authority={
                field: "manual_legacy_snapshot" for field in FinancialInput.model_fields
            },
            source_window={"basis": "legacy_snapshot"},
            financials=case.financials,
            reconciliation_status="warning",
            warnings=[
                "Legacy single-period snapshot; add a validated multi-period spread for trend analysis."
            ],
        )
        return FinancialResolution(case.financials, snapshot)

    method = case.financial_spread.selected_ltm_method
    selected: list[FinancialPeriodInput] | None = None
    basis: str = "derived_ltm"
    flow_mode = "sum"
    ytd_window: _FiscalYtdWindow | None = None
    issues = _validate_common_periods(periods, case.request.amount.currency)
    if method == "reported_ltm":
        reported = [item for item in periods if item.period_type == "ltm"]
        selected = [reported[-1]] if reported and not issues else None
        basis = "reported_ltm"
        flow_mode = "latest"
        if not reported:
            issues.append("Selected reported LTM method has no reported LTM period")
    elif method == "latest_four_quarters":
        selected, quarter_issues = _valid_four_quarters(
            periods, case.request.amount.currency
        )
        issues.extend(quarter_issues)
        basis = "derived_ltm"
        flow_mode = "sum"
    elif method == "fiscal_year_plus_current_ytd_minus_prior_ytd":
        ytd_window, ytd_issues = _valid_ytd_window(
            periods, case.request.amount.currency
        )
        issues.extend(ytd_issues)
        if ytd_window is not None and not issues:
            selected = list(ytd_window.periods)
        else:
            issues.append(
                "FY plus current YTD minus prior YTD requires comparable fiscal windows"
            )
        basis = "derived_ltm"
        flow_mode = "fy_ytd"
    else:
        issues.append(
            "A selected LTM method is required when financial spread periods are supplied"
        )

    # When both independent LTM paths are available, do not silently choose a
    # divergent result. A restatement or mapping change must be visible to credit.
    alternate: tuple[list[FinancialPeriodInput], str] | None = None
    if method == "latest_four_quarters":
        ytd_window, ytd_issues = _valid_ytd_window(
            periods, case.request.amount.currency
        )
        if ytd_window is not None and not ytd_issues:
            alternate = (list(ytd_window.periods), "fy_ytd")
            ytd_window = None
    elif method == "fiscal_year_plus_current_ytd_minus_prior_ytd":
        quarter_window, quarter_issues = _valid_four_quarters(
            periods, case.request.amount.currency
        )
        if quarter_window is not None and not quarter_issues:
            alternate = (quarter_window, "four_quarters")
    if selected is not None and alternate is not None:
        alternate_periods, alternate_mode = alternate
        for statement, field in (
            ("income_statement", "revenue"),
            ("income_statement", "ebitda"),
        ):
            selected_value = (
                _sum_period_money(selected, statement, field, case.request.amount)
                if flow_mode == "sum"
                else _fy_ytd_money(selected, statement, field, case.request.amount)
            )
            alternate_value = (
                _fy_ytd_money(alternate_periods, statement, field, case.request.amount)
                if alternate_mode == "fy_ytd"
                else _sum_period_money(
                    alternate_periods, statement, field, case.request.amount
                )
            )
            if selected_value is not None and alternate_value is not None:
                tolerance = max(
                    1, int(abs(selected_value.amount_minor) * Decimal("0.005"))
                )
                if (
                    abs(selected_value.amount_minor - alternate_value.amount_minor)
                    > tolerance
                ):
                    issues.append(
                        f"LTM {field} diverges between selected and alternate methods"
                    )

    if selected is None:
        snapshot = ResolvedFinancialSnapshot(
            snapshot_hash=_snapshot_hash(
                case.financials, basis="derived_ltm", source_period_ids=[]
            ),
            basis="derived_ltm",
            period_id="unresolved",
            period_end=None,
            source_period_ids=[],
            source_lineage={},
            source_authority={},
            source_window={"basis": "unresolved"},
            financials=case.financials,
            reconciliation_status="blocked",
            blocking_issues=sorted(set(issues)),
        )
        return FinancialResolution(case.financials, snapshot)

    resolved, lineage, calculated_fields = _derived_financials(
        case,
        selected,
        flow_mode=flow_mode,
        ytd_window=ytd_window,
    )
    quality_warnings: list[str] = []
    source_types = {item.source_type for item in selected}
    if len(source_types) > 1:
        quality_warnings.append(
            "Selected periods mix source types; analyst review is required before reliance"
        )
    if any(item.restated for item in selected):
        quality_warnings.append("At least one selected period is restated")
    if any(item.pro_forma for item in selected):
        quality_warnings.append("At least one selected period is pro forma")
    # Decision-critical lines may not silently inherit a legacy value after an
    # analyst supplied a non-empty spread. Debt schedule reconciliation can add
    # instrument-level detail, but the canonical balance sheet still needs its
    # own source for these headline metrics.
    core_fields = _DECISION_CRITICAL_FINANCIAL_FIELDS
    missing_core = [
        field
        for field in core_fields
        if field != "scheduled_principal" and lineage.get(field) == ["legacy_snapshot"]
    ]
    if resolved.revenue.amount_minor <= 0:
        issues.append("revenue: canonical source must contain positive revenue")
    if all(
        getattr(resolved, field).amount_minor == 0
        for field in ("revenue", "ebit", "depreciation_amortization", "cfo")
    ):
        issues.append("canonical source contains no non-zero operating financial data")
    issues.extend(
        f"{field}: required canonical line item is missing from the selected source"
        for field in missing_core
    )
    bs_difference = resolved.total_assets.amount_minor - (
        resolved.total_liabilities.amount_minor + resolved.equity.amount_minor
    )
    if abs(bs_difference) > 1:
        balance_source = (
            ytd_window.current_ytd
            if flow_mode == "fy_ytd" and ytd_window is not None
            else max(selected, key=lambda item: item.end_date)
        )
        issues.append(
            f"{balance_source.label}: assets do not reconcile to liabilities plus equity ({bs_difference} minor units)"
        )
    status = (
        "blocked"
        if issues
        else "warning"
        if quality_warnings
        or any(
            field in _PERIOD_SOURCE_FIELDS and source == ["legacy_snapshot"]
            for field, source in lineage.items()
        )
        else "pass"
    )
    latest_source = max(selected, key=lambda item: item.end_date)
    balance_source = (
        ytd_window.current_ytd
        if flow_mode == "fy_ytd" and ytd_window is not None
        else latest_source
    )
    source_authority: dict[str, SourceAuthority] = {}
    for field, source in lineage.items():
        if field in calculated_fields:
            source_authority[field] = "calculated"
        elif source == ["legacy_snapshot"]:
            source_authority[field] = (
                "blocked" if field in core_fields else "manual_legacy_snapshot"
            )
        else:
            source_authority[field] = "period_spread"
    blocked_authority_fields = sorted(
        field for field, authority in source_authority.items() if authority == "blocked"
    )
    defaulted_authority_fields = sorted(
        field
        for field, authority in source_authority.items()
        if authority == "defaulted"
    )
    source_window = {
        "fiscal_year": ytd_window.fiscal_year.id if ytd_window else None,
        "current_ytd": ytd_window.current_ytd.id if ytd_window else None,
        "prior_ytd": ytd_window.prior_ytd.id if ytd_window else None,
        "fiscal_year_end": (
            ytd_window.fiscal_year.end_date.isoformat() if ytd_window else None
        ),
        "current_ytd_end": (
            ytd_window.current_ytd.end_date.isoformat() if ytd_window else None
        ),
        "prior_ytd_end": (
            ytd_window.prior_ytd.end_date.isoformat() if ytd_window else None
        ),
    }
    snapshot = ResolvedFinancialSnapshot(
        snapshot_hash=_snapshot_hash(
            resolved, basis=basis, source_period_ids=[item.id for item in selected]
        ),
        basis=basis,  # type: ignore[arg-type]
        period_id=(
            latest_source.id
            if len(selected) == 1
            else "derived-" + ("fy-ytd" if flow_mode == "fy_ytd" else "four-quarters")
        ),
        period_end=balance_source.end_date,
        source_period_ids=[item.id for item in selected],
        flow_source_period_ids=[item.id for item in selected],
        balance_sheet_source_period_id=balance_source.id,
        source_lineage=lineage,
        source_authority=source_authority,
        source_window=source_window,
        bridge_formula=(
            "FY + Current YTD - Prior Comparable YTD" if flow_mode == "fy_ytd" else None
        ),
        blocked_authority_fields=blocked_authority_fields,
        defaulted_authority_fields=defaulted_authority_fields,
        financials=resolved,
        reconciliation_status=status,  # type: ignore[arg-type]
        warnings=[
            *quality_warnings,
            *[
                f"{field}: legacy snapshot inherited because the selected period omitted this optional line"
                for field, source in lineage.items()
                if source == ["legacy_snapshot"]
                and field in _PERIOD_SOURCE_FIELDS
                and field not in missing_core
            ],
            *(
                [
                    "scheduled_principal: authority is blocked until a debt schedule is reconciled"
                ]
                if source_authority.get("scheduled_principal") == "blocked"
                else []
            ),
        ],
        blocking_issues=sorted(set(issues)),
    )
    return FinancialResolution(resolved, snapshot)


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
    resolution = resolve_underwriting_financials(case)
    periods = _apply_period_precedence(case.financial_spread.periods)
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
            resolved_snapshot=resolution.snapshot,
            reconciliation_status=resolution.snapshot.reconciliation_status,
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
        window, window_issues = _valid_ytd_window(periods, case.request.amount.currency)
        if window is not None and not window_issues:
            ltm_id = "derived-fy-plus-current-ytd-minus-prior-ytd"
            status = "available"
        else:
            warnings.extend(
                window_issues or ["YTD periods are not comparable; LTM is blocked"]
            )
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
        resolved_snapshot=resolution.snapshot,
        reconciliation_status=resolution.snapshot.reconciliation_status,
    )


def summarize_adjustments(
    case: CaseInput,
    policy: CreditPolicy,
    adjusted_ebitda_value: Money,
    debt_reconciliation: DebtReconciliationView,
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
    signed_ebit = sum(
        abs(item.ebit_impact.amount_minor) * (1 if item.direction == "positive" else -1)
        for item in approved
    )
    signed_cfads = sum(
        abs(item.cfads_impact.amount_minor)
        * (1 if item.direction == "positive" else -1)
        for item in approved
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
    debt = debt_reconciliation.selected_debt.engine()
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
    service = debt_reconciliation.selected_interest.engine().add(
        debt_reconciliation.selected_scheduled_principal.engine()
    )
    dscr_before = debt_service_coverage(reported_cfads, service)
    dscr_after = debt_service_coverage(adjusted_cfads, service)
    return AdjustmentSummaryView(
        entries=case.normalization_adjustments,
        reported_ebitda=_money(reported_minor, template),
        approved_adjustment=_money(adjustment_minor, template),
        adjusted_ebitda=_money(adjusted_ebitda_value.amount_minor, template),
        approved_ebit=_money(signed_ebit, template),
        approved_cfads_impact=_money(signed_cfads, template),
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
