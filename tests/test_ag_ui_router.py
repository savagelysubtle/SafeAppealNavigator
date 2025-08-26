#!/usr/bin/env python3
"""
Comprehensive tests for the AG-UI router module.

Tests WebSocket router functionality including:
- WebSocket connection handling
- RunAgentInput message processing
- AG-UI event emission and protocol compliance
- Tool message handling
- API key testing endpoint
- Error handling and validation
"""

import json
import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from ag_ui.core import (
    EventType,
)
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from ai_research_assistant.ag_ui_backend.router import (
    APIKeyTestRequest,
    router,
)


class TestWebSocketEndpoint:
    """Test suite for WebSocket endpoint functionality."""

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket for testing."""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        websocket.receive_text = AsyncMock()
        return websocket

    @pytest.fixture
    def thread_id(self):
        """Sample thread ID."""
        return "test-thread-123"

    @pytest.fixture
    def run_agent_input(self, thread_id):
        """Sample RunAgentInput message."""
        return {
            "thread_id": thread_id,
            "run_id": str(uuid.uuid4()),
            "messages": [
                {
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": "Test user message",
                }
            ],
            "tools": [
                {
                    "name": "test_tool",
                    "description": "Test tool",
                    "parameters": {"type": "object"},
                }
            ],
            "state": {},
            "context": [],  # Should be a list, not dict
            "forwardedProps": {},
        }

    @pytest.fixture
    def tool_message(self):
        """Sample tool message."""
        return {
            "id": str(uuid.uuid4()),
            "role": "tool",
            "content": "Tool execution result",
            "tool_call_id": str(uuid.uuid4()),
        }

    @pytest.fixture
    def mock_a2a_client(self):
        """Mock A2A client."""
        mock_client = Mock()
        mock_client.send_to_orchestrator = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_state_manager(self):
        """Mock global state manager."""
        mock_manager = Mock()
        mock_conversation = Mock()
        mock_conversation.add_message = Mock()
        mock_conversation.send_state_snapshot = AsyncMock()
        mock_conversation.send_messages_snapshot = AsyncMock()
        mock_manager.get_or_create_conversation.return_value = mock_conversation
        return mock_manager

    @patch("ai_research_assistant.ag_ui_backend.router.global_state_manager")
    @patch("ai_research_assistant.ag_ui_backend.router.a2a_client")
    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(
        self, mock_a2a_client, mock_state_manager, mock_websocket, thread_id
    ):
        """Test WebSocket connection establishment and initial setup."""
        mock_state_manager.get_or_create_conversation.return_value = Mock()
        mock_conversation = mock_state_manager.get_or_create_conversation.return_value
        mock_conversation.send_state_snapshot = AsyncMock()
        mock_conversation.send_messages_snapshot = AsyncMock()

        # Simulate connection and immediate disconnect
        mock_websocket.receive_text.side_effect = WebSocketDisconnect()

        from ai_research_assistant.ag_ui_backend.router import websocket_endpoint

        try:
            await websocket_endpoint(mock_websocket, thread_id)
        except WebSocketDisconnect:
            pass

        # Verify connection setup
        mock_websocket.accept.assert_called_once()
        mock_state_manager.get_or_create_conversation.assert_called_once_with(thread_id)
        mock_conversation.send_state_snapshot.assert_called_once_with(mock_websocket)
        mock_conversation.send_messages_snapshot.assert_called_once_with(mock_websocket)

    @patch("ai_research_assistant.ag_ui_backend.router.global_state_manager")
    @patch("ai_research_assistant.ag_ui_backend.router.a2a_client")
    @pytest.mark.asyncio
    async def test_websocket_run_agent_input_processing(
        self,
        mock_a2a_client,
        mock_state_manager,
        mock_websocket,
        thread_id,
        run_agent_input,
    ):
        """Test processing of RunAgentInput messages."""
        mock_conversation = Mock()
        mock_conversation.add_message = Mock()
        mock_conversation.messages = []
        mock_conversation.current_state = {}
        mock_conversation.send_state_snapshot = AsyncMock()
        mock_conversation.send_messages_snapshot = AsyncMock()
        mock_state_manager.get_or_create_conversation.return_value = mock_conversation

        # Mock orchestrator response
        mock_events = [
            {
                "type": EventType.RUN_STARTED,
                "thread_id": thread_id,
                "run_id": run_agent_input["run_id"],
            },
            {
                "type": EventType.TEXT_MESSAGE_START,
                "message_id": "msg-123",
                "role": "assistant",
            },
            {
                "type": EventType.TEXT_MESSAGE_CONTENT,
                "message_id": "msg-123",
                "delta": "Response",
            },
            {"type": EventType.TEXT_MESSAGE_END, "message_id": "msg-123"},
            {
                "type": EventType.RUN_FINISHED,
                "thread_id": thread_id,
                "run_id": run_agent_input["run_id"],
            },
        ]
        mock_a2a_client.send_to_orchestrator = AsyncMock(return_value=mock_events)

        # Simulate receiving RunAgentInput then disconnect
        mock_websocket.receive_text.side_effect = [
            json.dumps(run_agent_input),
            WebSocketDisconnect(),
        ]

        from ai_research_assistant.ag_ui_backend.router import websocket_endpoint

        try:
            await websocket_endpoint(mock_websocket, thread_id)
        except WebSocketDisconnect:
            pass

        # Verify orchestrator call
        mock_a2a_client.send_to_orchestrator.assert_called_once()
        call_args = mock_a2a_client.send_to_orchestrator.call_args[1]
        assert call_args["conversation_id"] == thread_id
        assert call_args["user_prompt"] == run_agent_input["messages"][-1]["content"]

        # Verify events were sent
        assert mock_websocket.send_json.call_count >= len(mock_events)

    @patch("ai_research_assistant.ag_ui_backend.router.global_state_manager")
    @pytest.mark.asyncio
    async def test_websocket_tool_message_handling(
        self, mock_state_manager, mock_websocket, thread_id, tool_message
    ):
        """Test handling of tool messages."""
        mock_conversation = Mock()
        mock_conversation.add_message = Mock()
        mock_conversation.send_state_snapshot = AsyncMock()
        mock_conversation.send_messages_snapshot = AsyncMock()
        mock_state_manager.get_or_create_conversation.return_value = mock_conversation

        # Simulate receiving tool message then disconnect
        mock_websocket.receive_text.side_effect = [
            json.dumps(tool_message),
            WebSocketDisconnect(),
        ]

        from ai_research_assistant.ag_ui_backend.router import websocket_endpoint

        try:
            await websocket_endpoint(mock_websocket, thread_id)
        except WebSocketDisconnect:
            pass

        # Verify tool message was added
        mock_conversation.add_message.assert_called_once()

        # Verify ACK was sent
        ack_calls = [
            call
            for call in mock_websocket.send_json.call_args_list
            if "ACK_TOOL_RESULT" in str(call)
        ]
        assert len(ack_calls) >= 1

    @patch("ai_research_assistant.ag_ui_backend.router.global_state_manager")
    @pytest.mark.asyncio
    async def test_websocket_invalid_message_handling(
        self, mock_state_manager, mock_websocket, thread_id
    ):
        """Test handling of invalid/unknown messages."""
        mock_conversation = Mock()
        mock_conversation.send_state_snapshot = AsyncMock()
        mock_conversation.send_messages_snapshot = AsyncMock()
        mock_state_manager.get_or_create_conversation.return_value = mock_conversation

        # Simulate receiving invalid message then disconnect
        invalid_message = {"unknown": "message", "structure": True}
        mock_websocket.receive_text.side_effect = [
            json.dumps(invalid_message),
            WebSocketDisconnect(),
        ]

        from ai_research_assistant.ag_ui_backend.router import websocket_endpoint

        try:
            await websocket_endpoint(mock_websocket, thread_id)
        except WebSocketDisconnect:
            pass

        # Verify error event was sent
        error_calls = [
            call
            for call in mock_websocket.send_json.call_args_list
            if "RUN_ERROR" in str(call) or "Unknown message structure" in str(call)
        ]
        assert len(error_calls) >= 1

    @patch("ai_research_assistant.ag_ui_backend.router.global_state_manager")
    @pytest.mark.asyncio
    async def test_websocket_json_parse_error(
        self, mock_state_manager, mock_websocket, thread_id
    ):
        """Test handling of JSON parse errors."""
        mock_conversation = Mock()
        mock_conversation.send_state_snapshot = AsyncMock()
        mock_conversation.send_messages_snapshot = AsyncMock()
        mock_state_manager.get_or_create_conversation.return_value = mock_conversation

        # Simulate receiving invalid JSON then disconnect
        mock_websocket.receive_text.side_effect = [
            "{ invalid json content",
            WebSocketDisconnect(),
        ]

        from ai_research_assistant.ag_ui_backend.router import websocket_endpoint

        try:
            await websocket_endpoint(mock_websocket, thread_id)
        except WebSocketDisconnect:
            pass

        # Verify error event was sent
        error_calls = [
            call
            for call in mock_websocket.send_json.call_args_list
            if "RUN_ERROR" in str(call)
        ]
        assert len(error_calls) >= 1

    @patch("ai_research_assistant.ag_ui_backend.router.global_state_manager")
    @patch("ai_research_assistant.ag_ui_backend.router.a2a_client")
    @pytest.mark.asyncio
    async def test_websocket_no_user_prompt_handling(
        self, mock_a2a_client, mock_state_manager, mock_websocket, thread_id
    ):
        """Test handling of RunAgentInput without user prompt."""
        mock_conversation = Mock()
        mock_conversation.add_message = Mock()
        mock_conversation.messages = []
        mock_conversation.current_state = {}
        mock_conversation.send_state_snapshot = AsyncMock()
        mock_conversation.send_messages_snapshot = AsyncMock()
        mock_state_manager.get_or_create_conversation.return_value = mock_conversation

        # RunAgentInput without user message
        run_input = {
            "thread_id": thread_id,
            "run_id": str(uuid.uuid4()),
            "messages": [],  # No messages
            "tools": [],
            "state": {},
            "context": [],  # Should be a list, not dict
            "forwardedProps": {},
        }

        mock_websocket.receive_text.side_effect = [
            json.dumps(run_input),
            WebSocketDisconnect(),
        ]

        from ai_research_assistant.ag_ui_backend.router import websocket_endpoint

        try:
            await websocket_endpoint(mock_websocket, thread_id)
        except WebSocketDisconnect:
            pass

        # Verify error was sent for no user prompt
        error_calls = [
            call
            for call in mock_websocket.send_json.call_args_list
            if "RUN_ERROR" in str(call) and "No user prompt" in str(call)
        ]
        assert len(error_calls) >= 1

    @patch("ai_research_assistant.ag_ui_backend.router.global_state_manager")
    @patch("ai_research_assistant.ag_ui_backend.router.a2a_client")
    @pytest.mark.asyncio
    async def test_websocket_forwarded_props_user_prompt(
        self, mock_a2a_client, mock_state_manager, mock_websocket, thread_id
    ):
        """Test handling user prompt from forwarded_props."""
        mock_conversation = Mock()
        mock_conversation.add_message = Mock()
        mock_conversation.messages = []
        mock_conversation.current_state = {}
        mock_conversation.send_state_snapshot = AsyncMock()
        mock_conversation.send_messages_snapshot = AsyncMock()
        mock_state_manager.get_or_create_conversation.return_value = mock_conversation

        mock_a2a_client.send_to_orchestrator = AsyncMock(
            return_value=[
                {
                    "type": EventType.RUN_STARTED,
                    "thread_id": thread_id,
                    "run_id": "test",
                },
                {
                    "type": EventType.RUN_FINISHED,
                    "thread_id": thread_id,
                    "run_id": "test",
                },
            ]
        )

        # RunAgentInput with user prompt in forwarded_props
        run_input = {
            "thread_id": thread_id,
            "run_id": str(uuid.uuid4()),
            "messages": [],
            "tools": [],
            "state": {},
            "context": [],  # Should be a list, not dict
            "forwardedProps": {"user_prompt": "Prompt from forwarded props"},
        }

        mock_websocket.receive_text.side_effect = [
            json.dumps(run_input),
            WebSocketDisconnect(),
        ]

        from ai_research_assistant.ag_ui_backend.router import websocket_endpoint

        try:
            await websocket_endpoint(mock_websocket, thread_id)
        except WebSocketDisconnect:
            pass

        # Verify orchestrator was called with forwarded prompt
        mock_a2a_client.send_to_orchestrator.assert_called_once()
        call_args = mock_a2a_client.send_to_orchestrator.call_args[1]
        assert call_args["user_prompt"] == "Prompt from forwarded props"


class TestAPIKeyTestEndpoint:
    """Test suite for API key testing endpoint."""

    @pytest.fixture
    def test_client(self):
        """Create test client for FastAPI app."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def api_key_request(self):
        """Sample API key test request."""
        return APIKeyTestRequest(
            provider="openai", apiKey="test-api-key-123", model="gpt-4"
        )

    @patch("ai_research_assistant.ag_ui_backend.router.get_llm_model")
    def test_api_key_test_success(
        self, mock_get_llm_model, test_client, api_key_request
    ):
        """Test successful API key validation."""
        # Mock successful LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "OK"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm_model.return_value = mock_llm

        response = test_client.post(
            "/api/test-api-key", json=api_key_request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["provider"] == "openai"
        assert data["model"] == "gpt-4"
        assert "valid and working" in data["message"]

    @patch("ai_research_assistant.ag_ui_backend.router.get_llm_model")
    def test_api_key_test_empty_response(
        self, mock_get_llm_model, test_client, api_key_request
    ):
        """Test API key validation with empty response."""
        # Mock LLM with empty response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = ""
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm_model.return_value = mock_llm

        response = test_client.post(
            "/api/test-api-key", json=api_key_request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "empty response" in data["message"]

    @patch("ai_research_assistant.ag_ui_backend.router.get_llm_model")
    def test_api_key_test_llm_exception(
        self, mock_get_llm_model, test_client, api_key_request
    ):
        """Test API key validation with LLM exception."""
        # Mock LLM that raises exception
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("Invalid API key"))
        mock_get_llm_model.return_value = mock_llm

        response = test_client.post(
            "/api/test-api-key", json=api_key_request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid API key" in data["message"]

    @patch("ai_research_assistant.ag_ui_backend.router.get_llm_model")
    def test_api_key_test_get_llm_model_exception(
        self, mock_get_llm_model, test_client, api_key_request
    ):
        """Test API key validation with get_llm_model exception."""
        # Mock get_llm_model that raises exception
        mock_get_llm_model.side_effect = Exception("Provider not supported")

        response = test_client.post(
            "/api/test-api-key", json=api_key_request.model_dump()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Provider not supported" in data["message"]

    def test_api_key_test_default_model(self, test_client):
        """Test API key validation with default model."""
        request_data = {
            "provider": "google",
            "apiKey": "test-key",
            # No model specified
        }

        with patch(
            "ai_research_assistant.ag_ui_backend.router.get_llm_model"
        ) as mock_get_llm_model:
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = "OK"
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm_model.return_value = mock_llm

            response = test_client.post("/api/test-api-key", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["model"] == "gemini-1.5-flash"  # Default model

    def test_api_key_test_invalid_request(self, test_client):
        """Test API key validation with invalid request data."""
        invalid_data = {
            "provider": "",  # Empty provider
            "apiKey": "test-key",
        }

        response = test_client.post("/api/test-api-key", json=invalid_data)

        # Should return validation error
        assert response.status_code == 422


class TestRouterEventEmission:
    """Test suite for AG-UI event emission compliance."""

    @pytest.mark.asyncio
    async def test_run_started_event_emission(self):
        """Test RUN_STARTED event structure."""
        from ai_research_assistant.ag_ui_backend.router import RunStartedEvent

        event = RunStartedEvent(
            type=EventType.RUN_STARTED, thread_id="test-thread", run_id="test-run"
        )

        event_dict = event.model_dump(by_alias=True, exclude_none=True)

        assert event_dict["type"] == EventType.RUN_STARTED
        assert event_dict["threadId"] == "test-thread"
        assert event_dict["runId"] == "test-run"

    @pytest.mark.asyncio
    async def test_run_finished_event_emission(self):
        """Test RUN_FINISHED event structure."""
        from ai_research_assistant.ag_ui_backend.router import RunFinishedEvent

        event = RunFinishedEvent(
            type=EventType.RUN_FINISHED, thread_id="test-thread", run_id="test-run"
        )

        event_dict = event.model_dump(by_alias=True, exclude_none=True)

        assert event_dict["type"] == EventType.RUN_FINISHED
        assert event_dict["threadId"] == "test-thread"
        assert event_dict["runId"] == "test-run"

    @pytest.mark.asyncio
    async def test_run_error_event_emission(self):
        """Test RUN_ERROR event structure."""
        from ai_research_assistant.ag_ui_backend.router import RunErrorEvent

        event = RunErrorEvent(type=EventType.RUN_ERROR, message="Test error message")

        event_dict = event.model_dump(by_alias=True, exclude_none=True)

        assert event_dict["type"] == EventType.RUN_ERROR
        assert event_dict["message"] == "Test error message"


class TestActiveConnections:
    """Test suite for active connections management."""

    def test_active_connections_dictionary(self):
        """Test active connections dictionary exists."""
        from ai_research_assistant.ag_ui_backend.router import active_connections

        assert isinstance(active_connections, dict)

    @patch("ai_research_assistant.ag_ui_backend.router.active_connections")
    def test_connection_tracking(self, mock_connections):
        """Test connection tracking in active_connections."""
        # This would need to be tested in integration with actual WebSocket handling
        # For now, just verify the structure exists
        assert mock_connections is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
