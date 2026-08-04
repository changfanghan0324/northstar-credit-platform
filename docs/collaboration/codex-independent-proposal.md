# Codex Independent Proposal

Status: independent draft, written before reading Claude's proposal  
Date: 2026-08-03  
Author: Codex

## Product thesis

Build the smallest complete underwriting journey that proves credible financial engineering: open a synthetic case, understand the decision, inspect deterministic evidence, change stress assumptions, and generate a traceable memo. The portfolio view and reference workbook reinforce the project story but remain separate from the guided case workflow.

## Audience

- Primary: junior credit or banking analyst. They need a credible spread, transparent calculations, stress results, and a memo, but still benefit from guided interpretation.
- Secondary: recruiter or interviewer. They need a polished five-minute demonstration and visible technical depth.
- Secondary: finance student or guided non-expert. Plain-language labels and progressive disclosure should let them understand the recommendation without reading every formula.
- Explicitly deferred as a primary persona: portfolio risk manager. Portfolio analytics is a supporting demonstration surface, not the main application.

## MVP scope

Implement three synthetic cases, a six-step guided review, three historical periods plus LTM, adjustments, debt schedule, deterministic ratios, explainable score, facility assessment, debt capacity, three three-year stress scenarios, reverse stress, covenants, a recommendation engine, one-page and detailed memo views, Excel reconciliation, and a 30-50 borrower synthetic portfolio.

Defer live SEC ingestion, authentication, multi-user approval workflow, real Power BI binaries, and production cloud deployment until the local product and calculations pass. Provide documented extension points and a Power BI star-schema specification. Do not fake live integrations.

## Homepage and navigation

- Header: Home, Start Review, Cases, Portfolio, Methodology.
- Hero: one direct question, one sentence, primary CTA, sample-case CTA.
- Below: a single selected sample decision strip with three outcomes; four-step workflow; at most five recent cases; compact trust and disclaimer block.
- Visual direction: editorial banking brief rather than a dashboard wall—white background, deep ink/navy type, restrained copper accent, crisp rules, modest radii, tabular figures, and generous whitespace.
- Case shell: Summary, Financials, Risk, Stress, Terms, Memo. Guided mode is default; Analyst mode reveals existing detailed components instead of duplicating routes.

## Architecture

- Monorepo with `apps/web` (Next.js App Router + TypeScript), `apps/api` (FastAPI + Pydantic + SQLAlchemy + Alembic), `packages/credit_engine` (pure Python domain functions), `packages/policy` (versioned YAML), and `packages/shared_types` (generated/open schemas where useful).
- PostgreSQL is the production database. Tests use a disposable database-compatible configuration; no production behavior depends on an in-memory store.
- Domain calculations are pure, deterministic, versioned, and independently testable. The API orchestrates persistence and schemas but does not duplicate formulas.
- Server-render stable summaries, isolate interactive scenario controls as client components, and lazy-load heavy charts/memo rendering.
- No authentication in the portfolio MVP. Mutating endpoints are clearly demo-scoped, validated, rate-limit-ready, and protected by safe defaults and audit records.
- Printable HTML is the canonical memo surface; a backend PDF export provides the portable artifact.

## Financial model decisions

- Use policy-driven thresholds in YAML; every result carries model version, policy version, timestamp, source date, confidence, and overrides.
- Score borrower risk separately from facility protection. The decision engine consumes both but never hides a weak obligor score.
- Block grade and approval when critical data is missing. Return typed non-meaningful results for zero or negative denominators where the ratio has no valid interpretation.
- Debt capacity is the minimum of request, leverage, DSCR, collateral, and policy capacity. Amortizing DSCR capacity uses present-value annuity mechanics.
- Scenarios are deterministic and labeled as such. Severe stress may improve only when an explicitly documented offsetting input makes that outcome mathematically valid.

## Initial ownership proposal

- Codex authors: repository scaffold, credit engine, policy configuration, database/API, golden tests, Excel reference model, integration and security harness.
- Claude authors: product UX specification, Next.js design system and primary UI surfaces, memo narrative templates, accessibility implementation, usability documentation.
- Shared by alternating authors: scenario UX, decision presentation, sample cases, project documentation.
- Every changed file is reviewed by the non-author at diff-hunk level; required fixes are re-reviewed.

## First implementation task

Codex authors the pure financial primitives (typed money/ratio results, debt, EBITDA, CFADS, debt service, coverage, liquidity, and capacity helpers) with edge-case tests. Claude independently reproduces formulas, reviews every line, and supplies required fixes before the module is accepted.

## Main risks

- Overbuilding breadth before validating formula invariants.
- Letting polished UI imply more data confidence than synthetic inputs support.
- Spreadsheet/Python divergence.
- Treating an unavailable deployment or Power BI desktop binary as if it were complete.
- Review evidence becoming ceremonial; reviews must cite concrete hunks, tests, and dispositions.
