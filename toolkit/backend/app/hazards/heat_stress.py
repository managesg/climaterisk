"""Heat stress hazard module."""
from typing import Dict, Any, List, Optional
from .base import HazardModule, FeatureInput, ScoredFeature, normalize


class HeatStressHazard(HazardModule):
    name = "Heat Stress"
    description = "Extreme heat, urban heat island, and cooling demand risk."

    def collect_features(self, lat: float, lon: float, property_attrs: Dict[str, Any]) -> List[FeatureInput]:
        impervious_pct = property_attrs.get("impervious_surface_pct")
        tree_canopy_pct = property_attrs.get("tree_canopy_pct")
        year_built = property_attrs.get("year_built")
        construction_type = property_attrs.get("construction_type", "")
        asset_type = property_attrs.get("asset_type", "")

        projected_heat_days = self._projected_heat_days(lat, lon)
        uhi_score = self._uhi_proxy(impervious_pct, tree_canopy_pct)
        historical_hw = self._historical_heatwave_proxy(lat, lon)
        cooling_vuln = self._cooling_vulnerability(year_built, construction_type, asset_type)
        wet_bulb = self._wet_bulb_proxy(lat, lon)

        return [
            FeatureInput(
                name="projected_extreme_heat_days",
                value=projected_heat_days,
                unit="index_0_100",
                source_name="NASA NEX-GDDP-CMIP6 SSP2-4.5",
                source_url="https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/",
                data_type="modeled",
                notes="Proxy estimate. Replace with actual CMIP6 hot days projections (tasmax > 35°C).",
            ),
            FeatureInput(
                name="urban_heat_island_proxy",
                value=uhi_score,
                unit="index_0_100",
                source_name="NLCD Impervious Surface / Tree Canopy",
                source_url="https://www.usgs.gov/annualNLCD",
                data_type="estimated" if impervious_pct is not None else "missing",
                notes="Derived from impervious surface and canopy coverage.",
            ),
            FeatureInput(
                name="historical_heatwave_frequency",
                value=historical_hw,
                unit="index_0_100",
                source_name="NOAA Storm Events Database",
                source_url="https://www.ncei.noaa.gov/stormevents/",
                data_type="observed",
                notes="Coarse regional proxy from climate zone.",
            ),
            FeatureInput(
                name="cooling_vulnerability",
                value=cooling_vuln,
                unit="index_0_100",
                source_name="Building characteristics (user-provided)",
                source_url="",
                data_type="user_provided" if year_built else "missing",
                notes="Older buildings with poor insulation and no mechanical cooling are most vulnerable.",
            ),
            FeatureInput(
                name="wet_bulb_temperature_proxy",
                value=wet_bulb,
                unit="index_0_100",
                source_name="NOAA Climate Division Data / latitude proxy",
                source_url="https://www.ncei.noaa.gov/",
                data_type="modeled",
                notes="High wet-bulb temps threaten outdoor worker safety and HVAC demand.",
            ),
        ]

    def score_features(self, features: List[FeatureInput]) -> List[ScoredFeature]:
        return [
            ScoredFeature(
                name=f.name, raw_value=f.value, unit=f.unit,
                normalized_score=round(min(100.0, max(0.0, f.value if f.value is not None else 50.0)), 1),
                source_name=f.source_name, source_url=f.source_url,
                data_type=f.data_type, notes=f.notes,
            )
            for f in features
        ]

    def _projected_heat_days(self, lat: float, lon: float) -> float:
        if abs(lat) < 25:
            return 85.0
        if 25 < lat < 35:
            return 70.0
        if 35 < lat < 45:
            return 55.0
        if 45 < lat < 55:
            return 35.0
        return 20.0

    def _uhi_proxy(self, impervious: Optional[float], canopy: Optional[float]) -> float:
        score = 50.0
        if impervious is not None:
            score += (impervious - 50) * 0.5
        if canopy is not None:
            score -= canopy * 0.3
        return round(max(0.0, min(100.0, score)), 1)

    def _historical_heatwave_proxy(self, lat: float, lon: float) -> float:
        if 32 < lat < 38 and -100 < lon < -80:  # US Southeast
            return 72.0
        if lat < 30:
            return 80.0
        if 35 < lat < 45 and 0 < lon < 30:  # Southern Europe
            return 68.0
        if 40 < lat < 50:
            return 40.0
        return 30.0

    def _cooling_vulnerability(self, year_built: Optional[int], construction: str, asset_type: str) -> float:
        score = 50.0
        if year_built is not None:
            if year_built < 1970:
                score += 25.0
            elif year_built < 1990:
                score += 10.0
        if construction.lower() in ("wood frame", "masonry"):
            score += 10.0
        if asset_type.lower() in ("warehouse", "industrial"):
            score += 15.0
        return round(min(100.0, score), 1)

    def _wet_bulb_proxy(self, lat: float, lon: float) -> float:
        if abs(lat) < 20:
            return 80.0
        if 20 < abs(lat) < 30:
            return 65.0
        if 30 < abs(lat) < 40:
            return 50.0
        return 30.0
