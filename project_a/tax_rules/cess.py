"""
Health & Education Cess calculator.

References:
    - Section 2(9), Finance Act
    - 4% Health & Education Cess on (Income Tax + Surcharge)

The cess is computed on the aggregate of income tax and surcharge.
"""

from __future__ import annotations

from project_a.tax_rules import constants as c


def calc_cess(tax_plus_surcharge: int) -> tuple[int, str]:
    """
    Compute 4% Health & Education Cess.

    Args:
        tax_plus_surcharge: Income tax + surcharge (₹).

    Returns:
        (cess_amount, audit_note)
    """
    # Section 288B of Income Tax Act: Round to nearest rupee (>=50 paise rounds up)
    cess = round(tax_plus_surcharge * c.CESS_RATE / 100)
    note = (
        f"[Health & Education Cess] {c.CESS_RATE}% on "
        f"₹{tax_plus_surcharge:,} = ₹{cess:,}."
    )
    return cess, note
