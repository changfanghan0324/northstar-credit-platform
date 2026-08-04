# Claude Independent Product & Architecture Proposal

**Author:** Claude Opus 5 (`claude-opus-5`), invoked via Claude Code CLI in the Codex workspace
**Date:** 2026-08-03
**Status:** Independent proposal — written before reading `codex-independent-proposal.md`
**Scope:** Persona, MVP scope and deferrals, homepage/navigation, guided vs. analyst mode, architecture, financial model principles, ownership, first implementation task

> This document deliberately disagrees with several defaults in the master prompt. Where I disagree, I say so explicitly and give the counterexample that drove the disagreement. Sections 1, 3, and 4 contain the substantive dissents.

---

## 0. The one-sentence thesis

**The product's only defensible reason to exist is that it shows its work: a transparent chain from filed financials → normalized cash flow → repayment capacity → a named binding constraint → a decision.** Every scope decision below is resolved by asking whether it strengthens or dilutes that chain.

Everything that dilutes it — live XBRL ingestion, a second SME policy engine, ten Power BI pages, AI narrative, a global mode toggle — is deferred, regardless of how reasonable it sounds in isolation.

---

## 1. Personas — I disagree with the prompt's stated direction

### 1.1 The prompt's default, and why I think it's wrong

§3 of the master prompt says "the likely design direction is: default interface optimized for a guided non-expert or junior user." I accept the *interaction* half of that and reject the *persona* half.

**Counterexample that decides it.** Consider the archetypal Persona A user: a founder with $2M revenue asking "can I borrow $500k?" To serve them honestly, this platform would walk them through adjusted EBITDA, maintenance-capex carve-outs, CFADS, DSCR, covenant headroom, and facility protection. But that user cannot supply normalized financials, cannot approve an EBITDA adjustment, and — critically — **does not make the lending decision**. Their real job-to-be-done is "estimate whether I qualify and for how much," which is well served by a six-field affordability calculator and badly served by an underwriting platform.

If the primary persona's actual need is better met by a dramatically simpler product than the one we're building, the persona is wrong. That is the test, and Persona A fails it.

There is a second failure hiding here. Designing *primarily* for a non-expert pushes every hard, credible artifact — the spread, the adjustment ledger, the debt schedule, the reverse-stress solver — into an "advanced" ghetto that then gets deprioritized when time runs short. The parts that make this project worth putting on a résumé are exactly the parts a non-expert-primary design deprioritizes.

### 1.2 Selected personas

| Role | Persona | Why |
|---|---|---|
| **Primary** | **Junior credit / credit-risk analyst (Persona B)** — including the credit-risk graduate or CFA candidate | They perform this exact workflow. They can judge whether CFADS is defined correctly, and they are the population the product's depth is calibrated for. Designing for them forces financial credibility to be a build requirement rather than a polish task. |
| **Secondary 1** | **Recruiter / interviewer (Persona C)** | Determines the project's actual payoff. Needs proof of competence in under 60 seconds without any data entry. Costs little to serve — a pinned demo case and one deep link — but only if designed in from the start. |
| **Secondary 2** | **Finance student / guided newcomer (Persona A, narrowed)** | I keep the *learner* slice of Persona A and drop the small-business-owner slice. A student wants to understand *why* a decision was made; that is served by the same explanation layer the analyst uses, so it is nearly free. A borrower wants to know *if they qualify*; that is a different product. |

**Persona D (portfolio / risk manager) is explicitly not a persona for this build.** It is a second product with a different unit of analysis (the book, not the case). Serving it inside the case workflow is the single largest bloat risk in the prompt. See §2.3.

### 1.3 The critical distinction the prompt conflates

**Persona ≠ information density.** Choosing the analyst as primary does *not* license dense screens. My position:

- **Persona choice** determines *what must exist* → the spread, the adjustment ledger, the binding constraint, the reverse-stress solver.
- **Progressive disclosure** determines *what is visible first* → decision, reason, risk, next action.

So I fully adopt §4 and §5 of the prompt (simple-first, density limits, plain-language-then-jargon) while rejecting §3's persona ranking. The density rules in §5 should be treated as hard constraints and enforced in review, not as aspirations.

---

## 2. MVP scope

### 2.1 The spine — build this, in this order

