from __future__ import annotations

from decimal import Decimal

import pytest
from credit_engine.cashflow import (
    adjusted_ebitda,
    annual_debt_service,
    cfads,
    ebitda,
    free_cash_flow,
)
from credit_engine.money import (
    CurrencyMismatchError,
    Money,
    ensure_same_currency,
    normalize_reported_amount,
)
from credit_engine.ratios import (
    debt_service_coverage,
    gross_debt_to_ebitda,
    interest_coverage,
    net_debt_to_ebitda,
    safe_ratio,
)
from credit_engine.types import RatioReason, RatioStatus
from pydantic import ValidationError

USD = {"currency": "USD", "minor_unit_exponent": 2}


def usd_millions(value: int) -> Money:
    return Money(amount_minor=value * 100_000_000, **USD)


def test_money_rejects_binary_float() -> None:
    with pytest.raises((TypeError, ValidationError, ValueError)):
        Money(amount_minor=1.5, **USD)
    with pytest.raises((TypeError, ValidationError, ValueError)):
        Money(amount_minor=2.0, **USD)


def test_jpy_normalization_uses_zero_minor_unit_exponent() -> None:
    normalized = normalize_reported_amount(
        reported_value=Decimal(1234),
        currency="JPY",
        minor_unit_exponent=0,
        reported_scale=1_000,
    )
    assert normalized.amount_minor == 1_234_000
    assert normalized.minor_unit_exponent == 0


def test_currency_mismatch_is_rejected() -> None:
    usd = Money(amount_minor=100, currency="USD", minor_unit_exponent=2)
    eur = Money(amount_minor=100, currency="EUR", minor_unit_exponent=2)
    with pytest.raises(CurrencyMismatchError):
        ensure_same_currency(usd, eur)


def test_cashflow_functions_return_money_and_never_float() -> None:
    reported_ebitda = ebitda(
        ebit=usd_millions(28), depreciation_amortization=usd_millions(12)
    )
    adjusted = adjusted_ebitda(
        reported_ebitda=reported_ebitda,
        approved_positive_adjustments=usd_millions(2),
        approved_negative_adjustments=usd_millions(1),
    )
    fcf = free_cash_flow(cfo=usd_millions(30), capex=usd_millions(10))
    available = cfads(
        adjusted_ebitda_value=adjusted,
        cash_taxes=usd_millions(5),
        maintenance_capex=usd_millions(8),
        increase_in_operating_working_capital=usd_millions(3),
        mandatory_pension_contributions=usd_millions(1),
        other_mandatory_operating_cash_uses=usd_millions(0),
    )
    service = annual_debt_service(
        cash_interest=usd_millions(6),
        scheduled_principal=usd_millions(8),
        required_fixed_charges=usd_millions(1),
    )

    assert all(
        isinstance(item, Money)
        for item in (reported_ebitda, adjusted, fcf, available, service)
    )
    assert all(
        isinstance(item.amount_minor, int)
        for item in (reported_ebitda, adjusted, fcf, available, service)
    )


def test_negative_ebitda_leverage_is_adverse_not_meaningful() -> None:
    result = gross_debt_to_ebitda(usd_millions(50), usd_millions(-2))
    assert result.status is RatioStatus.NM
    assert result.reason_code is RatioReason.NM_NEGATIVE_BASE
    assert result.value is None


def test_missing_input_is_not_not_meaningful() -> None:
    result = gross_debt_to_ebitda(None, usd_millions(20))
    assert result.status is RatioStatus.MISSING
    assert result.reason_code is RatioReason.MISSING_INPUT


def test_zero_cash_interest_requires_deferred_obligation_guard() -> None:
    cash_pay = interest_coverage(
        adjusted_ebitda_value=usd_millions(20),
        cash_interest=usd_millions(0),
        has_deferred_or_capitalized_interest=False,
    )
    pik = interest_coverage(
        adjusted_ebitda_value=usd_millions(20),
        cash_interest=usd_millions(0),
        has_deferred_or_capitalized_interest=True,
    )
    assert cash_pay.reason_code is RatioReason.NM_NO_CASH_INTEREST
    assert pik.reason_code is RatioReason.NM_DEFERRED_OBLIGATION


def test_existing_and_proforma_zero_service_have_different_semantics() -> None:
    existing = debt_service_coverage(
        cfads_value=usd_millions(20),
        debt_service=usd_millions(0),
        is_proforma=False,
        proposed_principal=usd_millions(0),
    )
    invalid_proforma = debt_service_coverage(
        cfads_value=usd_millions(20),
        debt_service=usd_millions(0),
        is_proforma=True,
        proposed_principal=usd_millions(5),
    )
    assert existing.reason_code is RatioReason.NM_NO_OBLIGATION
    assert invalid_proforma.status is RatioStatus.ERROR
    assert invalid_proforma.reason_code is RatioReason.ERROR_INVALID_INPUT


def test_proforma_zero_service_requires_proposed_principal() -> None:
    result = debt_service_coverage(
        cfads_value=usd_millions(20),
        debt_service=usd_millions(0),
        is_proforma=True,
    )
    assert result.status is RatioStatus.MISSING
    assert result.reason_code is RatioReason.MISSING_INPUT
    assert result.confidence is not None
    assert result.confidence.value == "blocked"
    assert not result.is_favorable_nm


def test_valid_ratio_value_is_decimal_quantized_to_four_places() -> None:
    result = gross_debt_to_ebitda(usd_millions(75), usd_millions(41))
    assert result.status is RatioStatus.OK
    assert isinstance(result.value, Decimal)
    assert result.value.as_tuple().exponent == -4
    assert result.value_exact is not None


def test_round_half_up_contract_uses_non_golden_inputs() -> None:
    positive = safe_ratio("test.positive", Decimal("1.23465"), Decimal(1))
    negative = safe_ratio("test.negative", Decimal("-1.23465"), Decimal(1))
    assert positive.value == Decimal("1.2347")
    assert negative.value == Decimal("-1.2347")


def test_net_cash_is_a_valid_negative_ratio() -> None:
    result = net_debt_to_ebitda(usd_millions(-10), usd_millions(20))
    assert result.status is RatioStatus.OK
    assert result.value == Decimal("-0.5000")


def test_structural_zero_over_zero_is_not_meaningful() -> None:
    result = safe_ratio("test.undefined", Decimal(0), Decimal(0))
    assert result.status is RatioStatus.NM
    assert result.reason_code is RatioReason.NM_UNDEFINED


def test_cashflow_currency_mismatch_is_rejected() -> None:
    eur = Money(amount_minor=100, currency="EUR", minor_unit_exponent=2)
    with pytest.raises(CurrencyMismatchError):
        ebitda(ebit=usd_millions(1), depreciation_amortization=eur)
