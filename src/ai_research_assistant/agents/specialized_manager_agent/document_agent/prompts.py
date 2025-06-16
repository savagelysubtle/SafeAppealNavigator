# src/ai_research_assistant/agents/document_processing_coordinator/prompts.py

# Prompts for the DocumentProcessingCoordinator's internal Pydantic AI agent,
# if it uses LLM for tasks like metadata tagging or summarization during processing.

EXTRACT_METADATA_FROM_TEXT_PROMPT = """
Given the following document text, extract key metadata.
Focus on identifying: Title, Author(s), Publication Date, Document Type (e.g., legal brief, medical report, contract), Key Entities (people, organizations, locations mentioned), and a brief 1-2 sentence summary.

Document Text:
{document_text_snippet}

Respond in JSON format with the following keys: "title", "authors", "publication_date", "document_type", "key_entities", "summary".
If a piece of metadata is not found, use null or an empty list as appropriate.
"""

OCR_CORRECTION_PROMPT = """
The following text was extracted via OCR and may contain errors.
Please review and correct common OCR mistakes, improve formatting, and ensure readability.
Pay attention to broken words, misrecognized characters, and inconsistent spacing.

OCR Text:
{ocr_text}

Return the corrected text.
"""