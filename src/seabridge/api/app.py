"""SeaBridge AI Sustainability Toolkit — FastAPI application."""

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings
from ..database import close_db, init_db
from .routers import agents, assessments, companies, disclosure, properties

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=settings.LOG_LEVEL)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
    )
    await init_db()
    logger.info("SeaBridge toolkit started", mongodb_url=settings.MONGODB_URL)
    yield
    await close_db()
    logger.info("SeaBridge toolkit shut down")


app = FastAPI(
    title="SeaBridge AI Sustainability Toolkit",
    description=(
        "Physical climate risk, transition risk, nature risk, and climate opportunity analysis "
        "aligned with ISSB IFRS S2 / TCFD / TNFD."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(properties.router, prefix="/api/v1/properties", tags=["properties"])
app.include_router(assessments.router, prefix="/api/v1/assessments", tags=["assessments"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(disclosure.router, prefix="/api/v1/disclosures", tags=["disclosures"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
