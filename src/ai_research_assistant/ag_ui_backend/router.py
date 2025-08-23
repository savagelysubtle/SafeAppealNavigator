# src/savagelysubtle_airesearchagent/ag_ui_backend/router.py
import json
import logging
import uuid
from typing import Dict, Optional

# Use the official AG-UI Python SDK
from ag_ui.core import (
	EventType,
	RunAgentInput,
	RunErrorEvent,
	RunFinishedEvent,
	RunStartedEvent,
)
from ag_ui.core import Message as AGUIMessage
from ag_ui.core import ToolMessage as AGUIToolMessage  # Renamed
from ag_ui.core import UserMessage as AGUIUserMessage  # Renamed to avoid conflict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# Import LLM provider for API key testing
from ..core.llm_provider import get_llm_model
from .a2a_client import A2AClient
from .state_manager import AGUIConversationState, global_state_manager

logger = logging.getLogger(__name__)
router = APIRouter()
a2a_client = A2AClient()

active_connections: Dict[str, WebSocket] = {}  # thread_id -> WebSocket


@router.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
	await websocket.accept()
	active_connections[thread_id] = websocket
	logger.info(f"WebSocket connection established for thread_id: {thread_id}")

	conversation_state: AGUIConversationState = (
		global_state_manager.get_or_create_conversation(thread_id)
	)
	await conversation_state.send_state_snapshot(websocket)
	await conversation_state.send_messages_snapshot(websocket)

	try:
		while True:
			raw_data = await websocket.receive_text()
			logger.debug(
				f"Thread {thread_id}: Received raw data: {raw_data[:500]}"
			)  # Log more for debugging

			run_id_for_operation = str(uuid.uuid4())  # Generate a default run_id

			try:
				data = json.loads(raw_data)

				# Heuristic: if 'thread_id' and 'messages' are present, treat as RunAgentInput
				if (
					"thread_id" in data and "messages" in data and "run_id" in data
				):  # Check for RunAgentInput fields
					run_input = RunAgentInput.model_validate(data)
					run_id_for_operation = run_input.run_id or run_id_for_operation

					# Add new user message from input to conversation state
					user_message_to_process: Optional[AGUIMessage] = None
					if run_input.messages:
						latest_message_from_ui = run_input.messages[-1]
						if latest_message_from_ui.role == "user":
							user_message_to_process = latest_message_from_ui
							conversation_state.add_message(user_message_to_process)

					user_prompt_content = (
						user_message_to_process.content
						if user_message_to_process and user_message_to_process.content
						else ""
					)

					if not user_prompt_content:
						if (
							run_input.forwarded_props
							and "user_prompt" in run_input.forwarded_props
						):
							user_prompt_content = run_input.forwarded_props[
								"user_prompt"
							]
							if not user_message_to_process:
								user_msg_obj = AGUIUserMessage(
									id=str(uuid.uuid4()),
									role="user",
									content=user_prompt_content,
								)
								conversation_state.add_message(user_msg_obj)
						else:
							logger.warning(
								f"Thread {thread_id}: No user prompt found in RunAgentInput."
							)
							error_event = RunErrorEvent(
								type=EventType.RUN_ERROR,
								message="No user prompt provided.",
							)
							await websocket.send_json(
								error_event.model_dump(by_alias=True, exclude_none=True)
							)
							continue

					start_event = RunStartedEvent(
						type=EventType.RUN_STARTED,
						thread_id=thread_id,
						run_id=run_id_for_operation,
					)
					await websocket.send_json(
						start_event.model_dump(by_alias=True, exclude_none=True)
					)

					orchestrator_events_data = await a2a_client.send_to_orchestrator(
						conversation_id=thread_id,
						user_prompt=user_prompt_content,
						message_history=conversation_state.messages[
							:-1
						],  # History before current user message
						tools=run_input.tools,
						current_state=conversation_state.current_state,
					)

					for event_data_dict in orchestrator_events_data:
						await websocket.send_json(event_data_dict)

					finish_event = RunFinishedEvent(
						type=EventType.RUN_FINISHED,
						thread_id=thread_id,
						run_id=run_id_for_operation,
					)
					await websocket.send_json(
						finish_event.model_dump(by_alias=True, exclude_none=True)
					)

			elif ("role" in data and data["role"] == "tool"):
				tool_message = AGUIToolMessage.model_validate(data)
				conversation_state.add_message(tool_message)
				logger.info(
					f"Thread {thread_id}: Received tool result for {tool_message.tool_call_id}"
				)
				await websocket.send_json(
					{"type": "ACK_TOOL_RESULT", "tool_call_id": tool_message.tool_call_id}
				)
			else:
				logger.warning(
					f"Thread {thread_id}: Received unknown message structure: {data}"
				)
				error_event = RunErrorEvent(
						type=EventType.RUN_ERROR,
						message="Unknown message structure",
					)
				await websocket.send_json(
						error_event.model_dump(by_alias=True, exclude_none=True)
				)

			except ValueError as e:
				logger.error(
					f"Thread {thread_id}: Value error processing message: {e}",
					exc_info=True,
				)
				error_event = RunErrorEvent(
						type=EventType.RUN_ERROR,
						message=f"Invalid data format: {str(e)}",
					)
				await websocket.send_json(
						error_event.model_dump(by_alias=True, exclude_none=True)
				)
			except Exception as e:
				logger.error(
					f"Thread {thread_id}: Error processing message: {e}", exc_info=True
				)
				error_event = RunErrorEvent(
						type=EventType.RUN_ERROR,
						message=f"An internal error occurred: {str(e)}",
					)
				await websocket.send_json(
						error_event.model_dump(by_alias=True, exclude_none=True)
				)

	except WebSocketDisconnect:
		logger.info(f"WebSocket connection closed for thread_id: {thread_id}")
	finally:
		if thread_id in active_connections:
			del active_connections[thread_id]


# API Key Testing Endpoint (kept in AG-UI service)
class APIKeyTestRequest(BaseModel):
	provider: str
	apiKey: str
	model: Optional[str] = None


class APIKeyTestResponse(BaseModel):
	success: bool
	message: str
	provider: Optional[str] = None
	model: Optional[str] = None


@router.post("/api/test-api-key", response_model=APIKeyTestResponse)
async def test_api_key(request: APIKeyTestRequest):
	"""Test an API key for a specific LLM provider via backend LLM provider system."""
	try:
		logger.info(f"Testing API key for provider: {request.provider}")
		model_name = request.model or "gemini-1.5-flash"
		llm = get_llm_model(
			provider=request.provider, api_key=request.apiKey, model_name=model_name, temperature=0.0
		)
		try:
			response = await llm.ainvoke("Hello, respond with just 'OK'")
			if response and hasattr(response, "content") and response.content:
				return APIKeyTestResponse(
					success=True,
					message=f"API key is valid and working for {request.provider}",
					provider=request.provider,
					model=model_name,
				)
			else:
				return APIKeyTestResponse(
					success=False,
					message=f"API key test failed - empty response from {request.provider}",
					provider=request.provider,
					model=model_name,
				)
		except Exception as e:
			msg = str(e)
			return APIKeyTestResponse(success=False, message=msg, provider=request.provider, model=model_name)
	except Exception as e:
		return APIKeyTestResponse(success=False, message=str(e), provider=request.provider)


# --- End of src/savagelysubtle_airesearchagent/ag_ui_backend/router.py ---
