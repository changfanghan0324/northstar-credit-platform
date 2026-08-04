"""Deterministic ratio and metric evaluation.

Implements ``docs/methodology.md`` §3 (leverage), §4 (coverage and repayment),
§5 (liquidity), §6 (cash flow), and §7 (profitability and trend) for every metric
whose inputs can be expressed as pure function arguments.

Every result carries both ``value`` (four decimals, ``ROUND_HALF_UP``, for display and
score banding) and ``value_exact`` (unquantized, for covenant pass/breach, headroom,
and reverse-stress convergence), per §1.2 and §1.3.

Pure module: no I/O, no framework, no float.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import ROUND_HALF_UP, Decimal, localcontext

from .money import ENGINE_PRECISION, Money, ensure_same_currency, money_sum
from .types import (
    RATIO_QUANTUM,
    ConfidenceLevel,
    MetricComponent,
    MoneyMetricResult,
    RatioReason,
    RatioResult,
    RatioStatus,
)

__all__ = [
    "adjusted_debt_to_ebitda",
    "capex_to_cfo",
    "capex_to_ebitda",
    "cash_conversion",
    "cash_plus_undrawn_revolver",
    "cash_ratio",
    "cashflow_volatility",
    "cfads_debt_service_coverage",
    "cfo_to_debt",
    "current_ratio",
    "debt_service_coverage",
    "debt_to_capital",
    "debt_to_equity",
    "ebit_interest_coverage",
    "ebit_margin",
    "ebitda_growth",
    "ebitda_margin",
    "fcf_margin",
    "fcf_to_cash_interest",
    "fcf_to_debt",
    "fixed_charge_coverage",
    "gross_debt_to_ebitda",
    "interest_coverage",
    "invested_capital",
    "liabilities_to_assets",
    "liquidity_runway_months",
    "margin_volatility",
    "net_debt_to_ebitda",
    "positive_fcf_years",
    "quick_ratio",
    "return_on_assets",
    "return_on_invested_capital",
    "revenue_growth",
    "revenue_volatility",
    "safe_ratio",
    "secured_debt_to_total",
    "short_term_debt_coverage",
    "sources_uses_surplus",
    "working_capital",
]

#: Minimum comparable annual periods for a volatility statistic (methodology §6.6).
MINIMUM_VOLATILITY_PERIODS = 3


# -- internal helpers ------------------------------------------------------


def _exact_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Divide at an explicit precision so results never depend on ambient context."""
    with localcontext() as ctx:
        ctx.prec = ENGINE_PRECISION
        return numerator / denominator


def _quantize(exact: Decimal) -> Decimal:
    """Four-decimal ``ROUND_HALF_UP`` display and score-banding value (§1.2)."""
    with localcontext() as ctx:
        ctx.prec = ENGINE_PRECISION
        return exact.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _money_operands(
    numerator: Money | None, denominator: Money | None
) -> tuple[Decimal | None, Decimal | None]:
    """Verify a shared currency and return exact minor-unit operands.

    Both operands are expressed in minor units, so the minor-unit scale cancels in the
    quotient and the ratio is exact.
    """
    ensure_same_currency(numerator, denominator)
    exact_numerator = None if numerator is None else numerator.as_minor_decimal()
    exact_denominator = None if denominator is None else denominator.as_minor_decimal()
    return exact_numerator, exact_denominator


def _components(
    *items: tuple[str, Money | Decimal | None],
) -> tuple[MetricComponent, ...]:
    built: list[MetricComponent] = []
    for name, item in items:
        if item is None:
            built.append(MetricComponent(name=name, value=None))
        elif isinstance(item, Money):
            built.append(
                MetricComponent(
                    name=name, value=item.as_minor_decimal(), currency=item.currency
                )
            )
        else:
            built.append(MetricComponent(name=name, value=item))
    return tuple(built)


def _non_ok(
    metric_id: str,
    status: RatioStatus,
    reason: RatioReason,
    *,
    plain_label: str,
    professional_name: str,
    formula_id: str | None,
    components: tuple[MetricComponent, ...],
    interpretation: str | None,
    corrective_action: str | None,
    policy_ref: str | None = None,
) -> RatioResult:
    """Build a non-OK result.

    ``MISSING`` and ``ERROR`` imply blocked confidence (§13). ``NM`` leaves confidence
    unset for the policy layer, because whether an NM state is favorable or adverse is
    policy-controlled (§1.3, §4.1).

    ``formula_id`` and ``policy_ref`` are carried on every non-OK path: methodology §1.3
    requires a non-OK result to retain the same formula and policy references as an OK
    one, so that a blocked or not-meaningful metric remains traceable to the rule that
    produced it.
    """
    confidence = (
        ConfidenceLevel.BLOCKED
        if status in (RatioStatus.MISSING, RatioStatus.ERROR)
        else None
    )
    return RatioResult(
        metric_id=metric_id,
        status=status,
        reason_code=reason,
        value=None,
        value_exact=None,
        plain_label=plain_label,
        professional_name=professional_name,
        formula_id=formula_id,
        policy_ref=policy_ref,
        components=components,
        confidence=confidence,
        interpretation=interpretation,
        corrective_action=corrective_action,
    )


