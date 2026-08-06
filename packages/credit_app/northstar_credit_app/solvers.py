"""Deterministic bounded root solver used by every reverse-stress result."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from .models import MoneyValue, SolverResultView


def solve_reverse_stress(
    *,
    key: str,
    variable_solved: str,
    lower_bound: Decimal,
    upper_bound: Decimal,
    tolerance: Decimal,
    max_iterations: int,
    objective: Callable[[Decimal], Decimal | None],
    interpretation: str,
    result_multiplier: Decimal = Decimal(1),
    money_template: MoneyValue | None = None,
) -> SolverResultView:
    initial_lower = lower_bound
    initial_upper = upper_bound
    lower_value = objective(lower_bound)
    upper_value = objective(upper_bound)
    iterations = 0
    residual: Decimal | None = None
    converged = False
    failure_reason: str | None = None
    result_value: Decimal | None = None

    if lower_value is None or upper_value is None:
        failure_reason = (
            "The forecast metric is not numerically meaningful at a solver bound."
        )
    elif lower_value <= 0:
        converged = True
        residual = lower_value
        result_value = lower_bound
    elif upper_value > 0:
        residual = upper_value
        failure_reason = "The configured bounds do not bracket a policy breach."
    else:
        for iteration in range(1, max_iterations + 1):
            iterations = iteration
            midpoint = (lower_bound + upper_bound) / Decimal(2)
            midpoint_value = objective(midpoint)
            if midpoint_value is None:
                failure_reason = (
                    "The forecast metric became not meaningful during iteration."
                )
                break
            residual = midpoint_value
            if (
                abs(midpoint_value) <= tolerance
                or upper_bound - lower_bound <= tolerance
            ):
                converged = True
                result_value = midpoint
                break
            if midpoint_value > 0:
                lower_bound = midpoint
            else:
                upper_bound = midpoint
        if not converged and failure_reason is None:
            failure_reason = "The solver reached its iteration limit."

    displayed = None if result_value is None else result_value * result_multiplier
    result_money = None
    result = None
    if displayed is not None:
        if money_template is None:
            result = str(displayed.quantize(Decimal("0.01")))
        else:
            result_money = MoneyValue(
                amount_minor=int(displayed.quantize(Decimal(1))),
                currency=money_template.currency,
                minor_unit_exponent=money_template.minor_unit_exponent,
            )
    return SolverResultView(
        key=key,  # type: ignore[arg-type]
        variable_solved=variable_solved,
        lower_bound=str(initial_lower),
        upper_bound=str(initial_upper),
        tolerance=str(tolerance),
        iterations=iterations,
        residual=None
        if residual is None
        else str(residual.quantize(Decimal("0.0001"))),
        converged=converged,
        failure_reason=failure_reason,
        result=result,
        result_money=result_money,
        interpretation=interpretation,
    )
