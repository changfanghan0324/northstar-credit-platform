# Northstar v4 decision log

Status: revised after independent challenge; follow-on governance remains open  
Date: 2026-08-08  
Codex author: implementation proposal

## Decision V4-01 — canonical financial source

Proposal: add a deterministic resolver that selects a valid derived or reported LTM
from `financial_spread`, materializes the selected values into one immutable
underwriting snapshot, and uses that snapshot for ratios, score, capacity, scenarios,
pricing, decision, memo, and PDF. Legacy `financials` is used only when the spread is
empty and the output is labeled `legacy_snapshot`.

Rejected alternative: patch each downstream consumer independently. This would leave
multiple source-selection rules and make future divergence likely.

## Decision V4-02 — LTM representation

Proposal: calculate a real immutable `ResolvedFinancialSnapshot` in the spreading layer
with source period IDs, lineage, normalized currency/scale, and reconciliation state.
The API view keeps the selected period ID and status for explainability.

Rejected alternative: keep pseudo-IDs and status-only labels. That is the defect v4 is
required to close.

## Decision V4-03 — scope order

Proposal: implement the canonical source and LTM/validation gates first, then facility
and rate mechanics, then evidence/borrowing-base/UX polish. This minimizes the risk of
shipping a more polished UI over inconsistent decision numbers.

## Independent challenge and revisions

Claude Opus 5 High challenged the three proposals in session
`e8cdd3c7-1ca4-419a-8c8f-b074f60b183a` and returned **REVISE** for each. The full
record is in `v4-claude-opus-5-review.md`.

- V4-01 was revised to block every failed non-empty spread, retain immutable source
  lineage, and require explicit eligibility rules before a spread becomes canonical.
- V4-02 was revised to require explicit cumulative/discrete flow type, date-based
  contiguity, scale normalization, reconciliation, and no annualization. The first
  implementation and regression tests now enforce those rules.
- V4-03 was revised toward tiered severity. The current implementation closes the
  fallback loophole and exposes actionable blocking issues; role-gated overrides,
  metric-level blocks, restatement/entity scope and cache governance remain tracked
  follow-on work and are not claimed as complete.
