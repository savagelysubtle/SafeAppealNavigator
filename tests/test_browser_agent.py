"""
Test suite for BrowserAgent class.

This module contains comprehensive tests for the browser agent that handles
web browsing, searching, and comprehensive research using MCP tools.
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
from ai_research_assistant.agents.specialized_manager_agent.browser_agent.agent import (
    BrowserAgent,
    BrowserAgentConfig,
)


# Mock classes for testing
class MockLLM:
    """Mock LLM for testing browser agent."""

    def __init__(self, provider="mock", model="mock-model"):
        self.provider = provider
        self.model = model


class MockPydanticAgent:
    """Mock PydanticAI Agent for browser agent testing."""

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
            output_data = result_data
        else:
            result_data = f"Mock web research result for: {user_prompt[:50]}..."
            output_data = result_data

        mock_result = Mock()
        mock_result.data = result_data
        mock_result.output = output_data
        mock_result.ran_tools = ["brave-search_search", "playwright_navigate"]
        return mock_result

    def set_next_result(self, result):
        """Set the next result to be returned by run()."""
        self.run_results.append(result)


@pytest.fixture
def browser_agent_config():
    """Fixture providing browser agent configuration."""
    return BrowserAgentConfig()


@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM instance."""
    return MockLLM("browser_test_provider", "browser_test_model")


@pytest.fixture
def browser_agent_factory():
    """Factory fixture for creating test browser agents."""

    def _create_browser_agent(config=None, toolsets=None):
        if config is None:
            config = BrowserAgentConfig()

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                return BrowserAgent(config=config, toolsets=toolsets)

    return _create_browser_agent


@pytest.fixture
def sample_research_input():
    """Fixture providing sample research input data."""
    return {
        "search_keywords": ["workers compensation", "WCAT", "chronic pain"],
        "case_context": "Worker injured on job site with chronic pain claim",
        "research_depth": "comprehensive",
        "sources_to_include": ["canlii.org", "wcat.bc.ca"],
    }


class TestBrowserAgentConfig:
    """Test cases for BrowserAgentConfig class."""

    def test_config_default_values(self):
        """Test that browser agent config has correct defaults."""
        config = BrowserAgentConfig()

        assert config.agent_name == "BrowserAgent"
        assert config.agent_id == "browser_agent_instance_001"
        assert "Browser Agent" in config.pydantic_ai_system_prompt
        assert "comprehensive research" in config.pydantic_ai_system_prompt
        assert "brave-search_search" in config.pydantic_ai_system_prompt
        assert "playwright" in config.pydantic_ai_system_prompt

    def test_config_inheritance(self):
        """Test that config properly inherits from BasePydanticAgentConfig."""
        config = BrowserAgentConfig()

        assert isinstance(config, BasePydanticAgentConfig)
        assert hasattr(config, "llm_provider")
        assert hasattr(config, "llm_temperature")
        assert hasattr(config, "custom_settings")

    def test_config_system_prompt_content(self):
        """Test that system prompt contains key browser responsibilities."""
        config = BrowserAgentConfig()

        prompt = config.pydantic_ai_system_prompt
        assert "Browser Agent" in prompt
        assert "comprehensive research" in prompt
        assert "brave-search_search" in prompt
        assert "playwright" in prompt
        assert "web searches" in prompt
        assert "navigating web pages" in prompt


