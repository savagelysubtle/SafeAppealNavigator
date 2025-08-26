#!/usr/bin/env python3
"""
Comprehensive tests for the AG-UI state manager module.

Tests AG-UI protocol compliance for state management including:
- Conversation state management
- Message handling and snapshots
- State delta operations with JSON Patch
- WebSocket event emission
- AG-UI protocol event structure validation
"""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from ag_ui.core import (
    EventType,
)
from ag_ui.core import (
    UserMessage as AGUIUserMessage,
)
from fastapi import WebSocket

from ai_research_assistant.ag_ui_backend.state_manager import (
    AGUIConversationState,
    AGUIStateManager,
    global_state_manager,
)


class TestAGUIConversationState:
    """Test suite for AGUIConversationState class."""

    @pytest.fixture
    def thread_id(self):
        """Sample thread ID for testing."""
        return "test-thread-123"

    @pytest.fixture
    def sample_message(self):
        """Sample AG-UI message for testing."""
        return AGUIUserMessage(
            id=str(uuid.uuid4()), role="user", content="Hello, test message"
        )

    @pytest.fixture
    def sample_state(self):
        """Sample state data for testing."""
        return {
            "user_preferences": {"theme": "dark"},
            "conversation_context": {"last_topic": "AI"},
            "session_data": {"start_time": "2024-01-01T00:00:00Z"},
        }

    @pytest.fixture
    def conversation_state(self, thread_id, sample_state):
        """Create a conversation state instance for testing."""
        return AGUIConversationState(
            thread_id=thread_id, initial_state=sample_state.copy()
        )

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket for testing."""
        websocket = Mock(spec=WebSocket)
        websocket.send_json = AsyncMock()
        return websocket

    def test_conversation_state_initialization(self, thread_id, sample_state):
        """Test AGUIConversationState initialization."""
        # Test with initial state and messages
        messages = [AGUIUserMessage(id="1", role="user", content="test")]
        state = AGUIConversationState(
            thread_id=thread_id, initial_state=sample_state, initial_messages=messages
        )

        assert state.thread_id == thread_id
        assert state.current_state == sample_state
        assert len(state.messages) == 1
        assert state.messages[0].content == "test"

    def test_conversation_state_initialization_defaults(self, thread_id):
        """Test AGUIConversationState initialization with defaults."""
        state = AGUIConversationState(thread_id=thread_id)

        assert state.thread_id == thread_id
        assert state.current_state == {}
        assert state.messages == []

    def test_add_message(self, conversation_state, sample_message):
        """Test adding messages to conversation state."""
        # Initially no messages
        assert len(conversation_state.messages) == 0

        # Add a message
        conversation_state.add_message(sample_message)

        assert len(conversation_state.messages) == 1
        assert conversation_state.messages[0] == sample_message

        # Add another message
        second_message = AGUIUserMessage(
            id=str(uuid.uuid4()), role="user", content="Second message"
        )
        conversation_state.add_message(second_message)

        assert len(conversation_state.messages) == 2
        assert conversation_state.messages[1] == second_message

    def test_update_state(self, conversation_state):
        """Test updating conversation state with new snapshot."""
        new_state = {"updated_field": "new_value", "nested": {"data": "test"}}

        conversation_state.update_state(new_state)

        assert conversation_state.current_state == new_state
        # Ensure it's not the same object reference
        assert conversation_state.current_state is not new_state

    def test_patch_state_success(self, conversation_state):
        """Test successful state patching with JSON Patch operations."""
        # Apply a patch operation
        patch_ops = [
            {"op": "add", "path": "/new_field", "value": "new_value"},
            {"op": "replace", "path": "/user_preferences/theme", "value": "light"},
        ]

        result = conversation_state.patch_state(patch_ops)

        assert result is True
        assert conversation_state.current_state["new_field"] == "new_value"
        assert conversation_state.current_state["user_preferences"]["theme"] == "light"

    def test_patch_state_failure(self, conversation_state):
        """Test state patching failure with invalid JSON Patch operations."""
        # Invalid patch operation (path doesn't exist)
        patch_ops = [{"op": "replace", "path": "/nonexistent/field", "value": "value"}]

        result = conversation_state.patch_state(patch_ops)

        assert result is False
        # State should remain unchanged
        assert "nonexistent" not in conversation_state.current_state

    @pytest.mark.asyncio
    async def test_send_state_snapshot(self, conversation_state, mock_websocket):
        """Test sending state snapshot event via WebSocket."""
        await conversation_state.send_state_snapshot(mock_websocket)

        # Verify WebSocket call
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]

        # Verify AG-UI protocol compliance
        assert call_args["type"] == EventType.STATE_SNAPSHOT
        assert call_args["snapshot"] == conversation_state.current_state

    @pytest.mark.asyncio
    async def test_send_messages_snapshot(
        self, conversation_state, mock_websocket, sample_message
    ):
        """Test sending messages snapshot event via WebSocket."""
        # Add a message first
        conversation_state.add_message(sample_message)

        await conversation_state.send_messages_snapshot(mock_websocket)

        # Verify WebSocket call
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]

        # Verify AG-UI protocol compliance
        assert call_args["type"] == EventType.MESSAGES_SNAPSHOT
        assert len(call_args["messages"]) == 1
        assert call_args["messages"][0]["id"] == sample_message.id

    @pytest.mark.asyncio
    async def test_send_state_delta(self, conversation_state, mock_websocket):
        """Test sending state delta event via WebSocket."""
        patch_ops = [{"op": "add", "path": "/delta_field", "value": "delta_value"}]

        await conversation_state.send_state_delta(mock_websocket, patch_ops)

        # Verify WebSocket call
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]

        # Verify AG-UI protocol compliance
        assert call_args["type"] == EventType.STATE_DELTA
        assert call_args["delta"] == patch_ops


class TestAGUIStateManager:
    """Test suite for AGUIStateManager class."""

    @pytest.fixture
    def state_manager(self):
        """Create a fresh state manager for testing."""
        return AGUIStateManager()

    @pytest.fixture
    def thread_id(self):
        """Sample thread ID for testing."""
        return "manager-test-thread"

    def test_get_or_create_conversation_new(self, state_manager, thread_id):
        """Test creating a new conversation state."""
        initial_state = {"test": "data"}
        messages = [AGUIUserMessage(id="1", role="user", content="test")]

        conversation = state_manager.get_or_create_conversation(
            thread_id, initial_state=initial_state, initial_messages=messages
        )

        assert conversation.thread_id == thread_id
        assert conversation.current_state == initial_state
        assert len(conversation.messages) == 1
        assert thread_id in state_manager.conversations

    def test_get_or_create_conversation_existing(self, state_manager, thread_id):
        """Test retrieving an existing conversation state."""
        # Create initial conversation
        initial_conversation = state_manager.get_or_create_conversation(thread_id)
        initial_conversation.current_state = {"existing": "data"}

        # Retrieve the same conversation
        retrieved_conversation = state_manager.get_or_create_conversation(thread_id)

        assert retrieved_conversation is initial_conversation
        assert retrieved_conversation.current_state == {"existing": "data"}

    def test_get_conversation_exists(self, state_manager, thread_id):
        """Test getting an existing conversation."""
        # Create conversation first
        created = state_manager.get_or_create_conversation(thread_id)

        # Retrieve it
        retrieved = state_manager.get_conversation(thread_id)

        assert retrieved is created
        assert retrieved is not None

    def test_get_conversation_not_exists(self, state_manager):
        """Test getting a non-existent conversation."""
        result = state_manager.get_conversation("nonexistent-thread")
        assert result is None

    def test_remove_conversation(self, state_manager, thread_id):
        """Test removing a conversation."""
        # Create conversation
        state_manager.get_or_create_conversation(thread_id)
        assert thread_id in state_manager.conversations

        # Remove it
        state_manager.remove_conversation(thread_id)
        assert thread_id not in state_manager.conversations

    def test_remove_conversation_not_exists(self, state_manager):
        """Test removing a non-existent conversation (should not raise error)."""
        # This should not raise an error
        state_manager.remove_conversation("nonexistent-thread")


class TestGlobalStateManager:
    """Test suite for global state manager instance."""

    def test_global_state_manager_singleton(self):
        """Test that global_state_manager is properly initialized."""
        assert isinstance(global_state_manager, AGUIStateManager)
        assert global_state_manager.conversations == {}

    def test_global_state_manager_functionality(self):
        """Test basic functionality of global state manager."""
        thread_id = "global-test-thread"

        # Clean up any existing state
        if thread_id in global_state_manager.conversations:
            global_state_manager.remove_conversation(thread_id)

        # Test creating conversation
        conversation = global_state_manager.get_or_create_conversation(thread_id)
        assert conversation.thread_id == thread_id

        # Test retrieval
        retrieved = global_state_manager.get_conversation(thread_id)
        assert retrieved is conversation

        # Clean up
        global_state_manager.remove_conversation(thread_id)
        assert global_state_manager.get_conversation(thread_id) is None


class TestAGUIProtocolCompliance:
    """Test suite for AG-UI protocol compliance."""

    @pytest.fixture
    def conversation_state(self):
        """Create conversation state for protocol testing."""
        return AGUIConversationState("protocol-test-thread")

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket for protocol testing."""
        websocket = Mock(spec=WebSocket)
        websocket.send_json = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_state_snapshot_event_structure(
        self, conversation_state, mock_websocket
    ):
        """Test StateSnapshotEvent structure compliance."""
        test_state = {"protocol": "test", "nested": {"data": "value"}}
        conversation_state.current_state = test_state

        await conversation_state.send_state_snapshot(mock_websocket)

        call_args = mock_websocket.send_json.call_args[0][0]

        # Verify required fields
        assert "type" in call_args
        assert "snapshot" in call_args
        assert call_args["type"] == EventType.STATE_SNAPSHOT
        assert call_args["snapshot"] == test_state

    @pytest.mark.asyncio
    async def test_messages_snapshot_event_structure(
        self, conversation_state, mock_websocket
    ):
        """Test MessagesSnapshotEvent structure compliance."""
        messages = [
            AGUIUserMessage(id="1", role="user", content="Message 1"),
            AGUIUserMessage(id="2", role="user", content="Message 2"),
        ]

        for msg in messages:
            conversation_state.add_message(msg)

        await conversation_state.send_messages_snapshot(mock_websocket)

        call_args = mock_websocket.send_json.call_args[0][0]

        # Verify required fields
        assert "type" in call_args
        assert "messages" in call_args
        assert call_args["type"] == EventType.MESSAGES_SNAPSHOT
        assert len(call_args["messages"]) == 2

    @pytest.mark.asyncio
    async def test_state_delta_event_structure(
        self, conversation_state, mock_websocket
    ):
        """Test StateDeltaEvent structure compliance."""
        patch_ops = [
            {"op": "add", "path": "/new", "value": "data"},
            {"op": "replace", "path": "/existing", "value": "updated"},
        ]

        await conversation_state.send_state_delta(mock_websocket, patch_ops)

        call_args = mock_websocket.send_json.call_args[0][0]

        # Verify required fields
        assert "type" in call_args
        assert "delta" in call_args
        assert call_args["type"] == EventType.STATE_DELTA
        assert call_args["delta"] == patch_ops

    def test_json_patch_operations_compliance(self, conversation_state):
        """Test JSON Patch operations compliance (RFC 6902)."""
        # Set up initial state with required keys for testing
        conversation_state.current_state = {
            "user_preferences": {"theme": "dark"},
            "existing": "old_value",
        }

        # Test various JSON Patch operations
        test_cases = [
            # Add operation
            ([{"op": "add", "path": "/new_key", "value": "new_value"}], True),
            # Replace operation
            (
                [
                    {
                        "op": "replace",
                        "path": "/user_preferences",
                        "value": {"theme": "light"},
                    }
                ],
                True,
            ),
            # Remove operation (after adding something to remove)
            (
                [
                    {"op": "add", "path": "/temp", "value": "temporary"},
                    {"op": "remove", "path": "/temp"},
                ],
                True,
            ),
            # Invalid operation (missing required field)
            ([{"op": "add", "path": "/invalid"}], False),
            # Invalid path
            ([{"op": "replace", "path": "/nonexistent/path", "value": "value"}], False),
        ]

        for patch_ops, should_succeed in test_cases:
            result = conversation_state.patch_state(patch_ops)
            assert result == should_succeed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
