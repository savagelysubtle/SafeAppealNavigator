## README.md

```markdown
# savagelysubtle-airesearchagent - Architectural Design & Implementation Plan

## 1. Project Overview & Vision

**savagelysubtle-airesearchagent** is a sophisticated, distributed multi-agent system designed for advanced legal research. It leverages a microservice architecture to provide a modular, scalable, and maintainable platform for tasks including document ingestion, legal research, data analysis, and report generation.

The vision is to create a powerful AI assistant that can significantly augment legal professionals' capabilities by automating complex research workflows, providing insightful analysis, and ensuring data traceability and consistency. The system is built with a focus on modern AI frameworks, standardized communication protocols, and robust data management.

**WebUI:** is built on Gradio and supports most of `browser-use` functionalities. This UI is designed to be user-friendly and enables easy interaction with the browser agent.

**Expanded LLM Support:** We've integrated support for various Large Language Models (LLMs), including: Google, OpenAI, Azure OpenAI, Anthropic, DeepSeek, Ollama etc. And we plan to add support for even more models in the future.

**Custom Browser Support:** You can use your own browser with our tool, eliminating the need to re-login to sites or deal with other authentication challenges. This feature also supports high-definition screen recording.

**Persistent Browser Sessions:** You can choose to keep the browser window open between AI tasks, allowing you to see the complete history and state of AI interactions.

## Documentation

This project uses MkDocs to generate documentation. To build and view the documentation locally, follow these steps:

1.  **Install MkDocs and the Material theme:**
    ```bash
    pip install mkdocs mkdocs-material
    ```
2.  **Start the development server:**
    ```bash
    mkdocs serve
    ```
    This will start a local server, usually at `http://127.0.0.1:8000/`.
3.  **Build the static site (optional):**
    ```bash
    mkdocs build
    ```
    This will create a `site` directory with the static HTML files.
