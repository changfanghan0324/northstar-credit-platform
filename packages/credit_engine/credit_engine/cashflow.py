"""Debt and cash aggregations.

Implements ``docs/methodology.md`` §2 in full: gross/adjusted/net debt, EBITDA and
adjusted EBITDA, adjusted EBIT, EBITDAR, free cash flow, CFADS, and annual debt
service. Every function is a pure transformation over :class:`Money` and verifies
that its operands share one currency (§1.1).

Pure module: no I/O, no framework, no float.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from .money import (
    Money,
    PolicyConfigurationError,
    ensure_same_currency,
    money_sum,
    scale_money,
)

__all__ = [
    "adjusted_debt",
    "adjusted_ebit",
    "adjusted_ebitda",
    "annual_debt_service",
    "cfads",
    "ebitda",
    "ebitdar",
    "eligible_cash",
    "free_cash_flow",
    "gross_debt",
    "net_debt",
    "total_debt_service",
]


def _optional(amount: Money | None, template: Money) -> Money:
    """Treat an absent optional component as zero in the template's currency."""
    if amount is None:
        return template.zero_like()
    ensure_same_currency(template, amount)
    return amount


# -- §2.1-§2.3 debt --------------------------------------------------------


def gross_debt(
    *,
    short_term_borrowings: Money,
    current_maturities: Money,
    long_term_debt: Money,
    finance_lease_liabilities: Money,
    selected_debt_like_obligations: Money | None = None,
) -> Money:
    """Methodology §2.1. No cash netting occurs here."""
    ensure_same_currency(
        short_term_borrowings,
        current_maturities,
        long_term_debt,
        finance_lease_liabilities,
        selected_debt_like_obligations,
    )
    total = money_sum(
        [
            short_term_borrowings,
            current_maturities,
            long_term_debt,
            finance_lease_liabilities,
            _optional(selected_debt_like_obligations, short_term_borrowings),
        ]
    )
    if (
        total is None
    ):  # pragma: no cover - unreachable, required components are non-optional
        raise ValueError("gross_debt requires at least one component")
    return total


def adjusted_debt(
    *,
    gross_debt_value: Money,
    selected_operating_leases: Money | None = None,
    selected_pension_or_debt_like: Money | None = None,
) -> Money:
    """Methodology §2.2.

    Inclusion is an explicit caller decision: an obligation the caller does not pass
    is not silently included, and one that is passed is not silently dropped.
    """
    ensure_same_currency(
        gross_debt_value, selected_operating_leases, selected_pension_or_debt_like
    )
    return gross_debt_value.add(
        _optional(selected_operating_leases, gross_debt_value)
    ).add(_optional(selected_pension_or_debt_like, gross_debt_value))


def eligible_cash(
    *, unrestricted_cash: Money, cash_availability_factor: Decimal
) -> Money:
    """Methodology §2.3: ``unrestricted cash x availability factor``.

    The factor is policy data constrained to ``[0, 1]``.
    """
    if not isinstance(cash_availability_factor, Decimal):
        raise TypeError("cash_availability_factor must be a Decimal")
    if cash_availability_factor < Decimal(0) or cash_availability_factor > Decimal(1):
        raise ValueError(
            f"cash_availability_factor must be within [0,1], got {cash_availability_factor}"
        )
    return scale_money(unrestricted_cash, cash_availability_factor)


def net_debt(*, gross_debt_value: Money, eligible_cash_value: Money) -> Money:
    """Methodology §2.3. May be negative (net cash) and is never floored at zero."""
    ensure_same_currency(gross_debt_value, eligible_cash_value)
    return gross_debt_value.subtract(eligible_cash_value)


# -- §2.4-§2.6 earnings and cash flow --------------------------------------


def ebitda(*, ebit: Money, depreciation_amortization: Money) -> Money:
    """Methodology §2.4: ``EBIT + D&A``."""
    ensure_same_currency(ebit, depreciation_amortization)
    return ebit.add(depreciation_amortization)