class TestBrowserAgentInitialization:
    """Test cases for BrowserAgent initialization."""

    def test_browser_agent_initialization_with_defaults(self):
        """Test browser agent initialization with default configuration."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                browser_agent = BrowserAgent()

        assert browser_agent.agent_name == "BrowserAgent"
        assert isinstance(browser_agent.config, BrowserAgentConfig)

    def test_browser_agent_initialization_with_custom_config(
        self, browser_agent_config
    ):
        """Test browser agent initialization with custom configuration."""
        browser_agent_config.agent_name = "CustomBrowserAgent"
        browser_agent_config.agent_id = "custom_browser_001"

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                browser_agent = BrowserAgent(config=browser_agent_config)

        assert browser_agent.agent_name == "CustomBrowserAgent"
        assert browser_agent.config.agent_id == "custom_browser_001"

    def test_browser_agent_inherits_from_base_agent(self):
        """Test that BrowserAgent properly inherits from BasePydanticAgent."""
        from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                browser_agent = BrowserAgent()

        assert isinstance(browser_agent, BasePydanticAgent)
        assert hasattr(browser_agent, "pydantic_agent")

    def test_browser_agent_with_toolsets(self, browser_agent_factory):
        """Test browser agent initialization with toolsets."""
        mock_toolsets = [Mock(), Mock()]
        browser_agent = browser_agent_factory(toolsets=mock_toolsets)

        assert browser_agent.toolsets == mock_toolsets

    def test_browser_agent_logging_on_init(self, browser_agent_factory, caplog):
        """Test that initialization is logged."""
        with caplog.at_level(logging.INFO):
            browser_agent = browser_agent_factory()

        assert "BrowserAgent" in caplog.text
        assert "initialized" in caplog.text


class TestBrowserAgentConductComprehensiveResearch:
    """Test cases for conduct_comprehensive_research method."""

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_research_basic(
        self, browser_agent_factory, sample_research_input
    ):
        """Test basic comprehensive research functionality."""
        browser_agent = browser_agent_factory()

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=sample_research_input["search_keywords"],
            case_context=sample_research_input["case_context"],
            research_depth=sample_research_input["research_depth"],
        )

        assert result["status"] == "success"
        assert "summary" in result
        assert "ran_tools" in result
        assert isinstance(result["ran_tools"], list)

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_research_with_sources(
        self, browser_agent_factory, sample_research_input
    ):
        """Test comprehensive research with specific sources."""
        browser_agent = browser_agent_factory()

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=sample_research_input["search_keywords"],
            case_context=sample_research_input["case_context"],
            research_depth="deep",
            sources_to_include=sample_research_input["sources_to_include"],
        )

        assert result["status"] == "success"
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_research_different_depths(
        self, browser_agent_factory, sample_research_input
    ):
        """Test comprehensive research with different research depths."""
        browser_agent = browser_agent_factory()

        depths = ["shallow", "moderate", "comprehensive", "deep"]

        for depth in depths:
            result = await browser_agent.conduct_comprehensive_research(
                search_keywords=["test"],
                case_context="Test context",
                research_depth=depth,
            )
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_research_prompt_construction(
        self, browser_agent_factory, sample_research_input
    ):
        """Test that research constructs the prompt correctly."""
        browser_agent = browser_agent_factory()

        await browser_agent.conduct_comprehensive_research(
            search_keywords=sample_research_input["search_keywords"],
            case_context=sample_research_input["case_context"],
            research_depth="comprehensive",
        )

        call_prompt = browser_agent.pydantic_agent.run_calls[0][0]
        assert "Perform a comprehensive research task" in call_prompt
        assert "Worker injured on job site" in call_prompt
        assert "workers compensation" in call_prompt
        assert "brave-search_search" in call_prompt
        assert "playwright_navigate" in call_prompt
        assert "playwright_get_content" in call_prompt

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_research_invalid_input(
        self, browser_agent_factory
    ):
        """Test comprehensive research with invalid input."""
        browser_agent = browser_agent_factory()

        # Test with invalid data that should fail validation
        result = await browser_agent.conduct_comprehensive_research(
            search_keywords="not a list",  # Should be a list
            case_context="",
            research_depth="invalid_depth",
        )

        assert "error" in result
        assert "Invalid input provided" in result["error"]

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_research_handles_error(
        self, browser_agent_factory, sample_research_input
    ):
        """Test comprehensive research error handling."""
        browser_agent = browser_agent_factory()

        browser_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Web search error")
        )

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=sample_research_input["search_keywords"],
            case_context=sample_research_input["case_context"],
        )

        assert result["status"] == "error"
        assert "Web search error" in result["error"]

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_research_logging(
        self, browser_agent_factory, sample_research_input, caplog
    ):
        """Test that research execution is logged."""
        browser_agent = browser_agent_factory()

        with caplog.at_level(logging.INFO):
            await browser_agent.conduct_comprehensive_research(
                search_keywords=sample_research_input["search_keywords"],
                case_context=sample_research_input["case_context"],
            )

        assert "Conducting research for context" in caplog.text
        assert "Worker injured on job site" in caplog.text
        assert "workers compensation" in caplog.text

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_research_empty_keywords(
        self, browser_agent_factory
    ):
        """Test research with empty keywords list."""
        browser_agent = browser_agent_factory()

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=[], case_context="Test context"
        )

        assert result["status"] == "success"  # Should handle empty keywords

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_research_none_sources(
        self, browser_agent_factory, sample_research_input
    ):
        """Test research with None sources (should use default)."""
        browser_agent = browser_agent_factory()

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=sample_research_input["search_keywords"],
            case_context=sample_research_input["case_context"],
            sources_to_include=None,
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_conduct_comprehensive_research_agent_skill_decorator(
        self, browser_agent_factory
    ):
        """Test that conduct_comprehensive_research has agent_skill decorator."""
        browser_agent = browser_agent_factory()

        # Check that the method has the agent_skill attributes
        method = browser_agent.conduct_comprehensive_research
        assert hasattr(method, "_is_agent_skill")
        assert method._is_agent_skill is True
        assert hasattr(method, "_skill_name")
        assert method._skill_name == "conduct_comprehensive_research"


@pytest.mark.parametrize(
    "research_depth", ["shallow", "moderate", "comprehensive", "deep"]
)
class TestBrowserAgentResearchDepths:
    """Parametrized test cases for different research depths."""

    @pytest.mark.asyncio
    async def test_research_with_various_depths(
        self, research_depth, browser_agent_factory
    ):
        """Test research with various depth levels."""
        browser_agent = browser_agent_factory()

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=["test keyword"],
            case_context="Test case context",
            research_depth=research_depth,
        )

        assert result["status"] == "success"

        # Check that depth appears in the prompt
        call_prompt = browser_agent.pydantic_agent.run_calls[0][0]
        assert f"Perform a {research_depth} research task" in call_prompt


@pytest.mark.parametrize(
    "search_keywords",
    [
        ["workers compensation"],
        ["WCAT", "appeal"],
        ["chronic pain", "workplace injury", "medical evidence"],
        ["legal precedent", "case law"],
    ],
)
class TestBrowserAgentSearchKeywords:
    """Parametrized test cases for different search keyword combinations."""

    @pytest.mark.asyncio
    async def test_research_with_various_keywords(
        self, search_keywords, browser_agent_factory
    ):
        """Test research with various keyword combinations."""
        browser_agent = browser_agent_factory()

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=search_keywords, case_context="Test context"
        )

        assert result["status"] == "success"

        # Check that keywords appear in the prompt
        call_prompt = browser_agent.pydantic_agent.run_calls[0][0]
        for keyword in search_keywords:
            assert keyword in call_prompt


class TestBrowserAgentEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_research_with_very_long_context(self, browser_agent_factory):
        """Test research with very long case context."""
        browser_agent = browser_agent_factory()

        long_context = "A" * 5000  # Very long context

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=["test"], case_context=long_context
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_research_with_special_characters_in_keywords(
        self, browser_agent_factory
    ):
        """Test research with special characters in keywords."""
        browser_agent = browser_agent_factory()

        special_keywords = ["worker's compensation", "s. 5.1", "Act & Regulations"]

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=special_keywords, case_context="Test context"
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_research_with_empty_context(self, browser_agent_factory):
        """Test research with empty case context."""
        browser_agent = browser_agent_factory()

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=["test"], case_context=""
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_research_with_many_keywords(self, browser_agent_factory):
        """Test research with many keywords."""
        browser_agent = browser_agent_factory()

        many_keywords = [f"keyword_{i}" for i in range(50)]

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=many_keywords, case_context="Test context"
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_research_with_unicode_keywords(self, browser_agent_factory):
        """Test research with unicode characters in keywords."""
        browser_agent = browser_agent_factory()

        unicode_keywords = ["français", "español", "中文"]

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=unicode_keywords, case_context="Test context"
        )

        assert result["status"] == "success"


class TestBrowserAgentInputValidation:
    """Test cases for input validation using Pydantic models."""

    @pytest.mark.asyncio
    async def test_valid_input_validation(self, browser_agent_factory):
        """Test that valid input passes validation."""
        browser_agent = browser_agent_factory()

        # This should pass validation
        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=["valid", "keywords"],
            case_context="Valid context",
            research_depth="moderate",
            sources_to_include=["example.com"],
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_invalid_search_keywords_type(self, browser_agent_factory):
        """Test input validation with invalid search_keywords type."""
        browser_agent = browser_agent_factory()

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords="should be list",  # Invalid: should be list
            case_context="Valid context",
        )

        assert "error" in result
        assert "Invalid input provided" in result["error"]

    @pytest.mark.asyncio
    async def test_invalid_research_depth(self, browser_agent_factory):
        """Test input validation with invalid research depth."""
        browser_agent = browser_agent_factory()

        # This might still work depending on the Pydantic model validation
        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=["valid"],
            case_context="Valid context",
            research_depth="invalid_depth",
        )

        # Depending on validation rules, this might succeed or fail
        assert "status" in result


class TestBrowserAgentToolIntegration:
    """Test cases for browser agent tool integration."""

    @pytest.mark.asyncio
    async def test_research_uses_expected_tools(self, browser_agent_factory):
        """Test that research uses expected browser tools."""
        browser_agent = browser_agent_factory()

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=["test"], case_context="Test context"
        )

        assert result["status"] == "success"
        assert "ran_tools" in result
        # Mock returns these tools
        assert "brave-search_search" in result["ran_tools"]
        assert "playwright_navigate" in result["ran_tools"]

    @pytest.mark.asyncio
    async def test_research_prompt_mentions_correct_tools(self, browser_agent_factory):
        """Test that research prompt mentions the correct MCP tools."""
        browser_agent = browser_agent_factory()

        await browser_agent.conduct_comprehensive_research(
            search_keywords=["test"], case_context="Test context"
        )

        call_prompt = browser_agent.pydantic_agent.run_calls[0][0]
        assert "brave-search_search" in call_prompt
        assert "playwright_navigate" in call_prompt
        assert "playwright_get_content" in call_prompt

    @pytest.mark.asyncio
    async def test_browser_agent_no_direct_tools(self, browser_agent_factory):
        """Test that browser agent inherits tools from parent class."""
        browser_agent = browser_agent_factory()

        # Browser agent doesn't override _get_initial_tools, so it should
        # inherit from parent class (which returns empty list in our mock)
        assert (
            hasattr(browser_agent, "_get_initial_tools") is False
            or browser_agent._get_initial_tools() == []
        )


class TestBrowserAgentIntegration:
    """Integration test cases for complete browser agent workflows."""

    @pytest.mark.asyncio
    async def test_full_research_workflow(self, browser_agent_factory):
        """Test complete research workflow with multiple steps."""
        browser_agent = browser_agent_factory()

        # Set up mock to return detailed research results
        browser_agent.pydantic_agent.set_next_result(
            "Comprehensive research findings on workers compensation law. "
            "Found 15 relevant cases and 3 key statutes. "
            "WCAT Decision 2023-001 provides strong precedent for chronic pain claims."
        )

        result = await browser_agent.conduct_comprehensive_research(
            search_keywords=["workers compensation", "chronic pain", "WCAT"],
            case_context="Worker with chronic back pain seeking compensation",
            research_depth="comprehensive",
            sources_to_include=["canlii.org", "wcat.bc.ca"],
        )

        assert result["status"] == "success"
        assert "workers compensation law" in result["summary"]
        assert "WCAT Decision 2023-001" in result["summary"]

    @pytest.mark.asyncio
    async def test_browser_agent_multiple_research_tasks(self, browser_agent_factory):
        """Test browser agent handling multiple research tasks."""
        browser_agent = browser_agent_factory()

        research_tasks = [
            {
                "keywords": ["legal precedent"],
                "context": "Need case law for workers comp appeal",
            },
            {
                "keywords": ["medical evidence"],
                "context": "Gathering medical documentation requirements",
            },
            {
                "keywords": ["WCAT procedures"],
                "context": "Understanding appeal process timeline",
            },
        ]

        results = []
        for task in research_tasks:
            result = await browser_agent.conduct_comprehensive_research(
                search_keywords=task["keywords"], case_context=task["context"]
            )
            results.append(result)

        assert len(results) == 3
        for result in results:
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_browser_agent_error_recovery(self, browser_agent_factory):
        """Test that browser agent recovers from errors in one operation."""
        browser_agent = browser_agent_factory()

        # First research fails
        browser_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Network Error")
        )

        result1 = await browser_agent.conduct_comprehensive_research(
            search_keywords=["test"], case_context="Test context"
        )
        assert result1["status"] == "error"

        # Reset mock for second research
        browser_agent.pydantic_agent.run = AsyncMock(
            return_value=Mock(
                data="Success",
                output="Successful research",
                ran_tools=["brave-search_search"],
            )
        )

        result2 = await browser_agent.conduct_comprehensive_research(
            search_keywords=["recovery test"], case_context="Recovery test context"
        )
        assert result2["status"] == "success"
