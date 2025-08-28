# FILE: src/ai_research_assistant/agents/ceo_agent/prompts.py

"""
CEO Agent Prompts and Delegation Patterns

This module contains comprehensive prompts and decision-making frameworks for the CEO Agent.
The CEO Agent serves as the primary user interface and intelligent task router, delegating
complex operations to specialized agents while handling simple interactions directly.

Key Principles:
- Clear delegation patterns for common tasks
- User autonomy for critical decisions
- Contextual guidance for complex workflows
- A2A (Agent-to-Agent) communication optimization
- SafeAppealNavigator legal case management context
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ============================================================================
# SAFEAPPEALNAVIGATOR CONTEXT PATTERNS
# ============================================================================

SAFEAPPEALNAVIGATOR_CONTEXT = {
    "app_purpose": "WorkSafe BC and WCAT appeals management system",
    "primary_users": [
        "injured_workers",
        "legal_advocates",
        "family_members",
        "support_organizations",
    ],
    "main_functions": [
        "case_organization",
        "legal_research",
        "document_management",
        "appeal_preparation",
        "deadline_tracking",
        "evidence_organization",
    ],
    "document_types": [
        "medical_reports",
        "wcat_decisions",
        "legal_correspondence",
        "appeal_letters",
        "case_briefs",
        "evidence_packages",
        "policy_documents",
    ],
    "database_collections": {
        "case_files": "Primary case documents and correspondence",
        "medical_records": "Medical reports, assessments, and treatment records",
        "wcat_decisions": "WCAT decision precedents and similar cases",
        "legal_policies": "WorkSafe BC policies and procedures",
        "templates": "Appeal letter templates and legal document formats",
        "research_findings": "Legal research and precedent analysis results",
    },
}

# ============================================================================
# CORE DELEGATION PATTERNS (Updated for SafeAppealNavigator)
# ============================================================================

DELEGATION_PATTERNS = {
    "database_operations": {
        "triggers": [
            "create database",
            "setup database",
            "new database",
            "build database",
            "database for the app",
            "case database",
            "legal database",
            "create collection",
            "setup collection",
            "new collection",
            "store documents",
            "add documents",
            "document intake",
            "search documents",
            "find documents",
            "query database",
            "database maintenance",
            "optimize database",
            "clean database",
            "chromadb",
            "vector database",
            "vector search",
        ],
        "delegate_to": "orchestrator",
        "reasoning": "Database operations require specialized ChromaDB MCP tools and vector operations for legal case management",
        "prompt_template": (
            "I need to handle a database operation for SafeAppealNavigator: {user_request}. "
            "This involves setting up ChromaDB vector database collections for legal case management including "
            "case files, medical records, WCAT decisions, legal policies, and research findings. "
            "I'll delegate this to the Orchestrator Agent who has direct access to ChromaDB MCP tools and "
            "understands the legal case management context."
        ),
    },
    "document_processing": {
        "triggers": [
            "process document",
            "analyze document",
            "read file",
            "extract text",
            "parse document",
            "document analysis",
            "pdf",
            "docx",
            "text file",
            "upload file",
            "legal document",
            "medical report",
            "wcat decision",
            "case file",
            "appeal letter",
            "contract analysis",
            "brief analysis",
        ],
        "delegate_to": "orchestrator",
        "reasoning": "Document processing requires file I/O, text extraction, and legal document analysis tools",
        "prompt_template": (
            "I need to handle document processing for SafeAppealNavigator: {user_request}. "
            "This requires specialized document handling tools for legal and medical documents, "
            "potentially including WCAT decisions, medical reports, and legal correspondence. "
            "I'll delegate this to the Orchestrator Agent for proper coordination."
        ),
    },
    "research_tasks": {
        "triggers": [
            "research",
            "investigate",
            "find information",
            "web search",
            "browse",
            "lookup",
            "explore",
            "legal research",
            "wcat research",
            "worksafe research",
            "case law",
            "precedent",
            "statute",
            "policy research",
            "similar cases",
            "appeal decisions",
        ],
        "delegate_to": "orchestrator",
        "reasoning": "Research requires browser automation, web scraping, and legal database searches",
        "prompt_template": (
            "I need to conduct research for SafeAppealNavigator: {user_request}. "
            "This requires web browsing and legal research capabilities to find WCAT decisions, "
            "WorkSafe BC policies, and similar case precedents. "
            "I'll delegate this to the Orchestrator Agent who can coordinate the research workflow."
        ),
    },
    "case_management": {
        "triggers": [
            "new case",
            "create case",
            "case setup",
            "start case",
            "injury case",
            "appeal case",
            "wcat case",
            "workers compensation",
            "case organization",
            "timeline",
            "deadline",
            "evidence",
            "medical timeline",
        ],
        "delegate_to": "orchestrator",
        "reasoning": "Case management requires coordinated database, document, and research operations",
        "prompt_template": (
            "I need to handle case management for SafeAppealNavigator: {user_request}. "
            "This involves creating case file organization, setting up document collections, "
            "establishing timelines, and preparing evidence packages for WorkSafe BC or WCAT appeals. "
            "I'll delegate this to the Orchestrator Agent for comprehensive case setup."
        ),
    },
    "appeal_preparation": {
        "triggers": [
            "appeal",
            "prepare appeal",
            "appeal letter",
            "appeal documents",
            "wcat appeal",
            "worksafe appeal",
            "hearing preparation",
            "evidence package",
            "case brief",
            "legal argument",
            "appeal submission",
        ],
        "delegate_to": "orchestrator",
        "reasoning": "Appeal preparation requires legal document creation, research, and evidence organization",
        "prompt_template": (
            "I need to handle appeal preparation for SafeAppealNavigator: {user_request}. "
            "This involves coordinating legal research, document analysis, evidence organization, "
            "and professional appeal document creation for WorkSafe BC or WCAT proceedings. "
            "I'll delegate this to the Orchestrator Agent for comprehensive appeal preparation."
        ),
    },
    "multi_step_workflows": {
        "triggers": [
            "workflow",
            "process",
            "step by step",
            "procedure",
            "multiple steps",
            "complex task",
            "end-to-end",
            "automation",
            "pipeline",
            "sequence of tasks",
            "case workflow",
            "appeal workflow",
        ],
        "delegate_to": "orchestrator",
        "reasoning": "Multi-step workflows require coordination between multiple specialized agents",
        "prompt_template": (
            "I need to handle a complex workflow for SafeAppealNavigator: {user_request}. "
            "This involves multiple steps that may require coordination between legal research, "
            "document processing, database operations, and appeal preparation agents. "
            "I'll delegate this to the Orchestrator Agent for proper workflow management."
        ),
    },
    "legal_analysis": {
        "triggers": [
            "legal analysis",
            "legal opinion",
            "case analysis",
            "appeal analysis",
            "wcat analysis",
            "policy analysis",
            "precedent analysis",
            "legal research",
            "compliance",
            "regulation",
            "statute",
            "legal document",
            "legal strategy",
            "case strength",
            "appeal chances",
        ],
        "delegate_to": "orchestrator",
        "reasoning": "Legal analysis requires specialized legal knowledge, research, and document processing",
        "prompt_template": (
            "I need to handle legal analysis for SafeAppealNavigator: {user_request}. "
            "This requires specialized legal knowledge for WorkSafe BC and WCAT processes, "
            "policy analysis, precedent research, and case strength assessment. "
            "I'll delegate this to the Orchestrator Agent who can coordinate with legal research agents."
        ),
    },
}

# ============================================================================
# SAFEAPPEALNAVIGATOR-SPECIFIC INTERACTION PATTERNS
# ============================================================================

SIMPLE_INTERACTIONS = {
    "greetings": {
        "triggers": [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "greetings",
            "howdy",
            "what's up",
        ],
        "response_template": (
            "Hello! I'm the CEO Agent of SafeAppealNavigator - your intelligent companion for navigating "
            "WorkSafe BC and WCAT appeals. I can help you with:\n\n"
            "🗄️ **Case Database Setup**: Creating organized collections for case files, medical records, and legal documents\n"
            "📄 **Document Management**: Processing medical reports, WCAT decisions, and legal correspondence\n"
            "🔍 **Legal Research**: Finding similar cases, WCAT precedents, and relevant WorkSafe BC policies\n"
            "⚖️ **Appeal Preparation**: Organizing evidence, creating appeal letters, and preparing case briefs\n"
            "📅 **Case Organization**: Timeline building, deadline tracking, and evidence categorization\n"
            "🎯 **Strategic Analysis**: Case strength assessment and gap identification\n\n"
            "Whether you're an injured worker, legal advocate, or family member helping with an appeal, "
            "I'm here to make the complex legal process more manageable. What would you like me to help you with today?"
        ),
    },
    "capabilities": {
        "triggers": [
            "what can you do",
            "help",
            "capabilities",
            "features",
            "functions",
            "what are your abilities",
            "how can you help",
            "safeappealnavigator features",
        ],
        "response_template": (
            "I'm designed to help you navigate WorkSafe BC and WCAT appeals with confidence. Here's what I can do:\n\n"
            "**🎯 Case Management:**\n"
            "• Set up organized case databases with proper collections\n"
            "• Create timelines of injury, treatment, and legal milestones\n"
            "• Track deadlines for appeals and hearing dates\n"
            "• Organize evidence and supporting documentation\n\n"
            "**📋 Document Processing:**\n"
            "• Analyze medical reports and treatment records\n"
            "• Process WCAT decisions and legal correspondence\n"
            "• Extract key information from complex legal documents\n"
            "• Create professional appeal letters and case briefs\n\n"
            "**🔍 Legal Research:**\n"
            "• Find WCAT decisions with similar circumstances\n"
            "• Research relevant WorkSafe BC policies and procedures\n"
            "• Identify favorable precedents and legal arguments\n"
            "• Assess case strength based on similar successful appeals\n\n"
            "**⚖️ Appeal Preparation:**\n"
            "• Generate structured appeal submissions\n"
            "• Organize evidence packages for maximum impact\n"
            "• Create medical summaries in clear, compelling language\n"
            "• Prepare talking points for WCAT hearings\n\n"
            "I coordinate with specialized agents through our A2A protocol to ensure "
            "you get expert-level assistance for each type of task. Ready to get started?"
        ),
    },
    "status": {
        "triggers": [
            "status",
            "how are you",
            "are you working",
            "system status",
            "health check",
            "are you online",
            "connection test",
            "app status",
        ],
        "response_template": (
            "✅ **SafeAppealNavigator System Status**: All systems operational\n"
            "🤖 **CEO Agent**: Ready and responsive for legal case management\n"
            "🔗 **A2A Protocol**: Connected to specialized legal and database agents\n"
            "⚡ **Available Agents**: Database (ChromaDB), Document Processing, Legal Research, Browser Research\n"
            "🗄️ **Database Tools**: ChromaDB vector search ready for legal document management\n"
            "📄 **Document Tools**: File I/O ready for medical reports and legal documents\n"
            "🌐 **Research Tools**: Web search ready for WCAT and WorkSafe BC research\n\n"
            "SafeAppealNavigator is ready to help you organize your case, research precedents, "
            "and prepare compelling appeals. What legal challenge can I help you tackle today?"
        ),
    },
}

# ============================================================================
# SAFEAPPEALNAVIGATOR DATABASE SETUP PATTERNS
# ============================================================================

SAFEAPPEALNAVIGATOR_DATABASE_PATTERNS = {
    "new_case_database": {
        "user_triggers": [
            "new database for app",
            "database for the app",
            "build database",
            "setup case database",
            "create legal database",
            "new case system",
            "setup safeappealnavigator",
            "initialize case management",
        ],
        "analysis_prompt": (
            "🏗️ **SafeAppealNavigator Database Setup**\n\n"
            "I'll help you set up a comprehensive case management database optimized for WorkSafe BC and WCAT appeals. "
            "This will create specialized ChromaDB collections for:\n\n"
            "**📁 Case Organization Collections:**\n"
            "• **case_files** - Primary case documents and correspondence\n"
            "• **medical_records** - Medical reports, assessments, treatment records\n"
            "• **wcat_decisions** - WCAT precedents and similar case decisions\n"
            "• **legal_policies** - WorkSafe BC policies and procedures\n"
            "• **templates** - Appeal letter templates and legal document formats\n"
            "• **research_findings** - Legal research results and precedent analysis\n\n"
            "**🎯 Optimized For:**\n"
            "• Semantic search across legal and medical documents\n"
            "• Case similarity matching for precedent research\n"
            "• Evidence organization and retrieval\n"
            "• Timeline and deadline management\n\n"
            "This setup will enable powerful legal research, case organization, and appeal preparation. "
            "Shall I proceed with creating this comprehensive legal case management database?"
        ),
        "delegation_instruction": (
            "Please create a comprehensive SafeAppealNavigator database setup using ChromaDB MCP tools. "
            "Create the following specialized collections for legal case management:\n\n"
            "1. **case_files** - Primary case documents, correspondence, claim forms\n"
            "2. **medical_records** - Medical reports, assessments, treatment records, IME reports\n"
            "3. **wcat_decisions** - WCAT decision precedents, similar cases, appeal outcomes\n"
            "4. **legal_policies** - WorkSafe BC policies, procedures, regulations, guidelines\n"
            "5. **templates** - Appeal letter templates, legal document formats, form templates\n"
            "6. **research_findings** - Legal research results, precedent analysis, case law\n\n"
            "Use optimal HNSW parameters for legal document search and configure metadata schemas "
            "appropriate for WorkSafe BC and WCAT case management. The user request was: {user_request}"
        ),
    },
    "case_specific_database": {
        "user_triggers": [
            "database for my case",
            "setup my case",
            "organize my appeal",
            "new injury case",
            "workers comp case",
            "wcat appeal case",
        ],
        "analysis_prompt": (
            "📋 **Individual Case Database Setup**\n\n"
            "I'll create a personalized case database for your specific WorkSafe BC or WCAT matter:\n\n"
            "**Case Information Needed:**\n"
            "• Type of injury/condition\n"
            "• Current status (initial claim, appeal, WCAT hearing)\n"
            "• Key dates (injury date, claim submission, decisions)\n"
            "• Primary issues in dispute\n\n"
            "**Collections I'll Create:**\n"
            "• Your case timeline and documents\n"
            "• Relevant medical evidence\n"
            "• Similar WCAT cases for reference\n"
            "• Applicable policies and procedures\n\n"
            "What type of case are you working on? This will help me optimize the database structure."
        ),
        "delegation_instruction": (
            "Create a personalized case database for an individual WorkSafe BC/WCAT matter. "
            "Set up collections specific to their case type and organize for optimal case management. "
            "User request: {user_request}"
        ),
    },
    "research_database": {
        "user_triggers": [
            "research database",
            "precedent database",
            "wcat decisions database",
            "policy research database",
            "legal research collection",
        ],
        "analysis_prompt": (
            "🔍 **Legal Research Database Setup**\n\n"
            "I'll create a specialized research database focused on legal precedents and policy analysis:\n\n"
            "**Research Collections:**\n"
            "• WCAT decision archive with searchable precedents\n"
            "• WorkSafe BC policy library\n"
            "• Case law and legal precedents\n"
            "• Research methodology and search strategies\n\n"
            "**Search Capabilities:**\n"
            "• Semantic similarity matching for similar cases\n"
            "• Policy-to-case correlation analysis\n"
            "• Precedent strength assessment\n"
            "• Research gap identification\n\n"
            "This will enable powerful legal research for building strong appeals. Proceed?"
        ),
        "delegation_instruction": (
            "Create a legal research database optimized for WCAT precedent analysis and "
            "WorkSafe BC policy research. Focus on semantic search capabilities for case similarity. "
            "User request: {user_request}"
        ),
    },
}

# ============================================================================
# CRITICAL THINKING FRAMEWORKS
# ============================================================================

CRITICAL_THINKING_PROMPTS = {
    "task_analysis": (
        "Before I proceed, let me analyze this request:\n\n"
        "**Task Complexity**: {complexity_level}\n"
        "**Required Capabilities**: {required_capabilities}\n"
        "**Best Approach**: {recommended_approach}\n"
        "**Estimated Steps**: {estimated_steps}\n\n"
        "Would you like me to proceed with this approach, or would you prefer to modify the strategy?"
    ),
    "delegation_reasoning": (
        "I'm recommending delegation to the {target_agent} because:\n\n"
        "**Why This Agent**: {agent_reasoning}\n"
        "**Required Tools**: {required_tools}\n"
        "**Expected Outcome**: {expected_outcome}\n\n"
        "This ensures you get specialized expertise for optimal results. Shall I proceed?"
    ),
    "user_confirmation": (
        "I want to make sure I understand your request correctly:\n\n"
        "**My Understanding**: {interpretation}\n"
        "**Planned Action**: {planned_action}\n"
        "**Alternative Approaches**: {alternatives}\n\n"
        "Is this what you're looking for, or would you like me to adjust my approach?"
    ),
    "complexity_assessment": (
        "This request involves {complexity_indicators}. "
        "Given the complexity, I recommend:\n\n"
        "**Option 1**: {simple_approach}\n"
        "**Option 2**: {comprehensive_approach}\n"
        "**Option 3**: {alternative_approach}\n\n"
        "Which approach aligns best with your needs and timeline?"
    ),
}

# ============================================================================
# DATABASE-SPECIFIC DELEGATION PROMPTS
# ============================================================================

DATABASE_DELEGATION_PROMPTS = {
    "new_database_setup": {
        "user_triggers": [
            "start a new database",
            "create new database",
            "setup database",
            "initialize database",
            "new chromadb",
            "create collection",
        ],
        "analysis_prompt": (
            "I see you want to set up a new database. Let me help you plan this:\n\n"
            "**Database Type**: ChromaDB Vector Database (via MCP tools)\n"
            "**Available Tools**: chroma_create_collection, chroma_add_documents, chroma_list_collections\n"
            "**Purpose**: {intended_purpose}\n"
            "**Document Types**: {document_types}\n"
            "**Collection Strategy**: {collection_strategy}\n\n"
            "I'll delegate this to the Orchestrator Agent, who has direct access to ChromaDB MCP tools "
            "for optimal database setup. Shall I proceed?"
        ),
        "delegation_instruction": (
            "Please use the ChromaDB MCP tools to create a new database setup. "
            "The user wants: {user_request}. "
            "Use chroma_create_collection for collection creation, and configure optimal settings for {use_case}."
        ),
    },
    "document_storage": {
        "user_triggers": [
            "store documents",
            "add documents",
            "upload files",
            "save to database",
            "document intake",
        ],
        "analysis_prompt": (
            "I'll help you store documents in the database:\n\n"
            "**Storage Strategy**: {storage_strategy}\n"
            "**Collection Target**: {target_collection}\n"
            "**ChromaDB Tools**: chroma_add_documents, chroma_get_collection_info\n"
            "**Processing Needed**: {processing_requirements}\n\n"
            "This will use the chroma_add_documents MCP tool for efficient document storage with embeddings. "
            "Should I coordinate this workflow?"
        ),
        "delegation_instruction": (
            "Please coordinate document storage workflow: {user_request}. "
            "Use chroma_add_documents MCP tool to store documents in ChromaDB with proper embeddings and metadata."
        ),
    },
    "vector_search": {
        "user_triggers": [
            "search documents",
            "find similar",
            "vector search",
            "semantic search",
            "query database",
        ],
        "analysis_prompt": (
            "I'll set up a vector search for you:\n\n"
            "**Search Type**: {search_type}\n"
            "**Target Collections**: {collections}\n"
            "**ChromaDB Tools**: chroma_query_documents, chroma_get_documents\n"
            "**Expected Results**: {result_expectations}\n\n"
            "I'll use the chroma_query_documents MCP tool for semantic vector similarity search. "
            "Shall I initiate the search?"
        ),
        "delegation_instruction": (
            "Please perform vector search using ChromaDB MCP tools: {user_request}. "
            "Use chroma_query_documents for semantic search and return ranked results with relevance scores."
        ),
    },
}

# ============================================================================
# ENHANCED SYSTEM PROMPT FOR SAFEAPPEALNAVIGATOR
# ============================================================================

ENHANCED_SYSTEM_PROMPT = """
You are the CEO Agent of SafeAppealNavigator, an advanced AI system designed to help injured workers,
legal advocates, and their families navigate WorkSafe BC and WCAT appeals with confidence and expertise.

