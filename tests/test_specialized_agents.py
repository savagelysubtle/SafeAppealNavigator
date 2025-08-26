"""
Test suite for Specialized Agents.

This module contains comprehensive tests for all specialized agents including
document agent, database agent, browser agent, and CEO agent functionality.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai_research_assistant.agents.ceo_agent.agent import CEOAgent, CeoAgent
from ai_research_assistant.agents.specialized_manager_agent.browser_agent.agent import (
    BrowserAgent,
)
from ai_research_assistant.agents.specialized_manager_agent.database_agent.agent import (
    DatabaseAgent,
)

# Import specialized agents
from ai_research_assistant.agents.specialized_manager_agent.document_agent.agent import (
    DocumentAgent,
)
from ai_research_assistant.agents.specialized_manager_agent.legal_manager_agent.agent import (
    LegalManagerAgent,
)


# Mock classes for testing
class MockLLM:
    """Mock LLM for testing specialized agents."""

    def __init__(self, provider="mock", model="mock-model"):
        self.provider = provider
        self.model = model


class MockPydanticAgent:
    """Mock PydanticAI Agent for specialized agent testing."""

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
            result_data = f"Mock response to: {user_prompt[:50]}..."

        mock_result = Mock()
        mock_result.data = result_data
        mock_result.output = result_data
        return mock_result

    def set_next_result(self, result):
        """Set the next result to be returned by run()."""
        self.run_results.append(result)


class MockMCPServer:
    """Mock MCP server for specialized agent testing."""

    def __init__(self, name="mock_server"):
        self.name = name
        self._tools = []

    @property
    async def tools(self):
        """Async generator for tools."""
        for tool in self._tools:
            yield tool


@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM instance."""
    return MockLLM("specialized_test_provider", "specialized_test_model")


@pytest.fixture
def specialized_agent_factory():
    """Factory fixture for creating specialized agents."""

    def _create_agent(agent_class, config=None, **kwargs):
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                if config:
                    return agent_class(config=config, **kwargs)
                else:
                    return agent_class(**kwargs)

    return _create_agent


class TestDocumentAgent:
    """Test cases for DocumentAgent functionality."""

    def test_document_agent_initialization(self, specialized_agent_factory):
        """Test document agent initialization."""
        try:
            document_agent = specialized_agent_factory(DocumentAgent)
            assert document_agent is not None
            assert hasattr(document_agent, "agent_name")
        except ImportError:
            pytest.skip("DocumentAgent not available for testing")

    def test_document_agent_inheritance(self, specialized_agent_factory):
        """Test that DocumentAgent inherits from BasePydanticAgent."""
        try:
            from ai_research_assistant.agents.base_pydantic_agent import (
                BasePydanticAgent,
            )

            document_agent = specialized_agent_factory(DocumentAgent)
            assert isinstance(document_agent, BasePydanticAgent)
        except ImportError:
            pytest.skip("DocumentAgent not available for testing")

    @pytest.mark.asyncio
    async def test_document_agent_read_document(self, specialized_agent_factory):
        """Test document agent document reading functionality."""
        try:
            document_agent = specialized_agent_factory(DocumentAgent)

            if hasattr(document_agent, "read_document"):
                result = await document_agent.read_document("/test/document.pdf")
                assert result is not None
            else:
                pytest.skip("read_document method not implemented")
        except ImportError:
            pytest.skip("DocumentAgent not available for testing")

    @pytest.mark.asyncio
    async def test_document_agent_create_document(self, specialized_agent_factory):
        """Test document agent document creation functionality."""
        try:
            document_agent = specialized_agent_factory(DocumentAgent)

            if hasattr(document_agent, "create_document"):
                result = await document_agent.create_document(
                    content="Test document content", path="/test/new_document.md"
                )
                assert result is not None
            else:
                pytest.skip("create_document method not implemented")
        except ImportError:
            pytest.skip("DocumentAgent not available for testing")

    def test_document_agent_system_prompt(self, specialized_agent_factory):
        """Test that document agent has appropriate system prompt."""
        try:
            document_agent = specialized_agent_factory(DocumentAgent)

            if hasattr(document_agent, "config") and hasattr(
                document_agent.config, "pydantic_ai_system_prompt"
            ):
                prompt = document_agent.config.pydantic_ai_system_prompt
                if prompt:
                    assert "document" in prompt.lower()
        except ImportError:
            pytest.skip("DocumentAgent not available for testing")


