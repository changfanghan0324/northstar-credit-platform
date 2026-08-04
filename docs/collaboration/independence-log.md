# Independence Log

## Task 1 commitment — superseded

Recorded before Claude Opus 5 begins engine implementation and before Codex opens any Claude engine diff.

- Hidden independently derived golden values SHA-256: `a792223920d0269a66a4f53f411821370d52e35bf1bc211e1ed08fe9b9cd6edb`
- Independently authored Excel core formula specification SHA-256: `c0bff155103c111840d51aa6e525a2491cce31c54cbb216a188f36311ed022e2`
- Formula specification path: `excel/formulas/core.yaml`
- Golden plaintext status: derived values held outside the project workspace. Published inputs remain visible, so this is an anti-tamper timing control rather than a claim that the implementer cannot infer results.
- Derivation source: `docs/methodology.md`, manual Decimal calculations, and the Task 1 synthetic inputs in methodology §14.

This commitment was superseded after Claude review identified ambiguous lease treatment and debt-basis wording.

## Task 1 amended commitment — 2026-08-03

Recorded after methodology fixes F1–F4 and before Claude Opus 5 begins implementation or Codex opens any Claude engine diff.

- Hidden independently derived golden values SHA-256: `e914b23b862eb0a1cc5587402fee37fcfda1f6211ff785d052ce0c0d003f8fa3`
- Independently authored Excel core formula specification SHA-256: `0c22bf27006282e4309da4f7b4ee8e9abc6178402a4b0a0ffced2c84985caa29`
- Amendment reason: DSCR now excludes contractual operating rent already deducted in EBITDA/CFADS; leverage capacity explicitly uses existing gross debt excluding the proposed facility; the formula chain now defines DSCR capacity.
- Derived-value plaintext remains outside the project workspace until reveal.

After Claude's implementation is complete, plaintext is revealed into `tests/golden_cases/expected_values.json`; verification must reproduce the amended hash. Any further amendment requires a new hash and a disagreement-log entry citing the methodology clause and reason.
