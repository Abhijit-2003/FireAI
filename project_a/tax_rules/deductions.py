"""
Deduction calculators for the Indian Income Tax Computation Engine.

Each function returns (allowed_amount: int, audit_note: str).
All monetary values are whole rupees (int).

References:
    - Section 10(13A), Rule 2A — HRA Exemption
    - Section 16(ia) — Standard Deduction
    - Section 80C — Investments / expenditure deduction
    - Section 80CCD(1B) — Additional NPS contribution
    - Section 80D — Health insurance premium
    - Section 24(b) — Interest on borrowed capital (self-occupied property)
"""

from __future__ import annotations

from project_a.tax_rules import constants as c
from project_a.tax_rules import constants_2025_26 as c26


def calc_standard_deduction(
    regime: str,
    fy: str = "2024-25",
) -> tuple[int, str]:
    """
    Compute standard deduction under Section 16(ia).

    Args:
        regime: "old" or "new".
        fy: Financial year string, e.g. "2024-25" or "2025-26".

    Returns:
        (deduction_amount, audit_note)

    Rules:
        - Old regime: ₹50,000 for all FYs covered.
        - New regime FY 2024-25: ₹75,000.
        - New regime FY 2025-26: ₹75,000.
    """
    if regime == "old":
        amount = c.STANDARD_DEDUCTION_OLD
        note = (
            f"[Section 16(ia)] Standard deduction (old regime, FY {fy}): "
            f"₹{amount:,}"
        )
    else:
        if fy == "2025-26":
            amount = c26.STANDARD_DEDUCTION_NEW
        else:
            amount = c.STANDARD_DEDUCTION_NEW
        note = (
            f"[Section 16(ia)] Standard deduction (new regime, FY {fy}): "
            f"₹{amount:,}"
        )
    return amount, note


def calc_hra_exemption(
    basic: int,
    da: int,
    hra_received: int,
    rent_paid: int,
    is_metro: bool,
) -> tuple[int, str]:
    """
    Compute HRA exemption under Section 10(13A) read with Rule 2A.

    Only applicable under the **old regime**.

    The exempt amount is the **minimum** of:
        1. Actual HRA received from the employer.
        2. 50% of (Basic + DA) if metro, else 40%.
        3. Rent paid − 10% of (Basic + DA).

    Args:
        basic: Basic salary per annum (₹).
        da: Dearness Allowance per annum (₹).
        hra_received: HRA received from employer per annum (₹).
        rent_paid: Actual rent paid per annum (₹).
        is_metro: Whether city is Delhi, Mumbai, Kolkata, or Chennai.

    Returns:
        (exempt_amount, audit_note)
    """
    if hra_received == 0 or rent_paid == 0:
        return 0, "[Section 10(13A)] HRA exemption: ₹0 (no HRA/rent claimed)."

    basic_plus_da = basic + da
    metro_pct = c.HRA_METRO_PERCENT if is_metro else c.HRA_NON_METRO_PERCENT

    component_1 = hra_received
    component_2 = (basic_plus_da * metro_pct) // 100
    component_3 = max(0, rent_paid - (basic_plus_da * 10) // 100)

    exempt = min(component_1, component_2, component_3)

    city_type = "metro" if is_metro else "non-metro"
    note = (
        f"[Section 10(13A), Rule 2A] HRA exemption ({city_type}): "
        f"min(actual HRA ₹{component_1:,}, "
        f"{metro_pct}% of (Basic+DA) ₹{component_2:,}, "
        f"Rent−10%(Basic+DA) ₹{component_3:,}) = ₹{exempt:,}"
    )
    return exempt, note


def calc_section_80c(amount: int) -> tuple[int, str]:
    """
    Compute deduction under Section 80C.

    Covers: PPF, ELSS, EPF, LIC, NSC, tax-saving FD, home loan principal, etc.
    Maximum deduction: ₹1,50,000.

    Only applicable under the **old regime**.

    Args:
        amount: Total qualifying investments/expenditure (₹).

    Returns:
        (allowed_amount, audit_note)
    """
    allowed = min(amount, c.SECTION_80C_LIMIT)
    note = (
        f"[Section 80C] Claimed ₹{amount:,}, "
        f"allowed ₹{allowed:,} (limit ₹{c.SECTION_80C_LIMIT:,})."
    )
    return allowed, note


def calc_section_80ccd_1b(amount: int) -> tuple[int, str]:
    """
    Compute deduction under Section 80CCD(1B).

    Additional NPS contribution over and above Section 80C.
    Maximum deduction: ₹50,000.

    Only applicable under the **old regime**.

    Args:
        amount: NPS contribution claimed (₹).

    Returns:
        (allowed_amount, audit_note)
    """
    allowed = min(amount, c.SECTION_80CCD_1B_LIMIT)
    note = (
        f"[Section 80CCD(1B)] Claimed ₹{amount:,}, "
        f"allowed ₹{allowed:,} (limit ₹{c.SECTION_80CCD_1B_LIMIT:,})."
    )
    return allowed, note


def calc_section_80d(
    self_premium: int,
    parents_premium: int,
    is_self_senior: bool,
    are_parents_senior: bool,
) -> tuple[int, int, str]:
    """
    Compute deduction under Section 80D for health insurance premiums.

    Limits (per annum):
        - Self/family: ₹25,000 (below 60) / ₹50,000 (senior 60+)
        - Parents:     ₹25,000 (below 60) / ₹50,000 (senior 60+)

    Only applicable under the **old regime**.

    Args:
        self_premium: Premium paid for self/spouse/children (₹).
        parents_premium: Premium paid for parents (₹).
        is_self_senior: Is self/spouse a senior citizen?
        are_parents_senior: Are parents senior citizens?

    Returns:
        (self_allowed, parents_allowed, audit_note)
    """
    self_limit = (
        c.SECTION_80D_SELF_SENIOR if is_self_senior else c.SECTION_80D_SELF_BELOW_60
    )
    parents_limit = (
        c.SECTION_80D_PARENTS_SENIOR
        if are_parents_senior
        else c.SECTION_80D_PARENTS_BELOW_60
    )

    self_allowed = min(self_premium, self_limit)
    parents_allowed = min(parents_premium, parents_limit)

    note = (
        f"[Section 80D] Self: claimed ₹{self_premium:,}, "
        f"allowed ₹{self_allowed:,} (limit ₹{self_limit:,}, "
        f"senior={is_self_senior}). "
        f"Parents: claimed ₹{parents_premium:,}, "
        f"allowed ₹{parents_allowed:,} (limit ₹{parents_limit:,}, "
        f"senior={are_parents_senior})."
    )
    return self_allowed, parents_allowed, note


def calc_home_loan_interest(interest: int) -> tuple[int, str]:
    """
    Compute deduction under Section 24(b) for interest on home loan.

    For a **self-occupied property**, maximum deduction is ₹2,00,000 per annum.

    Only applicable under the **old regime**.

    Args:
        interest: Interest paid on home loan per annum (₹).

    Returns:
        (allowed_amount, audit_note)
    """
    allowed = min(interest, c.SECTION_24B_LIMIT)
    note = (
        f"[Section 24(b)] Home loan interest: claimed ₹{interest:,}, "
        f"allowed ₹{allowed:,} (limit ₹{c.SECTION_24B_LIMIT:,} "
        f"for self-occupied property)."
    )
    return allowed, note
