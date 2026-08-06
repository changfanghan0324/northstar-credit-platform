# Financial Methodology Contract

Version: 1.0.0
Date: 2026-08-06
Author: Codex
Independent reviewer: Claude Opus 5 High (`claude-opus-5`)

This document is the specification shared by the Python engine and the independent Excel reference model. It defines deterministic educational calculations, not a bank policy, agency rating, regulatory capital model, audited risk model, market quote, or lending advice.

## 1. Numeric and result contract

### 1.1 Money

Normalized monetary values are `{amount_minor: int, currency: ISO-4217 code, minor_unit_exponent: int}`. USD uses exponent 2, JPY 0, and KWD 3. Raw-file scale is converted exactly once during normalization and the original unit, reported scale, and applied multiplier remain in lineage. Money arithmetic never uses binary floating point. [Master prompt §17, §19]

MVP validation requires reporting currency, existing-debt currency, and requested-loan currency to match. A mismatch returns `currency_mismatch`, persists no partial calculation run, and tells the user that multi-currency cases are unsupported. [Master prompt §13, §14, §42]

### 1.2 Ratios and comparisons

Ratio arithmetic uses `Decimal`. The unquantized result is retained as `value_exact`. A separate `value` is quantized to four decimal places using `ROUND_HALF_UP` for display and score-band comparison. Score bands declare lower/upper inclusivity and default to `(lower, upper]`. Covenant pass/breach, covenant headroom, and reverse-stress convergence use `value_exact`, never the displayed value. [Master prompt §19 rules, §21, §28–29]

### 1.3 RatioResult

Every ratio returns:

- `metric_id`, plain-language and professional names;
- `value: Decimal | null`, quantized to four places for display and score banding;
- `value_exact: Decimal | null`, unquantized for covenant tests, headroom, and numerical solvers;
- `status: ok | nm | missing | error`;
- `reason_code`;
- numerator/denominator components with source periods;
- formula identifier and threshold/policy reference;
- categorical confidence and factors;
- interpretation and corrective action when applicable.

Reason codes:

- `ok` — valid calculation.
- `nm_no_cash_interest` — zero cash interest and no PIK, capitalized, or deferred obligation; favorable treatment is policy-controlled.
- `nm_no_cash_burn` — zero or negative stressed cash burn; liquidity is not being consumed, so runway is favorable but not finite.
- `nm_no_obligation` — zero existing scheduled debt service.
- `nm_deferred_obligation` — zero cash burden because interest/service is deferred or capitalized; adverse and flagged.
- `nm_negative_base` — ratio is not meaningful because earnings or cash-flow base is negative; adverse.
- `nm_undefined` — structural 0/0 or noncritical undefined ratio; may be excluded and reweighted within its category.
- `missing_input` — required input absent; critical cases block.
- `error_invalid_input` — invalid structure, including positive proposed principal producing zero pro forma debt service.

Existing DSCR and pro forma DSCR are distinct metrics. Zero existing debt service can be favorable NM; zero pro forma debt service for a positive facility is an error and blocks decisioning. [Master prompt §19 rules, §22, §25]

## 2. Debt and cash definitions

### 2.1 Gross debt — `debt.gross` [Master prompt §19, Debt]

`Gross Debt = short-term borrowings + current maturities + long-term debt + finance-lease liabilities + selected debt-like obligations`

All included components must share currency. No cash netting occurs here.

### 2.2 Adjusted debt — `debt.adjusted` [Master prompt §19, Debt]

`Adjusted Debt = Gross Debt + selected operating leases + selected pension or debt-like obligations`

Selection is explicit policy/input metadata; the engine cannot silently include or exclude an obligation.

### 2.3 Net debt — `debt.net` [Master prompt §19, Debt]

`Eligible Cash = unrestricted cash × cash_availability_factor`

`Net Debt = Gross Debt − Eligible Cash`

The availability factor is policy data in `[0,1]`. Net debt may be negative and is not floored at zero.

### 2.4 EBITDA — `cashflow.ebitda` [Master prompt §19, Earnings and cash flow]

`EBITDA = EBIT + D&A`

### 2.5 Adjusted EBITDA — `cashflow.adjusted_ebitda` [Master prompt §16, §19]

`Adjusted EBITDA = EBITDA + approved positive adjustments − approved negative adjustments`