def safe_ratio(
    metric_id: str,
    numerator: Decimal | None,
    denominator: Decimal | None,
    *,
    plain_label: str = "",
    professional_name: str = "",
    formula_id: str | None = None,
    policy_ref: str | None = None,
    components: tuple[MetricComponent, ...] = (),
    require_positive_denominator: bool = False,
    zero_denominator_reason: RatioReason = RatioReason.NM_UNDEFINED,
    nonpositive_denominator_reason: RatioReason = RatioReason.NM_NEGATIVE_BASE,
    offset: Decimal | None = None,
    interpretation: str | None = None,
    zero_denominator_interpretation: str | None = None,
    corrective_action: str | None = None,
) -> RatioResult:
    """Evaluate ``numerator / denominator`` under the §1.3 status and reason contract.

    Guard order:

    1. a missing operand is ``MISSING`` / ``missing_input`` -- never ``nm``;
    2. when ``require_positive_denominator`` is set, a denominator ``<= 0`` returns
       ``nonpositive_denominator_reason`` (adverse), covering the §3.1 rule that an
       adjusted EBITDA of zero or below is ``nm_negative_base`` rather than zero or
       infinity;
    3. a zero denominator returns ``zero_denominator_reason``, which callers set to the
       favorable or adverse code their metric requires. It defaults to ``nm_undefined``,
       which is the structural ``0/0`` case of §1.3.

    ``interpretation`` describes a successful result. ``zero_denominator_interpretation``
    describes the not-meaningful branch; the two are separate so an NM sentence can never
    be attached to a calculated value.

    ``offset`` is a constant added to the quotient. It exists for the growth metrics of
    §7.1, which are ``current / prior - 1``, so that ``value_exact`` is the growth rate
    itself rather than the underlying quotient.
    """
    if numerator is None or denominator is None:
        missing = "numerator" if numerator is None else "denominator"
        return _non_ok(
            metric_id,
            RatioStatus.MISSING,
            RatioReason.MISSING_INPUT,
            plain_label=plain_label,
            professional_name=professional_name,
            formula_id=formula_id,
            components=components,
            interpretation=f"Cannot be calculated: the {missing} is not available.",
            corrective_action=f"Supply the {missing} for this period.",
            policy_ref=policy_ref,
        )

    if require_positive_denominator and denominator <= Decimal(0):
        return _non_ok(
            metric_id,
            RatioStatus.NM,
            nonpositive_denominator_reason,
            plain_label=plain_label,
            professional_name=professional_name,
            formula_id=formula_id,
            components=components,
            interpretation=(
                "Not meaningful: the earnings or cash-flow base is zero or negative, "
                "which is an adverse result rather than a favorable one."
            ),
            corrective_action=corrective_action,
            policy_ref=policy_ref,
        )

    if denominator == Decimal(0):
        return _non_ok(
            metric_id,
            RatioStatus.NM,
            zero_denominator_reason,
            plain_label=plain_label,
            professional_name=professional_name,
            formula_id=formula_id,
            components=components,
            interpretation=zero_denominator_interpretation
            or "Not meaningful: the denominator is zero for this period.",
            corrective_action=corrective_action,
            policy_ref=policy_ref,
        )

    exact = _exact_divide(numerator, denominator)
    if offset is not None:
        with localcontext() as ctx:
            ctx.prec = ENGINE_PRECISION
            exact = exact + offset

    return RatioResult(
        metric_id=metric_id,
        status=RatioStatus.OK,
        reason_code=RatioReason.OK,
        value=_quantize(exact),
        value_exact=exact,
        plain_label=plain_label,
        professional_name=professional_name,
        formula_id=formula_id,
        policy_ref=policy_ref,
        components=components,
        interpretation=interpretation,
    )


def _money_ratio(
    metric_id: str,
    numerator: Money | None,
    denominator: Money | None,
    *,
    numerator_name: str,
    denominator_name: str,
    **options: object,
) -> RatioResult:
    exact_numerator, exact_denominator = _money_operands(numerator, denominator)
    components = _components(
        (numerator_name, numerator), (denominator_name, denominator)
    )
    return safe_ratio(
        metric_id,
        exact_numerator,
        exact_denominator,
        components=components,
        **options,  # type: ignore[arg-type]
    )


# -- §3 leverage -----------------------------------------------------------


def gross_debt_to_ebitda(
    gross_debt_value: Money | None, adjusted_ebitda_value: Money | None
) -> RatioResult:
    """Methodology §3.1. Adjusted EBITDA ``<= 0`` is adverse NM, not zero or infinity."""
    return _money_ratio(
        "ratio.gross_debt_ebitda",
        gross_debt_value,
        adjusted_ebitda_value,
        numerator_name="gross_debt",
        denominator_name="adjusted_ebitda",
        plain_label="Debt compared with earnings",
        professional_name="Gross Debt / Adjusted EBITDA",
        formula_id="gross_debt_to_ebitda",
        require_positive_denominator=True,
    )


def adjusted_debt_to_ebitda(
    adjusted_debt_value: Money | None, adjusted_ebitda_value: Money | None
) -> RatioResult:
    """Methodology §3.2."""
    return _money_ratio(
        "ratio.adjusted_debt_ebitda",
        adjusted_debt_value,
        adjusted_ebitda_value,
        numerator_name="adjusted_debt",
        denominator_name="adjusted_ebitda",
        plain_label="Debt including leases compared with earnings",
        professional_name="Adjusted Debt / Adjusted EBITDA",
        formula_id="adjusted_debt_to_ebitda",
        require_positive_denominator=True,
    )


def net_debt_to_ebitda(
    net_debt_value: Money | None, adjusted_ebitda_value: Money | None
) -> RatioResult:
    """Methodology §3.3.

    Net cash produces a valid negative ratio when EBITDA is positive; that is a real
    result, not a not-meaningful state.
    """
    return _money_ratio(
        "ratio.net_debt_ebitda",
        net_debt_value,
        adjusted_ebitda_value,
        numerator_name="net_debt",
        denominator_name="adjusted_ebitda",
        plain_label="Debt after cash compared with earnings",
        professional_name="Net Debt / Adjusted EBITDA",
        formula_id="net_debt_to_ebitda",
        require_positive_denominator=True,
    )


def debt_to_capital(
    gross_debt_value: Money | None, equity: Money | None
) -> RatioResult:
    """Methodology §3.4: ``Gross Debt / (Gross Debt + Equity)``.

    Total capital of zero or below is reported as adverse rather than favorable, for
    the same reason §3.5 gives for nonpositive equity.
    """
    ensure_same_currency(gross_debt_value, equity)
    capital = (
        None
        if gross_debt_value is None or equity is None
        else gross_debt_value.add(equity)
    )
    exact_numerator, exact_denominator = _money_operands(gross_debt_value, capital)
    return safe_ratio(
        "ratio.debt_capital",
        exact_numerator,
        exact_denominator,
        components=_components(
            ("gross_debt", gross_debt_value),
            ("equity", equity),
            ("total_capital", capital),
        ),
        plain_label="Share of funding provided by debt",
        professional_name="Debt / Capital",
        formula_id="debt_to_capital",
        require_positive_denominator=True,
    )


def debt_to_equity(gross_debt_value: Money | None, equity: Money | None) -> RatioResult:
    """Methodology §3.5. Nonpositive equity is adverse and never favorable."""
    return _money_ratio(
        "ratio.debt_equity",
        gross_debt_value,
        equity,
        numerator_name="gross_debt",
        denominator_name="equity",
        plain_label="Debt compared with owners' capital",
        professional_name="Debt / Equity",
        formula_id="debt_to_equity",
        require_positive_denominator=True,
        corrective_action=(
            "Equity is zero or negative. Review accumulated losses, distributions, and "
            "any quasi-equity treatment before relying on leverage measures."
        ),
    )


