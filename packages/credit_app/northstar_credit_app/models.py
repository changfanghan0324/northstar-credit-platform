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
    model_config = ConfigDict(extra="forbid", frozen=True)
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


SourceAuthority = Literal[
    "period_spread",
    "debt_schedule",
    "facility_request",
    "manual_legacy_snapshot",
    "calculated",
    "defaulted",
    "blocked",
]

ProvenanceSource = Literal[
    "template-derived",
    "user-entered",
    "calculated",
    "imported",
    "override",
]

DebtSource = Literal[
    "balance_sheet_aggregate",
    "instrument_schedule",
    "partial_schedule_with_residual",
    "blocked_mismatch",
]


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
    amortization_type: (
        Literal["fully_amortizing", "partial", "bullet", "revolver"] | None
    ) = None
    bullet_percentage: Decimal = Field(default=Decimal("1"), ge=0, le=1)
    initial_drawn_amount: MoneyValue | None = None
    commitment_fee_bps: int = Field(default=0, ge=0, le=2_000)
    upfront_fee_bps: int = Field(default=0, ge=0, le=2_000)
    availability_period_years: int | None = Field(default=None, gt=0, le=30)
    mandatory_prepayment: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    guarantee: str = "None"
    primary_repayment_source: str = "Operating cash flow"

    @model_validator(mode="after")
    def validate_mechanics(self) -> LoanRequestInput:
        if self.initial_drawn_amount is not None:
            if self.initial_drawn_amount.currency != self.amount.currency:
                raise ValueError("initial drawn amount must use the facility currency")
            if self.initial_drawn_amount.amount_minor > self.amount.amount_minor:
                raise ValueError("initial drawn amount cannot exceed commitment amount")
        if self.facility_type == "revolver" and self.amortization_type not in {
            None,
            "revolver",
        }:
            raise ValueError(
                "revolver facilities require revolver amortization mechanics"
            )
        if (
            self.amortization_type == "fully_amortizing"
            and self.amortization_years is None
        ):
            raise ValueError("fully amortizing facilities require amortization_years")
        if self.amortization_type == "bullet" and self.amortization_years is not None:
            raise ValueError(
                "bullet facilities cannot specify scheduled amortization_years"
            )
        if self.amortization_type == "bullet" and self.bullet_percentage <= 0:
            raise ValueError("bullet facilities require a positive bullet percentage")
        return self


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
    schedule_completeness: Literal["complete", "partial", "unspecified"] = "unspecified"

    @model_validator(mode="after")
    def validate_debt(self) -> DebtInstrumentInput:
        if (
            self.principal.amount_minor < 0
            or self.scheduled_amortization.amount_minor < 0
        ):
            raise ValueError(
                "debt principal and scheduled amortization must be nonnegative"
            )
        if self.scheduled_amortization.amount_minor > self.principal.amount_minor:
            raise ValueError(
                "scheduled amortization cannot exceed instrument principal"
            )
        return self


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
    flow_type: Literal["discrete", "cumulative", "point_in_time"] = "discrete"
    entity_scope: str = "borrower_consolidated"
    accounting_basis: Literal["gaap", "ifrs", "tax", "management", "unknown"] = (
        "management"
    )
    fiscal_calendar: Literal["calendar", "52_week", "53_week", "custom"] = "calendar"
    mapping_version: str = "default"
    restated: bool = False
    pro_forma: bool = False
    filing_date: date | None = None
    amendment_flag: bool = False
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
        if self.period_type == "quarter" and self.fiscal_quarter is None:
            raise ValueError("quarter periods require fiscal_quarter metadata")
        if (
            self.period_type in {"historical_fiscal_year", "quarter", "ltm"}
            and self.flow_type == "cumulative"
        ):
            raise ValueError(
                "annual, quarter, and reported LTM periods must use discrete flow_type"
            )
        if (
            self.period_type in {"ytd", "forecast"}
            and self.flow_type == "point_in_time"
        ):
            raise ValueError(
                "YTD and forecast periods cannot use point_in_time flow_type"
            )
        if self.period_type == "forecast" and self.source_type != "forecast":
            raise ValueError("forecast periods require source_type=forecast")
        if self.period_type != "forecast" and self.source_type == "forecast":
            raise ValueError("forecast source_type requires period_type=forecast")
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
        keyed: dict[tuple[str, int, int | None], list[FinancialPeriodInput]] = {}
        for period in self.periods:
            if period.period_type in {"historical_fiscal_year", "quarter", "ytd"}:
                key = (period.period_type, period.fiscal_year, period.fiscal_quarter)
                keyed.setdefault(key, []).append(period)
        if any(
            len(items) > 1
            and not any(item.restated or item.amendment_flag for item in items)
            for items in keyed.values()
        ):
            raise ValueError("financial periods must not duplicate fiscal metadata")
        quarters = [
            period for period in self.periods if period.period_type == "quarter"
        ]
        for index, first in enumerate(quarters):
            for second in quarters[index + 1 :]:
                same_key = (
                    first.fiscal_year == second.fiscal_year
                    and first.fiscal_quarter == second.fiscal_quarter
                )
                if max(first.start_date, second.start_date) <= min(
                    first.end_date, second.end_date
                ) and not (
                    same_key
                    and (
                        first.restated
                        or second.restated
                        or first.amendment_flag
                        or second.amendment_flag
                    )
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
        if self.amount.amount_minor < 0:
            raise ValueError(
                "adjustment amount must be nonnegative; direction carries the sign"
            )
        if not self.analyst_rationale.strip():
            raise ValueError("adjustment rationale is required")
        if not self.source_reference.strip():
            raise ValueError("adjustment source reference is required")
        impacts = (self.ebitda_impact, self.ebit_impact, self.cfads_impact)
        if any(value.amount_minor < 0 for value in impacts):
            raise ValueError(
                "adjustment impacts must be nonnegative; direction carries the sign"
            )
        if any(value.amount_minor > self.amount.amount_minor for value in impacts):
            raise ValueError("adjustment impacts cannot exceed the supported amount")
        if self.approval_status == "approved" and (
            not self.supporting_evidence.strip() or not self.reviewer
        ):
            raise ValueError(
                "approved adjustment requires supporting evidence and reviewer"
            )
        if self.recurrence == "recurring" and self.approval_status == "approved":
            raise ValueError(
                "recurring adjustments cannot be approved as one-time add-backs"
            )
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
        if not self.source.strip():
            raise ValueError("business-risk evidence source is required")
        expected_band = (
            "strong"
            if self.score >= 80
            else "adequate"
            if self.score >= 65
            else "moderate_concern"
            if self.score >= 50
            else "weak"
            if self.score >= 35
            else "severe_concern"
        )
        if self.band != expected_band:
            raise ValueError("business-risk score and band are inconsistent")
        if self.override_status == "approved" and self.reviewer_status != "reviewed":
            raise ValueError("approved business-risk override requires reviewed status")
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

    @model_validator(mode="after")
    def validate_collateral(self) -> AccountsReceivableBaseInput:
        values = {
            "gross_receivables": self.gross_receivables,
            "ineligible_receivables": self.ineligible_receivables,
            "past_due_receivables": self.past_due_receivables,
            "cross_aged_receivables": self.cross_aged_receivables,
            "foreign_receivables": self.foreign_receivables,
            "concentration_reserve": self.concentration_reserve,
            "dilution_reserve": self.dilution_reserve,
        }
        if any(value.amount_minor < 0 for value in values.values()):
            raise ValueError(
                "borrowing-base receivables and reserves must be nonnegative"
            )
        deductions = sum(
            values[name].amount_minor
            for name in (
                "ineligible_receivables",
                "past_due_receivables",
                "cross_aged_receivables",
                "foreign_receivables",
                "concentration_reserve",
                "dilution_reserve",
            )
        )
        if deductions > self.gross_receivables.amount_minor:
            raise ValueError("receivable deductions cannot exceed gross receivables")
        return self


class InventoryBaseInput(ContractModel):
    gross_inventory: MoneyValue
    ineligible_inventory: MoneyValue
    obsolete_inventory: MoneyValue
    advance_rate: Decimal = Field(ge=0, le=1)
    inventory_cap: MoneyValue

    @model_validator(mode="after")
    def validate_collateral(self) -> InventoryBaseInput:
        values = (
            self.gross_inventory,
            self.ineligible_inventory,
            self.obsolete_inventory,
            self.inventory_cap,
        )
        if any(value.amount_minor < 0 for value in values):
            raise ValueError("borrowing-base inventory and cap must be nonnegative")
        if (
            self.ineligible_inventory.amount_minor
            + self.obsolete_inventory.amount_minor
            > self.gross_inventory.amount_minor
        ):
            raise ValueError("inventory deductions cannot exceed gross inventory")
        return self


class OtherCollateralInput(ContractModel):
    equipment: MoneyValue
    real_estate: MoneyValue
    cash: MoneyValue
    other: MoneyValue
    equipment_advance_rate: Decimal = Field(default=Decimal("1.00"), ge=0, le=1)
    real_estate_advance_rate: Decimal = Field(default=Decimal("0.50"), ge=0, le=1)
    cash_advance_rate: Decimal = Field(default=Decimal("0.95"), ge=0, le=1)
    other_advance_rate: Decimal = Field(default=Decimal("0.25"), ge=0, le=1)

    @model_validator(mode="after")
    def validate_collateral(self) -> OtherCollateralInput:
        if any(
            value.amount_minor < 0
            for value in (self.equipment, self.real_estate, self.cash, self.other)
        ):
            raise ValueError("other collateral must be nonnegative")
        return self


class BorrowingBaseInput(ContractModel):
    accounts_receivable: AccountsReceivableBaseInput
    inventory: InventoryBaseInput
    other_collateral: OtherCollateralInput
    additional_reserves: MoneyValue
    prior_liens: MoneyValue

    @model_validator(mode="after")
    def validate_reserves(self) -> BorrowingBaseInput:
        if (
            self.additional_reserves.amount_minor < 0
            or self.prior_liens.amount_minor < 0
        ):
            raise ValueError(
                "borrowing-base reserves and prior liens must be nonnegative"
            )
        return self


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


class InputProvenance(ContractModel):
    """Client-carried source labels for material case inputs."""

    template_slug: str | None = None
    fields: dict[str, ProvenanceSource] = Field(default_factory=dict)
    acknowledged_template_inheritance: bool = False


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
    provenance: InputProvenance = Field(default_factory=InputProvenance)

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
    status: Literal["available", "blocked"] = "available"
    recommendation_state: Literal["calculated", "blocked"] = "calculated"
    underwritten_rate: str | None = None
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
    resolved_snapshot: ResolvedFinancialSnapshot | None = None
    reconciliation_status: Literal["pass", "warning", "blocked"] = "pass"


class ResolvedFinancialSnapshot(ContractModel):
    """The immutable, explainable financial basis used by underwriting."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    resolver_version: str = "v6.2"
    snapshot_hash: str
    basis: Literal["reported_ltm", "derived_ltm", "fiscal_year", "legacy_snapshot"]
    period_id: str
    period_end: date | None
    source_period_ids: list[str]
    flow_source_period_ids: list[str] = Field(default_factory=list)
    balance_sheet_source_period_id: str | None = None
    source_lineage: dict[str, list[str]]
    source_authority: dict[str, SourceAuthority] = Field(default_factory=dict)
    # Explicitly named window metadata prevents reviewers and downstream
    # consumers from having to infer the FY/YTD bridge from array position.
    source_window: dict[str, str | None] = Field(default_factory=dict)
    bridge_formula: str | None = None
    blocked_authority_fields: list[str] = Field(default_factory=list)
    defaulted_authority_fields: list[str] = Field(default_factory=list)
    financials: FinancialInput
    reconciliation_status: Literal["pass", "warning", "blocked"]
    warnings: list[str] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)


class AdjustmentSummaryView(ContractModel):
    entries: list[NormalizationAdjustmentInput]
    reported_ebitda: MoneyValue
    approved_adjustment: MoneyValue
    adjusted_ebitda: MoneyValue
    approved_ebit: MoneyValue | None = None
    approved_cfads_impact: MoneyValue | None = None
    positive_adjustment_pct: str
    warning: str | None
    leverage_before: str | None
    leverage_after: str | None
    dscr_before: str | None
    dscr_after: str | None


class FacilityProtectionView(ContractModel):
    score: str
    category: Literal[
        "strong", "adequate", "moderate", "weak", "severe", "not_applicable"
    ]
    expected_recovery_category: Literal[
        "high", "moderate", "limited", "low", "not_applicable"
    ]
    status: Literal["available", "blocked", "not_applicable_no_supported_exposure"] = (
        "available"
    )
    coverage_requested: str = "0"
    coverage_recommended: str = "0"
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
    commitment: MoneyValue | None = None
    outstanding: MoneyValue | None = None
    excess_or_deficiency: MoneyValue | None
    binding_constraint: str
    policy_notice: str


class RevolverAblView(ContractModel):
    """One visible contract for revolver and ABL liquidity mechanics."""

    applicable: bool
    status: Literal["calculated", "blocked", "not_applicable"]
    facility_type: Literal["term_loan", "revolver", "asset_based"]
    commitment: MoneyValue
    drawn_amount: MoneyValue
    undrawn_commitment: MoneyValue
    borrowing_base: MoneyValue | None
    availability: MoneyValue | None
    commitment_fee_bps: int | None
    commitment_fee: MoneyValue | None
    cash_interest: MoneyValue | None
    cash_interest_rate: str | None
    explanation: str


class PricingView(ContractModel):
    status: Literal["available", "blocked"] = "available"
    reference_base_rate: str
    risk_grade_spread_bps: int
    tenor_adjustment_bps: int
    security_adjustment_bps: int
    amortization_adjustment_bps: int
    covenant_adjustment_bps: int
    concentration_adjustment_bps: int
    relationship_adjustment_bps: int
    indicative_all_in_rate: str | None
    commitment_fee_bps: int | None
    upfront_fee_bps: int | None
    disclaimer: str


class RateDecisionView(ContractModel):
    """Single underwritten rate used consistently by pricing, capacity, and stress."""

    index_rate: str
    floor_rate: str
    shocked_index_rate: str
    spread_bps: int
    underwritten_rate: str
    commitment_fee_bps: int
    upfront_fee_bps: int
    status: Literal["available", "blocked"]
    explanation: str


class DebtReconciliationView(ContractModel):
    """Reconciles balance-sheet debt to instrument schedule debt on one basis."""

    status: Literal["reconciled", "immaterial_difference", "blocked", "aggregate_mode"]
    selected_source: DebtSource
    selected_debt: MoneyValue
    selected_scheduled_principal: MoneyValue
    selected_interest: MoneyValue
    selected_interest_source: Literal["reported_interest", "implied_interest"]
    floating_principal: MoneyValue
    interest_shock_basis: Literal[
        "instrument_rate_type",
        "aggregate_conservative",
        "partial_conservative_residual",
        "reported_aggregate",
    ]
    balance_sheet_gross_debt: MoneyValue
    instrument_gross_debt: MoneyValue | None
    scheduled_principal: MoneyValue | None
    implied_interest: MoneyValue | None
    reported_interest: MoneyValue
    difference: MoneyValue | None
    tolerance: MoneyValue
    interest_difference: MoneyValue | None = None
    interest_tolerance: MoneyValue | None = None
    explanation: str
    leverage_source: DebtSource
    stress_source: DebtSource
    maturity_source: DebtSource
    aggregate_mode: bool = False
    coverage_basis_notice: str = ""
    residual_debt: MoneyValue | None = None
    residual_maturity_year: int | None = None
    residual_maturity_status: Literal["known", "unknown", "not_applicable"] = (
        "not_applicable"
    )

    @model_validator(mode="after")
    def validate_selected_source(self) -> DebtReconciliationView:
        if {
            self.leverage_source,
            self.stress_source,
            self.maturity_source,
        } != {self.selected_source}:
            raise ValueError(
                "leverage, stress, and maturity must use the selected debt source"
            )
        if (
            self.residual_debt is not None
            and self.residual_maturity_status == "known"
            and self.residual_maturity_year is None
        ):
            raise ValueError("known residual maturity requires residual_maturity_year")
        return self


class ResolvedFacilityMechanics(ContractModel):
    """Canonical facility structure consumed by capacity, stress, and terms."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    facility_type: Literal["term_loan", "revolver", "asset_based"]
    amortization_type: Literal["fully_amortizing", "partial", "bullet", "revolver"]
    commitment: MoneyValue
    initial_drawn: MoneyValue
    bullet_percentage: str
    amortization_years: int | None
    maturity_years: int
    availability_period_years: int | None
    commitment_fee_bps: int
    mandatory_prepayment: str
    security_type: Literal["unsecured", "secured", "asset_based"]
    status: Literal["available", "blocked"]
    explanation: str
    blocking_issues: tuple[str, ...] = ()


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
    maturity_test_status: Literal["pass", "breach", "not_applicable", "blocked"] = (
        "not_applicable"
    )
    maturity_test_reason: str = ""
    balloon_amount: MoneyValue | None = None
    exit_leverage: str | None = None
    maturity_year: int | None = None
    exit_ebitda: MoneyValue | None = None
    refinance_capacity: MoneyValue | None = None
    refinance_headroom: MoneyValue | None = None
    no_refinancing_status: Literal["pass", "breach", "not_applicable", "blocked"] = (
        "not_applicable"
    )
    no_refinancing_reason: str = ""
    residual_debt: MoneyValue | None = None


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
    status: Literal["available", "blocked"] = "available"
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


class ProvenanceSummaryView(ContractModel):
    """Review-ready provenance counts carried into analysis and memo output."""

    template_slug: str | None
    counts: dict[ProvenanceSource, int]
    percentages: dict[ProvenanceSource, str]
    total_material_fields: int
    inherited_percentage: str
    unclassified_material_fields: list[str] = Field(default_factory=list)
    acknowledgement_required: bool
    warnings: list[str]


class CompletionSummaryView(ContractModel):
    """Evidence-based completion state; never derived from wizard step count."""

    required_completed: int
    required_total: int
    required_missing: list[str]
    evidence_completed: int
    evidence_total: int
    optional_completed: int
    optional_total: int
    warnings: list[str]
    analysis_ready: bool


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
    provenance: "ProvenanceSummaryView"
    completion: "CompletionSummaryView"
    rate_decision: "RateDecisionView | None" = None
    debt_reconciliation: "DebtReconciliationView | None" = None
    facility_mechanics: "ResolvedFacilityMechanics | None" = None
    capacity: CapacityView
    facility_protection: FacilityProtectionView
    borrowing_base: BorrowingBaseView
    revolver_abl: "RevolverAblView"
    pricing: PricingView
    scorecard: ScorecardView
    scenarios: list[ScenarioView]
    covenants: list[CovenantView]
    policy_checks: list[PolicyCheckView]
    reverse_stress: ReverseStressView
    decision: DecisionView
    memo_sections: dict[str, list[str]]
    analysis_status: Literal["final", "blocked"] = "final"
