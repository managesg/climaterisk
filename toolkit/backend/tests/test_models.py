"""Tests for Pydantic data models."""
import pytest
from app.models.company import Company, CompanyCreate
from app.models.property import Property, PropertyCreate
from app.models.common import score_to_rating, RiskRating, confidence_from_completeness, ConfidenceLevel
from app.models.agent_run import AgentRun, AgentRunState


def test_score_to_rating_boundaries():
    assert score_to_rating(0) == RiskRating.VERY_LOW
    assert score_to_rating(20) == RiskRating.VERY_LOW
    assert score_to_rating(21) == RiskRating.LOW
    assert score_to_rating(40) == RiskRating.LOW
    assert score_to_rating(41) == RiskRating.MODERATE
    assert score_to_rating(60) == RiskRating.MODERATE
    assert score_to_rating(61) == RiskRating.HIGH
    assert score_to_rating(80) == RiskRating.HIGH
    assert score_to_rating(81) == RiskRating.VERY_HIGH
    assert score_to_rating(100) == RiskRating.VERY_HIGH


def test_confidence_from_completeness():
    assert confidence_from_completeness(10, 10) == ConfidenceLevel.HIGH
    assert confidence_from_completeness(7, 10) == ConfidenceLevel.MEDIUM
    assert confidence_from_completeness(4, 10) == ConfidenceLevel.LOW
    assert confidence_from_completeness(2, 10) == ConfidenceLevel.VERY_LOW
    assert confidence_from_completeness(0, 0) == ConfidenceLevel.VERY_LOW


def test_company_create_generates_id():
    co = Company(name="Test Co", sector="RE", industry="Office", geography="USA")
    assert co.company_id is not None
    assert len(co.company_id) > 0


def test_property_create_validates_lat():
    with pytest.raises(Exception):
        PropertyCreate(
            company_id="co-1",
            name="Bad property",
            latitude=100,  # invalid
            longitude=0,
            asset_type="Office",
        )


def test_property_create_validates_lon():
    with pytest.raises(Exception):
        PropertyCreate(
            company_id="co-1",
            name="Bad property",
            latitude=0,
            longitude=200,  # invalid
            asset_type="Office",
        )


def test_property_valid():
    prop = Property(
        company_id="co-1",
        name="HQ",
        latitude=37.77,
        longitude=-122.42,
        asset_type="Office",
    )
    assert prop.property_id is not None
    assert prop.latitude == 37.77


def test_agent_run_default_state():
    run = AgentRun(company_id="co-1", property_ids=["p-1"], task_type="full_assessment")
    assert run.state == AgentRunState.PENDING
    assert run.run_id is not None