def liabilities_to_assets(
    total_liabilities: Money | None, total_assets: Money | None
) -> RatioResult:
    """Methodology §3.6."""
    return _money_ratio(
        "ratio.liabilities_assets",
        total_liabilities,
        total_assets,
        numerator_name="total_liabilities",
        denominator_name="total_assets",
        plain_label="Share of assets funded by liabilities",
        professional_name="Liabilities / Assets",
        formula_id="liabilities_to_assets",
        require_positive_denominator=True,
    )


def secured_debt_to_total(
    secured_debt: Money | None, gross_debt_value: Money | None
) -> RatioResult:
    """Methodology §3.7. Zero gross debt with complete inputs is favorable NM."""
    return _money_ratio(
        "ratio.secured_debt_total",
        secured_debt,
        gross_debt_value,
        numerator_name="secured_debt",
        denominator_name="gross_debt",
        plain_label="Share of debt backed by collateral",
        professional_name="Secured Debt / Total Debt",
        formula_id="secured_debt_to_total",
        zero_denominator_reason=RatioReason.NM_NO_OBLIGATION,
        zero_denominator_interpretation="Not meaningful: the borrower has no debt outstanding.",
    )


# -- §4 coverage and repayment --------------------------------------------


def _interest_style_coverage(
    metric_id: str,
    numerator: Money | None,
    cash_interest: Money | None,
    has_deferred_or_capitalized_interest: bool,
    *,
    numerator_name: str,
    plain_label: str,
    professional_name: str,
    formula_id: str,
) -> RatioResult:
    """Shared zero-cash-interest guard for the §4.1, §4.2, and §4.6 coverage metrics.

    Zero cash interest is favorable only when nothing is PIK, capitalized, or deferred.
    Otherwise the absence of a cash burden is a deferred obligation and is adverse --
    treating it as favorable is the classic zero-interest false positive.

    A missing operand is resolved first. Methodology §1.3 requires missing inputs to take
    precedence over every zero-denominator special case: a borrower with no cash interest
    and no reported earnings has unknown coverage, not favorable coverage.
    """
    exact_numerator, exact_denominator = _money_operands(numerator, cash_interest)
    components = _components(
        (numerator_name, numerator), ("cash_interest", cash_interest)
    )
    if exact_numerator is None or exact_denominator is None:
        return safe_ratio(
            metric_id,
            exact_numerator,
            exact_denominator,
            components=components,
            plain_label=plain_label,
            professional_name=professional_name,
            formula_id=formula_id,
        )
    if exact_denominator == Decimal(0):
        if has_deferred_or_capitalized_interest:
            return _non_ok(
                metric_id,
                RatioStatus.NM,
                RatioReason.NM_DEFERRED_OBLIGATION,
                plain_label=plain_label,
                professional_name=professional_name,
                formula_id=formula_id,
                components=components,
                interpretation=(
                    "Not meaningful and adverse: there is no cash interest because "
                    "interest is deferred or capitalized, so the obligation is growing."
                ),
                corrective_action=(
                    "Review accrued and capitalized interest and test coverage against "
                    "the cash interest that becomes payable."
                ),
            )
        return _non_ok(
            metric_id,
            RatioStatus.NM,
            RatioReason.NM_NO_CASH_INTEREST,
            plain_label=plain_label,
            professional_name=professional_name,
            formula_id=formula_id,
            components=components,
            interpretation="Not meaningful: the borrower pays no cash interest.",
            corrective_action=None,
        )
    return safe_ratio(
        metric_id,
        exact_numerator,
        exact_denominator,
        components=components,
        plain_label=plain_label,
        professional_name=professional_name,
        formula_id=formula_id,
    )


def interest_coverage(
    adjusted_ebitda_value: Money | None,
    cash_interest: Money | None,
    has_deferred_or_capitalized_interest: bool = False,
) -> RatioResult:
    """Methodology §4.1: ``Adjusted EBITDA / Cash Interest``."""
    return _interest_style_coverage(
        "ratio.ebitda_interest",
        adjusted_ebitda_value,
        cash_interest,
        has_deferred_or_capitalized_interest,
        numerator_name="adjusted_ebitda",
        plain_label="Ability to cover interest",
        professional_name="Adjusted EBITDA / Cash Interest",
        formula_id="interest_coverage",
    )


def ebit_interest_coverage(
    adjusted_ebit_value: Money | None,
    cash_interest: Money | None,
    has_deferred_or_capitalized_interest: bool = False,
) -> RatioResult:
    """Methodology §4.2, with the same zero-interest guard as §4.1."""
    return _interest_style_coverage(
        "ratio.ebit_interest",
        adjusted_ebit_value,
        cash_interest,
        has_deferred_or_capitalized_interest,
        numerator_name="adjusted_ebit",
        plain_label="Ability to cover interest after depreciation",
        professional_name="Adjusted EBIT / Cash Interest",
        formula_id="ebit_interest_coverage",
    )


def debt_service_coverage(
    cfads_value: Money | None,
    debt_service: Money | None,
    is_proforma: bool = False,
    proposed_principal: Money | None = None,
) -> RatioResult:
    """Methodology §4.3 and §1.3.

    Existing and pro forma DSCR are distinct metrics with distinct zero-service
    semantics. Zero *existing* debt service is favorable NM: the borrower owes nothing.
    Zero *pro forma* debt service while a positive facility is being proposed is
    structurally impossible, so it is an error that blocks decisioning rather than a
    not-meaningful state that quietly passes through.

    ``proposed_principal`` participates in the currency guard even though it is not an
    operand of the quotient: a facility denominated in another currency is a multi-
    currency case, which the MVP does not support (§1.1), and it must be rejected before
    any branch rather than silently ignored.

    A missing operand is resolved before either zero-service branch, per §1.3.
    """
    metric_id = "ratio.dscr_proforma" if is_proforma else "ratio.dscr_existing"
    professional_name = "Pro forma DSCR" if is_proforma else "Existing DSCR"
    ensure_same_currency(cfads_value, debt_service, proposed_principal)
    exact_numerator, exact_denominator = _money_operands(cfads_value, debt_service)
    components = _components(
        ("cfads", cfads_value),
        ("annual_debt_service", debt_service),
        ("proposed_principal", proposed_principal),
    )

    if exact_numerator is None or exact_denominator is None:
        return safe_ratio(
            metric_id,
            exact_numerator,
            exact_denominator,
            components=components,
            plain_label="Ability to cover annual debt payments",
            professional_name=professional_name,
            formula_id="debt_service_coverage",
        )

    if exact_denominator == Decimal(0):
        if is_proforma and proposed_principal is None:
            return _non_ok(
                metric_id,
                RatioStatus.MISSING,
                RatioReason.MISSING_INPUT,
                plain_label="Ability to cover annual debt payments",
                professional_name=professional_name,
                formula_id="debt_service_coverage",
                components=components,
                interpretation=(
                    "Missing input: proposed principal is required to interpret zero "
                    "pro forma debt service."
                ),
                corrective_action=(
                    "Supply the proposed principal and the facility's interest and "
                    "scheduled principal."
                ),
            )
        if (
            is_proforma
            and proposed_principal is not None
            and proposed_principal.is_positive()
        ):
            return _non_ok(
                metric_id,
                RatioStatus.ERROR,
                RatioReason.ERROR_INVALID_INPUT,
                plain_label="Ability to cover annual debt payments",
                professional_name=professional_name,
                formula_id="debt_service_coverage",
                components=components,
                interpretation=(
                    "Invalid: a positive proposed facility cannot produce zero pro forma "
                    "debt service."
                ),
                corrective_action=(
                    "Supply the proposed facility's interest and scheduled principal, or "
                    "correct the requested amount."
                ),
            )
        return _non_ok(
            metric_id,
            RatioStatus.NM,
            RatioReason.NM_NO_OBLIGATION,
            plain_label="Ability to cover annual debt payments",
            professional_name=professional_name,
            formula_id="debt_service_coverage",
            components=components,
            interpretation="Not meaningful: there is no scheduled debt service.",
            corrective_action=None,
        )

    return safe_ratio(
        metric_id,
        exact_numerator,
        exact_denominator,
        components=components,
        plain_label="Ability to cover annual debt payments",
        professional_name=professional_name,
        formula_id="debt_service_coverage",
    )


