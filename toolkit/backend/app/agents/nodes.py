"""
Individual node functions for the LangGraph workflow.
Each node receives a WorkflowState and returns a dict of field updates.
All AI-generated content is clearly labelled as data_source_type='ai_generated'.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation & loading
# ---------------------------------------------------------------------------

async def validate_request(state) -> Dict[str, Any]:
    errors = list(state.errors)
    if not state.company_id:
        errors.append("company_id is required")
    if not state.property_ids:
        errors.append("At least one property_id is required")
    valid_scenarios = {"SSP1-2.6", "SSP2-4.5", "SSP5-8.5", "NGFS_NET_ZERO", "NGFS_DELAYED_TRANSITION", "NGFS_HOTHOUSE"}
    if state.scenario and state.scenario not in valid_scenarios:
        errors.append(f"Unknown scenario: {state.scenario}")
    updates = {"errors": errors}
    if not errors:
        updates["steps_completed"] = list(state.steps_completed) + ["validate_request"]
    return updates


async def load_company(state) -> Dict[str, Any]:
    from langgraph.config import get_config
    try:
        config = get_config()
        store = config.get("configurable", {}).get("in_memory_companies", {})
    except Exception:
        store = {}
    company = store.get(state.company_id)
    gaps = list(state.data_gaps)
    if company is None:
        company = {
            "company_id": state.company_id,
            "name": "Unknown Company",
            "sector": "Unknown",
            "industry": "Unknown",
            "geography": "Unknown",
        }
        gaps.append("Company record not found — using placeholder")
    return {
        "company": company,
        "data_gaps": gaps,
        "steps_completed": list(state.steps_completed) + ["load_company"],
    }


async def load_properties(state) -> Dict[str, Any]:
    from langgraph.config import get_config
    try:
        config = get_config()
        store = config.get("configurable", {}).get("in_memory_properties", {})
    except Exception:
        store = {}
    found = []
    gaps = list(state.data_gaps)
    for pid in state.property_ids:
        prop = store.get(pid)
        if prop:
            found.append(prop)
        else:
            gaps.append(f"Property {pid} not found in store")
    return {
        "properties": found,
        "data_gaps": gaps,
        "steps_completed": list(state.steps_completed) + ["load_properties"],
    }


async def geocode_or_validate_coordinates(state) -> Dict[str, Any]:
    validated = []
    gaps = list(state.data_gaps)
    errors = list(state.errors)
    for prop in state.properties:
        lat = prop.get("latitude")
        lon = prop.get("longitude")
        if lat is None or lon is None:
            gaps.append(f"Property {prop.get('property_id', '?')} missing coordinates — cannot score")
            continue
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            errors.append(f"Property {prop.get('property_id', '?')} has invalid coordinates")
            continue
        prop = dict(prop)
        prop["geocode_validated"] = True
        validated.append(prop)
    return {
        "properties": validated,
        "data_gaps": gaps,
        "errors": errors,
        "steps_completed": list(state.steps_completed) + ["geocode_or_validate_coordinates"],
    }


async def enrich_building_context(state) -> Dict[str, Any]:
    enriched = []
    for prop in state.properties:
        prop = dict(prop)
        if prop.get("country") is None:
            lat = prop.get("latitude", 0)
            lon = prop.get("longitude", 0)
            prop["country"] = _coarse_country_from_coords(lat, lon)
            prop["_country_inferred"] = True
        enriched.append(prop)
    return {
        "properties": enriched,
        "steps_completed": list(state.steps_completed) + ["enrich_building_context"],
    }


def _coarse_country_from_coords(lat: float, lon: float) -> str:
    if 24 < lat < 50 and -125 < lon < -66:
        return "USA"
    if 49 < lat < 60 and -141 < lon < -52:
        return "Canada"
    if 36 < lat < 71 and -25 < lon < 40:
        return "Europe"
    if 7 < lat < 36 and 68 < lon < 97:
        return "India"
    if 20 < lat < 55 and 73 < lon < 135:
        return "China"
    return "Unknown"


# ---------------------------------------------------------------------------
# Physical risk scoring
# ---------------------------------------------------------------------------

async def score_physical_risk(state) -> Dict[str, Any]:
    from app.hazards.scorer import score_property
    results = []
    evidence = list(state.evidence)
    gaps = list(state.data_gaps)
    for prop in state.properties:
        lat = prop.get("latitude", 0)
        lon = prop.get("longitude", 0)
        result = score_property(
            lat=lat,
            lon=lon,
            property_attrs=prop,
            scenario=state.scenario,
            time_horizon=state.time_horizon,
        )
        result["property_id"] = prop.get("property_id", "")
        result["property_name"] = prop.get("name", "")
        results.append(result)
        evidence.extend(result.get("evidence", []))
        gaps.extend(result.get("data_gaps", []))
    return {
        "physical_risk_results": results,
        "evidence": evidence,
        "data_gaps": gaps,
        "steps_completed": list(state.steps_completed) + ["score_physical_risk"],
    }


# ---------------------------------------------------------------------------
# Transition risk
# ---------------------------------------------------------------------------

async def run_transition_risk_agent(state) -> Dict[str, Any]:
    from app.transition.transition_risk import TransitionRiskEngine
    company = state.company or {}
    engine = TransitionRiskEngine()
    risks = engine.assess(
        sector=company.get("sector", "Unknown"),
        industry=company.get("industry", "Unknown"),
        geography=company.get("geography", "Unknown"),
        scenario=state.scenario,
        physical_risk_results=state.physical_risk_results,
    )
    return {
        "transition_risks": risks,
        "steps_completed": list(state.steps_completed) + ["run_transition_risk_agent"],
    }


# ---------------------------------------------------------------------------
# Opportunities
# ---------------------------------------------------------------------------

async def run_climate_opportunities_agent(state) -> Dict[str, Any]:
    from app.opportunities.opportunities import OpportunitiesEngine
    company = state.company or {}
    engine = OpportunitiesEngine()
    opps = engine.identify(
        sector=company.get("sector", "Unknown"),
        industry=company.get("industry", "Unknown"),
        scenario=state.scenario,
        physical_risk_results=state.physical_risk_results,
        transition_risks=state.transition_risks,
    )
    return {
        "opportunities": opps,
        "steps_completed": list(state.steps_completed) + ["run_climate_opportunities_agent"],
    }


# ---------------------------------------------------------------------------
# Nature risk
# ---------------------------------------------------------------------------

async def run_nature_risk_agent(state) -> Dict[str, Any]:
    from app.nature.nature_risk import NatureRiskEngine
    company = state.company or {}
    engine = NatureRiskEngine()
    nature = engine.assess(
        sector=company.get("sector", "Unknown"),
        industry=company.get("industry", "Unknown"),
        properties=state.properties,
    )
    return {
        "nature_risks": nature,
        "steps_completed": list(state.steps_completed) + ["run_nature_risk_agent"],
    }


# ---------------------------------------------------------------------------
# Validation and confidence
# ---------------------------------------------------------------------------

async def validate_evidence(state) -> Dict[str, Any]:
    issues = list(state.review_reasons)
    for result in state.physical_risk_results:
        if result.get("overall_score", 0) > 60:
            evidence = result.get("evidence", [])
            if len(evidence) < 2:
                issues.append(
                    f"High-risk property {result.get('property_id', '?')} "
                    f"has insufficient evidence for disclosure claim"
                )
    return {
        "review_reasons": issues,
        "steps_completed": list(state.steps_completed) + ["validate_evidence"],
    }


async def check_confidence(state) -> Dict[str, Any]:
    physical = state.physical_risk_results
    if not physical:
        return {
            "confidence": 0.0,
            "requires_human_review": True,
            "review_reasons": list(state.review_reasons) + ["No physical risk results to evaluate"],
            "steps_completed": list(state.steps_completed) + ["check_confidence"],
        }

    conf_map = {"high": 0.9, "medium": 0.7, "low": 0.5, "very_low": 0.3}
    confs = [conf_map.get(r.get("confidence", "low"), 0.5) for r in physical]
    avg_conf = sum(confs) / len(confs)

    needs_review = False
    reasons = list(state.review_reasons)

    if avg_conf < 0.70:
        needs_review = True
        reasons.append(f"Average confidence {avg_conf:.2f} is below 0.70 threshold")

    for r in physical:
        if r.get("overall_score", 0) > 60:
            needs_review = True
            reasons.append(
                f"High-risk score {r['overall_score']} for property "
                f"{r.get('property_id', '?')} — disclosure language requires review"
            )
            break

    return {
        "confidence": round(avg_conf, 3),
        "requires_human_review": needs_review,
        "review_reasons": reasons,
        "steps_completed": list(state.steps_completed) + ["check_confidence"],
    }


# ---------------------------------------------------------------------------
# Disclosure
# ---------------------------------------------------------------------------

async def generate_disclosure_summary(state) -> Dict[str, Any]:
    from app.disclosure.generator import DisclosureGenerator
    gen = DisclosureGenerator()
    summary = gen.generate(
        company=state.company or {},
        properties=state.properties,
        physical_risk_results=state.physical_risk_results,
        transition_risks=state.transition_risks,
        nature_risks=state.nature_risks,
        opportunities=state.opportunities,
        scenario=state.scenario,
        time_horizon=state.time_horizon,
        confidence=state.confidence,
        data_gaps=state.data_gaps,
        assumptions=state.assumptions,
    )
    return {
        "disclosure_summary": summary,
        "steps_completed": list(state.steps_completed) + ["generate_disclosure_summary"],
    }
