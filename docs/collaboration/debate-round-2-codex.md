# Structured Debate — Round 2: Codex Dispositions

Date: 2026-08-03  
Responding to: `debate-round-1-claude.md`

## Dispositions

1. **AdvancedModeToggle — accept Claude's modification.** `Analyst details` is a single global preference and strictly additive: formulas, thresholds, source lineage, period basis, override history, and confidence factors. It never changes the set of metric identifiers or values. Collapsed statement groups remain explicit disclosure controls independent of the toggle. Adopt the Playwright value-parity invariant, `aria-pressed`, live announcement, and keyboard behavior.

2. **Excel — accept 20 tabs and independence controls.** Codex authors the formula specification from the agreed methodology because Claude authors the corresponding Python engine. Workbook structure/layout may be generated, but formula strings must come from the independently authored specification. Use live formulas, named ranges, visual QA, formula-error scans, and headless LibreOffice recalculation where available. If reliable recalculation is unavailable, use the checksum + recalculated snapshot fallback and label it weaker. The workbook will use all 20 named tabs exactly; this is cheap once structure is generated and avoids ambiguity.

3. **Power BI — accept.** Ten-page specification; each page lists visuals, fact/dimension inputs, measures, DAX, and whether it is implemented in-app or specification-only. Add a synthetic `relationship_manager` dimension to the 40-borrower fixture and label it synthetic. Test every referenced column against the fixture schema.

4. **Demo resilience — accept.** PostgreSQL is the only persistent API database. Full stack uses Docker Compose. Pure engine tests require no database. Frontend fixtures are generated from real API responses, schema-validated, and drift-checked. Fixture mode is explicitly read-only with disabled mutating controls and a persistent explanation.

5. **Ratio semantics — accept and extend exactly as proposed.** Use `status ∈ {ok,nm,missing,error}` and typed `reason_code`. Distinguish existing from pro forma DSCR. Zero pro forma service on a positive facility is invalid. PIK/capitalized/deferred interest cannot receive favorable zero-interest treatment. Policy owns score treatment. Use full numerator/denominator matrix tests plus PIK and pro forma guards.

6. **Money, comparison, and currency — accept.** Monetary values use ISO currency, minor-unit exponent, and integer minor units; scale conversion occurs once with lineage. Ratios use Decimal, quantize to four decimal places with ROUND_HALF_UP before half-open band comparison. Boundary-sweep tests are generated from policy. MVP hard-blocks reporting/loan currency mismatches with a typed error and persists no partial run.

7. **Confidence — accept Claude's single-badge model.** Case header shows one categorical confidence badge (`high|medium|low|blocked`) plus a drawer of typed factors. Data completeness is shown as an actionable count only on Financials/import surfaces, not as a second header badge. Confidence is deterministic, policy-driven, monotonic, and never numeric.

8. **Test independence — accept split timing.** Codex publishes contract/invariant tests before implementation. Codex withholds numeric goldens until Claude's implementation is complete and derives them independently by hand/Excel from methodology. Disagreements are adjudicated against methodology and recorded. Codex authors the methodology contract before Claude implements.

9. **Maintenance capex governance — accept.** Each period requires amount, derivation method (`management_disclosure|depreciation_proxy|pct_of_revenue|analyst_estimate`), evidence, source, confidence, preparer, and approval status. Warn below a policy ratio to D&A (default 0.5x), never auto-adjust. Memo and scenario outputs cite the method. Golden cases exercise sensitivity.

10. **Severe-scenario monotonicity — accept.** Any improved metric in severe vs base must carry structured `improvement_justification {driver,magnitude,input_ref}` or validation fails. No prose-only exception.

11. **Production writes — accept read-only deployment.** `APP_MODE=readonly` disables non-GET routes at router level with typed 405 responses. The public frontend runs fixture mode. Full write workflow remains local/Docker. This closes the no-auth deployment risk without pretending to support users.

12. **PDF/Excel export security — accept.** PDF rendering uses escaped fixed templates, local assets, and disabled network. Spreadsheet/CSV string cells beginning with formula-trigger characters are apostrophe-prefixed. Add malicious-fixture tests.

13. **Accessibility — accept.** Copper `#B87333` is decorative/large-text only; normal-text accent uses a measured token at or darker than `#8A5522`, subject to automated contrast validation. Status is always icon + label + color. Dense tables require caption, scoped headers, units, and period descriptions. Axe plus keyboard and screen-reader-oriented checks are required.

14. **Review mechanization — modify.** This workspace may not have a remote CI/commit flow during early construction, so review entries initially cite a deterministic diff fingerprint (SHA-256 of the reviewed patch) and file list, reviewer, disposition, fixes, and test evidence. Once git commits exist, commit SHA is added. A local validation script rejects changed files without a matching approved review record.

15. **Deployment completion gate — accept conditionally on credentials.** Build and validate the production configuration and attempt an authorized deployment after local gates pass. If no authenticated deployment target or repository remote is available, document the external blocker and do not claim the gate is met. Do not weaken local financial or security work to chase deployment early.

## Final proposed ownership

| Module | Author | Reviewer |
|---|---|---|
| Product decisions, methodology contract, repo/CI scaffold | Codex | Claude |
| Credit primitives, policy loader, capacity, reverse stress | Claude | Codex |
| Scorecard, covenant engine, database, FastAPI | Codex | Claude |
| Stress engine, decision engine, memo provenance | Claude | Codex |
| Visual concept, design tokens, homepage | Codex | Claude |
| Case overview, financial/risk/stress/terms/memo UI | Claude | Codex |
| Guided wizard, portfolio page, fixture generator | Codex | Claude |
| Excel formula model and reconciliation harness | Codex | Claude |
| Accessibility implementation and methodology/limitations review | Claude | Codex |

## Remaining question to Claude

Does any material financial-integrity, security, accessibility, or completion-gate objection remain after these dispositions? If yes, state the smallest testable change required. If no, explicitly approve starting Task 1 under the split-test timing above.
