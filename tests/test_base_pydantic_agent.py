"""
Test suite for BasePydanticAgent class.

This module contains comprehensive tests for the base agent class that serves
as the foundation for all agents in the system, including LLM integration,
MCP tool management, and agent skill functionality.
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai_research_assistant.agents.base_pydantic_agent import (
    BasePydanticAgent,
    agent_skill,
)
from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)


# Mock classes for testing
class MockLLM:
    """Mock LLM for testing."""

    def __init__(self, provider="mock", model="mock-model"):
        self.provider = provider
        self.model = model


class MockMCPServer:
    """Mock MCP server for testing."""

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


class MockPydanticAgent:
    """Mock PydanticAI Agent for testing."""

    def __init__(self, model=None, system_prompt="", toolsets=None):
        self.model = model
        self.system_prompt = system_prompt
        self.toolsets = toolsets or []
        self.tools = []
        self.run_calls = []

    async def run(self, prompt, **kwargs):
        """Mock run method."""
        self.run_calls.append((prompt, kwargs))
        mock_result = Mock()
        mock_result.output = f"Mock response to: {prompt[:50]}..."
        return mock_result


class MockLLMFactory:
    """Mock LLM factory for testing."""

    def __init__(self):
        self.create_calls = []

    def create_llm_from_config(self, config):
        """Mock LLM creation."""
        self.create_calls.append(config)
        return MockLLM(config.get("provider", "mock"), config.get("model_name", "mock"))


@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM instance."""
    return MockLLM("test_provider", "test_model")


@pytest.fixture
def mock_llm_factory():
    """Fixture providing a mock LLM factory."""
    return MockLLMFactory()


@pytest.fixture
def mock_mcp_server():
    """Fixture providing a mock MCP server."""
    server = MockMCPServer("test_server")
    server.add_tool(MockPydanticAITool("tool1"))
    server.add_tool(MockPydanticAITool("tool2"))
    return server


@pytest.fixture
def sample_config():
    """Fixture providing a sample agent configuration."""
    return BasePydanticAgentConfig(
        agent_id="test_agent_001",
        agent_name="TestAgent",
        llm_provider="google",
        llm_model_name="gemini-1.5-flash",
    )


@pytest.fixture
def agent_factory(mock_llm_factory):
    """Factory fixture for creating test agents."""

    def _create_agent(config=None, llm_instance=None, toolsets=None):
        if config is None:
            config = BasePydanticAgentConfig(
                agent_id="factory_agent", agent_name="FactoryAgent"
            )

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory",
            return_value=mock_llm_factory,
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.Agent",
                MockPydanticAgent,
            ):
                return BasePydanticAgent(
                    config=config, llm_instance=llm_instance, toolsets=toolsets
                )

    return _create_agent


class TestAgentSkillDecorator:
    """Test cases for the @agent_skill decorator."""

    def test_agent_skill_decorator_adds_attributes(self):
        """Test that @agent_skill decorator adds the required attributes."""

        @agent_skill
        def test_skill(self):
            return "skill result"

        assert hasattr(test_skill, "_is_agent_skill")
        assert test_skill._is_agent_skill is True
        assert hasattr(test_skill, "_skill_name")
        assert test_skill._skill_name == "test_skill"

    def test_agent_skill_decorator_preserves_function(self):
        """Test that decorator preserves the original function."""

        @agent_skill
        def test_skill(self, arg1, arg2=None):
            return f"Result: {arg1}, {arg2}"

        # Function should still work normally
        result = test_skill(None, "value1", arg2="value2")
        assert result == "Result: value1, value2"

    def test_agent_skill_decorator_with_async_function(self):
        """Test decorator works with async functions."""

        @agent_skill
        async def async_skill(self):
            return "async result"

        assert hasattr(async_skill, "_is_agent_skill")
        assert async_skill._is_agent_skill is True
        assert async_skill._skill_name == "async_skill"


