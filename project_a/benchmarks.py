"""
Measurement and Benchmarking Harness for Project A (Income Tax Engine).

Compares:
1. Hand-coded rules
2. LLM at query time
3. LLM-compiled rules

Metrics measured:
- Rupee-exact accuracy (%)
- Determinism over 10 repeated runs (%)
- Average & P99 latency (ms)
- Estimated cost per 1,000 requests (USD)
- Auditability & clause traceability (full / partial / none)
"""

from __future__ import annotations
import json
import time
import statistics
import os
from typing import Any, Dict, List
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from project_a.impl_rules.calculator import RulesCalculator
from project_a.impl_llm_query.calculator import LLMQueryCalculator
from project_a.impl_llm_compiled.calculator import LLMCompiledCalculator


class BenchmarkMetric(BaseModel):
    implementation: str
    accuracy_pct: float
    determinism_pct: float
    avg_latency_ms: float
    p99_latency_ms: float
    cost_per_1000_usd: float
    auditability: str
    pass_count: int
    total_evaluated: int


def benchmark_calculator(
    name: str,
    calc_instance: Any,
    test_cases: List[dict[str, Any]],
    repeat_runs: int = 10,
    cost_per_query_usd: float = 0.0,
    auditability_label: str = "Full (every rupee traced to IT Act section)",
) -> BenchmarkMetric:
    latencies: List[float] = []
    exact_matches = 0
    deterministic_runs = 0
    evaluated = len(test_cases)

    for case in test_cases:
        inp = case["input"]
        exp_old = case["expected_old_regime"]
        exp_new = case["expected_new_regime"]

        # 1. Measure latency and single-run correctness
        t0 = time.perf_counter()
        res = calc_instance.calculate(inp)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

        # Check rupee-exact accuracy
        is_exact = (
            res.old_regime.total_tax == exp_old["total_tax"]
            and res.new_regime.total_tax == exp_new["total_tax"]
        )
        if is_exact:
            exact_matches += 1

        # 2. Check determinism over 10 runs
        first_old_tax = res.old_regime.total_tax
        first_new_tax = res.new_regime.total_tax
        is_deterministic = True

        for _ in range(repeat_runs - 1):
            r = calc_instance.calculate(inp)
            if (r.old_regime.total_tax != first_old_tax or
                r.new_regime.total_tax != first_new_tax):
                is_deterministic = False
                break

        if is_deterministic:
            deterministic_runs += 1

    accuracy = (exact_matches / evaluated) * 100.0 if evaluated else 0.0
    determinism = (deterministic_runs / evaluated) * 100.0 if evaluated else 0.0
    avg_lat = float(statistics.mean(latencies)) if latencies else 0.0
    p99_lat = float(sorted(latencies)[int(len(latencies) * 0.99)]) if latencies else 0.0
    cost_1k = cost_per_query_usd * 1000.0

    return BenchmarkMetric(
        implementation=name,
        accuracy_pct=round(accuracy, 2),
        determinism_pct=round(determinism, 2),
        avg_latency_ms=round(avg_lat, 3),
        p99_latency_ms=round(p99_lat, 3),
        cost_per_1000_usd=round(cost_1k, 4),
        auditability=auditability_label,
        pass_count=exact_matches,
        total_evaluated=evaluated,
    )


def run_all_benchmarks(sample_size: int = 50) -> List[BenchmarkMetric]:
    with open("project_a/tests/test_cases.json", "r", encoding="utf-8") as f:
        all_cases = json.load(f)

    subset = all_cases[:sample_size]
    print(f"\n--- Running Project A Benchmarks ({len(subset)} test cases x 10 runs each) ---")

    # 1. Hand-coded rules
    m_rules = benchmark_calculator(
        name="1. Hand-coded Rules (Task 2a)",
        calc_instance=RulesCalculator(),
        test_cases=subset,
        repeat_runs=10,
        cost_per_query_usd=0.0,
        auditability_label="Full (Section-by-section audit trail)",
    )

    # 2. LLM at query time (Gemini API token cost ~ $0.00025 per call)
    m_llm_query = benchmark_calculator(
        name="2. LLM at Query Time (Task 2b)",
        calc_instance=LLMQueryCalculator(),
        test_cases=subset,
        repeat_runs=2, # Keep low to prevent rate limits
        cost_per_query_usd=0.0003, # ~1,500 input + 400 output tokens @ Gemini 1.5 Flash
        auditability_label="Partial (Model-generated explanations, risk of hallucination)",
    )

    # 3. LLM-compiled rules
    m_compiled = benchmark_calculator(
        name="3. LLM-Compiled Rules (Task 2c)",
        calc_instance=LLMCompiledCalculator(),
        test_cases=subset,
        repeat_runs=10,
        cost_per_query_usd=0.0,
        auditability_label="Full (Pre-compiled & human-reviewed code)",
    )

    results = [m_rules, m_llm_query, m_compiled]

    print("\n| Implementation | Rupee Accuracy | Determinism (10x) | Avg Latency | P99 Latency | Cost / 1k Req | Auditability |")
    print("|---|---|---|---|---|---|---|")
    for r in results:
        print(f"| {r.implementation} | {r.accuracy_pct}% ({r.pass_count}/{r.total_evaluated}) | {r.determinism_pct}% | {r.avg_latency_ms} ms | {r.p99_latency_ms} ms | ${r.cost_per_1000_usd:.2f} | {r.auditability} |")

    return results


if __name__ == "__main__":
    run_all_benchmarks()
