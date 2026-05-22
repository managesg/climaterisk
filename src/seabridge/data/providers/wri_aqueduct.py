"""WRI Aqueduct Water Risk Atlas — public REST API."""

import logging
from typing import Any

import httpx

from ..base_provider import DataProvider
from ...config import settings

logger = logging.getLogger(__name__)

_ENDPOINT = "https://aqueduct40.roc.circulate.io/api/v1/aqueduct40"


class WRIAqueductProvider(DataProvider):
    """Returns baseline water stress score (0-5 scale) from WRI Aqueduct 4.0."""

    name = "wri_aqueduct"
    cache_ttl_seconds = 90 * 86400

    def is_available(self) -> bool:
        return settings.ENABLE_LIVE_DATA

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        cache_key = self._cache_key(lat, lon)
        if cached := self._get_cached(cache_key):
            return cached

        if not self.is_available():
            return {"water_stress_score": None, "water_stress_label": None,
                    "source": self.name, "available": False}

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    _ENDPOINT,
                    json={
                        "geogr_input": [{"row_id": 1, "longitude": lon, "latitude": lat}],
                        "month": "annual",
                        "scenario": "optimistic",
                        "year": "2030",
                        "indicators": ["bws_score", "bws_label"],
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                rows = data.get("rows", [])
                if rows:
                    score = rows[0].get("bws_score")
                    label = rows[0].get("bws_label")
                    result = {
                        "water_stress_score": float(score) if score is not None else None,
                        "water_stress_label": label,
                        "source": self.name,
                        "source_url": "https://www.wri.org/aqueduct",
                        "available": True,
                    }
                else:
                    result = {"water_stress_score": None, "water_stress_label": "No data",
                              "source": self.name, "available": False}
        except Exception as exc:
            logger.warning("WRI Aqueduct fetch failed: %s", exc)
            result = {"water_stress_score": None, "water_stress_label": None,
                      "source": self.name, "available": False, "error": str(exc)}

        self._set_cached(cache_key, result)
        return result