```
Company + Loan Request
  → Financials (3 FY + LTM, fixture / CSV / manual)
    → Adjustments (explicit, approved, evidenced)
      → Debt schedule
        → Ratios (with "not meaningful" as a first-class state)
          → Obligor score (explainable, component-level)
          → Facility protection score (separate, never improves obligor grade)
            → Debt capacity = min(4 constraints), binding constraint NAMED
              → 3 scenarios × 3 years (base / downside / severe)
                → Covenant tests + headroom
                → Reverse stress (4 solvers)
                  → Decision + conditions
                    → Memo (1-page + detailed), traceable to persisted run outputs
```

This satisfies all 25 items in §48 (MVP acceptance criteria). Nothing below the line in §2.2 is needed to satisfy them.

### 2.2 Explicit deferrals — with the reason each was cut

| Deferred | Prompt ref | Reason | Replacement in MVP |
|---|---|---|---|
| **Live SEC/XBRL ingestion** | §17 | Highest scope-death risk in the project. Tag mapping, restatements, 52/53-week years, and unit scaling can consume 40% of the timeline with zero visible product improvement. | **Curated, version-pinned fixture packs** derived from real filings, with `accession_number`, `filing_date`, `taxonomy`, `tag`, `raw_value`, `unit`, `retrieval_timestamp` all committed. The raw → normalized → adjusted three-layer lineage model is **fully built**; only the *fetcher* is stubbed. A live `SecFilingSource` adapter drops in behind the same interface post-MVP. Every lineage acceptance criterion in §48 remains satisfiable. |
| **Separate SME/private policy engine** | §12 | Two parallel policy engines before one is validated. | One borrower form with an `entity_type` discriminator, plus ~8 SME-only optional fields (owner distributions, key-person, related-party, reporting quality). Policy overrides by entity type are a config key, not a code branch. |
| **Full integrated 3-statement forecast** | §27 | A forecast balance sheet that doesn't tie destroys credibility faster than having no balance sheet forecast. | **Cash-flow and debt roll-forward model**: revenue → EBITDA → cash taxes → working capital → capex → CFADS → interest → principal → ending debt / ending cash / revolver draw. Documented explicitly as a debt-service model, *not* a balancing 3-statement model. Honest and sufficient for every covenant and DSCR test we run. |
| **Power BI workbook (10 pages)** | §36 | A second product. Near-zero incremental portfolio value versus a working stress engine. | **One read-only `/portfolio` page**, four visuals (grade distribution, industry exposure, maturity wall, covenant watchlist), driven by a 40-borrower synthetic JSON fixture labeled synthetic. Plus a written **star-schema specification** in `docs/` so the Power BI work is *designed* even though it isn't *built*. |
| **AI-generated memo narrative** | §11.5 | Removes an entire class of hallucination failure modes at the cost of slightly stiffer prose. | Deterministic template + structured facts. Post-MVP: a "polish wording" action that may only rephrase, never introduce a number. |
| **Authentication / RBAC** | §43 | No portfolio value in a single-tenant demo; adds real security surface. | No auth. Audit log records `actor` from a settings-level analyst identity string. Documented as a deliberate limitation. |
| **Rating migration, Monte Carlo, ML** | §36, §2 | No time series to migrate; probabilities we cannot honestly produce. | Excluded. Migration needs multi-period history the demo doesn't have. |
| **Numeric "confidence %" indicator** | §9, §33 | Fake precision. A "confidence: 87%" with no model behind it is exactly the black box §2 forbids. | **Three-state data-quality badge: Complete / Partial / Blocked**, derived deterministically from the §22 missing-data policy, with the specific missing fields enumerated. |
| **Visual regression testing** | §42 | Low yield at this size; high maintenance. | Component tests + axe accessibility checks + Playwright E2E on the three golden cases. |
| **Rate limiting** | §43 | No auth, no public write path in MVP. | Input validation, size limits, content-type validation on upload retained. |
| **5 historical years** | §15 | 3 FY + LTM is the acceptance-criteria minimum and is enough for volatility measures. | 3 FY + latest quarter + LTM. |

### 2.3 Deliberate MVP simplification worth flagging now

**Recommended loan = min(requested, leverage, DSCR, collateral, policy)** is correct as far as it goes, but there is a counterexample it handles badly:

> A working-capital revolver where leverage capacity is $40M but the borrowing base supports $8M. The right credit answer is not "lend $8M as a term loan" — it is "the facility structure is wrong for this collateral."

