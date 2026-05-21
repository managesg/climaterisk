"""Property / Building data model."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import uuid


class GeoCoordinate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class PropertyCreate(BaseModel):
    company_id: str
    name: str
    address: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    country: Optional[str] = None
    state_province: Optional[str] = None
    city: Optional[str] = None

    # Physical characteristics
    asset_type: str  # e.g. "Office", "Retail", "Industrial", "Residential", "Data Center"
    floor_area_m2: Optional[float] = None
    year_built: Optional[int] = None
    occupancy: Optional[str] = None
    construction_type: Optional[str] = None  # e.g. "Wood Frame", "Masonry", "Steel Frame", "Concrete"
    num_stories: Optional[int] = None

    # Exposure attributes
    elevation_m: Optional[float] = None
    distance_to_coast_km: Optional[float] = None
    distance_to_river_km: Optional[float] = None

    # Land/environment
    land_cover: Optional[str] = None
    impervious_surface_pct: Optional[float] = None
    tree_canopy_pct: Optional[float] = None

    # Energy/water intensity
    energy_intensity_kwh_m2: Optional[float] = None
    water_intensity_m3_m2: Optional[float] = None

    # Financial
    replacement_value_usd: Optional[float] = None
    business_interruption_value_usd: Optional[float] = None

    # User-supplied risk context
    fema_flood_zone: Optional[str] = None
    notes: Optional[str] = None


class Property(PropertyCreate):
    property_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    geocode_source: str = "user_provided"

    model_config = {"json_schema_extra": {
        "example": {
            "company_id": "abc-123",
            "name": "HQ Building",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "country": "USA",
            "city": "San Francisco",
            "asset_type": "Office",
            "floor_area_m2": 5000
        }
    }}
