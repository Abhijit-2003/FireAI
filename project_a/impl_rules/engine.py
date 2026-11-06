"""
Tax computation engine — the main orchestrator.

Computes income tax under both old and new regimes for a given
``TaxpayerInput`` and returns a ``TaxBreakdown`` for each regime.

All computations use integer arithmetic.  Every step appends to the
audit trail for full traceability back to the Income Tax Act.

References:
    - Income Tax Act, 1961 — various sections cited in audit trail
    - Finance Act, 2024 / 2025
"""

from __future__ import annotations

from project_a.models import (
    AgeCategory,
    DeductionDetail,
    TaxBreakdown,
    TaxpayerInput,
    TaxRegime,
)
from project_a.tax_rules import constants as c
from project_a.tax_rules import constants_2025_26 as c26
from project_a.tax_rules.cess import calc_cess
from project_a.tax_rules.constants import TaxSlab
from project_a.tax_rules.deductions import (
    calc_home_loan_interest,
    calc_hra_exemption,
    calc_section_80c,
    calc_section_80ccd_1b,
    calc_section_80d,
    calc_standard_deduction,
)
from project_a.tax_rules.rebate import calc_rebate_87a
from project_a.tax_rules.surcharge import calc_surcharge


def _get_old_regime_slabs(age: AgeCategory) -> list[TaxSlab]:
    """Return old-regime slab schedule based on age category."""
    if age == AgeCategory.SUPER_SENIOR_80_PLUS:
        return c.OLD_REGIME_SLABS_SUPER_SENIOR
    elif age == AgeCategory.SENIOR_60_80:
        return c.OLD_REGIME_SLABS_SENIOR
    else:
        return c.OLD_REGIME_SLABS_BELOW_60


def _get_new_regime_slabs(fy: str) -> list[TaxSlab]:
    """Return new-regime slab schedule for the given FY."""
    if fy == "2025-26":
        return c26.NEW_REGIME_SLABS
    return c.NEW_REGIME_SLABS


def _compute_tax_on_slabs(
    taxable_income: int,
    slabs: list[TaxSlab],
) -> tuple[int, list[str]]:
    """
    Compute income tax on given slabs. Returns (tax, slab_audit_lines).

    Applies Section 288B of Income Tax Act: rounding to nearest rupee
    (>=50 paise rounds up).
    """
    tax_paise = 0
    prev_upper = 0
    audit_lines: list[str] = []

    for slab in slabs:
        if slab.upper is None:
            if taxable_income > prev_upper:
                chunk = taxable_income - prev_upper
                slab_tax_paise = chunk * slab.rate
                tax_paise += slab_tax_paise
                slab_tax_rs = (slab_tax_paise + 50) // 100
                audit_lines.append(
                    f"  Slab ₹{prev_upper:,}+ @ {slab.rate}%: "
                    f"₹{chunk:,} × {slab.rate}% = ₹{slab_tax_rs:,}"
                )
            break

        if taxable_income <= prev_upper:
            break

        chunk = min(taxable_income, slab.upper) - prev_upper
        slab_tax_paise = chunk * slab.rate
        tax_paise += slab_tax_paise
        slab_tax_rs = (slab_tax_paise + 50) // 100

        upper_str = f"₹{slab.upper:,}"
        audit_lines.append(
            f"  Slab ₹{prev_upper:,}–{upper_str} @ {slab.rate}%: "
            f"₹{chunk:,} × {slab.rate}% = ₹{slab_tax_rs:,}"
        )
        prev_upper = slab.upper

    tax = (tax_paise + 50) // 100
    return tax, audit_lines


