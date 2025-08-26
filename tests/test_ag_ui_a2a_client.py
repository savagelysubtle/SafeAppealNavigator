#!/usr/bin/env python3
"""
Comprehensive tests for the A2A client module.

Tests A2A client functionality including:
- Orchestrator communication via HTTP
- AG-UI event processing and conversion
- MessageEnvelope handling
- Custom event creation and validation
- Error handling and HTTP failures
"""

import uuid
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from ag_ui.core import (
    EventType,
)
from ag_ui.core import (
    Tool as AGUITool,
)
from ag_ui.core import (
    UserMessage as AGUIUserMessage,
)

from ai_research_assistant.ag_ui_backend.a2a_client import (
    A2AClient,
    CustomEventType,
    NotificationEvent,
    PlanEvent,
    StatusEvent,
)
from ai_research_assistant.core.models import (
    SkillInvocation,
)


class TestA2AClient:
    """Test suite for A2AClient class."""

    @pytest.fixture
    def client(self):
        """Create A2A client instance for testing."""
        return A2AClient("http://localhost:8001")

    @pytest.fixture
    def conversation_id(self):
        """Sample conversation ID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def user_prompt(self):
        """Sample user prompt."""
        return "Test user prompt for orchestrator"

    @pytest.fixture
    def message_history(self):
        """Sample message history."""
        return [
            AGUIUserMessage(id="1", role="user", content="Previous message"),
            AGUIUserMessage(id="2", role="user", content="Another message"),
        ]

    @pytest.fixture
    def tools(self):
        """Sample tools list."""
        return [
            AGUITool(
                name="test_tool",
                description="Test tool description",
                parameters={"type": "object", "properties": {}},
            )
        ]

    @pytest.fixture
    def current_state(self):
        """Sample current state."""
        return {"session": "active", "context": "legal_research"}

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client."""
        mock_client = Mock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock()
        return mock_client

    def test_client_initialization(self):
        """Test A2AClient initialization."""
        client = A2AClient()
        assert client.orchestrator_url is not None
        assert isinstance(client.http_client, httpx.AsyncClient)

        custom_url = "http://custom-orchestrator:9000"
        custom_client = A2AClient(custom_url)
        assert custom_client.orchestrator_url == custom_url

    @pytest.mark.asyncio
    async def test_send_to_orchestrator_success_text_response(
        self,
        client,
        conversation_id,
        user_prompt,
        message_history,
        tools,
        current_state,
    ):
        """Test successful orchestrator communication with text response."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "source_agent_id": "chief_legal_orchestrator",
            "target_agent_id": "ag_ui_backend",
            "task_result": {
                "parts": [{"type": "text/plain", "content": "Hello from orchestrator"}]
            },
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(
            client.http_client, "post", return_value=mock_response
        ) as mock_post:
            events = await client.send_to_orchestrator(
                conversation_id, user_prompt, message_history, tools, current_state
            )

            # Verify HTTP request
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == client.orchestrator_url

            # Verify events structure
            assert len(events) >= 3  # Start, Content, End

            # Check for TextMessageStart
            start_events = [
                e for e in events if e.get("type") == EventType.TEXT_MESSAGE_START
            ]
            assert len(start_events) == 1

            # Check for TextMessageContent
            content_events = [
                e for e in events if e.get("type") == EventType.TEXT_MESSAGE_CONTENT
            ]
            assert len(content_events) >= 1

            # Check for TextMessageEnd
            end_events = [
                e for e in events if e.get("type") == EventType.TEXT_MESSAGE_END
            ]
            assert len(end_events) == 1

    @pytest.mark.asyncio
    async def test_send_to_orchestrator_plan_response(
        self,
        client,
        conversation_id,
        user_prompt,
        message_history,
        tools,
        current_state,
    ):
        """Test orchestrator response with plan content."""
        plan_content = {
            "plan": ["Step 1", "Step 2"],
            "is_approved": False,
        }

        mock_response = Mock()
        mock_response.json.return_value = {
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "source_agent_id": "chief_legal_orchestrator",
            "target_agent_id": "ag_ui_backend",
            "task_result": {
                "parts": [
                    {
                        "type": "application/vnd.agent-plan.v1+json",
                        "content": plan_content,
                    }
                ]
            },
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(client.http_client, "post", return_value=mock_response):
            events = await client.send_to_orchestrator(
                conversation_id, user_prompt, message_history, tools, current_state
            )

            # Check for PlanEvent
            plan_events = [
                e for e in events if e.get("type") == CustomEventType.AGENT_PLAN
            ]
            assert len(plan_events) == 1
            assert plan_events[0]["data"]["plan"] == plan_content["plan"]

    @pytest.mark.asyncio
    async def test_send_to_orchestrator_status_response(
        self,
        client,
        conversation_id,
        user_prompt,
        message_history,
        tools,
        current_state,
    ):
        """Test orchestrator response with status content."""
        status_content = {
            "message": "Almost complete",
            "step": 75,
            "total_steps": 100,
        }

        mock_response = Mock()
        mock_response.json.return_value = {
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "source_agent_id": "chief_legal_orchestrator",
            "target_agent_id": "ag_ui_backend",
            "task_result": {
                "parts": [
                    {
                        "type": "application/vnd.agent-status.v1+json",
                        "content": status_content,
                    }
                ]
            },
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(client.http_client, "post", return_value=mock_response):
            events = await client.send_to_orchestrator(
                conversation_id, user_prompt, message_history, tools, current_state
            )

            # Check for StatusEvent
            status_events = [
                e for e in events if e.get("type") == CustomEventType.AGENT_STATUS
            ]
            assert len(status_events) == 1
            assert status_events[0]["data"]["message"] == status_content["message"]

    @pytest.mark.asyncio
    async def test_send_to_orchestrator_multiple_content_types(
        self,
        client,
        conversation_id,
        user_prompt,
        message_history,
        tools,
        current_state,
    ):
        """Test orchestrator response with multiple content types."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "source_agent_id": "chief_legal_orchestrator",
            "target_agent_id": "ag_ui_backend",
            "task_result": {
                "parts": [
                    {"type": "text/plain", "content": "Text response"},
                    {
                        "type": "application/vnd.agent-plan.v1+json",
                        "content": {"plan": ["Plan step"], "is_approved": False},
                    },
                    {
                        "type": "application/vnd.notification.v1+json",
                        "content": {"severity": "info", "message": "Notification"},
                    },
                ]
            },
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(client.http_client, "post", return_value=mock_response):
            events = await client.send_to_orchestrator(
                conversation_id, user_prompt, message_history, tools, current_state
            )

            # Should have text events plus custom events
            event_types = [e.get("type") for e in events]
            assert EventType.TEXT_MESSAGE_START in event_types
            assert EventType.TEXT_MESSAGE_CONTENT in event_types
            assert EventType.TEXT_MESSAGE_END in event_types
            assert CustomEventType.AGENT_PLAN in event_types
            assert CustomEventType.NOTIFICATION in event_types

    @pytest.mark.asyncio
    async def test_send_to_orchestrator_http_error(
        self,
        client,
        conversation_id,
        user_prompt,
        message_history,
        tools,
        current_state,
    ):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        http_error = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        )

        with patch.object(client.http_client, "post", side_effect=http_error):
            events = await client.send_to_orchestrator(
                conversation_id, user_prompt, message_history, tools, current_state
            )

            # Should return error events
            assert len(events) >= 3  # Start, Content (error), End
            content_events = [
                e for e in events if e.get("type") == EventType.TEXT_MESSAGE_CONTENT
            ]
            error_content = content_events[0]["delta"]
            assert "Error communicating with orchestrator" in error_content

    @pytest.mark.asyncio
    async def test_send_to_orchestrator_general_exception(
        self,
        client,
        conversation_id,
        user_prompt,
        message_history,
        tools,
        current_state,
    ):
        """Test general exception handling."""
        with patch.object(
            client.http_client, "post", side_effect=Exception("Connection failed")
        ):
            events = await client.send_to_orchestrator(
                conversation_id, user_prompt, message_history, tools, current_state
            )

            # Should return error events
            content_events = [
                e for e in events if e.get("type") == EventType.TEXT_MESSAGE_CONTENT
            ]
            error_content = content_events[0]["delta"]
            assert "An internal error occurred" in error_content

    @pytest.mark.asyncio
    async def test_send_to_orchestrator_no_task_result(
        self,
        client,
        conversation_id,
        user_prompt,
        message_history,
        tools,
        current_state,
    ):
        """Test orchestrator response without task result."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "source_agent_id": "chief_legal_orchestrator",
            "target_agent_id": "ag_ui_backend",
            "task_result": None,
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(client.http_client, "post", return_value=mock_response):
            events = await client.send_to_orchestrator(
                conversation_id, user_prompt, message_history, tools, current_state
            )

            # Should have fallback message
            content_events = [
                e for e in events if e.get("type") == EventType.TEXT_MESSAGE_CONTENT
            ]
            assert len(content_events) == 1
            assert "Orchestrator processed the request" in content_events[0]["delta"]

    def test_skill_invocation_creation(self, client, user_prompt, message_history):
        """Test SkillInvocation creation and serialization."""
        history_dicts = [
            msg.model_dump(by_alias=True, exclude_none=True) for msg in message_history
        ]

        skill_invocation = SkillInvocation(
            skill_name="handle_user_request",
            parameters={"user_prompt": user_prompt, "history": history_dicts},
        )

        assert skill_invocation.skill_name == "handle_user_request"
        assert skill_invocation.parameters["user_prompt"] == user_prompt
        assert len(skill_invocation.parameters["history"]) == len(message_history)

    @pytest.mark.asyncio
    async def test_invalid_content_type_handling(
        self,
        client,
        conversation_id,
        user_prompt,
        message_history,
        tools,
        current_state,
    ):
        """Test handling of invalid/unknown content types."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "source_agent_id": "chief_legal_orchestrator",
            "target_agent_id": "ag_ui_backend",
            "task_result": {
                "parts": [
                    {"type": "application/unknown-type", "content": "Unknown content"}
                ]
            },
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(client.http_client, "post", return_value=mock_response):
            events = await client.send_to_orchestrator(
                conversation_id, user_prompt, message_history, tools, current_state
            )

            # Unknown content should be treated as text
            content_events = [
                e for e in events if e.get("type") == EventType.TEXT_MESSAGE_CONTENT
            ]
            assert len(content_events) == 1
            assert "Unknown content" in content_events[0]["delta"]

    @pytest.mark.asyncio
    async def test_malformed_content_handling(
        self,
        client,
        conversation_id,
        user_prompt,
        message_history,
        tools,
        current_state,
    ):
        """Test handling of malformed content data."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "source_agent_id": "chief_legal_orchestrator",
            "target_agent_id": "ag_ui_backend",
            "task_result": {
                "parts": [
                    {
                        "type": "application/vnd.agent-plan.v1+json",
                        "content": "This should be a dict but it's a string",
                    }
                ]
            },
        }
        mock_response.raise_for_status.return_value = None

        with patch.object(client.http_client, "post", return_value=mock_response):
            events = await client.send_to_orchestrator(
                conversation_id, user_prompt, message_history, tools, current_state
            )

            # Malformed content should be treated as text
            content_events = [
                e for e in events if e.get("type") == EventType.TEXT_MESSAGE_CONTENT
            ]
            assert len(content_events) == 1


class TestCustomEvents:
    """Test suite for custom event classes."""

    def test_plan_event_creation(self):
        """Test PlanEvent creation and structure."""
        plan_data = {"plan": ["Step 1", "Step 2"], "is_approved": False}

        from ai_research_assistant.core.models import PlanPart

        plan_part = PlanPart.model_validate(plan_data)

        event = PlanEvent(message_id="test-123", data=plan_part)

        assert event.type == CustomEventType.AGENT_PLAN
        assert event.message_id == "test-123"
        assert event.data.plan == plan_data["plan"]

    def test_status_event_creation(self):
        """Test StatusEvent creation and structure."""
        status_data = {"message": "Processing step 50", "step": 50, "total_steps": 100}

        from ai_research_assistant.core.models import StatusPart

        status_part = StatusPart.model_validate(status_data)

        event = StatusEvent(message_id="test-456", data=status_part)

        assert event.type == CustomEventType.AGENT_STATUS
        assert event.message_id == "test-456"
        assert event.data.message == status_data["message"]

    def test_notification_event_creation(self):
        """Test NotificationEvent creation and structure."""
        notification_data = {"severity": "warn", "message": "Test notification"}

        from ai_research_assistant.core.models import NotificationPart

        notification_part = NotificationPart.model_validate(notification_data)

        event = NotificationEvent(message_id="test-789", data=notification_part)

        assert event.type == CustomEventType.NOTIFICATION
        assert event.message_id == "test-789"
        assert event.data.severity == notification_data["severity"]

    def test_all_custom_event_types(self):
        """Test all custom event types are defined."""
        expected_types = [
            "agent_plan",
            "agent_status",
            "code_diff",
            "file_content",
            "notification",
            "ide_command",
            "legal_analysis",
            "contract_summary",
        ]

        for event_type in expected_types:
            assert hasattr(CustomEventType, event_type.upper().replace("-", "_"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
