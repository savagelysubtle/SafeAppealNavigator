"""
Test suite for OrchestratorAgent class.

This module contains comprehensive tests for the orchestrator agent that serves
as the central coordinator for legal research workflows and task delegation.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai_research_assistant.agents.orchestrator_agent.agent import OrchestratorAgent
from ai_research_assistant.agents.orchestrator_agent.config import (
    OrchestratorAgentConfig,
)


# Mock classes for testing
class MockLLM:
    """Mock LLM for testing orchestrator."""

    def __init__(self, provider="mock", model="mock-model"):
        self.provider = provider
        self.model = model


class MockPydanticAgent:
    """Mock PydanticAI Agent for orchestrator testing."""

    def __init__(self, model=None, system_prompt="", toolsets=None):
        self.model = model
        self.system_prompt = system_prompt
        self.toolsets = toolsets or []
        self.tools = []
        self.run_calls = []
        self.run_results = []

    async def run(self, prompt, **kwargs):
        """Mock run method that returns configurable results."""
        self.run_calls.append((prompt, kwargs))

        if self.run_results:
            result_data = self.run_results.pop(0)
        else:
            result_data = f"Mock orchestrator response to: {prompt[:50]}..."

        mock_result = Mock()
        mock_result.output = result_data
        return mock_result

    def set_next_result(self, result):
        """Set the next result to be returned by run()."""
        self.run_results.append(result)


class MockMCPServer:
    """Mock MCP server for orchestrator testing."""

    def __init__(self, name="mock_server"):
        self.name = name
        self._tools = []

    @property
    async def tools(self):
        """Async generator for tools."""
        for tool in self._tools:
            yield tool

    def add_tool(self, tool):
        """Add a tool to the mock server."""
        self._tools.append(tool)


class MockPydanticAITool:
    """Mock PydanticAI tool for testing."""

    def __init__(self, name="mock_tool"):
        self.name = name
        self.description = f"Mock tool: {name}"


@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM instance."""
    return MockLLM("test_provider", "test_model")


@pytest.fixture
def orchestrator_config():
    """Fixture providing orchestrator agent configuration."""
    return OrchestratorAgentConfig(
        agent_id="orchestrator_test_001", agent_name="TestOrchestratorAgent"
    )


@pytest.fixture
def mock_mcp_server():
    """Fixture providing a mock MCP server with tools."""
    server = MockMCPServer("orchestrator_server")
    server.add_tool(MockPydanticAITool("find_agent_tool"))
    server.add_tool(MockPydanticAITool("graph_db_tool"))
    return server


@pytest.fixture
def orchestrator_factory(mock_llm):
    """Factory fixture for creating test orchestrator agents."""

    def _create_orchestrator(config=None, toolsets=None):
        if config is None:
            config = OrchestratorAgentConfig(
                agent_id="factory_orchestrator", agent_name="FactoryOrchestrator"
            )

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            return OrchestratorAgent(
                llm_instance=mock_llm, config=config, toolsets=toolsets
            )

    return _create_orchestrator


