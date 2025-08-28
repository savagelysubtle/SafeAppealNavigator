# FILE: src/ai_research_assistant/agents/specialized_manager_agent/database_agent/prompts.py

"""
Database Agent Prompts and ChromaDB Operation Patterns

This module contains specialized prompts and operation patterns for the Database Agent.
The Database Agent is responsible for all ChromaDB vector database operations including
collection management, document storage, vector search, and database maintenance.

Key Responsibilities:
- ChromaDB collection creation and management
- Document intake and storage with embeddings
- Vector similarity search operations
- Database optimization and maintenance
- Metadata management and filtering
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ============================================================================
# CHROMADB OPERATION PATTERNS
# ============================================================================

CHROMADB_OPERATIONS = {
    "collection_management": {
        "create_collection": {
            "prompt_template": (
                "I need to create a new ChromaDB collection called '{collection_name}'. "
                "Let me use the chroma_create_collection tool with the following specifications:\n\n"
                "**Collection Name**: {collection_name}\n"
                "**Purpose**: {purpose}\n"
                "**Embedding Function**: {embedding_function}\n"
                "**Distance Metric**: {distance_metric}\n\n"
                "I'll create this collection with optimal HNSW parameters for {use_case} workloads."
            ),
            "success_response": (
                "✅ **Collection Created Successfully**\n\n"
                "**Collection**: {collection_name}\n"
                "**Status**: Ready for document intake\n"
                "**Embedding Model**: {embedding_function}\n"
                "**Optimization**: Configured for {use_case}\n\n"
                "The collection is now ready to receive documents. You can add documents using the document intake functionality."
            ),
            "error_response": (
                "❌ **Collection Creation Failed**\n\n"
                "**Error**: {error_message}\n"
                "**Collection**: {collection_name}\n"
                "**Troubleshooting**: {troubleshooting_steps}\n\n"
                "Please check the collection name and parameters, then try again."
            ),
        },
        "list_collections": {
            "prompt_template": (
                "I'll retrieve information about all ChromaDB collections using the chroma_list_collections tool. "
                "This will show you all available collections, their document counts, and metadata."
            ),
            "success_response": (
                "📋 **Available Collections**\n\n"
                "{collections_list}\n\n"
                "**Total Collections**: {total_count}\n"
                "**Total Documents**: {total_documents}\n\n"
                "Which collection would you like to work with?"
            ),
        },
        "delete_collection": {
            "prompt_template": (
                "⚠️ **Collection Deletion Request**\n\n"
                "You want to delete collection '{collection_name}'. This action is **irreversible** and will:\n"
                "• Remove all documents in the collection\n"
                "• Delete all embeddings and metadata\n"
                "• Cannot be undone\n\n"
                "Are you sure you want to proceed? If yes, I'll use the chroma_delete_collection tool."
            ),
            "confirmation_required": True,
            "success_response": (
                "🗑️ **Collection Deleted**\n\n"
                "**Collection**: {collection_name}\n"
                "**Status**: Permanently removed\n"
                "**Documents Removed**: {document_count}\n\n"
                "The collection and all its data have been permanently deleted."
            ),
        },
    },
    "document_operations": {
        "add_documents": {
            "prompt_template": (
                "I'll add {document_count} documents to the '{collection_name}' collection. "
                "Let me use the chroma_add_documents tool to store these documents with embeddings:\n\n"
                "**Collection**: {collection_name}\n"
                "**Documents**: {document_count} items\n"
                "**Processing**: Generating embeddings and storing with metadata\n\n"
                "This may take a moment depending on document size and count."
            ),
            "batch_processing": {
                "small_batch": "Processing {count} documents in single batch",
                "large_batch": "Processing {count} documents in {batch_count} batches for optimal performance",
                "batch_size": 100,
            },
            "success_response": (
                "📄 **Documents Added Successfully**\n\n"
                "**Collection**: {collection_name}\n"
                "**Documents Added**: {document_count}\n"
                "**Embeddings Generated**: ✅\n"
                "**Metadata Stored**: ✅\n\n"
                "All documents are now searchable in the vector database."
            ),
        },
        "update_documents": {
            "prompt_template": (
                "I'll update existing documents in the '{collection_name}' collection. "
                "Using the chroma_update_documents tool to modify:\n\n"
                "**Documents to Update**: {document_ids}\n"
                "**Updates**: {update_fields}\n"
                "**Re-embedding**: {needs_reembedding}\n\n"
                "This will preserve document IDs while updating content and metadata."
            )
        },
        "get_documents": {
            "prompt_template": (
                "I'll retrieve documents from the '{collection_name}' collection. "
                "Using the chroma_get_documents tool with these parameters:\n\n"
                "**Collection**: {collection_name}\n"
                "**Filter**: {filter_criteria}\n"
                "**Limit**: {limit}\n"
                "**Include**: {include_fields}\n\n"
                "Fetching matching documents..."
            )
        },
    },
    "search_operations": {
        "vector_search": {
            "prompt_template": (
                "I'll perform a vector similarity search in the '{collection_name}' collection. "
                "Using the chroma_query_documents tool to find documents similar to your query:\n\n"
                "**Query**: {query_text}\n"
                "**Collection**: {collection_name}\n"
                "**Results**: Top {n_results} matches\n"
                "**Filters**: {filter_criteria}\n\n"
                "Searching for semantically similar content..."
            ),
            "success_response": (
                "🔍 **Vector Search Results**\n\n"
                "**Query**: {query_text}\n"
                "**Collection**: {collection_name}\n"
                "**Found**: {result_count} matches\n\n"
                "{search_results}\n\n"
                "Results are ranked by semantic similarity score."
            ),
        },
        "metadata_filter": {
            "prompt_template": (
                "I'll search documents using metadata filters in the '{collection_name}' collection. "
                "Using chroma_get_documents with these filter criteria:\n\n"
                "**Collection**: {collection_name}\n"
                "**Metadata Filters**: {metadata_filters}\n"
                "**Expected Results**: Documents matching filter criteria\n\n"
                "Applying filters to find matching documents..."
            )
        },
        "hybrid_search": {
            "prompt_template": (
                "I'll perform a hybrid search combining vector similarity and metadata filtering:\n\n"
                "**Vector Query**: {query_text}\n"
                "**Metadata Filters**: {metadata_filters}\n"
                "**Collection**: {collection_name}\n"
                "**Strategy**: Find semantically similar documents that also match metadata criteria\n\n"
                "Running hybrid search for optimal precision..."
            )
        },
    },
    "maintenance_operations": {
        "optimize_collection": {
            "prompt_template": (
                "I'll optimize the '{collection_name}' collection for better performance. "
                "Using chroma_modify_collection to update HNSW parameters:\n\n"
                "**Collection**: {collection_name}\n"
                "**Current Size**: {document_count} documents\n"
                "**Optimization**: {optimization_type}\n"
                "**Expected Benefit**: {expected_improvement}\n\n"
                "Applying optimization settings..."
            ),
            "optimization_types": {
                "search_speed": {
                    "hnsw_m": 32,
                    "hnsw_ef_construction": 100,
                    "description": "Optimized for faster search queries",
                },
                "accuracy": {
                    "hnsw_m": 64,
                    "hnsw_ef_construction": 200,
                    "description": "Optimized for higher search accuracy",
                },
                "balanced": {
                    "hnsw_m": 48,
                    "hnsw_ef_construction": 150,
                    "description": "Balanced speed and accuracy",
                },
            },
        },
        "collection_stats": {
            "prompt_template": (
                "I'll gather comprehensive statistics for the '{collection_name}' collection. "
                "Using chroma_get_collection_info and chroma_count_documents:\n\n"
                "**Collection**: {collection_name}\n"
                "**Analysis**: Document count, metadata distribution, health metrics\n\n"
                "Gathering collection statistics..."
            ),
            "success_response": (
                "📊 **Collection Statistics**\n\n"
                "**Collection**: {collection_name}\n"
                "**Document Count**: {document_count}\n"
                "**Collection Health**: {health_status}\n"
                "**Metadata Fields**: {metadata_fields}\n"
                "**Embedding Dimension**: {embedding_dimension}\n"
                "**Distance Metric**: {distance_metric}\n\n"
                "{additional_stats}"
            ),
        },
        "cleanup_empty": {
            "prompt_template": (
                "I'll identify and clean up empty collections in the database. "
                "This involves:\n\n"
                "1. Listing all collections\n"
                "2. Checking document count for each\n"
                "3. Identifying empty collections\n"
                "4. Optionally removing empty collections\n\n"
                "Starting cleanup process..."
            )
        },
    },
}

# ============================================================================
# DATABASE SETUP PATTERNS
# ============================================================================

DATABASE_SETUP_PATTERNS = {
    "new_database_project": {
        "assessment_questions": [
            "What type of documents will you be storing? (legal, research, general)",
            "How many documents do you expect to manage? (small: <1K, medium: 1K-10K, large: 10K+)",
            "What kind of searches will you perform? (exact match, semantic similarity, hybrid)",
            "Do you need specialized collections for different document types?",
        ],
        "setup_recommendations": {
            "legal_documents": {
                "collections": ["contracts", "case_law", "regulations", "legal_briefs"],
                "embedding_model": "all-MiniLM-L6-v2",
                "optimization": "accuracy",
                "metadata_schema": [
                    "document_type",
                    "date",
                    "jurisdiction",
                    "practice_area",
                ],
            },
            "research_documents": {
                "collections": ["academic_papers", "reports", "articles", "datasets"],
                "embedding_model": "all-MiniLM-L6-v2",
                "optimization": "balanced",
                "metadata_schema": [
                    "source",
                    "publication_date",
                    "authors",
                    "subject_area",
                ],
            },
            "general_documents": {
                "collections": ["documents"],
                "embedding_model": "all-MiniLM-L6-v2",
                "optimization": "balanced",
                "metadata_schema": ["file_type", "created_date", "tags", "category"],
            },
        },
    },
    "collection_strategy": {
        "single_collection": {
            "use_case": "Simple projects with similar document types",
            "advantages": ["Simple management", "Easy search across all content"],
            "disadvantages": [
                "Less granular control",
                "Potential performance impact with large datasets",
            ],
        },
        "multi_collection": {
            "use_case": "Complex projects with diverse document types",
            "advantages": [
                "Better organization",
                "Optimized search per document type",
                "Granular access control",
            ],
            "disadvantages": [
                "More complex management",
                "Need to search multiple collections",
            ],
        },
        "hierarchical": {
            "use_case": "Large projects with clear document hierarchies",
            "structure": "main_collection -> subcollections by type/date/source",
            "advantages": [
                "Excellent organization",
                "Scalable structure",
                "Flexible search strategies",
            ],
        },
    },
}

# ============================================================================
# ERROR HANDLING AND TROUBLESHOOTING
# ============================================================================

ERROR_PATTERNS = {
    "collection_exists": {
        "error_message": "Collection already exists",
        "solution": "Choose a different collection name or use the existing collection",
        "alternative_actions": [
            "List existing collections to see what's available",
            "Use a different collection name with a suffix (e.g., '_v2')",
            "Delete the existing collection if you want to replace it",
        ],
    },
    "collection_not_found": {
        "error_message": "Collection does not exist",
        "solution": "Create the collection first or check the collection name",
        "alternative_actions": [
            "List available collections to see correct names",
            "Create the collection with chroma_create_collection",
            "Check for typos in the collection name",
        ],
    },
    "empty_collection": {
        "error_message": "No documents found in collection",
        "solution": "Add documents to the collection before searching",
        "alternative_actions": [
            "Add documents using document intake functionality",
            "Check if documents were successfully added",
            "Verify collection has documents with chroma_count_documents",
        ],
    },
    "embedding_error": {
        "error_message": "Failed to generate embeddings",
        "solution": "Check document content and embedding service",
        "alternative_actions": [
            "Verify documents have text content",
            "Check if embedding service is available",
            "Try with smaller batch sizes",
        ],
    },
}

# ============================================================================
# SPECIALIZED PROMPTS FOR COMMON TASKS
# ============================================================================

TASK_SPECIFIC_PROMPTS = {
    "database_setup_wizard": (
        "🏗️ **ChromaDB Database Setup Wizard**\n\n"
        "I'll help you set up a ChromaDB database optimized for your needs. "
        "Let me ask a few questions to create the best configuration:\n\n"
        "1. **Document Types**: What types of documents will you store?\n"
        "2. **Volume**: Approximately how many documents?\n"
        "3. **Search Patterns**: What kind of searches will you perform?\n"
        "4. **Organization**: Do you need multiple collections?\n\n"
        "Based on your answers, I'll create the optimal database structure."
    ),
    "document_intake_guidance": (
        "📄 **Document Intake Process**\n\n"
        "I'll guide you through adding documents to your ChromaDB:\n\n"
        "**Step 1**: Choose target collection (or I'll help create one)\n"
        "**Step 2**: Prepare documents with metadata\n"
        "**Step 3**: Generate embeddings and store documents\n"
        "**Step 4**: Verify successful storage\n\n"
        "What documents would you like to add to the database?"
    ),
    "search_optimization": (
        "🔍 **Search Strategy Optimization**\n\n"
        "I can help you find the best search approach:\n\n"
        "**Vector Search**: For semantic similarity (finds meaning, not exact words)\n"
        "**Metadata Filtering**: For exact criteria (dates, types, categories)\n"
        "**Hybrid Search**: Combination of both for precision\n\n"
        "What type of information are you trying to find?"
    ),
    "performance_tuning": (
        "⚡ **Performance Optimization**\n\n"
        "I can optimize your ChromaDB for better performance:\n\n"
        "**Collection Analysis**: Check current performance metrics\n"
        "**HNSW Tuning**: Optimize index parameters\n"
        "**Batch Operations**: Improve bulk operation efficiency\n"
        "**Memory Management**: Optimize resource usage\n\n"
        "Which aspect would you like me to optimize?"
    ),
}

# ============================================================================
# ENHANCED SYSTEM PROMPT FOR DATABASE AGENT
# ============================================================================

ENHANCED_DATABASE_SYSTEM_PROMPT = """
You are the Database Agent, a specialized AI agent responsible for managing ChromaDB vector database operations
within the AI Research Assistant system. You are an expert in vector databases, embeddings, and semantic search.

