"""Tests for the coastal flood hazard module."""
import pytest
from app.hazards.coastal_flood import CoastalFloodHazard


@pytest.fixture
def hazard():
    return CoastalFloodHazard()


def test_coastal_name(hazard):
    assert hazard.name == "Coastal Flood / Sea Level Rise"


def test_coastal_property_higher_than_inland(hazard, sample_property_florida, sample_property_inland):
    """Miami coastal property should score higher than Denver inland."""
    coastal = hazard.compute(
        sample_property_florida["latitude"],
        sample_property_florida["longitude"],
        sample_property_florida,
    )
    inland = hazard.compute(
        sample_property_inland["latitude"],
        sample_property_inland["longitude"],
        sample_property_inland,
    )
    assert coastal["category_score"] > inland["category_score"]


def test_inland_scores_near_zero(hazard, sample_property_inland):
    """Property > 50km from coast should have near-zero coastal score."""
    result = hazard.compute(
        sample_property_inland["latitude"],
        sample_property_inland["longitude"],
        sample_property_inland,
    )
    # Non-applicable features set to 0 for inland properties
    assert result["category_score"] < 30.0


def test_score_in_range(hazard, sample_property_florida):
    result = hazard.compute(
        sample_property_florida["latitude"],
        sample_property_florida["longitude"],
        sample_property_florida,
    )
    assert 0 <= result["category_score"] <= 100
