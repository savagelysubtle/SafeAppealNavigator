"""
Test suite for DatabaseAgent class.

This module contains comprehensive tests for the database agent that handles
document intake, sorting, and Chroma vector database management operations.
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
from ai_research_assistant.agents.specialized_manager_agent.database_agent.agent import (
    DatabaseAgent,
    DatabaseAgentConfig,
)


# Mock classes for testing
class MockLLM:
    """Mock LLM for testing database agent."""

    def __init__(self, provider="mock", model="mock-model"):
        self.provider = provider
        self.model = model


class MockPydanticAgent:
    """Mock PydanticAI Agent for database agent testing."""

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
            result_data = f"Mock database response to: {user_prompt[:50]}..."

        mock_result = Mock()
        mock_result.data = result_data
        return mock_result

    def set_next_result(self, result):
        """Set the next result to be returned by run()."""
        self.run_results.append(result)


@pytest.fixture
def database_agent_config():
    """Fixture providing database agent configuration."""
    return DatabaseAgentConfig()


@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM instance."""
    return MockLLM("database_test_provider", "database_test_model")


@pytest.fixture
def database_agent_factory():
    """Factory fixture for creating test database agents."""

    def _create_database_agent(config=None):
        if config is None:
            config = DatabaseAgentConfig()

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                return DatabaseAgent(config=config)

    return _create_database_agent


@pytest.fixture
def sample_documents():
    """Fixture providing sample documents for testing."""
    return [
        {
            "id": "doc_1",
            "content": "Legal document about workers compensation",
            "metadata": {"type": "legal", "category": "workers_comp"},
        },
        {
            "id": "doc_2",
            "content": "Medical report on workplace injury",
            "metadata": {"type": "medical", "category": "injury_report"},
        },
        {
            "id": "doc_3",
            "content": "Case law precedent for similar cases",
            "metadata": {"type": "legal", "category": "case_law"},
        },
    ]


class TestDatabaseAgentConfig:
    """Test cases for DatabaseAgentConfig class."""

    def test_config_default_values(self):
        """Test that database agent config has correct defaults."""
        config = DatabaseAgentConfig()

        assert config.agent_name == "DatabaseAgent"
        assert config.agent_id == "database_agent_instance_001"
        assert "Database Agent" in config.pydantic_ai_system_prompt
        assert "Chroma vector database" in config.pydantic_ai_system_prompt
        assert "Document intake" in config.pydantic_ai_system_prompt
        assert "Document sorting" in config.pydantic_ai_system_prompt
        assert "Database maintenance" in config.pydantic_ai_system_prompt

    def test_config_inheritance(self):
        """Test that config properly inherits from BasePydanticAgentConfig."""
        config = DatabaseAgentConfig()

        assert isinstance(config, BasePydanticAgentConfig)
        assert hasattr(config, "llm_provider")
        assert hasattr(config, "llm_temperature")
        assert hasattr(config, "custom_settings")

    def test_config_system_prompt_content(self):
        """Test that system prompt contains key database responsibilities."""
        config = DatabaseAgentConfig()

        prompt = config.pydantic_ai_system_prompt
        assert "Database Agent" in prompt
        assert "Chroma vector database" in prompt
        assert "Document intake" in prompt
        assert "Document sorting" in prompt
        assert "Vector operations" in prompt
        assert "Document Agent" in prompt
        assert "file I/O operations" in prompt


