# Northstar v6 decision log

## v6-01 — Money scale contract

Date: 2026-08-08
Status: implementation complete; phase review complete; production check pending

Decision: normalize `whole`, `thousands`, and `millions` exactly once at the
browser/import boundary. Store actual USD cents in `MoneyValue.amount_minor`;
keep `FinancialPeriod.scale` as presentation/import metadata. Use BigInt for
scale-aware redisplay and reject values that exceed the JavaScript safe integer
range after normalization.

Evidence:

- `apps/web/lib/money.ts` owns `normalizeMoneyInput` and
  `formatMoneyAtScale`.
- `apps/web/components/workspace/FinancialSpreadEditor.tsx` uses the same
  normalizer for direct entry and Excel paste.
- `docs/architecture/money-scale-contract.md` is the API and UI contract.
- `tests/fixtures/money_scale_vectors.json` is consumed by Python and
  TypeScript tests.
- Claude Opus 5 High initial challenge:
  `606598e7-85f1-4dbe-9add-33b244ee57ac`.
- Claude Opus 5 High re-challenge PASS:
  `728dc361-bd7d-4459-b287-00894cb99a96`.

Follow-ups carried to later v6 work: computed-output safe bounds, broader
Excel accounting grammar, explicit negative-bound fixture, fixture parity
assertions, and module-scoped coverage reporting.

## v6-02 — Financial lineage and FY/YTD consistency

Date: 2026-08-08
Status: implementation complete; phase review complete; production check pending

Decision: make the FY/current-YTD/prior-comparable-YTD window explicit and
fail-closed. Flows use `FY + Current YTD - Prior Comparable YTD`; point-in-time
balance-sheet lines and snapshot `period_end` use current YTD only. Selection is
based on fiscal metadata and matching fiscal cuts, never generic array
positions. The snapshot now publishes source IDs, period-end dates, formula,
field lineage, authority, and blocked/defaulted fields.

Blocked authority is a first-class state. Until v6-03 reconciles a debt
schedule, missing scheduled principal remains blocked and propagates to DSCR,
capacity, forecast covenants/maturity, and reverse stress; no dependent output
coerces it to zero or presents a numeric approval basis.

Evidence:

- `docs/architecture/financial-lineage-contract.md`
- Strict same-cut/missing-window and blocked-propagation tests in
  `tests/unit/test_v5_logic_contract.py`.
- Full gate: 113 Python tests, 92.83% coverage, strict mypy, TypeScript,
  ESLint, Next build; Playwright 11 passed and 1 intentional mobile skip.
- Initial Claude challenge: `60d3c93c-0f18-4c8d-a235-bea947f64253` (FAIL).
- Remediation challenge: `9be6e487-9218-424f-a06c-bf811760802c` (PASS).

## v6-03 — Debt reconciliation and residual treatment

Date: 2026-08-08
Status: implementation complete; phase review complete; production check pending

Decision: expose one typed debt-reconciliation object and pass it unchanged to
leverage, DSCR, capacity, stress, reverse stress, adjustments, maturity, and
memo/PDF consumers. Aggregate debt is an explicit source. Complete schedules
must reconcile within fixed-denominator directional tolerances. Partial
long-term schedules retain balance-sheet residual debt, use the greater of
reported and declared scheduled principal, mark residual maturity unknown, and
block when residual exceeds the governed 20% ceiling. Contractual interest
remains reported interest while implied interest stays diagnostic.

Stress uses a typed floating basis: instrument floating debt when a complete
schedule exists, conservative aggregate floating debt when no schedule exists,
and instrument floating debt plus conservative residual floating debt for a
partial schedule. Fixed-rate instruments are not repriced. Blocked capacity is
typed with `recommendation_state=blocked` and is rendered in the bilingual UI
and memo/PDF.

Evidence:

- `docs/architecture/debt-reconciliation-contract.md`
- Debt source, tolerance, partial residual, stress, currency, and PDF tests in
  `tests/unit/test_v5_logic_contract.py`, `tests/unit/test_application_analysis.py`,
  and `tests/integration/test_api_workflow.py`.
- Claude Opus 5 High initial challenge:
  `af62da6d-b9e5-41aa-be25-48f3e1dd922b` (FAIL; remediated).
- Claude Opus 5 High re-challenge:
  `2ee7d0c4-9a06-4350-96af-b067dacd736a` (PASS pending green gate).
- Final local gate: 122 Python tests, 92.87% coverage, strict Mypy/Ruff,
  TypeScript, ESLint, Next build, and Playwright 11 passed / 1 intentional
  mobile skip.
