"""Coastal flood / sea level rise hazard scorer — 7 features."""

from ..data.providers.usgs_elevation import USGSElevationProvider
from ..data.providers.noaa_sea_level import NOAASeaLevelProvider
from ..data.providers.fema_flood import FEMAFloodProvider
from ..data.providers.stub import StubProvider
from ..models.enums import DataType, HazardType
from .base import FeatureScore, HazardResult, HazardScorer
from .scoring import compute_category_score, rating_from_score


class CoastalFloodScorer(HazardScorer):
    """Score coastal flood and sea level rise risk using 7 features."""

    hazard_type = HazardType.COASTAL_FLOOD

    def __init__(self) -> None:
        self._elevation = USGSElevationProvider()
        self._slr = NOAASeaLevelProvider()
        self._fema = FEMAFloodProvider()
        self._surge_stub = StubProvider("storm_surge", "Requires NOAA SLOSH or ADCIRC model output.")
        self._tidal_stub = StubProvider("tidal_flooding", "Requires NOAA tidal flooding frequency data.")
        self._erosion_stub = StubProvider("coastal_erosion", "Requires USGS Coastal Change Hazards data.")

    async def score(
        self,
        lat: float,
        lon: float,
        property_data: dict,
        scenario: str,
        year: int,
    ) -> HazardResult:
        elev_data = await self._elevation.fetch(lat, lon)
        slr_data = await self._slr.fetch(lat, lon)
        fema_data = await self._fema.fetch(lat, lon)

        features: list[FeatureScore] = []

        # 1. Distance to coastline (property-provided or default)
        dist_coast = property_data.get("distance_to_coast")
        # Inverse: closer to coast = higher score
        coast_score = max(0.0, 100.0 - self.normalize(dist_coast or 50, 0, 100)) if dist_coast else 50.0
        features.append(FeatureScore(
            feature_name="distance_to_coastline",
            raw_value=dist_coast,
            normalized_score=coast_score,
            source="user_provided",
            data_type=DataType.USER_PROVIDED if dist_coast is not None else DataType.MISSING,
            is_available=dist_coast is not None,
            confidence=0.9 if dist_coast is not None else 0.0,
            note=f"{dist_coast} km to coast" if dist_coast else None,
        ))

        # 2. Elevation (low elevation = higher coastal exposure)
        elev_m = elev_data.get("elevation_m") or property_data.get("elevation")
        elev_score = max(0.0, 100.0 - self.normalize(elev_m or 5, 0, 20)) if elev_m is not None else 50.0
        features.append(FeatureScore(
            feature_name="elevation",
            raw_value=elev_m,
            normalized_score=elev_score,
            source="usgs_3dep" if self._elevation.is_available() else "user_provided",
            source_url="https://www.usgs.gov/3d-elevation-program",
            data_type=DataType.OBSERVED if self._elevation.is_available() else (
                DataType.USER_PROVIDED if elev_m else DataType.MISSING),
            is_available=self._elevation.is_available() or elev_m is not None,
            confidence=0.85,
        ))

        # 3. FEMA coastal flood zone
        zone_sev = fema_data.get("zone_severity") or 0.0
        features.append(FeatureScore(
            feature_name="fema_coastal_flood_zone",
            raw_value=fema_data.get("flood_zone"),
            normalized_score=float(zone_sev),
            source=self._fema.name,
            source_url="https://www.fema.gov/flood-maps",
            data_type=DataType.OBSERVED if self._fema.is_available() else DataType.MISSING,
            is_available=self._fema.is_available(),
            confidence=0.9 if self._fema.is_available() else 0.0,
        ))

        # 4. Sea level rise trend (mm/yr)
        slr = slr_data.get("slr_mm_per_yr")
        # Typical range: 0-10 mm/yr; some hotspot locations 15+ mm/yr
        slr_score = self.normalize(slr or 3.0, 0, 12) if slr is not None else 30.0
        features.append(FeatureScore(
            feature_name="sea_level_trend",
            raw_value=slr,
            normalized_score=slr_score,
            source=self._slr.name,
            source_url="https://www.tidesandcurrents.noaa.gov/sltrends/",
            data_type=DataType.OBSERVED if self._slr.is_available() else DataType.MISSING,
            is_available=self._slr.is_available(),
            confidence=0.9 if self._slr.is_available() else 0.0,
            note=slr_data.get("nearest_gauge"),
        ))

        # 5. Storm surge exposure (stub)
        features.append(FeatureScore(
            feature_name="storm_surge_exposure",
            raw_value=None,
            normalized_score=0.0,
            source=self._surge_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="Requires NOAA SLOSH or ADCIRC storm surge model.",
        ))

        # 6. Tidal flooding frequency (stub)
        features.append(FeatureScore(
            feature_name="tidal_flooding_frequency",
            raw_value=None,
            normalized_score=0.0,
            source=self._tidal_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="Requires NOAA tidal flooding frequency dataset.",
        ))

        # 7. Coastal erosion proxy (stub)
        features.append(FeatureScore(
            feature_name="coastal_erosion",
            raw_value=None,
            normalized_score=0.0,
            source=self._erosion_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="Requires USGS Coastal Change Hazards Portal data.",
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
                "Commission coastal engineering assessment and evaluate SLR adaptation strategy."
                if cat_score > 60 else
                "Monitor sea level trends and review coastal flood insurance annually."
            ),
        )
