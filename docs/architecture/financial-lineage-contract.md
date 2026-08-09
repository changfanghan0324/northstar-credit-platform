# Financial lineage contract

Status: v6-02 implementation contract

## FY + current YTD − prior comparable YTD

The resolver selects a named tuple, not positional rows:

```text
FiscalYear, CurrentYTD, PriorComparableYTD
```

Flow lines use:

```text
FY + CurrentYTD - PriorComparableYTD
```

Point-in-time balance-sheet lines use `CurrentYTD` only. The immutable
snapshot therefore records both `flow_source_period_ids` and
`balance_sheet_source_period_id`; its `period_end` is the current YTD ending
date. The resolver does not use `selected[-1]` as a generic source rule for
this tuple.

The prior YTD must be a strict subset of the named FY, share the FY start cut,
and match the current YTD's fiscal start and period-end month/day. Duration by
itself is not a comparability test. Missing or degenerate windows block the
bridge; they never subtract an implicit zero or fall back to a stale snapshot.
The snapshot publishes the three source IDs and their period-end dates so a
reviewer can verify the window without reconstructing it from array order.

## Source authority

Every canonical financial field in the snapshot has one authority:

- `period_spread` — supplied by the selected period(s);
- `debt_schedule` — supplied by a reconciled instrument schedule;
- `facility_request` — supplied by the facility request;
- `manual_legacy_snapshot` — explicitly retained legacy input;
- `calculated` — derived from other canonical fields;
- `defaulted` — an explicit policy/default value;
- `blocked` — no trustworthy source is available for the affected metric.

Missing decision-critical lines are never silently presented as period-sourced.
For v6-02, scheduled principal remains `blocked` until the v6-03 debt
reconciliation layer can declare a debt-schedule authority. Affected
decisioning must carry that source state forward.

Blocked authority propagates to dependent decision outputs: DSCR is blocked,
capacity is zero/non-approvable, forecast DSCR covenants are blocked, and
reverse stress is not reported as converged. A blocked field is never coerced
to zero for ratio math. Authority precedence is explicit: current period
spread, reconciled debt schedule, and facility request sources take precedence
over a manual legacy snapshot; legacy inheritance is displayed as a warning
and cannot overwrite a current spread line.

The same resolved snapshot is passed to leverage, liquidity, capacity, stress,
memo, PDF, API, and both Guided and Analyst displays. Analyst Mode exposes the
field-level authority map; Guided Mode shows a concise source-quality state.
