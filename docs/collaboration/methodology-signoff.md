# Methodology Sign-Off — Claude Opus 5 (independent reviewer)

Date: 2026-08-03
Reviewer: Claude Opus 5 (non-author)
Author under review: Codex
Reference: `Project_2_Codex_Claude_Master_Prompt_v2.md`, §§16, 19–30, 42

Artifacts in scope (no other file was inspected in this invocation):

1. `docs/methodology.md` v1.0.0-draft
2. `excel/formulas/core.yaml` v1.0.0
3. `tests/unit/test_task1_contracts.py`
4. `tests/unit/test_task1_invariants.py`
5. `tests/unit/test_task1_architecture.py`

No file was edited. All fixes below are requests to the author.

---

## 1. Per-section disposition — `docs/methodology.md`

| § | Section | Disposition | Basis |
|---|---|---|---|
| 1.1 | Money | approved | Integer minor units, ISO exponent, single scale conversion at normalization, no binary float. USD 2 / JPY 0 / KWD 3 correct. Currency-mismatch hard stop with no partial run matches §13, §14, §42. |
| 1.2 | Ratios and comparisons | **required fix — F3** | Decimal arithmetic and declared band inclusivity are correct. Quantize-before-compare is internally consistent but discards the exact value, so a 4-dp round can convert a covenant breach into a pass. |
| 1.3 | RatioResult | **required fix — F3** | The reason-code taxonomy is the strongest element of the contract: it correctly separates favorable NM, adverse NM, missing, and error, and the existing-vs-pro-forma DSCR split is right. The result shape must also carry the unquantized value. |
| 2.1 | Gross debt | approved | Exact component list of §19; no cash netting; single-currency guard. |
| 2.2 | Adjusted debt | approved | Explicit selection metadata implements "selected" in §19; no silent inclusion. |
| 2.3 | Net debt | approved | Availability factor in [0,1]; not floored at zero, which is required for the §42 net-cash case. |
| 2.4 | EBITDA | approved | `EBIT + D&A` per §19. |
| 2.5 | Adjusted EBITDA | approved | Approved-only add-backs; 15% default enhanced-review trigger implements §16's configurable percentage; no automatic approval. |
| 2.6 | Free cash flow | approved | `CFO − Capex` per §19; capex stored positive, consistent with §17 validation 10. |
| 2.7 | CFADS | **required fix — F1** | Component list matches §19 term-for-term and the increase/release sign rule is correct. The base does not reconcile with the lease term admitted in §2.8. |
| 2.8 | Annual debt service | **required fix — F1** | §19 permits policy-included lease/fixed-charge payments, but the contract never states whether the corresponding expense already sits inside the CFADS base. |
| 3.1 | Gross Debt / Adjusted EBITDA | approved | Adjusted EBITDA ≤ 0 yields adverse NM, not 0 or ∞, per §19 "return not meaningful when appropriate". |
| 3.2–3.3 | Adjusted and Net Debt / EBITDA | approved | Net cash producing a valid negative ratio is correct and matches §42 case 5. |
| 3.4–3.6 | Debt/Capital, Debt/Equity, Liabilities/Assets | approved | Nonpositive equity is explicitly adverse and never favorable — the correct treatment of the classic sign trap. |
| 3.7 | Secured / Total Debt | approved | Zero gross debt → `nm_no_obligation` only when debt inputs are complete; correctly distinguished from missing. All seven §20 leverage metrics are present. |
| 4.1 | EBITDA interest coverage | approved | PIK/capitalized/deferred guard is correct and is the right defense against a zero-interest false positive (§42 case 4). |
| 4.2 | EBIT interest coverage | approved | `Adjusted EBIT = Adjusted EBITDA − D&A` is consistent with §2.4. |
| 4.3 | DSCR | **required fix — F1** | `CFADS / Annual Debt Service` per §19; inherits the §2.8 lease ambiguity. |
| 4.4 | Fixed-charge coverage | approved | Reproduces §19 term-for-term, and the EBITDAR add-back correctly matches the rent that appears in the denominator. |
| 4.5–4.6 | CFADS/Debt Service, FCF/Cash Interest | approved | All six §20 coverage metrics present. |
| 5.1–5.4 | Current, quick, cash, working capital | approved | Match §19. Working capital correctly typed as monetary, not a ratio. |
| 5.5 | Short-term debt coverage | approved | Matches §20. |
| 5.6 | Liquidity runway | approved | Matches §19. Reporting cash generation as NM rather than a negative runway is the correct anti-nonsense guard. |
| 5.x | Liquidity completeness | **required fix — F7** | §20 also lists "cash plus undrawn revolver" and "sources versus uses". Neither exists as a named metric. |
| 6.1–6.3 | CFO/Debt, FCF/Debt, FCF margin | approved | Match §19–20. |
| 6.4 | Cash conversion | **required fix — F8** | `CFO / Adjusted EBITDA` mixes an unadjusted numerator with an adjusted denominator, so every approved positive add-back mechanically depresses the metric. |
| 6.5 | Capex burden | approved | Both §19 variants present. |
| 6.6 | Cash-flow volatility | approved | Declaring population σ, a ≥3-period minimum, and `nm_undefined` on a zero mean resolves the ambiguity §19 leaves open. |
| 6.7 | Positive FCF years | approved | Matches §20. |
| 7.1 | Growth | approved | Nonpositive prior returns explicit NM instead of an economically meaningless percentage. |
| 7.2 | Margins | approved | Matches §20. |
| 7.3 | ROA | approved | Average-assets rule with a documented lower-confidence fallback is correct. |
| 7.4 | ROIC | **required fix — F9** | Invested capital subtracts availability-factored eligible cash, coupling a return metric to a lending-policy parameter. |
| 7.5 | Revenue and margin volatility | approved | Consistent with §6.6; all eight §20 profitability/trend metrics present. |
| 8.1 | Leverage capacity | **required fix — F2** | Reproduces §25 wording but leaves "Existing Pro Forma Debt" and the debt measure undefined; the §14 golden admits two defensible answers. |
| 8.2 | DSCR capacity | approved | `CFADS / Minimum Required DSCR` per §25. The annuity present value is the correct ordinary-annuity closed form with an explicit r=0 branch, and §25's prohibition on `annual debt service × years` is named. |
| 8.3 | Bullet capacity | approved | All seven §25 bullet considerations including the severe no-refinancing outcome; refinancing is not assumed. |
| 8.4 | Collateral capacity | approved | `Σ(eligible × advance rate) − prior liens − reserves` per §25 with per-class visibility. |
| 8.5 | Policy capacity and recommendation | approved | Five-way `min` per §25, binding constraint always named, co-binding ties reported. |
| 9 | Score and grade contract | **required fix — F10** | 65/35 split per §21; thresholds as policy data per §21; facility risk cannot improve obligor grade per §24. The §21 default sub-weight vector is not stated, leaving Excel and Python without a shared default. |
| 9.1 | Illustrative bands | approved | Leverage, interest-coverage, and DSCR bands reproduce §21 exactly. I checked real-line coverage: all three band sets are gapless and non-overlapping, and inclusivity direction is correctly inverted between lower-is-better and higher-is-better metrics. |
| 9.2 | Missing-data reweighting | approved | Critical-data block and within-category-only reweighting match §22. The 15%/30% ceilings and the exact-Decimal weight-sum requirement exceed the prompt's floor and are sound. |
| 9.3 | Grade mapping | **required fix — F11** | Reproduces §23 exactly and therefore inherits its integer-only bands: a Decimal score of 89.5 maps to no grade. |
| 10 | Scenarios and covenants | approved | Forecast line items, interest drivers, and the deterministic-not-probability label match §27. Headroom signs match §29 and no breach probability is shown. The `improvement_justification` requirement is a correct, testable implementation of the §42 severe-scenario invariant. |
| 11 | Reverse stress | approved | All six §28 solves present; declaring monotonic direction, bounds, tolerance, iteration cap, convergence status, and a no-solution state satisfies §28's deterministic-convergence requirement. |
| 12 | Decision and memo | approved | Five §30 outcomes; blocking conditions match §22 and §30; per-sentence provenance and the AI prohibition match §11.5 and §32. |
| 13 | Confidence | approved | Categorical only, monotone (adding a factor cannot raise confidence), blocked on missing critical input. Matches §11.3, §22, §33. |
| 14 | Reference golden case | **required fix — F12** | Inputs are complete and internally consistent (EBITDA 40, adjusted EBITDA 41, gross debt 75, eligible cash 16). Two golden outputs are indeterminate until F1 and F2 land. |

