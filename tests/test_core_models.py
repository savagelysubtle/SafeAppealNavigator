"""
Test suite for core.models module.

This module contains comprehensive tests for all Pydantic models defined in
the core.models module, including message envelopes, document processing models,
legal research models, and IDE integration models.
"""

import time
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from ai_research_assistant.core.models import (
    # Resource Management Models
    AgentTask,
    # User Request Models
    AnalyzeDocumentRequest,
    ChatRequest,
    # IDE Integration Models
    CodeDiffPart,
    ComprehensiveResearchResult,
    # Legal Research Models
    ConductComprehensiveResearchInput,
    CreateFileRequest,
    # Document Processing Models
    DocumentProcessingSummary,
    DocumentSourceInfo,
    IDECommandPart,
    InlineEditRequest,
    LegalClauseAnalysisPart,
    LegalResearchFindingsSummary,
    # Message Envelope Models
    MessageEnvelope,
    NotificationPart,
    Part,
    PlanPart,
    ProcessAndStoreDocumentsInput,
    ProcessedDocumentInfo,
    # Data Query Models
    QueryAndSynthesizeReportInput,
    ResearchFinding,
    SkillInvocation,
    StatusPart,
    SynthesizedReportOutput,
    TaskResult,
)


class TestPart:
    """Test cases for Part model."""

    def test_part_creation_with_defaults(self):
        """Test creating Part with default values."""
        part = Part()
        assert part.content == ""
        assert part.type == "text/plain"

    def test_part_creation_with_values(self):
        """Test creating Part with custom values."""
        content = "Hello, world!"
        mime_type = "text/html"

        part = Part(content=content, type=mime_type)
        assert part.content == content
        assert part.type == mime_type

    def test_part_with_dict_content(self):
        """Test Part with dictionary content."""
        content = {"key": "value", "number": 42}
        part = Part(content=content, type="application/json")

        assert part.content == content
        assert part.type == "application/json"


class TestSkillInvocation:
    """Test cases for SkillInvocation model."""

    def test_skill_invocation_creation(self):
        """Test creating SkillInvocation with parameters."""
        skill_name = "test_skill"
        parameters = {"param1": "value1", "param2": 42}

        invocation = SkillInvocation(skill_name=skill_name, parameters=parameters)
        assert invocation.skill_name == skill_name
        assert invocation.parameters == parameters

    def test_skill_invocation_empty_parameters(self):
        """Test creating SkillInvocation with default empty parameters."""
        invocation = SkillInvocation(skill_name="test_skill")
        assert invocation.skill_name == "test_skill"
        assert invocation.parameters == {}


class TestTaskResult:
    """Test cases for TaskResult model."""

    def test_task_result_creation_with_defaults(self):
        """Test creating TaskResult with default values."""
        result = TaskResult()

        assert isinstance(result.task_id, UUID)
        assert result.status == "success"
        assert result.parts == []
        assert result.error_message is None
        assert result.metadata == {}

    def test_task_result_creation_with_values(self):
        """Test creating TaskResult with custom values."""
        task_id = uuid4()
        status = "error"
        parts = [Part(content="Error occurred")]
        error_message = "Test error"
        metadata = {"timestamp": "2024-01-01T00:00:00Z"}

        result = TaskResult(
            task_id=task_id,
            status=status,
            parts=parts,
            error_message=error_message,
            metadata=metadata,
        )

        assert result.task_id == task_id
        assert result.status == status
        assert result.parts == parts
        assert result.error_message == error_message
        assert result.metadata == metadata


class TestMessageEnvelope:
    """Test cases for MessageEnvelope model."""

    def test_message_envelope_creation_with_defaults(self):
        """Test creating MessageEnvelope with required fields only."""
        envelope = MessageEnvelope(source_agent_id="agent1", target_agent_id="agent2")

        assert isinstance(envelope.message_id, UUID)
        assert envelope.conversation_id is None
        assert envelope.task_id is None
        assert isinstance(envelope.timestamp, int)
        assert envelope.source_agent_id == "agent1"
        assert envelope.target_agent_id == "agent2"
        assert envelope.skill_invocation is None
        assert envelope.task_result is None
        assert envelope.parts == []
        assert envelope.metadata == {}

    def test_message_envelope_with_skill_invocation(self):
        """Test MessageEnvelope with skill invocation."""
        skill_invocation = SkillInvocation(
            skill_name="test_skill", parameters={"param": "value"}
        )

        envelope = MessageEnvelope(
            source_agent_id="agent1",
            target_agent_id="agent2",
            skill_invocation=skill_invocation,
        )

        assert envelope.skill_invocation == skill_invocation

    def test_message_envelope_with_task_result(self):
        """Test MessageEnvelope with task result."""
        task_result = TaskResult(status="completed")

        envelope = MessageEnvelope(
            source_agent_id="agent1", target_agent_id="agent2", task_result=task_result
        )

        assert envelope.task_result == task_result

    def test_message_envelope_timestamp_generation(self):
        """Test that timestamp is generated automatically."""
        start_time = int(time.time() * 1000)
        envelope = MessageEnvelope(source_agent_id="agent1", target_agent_id="agent2")
        end_time = int(time.time() * 1000)

        assert start_time <= envelope.timestamp <= end_time


