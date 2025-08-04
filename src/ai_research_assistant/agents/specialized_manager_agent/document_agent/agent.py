# src/ai_research_assistant/agents/specialized_manager_agent/document_agent/agent.py
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field
from pydantic_ai.tools import Tool as PydanticAITool

from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent
from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)

logger = logging.getLogger(__name__)


class DocumentAgentConfig(BasePydanticAgentConfig):
    """Configuration for the DocumentAgent."""

    agent_name: str = "DocumentAgent"
    agent_id: str = Field(default_factory=lambda: f"doc_agent_{uuid.uuid4()}")

    pydantic_ai_system_prompt: str = (
        "You are a Document Agent focused exclusively on reading existing documents "
        "and creating new documents. Your responsibilities are:\n"
        "1. Reading document content from files using read_file tools\n"
        "2. Creating new documents by writing content to files using write_file tools\n"
        "3. Reading multiple related documents when needed\n\n"
        "You work closely with the Database Agent who handles document storage and retrieval "
        "in the vector database. You only handle file I/O operations - reading and writing documents. "
        "You do NOT manage databases, embeddings, or document organization."
    )


class DocumentAgent(BasePydanticAgent):
    """
    Document agent focused on reading existing documents and creating new documents.
    Uses only file I/O tools (read_file, write_file, read_multiple_files).
    """

    def __init__(self, config: Optional[DocumentAgentConfig] = None):
        super().__init__(config=config or DocumentAgentConfig())
        self.agent_config: DocumentAgentConfig = self.config  # type: ignore
        logger.info(
            f"DocumentAgent '{self.agent_name}' initialized with file I/O tools."
        )

    def _get_initial_tools(self) -> List[PydanticAITool]:
        """Get MCP tools from parent class - will automatically get file I/O tools."""
        return super()._get_initial_tools()

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
            # Use the appropriate read tool based on available MCP servers
            result = await self.pydantic_agent.run(
                user_prompt=f"Read the document at path: {file_path}"
            )

            content = result.data if hasattr(result, "data") else str(result)

            response: Dict[str, Any] = {
                "status": "success",
                "file_path": file_path,
                "content": content,
                "file_type": Path(file_path).suffix.lower(),
            }

            if extract_metadata:
                # Extract basic metadata using LLM
                metadata_result = await self.pydantic_agent.run(
                    user_prompt=(
                        f"Extract key metadata from this document content:\n\n{content[:2000]}\n\n"
                        "Return as JSON with keys: title, author, date, document_type, summary"
                    )
                )
                try:
                    metadata = json.loads(str(metadata_result.data))
                    response["metadata"] = metadata
                except:
                    response["metadata"] = {"summary": str(metadata_result.data)}

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
            # Use read_multiple_files tool if available
            result = await self.pydantic_agent.run(
                user_prompt=f"Read multiple documents from these paths: {file_paths}"
            )

            documents = []
            # Process each document result
            for i, file_path in enumerate(file_paths):
                doc_data = {"file_path": file_path, "status": "success"}

                # Extract content for this file from result
                if hasattr(result, "data") and isinstance(result.data, list):
                    doc_data["content"] = result.data[i] if i < len(result.data) else ""
                else:
                    doc_data["content"] = str(result)

                if extract_metadata:
                    # Simple metadata extraction
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
        metadata: Optional[Dict[str, Any]] = None,
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

            # Write document using write_file tool
            result = await self.pydantic_agent.run(
                user_prompt=f"Write the following content to file at {file_path}:\n\n{final_content}"
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
                user_prompt=(
                    f"Fill this template with the provided data.\n\n"
                    f"Template:\n{template_content}\n\n"
                    f"Data:\n{json.dumps(template_data, indent=2)}\n\n"
                    f"Replace all placeholders with appropriate data values."
                )
            )

            filled_content = (
                filled_result.data
                if hasattr(filled_result, "data")
                else str(filled_result)
            )

            # Create the report
            return await self.create_document(
                file_path=output_path,
                content=filled_content,
                document_type="report",
                metadata={
                    "template": template_path,
                    "created_from": "template",
                    **template_data.get("metadata", {}),
                },
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

            # Write back
            result = await self.pydantic_agent.run(
                user_prompt=f"Write the following updated content to file at {file_path}:\n\n{new_content}"
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
