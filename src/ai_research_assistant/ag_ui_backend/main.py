import logging

from fastapi import FastAPI

from ..config.global_settings import settings
from ..mcp_intergration.http_api import mcp_router
from .router import router as ag_ui_router

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SavagelySubtle AI Research Agent - Backend",
    version="1.0.0",
    description="Backend services: AG-UI conversation API and MCP HTTP API.",
)

# Mount AG-UI only under /ag_ui
app.include_router(ag_ui_router, prefix="/ag_ui")

# Mount MCP HTTP API at root so existing /api/* paths remain valid
app.include_router(mcp_router)


@app.get("/")
async def root():
    return {"message": "Backend running. AG-UI WS at /ag_ui/ws/{thread_id}"}


@app.on_event("startup")
async def startup_event():
    logger.info("Backend starting up...")
    logger.info(
        f"ChiefLegalOrchestrator A2A URL: {settings.CHIEF_LEGAL_ORCHESTRATOR_A2A_URL}"
    )
    logger.info("Backend ready.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Backend shutting down...")
