"""
Integration tests for Hybrid Data Quality Pipeline (Project B Task 5).
"""

import pytest
from project_b.data.download import generate_clean_batch
from project_b.injector.injector import CorruptionInjector
from project_b.hybrid_pipeline import HybridPipeline


def test_hybrid_pipeline_end_to_end():
    batch = generate_clean_batch(size=500, seed=12)
    inj = CorruptionInjector(seed=99)

    # Inject a realistic cocktail of errors
    batch, aff_lat = inj.inject(batch, "lat_lng_swapped", rate=0.02)
    batch, aff_cl = inj.inject(batch, "closed_before_created", rate=0.02)
    batch, aff_pii = inj.inject(batch, "pii_in_text", rate=0.02)
    batch, aff_rs = inj.inject(batch, "resolution_status_contradiction", rate=0.02)

    pipeline = HybridPipeline()
    result = pipeline.run_pipeline(batch)

    assert result["total_rows_evaluated"] == 500
    assert result["total_flagged_rows"] > 0
    # Tier 1, 2, and 3 should all have executed
    assert result["pipeline_timing_ms"]["tier1_rules_ms"] > 0
    assert result["pipeline_timing_ms"]["total_duration_ms"] > 0
    assert result["cost_per_million_rows_usd"] < 250.0  # Much cheaper than full LLM ($300-$600/M)
