"""
Search Agent for AI Research Assistant

This agent specializes in enhanced search capabilities including web search,
database queries, document similarity search, and intelligent query processing.
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urlparse

# Core agent imports
from ..core.base_agent import AgentConfig, AgentTask, BaseAgent

logger = logging.getLogger(__name__)


class SearchType:
    """Search type classifications"""

    WEB_SEARCH = "web_search"
    DATABASE_SEARCH = "database_search"
    DOCUMENT_SEARCH = "document_search"
    SIMILARITY_SEARCH = "similarity_search"
    SEMANTIC_SEARCH = "semantic_search"
    HYBRID_SEARCH = "hybrid_search"


class SearchScope:
    """Search scope definitions"""

    LOCAL = "local"
    GLOBAL = "global"
    TARGETED = "targeted"
    COMPREHENSIVE = "comprehensive"


class SearchAgent(BaseAgent):
    """
    Specialized agent for enhanced search capabilities.

    Capabilities:
    - Web search with intelligent query processing
    - Database search with optimized queries
    - Document similarity and semantic search
    - Multi-source search coordination
    - Search result ranking and filtering
    - Query enhancement and expansion
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[AgentConfig] = None,
        global_settings_manager=None,
        max_results_per_source: int = 50,
        search_timeout: int = 30,
        enable_web_search: bool = True,
        enable_database_search: bool = True,
        **kwargs,
    ):
        super().__init__(
            agent_id=agent_id,
            config=config,
            global_settings_manager=global_settings_manager,
            **kwargs,
        )

        # Search-specific configuration
        self.max_results_per_source = max_results_per_source
        self.search_timeout = search_timeout
        self.enable_web_search = enable_web_search
        self.enable_database_search = enable_database_search

        # Search caching and optimization
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.search_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, List[float]] = {}

        # Web search configuration
        self.web_search_engines = {
            "duckduckgo": {"enabled": True, "priority": 1},
            "bing": {"enabled": False, "priority": 2},
            "google": {"enabled": False, "priority": 3},
        }

        logger.info(f"SearchAgent initialized: {self.agent_id}")

    def get_supported_task_types(self) -> List[str]:
        """Return list of task types this agent can handle."""
        return [
            "web_search",
            "database_search",
            "document_search",
            "similarity_search",
            "semantic_search",
            "hybrid_search",
            "query_enhancement",
            "search_optimization",
        ]

    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a specific search task."""
        task_type = task.task_type
        params = task.parameters

        start_time = datetime.now()

        try:
            if task_type == "web_search":
                query = params.get("query")
                if not query:
                    raise ValueError("query parameter is required")
                result = await self._perform_web_search(
                    query=query,
                    max_results=params.get("max_results", self.max_results_per_source),
                    search_engines=params.get("search_engines", ["duckduckgo"]),
                    filters=params.get("filters", {}),
                )

            elif task_type == "database_search":
                query = params.get("query")
                database = params.get("database")
                if not query:
                    raise ValueError("query parameter is required")
                result = await self._perform_database_search(
                    query=query,
                    database=database,
                    filters=params.get("filters", {}),
                    limit=params.get("limit", self.max_results_per_source),
                )

            elif task_type == "document_search":
                query = params.get("query")
                collection = params.get("collection")
                if not query:
                    raise ValueError("query parameter is required")
                result = await self._perform_document_search(
                    query=query,
                    collection=collection,
                    search_type=params.get("search_type", "text"),
                    filters=params.get("filters", {}),
                )

            elif task_type == "similarity_search":
                content = params.get("content")
                reference_id = params.get("reference_id")
                if not content:
                    raise ValueError("content parameter is required")
                result = await self._perform_similarity_search(
                    content=content,
                    reference_id=reference_id,
                    threshold=params.get("threshold", 0.7),
                    limit=params.get("limit", self.max_results_per_source),
                )

            elif task_type == "semantic_search":
                query = params.get("query")
                if not query:
                    raise ValueError("query parameter is required")
                result = await self._perform_semantic_search(
                    query=query,
                    collections=params.get("collections", []),
                    embedding_model=params.get("embedding_model", "default"),
                )

            elif task_type == "hybrid_search":
                query = params.get("query")
                if not query:
                    raise ValueError("query parameter is required")
                result = await self._perform_hybrid_search(
                    query=query,
                    sources=params.get("sources", ["web", "database", "documents"]),
                    weights=params.get(
                        "weights", {"web": 0.4, "database": 0.3, "documents": 0.3}
                    ),
                )

            elif task_type == "query_enhancement":
                query = params.get("query")
                if not query:
                    raise ValueError("query parameter is required")
                result = await self._enhance_query(
                    query=query,
                    context=params.get("context", {}),
                    enhancement_type=params.get("enhancement_type", "expand"),
                )

            elif task_type == "search_optimization":
                result = await self._optimize_search_performance(
                    analysis_period_days=params.get("analysis_period_days", 7)
                )

            else:
                raise ValueError(f"Unsupported task type: {task_type}")

            # Record performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._record_performance_metric(task_type, execution_time)

            result["execution_time"] = execution_time
            result["timestamp"] = datetime.now().isoformat()

            return result

        except Exception as e:
            logger.error(f"Task execution failed for {task_type}: {e}", exc_info=True)
            raise

    async def _perform_web_search(
        self,
        query: str,
        max_results: int = 50,
        search_engines: List[str] = None,
        filters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Perform web search across multiple search engines."""
        if not self.enable_web_search:
            return {"success": False, "error": "Web search is disabled", "results": []}

        search_engines = search_engines or ["duckduckgo"]
        filters = filters or {}

        # Check cache first
        cache_key = self._generate_cache_key(
            "web", query, str(search_engines), str(filters)
        )
        if cache_key in self.query_cache:
            cached_result = self.query_cache[cache_key]
            if self._is_cache_valid(cached_result):
                logger.info(f"Returning cached web search results for: {query}")
                cached_result["from_cache"] = True
                return cached_result

        logger.info(f"Performing web search: {query}")

        all_results = []
        search_summary = {"total_results": 0, "engines_used": [], "errors": []}

        for engine in search_engines:
            if (
                engine not in self.web_search_engines
                or not self.web_search_engines[engine]["enabled"]
            ):
                continue

            try:
                engine_results = await self._search_with_engine(
                    engine, query, max_results, filters
                )
                if engine_results["success"]:
                    all_results.extend(engine_results["results"])
                    search_summary["engines_used"].append(engine)
                    search_summary["total_results"] += len(engine_results["results"])
                else:
                    search_summary["errors"].append(
                        {
                            "engine": engine,
                            "error": engine_results.get("error", "Unknown error"),
                        }
                    )
            except Exception as e:
                search_summary["errors"].append({"engine": engine, "error": str(e)})
                logger.warning(f"Web search failed for engine {engine}: {e}")

        # Remove duplicates and rank results
        unique_results = self._deduplicate_web_results(all_results)
        ranked_results = self._rank_web_results(unique_results, query)

        # Limit results
        final_results = ranked_results[:max_results]

        result = {
            "success": True,
            "query": query,
            "search_type": SearchType.WEB_SEARCH,
            "results": final_results,
            "summary": search_summary,
            "total_found": len(unique_results),
            "returned_count": len(final_results),
            "from_cache": False,
        }

        # Cache the result
        self.query_cache[cache_key] = result
        self._add_to_search_history("web_search", query, len(final_results))

        return result

    async def _search_with_engine(
        self, engine: str, query: str, max_results: int, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform search with a specific search engine."""
        if engine == "duckduckgo":
            return await self._duckduckgo_search(query, max_results, filters)
        elif engine == "bing":
            return await self._bing_search(query, max_results, filters)
        elif engine == "google":
            return await self._google_search(query, max_results, filters)
        else:
            return {
                "success": False,
                "error": f"Unsupported search engine: {engine}",
                "results": [],
            }

    async def _duckduckgo_search(
        self, query: str, max_results: int, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform search using DuckDuckGo."""
        try:
            # This is a placeholder for actual DuckDuckGo API integration
            # In a real implementation, you would use the duckduckgo-search library
            # or make HTTP requests to DuckDuckGo's API

            logger.info(f"DuckDuckGo search for: {query}")

            # Simulate search results (replace with actual implementation)
            mock_results = [
                {
                    "title": f"Mock Result 1 for {query}",
                    "url": f"https://example.com/result1?q={quote_plus(query)}",
                    "snippet": f"This is a mock search result snippet for {query}...",
                    "engine": "duckduckgo",
                    "rank": 1,
                    "relevance_score": 0.95,
                },
                {
                    "title": f"Mock Result 2 for {query}",
                    "url": f"https://example.com/result2?q={quote_plus(query)}",
                    "snippet": f"Another mock search result snippet for {query}...",
                    "engine": "duckduckgo",
                    "rank": 2,
                    "relevance_score": 0.87,
                },
            ]

            return {
                "success": True,
                "engine": "duckduckgo",
                "results": mock_results[:max_results],
                "total_found": len(mock_results),
            }

        except Exception as e:
            return {
                "success": False,
                "engine": "duckduckgo",
                "error": str(e),
                "results": [],
            }

    async def _bing_search(
        self, query: str, max_results: int, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform search using Bing Search API."""
        # Placeholder for Bing Search API integration
        return {
            "success": False,
            "engine": "bing",
            "error": "Bing Search API not configured",
            "results": [],
        }

    async def _google_search(
        self, query: str, max_results: int, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform search using Google Custom Search API."""
        # Placeholder for Google Custom Search API integration
        return {
            "success": False,
            "engine": "google",
            "error": "Google Custom Search API not configured",
            "results": [],
        }

    async def _perform_database_search(
        self,
        query: str,
        database: Optional[str] = None,
        filters: Dict[str, Any] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Perform database search with intelligent query processing."""
        if not self.enable_database_search:
            return {
                "success": False,
                "error": "Database search is disabled",
                "results": [],
            }

        filters = filters or {}

        logger.info(f"Performing database search: {query}")

        try:
            # This would integrate with the actual database search functionality
            # For now, we'll return a mock implementation

            # Parse and optimize the query
            optimized_query = await self._optimize_database_query(query, database)

            # Execute the search (placeholder)
            mock_results = [
                {
                    "id": "doc_1",
                    "title": f"Database Document 1 for {query}",
                    "content": f"Mock database content matching {query}...",
                    "source": database or "default_db",
                    "score": 0.92,
                    "metadata": {
                        "type": "legal_case",
                        "date": "2024-01-15",
                        "category": "research",
                    },
                },
                {
                    "id": "doc_2",
                    "title": f"Database Document 2 for {query}",
                    "content": f"Another mock database result for {query}...",
                    "source": database or "default_db",
                    "score": 0.85,
                    "metadata": {
                        "type": "technical_doc",
                        "date": "2024-01-10",
                        "category": "documentation",
                    },
                },
            ]

            # Apply filters
            filtered_results = self._apply_database_filters(mock_results, filters)

            # Limit results
            final_results = filtered_results[:limit]

            return {
                "success": True,
                "query": query,
                "optimized_query": optimized_query,
                "search_type": SearchType.DATABASE_SEARCH,
                "database": database or "default_db",
                "results": final_results,
                "total_found": len(filtered_results),
                "returned_count": len(final_results),
            }

        except Exception as e:
            logger.error(f"Database search failed: {e}")
            return {"success": False, "error": str(e), "results": []}

    async def _perform_document_search(
        self,
        query: str,
        collection: Optional[str] = None,
        search_type: str = "text",
        filters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Perform document search within specified collections."""
        filters = filters or {}

        logger.info(f"Performing document search: {query} (type: {search_type})")

        try:
            # This would integrate with document indexing and search
            # For now, we'll return a mock implementation

            if search_type == "text":
                results = await self._text_based_document_search(
                    query, collection, filters
                )
            elif search_type == "semantic":
                results = await self._semantic_document_search(
                    query, collection, filters
                )
            else:
                raise ValueError(f"Unsupported document search type: {search_type}")

            return {
                "success": True,
                "query": query,
                "search_type": f"{SearchType.DOCUMENT_SEARCH}_{search_type}",
                "collection": collection or "all_collections",
                "results": results,
                "total_found": len(results),
                "returned_count": len(results),
            }

        except Exception as e:
            logger.error(f"Document search failed: {e}")
            return {"success": False, "error": str(e), "results": []}

    async def _perform_similarity_search(
        self,
        content: str,
        reference_id: Optional[str] = None,
        threshold: float = 0.7,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Perform similarity search to find related content."""
        logger.info(f"Performing similarity search (threshold: {threshold})")

        try:
            # This would use embeddings and vector similarity
            # For now, we'll return a mock implementation

            # Generate content hash for caching
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]

            mock_results = [
                {
                    "id": "similar_1",
                    "title": f"Similar Document 1 to {content_hash}",
                    "similarity_score": 0.89,
                    "content_preview": "This document has similar content patterns...",
                    "metadata": {
                        "type": "legal_case",
                        "length": len(content),
                        "source": "database",
                    },
                },
                {
                    "id": "similar_2",
                    "title": f"Similar Document 2 to {content_hash}",
                    "similarity_score": 0.76,
                    "content_preview": "Another document with matching themes...",
                    "metadata": {
                        "type": "research_paper",
                        "length": len(content) * 0.8,
                        "source": "web",
                    },
                },
            ]

            # Filter by threshold and limit
            filtered_results = [
                result
                for result in mock_results
                if result["similarity_score"] >= threshold
            ][:limit]

            return {
                "success": True,
                "search_type": SearchType.SIMILARITY_SEARCH,
                "reference_id": reference_id,
                "threshold": threshold,
                "content_length": len(content),
                "results": filtered_results,
                "total_found": len(filtered_results),
                "returned_count": len(filtered_results),
            }

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return {"success": False, "error": str(e), "results": []}

    async def _perform_semantic_search(
        self,
        query: str,
        collections: List[str] = None,
        embedding_model: str = "default",
    ) -> Dict[str, Any]:
        """Perform semantic search using embeddings."""
        collections = collections or []

        logger.info(f"Performing semantic search: {query}")

        try:
            # This would use actual embedding models for semantic search
            # For now, we'll return a mock implementation

            mock_results = [
                {
                    "id": "semantic_1",
                    "title": f"Semantic Match 1 for {query}",
                    "semantic_score": 0.93,
                    "content": f"Content semantically related to {query}...",
                    "collection": collections[0] if collections else "default",
                    "embedding_model": embedding_model,
                },
                {
                    "id": "semantic_2",
                    "title": f"Semantic Match 2 for {query}",
                    "semantic_score": 0.81,
                    "content": f"Another semantically similar content for {query}...",
                    "collection": collections[0] if collections else "default",
                    "embedding_model": embedding_model,
                },
            ]

            return {
                "success": True,
                "query": query,
                "search_type": SearchType.SEMANTIC_SEARCH,
                "collections": collections,
                "embedding_model": embedding_model,
                "results": mock_results,
                "total_found": len(mock_results),
                "returned_count": len(mock_results),
            }

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {"success": False, "error": str(e), "results": []}

    async def _perform_hybrid_search(
        self, query: str, sources: List[str], weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Perform hybrid search across multiple sources."""
        logger.info(f"Performing hybrid search: {query}")

        all_results = []
        source_results = {}

        try:
            # Execute searches across all sources in parallel
            search_tasks = []

            if "web" in sources and self.enable_web_search:
                search_tasks.append(self._perform_web_search(query))

            if "database" in sources and self.enable_database_search:
                search_tasks.append(self._perform_database_search(query))

            if "documents" in sources:
                search_tasks.append(self._perform_document_search(query))

            # Wait for all searches to complete
            if search_tasks:
                results = await asyncio.gather(*search_tasks, return_exceptions=True)

                # Process results from each source
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.warning(
                            f"Search failed for source {sources[i]}: {result}"
                        )
                        continue

                    if result.get("success"):
                        source_name = sources[i] if i < len(sources) else f"source_{i}"
                        source_results[source_name] = result

                        # Apply weights to results
                        weighted_results = self._apply_source_weights(
                            result["results"],
                            weights.get(source_name, 1.0),
                            source_name,
                        )
                        all_results.extend(weighted_results)

            # Merge and rank all results
            merged_results = self._merge_hybrid_results(all_results)
            ranked_results = self._rank_hybrid_results(merged_results, query)

            return {
                "success": True,
                "query": query,
                "search_type": SearchType.HYBRID_SEARCH,
                "sources_used": list(source_results.keys()),
                "weights": weights,
                "source_results": source_results,
                "merged_results": ranked_results,
                "total_found": len(ranked_results),
                "returned_count": len(ranked_results),
            }

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return {"success": False, "error": str(e), "results": []}

    async def _enhance_query(
        self,
        query: str,
        context: Dict[str, Any] = None,
        enhancement_type: str = "expand",
    ) -> Dict[str, Any]:
        """Enhance search queries using LLM analysis."""
        context = context or {}

        logger.info(f"Enhancing query: {query} (type: {enhancement_type})")

        try:
            if enhancement_type == "expand":
                enhanced_query = await self._expand_query(query, context)
            elif enhancement_type == "refine":
                enhanced_query = await self._refine_query(query, context)
            elif enhancement_type == "translate":
                enhanced_query = await self._translate_query(query, context)
            else:
                raise ValueError(f"Unsupported enhancement type: {enhancement_type}")

            return {
                "success": True,
                "original_query": query,
                "enhanced_query": enhanced_query,
                "enhancement_type": enhancement_type,
                "context_used": bool(context),
                "improvements": self._analyze_query_improvements(query, enhanced_query),
            }

        except Exception as e:
            logger.error(f"Query enhancement failed: {e}")
            return {"success": False, "error": str(e), "original_query": query}

    # Helper methods for various search operations

    def _generate_cache_key(self, *components: str) -> str:
        """Generate a cache key from multiple components."""
        combined = "|".join(str(c) for c in components)
        return hashlib.md5(combined.encode()).hexdigest()

    def _is_cache_valid(
        self, cached_result: Dict[str, Any], max_age_hours: int = 1
    ) -> bool:
        """Check if cached result is still valid."""
        if "timestamp" not in cached_result:
            return False

        cache_time = datetime.fromisoformat(cached_result["timestamp"])
        age_hours = (datetime.now() - cache_time).total_seconds() / 3600
        return age_hours < max_age_hours

    def _deduplicate_web_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate results based on URL similarity."""
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get("url", "")
            # Normalize URL for comparison
            normalized_url = urlparse(url).netloc + urlparse(url).path

            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(result)

        return unique_results

    def _rank_web_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """Rank web search results by relevance."""
        # Simple ranking based on title and snippet relevance
        query_terms = query.lower().split()

        for result in results:
            score = 0
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()

            # Count query term matches
            for term in query_terms:
                score += title.count(term) * 2  # Title matches worth more
                score += snippet.count(term)

            result["calculated_score"] = score

        # Sort by calculated score descending
        return sorted(results, key=lambda x: x.get("calculated_score", 0), reverse=True)

    async def _optimize_database_query(
        self, query: str, database: Optional[str]
    ) -> str:
        """Optimize database query for better performance."""
        # This would include query optimization logic
        # For now, return the original query
        return query

    def _apply_database_filters(
        self, results: List[Dict[str, Any]], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply filters to database search results."""
        filtered_results = results

        for filter_key, filter_value in filters.items():
            if filter_key == "type":
                filtered_results = [
                    r
                    for r in filtered_results
                    if r.get("metadata", {}).get("type") == filter_value
                ]
            elif filter_key == "date_range":
                # Apply date range filtering
                pass
            elif filter_key == "min_score":
                filtered_results = [
                    r for r in filtered_results if r.get("score", 0) >= filter_value
                ]

        return filtered_results

    async def _text_based_document_search(
        self, query: str, collection: Optional[str], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform text-based document search."""
        # Mock implementation
        return [
            {
                "id": "text_doc_1",
                "title": f"Text Document 1 for {query}",
                "content": f"Text content matching {query}...",
                "collection": collection or "default",
                "text_score": 0.88,
            }
        ]

    async def _semantic_document_search(
        self, query: str, collection: Optional[str], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Perform semantic document search."""
        # Mock implementation
        return [
            {
                "id": "semantic_doc_1",
                "title": f"Semantic Document 1 for {query}",
                "content": f"Semantic content for {query}...",
                "collection": collection or "default",
                "semantic_score": 0.91,
            }
        ]

    def _apply_source_weights(
        self, results: List[Dict[str, Any]], weight: float, source_name: str
    ) -> List[Dict[str, Any]]:
        """Apply weights to search results from a specific source."""
        weighted_results = []

        for result in results:
            weighted_result = result.copy()

            # Apply weight to existing scores
            if "relevance_score" in result:
                weighted_result["weighted_score"] = result["relevance_score"] * weight
            elif "score" in result:
                weighted_result["weighted_score"] = result["score"] * weight
            else:
                weighted_result["weighted_score"] = weight

            weighted_result["source"] = source_name
            weighted_result["weight_applied"] = weight
            weighted_results.append(weighted_result)

        return weighted_results

    def _merge_hybrid_results(
        self, all_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge results from multiple sources."""
        # Remove duplicates based on content similarity
        merged = []
        seen_titles = set()

        for result in all_results:
            title = result.get("title", "").lower()
            if title not in seen_titles:
                seen_titles.add(title)
                merged.append(result)

        return merged

    def _rank_hybrid_results(
        self, results: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """Rank hybrid search results."""
        # Sort by weighted score descending
        return sorted(results, key=lambda x: x.get("weighted_score", 0), reverse=True)

    async def _expand_query(self, query: str, context: Dict[str, Any]) -> str:
        """Expand query with related terms."""
        try:
            expansion_prompt = f"""
            Expand the following search query with related terms, synonyms, and context:

            Original query: {query}
            Context: {context}

            Provide an expanded query that includes:
            1. Synonyms and related terms
            2. Alternative phrasings
            3. Domain-specific terminology

            Return only the expanded query without explanation.
            """

            response = await self.llm.ainvoke(expansion_prompt)
            return response.content.strip()

        except Exception as e:
            logger.warning(f"Query expansion failed: {e}")
            return query

    async def _refine_query(self, query: str, context: Dict[str, Any]) -> str:
        """Refine query for better precision."""
        try:
            refinement_prompt = f"""
            Refine the following search query for better precision and clarity:

            Original query: {query}
            Context: {context}

            Make the query more specific and targeted while maintaining its intent.
            Return only the refined query without explanation.
            """

            response = await self.llm.ainvoke(refinement_prompt)
            return response.content.strip()

        except Exception as e:
            logger.warning(f"Query refinement failed: {e}")
            return query

    async def _translate_query(self, query: str, context: Dict[str, Any]) -> str:
        """Translate query to different domain terminology."""
        target_domain = context.get("domain", "general")

        try:
            translation_prompt = f"""
            Translate the following query to {target_domain} domain terminology:

            Original query: {query}
            Target domain: {target_domain}

            Return only the translated query without explanation.
            """

            response = await self.llm.ainvoke(translation_prompt)
            return response.content.strip()

        except Exception as e:
            logger.warning(f"Query translation failed: {e}")
            return query

    def _analyze_query_improvements(
        self, original: str, enhanced: str
    ) -> Dict[str, Any]:
        """Analyze improvements made to the query."""
        return {
            "original_length": len(original.split()),
            "enhanced_length": len(enhanced.split()),
            "length_change": len(enhanced.split()) - len(original.split()),
            "complexity_increase": len(enhanced) > len(original) * 1.2,
            "terms_added": len(set(enhanced.split()) - set(original.split())),
        }

    def _record_performance_metric(self, task_type: str, execution_time: float):
        """Record performance metrics for optimization."""
        if task_type not in self.performance_metrics:
            self.performance_metrics[task_type] = []

        self.performance_metrics[task_type].append(execution_time)

        # Keep only recent metrics (last 100 executions)
        if len(self.performance_metrics[task_type]) > 100:
            self.performance_metrics[task_type] = self.performance_metrics[task_type][
                -100:
            ]

    def _add_to_search_history(self, search_type: str, query: str, result_count: int):
        """Add search to history for analysis."""
        self.search_history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "search_type": search_type,
                "query": query,
                "result_count": result_count,
            }
        )

        # Keep only recent history (last 1000 searches)
        if len(self.search_history) > 1000:
            self.search_history = self.search_history[-1000:]

    async def _optimize_search_performance(
        self, analysis_period_days: int = 7
    ) -> Dict[str, Any]:
        """Analyze and optimize search performance."""
        try:
            cutoff_date = datetime.now().timestamp() - (
                analysis_period_days * 24 * 3600
            )

            # Analyze recent performance
            recent_metrics = {}
            for task_type, metrics in self.performance_metrics.items():
                if metrics:
                    recent_metrics[task_type] = {
                        "avg_time": sum(metrics) / len(metrics),
                        "max_time": max(metrics),
                        "min_time": min(metrics),
                        "count": len(metrics),
                    }

            # Analyze search patterns
            recent_searches = [
                search
                for search in self.search_history
                if datetime.fromisoformat(search["timestamp"]).timestamp() > cutoff_date
            ]

            optimization_suggestions = []

            # Generate optimization suggestions based on metrics
            for task_type, metrics in recent_metrics.items():
                if metrics["avg_time"] > 10:  # Slow searches
                    optimization_suggestions.append(
                        f"Consider caching for {task_type} (avg: {metrics['avg_time']:.2f}s)"
                    )

                if metrics["count"] > 50:  # Frequent searches
                    optimization_suggestions.append(
                        f"High usage for {task_type} - consider performance optimization"
                    )

            return {
                "success": True,
                "analysis_period_days": analysis_period_days,
                "performance_metrics": recent_metrics,
                "total_searches": len(recent_searches),
                "cache_hit_rate": len(
                    [r for r in recent_searches if "cached" in str(r)]
                )
                / max(len(recent_searches), 1),
                "optimization_suggestions": optimization_suggestions,
            }

        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_search_statistics(self) -> Dict[str, Any]:
        """Get comprehensive search statistics."""
        return {
            "agent_id": self.agent_id,
            "total_searches": len(self.search_history),
            "cache_size": len(self.query_cache),
            "performance_metrics": self.performance_metrics,
            "web_search_enabled": self.enable_web_search,
            "database_search_enabled": self.enable_database_search,
            "supported_engines": list(self.web_search_engines.keys()),
            "max_results_per_source": self.max_results_per_source,
            "search_timeout": self.search_timeout,
        }
