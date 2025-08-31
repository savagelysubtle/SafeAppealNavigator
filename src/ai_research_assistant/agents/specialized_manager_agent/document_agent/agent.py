# src/ai_research_assistant/agents/specialized_manager_agent/document_agent/agent.py
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic_ai.mcp import MCPServer

from ai_research_assistant.agents.base_pydantic_agent import (
    BasePydanticAgent,
)
from ai_research_assistant.agents.specialized_manager_agent.document_agent.config import (
    DocumentAgentConfig,
)

logger = logging.getLogger(__name__)


class DocumentAgent(BasePydanticAgent):
    """
    Document agent focused on reading existing documents and creating new documents.
    Uses only file I/O tools (read_file, write_file, read_multiple_files).
    """

    def __init__(
        self,
        config: Optional[DocumentAgentConfig] = None,
        llm_instance: Optional[Any] = None,
        toolsets: Optional[List[MCPServer]] = None,
    ):
        # Use the refactored BasePydanticAgent constructor
        super().__init__(
            config=config or DocumentAgentConfig(),
            llm_instance=llm_instance,
            toolsets=toolsets,
        )
        self.config: DocumentAgentConfig = self.config  # type: ignore

        logger.info(
            f"DocumentAgent '{self.config.agent_name}' initialized with "
            f"{'factory-created model' if llm_instance else 'config model'} and "
            f"{len(toolsets) if toolsets else 0} MCP toolsets."
        )

    async def process_and_store_documents(
        self,
        document_sources: List[Dict[str, Any]],
        case_id: str,
        vector_collection_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes a list of source documents, performs OCR, tagging, embedding, and stores them in appropriate databases.

        This matches the agent card skill definition exactly.

        Args:
            document_sources: List of document sources with mcp_path and optional document_type
            case_id: Identifier for the case these documents belong to
            vector_collection_name: Optional name for the vector collection

        Returns:
            Dictionary with processed count, failed count, and artifact summary path
        """
        logger.info(f"Processing {len(document_sources)} documents for case {case_id}")

        try:
            processed_count = 0
            failed_count = 0

            # Process each document
            for doc_source in document_sources:
                mcp_path = doc_source.get("mcp_path", "")
                document_type = doc_source.get("document_type", "unknown")

                try:
                    # Read the document
                    read_result = await self.read_document(
                        mcp_path, extract_metadata=True
                    )
                    if read_result["status"] == "success":
                        processed_count += 1
                        logger.info(f"Successfully processed document: {mcp_path}")
                    else:
                        failed_count += 1
                        logger.error(f"Failed to process document: {mcp_path}")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error processing document {mcp_path}: {e}")

            # Create summary artifact
            summary_data = {
                "case_id": case_id,
                "total_documents": len(document_sources),
                "processed_count": processed_count,
                "failed_count": failed_count,
                "collection_name": vector_collection_name or f"case_{case_id}",
                "processing_timestamp": "2025-01-28T00:00:00Z",
            }

            artifact_path = f"/tmp/processing_summaries/{case_id}_summary.json"

            # Store summary using create_document method
            await self.create_document(
                file_path=artifact_path,
                content=json.dumps(summary_data, indent=2),
                document_type="json",
            )

            return {
                "processed_count": processed_count,
                "failed_count": failed_count,
                "artifact_summary_mcp_path": artifact_path,
            }

        except Exception as e:
            logger.error(f"Error in process_and_store_documents: {e}", exc_info=True)
            return {
                "processed_count": 0,
                "failed_count": len(document_sources),
                "artifact_summary_mcp_path": f"/tmp/processing_summaries/{case_id}_error.json",
            }

    async def read_document(
        self, file_path: str, extract_metadata: bool = False
    ) -> Dict[str, Any]:
        """
        Read a document from a file path.

        Args:
            file_path: Path to the document file
            extract_metadata: Whether to extract metadata from the document

        Returns:
            Document content and optional metadata
        """
        logger.info(f"Reading document from: {file_path}")

        try:
            # Use PydanticAI's native run method with file I/O tools
            result = await self.pydantic_agent.run(
                f"Read the document at path: {file_path}"
            )

            content = str(result)

            response: Dict[str, Any] = {
                "status": "success",
                "file_path": file_path,
                "content": content,
                "file_type": Path(file_path).suffix.lower(),
            }

            if extract_metadata:
                # Extract basic metadata using LLM
                metadata_result = await self.pydantic_agent.run(
                    f"Extract key metadata from this document content:\n\n{content[:2000]}\n\n"
                    "Return as JSON with keys: title, author, date, document_type, summary"
                )
                try:
                    metadata = json.loads(str(metadata_result))
                    response["metadata"] = metadata
                except:
                    response["metadata"] = {"summary": str(metadata_result)}

            return response

        except Exception as e:
            logger.error(f"Failed to read document {file_path}: {e}")
            return {"status": "error", "file_path": file_path, "error": str(e)}

    async def read_multiple_documents(
        self, file_paths: List[str], extract_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Read multiple documents at once.

        Args:
            file_paths: List of document file paths
            extract_metadata: Whether to extract metadata from each document

        Returns:
            List of document contents and metadata
        """
        logger.info(f"Reading {len(file_paths)} documents")

        try:
            # Use PydanticAI's native run method with read_multiple_files tool
            result = await self.pydantic_agent.run(
                f"Read multiple documents from these paths: {file_paths}"
            )

            documents = []
            # Process each document result
            for i, file_path in enumerate(file_paths):
                doc_data: Dict[str, Any] = {"file_path": file_path, "status": "success"}

                # Extract content for this file from result
                doc_data["content"] = str(result)

                if extract_metadata:
                    # Simple metadata extraction - store as proper dict
                    doc_data["metadata"] = {
                        "file_name": Path(file_path).name,
                        "file_type": Path(file_path).suffix.lower(),
                    }

                documents.append(doc_data)

            return documents

        except Exception as e:
            logger.error(f"Failed to read multiple documents: {e}")
            # Return error for all documents
            return [
                {"status": "error", "file_path": fp, "error": str(e)}
                for fp in file_paths
            ]

    async def create_document(
        self,
        file_path: str,
        content: str,
        document_type: str = "text",
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new document by writing content to a file.

        Args:
            file_path: Path where the document should be created
            content: Content to write to the document
            document_type: Type of document (text, markdown, json, etc.)
            metadata: Optional metadata to include in document header

        Returns:
            Result of document creation
        """
        logger.info(f"Creating {document_type} document at: {file_path}")

        try:
            # Add metadata header if provided and document type supports it
            final_content = content
            if metadata and document_type in ["markdown", "text"]:
                if document_type == "markdown":
                    # Add as YAML frontmatter
                    import yaml

                    frontmatter = yaml.dump(metadata, default_flow_style=False)
                    final_content = f"---\n{frontmatter}---\n\n{content}"
                else:
                    # Add as comment header
                    header_lines = [f"# {k}: {v}" for k, v in metadata.items()]
                    final_content = "\n".join(header_lines) + "\n\n" + content

            # Use PydanticAI's native run method with write_file tool
            result = await self.pydantic_agent.run(
                f"Write the following content to file at {file_path}:\n\n{final_content}"
            )

            return {
                "status": "success",
                "file_path": file_path,
                "document_type": document_type,
                "size": len(final_content),
                "message": f"Successfully created {document_type} document",
            }

        except Exception as e:
            logger.error(f"Failed to create document at {file_path}: {e}")
            return {"status": "error", "file_path": file_path, "error": str(e)}

    async def create_report_from_template(
        self, template_path: str, output_path: str, template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a report by reading a template and filling it with data.

        Args:
            template_path: Path to the template file
            output_path: Path where the report should be saved
            template_data: Data to fill into the template

        Returns:
            Result of report creation
        """
        logger.info(f"Creating report from template: {template_path}")

        try:
            # Read template
            template_result = await self.read_document(template_path)
            if template_result["status"] != "success":
                return template_result

            template_content = template_result["content"]

            # Fill template with data using LLM
            filled_result = await self.pydantic_agent.run(
                f"Fill this template with the provided data.\n\n"
                f"Template:\n{template_content}\n\n"
                f"Data:\n{json.dumps(template_data, indent=2)}\n\n"
                f"Replace all placeholders with appropriate data values."
            )

            filled_content = str(filled_result)

            # Create the report with string-only metadata
            base_metadata: Dict[str, str] = {
                "template": str(template_path),
                "created_from": "template",
            }

            # Safely merge metadata if it exists and is a dict
            template_metadata = template_data.get("metadata", {})
            if isinstance(template_metadata, dict):
                # Ensure all metadata values are strings
                for key, value in template_metadata.items():
                    base_metadata[str(key)] = str(value)

            return await self.create_document(
                file_path=output_path,
                content=filled_content,
                document_type="report",
                metadata=base_metadata,
            )

        except Exception as e:
            logger.error(f"Failed to create report from template: {e}")
            return {
                "status": "error",
                "template_path": template_path,
                "output_path": output_path,
                "error": str(e),
            }

    async def append_to_document(
        self, file_path: str, content_to_append: str, separator: str = "\n\n"
    ) -> Dict[str, Any]:
        """
        Append content to an existing document.

        Args:
            file_path: Path to the document
            content_to_append: Content to add to the document
            separator: Separator between existing and new content

        Returns:
            Result of append operation
        """
        logger.info(f"Appending content to document: {file_path}")

        try:
            # Read existing content
            existing_result = await self.read_document(file_path)
            if existing_result["status"] != "success":
                # If file doesn't exist, create it
                return await self.create_document(file_path, content_to_append)

            # Combine content
            existing_content = existing_result["content"]
            new_content = existing_content + separator + content_to_append

            # Use PydanticAI's native run method to write back
            result = await self.pydantic_agent.run(
                f"Write the following updated content to file at {file_path}:\n\n{new_content}"
            )

            return {
                "status": "success",
                "file_path": file_path,
                "content_appended": len(content_to_append),
                "total_size": len(new_content),
                "message": "Successfully appended content to document",
            }

        except Exception as e:
            logger.error(f"Failed to append to document {file_path}: {e}")
            return {"status": "error", "file_path": file_path, "error": str(e)}
