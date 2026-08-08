# Northstar v5 decision log

Date: 2026-08-08

| Decision | Evidence / invariant | Resolution |
| --- | --- | --- |
| Scale semantics | Stored `MoneyValue.amount_minor` is actual currency minor units | Normalize at browser/import boundary; resolver treats `scale` as metadata only; test whole/millions no double scaling |
| FY/YTD | Flow tuple is FY, current YTD, prior YTD | Compose flows; use current YTD for all point-in-time balances; expose separate lineage |
| Canonical completeness | A failed non-empty spread must not hide behind legacy values | Block decision-critical lines and preserve snapshot hash/issues |
| Debt basis | Balance sheet and instruments can disagree | Typed reconciliation with tolerance and explicit aggregate/partial mode; unexplained material mismatch blocks |
| Adjustments | Itemized approvals are authoritative | Validate evidence/reviewer/amount; carry EBITDA, EBIT, and CFADS impacts; drafts/rejected have no effect |
| Facility | Consumers must not infer structure independently | Resolve one mechanics object; use explicit term/partial/bullet/revolver/ABL fields |
| Exit and ABL | Three forecast years can miss a longer maturity; borrowing base is not commitment | Add maturity exit test; report commitment, drawn, borrowing base, and availability separately |
| Pricing | Floors/spreads were easy to double count | Record one RateDecision and surface it in analysis output |
| Zero exposure and declines | Zero denominators and declined cases can look like active loans | Typed not-applicable protection state; declines contain reasons/prerequisites, no active covenant package |
| Guided UX | Step index is not data completeness | Required-valid-field completion, percentage entry, provenance warning, reset/clear actions, narrow status live region |
| Release claim | Historical audits must not compete with current truth | Add `docs/release-status.md`; older records remain historical and the README links current status first |

Claude Opus 5 High was used as an independent challenger. Its open-risk disposition is preserved in `docs/collaboration/v5-claude-opus-5-review.md`.
