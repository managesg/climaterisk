"""Property CRUD endpoints."""
import logging
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from app.models.property import Property, PropertyCreate
from app.data.store import save_property, get_property, list_properties

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=Property, status_code=status.HTTP_201_CREATED)
async def create_property(payload: PropertyCreate):
    prop = Property(**payload.model_dump())
    await save_property(prop.model_dump())
    return prop


@router.get("/", response_model=list[Property])
async def get_properties(company_id: Optional[str] = Query(default=None)):
    items = await list_properties(company_id=company_id)
    return [Property(**i) for i in items]


@router.get("/{property_id}", response_model=Property)
async def get_property_by_id(property_id: str):
    item = await get_property(property_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
    return Property(**item)
