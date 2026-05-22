"""Tests for heat stress hazard module."""
import pytest
from app.hazards.heat_stress import HeatStressHazard


@pytest.fixture
def hazard():
    return HeatStressHazard()


def test_heat_name(hazard):
    assert hazard.name == "Heat Stress"


def test_tropical_higher_than_polar(hazard):
    """Tropical latitude should score higher than high-latitude."""
    tropical = hazard.compute(15.0, 30.0, {})
    polar = hazard.compute(65.0, 25.0, {})
    assert tropical["category_score"] > polar["category_score"]


def test_old_building_increases_score(hazard):
    new_props = {"year_built": 2020, "construction_type": "Concrete"}
    old_props = {"year_built": 1960, "construction_type": "Wood Frame"}
    new_result = hazard.compute(35.0, -90.0, new_props)
    old_result = hazard.compute(35.0, -90.0, old_props)
    assert old_result["category_score"] >= new_result["category_score"]


def test_score_in_range(hazard, sample_property_florida):
    result = hazard.compute(
        sample_property_florida["latitude"],
        sample_property_florida["longitude"],
        sample_property_florida,
    )
    assert 0 <= result["category_score"] <= 100


def test_uhi_increases_with_impervious(hazard):
    high_impervious = {"impervious_surface_pct": 95.0, "tree_canopy_pct": 2.0}
    low_impervious = {"impervious_surface_pct": 20.0, "tree_canopy_pct": 40.0}
    high = hazard.compute(40.0, -74.0, high_impervious)
    low = hazard.compute(40.0, -74.0, low_impervious)
    assert high["category_score"] >= low["category_score"]
