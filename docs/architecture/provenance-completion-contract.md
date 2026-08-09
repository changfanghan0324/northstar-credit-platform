# Provenance and completion contract

This v6-07 contract keeps underwriting review honest about where material inputs
came from and whether a case is actually ready for analysis. It is separate from
wizard navigation: a case is never considered complete merely because it reached
step 7 of 7.

## Provenance

Every material input path is assigned exactly one source:

- `template-derived` — inherited from a selected synthetic template;
- `user-entered` — entered or changed by the analyst;
- `calculated` — produced by a deterministic model calculation;
- `imported` — loaded from an external file or system; or
- `override` — an explicit authorized override.

The backend returns counts and percentages for all five categories, the template
slug, warnings, and an inherited percentage. A template-backed case requires an
explicit acknowledgement when at least 75% of material fields remain
template-derived. The acknowledgement is persisted with the input and is checked
again before analysis. Provenance is included in the analysis result, memo
metadata, validation payload, and English/Traditional Chinese detailed PDFs.

## Completion

Completion is evidence-based and exposes three independent dimensions:

1. required fields completed;
2. business-risk evidence completed; and
3. optional sections completed.

`analysis_ready` is true only when all required fields and evidence are present, a
scorecard grade exists, and any required template acknowledgement is present. The
UI shows the counts and warnings on the Review page and does not render a step
percentage as a readiness claim. A missing required field, missing risk evidence,
or unacknowledged inherited template data remains a blocking warning.

## Invariants and tests

- The five source labels are closed and typed; unknown labels fail validation.
- Percentages are calculated from the material-field denominator and sum to 100%
  (subject to display rounding).
- Editing a material field marks that path `user-entered` without changing other
  paths.
- The clear-template action removes template provenance and requires fresh entry.
- Validation, analysis, memo, and PDF use the same provenance and completion
  objects.
- Unit, API/PDF integration, and Playwright Review-page tests cover the contract
  in English and Traditional Chinese.
