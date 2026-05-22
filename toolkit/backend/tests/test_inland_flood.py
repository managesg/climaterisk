"""Tests for the inland flood hazard module."""
import pytest
from app.hazards.inland_flood import InlandFloodHazard


@pytest.fixture
def hazard():
    return InlandFloodHazard()


def test_inland_flood_name(hazard):
    assert hazard.name == "Inland Flood"


def test_fema_ae_zone_higher_than_x(hazard, sample_property_florida, sample_property_sf):
    """FEMA AE zone should score higher than FEMA X zone."""
    ae = hazard.compute(
        sample_property_florida["latitude"],
        sample_property_florida["longitude"],
        sample_property_florida,
    )
    x = hazard.compute(
        sample_property_sf["latitude"],
        sample_property_sf["longitude"],
        sample_property_sf,
    )
    assert ae["category_score"] > x["category_score"]


def test_score_in_range(hazard, sample_property_florida):
    result = hazard.compute(
        sample_property_florida["latitude"],
        sample_property_florida["longitude"],
        sample_property_florida,
    )
    assert 0 <= result["category_score"] <= 100


def test_river_proximity_increases_score(hazard):
    """Closer river = higher score."""
    close_props = {"distance_to_river_km": 0.05, "fema_flood_zone": "X"}
    far_props = {"distance_to_river_km": 20.0, "fema_flood_zone": "X"}
    close = hazard.compute(37.0, -77.0, close_props)
    far = hazard.compute(37.0, -77.0, far_props)
    assert close["category_score"] >= far["category_score"]


def test_high_elevation_lowers_score(hazard):
    """Higher elevation should reduce flood score."""
    low_props = {"elevation_m": 2.0}
    high_props = {"elevation_m": 500.0}
    low = hazard.compute(37.0, -77.0, low_props)
    high = hazard.compute(37.0, -77.0, high_props)
    assert low["category_score"] >= high["category_score"]
