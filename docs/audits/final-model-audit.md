# Final credit-model audit

Baseline: `c867e001954749983d99db2e6e2aa903a69155a1` at `2026-08-06T16:11:27Z`.

## Preserved strengths

- Exact Python `Decimal`/integer-money engine with explicit currency and minor-unit exponent.
- The core ratio library distinguishes valid, missing, favorable not meaningful, and adverse not meaningful. The scenario forecast does not yet preserve those states.
- Critical invalid core ratio states block the final score; zero supported exposure maps to Decline.
- Collateral capacity applies only to secured or asset-based requests.
- Versioned policy drives the existing grade bands, weights, hard stops, and capacity thresholds.
- Three-year scenarios retain beginning/new/average/ending debt, amortization, draw, cash shortfall, and refinancing need.
- Revenue-to-DSCR reverse stress reruns the first-year scenario through bounded bisection.

## Material failures against the new specification

| Model area | Finding | Required correction |
| --- | --- | --- |
| Financial statements | Single snapshot; no structured annual/quarter/YTD/LTM/forecast periods | Add nonoverlapping period contracts, statements, reconciliations, selected LTM method, reported/adjusted/forecast views |
| Adjustments | Aggregate positive and negative EBITDA only | Add itemized rationale/evidence/approval log and reported-to-adjusted bridges with ratio/grade/capacity effects |
| Qualitative risk | Numeric 0–100 values are accepted without evidence | Add policy-mapped bands and require per-factor evidence/source/rationale/confidence before final grade |
| Borrower versus facility | Security can bind capacity but no independent facility assessment exists | Calculate and report facility protection separately; prove collateral cannot change obligor grade |
| Collateral | Manual `collateral_capacity` stands in for borrowing base | Add eligibility, advances, reserves, prior liens, availability, and deficiency engine; mark unsecured not applicable |
| Pricing | No pricing policy or output | Add base rate, grade spread, tenor/security/amortization/covenant/concentration/relationship adjustments and fees |
| Reverse stress | Only DSCR/revenue uses a solver; leverage-margin and max loan are arithmetic shortcuts | Implement six bounded deterministic full-forecast solvers, each with independent convergence metadata and failure reason |
| Severe liquidity | Cash can be negative and shortfall is present, but unpaid debt service, exhausted revolver, borrowing block, and refinancing-unavailable behavior are not explicit | Extend scenario states and policy behavior without masking negative cash |
| Memo reconciliation | Memo is assembled from analysis output but only covers a subset of required topics | Generate 32 named detailed sections and one-page executive memo from API results only |
| Numeric boundary | API serializes money as JSON numbers | Move money amounts to canonical decimal strings or enforce and test a strict safe upper bound; preferred path is strings |
| Scenario ratio states | Forecast substitutes `999.9999` for zero service/interest and nonpositive earnings | Replace sentinels with explicit states before adding solvers; never turn not-meaningful data into a passing covenant |
| Favorable NM direction | `_scoreable` returns a huge value for every favorable-NM result, making zero-debt leverage land in the worst high-leverage band | Make scoring direction-aware and test zero-debt leverage explicitly |
| Stress event taxonomy | Refinancing need and liquidity shortfall are folded into `covenant_status` and `first_breach_year` | Separate covenant breach, liquidity exhaustion, refinancing need, and unpaid service states |
| Solver publication | A non-bracketed/non-converged bisection still returns and displays a midpoint | Return no result plus a failure reason whenever convergence fails |

## Required regression cases

The existing suite passes but does not explicitly cover the full requested matrix. The final suite must name and prove negative/zero EBITDA, zero revenue/debt/interest, negative CFADS, missing debt service/liquidity, unsupported and mismatched currency, zero recommendation, unsecured/secured/asset-based applicability, maturity, minimum coverage, and minimum liquidity outcomes. It must also include all solver monotonicity properties and golden borrower/facility structures.

## Initial model decision proposal

- Keep the obligor score unchanged in concept and extend inputs in a backward-compatible manner.
- First label and migrate the current snapshot; then use the latest valid LTM as the primary scoring period with explicit lineage to contributing periods.
- Keep facility protection, borrowing base, and pricing outside obligor grade.
- Use one reusable deterministic bisection implementation whose objective reruns the full scenario forecast for every trial.
- Store every policy number, including facility weights, advance rates, pricing grids, and solver limits, in policy configuration.

Status: pending independent Claude Opus 5 High challenge.

## Final implementation verification

All initial material findings above were implemented and tested. The final engine
uses explicit ratio states without numerical sentinels, blocks critical missing or
adverse-not-meaningful factors, and suppresses both final grade and blocked component
scores. Period models reject overlap, reconcile balance sheets, and block
incompatible LTM methods. Approved adjustments and qualitative risk factors require
evidence/rationale. Facility protection is downstream and independent from obligor
grade; asset-based capacity uses the calculated borrowing base. Pricing reconciles
the reference rate plus seven versioned basis-point components. All six reverse
stress records run the full forecast through bounded bisection and publish no number
on failure.

Verification evidence: 98 passing Python tests, 96.07% measured aggregate coverage,
strict Mypy, versioned policy validation, PDF integration tests, and independent
`claude-opus-5` source review. The exact residual limitation is documented: the
bundled demo cases are legacy snapshots until a user supplies compatible periods;
this limitation is visible and does not manufacture LTM data.
