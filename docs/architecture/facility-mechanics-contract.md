# Facility mechanics contract

## Purpose

Northstar resolves one `ResolvedFacilityMechanics` object from the explicit
facility request. The resolved object is the canonical source for facility
type, amortization, commitment, initial drawn amount, maturity, availability,
pricing fees, mandatory prepayment, and security type.

## Resolution rules

- A term loan resolves to `fully_amortizing`, `partial`, or `bullet` mechanics
  from the request. A missing amortization type is inferred only from the
  presence of `amortization_years`; the resolved value is then retained.
- A revolver and an asset-based facility resolve to `revolver` mechanics.
- Asset-based facilities require asset-based security and revolver mechanics.
- Bullet and partial mechanics require a positive `bullet_percentage`.
- Revolver mechanics cannot carry a partial or bullet percentage.
- Any contradiction produces `status=blocked` with typed `blocking_issues`.

The conflict matrix is intentionally fail-closed: asset-based plus a
non-revolver amortization or non-asset-based security; term loan plus revolver
amortization; bullet/partial with a non-positive balloon; and revolver with a
partial balloon are blocked. Request-level validation separately blocks
missing amortization years for fully amortizing facilities, bullet schedules
that also declare scheduled amortization, and an initial draw above
commitment. An asset-based/revolver request with asset-based security and a
zero-or-one balloon is the supported near-miss control case.

## Consumers

The same object is passed, unchanged, to:

- borrowing-base and collateral capacity;
- leverage/DSCR capacity and the underwritten rate;
- pricing and commitment-fee calculations;
- facility protection;
- base, downside, severe, and reverse-stress forecasts;
- covenants and policy restrictions;
- the decision object;
- English memo sections, bilingual UI lineage, and English/Traditional
  Chinese PDF output.

No downstream consumer may re-infer `facility_type`, amortization, maturity,
or revolving behavior from the raw request. A blocked mechanics object blocks
capacity, pricing, facility protection, stress, and the final decision until
the contradiction is resolved.

`ResolvedFacilityMechanics` and its nested `MoneyValue` fields are frozen.
The architecture test asserts there is one constructor in the analysis module,
no raw-request facility/security inference in downstream analysis, and that
consumer mutation attempts fail.

## Evidence

`tests/unit/test_application_analysis.py` verifies canonical equality across
the decision, capacity, pricing, borrowing base, scenarios, reverse stress,
covenants, policy checks, facility protection, and memo, plus the conflict
matrix, immutable resolver object, and fail-closed behavior. API integration
tests assert English and Traditional Chinese PDF sections carry the same
canonical mechanics text as the analysis memo.
