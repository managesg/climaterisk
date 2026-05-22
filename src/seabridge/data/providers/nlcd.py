"""USGS National Land Cover Database (NLCD) — stub provider.

Full integration requires the MRLC web service or NLCD Zarr/GeoTIFF download.
https://www.usgs.gov/annualNLCD
"""

from typing import Any
from ..base_provider import DataProvider


_IMPERVIOUS_BY_COVER: dict[str, float] = {
    "developed_high": 0.85,
    "developed_medium": 0.65,
    "developed_low": 0.35,
    "developed_open": 0.10,
    "forest": 0.02,
    "shrub": 0.03,
    "grassland": 0.02,
    "cropland": 0.05,
    "wetland": 0.01,
    "water": 0.0,
    "barren": 0.10,
}


class NLCDProvider(DataProvider):
    """Returns land cover class, impervious surface fraction, and tree canopy.

    Stub: returns None for all spatial fields.
    """

    name = "nlcd"

    def is_available(self) -> bool:
        return False

    async def fetch(self, lat: float, lon: float, **params: Any) -> dict:
        return {
            "land_cover_class": None,
            "impervious_fraction": None,
            "tree_canopy_fraction": None,
            "source": self.name,
            "source_url": "https://www.usgs.gov/annualNLCD",
            "available": False,
            "note": "Requires NLCD raster download or MRLC web service integration.",
        }
