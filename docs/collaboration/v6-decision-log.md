# Northstar v6 decision log

## v6-01 — Money scale contract

Date: 2026-08-08
Status: implementation complete; phase review complete; production check pending

Decision: normalize `whole`, `thousands`, and `millions` exactly once at the
browser/import boundary. Store actual USD cents in `MoneyValue.amount_minor`;
keep `FinancialPeriod.scale` as presentation/import metadata. Use BigInt for
scale-aware redisplay and reject values that exceed the JavaScript safe integer
range after normalization.

Evidence:

- `apps/web/lib/money.ts` owns `normalizeMoneyInput` and
  `formatMoneyAtScale`.
- `apps/web/components/workspace/FinancialSpreadEditor.tsx` uses the same
  normalizer for direct entry and Excel paste.
- `docs/architecture/money-scale-contract.md` is the API and UI contract.
- `tests/fixtures/money_scale_vectors.json` is consumed by Python and
  TypeScript tests.
- Claude Opus 5 High initial challenge:
  `606598e7-85f1-4dbe-9add-33b244ee57ac`.
- Claude Opus 5 High re-challenge PASS:
  `728dc361-bd7d-4459-b287-00894cb99a96`.

Follow-ups carried to later v6 work: computed-output safe bounds, broader
Excel accounting grammar, explicit negative-bound fixture, fixture parity
assertions, and module-scoped coverage reporting.