## 2. Formula and semantic defects, by exact location

### D1 — `docs/methodology.md` §2.7 / §2.8 / §4.3 — lease and rent double count (material)

Adjusted EBITDA is stated after rent expense, so CFADS is already net of operating rent. §2.8
nonetheless admits "required lease/fixed-charge payments included by policy" into the DSCR
denominator. Where policy includes an operating-lease or rent payment, that payment is deducted
twice — once inside the CFADS numerator, once in the debt-service denominator — understating
DSCR, DSCR capacity (§8.2), covenant headroom (§10), and the decision (§12). Finance-lease
payments are unaffected because they sit below EBITDA as D&A and interest. §4.4 already solves
exactly this problem for fixed-charge coverage via the EBITDAR add-back; DSCR has no equivalent
rule. §14 supplies both `required lease payments 1` and `contractual rent 4`, so the golden DSCR
is currently ambiguous.

### D2 — `docs/methodology.md` §8.1 — undefined capacity operands (material)

"Existing Pro Forma Debt" is used without definition. Read literally as pro forma *including* the
proposed facility, the calculation is circular. The debt measure is also unspecified while §9.1
scores on gross leverage and §29 supports both gross and net covenants. With the §14 inputs:
gross basis `3.50 × 41 − 75 = 68.5`; net basis `3.50 × 41 − 59 = 84.5`. A 16.0 swing in an MVP
acceptance number (§48 item 7) with no way to choose from the document.

