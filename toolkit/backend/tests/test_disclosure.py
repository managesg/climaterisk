"""Tests for disclosure generator."""
import pytest
from app.disclosure.generator import DisclosureGenerator, DISCLOSURE_DISCLAIMER


@pytest.fixture
def generator():
    return DisclosureGenerator()


@pytest.fixture
def sample_physical_results(sample_property_sf, sample_property_florida):
    from app.hazards.scorer import score_property
    sf = score_property(
        lat=sample_property_sf["latitude"],
        lon=sample_property_sf["longitude"],
        property_attrs=sample_property_sf,
        scenario="SSP2-4.5",
        time_horizon="2050",
    )
    sf["property_id"] = "prop-sf-001"
    sf["property_name"] = "SF Office HQ"
    fl = score_property(
        lat=sample_property_florida["latitude"],
        lon=sample_property_florida["longitude"],
        property_attrs=sample_property_florida,
        scenario="SSP2-4.5",
        time_horizon="2050",
    )
    fl["property_id"] = "prop-fl-001"
    fl["property_name"] = "Miami Retail"
    return [sf, fl]


def test_disclosure_returns_six_sections(generator, sample_company, sample_physical_results):
    result = generator.generate(
        company=sample_company,
        properties=[],
        physical_risk_results=sample_physical_results,
        transition_risks=[],
        nature_risks=[],
        opportunities=[],
        scenario="SSP2-4.5",
        time_horizon="2050",
        confidence=0.6,
        data_gaps=["Missing elevation data for SF property"],
        assumptions=[],
    )
    assert "1_executive_summary" in result
    assert "2_governance" in result
    assert "3_strategy" in result
    assert "4_risk_management" in result
    assert "5_metrics_and_targets" in result
    assert "6_appendix" in result


def test_disclosure_includes_disclaimer(generator, sample_company, sample_physical_results):
    result = generator.generate(
        company=sample_company,
        properties=[],
        physical_risk_results=sample_physical_results,
        transition_risks=[],
        nature_risks=[],
        opportunities=[],
        scenario="SSP2-4.5",
        time_horizon="2050",
        confidence=0.6,
        data_gaps=[],
        assumptions=[],
    )
    assert result["disclaimer"] == DISCLOSURE_DISCLAIMER


def test_framework_alignment(generator, sample_company, sample_physical_results):
    result = generator.generate(
        company=sample_company,
        properties=[],
        physical_risk_results=sample_physical_results,
        transition_risks=[],
        nature_risks=[],
        opportunities=[],
        scenario="SSP2-4.5",
        time_horizon="2050",
        confidence=0.7,
        data_gaps=[],
        assumptions=[],
    )
    assert "ISSB IFRS S2" in result["framework_alignment"]
    assert "TCFD" in result["framework_alignment"]
    assert "TNFD" in result["framework_alignment"]


def test_ai_generated_label_in_executive_summary(generator, sample_company, sample_physical_results):
    result = generator.generate(
        company=sample_company,
        properties=[],
        physical_risk_results=sample_physical_results,
        transition_risks=[],
        nature_risks=[],
        opportunities=[],
        scenario="SSP2-4.5",
        time_horizon="2050",
        confidence=0.7,
        data_gaps=[],
        assumptions=[],
    )
    exec_summary = result["1_executive_summary"]
    assert exec_summary.get("data_source_type") == "ai_generated"
    assert "[AI-GENERATED INTERPRETATION]" in exec_summary.get("narrative", "")


def test_data_gaps_preserved(generator, sample_company, sample_physical_results):
    gaps = ["Missing elevation data", "FEMA zone not provided"]
    result = generator.generate(
        company=sample_company,
        properties=[],
        physical_risk_results=sample_physical_results,
        transition_risks=[],
        nature_risks=[],
        opportunities=[],
        scenario="SSP2-4.5",
        time_horizon="2050",
        confidence=0.6,
        data_gaps=gaps,
        assumptions=[],
    )
    appendix = result["6_appendix"]
    for gap in gaps:
        assert gap in appendix["data_gaps"]


def test_no_fabricated_financial_values(generator, sample_company, sample_physical_results):
    result = generator.generate(
        company=sample_company,
        properties=[],
        physical_risk_results=sample_physical_results,
        transition_risks=[],
        nature_risks=[],
        opportunities=[],
        scenario="SSP2-4.5",
        time_horizon="2050",
        confidence=0.6,
        data_gaps=[],
        assumptions=[],
    )
    # Check metrics section doesn't have fabricated financial figures
    metrics = result["5_metrics_and_targets"]
    assert metrics["financial_metrics_note"] is not None
    # No raw loss amounts
    assert "loss_usd" not in str(metrics)
    assert "revenue_at_risk_usd" not in str(metrics)
