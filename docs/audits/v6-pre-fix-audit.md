# Northstar v6 pre-fix audit

Date: 2026-08-08
Scope: baseline review before the eight independently committed v6 hardening phases.
Product boundary: Portfolio Demo Mode, synthetic data only.

## Findings carried into v6

The v6 prompt and the phase evidence identified model-consistency risks rather
than a need for a visual rewrite:

| Priority | Risk | Required invariant |
| --- | --- | --- |
| P0 | Display scale could be normalized twice | `MoneyValue.amount_minor` is canonical and normalized exactly once |
| P0 | FY/YTD flows and point-in-time balances could share a generic last-period rule | FY + current YTD − prior YTD for flows; current YTD ending balance for balances |
| P0 | Legacy and instrument debt could diverge | One debt reconciliation and selected source for every decision output |
| P0 | Itemized adjustments could coexist with legacy aggregate fields | Approved `NormalizationAdjustmentInput[]` is the sole adjustment authority |
| P0 | Facility consumers could infer different mechanics | One resolved facility-mechanics object is passed unchanged downstream |
| P0 | Three-year tables could hide a five-year bullet balloon | Contractual maturity, refinancing, and severe no-refinancing tests |
| P0 | Revolver/ABL commitment and availability could be conflated | Separate commitment, drawn, borrowing base, availability, fee, and interest |
| P1 | Template inheritance and wizard progress could overstate readiness | Typed provenance and evidence-based completion |

## Audit method

The baseline was converted into executable contracts, then each phase added a
failing regression test before its implementation was accepted. Every phase had a
separate Claude Opus 5 High challenge, local verification, production smoke, and
commit. Claude reviews were supplied-summary challenges; they were not represented
as source-code inspection. Initial failures and remediation are recorded in
[`v6-claude-opus-5-review.md`](../collaboration/v6-claude-opus-5-review.md).

## Boundary retained

Northstar remains an educational underwriting portfolio demonstration. It does not
claim live data, regulated credit authority, a lending commitment, a market quote,
real-user authentication, or durable multi-tenant storage.
