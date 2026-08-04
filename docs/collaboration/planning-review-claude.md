# Planning and Test Review — Claude Opus 5 (independent reviewer)

Date: 2026-08-03
Reviewer: Claude Opus 5 (non-author)
Author under review: Codex
Change set: all files are new and untracked, so each file is a single add-hunk; coverage below is
stated section-by-section within each hunk, per master prompt §0.4.
I edited no Codex-authored file and no test.

Legend: `approved` · `approved-with-required-fixes` · `rejected`

---

## 1. `tests/unit/test_task1_contracts.py` — approved-with-required-fixes

| Lines | Content | Disposition |
|---|---|---|
| 1–29 | Imports, `USD`, `usd_millions` | approved. Helper is exact integer math (`value * 100_000_000`), no float path. |
| 31–34 | `test_money_rejects_binary_float` | **required fix (blocking, R15)** |
| 36–45 | JPY normalization | approved. 1234 × scale 1000 → 1_234_000 minor units at exponent 0 is correct; this is the exponent bug §1.1 exists to prevent. |
| 47–51 | Currency mismatch | approved-with-required-fixes (R17) |
| 54–77 | Cashflow return types | approved. Asserting `isinstance(amount_minor, int)` is the right shape guard, and `bool` is not a realistic false positive here. |
| 80–85 | Negative EBITDA leverage | approved. Correctly demands adverse NM with `value is None` rather than a signed number — this is the §42 "negative EBITDA" case and it forbids the common wrong answer. |
| 87–91 | Missing vs NM | approved. Enforces the §22 distinction that missing is not "not meaningful". |
| 93–105 | Zero cash interest / PIK | approved. The strongest test in the file: it makes the favorable-vs-adverse split falsifiable and cannot be satisfied by a single NM state. |
| 108–123 | Existing vs pro forma zero service | approved. Correctly requires `ERROR`, not NM, for positive proposed principal with zero pro forma service. |
| 126–130 | 4-dp quantization | approved-with-required-fixes (R18) |

**R15 (blocking).** `Money(amount_minor=1.5)` raises under Pydantic v2 lax mode only because
1.5 is non-integral. An integral float `2.0` is silently coerced to `2` in lax mode, so this
test passes against a contract that accepts floats — the exact defect it is named for. Add an
assertion that `Money(amount_minor=2.0)` also raises, or configure the model `strict=True`.
As written this test can reward an incorrect implementation.

**R17 (non-blocking).** `pytest.raises(ValueError, match="currency")` — the message substring is
untyped. Prefer a typed `CurrencyMismatchError` so the API layer can map it to the
`currency_mismatch` reason code methodology §1.1 requires.

