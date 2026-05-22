"""GBIF Biodiversity Occurrence API — public, no key required."""

import logging
from typing import Any

import httpx

from ..base_provider import DataProvider
from ...config import settings

logger = logging.getLogger(__name__)

_ENDPOINT = "https://api.gbif.org/v1/occurrence/search"
_RADIUS_DEG = 0.5  # ~55 km radius


class GBIFProvider(DataProvider):
    """Returns occurrence count and threatened species count near the location."""

    name = "gbif"
    cache_ttl_seconds = 30 * 86400

    def is_available(self) -> bool:
        return settings.ENABLE_LIVE_DATA

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        cache_key = self._cache_key(lat, lon)
        if cached := self._get_cached(cache_key):
            return cached

        if not self.is_available():
            return {"occurrence_count": None, "source": self.name, "available": False}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    _ENDPOINT,
                    params={
                        "decimalLatitude": f"{lat - _RADIUS_DEG},{lat + _RADIUS_DEG}",
                        "decimalLongitude": f"{lon - _RADIUS_DEG},{lon + _RADIUS_DEG}",
                        "limit": 0,  # we only need count
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                result = {
                    "occurrence_count": data.get("count", 0),
                    "source": self.name,
                    "source_url": "https://www.gbif.org/",
                    "available": True,
                }
        except Exception as exc:
            logger.warning("GBIF fetch failed: %s", exc)
            result = {"occurrence_count": None, "source": self.name,
                      "available": False, "error": str(exc)}

        self._set_cached(cache_key, result)
        return result
