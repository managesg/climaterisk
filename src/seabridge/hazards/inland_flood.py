"""Inland flood hazard scorer — 8 features."""

from ..data.providers.fema_flood import FEMAFloodProvider
from ..data.providers.usgs_elevation import USGSElevationProvider
from ..data.providers.nasa_nexgddp import NASANexGDDPProvider
from ..data.providers.noaa_storm_events import NOAAStormEventsProvider
from ..data.providers.nlcd import NLCDProvider
from ..data.providers.stub import StubProvider
from ..models.enums import DataType, HazardType
from .base import FeatureScore, HazardResult, HazardScorer
from .scoring import compute_category_score, rating_from_score


class InlandFloodScorer(HazardScorer):
    """Score inland (riverine/pluvial) flood risk using 8 features."""

    hazard_type = HazardType.INLAND_FLOOD

    def __init__(self) -> None:
        self._fema = FEMAFloodProvider()
        self._elevation = USGSElevationProvider()
        self._climate = NASANexGDDPProvider()
        self._storm_events = NOAAStormEventsProvider()
        self._nlcd = NLCDProvider()
        self._soil_stub = StubProvider("soil_permeability", "Requires SSURGO soil data.")
        self._watershed_stub = StubProvider("watershed_drainage", "Requires NHDPlus hydrography.")

    async def score(
        self,
        lat: float,
        lon: float,
        property_data: dict,
        scenario: str,
        year: int,
    ) -> HazardResult:
        fema_data = await self._fema.fetch(lat, lon)
        elev_data = await self._elevation.fetch(lat, lon)
        climate_data = await self._climate.fetch(lat, lon, scenario=scenario, year=year)
        storm_data = await self._storm_events.fetch(lat, lon)
        nlcd_data = await self._nlcd.fetch(lat, lon)

        features: list[FeatureScore] = []

        # 1. FEMA flood zone
        zone_sev = fema_data.get("zone_severity")
        features.append(FeatureScore(
            feature_name="fema_flood_zone",
            raw_value=fema_data.get("flood_zone"),
            normalized_score=float(zone_sev) if zone_sev is not None else 0.0,
            source=self._fema.name,
            source_url="https://www.fema.gov/flood-maps",
            data_type=DataType.OBSERVED if self._fema.is_available() else DataType.MISSING,
            is_available=self._fema.is_available(),
            confidence=0.9 if self._fema.is_available() else 0.0,
        ))

        # 2. Distance to river/stream
        dist_river = property_data.get("distance_to_river")
        river_score = self.normalize(1.0 / max(dist_river, 0.1), 0, 10) if dist_river else 30.0
        features.append(FeatureScore(
            feature_name="distance_to_river",
            raw_value=dist_river,
            normalized_score=river_score,
            source="user_provided",
            data_type=DataType.USER_PROVIDED if dist_river is not None else DataType.MISSING,
            is_available=dist_river is not None,
            confidence=0.8 if dist_river is not None else 0.0,
            note=f"{dist_river} km to nearest river" if dist_river else None,
        ))

        # 3. Elevation above drainage (low elevation = higher flood exposure)
        elev_m = elev_data.get("elevation_m") or property_data.get("elevation")
        elev_score = max(0.0, 100.0 - self.normalize(elev_m or 10, 0, 50)) if elev_m else 50.0
        features.append(FeatureScore(
            feature_name="elevation_above_drainage",
            raw_value=elev_m,
            normalized_score=elev_score,
            source="usgs_3dep" if self._elevation.is_available() else "user_provided",
            source_url="https://www.usgs.gov/3d-elevation-program",
            data_type=DataType.OBSERVED if self._elevation.is_available() else (
                DataType.USER_PROVIDED if elev_m else DataType.MISSING),
            is_available=self._elevation.is_available() or elev_m is not None,
            confidence=0.75,
        ))

        # 4. Extreme precipitation change (projected %)
        precip_change = climate_data.get("precip_change_pct") or 0.0
        # Negative = drier; positive = wetter. For flood risk, larger negative = drier regions
        # but sudden intense events still increase. Use absolute magnitude.
        precip_score = self.normalize(abs(precip_change), 0, 25)
        features.append(FeatureScore(
            feature_name="extreme_precipitation",
            raw_value=precip_change,
            normalized_score=precip_score,
            source=self._climate.name,
            source_url="https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/",
            data_type=DataType.SCENARIO,
            is_available=True,
            confidence=0.55,
            note=f"Projected precip change: {precip_change}% ({scenario}, {year})",
        ))

        # 5. Soil permeability (stub)
        features.append(FeatureScore(
            feature_name="soil_permeability",
            raw_value=None,
            normalized_score=0.0,
            source=self._soil_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="Requires USDA SSURGO soil survey data.",
        ))

        # 6. Watershed drainage capacity (stub)
        features.append(FeatureScore(
            feature_name="watershed_drainage",
            raw_value=None,
            normalized_score=0.0,
            source=self._watershed_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="Requires NHDPlus hydrography data.",
        ))

        # 7. Impervious surface (higher = faster runoff)
        imperv = nlcd_data.get("impervious_fraction") or property_data.get("impervious_surface")
        imperv_score = self.normalize(imperv or 0.3, 0, 1.0) if imperv else 30.0
        features.append(FeatureScore(
            feature_name="impervious_surface",
            raw_value=imperv,
            normalized_score=imperv_score,
            source="nlcd" if nlcd_data.get("available") else "user_provided",
            source_url="https://www.usgs.gov/annualNLCD",
            data_type=DataType.OBSERVED if nlcd_data.get("available") else (
                DataType.USER_PROVIDED if imperv else DataType.MISSING),
            is_available=nlcd_data.get("available", False) or imperv is not None,
            confidence=0.7,
        ))

        # 8. Historical flood events
        flood_events = storm_data.get("flood_events_30yr")
        features.append(FeatureScore(
            feature_name="historical_flood_events",
            raw_value=flood_events,
            normalized_score=self.normalize(flood_events or 0, 0, 30) if flood_events else 0.0,
            source=self._storm_events.name,
            source_url="https://www.ncei.noaa.gov/stormevents/",
            data_type=DataType.OBSERVED if self._storm_events.is_available() else DataType.MISSING,
            is_available=self._storm_events.is_available(),
            confidence=0.85 if self._storm_events.is_available() else 0.0,
        ))

        scores = [f.normalized_score for f in features]
        cat_score = compute_category_score(scores)
        available = [f for f in features if f.is_available]
        confidence = sum(f.confidence for f in available) / len(available) if available else 0.0

        return HazardResult(
            hazard_type=self.hazard_type,
            feature_scores=features,
            category_score=cat_score,
            rating=rating_from_score(cat_score),
            confidence=confidence,
            top_drivers=[f.feature_name for f in sorted(features, key=lambda f: f.normalized_score, reverse=True)[:3]],
            data_gaps=[f.feature_name for f in features if not f.is_available],
            recommended_action=(
                "Commission detailed hydrological study and review flood insurance."
                if cat_score > 60 else
                "Review FEMA flood maps and consider flood-resilient retrofits."
            ),
        )