Only explicitly approved adjustments enter. Each carries evidence, rationale, cash/non-cash, recurring/nonrecurring, and EBITDA/CFADS effects. Positive adjustments above the policy share of reported EBITDA (default 15%) raise `large_ebitda_adjustment` and enhanced review; no automatic approval occurs.

### 2.6 Free cash flow — `cashflow.fcf` [Master prompt §15 Cash-flow statement, §19]

`Free Cash Flow = CFO − Capex`

Capex is stored as a positive cash-use amount in the normalized layer.

### 2.7 CFADS — `cashflow.cfads` [Master prompt §19]

`CFADS = Adjusted EBITDA − Cash taxes − Maintenance capex − Increase in operating working capital − Mandatory pension contributions − Other mandatory operating cash uses`

An increase in working capital is a positive cash use; a release is negative and increases CFADS. CFADS is the primary repayment-capacity numerator.

Maintenance capex requires amount, period, derivation method (`management_disclosure`, `depreciation_proxy`, `pct_of_revenue`, or `analyst_estimate`), evidence, source, confidence, and illustrative preparer/approval fields. An amount below the policy share of D&A (default 0.5x) raises a warning and never auto-adjusts. [Master prompt §11.2, §16, §27]

### 2.8 Annual debt service — `cashflow.debt_service` [Master prompt §19]

`Annual Debt Service = cash interest + scheduled principal + required finance-lease or fixed-charge payments not already deducted in CFADS`

Only obligations not already deducted in the CFADS base may be added to annual debt service. Finance-lease principal and interest qualify. Where policy includes contractual rent or operating-lease payments, the same rent must be added back to the numerator and the resulting metric is fixed-charge coverage (§4.4), not DSCR. A policy configuration that includes rent in debt service without the matching numerator add-back is invalid. Pro forma service includes existing instruments and the proposed facility under exact payment mechanics.

## 3. Leverage ratios

All ratios protect against missing or invalid bases and preserve components. [Master prompt §19–20]

### 3.1 Gross Debt / Adjusted EBITDA — `ratio.gross_debt_ebitda`

`Gross Debt / Adjusted EBITDA`

Adjusted EBITDA `<= 0` yields `nm_negative_base`, not zero or infinity.

### 3.2 Adjusted Debt / Adjusted EBITDA — `ratio.adjusted_debt_ebitda`

`Adjusted Debt / Adjusted EBITDA`

### 3.3 Net Debt / Adjusted EBITDA — `ratio.net_debt_ebitda`

`Net Debt / Adjusted EBITDA`; net cash can yield a negative valid ratio when EBITDA is positive.

### 3.4 Debt / Capital — `ratio.debt_capital`

`Gross Debt / (Gross Debt + Equity)`

### 3.5 Debt / Equity — `ratio.debt_equity`

`Gross Debt / Equity`

Nonpositive equity is reported with explicit reason and adverse interpretation; it is never treated as favorable.

### 3.6 Liabilities / Assets — `ratio.liabilities_assets`

`Total Liabilities / Total Assets`

### 3.7 Secured Debt / Total Debt — `ratio.secured_debt_total`

`Secured Debt / Gross Debt`

Zero gross debt yields `nm_no_obligation` when debt inputs are complete.

## 4. Coverage and repayment ratios

### 4.1 EBITDA interest coverage — `ratio.ebitda_interest` [Master prompt §19]

`Adjusted EBITDA / Cash Interest`

Zero cash interest is favorable only when no instrument is PIK, capitalized, or deferred and accrued interest has not materially increased. Otherwise return `nm_deferred_obligation`.

### 4.2 EBIT interest coverage — `ratio.ebit_interest` [Master prompt §19]

`Adjusted EBIT / Cash Interest`, where `Adjusted EBIT = Adjusted EBITDA − D&A`.

### 4.3 DSCR — `ratio.dscr` [Master prompt §19]

`DSCR = CFADS / Annual Debt Service`

Existing and pro forma variants follow the distinct zero-service semantics in §1.3.

### 4.4 Fixed-charge coverage — `ratio.fixed_charge_coverage` [Master prompt §19]

`(EBITDAR − Cash taxes − Maintenance capex − Increase in operating working capital) / (Cash interest + Scheduled principal + Contractual rent or lease payments)`

