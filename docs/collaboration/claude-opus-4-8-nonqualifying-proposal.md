# Claude Independent Proposal — Corporate Credit Underwriting & Banking Risk Platform

- **Author:** Claude (Claude Code CLI, Opus, medium effort)
- **Date:** 2026-08-03
- **Status:** Independent proposal. Written without reading `codex-independent-proposal.md`. The master prompt file was not readable in this session (permission not granted); this proposal is derived from the task mandate and the collaboration docs (`decision-protocol.md`, `model-configuration.md`).
- **Purpose:** An opinionated, buildable product-and-architecture proposal that a hiring manager in banking/fintech/risk would find credible, and that two agents can actually ship.

---

## 0. Framing: what this project is *for*

This is a **portfolio artifact**, not a bank system of record. That single fact should drive every scope decision, and it is the assumption most likely to get lost. The audience is a reviewer (hiring manager, senior engineer, risk lead) who spends **5–10 minutes** deciding whether the author can (a) model credit risk correctly, (b) build a clean, defensible full-stack application, and (c) exercise judgment about what *not* to build.

Therefore the winning move is **depth in a narrow, correct core**, not breadth. A believable single-name corporate credit underwriting workflow that is financially sound beats a sprawling "risk platform" with ten half-features. The biggest risk to this project is **feature bloat dressed as ambition**.

**Design tenet:** every feature must earn its place by making the *credit decision* more correct or more legible. If a feature does neither, defer it.

---

## 1. Personas

### Primary — **Corporate Credit Analyst ("Underwriter")**
Owns a single obligor's credit assessment: spreads financials, computes ratios, assigns an internal risk rating (PD proxy), sizes/structures a facility, and writes a recommendation for a credit committee. This persona *is* the product's core loop. Everything else is supporting cast.

Why primary: the underwriting workflow is the densest concentration of domain skill I can demonstrate — financial statement spreading, ratio analysis, rating logic, expected loss math, and a decision memo. It is legible to a reviewer in minutes.

### Secondary 1 — **Credit Risk Officer / Approver**
Reviews the analyst's package, applies policy (limits, covenants, delegated authority), approves/declines/conditions. Justifies a **review/approval surface** and a light **audit trail** — cheap to build, and it signals that the author understands separation of duties and controls (a real differentiator for banking roles).

### Secondary 2 — **Portfolio / Risk Manager** *(deferred to a stub)*
Wants aggregate exposure, rating migration, concentration. I list this persona to show I understand the portfolio dimension, but I **explicitly defer** real portfolio analytics to post-MVP. Building portfolio dashboards before the single-name model is correct is the classic bloat trap: charts over substance.

**Rejected as a persona:** *Borrower/relationship-manager self-service intake.* It pulls the project toward CRM/onboarding UX and away from risk modeling — the wrong signal for this portfolio. **Rejected:** *Regulator/auditor* as a first-class persona; audit *trail* yes, audit *persona* no.

---

## 2. Guided vs. Analyst mode — resolve the false binary

A "guided vs. analyst mode" toggle is tempting and mostly a trap: two modes means two UIs to build, test, and keep consistent, for a project whose reviewers are themselves analysts.

**Decision:** Build **one analyst-first workflow** that is *progressively disclosed*, not two modes.
- The underwriting flow is a linear, numbered set of steps (Intake → Spread → Ratios → Rating → Facility/EL → Decision). That linearity *is* the guidance.
- "Guided" affordances are lightweight and inline: contextual help, sensible defaults, inline validation, and a "why this number" explanation on each computed field. No separate mode.
- The only real mode distinction worth keeping is **read-only reviewer view** vs. **editable analyst view** — and that is driven by persona/permission, not a UI toggle.

**Counterexample that would change my mind:** if the primary audience were non-analysts (e.g., a sales demo to SME borrowers), a true guided wizard would win. It isn't, so it doesn't. This is the assumption to challenge with Codex: *who actually clicks through the deployed demo?* If the answer is "recruiters who aren't credit people," a thin guided intro screen (not a full second mode) is the compromise.

---

## 3. MVP scope

The MVP is **one obligor, end to end, correct.**

**In scope (the core loop):**
1. **Obligor & financials intake** — create a company; enter 2–3 years of income statement + balance sheet (+ minimal cash flow) via a structured form. Seed data (2–3 fictional companies across risk tiers) so the demo is instant.
2. **Financial spreading & ratios** — leverage (Debt/EBITDA, D/E), coverage (EBITDA/Interest, DSCR), liquidity (current, quick), profitability (margins, ROA), with common-size and trend. Deterministic, unit-tested, transparent formulas.
3. **Internal risk rating** — a transparent, documented scorecard mapping ratios → ordinal rating (e.g., 1–10 or AAA…D-style bands) → **PD**. Rules-based and explainable, **not** an opaque ML model.
4. **Facility structuring & Expected Loss** — facility amount, EAD, and configurable **LGD**; compute **EL = PD × LGD × EAD** and a simple RAROC-style spread indication. This is the financial payoff that says "I understand credit," and it is small.
5. **Decision memo & workflow** — analyst recommendation → officer review → approve/decline/condition, with status and a timestamped audit trail.