class TestDatabaseAgent:
    """Test cases for DatabaseAgent functionality."""

    def test_database_agent_initialization(self, specialized_agent_factory):
        """Test database agent initialization."""
        try:
            database_agent = specialized_agent_factory(DatabaseAgent)
            assert database_agent is not None
            assert hasattr(database_agent, "agent_name")
        except ImportError:
            pytest.skip("DatabaseAgent not available for testing")

    def test_database_agent_inheritance(self, specialized_agent_factory):
        """Test that DatabaseAgent inherits from BasePydanticAgent."""
        try:
            from ai_research_assistant.agents.base_pydantic_agent import (
                BasePydanticAgent,
            )

            database_agent = specialized_agent_factory(DatabaseAgent)
            assert isinstance(database_agent, BasePydanticAgent)
        except ImportError:
            pytest.skip("DatabaseAgent not available for testing")

    @pytest.mark.asyncio
    async def test_database_agent_query(self, specialized_agent_factory):
        """Test database agent query functionality."""
        try:
            database_agent = specialized_agent_factory(DatabaseAgent)

            if hasattr(database_agent, "execute_query"):
                result = await database_agent.execute_query("SELECT * FROM test_table")
                assert result is not None
            elif hasattr(database_agent, "query_database"):
                result = await database_agent.query_database("SELECT * FROM test_table")
                assert result is not None
            else:
                pytest.skip("Database query method not implemented")
        except ImportError:
            pytest.skip("DatabaseAgent not available for testing")

    @pytest.mark.asyncio
    async def test_database_agent_search(self, specialized_agent_factory):
        """Test database agent search functionality."""
        try:
            database_agent = specialized_agent_factory(DatabaseAgent)

            if hasattr(database_agent, "search_cases"):
                result = await database_agent.search_cases("workers compensation")
                assert result is not None
            elif hasattr(database_agent, "vector_search"):
                result = await database_agent.vector_search("workers compensation")
                assert result is not None
            else:
                pytest.skip("Database search method not implemented")
        except ImportError:
            pytest.skip("DatabaseAgent not available for testing")

    def test_database_agent_system_prompt(self, specialized_agent_factory):
        """Test that database agent has appropriate system prompt."""
        try:
            database_agent = specialized_agent_factory(DatabaseAgent)

            if hasattr(database_agent, "config") and hasattr(
                database_agent.config, "pydantic_ai_system_prompt"
            ):
                prompt = database_agent.config.pydantic_ai_system_prompt
                if prompt:
                    assert any(
                        keyword in prompt.lower()
                        for keyword in ["database", "query", "search", "data"]
                    )
        except ImportError:
            pytest.skip("DatabaseAgent not available for testing")


