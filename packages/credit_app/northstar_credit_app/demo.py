"""Load synthetic input-only demo cases with optional inheritance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CaseInput

DEMO_ROOT = Path(__file__).resolve().parents[3] / "data" / "demo_cases"


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_demo_case(slug: str) -> CaseInput:
    path = DEMO_ROOT / f"{slug}.json"
    if not path.is_file():
        raise KeyError(slug)
    payload: dict[str, Any] = json.loads(path.read_text())
    parent = payload.pop("extends", None)
    if parent is not None:
        parent_payload = load_demo_case(str(parent)).model_dump(mode="json")
        payload = _merge(parent_payload, payload)
    business_risk = payload["business_risk"]
    factor_evidence: dict[str, Any] = {}
    for key in (
        "industry",
        "competitive_position",
        "customer_concentration",
        "diversification",
        "management_policy",
        "governance_event",
    ):
        score = int(business_risk[key])
        band = (
            "strong"
            if score >= 80
            else "adequate"
            if score >= 65
            else "moderate_concern"
            if score >= 50
            else "weak"
            if score >= 35
            else "severe_concern"
        )
        factor_evidence[key] = {
            "score": score,
            "band": band,
            "evidence": f"Synthetic template evidence for {key.replace('_', ' ')}; no external borrower fact is asserted.",
            "source": f"synthetic-template/{slug}",
            "analyst_rationale": "Illustrative policy mapping for the educational demo case.",
            "confidence": "medium",
            "override_status": "none",
            "reviewer_status": "reviewed",
            "last_updated": f"{payload['data_as_of']}T00:00:00Z",
        }
    business_risk["factor_evidence"] = factor_evidence
    return CaseInput.model_validate(payload)


def list_demo_cases() -> list[CaseInput]:
    return [
        load_demo_case(slug)
        for slug in ("stable-manufacturer", "cyclical-distributor", "software-services")
    ]