**Explicit deferrals (named, not silently dropped):**
- Portfolio aggregation / migration / concentration dashboards → **stub with a "coming soon" and one static illustrative chart** at most.
- ML/statistical PD estimation, macro overlays, IFRS 9 / CECL lifetime ECL staging → deferred; MVP uses a documented point-in-time scorecard PD.
- Document ingestion / OCR / PDF statement parsing → deferred (manual/structured entry + seeds).
- Multi-tenant auth, SSO, real RBAC hardening → deferred; MVP uses simple role selection sufficient to demonstrate separation of duties.
- Monte Carlo, correlation, stress scenarios beyond one deterministic sensitivity slider → deferred.
- Real-time market data / credit spreads feeds → deferred (out of scope for a static-friendly demo).

**Why these deferrals:** each deferred item is either (a) reviewer-invisible plumbing, or (b) breadth that dilutes the correct core. Naming them *is* the signal of judgment.

---

## 4. Homepage & navigation

**Homepage = a working entry point, not a marketing splash.** A portfolio reviewer should reach a real screen in one click.

- **Landing:** a concise value statement + a **prominent "Open the workbench" / obligor list**. One short paragraph on what it is and the financial model, with a link to the methodology doc. No hero-carousel bloat.
- **Primary object is the Obligor.** Navigation is object-centric:
  - **Obligors** (list → detail) is the home of real work.
  - **Obligor detail** is a **tabbed workspace** following the loop: Overview · Financials · Ratios & Rating · Facility & EL · Decision & Audit.
  - **Review queue** (officer persona) — obligors pending approval.
  - **Methodology** — a page that documents the rating scorecard and EL math (doubles as reviewer credibility).
- Top nav: Obligors · Review Queue · Methodology. That's it. Resist adding a "Portfolio" and "Reports" tab until they contain real content.

**Failure mode to avoid:** a nav bar advertising sections that are empty. Empty tabs read as abandonment. Better three full sections than seven hollow ones.

---

## 5. Architecture

Optimize for **credibility + reviewability + cheap hosting**, in that order.

**Recommended stack:**
- **Frontend:** React + TypeScript (Vite), a small component set (e.g., shadcn/ui or equivalent), a charting lib (Recharts). Type safety is itself a signal.
- **Backend:** one of two paths — pick by the deploy target, decide with Codex:
  - **(A) TypeScript full-stack** (Next.js app-router, API routes/server actions) — single language, single deploy (Vercel), least friction. **My default recommendation** given hosting simplicity and the portfolio context.
  - **(B) Python (FastAPI) API + React SPA** — stronger "quant" signal because the *financial engine in Python* is legible to risk reviewers; costs a second service to deploy.
  - **Tie-breaker:** the decision protocol favors simpler/more reversible. **(A)** wins unless we judge the "Python quant engine" signal is worth the ops cost to the target audience. This is the top item to arbitrate with Codex.
- **Financial engine:** an **isolated, pure, dependency-light module** with no framework imports — pure functions `ratios()`, `rating()`, `expectedLoss()`. This is the crown jewel; it must be independently unit-testable and portable across (A)/(B).
- **Data:** relational (Postgres in prod; SQLite for local/dev). Schema: Obligor, FinancialStatement, RatioSet (derived/cached), RatingResult, Facility, Decision, AuditEvent. Money as integer minor units or `Decimal`/`bigint` — **never floats for currency.**
- **Persistence stance:** a real DB, but **all financial computation lives in the pure engine, never in SQL.** The DB stores inputs and audited outputs; it does not do math.
- **Testing:** the engine has the highest coverage bar (golden tests on seed companies with hand-verified expected values). API/UI get smoke + a couple of workflow integration tests.
- **Deploy:** single hosted demo with seed data; must load and be usable without login for a reviewer (read-only demo obligor), with role switch to try the workflow.

**Explicitly rejected architecture choices:** microservices, message queues, event sourcing, a separate ML service, GraphQL. All are resume-cosplay for this scope and would burn the budget that should go into a correct model. If asked "why not microservices," the answer is: one obligor workflow does not have bounded contexts worth splitting, and reversibility/velocity win.

---

## 6. Financial model principles (non-negotiable)

These are the correctness guardrails; violations are financial-integrity objections under the decision protocol and cannot be silently waived.

