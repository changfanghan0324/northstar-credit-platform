"""Exact monetary primitives.

Implements ``docs/methodology.md`` §1.1 (Money) and the currency guard required by
§1.1 and §2.1. Monetary values are integer minor units with an ISO-4217 code and a
minor-unit exponent; arithmetic never touches binary floating point.

Pure module: no I/O, no framework, no float.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal, localcontext

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

#: Working precision for the few Decimal operations performed on monetary values.
#: Set explicitly so results never depend on the ambient decimal context.
ENGINE_PRECISION = 34

#: ISO-4217 minor-unit exponents used by the methodology's worked examples (§1.1).
#: This is a convenience reference only; the exponent is always supplied explicitly.
KNOWN_MINOR_UNIT_EXPONENTS = {"USD": 2, "EUR": 2, "GBP": 2, "JPY": 0, "KWD": 3}

_MAX_MINOR_UNIT_EXPONENT = 4
_CURRENCY_CODE_LENGTH = 3


class CurrencyMismatchError(ValueError):
    """Raised when amounts of different currencies or scales are combined.

    Subclasses :class:`ValueError` so that callers using the broad numeric-input
    contract still catch it. Methodology §1.1 requires a mismatch to abort the
    calculation rather than convert implicitly.
    """


class PolicyConfigurationError(ValueError):
    """Raised when a policy combination is invalid under the methodology.

    Currently used for the §2.8 rule that a fixed charge already deducted inside
    CFADS may not also be added to annual debt service.
    """


class Money(BaseModel):
    """An exact monetary amount in integer minor units.

    Strict by construction: ``amount_minor`` accepts only ``int``. Floats -- including
    integral floats such as ``2.0`` -- and ``bool`` are rejected, because silent
    coercion is exactly the defect methodology §1.1 exists to prevent.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    amount_minor: int
    currency: str
    minor_unit_exponent: int

    @field_validator("amount_minor", mode="before")
    @classmethod
    def _reject_non_integer_amount(cls, value: object) -> object:
        if isinstance(value, bool):
            raise TypeError(
                "amount_minor must be an int; bool is not a monetary amount"
            )
        if isinstance(value, float):
            raise TypeError(
                "amount_minor must be an exact int in minor units; "
                "binary floating point is prohibited by methodology 1.1"
            )
        if isinstance(value, Decimal):
            raise TypeError(
                "amount_minor must be an int; normalize a Decimal with "
                "normalize_reported_amount() before constructing Money"
            )
        return value

    @field_validator("currency", mode="before")
    @classmethod
    def _validate_currency(cls, value: object) -> object:
        if not isinstance(value, str):
            raise TypeError("currency must be a three-letter ISO-4217 string")
        if (
            len(value) != _CURRENCY_CODE_LENGTH
            or not value.isalpha()
            or value != value.upper()
        ):
            raise ValueError(
                f"currency must be an uppercase ISO-4217 alpha code, got {value!r}"
            )
        return value

    @field_validator("minor_unit_exponent", mode="before")
    @classmethod
    def _validate_exponent(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("minor_unit_exponent must be an int")
        if value < 0 or value > _MAX_MINOR_UNIT_EXPONENT:
            raise ValueError(
                f"minor_unit_exponent must be between 0 and {_MAX_MINOR_UNIT_EXPONENT}, got {value}"
            )
        return value

    @model_validator(mode="after")
    def _validate_known_currency_exponent(self) -> Money:
        expected = KNOWN_MINOR_UNIT_EXPONENTS.get(self.currency)
        if expected is not None and self.minor_unit_exponent != expected:
            raise ValueError(
                f"{self.currency} requires minor_unit_exponent {expected}, "
                f"got {self.minor_unit_exponent}"
            )
        return self

    # -- pure arithmetic -------------------------------------------------

    def add(self, other: Money) -> Money:
        ensure_same_currency(self, other)
        return Money(
            amount_minor=self.amount_minor + other.amount_minor,
            currency=self.currency,
            minor_unit_exponent=self.minor_unit_exponent,
        )

    def subtract(self, other: Money) -> Money:
        ensure_same_currency(self, other)
        return Money(
            amount_minor=self.amount_minor - other.amount_minor,
            currency=self.currency,
            minor_unit_exponent=self.minor_unit_exponent,
        )

    def negate(self) -> Money:
        return Money(
            amount_minor=-self.amount_minor,
            currency=self.currency,
            minor_unit_exponent=self.minor_unit_exponent,
        )

    def is_zero(self) -> bool:
        return self.amount_minor == 0

    def is_positive(self) -> bool:
        return self.amount_minor > 0

    def as_minor_decimal(self) -> Decimal:
        """Return the amount in minor units as a Decimal.

        Ratios between two same-currency amounts cancel the minor-unit scale, so this
        is the exact operand used throughout :mod:`credit_engine.ratios`.
        """
        return Decimal(self.amount_minor)

    def zero_like(self) -> Money:
        return Money(
            amount_minor=0,
            currency=self.currency,
            minor_unit_exponent=self.minor_unit_exponent,
        )


def ensure_same_currency(*amounts: Money | None) -> str | None:
    """Verify that every supplied amount shares one currency and minor-unit scale.

    ``None`` entries are ignored so callers can pass optional inputs directly.
    Returns the shared currency code, or ``None`` when nothing was supplied.
    Raises :class:`CurrencyMismatchError` on any mismatch (methodology §1.1).
    """
    reference: Money | None = None
    for amount in amounts:
        if amount is None:
            continue
        if reference is None:
            reference = amount
            continue
        if amount.currency != reference.currency:
            raise CurrencyMismatchError(
                f"currency mismatch: {reference.currency} and {amount.currency}; "
                "multi-currency cases are unsupported in the MVP"
            )
        if amount.minor_unit_exponent != reference.minor_unit_exponent:
            raise CurrencyMismatchError(
                f"currency scale mismatch for {reference.currency}: exponent "
                f"{reference.minor_unit_exponent} and {amount.minor_unit_exponent}"
            )
    return None if reference is None else reference.currency


def money_sum(
    amounts: Iterable[Money | None], *, template: Money | None = None
) -> Money | None:
    """Sum same-currency amounts exactly.

    ``None`` entries are skipped. Returns ``None`` when nothing summable is supplied
    and no ``template`` is given to establish the currency.
    """
    present = [amount for amount in amounts if amount is not None]
    ensure_same_currency(*present, template)
    if not present:
        return None if template is None else template.zero_like()
    total = 0
    for amount in present:
        total += amount.amount_minor
    reference = present[0]
    return Money(
        amount_minor=total,
        currency=reference.currency,
        minor_unit_exponent=reference.minor_unit_exponent,
    )


def scale_money(amount: Money, factor: Decimal) -> Money:
    """Multiply an amount by a Decimal factor, rounding to whole minor units.

    Used for the §2.3 cash-availability factor. Rounding is ``ROUND_HALF_UP`` on the
    integer minor unit, consistent with the rounding rule recorded in
    ``excel/formulas/core.yaml``.
    """
    if not isinstance(factor, Decimal):
        raise TypeError("factor must be a Decimal; binary floating point is prohibited")
    with localcontext() as ctx:
        ctx.prec = ENGINE_PRECISION
        scaled = amount.as_minor_decimal() * factor
        rounded = scaled.quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return Money(
        amount_minor=int(rounded),
        currency=amount.currency,
        minor_unit_exponent=amount.minor_unit_exponent,
    )


def normalize_reported_amount(
    *,
    reported_value: Decimal | int,
    currency: str,
    minor_unit_exponent: int,
    reported_scale: int = 1,
) -> Money:
    """Convert a reported figure to exact integer minor units.

    Methodology §1.1: raw-file scale is applied exactly once. ``reported_scale`` is the
    multiplier implied by the source presentation (for example ``1_000`` for a
    statement reported in thousands). The result must land on a whole minor unit;
    a fractional result is a normalization error rather than something to round away.
    """
    if isinstance(reported_value, (bool, float)):
        raise TypeError(
            "reported_value must be a Decimal or int; binary floating point is prohibited"
        )
    if isinstance(reported_scale, bool) or not isinstance(reported_scale, int):
        raise TypeError("reported_scale must be an int multiplier")
    if reported_scale <= 0:
        raise ValueError(f"reported_scale must be positive, got {reported_scale}")

    with localcontext() as ctx:
        ctx.prec = ENGINE_PRECISION
        scaled = (
            Decimal(reported_value)
            * Decimal(reported_scale)
            * (Decimal(10) ** minor_unit_exponent)
        )
        if scaled != scaled.to_integral_value():
            raise ValueError(
                f"reported value {reported_value} at scale {reported_scale} does not "
                f"resolve to a whole minor unit for {currency}"
            )
        amount_minor = int(scaled)

    return Money(
        amount_minor=amount_minor,
        currency=currency,
        minor_unit_exponent=minor_unit_exponent,
    )
