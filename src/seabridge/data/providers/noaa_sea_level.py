"""NOAA Tides & Currents — sea level trends (public API)."""

import logging
import math
from typing import Any

import httpx

from ..base_provider import DataProvider
from ...config import settings

logger = logging.getLogger(__name__)

_STATIONS_URL = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json"
_TRENDS_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"


class NOAASeaLevelProvider(DataProvider):
    """Returns relative sea level trend (mm/yr) from nearest NOAA tide gauge."""

    name = "noaa_slr"
    cache_ttl_seconds = 30 * 86400

    def is_available(self) -> bool:
        return settings.ENABLE_LIVE_DATA

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        cache_key = self._cache_key(lat, lon)
        if cached := self._get_cached(cache_key):
            return cached

        if not self.is_available():
            return {"slr_mm_per_yr": None, "nearest_gauge": None,
                    "distance_km": None, "source": self.name, "available": False}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Get station list (filter to tide gauge type)
                resp = await client.get(_STATIONS_URL, params={"type": "tidegauge"})
                resp.raise_for_status()
                stations = resp.json().get("stations", [])

                # Find nearest station by Haversine distance
                nearest = _nearest_station(lat, lon, stations)
                if nearest is None:
                    raise ValueError("No tide gauge stations found")

                slr_trend = nearest.get("slr", None)
                result = {
                    "slr_mm_per_yr": float(slr_trend) if slr_trend else None,
                    "nearest_gauge": nearest.get("name"),
                    "station_id": nearest.get("id"),
                    "distance_km": nearest.get("_dist_km"),
                    "source": self.name,
                    "source_url": "https://www.tidesandcurrents.noaa.gov/sltrends/",
                    "available": True,
                }
        except Exception as exc:
            logger.warning("NOAA SLR fetch failed: %s", exc)
            result = {"slr_mm_per_yr": None, "nearest_gauge": None,
                      "source": self.name, "available": False, "error": str(exc)}

        self._set_cached(cache_key, result)
        return result


def _nearest_station(lat: float, lon: float, stations: list[dict]) -> dict | None:
    best = None
    best_dist = float("inf")
    for s in stations:
        try:
            slat, slon = float(s["lat"]), float(s["lng"])
            d = _haversine(lat, lon, slat, slon)
            if d < best_dist:
                best_dist = d
                best = dict(s)
                best["_dist_km"] = round(d, 1)
        except Exception:
            continue
    return best


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
