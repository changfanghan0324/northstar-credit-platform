# Data Model

## Core entities

- `companies` and `borrower_profiles`: identity, business risk, concentration, management, governance, evidence.
- `source_documents`, `raw_financial_facts`, `financial_periods`, `normalized_financials`: raw-to-normalized lineage.
- `financial_adjustments`: amount, EBITDA/CFADS effects, cash/recurrence flags, evidence, rationale, status.
- `maintenance_capex_inputs`: period, amount, derivation method, evidence, source, confidence, illustrative preparer/status.
- `debt_instruments` and `loan_requests`: existing and proposed terms, currencies, repayment sources, structure.
- `calculation_runs`: immutable engine/policy/input versions and staleness hash.
- `ratio_results`, `scorecards`, `score_components`, `facility_assessments`: explainable borrower/facility risk.
- `scenarios`, `scenario_assumptions`, `scenario_results`: deterministic three-year stress outputs and structured improvement justifications.
- `covenants`, `covenant_tests`: actual, threshold, headroom, status, first breach, cure/action.
- `capacity_constraints`, `credit_decisions`, `credit_memos`: binding capacity, recommendation, conditions, and provenance.
- `audit_logs`, `policy_versions`, `model_versions`: change and calculation traceability.

## Universal result metadata

Every user-visible result carries `source_date`, `model_version`, `policy_version`, `calculated_at`, categorical `confidence`, active `confidence_factors`, and override indicators. Monetary columns carry `currency`, `minor_unit_exponent`, and integer `amount_minor`.

Ratio results store both `value` (four-decimal display/score value) and `value_exact` (unquantized covenant, headroom, and solver value).

## Integrity rules

- Calculation runs are immutable.
- Memo exports read only persisted run outputs and are blocked when the current input hash differs.
- Reporting and loan currencies must match in the MVP.
- Critical missing inputs block grade and decision.
- Scorecard exclusions expose excluded weight and block above the policy ceiling.