### D3 — `docs/methodology.md` §1.2 / §1.3 — exact value discarded (material)

§1.2 quantizes to four decimals with `ROUND_HALF_UP` *before* threshold comparison, and §1.3
stores only that value. A true DSCR of 1.24996 becomes 1.2500 and passes a 1.25x covenant. §29
requires pass/breach, headroom, and first breach period; rounding a breach into a pass errs in
the unsafe direction and is unrecoverable once the exact value is gone. This also degrades the
§28 reverse-stress solvers, whose convergence tolerance cannot be finer than the stored
precision.

### D4 — `excel/formulas/core.yaml` `recommended_loan` — undefined reference and missing floor

`=MIN({requested_amount},{leverage_capacity},{dscr_capacity},{collateral_capacity},{policy_capacity})`
references `{dscr_capacity}`, which no key in the file defines; the defined keys are
`maximum_annual_debt_service`, `available_new_debt_service`, and `annuity_capacity`. The
derivation chain is broken, so the independent Excel model cannot compute §25's final
recommendation. The expression is also unfloored: methodology §8.4 leaves collateral capacity
unfloored (prior liens and reserves may exceed eligible collateral), so this can emit a negative
recommended loan.

### D5 — `excel/formulas/core.yaml` `leverage_capacity` — name/expression mismatch, floor loses data

The key is named `leverage_capacity` but the expression is methodology's *incremental* capacity
(`max leverage × adjusted EBITDA − existing pro forma debt`). Methodology §8.1 names two distinct
quantities and requires the negative raw headroom to survive for interpretation; `MAX(0,…)`
discards it. Also inherits D2.

### D6 — `excel/formulas/core.yaml` `interest_coverage`, `dscr` — reason codes collapsed