class TestOrchestratorAgentInitialization:
    """Test cases for OrchestratorAgent initialization."""

    def test_orchestrator_initialization_with_defaults(self, mock_llm):
        """Test orchestrator initialization with default configuration."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            orchestrator = OrchestratorAgent(llm_instance=mock_llm)

        assert orchestrator.agent_name == "OrchestratorAgent"
        assert isinstance(orchestrator.config, OrchestratorAgentConfig)
        assert orchestrator.llm == mock_llm

    def test_orchestrator_initialization_with_custom_config(
        self, mock_llm, orchestrator_config
    ):
        """Test orchestrator initialization with custom configuration."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            orchestrator = OrchestratorAgent(
                llm_instance=mock_llm, config=orchestrator_config
            )

        assert orchestrator.agent_name == "TestOrchestratorAgent"
        assert orchestrator.config == orchestrator_config

    def test_orchestrator_initialization_with_toolsets(self, mock_llm, mock_mcp_server):
        """Test orchestrator initialization with MCP toolsets."""
        toolsets = [mock_mcp_server]

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            orchestrator = OrchestratorAgent(llm_instance=mock_llm, toolsets=toolsets)

        assert orchestrator.toolsets == toolsets
        assert len(orchestrator.toolsets) == 1

    def test_orchestrator_inherits_from_base_agent(self, mock_llm):
        """Test that OrchestratorAgent properly inherits from BasePydanticAgent."""
        from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            orchestrator = OrchestratorAgent(llm_instance=mock_llm)

        assert isinstance(orchestrator, BasePydanticAgent)
        assert hasattr(orchestrator, "pydantic_agent")
        assert hasattr(orchestrator, "config")

    def test_orchestrator_config_type_annotation(self, mock_llm, orchestrator_config):
        """Test that orchestrator properly annotates config type."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            orchestrator = OrchestratorAgent(
                llm_instance=mock_llm, config=orchestrator_config
            )

        # The config should be properly typed
        assert isinstance(orchestrator.config, OrchestratorAgentConfig)


class TestOrchestratorAgentOrchestrate:
    """Test cases for the orchestrate method (main agent skill)."""

    @pytest.mark.asyncio
    async def test_orchestrate_simple_query(self, orchestrator_factory):
        """Test orchestration with a simple user query."""
        orchestrator = orchestrator_factory()

        result = await orchestrator.orchestrate("Hello, how are you?")

        assert "Mock orchestrator response" in result
        assert len(orchestrator.pydantic_agent.run_calls) == 1

        # Verify the prompt construction
        call_prompt = orchestrator.pydantic_agent.run_calls[0][0]
        assert "You are an orchestrator agent" in call_prompt
        assert "Hello, how are you?" in call_prompt

    @pytest.mark.asyncio
    async def test_orchestrate_complex_request(self, orchestrator_factory):
        """Test orchestration with a complex request requiring tools."""
        orchestrator = orchestrator_factory()

        complex_query = "Search for legal precedents about workers compensation and create a summary report"
        result = await orchestrator.orchestrate(complex_query)

        assert "Mock orchestrator response" in result
        call_prompt = orchestrator.pydantic_agent.run_calls[0][0]
        assert complex_query in call_prompt
        assert "analyze the request" in call_prompt

    @pytest.mark.asyncio
    async def test_orchestrate_prompt_construction(self, orchestrator_factory):
        """Test that orchestrate constructs the prompt correctly."""
        orchestrator = orchestrator_factory()

        user_prompt = "Test prompt for analysis"
        await orchestrator.orchestrate(user_prompt)

        call_prompt = orchestrator.pydantic_agent.run_calls[0][0]

        # Verify prompt contains key elements
        assert "You are an orchestrator agent" in call_prompt
        assert "primary goal is to answer the user's request" in call_prompt
        assert "analyze the request" in call_prompt
        assert "simple question or a greeting" in call_prompt
        assert "requires an action" in call_prompt
        assert f"User request: '{user_prompt}'" in call_prompt

    @pytest.mark.asyncio
    async def test_orchestrate_with_custom_llm_response(self, orchestrator_factory):
        """Test orchestration with custom LLM response."""
        orchestrator = orchestrator_factory()

        # Set a custom response
        custom_response = "I have analyzed your request and found relevant information."
        orchestrator.pydantic_agent.set_next_result(custom_response)

        result = await orchestrator.orchestrate("Find legal information")

        assert result == custom_response

    @pytest.mark.asyncio
    async def test_orchestrate_logging_behavior(self, orchestrator_factory, caplog):
        """Test that orchestrate logs appropriately."""
        orchestrator = orchestrator_factory()

        with caplog.at_level(logging.INFO):
            await orchestrator.orchestrate("Test logging behavior")

        assert "Orchestrator received task" in caplog.text
        assert "Test logging behavior" in caplog.text

    @pytest.mark.asyncio
    async def test_orchestrate_logs_prompt_to_console(
        self, orchestrator_factory, capsys
    ):
        """Test that orchestrate logs the prompt to console."""
        orchestrator = orchestrator_factory()

        await orchestrator.orchestrate("Test console logging")

        captured = capsys.readouterr()
        assert "PROMPT SENT TO LLM" in captured.out
        assert "Test console logging" in captured.out
        assert "=" in captured.out  # Check for the separator lines

    @pytest.mark.asyncio
    async def test_orchestrate_multiple_calls(self, orchestrator_factory):
        """Test multiple orchestration calls."""
        orchestrator = orchestrator_factory()

        result1 = await orchestrator.orchestrate("First request")
        result2 = await orchestrator.orchestrate("Second request")

        assert len(orchestrator.pydantic_agent.run_calls) == 2
        assert "First request" in orchestrator.pydantic_agent.run_calls[0][0]
        assert "Second request" in orchestrator.pydantic_agent.run_calls[1][0]

    @pytest.mark.asyncio
    async def test_orchestrate_truncates_long_prompts_in_log(
        self, orchestrator_factory, caplog
    ):
        """Test that long prompts are truncated in logging."""
        orchestrator = orchestrator_factory()

        long_prompt = "A" * 200  # Create a long prompt

        with caplog.at_level(logging.INFO):
            await orchestrator.orchestrate(long_prompt)

        # Should truncate to 100 characters in log
        assert long_prompt[:100] in caplog.text
        assert (
            len([record for record in caplog.records if long_prompt in record.message])
            == 0
        )


class TestOrchestratorAgentErrorHandling:
    """Test cases for error handling in orchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrate_handles_llm_exception(
        self, orchestrator_factory, caplog
    ):
        """Test that orchestrate handles LLM exceptions gracefully."""
        orchestrator = orchestrator_factory()

        # Mock the pydantic_agent.run to raise an exception
        orchestrator.pydantic_agent.run = AsyncMock(side_effect=Exception("LLM Error"))

        with caplog.at_level(logging.ERROR):
            result = await orchestrator.orchestrate("Test error handling")

        assert "I'm sorry, I encountered an error" in result
        assert "LLM Error" in result
        assert "Error during orchestration" in caplog.text

    @pytest.mark.asyncio
    async def test_orchestrate_handles_timeout_exception(self, orchestrator_factory):
        """Test orchestrate handling of timeout exceptions."""
        orchestrator = orchestrator_factory()

        orchestrator.pydantic_agent.run = AsyncMock(
            side_effect=asyncio.TimeoutError("Request timeout")
        )

        result = await orchestrator.orchestrate("Test timeout")

        assert "I'm sorry, I encountered an error" in result
        assert "Request timeout" in result

    @pytest.mark.asyncio
    async def test_orchestrate_handles_network_exception(self, orchestrator_factory):
        """Test orchestrate handling of network-related exceptions."""
        orchestrator = orchestrator_factory()

        orchestrator.pydantic_agent.run = AsyncMock(
            side_effect=ConnectionError("Network unavailable")
        )

        result = await orchestrator.orchestrate("Test network error")

        assert "I'm sorry, I encountered an error" in result
        assert "Network unavailable" in result

    @pytest.mark.asyncio
    async def test_orchestrate_logs_exception_details(
        self, orchestrator_factory, caplog
    ):
        """Test that orchestrate logs detailed exception information."""
        orchestrator = orchestrator_factory()

        test_exception = ValueError("Detailed test error")
        orchestrator.pydantic_agent.run = AsyncMock(side_effect=test_exception)

        with caplog.at_level(logging.ERROR):
            await orchestrator.orchestrate("Test detailed logging")

        assert "Error during orchestration" in caplog.text
        assert "Detailed test error" in caplog.text
        # Should log with exc_info=True for stack trace
        assert any(
            "Traceback" in record.message or record.exc_info
            for record in caplog.records
        )