def cfads_debt_service_coverage(
    cfads_value: Money | None,
    debt_service: Money | None,
    is_proforma: bool = False,
    proposed_principal: Money | None = None,
) -> RatioResult:
    """Methodology §4.5. Numerically identical to DSCR; retained as a named output."""
    result = debt_service_coverage(
        cfads_value, debt_service, is_proforma, proposed_principal
    )
    return RatioResult(
        metric_id="ratio.cfads_debt_service",
        status=result.status,
        reason_code=result.reason_code,
        value=result.value,
        value_exact=result.value_exact,
        plain_label="Cash available before debt payments, compared with those payments",
        professional_name="CFADS / Debt Service",
        formula_id="cfads_debt_service_coverage",
        policy_ref=result.policy_ref,
        components=result.components,
        confidence=result.confidence,
        confidence_factors=result.confidence_factors,
        interpretation=result.interpretation,
        corrective_action=result.corrective_action,
    )


def fixed_charge_coverage(
    *,
    ebitdar_value: Money | None,
    cash_taxes: Money | None,
    maintenance_capex: Money | None,
    increase_in_operating_working_capital: Money | None,
    cash_interest: Money | None,
    scheduled_principal: Money | None,
    contractual_rent: Money | None,
) -> RatioResult:
    """Methodology §4.4.

    ``(EBITDAR - cash taxes - maintenance capex - increase in OWC) /
    (cash interest + scheduled principal + contractual rent)``.

    The numerator deliberately omits mandatory pension contributions and other
    mandatory operating cash uses, so it is *not* ``CFADS + rent``. That follows the
    master prompt's literal §19 definition; the two numerators must not be harmonized
    without a methodology change.
    """
    inputs = (
        ebitdar_value,
        cash_taxes,
        maintenance_capex,
        increase_in_operating_working_capital,
        cash_interest,
        scheduled_principal,
        contractual_rent,
    )
    ensure_same_currency(*inputs)
    components = _components(
        ("ebitdar", ebitdar_value),
        ("cash_taxes", cash_taxes),
        ("maintenance_capex", maintenance_capex),
        (
            "increase_in_operating_working_capital",
            increase_in_operating_working_capital,
        ),
        ("cash_interest", cash_interest),
        ("scheduled_principal", scheduled_principal),
        ("contractual_rent", contractual_rent),
    )
    if any(item is None for item in inputs):
        return _non_ok(
            "ratio.fixed_charge_coverage",
            RatioStatus.MISSING,
            RatioReason.MISSING_INPUT,
            plain_label="Ability to cover interest, principal, and rent",
            professional_name="Fixed-Charge Coverage",
            formula_id="fixed_charge_coverage",
            components=components,
            interpretation="Cannot be calculated: a fixed-charge input is not available.",
            corrective_action="Supply every fixed-charge input for this period.",
        )

    assert ebitdar_value is not None
    assert cash_taxes is not None
    assert maintenance_capex is not None
    assert increase_in_operating_working_capital is not None
    assert cash_interest is not None
    assert scheduled_principal is not None
    assert contractual_rent is not None

    numerator = (
        ebitdar_value.subtract(cash_taxes)
        .subtract(maintenance_capex)
        .subtract(increase_in_operating_working_capital)
    )
    denominator = cash_interest.add(scheduled_principal).add(contractual_rent)
    return safe_ratio(
        "ratio.fixed_charge_coverage",
        numerator.as_minor_decimal(),
        denominator.as_minor_decimal(),
        components=components,
        plain_label="Ability to cover interest, principal, and rent",
        professional_name="Fixed-Charge Coverage",
        formula_id="fixed_charge_coverage",
        zero_denominator_reason=RatioReason.NM_NO_OBLIGATION,
        zero_denominator_interpretation="Not meaningful: there are no fixed charges for this period.",
    )


def fcf_to_cash_interest(
    free_cash_flow_value: Money | None,
    cash_interest: Money | None,
    has_deferred_or_capitalized_interest: bool = False,
) -> RatioResult:
    """Methodology §4.6, with the §4.1 zero-interest guard."""
    return _interest_style_coverage(
        "ratio.fcf_cash_interest",
        free_cash_flow_value,
        cash_interest,
        has_deferred_or_capitalized_interest,
        numerator_name="free_cash_flow",
        plain_label="Spare cash compared with interest cost",
        professional_name="Free Cash Flow / Cash Interest",
        formula_id="fcf_to_cash_interest",
    )


# -- §5 liquidity ----------------------------------------------------------


def current_ratio(
    current_assets: Money | None, current_liabilities: Money | None
) -> RatioResult:
    """Methodology §5.1."""
    return _money_ratio(
        "ratio.current",
        current_assets,
        current_liabilities,
        numerator_name="current_assets",
        denominator_name="current_liabilities",
        plain_label="Short-term assets compared with short-term bills",
        professional_name="Current Ratio",
        formula_id="current_ratio",
        zero_denominator_reason=RatioReason.NM_NO_OBLIGATION,
        zero_denominator_interpretation="Not meaningful: there are no current liabilities.",
    )


