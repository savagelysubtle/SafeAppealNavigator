# src/savagelysubtle_airesearchagent/mcp_integration/server_main.py
# Revised to only serve agent discovery functionalities.
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from typing import Dict, Any, List

from .agent_registry import agent_registry_instance
from ..config.global_settings import settings
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SavagelySubtle AI - Agent Registry MCP Server",
    version="1.0.0",
    description="MCP Server for Agent Discovery (via Agent Cards)."
)

# --- Agent Discovery Endpoints ---

class FindAgentInput(BaseModel):
    task_description: str

@app.post(
    "/mcp_tool/find_agent_for_task",
    summary="Finds an agent for a given task description",
    response_model=Optional[Dict[str, Any]] # AgentCard or null
)
async def find_agent_tool_endpoint(payload: FindAgentInput = Body(...)):
    """
    This endpoint simulates an MCP tool provided by this server.
    The ChiefLegalOrchestrator can use this "tool" to find coordinator agents.
    """
    task_description = payload.task_description
    if not task_description:
        raise HTTPException(status_code=400, detail="task_description is required")

    logger.info(f"MCP Server: Received find_agent_for_task request: '{task_description}'")
    agent_card = agent_registry_instance.find_agent_for_task(task_description)

    if not agent_card:
        logger.warning(f"MCP Server: No suitable agent found for task: '{task_description}'")
        # MCP spec might prefer a structured "not found" response rather than HTTP 404 for a tool call
        # For now, returning null/None in the response body if agent_card is None.
        return None
    logger.info(f"MCP Server: Found agent '{agent_card.get('agent_id')}' for task '{task_description}'")
    return agent_card

@app.get(
    "/mcp_tool/list_all_agents",
    summary="Lists all registered agent cards",
    response_model=List[Dict[str, Any]]
)
async def list_all_agents_endpoint() -> List[Dict[str, Any]]:
    """
    This endpoint allows listing all known agent capabilities.
    """
    logger.info("MCP Server: Received list_all_agents request.")
    cards = agent_registry_instance.list_all_agent_cards()
    logger.info(f"MCP Server: Returning {len(cards)} agent cards.")
    return cards

@app.on_event("startup")
async def startup_event():
    logger.info("Agent Registry MCP Server starting up...")
    # Agent registry is loaded at import time of agent_registry_instance
    logger.info(f"Agent Registry loaded with {len(agent_registry_instance.list_all_agent_cards())} agents.")
    logger.info("Agent Registry MCP Server ready to accept requests.")

def main():
    """
    Main entry point to run the Agent Registry MCP Server.
    """
    logging.basicConfig(level=settings.LOG_LEVEL.upper(), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info(f"Starting Agent Registry MCP Server on {settings.MCP_SERVER_HOST}:{settings.MCP_SERVER_PORT}")
    uvicorn.run(
        "savagelysubtle_airesearchagent.mcp_integration.server_main:app", # Path to the app instance
        host=settings.MCP_SERVER_HOST,
        port=settings.MCP_SERVER_PORT,
        reload=True # Useful for development
    )

if __name__ == "__main__":
    main()

# --- End of src/savagelysubtle_airesearchagent/mcp_integration/server_main.py ---