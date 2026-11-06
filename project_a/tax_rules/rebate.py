"""
Section 87A rebate calculator.

References:
    - Section 87A of the Income Tax Act, 1961
    - Finance Act, 2024 (FY 2024-25)
    - Finance Act, 2025 (FY 2025-26)

Rules:
    OLD regime (all FYs covered):
        If taxable income ≤ ₹5,00,000 → rebate = min(tax, ₹12,500)

    NEW regime FY 2024-25:
        If taxable income ≤ ₹7,00,000 → rebate = min(tax, ₹25,000)

    NEW regime FY 2025-26:
        If taxable income ≤ ₹12,00,000 → rebate = full tax amount
        (i.e., entire income tax is rebated, resulting in zero tax)
"""

from __future__ import annotations

from project_a.tax_rules import constants as c
from project_a.tax_rules import constants_2025_26 as c26


def calc_rebate_87a(
    taxable_income: int,
    tax_on_income: int,
    regime: str,
    fy: str = "2024-25",
) -> tuple[int, str]:
    """
    Compute rebate under Section 87A.

    Args:
        taxable_income: Total taxable income after all deductions (₹).
        tax_on_income: Tax computed on taxable income before rebate (₹).
        regime: "old" or "new".
        fy: Financial year string.

    Returns:
        (rebate_amount, audit_note)
    """
    if regime == "old":
        if taxable_income <= c.REBATE_87A_OLD_INCOME_LIMIT:
            rebate = min(tax_on_income, c.REBATE_87A_OLD_MAX)
            note = (
                f"[Section 87A] Old regime: taxable income ₹{taxable_income:,} "
                f"≤ ₹{c.REBATE_87A_OLD_INCOME_LIMIT:,} → "
                f"rebate = min(tax ₹{tax_on_income:,}, ₹{c.REBATE_87A_OLD_MAX:,}) "
                f"= ₹{rebate:,}"
            )
        else:
            rebate = 0
            note = (
                f"[Section 87A] Old regime: taxable income ₹{taxable_income:,} "
                f"> ₹{c.REBATE_87A_OLD_INCOME_LIMIT:,} → no rebate."
            )
    elif regime == "new" and fy == "2025-26":
        if taxable_income <= c26.REBATE_87A_NEW_INCOME_LIMIT:
            # Full rebate: entire tax is rebated
            rebate = tax_on_income
            note = (
                f"[Section 87A] New regime FY 2025-26: taxable income "
                f"₹{taxable_income:,} ≤ ₹{c26.REBATE_87A_NEW_INCOME_LIMIT:,} → "
                f"full rebate = ₹{rebate:,} (zero tax)."
            )
        else:
            rebate = 0
            note = (
                f"[Section 87A] New regime FY 2025-26: taxable income "
                f"₹{taxable_income:,} > ₹{c26.REBATE_87A_NEW_INCOME_LIMIT:,} → "
                f"no rebate."
            )
    else:
        # New regime, FY 2024-25
        if taxable_income <= c.REBATE_87A_NEW_INCOME_LIMIT:
            rebate = min(tax_on_income, c.REBATE_87A_NEW_MAX)
            note = (
                f"[Section 87A] New regime FY {fy}: taxable income "
                f"₹{taxable_income:,} ≤ ₹{c.REBATE_87A_NEW_INCOME_LIMIT:,} → "
                f"rebate = min(tax ₹{tax_on_income:,}, "
                f"₹{c.REBATE_87A_NEW_MAX:,}) = ₹{rebate:,}"
            )
        else:
            rebate = 0
            note = (
                f"[Section 87A] New regime FY {fy}: taxable income "
                f"₹{taxable_income:,} > ₹{c.REBATE_87A_NEW_INCOME_LIMIT:,} → "
                f"no rebate."
            )

    return rebate, note
