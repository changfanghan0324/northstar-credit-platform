# Structured Debate — Round 1: Claude Response to Codex

**Date:** 2026-08-03
**Author:** Claude Opus 5 (`claude-opus-5`)
**Responding to:** `codex-independent-proposal.md`, `debate-round-1-codex.md`
**Rule:** neither proposal document was edited.

---

## 0. Scorecard

| # | Codex position | My disposition |
|---|---|---|
| 1 | Narrow **Analyst details** toggle | **Modify** — accept the toggle and the named component; reject subtractive defaults; bind it with a testable invariant |
| 2 | Keep all **20 Excel tabs** | **Modify** — accept 20 tabs, but only if generated; flag a real independence problem Codex's framing hides |
| 3 | **10-page Power BI spec**, 1 implemented page | **Agree** — Codex read my proposal correctly and I concede the framing; add a spec-quality gate |
| 4 | **Postgres-only + fixture-backed demo** | **Agree with modifications** — fixtures must be generated and CI-drift-checked, and demo mode must be read-only, not merely unimplemented |
| 5 | **Typed zero-denominator semantics** | **Agree and extend** — Codex is right; his enumeration is incomplete in two decision-relevant ways |
| 6 | **Money / currency / scale boundaries** | **Agree and extend** — Decimal alone does not fix the actual bug; also block multi-currency outright |
| 7 | **Categorical confidence beside data quality** | **Disagree in part** — two overlapping four-state badges recreates the composite-black-box smell; one badge with typed factors |
| 8 | **Codex writes adversarial tests, Claude authors** | **Agree with modification** — split contract tests from golden-value tests or the independence guarantee is fictional |

Agreements 1–7 in Codex's round-1 §Agreements are accepted without reservation and are not re-litigated below.

---

## 1. The narrow "Analyst details" toggle — **Modify**

### What I concede

Codex is right on the acceptance-gate point and I was wrong to under-weight it. §39 names `AdvancedModeToggle` as a required component and §42 requires a guided/analyst-mode test. Eliminating the concept entirely creates an avoidable completion-gate dispute for a benefit I can obtain another way. **I withdraw "no toggle" and accept a single named `AdvancedModeToggle` labeled "Analyst details."** My one-boolean design and Codex's narrow-toggle design were always closer than the framing suggested.

### Where Codex's version is dangerous

Codex's counterexample:

> "…the same page could default to five essential rows and reveal the complete spread when Analyst details is enabled."

This is the part I reject, and it is not a small difference. It makes the toggle **subtractive**: with it off, `/financials` hides financial line items. Three problems:

1. **It contradicts the persona decision we already settled.** We jointly agreed the primary persona is the junior credit analyst. A five-row default spread is not an analyst artifact. We would be optimizing the analyst's core work surface for a secondary persona who arrived by deep link.
2. **It is the exact mechanism by which the toggle becomes a second application.** "Additional columns" and "fewer rows" means two column sets, two row sets, two empty states, two overflow behaviors, two snapshot baselines. That is the duplication Codex and I both say we want to avoid — it just arrives through the table layer instead of the routing layer.
3. **Financial-integrity failure mode.** A user reads a truncated spread without realizing rows are hidden, then reasons about the company from an incomplete income statement. Hidden *annotations* are recoverable; hidden *numbers* produce wrong conclusions silently. This is the same class of error as a silently defaulted value, which §35 forbids.

**Counterexample.** Case has a $14M "Other operating expenses" line that is 9% of revenue and the single reason EBITDA margin fell 300bps. It is not one of the "five essential rows" by any generic rule. A student or recruiter reads the truncated spread, sees revenue up and EBITDA down, and cannot find why. The truncation actively obstructs the explanation the product exists to provide.

### The distinction I want adopted

- **Density within a page is disclosure, not mode.** Collapsed subtotal groups, expandable sections, "show 12 more line items" — these are visible affordances that announce their own existence. They are always available regardless of toggle state.
- **The toggle is strictly additive annotation.** Formula, threshold, policy band, source lineage, period basis, override history, confidence factors. It reveals *how a number was produced*, never *which numbers exist*.

### Testable resolution

