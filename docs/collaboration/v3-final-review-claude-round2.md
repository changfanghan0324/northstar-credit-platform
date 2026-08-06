# Northstar v3 — Claude final review, round 2

- Reviewer: Claude Opus 5, high effort
- Session: `7604e3b5-e323-45f3-9a18-ab9ad73992a3`
- Scope: full corrective master prompt, current implementation, current diff, and independent repository verification
- Verification reproduced by reviewer: `./scripts/verify` exited 0; 79 tests passed
- Verdict: `APPROVED_WITH_REQUIRED_FIXES`

## Resolved blockers

Claude independently confirmed that all three round-one P0 findings were corrected:

1. Adverse not-meaningful leverage no longer receives favorable scoring.
2. Covenant packages respond to facility type, collateral reliance, downside headroom, and risk.
3. Traditional Chinese decision presentation preserves the underlying model outcome and repayment logic.

The reviewer also confirmed typed missing/invalid scoring, zero-supported decision priority, all thirteen active policy checks, the three-year debt identity, validation and stale-analysis lifecycle, anonymous-session TTL enforcement, demo rate limits, server-rendered language metadata, mobile navigation, and English PDF punctuation.

## Required-fix register from that review

The round-two report identified thirteen P1 items. They were entered into the implementation closeout and addressed as follows:

| Finding | Closeout |
|---|---|
| Chinese detailed PDF was thinner and exposed machine labels | Expanded localized debt, adjustment, scenario, policy, monitoring, limitations, and sign-off sections; mapped common machine labels. |
| Machine field names remained in parts of the UI | Added field, scenario, constraint, outcome, condition, and priority presentation mappings for primary workflows. |
| Clearing a money field could throw | Empty money input now enters a controlled zero value and is validated before analysis. |
| Scenario save and PDF download lacked recoverable error states | Added busy, `try/catch/finally`, and visible alert handling. |
| Material inputs were not all editable after creation | The inputs workspace exposes request and full financial inputs; scenario assumptions are editable on the stress page. |
| Wizard lacked debt schedule entry | Added editable debt instruments including balance, pricing, amortization, maturity, seniority, collateral, and security. |
| Wizard review was not a true validation preview | Added pre-creation server validation with missing fields, warnings, and estimated confidence. |
| Business-risk fields used bare keys | Added guided questions, evidence prompts, and localized labels. |
| Methodology covered only eight topics | Expanded to twenty bilingual methodology topics. |
| Reverse-stress presentation overstated non-convergence | Retains bounded solver diagnostics and surfaces convergence status, bounds, tolerance, iterations, and residual. |
| Revolver draws had no interest; later-year revenue shock compounded implicitly | Added half-year revolver-draw interest and a distinct subsequent-year growth assumption. |
| Blocked profitability could display a favorable score | Adverse not-meaningful higher-is-better measures now score zero while remaining blocked. |
| No browser/visual/production evidence | Closed through local responsive browser QA, screenshots, public deployment smoke testing, and the repository verification gate. |

No Claude process edited repository files. Codex remained the implementation owner and used Claude strictly as an independent read-only reviewer.
