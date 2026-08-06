# v3 independent Claude review — round 1

Date: 2026-08-05  
Reviewer: Claude Opus 5 (`claude-opus-5`, high effort)  
Runtime: Claude Code 2.1.221, launched read-only from inside the Codex project  
Session: `4e5cf32e-a497-4f30-8e74-4ed5c1354641`

## Scope and independence

Claude received read-only `Read`, `Grep`, and `Glob` tools and inspected the actual
engine, application models, policy, API/database, migrations, tests, and web app. It
did not edit repository files. The first session could not open the corrective prompt
from Downloads because of its filesystem sandbox; the six-part Codex proposal was
therefore included in the review request. A final re-review is required with the
prompt explicitly added to Claude's read scope.

## Confirmed defects

- Missing and invalid ratios were coerced to zero before scoring, creating inverted
  favorable outcomes for measures where lower is better.
- Collateral capacity lacked a typed applicability state and could constrain an
  unsecured request.
- Zero supportable exposure led to referral instead of decline.
- Scenario mechanics did not maintain a complete debt, interest, cash, revolver, and
  refinancing roll-forward; the reverse-stress output was not a numerical solver.
- Anonymous ownership trusted a client-selected session identifier, while Vercel's
  SQLite fallback lived in `/tmp` and could not truthfully provide durable storage.
- The custom flow, case workspace, Guided/Analyst distinction, Traditional Chinese
  coverage, and PDF output were materially incomplete.
- Test coverage measured the pure engine only and did not substantiate application,
  API, security, persistence, or PDF behavior.

## Required invariants and corrections

1. Critical missing or invalid measures must block final scoring; no coercion to zero.
2. Every capacity constraint must be valid, blocked, or policy-not-applicable before
   it can participate in the minimum; zero supportable exposure must decline.
3. Reverse stress must establish a bracket, document monotonicity assumptions, expose
   tolerance/residual/iterations, and return a typed non-convergence result.
4. Session identifiers must be server-generated and stored only as hashes. Every case
   operation must enforce ownership, quotas, payload limits, and CORS controls.
5. Scoring must disclose blocked components and confidence penalties instead of
   silently reweighting missing data.
6. PDF generation must localize content, display human currency, sanitize filenames,
   and paginate instead of silently truncating lines.
7. Input provenance must bind the case, policy version/hash, and engine version.

## Verdict

Direction approved, previous implementation rejected until the P0 invariants and
operational controls above were implemented and independently re-reviewed.