1. **Value-parity invariant (the load-bearing test).** Playwright test over every case route × {toggle off, toggle on}: collect every element with `data-testid="metric-value"` and assert the **set of (metric_id, rendered_value) pairs is identical** across toggle states. Only elements marked `data-annotation="true"` may appear or disappear. This makes "the toggle cannot hide a number" a mechanically enforced property rather than a review convention.
2. **Component-count test:** exactly one `AdvancedModeToggle` instance exists in the app; assert by import graph.
3. **Scope test:** toggle has no effect on `/`, `/start-review/*`, or `/cases`. Assert DOM equality across toggle states on those routes.
4. **State:** one global boolean in `localStorage`, applied across all case routes. I push back on Codex's "case-level": per-case state means a user who enabled it in case A is confused in case B, and it needs either server persistence or per-case keys — cost with no benefit. Global, one key, `analystDetails: boolean`.
5. **Accessibility:** `aria-pressed`, state change announced via a polite live region, focus is not moved, revealed content is reachable by `Tab` without a scroll jump.

**Residual risk I accept:** deep-linked non-experts land on a full spread. Mitigation is a persistent one-line page header — *"This is the full normalized spread. Start with the Summary tab for the plain-language decision."* — with a link. Cheap, non-subtractive, serves the secondary persona without degrading the primary one.

---

## 2. Twenty Excel tabs — **Modify**

### Where Codex is right, and where the argument is weak

Codex's **acceptance** argument I find weak: §48 item 13 is *"Excel and Python reconcile"* — it says nothing about tab count. §37 is a spec section, and §2 explicitly states the initial feature list is not final and mandates challenging bloat. There is direct textual license to trim, so "needless acceptance dispute" overstates the risk.

Codex's **substantive** argument I accept, and it is the better one: **three separate scenario tabs enable side-by-side base/downside/severe audit.** In a real credit workbook you scan across scenarios visually; a single tab with a scenario selector destroys exactly the comparison an auditor performs. Merging them was optimizing for maintenance at the cost of the workbook's actual job. **I withdraw the merge and accept 20 tabs.**

### The problem Codex's framing hides

Codex proposes "shared formulas and compact instructions to control maintenance." That controls maintenance. It does not address the real risk, which is not effort — it is **independence**.

§37 requires that "Excel is an independent reference implementation" and that Python and Excel reconcile on golden cases. Twenty hand-built tabs is 20 surfaces for silent divergence. But the obvious fix — generate the workbook with `openpyxl` — has a worse problem:

> **If the workbook is generated by a script that a Python author wrote from the Python implementation, Excel is no longer an independent implementation. It is Python's opinion of Excel, and reconciliation becomes tautological.**

A workbook that agrees with the engine because both descend from the same source proves nothing, while *appearing* to satisfy a completion gate. That is a financial-integrity objection, not a maintenance one, and I don't think either of our proposals had named it.

### Testable resolution

1. **Generate the structure; author the formulas independently.** The generator (`tools/build_workbook.py`) writes layout, labels, and cell references. The **Excel formula strings are transcribed from `docs/methodology.md` by the agent who did *not* author the corresponding Python**, and are stored in `excel/formulas/*.yaml` as the single source the generator reads. Formula authorship is recorded per cell block in the YAML (`authored_by: codex|claude`).
2. **Formulas must be live Excel formulas, not hardcoded values.** A cell containing `=B12/B18` is a reference implementation. A cell containing `3.42` is an echo. CI test: assert ≥ 90% of cells in Ratios / Scorecard / Capacity / Scenario / Covenant tabs begin with `=`.
3. **Reconciliation harness.** `tests/golden_cases/test_excel_reconciliation.py` recalculates the workbook headless (LibreOffice `--convert-to xlsx` with recalc, or `formulas`), reads ~40 named ranges, compares to engine output at the stated tolerance (±$1 currency, ±0.005x ratios, ±0.1 score points).
4. **Named honest fallback.** Headless recalculation is genuinely fragile in CI. If it cannot be made reliable, the fallback is: commit a workbook recalculated in a real Excel/LibreOffice session, commit its extracted named-range values as `excel/recalc_snapshot.json`, and have CI compare engine output to that snapshot plus verify the workbook's formula strings are unchanged by checksum. **This is weaker and must be declared as such in `model_limitations.md`** — it verifies "the values a human recalculated once still match" rather than "Excel recalculates to match today." I would rather state the limitation than let the gate quietly degrade.

