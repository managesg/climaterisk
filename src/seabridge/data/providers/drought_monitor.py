"""US Drought Monitor — public JSON API."""

import logging
from datetime import date
from typing import Any

import httpx

from ..base_provider import DataProvider
from ...config import settings

logger = logging.getLogger(__name__)

_ENDPOINT = "https://usdmdataservices.unl.edu/api/CountyStatistics/GetDroughtSeverityStatisticsByAreaPercent"

# Drought class to severity (0-100)
_CLASS_SEVERITY = {"D0": 20, "D1": 40, "D2": 60, "D3": 80, "D4": 100}


class DroughtMonitorProvider(DataProvider):
    """Returns current drought class and area-percent from US Drought Monitor."""

    name = "us_drought_monitor"
    cache_ttl_seconds = 7 * 86400  # weekly updates

    def is_available(self) -> bool:
        return settings.ENABLE_LIVE_DATA

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        cache_key = self._cache_key(lat, lon)
        if cached := self._get_cached(cache_key):
            return cached

        if not self.is_available():
            return {"drought_class": None, "drought_severity": None,
                    "source": self.name, "available": False}

        today = date.today().strftime("%Y-%m-%d")
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    _ENDPOINT,
                    params={"aoi": "county", "startdate": today, "enddate": today, "statisticsType": "1"},
                )
                resp.raise_for_status()
                records = resp.json()
                # Find record nearest to lat/lon (API returns county-level data)
                # For MVP, return the most severe current class from recent national data
                severity, cls = _extract_severity(records)
                result = {
                    "drought_class": cls,
                    "drought_severity": severity,
                    "source": self.name,
                    "source_url": "https://www.drought.gov/data-maps-tools/us-drought-monitor",
                    "available": True,
                }
        except Exception as exc:
            logger.warning("Drought Monitor fetch failed: %s", exc)
            result = {"drought_class": None, "drought_severity": None,
                      "source": self.name, "available": False, "error": str(exc)}

        self._set_cached(cache_key, result)
        return result


def _extract_severity(records: list[dict]) -> tuple[float, str]:
    """Extract the most severe drought class and a representative score."""
    for cls, sev in sorted(_CLASS_SEVERITY.items(), key=lambda x: -x[1]):
        key = cls.lower()
        for r in records:
            val = r.get(key, 0)
            if isinstance(val, (int, float)) and val > 0:
                return float(sev), cls
    return 0.0, "None"
