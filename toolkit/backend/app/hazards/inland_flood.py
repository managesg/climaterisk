"""Inland flood hazard module."""
from typing import Dict, Any, List, Optional
from .base import HazardModule, FeatureInput, ScoredFeature, normalize


class InlandFloodHazard(HazardModule):
    name = "Inland Flood"
    description = "Riverine and pluvial flood risk screening."

    FEMA_HIGH_RISK_ZONES = {"A", "AE", "AO", "AH", "VE", "V", "AE-FLOODWAY"}

    def collect_features(self, lat: float, lon: float, property_attrs: Dict[str, Any]) -> List[FeatureInput]:
        fema_zone = property_attrs.get("fema_flood_zone", "")
        elevation_m = property_attrs.get("elevation_m")
        dist_river_km = property_attrs.get("distance_to_river_km")
        impervious_pct = property_attrs.get("impervious_surface_pct")

        # Derive flood zone risk
        fema_score = self._fema_zone_score(fema_zone)
        elev_score = self._elevation_score(elevation_m)
        river_score = self._river_proximity_score(dist_river_km)
        precip_score = self._precipitation_proxy(lat, lon)
        impervious_score = normalize(impervious_pct or 50.0, 0, 100)

        return [
            FeatureInput(
                name="fema_flood_zone",
                value=fema_score,
                unit="index_0_100",
                source_name="FEMA National Flood Hazard Layer",
                source_url="https://www.fema.gov/flood-maps",
                data_type="observed" if fema_zone else "missing",
                notes=f"Zone: {fema_zone or 'not provided'}. User-supplied.",
            ),
            FeatureInput(
                name="elevation_above_drainage",
                value=elev_score,
                unit="index_0_100",
                source_name="USGS 3DEP DEM",
                source_url="https://www.usgs.gov/3d-elevation-program",
                data_type="estimated" if elevation_m is not None else "missing",
                notes="Low elevation = higher flood exposure.",
            ),
            FeatureInput(
                name="distance_to_river_stream",
                value=river_score,
                unit="index_0_100",
                source_name="NHD / OpenStreetMap waterways",
                source_url="https://www.usgs.gov/national-hydrography",
                data_type="estimated" if dist_river_km is not None else "missing",
                notes="Closer proximity = higher score.",
            ),
            FeatureInput(
                name="extreme_precipitation_proxy",
                value=precip_score,
                unit="index_0_100",
                source_name="NOAA MRMS / NASA NEX-GDDP-CMIP6",
                source_url="https://vlab.noaa.gov/web/mrms",
                data_type="modeled",
                notes="Coarse climate-zone proxy. NEX-GDDP-CMIP6 recommended for production.",
            ),
            FeatureInput(
                name="impervious_surface",
                value=impervious_score,
                unit="index_0_100",
                source_name="NLCD Impervious Surface",
                source_url="https://www.usgs.gov/annualNLCD",
                data_type="estimated" if impervious_pct is not None else "missing",
                notes="Higher impervious surface reduces infiltration, increases runoff.",
            ),
        ]

    def score_features(self, features: List[FeatureInput]) -> List[ScoredFeature]:
        return [
            ScoredFeature(
                name=f.name, raw_value=f.raw_value if hasattr(f, 'raw_value') else f.value,
                unit=f.unit,
                normalized_score=round(min(100.0, max(0.0, f.value if f.value is not None else 50.0)), 1),
                source_name=f.source_name, source_url=f.source_url,
                data_type=f.data_type, notes=f.notes,
            )
            for f in features
        ]

    def _fema_zone_score(self, zone: str) -> float:
        z = (zone or "").upper().strip()
        if not z:
            return 50.0  # missing = conservative
        if z in self.FEMA_HIGH_RISK_ZONES or z.startswith("A") or z.startswith("V"):
            return 90.0
        if z in ("B", "X500", "0.2 PCT ANNUAL CHANCE"):
            return 45.0
        if z in ("C", "X", "X UNSHADED"):
            return 10.0
        return 50.0

    def _elevation_score(self, elevation_m: Optional[float]) -> float:
        if elevation_m is None:
            return 50.0
        if elevation_m < 5:
            return 80.0
        if elevation_m < 20:
            return 55.0
        if elevation_m < 100:
            return 30.0
        return 10.0

    def _river_proximity_score(self, dist_km: Optional[float]) -> float:
        if dist_km is None:
            return 50.0
        if dist_km < 0.1:
            return 95.0
        if dist_km < 0.5:
            return 75.0
        if dist_km < 2:
            return 50.0
        if dist_km < 10:
            return 25.0
        return 10.0

    def _precipitation_proxy(self, lat: float, lon: float) -> float:
        # Gulf Coast, SE US, tropics: higher precip risk
        if 25 < lat < 35 and -100 < lon < -75:
            return 70.0
        if lat < 25:
            return 60.0
        if 40 < lat < 55 and -10 < lon < 20:
            return 55.0  # NW Europe
        return 40.0