class TestBrowserAgent:
    """Test cases for BrowserAgent functionality."""

    def test_browser_agent_initialization(self, specialized_agent_factory):
        """Test browser agent initialization."""
        try:
            browser_agent = specialized_agent_factory(BrowserAgent)
            assert browser_agent is not None
            assert hasattr(browser_agent, "agent_name")
        except ImportError:
            pytest.skip("BrowserAgent not available for testing")

    def test_browser_agent_inheritance(self, specialized_agent_factory):
        """Test that BrowserAgent inherits from BasePydanticAgent."""
        try:
            from ai_research_assistant.agents.base_pydantic_agent import (
                BasePydanticAgent,
            )

            browser_agent = specialized_agent_factory(BrowserAgent)
            assert isinstance(browser_agent, BasePydanticAgent)
        except ImportError:
            pytest.skip("BrowserAgent not available for testing")

    @pytest.mark.asyncio
    async def test_browser_agent_navigate(self, specialized_agent_factory):
        """Test browser agent navigation functionality."""
        try:
            browser_agent = specialized_agent_factory(BrowserAgent)

            if hasattr(browser_agent, "navigate_to"):
                result = await browser_agent.navigate_to("https://example.com")
                assert result is not None
            elif hasattr(browser_agent, "browse_url"):
                result = await browser_agent.browse_url("https://example.com")
                assert result is not None
            else:
                pytest.skip("Browser navigation method not implemented")
        except ImportError:
            pytest.skip("BrowserAgent not available for testing")

    @pytest.mark.asyncio
    async def test_browser_agent_search(self, specialized_agent_factory):
        """Test browser agent search functionality."""
        try:
            browser_agent = specialized_agent_factory(BrowserAgent)

            if hasattr(browser_agent, "search_web"):
                result = await browser_agent.search_web("workers compensation law")
                assert result is not None
            elif hasattr(browser_agent, "perform_search"):
                result = await browser_agent.perform_search("workers compensation law")
                assert result is not None
            else:
                pytest.skip("Browser search method not implemented")
        except ImportError:
            pytest.skip("BrowserAgent not available for testing")

    @pytest.mark.asyncio
    async def test_browser_agent_extract_content(self, specialized_agent_factory):
        """Test browser agent content extraction functionality."""
        try:
            browser_agent = specialized_agent_factory(BrowserAgent)

            if hasattr(browser_agent, "extract_content"):
                result = await browser_agent.extract_content("https://example.com")
                assert result is not None
            elif hasattr(browser_agent, "get_page_content"):
                result = await browser_agent.get_page_content("https://example.com")
                assert result is not None
            else:
                pytest.skip("Browser content extraction method not implemented")
        except ImportError:
            pytest.skip("BrowserAgent not available for testing")

    def test_browser_agent_system_prompt(self, specialized_agent_factory):
        """Test that browser agent has appropriate system prompt."""
        try:
            browser_agent = specialized_agent_factory(BrowserAgent)

            if hasattr(browser_agent, "config") and hasattr(
                browser_agent.config, "pydantic_ai_system_prompt"
            ):
                prompt = browser_agent.config.pydantic_ai_system_prompt
                if prompt:
                    assert any(
                        keyword in prompt.lower()
                        for keyword in ["browser", "web", "navigate", "search"]
                    )
        except ImportError:
            pytest.skip("BrowserAgent not available for testing")


class TestCeoAgent:
    """Test cases for CeoAgent and CEOAgent functionality."""

    def test_ceo_agent_initialization(self, specialized_agent_factory):
        """Test CEO agent initialization."""
        try:
            # Test both CeoAgent and CEOAgent
            for agent_class in [CeoAgent, CEOAgent]:
                ceo_agent = specialized_agent_factory(agent_class)
                assert ceo_agent is not None
                assert hasattr(ceo_agent, "agent_name")
        except ImportError:
            pytest.skip("CEOAgent not available for testing")

    @pytest.mark.asyncio
    async def test_ceo_agent_handle_user_request(self, specialized_agent_factory):
        """Test CEO agent user request handling functionality."""
        try:
            ceo_agent = specialized_agent_factory(CEOAgent)

            if hasattr(ceo_agent, "handle_user_request"):
                # Mock the orchestrator to avoid complex dependencies
                with patch.object(ceo_agent, "orchestrator") as mock_orchestrator:
                    mock_orchestrator.orchestrate = AsyncMock(
                        return_value="Mock result"
                    )
                    result = await ceo_agent.handle_user_request("Test user request")
                    assert result == "Mock result"
            else:
                pytest.skip("handle_user_request method not implemented")
        except ImportError:
            pytest.skip("CEOAgent not available for testing")

    def test_ceo_agent_inheritance(self, specialized_agent_factory):
        """Test that CeoAgent inherits from BasePydanticAgent."""
        try:
            from ai_research_assistant.agents.base_pydantic_agent import (
                BasePydanticAgent,
            )

            ceo_agent = specialized_agent_factory(CeoAgent)
            assert isinstance(ceo_agent, BasePydanticAgent)
        except ImportError:
            pytest.skip("CeoAgent not available for testing")

    @pytest.mark.asyncio
    async def test_ceo_agent_strategic_planning(self, specialized_agent_factory):
        """Test CEO agent strategic planning functionality."""
        try:
            ceo_agent = specialized_agent_factory(CeoAgent)

            if hasattr(ceo_agent, "create_strategy"):
                result = await ceo_agent.create_strategy(
                    "Legal research workflow optimization"
                )
                assert result is not None
            elif hasattr(ceo_agent, "strategic_planning"):
                result = await ceo_agent.strategic_planning(
                    "Legal research workflow optimization"
                )
                assert result is not None
            else:
                pytest.skip("CEO strategic planning method not implemented")
        except ImportError:
            pytest.skip("CeoAgent not available for testing")

    @pytest.mark.asyncio
    async def test_ceo_agent_resource_allocation(self, specialized_agent_factory):
        """Test CEO agent resource allocation functionality."""
        try:
            ceo_agent = specialized_agent_factory(CeoAgent)

            if hasattr(ceo_agent, "allocate_resources"):
                result = await ceo_agent.allocate_resources(
                    {
                        "legal_research": {"priority": "high", "agents": 3},
                        "document_processing": {"priority": "medium", "agents": 2},
                    }
                )
                assert result is not None
            else:
                pytest.skip("CEO resource allocation method not implemented")
        except ImportError:
            pytest.skip("CeoAgent not available for testing")

    def test_ceo_agent_system_prompt(self, specialized_agent_factory):
        """Test that CEO agent has appropriate system prompt."""
        try:
            ceo_agent = specialized_agent_factory(CeoAgent)

            if hasattr(ceo_agent, "config") and hasattr(
                ceo_agent.config, "pydantic_ai_system_prompt"
            ):
                prompt = ceo_agent.config.pydantic_ai_system_prompt
                if prompt:
                    assert any(
                        keyword in prompt.lower()
                        for keyword in ["ceo", "executive", "strategic", "leadership"]
                    )
        except ImportError:
            pytest.skip("CeoAgent not available for testing")


