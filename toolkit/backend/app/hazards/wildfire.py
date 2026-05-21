"""Wildfire hazard module — open-access screening tier."""
from typing import Dict, Any, List, Optional
import math
from .base import HazardModule, FeatureInput, ScoredFeature, normalize, normalize_inverse


class WildfireHazard(HazardModule):
    name = "Wildfire"
    description = "Wildfire risk scoring based on climate, fuel, terrain, and exposure features."

    # US states with historically elevated wildfire risk
    HIGH_RISK_STATES = {
        "CA", "OR", "WA", "NV", "AZ", "NM", "CO", "UT", "ID", "MT",
        "WY", "TX", "FL", "GA", "NC"
    }

    def collect_features(self, lat: float, lon: float, property_attrs: Dict[str, Any]) -> List[FeatureInput]:
        state = property_attrs.get("state_province", "")
        country = property_attrs.get("country", "")
        elevation_m = property_attrs.get("elevation_m")
        tree_canopy_pct = property_attrs.get("tree_canopy_pct")
        impervious_pct = property_attrs.get("impervious_surface_pct")
        land_cover = property_attrs.get("land_cover", "")

        # Climate zone proxy from latitude (coarse)
        climate_aridity = self._aridity_proxy(lat, lon, country, state)
        slope_proxy = self._slope_proxy(elevation_m)
        vegetation_score = self._vegetation_proxy(tree_canopy_pct, impervious_pct, land_cover)
        state_risk = 100.0 if str(state).upper() in self.HIGH_RISK_STATES else 30.0

        return [
            FeatureInput(
                name="climate_aridity_proxy",
                value=climate_aridity,
                unit="index_0_100",
                source_name="Latitude/longitude climate zone estimate",
                source_url="https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/",
                data_type="estimated",
                notes="Coarse aridity estimate from geographic position. Replace with NEX-GDDP-CMIP6 for production.",
            ),
            FeatureInput(
                name="vegetation_fuel_proxy",
                value=vegetation_score,
                unit="index_0_100",
                source_name="NLCD Tree Canopy / LANDFIRE proxy",
                source_url="https://landfire.gov/data",
                data_type="estimated" if tree_canopy_pct is not None else "missing",
                notes="Derived from tree canopy % if available. LANDFIRE fuels data recommended.",
            ),
            FeatureInput(
                name="slope_elevation_proxy",
                value=slope_proxy,
                unit="index_0_100",
                source_name="Elevation proxy",
                source_url="https://www.usgs.gov/3d-elevation-program",
                data_type="estimated" if elevation_m is not None else "missing",
                notes="Slope increases fire spread. USGS 3DEP recommended.",
            ),
            FeatureInput(
                name="state_historical_risk",
                value=state_risk,
                unit="index_0_100",
                source_name="NIFC wildfire history / US state risk tier",
                source_url="https://www.nifc.gov/fire-information/statistics",
                data_type="observed",
                notes="Binary high/low based on NIFC high-risk state classification.",
            ),
            FeatureInput(
                name="smoke_air_quality_exposure",
                value=self._smoke_proxy(lat, lon, state, country),
                unit="index_0_100",
                source_name="EPA AQS smoke event proxy",
                source_url="https://www.epa.gov/aqs",
                data_type="estimated",
                notes="Coarse proxy. EPA smoke event data recommended.",
            ),
        ]

    def score_features(self, features: List[FeatureInput]) -> List[ScoredFeature]:
        scored = []
        for f in features:
            if f.value is None:
                score = 50.0  # conservative median for missing data
            else:
                score = round(min(100.0, max(0.0, f.value)), 1)
            scored.append(ScoredFeature(
                name=f.name, raw_value=f.value, unit=f.unit,
                normalized_score=score, source_name=f.source_name,
                source_url=f.source_url, data_type=f.data_type, notes=f.notes,
            ))
        return scored

    def _aridity_proxy(self, lat: float, lon: float, country: str, state: str) -> float:
        # Mediterranean / semi-arid zones have higher wildfire risk
        if country in ("USA", "US", "United States"):
            if lon < -100:  # Western US
                return 70.0
            return 35.0
        if -35 < lat < 35:  # Tropical — lower wildfire, higher humidity
            return 30.0
        if 30 < lat < 50 and lon > 0:  # Southern Europe
            return 60.0
        return 40.0

    def _vegetation_proxy(self, canopy_pct: Optional[float], impervious: Optional[float], land_cover: str) -> float:
        if land_cover.lower() in ("forest", "shrubland", "grassland"):
            return 75.0
        if impervious is not None and impervious > 80:
            return 10.0
        if canopy_pct is not None:
            return normalize(canopy_pct, 0, 80)
        return 50.0

    def _slope_proxy(self, elevation_m: Optional[float]) -> float:
        if elevation_m is None:
            return 50.0
        if elevation_m > 1500:
            return 65.0
        if elevation_m > 500:
            return 45.0
        return 30.0

    def _smoke_proxy(self, lat: float, lon: float, state: str, country: str) -> float:
        if country in ("USA", "US", "United States") and str(state).upper() in ("CA", "OR", "WA"):
            return 70.0
        if lon < -100:
            return 50.0
        return 25.0
