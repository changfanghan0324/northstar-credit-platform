"""Typed request and response contracts for a Northstar credit case."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from credit_engine import Money
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MoneyValue(ContractModel):
    amount_minor: int = Field(
        ge=-9_007_199_254_740_991,
        le=9_007_199_254_740_991,
        description="Exact signed minor units within JavaScript's safe-integer range.",
    )
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    minor_unit_exponent: int = Field(default=2, ge=0, le=6)

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


class IncomeStatementPeriodInput(ContractModel):
    revenue: MoneyValue | None = None
    cogs: MoneyValue | None = None
    gross_profit: MoneyValue | None = None
    operating_expenses: MoneyValue | None = None
    ebitda: MoneyValue | None = None
    depreciation_amortization: MoneyValue | None = None
    ebit: MoneyValue | None = None
    cash_interest: MoneyValue | None = None
    pretax_income: MoneyValue | None = None
    cash_taxes: MoneyValue | None = None
    net_income: MoneyValue | None = None


class BalanceSheetPeriodInput(ContractModel):
    cash: MoneyValue | None = None
    restricted_cash: MoneyValue | None = None
    accounts_receivable: MoneyValue | None = None
    inventory: MoneyValue | None = None
    current_assets: MoneyValue | None = None
    ppe: MoneyValue | None = None
    goodwill: MoneyValue | None = None
    intangible_assets: MoneyValue | None = None
    total_assets: MoneyValue | None = None
    accounts_payable: MoneyValue | None = None
    current_liabilities: MoneyValue | None = None
    short_term_debt: MoneyValue | None = None
    current_maturities: MoneyValue | None = None
    long_term_debt: MoneyValue | None = None
    lease_liabilities: MoneyValue | None = None
    total_liabilities: MoneyValue | None = None
    equity: MoneyValue | None = None


class CashFlowPeriodInput(ContractModel):
    operating_cash_flow: MoneyValue | None = None
    working_capital_change: MoneyValue | None = None
    capital_expenditures: MoneyValue | None = None
    maintenance_capex: MoneyValue | None = None
    acquisitions: MoneyValue | None = None
    asset_sales: MoneyValue | None = None
    dividends: MoneyValue | None = None
    share_repurchases: MoneyValue | None = None
    debt_issued: MoneyValue | None = None
    debt_repaid: MoneyValue | None = None
    free_cash_flow: MoneyValue | None = None


class FinancialPeriodInput(ContractModel):
    id: str
    label: str
    period_type: Literal["historical_fiscal_year", "quarter", "ytd", "ltm", "forecast"]
    start_date: date
    end_date: date
    fiscal_year: int
    fiscal_quarter: int | None = Field(default=None, ge=1, le=4)
    audited: bool = False
    source_type: Literal["audited", "reviewed", "management", "derived", "forecast"]
    source_reference: str
    currency: str = "USD"
    scale: Literal["whole", "thousands", "millions"] = "whole"
    income_statement: IncomeStatementPeriodInput = Field(
        default_factory=IncomeStatementPeriodInput
    )
    balance_sheet: BalanceSheetPeriodInput = Field(
        default_factory=BalanceSheetPeriodInput
    )
    cash_flow: CashFlowPeriodInput = Field(default_factory=CashFlowPeriodInput)

    @model_validator(mode="after")
    def validate_dates_and_source(self) -> FinancialPeriodInput:
        if self.end_date < self.start_date:
            raise ValueError("financial period end_date must not precede start_date")
        if not self.source_reference.strip():
            raise ValueError("financial period source_reference is required")
        return self


class FinancialSpreadInput(ContractModel):
    periods: list[FinancialPeriodInput] = Field(default_factory=list)
    selected_ltm_method: (
        Literal[
            "fiscal_year_plus_current_ytd_minus_prior_ytd",
            "latest_four_quarters",
            "reported_ltm",
        ]
        | None
    ) = None

    @model_validator(mode="after")
    def validate_periods(self) -> FinancialSpreadInput:
        ids = [period.id for period in self.periods]
        if len(ids) != len(set(ids)):
            raise ValueError("financial period ids must be unique")
        quarters = [
            period for period in self.periods if period.period_type == "quarter"
        ]
        for index, first in enumerate(quarters):
            for second in quarters[index + 1 :]:
                if max(first.start_date, second.start_date) <= min(
                    first.end_date, second.end_date
                ):
                    raise ValueError("financial quarter periods must not overlap")
        return self


class NormalizationAdjustmentInput(ContractModel):
    id: str
    name: str
    period_id: str
    category: Literal[
        "restructuring",
        "litigation",
        "impairment",
        "acquisition_related",
        "asset_sale_gain",
        "one_time_compensation",
        "government_support",
        "related_party",
        "owner_compensation",
        "other",
    ]
    amount: MoneyValue
    direction: Literal["positive", "negative"]
    cash_classification: Literal["cash", "noncash"]
    recurrence: Literal["recurring", "nonrecurring"]
    ebitda_impact: MoneyValue
    ebit_impact: MoneyValue
    cfads_impact: MoneyValue
    supporting_evidence: str
    source_reference: str
    analyst_rationale: str
    approval_status: Literal["draft", "pending", "approved", "rejected"] = "draft"
    reviewer: str | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_support(self) -> NormalizationAdjustmentInput:
        if not self.analyst_rationale.strip():
            raise ValueError("adjustment rationale is required")
        if self.approval_status == "approved" and not self.supporting_evidence.strip():
            raise ValueError("approved adjustment requires supporting evidence")
        return self


class BusinessRiskEvidenceInput(ContractModel):
    score: Decimal = Field(ge=0, le=100)
    band: Literal["strong", "adequate", "moderate_concern", "weak", "severe_concern"]
    evidence: str
    source: str
    analyst_rationale: str
    confidence: Literal["high", "medium", "low"]
    override_status: Literal["none", "pending", "approved", "rejected"] = "none"
    reviewer_status: Literal["unreviewed", "reviewed", "challenged"] = "unreviewed"
    last_updated: datetime

    @model_validator(mode="after")
    def validate_evidence(self) -> BusinessRiskEvidenceInput:
        if not self.evidence.strip() or not self.analyst_rationale.strip():
            raise ValueError("business-risk evidence and rationale are required")
        return self


class AccountsReceivableBaseInput(ContractModel):
    gross_receivables: MoneyValue
    ineligible_receivables: MoneyValue
    past_due_receivables: MoneyValue
    cross_aged_receivables: MoneyValue
    foreign_receivables: MoneyValue
    concentration_reserve: MoneyValue
    dilution_reserve: MoneyValue
    advance_rate: Decimal = Field(ge=0, le=1)


class InventoryBaseInput(ContractModel):
    gross_inventory: MoneyValue
    ineligible_inventory: MoneyValue
    obsolete_inventory: MoneyValue
    advance_rate: Decimal = Field(ge=0, le=1)
    inventory_cap: MoneyValue


class OtherCollateralInput(ContractModel):
    equipment: MoneyValue
    real_estate: MoneyValue
    cash: MoneyValue
    other: MoneyValue


class BorrowingBaseInput(ContractModel):
    accounts_receivable: AccountsReceivableBaseInput
    inventory: InventoryBaseInput
    other_collateral: OtherCollateralInput
    additional_reserves: MoneyValue
    prior_liens: MoneyValue


class PricingInput(ContractModel):
    reference_base_rate: Decimal = Field(ge=0, le=1)
    relationship_adjustment_bps: int = Field(default=0, ge=-200, le=200)
    include_upfront_fee: bool = False


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
    factor_evidence: dict[
        Literal[
            "industry",
            "competitive_position",
            "customer_concentration",
            "diversification",
            "management_policy",
            "governance_event",
        ],
        BusinessRiskEvidenceInput,
    ] = Field(default_factory=dict)


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
    financial_spread: FinancialSpreadInput = Field(default_factory=FinancialSpreadInput)
    normalization_adjustments: list[NormalizationAdjustmentInput] = Field(
        default_factory=list
    )
    borrowing_base: BorrowingBaseInput | None = None
    pricing: PricingInput = Field(
        default_factory=lambda: PricingInput(reference_base_rate=Decimal("0.04"))
    )
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


class FinancialSpreadingView(ContractModel):
    periods: list[FinancialPeriodInput]
    historical_years: int
    forecast_years: int
    selected_ltm_method: str | None
    ltm_period_id: str | None
    ltm_status: Literal["available", "blocked", "legacy_snapshot"]
    reconciliation_warnings: list[str]
    trend: dict[str, list[str | None]]


class AdjustmentSummaryView(ContractModel):
    entries: list[NormalizationAdjustmentInput]
    reported_ebitda: MoneyValue
    approved_adjustment: MoneyValue
    adjusted_ebitda: MoneyValue
    positive_adjustment_pct: str
    warning: str | None
    leverage_before: str | None
    leverage_after: str | None
    dscr_before: str | None
    dscr_after: str | None


class FacilityProtectionView(ContractModel):
    score: str
    category: Literal["strong", "adequate", "moderate", "weak", "severe"]
    expected_recovery_category: Literal["high", "moderate", "limited", "low"]
    factors: dict[str, str]
    main_protections: list[str]
    main_structural_weaknesses: list[str]
    required_improvements: list[str]
    documentation_requirements: list[str]


class BorrowingBaseView(ContractModel):
    applicable: bool
    status: Literal["calculated", "blocked", "not_applicable", "legacy_manual"]
    gross_collateral: MoneyValue | None
    eligibility_reductions: MoneyValue | None
    eligible_receivables: MoneyValue | None
    receivables_availability: MoneyValue | None
    eligible_inventory: MoneyValue | None
    inventory_availability: MoneyValue | None
    other_eligible_collateral: MoneyValue | None
    reserves: MoneyValue | None
    prior_liens: MoneyValue | None
    borrowing_base: MoneyValue | None
    availability: MoneyValue | None
    excess_or_deficiency: MoneyValue | None
    binding_constraint: str
    policy_notice: str


class PricingView(ContractModel):
    reference_base_rate: str
    risk_grade_spread_bps: int
    tenor_adjustment_bps: int
    security_adjustment_bps: int
    amortization_adjustment_bps: int
    covenant_adjustment_bps: int
    concentration_adjustment_bps: int
    relationship_adjustment_bps: int
    indicative_all_in_rate: str
    commitment_fee_bps: int | None
    upfront_fee_bps: int | None
    disclaimer: str


class SolverResultView(ContractModel):
    key: Literal[
        "revenue_dscr",
        "margin_leverage",
        "rate_coverage",
        "working_capital_liquidity",
        "maximum_downside_loan",
        "maximum_severe_liquidity_loan",
    ]
    variable_solved: str
    lower_bound: str
    upper_bound: str
    tolerance: str
    iterations: int
    residual: str | None
    converged: bool
    failure_reason: str | None
    result: str | None
    result_money: MoneyValue | None = None
    interpretation: str


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
    revolver_remaining: MoneyValue
    refinancing_need: MoneyValue
    unpaid_debt_service: MoneyValue
    leverage: str | None
    leverage_status: str
    leverage_reason_code: str
    interest_coverage: str | None
    interest_coverage_status: str
    interest_coverage_reason_code: str
    dscr: str | None
    dscr_status: str
    dscr_reason_code: str
    covenant_status: Literal["pass", "breach", "not_applicable", "blocked"]
    liquidity_status: Literal["adequate", "shortfall"]
    refinancing_status: Literal["none", "required"]
    debt_service_status: Literal["paid", "unpaid"]
    revolver_status: Literal["available", "exhausted", "not_applicable"]


class ScenarioView(ContractModel):
    name: Literal["base", "downside", "severe"]
    years: list[ScenarioYearView]
    first_breach_year: int | None
    first_stress_event_year: int | None
    liquidity_exhaustion_year: int | None


class CovenantView(ContractModel):
    name: str
    threshold: str
    actual: str
    headroom: str
    status: Literal["pass", "breach", "not_applicable", "blocked"]
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
    dscr_minimum_revenue_decline: str | None
    leverage_breach_margin_decline: str | None
    maximum_downside_loan: MoneyValue | None
    converged: bool
    method: Literal["bounded_bisection"] = "bounded_bisection"
    iterations: int
    tolerance: str
    residual: str
    lower_bound: str
    upper_bound: str
    interpretation: str
    failure_reason: str | None = None
    solvers: list[SolverResultView] = Field(default_factory=list)


class AnalysisResult(ContractModel):
    case: CaseInput
    policy_version: str
    policy_hash: str
    engine_version: str
    input_hash: str
    calculated_at: str
    metrics: dict[str, RatioView]
    financial_spreading: FinancialSpreadingView
    adjustments: AdjustmentSummaryView
    capacity: CapacityView
    facility_protection: FacilityProtectionView
    borrowing_base: BorrowingBaseView
    pricing: PricingView
    scorecard: ScorecardView
    scenarios: list[ScenarioView]
    covenants: list[CovenantView]
    policy_checks: list[PolicyCheckView]
    reverse_stress: ReverseStressView
    decision: DecisionView
    memo_sections: dict[str, list[str]]
    analysis_status: Literal["final", "blocked"] = "final"
