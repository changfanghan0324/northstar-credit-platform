# Claude Opus 5 Task 1 Re-Review — Round 1

- Captured verbatim from Claude Code session `cd83228c-c036-4edb-b22e-cb97dd3ff177`.
- Model identifier from the Claude Code stream: `claude-opus-5`.
- Claude Code CLI version observed by the Codex host: `2.1.221`.
- This round was read-only; its Bash requests were denied by the initial permission mode.

## Verbatim reviewer output
I have read all 18 files completely. Below is the review record.

---

# Task 1 Required-Fix Re-Review — Independent Non-Author Record

**Date:** 2026-08-04
**Reviewer:** Claude Opus 5 (non-author). Exact model identifier observable in this session's environment: `claude-opus-5`.
**Claude Code version:** **not observable.** Command execution was denied in this session, so I could not query it, and it is not exposed to me otherwise. I do not assert a version.
**Original implementation author:** Claude Opus 5. **Required-fix author:** Codex.
**Predecessors:** `docs/collaboration/methodology-signoff.md`, `docs/collaboration/methodology-rereview-claude.md`, `docs/collaboration/review-log.md`, `docs/collaboration/task1-rereview-request.md`.

No file was edited or created. I did not enumerate the workspace, did not use `find`, and did not inspect `.venv` or `.venv-rebuilt`.

---

## 1. Reproduction — commands and results

### 1.1 Bundle hash — NOT REPRODUCED

The request requires reproducing `29fe54d7ebe2e772c35fa99e54956addec1bded1eaf275287b3d07a412829700` with:

