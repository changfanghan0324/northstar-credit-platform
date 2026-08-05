from __future__ import annotations

from decimal import Decimal

import pytest
from northstar_credit_app import analyze_case
from northstar_credit_app.demo import list_demo_cases, load_demo_case
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
        ("cyclical-distributor", "Refer to credit committee", 0),
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
