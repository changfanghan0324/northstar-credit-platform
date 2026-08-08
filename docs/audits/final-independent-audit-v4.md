# Northstar v4 independent audit and corrective record

Status: active corrective cycle  
Date opened: 2026-08-08  
Production alias: <https://northstar-credit-platform.vercel.app>

## Phase 0 baseline

The latest `main` commit at the start of v4 was `bf1443e`. The existing verification
gate passed after removing two stale generated Next type files from the local build
cache: 98 Python tests, 96.07% branch-aware application/API coverage, Ruff, Ruff
format, strict Mypy, strict TypeScript, ESLint, and Next.js production build.

The v4 audit is independent of the prior “complete” label. The following gap matrix
records behavior observed in source inspection and will be updated with reproduction
and post-fix evidence.

## Post-fix evidence (current worktree)

The canonical-source, LTM, period-validation, pricing-block, and basic facility
mechanics corrections are now implemented. The repository gate passes with 103
Python tests, 92.16% total coverage, Ruff, strict Mypy, strict TypeScript, ESLint,
and Next.js production build. The new v4 regression file is
`tests/unit/test_v4_canonical_resolution.py` (105 tests total; 91.60% total coverage).
The independent Claude challenge and
its required revisions are recorded in `docs/collaboration/v4-claude-opus-5-review.md`.

The remaining items are deliberately not marked complete: governed overrides and
metric-level severity, restatement/entity/scope controls, full borrowing-base
availability policy, provenance E2E coverage, and the final public redeploy/re-audit.

## Final public deployment evidence

- GitHub `main`: commit `2020c8e` (includes the V4 implementation commit `c7a87d9`)
- Vercel production deployment: `dpl_HThbHYhoF5xRTEXK9CFZzo4Fubmk`
- Ready state: `READY`; production alias: <https://northstar-credit-platform.vercel.app>
- Public checks: `/`, `/zh-TW`, `/health`, `/runtime`, `/demo-cases`, all HTTP 200
- Demo workflow: template GET 200, demo open 200, analyze 200, English detailed PDF 200
  (5 pages), Traditional Chinese detailed PDF 200
- Vercel runtime log sample: all final deployment requests above completed without
  error. An earlier deployment was intentionally not retained after its log exposed
  the missing `reportlab` dependency; `pyproject.toml` was corrected before the final
  production deployment.

## Current-state gap matrix

| Area | Current behavior | Expected behavior | Impact | Severity | Reproduction | Source files | Planned proof |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Canonical financial source | Fixed: resolver materializes `ResolvedFinancialSnapshot`; unresolved non-empty spread blocks and does not fall back | A valid selected LTM drives all decision outputs; legacy is fallback only when spread is empty | Remaining risk is governance of scope/version/override | P0 | v4 test changes source periods and checks analysis provenance | `analysis.py`, `spreading.py`, `models.py` | `test_v4_canonical_resolution.py` |
| LTM | Fixed: FY/YTD and four-quarter methods calculate normalized values with lineage | Explicit flow type, date contiguity, reconciliation, and no annualization | Average-balance and restatement policies remain | P0 | v4 arithmetic and gap tests | `spreading.py` | `test_v4_canonical_resolution.py` |
| Period validation | Fixed: duplicate fiscal metadata, quarter overlap, source/date, flow-type, and balance checks | Tiered severity and governed overrides remain | Metric-level blocks are still follow-on | P0 | v4 cumulative-YTD and gap tests | `models.py`, `spreading.py` | New regression gate |
| Facility mechanics | Fixed baseline: explicit fully-amortizing, partial, bullet, revolver draw, availability, commitment fee, and mandatory prepayment paths | Asset-based availability and detailed maturity/refinancing policy remain | Forecast horizon still three years | P0 | v4 bullet/revolver test | `models.py`, `analysis.py`, `facility.py` | Mechanics regression gate |
| Rate architecture | Fixed: pricing blocks with no rate when grade/canonical source is blocked; one conservative underwritten rate feeds capacity/stress | Full market index/spread governance remains | Rate floor/index semantics need documentation | P0 | Blocked pricing and underwritten-rate path | `analysis.py`, `facility.py` | Regression gate |
| Facility protection | Fixed: requested and recommended coverage are both returned and memo-visible | Evidence-backed seniority/guarantee still requires production controls | Coverage policy remains illustrative | P0 | Requested/recommended fields | `facility.py`, `analysis.py` | Regression gate |
| Adjustments | Approved item EBITDA impacts are used, but EBIT/CFADS/cash/recurrence/sign cross-fields are not fully enforced | Approved item metadata affects EBITDA, EBIT, and CFADS with evidence and consistent signs | Add-backs can distort multiple outputs | P0 | Submit mismatched item impacts | `models.py`, `spreading.py`, `analysis.py` | Adjustment bridge tests |
| Qualitative risk | Numeric score remains independently editable beside band | Band maps to policy; override requires evidence, rationale, reviewer, and audit | Score/band contradiction can alter grade | P0 | Pair severe band with 95 score | `models.py`, `analysis.py` | Band consistency tests |
| Borrowing base | Negative and overlapping deductions are clamped with `max(0, ...)`; other collateral is 100% eligible | Invalid inputs block; overlap and reserves are explicit; availability is separate | Invalid data may inflate capacity | P0 | Submit negative reserve or ineligible > gross | `facility.py`, `models.py` | Validation/availability tests |
| Decision status | API always marks analyzed after calculation; blocked result is not persisted as blocked | Blocked analysis has `blocked` status and no final grade/pricing | Users can see “analyzed” despite missing critical inputs | P1 | Analyze a case missing factor evidence | `main.py`, `analysis.py` | Lifecycle integration test |
| Guided provenance | Demo/template-derived values can be retained after changing borrower name | Template-derived badges, unchanged count, warning, clear action, acknowledgment | Renamed template can look borrower-specific | P1 | Rename demo borrower and inspect review | `NewCase.tsx`, `models.py` | E2E provenance test |
| Methodology | Public pages describe prior and current behavior unevenly | Methodology, UI, memo, PDF, and runtime agree | Misleading portfolio-demo positioning | P1 | Compare methodology text with output fields | `InfoPage.tsx`, `pdf.py`, docs | Localization/content scan |

## Collaboration gate

Codex proposal and the independent Claude Opus 5 High challenge are recorded in
`docs/collaboration/v4-claude-opus-5-review.md`; decisions and rejected alternatives
are recorded in `docs/collaboration/v4-decision-log.md`.

## Product boundary

Northstar remains Portfolio Demo Mode: synthetic data, anonymous HttpOnly session,
temporary seven-day storage, quotas, best-effort instance rate limiting, and
educational analysis only.
