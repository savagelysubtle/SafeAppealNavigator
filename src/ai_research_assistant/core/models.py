# src/ai_research_assistant/core/models.py
import time
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# --- Message Envelope (as per ARCHITECTURE.MD) ---
class Part(BaseModel):
    content: Union[str, Dict[str, Any]] = ""
    type: str = Field(default="text/plain", description="MIME type of the content.")


class SkillInvocation(BaseModel):
    skill_name: str = Field(description="The name of the skill to be invoked.")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters for the skill."
    )


class TaskResult(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    status: str = Field(
        default="success",
        description="Status of the task (e.g., 'success', 'error', 'in_progress').",
    )
    parts: List[Part] = Field(
        default_factory=list, description="Output parts from the task execution."
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if the task failed."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the task result."
    )


class MessageEnvelope(BaseModel):
    message_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the message.",
    )
    conversation_id: Optional[UUID] = Field(
        default=None, description="Identifier for the conversation thread."
    )
    task_id: Optional[UUID] = Field(
        default=None, description="Identifier for the task this message relates to."
    )
    timestamp: int = Field(
        default_factory=lambda: int(time.time() * 1000),
        description="Timestamp of message creation in milliseconds.",
    )
    source_agent_id: str = Field(description="ID of the agent sending the message.")
    target_agent_id: str = Field(
        description="ID of the agent intended to receive the message."
    )
    skill_invocation: Optional[SkillInvocation] = Field(
        default=None,
        description="Details for skill invocation if this message is a request.",
    )
    task_result: Optional[TaskResult] = Field(
        default=None, description="Result of a task if this message is a response."
    )
    parts: List[Part] = Field(
        default_factory=list,
        description="Content parts of the message if not a direct skill invocation/result.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for the message."
    )


# --- DocumentProcessingCoordinator I/O Models (as per ARCHITECTURE.MD) ---
class DocumentSourceInfo(BaseModel):
    mcp_path: str = Field(description="Path to the document in the MCP Filesystem.")
    original_filename: Optional[str] = Field(
        default=None, description="Original filename of the document."
    )
    document_type: Optional[str] = Field(
        default=None,
        description="Optional hint for document type (e.g., 'pdf', 'docx').",
    )


class ProcessedDocumentInfo(BaseModel):
    source_path: str = Field(description="Original MCP path of the processed document.")
    document_type: Optional[str] = Field(
        default=None, description="Detected or assigned document type."
    )
    text_artifact_mcp_path: str = Field(
        description="MCP path to the extracted text artifact."
    )
    metadata_artifact_mcp_path: str = Field(
        description="MCP path to the extracted metadata artifact (e.g., entities)."
    )
    vector_db_chunk_ids: List[str] = Field(
        description="List of chunk IDs stored in the vector database."
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if processing failed for this document.",
    )
    status: str = Field(
        default="success", description="Processing status for this document."
    )


class ProcessAndStoreDocumentsInput(BaseModel):
    document_sources: List[DocumentSourceInfo] = Field(
        description="List of documents to process."
    )
    case_id: str = Field(
        description="Identifier for the case these documents belong to."
    )
    target_vector_collection: str = Field(
        description="Name of the target vector collection for embeddings."
    )
    ocr_enabled: bool = Field(
        default=True, description="Whether to perform OCR on image-based documents."
    )
    metadata_extraction_level: str = Field(
        default="standard",
        description="Level of metadata extraction (e.g., 'basic', 'standard', 'full').",
    )


class DocumentProcessingSummary(BaseModel):
    case_id: str = Field(description="Identifier for the case.")
    processed_documents: List[ProcessedDocumentInfo] = Field(
        description="List of processed document details."
    )
    overall_status: str = Field(
        description="Overall status of the batch processing (e.g., 'Completed', 'CompletedWithErrors')."
    )
    total_documents_input: int = Field(
        description="Total number of documents received for processing."
    )
    total_documents_processed_successfully: int = Field(
        description="Number of documents processed successfully."
    )
    total_documents_failed: int = Field(
        description="Number of documents that failed processing."
    )
    errors_summary: List[str] = Field(
        default_factory=list,
        description="Summary of errors encountered during processing.",
    )
    processing_time_seconds: Optional[float] = Field(
        default=None, description="Total time taken for processing in seconds."
    )


# --- LegalResearchCoordinator I/O Models (Placeholder based on ARCHITECTURE.MD and WORKFLOWS.MD) ---
class ConductComprehensiveResearchInput(BaseModel):
    search_keywords: List[str] = Field(description="Keywords to guide the research.")
    case_context: str = Field(
        description="Contextual information about the case or research topic."
    )
    research_depth: str = Field(
        default="moderate",
        description="Depth of research (e.g., 'shallow', 'moderate', 'deep').",
    )
    sources_to_include: Optional[List[str]] = Field(
        default=None,
        description="Specific sources to prioritize or include (e.g., 'wcat', 'canlii').",
    )
    max_results_per_source: int = Field(
        default=10, description="Maximum results to fetch from each source."
    )


class ResearchFinding(BaseModel):
    source_name: str = Field(
        description="Name of the research source (e.g., 'WCAT Decision Search', 'Web Search')."
    )
    title: Optional[str] = Field(default=None, description="Title of the found item.")
    url: Optional[str] = Field(default=None, description="URL of the found item.")
    snippet: Optional[str] = Field(
        default=None, description="A relevant snippet from the content."
    )
    relevance_score: Optional[float] = Field(
        default=None, description="A score indicating relevance to the query."
    )
    full_content_mcp_path: Optional[str] = Field(
        default=None,
        description="MCP path to the full content artifact if saved separately.",
    )


