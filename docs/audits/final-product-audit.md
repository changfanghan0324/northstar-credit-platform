# Final product audit

Baseline captured at `2026-08-06T16:11:27Z` before this corrective cycle.

## Revalidated baseline

| Evidence | Result |
| --- | --- |
| Local and remote revision | `main` and `origin/main` both `c867e001954749983d99db2e6e2aa903a69155a1`; clean worktree |
| Production deployment | Vercel `dpl_EUzUu8RxvaBd6MFpq2M3RbXkt1BZ`, `READY`, production alias `northstar-credit-platform.vercel.app` |
| Existing quality gate | Ruff, Ruff format, mypy, TypeScript, ESLint, Next production build passed; 79 pytest tests passed; **credit-engine-only** coverage 99.54%. Application/API coverage was not measured by the baseline command. |
| Public pages | English and Traditional Chinese homepage, cases, new case, methodology, technical validation, about, and 404 rendered without framework overlay or console warning/error |
| Workspace | Overview, inputs, financials, capacity, risk, stress, decision, and memo rendered for a newly opened synthetic demo case |
| Wizard | All seven existing steps rendered and were reachable |
| Responsive shell | 1440, 1280, 1024, 768, 430, 390, and 360 CSS-pixel widths had no horizontal document overflow on the overview |
| Existing interaction | English-to-Traditional-Chinese navigation and demo-case opening changed route and rendered the expected localized content |

The baseline proves the previously delivered MVP works. It does not satisfy the new acceptance criteria by itself.

## Current-state gap matrix

| Requirement | Baseline state | Evidence / gap | Priority |
| --- | --- | --- | --- |
| Honest product positioning | Pass | Homepage and runtime disclose synthetic educational use and temporary anonymous persistence | Preserve |
| Mode A versus Mode B | Partial | Runtime is Mode A, but no single versioned product-mode declaration is exposed throughout every page and output | P0 |
| Complete case lifecycle | Partial | Create, update/stale, analyze, duplicate, archive, **restore**, and delete exist; user-visible audit history and historical-version restore do not | P0 |
| Database design | Fail | Runtime `create_all` owns two ORM tables while migration 0002 declares 17 unused JSON stubs and architecture docs describe a third normalized design | P0 |
| True case versioning | Fail | Updates overwrite `input_json` and increment a counter; no historical version is written or restorable | P0 |
| Security / operational controls | Fail | Process-local request/PDF dictionaries cannot enforce fleet-wide quotas on serverless; runtime retention wording is internally inconsistent when persistence is temporary | P0 |
| Multi-period spreading | Fail | `FinancialInput` is one reported snapshot plus `prior_revenue` and `prior_adjusted_ebitda`; no period collection, period reconciliation, LTM method, or forecast statements | P0 |
| Guided versus Analyst entry | Partial | Mode toggle exists; both modes use nearly the same snapshot inputs and neither provides full statement-by-period entry, scale, bulk paste, CSV template, provenance, autosave, or undo | P0 |
| Normalization adjustments | Fail | Two aggregate EBITDA adjustment amounts; no evidence/rationale/approval/change log or bridge | P0 |
| Evidence-backed business risk | Fail | Six unexplained numeric values plus free-text strengths/risks; no required factor evidence, band, source, confidence, reviewer, or override | P0 |
| Facility protection | Fail | Security affects collateral applicability only; no independent facility score/category/protections/weaknesses | P0 |
| Borrowing base | Fail | Asset-based cases use one manual `collateral_capacity`; no AR/inventory eligibility, reserves, prior liens, availability, or deficiency | P0 |
| Indicative pricing | Fail | Request has a rate, but no versioned spread/adjustment/fee engine or transparent pricing output | P0 |
| Six genuine reverse-stress solvers | Fail | One revenue/DSCR bisection exists; margin and maximum-loan outputs are shortcuts; three required solvers are absent; solver metadata is shared rather than per result | P0 |
| Stress completeness | Partial | Three years, debt behavior, draws, cash shortfall, and refinancing need exist; no fixed/floating and maturity-wall views, refinancing-unavailable switch, explicit unpaid service/exhaustion states, or charts | P1 |
| Beginner progressive disclosure | Partial | Plain labels and some metric explanations exist; no three-layer reusable metric detail or glossary drawer | P1 |
| Page density | Partial | Core workspace pages have distinct questions; inputs and tables remain dense and details are not consistently collapsed in Guided mode | P1 |
| Simplified wizard | Partial | Seven steps work; no Essential/Advanced grouping, completion percentage, autosave state, provenance, skip-optional action, unit/sign guidance, or severity-grouped review | P1 |
| Numeric input correctness | Fail | Empty input silently becomes zero and invalid input can throw during React updates, causing inconsistent error behavior or a global error page | P0 |
| Numeric transport safety | Fail | Python uses exact integers/Decimal, but TypeScript models `amount_minor` as `number` and converts parsed decimal strings through `Number.parseInt`; the current $25M exposure cap reduces immediate overflow risk but does not satisfy the requested exact-string contract | P1 |
| One-page and 32-section memo | Fail | Executive/detailed PDF controls exist, but the memo model contains 13 sections and the detailed PDF is not the required 32-section document | P0 |
| PDF rendering integrity | Fail | English uses cp1252 replacement and Traditional Chinese relies on a non-embedded CID font; byte tests do not prove readable, equivalent localized documents | P0 |
| Complete localization | Partial | Route-level bilingual UI exists; API-sourced labels/status/reasons and portions of memo/workspace can remain English in Traditional Chinese | P0 |
| WCAG 2.2 AA evidence | Partial | Labels, keyboard-capable controls, mobile dialog focus handling, and reduced-motion CSS exist; no axe suite, full error-summary semantics, chart alternatives, or recorded screen-reader smoke | P0 |
| Component quality | Fail | `CaseWorkspace.tsx` and `NewCase.tsx` use extremely long minified lines and combine data, state, navigation, formatting, and all page bodies | P1 |
| Comprehensive new tests | Fail | Current 79 tests cover the prior scope only; required period, adjustment, facility, borrowing-base, pricing, six-solver, restore, accessibility, localization, and browser cases are absent | P0 |
| Frontend test foundation | Fail | No committed browser runner, axe dependency, or rendered-localization suite exists in `apps/web/package.json` | P0 |