`IF({cash_interest}=0,NA(),…)` and `IF({annual_debt_service}=0,NA(),…)` are numerically correct
but flatten the four states methodology §1.3 requires into one `NA()`. In particular the pro
forma zero-service case must be an **error** that blocks decisioning, not NM. §37 makes Excel an
independent reference implementation and §42 requires Excel and Python to reconcile; as written,
reconciliation can compare magnitudes but not semantics, so a reason-code regression would pass.

### D7 — `excel/formulas/core.yaml` `annual_debt_service` — inherits D1.

### D8 — `excel/formulas/core.yaml` header — rounding equivalence unrecorded

`rounding: Decimal-compatible calculations; ratios display four decimals` does not pin the mode.
I verified the equivalence holds: Excel `ROUND` and Decimal `ROUND_HALF_UP` are both
half-away-from-zero, including on the negative net-debt ratios this model can produce, while
Python's builtin `round` is banker's rounding and disagrees. This is the most common
Excel/Python reconciliation failure and should be stated, not left to be rediscovered.

### D9 — scope note, not a defect

`core.yaml` defines 15 formulas against roughly 45 methodology metrics. Acceptable for Task 1.
Before the §37 twenty-tab model, `STDEV.P` versus `STDEV.S` must be pinned to match methodology
§6.6's population σ, or volatility will not reconcile.

## 3. Test-file review

### 3.1 `tests/unit/test_task1_contracts.py` — approved-with-required-fixes

**Contamination check — clean.** Line 127 uses `(75, 41)`, the §14 golden gross debt and adjusted
EBITDA, but asserts only `value.as_tuple().exponent == -4` and reveals no result. Every §14
*input* is already published in plaintext in `docs/methodology.md`, so no test here discloses
anything the implementer cannot already read. No expected golden magnitude appears in any test
file. Recorded observation: the commit-and-reveal control therefore protects against retro-fitting
expected values to an implementation, not against inference — the calculations are deterministic
from published inputs.

**Correct and load-bearing:** lines 36–45 (JPY exponent-0 scaling, the precise bug §1.1 exists to
prevent); 80–85 (negative EBITDA must be adverse NM with `value is None`, forbidding the common
wrong answer of a signed ratio); 87–91 (missing is not NM, per §22); 93–105 (favorable vs deferred
zero-interest split, which cannot be satisfied by a single NM state); 108–123 (pro forma zero
service must be `ERROR`, not NM). Lines 54–77 correctly assert `isinstance(amount_minor, int)`.

**Incorrect expectation — D10 (lines 31–34), blocking.** `test_money_rejects_binary_float` passes
under Pydantic v2 lax mode only because `1.5` is non-integral. An integral float `2.0` is silently
coerced to `2` in lax mode, so this test passes against a contract that accepts floats — the exact
defect it is named for. It can reward an incorrect implementation.

**Weak expectations — D11 (non-blocking).** Line 130 asserts only the exponent, accepting any
magnitude, so the `ROUND_HALF_UP` mode itself is untested. Line 50's
`pytest.raises(ValueError, match="currency")` matches an untyped message substring rather than a
typed error the API layer can map to methodology §1.1's `currency_mismatch` code.

**Missing edge semantics — D12 (non-blocking).** Against §42's ten cases, this file covers
negative EBITDA, zero interest, and missing critical data. Not covered and within Task 1 reach:
net cash (§42 case 5 — methodology §3.3 requires a *valid negative* ratio, and nothing pins this,
so an implementer could plausibly return NM); nonpositive equity as adverse (§3.5); `nm_undefined`
for structural 0/0 (§1.3); currency mismatch raised from inside a cashflow function rather than
only from `ensure_same_currency` called directly.

### 3.2 `tests/unit/test_task1_invariants.py` — approved-with-required-fixes

**Contamination check — clean.** All inputs (60/30, 60/20, 50/25, 75/25, 30/5, 20/5, 30/8, 24/12,
24/15) are non-golden and no expected magnitude is asserted.

