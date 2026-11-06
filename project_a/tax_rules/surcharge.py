"""
Surcharge calculator with marginal relief.

References:
    - Section 2(9), Finance Act
    - Paragraph A / B of Part I of the First Schedule to the Finance Act
    - Section 115BAC (new regime surcharge cap at 25%)

Surcharge thresholds (applicable on total income):
    ₹50,00,000  → 10% surcharge on income tax
    ₹1,00,00,000 → 15% surcharge on income tax
    ₹2,00,00,000 → 25% surcharge on income tax
    ₹5,00,00,000 → 37% surcharge on income tax

New regime: maximum surcharge rate is capped at 25%.

Marginal relief:
    When income marginally exceeds a surcharge threshold, the total tax
    (tax + surcharge) should not exceed the total tax at the threshold
    plus the excess income over the threshold. This prevents a situation
    where earning ₹1 more causes a disproportionate tax jump.
"""

from __future__ import annotations

from project_a.tax_rules import constants as c
from project_a.tax_rules.constants import TaxSlab


def _compute_tax_on_slabs(taxable_income: int, slabs: list[TaxSlab]) -> int:
    """Compute income tax using the given slab schedule. Uses Section 288B rounding."""
    tax_paise = 0
    prev_upper = 0
    for slab in slabs:
        if slab.upper is None:
            # Last slab — no upper bound
            if taxable_income > prev_upper:
                tax_paise += (taxable_income - prev_upper) * slab.rate
            break
        if taxable_income <= prev_upper:
            break
        taxable_in_slab = min(taxable_income, slab.upper) - prev_upper
        tax_paise += taxable_in_slab * slab.rate
        prev_upper = slab.upper
    return (tax_paise + 50) // 100


def _get_applicable_surcharge_rate(
    taxable_income: int,
    is_new_regime: bool,
) -> int:
    """Return the surcharge rate (%) applicable for the given income."""
    applicable_rate = 0
    for threshold, rate in c.SURCHARGE_SLABS:
        if taxable_income > threshold:
            applicable_rate = rate
    if is_new_regime:
        applicable_rate = min(applicable_rate, c.NEW_REGIME_MAX_SURCHARGE_RATE)
    return applicable_rate


def calc_surcharge(
    taxable_income: int,
    tax_after_rebate: int,
    regime: str,
    slabs: list[TaxSlab],
) -> tuple[int, str]:
    """
    Compute surcharge on income tax with marginal relief.

    Args:
        taxable_income: Total taxable income (₹).
        tax_after_rebate: Tax after Section 87A rebate (₹).
        regime: "old" or "new".
        slabs: The tax slab schedule used (needed for marginal relief calc).

    Returns:
        (surcharge_amount, audit_note)
    """
    if tax_after_rebate == 0:
        return 0, "[Surcharge] No surcharge — tax after rebate is ₹0."

    is_new_regime = regime == "new"
    applicable_rate = _get_applicable_surcharge_rate(taxable_income, is_new_regime)

    if applicable_rate == 0:
        return 0, (
            f"[Surcharge] Taxable income ₹{taxable_income:,} does not exceed "
            f"₹{c.SURCHARGE_SLABS[0][0]:,} — no surcharge."
        )

    # Compute surcharge without marginal relief (Section 288B round)
    surcharge_raw = round(tax_after_rebate * applicable_rate / 100)

    # --- Marginal relief calculation ---
    # Find the threshold that was just crossed
    crossed_threshold = 0
    for threshold, rate in c.SURCHARGE_SLABS:
        if taxable_income > threshold:
            crossed_threshold = threshold

    # Tax at the threshold (where surcharge was at the lower rate)
    tax_at_threshold = _compute_tax_on_slabs(crossed_threshold, slabs)
    # Surcharge rate at the threshold (the rate just below)
    lower_rate = 0
    for threshold, rate in c.SURCHARGE_SLABS:
        if crossed_threshold > threshold:
            lower_rate = rate
    if is_new_regime:
        lower_rate = min(lower_rate, c.NEW_REGIME_MAX_SURCHARGE_RATE)

    surcharge_at_threshold = round(tax_at_threshold * lower_rate / 100)
    total_at_threshold = tax_at_threshold + surcharge_at_threshold

    excess_income = taxable_income - crossed_threshold
    # With marginal relief, total tax + surcharge should not exceed:
    # total_at_threshold + excess_income
    total_with_surcharge_raw = tax_after_rebate + surcharge_raw
    marginal_ceiling = total_at_threshold + excess_income

    if total_with_surcharge_raw > marginal_ceiling:
        # Apply marginal relief
        surcharge_with_relief = max(0, marginal_ceiling - tax_after_rebate)
        marginal_relief = surcharge_raw - surcharge_with_relief
        note = (
            f"[Surcharge] Rate {applicable_rate}% on tax ₹{tax_after_rebate:,} "
            f"= ₹{surcharge_raw:,}. "
            f"Marginal relief applied: tax+surcharge (₹{total_with_surcharge_raw:,}) "
            f"exceeds ceiling (₹{marginal_ceiling:,} = tax@₹{crossed_threshold:,} "
            f"+ surcharge@{lower_rate}% + excess ₹{excess_income:,}). "
            f"Relief = ₹{marginal_relief:,}. "
            f"Surcharge after relief = ₹{surcharge_with_relief:,}."
        )
        return surcharge_with_relief, note
    else:
        note = (
            f"[Surcharge] Rate {applicable_rate}% on tax ₹{tax_after_rebate:,} "
            f"= ₹{surcharge_raw:,}. No marginal relief needed."
        )
        return surcharge_raw, note
