"""Application-level corporate-credit analysis built on the pure numeric engine."""

from .analysis import analyze_case
from .models import AnalysisResult, CaseInput

__all__ = ["AnalysisResult", "CaseInput", "analyze_case"]
