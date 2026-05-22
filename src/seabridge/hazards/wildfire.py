"""Wildfire hazard scorer — 8 features."""

from ..data.providers.nasa_firms import NASAFirmsProvider
from ..data.providers.nlcd import NLCDProvider
from ..data.providers.usgs_elevation import USGSElevationProvider
from ..data.providers.nasa_nexgddp import NASANexGDDPProvider
from ..data.providers.drought_monitor import DroughtMonitorProvider
from ..data.providers.stub import StubProvider
from ..models.enums import DataType, HazardType
from .base import FeatureScore, HazardResult, HazardScorer
from .scoring import compute_category_score, rating_from_score


class WildfireScorer(HazardScorer):
    """Score wildfire risk using 8 observable/modeled features."""

    hazard_type = HazardType.WILDFIRE

    def __init__(self) -> None:
        self._firms = NASAFirmsProvider()
        self._nlcd = NLCDProvider()
        self._elevation = USGSElevationProvider()
        self._climate = NASANexGDDPProvider()
        self._drought = DroughtMonitorProvider()
        self._smoke_stub = StubProvider("smoke_aq", "No open smoke/AQ spatial API configured.")
        self._defensible_stub = StubProvider("defensible_space", "Requires parcel-level imagery.")

    async def score(
        self,
        lat: float,
        lon: float,
        property_data: dict,
        scenario: str,
        year: int,
    ) -> HazardResult:
        firms_data = await self._firms.fetch(lat, lon)
        nlcd_data = await self._nlcd.fetch(lat, lon)
        elev_data = await self._elevation.fetch(lat, lon)
        climate_data = await self._climate.fetch(lat, lon, scenario=scenario, year=year)
        drought_data = await self._drought.fetch(lat, lon)

        features: list[FeatureScore] = []

        # 1. Active fire proximity (annual fire detections within 50 km)
        fire_count = firms_data.get("fire_count_annual")
        features.append(FeatureScore(
            feature_name="active_fire_proximity",
            raw_value=fire_count,
            normalized_score=self.normalize(fire_count or 0, 0, 200) if fire_count is not None else 0.0,
            source=self._firms.name,
            source_url="https://firms.modaps.eosdis.nasa.gov/",
            data_type=DataType.OBSERVED if self._firms.is_available() else DataType.MISSING,
            is_available=self._firms.is_available(),
            confidence=0.85 if self._firms.is_available() else 0.0,
            note=firms_data.get("note"),
        ))

        # 2. Fuel / vegetation (impervious surface inverted — more vegetation = more fuel)
        imperv = nlcd_data.get("impervious_fraction") or property_data.get("impervious_surface")
        canopy = nlcd_data.get("tree_canopy_fraction") or property_data.get("vegetation_canopy")
        fuel_proxy = (1.0 - (imperv or 0.3)) * 100  # lower impervious → more vegetation/fuel
        features.append(FeatureScore(
            feature_name="fuel_vegetation",
            raw_value=canopy,
            normalized_score=min(100.0, fuel_proxy),
            source="nlcd" if nlcd_data.get("available") else "user_provided",
            source_url="https://www.usgs.gov/annualNLCD",
            data_type=DataType.OBSERVED if nlcd_data.get("available") else (
                DataType.USER_PROVIDED if imperv is not None else DataType.MISSING),
            is_available=nlcd_data.get("available", False) or imperv is not None,
            confidence=0.7 if nlcd_data.get("available") else 0.4,
        ))

        # 3. Drought contribution (current drought class severity)
        drought_sev = drought_data.get("drought_severity") or 0.0
        features.append(FeatureScore(
            feature_name="drought_contribution",
            raw_value=drought_data.get("drought_class"),
            normalized_score=float(drought_sev),
            source=self._drought.name,
            source_url="https://www.drought.gov/data-maps-tools/us-drought-monitor",
            data_type=DataType.OBSERVED if self._drought.is_available() else DataType.MISSING,
            is_available=self._drought.is_available(),
            confidence=0.9 if self._drought.is_available() else 0.0,
        ))

        # 4. Heat contribution (projected extreme heat days above 35°C)
        heat_days = climate_data.get("extreme_heat_days_above_35c") or 0.0
        features.append(FeatureScore(
            feature_name="heat_contribution",
            raw_value=heat_days,
            normalized_score=self.normalize(heat_days, 0, 90),
            source=self._climate.name,
            source_url="https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/",
            data_type=DataType.SCENARIO,
            is_available=True,
            confidence=0.6,
            note=f"Scenario: {scenario}, Year: {year}",
        ))

        # 5. Slope / elevation (higher slope = higher fire spread rate)
        elev_m = elev_data.get("elevation_m") or property_data.get("elevation")
        slope = property_data.get("slope_degrees")
        slope_score = self.normalize(slope or 5, 0, 45) if slope is not None else 30.0
        features.append(FeatureScore(
            feature_name="slope_elevation",
            raw_value=slope,
            normalized_score=slope_score,
            source="usgs_3dep" if self._elevation.is_available() else "user_provided",
            source_url="https://www.usgs.gov/3d-elevation-program",
            data_type=DataType.OBSERVED if self._elevation.is_available() else (
                DataType.USER_PROVIDED if slope is not None else DataType.MISSING),
            is_available=self._elevation.is_available() or slope is not None,
            confidence=0.7 if self._elevation.is_available() else 0.3,
            note=f"Elevation: {elev_m} m" if elev_m else None,
        ))

        # 6. Smoke / air quality exposure (stub)
        features.append(FeatureScore(
            feature_name="smoke_air_quality",
            raw_value=None,
            normalized_score=0.0,
            source=self._smoke_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="No open smoke/AQ spatial API configured. Consider EPA AQS or PurpleAir.",
        ))

        # 7. Defensible space proxy (stub)
        features.append(FeatureScore(
            feature_name="defensible_space",
            raw_value=None,
            normalized_score=0.0,
            source=self._defensible_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="Requires parcel-level canopy/clearance data.",
        ))

        # 8. Building vulnerability proxy (construction type / year)
        year_built = property_data.get("year_built") or 1980
        construction = property_data.get("construction_type", "unknown")
        vuln_score = _building_fire_vulnerability(year_built, construction)
        features.append(FeatureScore(
            feature_name="building_vulnerability",
            raw_value=year_built,
            normalized_score=vuln_score,
            source="user_provided",
            data_type=DataType.USER_PROVIDED if year_built != 1980 else DataType.MISSING,
            is_available=property_data.get("year_built") is not None,
            confidence=0.5,
            note=f"Construction: {construction}, Year built: {year_built}",
        ))

        scores = [f.normalized_score for f in features]
        cat_score = compute_category_score(scores)
        available_features = [f for f in features if f.is_available]
        confidence = (
            sum(f.confidence for f in available_features) / len(available_features)
            if available_features else 0.0
        )
        top_drivers = sorted(features, key=lambda f: f.normalized_score, reverse=True)
        data_gaps = [f.feature_name for f in features if not f.is_available]

        return HazardResult(
            hazard_type=self.hazard_type,
            feature_scores=features,
            category_score=cat_score,
            rating=rating_from_score(cat_score),
            confidence=confidence,
            top_drivers=[f.feature_name for f in top_drivers[:3]],
            data_gaps=data_gaps,
            recommended_action=(
                "Commission site-level fire risk assessment and verify defensible space."
                if cat_score > 60 else
                "Monitor annual fire data and review vegetation management."
            ),
        )


def _building_fire_vulnerability(year_built: int, construction_type: str) -> float:
    """Proxy vulnerability score based on building age and construction."""
    base = 50.0
    if year_built < 1970:
        base += 25.0
    elif year_built < 1990:
        base += 10.0
    elif year_built > 2010:
        base -= 15.0

    ctype = construction_type.lower() if construction_type else ""
    if "wood" in ctype:
        base += 20.0
    elif "masonry" in ctype:
        base -= 10.0
    elif "concrete" in ctype or "steel" in ctype:
        base -= 15.0

    return max(0.0, min(100.0, base))