class TestOrchestratorAgentSkillDecorator:
    """Test cases for agent skill decorator on orchestrate method."""

    def test_orchestrate_has_agent_skill_decorator(self):
        """Test that orchestrate method has @agent_skill decorator."""
        from ai_research_assistant.agents.orchestrator_agent.agent import (
            OrchestratorAgent,
        )

        orchestrate_method = getattr(OrchestratorAgent, "orchestrate")

        assert hasattr(orchestrate_method, "_is_agent_skill")
        assert orchestrate_method._is_agent_skill is True
        assert hasattr(orchestrate_method, "_skill_name")
        assert orchestrate_method._skill_name == "orchestrate"

    def test_orchestrate_skill_discovery(self, orchestrator_factory):
        """Test that orchestrate can be discovered as an agent skill."""
        orchestrator = orchestrator_factory()

        # Get all methods that are marked as skills
        skills = []
        for attr_name in dir(orchestrator):
            attr = getattr(orchestrator, attr_name)
            if hasattr(attr, "_is_agent_skill") and attr._is_agent_skill:
                skills.append(attr_name)

        assert "orchestrate" in skills


class TestOrchestratorAgentIntegration:
    """Integration test cases for orchestrator workflows."""

    @pytest.mark.asyncio
    async def test_full_orchestrator_workflow(self, mock_llm, mock_mcp_server):
        """Test complete orchestrator workflow with tools."""
        # Add more tools to the server
        mock_mcp_server.add_tool(MockPydanticAITool("legal_search_tool"))
        mock_mcp_server.add_tool(MockPydanticAITool("document_creation_tool"))

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            orchestrator = OrchestratorAgent(
                llm_instance=mock_llm, toolsets=[mock_mcp_server]
            )

            # Initialize MCP tools
            await orchestrator.initialize_mcp_tools()

            # Execute orchestration
            result = await orchestrator.orchestrate(
                "I need help with a workers compensation appeal. Can you search for relevant precedents?"
            )

        assert orchestrator.agent_name == "OrchestratorAgent"
        assert len(orchestrator.toolsets) == 1
        assert len(orchestrator.pydantic_agent.tools) == 4  # 2 original + 2 added
        assert "Mock orchestrator response" in result

    @pytest.mark.asyncio
    async def test_orchestrator_with_multiple_toolsets(self, mock_llm):
        """Test orchestrator with multiple MCP toolsets."""
        server1 = MockMCPServer("legal_server")
        server2 = MockMCPServer("document_server")

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            orchestrator = OrchestratorAgent(
                llm_instance=mock_llm, toolsets=[server1, server2]
            )

            await orchestrator.initialize_mcp_tools()
            result = await orchestrator.orchestrate("Complex multi-tool request")

        assert len(orchestrator.toolsets) == 2
        assert "Mock orchestrator response" in result

    @pytest.mark.asyncio
    async def test_orchestrator_config_inheritance(self, mock_llm):
        """Test that orchestrator config properly inherits from base config."""
        config = OrchestratorAgentConfig(
            agent_id="config_test_orchestrator",
            agent_name="ConfigTestOrchestrator",
            llm_provider="openai",
            llm_model_name="gpt-4",
            pydantic_ai_system_prompt="Custom orchestrator prompt",
        )

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent",
            Mock(return_value=MockPydanticAgent()),
        ) as mock_agent_class:
            orchestrator = OrchestratorAgent(llm_instance=mock_llm, config=config)

        # Verify the Agent was created with the correct prompt
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["system_prompt"] == "Custom orchestrator prompt"


