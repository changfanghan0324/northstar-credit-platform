# Northstar current release status

Status: **Portfolio Demo Mode release — verified for synthetic educational use**

This is the single current release truth. Historical audits and debate logs remain in the repository for traceability but do not override this page.

## Release coordinates

- Release commit: finalized in the release commit after this document is updated
- Production URL: https://northstar-credit-platform.vercel.app
- Deployment: production alias verified after the final application build
- Product mode: Portfolio Demo Mode (synthetic, anonymous, temporary seven-day cases)

## Verification at release authoring

- 110 Python tests passed; total coverage 92.43%.
- Ruff, strict Mypy, TypeScript, ESLint, and Next.js production build passed.
- English and Traditional Chinese routes, API health/runtime endpoints, demo-case lifecycle, and English/Traditional Chinese PDF generation are release smoke checks.
- Claude Code recorded an actual `claude-opus-5` High-effort independent challenge (`78e19b11-a37b-4c55-81bd-2aa2e9b908a5`); disposition is open-risk challenge, not external approval.
- Final re-review (`6597c696-e6e3-499c-999a-1dc4e67395b8`) is fit to demonstrate within Portfolio Demo Mode, not fit to decide; residual debt and ABL availability artifacts are now exposed and covered by regression tests.

## Current limitations

Synthetic inputs only. No live bank, bureau, ratings, market quotes, regulated credit decision, lending commitment, production identity, or durable multi-tenant data service. Optional debt schedules explicitly use aggregate mode. The interface is bank-style/committee-format educational work, not “committee-ready.”

## Navigation

- [Methodology](methodology.md)
- [v5 post-fix audit](audits/v5-post-fix-audit.md)
- [v5 pre-fix audit](audits/v5-pre-fix-audit.md)
- [v5 decision log](collaboration/v5-decision-log.md)
- [v5 Claude challenge](collaboration/v5-claude-opus-5-review.md)
