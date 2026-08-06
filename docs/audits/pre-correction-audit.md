# Northstar v3 pre-correction audit

Audit date: 2026-08-05  
Repository baseline: `2414c80` (`main`, aligned with `origin/main`)  
Production baseline: `https://northstar-credit-platform.vercel.app`

## Baseline evidence

- `./scripts/verify`: 63 tests passed; Ruff, formatting, and strict mypy passed.
- Credit-engine branch coverage: 99.53%.
- Next.js 16.3 production build: passed.
- Passing legacy checks do not cover the corrective requirements below.

## Confirmed suspected defects

| # | Severity | Finding | Evidence | Corrective task |
|---|---|---|---|---|
| 1 | P1 | “Custom” cases clone a demo and change only name/amount. | `apps/web/components/NewCase.tsx` opens a demo, mutates two fields, then creates a case. | Build a seven-step draft wizard over the complete input contract. |
| 2 | P1 | Opening a demo persists an otherwise unused record. | `POST /demo-cases/{slug}/open` calls `create_case`. The custom flow then creates a second record. | Add a read-only template endpoint; persist exactly once only on explicit save/open. |
| 3 | P1 | Most inputs are read-only. | Workspace `Inputs` renders ten `readOnly` fields. | Make all material borrower, facility, financial, debt, risk, and scenario inputs editable. |
| 4 | P1 | The update API is not surfaced as a complete edit/recalculate workflow. | `PUT /cases/{id}` exists, but the UI has no save, validation, stale-analysis, or rerun controls. | Surface edit, autosave, validate, stale warning, change summary, and rerun. |
| 5 | P1 | Case lifecycle management is absent. | No list/search/filter/sort/duplicate/archive/delete endpoints or UI. | Add full session-owned case management and confirmation states. |
| 6 | P1 | Mobile hides the only workflow navigation. | CSS hides `.workspace-shell>aside` below 900px. | Add an accessible mobile drawer containing the full workflow. |
| 7 | P1 | The navigation icon refreshes the page. | `PanelLeft` calls `router.refresh()`. | Open/close a real focus-trapped drawer; Escape and scroll lock required. |
| 8 | P0 | Missing/NM ratios can receive favorable scores as zero. | `_exact()` converts any absent ratio to `ZERO`; leverage policy awards zero leverage its best band. | Typed states and blocked/adverse missing-data scoring; never coerce to numeric zero. |
| 9 | P0 | Collateral capacity always applies. | `_capacity()` always includes `collateral_capacity` in `min(candidates)`. | Typed applicability driven by facility/security structure; show N/A when irrelevant. |
| 10 | P0 | Zero supported exposure may still be referred rather than declined. | Cyclical demo returns zero capacity and `Refer to credit committee`. | Enforce zero-exposure decision priority: Decline absent an explicit exception path. |
| 11 | P0 | Active policy fields are not all enforced. | Maturity, liquidity, and minimum interest coverage exist in policy but do not control decision/capacity. | Emit structured policy checks with severity, status, exceptionability, and remediation. |
| 12 | P0 | Stress mechanics are materially simplified. | A single payment, hard-coded 12% tax, fixed existing debt service, and cash floored at zero omit deficits/refinancing. | Implement yearly debt/cash roll-forward, rate type/floor/shock, revolver, shortfall, maturity, refinance, and covenant events. |
| 13 | P0 | Reverse stress is algebraic, not a solver. | `_reverse_stress()` applies closed-form ratios and always sets `converged=True`. | Re-run the full forecast per trial using bounded bisection and expose convergence metadata. |
| 14 | P1 | Confidence is fixed. | `_scorecard()` always emits `"medium"`. | Calculate 0–100 confidence, label, drivers, penalties, missing evidence, and improvement actions. |
| 15 | P1 | Covenants are generic. | Every case receives the same leverage/DSCR tests and decision conditions. | Generate structure- and risk-responsive recommendations with rationale/headroom/cure/frequency/type. |
| 16 | P1 | Memo/PDF is too short and incorrectly formats money. | PDF emits `Requested minor units` and only a handful of English lines. | Add one-page and detailed localized memo; use human currency formatting and engine reconciliation tests. |
| 17 | P1 | Traditional Chinese is incomplete. | English outcomes, scenario/covenant names, model labels, memo body, root metadata, and `html lang` remain English. | Localize the full vocabulary, metadata, alternates, errors, tooltips, and PDF. |
| 18 | P1 | Methodology is incomplete in the product. | Five short info titles omit most required mechanics and limitations. | Publish the complete concise methodology as readable sections/accordions. |

## Additional confirmed defects

- `X-Northstar-Session` defaults to the shared value `public-demo`, is accepted from the client without signature, and is not cryptographically generated.
- Production CORS currently allows every origin.
- SQLite `/tmp` fallback is silently used when `DATABASE_URL` is absent, while the UI has no temporary-session disclosure.
- There is no quota, payload-size control, rate limit, PDF limit, cleanup/retention job, or audit log.
- `updated_at` is not changed during update or analysis.
- The current schema stores only JSON blobs and cannot represent versions, debt instruments, policy checks, covenants, memo versions, or audit events independently.
- Unknown information routes fall through to About-like content instead of an explicit localized 404.

## Phase gate

All eighteen suspected defects are confirmed. P0 model defects must be corrected and covered by unit/property tests before the major workspace redesign is accepted.
