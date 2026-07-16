"""The numbers authority (R1): every price in the product originates here.

Pure functions, zero I/O, stdlib only. The LLM never generates numbers —
it only ever restates values computed by this module.
"""

from decimal import ROUND_HALF_UP, Decimal

BASE_PRICE_IDR_PER_KG = 40_000  # demo constant; "configurable per coop per day" in Q&A
TIER_MULTIPLIER = {"fresh": 1.00, "sell_today": 0.80, "wilted": 0.55}
MIN_WEIGHT_KG = 0.05
MAX_WEIGHT_KG = 10.0  # load cell ceiling


def price_per_kg(tier: str) -> int:
    """IDR per kilogram for a grade tier. Raises ValueError on unknown tier."""
    if tier not in TIER_MULTIPLIER:
        raise ValueError(f"unknown tier: {tier!r}")
    return int(
        (Decimal(BASE_PRICE_IDR_PER_KG) * Decimal(str(TIER_MULTIPLIER[tier]))).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


def total_idr(tier: str, weight_kg: float) -> int:
    """Total payout in IDR, rounded to the nearest 100 IDR (half rounds up).

    Raises ValueError on unknown tier or weight outside [MIN_WEIGHT_KG, MAX_WEIGHT_KG].
    """
    per_kg = price_per_kg(tier)
    if not MIN_WEIGHT_KG <= weight_kg <= MAX_WEIGHT_KG:
        raise ValueError(
            f"weight {weight_kg} kg outside [{MIN_WEIGHT_KG}, {MAX_WEIGHT_KG}]"
        )
    # Decimal(str(...)) sidesteps float artifacts so rounding is reproducible.
    raw = Decimal(str(weight_kg)) * per_kg
    hundreds = (raw / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(hundreds) * 100