class TestDatabaseAgentInitialization:
    """Test cases for DatabaseAgent initialization."""

    def test_database_agent_initialization_with_defaults(self):
        """Test database agent initialization with default configuration."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                database_agent = DatabaseAgent()

        assert database_agent.agent_name == "DatabaseAgent"
        assert isinstance(database_agent.agent_config, DatabaseAgentConfig)

    def test_database_agent_initialization_with_custom_config(
        self, database_agent_config
    ):
        """Test database agent initialization with custom configuration."""
        database_agent_config.agent_name = "CustomDatabaseAgent"
        database_agent_config.agent_id = "custom_db_001"

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                database_agent = DatabaseAgent(config=database_agent_config)

        assert database_agent.agent_name == "CustomDatabaseAgent"
        assert database_agent.agent_config.agent_id == "custom_db_001"

    def test_database_agent_inherits_from_base_agent(self):
        """Test that DatabaseAgent properly inherits from BasePydanticAgent."""
        from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                database_agent = DatabaseAgent()

        assert isinstance(database_agent, BasePydanticAgent)
        assert hasattr(database_agent, "pydantic_agent")

    def test_database_agent_chroma_tools(self, database_agent_factory):
        """Test that database agent has access to toolsets."""
        database_agent = database_agent_factory()

        # Should have toolsets attribute from parent class
        assert hasattr(database_agent, "toolsets")
        assert isinstance(database_agent.toolsets, list)

    def test_database_agent_logging_on_init(self, database_agent_factory, caplog):
        """Test that initialization is logged."""
        with caplog.at_level(logging.INFO):
            database_agent = database_agent_factory()

        assert "DatabaseAgent" in caplog.text
        assert "initialized with Chroma tools" in caplog.text


class TestDatabaseAgentIntakeDocuments:
    """Test cases for intake_documents method."""

    @pytest.mark.asyncio
    async def test_intake_documents_basic(
        self, database_agent_factory, sample_documents
    ):
        """Test basic document intake functionality."""
        database_agent = database_agent_factory()

        result = await database_agent.intake_documents(
            documents=sample_documents, collection_name="test_collection"
        )

        assert result["status"] == "success"
        assert result["collection"] == "test_collection"
        assert result["documents_processed"] == 3
        assert "Successfully added 3 documents" in result["message"]

    @pytest.mark.asyncio
    async def test_intake_documents_collection_exists(
        self, database_agent_factory, sample_documents
    ):
        """Test document intake when collection already exists."""
        database_agent = database_agent_factory()

        # Mock collection exists check
        database_agent.pydantic_agent.set_next_result("Collection exists")
        database_agent.pydantic_agent.set_next_result("Documents added")

        result = await database_agent.intake_documents(
            documents=sample_documents, collection_name="existing_collection"
        )

        assert result["status"] == "success"
        assert result["collection"] == "existing_collection"

    @pytest.mark.asyncio
    async def test_intake_documents_create_collection(
        self, database_agent_factory, sample_documents
    ):
        """Test document intake with collection creation."""
        database_agent = database_agent_factory()

        result = await database_agent.intake_documents(
            documents=sample_documents,
            collection_name="new_collection",
            create_if_not_exists=True,
        )

        assert result["status"] == "success"
        # Should have attempted collection creation and document addition
        assert len(database_agent.pydantic_agent.run_calls) >= 2

    @pytest.mark.asyncio
    async def test_intake_documents_no_create_collection(
        self, database_agent_factory, sample_documents
    ):
        """Test document intake without collection creation."""
        database_agent = database_agent_factory()

        result = await database_agent.intake_documents(
            documents=sample_documents,
            collection_name="missing_collection",
            create_if_not_exists=False,
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_intake_documents_prompt_construction(
        self, database_agent_factory, sample_documents
    ):
        """Test that document intake constructs the prompt correctly."""
        database_agent = database_agent_factory()

        await database_agent.intake_documents(
            documents=sample_documents, collection_name="test_collection"
        )

        # Check collection check prompt
        check_prompt = database_agent.pydantic_agent.run_calls[0][0]
        assert "Check if collection 'test_collection' exists" in check_prompt
        assert "chroma_get_collection_info" in check_prompt

        # Check document addition prompt
        add_prompt = database_agent.pydantic_agent.run_calls[-1][0]
        assert "Add the following 3 documents" in add_prompt
        assert "test_collection" in add_prompt
        assert "chroma_add_documents" in add_prompt

    @pytest.mark.asyncio
    async def test_intake_documents_handles_error(
        self, database_agent_factory, sample_documents
    ):
        """Test document intake error handling."""
        database_agent = database_agent_factory()

        database_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await database_agent.intake_documents(
            documents=sample_documents, collection_name="error_collection"
        )

        assert result["status"] == "error"
        assert "Database error" in result["error"]
        assert result["documents_processed"] == 0

    @pytest.mark.asyncio
    async def test_intake_documents_empty_list(self, database_agent_factory):
        """Test document intake with empty document list."""
        database_agent = database_agent_factory()

        result = await database_agent.intake_documents(
            documents=[], collection_name="empty_collection"
        )

        assert result["status"] == "success"
        assert result["documents_processed"] == 0


class TestDatabaseAgentSortDocuments:
    """Test cases for sort_documents_into_collections method."""

    @pytest.mark.asyncio
    async def test_sort_documents_basic(self, database_agent_factory):
        """Test basic document sorting functionality."""
        database_agent = database_agent_factory()

        sorting_criteria = {
            "legal_docs": {
                "target_collection": "legal_collection",
                "filter_metadata": {"type": "legal"},
            },
            "medical_docs": {
                "target_collection": "medical_collection",
                "filter_metadata": {"type": "medical"},
            },
        }

        result = await database_agent.sort_documents_into_collections(
            source_collection="mixed_collection", sorting_criteria=sorting_criteria
        )

        assert result["status"] == "success"
        assert result["source_collection"] == "mixed_collection"
        assert "legal_collection" in result["sorted_collections"]
        assert "medical_collection" in result["sorted_collections"]

    @pytest.mark.asyncio
    async def test_sort_documents_default_target_collection(
        self, database_agent_factory
    ):
        """Test document sorting with default target collection names."""
        database_agent = database_agent_factory()

        sorting_criteria = {
            "priority": {"filter_metadata": {"priority": "high"}},
        }

        result = await database_agent.sort_documents_into_collections(
            source_collection="source", sorting_criteria=sorting_criteria
        )

        assert result["status"] == "success"
        # Should create default target collection name
        assert "source_priority" in result["sorted_collections"]

    @pytest.mark.asyncio
    async def test_sort_documents_prompt_construction(self, database_agent_factory):
        """Test that document sorting constructs the prompt correctly."""
        database_agent = database_agent_factory()

        sorting_criteria = {
            "legal": {
                "target_collection": "legal_docs",
                "filter_metadata": {"type": "legal"},
            }
        }

        await database_agent.sort_documents_into_collections(
            "source_collection", sorting_criteria
        )

        # Should have multiple calls for querying, creating collections, and moving docs
        assert len(database_agent.pydantic_agent.run_calls) >= 3

        # Check for collection retrieval prompt
        retrieve_prompt = database_agent.pydantic_agent.run_calls[0][0]
        assert (
            "Retrieve all documents from collection 'source_collection'"
            in retrieve_prompt
        )

        # Check for collection creation prompt
        create_prompt = database_agent.pydantic_agent.run_calls[1][0]
        assert "Create collection 'legal_docs'" in create_prompt

    @pytest.mark.asyncio
    async def test_sort_documents_handles_error(self, database_agent_factory):
        """Test document sorting error handling."""
        database_agent = database_agent_factory()

        database_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Sorting error")
        )

        result = await database_agent.sort_documents_into_collections(
            "source_collection", {"test": {"filter_metadata": {}}}
        )

        assert result["status"] == "error"
        assert "Sorting error" in result["error"]
        assert result["source_collection"] == "source_collection"

    @pytest.mark.asyncio
    async def test_sort_documents_multiple_criteria(self, database_agent_factory):
        """Test document sorting with multiple criteria."""
        database_agent = database_agent_factory()

        sorting_criteria = {
            "by_type": {
                "target_collection": "type_collection",
                "filter_metadata": {"type": "legal"},
            },
            "by_priority": {
                "target_collection": "priority_collection",
                "filter_metadata": {"priority": "high"},
            },
            "by_category": {
                "target_collection": "category_collection",
                "filter_metadata": {"category": "workers_comp"},
            },
        }

        result = await database_agent.sort_documents_into_collections(
            "source", sorting_criteria
        )

        assert result["status"] == "success"
        assert len(result["sorted_collections"]) == 3


class TestDatabaseAgentMaintainDatabase:
    """Test cases for maintain_database method."""

    @pytest.mark.asyncio
    async def test_maintain_database_cleanup_empty_collections(
        self, database_agent_factory
    ):
        """Test database maintenance - cleanup empty collections."""
        database_agent = database_agent_factory()

        result = await database_agent.maintain_database("cleanup_empty_collections")

        assert result["status"] == "success"
        assert result["operation"] == "cleanup_empty_collections"
        assert result["result"] == "Cleaned up empty collections"

    @pytest.mark.asyncio
    async def test_maintain_database_optimize_collection(self, database_agent_factory):
        """Test database maintenance - optimize collection."""
        database_agent = database_agent_factory()

        result = await database_agent.maintain_database(
            "optimize_collection", collection_name="test_collection"
        )

        assert result["status"] == "success"
        assert result["operation"] == "optimize_collection"
        assert result["collection"] == "test_collection"

    @pytest.mark.asyncio
    async def test_maintain_database_optimize_without_collection_name(
        self, database_agent_factory
    ):
        """Test database maintenance - optimize without collection name."""
        database_agent = database_agent_factory()

        result = await database_agent.maintain_database("optimize_collection")

        assert result["status"] == "error"
        assert "collection_name required" in result["error"]

    @pytest.mark.asyncio
    async def test_maintain_database_collection_stats(self, database_agent_factory):
        """Test database maintenance - collection statistics."""
        database_agent = database_agent_factory()

        result = await database_agent.maintain_database("collection_stats")

        assert result["status"] == "success"
        assert result["operation"] == "collection_stats"
        assert result["stats"] == "Database statistics generated"

    @pytest.mark.asyncio
    async def test_maintain_database_unknown_operation(self, database_agent_factory):
        """Test database maintenance with unknown operation."""
        database_agent = database_agent_factory()

        result = await database_agent.maintain_database("unknown_operation")

        assert result["status"] == "error"
        assert "Unknown maintenance operation" in result["error"]

    @pytest.mark.asyncio
    async def test_maintain_database_prompt_construction(self, database_agent_factory):
        """Test that database maintenance constructs the prompt correctly."""
        database_agent = database_agent_factory()

        await database_agent.maintain_database(
            "optimize_collection", collection_name="test_collection"
        )

        call_prompt = database_agent.pydantic_agent.run_calls[0][0]
        assert "Optimize collection 'test_collection'" in call_prompt
        assert "HNSW parameters" in call_prompt
        assert "chroma_modify_collection" in call_prompt

    @pytest.mark.asyncio
    async def test_maintain_database_handles_error(self, database_agent_factory):
        """Test database maintenance error handling."""
        database_agent = database_agent_factory()

        database_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Maintenance error")
        )

        result = await database_agent.maintain_database("cleanup_empty_collections")

        assert result["status"] == "error"
        assert "Maintenance error" in result["error"]
        assert result["operation"] == "cleanup_empty_collections"


class TestDatabaseAgentCreateSpecializedCollection:
    """Test cases for create_specialized_collection method."""

    @pytest.mark.asyncio
    async def test_create_specialized_collection_basic(self, database_agent_factory):
        """Test basic specialized collection creation."""
        database_agent = database_agent_factory()

        result = await database_agent.create_specialized_collection(
            collection_name="legal_docs",
            collection_type="legal_documents",
            embedding_function="sentence_transformers",
        )

        assert result["status"] == "success"
        assert result["collection_name"] == "legal_docs"
        assert result["collection_type"] == "legal_documents"
        assert result["embedding_function"] == "sentence_transformers"

    @pytest.mark.asyncio
    async def test_create_specialized_collection_with_metadata(
        self, database_agent_factory
    ):
        """Test specialized collection creation with metadata."""
        database_agent = database_agent_factory()

        metadata = {"domain": "legal", "version": "1.0"}

        result = await database_agent.create_specialized_collection(
            collection_name="legal_v1",
            collection_type="legal",
            embedding_function="custom_legal_embeddings",
            metadata=metadata,
        )

        assert result["status"] == "success"
        assert result["collection_name"] == "legal_v1"

    @pytest.mark.asyncio
    async def test_create_specialized_collection_default_embedding(
        self, database_agent_factory
    ):
        """Test specialized collection creation with default embedding function."""
        database_agent = database_agent_factory()

        result = await database_agent.create_specialized_collection(
            collection_name="default_collection", collection_type="general"
        )

        assert result["status"] == "success"
        assert result["embedding_function"] == "default"

    @pytest.mark.asyncio
    async def test_create_specialized_collection_prompt_construction(
        self, database_agent_factory
    ):
        """Test that specialized collection creation constructs the prompt correctly."""
        database_agent = database_agent_factory()

        metadata = {"purpose": "testing"}

        await database_agent.create_specialized_collection(
            collection_name="test_collection",
            collection_type="test_docs",
            embedding_function="test_embeddings",
            metadata=metadata,
        )

        call_prompt = database_agent.pydantic_agent.run_calls[0][0]
        assert "Create a new collection named 'test_collection'" in call_prompt
        assert "test_docs documents" in call_prompt
        assert "test_embeddings" in call_prompt
        assert "chroma_create_collection" in call_prompt

    @pytest.mark.asyncio
    async def test_create_specialized_collection_handles_error(
        self, database_agent_factory
    ):
        """Test specialized collection creation error handling."""
        database_agent = database_agent_factory()

        database_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Collection creation error")
        )

        result = await database_agent.create_specialized_collection(
            "error_collection", "error_type"
        )

        assert result["status"] == "error"
        assert "Collection creation error" in result["error"]
        assert result["collection_name"] == "error_collection"


@pytest.mark.parametrize(
    "operation",
    ["cleanup_empty_collections", "optimize_collection", "collection_stats"],
)
class TestDatabaseAgentMaintenanceOperations:
    """Parametrized test cases for different maintenance operations."""

    @pytest.mark.asyncio
    async def test_maintenance_operations(self, operation, database_agent_factory):
        """Test various maintenance operations."""
        database_agent = database_agent_factory()

        kwargs = {}
        if operation == "optimize_collection":
            kwargs["collection_name"] = "test_collection"

        result = await database_agent.maintain_database(operation, **kwargs)

        if operation == "optimize_collection":
            assert result["status"] == "success"
        else:
            assert result["status"] == "success"
        assert result["operation"] == operation


@pytest.mark.parametrize(
    "collection_type", ["legal", "medical", "financial", "general", "research"]
)
class TestDatabaseAgentCollectionTypes:
    """Parametrized test cases for different collection types."""

    @pytest.mark.asyncio
    async def test_specialized_collections_with_various_types(
        self, collection_type, database_agent_factory
    ):
        """Test specialized collection creation with various types."""
        database_agent = database_agent_factory()

        result = await database_agent.create_specialized_collection(
            f"{collection_type}_collection", collection_type
        )

        assert result["status"] == "success"
        assert result["collection_type"] == collection_type


class TestDatabaseAgentEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_intake_documents_empty_metadata(self, database_agent_factory):
        """Test document intake with empty metadata."""
        database_agent = database_agent_factory()

        documents = [{"content": "Test content", "metadata": {}}]

        result = await database_agent.intake_documents(documents, "test_collection")

        assert result["status"] == "success"
        assert result["documents_processed"] == 1

    @pytest.mark.asyncio
    async def test_sort_documents_empty_criteria(self, database_agent_factory):
        """Test document sorting with empty criteria."""
        database_agent = database_agent_factory()

        result = await database_agent.sort_documents_into_collections(
            "source_collection", {}
        )

        assert result["status"] == "success"
        assert len(result["sorted_collections"]) == 0

    @pytest.mark.asyncio
    async def test_create_specialized_collection_empty_name(
        self, database_agent_factory
    ):
        """Test specialized collection creation with empty name."""
        database_agent = database_agent_factory()

        result = await database_agent.create_specialized_collection("", "test_type")

        assert result["collection_name"] == ""
        # Should still attempt to process

    @pytest.mark.asyncio
    async def test_intake_very_large_document_list(self, database_agent_factory):
        """Test document intake with very large document list."""
        database_agent = database_agent_factory()

        # Create 1000 documents
        large_doc_list = [
            {"content": f"Document {i}", "metadata": {"doc_id": i}} for i in range(1000)
        ]

        result = await database_agent.intake_documents(
            large_doc_list, "large_collection"
        )

        assert result["status"] == "success"
        assert result["documents_processed"] == 1000


class TestDatabaseAgentIntegration:
    """Integration test cases for complete database agent workflows."""

    @pytest.mark.asyncio
    async def test_full_database_workflow(
        self, database_agent_factory, sample_documents
    ):
        """Test complete database workflow: intake, sort, maintain."""
        database_agent = database_agent_factory()

        # Intake documents
        intake_result = await database_agent.intake_documents(
            sample_documents, "main_collection"
        )
        assert intake_result["status"] == "success"

        # Sort documents
        sorting_criteria = {
            "legal": {
                "target_collection": "legal_docs",
                "filter_metadata": {"type": "legal"},
            }
        }
        sort_result = await database_agent.sort_documents_into_collections(
            "main_collection", sorting_criteria
        )
        assert sort_result["status"] == "success"

        # Maintain database
        maintain_result = await database_agent.maintain_database("collection_stats")
        assert maintain_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_database_agent_with_multiple_collections(
        self, database_agent_factory
    ):
        """Test database agent handling multiple collections."""
        database_agent = database_agent_factory()

        collections = ["legal_docs", "medical_docs", "financial_docs"]
        results = []

        for collection in collections:
            result = await database_agent.create_specialized_collection(
                collection, collection.split("_")[0]
            )
            results.append(result)

        assert len(results) == 3
        for result in results:
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_database_agent_error_recovery(
        self, database_agent_factory, sample_documents
    ):
        """Test that database agent recovers from errors in one operation."""
        database_agent = database_agent_factory()

        # First operation fails
        database_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("First Error")
        )

        result1 = await database_agent.intake_documents(
            sample_documents, "error_collection"
        )
        assert result1["status"] == "error"

        # Reset mock for second operation
        database_agent.pydantic_agent.run = AsyncMock(return_value=Mock(data="Success"))

        result2 = await database_agent.maintain_database("collection_stats")
        assert result2["status"] == "success"
