# Northstar interface system

## Direction

Northstar uses an editorial banking-brief visual language: true white, deep ink and
navy, a restrained copper action color, pale blue-gray analytical surfaces, crisp
one-pixel rules, tabular figures, and generous whitespace. Georgia supplies the
display voice; system sans-serif fonts keep dense UI legible. The product uses no
gradients, no decorative data visualizations, and no marketing proof badges.

## Product hierarchy

The public homepage leads with the lending question, then exposes three synthetic
borrower profiles whose outputs are calculated by the live API. Engine tests,
technical validation, repository links, and collaboration evidence remain available
in documentation but do not compete with the first-minute product story.

The analyst workspace follows the underwriting sequence: Overview, Inputs,
Financials, Risk, Stress & Covenants, Decision, and Credit Memo. Guided and Analyst
modes are presentation modes over one persisted input and calculation contract.

## Responsive rules

- At desktop width, the workspace uses a fixed underwriting rail and a fluid canvas.
- Below 900px, the rail is removed and all analytical grids become single-column or
  two-column as space permits.
- At 390px, navigation is reduced to brand and language switch, actions become
  full-width, and horizontal document overflow is prohibited.

## Image-concept fidelity ledger

The six generated concepts established the structural direction rather than literal
content. The implementation preserves their editorial hierarchy, navy/copper
palette, serif display typography, crisp rule system, capacity comparison, scenario
cards, covenant table, decision terms, and document-like memo.

Intentional corrections:

- All borrower names, dates, ratios, grades, capacities, and decisions come from the
  runtime API; concept-image example numbers were not copied.
- The concept's incorrect DSCR explanatory note and invented analysis date were
  excluded.
- The workspace rail uses the seven required product surfaces rather than the extra
  concept-image labels.
- The mode switch lives in the rail so it remains visually secondary to the credit
  decision.
- The memo uses deterministic template copy with input and policy hashes rather than
  invented analyst or bank identities.
