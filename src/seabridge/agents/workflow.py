"""LangGraph workflow — 15-node AI sustainability assessment pipeline."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph

from ..config import settings
from ..hazards.registry import HazardRegistry
from ..models.agent_run import AgentRun
from ..models.assessment import EvidenceItem, FeatureScoreRecord, HazardScore, RiskAssessment
from ..models.company import Company
from ..models.enums import ApprovalState, DataType, Scenario
from ..models.property import Property
from .state import AgentState

logger = logging.getLogger(__name__)

_registry = HazardRegistry()


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=4096,
    )


# ─────────────────────────── node implementations ────────────────────────────


async def validate_request(state: AgentState) -> AgentState:
    errors: list[str] = list(state.get("errors", []))
    if not state.get("company_id"):
        errors.append("company_id is required")
    if not state.get("property_ids"):
        errors.append("At least one property_id is required")
    scenario = state.get("scenario", "ssp245")
    if scenario not in {"ssp126", "ssp245", "ssp585"}:
        errors.append(f"Invalid scenario: {scenario}")
    year = state.get("year", 2050)
    if year not in {2030, 2050, 2100}:
        errors.append(f"Invalid year: {year}")
    return {**state, "errors": errors}


async def load_company(state: AgentState) -> AgentState:
    try:
        company = await Company.find_one({"company_id": uuid.UUID(state["company_id"])})
        if company is None:
            return {**state, "errors": state.get("errors", []) + [f"Company {state['company_id']} not found"]}
        return {**state, "company": company.model_dump(mode="json")}
    except Exception as exc:
        return {**state, "errors": state.get("errors", []) + [str(exc)]}


async def load_properties(state: AgentState) -> AgentState:
    try:
        prop_ids = [uuid.UUID(pid) for pid in state.get("property_ids", [])]
        properties = await Property.find({"property_id": {"$in": prop_ids}}).to_list()
        return {**state, "properties": [p.model_dump(mode="json") for p in properties]}
    except Exception as exc:
        return {**state, "errors": state.get("errors", []) + [str(exc)]}


async def geocode_or_validate_coordinates(state: AgentState) -> AgentState:
    props = state.get("properties", [])
    validated: list[dict] = []
    errors = list(state.get("errors", []))
    for prop in props:
        lat = prop.get("latitude")
        lon = prop.get("longitude")
        if lat is None or lon is None:
            errors.append(f"Property {prop.get('property_id')} missing coordinates")
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            errors.append(f"Property {prop.get('property_id')} has invalid coordinates: {lat}, {lon}")
            continue
        validated.append(prop)
    return {**state, "properties": validated, "errors": errors}


async def enrich_building_context(state: AgentState) -> AgentState:
    """Populate missing property fields from data providers where possible."""
    props = state.get("properties", [])
    enriched: list[dict] = []
    for prop in props:
        # Minimal enrichment for MVP — mark that enrichment was attempted
        enriched.append({**prop, "_enriched": True})
    return {**state, "enriched_properties": enriched}


async def collect_physical_hazard_data(state: AgentState) -> AgentState:
    """Collect raw hazard data for all properties (passed through to scorer)."""
    return {**state, "hazard_data": {"status": "collected"}}


async def score_physical_risk(state: AgentState) -> AgentState:
    """Run all 6 hazard scorers for each property and scenario/year."""
    props = state.get("enriched_properties") or state.get("properties", [])
    scenario = state.get("scenario", "ssp245")
    year = state.get("year", 2050)
    company_id = state.get("company_id", "")

    results: dict[str, Any] = {}
    all_data_gaps: list[str] = []
    evidence: list[dict] = list(state.get("evidence", []))

    for prop in props:
        lat = prop["latitude"]
        lon = prop["longitude"]
        pid = str(prop.get("property_id", ""))

        scored = await _registry.score_all(lat, lon, prop, scenario, year)
        hazard_results = scored["hazard_results"]
        overall_score = scored["overall_score"]
        overall_rating = scored["overall_rating"]
        all_data_gaps.extend(scored["data_gaps"])

        # Build Beanie-ready HazardScore objects
        hazard_scores_doc: dict[str, HazardScore] = {}
        for htype, hr in hazard_results.items():
            feature_records = [
                FeatureScoreRecord(
                    feature_name=f.feature_name,
                    raw_value=f.raw_value if isinstance(f.raw_value, (int, float, str, type(None))) else str(f.raw_value),
                    normalized_score=f.normalized_score,
                    source=f.source,
                    source_url=f.source_url,
                    data_type=f.data_type,
                    is_available=f.is_available,
                    confidence=f.confidence,
                    note=f.note,
                )
                for f in hr.feature_scores
            ]
            hazard_scores_doc[htype.value] = HazardScore(
                hazard=htype,
                feature_scores=feature_records,
                category_score=hr.category_score,
                rating=hr.rating,
                confidence=hr.confidence,
                top_drivers=hr.top_drivers,
                data_gaps=hr.data_gaps,
                recommended_action=hr.recommended_action,
            )

        # Persist assessment
        try:
            assessment = RiskAssessment(
                property_id=uuid.UUID(pid) if pid else uuid.uuid4(),
                company_id=uuid.UUID(company_id) if company_id else uuid.uuid4(),
                scenario=Scenario(scenario),
                time_horizon=year,
                hazard_scores=hazard_scores_doc,
                overall_score=overall_score,
                overall_rating=overall_rating,
                confidence=sum(hs.confidence for hs in hazard_scores_doc.values()) / max(len(hazard_scores_doc), 1),
                data_gaps=scored["data_gaps"],
                assumptions=[
                    "Feature normalization bounds are calibrated to representative US building stock.",
                    "Stub providers return zero scores; data gaps are explicitly listed.",
                    f"Scenario: {scenario}, time horizon: {year}.",
                ],
            )
            await assessment.insert()
            results[pid] = {"assessment_id": str(assessment.assessment_id), "overall_score": overall_score}

            evidence.append({
                "claim": f"Physical risk scored for property {pid}",
                "source": "seabridge_hazard_scorer",
                "data_type": DataType.MODELED.value,
                "confidence": assessment.confidence,
                "accessed_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as exc:
            logger.warning("Could not persist assessment for %s: %s", pid, exc)
            results[pid] = {"error": str(exc)}

    confidence = (
        sum(r.get("overall_score", 0) for r in results.values() if isinstance(r, dict)) / max(len(results), 1) / 100
    )

    return {
        **state,
        "physical_risk_results": results,
        "evidence": evidence,
        "data_gaps": list(set(all_data_gaps)),
        "confidence": confidence,
    }


async def run_transition_risk_agent(state: AgentState) -> AgentState:
    """Analyse transition risk across 7 categories using the LLM."""
    if not settings.ANTHROPIC_API_KEY:
        return {
            **state,
            "transition_risk": {
                "status": "skipped",
                "reason": "ANTHROPIC_API_KEY not configured",
                "data_type": DataType.MISSING.value,
            },
        }

    company = state.get("company", {})
    phys_results = state.get("physical_risk_results", {})

    prompt = f"""You are a climate transition risk analyst. Analyse transition risk for the following company.

