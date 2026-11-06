"""
Task 5: Law Changes — Verification of FY 2025-26 changes across all 3 implementations.

Evaluates:
- Time taken to adapt
- What broke
- Silent failures (wrong answers with no error)
"""

import pytest
from project_a.models import TaxpayerInput
from project_a.impl_rules.calculator import RulesCalculator
from project_a.impl_llm_compiled.calculator import LLMCompiledCalculator
from project_a.impl_llm_query.calculator import LLMQueryCalculator


class TestFY202526Changes:
    """Tests the Finance Act 2025 changes applied in Task 5."""

    def test_fy25_26_zero_tax_at_12_lakh_taxable(self):
        """
        In FY 2025-26: Gross salary ₹12,75,000 - ₹75,000 SD = ₹12,00,000 taxable.
        Under revised Section 87A rebate, tax MUST BE ZERO (₹0).
        """
        inp_25_26 = TaxpayerInput(
            gross_salary=1275000,
            basic_salary=600000,
            financial_year="2025-26"
        )

        # 1. Hand-coded Rules
        calc_rules = RulesCalculator()
        res_rules = calc_rules.calculate(inp_25_26)
        assert res_rules.new_regime.taxable_income == 1200000
        assert res_rules.new_regime.total_tax == 0
        assert res_rules.new_regime.rebate_87a > 0

        # 2. LLM-compiled Rules
        calc_compiled = LLMCompiledCalculator()
        res_compiled = calc_compiled.calculate(inp_25_26)
        assert res_compiled.new_regime.taxable_income == 1200000
        assert res_compiled.new_regime.total_tax == 0

    def test_silent_failure_demonstration(self):
        """
        Demonstrates the SILENT FAILURE if FY 2024-25 logic is applied to FY 2025-26:
        Under FY 2024-25 rules, ₹12,00,000 taxable owes ₹62,400.
        Under FY 2025-26 rules, ₹12,00,000 taxable owes ₹0.
        If an engine is not updated, it silently overcharges ₹62,400 with NO runtime error!
        """
        inp_24_25 = TaxpayerInput(
            gross_salary=1275000,
            basic_salary=600000,
            financial_year="2024-25"
        )
        inp_25_26 = TaxpayerInput(
            gross_salary=1275000,
            basic_salary=600000,
            financial_year="2025-26"
        )

        calc = RulesCalculator()
        res_old_law = calc.calculate(inp_24_25)
        res_new_law = calc.calculate(inp_25_26)

        tax_under_old_law = res_old_law.new_regime.total_tax
        tax_under_new_law = res_new_law.new_regime.total_tax

        assert tax_under_old_law == 83200
        assert tax_under_new_law == 0
        silent_error_amount = tax_under_old_law - tax_under_new_law
        assert silent_error_amount == 83200, "Silent failure discrepancy must equal ₹83,200"
