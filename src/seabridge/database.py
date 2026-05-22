import beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .config import settings
from .models.company import Company
from .models.property import Property
from .models.assessment import RiskAssessment
from .models.agent_run import AgentRun

_client: AsyncIOMotorClient | None = None


async def init_db() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    await beanie.init_beanie(
        database=_client[settings.DATABASE_NAME],
        document_models=[Company, Property, RiskAssessment, AgentRun],
    )


async def close_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