`EBITDAR = Adjusted EBITDA + contractual rent or lease expense` when the input is present.

### 4.5 CFADS / Debt Service — `ratio.cfads_debt_service` [Master prompt §20]

Same numeric definition as DSCR, retained as a named output for professional reporting.

### 4.6 FCF / Cash Interest — `ratio.fcf_cash_interest` [Master prompt §20]

`Free Cash Flow / Cash Interest`, with the guarded zero-interest semantics above.

## 5. Liquidity ratios

### 5.1 Current ratio — `ratio.current` [Master prompt §19]

`Current Assets / Current Liabilities`

### 5.2 Quick ratio — `ratio.quick` [Master prompt §19]

`(Cash + Eligible marketable securities + Accounts receivable) / Current Liabilities`

### 5.3 Cash ratio — `ratio.cash` [Master prompt §19]

`Eligible Cash / Current Liabilities`

### 5.4 Working capital — `metric.working_capital` [Master prompt §19]

`Current Assets − Current Liabilities`

This is a monetary metric, not a ratio.

### 5.5 Short-term debt coverage — `ratio.short_term_debt_coverage` [Master prompt §20]

`(Eligible Cash + Undrawn Committed Revolver) / (Short-term Borrowings + Current Maturities)`

### 5.6 Liquidity runway — `ratio.liquidity_runway_months` [Master prompt §19]

`(Eligible Cash + Undrawn Committed Revolver − Minimum Operating Cash) / Monthly Stressed Cash Burn`

If monthly stressed cash burn is zero and inputs are complete, return favorable NM with a clear reason; a negative burn (cash generation) is reported as NM rather than a negative runway.

### 5.7 Cash plus undrawn revolver — `metric.cash_plus_undrawn_revolver` [Master prompt §20]

`Eligible Cash + Undrawn Committed Revolver`. This is a monetary liquidity source and preserves each component.

### 5.8 Sources versus uses — `metric.sources_uses_surplus` [Master prompt §20]

`Total Committed Liquidity Sources − Total Contractual and Forecast Uses` over an explicitly labeled horizon. Sources include eligible cash, committed undrawn revolver, and evidenced operating inflows; uses include minimum operating cash, maturities, interest, maintenance capex, taxes, and other mandatory uses. A negative result is a shortfall and no uncommitted refinancing source is assumed.

## 6. Cash-flow ratios

### 6.1 CFO / Debt — `ratio.cfo_debt` [Master prompt §19]

`CFO / Gross Debt`

### 6.2 FCF / Debt — `ratio.fcf_debt` [Master prompt §19]

`Free Cash Flow / Gross Debt`

### 6.3 FCF margin — `ratio.fcf_margin` [Master prompt §20]

`Free Cash Flow / Revenue`

### 6.4 Cash conversion — `ratio.cash_conversion` [Master prompt §20]

`CFO / Reported EBITDA`

Both numerator and denominator are unadjusted to avoid mechanically depressing the ratio when an EBITDA add-back has no matching CFO adjustment. The chosen definition is documented because cash conversion has multiple industry conventions.

### 6.5 Capex burden — `ratio.capex_cfo`, `ratio.capex_ebitda` [Master prompt §19]

`Capex / CFO` and `Capex / Adjusted EBITDA`

### 6.6 Cash-flow volatility — `ratio.cashflow_volatility` [Master prompt §19]

`population standard deviation of historical CFADS / absolute average historical CFADS`

Use at least three comparable annual periods. If the absolute mean is zero, return `nm_undefined`; missing/noncomparable periods return `missing_input` with corrective action.

### 6.7 Positive FCF years — `metric.positive_fcf_years` [Master prompt §20]

Count and percentage of comparable historical years with FCF `> 0`.

## 7. Profitability and trend

### 7.1 Growth — `ratio.revenue_growth`, `ratio.ebitda_growth` [Master prompt §20]

`Current / Prior − 1`; a prior value `<= 0` returns an explicit NM reason rather than an economically misleading growth percentage.

### 7.2 Margins — `ratio.ebitda_margin`, `ratio.ebit_margin`, `ratio.fcf_margin` [Master prompt §20]

`Adjusted EBITDA / Revenue`, `Adjusted EBIT / Revenue`, and `FCF / Revenue`.

### 7.3 ROA — `ratio.roa` [Master prompt §20]

