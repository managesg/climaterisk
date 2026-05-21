"""Coastal flood and sea level rise hazard module."""
from typing import Dict, Any, List, Optional
from .base import HazardModule, FeatureInput, ScoredFeature, normalize


class CoastalFloodHazard(HazardModule):
    name = "Coastal Flood / Sea Level Rise"
    description = "Coastal inundation, storm surge, and sea level rise exposure screening."

    def collect_features(self, lat: float, lon: float, property_attrs: Dict[str, Any]) -> List[FeatureInput]:
        dist_coast_km = property_attrs.get("distance_to_coast_km")
        elevation_m = property_attrs.get("elevation_m")
        fema_zone = property_attrs.get("fema_flood_zone", "")

        coastal_score = self._coastal_proximity_score(dist_coast_km)
        slr_score = self._slr_exposure(lat, lon, elevation_m)
        surge_score = self._storm_surge_proxy(lat, lon, dist_coast_km)
        fema_coastal = self._fema_coastal_score(fema_zone)
        erosion_score = self._coastal_erosion_proxy(lat, lon)

        not_coastal = dist_coast_km is not None and dist_coast_km > 50

        return [
            FeatureInput(
                name="distance_to_coastline",
                value=coastal_score,
                unit="index_0_100",
                source_name="NOAA Coastline / OpenStreetMap",
                source_url="https://coast.noaa.gov/nationalviewer/",
                data_type="estimated" if dist_coast_km is not None else "missing",
                notes=f"Distance: {dist_coast_km} km" if dist_coast_km else "Not provided.",
            ),
            FeatureInput(
                name="sea_level_rise_exposure",
                value=0.0 if not_coastal else slr_score,
                unit="index_0_100",
                source_name="NOAA Tides & Currents SLR trends",
                source_url="https://www.tidesandcurrents.noaa.gov/sltrends/",
                data_type="modeled",
                notes="Scenario-based SLR proxy. Replace with NOAA CO-OPS gauge data.",
            ),
            FeatureInput(
                name="storm_surge_exposure",
                value=0.0 if not_coastal else surge_score,
                unit="index_0_100",
                source_name="NOAA National Hurricane Center / SLOSH model proxy",
                source_url="https://www.nhc.noaa.gov/surge/",
                data_type="modeled",
                notes="Gulf/Atlantic coasts receive higher scores. SLOSH model data recommended.",
            ),
            FeatureInput(
                name="fema_coastal_flood_zone",
                value=fema_coastal,
                unit="index_0_100",
                source_name="FEMA NFHL",
                source_url="https://www.fema.gov/flood-maps",
                data_type="observed" if fema_zone else "missing",
                notes=f"Zone: {fema_zone or 'not provided'}",
            ),
            FeatureInput(
                name="coastal_erosion_proxy",
                value=0.0 if not_coastal else erosion_score,
                unit="index_0_100",
                source_name="USGS Coastal Change Hazards Portal",
                source_url="https://marine.usgs.gov/coastalchangehazardsportal/",
                data_type="estimated",
                notes="Coarse proxy by geography. USGS CVI data recommended.",
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

    def _coastal_proximity_score(self, dist_km: Optional[float]) -> float:
        if dist_km is None:
            return 30.0
        if dist_km < 0.5:
            return 95.0
        if dist_km < 2:
            return 80.0
        if dist_km < 10:
            return 60.0
        if dist_km < 25:
            return 35.0
        if dist_km < 50:
            return 15.0
        return 0.0

    def _slr_exposure(self, lat: float, lon: float, elevation_m: Optional[float]) -> float:
        base = 50.0
        if elevation_m is not None and elevation_m < 3:
            base = 85.0
        elif elevation_m is not None and elevation_m < 10:
            base = 65.0
        # Subsiding coasts (US Gulf, Chesapeake, SE Asia)
        if 25 < lat < 32 and -100 < lon < -80:  # Gulf Coast
            return min(100.0, base + 15.0)
        return base

    def _storm_surge_proxy(self, lat: float, lon: float, dist_km: Optional[float]) -> float:
        if dist_km and dist_km > 30:
            return 5.0
        # Atlantic / Gulf hurricane belt
        if 20 < lat < 40 and -100 < lon < -60:
            return 75.0
        # Tropical cyclone zones
        if lat < 30:
            return 65.0
        return 35.0

    def _fema_coastal_score(self, zone: str) -> float:
        z = (zone or "").upper().strip()
        if not z:
            return 50.0
        if z.startswith("V") or z in ("VE",):
            return 95.0
        if z.startswith("A"):
            return 70.0
        return 15.0

    def _coastal_erosion_proxy(self, lat: float, lon: float) -> float:
        if 35 < lat < 50 and -80 < lon < -65:  # US NE coast
            return 60.0
        if 25 < lat < 32 and -100 < lon < -80:  # Gulf Coast
            return 65.0
        return 40.0
