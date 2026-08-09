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
- **v6-02 — Financial lineage and FY/YTD consistency:** production-verified in
  Vercel deployment `dpl_8yQdunYTeqp8Gzd66Zs8863BgKW9` (READY; production
  alias verified). Commit: `v6-02-fix-financial-lineage`. Claude Opus 5 High
  remediation challenge `9be6e487-9218-424f-a06c-bf811760802c` (PASS).
- **v6-03 — Debt reconciliation and residual treatment:** production-verified
  in Vercel deployment `dpl_8C8MTsWeV9N5fwnjCjTbT4L9SYAw` (READY; production
  alias verified). The exact phase commit is recorded in the release commit
  metadata. Claude Opus 5 High re-challenge `2ee7d0c4-9a06-4350-96af-b067dacd736a`
  (PASS pending final green gate; gate passed below).
- **v6-04 through v6-08:** pending; no completion claim is made for those
  phases.

## Verification at release authoring

- v6-02 verification: 113 Python tests passed; total coverage 92.83%.
- v6-03 verification: 122 Python tests passed; total coverage 92.87%.
  The gate added reconciliation, tolerance, partial residual, conservative
  aggregate/partial stress, currency, and bilingual memo/PDF tests.
- Ruff, strict Mypy, TypeScript, ESLint, and Next.js production build passed;
  unrelated generated `.next/* 2.ts` duplicates were temporarily excluded and
  restored without deleting user files.
- Playwright: 11 passed, 1 intentional mobile skip. Production smoke: English
  and Traditional Chinese routes, `/health`, `/runtime`, and `/demo-cases`
  returned 200; all three demo opens matched expected outcomes and amounts;
  six detailed PDFs returned 200; Vercel runtime errors in the last hour: none.
- v6-03 production smoke: `/`, `/zh-TW/`, `/health`, `/runtime`, and
  `/demo-cases` returned 200; all three demo outcomes and recommended amounts
  matched the catalog; six bilingual detailed PDFs returned 200 and exceeded
  1 KB; a transient rate limit on one retry cleared and the final check passed;
  Vercel runtime errors in the last hour: none.
- Earlier v5 production evidence remains in the historical audit documents;
  it does not override the phase-specific v6 record above.

## Current limitations

Synthetic inputs only. No live bank, bureau, ratings, market quotes, regulated credit decision, lending commitment, production identity, or durable multi-tenant data service. Optional debt schedules explicitly use aggregate mode. The interface is bank-style/committee-format educational work, not “committee-ready.”

## Navigation

- [Methodology](methodology.md)
- [v5 post-fix audit](audits/v5-post-fix-audit.md)
- [v5 pre-fix audit](audits/v5-pre-fix-audit.md)
- [v5 decision log](collaboration/v5-decision-log.md)
- [v5 Claude challenge](collaboration/v5-claude-opus-5-review.md)
