"""Wind, hurricane, and severe storm hazard module."""
from typing import Dict, Any, List, Optional
from .base import HazardModule, FeatureInput, ScoredFeature


class WindHazard(HazardModule):
    name = "Wind / Hurricane / Severe Storm"
    description = "High wind, hurricane track, and severe convective storm exposure."

    def collect_features(self, lat: float, lon: float, property_attrs: Dict[str, Any]) -> List[FeatureInput]:
        dist_coast_km = property_attrs.get("distance_to_coast_km")
        year_built = property_attrs.get("year_built")
        construction_type = property_attrs.get("construction_type", "")
        country = property_attrs.get("country", "")
        state = property_attrs.get("state_province", "")

        hurricane_score = self._hurricane_exposure(lat, lon)
        wind_zone = self._design_wind_zone(lat, lon, country, state)
        tornado_score = self._tornado_proxy(lat, lon)
        vuln = self._building_vulnerability(year_built, construction_type)
        coastal_amp = self._coastal_amplification(dist_coast_km)

        return [
            FeatureInput(
                name="hurricane_tropical_cyclone_track",
                value=hurricane_score,
                unit="index_0_100",
                source_name="NOAA IBTrACS / HURDAT2",
                source_url="https://www.ncei.noaa.gov/products/international-best-track-archive",
                data_type="observed",
                notes="Historical TC track density proxy. IBTrACS provides full track dataset.",
            ),
            FeatureInput(
                name="design_wind_zone_proxy",
                value=wind_zone,
                unit="index_0_100",
                source_name="ASCE 7 Wind Speed Map / NOAA Storm Events",
                source_url="https://www.ncei.noaa.gov/stormevents/",
                data_type="observed",
                notes="Proxy from regional wind speed classification.",
            ),
            FeatureInput(
                name="tornado_severe_convective_storm",
                value=tornado_score,
                unit="index_0_100",
                source_name="NOAA Storm Prediction Center Tornado Database",
                source_url="https://www.spc.noaa.gov/gis/svrgis/",
                data_type="observed",
                notes="Tornado alley and Dixie alley receive elevated scores.",
            ),
            FeatureInput(
                name="building_wind_vulnerability",
                value=vuln,
                unit="index_0_100",
                source_name="Building characteristics (user-provided)",
                source_url="",
                data_type="user_provided" if year_built or construction_type else "missing",
                notes="Wood frame pre-1990 buildings have highest wind vulnerability.",
            ),
            FeatureInput(
                name="coastal_wind_amplification",
                value=coastal_amp,
                unit="index_0_100",
                source_name="Distance-to-coast proxy",
                source_url="",
                data_type="estimated" if dist_coast_km is not None else "missing",
                notes="Coastal exposure amplifies wind hazard from landfalling storms.",
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

    def _hurricane_exposure(self, lat: float, lon: float) -> float:
        if 20 < lat < 45 and -100 < lon < -60:  # US East/Gulf
            return 75.0
        if 10 < lat < 25 and -90 < lon < -60:  # Caribbean
            return 85.0
        if 10 < lat < 30 and 100 < lon < 140:  # Western Pacific typhoon
            return 80.0
        if lat < 25 and 50 < lon < 100:  # Indian Ocean
            return 65.0
        return 15.0

    def _design_wind_zone(self, lat: float, lon: float, country: str, state: str) -> float:
        s = str(state).upper()
        if s in ("FL", "LA", "TX", "MS", "AL", "SC", "NC"):
            return 80.0
        if s in ("OK", "KS", "NE", "SD", "ND", "IA", "MN"):
            return 70.0  # Tornado / plains
        if s in ("NY", "NJ", "MA", "CT", "RI"):
            return 60.0
        if 20 < lat < 40 and -100 < lon < -70:
            return 55.0
        return 35.0

    def _tornado_proxy(self, lat: float, lon: float) -> float:
        if 30 < lat < 45 and -100 < lon < -80:  # Tornado alley
            return 80.0
        if 30 < lat < 37 and -90 < lon < -80:  # Dixie alley
            return 75.0
        return 20.0

    def _building_vulnerability(self, year_built: Optional[int], construction: str) -> float:
        score = 50.0
        if year_built and year_built < 1990:
            score += 20.0
        if construction.lower() in ("wood frame",):
            score += 25.0
        elif construction.lower() in ("masonry",):
            score += 10.0
        return round(min(100.0, score), 1)

    def _coastal_amplification(self, dist_km: Optional[float]) -> float:
        if dist_km is None:
            return 40.0
        if dist_km < 1:
            return 85.0
        if dist_km < 5:
            return 65.0
        if dist_km < 20:
            return 45.0
        return 20.0
