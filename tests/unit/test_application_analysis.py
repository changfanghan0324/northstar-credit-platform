from __future__ import annotations

from decimal import Decimal

import pytest
from northstar_credit_app import analyze_case
from northstar_credit_app.demo import list_demo_cases, load_demo_case
from northstar_credit_app.models import DebtInstrumentInput
from northstar_policy import load_policy


def test_policy_is_versioned_and_weights_sum_to_100() -> None:
    policy, policy_hash = load_policy()
    assert policy.version == "1.0.0"
    assert len(policy_hash) == 64
    assert sum((item.weight for item in policy.weights), Decimal(0)) == Decimal(100)


def test_reference_case_calculates_golden_ratios_and_capacity() -> None:
    result = analyze_case(load_demo_case("stable-manufacturer"))

    assert result.metrics["gross_leverage"].value == "1.8293"
    assert result.metrics["dscr"].value == "1.7143"
    assert result.capacity.requested.amount_minor == 1_500_000_000
    assert result.capacity.recommended.amount_minor == 1_500_000_000
    assert result.capacity.binding_constraints == ["requested_amount"]
    assert result.decision.outcome == "Approve with conditions"


@pytest.mark.parametrize(
    ("slug", "outcome", "recommended_minor"),
    [
        ("stable-manufacturer", "Approve with conditions", 1_500_000_000),
        ("cyclical-distributor", "Decline", 0),
        ("software-services", "Reduce requested amount", 900_000_000),
    ],
)
def test_demo_profiles_are_computed_not_stored(
    slug: str, outcome: str, recommended_minor: int
) -> None:
    result = analyze_case(load_demo_case(slug))

    assert result.decision.outcome == outcome
    assert result.capacity.recommended.amount_minor == recommended_minor


def test_every_demo_has_three_three_year_scenarios_and_worsening_severe_case() -> None:
    for case in list_demo_cases():
        result = analyze_case(case)
        assert [scenario.name for scenario in result.scenarios] == [
            "base",
            "downside",
            "severe",
        ]
        assert all(len(scenario.years) == 3 for scenario in result.scenarios)
        base = result.scenarios[0].years[0]
        severe = result.scenarios[2].years[0]
        assert severe.revenue.amount_minor < base.revenue.amount_minor
        assert severe.adjusted_ebitda.amount_minor < base.adjusted_ebitda.amount_minor
        assert Decimal(severe.dscr) < Decimal(base.dscr)


def test_analysis_is_reproducible_when_timestamp_is_injected() -> None:
    case = load_demo_case("stable-manufacturer")
    first = analyze_case(case)
    second = analyze_case(case)

    assert first.input_hash == second.input_hash
    assert first.policy_hash == second.policy_hash
    assert first.metrics == second.metrics
    assert first.capacity == second.capacity
    assert first.scorecard == second.scorecard
    assert first.scenarios == second.scenarios
    assert first.decision == second.decision


def test_zero_capacity_has_adverse_decision_priority() -> None:
    result = analyze_case(load_demo_case("cyclical-distributor"))

    assert result.capacity.recommended.amount_minor == 0
    assert result.decision.outcome == "Decline"
    assert result.decision.decision_priority == "zero_supported_exposure"


def test_unsecured_facility_excludes_collateral_from_capacity() -> None:
    case = load_demo_case("software-services")
    request = case.request.model_copy(update={"security_type": "unsecured"})
    result = analyze_case(case.model_copy(update={"request": request}))

    collateral = next(
        item
        for item in result.capacity.constraints
        if item.key == "collateral_capacity"
    )
    assert collateral.applicable is False
    assert collateral.status == "policy_not_applicable"
    assert collateral.amount is None
    assert "collateral_capacity" not in result.capacity.binding_constraints


def test_all_active_policy_limits_are_reported() -> None:
    result = analyze_case(load_demo_case("stable-manufacturer"))

    assert {item.key for item in result.policy_checks} == {
        "maximum_leverage",
        "minimum_dscr",
        "minimum_interest_coverage",
        "maximum_maturity",
        "minimum_liquidity",
        "reporting_currency",
        "positive_capacity",
        "minimum_data_quality",
        "maximum_adjustment_magnitude",
        "grade_eligibility",
        "maximum_exposure",
        "minimum_collateral_coverage",
        "facility_restrictions",
    }


def test_roll_forward_exposes_debt_liquidity_and_refinancing_states() -> None:
    result = analyze_case(load_demo_case("stable-manufacturer"))
    first = result.scenarios[0].years[0]

    assert (
        first.beginning_debt.amount_minor + first.new_facility.amount_minor
        > first.ending_debt.amount_minor
    )
    assert first.average_debt.amount_minor <= (
        first.beginning_debt.amount_minor + first.new_facility.amount_minor
    )
    assert first.scheduled_amortization.amount_minor > 0
    assert first.cash_shortfall.amount_minor >= 0
    assert first.revolver_draw.amount_minor >= 0
    assert first.refinancing_need.amount_minor == 0


