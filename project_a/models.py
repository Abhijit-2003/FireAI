"""
Pydantic v2 data models for the Indian Income Tax Computation Engine.

All monetary fields are integers representing whole rupees.
No floats are used for money anywhere in the system.

References:
    - Income Tax Act, 1961
    - Finance Act, 2024 (for FY 2024-25 / AY 2025-26)
    - Finance Act, 2025 (for FY 2025-26 / AY 2026-27)
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AgeCategory(str, Enum):
    """
    Age category of the taxpayer as on 31st March of the assessment year.

    Relevant for:
        - Section 87A rebate eligibility
        - Section 80D deduction limits
        - Old regime basic exemption limit (60+ gets ₹3L, 80+ gets ₹5L)
    """

    BELOW_60 = "below_60"
    SENIOR_60_80 = "senior_60_80"
    SUPER_SENIOR_80_PLUS = "super_senior_80_plus"


class TaxRegime(str, Enum):
    """Tax regime choice — Section 115BAC (new) vs default (old)."""

    OLD = "old"
    NEW = "new"


class TaxpayerInput(BaseModel):
    """
    Complete input required to compute income tax under both regimes.

    All monetary fields are in whole rupees (int).
    Fields that are only relevant to the old regime (e.g. HRA, 80C) are
    still accepted so we can compute both regimes and recommend the better one.

    Attributes:
        financial_year: The financial year, e.g. "2024-25" or "2025-26".
        age_category: Age bracket of the taxpayer as on 31-Mar of the AY.
        gross_salary: Total gross salary before any exemptions/deductions.
        basic_salary: Basic pay component of salary (used for HRA calc).
        da: Dearness Allowance component (used for HRA calc).
        hra_received: HRA component received from employer.
        rent_paid: Actual rent paid per annum (for HRA exemption).
        is_metro: Whether the taxpayer lives in a metro city
                  (Delhi, Mumbai, Kolkata, Chennai) — affects HRA %.
        investment_80c: Qualifying investments/expenditure under Section 80C.
        investment_80ccd_1b: Additional NPS contribution under Section 80CCD(1B).
        health_insurance_self: Health insurance premium paid for self/family
                              under Section 80D.
        health_insurance_parents: Health insurance premium paid for parents
                                 under Section 80D.
        is_self_senior: Whether self (or spouse) is a senior citizen for 80D.
        are_parents_senior: Whether parents are senior citizens for 80D.
        home_loan_interest: Interest paid on home loan for self-occupied property
                           under Section 24(b).
        other_income: Income from other sources (interest, dividends, etc.).
        other_deductions_old: Any other Chapter VI-A deductions applicable
                             under the old regime only.
    """

    financial_year: Literal["2024-25", "2025-26"] = Field(
        default="2024-25",
        description="Financial year for tax computation.",
    )
    age_category: AgeCategory = Field(
        default=AgeCategory.BELOW_60,
        description="Age bracket as on 31-Mar of the AY.",
    )

    # --- Income components ---
    gross_salary: int = Field(
        ge=0,
        description="Total gross salary income (₹).",
    )
    basic_salary: int = Field(
        default=0,
        ge=0,
        description="Basic pay component of salary (₹).",
    )
    da: int = Field(
        default=0,
        ge=0,
        description="Dearness Allowance component (₹).",
    )

    # --- HRA (old regime, Section 10(13A)) ---
    hra_received: int = Field(
        default=0,
        ge=0,
        description="HRA received from employer (₹).",
    )
    rent_paid: int = Field(
        default=0,
        ge=0,
        description="Actual rent paid per annum (₹).",
    )
    is_metro: bool = Field(
        default=False,
        description="Lives in metro (Delhi/Mumbai/Kolkata/Chennai)?",
    )

    # --- Section 80C ---
    investment_80c: int = Field(
        default=0,
        ge=0,
        description="Qualifying 80C investments (₹) — PF, ELSS, PPF, etc.",
    )

    # --- Section 80CCD(1B) ---
    investment_80ccd_1b: int = Field(
        default=0,
        ge=0,
        description="Additional NPS contribution under 80CCD(1B) (₹).",
    )

    # --- Section 80D ---
    health_insurance_self: int = Field(
        default=0,
        ge=0,
        description="Health insurance premium for self/family (₹).",
    )
    health_insurance_parents: int = Field(
        default=0,
        ge=0,
        description="Health insurance premium for parents (₹).",
    )
    is_self_senior: bool = Field(
        default=False,
        description="Is self/spouse a senior citizen (60+) for 80D?",
    )
    are_parents_senior: bool = Field(
        default=False,
        description="Are parents senior citizens (60+) for 80D?",
    )

    # --- Section 24(b) ---
    home_loan_interest: int = Field(
        default=0,
        ge=0,
        description="Home loan interest for self-occupied property (₹).",
    )

    # --- Other ---
    other_income: int = Field(
        default=0,
        ge=0,
        description="Income from other sources (₹).",
    )
    other_deductions_old: int = Field(
        default=0,
        ge=0,
        description="Other Chapter VI-A deductions under old regime (₹).",
    )

    @model_validator(mode="after")
    def _validate_salary_components(self) -> "TaxpayerInput":
        """Ensure basic + DA ≤ gross salary."""
        if self.basic_salary + self.da > self.gross_salary:
            raise ValueError(
                f"basic_salary ({self.basic_salary}) + da ({self.da}) "
                f"cannot exceed gross_salary ({self.gross_salary})."
            )
        return self


class DeductionDetail(BaseModel):
    """A single deduction line item with audit trail."""

    section: str = Field(description="IT Act section reference.")
    description: str = Field(description="Human-readable description.")
    claimed: int = Field(description="Amount claimed by taxpayer (₹).")
    allowed: int = Field(description="Amount allowed after applying limits (₹).")


class TaxBreakdown(BaseModel):
    """
    Detailed tax computation breakdown for one regime.

    Every step appends to ``audit_trail`` for full traceability.
    """

    regime: TaxRegime
    financial_year: str

    # --- Income computation ---
    gross_total_income: int = Field(
        description="Gross total income before deductions (₹).",
    )
    standard_deduction: int = Field(
        default=0,
        description="Standard deduction (₹).",
    )
    hra_exemption: int = Field(
        default=0,
        description="HRA exemption under Section 10(13A) (₹).",
    )
    home_loan_deduction: int = Field(
        default=0,
        description="Home loan interest deduction under Section 24(b) (₹).",
    )
    total_income_from_salary: int = Field(
        default=0,
        description="Income from salary after exemptions (₹).",
    )
    total_gross_income: int = Field(
        default=0,
        description="Gross total income = salary + other sources (₹).",
    )

    # --- Deductions under Chapter VI-A ---
    deductions: list[DeductionDetail] = Field(
        default_factory=list,
        description="Itemized Chapter VI-A deductions.",
    )
    total_deductions: int = Field(
        default=0,
        description="Total Chapter VI-A deductions (₹).",
    )

    # --- Taxable income ---
    taxable_income: int = Field(
        default=0,
        description="Total taxable income after all deductions (₹).",
    )

    # --- Tax computation ---
    tax_on_income: int = Field(
        default=0,
        description="Tax computed on taxable income using slab rates (₹).",
    )
    rebate_87a: int = Field(
        default=0,
        description="Rebate under Section 87A (₹).",
    )
    tax_after_rebate: int = Field(
        default=0,
        description="Tax after rebate (₹).",
    )
    surcharge: int = Field(
        default=0,
        description="Surcharge on income tax (₹).",
    )
    tax_plus_surcharge: int = Field(
        default=0,
        description="Tax + surcharge (₹).",
    )
    cess: int = Field(
        default=0,
        description="Health & Education Cess @ 4% (₹).",
    )
    total_tax: int = Field(
        default=0,
        description="Final total tax payable (₹).",
    )

    # --- Audit trail ---
    audit_trail: list[str] = Field(
        default_factory=list,
        description="Step-by-step computation log with IT Act references.",
    )


class TaxResult(BaseModel):
    """
    Final result containing tax computation under both regimes
    and a recommendation.
    """

    old_regime: TaxBreakdown
    new_regime: TaxBreakdown
    recommended_regime: TaxRegime = Field(
        description="Regime with lower total tax liability.",
    )
    tax_savings: int = Field(
        description="Tax savings by choosing the recommended regime (₹).",
    )
