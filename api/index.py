"""Vercel entry point for the Northstar FastAPI application."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for source in (
    ROOT / "packages" / "credit_engine",
    ROOT / "packages" / "credit_app",
    ROOT / "packages" / "policy",
    ROOT / "apps" / "api",
):
    sys.path.insert(0, str(source))

from northstar_api.main import app  # noqa: E402

__all__ = ["app"]
