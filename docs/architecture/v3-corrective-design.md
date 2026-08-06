# v3 corrective architecture and model design

## Product boundary

Northstar is an educational, synthetic-data corporate credit workflow for finance students, junior analysts, small-business lenders, recruiters, and experienced reviewers. It is not a bank system of record and must not invite confidential data.

The system keeps one deterministic source of truth: typed Python input plus a versioned policy produces a versioned analysis. Guided and Analyst modes are projections of the same input and output, never separate calculations.

## Calculation contract

Every calculated value has one of six states: `valid`, `missing_input`, `invalid_denominator`, `not_meaningful`, `blocked`, or `policy_not_applicable`. A result also retains its plain and professional labels, reason, formula, source period, policy reference, direction, components, confidence factors, and model version.

Only `valid` values may enter numeric score bands or applicable capacity minima. Favorable not-meaningful states are explicit policy mappings; all other non-valid states are either adverse or block a final grade. Missing values never become numeric zero.

Capacity is a list of typed constraints. Each constraint includes method, amount, applicability, status, reason, formula/policy reference, and binding flag. The recommendation is the minimum valid applicable amount, capped by the request. Collateral is applicable only to a secured or asset-based structure with eligible collateral. No supported exposure has decision priority over ordinary approval/refer rules.

Stress uses an annual roll-forward with beginning debt, new facility, scheduled amortization, optional paydown, maturity/refinancing, ending debt, average debt, fixed/floating interest, base rate, floor, shock, cash, revolver availability/draw, shortfall, and covenant tests. Reverse stress repeatedly runs this complete forecast through a bounded bisection solver and records target, bounds, iterations, tolerance, residual, and convergence status.

## Persistence and ownership

The normalized model comprises cases, case versions, borrowers, loan requests, financial periods, normalized financials, adjustments, debt instruments, business-risk assessments, scenarios/assumptions, analyses, policy checks, capacity constraints, covenant recommendations/tests, decisions, memo versions, and audit logs.

The FastAPI service is the sole authority for ownership. A cryptographically random anonymous session token is set in an HttpOnly, SameSite=Lax cookie; a hashed identifier is stored server-side. Headers remain supported for deterministic integration tests but cannot default to a shared owner. Every case mutation records an audit event and increments a version. Analyses retain the exact input version/hash and become stale after any material edit.

PostgreSQL is required when durable persistence is advertised. Without `DATABASE_URL`, the app declares temporary-session mode and disables durable-persistence claims. Production uses a pooled PostgreSQL/Supabase connection with SSL and migration-controlled schema. Public Data API grants are not required; if tables live in Supabase `public`, RLS remains enabled as defense in depth.

## API surface

- `GET /runtime` — persistence mode, retention, limits, model/policy versions.
- `GET /demo-cases` and `GET /demo-cases/{slug}/template` — read-only templates; no persistence.
- `GET/POST /cases`, `GET/PATCH/DELETE /cases/{id}` — list/create/read/update/delete.
- `POST /cases/{id}/duplicate`, `/archive`, `/validate`, `/analyze`.
- `PATCH /cases/{id}/scenarios` — update scenario assumptions and mark stale.
- `GET /cases/{id}/analysis`, `/memo`, `/memo.pdf?locale=...&detail=...`.
- Structured errors include code, message, field, remediation, and request ID.

## Route map

- `/[locale]` — concise product entry and sample launcher.
- `/[locale]/app/cases` — list/search/filter/sort and lifecycle actions.
- `/[locale]/app/cases/new` — seven-step wizard and review gate.
- `/[locale]/app/cases/[id]/{overview,inputs,financials,capacity,risk,stress,decision,memo}`.
- `/[locale]/{methodology,technical-validation,about}`.
- Localized `not-found`, API error, offline, missing/expired, and stale states.

## Operational controls

Default anonymous limits are ten active cases, 60 requests/minute/session, five PDFs/hour/session, and a 1 MiB request body. CORS is restricted to configured production origins. Retention defaults to seven days and is disclosed. Delete is permanent and testable. Confidential-data warnings appear at entry and in every input flow.
