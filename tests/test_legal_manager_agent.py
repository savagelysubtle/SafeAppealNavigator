"""
Test suite for LegalManagerAgent class.

This module contains comprehensive tests for the legal manager agent that handles
legal document creation, citation verification, and document review workflows.
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
from ai_research_assistant.agents.specialized_manager_agent.legal_manager_agent.agent import (
    LegalManagerAgent,
    LegalManagerAgentConfig,
)


# Mock classes for testing
class MockLLM:
    """Mock LLM for testing legal manager."""

    def __init__(self, provider="mock", model="mock-model"):
        self.provider = provider
        self.model = model


class MockPydanticAgent:
    """Mock PydanticAI Agent for legal manager testing."""

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
            # Extract case name or other content from the prompt for more realistic mocking
            if "Smith v. WorkSafe BC" in user_prompt:
                result_data = "Legal memo for Smith v. WorkSafe BC case based on research findings..."
            else:
                result_data = f"Mock legal response to: {user_prompt[:50]}..."

        mock_result = Mock()
        mock_result.data = result_data
        return mock_result

    def set_next_result(self, result):
        """Set the next result to be returned by run()."""
        self.run_results.append(result)


@pytest.fixture
def legal_manager_config():
    """Fixture providing legal manager agent configuration."""
    return LegalManagerAgentConfig()


@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM instance."""
    return MockLLM("legal_test_provider", "legal_test_model")


@pytest.fixture
def legal_manager_factory():
    """Factory fixture for creating test legal manager agents."""

    def _create_legal_manager(config=None):
        if config is None:
            config = LegalManagerAgentConfig()

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                return LegalManagerAgent(config=config)

    return _create_legal_manager


@pytest.fixture
def sample_research_summary():
    """Fixture providing sample research summary for testing."""
    return {
        "case_name": "Smith v. WorkSafe BC",
        "case_number": "WCAT-2023-001234",
        "issues": ["chronic pain assessment", "functional capacity evaluation"],
        "findings": [
            "Chronic pain is compensable under s. 5.1 of the Workers Compensation Act",
            "FCE results must be considered in context of medical evidence",
        ],
        "precedents": [
            "Decision No. 2022-0567: Similar chronic pain case",
            "Decision No. 2021-1234: FCE evaluation standards",
        ],
        "recommendations": "Appeal has strong merit based on precedent analysis",
    }


class TestLegalManagerAgentConfig:
    """Test cases for LegalManagerAgentConfig class."""

    def test_config_default_values(self):
        """Test that legal manager config has correct defaults."""
        config = LegalManagerAgentConfig()

        assert config.agent_name == "LegalManagerAgent"
        assert config.agent_id == "legal_manager_agent_instance_001"
        assert "Legal Manager Agent" in config.pydantic_ai_system_prompt
        assert (
            "coordinating legal document creation" in config.pydantic_ai_system_prompt
        )
        assert "Document Agent" in config.pydantic_ai_system_prompt

    def test_config_inheritance(self):
        """Test that config properly inherits from BasePydanticAgentConfig."""
        config = LegalManagerAgentConfig()

        assert isinstance(config, BasePydanticAgentConfig)
        assert hasattr(config, "llm_provider")
        assert hasattr(config, "llm_temperature")
        assert hasattr(config, "custom_settings")

    def test_config_system_prompt_content(self):
        """Test that system prompt contains key legal responsibilities."""
        config = LegalManagerAgentConfig()

        prompt = config.pydantic_ai_system_prompt
        assert "legal document creation" in prompt
        assert "citation verification" in prompt
        assert "legal documents for accuracy" in prompt
        assert "legal document workflows" in prompt
        assert "Orchestrator" in prompt
        assert "do NOT directly access files or databases" in prompt


