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
    facility_type: Literal["term_loan", "revolver", "asset_based"] = "term_loan"
    security_type: Literal["unsecured", "secured", "asset_based"] = "secured"
    rate_type: Literal["fixed", "floating"] = "fixed"
    base_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    rate_floor: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    amortization_years: int | None = Field(default=None, gt=0, le=30)
    guarantee: str = "None"
    primary_repayment_source: str = "Operating cash flow"


class DebtInstrumentInput(ContractModel):
    name: str
    principal: MoneyValue
    annual_rate: Decimal = Field(ge=0, le=1)
    rate_type: Literal["fixed", "floating"] = "fixed"
    spread: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    rate_floor: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    scheduled_amortization: MoneyValue
    maturity_year: int = Field(default=3, ge=1, le=30)
    secured: bool = False
    seniority: str = "Senior"
    collateral: str = "None"


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
    tax_rate: Decimal = Field(default=Decimal("0.12"), ge=0, le=1)


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
    subsequent_growth: Decimal = Decimal("0")
    ebitda_margin_change: Decimal
    rate_shock: Decimal
    working_capital_pct_revenue: Decimal = Field(ge=0, le=1)
    maintenance_capex_pct_revenue: Decimal = Field(ge=0, le=1)


class CaseInput(ContractModel):
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    borrower: BorrowerInput
    request: LoanRequestInput
    financials: FinancialInput
    business_risk: BusinessRiskInput
    debt_instruments: list[DebtInstrumentInput] = Field(default_factory=list)
    scenarios: dict[Literal["base", "downside", "severe"], ScenarioInput]
    data_as_of: str

    @model_validator(mode="after")
    def validate_scenarios(self) -> CaseInput:
        if set(self.scenarios) != {"base", "downside", "severe"}:
            raise ValueError("base, downside, and severe scenarios are required")
        currencies: set[str] = set()

        def collect(value: object) -> None:
            if isinstance(value, dict):
                if "amount_minor" in value and "currency" in value:
                    currencies.add(str(value["currency"]))
                for nested in value.values():
                    collect(nested)
            elif isinstance(value, list):
                for nested in value:
                    collect(nested)

        collect(self.model_dump(mode="python"))
        if len(currencies) > 1:
            raise ValueError(
                "currency mismatch: all monetary inputs must use one reporting currency"
            )
        return self


class RatioView(ContractModel):
    metric_id: str
    status: str
    value: str | None
    reason_code: str
    label: str
    plain_label: str
    formula_id: str | None = None
    policy_ref: str | None = None
    direction: Literal["higher_is_better", "lower_is_better", "neutral"] = "neutral"
    source_period: str | None = None
    components: list[dict[str, str | None]] = Field(default_factory=list)
    model_version: str


class CapacityConstraintView(ContractModel):
    key: str
    label: str
    amount: MoneyValue | None
    applicable: bool
    status: Literal["valid", "blocked", "policy_not_applicable"]
    reason: str
    policy_ref: str | None = None
    binding: bool = False


class CapacityView(ContractModel):
    requested: MoneyValue
    leverage: MoneyValue
    dscr: MoneyValue
    collateral: MoneyValue | None
    policy: MoneyValue
    recommended: MoneyValue
    binding_constraints: list[str]
    constraints: list[CapacityConstraintView]


class ScoreComponentView(ContractModel):
    key: str
    score: str
    weight: str
    contribution: str
    band: str
    status: Literal["valid", "adverse", "blocked"] = "valid"
    evidence: str = "Calculated from supplied synthetic inputs"


class ScorecardView(ContractModel):
    score: str | None
    grade: int | None
    grade_label: str
    components: list[ScoreComponentView]
    confidence: Literal["high", "medium", "low", "blocked"]
    confidence_score: int
    confidence_drivers: list[str]
    confidence_penalties: list[str]
    improvement_actions: list[str]
    synthetic_notice: str = (
        "Synthetic demonstration — not a real data-quality assessment"
    )


class ScenarioYearView(ContractModel):
    year: int
    revenue: MoneyValue
    adjusted_ebitda: MoneyValue
    cfads: MoneyValue
    ending_debt: MoneyValue
    beginning_debt: MoneyValue
    new_facility: MoneyValue
    scheduled_amortization: MoneyValue
    optional_paydown: MoneyValue
    average_debt: MoneyValue
    ending_cash: MoneyValue
    cash_shortfall: MoneyValue
    revolver_draw: MoneyValue
    refinancing_need: MoneyValue
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
    frequency: Literal["monthly", "quarterly", "annual"] = "quarterly"
    rationale: str = "Protects debt repayment capacity"
    cure: str = "Equity cure or lender waiver subject to policy"
    covenant_type: Literal["maintenance", "incurrence", "reporting"] = "maintenance"


class PolicyCheckView(ContractModel):
    key: str
    label: str
    status: Literal["pass", "warning", "hard_stop", "not_applicable"]
    severity: Literal["informational", "warning", "hard_stop"]
    actual: str
    threshold: str
    exception_allowed: bool
    remediation: str
    required_approval: str = "Credit officer"
    decision_impact: str = "Informational"


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
    facility_type: str
    maturity_years: int
    amortization_years: int
    collateral: str
    guarantee: str
    monitoring: list[str]
    policy_exceptions: list[str]
    decision_priority: str


class ReverseStressView(ContractModel):
    dscr_minimum_revenue_decline: str
    leverage_breach_margin_decline: str
    maximum_downside_loan: MoneyValue
    converged: bool
    method: Literal["bounded_bisection"] = "bounded_bisection"
    iterations: int
    tolerance: str
    residual: str
    lower_bound: str
    upper_bound: str
    interpretation: str


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
    policy_checks: list[PolicyCheckView]
    reverse_stress: ReverseStressView
    decision: DecisionView
    memo_sections: dict[str, list[str]]
    analysis_status: Literal["final", "blocked"] = "final"
