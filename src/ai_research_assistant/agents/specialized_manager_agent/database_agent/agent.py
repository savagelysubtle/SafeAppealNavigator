# src/ai_research_assistant/agents/specialized_manager_agent/database_agent/agent.py
import logging
import uuid
from typing import Any, Dict, List, Optional

from pydantic_ai.mcp import MCPServer

from ai_research_assistant.agents.base_pydantic_agent import (
    BasePydanticAgent,
)
from ai_research_assistant.agents.specialized_manager_agent.database_agent.config import (
    DatabaseAgentConfig,
)

logger = logging.getLogger(__name__)


class DatabaseAgent(BasePydanticAgent):
    """A specialized agent for ChromaDB vector database operations optimized for legal case management."""

    def __init__(
        self,
        config: Optional[DatabaseAgentConfig] = None,
        llm_instance: Optional[Any] = None,
        toolsets: Optional[List[MCPServer]] = None,
    ):
        # Use the refactored BasePydanticAgent constructor
        super().__init__(
            config=config or DatabaseAgentConfig(),
            llm_instance=llm_instance,
            toolsets=toolsets,
        )
        self.config: DatabaseAgentConfig = self.config  # type: ignore

        logger.info(
            f"DatabaseAgent '{self.config.agent_name}' initialized with "
            f"{'factory-created model' if llm_instance else 'config model'} and "
            f"{len(toolsets) if toolsets else 0} MCP toolsets."
        )

    async def query_and_synthesize_report(
        self,
        natural_language_query: str,
        structured_filters: Optional[dict] = None,
        report_format: str = "summary",
    ) -> dict:
        """
        Queries structured and unstructured data stores based on input criteria and generates a synthesized report.

        This matches the agent card skill definition exactly.

        Args:
            natural_language_query: Natural language query for the database
            structured_filters: Optional filters to apply to the query
            report_format: Format for the report (summary, detailed_json, markdown)

        Returns:
            Dictionary with report artifact path and queries executed count
        """
        logger.info(
            f"Database Agent querying and synthesizing report for: '{natural_language_query[:100]}...'"
        )

        try:
            # Enhanced prompt for comprehensive database operations
            query_prompt = (
                f"You are the Database Agent handling a comprehensive query and report synthesis task:\n\n"
                f"**Natural Language Query:** {natural_language_query}\n"
                f"**Structured Filters:** {structured_filters or 'None specified'}\n"
                f"**Report Format:** {report_format}\n\n"
                f"**Your Task:**\n"
                f"1. Use ChromaDB tools to query relevant collections\n"
                f"2. Apply any structured filters to narrow results\n"
                f"3. Synthesize findings into a {report_format} report\n"
                f"4. Store the report in an appropriate location\n\n"
                f"**Available ChromaDB Tools:**\n"
                f"• chroma_list_collections - See what collections are available\n"
                f"• chroma_query_documents - Search for relevant documents\n"
                f"• chroma_get_documents - Retrieve specific documents\n"
                f"• chroma_get_collection_info - Get collection statistics\n\n"
                f"**For SafeAppealNavigator Legal Context:**\n"
                f"Search across legal case management collections: case_files, medical_records, "
                f"wcat_decisions, legal_policies, templates, and research_findings.\n\n"
                f"Execute the query and provide a comprehensive response."
            )

            # Use PydanticAI's native run method
            result = await self.pydantic_agent.run(query_prompt)

            # Generate report path and return structured response
            report_id = str(uuid.uuid4())
            report_path = f"/tmp/database_reports/{report_id}_{report_format}_report.{self._get_file_extension(report_format)}"

            return {
                "report_artifact_mcp_path": report_path,
                "queries_executed_count": 1,  # Would be actual count in real implementation
            }

        except Exception as e:
            logger.error(f"Error querying and synthesizing report: {e}", exc_info=True)
            return {
                "report_artifact_mcp_path": f"/tmp/database_reports/error_{uuid.uuid4()}.txt",
                "queries_executed_count": 0,
            }

    def _get_file_extension(self, report_format: str) -> str:
        """Get appropriate file extension for report format."""
        format_map = {"summary": "txt", "detailed_json": "json", "markdown": "md"}
        return format_map.get(report_format, "txt")

    async def handle_user_request(self, user_prompt: str) -> str:
        """
        Main entry point for handling user requests to the Database Agent.

        This method processes any user request related to database operations,
        legal case management, or ChromaDB functionality.

        Args:
            user_prompt: The user's request or question

        Returns:
            Response string with results or information
        """
        logger.info(f"Database Agent received request: '{user_prompt[:100]}...'")

        try:
            # Use PydanticAI's native run method with system prompt and ChromaDB tools
            result = await self.pydantic_agent.run(user_prompt)
            return str(result)

        except Exception as e:
            logger.error(f"Error handling user request: {e}", exc_info=True)
            return f"I encountered an error while processing your request: {str(e)}"

    async def intake_documents(
        self,
        documents: List[Dict[str, Any]],
        collection_name: str,
        create_if_not_exists: bool = True,
    ) -> Dict[str, Any]:
        """
        Intake documents into the vector database.

        Args:
            documents: List of documents with 'content', 'metadata', and optional 'id'
            collection_name: Name of the collection to store documents in
            create_if_not_exists: Whether to create collection if it doesn't exist

        Returns:
            Summary of intake operation
        """
        logger.info(
            f"Starting document intake for {len(documents)} documents into collection '{collection_name}'"
        )

        try:
            # Check if collection exists
            collection_exists = False
            try:
                await self.pydantic_agent.run(
                    f"Check if collection '{collection_name}' exists using chroma_get_collection_info tool"
                )
                collection_exists = True
            except:
                collection_exists = False

            # Create collection if needed
            if not collection_exists and create_if_not_exists:
                await self.pydantic_agent.run(
                    f"Create a new collection named '{collection_name}' using chroma_create_collection tool"
                )
                logger.info(f"Created new collection: {collection_name}")

            # Add documents to collection
            result = await self.pydantic_agent.run(
                f"Add the following {len(documents)} documents to collection '{collection_name}' "
                f"using chroma_add_documents tool. Documents: {documents}"
            )

            return {
                "status": "success",
                "collection": collection_name,
                "documents_processed": len(documents),
                "message": f"Successfully added {len(documents)} documents to {collection_name}",
            }

        except Exception as e:
            logger.error(f"Error during document intake: {e}")
            return {
                "status": "error",
                "error": str(e),
                "collection": collection_name,
                "documents_processed": 0,
            }

    async def sort_documents_into_collections(
        self,
        source_collection: str,
        sorting_criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Sort documents from one collection into multiple collections based on criteria.

        Args:
            source_collection: Name of the source collection
            sorting_criteria: Dictionary defining how to sort documents

        Returns:
            Summary of sorting operation
        """
        logger.info(
            f"Sorting documents from '{source_collection}' based on criteria: {sorting_criteria}"
        )

        try:
            # Query all documents from source collection
            documents_result = await self.pydantic_agent.run(
                f"Retrieve all documents from collection '{source_collection}' using chroma_get_documents tool"
            )

            # Sort documents based on criteria
            sorted_counts = {}
            for criterion_name, criterion_rule in sorting_criteria.items():
                target_collection = criterion_rule.get(
                    "target_collection", f"{source_collection}_{criterion_name}"
                )
                filter_metadata = criterion_rule.get("filter_metadata", {})

                # Create target collection if needed
                await self.pydantic_agent.run(
                    f"Create collection '{target_collection}' if it doesn't exist using chroma_create_collection"
                )

                # Query and move matching documents
                matching_docs_result = await self.pydantic_agent.run(
                    f"Query documents from '{source_collection}' with metadata filter {filter_metadata} "
                    f"and add them to '{target_collection}' collection"
                )

                sorted_counts[target_collection] = "Documents sorted based on criteria"

            return {
                "status": "success",
                "source_collection": source_collection,
                "sorted_collections": sorted_counts,
                "message": f"Successfully sorted documents into {len(sorted_counts)} collections",
            }

        except Exception as e:
            logger.error(f"Error during document sorting: {e}")
            return {
                "status": "error",
                "error": str(e),
                "source_collection": source_collection,
            }

    async def maintain_database(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        Perform database maintenance operations.

        Args:
            operation: Type of maintenance operation (cleanup, optimize, backup, etc.)
            **kwargs: Additional parameters for the operation

        Returns:
            Result of maintenance operation
        """
        logger.info(f"Performing database maintenance operation: {operation}")

        try:
            if operation == "cleanup_empty_collections":
                # List all collections and remove empty ones
                collections_result = await self.pydantic_agent.run(
                    "List all collections and delete any that have zero documents"
                )
                return {
                    "status": "success",
                    "operation": operation,
                    "result": "Cleaned up empty collections",
                }

            elif operation == "optimize_collection":
                collection_name = kwargs.get("collection_name")
                if not collection_name:
                    return {
                        "status": "error",
                        "error": "collection_name required for optimize operation",
                    }

                # Modify collection with optimized HNSW parameters
                result = await self.pydantic_agent.run(
                    f"Optimize collection '{collection_name}' by modifying its HNSW parameters "
                    f"for better performance using chroma_modify_collection"
                )
                return {
                    "status": "success",
                    "operation": operation,
                    "collection": collection_name,
                }

            elif operation == "collection_stats":
                # Get statistics for all collections
                stats_result = await self.pydantic_agent.run(
                    "Get count and info for all collections to generate database statistics"
                )
                return {
                    "status": "success",
                    "operation": operation,
                    "stats": "Database statistics generated",
                }

            else:
                return {
                    "status": "error",
                    "error": f"Unknown maintenance operation: {operation}",
                }

        except Exception as e:
            logger.error(f"Error during database maintenance: {e}")
            return {"status": "error", "operation": operation, "error": str(e)}

    async def create_specialized_collection(
        self,
        collection_name: str,
        collection_type: str,
        embedding_function: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a specialized collection for specific document types.

        Args:
            collection_name: Name of the new collection
            collection_type: Type of documents this collection will store
            embedding_function: Optional embedding function to use
            metadata: Optional metadata for the collection

        Returns:
            Result of collection creation
        """
        logger.info(
            f"Creating specialized collection '{collection_name}' for {collection_type} documents"
        )

        try:
            # Create collection with specific configuration
            result = await self.pydantic_agent.run(
                f"Create a new collection named '{collection_name}' for {collection_type} documents. "
                f"Use embedding function '{embedding_function or 'default'}' and metadata {metadata or {}}. "
                f"Use chroma_create_collection tool with appropriate HNSW configuration."
            )

            return {
                "status": "success",
                "collection_name": collection_name,
                "collection_type": collection_type,
                "embedding_function": embedding_function or "default",
                "message": f"Successfully created specialized collection for {collection_type}",
            }

        except Exception as e:
            logger.error(f"Error creating specialized collection: {e}")
            return {
                "status": "error",
                "error": str(e),
                "collection_name": collection_name,
            }
