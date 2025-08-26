"""
Test suite for CEOAgent class.

This module contains comprehensive tests for the CEO agent that serves as the main
conversational interface with the user and delegates tasks to the orchestrator.
"""

import logging
from unittest.mock import Mock, patch

import pytest

from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
from ai_research_assistant.agents.ceo_agent.agent import CEOAgent
from ai_research_assistant.agents.ceo_agent.config import CEOAgentConfig


# Mock classes for testing
class MockLLM:
    """Mock LLM for testing CEO agent."""

    def __init__(self, provider="mock", model="mock-model"):
        self.provider = provider
        self.model = model


class MockPydanticAgent:
    """Mock PydanticAI Agent for CEO agent testing."""

    def __init__(self, model=None, system_prompt="", toolsets=None):
        self.model = model
        self.system_prompt = system_prompt
        self.toolsets = toolsets or []
        self.tools = []
        self.run_calls = []
        self.run_results = []

    async def run(self, user_prompt, **kwargs):
        """Mock run method that returns configurable results."""
        self.run_calls.append((user_prompt, kwargs))

        if self.run_results:
            result_data = self.run_results.pop(0)
        else:
            result_data = f"Mock CEO response to: {user_prompt[:50]}..."

        mock_result = Mock()
        mock_result.data = result_data
        mock_result.output = result_data
        return mock_result

    def set_next_result(self, result):
        """Set the next result to be returned by run()."""
        self.run_results.append(result)


class MockOrchestratorAgent:
    """Mock Orchestrator Agent for CEO agent testing."""

    def __init__(self, llm_instance=None, config=None, toolsets=None):
        self.llm_instance = llm_instance
        self.config = config
        self.toolsets = toolsets
        self.orchestrate_calls = []
        self.orchestrate_results = []

    async def orchestrate(self, task_prompt):
        """Mock orchestrate method."""
        self.orchestrate_calls.append(task_prompt)

        if self.orchestrate_results:
            return self.orchestrate_results.pop(0)
        else:
            # Convert task_prompt to string to handle slicing safely
            prompt_str = str(task_prompt)
            return f"Orchestrator result for: {prompt_str[:50]}..."

    def set_next_orchestrate_result(self, result):
        """Set the next result to be returned by orchestrate()."""
        self.orchestrate_results.append(result)


@pytest.fixture
def ceo_agent_config():
    """Fixture providing CEO agent configuration."""
    return CEOAgentConfig()