class TestLegalManagerAgentInitialization:
    """Test cases for LegalManagerAgent initialization."""

    def test_legal_manager_initialization_with_defaults(self):
        """Test legal manager initialization with default configuration."""
        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                legal_manager = LegalManagerAgent()

        assert legal_manager.agent_name == "LegalManagerAgent"
        assert isinstance(legal_manager.agent_config, LegalManagerAgentConfig)

    def test_legal_manager_initialization_with_custom_config(
        self, legal_manager_config
    ):
        """Test legal manager initialization with custom configuration."""
        legal_manager_config.agent_name = "CustomLegalManager"
        legal_manager_config.agent_id = "custom_legal_001"

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                legal_manager = LegalManagerAgent(config=legal_manager_config)

        assert legal_manager.agent_name == "CustomLegalManager"
        assert legal_manager.agent_config.agent_id == "custom_legal_001"

    def test_legal_manager_inherits_from_base_agent(self):
        """Test that LegalManagerAgent properly inherits from BasePydanticAgent."""
        from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent

        with patch(
            "ai_research_assistant.agents.base_pydantic_agent.Agent", MockPydanticAgent
        ):
            with patch(
                "ai_research_assistant.agents.base_pydantic_agent.get_llm_factory"
            ):
                legal_manager = LegalManagerAgent()

        assert isinstance(legal_manager, BasePydanticAgent)
        assert hasattr(legal_manager, "pydantic_agent")

    def test_legal_manager_no_direct_tools(self, legal_manager_factory):
        """Test that legal manager has no direct tools (coordinates through other agents)."""
        legal_manager = legal_manager_factory()

        tools = legal_manager._get_initial_tools()
        assert tools == []

    def test_legal_manager_logging_on_init(self, legal_manager_factory, caplog):
        """Test that initialization is logged."""
        with caplog.at_level(logging.INFO):
            legal_manager = legal_manager_factory()

        assert "LegalManagerAgent" in caplog.text
        assert "initialized" in caplog.text


class TestLegalManagerAgentDraftLegalMemo:
    """Test cases for draft_legal_memo method."""

    @pytest.mark.asyncio
    async def test_draft_legal_memo_standard(
        self, legal_manager_factory, sample_research_summary
    ):
        """Test drafting a standard legal memo."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.draft_legal_memo(sample_research_summary)

        assert result["status"] == "success"
        assert result["memo_type"] == "standard"
        assert "Smith v. WorkSafe BC" in result["content_preview"]
        assert result["output_path"].startswith("/legal/memos/")
        assert result["output_path"].endswith(".md")

    @pytest.mark.asyncio
    async def test_draft_legal_memo_custom_type(
        self, legal_manager_factory, sample_research_summary
    ):
        """Test drafting a memo with custom type."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.draft_legal_memo(
            sample_research_summary,
            memo_type="brief",
            output_path="/custom/path/memo.md",
        )

        assert result["status"] == "success"
        assert result["memo_type"] == "brief"
        assert result["output_path"] == "/custom/path/memo.md"

    @pytest.mark.asyncio
    async def test_draft_legal_memo_prompt_construction(
        self, legal_manager_factory, sample_research_summary
    ):
        """Test that memo drafting constructs the prompt correctly."""
        legal_manager = legal_manager_factory()

        await legal_manager.draft_legal_memo(
            sample_research_summary, memo_type="opinion"
        )

        # Check the prompt sent to LLM
        call_prompt = legal_manager.pydantic_agent.run_calls[0][0]
        assert "Create a opinion legal memo" in call_prompt
        assert "Smith v. WorkSafe BC" in call_prompt
        assert "Executive Summary" in call_prompt
        assert "Issue Statement" in call_prompt
        assert "Brief Answer" in call_prompt
        assert "Discussion/Analysis" in call_prompt
        assert "Properly formatted citations" in call_prompt

    @pytest.mark.asyncio
    async def test_draft_legal_memo_with_complex_research(self, legal_manager_factory):
        """Test memo drafting with complex research summary."""
        complex_research = {
            "multiple_cases": ["Case A", "Case B", "Case C"],
            "legal_issues": ["Issue 1", "Issue 2"],
            "statutes": ["Section 5.1", "Section 10.2"],
            "analysis": "Complex legal analysis with multiple precedents",
        }

        legal_manager = legal_manager_factory()
        result = await legal_manager.draft_legal_memo(
            complex_research, memo_type="comprehensive"
        )

        assert result["status"] == "success"
        assert result["memo_type"] == "comprehensive"

    @pytest.mark.asyncio
    async def test_draft_legal_memo_handles_llm_error(
        self, legal_manager_factory, sample_research_summary
    ):
        """Test memo drafting error handling."""
        legal_manager = legal_manager_factory()

        # Mock LLM to raise an exception
        legal_manager.pydantic_agent.run = AsyncMock(side_effect=Exception("LLM Error"))

        result = await legal_manager.draft_legal_memo(sample_research_summary)

        assert result["status"] == "error"
        assert "LLM Error" in result["error"]
        assert result["memo_type"] == "standard"

    @pytest.mark.asyncio
    async def test_draft_legal_memo_logging(
        self, legal_manager_factory, sample_research_summary, caplog
    ):
        """Test that memo drafting is logged."""
        legal_manager = legal_manager_factory()

        with caplog.at_level(logging.INFO):
            await legal_manager.draft_legal_memo(
                sample_research_summary, memo_type="brief"
            )

        assert "Coordinating legal memo drafting (brief)" in caplog.text

    @pytest.mark.asyncio
    async def test_draft_legal_memo_uuid_generation(
        self, legal_manager_factory, sample_research_summary
    ):
        """Test that memo paths include unique UUIDs."""
        legal_manager = legal_manager_factory()

        result1 = await legal_manager.draft_legal_memo(sample_research_summary)
        result2 = await legal_manager.draft_legal_memo(sample_research_summary)

        # Paths should be different due to UUID
        assert result1["output_path"] != result2["output_path"]
        assert "/legal/memos/" in result1["output_path"]
        assert "/legal/memos/" in result2["output_path"]

    @pytest.mark.asyncio
    async def test_draft_legal_memo_document_agent_coordination_log(
        self, legal_manager_factory, sample_research_summary, caplog
    ):
        """Test that coordination with Document Agent is logged."""
        legal_manager = legal_manager_factory()

        with caplog.at_level(logging.INFO):
            await legal_manager.draft_legal_memo(sample_research_summary)

        assert "Would coordinate with Document Agent to create memo file" in caplog.text


