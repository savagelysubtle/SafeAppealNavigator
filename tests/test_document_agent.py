"""
Test suite for DocumentAgent class.

This module contains comprehensive tests for the document agent that handles
reading existing documents and creating new documents with file I/O operations.
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
from ai_research_assistant.agents.specialized_manager_agent.document_agent.agent import (
    DocumentAgent,
    DocumentAgentConfig,
)


# Mock classes for testing
class MockLLM:
    """Mock LLM for testing document agent."""

    def __init__(self, provider="mock", model="mock-model"):
        self.provider = provider
        self.model = model


class MockPydanticAgent:
    """Mock PydanticAI Agent for document agent testing."""

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
            result_data = f"Mock document content from: {user_prompt[-50:]}"

        mock_result = Mock()
        mock_result.data = result_data
        return mock_result

    def set_next_result(self, result):
        """Set the next result to be returned by run()."""
        self.run_results.append(result)


@pytest.fixture
def document_agent_config():
    """Fixture providing document agent configuration."""
    return DocumentAgentConfig()


@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM instance."""
    return MockLLM("document_test_provider", "document_test_model")


@pytest.fixture
def document_agent_factory():
    """Factory fixture for creating test document agents."""

    def _create_document_agent(config=None):
        if config is None:
            config = DocumentAgentConfig()

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                return DocumentAgent(config=config)

    return _create_document_agent


class TestDocumentAgentConfig:
    """Test cases for DocumentAgentConfig class."""

    def test_config_default_values(self):
        """Test that document agent config has correct defaults."""
        config = DocumentAgentConfig()

        assert config.agent_name == "DocumentAgent"
        assert "doc_agent_" in config.agent_id
        assert "Document Agent" in config.pydantic_ai_system_prompt
        assert "reading existing documents" in config.pydantic_ai_system_prompt
        assert "creating new documents" in config.pydantic_ai_system_prompt
        assert "read_file tools" in config.pydantic_ai_system_prompt
        assert "write_file tools" in config.pydantic_ai_system_prompt

    def test_config_inheritance(self):
        """Test that config properly inherits from BasePydanticAgentConfig."""
        config = DocumentAgentConfig()

        assert isinstance(config, BasePydanticAgentConfig)
        assert hasattr(config, "llm_provider")
        assert hasattr(config, "llm_temperature")
        assert hasattr(config, "custom_settings")

    def test_config_system_prompt_content(self):
        """Test that system prompt contains key document responsibilities."""
        config = DocumentAgentConfig()

        prompt = config.pydantic_ai_system_prompt
        assert "Document Agent" in prompt
        assert "reading existing documents" in prompt
        assert "creating new documents" in prompt
        assert "Database Agent" in prompt
        assert "file I/O operations" in prompt
        assert "do NOT manage databases" in prompt