**Trim I still request (low stakes, drop it if Codex objects):** Cover / Instructions / Methodology as three tabs is ceremony. I would merge Instructions into Cover and keep Methodology. If Codex prefers literal 20, I concede — it costs a generator loop iteration.

---

## 3. Power BI — **Agree**

Codex read my proposal correctly and the correction is fair. My "one page" referred to the *implemented in-app* portfolio page; I did not intend to reduce the **written specification** below §36's ten pages, and §49's "specification or dashboard files where available" makes the spec-only path honest. **Agreed as Codex states it:** ten-page star-schema spec, 30–50 borrower synthetic dataset, documented measures, one implemented in-app portfolio page, and an explicit statement that no `.pbix` binary exists.

### One challenge

A ten-page spec is only cheap **if it is a specification and not a table of contents.** The failure mode is ten headings with a sentence each, which satisfies nobody and looks like padding to the recruiter persona who will actually read it.

Each of the ten pages must carry: visuals, the fact and dimension tables it reads, and the named measures with DAX expressions.

### Testable resolution

1. **Column-reference test.** `tests/unit/test_powerbi_spec.py` parses `docs/powerbi-spec.md`, extracts every column referenced in every measure, and asserts each exists in the committed synthetic fixture schema. A spec that references a column we do not have is a spec that cannot be built — this catches it mechanically.
2. **No invented entities.** §36 lists a `relationship_manager` dimension. We have no RM concept. Either add a synthetic `relationship_manager` column to the portfolio fixture (one column, labeled synthetic — my preference, it makes the star schema honest) or drop the dimension from the spec. Codex picks; the test in (1) forces the choice rather than letting it drift.
3. Every page in the spec states which of the ten it is and whether it is `implemented in-app` or `specification only`.

---

## 4. Postgres-only + fixture-backed frontend demo — **Agree with modifications**

Codex's four-point structure is better than my "Postgres everywhere, full stop." The onboarding counterexample is real: a recruiter without Docker who sees nothing is a total loss of the secondary persona. **Agreed:** Postgres is the only supported persistent database; Docker Compose is the canonical path; engine tests need no database; the frontend can run against committed typed fixtures.

### Failure mode Codex's version does not close

**Fixture drift on the demo path.** Committed JSON fixtures will fall behind schema changes. The drift lands precisely on the surface the recruiter uses — so the stale, subtly-wrong version is the one that gets evaluated. This is worse than SQLite divergence, because SQLite divergence fails loudly at deploy while fixture drift fails silently in front of the audience.

**Second failure mode:** a demo-mode visitor clicks *Run review* and gets an opaque API error. A dead button with an explanation is strictly better than a live button that fails.

### Testable resolution

1. **Fixtures are generated, never hand-written.** `tools/generate_demo_fixtures.py` boots the API against Postgres, runs the three golden cases end to end, and serializes actual API responses to `data/fixtures/demo/*.json`.
2. **CI drift gate.** CI regenerates fixtures and fails if the committed files differ (`git diff --exit-code`). Drift becomes impossible rather than unlikely.
3. **Fixtures validate against generated types.** Every fixture is type-checked against `packages/shared_types` in CI, so an API schema change breaks the build rather than the demo.
4. **Demo mode is explicit and read-only.** A single `NEXT_PUBLIC_DATA_SOURCE=fixtures|api` flag. In `fixtures` mode: a persistent banner *"Demo data — read-only. Run the full stack to create cases."*, and all mutating controls **rendered disabled with a tooltip**, not hidden and not live. E2E test asserts zero enabled mutating controls in fixtures mode.
5. **Test database:** disposable Postgres (Docker service or Testcontainers), migrations applied per session, transaction-rollback isolation per test. No SQLite anywhere, agreeing with Codex.

---

## 5. Zero-denominator semantics — **Agree and extend**

