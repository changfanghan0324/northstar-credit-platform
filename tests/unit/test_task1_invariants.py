from __future__ import annotations

from credit_engine.money import Money
from credit_engine.ratios import (
    debt_service_coverage,
    gross_debt_to_ebitda,
    interest_coverage,
)
from credit_engine.types import RatioStatus


def usd_millions(value: int) -> Money:
    return Money(
        amount_minor=value * 100_000_000, currency="USD", minor_unit_exponent=2
    )


def test_lower_ebitda_never_improves_leverage() -> None:
    stronger = gross_debt_to_ebitda(usd_millions(60), usd_millions(30))
    weaker = gross_debt_to_ebitda(usd_millions(60), usd_millions(20))
    assert stronger.status is weaker.status is RatioStatus.OK
    assert weaker.value > stronger.value


def test_higher_debt_never_improves_leverage() -> None:
    lower = gross_debt_to_ebitda(usd_millions(50), usd_millions(25))
    higher = gross_debt_to_ebitda(usd_millions(75), usd_millions(25))
    assert lower.status is higher.status is RatioStatus.OK
    assert higher.value > lower.value


def test_lower_ebitda_never_improves_interest_coverage() -> None:
    stronger = interest_coverage(usd_millions(30), usd_millions(5), False)
    weaker = interest_coverage(usd_millions(20), usd_millions(5), False)
    assert stronger.status is weaker.status is RatioStatus.OK
    assert weaker.value < stronger.value


def test_higher_interest_never_improves_coverage() -> None:
    lower = interest_coverage(usd_millions(30), usd_millions(5), False)
    higher = interest_coverage(usd_millions(30), usd_millions(8), False)
    assert lower.status is higher.status is RatioStatus.OK
    assert higher.value < lower.value


def test_higher_principal_service_never_improves_dscr() -> None:
    lower = debt_service_coverage(
        usd_millions(24), usd_millions(12), True, usd_millions(10)
    )
    higher = debt_service_coverage(
        usd_millions(24), usd_millions(15), True, usd_millions(10)
    )
    assert lower.status is higher.status is RatioStatus.OK
    assert higher.value < lower.value


# Remaining master-prompt §42 invariants belong to later score, scenario,
# decision, memo, and Excel modules and are gated in the full verify script.
