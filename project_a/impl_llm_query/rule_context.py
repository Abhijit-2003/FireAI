"""
Official rule context text for LLM at query time.

References:
    - Income Tax Act, 1961
    - Finance Act, 2024 (for FY 2024-25 / AY 2025-26)
    - Finance Act, 2025 (for FY 2025-26 / AY 2026-27)
"""

TAX_RULES_TEXT_FY_2024_25 = """
INDIAN INCOME TAX RULES FOR SALARIED INDIVIDUALS — FY 2024-25 (AY 2025-26)

1. OLD REGIME (Default before FY 2023-24):
   - Standard Deduction (Section 16(ia)): Flat ₹50,000 deduction from gross salary.
   - Slabs (Individuals age < 60):
     * Up to ₹2,50,000: Nil (0%)
     * ₹2,50,001 to ₹5,00,000: 5%
     * ₹5,00,001 to ₹10,00,000: 20%
     * Above ₹10,00,000: 30%
   - Slabs (Senior citizens age 60 to 79):
     * Up to ₹3,00,000: Nil (0%)
     * ₹3,00,001 to ₹5,00,000: 5%
     * ₹5,00,001 to ₹10,00,000: 20%
     * Above ₹10,00,000: 30%
   - Slabs (Super Senior citizens age 80+):
     * Up to ₹5,00,000: Nil (0%)
     * ₹5,00,001 to ₹10,00,000: 20%
     * Above ₹10,00,000: 30%
   - Section 87A Rebate:
     * Applicable if total taxable income does not exceed ₹5,00,000.
     * Rebate = 100% of tax payable or ₹12,500, whichever is less.
   - Deductions & Exemptions Allowed in Old Regime:
     * HRA Exemption (Section 10(13A), Rule 2A): Least of:
       (a) Actual HRA received
       (b) 50% of (Basic + DA) for metro cities (Delhi, Mumbai, Kolkata, Chennai), 40% for non-metro
       (c) Rent paid minus 10% of (Basic + DA)
     * Section 80C: Investments in EPF, PPF, ELSS, life insurance premium, etc., capped at ₹1,50,000.
     * Section 80CCD(1B): Additional NPS contribution up to ₹50,000.
     * Section 80D: Health insurance premium:
       - Self/family: ₹25,000 (₹50,000 if senior citizen)
       - Parents: ₹25,000 (₹50,000 if parents are senior citizens)
     * Section 24(b): Interest on home loan for self-occupied property, capped at ₹2,00,000.

2. NEW REGIME (Section 115BAC, default regime from FY 2023-24):
   - Standard Deduction (Section 16(ia)): Flat ₹75,000 deduction from gross salary.
   - Slabs (Same for all ages):
     * Up to ₹3,00,000: Nil (0%)
     * ₹3,00,001 to ₹7,00,000: 5%
     * ₹7,00,001 to ₹10,00,000: 10%
     * ₹10,00,001 to ₹12,00,000: 15%
     * ₹12,00,001 to ₹15,00,000: 20%
     * Above ₹15,00,000: 30%
   - Section 87A Rebate:
     * Applicable if total taxable income does not exceed ₹7,00,000.
     * Rebate = 100% of tax payable or ₹25,000, whichever is less.
   - No deductions under Chapter VI-A (except 80CCD(2) employer contribution, not salaried personal), no HRA exemption, no Section 24(b) home loan interest.

3. COMMON PROVISIONS (Both Regimes):
   - Surcharge on Income Tax:
     * Taxable income ₹50,00,001 to ₹1,00,00,000: 10% of tax
     * Taxable income ₹1,00,00,01 to ₹2,00,00,000: 15% of tax
     * Taxable income ₹2,00,00,01 to ₹5,00,00,000: 25% of tax
     * Taxable income above ₹5,00,00,000: 37% in Old Regime, but CAPPED at 25% in New Regime.
     * Marginal Relief applies when income exceeds thresholds to ensure extra tax does not exceed excess income.
   - Health and Education Cess:
     * Flat 4% on (Income Tax + Surcharge - Rebate).
   - Rounding Off (Section 288B):
     * Tax payable is rounded off to the nearest rupee (50 paise or more rounded up).
"""

TAX_RULES_TEXT_FY_2025_26 = """
INDIAN INCOME TAX RULES FOR SALARIED INDIVIDUALS — FY 2025-26 (AY 2026-27)
(Finance Act, 2025 Changes Applied)

1. OLD REGIME:
   - Remains completely unchanged from FY 2024-25.

2. NEW REGIME (Section 115BAC - Revised):
   - Standard Deduction: ₹75,000.
   - Revised Slabs:
     * Up to ₹4,00,000: Nil (0%)
     * ₹4,00,001 to ₹8,00,000: 5%
     * ₹8,00,001 to ₹12,00,000: 10%
     * ₹12,00,001 to ₹16,00,000: 15%
     * ₹16,00,001 to ₹20,00,000: 20%
     * ₹20,00,001 to ₹24,00,000: 25%
     * Above ₹24,00,000: 30%
   - Section 87A Rebate:
     * Full rebate for taxable income up to ₹12,00,000. Zero tax for taxable income <= ₹12,00,000.
"""

