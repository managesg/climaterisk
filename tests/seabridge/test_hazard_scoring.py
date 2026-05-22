"""Tests for the deterministic hazard scoring engine."""

import pytest

from seabridge.hazards.base import FeatureScore, HazardResult
from seabridge.hazards.scoring import (
    compute_category_score,
    compute_overall_physical_risk,
    rating_from_score,
)
from seabridge.hazards.wildfire import WildfireScorer
from seabridge.hazards.inland_flood import InlandFloodScorer
from seabridge.hazards.coastal_flood import CoastalFloodScorer
from seabridge.hazards.heat_stress import HeatStressScorer
from seabridge.hazards.drought import DroughtScorer
from seabridge.hazards.wind_hurricane import WindHurricaneScorer
from seabridge.models.enums import DataType, HazardType, RiskRating


# ─────────────────────── scoring formula tests ───────────────────────────────


def test_category_score_formula():
    """0.5 * max + 0.5 * mean(remaining)."""
    scores = [80.0, 40.0, 20.0]
    result = compute_category_score(scores)
    # max=80, remaining=[40,20], mean_remaining=30
    expected = 0.5 * 80.0 + 0.5 * 30.0
    assert abs(result - expected) < 0.01


def test_category_score_single_feature():
    assert compute_category_score([75.0]) == 75.0


def test_category_score_empty():
    assert compute_category_score([]) == 0.0


def test_category_score_two_features():
    result = compute_category_score([60.0, 40.0])
    expected = 0.5 * 60.0 + 0.5 * 40.0
    assert abs(result - expected) < 0.01


def test_rating_thresholds():
    assert rating_from_score(0) == RiskRating.VERY_LOW
    assert rating_from_score(20) == RiskRating.VERY_LOW
    assert rating_from_score(21) == RiskRating.LOW
    assert rating_from_score(40) == RiskRating.LOW
    assert rating_from_score(41) == RiskRating.MODERATE
    assert rating_from_score(60) == RiskRating.MODERATE
    assert rating_from_score(61) == RiskRating.HIGH
    assert rating_from_score(80) == RiskRating.HIGH
    assert rating_from_score(81) == RiskRating.VERY_HIGH
    assert rating_from_score(100) == RiskRating.VERY_HIGH


def test_overall_physical_risk_weights_highest():
    """Highest hazard is counted twice."""
    scores = {HazardType.WILDFIRE: 80.0, HazardType.INLAND_FLOOD: 40.0}
    result = compute_overall_physical_risk(scores)
    # max=80, total = 80 + 80 + 40 = 200, / 3 = 66.67
    expected = (80 + 80 + 40) / 3
    assert abs(result - expected) < 0.01


def test_overall_physical_risk_all_zero():
    scores = {HazardType.WILDFIRE: 0.0, HazardType.INLAND_FLOOD: 0.0}
    assert compute_overall_physical_risk(scores) == 0.0


def test_normalize():
    scorer = WildfireScorer()
    assert scorer.normalize(0, 0, 100) == 0.0
    assert scorer.normalize(100, 0, 100) == 100.0
    assert scorer.normalize(50, 0, 100) == 50.0
    assert scorer.normalize(-10, 0, 100) == 0.0  # clamped
    assert scorer.normalize(150, 0, 100) == 100.0  # clamped


# ─────────────────────── stub behaviour tests ────────────────────────────────


@pytest.mark.asyncio
async def test_wildfire_stub_marks_missing(sample_property_data):
    scorer = WildfireScorer()
    result = await scorer.score(37.77, -122.42, sample_property_data, "ssp245", 2050)
    assert isinstance(result, HazardResult)
    assert result.hazard_type == HazardType.WILDFIRE

    # Features with stub providers must be marked missing
    stub_features = [f for f in result.feature_scores if not f.is_available]
    assert len(stub_features) > 0
    for f in stub_features:
        assert f.data_type == DataType.MISSING


@pytest.mark.asyncio
async def test_inland_flood_returns_result(sample_property_data):
    scorer = InlandFloodScorer()
    result = await scorer.score(37.77, -122.42, sample_property_data, "ssp245", 2050)
    assert result.hazard_type == HazardType.INLAND_FLOOD
    assert 0.0 <= result.category_score <= 100.0
    assert len(result.feature_scores) == 8
    assert result.data_gaps  # expect some gaps since providers are stubs


@pytest.mark.asyncio
async def test_coastal_flood_returns_result(sample_property_data):
    scorer = CoastalFloodScorer()
    result = await scorer.score(37.77, -122.42, sample_property_data, "ssp245", 2050)
    assert result.hazard_type == HazardType.COASTAL_FLOOD
    assert len(result.feature_scores) == 7


@pytest.mark.asyncio
async def test_heat_stress_scenario_feature_available(sample_property_data):
    scorer = HeatStressScorer()
    result = await scorer.score(37.77, -122.42, sample_property_data, "ssp585", 2100)
    # NASA NEX-GDDP is a static summary — should always be available
    heat_feature = next(f for f in result.feature_scores if f.feature_name == "projected_extreme_heat_days")
    assert heat_feature.is_available is True
    assert heat_feature.data_type == DataType.SCENARIO


@pytest.mark.asyncio
async def test_drought_scorer(sample_property_data):
    scorer = DroughtScorer()
    result = await scorer.score(37.77, -122.42, sample_property_data, "ssp245", 2050)
    assert result.hazard_type == HazardType.DROUGHT
    assert 0.0 <= result.category_score <= 100.0


@pytest.mark.asyncio
async def test_wind_hurricane_returns_result(sample_property_data):
    scorer = WindHurricaneScorer()
    result = await scorer.score(25.77, -80.19, sample_property_data, "ssp245", 2050)
    assert result.hazard_type == HazardType.WIND_HURRICANE
    assert len(result.feature_scores) == 7


@pytest.mark.asyncio
async def test_all_feature_scores_have_data_type(sample_property_data):
    """Every FeatureScore must have an explicit DataType — never None."""
    scorers = [WildfireScorer(), InlandFloodScorer(), CoastalFloodScorer(),
               HeatStressScorer(), DroughtScorer(), WindHurricaneScorer()]
    for scorer in scorers:
        result = await scorer.score(37.77, -122.42, sample_property_data, "ssp245", 2050)
        for f in result.feature_scores:
            assert f.data_type is not None, f"{scorer.hazard_type}: {f.feature_name} missing data_type"
