# Methodology Re-Review — Claude Opus 5 (independent reviewer)

Date: 2026-08-03
Reviewer: Claude Opus 5 (non-author)
Author under review: Codex
Predecessor: `docs/collaboration/methodology-signoff.md` (disposition: approved-with-required-fixes)
Reference: `Project_2_Codex_Claude_Master_Prompt_v2.md`, §§16, 19–30, 42

Scope: the eleven files changed in response to the sign-off. No file was edited. I did not request,
search for, open, or attempt to infer the hidden golden plaintext.

---

## 1. Hunk coverage

| File | Hunks reviewed | Coverage |
|---|---|---|
| `docs/methodology.md` | §1.2, §1.3, §2.8, §5.7–5.8 (new), §6.4, §7.4, §8.1, §9 preamble, §9.3, §10, §14 | all 11 changed regions read line-by-line; unchanged sections re-checked for consistency with the edits |
| `excel/formulas/core.yaml` | header `rounding`; `annual_debt_service`; `maximum_total_debt` / `incremental_leverage_capacity_raw` / `leverage_capacity` (replacing one key); `periodic_payment`, `dscr_capacity` (new); `annuity_capacity`; `recommended_loan`; `reason_code_contract` (new) | all 8 changed regions; full file re-read for reference integrity |
| `tests/unit/test_task1_contracts.py` | imports (L15–23); L33–37; L51–55; L130–135; L138–142, L145–148, L151–154, L157–160 (new) | all 8 changed regions; whole file re-read for contamination |
| `tests/unit/test_task1_invariants.py` | import L5; status assertions L15, L22, L29, L36, L43; scope comment L47–48 | all 7 changed regions |
| `tests/unit/test_task1_architecture.py` | L7–15 (root resolution + `engine_modules`); L18–35; L38–54 | whole file rewritten; every line reviewed |
| `docs/collaboration/independence-log.md` | superseded block L3–13; amended block L15–24 | both hunks |
| `docs/collaboration/disagreement-log.md` | D-003 L22; D-006 retitle/rewrite L39–43; D-008 new L45–50 | all 3 hunks |
| `docs/collaboration/decision-log.md` | date/owner/reviewer lines on DEC-001–007; DEC-007 outcome L57; DEC-008 new L59–67 | all 9 hunks |
| `docs/collaboration/review-log.md` | entry L20–27 | 1 hunk |
| `docs/architecture/data-model.md` | L21 | 1 hunk |
| `docs/implementation-plan.md` | L15 | 1 hunk |

## 2. Blocking-fix dispositions

### F1 — lease/rent double count — **resolved**

`docs/methodology.md` §2.8 now reads "required finance-lease or fixed-charge payments **not already
deducted in CFADS**" and adds the operative rule: finance-lease principal and interest qualify;
where policy includes contractual rent, the same rent must be added back to the numerator and the
metric becomes fixed-charge coverage (§4.4), not DSCR; a configuration that includes rent without
the matching add-back is invalid. §14 now states "no additional fixed charge in DSCR" and
"contractual operating rent 4 used only in fixed-charge coverage with the EBITDAR add-back".
`core.yaml` `annual_debt_service` mirrors the wording.

I re-derived the boundary: rent now appears in exactly one place per metric — inside EBITDA/CFADS
for DSCR, and added back to EBITDAR against the denominator for FCC. Finance-lease payments, which
sit below EBITDA as D&A and interest, correctly remain additive to debt service. The defect is
closed and the §14 DSCR input set is now determinate.

### F2 — leverage-capacity operands — **resolved**

§8.1 defines `Existing Pro Forma Debt` as existing debt adjusted for committed transactions that
close regardless of this request, explicitly excluding the proposed facility — removing the
circularity. It requires the policy limit to declare gross, adjusted, or net and the same measure on
both sides, and names gross debt for the §14 golden. §14 now says "a gross-debt 3.50x maximum
leverage limit". `core.yaml` splits the former single key into `maximum_total_debt`,
`incremental_leverage_capacity_raw`, and `leverage_capacity`, with the raw negative headroom
preserved (this also closes non-blocking F5).

The golden is now single-valued: `3.50 × 41 − 75 = 68.5`. The prior 68.5-vs-84.5 ambiguity is gone.

### F3 — exact ratio value — **resolved**

§1.2 rewritten: `value_exact` is retained unquantized; `value` is the four-decimal `ROUND_HALF_UP`
display and score-banding value; "Covenant pass/breach, covenant headroom, and reverse-stress
convergence use `value_exact`, never the displayed value." §1.3 adds the field to `RatioResult`.
§10 repeats the rule for covenant comparisons and headroom and adds the conservative-rounding
fallback. `data-model.md` L21 adds the persisted column. `test_task1_contracts.py` L135 asserts
`result.value_exact is not None`.