@pytest.mark.parametrize(
    "user_input,expected_in_prompt",
    [
        ("Hello", "Hello"),
        ("Search for legal cases", "Search for legal cases"),
        (
            "Create a document about workers compensation",
            "Create a document about workers compensation",
        ),
        ("What is the weather?", "What is the weather?"),
        ("Help me with WCAT appeal", "Help me with WCAT appeal"),
    ],
)
class TestOrchestratorAgentParametrized:
    """Parametrized test cases for different user inputs."""

    @pytest.mark.asyncio
    async def test_orchestrate_with_various_inputs(
        self, user_input, expected_in_prompt, orchestrator_factory
    ):
        """Test orchestration with various user inputs."""
        orchestrator = orchestrator_factory()

        await orchestrator.orchestrate(user_input)

        call_prompt = orchestrator.pydantic_agent.run_calls[0][0]
        assert expected_in_prompt in call_prompt


class TestOrchestratorAgentEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_orchestrate_with_empty_string(self, orchestrator_factory):
        """Test orchestration with empty string input."""
        orchestrator = orchestrator_factory()

        result = await orchestrator.orchestrate("")

        assert "Mock orchestrator response" in result
        call_prompt = orchestrator.pydantic_agent.run_calls[0][0]
        assert "User request: ''" in call_prompt

    @pytest.mark.asyncio
    async def test_orchestrate_with_very_long_input(self, orchestrator_factory):
        """Test orchestration with very long input."""
        orchestrator = orchestrator_factory()

        long_input = "A" * 5000  # Very long input
        result = await orchestrator.orchestrate(long_input)

        assert "Mock orchestrator response" in result
        call_prompt = orchestrator.pydantic_agent.run_calls[0][0]
        assert long_input in call_prompt

    @pytest.mark.asyncio
    async def test_orchestrate_with_special_characters(self, orchestrator_factory):
        """Test orchestration with special characters in input."""
        orchestrator = orchestrator_factory()

        special_input = "Test with 'quotes', \"double quotes\", and \n newlines \t tabs"
        result = await orchestrator.orchestrate(special_input)

        assert "Mock orchestrator response" in result
        call_prompt = orchestrator.pydantic_agent.run_calls[0][0]
        assert special_input in call_prompt

    @pytest.mark.asyncio
    async def test_orchestrate_with_unicode_characters(self, orchestrator_factory):
        """Test orchestration with unicode characters."""
        orchestrator = orchestrator_factory()

        unicode_input = (
            "Test with émojis 🤖 and special characters: café, naïve, résumé"
        )
        result = await orchestrator.orchestrate(unicode_input)

        assert "Mock orchestrator response" in result
        call_prompt = orchestrator.pydantic_agent.run_calls[0][0]
        assert unicode_input in call_prompt