MVP behavior: recommend the amount **and raise a structure-mismatch flag** (`purpose ↔ facility_type ↔ repayment_source` alignment check from §26). We do **not** attempt automatic restructuring. This is documented as a limitation rather than papered over.

---

## 3. Homepage and navigation

### 3.1 Navigation — five items, and one of them must earn its place

```
Home | Start Review | Cases | Portfolio | Methodology          [ Help ]
```

I accept §6.1. Two amendments:

1. **`Portfolio` ships only if the synthetic page is real.** If it slips, it comes out of the nav rather than shipping as a stub. A dead nav item is worse than four items.
2. **`Methodology` is a first-class marketing surface, not a docs dump.** For the recruiter persona it is the second-most-visited page. It gets the same design care as the homepage: the scorecard weights, the CFADS definition, the capacity math, and the limitations — each in under a screen, with links to the code.

### 3.2 The homepage problem the prompt doesn't solve

§6.3 says the three outcome cards show results "for a selected demo or recent case." **On a cold install there are no recent cases**, so the recruiter's first impression is three empty cards — the worst possible outcome for the secondary persona that decides the project's payoff.

**My fix: the homepage is always bound to a pinned demo case** (the stable borrower), clearly labeled `Sample case — Meridian Industrial (synthetic)`. Real numbers, always, in under 10 seconds, with zero data entry. If the user has cases of their own, a switcher lets them bind the cards to their most recent one.

### 3.3 Homepage structure

| Band | Content |
|---|---|
| **Hero** | H1: *Should this company receive this loan?* · Sub: one sentence · **Primary CTA: Start a guided credit review** · **Secondary CTA: Open a sample case** |
| **Three outcome cards** | (1) Repayment outlook — `DSCR 1.62x` "Cash flow covers debt payments with a 62% cushion." (2) Recommended loan amount — `$24.0M of $30.0M requested` "Limited by DSCR capacity." (3) Stress resilience — `Holds in downside, breaches in severe` "Leverage covenant breaks in year 2." Each card: plain label → one result → one sentence → *Why?* |
| **Four-step preview** | Add company → Enter loan request → Review stress results → Receive recommendation |
| **Recent cases** | ≤5 rows, 5 columns (company, status, recommendation, updated, open) |
| **Trust band** | Transparent calculations · no black-box approval · details on demand · educational disclaimer |
| **Footer** | Methodology · Limitations · Data sources · Educational disclaimer |

Two changes from §6 worth calling out:

- **The secondary CTA deep-links to the sample case's *decision* page, not the wizard.** Recruiters want the payoff before the process. Making them walk six wizard steps to see the output is the most likely cause of a 20-second bounce.
- **Card 2 names the binding constraint on the homepage.** "Limited by DSCR capacity" is the single most credit-literate sentence in the product, and it belongs where it will actually be read. This is the differentiator versus every other loan-calculator portfolio project, and burying it is a mistake.

All §6.8 exclusions are accepted without exception.

---

## 4. Guided vs. analyst mode — I recommend **no global toggle**

### 4.1 The disagreement

§7 asks for a Guided Mode and an Analyst Mode reachable "through a clear switch." I recommend against a global mode switch in MVP.

**Why.** A global mode flag is a hidden multiplier on the QA surface: every page, every empty state, every error state, and every E2E test now has two variants. It is also a well-documented usability trap — users forget which mode they are in and then report bugs that are mode differences. §7 itself hedges ("the mode switch must not duplicate the whole application"), which is an admission that the mechanism invites exactly the failure it warns about.

### 4.2 What I propose instead

**Density is a property of the route, not of the user.**

| Surface | Always |
|---|---|
| Home, Wizard, Case → Summary, Decision, Memo (1-page) | Plain language. ≤5 headline metrics. Explanation on demand via `WhyDrawer` / `FormulaDrawer`. |
| Case → Financials, Risk, Stress, Terms; Adjustments; Debt schedule; Audit | Analyst-grade by default. Full spread, component tables, thresholds, lineage, overrides. No apology, no "advanced" gate. |

Plus **exactly one persisted preference**: `Show formulas and thresholds inline` (a single boolean in `localStorage`). When on, `FormulaDrawer` content renders expanded in place instead of behind a click. That is the entire "analyst mode" — one boolean, one conditional render path, ~2% of the complexity of a global mode system, and it delivers the actual thing analysts want (stop making me click).

**Reversibility argument (per §0.5):** a route-level design can have a global toggle added later at low cost. A global toggle, once shipped, is very hard to remove because users and tests depend on it. Prefer the reversible option.

