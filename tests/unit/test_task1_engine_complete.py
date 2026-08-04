from __future__ import annotations

from decimal import Decimal

import pytest
from credit_engine import cashflow, ratios
from credit_engine.money import (
    CurrencyMismatchError,
    Money,
    PolicyConfigurationError,
    ensure_same_currency,
    money_sum,
    normalize_reported_amount,
    scale_money,
)
from credit_engine.types import (
    ConfidenceLevel,
    MetricComponent,
    MoneyMetricResult,
    RatioReason,
    RatioResult,
    RatioStatus,
)
from pydantic import ValidationError


def money(value: int, currency: str = "USD", exponent: int = 2) -> Money:
    return Money(amount_minor=value, currency=currency, minor_unit_exponent=exponent)


def assert_ok(result: RatioResult, expected: str) -> None:
    assert result.status is RatioStatus.OK
    assert result.reason_code is RatioReason.OK
    assert result.value == Decimal(expected)
    assert result.value.as_tuple().exponent == -4
    assert result.value_exact is not None
    assert result.formula_id


def test_money_validation_and_arithmetic_contract() -> None:
    with pytest.raises((TypeError, ValidationError)):
        money(True)  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationError)):
        money(Decimal(1))  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValidationError)):
        Money(amount_minor=1, currency=123, minor_unit_exponent=2)  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        money(1, "usd")
    with pytest.raises(ValidationError):
        money(1, "US")
    with pytest.raises((TypeError, ValidationError)):
        Money(amount_minor=1, currency="USD", minor_unit_exponent=True)
    with pytest.raises(ValidationError):
        money(1, exponent=5)
    with pytest.raises(ValidationError, match="USD requires"):
        money(1, exponent=0)

    amount = money(125)
    other = money(25)
    assert amount.add(other).amount_minor == 150
    assert amount.subtract(other).amount_minor == 100
    assert amount.negate().amount_minor == -125
    assert amount.is_positive()
    assert not amount.is_zero()
    assert amount.as_minor_decimal() == Decimal(125)
    assert amount.zero_like().is_zero()


def test_currency_and_money_helpers_cover_empty_scale_and_normalization_edges() -> None:
    usd = money(10)
    assert ensure_same_currency(None, usd) == "USD"
    assert ensure_same_currency(None) is None
    with pytest.raises(CurrencyMismatchError, match="scale mismatch"):
        ensure_same_currency(money(10, "ABC", 2), money(10, "ABC", 3))

    assert money_sum([]) is None
    assert money_sum([], template=usd) == usd.zero_like()
    assert money_sum([usd, None, money(5)]).amount_minor == 15  # type: ignore[union-attr]

    assert scale_money(money(5), Decimal("0.5")).amount_minor == 3
    with pytest.raises(TypeError):
        scale_money(usd, 0.5)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        normalize_reported_amount(
            reported_value=True, currency="USD", minor_unit_exponent=2
        )
    with pytest.raises(TypeError):
        normalize_reported_amount(
            reported_value=1, currency="USD", minor_unit_exponent=2, reported_scale=True
        )
    with pytest.raises(ValueError, match="positive"):
        normalize_reported_amount(
            reported_value=1, currency="USD", minor_unit_exponent=2, reported_scale=0
        )
    with pytest.raises(ValueError, match="whole minor unit"):
        normalize_reported_amount(
            reported_value=Decimal("0.001"), currency="USD", minor_unit_exponent=2
        )