1. **Transparency over sophistication.** Every rating and PD is traceable to inputs via documented rules. A reviewer must be able to reconstruct any number by hand. No black boxes in the MVP.
2. **`EL = PD × LGD × EAD`, stated plainly**, with each input sourced and bounded (PD∈[0,1], LGD∈[0,1], EAD≥0). Show the components, not just the product.
3. **Deterministic and pure.** Same inputs → same outputs, no hidden state, no time-dependence except where explicitly modeled and dated.
4. **No floats for money.** Decimal/minor-units throughout; define rounding rules once and test them.
5. **Point-in-time, documented PD.** The scorecard is calibrated to *illustrative* bands and labeled as such — never imply regulatory calibration or real-world backtesting it doesn't have. Honesty about limitations is a credibility asset, not a weakness.
6. **Guard the divide-by-zero and degenerate cases** (zero EBITDA, negative equity, no debt). These are where naive credit models embarrass their authors; handling them well is a differentiator.
7. **Units and periods are explicit** (currency, thousands/millions, fiscal vs. calendar). Ambiguous units are a classic silent error.
8. **Sensitivity, minimally.** One honest lever (e.g., EBITDA haircut or rating downgrade) showing EL response beats a fake Monte Carlo. Show you understand *directional* risk sensitivity.

**Counterexample / failure mode:** the tempting error is to over-model — add correlations, macro factors, lifetime ECL — and ship something impressive-looking but wrong or unverifiable. A reviewer who knows credit will find the crack immediately, and it reads worse than a modest, correct model. **Under-promise the model; over-deliver on its correctness and clarity.**

---

## 7. Likely failure modes (project-level)

1. **Bloat creep** — portfolio dashboards, ML, doc parsing sneak in and the core ships late/thin. *Mitigation:* the deferral list above is a contract; re-adding a deferred item requires a decision record.
2. **Empty-nav syndrome** — nav promises sections with no content. *Mitigation:* a tab ships only when it has real content.
3. **Two-mode tax** — guided vs. analyst doubles the surface. *Mitigation:* one progressively-disclosed workflow.
4. **Financial-correctness cracks** — divide-by-zero, float money, unlabeled units, uncalibrated PD presented as real. *Mitigation:* the §6 guardrails + golden tests.
5. **Un-runnable demo** — reviewer hits a login wall or an empty DB. *Mitigation:* seed data + a public read-only demo obligor; the happy path must work in <10s with zero setup.
6. **Split-brain math** — logic duplicated in UI and backend and drifting. *Mitigation:* single pure engine, imported by both.
7. **Over-engineered infra** — microservices/queues eat the budget. *Mitigation:* §5 rejection list.

---

## 8. Ownership split (Codex ↔ Claude)

Aligned with the decision protocol (independent proposals, cross-review, non-author signs off every hunk).

- **Codex (primary orchestrator / implementation peer):** scaffolding, framework wiring, API/routes, DB schema + migrations, UI components and pages, deploy pipeline, seed data plumbing. Owns velocity and integration.
- **Claude:** the **financial engine spec + implementation review** (ratios, rating scorecard, EL/RAROC), the **methodology doc**, the **golden/unit test design**, and **adversarial review** of financial-integrity, accessibility, and scope. I am the correctness and "is this actually credible to a credit person" check.
- **Shared / arbitrated first:** the (A) vs. (B) stack decision — this gates everything and must be a recorded decision before scaffolding.
- **Protocol:** no financial-engine or schema change lands without the non-author reviewing every diff hunk; §6 objections block until resolved.

---

## 9. First implementation task

**Do the stack decision as a 1-page decision record first** (A vs. B), because it is irreversible-ish and blocks scaffolding.

Then, the first *code*:

> **Build the pure financial engine module + its golden test suite, framework-free, against 2–3 seed companies with hand-verified expected ratios, rating, PD, and EL.**

Rationale: it is (a) the highest-signal, highest-risk part, (b) portable across whichever stack we pick so it is never wasted work, (c) independently testable with no UI/DB, and (d) it forces us to pin down the model *before* building screens around it. Screens built before the model is settled get rebuilt; the engine built first never does. Ship the engine, prove it, then build the workbench around a known-correct core.

**Concrete deliverable:** `engine/` with `ratios.ts|py`, `rating.ts|py`, `expectedLoss.ts|py`, a `seeds/` fixture of 2–3 obligors, and a passing golden-test file whose expected values I have verified by hand and documented in `Methodology`.

---

## 10. One-paragraph counter-position (steelman of the opposite)

The strongest case *against* my "narrow and correct" thesis: a portfolio piece is partly a breadth advertisement, and a lone single-name underwriting form can look small next to a "platform." If the target roles are generalist full-stack rather than risk-specialist, breadth-signaling (more screens, a portfolio view, auth) might score better with non-expert screeners. My rebuttal: breadth without correctness is the *more* common and *more* punished failure, expert screeners are the ones who decide, and a tight correct core with named deferrals demonstrates *both* competence and judgment — which is the rarer, higher signal. But this hinges on **who reviews the demo**, and that is the assumption Codex and I must nail down together before locking scope.

---

*End of independent proposal. Ready for comparison against Codex's proposal per the decision protocol.*