## Proposed implementation sequence for independent challenge

1. P0 correctness/reviewability gate: de-minify the two client files in a formatting-only change; fix empty/invalid money entry, scenario sentinels, favorable-NM scoring, event/covenant conflation, and non-converged solver publication; correct Mode A/runtime disclosures and measure application/API coverage.
2. P1 foundation gate: reconcile runtime schema and migrations, implement real case snapshots/audit reads, establish typed localization and browser/axe characterization tests, then split components without behavior drift.
3. P2 capability gate: multi-period/LTM → adjustments and qualitative evidence → facility protection/borrowing base/pricing → all six solvers/stress views → one-source localized memos → progressive-disclosure UX.
4. Final gate: full static/unit/property/integration/browser/accessibility/localization/PDF/golden-case suite, new independent diff review, one validated deploy artifact, and production smoke test.

This order is a Codex proposal, not a final decision. Claude Opus 5 High must challenge it before material implementation.

## Final implementation disposition

The baseline gap matrix above is retained as before-state evidence. The resulting
implementation closes the P0 capability gaps with backward-compatible contracts:
real immutable case versions/audit reads, period statements and guarded LTM,
itemized adjustments, six evidence-backed qualitative factors, independent facility
protection, an asset-based borrowing base, transparent pricing, six solver records,
32-section bilingual memos, Guided/Analyst disclosure, browser/axe tests, and exact
money bounds.

Local final gate on 2026-08-06:

- 98 Python unit/integration tests passed; measured engine/application/API coverage
  was 96.07%.
- Ruff, Ruff format, strict Mypy, strict TypeScript, ESLint, and the Next.js 16
  production build passed.
- Eight Playwright tests passed across desktop Chromium and mobile Chromium,
  including axe, both modes, nine workspace sections, mobile dialog behavior,
  keyboard skip navigation, localized 404, and rendered Traditional Chinese leak
  scanning.
- English and Traditional Chinese detailed PDFs were regenerated and visually
  reviewed page by page; the embedded font/license are release files.
- Independent final reviewer `claude-opus-5` session
  `e780a0d1-7fc4-46a6-a258-65f54bef2b06` found no blocker and returned
  **PROCEED WITH DEPLOYMENT**.

Production deployment and public alias verification are recorded after the release
commit in the production verification section added below.
