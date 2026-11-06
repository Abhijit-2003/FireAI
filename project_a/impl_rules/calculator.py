"""
RulesCalculator — the public API for the tax computation engine.

Usage::

    from project_a.models import TaxpayerInput
    from project_a.impl_rules.calculator import RulesCalculator

    calc = RulesCalculator()
    inp = TaxpayerInput(gross_salary=1_500_000, ...)
    result = calc.calculate(inp)
    print(result.recommended_regime)
    print(result.tax_savings)

All monetary values are in whole rupees (int). No floats.
"""

from __future__ import annotations
from typing import Any

from project_a.impl_rules.engine import compute_tax_for_regime
from project_a.models import (
    AgeCategory,
    TaxpayerInput,
    TaxRegime,
    TaxResult,
    TaxBreakdown,
)


def _dict_to_taxpayer_input(d: dict[str, Any]) -> TaxpayerInput:
    """Helper to convert raw dictionary inputs (from JSON/test cases) into TaxpayerInput."""
    age = d.get("age", 30)
    if "age_category" in d:
        age_cat = (
            d["age_category"]
            if isinstance(d["age_category"], AgeCategory)
            else AgeCategory(d["age_category"])
        )
    else:
        if age >= 80:
            age_cat = AgeCategory.SUPER_SENIOR_80_PLUS
        elif age >= 60:
            age_cat = AgeCategory.SENIOR_60_80
        else:
            age_cat = AgeCategory.BELOW_60

    is_metro = d.get("is_metro")
    if is_metro is None:
        is_metro = d.get("city_type", "non_metro").lower() == "metro"

    inv_80c = d.get("investment_80c", d.get("section_80c", 0))
    inv_80ccd = d.get("investment_80ccd_1b", d.get("section_80ccd_1b", 0))
    hi_self = d.get("health_insurance_self", d.get("section_80d_self", 0))
    hi_parents = d.get("health_insurance_parents", d.get("section_80d_parents", 0))
    are_parents_senior = d.get(
        "are_parents_senior", d.get("parents_senior_citizen", False)
    )
    is_self_senior = d.get("is_self_senior", age >= 60)

    gross = d.get("gross_salary", 0) or 0
    basic = d.get("basic_salary")
    if basic is None:
        basic = gross
    da = d.get("da", 0) or 0

    # Basic + DA cannot exceed gross salary in valid salary structure
    if basic + da > gross:
        basic = max(0, gross - da)

    return TaxpayerInput(
        financial_year=d.get("financial_year", "2024-25"),
        age_category=age_cat,
        gross_salary=gross,
        basic_salary=basic,
        da=da,
        hra_received=d.get("hra_received", 0),
        rent_paid=d.get("rent_paid", 0),
        is_metro=is_metro,
        investment_80c=inv_80c,
        investment_80ccd_1b=inv_80ccd,
        health_insurance_self=hi_self,
        health_insurance_parents=hi_parents,
        is_self_senior=is_self_senior,
        are_parents_senior=are_parents_senior,
        home_loan_interest=d.get("home_loan_interest", 0),
        other_income=d.get("other_income", 0),
        other_deductions_old=d.get("other_deductions_old", 0),
    )


class RulesCalculator:
    """
    Stateless tax calculator that computes tax under both regimes
    and recommends the one with lower liability.
    """

    def calculate(self, inp: TaxpayerInput | dict[str, Any]) -> TaxResult:
        """
        Compute income tax under Old and New regimes and return
        a ``TaxResult`` with a recommendation.
        """
        if isinstance(inp, dict):
            inp = _dict_to_taxpayer_input(inp)

        old_breakdown = compute_tax_for_regime(inp, TaxRegime.OLD)
        new_breakdown = compute_tax_for_regime(inp, TaxRegime.NEW)

        if old_breakdown.total_tax <= new_breakdown.total_tax:
            recommended = TaxRegime.OLD
            savings = new_breakdown.total_tax - old_breakdown.total_tax
        else:
            recommended = TaxRegime.NEW
            savings = old_breakdown.total_tax - new_breakdown.total_tax

        return TaxResult(
            old_regime=old_breakdown,
            new_regime=new_breakdown,
            recommended_regime=recommended,
            tax_savings=savings,
        )

    def compute(
        self,
        inp: TaxpayerInput | dict[str, Any],
        regime: str | TaxRegime | None = None,
    ) -> dict[str, Any] | TaxResult:
        """
        Compute tax for a specific regime (returning a flat dict of values)
        or for both regimes (returning a TaxResult).
        """
        if regime is None:
            return self.calculate(inp)

        if isinstance(inp, dict):
            inp = _dict_to_taxpayer_input(inp)

        regime_enum = (
            regime if isinstance(regime, TaxRegime) else TaxRegime(regime.lower())
        )
        bd = compute_tax_for_regime(inp, regime_enum)

        return {
            "taxable_income": bd.taxable_income,
            "tax_before_rebate": bd.tax_on_income,
            "rebate_87a": bd.rebate_87a,
            "tax_after_rebate": bd.tax_after_rebate,
            "surcharge": bd.surcharge,
            "cess": bd.cess,
            "total_tax": bd.total_tax,
            "breakdown": bd,
        }