**Counterexample against my own position.** An analyst who wants full density on the *Summary* tab. Fair — but the summary's job is the §5.5 hierarchy (decision → reason → risk → next action → evidence), and one click to `Financials` is a low price. If usability testing (§41) shows analysts bouncing off the summary, the single boolean can be extended to control summary density too, without introducing a mode.

**Failure mode I'm accepting:** manual overrides and audit trail have no "advanced mode" to live in. Resolution: they are workflow surfaces, not density surfaces. Overrides live on the Financials and Assumptions tabs as permanent affordances; the audit trail is its own route. This is arguably better than hiding compliance-relevant features behind a preference.

---

## 5. Architecture

### 5.1 Shape

Pragmatic monorepo, no microservices (agreeing with §34), with one structural rule that matters more than all the others:

```
/apps
  /web              Next.js 15 (App Router) + TypeScript
  /api              FastAPI — thin: HTTP, auth-less, persistence, orchestration
/packages
  /credit_engine    PURE PYTHON. No DB. No FastAPI. No I/O. No network.
  /policy           Versioned YAML policy + loader + JSON Schema
  /shared_types     TS types generated from FastAPI OpenAPI
  /ui               Design-system components
/data
  /fixtures         Committed filing snapshots w/ full lineage metadata
  /golden_cases     Canonical inputs + expected outputs
  /synthetic_portfolio
/docs               product / collaboration / adr / methodology
/tests              unit / integration / e2e / golden_cases
/excel
```

### 5.2 The decisions I consider non-negotiable

**1. The credit engine is a pure library.**
`packages/credit_engine` takes Pydantic models in and returns Pydantic models out. No session, no request, no filesystem. This is the highest-leverage decision in the document: it is what makes the engine unit-testable, Excel-reconcilable, deterministic, and independently reviewable line-by-line by whichever agent didn't write it. If the engine ends up importing SQLAlchemy, the project has failed architecturally.

**2. Money is integer minor units.**
`Decimal` at the API boundary, `int` (cents) inside the engine. **No floats for currency, ever.** Ratios are `float`, rounded only at presentation. This single rule eliminates the most common cause of Excel↔Python reconciliation drift.

**3. Results are persisted, never recomputed on read.**
Every engine invocation writes an immutable `calculation_run` row: `engine_version`, `policy_version`, `input_hash`, plus every ratio result, score component, scenario year, covenant test, and capacity constraint. The memo reads *only* from a persisted run.

> **Failure mode this closes:** analyst edits an adjustment after generating a memo; memo now shows numbers that no longer exist anywhere. **Mitigation:** runs are immutable; the case computes `input_hash` on load and, if it differs, shows *"Inputs changed since the last run — re-run required"* and **blocks memo export**. This makes §32's "do not invent facts" a structural property rather than a promise.

**4. Postgres everywhere, including local dev.**
Docker Compose, one command. I reject SQLite-for-dev: JSONB, `NUMERIC` precision, and constraint behavior diverge, and the divergence surfaces at deployment — the worst possible time.

**5. One source of truth for types.**
FastAPI → OpenAPI → generated TypeScript in `packages/shared_types`. Hand-written duplicate interfaces are banned; a CI check fails if generated types are stale.

**6. Frontend state is boring.**
React Server Components for data fetching, URL search params for view state, one form context for the wizard. **No Redux, no Zustand, no client cache library in MVP.** The wizard persists a draft case to the API after each step — losing a half-finished review to a refresh is a real usability failure, and it's cheap to prevent.

**7. Policy is data, not code.**
All thresholds, weights, grade bands, advance rates, and scenario defaults live in `packages/policy/policy.v1.yaml`, validated against a JSON Schema, hashed at load. Changing a threshold bumps `policy_version` and invalidates cached runs. §21's "store thresholds in configuration, not application code" is enforced by making the engine take a `Policy` object as an explicit argument — it has no default and no global.

### 5.3 Deployment

Vercel (web) · Render or Fly.io (api) · Neon or Supabase managed Postgres. Migrations via Alembic, run in a release step, never on app boot.

---

## 6. Financial model principles

These are the commitments I would defend in a credit interview.

1. **CFADS is the spine, not EBITDA.** The decision hinges on DSCR computed from CFADS (adjusted EBITDA − cash taxes − maintenance capex − ΔOWC − mandatory pension/other). A model that leads with EBITDA/interest is the tell of a non-credible credit tool. Maintenance capex must be an explicit, evidenced input — never a hardcoded % of revenue.