def quick_ratio(
    *,
    cash: Money | None,
    eligible_marketable_securities: Money | None,
    accounts_receivable: Money | None,
    current_liabilities: Money | None,
) -> RatioResult:
    """Methodology §5.2.

    Uses unrestricted cash as reported. Unlike §5.3, no availability factor is applied,
    because §5.2 defines the numerator on cash rather than eligible cash.
    """
    parts = (cash, eligible_marketable_securities, accounts_receivable)
    ensure_same_currency(*parts, current_liabilities)
    numerator = None if any(part is None for part in parts) else money_sum(list(parts))
    return _money_ratio(
        "ratio.quick",
        numerator,
        current_liabilities,
        numerator_name="quick_assets",
        denominator_name="current_liabilities",
        plain_label="Readily available assets compared with short-term bills",
        professional_name="Quick Ratio",
        formula_id="quick_ratio",
        zero_denominator_reason=RatioReason.NM_NO_OBLIGATION,
        zero_denominator_interpretation="Not meaningful: there are no current liabilities.",
    )


def cash_ratio(
    eligible_cash_value: Money | None, current_liabilities: Money | None
) -> RatioResult:
    """Methodology §5.3."""
    return _money_ratio(
        "ratio.cash",
        eligible_cash_value,
        current_liabilities,
        numerator_name="eligible_cash",
        denominator_name="current_liabilities",
        plain_label="Cash compared with short-term bills",
        professional_name="Cash Ratio",
        formula_id="cash_ratio",
        zero_denominator_reason=RatioReason.NM_NO_OBLIGATION,
        zero_denominator_interpretation="Not meaningful: there are no current liabilities.",
    )


def working_capital(
    current_assets: Money | None, current_liabilities: Money | None
) -> MoneyMetricResult:
    """Methodology §5.4. A monetary metric, not a ratio."""
    components = _components(
        ("current_assets", current_assets), ("current_liabilities", current_liabilities)
    )
    if current_assets is None or current_liabilities is None:
        return MoneyMetricResult(
            metric_id="metric.working_capital",
            status=RatioStatus.MISSING,
            reason_code=RatioReason.MISSING_INPUT,
            plain_label="Short-term cushion",
            professional_name="Working Capital",
            formula_id="working_capital",
            components=components,
            confidence=ConfidenceLevel.BLOCKED,
            corrective_action="Supply current assets and current liabilities.",
        )
    ensure_same_currency(current_assets, current_liabilities)
    return MoneyMetricResult(
        metric_id="metric.working_capital",
        status=RatioStatus.OK,
        reason_code=RatioReason.OK,
        value=current_assets.subtract(current_liabilities),
        plain_label="Short-term cushion",
        professional_name="Working Capital",
        formula_id="working_capital",
        components=components,
    )


def short_term_debt_coverage(
    *,
    eligible_cash_value: Money | None,
    undrawn_committed_revolver: Money | None,
    short_term_borrowings: Money | None,
    current_maturities: Money | None,
) -> RatioResult:
    """Methodology §5.5."""
    sources = (eligible_cash_value, undrawn_committed_revolver)
    uses = (short_term_borrowings, current_maturities)
    ensure_same_currency(*sources, *uses)
    numerator = (
        None if any(part is None for part in sources) else money_sum(list(sources))
    )
    denominator = None if any(part is None for part in uses) else money_sum(list(uses))
    return _money_ratio(
        "ratio.short_term_debt_coverage",
        numerator,
        denominator,
        numerator_name="committed_liquidity",
        denominator_name="short_term_debt",
        plain_label="Available liquidity compared with debt due within a year",
        professional_name="Short-Term Debt Coverage",
        formula_id="short_term_debt_coverage",
        zero_denominator_reason=RatioReason.NM_NO_OBLIGATION,
        zero_denominator_interpretation="Not meaningful: no debt falls due within the year.",
    )


def liquidity_runway_months(
    *,
    eligible_cash_value: Money | None,
    undrawn_committed_revolver: Money | None,
    minimum_operating_cash: Money | None,
    monthly_stressed_cash_burn: Money | None,
) -> RatioResult:
    """Methodology §5.6.

    A zero burn means the runway does not expire, and a negative burn means the
    business generates cash under stress. Both are reported as favorable NM rather
    than as an infinite or negative month count, under the liquidity-specific reason
    code ``nm_no_cash_burn`` -- deliberately not ``nm_no_obligation``, which is about
    debt and liability obligations and must not attract the same policy treatment.
    """
    inputs = (
        eligible_cash_value,
        undrawn_committed_revolver,
        minimum_operating_cash,
        monthly_stressed_cash_burn,
    )
    ensure_same_currency(*inputs)
    components = _components(
        ("eligible_cash", eligible_cash_value),
        ("undrawn_committed_revolver", undrawn_committed_revolver),
        ("minimum_operating_cash", minimum_operating_cash),
        ("monthly_stressed_cash_burn", monthly_stressed_cash_burn),
    )
    if any(item is None for item in inputs):
        return _non_ok(
            "ratio.liquidity_runway_months",
            RatioStatus.MISSING,
            RatioReason.MISSING_INPUT,
            plain_label="Months of cash cover under stress",
            professional_name="Liquidity Runway",
            formula_id="liquidity_runway_months",
            components=components,
            interpretation="Cannot be calculated: a liquidity input is not available.",
            corrective_action="Supply cash, revolver availability, minimum operating cash, and the stressed burn rate.",
        )

    assert eligible_cash_value is not None
    assert undrawn_committed_revolver is not None
    assert minimum_operating_cash is not None
    assert monthly_stressed_cash_burn is not None

    available = eligible_cash_value.add(undrawn_committed_revolver).subtract(
        minimum_operating_cash
    )
    burn = monthly_stressed_cash_burn.as_minor_decimal()
    if burn <= Decimal(0):
        interpretation = (
            "Not meaningful: there is no stressed cash burn, so liquidity is not consumed."
            if burn == Decimal(0)
            else "Not meaningful: the business generates cash under stress rather than consuming it."
        )
        return _non_ok(
            "ratio.liquidity_runway_months",
            RatioStatus.NM,
            RatioReason.NM_NO_CASH_BURN,
            plain_label="Months of cash cover under stress",
            professional_name="Liquidity Runway",
            formula_id="liquidity_runway_months",
            components=components,
            interpretation=interpretation,
            corrective_action=None,
        )

    return safe_ratio(
        "ratio.liquidity_runway_months",
        available.as_minor_decimal(),
        burn,
        components=components,
        plain_label="Months of cash cover under stress",
        professional_name="Liquidity Runway",
        formula_id="liquidity_runway_months",
    )


