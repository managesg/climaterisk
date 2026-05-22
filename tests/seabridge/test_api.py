"""Tests for FastAPI endpoints using TestClient."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from seabridge.api.app import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_and_get_company(client):
    payload = {
        "name": "Test Corp",
        "sector": "Real Estate",
        "industry": "Office",
        "geography": "USA",
        "emissions": 1500.0,
    }
    resp = await client.post("/api/v1/companies", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    company_id = data["company_id"]
    assert data["name"] == "Test Corp"

    get_resp = await client.get(f"/api/v1/companies/{company_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["company_id"] == company_id


@pytest.mark.asyncio
async def test_create_property(client):
    # First create a company
    co = await client.post("/api/v1/companies", json={
        "name": "Prop Owner", "sector": "RE", "industry": "Office", "geography": "USA"
    })
    cid = co.json()["company_id"]

    resp = await client.post("/api/v1/properties", json={
        "company_id": cid,
        "name": "HQ",
        "latitude": 37.77,
        "longitude": -122.42,
        "asset_type": "office",
        "year_built": 2000,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["latitude"] == 37.77
    assert data["company_id"] == cid


@pytest.mark.asyncio
async def test_assessment_run_returns_hazard_scores(client):
    co = await client.post("/api/v1/companies", json={
        "name": "Risk Co", "sector": "RE", "industry": "Residential", "geography": "USA"
    })
    cid = co.json()["company_id"]

    prop = await client.post("/api/v1/properties", json={
        "company_id": cid,
        "name": "Test Building",
        "latitude": 37.77,
        "longitude": -122.42,
        "asset_type": "residential",
        "year_built": 1985,
        "construction_type": "wood_frame",
    })
    pid = prop.json()["property_id"]

    resp = await client.post("/api/v1/assessments/run", json={
        "company_id": cid,
        "property_ids": [pid],
        "scenario": "ssp245",
        "time_horizon": 2050,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["count"] == 1
    assessment = data["assessments"][0]
    assert "hazard_scores" in assessment
    # Should have all 6 hazards
    assert len(assessment["hazard_scores"]) == 6
    # All hazards should have DataType info
    for hname, hs in assessment["hazard_scores"].items():
        for feature in hs["feature_scores"]:
            assert "data_type" in feature, f"{hname}.{feature['feature_name']} missing data_type"


@pytest.mark.asyncio
async def test_list_companies(client):
    for i in range(3):
        await client.post("/api/v1/companies", json={
            "name": f"Company {i}", "sector": "RE", "industry": "Office", "geography": "USA"
        })
    resp = await client.get("/api/v1/companies")
    assert resp.status_code == 200
    assert len(resp.json()) >= 3


@pytest.mark.asyncio
async def test_company_not_found(client):
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/companies/{fake_id}")
    assert resp.status_code == 404
