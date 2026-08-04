# Task 1 Required-Fix Re-Review Request

Date: 2026-08-04  
Requested reviewer: Claude Opus 5 (`claude-opus-5`)  
Original implementation author: Claude Opus 5  
Required-fix author: Codex

## Scope

Review every changed line in:

- `packages/credit_engine/credit_engine/types.py`
- `packages/credit_engine/credit_engine/money.py`
- `packages/credit_engine/credit_engine/cashflow.py`
- `packages/credit_engine/credit_engine/ratios.py`
- `tests/unit/test_task1_engine_complete.py`
- `docs/methodology.md`
- `.gitignore`
- `scripts/verify`

The deterministic engine-and-test bundle SHA-256 is:

`29fe54d7ebe2e772c35fa99e54956addec1bded1eaf275287b3d07a412829700`

Reproduce it from the repository root with:

```sh
find packages/credit_engine/credit_engine tests/unit -type f -name '*.py' -print0 \
  | sort -z \
  | xargs -0 shasum -a 256 \
  | shasum -a 256
```

## Required-fix checklist

Confirm independently that:

1. missing ratio inputs take precedence over favorable zero-denominator outcomes;
2. proposed principal participates in the DSCR currency guard;
3. known ISO currencies reject an incorrect minor-unit exponent;
4. non-OK ratio results preserve formula and policy references;
5. zero or negative stressed cash burn returns the distinct favorable reason `nm_no_cash_burn`;
6. single-period ROA and ROIC fallbacks are explicitly low confidence and preserve blocked states;
7. monetary metric results can carry confidence factors; and
8. fixed-charge coverage and liquidity runway are statically type-safe after missing-input guards.

Also confirm that the new tests do not encode or reveal a hidden golden output and do not reward an incorrect formula.

## Reproduction

Run:

```sh
./scripts/verify
```

The author-side result was 53 passing tests, 99.53% branch-aware engine coverage, clean Ruff lint and formatting, and clean Mypy output for all engine modules.

## Required response

Record a hunk-by-hunk coverage statement, independent reproduction, findings, required fixes, and one disposition: `approved`, `approved-with-required-fixes`, or `rejected`. If fixes are required, re-review them before marking Task 1 accepted.
