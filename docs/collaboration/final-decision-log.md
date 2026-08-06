# Final-cycle decision log

This log is append-only for the final corrective cycle. A proposal is not a final decision until the independent Claude review and Codex response are recorded.

## D-000 — Baseline and scope gate

- Timestamp: `2026-08-06T16:11:27Z`
- Question: Can the previous completion records be reused as proof that the new specification is complete?
- Codex proposal: No. Preserve the working MVP but treat every newly requested acceptance criterion as unverified until independently tested.
- Claude recommendation: Agree; correct the new audit before implementation and do not reuse old completion evidence.
- Codex response: Accepted.
- Final decision: Every new criterion requires fresh evidence. Previous functionality is a regression baseline only.
- Files affected: `docs/audits/final-product-audit.md`, `docs/audits/final-model-audit.md`, `docs/audits/final-ux-audit.md`
- Evidence: current main/production/test/browser baseline recorded in the audit files.

## D-001 — Product mode

- Question: Portfolio Demo Mode A or Durable User Product Mode B?
- Codex proposal: Mode A. It is honest, already implemented, suitable for the portfolio, and avoids an incomplete security posture masquerading as a durable product.
- Claude recommendation: Mode A, conditional on honest runtime disclosure, schema documentation, and non-decorative operational controls.
- Codex response: Accepted. Fleet-wide quotas require shared storage; the application must state whether enforcement is shared or best-effort.
- Final decision: **Mode A — Portfolio Demo.** Synthetic data only, anonymous temporary sessions, no confidential information, no claim of regulated or durable underwriting.

## D-002 — Compatibility and data model

- Question: Rewrite the product or extend the existing case contract?
- Codex proposal: Extend in place with versioned, typed, backward-compatible defaults and migrations. Preserve current demos and workflows while adding structured periods, adjustments, evidence, facility, collateral, pricing, and solver results.
- Claude recommendation: Extend in place, but first reconcile ORM runtime tables, unused migration stubs, and architecture documentation; implement real history or stop calling a counter versioning.
- Codex response: Accepted. For Mode A, the case remains a JSON aggregate, while immutable case-version snapshots and audit reads become real runtime capabilities. Periods and other professional structures are typed within the aggregate and versioned by the case snapshot.
- Final decision: No rewrite. Reconcile schema ownership and migrations; preserve backward compatibility; add real immutable versions/audit reads.

## D-003 — Implementation sequence

- Question: What order minimizes model and UX regression risk?
- Codex proposal: contracts/policy → deterministic engines/tests → persistence/APIs → exact money transport → component split/UI → memo/localization/accessibility → complete verification/deploy.
- Claude recommendation: P0 correctness/reviewability → P1 schema/localization/testing foundations → P2 new credit capabilities, each with a gate.
- Codex response: Accepted. Full requested scope remains the target; no unmet criterion will be relabeled complete.
- Final decision: Adopt the gated sequence recorded in `final-review-claude-opus-5.md`.

## D-004 — Money correctness and transport

- Question: What is the first money-safety change?
- Claude recommendation: Fix empty-to-zero and uncaught parser errors first; current policy cap lowers immediate JS overflow risk.
- Codex response: Agreed on order. Exact decimal-string transport is still required before expanded spreading inputs.
- Final decision: P0 typed parser/missing state; P1/P2 canonical decimal-string API transport with compatibility conversion at the Python money boundary.

## D-005 — Facility protection information architecture

- Question: Separate page or Decision & Terms subsection?
- Claude recommendation: Avoid overlapping questions; either use an anchored subsection or sharply split ownership.
- Codex response: A dedicated page is required by the specification and is useful for lender-protection analysis.
- Final decision: Dedicated Facility Protection page answers protection quality; Decision & Terms owns the proposed instrument and consumes protection/pricing outputs.
