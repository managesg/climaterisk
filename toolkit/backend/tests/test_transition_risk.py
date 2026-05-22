"""Tests for transition risk engine."""
import pytest
from app.transition.transition_risk import TransitionRiskEngine

CATEGORIES = {
    "Policy and Legal",
    "Market",
    "Technology",
    "Reputation",
    "Insurance",
    "Utilities / Energy / Water",
    "Capital Access / Financing",
}


@pytest.fixture
def engine():
    return TransitionRiskEngine()


def test_returns_seven_categories(engine):
    risks = engine.assess(
        sector="Real Estate",
        industry="Commercial Real Estate",
        geography="USA",
        scenario="SSP2-4.5",
        physical_risk_results=[],
    )
    assert len(risks) == 7


def test_all_categories_present(engine):
    risks = engine.assess(
        sector="Energy",
        industry="Oil & Gas",
        geography="USA",
        scenario="NGFS_NET_ZERO",
        physical_risk_results=[],
    )
    returned_categories = {r["category"] for r in risks}
    assert returned_categories == CATEGORIES


def test_high_policy_under_net_zero(engine):
    risks = engine.assess(
        sector="Energy",
        industry="Oil & Gas",
        geography="USA",
        scenario="NGFS_NET_ZERO",
        physical_risk_results=[],
    )
    policy = next(r for r in risks if r["category"] == "Policy and Legal")
    assert policy["severity"] in ("High", "Very High")


def test_no_financial_values_fabricated(engine):
    """Ensure financial estimates always have a note, never a raw number."""
    risks = engine.assess(
        sector="Real Estate",
        industry="Commercial Real Estate",
        geography="USA",
        scenario="SSP2-4.5",
        physical_risk_results=[],
    )
    for risk in risks:
        assert "financial_impact_note" in risk
        # Should not have raw financial values
        assert "financial_loss_usd" not in risk
        assert "financial_impact_usd" not in risk


def test_data_source_type_is_ai_generated(engine):
    risks = engine.assess("Real Estate", "Office", "USA", "SSP2-4.5", [])
    for risk in risks:
        assert risk.get("data_source_type") == "ai_generated"


def test_insurance_risk_elevated_with_high_physical_risk(engine):
    high_physical = [{"overall_score": 75, "property_id": "p-1"}]
    no_physical = []
    high = engine.assess("Real Estate", "Office", "USA", "SSP2-4.5", high_physical)
    low = engine.assess("Real Estate", "Office", "USA", "SSP2-4.5", no_physical)
    high_ins = next(r for r in high if r["category"] == "Insurance")
    low_ins = next(r for r in low if r["category"] == "Insurance")
    assert high_ins["severity"] in ("High", "Very High")


def test_required_data_not_empty(engine):
    risks = engine.assess("Real Estate", "Office", "USA", "SSP2-4.5", [])
    for risk in risks:
        assert len(risk.get("required_data", [])) > 0
