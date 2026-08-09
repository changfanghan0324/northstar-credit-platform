# Revolver and ABL mechanics contract

## Purpose

Revolver and asset-based revolving facilities expose one typed liquidity view.
The view keeps contractual commitment, drawn amount, undrawn commitment,
borrowing base, availability, commitment fee, and cash interest distinct.

## Rules

- A committed revolver has `availability = commitment - drawn amount`.
- An ABL has `availability = min(commitment, borrowing base) - drawn amount`.
- Availability is clamped at zero; a missing ABL borrowing base blocks
  availability and capacity rather than treating undrawn commitment as
  liquidity.
- Commitment fee is calculated from undrawn commitment and the resolved fee
  basis. Cash interest is calculated from drawn amount and the single resolved
  `RateDecision` underwritten rate.
- Borrowing-base eligibility remains decomposed into receivables, inventory,
  other collateral, reserves, and prior liens. It is not replaced by a single
  collateral headline.

## Evidence

`RevolverAblView` is returned in every analysis and is rendered in the facility
protection workspace and both memo locales. Unit tests cover policy-capped ABL
availability, commitment-limited revolver availability, fee and cash-interest
amounts, missing-input blocking, and capacity linkage. API integration tests
assert the contract and its English/Traditional Chinese PDF evidence.
