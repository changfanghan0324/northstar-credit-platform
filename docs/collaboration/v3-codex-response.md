# Codex response to v3 Claude review

Date: 2026-08-05  
Author: Codex  
Required re-reviewer: Claude Opus 5 (`claude-opus-5`, high effort)

## Accepted and implemented

- Ratio values now preserve typed `valid`, `missing_input`,
  `invalid_denominator`, `not_meaningful`, `blocked`, and
  `policy_not_applicable` states. Critical blocked values prevent a final grade.
- Capacity exposes per-constraint applicability and status. Collateral is excluded
  for unsecured facilities. The decision priority declines zero supported exposure.
- Active leverage, DSCR, interest coverage, maturity, liquidity, reporting-currency,
  and positive-exposure rules are returned as explicit policy checks.
- Each scenario contains beginning debt, new facility, average debt, interest-driven
  cash generation, scheduled/optional paydown, cash shortfall, revolver draw, ending
  debt/cash, and refinancing need for three years.
- Reverse stress uses bounded bisection and exposes its bracket, tolerance, residual,
  iteration count, method, interpretation, and convergence state.
- Confidence is dynamic, numeric, and accompanied by drivers, penalties, improvement
  actions, and an explicit synthetic-data notice.
- The API now uses a server-issued cryptographic HttpOnly cookie in public deployment;
  a header override exists only under Pytest or an explicit local test setting. It
  applies ownership, quotas, request/PDF limits, payload caps, CORS, request IDs, and
  structured errors.
- Memo PDFs paginate, use human currency, provide executive/detailed and English/
  Traditional Chinese variants, and use validated slugs for filenames.
- The input hash now binds case data, policy version/hash, and engine version.

## Modified or constrained

- PostgreSQL remains the only durable production design, but the connected Supabase
  account currently has no project. The public runtime therefore reports
  `temporary_session` instead of making a false persistence claim. No paid database
  resource was created without user authorization.
- Anonymous request limiting is session-based. A trusted-proxy IP limiter remains an
  infrastructure enhancement because accepting arbitrary forwarding headers would
  introduce a spoofing path.
- The migration provides normalized domain tables and version/audit records; runtime
  JSON snapshots remain for backward-compatible deterministic reconstruction.

## Verification after required-fix round 1

- 79 Python tests pass, including zero/negative-EBITDA blocking, debt identities,
  responsive covenant packages, TTL enforcement, stale duplicates, and PDF encoding.
- Branch-aware pure-engine coverage is 99.54%.
- Ruff lint/format, strict Mypy, ESLint, strict TypeScript, and the Next.js production
  build pass through `./scripts/verify`.