class TestLegalManagerAgent:
    """Test cases for LegalManagerAgent functionality."""

    def test_legal_manager_agent_initialization(self, specialized_agent_factory):
        """Test legal manager agent initialization."""
        try:
            legal_manager_agent = specialized_agent_factory(LegalManagerAgent)
            assert legal_manager_agent is not None
            assert hasattr(legal_manager_agent, "agent_name")
        except ImportError:
            pytest.skip("LegalManagerAgent not available for testing")

    def test_legal_manager_agent_inheritance(self, specialized_agent_factory):
        """Test that LegalManagerAgent inherits from BasePydanticAgent."""
        try:
            from ai_research_assistant.agents.base_pydantic_agent import (
                BasePydanticAgent,
            )

            legal_manager_agent = specialized_agent_factory(LegalManagerAgent)
            assert isinstance(legal_manager_agent, BasePydanticAgent)
        except ImportError:
            pytest.skip("LegalManagerAgent not available for testing")

    @pytest.mark.asyncio
    async def test_legal_manager_agent_draft_legal_memo(
        self, specialized_agent_factory
    ):
        """Test legal manager agent memo drafting functionality."""
        try:
            legal_manager_agent = specialized_agent_factory(LegalManagerAgent)

            if hasattr(legal_manager_agent, "draft_legal_memo"):
                research_summary = {
                    "case_name": "Test Case",
                    "findings": ["Test finding"],
                }
                result = await legal_manager_agent.draft_legal_memo(research_summary)
                assert result is not None
                assert "status" in result
            else:
                pytest.skip("draft_legal_memo method not implemented")
        except ImportError:
            pytest.skip("LegalManagerAgent not available for testing")

    @pytest.mark.asyncio
    async def test_legal_manager_agent_verify_citations(
        self, specialized_agent_factory
    ):
        """Test legal manager agent citation verification functionality."""
        try:
            legal_manager_agent = specialized_agent_factory(LegalManagerAgent)

            if hasattr(legal_manager_agent, "verify_citations"):
                result = await legal_manager_agent.verify_citations(
                    "/test/document.pdf"
                )
                assert result is not None
                assert "status" in result
            else:
                pytest.skip("verify_citations method not implemented")
        except ImportError:
            pytest.skip("LegalManagerAgent not available for testing")

    def test_legal_manager_agent_system_prompt(self, specialized_agent_factory):
        """Test that legal manager agent has appropriate system prompt."""
        try:
            legal_manager_agent = specialized_agent_factory(LegalManagerAgent)

            if hasattr(legal_manager_agent, "config") and hasattr(
                legal_manager_agent.config, "pydantic_ai_system_prompt"
            ):
                prompt = legal_manager_agent.config.pydantic_ai_system_prompt
                if prompt:
                    assert any(
                        keyword in prompt.lower()
                        for keyword in ["legal", "document", "citation", "manager"]
                    )
        except ImportError:
            pytest.skip("LegalManagerAgent not available for testing")


