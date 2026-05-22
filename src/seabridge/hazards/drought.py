"""Drought / water stress hazard scorer — 7 features."""

from ..data.providers.drought_monitor import DroughtMonitorProvider
from ..data.providers.wri_aqueduct import WRIAqueductProvider
from ..data.providers.nasa_nexgddp import NASANexGDDPProvider
from ..data.providers.stub import StubProvider
from ..models.enums import DataType, HazardType
from .base import FeatureScore, HazardResult, HazardScorer
from .scoring import compute_category_score, rating_from_score


class DroughtScorer(HazardScorer):
    """Score drought and water stress risk using 7 features."""

    hazard_type = HazardType.DROUGHT

    def __init__(self) -> None:
        self._drought = DroughtMonitorProvider()
        self._aqueduct = WRIAqueductProvider()
        self._climate = NASANexGDDPProvider()
        self._drought_hist_stub = StubProvider("historical_drought", "Requires PDSI or SPI time-series analysis.")
        self._soil_moisture_stub = StubProvider("soil_moisture", "Requires NASA SMAP or ERA5 data.")

    async def score(
        self,
        lat: float,
        lon: float,
        property_data: dict,
        scenario: str,
        year: int,
    ) -> HazardResult:
        drought_data = await self._drought.fetch(lat, lon)
        aqueduct_data = await self._aqueduct.fetch(lat, lon)
        climate_data = await self._climate.fetch(lat, lon, scenario=scenario, year=year)

        features: list[FeatureScore] = []

        # 1. Current drought class
        drought_sev = drought_data.get("drought_severity") or 0.0
        features.append(FeatureScore(
            feature_name="current_drought_class",
            raw_value=drought_data.get("drought_class"),
            normalized_score=float(drought_sev),
            source=self._drought.name,
            source_url="https://www.drought.gov/data-maps-tools/us-drought-monitor",
            data_type=DataType.OBSERVED if self._drought.is_available() else DataType.MISSING,
            is_available=self._drought.is_available(),
            confidence=0.9 if self._drought.is_available() else 0.0,
        ))

        # 2. Historical drought frequency (stub)
        features.append(FeatureScore(
            feature_name="historical_drought_frequency",
            raw_value=None,
            normalized_score=0.0,
            source=self._drought_hist_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="Requires PDSI/SPI historical analysis.",
        ))

        # 3. Projected precipitation change
        precip_change = climate_data.get("precip_change_pct") or 0.0
        # Negative = drier = higher drought risk
        drought_precip_score = self.normalize(-min(precip_change, 0), 0, 20)
        features.append(FeatureScore(
            feature_name="projected_precipitation_change",
            raw_value=precip_change,
            normalized_score=drought_precip_score,
            source=self._climate.name,
            source_url="https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/",
            data_type=DataType.SCENARIO,
            is_available=True,
            confidence=0.6,
            note=f"Projected change: {precip_change}% ({scenario}, {year})",
        ))

        # 4. WRI Aqueduct water stress score (0-5 scale)
        ws_score_raw = aqueduct_data.get("water_stress_score")
        ws_normalised = self.normalize(ws_score_raw or 0, 0, 5) if ws_score_raw is not None else 0.0
        features.append(FeatureScore(
            feature_name="water_stress_basin",
            raw_value=ws_score_raw,
            normalized_score=ws_normalised,
            source=self._aqueduct.name,
            source_url="https://www.wri.org/aqueduct",
            data_type=DataType.MODELED if self._aqueduct.is_available() else DataType.MISSING,
            is_available=self._aqueduct.is_available(),
            confidence=0.85 if self._aqueduct.is_available() else 0.0,
            note=aqueduct_data.get("water_stress_label"),
        ))

        # 5. Soil moisture (stub)
        features.append(FeatureScore(
            feature_name="soil_moisture",
            raw_value=None,
            normalized_score=0.0,
            source=self._soil_moisture_stub.name,
            data_type=DataType.MISSING,
            is_available=False,
            confidence=0.0,
            note="Requires NASA SMAP or ERA5 reanalysis data.",
        ))

        # 6. Water demand intensity (from property)
        water_intensity = property_data.get("water_intensity")
        demand_score = self.normalize(water_intensity or 0, 0, 5.0) if water_intensity else 20.0
        features.append(FeatureScore(
            feature_name="water_demand_intensity",
            raw_value=water_intensity,
            normalized_score=demand_score,
            source="user_provided",
            data_type=DataType.USER_PROVIDED if water_intensity else DataType.MISSING,
            is_available=water_intensity is not None,
            confidence=0.8 if water_intensity else 0.0,
            note=f"{water_intensity} m3/m2/yr" if water_intensity else None,
        ))

        # 7. Cooling/water dependency (asset type proxy)
        asset_type = property_data.get("asset_type", "")
        water_dep_score = _water_dependency_score(asset_type)
        features.append(FeatureScore(
            feature_name="cooling_water_dependency",
            raw_value=asset_type,
            normalized_score=water_dep_score,
            source="user_provided",
            data_type=DataType.USER_PROVIDED,
            is_available=True,
            confidence=0.5,
            note=f"Asset type: {asset_type}",
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
                "Conduct water security assessment and explore efficiency/recycling measures."
                if cat_score > 60 else
                "Monitor WRI Aqueduct scores and review water utility dependency."
            ),
        )


def _water_dependency_score(asset_type: str) -> float:
    at = asset_type.lower()
    if any(k in at for k in ["industrial", "manufacturing", "data_center", "data center"]):
        return 75.0
    if any(k in at for k in ["hotel", "hospital", "hospitality"]):
        return 60.0
    if "office" in at:
        return 35.0
    if "residential" in at:
        return 30.0
    return 40.0