**Verified against a wrong implementation.** I re-derived each of the five invariants under an
inverted formula (numerator and denominator swapped) and confirmed all five fail rather than pass:
leverage 30/60 vs 20/60 → `weaker > stronger` false; 25/50 vs 25/75 → false; coverage 5/30 vs 5/20
→ `weaker < stronger` false; 5/30 vs 8/30 → false; DSCR 12/24 vs 15/24 → `higher < lower` false.
These tests do not reward an incorrect formula. They implement §42 invariants 1–5.

**D13 (non-blocking).** No test asserts `status is RatioStatus.OK` before dereferencing `.value`.
If a formula wrongly returns NM the comparison raises `TypeError`, so this is not a false green,
but the failure is uninformative. Add the status assertion.

**D14 (non-blocking, scope).** Five of §42's eleven invariants are present; the other six
(rate→coverage as a distinct rate path, severe-scenario non-improvement, recommended loan ≤
binding capacity, missing critical data blocks approval, score components sum, memo equals engine,
Excel reconciles) belong to later modules. Record this as sequencing so the gap does not read as
omission.

### 3.3 `tests/unit/test_task1_architecture.py` — rejected

Both tests in this file are **false greens**: they report success while enforcing nothing. These
are the only automated enforcement of methodology §1.1's no-binary-float rule, so a silent pass is
worse than no test at all.

**D15 (blocking) — vacuous pass.** `ENGINE_ROOT = Path("packages/credit_engine/credit_engine")`
(line 7) is CWD-relative and the directory does not yet exist. `Path(...).glob("*.py")` on a
missing directory yields nothing, `violations` stays empty, and both tests pass. They also pass
whenever pytest is invoked from any directory other than the repository root.

**D16 (blocking) — non-recursive scan.** `glob("*.py")` (line 13) skips every subpackage under
`credit_engine/`, so any module in a subdirectory escapes the import-boundary check entirely.

**D17 (blocking) — forbidden set too narrow.** `{"apps", "fastapi", "sqlalchemy", "requests",
"httpx"}` (line 11) does not cover the float-native libraries that would silently defeat the
Decimal contract (`numpy`, `pandas`, `math`) or the nondeterminism and I/O that a pure engine must
exclude (`random`, `datetime`, `time`, `os`, `pathlib`, `json`, `socket`, `urllib`).

**D18 (blocking) — float guard misses the likely defect sites.** Lines 27–35 scan only `money.py`
and `cashflow.py`, **not `ratios.py`** — the module where division actually happens and where a
float will realistically appear. The guard also detects only `float(...)` calls, so a bare float
literal (`0.8` for the §2.3 cash-availability factor, `1.25` for a DSCR threshold) passes, and it
does not detect `Decimal(1.5)`, the classic way to inherit binary error while appearing to honour
the contract.

## 4. Exact required fixes

**F1 (blocking) — `docs/methodology.md` §2.8, then §2.7, §4.3, §14.** Add to §2.8: *"Only
obligations not already deducted in the CFADS base may be added to annual debt service.
Finance-lease principal and interest qualify. Where policy includes contractual rent or
operating-lease payments, the same rent must be added back to the CFADS numerator, and the
resulting metric is reported as fixed-charge coverage (§4.4), not DSCR. The engine must reject a
policy configuration that includes rent in debt service without the matching add-back."* Then
restate §14: either remove `required lease payments 1` from the golden's debt service, or state
the add-back and re-derive.

**F2 (blocking) — `docs/methodology.md` §8.1.** Add: *"`Existing Pro Forma Debt` is existing debt
adjusted for committed transactions that will close regardless of this request (refinancings,
acquisitions, scheduled repayments) and explicitly excludes the proposed facility. The debt
measure — gross, adjusted, or net — is declared by the policy limit itself and must be the same
measure on both sides of the comparison; mixing measures is a configuration error. The §14 golden
uses `<measure>`."*

