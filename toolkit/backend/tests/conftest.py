"""Shared pytest fixtures."""
import pytest


@pytest.fixture
def sample_property_sf():
    """Sample San Francisco commercial property."""
    return {
        "property_id": "prop-sf-001",
        "company_id": "co-001",
        "name": "SF Office HQ",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "country": "USA",
        "state_province": "CA",
        "city": "San Francisco",
        "asset_type": "Office",
        "floor_area_m2": 5000,
        "year_built": 1990,
        "construction_type": "Masonry",
        "elevation_m": 15.0,
        "distance_to_coast_km": 3.5,
        "distance_to_river_km": 8.0,
        "tree_canopy_pct": 20.0,
        "impervious_surface_pct": 70.0,
        "fema_flood_zone": "X",
    }


@pytest.fixture
def sample_property_florida():
    """Sample Florida coastal property."""
    return {
        "property_id": "prop-fl-001",
        "company_id": "co-001",
        "name": "Miami Beach Retail",
        "latitude": 25.7617,
        "longitude": -80.1918,
        "country": "USA",
        "state_province": "FL",
        "city": "Miami",
        "asset_type": "Retail",
        "floor_area_m2": 2000,
        "year_built": 1975,
        "construction_type": "Masonry",
        "elevation_m": 2.0,
        "distance_to_coast_km": 0.5,
        "distance_to_river_km": 5.0,
        "tree_canopy_pct": 10.0,
        "impervious_surface_pct": 85.0,
        "fema_flood_zone": "AE",
    }


@pytest.fixture
def sample_property_inland():
    """Sample inland property with minimal coastal exposure."""
    return {
        "property_id": "prop-co-001",
        "company_id": "co-001",
        "name": "Denver Industrial Park",
        "latitude": 39.7392,
        "longitude": -104.9903,
        "country": "USA",
        "state_province": "CO",
        "city": "Denver",
        "asset_type": "Industrial",
        "floor_area_m2": 10000,
        "year_built": 2005,
        "construction_type": "Steel Frame",
        "elevation_m": 1609.0,
        "distance_to_coast_km": 1600.0,
        "distance_to_river_km": 0.8,
        "tree_canopy_pct": 5.0,
        "impervious_surface_pct": 90.0,
        "fema_flood_zone": "X",
    }


@pytest.fixture
def sample_company():
    return {
        "company_id": "co-001",
        "name": "Test Property Holdings",
        "sector": "Real Estate",
        "industry": "Commercial Real Estate",
        "geography": "United States",
        "reporting_boundary": "operational_control",
    }
