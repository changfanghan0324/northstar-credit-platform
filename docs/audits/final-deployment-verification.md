# Final deployment verification

Date: 2026-08-06  
Production: <https://northstar-credit-platform.vercel.app>  
Vercel deployment: `dpl_32Cs6Ua26prafDw82ZvAFmanY3Ej` (`READY`)  
Release application commit: `0bb216e`

## Release gates

| Gate | Result |
| --- | --- |
| Python unit/integration tests | 98 passed |
| Branch-aware application/API coverage | 96.07% |
| Ruff, Ruff format, strict Mypy | Passed |
| Strict TypeScript, ESLint, Next.js production build | Passed |
| Playwright desktop/mobile and axe | 8 passed |
| Independent Claude Opus 5 High review | `PROCEED WITH DEPLOYMENT` |
| Vercel production build | `READY` |

## Public smoke tests

- English and Traditional Chinese entry routes render from the public alias.
- `/health` returns the Northstar API health document.
- `/runtime` reports `portfolio_demo`, temporary session persistence, seven-day
  retention, and the documented quotas.
- All three synthetic demo profiles are returned, and the stable manufacturer opens
  as an analyzed versioned case.
- The Traditional Chinese detailed memo downloads as a valid four-page PDF with
  embedded Noto Sans TC and `ToUnicode` data.
- In-app browser accessibility snapshots expose semantic landmarks, headings, tables,
  all nine workflow links, Guided/Analyst controls, glossary, and version/audit history.
- A 1440 by 1000 production viewport has no horizontal document overflow. The final
  Playwright suite separately covers desktop and mobile Chromium, including the mobile
  drawer/dialog and localized route behavior.

## Product-mode boundary

This is Mode A: a public synthetic portfolio demonstration, not a production banking
system. Anonymous session data is temporary and may disappear earlier after a service
restart. The limitation is visible in the UI and machine-readable at `/runtime`.
