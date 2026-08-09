# Bullet exit and maturity contract

## Purpose

Bullet and partial-balloon facilities are rolled through contractual maturity,
even when the visible stress table remains three years. The three-year table
is a presentation window; it is not a maturity assumption.

## Required outputs

Each bullet or partial scenario exposes:

- contractual `maturity_year`;
- contractual `balloon_amount` and maturity `residual_debt`;
- `exit_ebitda` and `exit_leverage` after the full maturity roll-forward;
- policy-based `refinance_capacity` and `refinance_headroom`;
- `no_refinancing_status` and an explanatory reason;
- `maturity_test_status` and an explicit reason.

The balloon is not treated as ordinary scheduled amortization. At maturity,
the residual debt remains visible while the contractual balloon is tested
against policy exit leverage and refinance capacity. The no-refinancing case
deducts the balloon from maturity cash and checks that minimum operating cash
is preserved. A severe case therefore reports a breach when the balloon cannot
be paid without refinancing or additional support.

## Evidence

`tests/unit/test_v5_logic_contract.py` rolls a five-year bullet beyond the
three-year display and asserts balloon, exit EBITDA/leverage, refinance
capacity/headroom, residual debt, and severe no-refinancing breach. API
integration tests assert the maturity fields and bilingual detailed PDF text.
