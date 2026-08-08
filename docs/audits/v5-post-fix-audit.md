# Northstar v5 post-fix audit

Date: 2026-08-08
Scope: Portfolio Demo Mode only. No real borrower, bank, rating-agency, market-quote, regulated, or lending-commitment claim is made.

## Fixed and verified

- Exact integer minor-unit contract: display scale is metadata; the browser/import boundary normalizes once; the resolver does not multiply again. Whole/thousands/millions no-double-scale coverage is explicit.
- FY/YTD flows use FY + current YTD − prior YTD. Point-in-time balance-sheet lines use current YTD, with separate flow and balance source lineage in the immutable snapshot.
- Non-empty invalid spreads block decision-critical outputs and cannot silently reuse legacy values. Snapshot hash, resolver version, source authority, warnings, and blocking issues are retained.
- Debt reconciliation is typed as reconciled, immaterial difference, blocked, or governed aggregate/partial mode. A material unexplained mismatch blocks grade, pricing, and decision outputs.
- Approved itemized adjustments validate evidence, reviewer, recurrence, magnitude, and explicit EBITDA/EBIT/CFADS impacts. Draft/rejected entries do not change outputs.
- `ResolvedFacilityMechanics`, `RateDecisionView`, bullet exit/maturity test fields, revolver/ABL commitment-versus-drawn availability, configurable other-collateral haircuts, and typed zero-exposure facility protection are exposed in the result contract.
- Declines suppress active-loan conditions/monitoring and unsecured outputs do not claim collateral repayment support.
- Guided Mode accepts percentage notation, reports completion from required valid fields, exposes template provenance/reset actions, and uses a narrow status live region.
- Methodology now describes the five v5 behavior groups and keeps Portfolio Demo Mode limitations explicit.

## Evidence

- Python unit/integration suite: 108 passed.
- Total coverage: 92.13% (required threshold 90%).
- Ruff, strict Mypy, TypeScript, ESLint, and Next.js production build: passed.
- Added `tests/unit/test_v5_logic_contract.py` for scale, FY/YTD lineage, and debt mismatch blocking.

## Accepted limitations

The product remains a synthetic portfolio demonstration. It does not connect to banks, credit bureaus, ratings, live market data, production identity, durable multi-tenant storage, or regulated decision workflows. Instrument schedules are optional; when omitted, the result explicitly uses aggregate mode. Browser and production smoke/PDF/accessibility evidence must be refreshed after each deployment.
