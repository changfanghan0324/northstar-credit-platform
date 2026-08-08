# Northstar current release status

Status: **Portfolio Demo Mode release — v6 hardening in progress**

This is the single current release truth. Historical audits and debate logs remain in the repository for traceability but do not override this page.

The [Northstar v6 — Final Credit Model Consistency](prompts/Northstar_v6_Final_Credit_Model_Consistency_Prompt.md)
specification is being executed as eight independently tested and committed
phases. v6-01 is production-verified; the product is not v6-complete until
v6-02 through v6-08 are finished.

## Release coordinates

- v5 baseline release commit: `ea797c1b6d59934a1f7b8b8e6405c1aeac2aeae6`
- Production URL: https://northstar-credit-platform.vercel.app
- Vercel deployment: `dpl_HG6b9t5t4aJRxsPEzrgJcc6dtQ2k` (READY; production alias verified)
- Product mode: Portfolio Demo Mode (synthetic, anonymous, temporary seven-day cases)

## v6 phase progress

- **v6-01 — Money scale contract:** production-verified in Vercel deployment
  `dpl_4R2hw9cS9QrzuEu5SuM4Tn6th5vq` (READY; production alias verified).
  The exact Git commit is `v6-01-fix-money-scale-contract`.
- Claude Opus 5 High initial challenge:
  `606598e7-85f1-4dbe-9add-33b244ee57ac` (resolved before deploy).
- Claude Opus 5 High re-challenge:
  `728dc361-bd7d-4459-b287-00894cb99a96` (PASS; no v6-01 production gate).
- **v6-02 through v6-08:** pending; no completion claim is made for those phases.

## Verification at release authoring

- 110 Python tests passed; total coverage 92.43%.
- Ruff, strict Mypy, TypeScript, ESLint, and Next.js production build passed.
- English and Traditional Chinese routes, API health/runtime endpoints, demo-case lifecycle, and English/Traditional Chinese PDF generation are release smoke checks.
- Claude Code recorded an actual `claude-opus-5` High-effort independent challenge (`78e19b11-a37b-4c55-81bd-2aa2e9b908a5`); disposition is open-risk challenge, not external approval.
- Final re-review (`6597c696-e6e3-499c-999a-1dc4e67395b8`) is fit to demonstrate within Portfolio Demo Mode, not fit to decide; residual debt and ABL availability artifacts are now exposed and covered by regression tests.
- Final production smoke: English/Traditional Chinese home routes, `/health`, `/runtime`, and `/demo-cases` returned 200; all three demo opens returned 200 with distinct outcomes; detailed PDF returned 200 in English (10,907 bytes, 5 pages) and Traditional Chinese (86,492 bytes, 4 pages); Vercel runtime error clusters: none in the last hour.

## Current limitations

Synthetic inputs only. No live bank, bureau, ratings, market quotes, regulated credit decision, lending commitment, production identity, or durable multi-tenant data service. Optional debt schedules explicitly use aggregate mode. The interface is bank-style/committee-format educational work, not “committee-ready.”

## Navigation

- [Methodology](methodology.md)
- [v5 post-fix audit](audits/v5-post-fix-audit.md)
- [v5 pre-fix audit](audits/v5-pre-fix-audit.md)
- [v5 decision log](collaboration/v5-decision-log.md)
- [v5 Claude challenge](collaboration/v5-claude-opus-5-review.md)
