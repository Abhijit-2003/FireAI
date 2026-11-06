"""
Unit and integration tests for LLM-Compiled Rules implementation.
"""

import json
import pytest
from project_a.impl_llm_compiled.calculator import LLMCompiledCalculator
from project_a.impl_rules.calculator import RulesCalculator


def _load_cases():
    with open("project_a/tests/test_cases.json", "r", encoding="utf-8") as f:
        return json.load(f)


CASES = _load_cases()


class TestLLMCompiledCalculator:
    """Validate that LLM-compiled rules produce rupee-exact identical results to hand-coded rules."""

    @pytest.mark.parametrize("case", CASES[:50], ids=[f"{c['id']}" for c in CASES[:50]])
    def test_matches_rules_old_regime(self, case):
        calc_compiled = LLMCompiledCalculator()
        calc_rules = RulesCalculator()

        inp = case["input"]
        res_compiled = calc_compiled.compute(inp, regime="old")
        res_rules = calc_rules.compute(inp, regime="old")

        assert res_compiled["taxable_income"] == res_rules["taxable_income"]
        assert res_compiled["total_tax"] == res_rules["total_tax"]
        assert res_compiled["tax_before_rebate"] == res_rules["tax_before_rebate"]
        assert res_compiled["rebate_87a"] == res_rules["rebate_87a"]
        assert res_compiled["surcharge"] == res_rules["surcharge"]
        assert res_compiled["cess"] == res_rules["cess"]

    @pytest.mark.parametrize("case", CASES[:50], ids=[f"{c['id']}" for c in CASES[:50]])
    def test_matches_rules_new_regime(self, case):
        calc_compiled = LLMCompiledCalculator()
        calc_rules = RulesCalculator()

        inp = case["input"]
        res_compiled = calc_compiled.compute(inp, regime="new")
        res_rules = calc_rules.compute(inp, regime="new")

        assert res_compiled["taxable_income"] == res_rules["taxable_income"]
        assert res_compiled["total_tax"] == res_rules["total_tax"]
        assert res_compiled["tax_before_rebate"] == res_rules["tax_before_rebate"]
        assert res_compiled["rebate_87a"] == res_rules["rebate_87a"]
        assert res_compiled["surcharge"] == res_rules["surcharge"]
        assert res_compiled["cess"] == res_rules["cess"]