def test_cashflow_surface_and_configuration_guards() -> None:
    gross = cashflow.gross_debt(
        short_term_borrowings=money(10),
        current_maturities=money(5),
        long_term_debt=money(60),
        finance_lease_liabilities=money(4),
        selected_debt_like_obligations=money(1),
    )
    assert gross.amount_minor == 80
    adjusted = cashflow.adjusted_debt(
        gross_debt_value=gross,
        selected_operating_leases=money(8),
        selected_pension_or_debt_like=money(2),
    )
    assert adjusted.amount_minor == 90
    eligible = cashflow.eligible_cash(
        unrestricted_cash=money(20), cash_availability_factor=Decimal("0.8")
    )
    assert eligible.amount_minor == 16
    assert (
        cashflow.net_debt(
            gross_debt_value=gross, eligible_cash_value=eligible
        ).amount_minor
        == 64
    )

    reported = cashflow.ebitda(ebit=money(30), depreciation_amortization=money(10))
    adjusted_ebitda = cashflow.adjusted_ebitda(
        reported_ebitda=reported,
        approved_positive_adjustments=money(3),
        approved_negative_adjustments=money(2),
    )
    assert adjusted_ebitda.amount_minor == 41
    assert (
        cashflow.adjusted_ebit(
            adjusted_ebitda_value=adjusted_ebitda, depreciation_amortization=money(10)
        ).amount_minor
        == 31
    )
    assert (
        cashflow.ebitdar(
            adjusted_ebitda_value=adjusted_ebitda,
            contractual_rent_or_lease_expense=money(4),
        ).amount_minor
        == 45
    )
    assert cashflow.free_cash_flow(cfo=money(24), capex=money(7)).amount_minor == 17
    assert (
        cashflow.cfads(
            adjusted_ebitda_value=adjusted_ebitda,
            cash_taxes=money(4),
            maintenance_capex=money(6),
            increase_in_operating_working_capital=money(2),
        ).amount_minor
        == 29
    )
    assert (
        cashflow.annual_debt_service(
            cash_interest=money(5), scheduled_principal=money(7)
        ).amount_minor
        == 12
    )
    assert cashflow.total_debt_service([money(5), money(7)]).amount_minor == 12  # type: ignore[union-attr]
    assert cashflow.total_debt_service([]) is None

    with pytest.raises(TypeError):
        cashflow.eligible_cash(unrestricted_cash=money(1), cash_availability_factor=1)  # type: ignore[arg-type]
    for invalid in (Decimal("-0.01"), Decimal("1.01")):
        with pytest.raises(ValueError, match="within"):
            cashflow.eligible_cash(
                unrestricted_cash=money(1), cash_availability_factor=invalid
            )
    with pytest.raises(PolicyConfigurationError):
        cashflow.annual_debt_service(
            cash_interest=money(1),
            scheduled_principal=money(1),
            required_fixed_charges=money(1),
            fixed_charges_deducted_in_cfads=True,
        )


@pytest.mark.parametrize(
    ("calculation", "expected"),
    [
        (lambda: ratios.gross_debt_to_ebitda(money(60), money(20)), "3.0000"),
        (lambda: ratios.adjusted_debt_to_ebitda(money(70), money(20)), "3.5000"),
        (lambda: ratios.net_debt_to_ebitda(money(40), money(20)), "2.0000"),
        (lambda: ratios.debt_to_capital(money(60), money(40)), "0.6000"),
        (lambda: ratios.debt_to_equity(money(60), money(40)), "1.5000"),
        (lambda: ratios.liabilities_to_assets(money(75), money(100)), "0.7500"),
        (lambda: ratios.secured_debt_to_total(money(30), money(60)), "0.5000"),
        (lambda: ratios.interest_coverage(money(30), money(5)), "6.0000"),
        (lambda: ratios.ebit_interest_coverage(money(25), money(5)), "5.0000"),
        (lambda: ratios.fcf_to_cash_interest(money(15), money(5)), "3.0000"),
        (lambda: ratios.current_ratio(money(50), money(25)), "2.0000"),
        (lambda: ratios.cash_ratio(money(10), money(25)), "0.4000"),
        (lambda: ratios.cfo_to_debt(money(20), money(80)), "0.2500"),
        (lambda: ratios.fcf_to_debt(money(12), money(80)), "0.1500"),
        (lambda: ratios.fcf_margin(money(12), money(120)), "0.1000"),
        (lambda: ratios.cash_conversion(money(24), money(30)), "0.8000"),
        (lambda: ratios.capex_to_cfo(money(6), money(24)), "0.2500"),
        (lambda: ratios.capex_to_ebitda(money(6), money(30)), "0.2000"),
        (lambda: ratios.revenue_growth(money(120), money(100)), "0.2000"),
        (lambda: ratios.ebitda_growth(money(30), money(25)), "0.2000"),
        (lambda: ratios.ebitda_margin(money(30), money(120)), "0.2500"),
        (lambda: ratios.ebit_margin(money(24), money(120)), "0.2000"),
    ],
)
def test_ratio_happy_path_surface(calculation: object, expected: str) -> None:
    assert_ok(calculation(), expected)  # type: ignore[operator]