The 1.24996-rounds-into-a-pass path is closed, and the §28 solvers now have precision below the
display quantum.

### F4 — `recommended_loan` chain — **resolved**

`core.yaml` adds `periodic_payment` (`available_new_debt_service / payments_per_year`) and
`dscr_capacity` (`={annuity_capacity}`), completing the chain
`maximum_annual_debt_service → available_new_debt_service → periodic_payment → annuity_capacity →
dscr_capacity`. `recommended_loan` is now `=MAX(0,MIN(...))`, so an unfloored collateral capacity
(§8.4, which nets prior liens and reserves) can no longer emit a negative recommended loan. Every
name referenced in `recommended_loan` now resolves within the file.

### F12 — golden re-derivation and re-hash — **resolved (procedurally)**

`independence-log.md` marks the original commitment "superseded", preserves both original digests
for audit, and records an amended commitment with new golden and formula digests, an amendment
reason naming the DSCR rent exclusion, the gross-debt capacity basis, and the new DSCR-capacity
chain. This matches the amendment procedure the log itself defines. See §5 for the one verification
step I could not perform.

### F14 — strict float rejection — **resolved**

`test_task1_contracts.py` L33–37 now asserts that both `Money(amount_minor=1.5)` and
`Money(amount_minor=2.0)` raise. The integral-float lax-coercion hole is closed; the test can no
longer pass against a contract that accepts floats.

### F18 — vacuous pass — **resolved**

L7–8 resolve `REPO_ROOT` from `Path(__file__).resolve().parents[2]`. I verified the arithmetic:
`parents[0]` = `tests/unit`, `parents[1]` = `tests`, `parents[2]` = repository root. `engine_modules()`
asserts `ENGINE_ROOT.is_dir()` with the path in the message and asserts the module list is non-empty,
so both tests now fail loudly rather than passing against a missing engine or a non-root CWD.

### F19 — recursive scan — **resolved**

L13 uses `rglob("*.py")`; subpackages can no longer escape either guard.

### F20 — forbidden import set — **resolved**

L19–22 now covers `apps`, `datetime`, `fastapi`, `httpx`, `json`, `math`, `numpy`, `os`, `pandas`,
`pathlib`, `random`, `requests`, `socket`, `sqlalchemy`, `time`, `urllib` — the float-native,
nondeterministic, I/O, and network roots I named. Consistent with ADR 0001's purity rule. Note that
excluding `datetime` is correct rather than restrictive: calculation-run timestamps belong to the
persistence layer and must be injected into the engine, never read inside it.

### F21 — float AST guard — **resolved**

L38–54 now scans every engine module via `engine_modules()` (including `ratios.py`, the division
site the previous version omitted), and flags three patterns: `float(...)` calls, bare `ast.Constant`
float literals, and `Decimal(...)` / `Money(...)` constructed from a float constant. I traced two
edge cases: a negative literal such as `-0.8` parses as `UnaryOp(USub, Constant(0.8))` and the inner
`Constant` is still reached by `ast.walk`, so it is caught; and `Decimal(value=1.5)` passed by
keyword escapes the third check but is caught by the generic literal check. Coverage is sound.

**All ten blocking fixes are resolved.**

## 3. Non-blocking fixes also applied

