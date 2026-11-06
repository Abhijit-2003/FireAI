"""
Base classes and result models for Project B detectors.
"""

from __future__ import annotations
from pydantic import BaseModel
from typing import Any, Dict, List, Set


class DetectorResult(BaseModel):
    """Result returned by any data-quality detector."""
    detector_name: str
    detector_family: str       # "rules" | "statistical" | "llm"
    problem_type: str
    flagged_row_indices: Set[int]
    total_rows_evaluated: int
    execution_time_ms: float
    explanation_clarity: str   # "high" | "medium" | "low"
    alert_messages: List[str]  # Human-readable explanations for CFO/team

