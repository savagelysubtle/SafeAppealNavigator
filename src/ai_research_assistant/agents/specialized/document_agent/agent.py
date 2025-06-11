# src/ai_research_assistant/agents/document_processing_coordinator/agent.py
import asyncio
import io
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pypdf
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import Field
from pydantic_ai.tools import Tool as PydanticAITool

from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent
from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
from ai_research_assistant.agents.document_agent.prompts import (
    EXTRACT_METADATA_FROM_TEXT_PROMPT,
)
from ai_research_assistant.config.global_settings import settings
from ai_research_assistant.core.mcp_client import fetch_and_wrap_mcp_tools
from ai_research_assistant.core.models import (
    DocumentProcessingSummary,
    DocumentSourceInfo,
    ProcessAndStoreDocumentsInput,
    ProcessedDocumentInfo,
)

logger = logging.getLogger(__name__)


class DocumentProcessingCoordinatorConfig(BasePydanticAgentConfig):
    """Configuration for the DocumentProcessingCoordinator."""

    agent_name: str = "DocumentProcessingCoordinator"
    agent_id: str = Field(default_factory=lambda: f"doc_proc_coord_{uuid.uuid4()}")
    default_artifact_storage_mcp_path: str = "/mcp/artifacts/"
    default_text_splitter_chunk_size: int = 1500
    default_text_splitter_chunk_overlap: int = 150

    pydantic_ai_system_prompt: str = (
        "You are an expert at analyzing and extracting structured metadata from unstructured text. "
        "Based on the provided text, you will identify key information as requested in the user prompt "
        "and respond in JSON format."
    )


