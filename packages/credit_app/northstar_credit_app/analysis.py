"""Deterministic underwriting orchestration; all numbers originate here."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, localcontext

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
    CapacityView,
    CaseInput,
    CovenantView,
    DecisionView,
    MoneyValue,
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
    )


def _exact(result: RatioResult) -> Decimal:
    return result.value_exact if result.value_exact is not None else ZERO


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
    leverage_score, leverage_band = policy.score_for("leverage", _exact(leverage))
    coverage_score, coverage_band = policy.score_for("coverage", _exact(coverage))
    dscr_score, dscr_band = policy.score_for("dscr", _exact(dscr))
    combined_coverage = (coverage_score + dscr_score) / Decimal(2)
    weight_map = {item.key: item.weight for item in policy.weights}
    direct: dict[str, tuple[Decimal, str]] = {
        "leverage": (leverage_score, leverage_band),
        "coverage": (combined_coverage, f"{coverage_band}; {dscr_band}"),
        "liquidity": (
            _linear_score(_exact(liquidity), Decimal("0.75"), Decimal("2.0")),
            "Current ratio",
        ),
        "cash_flow": (
            _linear_score(_exact(cfo_debt), Decimal("0.05"), Decimal("0.50")),
            "CFO / Debt",
        ),
        "profitability": (
            _linear_score(_exact(margin), Decimal("0.05"), Decimal("0.25")),
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
    components = [
        _score_piece(key, score, weight_map[key], band)
        for key, (score, band) in direct.items()
    ]
    total = sum((Decimal(item.contribution) for item in components), ZERO)
    grade = policy.grade_for(total)
    return ScorecardView(
        score=str(total.quantize(Decimal("0.01"))),
        grade=grade,
        grade_label=policy.grade_labels[grade],
        components=components,
        confidence="medium",
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
    candidates = {
        "requested_amount": request.amount_minor,
        "leverage_capacity": leverage_minor,
        "dscr_capacity": dscr_minor,
        "collateral_capacity": case.financials.collateral_capacity.amount_minor,
        "policy_capacity": policy.policy_capacity_minor,
    }
    recommended_minor = min(candidates.values())
    binding = [
        key for key, value in candidates.items() if abs(value - recommended_minor) <= 1
    ]
    return CapacityView(
        requested=_view(request),
        leverage=_view(_new_money(leverage_minor, request)),
        dscr=_view(_new_money(dscr_minor, request)),
        collateral=case.financials.collateral_capacity,
        policy=_view(_new_money(policy.policy_capacity_minor, request)),
        recommended=_view(_new_money(recommended_minor, request)),
        binding_constraints=binding,
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
    initial_margin = Decimal(current_ebitda.amount_minor) / Decimal(
        revenue.amount_minor
    )
    outstanding = debt.amount_minor + capacity.recommended.amount_minor
    cash = starting_cash.amount_minor
    annual_payment = _annual_payment(
        capacity.recommended.amount_minor,
        case.request.annual_rate + assumptions.rate_shock,
        case.request.maturity_years,
    )
    existing_interest = case.financials.cash_interest.amount_minor
    existing_principal = case.financials.scheduled_principal.amount_minor
    years: list[ScenarioYearView] = []
    first_breach: int | None = None
    for year in range(1, 4):
        revenue = _scaled(revenue, ONE + assumptions.revenue_growth)
        margin = max(Decimal("0.01"), initial_margin + assumptions.ebitda_margin_change)
        earnings = _scaled(revenue, margin)
        taxes = _scaled(earnings, Decimal("0.12"))
        maintenance_capex = _scaled(revenue, assumptions.maintenance_capex_pct_revenue)
        working_capital = _scaled(revenue, assumptions.working_capital_pct_revenue)
        available = (
            earnings.subtract(taxes)
            .subtract(maintenance_capex)
            .subtract(working_capital)
        )
        new_interest = Decimal(capacity.recommended.amount_minor) * (
            case.request.annual_rate + assumptions.rate_shock
        )
        total_interest = Decimal(existing_interest) + new_interest
        total_service = Decimal(existing_interest + existing_principal) + annual_payment
        leverage = Decimal(outstanding) / Decimal(earnings.amount_minor)
        coverage = Decimal(earnings.amount_minor) / total_interest
        dscr_value = Decimal(available.amount_minor) / total_service
        principal_paid = max(ZERO, annual_payment - new_interest) + Decimal(
            existing_principal
        )
        outstanding = max(0, outstanding - int(principal_paid))
        cash = max(0, cash + available.amount_minor - int(total_service))
        breach = leverage > policy.maximum_leverage or dscr_value < policy.minimum_dscr
        if breach and first_breach is None:
            first_breach = year
        years.append(
            ScenarioYearView(
                year=year,
                revenue=_view(revenue),
                adjusted_ebitda=_view(earnings),
                cfads=_view(available),
                ending_debt=_view(_new_money(outstanding, revenue)),
                ending_cash=_view(_new_money(cash, revenue)),
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
    scenarios: list[ScenarioView], policy: CreditPolicy
) -> list[CovenantView]:
    output: list[CovenantView] = []
    for scenario in scenarios:
        for year in scenario.years:
            leverage = Decimal(year.leverage)
            dscr = Decimal(year.dscr)
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
    required_cfads = Decimal(service.amount_minor) * policy.minimum_dscr
    decline = max(ZERO, ONE - required_cfads / Decimal(base_cfads.amount_minor))
    required_earnings = (
        Decimal(debt.amount_minor + capacity.recommended.amount_minor)
        / policy.maximum_leverage
    )
    margin_decline = max(ZERO, ONE - required_earnings / Decimal(earnings.amount_minor))
    maximum_downside = min(
        capacity.recommended.amount_minor, capacity.dscr.amount_minor
    )
    return ReverseStressView(
        dscr_minimum_revenue_decline=str((decline * HUNDRED).quantize(Decimal("0.01"))),
        leverage_breach_margin_decline=str(
            (margin_decline * HUNDRED).quantize(Decimal("0.01"))
        ),
        maximum_downside_loan=_view(
            _new_money(maximum_downside, _money(case.request.amount))
        ),
        converged=True,
    )


def _decision(
    case: CaseInput,
    scorecard: ScorecardView,
    capacity: CapacityView,
    scenarios: list[ScenarioView],
) -> DecisionView:
    downside = next(item for item in scenarios if item.name == "downside")
    reduced = capacity.recommended.amount_minor < capacity.requested.amount_minor
    if scorecard.grade >= 9:
        outcome = "Decline"
    elif scorecard.grade >= 7 or (
        scorecard.grade >= 6 and downside.first_breach_year == 1
    ):
        outcome = "Refer to credit committee"
    elif reduced:
        outcome = "Reduce requested amount"
    elif downside.first_breach_year is not None or scorecard.grade >= 5:
        outcome = "Approve with conditions"
    else:
        outcome = "Approve"
    rationale = [
        f"Obligor score {scorecard.score} maps to Grade {scorecard.grade} ({scorecard.grade_label}).",
        f"Recommended exposure is constrained by {', '.join(capacity.binding_constraints)}.",
        "Downside debt-service capacity and covenant headroom determine approval conditions.",
    ]
    return DecisionView(
        outcome=outcome,  # type: ignore[arg-type]
        rationale=rationale,
        conditions=[
            "Maximum total leverage of 3.50x, tested quarterly.",
            "Minimum DSCR of 1.25x, tested quarterly.",
            "Quarterly financial reporting within 45 days.",
            "No distributions while a financial covenant breach is continuing.",
        ],
        primary_repayment_source="Operating cash flow generated by the borrower.",
        secondary_repayment_source="Eligible collateral and enterprise-value support; refinancing is not assumed.",
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
    covenants = _covenants(scenarios, policy)
    reverse_stress = _reverse_stress(
        case, policy, cash_available, service, earnings, debt, capacity
    )
    decision = _decision(case, scorecard, capacity, scenarios)
    serialized = case.model_dump_json().encode()
    input_hash = hashlib.sha256(serialized).hexdigest()
    timestamp = calculated_at or datetime.now(UTC)
    memo_sections = {
        "request": [
            f"{case.borrower.legal_name} requests {case.request.amount.amount_minor} minor units for {case.request.purpose}."
        ],
        "analysis": decision.rationale,
        "strengths": case.business_risk.strengths,
        "risks": case.business_risk.risks,
        "recommendation": [decision.outcome, *decision.conditions],
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
        reverse_stress=reverse_stress,
        decision=decision,
        memo_sections=memo_sections,
    )