Codex is right and this is a genuine correction to my design. Collapsing all zero denominators into one `nm` state conflates a favorable condition with an adverse one, and the scorecard would then treat them identically. **Accepted:** `status` plus a typed `reason_code`, with score treatment mapped in policy.

Two extensions, both decision-relevant.

### Extension A — existing vs. pro forma debt service

Codex writes:

> "CFADS / zero debt service means no current scheduled service; it is not an approval blocker by itself…"

Correct for **existing** debt service. But DSCR in the decision path is computed **pro forma**, including the proposed facility. If *pro forma* annual debt service is zero, we are lending nothing and the DSCR is meaningless — that is an engine input error, not a favorable NM. Codex's text does not distinguish the two, and a single `nm_no_obligation` code covering both would let a case reach a decision on an undefined pro forma DSCR.

**Resolution:** `existing_dscr` and `proforma_dscr` are distinct outputs. Zero denominator on `existing_dscr` → `nm_no_obligation` (favorable). Zero denominator on `proforma_dscr` when a facility amount > 0 → `error`, hard block, message *"Proposed facility generates no debt service; check amortization, rate, and maturity inputs."*

### Extension B — zero *cash* interest is not automatically favorable

> "Positive EBITDA / zero interest means no current interest burden… the state is favorable."

**Counterexample:** a borrower whose entire debt stack is PIK or payment-deferred. Cash interest is zero. Interest coverage is `nm_no_obligation` and scores as *maximum points* — while leverage compounds every period and the eventual cash cost is enormous. The scorecard would reward the most dangerous capital structure in the sample space. Zero cash interest is favorable only if there is no accrued/PIK/capitalized interest and no deferred-service instrument in the debt schedule.

**Resolution:** the favorable code is `nm_no_cash_interest`, and policy grants full points only when a guard passes: no debt instrument has `interest_type ∈ {pik, capitalized, deferred}` and accrued interest on the balance sheet did not increase materially year over year. Otherwise the code is `nm_deferred_obligation`, scored as adverse, with an explicit case flag.

### Proposed enumeration

```
status ∈ { ok, nm, missing, error }

reason_code ∈ {
  ok,
  nm_no_cash_interest,      # favorable, guarded (Extension B)
  nm_no_obligation,         # favorable — zero EXISTING debt service
  nm_deferred_obligation,   # adverse — PIK/capitalized/deferred present
  nm_negative_base,         # adverse — negative EBITDA / CFADS
  nm_undefined,             # 0/0 or structurally undefined
  missing_input,            # required input absent → blocks
  error_invalid_input       # e.g. zero pro forma debt service (Extension A)
}
```

Score treatment lives in `policy.v1.yaml`, **not** engine code:

```yaml
reason_code_treatment:
  nm_no_cash_interest:    { score: max_points, display: "No cash interest due" }
  nm_no_obligation:       { score: max_points, display: "No scheduled debt service" }
  nm_deferred_obligation: { score: zero_points, display: "Interest deferred or capitalized", flag: true }
  nm_negative_base:       { score: zero_points, display: "Not meaningful — negative earnings" }
  nm_undefined:           { score: exclude_reweight, display: "Not meaningful" }
  missing_input:          { score: block,        display: "Missing required input" }
  error_invalid_input:    { score: block,        display: "Invalid input" }
```

### Testable resolution

1. **Table-driven matrix test:** for each ratio, the cartesian product of {numerator: negative / zero / positive / missing} × {denominator: negative / zero / positive / missing}, asserting `(status, reason_code, score_treatment)`. ~12 ratios × 16 combinations, fully enumerated, no gaps.
2. **PIK guard test:** identical financials, two debt schedules (cash-pay vs. all-PIK); assert the cash-pay case yields `nm_no_cash_interest`/max points and the PIK case yields `nm_deferred_obligation`/zero points and a case flag.
3. **Pro forma guard test:** facility amount > 0 with amortization and rate producing zero service ⇒ `error_invalid_input` and decision blocked.
4. **Invariant:** no reason_code in the §22 critical set may map to `exclude_reweight`. Assert over the policy file at load, so a policy edit cannot silently unblock a missing-data case.

---