class DocumentProcessingCoordinator(BasePydanticAgent):
    """
    Coordinates the entire document intake pipeline: ingestion, OCR, metadata tagging,
    chunking, and embedding for legal documents.
    """

    def __init__(self, config: Optional[DocumentProcessingCoordinatorConfig] = None):
        super().__init__(config=config or DocumentProcessingCoordinatorConfig())
        self.coordinator_config: DocumentProcessingCoordinatorConfig = self.config  # type: ignore
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.coordinator_config.default_text_splitter_chunk_size,
            chunk_overlap=self.coordinator_config.default_text_splitter_chunk_overlap,
            length_function=len,
        )
        logger.info(f"DocumentProcessingCoordinator '{self.agent_name}' initialized.")

    def _get_initial_tools(self) -> List[PydanticAITool]:
        base_tools = super()._get_initial_tools()
        try:
            mcp_tools = asyncio.run(fetch_and_wrap_mcp_tools(settings.MCP_SERVER_URL))
        except Exception as e:
            logger.error(f"Failed to fetch MCP tools: {e}")
            mcp_tools = []
        logger.info(f"{self.agent_name} initialized with {len(mcp_tools)} MCP tools.")
        return base_tools + mcp_tools

    async def _read_document(
        self, source_info: DocumentSourceInfo, ocr_enabled: bool
    ) -> Dict[str, Any]:
        """Reads a document from an MCP path and returns its content and type."""
        logger.info(f"Reading document from: {source_info.mcp_path}")
        try:
            read_result = await self.run_tool(
                "read_mcp_file", mcp_path=source_info.mcp_path
            )
            content_bytes = read_result.get("content")
            if not content_bytes:
                raise ValueError("MCP file read returned no content.")
            file_type = (
                source_info.document_type
                or Path(source_info.original_filename or source_info.mcp_path).suffix
            ).lower()
            text_content = ""
            if file_type == ".pdf":
                reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                text_content = "".join(page.extract_text() for page in reader.pages)
                if not text_content.strip() and ocr_enabled:
                    logger.warning(
                        "PDF appears to be image-based. OCR is a placeholder."
                    )
                    text_content = "[OCR Placeholder: This PDF requires OCR processing]"
            else:
                text_content = content_bytes.decode("utf-8", errors="ignore")
            return {"text": text_content, "type": file_type, "error": None}
        except Exception as e:
            logger.error(f"Failed to read/process document {source_info.mcp_path}: {e}")
            return {"text": None, "type": None, "error": str(e)}

    async def _extract_metadata(self, text_snippet: str) -> Dict[str, Any]:
        """Extracts metadata from text using an LLM call."""
        try:
            prompt = EXTRACT_METADATA_FROM_TEXT_PROMPT.format(
                document_text_snippet=text_snippet
            )
            llm_result = await self.pydantic_agent.run(prompt=prompt)
            return json.loads(llm_result.output)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(
                f"LLM metadata extraction/parsing failed: {e}. Raw output: {llm_result.output}"
            )
            return {"error": f"Failed to parse LLM metadata output: {e}"}
        except Exception as e:
            logger.error(f"LLM metadata extraction failed: {e}")
            return {"error": str(e)}

    async def _store_artifact(self, content: str, case_id: str, filename: str) -> str:
        """Stores a text artifact using an MCP tool and returns its path."""
        storage_path = self.coordinator_config.default_artifact_storage_mcp_path
        mcp_path = f"{storage_path.rstrip('/')}/{case_id}/{filename}"
        await self.run_tool("write_mcp_file", mcp_path=mcp_path, content=content)
        return mcp_path

    async def _chunk_and_embed(
        self, text: str, collection_name: str, metadata: Dict[str, Any]
    ) -> List[str]:
        """Chunks text and stores embeddings in a vector DB via an MCP tool."""
        chunks = self.text_splitter.split_text(text)
        logger.info(f"Split text into {len(chunks)} chunks.")
        result = await self.run_tool(
            "add_texts_to_vector_db",
            collection_name=collection_name,
            texts=chunks,
            metadatas=[metadata] * len(chunks),
        )
        chunk_ids = result.get("ids", [])
        if not chunk_ids:
            raise ValueError("Failed to get chunk IDs from vector DB.")
        logger.info(f"Stored {len(chunk_ids)} chunks in vector DB.")
        return chunk_ids

    async def process_and_store_documents(
        self, input_data: ProcessAndStoreDocumentsInput
    ) -> Dict[str, Any]:
        """
        Manages the full lifecycle of document intake, from raw files to indexed embeddings.
        """
        start_time = time.time()
        logger.info(
            f"Starting document processing for case '{input_data.case_id}' with {len(input_data.document_sources)} documents."
        )
        processed_docs_info: List[ProcessedDocumentInfo] = []
        errors_summary: List[str] = []
        for source_info in input_data.document_sources:
            doc_id, process_status, error_msg = str(uuid.uuid4()), "success", None
            text_mcp_path, meta_mcp_path, doc_type = "", "", ""
            vdb_chunk_ids: List[str] = []
            try:
                read_output = await self._read_document(
                    source_info, input_data.ocr_enabled
                )
                if read_output["error"]:
                    raise Exception(f"Read error: {read_output['error']}")
                doc_text, doc_type = read_output["text"], read_output["type"]
                text_filename = f"{doc_id}_extracted_text.txt"
                text_mcp_path = await self._store_artifact(
                    doc_text, input_data.case_id, text_filename
                )
                metadata = await self._extract_metadata(doc_text[:4096])
                if metadata.get("error"):
                    raise Exception(f"Metadata extraction error: {metadata['error']}")
                metadata["source_mcp_path"] = source_info.mcp_path
                metadata["original_filename"] = source_info.original_filename
                meta_filename = f"{doc_id}_metadata.json"
                meta_mcp_path = await self._store_artifact(
                    json.dumps(metadata, indent=2), input_data.case_id, meta_filename
                )
                vdb_chunk_ids = await self._chunk_and_embed(
                    doc_text, input_data.target_vector_collection, metadata
                )
            except Exception as e:
                logger.error(
                    f"Failed to process document {source_info.mcp_path}: {e}",
                    exc_info=True,
                )
                process_status = "failed"
                error_msg = str(e)
                errors_summary.append(f"{source_info.mcp_path}: {error_msg}")
            processed_docs_info.append(
                ProcessedDocumentInfo(
                    source_path=source_info.mcp_path,
                    document_type=doc_type,
                    text_artifact_mcp_path=text_mcp_path,
                    metadata_artifact_mcp_path=meta_mcp_path,
                    vector_db_chunk_ids=vdb_chunk_ids,
                    status=process_status,
                    error_message=error_msg,
                )
            )
        end_time = time.time()
        successful_count = sum(1 for d in processed_docs_info if d.status == "success")
        failed_count = len(processed_docs_info) - successful_count
        summary = DocumentProcessingSummary(
            case_id=input_data.case_id,
            processed_documents=processed_docs_info,
            overall_status="CompletedWithErrors" if failed_count > 0 else "Completed",
            total_documents_input=len(input_data.document_sources),
            total_documents_processed_successfully=successful_count,
            total_documents_failed=failed_count,
            errors_summary=errors_summary,
            processing_time_seconds=end_time - start_time,
        )
        return summary.model_dump(exclude_none=True)
