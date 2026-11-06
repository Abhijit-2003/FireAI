"""
LLM-Compiled Rules for Indian Income Tax.

This module was compiled once from the official rule text by LLM (Gemini),
reviewed by an engineer, and executes deterministically without runtime LLM calls.

References:
    - Income Tax Act, 1961
    - Finance Act, 2024 / 2025
"""

from __future__ import annotations
from typing import Any, Tuple, List


def compiled_standard_deduction(regime: str, fy: str = "2024-25") -> int:
    """[Section 16(ia)] Standard deduction: 50,000 for old; 75,000 for new."""
    if regime.lower() == "old":
        return 50000
    return 75000


def compiled_hra_exemption(
    basic: int,
    da: int,
    hra_received: int,
    rent_paid: int,
    is_metro: bool
) -> Tuple[int, str]:
    """[Section 10(13A), Rule 2A] HRA exemption calculation."""
    if hra_received <= 0 or rent_paid <= 0:
        return 0, "[Section 10(13A)] HRA: 0"
    bda = basic + da
    m_pct = 50 if is_metro else 40
    c1 = hra_received
    c2 = (bda * m_pct) // 100
    c3 = max(0, rent_paid - (bda * 10) // 100)
    exempt = min(c1, c2, c3)
    return exempt, f"[Section 10(13A)] HRA Exempt: {exempt} (min of {c1}, {c2}, {c3})"


def compiled_deductions_chapter_via(inp: dict[str, Any]) -> Tuple[int, List[str]]:
    """[Chapter VI-A] Deductions under Sections 80C, 80CCD(1B), 80D."""
    total = 0
    audit = []

    # 80C: capped at 150,000
    c80 = min(inp.get("investment_80c", inp.get("section_80c", 0)), 150000)
    if c80 > 0:
        total += c80
        audit.append(f"[Section 80C] Allowed: ₹{c80:,}")

    # 80CCD(1B): capped at 50,000
    ccd = min(inp.get("investment_80ccd_1b", inp.get("section_80ccd_1b", 0)), 50000)
    if ccd > 0:
        total += ccd
        audit.append(f"[Section 80CCD(1B)] Allowed: ₹{ccd:,}")

    # 80D: health insurance
    age = inp.get("age", 30)
    self_cap = 50000 if (age >= 60 or inp.get("is_self_senior", False)) else 25000
    par_cap = 50000 if inp.get("are_parents_senior", inp.get("parents_senior_citizen", False)) else 25000

    d_self = min(inp.get("health_insurance_self", inp.get("section_80d_self", 0)), self_cap)
    d_par = min(inp.get("health_insurance_parents", inp.get("section_80d_parents", 0)), par_cap)
    d80 = d_self + d_par
    if d80 > 0:
        total += d80
        audit.append(f"[Section 80D] Allowed: ₹{d80:,} (Self: {d_self}, Parents: {d_par})")

    # Other deductions
    other_ded = inp.get("other_deductions_old", 0)
    if other_ded > 0:
        total += other_ded
        audit.append(f"[Chapter VI-A Other] Allowed: ₹{other_ded:,}")

    return total, audit


def compiled_old_slab_tax(taxable: int, age: int = 30) -> Tuple[int, List[str]]:
    """Compute tax on old regime slabs with Section 288B rounding."""
    exempt = 500000 if age >= 80 else (300000 if age >= 60 else 250000)
    if taxable <= exempt:
        return 0, [f"Taxable income ₹{taxable:,} <= exemption ₹{exempt:,}: ₹0 tax"]

    paise = 0
    audit = []
    if exempt < 500000 and taxable > exempt:
        chunk = min(taxable, 500000) - exempt
        p = chunk * 5
        paise += p
        audit.append(f"Slab ₹{exempt:,}-₹5,00,000 @ 5%: ₹{chunk:,} = ₹{(p+50)//100:,}")

    if taxable > 500000:
        chunk = min(taxable, 1000000) - 500000
        p = chunk * 20
        paise += p
        audit.append(f"Slab ₹5,00,000-₹10,00,000 @ 20%: ₹{chunk:,} = ₹{(p+50)//100:,}")

    if taxable > 1000000:
        chunk = taxable - 1000000
        p = chunk * 30
        paise += p
        audit.append(f"Slab > ₹10,00,000 @ 30%: ₹{chunk:,} = ₹{(p+50)//100:,}")

    tax = (paise + 50) // 100
    return tax, audit


def compiled_new_slab_tax(taxable: int, fy: str = "2024-25") -> Tuple[int, List[str]]:
    """Compute tax on new regime slabs (FY 2024-25 or FY 2025-26)."""
    if fy == "2025-26":
        # FY 2025-26 slabs: 0-4L, 4-8L(5%), 8-12L(10%), 12-16L(15%), 16-20L(20%), 20-24L(25%), >24L(30%)
        slabs = [
            (0, 400000, 0),
            (400000, 800000, 5),
            (800000, 1200000, 10),
            (1200000, 1600000, 15),
            (1600000, 2000000, 20),
            (2000000, 2400000, 25),
            (2400000, 10**12, 30),
        ]
    else:
        # FY 2024-25 slabs: 0-3L, 3-7L(5%), 7-10L(10%), 10-12L(15%), 12-15L(20%), >15L(30%)
        slabs = [
            (0, 300000, 0),
            (300000, 700000, 5),
            (700000, 1000000, 10),
            (1000000, 1200000, 15),
            (1200000, 1500000, 20),
            (1500000, 10**12, 30),
        ]

    paise = 0
    audit = []
    for lo, hi, r in slabs:
        if taxable > lo and r > 0:
            chunk = min(taxable, hi) - lo
            p = chunk * r
            paise += p
            audit.append(f"Slab ₹{lo:,}-₹{hi:,} @ {r}%: ₹{chunk:,} = ₹{(p+50)//100:,}")

    tax = (paise + 50) // 100
    return tax, audit


def compiled_surcharge_and_relief(tax: int, taxable: int, is_new: bool, fy: str = "2024-25") -> Tuple[int, str]:
    """Compute surcharge with marginal relief per IT Act First Schedule."""
    if tax <= 0:
        return 0, "No surcharge on 0 tax"

    if taxable <= 5000000:
        return 0, "Taxable income <= 50L: No surcharge"

    if taxable <= 10000000:
        rate, thr, prev = 0.10, 5000000, 0
    elif taxable <= 20000000:
        rate, thr, prev = 0.15, 10000000, 0.10
    elif taxable <= 50000000:
        rate, thr, prev = 0.25, 20000000, 0.15
    else:
        rate = 0.25 if is_new else 0.37
        thr = 50000000
        prev = 0.25

    raw_surcharge = round(tax * rate)
    slab_fn = (lambda t: compiled_new_slab_tax(t, fy)[0]) if is_new else (lambda t: compiled_old_slab_tax(t, 30)[0])
    t_thr = slab_fn(thr)
    tot_thr = t_thr + round(t_thr * prev)
    max_total = tot_thr + (taxable - thr)

    if tax + raw_surcharge > max_total:
        relief_sc = max(0, max_total - tax)
        return relief_sc, f"Surcharge with marginal relief: ₹{relief_sc:,} (rate {int(rate*100)}%)"

    return raw_surcharge, f"Surcharge: ₹{raw_surcharge:,} @ {int(rate*100)}%"

