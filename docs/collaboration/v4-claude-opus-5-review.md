# Claude Opus 5 High — Independent v4 Challenge

## Session evidence

- Runtime: local Claude CLI, version `2.1.223`
- Authentication: `claude auth status` reported the authenticated first-party account
- Model requested and returned: `claude-opus-5`
- Effort: `high`
- Tools: disabled for the review so the response was an independent text-only challenge, not a simulated repository inspection
- Session ID: `e8cdd3c7-1ca4-419a-8c8f-b074f60b183a`
- Output metadata: 9,661 output tokens; approximately 145.9 seconds; no permission denials; `canonicalModel: claude-opus-5`

This is recorded as an independent challenge record. Because the review was text-only, it is not represented as Claude having inspected or approved production code. Its disposition was “revise before implementation.”

## Challenge disposition

### V4-01 — Canonical resolver

**Disposition: REVISE.** The direction is correct, but the resolver must define eligibility rather than accepting any non-empty spread. Claude called out stale periods, missing required statements, entity/scope mismatches, precedence and versioning, an immutable pinned snapshot, and provenance on every downstream output. Audited FY or covenant/regulatory calculations may need an explicit carve-out rather than an accidental fallback.

The implementation response is a deterministic `resolve_underwriting_financials` snapshot. It blocks a non-empty spread that cannot be resolved, records source period IDs and field lineage, materializes the selected values once, and passes the resulting financial object to the analysis pipeline. Remaining production governance items are documented in the task board rather than hidden behind the legacy single-period path.

### V4-02 — LTM arithmetic and reconciliation

**Disposition: REVISE.** The arithmetic is acceptable only when cumulative versus discrete flow type is explicit; cumulative interim periods must not be summed. Contiguity should be proven by dates and fiscal metadata, not labels. Ratios that use balances may require average balances. Comparable definitions should include calendar, accounting basis, scope, mapping version, restatements, standards, fiscal calendars, and pro forma M&A flags. Annualization is prohibited. Reconciliation and sanity-bound outputs are required.

The implementation response adds explicit `flow_type`, four-quarter contiguity checks, FY + current YTD − prior YTD checks, scale normalization, balance-sheet reconciliation, core-line blocking, and lineage. The v4 tests cover discrete four-quarter summation, cumulative YTD arithmetic, a discrete-YTD block, and a quarter-gap block.

### V4-03 — Reconciliation severity and fallback

**Disposition: REVISE.** Claude recommended tiered severity rather than one global switch:

- **BLOCK:** overlap, gap, unknown calendar, cumulative ambiguity, currency/entity/mapping mismatch, or less than twelve months.
- **WARN / basis downgrade:** unaudited-to-audited mixing and 52/53-week calendars when the period remains comparable.
- **Override:** role-gated, reason-coded, immutable and logged.

Metric-level blocks are preferred: missing cash-flow data should block DSCR while preserving leverage where valid. The highest-risk issue is a fallback loophole where old numbers survive a failed spread. The review also requested actionable errors.

The implementation response closes the fallback loophole for the main underwriting path: any supplied but unresolved spread produces a blocked snapshot and blocked pricing. The task board retains metric-level blocking, governed override, restatement policy, and cache/concurrency controls as follow-on governance items rather than claiming they already exist.

## Hidden risks recorded

Claude additionally identified portfolio-wide metric shifts, model-risk/change-control requirements, downstream “two truths,” cache/concurrency races, scope ambiguity, tax-only and FX issues, interim bias, single-resolver failure, and orphaned references. These are explicitly tracked in `docs/implementation-task-board-v4.md`.

## Required test themes recorded

The challenge required golden cross-method parity, cumulative interim tests, a period matrix, precedence tests, a fallback-loophole test, determinism/hash/replay tests, average-versus-ending balance tests, and scenario flags. The repository now includes the first canonical-resolution and mechanics gate in `tests/unit/test_v4_canonical_resolution.py`; remaining governance themes are tracked as pending rather than represented as completed.

## Post-implementation challenge

A second no-tool Claude Opus 5 High challenge was run after the implementation
changes:

- Session ID: `d90a1a33-4540-4fd2-b424-fdc333b93792`
- Actual model metadata: `canonicalModel: claude-opus-5`
- Effort: `high`; output: 8,455 tokens; duration: 125.1 seconds; cost: approximately $1.27
- Permission denials: none; terminal reason: completed

**Disposition: NOT APPROVED.** The challenge identified eight P0 risks and ten P1
risks. The immediate corrective follow-up added explicit positive/non-zero source
guards, replayable `snapshot_hash` plus resolver version, blocked capacity status when
pricing is blocked, index-shock treatment that avoids adding the margin twice, and
cross-method revenue/EBITDA divergence checks. Existing balance-sheet composition is
already point-in-time (only flow fields are composed); monetary amounts are integer
minor units with Decimal rates. Remaining P0/P1 governance requirements are kept
visible in the task board: line-kind metadata, full rate-decision object, restatement
precedence and filing dates, stale/as-of thresholds, metric-level severity, complete
facility schedule sizing, and OpenAPI/provenance snapshot tests. No approval is
claimed until those controls are implemented or explicitly accepted as product scope.