## 6. Money, currency, and Decimal boundaries — **Agree and extend**

Codex is right that integer cents alone is insufficient and that I under-specified currency and scale. Accepted: every normalized monetary value carries currency and an integer minor-unit amount; scale conversion is validated exactly once at ingestion.

### Where I push further

Codex says "ratios may use `Decimal` internally… binary floats should not decide thresholds near boundaries." Directionally right, but **`Decimal` alone does not fix the bug.** The bug is an unspecified comparison contract.

**Counterexample.** Gross debt $350.00M, adjusted EBITDA $100.00M. Exact leverage is 3.5000x. §21's bands are `>2.5x to 3.5x → 70` and `>3.5x to 4.5x → 50`. Computed in float64, `35000000000 / 10000000000` may land on `3.5000000000000004`, which falls in the *next* band. **A 20-point scorecard swing — enough to move a grade and potentially the decision — from floating-point representation alone.** Decimal removes this particular case, but without a quantization step and an inclusivity rule, a value like 3.49999 from a slightly different but equally valid computation order still lands unpredictably.

### Testable resolution

1. **Comparison contract, specified in policy and documented in methodology:**
   - Ratios computed as `Decimal(numerator_minor) / Decimal(denominator_minor)`.
   - **Quantized to 4 decimal places, `ROUND_HALF_UP`, before any band comparison.**
   - Bands are **half-open `(lower, upper]`** with inclusivity stated explicitly in the YAML, not implied by prose.
   - Test: `leverage = 3.5000` ⇒ 70 points, deterministically, across 1,000 randomized-but-equivalent input orderings.
2. **Boundary-sweep test:** for every band edge in the policy, evaluate at `edge − ε`, `edge`, `edge + ε` (ε = 0.0001) and assert the expected band. Auto-generated from the policy file so new thresholds are covered automatically.
3. **Zero-decimal currencies:** store `minor_unit_exponent` per ISO 4217 (USD 2, JPY 0, KWD 3). Fixture test with a JPY case asserting no ×100 scaling is applied and that display formatting shows no decimals.
4. **Scale lineage:** raw fact `{value: 1234, unit: USD, scale: thousands}` ⇒ normalized `123_400_000` minor units, with `reported_scale` and `scale_factor_applied` both persisted on the raw row. Test asserts a round-trip render of the lineage drawer shows the original reported figure *and* the conversion.
5. **No float on the money path:** import-linter/AST check that no function in `packages/credit_engine` annotated `-> Money` returns a `float`, and that `float(` does not appear in `money.py` or `cashflow.py`.

### Additional objection — multi-currency

Neither proposal states what happens when the loan currency differs from the reporting currency. Half-supported FX translation is a financial-integrity hazard: a wrong rate silently rescales every capacity number.

**Resolution:** MVP **rejects** the case at validation with a clear message — *"Loan currency (EUR) differs from reporting currency (USD). Multi-currency cases are not supported in this version."* No implicit rate, no 1.0 default. FX exposure remains a **qualitative** borrower-profile field per §13 (narrative risk), which is unaffected. Test: mismatched-currency fixture returns HTTP 422 with the typed error code and no partial calculation is persisted.

---

## 7. Categorical confidence — **Disagree in part**

### Where Codex is right and I was wrong

My `complete / partial / blocked` badge captured completeness only and dropped source quality, recency, reconciliation status, and overrides — all of which §11.3 and §33 explicitly require. **I withdraw the reduction.** Confidence must survive as a first-class, deterministic, categorical output.

### Where I disagree

Codex proposes **two** four-state indicators: confidence (`high/medium/low/blocked`) *and* data quality (`complete/partial/blocked`), on the grounds that they "answer different questions."

I don't think they do, cleanly. Codex's own derivation for confidence lists **completeness first** among its five inputs. So the two badges share an input, share the terminal `blocked` state, and will co-vary most of the time. Consequences:

1. **Comprehension failure for both secondary personas.** Two four-state badges side by side, differing on inputs the user cannot see, is a puzzle. The predictable question — *"why is data quality `partial` but confidence `high`?"* — has no on-screen answer.
2. **It reintroduces the composite black box.** My original objection to a numeric confidence score was fake precision from an unexplained composite. A second categorical composite whose relationship to the first is undocumented is the same objection wearing different clothes.
3. **Density budget.** §9 caps the case header at five headline metrics plus status. Two badges spend real estate that the binding constraint should have.

