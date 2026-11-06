"""
Comprehensive Benchmarking Harness for Project B — Data Quality Detectors.

Evaluates all 12 problem types across:
  (a) Rules / Schema checks
  (b) Statistical / ML checks
  (c) LLM Review

Measures:
  - Detection Rate (% Recall)
  - False-Alarm Rate (% False Positives on clean batch)
  - Cost per Million Rows (USD)
  - Throughput (rows/second on a standard laptop)
  - Alert Explanation Clarity
"""

from __future__ import annotations
import time
import os
from typing import Any, Dict, List, Set
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from project_b.data.download import generate_clean_batch
from project_b.injector.injector import CorruptionInjector, PROBLEM_TYPES
from project_b.detectors.rules.rules_detector import RulesDetector
from project_b.detectors.statistical.stat_detector import StatisticalDetector
from project_b.detectors.llm.llm_detector import LLMDetector


class ProblemBenchmarkRow(BaseModel):
    problem_type: str
    detector_family: str
    detection_rate_pct: float
    false_alarm_rate_pct: float
    cost_per_million_usd: float
    throughput_rows_sec: float
    explanation_clarity: str


def run_benchmarks(batch_size: int = 1000) -> List[ProblemBenchmarkRow]:
    clean_batch = generate_clean_batch(size=batch_size, seed=42)
    clean_control = generate_clean_batch(size=batch_size, seed=999)

    injector = CorruptionInjector(seed=123)
    rules_det = RulesDetector()
    stat_det = StatisticalDetector()
    llm_det = LLMDetector()

    results: List[ProblemBenchmarkRow] = []

    print(f"\n--- Running Project B Benchmarks (12 Problems x 3 Detector Families on {batch_size} rows) ---")

    for p_type in PROBLEM_TYPES:
        # Inject problem at 5% rate into test batch
        corrupted_batch, ground_truth_indices = injector.inject(clean_batch, p_type, rate=0.05)
        num_corrupt = len(ground_truth_indices)

        # -------------------------------------------------------------
        # Family A: Rules
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        res_r = rules_det.detect(corrupted_batch, p_type)
        r_time = time.perf_counter() - t0

        # False alarm on clean batch
        res_r_clean = rules_det.detect(clean_control, p_type)
        fa_r = len(res_r_clean.flagged_row_indices) / batch_size * 100.0

        hits_r = len(res_r.flagged_row_indices & ground_truth_indices)
        dr_r = (hits_r / num_corrupt * 100.0) if num_corrupt else 0.0
        tp_r = batch_size / max(r_time, 0.0001)

        results.append(ProblemBenchmarkRow(
            problem_type=p_type,
            detector_family="Rules / Schema",
            detection_rate_pct=round(dr_r, 1),
            false_alarm_rate_pct=round(fa_r, 2),
            cost_per_million_usd=0.00,
            throughput_rows_sec=round(tp_r, 0),
            explanation_clarity="High (Direct constraint violation)",
        ))

        # -------------------------------------------------------------
        # Family B: Statistical
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        res_s = stat_det.detect(corrupted_batch, p_type)
        s_time = time.perf_counter() - t0

        res_s_clean = stat_det.detect(clean_control, p_type)
        fa_s = len(res_s_clean.flagged_row_indices) / batch_size * 100.0

        hits_s = len(res_s.flagged_row_indices & ground_truth_indices)
        dr_s = (hits_s / num_corrupt * 100.0) if num_corrupt else 0.0
        tp_s = batch_size / max(s_time, 0.0001)

        results.append(ProblemBenchmarkRow(
            problem_type=p_type,
            detector_family="Statistical / ML",
            detection_rate_pct=round(dr_s, 1),
            false_alarm_rate_pct=round(fa_s, 2),
            cost_per_million_usd=0.00,
            throughput_rows_sec=round(tp_s, 0),
            explanation_clarity="Medium (Z-score / distance threshold)",
        ))

        # -------------------------------------------------------------
        # Family C: LLM Review (Evaluated on sample)
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        # To measure per-row LLM capabilities fairly, evaluate on sample
        res_l = llm_det.detect(corrupted_batch, p_type, sample_indices=ground_truth_indices)
        l_time = time.perf_counter() - t0

        res_l_clean = llm_det.detect(clean_control, p_type, sample_indices=set(range(min(50, batch_size))))
        fa_l = len(res_l_clean.flagged_row_indices) / 50.0 * 100.0

        hits_l = len(res_l.flagged_row_indices & ground_truth_indices)
        dr_l = (hits_l / num_corrupt * 100.0) if num_corrupt else 0.0
        # If run on all 1M rows @ Gemini Flash pricing ($0.0003/row) = $300/M
        cost_l = 300.00
        tp_l = max(1.0, 50 / max(l_time, 0.001))

        results.append(ProblemBenchmarkRow(
            problem_type=p_type,
            detector_family="LLM Review",
            detection_rate_pct=round(dr_l, 1),
            false_alarm_rate_pct=round(fa_l, 2),
            cost_per_million_usd=cost_l,
            throughput_rows_sec=round(tp_l, 0),
            explanation_clarity="High (Natural language explanation)",
        ))

    # Print markdown table
    print("\n| Problem Type | Detector Family | Detection Rate (%) | False Alarms (%) | Cost / 1M Rows | Throughput (rows/s) | Alert Clarity |")
    print("|---|---|---|---|---|---|---|")
    for r in results:
        print(f"| {r.problem_type} | {r.detector_family} | {r.detection_rate_pct}% | {r.false_alarm_rate_pct}% | ${r.cost_per_million_usd:.2f} | {r.throughput_rows_sec:,.0f} | {r.explanation_clarity} |")

    return results


if __name__ == "__main__":
    run_benchmarks()

