"""Typed request and response contracts for a Northstar credit case."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from credit_engine import Money
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MoneyValue(ContractModel):
    amount_minor: int
    currency: str = "USD"
    minor_unit_exponent: int = 2

    def engine(self) -> Money:
        return Money(
            amount_minor=self.amount_minor,
            currency=self.currency,
            minor_unit_exponent=self.minor_unit_exponent,
        )


class BorrowerInput(ContractModel):
    legal_name: str
    industry: str
    headquarters: str
    description: str


class LoanRequestInput(ContractModel):
    amount: MoneyValue
    purpose: str
    annual_rate: Decimal = Field(gt=0, le=1)
    maturity_years: int = Field(gt=0, le=30)


class FinancialInput(ContractModel):
    revenue: MoneyValue
    prior_revenue: MoneyValue
    ebit: MoneyValue
    depreciation_amortization: MoneyValue
    positive_ebitda_adjustments: MoneyValue
    negative_ebitda_adjustments: MoneyValue
    prior_adjusted_ebitda: MoneyValue
    cfo: MoneyValue
    capex: MoneyValue
    maintenance_capex: MoneyValue
    cash_taxes: MoneyValue
    working_capital_increase: MoneyValue
    mandatory_pension: MoneyValue
    cash_interest: MoneyValue
    scheduled_principal: MoneyValue
    short_term_borrowings: MoneyValue
    current_maturities: MoneyValue
    long_term_debt: MoneyValue
    finance_leases: MoneyValue
    unrestricted_cash: MoneyValue
    cash_availability_factor: Decimal = Field(ge=0, le=1)
    current_assets: MoneyValue
    current_liabilities: MoneyValue
    accounts_receivable: MoneyValue
    inventory: MoneyValue
    other_current_assets: MoneyValue
    undrawn_revolver: MoneyValue
    minimum_operating_cash: MoneyValue
    monthly_stressed_cash_burn: MoneyValue
    equity: MoneyValue
    total_liabilities: MoneyValue
    total_assets: MoneyValue
    secured_debt: MoneyValue
    contractual_rent: MoneyValue
    net_income: MoneyValue
    collateral_capacity: MoneyValue


class BusinessRiskInput(ContractModel):
    industry: Decimal = Field(ge=0, le=100)
    competitive_position: Decimal = Field(ge=0, le=100)
    customer_concentration: Decimal = Field(ge=0, le=100)
    diversification: Decimal = Field(ge=0, le=100)
    management_policy: Decimal = Field(ge=0, le=100)
    governance_event: Decimal = Field(ge=0, le=100)
    strengths: list[str]
    risks: list[str]


class ScenarioInput(ContractModel):
    revenue_growth: Decimal
    ebitda_margin_change: Decimal
    rate_shock: Decimal
    working_capital_pct_revenue: Decimal = Field(ge=0, le=1)
    maintenance_capex_pct_revenue: Decimal = Field(ge=0, le=1)


class CaseInput(ContractModel):
    slug: str
    borrower: BorrowerInput
    request: LoanRequestInput
    financials: FinancialInput
    business_risk: BusinessRiskInput
    scenarios: dict[Literal["base", "downside", "severe"], ScenarioInput]
    data_as_of: str

    @model_validator(mode="after")
    def validate_scenarios(self) -> CaseInput:
        if set(self.scenarios) != {"base", "downside", "severe"}:
            raise ValueError("base, downside, and severe scenarios are required")
        return self


class RatioView(ContractModel):
    metric_id: str
    status: str
    value: str | None
    reason_code: str
    label: str


class CapacityView(ContractModel):
    requested: MoneyValue
    leverage: MoneyValue
    dscr: MoneyValue
    collateral: MoneyValue
    policy: MoneyValue
    recommended: MoneyValue
    binding_constraints: list[str]


class ScoreComponentView(ContractModel):
    key: str
    score: str
    weight: str
    contribution: str
    band: str


class ScorecardView(ContractModel):
    score: str
    grade: int
    grade_label: str
    components: list[ScoreComponentView]
    confidence: Literal["high", "medium", "low", "blocked"]


class ScenarioYearView(ContractModel):
    year: int
    revenue: MoneyValue
    adjusted_ebitda: MoneyValue
    cfads: MoneyValue
    ending_debt: MoneyValue
    ending_cash: MoneyValue
    leverage: str
    interest_coverage: str
    dscr: str
    covenant_status: Literal["pass", "breach"]


class ScenarioView(ContractModel):
    name: Literal["base", "downside", "severe"]
    years: list[ScenarioYearView]
    first_breach_year: int | None


class CovenantView(ContractModel):
    name: str
    threshold: str
    actual: str
    headroom: str
    status: Literal["pass", "breach"]
    scenario: str
    year: int


class DecisionView(ContractModel):
    outcome: Literal[
        "Approve",
        "Approve with conditions",
        "Reduce requested amount",
        "Refer to credit committee",
        "Decline",
    ]
    rationale: list[str]
    conditions: list[str]
    primary_repayment_source: str
    secondary_repayment_source: str


class ReverseStressView(ContractModel):
    dscr_minimum_revenue_decline: str
    leverage_breach_margin_decline: str
    maximum_downside_loan: MoneyValue
    converged: bool


class AnalysisResult(ContractModel):
    case: CaseInput
    policy_version: str
    policy_hash: str
    engine_version: str
    input_hash: str
    calculated_at: str
    metrics: dict[str, RatioView]
    capacity: CapacityView
    scorecard: ScorecardView
    scenarios: list[ScenarioView]
    covenants: list[CovenantView]
    reverse_stress: ReverseStressView
    decision: DecisionView
    memo_sections: dict[str, list[str]]
