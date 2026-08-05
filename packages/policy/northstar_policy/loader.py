"""Load and hash a Northstar policy file."""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from .models import CreditPolicy


def load_policy(path: Path | None = None) -> tuple[CreditPolicy, str]:
    policy_path = path or Path(__file__).resolve().parent.parent / "policy.v1.yaml"
    raw = policy_path.read_bytes()
    payload = yaml.safe_load(raw)
    return CreditPolicy.model_validate(payload), hashlib.sha256(raw).hexdigest()
