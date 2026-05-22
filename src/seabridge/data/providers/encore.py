"""ENCORE Nature Dependencies & Impacts — stub.

ENCORE provides ecosystem service dependency mapping by industry sector.
https://www.encorenature.org/
"""

from typing import Any
from ..base_provider import DataProvider


# Key ecosystem services and their relevance by sector
_SECTOR_DEPENDENCIES: dict[str, list[str]] = {
    "real_estate": ["water_supply", "climate_regulation", "erosion_control"],
    "agriculture": ["pollination", "water_supply", "soil_formation", "pest_control"],
    "manufacturing": ["water_supply", "climate_regulation"],
    "energy": ["water_supply", "climate_regulation"],
    "default": ["water_supply", "climate_regulation"],
}


class ENCOREProvider(DataProvider):
    """Returns nature dependency and impact profile by sector from ENCORE."""

    name = "encore"

    def is_available(self) -> bool:
        return False

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        sector = params.get("sector", "default")
        deps = _SECTOR_DEPENDENCIES.get(sector, _SECTOR_DEPENDENCIES["default"])
        return {
            "ecosystem_service_dependencies": deps,
            "high_dependency_services": deps[:2] if deps else [],
            "source": self.name,
            "source_url": "https://www.encorenature.org/",
            "available": False,
            "note": "Sector-level dependency list from ENCORE. Spatial data requires ENCORE API.",
        }