def cash_plus_undrawn_revolver(
    eligible_cash_value: Money | None, undrawn_committed_revolver: Money | None
) -> MoneyMetricResult:
    """Methodology §5.7. Components are preserved rather than collapsed."""
    components = _components(
        ("eligible_cash", eligible_cash_value),
        ("undrawn_committed_revolver", undrawn_committed_revolver),
    )
    if eligible_cash_value is None or undrawn_committed_revolver is None:
        return MoneyMetricResult(
            metric_id="metric.cash_plus_undrawn_revolver",
            status=RatioStatus.MISSING,
            reason_code=RatioReason.MISSING_INPUT,
            plain_label="Cash plus committed borrowing capacity",
            professional_name="Cash Plus Undrawn Revolver",
            formula_id="cash_plus_undrawn_revolver",
            components=components,
            confidence=ConfidenceLevel.BLOCKED,
            corrective_action="Supply eligible cash and committed undrawn revolver availability.",
        )
    ensure_same_currency(eligible_cash_value, undrawn_committed_revolver)
    return MoneyMetricResult(
        metric_id="metric.cash_plus_undrawn_revolver",
        status=RatioStatus.OK,
        reason_code=RatioReason.OK,
        value=eligible_cash_value.add(undrawn_committed_revolver),
        plain_label="Cash plus committed borrowing capacity",
        professional_name="Cash Plus Undrawn Revolver",
        formula_id="cash_plus_undrawn_revolver",
        components=components,
    )


def sources_uses_surplus(
    *,
    committed_sources: Sequence[Money],
    contractual_uses: Sequence[Money],
    horizon_label: str,
) -> MoneyMetricResult:
    """Methodology §5.8.

    Only committed sources may be supplied; uncommitted refinancing is never assumed.
    A negative result is a shortfall. The horizon must be labeled explicitly because
    the figure is meaningless without it.
    """
    if not horizon_label:
        raise ValueError(
            "horizon_label is required: a sources-and-uses surplus is horizon-specific"
        )
    sources = list(committed_sources)
    uses = list(contractual_uses)
    ensure_same_currency(*sources, *uses)
    components = tuple(
        MetricComponent(
            name="committed_source",
            value=item.as_minor_decimal(),
            currency=item.currency,
        )
        for item in sources
    ) + tuple(
        MetricComponent(
            name="contractual_use",
            value=item.as_minor_decimal(),
            currency=item.currency,
        )
        for item in uses
    )
    if not sources and not uses:
        return MoneyMetricResult(
            metric_id="metric.sources_uses_surplus",
            status=RatioStatus.MISSING,
            reason_code=RatioReason.MISSING_INPUT,
            plain_label="Money available compared with money required",
            professional_name="Sources versus Uses",
            formula_id="sources_uses_surplus",
            components=components,
            confidence=ConfidenceLevel.BLOCKED,
            corrective_action="Supply at least one committed source or contractual use.",
        )
    template = sources[0] if sources else uses[0]
    total_sources = money_sum(sources, template=template)
    total_uses = money_sum(uses, template=template)
    surplus = total_sources.subtract(total_uses)  # type: ignore[union-attr,arg-type]
    return MoneyMetricResult(
        metric_id="metric.sources_uses_surplus",
        status=RatioStatus.OK,
        reason_code=RatioReason.OK,
        value=surplus,
        plain_label="Money available compared with money required",
        professional_name="Sources versus Uses",
        formula_id="sources_uses_surplus",
        components=components,
        interpretation=(
            f"Shortfall over {horizon_label}."
            if surplus.amount_minor < 0
            else f"Surplus over {horizon_label}."
        ),
    )


# -- §6 cash flow ----------------------------------------------------------


def cfo_to_debt(cfo: Money | None, gross_debt_value: Money | None) -> RatioResult:
    """Methodology §6.1."""
    return _money_ratio(
        "ratio.cfo_debt",
        cfo,
        gross_debt_value,
        numerator_name="cfo",
        denominator_name="gross_debt",
        plain_label="Operating cash compared with debt",
        professional_name="CFO / Debt",
        formula_id="cfo_to_debt",
        zero_denominator_reason=RatioReason.NM_NO_OBLIGATION,
        zero_denominator_interpretation="Not meaningful: the borrower has no debt outstanding.",
    )


def fcf_to_debt(
    free_cash_flow_value: Money | None, gross_debt_value: Money | None
) -> RatioResult:
    """Methodology §6.2."""
    return _money_ratio(
        "ratio.fcf_debt",
        free_cash_flow_value,
        gross_debt_value,
        numerator_name="free_cash_flow",
        denominator_name="gross_debt",
        plain_label="Spare cash compared with debt",
        professional_name="FCF / Debt",
        formula_id="fcf_to_debt",
        zero_denominator_reason=RatioReason.NM_NO_OBLIGATION,
        zero_denominator_interpretation="Not meaningful: the borrower has no debt outstanding.",
    )


def fcf_margin(
    free_cash_flow_value: Money | None, revenue: Money | None
) -> RatioResult:
    """Methodology §6.3 and §7.2."""
    return _money_ratio(
        "ratio.fcf_margin",
        free_cash_flow_value,
        revenue,
        numerator_name="free_cash_flow",
        denominator_name="revenue",
        plain_label="Spare cash as a share of sales",
        professional_name="FCF Margin",
        formula_id="fcf_margin",
        require_positive_denominator=True,
    )


def cash_conversion(
    cfo: Money | None, reported_ebitda_value: Money | None
) -> RatioResult:
    """Methodology §6.4: ``CFO / Reported EBITDA``.

    Both operands are unadjusted. Pairing an unadjusted CFO with an adjusted EBITDA
    would mechanically depress the ratio whenever an approved add-back has no matching
    cash-flow adjustment.
    """
    return _money_ratio(
        "ratio.cash_conversion",
        cfo,
        reported_ebitda_value,
        numerator_name="cfo",
        denominator_name="reported_ebitda",
        plain_label="How much reported profit turns into cash",
        professional_name="Cash Conversion",
        formula_id="cash_conversion",
        require_positive_denominator=True,
    )


def capex_to_cfo(capex: Money | None, cfo: Money | None) -> RatioResult:
    """Methodology §6.5."""
    return _money_ratio(
        "ratio.capex_cfo",
        capex,
        cfo,
        numerator_name="capex",
        denominator_name="cfo",
        plain_label="Share of operating cash spent on assets",
        professional_name="Capex / CFO",
        formula_id="capex_to_cfo",
        require_positive_denominator=True,
    )


