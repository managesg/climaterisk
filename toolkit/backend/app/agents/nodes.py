"""
Individual node functions for the LangGraph workflow.
Each node receives and returns a WorkflowState dict.
All AI-generated content is clearly labelled as data_source_type='ai_generated'.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Validation & loading
# ---------------------------------------------------------------------------

async def validate_request(state: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    if not state.get("company_id"):
        errors.append("company_id is required")
    if not state.get("property_ids"):
        errors.append("At least one property_id is required")
    valid_scenarios = {"SSP1-2.6", "SSP2-4.5", "SSP5-8.5", "NGFS_NET_ZERO", "NGFS_DELAYED_TRANSITION", "NGFS_HOTHOUSE"}
    if state.get("scenario") and state["scenario"] not in valid_scenarios:
        errors.append(f"Unknown scenario: {state['scenario']}")
    state["errors"] = errors
    if not errors:
        state.setdefault("steps_completed", []).append("validate_request")
    return state


async def load_company(state: Dict[str, Any]) -> Dict[str, Any]:
    config = state.get("__config__", {}).get("configurable", {})
    store = config.get("in_memory_companies", {})
    company = store.get(state["company_id"])
    if company is None:
        # Return a placeholder so the workflow can continue with available data
        company = {
            "company_id": state["company_id"],
            "name": "Unknown Company",
            "sector": "Unknown",
            "industry": "Unknown",
            "geography": "Unknown",
        }
        state.setdefault("data_gaps", []).append("Company record not found — using placeholder")
    state["company"] = company
    state.setdefault("steps_completed", []).append("load_company")
    return state


async def load_properties(state: Dict[str, Any]) -> Dict[str, Any]:
    config = state.get("__config__", {}).get("configurable", {})
    store = config.get("in_memory_properties", {})
    found = []
    missing = []
    for pid in state.get("property_ids", []):
        prop = store.get(pid)
        if prop:
            found.append(prop)
        else:
            missing.append(pid)
            state.setdefault("data_gaps", []).append(f"Property {pid} not found in store")
    state["properties"] = found
    state.setdefault("steps_completed", []).append("load_properties")
    return state


async def geocode_or_validate_coordinates(state: Dict[str, Any]) -> Dict[str, Any]:
    validated = []
    for prop in state.get("properties", []):
        lat = prop.get("latitude")
        lon = prop.get("longitude")
        if lat is None or lon is None:
            state.setdefault("data_gaps", []).append(
                f"Property {prop.get('property_id', '?')} missing coordinates — cannot score"
            )
            continue
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            state.setdefault("errors", []).append(
                f"Property {prop.get('property_id', '?')} has invalid coordinates"
            )
            continue
        prop["geocode_validated"] = True
        validated.append(prop)
    state["properties"] = validated
    state.setdefault("steps_completed", []).append("geocode_or_validate_coordinates")
    return state


async def enrich_building_context(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fill in missing building context where possible from open proxies.
    Clearly marks inferred data.
    """
    for prop in state.get("properties", []):
        if prop.get("country") is None:
            lat = prop.get("latitude", 0)
            lon = prop.get("longitude", 0)
            prop["country"] = _coarse_country_from_coords(lat, lon)
            prop["_country_inferred"] = True
    state.setdefault("steps_completed", []).append("enrich_building_context")
    return state


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

async def score_physical_risk(state: Dict[str, Any]) -> Dict[str, Any]:
    from app.hazards.scorer import score_property
    results = []
    for prop in state.get("properties", []):
        lat = prop.get("latitude", 0)
        lon = prop.get("longitude", 0)
        result = score_property(
            lat=lat,
            lon=lon,
            property_attrs=prop,
            scenario=state.get("scenario", "SSP2-4.5"),
            time_horizon=state.get("time_horizon", "2050"),
        )
        result["property_id"] = prop.get("property_id", "")
        result["property_name"] = prop.get("name", "")
        results.append(result)
        state.setdefault("evidence", []).extend(result.get("evidence", []))
        state.setdefault("data_gaps", []).extend(result.get("data_gaps", []))
    state["physical_risk_results"] = results
    state.setdefault("steps_completed", []).append("score_physical_risk")
    return state


# ---------------------------------------------------------------------------
# Transition risk
# ---------------------------------------------------------------------------

