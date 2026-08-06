# v3 implementation task board

## P0 — model correctness

- [x] Replace ratio state vocabulary and remove missing-to-zero coercion.
- [x] Block final grade for critical missing/adverse invalid inputs.
- [x] Add capacity applicability and zero-exposure decision priority.
- [x] Evaluate maturity, liquidity, interest coverage, leverage, DSCR, and currency policy checks.
- [x] Implement debt/interest/cash/revolver/refinancing roll-forward.
- [x] Implement real reverse-stress bisection with convergence metadata.
- [x] Add invariant/property tests and update all three golden cases.

## P1 — persistence, workflow, UX

- [x] Normalized migration with versions, analyses, checks, constraints, covenants, memos, and audit logs.
- [x] Cryptographic anonymous ownership, honest runtime mode, quota/rate/PDF/payload/CORS controls.
- [x] List/create/update/validate/analyze/stale/rerun/duplicate/archive/delete APIs.
- [x] Read-only demo template and exactly-one-record sample/custom flows.
- [x] Seven-step editable case wizard with review gate and recoverable template state.
- [x] Case list with search/filter/sort/reopen/rename-by-edit/duplicate/archive/delete.
- [x] Eight-question workspace including dedicated capacity page.
- [x] Distinct Guided and Analyst presentations over identical values.
- [x] English/Traditional Chinese routes, primary product copy, error states, and metadata.
- [x] Accessible mobile drawer, error states, keyboard support, and responsive tables.
- [x] Dynamic confidence and responsive covenant recommendations.
- [x] One-page/detailed localized memo and paginated PDF.

## P2 — evidence and polish

- [x] Complete methodology, limitations, retention, architecture, and README.
- [x] Browser E2E for fourteen required flows and screenshots at 390/768/1024/desktop.
- [x] Accessibility and visual fidelity review against the established Northstar concept system.
- [x] Claude re-review of critical calculations, database/session ownership, and PDF line by line.
- [x] Close all P0/P1 findings; deploy production, smoke-test the public alias, verify lifecycle/PDF controls, and confirm honest temporary-session persistence reporting.