`Net Income / Average Total Assets`; average uses beginning and ending assets when both are available, otherwise ending assets with a lower-confidence factor.

### 7.4 ROIC — `ratio.roic` [Master prompt §20]

`NOPAT / Average Invested Capital`

`NOPAT = Adjusted EBIT × (1 − effective cash tax rate)` and `Invested Capital = Gross Debt + Equity − Unrestricted Cash`. This return metric does not use the lending-policy cash-availability factor. The illustrative definition is explicitly labeled because industry practice varies.

### 7.5 Revenue and margin volatility — `ratio.revenue_volatility`, `ratio.margin_volatility` [Master prompt §20]

Population standard deviation divided by the absolute mean over at least three comparable annual periods. Margin volatility uses EBITDA-margin observations.

## 8. Debt capacity

### 8.0 Multi-period spreading and LTM

Every structured period stores type, start/end date, fiscal year/quarter, source,
currency, scale, audit state, and separate income-statement, balance-sheet, and
cash-flow facts. Quarters cannot overlap. When the source data are available, LTM is
either a reported LTM period, the sum of the latest four nonoverlapping quarters, or
latest fiscal year plus current YTD less prior comparable YTD. Incompatible dates or
missing components block the selected LTM method and retain the explanation.

Assets are compared with liabilities plus equity to the minor-unit tolerance. The
analysis exposes every reconciliation warning and never converts a failed
reconciliation into zero.

### 8.1 Leverage capacity [Master prompt §25]

`Maximum Total Debt = Maximum Allowed Leverage × Adjusted EBITDA`

`Incremental Debt Capacity = Maximum Total Debt − Existing Pro Forma Debt`

`Existing Pro Forma Debt` is existing debt adjusted for committed transactions that will close regardless of this request (such as committed refinancings, acquisitions, or scheduled repayments) and explicitly excludes the proposed facility. The policy limit declares gross, adjusted, or net debt and the same measure must appear on both sides; mixing measures is invalid. Incremental capacity is floored at zero for lending recommendation but the negative raw headroom is preserved for interpretation. The §14 golden case uses gross debt.

### 8.2 DSCR capacity [Master prompt §25]

`Maximum Annual Debt Service = CFADS / Minimum Required DSCR`

`Available New Debt Service = Maximum Annual Debt Service − Existing Annual Debt Service`

For level-payment amortizing debt with periodic rate `r` and `n` payments:

`Present Value Capacity = Payment × (1 − (1+r)^−n) / r`

When `r = 0`, capacity is `Payment × n`. Payment frequency, maturity, and rate must be explicit. Annual service is converted to periodic payment consistently. The forbidden shortcut is `annual debt service × years` when `r ≠ 0`.

### 8.3 Bullet capacity [Master prompt §25]

Bullet capacity reports interest coverage, projected cash accumulation, exit leverage, balloon amount, refinancing dependence, asset-sale support, and a severe no-refinancing outcome. It cannot rely on refinancing as an assumed certainty.

### 8.4 Collateral capacity [Master prompt §25]

`Collateral Capacity = Σ(Eligible Collateral Amount × Policy Advance Rate) − Prior Liens − Reserves`

Each collateral class and advance rate remains visible.

For an asset-based facility, eligible receivables equal gross receivables less
ineligible, past-due, cross-aged, foreign, concentration, and dilution reductions.
Eligible inventory equals gross inventory less ineligible and obsolete inventory.
Policy caps both advance rates. Final borrowing base adds other eligible collateral
and subtracts additional reserves and prior liens. It replaces the legacy manual
collateral capacity for the asset-based constraint. Unsecured facilities mark the
borrowing base not applicable.

### 8.5 Policy capacity and recommendation [Master prompt §25]

Policy capacity applies single-name, industry, country, maturity, leverage, DSCR, collateral, and grade limits as configured.

`Recommended Loan = min(Requested Amount, Leverage Capacity, DSCR Capacity, Collateral Capacity, Policy Capacity)`

The binding constraint is always named. Ties report all co-binding constraints within one minor currency unit.

## 9. Score and grade contract