```sh
find packages/credit_engine/credit_engine tests/unit -type f -name '*.py' -print0 \
  | sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

I invoked exactly this command. **Result: denied.** Claude Code is running in "don't ask" permission mode and the Bash tool returned a permission denial, not a command failure. SHA-256 cannot be computed by inspection, and I did not attempt to circumvent the denial.

**I did not verify the bundle hash and I am not asserting it.** The same limitation applies to the three supporting digests recorded at `review-log.md:47` (methodology `1d15a855…`, verify `66930c9e…`, ignore-file `3be0ee4b…`) and to the `core.yaml` digest `0c22bf27…` that `methodology-rereview-claude.md` §5 left open. That §5 governance precondition therefore remains **unverified across two consecutive reviews**, which is itself worth recording.

### 1.2 `./scripts/verify` — NOT RUN

Denied by the same permission mode. **I did not independently reproduce the claimed 53 passing tests, 99.53% branch coverage, clean Ruff, or clean Mypy.** Every statement below about behavior is derived from reading source, not from execution. Where I assert an arithmetic result I derived it by hand and show the derivation.

This is a material gap against the request. Section 8 accounts for it in the disposition.

### 1.3 What I did instead

Manual re-derivation of every asserted numeric expectation (§3), hand-tracing of every guard ordering (§5), and adversarial search for inputs that reach a wrong or unsafely favorable state (§6).

---

## 2. File list and explicit coverage statement

Every listed file was read **in full**, in bounded chunks, with no sampling. Ranges are the actual read spans.

| File | Lines | Read spans | Coverage |
|---|---|---|---|
| `docs/collaboration/task1-rereview-request.md` | 62 | 1–62 | complete |
| `docs/collaboration/review-log.md` | 51 | 1–51 | complete |
| `docs/collaboration/methodology-rereview-claude.md` | 261 | 1–261 | complete |
| `docs/collaboration/methodology-signoff.md` | 360 | 1–360 | complete |
| `docs/methodology.md` | 362 | 1–250, 250–362 | complete |
| `packages/credit_engine/credit_engine/__init__.py` | 171 | 1–171 | complete |
| `packages/credit_engine/credit_engine/types.py` | 151 | 1–151 | complete |
| `packages/credit_engine/credit_engine/money.py` | 274 | 1–274 | complete |
| `packages/credit_engine/credit_engine/cashflow.py` | 254 | 1–254 | complete |
| `packages/credit_engine/credit_engine/ratios.py` | 1586 | 1–400, 400–800, 800–1219, 1219–1586 | complete |
| `tests/unit/test_task1_architecture.py` | 77 | 1–77 | complete |
| `tests/unit/test_task1_contracts.py` | 172 | 1–172 | complete |
| `tests/unit/test_task1_invariants.py` | 58 | 1–58 | complete |
| `tests/unit/test_task1_engine_complete.py` | 479 | 1–420, 420–479 | complete |
| `scripts/verify` | 37 | 1–37 | complete |
| `.gitignore` | 11 | 1–11 | complete |
| `pyproject.toml` | 32 | 1–32 | complete |
| `packages/credit_engine/pyproject.toml` | 14 | 1–14 | complete |

**Hunk-by-hunk coverage of the eight files named in the request's Scope:** `types.py` — all 151 lines including the new `NM_NO_CASH_BURN` member (L41), `FAVORABLE_NM_REASONS` (L51–57), `confidence_factors` on both `RatioResult` (L108) and `MoneyMetricResult` (L144). `money.py` — all 274 lines including the new known-exponent model validator (L105–113) and `PolicyConfigurationError` (L38–43). `cashflow.py` — all 254 lines including the §2.8 policy guard (L239–244). `ratios.py` — all 1586 lines; every one of the 40 public entry points and all six internal helpers traced individually. `test_task1_engine_complete.py` — all 479 lines; every assertion re-derived by hand. `docs/methodology.md` — all 14 sections. `.gitignore` and `scripts/verify` — every line.

---

## 3. Independent re-derivation of asserted values

I recomputed every numeric expectation by hand. **All are arithmetically correct.** Selected derivations:

| Assertion | Location | My derivation | Match |
|---|---|---|---|
| gross debt 80 | complete:109 | 10+5+60+4+1 | ✔ |
| adjusted debt 90 | :115 | 80+8+2 | ✔ |
| eligible cash 16 | :119 | 20 × 0.8 | ✔ |
| net debt 64 | :124 | 80−16 | ✔ |
| adjusted EBITDA 41 | :133 | (30+10)+3−2 | ✔ |
| adjusted EBIT 31 | :139 | 41−10 | ✔ |
| EBITDAR 45 | :146 | 41+4 | ✔ |
| CFADS 29 | :155 | 41−4−6−2 | ✔ |
| `scale_money(5, 0.5)` → **3** | :79 | 2.5 half-away-from-zero | ✔ (see F4) |
| FCC 2.1000 | :284 | (30−3−4−2)/(3+4+3) = 21/10 | ✔ |
| runway 6.0000 | :330 | (10+20−6)/4 = 24/4 | ✔ |
| positive FCF 0.6667 | :426 | 2/3 = 0.6666… → HALF_UP | ✔ |
| ROA 0.1111 | :432 | 10/((80+100)/2) = 10/90 | ✔ |
| ROIC 0.1667 | :448 | (20×0.75)/90 = 15/90 | ✔ |
| all 22 happy-path ratios | :185–206 | each recomputed | ✔ |

**Formula conformance to `docs/methodology.md`:** I checked all 40 metrics term-for-term against §§2–7. Every implemented formula reproduces the contract, including the three that the first sign-off specifically repaired — §2.8 excludes rent from debt service (`cashflow.py:221–248`), §6.4 uses **reported** EBITDA (`ratios.py:1136–1155`), §7.4 invested capital uses **unrestricted** cash (`ratios.py:1517–1526`). §4.4's numerator correctly omits pension and other mandatory uses (i.e. it is deliberately *not* `CFADS + rent`), matching N7 of the prior re-review, and the code says so at `ratios.py:689–692`. **I found no formula error, no currency error, and no type error.**

---

## 4. Checklist dispositions (all eight)

**1. Missing ratio inputs take precedence over favorable zero-denominator outcomes — SATISFIED.**
Verified at every guarded site by tracing statement order, not by reading comments: `safe_ratio` L210 (missing) precedes L225 (nonpositive) precedes L242 (zero); `_interest_style_coverage` L471 precedes L481; `debt_service_coverage` L589 precedes L600; `fixed_charge_coverage` L716 precedes the division; `liquidity_runway_months` L931 precedes L953. Composite-numerator metrics (`quick_ratio` L809, `short_term_debt_coverage` L885–888) null the numerator before dispatch, so a missing component beats a zero denominator. **One exception is not covered by this ordering — see F1.**

**2. Proposed principal participates in the DSCR currency guard — SATISFIED.**
`ratios.py:581` calls `ensure_same_currency(cfads_value, debt_service, proposed_principal)` **before** `_money_operands` and before every branch, so it also protects the missing and zero-service paths, not just the division path. `cfads_debt_service_coverage` (L653) inherits it by delegation. Covered by `complete:260–261`.

**3. Known ISO currencies reject an incorrect minor-unit exponent — SATISFIED.**
`money.py:105–113`, a `model_validator(mode="after")`, rejects any mismatch against `KNOWN_MINOR_UNIT_EXPONENTS` (USD/EUR/GBP 2, JPY 0, KWD 3). Covered by `complete:54–55`. Unknown codes still fall through to the generic 0–4 range check (L99–103), which is the correct conservative behavior — and `complete:72–73` confirms unknown-code pairs are still caught by the *scale* guard.

**4. Non-OK ratio results preserve formula and policy references — SATISFIED, but narrowly evidenced.**
`_non_ok` (L125–168) accepts and forwards both `formula_id` and `policy_ref`; all 12 call sites pass `formula_id`. However, **no public metric function accepts or supplies a `policy_ref`.** The only evidence for the policy-reference half is `complete:213–237`, which calls the low-level `safe_ratio` helper directly with `policy_ref="p-1"` — a path no production caller exercises. The six direct `_non_ok` call sites (`_interest_style_coverage`, `debt_service_coverage`, `fixed_charge_coverage`, `liquidity_runway_months`, `positive_fcf_years`, `_population_volatility`) do not forward `policy_ref` at all. Harmless today because none has one; a latent drop when §9 policy thresholds are wired in. See F6.

**5. Zero or negative stressed cash burn returns `nm_no_cash_burn` — SATISFIED.**
`ratios.py:953–969` branches on `burn <= 0` with two distinct interpretations for the zero and negative cases. `NM_NO_CASH_BURN` is a distinct member (`types.py:41`) inside `FAVORABLE_NM_REASONS` (L53) and deliberately separate from `NM_NO_OBLIGATION`, so policy cannot conflate liquidity with debt obligations. Both branches covered (`complete:332–346`).

**6. Single-period ROA and ROIC fallbacks are explicitly low confidence and preserve blocked states — SATISFIED.**
`_with_confidence_factor` (L1426–1457) sets `LOW` only when `result.is_ok`, otherwise passes `result.confidence` through unchanged — so a `MISSING`/`BLOCKED` result stays `BLOCKED` while still gaining the factor, and monotonicity per §13 holds. The preservation path **is** genuinely exercised, by `complete:454–456` (ROIC with `adjusted_ebit=None`, `beginning=None`, `ending` present → fallback applies to an already-blocked result). ROA's equivalent path is untested but shares the same helper. Interpretation replacement is correctly gated on `is_ok` (L1439) so an NM or missing explanation is never overwritten.

**7. Monetary metric results can carry confidence factors — SATISFIED AS A TYPE CAPABILITY ONLY.**
`MoneyMetricResult.confidence_factors` exists (`types.py:144`). But **no engine function ever populates it**: `working_capital`, `cash_plus_undrawn_revolver`, and `sources_uses_surplus` construct results at L850, L862, L991, L1003, L1050, L1065 and none passes the field. Correspondingly, `complete:370–379` verifies the item by **constructing a `MoneyMetricResult` literal inside the test**, then asserting the value it just passed in. That assertion cannot fail for any engine reason. It is not a false green masking a bug — the checklist says "can carry", which is literally true — but it is self-referential evidence. See F5.

**8. Fixed-charge coverage and liquidity runway are statically type-safe after missing-input guards — SATISFIED.**
`fixed_charge_coverage` L716 guards all seven inputs then narrows with seven `assert … is not None` (L729–735); `liquidity_runway_months` L931 guards four then narrows with four (L944–947). I confirmed the narrowing is sound under mypy's **default** settings (strict-optional is on by default), so this holds regardless of the strictness question in F3. The asserts are narrowing devices only — the preceding guards already returned — so stripping them under `python -O` is behaviorally safe.

---

## 5. Hidden-golden contamination assessment

**Method.** I derived every §14 golden output myself from the plaintext inputs at `methodology.md:359` and searched all four test files for each. I did not seek, open, or attempt to infer the sealed expected-value file.

**Golden outputs I derived and searched for:** gross debt 75; eligible cash 16; net debt 59; EBITDA 40; adjusted EBITDA 41; EBITDAR 45; CFADS 24; annual debt service 14; DSCR 24/14 = 1.7143; gross leverage 75/41 = 1.8293; net leverage 59/41 = 1.4390; FCC 29/18 = 1.6111; cash conversion 30/40 = 0.75; EBITDA margin 0.205; revenue growth 0.0526; EBITDA growth 0.0789; working capital 40; current ratio 2.0; quick ratio 1.25; runway 6.0; ROA 0.0889; ROIC 0.1611; CFADS volatility 0.0355; positive FCF years 1.0; leverage capacity 3.50 × 41 − 75 = 68.5.

**Result: no golden ratio-level output is asserted anywhere.** Every ratio expectation in the test suite uses non-golden operands and produces a non-golden magnitude. The two places that reuse golden *operand pairs* assert no magnitude: `contracts:142–146` uses `(75, 41)` but asserts only status, `isinstance`, `exponent == -4`, and `value_exact is not None`; `invariants:47–54` uses CFADS 24 but asserts only monotonic ordering. Both match what the prior re-review already recorded and accepted.

**One observation, advisory.** Three golden *monetary intermediates* are reproduced exactly in `test_task1_engine_complete.py`: eligible cash **16** (L116–119, from the golden's own inputs 20 and 0.8), adjusted EBITDA **41** (L133), and EBITDAR **45** (L146). The EBITDA/adjusted-EBITDA path reaches 41 from different components (30+10, +3/−2 rather than 28+12, +2/−1), but `eligible_cash` uses the golden inputs verbatim. Separately, `liquidity_runway_months` at L323–331 yields **6.0000**, numerically equal to the golden runway (16+10−8)/3, from unrelated inputs — I judge that coincidental.

**Disposition: not a breach.** All §14 inputs are published in plaintext at `methodology.md:359`; these three values are single-operation derivations from published data and disclose nothing an implementer could not compute directly. This is consistent with the standing finding (`methodology-signoff.md:149–155`, `methodology-rereview-claude.md:228–231`) that the commit-and-reveal control is anti-tamper, not anti-inference. It is nonetheless an avoidable overlap: if the sealed file records `eligible_cash = 16`, a repository test now asserts a value that also appears in the sealed file. Recommend perturbing those three fixtures (F8).

**Do the new tests reward an incorrect formula?** No. I re-derived all 22 parametrized ratios and all cashflow aggregates under inverted operands and confirmed each expectation fails. The five §42 invariants remain magnitude-free and directional. **One quantization contract is not discriminated — see F4.** I found no `pragma: no cover` used to hide a live path; the single instance (`cashflow.py:78`) marks a genuinely unreachable branch and is honestly annotated.

---

## 6. Findings, severity-ranked

### F1 — MEDIUM. Pro forma DSCR returns a *favorable* result when `proposed_principal` is omitted

`ratios.py:600–633`. The error branch fires only when `is_proforma and proposed_principal is not None and proposed_principal.is_positive()`. A caller who sets `is_proforma=True` and zero debt service but **omits** `proposed_principal` (it defaults to `None` at L562) falls through to `NM_NO_OBLIGATION` — a **favorable** reason in `FAVORABLE_NM_REASONS`.

Counterexample: `debt_service_coverage(cfads_value=Money(1000…), debt_service=Money(0…), is_proforma=True)` returns `status=NM`, `reason_code=nm_no_obligation`, `is_favorable_nm=True`, `confidence=None` (not blocked).

This is precisely the defect class the required-fix round existed to close. Checklist item 1 establishes that a missing input must beat a favorable zero-denominator outcome; here an *unsupplied* input produces exactly that favorable outcome, and the engine has the signal (`is_proforma=True`) to know better. `methodology.md:48` states the pro forma zero-service case "is an error and blocks decisioning."

**No test covers it.** `contracts:130–135` and `complete:248–250` both pass a positive principal. The 99.53% branch-coverage figure does not help: the false limb of the compound condition is satisfied by the `is_proforma=False` case at `complete:253`, so the branch counter is green while this semantic path is never entered.

**Required fix:** when `is_proforma=True`, `debt_service == 0`, and `proposed_principal is None`, return `MISSING` / `missing_input` with blocked confidence. Add a regression test.

### F2 — MEDIUM. `scripts/verify` cannot run from the declared environment: Ruff and Mypy are undeclared dependencies

`scripts/verify:33–35` invokes `python -m ruff` and `python -m mypy`. Neither tool appears in `pyproject.toml` `[project].dependencies` (L5–9), `[dependency-groups].dev` (L11–15, which lists only `pytest` and `pytest-cov`), or `packages/credit_engine/pyproject.toml`. An environment provisioned from these manifests fails at line 33 with `No module named ruff`, and `set -eu` aborts before any test runs.

This directly obstructs the independent reproduction the request mandates, and means the gate passes only on a hand-provisioned interpreter. **Required fix:** add pinned `ruff` and `mypy` to the dev dependency group.

### F3 — MEDIUM. The "strict Mypy" claim is not evidenced by any reviewed configuration

`review-log.md:49` records "strict Mypy checking for all five engine modules." `scripts/verify:35` runs `mypy packages/credit_engine/credit_engine` with **no `--strict` flag**, and **neither reviewed `pyproject.toml` contains a `[tool.mypy]` table.** Absent configuration, mypy runs in default mode: `disallow_untyped_defs`, `disallow_any_generics`, `warn_return_any`, and related checks are off.

I could not rule out a `mypy.ini`/`setup.cfg`/`.mypy.ini` outside my read scope, so I state this as unevidenced rather than false. But `pyproject.toml` was explicitly in scope and is the conventional location. Note this does **not** undermine checklist item 8 (§4), which holds under default settings. **Required fix:** either add `[tool.mypy] strict = true` (plus `ruff` rule selection — `[tool.ruff]` is likewise absent, so lint runs on the minimal default `E4,E7,E9,F` set and E501 is not enforced), or correct the review-log wording to match what is actually run.

### F4 — MEDIUM-LOW. No test distinguishes `ROUND_HALF_UP` from banker's rounding at the *ratio* quantum

`contracts:149–153` is the designated rounding test (fix F15). But `Decimal("1.23455")` quantized to `0.0001` yields **1.2346 under both `ROUND_HALF_UP` and `ROUND_HALF_EVEN`** — the retained digit would be 5 (odd), so half-even rounds up to 6 as well. The negative case is symmetric. The test therefore cannot fail if `ratios.py:90` were changed to `ROUND_HALF_EVEN` or to Python's builtin `round`.

This matters because `methodology-signoff.md:132–137` (D8/F13) identifies exactly this divergence as "the most common Excel/Python reconciliation failure," and the earlier re-review recorded the case as confirming half-away-from-zero — correct, but non-discriminating.

Compounding it, `assert_ok` (`complete:31–37`) compares with `result.value == Decimal(expected)`, and `Decimal.__eq__` is numeric: `Decimal("3") == Decimal("3.0000")` is `True`. So the 4-dp exponent is pinned for exactly **one** metric, at `contracts:145`.

The implementation is correct — `ratios.py:90` uses `ROUND_HALF_UP`, and `scale_money`'s HALF_UP *is* discriminated by `complete:79` (2.5 → 3, where banker's gives 2). This is a regression-protection gap, not a live bug. **Required fix:** add a discriminating case such as `1.23465 → 1.2347` (half-even would give 1.2346), and assert `.as_tuple().exponent == -4` inside `assert_ok`.

### F5 — MEDIUM-LOW. Checklist item 7 is evidenced by a self-referential test

Per §4 item 7: no engine function populates `MoneyMetricResult.confidence_factors`, and `complete:370–379` asserts against a literal the test itself constructed. **Recommended fix:** either populate the field on a real path (e.g. `working_capital` when a component is estimated), or restate item 7 in the log as a type-contract guarantee so the evidence matches the claim.

### F6 — LOW-MEDIUM. Fixed-charge coverage has no deferred-interest guard, so §4.1's false positive is reachable via §4.4

`fixed_charge_coverage` (`ratios.py:674–753`) sets `zero_denominator_reason=NM_NO_OBLIGATION` — favorable — and takes no `has_deferred_or_capitalized_interest` parameter. With PIK interest (cash interest 0), zero scheduled principal, and zero rent, FCC reports **favorable** NM on facts where `interest_coverage` correctly reports adverse `NM_DEFERRED_OBLIGATION` (L482–499). `methodology.md:158–162` does not mandate the guard, so this is a contract gap rather than a violation — but the §4.1 rationale applies identically, and the whole point of splitting favorable from adverse NM is to prevent this. **Recommended fix:** thread the flag through §4.4, or record the asymmetry as a deliberate methodology decision.

### F7 — LOW. `normalize_reported_amount` accepts non-finite and string inputs, failing with untyped exceptions

`money.py:232–273` rejects `float` and `bool` (L246) but does not check for `str` or non-finite `Decimal`. `Decimal("Infinity")` passes the whole-minor-unit check at L262 (`Infinity != Infinity` is `False`) and then raises `OverflowError` at L267 — not a domain error the API layer can map to a reason code. `Decimal("sNaN")` raises `decimal.InvalidOperation`. A `str` such as `"1.5"` is silently accepted via `Decimal(reported_value)` despite the `Decimal | int` annotation. This is inconsistent with `Money` itself, which is `strict=True`. **Recommended fix:** reject non-finite values and non-`(Decimal, int)` types explicitly.

### F8 — LOW (advisory). Golden intermediates reproduced in tests

Per §5: `eligible_cash(20, 0.8) → 16` uses the golden inputs verbatim; adjusted EBITDA 41 and EBITDAR 45 are golden intermediates. Not a breach. **Recommended:** perturb these fixtures so no repository test asserts a value that also appears in the sealed file.

### F9 — LOW (advisory), consolidated

- **`annual_debt_service` false rejection.** `cashflow.py:239` raises `PolicyConfigurationError` when `fixed_charges_deducted_in_cfads=True` even if `required_fixed_charges is None`, where nothing would be double-counted.
- **Negative denominators unguarded.** Metrics with `require_positive_denominator=False` (`secured_debt_to_total`, `current_ratio`, `quick_ratio`, `cash_ratio`, `short_term_debt_coverage`, `cfo_to_debt`, `fcf_to_debt`) divide by a negative denominator and return `OK`. Structurally impossible inputs, and domain validation belongs to the normalization layer — but nothing pins it here. Relatedly, `short_term_debt_coverage` treats offsetting components summing to zero as favorable `nm_no_obligation`.
- **F18's fix depends on assertions being enabled.** `test_task1_architecture.py:11,13` uses `assert` for its non-vacuity guard. Under `python -O` those vanish and the original vacuous-pass defect returns. Pytest does not run under `-O` by default; worth a comment.
- **Two `type: ignore` comments remain.** `ratios.py:1064` (`sources_uses_surplus`) and `ratios.py:296` (`_money_ratio(**options: object)`). I traced both and confirmed neither masks a live defect — at L1064 the L1049 guard guarantees a non-`None` template — but the second removes static checking of every ratio's option keywords.
- **`positive_fcf_years` returns a fraction** (0.6667) while `methodology.md:242` says "Count and percentage". Internally consistent with §7.1 growth; the docstring is explicit. Cosmetic.
- **`has_deferred_or_capitalized_interest` does not name §4.1's second limb** ("accrued interest has not materially increased"), which a caller must fold into the same flag.

---

## 7. What I confirmed is *not* wrong

Stated plainly so the record is balanced: I found **no formula error, no currency-handling error, no missing-data precedence bug in the ordering of the guards, no confidence-contract monotonicity violation, and no false-green test that rewards an incorrect formula.** All 22 parametrized ratios, all 12 cashflow aggregates, and all five §42 invariants are arithmetically correct and directionally enforcing. The seven C1–C8 defects from Codex's round-1 review are, on inspection of the code, closed. The architecture guards resolve from `__file__`, recurse with `rglob`, cover a broad forbidden-import set, and flag float calls, bare float literals, and `Decimal(<float>)`/`Money(<float>)` — matching F18–F21.

---

## 8. Disposition

**`approved-with-required-fixes`**

Two independent grounds, either sufficient on its own:

1. **The mandated reproductions did not occur.** Command execution was denied in this session. I did not verify the bundle hash `29fe54d7…`, the three supporting digests, or any part of `./scripts/verify`. The request makes both mandatory. No reviewer should record `approved` on a diff whose stated evidence they could not check, and F2 shows the script is in fact not runnable from the declared manifests, so that evidence needs re-establishing regardless of my permissions.
2. **F1 is a live defect in the exact class this fix round addressed** — an omitted optional input yielding a *favorable* result where the methodology requires a blocking one, unprotected by any test and invisible to the branch-coverage figure.

**Blocking, before Task 1 may be marked accepted:**

- **F1** — `ratios.py:600–633`: return `MISSING` / `missing_input` when `is_proforma=True`, debt service is zero, and `proposed_principal is None`; add the regression test.
- **F2** — `pyproject.toml`: declare pinned `ruff` and `mypy` in the dev dependency group so `./scripts/verify` runs from a clean provision.
- **F3** — add `[tool.mypy]` (and `[tool.ruff]`) configuration, or correct `review-log.md:49` to state what is actually enforced.
- **F4** — add a rounding case that discriminates `ROUND_HALF_UP` from `ROUND_HALF_EVEN` at the ratio quantum, and assert the 4-dp exponent inside `assert_ok`.
- **Reproduction** — the bundle hash and `./scripts/verify` must be reproduced by a non-author with execution capability, and the `core.yaml` digest `0c22bf27…` left open at `methodology-rereview-claude.md:175–196` must finally be checked. Neither of the two Claude re-reviews has been able to run a command.

**Non-blocking, to record and schedule:** F5, F6, F7, F8, F9.

I will re-review these fixes before Task 1 is marked accepted, as `task1-rereview-request.md:61` requires.

TASK_1_ACCEPTED: no

