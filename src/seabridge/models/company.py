from typing import Optional
from uuid import UUID, uuid4
from beanie import Document
from pydantic import Field


class Company(Document):
    company_id: UUID = Field(default_factory=uuid4)
    name: str
    sector: str
    industry: str
    geography: str  # primary operating geography (ISO country or region)

    revenue: Optional[float] = None           # USD millions
    asset_value: Optional[float] = None       # USD millions
    emissions: Optional[float] = None         # tCO2e/yr
    energy_use: Optional[float] = None        # MWh/yr
    water_use: Optional[float] = None         # m3/yr
    reporting_boundary: Optional[str] = None  # e.g. "operational control", "equity share"

    class Settings:
        name = "companies"
