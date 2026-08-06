# Disagreement Log

## D-001 — Primary persona

- Positions: prompt suggested a guided non-expert direction; both independent proposals selected a junior credit analyst as primary.
- Evidence: a borrower self-service user is better served by a much smaller affordability product and cannot perform or approve the required underwriting work.
- Resolution: junior credit analyst primary; recruiter/interviewer and finance student secondary.
- Status: resolved.

## D-002 — Guided and analyst modes

- Codex initial position: a narrow mode can reduce visible detail.
- Claude initial position: no global mode toggle; route-level density only.
- Failure mode: subtractive mode can hide financially material rows and creates two effective applications.
- Resolution: one global `Analyst details` toggle is additive only. It reveals formulas, thresholds, lineage, overrides, and confidence factors; it never changes metric identifiers or values. Disclosure groups are independent controls.
- Status: resolved with automated value-parity and export-parity tests.

## D-003 — Excel scope and independence

- Claude initial position: reduce or merge some of the 20 named sheets.
- Codex position: keep all 20 for side-by-side scenario audit and unambiguous delivery.
- Resolution: keep all 20 because separate Base, Downside, and Severe sheets support side-by-side audit of the same line items. Codex authors independent formula specifications before viewing Claude's engine diff; hashes are committed before review. Workbook formulas remain live and reconcile through headless recalculation where reliable.
- Status: resolved.

## D-004 — Confidence representation

- Codex initial position: confidence badge plus separate data-quality badge.
- Claude challenge: overlapping composite badges create a new black box.
- Resolution: one deterministic categorical confidence badge plus typed factors. Completeness appears as an actionable count on Financials/import only.
- Status: resolved.

## D-005 — Ratio zero-denominator semantics

- Claude initial position: one `nm` state.
- Codex challenge: favorable no-obligation, adverse negative base, deferred obligations, missing inputs, and invalid pro forma service require distinct treatment.
- Resolution: `status` plus typed `reason_code`; policy-owned scoring; existing/pro forma DSCR split; PIK guard.
- Status: resolved.

## D-006 — Review anti-tamper timing

- Risk: deriving or silently amending goldens after reading the implementation can contaminate independent verification.
- Resolution: commit-and-reveal hashes prove the expected-value and Excel-formula artifacts existed before Codex opened Claude's engine diff. Published inputs remain inferable; the control prevents unlogged post-hoc edits rather than preventing inference. Amendments require a logged explanation against methodology.
- Status: resolved.

## D-008 — Lease treatment and capacity basis

- Claude review found that operating rent could be deducted in both EBITDA/CFADS and debt service, and that "existing pro forma debt" did not name a debt measure.
- Resolution: DSCR includes only obligations not already deducted in CFADS; operating rent belongs in fixed-charge coverage with an EBITDAR add-back. The golden leverage capacity uses existing gross debt excluding the proposed facility.
- Evidence: `methodology-signoff.md` F1–F2; amended golden/formula hashes in `independence-log.md`.
- Status: resolved pending re-review.

## D-007 — Public writes without authentication

- Risk: an unauthenticated deployed API can be polluted.
- Resolution: public deployment is fixture-backed and read-only; routes are denied by explicit allowlist rather than HTTP method alone. Full writes are local-only.
- Status: resolved.

## D-009 — Zero capacity and non-applicable collateral

- Claude position: a zero capacity result cannot be referred for discretionary
  approval, and collateral must not enter the minimum when the facility is unsecured.
- Codex response: accepted. Every capacity row now carries applicability and typed
  status; zero supported exposure precedes grade and referral logic and returns
  `Decline`.
- Status: resolved; regression tests added.

## D-010 — Production database availability

- Product requirement: durable anonymous PostgreSQL persistence with seven-day TTL.
- Observed external state: the connected Supabase account contains no projects.
- Resolution: implement the complete schema/migration and runtime contract, deploy in
  explicitly labeled temporary-session mode, and require user authorization before
  creating a potentially billable database project.
- Status: operationally constrained, not misrepresented as complete persistence.
