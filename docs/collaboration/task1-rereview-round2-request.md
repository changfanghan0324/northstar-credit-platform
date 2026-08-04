# Task 1 Claude Re-Review — Round 2 Request

Date: 2026-08-04

This request addresses every blocking item in Claude Opus 5 session
`cd83228c-c036-4edb-b22e-cb97dd3ff177`. Codex authored the fixes. Claude remains the
independent non-author reviewer.

## Blocking fixes applied

1. F1: zero-service pro forma DSCR now returns `MISSING` / `missing_input` with
   blocked confidence when `proposed_principal` is absent. A regression test confirms
   the outcome is not favorable NM.
2. F2: the root dev dependency group now pins `ruff==0.16.1` and `mypy==1.20.2`.
3. F3: root configuration now enables strict Mypy and an explicit Ruff rule set.
4. F4: the ratio rounding test now uses `1.23465`, which distinguishes
   `ROUND_HALF_UP` from `ROUND_HALF_EVEN`, and the shared `assert_ok` helper pins the
   four-decimal exponent for all covered successful ratios.
5. Reproduction: the reviewer is explicitly authorized to run the bounded commands
   below from the project root. No file enumeration beyond the stated paths is needed.

## Changed files for this round

- `packages/credit_engine/credit_engine/ratios.py`
- `tests/unit/test_task1_contracts.py`
- `tests/unit/test_task1_engine_complete.py`
- `pyproject.toml`
- `docs/collaboration/task1-rereview-round2-request.md`

The round-1 report was captured verbatim at
`docs/collaboration/task1-rereview-claude-opus-5-round1.md`; that capture does not
change implementation behavior.

## Required reproduction commands

```sh
find packages/credit_engine/credit_engine tests/unit -type f -name '*.py' -print0 \
  | sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

Expected engine-and-test bundle digest:
`4bb34ad128289b6336d3b7a797ec22e1d05ab983821fd503285b5bfc18db6ccc`.

```sh
shasum -a 256 pyproject.toml scripts/verify excel/formulas/core.yaml \
  docs/methodology.md .gitignore
```

Expected digests:

- `pyproject.toml`: `7dc9f96909acb708a11bdd25205d25df46128bae28eeb38bba5c017a67b1651c`
- `scripts/verify`: `66930c9eaa2cb75dd5ef0b02b21eb0f757861c5d301de2cc4c5fb68f2fea41b6`
- `excel/formulas/core.yaml`: `0c22bf27006282e4309da4f7b4ee8e9abc6178402a4b0a0ffced2c84985caa29`
- `docs/methodology.md`: `1d15a8551b2b4f3546302406f65ad84f556d4aa8dc8fcb0bb90d0c744d95dfa1`
- `.gitignore`: `3be0ee4be7185c67ce609a0638dceb4a456d6cb191cda0897ad8d476f940a0ec`

```sh
PYTHON_BIN=.venv-rebuilt/bin/python ./scripts/verify
```

Codex reproduction before handoff: 54 tests passed, total branch-aware coverage
99.53%, Ruff check and format check clean, strict Mypy clean.

## Reviewer response required

- Read the five changed files and the round-1 disposition.
- Run all three reproduction commands exactly.
- Decide each blocking item F1–F4 and the reproduction requirement.
- Report any new blocking defect separately from the round-1 non-blocking backlog.
- End with exactly one of `TASK_1_ACCEPTED: yes` or `TASK_1_ACCEPTED: no`.

Do not edit any project file.
