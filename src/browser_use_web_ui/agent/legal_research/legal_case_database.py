"""
Legal Case Database for WCAT Case Storage, Search, and Cross-Referencing

This module provides:
1. SQLite database for persistent case storage
2. Full-text search capabilities across case content
3. Cross-referencing between similar cases
4. Advanced filtering and indexing
5. Case relationship analysis
"""

import json
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class LegalCaseDatabase:
    """
    Comprehensive database for storing and searching WCAT legal cases.

    Features:
    - Full case metadata and content storage
    - Full-text search across case summaries and outcomes
    - Cross-referencing similar cases
    - Advanced filtering by date, condition, outcome
    - Case relationship mapping
    - Search history and analytics
    """

    def __init__(self, db_path: Optional[str] = None):
        # Use environment variable if available, otherwise use provided path or default
        if db_path is None:
            env_path = os.getenv("WCAT_DATABASE_PATH")
            if env_path:
                self.db_path = Path(env_path)
            else:
                self.db_path = Path("./tmp/legal_research/cases.db")
        else:
            self.db_path = Path(db_path)

        # Ensure the directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize the database with all required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # Main cases table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appeal_number TEXT UNIQUE NOT NULL,
                    date TEXT NOT NULL,
                    appeal_type TEXT,
                    decision_type TEXT,
                    issues TEXT,
                    case_summary TEXT,
                    outcome TEXT,
                    pdf_url TEXT,
                    pdf_path TEXT,
                    full_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Keywords table for better searching
            conn.execute("""
                CREATE TABLE IF NOT EXISTS case_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER,
                    keyword TEXT NOT NULL,
                    keyword_type TEXT, -- 'medical', 'legal', 'procedural'
                    FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE CASCADE
                )
            """)

            # Case relationships (similar cases)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS case_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id_1 INTEGER,
                    case_id_2 INTEGER,
                    similarity_score REAL,
                    relationship_type TEXT, -- 'similar_condition', 'similar_outcome', 'precedent'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (case_id_1) REFERENCES cases (id) ON DELETE CASCADE,
                    FOREIGN KEY (case_id_2) REFERENCES cases (id) ON DELETE CASCADE
                )
            """)

            # Search history and analytics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    filters TEXT, -- JSON of filters applied
                    results_count INTEGER,
                    user_case_summary TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Case analysis results
            conn.execute("""
                CREATE TABLE IF NOT EXISTS case_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_case_summary TEXT,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    similar_cases_found INTEGER,
                    favorable_precedents INTEGER,
                    unfavorable_precedents INTEGER,
                    recommendations TEXT, -- JSON
                    confidence_score REAL
                )
            """)

            # Create indexes for better performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_appeal_number ON cases (appeal_number)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_case_date ON cases (date)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_keywords ON case_keywords (keyword)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_similarity ON case_relationships (similarity_score)"
            )

            # Create full-text search virtual table
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS cases_fts USING fts5(
                    appeal_number, issues, case_summary, outcome, full_text,
                    content='cases', content_rowid='id'
                )
            """)

            conn.commit()
            logger.info(f"Legal case database initialized at {self.db_path}")

    def add_case(self, case_data: Dict[str, Any]) -> int:
        """Add or update a case in the database"""
        with sqlite3.connect(self.db_path) as conn:
            # Check if case already exists
            cursor = conn.execute(
                "SELECT id FROM cases WHERE appeal_number = ?",
                (case_data.get("appeal_number"),),
            )
            existing_case = cursor.fetchone()

            if existing_case:
                # Update existing case
                case_id = existing_case[0]
                conn.execute(
                    """
                    UPDATE cases SET
                        date = ?, appeal_type = ?, decision_type = ?,
                        issues = ?, case_summary = ?, outcome = ?,
                        pdf_url = ?, pdf_path = ?, full_text = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (
                        case_data.get("date"),
                        case_data.get("appeal_type"),
                        case_data.get("decision_type"),
                        case_data.get("issues"),
                        case_data.get("case_summary"),
                        case_data.get("outcome"),
                        case_data.get("pdf_url"),
                        case_data.get("pdf_path"),
                        case_data.get("full_text", ""),
                        case_id,
                    ),
                )
                logger.info(f"Updated case {case_data.get('appeal_number')}")
            else:
                # Insert new case
                cursor = conn.execute(
                    """
                    INSERT INTO cases (
                        appeal_number, date, appeal_type, decision_type,
                        issues, case_summary, outcome, pdf_url, pdf_path, full_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        case_data.get("appeal_number"),
                        case_data.get("date"),
                        case_data.get("appeal_type"),
                        case_data.get("decision_type"),
                        case_data.get("issues"),
                        case_data.get("case_summary"),
                        case_data.get("outcome"),
                        case_data.get("pdf_url"),
                        case_data.get("pdf_path"),
                        case_data.get("full_text", ""),
                    ),
                )
                case_id = cursor.lastrowid
                if case_id is None:
                    raise RuntimeError("Failed to insert case - no ID returned")
                logger.info(
                    f"Added new case {case_data.get('appeal_number')} with ID {case_id}"
                )

            # Update full-text search index
            conn.execute(
                """
                INSERT OR REPLACE INTO cases_fts (rowid, appeal_number, issues, case_summary, outcome, full_text)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    case_id,
                    case_data.get("appeal_number", ""),
                    case_data.get("issues", ""),
                    case_data.get("case_summary", ""),
                    case_data.get("outcome", ""),
                    case_data.get("full_text", ""),
                ),
            )

            # Add keywords
            self._add_keywords(conn, case_id, case_data.get("keywords", []))

            conn.commit()
            return case_id

    def _add_keywords(
        self, conn: sqlite3.Connection, case_id: int, keywords: List[str]
    ):
        """Add keywords for a case"""
        # Clear existing keywords
        conn.execute("DELETE FROM case_keywords WHERE case_id = ?", (case_id,))

        # Categorize and add new keywords
        for keyword in keywords:
            keyword_type = self._categorize_keyword(keyword)
            conn.execute(
                """
                INSERT INTO case_keywords (case_id, keyword, keyword_type)
                VALUES (?, ?, ?)
            """,
                (case_id, keyword.lower(), keyword_type),
            )

    def _categorize_keyword(self, keyword: str) -> str:
        """Categorize keywords by type"""
        keyword_lower = keyword.lower()

        medical_terms = {
            "stenosis",
            "herniation",
            "radiculopathy",
            "spondylosis",
            "neuropathy",
            "disc",
            "spinal",
            "cervical",
            "lumbar",
        }
        legal_terms = {
            "compensable",
            "causation",
            "aggravation",
            "employment",
            "workplace",
            "appeal",
            "decision",
            "tribunal",
        }

        if any(term in keyword_lower for term in medical_terms):
            return "medical"
        elif any(term in keyword_lower for term in legal_terms):
            return "legal"
        else:
            return "general"

    def search_cases(
        self, query: str = "", filters: Optional[Dict[str, Any]] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search cases with various filters and full-text search"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            where_clauses = []
            params = []

            # Full-text search if query provided
            if query.strip():
                where_clauses.append("""
                    cases.id IN (
                        SELECT rowid FROM cases_fts WHERE cases_fts MATCH ?
                    )
                """)
                params.append(query)

            # Apply filters
            if filters:
                if filters.get("date_from"):
                    where_clauses.append("cases.date >= ?")
                    params.append(filters["date_from"])

                if filters.get("date_to"):
                    where_clauses.append("cases.date <= ?")
                    params.append(filters["date_to"])

                if filters.get("appeal_type"):
                    where_clauses.append("cases.appeal_type = ?")
                    params.append(filters["appeal_type"])

                if filters.get("outcome_contains"):
                    where_clauses.append("cases.outcome LIKE ?")
                    params.append(f"%{filters['outcome_contains']}%")

                if filters.get("keywords"):
                    keyword_list = filters["keywords"]
                    if isinstance(keyword_list, str):
                        keyword_list = [keyword_list]

                    keyword_clause = """
                        cases.id IN (
                            SELECT case_id FROM case_keywords
                            WHERE keyword IN ({})
                        )
                    """.format(",".join("?" * len(keyword_list)))
                    where_clauses.append(keyword_clause)
                    params.extend(keyword_list)

            # Build query
            base_query = """
                SELECT DISTINCT cases.*,
                       GROUP_CONCAT(case_keywords.keyword) as keywords
                FROM cases
                LEFT JOIN case_keywords ON cases.id = case_keywords.case_id
            """

            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)

            base_query += " GROUP BY cases.id ORDER BY cases.date DESC LIMIT ?"
            params.append(limit)

            # Log search for analytics
            self._log_search(query, filters, conn)

            cursor = conn.execute(base_query, params)
            results = [dict(row) for row in cursor.fetchall()]

            # Convert keywords back to list
            for result in results:
                if result["keywords"]:
                    result["keywords"] = result["keywords"].split(",")
                else:
                    result["keywords"] = []

            return results

    def find_similar_cases(
        self,
        user_keywords: List[str],
        user_case_summary: str = "",
        min_similarity: float = 0.3,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Find cases similar to user's case based on keywords and content"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get all cases with their keywords
            all_cases = conn.execute("""
                SELECT cases.*, GROUP_CONCAT(case_keywords.keyword) as keywords
                FROM cases
                LEFT JOIN case_keywords ON cases.id = case_keywords.case_id
                GROUP BY cases.id
            """).fetchall()

            similar_cases = []
            user_keywords_set = set(k.lower() for k in user_keywords)

            for case in all_cases:
                case_dict = dict(case)
                case_keywords = (
                    case_dict["keywords"].split(",") if case_dict["keywords"] else []
                )
                case_keywords_set = set(k.strip().lower() for k in case_keywords)

                # Calculate similarity score
                similarity = self._calculate_similarity_score(
                    user_keywords_set, case_keywords_set, user_case_summary, case_dict
                )

                if similarity >= min_similarity:
                    case_dict["similarity_score"] = similarity
                    case_dict["keywords"] = case_keywords
                    similar_cases.append(case_dict)

            # Sort by similarity score
            similar_cases.sort(key=lambda x: x["similarity_score"], reverse=True)

            return similar_cases[:limit]

    def _calculate_similarity_score(
        self,
        user_keywords: Set[str],
        case_keywords: Set[str],
        user_summary: str,
        case_data: Dict[str, Any],
    ) -> float:
        """Calculate comprehensive similarity score between user case and stored case"""

        # Keyword overlap similarity (0.0 - 0.6)
        if not user_keywords and not case_keywords:
            keyword_similarity = 0.0
        elif not user_keywords or not case_keywords:
            keyword_similarity = 0.0
        else:
            intersection = user_keywords.intersection(case_keywords)
            union = user_keywords.union(case_keywords)
            keyword_similarity = (len(intersection) / len(union)) * 0.6

        # Content similarity (0.0 - 0.3)
        content_similarity = 0.0
        if user_summary and case_data.get("case_summary"):
            content_similarity = (
                self._text_similarity(user_summary, case_data["case_summary"]) * 0.3
            )

        # Medical condition boost (0.0 - 0.1)
        medical_boost = 0.0
        medical_terms = {"stenosis", "herniation", "radiculopathy", "disc"}
        if intersection := user_keywords.intersection(case_keywords).intersection(
            medical_terms
        ):
            medical_boost = min(len(intersection) * 0.05, 0.1)

        return keyword_similarity + content_similarity + medical_boost

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity based on common words"""
        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def add_case_relationship(
        self,
        case_id_1: int,
        case_id_2: int,
        similarity_score: float,
        relationship_type: str = "similar_condition",
    ):
        """Add a relationship between two cases"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO case_relationships
                (case_id_1, case_id_2, similarity_score, relationship_type)
                VALUES (?, ?, ?, ?)
            """,
                (case_id_1, case_id_2, similarity_score, relationship_type),
            )
            conn.commit()

    def get_case_relationships(self, case_id: int) -> List[Dict[str, Any]]:
        """Get all related cases for a given case"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT r.*, c.appeal_number, c.issues, c.outcome
                FROM case_relationships r
                JOIN cases c ON (r.case_id_2 = c.id)
                WHERE r.case_id_1 = ?
                ORDER BY r.similarity_score DESC
            """,
                (case_id,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def _log_search(
        self, query: str, filters: Optional[Dict[str, Any]], conn: sqlite3.Connection
    ):
        """Log search for analytics"""
        conn.execute(
            """
            INSERT INTO search_history (query, filters, user_case_summary)
            VALUES (?, ?, ?)
        """,
            (
                query,
                json.dumps(filters) if filters else None,
                filters.get("user_case_summary") if filters else None,
            ),
        )

    def save_analysis_results(
        self,
        user_case_summary: str,
        similar_cases_found: int,
        favorable_precedents: int,
        unfavorable_precedents: int,
        recommendations: List[str],
        confidence_score: float,
    ) -> int:
        """Save case analysis results for future reference"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO case_analysis (
                    user_case_summary, similar_cases_found, favorable_precedents,
                    unfavorable_precedents, recommendations, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    user_case_summary,
                    similar_cases_found,
                    favorable_precedents,
                    unfavorable_precedents,
                    json.dumps(recommendations),
                    confidence_score,
                ),
            )

            analysis_id = cursor.lastrowid
            conn.commit()
            return analysis_id if analysis_id is not None else 0

    def get_case_statistics(self) -> Dict[str, Any]:
        """Get database statistics and insights"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Basic counts
            total_cases = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]

            # Cases by outcome type
            outcome_stats = conn.execute("""
                SELECT
                    CASE
                        WHEN outcome LIKE '%allowed%' OR outcome LIKE '%granted%'
                        THEN 'Favorable'
                        WHEN outcome LIKE '%dismissed%' OR outcome LIKE '%denied%'
                        THEN 'Unfavorable'
                        ELSE 'Other'
                    END as outcome_type,
                    COUNT(*) as count
                FROM cases
                WHERE outcome IS NOT NULL
                GROUP BY outcome_type
            """).fetchall()

            # Most common keywords
            common_keywords = conn.execute("""
                SELECT keyword, COUNT(*) as frequency
                FROM case_keywords
                GROUP BY keyword
                ORDER BY frequency DESC
                LIMIT 20
            """).fetchall()

            # Recent search activity
            recent_searches = conn.execute("""
                SELECT query, COUNT(*) as frequency
                FROM search_history
                WHERE timestamp >= datetime('now', '-30 days')
                GROUP BY query
                ORDER BY frequency DESC
                LIMIT 10
            """).fetchall()

            return {
                "total_cases": total_cases,
                "outcome_statistics": [dict(row) for row in outcome_stats],
                "common_keywords": [dict(row) for row in common_keywords],
                "recent_searches": [dict(row) for row in recent_searches],
                "database_path": str(self.db_path),
            }

    def export_cases(self, output_path: str, format: str = "json") -> str:
        """Export all cases to JSON or CSV format"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cases = conn.execute("""
                SELECT cases.*, GROUP_CONCAT(case_keywords.keyword) as keywords
                FROM cases
                LEFT JOIN case_keywords ON cases.id = case_keywords.case_id
                GROUP BY cases.id
                ORDER BY cases.date DESC
            """).fetchall()

            cases_data = []
            for case in cases:
                case_dict = dict(case)
                if case_dict["keywords"]:
                    case_dict["keywords"] = case_dict["keywords"].split(",")
                else:
                    case_dict["keywords"] = []
                cases_data.append(case_dict)

            output_file = Path(output_path)

            if format.lower() == "json":
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(cases_data, f, indent=2, ensure_ascii=False)
            else:
                # CSV export would go here
                pass

            logger.info(f"Exported {len(cases_data)} cases to {output_file}")
            return str(output_file)

    def close(self):
        """Clean up database connections"""
        # SQLite connections are automatically closed, but this method
        # is here for consistency and future enhancements
        pass
