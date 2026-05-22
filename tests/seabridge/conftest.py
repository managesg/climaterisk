"""Shared pytest fixtures for seabridge tests."""

import pytest
import pytest_asyncio
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from seabridge.models.agent_run import AgentRun
from seabridge.models.assessment import RiskAssessment
from seabridge.models.company import Company
from seabridge.models.property import Property


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    """Initialise Beanie with an in-memory MongoDB for each test."""
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["test_seabridge"],
        document_models=[Company, Property, RiskAssessment, AgentRun],
    )
    yield
    # mongomock_motor resets state between test runs automatically


@pytest.fixture
def sample_property_data() -> dict:
    return {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "asset_type": "office",
        "year_built": 1995,
        "construction_type": "concrete",
        "elevation": 15.0,
        "distance_to_coast": 5.0,
        "distance_to_river": 2.0,
        "impervious_surface": 0.7,
        "vegetation_canopy": 0.1,
        "energy_intensity": 120.0,
        "water_intensity": 0.5,
    }
