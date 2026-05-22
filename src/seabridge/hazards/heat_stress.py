"""Heat stress hazard scorer — 7 features."""

from ..data.providers.nasa_nexgddp import NASANexGDDPProvider
from ..data.providers.nlcd import NLCDProvider
from ..data.providers.stub import StubProvider
from ..models.enums import DataType, HazardType
from .base import FeatureScore, HazardResult, HazardScorer
from .scoring import compute_category_score, rating_from_score


class HeatStressScorer(HazardScorer):
    """Score heat stress risk using 7 features."""

    hazard_type = HazardType.HEAT_STRESS

    def __init__(self) -> None:
        self._climate = NASANexGDDPProvider()
        self._nlcd = NLCDProvider()
        self._heatwave_stub = StubProvider("historical_heatwaves", "Requires NOAA GHCND station analysis.")
        self._uhi_stub = StubProvider("urban_heat_island", "Requires Landsat LST or NLCD-derived UHI data.")

    async def score(
        self,
        lat: float,
        lon: float,
        property_data: dict,
        scenario: str,
        year: int,
    ) -> HazardResult:
        climate_data = await self._climate.fetch(lat, lon, scenario=scenario, year=year)
        nlcd_data = await self._nlcd.fetch(lat, lon)

        features: list[FeatureScore] = []

        # 1. Projected extreme heat days above 35°C
        heat_days = climate_data.get("extreme_heat_days_above_35c") or 0.0
        features.append(FeatureScore(
            feature_name="projected_extreme_heat_days",
            raw_value=heat_days,
            normalized_score=self.normalize(heat_days, 0, 90),
            source=self._climate.name,
            source_url="https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/",
            data_type=DataType.SCENARIO,
            is_available=True,
            confidence=0.65,
            note=f"Scenario {scenario}, year {year}",
        ))

        # 2. Historical heat waves (stub)
        features.append(FeatureScore(
            feature_name="historical_heatwaves",
            raw_value=None,
            normalized_score=0.0,
            source=self._heatwave_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="Requires NOAA GHCND daily temperature analysis.",
        ))

        # 3. Urban heat island proxy (impervious surface)
        imperv = nlcd_data.get("impervious_fraction") or property_data.get("impervious_surface")
        uhi_score = self.normalize(imperv or 0.3, 0, 1.0) if imperv is not None else 30.0
        features.append(FeatureScore(
            feature_name="urban_heat_island_proxy",
            raw_value=imperv,
            normalized_score=uhi_score,
            source="nlcd" if nlcd_data.get("available") else "user_provided",
            source_url="https://www.usgs.gov/annualNLCD",
            data_type=DataType.OBSERVED if nlcd_data.get("available") else (
                DataType.USER_PROVIDED if imperv is not None else DataType.MISSING),
            is_available=nlcd_data.get("available", False) or imperv is not None,
            confidence=0.7,
        ))

        # 4. Impervious surface (heat retention)
        features.append(FeatureScore(
            feature_name="impervious_surface",
            raw_value=imperv,
            normalized_score=uhi_score,  # same data source
            source="nlcd" if nlcd_data.get("available") else "user_provided",
            data_type=DataType.OBSERVED if nlcd_data.get("available") else DataType.MISSING,
            is_available=nlcd_data.get("available", False) or imperv is not None,
            confidence=0.7,
        ))

        # 5. Tree canopy / vegetation (mitigating factor — inverse)
        canopy = nlcd_data.get("tree_canopy_fraction") or property_data.get("vegetation_canopy")
        canopy_score = max(0.0, 100.0 - self.normalize(canopy or 0.2, 0, 1.0)) if canopy else 50.0
        features.append(FeatureScore(
            feature_name="tree_canopy_vegetation",
            raw_value=canopy,
            normalized_score=canopy_score,
            source="nlcd" if nlcd_data.get("available") else "user_provided",
            data_type=DataType.OBSERVED if nlcd_data.get("available") else DataType.MISSING,
            is_available=nlcd_data.get("available", False) or canopy is not None,
            confidence=0.65,
            note="Higher canopy = lower heat exposure",
        ))

        # 6. Cooling vulnerability (building age/type proxy)
        year_built = property_data.get("year_built") or 1980
        cooling_score = _cooling_vulnerability(year_built, property_data.get("construction_type"))
        features.append(FeatureScore(
            feature_name="cooling_vulnerability",
            raw_value=year_built,
            normalized_score=cooling_score,
            source="user_provided",
            data_type=DataType.USER_PROVIDED if property_data.get("year_built") else DataType.MISSING,
            is_available=property_data.get("year_built") is not None,
            confidence=0.5,
        ))

        # 7. Building age/type heat retention
        features.append(FeatureScore(
            feature_name="building_age_type",
            raw_value=year_built,
            normalized_score=self.normalize(max(0, 2024 - year_built), 0, 100),
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
                "Evaluate HVAC capacity, passive cooling upgrades, and urban greening."
                if cat_score > 60 else
                "Review cooling systems and monitor projected heat trends."
            ),
        )


def _cooling_vulnerability(year_built: int, construction_type: str | None) -> float:
    """Higher score = more vulnerable to heat."""
    score = 50.0
    if year_built < 1980:
        score += 30.0
    elif year_built < 2000:
        score += 10.0
    elif year_built > 2015:
        score -= 15.0
    ctype = (construction_type or "").lower()
    if "concrete" in ctype:
        score += 10.0  # high thermal mass
    elif "light" in ctype or "prefab" in ctype:
        score += 5.0
    return max(0.0, min(100.0, score))
