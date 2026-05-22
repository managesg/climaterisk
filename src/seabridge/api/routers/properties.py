"""Property CRUD endpoints."""

import uuid
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...models.property import Property

router = APIRouter()


class PropertyCreate(BaseModel):
    company_id: str
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    building_footprint: Optional[dict[str, Any]] = None
    asset_type: str
    floor_area: Optional[float] = None
    year_built: Optional[int] = None
    occupancy: Optional[str] = None
    construction_type: Optional[str] = None
    number_of_storeys: Optional[int] = None
    elevation: Optional[float] = None
    distance_to_coast: Optional[float] = None
    distance_to_river: Optional[float] = None
    land_cover: Optional[str] = None
    impervious_surface: Optional[float] = None
    vegetation_canopy: Optional[float] = None
    slope_degrees: Optional[float] = None
    energy_intensity: Optional[float] = None
    water_intensity: Optional[float] = None
    replacement_value: Optional[float] = None
    business_interruption_value: Optional[float] = None


@router.post("", status_code=201)
async def create_property(body: PropertyCreate) -> dict:
    prop = Property(**{**body.model_dump(), "company_id": uuid.UUID(body.company_id)})
    await prop.insert()
    return prop.model_dump(mode="json")


@router.get("")
async def list_properties(company_id: Optional[str] = None) -> list[dict]:
    query = {}
    if company_id:
        query["company_id"] = uuid.UUID(company_id)
    props = await Property.find(query).to_list()
    return [p.model_dump(mode="json") for p in props]


@router.get("/{property_id}")
async def get_property(property_id: str) -> dict:
    prop = await Property.find_one({"property_id": uuid.UUID(property_id)})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop.model_dump(mode="json")


@router.put("/{property_id}")
async def update_property(property_id: str, body: PropertyCreate) -> dict:
    prop = await Property.find_one({"property_id": uuid.UUID(property_id)})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    update = body.model_dump(exclude_none=True)
    update.pop("company_id", None)
    for field, value in update.items():
        setattr(prop, field, value)
    await prop.save()
    return prop.model_dump(mode="json")
