# Structured Debate — Round 1: Codex Comparison and Challenge

Date: 2026-08-03  
Codex proposal: `codex-independent-proposal.md`  
Claude proposal: `claude-independent-proposal.md`  

## Agreements

1. Primary persona is the junior credit or banking analyst; recruiter/interviewer and finance student are secondary. A borrower self-service experience is a different product.
2. Progressive disclosure is required even though the primary persona is an analyst.
3. A pinned synthetic sample case must make the homepage useful on first load.
4. The financial spine is deterministic: financials → adjustments → debt → CFADS/ratios → separate obligor/facility assessments → capacity → stress/covenants/reverse stress → decision → traceable memo.
5. `packages/credit_engine` is a pure Python domain library and policy thresholds are versioned data.
6. Live SEC ingestion, authentication, AI decisioning, ML, Monte Carlo, and a full Power BI binary are not required for the honest portfolio MVP. Extension points and limitations must be explicit.
7. Three golden cases must produce materially different outcomes.

## Codex challenges to Claude

### 1. The mode-toggle proposal under-reads an explicit acceptance gate

The prompt requires Guided Mode, Analyst Mode, an `AdvancedModeToggle` component, and tests for guided/analyst mode. Eliminating the toggle entirely risks a literal acceptance failure. However, duplicating the application would be wasteful. Codex proposes a narrow case-level preference called **Analyst details** that expands formulas, thresholds, lineage, and additional columns on the same routes and components. It is not a second application and does not double routing or data states.

Counterexample to route-only density: a recruiter or student opens `/cases/{id}/financials` from a deep link. Route-only density forces the full spread immediately, while the same page could default to five essential rows and reveal the complete spread when Analyst details is enabled. The route does not always determine the user's information tolerance.

### 2. Excel cannot be cut below the named reference structure

The master prompt explicitly lists 20 workbook tabs and makes Excel/Python reconciliation an MVP criterion. Merging the scenario sheets may be elegant but creates a needless acceptance dispute and makes side-by-side base/downside/severe audit harder. Codex proposes keeping the 20 named tabs, while using shared formulas and compact instructions to control maintenance.

### 3. Power BI scope should distinguish "binary" from "specification"

The final deliverable permits a "Power BI specification or dashboard files where available." A 40-borrower synthetic dataset, star-schema files, documented measures, and an in-app portfolio page satisfy the honest local deliverable. No claim should be made that a `.pbix` exists. Claude's one-page phrase should not override the ten-page Power BI specification requested in §36; specifying ten pages is cheap and useful even when implementing only the in-app page.

### 4. Postgres everywhere has an onboarding counterexample

Postgres production parity is desirable, but a recruiter cloning the repo on a machine without Docker should still be able to run pure engine tests and view the frontend demo. Codex proposes:

- Postgres is the only supported persistent API database.
- Docker Compose provides the canonical full-stack path.
- Engine unit tests need no database.
- Frontend can run against committed typed sample fixtures for a read-only demo mode when the API is absent.

This does not introduce SQLite divergence and materially improves demonstration resilience.

### 5. "NM" requires separate zero-denominator semantics

Treating all zero denominators as one `nm` state is insufficient.

- Positive EBITDA / zero interest means no current interest burden; displaying Infinity is poor, but the state is favorable and must not be scored like missing data.
- CFADS / zero debt service means no current scheduled service; it is not an approval blocker by itself, but a proposed facility must generate nonzero pro forma service before a final decision.
- Negative EBITDA leverage is adverse NM and should not receive neutral treatment.
- Missing interest is `missing`, not `nm`.

Codex proposes `status` plus a typed `reason_code` and score policy mapping so UI wording and scoring cannot conflate favorable NM, adverse NM, and missing data.

### 6. Integer cents is necessary but not sufficient

Integer minor units should represent monetary amounts, but the engine also needs explicit currency and scale at boundaries. A JPY amount has no decimal minor units; SEC facts may arrive in units or thousands; a workbook may display USD millions. Every normalized monetary value should carry currency and stored minor-unit integer, with scale conversion validated exactly once at ingestion. Ratios may use `Decimal` internally and serialize to numbers/strings deliberately; binary floats should not decide thresholds near boundaries.

### 7. Confidence should not disappear

Claude is right to reject a fake numeric percentage. The prompt still requires confidence on user-visible results. Codex proposes deterministic categorical confidence (`high`, `medium`, `low`, `blocked`) derived from completeness, source quality, recency, reconciliation, and overrides, alongside data-quality state (`complete`, `partial`, `blocked`). These answer different questions and remain explainable.

### 8. First-task ownership

Codex accepts Claude as author of the pure financial core because it makes Claude a meaningful implementer immediately. Before reading Claude's implementation, Codex will author adversarial specification tests for denominator semantics, monotonicity, money/currency boundaries, and stable-case expectations. Claude then implements against the published acceptance criteria; Codex reviews every diff hunk and Claude fixes/re-submits.

## Proposed resolution

- Keep Claude's analyst-primary persona, scope cuts, pinned sample, pure engine, immutable calculation runs, and typed NM approach.
- Adopt the narrow Analyst-details toggle to satisfy the explicit two-level experience without duplicating routes.
- Keep all 20 Excel tabs and the full ten-page Power BI specification, while implementing one in-app portfolio page and clearly omitting a `.pbix` binary.
- Use Postgres only for persistence, Docker for the canonical stack, database-free unit tests, and fixture-backed frontend demo resilience.
- Enrich `RatioResult` with `reason_code`, `components`, and categorical confidence.
- Claude authors the first engine module after Codex publishes adversarial tests.