| Fix | Disposition | Note |
|---|---|---|
| F5 — split leverage keys | applied | Three keys; raw negative headroom preserved per §8.1. |
| F6 — Excel reason codes | **partially applied** | A `reason_code_contract` block now declares the four guarded metrics and all seven required states — a real improvement. But no `excel_template` emits a status or reason cell; `interest_coverage` and `dscr` still return a uniform `NA()`. The contract is declared, not yet implemented in formulas. Carry to the §37 workbook. |
| F7 — liquidity gaps | applied | §5.7 `metric.cash_plus_undrawn_revolver` and §5.8 `metric.sources_uses_surplus`. §5.8 is well specified: explicit horizon label, component preservation, shortfall semantics, and no assumed uncommitted refinancing — the last point correctly enforces §11.2. |
| F8 — cash conversion | applied | Now `CFO / Reported EBITDA`, both unadjusted, with the rationale recorded. Basis mismatch closed. |
| F9 — ROIC | applied | Invested capital uses unrestricted cash; the lending-policy availability factor is explicitly excluded from the return metric. |
| F10 — score sub-weights | applied | §9 states the full §21 vector. I re-verified: 18+18+10+10+9 = 65 and 10+7+6+4+5+3 = 35. |
| F11 — grade bands | applied | §9.3 restated half-open. I checked real-line coverage: `0` → Grade 10, `(0,34)` → 9, `[34,42)` → 8, `[42,50)` → 7, `[50,58)` → 6, `[58,66)` → 5, `[66,74)` → 4, `[74,82)` → 3, `[82,90)` → 2, `[90,100]` → 1. Gapless and non-overlapping over `[0,100]`; the 89.5 hole is closed and §23's integer intent is preserved. |
| F13 — rounding note | applied | Header records the Excel `ROUND` / Decimal `ROUND_HALF_UP` equivalence including negatives, and prohibits Python's builtin `round`. |
| F15 — quantization and typed error | applied | `CurrencyMismatchError` replaces the message-substring match. `test_round_half_up_contract_uses_non_golden_inputs` asserts `1.23455 → 1.2346` and `-1.23455 → -1.2346`; I confirmed both are correct for half-away-from-zero and that neither input touches the golden. |
| F16 — missing edge cases | mostly applied | Net cash as a valid negative ratio (`-10/20 → -0.5000`), structural `0/0 → NM_UNDEFINED`, and currency mismatch raised from inside `ebitda()` are all added. §3.5's nonpositive-equity adverse case is still untested — see N5. |
| F17 — invariant status assertions | applied | All five invariants now assert `RatioStatus.OK` before comparing; L47–48 records the §42 scope boundary. |
| F22 / F23 — decision-log | applied | DEC-007 records the withheld countersignature and its five causes; all seven prior entries carry date, owner, reviewer, and model identifier per §0.3. |
| F24 — D-003 evidence | applied | The user-value argument (side-by-side audit of the same line items across Base/Downside/Severe) is now the stated deciding evidence. |
| F25 / F27 — anti-tamper wording | applied | D-006 retitled "Review anti-tamper timing" and both logs now state that published inputs remain inferable and the control prevents unlogged post-hoc edits. This is the accurate claim. |
| F26 — review-log entry | applied | Entry records author, reviewer, model ID, evidence, mixed dispositions including the rejection, required fixes, and that nothing is accepted pending re-review. |
| F29 — Excel sequencing | applied | DEC-008 records the deviation with rationale, risk, and reversibility; `implementation-plan.md` L15 cross-references it. |

## 4. Remaining findings (all non-blocking)

- **N1** — `disagreement-log.md`: D-008 is inserted between D-006 and D-007. Cosmetic ordering only.
- **N2** — `core.yaml`: F6 partially applied; the declared `reason_code_contract` has no formula-level
  emission. Until the workbook emits status cells, §42's Excel/Python reconciliation compares
  magnitudes only, not reason codes.
- **N3** — `core.yaml`: `{periodic_rate}` and `{payment_count}` are consumed by `annuity_capacity` but
  never derived. The §14 golden is annual (`payments_per_year = 1`), so it is unaffected, but
  frequency conversion is exactly where amortization errors occur. Add derived keys
  `periodic_rate = annual_rate / payments_per_year` and `payment_count = years × payments_per_year`
  before the §37 workbook.
- **N4** — `methodology.md` §2.8: the rent-without-add-back configuration is declared "invalid" but no
  reason code or error path is assigned. Recommend routing it to `error_invalid_input` or a distinct
  policy-validation error so it surfaces the same way as the pro forma zero-service case.
- **N5** — `test_task1_contracts.py`: §3.5's nonpositive-equity adverse case remains untested, so
  nothing pins that a negative Debt/Equity is never reported as favorable.
- **N6** — `test_task1_contracts.py` L77: `required_fixed_charges=usd_millions(1)` is now inconsistent
  in spirit with §14's "no additional fixed charge in DSCR". Harmless — this is a type-shape test with
  arbitrary inputs, not a golden test — but a one-line comment would prevent a future reader from
  reading it as a golden.
- **N7** — `methodology.md` §4.4: the FCC numerator deliberately omits mandatory pension and other
  mandatory operating cash uses, so it is *not* `CFADS + rent`. This is faithful to §19's literal
  text and I am not asking for a change; recommend a one-line note so an implementer does not
  "harmonize" the two numerators.
- **N8** — `test_task1_architecture.py`: the AST guard cannot catch `Decimal(x)` where `x` is a float
  *variable*. This is an inherent static limit; complement it with runtime type validation inside
  `Money` and the ratio constructors rather than extending the AST scan.

None of these affect a formula result, a golden value, or a decision path.

## 5. Verification I could not perform

