# Enhanced Legal Intake Workflow for WCB Cases

## 🎯 Overview

The Enhanced Legal Intake Agent provides a comprehensive workflow for processing large WCB (Workers' Compensation Board) file dumps, automatically organizing documents, and preparing structured search points for legal research.

## 🚀 Key Features

### **Automated File Processing**
- **Mass File Ingestion**: Process hundreds of documents at once
- **Intelligent Document Classification**: Identify decisions, letters, medical reports, forms
- **Smart Organization**: Automatically sort files into structured directories
- **Entity Extraction**: Extract claim numbers, dates, medical conditions, and key entities

### **WCB-Specific Intelligence**
- **Document Type Recognition**:
  - Tribunal/Board/Appeal Decisions
  - Claim/Denial/Approval Letters
  - Medical Reports and Assessments
  - Employment Records and Forms
  - General Correspondence

### **Legal Research Preparation**
- **Search Point Generation**: Create targeted search strategies for precedent research
- **Timeline Reconstruction**: Chronological organization of case events
- **Entity Mapping**: Comprehensive extraction of legal entities and relationships
- **Database Integration**: Seamless integration with Legal Case Database

## 📋 Workflow Stages

### **Stage 1: File Scanning and Validation**
```python
# Scan dump directory for supported file types
scan_result = await agent._scan_dump_directory(dump_path)
# Results: file inventory, size analysis, type distribution
```

### **Stage 2: Case Organization Structure**
```python
# Create organized directory structure
org_result = await agent._create_case_organization(case_id)
# Creates: decisions/, letters/, medical_reports/, etc.
```

### **Stage 3: Document Processing and Categorization**
```python
# Process each file: extract content, classify type, organize
process_result = await agent._batch_process_legal_files(dump_path, files)
# Results: categorized files, metadata extraction, organization
```

### **Stage 4: Legal Entity Extraction**
```python
# Extract key legal entities from all documents
entities_result = await agent._extract_case_entities()
# Extracts: claim numbers, dates, medical conditions, employers
```

### **Stage 5: Timeline Reconstruction**
```python
# Build chronological timeline of case events
timeline_result = await agent._reconstruct_case_timeline()
# Results: ordered timeline with document references
```

### **Stage 6: Search Point Generation**
```python
# Generate targeted search strategies for legal research
search_result = await agent._generate_search_points()
# Creates: precedent searches, condition-based queries, case law research
```

### **Stage 7: Legal Research Preparation**
```python
# Prepare structured package for Legal Research Agent
research_result = await agent._prepare_legal_research()
# Output: research package with search points and organized data
```

## 🗂️ Output Directory Structure

After processing, your case will be organized as follows:

```
organized_cases/
└── {case_id}/
    ├── case_metadata.json              # Case processing metadata
    ├── legal_research_package.json     # Research preparation data
    ├── decisions/                      # Tribunal/board decisions
    │   ├── 20240315_tribunal_decision_123.pdf
    │   └── 20240420_appeal_decision_456.pdf
    ├── letters/                        # Correspondence and notifications
    │   ├── 20240301_claim_letter_789.pdf
    │   └── 20240410_denial_letter_101.pdf
    ├── medical_reports/                # Medical assessments and reports
    ├── case_files/                     # Main case documentation
    ├── review_files/                   # Case review documents
    ├── employment_records/             # Employment history
    ├── forms/                          # Application and claim forms
    ├── correspondence/                 # General correspondence
    ├── timeline/
    │   └── case_timeline.json          # Chronological case events
    ├── search_points/
    │   └── legal_search_points.json    # Generated search strategies
    └── unknown/                        # Unclassified documents
```

## 🔧 Usage Examples

### **Basic File Dump Processing**

```python
from enhanced_legal_intake import EnhancedLegalIntakeAgent
from ..core import AgentTask, TaskPriority

# Initialize agent
agent = EnhancedLegalIntakeAgent(
    case_organization_directory="./tmp/organized_cases"
)

# Create processing task
task = AgentTask(
    task_type="process_legal_dump",
    parameters={
        "dump_directory": "/path/to/wcb/files",
        "case_id": "WCB_CASE_2024_001"
    },
    priority=TaskPriority.HIGH
)

# Execute workflow
result = await agent.execute_task(task)

if result["success"]:
    print(f"✅ Case processed: {result['case_id']}")
    print(f"📁 Documents organized: {result['documents_organized']}")
    print(f"🔍 Search points: {result['search_points_generated']}")
```

### **Batch Processing Multiple Cases**

```python
# Process multiple file dumps as separate cases
task = AgentTask(
    task_type="batch_legal_organize",
    parameters={
        "dump_directories": [
            "/path/to/case1/files",
            "/path/to/case2/files",
            "/path/to/case3/files"
        ]
    },
    priority=TaskPriority.HIGH
)

result = await agent.execute_task(task)
```

### **Document Type Identification**

```python
# Identify specific document types
task = AgentTask(
    task_type="identify_wcb_document_type",
    parameters={
        "content": document_text,
        "file_path": "/path/to/document.pdf"
    }
)

result = await agent.execute_task(task)
print(f"Document type: {result['wcb_document_type']}")
print(f"Confidence: {result['confidence']}")
```

## 🔍 Search Point Types Generated

The system automatically generates different types of search points for the Legal Research Agent:

### **Precedent Searches**
- **Purpose**: Find similar WCB decisions for precedent analysis
- **Keywords**: "similar decisions", "comparable cases", specific conditions
- **Priority**: High
- **Context**: Precedent analysis for decision outcomes

### **Medical Precedent Searches**
- **Purpose**: Find cases with similar medical evidence
- **Keywords**: "medical evidence", specific conditions, medical assessments
- **Priority**: Medium
- **Context**: Medical evidence comparison and analysis

### **Condition-Based Searches**
- **Purpose**: Find precedent cases involving specific medical conditions
- **Keywords**: Condition names, "case law", "precedent"
- **Priority**: High
- **Context**: Condition-specific legal precedent research

### **Temporal Relationship Searches**
- **Purpose**: Find cases with similar timelines or procedural patterns
- **Keywords**: Timeline events, procedural steps
- **Priority**: Medium
- **Context**: Procedural precedent and timeline analysis

## 🎯 Integration with Legal Research Agent

The Enhanced Legal Intake Agent seamlessly integrates with the Legal Research Agent:

```python
# After intake processing completes, the Legal Research Agent can use:

# 1. Generated search points
search_points = load_search_points(case_id)
for point in search_points:
    research_results = await legal_research_agent.execute_search(point)

# 2. Organized case structure
case_directory = get_case_directory(case_id)
decisions = load_documents(case_directory / "decisions")
medical_reports = load_documents(case_directory / "medical_reports")

# 3. Extracted entities for targeted searches
entities = load_case_entities(case_id)
similar_cases = await legal_research_agent.find_similar_cases(
    medical_conditions=entities["medical_conditions"],
    case_references=entities["case_references"]
)
```

## 📊 Processing Statistics

After completion, you'll receive comprehensive statistics:

- **Total Files Processed**: Number of documents successfully processed
- **Documents Organized**: Files categorized and organized
- **Search Points Generated**: Number of research strategies created
- **Timeline Events**: Chronological events extracted
- **Entity Extraction**: Legal entities identified and categorized
- **Processing Time**: Complete workflow duration

## 🚦 Next Steps After Processing

1. **Review Organized Documents**: Examine the structured case directory
2. **Execute Legal Research**: Use generated search points with Legal Research Agent
3. **Analyze Case Timeline**: Review chronological case progression
4. **Prepare Legal Arguments**: Use categorized evidence and precedent research
5. **Generate Case Summary**: Create comprehensive case analysis report

## 🔧 Configuration Options

### **Agent Initialization**
```python
agent = EnhancedLegalIntakeAgent(
    legal_case_db=custom_database,                    # Custom legal database
    case_organization_directory="./custom/path",     # Custom output directory
    intake_directory="./custom/intake",              # Custom intake directory
    processed_directory="./custom/processed",        # Custom processing directory
    max_file_size_mb=200                            # Maximum file size limit
)
```

### **Processing Parameters**
```python
task = AgentTask(
    task_type="process_legal_dump",
    parameters={
        "dump_directory": "/path/to/files",
        "case_id": "custom_case_id",                 # Optional custom case ID
        "classification_threshold": 0.8,            # Confidence threshold for classification
        "entity_extraction_depth": "comprehensive"   # Level of entity extraction
    }
)
```

## 🐛 Troubleshooting

### **Common Issues**

**Files not being processed**:
- Check file formats (PDF, DOCX, TXT, HTML, JSON supported)
- Verify file size limits (default: 100MB)
- Ensure proper file permissions

**Low classification confidence**:
- Review document content quality
- Check if documents contain WCB-specific terminology
- Consider manual classification for edge cases

**Missing search points**:
- Verify entity extraction completed successfully
- Check that legal entities were found in documents
- Review document types for search point generation

### **Performance Optimization**

- Use SSD storage for faster file processing
- Increase memory allocation for large document sets
- Process in batches for very large file dumps
- Enable parallel processing for multiple cases

## 📝 Logging and Monitoring

The system provides comprehensive logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Logs include:
# - File processing progress
# - Document classification results
# - Entity extraction outcomes
# - Search point generation
# - Error handling and recovery
```

## 🔗 Related Components

- **[IntakeAgent](./intake_agent.py)**: Base document processing agent
- **[Legal Research Agent](../legal_research/)**: Legal precedent research
- **[Legal Case Database](../legal_research/legal_case_database.py)**: Case storage and search
- **[Cross Reference Agent](../cross_reference/)**: Document relationship analysis

---

This enhanced workflow transforms chaotic file dumps into organized, searchable case structures ready for sophisticated legal research and analysis.