import pytest

from app.services.pricing_engine import (
    MAX_WEIGHT_KG,
    MIN_WEIGHT_KG,
    price_per_kg,
    total_idr,
)

TIERS = ["fresh", "sell_today", "wilted"]
IN_RANGE_WEIGHTS = [0.05, 1.0, 2.37, 9.99, 10.0]
OUT_OF_RANGE_WEIGHTS = [0, 0.049, 10.01]

# Hand-computed oracle: base 40_000 IDR/kg, multipliers 1.00 / 0.80 / 0.55,
# total rounded to nearest 100 IDR with halves up.
EXPECTED_TOTALS = {
    ("fresh", 0.05): 2_000,
    ("fresh", 1.0): 40_000,
    ("fresh", 2.37): 94_800,
    ("fresh", 9.99): 399_600,
    ("fresh", 10.0): 400_000,
    ("sell_today", 0.05): 1_600,
    ("sell_today", 1.0): 32_000,
    ("sell_today", 2.37): 75_800,   # 75_840 -> nearest 100
    ("sell_today", 9.99): 319_700,  # 319_680 -> nearest 100
    ("sell_today", 10.0): 320_000,
    ("wilted", 0.05): 1_100,
    ("wilted", 1.0): 22_000,
    ("wilted", 2.37): 52_100,   # 52_140 -> nearest 100
    ("wilted", 9.99): 219_800,  # 219_780 -> nearest 100
    ("wilted", 10.0): 220_000,
}


@pytest.mark.parametrize("tier", TIERS)
@pytest.mark.parametrize("weight", IN_RANGE_WEIGHTS)
def test_total_idr_matches_oracle(tier, weight):
    assert total_idr(tier, weight) == EXPECTED_TOTALS[(tier, weight)]


@pytest.mark.parametrize("tier", TIERS)
@pytest.mark.parametrize("weight", OUT_OF_RANGE_WEIGHTS)
def test_out_of_range_weight_raises(tier, weight):
    with pytest.raises(ValueError):
        total_idr(tier, weight)


@pytest.mark.parametrize("weight", [MIN_WEIGHT_KG, MAX_WEIGHT_KG])
def test_range_bounds_inclusive(weight):
    assert total_idr("fresh", weight) > 0


@pytest.mark.parametrize("tier", ["Fresh", "FRESH", "rotten", "", "sell-today", None])
def test_unknown_tier_raises(tier):
    with pytest.raises(ValueError):
        price_per_kg(tier)
    with pytest.raises(ValueError):
        total_idr(tier, 1.0)


def test_multiplier_exactness():
    assert price_per_kg("fresh") == 40_000
    assert price_per_kg("sell_today") == 32_000
    assert price_per_kg("wilted") == 22_000


def test_rounding_boundaries():
    # 40_000 * 0.05125 = 2_050 -> exactly half a hundred -> rounds up
    assert total_idr("fresh", 0.05125) == 2_100
    # 40_000 * 0.0512 = 2_048 -> rounds down
    assert total_idr("fresh", 0.0512) == 2_000
    # 40_000 * 0.0513 = 2_052 -> rounds up
    assert total_idr("fresh", 0.0513) == 2_100


def test_totals_are_ints():
    for tier in TIERS:
        assert isinstance(total_idr(tier, 1.23), int)
