# src/ai_research_assistant/agents/specialized_manager_agent/database_agent/agent.py
import logging
from typing import Any, Dict, List, Optional

from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent
from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)

logger = logging.getLogger(__name__)


class DatabaseAgentConfig(BasePydanticAgentConfig):
    agent_name: str = "DatabaseAgent"
    agent_id: str = "database_agent_instance_001"
    pydantic_ai_system_prompt: str = (
        "You are a Database Agent responsible for managing the Chroma vector database. "
        "Your primary responsibilities are:\n"
        "1. Document intake - receiving and storing documents in appropriate collections\n"
        "2. Document sorting - organizing documents into collections based on type, content, or metadata\n"
        "3. Database maintenance - creating, modifying, and managing collections\n"
        "4. Vector operations - adding embeddings and managing vector search capabilities\n\n"
        "You work closely with the Document Agent who handles file I/O operations. "
        "You receive processed documents and store them efficiently in the vector database for retrieval."
    )


class DatabaseAgent(BasePydanticAgent):
    def __init__(self, config: Optional[DatabaseAgentConfig] = None):
        super().__init__(config=config or DatabaseAgentConfig())
        self.agent_config: DatabaseAgentConfig = self.config  # type: ignore
        logger.info(f"DatabaseAgent '{self.agent_name}' initialized with Chroma tools.")

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
                    user_prompt=f"Check if collection '{collection_name}' exists using chroma_get_collection_info tool"
                )
                collection_exists = True
            except:
                collection_exists = False

            # Create collection if needed
            if not collection_exists and create_if_not_exists:
                await self.pydantic_agent.run(
                    user_prompt=f"Create a new collection named '{collection_name}' using chroma_create_collection tool"
                )
                logger.info(f"Created new collection: {collection_name}")

            # Add documents to collection
            result = await self.pydantic_agent.run(
                user_prompt=(
                    f"Add the following {len(documents)} documents to collection '{collection_name}' "
                    f"using chroma_add_documents tool. Documents: {documents}"
                )
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
                user_prompt=f"Retrieve all documents from collection '{source_collection}' using chroma_get_documents tool"
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
                    user_prompt=f"Create collection '{target_collection}' if it doesn't exist using chroma_create_collection"
                )

                # Query and move matching documents
                matching_docs_result = await self.pydantic_agent.run(
                    user_prompt=(
                        f"Query documents from '{source_collection}' with metadata filter {filter_metadata} "
                        f"and add them to '{target_collection}' collection"
                    )
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
                    user_prompt="List all collections and delete any that have zero documents"
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
                    user_prompt=(
                        f"Optimize collection '{collection_name}' by modifying its HNSW parameters "
                        f"for better performance using chroma_modify_collection"
                    )
                )
                return {
                    "status": "success",
                    "operation": operation,
                    "collection": collection_name,
                }

            elif operation == "collection_stats":
                # Get statistics for all collections
                stats_result = await self.pydantic_agent.run(
                    user_prompt="Get count and info for all collections to generate database statistics"
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
                user_prompt=(
                    f"Create a new collection named '{collection_name}' for {collection_type} documents. "
                    f"Use embedding function '{embedding_function or 'default'}' and metadata {metadata or {}}. "
                    f"Use chroma_create_collection tool with appropriate HNSW configuration."
                )
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