The obligor score is 0–100: 65 financial points and 35 business-risk points. Default sub-weights are: leverage 18, coverage/DSCR 18, liquidity 10, cash-flow quality/stability 10, profitability/trend 9; industry/cyclicality 10, competitive position/scale 7, customer concentration 6, geographic/product diversification 4, management/financial policy 5, governance/event risk 3. Thresholds and weights are policy data, never application constants. Each component stores input, formula, band, points, weight, contribution, source, period, confidence, override, and reason. Facility protection remains separate and cannot improve obligor grade. [Master prompt §21, §23–24]

### 9.1 Illustrative financial bands [Master prompt §21]

- Gross leverage: `<=1.5x 100`; `(1.5,2.5] 85`; `(2.5,3.5] 70`; `(3.5,4.5] 50`; `(4.5,6.0] 25`; `>6.0 10`; EBITDA `<=0` 0.
- Interest coverage: `>=8.0x 100`; `[5.0,8.0) 85`; `[3.0,5.0) 70`; `[2.0,3.0) 50`; `[1.5,2.0) 30`; `[1.0,1.5) 15`; `<1.0 0`.
- DSCR: `>=2.0x 100`; `[1.50,2.0) 80`; `[1.25,1.50) 60`; `[1.00,1.25) 35`; `<1.00 0`.

Band inclusivity is encoded explicitly in policy and boundary-tested after four-decimal quantization.

### 9.2 Missing-data reweighting [Master prompt §22]

Critical missing EBITDA, debt, interest, cash, debt service, working capital, or loan terms blocks grade and approval. Noncritical missing components may reweight only within their category.

`ScorecardResult` exposes `excluded_weight_pct` and `reweight_applied`. Policy defaults:

- excluded weight `>15%` adds `material_reweighting` and caps confidence at medium;
- excluded weight `>30%` blocks grade and decision.

Active weights must sum exactly to one within the reweighted category using Decimal.

### 9.3 Grade mapping [Master prompt §23]

Decimal score bands are half-open: `[90,100]` Grade 1; `[82,90)` Grade 2; `[74,82)` Grade 3; `[66,74)` Grade 4; `[58,66)` Grade 5; `[50,58)` Grade 6; `[42,50)` Grade 7; `[34,42)` Grade 8; `(0,34)` Grade 9; `0` or verified default Grade 10. External-equivalent ranges are always labeled educational approximations and never use agency logos.

## 10. Scenarios and covenants

Base, downside, and severe scenarios forecast three years of revenue, EBITDA, EBIT, taxes, working capital, capex, CFADS, interest, principal, ending debt/cash, revolver, leverage, coverage, DSCR, liquidity, and covenant status. Interest responds to average debt, fixed/floating mix, rate shock, floors, and proposed debt. Scenarios are deterministic and never presented as probabilities. [Master prompt §27]

If any severe metric improves versus base, the result must carry `improvement_justification {driver, magnitude, input_ref}`. Absence is a validation error. [Master prompt §42 invariant]

Minimum covenant headroom is `Actual − Required Minimum`; maximum covenant headroom is `Permitted Maximum − Actual`. Status includes pass/breach, first breach, scenario, cure, and action. Covenant comparisons and headroom use `value_exact`; if a quantized comparison is ever required by an external policy, it must round conservatively for the covenant polarity. No breach probability is displayed. [Master prompt §29]

## 11. Reverse stress

Every output uses the same deterministic bounded-bisection implementation and reruns
the complete three-year forecast. The six solved variables are: revenue decline at
minimum DSCR, EBITDA-margin decline at maximum leverage, interest-rate shock at
minimum coverage, working-capital use at liquidity exhaustion, maximum proposed loan
passing downside policy, and maximum proposed loan preserving severe minimum
liquidity. Each record includes initial bounds, tolerance, iterations, residual,
convergence status, failure reason, result, and interpretation. A nonconverged record
never exposes a numeric result. [Master prompt §28]

## 11.1 Facility protection and indicative pricing

Facility protection is independent from the obligor grade. Versioned policy weights
seniority, collateral quality/coverage, guarantee, amortization, maturity/refinancing,
covenants, reporting, and purpose/repayment alignment. It produces a protection
score/category, expected-recovery category, strengths, weaknesses, required
improvements, and documentation requirements.

Indicative pricing starts with a user-entered reference base rate, then adds
versioned risk-grade, tenor, security, amortization, covenant, concentration, and
optional relationship adjustments. Revolvers can include a commitment fee and an
optional upfront fee. It is always labeled educational and is not a market quote,
commitment, or recommendation.

