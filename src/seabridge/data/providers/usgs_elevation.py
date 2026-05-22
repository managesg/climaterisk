"""USGS 3DEP Elevation Service — public REST API, no key required."""

import logging
from typing import Any

import httpx

from ..base_provider import DataProvider
from ...config import settings

logger = logging.getLogger(__name__)

_ENDPOINT = "https://epqs.nationalmap.gov/v1/json"


class USGSElevationProvider(DataProvider):
    """Fetches elevation above sea level from USGS 3DEP (metres)."""

    name = "usgs_3dep"
    cache_ttl_seconds = 7 * 86400  # static data — 7 days

    def is_available(self) -> bool:
        return settings.ENABLE_LIVE_DATA

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        cache_key = self._cache_key(lat, lon)
        if cached := self._get_cached(cache_key):
            return cached

        if not self.is_available():
            return {"elevation_m": None, "source": self.name, "available": False}

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    _ENDPOINT,
                    params={"x": lon, "y": lat, "units": "Meters", "includeDate": False},
                )
                resp.raise_for_status()
                data = resp.json()
                elevation = float(data["value"])
                result = {"elevation_m": elevation, "source": self.name, "available": True,
                          "source_url": _ENDPOINT}
        except Exception as exc:
            logger.warning("USGS 3DEP fetch failed: %s", exc)
            result = {"elevation_m": None, "source": self.name, "available": False,
                      "error": str(exc)}

        self._set_cached(cache_key, result)
        return result