def test_ratio_non_ok_paths_keep_trace_and_status_semantics() -> None:
    missing = ratios.safe_ratio(
        "test.trace", None, Decimal(2), formula_id="f-1", policy_ref="p-1"
    )
    assert missing.status is RatioStatus.MISSING
    assert missing.confidence is ConfidenceLevel.BLOCKED
    assert missing.formula_id == "f-1"
    assert missing.policy_ref == "p-1"
    assert missing.corrective_action

    adverse = ratios.safe_ratio(
        "test.trace",
        Decimal(1),
        Decimal(-1),
        require_positive_denominator=True,
        formula_id="f-1",
        policy_ref="p-1",
    )
    assert adverse.is_adverse_nm
    assert adverse.policy_ref == "p-1"
    assert not adverse.is_favorable_nm

    zero = ratios.safe_ratio("test.trace", Decimal(1), Decimal(0), policy_ref="p-1")
    assert zero.reason_code is RatioReason.NM_UNDEFINED
    assert zero.policy_ref == "p-1"


def test_interest_and_debt_service_missing_zero_and_currency_cases() -> None:
    assert ratios.interest_coverage(None, money(0)).status is RatioStatus.MISSING
    assert ratios.interest_coverage(money(10), money(0)).is_favorable_nm
    assert (
        ratios.interest_coverage(money(10), money(0), True).reason_code
        is RatioReason.NM_DEFERRED_OBLIGATION
    )

    missing = ratios.debt_service_coverage(None, money(0), True, money(10))
    assert missing.status is RatioStatus.MISSING
    error = ratios.debt_service_coverage(money(10), money(0), True, money(10))
    assert error.status is RatioStatus.ERROR
    assert error.confidence is ConfidenceLevel.BLOCKED
    existing = ratios.debt_service_coverage(money(10), money(0))
    assert existing.is_favorable_nm
    assert_ok(ratios.debt_service_coverage(money(10), money(5)), "2.0000")
    alias = ratios.cfads_debt_service_coverage(money(10), money(5))
    assert alias.metric_id == "ratio.cfads_debt_service"
    assert alias.value == Decimal("2.0000")

    with pytest.raises(CurrencyMismatchError):
        ratios.debt_service_coverage(money(10), money(5), True, money(2, "EUR", 2))


