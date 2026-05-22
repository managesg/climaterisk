"""Tests for Beanie document models."""

import uuid

import pytest
import pytest_asyncio

from seabridge.models.assessment import EvidenceItem, FeatureScoreRecord, HazardScore, RiskAssessment
from seabridge.models.company import Company
from seabridge.models.enums import DataType, HazardType, RiskRating, Scenario
from seabridge.models.property import Property


@pytest.mark.asyncio
async def test_company_round_trip():
    company = Company(
        name="Acme Corp",
        sector="Real Estate",
        industry="Commercial Real Estate",
        geography="USA",
        emissions=5000.0,
    )
    await company.insert()

    found = await Company.find_one({"company_id": company.company_id})
    assert found is not None
    assert found.name == "Acme Corp"
    assert found.emissions == 5000.0


@pytest.mark.asyncio
async def test_property_round_trip():
    cid = uuid.uuid4()
    prop = Property(
        company_id=cid,
        name="HQ Building",
        latitude=37.77,
        longitude=-122.42,
        asset_type="office",
        floor_area=5000.0,
        year_built=2005,
    )
    await prop.insert()

    found = await Property.find_one({"property_id": prop.property_id})
    assert found is not None
    assert found.latitude == 37.77
    assert found.year_built == 2005


@pytest.mark.asyncio
async def test_risk_assessment_data_type_tagging():
    """Every FeatureScoreRecord must have a DataType."""
    pid = uuid.uuid4()
    cid = uuid.uuid4()

    feature = FeatureScoreRecord(
        feature_name="fema_flood_zone",
        raw_value="AE",
        normalized_score=100.0,
        source="fema_nfhl",
        data_type=DataType.OBSERVED,
        is_available=True,
        confidence=0.9,
    )
    hazard_score = HazardScore(
        hazard=HazardType.INLAND_FLOOD,
        feature_scores=[feature],
        category_score=60.0,
        rating=RiskRating.MODERATE,
        confidence=0.9,
        top_drivers=["fema_flood_zone"],
        data_gaps=[],
    )

    assessment = RiskAssessment(
        property_id=pid,
        company_id=cid,
        scenario=Scenario.SSP2_45,
        time_horizon=2050,
        hazard_scores={"inland_flood": hazard_score},
        overall_score=60.0,
        overall_rating=RiskRating.MODERATE,
        confidence=0.9,
    )
    await assessment.insert()

    found = await RiskAssessment.find_one({"assessment_id": assessment.assessment_id})
    assert found is not None
    flood = found.hazard_scores["inland_flood"]
    assert flood.feature_scores[0].data_type == DataType.OBSERVED


def test_data_type_enum_coverage():
    """All required DataType values exist."""
    required = {"observed", "modeled", "scenario", "ai_generated", "user_provided", "missing"}
    actual = {dt.value for dt in DataType}
    assert required == actual
