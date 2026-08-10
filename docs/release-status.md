# Northstar current release status

Status: **Portfolio Demo Mode release — v6.0.0 formally frozen**

Freeze date: 2026-08-09
Release tag: `v6.0.0`
Freeze policy: no feature, model, policy, or public-claim changes are included
after this tag without a new release review.

This is the single current release truth. Historical audits and debate logs remain in the repository for traceability but do not override this page.

The [Northstar v6 — Final Credit Model Consistency](prompts/Northstar_v6_Final_Credit_Model_Consistency_Prompt.md)
specification is being executed as eight independently tested and committed
phases. v6-01 through v6-08 are independently tested, reviewed, committed, and
production-verified.

## Release coordinates

- v5 baseline release commit: `ea797c1b6d59934a1f7b8b8e6405c1aeac2aeae6`
- Production URL: https://northstar-credit-platform.vercel.app
- Vercel deployment: `dpl_4scrQ5hLioEdH7GqLywNPNrn3xf7` (READY; production alias verified)
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
  (PASS; final gate passed).
- **v6-04 — Unified facility mechanics:** production-verified in Vercel
  deployment `dpl_BjbFua5rfC4wvhBaZ4X1JC4SGqYd` (READY; production alias
  verified). Phase commit is `v6-04-unify-facility-mechanics`. Claude Opus 5
  High re-challenge `06d9fdb8-2128-42fc-bb10-37bd96160182` (PASS; gate passed
  below).
- **v6-05 — Bullet exit and maturity tests:** production-verified in Vercel
  deployment `dpl_3dDHFQgysjjeMehpo2XpLZmf4XxE` (READY; production aliases
  verified). Phase commit is `v6-05-add-bullet-exit-tests`. Claude Opus 5
  High challenge `ddd0fb7f-cfbc-4d58-84ea-45c575b880a0` (PASS; no blocking
  findings).
- **v6-06 — Revolver and ABL mechanics:** production verification is recorded
  below; phase commit is `v6-06-add-revolver-abl-model`. Claude Opus 5 High
  challenge `e1424c55-8110-449d-bae6-0b76e6983ce1` (PASS; no blocking
  findings).
- **v6-07 — Provenance and evidence-based completion:** production-verified in
  Vercel deployment `dpl_AadQpGe2ZVipaPo9Jjva84znAakA` (READY; production
  alias verified). Phase commit is `v6-07-add-provenance-and-completion`.
  Claude Opus 5 High initial challenge
  `821d7747-de3d-4591-9f12-522f635a91d1` was remediated; re-challenge
  `941f9c2e-e94a-4df7-9f03-48a307b23de1` passed with no blocking findings.
- **v6-08 — Final independent audit:** complete under the stated Portfolio Demo
  Mode boundary. Phase commit is `v6-08-final-audit`; Claude Opus 5 High final
  challenge `bfd2d614-e755-463a-ae44-ec251857ecef` passed with no blocking
  findings. The production verification remains anchored to READY deployment
  `dpl_AadQpGe2ZVipaPo9Jjva84znAakA` because v6-08 changes are documentation and
  audit records only.

## Formal freeze checklist

- Eight phase commits are present on `main` and preserved as separate history.
- `v6.0.0` is the immutable release tag for the audited repository state.
- GitHub Release notes identify the exact model, test, Claude review, and
  production evidence.
- The public production alias is READY and remains in Portfolio Demo Mode.
- Unrelated local user files remain untracked and were not included in the release.

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
- v6-04 verification: 126 Python tests passed; total coverage 92.94%; strict
  Mypy, Ruff, TypeScript, ESLint, and Next production build passed; API
  integration and Playwright both passed (11 passed, 1 intentional mobile
  skip). Production smoke after `dpl_BjbFua5rfC4wvhBaZ4X1JC4SGqYd`: English
  and Traditional Chinese routes, `/health`, `/runtime`, and `/demo-cases`
  returned 200; all three demo decisions, recommended amounts, and resolved
  mechanics matched their catalog outputs; six bilingual detailed PDFs
  returned 200 and exceeded 1 KB; browser UI showed the resolved mechanics
  lineage panel; Vercel runtime errors in the last hour: none.
- v6-05 verification: 128 Python tests passed; total coverage 93.03%; strict
  Mypy, Ruff, TypeScript, ESLint, and Next production build passed; Playwright
  passed 11 tests with 1 intentional mobile skip. Production smoke covered
  English and Traditional Chinese routes, `/health`, `/runtime`, and
  `/demo-cases`, all three demo outcomes and mechanics, six detailed bilingual
  PDFs, and a clean Vercel runtime-error check. The five-year bullet maturity
  fields and severe no-refinancing outcome are covered by local unit and API
  integration tests.
- v6-06 verification: 130 Python tests passed; total coverage 93.13%; strict
  Mypy, Ruff, TypeScript, ESLint, and Next production build passed; Playwright
  passed 11 tests with 1 intentional mobile skip. Production smoke covered
  English and Traditional Chinese routes, `/health`, `/runtime`, and
  `/demo-cases`, all three demo outcomes and mechanics, six detailed bilingual
  PDFs, and a clean Vercel runtime-error check. The revolver/ABL contract is
  covered by unit tests and bilingual API/PDF integration evidence.
- v6-07 verification: 133 Python tests passed; total coverage 93.30%; strict
  Mypy, Ruff, TypeScript, ESLint, and Next production build passed. Playwright
  passed 13 tests with 1 intentional mobile skip. Production smoke after
  `dpl_AadQpGe2ZVipaPo9Jjva84znAakA`: English and Traditional Chinese routes,
  `/health`, `/runtime`, and `/demo-cases` returned 200; three demo opens
  returned typed provenance/completion; five detailed PDF requests returned 200
  and exceeded 1 KB, while the sixth correctly returned the configured
  five-per-hour rate limit; a production validation case returned 95.00%
  inherited data, acknowledgement required, and `analysis_ready=false`.
  Browser production review showed provenance/completion, source counts,
  acknowledgement, and no application error. Vercel runtime errors in the last
  hour: none.
- v6-08 verification: the final audit reran the complete v6-07 gate unchanged:
  133 Python tests passed at 93.30% coverage; strict Mypy, Ruff, formatting,
  TypeScript, ESLint, Next build, and Playwright 13 passed with one intentional
  mobile skip. Documentation diff checks passed. Production remained READY at
  `dpl_AadQpGe2ZVipaPo9Jjva84znAakA`; public bilingual routes, API/demo health,
  provenance/completion validation, detailed PDF evidence, browser Review UI,
  and Vercel runtime-error checks remained green.
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
