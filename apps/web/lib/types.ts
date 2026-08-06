export type Money = {
  amount_minor: number;
  currency: string;
  minor_unit_exponent: number;
};
export type Ratio = {
  metric_id: string;
  status: string;
  value: string | null;
  reason_code: string;
  label: string;
  plain_label: string;
  formula_id: string | null;
  policy_ref: string | null;
  direction: string;
  source_period: string | null;
  model_version: string;
};
export type Borrower = {
  legal_name: string;
  industry: string;
  headquarters: string;
  description: string;
};
export type LoanRequest = {
  amount: Money;
  purpose: string;
  annual_rate: string;
  maturity_years: number;
  facility_type: "term_loan" | "revolver" | "asset_based";
  security_type: "unsecured" | "secured" | "asset_based";
  rate_type: "fixed" | "floating";
  base_rate: string;
  rate_floor: string;
  amortization_years: number | null;
  guarantee: string;
  primary_repayment_source: string;
};
export type DemoCase = {
  slug: string;
  borrower: Borrower;
  request: LoanRequest;
  decision: { outcome: string; rationale: string[]; conditions: string[] };
  grade: number | null;
  recommended: Money;
};
export type ScenarioInput = {
  revenue_growth: string;
  subsequent_growth: string;
  ebitda_margin_change: string;
  rate_shock: string;
  working_capital_pct_revenue: string;
  maintenance_capex_pct_revenue: string;
};
export type DebtInstrument = {
  name: string;
  principal: Money;
  annual_rate: string;
  rate_type: "fixed" | "floating";
  spread: string;
  rate_floor: string;
  scheduled_amortization: Money;
  maturity_year: number;
  secured: boolean;
  seniority: string;
  collateral: string;
};
export type CaseInput = {
  slug: string;
  borrower: Borrower;
  request: LoanRequest;
  financials: Record<string, Money | string>;
  debt_instruments: DebtInstrument[];
  business_risk: {
    strengths: string[];
    risks: string[];
    factor_evidence?: Record<
      string,
      {
        score: string;
        band: string;
        evidence: string;
        source: string;
        analyst_rationale: string;
        confidence: string;
        override_status: string;
        reviewer_status: string;
        last_updated: string;
      }
    >;
    [key: string]: unknown;
  };
  financial_spread?: {
    periods: FinancialPeriod[];
    selected_ltm_method: string | null;
  };
  normalization_adjustments?: Adjustment[];
  borrowing_base?: BorrowingBaseInput | null;
  pricing?: {
    reference_base_rate: string;
    relationship_adjustment_bps: number;
    include_upfront_fee: boolean;
  };
  scenarios: Record<"base" | "downside" | "severe", ScenarioInput>;
  data_as_of: string;
};
export type BorrowingBaseInput = {
  accounts_receivable: Record<string, Money | string>;
  inventory: Record<string, Money | string>;
  other_collateral: Record<string, Money>;
  additional_reserves: Money;
  prior_liens: Money;
};
export type FinancialPeriod = {
  id: string;
  label: string;
  period_type: string;
  start_date: string;
  end_date: string;
  fiscal_year: number;
  fiscal_quarter: number | null;
  audited: boolean;
  source_type: string;
  source_reference: string;
  currency: string;
  scale: "whole" | "thousands" | "millions";
  income_statement: Record<string, Money | null>;
  balance_sheet: Record<string, Money | null>;
  cash_flow: Record<string, Money | null>;
};
export type Adjustment = {
  id: string;
  name: string;
  period_id: string;
  category: string;
  amount: Money;
  direction: "positive" | "negative";
  cash_classification: "cash" | "noncash";
  recurrence: "recurring" | "nonrecurring";
  ebitda_impact: Money;
  ebit_impact: Money;
  cfads_impact: Money;
  supporting_evidence: string;
  source_reference: string;
  analyst_rationale: string;
  approval_status: string;
  reviewer: string | null;
  created_at: string;
  updated_at: string;
};
export type CapacityConstraint = {
  key: string;
  label: string;
  amount: Money | null;
  applicable: boolean;
  status: "valid" | "blocked" | "policy_not_applicable";
  reason: string;
  policy_ref: string | null;
  binding: boolean;
};
export type ScenarioYear = {
  year: number;
  revenue: Money;
  adjusted_ebitda: Money;
  cfads: Money;
  beginning_debt: Money;
  new_facility: Money;
  scheduled_amortization: Money;
  optional_paydown: Money;
  average_debt: Money;
  ending_debt: Money;
  ending_cash: Money;
  cash_shortfall: Money;
  revolver_draw: Money;
  revolver_remaining: Money;
  refinancing_need: Money;
  unpaid_debt_service: Money;
  leverage: string | null;
  leverage_status: string;
  leverage_reason_code: string;
  interest_coverage: string | null;
  interest_coverage_status: string;
  interest_coverage_reason_code: string;
  dscr: string | null;
  dscr_status: string;
  dscr_reason_code: string;
  covenant_status: "pass" | "breach" | "not_applicable" | "blocked";
  liquidity_status: "adequate" | "shortfall";
  refinancing_status: "none" | "required";
  debt_service_status: "paid" | "unpaid";
  revolver_status: "available" | "exhausted" | "not_applicable";
};
export type Analysis = {
  case: CaseInput;
  input_hash: string;
  calculated_at: string;
  analysis_status: "final" | "blocked";
  policy_version: string;
  engine_version: string;
  metrics: Record<string, Ratio>;
  financial_spreading: {
    periods: FinancialPeriod[];
    historical_years: number;
    forecast_years: number;
    selected_ltm_method: string | null;
    ltm_period_id: string | null;
    ltm_status: "available" | "blocked" | "legacy_snapshot";
    reconciliation_warnings: string[];
    trend: Record<string, Array<string | null>>;
  };
  adjustments: {
    entries: Adjustment[];
    reported_ebitda: Money;
    approved_adjustment: Money;
    adjusted_ebitda: Money;
    positive_adjustment_pct: string;
    warning: string | null;
    leverage_before: string | null;
    leverage_after: string | null;
    dscr_before: string | null;
    dscr_after: string | null;
  };
  capacity: {
    requested: Money;
    leverage: Money;
    dscr: Money;
    collateral: Money | null;
    policy: Money;
    recommended: Money;
    binding_constraints: string[];
    constraints: CapacityConstraint[];
  };
  scorecard: {
    score: string | null;
    grade: number | null;
    grade_label: string;
    confidence: string;
    confidence_score: number;
    confidence_drivers: string[];
    confidence_penalties: string[];
    improvement_actions: string[];
    synthetic_notice: string;
    components: Array<{
      key: string;
      score: string;
      weight: string;
      contribution: string;
      band: string;
      status: string;
      evidence: string;
    }>;
  };
  facility_protection: {
    score: string;
    category: string;
    expected_recovery_category: string;
    factors: Record<string, string>;
    main_protections: string[];
    main_structural_weaknesses: string[];
    required_improvements: string[];
    documentation_requirements: string[];
  };
  borrowing_base: {
    applicable: boolean;
    status: string;
    gross_collateral: Money | null;
    eligibility_reductions: Money | null;
    eligible_receivables: Money | null;
    receivables_availability: Money | null;
    eligible_inventory: Money | null;
    inventory_availability: Money | null;
    other_eligible_collateral: Money | null;
    reserves: Money | null;
    prior_liens: Money | null;
    borrowing_base: Money | null;
    availability: Money | null;
    excess_or_deficiency: Money | null;
    binding_constraint: string;
    policy_notice: string;
  };
  pricing: {
    reference_base_rate: string;
    risk_grade_spread_bps: number;
    tenor_adjustment_bps: number;
    security_adjustment_bps: number;
    amortization_adjustment_bps: number;
    covenant_adjustment_bps: number;
    concentration_adjustment_bps: number;
    relationship_adjustment_bps: number;
    indicative_all_in_rate: string;
    commitment_fee_bps: number | null;
    upfront_fee_bps: number | null;
    disclaimer: string;
  };
  scenarios: Array<{
    name: "base" | "downside" | "severe";
    years: ScenarioYear[];
    first_breach_year: number | null;
    first_stress_event_year: number | null;
    liquidity_exhaustion_year: number | null;
  }>;
  covenants: Array<{
    name: string;
    threshold: string;
    actual: string;
    headroom: string;
    status: "pass" | "breach";
    scenario: string;
    year: number;
    frequency: string;
    rationale: string;
    cure: string;
    covenant_type: string;
  }>;
  policy_checks: Array<{
    key: string;
    label: string;
    status: string;
    severity: string;
    actual: string;
    threshold: string;
    exception_allowed: boolean;
    remediation: string;
  }>;
  reverse_stress: {
    dscr_minimum_revenue_decline: string | null;
    leverage_breach_margin_decline: string | null;
    maximum_downside_loan: Money | null;
    converged: boolean;
    method: string;
    iterations: number;
    tolerance: string;
    residual: string;
    lower_bound: string;
    upper_bound: string;
    interpretation: string;
    failure_reason: string | null;
    solvers: Array<{
      key: string;
      variable_solved: string;
      lower_bound: string;
      upper_bound: string;
      tolerance: string;
      iterations: number;
      residual: string | null;
      converged: boolean;
      failure_reason: string | null;
      result: string | null;
      result_money: Money | null;
      interpretation: string;
    }>;
  };
  decision: {
    outcome: string;
    rationale: string[];
    conditions: string[];
    primary_repayment_source: string;
    secondary_repayment_source: string;
    facility_type: string;
    maturity_years: number;
    amortization_years: number;
    collateral: string;
    guarantee: string;
    monitoring: string[];
    policy_exceptions: string[];
    decision_priority: string;
  };
  memo_sections: Record<string, string[]>;
};
export type CaseEnvelope = {
  id: string;
  title: string;
  status: string;
  version: number;
  archived: boolean;
  updated_at: string;
  expires_at: string;
  input: CaseInput;
  analysis: Analysis | null;
};
export type CaseSummary = {
  id: string;
  title: string;
  slug: string;
  borrower_name: string;
  status: string;
  version: number;
  archived: boolean;
  updated_at: string;
  decision: string | null;
  grade: number | null;
};
export type RuntimeInfo = {
  product_mode: "portfolio_demo";
  persistence: string;
  durable: boolean;
  retention_days: number;
  case_quota: number;
  requests_per_minute: number;
  pdfs_per_hour: number;
  maximum_payload_bytes: number;
  rate_limit_scope: "best_effort_instance" | "shared";
  notice: string;
};

export type AuditEntry = {
  id: string;
  action: string;
  version: number;
  details: Record<string, unknown>;
  created_at: string;
};

export type CaseVersionSummary = {
  version: number;
  status: string;
  created_at: string;
  analyzed: boolean;
};
