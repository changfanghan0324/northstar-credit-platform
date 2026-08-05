# Corrective Recovery Debate — Codex Proposal

Date: 2026-08-04
Author: Codex
Required reviewer: Claude Opus 5 (`claude-opus-5`, high effort)

## Audience

Design the first 90 seconds for a non-specialist evaluator who must understand the
lending decision quickly. After the first click, optimize the workspace for a junior
credit analyst while keeping explanations accessible to finance students and business
users. Borrower self-service remains out of scope because the product expresses lender
judgment.

## Guided and Analyst presentation

Keep one calculation and one case. Guided is the default presentation; Analyst details
are additive annotations and drill-downs. The toggle may never hide a breach, critical
missing-data block, adverse not-meaningful state, policy exception, displayed value, or
exported value.

## Architecture

- Preserve `packages/credit_engine` unchanged as the pure numeric source of truth.
- Add pure `packages/credit_app` modules for policy evaluation, scorecard, capacity,
  scenarios, covenants, decision, and memo assembly.
- Add versioned policy YAML and schema under `packages/policy`.
- Put only orchestration, serialization, repositories, timestamps, and transactions in
  `apps/api` (FastAPI).
- Put only presentation and interaction in `apps/web` (Next.js App Router, strict
  TypeScript). The frontend never computes a ratio, grade, capacity, breach, or decision.
- Serialize monetary amounts as integer minor-unit objects and ratios as strings.
- Define a `CaseRepository` protocol. In-memory persistence supports tests and the first
  vertical slice; PostgreSQL is the only durable multi-user store.
- Public unauthenticated creation is session-scoped and ephemeral, with TTL and no
  cross-session reads. No authentication claim is made.

## Vertical-slice sequence

Slice 1A proves the complete calculation pipe with one stable synthetic case:

1. Policy load and hash.
2. Engine adapter and scorecard.
3. Leverage/DSCR/policy capacity and binding constraint.
4. FastAPI case and analysis endpoints.
5. Next.js homepage and computed Overview.
6. An end-to-end assertion that displayed DSCR exactly equals the API string.

Slice 1B immediately completes the corrective prompt's first end-to-end case:

1. Base, Downside, and Severe projections.
2. Covenant headroom and first breach.
3. Decision, recommended terms, and mitigants.
4. One-page memo PDF.
5. Guided input/save/reload flow.

The split is an implementation order, not a scope deferral. Styling begins only after a
real computed grade and binding capacity render through the API.

## Scope recovery

Remove the 40-borrower portfolio and ten-page Power BI specification from the completion
path. Preserve their planning records but prioritize the corrective definition of done.
Keep the full Excel workbook as a later reconciliation artifact; the golden-case formula
harness is the near-term financial verification gate.

## Risks and controls

- Scope risk: never render placeholder financial outputs; blocked states are explicit.
- Split-brain risk: API-to-UI value-equality tests and no TypeScript formulas.
- Persistence risk: immutable calculation runs with input hash and versions.
- Localization risk: terminology review in both languages, not mechanical translation.
- Deployment risk: frontend and API are independently health-checked before the public
  alias changes.