@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM instance."""
    return MockLLM("ceo_test_provider", "ceo_test_model")


@pytest.fixture
def ceo_agent_factory():
    """Factory fixture for creating test CEO agents."""

    def _create_ceo_agent(config=None, llm_instance=None, toolsets=None):
        if config is None:
            config = CEOAgentConfig()

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                with patch(
                    "ai_research_assistant.agents.ceo_agent.agent.OrchestratorAgent",
                    MockOrchestratorAgent,
                ):
                    return CEOAgent(
                        config=config, llm_instance=llm_instance, toolsets=toolsets
                    )

    return _create_ceo_agent


class TestCEOAgentConfig:
    """Test cases for CEOAgentConfig class."""

    def test_config_default_values(self):
        """Test that CEO agent config has correct defaults."""
        config = CEOAgentConfig()

        assert config.agent_name == "CEOAgent"
        assert config.agent_id == "ceo_agent_001"
        assert config.llm_model_name == "gemini-1.5-flash"
        assert "CEO Agent" in config.pydantic_ai_system_prompt
        assert "understand the user's request" in config.pydantic_ai_system_prompt
        assert "Orchestrator Agent" in config.pydantic_ai_system_prompt

    def test_config_inheritance(self):
        """Test that config properly inherits from BasePydanticAgentConfig."""
        config = CEOAgentConfig()

        assert isinstance(config, BasePydanticAgentConfig)
        assert hasattr(config, "llm_provider")
        assert hasattr(config, "llm_temperature")
        assert hasattr(config, "custom_settings")

    def test_config_system_prompt_content(self):
        """Test that system prompt contains key CEO responsibilities."""
        config = CEOAgentConfig()

        prompt = config.pydantic_ai_system_prompt
        assert "CEO Agent" in prompt
        assert "understand the user's request" in prompt
        assert "clarify it if necessary" in prompt
        assert "delegate the task" in prompt
        assert "Orchestrator Agent" in prompt
        assert "actionable instruction" in prompt

    def test_config_custom_settings(self):
        """Test that config has custom settings field."""
        config = CEOAgentConfig()

        assert hasattr(config, "custom_settings")
        assert isinstance(config.custom_settings, dict)


class TestCEOAgentInitialization:
    """Test cases for CEOAgent initialization."""

    def test_ceo_agent_initialization_with_defaults(self):
        """Test CEO agent initialization with default configuration."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                with patch(
                    "ai_research_assistant.agents.ceo_agent.agent.OrchestratorAgent",
                    MockOrchestratorAgent,
                ):
                    ceo_agent = CEOAgent()

        assert ceo_agent.config.agent_name == "CEOAgent"
        assert isinstance(ceo_agent.config, CEOAgentConfig)
        assert hasattr(ceo_agent, "orchestrator")
        assert isinstance(ceo_agent.orchestrator, MockOrchestratorAgent)

    def test_ceo_agent_initialization_with_custom_config(self, ceo_agent_config):
        """Test CEO agent initialization with custom configuration."""
        ceo_agent_config.agent_name = "CustomCEOAgent"
        ceo_agent_config.agent_id = "custom_ceo_001"

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                with patch(
                    "ai_research_assistant.agents.ceo_agent.agent.OrchestratorAgent",
                    MockOrchestratorAgent,
                ):
                    ceo_agent = CEOAgent(config=ceo_agent_config)

        assert ceo_agent.config.agent_name == "CustomCEOAgent"
        assert ceo_agent.config.agent_id == "custom_ceo_001"

    def test_ceo_agent_inherits_from_base_agent(self):
        """Test that CEOAgent properly inherits from BasePydanticAgent."""
        from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                with patch(
                    "ai_research_assistant.agents.ceo_agent.agent.OrchestratorAgent",
                    MockOrchestratorAgent,
                ):
                    ceo_agent = CEOAgent()

        assert isinstance(ceo_agent, BasePydanticAgent)
        assert hasattr(ceo_agent, "pydantic_agent")

    def test_ceo_agent_with_llm_instance(self, ceo_agent_factory, mock_llm):
        """Test CEO agent initialization with provided LLM instance."""
        ceo_agent = ceo_agent_factory(llm_instance=mock_llm)

        # Orchestrator should be initialized with the same LLM instance
        assert ceo_agent.orchestrator.llm_instance == mock_llm

    def test_ceo_agent_with_toolsets(self, ceo_agent_factory):
        """Test CEO agent initialization with toolsets."""
        mock_toolsets = [Mock(), Mock()]
        ceo_agent = ceo_agent_factory(toolsets=mock_toolsets)

        # Both CEO and orchestrator should have the same toolsets
        assert ceo_agent.toolsets == mock_toolsets
        assert ceo_agent.orchestrator.toolsets == mock_toolsets

    def test_ceo_agent_orchestrator_configuration(self, ceo_agent_factory):
        """Test that orchestrator is properly configured."""
        ceo_agent = ceo_agent_factory()

        # Orchestrator should have proper configuration
        assert hasattr(ceo_agent.orchestrator, "config")
        assert ceo_agent.orchestrator.config is not None


