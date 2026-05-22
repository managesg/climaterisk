"""IUCN Red List API — stub (API key required).

Register at https://api.iucnredlist.org/ to obtain a token.
"""

from typing import Any
from ..base_provider import DataProvider
from ...config import settings


class IUCNProvider(DataProvider):
    """Returns threatened species richness near the location from IUCN Red List."""

    name = "iucn_redlist"

    def is_available(self) -> bool:
        return bool(settings.IUCN_API_KEY) and settings.ENABLE_LIVE_DATA

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        return {
            "threatened_species_count": None,
            "critically_endangered_count": None,
            "source": self.name,
            "source_url": "https://api.iucnredlist.org/",
            "available": False,
            "note": "Requires IUCN_API_KEY. Register at https://api.iucnredlist.org/",
        }
