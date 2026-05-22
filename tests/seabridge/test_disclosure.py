"""Tests for the disclosure report generator."""

import pytest

from seabridge.disclosure.generator import DisclosureGenerator
from seabridge.models.enums import DataType


def _sample_state() -> dict:
    return {
        "company": {
            "name": "Test Corp",
            "sector": "Real Estate",
            "industry": "Office Buildings",
            "geography": "USA",
            "emissions": 1500.0,
        },
        "physical_risk_results": {
            "prop-001": {"overall_score": 55.3, "assessment_id": "assess-001"},
            "prop-002": {"overall_score": 72.1, "assessment_id": "assess-002"},
        },
        "transition_risk": {
            "categories": [
                {
                    "risk_driver": "Carbon pricing",
                    "explanation": "Increased operating costs",
                    "time_horizon": "medium",
                    "severity": "high",
                    "confidence": 0.7,
                    "data_type": DataType.AI_GENERATED.value,
                }
            ],
            "data_type": DataType.AI_GENERATED.value,
        },
        "opportunities": {
            "opportunities": [
                {
                    "title": "Green building certification",
                    "category": "Products and services",
                    "description": "Achieve LEED certification to attract ESG-conscious tenants",
                    "confidence": 0.8,
                }
            ]
        },
        "nature_risk": {"leap": {"locate": {"findings": ["Near protected area"]}}},
        "data_gaps": ["wildfire:smoke_air_quality", "inland_flood:soil_permeability"],
        "confidence": 0.65,
        "scenario": "ssp245",
        "year": 2050,
        "assumptions": ["Feature normalization calibrated to US building stock."],
    }


def test_disclosure_generates_all_sections():
    gen = DisclosureGenerator()
    report = gen.generate(_sample_state())

    required_headings = [
        "# Climate Risk",
        "## 1. Executive Summary",
        "## 2. Governance",
        "## 3. Strategy",
        "## 4. Risk Management",
        "## 5. Metrics and Targets",
        "## 6. Appendix",
    ]
    for heading in required_headings:
        assert heading in report, f"Missing section: {heading}"


def test_disclosure_contains_data_integrity_notice():
    gen = DisclosureGenerator()
    report = gen.generate(_sample_state())
    assert "Data integrity notice" in report


def test_disclosure_lists_data_gaps():
    gen = DisclosureGenerator()
    report = gen.generate(_sample_state())
    # Appendix should list the data gaps
    assert "soil_permeability" in report or "Data Gaps" in report


def test_disclosure_tags_ai_generated_content():
    gen = DisclosureGenerator()
    report = gen.generate(_sample_state())
    assert "AI-generated" in report or "ai_generated" in report


def test_disclosure_includes_scenario():
    gen = DisclosureGenerator()
    report = gen.generate(_sample_state())
    assert "ssp245" in report.lower() or "SSP245" in report


def test_disclosure_no_fabricated_financial_figures():
    """Disclosure must not claim specific financial losses without assumptions."""
    gen = DisclosureGenerator()
    report = gen.generate(_sample_state())
    # Should not contain $ amounts fabricated by the generator
    import re
    dollar_amounts = re.findall(r"\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion))?", report, re.IGNORECASE)
    # Any dollar amounts in the report should come from user-provided data, not fabrication
    # For this test we verify no large fabricated losses appear
    large_amounts = [a for a in dollar_amounts if any(c in a.lower() for c in ["billion", "million"])]
    # Generator itself shouldn't produce large financial claims
    assert len(large_amounts) == 0, f"Fabricated financial figures found: {large_amounts}"


def test_disclosure_confidence_displayed():
    gen = DisclosureGenerator()
    report = gen.generate(_sample_state())
    assert "65%" in report or "0.65" in report


def test_disclosure_empty_physical_results():
    """Generator must handle empty physical results gracefully."""
    state = _sample_state()
    state["physical_risk_results"] = {}
    gen = DisclosureGenerator()
    report = gen.generate(state)
    assert "## 1. Executive Summary" in report  # should not crash
