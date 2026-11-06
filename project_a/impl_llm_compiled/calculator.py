"""
LLM-Compiled Calculator — executes compiled rules deterministically.

Matches the exact interface of RulesCalculator and LLMQueryCalculator.
"""

from __future__ import annotations
from typing import Any

from project_a.models import (
    AgeCategory,
    TaxpayerInput,
    TaxRegime,
    TaxResult,
    TaxBreakdown,
    DeductionDetail,
)
from project_a.impl_rules.calculator import _dict_to_taxpayer_input
from project_a.impl_llm_compiled import generated_rules as gr


class LLMCompiledCalculator:
    """
    Executes rules compiled once by an LLM and reviewed by an engineer.
    Zero LLM latency and zero LLM API cost at query time.
    """

    def calculate(self, inp: TaxpayerInput | dict[str, Any]) -> TaxResult:
        if isinstance(inp, dict):
            inp = _dict_to_taxpayer_input(inp)

        old_bd = self._compute_old_regime(inp)
        new_bd = self._compute_new_regime(inp)

        if old_bd.total_tax <= new_bd.total_tax:
            rec = TaxRegime.OLD
            savings = new_bd.total_tax - old_bd.total_tax
        else:
            rec = TaxRegime.NEW
            savings = old_bd.total_tax - new_bd.total_tax

        return TaxResult(
            old_regime=old_bd,
            new_regime=new_bd,
            recommended_regime=rec,
            tax_savings=savings,
        )

    def compute(
        self,
        inp: TaxpayerInput | dict[str, Any],
        regime: str | TaxRegime | None = None,
    ) -> dict[str, Any] | TaxResult:
        if regime is None:
            return self.calculate(inp)

        if isinstance(inp, dict):
            inp = _dict_to_taxpayer_input(inp)

        r_str = regime.value if isinstance(regime, TaxRegime) else regime.lower()
        bd = self._compute_old_regime(inp) if r_str == "old" else self._compute_new_regime(inp)

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

    def _compute_old_regime(self, inp: TaxpayerInput) -> TaxBreakdown:
        audit: list[str] = ["[LLM-Compiled Rules: Old Regime FY 2024-25]"]
        gross = inp.gross_salary
        sd = min(gr.compiled_standard_deduction("old"), gross)
        audit.append(f"[Step 2] Standard Deduction: ₹{sd:,}")

        hra_ex, hra_note = gr.compiled_hra_exemption(
            inp.basic_salary, inp.da, inp.hra_received, inp.rent_paid, inp.is_metro
        )
        audit.append(f"[Step 3] {hra_note}")

        sal_income = max(0, gross - sd - hra_ex)
        hl = min(inp.home_loan_interest, 200000)
        if hl > 0:
            sal_income = max(0, sal_income - hl)
            audit.append(f"[Step 5] Section 24(b) Home Loan Interest: ₹{hl:,}")

        gross_tot = sal_income + inp.other_income
        ch_via, ch_notes = gr.compiled_deductions_chapter_via(inp.model_dump())
        audit.extend(ch_notes)

        taxable = max(0, gross_tot - ch_via)
        audit.append(f"[Step 8] Taxable Income: ₹{taxable:,}")

        age = 85 if inp.age_category == AgeCategory.SUPER_SENIOR_80_PLUS else (
            65 if inp.age_category == AgeCategory.SENIOR_60_80 else 30
        )
        tax_on_income, slab_lines = gr.compiled_old_slab_tax(taxable, age)
        audit.extend(slab_lines)

        # Section 87A rebate
        rebate = min(tax_on_income, 12500) if taxable <= 500000 else 0
        if rebate > 0:
            audit.append(f"[Step 10] Section 87A Rebate: ₹{rebate:,}")
        tax_after_reb = max(0, tax_on_income - rebate)

        surcharge, sc_note = gr.compiled_surcharge_and_relief(
            tax_after_reb, taxable, is_new=False, fy=inp.financial_year
        )
        audit.append(f"[Step 11] {sc_note}")

        cess = round((tax_after_reb + surcharge) * 0.04)
        total = tax_after_reb + surcharge + cess
        audit.append(f"[Step 12] Health & Education Cess @ 4%: ₹{cess:,}")
        audit.append(f"Total Tax Payable: ₹{total:,}")

        return TaxBreakdown(
            regime=TaxRegime.OLD,
            financial_year=inp.financial_year,
            gross_total_income=gross + inp.other_income,
            standard_deduction=sd,
            hra_exemption=hra_ex,
            home_loan_deduction=hl,
            total_income_from_salary=sal_income,
            total_gross_income=gross_tot,
            total_deductions=ch_via,
            taxable_income=taxable,
            tax_on_income=tax_on_income,
            rebate_87a=rebate,
            tax_after_rebate=tax_after_reb,
            surcharge=surcharge,
            tax_plus_surcharge=tax_after_reb + surcharge,
            cess=cess,
            total_tax=total,
            audit_trail=audit,
        )

    def _compute_new_regime(self, inp: TaxpayerInput) -> TaxBreakdown:
        fy = inp.financial_year
        audit: list[str] = [f"[LLM-Compiled Rules: New Regime FY {fy}]"]
        gross = inp.gross_salary
        sd = min(gr.compiled_standard_deduction("new", fy), gross)
        audit.append(f"[Step 2] Standard Deduction: ₹{sd:,}")

        taxable = max(0, (gross - sd) + inp.other_income)
        audit.append(f"[Step 8] Taxable Income: ₹{taxable:,}")

        tax_on_income, slab_lines = gr.compiled_new_slab_tax(taxable, fy)
        audit.extend(slab_lines)

        # Section 87A Rebate
        if fy == "2025-26":
            rebate = tax_on_income if taxable <= 1200000 else 0
        else:
            rebate = min(tax_on_income, 25000) if taxable <= 700000 else 0

        if rebate > 0:
            audit.append(f"[Step 10] Section 87A Rebate: ₹{rebate:,}")
        tax_after_reb = max(0, tax_on_income - rebate)

        surcharge, sc_note = gr.compiled_surcharge_and_relief(
            tax_after_reb, taxable, is_new=True, fy=fy
        )
        audit.append(f"[Step 11] {sc_note}")

        cess = round((tax_after_reb + surcharge) * 0.04)
        total = tax_after_reb + surcharge + cess
        audit.append(f"[Step 12] Health & Education Cess @ 4%: ₹{cess:,}")
        audit.append(f"Total Tax Payable: ₹{total:,}")

        return TaxBreakdown(
            regime=TaxRegime.NEW,
            financial_year=fy,
            gross_total_income=gross + inp.other_income,
            standard_deduction=sd,
            hra_exemption=0,
            home_loan_deduction=0,
            total_income_from_salary=max(0, gross - sd),
            total_gross_income=taxable,
            total_deductions=0,
            taxable_income=taxable,
            tax_on_income=tax_on_income,
            rebate_87a=rebate,
            tax_after_rebate=tax_after_reb,
            surcharge=surcharge,
            tax_plus_surcharge=tax_after_reb + surcharge,
            cess=cess,
            total_tax=total,
            audit_trail=audit,
        )

