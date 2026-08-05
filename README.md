# Northstar Credit Platform

A deterministic credit-analysis engine with Decimal-safe money, typed reason codes,
currency guards, explicit confidence handling, and independently reproduced review
evidence.

## Public delivery

- Website: https://northstar-credit-platform.vercel.app
- Source: `packages/credit_engine/credit_engine/`
- Methodology: `docs/methodology.md`
- Independent acceptance record:
  `docs/collaboration/task1-rereview-claude-opus-5-round2.md`

## Verification

```sh
PYTHON_BIN=.venv-rebuilt/bin/python ./scripts/verify
```

The accepted Task 1 build passes 54 tests with 99.53% branch-aware coverage, clean
Ruff lint and formatting, and clean strict Mypy checks. Claude Opus 5 independently
reproduced the verification gate and accepted the implementation.

## Website

The public project page is a dependency-free static site. Run it locally with any
static HTTP server, for example:

```sh
python3 -m http.server 4173
```
