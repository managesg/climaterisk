"""Tests for the wildfire hazard module."""
import pytest
from app.hazards.wildfire import WildfireHazard


@pytest.fixture
def hazard():
    return WildfireHazard()


def test_wildfire_name(hazard):
    assert hazard.name == "Wildfire"


def test_wildfire_ca_higher_than_midwest(hazard):
    """California should score higher than Illinois."""
    ca_props = {"state_province": "CA", "country": "USA", "latitude": 37.7, "longitude": -122.4}
    il_props = {"state_province": "IL", "country": "USA", "latitude": 41.8, "longitude": -87.6}
    ca = hazard.compute(37.7, -122.4, ca_props)
    il = hazard.compute(41.8, -87.6, il_props)
    assert ca["category_score"] > il["category_score"]


def test_wildfire_result_keys(hazard, sample_property_sf):
    result = hazard.compute(
        sample_property_sf["latitude"],
        sample_property_sf["longitude"],
        sample_property_sf,
    )
    assert "hazard" in result
    assert "category_score" in result
    assert "rating" in result
    assert "feature_scores" in result
    assert "top_drivers" in result
    assert "data_gaps" in result
    assert "recommended_action" in result


def test_wildfire_score_in_range(hazard, sample_property_sf):
    result = hazard.compute(
        sample_property_sf["latitude"],
        sample_property_sf["longitude"],
        sample_property_sf,
    )
    assert 0 <= result["category_score"] <= 100


def test_wildfire_feature_count(hazard, sample_property_sf):
    result = hazard.compute(
        sample_property_sf["latitude"],
        sample_property_sf["longitude"],
        sample_property_sf,
    )
    assert len(result["feature_scores"]) == 5


def test_wildfire_missing_data_shows_gap(hazard):
    """Missing canopy data should produce a data_gap entry."""
    props = {"state_province": "CA", "country": "USA"}  # no canopy
    result = hazard.compute(37.7, -122.4, props)
    gaps = result.get("data_gaps", [])
    # vegetation_fuel_proxy and slope_elevation_proxy should be flagged
    assert len(gaps) > 0
