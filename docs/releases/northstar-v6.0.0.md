# Northstar v6.0.0 — Final Model Consistency Release

Release date: 2026-08-09
Production: https://northstar-credit-platform.vercel.app/
Mode: Portfolio Demo Mode

## What is frozen

Northstar v6.0.0 is the final eight-phase model-consistency hardening release.
Each phase was independently tested, challenged by Claude Opus 5 High, checked
in production, and committed separately:

1. canonical money scale contract;
2. FY/YTD financial lineage;
3. debt reconciliation;
4. resolved facility mechanics;
5. bullet exit and maturity testing;
6. revolver and ABL mechanics;
7. provenance and evidence-based completion; and
8. final independent audit and release documentation.

## Verification

- 133 Python tests passed; total coverage 93.30%.
- Strict Mypy, Ruff, formatting, TypeScript, ESLint, and Next production build
  passed.
- Playwright: 13 passed, one intentional mobile skip.
- Claude Opus 5 High final audit: PASS, no blocking findings.
- Production deployment `dpl_4scrQ5hLioEdH7GqLywNPNrn3xf7`: READY; English and
  Traditional Chinese routes, API health/runtime/demo endpoints, typed
  provenance/completion outputs, detailed PDFs, and browser Review UI verified.
- Vercel runtime errors in the final check window: none.

## Product boundary

This release remains synthetic, anonymous, temporary, educational Portfolio Demo
Mode. It is not a regulated credit decision, lending commitment, market quote,
official rating, or committee-ready banking system. Unsupported multi-currency
consolidation, best-effort instance-local limits, seven-day expiry, illustrative
pricing, and untagged PDF accessibility remain disclosed limitations.
