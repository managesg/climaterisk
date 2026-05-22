"""Tests for the portfolio physical risk scorer."""
import pytest
from app.hazards.scorer import score_property, score_portfolio, _overall_score


def test_score_property_returns_required_keys(sample_property_sf):
    result = score_property(
        lat=sample_property_sf["latitude"],
        lon=sample_property_sf["longitude"],
        property_attrs=sample_property_sf,
    )
    assert "overall_score" in result
    assert "overall_rating" in result
    assert "hazard_results" in result
    assert "top_hazards" in result
    assert "confidence" in result
    assert "data_gaps" in result
    assert "methodology_note" in result


def test_score_property_overall_in_range(sample_property_sf):
    result = score_property(
        lat=sample_property_sf["latitude"],
        lon=sample_property_sf["longitude"],
        property_attrs=sample_property_sf,
    )
    assert 0 <= result["overall_score"] <= 100


def test_score_has_six_hazards(sample_property_sf):
    result = score_property(
        lat=sample_property_sf["latitude"],
        lon=sample_property_sf["longitude"],
        property_attrs=sample_property_sf,
    )
    assert len(result["hazard_results"]) == 6


def test_florida_coastal_higher_than_denver(sample_property_florida, sample_property_inland):
    fl = score_property(
        lat=sample_property_florida["latitude"],
        lon=sample_property_florida["longitude"],
        property_attrs=sample_property_florida,
    )
    co = score_property(
        lat=sample_property_inland["latitude"],
        lon=sample_property_inland["longitude"],
        property_attrs=sample_property_inland,
    )
    assert fl["overall_score"] > co["overall_score"]


def test_score_portfolio_aggregates(sample_property_sf, sample_property_florida):
    props = [sample_property_sf, sample_property_florida]
    result = score_portfolio(properties=props)
    assert "properties" in result
    assert "portfolio_summary" in result
    assert result["portfolio_summary"]["property_count"] == 2
    assert "average_score" in result["portfolio_summary"]
    assert "max_score" in result["portfolio_summary"]


def test_score_portfolio_empty():
    result = score_portfolio(properties=[])
    assert result["properties"] == []


def test_overall_score_weights_max(sample_property_sf):
    """Highest hazard should be weighted twice."""
    scores = [{"category_score": 80}, {"category_score": 40}, {"category_score": 20}]
    result = _overall_score(scores)
    # weighted: [80*2, 40, 20] / 4 = 220/4 = 55
    assert result == pytest.approx(55.0)


def test_rating_very_low():
    result = score_property(
        lat=65.0, lon=25.0,  # High-latitude, low-risk
        property_attrs={"distance_to_coast_km": 200, "elevation_m": 300, "fema_flood_zone": "X"},
    )
    # Shouldn't be very high risk
    assert result["overall_score"] < 80


def test_scenario_stored_in_result(sample_property_sf):
    result = score_property(
        lat=sample_property_sf["latitude"],
        lon=sample_property_sf["longitude"],
        property_attrs=sample_property_sf,
        scenario="SSP5-8.5",
        time_horizon="2050",
    )
    # Scenario should be recorded in results
    for h in result["hazard_results"]:
        assert h.get("scenario") == "SSP5-8.5"
        assert h.get("time_horizon") == "2050"
