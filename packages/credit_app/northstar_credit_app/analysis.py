"""Deterministic underwriting orchestration; all numbers originate here."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, localcontext
from typing import Literal, cast

import credit_engine
from credit_engine import (
    Money,
    adjusted_debt_to_ebitda,
    adjusted_ebitda,
    annual_debt_service,
    cfads,
    cfo_to_debt,
    current_ratio,
    debt_service_coverage,
    ebitda,
    ebitda_margin,
    eligible_cash,
    gross_debt_to_ebitda,
    interest_coverage,
    net_debt,
    net_debt_to_ebitda,
    quick_ratio,
)
from credit_engine.types import RatioReason, RatioResult, RatioStatus
from northstar_policy import CreditPolicy, load_policy

from .facility import (
    assess_facility,
    calculate_borrowing_base,
    calculate_pricing,
    calculate_revolver_abl,
)
from .models import (
    AnalysisResult,
    BorrowingBaseView,
    CapacityConstraintView,
    CapacityView,
    CaseInput,
    CovenantView,
    DebtReconciliationView,
    DebtSource,
    DecisionView,
    FinancialInput,
    MoneyValue,
    PolicyCheckView,
    RateDecisionView,
    RatioView,
    ResolvedFacilityMechanics,
    ReverseStressView,
    RevolverAblView,
    ScenarioView,
    ScenarioYearView,
    ScorecardView,
    ScoreComponentView,
)
from .solvers import solve_reverse_stress
from .spreading import (
    analyze_spreading,
    resolve_underwriting_financials,
    summarize_adjustments,
)

ZERO = Decimal(0)
ONE = Decimal(1)
HUNDRED = Decimal(100)
BusinessRiskKey = Literal[
    "industry",
    "competitive_position",
    "customer_concentration",
    "diversification",
    "management_policy",
    "governance_event",
]


def _money(value: MoneyValue) -> Money:
    return value.engine()


def _view(value: Money) -> MoneyValue:
    return MoneyValue(
        amount_minor=value.amount_minor,
        currency=value.currency,
        minor_unit_exponent=value.minor_unit_exponent,
    )


def _new_money(amount_minor: int, template: Money) -> Money:
    return Money(
        amount_minor=amount_minor,
        currency=template.currency,
        minor_unit_exponent=template.minor_unit_exponent,
    )


def _signed_adjustment_total(case: CaseInput, field: str) -> int:
    approved = [
        item
        for item in case.normalization_adjustments
        if item.approval_status == "approved"
    ]
    if not approved:
        return 0
    return sum(
        abs(getattr(item, field).amount_minor)
        * (1 if item.direction == "positive" else -1)
        for item in approved
    )


def _resolve_facility_mechanics(case: CaseInput) -> ResolvedFacilityMechanics:
    request = case.request
    blocking_issues: list[str] = []
    kind = (
        "revolver"
        if request.facility_type == "asset_based"
        else request.amortization_type
    )
    if kind is None:
        kind = (
            "revolver"
            if request.facility_type in {"revolver", "asset_based"}
            else "fully_amortizing"
            if request.amortization_years is not None
            else "bullet"
        )
    if request.facility_type == "asset_based" and request.amortization_type not in {
        None,
        "revolver",
    }:
        blocking_issues.append(
            "Asset-based facilities must resolve to revolver mechanics; the submitted amortization type conflicts."
        )
    if (
        request.facility_type == "asset_based"
        and request.security_type != "asset_based"
    ):
        blocking_issues.append(
            "Asset-based facilities must declare asset-based security so collateral mechanics are explicit."
        )
    if request.facility_type == "term_loan" and request.amortization_type == "revolver":
        blocking_issues.append(
            "Term loans cannot declare revolver amortization mechanics."
        )
    if kind == "bullet" and request.bullet_percentage <= 0:
        blocking_issues.append(
            "Bullet mechanics require a positive balloon percentage."
        )
    if kind == "partial" and request.bullet_percentage <= 0:
        blocking_issues.append(
            "Partial-balloon mechanics require a positive balloon percentage."
        )
    if kind == "revolver" and request.bullet_percentage not in {
        Decimal("0"),
        Decimal("1"),
    }:
        blocking_issues.append(
            "Revolver mechanics cannot carry a partial or bullet balloon percentage."
        )
    initial = request.initial_drawn_amount or request.amount.model_copy(
        update={"amount_minor": 0}
    )
    return ResolvedFacilityMechanics(
        facility_type=request.facility_type,
        amortization_type=kind,
        commitment=request.amount,
        initial_drawn=initial,
        bullet_percentage=str(request.bullet_percentage),
        amortization_years=request.amortization_years,
        maturity_years=request.maturity_years,
        availability_period_years=request.availability_period_years,
        commitment_fee_bps=request.commitment_fee_bps,
        mandatory_prepayment=str(request.mandatory_prepayment),
        security_type=request.security_type,
        status="blocked" if blocking_issues else "available",
        explanation=(
            "Facility mechanics are blocked: " + " ".join(blocking_issues)
            if blocking_issues
            else "Resolved once from explicit facility mechanics and reused by downstream views."
        ),
        blocking_issues=tuple(blocking_issues),
    )


def _rate_decision(
    case: CaseInput,
    mechanics: ResolvedFacilityMechanics,
    pricing_rate: Decimal | None,
) -> RateDecisionView:
    index = (
        case.request.base_rate
        if case.request.rate_type == "floating"
        else case.pricing.reference_base_rate
    )
    floor = case.request.rate_floor
    underwritten_index = max(index, floor)
    all_in = _underwritten_rate(case, pricing_rate)
    spread_bps = max(
        0, int(((all_in - underwritten_index) * Decimal(10000)).quantize(Decimal(1)))
    )
    return RateDecisionView(
        index_rate=str(index),
        floor_rate=str(floor),
        shocked_index_rate=str(underwritten_index),
        spread_bps=spread_bps,
        underwritten_rate=str(all_in.quantize(Decimal("0.0001"))),
        commitment_fee_bps=mechanics.commitment_fee_bps,
        upfront_fee_bps=case.request.upfront_fee_bps,
        status="available" if pricing_rate is not None else "blocked",
        explanation="Floor applies to the index; the spread is applied once and the resulting rate is the underwritten rate.",
    )


def _reconcile_debt(
    case: CaseInput, financials: FinancialInput
) -> DebtReconciliationView:
    template = case.request.amount

    def value(amount_minor: int) -> MoneyValue:
        return MoneyValue(
            amount_minor=amount_minor,
            currency=template.currency,
            minor_unit_exponent=template.minor_unit_exponent,
        )

    balance_minor = sum(
        getattr(financials, field).amount_minor
        for field in (
            "short_term_borrowings",
            "current_maturities",
            "long_term_debt",
            "finance_leases",
        )
    )
    balance = value(balance_minor)
    reported_interest = financials.cash_interest
    if not case.debt_instruments:
        return DebtReconciliationView(
            status="aggregate_mode",
            selected_source="balance_sheet_aggregate",
            selected_debt=balance,
            selected_scheduled_principal=financials.scheduled_principal,
            selected_interest=reported_interest,
            selected_interest_source="reported_interest",
            # Aggregate debt has no instrument rate metadata. For stress, the
            # unclassified balance is conservatively treated as floating; this
            # keeps an aggregate-only case from silently receiving no rate shock.
            floating_principal=balance,
            interest_shock_basis="aggregate_conservative",
            balance_sheet_gross_debt=balance,
            instrument_gross_debt=None,
            scheduled_principal=financials.scheduled_principal,
            implied_interest=None,
            reported_interest=reported_interest,
            difference=None,
            tolerance=value(1),
            explanation="No instrument schedule supplied; aggregate balance-sheet debt is used consistently.",
            leverage_source="balance_sheet_aggregate",
            stress_source="balance_sheet_aggregate",
            maturity_source="balance_sheet_aggregate",
            aggregate_mode=True,
            coverage_basis_notice="Coverage uses aggregate balance-sheet debt because no instrument schedule was supplied.",
            residual_debt=None,
        )
    instrument_minor = sum(
        item.principal.amount_minor for item in case.debt_instruments
    )
    scheduled_minor = sum(
        item.scheduled_amortization.amount_minor for item in case.debt_instruments
    )
    floating_principal_minor = sum(
        item.principal.amount_minor
        for item in case.debt_instruments
        if item.rate_type == "floating"
    )
    implied_minor = sum(
        int(
            (
                Decimal(item.principal.amount_minor)
                * (
                    max(item.rate_floor, item.annual_rate + item.spread)
                    if item.rate_type == "floating"
                    else item.annual_rate
                )
            ).quantize(Decimal(1))
        )
        for item in case.debt_instruments
    )
    difference = balance_minor - instrument_minor
    # A schedule that explicitly covers only the long-term debt line is a
    # governed partial schedule; short-term debt, leases, and current maturities
    # remain on the aggregate balance-sheet basis rather than creating a false
    # mismatch. Any other unexplained difference remains a hard stop.
    schedule_scopes = {item.schedule_completeness for item in case.debt_instruments}
    explicit_scope = len(schedule_scopes) == 1 and "unspecified" not in schedule_scopes
    partial_long_term_schedule = (
        explicit_scope
        and schedule_scopes == {"partial"}
        and instrument_minor == case.financials.long_term_debt.amount_minor
        and case.financials.long_term_debt.amount_minor > 0
        and difference >= 0
    )
    # Use balance-sheet debt as the fixed denominator. A schedule below the
    # balance sheet suggests missing obligations, so its acceptable band is
    # tighter than an overstatement; the absolute floor protects tiny balances.
    debt_relative_tolerance = Decimal("0.0025") if difference > 0 else Decimal("0.005")
    tolerance_minor = max(1, int(abs(balance_minor) * debt_relative_tolerance))
    interest_difference = implied_minor - reported_interest.amount_minor
    interest_relative_tolerance = (
        Decimal("0.0025") if interest_difference > 0 else Decimal("0.005")
    )
    interest_tolerance_minor = max(
        1,
        int(abs(reported_interest.amount_minor) * interest_relative_tolerance),
    )
    residual_share = (
        Decimal(max(0, difference)) / Decimal(max(1, balance_minor))
        if balance_minor > 0
        else ZERO
    )
    partial_residual_too_large = (
        partial_long_term_schedule and residual_share > Decimal("0.20")
    )
    debt_status = (
        "reconciled"
        if partial_long_term_schedule and not partial_residual_too_large
        else "reconciled"
        if explicit_scope and schedule_scopes == {"complete"} and difference == 0
        else "immaterial_difference"
        if explicit_scope
        and schedule_scopes == {"complete"}
        and abs(difference) <= tolerance_minor
        else "blocked"
    )
    interest_mismatch = (
        explicit_scope
        and schedule_scopes == {"complete"}
        and abs(interest_difference) > interest_tolerance_minor
    )
    status = "blocked" if debt_status == "blocked" or interest_mismatch else debt_status
    selected_shock_basis: Literal[
        "instrument_rate_type",
        "aggregate_conservative",
        "partial_conservative_residual",
        "reported_aggregate",
    ]
    if partial_long_term_schedule and not partial_residual_too_large:
        selected_source: DebtSource = "partial_schedule_with_residual"
        selected_debt = balance
        # The residual's scheduled principal is unknown, so partial mode uses
        # the reported aggregate debt-service line for the full debt population
        # rather than overstating DSCR with only the scheduled subset.
        selected_scheduled = value(
            max(financials.scheduled_principal.amount_minor, scheduled_minor)
        )
        selected_interest = reported_interest
        selected_floating_principal = value(
            floating_principal_minor + max(0, difference)
        )
        selected_shock_basis = "partial_conservative_residual"
    elif status == "blocked":
        selected_source = "blocked_mismatch"
        selected_debt = balance
        selected_scheduled = financials.scheduled_principal
        selected_interest = reported_interest
        selected_floating_principal = value(0)
        selected_shock_basis = "reported_aggregate"
    else:
        selected_source = "instrument_schedule"
        selected_debt = value(instrument_minor)
        selected_scheduled = value(scheduled_minor)
        selected_interest = reported_interest
        selected_floating_principal = value(floating_principal_minor)
        selected_shock_basis = "instrument_rate_type"
    return DebtReconciliationView(
        status=cast(
            Literal["reconciled", "immaterial_difference", "blocked", "aggregate_mode"],
            status,
        ),
        selected_source=selected_source,
        selected_debt=selected_debt,
        selected_scheduled_principal=selected_scheduled,
        selected_interest=selected_interest,
        selected_interest_source="reported_interest",
        floating_principal=selected_floating_principal,
        interest_shock_basis=selected_shock_basis,
        balance_sheet_gross_debt=balance,
        instrument_gross_debt=value(instrument_minor),
        scheduled_principal=value(scheduled_minor),
        implied_interest=value(implied_minor),
        reported_interest=reported_interest,
        difference=value(difference),
        tolerance=value(tolerance_minor),
        interest_difference=value(interest_difference),
        interest_tolerance=value(interest_tolerance_minor),
        explanation=(
            "Instrument schedule reconciles to the balance sheet."
            if difference == 0
            else "Declared partial schedule leaves a residual above the 20% governed ceiling; reconciliation is blocked."
            if partial_residual_too_large
            else "Partial long-term schedule is explicitly combined with aggregate current and lease debt."
            if partial_long_term_schedule
            else "Difference is within the governed tolerance."
            if status == "immaterial_difference"
            else "Debt schedule interest does not reconcile to reported interest; leverage, DSCR, stress, and maturity outputs are blocked."
            if interest_mismatch
            else "Debt schedule does not reconcile to the balance sheet; leverage, DSCR, stress, and maturity outputs are blocked."
        ),
        leverage_source=selected_source,
        stress_source=selected_source,
        maturity_source=selected_source,
        aggregate_mode=partial_long_term_schedule,
        coverage_basis_notice=(
            "Coverage uses aggregate debt plus the supplied long-term schedule; unscheduled residual debt remains outstanding and is not silently amortized."
            if partial_long_term_schedule
            else "Coverage uses the selected debt reconciliation source: "
            + selected_source
            + "."
        ),
        residual_debt=(
            value(max(0, difference)) if partial_long_term_schedule else None
        ),
        residual_maturity_year=None,
        residual_maturity_status=(
            "unknown" if partial_long_term_schedule else "not_applicable"
        ),
    )


def _currency(value: MoneyValue) -> str:
    amount = Decimal(value.amount_minor) / (Decimal(10) ** value.minor_unit_exponent)
    return f"{value.currency} {amount:,.2f}"


def _currency_optional(value: MoneyValue | None) -> str:
    return _currency(value) if value is not None else "N/A"


def _scaled(amount: Money, factor: Decimal) -> Money:
    value = (Decimal(amount.amount_minor) * factor).quantize(
        Decimal(1), rounding=ROUND_HALF_UP
    )
    return _new_money(int(value), amount)


def _ratio_view(result: RatioResult) -> RatioView:
    return RatioView(
        metric_id=result.metric_id,
        status=result.status.value,
        value=None if result.value is None else str(result.value),
        reason_code=result.reason_code.value,
        label=result.professional_name,
        plain_label=result.plain_label,
        formula_id=result.formula_id,
        policy_ref=result.policy_ref,
        direction=(
            "lower_is_better" if "leverage" in result.metric_id else "higher_is_better"
        ),
        components=[
            {
                "name": item.name,
                "value": None if item.value is None else str(item.value),
                "currency": item.currency,
                "period": item.period,
            }
            for item in result.components
        ],
        model_version=credit_engine.__version__,
    )


def _blocked_ratio(metric_id: str, label: str, reason: str) -> RatioResult:
    """Create an explicit blocked metric; never coerce blocked inputs to zero."""
    return RatioResult(
        metric_id=metric_id,
        status=RatioStatus.BLOCKED,
        reason_code=RatioReason.MISSING_INPUT,
        plain_label=label,
        professional_name=label,
        formula_id="blocked_missing_authority",
        interpretation=reason,
        corrective_action="Provide the authoritative source and rerun the analysis.",
    )


def _scoreable(result: RatioResult, *, adverse_high: bool = False) -> Decimal | None:
    """Return an explicit score-band operand without inventing numeric data."""
    if result.is_ok:
        return result.value_exact
    if result.is_favorable_nm:
        return ZERO if adverse_high else Decimal("999999")
    if result.is_adverse_nm:
        return Decimal("999999") if adverse_high else ZERO
    return None


def _score_piece(
    key: str, score: Decimal, weight: Decimal, band: str
) -> ScoreComponentView:
    contribution = score * weight / HUNDRED
    return ScoreComponentView(
        key=key,
        score=str(score.quantize(Decimal("0.01"))),
        weight=str(weight),
        contribution=str(contribution.quantize(Decimal("0.01"))),
        band=band,
    )


def _linear_score(value: Decimal, lower: Decimal, upper: Decimal) -> Decimal:
    if value <= lower:
        return ZERO
    if value >= upper:
        return HUNDRED
    return ((value - lower) / (upper - lower) * HUNDRED).quantize(Decimal("0.01"))


def _scorecard(
    policy: CreditPolicy,
    leverage: RatioResult,
    coverage: RatioResult,
    dscr: RatioResult,
    liquidity: RatioResult,
    cfo_debt: RatioResult,
    margin: RatioResult,
    case: CaseInput,
) -> ScorecardView:
    leverage_value = _scoreable(leverage, adverse_high=True)
    coverage_value = _scoreable(coverage)
    dscr_value = _scoreable(dscr)
    liquidity_value = _scoreable(liquidity)
    cfo_debt_value = _scoreable(cfo_debt)
    margin_value = _scoreable(margin)
    critical = {
        "leverage": leverage_value,
        "coverage": coverage_value,
        "dscr": dscr_value,
        "liquidity": liquidity_value,
        "cash_flow": cfo_debt_value,
        "profitability": margin_value,
    }
    results = {
        "leverage": leverage,
        "coverage": coverage,
        "dscr": dscr,
        "liquidity": liquidity,
        "cash_flow": cfo_debt,
        "profitability": margin,
    }
    blocked_keys = [
        key
        for key, value in critical.items()
        if value is None or results[key].is_adverse_nm
    ]
    business_keys: tuple[BusinessRiskKey, ...] = (
        "industry",
        "competitive_position",
        "customer_concentration",
        "diversification",
        "management_policy",
        "governance_event",
    )
    missing_evidence = [
        key for key in business_keys if key not in case.business_risk.factor_evidence
    ]
    blocked_keys.extend(missing_evidence)
    leverage_score, leverage_band = policy.score_for(
        "leverage", leverage_value if leverage_value is not None else Decimal("999")
    )
    coverage_score, coverage_band = policy.score_for(
        "coverage", coverage_value if coverage_value is not None else ZERO
    )
    dscr_score, dscr_band = policy.score_for(
        "dscr", dscr_value if dscr_value is not None else ZERO
    )
    combined_coverage = (coverage_score + dscr_score) / Decimal(2)
    weight_map = {item.key: item.weight for item in policy.weights}
    direct: dict[str, tuple[Decimal, str]] = {
        "leverage": (leverage_score, leverage_band),
        "coverage": (combined_coverage, f"{coverage_band}; {dscr_band}"),
        "liquidity": (
            _linear_score(
                liquidity_value if liquidity_value is not None else ZERO,
                Decimal("0.75"),
                Decimal("2.0"),
            ),
            "Current ratio",
        ),
        "cash_flow": (
            _linear_score(
                cfo_debt_value if cfo_debt_value is not None else ZERO,
                Decimal("0.05"),
                Decimal("0.50"),
            ),
            "CFO / Debt",
        ),
        "profitability": (
            _linear_score(
                margin_value if margin_value is not None else ZERO,
                Decimal("0.05"),
                Decimal("0.25"),
            ),
            "EBITDA margin",
        ),
    }
    business = case.business_risk
    for risk_key in business_keys:
        factor_evidence = business.factor_evidence.get(risk_key)
        direct[risk_key] = (
            getattr(business, risk_key)
            if factor_evidence is None
            else factor_evidence.score,
            "Evidence required"
            if factor_evidence is None
            else factor_evidence.band.replace("_", " ").title(),
        )
    components = []
    for component_key, (score, band) in direct.items():
        piece = _score_piece(component_key, score, weight_map[component_key], band)
        factor_evidence = (
            case.business_risk.factor_evidence.get(component_key)
            if component_key in business_keys
            else None
        )
        if factor_evidence is not None:
            piece = piece.model_copy(update={"evidence": factor_evidence.evidence})
        if component_key in blocked_keys:
            piece = piece.model_copy(
                update={
                    "status": "blocked",
                    "score": "0.00",
                    "contribution": "0.00",
                    "evidence": "Critical input is missing or invalid; no numeric score was inferred.",
                }
            )
        components.append(piece)
    total = sum((Decimal(item.contribution) for item in components), ZERO)
    grade = None if blocked_keys else policy.grade_for(total)
    reported_ebitda_minor = (
        case.financials.ebit.amount_minor
        + case.financials.depreciation_amortization.amount_minor
    )
    adjustment_minor = abs(
        case.financials.positive_ebitda_adjustments.amount_minor
    ) + abs(case.financials.negative_ebitda_adjustments.amount_minor)
    adjustment_pct = (
        Decimal(adjustment_minor) / Decimal(abs(reported_ebitda_minor))
        if reported_ebitda_minor
        else ONE
    )
    penalties = ["Synthetic demonstration inputs"]
    penalty_points = 15 + len(blocked_keys) * 20
    if not case.debt_instruments and (
        case.financials.short_term_borrowings.amount_minor
        + case.financials.current_maturities.amount_minor
        + case.financials.long_term_debt.amount_minor
        + case.financials.finance_leases.amount_minor
        > 0
    ):
        penalty_points += 10
        penalties.append("Existing debt is supplied as aggregates, not instruments")
    if adjustment_pct > policy.material_reweighting_pct / HUNDRED:
        penalty_points += 10
        penalties.append("Material EBITDA adjustments require independent support")
    qualitative_values = [
        case.business_risk.industry,
        case.business_risk.competitive_position,
        case.business_risk.customer_concentration,
        case.business_risk.diversification,
        case.business_risk.management_policy,
        case.business_risk.governance_event,
    ]
    if min(qualitative_values) < Decimal("40"):
        penalty_points += 10
        penalties.append("A qualitative risk factor is below 40")
    confidence_score = max(0, 100 - penalty_points)
    confidence: Literal["high", "medium", "low", "blocked"] = (
        "blocked"
        if blocked_keys
        else "high"
        if confidence_score >= 80
        else "medium"
        if confidence_score >= 60
        else "low"
    )
    return ScorecardView(
        score=None if blocked_keys else str(total.quantize(Decimal("0.01"))),
        grade=grade,
        grade_label="Blocked — complete critical inputs"
        if grade is None
        else policy.grade_labels[grade],
        components=components,
        confidence=confidence,
        confidence_score=confidence_score,
        confidence_drivers=[
            "Deterministic formulas",
            "Versioned policy",
            "Source components retained",
            *(
                ["Instrument-level debt schedule supplied"]
                if case.debt_instruments
                else []
            ),
        ],
        confidence_penalties=[
            *penalties,
            *[f"Blocked critical factor: {key}" for key in blocked_keys],
        ],
        improvement_actions=(
            [
                f"Provide valid evidence for {key.replace('_', ' ')}"
                for key in blocked_keys
            ]
            or [
                "Replace synthetic values with independently verified borrower evidence",
                *(
                    ["Provide an instrument-level debt schedule"]
                    if not case.debt_instruments
                    else []
                ),
                *(
                    ["Document and independently support EBITDA adjustments"]
                    if adjustment_pct > policy.material_reweighting_pct / HUNDRED
                    else []
                ),
            ]
        ),
    )


def _annuity_capacity(payment_minor: Decimal, rate: Decimal, years: int) -> Decimal:
    if payment_minor <= ZERO:
        return ZERO
    if rate == ZERO:
        return payment_minor * Decimal(years)
    with localcontext() as context:
        context.prec = credit_engine.ENGINE_PRECISION
        return payment_minor * (ONE - (ONE + rate) ** Decimal(-years)) / rate


def _annual_payment(principal_minor: int, rate: Decimal, years: int) -> Decimal:
    principal = Decimal(principal_minor)
    if principal == ZERO:
        return ZERO
    if rate == ZERO:
        return principal / Decimal(years)
    with localcontext() as context:
        context.prec = credit_engine.ENGINE_PRECISION
        return principal * rate / (ONE - (ONE + rate) ** Decimal(-years))


def _underwritten_rate(case: CaseInput, pricing_rate: Decimal | None = None) -> Decimal:
    """Use one conservative all-in rate across capacity and stress scenarios."""
    request_floor = max(
        case.request.annual_rate,
        case.request.base_rate + case.request.rate_floor,
        case.pricing.reference_base_rate + case.request.rate_floor,
    )
    return max(request_floor, pricing_rate or ZERO)


def _amortization_kind(mechanics: ResolvedFacilityMechanics) -> str:
    return mechanics.amortization_type


def _capacity(
    case: CaseInput,
    policy: CreditPolicy,
    mechanics: ResolvedFacilityMechanics,
    debt_reconciliation: DebtReconciliationView,
    earnings: Money,
    cash_available: Money,
    existing_service: Money,
    borrowing_base: BorrowingBaseView,
    revolver_abl: RevolverAblView,
    underwritten_rate: Decimal | None = None,
    pricing_status: Literal["available", "blocked"] = "available",
) -> CapacityView:
    debt = debt_reconciliation.selected_debt.engine()
    request = mechanics.commitment.engine()
    maximum_debt = Decimal(earnings.amount_minor) * policy.maximum_leverage
    leverage_raw = maximum_debt - Decimal(debt.amount_minor)
    leverage_minor = max(
        0, int(leverage_raw.quantize(Decimal(1), rounding=ROUND_HALF_UP))
    )
    max_service = Decimal(cash_available.amount_minor) / policy.minimum_dscr
    available_service = max(ZERO, max_service - Decimal(existing_service.amount_minor))
    effective_rate = underwritten_rate or _underwritten_rate(case)
    amortization_kind = _amortization_kind(mechanics)
    if amortization_kind in {"bullet", "revolver"}:
        dscr_raw = (
            available_service / effective_rate
            if effective_rate > ZERO
            else available_service * Decimal(mechanics.maturity_years)
        )
    else:
        dscr_raw = _annuity_capacity(
            available_service,
            effective_rate,
            mechanics.amortization_years or mechanics.maturity_years,
        )
    dscr_minor = max(0, int(dscr_raw.quantize(Decimal(1), rounding=ROUND_HALF_UP)))
    collateral_applicable = mechanics.security_type in {"secured", "asset_based"}
    candidates = {
        "requested_amount": request.amount_minor,
        "leverage_capacity": leverage_minor,
        "dscr_capacity": dscr_minor,
        "policy_capacity": policy.policy_capacity_minor,
    }
    if mechanics.facility_type == "asset_based":
        candidates["collateral_capacity"] = (
            0
            if revolver_abl.availability is None
            else revolver_abl.availability.amount_minor
        )
    elif collateral_applicable:
        candidates["collateral_capacity"] = (
            case.financials.collateral_capacity.amount_minor
        )
    recommended_minor = min(candidates.values())
    binding = [
        key for key, value in candidates.items() if abs(value - recommended_minor) <= 1
    ]
    constraints = [
        CapacityConstraintView(
            key=key,
            label=key.replace("_", " ").title(),
            amount=_view(_new_money(value, request)),
            applicable=True,
            status=(
                "blocked"
                if key == "collateral_capacity"
                and mechanics.facility_type == "asset_based"
                and borrowing_base.status == "blocked"
                else "valid"
            ),
            reason=(
                borrowing_base.policy_notice
                if key == "collateral_capacity"
                and mechanics.facility_type == "asset_based"
                else "Calculated from the request, financial inputs, and active policy."
            ),
            policy_ref="policy.v1" if key == "policy_capacity" else None,
            binding=key in binding,
        )
        for key, value in candidates.items()
    ]
    if not collateral_applicable:
        constraints.append(
            CapacityConstraintView(
                key="collateral_capacity",
                label="Collateral capacity",
                amount=None,
                applicable=False,
                status="policy_not_applicable",
                reason="The proposed facility is unsecured; collateral does not constrain capacity.",
            )
        )
    return CapacityView(
        status=pricing_status,
        underwritten_rate=(
            str(effective_rate.quantize(Decimal("0.0001")))
            if pricing_status == "available"
            else None
        ),
        requested=_view(request),
        leverage=_view(_new_money(leverage_minor, request)),
        dscr=_view(_new_money(dscr_minor, request)),
        collateral=(
            borrowing_base.borrowing_base
            if mechanics.facility_type == "asset_based"
            else case.financials.collateral_capacity
            if collateral_applicable
            else None
        ),
        policy=_view(_new_money(policy.policy_capacity_minor, request)),
        recommended=_view(_new_money(recommended_minor, request)),
        binding_constraints=binding,
        constraints=constraints,
    )


def _scenario(
    name: str,
    case: CaseInput,
    policy: CreditPolicy,
    mechanics: ResolvedFacilityMechanics,
    debt_reconciliation: DebtReconciliationView,
    starting_cash: Money,
    capacity: CapacityView,
    revolver_abl: RevolverAblView,
    underwritten_rate: Decimal | None = None,
) -> ScenarioView:
    assumptions = case.scenarios[name]  # type: ignore[index]
    revenue = _money(case.financials.revenue)
    current_ebitda = _money(case.financials.ebit).add(
        _money(case.financials.depreciation_amortization)
    )
    initial_margin = (
        Decimal(current_ebitda.amount_minor) / Decimal(revenue.amount_minor)
        if revenue.amount_minor > 0
        else ZERO
    )
    existing_debt = debt_reconciliation.selected_debt.amount_minor
    commitment = capacity.recommended.amount_minor
    amortization_kind = _amortization_kind(mechanics)
    initial_draw = mechanics.initial_drawn.amount_minor
    initial_draw = min(commitment, max(0, initial_draw))
    new_debt = initial_draw if amortization_kind == "revolver" else commitment
    outstanding = existing_debt
    cash = starting_cash.amount_minor
    if amortization_kind == "revolver":
        base_limit = (
            revolver_abl.borrowing_base.amount_minor
            if revolver_abl.borrowing_base is not None
            else commitment
        )
        revolver_available = max(0, min(commitment, base_limit) - initial_draw)
    else:
        revolver_available = case.financials.undrawn_revolver.amount_minor
    minimum_cash = case.financials.minimum_operating_cash.amount_minor
    effective_new_rate = _underwritten_rate(case, underwritten_rate)
    if case.request.rate_type == "floating":
        effective_new_rate = max(
            case.request.rate_floor,
            effective_new_rate + assumptions.rate_shock,
        )
    amortization_years = mechanics.amortization_years or mechanics.maturity_years
    annual_payment = _annual_payment(new_debt, effective_new_rate, amortization_years)
    existing_interest = debt_reconciliation.selected_interest.amount_minor
    if debt_reconciliation.interest_shock_basis in {
        "instrument_rate_type",
        "aggregate_conservative",
        "partial_conservative_residual",
    }:
        # Keep reported interest as the base source while repricing only the
        # floating instrument population in a stress case. Fixed-rate debt is
        # not mechanically shocked.
        existing_interest += int(
            Decimal(debt_reconciliation.floating_principal.amount_minor)
            * assumptions.rate_shock
        )
    existing_principal = debt_reconciliation.selected_scheduled_principal.amount_minor
    # Keep the visible scenario table at three years, but roll bullet and
    # partial-balloon structures through contractual maturity so a five-year
    # balloon cannot appear safe merely because it is outside the table.
    calculation_horizon = max(
        3, mechanics.maturity_years if amortization_kind in {"bullet", "partial"} else 3
    )
    years: list[ScenarioYearView] = []
    first_breach: int | None = None
    first_stress_event: int | None = None
    liquidity_exhaustion: int | None = None
    for year in range(1, calculation_horizon + 1):
        beginning_debt = outstanding
        draw_allowed = (
            mechanics.availability_period_years is None
            or year <= mechanics.availability_period_years
        )
        new_facility = new_debt if year == 1 else 0
        debt_before_amortization = beginning_debt + new_facility
        growth = (
            assumptions.revenue_growth if year == 1 else assumptions.subsequent_growth
        )
        revenue = _scaled(revenue, ONE + growth)
        margin = initial_margin + assumptions.ebitda_margin_change
        earnings = _scaled(revenue, margin)
        taxes = _scaled(
            earnings,
            case.financials.tax_rate if earnings.amount_minor > 0 else ZERO,
        )
        maintenance_capex = _scaled(revenue, assumptions.maintenance_capex_pct_revenue)
        working_capital = _scaled(revenue, assumptions.working_capital_pct_revenue)
        available = (
            earnings.subtract(taxes)
            .subtract(maintenance_capex)
            .subtract(working_capital)
        )
        estimated_new_balance = max(0, debt_before_amortization - existing_debt)
        estimated_new_interest = Decimal(estimated_new_balance) * effective_new_rate
        if amortization_kind == "fully_amortizing":
            scheduled_new_principal = max(ZERO, annual_payment - estimated_new_interest)
        elif amortization_kind == "partial":
            scheduled_new_principal = max(
                ZERO,
                Decimal(commitment)
                * (ONE - Decimal(mechanics.bullet_percentage))
                / Decimal(max(1, amortization_years)),
            )
        elif amortization_kind == "bullet":
            # Contractual bullet principal is handled by the explicit maturity
            # test below, not as scheduled amortization in the annual roll.
            scheduled_new_principal = ZERO
        else:
            scheduled_new_principal = ZERO
        scheduled_amortization = min(
            Decimal(debt_before_amortization),
            Decimal(existing_principal) + scheduled_new_principal,
        )
        outstanding = max(0, debt_before_amortization - int(scheduled_amortization))
        average_debt = (
            Decimal(debt_before_amortization) + Decimal(outstanding)
        ) / Decimal(2)
        existing_rate = (
            Decimal(existing_interest) / Decimal(existing_debt)
            if existing_debt > 0
            else ZERO
        )
        existing_average = min(average_debt, Decimal(existing_debt))
        new_average = max(ZERO, average_debt - existing_average)
        commitment_fee = (
            Decimal(max(0, commitment - estimated_new_balance))
            * Decimal(mechanics.commitment_fee_bps)
            / Decimal(10_000)
            if amortization_kind == "revolver"
            else ZERO
        )
        base_interest = (
            existing_average * existing_rate + new_average * effective_new_rate
        ) + commitment_fee
        optional_paydown = ZERO
        revolver_draw = ZERO
        for _ in range(8):
            total_interest = (
                base_interest + revolver_draw * effective_new_rate / Decimal(2)
            )
            total_service = total_interest + scheduled_amortization
            pre_financing_cash = Decimal(cash + available.amount_minor) - total_service
            required_draw = max(ZERO, Decimal(minimum_cash) - pre_financing_cash)
            next_draw = (
                min(Decimal(revolver_available), required_draw)
                if amortization_kind == "revolver" and draw_allowed
                else ZERO
            )
            if abs(next_draw - revolver_draw) <= Decimal(1):
                revolver_draw = next_draw
                break
            revolver_draw = next_draw
        total_interest = base_interest + revolver_draw * effective_new_rate / Decimal(2)
        total_service = total_interest + scheduled_amortization
        pre_financing_cash = Decimal(cash + available.amount_minor) - total_service
        revolver_available -= int(revolver_draw)
        outstanding += int(revolver_draw)
        cash_after_draw = pre_financing_cash + revolver_draw
        mandatory_prepayment = min(
            Decimal(max(0, outstanding)),
            max(
                ZERO,
                Decimal(available.amount_minor)
                * Decimal(mechanics.mandatory_prepayment),
            ),
        )
        if mandatory_prepayment > 0:
            outstanding -= int(mandatory_prepayment)
            cash_after_draw -= mandatory_prepayment
            optional_paydown = mandatory_prepayment
            total_service += mandatory_prepayment
        cash_shortfall = max(ZERO, Decimal(minimum_cash) - cash_after_draw)
        unpaid_debt_service = max(ZERO, -cash_after_draw)
        cash = int(cash_after_draw.quantize(Decimal(1), rounding=ROUND_HALF_UP))
        interest_money = _new_money(
            int(total_interest.quantize(Decimal(1), rounding=ROUND_HALF_UP)), revenue
        )
        service_money = _new_money(
            int(total_service.quantize(Decimal(1), rounding=ROUND_HALF_UP)), revenue
        )
        leverage_result = gross_debt_to_ebitda(
            _new_money(outstanding, revenue), earnings
        )
        coverage_result = interest_coverage(earnings, interest_money)
        dscr_result = debt_service_coverage(available, service_money)
        instrument_maturities = (
            sum(
                item.principal.amount_minor
                for item in case.debt_instruments
                if item.maturity_year == year
            )
            if debt_reconciliation.selected_source == "instrument_schedule"
            else 0
        )
        refinancing_need = min(Decimal(outstanding), Decimal(instrument_maturities))
        if year >= mechanics.maturity_years and outstanding > 0:
            refinancing_need = Decimal(outstanding)
        leverage_breach = (
            leverage_result.value_exact > policy.maximum_leverage
            if leverage_result.value_exact is not None
            else not leverage_result.is_favorable_nm
        )
        dscr_breach = (
            dscr_result.value_exact < policy.minimum_dscr
            if dscr_result.value_exact is not None
            else not dscr_result.is_favorable_nm
        )
        blocked = leverage_result.status in {
            RatioStatus.MISSING,
            RatioStatus.ERROR,
            RatioStatus.BLOCKED,
        } or dscr_result.status in {
            RatioStatus.MISSING,
            RatioStatus.ERROR,
            RatioStatus.BLOCKED,
        }
        covenant_status: Literal["pass", "breach", "not_applicable", "blocked"] = (
            "blocked"
            if blocked
            else "breach"
            if leverage_breach or dscr_breach
            else "not_applicable"
            if leverage_result.value_exact is None and dscr_result.value_exact is None
            else "pass"
        )
        stress_event = (
            covenant_status in {"breach", "blocked"}
            or cash_shortfall > 0
            or refinancing_need > 0
            or unpaid_debt_service > 0
        )
        if covenant_status in {"breach", "blocked"} and first_breach is None:
            first_breach = year
        if stress_event and first_stress_event is None:
            first_stress_event = year
        if cash_shortfall > 0 and liquidity_exhaustion is None:
            liquidity_exhaustion = year
        years.append(
            ScenarioYearView(
                year=year,
                revenue=_view(revenue),
                adjusted_ebitda=_view(earnings),
                cfads=_view(available),
                ending_debt=_view(_new_money(outstanding, revenue)),
                beginning_debt=_view(_new_money(beginning_debt, revenue)),
                new_facility=_view(_new_money(new_facility, revenue)),
                scheduled_amortization=_view(
                    _new_money(int(scheduled_amortization), revenue)
                ),
                optional_paydown=_view(_new_money(int(optional_paydown), revenue)),
                average_debt=_view(_new_money(int(average_debt), revenue)),
                ending_cash=_view(_new_money(cash, revenue)),
                cash_shortfall=_view(_new_money(int(cash_shortfall), revenue)),
                revolver_draw=_view(_new_money(int(revolver_draw), revenue)),
                revolver_remaining=_view(
                    _new_money(max(0, revolver_available), revenue)
                ),
                refinancing_need=_view(_new_money(int(refinancing_need), revenue)),
                unpaid_debt_service=_view(
                    _new_money(int(unpaid_debt_service), revenue)
                ),
                leverage=(
                    None
                    if leverage_result.value is None
                    else str(leverage_result.value)
                ),
                leverage_status=leverage_result.status.value,
                leverage_reason_code=leverage_result.reason_code.value,
                interest_coverage=(
                    None
                    if coverage_result.value is None
                    else str(coverage_result.value)
                ),
                interest_coverage_status=coverage_result.status.value,
                interest_coverage_reason_code=coverage_result.reason_code.value,
                dscr=None if dscr_result.value is None else str(dscr_result.value),
                dscr_status=dscr_result.status.value,
                dscr_reason_code=dscr_result.reason_code.value,
                covenant_status=covenant_status,
                liquidity_status="shortfall" if cash_shortfall > 0 else "adequate",
                refinancing_status="required" if refinancing_need > 0 else "none",
                debt_service_status=("unpaid" if unpaid_debt_service > 0 else "paid"),
                revolver_status=(
                    "not_applicable"
                    if case.financials.undrawn_revolver.amount_minor <= 0
                    else "exhausted"
                    if revolver_available <= 0
                    else "available"
                ),
            )
        )
    visible_years = years[:3]
    maturity_status: Literal["pass", "breach", "not_applicable", "blocked"] = (
        "not_applicable"
    )
    maturity_reason = "No bullet or partial balloon is present."
    balloon_amount: MoneyValue | None = None
    exit_leverage: str | None = None
    maturity_year: int | None = None
    exit_ebitda_money: MoneyValue | None = None
    refinance_capacity: MoneyValue | None = None
    refinance_headroom: MoneyValue | None = None
    no_refinancing_status: Literal["pass", "breach", "not_applicable", "blocked"] = (
        "not_applicable"
    )
    no_refinancing_reason = "No bullet or partial balloon is present."
    residual_debt: MoneyValue | None = None
    if amortization_kind in {"bullet", "partial"}:
        maturity_year = mechanics.maturity_years
        horizon = mechanics.maturity_years
        maturity_row = years[min(mechanics.maturity_years, len(years)) - 1]
        exit_revenue = (
            Decimal(case.financials.revenue.amount_minor)
            * (ONE + assumptions.revenue_growth) ** horizon
        )
        exit_ebitda = exit_revenue * initial_margin
        exit_ebitda_money = _view(
            _new_money(
                int(exit_ebitda.quantize(Decimal(1), rounding=ROUND_HALF_UP)),
                revenue,
            )
        )
        contractual_balloon = int(
            (Decimal(commitment) * Decimal(mechanics.bullet_percentage)).quantize(
                Decimal(1), rounding=ROUND_HALF_UP
            )
        )
        balloon_minor = min(
            maturity_row.ending_debt.amount_minor,
            max(0, contractual_balloon),
        )
        # The balloon is already included in residual debt immediately before
        # maturity. Exit leverage therefore uses that residual debt once; it
        # must never add the balloon a second time.
        exit_debt = Decimal(maturity_row.ending_debt.amount_minor)
        balloon_amount = _view(_new_money(balloon_minor, revenue))
        residual_debt = maturity_row.ending_debt
        if exit_ebitda <= 0:
            maturity_status = "blocked"
            maturity_reason = "Exit EBITDA is not positive; maturity refinance capacity cannot be tested."
            no_refinancing_status = "blocked"
            no_refinancing_reason = (
                "Exit EBITDA is not positive; no-refinancing capacity is blocked."
            )
        else:
            exit_ratio = exit_debt / exit_ebitda
            exit_leverage = str(exit_ratio.quantize(Decimal("0.0001")))
            maximum_exit_debt = int(
                (exit_ebitda * policy.maximum_leverage).quantize(
                    Decimal(1), rounding=ROUND_HALF_UP
                )
            )
            post_balloon_debt = max(
                0, maturity_row.ending_debt.amount_minor - balloon_minor
            )
            refinance_capacity_minor = max(0, maximum_exit_debt - post_balloon_debt)
            refinance_capacity = _view(_new_money(refinance_capacity_minor, revenue))
            refinance_headroom = _view(
                _new_money(refinance_capacity_minor - balloon_minor, revenue)
            )
            maturity_status = (
                "pass" if refinance_capacity_minor >= balloon_minor else "breach"
            )
            maturity_reason = (
                "Balloon repayment is within exit refinance capacity and policy leverage headroom."
                if maturity_status == "pass"
                else "Balloon repayment exceeds exit refinance capacity; additional support or a policy exception is required."
            )
            no_refinancing_cash = maturity_row.ending_cash.amount_minor - balloon_minor
            no_refinancing_status = (
                "pass"
                if no_refinancing_cash
                >= case.financials.minimum_operating_cash.amount_minor
                else "breach"
            )
            no_refinancing_reason = (
                "Balloon can be repaid from cash while preserving minimum operating cash."
                if no_refinancing_status == "pass"
                else "Severe no-refinancing case exhausts cash below minimum operating cash."
            )
    if (
        debt_reconciliation.residual_maturity_status == "unknown"
        and debt_reconciliation.residual_debt is not None
    ):
        maturity_status = "blocked"
        maturity_reason = (
            "Unscheduled residual debt is visible but its contractual maturity was not supplied;"
            " refinancing capacity cannot be asserted."
        )
    return ScenarioView(
        name=cast(Literal["base", "downside", "severe"], name),
        years=visible_years,
        first_breach_year=first_breach,
        first_stress_event_year=first_stress_event,
        liquidity_exhaustion_year=liquidity_exhaustion,
        maturity_test_status=maturity_status,
        maturity_test_reason=maturity_reason,
        balloon_amount=balloon_amount,
        exit_leverage=exit_leverage,
        maturity_year=maturity_year,
        exit_ebitda=exit_ebitda_money,
        refinance_capacity=refinance_capacity,
        refinance_headroom=refinance_headroom,
        no_refinancing_status=no_refinancing_status,
        no_refinancing_reason=no_refinancing_reason,
        residual_debt=residual_debt,
    )


def _covenants(
    scenarios: list[ScenarioView],
    policy: CreditPolicy,
    case: CaseInput,
    mechanics: ResolvedFacilityMechanics,
    scorecard: ScorecardView,
    borrowing_base: BorrowingBaseView,
) -> list[CovenantView]:
    favorable_reasons = {"nm_no_obligation", "nm_no_cash_interest"}

    def covenant_result(
        value: str | None,
        status: str,
        reason: str,
        threshold: Decimal,
        *,
        minimum: bool,
    ) -> tuple[Literal["pass", "breach", "not_applicable", "blocked"], str]:
        if value is None:
            if reason in favorable_reasons:
                return "not_applicable", "Not meaningful — no applicable obligation"
            if status in {"missing_input", "invalid_denominator", "blocked"}:
                return "blocked", reason
            return "breach", reason
        actual = Decimal(value)
        passed = actual >= threshold if minimum else actual <= threshold
        headroom = actual - threshold if minimum else threshold - actual
        return ("pass" if passed else "breach"), str(
            headroom.quantize(Decimal("0.0001"))
        )

    output: list[CovenantView] = []
    for scenario in scenarios:
        for year in scenario.years:
            leverage_status, leverage_headroom = covenant_result(
                year.leverage,
                year.leverage_status,
                year.leverage_reason_code,
                policy.maximum_leverage,
                minimum=False,
            )
            dscr_status, dscr_headroom = covenant_result(
                year.dscr,
                year.dscr_status,
                year.dscr_reason_code,
                policy.minimum_dscr,
                minimum=True,
            )
            coverage_status, coverage_headroom = covenant_result(
                year.interest_coverage,
                year.interest_coverage_status,
                year.interest_coverage_reason_code,
                policy.minimum_interest_coverage,
                minimum=True,
            )
            output.extend(
                [
                    CovenantView(
                        name="Maximum total leverage",
                        threshold=str(policy.maximum_leverage),
                        actual=year.leverage or year.leverage_reason_code,
                        headroom=leverage_headroom,
                        status=leverage_status,
                        scenario=scenario.name,
                        year=year.year,
                        rationale="Limits balance-sheet leverage and protects refinance capacity.",
                    ),
                    CovenantView(
                        name="Minimum DSCR",
                        threshold=str(policy.minimum_dscr),
                        actual=year.dscr or year.dscr_reason_code,
                        headroom=dscr_headroom,
                        status=dscr_status,
                        scenario=scenario.name,
                        year=year.year,
                        rationale="Requires recurring cash flow to cover interest and scheduled principal.",
                    ),
                ]
            )
            if year.interest_coverage is None or Decimal(
                year.interest_coverage
            ) < policy.minimum_interest_coverage + Decimal("0.75"):
                output.append(
                    CovenantView(
                        name="Minimum interest coverage",
                        threshold=str(policy.minimum_interest_coverage),
                        actual=year.interest_coverage
                        or year.interest_coverage_reason_code,
                        headroom=coverage_headroom,
                        status=coverage_status,
                        scenario=scenario.name,
                        year=year.year,
                        rationale="Adds protection when projected interest headroom is limited.",
                    )
                )
            if (
                year.cash_shortfall.amount_minor > 0
                or year.ending_cash.amount_minor < policy.minimum_liquidity_minor
            ):
                liquidity_headroom = (
                    year.ending_cash.amount_minor - policy.minimum_liquidity_minor
                )
                output.append(
                    CovenantView(
                        name="Minimum unrestricted liquidity",
                        threshold=_currency(
                            MoneyValue(
                                amount_minor=policy.minimum_liquidity_minor,
                                currency=year.ending_cash.currency,
                                minor_unit_exponent=year.ending_cash.minor_unit_exponent,
                            )
                        ),
                        actual=_currency(year.ending_cash),
                        headroom=_currency(
                            MoneyValue(
                                amount_minor=liquidity_headroom,
                                currency=year.ending_cash.currency,
                                minor_unit_exponent=year.ending_cash.minor_unit_exponent,
                            )
                        ),
                        status="pass" if liquidity_headroom >= 0 else "breach",
                        scenario=scenario.name,
                        year=year.year,
                        rationale="Protects operating liquidity when forecast cash headroom is thin.",
                    )
                )

    base_year = scenarios[0].years[0]
    output.append(
        CovenantView(
            name="Quarterly financial reporting",
            threshold="Within 45 days",
            actual="Required",
            headroom="Not applicable",
            status="pass",
            scenario="base",
            year=base_year.year,
            frequency="quarterly",
            rationale="Supports timely monitoring of leverage, coverage, and liquidity.",
            cure="Deliver complete reporting promptly; repeated delay requires lender waiver.",
            covenant_type="reporting",
        )
    )
    weak_grade = scorecard.grade is None or scorecard.grade >= 6
    downside_breach = any(
        scenario.first_breach_year is not None
        for scenario in scenarios
        if scenario.name in {"downside", "severe"}
    )
    if weak_grade or downside_breach:
        output.extend(
            [
                CovenantView(
                    name="Restricted distributions",
                    threshold="No distributions while a default or covenant breach exists",
                    actual="Proposed restriction",
                    headroom="Not applicable",
                    status="pass",
                    scenario="base",
                    year=base_year.year,
                    rationale="Preserves cash when grade or downside headroom is limited.",
                    cure="Equity contribution or lender consent.",
                    covenant_type="incurrence",
                ),
                CovenantView(
                    name="Capital expenditure control",
                    threshold="Annual budget; lender consent above 120%",
                    actual=_currency(case.financials.capex),
                    headroom="20% above approved budget",
                    status="pass",
                    scenario="base",
                    year=base_year.year,
                    rationale="Limits discretionary cash use during a weak or stressed profile.",
                    cure="Lender-approved revised capital plan.",
                    covenant_type="incurrence",
                ),
            ]
        )
    if mechanics.facility_type == "asset_based":
        output.extend(
            [
                CovenantView(
                    name="Borrowing-base availability",
                    threshold="Outstanding amount may not exceed eligible collateral",
                    actual=(
                        _currency(borrowing_base.borrowing_base)
                        if borrowing_base.borrowing_base is not None
                        else "Blocked - borrowing-base inputs required"
                    ),
                    headroom="Calculated at each draw",
                    status="pass",
                    scenario="base",
                    year=base_year.year,
                    frequency="monthly",
                    rationale="Ties asset-based exposure to eligible collateral.",
                ),
                CovenantView(
                    name="Collateral reporting",
                    threshold="Monthly borrowing-base certificate",
                    actual="Required",
                    headroom="Not applicable",
                    status="pass",
                    scenario="base",
                    year=base_year.year,
                    frequency="monthly",
                    rationale="Provides current collateral eligibility and dilution evidence.",
                    covenant_type="reporting",
                ),
            ]
        )
    return output


def _reverse_stress(
    case: CaseInput,
    policy: CreditPolicy,
    mechanics: ResolvedFacilityMechanics,
    base_cfads: Money,
    service: Money,
    earnings: Money,
    debt_reconciliation: DebtReconciliationView,
    capacity: CapacityView,
    revolver_abl: RevolverAblView,
    underwritten_rate: Decimal | None = None,
) -> ReverseStressView:
    del base_cfads, service, earnings
    tolerance = policy.solver_tolerance
    starting_cash = _money(case.financials.unrestricted_cash)

    def run(
        scenario_name: Literal["base", "downside", "severe"],
        updates: dict[str, Decimal],
        loan_minor: Decimal | None = None,
    ) -> ScenarioView:
        assumption = case.scenarios[scenario_name].model_copy(update=updates)
        scenarios = dict(case.scenarios)
        scenarios[scenario_name] = assumption
        trial_case = case.model_copy(update={"scenarios": scenarios})
        trial_capacity = capacity
        if loan_minor is not None:
            trial_capacity = capacity.model_copy(
                update={
                    "recommended": _view(
                        _new_money(
                            max(0, int(loan_minor.quantize(Decimal(1)))),
                            mechanics.commitment.engine(),
                        )
                    )
                }
            )
        return _scenario(
            scenario_name,
            trial_case,
            policy,
            mechanics,
            debt_reconciliation,
            starting_cash,
            trial_capacity,
            revolver_abl,
            underwritten_rate,
        )

    def ratio_headroom(
        value: str | None, threshold: Decimal, minimum: bool
    ) -> Decimal | None:
        if value is None:
            return None
        actual = Decimal(value)
        return actual - threshold if minimum else threshold - actual

    revenue_solver = solve_reverse_stress(
        key="revenue_dscr",
        variable_solved="Revenue decline",
        lower_bound=ZERO,
        upper_bound=Decimal("0.95"),
        tolerance=tolerance,
        max_iterations=policy.solver_max_iterations,
        objective=lambda decline: ratio_headroom(
            run("base", {"revenue_growth": -decline}).years[0].dscr,
            policy.minimum_dscr,
            True,
        ),
        result_multiplier=HUNDRED,
        interpretation="Revenue decline causing first-year DSCR to reach the active minimum; every trial reruns the full forecast.",
    )
    margin_solver = solve_reverse_stress(
        key="margin_leverage",
        variable_solved="EBITDA margin decline",
        lower_bound=ZERO,
        upper_bound=Decimal("0.60"),
        tolerance=tolerance,
        max_iterations=policy.solver_max_iterations,
        objective=lambda decline: ratio_headroom(
            run(
                "base",
                {
                    "ebitda_margin_change": case.scenarios["base"].ebitda_margin_change
                    - decline
                },
            )
            .years[0]
            .leverage,
            policy.maximum_leverage,
            False,
        ),
        result_multiplier=HUNDRED,
        interpretation="EBITDA-margin decline causing first-year leverage to reach the active maximum.",
    )
    rate_solver = solve_reverse_stress(
        key="rate_coverage",
        variable_solved="Interest-rate shock",
        lower_bound=ZERO,
        upper_bound=Decimal("0.25"),
        tolerance=tolerance,
        max_iterations=policy.solver_max_iterations,
        objective=lambda shock: ratio_headroom(
            run("base", {"rate_shock": shock}).years[0].interest_coverage,
            policy.minimum_interest_coverage,
            True,
        ),
        result_multiplier=HUNDRED,
        interpretation="Interest-rate shock causing first-year interest coverage to reach the active minimum.",
    )

    minimum_cash = Decimal(case.financials.minimum_operating_cash.amount_minor)

    def liquidity_headroom(shock: Decimal) -> Decimal:
        result = run(
            "base",
            {
                "working_capital_pct_revenue": min(
                    ONE,
                    case.scenarios["base"].working_capital_pct_revenue + shock,
                )
            },
        )
        return min(
            Decimal(year.ending_cash.amount_minor) - minimum_cash
            for year in result.years
        )

    working_capital_solver = solve_reverse_stress(
        key="working_capital_liquidity",
        variable_solved="Working-capital use as a share of revenue",
        lower_bound=ZERO,
        upper_bound=Decimal("0.75"),
        tolerance=Decimal(1),
        max_iterations=policy.solver_max_iterations,
        objective=liquidity_headroom,
        result_multiplier=HUNDRED,
        interpretation="Incremental working-capital use causing minimum operating liquidity to be exhausted.",
    )

    def policy_loan_headroom(amount: Decimal) -> Decimal | None:
        result = run("downside", {}, amount)
        headrooms: list[Decimal] = []
        for year in result.years:
            leverage = ratio_headroom(year.leverage, policy.maximum_leverage, False)
            dscr = ratio_headroom(year.dscr, policy.minimum_dscr, True)
            if leverage is None or dscr is None:
                return None
            headrooms.extend(
                [
                    leverage,
                    dscr,
                    Decimal(year.ending_cash.amount_minor) - minimum_cash,
                ]
            )
        return min(headrooms)

    maximum_downside_solver = solve_reverse_stress(
        key="maximum_downside_loan",
        variable_solved="Maximum proposed loan passing downside policy",
        lower_bound=ZERO,
        upper_bound=Decimal(policy.maximum_exposure_minor),
        tolerance=Decimal(100),
        max_iterations=policy.solver_max_iterations,
        objective=policy_loan_headroom,
        money_template=mechanics.commitment,
        interpretation="Maximum proposed loan that preserves downside leverage, DSCR, and minimum-liquidity policy.",
    )

    def severe_liquidity_headroom(amount: Decimal) -> Decimal:
        result = run("severe", {}, amount)
        return min(
            Decimal(year.ending_cash.amount_minor) - minimum_cash
            for year in result.years
        )

    maximum_severe_solver = solve_reverse_stress(
        key="maximum_severe_liquidity_loan",
        variable_solved="Maximum proposed loan passing severe liquidity",
        lower_bound=ZERO,
        upper_bound=Decimal(policy.maximum_exposure_minor),
        tolerance=Decimal(100),
        max_iterations=policy.solver_max_iterations,
        objective=severe_liquidity_headroom,
        money_template=mechanics.commitment,
        interpretation="Maximum proposed loan that preserves minimum operating cash in the severe forecast.",
    )
    solvers = [
        revenue_solver,
        margin_solver,
        rate_solver,
        working_capital_solver,
        maximum_downside_solver,
        maximum_severe_solver,
    ]
    return ReverseStressView(
        dscr_minimum_revenue_decline=revenue_solver.result,
        leverage_breach_margin_decline=margin_solver.result,
        maximum_downside_loan=maximum_downside_solver.result_money,
        converged=revenue_solver.converged,
        iterations=revenue_solver.iterations,
        tolerance=str(tolerance),
        residual=revenue_solver.residual or "not_available",
        lower_bound=revenue_solver.lower_bound,
        upper_bound=revenue_solver.upper_bound,
        interpretation=(
            "Revenue decline that causes first-year DSCR to reach the active policy minimum; the full forecast is rerun for every trial."
        ),
        failure_reason=revenue_solver.failure_reason,
        solvers=solvers,
    )


def _policy_checks(
    case: CaseInput,
    policy: CreditPolicy,
    mechanics: ResolvedFacilityMechanics,
    metrics: dict[str, RatioResult],
    capacity: CapacityView,
    scorecard: ScorecardView,
    borrowing_base: BorrowingBaseView,
) -> list[PolicyCheckView]:
    def ratio_check(
        key: str,
        label: str,
        metric: RatioResult,
        threshold: Decimal,
        *,
        minimum: bool,
        hard_stop: bool,
    ) -> PolicyCheckView:
        value = _scoreable(metric, adverse_high=not minimum)
        if value is None:
            status = "hard_stop"
            actual = metric.status.value
        else:
            passed = value >= threshold if minimum else value <= threshold
            status = "pass" if passed else ("hard_stop" if hard_stop else "warning")
            actual = str(value.quantize(Decimal("0.0001")))
        return PolicyCheckView(
            key=key,
            label=label,
            status=cast(
                Literal["pass", "warning", "hard_stop", "not_applicable"], status
            ),
            severity="hard_stop"
            if status == "hard_stop"
            else "warning"
            if status == "warning"
            else "informational",
            actual=actual,
            threshold=str(threshold),
            exception_allowed=not hard_stop,
            remediation=f"Provide valid {label.lower()} evidence or obtain an approved policy exception.",
            required_approval="Credit committee" if status != "pass" else "None",
            decision_impact="Blocks approval"
            if status == "hard_stop"
            else "Conditions approval"
            if status == "warning"
            else "None",
        )

    liquidity_minor = (
        case.financials.unrestricted_cash.amount_minor
        + case.financials.undrawn_revolver.amount_minor
        - case.financials.minimum_operating_cash.amount_minor
    )
    maturity_pass = mechanics.maturity_years * 12 <= policy.maximum_maturity_months
    liquidity_pass = liquidity_minor >= policy.minimum_liquidity_minor
    currency_pass = all(
        value.currency == policy.reporting_currency
        for value in (
            mechanics.commitment,
            case.financials.revenue,
            case.financials.cash_interest,
            case.financials.long_term_debt,
            case.financials.unrestricted_cash,
        )
    )
    reported_ebitda = (
        case.financials.ebit.amount_minor
        + case.financials.depreciation_amortization.amount_minor
    )
    adjustment_amount = abs(
        case.financials.positive_ebitda_adjustments.amount_minor
    ) + abs(case.financials.negative_ebitda_adjustments.amount_minor)
    adjustment_pct = (
        Decimal(adjustment_amount) / Decimal(abs(reported_ebitda))
        if reported_ebitda
        else ONE
    )
    checks = [
        ratio_check(
            "maximum_leverage",
            "Maximum leverage",
            metrics["gross_leverage"],
            policy.maximum_leverage,
            minimum=False,
            hard_stop=False,
        ),
        ratio_check(
            "minimum_dscr",
            "Minimum DSCR",
            metrics["dscr"],
            policy.minimum_dscr,
            minimum=True,
            hard_stop=True,
        ),
        ratio_check(
            "minimum_interest_coverage",
            "Minimum interest coverage",
            metrics["interest_coverage"],
            policy.minimum_interest_coverage,
            minimum=True,
            hard_stop=False,
        ),
    ]
    for key, label, passed, actual, threshold, hard_stop in (
        (
            "maximum_maturity",
            "Maximum maturity",
            maturity_pass,
            f"{mechanics.maturity_years * 12} months",
            f"{policy.maximum_maturity_months} months",
            False,
        ),
        (
            "minimum_liquidity",
            "Minimum liquidity",
            liquidity_pass,
            str(liquidity_minor),
            str(policy.minimum_liquidity_minor),
            True,
        ),
        (
            "reporting_currency",
            "Reporting currency",
            currency_pass,
            mechanics.commitment.currency,
            policy.reporting_currency,
            True,
        ),
        (
            "positive_capacity",
            "Positive supported exposure",
            capacity.recommended.amount_minor > 0,
            str(capacity.recommended.amount_minor),
            "> 0",
            True,
        ),
        (
            "minimum_data_quality",
            "Minimum data confidence",
            scorecard.confidence_score >= policy.minimum_data_confidence_score,
            str(scorecard.confidence_score),
            str(policy.minimum_data_confidence_score),
            True,
        ),
        (
            "maximum_adjustment_magnitude",
            "Maximum EBITDA adjustment magnitude",
            adjustment_pct <= policy.maximum_ebitda_adjustment_pct,
            str(adjustment_pct.quantize(Decimal("0.0001"))),
            str(policy.maximum_ebitda_adjustment_pct),
            False,
        ),
        (
            "grade_eligibility",
            "Maximum eligible risk grade",
            scorecard.grade is not None
            and scorecard.grade <= policy.maximum_eligible_grade,
            "blocked" if scorecard.grade is None else str(scorecard.grade),
            str(policy.maximum_eligible_grade),
            True,
        ),
        (
            "maximum_exposure",
            "Maximum exposure",
            mechanics.commitment.amount_minor <= policy.maximum_exposure_minor,
            str(mechanics.commitment.amount_minor),
            str(policy.maximum_exposure_minor),
            True,
        ),
        (
            "facility_restrictions",
            "Permitted facility type",
            mechanics.facility_type in policy.allowed_facility_types,
            mechanics.facility_type,
            ", ".join(policy.allowed_facility_types),
            True,
        ),
    ):
        status = "pass" if passed else ("hard_stop" if hard_stop else "warning")
        checks.append(
            PolicyCheckView(
                key=key,
                label=label,
                status=cast(
                    Literal["pass", "warning", "hard_stop", "not_applicable"],
                    status,
                ),
                severity="hard_stop"
                if status == "hard_stop"
                else "warning"
                if status == "warning"
                else "informational",
                actual=actual,
                threshold=threshold,
                exception_allowed=not hard_stop,
                remediation=f"Correct {label.lower()} or document an authorized exception.",
                required_approval="Credit committee" if status != "pass" else "None",
                decision_impact="Blocks approval"
                if status == "hard_stop"
                else "Conditions approval"
                if status == "warning"
                else "None",
            )
        )
    if mechanics.security_type == "unsecured":
        checks.append(
            PolicyCheckView(
                key="minimum_collateral_coverage",
                label="Minimum collateral coverage",
                status="not_applicable",
                severity="informational",
                actual="Unsecured facility",
                threshold="Not applicable",
                exception_allowed=False,
                remediation="No remediation required for an unsecured structure.",
                required_approval="None",
                decision_impact="None",
            )
        )
    else:
        collateral_amount = (
            borrowing_base.borrowing_base
            if mechanics.facility_type == "asset_based"
            else case.financials.collateral_capacity
        )
        collateral_coverage = (
            Decimal(collateral_amount.amount_minor)
            / Decimal(mechanics.commitment.amount_minor)
            if collateral_amount is not None and mechanics.commitment.amount_minor > 0
            else ZERO
        )
        passed = collateral_coverage >= policy.minimum_collateral_coverage
        checks.append(
            PolicyCheckView(
                key="minimum_collateral_coverage",
                label="Minimum collateral coverage",
                status="pass" if passed else "warning",
                severity="informational" if passed else "warning",
                actual=str(collateral_coverage.quantize(Decimal("0.0001"))),
                threshold=str(policy.minimum_collateral_coverage),
                exception_allowed=True,
                remediation="Reduce exposure, add eligible collateral, or obtain credit committee approval.",
                required_approval="None" if passed else "Credit committee",
                decision_impact="None" if passed else "Conditions approval",
            )
        )
    return checks


def _decision(
    case: CaseInput,
    mechanics: ResolvedFacilityMechanics,
    scorecard: ScorecardView,
    capacity: CapacityView,
    scenarios: list[ScenarioView],
    policy_checks: list[PolicyCheckView],
) -> DecisionView:
    downside = next(item for item in scenarios if item.name == "downside")
    reduced = capacity.recommended.amount_minor < capacity.requested.amount_minor
    hard_stops = [item for item in policy_checks if item.status == "hard_stop"]
    if scorecard.grade is None:
        outcome = "Decline"
        priority = "critical_inputs_blocked"
    elif capacity.recommended.amount_minor <= 0:
        outcome = "Decline"
        priority = "zero_supported_exposure"
    elif hard_stops:
        outcome = "Decline"
        priority = "policy_hard_stop"
    elif scorecard.grade >= 9:
        outcome = "Decline"
        priority = "risk_grade"
    elif scorecard.grade >= 7 or (
        scorecard.grade >= 6 and downside.first_breach_year == 1
    ):
        outcome = "Refer to credit committee"
        priority = "risk_referral"
    elif reduced:
        outcome = "Reduce requested amount"
        priority = "capacity_reduction"
    elif downside.first_breach_year is not None or scorecard.grade >= 5:
        outcome = "Approve with conditions"
        priority = "conditional_approval"
    else:
        outcome = "Approve"
        priority = "standard_approval"
    rationale = [
        f"Obligor score {scorecard.score or 'blocked'} maps to {('Grade ' + str(scorecard.grade)) if scorecard.grade is not None else 'no final grade'} ({scorecard.grade_label}).",
        f"Recommended exposure is constrained by {', '.join(capacity.binding_constraints)}.",
        "Downside debt-service capacity and covenant headroom determine approval conditions.",
    ]
    conditions = [
        "Maximum total leverage tested quarterly with threshold set from policy and forecast headroom.",
        "Minimum DSCR tested quarterly with cure or waiver subject to lender approval.",
        "Quarterly financial reporting within 45 days.",
    ]
    if downside.first_breach_year is not None:
        conditions.append(
            "Monthly liquidity reporting until downside headroom is restored."
        )
    if mechanics.security_type != "unsecured":
        conditions.append(
            "Perfect and maintain the proposed collateral security interest."
        )
    if outcome == "Decline":
        conditions = []
        monitoring: list[str] = []
        secondary_source = (
            "No collateral-based secondary repayment source is recognized for an unsecured declined facility."
            if mechanics.security_type == "unsecured"
            else "No active-loan conditions; reconsider only after the listed prerequisites are satisfied."
        )
    else:
        monitoring = [
            "Quarterly financial statements",
            "Annual covenant compliance certificate",
            "Prompt notice of material adverse events",
        ]
        secondary_source = (
            "No collateral-based secondary repayment source; refinancing is not assumed."
            if mechanics.security_type == "unsecured"
            else "Eligible borrower collateral subject to documented advance rates; refinancing is not assumed."
        )
    return DecisionView(
        outcome=outcome,  # type: ignore[arg-type]
        rationale=rationale,
        conditions=conditions,
        primary_repayment_source=case.request.primary_repayment_source,
        secondary_repayment_source=secondary_source,
        facility_type=mechanics.facility_type,
        maturity_years=mechanics.maturity_years,
        amortization_years=mechanics.amortization_years or mechanics.maturity_years,
        collateral=(
            "None — unsecured"
            if mechanics.security_type == "unsecured"
            else "Eligible borrower assets subject to documented advance rates"
        ),
        guarantee=case.request.guarantee,
        monitoring=monitoring,
        policy_exceptions=[
            item.label for item in policy_checks if item.status == "warning"
        ],
        decision_priority=priority,
    )


def analyze_case(
    case: CaseInput, *, calculated_at: datetime | None = None
) -> AnalysisResult:
    policy, policy_hash = load_policy()
    resolution = resolve_underwriting_financials(case)
    debt_reconciliation = _reconcile_debt(case, resolution.financials)
    debt_blocked = debt_reconciliation.status == "blocked"
    facility_mechanics = _resolve_facility_mechanics(case)
    mechanics_blocked = facility_mechanics.status == "blocked"
    canonical_blocked = bool(
        (case.financial_spread.periods and resolution.snapshot.blocking_issues)
        or resolution.snapshot.blocked_authority_fields
        or debt_blocked
        or mechanics_blocked
    )
    # Every downstream consumer receives the same resolved financial object. A
    # failed non-empty spread remains blocked; it is never silently replaced by
    # plausible-looking legacy numbers.
    case = case.model_copy(update={"financials": resolution.financials})
    financials = case.financials
    reported_ebitda = ebitda(
        ebit=_money(financials.ebit),
        depreciation_amortization=_money(financials.depreciation_amortization),
    )
    approved_adjustments = [
        item
        for item in case.normalization_adjustments
        if item.approval_status == "approved"
    ]
    positive_adjustments = (
        _new_money(
            sum(
                abs(item.ebitda_impact.amount_minor)
                for item in approved_adjustments
                if item.direction == "positive"
            ),
            reported_ebitda,
        )
        if approved_adjustments
        else _money(financials.positive_ebitda_adjustments)
    )
    negative_adjustments = (
        _new_money(
            sum(
                abs(item.ebitda_impact.amount_minor)
                for item in approved_adjustments
                if item.direction == "negative"
            ),
            reported_ebitda,
        )
        if approved_adjustments
        else _money(financials.negative_ebitda_adjustments)
    )
    earnings = adjusted_ebitda(
        reported_ebitda=reported_ebitda,
        approved_positive_adjustments=positive_adjustments,
        approved_negative_adjustments=negative_adjustments,
    )
    debt = debt_reconciliation.selected_debt.engine()
    available_cash = eligible_cash(
        unrestricted_cash=_money(financials.unrestricted_cash),
        cash_availability_factor=financials.cash_availability_factor,
    )
    net_debt_value = net_debt(gross_debt_value=debt, eligible_cash_value=available_cash)
    cash_available = cfads(
        adjusted_ebitda_value=earnings,
        cash_taxes=_money(financials.cash_taxes),
        maintenance_capex=_money(financials.maintenance_capex),
        increase_in_operating_working_capital=_money(
            financials.working_capital_increase
        ),
        mandatory_pension_contributions=_money(financials.mandatory_pension),
    )
    # Approved itemized adjustments are authoritative. Their explicit CFADS
    # impacts flow into capacity, stress, ratios, and the memo; draft/rejected
    # entries and legacy aggregates do not.
    if approved_adjustments:
        cash_available = _new_money(
            cash_available.amount_minor
            + _signed_adjustment_total(case, "cfads_impact"),
            cash_available,
        )
    service = annual_debt_service(
        cash_interest=debt_reconciliation.selected_interest.engine(),
        scheduled_principal=debt_reconciliation.selected_scheduled_principal.engine(),
    )
    metrics_raw = {
        "gross_leverage": gross_debt_to_ebitda(debt, earnings),
        "adjusted_leverage": adjusted_debt_to_ebitda(debt, earnings),
        "net_leverage": net_debt_to_ebitda(net_debt_value, earnings),
        "interest_coverage": interest_coverage(
            earnings, debt_reconciliation.selected_interest.engine()
        ),
        "dscr": debt_service_coverage(cash_available, service),
        "current_ratio": current_ratio(
            _money(financials.current_assets), _money(financials.current_liabilities)
        ),
        "quick_ratio": quick_ratio(
            cash=_money(financials.unrestricted_cash),
            eligible_marketable_securities=_money(financials.other_current_assets),
            accounts_receivable=_money(financials.accounts_receivable),
            current_liabilities=_money(financials.current_liabilities),
        ),
        "cfo_debt": cfo_to_debt(_money(financials.cfo), debt),
        "ebitda_margin": ebitda_margin(earnings, _money(financials.revenue)),
    }
    blocked_authority = resolution.snapshot.blocked_authority_fields
    if blocked_authority or debt_blocked:
        blocked_reason = (
            "Decision-critical financial source authority is blocked: "
            + ", ".join(blocked_authority)
            + ("; debt reconciliation is blocked" if debt_blocked else "")
        )
        if "scheduled_principal" in blocked_authority or debt_blocked:
            # DSCR is not allowed to appear as a numeric ratio when the debt
            # service input is only an inherited legacy value.
            metrics_raw["dscr"] = _blocked_ratio(
                "ratio.dscr_existing",
                "Existing DSCR",
                blocked_reason,
            )
    financial_spreading = analyze_spreading(case)
    borrowing_base = calculate_borrowing_base(case, policy, facility_mechanics)
    scorecard = _scorecard(
        policy,
        metrics_raw["gross_leverage"],
        metrics_raw["interest_coverage"],
        metrics_raw["dscr"],
        metrics_raw["current_ratio"],
        metrics_raw["cfo_debt"],
        metrics_raw["ebitda_margin"],
        case,
    )
    if canonical_blocked:
        scorecard = scorecard.model_copy(
            update={
                "score": None,
                "grade": None,
                "grade_label": "Blocked — resolve canonical financial periods",
                "confidence": "blocked",
                "confidence_score": 0,
                "confidence_penalties": [
                    *scorecard.confidence_penalties,
                    *resolution.snapshot.blocking_issues,
                    *(
                        [
                            "Debt reconciliation is blocked; downstream debt-service outputs are not decisionable."
                        ]
                        if debt_blocked
                        else []
                    ),
                    *facility_mechanics.blocking_issues,
                ],
                "improvement_actions": [
                    "Resolve the canonical financial-period validation issues before analysis.",
                    *resolution.snapshot.blocking_issues,
                    *(
                        [
                            "Reconcile balance-sheet debt to the instrument schedule before analysis."
                        ]
                        if debt_blocked
                        else []
                    ),
                    *(
                        ["Resolve facility mechanics conflicts before analysis."]
                        if mechanics_blocked
                        else []
                    ),
                ],
            }
        )
    pricing = calculate_pricing(case, policy, scorecard, facility_mechanics)
    pricing_rate = (
        None
        if pricing.indicative_all_in_rate is None
        else Decimal(pricing.indicative_all_in_rate)
    )
    underwritten_rate = _underwritten_rate(case, pricing_rate)
    rate_decision = _rate_decision(case, facility_mechanics, pricing_rate)
    revolver_abl = calculate_revolver_abl(
        facility_mechanics, borrowing_base, rate_decision
    )
    capacity = _capacity(
        case,
        policy,
        facility_mechanics,
        debt_reconciliation,
        earnings,
        cash_available,
        service,
        borrowing_base,
        revolver_abl,
        underwritten_rate,
        pricing.status,
    )
    if blocked_authority or debt_blocked or mechanics_blocked:
        zero_capacity = _view(_new_money(0, facility_mechanics.commitment.engine()))
        capacity = capacity.model_copy(
            update={
                "status": "blocked",
                "recommendation_state": "blocked",
                "underwritten_rate": None,
                "dscr": zero_capacity,
                "recommended": zero_capacity,
                "binding_constraints": [
                    "blocked_facility_mechanics"
                    if mechanics_blocked
                    else "blocked_financial_source"
                ],
            }
        )
    adjustments = summarize_adjustments(case, policy, earnings, debt_reconciliation)
    facility_protection = assess_facility(
        case, policy, facility_mechanics, borrowing_base, capacity.recommended
    )
    scenarios = [
        _scenario(
            name,
            case,
            policy,
            facility_mechanics,
            debt_reconciliation,
            available_cash,
            capacity,
            revolver_abl,
            underwritten_rate,
        )
        for name in ("base", "downside", "severe")
    ]
    if blocked_authority or debt_blocked or mechanics_blocked:
        scenarios = [
            scenario.model_copy(
                update={
                    "years": [
                        year.model_copy(
                            update={
                                "dscr": None,
                                "dscr_status": "blocked",
                                "dscr_reason_code": "blocked_missing_authority",
                                "covenant_status": "blocked",
                                "debt_service_status": "unpaid",
                            }
                        )
                        for year in scenario.years
                    ],
                    "maturity_test_status": "blocked",
                    "maturity_test_reason": (
                        "Blocked until canonical facility mechanics are resolved."
                        if mechanics_blocked
                        else "Blocked until debt-service source authority is reconciled."
                    ),
                }
            )
            for scenario in scenarios
        ]
    covenants = _covenants(
        scenarios, policy, case, facility_mechanics, scorecard, borrowing_base
    )
    policy_checks = _policy_checks(
        case,
        policy,
        facility_mechanics,
        metrics_raw,
        capacity,
        scorecard,
        borrowing_base,
    )
    reverse_stress = _reverse_stress(
        case,
        policy,
        facility_mechanics,
        cash_available,
        service,
        earnings,
        debt_reconciliation,
        capacity,
        revolver_abl,
        underwritten_rate,
    )
    if blocked_authority or debt_blocked or mechanics_blocked:
        reverse_stress = reverse_stress.model_copy(
            update={
                "status": "blocked",
                "dscr_minimum_revenue_decline": None,
                "maximum_downside_loan": None,
                "converged": False,
                "failure_reason": (
                    "Blocked until canonical facility mechanics are resolved."
                    if mechanics_blocked
                    else "Blocked until decision-critical financial source authority is reconciled."
                ),
            }
        )
    decision = _decision(
        case, facility_mechanics, scorecard, capacity, scenarios, policy_checks
    )
    serialized = json.dumps(
        {
            "case": case.model_dump(mode="json"),
            "engine_version": credit_engine.__version__,
            "policy_hash": policy_hash,
            "policy_version": policy.version,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    input_hash = hashlib.sha256(serialized).hexdigest()
    timestamp = calculated_at or datetime.now(UTC)
    downside = next(item for item in scenarios if item.name == "downside")
    base_scenario = next(item for item in scenarios if item.name == "base")
    severe = next(item for item in scenarios if item.name == "severe")
    borrowing_base_text = (
        _currency(borrowing_base.borrowing_base)
        if borrowing_base.borrowing_base is not None
        else borrowing_base.status.replace("_", " ")
    )
    maturity_lines = [
        f"Debt basis: {debt_reconciliation.selected_source}; {debt_reconciliation.coverage_basis_notice}"
    ]
    if debt_reconciliation.selected_source in {
        "instrument_schedule",
        "partial_schedule_with_residual",
    }:
        maturity_lines.extend(
            f"{item.name}: {_currency(item.principal)} outstanding; year {item.maturity_year} maturity; {_currency(item.scheduled_amortization)} scheduled annual amortization."
            for item in case.debt_instruments
        )
    else:
        maturity_lines.append(
            "Instrument-level debt maturity schedule was not supplied; no instrument maturity is inferred."
        )
    if debt_reconciliation.residual_debt is not None:
        maturity_lines.append(
            f"Unscheduled residual debt: {_currency(debt_reconciliation.residual_debt)}; maturity status {debt_reconciliation.residual_maturity_status}."
        )
    memo_sections = {
        "executive_recommendation": [
            f"Recommendation: {decision.outcome}; requested {_currency(capacity.requested)}; supportable {_currency(capacity.recommended)}; internal grade {scorecard.grade or 'blocked'}.",
            *decision.rationale,
        ],
        "borrower_overview": [
            case.borrower.description,
            f"Industry: {case.borrower.industry}. Headquarters: {case.borrower.headquarters}.",
        ],
        "ownership_and_management": [
            "Ownership details were not supplied in the synthetic case.",
            "Management assessment is supported by the qualitative evidence record.",
        ],
        "business_model": [case.borrower.description],
        "industry_risk": [*case.business_risk.risks, *case.business_risk.strengths],
        "loan_request": [
            f"{case.borrower.legal_name} requests {_currency(case.request.amount)}."
        ],
        "facility_structure": [
            f"Resolved mechanics: {facility_mechanics.facility_type}; {facility_mechanics.amortization_type}; status {facility_mechanics.status}; {case.request.rate_type} rate; {facility_mechanics.maturity_years}-year maturity; {facility_mechanics.amortization_years or facility_mechanics.maturity_years}-year amortization.",
            f"Revolver/ABL mechanics: status {revolver_abl.status}; commitment {_currency(revolver_abl.commitment)}; drawn amount {_currency(revolver_abl.drawn_amount)}; borrowing base {_currency_optional(revolver_abl.borrowing_base)}; availability {_currency_optional(revolver_abl.availability)}; commitment fee {revolver_abl.commitment_fee_bps if revolver_abl.commitment_fee_bps is not None else 'N/A'} bps / {_currency_optional(revolver_abl.commitment_fee)}; cash interest {_currency_optional(revolver_abl.cash_interest)} at {revolver_abl.cash_interest_rate or 'N/A'}.",
            revolver_abl.explanation,
            *facility_mechanics.blocking_issues,
        ],
        "loan_purpose": [case.request.purpose],
        "sources_and_uses": [
            f"Proposed lender source: {_currency(case.request.amount)}.",
            f"Stated use: {case.request.purpose}. No additional sources or uses were supplied.",
        ],
        "primary_repayment_source": [decision.primary_repayment_source],
        "secondary_repayment_source": [decision.secondary_repayment_source],
        "historical_financial_performance": [
            f"Revenue {_currency(financials.revenue)}; reported EBITDA {_currency(_view(reported_ebitda))}; adjusted EBITDA {_currency(_view(earnings))}.",
            f"Selected LTM method: {financial_spreading.selected_ltm_method or 'legacy snapshot'}; status {financial_spreading.ltm_status}; snapshot {resolution.snapshot.snapshot_hash[:16]}.",
        ],
        "financial_adjustments": [
            f"Reported EBITDA {_currency(adjustments.reported_ebitda)}; approved adjustment {_currency(adjustments.approved_adjustment)}; adjusted EBITDA {_currency(adjustments.adjusted_ebitda)}.",
            adjustments.warning or "No adjustment-threshold warning.",
        ],
        "capital_structure": [
            f"Gross debt {_currency(_view(debt))}; unrestricted cash {_currency(financials.unrestricted_cash)}; equity {_currency(financials.equity)}.",
            f"Debt reconciliation: {debt_reconciliation.status}; {debt_reconciliation.coverage_basis_notice}",
        ],
        "debt_maturity_schedule": maturity_lines,
        "key_ratios": [
            f"Gross leverage {metrics_raw['gross_leverage'].value or 'N/M'}x; interest coverage {metrics_raw['interest_coverage'].value or 'N/M'}x; DSCR {metrics_raw['dscr'].value or 'N/M'}x."
        ],
        "obligor_grade": [
            f"Score {scorecard.score or 'blocked'}; grade {scorecard.grade or 'blocked'}; confidence {scorecard.confidence_score}/100.",
            "Facility protection is assessed separately and does not alter this obligor grade.",
        ],
        "facility_protection": [
            f"Score {facility_protection.score}; category {facility_protection.category}; expected recovery {facility_protection.expected_recovery_category}; requested/recommended coverage {facility_protection.coverage_requested}x / {facility_protection.coverage_recommended}x.",
            *facility_protection.main_protections,
            *facility_protection.main_structural_weaknesses,
        ],
        "debt_capacity": [
            f"Capacity status {capacity.status}; recommendation state {capacity.recommendation_state}; underwritten rate {capacity.underwritten_rate or 'suppressed'}; requested {_currency(capacity.requested)}; recommended {_currency(capacity.recommended)}.",
            f"Binding constraint(s): {', '.join(capacity.binding_constraints)}.",
        ],
        "base_case": [
            f"First covenant breach year: {base_scenario.first_breach_year or 'none in forecast'}.",
            *(
                [
                    f"Maturity year {base_scenario.maturity_year}; balloon {_currency_optional(base_scenario.balloon_amount)}; exit EBITDA {_currency_optional(base_scenario.exit_ebitda)}; exit leverage {base_scenario.exit_leverage or 'N/M'}x; refinance capacity {_currency_optional(base_scenario.refinance_capacity)}; refinance headroom {_currency_optional(base_scenario.refinance_headroom)}; no-refinancing {base_scenario.no_refinancing_status}.",
                    base_scenario.no_refinancing_reason,
                ]
                if base_scenario.maturity_year is not None
                else []
            ),
            *[
                f"Year {year.year}: revenue {_currency(year.revenue)}; EBITDA {_currency(year.adjusted_ebitda)}; DSCR {year.dscr or 'N/M'}x; ending cash {_currency(year.ending_cash)}."
                for year in base_scenario.years
            ],
        ],
        "downside_case": [
            f"First covenant breach year: {downside.first_breach_year or 'none in forecast'}; liquidity exhaustion year {downside.liquidity_exhaustion_year or 'none in forecast'}.",
            *(
                [
                    f"Maturity year {downside.maturity_year}; balloon {_currency_optional(downside.balloon_amount)}; exit EBITDA {_currency_optional(downside.exit_ebitda)}; exit leverage {downside.exit_leverage or 'N/M'}x; refinance capacity {_currency_optional(downside.refinance_capacity)}; refinance headroom {_currency_optional(downside.refinance_headroom)}; no-refinancing {downside.no_refinancing_status}.",
                    downside.no_refinancing_reason,
                ]
                if downside.maturity_year is not None
                else []
            ),
            *[
                f"Year {year.year}: revenue {_currency(year.revenue)}; EBITDA {_currency(year.adjusted_ebitda)}; DSCR {year.dscr or 'N/M'}x; cash shortfall {_currency(year.cash_shortfall)}."
                for year in downside.years
            ],
        ],
        "severe_case": [
            f"First covenant breach year: {severe.first_breach_year or 'none in forecast'}; liquidity exhaustion year {severe.liquidity_exhaustion_year or 'none in forecast'}.",
            *(
                [
                    f"Maturity year {severe.maturity_year}; balloon {_currency_optional(severe.balloon_amount)}; exit EBITDA {_currency_optional(severe.exit_ebitda)}; exit leverage {severe.exit_leverage or 'N/M'}x; refinance capacity {_currency_optional(severe.refinance_capacity)}; refinance headroom {_currency_optional(severe.refinance_headroom)}; no-refinancing {severe.no_refinancing_status}.",
                    severe.no_refinancing_reason,
                ]
                if severe.maturity_year is not None
                else []
            ),
            *[
                f"Year {year.year}: ending debt {_currency(year.ending_debt)}; ending cash {_currency(year.ending_cash)}; refinancing need {_currency(year.refinancing_need)}; unpaid debt service {_currency(year.unpaid_debt_service)}."
                for year in severe.years
            ],
        ],
        "reverse_stress": [
            *[
                f"{solver.variable_solved}: {solver.result or (_currency(solver.result_money) if solver.result_money else 'no converged result')}; iterations {solver.iterations}; residual {solver.residual or 'not available'}; {solver.failure_reason or solver.interpretation}."
                for solver in reverse_stress.solvers
            ]
        ],
        "collateral_or_borrowing_base": [
            f"Borrowing-base status: {borrowing_base.status}; amount {borrowing_base_text}.",
            borrowing_base.policy_notice,
        ],
        "indicative_pricing": [
            f"Reference base rate {pricing.reference_base_rate}; risk-grade spread {pricing.risk_grade_spread_bps} bps; indicative all-in rate {pricing.indicative_all_in_rate}.",
            pricing.disclaimer,
        ],
        "covenants": [
            *[
                f"{item.name}: {item.actual} versus {item.threshold}; {item.status}; {item.frequency}."
                for item in covenants
            ]
        ],
        "policy_exceptions": decision.policy_exceptions or ["None identified."],
        "conditions_precedent": decision.conditions,
        "monitoring": decision.monitoring,
        "data_limitations": [
            *scorecard.confidence_penalties,
            *financial_spreading.reconciliation_warnings,
            "Synthetic demonstration - not a real data-quality assessment.",
            "Educational and illustrative only; not lending, investment, accounting, or legal advice.",
        ],
        "analyst_sign_off": [
            "Prepared by: ____________________",
            f"Data as of: {case.data_as_of}.",
        ],
        "reviewer_sign_off": [
            "Reviewed by: ____________________",
            f"Model {credit_engine.__version__}; policy {policy.version}; calculation {timestamp.isoformat()}.",
        ],
    }
    return AnalysisResult(
        case=case,
        policy_version=policy.version,
        policy_hash=policy_hash,
        engine_version=credit_engine.__version__,
        input_hash=input_hash,
        calculated_at=timestamp.isoformat(),
        metrics={key: _ratio_view(value) for key, value in metrics_raw.items()},
        financial_spreading=financial_spreading,
        adjustments=adjustments,
        rate_decision=rate_decision,
        debt_reconciliation=debt_reconciliation,
        facility_mechanics=facility_mechanics,
        capacity=capacity,
        facility_protection=facility_protection,
        borrowing_base=borrowing_base,
        revolver_abl=revolver_abl,
        pricing=pricing,
        scorecard=scorecard,
        scenarios=scenarios,
        covenants=covenants,
        policy_checks=policy_checks,
        reverse_stress=reverse_stress,
        decision=decision,
        memo_sections=memo_sections,
        analysis_status="blocked" if scorecard.grade is None else "final",
    )