def adjusted_ebitda(
    *,
    reported_ebitda: Money,
    approved_positive_adjustments: Money | None = None,
    approved_negative_adjustments: Money | None = None,
) -> Money:
    """Methodology §2.5.

    Only adjustments the caller has already marked approved may be supplied; the
    engine performs no approval and applies no default add-back. Both adjustment
    inputs are magnitudes: the negative leg is subtracted, not sign-flipped.
    """
    ensure_same_currency(
        reported_ebitda, approved_positive_adjustments, approved_negative_adjustments
    )
    return reported_ebitda.add(
        _optional(approved_positive_adjustments, reported_ebitda)
    ).subtract(_optional(approved_negative_adjustments, reported_ebitda))


def adjusted_ebit(
    *, adjusted_ebitda_value: Money, depreciation_amortization: Money
) -> Money:
    """Methodology §4.2: ``Adjusted EBIT = Adjusted EBITDA - D&A``."""
    ensure_same_currency(adjusted_ebitda_value, depreciation_amortization)
    return adjusted_ebitda_value.subtract(depreciation_amortization)


def ebitdar(
    *, adjusted_ebitda_value: Money, contractual_rent_or_lease_expense: Money
) -> Money:
    """Methodology §4.4: ``EBITDAR = Adjusted EBITDA + contractual rent``.

    The add-back exists so that rent appearing in the fixed-charge denominator is not
    also deducted inside the numerator.
    """
    ensure_same_currency(adjusted_ebitda_value, contractual_rent_or_lease_expense)
    return adjusted_ebitda_value.add(contractual_rent_or_lease_expense)


def free_cash_flow(*, cfo: Money, capex: Money) -> Money:
    """Methodology §2.6: ``CFO - Capex``.

    Capex is supplied as a positive cash-use amount, per the normalized-layer
    sign convention.
    """
    ensure_same_currency(cfo, capex)
    return cfo.subtract(capex)


# -- §2.7 CFADS ------------------------------------------------------------


def cfads(
    *,
    adjusted_ebitda_value: Money,
    cash_taxes: Money,
    maintenance_capex: Money,
    increase_in_operating_working_capital: Money,
    mandatory_pension_contributions: Money | None = None,
    other_mandatory_operating_cash_uses: Money | None = None,
) -> Money:
    """Methodology §2.7.

    ``increase_in_operating_working_capital`` is a signed cash use: a positive value
    is an investment in working capital and reduces CFADS, while a negative value is
    a release and increases it.
    """
    ensure_same_currency(
        adjusted_ebitda_value,
        cash_taxes,
        maintenance_capex,
        increase_in_operating_working_capital,
        mandatory_pension_contributions,
        other_mandatory_operating_cash_uses,
    )
    return (
        adjusted_ebitda_value.subtract(cash_taxes)
        .subtract(maintenance_capex)
        .subtract(increase_in_operating_working_capital)
        .subtract(_optional(mandatory_pension_contributions, adjusted_ebitda_value))
        .subtract(_optional(other_mandatory_operating_cash_uses, adjusted_ebitda_value))
    )


# -- §2.8 annual debt service ---------------------------------------------


def annual_debt_service(
    *,
    cash_interest: Money,
    scheduled_principal: Money,
    required_fixed_charges: Money | None = None,
    fixed_charges_deducted_in_cfads: bool = False,
) -> Money:
    """Methodology §2.8.

    Only obligations *not already deducted* in the CFADS base may be added. Finance
    lease principal and interest qualify, because they sit below EBITDA. Contractual
    operating rent does not: it is already inside EBITDA and therefore inside CFADS,
    so including it here would deduct the same cash twice. Rent belongs to
    fixed-charge coverage (§4.4) with the matching EBITDAR add-back.

    ``fixed_charges_deducted_in_cfads=True`` names the invalid configuration
    explicitly and rejects it rather than silently producing an understated DSCR.
    """
    if fixed_charges_deducted_in_cfads:
        raise PolicyConfigurationError(
            "a fixed charge already deducted inside CFADS may not also be added to "
            "annual debt service; use fixed_charge_coverage() with the EBITDAR "
            "add-back instead (methodology 2.8, 4.4)"
        )
    ensure_same_currency(cash_interest, scheduled_principal, required_fixed_charges)
    return cash_interest.add(scheduled_principal).add(
        _optional(required_fixed_charges, cash_interest)
    )


def total_debt_service(services: Iterable[Money]) -> Money | None:
    """Aggregate per-instrument annual debt service into a portfolio figure."""
    return money_sum(list(services))
