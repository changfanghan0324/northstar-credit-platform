# Final UX, localization, and accessibility audit

Baseline: `c867e001954749983d99db2e6e2aa903a69155a1` at `2026-08-06T16:11:27Z`.

## Rendered baseline evidence

- English and Traditional Chinese public routes loaded without framework overlay or console warning/error.
- All eight current workspace pages and seven wizard steps rendered.
- The workspace overview showed no document-level horizontal overflow at 1440, 1280, 1024, 768, 430, 390, or 360 CSS pixels.
- Mobile/tablet navigation controls rendered, and the existing drawer implementation includes initial focus, Tab wrapping, Escape close, and scroll locking.
- The current visual system remains the accepted navy/copper editorial design; this cycle should extend it rather than replace it.

## Gaps

| Area | Current state | Required outcome |
| --- | --- | --- |
| Guided mode | Mode label exists, but all material snapshot inputs remain visible | Essential-first flow with optional detail, plain status, fewer defaults, provenance, help, completion and autosave |
| Analyst mode | Adds small lineage text and a table | Full period statements, sticky headers, unit/currency controls, copy period, bulk paste, CSV template, overrides and validation |
| Navigation / IA | Eight pages; facility protection is absent | Add a dedicated facility-protection page without losing one-question-per-page clarity |
| Metric explanation | Some `<details>` explanations | Reusable status → metric → exact formula/source/policy detail and a glossary drawer |
| Tables and charts | Dense tables; no forecast charts | Default to at most two accessible primary charts; collapse detail in Guided mode; caption tables |
| Wizard | Seven steps work | Essential/Advanced groups, required count, completion, save status, source/unit/sign help, optional skip and grouped warnings |
| Localization | Route copy is bilingual; API-sourced values leak English | Localize statuses, policy labels/reasons, score factors, constraints, memo/PDF, errors, metadata and accessibility labels; add automated leak test |
| Accessibility evidence | Several semantics exist; no automated audit | Add skip link, consistent focus, fieldsets/legends, error summary and inline association, aria-live save/analyze state, chart alternatives, touch target/contrast/reduced-motion checks, axe and keyboard/screen-reader smoke evidence |
| Money entry | Custom parser silently maps empty to zero and transports as JS number | Preserve empty as missing, reject unsafe/scientific/overprecision values, show locale-safe validation, and transport exact decimal strings |
| Memo | HTML preview and two PDF buttons exist | One-page and 32-section localized memo with safe wrapping, page breaks, table clipping tests, model/policy/data dates and disclaimers |
| Component ownership | Two client components contain almost the entire workflow | Split by page/step and shared control responsibilities after behavior tests, keeping server/client boundaries deliberate |

Additional baseline defect: the wizard places `aria-live="polite"` around an entire changing panel, which can re-announce whole forms. Replace it with a narrow status live region.

## Proposed UX principle

Keep the accepted visual language and existing routes. Make complexity conditional: Guided mode should complete a valid synthetic analysis from essential fields, while Analyst mode exposes professional spreading and lineage. Do not add decorative redesign work until the new model and workflow are usable and testable.

Status: pending independent Claude Opus 5 High challenge.

## Final implementation verification

The accepted navy/copper design was preserved. The workspace now has nine
single-question pages, a mobile workflow dialog, Guided/Analyst mode, financial
period and adjustment editors, facility-protection analysis, two accessible stress
charts, solver details, glossary, and version/audit history. Traditional Chinese
routes localize navigation, status, decisions, scenarios, constraints, score
components, evidence, policy checks, errors, metadata, memo, PDF, 404, and dialog
labels; a rendered nine-page leak test rejects known English interface copy.

WCAG evidence includes axe WCAG 2.0/2.1/2.2 AA checks on public and professional
workspace surfaces, a keyboard skip-link check, focus-trapped Escape-close dialogs,
fieldset/legend form semantics, table captions, chart text alternatives, keyboard
focus for horizontally scrollable tables, reduced-motion CSS, and desktop/mobile
browser flows. The final browser smoke also records the production accessibility
tree and responsive screenshots. PDF/UA tagging remains an explicit limitation;
the web workspace is the primary accessible output.
