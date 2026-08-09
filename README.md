# Northstar Credit Platform

**Language:** [English](README.md) | [繁體中文](README.zh-TW.md)

> Should we lend to this company? If yes, how much—and under what terms?

Northstar is a full-stack, educational corporate-credit underwriting workspace. It
connects normalized borrower and facility inputs to financial ratios, a transparent
credit score and grade, debt capacity, independent facility protection, an optional
borrowing base, three-year stress scenarios, six numerical reverse-stress solvers,
transparent indicative pricing, proposed terms, and localized credit-memo PDFs.

## Public product

- Website: https://northstar-credit-platform.vercel.app
- English: `/`
- Traditional Chinese: `/zh-TW/`
- Three synthetic cases: stable manufacturer, cyclical distributor, and software
  services
- Workspace: Overview, Inputs, Financials, Debt Capacity, Facility Protection, Risk,
  Stress & Covenants, Decision & Terms, and Credit Memo
- Modes: Guided and Analyst are two presentations of the same persisted inputs and
  calculated outputs
- Analyst entry supports multi-period income statements, balance sheets, cash-flow
  statements, CSV templates, Excel paste, period copy/remove, reconciliation, and
  explicit LTM methodology.
- Normalization adjustments and qualitative business-risk factors require rationale,
  evidence, source, and review state before they can support a final grade.
- The canonical financial resolver records one immutable reported/derived LTM snapshot;
  unresolved non-empty spreads block final grading and pricing instead of silently
  reusing stale legacy values. Term, bullet, partial-amortization, and revolver
  mechanics are represented explicitly in stress scenarios.

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

Northstar intentionally operates in **Portfolio Demo Mode (Mode A)**. A PostgreSQL
connection can be supplied through `DATABASE_URL`, while local and ephemeral demo
environments use a SQLite fallback in `/tmp`. Public cases are synthetic,
anonymous, session-scoped, quota-limited, and expire after seven days. The `/runtime`
endpoint states these limitations. Monetary values use exact integer minor units,
with a contract and browser parser that reject values outside JavaScript's safe
integer range, invalid grouping, scientific notation, and excess precision. Ratio
values are serialized as decimal strings.

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

Verification covers Python unit/integration tests with branch-aware application
coverage, Ruff lint and formatting, strict Mypy, strict TypeScript, ESLint, a Next.js
production build, Playwright desktop/mobile flows, and axe WCAG checks. Browser QA
covers English and Traditional Chinese, Guided/Analyst workflows, multi-period
spreading, facility protection, solver metadata, keyboard navigation, localized
error routes, and executive/detailed memo PDFs. PDF QA renders every page to images
and uses an embedded open-source Noto Sans TC font for Traditional Chinese.

## Documentation

- [Current release status](docs/release-status.md)
- [v6 pre-fix self-audit](docs/audits/v6-pre-fix-audit.md)
- [v6 post-fix self-audit](docs/audits/v6-post-fix-audit.md)
- [Methodology](docs/methodology.md)
- [v6 model-consistency hardening prompt](docs/prompts/Northstar_v6_Final_Credit_Model_Consistency_Prompt.md)
- [Money scale contract](docs/architecture/money-scale-contract.md)
- [Financial lineage contract](docs/architecture/financial-lineage-contract.md)
- [Debt reconciliation contract](docs/architecture/debt-reconciliation-contract.md)
- [Facility mechanics contract](docs/architecture/facility-mechanics-contract.md)
- [Bullet exit and maturity contract](docs/architecture/bullet-exit-contract.md)
- [Revolver and ABL mechanics contract](docs/architecture/revolver-abl-contract.md)
- [Provenance and completion contract](docs/architecture/provenance-completion-contract.md)
- [v6 Claude Opus 5 High review](docs/collaboration/v6-claude-opus-5-review.md)
- [v6 decision log](docs/collaboration/v6-decision-log.md)
- [Current model limitations](docs/release-status.md#current-limitations)
- [Test evidence](docs/release-status.md#verification-at-release-authoring)
- [Demo cases](data/demo_cases/)
- [Recovery audit](docs/architecture/recovery-audit.md)
- [Data model](docs/architecture/data-model.md)
- [Design system and concept fidelity](docs/product/design-system.md)
- [Corrective decision log](docs/collaboration/decision-log.md)
- [Claude Opus 5 High configuration evidence](docs/collaboration/model-config.md)
- [Independent Claude review](docs/collaboration/corrective-debate-claude.md)
- [v3 corrective audit](docs/audits/pre-correction-audit.md)
- [v3 Claude review and Codex response](docs/collaboration/v3-claude-opus-5-review.md)
- [Final product audit](docs/audits/final-product-audit.md)
- [Final model audit](docs/audits/final-model-audit.md)
- [Final UX audit](docs/audits/final-ux-audit.md)
- [Production deployment verification](docs/audits/final-deployment-verification.md)
- [Final Claude Opus 5 High review](docs/collaboration/final-review-claude-opus-5.md)
- [v4 independent audit](docs/audits/final-independent-audit-v4.md)
- [v4 implementation task board](docs/implementation-task-board-v4.md)
- [v4 Claude Opus 5 High challenge](docs/collaboration/v4-claude-opus-5-review.md)

### Historical review records

The v3/v4 audits, task boards, and debate logs above are retained as historical
evidence. The current product claim, test count, deployment, and limitations are
maintained only in [Current release status](docs/release-status.md).

The independent collaboration record is repository evidence only; it is deliberately
not used as a product-interface marketing claim.