def test_fixed_charge_and_liquidity_ratio_paths() -> None:
    missing = ratios.fixed_charge_coverage(
        ebitdar_value=None,
        cash_taxes=money(1),
        maintenance_capex=money(1),
        increase_in_operating_working_capital=money(1),
        cash_interest=money(1),
        scheduled_principal=money(1),
        contractual_rent=money(1),
    )
    assert missing.status is RatioStatus.MISSING
    fixed = ratios.fixed_charge_coverage(
        ebitdar_value=money(30),
        cash_taxes=money(3),
        maintenance_capex=money(4),
        increase_in_operating_working_capital=money(2),
        cash_interest=money(3),
        scheduled_principal=money(4),
        contractual_rent=money(3),
    )
    assert_ok(fixed, "2.1000")

    assert_ok(
        ratios.quick_ratio(
            cash=money(5),
            eligible_marketable_securities=money(3),
            accounts_receivable=money(12),
            current_liabilities=money(10),
        ),
        "2.0000",
    )
    assert (
        ratios.quick_ratio(
            cash=None,
            eligible_marketable_securities=money(3),
            accounts_receivable=money(12),
            current_liabilities=money(10),
        ).status
        is RatioStatus.MISSING
    )
    assert_ok(
        ratios.short_term_debt_coverage(
            eligible_cash_value=money(10),
            undrawn_committed_revolver=money(20),
            short_term_borrowings=money(5),
            current_maturities=money(5),
        ),
        "3.0000",
    )
    assert (
        ratios.short_term_debt_coverage(
            eligible_cash_value=None,
            undrawn_committed_revolver=money(20),
            short_term_borrowings=money(5),
            current_maturities=money(5),
        ).status
        is RatioStatus.MISSING
    )

    assert_ok(
        ratios.liquidity_runway_months(
            eligible_cash_value=money(10),
            undrawn_committed_revolver=money(20),
            minimum_operating_cash=money(6),
            monthly_stressed_cash_burn=money(4),
        ),
        "6.0000",
    )
    no_burn = ratios.liquidity_runway_months(
        eligible_cash_value=money(10),
        undrawn_committed_revolver=money(20),
        minimum_operating_cash=money(6),
        monthly_stressed_cash_burn=money(0),
    )
    assert no_burn.reason_code is RatioReason.NM_NO_CASH_BURN
    assert no_burn.is_favorable_nm
    generation = ratios.liquidity_runway_months(
        eligible_cash_value=money(10),
        undrawn_committed_revolver=money(20),
        minimum_operating_cash=money(6),
        monthly_stressed_cash_burn=money(-2),
    )
    assert generation.reason_code is RatioReason.NM_NO_CASH_BURN
    assert (
        ratios.liquidity_runway_months(
            eligible_cash_value=None,
            undrawn_committed_revolver=money(20),
            minimum_operating_cash=money(6),
            monthly_stressed_cash_burn=money(4),
        ).status
        is RatioStatus.MISSING
    )


def test_monetary_metrics_have_complete_result_contract() -> None:
    missing_wc = ratios.working_capital(None, money(5))
    assert missing_wc.status is RatioStatus.MISSING
    assert missing_wc.confidence is ConfidenceLevel.BLOCKED
    wc = ratios.working_capital(money(20), money(8))
    assert wc.value == money(12)

    missing_liquidity = ratios.cash_plus_undrawn_revolver(None, money(5))
    assert missing_liquidity.status is RatioStatus.MISSING
    liquidity = ratios.cash_plus_undrawn_revolver(money(7), money(5))
    assert liquidity.value == money(12)

    result = MoneyMetricResult(
        metric_id="metric.test",
        status=RatioStatus.OK,
        reason_code=RatioReason.OK,
        value=money(1),
        confidence=ConfidenceLevel.LOW,
        confidence_factors=("estimated_input",),
    )
    assert result.is_ok
    assert result.confidence_factors == ("estimated_input",)


def test_sources_uses_requires_horizon_and_handles_missing_surplus_and_shortfall() -> (
    None
):
    with pytest.raises(ValueError, match="horizon"):
        ratios.sources_uses_surplus(
            committed_sources=[money(1)], contractual_uses=[], horizon_label=""
        )
    empty = ratios.sources_uses_surplus(
        committed_sources=[], contractual_uses=[], horizon_label="12 months"
    )
    assert empty.status is RatioStatus.MISSING
    surplus = ratios.sources_uses_surplus(
        committed_sources=[money(20)],
        contractual_uses=[money(12)],
        horizon_label="12 months",
    )
    assert surplus.value == money(8)
    assert "Surplus" in surplus.interpretation  # type: ignore[operator]
    shortfall = ratios.sources_uses_surplus(
        committed_sources=[],
        contractual_uses=[money(12)],
        horizon_label="12 months",
    )
    assert shortfall.value == money(-12)
    assert "Shortfall" in shortfall.interpretation  # type: ignore[operator]


