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
    gross_debt,
    gross_debt_to_ebitda,
    interest_coverage,
    net_debt,
    net_debt_to_ebitda,
    quick_ratio,
)
from credit_engine.types import RatioResult
from northstar_policy import CreditPolicy, load_policy

from .models import (
    AnalysisResult,
    CapacityConstraintView,
    CapacityView,
    CaseInput,
    CovenantView,
    DecisionView,
    MoneyValue,
    PolicyCheckView,
    RatioView,
    ReverseStressView,
    ScenarioView,
    ScenarioYearView,
    ScorecardView,
    ScoreComponentView,
)

ZERO = Decimal(0)
ONE = Decimal(1)
HUNDRED = Decimal(100)


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


def _currency(value: MoneyValue) -> str:
    amount = Decimal(value.amount_minor) / (Decimal(10) ** value.minor_unit_exponent)
    return f"{value.currency} {amount:,.2f}"


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


def _scoreable(result: RatioResult, *, adverse_high: bool = False) -> Decimal | None:
    """Return an explicit score-band operand without inventing numeric data."""
    if result.is_ok:
        return result.value_exact
    if result.is_favorable_nm:
        return Decimal("999999")
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
    for key in (
        "industry",
        "competitive_position",
        "customer_concentration",
        "diversification",
        "management_policy",
        "governance_event",
    ):
        direct[key] = (getattr(business, key), "Analyst assessment")
    components = []
    for key, (score, band) in direct.items():
        piece = _score_piece(key, score, weight_map[key], band)
        if key in blocked_keys:
            piece = piece.model_copy(
                update={
                    "status": "blocked",
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


def _capacity(
    case: CaseInput,
    policy: CreditPolicy,
    debt: Money,
    earnings: Money,
    cash_available: Money,
    existing_service: Money,
) -> CapacityView:
    request = _money(case.request.amount)
    maximum_debt = Decimal(earnings.amount_minor) * policy.maximum_leverage
    leverage_raw = maximum_debt - Decimal(debt.amount_minor)
    leverage_minor = max(
        0, int(leverage_raw.quantize(Decimal(1), rounding=ROUND_HALF_UP))
    )
    max_service = Decimal(cash_available.amount_minor) / policy.minimum_dscr
    available_service = max(ZERO, max_service - Decimal(existing_service.amount_minor))
    dscr_raw = _annuity_capacity(
        available_service, case.request.annual_rate, case.request.maturity_years
    )
    dscr_minor = max(0, int(dscr_raw.quantize(Decimal(1), rounding=ROUND_HALF_UP)))
    collateral_applicable = case.request.security_type in {"secured", "asset_based"}
    candidates = {
        "requested_amount": request.amount_minor,
        "leverage_capacity": leverage_minor,
        "dscr_capacity": dscr_minor,
        "policy_capacity": policy.policy_capacity_minor,
    }
    if collateral_applicable:
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
            status="valid",
            reason="Calculated from the request, financial inputs, and active policy.",
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
        requested=_view(request),
        leverage=_view(_new_money(leverage_minor, request)),
        dscr=_view(_new_money(dscr_minor, request)),
        collateral=(
            case.financials.collateral_capacity if collateral_applicable else None
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
    debt: Money,
    starting_cash: Money,
    capacity: CapacityView,
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
    existing_debt = debt.amount_minor
    new_debt = capacity.recommended.amount_minor
    outstanding = existing_debt
    cash = starting_cash.amount_minor
    revolver_available = case.financials.undrawn_revolver.amount_minor
    minimum_cash = case.financials.minimum_operating_cash.amount_minor
    effective_new_rate = case.request.annual_rate
    if case.request.rate_type == "floating":
        effective_new_rate = max(
            case.request.rate_floor,
            case.request.annual_rate + assumptions.rate_shock,
        )
    amortization_years = case.request.amortization_years or case.request.maturity_years
    annual_payment = _annual_payment(new_debt, effective_new_rate, amortization_years)
    existing_interest = (
        sum(
            int(Decimal(item.principal.amount_minor) * item.annual_rate)
            for item in case.debt_instruments
        )
        if case.debt_instruments
        else case.financials.cash_interest.amount_minor
    )
    existing_principal = (
        sum(item.scheduled_amortization.amount_minor for item in case.debt_instruments)
        if case.debt_instruments
        else case.financials.scheduled_principal.amount_minor
    )
    years: list[ScenarioYearView] = []
    first_breach: int | None = None
    for year in range(1, 4):
        beginning_debt = outstanding
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
        scheduled_new_principal = max(ZERO, annual_payment - estimated_new_interest)
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
        base_interest = (
            existing_average * existing_rate + new_average * effective_new_rate
        )
        optional_paydown = ZERO
        revolver_draw = ZERO
        for _ in range(8):
            total_interest = (
                base_interest + revolver_draw * effective_new_rate / Decimal(2)
            )
            total_service = total_interest + scheduled_amortization
            pre_financing_cash = Decimal(cash + available.amount_minor) - total_service
            required_draw = max(ZERO, Decimal(minimum_cash) - pre_financing_cash)
            next_draw = min(Decimal(revolver_available), required_draw)
            if abs(next_draw - revolver_draw) <= Decimal(1):
                revolver_draw = next_draw
                break
            revolver_draw = next_draw
        total_interest = base_interest + revolver_draw * effective_new_rate / Decimal(2)
        total_service = total_interest + scheduled_amortization
        pre_financing_cash = Decimal(cash + available.amount_minor) - total_service
        coverage = (
            Decimal(earnings.amount_minor) / total_interest
            if total_interest > 0
            else Decimal("999.9999")
        )
        dscr_value = (
            Decimal(available.amount_minor) / total_service
            if total_service > 0
            else Decimal("999.9999")
        )
        revolver_available -= int(revolver_draw)
        outstanding += int(revolver_draw)
        cash_after_draw = pre_financing_cash + revolver_draw
        cash_shortfall = max(ZERO, Decimal(minimum_cash) - cash_after_draw)
        cash = int(cash_after_draw)
        leverage = (
            Decimal(outstanding) / Decimal(earnings.amount_minor)
            if earnings.amount_minor > 0
            else Decimal("999.9999")
        )
        instrument_maturities = sum(
            item.principal.amount_minor
            for item in case.debt_instruments
            if item.maturity_year == year
        )
        refinancing_need = min(Decimal(outstanding), Decimal(instrument_maturities))
        if year >= case.request.maturity_years and outstanding > 0:
            refinancing_need = Decimal(outstanding)
        breach = leverage > policy.maximum_leverage or dscr_value < policy.minimum_dscr
        breach = breach or cash_shortfall > 0 or refinancing_need > 0
        if breach and first_breach is None:
            first_breach = year
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
                refinancing_need=_view(_new_money(int(refinancing_need), revenue)),
                leverage=str(
                    leverage.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                ),
                interest_coverage=str(
                    coverage.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                ),
                dscr=str(
                    dscr_value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                ),
                covenant_status="breach" if breach else "pass",
            )
        )
    return ScenarioView(name=name, years=years, first_breach_year=first_breach)  # type: ignore[arg-type]


def _covenants(
    scenarios: list[ScenarioView],
    policy: CreditPolicy,
    case: CaseInput,
    scorecard: ScorecardView,
) -> list[CovenantView]:
    output: list[CovenantView] = []
    for scenario in scenarios:
        for year in scenario.years:
            leverage = Decimal(year.leverage)
            dscr = Decimal(year.dscr)
            coverage = Decimal(year.interest_coverage)
            output.extend(
                [
                    CovenantView(
                        name="Maximum total leverage",
                        threshold=str(policy.maximum_leverage),
                        actual=year.leverage,
                        headroom=str(
                            (policy.maximum_leverage - leverage).quantize(
                                Decimal("0.0001")
                            )
                        ),
                        status="pass"
                        if leverage <= policy.maximum_leverage
                        else "breach",
                        scenario=scenario.name,
                        year=year.year,
                        rationale="Limits balance-sheet leverage and protects refinance capacity.",
                    ),
                    CovenantView(
                        name="Minimum DSCR",
                        threshold=str(policy.minimum_dscr),
                        actual=year.dscr,
                        headroom=str(
                            (dscr - policy.minimum_dscr).quantize(Decimal("0.0001"))
                        ),
                        status="pass" if dscr >= policy.minimum_dscr else "breach",
                        scenario=scenario.name,
                        year=year.year,
                        rationale="Requires recurring cash flow to cover interest and scheduled principal.",
                    ),
                ]
            )
            if coverage < policy.minimum_interest_coverage + Decimal("0.75"):
                output.append(
                    CovenantView(
                        name="Minimum interest coverage",
                        threshold=str(policy.minimum_interest_coverage),
                        actual=year.interest_coverage,
                        headroom=str(
                            (coverage - policy.minimum_interest_coverage).quantize(
                                Decimal("0.0001")
                            )
                        ),
                        status="pass"
                        if coverage >= policy.minimum_interest_coverage
                        else "breach",
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
    if case.request.facility_type == "asset_based":
        output.extend(
            [
                CovenantView(
                    name="Borrowing-base availability",
                    threshold="Outstanding amount may not exceed eligible collateral",
                    actual=_currency(case.financials.collateral_capacity),
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
    base_cfads: Money,
    service: Money,
    earnings: Money,
    debt: Money,
    capacity: CapacityView,
) -> ReverseStressView:
    del base_cfads, service, earnings

    def trial(decline: Decimal) -> Decimal:
        base = case.scenarios["base"]
        shocked = base.model_copy(update={"revenue_growth": -decline})
        scenarios = dict(case.scenarios)
        scenarios["base"] = shocked
        trial_case = case.model_copy(update={"scenarios": scenarios})
        result = _scenario(
            "base",
            trial_case,
            policy,
            debt,
            _money(case.financials.unrestricted_cash),
            capacity,
        )
        return Decimal(result.years[0].dscr) - policy.minimum_dscr

    lower = ZERO
    upper = Decimal("0.95")
    tolerance = Decimal("0.0001")
    lower_value = trial(lower)
    upper_value = trial(upper)
    iterations = 0
    converged = False
    if lower_value <= ZERO:
        upper = lower
        residual = lower_value
        converged = True
    elif upper_value > ZERO:
        residual = upper_value
    else:
        residual = upper_value
        for iteration in range(1, 61):
            iterations = iteration
            midpoint = (lower + upper) / Decimal(2)
            residual = trial(midpoint)
            if abs(residual) <= tolerance or upper - lower <= tolerance:
                lower = upper = midpoint
                converged = True
                break
            if residual > ZERO:
                lower = midpoint
            else:
                upper = midpoint
    solved_decline = (lower + upper) / Decimal(2)
    required_earnings = (
        Decimal(debt.amount_minor + capacity.recommended.amount_minor)
        / policy.maximum_leverage
    )
    current_earnings = max(
        Decimal(1),
        Decimal(
            _money(case.financials.ebit).amount_minor
            + _money(case.financials.depreciation_amortization).amount_minor
        ),
    )
    margin_decline = max(ZERO, ONE - required_earnings / current_earnings)
    maximum_downside = min(
        capacity.recommended.amount_minor, capacity.dscr.amount_minor
    )
    return ReverseStressView(
        dscr_minimum_revenue_decline=str(
            (solved_decline * HUNDRED).quantize(Decimal("0.01"))
        ),
        leverage_breach_margin_decline=str(
            (margin_decline * HUNDRED).quantize(Decimal("0.01"))
        ),
        maximum_downside_loan=_view(
            _new_money(maximum_downside, _money(case.request.amount))
        ),
        converged=converged,
        iterations=iterations,
        tolerance=str(tolerance),
        residual=str(residual.quantize(Decimal("0.0001"))),
        lower_bound=str(lower),
        upper_bound=str(upper),
        interpretation=(
            "Revenue decline that causes first-year DSCR to reach the active policy minimum; the full forecast is rerun for every trial."
        ),
    )


def _policy_checks(
    case: CaseInput,
    policy: CreditPolicy,
    metrics: dict[str, RatioResult],
    capacity: CapacityView,
    scorecard: ScorecardView,
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
    maturity_pass = case.request.maturity_years * 12 <= policy.maximum_maturity_months
    liquidity_pass = liquidity_minor >= policy.minimum_liquidity_minor
    currency_pass = all(
        value.currency == policy.reporting_currency
        for value in (
            case.request.amount,
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
            f"{case.request.maturity_years * 12} months",
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
            case.request.amount.currency,
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
            case.request.amount.amount_minor <= policy.maximum_exposure_minor,
            str(case.request.amount.amount_minor),
            str(policy.maximum_exposure_minor),
            True,
        ),
        (
            "facility_restrictions",
            "Permitted facility type",
            case.request.facility_type in policy.allowed_facility_types,
            case.request.facility_type,
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
    if case.request.security_type == "unsecured":
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
        collateral_coverage = (
            Decimal(case.financials.collateral_capacity.amount_minor)
            / Decimal(case.request.amount.amount_minor)
            if case.request.amount.amount_minor > 0
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
    if case.request.security_type != "unsecured":
        conditions.append(
            "Perfect and maintain the proposed collateral security interest."
        )
    return DecisionView(
        outcome=outcome,  # type: ignore[arg-type]
        rationale=rationale,
        conditions=conditions,
        primary_repayment_source=case.request.primary_repayment_source,
        secondary_repayment_source="Eligible collateral and enterprise-value support; refinancing is not assumed.",
        facility_type=case.request.facility_type,
        maturity_years=case.request.maturity_years,
        amortization_years=case.request.amortization_years
        or case.request.maturity_years,
        collateral=(
            "None — unsecured"
            if case.request.security_type == "unsecured"
            else "Eligible borrower assets subject to documented advance rates"
        ),
        guarantee=case.request.guarantee,
        monitoring=[
            "Quarterly financial statements",
            "Annual covenant compliance certificate",
            "Prompt notice of material adverse events",
        ],
        policy_exceptions=[
            item.label for item in policy_checks if item.status == "warning"
        ],
        decision_priority=priority,
    )


def analyze_case(
    case: CaseInput, *, calculated_at: datetime | None = None
) -> AnalysisResult:
    policy, policy_hash = load_policy()
    financials = case.financials
    reported_ebitda = ebitda(
        ebit=_money(financials.ebit),
        depreciation_amortization=_money(financials.depreciation_amortization),
    )
    earnings = adjusted_ebitda(
        reported_ebitda=reported_ebitda,
        approved_positive_adjustments=_money(financials.positive_ebitda_adjustments),
        approved_negative_adjustments=_money(financials.negative_ebitda_adjustments),
    )
    debt = gross_debt(
        short_term_borrowings=_money(financials.short_term_borrowings),
        current_maturities=_money(financials.current_maturities),
        long_term_debt=_money(financials.long_term_debt),
        finance_lease_liabilities=_money(financials.finance_leases),
    )
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
    service = annual_debt_service(
        cash_interest=_money(financials.cash_interest),
        scheduled_principal=_money(financials.scheduled_principal),
    )
    metrics_raw = {
        "gross_leverage": gross_debt_to_ebitda(debt, earnings),
        "adjusted_leverage": adjusted_debt_to_ebitda(debt, earnings),
        "net_leverage": net_debt_to_ebitda(net_debt_value, earnings),
        "interest_coverage": interest_coverage(
            earnings, _money(financials.cash_interest)
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
    capacity = _capacity(case, policy, debt, earnings, cash_available, service)
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
    scenarios = [
        _scenario(name, case, policy, debt, available_cash, capacity)
        for name in ("base", "downside", "severe")
    ]
    covenants = _covenants(scenarios, policy, case, scorecard)
    policy_checks = _policy_checks(case, policy, metrics_raw, capacity, scorecard)
    reverse_stress = _reverse_stress(
        case, policy, cash_available, service, earnings, debt, capacity
    )
    decision = _decision(case, scorecard, capacity, scenarios, policy_checks)
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
    memo_sections = {
        "executive_summary": [
            f"{case.borrower.legal_name} requests {_currency(case.request.amount)} for {case.request.purpose}.",
            f"Recommendation: {decision.outcome}; supportable amount {_currency(capacity.recommended)}; internal grade {scorecard.grade or 'blocked'}.",
        ],
        "borrower_overview": [
            case.borrower.description,
            f"Industry: {case.borrower.industry}. Headquarters: {case.borrower.headquarters}.",
        ],
        "request_and_structure": [
            f"Facility: {decision.facility_type}; maturity {decision.maturity_years} years; amortization {decision.amortization_years} years.",
            f"Collateral: {decision.collateral}. Guarantee: {decision.guarantee}.",
        ],
        "historical_financial_performance": [
            f"Revenue {_currency(financials.revenue)}; reported EBITDA {_currency(_view(reported_ebitda))}; adjusted EBITDA {_currency(_view(earnings))}.",
            f"Gross leverage {metrics_raw['gross_leverage'].value or 'N/M'}x; DSCR {metrics_raw['dscr'].value or 'N/M'}x.",
        ],
        "capacity": [
            f"Requested {_currency(capacity.requested)}; recommended {_currency(capacity.recommended)}.",
            f"Binding constraint(s): {', '.join(capacity.binding_constraints)}.",
        ],
        "scenario_and_reverse_stress": [
            f"Downside first breach year: {downside.first_breach_year or 'none in forecast'}.",
            f"Revenue decline to minimum DSCR: {reverse_stress.dscr_minimum_revenue_decline}% (converged: {reverse_stress.converged}).",
        ],
        "analysis": decision.rationale,
        "strengths": case.business_risk.strengths,
        "risks": case.business_risk.risks,
        "recommendation_and_terms": [decision.outcome, *decision.conditions],
        "policy_exceptions": decision.policy_exceptions or ["None identified."],
        "monitoring": decision.monitoring,
        "limitations": [
            "Synthetic demonstration — not a real data-quality assessment",
            "Educational and illustrative only; not lending, investment, accounting, or legal advice.",
        ],
        "sign_off": [
            "Prepared by: ____________________",
            "Reviewed by: ____________________",
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
        capacity=capacity,
        scorecard=scorecard,
        scenarios=scenarios,
        covenants=covenants,
        policy_checks=policy_checks,
        reverse_stress=reverse_stress,
        decision=decision,
        memo_sections=memo_sections,
        analysis_status="blocked" if scorecard.grade is None else "final",
    )