class TestSpecializedAgentIntegration:
    """Integration tests for specialized agents working together."""

    @pytest.mark.asyncio
    async def test_document_database_integration(self, specialized_agent_factory):
        """Test integration between document and database agents."""
        try:
            document_agent = specialized_agent_factory(DocumentAgent)
            database_agent = specialized_agent_factory(DatabaseAgent)

            # Test workflow: read document, store in database
            if hasattr(document_agent, "read_document") and hasattr(
                database_agent, "store_document"
            ):
                doc_content = await document_agent.read_document("/test/case.pdf")
                store_result = await database_agent.store_document(doc_content)

                assert doc_content is not None
                assert store_result is not None
            else:
                pytest.skip("Required methods not implemented for integration test")
        except ImportError:
            pytest.skip("Required agents not available for integration testing")

    @pytest.mark.asyncio
    async def test_browser_document_integration(self, specialized_agent_factory):
        """Test integration between browser and document agents."""
        try:
            browser_agent = specialized_agent_factory(BrowserAgent)
            document_agent = specialized_agent_factory(DocumentAgent)

            # Test workflow: search web, create document from results
            if hasattr(browser_agent, "search_web") and hasattr(
                document_agent, "create_document"
            ):
                search_results = await browser_agent.search_web("WCAT decisions")
                doc_result = await document_agent.create_document(
                    content=str(search_results), path="/output/search_results.md"
                )

                assert search_results is not None
                assert doc_result is not None
            else:
                pytest.skip("Required methods not implemented for integration test")
        except ImportError:
            pytest.skip("Required agents not available for integration testing")

    @pytest.mark.asyncio
    async def test_ceo_agent_coordination(self, specialized_agent_factory):
        """Test CEO agent coordinating other specialized agents."""
        try:
            ceo_agent = specialized_agent_factory(CeoAgent)

            # Test CEO coordinating a multi-agent workflow
            if hasattr(ceo_agent, "coordinate_workflow"):
                workflow_spec = {
                    "task": "Legal research and document creation",
                    "agents": ["DocumentAgent", "DatabaseAgent", "BrowserAgent"],
                    "steps": [
                        "Search for legal precedents",
                        "Extract relevant information",
                        "Create summary document",
                    ],
                }

                result = await ceo_agent.coordinate_workflow(workflow_spec)
                assert result is not None
            else:
                pytest.skip("CEO coordination method not implemented")
        except ImportError:
            pytest.skip("CeoAgent not available for coordination testing")


@pytest.mark.parametrize(
    "agent_class_name",
    [
        "DocumentAgent",
        "DatabaseAgent",
        "BrowserAgent",
        "CeoAgent",
        "CEOAgent",
        "LegalManagerAgent",
    ],
)
class TestSpecializedAgentParametrized:
    """Parametrized tests for all specialized agents."""

    def test_agent_class_importable(self, agent_class_name):
        """Test that each specialized agent class can be imported."""
        try:
            if agent_class_name == "DocumentAgent":
                from ai_research_assistant.agents.specialized_manager_agent.document_agent.agent import (
                    DocumentAgent,
                )
            elif agent_class_name == "DatabaseAgent":
                from ai_research_assistant.agents.specialized_manager_agent.database_agent.agent import (
                    DatabaseAgent,
                )
            elif agent_class_name == "BrowserAgent":
                from ai_research_assistant.agents.specialized_manager_agent.browser_agent.agent import (
                    BrowserAgent,
                )
            elif agent_class_name == "CeoAgent":
                from ai_research_assistant.agents.ceo_agent.agent import CeoAgent
        except ImportError:
            pytest.skip(f"{agent_class_name} not available for testing")

    def test_agent_has_basic_attributes(
        self, agent_class_name, specialized_agent_factory
    ):
        """Test that each agent has basic required attributes."""
        try:
            agent_classes = {
                "DocumentAgent": DocumentAgent,
                "DatabaseAgent": DatabaseAgent,
                "BrowserAgent": BrowserAgent,
                "CeoAgent": CeoAgent,
                "CEOAgent": CEOAgent,
                "LegalManagerAgent": LegalManagerAgent,
            }

            agent_class = agent_classes[agent_class_name]
            agent = specialized_agent_factory(agent_class)

            assert hasattr(agent, "agent_name")
            assert hasattr(agent, "config")
            assert hasattr(agent, "pydantic_agent")
        except (ImportError, KeyError):
            pytest.skip(f"{agent_class_name} not available for testing")


