"""
LangGraph workflow for the AI Sustainability Toolkit.

Workflow steps:
  1. validate_request
  2. load_company
  3. load_properties
  4. geocode_or_validate_coordinates
  5. enrich_building_context
  6. collect_physical_hazard_data
  7. score_physical_risk
  8. run_transition_risk_agent
  9. run_climate_opportunities_agent
 10. run_nature_risk_agent
 11. validate_evidence
 12. check_confidence
 13. require_human_review_if_needed
 14. persist_results
 15. generate_disclosure_summary
"""
import logging
import uuid
from typing import Dict, Any, Optional

from langgraph.graph import StateGraph, END

from .states import WorkflowState
from .nodes import (
    validate_request,
    load_company,
    load_properties,
    geocode_or_validate_coordinates,
    enrich_building_context,
    score_physical_risk,
    run_transition_risk_agent,
    run_climate_opportunities_agent,
    run_nature_risk_agent,
    validate_evidence,
    check_confidence,
    generate_disclosure_summary,
)

logger = logging.getLogger(__name__)


def _needs_human_review(state: WorkflowState) -> str:
    if state.requires_human_review:
        return "await_human"
    return "persist_results"


def _has_errors(state: WorkflowState) -> str:
    if state.errors:
        return "end_with_error"
    return "load_company"


def build_workflow() -> StateGraph:
    graph = StateGraph(WorkflowState)

    graph.add_node("validate_request", validate_request)
    graph.add_node("load_company", load_company)
    graph.add_node("load_properties", load_properties)
    graph.add_node("geocode_or_validate_coordinates", geocode_or_validate_coordinates)
    graph.add_node("enrich_building_context", enrich_building_context)
    graph.add_node("score_physical_risk", score_physical_risk)
    graph.add_node("run_transition_risk_agent", run_transition_risk_agent)
    graph.add_node("run_climate_opportunities_agent", run_climate_opportunities_agent)
    graph.add_node("run_nature_risk_agent", run_nature_risk_agent)
    graph.add_node("validate_evidence", validate_evidence)
    graph.add_node("check_confidence", check_confidence)
    graph.add_node("generate_disclosure_summary", generate_disclosure_summary)

    graph.set_entry_point("validate_request")

    graph.add_conditional_edges(
        "validate_request",
        _has_errors,
        {"load_company": "load_company", "end_with_error": END},
    )
    graph.add_edge("load_company", "load_properties")
    graph.add_edge("load_properties", "geocode_or_validate_coordinates")
    graph.add_edge("geocode_or_validate_coordinates", "enrich_building_context")
    graph.add_edge("enrich_building_context", "score_physical_risk")
    graph.add_edge("score_physical_risk", "run_transition_risk_agent")
    graph.add_edge("run_transition_risk_agent", "run_climate_opportunities_agent")
    graph.add_edge("run_climate_opportunities_agent", "run_nature_risk_agent")
    graph.add_edge("run_nature_risk_agent", "validate_evidence")
    graph.add_edge("validate_evidence", "check_confidence")
    graph.add_conditional_edges(
        "check_confidence",
        _needs_human_review,
        {"await_human": END, "persist_results": "generate_disclosure_summary"},
    )
    graph.add_edge("generate_disclosure_summary", END)

    return graph


def compile_workflow():
    graph = build_workflow()
    return graph.compile()


async def run_assessment(
    company_id: str,
    property_ids: list,
    task_type: str = "full_assessment",
    scenario: str = "SSP2-4.5",
    time_horizon: str = "2050",
    run_id: Optional[str] = None,
    in_memory_companies: Optional[Dict] = None,
    in_memory_properties: Optional[Dict] = None,
) -> WorkflowState:
    """
    Run the full assessment workflow. Returns the final WorkflowState.
    in_memory_companies and in_memory_properties are simple dict stores for MVP
    (MongoDB integration deferred to production).
    """
    workflow = compile_workflow()
    initial_state = WorkflowState(
        company_id=company_id,
        property_ids=property_ids,
        task_type=task_type,
        scenario=scenario,
        time_horizon=time_horizon,
        run_id=run_id or str(uuid.uuid4()),
    )

    config = {
        "configurable": {
            "in_memory_companies": in_memory_companies or {},
            "in_memory_properties": in_memory_properties or {},
        }
    }

    result = await workflow.ainvoke(initial_state.model_dump(), config=config)
    return WorkflowState(**result)
