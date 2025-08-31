# FILE: src/ai_research_assistant/a2a_services/a2a_compatibility.py
# Pure A2A Protocol Client - Works with PydanticAI native A2A servers

import logging
import uuid
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


async def send_a2a_message(
    url: str,
    prompt: str,
    agent_name: str = "agent",
    timeout: float = 300.0,
    context_id: Optional[str] = None,
) -> str:
    """
    Send a message to a PydanticAI A2A agent using the standard A2A protocol.

    This client works with any A2A-compliant agent, including those created
    with PydanticAI's native to_a2a() method.

    Args:
        url: The agent's A2A service URL
        prompt: The user's input string
        agent_name: The name of the agent (for logging)
        timeout: Request timeout in seconds
        context_id: Optional context ID for conversation continuity

    Returns:
        The agent's response as a string

    Raises:
        httpx.HTTPStatusError: If the HTTP request fails
        Exception: For other communication errors
    """
    logger.info(f"Sending A2A message to {agent_name} at {url}")

    # Standard A2A JSON-RPC request format
    # This works with PydanticAI native A2A servers and fasta2a servers
    a2a_payload = {
        "jsonrpc": "2.0",
        "method": "tasks/send",
        "params": {
            "id": str(uuid.uuid4()),  # Unique task ID
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": prompt}],
                "messageId": str(uuid.uuid4()),
            },
        },
        "id": str(uuid.uuid4()),  # Request ID
    }

    # Add context for conversation continuity
    if context_id:
        a2a_payload["params"]["contextId"] = context_id

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                url,
                json=a2a_payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            response_data = response.json()

            logger.debug(f"A2A response from {agent_name}: {response_data}")

            # Parse the A2A response according to the protocol
            result = _extract_response_content(response_data, agent_name)
            logger.info(f"✅ Successfully received response from {agent_name}")
            return result

        except httpx.HTTPStatusError as e:
            error_details = e.response.text
            logger.error(
                f"HTTP error from {agent_name}: {e.response.status_code} - {error_details}"
            )
            return f"Error: Received HTTP {e.response.status_code} from {agent_name}. Details: {error_details}"

        except Exception as e:
            logger.error(f"Communication error with {agent_name}: {e}", exc_info=True)
            return f"Error: Could not communicate with {agent_name}. Is the service running on {url}?"


def _extract_response_content(response_data: dict, agent_name: str) -> str:
    """
    Extract text content from A2A response data.

    Handles multiple response formats from different A2A implementations.
    """
    if "result" not in response_data:
        return "Agent returned no recognizable result."

    task = response_data["result"]

    # Handle completed task with artifacts (PydanticAI native format)
    if isinstance(task, dict) and task.get("status", {}).get("state") == "completed":
        artifacts = task.get("artifacts", [])
        for artifact in artifacts:
            if artifact.get("parts"):
                for part in artifact["parts"]:
                    if part.get("type") == "text":
                        return part.get("text", "Agent returned no text content.")

    # Handle direct message response format
    if isinstance(task, dict) and "parts" in task:
        for part in task["parts"]:
            if part.get("type") == "text":
                return part.get("text", "Agent returned no text content.")

    # Handle direct string response
    if isinstance(task, str):
        return task

    # Handle task in progress (polling would be implemented here)
    if isinstance(task, dict):
        task_id = task.get("id") or task.get("taskId")
        state = task.get("status", {}).get("state")
        if task_id and state in ["running", "pending"]:
            return f"Task {task_id} is in progress (status: {state}). Polling not yet implemented."

    # Fallback for unexpected response formats
    logger.warning(f"Unexpected response format from {agent_name}: {type(task)}")
    return f"Received response from {agent_name}, but format was unexpected: {str(task)[:200]}..."