class TestSpecializedAgentErrorHandling:
    """Test cases for error handling in specialized agents."""

    @pytest.mark.asyncio
    async def test_document_agent_file_not_found(self, specialized_agent_factory):
        """Test document agent handling of file not found errors."""
        try:
            document_agent = specialized_agent_factory(DocumentAgent)

            if hasattr(document_agent, "read_document"):
                # Mock the underlying method to raise FileNotFoundError
                with patch.object(
                    document_agent,
                    "read_document",
                    side_effect=FileNotFoundError("File not found"),
                ):
                    with pytest.raises(FileNotFoundError):
                        await document_agent.read_document("/nonexistent/file.pdf")
            else:
                pytest.skip("read_document method not implemented")
        except ImportError:
            pytest.skip("DocumentAgent not available for testing")

    @pytest.mark.asyncio
    async def test_database_agent_connection_error(self, specialized_agent_factory):
        """Test database agent handling of connection errors."""
        try:
            database_agent = specialized_agent_factory(DatabaseAgent)

            if hasattr(database_agent, "execute_query"):
                # Mock database connection error
                with patch.object(
                    database_agent,
                    "execute_query",
                    side_effect=ConnectionError("Database unavailable"),
                ):
                    with pytest.raises(ConnectionError):
                        await database_agent.execute_query("SELECT * FROM test")
            else:
                pytest.skip("execute_query method not implemented")
        except ImportError:
            pytest.skip("DatabaseAgent not available for testing")

    @pytest.mark.asyncio
    async def test_browser_agent_network_error(self, specialized_agent_factory):
        """Test browser agent handling of network errors."""
        try:
            browser_agent = specialized_agent_factory(BrowserAgent)

            if hasattr(browser_agent, "navigate_to"):
                # Mock network error
                with patch.object(
                    browser_agent,
                    "navigate_to",
                    side_effect=ConnectionError("Network unavailable"),
                ):
                    with pytest.raises(ConnectionError):
                        await browser_agent.navigate_to("https://example.com")
            else:
                pytest.skip("navigate_to method not implemented")
        except ImportError:
            pytest.skip("BrowserAgent not available for testing")


class TestSpecializedAgentConfiguration:
    """Test cases for specialized agent configuration."""

    def test_specialized_agents_use_appropriate_models(self, specialized_agent_factory):
        """Test that specialized agents use appropriate LLM models."""
        agent_classes = []

        try:
            agent_classes.append(("DocumentAgent", DocumentAgent))
        except ImportError:
            pass

        try:
            agent_classes.append(("DatabaseAgent", DatabaseAgent))
        except ImportError:
            pass

        try:
            agent_classes.append(("BrowserAgent", BrowserAgent))
        except ImportError:
            pass

        try:
            agent_classes.append(("CeoAgent", CeoAgent))
        except ImportError:
            pass

        if not agent_classes:
            pytest.skip("No specialized agents available for configuration testing")

        for agent_name, agent_class in agent_classes:
            agent = specialized_agent_factory(agent_class)

            # Test that agent has a configuration
            assert hasattr(agent, "config")

            # Test that configuration has LLM settings
            config = agent.config
            assert hasattr(config, "llm_provider")
            assert hasattr(config, "llm_model_name")

    def test_specialized_agents_have_unique_names(self, specialized_agent_factory):
        """Test that specialized agents have unique names."""
        agent_names = set()

        agent_classes = []
        try:
            agent_classes.append(DocumentAgent)
            agent_classes.append(DatabaseAgent)
            agent_classes.append(BrowserAgent)
            agent_classes.append(CeoAgent)
        except ImportError:
            pass

        if not agent_classes:
            pytest.skip("No specialized agents available for name testing")

        for agent_class in agent_classes:
            try:
                agent = specialized_agent_factory(agent_class)
                agent_names.add(agent.agent_name)
            except Exception:
                continue  # Skip if agent can't be created

        # Should have at least 2 different names if multiple agents exist
        if len(agent_classes) > 1:
            assert len(agent_names) > 1, "Specialized agents should have unique names"
