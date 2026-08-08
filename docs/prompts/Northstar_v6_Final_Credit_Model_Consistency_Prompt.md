# Northstar v6 — Final Credit Model Consistency Prompt

> **This is not a feature expansion prompt. This is a final model-consistency and underwriting-integrity hardening pass.**

Repository: `changfanghan0324/northstar-credit-platform`  
Production: <https://northstar-credit-platform.vercel.app/>  
Product mode: **Portfolio Demo Mode**

## Mission

Continue from the existing Northstar application. Do not rewrite the product, redesign it from scratch, add authentication, or turn it into a banking SaaS. Preserve the current navy/copper visual language, routes, bilingual English/Traditional Chinese experience, case lifecycle, audit/version history, accessibility work, stress pages, PDF generation, and synthetic-data boundary.

This pass is specifically about making every displayed credit conclusion trace to one authoritative normalized calculation path.

Priority order:

1. Financial correctness
2. One-source consistency
3. Facility-structure correctness
4. Decision semantics
5. Beginner usability
6. Portfolio presentation

Do not begin decorative work until the P0 invariants and regression tests pass.

## Product boundary

Northstar remains a synthetic-data, educational corporate-credit underwriting portfolio application. Preserve and disclose:

- anonymous HttpOnly session;
- synthetic data only;
- temporary storage with a seven-day maximum retention;
- best-effort per-instance limits;
- no real bank commitment, official rating, live market quote, regulated-credit use, or lending advice.

Do not add real-user authentication or confidential-data claims.

## Required collaboration protocol

For every material model or architecture decision:

1. Codex reproduces the issue and writes the proposed correction and invariant.
2. A real Claude Opus 5 High session independently challenges the proposal.
3. Codex answers every objection and records the resolution.
4. Add a failing regression test before or together with the correction.
5. A non-author reviewer checks the changed diff.
6. Record the actual model identifier, session ID, date, finding, resolution, files, and test evidence.

Do not fabricate Claude participation or describe a text-only review as source-code inspection.

Maintain these records:

- `docs/audits/v6-pre-fix-audit.md`
- `docs/audits/v6-post-fix-audit.md`
- `docs/collaboration/v6-claude-opus-5-review.md`
- `docs/collaboration/v6-decision-log.md`
- `docs/release-status.md` as the single current release truth.

## P0-1 — Canonical financial scale contract

`MoneyValue.amount_minor` always means the actual exact monetary amount in minor units. `FinancialPeriod.scale` is display/import metadata only.

Normalize `whole`, `thousands`, and `millions` exactly once at the browser/import boundary. The API, stored payload, resolver, analysis, memo, and PDF must not normalize the same value a second time.

Required invariants:

- `100.00` at whole scale resolves to `$100.00`;
- `100.00` at thousands resolves to `$100,000.00`;
- `100.00` at millions resolves to `$100,000,000.00`;
- edit → save → reload → resolve → analyze → redisplay is lossless;
- switching display scale cannot change the underlying actual amount;
- direct entry and CSV/Excel paste produce identical normalized payloads;
- unsafe-integer validation occurs after normalization;
- the millions case can never become `$100 trillion`.

Add an explicit API-contract statement and end-to-end regression coverage.

## P0-2 — FY + current YTD − prior YTD

For `Latest Fiscal Year + Current YTD − Prior Comparable YTD`:

- flow lines use `FY + current YTD − prior YTD`;
- point-in-time balance-sheet lines use the **current YTD ending balance sheet only**;
- `selected[-1]` is forbidden as a generic source rule for the `(FY, current YTD, prior YTD)` tuple.

The immutable snapshot must separately expose flow-source periods and the balance-sheet source period. Revenue, EBITDA, CFO, cash, debt, assets, liabilities, equity, leverage, liquidity, capacity, stress, memo, UI, and API must all consume the same snapshot.

Test materially different current/prior YTD cash, debt, assets, liabilities, equity, AR, inventory, and current liabilities.

## P0-3 — Complete canonical snapshot and source authority

When a non-empty multi-period spread is supplied, decision-critical fields may not silently inherit stale legacy values.

Every decision-critical field must record one authority:

- `period_spread`
- `debt_schedule`
- `facility_request`
- `manual_legacy_snapshot`
- `calculated`
- `defaulted`
- `blocked`