**SafeAppealNavigator Context:**
This system specializes in Workers' Compensation appeals, helping users organize case files, research
legal precedents, prepare professional appeals, and build compelling evidence packages for WCAT hearings.

**Core Responsibilities:**
1. **Intelligent Task Routing**: Analyze user requests and delegate to appropriate specialized agents
2. **Legal Case Guidance**: Provide context-aware assistance for WorkSafe BC and WCAT processes
3. **Database Coordination**: Oversee creation and management of legal case databases
4. **Workflow Orchestration**: Ensure seamless collaboration between specialized agents

**Delegation Philosophy for Legal Cases:**
- Delegate complex legal tasks requiring specialized tools (database, documents, research)
- Handle simple interactions and guidance directly (greetings, status, basic questions)
- Always explain legal context and reasoning when delegating
- Provide options tailored to WorkSafe BC and WCAT processes
- Preserve user agency in critical legal decision-making

**Specialized Agents Available:**
- **Orchestrator Agent**: Coordinates complex legal workflows and has direct access to ChromaDB MCP tools
- **Database Agent**: ChromaDB specialist for legal case document management and vector search
- **Document Agent**: Legal document processing, medical report analysis, appeal letter creation
- **Browser Agent**: Legal research, WCAT decision searches, WorkSafe BC policy research
- **Legal Manager Agent**: Legal workflow coordination, citation verification, case analysis

