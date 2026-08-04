# Case Workflow

## Guided review

1. **Company** — name, entity type, industry, country, reporting currency.
2. **Loan request** — amount, purpose, facility, maturity, rate type, collateral, and repayment sources.
3. **Financial data** — sample fixture, structured upload, or manual entry; show reconciliation and missing-field status.
4. **Assumptions** — key values, approved adjustments, debt definition, maintenance-capex method, and scenario defaults.
5. **Run review** — financial checks, repayment capacity, stress, capacity, and decision progress.
6. **Recommendation** — decision, amount, three reasons, three risks, conditions, next actions, and links to evidence.

Drafts persist through the API in full-stack mode. Fixture mode is visibly read-only and disables mutating controls.

## Case shell

- Summary — decision, reasons, risks, next action, five headline metrics.
- Financials — normalized statements, adjustments, lineage, debt schedule.
- Risk — obligor score and separate facility-protection assessment.
- Stress — three scenarios, reverse stress, covenant headroom.
- Terms — recommended amount, structure, pricing disclaimer, conditions, monitoring.
- Memo — one-page and detailed deterministic narratives with provenance.

## Analyst details

One global additive preference reveals formulas, policy bands, sources, period basis, overrides, and confidence factors. It cannot add, remove, or change a financial value and cannot alter exports.