At minimum cover revenue, EBIT, EBITDA, D&A, CFO, cash taxes, maintenance capex, working-capital use, cash interest, scheduled principal, cash, current assets, current liabilities, short-term debt, current maturities, long-term debt, leases, total assets, total liabilities, and equity.

If a higher-quality source such as a reconciled debt schedule supplies a field, use it explicitly. Otherwise block the affected metric where possible; never quietly use old values. Analyst Mode shows the source beside every headline metric. Guided Mode shows a concise source-quality state.

Use metric states `valid`, `warning`, `blocked`, and `not_applicable`. Prove that changing only a canonical debt/liquidity field changes the affected leverage, liquidity, and capacity output.

## P0-4 — One debt reconciliation layer

Create one typed `DebtReconciliation` object containing:

- balance-sheet gross debt;
- instrument gross debt;
- scheduled principal;
- implied interest;
- reported interest;
- difference and tolerance;
- status and explanation;
- selected leverage, stress, and maturity sources;
- aggregate/partial-mode state and any unscheduled residual debt.

All leverage, DSCR, capacity, stress, maturity, memo, and PDF outputs must use the same declared debt basis. A material unexplained mismatch blocks affected decision outputs. Aggregate mode is explicit, not inferred from a zero or missing value. Partial schedules must label the residual treatment on every affected coverage output.

Test reconciled, immaterial-difference, material-mismatch, aggregate, and partial-residual cases.

## P0-5 — Itemized adjustment authority

When `NormalizationAdjustmentInput[]` exists, approved itemized entries are the only authoritative adjustment source. Legacy aggregate positive/negative EBITDA fields must not continue to influence score, confidence, policy checks, leverage, DSCR, CFADS, EBIT, EBITDA, capacity, stress, decision, memo, or PDF.

Draft, pending, and rejected entries have no financial effect. Validate amount, direction, magnitude, recurrence, cash/noncash classification, evidence, source, rationale, reviewer, and approval state. Add per-item lineage and regression tests proving legacy aggregates cannot bypass policy limits when itemized entries are present.

## P0-6 — One resolved facility-mechanics object

Create one `ResolvedFacilityMechanics` object and pass it to every downstream consumer. It must explicitly resolve:

- term loan;
- fully amortizing, partial, and bullet repayment;
- revolver;
- asset-based revolver.

Capacity, pricing, stress, maturity, facility protection, decision, memo, and PDF may not independently infer whether a facility is amortizing, bullet, or revolving. Contradictions must block or be resolved visibly. Demo templates must declare their mechanics explicitly.

## P0-7 — Bullet exit and maturity test

Any bullet or partial-balloon facility must be tested through contractual maturity, even when maturity exceeds the three-year forecast.

Expose and test:

- balloon repayment;
- exit EBITDA and exit leverage;
- refinance capacity and policy headroom;
- severe no-refinancing case;
- maturity date/year and residual debt.

A three-year stress table must not imply that a five-year bullet repays safely merely because the balloon falls outside the displayed forecast.

## P0-8 — Revolver and ABL mechanics

Keep these values distinct and visible:

```text
commitment
drawn amount
borrowing base
availability
commitment fee
cash interest
```

For a revolver/ABL:

```text
availability = min(commitment, borrowing base) − drawn amount
```

Borrowing-base eligibility must separately show AR, inventory, other-collateral haircuts, reserves, prior liens, and deductions. Undrawn commitment must not become headline liquidity beyond borrowing-base availability. Test utilization monotonicity, fee mechanics, commitment limits, and ABL availability after draws.

## P0-9 — One formal rate decision

Create one `RateDecision` used by pricing, capacity, interest, DSCR, stress, and memo:

```text
underwritten index = max(index, floor)
underwritten rate = underwritten index + spread
```

Apply a shock to the index only. Apply spread once. Reconcile commitment fees and upfront fees separately. Block or clearly label pricing, capacity, and decision outputs when the rate decision is unavailable. Test floor/index/spread/shock monotonicity and equality between displayed and modeled underwritten rates.

## P0-10 — Validation and zero-exposure protections

Reject or block:

- negative requested amount;
- negative initial draw;
- negative principal or scheduled amortization;
- scheduled amortization above principal;
- inconsistent amortization type and facility type;
- invalid maturity/availability periods;
- invalid bullet percentage;
- invalid revolver/ABL cross-fields;
- currency or scale contract violations.

