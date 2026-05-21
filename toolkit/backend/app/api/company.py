"""Company CRUD endpoints."""
import logging
from fastapi import APIRouter, HTTPException, status
from app.models.company import Company, CompanyCreate
from app.data.store import save_company, get_company, list_companies

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=Company, status_code=status.HTTP_201_CREATED)
async def create_company(payload: CompanyCreate):
    company = Company(**payload.model_dump())
    await save_company(company.model_dump())
    return company


@router.get("/", response_model=list[Company])
async def get_companies():
    items = await list_companies()
    return [Company(**i) for i in items]


@router.get("/{company_id}", response_model=Company)
async def get_company_by_id(company_id: str):
    item = await get_company(company_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    return Company(**item)