async def run_transition_risk_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    from app.transition.transition_risk import TransitionRiskEngine
    company = state.get("company") or {}
    physical_results = state.get("physical_risk_results", [])
    engine = TransitionRiskEngine()
    risks = engine.assess(
        sector=company.get("sector", "Unknown"),
        industry=company.get("industry", "Unknown"),
        geography=company.get("geography", "Unknown"),
        scenario=state.get("scenario", "SSP2-4.5"),
        physical_risk_results=physical_results,
    )
    state["transition_risks"] = risks
    state.setdefault("steps_completed", []).append("run_transition_risk_agent")
    return state


# ---------------------------------------------------------------------------
# Opportunities
# ---------------------------------------------------------------------------

async def run_climate_opportunities_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    from app.opportunities.opportunities import OpportunitiesEngine
    company = state.get("company") or {}
    engine = OpportunitiesEngine()
    opps = engine.identify(
        sector=company.get("sector", "Unknown"),
        industry=company.get("industry", "Unknown"),
        scenario=state.get("scenario", "SSP2-4.5"),
        physical_risk_results=state.get("physical_risk_results", []),
        transition_risks=state.get("transition_risks", []),
    )
    state["opportunities"] = opps
    state.setdefault("steps_completed", []).append("run_climate_opportunities_agent")
    return state


# ---------------------------------------------------------------------------
# Nature risk
# ---------------------------------------------------------------------------

async def run_nature_risk_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    from app.nature.nature_risk import NatureRiskEngine
    company = state.get("company") or {}
    engine = NatureRiskEngine()
    nature = engine.assess(
        sector=company.get("sector", "Unknown"),
        industry=company.get("industry", "Unknown"),
        properties=state.get("properties", []),
    )
    state["nature_risks"] = nature
    state.setdefault("steps_completed", []).append("run_nature_risk_agent")
    return state


# ---------------------------------------------------------------------------
# Validation and confidence
# ---------------------------------------------------------------------------

async def validate_evidence(state: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    physical = state.get("physical_risk_results", [])
    for result in physical:
        if result.get("overall_score", 0) > 60:
            evidence = result.get("evidence", [])
            if len(evidence) < 2:
                issues.append(
                    f"High-risk property {result.get('property_id', '?')} "
                    f"has insufficient evidence for disclosure claim"
                )
    state["review_reasons"] = state.get("review_reasons", []) + issues
    state.setdefault("steps_completed", []).append("validate_evidence")
    return state


async def check_confidence(state: Dict[str, Any]) -> Dict[str, Any]:
    physical = state.get("physical_risk_results", [])
    if not physical:
        state["confidence"] = 0.0
        state["requires_human_review"] = True
        state.setdefault("review_reasons", []).append("No physical risk results to evaluate")
        state.setdefault("steps_completed", []).append("check_confidence")
        return state

    conf_map = {"high": 0.9, "medium": 0.7, "low": 0.5, "very_low": 0.3}
    confs = [conf_map.get(r.get("confidence", "low"), 0.5) for r in physical]
    avg_conf = sum(confs) / len(confs)
    state["confidence"] = round(avg_conf, 3)

    needs_review = False
    reasons = list(state.get("review_reasons", []))

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

    state["requires_human_review"] = needs_review
    state["review_reasons"] = reasons
    state.setdefault("steps_completed", []).append("check_confidence")
    return state


# ---------------------------------------------------------------------------
# Disclosure
# ---------------------------------------------------------------------------

async def generate_disclosure_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    from app.disclosure.generator import DisclosureGenerator
    gen = DisclosureGenerator()
    summary = gen.generate(
        company=state.get("company") or {},
        properties=state.get("properties", []),
        physical_risk_results=state.get("physical_risk_results", []),
        transition_risks=state.get("transition_risks", []),
        nature_risks=state.get("nature_risks", []),
        opportunities=state.get("opportunities", []),
        scenario=state.get("scenario", "SSP2-4.5"),
        time_horizon=state.get("time_horizon", "2050"),
        confidence=state.get("confidence", 0.0),
        data_gaps=state.get("data_gaps", []),
        assumptions=state.get("assumptions", []),
    )
    state["disclosure_summary"] = summary
    state.setdefault("steps_completed", []).append("generate_disclosure_summary")
    return state
