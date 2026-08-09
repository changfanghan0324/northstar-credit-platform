# Northstar v6 post-fix audit

Date: 2026-08-08
Release commit: `bf0906b` (`v6-07-add-provenance-and-completion`)
Production deployment: `dpl_AadQpGe2ZVipaPo9Jjva84znAakA` (READY)

## Final invariant matrix

| Contract | Evidence | Disposition |
| --- | --- | --- |
| Money scale | Canonical minor-unit model, whole/thousands/millions vectors, unsafe-integer and browser round-trip tests | Fixed |
| FY/YTD lineage | Separate flow and current-YTD balance sources, materially different YTD fixture, API/PDF lineage | Fixed |
| Source authority | Canonical snapshot and field authorities block stale spread inheritance | Fixed |
| Debt reconciliation | Reconciled, tolerance, mismatch, aggregate, partial residual, stress and bilingual memo/PDF tests | Fixed |
| Adjustment authority | Itemized approved entries drive all outputs; legacy aggregate bypass regression tests | Fixed |
| Facility mechanics | Immutable resolver passed through capacity, pricing, scenarios, stress, decision, memo, UI and PDF | Fixed |
| Bullet maturity | Five-year balloon, exit leverage, refinancing headroom and severe no-refinancing tests | Fixed |
| Revolver/ABL | Typed commitment, drawn, base, availability, fees, cash interest and capacity linkage | Fixed |
| Rate decision | One floor/index/spread/shock result drives pricing, capacity, interest, DSCR, stress and memo | Fixed |
| Zero exposure and validation | Typed not-applicable state, negative/cross-field rejection, no denominator disguise | Fixed |
| Outcome semantics | Decline reasons and improvements without active-loan covenant presentation; bilingual coverage | Fixed |
| Provenance/completion | Closed source taxonomy, 75% boundary, unclassified blocking, acknowledgement, evidence readiness, bilingual parity | Fixed |

## Verification

- 133 Python tests passed at 93.30% total coverage.
- Ruff, strict Mypy, formatting, TypeScript, ESLint, and Next production build
  passed.
- Playwright passed 13 tests with one intentional mobile skip; the custom-case
  Review page checks source counts, evidence completion, and acknowledgement.
- Production English/Traditional Chinese routes, health/runtime/demo endpoints,
  three demo opens, provenance/completion payloads, detailed PDFs, and the
  95.00%-inherited validation gate were checked. The configured five-per-hour
  PDF limit correctly rate-limited the sixth request.
- Vercel reported no runtime errors in the last hour. Browser production review
  showed the provenance/completion panel and no application error.

## Accepted limitations

Synthetic inputs, anonymous temporary sessions, best-effort instance-local limits,
seven-day expiry, illustrative policy and pricing, unsupported multi-currency
consolidation, and untagged PDF accessibility remain explicit product limits. The
product remains Portfolio Demo Mode and uses “bank-style”/“committee-format”
language; it is not committee-ready or a regulated lending system.