class TestDocumentProcessingModels:
    """Test cases for document processing models."""

    def test_document_source_info_creation(self):
        """Test DocumentSourceInfo model."""
        source = DocumentSourceInfo(
            mcp_path="/path/to/document.pdf",
            original_filename="document.pdf",
            document_type="pdf",
        )

        assert source.mcp_path == "/path/to/document.pdf"
        assert source.original_filename == "document.pdf"
        assert source.document_type == "pdf"

    def test_processed_document_info_creation(self):
        """Test ProcessedDocumentInfo model."""
        processed = ProcessedDocumentInfo(
            source_path="/path/to/source.pdf",
            text_artifact_mcp_path="/artifacts/text.txt",
            metadata_artifact_mcp_path="/artifacts/metadata.json",
            vector_db_chunk_ids=["chunk1", "chunk2"],
        )

        assert processed.source_path == "/path/to/source.pdf"
        assert processed.text_artifact_mcp_path == "/artifacts/text.txt"
        assert processed.metadata_artifact_mcp_path == "/artifacts/metadata.json"
        assert processed.vector_db_chunk_ids == ["chunk1", "chunk2"]
        assert processed.error_message is None
        assert processed.status == "success"

    def test_process_and_store_documents_input(self):
        """Test ProcessAndStoreDocumentsInput model."""
        sources = [
            DocumentSourceInfo(mcp_path="/doc1.pdf"),
            DocumentSourceInfo(mcp_path="/doc2.docx"),
        ]

        input_model = ProcessAndStoreDocumentsInput(
            document_sources=sources,
            case_id="case123",
            target_vector_collection="legal_docs",
        )

        assert input_model.document_sources == sources
        assert input_model.case_id == "case123"
        assert input_model.target_vector_collection == "legal_docs"
        assert input_model.ocr_enabled is True
        assert input_model.metadata_extraction_level == "standard"

    def test_document_processing_summary(self):
        """Test DocumentProcessingSummary model."""
        processed_docs = [
            ProcessedDocumentInfo(
                source_path="/doc1.pdf",
                text_artifact_mcp_path="/text1.txt",
                metadata_artifact_mcp_path="/meta1.json",
                vector_db_chunk_ids=["chunk1"],
            )
        ]

        summary = DocumentProcessingSummary(
            case_id="case123",
            processed_documents=processed_docs,
            overall_status="Completed",
            total_documents_input=2,
            total_documents_processed_successfully=1,
            total_documents_failed=1,
            processing_time_seconds=45.5,
        )

        assert summary.case_id == "case123"
        assert summary.processed_documents == processed_docs
        assert summary.overall_status == "Completed"
        assert summary.total_documents_input == 2
        assert summary.total_documents_processed_successfully == 1
        assert summary.total_documents_failed == 1
        assert summary.processing_time_seconds == 45.5
        assert summary.errors_summary == []


