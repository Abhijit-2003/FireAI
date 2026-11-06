"""
Hybrid Data Quality Pipeline — Task 5 of Project B.

Combines:
  Tier 1: Fast Declarative Rules on EVERY ROW ($0, ~0.05 ms/row)
  Tier 2: Statistical & Group Checks PER BATCH ($0, ~0.5 ms/row)
  Tier 3: Targeted LLM Semantic Review ONLY on flagged/candidate rows (~$0.0003/row)
"""

from __future__ import annotations
import time
from typing import Any, Dict, List, Set

from project_b.detectors.rules.rules_detector import RulesDetector
from project_b.detectors.statistical.stat_detector import StatisticalDetector
from project_b.detectors.llm.llm_detector import LLMDetector
from project_b.detectors.base import DetectorResult


class HybridPipeline:
    """
    Three-tier tiered data-quality pipeline.
    Minimizes latency and eliminates unnecessary LLM spend.
    """

    def __init__(self):
        self.rules_detector = RulesDetector()
        self.stat_detector = StatisticalDetector()
        self.llm_detector = LLMDetector()

    def run_pipeline(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs the full end-to-end hybrid pipeline on an incoming batch.
        """
        t0 = time.perf_counter()
        total_rows = len(batch)

        # -------------------------------------------------------------
        # TIER 1: CHEAP RULES ON EVERY ROW (Cost = $0.00)
        # -------------------------------------------------------------
        t1_start = time.perf_counter()
        tier1_flags: Dict[str, Set[int]] = {}
        tier1_all_flagged: Set[int] = set()

        rule_checks = [
            "renamed_dropped_col",
            "col_type_change",
            "date_format_switch",
            "lat_lng_swapped",
            "exact_duplicates",
            "closed_before_created",
            "zip_borough_mismatch",
            "pii_in_text",
        ]

        for p_type in rule_checks:
            res = self.rules_detector.detect(batch, p_type)
            if res.flagged_row_indices:
                tier1_flags[p_type] = res.flagged_row_indices
                tier1_all_flagged.update(res.flagged_row_indices)

        t1_duration_ms = (time.perf_counter() - t1_start) * 1000.0

        # -------------------------------------------------------------
        # TIER 2: STATISTICAL MONITORS PER BATCH (Cost = $0.00)
        # -------------------------------------------------------------
        t2_start = time.perf_counter()
        tier2_flags: Dict[str, Set[int]] = {}
        tier2_all_flagged: Set[int] = set()

        stat_checks = [
            "null_spike",
            "near_duplicates",
            "complaint_descriptor_mismatch",
        ]

        for p_type in stat_checks:
            res = self.stat_detector.detect(batch, p_type)
            if res.flagged_row_indices:
                tier2_flags[p_type] = res.flagged_row_indices
                tier2_all_flagged.update(res.flagged_row_indices)

        t2_duration_ms = (time.perf_counter() - t2_start) * 1000.0

        # -------------------------------------------------------------
        # TIER 3: LLM REVIEW (ONLY ON FLAGGED / SUSPICIOUS ROWS)
        # -------------------------------------------------------------
        t3_start = time.perf_counter()
        tier3_flags: Dict[str, Set[int]] = {}
        tier3_alerts: List[str] = []

        # Only pass candidates flagged by near_duplicates and complaint_descriptor to LLM
        semantic_candidates = (
            tier2_flags.get("near_duplicates", set()) |
            tier2_flags.get("complaint_descriptor_mismatch", set())
        )

        llm_calls_made = 0
        if semantic_candidates:
            # 1. Near-dupe confirmation
            if "near_duplicates" in tier2_flags:
                res_nd = self.llm_detector.detect(
                    batch, "near_duplicates", sample_indices=tier2_flags["near_duplicates"]
                )
                tier3_flags["confirmed_near_duplicates"] = res_nd.flagged_row_indices
                tier3_alerts.extend(res_nd.alert_messages)
                llm_calls_made += len(tier2_flags["near_duplicates"])

            # 2. Complaint-Descriptor semantic verification
            if "complaint_descriptor_mismatch" in tier2_flags:
                res_cd = self.llm_detector.detect(
                    batch, "complaint_descriptor_mismatch", sample_indices=tier2_flags["complaint_descriptor_mismatch"]
                )
                tier3_flags["confirmed_complaint_descriptor"] = res_cd.flagged_row_indices
                tier3_alerts.extend(res_cd.alert_messages)
                llm_calls_made += len(tier2_flags["complaint_descriptor_mismatch"])

        # Resolution vs Status contradiction: inspect sample or flagged rows
        # Check candidate rows that have complex text
        suspicious_status_candidates = {
            i for i, r in enumerate(batch)
            if "closed" in str(r.get("Status")).lower() and ("open" in str(r.get("Resolution Description")).lower() or "active" in str(r.get("Resolution Description")).lower() or "unresolved" in str(r.get("Resolution Description")).lower())
        }
        if suspicious_status_candidates:
            res_rs = self.llm_detector.detect(batch, "resolution_status_contradiction", sample_indices=suspicious_status_candidates)
            tier3_flags["confirmed_status_contradiction"] = res_rs.flagged_row_indices
            tier3_alerts.extend(res_rs.alert_messages)
            llm_calls_made += len(suspicious_status_candidates)

        t3_duration_ms = (time.perf_counter() - t3_start) * 1000.0
        total_time_ms = (time.perf_counter() - t0) * 1000.0

        # Cost calculation
        # Gemini 1.5 Flash: ~$0.000075 per 1K input tokens + $0.0003 per 1K output tokens -> ~$0.0003 per verification
        llm_cost_usd = llm_calls_made * 0.0003

        # Consolidate all flagged indices
        all_flagged: Set[int] = set(tier1_all_flagged)
        all_flagged.update(tier2_all_flagged)
        for s in tier3_flags.values():
            all_flagged.update(s)

        return {
            "total_rows_evaluated": total_rows,
            "total_flagged_rows": len(all_flagged),
            "flagged_indices": sorted(list(all_flagged)),
            "pipeline_timing_ms": {
                "tier1_rules_ms": round(t1_duration_ms, 3),
                "tier2_stats_ms": round(t2_duration_ms, 3),
                "tier3_llm_ms": round(t3_duration_ms, 3),
                "total_duration_ms": round(total_time_ms, 3),
            },
            "tier1_breakdown": {k: len(v) for k, v in tier1_flags.items()},
            "tier2_breakdown": {k: len(v) for k, v in tier2_flags.items()},
            "tier3_breakdown": {k: len(v) for k, v in tier3_flags.items()},
            "llm_calls_made": llm_calls_made,
            "llm_cost_usd": round(llm_cost_usd, 6),
            "cost_per_million_rows_usd": round((llm_cost_usd / max(total_rows, 1)) * 1_000_000, 2),
            "tier3_sample_alerts": tier3_alerts[:5],
        }

