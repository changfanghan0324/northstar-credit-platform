# Money scale contract

Status: v6-01 implementation contract
Owner: Northstar model and product layers
Canonical unit: actual minor currency units

## Contract

`MoneyValue.amount_minor` is the canonical amount at the currency's
`minor_unit_exponent`. For USD, `10_001` means exactly `$100.01`.

`FinancialPeriod.scale` is display/import metadata only. It is not another
money exponent and must never be multiplied by the Python resolver or by an
API consumer after the browser has normalized a value.

The browser and any import adapter normalize once at the boundary. The API
payload therefore contains actual minor units:

| Display scale | User enters | Canonical USD `amount_minor` |
| --- | ---: | ---: |
| `whole` | `100.00` | `10_000` |
| `thousands` | `100.00` | `10_000_000` |
| `millions` | `100.00` | `10_000_000_000` |

The resolver consumes that canonical value unchanged. It does not inspect
`FinancialPeriod.scale` when performing money arithmetic.

Changing a period's scale is presentation-only. The editor keeps the
canonical amount and re-renders it; it never parses the rendered string during
a scale change. Repeating whole → thousands → millions → whole therefore
leaves the amount bit-identical. An untouched cell is never re-parsed from its
display value merely because another control changed.

For USD, the accepted input precision is explicit:

| Display scale | Parser exponent | Maximum fractional digits |
| --- | ---: | ---: |
| `whole` | 2 | 2 |
| `thousands` | 5 | 5 |
| `millions` | 8 | 8 |

This is display precision required to preserve actual cents, not a change to
the stored USD exponent of 2. Values with a ninth fractional digit at millions
are rejected; no rounding or truncation is performed.

## Round-trip invariants

- Whole, thousands, and millions inputs preserve exact USD cents through
  edit, save, reload, resolve, analyze, and redisplay.
- Changing a period's display scale changes presentation only; it never
  changes the underlying `amount_minor`.
- Direct cell entry and Excel paste use the same scale-aware normalizer and
  produce the same canonical amount.
- Scientific notation, malformed grouping, excess precision, and values that
  exceed JavaScript's safe integer range are rejected before persistence.
- The normalized value is never normalized a second time downstream.
- Excel paste accepts the same standard decimal grammar as direct entry,
  including optional ASCII comma grouping; scientific notation, accounting
  parentheses, currency symbols, NBSP grouping, non-ASCII minus signs, and
  em-dash placeholders are rejected rather than guessed. This v6-01 contract
  is deliberately locale-explicit and loss-averse.

## Legacy data status

The v5 resolver release already treats `FinancialPeriod.scale` as metadata and
stores canonical minor units. Northstar's public Portfolio Demo Mode cases are
synthetic, anonymous, session-scoped, and temporary; there is no durable
pre-v6 customer dataset requiring a scale backfill. Any future durable import
must declare the canonical contract at ingestion and reject an unversioned
legacy payload rather than guessing its scale.

For a non-USD currency, the same rule applies using that currency's
`minor_unit_exponent`; the display-scale digits are added to the parser's
input precision, not to the stored money exponent.
