# Independent final-cycle review — Claude Opus 5 High

## Execution record

- Model requested and returned: `claude-opus-5`
- Claude Code version: `2.1.221`
- Effort: `high`
- Session ID: `84cea149-3125-4ba4-bdb8-3529292d89cb`
- Started: 2026-08-06 UTC
- Completed/recorded: `2026-08-06T16:21:47Z`
- Mode: local Codex workspace, `--print`, read-only tool instructions; no Claude App control
- Baseline: `c867e001954749983d99db2e6e2aa903a69155a1`
- Verdict: **PROCEED WITH CHANGES**
- Limitation reported by Claude: one Bash inspection command was denied because it referenced a stale path; Claude did not independently rerun `./scripts/verify` or validate Vercel. Codex had already run and recorded those checks separately.

## Question reviewed

Claude independently reviewed the complete user specification, the three Codex current-state audits, the proposed sequence, and the actual models, analysis, policy, persistence, API, PDF, frontend, migration, and test code. It was asked to challenge product scope, personas/IA, financial definitions, database design, scoring, stress/reverse stress, facility protection, borrowing base, pricing, memo, localization, accessibility, security, and code-change risk before material implementation.

## Claude recommendation

Claude agreed that the baseline should be extended rather than rewritten and that Mode A is the correct product posture, but required a gated sequence and raised these material objections:

1. Correct a factual audit error: archive toggling already implements restore; audit-history reads and historical-version restore are the actual gaps.
2. Eliminate forecast `999.9999` sentinels because zero service/interest can produce favorable covenant output and negative earnings become a displayed pseudo-ratio.
3. Make favorable-not-meaningful scoring direction-aware; zero debt currently receives the worst leverage band.
4. Separate covenant breach, liquidity shortfall, and refinancing events; they are currently conflated.
5. Never expose a numerical reverse-stress result when bisection does not bracket/converge.
6. Reconcile three divergent database descriptions: ORM runtime tables, unused migration stubs, and normalized architecture documentation. A version counter is not historical versioning.
7. Fix money parsing first: empty input silently becomes zero and invalid text can throw in React update paths.
8. Make source reviewable before feature work: the two main client files are source-minified into very long lines.
9. Add a real typed localization architecture before copying inline ternaries into split components.
10. Treat PDF equivalence/readability as a functional requirement; current English replacement encoding and non-embedded Traditional Chinese font are not proven safe.
11. Treat process-local serverless quotas as best-effort rather than fleet-wide enforcement and make runtime disclosure internally consistent.
12. Add frontend/browser/axe infrastructure and application/API coverage before relying on the baseline engine-only coverage number.

Claude recommended P0 correctness/reviewability, P1 foundations, then P2 capability work, with explicit gates. It also recommended a scope-reduction gate if resources prove insufficient, while clearly forbidding a false completion claim.

## Codex response

| Claude concern | Codex response | Decision |
| --- | --- | --- |
| Restore finding is wrong | Accepted; source confirms archive toggles to restore | Audits corrected; no duplicate restore implementation |
| Scenario sentinels and favorable-NM inversion | Accepted as newly discovered P0 defects | Fix and add named/property tests before new solvers |
| Event/covenant conflation and non-converged display | Accepted | Split states and nullable solver result/failure reason first |
| Database drift and fake version history | Accepted | Keep Mode A JSON aggregate persistence, make it explicit, add actual immutable case-version snapshots/audit reads, and reconcile migrations/docs |
| Source-minified components | Accepted | Formatting-only normalization is the first code change; add formatting enforcement and characterization tests before responsibility split |
| Money overflow priority should be demoted | Partially accepted | Parser crash and empty-to-zero are first. Exact decimal-string transport remains required by the user and will be completed before expanded financial input, even though the present policy cap lowers immediate overflow risk |
| Message catalog before component split | Accepted | Typed catalog/localization helpers precede the final split |
| Mode A requires durable fleet-wide quota | Accepted as a limitation, with implementation caveat | Do not overclaim process-local limits. Prefer a shared database-backed limiter when durable storage is configured; expose honest best-effort status otherwise. Mode A remains selected |
| Scope reduction | Not adopted as the delivery target | The user explicitly requires the full acceptance set. The gates are adopted, and any unachieved criterion must be reported as a limitation rather than falsely declared complete |
| Facility Protection page may overlap Decision & Terms | Resolved by scope | Facility Protection owns lender-protection analysis; Decision & Terms owns the approval instrument and incorporates its outputs |

## Agreed implementation sequence

### Gate P0 — correctness, honesty, reviewability

- Pure formatting normalization and enforcement for the large client files.
- Safe money parser with missing/error states and no throw inside React state updates.
- Explicit forecast ratio states; direction-aware favorable NM scoring.
- Separate covenant/liquidity/refinancing/unpaid-service states.
- Suppress non-converged solver results.
- Honest Mode A/runtime quota and retention disclosure.
- Expand measured coverage to application/API packages.

### Gate P1 — foundations

- Reconcile schema ownership; implement immutable case versions and audit reads.
- Typed localization catalog and rendered Traditional Chinese leak test.
- Frontend characterization, browser, and axe test infrastructure.
- Component split with preserved behavior.

### Gate P2 — requested capabilities

- Structured multi-period spreading and LTM reconciliation.
- Itemized normalization adjustments and evidence-backed business risk.
- Separate facility protection, borrowing base, and versioned pricing.
- Six full-forecast deterministic solvers and enhanced stress presentation.
- One-source one-page and 32-section localized memo/PDF.
- Guided/Analyst progressive disclosure, glossary, wizard provenance/autosave/validation/accessibility.

### Final gate

- All static, unit, property, integration, golden-case, browser, accessibility, localization, PDF, responsive, and production checks.
- A new independent Claude Opus 5 High review of the final diff.
- GitHub push, one validated Vercel production artifact, alias/commit verification, and production smoke evidence.

## Files affected by this review

- `docs/audits/final-product-audit.md`
- `docs/audits/final-model-audit.md`
- `docs/audits/final-ux-audit.md`
- `docs/collaboration/final-decision-log.md`
- `docs/collaboration/final-review-claude-opus-5.md`

The review record is intentionally honest about its Bash limitation and does not reuse previous Claude sessions as this cycle's evidence.