2. **Obligor risk and facility risk never mix.** The facility assessment may influence *decision, amount, terms, conditions, and pricing*. It may **never** improve the obligor grade. Enforced as a test invariant: for fixed borrower financials, varying every facility input across its full range leaves `obligor_grade` bit-identical.

3. **"Not meaningful" is a typed value, not a null or a zero.**
   ```python
   RatioResult = { value: float | None, status: 'ok' | 'nm' | 'missing', reason: str, components: dict, threshold: float | None }
   ```
   > **Counterexample driving this:** a company with negative EBITDA but strong contracted receivables. Leverage is genuinely NM — not `0.0x`, not `999x`, not a crash. The decision is carried by DSCR and liquidity runway. Every ratio consumer (UI, memo, Excel export, scorecard) must handle all three states.

4. **Amortizing debt capacity uses present value of an annuity.** Never `annual debt service × years`. Enforced by a unit test that fails the naive formula. This is an easy error and a highly visible one.

5. **Debt capacity is min of four constraints, and the binding one is always named and shown.** Leverage / DSCR / collateral / policy. The binding constraint is the product's single most credit-literate output and it appears on the homepage, the case overview, the decision, and the memo.

6. **Missing critical data blocks the *grade*, not merely the approval.** §22 says block approval; I go further. A grade computed on missing EBITDA or missing debt service is worse than no grade, because downstream consumers will treat it as real. Output is `grade: null, blocked_by: ['annual_debt_service', 'cash_interest']` with a specific corrective action per field.

7. **Deterministic scenarios are never described as probabilities.** No "% chance of breach." No implied likelihood in any label or chart legend. §29's prohibition is enforced by a lint rule over user-facing strings.

8. **Adjustments require evidence, rationale, and explicit approval.** Nothing auto-approves. If total positive EBITDA adjustments exceed a configurable share of reported EBITDA (default 15%), the case is flagged `enhanced review required` and the flag propagates to the decision and memo.

9. **Full traceability by construction.** Every score component persists `input, formula_id, threshold, points, weight, contribution, explanation, source_ref, period, data_quality, override, override_reason`. Every memo sentence containing a number carries a `provenance` pointer to a persisted `ratio_result` or `score_component` row. Memo generation cannot access raw inputs — only run outputs.

10. **Excel is an independent implementation with a stated tolerance.** Reconciliation tolerance is documented, not implied: **±$1 on currency, ±0.005x on ratios, ±0.1 points on scores.** Claiming bit-exact agreement across two floating-point environments is not credible; naming a tolerance is.

11. **Internal grade only.** Internal score → internal grade → *illustrative* external-equivalent range, always labeled educational. No agency logos. No claim of a rating.

12. **Sample cases must disagree with each other.** All three golden cases must produce **different decisions and different binding constraints**:

| Case | Decision | Binding constraint |
|---|---|---|
| Stable borrower | Approve | Requested amount (no constraint binds) |
| Leveraged borrower | Reduce requested amount | Leverage capacity |
| Cyclical borrower | Approve with conditions | DSCR capacity (severe scenario breaches leverage covenant in yr 2) |

> **Failure mode this closes:** if every demo case approves, the product reads as a rubber stamp and the stress engine looks decorative. This is the most common way credit portfolio projects fail to impress credit professionals, and it is entirely preventable at fixture-design time.

---

## 7. Ownership between Codex and Claude

### 7.1 Principle

Split by **module**, not by layer, so that neither agent is the sole author of an end-to-end path. Alternate on the shared spine. Neither agent may be author and final approver of the same code (§0.2).

### 7.2 Proposed matrix