class TestLegalManagerAgentVerifyCitations:
    """Test cases for verify_citations method."""

    @pytest.mark.asyncio
    async def test_verify_citations_bluebook_style(self, legal_manager_factory):
        """Test citation verification with Bluebook style."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.verify_citations(
            "/path/to/document.pdf", "bluebook"
        )

        assert result["status"] == "success"
        assert result["document_path"] == "/path/to/document.pdf"
        assert result["citation_style"] == "bluebook"
        assert "Mock legal response" in result["verification_results"]

    @pytest.mark.asyncio
    async def test_verify_citations_other_styles(self, legal_manager_factory):
        """Test citation verification with different citation styles."""
        legal_manager = legal_manager_factory()

        styles = ["APA", "MLA", "Chicago", "custom"]

        for style in styles:
            result = await legal_manager.verify_citations("/test/doc.pdf", style)
            assert result["citation_style"] == style
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_verify_citations_prompt_construction(self, legal_manager_factory):
        """Test that citation verification constructs the prompt correctly."""
        legal_manager = legal_manager_factory()

        await legal_manager.verify_citations("/legal/document.pdf", "bluebook")

        call_prompt = legal_manager.pydantic_agent.run_calls[0][0]
        assert "Verify all legal citations" in call_prompt
        assert "bluebook style" in call_prompt
        assert "Mock content from /legal/document.pdf" in call_prompt
        assert "incorrect citations and provide corrections" in call_prompt

    @pytest.mark.asyncio
    async def test_verify_citations_default_style(self, legal_manager_factory):
        """Test citation verification with default style."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.verify_citations("/test/document.docx")

        assert result["citation_style"] == "bluebook"  # Default style

    @pytest.mark.asyncio
    async def test_verify_citations_document_coordination_log(
        self, legal_manager_factory, caplog
    ):
        """Test that Document Agent coordination is logged."""
        legal_manager = legal_manager_factory()

        with caplog.at_level(logging.INFO):
            await legal_manager.verify_citations("/test/doc.pdf")

        assert "Would coordinate with Document Agent to read document" in caplog.text

    @pytest.mark.asyncio
    async def test_verify_citations_handles_error(self, legal_manager_factory):
        """Test citation verification error handling."""
        legal_manager = legal_manager_factory()

        legal_manager.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Verification Error")
        )

        result = await legal_manager.verify_citations("/error/doc.pdf")

        assert result["status"] == "error"
        assert "Verification Error" in result["error"]
        assert result["document_path"] == "/error/doc.pdf"

    @pytest.mark.asyncio
    async def test_verify_citations_result_structure(self, legal_manager_factory):
        """Test that citation verification returns correct result structure."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.verify_citations("/structure/test.pdf", "APA")

        required_keys = [
            "status",
            "document_path",
            "citation_style",
            "verification_results",
            "citations_found",
            "corrections_needed",
        ]
        for key in required_keys:
            assert key in result

        assert result["citations_found"] == 0  # Mock implementation
        assert result["corrections_needed"] == 0  # Mock implementation


class TestLegalManagerAgentReviewLegalDocument:
    """Test cases for review_legal_document method."""

    @pytest.mark.asyncio
    async def test_review_legal_document_default_criteria(self, legal_manager_factory):
        """Test document review with default criteria."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.review_legal_document("/review/document.pdf")

        assert result["status"] == "success"
        assert result["document_path"] == "/review/document.pdf"

        criteria = result["review_criteria"]
        assert criteria["check_citations"] is True
        assert criteria["check_legal_accuracy"] is True
        assert criteria["check_formatting"] is True
        assert criteria["check_completeness"] is True

    @pytest.mark.asyncio
    async def test_review_legal_document_custom_criteria(self, legal_manager_factory):
        """Test document review with custom criteria."""
        legal_manager = legal_manager_factory()

        custom_criteria = {
            "check_citations": False,
            "check_legal_accuracy": True,
            "check_grammar": True,
            "check_tone": True,
        }

        result = await legal_manager.review_legal_document(
            "/custom/document.pdf", review_criteria=custom_criteria
        )

        assert result["status"] == "success"
        assert result["review_criteria"] == custom_criteria

    @pytest.mark.asyncio
    async def test_review_legal_document_prompt_construction(
        self, legal_manager_factory
    ):
        """Test that document review constructs the prompt correctly."""
        legal_manager = legal_manager_factory()

        await legal_manager.review_legal_document("/review/test.pdf")

        call_prompt = legal_manager.pydantic_agent.run_calls[0][0]
        assert "Perform a comprehensive legal review" in call_prompt
        assert "Mock legal document content from /review/test.pdf" in call_prompt
        assert "Legal accuracy and completeness" in call_prompt
        assert "Citation correctness" in call_prompt
        assert "Document structure and formatting" in call_prompt
        assert "Recommendations for improvement" in call_prompt

    @pytest.mark.asyncio
    async def test_review_legal_document_coordination_log(
        self, legal_manager_factory, caplog
    ):
        """Test that Document Agent coordination is logged for review."""
        legal_manager = legal_manager_factory()

        with caplog.at_level(logging.INFO):
            await legal_manager.review_legal_document("/log/test.pdf")

        assert (
            "Would coordinate with Document Agent to read document for review"
            in caplog.text
        )

    @pytest.mark.asyncio
    async def test_review_legal_document_handles_error(self, legal_manager_factory):
        """Test document review error handling."""
        legal_manager = legal_manager_factory()

        legal_manager.pydantic_agent.run = AsyncMock(
            side_effect=Exception("Review Error")
        )

        result = await legal_manager.review_legal_document("/error/document.pdf")

        assert result["status"] == "error"
        assert "Review Error" in result["error"]
        assert result["document_path"] == "/error/document.pdf"

    @pytest.mark.asyncio
    async def test_review_legal_document_result_structure(self, legal_manager_factory):
        """Test that document review returns correct result structure."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.review_legal_document("/structure/document.pdf")

        required_keys = [
            "status",
            "document_path",
            "review_criteria",
            "review_results",
            "recommendations",
        ]
        for key in required_keys:
            assert key in result

        assert isinstance(result["recommendations"], list)


@pytest.mark.parametrize(
    "memo_type", ["standard", "brief", "opinion", "comprehensive", "summary"]
)
class TestLegalManagerAgentMemoTypes:
    """Parametrized test cases for different memo types."""

    @pytest.mark.asyncio
    async def test_draft_memo_with_various_types(
        self, memo_type, legal_manager_factory, sample_research_summary
    ):
        """Test memo drafting with various memo types."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.draft_legal_memo(
            sample_research_summary, memo_type=memo_type
        )

        assert result["status"] == "success"
        assert result["memo_type"] == memo_type

        # Check that memo type appears in the prompt
        call_prompt = legal_manager.pydantic_agent.run_calls[0][0]
        assert f"Create a {memo_type} legal memo" in call_prompt


