"""Result and enumeration contracts.

Implements ``docs/methodology.md`` §1.3 (RatioResult, reason codes) and the
categorical confidence vocabulary of §13.

Pure module: no I/O, no framework, no float.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .money import Money

#: Display/scoring quantum required by methodology §1.2.
RATIO_QUANTUM = Decimal("0.0001")


class RatioStatus(str, Enum):
    """Outcome class of a metric evaluation (methodology §1.3)."""

    # Member names remain source-compatible with the original engine while the
    # serialized values implement the public v3 calculation-state contract.
    OK = "valid"
    NM = "not_meaningful"
    MISSING = "missing_input"
    ERROR = "invalid_denominator"
    BLOCKED = "blocked"
    POLICY_NOT_APPLICABLE = "policy_not_applicable"


class RatioReason(str, Enum):
    """Typed reason codes (methodology §1.3).

    The distinction between favorable and adverse "not meaningful" is deliberate:
    ``nm_no_obligation`` and ``nm_no_cash_interest`` are favorable, while
    ``nm_deferred_obligation`` and ``nm_negative_base`` are adverse. Collapsing them
    into a single NM state is the defect this vocabulary exists to prevent.
    """

    OK = "ok"
    NM_NO_CASH_INTEREST = "nm_no_cash_interest"
    NM_NO_CASH_BURN = "nm_no_cash_burn"
    NM_NO_OBLIGATION = "nm_no_obligation"
    NM_DEFERRED_OBLIGATION = "nm_deferred_obligation"
    NM_NEGATIVE_BASE = "nm_negative_base"
    NM_UNDEFINED = "nm_undefined"
    MISSING_INPUT = "missing_input"
    ERROR_INVALID_INPUT = "error_invalid_input"


#: Reason codes the methodology treats as favorable when they occur.
FAVORABLE_NM_REASONS = frozenset(
    {
        RatioReason.NM_NO_CASH_BURN,
        RatioReason.NM_NO_CASH_INTEREST,
        RatioReason.NM_NO_OBLIGATION,
    }
)

#: Reason codes the methodology treats as adverse when they occur.
ADVERSE_NM_REASONS = frozenset(
    {RatioReason.NM_DEFERRED_OBLIGATION, RatioReason.NM_NEGATIVE_BASE}
)


class ConfidenceLevel(str, Enum):
    """Categorical confidence (methodology §13). No numeric confidence is exposed."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class MetricComponent:
    """A named input that contributed to a metric, retained for explainability.

    Methodology §1.3 requires numerator/denominator components with source periods.
    """

    name: str
    value: Decimal | None
    currency: str | None = None
    period: str | None = None


@dataclass(frozen=True, slots=True)
class RatioResult:
    """A single ratio evaluation.

    ``value`` is quantized to four decimal places with ``ROUND_HALF_UP`` and is used
    for display and score banding. ``value_exact`` is the unquantized Decimal and is
    the operand for covenant pass/breach, headroom, and reverse-stress convergence
    (methodology §1.2, §1.3, §10).
    """

    metric_id: str
    status: RatioStatus
    reason_code: RatioReason
    value: Decimal | None = None
    value_exact: Decimal | None = None
    plain_label: str = ""
    professional_name: str = ""
    formula_id: str | None = None
    policy_ref: str | None = None
    components: tuple[MetricComponent, ...] = ()
    confidence: ConfidenceLevel | None = None
    confidence_factors: tuple[str, ...] = ()
    interpretation: str | None = None
    corrective_action: str | None = None

    @property
    def is_ok(self) -> bool:
        return self.status is RatioStatus.OK

    @property
    def is_favorable_nm(self) -> bool:
        return (
            self.status is RatioStatus.NM and self.reason_code in FAVORABLE_NM_REASONS
        )

    @property
    def is_adverse_nm(self) -> bool:
        return self.status is RatioStatus.NM and self.reason_code in ADVERSE_NM_REASONS


@dataclass(frozen=True, slots=True)
class MoneyMetricResult:
    """A metric whose result is a monetary amount rather than a ratio.

    Used for methodology §5.4 working capital, §5.7 cash plus undrawn revolver, and
    §5.8 sources versus uses.
    """

    metric_id: str
    status: RatioStatus
    reason_code: RatioReason
    value: Money | None = None
    plain_label: str = ""
    professional_name: str = ""
    formula_id: str | None = None
    components: tuple[MetricComponent, ...] = ()
    confidence: ConfidenceLevel | None = None
    confidence_factors: tuple[str, ...] = ()
    interpretation: str | None = None
    corrective_action: str | None = None

    @property
    def is_ok(self) -> bool:
        return self.status is RatioStatus.OK
