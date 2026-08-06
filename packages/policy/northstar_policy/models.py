"""Typed policy contract. Financial thresholds are data, not application constants."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScoreBand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    lower: Decimal | None = None
    upper: Decimal | None = None
    lower_inclusive: bool = True
    upper_inclusive: bool = False
    score: Decimal = Field(ge=0, le=100)
    label: str

    def matches(self, value: Decimal) -> bool:
        if self.lower is not None:
            if self.lower_inclusive and value < self.lower:
                return False
            if not self.lower_inclusive and value <= self.lower:
                return False
        if self.upper is not None:
            if self.upper_inclusive and value > self.upper:
                return False
            if not self.upper_inclusive and value >= self.upper:
                return False
        return True


class ScoreWeight(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str
    weight: Decimal = Field(gt=0, le=100)
    category: str


class CreditPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str
    name: str
    reporting_currency: str = "USD"
    maximum_leverage: Decimal
    minimum_dscr: Decimal
    minimum_interest_coverage: Decimal
    minimum_liquidity_minor: int
    maximum_maturity_months: int
    policy_capacity_minor: int
    minimum_data_confidence_score: int = Field(ge=0, le=100)
    maximum_ebitda_adjustment_pct: Decimal = Field(ge=0)
    maximum_eligible_grade: int = Field(ge=1, le=10)
    maximum_exposure_minor: int = Field(gt=0)
    minimum_collateral_coverage: Decimal = Field(ge=0)
    allowed_facility_types: list[str]
    grade_labels: dict[int, str]
    grade_bands: list[ScoreBand]
    leverage_bands: list[ScoreBand]
    coverage_bands: list[ScoreBand]
    dscr_bands: list[ScoreBand]
    weights: list[ScoreWeight]
    material_reweighting_pct: Decimal = Decimal("15")
    blocked_reweighting_pct: Decimal = Decimal("30")
    maximum_ar_advance_rate: Decimal = Field(ge=0, le=1)
    maximum_inventory_advance_rate: Decimal = Field(ge=0, le=1)
    facility_protection_weights: dict[str, Decimal]
    pricing_grade_spreads_bps: dict[int, int]
    pricing_tenor_adjustments_bps: dict[str, int]
    pricing_security_adjustments_bps: dict[str, int]
    pricing_amortization_adjustments_bps: dict[str, int]
    pricing_covenant_adjustment_bps: int
    pricing_concentration_adjustment_bps: int
    pricing_commitment_fee_bps: int
    pricing_upfront_fee_bps: int
    solver_tolerance: Decimal = Field(gt=0)
    solver_max_iterations: int = Field(gt=0, le=200)

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, value: list[ScoreWeight]) -> list[ScoreWeight]:
        total = sum((item.weight for item in value), Decimal(0))
        if total != Decimal(100):
            raise ValueError(f"score weights must sum to 100, got {total}")
        return value

    @field_validator("facility_protection_weights")
    @classmethod
    def validate_facility_weights(cls, value: dict[str, Decimal]) -> dict[str, Decimal]:
        if sum(value.values(), Decimal(0)) != Decimal(100):
            raise ValueError("facility protection weights must sum to 100")
        return value

    def score_for(self, metric: str, value: Decimal) -> tuple[Decimal, str]:
        table = {
            "leverage": self.leverage_bands,
            "coverage": self.coverage_bands,
            "dscr": self.dscr_bands,
        }[metric]
        for band in table:
            if band.matches(value):
                return band.score, band.label
        raise ValueError(f"no {metric} policy band matched {value}")

    def grade_for(self, score: Decimal) -> int:
        for band in self.grade_bands:
            if band.matches(score):
                return int(band.label)
        return 10