@pytest.mark.parametrize(
    "citation_style", ["bluebook", "APA", "MLA", "Chicago", "Harvard"]
)
class TestLegalManagerAgentCitationStyles:
    """Parametrized test cases for different citation styles."""

    @pytest.mark.asyncio
    async def test_verify_citations_with_various_styles(
        self, citation_style, legal_manager_factory
    ):
        """Test citation verification with various styles."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.verify_citations(
            "/test/document.pdf", citation_style
        )

        assert result["status"] == "success"
        assert result["citation_style"] == citation_style

        # Check that citation style appears in the prompt
        call_prompt = legal_manager.pydantic_agent.run_calls[0][0]
        assert f"{citation_style} style" in call_prompt


class TestLegalManagerAgentEdgeCases:
    """Test cases for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_draft_memo_with_empty_research(self, legal_manager_factory):
        """Test memo drafting with empty research summary."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.draft_legal_memo({})

        assert result["status"] == "success"
        assert result["memo_type"] == "standard"

    @pytest.mark.asyncio
    async def test_verify_citations_with_empty_path(self, legal_manager_factory):
        """Test citation verification with empty document path."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.verify_citations("")

        assert result["status"] == "success"
        assert result["document_path"] == ""

    @pytest.mark.asyncio
    async def test_review_document_with_none_criteria(self, legal_manager_factory):
        """Test document review with None criteria (should use defaults)."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.review_legal_document(
            "/test/doc.pdf", review_criteria=None
        )

        assert result["status"] == "success"
        assert result["review_criteria"]["check_citations"] is True

    @pytest.mark.asyncio
    async def test_draft_memo_with_none_output_path(
        self, legal_manager_factory, sample_research_summary
    ):
        """Test memo drafting with None output path (should generate UUID path)."""
        legal_manager = legal_manager_factory()

        result = await legal_manager.draft_legal_memo(
            sample_research_summary, output_path=None
        )

        assert result["status"] == "success"
        assert result["output_path"].startswith("/legal/memos/")
        assert ".md" in result["output_path"]

    @pytest.mark.asyncio
    async def test_methods_with_very_long_inputs(self, legal_manager_factory):
        """Test methods with very long inputs."""
        legal_manager = legal_manager_factory()

        long_path = "/very/long/path/" + "a" * 1000 + "/document.pdf"
        long_research = {"case_name": "A" * 5000}

        # Should handle long inputs gracefully
        result1 = await legal_manager.verify_citations(long_path)
        result2 = await legal_manager.draft_legal_memo(long_research)
        result3 = await legal_manager.review_legal_document(long_path)

        assert result1["status"] == "success"
        assert result2["status"] == "success"
        assert result3["status"] == "success"


class TestLegalManagerAgentIntegration:
    """Integration test cases for complete legal manager workflows."""

    @pytest.mark.asyncio
    async def test_full_legal_workflow(
        self, legal_manager_factory, sample_research_summary
    ):
        """Test complete legal workflow: draft memo, verify citations, review document."""
        legal_manager = legal_manager_factory()

        # Draft memo
        memo_result = await legal_manager.draft_legal_memo(sample_research_summary)
        memo_path = memo_result["output_path"]

        # Verify citations
        citation_result = await legal_manager.verify_citations(memo_path)

        # Review document
        review_result = await legal_manager.review_legal_document(memo_path)

        assert memo_result["status"] == "success"
        assert citation_result["status"] == "success"
        assert review_result["status"] == "success"

        # All operations should reference the same document
        assert citation_result["document_path"] == memo_path
        assert review_result["document_path"] == memo_path

    @pytest.mark.asyncio
    async def test_legal_manager_with_multiple_documents(self, legal_manager_factory):
        """Test legal manager handling multiple documents."""
        legal_manager = legal_manager_factory()

        documents = ["/doc1.pdf", "/doc2.docx", "/doc3.txt"]
        results = []

        for doc in documents:
            citation_result = await legal_manager.verify_citations(doc)
            review_result = await legal_manager.review_legal_document(doc)
            results.append((citation_result, review_result))

        assert len(results) == 3
        for citation_result, review_result in results:
            assert citation_result["status"] == "success"
            assert review_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_legal_manager_error_recovery(
        self, legal_manager_factory, sample_research_summary
    ):
        """Test that legal manager recovers from errors in one operation."""
        legal_manager = legal_manager_factory()

        # First operation fails
        legal_manager.pydantic_agent.set_next_result("Error in first operation")
        legal_manager.pydantic_agent.run = AsyncMock(
            side_effect=Exception("First Error")
        )

        result1 = await legal_manager.draft_legal_memo(sample_research_summary)
        assert result1["status"] == "error"

        # Reset mock for second operation
        legal_manager.pydantic_agent.run = AsyncMock(return_value=Mock(data="Success"))

        result2 = await legal_manager.verify_citations("/test/doc.pdf")
        assert result2["status"] == "success"
