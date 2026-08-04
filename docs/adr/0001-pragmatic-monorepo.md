# ADR 0001 — Pure credit engine in a pragmatic monorepo

Status: accepted  
Date: 2026-08-03  

## Context

The product needs deterministic financial logic, persistence, an accessible web workflow, independent Excel reconciliation, and a simple portfolio deployment. The primary engineering risk is split-brain formulas or infrastructure that obscures review.

## Decision

- `apps/web`: Next.js App Router and TypeScript.
- `apps/api`: FastAPI, Pydantic, SQLAlchemy, Alembic.
- `packages/credit_engine`: pure Python, no I/O, database, web framework, or network imports.
- `packages/policy`: versioned YAML plus schema and hash.
- PostgreSQL is the only persistent database.
- API-generated typed fixtures provide a read-only frontend demonstration when the API is absent.
- Calculation runs are immutable and carry engine version, policy version, input hash, timestamp, source date, confidence, and overrides.

## Consequences

Positive: formulas are independently testable, Excel-reconcilable, and reviewable; one repository keeps deployment understandable. Negative: cross-language types require generation; Postgres requires an external service for the full local stack. Fixture drift and shared-type staleness are blocked by verification scripts.

## Rejected alternatives

Microservices, GraphQL, SQLite persistence, duplicated TypeScript formulas, machine-learning decisions, and a client global-state framework were rejected as unnecessary or integrity-reducing.
