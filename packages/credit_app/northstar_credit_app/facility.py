"""Independent facility protection, collateral, and educational pricing engines."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from northstar_policy import CreditPolicy

from .models import (
    BorrowingBaseView,
    CaseInput,
    FacilityProtectionView,
    MoneyValue,
    PricingView,
    ScorecardView,
)


def _money(value: int, template: MoneyValue) -> MoneyValue:
    return MoneyValue(
        amount_minor=value,
        currency=template.currency,
        minor_unit_exponent=template.minor_unit_exponent,
    )


def calculate_borrowing_base(
    case: CaseInput, policy: CreditPolicy
) -> BorrowingBaseView:
    template = case.request.amount
    if case.request.facility_type != "asset_based":
        return BorrowingBaseView(
            applicable=False,
            status="not_applicable",
            gross_collateral=None,
            eligibility_reductions=None,
            eligible_receivables=None,
            receivables_availability=None,
            eligible_inventory=None,
            inventory_availability=None,
            other_eligible_collateral=None,
            reserves=None,
            prior_liens=None,
            borrowing_base=None,
            availability=None,
            excess_or_deficiency=None,
            binding_constraint="not_applicable",
            policy_notice="Illustrative borrowing-base policy; not applicable to this facility type.",
        )
    inputs = case.borrowing_base
    if inputs is None:
        return BorrowingBaseView(
            applicable=True,
            status="blocked",
            gross_collateral=None,
            eligibility_reductions=None,
            eligible_receivables=None,
            receivables_availability=None,
            eligible_inventory=None,
            inventory_availability=None,
            other_eligible_collateral=None,
            reserves=None,
            prior_liens=None,
            borrowing_base=None,
            availability=None,
            excess_or_deficiency=None,
            binding_constraint="missing_borrowing_base_inputs",
            policy_notice="Asset-based capacity is blocked until collateral eligibility inputs are supplied.",
        )

    ar = inputs.accounts_receivable
    inventory = inputs.inventory
    ar_reductions = sum(
        value.amount_minor
        for value in (
            ar.ineligible_receivables,
            ar.past_due_receivables,
            ar.cross_aged_receivables,
            ar.foreign_receivables,
            ar.concentration_reserve,
            ar.dilution_reserve,
        )
    )
    eligible_ar = max(0, ar.gross_receivables.amount_minor - ar_reductions)
    ar_rate = min(ar.advance_rate, policy.maximum_ar_advance_rate)
    ar_availability = int(
        (Decimal(eligible_ar) * ar_rate).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    )
    inventory_reductions = (
        inventory.ineligible_inventory.amount_minor
        + inventory.obsolete_inventory.amount_minor
    )
    eligible_inventory = max(
        0, inventory.gross_inventory.amount_minor - inventory_reductions
    )
    inventory_rate = min(inventory.advance_rate, policy.maximum_inventory_advance_rate)
    inventory_availability = min(
        inventory.inventory_cap.amount_minor,
        int(
            (Decimal(eligible_inventory) * inventory_rate).quantize(
                Decimal(1), rounding=ROUND_HALF_UP
            )
        ),
    )
    other = inputs.other_collateral
    other_eligible = sum(
        value.amount_minor
        for value in (other.equipment, other.real_estate, other.cash, other.other)
    )
    reserves = inputs.additional_reserves.amount_minor
    prior_liens = inputs.prior_liens.amount_minor
    final_base = max(
        0,
        ar_availability
        + inventory_availability
        + other_eligible
        - reserves
        - prior_liens,
    )
    gross = (
        ar.gross_receivables.amount_minor
        + inventory.gross_inventory.amount_minor
        + other_eligible
    )
    reductions = ar_reductions + inventory_reductions
    excess = final_base - case.request.amount.amount_minor
    return BorrowingBaseView(
        applicable=True,
        status="calculated",
        gross_collateral=_money(gross, template),
        eligibility_reductions=_money(reductions, template),
        eligible_receivables=_money(eligible_ar, template),
        receivables_availability=_money(ar_availability, template),
        eligible_inventory=_money(eligible_inventory, template),
        inventory_availability=_money(inventory_availability, template),
        other_eligible_collateral=_money(other_eligible, template),
        reserves=_money(reserves, template),
        prior_liens=_money(prior_liens, template),
        borrowing_base=_money(final_base, template),
        availability=_money(final_base, template),
        excess_or_deficiency=_money(excess, template),
        binding_constraint=(
            "borrowing_base"
            if final_base < case.request.amount.amount_minor
            else "requested_amount"
        ),
        policy_notice="Illustrative policy advance rates; not a lending commitment.",
    )


def assess_facility(
    case: CaseInput,
    policy: CreditPolicy,
    borrowing_base: BorrowingBaseView,
) -> FacilityProtectionView:
    request_minor = max(1, case.request.amount.amount_minor)
    collateral_minor = (
        borrowing_base.borrowing_base.amount_minor
        if borrowing_base.borrowing_base is not None
        else case.financials.collateral_capacity.amount_minor
        if case.request.security_type != "unsecured"
        else 0
    )
    coverage = Decimal(collateral_minor) / Decimal(request_minor)
    factors = {
        "seniority": Decimal(90),
        "collateral": min(Decimal(100), coverage * Decimal(80)),
        "guarantee": Decimal(75)
        if case.request.guarantee.lower() != "none"
        else Decimal(40),
        "amortization": Decimal(85)
        if (case.request.amortization_years or case.request.maturity_years)
        < case.request.maturity_years
        else Decimal(55),
        "maturity": Decimal(90)
        if case.request.maturity_years <= 3
        else Decimal(70)
        if case.request.maturity_years <= 5
        else Decimal(40),
        "covenants": Decimal(75),
        "reporting": Decimal(70),
        "purpose_alignment": Decimal(75)
        if case.request.purpose.strip()
        else Decimal(30),
    }
    score = sum(
        (
            factors[key] * policy.facility_protection_weights[key] / Decimal(100)
            for key in factors
        ),
        Decimal(0),
    )
    category = (
        "strong"
        if score >= 80
        else "adequate"
        if score >= 65
        else "moderate"
        if score >= 50
        else "weak"
        if score >= 35
        else "severe"
    )
    recovery = (
        "high"
        if coverage >= Decimal("1.25")
        else "moderate"
        if coverage >= Decimal("0.8")
        else "limited"
        if coverage > 0
        else "low"
    )
    protections = ["Senior claim", "Quarterly covenant testing", "Financial reporting"]
    weaknesses: list[str] = []
    improvements: list[str] = []
    if case.request.security_type == "unsecured":
        weaknesses.append("No collateral support")
        improvements.append("Maintain tighter leverage and liquidity covenants")
    else:
        protections.append("Collateral security package")
    if case.request.amortization_years is None:
        weaknesses.append("Bullet-style repayment concentration")
        improvements.append("Add scheduled amortization")
    if coverage < Decimal(1):
        weaknesses.append("Collateral coverage below requested exposure")
        improvements.append("Reduce exposure or add eligible collateral")
    return FacilityProtectionView(
        score=str(score.quantize(Decimal("0.01"))),
        category=category,  # type: ignore[arg-type]
        expected_recovery_category=recovery,  # type: ignore[arg-type]
        factors={
            key: str(value.quantize(Decimal("0.01"))) for key, value in factors.items()
        },
        main_protections=protections,
        main_structural_weaknesses=weaknesses
        or ["No material structural weakness identified in the synthetic inputs"],
        required_improvements=improvements
        or ["Maintain proposed structure and reporting"],
        documentation_requirements=[
            "Executed credit agreement",
            "Evidence of priority and perfection where secured",
            "Quarterly compliance certificate",
            "Annual financial statements",
        ],
    )


def calculate_pricing(
    case: CaseInput, policy: CreditPolicy, scorecard: ScorecardView
) -> PricingView:
    grade = scorecard.grade or 10
    grade_spread = policy.pricing_grade_spreads_bps[grade]
    tenor_key = (
        "short"
        if case.request.maturity_years <= 3
        else "medium"
        if case.request.maturity_years <= 5
        else "long"
    )
    tenor = policy.pricing_tenor_adjustments_bps[tenor_key]
    security = policy.pricing_security_adjustments_bps[case.request.security_type]
    amortization_key = (
        "amortizing" if case.request.amortization_years is not None else "bullet"
    )
    amortization = policy.pricing_amortization_adjustments_bps[amortization_key]
    covenant = policy.pricing_covenant_adjustment_bps if grade >= 6 else 0
    concentration = (
        policy.pricing_concentration_adjustment_bps
        if case.business_risk.customer_concentration < Decimal(60)
        else 0
    )
    relationship = case.pricing.relationship_adjustment_bps
    total_bps = (
        grade_spread
        + tenor
        + security
        + amortization
        + covenant
        + concentration
        + relationship
    )
    all_in = case.pricing.reference_base_rate + Decimal(total_bps) / Decimal(10000)
    return PricingView(
        reference_base_rate=str(
            case.pricing.reference_base_rate.quantize(Decimal("0.0001"))
        ),
        risk_grade_spread_bps=grade_spread,
        tenor_adjustment_bps=tenor,
        security_adjustment_bps=security,
        amortization_adjustment_bps=amortization,
        covenant_adjustment_bps=covenant,
        concentration_adjustment_bps=concentration,
        relationship_adjustment_bps=relationship,
        indicative_all_in_rate=str(all_in.quantize(Decimal("0.0001"))),
        commitment_fee_bps=(
            policy.pricing_commitment_fee_bps
            if case.request.facility_type in {"revolver", "asset_based"}
            else None
        ),
        upfront_fee_bps=(
            policy.pricing_upfront_fee_bps if case.pricing.include_upfront_fee else None
        ),
        disclaimer="Educational indicative pricing only. This is not a live market quote, bank commitment, or lending recommendation.",
    )
