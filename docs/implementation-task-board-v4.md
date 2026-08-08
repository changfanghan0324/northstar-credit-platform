# Northstar v4 implementation task board

Status: active  
Owner: Codex  
Independent challenger: Claude Opus 5 High

| ID | Workstream | Status | Acceptance evidence |
| --- | --- | --- | --- |
| V4-01 | Phase 0 baseline and gap matrix | completed | `final-independent-audit-v4.md`; 98-test baseline |
| V4-02 | Canonical underwriting financial snapshot | completed | `resolve_underwriting_financials`; shared snapshot; blocked no-fallback test |
| V4-03 | Real LTM derivation and period validation | completed | FY/YTD, cumulative-flow, scale, contiguity, reconciliation tests |
| V4-04 | Facility mechanics and underwritten rate | in progress | Explicit term/bullet/partial/revolver mechanics; pricing-rate gate; schedule-wide sizing and formal rate object remain |
| V4-05 | Facility protection, adjustments, qualitative risk, borrowing base | in progress | Requested/approved coverage, cross-field validators, qualitative and collateral tests |
| V4-05a | Post-challenge P0 hardening | in progress | Positive-source guard, snapshot hash/freeze, blocked capacity state, amended precedence, cross-method divergence |
| V4-06 | Guided provenance and accessibility polish | pending | Playwright, axe, localization |
| V4-07 | Independent Claude challenge and non-author diff review | completed | `v4-claude-opus-5-review.md`; session `e8cdd3c7-1ca4-419a-8c8f-b074f60b183a` |
| V4-08 | Production deploy and smoke verification | pending | READY deployment, public API/PDF/browser checks |
