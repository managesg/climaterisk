"""Tests for data provider stubs and availability checks."""

import pytest

from seabridge.data.providers.stub import StubProvider
from seabridge.data.providers.nasa_nexgddp import NASANexGDDPProvider
from seabridge.data.providers.encore import ENCOREProvider
from seabridge.data.providers.iucn import IUCNProvider
from seabridge.data.providers.wdpa import WDPAProvider
from seabridge.data.providers.noaa_ibtracs import NOAAIBTracsProvider
from seabridge.data.providers.noaa_storm_events import NOAAStormEventsProvider
from seabridge.data.providers.nlcd import NLCDProvider


def test_stub_provider_not_available():
    stub = StubProvider("test_stub", "Test note")
    assert stub.is_available() is False


@pytest.mark.asyncio
async def test_stub_provider_fetch_returns_dict():
    stub = StubProvider()
    result = await stub.fetch(37.77, -122.42)
    assert isinstance(result, dict)
    assert result["available"] is False
    assert "note" in result


@pytest.mark.asyncio
async def test_nasa_nexgddp_always_available():
    """NASA NEX-GDDP uses static summaries — always returns data."""
    provider = NASANexGDDPProvider()
    assert provider.is_available() is True


@pytest.mark.asyncio
async def test_nasa_nexgddp_returns_scenario_data():
    provider = NASANexGDDPProvider()
    result = await provider.fetch(37.77, -122.42, scenario="ssp585", year=2100)
    assert result["available"] is True
    assert isinstance(result["extreme_heat_days_above_35c"], (int, float))
    assert result["scenario"] == "ssp585"


@pytest.mark.asyncio
async def test_nasa_nexgddp_all_scenarios():
    provider = NASANexGDDPProvider()
    for scenario in ["ssp126", "ssp245", "ssp585"]:
        result = await provider.fetch(37.77, -122.42, scenario=scenario, year=2050)
        assert result["available"] is True
        assert result["extreme_heat_days_above_35c"] is not None


@pytest.mark.asyncio
async def test_encore_returns_sector_dependencies():
    provider = ENCOREProvider()
    result = await provider.fetch(0.0, 0.0, sector="real_estate")
    assert isinstance(result["ecosystem_service_dependencies"], list)
    assert len(result["ecosystem_service_dependencies"]) > 0


@pytest.mark.asyncio
async def test_iucn_stub_not_available():
    provider = IUCNProvider()
    assert provider.is_available() is False
    result = await provider.fetch(0.0, 0.0)
    assert result["threatened_species_count"] is None


@pytest.mark.asyncio
async def test_all_stubs_return_source_url():
    """Every provider must return a source_url for citability."""
    stubs = [
        NOAAIBTracsProvider(),
        NOAAStormEventsProvider(),
        NLCDProvider(),
        IUCNProvider(),
        WDPAProvider(),
    ]
    for stub in stubs:
        result = await stub.fetch(37.77, -122.42)
        assert "source_url" in result, f"{stub.name} missing source_url"
        assert result["source_url"].startswith("http"), f"{stub.name} source_url invalid"