| Module | Author | Reviewer |
|---|---|---|
| Repo scaffold, tooling, CI | Codex | Claude |
| DB schema + Alembic migrations | Codex | Claude |
| FastAPI layer, error contracts, OpenAPI | Codex | Claude |
| Fixture ingestion + validation (§17 checks 1–10) | Codex | Claude |
| Next.js app shell, routing, design system | Codex | Claude |
| Exports (PDF / Excel) | Codex | Claude |
| Deployment | Codex | Claude |
| **credit_engine core** (money, ratios, CFADS, DSCR, coverage) | **Claude** | Codex |
| **Debt capacity + PV annuity math** | **Claude** | Codex |
| **Reverse-stress solver** | **Claude** | Codex |
| **Policy schema + loader** | **Claude** | Codex |
| **Decision engine** | **Claude** | Codex |
| **Memo generator + provenance enforcement** | **Claude** | Codex |
| **Methodology, scoring-policy, limitations docs** | **Claude** | Codex |
| **Accessibility review** | **Claude** | Codex |
| Scorecard | Codex | Claude |
| Stress engine (3 scenarios × 3 yrs) | Claude | Codex |
| Homepage | Codex | Claude |
| Case overview + tabs | Claude | Codex |
| Covenant engine | Codex | Claude |
| Wizard | Codex | Claude |
| Portfolio page + synthetic data | Codex | Claude |

Roughly balanced by both file count and difficulty. Claude owns the financial core and the explanation layer; Codex owns the platform and the shell; the spine alternates.

### 7.3 One review rule I'd add that the prompt doesn't have

§0.4 requires every changed line to be reviewed. In practice, line-by-line reading of financial code by an agent that has already seen the implementation produces confirmation bias, not defect detection. So:

> **For every financial module, the reviewer must write at least one test derived from the specification *before reading the implementation*, and that test must be committed alongside the review.**

This is the only version of dual review that reliably catches a wrong formula, and it produces a durable artifact (an adversarial test) rather than a comment that says "verified."

Complementary rules:
- **UI review** must include a §5 density audit (card count, chart count, column count, headline-metric count) and one keyboard-only pass.
- **API review** must exercise malformed input, missing required fields, and unit/currency mismatch.
- **Data review** must verify lineage round-trip: raw fact → normalized value → ratio → memo sentence.

---

## 8. First implementation task

**Task 1 — `packages/credit_engine`: the deterministic ratio & cash-flow core, plus the policy loader and the first golden case.**
**Author: Claude · Reviewer: Codex**

### Why this first

- **Highest credibility risk.** If CFADS or DSCR is wrong, everything downstream is wrong and no amount of UI polish saves it.
- **Zero dependencies.** No DB, no API, no UI — so it cannot be blocked and it cannot block.
- **Unblocks Excel.** The golden case is the reconciliation target for the workbook.
- **Ideal first dual-review artifact.** Pure functions with published formulas are exactly where independent reproduction (§7.3) works best.
- It directly refuses the §46 warning about jumping to a polished frontend before the engine is validated.

### Deliverables

```
packages/credit_engine/
  types.py       Money, RatioResult (ok|nm|missing), Period, DataQuality
  money.py       integer-cents arithmetic, safe_div, rounding spec
  accounts.py    normalized chart of accounts (§15)
  ratios.py      leverage, coverage, liquidity, cash-flow ratios (§19–20)
  cashflow.py    adjusted EBITDA, FCF, CFADS, annual debt service
  policy.py      Policy model + YAML loader + schema validation + hash
packages/policy/
  policy.v1.yaml            thresholds, weights, grade bands, scenario defaults
  policy.schema.json
data/golden_cases/
  stable_borrower.json      inputs + expected outputs, synthetic, labeled
tests/unit/
  test_money.py  test_ratios.py  test_cashflow.py  test_policy.py
```

### Acceptance criteria

1. All ratios in §19–20 implemented as pure functions taking an explicit `Policy`.
2. `RatioResult` correctly returns `nm` for: negative EBITDA leverage, zero interest coverage, zero-denominator DSCR, zero current liabilities.
3. No float arithmetic on any currency value anywhere in the package.
4. Divide-by-zero is impossible — a single `safe_div` chokepoint, enforced by a lint rule.
5. Invariant tests pass (§42): lower EBITDA never improves leverage or coverage; higher debt never improves leverage; higher rate never improves coverage; higher principal never improves DSCR.
6. `stable_borrower.json` reproduces to the documented tolerance.
7. `credit_engine` imports nothing from `apps/`; enforced by an import-linter contract in CI.
8. Codex has committed ≥1 adversarial test written from the spec before reading the implementation (§7.3).

---

## 9. Consolidated failure-mode register

