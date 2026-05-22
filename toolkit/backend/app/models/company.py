"""Company and portfolio data model."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class CompanyEmissions(BaseModel):
    scope_1_tco2e: Optional[float] = None
    scope_2_tco2e: Optional[float] = None
    scope_3_tco2e: Optional[float] = None
    base_year: Optional[int] = None
    reporting_standard: Optional[str] = None
    data_source: str = "user_provided"


class CompanyCreate(BaseModel):
    name: str
    sector: str
    industry: str
    geography: str
    revenue_usd: Optional[float] = None
    asset_value_usd: Optional[float] = None
    emissions: Optional[CompanyEmissions] = None
    energy_use_mwh: Optional[float] = None
    water_use_m3: Optional[float] = None
    reporting_boundary: str = "operational_control"
    disclosed_net_zero_target: Optional[str] = None
    disclosed_science_based_target: Optional[bool] = None
    notes: Optional[str] = None


class Company(CompanyCreate):
    company_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"json_schema_extra": {
        "example": {
            "name": "Example Property Holdings Ltd",
            "sector": "Real Estate",
            "industry": "Commercial Real Estate",
            "geography": "United States",
            "reporting_boundary": "operational_control"
        }
    }}
