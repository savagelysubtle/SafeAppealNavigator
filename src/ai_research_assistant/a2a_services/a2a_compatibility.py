# src/ai_research_assistant/a2a_services/a2a_compatibility.py
"""
A2A Protocol Compatibility Layer

This module provides compatibility between different versions of the A2A protocol,
handling the transition from 'tasks/send' to 'message/send' methods and ensuring
proper response format handling.
"""

import logging
import uuid
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class A2AProtocolHandler:
    """
    Handler for A2A protocol communication with version compatibility.

    This class automatically detects and adapts to different A2A protocol versions,
    handling both the older 'tasks/send' and newer 'message/send' methods.
    """

    def __init__(self, base_url: str, timeout: float = 300.0):
        """
        Initialize the A2A protocol handler.

        Args:
            base_url: Base URL of the A2A agent
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self._protocol_version = None  # Auto-detected

    async def send_message(
        self, prompt: str, agent_name: str = "agent", context_id: Optional[str] = None
    ) -> str:
        """
        Send a message to the A2A agent with automatic protocol detection.

        Args:
            prompt: The message to send
            agent_name: Name of the target agent (for logging)
            context_id: Optional context ID for conversation continuity

        Returns:
            Agent response as string
        """
        logger.info(f"Sending message to {agent_name}: {prompt[:100]}...")

        # --- FIX: Only use old protocol for FastA2A servers ---
        # FastA2A only supports tasks/* methods, so don't fall back to message/send
        try:
            return await self._send_with_old_protocol(prompt, context_id)
        except Exception as e:
            logger.error(f"FastA2A protocol failed: {e}")
            # Don't fall back to message/send - FastA2A doesn't support it
            raise e

    async def _send_with_new_protocol(
        self, prompt: str, context_id: Optional[str] = None
    ) -> str:
        """Send message using the newer A2A protocol (message/send)."""
        message_id = str(uuid.uuid4())

        a2a_message = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [
                        {"type": "text", "text": prompt}
                    ],  # --- FIX: Changed 'kind' to 'type' ---
                    "messageId": message_id,
                }
            },
            "id": str(uuid.uuid4()),
        }

        # Add context ID if provided
        if context_id:
            a2a_message["params"]["contextId"] = context_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.base_url,
                json=a2a_message,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            response_data = response.json()

            # Handle direct response format (newer protocol)
            if "result" in response_data:
                result = response_data["result"]
                if isinstance(result, str):
                    self._protocol_version = "new"
                    return result
                elif isinstance(result, dict):
                    # Check for direct message content
                    if "content" in result:
                        self._protocol_version = "new"
                        return result["content"]
                    # Extract from message parts
                    if "parts" in result:
                        for part in result["parts"]:
                            if (
                                part.get("type") == "text"
                            ):  # --- FIX: Changed 'kind' to 'type' ---
                                self._protocol_version = "new"
                                return part.get("text", "No response")

            elif "error" in response_data:
                error_msg = response_data["error"]
                raise Exception(f"A2A Error: {error_msg}")

            # If we get here, the response format is unexpected
            raise Exception(f"Unexpected response format: {response_data}")

    async def _send_with_old_protocol(
        self, prompt: str, context_id: Optional[str] = None
    ) -> str:
        """Send message using the older A2A protocol (tasks/send)."""
        message_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        a2a_message = {
            "jsonrpc": "2.0",
            "method": "tasks/send",
            "params": {
                "id": task_id,  # --- FIX: Add missing id field to params ---
                "message": {
                    "role": "user",
                    "parts": [
                        {"type": "text", "text": prompt}
                    ],  # --- FIX: Changed 'kind' to 'type' ---
                    "messageId": message_id,
                },
            },
            "id": str(uuid.uuid4()),
        }

        # Add context ID if provided
        if context_id:
            a2a_message["params"]["contextId"] = context_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.base_url,
                json=a2a_message,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            response_data = response.json()

            # --- DEBUG: Log the response to understand the format ---
            logger.info(f"A2A Response format: {type(response_data)}")
            logger.info(
                f"A2A Response keys: {response_data.keys() if isinstance(response_data, dict) else 'Not a dict'}"
            )
            # --- END DEBUG ---

            # Handle task-based response format (older protocol)
            if "result" in response_data:
                result = response_data["result"]
                if isinstance(result, dict) and ("taskId" in result or "id" in result):
                    # Poll for task completion - handle both taskId and id fields
                    task_id = result.get("taskId") or result.get("id")
                    if task_id:  # Ensure task_id is not None
                        return await self._poll_task_result(task_id, client)
                    else:
                        raise Exception("Task ID not found in response")
                else:
                    # Direct result
                    self._protocol_version = "old"
                    return str(result)

            # Handle direct response format (could be the task itself)
            elif "id" in response_data and "status" in response_data:
                # This looks like a task creation response - poll for completion
                task_id = response_data["id"]
                if task_id:  # Ensure task_id is not None
                    return await self._poll_task_result(task_id, client)
                else:
                    raise Exception("Task ID not found in direct response")

            elif "error" in response_data:
                error_msg = response_data["error"]
                raise Exception(f"A2A Error: {error_msg}")

            # If we get here, the response format is unexpected
            raise Exception(f"Unexpected response format: {response_data}")

    async def _poll_task_result(self, task_id: str, client: httpx.AsyncClient) -> str:
        """Poll for task completion and extract result."""
        import asyncio

        # Poll multiple times with increasing delays
        max_attempts = 10
        for attempt in range(max_attempts):
            # Wait before polling (exponential backoff)
            wait_time = min(2 * (attempt + 1), 10)  # Max 10 seconds
            await asyncio.sleep(wait_time)

            # Get task result - try both taskId and id parameters
            task_result_message = {
                "jsonrpc": "2.0",
                "method": "tasks/get",
                "params": {"id": task_id},  # --- FIX: Use 'id' instead of 'taskId' ---
                "id": str(uuid.uuid4()),
            }

            try:
                result_response = await client.post(
                    self.base_url,
                    json=task_result_message,
                    headers={"Content-Type": "application/json"},
                )
                result_response.raise_for_status()
                result_data = result_response.json()

                if "result" in result_data:
                    task = result_data["result"]

                    # Check if task is completed
                    if isinstance(task, dict):
                        status = task.get("status", {})
                        if status.get("state") in ["completed", "finished", "done"]:
                            # Extract the actual response from artifacts (FastA2A format)
                            if "artifacts" in task:
                                artifacts = task.get("artifacts", [])
                                for artifact in artifacts:
                                    if artifact.get("name") == "result":
                                        parts = artifact.get("parts", [])
                                        for part in parts:
                                            if part.get("type") == "text":
                                                response_text = part.get("text", "")
                                                self._protocol_version = "old"
                                                return response_text.strip()

                            # Fallback: try messages format (older A2A versions)
                            if "messages" in task:
                                messages = task.get("messages", [])
                                for msg in messages:
                                    if msg.get("role") == "assistant":
                                        parts = msg.get("parts", [])
                                        for part in parts:
                                            if part.get("type") == "text":
                                                self._protocol_version = "old"
                                                return part.get("text", "No response")
                        elif status.get("state") in ["failed", "error"]:
                            raise Exception(f"Task failed: {status}")
                        # else: task still running, continue polling

                    # If we get here, task might be complete but in different format
                    if attempt == max_attempts - 1:  # Last attempt
                        self._protocol_version = "old"
                        return str(task)
            except Exception as e:
                if attempt == max_attempts - 1:  # Last attempt
                    raise e
                continue

        raise Exception(
            f"Task {task_id} did not complete after {max_attempts} attempts"
        )


# Convenience functions for easier usage
async def send_a2a_message(
    url: str,
    prompt: str,
    agent_name: str = "agent",
    timeout: float = 300.0,
    context_id: Optional[str] = None,
) -> str:
    """
    Convenience function to send a message to an A2A agent.

    Args:
        url: Agent URL
        prompt: Message to send
        agent_name: Agent name for logging
        timeout: Request timeout
        context_id: Optional context ID

    Returns:
        Agent response
    """
    handler = A2AProtocolHandler(url, timeout)
    return await handler.send_message(prompt, agent_name, context_id)


def create_a2a_handler(url: str, timeout: float = 300.0) -> A2AProtocolHandler:
    """
    Create an A2A protocol handler for reuse.

    Args:
        url: Agent URL
        timeout: Request timeout

    Returns:
        Configured A2A handler
    """
    return A2AProtocolHandler(url, timeout)
