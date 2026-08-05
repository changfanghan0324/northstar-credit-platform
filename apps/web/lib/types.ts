export type Money = { amount_minor: number; currency: string; minor_unit_exponent: number };
export type Ratio = { metric_id: string; status: string; value: string | null; reason_code: string; label: string };
export type DemoCase = {
  slug: string;
  borrower: { legal_name: string; industry: string; headquarters: string; description: string };
  request: { amount: Money; purpose: string; annual_rate: string; maturity_years: number };
  decision: { outcome: string; rationale: string[]; conditions: string[] };
  grade: number;
  recommended: Money;
};
export type CaseInput = {
  slug: string;
  borrower: DemoCase["borrower"];
  request: DemoCase["request"];
  financials: Record<string, Money | string>;
  business_risk: { strengths: string[]; risks: string[]; [key: string]: unknown };
  scenarios: Record<string, unknown>;
  data_as_of: string;
};
export type ScenarioYear = {
  year: number; revenue: Money; adjusted_ebitda: Money; cfads: Money; ending_debt: Money;
  ending_cash: Money; leverage: string; interest_coverage: string; dscr: string; covenant_status: "pass" | "breach";
};
export type Analysis = {
  case: CaseInput;
  input_hash: string;
  calculated_at: string;
  metrics: Record<string, Ratio>;
  capacity: { requested: Money; leverage: Money; dscr: Money; collateral: Money; policy: Money; recommended: Money; binding_constraints: string[] };
  scorecard: { score: string; grade: number; grade_label: string; confidence: string; components: Array<{ key: string; score: string; weight: string; contribution: string; band: string }> };
  scenarios: Array<{ name: "base" | "downside" | "severe"; years: ScenarioYear[]; first_breach_year: number | null }>;
  covenants: Array<{ name: string; threshold: string; actual: string; headroom: string; status: "pass" | "breach"; scenario: string; year: number }>;
  reverse_stress: { dscr_minimum_revenue_decline: string; leverage_breach_margin_decline: string; maximum_downside_loan: Money; converged: boolean };
  decision: { outcome: string; rationale: string[]; conditions: string[]; primary_repayment_source: string; secondary_repayment_source: string };
  memo_sections: Record<string, string[]>;
};
export type CaseEnvelope = { id: string; input: CaseInput; analysis: Analysis | null };