**Legal Case Understanding:**
You understand the unique challenges of WorkSafe BC and WCAT appeals including:
- Complex medical evidence requirements
- Strict deadlines and procedural requirements
- Need for precedent research and policy analysis
- Importance of organized evidence packages
- Emotional and financial stakes for injured workers

**Communication Style for Legal Matters:**
- Be professional yet empathetic to injured workers' situations
- Explain legal processes in plain language when needed
- Provide clear next steps and realistic timelines
- Offer multiple approaches for complex legal strategies
- Always confirm understanding before proceeding with legal actions
- Respect the serious nature of workers' compensation appeals

**Database Setup Expertise:**
When users request database creation "for the app", understand this means creating a comprehensive
legal case management system with collections for case files, medical records, WCAT decisions,
legal policies, templates, and research findings - all optimized for WorkSafe BC and WCAT appeals.

Remember: Every interaction may involve someone's livelihood, health benefits, or financial security.
Approach each request with the gravity and expertise it deserves while maintaining accessibility and hope.
"""

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def analyze_user_request(user_input: str) -> Dict[str, Any]:
    """
    Analyze user input to determine delegation pattern and approach for SafeAppealNavigator.

    Args:
        user_input: The user's request text

    Returns:
        Analysis dictionary with delegation recommendations
    """
    user_input_lower = user_input.lower()

    # Check for SafeAppealNavigator database setup patterns first
    for pattern_name, pattern_info in SAFEAPPEALNAVIGATOR_DATABASE_PATTERNS.items():
        for trigger in pattern_info["user_triggers"]:
            if trigger in user_input_lower:
                return {
                    "pattern_type": "safeappealnavigator_database",
                    "pattern_name": pattern_name,
                    "delegate_to": "orchestrator",
                    "reasoning": f"SafeAppealNavigator {pattern_name} setup required",
                    "analysis_prompt": pattern_info["analysis_prompt"],
                    "delegation_instruction": pattern_info["delegation_instruction"],
                }

    # Check for general delegation patterns
    for pattern_name, pattern_info in DELEGATION_PATTERNS.items():
        for trigger in pattern_info["triggers"]:
            if trigger in user_input_lower:
                return {
                    "pattern_type": "delegation",
                    "pattern_name": pattern_name,
                    "delegate_to": pattern_info["delegate_to"],
                    "reasoning": pattern_info["reasoning"],
                    "prompt_template": pattern_info["prompt_template"],
                }

    # Check for simple interactions
    for interaction_type, interaction_info in SIMPLE_INTERACTIONS.items():
        for trigger in interaction_info["triggers"]:
            if trigger in user_input_lower:
                return {
                    "pattern_type": "simple",
                    "interaction_type": interaction_type,
                    "response_template": interaction_info["response_template"],
                }

    # Default: complex task requiring analysis
    return {
        "pattern_type": "complex",
        "requires_analysis": True,
        "recommended_approach": "delegation_with_analysis",
    }


def get_delegation_prompt(pattern_name: str, user_request: str) -> str:
    """
    Get formatted delegation prompt for a specific pattern.

    Args:
        pattern_name: Name of the delegation pattern
        user_request: Original user request

    Returns:
        Formatted prompt for delegation
    """
    if pattern_name in DELEGATION_PATTERNS:
        template = DELEGATION_PATTERNS[pattern_name]["prompt_template"]
        return template.format(user_request=user_request)

    return f"I need to handle this request: {user_request}. Let me delegate this to the appropriate agent."


def get_database_delegation_prompt(
    operation_type: str, user_request: str, **kwargs
) -> Dict[str, str]:
    """
    Get specialized database delegation prompts.

    Args:
        operation_type: Type of database operation
        user_request: Original user request
        **kwargs: Additional context parameters

    Returns:
        Dictionary with analysis and delegation prompts
    """
    if operation_type in DATABASE_DELEGATION_PROMPTS:
        prompts = DATABASE_DELEGATION_PROMPTS[operation_type]

        return {
            "analysis": prompts["analysis_prompt"].format(
                user_request=user_request, **kwargs
            ),
            "delegation": prompts["delegation_instruction"].format(
                user_request=user_request, **kwargs
            ),
        }

    return {
        "analysis": f"I'll help you with this database operation: {user_request}",
        "delegation": f"Please handle this database request: {user_request}",
    }


def should_delegate(user_input: str) -> bool:
    """
    Determine if a user request should be delegated or handled directly.

    Args:
        user_input: The user's request text

    Returns:
        True if should delegate, False if handle directly
    """
    analysis = analyze_user_request(user_input)
    return analysis["pattern_type"] in ["delegation", "complex"]


def get_critical_thinking_prompt(prompt_type: str, **kwargs) -> str:
    """
    Get a critical thinking framework prompt.

    Args:
        prompt_type: Type of critical thinking prompt
        **kwargs: Context variables for the prompt

    Returns:
        Formatted critical thinking prompt
    """
    if prompt_type in CRITICAL_THINKING_PROMPTS:
        return CRITICAL_THINKING_PROMPTS[prompt_type].format(**kwargs)

    return "Let me analyze this request to provide the best assistance."


# ============================================================================
# EXPORT ALL PROMPTS AND UTILITIES
# ============================================================================

__all__ = [
    "DELEGATION_PATTERNS",
    "SIMPLE_INTERACTIONS",
    "CRITICAL_THINKING_PROMPTS",
    "DATABASE_DELEGATION_PROMPTS",
    "ENHANCED_SYSTEM_PROMPT",
    "analyze_user_request",
    "get_delegation_prompt",
    "get_database_delegation_prompt",
    "should_delegate",
    "get_critical_thinking_prompt",
]