def test_volatility_and_historical_metrics_cover_boundaries() -> None:
    assert (
        ratios.cashflow_volatility([money(10), money(12)]).status is RatioStatus.MISSING
    )
    volatility = ratios.cashflow_volatility([money(10), money(20), money(30)])
    assert volatility.status is RatioStatus.OK
    zero_mean = ratios.cashflow_volatility([money(-10), money(0), money(10)])
    assert zero_mean.reason_code is RatioReason.NM_UNDEFINED
    assert ratios.revenue_volatility([money(10), money(11), money(12)]).is_ok
    assert ratios.margin_volatility(
        [Decimal("0.1"), Decimal("0.2"), Decimal("0.3")]
    ).is_ok
    with pytest.raises(TypeError):
        ratios.margin_volatility([Decimal("0.1"), 0.2, Decimal("0.3")])  # type: ignore[list-item]

    assert ratios.positive_fcf_years([]).status is RatioStatus.MISSING
    history = ratios.positive_fcf_years([money(5), money(-1), money(2)])
    assert history.value == Decimal("0.6667")
    assert any(component.name == "positive_years" for component in history.components)


def test_return_metrics_use_average_or_explicit_low_confidence_fallback() -> None:
    roa = ratios.return_on_assets(money(10), money(100), money(80))
    assert_ok(roa, "0.1111")
    fallback_roa = ratios.return_on_assets(money(10), money(100))
    assert fallback_roa.confidence is ConfidenceLevel.LOW
    assert fallback_roa.confidence_factors == ("single_period_asset_base",)
    assert "ending asset" in fallback_roa.interpretation  # type: ignore[operator]
    missing_roa = ratios.return_on_assets(money(10), None)
    assert missing_roa.status is RatioStatus.MISSING
    assert missing_roa.confidence is ConfidenceLevel.BLOCKED

    capital = ratios.invested_capital(
        gross_debt_value=money(60), equity=money(40), unrestricted_cash=money(10)
    )
    assert capital == money(90)
    roic = ratios.return_on_invested_capital(
        money(20), Decimal("0.25"), money(100), money(80)
    )
    assert_ok(roic, "0.1667")
    fallback_roic = ratios.return_on_invested_capital(
        money(20), Decimal("0.25"), money(100)
    )
    assert fallback_roic.confidence is ConfidenceLevel.LOW
    assert fallback_roic.confidence_factors == ("single_period_invested_capital_base",)
    missing_roic = ratios.return_on_invested_capital(None, Decimal("0.25"), money(100))
    assert missing_roic.status is RatioStatus.MISSING
    assert missing_roic.confidence is ConfidenceLevel.BLOCKED
    with pytest.raises(ValueError):
        ratios.return_on_invested_capital(money(20), Decimal("1.1"), money(100))
    with pytest.raises(ValueError):
        ratios.return_on_invested_capital(money(20), Decimal("-0.1"), money(100))
    with pytest.raises(ValueError):
        ratios.return_on_invested_capital(money(20), 0.2, money(100))  # type: ignore[arg-type]


def test_result_properties_and_component_shape() -> None:
    component = MetricComponent(
        name="revenue", value=Decimal(10), currency="USD", period="2026"
    )
    result = RatioResult(
        metric_id="ratio.test",
        status=RatioStatus.NM,
        reason_code=RatioReason.NM_NO_OBLIGATION,
        components=(component,),
    )
    assert not result.is_ok
    assert result.is_favorable_nm
    assert not result.is_adverse_nm
    assert result.components[0].period == "2026"
