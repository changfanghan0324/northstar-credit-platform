# Browser and responsive QA — v3 closeout

Date: 2026-08-05

## Automated local browser matrix

The final application was exercised through the browser at 390×844, 768×900, 1024×900, and 1440×900. Fourteen routes were checked at every size (56 route-size checks):

- Home, cases, new-case wizard, methodology, technical validation, and about
- Overview, inputs, financials, capacity, risk, stress, decision, and memo workspace sections

Result: 56/56 routes rendered with a document title and no horizontal document overflow.

## Interaction checks

- English and Traditional Chinese home pages load all three computed demonstrations.
- Opening a sample creates exactly one session-owned case and shows the computed result.
- The seven-step custom wizard exposes borrower, structure, financial, debt-instrument, qualitative-risk, scenario, and review steps.
- The review step calls server-side validation before case creation and reports validation status and estimated confidence.
- A custom case was created, analyzed, and opened successfully.
- Guided and Analyst modes use the same result values.
- The mobile workflow drawer opens, traps keyboard focus, closes, and exposes all eight sections.
- Traditional Chinese pages emit `lang="zh-Hant-TW"`; English pages emit English metadata.
- Detailed Traditional Chinese PDF export completed without a visible error.
- The methodology page contains twenty bilingual topics.

## Visual review

The final desktop and mobile screens were compared with the approved Northstar concept: navy decision hierarchy, copper accents, serif decision typography, compact evidence tables, visible workflow navigation, and clear Guided/Analyst control were retained. The implementation adapts that system to responsive web behavior instead of reproducing a fixed mockup.

## Expected protection behavior

After the intentionally dense local route matrix, the anonymous request-rate guard returned its localized recoverable error. This confirms the limit is enforced; lifecycle behavior is also covered by integration tests without waiting for the time window to reset.