Zero supported exposure must produce a typed `not_applicable_no_supported_exposure` facility state. Do not use `max(1)` denominators, infinite coverage, or a stronger protection category for a zero-exposure decline.

## P0-11 — Outcome-specific decision semantics

For `Decline`, show reasons, policy failures, reconsideration prerequisites, and required improvements. Do not show active-loan covenant monitoring, collateral reporting, or conditions precedent as if a loan were approved.

An unsecured facility cannot claim collateral as a secondary repayment source. Test approve, conditional approval, reduce, refer, and decline outputs separately.

## P1-1 — Template provenance

Every material value must be classifiable as:

- `template-derived`
- `user-entered`
- `calculated`
- `imported`
- `override`

The Review page must show counts and percentages, for example:

> 82% of this case is still inherited from the selected template.

Warn when the borrower name changes while most template facts remain unchanged. Provide “Clear template values” and “Reset to template.” Require acknowledgment before generating a memo from mostly unchanged template data. Provenance must travel into analysis/memo metadata where feasible.

## P1-2 — Evidence-based completion

Completion is not `current_step / seven` and reaching Review is not 100%.

Show:

- required fields completed;
- required fields missing;
- evidence completed;
- warnings;
- optional sections completed;
- analysis-ready state.

The same normalized inputs must yield identical values in Guided and Analyst Mode. Guided Mode uses natural percentage inputs, plain-language labels, examples, units, “where to find this” help, collapsed advanced sections, and inline validation. Use a narrow `aria-live` status region rather than re-announcing the whole form.

## P1-3 — Methodology, release story, and public claims

Update methodology to match behavior, grouped into:

1. Data and spreading
2. Borrower risk
3. Facility and capacity
4. Stress and decision
5. Governance and limitations

Use “bank-style” or “committee-format” unless the factual and governance requirements for a stronger claim are genuinely present. README must link primarily to the live product, architecture, methodology, current limitations, current release status, test evidence, and demo cases. Historical audits remain traceability records and must not contradict `docs/release-status.md`.

## Required test matrix

Add or retain unit, invariant, integration, Playwright, accessibility, bilingual, and PDF coverage for:

- scale round-trip and unsafe integers;
- FY/YTD flows and current-YTD balances;
- canonical source authority and legacy-inheritance blocking;
- debt reconciliation and residual treatment;
- adjustment authority and policy magnitude;
- facility mechanics, bullet exit, revolver fees, and ABL availability;
- rate-floor/spread/shock consistency;
- invalid negative/cross-field inputs;
- zero-exposure state;
- outcome-specific decisions;
- three differentiated demos;
- template provenance and evidence completion;
- English/Traditional Chinese UI and PDF output;
- mobile navigation, narrow live region, and serious/critical axe violations;
- production health, runtime, demo lifecycle, PDF, and runtime-error smoke.

## Definition of done

Do not call this v6 pass complete until:

1. Every monetary value is normalized exactly once.
2. FY/YTD balances use current YTD and carry separate lineage.
3. Every decision-critical field has an explicit authority or is blocked.
4. Debt reconciliation, residual treatment, and ABL availability are visible and tested.
5. Itemized adjustments are the sole adjustment authority when present.
6. One facility-mechanics object and one rate decision drive all downstream consumers.
7. Bullet maturity and severe no-refinancing outcomes are explicit.
8. Zero exposure is typed not applicable, never disguised by denominator guards.
9. Decline semantics do not present an active loan.
10. Template provenance and evidence-based completion are visible before memo generation.
11. Methodology, README, release status, and public claims agree.
12. Real Claude Opus 5 High review evidence and a non-author diff review are recorded.
13. Production is verified against the exact release commit, with accepted limitations stated honestly.

## Final delivery report

Report:

1. Production URL
2. Exact release commit SHA
3. Vercel deployment ID
4. Actual Claude model identifier, session ID, and disposition
5. P0/P1 issues fixed and accepted limitations
6. Files created/modified
7. Invariants and regression tests added
8. Test count and coverage
9. Three demo outcomes
10. English/Traditional Chinese and PDF verification
11. Production runtime-error verification
12. Explicit statement that the product remains Portfolio Demo Mode
