# Northstar v5 pre-fix audit

Date: 2026-08-08
Scope: Portfolio Demo Mode only; synthetic borrower data, anonymous temporary cases, educational outputs.

## Reproduced P0 issues

1. Scale round-trip: the Analyst browser editor multiplied a value entered in thousands/millions into actual minor units, while the resolver multiplied again using `FinancialPeriod.scale`. A value could therefore be double-scaled.
2. FY/YTD balance source: the FY + current YTD − prior YTD flow tuple is ordered `(FY, current YTD, prior YTD)`, but balance-sheet lines were read from `selected[-1]`, which selected prior YTD instead of the current point-in-time balance sheet.
3. Facility ambiguity: public templates did not explicitly declare amortization mechanics. A missing `amortization_years` could be interpreted as bullet by stress while the UI/request did not make the structure visible.
4. Adjustment authority: approved itemized EBITDA impacts were bridged, but explicit EBIT/CFADS impacts and magnitude controls were not fully carried through every downstream output.

## Additional findings

- Decision-critical fields in a non-empty spread needed a complete-source block rather than optional legacy inheritance.
- Debt schedule and balance-sheet debt had no typed reconciliation output.
- Facility protection used a denominator guard (`max(1, ...)`) that could turn zero supported exposure into misleading coverage.
- Public methodology and release navigation did not yet describe one v5 current truth.

The audit intentionally precedes visual redesign. It treats any unverified external/market/regulated use as out of scope.
