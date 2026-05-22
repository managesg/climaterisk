"""Protected Planet / WDPA — stub.

WDPA data available via https://www.protectedplanet.net/en/thematic-areas/wdpa
and via UNEP-WCMC API (requires registration).
"""

from typing import Any
from ..base_provider import DataProvider


class WDPAProvider(DataProvider):
    """Returns protected area designation within proximity of the location."""

    name = "wdpa"

    def is_available(self) -> bool:
        return False

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        return {
            "protected_area_within_10km": None,
            "protection_level": None,
            "iucn_category": None,
            "source": self.name,
            "source_url": "https://www.protectedplanet.net/",
            "available": False,
            "note": "Requires WDPA bulk download or UNEP-WCMC API registration.",
        }