class LegalResearchFindingsSummary(BaseModel):
    research_query_summary: str = Field(
        description="Summary of the initial research query and context."
    )
    findings: List[ResearchFinding] = Field(description="List of research findings.")
    overall_summary: str = Field(
        description="Overall synthesized summary of the research."
    )
    key_insights: List[str] = Field(
        default_factory=list, description="Key insights derived from the research."
    )
    research_time_seconds: Optional[float] = Field(
        default=None, description="Total time taken for research."
    )
    mcp_path_to_full_report: Optional[str] = Field(
        default=None, description="MCP path to a more detailed report artifact."
    )


# --- DataQueryCoordinator I/O Models (Placeholder based on ARCHITECTURE.MD and WORKFLOWS.MD) ---
class QueryAndSynthesizeReportInput(BaseModel):
    intake_summary_mcp_path: Optional[str] = Field(
        default=None, description="MCP path to the document intake summary."
    )
    research_summary_mcp_path: Optional[str] = Field(
        default=None, description="MCP path to the legal research summary."
    )
    user_query_details: str = Field(
        description="Natural language query or specific instructions for querying and synthesis."
    )
    report_format: str = Field(
        default="markdown",
        description="Desired format for the output report (e.g., 'markdown', 'json_summary').",
    )
    target_audience: Optional[str] = Field(
        default=None,
        description="Intended audience for the report (e.g., 'legal_professional', 'client').",
    )


class SynthesizedReportOutput(BaseModel):
    report_artifact_mcp_path: str = Field(
        description="MCP path to the generated report artifact."
    )
    queries_executed_count: int = Field(
        description="Number of distinct queries executed against data stores."
    )
    synthesis_quality_score: Optional[float] = Field(
        default=None, description="Internal score for the quality of synthesis."
    )
    generation_time_seconds: Optional[float] = Field(
        default=None, description="Time taken for querying and synthesis."
    )


# --- Void IDE Integration Models (Phase 1) ---
# This section defines the standardized API contract for communication
# between the AI backend and the Void IDE frontend.

# --- Part Content Schemas (Backend -> Frontend) ---


class PlanPart(BaseModel):
    """A proposed plan of action from the agent."""

    plan: List[str]
    is_approved: bool = False


class StatusPart(BaseModel):
    """A real-time status update on the agent's current activity."""

    message: str
    step: Optional[int] = None
    total_steps: Optional[int] = None


class CodeDiffPart(BaseModel):
    """Represents a code change using a diff format."""

    uri: str  # Typically a file URI e.g., "file:///path/to/file.py"
    diff: str


class FileContentPart(BaseModel):
    """Represents the full content for a file."""

    uri: str  # Typically a file URI
    content: str


class NotificationPart(BaseModel):
    """A toast notification to display to the user."""

    severity: Literal["info", "warn", "error"]
    message: str


class IDECommandPart(BaseModel):
    """Instructs the IDE to run a built-in or custom command."""

    commandId: str
    args: List[Any] = Field(default_factory=list)


class LegalClauseAnalysisPart(BaseModel):
    """In-depth analysis of a specific legal clause."""

    uri: str
    clause_text: str
    analysis: str
    risk_level: Literal["low", "medium", "high"]


class ContractSummaryPart(BaseModel):
    """A high-level summary of a legal document."""

    uri: str
    summary: Dict[str, Any]  # e.g., {"parties": [...], "term_length": "..."}


# --- SkillInvocation Parameter Schemas (Frontend -> Backend) ---


class InlineEditRequest(BaseModel):
    """User wants to modify a selection of code in a file."""

    type: Literal["inline_edit"]
    uri: str
    selection: str
    prompt: str


class CreateFileRequest(BaseModel):
    """User or agent wants to create a new file with initial content."""

    type: Literal["create_file"]
    uri: str
    content: Optional[str] = None


class AnalyzeDocumentRequest(BaseModel):
    """User wants a legal analysis of the specified document."""

    type: Literal["analyze_document"]
    uri: str


class ApprovePlanRequest(BaseModel):
    """User approves a plan proposed by the agent."""

    type: Literal["approve_plan"]
    plan_id: str  # This ID should correlate with a previously sent PlanPart


class ChatRequest(BaseModel):
    """A standard chat message from the user."""

    type: Literal["chat"]
    prompt: str


UserPrompt = Union[
    InlineEditRequest,
    CreateFileRequest,
    AnalyzeDocumentRequest,
    ApprovePlanRequest,
    ChatRequest,
]


class ComprehensiveResearchResult(BaseModel):
    research_summary: str = Field(
        description="A high-level summary of the comprehensive research findings."
    )
    findings: List[ResearchFinding] = Field(
        description="A detailed list of all findings from various sources."
    )
    suggested_next_steps: List[str] = Field(
        default_factory=list,
        description="Suggestions for next steps based on the research.",
    )
    synthesis_quality_score: Optional[float] = Field(
        default=None, description="Internal score for the quality of synthesis."
    )
    generation_time_seconds: Optional[float] = Field(
        default=None, description="Time taken for querying and synthesis."
    )


# --- Resource Manager Models (Placeholder) ---
# Added to resolve dependency for core/resource_manager.py
class AgentTask(BaseModel):
    """Represents a task to be executed by an agent."""

    id: UUID = Field(default_factory=uuid4)
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 1
    parent_workflow_id: Optional[str] = None
