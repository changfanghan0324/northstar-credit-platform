# Corrective Recovery Debate — Claude Review

Date: 2026-08-04
Reviewer: Claude Opus 5 (`claude-opus-5`, high effort), independent non-author
Claude Code: `2.1.221`
Session: `ae81cc80-46bf-436f-8644-d43f371ade57`
Provider recorded by `modelUsage`: `firstParty`
Disposition: approved with the amendments below

## Accepted points

1. Preserve `packages/credit_engine` unchanged and pure; adapters go around it and
   formulas never move into TypeScript.
2. Put scorecard, capacity, scenarios, covenants, decision, and memo assembly in pure
   `packages/credit_app`, not FastAPI handlers.
3. Add versioned policy YAML plus schema and hash.
4. Serialize integer minor units for money and decimal strings for ratios.
5. Use a `CaseRepository` protocol between orchestration and storage.
6. Guided is the default and Analyst details are additive.
7. Remove the 40-borrower portfolio and ten-page Power BI specification from the
   corrective completion path; demote the full Excel workbook to reconciliation work.
8. Health-check frontend and API independently before moving the production alias.
9. Assert that displayed DSCR is byte-equal to the API value.

## Required amendments

- PostgreSQL models, Alembic migrations, and a Postgres repository integration test are
  Slice 1B exit criteria; in-memory storage is a test double only.
- Existing Task 1 re-review evidence must be distinguished from the new, still-unbuilt
  scorecard/capacity verification gate.
- Supersede conflicting audience, scope, and public-write decisions explicitly.
- Keep generated shared contracts and a drift check.
- Express Guided/Analyst behavior as testable materiality and equality invariants.
- Begin product styling only after Slice 1B completes the case.
- Extend value equality from DSCR to every displayed numeric and PDF output.
- Seed demo cases as inputs only and calculate every output through the API.
- Use one canonical `docs/collaboration/model-config.md`; no “Claude approved” product
  claim.
- Use deterministic memo templates for the first release.

## Resolved audience

Use one session-phased product. The public surface and the first 90 seconds of Overview
serve a non-specialist evaluator. Everything after the first click is optimized for a
junior credit analyst while remaining legible to the evaluator. A banking professional
is the secondary persona served by Analyst annotations. Borrower self-service remains
out of scope because the product expresses lender judgment.

## Resolved Guided and Analyst invariants

1. **Materiality:** covenant breaches, first breach period, critical missing-data blocks,
   adverse not-meaningful states, policy exceptions, binding capacity, and the decision
   are visible in Guided mode without expansion. Derivations may collapse; adverse
   conclusions may not.
2. **Equality:** for the same case, the reachable `(metric_id, value)` set and every
   export are identical across modes. Analyst may add only formula ID, components,
   reason code, score band, weighted contribution, source period, and lineage.

## Resolved architecture

```text
packages/credit_engine   pure numeric source of truth, unchanged
packages/credit_app      pure scorecard, capacity, scenarios, covenants,
                         decision, and memo assembly
packages/policy          versioned YAML, schema, and hash
packages/contracts       generated TypeScript types from OpenAPI, drift-checked
apps/api                 FastAPI orchestration, serialization, repositories,
                         transactions, and timestamps only
apps/web                 Next.js App Router, strict TypeScript, presentation only
```

Calculation runs are immutable and stamped with engine version, policy version and hash,
input hash, and timestamp. No partial result persists after failure. Public case creation
is session-scoped and ephemeral, with TTL, no cross-session reads, no PII fields, rate
limits, payload caps, and an explicit statement that there is no account and data expires.

## Resolved first milestone

**Slice 1A — prove the pipe:** policy load and hash, adapter and scorecard,
leverage/DSCR/policy capacity and binding constraint, create/analyze/read endpoints,
homepage and computed Overview, missing-critical-data block, immutable calculation-run
stamps, and value-equality E2E.

**Slice 1B — complete the case:** Base/Downside/Severe projections, covenant headroom and
first breach, decision, terms, mitigants, deterministic one-page memo PDF, and guided
save/reload against PostgreSQL. Both corrective E2E paths and PDF-to-calculation-run
numeric equality are milestone exit criteria.

The 1A/1B split is implementation order, not scope deferral. Product styling begins only
after 1B exits.

## Highest risks

1. Persistence deferral becoming permanent.
2. New scorecard/capacity logic being treated as covered by the earlier Task 1 review.
3. Display-layer scaling or rounding creating split-brain numbers despite no formulas.
4. Scope overrun across currently absent API, UI, persistence, and decision layers.
5. Abuse or misleading security expectations on an unauthenticated public write surface.

Watch items: professional Traditional Chinese terminology, memo language inventing facts,
and residual technical-validation marketing on the homepage.

`CLAUDE_CORRECTIVE_DEBATE_COMPLETE`