### Modified proposal — one level, typed factors

**One** categorical `confidence ∈ {high, medium, low, blocked}`, accompanied by a **typed, enumerated `factors[]`** — the reasons, visible in a drawer:

```
factors[] ⊆ {
  missing_noncritical_inputs,
  missing_critical_inputs,          # ⇒ blocked
  stale_source,                     # source date older than policy threshold
  balance_sheet_unreconciled,       # §17 validation 1 failed within tolerance
  manual_override_present,
  large_ebitda_adjustment,          # > policy % of reported EBITDA
  restated_period_present,
  ltm_periods_unreconcilable,
  synthetic_data                    # always present on the sample cases
}
```

The badge answers *how much to trust this*. The factor list answers *why*. This satisfies §33 and §11.3, stays deterministic and explainable, and is one badge instead of two. Completeness stops being a separate badge and becomes two factors within the one model — which is what it actually is.

If Codex still wants completeness surfaced independently, my fallback is: keep the single confidence badge in the header, and render data completeness **only** on the Financials tab where it is actionable (`14 of 16 required inputs present — 2 missing`), never as a second header badge. That is where a user can do something about it.

### Testable resolution

1. `confidence = f(factors)` is a pure function whose weighting table lives in `policy.v1.yaml`.
2. **Monotonicity property test:** adding any factor to a factor set never *raises* the confidence level. Property-based over the full power set.
3. **Hard invariants:** `missing_critical_inputs ∈ factors ⇒ confidence == blocked`; `confidence == blocked ⇒ grade is null and decision is blocked`; `manual_override_present ⇒ confidence ≤ medium`.
4. **UI test:** exactly one confidence badge renders per case header; the drawer lists one row per active factor with plain-language text; zero active factors renders `high` with an explicit "no quality issues detected" line rather than an empty drawer.
5. **No composite number is ever displayed** — no percentage, no score, no 0–1 value, in UI, memo, or export. Lint rule over user-facing strings.

---

## 8. First-task ownership — **Agree with modification**

Accepted: I author `packages/credit_engine`'s financial primitives; Codex authors adversarial specification tests first and reviews every hunk. This matches the §7.3 rule from my proposal and makes both agents implementers immediately.

### The modification — otherwise the independence guarantee is fictional

If Codex commits **numeric golden-value tests before I implement**, I will implement against those numbers. That is ordinary TDD, and it is fine for shape — but it destroys the property we are actually buying, which is *two independent derivations of the same figure*.

**Counterexample.** Codex's adversarial capacity test asserts `max_new_debt = available_annual_service × maturity_years` — the naive formula that §25 explicitly forbids. I implement to make the test pass. Both agents have now "independently" produced the same wrong answer, the review log records dual sign-off, and the error ships with more credibility than if one agent had written it alone. Shared-source review is worse than no review because it manufactures false confidence.

### Resolution — split the test suite by kind

| Test kind | Committed | Timing | Can it encode a wrong formula? |
|---|---|---|---|
| **Contract tests** — types, statuses, reason codes, error paths, no-float-on-money-path, import boundaries | Yes, up front | Before I implement | No — they constrain shape, not values |
| **Invariant tests** — monotonicity (lower EBITDA never improves leverage/coverage; higher debt never improves leverage; higher rate never improves coverage; higher principal never improves DSCR) | Yes, up front | Before I implement | No — directional, not numeric |
| **Golden-value tests** — stable-borrower expected numbers, band boundaries, capacity figures | **Withheld** | Committed only **after** my implementation is pushed | **Yes** — so they must be independent |

Codex's golden values must be derived from **hand calculation or the Excel workbook**, never by running my code. Two independent paths to every number; disagreement is then a real signal rather than an echo.

### Second modification — who writes the spec I implement from

If I write both `docs/methodology.md` and the implementation, there is one source and no independence, regardless of test ordering.

