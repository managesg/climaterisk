"""Wind / hurricane / severe storm hazard scorer — 7 features."""

from ..data.providers.noaa_ibtracs import NOAAIBTracsProvider
from ..data.providers.noaa_storm_events import NOAAStormEventsProvider
from ..data.providers.stub import StubProvider
from ..models.enums import DataType, HazardType
from .base import FeatureScore, HazardResult, HazardScorer
from .scoring import compute_category_score, rating_from_score


class WindHurricaneScorer(HazardScorer):
    """Score wind/hurricane/severe storm risk using 7 features."""

    hazard_type = HazardType.WIND_HURRICANE

    def __init__(self) -> None:
        self._ibtracs = NOAAIBTracsProvider()
        self._storm_events = NOAAStormEventsProvider()
        self._wind_zone_stub = StubProvider("design_wind_zone", "Requires ASCE 7 wind zone map.")

    async def score(
        self,
        lat: float,
        lon: float,
        property_data: dict,
        scenario: str,
        year: int,
    ) -> HazardResult:
        ibtracs_data = await self._ibtracs.fetch(lat, lon)
        storm_data = await self._storm_events.fetch(lat, lon)

        features: list[FeatureScore] = []

        # 1. Historical high wind events
        wind_events = storm_data.get("severe_wind_events_30yr")
        features.append(FeatureScore(
            feature_name="historical_high_wind_events",
            raw_value=wind_events,
            normalized_score=self.normalize(wind_events or 0, 0, 50) if wind_events else 0.0,
            source=self._storm_events.name,
            source_url="https://www.ncei.noaa.gov/stormevents/",
            data_type=DataType.OBSERVED if self._storm_events.is_available() else DataType.MISSING,
            is_available=self._storm_events.is_available(),
            confidence=0.85 if self._storm_events.is_available() else 0.0,
        ))

        # 2. Hurricane/tropical cyclone tracks
        cat3_tracks = ibtracs_data.get("cat3plus_tracks_within_200km_30yr")
        features.append(FeatureScore(
            feature_name="hurricane_cyclone_tracks",
            raw_value=cat3_tracks,
            normalized_score=self.normalize(cat3_tracks or 0, 0, 10) if cat3_tracks else 0.0,
            source=self._ibtracs.name,
            source_url="https://www.ncei.noaa.gov/products/international-best-track-archive",
            data_type=DataType.OBSERVED if self._ibtracs.is_available() else DataType.MISSING,
            is_available=self._ibtracs.is_available(),
            confidence=0.9 if self._ibtracs.is_available() else 0.0,
        ))

        # 3. Design wind zone proxy (stub)
        features.append(FeatureScore(
            feature_name="design_wind_zone",
            raw_value=None,
            normalized_score=0.0,
            source=self._wind_zone_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="Requires ASCE 7 wind hazard map integration.",
        ))

        # 4. Distance to coast (proxy for hurricane exposure)
        dist_coast = property_data.get("distance_to_coast")
        coast_wind_score = max(0.0, 80.0 - self.normalize(dist_coast or 200, 0, 400)) if dist_coast else 20.0
        features.append(FeatureScore(
            feature_name="coastal_hurricane_exposure",
            raw_value=dist_coast,
            normalized_score=coast_wind_score,
            source="user_provided",
            data_type=DataType.USER_PROVIDED if dist_coast is not None else DataType.MISSING,
            is_available=dist_coast is not None,
            confidence=0.75 if dist_coast is not None else 0.0,
        ))

        # 5. Tornado / severe convective storm history
        tornado_events = storm_data.get("tornado_events_30yr")
        features.append(FeatureScore(
            feature_name="tornado_convective_storm_history",
            raw_value=tornado_events,
            normalized_score=self.normalize(tornado_events or 0, 0, 20) if tornado_events else 0.0,
            source=self._storm_events.name,
            source_url="https://www.ncei.noaa.gov/stormevents/",
            data_type=DataType.OBSERVED if self._storm_events.is_available() else DataType.MISSING,
            is_available=self._storm_events.is_available(),
            confidence=0.85 if self._storm_events.is_available() else 0.0,
        ))

        # 6. Maximum historical wind speed
        max_wind_kt = ibtracs_data.get("max_wind_speed_historical_kt")
        wind_speed_score = self.normalize(max_wind_kt or 0, 0, 150) if max_wind_kt else 0.0
        features.append(FeatureScore(
            feature_name="storm_intensity_history",
            raw_value=max_wind_kt,
            normalized_score=wind_speed_score,
            source=self._ibtracs.name,
            data_type=DataType.OBSERVED if self._ibtracs.is_available() else DataType.MISSING,
            is_available=self._ibtracs.is_available(),
            confidence=0.8 if self._ibtracs.is_available() else 0.0,
        ))

        # 7. Building vulnerability proxy
        year_built = property_data.get("year_built") or 1980
        construction = property_data.get("construction_type", "unknown")
        vuln_score = _wind_vulnerability(year_built, construction)
        features.append(FeatureScore(
            feature_name="building_wind_vulnerability",
            raw_value=year_built,
            normalized_score=vuln_score,
            source="user_provided",
            data_type=DataType.USER_PROVIDED if property_data.get("year_built") else DataType.MISSING,
            is_available=property_data.get("year_built") is not None,
            confidence=0.5,
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
                "Conduct wind engineering assessment and review structural resilience."
                if cat_score > 60 else
                "Review wind insurance coverage and building code compliance."
            ),
        )


def _wind_vulnerability(year_built: int, construction_type: str) -> float:
    score = 50.0
    if year_built < 1990:
        score += 20.0
    elif year_built > 2010:
        score -= 20.0
    ctype = construction_type.lower() if construction_type else ""
    if "wood" in ctype:
        score += 25.0
    elif "unreinforced" in ctype or "urm" in ctype:
        score += 30.0
    elif "steel" in ctype or "concrete" in ctype:
        score -= 15.0
    return max(0.0, min(100.0, score))