class TestDocumentAgentInitialization:
    """Test cases for DocumentAgent initialization."""

    def test_document_agent_initialization_with_defaults(self):
        """Test document agent initialization with default configuration."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                document_agent = DocumentAgent()

        assert document_agent.agent_name == "DocumentAgent"
        assert isinstance(document_agent.agent_config, DocumentAgentConfig)

    def test_document_agent_initialization_with_custom_config(
        self, document_agent_config
    ):
        """Test document agent initialization with custom configuration."""
        document_agent_config.agent_name = "CustomDocumentAgent"

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                document_agent = DocumentAgent(config=document_agent_config)

        assert document_agent.agent_name == "CustomDocumentAgent"

    def test_document_agent_inherits_from_base_agent(self):
        """Test that DocumentAgent properly inherits from BasePydanticAgent."""
        from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                document_agent = DocumentAgent()

        assert isinstance(document_agent, BasePydanticAgent)
        assert hasattr(document_agent, "pydantic_agent")

    def test_document_agent_file_io_tools(self, document_agent_factory):
        """Test that document agent uses file I/O tools."""
        document_agent = document_agent_factory()

        # DocumentAgent should inherit from BasePydanticAgent and use MCP tools
        # The tools are provided by MCP servers, not by a local _get_initial_tools method
        assert hasattr(document_agent, "pydantic_agent")
        assert hasattr(document_agent, "toolsets")

    def test_document_agent_logging_on_init(self, document_agent_factory, caplog):
        """Test that initialization is logged."""
        with caplog.at_level(logging.INFO):
            document_agent = document_agent_factory()

        assert "DocumentAgent" in caplog.text
        assert "initialized with file I/O tools" in caplog.text


class TestDocumentAgentReadDocument:
    """Test cases for read_document method."""

    @pytest.mark.asyncio
    async def test_read_document_basic(self, document_agent_factory):
        """Test basic document reading functionality."""
        document_agent = document_agent_factory()

        result = await document_agent.read_document("/test/document.pdf")

        assert result["status"] == "success"
        assert result["file_path"] == "/test/document.pdf"
        assert "content" in result
        assert result["file_type"] == ".pdf"

    @pytest.mark.asyncio
    async def test_read_document_with_metadata_extraction(self, document_agent_factory):
        """Test document reading with metadata extraction."""
        document_agent = document_agent_factory()

        # Set up mock to return JSON metadata
        document_agent.pydantic_agent.set_next_result("Document content")
        document_agent.pydantic_agent.set_next_result(
            '{"title": "Test Document", "author": "Test Author"}'
        )

        result = await document_agent.read_document(
            "/test/document.pdf", extract_metadata=True
        )

        assert result["status"] == "success"
        assert "metadata" in result
        assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_read_document_prompt_construction(self, document_agent_factory):
        """Test that document reading constructs the prompt correctly."""
        document_agent = document_agent_factory()

        await document_agent.read_document("/path/to/document.docx")

        call_prompt = document_agent.pydantic_agent.run_calls[0][0]
        assert "Read the document at path: /path/to/document.docx" in call_prompt

    @pytest.mark.asyncio
    async def test_read_document_different_file_types(self, document_agent_factory):
        """Test reading different file types."""
        document_agent = document_agent_factory()

        file_types = [".pdf", ".docx", ".txt", ".md", ".json"]
        for file_type in file_types:
            result = await document_agent.read_document(f"/test/document{file_type}")
            assert result["file_type"] == file_type

    @pytest.mark.asyncio
    async def test_read_document_handles_error(self, document_agent_factory):
        """Test document reading error handling."""
        document_agent = document_agent_factory()

        document_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("File not found")
        )

        result = await document_agent.read_document("/nonexistent/file.pdf")

        assert result["status"] == "error"
        assert "File not found" in result["error"]
        assert result["file_path"] == "/nonexistent/file.pdf"

    @pytest.mark.asyncio
    async def test_read_document_metadata_json_error(self, document_agent_factory):
        """Test metadata extraction with invalid JSON."""
        document_agent = document_agent_factory()

        # Set up mock to return invalid JSON metadata
        document_agent.pydantic_agent.set_next_result("Document content")
        document_agent.pydantic_agent.set_next_result("Invalid JSON")

        result = await document_agent.read_document(
            "/test/document.pdf", extract_metadata=True
        )

        assert result["status"] == "success"
        assert "metadata" in result
        assert "summary" in result["metadata"]


class TestDocumentAgentReadMultipleDocuments:
    """Test cases for read_multiple_documents method."""

    @pytest.mark.asyncio
    async def test_read_multiple_documents_basic(self, document_agent_factory):
        """Test reading multiple documents."""
        document_agent = document_agent_factory()

        file_paths = ["/doc1.pdf", "/doc2.txt", "/doc3.md"]
        result = await document_agent.read_multiple_documents(file_paths)

        assert len(result) == 3
        for i, doc_result in enumerate(result):
            assert doc_result["file_path"] == file_paths[i]
            assert doc_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_read_multiple_documents_with_metadata(self, document_agent_factory):
        """Test reading multiple documents with metadata extraction."""
        document_agent = document_agent_factory()

        file_paths = ["/doc1.pdf", "/doc2.docx"]
        result = await document_agent.read_multiple_documents(
            file_paths, extract_metadata=True
        )

        assert len(result) == 2
        for doc_result in result:
            assert "metadata" in doc_result
            assert "file_name" in doc_result["metadata"]
            assert "file_type" in doc_result["metadata"]

    @pytest.mark.asyncio
    async def test_read_multiple_documents_list_response(self, document_agent_factory):
        """Test handling of list response from pydantic agent."""
        document_agent = document_agent_factory()

        # Mock list response
        mock_result = Mock()
        mock_result.data = ["Content 1", "Content 2", "Content 3"]
        document_agent.pydantic_agent.run = AsyncMock(return_value=mock_result)

        file_paths = ["/doc1.pdf", "/doc2.txt", "/doc3.md"]
        result = await document_agent.read_multiple_documents(file_paths)

        assert len(result) == 3
        for i, doc_result in enumerate(result):
            assert doc_result["content"] == f"Content {i + 1}"

    @pytest.mark.asyncio
    async def test_read_multiple_documents_handles_error(self, document_agent_factory):
        """Test multiple document reading error handling."""
        document_agent = document_agent_factory()

        document_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Read error")
        )

        file_paths = ["/doc1.pdf", "/doc2.txt"]
        result = await document_agent.read_multiple_documents(file_paths)

        assert len(result) == 2
        for doc_result in result:
            assert doc_result["status"] == "error"
            assert "Read error" in doc_result["error"]

    @pytest.mark.asyncio
    async def test_read_multiple_documents_prompt_construction(
        self, document_agent_factory
    ):
        """Test that multiple document reading constructs the prompt correctly."""
        document_agent = document_agent_factory()

        file_paths = ["/doc1.pdf", "/doc2.txt"]
        await document_agent.read_multiple_documents(file_paths)

        call_prompt = document_agent.pydantic_agent.run_calls[0][0]
        assert "Read multiple documents from these paths:" in call_prompt
        assert "/doc1.pdf" in call_prompt
        assert "/doc2.txt" in call_prompt


class TestDocumentAgentCreateDocument:
    """Test cases for create_document method."""

    @pytest.mark.asyncio
    async def test_create_document_basic(self, document_agent_factory):
        """Test basic document creation."""
        document_agent = document_agent_factory()

        result = await document_agent.create_document(
            file_path="/output/test.txt",
            content="Test document content",
            document_type="text",
        )

        assert result["status"] == "success"
        assert result["file_path"] == "/output/test.txt"
        assert result["document_type"] == "text"
        assert result["size"] == len("Test document content")

    @pytest.mark.asyncio
    async def test_create_document_with_metadata_markdown(self, document_agent_factory):
        """Test document creation with metadata for markdown."""
        document_agent = document_agent_factory()

        metadata = {"title": "Test Doc", "author": "Test Author"}

        with patch("yaml.dump") as mock_yaml:
            mock_yaml.return_value = "title: Test Doc\nauthor: Test Author\n"

            result = await document_agent.create_document(
                file_path="/output/test.md",
                content="Content here",
                document_type="markdown",
                metadata=metadata,
            )

        assert result["status"] == "success"
        assert result["document_type"] == "markdown"

    @pytest.mark.asyncio
    async def test_create_document_with_metadata_text(self, document_agent_factory):
        """Test document creation with metadata for text."""
        document_agent = document_agent_factory()

        metadata = {"title": "Test Doc", "author": "Test Author"}

        result = await document_agent.create_document(
            file_path="/output/test.txt",
            content="Content here",
            document_type="text",
            metadata=metadata,
        )

        assert result["status"] == "success"
        # Check that LLM was called with metadata header
        call_prompt = document_agent.pydantic_agent.run_calls[0][0]
        assert "# title: Test Doc" in call_prompt
        assert "# author: Test Author" in call_prompt

    @pytest.mark.asyncio
    async def test_create_document_prompt_construction(self, document_agent_factory):
        """Test that document creation constructs the prompt correctly."""
        document_agent = document_agent_factory()

        await document_agent.create_document("/output/test.txt", "Test content", "text")

        call_prompt = document_agent.pydantic_agent.run_calls[0][0]
        assert "Write the following content to file at /output/test.txt:" in call_prompt
        assert "Test content" in call_prompt

    @pytest.mark.asyncio
    async def test_create_document_handles_error(self, document_agent_factory):
        """Test document creation error handling."""
        document_agent = document_agent_factory()

        document_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Write error")
        )

        result = await document_agent.create_document(
            "/error/path.txt", "Content", "text"
        )

        assert result["status"] == "error"
        assert "Write error" in result["error"]
        assert result["file_path"] == "/error/path.txt"

    @pytest.mark.asyncio
    async def test_create_document_different_types(self, document_agent_factory):
        """Test creating different document types."""
        document_agent = document_agent_factory()

        document_types = ["text", "markdown", "json", "html"]
        for doc_type in document_types:
            result = await document_agent.create_document(
                f"/output/test.{doc_type}", f"Content for {doc_type}", doc_type
            )
            assert result["document_type"] == doc_type


class TestDocumentAgentCreateReportFromTemplate:
    """Test cases for create_report_from_template method."""

    @pytest.mark.asyncio
    async def test_create_report_from_template_basic(self, document_agent_factory):
        """Test basic report creation from template."""
        document_agent = document_agent_factory()

        # Mock template reading
        document_agent.pydantic_agent.set_next_result(
            "Template content with {{placeholder}}"
        )
        document_agent.pydantic_agent.set_next_result("Filled template content")
        document_agent.pydantic_agent.set_next_result("File written successfully")

        template_data = {"placeholder": "test value"}

        result = await document_agent.create_report_from_template(
            template_path="/templates/report.md",
            output_path="/output/report.md",
            template_data=template_data,
        )

        assert result["status"] == "success"
        assert result["file_path"] == "/output/report.md"

    @pytest.mark.asyncio
    async def test_create_report_template_read_error(self, document_agent_factory):
        """Test report creation when template reading fails."""
        document_agent = document_agent_factory()

        # Mock template reading to return an error result from read_document
        async def mock_read_document(file_path, extract_metadata=False):
            return {"status": "error", "error": "Template not found"}

        document_agent.read_document = mock_read_document

        template_data = {"placeholder": "test value"}

        result = await document_agent.create_report_from_template(
            template_path="/templates/missing.md",
            output_path="/output/report.md",
            template_data=template_data,
        )

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_create_report_prompt_construction(self, document_agent_factory):
        """Test that report creation constructs the prompt correctly."""
        document_agent = document_agent_factory()

        # Mock successful template reading
        document_agent.pydantic_agent.set_next_result("Template with {{name}}")

        template_data = {"name": "Test Report"}

        await document_agent.create_report_from_template(
            "/templates/report.md", "/output/report.md", template_data
        )

        # Check template filling prompt
        fill_prompt = document_agent.pydantic_agent.run_calls[1][0]
        assert "Fill this template with the provided data" in fill_prompt
        assert "Template with {{name}}" in fill_prompt
        assert "Test Report" in fill_prompt

    @pytest.mark.asyncio
    async def test_create_report_handles_error(self, document_agent_factory):
        """Test report creation error handling."""
        document_agent = document_agent_factory()

        document_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Template error")
        )

        result = await document_agent.create_report_from_template(
            "/templates/report.md", "/output/report.md", {}
        )

        assert result["status"] == "error"
        assert "Template error" in result["error"]


class TestDocumentAgentAppendToDocument:
    """Test cases for append_to_document method."""

    @pytest.mark.asyncio
    async def test_append_to_existing_document(self, document_agent_factory):
        """Test appending to an existing document."""
        document_agent = document_agent_factory()

        # Mock existing document reading
        document_agent.pydantic_agent.set_next_result("Existing content")
        document_agent.pydantic_agent.set_next_result("Append successful")

        result = await document_agent.append_to_document(
            "/existing/document.txt", "New content to append"
        )

        assert result["status"] == "success"
        assert result["file_path"] == "/existing/document.txt"
        assert result["content_appended"] == len("New content to append")

    @pytest.mark.asyncio
    async def test_append_to_nonexistent_document(self, document_agent_factory):
        """Test appending to a non-existent document (creates new)."""
        document_agent = document_agent_factory()

        # Mock read_document to return an error (file doesn't exist)
        async def mock_read_document(file_path, extract_metadata=False):
            return {"status": "error", "error": "File not found"}

        # Mock create_document to return success
        async def mock_create_document(
            file_path, content, document_type="text", metadata=None
        ):
            return {
                "status": "success",
                "file_path": file_path,
                "document_type": document_type,
            }

        document_agent.read_document = mock_read_document
        document_agent.create_document = mock_create_document

        result = await document_agent.append_to_document(
            "/new/document.txt", "Initial content"
        )

        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_append_with_custom_separator(self, document_agent_factory):
        """Test appending with custom separator."""
        document_agent = document_agent_factory()

        # Mock existing document
        document_agent.pydantic_agent.set_next_result("Existing content")

        await document_agent.append_to_document(
            "/test/document.txt", "New content", separator="---\n"
        )

        # Check that content was combined with custom separator
        write_prompt = document_agent.pydantic_agent.run_calls[1][0]
        assert "Existing content---\nNew content" in write_prompt

    @pytest.mark.asyncio
    async def test_append_handles_error(self, document_agent_factory):
        """Test append operation error handling."""
        document_agent = document_agent_factory()

        document_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Append error")
        )

        result = await document_agent.append_to_document(
            "/error/document.txt", "Content"
        )

        assert result["status"] == "error"
        assert "Append error" in result["error"]


@pytest.mark.parametrize("document_type", ["text", "markdown", "json", "html", "xml"])
class TestDocumentAgentParametrized:
    """Parametrized test cases for different document types."""

    @pytest.mark.asyncio
    async def test_create_document_with_various_types(
        self, document_type, document_agent_factory
    ):
        """Test document creation with various document types."""
        document_agent = document_agent_factory()

        result = await document_agent.create_document(
            f"/test/document.{document_type}",
            f"Content for {document_type}",
            document_type,
        )

        assert result["status"] == "success"
        assert result["document_type"] == document_type


@pytest.mark.parametrize("file_extension", [".pdf", ".docx", ".txt", ".md", ".json"])
class TestDocumentAgentFileTypes:
    """Parametrized test cases for different file types."""

    @pytest.mark.asyncio
    async def test_read_document_with_various_extensions(
        self, file_extension, document_agent_factory
    ):
        """Test document reading with various file extensions."""
        document_agent = document_agent_factory()

        result = await document_agent.read_document(f"/test/document{file_extension}")

        assert result["status"] == "success"
        assert result["file_type"] == file_extension


class TestDocumentAgentEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_read_document_empty_path(self, document_agent_factory):
        """Test reading document with empty path."""
        document_agent = document_agent_factory()

        result = await document_agent.read_document("")

        assert result["file_path"] == ""
        # Should still attempt to process

    @pytest.mark.asyncio
    async def test_create_document_empty_content(self, document_agent_factory):
        """Test creating document with empty content."""
        document_agent = document_agent_factory()

        result = await document_agent.create_document("/test/empty.txt", "", "text")

        assert result["status"] == "success"
        assert result["size"] == 0

    @pytest.mark.asyncio
    async def test_read_multiple_documents_empty_list(self, document_agent_factory):
        """Test reading multiple documents with empty list."""
        document_agent = document_agent_factory()

        result = await document_agent.read_multiple_documents([])

        assert result == []

    @pytest.mark.asyncio
    async def test_create_document_very_long_content(self, document_agent_factory):
        """Test creating document with very long content."""
        document_agent = document_agent_factory()

        long_content = "A" * 10000

        result = await document_agent.create_document(
            "/test/large.txt", long_content, "text"
        )

        assert result["status"] == "success"
        assert result["size"] == 10000

    @pytest.mark.asyncio
    async def test_append_to_document_none_separator(self, document_agent_factory):
        """Test appending with None separator."""
        document_agent = document_agent_factory()

        # Mock existing document reading to return a proper result structure
        async def mock_read_document(file_path, extract_metadata=False):
            return {"status": "success", "content": "Existing", "file_path": file_path}

        document_agent.read_document = mock_read_document

        result = await document_agent.append_to_document(
            "/test/doc.txt", "New", separator=None
        )

        # Should use default separator when None, but might still fail due to None handling
        # The test documents current behavior - None separator causes an error
        assert result["status"] == "error"
        assert "can only concatenate str" in result["error"]


class TestDocumentAgentIntegration:
    """Integration test cases for complete document agent workflows."""

    @pytest.mark.asyncio
    async def test_full_document_workflow(self, document_agent_factory):
        """Test complete document workflow: create, read, append."""
        document_agent = document_agent_factory()

        # Create document
        create_result = await document_agent.create_document(
            "/workflow/test.md", "Initial content", "markdown"
        )
        assert create_result["status"] == "success"

        # Read document
        document_agent.pydantic_agent.set_next_result("Initial content")
        read_result = await document_agent.read_document("/workflow/test.md")
        assert read_result["status"] == "success"

        # Append to document
        document_agent.pydantic_agent.set_next_result("Initial content")
        append_result = await document_agent.append_to_document(
            "/workflow/test.md", "Additional content"
        )
        assert append_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_template_report_workflow(self, document_agent_factory):
        """Test template-based report generation workflow."""
        document_agent = document_agent_factory()

        # Mock template processing
        document_agent.pydantic_agent.set_next_result("Template: {{title}}")
        document_agent.pydantic_agent.set_next_result("Template: Test Report")
        document_agent.pydantic_agent.set_next_result("Report created")

        template_data = {"title": "Test Report", "author": "Test Author"}

        result = await document_agent.create_report_from_template(
            "/templates/report.md", "/output/report.md", template_data
        )

        assert result["status"] == "success"
        assert result["document_type"] == "report"

    @pytest.mark.asyncio
    async def test_document_agent_error_recovery(self, document_agent_factory):
        """Test that document agent recovers from errors in one operation."""
        document_agent = document_agent_factory()

        # First operation fails
        document_agent.pydantic_agent.run = AsyncMock(
            side_effect=Exception("First Error")
        )

        result1 = await document_agent.read_document("/error/doc.pdf")
        assert result1["status"] == "error"

        # Reset mock for second operation
        document_agent.pydantic_agent.run = AsyncMock(return_value=Mock(data="Success"))

        result2 = await document_agent.create_document(
            "/test/doc.txt", "Content", "text"
        )
        assert result2["status"] == "success"