class TestLegalResearchModels:
    """Test cases for legal research models."""

    def test_conduct_comprehensive_research_input(self):
        """Test ConductComprehensiveResearchInput model."""
        research_input = ConductComprehensiveResearchInput(
            search_keywords=["workers compensation", "appeal"],
            case_context="Worker injured on job site",
            research_depth="deep",
            sources_to_include=["wcat", "canlii"],
            max_results_per_source=20,
        )

        assert research_input.search_keywords == ["workers compensation", "appeal"]
        assert research_input.case_context == "Worker injured on job site"
        assert research_input.research_depth == "deep"
        assert research_input.sources_to_include == ["wcat", "canlii"]
        assert research_input.max_results_per_source == 20

    def test_research_finding_creation(self):
        """Test ResearchFinding model."""
        finding = ResearchFinding(
            source_name="WCAT Decision Search",
            title="Appeal Decision 2024-001",
            url="https://wcat.bc.ca/decision/2024-001",
            snippet="This appeal concerns...",
            relevance_score=0.95,
            full_content_mcp_path="/content/decision.txt",
        )

        assert finding.source_name == "WCAT Decision Search"
        assert finding.title == "Appeal Decision 2024-001"
        assert finding.url == "https://wcat.bc.ca/decision/2024-001"
        assert finding.snippet == "This appeal concerns..."
        assert finding.relevance_score == 0.95
        assert finding.full_content_mcp_path == "/content/decision.txt"

    def test_legal_research_findings_summary(self):
        """Test LegalResearchFindingsSummary model."""
        findings = [
            ResearchFinding(source_name="WCAT", title="Decision 1"),
            ResearchFinding(source_name="CanLII", title="Case 2"),
        ]

        summary = LegalResearchFindingsSummary(
            research_query_summary="Research on workers compensation appeals",
            findings=findings,
            overall_summary="Found relevant precedents for the case",
            key_insights=["Appeals often succeed on procedural grounds"],
            research_time_seconds=120.5,
            mcp_path_to_full_report="/reports/research.md",
        )

        assert (
            summary.research_query_summary == "Research on workers compensation appeals"
        )
        assert summary.findings == findings
        assert summary.overall_summary == "Found relevant precedents for the case"
        assert summary.key_insights == ["Appeals often succeed on procedural grounds"]
        assert summary.research_time_seconds == 120.5
        assert summary.mcp_path_to_full_report == "/reports/research.md"

    def test_comprehensive_research_result(self):
        """Test ComprehensiveResearchResult model."""
        findings = [ResearchFinding(source_name="Test", title="Test Finding")]

        result = ComprehensiveResearchResult(
            research_summary="Comprehensive research completed",
            findings=findings,
            suggested_next_steps=["Review precedents", "Draft appeal"],
            synthesis_quality_score=0.85,
            generation_time_seconds=180.2,
        )

        assert result.research_summary == "Comprehensive research completed"
        assert result.findings == findings
        assert result.suggested_next_steps == ["Review precedents", "Draft appeal"]
        assert result.synthesis_quality_score == 0.85
        assert result.generation_time_seconds == 180.2


class TestDataQueryModels:
    """Test cases for data query models."""

    def test_query_and_synthesize_report_input(self):
        """Test QueryAndSynthesizeReportInput model."""
        query_input = QueryAndSynthesizeReportInput(
            intake_summary_mcp_path="/summaries/intake.md",
            research_summary_mcp_path="/summaries/research.md",
            user_query_details="Generate appeal letter for workplace injury",
            report_format="markdown",
            target_audience="legal_professional",
        )

        assert query_input.intake_summary_mcp_path == "/summaries/intake.md"
        assert query_input.research_summary_mcp_path == "/summaries/research.md"
        assert (
            query_input.user_query_details
            == "Generate appeal letter for workplace injury"
        )
        assert query_input.report_format == "markdown"
        assert query_input.target_audience == "legal_professional"

    def test_synthesized_report_output(self):
        """Test SynthesizedReportOutput model."""
        output = SynthesizedReportOutput(
            report_artifact_mcp_path="/reports/appeal_letter.md",
            queries_executed_count=5,
            synthesis_quality_score=0.92,
            generation_time_seconds=45.8,
        )

        assert output.report_artifact_mcp_path == "/reports/appeal_letter.md"
        assert output.queries_executed_count == 5
        assert output.synthesis_quality_score == 0.92
        assert output.generation_time_seconds == 45.8


class TestIDEIntegrationModels:
    """Test cases for IDE integration models."""

    def test_plan_part_creation(self):
        """Test PlanPart model."""
        plan = PlanPart(
            plan=["Step 1: Analyze", "Step 2: Generate", "Step 3: Review"],
            is_approved=True,
        )

        assert plan.plan == ["Step 1: Analyze", "Step 2: Generate", "Step 3: Review"]
        assert plan.is_approved is True

    def test_status_part_creation(self):
        """Test StatusPart model."""
        status = StatusPart(message="Processing document", step=2, total_steps=5)

        assert status.message == "Processing document"
        assert status.step == 2
        assert status.total_steps == 5

    def test_code_diff_part_creation(self):
        """Test CodeDiffPart model."""
        diff = CodeDiffPart(
            uri="file:///path/to/file.py", diff="@@ -1,3 +1,3 @@\n-old line\n+new line"
        )

        assert diff.uri == "file:///path/to/file.py"
        assert diff.diff == "@@ -1,3 +1,3 @@\n-old line\n+new line"

    def test_notification_part_creation(self):
        """Test NotificationPart model."""
        notification = NotificationPart(
            severity="error", message="An error occurred during processing"
        )

        assert notification.severity == "error"
        assert notification.message == "An error occurred during processing"

    def test_ide_command_part_creation(self):
        """Test IDECommandPart model."""
        command = IDECommandPart(
            commandId="editor.action.formatDocument", args=["--preserve-newlines"]
        )

        assert command.commandId == "editor.action.formatDocument"
        assert command.args == ["--preserve-newlines"]

    def test_legal_clause_analysis_part(self):
        """Test LegalClauseAnalysisPart model."""
        analysis = LegalClauseAnalysisPart(
            uri="file:///contract.pdf",
            clause_text="Force majeure clause",
            analysis="This clause protects against unforeseen circumstances",
            risk_level="medium",
        )

        assert analysis.uri == "file:///contract.pdf"
        assert analysis.clause_text == "Force majeure clause"
        assert (
            analysis.analysis == "This clause protects against unforeseen circumstances"
        )
        assert analysis.risk_level == "medium"


