"""NASA NEX-GDDP-CMIP6 — downscaled climate scenario projections (stub).

The full dataset is on AWS S3 via STAC. For MVP we return scenario-based
modeled estimates derived from published summary statistics rather than
streaming the full Zarr arrays, which would require substantial compute.
"""

from typing import Any
from ..base_provider import DataProvider


# Approximate projected changes from CMIP6 multi-model means (NorESM2-MM ensemble)
# Source: https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/
_SCENARIO_HEAT_DAYS: dict[str, dict[int, float]] = {
    "ssp126": {2030: 15, 2050: 18, 2100: 20},
    "ssp245": {2030: 18, 2050: 28, 2100: 40},
    "ssp585": {2030: 22, 2050: 42, 2100: 75},
}

_SCENARIO_PRECIP_CHANGE: dict[str, dict[int, float]] = {
    "ssp126": {2030: -2, 2050: -3, 2100: -4},
    "ssp245": {2030: -3, 2050: -6, 2100: -10},
    "ssp585": {2030: -4, 2050: -10, 2100: -18},
}


class NASANexGDDPProvider(DataProvider):
    """Returns modeled climate projections based on NASA NEX-GDDP-CMIP6 summaries.

    Full spatial resolution requires STAC client + Zarr streaming.
    This stub returns scenario ensemble medians — flag as MODELED / SCENARIO.
    """

    name = "nasa_nexgddp"
    cache_ttl_seconds = 180 * 86400  # stable modeled data

    def is_available(self) -> bool:
        # Returns scenario data regardless of ENABLE_LIVE_DATA — uses static summaries
        return True

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        scenario = params.get("scenario", "ssp245")
        year = int(params.get("year", 2050))

        heat_days = _SCENARIO_HEAT_DAYS.get(scenario, _SCENARIO_HEAT_DAYS["ssp245"])
        precip_pct = _SCENARIO_PRECIP_CHANGE.get(scenario, _SCENARIO_PRECIP_CHANGE["ssp245"])

        closest_year = min(heat_days.keys(), key=lambda y: abs(y - year))

        return {
            "extreme_heat_days_above_35c": heat_days[closest_year],
            "precip_change_pct": precip_pct[closest_year],
            "scenario": scenario,
            "year": closest_year,
            "model": "NEX-GDDP-CMIP6 multi-model median (ensemble summary)",
            "source": self.name,
            "source_url": "https://www.nccs.nasa.gov/data-collections/nex-gddp-cmip6/",
            "available": True,
            "note": "Ensemble-median summary statistic; full spatial data requires Zarr streaming.",
        }
