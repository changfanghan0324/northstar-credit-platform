# Decision Log

## DEC-001 — Product and audience (superseded by DEC-009)

Date: 2026-08-03 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`)

- Decision: optimize for a junior credit analyst, with recruiter/interviewer and finance student as secondary users.
- Alternative rejected: small-business owner as primary, because the platform requires underwriting judgments the borrower cannot make and does not own.
- Reversibility: high; copy and onboarding can be widened later without changing the financial core.
- Owner/reviewer: Codex / Claude Opus 5.

## DEC-002 — MVP scope (superseded by DEC-011)

Date: 2026-08-03 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`)

- Decision: implement the complete transparent case spine and defer live SEC fetching, auth, ML/Monte Carlo, AI narrative, full forecast balance sheet, and a `.pbix` binary.
- Replacement: synthetic fixture packs with full lineage, deterministic templates, debt/cash roll-forward, ten-page Power BI specification, one in-app portfolio page.
- Risk: breadth can still overrun; every feature must strengthen the trace from inputs to decision.
- Reversibility: deferred adapters can be added behind stable interfaces.

## DEC-003 — Architecture

Date: 2026-08-03 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`)

- Decision: pragmatic monorepo; pure I/O-free Python credit engine; FastAPI orchestration; PostgreSQL persistence; Next.js frontend; versioned YAML policy; generated shared schemas.
- Alternative rejected: microservices, GraphQL, client global-state frameworks, SQLite persistence.
- Risk controls: import boundaries, immutable calculation runs, input hashes, Postgres integration tests, fixture drift checks.

## DEC-004 — Numeric and missing-data contract

Date: 2026-08-03 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`)

- Decision: integer minor units for money, ISO currency/exponent, Decimal ratio math quantized to four decimals with `ROUND_HALF_UP`, half-open policy bands, typed reason codes, no implicit FX.
- Failure modes addressed: threshold flips from binary floats, JPY scaling errors, favorable and adverse NM states conflated, partial multi-currency calculations.

## DEC-005 — Two-level experience

Date: 2026-08-03 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`)

- Decision: one additive-only `Analyst details` preference. No duplicated application, hidden values, or export differences.
- Test: metric-value set and exports are identical across states; annotations are the only permitted difference.

## DEC-006 — Deployment security (superseded by DEC-010)

Date: 2026-08-03 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`)

- Decision: local full-stack supports writes; public deployment is read-only, fixture-backed, and route-allowlisted.
- Alternatives rejected: unauthenticated public writes; pretending authentication exists.

## DEC-007 — Independent verification

Date: 2026-08-03 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`)

- Decision: methodology is the cited contract; Claude counter-signs it. Codex contract/invariant tests precede implementation. Numeric goldens and Excel formula specs are hash-committed before code review and then revealed.
- Risk: shared methodology can be wrong.
- Control: per-formula master-prompt citations and Claude counter-signature before implementation.
- Review outcome: initial counter-signature was withheld for lease double-counting, ambiguous leverage basis, missing exact covenant value, an incomplete Excel capacity chain, and false-green architecture tests. Codex applied the required fixes; re-review is mandatory before implementation.

## DEC-008 — Excel build sequencing

Date: 2026-08-03 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`)

- Decision: author and hash the independent Excel formula specification before the engine, but generate the fully styled 20-tab workbook after the API/frontend foundation.
- Alternative: build the complete workbook before the Python engine, as the phase ordering suggests.
- Rationale: early formulas/goldens preserve independent verification; later workbook generation avoids front-loading layout work that does not unblock engine correctness.
- Risk: the final workbook could slip; it remains a completion gate and the verify plan keeps reconciliation mandatory.
- Reversibility: high; workbook generation can move earlier without changing formulas.

## DEC-009 — Corrective audience model

Date: 2026-08-04 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`, high)

- Decision: the public surface and first 90 seconds of Overview serve a non-specialist
  evaluator; the workspace depth target is a junior credit analyst; professional users
  receive additive Analyst annotations.
- Guided mode never hides material adverse facts. Guided and Analyst expose identical
  metric/value sets and exports.
- Evidence: `corrective-debate-codex.md` and `corrective-debate-claude.md`.

## DEC-010 — Public session persistence and security

Date: 2026-08-04 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`, high)

- Decision: public unauthenticated cases are session-scoped and ephemeral, TTL-expired,
  rate-limited, payload-capped, and inaccessible across sessions. The UI states that
  there is no account and data expires.
- PostgreSQL is the only durable multi-user store. In-memory repositories are test
  doubles only.
- No PII fields or authentication claim appear in the public demo.

## DEC-011 — Corrective scope and vertical slices

Date: 2026-08-04 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`, high)

- Decision: remove the 40-borrower portfolio and Power BI specification from the
  corrective completion path. Demote the full Excel workbook to reconciliation work.
- Slice 1A proves engine-to-API-to-UI equality. Slice 1B immediately adds scenarios,
  covenants, decision, memo, guided save/reload, and PostgreSQL.
- Styling begins only after Slice 1B exits. The split is ordering, not scope deferral.

## DEC-012 — API numeric contract and calculation runs

Date: 2026-08-04 · Owner: Codex · Reviewer: Claude Opus 5 (`claude-opus-5`, high)

- Money uses integer minor-unit objects with currency and exponent; ratios use decimal
  strings; the frontend performs no financial arithmetic.
- Generated TypeScript contracts are drift-checked against OpenAPI.
- Calculation runs are immutable and include engine version, policy version and hash,
  input hash, and calculation timestamp. Failed calculations persist no partial results.
