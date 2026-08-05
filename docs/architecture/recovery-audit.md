# Corrective Recovery Audit

Date: 2026-08-04
Baseline commit: `7b0c000` (`main`)
Source mandate: `/Users/peter/Downloads/Northstar_Corrective_Master_Prompt.md`

## Verified baseline

- `./scripts/verify` passes from the repository root.
- 54 unit tests pass.
- Branch-aware coverage is 99.53% (520 statements, one uncovered statement,
  124 branches, two partial branches).
- Ruff lint and format checks pass.
- Strict Mypy passes for the existing engine package.
- The working tree was clean before corrective implementation began.
- The public Vercel deployment is a bilingual static technical landing page, not
  an underwriting application.

## Preserved public engine surface

`packages/credit_engine` is a pure, I/O-free Python package and remains the financial
calculation source of truth. Its public surface currently includes:

- Decimal-safe `Money`, currency validation, normalization, aggregation, and scaling.
- Debt, cash, EBITDA, FCF, CFADS, and debt-service aggregations.
- Forty leverage, coverage, liquidity, cash-flow, trend, profitability, and return
  metrics.
- Typed `ok`, `nm`, `missing`, and `error` states with controlled reason codes.
- Exact and four-decimal ratio values, formula metadata, components, confidence, and
  corrective-action fields.

The architecture tests prohibit framework, database, network, time, random, JSON,
and binary-float dependencies inside the engine. That boundary remains mandatory.

## Product and application gaps

The repository does not yet contain:

- A scorecard or internal risk-grade engine.
- Policy loading and versioned thresholds.
- Debt-capacity, reverse-stress, scenario, covenant, decision, or memo services.
- Case/application schemas and adapters around the numeric engine.
- FastAPI endpoints, OpenAPI contracts, or service-layer transaction boundaries.
- PostgreSQL models, Alembic migrations, or calculation-run persistence.
- A Next.js application, shared TypeScript contracts, localized application routes,
  or Guided/Analyst workspace.
- Synthetic demo-case input packs calculated through a real application service.
- PDF memo generation, application tests, or end-to-end tests.

## Recovery conclusion

The validated engine is a strong foundation but represents only the numeric-metric
layer. Corrective work must add adapters and application services around it; it must
not copy formulas into TypeScript or weaken the existing contracts. The first vertical
slice should compute one synthetic case through a real API and expose overview, stress,
decision, terms, and memo output before broader UI work.