| # | Failure mode | Likelihood | Mitigation |
|---|---|---|---|
| 1 | **Scope death by XBRL** — weeks lost to tag mapping | High | Fixture packs; live fetch is a post-MVP adapter behind a stable interface |
| 2 | **Forecast balance sheet doesn't tie** | High if attempted | Don't forecast a balance sheet; ship an explicit cash-flow/debt roll-forward and say so |
| 3 | **Excel ↔ Python drift** | High | Integer cents; documented tolerance (±$1 / ±0.005x / ±0.1 pt); golden cases in CI |
| 4 | **Scorecard looks arbitrary to a credit interviewer** | High | Rationale documented per threshold; defaults labeled illustrative; thresholds editable in-app so the model visibly responds; always show the ratio next to the points |
| 5 | **All demo cases approve → product reads as a rubber stamp** | Medium-high | Three cases, three decisions, three *different* binding constraints (§6.12) |
| 6 | **Guided mode becomes a second application** | Medium-high | No global mode toggle; density is route-level; one boolean preference (§4) |
| 7 | **Recruiter bounces before seeing output** | Medium-high | Pinned demo case on homepage; secondary CTA deep-links to the decision page |
| 8 | **Memo drifts from engine after an input edit** | Medium | Immutable runs + `input_hash` staleness check that blocks memo export |
| 9 | **Over-claiming** ("credit rating", "approval") | Medium | Disclaimer in memo body, PDF footer, Excel cover, and API response metadata — not just the site footer |
| 10 | **Collaboration theater** — reviews that verify nothing | Medium | Reviewer writes a spec-derived test before reading the implementation (§7.3) |
| 11 | **Accessibility: color-only risk indicators** | Medium | Status = icon + text label + color, always; axe in CI; manual keyboard pass per UI review |
| 12 | **NM ratios crash the UI or render as `0.0x` / `Infinity`** | Medium | `RatioResult` status is typed and every consumer handles all three states; explicit test fixtures for each |
| 13 | **Portfolio page half-built and shipped as a stub** | Medium | It either ships complete (4 visuals, synthetic fixture) or it comes out of the nav |
| 14 | **Density rules treated as aspirations** | Medium | §5 limits are a review checklist item with counts, and a UI review cannot be approved without them |
| 15 | **Engine grows a DB dependency** | Low-medium | CI import-linter contract fails the build |

---

## 10. Open questions for the debate with Codex

1. **Persona.** If Codex selected Persona A as primary, the decisive test is §1.1: is the primary user better served by a much simpler product? I'll defend the analyst-primary position, but I'd concede if Codex can name a job-to-be-done that a non-expert has *and* that requires this depth.
2. **Mode toggle.** I expect this to be the sharpest disagreement. My case rests on reversibility (§0.5 favors the reversible option) and QA-surface cost.
3. **XBRL.** If Codex wants live ingestion in MVP, I'd want a hard timebox (≤2 days) and a pre-committed fallback to fixtures, rather than an open-ended commitment.
4. **Power BI.** I've cut the workbook to a spec + one page. If Codex disagrees, the question is which acceptance criterion in §48 the workbook satisfies that the spec doesn't. I believe the answer is none.
5. **Excel scope.** 20 tabs (§37) vs. ~12. I'd trim Cover/Instructions/Methodology to two tabs and merge the three scenario tabs into one with a scenario selector — same reconciliation value, less maintenance.

---

## 11. Summary of positions

| Question | Position |
|---|---|
| Primary persona | **Junior credit analyst** — dissenting from §3's suggested default |
| Secondary personas | Recruiter/interviewer; finance student (borrower slice of Persona A dropped) |
| Portfolio/risk persona | Not a persona for this build |
| MVP spine | Company → financials → adjustments → debt → ratios → dual scores → capacity → stress → covenants → reverse stress → decision → memo |
| Biggest cuts | Live XBRL, SME policy engine, Power BI workbook, AI narrative, auth, forecast balance sheet, numeric confidence score |
| Homepage | Pinned demo case so it's never empty; binding constraint named on the homepage; sample CTA deep-links to the decision |
| Guided vs. analyst | **No global toggle.** Route-level density + one `show formulas inline` boolean |
| Architecture | Monorepo; `credit_engine` is a pure, I/O-free Python package; integer cents; immutable persisted runs; Postgres everywhere; policy as versioned data |
| Financial spine | CFADS → DSCR; obligor and facility strictly separate; NM is a typed state; PV-annuity capacity; binding constraint always named |
| Ownership | Claude: financial core + explanation layer. Codex: platform + shell. Spine alternates. Reviewer writes a spec-derived test before reading the code. |
| First task | `packages/credit_engine` ratio/cash-flow core + policy loader + stable-borrower golden case (Claude author, Codex reviewer) |
```