## 12. Decision and memo

Decision rules produce Approve, Approve with conditions, Reduce requested amount, Refer to credit committee, or Decline, using the configured grade, base/downside DSCR, breaches, repayment source, capacity, policy exceptions, overrides, and data integrity. Missing critical data, invalid pro forma service, currency mismatch, or excluded score weight above the block ceiling prevents final approval. [Master prompt §22, §30]

Memo sentences use only imported/synthetic source data, approved analyst inputs, and persisted calculation outputs. Every numeric sentence has a provenance pointer. Input-hash drift blocks export. AI cannot calculate, select, or alter a number or decision. [Master prompt §11.5, §32]

## 13. Confidence

One categorical confidence result (`high`, `medium`, `low`, `blocked`) and a
transparent 0-100 completeness indicator are derived from typed factors. Factors
include missing inputs, absent instrument detail, unreviewed evidence, large EBITDA
adjustment, unreconcilable LTM, and synthetic data. Adding a penalty cannot raise
confidence. Missing critical input implies blocked confidence, null grade, and a
blocked analysis. [Master prompt §11.3, §22, §33]

## 14. Reference golden case

The first synthetic stable case uses USD and the following normalized LTM inputs (USD millions shown here; storage is integer cents): revenue 200; prior revenue 190; EBIT 28; D&A 12; approved positive EBITDA adjustments 2; approved negative adjustments 1; prior adjusted EBITDA 38; CFO 30; total capex 10; maintenance capex 8; cash taxes 5; increase in operating working capital 3; mandatory pension 1; cash interest 6; scheduled principal 8; no additional fixed charge in DSCR; gross debt components 5 + 5 + 60 + 5; unrestricted cash 20; cash-availability factor 80%; current assets 80; current liabilities 40; accounts receivable 30; inventory 25; other current assets 5; undrawn revolver 10; minimum operating cash 8; monthly stressed burn 3; equity 80; total liabilities 100; total assets 180; secured debt 30; contractual operating rent 4 used only in fixed-charge coverage with the EBITDAR add-back; net income 16; effective cash tax rate 25%; historical CFADS 22, 24, 23; historical FCF 18, 20, 19; historical revenue 180, 190, 200; historical EBITDA margins 19.0%, 20.0%, 20.5%. Capacity inputs are a USD 15 million request, a gross-debt 3.50x maximum leverage limit, 1.25x minimum DSCR, 8% fixed annual rate, five annual payments, USD 30 million collateral capacity, and USD 25 million policy capacity.

Codex derives and hash-commits the numeric expected file and independent Excel formula specification before opening Claude's implementation diff. Plaintext values are revealed only after the implementation is complete; discrepancies are adjudicated against this contract and logged.

## 15. Model and product limitations

- Northstar is an educational, synthetic-data portfolio demonstration. It is not a
  bank, rating agency, regulated underwriting system, market quote, legal opinion,
  or lending commitment.
- Public operation is Portfolio Demo Mode (Mode A): anonymous session ownership,
  best-effort instance-local rate/PDF limits, a ten-case quota, and seven-day expiry.
  There is no user authentication, authorization administration, encryption key
  management, confidential-document ingestion, or regulated-data governance.
- Mode A startup creates the three runtime aggregate tables from ORM metadata. The
  Alembic sequence is migration lineage for a separately governed durable rollout;
  operators must not run both schema owners against the same fresh database. A
  future durable rollout must apply and validate migrations before enabling app
  traffic, including checking for duplicate legacy case-version numbers.
- The three bundled demonstration cases retain a legacy single-period snapshot so
  they open immediately. Trend and calculated LTM conclusions remain explicitly
  limited until a user supplies compatible, nonoverlapping multi-period statements.
- Scenario and solver outputs are deterministic sensitivities, not probabilities.
  A nonconverged solver publishes no numeric result.
- Indicative pricing uses a user-supplied reference rate plus illustrative versioned
  policy adjustments. It is not live pricing.
- Monetary transport is limited to JavaScript's exact integer range in minor units.
  Multi-currency consolidation and foreign-exchange translation are unsupported.
- The localized PDFs embed Noto Sans TC and are visually verified, but they are not
  tagged PDF/UA documents. The web application is the primary accessible interface.