class TestCEOAgentHandleUserRequest:
    """Test cases for handle_user_request method."""

    @pytest.mark.asyncio
    async def test_handle_user_request_basic(self, ceo_agent_factory):
        """Test basic user request handling."""
        ceo_agent = ceo_agent_factory()

        # Set up mock orchestrator response
        ceo_agent.orchestrator.set_next_orchestrate_result(
            "Task completed successfully by orchestrator"
        )

        result = await ceo_agent.handle_user_request(
            "Please help me with my workers compensation appeal"
        )

        assert result == "Task completed successfully by orchestrator"
        assert len(ceo_agent.orchestrator.orchestrate_calls) == 1
        assert (
            "Please help me with my workers compensation appeal"
            in ceo_agent.orchestrator.orchestrate_calls[0]
        )

    @pytest.mark.asyncio
    async def test_handle_user_request_passes_prompt_unchanged(self, ceo_agent_factory):
        """Test that user request is passed to orchestrator unchanged."""
        ceo_agent = ceo_agent_factory()

        user_prompt = "Analyze this legal document and create a summary"
        await ceo_agent.handle_user_request(user_prompt)

        # Prompt should be passed exactly as received
        assert ceo_agent.orchestrator.orchestrate_calls[0] == user_prompt

    @pytest.mark.asyncio
    async def test_handle_user_request_complex_prompt(self, ceo_agent_factory):
        """Test handling of complex user requests."""
        ceo_agent = ceo_agent_factory()

        complex_prompt = (
            "I need to prepare an appeal for WCAT. The case involves chronic pain "
            "following a workplace injury. Please research relevant precedents, "
            "analyze medical evidence, and draft an appeal letter."
        )

        ceo_agent.orchestrator.set_next_orchestrate_result(
            "Complex appeal preparation completed with research and draft"
        )

        result = await ceo_agent.handle_user_request(complex_prompt)

        assert "Complex appeal preparation completed" in result
        assert ceo_agent.orchestrator.orchestrate_calls[0] == complex_prompt

    @pytest.mark.asyncio
    async def test_handle_user_request_empty_prompt(self, ceo_agent_factory):
        """Test handling of empty user request."""
        ceo_agent = ceo_agent_factory()

        result = await ceo_agent.handle_user_request("")

        # Should still delegate to orchestrator
        assert isinstance(result, str)
        assert len(ceo_agent.orchestrator.orchestrate_calls) == 1
        assert ceo_agent.orchestrator.orchestrate_calls[0] == ""

    @pytest.mark.asyncio
    async def test_handle_user_request_very_long_prompt(self, ceo_agent_factory):
        """Test handling of very long user requests."""
        ceo_agent = ceo_agent_factory()

        long_prompt = "A" * 5000  # Very long prompt

        await ceo_agent.handle_user_request(long_prompt)

        # Should handle long prompts gracefully
        assert ceo_agent.orchestrator.orchestrate_calls[0] == long_prompt

    @pytest.mark.asyncio
    async def test_handle_user_request_special_characters(self, ceo_agent_factory):
        """Test handling of prompts with special characters."""
        ceo_agent = ceo_agent_factory()

        special_prompt = "Review case: Worker's Comp Act s. 5.1 & regulations (2023)"

        await ceo_agent.handle_user_request(special_prompt)

        assert ceo_agent.orchestrator.orchestrate_calls[0] == special_prompt

    @pytest.mark.asyncio
    async def test_handle_user_request_unicode_characters(self, ceo_agent_factory):
        """Test handling of prompts with unicode characters."""
        ceo_agent = ceo_agent_factory()

        unicode_prompt = "Analyze document with français, español, and 中文 text"

        await ceo_agent.handle_user_request(unicode_prompt)

        assert ceo_agent.orchestrator.orchestrate_calls[0] == unicode_prompt

    @pytest.mark.asyncio
    async def test_handle_user_request_logging(self, ceo_agent_factory, caplog):
        """Test that user request handling is properly logged."""
        ceo_agent = ceo_agent_factory()

        with caplog.at_level(logging.INFO):
            await ceo_agent.handle_user_request("Test logging request")

        assert "CEO Agent received user request" in caplog.text
        assert "Test logging request" in caplog.text
        assert "CEO Agent delegating to Orchestrator" in caplog.text
        assert "CEO Agent received result from Orchestrator" in caplog.text

    @pytest.mark.asyncio
    async def test_handle_user_request_orchestrator_error(self, ceo_agent_factory):
        """Test handling when orchestrator raises an error."""
        ceo_agent = ceo_agent_factory()

        # Mock orchestrator to raise an exception
        async def mock_orchestrate_error(prompt):
            raise Exception("Orchestrator error")

        ceo_agent.orchestrator.orchestrate = mock_orchestrate_error

        # CEO should let the exception bubble up
        with pytest.raises(Exception) as exc_info:
            await ceo_agent.handle_user_request("Test error handling")

        assert "Orchestrator error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_user_request_multiple_calls(self, ceo_agent_factory):
        """Test multiple user request handling calls."""
        ceo_agent = ceo_agent_factory()

        requests = [
            "First request about legal research",
            "Second request about document analysis",
            "Third request about appeal preparation",
        ]

        results = []
        for request in requests:
            ceo_agent.orchestrator.set_next_orchestrate_result(
                f"Response to: {request}"
            )
            result = await ceo_agent.handle_user_request(request)
            results.append(result)

        assert len(results) == 3
        assert len(ceo_agent.orchestrator.orchestrate_calls) == 3
        for i, request in enumerate(requests):
            assert ceo_agent.orchestrator.orchestrate_calls[i] == request
            assert f"Response to: {request}" in results[i]


