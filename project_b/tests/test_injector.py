"""
Unit tests for CorruptionInjector (Project B Task 2).
"""

import pytest
from project_b.data.download import generate_clean_batch
from project_b.injector.injector import CorruptionInjector, PROBLEM_TYPES


@pytest.fixture
def clean_batch():
    return generate_clean_batch(size=200, seed=42)


class TestCorruptionInjector:
    @pytest.mark.parametrize("p_type", PROBLEM_TYPES)
    def test_inject_all_12_types(self, clean_batch, p_type):
        injector = CorruptionInjector(seed=10)
        corrupted, affected = injector.inject(clean_batch, p_type, rate=0.05)

        assert len(corrupted) == len(clean_batch)
        assert len(affected) > 0
        assert all(isinstance(idx, int) for idx in affected)
        assert all(0 <= idx < len(clean_batch) for idx in affected)

