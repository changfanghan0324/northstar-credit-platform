# Northstar v6 Claude Opus 5 High review

This is repository evidence of an adversarial model challenge. It is not
external approval, a regulatory opinion, or a replacement for the test and
production evidence recorded for each phase.

## v6-01 — Money scale contract

Date: 2026-08-08
Model: `claude-opus-5` (High effort; no tools; independent supplied-summary review)

### Initial challenge

- Session: `606598e7-85f1-4dbe-9add-33b244ee57ac`
- Verdict: **not acceptable to deploy as first evidenced**.
- Main challenges: prove legacy-row status, bound the JSON/API amount contract,
  define scale-switch semantics, prevent coarse-scale precision loss, state
  per-scale precision, and add shared TypeScript/Python golden vectors.
- Usability follow-up: declare the accepted Excel grammar instead of silently
  guessing accounting or locale-specific tokens.

### Codex response

- Confirmed the server-side `MoneyValue.amount_minor` safe-integer bound and
  added a regression test at `MAX_SAFE_INTEGER + 1`.
- Documented that the v5 canonical-minor-units resolver release and the
  enforced temporary Portfolio Demo Mode leave no durable pre-v6 customer
  corpus to backfill; future unversioned legacy imports are rejected.
- Made scale changes presentation-only: canonical amounts remain in state and
  are re-rendered with BigInt; rendered text is never re-parsed by a scale
  selector.
- Added the explicit USD display precision table (whole 2, thousands 5,
  millions 8), reject-not-round behavior, standard-decimal Excel grammar, and
  loss-averse rejection of ambiguous accounting tokens.
- Added shared vectors at `tests/fixtures/money_scale_vectors.json`, consumed
  by Python and TypeScript, including arbitrary-cent millions values and a
  negative vector. Playwright now proves repeated scale changes and direct
  versus paste parity.

### Re-challenge

- Session: `728dc361-bd7d-4459-b287-00894cb99a96`
- Verdict: **PASS — v6-01 approved for production**.
- Remaining P1/P2 follow-ups: bounds for computed aggregate outputs, broader
  idiomatic Excel accounting grammar, explicit negative safe-bound vector,
  fixture count assertions, module-scoped coverage reporting, and a broader
  browser matrix. Claude explicitly classified these as non-gating for the
  v6-01 scope because the current behavior fails safe and the aggregate case
  is unreachable in the enforced Portfolio Demo Mode profile.

The first challenge and the re-challenge were both supplied-summary reviews;
they did not inspect the repository or production directly. Their claims are
therefore paired with the executable tests, build output, and production smoke
check for this phase.

## v6-02 — Financial lineage and FY/YTD consistency

Date: 2026-08-08
Model: `claude-opus-5` (High effort; independent adversarial review)

### Initial challenge

- Session: `60d3c93c-0f18-4c8d-a235-bea947f64253`
- Verdict: **FAIL — release blocked pending remediation**.
- P0: a blocked `scheduled_principal` source had no explicit propagation
  contract; DSCR and dependent decision outputs could otherwise be overstated.
- P1: duration-only YTD comparability, missing-prior/FY-only behavior, stale
  legacy precedence, default propagation, and insufficient UI window evidence.

### Codex response

- Replaced the arbitrary YTD fallback with a fail-closed named window. Prior
  YTD must be a strict FY subset with matching fiscal start and period-end
  month/day; missing or degenerate windows block.
- Added immutable snapshot `source_window` IDs and period-end dates plus the
  applied bridge formula. Current YTD remains the sole balance-sheet and
  snapshot `period_end` source.
- Added `blocked_authority_fields` and explicit propagation: blocked
  scheduled principal makes the analysis non-approvable, DSCR blocked, capacity
  zero, forecast DSCR/maturity outputs blocked, and reverse stress non-converged.
- Exposed selected window, dates, formula, authority map, and blocked fields in
  the bilingual Analyst/Guided financial-spreading UI. Added wrong-cut,
  missing-window, and blocked-propagation tests.

### Re-challenge

- Session: `9be6e487-9218-424f-a06c-bf811760802c`
- Verdict: **PASS — v6-02 approved for production**.
- Non-gating watch item: 52/53-week fiscal-calendar duration checks should be
  extended in a later hardening pass; the current month/day rule is correct for
  the calendar-fiscal contract. The intentionally skipped mobile money-scale
  test remains named and justified in the release evidence.