def test_reverse_stress_uses_bounded_solver_metadata() -> None:
    result = analyze_case(load_demo_case("stable-manufacturer"))

    assert result.reverse_stress.method == "bounded_bisection"
    assert result.reverse_stress.iterations <= 60
    assert Decimal(result.reverse_stress.lower_bound) <= Decimal(
        result.reverse_stress.upper_bound
    )
    assert "full forecast" in result.reverse_stress.interpretation


def test_dynamic_confidence_and_human_memo_money() -> None:
    result = analyze_case(load_demo_case("stable-manufacturer"))
    case = load_demo_case("stable-manufacturer")
    instrument = DebtInstrumentInput(
        name="Synthetic term debt",
        principal=case.financials.long_term_debt,
        annual_rate=Decimal("0.06"),
        scheduled_amortization=case.financials.scheduled_principal,
        maturity_year=3,
        schedule_completeness="partial",
    )
    documented = analyze_case(
        case.model_copy(update={"debt_instruments": [instrument]})
    )

    assert 0 <= result.scorecard.confidence_score <= 100
    assert documented.scorecard.confidence_score > result.scorecard.confidence_score
    assert result.scorecard.synthetic_notice == (
        "Synthetic demonstration — not a real data-quality assessment"
    )
    memo = " ".join(
        value for section in result.memo_sections.values() for value in section
    )
    assert "USD 15,000,000.00" in memo
    assert "minor units" not in memo


def test_currency_mismatch_is_rejected_before_analysis() -> None:
    case = load_demo_case("stable-manufacturer").model_dump(mode="python")
    case["financials"]["revenue"]["currency"] = "EUR"

    with pytest.raises(ValueError, match="currency mismatch"):
        type(load_demo_case("stable-manufacturer")).model_validate(case)

    debt_case = load_demo_case("stable-manufacturer").model_dump(mode="python")
    debt_case["debt_instruments"] = [
        {
            "name": "EUR debt",
            "principal": {
                "amount_minor": 1_000,
                "currency": "EUR",
                "minor_unit_exponent": 2,
            },
            "annual_rate": "0.06",
            "scheduled_amortization": {
                "amount_minor": 100,
                "currency": "EUR",
                "minor_unit_exponent": 2,
            },
            "maturity_year": 3,
            "schedule_completeness": "complete",
        }
    ]
    with pytest.raises(ValueError, match="currency mismatch"):
        type(load_demo_case("stable-manufacturer")).model_validate(debt_case)


@pytest.mark.parametrize("ebit_minor", [0, -500_000_000])
def test_zero_or_negative_ebitda_cannot_receive_favorable_leverage_score(
    ebit_minor: int,
) -> None:
    case = load_demo_case("stable-manufacturer")
    financials = case.financials.model_copy(
        update={
            "ebit": case.financials.ebit.model_copy(
                update={"amount_minor": ebit_minor}
            ),
            "depreciation_amortization": case.financials.depreciation_amortization.model_copy(
                update={"amount_minor": 0}
            ),
            "positive_ebitda_adjustments": case.financials.positive_ebitda_adjustments.model_copy(
                update={"amount_minor": 0}
            ),
            "negative_ebitda_adjustments": case.financials.negative_ebitda_adjustments.model_copy(
                update={"amount_minor": 0}
            ),
        }
    )
    result = analyze_case(case.model_copy(update={"financials": financials}))
    leverage = next(
        item for item in result.scorecard.components if item.key == "leverage"
    )

    assert result.metrics["gross_leverage"].status == "not_meaningful"
    assert leverage.status == "blocked"
    assert result.scorecard.grade is None
    assert result.decision.decision_priority == "critical_inputs_blocked"


def test_scenario_debt_identity_includes_new_facility_and_revolver() -> None:
    result = analyze_case(load_demo_case("stable-manufacturer"))

    for scenario in result.scenarios:
        for year in scenario.years:
            expected = (
                year.beginning_debt.amount_minor
                + year.new_facility.amount_minor
                + year.revolver_draw.amount_minor
                - year.scheduled_amortization.amount_minor
                - year.optional_paydown.amount_minor
            )
            assert year.ending_debt.amount_minor == expected


def test_covenant_package_responds_to_risk_and_facility_structure() -> None:
    weak = analyze_case(load_demo_case("cyclical-distributor"))
    assert {item.name for item in weak.covenants} >= {
        "Maximum total leverage",
        "Minimum DSCR",
        "Quarterly financial reporting",
        "Restricted distributions",
        "Capital expenditure control",
    }

    case = load_demo_case("stable-manufacturer")
    request = case.request.model_copy(
        update={"facility_type": "asset_based", "security_type": "asset_based"}
    )
    asset_based = analyze_case(case.model_copy(update={"request": request}))
    assert {item.name for item in asset_based.covenants} >= {
        "Borrowing-base availability",
        "Collateral reporting",
    }
