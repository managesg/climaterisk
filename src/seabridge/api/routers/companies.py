"""Company CRUD endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...models.company import Company

router = APIRouter()


class CompanyCreate(BaseModel):
    name: str
    sector: str
    industry: str
    geography: str
    revenue: Optional[float] = None
    asset_value: Optional[float] = None
    emissions: Optional[float] = None
    energy_use: Optional[float] = None
    water_use: Optional[float] = None
    reporting_boundary: Optional[str] = None


@router.post("", status_code=201)
async def create_company(body: CompanyCreate) -> dict:
    company = Company(**body.model_dump())
    await company.insert()
    return company.model_dump(mode="json")


@router.get("")
async def list_companies() -> list[dict]:
    companies = await Company.find_all().to_list()
    return [c.model_dump(mode="json") for c in companies]


@router.get("/{company_id}")
async def get_company(company_id: str) -> dict:
    company = await Company.find_one({"company_id": uuid.UUID(company_id)})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company.model_dump(mode="json")


@router.put("/{company_id}")
async def update_company(company_id: str, body: CompanyCreate) -> dict:
    company = await Company.find_one({"company_id": uuid.UUID(company_id)})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(company, field, value)
    await company.save()
    return company.model_dump(mode="json")
