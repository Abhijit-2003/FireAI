"""
Tax constants for FY 2025-26 (AY 2026-27).

Only values that differ from FY 2024-25 are redefined here.
Import from ``constants.py`` for anything unchanged (old regime slabs,
80C/80CCD/80D limits, HRA constants, Section 24(b), surcharge slabs, cess).

References:
    - Finance Act, 2025
    - Section 115BAC as amended
"""

from __future__ import annotations

from project_a.tax_rules.constants import TaxSlab

# ---------------------------------------------------------------------------
# Financial year identifier
# ---------------------------------------------------------------------------
FY = "2025-26"

# ---------------------------------------------------------------------------
# New Regime Tax Slabs — Section 115BAC (FY 2025-26, revised)
#
# Budget 2025 introduced wider slabs and a new 25% bracket:
#   0 – 4L   :  0%
#   4L – 8L  :  5%
#   8L – 12L : 10%
#  12L – 16L : 15%
#  16L – 20L : 20%
#  20L – 24L : 25%
#  Above 24L : 30%
# ---------------------------------------------------------------------------
NEW_REGIME_SLABS: list[TaxSlab] = [
    TaxSlab(upper=400_000, rate=0),
    TaxSlab(upper=800_000, rate=5),
    TaxSlab(upper=1_200_000, rate=10),
    TaxSlab(upper=1_600_000, rate=15),
    TaxSlab(upper=2_000_000, rate=20),
    TaxSlab(upper=2_400_000, rate=25),
    TaxSlab(upper=None, rate=30),
]

# ---------------------------------------------------------------------------
# Standard Deduction — Section 16(ia)
# Old regime: unchanged at ₹50,000
# New regime: ₹75,000 (same as FY 2024-25 new regime)
# ---------------------------------------------------------------------------
STANDARD_DEDUCTION_NEW: int = 75_000

# ---------------------------------------------------------------------------
# Section 87A — Rebate (New Regime, FY 2025-26)
#
# If total income ≤ ₹12,00,000 under new regime, full tax is rebated
# (i.e., rebate = entire tax on income, effectively zero tax).
# Old regime rebate remains unchanged.
# ---------------------------------------------------------------------------
REBATE_87A_NEW_INCOME_LIMIT: int = 1_200_000
# "Full rebate" means rebate = tax_on_income (no fixed cap)
REBATE_87A_NEW_FULL_REBATE: bool = True
