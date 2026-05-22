"""NASA FIRMS — active fire detections (MODIS/VIIRS).

Public API — MAP_KEY optional for higher rate limits.
"""

import logging
from typing import Any

import httpx

from ..base_provider import DataProvider
from ...config import settings

logger = logging.getLogger(__name__)

# FIRMS area stats endpoint returns CSV; we use the simpler transaction endpoint
_ENDPOINT = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Radius in km for proximity query; large enough to capture regional fire context
_RADIUS_KM = 50
_DAYS = 365  # look-back period for annual fire frequency


class NASAFirmsProvider(DataProvider):
    """Returns active fire count within radius from NASA FIRMS MODIS/VIIRS."""

    name = "nasa_firms"
    cache_ttl_seconds = 24 * 3600  # fires change daily

    def is_available(self) -> bool:
        # Requires MAP_KEY for reliable access; without it still works at low rate
        return settings.ENABLE_LIVE_DATA

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        cache_key = self._cache_key(lat, lon)
        if cached := self._get_cached(cache_key):
            return cached

        if not self.is_available():
            return {"fire_count_annual": None, "source": self.name, "available": False,
                    "note": "NASA FIRMS requires ENABLE_LIVE_DATA=true"}

        map_key = settings.NASA_EARTHDATA_TOKEN or "d26c9edae9ef7d82c5a67792f5c76ca6"
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    f"{_ENDPOINT}/{map_key}/VIIRS_SNPP_NRT/{lon},{lat},{_RADIUS_KM}/{_DAYS}",
                )
                # Response is CSV — count rows (each row = one fire detection)
                if resp.status_code == 200:
                    lines = [l for l in resp.text.strip().split("\n") if l]
                    fire_count = max(0, len(lines) - 1)  # subtract header
                    result = {
                        "fire_count_annual": fire_count,
                        "radius_km": _RADIUS_KM,
                        "days": _DAYS,
                        "source": self.name,
                        "source_url": "https://firms.modaps.eosdis.nasa.gov/",
                        "available": True,
                    }
                else:
                    result = {"fire_count_annual": None, "source": self.name, "available": False,
                              "note": f"HTTP {resp.status_code}"}
        except Exception as exc:
            logger.warning("NASA FIRMS fetch failed: %s", exc)
            result = {"fire_count_annual": None, "source": self.name, "available": False,
                      "error": str(exc)}

        self._set_cached(cache_key, result)
        return result