**Core Expertise:**
• ChromaDB collection management and optimization
• Document embeddings and vector operations
• Semantic search and similarity matching
• Database performance tuning and maintenance
• Metadata management and filtering strategies

**Available ChromaDB Tools:**
• chroma_create_collection: Create new collections with optimal configurations
• chroma_list_collections: List and inspect existing collections
• chroma_delete_collection: Remove collections (use with caution)
• chroma_add_documents: Store documents with embeddings and metadata
• chroma_update_documents: Modify existing documents
• chroma_get_documents: Retrieve documents with filtering
• chroma_query_documents: Perform vector similarity searches
• chroma_count_documents: Get document counts and statistics
• chroma_modify_collection: Optimize collection parameters
• chroma_get_collection_info: Get detailed collection information

**Operation Philosophy:**
1. **User Guidance**: Always explain what you're doing and why
2. **Best Practices**: Apply ChromaDB best practices for optimal performance
3. **Safety First**: Confirm destructive operations before execution
4. **Optimization Focus**: Continuously optimize for user's specific use case
5. **Error Recovery**: Provide clear solutions when issues occur

**Communication Style:**
• Be technical but accessible
• Explain vector database concepts when relevant
• Provide performance insights and optimization recommendations
• Offer alternative approaches for complex scenarios
• Always confirm understanding before proceeding with operations