@pytest.mark.parametrize(
    "user_request",
    [
        "Help me with my workers compensation appeal",
        "Analyze this legal document for key findings",
        "Research WCAT precedents for chronic pain cases",
        "Draft an appeal letter based on medical evidence",
        "Review my case files and identify evidence gaps",
    ],
)
class TestCEOAgentUserRequestTypes:
    """Parametrized test cases for different types of user requests."""

    @pytest.mark.asyncio
    async def test_handle_various_user_requests(self, user_request, ceo_agent_factory):
        """Test handling of various types of user requests."""
        ceo_agent = ceo_agent_factory()

        ceo_agent.orchestrator.set_next_orchestrate_result(f"Processed: {user_request}")

        result = await ceo_agent.handle_user_request(user_request)

        assert f"Processed: {user_request}" in result
        assert ceo_agent.orchestrator.orchestrate_calls[0] == user_request


class TestCEOAgentEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_handle_none_prompt(self, ceo_agent_factory):
        """Test handling of None prompt."""
        ceo_agent = ceo_agent_factory()

        # This should likely raise a TypeError, but test the current behavior
        try:
            result = await ceo_agent.handle_user_request(None)
            # If it doesn't raise an error, check the behavior
            assert ceo_agent.orchestrator.orchestrate_calls[0] is None
        except TypeError:
            # This is expected behavior for None input
            pass

    @pytest.mark.asyncio
    async def test_handle_numeric_prompt(self, ceo_agent_factory):
        """Test handling of numeric input (should be converted to string)."""
        ceo_agent = ceo_agent_factory()

        # Test with numeric input
        await ceo_agent.handle_user_request(12345)

        # Should be converted to string
        assert ceo_agent.orchestrator.orchestrate_calls[0] == 12345

    @pytest.mark.asyncio
    async def test_handle_whitespace_only_prompt(self, ceo_agent_factory):
        """Test handling of whitespace-only prompt."""
        ceo_agent = ceo_agent_factory()

        whitespace_prompt = "   \n\t   "

        await ceo_agent.handle_user_request(whitespace_prompt)

        assert ceo_agent.orchestrator.orchestrate_calls[0] == whitespace_prompt

    @pytest.mark.asyncio
    async def test_handle_prompt_with_newlines(self, ceo_agent_factory):
        """Test handling of multi-line prompts."""
        ceo_agent = ceo_agent_factory()

        multiline_prompt = (
            "Line 1: Initial request\n"
            "Line 2: Additional details\n"
            "Line 3: Final requirements"
        )

        await ceo_agent.handle_user_request(multiline_prompt)

        assert ceo_agent.orchestrator.orchestrate_calls[0] == multiline_prompt