def capex_to_ebitda(
    capex: Money | None, adjusted_ebitda_value: Money | None
) -> RatioResult:
    """Methodology §6.5."""
    return _money_ratio(
        "ratio.capex_ebitda",
        capex,
        adjusted_ebitda_value,
        numerator_name="capex",
        denominator_name="adjusted_ebitda",
        plain_label="Share of earnings spent on assets",
        professional_name="Capex / EBITDA",
        formula_id="capex_to_ebitda",
        require_positive_denominator=True,
    )


def _population_volatility(
    metric_id: str,
    observations: Sequence[Decimal],
    *,
    plain_label: str,
    professional_name: str,
    formula_id: str,
    components: tuple[MetricComponent, ...],
    minimum_periods: int = MINIMUM_VOLATILITY_PERIODS,
) -> RatioResult:
    """Population standard deviation divided by the absolute mean (§6.6, §7.5)."""
    if len(observations) < minimum_periods:
        return _non_ok(
            metric_id,
            RatioStatus.MISSING,
            RatioReason.MISSING_INPUT,
            plain_label=plain_label,
            professional_name=professional_name,
            formula_id=formula_id,
            components=components,
            interpretation=(
                f"Cannot be calculated: {minimum_periods} comparable annual periods are "
                f"required and {len(observations)} were supplied."
            ),
            corrective_action=f"Supply at least {minimum_periods} comparable annual periods.",
        )

    with localcontext() as ctx:
        ctx.prec = ENGINE_PRECISION
        count = Decimal(len(observations))
        total = Decimal(0)
        for observation in observations:
            total += observation
        mean = total / count
        squared = Decimal(0)
        for observation in observations:
            deviation = observation - mean
            squared += deviation * deviation
        variance = squared / count
        standard_deviation = variance.sqrt()
        absolute_mean = abs(mean)

    return safe_ratio(
        metric_id,
        standard_deviation,
        absolute_mean,
        components=components
        + _components(
            ("population_standard_deviation", standard_deviation),
            ("absolute_mean", absolute_mean),
        ),
        plain_label=plain_label,
        professional_name=professional_name,
        formula_id=formula_id,
        zero_denominator_interpretation=(
            "Not meaningful: the average of the period values is zero."
        ),
    )


def cashflow_volatility(
    historical_cfads: Sequence[Money],
    minimum_periods: int = MINIMUM_VOLATILITY_PERIODS,
) -> RatioResult:
    """Methodology §6.6. Population sigma of historical CFADS over its absolute mean."""
    values = list(historical_cfads)
    ensure_same_currency(*values)
    return _population_volatility(
        "ratio.cashflow_volatility",
        [item.as_minor_decimal() for item in values],
        plain_label="How much cash flow swings year to year",
        professional_name="Cash-Flow Volatility",
        formula_id="cashflow_volatility",
        components=_components(*[("historical_cfads", item) for item in values]),
        minimum_periods=minimum_periods,
    )


def revenue_volatility(
    historical_revenue: Sequence[Money],
    minimum_periods: int = MINIMUM_VOLATILITY_PERIODS,
) -> RatioResult:
    """Methodology §7.5."""
    values = list(historical_revenue)
    ensure_same_currency(*values)
    return _population_volatility(
        "ratio.revenue_volatility",
        [item.as_minor_decimal() for item in values],
        plain_label="How much sales swing year to year",
        professional_name="Revenue Volatility",
        formula_id="revenue_volatility",
        components=_components(*[("historical_revenue", item) for item in values]),
        minimum_periods=minimum_periods,
    )


def margin_volatility(
    historical_ebitda_margins: Sequence[Decimal],
    minimum_periods: int = MINIMUM_VOLATILITY_PERIODS,
) -> RatioResult:
    """Methodology §7.5, over EBITDA-margin observations."""
    values = list(historical_ebitda_margins)
    for value in values:
        if not isinstance(value, Decimal):
            raise TypeError("margin observations must be Decimal")
    return _population_volatility(
        "ratio.margin_volatility",
        values,
        plain_label="How much profitability swings year to year",
        professional_name="Margin Volatility",
        formula_id="margin_volatility",
        components=_components(
            *[("historical_ebitda_margin", item) for item in values]
        ),
        minimum_periods=minimum_periods,
    )


def positive_fcf_years(historical_fcf: Sequence[Money]) -> RatioResult:
    """Methodology §6.7.

    ``value`` is the share of comparable years with positive free cash flow, expressed
    as a fraction in ``[0, 1]``. The count and the period total are preserved as
    components so a caller can present either form.
    """
    values = list(historical_fcf)
    ensure_same_currency(*values)
    components = _components(*[("historical_fcf", item) for item in values])
    if not values:
        return _non_ok(
            "metric.positive_fcf_years",
            RatioStatus.MISSING,
            RatioReason.MISSING_INPUT,
            plain_label="Years with spare cash",
            professional_name="Positive FCF Years",
            formula_id="positive_fcf_years",
            components=components,
            interpretation="Cannot be calculated: no comparable annual periods were supplied.",
            corrective_action="Supply comparable annual free-cash-flow history.",
        )
    positive = 0
    for item in values:
        if item.is_positive():
            positive += 1
    return safe_ratio(
        "metric.positive_fcf_years",
        Decimal(positive),
        Decimal(len(values)),
        components=components
        + _components(
            ("positive_years", Decimal(positive)), ("total_years", Decimal(len(values)))
        ),
        plain_label="Years with spare cash",
        professional_name="Positive FCF Years",
        formula_id="positive_fcf_years",
        interpretation=f"{positive} of {len(values)} comparable years had positive free cash flow.",
    )


# -- §7 profitability and trend -------------------------------------------


def revenue_growth(
    current_revenue: Money | None, prior_revenue: Money | None
) -> RatioResult:
    """Methodology §7.1: ``current / prior - 1``.

    A prior value of zero or below returns an explicit NM state, because a growth
    percentage measured against a nonpositive base is economically misleading.
    """
    return _money_ratio(
        "ratio.revenue_growth",
        current_revenue,
        prior_revenue,
        numerator_name="current_revenue",
        denominator_name="prior_revenue",
        plain_label="Change in sales",
        professional_name="Revenue Growth",
        formula_id="revenue_growth",
        require_positive_denominator=True,
        offset=Decimal(-1),
    )


def ebitda_growth(
    current_adjusted_ebitda: Money | None, prior_adjusted_ebitda: Money | None
) -> RatioResult:
    """Methodology §7.1."""
    return _money_ratio(
        "ratio.ebitda_growth",
        current_adjusted_ebitda,
        prior_adjusted_ebitda,
        numerator_name="current_adjusted_ebitda",
        denominator_name="prior_adjusted_ebitda",
        plain_label="Change in earnings",
        professional_name="EBITDA Growth",
        formula_id="ebitda_growth",
        require_positive_denominator=True,
        offset=Decimal(-1),
    )


