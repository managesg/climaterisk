"""
In-memory store for MVP — replace with MongoDB/Beanie for production.
Stores companies and properties as plain dicts.
"""
from typing import Dict, Any, List, Optional
import asyncio

_companies: Dict[str, Dict[str, Any]] = {}
_properties: Dict[str, Dict[str, Any]] = {}
_assessments: Dict[str, Dict[str, Any]] = {}
_agent_runs: Dict[str, Dict[str, Any]] = {}
_lock = asyncio.Lock()


async def save_company(company: Dict[str, Any]) -> str:
    cid = company["company_id"]
    async with _lock:
        _companies[cid] = company
    return cid


async def get_company(company_id: str) -> Optional[Dict[str, Any]]:
    return _companies.get(company_id)


async def list_companies() -> List[Dict[str, Any]]:
    return list(_companies.values())


async def save_property(prop: Dict[str, Any]) -> str:
    pid = prop["property_id"]
    async with _lock:
        _properties[pid] = prop
    return pid


async def get_property(property_id: str) -> Optional[Dict[str, Any]]:
    return _properties.get(property_id)


async def list_properties(company_id: Optional[str] = None) -> List[Dict[str, Any]]:
    props = list(_properties.values())
    if company_id:
        props = [p for p in props if p.get("company_id") == company_id]
    return props


async def save_assessment(assessment: Dict[str, Any]) -> str:
    aid = assessment["assessment_id"]
    async with _lock:
        _assessments[aid] = assessment
    return aid


async def get_assessment(assessment_id: str) -> Optional[Dict[str, Any]]:
    return _assessments.get(assessment_id)


async def list_assessments(company_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = list(_assessments.values())
    if company_id:
        items = [a for a in items if a.get("company_id") == company_id]
    return items


async def save_agent_run(run: Dict[str, Any]) -> str:
    rid = run["run_id"]
    async with _lock:
        _agent_runs[rid] = run
    return rid


async def get_agent_run(run_id: str) -> Optional[Dict[str, Any]]:
    return _agent_runs.get(run_id)


async def list_agent_runs(company_id: Optional[str] = None) -> List[Dict[str, Any]]:
    runs = list(_agent_runs.values())
    if company_id:
        runs = [r for r in runs if r.get("company_id") == company_id]
    return runs


def get_all_companies_dict() -> Dict[str, Any]:
    return dict(_companies)


def get_all_properties_dict() -> Dict[str, Any]:
    return dict(_properties)