class TestBasePydanticAgentInitialization:
    """Test cases for BasePydanticAgent initialization."""

    def test_agent_initialization_with_defaults(self, sample_config, mock_llm_factory):
        """Test agent initialization with default parameters."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory",
            return_value=mock_llm_factory,
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.Agent",
                MockPydanticAgent,
            ):
                agent = BasePydanticAgent(config=sample_config)

        assert agent.config == sample_config
        assert agent.agent_name == "TestAgent"
        assert agent.toolsets == []
        assert mock_llm_factory.create_calls == [
            {"provider": "google", "model_name": "gemini-1.5-flash"}
        ]

    def test_agent_initialization_with_custom_llm(self, sample_config, mock_llm):
        """Test agent initialization with provided LLM instance."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            agent = BasePydanticAgent(config=sample_config, llm_instance=mock_llm)

        assert agent.llm == mock_llm
        assert agent.agent_name == "TestAgent"

    def test_agent_initialization_with_toolsets(
        self, sample_config, mock_llm, mock_mcp_server
    ):
        """Test agent initialization with MCP toolsets."""
        toolsets = [mock_mcp_server]

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            agent = BasePydanticAgent(
                config=sample_config, llm_instance=mock_llm, toolsets=toolsets
            )

        assert agent.toolsets == toolsets
        assert len(agent.toolsets) == 1

    def test_agent_initialization_creates_pydantic_agent(self, sample_config, mock_llm):
        """Test that initialization creates underlying PydanticAI agent."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent",
            Mock(return_value=MockPydanticAgent()),
        ) as mock_agent_class:
            agent = BasePydanticAgent(config=sample_config, llm_instance=mock_llm)

        assert isinstance(agent.pydantic_agent, MockPydanticAgent)
        mock_agent_class.assert_called_once()

    def test_agent_initialization_with_system_prompt(self, sample_config, mock_llm):
        """Test agent initialization with system prompt configuration."""
        sample_config.pydantic_ai_system_prompt = "You are a test agent"

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent",
            Mock(return_value=MockPydanticAgent()),
        ) as mock_agent_class:
            agent = BasePydanticAgent(config=sample_config, llm_instance=mock_llm)

        # Verify Agent was called with the system prompt
        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["system_prompt"] == "You are a test agent"

    def test_agent_initialization_with_instructions(self, sample_config, mock_llm):
        """Test agent initialization with AI instructions."""
        sample_config.pydantic_ai_instructions = "Follow these instructions"

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent",
            Mock(return_value=MockPydanticAgent()),
        ) as mock_agent_class:
            agent = BasePydanticAgent(config=sample_config, llm_instance=mock_llm)

        call_kwargs = mock_agent_class.call_args[1]
        assert call_kwargs["system_prompt"] == "Follow these instructions"


class TestBasePydanticAgentMCPTools:
    """Test cases for MCP tool management."""

    @pytest.mark.asyncio
    async def test_initialize_mcp_tools_empty_toolsets(self, agent_factory):
        """Test MCP tool initialization with empty toolsets."""
        agent = agent_factory()

        await agent.initialize_mcp_tools()

        # Should not add any tools since no toolsets provided
        assert len(agent.pydantic_agent.tools) == 0

    @pytest.mark.asyncio
    async def test_initialize_mcp_tools_with_toolsets(
        self, agent_factory, mock_mcp_server
    ):
        """Test MCP tool initialization with toolsets."""
        agent = agent_factory(toolsets=[mock_mcp_server])

        await agent.initialize_mcp_tools()

        # Should add tools from the mock server
        assert len(agent.pydantic_agent.tools) == 2

    @pytest.mark.asyncio
    async def test_get_mcp_tools_empty_toolsets(self, agent_factory):
        """Test _get_mcp_tools with empty toolsets."""
        agent = agent_factory()

        tools = await agent._get_mcp_tools()

        assert tools == []

    @pytest.mark.asyncio
    async def test_get_mcp_tools_with_multiple_servers(self, agent_factory):
        """Test _get_mcp_tools with multiple MCP servers."""
        server1 = MockMCPServer("server1")
        server1.add_tool(MockPydanticAITool("tool_a"))
        server1.add_tool(MockPydanticAITool("tool_b"))

        server2 = MockMCPServer("server2")
        server2.add_tool(MockPydanticAITool("tool_c"))

        agent = agent_factory(toolsets=[server1, server2])

        tools = await agent._get_mcp_tools()

        assert len(tools) == 3
        tool_names = [tool.name for tool in tools]
        assert "tool_a" in tool_names
        assert "tool_b" in tool_names
        assert "tool_c" in tool_names

    @pytest.mark.asyncio
    async def test_get_mcp_tools_handles_exceptions(self, agent_factory, caplog):
        """Test _get_mcp_tools handles exceptions gracefully."""
        # Create a mock server that raises an exception
        faulty_server = Mock()

        async def faulty_tools():
            raise Exception("Server error")
            yield  # This will never be reached

        faulty_server.tools = faulty_tools()

        good_server = MockMCPServer("good_server")
        good_server.add_tool(MockPydanticAITool("working_tool"))

        agent = agent_factory(toolsets=[faulty_server, good_server])

        with caplog.at_level(logging.ERROR):
            tools = await agent._get_mcp_tools()

        # Should still get tools from the working server
        assert len(tools) == 1
        assert tools[0].name == "working_tool"

        # Should log the error
        assert "Failed to fetch tools" in caplog.text


class TestBasePydanticAgentSkillExecution:
    """Test cases for agent skill execution."""

    @pytest.mark.asyncio
    async def test_run_skill_basic_execution(self, agent_factory):
        """Test basic skill execution."""
        agent = agent_factory()

        result = await agent.run_skill("Test prompt")

        assert "Mock response to: Test prompt" in result
        assert len(agent.pydantic_agent.run_calls) == 1

    @pytest.mark.asyncio
    async def test_run_skill_with_kwargs(self, agent_factory):
        """Test skill execution with keyword arguments."""
        agent = agent_factory()

        result = await agent.run_skill("Test prompt", temperature=0.5, max_tokens=100)

        assert "Mock response to: Test prompt" in result
        call_args = agent.pydantic_agent.run_calls[0]
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_run_skill_multiple_calls(self, agent_factory):
        """Test multiple skill executions."""
        agent = agent_factory()

        result1 = await agent.run_skill("First prompt")
        result2 = await agent.run_skill("Second prompt")

        assert len(agent.pydantic_agent.run_calls) == 2
        assert "First prompt" in agent.pydantic_agent.run_calls[0][0]
        assert "Second prompt" in agent.pydantic_agent.run_calls[1][0]

    @pytest.mark.asyncio
    async def test_run_skill_logs_execution(self, agent_factory, caplog):
        """Test that skill execution is logged."""
        agent = agent_factory()

        with caplog.at_level(logging.DEBUG):
            await agent.run_skill("Test prompt for logging")

        assert "Running skill for FactoryAgent" in caplog.text
        assert "Test prompt for logging" in caplog.text


class TestBasePydanticAgentErrorHandling:
    """Test cases for error handling scenarios."""

    def test_agent_initialization_with_invalid_config(self):
        """Test agent initialization with invalid configuration."""
        with pytest.raises(Exception):
            # This should fail due to missing required config fields
            BasePydanticAgent(config=None)

    @pytest.mark.asyncio
    async def test_run_skill_with_llm_error(self, agent_factory):
        """Test skill execution when LLM raises an error."""
        agent = agent_factory()

        # Mock the pydantic_agent.run to raise an exception
        agent.pydantic_agent.run = AsyncMock(side_effect=Exception("LLM Error"))

        with pytest.raises(Exception) as exc_info:
            await agent.run_skill("Test prompt")

        assert "LLM Error" in str(exc_info.value)

    def test_agent_with_missing_llm_factory(self, sample_config):
        """Test agent creation when LLM factory is not available."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory",
            side_effect=ImportError("LLM factory not available"),
        ):
            with pytest.raises(ImportError):
                BasePydanticAgent(config=sample_config)


