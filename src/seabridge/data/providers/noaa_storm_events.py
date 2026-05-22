"""NOAA Storm Events Database — stub provider.

Full integration requires downloading annual CSV archives from
https://www.ncei.noaa.gov/stormevents/ and indexing by county/location.
"""

from typing import Any
from ..base_provider import DataProvider


class NOAAStormEventsProvider(DataProvider):
    """Returns historical severe weather event frequency from NOAA Storm Events DB.

    Stub: returns None for all fields. Full integration requires STAC/bulk download.
    """

    name = "noaa_storm_events"

    def is_available(self) -> bool:
        return False

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        return {
            "tornado_events_30yr": None,
            "hail_events_30yr": None,
            "severe_wind_events_30yr": None,
            "flood_events_30yr": None,
            "source": self.name,
            "source_url": "https://www.ncei.noaa.gov/stormevents/",
            "available": False,
            "note": "Full integration requires bulk download of NOAA Storm Events CSV archives.",
        }