**R18 (non-blocking).** Asserting only `exponent == -4` accepts any magnitude. Add one
`ROUND_HALF_UP` boundary case with a literal expected Decimal on non-golden inputs (e.g. a value
whose fifth decimal is exactly 5, and one negative-value case, since Decimal `ROUND_HALF_UP` and
Python's builtin `round` disagree). Without it the quantization mode is untested.

**Golden contamination check — clean.** Lines 127 use `(75, 41)`, which are the §14 golden gross
debt and adjusted EBITDA, but the test asserts only the exponent and reveals no result. Every
§14 *input* is already published in plaintext in `docs/methodology.md`, so no test here leaks
anything the implementer cannot already read. Recorded observation, not a defect: the
commit-and-reveal control in `independence-log.md` is therefore anti-tamper (it prevents
retro-fitting expected values to the implementation), not anti-inference. That claim should be
worded accordingly — see §6.

**Missing edge semantics (non-blocking, R19).** Against master §42's ten required cases, this
file covers negative EBITDA, zero interest, and missing critical data. Not covered and in Task 1
reach: **net cash** (§42 case 5 — methodology §3.3 says a negative Net Debt / EBITDA is a *valid*
ratio, not NM; nothing pins this and an implementer could plausibly return NM); nonpositive
equity as adverse (§3.5); `nm_undefined` for structural 0/0 (§1.3); and currency mismatch raised
from inside a cashflow function rather than only from `ensure_same_currency` directly.

## 2. `tests/unit/test_task1_invariants.py` — approved-with-required-fixes

| Lines | Content | Disposition |
|---|---|---|
| 1–8 | Imports, helper | approved |
| 11–14 | Lower EBITDA ≠ better leverage | approved |
| 17–20 | Higher debt ≠ better leverage | approved |
| 23–26 | Lower EBITDA ≠ better coverage | approved |
| 29–32 | Higher interest ≠ better coverage | approved |
| 35–38 | Higher service ≠ better DSCR | approved |

I independently checked each invariant against an inverted implementation (numerator and
denominator swapped) and confirmed all five fail under inversion rather than passing — these
do not reward a wrong formula. Inputs are non-golden.

**R20 (non-blocking).** No test asserts `status is RatioStatus.OK` before comparing `.value`.
If a formula returns NM the comparison raises `TypeError` and the test fails, so this is not a
false green — but the failure is uninformative. Add the status assertion.

**R21 (non-blocking).** Five of master §42's eleven invariants are present. The remaining six
(rate→coverage as a distinct rate path, severe-scenario non-improvement, recommended loan ≤
binding capacity, missing critical data blocks approval, score components sum, memo equals
engine, Excel reconciles) belong to later modules. Record this scope statement in the file or
in `review-log.md` so the gap reads as sequencing rather than omission.

## 3. `tests/unit/test_task1_architecture.py` — **rejected**

| Lines | Content | Disposition |
|---|---|---|
| 7 | `ENGINE_ROOT = Path("packages/credit_engine/credit_engine")` | rejected (R16a) |
| 10–24 | Import-boundary guard | rejected (R16b, R16c) |
| 27–35 | Float-constructor guard | rejected (R16d) |

This file is rejected rather than approved-with-fixes because all four defects are
**false greens**: the suite reports success while enforcing nothing. These two tests are the
only automated enforcement of ADR 0001's purity rule and methodology §1.1's no-binary-float
rule, so a silent pass is worse than no test.

**R16a (blocking).** `ENGINE_ROOT` is a CWD-relative path and `packages/credit_engine/credit_engine`
does not exist yet. `Path(...).glob("*.py")` on a missing directory yields nothing, `violations`
stays empty, and both tests pass. They also pass when pytest is invoked from any directory other
than the repo root — `pythonpath` in `pyproject.toml` is rootdir-relative, but CWD is not.
Fix: resolve the root from `__file__` (e.g. `Path(__file__).resolve().parents[2] / "packages/..."`)
and assert `ENGINE_ROOT.is_dir()` and that at least one module was scanned.

**R16b (blocking).** `glob("*.py")` is non-recursive; any subpackage under `credit_engine/`
escapes the import-boundary check entirely. Use `rglob("*.py")`.

**R16c (blocking).** `forbidden_roots = {"apps", "fastapi", "sqlalchemy", "requests", "httpx"}`
does not enforce what ADR 0001 states ("no I/O, database, web framework, or network imports")
and does not enforce determinism. Add at minimum `os`, `pathlib`, `open` usage, `json`, `random`,
`datetime`, `time`, `socket`, `urllib`, and — because they are float-native and would silently
defeat the Decimal contract — `numpy`, `pandas`, and `math`.

**R16d (blocking).** The float guard is the narrowest control in the change set and misses the
most likely defect sites:
- it scans only `money.py` and `cashflow.py`, **not `ratios.py`** — the file where division
  happens and where a float will actually appear;
- it detects only `float(...)` calls, so a bare float literal (`0.8` for the cash-availability
  factor, `1.25` for a DSCR threshold) passes;
- it does not detect `Decimal(1.5)` — constructing a Decimal from a float literal, which is the
  classic way to inherit binary error while appearing to honour the contract.
Fix: scan every engine module; flag `ast.Constant` float literals; flag `Decimal(...)` and
`Money(...)` calls whose argument is a float constant.

## 4. `docs/collaboration/task-ownership.md` — approved

Single hunk, lines 1–18. Nine modules, alternating authorship, non-author reviewer on every row.
Satisfies §0.2 (neither agent writes everything, neither is a passive consultant) and §44 (both
write and review meaningful code). Deviates from §44's *example* split — Claude authors credit
primitives, capacity, reverse stress, stress, decision, and memo provenance rather than acting as
reviewer-only — but §44 marks its split "subject to debate" and this allocation is strictly
better for §0.2 because it gives Claude real implementation ownership. Row 1 (Codex authors the
methodology contract, Claude reviews) is consistent with DEC-007 and is the basis of this review.
Line 18's per-review requirements match §0.4 exactly. No fixes.

## 5. `docs/collaboration/decision-log.md` — approved-with-required-fixes

| Entry | Disposition |
|---|---|
| DEC-001 Product and audience | approved — resolves D-001; §3 permits either direction and the rationale (a borrower cannot perform or own the underwriting judgment) is sound. |
| DEC-002 MVP scope | approved — deferrals (live SEC fetch, auth, ML, Monte Carlo, AI narrative, `.pbix`) are all explicitly discouraged or optional in §2/§36/§43, and each has a named replacement. |
| DEC-003 Architecture | approved — matches §34 and ADR 0001; microservices rejected per §34. |
| DEC-004 Numeric contract | approved — the four named failure modes are the right ones. |
| DEC-005 Two-level experience | approved — additive-only resolves §7.2's "must not duplicate the whole application" and is testable. |
| DEC-006 Deployment security | approved — matches §43's "do not add authentication unless it serves the demo". |
| DEC-007 Independent verification | **required fix (non-blocking, R22)** |

**R22.** DEC-007 lists the risk "shared methodology can be wrong" with the control "Claude
counter-signature before implementation." That control has now executed and returned
*approved-with-required-fixes*, not approval. Amend DEC-007 to record the outcome and the four
blocking items, so the log does not imply a clean countersignature.

Each entry carries decision, alternatives, risks, and reversibility. §0.3 also requires
implementation owner, reviewer, date, and model identifier per decision; only DEC-001 names an
owner/reviewer pair and none names a date or model ID. **R23 (non-blocking):** add those four
fields to DEC-002 through DEC-007.

## 6. `docs/collaboration/disagreement-log.md` — approved-with-required-fixes

| Entry | Disposition |
|---|---|
| D-001 Primary persona | approved — consistent with DEC-001 and `personas.md`. |
| D-002 Guided/analyst modes | approved — a genuine position change with a named failure mode and automated parity tests; consistent with DEC-005 and `case-workflow.md`. |
| D-003 Excel scope | approved-with-required-fixes (R24) |
| D-004 Confidence | approved — consistent with methodology §13. |
| D-005 Zero-denominator semantics | approved — this is the debate that produced methodology §1.3, the best part of the contract; the recorded positions and resolution match the shipped taxonomy exactly. |
| D-006 Review independence | **required fix (non-blocking, R25)** |
| D-007 Public writes | approved — allowlist rather than method-based denial is the correct choice per §43. |

**R24 (non-blocking).** D-003 resolves in Codex's favour on all 20 sheets. §37 requires the 20
tabs, so the resolution is right, but §0.5 prefers the simpler option absent clear user value;
record the user-value argument (side-by-side scenario audit) as the deciding evidence rather
than leaving it as an assertion.

**R25 (non-blocking).** D-006 frames commit-and-reveal as protecting "independent verification."
It protects against post-hoc amendment of expected values. It cannot prevent inference, because
every §14 input is published in plaintext in `methodology.md` and the calculations are
deterministic. State the narrower, accurate claim — an overstated control is a governance risk.

## 7. `docs/collaboration/review-log.md` — approved-with-required-fixes

Single hunk, lines 1–20. The required-fields list matches §0.4 completely (diff SHA, hunk
coverage, independent reproduction, disposition, re-review evidence). Honest that nothing has
been accepted.

**R26 (non-blocking).** §0.4 requires *every* changed file to be reviewed by the non-author, and
the planning documents are themselves Codex-authored changed files. Add an entry for this review
citing `methodology-signoff.md` and `planning-review-claude.md`, dispositions
`approved-with-required-fixes` / `rejected` for the architecture test, and the required-fix list.

## 8. `docs/collaboration/independence-log.md` — approved-with-required-fixes

Single hunk, lines 1–13. Both SHA-256 values are well-formed 64-hex digests, the formula-spec
path resolves to a file that exists, the derivation source is named, and the amendment procedure
(new hash plus a disagreement-log entry citing the methodology clause) is correct.

**R27 (non-blocking).** "Golden plaintext status: held outside the project workspace and not
available to the implementing agent" — see R25. The inputs are in-repo; only the derived values
are withheld. Reword to claim anti-tamper, not unavailability of the underlying information.

**R28 (blocking, procedural).** Methodology fixes R1 and R2 change the DSCR and leverage-capacity
goldens. Re-derive, re-hash, and log the amendment before Task 1 implementation begins.
Implementing against the current hash would lock in a value derived from an ambiguous contract.

## 9. `docs/product/personas.md` — approved

Single hunk, lines 1–35. §3 requires one primary and at most two secondary personas: satisfied
(junior credit analyst; recruiter/interviewer, finance student). Every §3 required field is
present for all three — goals, knowledge level, jobs to be done, common errors, required
explanations, information tolerance, success criteria. The explicit-exclusions section is beyond
the prompt's floor and is good practice. The "common errors" entries are substantive and
directly shape UI requirements (NM read as zero, service × years capacity, collateral mistaken
for repayment, scenarios mistaken for probabilities) and trace to methodology §1.3, §8.2, §11.2,
and §10 respectively. Consistent with DEC-001 and D-001. No fixes.

## 10. `docs/product/homepage-wireframe.md` — approved

Single hunk, lines 1–44. Checked against §6 clause by clause: header matches §6.1 (five items
plus optional Help, no technical modules); hero question, supporting statement, and both CTAs
match §6.2 verbatim; exactly three outcome cards with a `Why?` action match §6.3; the four
workflow steps match §6.4; recent cases capped at five with the exact five columns match §6.5;
trust section and footer match §6.6–6.7. Against §6.8's exclusion list, none of the ten forbidden
elements appear. §5.1 density limits are respected (one title, one primary CTA, one secondary,
three cards, no charts, one small table). The synthetic label is pinned, satisfying §36/§38.
No fixes.

## 11. `docs/product/case-workflow.md` — approved

Single hunk, lines 1–25. The six guided steps map one-to-one to §8 steps 1–6 with the correct
field sets, and step 6 carries the decision, amount, three reasons, three risks, conditions, and
next actions §8 requires. The case shell's six tabs match §9's tab list exactly, and "five
headline metrics" respects §9's cap. The analyst-details paragraph restates D-002's
additive-only resolution and correctly forbids export differences. No fixes.

## 12. `docs/adr/0001-pragmatic-monorepo.md` — approved

Single hunk, lines 1–26. Correct ADR shape (context, decision, consequences, rejected
alternatives). Matches §34's stack and directory suggestion, and explicitly rejects
microservices per §34's "do not use microservices unless proven necessary". Honest negative
consequences. The purity rule stated on line 14 is the rule that
`tests/unit/test_task1_architecture.py` fails to enforce — see R16c.

## 13. `docs/architecture/data-model.md` — approved

Single hunk, lines 1–27. I checked all 23 tables required by §33 and every one is present:
companies, borrower_profiles, source_documents, raw_financial_facts, financial_periods,
normalized_financials, financial_adjustments, debt_instruments, loan_requests, ratio_results,
scorecards, score_components, facility_assessments, scenarios, scenario_assumptions,
scenario_results, covenants, covenant_tests, credit_decisions, credit_memos, audit_logs,
policy_versions, model_versions. The additions (`maintenance_capex_inputs`, `calculation_runs`,
`capacity_constraints`) are justified by methodology §2.7, §12, and §8.5. Line 19 satisfies §33's
universal-metadata requirement (source date, model version, calculation timestamp, confidence,
override indicators) and correctly carries currency and exponent on every monetary column.
Integrity rules match methodology §1.1, §9.2, and §12. No fixes.

Note (not a defect): once methodology R3 lands, `ratio_results` will need the `value_exact`
column. Track it with R3 rather than as a separate finding.

## 14. `docs/implementation-plan.md` — approved-with-required-fixes

Single hunk, lines 1–13. The nine steps map cleanly onto §46 phases 0–11, and line 13's gate
(non-author diff review plus a green `verify`) matches §0.4 and §47. Critically, the engine
(step 3) precedes the frontend (step 5), honouring §46's closing instruction not to reach a
polished frontend before the financial engine is validated.

**R29 (non-blocking).** §46 places the Excel golden model at Phase 3, *before* the credit engine;
this plan places it at step 7, after the API and frontend. The independence intent is preserved
because the formula spec and golden hashes are committed at step 2, but the reordering is a
deliberate deviation from the prompt and should be recorded as a decision-log entry with that
rationale rather than left implicit.

## 15. Supporting files read for consistency (not in the assigned set)

- `pyproject.toml` — noted, not reviewed for disposition. `pythonpath = ["packages/credit_engine"]`
  and `testpaths = ["tests"]` are rootdir-relative and correct; this is what makes the
  CWD-relative path in R16a inconsistent with the rest of the configuration.
  `fail_under = 90` with `branch = true` is a real gate.
- `packages/credit_engine/pyproject.toml` — dependency set (`jsonschema`, `pydantic`, `pyyaml`)
  contains no I/O, web, or float-native library, consistent with ADR 0001. Note that this
  purity is currently enforced by packaging convention only, not by the architecture test.

---

## Summary of dispositions

| File | Disposition |
|---|---|
| `docs/methodology.md` | approved-with-required-fixes |
| `excel/formulas/core.yaml` | approved-with-required-fixes |
| `tests/unit/test_task1_contracts.py` | approved-with-required-fixes |
| `tests/unit/test_task1_invariants.py` | approved-with-required-fixes |
| `tests/unit/test_task1_architecture.py` | **rejected** |
| `docs/collaboration/task-ownership.md` | approved |
| `docs/collaboration/decision-log.md` | approved-with-required-fixes |
| `docs/collaboration/disagreement-log.md` | approved-with-required-fixes |
| `docs/collaboration/review-log.md` | approved-with-required-fixes |
| `docs/collaboration/independence-log.md` | approved-with-required-fixes |
| `docs/product/personas.md` | approved |
| `docs/product/homepage-wireframe.md` | approved |
| `docs/product/case-workflow.md` | approved |
| `docs/adr/0001-pragmatic-monorepo.md` | approved |
| `docs/architecture/data-model.md` | approved |
| `docs/implementation-plan.md` | approved-with-required-fixes |

Task 1 implementation is **not approved**. Blocking items: R1, R2, R3, R6, R15, R16a–d, R28.