Company: {company.get('name', 'Unknown')}
Sector: {company.get('sector', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}
Geography: {company.get('geography', 'Unknown')}
Scenario: {state.get('scenario', 'ssp245')}
Year: {state.get('year', 2050)}

Physical risk context (scores 0-100):
{phys_results}

Analyse these SEVEN transition risk categories:
1. Policy and legal
2. Market
3. Technology
4. Reputation
5. Insurance
6. Utilities / energy / water
7. Capital access / financing

For EACH category output JSON with:
- risk_driver: string
- explanation: string (how it affects this company)
- time_horizon: "short" | "medium" | "long"
- severity: "low" | "medium" | "high" | "very_high"
- confidence: float 0-1
- financial_impact_note: string (only if financial assumptions are available; otherwise state required data)
- disclosure_area: "governance" | "strategy" | "risk_management" | "metrics_and_targets"

CRITICAL RULES:
- Do NOT invent financial figures without explicit stated assumptions
- Do NOT present AI interpretation as measured data
- If information is insufficient, state what data is required
- Tag every output as data_type: "ai_generated"

Respond with valid JSON only: {{"categories": [...]}}"""

    try:
        llm = _get_llm()
        response = await llm.ainvoke(prompt)
        import json
        content = response.content
        # Extract JSON from response
        start = content.find("{")
        end = content.rfind("}") + 1
        result = json.loads(content[start:end]) if start >= 0 else {"categories": [], "parse_error": content}
        result["data_type"] = DataType.AI_GENERATED.value
        result["scenario"] = state.get("scenario")
        result["year"] = state.get("year")
        return {**state, "transition_risk": result}
    except Exception as exc:
        logger.warning("Transition risk agent failed: %s", exc)
        return {
            **state,
            "transition_risk": {
                "status": "error",
                "error": str(exc),
                "data_type": DataType.MISSING.value,
            },
        }


async def run_climate_opportunities_agent(state: AgentState) -> AgentState:
    """Identify climate-related opportunities across 7 categories."""
    if not settings.ANTHROPIC_API_KEY:
        return {
            **state,
            "opportunities": {
                "status": "skipped",
                "reason": "ANTHROPIC_API_KEY not configured",
                "data_type": DataType.MISSING.value,
            },
        }

    company = state.get("company", {})

    prompt = f"""You are a climate opportunities analyst. Identify climate-related opportunities for:

Company: {company.get('name', 'Unknown')}
Sector: {company.get('sector', 'Unknown')}
Industry: {company.get('industry', 'Unknown')}
Scenario: {state.get('scenario', 'ssp245')}

Identify opportunities in these SEVEN categories:
1. Resource efficiency
2. Energy source
3. Products and services
4. Markets
5. Resilience / adaptation
6. Insurance or financing advantage
7. Customer demand / green premium

For EACH relevant opportunity output JSON with:
- title: string
- category: string
- description: string
- linked_risks: list of strings
- required_data: list of strings (what additional data would improve this analysis)
- implementation_actions: list of strings
- expected_benefit_type: "cost_reduction" | "revenue" | "risk_reduction" | "reputational"
- financial_estimate: string (only if supported by assumptions; otherwise "Requires: [data needed]")
- evidence: list of strings (sources)
- confidence: float 0-1
- time_horizon: "short" | "medium" | "long"
- disclosure_relevance: string

Tag all outputs as data_type: "ai_generated". Do NOT fabricate financial figures.
Respond with valid JSON only: {{"opportunities": [...]}}"""

    try:
        llm = _get_llm()
        response = await llm.ainvoke(prompt)
        import json
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        result = json.loads(content[start:end]) if start >= 0 else {"opportunities": [], "parse_error": content}
        result["data_type"] = DataType.AI_GENERATED.value
        return {**state, "opportunities": result}
    except Exception as exc:
        logger.warning("Opportunities agent failed: %s", exc)
        return {**state, "opportunities": {"status": "error", "error": str(exc)}}


async def run_nature_risk_agent(state: AgentState) -> AgentState:
    """Run TNFD LEAP-inspired nature risk analysis."""
    if not settings.ANTHROPIC_API_KEY:
        return {
            **state,
            "nature_risk": {
                "status": "skipped",
                "reason": "ANTHROPIC_API_KEY not configured",
                "data_type": DataType.MISSING.value,
            },
        }

    company = state.get("company", {})
    props = state.get("properties", [])

    prompt = f"""You are a nature risk analyst applying the TNFD LEAP framework.

Company: {company.get('name', 'Unknown')}
Sector: {company.get('sector', 'Unknown')}
Number of properties: {len(props)}
Geographies: {list(set(p.get('country', 'Unknown') for p in props))}

Apply the TNFD LEAP process:

L — LOCATE: Identify interface with nature (biomes, ecosystems, protected areas)
E — EVALUATE: Assess dependencies and impacts on ecosystem services (use ENCORE framework)
A — ASSESS: Determine material nature-related risks and opportunities
P — PREPARE: Recommend disclosure language and management actions

For each LEAP step output:
- findings: list of strings
- data_sources_used: list of strings
- data_gaps: list of strings
- confidence: float 0-1
- data_type: "ai_generated"

Include:
- nature_transition_risks: list (policy, market, reputation risks related to nature)
- nature_opportunities: list (green infrastructure, ecosystem restoration, etc.)

RULES: Do not fabricate species counts or biodiversity data. State data gaps explicitly.
Respond with valid JSON only: {{"leap": {{...}}, "nature_transition_risks": [...], "nature_opportunities": [...]}}"""

    try:
        llm = _get_llm()
        response = await llm.ainvoke(prompt)
        import json
        content = response.content
        start = content.find("{")
        end = content.rfind("}") + 1
        result = json.loads(content[start:end]) if start >= 0 else {"leap": {}, "parse_error": content}
        result["data_type"] = DataType.AI_GENERATED.value
        return {**state, "nature_risk": result}
    except Exception as exc:
        logger.warning("Nature risk agent failed: %s", exc)
        return {**state, "nature_risk": {"status": "error", "error": str(exc)}}


async def validate_evidence(state: AgentState) -> AgentState:
    """Verify that material claims have evidence and data types assigned."""
    evidence = state.get("evidence", [])
    warnings: list[str] = []

    for item in evidence:
        if not item.get("source"):
            warnings.append(f"Evidence item missing source: {item.get('claim', 'unknown')}")
        if not item.get("data_type"):
            warnings.append(f"Evidence item missing data_type: {item.get('claim', 'unknown')}")

    if warnings:
        logger.warning("Evidence validation warnings: %s", warnings)

    return {**state, "errors": state.get("errors", []) + warnings if len(warnings) > 3 else state.get("errors", [])}


async def check_confidence(state: AgentState) -> AgentState:
    """Flag for human review if confidence is below threshold or evidence is weak."""
    confidence = state.get("confidence", 0.0)
    data_gaps = state.get("data_gaps", [])
    phys_results = state.get("physical_risk_results", {})

    requires_review = False
    reasons: list[str] = []

    if confidence < 0.70:
        requires_review = True
        reasons.append(f"Overall confidence {confidence:.2f} below 0.70 threshold")

    if len(data_gaps) > 10:
        requires_review = True
        reasons.append(f"{len(data_gaps)} data gaps — material claims may be unsupported")

    # Check if any property scored HIGH/VERY_HIGH
    for pid, r in phys_results.items():
        if isinstance(r, dict) and r.get("overall_score", 0) > 60:
            requires_review = True
            reasons.append(f"Property {pid} has high physical risk score {r['overall_score']:.1f}")
            break

    if requires_review:
        logger.info("Human review required: %s", reasons)

    return {**state, "human_review_required": requires_review, "assumptions": state.get("assumptions", []) + reasons}


async def require_human_review_if_needed(state: AgentState) -> AgentState:
    """Mark AgentRun as pending human review and record in database."""
    run_id = state.get("run_id")
    if run_id:
        try:
            run = await AgentRun.find_one({"run_id": uuid.UUID(run_id)})
            if run:
                run.approval_state = ApprovalState.PENDING
                run.state = dict(state)
                await run.save()
        except Exception as exc:
            logger.warning("Could not update AgentRun approval state: %s", exc)
    return state


async def persist_results(state: AgentState) -> AgentState:
    """Persist final AgentRun state to MongoDB."""
    run_id = state.get("run_id")
    if run_id:
        try:
            run = await AgentRun.find_one({"run_id": uuid.UUID(run_id)})
            if run:
                run.final_output = {
                    "physical_risk": state.get("physical_risk_results"),
                    "transition_risk": state.get("transition_risk"),
                    "opportunities": state.get("opportunities"),
                    "nature_risk": state.get("nature_risk"),
                    "overall_confidence": state.get("confidence"),
                    "data_gaps": state.get("data_gaps"),
                }
                run.confidence = state.get("confidence")
                if not state.get("human_review_required"):
                    run.approval_state = ApprovalState.NOT_REQUIRED
                run.updated_at = datetime.now(timezone.utc)
                await run.save()
        except Exception as exc:
            logger.warning("Could not persist results: %s", exc)
    return state


async def generate_disclosure_summary(state: AgentState) -> AgentState:
    """Generate ISSB/TCFD-aligned disclosure draft."""
    from ..disclosure.generator import DisclosureGenerator
    try:
        gen = DisclosureGenerator()
        draft = gen.generate(state)
        return {**state, "disclosure_draft": draft}
    except Exception as exc:
        logger.warning("Disclosure generation failed: %s", exc)
        return {**state, "disclosure_draft": f"Disclosure generation failed: {exc}"}


# ───────────────────────────── graph assembly ─────────────────────────────────


def _route_after_confidence(state: AgentState) -> str:
    if state.get("human_review_required"):
        return "require_human_review_if_needed"
    return "persist_results"


def build_graph() -> Any:
    """Build and compile the LangGraph StateGraph."""
    graph = StateGraph(AgentState)

    graph.add_node("validate_request", validate_request)
    graph.add_node("load_company", load_company)
    graph.add_node("load_properties", load_properties)
    graph.add_node("geocode_or_validate_coordinates", geocode_or_validate_coordinates)
    graph.add_node("enrich_building_context", enrich_building_context)
    graph.add_node("collect_physical_hazard_data", collect_physical_hazard_data)
    graph.add_node("score_physical_risk", score_physical_risk)
    graph.add_node("run_transition_risk_agent", run_transition_risk_agent)
    graph.add_node("run_climate_opportunities_agent", run_climate_opportunities_agent)
    graph.add_node("run_nature_risk_agent", run_nature_risk_agent)
    graph.add_node("validate_evidence", validate_evidence)
    graph.add_node("check_confidence", check_confidence)
    graph.add_node("require_human_review_if_needed", require_human_review_if_needed)
    graph.add_node("persist_results", persist_results)
    graph.add_node("generate_disclosure_summary", generate_disclosure_summary)

    graph.add_edge(START, "validate_request")
    graph.add_edge("validate_request", "load_company")
    graph.add_edge("load_company", "load_properties")
    graph.add_edge("load_properties", "geocode_or_validate_coordinates")
    graph.add_edge("geocode_or_validate_coordinates", "enrich_building_context")
    graph.add_edge("enrich_building_context", "collect_physical_hazard_data")
    graph.add_edge("collect_physical_hazard_data", "score_physical_risk")
    graph.add_edge("score_physical_risk", "run_transition_risk_agent")
    graph.add_edge("run_transition_risk_agent", "run_climate_opportunities_agent")
    graph.add_edge("run_climate_opportunities_agent", "run_nature_risk_agent")
    graph.add_edge("run_nature_risk_agent", "validate_evidence")
    graph.add_edge("validate_evidence", "check_confidence")
    graph.add_conditional_edges("check_confidence", _route_after_confidence)
    graph.add_edge("require_human_review_if_needed", END)
    graph.add_edge("persist_results", "generate_disclosure_summary")
    graph.add_edge("generate_disclosure_summary", END)

    return graph.compile()


async def run_assessment(
    company_id: str,
    property_ids: list[str],
    scenario: str = "ssp245",
    year: int = 2050,
    task_type: str = "full_assessment",
) -> dict[str, Any]:
    """Entry point: create AgentRun, execute graph, return final state."""
    run_id = str(uuid.uuid4())

    # Create AgentRun record
    try:
        run = AgentRun(
            run_id=uuid.UUID(run_id),
            company_id=uuid.UUID(company_id),
            property_ids=[uuid.UUID(pid) for pid in property_ids],
            task_type=task_type,
            approval_state=ApprovalState.NOT_REQUIRED,
        )
        await run.insert()
    except Exception as exc:
        logger.warning("Could not create AgentRun: %s", exc)

    initial_state: AgentState = {
        "run_id": run_id,
        "company_id": company_id,
        "property_ids": property_ids,
        "task_type": task_type,
        "scenario": scenario,
        "year": year,
        "confidence": 0.0,
        "evidence": [],
        "data_gaps": [],
        "assumptions": [],
        "human_review_required": False,
        "human_feedback": None,
        "errors": [],
    }

    graph = build_graph()
    final_state = await graph.ainvoke(initial_state)
    return dict(final_state)