The re-review asked me to confirm that `excel/formulas/core.yaml` currently hashes to the amended
digest `0c22bf27006282e4309da4f7b4ee8e9abc6178402a4b0a0ffced2c84985caa29` recorded in
`independence-log.md`.

**I did not verify this, and I am not asserting it.** This invocation has no shell or command
execution available to me, and SHA-256 cannot be computed by inspection. I confirmed only what
reading permits: the file exists at the logged path, its content matches the F1/F2/F4/F5/F6/F13
fixes the amendment reason describes, and the digest is a well-formed 64-character hex string
distinct from the superseded one.

Run before implementation begins:

```
shasum -a 256 excel/formulas/core.yaml
```

It must print `0c22bf27006282e4309da4f7b4ee8e9abc6178402a4b0a0ffced2c84985caa29`. If it does not, the
log is stale relative to the file and the amended commitment must be re-issued under the procedure in
`independence-log.md` before any engine code is written. This is a governance precondition, not a
methodology defect — no formula outcome depends on it.

## 6. Counter-signature

I counter-sign `docs/methodology.md` (as amended) and `excel/formulas/core.yaml` (as amended) against
master-prompt §§16, 19–30, and 42, subject to the §5 hash check.

Basis for the countersignature:

- **§16** — adjustments require evidence, rationale, cash/non-cash and recurrence flags, and explicit
  approval; the 15% enhanced-review trigger is configurable and nothing auto-approves.
- **§19** — every listed formula is present and reproduces the prompt term-for-term; divide-by-zero,
  NM, component visibility, and reported-vs-adjusted rules are all honoured, and the newly separated
  `value` / `value_exact` pair means threshold comparison no longer depends on display rounding.
- **§20** — all five ratio families are now complete, including the two liquidity metrics added at
  §5.7–5.8.
- **§21, §23** — the 65/35 split, the full default sub-weight vector, the three illustrative band
  sets, and the grade map are stated as policy data with gapless, non-overlapping, explicitly
  inclusive bands.
- **§22** — critical-data blocking, within-category-only reweighting, and the 15%/30% ceilings.
- **§24** — facility protection is separate and cannot improve the obligor grade.
- **§25** — leverage, DSCR, bullet, collateral, and policy capacities with a determinate debt basis,
  exact annuity mechanics, the explicit prohibition on `service × years`, a floored five-way minimum,
  and a named binding constraint.
- **§26–§30** — deterministic three-year scenarios that are never labelled probabilities, the severe
  `improvement_justification` requirement, exact-value covenant headroom, bounded declarative reverse
  stress, and the five decision outcomes with their blocking conditions.
- **§42** — the three pre-implementation test files now enforce rather than merely assert: the float
  contract is strict, the purity and float guards fail loudly instead of passing vacuously, five §42
  invariants are pinned with status assertions and remain non-golden, and no expected golden
  magnitude appears in any test file.

**Contamination re-check: clean.** The only added numeric expectations are `1.23455 → 1.2346`,
`-1.23455 → -1.2346`, and `-10/20 → -0.5000`. None derives from the §14 golden inputs, and the two
quantization cases are explicitly named non-golden. `(75, 41)` still appears at L131 but asserts only
type, exponent, and `value_exact is not None`, revealing no magnitude.

The methodology is safe to implement. The four formula and semantic defects that blocked the first
sign-off are closed, the golden case is determinate under a single reading, and the guard tests now
fail when the contract is violated.

## 7. Task 1 authorship authorization

Per `task-ownership.md` row 2, Claude Opus 5 authors credit primitives, the policy loader, debt
capacity, and reverse stress, with Codex as reviewer. Subject to the §5 hash check passing, **I
authorize myself to begin Task 1 engine authorship in a subsequent invocation**, implementing
`packages/credit_engine/credit_engine/` — `money.py`, `types.py`, `cashflow.py`, `ratios.py` — against
this amended contract.

Conditions I hold myself to:

1. Run the §5 hash check first and stop if it does not match.
2. Implement only against `docs/methodology.md`; do not seek, open, or reconstruct the hidden golden
   plaintext, and do not modify any test to make it pass.
3. Treat the three pre-implementation test files as fixed acceptance criteria.
4. Submit every diff to Codex for non-author line-level review under §0.4 before anything is marked
   complete.
5. Raise N2–N8 as follow-ups rather than silently resolving them inside engine code.

---

Disposition: **approved** (methodology and Excel formula specification counter-signed;
`test_task1_architecture.py` rejection lifted)

METHODOLOGY_APPROVED_FOR_IMPLEMENTATION: yes
