"""NOAA IBTrACS / HURDAT2 — tropical cyclone tracks (stub).

Full integration requires downloading IBTrACS CSV/NetCDF from
https://www.ncei.noaa.gov/products/international-best-track-archive
and spatially querying storm track proximity.
"""

from typing import Any
from ..base_provider import DataProvider


class NOAAIBTracsProvider(DataProvider):
    """Returns cyclone track proximity from IBTrACS. Stub for MVP."""

    name = "noaa_ibtracs"

    def is_available(self) -> bool:
        return False

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        return {
            "cat3plus_tracks_within_200km_30yr": None,
            "max_wind_speed_historical_kt": None,
            "distance_to_nearest_track_km": None,
            "source": self.name,
            "source_url": "https://www.ncei.noaa.gov/products/international-best-track-archive",
            "available": False,
            "note": "Requires IBTrACS bulk download and spatial indexing.",
        }
