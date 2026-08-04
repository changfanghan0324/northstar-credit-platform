# Review Log

Task 1 engine primitives are accepted. Later implementation phases are not yet
accepted.

Each entry must include:

- date and task
- author and reviewer
- exact model identifier
- changed files
- reviewed diff SHA-256 or commit SHA
- hunk-by-hunk coverage statement
- independent tests or reproduction performed
- findings and required fixes
- final disposition: `approved`, `approved-with-required-fixes`, or `rejected`
- re-review evidence when fixes were required

## Review entries

### 2026-08-03 — Planning, methodology, and pre-implementation tests

- Author: Codex.
- Reviewer: Claude Opus 5 (`claude-opus-5`).
- Evidence: `methodology-signoff.md` and `planning-review-claude.md`; all new-file add hunks covered section-by-section.
- Disposition: planning files mixed `approved` / `approved-with-required-fixes`; methodology and two test files `approved-with-required-fixes`; `test_task1_architecture.py` rejected for false-green enforcement.
- Required fixes: methodology F1–F4/F12, strict float rejection, non-vacuous recursive purity checks, broader import/float AST guards, log wording and sequencing metadata.
- Fix status: implemented by Codex; amended golden/formula hashes recorded.
- Re-review: Claude Opus 5 reviewed every requested fix in `methodology-rereview-claude.md`, counter-signed the methodology and formula specification, and lifted the architecture-test rejection. The required formula hash was subsequently reproduced exactly as `0c22bf27006282e4309da4f7b4ee8e9abc6178402a4b0a0ffced2c84985caa29`.
- Final disposition: `approved` for implementation.

### 2026-08-03 — Task 1 engine primitives, Codex round 1

- Author: Claude Opus 5 (`claude-opus-5`).
- Reviewer: Codex.
- Files: `packages/credit_engine/credit_engine/{__init__,types,money,cashflow,ratios}.py`.
- Reviewed bundle SHA-256: `b19722b2aa71961b2a22b66945ac6dae6ffdc98969c82a3bde762dd2cd3a3934`; every add-hunk line read.
- Reproduction: 20 pre-authored tests passed; revealed golden hash matched; stable-case money and ratio values matched; eight reviewer regression tests failed and reproduced C1–C8.
- Disposition: `approved-with-required-fixes`.
- Required fixes: missing-data precedence, proposed-principal currency, known-currency exponent, non-OK policy trace, runway reason code, ROIC fallback confidence, monetary confidence factors.
- Re-review: completed on 2026-08-04 by Claude Opus 5 in the two records cited in
  the required-fix entry below. All round-1 defects and the additional re-review
  blockers were closed before acceptance.

### 2026-08-04 — Task 1 engine primitives, required-fix implementation

- Original author: Claude Opus 5 (`claude-opus-5`); required-fix author: Codex.
- Required reviewer: Claude Opus 5 (`claude-opus-5`) through Claude Code 2.1.221,
  session `cd83228c-c036-4edb-b22e-cb97dd3ff177`, running inside this Codex
  project. Claude received only read and bounded Bash capabilities and did not edit
  project files.
- Files: `packages/credit_engine/credit_engine/{types,money,cashflow,ratios}.py`,
  `tests/unit/{test_task1_contracts,test_task1_engine_complete}.py`,
  `docs/methodology.md`, `pyproject.toml`, `.gitignore`, and `scripts/verify`.
- Final engine-and-test bundle SHA-256:
  `4bb34ad128289b6336d3b7a797ec22e1d05ab983821fd503285b5bfc18db6ccc`.
  Supporting digests independently reproduced by Claude were `pyproject.toml`
  `7dc9f96909acb708a11bdd25205d25df46128bae28eeb38bba5c017a67b1651c`,
  methodology `1d15a8551b2b4f3546302406f65ad84f556d4aa8dc8fcb0bb90d0c744d95dfa1`,
  verify script `66930c9eaa2cb75dd5ef0b02b21eb0f757861c5d301de2cc4c5fb68f2fea41b6`,
  ignore file `3be0ee4be7185c67ce609a0638dceb4a456d6cb191cda0897ad8d476f940a0ec`,
  and formula specification `0c22bf27006282e4309da4f7b4ee8e9abc6178402a4b0a0ffced2c84985caa29`.
- Fix coverage: C1–C8 were reviewed hunk-by-hunk. Claude's first re-review
  additionally found and required closure of a pro forma DSCR missing-principal
  false-favorable path, undeclared Ruff/Mypy tooling, unevidenced strict Mypy/Ruff
  configuration, and a non-discriminating ratio rounding test. Codex fixed all four
  and added regression/configuration evidence without weakening assertions.
- Hunk coverage: Claude read all 18 round-1 files in full, then re-derived the
  round-2 diff line offsets and confirmed the DSCR hunk was the sole `ratios.py`
  change, one new contract test accounted for the test-count change, and the shared
  exponent assertion was the sole engine-complete-test change.
- Independent reproduction: Claude ran the requested bundle hash, five supporting
  hashes, and `PYTHON_BIN=.venv-rebuilt/bin/python ./scripts/verify`. Results were 54
  passing tests, 99.53% branch-aware coverage, clean Ruff lint and format, and clean
  strict Mypy across all five engine modules, with no discrepancy from Codex's run.
- Evidence: `task1-rereview-claude-opus-5-round1.md` records the initial
  `approved-with-required-fixes` result; `task1-rereview-claude-opus-5-round2.md`
  records each blocker as resolved and ends `TASK_1_ACCEPTED: yes`.
- Non-blocking backlog: the round-1 F5–F9 advisories remain recorded for later work;
  Claude explicitly determined they do not gate Task 1 acceptance.
- Final disposition: `approved`.
