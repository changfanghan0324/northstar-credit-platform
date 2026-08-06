# Northstar Credit Platform

**Language:** [English](README.md) | [繁體中文](README.zh-TW.md)

> Should we lend to this company? If yes, how much—and under what terms?

Northstar is a full-stack, educational corporate-credit underwriting workspace. It
connects normalized borrower and facility inputs to financial ratios, a transparent
credit score and grade, debt capacity, three-year stress scenarios, covenant
headroom, a rule-based lending recommendation, proposed terms, and a deterministic
credit-memo PDF.

## Public product

- Website: https://northstar-credit-platform.vercel.app
- English: `/`
- Traditional Chinese: `/zh-TW/`
- Three synthetic cases: stable manufacturer, cyclical distributor, and software
  services
- Workspace: Overview, Inputs, Financials, Debt Capacity, Risk, Stress & Covenants,
  Decision & Terms, and Credit Memo
- Modes: Guided and Analyst are two presentations of the same persisted inputs and
  calculated outputs

All displayed borrower data is synthetic. Northstar is an educational demonstration,
not a bank, rating agency, credit opinion, or lending commitment.

## Architecture

```text
Next.js 16 + strict TypeScript
            │
            ▼
FastAPI + Pydantic contracts
            │
            ▼
credit_app orchestration ── versioned YAML policy
            │
            ▼
Decimal-safe credit_engine
            │
            ▼
SQLAlchemy repository + Alembic migrations
```

Production accepts a PostgreSQL connection through `DATABASE_URL`. Local and
ephemeral demonstration environments use a SQLite fallback in `/tmp`; public cases
are anonymous and session-scoped. The `/runtime` endpoint and case-list banner state
whether persistence is durable or temporary. Monetary values cross every boundary as
integer minor units, while ratio values are serialized as decimal strings.

## Run locally

Python API:

```sh
PYTHONPATH=packages/credit_engine:packages/credit_app:packages/policy:apps/api \
  .venv-rebuilt/bin/uvicorn northstar_api.main:app --reload
```

Web app:

```sh
cd apps/web
pnpm install
pnpm dev
```

The development web app uses `http://127.0.0.1:8000` through
`apps/web/.env.development`. Production uses same-origin API rewrites.

## Verification

```sh
PYTHON_BIN=.venv-rebuilt/bin/python ./scripts/verify
```

The current delivery passes 79 Python tests with 99.54% branch-aware engine
coverage, Ruff lint and formatting, strict Mypy, strict TypeScript, ESLint, and a
Next.js production build. Browser QA covers the English and Traditional Chinese
homepages, a 390px mobile viewport, sample-case opening, custom-case creation,
session isolation, Guided/Analyst value equality, stress and covenant rendering, and
memo PDF generation.

## Documentation

- [Methodology](docs/methodology.md)
- [Recovery audit](docs/architecture/recovery-audit.md)
- [Data model](docs/architecture/data-model.md)
- [Design system and concept fidelity](docs/product/design-system.md)
- [Corrective decision log](docs/collaboration/decision-log.md)
- [Claude Opus 5 High configuration evidence](docs/collaboration/model-config.md)
- [Independent Claude review](docs/collaboration/corrective-debate-claude.md)
- [v3 corrective audit](docs/audits/pre-correction-audit.md)
- [v3 Claude review and Codex response](docs/collaboration/v3-claude-opus-5-review.md)

The independent collaboration record is repository evidence only; it is deliberately
not used as a product-interface marketing claim.
