# Debt reconciliation contract

Status: v6-03 implementation contract

## One selected debt basis

Every analysis produces one typed `DebtReconciliationView`. It retains the
balance-sheet gross debt, instrument gross debt, scheduled principal, implied
interest, reported interest, differences, tolerances, status, explanation, and
residual treatment. It also publishes the selected source and the exact debt,
scheduled-principal, and interest values consumed downstream.

The selected source is one of:

- `balance_sheet_aggregate` — no instrument schedule was supplied; aggregate
  balance-sheet debt and reported debt service remain explicit;
- `instrument_schedule` — the instrument schedule reconciles to balance-sheet
  debt within policy tolerance;
- `partial_schedule_with_residual` — a governed long-term schedule is combined
  with aggregate current/lease debt, and the unscheduled residual remains
  outstanding rather than being silently amortized;
- `blocked_mismatch` — a material debt or interest mismatch prevents
  decisioning.

Every instrument schedule must declare `schedule_completeness`. An unspecified
or mixed declaration blocks reconciliation. A declared partial schedule is
accepted only for the governed long-term-debt coverage pattern and only while
the unscheduled residual is no more than 20% of balance-sheet debt; otherwise
it is blocked. The 20% ceiling is a conservative governance threshold: a
residual above one-fifth of gross debt is too large to support a partial
schedule without a material risk of omitted obligations. The exact boundary
is accepted and tested. This prevents an omitted instrument from being
mistaken for a benign residual.

Leverage, DSCR, interest coverage, capacity, stress, maturity, memo, and PDF
outputs consume the same selected debt, scheduled-principal, and reported
interest values. Implied instrument interest is retained for reconciliation and
diagnostics; it does not silently redefine a contractual coverage test. Stress
shocks use instrument floating principal when a complete schedule is known. In
aggregate mode, all unclassified debt is conservatively treated as floating;
in partial mode, instrument floating principal plus the unclassified residual
is shocked. Fixed-rate debt is not repriced by a rate shock. The object repeats
the selected source for leverage, stress, and maturity and validates that those
labels cannot diverge. A blocked reconciliation propagates to blocked
DSCR/capacity/covenants/reverse stress outputs; it is never coerced to zero for
ratio math.

Aggregate and partial modes are visible in the API, financial-spreading UI,
memo, and PDF. Partial mode states exactly how residual debt is treated.
Residual maturity is a distinct, labeled unknown state until a contractual
maturity is supplied; maturity testing is blocked rather than placing the
residual into an invented bucket.
