"""
Tax constants for FY 2024-25 (AY 2025-26).

All monetary values are in whole rupees (int).

References:
    - Income Tax Act, 1961
    - Finance (No. 2) Act, 2024
    - Section 115BAC (new tax regime)
"""

from __future__ import annotations

from typing import NamedTuple


class TaxSlab(NamedTuple):
    """A single tax slab: income up to ``upper`` is taxed at ``rate`` (percentage)."""

    upper: int | None  # None means no upper limit (the last slab)
    rate: int  # percentage, e.g. 5 means 5%


# ---------------------------------------------------------------------------
# Financial year identifier
# ---------------------------------------------------------------------------
FY = "2024-25"

# ---------------------------------------------------------------------------
# Old Regime Tax Slabs — Section 2(9) read with Part I/III of First Schedule
# ---------------------------------------------------------------------------
# For individuals below 60
OLD_REGIME_SLABS_BELOW_60: list[TaxSlab] = [
    TaxSlab(upper=250_000, rate=0),
    TaxSlab(upper=500_000, rate=5),
    TaxSlab(upper=1_000_000, rate=20),
    TaxSlab(upper=None, rate=30),
]

# For senior citizens (60-80)
OLD_REGIME_SLABS_SENIOR: list[TaxSlab] = [
    TaxSlab(upper=300_000, rate=0),
    TaxSlab(upper=500_000, rate=5),
    TaxSlab(upper=1_000_000, rate=20),
    TaxSlab(upper=None, rate=30),
]

# For super senior citizens (80+)
OLD_REGIME_SLABS_SUPER_SENIOR: list[TaxSlab] = [
    TaxSlab(upper=500_000, rate=0),
    TaxSlab(upper=1_000_000, rate=20),
    TaxSlab(upper=None, rate=30),
]

# ---------------------------------------------------------------------------
# New Regime Tax Slabs — Section 115BAC (FY 2024-25)
# ---------------------------------------------------------------------------
NEW_REGIME_SLABS: list[TaxSlab] = [
    TaxSlab(upper=300_000, rate=0),
    TaxSlab(upper=700_000, rate=5),
    TaxSlab(upper=1_000_000, rate=10),
    TaxSlab(upper=1_200_000, rate=15),
    TaxSlab(upper=1_500_000, rate=20),
    TaxSlab(upper=None, rate=30),
]

# ---------------------------------------------------------------------------
# Standard Deduction — Section 16(ia)
# ---------------------------------------------------------------------------
STANDARD_DEDUCTION_OLD: int = 50_000
STANDARD_DEDUCTION_NEW: int = 75_000

# ---------------------------------------------------------------------------
# HRA Exemption — Section 10(13A), Rule 2A
# ---------------------------------------------------------------------------
HRA_METRO_PERCENT: int = 50  # 50% of (Basic + DA) for metro cities
HRA_NON_METRO_PERCENT: int = 40  # 40% of (Basic + DA) for non-metro cities

# ---------------------------------------------------------------------------
# Section 80C — Deduction limit
# ---------------------------------------------------------------------------
SECTION_80C_LIMIT: int = 150_000

# ---------------------------------------------------------------------------
# Section 80CCD(1B) — Additional NPS deduction
# ---------------------------------------------------------------------------
SECTION_80CCD_1B_LIMIT: int = 50_000

# ---------------------------------------------------------------------------
# Section 80D — Health insurance premium deduction limits
# ---------------------------------------------------------------------------
SECTION_80D_SELF_BELOW_60: int = 25_000
SECTION_80D_SELF_SENIOR: int = 50_000
SECTION_80D_PARENTS_BELOW_60: int = 25_000
SECTION_80D_PARENTS_SENIOR: int = 50_000

# ---------------------------------------------------------------------------
# Section 24(b) — Interest on home loan (self-occupied property)
# ---------------------------------------------------------------------------
SECTION_24B_LIMIT: int = 200_000

# ---------------------------------------------------------------------------
# Section 87A — Rebate
# ---------------------------------------------------------------------------
REBATE_87A_OLD_INCOME_LIMIT: int = 500_000
REBATE_87A_OLD_MAX: int = 12_500

REBATE_87A_NEW_INCOME_LIMIT: int = 700_000
REBATE_87A_NEW_MAX: int = 25_000

# ---------------------------------------------------------------------------
# Surcharge — Section 2(9), Finance Act
# ---------------------------------------------------------------------------
# (threshold, rate_percent)
# Income above this threshold attracts this surcharge rate on the income tax.
SURCHARGE_SLABS: list[tuple[int, int]] = [
    (5_000_000, 10),
    (10_000_000, 15),
    (20_000_000, 25),
    (50_000_000, 37),
]

# New regime caps surcharge at 25%
NEW_REGIME_MAX_SURCHARGE_RATE: int = 25

# ---------------------------------------------------------------------------
# Health & Education Cess — Section 2(9), Finance Act
# ---------------------------------------------------------------------------
CESS_RATE: int = 4  # 4% on tax + surcharge
