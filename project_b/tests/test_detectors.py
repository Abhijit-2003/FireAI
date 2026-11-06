"""
Unit tests for all 3 detector families (Project B Task 3).
"""

import pytest
from project_b.data.download import generate_clean_batch
from project_b.injector.injector import CorruptionInjector
from project_b.detectors.rules.rules_detector import RulesDetector
from project_b.detectors.statistical.stat_detector import StatisticalDetector
from project_b.detectors.llm.llm_detector import LLMDetector


@pytest.fixture
def clean_batch():
    return generate_clean_batch(size=300, seed=77)


class TestDetectors:
    def test_rules_catches_schema_drop(self, clean_batch):
        inj = CorruptionInjector()
        corrupted, affected = inj.inject(clean_batch, "renamed_dropped_col")
        det = RulesDetector()
        res = det.detect(corrupted, "renamed_dropped_col")
        assert len(res.flagged_row_indices) > 0

    def test_rules_catches_closed_before_created(self, clean_batch):
        inj = CorruptionInjector()
        corrupted, affected = inj.inject(clean_batch, "closed_before_created", rate=0.05)
        det = RulesDetector()
        res = det.detect(corrupted, "closed_before_created")
        assert affected.issubset(res.flagged_row_indices)

    def test_rules_catches_lat_lng_swap(self, clean_batch):
        inj = CorruptionInjector()
        corrupted, affected = inj.inject(clean_batch, "lat_lng_swapped", rate=0.05)
        det = RulesDetector()
        res = det.detect(corrupted, "lat_lng_swapped")
        assert affected.issubset(res.flagged_row_indices)

    def test_rules_catches_pii(self, clean_batch):
        inj = CorruptionInjector()
        corrupted, affected = inj.inject(clean_batch, "pii_in_text", rate=0.05)
        det = RulesDetector()
        res = det.detect(corrupted, "pii_in_text")
        assert len(res.flagged_row_indices & affected) > 0

    def test_stat_catches_null_spike(self, clean_batch):
        inj = CorruptionInjector()
        corrupted, affected = inj.inject(clean_batch, "null_spike", rate=0.10)
        det = StatisticalDetector()
        res = det.detect(corrupted, "null_spike")
        assert len(res.flagged_row_indices) > 0

    def test_llm_catches_status_contradiction(self, clean_batch):
        inj = CorruptionInjector()
        corrupted, affected = inj.inject(clean_batch, "resolution_status_contradiction", rate=0.05)
        det = LLMDetector()
        res = det.detect(corrupted, "resolution_status_contradiction", sample_indices=affected)
        assert len(res.flagged_row_indices & affected) > 0

