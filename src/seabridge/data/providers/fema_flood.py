"""FEMA National Flood Hazard Layer — public WFS/REST service."""

import logging
from typing import Any

import httpx

from ..base_provider import DataProvider
from ...config import settings

logger = logging.getLogger(__name__)

_ENDPOINT = "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"

# FEMA flood zone severity mapping (0-100 for normalization)
_ZONE_SEVERITY: dict[str, float] = {
    "AE": 100, "AO": 90, "AH": 85, "A": 80, "A99": 75,
    "VE": 100, "V": 95,
    "X500": 40,  # 0.2% annual chance (500-yr)
    "X": 10,
    "D": 50,     # undetermined
    "OPEN WATER": 0,
}


class FEMAFloodProvider(DataProvider):
    """Returns FEMA flood zone designation and normalised severity score."""

    name = "fema_nfhl"
    cache_ttl_seconds = 30 * 86400  # flood maps change infrequently

    def is_available(self) -> bool:
        return settings.ENABLE_LIVE_DATA

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        cache_key = self._cache_key(lat, lon)
        if cached := self._get_cached(cache_key):
            return cached

        if not self.is_available():
            return {"flood_zone": None, "zone_severity": None,
                    "source": self.name, "available": False}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    _ENDPOINT,
                    params={
                        "geometry": f"{lon},{lat}",
                        "geometryType": "esriGeometryPoint",
                        "inSR": "4326",
                        "spatialRel": "esriSpatialRelIntersects",
                        "outFields": "FLD_ZONE,ZONE_SUBTY",
                        "returnGeometry": False,
                        "f": "json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                features = data.get("features", [])
                if features:
                    attrs = features[0]["attributes"]
                    zone = attrs.get("FLD_ZONE", "X")
                    severity = _ZONE_SEVERITY.get(zone, 10)
                    result = {
                        "flood_zone": zone,
                        "zone_severity": severity,
                        "source": self.name,
                        "source_url": _ENDPOINT,
                        "available": True,
                    }
                else:
                    result = {"flood_zone": "X", "zone_severity": 10,
                              "source": self.name, "available": True,
                              "note": "No FEMA feature at this location — assumed Zone X"}
        except Exception as exc:
            logger.warning("FEMA flood fetch failed: %s", exc)
            result = {"flood_zone": None, "zone_severity": None,
                      "source": self.name, "available": False, "error": str(exc)}

        self._set_cached(cache_key, result)
        return result