def ebitda_margin(
    adjusted_ebitda_value: Money | None, revenue: Money | None
) -> RatioResult:
    """Methodology §7.2."""
    return _money_ratio(
        "ratio.ebitda_margin",
        adjusted_ebitda_value,
        revenue,
        numerator_name="adjusted_ebitda",
        denominator_name="revenue",
        plain_label="Earnings as a share of sales",
        professional_name="EBITDA Margin",
        formula_id="ebitda_margin",
        require_positive_denominator=True,
    )


def ebit_margin(
    adjusted_ebit_value: Money | None, revenue: Money | None
) -> RatioResult:
    """Methodology §7.2."""
    return _money_ratio(
        "ratio.ebit_margin",
        adjusted_ebit_value,
        revenue,
        numerator_name="adjusted_ebit",
        denominator_name="revenue",
        plain_label="Operating profit as a share of sales",
        professional_name="EBIT Margin",
        formula_id="ebit_margin",
        require_positive_denominator=True,
    )


def _with_confidence_factor(
    result: RatioResult, factor: str, *, interpretation: str | None = None
) -> RatioResult:
    """Return a copy of ``result`` carrying one additional confidence factor.

    Every other field is preserved, including ``policy_ref``, ``confidence``, and
    ``corrective_action``. The interpretation is replaced only on a successful result,
    so a missing-input or not-meaningful explanation is never overwritten.
    """
    if factor in result.confidence_factors:
        return result
    replacement = (
        interpretation
        if interpretation is not None and result.is_ok
        else result.interpretation
    )
    return RatioResult(
        metric_id=result.metric_id,
        status=result.status,
        reason_code=result.reason_code,
        value=result.value,
        value_exact=result.value_exact,
        plain_label=result.plain_label,
        professional_name=result.professional_name,
        formula_id=result.formula_id,
        policy_ref=result.policy_ref,
        components=result.components,
        confidence=(ConfidenceLevel.LOW if result.is_ok else result.confidence),
        confidence_factors=result.confidence_factors + (factor,),
        interpretation=replacement,
        corrective_action=result.corrective_action,
    )


def _average_minor(
    beginning: Money | None, ending: Money | None
) -> tuple[Decimal | None, bool]:
    """Return the average of two balances in minor units and whether it is an average.

    When only the ending balance is available, that value is used and the caller
    records a lower-confidence factor (§7.3).
    """
    ensure_same_currency(beginning, ending)
    if ending is None:
        return None, False
    if beginning is None:
        return ending.as_minor_decimal(), False
    with localcontext() as ctx:
        ctx.prec = ENGINE_PRECISION
        return (beginning.as_minor_decimal() + ending.as_minor_decimal()) / Decimal(
            2
        ), True


def return_on_assets(
    net_income: Money | None,
    ending_total_assets: Money | None,
    beginning_total_assets: Money | None = None,
) -> RatioResult:
    """Methodology §7.3: ``Net Income / Average Total Assets``."""
    average_assets, _averaged = _average_minor(
        beginning_total_assets, ending_total_assets
    )
    ensure_same_currency(net_income, ending_total_assets, beginning_total_assets)
    result = safe_ratio(
        "ratio.roa",
        None if net_income is None else net_income.as_minor_decimal(),
        average_assets,
        components=_components(
            ("net_income", net_income),
            ("beginning_total_assets", beginning_total_assets),
            ("ending_total_assets", ending_total_assets),
            ("average_total_assets", average_assets),
        ),
        plain_label="Profit earned on the assets employed",
        professional_name="Return on Assets",
        formula_id="return_on_assets",
        require_positive_denominator=True,
    )
    if beginning_total_assets is None and ending_total_assets is not None:
        return _with_confidence_factor(
            result,
            "single_period_asset_base",
            interpretation=(
                "Calculated on the ending asset balance because an opening balance was "
                "not available."
            ),
        )
    return result


def invested_capital(
    *, gross_debt_value: Money, equity: Money, unrestricted_cash: Money
) -> Money:
    """Methodology §7.4: ``Gross Debt + Equity - Unrestricted Cash``.

    Uses unrestricted cash rather than availability-factored eligible cash: the
    lending-policy cash-availability factor does not belong in a return metric.
    """
    ensure_same_currency(gross_debt_value, equity, unrestricted_cash)
    return gross_debt_value.add(equity).subtract(unrestricted_cash)


def return_on_invested_capital(
    adjusted_ebit_value: Money | None,
    effective_cash_tax_rate: Decimal | None,
    ending_invested_capital: Money | None,
    beginning_invested_capital: Money | None = None,
) -> RatioResult:
    """Methodology §7.4: ``NOPAT / Average Invested Capital``.

    ``NOPAT = Adjusted EBIT x (1 - effective cash tax rate)``. This illustrative
    definition is one of several in industry practice and is labeled as such.
    """
    if effective_cash_tax_rate is not None:
        if not isinstance(effective_cash_tax_rate, Decimal):
            raise ValueError("effective_cash_tax_rate must be a Decimal")
        if effective_cash_tax_rate < Decimal(0) or effective_cash_tax_rate > Decimal(1):
            raise ValueError(
                f"effective_cash_tax_rate must be within [0,1], got {effective_cash_tax_rate}"
            )

    average_capital, _averaged = _average_minor(
        beginning_invested_capital, ending_invested_capital
    )
    nopat: Decimal | None = None
    if adjusted_ebit_value is not None and effective_cash_tax_rate is not None:
        with localcontext() as ctx:
            ctx.prec = ENGINE_PRECISION
            nopat = adjusted_ebit_value.as_minor_decimal() * (
                Decimal(1) - effective_cash_tax_rate
            )

    result = safe_ratio(
        "ratio.roic",
        nopat,
        average_capital,
        components=_components(
            ("adjusted_ebit", adjusted_ebit_value),
            ("effective_cash_tax_rate", effective_cash_tax_rate),
            ("nopat", nopat),
            ("beginning_invested_capital", beginning_invested_capital),
            ("ending_invested_capital", ending_invested_capital),
            ("average_invested_capital", average_capital),
        ),
        plain_label="Profit earned on the money invested in the business",
        professional_name="Return on Invested Capital",
        formula_id="return_on_invested_capital",
        require_positive_denominator=True,
    )
    if beginning_invested_capital is None and ending_invested_capital is not None:
        return _with_confidence_factor(
            result,
            "single_period_invested_capital_base",
            interpretation=(
                "Calculated on the ending invested-capital balance because an opening "
                "balance was not available."
            ),
        )
    return result
