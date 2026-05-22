from typing import Optional, Any
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field


class Property(Document):
    property_id: UUID = Field(default_factory=uuid4)
    company_id: UUID

    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None

    # Building footprint as GeoJSON polygon dict (optional)
    building_footprint: Optional[dict[str, Any]] = None

    asset_type: str  # e.g. "residential", "office", "industrial", "retail"
    floor_area: Optional[float] = None        # m2
    year_built: Optional[int] = None
    occupancy: Optional[str] = None           # e.g. "RES1", "COM1" (HAZUS codes)
    construction_type: Optional[str] = None   # e.g. "wood_frame", "masonry", "concrete"
    number_of_storeys: Optional[int] = None

    # Site characteristics — populated by data-enrichment step or user
    elevation: Optional[float] = None              # metres above sea level
    distance_to_coast: Optional[float] = None      # km
    distance_to_river: Optional[float] = None      # km
    land_cover: Optional[str] = None               # NLCD class
    impervious_surface: Optional[float] = None     # fraction 0-1
    vegetation_canopy: Optional[float] = None      # tree canopy fraction 0-1
    slope_degrees: Optional[float] = None

    # Operational intensity (user-provided or from disclosures)
    energy_intensity: Optional[float] = None       # kWh/m2/yr
    water_intensity: Optional[float] = None        # m3/m2/yr

    # Financial context (user-provided)
    replacement_value: Optional[float] = None          # USD
    business_interruption_value: Optional[float] = None  # USD/day

    class Settings:
        name = "properties"
