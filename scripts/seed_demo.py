#!/usr/bin/env python3
"""
Seed demo data into the SeaBridge API.
Run after `docker compose up` when the API is healthy.

Usage:
    python scripts/seed_demo.py [--api http://localhost:8000]
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def post(base: str, path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get(base: str, path: str) -> dict:
    with urllib.request.urlopen(f"{base}{path}") as resp:
        return json.loads(resp.read())


def wait_for_api(base: str, retries: int = 30) -> None:
    for i in range(retries):
        try:
            get(base, "/health")
            print(f"  API ready ({base})")
            return
        except Exception:
            print(f"  Waiting for API… ({i+1}/{retries})")
            time.sleep(2)
    print("ERROR: API did not become ready in time.", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()
    base = args.api.rstrip("/")

    wait_for_api(base)

    # ── Check idempotency ─────────────────────────────────────────────────────
    existing = get(base, "/api/v1/companies")
    if existing:
        print(f"Demo data already seeded ({len(existing)} companies). Skipping.")
        return

    # ── Company ───────────────────────────────────────────────────────────────
    print("Creating demo company…")
    company = post(base, "/api/v1/companies", {
        "name": "SeaBridge Demo Corp",
        "sector": "Real Estate",
        "industry": "Diversified REITs",
        "geography": "United States",
        "revenue": 850_000_000,
        "asset_value": 4_200_000_000,
        "emissions": 42_000,
        "energy_use": 185_000,
        "water_use": 9_200,
        "reporting_boundary": "Operational control — US portfolio",
    })
    cid = company["company_id"]
    print(f"  company_id: {cid}")

    # ── Properties ────────────────────────────────────────────────────────────
    PROPERTIES = [
        {
            "name": "Miami Beach Waterfront Condo",
            "address": "100 Ocean Dr, Miami Beach, FL 33139",
            "latitude": 25.7749,
            "longitude": -80.1341,
            "country": "US", "state": "FL", "city": "Miami Beach",
            "asset_type": "residential",
            "floor_area": 4_200,
            "year_built": 1998,
            "occupancy": "residential",
            "construction_type": "concrete",
            "elevation": 1.2,
            "distance_to_coast": 0.08,
            "distance_to_river": 2.1,
            "replacement_value": 12_000_000,
            "business_interruption_value": 480_000,
        },
        {
            "name": "Sacramento Valley Office Park",
            "address": "2200 Butano Dr, Sacramento, CA 95825",
            "latitude": 38.6202,
            "longitude": -121.3972,
            "country": "US", "state": "CA", "city": "Sacramento",
            "asset_type": "office",
            "floor_area": 28_500,
            "year_built": 2005,
            "occupancy": "office",
            "construction_type": "steel_frame",
            "elevation": 8.4,
            "distance_to_coast": 115.0,
            "distance_to_river": 4.2,
            "replacement_value": 34_000_000,
            "business_interruption_value": 5_200_000,
        },
        {
            "name": "Houston Logistics Warehouse",
            "address": "8500 Will Clayton Pkwy, Humble, TX 77338",
            "latitude": 29.9901,
            "longitude": -95.2671,
            "country": "US", "state": "TX", "city": "Houston",
            "asset_type": "industrial",
            "floor_area": 92_000,
            "year_built": 2012,
            "occupancy": "warehouse",
            "construction_type": "steel_frame",
            "elevation": 22.1,
            "distance_to_coast": 65.0,
            "distance_to_river": 1.8,
            "replacement_value": 48_000_000,
            "business_interruption_value": 9_800_000,
        },
        {
            "name": "Phoenix Data Center Campus",
            "address": "2355 E Camelback Rd, Phoenix, AZ 85016",
            "latitude": 33.5092,
            "longitude": -112.0150,
            "country": "US", "state": "AZ", "city": "Phoenix",
            "asset_type": "data_center",
            "floor_area": 15_000,
            "year_built": 2018,
            "occupancy": "data_center",
            "construction_type": "concrete",
            "elevation": 331.0,
            "distance_to_coast": 480.0,
            "distance_to_river": 8.3,
            "replacement_value": 120_000_000,
            "business_interruption_value": 62_000_000,
        },
    ]

    property_ids = []
    for p in PROPERTIES:
        prop = post(base, "/api/v1/properties", {"company_id": cid, **p})
        pid = prop["property_id"]
        property_ids.append(pid)
        print(f"  property: {p['name']} → {pid}")

    # ── Run assessments ───────────────────────────────────────────────────────
    for scenario, year in [("ssp245", 2050), ("ssp585", 2050), ("ssp245", 2030)]:
        print(f"  Running {scenario}/{year} assessments…")
        result = post(base, "/api/v1/assessments/run", {
            "company_id": cid,
            "property_ids": property_ids,
            "scenario": scenario,
            "time_horizon": year,
        })
        print(f"    → {result['count']} assessments created")

    print()
    print("Demo data seeded.")
    print(f"  Company ID : {cid}")
    print(f"  Properties : {len(property_ids)}")
    print(f"  Open the app at http://localhost:4000")


if __name__ == "__main__":
    main()
