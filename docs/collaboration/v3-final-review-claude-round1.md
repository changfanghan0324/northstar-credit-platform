# v3 Claude Opus 5 final review — round 1

Date: 2026-08-06  
Reviewer: Claude Opus 5 (`claude-opus-5`, high effort)  
Claude Code: 2.1.221  
Session: `ad9b10bf-5304-4a42-9e9b-7f6fa2e2cda4`  
Turns: 51  
Disposition: `REJECTED`

Claude read the complete 1,743-line v3 master prompt and the current repository in
read-only mode. It made no edits. Its two attempts to execute `./scripts/verify` were
denied by its own tool permission policy; Codex independently reproduced the gate.

## Blocking findings

1. Adverse not-meaningful leverage could still become the best leverage score because
   `_scoreable()` returned zero for a lower-is-better measure. Zero and negative
   EBITDA had no regression coverage.
2. Covenant recommendations were identical for every borrower and omitted responsive
   interest-coverage, liquidity, reporting, distributions, capex, borrowing-base, and
   collateral-reporting protections.
3. The Traditional Chinese decision page replaced actual rationale, conditions, and
   repayment-source output with fixed text, allowing the two languages to state
   different model conclusions.

## Major required fixes accepted by Codex

- Dynamic confidence and broader policy checks.
- Debt-roll-forward identity and instrument schedule use.
- Real validation, stale duplicate behavior, enforced TTL, and structured validation
  errors.
- Rate limiting for computed demo endpoints.
- SSR-correct document language, mobile site navigation, responsive tables, and no
  hidden mobile outcome strip.
- English PDF punctuation and fuller localized executive/detailed PDF content.

The complete reviewer output remains available in the Codex task transcript. This
record summarizes it without claiming approval. Round 2 is mandatory after fixes.