def compute_tax_for_regime(
    inp: TaxpayerInput,
    regime: TaxRegime,
) -> TaxBreakdown:
    """
    Compute complete tax breakdown for a single regime.

    Args:
        inp: Validated taxpayer input.
        regime: OLD or NEW.

    Returns:
        Fully populated ``TaxBreakdown`` with audit trail.
    """
    fy = inp.financial_year
    regime_str = regime.value
    audit: list[str] = []
    deductions: list[DeductionDetail] = []

    audit.append(f"=== Tax Computation: {regime_str.upper()} Regime, FY {fy} ===")

    # ------------------------------------------------------------------
    # Step 1: Gross total income
    # ------------------------------------------------------------------
    gross_salary = inp.gross_salary
    audit.append(f"[Step 1] Gross salary income: ₹{gross_salary:,}")

    # ------------------------------------------------------------------
    # Step 2: Standard deduction — Section 16(ia)
    # ------------------------------------------------------------------
    std_ded, std_note = calc_standard_deduction(regime_str, fy)
    # Standard deduction cannot exceed gross salary
    std_ded = min(std_ded, gross_salary)
    audit.append(f"[Step 2] {std_note}")

    # ------------------------------------------------------------------
    # Step 3: HRA exemption — Section 10(13A) [old regime only]
    # ------------------------------------------------------------------
    hra_exempt = 0
    if regime == TaxRegime.OLD:
        hra_exempt, hra_note = calc_hra_exemption(
            basic=inp.basic_salary,
            da=inp.da,
            hra_received=inp.hra_received,
            rent_paid=inp.rent_paid,
            is_metro=inp.is_metro,
        )
        audit.append(f"[Step 3] {hra_note}")
    else:
        audit.append("[Step 3] HRA exemption: not applicable under new regime.")

    # ------------------------------------------------------------------
    # Step 4: Income from salary after exemptions
    # ------------------------------------------------------------------
    income_from_salary = max(0, gross_salary - std_ded - hra_exempt)
    audit.append(
        f"[Step 4] Income from salary = ₹{gross_salary:,} "
        f"− ₹{std_ded:,} (std ded) − ₹{hra_exempt:,} (HRA) "
        f"= ₹{income_from_salary:,}"
    )

    # ------------------------------------------------------------------
    # Step 5: Home loan interest deduction — Section 24(b) [old regime only]
    # ------------------------------------------------------------------
    home_loan_ded = 0
    if regime == TaxRegime.OLD and inp.home_loan_interest > 0:
        home_loan_ded, hl_note = calc_home_loan_interest(inp.home_loan_interest)
        audit.append(f"[Step 5] {hl_note}")
        # Section 24(b) is a deduction from income from house property
        # Net effect: reduces total income
        income_from_salary = max(0, income_from_salary - home_loan_ded)
        audit.append(
            f"[Step 5] Income after Sec 24(b): ₹{income_from_salary:,}"
        )
    else:
        audit.append(
            "[Step 5] Home loan interest: "
            + (
                "not applicable under new regime."
                if regime == TaxRegime.NEW
                else "₹0 claimed."
            )
        )

    # ------------------------------------------------------------------
    # Step 6: Gross total income (salary + other sources)
    # ------------------------------------------------------------------
    gross_total_income = income_from_salary + inp.other_income
    audit.append(
        f"[Step 6] Gross total income = ₹{income_from_salary:,} (salary) "
        f"+ ₹{inp.other_income:,} (other) = ₹{gross_total_income:,}"
    )

    # ------------------------------------------------------------------
    # Step 7: Chapter VI-A deductions [old regime only]
    # ------------------------------------------------------------------
    total_chapter_via = 0

    if regime == TaxRegime.OLD:
        audit.append("[Step 7] Chapter VI-A Deductions (Old Regime):")

        # 80C
        if inp.investment_80c > 0:
            allowed_80c, note_80c = calc_section_80c(inp.investment_80c)
            deductions.append(
                DeductionDetail(
                    section="80C",
                    description="PPF/ELSS/EPF/LIC/etc.",
                    claimed=inp.investment_80c,
                    allowed=allowed_80c,
                )
            )
            total_chapter_via += allowed_80c
            audit.append(f"  {note_80c}")

        # 80CCD(1B)
        if inp.investment_80ccd_1b > 0:
            allowed_nps, note_nps = calc_section_80ccd_1b(inp.investment_80ccd_1b)
            deductions.append(
                DeductionDetail(
                    section="80CCD(1B)",
                    description="Additional NPS contribution",
                    claimed=inp.investment_80ccd_1b,
                    allowed=allowed_nps,
                )
            )
            total_chapter_via += allowed_nps
            audit.append(f"  {note_nps}")

        # 80D
        if inp.health_insurance_self > 0 or inp.health_insurance_parents > 0:
            self_80d, parents_80d, note_80d = calc_section_80d(
                self_premium=inp.health_insurance_self,
                parents_premium=inp.health_insurance_parents,
                is_self_senior=inp.is_self_senior,
                are_parents_senior=inp.are_parents_senior,
            )
            total_80d = self_80d + parents_80d
            deductions.append(
                DeductionDetail(
                    section="80D",
                    description="Health insurance premium",
                    claimed=inp.health_insurance_self + inp.health_insurance_parents,
                    allowed=total_80d,
                )
            )
            total_chapter_via += total_80d
            audit.append(f"  {note_80d}")

        # Other old-regime deductions
        if inp.other_deductions_old > 0:
            deductions.append(
                DeductionDetail(
                    section="Chapter VI-A (other)",
                    description="Other old-regime deductions",
                    claimed=inp.other_deductions_old,
                    allowed=inp.other_deductions_old,
                )
            )
            total_chapter_via += inp.other_deductions_old
            audit.append(
                f"  [Chapter VI-A (other)] Other deductions: "
                f"₹{inp.other_deductions_old:,}"
            )

        audit.append(f"  Total Chapter VI-A deductions: ₹{total_chapter_via:,}")
    else:
        audit.append(
            "[Step 7] Chapter VI-A deductions: not available under new regime."
        )

    # ------------------------------------------------------------------
    # Step 8: Taxable income
    # ------------------------------------------------------------------
    taxable_income = max(0, gross_total_income - total_chapter_via)
    audit.append(
        f"[Step 8] Taxable income = ₹{gross_total_income:,} "
        f"− ₹{total_chapter_via:,} = ₹{taxable_income:,}"
    )

    # ------------------------------------------------------------------
    # Step 9: Tax on income (slab rates)
    # ------------------------------------------------------------------
    if regime == TaxRegime.OLD:
        slabs = _get_old_regime_slabs(inp.age_category)
        slab_label = f"old regime ({inp.age_category.value})"
    else:
        slabs = _get_new_regime_slabs(fy)
        slab_label = f"new regime (FY {fy})"

    tax_on_income, slab_lines = _compute_tax_on_slabs(taxable_income, slabs)
    audit.append(f"[Step 9] Tax on ₹{taxable_income:,} using {slab_label} slabs:")
    audit.extend(slab_lines)
    audit.append(f"  Total tax on income = ₹{tax_on_income:,}")

    # ------------------------------------------------------------------
    # Step 10: Rebate under Section 87A
    # ------------------------------------------------------------------
    rebate, rebate_note = calc_rebate_87a(
        taxable_income=taxable_income,
        tax_on_income=tax_on_income,
        regime=regime_str,
        fy=fy,
    )
    tax_after_rebate = max(0, tax_on_income - rebate)
    audit.append(f"[Step 10] {rebate_note}")
    audit.append(f"  Tax after rebate = ₹{tax_after_rebate:,}")

    # ------------------------------------------------------------------
    # Step 11: Surcharge (with marginal relief)
    # ------------------------------------------------------------------
    surcharge, surcharge_note = calc_surcharge(
        taxable_income=taxable_income,
        tax_after_rebate=tax_after_rebate,
        regime=regime_str,
        slabs=slabs,
    )
    tax_plus_surcharge = tax_after_rebate + surcharge
    audit.append(f"[Step 11] {surcharge_note}")
    audit.append(f"  Tax + surcharge = ₹{tax_plus_surcharge:,}")

    # ------------------------------------------------------------------
    # Step 12: Health & Education Cess — 4%
    # ------------------------------------------------------------------
    cess, cess_note = calc_cess(tax_plus_surcharge)
    total_tax = tax_plus_surcharge + cess
    audit.append(f"[Step 12] {cess_note}")
    audit.append(f"  *** Total tax payable = ₹{total_tax:,} ***")

    # ------------------------------------------------------------------
    # Build result
    # ------------------------------------------------------------------
    return TaxBreakdown(
        regime=regime,
        financial_year=fy,
        gross_total_income=inp.gross_salary + inp.other_income,
        standard_deduction=std_ded,
        hra_exemption=hra_exempt,
        home_loan_deduction=home_loan_ded,
        total_income_from_salary=income_from_salary,
        total_gross_income=gross_total_income,
        deductions=deductions,
        total_deductions=total_chapter_via,
        taxable_income=taxable_income,
        tax_on_income=tax_on_income,
        rebate_87a=rebate,
        tax_after_rebate=tax_after_rebate,
        surcharge=surcharge,
        tax_plus_surcharge=tax_plus_surcharge,
        cess=cess,
        total_tax=total_tax,
        audit_trail=audit,
    )