**F3 (blocking) — `docs/methodology.md` §1.3, and §1.2.** Add to §1.3: *"`RatioResult` carries both
`value` (Decimal quantized to four decimals with `ROUND_HALF_UP`, used for display and score
banding) and `value_exact` (unquantized Decimal, used for covenant pass/breach, headroom, and
reverse-stress convergence). Covenant tests compare `value_exact`. Where a quantized comparison is
used, it must be quantized in the conservative direction for the covenant's polarity."* Cross-
reference from §1.2 and §10.

**F4 (blocking) — `excel/formulas/core.yaml` `recommended_loan`.** Define the missing chain:
`available_new_debt_service` → `periodic_payment` (with the §8.2 frequency conversion stated) →
`annuity_capacity` → `dscr_capacity`. Then floor the result: `=MAX(0, MIN(...))`. A zero or
negative minimum must surface as a decline with the binding constraint named, never as a
recommended loan amount.

**F5 (non-blocking) — `excel/formulas/core.yaml`.** Split into `maximum_total_debt`
(`{maximum_leverage}*{adjusted_ebitda}`) and `incremental_leverage_capacity_raw` (unfloored), then
derive `leverage_capacity = MAX(0, raw)`, preserving the negative raw headroom §8.1 requires.

**F6 (non-blocking) — `excel/formulas/core.yaml`.** Add `status` and `reason_code` cells beside
each guarded ratio so §37/§42 reconciliation compares reason codes as well as magnitudes. Minimum
set: favorable no-obligation, adverse deferred obligation, adverse negative base, pro forma error.

**F7 (non-blocking) — `docs/methodology.md` §5.** Add named metrics
`metric.cash_plus_undrawn_revolver` and a `sources versus uses` definition (§20).

**F8 (non-blocking) — `docs/methodology.md` §6.4.** Define cash conversion as `CFO / EBITDA` (both
unadjusted) or `Adjusted CFO / Adjusted EBITDA`, and state which.

**F9 (non-blocking) — `docs/methodology.md` §7.4.** Subtract unrestricted cash, not
availability-factored eligible cash, from invested capital, or state why a lending-policy
parameter belongs in a return metric.

**F10 (non-blocking) — `docs/methodology.md` §9.** State the §21 default sub-weight vector:
Leverage 18, Coverage/DSCR 18, Liquidity 10, Cash-flow quality 10, Profitability 9; Industry 10,
Competitive position 7, Customer concentration 6, Geographic/product 4, Management 5, Governance 3.
I verified these sum to 65 and 35.

**F11 (non-blocking) — `docs/methodology.md` §9.3.** Specify that the score is quantized to an
integer with `ROUND_HALF_UP` before grade lookup, or restate the bands half-open (`[82,90)`).

**F12 (blocking, procedural) — `docs/methodology.md` §14.** After F1 and F2, restate the golden with the
lease treatment and debt basis explicit. Note that the DSCR and leverage-capacity goldens change,
so the committed golden hash must be re-derived and re-issued before implementation begins.

**F13 (non-blocking) — `excel/formulas/core.yaml` header.** Record that Excel `ROUND` and Decimal
`ROUND_HALF_UP` agree (both half-away-from-zero, including on negative values) and that Python's
builtin `round` does not.

**F14 (blocking) — `tests/unit/test_task1_contracts.py` lines 31–34.** Assert that an integral
float (`Money(amount_minor=2.0, **USD)`) also raises, or configure the model `strict=True`, so the
test cannot pass against a lax-coercion contract.

**F15 (non-blocking) — `tests/unit/test_task1_contracts.py`.** Add a `ROUND_HALF_UP` boundary case
with a literal expected Decimal on non-golden inputs, including one negative value; replace the
message-substring match on line 50 with a typed `CurrencyMismatchError`.