class TestBasePydanticAgentIntegration:
    """Integration test cases for complete agent workflows."""

    @pytest.mark.asyncio
    async def test_full_agent_workflow(self, sample_config, mock_llm):
        """Test complete agent workflow from initialization to execution."""
        # Create toolsets
        server = MockMCPServer("integration_server")
        server.add_tool(MockPydanticAITool("integration_tool"))

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            # Initialize agent
            agent = BasePydanticAgent(
                config=sample_config, llm_instance=mock_llm, toolsets=[server]
            )

            # Initialize MCP tools
            await agent.initialize_mcp_tools()

            # Execute skill
            result = await agent.run_skill("Integration test prompt")

        assert agent.agent_name == "TestAgent"
        assert len(agent.toolsets) == 1
        assert len(agent.pydantic_agent.tools) == 1
        assert "Mock response to: Integration test prompt" in result

    @pytest.mark.asyncio
    async def test_agent_with_complex_configuration(self, mock_llm_factory):
        """Test agent with complex configuration settings."""
        config = BasePydanticAgentConfig(
            agent_id="complex_agent_001",
            agent_name="ComplexAgent",
            llm_provider="openai",
            llm_model_name="gpt-4",
            llm_temperature=0.2,
            llm_max_tokens=8192,
            pydantic_ai_system_prompt="You are a complex agent with specific instructions",
            pydantic_ai_retries=3,
            custom_settings={
                "feature_flags": {"experimental": True},
                "performance": {"cache_size": 1000},
            },
        )

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory",
            return_value=mock_llm_factory,
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.Agent",
                MockPydanticAgent,
            ):
                agent = BasePydanticAgent(config=config)

                result = await agent.run_skill("Complex test")

        assert agent.config.custom_settings["feature_flags"]["experimental"] is True
        assert "Mock response to: Complex test" in result


@pytest.mark.parametrize(
    "provider,model",
    [
        ("openai", "gpt-4"),
        ("google", "gemini-pro"),
        ("anthropic", "claude-3"),
        ("custom", "custom-model"),
    ],
)
class TestBasePydanticAgentParametrized:
    """Parametrized test cases for different LLM configurations."""

    def test_agent_with_different_providers(self, provider, model, mock_llm_factory):
        """Test agent initialization with different LLM providers."""
        config = BasePydanticAgentConfig(
            agent_id=f"provider_test_{provider}",
            agent_name="ProviderTest",
            llm_provider=provider,
            llm_model_name=model,
        )

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory",
            return_value=mock_llm_factory,
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.Agent",
                MockPydanticAgent,
            ):
                agent = BasePydanticAgent(config=config)

        assert agent.config.llm_provider == provider
        assert agent.config.llm_model_name == model

        # Verify LLM factory was called with correct config
        expected_call = {"provider": provider, "model_name": model}
        assert expected_call in mock_llm_factory.create_calls
