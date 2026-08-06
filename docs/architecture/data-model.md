# Data Model

## Portfolio Demo persistence boundary

Northstar operates in Portfolio Demo Mode. The runtime persistence model deliberately
uses a case aggregate rather than presenting the public product as a durable bank
system:

- `credit_cases` stores the current validated `CaseInput`, latest `AnalysisResult`,
  workflow state, anonymous session owner hash, archive state, version, and expiry.
- `case_versions` stores one immutable JSON snapshot for every visible case version.
  Revision `0003` enforces uniqueness on `(case_id, case_version)`.
- `case_audit_logs` stores append-only workflow events, including create, update,
  analyze, duplicate, archive/restore, version restore, and delete intent.

Migration `0002` also created reserved normalized projection tables. They are not
runtime sources of truth in Mode A and the application does not claim that they are
populated. They remain a documented migration path for a future durable product;
introducing that mode requires authentication, ownership, durable PostgreSQL,
retention controls, monitoring, and a separate product decision.

Mode A uses ORM `create_all` as its sole runtime schema owner. Alembic migrations are
kept as reviewed durable-mode lineage and must not be applied after Mode A has already
created a fresh schema. A future durable deployment must run migrations on an empty
or preflighted database before app traffic, and revision `0003` requires that legacy
`(case_id, case_version)` pairs contain no duplicates.

## Case aggregate

`CaseInput` includes:

- borrower and proposed facility;
- legacy essential financial snapshot used by the deterministic engine;
- structured multi-period financial spread (historical fiscal years, quarters, YTD,
  reported LTM, and three forecast years);
- income statement, balance sheet, and cash-flow statements per period, with source,
  currency, scale, audit state, and dates;
- normalization-adjustment log with evidence, rationale, review, timestamps, and
  EBITDA/EBIT/CFADS impacts;
- instrument-level debt schedule;
- six business-risk evidence records;
- optional asset-based borrowing-base inputs;
- pricing inputs and three scenario assumption sets.

`AnalysisResult` stores deterministic, versioned outputs for ratio states, financial
spreading and LTM status, adjustment bridge, capacity constraints, independent
facility protection, borrowing base, indicative pricing, scorecard, three-year
scenarios, covenants, all policy checks, six solver records, decision, and the
32-section memo source.

## Integrity and safety rules

- Critical missing or invalid inputs block the grade and final analysis.
- Financial quarters cannot overlap; source references and period dates are required.
- Balance-sheet reconciliation differences and incompatible LTM periods remain
  visible and block the selected LTM method.
- Approved adjustments require supporting evidence and analyst rationale.
- Every qualitative factor requires an evidence statement before a final grade.
- Asset-based capacity uses the calculated borrowing base; unsecured facilities mark
  it not applicable.
- Facility protection never changes the obligor grade.
- Solver results are omitted when the configured bounds do not converge.
- Monetary values are integer minor units within `±9,007,199,254,740,991`; currency
  codes are uppercase ISO-style three-letter values and exponent is limited to 0-6.
- Every case update creates a new version snapshot and audit event; restore creates a
  new version rather than mutating history.

## Result provenance

Every analysis includes `input_hash`, `engine_version`, `policy_version`,
`policy_hash`, `calculated_at`, `data_as_of`, ratio reason codes, policy references,
solver bounds/tolerance/iterations/residual, and the current Portfolio Demo runtime
disclosure. PDFs are generated only from the persisted analysis payload.