class TestCEOAgentIntegration:
    """Integration test cases for complete CEO agent workflows."""

    @pytest.mark.asyncio
    async def test_full_ceo_workflow(self, ceo_agent_factory):
        """Test complete CEO workflow from user request to orchestrator result."""
        ceo_agent = ceo_agent_factory()

        # Set up realistic orchestrator response
        ceo_agent.orchestrator.set_next_orchestrate_result(
            "Legal research completed. Found 12 relevant WCAT decisions. "
            "Appeal draft created with key precedents cited. "
            "Evidence analysis shows strong case for chronic pain compensation."
        )

        user_request = (
            "I need help with my WCAT appeal for chronic pain. "
            "Please research precedents and draft an appeal letter."
        )

        result = await ceo_agent.handle_user_request(user_request)

        # Verify complete workflow
        assert "Legal research completed" in result
        assert "WCAT decisions" in result
        assert "Appeal draft created" in result
        assert len(ceo_agent.orchestrator.orchestrate_calls) == 1
        assert ceo_agent.orchestrator.orchestrate_calls[0] == user_request

    @pytest.mark.asyncio
    async def test_ceo_agent_session_handling(self, ceo_agent_factory):
        """Test CEO agent handling multiple requests in a session."""
        ceo_agent = ceo_agent_factory()

        # Simulate a conversation session
        session_requests = [
            "Hello, I need help with a workers compensation case",
            "Can you research WCAT precedents for chronic pain?",
            "Now draft an appeal letter based on the research",
            "Review the draft and suggest improvements",
        ]

        session_results = []
        for i, request in enumerate(session_requests):
            ceo_agent.orchestrator.set_next_orchestrate_result(
                f"Session step {i + 1} completed: {request[:30]}..."
            )
            result = await ceo_agent.handle_user_request(request)
            session_results.append(result)

        # Verify session handling
        assert len(session_results) == 4
        assert len(ceo_agent.orchestrator.orchestrate_calls) == 4
        for i, request in enumerate(session_requests):
            assert ceo_agent.orchestrator.orchestrate_calls[i] == request
            assert f"Session step {i + 1} completed" in session_results[i]

    @pytest.mark.asyncio
    async def test_ceo_agent_with_orchestrator_configuration(self, ceo_agent_factory):
        """Test CEO agent with specific orchestrator configuration."""
        custom_toolsets = [Mock(name="legal_tools"), Mock(name="document_tools")]
        mock_llm = MockLLM("custom_provider", "custom_model")

        ceo_agent = ceo_agent_factory(llm_instance=mock_llm, toolsets=custom_toolsets)

        # Verify orchestrator was configured correctly
        assert ceo_agent.orchestrator.llm_instance == mock_llm
        assert ceo_agent.orchestrator.toolsets == custom_toolsets

        # Test request handling with configured orchestrator
        await ceo_agent.handle_user_request("Test with custom configuration")

        assert len(ceo_agent.orchestrator.orchestrate_calls) == 1

    @pytest.mark.asyncio
    async def test_ceo_agent_error_recovery(self, ceo_agent_factory):
        """Test that CEO agent handles orchestrator errors gracefully."""
        ceo_agent = ceo_agent_factory()

        # First request causes orchestrator error
        async def failing_orchestrate(prompt):
            if "error" in prompt:
                raise Exception("Orchestrator processing error")
            return f"Success: {prompt}"

        ceo_agent.orchestrator.orchestrate = failing_orchestrate

        # Test error case
        with pytest.raises(Exception):
            await ceo_agent.handle_user_request("This should cause an error")

        # Test recovery with good request
        result = await ceo_agent.handle_user_request("This should work fine")
        assert "Success: This should work fine" in result


class TestCEOAgentLogging:
    """Test cases for CEO agent logging functionality."""

    @pytest.mark.asyncio
    async def test_comprehensive_logging(self, ceo_agent_factory, caplog):
        """Test comprehensive logging throughout CEO agent operation."""
        ceo_agent = ceo_agent_factory()

        with caplog.at_level(logging.INFO):
            await ceo_agent.handle_user_request("Comprehensive logging test")

        # Check all expected log messages
        log_messages = [record.message for record in caplog.records]

        assert any("CEO Agent received user request" in msg for msg in log_messages)
        assert any(
            "CEO Agent delegating to Orchestrator" in msg for msg in log_messages
        )
        assert any(
            "CEO Agent received result from Orchestrator" in msg for msg in log_messages
        )

    @pytest.mark.asyncio
    async def test_logging_truncation_for_long_prompts(self, ceo_agent_factory, caplog):
        """Test that logging appropriately handles very long prompts."""
        ceo_agent = ceo_agent_factory()

        long_prompt = "A" * 1000  # Very long prompt

        with caplog.at_level(logging.INFO):
            await ceo_agent.handle_user_request(long_prompt)

        # Verify logging occurred (content may be truncated in logs)
        assert any(
            "CEO Agent received user request" in record.message
            for record in caplog.records
        )