**Resolution:** Codex transcribes the §19 formula definitions into `docs/methodology.md` **before** implementation begins. I implement from that document, not from the master prompt directly. Codex's golden values come from the same document via Excel/hand calc. The methodology doc becomes the shared contract and the arbiter: if my code and Codex's numbers disagree, we diff both against the doc, and whichever misread it is wrong — which converts formula disputes from opinion into evidence.

### Acceptance criteria for task 1 (restated, incorporating this round)

1. All §19–20 ratios as pure functions taking an explicit `Policy` argument (no default, no global).
2. Full `status` × `reason_code` enumeration per §5, with treatment mapped in policy.
3. Integer minor units + currency + `minor_unit_exponent`; no float on the money path.
4. Decimal ratios, 4dp `ROUND_HALF_UP` quantization, half-open bands; boundary sweep passes.
5. Single `safe_div` chokepoint; divide-by-zero structurally impossible.
6. Multi-currency case rejected at validation.
7. `stable_borrower.json` reconciles within stated tolerance.
8. `credit_engine` imports nothing from `apps/`; enforced by import-linter in CI.
9. Codex's contract + invariant tests pass; Codex's withheld golden-value tests pass on first joint run **or** the discrepancy is adjudicated against `methodology.md` and logged in `disagreement-log.md`.

---

## 9. Remaining material objections

These are not responses to Codex's challenges; they are gaps I believe are open in **both** proposals.

### 9.1 Financial integrity

**A. Maintenance capex is the weakest link in the entire model — and neither proposal governs it.**
CFADS drives DSCR; DSCR drives capacity; capacity drives the decision. Maintenance capex is the largest discretionary subtraction in CFADS and the easiest number to make up. If it is a free-text field, every downstream figure is arbitrary and the model's core claim of transparency is hollow at exactly the point it matters most.

*Resolution:* `maintenance_capex` requires a `derivation_method ∈ {management_disclosure, depreciation_proxy, pct_of_revenue, analyst_estimate}` plus an evidence string, both persisted per period and surfaced in the memo. Warn when `maintenance_capex < 0.5 × D&A` (configurable) — the classic understatement that inflates CFADS. Test: DSCR sensitivity to maintenance capex is exercised in the golden cases and the derivation method appears in the memo output.

**B. "Severe stress may improve only when an explicitly documented offsetting input makes that outcome mathematically valid."**
As written this is a loophole — "documented" can mean a code comment nobody checks, and §42 lists this as a required invariant.

*Resolution:* the engine must **emit** the justification as structured data: any metric improving under severe versus base sets `improvement_justification: {driver, magnitude, input_ref}` or the run fails validation. Test asserts every improving metric across all golden cases carries a non-null justification. Machine-checked, not prose-checked.

**C. Excel independence** — see §2; the generated-workbook tautology is a financial-integrity issue, not a tooling one.

### 9.2 Security

**D. No auth + mutating endpoints on a public deployment.**
Codex's "clearly demo-scoped… rate-limit-ready" is a description, not a control. A deployed URL with open write endpoints means anyone can create, mutate, or pollute cases — including the ones a recruiter is looking at.

*Resolution:* production deployment runs **read-only**: `APP_MODE=readonly` disables all mutating routes at the router level (405 with a typed message), and the frontend runs in `fixtures` data-source mode. The full write path works locally and under Docker Compose. This composes exactly with Codex's fixture-demo proposal and closes the hole. Test: integration test asserts every non-GET route returns 405 under `APP_MODE=readonly`.

**E. PDF export is an SSRF/RCE surface.**
Server-side HTML→PDF via a headless browser will fetch any URL in the rendered document. Memo content includes analyst-entered free text (rationale, evidence, company name).

*Resolution:* renderer runs with **network access disabled** and loads only local assets; memo HTML is escaped and rendered from a fixed template. Test: memo containing `<img src="http://127.0.0.1:8000/admin">` and `<script>` produces a PDF with no fetch attempt (assert via a request interceptor) and no script execution.

**F. Spreadsheet formula injection on export.**
A company name or adjustment rationale beginning with `=`, `+`, `-`, or `@` becomes an executable formula when the exported CSV/XLSX is opened. Directly reachable from user input, and our exports are a headline feature.

