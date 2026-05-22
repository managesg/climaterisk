"""Drought and water stress hazard module."""
from typing import Dict, Any, List, Optional
from .base import HazardModule, FeatureInput, ScoredFeature, normalize


class DroughtHazard(HazardModule):
    name = "Drought / Water Stress"
    description = "Drought frequency, water stress basin risk, and water dependency."

    def collect_features(self, lat: float, lon: float, property_attrs: Dict[str, Any]) -> List[FeatureInput]:
        water_intensity = property_attrs.get("water_intensity_m3_m2")
        asset_type = property_attrs.get("asset_type", "")
        country = property_attrs.get("country", "")

        drought_class = self._drought_class_proxy(lat, lon)
        precip_change = self._precipitation_change_proxy(lat, lon)
        water_stress = self._water_stress_proxy(lat, lon, country)
        soil_moisture = self._soil_moisture_proxy(lat, lon)
        water_demand = self._water_demand_score(water_intensity, asset_type)

        return [
            FeatureInput(
                name="current_drought_class",
                value=drought_class,
                unit="index_0_100",
                source_name="US Drought Monitor / global drought proxy",
                source_url="https://www.drought.gov/data-maps-tools/us-drought-monitor",
                data_type="observed",
                notes="Coarse regional proxy. US Drought Monitor provides weekly D0-D4 classification.",
            ),
            FeatureInput(
                name="projected_precipitation_change",
                value=precip_change,
                unit="index_0_100",
                source_name="NASA NEX-GDDP-CMIP6 SSP2-4.5",
                source_url="https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/",
                data_type="modeled",
                notes="Negative precipitation trends increase drought risk.",
            ),
            FeatureInput(
                name="water_stress_basin",
                value=water_stress,
                unit="index_0_100",
                source_name="WRI Aqueduct Water Risk Atlas",
                source_url="https://www.wri.org/aqueduct",
                data_type="modeled",
                notes="WRI Aqueduct Overall Water Risk recommended for precision.",
            ),
            FeatureInput(
                name="soil_moisture_proxy",
                value=soil_moisture,
                unit="index_0_100",
                source_name="NASA SMAP / latitude proxy",
                source_url="https://smap.jpl.nasa.gov/",
                data_type="estimated",
                notes="Proxy from climate zone. NASA SMAP soil moisture data recommended.",
            ),
            FeatureInput(
                name="water_demand_intensity",
                value=water_demand,
                unit="index_0_100",
                source_name="User-provided water intensity",
                source_url="",
                data_type="user_provided" if water_intensity is not None else "missing",
                notes="High water-using operations face greater drought exposure.",
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

    def _drought_class_proxy(self, lat: float, lon: float) -> float:
        if 30 < lat < 40 and -120 < lon < -100:  # US Southwest
            return 80.0
        if 25 < lat < 35 and -110 < lon < -95:  # Southern Plains
            return 70.0
        if -35 < lat < -10 and 115 < lon < 155:  # Australia
            return 65.0
        if 30 < lat < 45 and 0 < lon < 40:  # MENA
            return 75.0
        if 35 < lat < 45 and -10 < lon < 10:  # Iberia
            return 65.0
        return 35.0

    def _precipitation_change_proxy(self, lat: float, lon: float) -> float:
        # Drying regions under SSP2-4.5
        if 25 < lat < 45 and -120 < lon < -100:
            return 70.0
        if 30 < lat < 45 and 0 < lon < 40:
            return 65.0
        return 40.0

    def _water_stress_proxy(self, lat: float, lon: float, country: str) -> float:
        high_stress = {"India", "IN", "Pakistan", "SA", "Iran", "IR", "Iraq", "Jordan"}
        if country in high_stress:
            return 85.0
        if 30 < lat < 40 and -120 < lon < -100:
            return 75.0
        return 40.0

    def _soil_moisture_proxy(self, lat: float, lon: float) -> float:
        if abs(lat) < 20:
            return 30.0  # Tropics — humid
        if 25 < lat < 45 and -120 < lon < -90:
            return 70.0
        if 30 < lat < 45 and 0 < lon < 45:
            return 68.0
        return 40.0

    def _water_demand_score(self, intensity: Optional[float], asset_type: str) -> float:
        if asset_type.lower() in ("data center", "industrial", "manufacturing"):
            return 75.0
        if intensity is not None and intensity > 2.0:
            return 70.0
        if intensity is not None and intensity > 0.5:
            return 45.0
        return 30.0
