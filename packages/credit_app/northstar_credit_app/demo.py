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
    return CaseInput.model_validate(payload)


def list_demo_cases() -> list[CaseInput]:
    return [
        load_demo_case(slug)
        for slug in ("stable-manufacturer", "cyclical-distributor", "software-services")
    ]