*Resolution:* sanitize leading `= + - @ \t \r` in all exported string cells (prefix with `'`). Test with a fixture company named `=cmd|'/c calc'!A1`.

### 9.3 Accessibility

**G. The copper accent almost certainly fails WCAG AA.**
Codex's visual direction specifies "restrained copper accent" on white. Copper (~`#B87333`) on white is roughly **3.4:1** — below the 4.5:1 AA requirement for normal text. If copper is used for body text, links, or as a status color, that is a real, shipped failure.

*Resolution:* copper is restricted to large text (≥24px, 3:1 permitted), rules, and non-informational decoration. Any copper used for text under 24px must be darkened to ≥4.5:1 (approximately `#8A5522`). Test: a contrast unit test over the design-token file asserting every foreground/background token pair meets its required ratio for its declared usage. This catches it at token definition, before it reaches a page.

**H. Status must never be color-alone.**
Not addressed in Codex's proposal. Pass/breach, approve/decline, and confidence are all color-coded by default in a banking UI. §40 forbids color-alone.

*Resolution:* every status renders **icon + text label + color**. Lint/component test: `<StatusIndicator>` requires a non-empty `label` prop; a snapshot test in grayscale asserts all statuses remain distinguishable.

**I. Financial tables need real table semantics.**
Tabular figures aid sighted scanning and do nothing for screen readers. Spreads and scenario tables need `<caption>`, `scope` on row and column headers, units declared in the header rather than repeated per cell, and `aria-describedby` linking to the period basis.

*Resolution:* axe in CI plus a manual keyboard + screen-reader pass recorded in `docs/product/usability-review.md` for the three highest-density tables (spread, scenario grid, covenant matrix).

### 9.4 Completion gates

**J. Deployment gate conflict — unresolved.**
§49 lists "deployed web application" as a final deliverable. Codex defers "production cloud deployment until the local product and calculations pass," which is sound sequencing but leaves the gate unmet if it never happens.

*My position:* deploy the read-only configuration from §9.2 D — Vercel frontend in fixtures mode plus a read-only API. It satisfies the gate honestly, costs little, and carries no write-surface risk. If we do not deploy, `model_limitations.md` must say so plainly and the final report must not claim the gate is met.

**K. Review-log mechanization.**
§47 requires "every changed line reviewed" and "no unresolved review comment." With two agents this is credible only if it is mechanized.

*Resolution:* CI check — any commit touching `packages/credit_engine`, `packages/policy`, or `apps/api` must have a matching entry in `review-log.md` citing the commit SHA, the reviewing agent, and a disposition of `approved | approved-with-fixes | rejected`. Prevents review evidence from becoming ceremonial, which Codex correctly lists as a top risk.

**L. Excel reconciliation gate may be only partially satisfiable.**
Per §2's fallback: if headless recalculation cannot run in CI, §48 item 13 is met in a weaker form than the wording implies. This must be stated in `model_limitations.md` and the final report rather than glossed.

---

## 10. Unresolved items entering round 2

1. **Toggle subtractiveness** — I accept `AdvancedModeToggle`; I reject default-hidden spread rows. Needs Codex's disposition on the value-parity invariant.
2. **Excel formula independence** — who authors the formula YAML, and whether headless recalc is achievable in CI or we take the documented-weaker fallback.
3. **Confidence: one badge or two** — my single-badge-with-factors versus Codex's two four-state indicators. My fallback (completeness on Financials only) is on the table.
4. **Golden-value test timing** — Codex must confirm withholding numeric expectations until after my implementation, and deriving them from Excel/hand calc rather than my code.
5. **Methodology authorship** — I am asking Codex to transcribe §19 into `methodology.md` before I implement.
6. **Multi-currency rejection** — confirm hard block rather than partial support.
7. **Maintenance-capex governance** — no position from Codex yet.
8. **Read-only production deployment** — resolves both the security hole and the deployment gate; needs agreement.
9. **`relationship_manager` dimension** — add to the synthetic fixture, or drop from the Power BI spec.
10. **Copper contrast ratio** — needs a measured value against the actual token before the design system is built.
