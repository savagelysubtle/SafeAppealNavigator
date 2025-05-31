from fastapi import FastAPI
from ..config.global_settings import settings
from .router import router as ag_ui_router
import logging

logging.basicConfig(level=settings.LOG_LEVEL.upper(), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SavagelySubtle AI Research Agent - AG-UI Backend",
    version="1.0.0",
    description="Acts as a bridge between the Gradio Web UI (using AG-UI protocol) and the ChiefLegalOrchestrator's A2A service."
)

app.include_router(ag_ui_router, prefix="/ag_ui")

@app.get("/")
async def root():
    return {"message": "AG-UI Backend is running. Connect via WebSocket at /ag_ui/ws/{thread_id}"}

@app.on_event("startup")
async def startup_event():
    logger.info("AG-UI Backend starting up...")
    logger.info(f"ChiefLegalOrchestrator A2A URL: {settings.CHIEF_LEGAL_ORCHESTRATOR_A2A_URL}")
    logger.info("AG-UI Backend ready.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("AG-UI Backend shutting down...")

# --- End of src/savagelysubtle_airesearchagent/ag_ui_backend/main.py ---