**F16 (non-blocking) — `tests/unit/test_task1_contracts.py`.** Add the four missing edge cases from
D12: net cash yields a valid negative ratio; nonpositive equity is adverse; structural 0/0 yields
`nm_undefined`; currency mismatch raised from inside a cashflow function.

**F17 (non-blocking) — `tests/unit/test_task1_invariants.py`.** Assert `status is RatioStatus.OK`
before each `.value` comparison, and record the §42 invariant-coverage scope.

**F18 (blocking) — `tests/unit/test_task1_architecture.py` line 7.** Resolve `ENGINE_ROOT` from
`__file__` rather than CWD, and assert `ENGINE_ROOT.is_dir()` and that at least one module was
scanned, so the tests cannot pass vacuously.

**F19 (blocking) — `tests/unit/test_task1_architecture.py` line 13.** Use `rglob("*.py")`.

**F20 (blocking) — `tests/unit/test_task1_architecture.py` line 11.** Extend `forbidden_roots` with
`numpy`, `pandas`, `math`, `random`, `datetime`, `time`, `os`, `pathlib`, `json`, `socket`,
`urllib`.

**F21 (blocking) — `tests/unit/test_task1_architecture.py` lines 27–35.** Scan every engine module
including `ratios.py`; flag `ast.Constant` float literals in addition to `float(...)` calls; and
flag `Decimal(...)` and `Money(...)` calls whose argument is a float constant.

## 5. Countersignature

**Withheld.**

I do not counter-sign `docs/methodology.md` against master-prompt §§16, 19–30, and 42 at this
revision. The contract is well built and several elements exceed the prompt's floor — the §1.3
reason-code taxonomy, the §9.2 reweighting ceilings with exact Decimal weight sums, the §8.2
annuity mechanics with the explicit prohibition on `service × years`, the gapless and correctly
inverted §9.1 band inclusivity, and the §10 severe-scenario `improvement_justification`
requirement. Coverage against §20 is complete for leverage, coverage, cash flow, and profitability,
and against §33-adjacent result metadata it is consistent.

The withholding rests on four items. D1 and D2 leave two §14 golden outputs indeterminate, so the
committed golden hash cannot be treated as a verified expectation. D3 discards data the §29
covenant engine and §28 solvers require. D4 breaks the §25 derivation chain in the independent
Excel reference, which §37 and §42 make load-bearing for reconciliation. Separately,
`tests/unit/test_task1_architecture.py` is rejected outright: it is the only automated enforcement
of the numeric contract and it currently passes while enforcing nothing.

I will counter-sign once F1, F2, F3, F4, F14, and F18–F21 land and the golden is re-derived and
re-hashed.

---

Disposition: **approved-with-required-fixes**

METHODOLOGY_APPROVED_FOR_IMPLEMENTATION: no

Blocking fixes:

- F1 — `docs/methodology.md` §2.8 (with §2.7, §4.3, §14): eliminate the lease/rent double count in the DSCR denominator.
- F2 — `docs/methodology.md` §8.1: define `Existing Pro Forma Debt` and the leverage-capacity debt measure.
- F3 — `docs/methodology.md` §1.3 (with §1.2, §10): retain `value_exact` and compare covenants against it.
- F4 — `excel/formulas/core.yaml` `recommended_loan`: define the `dscr_capacity` derivation chain and floor the result at zero.
- F12 — `docs/methodology.md` §14: re-derive and re-hash the golden after F1 and F2.
- F14 — `tests/unit/test_task1_contracts.py` lines 31–34: reject integral floats, not only non-integral ones.
- F18 — `tests/unit/test_task1_architecture.py` line 7: resolve the engine root from `__file__` and assert it was scanned.
- F19 — `tests/unit/test_task1_architecture.py` line 13: use `rglob`.
- F20 — `tests/unit/test_task1_architecture.py` line 11: extend `forbidden_roots` to float-native, nondeterministic, and I/O modules.
- F21 — `tests/unit/test_task1_architecture.py` lines 27–35: scan `ratios.py`, float literals, and `Decimal(<float>)`.