class TestUserRequestModels:
    """Test cases for user request models."""

    def test_inline_edit_request(self):
        """Test InlineEditRequest model."""
        request = InlineEditRequest(
            type="inline_edit",
            uri="file:///code.py",
            selection="def old_function():",
            prompt="Rename function to new_function",
        )

        assert request.type == "inline_edit"
        assert request.uri == "file:///code.py"
        assert request.selection == "def old_function():"
        assert request.prompt == "Rename function to new_function"

    def test_create_file_request(self):
        """Test CreateFileRequest model."""
        request = CreateFileRequest(
            type="create_file",
            uri="file:///new_file.py",
            content="# New Python file\nprint('Hello, World!')",
        )

        assert request.type == "create_file"
        assert request.uri == "file:///new_file.py"
        assert request.content == "# New Python file\nprint('Hello, World!')"

    def test_analyze_document_request(self):
        """Test AnalyzeDocumentRequest model."""
        request = AnalyzeDocumentRequest(
            type="analyze_document", uri="file:///contract.pdf"
        )

        assert request.type == "analyze_document"
        assert request.uri == "file:///contract.pdf"

    def test_chat_request(self):
        """Test ChatRequest model."""
        request = ChatRequest(
            type="chat", prompt="What are the key terms in this contract?"
        )

        assert request.type == "chat"
        assert request.prompt == "What are the key terms in this contract?"


class TestAgentTask:
    """Test cases for AgentTask model."""

    def test_agent_task_creation_with_defaults(self):
        """Test creating AgentTask with default values."""
        task = AgentTask(
            task_type="document_analysis", parameters={"document_id": "doc123"}
        )

        assert isinstance(task.id, UUID)
        assert task.task_type == "document_analysis"
        assert task.parameters == {"document_id": "doc123"}
        assert task.priority == 1
        assert task.parent_workflow_id is None

    def test_agent_task_creation_with_values(self):
        """Test creating AgentTask with custom values."""
        task_id = uuid4()
        task = AgentTask(
            id=task_id,
            task_type="legal_research",
            parameters={"query": "workers comp"},
            priority=5,
            parent_workflow_id="workflow_123",
        )

        assert task.id == task_id
        assert task.task_type == "legal_research"
        assert task.parameters == {"query": "workers comp"}
        assert task.priority == 5
        assert task.parent_workflow_id == "workflow_123"


class TestModelValidation:
    """Test cases for model validation and error handling."""

    def test_message_envelope_missing_required_fields(self):
        """Test MessageEnvelope validation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            MessageEnvelope()

        errors = exc_info.value.errors()
        field_names = [error["loc"][0] for error in errors]
        assert "source_agent_id" in field_names
        assert "target_agent_id" in field_names

    def test_notification_part_invalid_severity(self):
        """Test NotificationPart with invalid severity value."""
        with pytest.raises(ValidationError) as exc_info:
            NotificationPart(severity="invalid", message="Test message")

        errors = exc_info.value.errors()
        assert any("Input should be" in str(error["msg"]) for error in errors)

    def test_legal_clause_analysis_invalid_risk_level(self):
        """Test LegalClauseAnalysisPart with invalid risk level."""
        with pytest.raises(ValidationError) as exc_info:
            LegalClauseAnalysisPart(
                uri="file:///test.pdf",
                clause_text="Test clause",
                analysis="Test analysis",
                risk_level="invalid",
            )

        errors = exc_info.value.errors()
        assert any("Input should be" in str(error["msg"]) for error in errors)

    def test_skill_invocation_empty_skill_name(self):
        """Test SkillInvocation with empty skill name."""
        # Empty skill names should be allowed according to the model definition
        # This test documents that empty strings are permitted
        invocation = SkillInvocation(skill_name="")
        assert invocation.skill_name == ""
        assert invocation.parameters == {}