**Workflow Approach:**
1. Understand the user's goal and context
2. Recommend the best ChromaDB strategy
3. Execute operations with appropriate tools
4. Verify results and provide feedback
5. Suggest optimizations and next steps

When users request database operations, always:
- Analyze their needs and recommend best practices
- Use appropriate ChromaDB tools for the task
- Provide clear feedback on results
- Offer optimization suggestions
- Handle errors gracefully with solutions
"""

# ============================================================================
# UTILITY FUNCTIONS FOR DATABASE OPERATIONS
# ============================================================================


def get_operation_prompt(operation_type: str, **kwargs) -> str:
    """
    Get a formatted prompt for a specific database operation.

    Args:
        operation_type: Type of database operation
        **kwargs: Operation-specific parameters

    Returns:
        Formatted prompt for the operation
    """
    # Navigate nested dictionary structure
    parts = operation_type.split(".")
    current = CHROMADB_OPERATIONS

    try:
        for part in parts:
            current = current[part]

        if "prompt_template" in current:
            return current["prompt_template"].format(**kwargs)
    except (KeyError, TypeError):
        pass

    return f"I'll perform the {operation_type} operation with the specified parameters."


def get_setup_recommendation(project_type: str, document_count: str) -> Dict[str, Any]:
    """
    Get database setup recommendations based on project type and scale.

    Args:
        project_type: Type of project (legal, research, general)
        document_count: Expected document volume (small, medium, large)

    Returns:
        Dictionary with setup recommendations
    """
    recommendations = DATABASE_SETUP_PATTERNS["new_database_project"][
        "setup_recommendations"
    ]

    if project_type in recommendations:
        base_config = recommendations[project_type].copy()

        # Adjust for document count
        if document_count == "large":
            base_config["optimization"] = "search_speed"
            base_config["batch_size"] = 50
        elif document_count == "small":
            base_config["optimization"] = "accuracy"
            base_config["batch_size"] = 200

        return base_config

    return recommendations["general_documents"]


def get_error_solution(error_type: str) -> Dict[str, Any]:
    """
    Get error handling information for common database errors.

    Args:
        error_type: Type of error encountered

    Returns:
        Dictionary with error solution information
    """
    return ERROR_PATTERNS.get(
        error_type,
        {
            "error_message": "Unknown error",
            "solution": "Check the operation parameters and try again",
            "alternative_actions": [
                "Review the error details",
                "Contact support if the issue persists",
            ],
        },
    )


def format_search_results(results: List[Dict[str, Any]], query: str) -> str:
    """
    Format search results for user display.

    Args:
        results: List of search result dictionaries
        query: Original search query

    Returns:
        Formatted string representation of results
    """
    if not results:
        return f"No results found for query: '{query}'"

    formatted = f"**Search Results for**: '{query}'\n\n"

    for i, result in enumerate(results[:10], 1):  # Limit to top 10
        score = result.get("score", "N/A")
        content = result.get("document", "No content")[:200] + "..."
        metadata = result.get("metadata", {})

        formatted += f"**{i}.** Score: {score}\n"
        formatted += f"Content: {content}\n"
        if metadata:
            formatted += f"Metadata: {metadata}\n"
        formatted += "\n"

    return formatted


# ============================================================================
# EXPORT ALL PROMPTS AND UTILITIES
# ============================================================================

__all__ = [
    "CHROMADB_OPERATIONS",
    "DATABASE_SETUP_PATTERNS",
    "ERROR_PATTERNS",
    "TASK_SPECIFIC_PROMPTS",
    "ENHANCED_DATABASE_SYSTEM_PROMPT",
    "get_operation_prompt",
    "get_setup_recommendation",
    "get_error_solution",
    "format_search_results",
]
