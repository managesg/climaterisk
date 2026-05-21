"""
Seed the in-memory store with a demo company and portfolio for local development.
Run: python -m scripts.seed_demo  (from toolkit/backend/)
Uses the live API so the server must be running on localhost:8000.
"""
import asyncio
import httpx

BASE = "http://localhost:8000/api/v1"

COMPANY = {
    "name": "Meridian Property Group",
    "sector": "Real Estate",
    "industry": "Commercial Real Estate",
    "geography": "United States",
    "reporting_boundary": "operational_control",
    "emissions": {
        "scope_1_tco2e": 1200,
        "scope_2_tco2e": 8400,
        "base_year": 2023,
        "reporting_standard": "GHG Protocol",
        "data_source": "user_provided",
    },
    "energy_use_mwh": 18500,
    "water_use_m3": 42000,
}

PROPERTIES = [
    {
        "name": "Miami Beach Flagship",
        "latitude": 25.7617,
        "longitude": -80.1918,
        "country": "USA",
        "state_province": "FL",
        "city": "Miami",
        "asset_type": "Retail",
        "floor_area_m2": 3200,
        "year_built": 1985,
        "construction_type": "Masonry",
        "elevation_m": 1.5,
        "distance_to_coast_km": 0.3,
        "distance_to_river_km": 6.0,
        "tree_canopy_pct": 8.0,
        "impervious_surface_pct": 90.0,
        "fema_flood_zone": "AE",
        "replacement_value_usd": 12_000_000,
    },
    {
        "name": "San Francisco Office Tower",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "country": "USA",
        "state_province": "CA",
        "city": "San Francisco",
        "asset_type": "Office",
        "floor_area_m2": 8500,
        "year_built": 1994,
        "construction_type": "Steel Frame",
        "elevation_m": 15.0,
        "distance_to_coast_km": 3.5,
        "distance_to_river_km": 10.0,
        "tree_canopy_pct": 22.0,
        "impervious_surface_pct": 72.0,
        "fema_flood_zone": "X",
        "replacement_value_usd": 45_000_000,
    },
    {
        "name": "Phoenix Industrial Complex",
        "latitude": 33.4484,
        "longitude": -112.0740,
        "country": "USA",
        "state_province": "AZ",
        "city": "Phoenix",
        "asset_type": "Industrial",
        "floor_area_m2": 15000,
        "year_built": 2002,
        "construction_type": "Steel Frame",
        "elevation_m": 331.0,
        "distance_to_coast_km": 400.0,
        "distance_to_river_km": 5.0,
        "tree_canopy_pct": 3.0,
        "impervious_surface_pct": 88.0,
        "fema_flood_zone": "X",
        "replacement_value_usd": 28_000_000,
    },
    {
        "name": "Houston Data Center",
        "latitude": 29.7604,
        "longitude": -95.3698,
        "country": "USA",
        "state_province": "TX",
        "city": "Houston",
        "asset_type": "Data Center",
        "floor_area_m2": 4000,
        "year_built": 2015,
        "construction_type": "Concrete",
        "elevation_m": 12.0,
        "distance_to_coast_km": 80.0,
        "distance_to_river_km": 1.5,
        "tree_canopy_pct": 10.0,
        "impervious_surface_pct": 95.0,
        "fema_flood_zone": "AE",
        "replacement_value_usd": 55_000_000,
        "water_intensity_m3_m2": 3.2,
        "energy_intensity_kwh_m2": 1200.0,
    },
    {
        "name": "Denver Logistics Hub",
        "latitude": 39.7392,
        "longitude": -104.9903,
        "country": "USA",
        "state_province": "CO",
        "city": "Denver",
        "asset_type": "Industrial",
        "floor_area_m2": 22000,
        "year_built": 2010,
        "construction_type": "Steel Frame",
        "elevation_m": 1609.0,
        "distance_to_coast_km": 1600.0,
        "distance_to_river_km": 2.0,
        "tree_canopy_pct": 5.0,
        "impervious_surface_pct": 88.0,
        "fema_flood_zone": "X",
        "replacement_value_usd": 18_000_000,
    },
]


async def seed():
    async with httpx.AsyncClient(timeout=30) as client:
        # Create company
        r = await client.post(f"{BASE}/companies/", json=COMPANY)
        r.raise_for_status()
        company = r.json()
        company_id = company["company_id"]
        print(f"Created company: {company['name']} ({company_id})")

        # Create properties
        prop_ids = []
        for prop_data in PROPERTIES:
            prop_data["company_id"] = company_id
            r = await client.post(f"{BASE}/properties/", json=prop_data)
            r.raise_for_status()
            prop = r.json()
            prop_ids.append(prop["property_id"])
            print(f"  Created property: {prop['name']} ({prop['property_id']})")

        # Quick screen all
        print("\nRunning quick screens...")
        for pid in prop_ids:
            r = await client.get(f"{BASE}/risk/property/{pid}/quick?scenario=SSP2-4.5&time_horizon=2050")
            if r.status_code == 200:
                result = r.json()
                print(f"  {result['property_id']}: {result['overall_rating']} ({result['overall_score']:.0f}) — {result['top_hazards']}")

        print(f"\nDemo data seeded. Company ID: {company_id}")
        print(f"Property IDs: {prop_ids}")
        print("\nStart full AI assessment:")
        print(f"  POST {BASE}/agent/run")
        print(f"  Body: {{\"company_id\": \"{company_id}\", \"property_ids\": {prop_ids[:3]}}}")


if __name__ == "__main__":
    asyncio.run(seed())
