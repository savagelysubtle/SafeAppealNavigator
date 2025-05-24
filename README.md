<img src="./assets/web-ui.png" alt="Browser Use Web UI" width="full"/>

<br/>

[![GitHub stars](https://img.shields.io/github/stars/browser-use/web-ui?style=social)](https://github.com/browser-use/web-ui/stargazers)
[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)
[![Documentation](https://img.shields.io/badge/Documentation-📕-blue)](https://docs.browser-use.com)
[![WarmShao](https://img.shields.io/twitter/follow/warmshao?style=social)](https://x.com/warmshao)

This project builds upon the foundation of the [browser-use](https://github.com/browser-use/browser-use), which is designed to make websites accessible for AI agents.

We would like to officially thank [WarmShao](https://github.com/warmshao) for his contribution to this project.

**WebUI:** is built on Gradio and supports most of `browser-use` functionalities. This UI is designed to be user-friendly and enables easy interaction with the browser agent.

**Expanded LLM Support:** We've integrated support for various Large Language Models (LLMs), including: Google, OpenAI, Azure OpenAI, Anthropic, DeepSeek, Ollama etc. And we plan to add support for even more models in the future.

**Custom Browser Support:** You can use your own browser with our tool, eliminating the need to re-login to sites or deal with other authentication challenges. This feature also supports high-definition screen recording.

**Persistent Browser Sessions:** You can choose to keep the browser window open between AI tasks, allowing you to see the complete history and state of AI interactions.

<video src="https://github.com/user-attachments/assets/56bc7080-f2e3-4367-af22-6bf2245ff6cb" controls="controls">Your browser does not support playing this video!</video>

## Installation Guide

### Option 1: Local Installation

Read the [quickstart guide](https://docs.browser-use.com/quickstart#prepare-the-environment) or follow the steps below to get started.

#### Step 1: Clone the Repository
```bash
git clone https://github.com/browser-use/web-ui.git
cd web-ui
```

#### Step 2: Set Up Python Environment
We recommend using [uv](https://docs.astral.sh/uv/) for managing the Python environment.

Using uv (recommended):
```bash
uv venv --python 3.11
```

Activate the virtual environment:
- Windows (Command Prompt):
```cmd
.venv\Scripts\activate
```
- Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```
- macOS/Linux:
```bash
source .venv/bin/activate
```

#### Step 3: Install Dependencies
Install Python packages:
```bash
uv pip install -r requirements.txt
```

Install Browsers in playwright.
```bash
playwright install --with-deps
```
Or you can install specific browsers by running:
```bash
playwright install chromium --with-deps
```

#### Step 4: Configure Environment
1. Create a copy of the example environment file:
- Windows (Command Prompt):
```bash
copy .env.example .env
```
- macOS/Linux/Windows (PowerShell):
```bash
cp .env.example .env
```
2. Open `.env` in your preferred text editor and add your API keys and other settings

#### Step 5: Enjoy the web-ui
1.  **Run the WebUI:**
    ```bash
    python webui.py --ip 127.0.0.1 --port 7788
    ```
2. **Access the WebUI:** Open your web browser and navigate to `http://127.0.0.1:7788`.
3. **Using Your Own Browser(Optional):**
    - Set `BROWSER_PATH` to the executable path of your browser and `BROWSER_USER_DATA` to the user data directory of your browser. Leave `BROWSER_USER_DATA` empty if you want to use local user data.
      - Windows
        ```env
         BROWSER_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
         BROWSER_USER_DATA="C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data"
        ```
        > Note: Replace `YourUsername` with your actual Windows username for Windows systems.
      - Mac
        ```env
         BROWSER_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
         BROWSER_USER_DATA="/Users/YourUsername/Library/Application Support/Google/Chrome"
        ```
    - Close all Chrome windows
    - Open the WebUI in a non-Chrome browser, such as Firefox or Edge. This is important because the persistent browser context will use the Chrome data when running the agent.
    - Check the "Use Own Browser" option within the Browser Settings.

### Option 2: Docker Installation

#### Prerequisites
- Docker and Docker Compose installed
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (For Windows/macOS)
  - [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) (For Linux)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/browser-use/web-ui.git
cd web-ui
```

#### Step 2: Configure Environment
1. Create a copy of the example environment file:
- Windows (Command Prompt):
```bash
copy .env.example .env
```
- macOS/Linux/Windows (PowerShell):
```bash
cp .env.example .env
```
2. Open `.env` in your preferred text editor and add your API keys and other settings

#### Step 3: Docker Build and Run
```bash
docker compose up --build
```
For ARM64 systems (e.g., Apple Silicon Macs), please run follow command:
```bash
TARGETPLATFORM=linux/arm64 docker compose up --build
```

#### Step 4: Enjoy the web-ui and vnc
- Web-UI: Open `http://localhost:7788` in your browser
- VNC Viewer (for watching browser interactions): Open `http://localhost:6080/vnc.html`
  - Default VNC password: "youvncpassword"
  - Can be changed by setting `VNC_PASSWORD` in your `.env` file

## Changelog
- [x] **2025/01/26:** Thanks to @vvincent1234. Now browser-use-webui can combine with DeepSeek-r1 to engage in deep thinking!
- [x] **2025/01/10:** Thanks to @casistack. Now we have Docker Setup option and also Support keep browser open between tasks.[Video tutorial demo](https://github.com/browser-use/web-ui/issues/1#issuecomment-2582511750).
- [x] **2025/01/06:** Thanks to @richard-devbot. A New and Well-Designed WebUI is released. [Video tutorial demo](https://github.com/warmshao/browser-use-webui/issues/1#issuecomment-2573393113).

# 🔬 Enhanced AI Research Assistant

[![GitHub stars](https://img.shields.io/github/stars/savagelysubtle/ai-research-assistant?style=social)](https://github.com/savagelysubtle/ai-research-assistant/stargazers)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

**An advanced AI-powered research assistant with specialized legal research capabilities, multi-LLM support, and intelligent document generation.**

Built upon the foundation of browser-use, this enhanced research assistant has evolved into a comprehensive tool for complex research tasks, with particular strength in legal case analysis and document generation.

## ✨ Key Features

### 🧠 Multi-LLM Intelligence
- **Broad LLM Support**: OpenAI GPT-4, Anthropic Claude, Google AI, DeepSeek, Ollama, and more
- **Intelligent Routing**: Automatically select the best model for specific tasks
- **Enhanced Reasoning**: Deep thinking capabilities with DeepSeek-r1 integration

### ⚖️ Advanced Legal Research
- **WCAT Case Research**: Specialized Workers' Compensation Appeal Tribunal case analysis
- **Multi-Jurisdictional Search**: BC WCAT, CanLII, and other legal databases
- **Precedent Analysis**: AI-powered legal precedent identification and analysis
- **Strategy Generation**: Comprehensive legal strategy development

### 📄 Intelligent Document Generation
- **Legal Documents**: Auto-generate appeal notices, case summaries, and legal briefs
- **Research Reports**: Structured analysis reports with citations
- **Template System**: Extensible document templates for various use cases
- **Professional Formatting**: Court-ready document formatting

### 🗄️ Advanced Database Features
- **Full-Text Search**: Search across all case content and metadata
- **Similarity Analysis**: Find cases similar to your situation using advanced algorithms
- **Cross-Referencing**: Build relationships between related cases
- **Progress Tracking**: Track case milestones and deadlines

### 🌐 Web Research Capabilities
- **Intelligent Browsing**: AI-powered web navigation and data extraction
- **Multi-Source Integration**: Combine information from multiple sources
- **Content Analysis**: Advanced content parsing and summarization
- **Persistent Sessions**: Maintain browser state across research tasks

## 🚀 Getting Started

### Prerequisites
- **Python 3.13+** with uv package manager
- **Browser**: Chrome/Chromium for automated browsing
- **API Keys**: Optional but recommended for enhanced AI capabilities

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/savagelysubtle/ai-research-assistant.git
   cd ai-research-assistant
   ```

2. **Set Up Environment**
   ```bash
   # Using uv (recommended)
   uv venv --python 3.13

   # Activate virtual environment
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Windows CMD:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   uv sync

   # Install browsers for automated browsing
   playwright install chromium --with-deps
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

5. **Launch the Assistant**
   ```bash
   python webui.py --ip 127.0.0.1 --port 7788
   ```

   Open your browser and navigate to `http://127.0.0.1:7788`

### Docker Installation (Alternative)

```bash
# Clone and configure
git clone https://github.com/savagelysubtle/ai-research-assistant.git
cd ai-research-assistant
cp .env.example .env

# Build and run
docker compose up --build

# Access interfaces
# Web UI: http://localhost:7788
# VNC Viewer: http://localhost:6080/vnc.html
```

## 📖 Usage Guide

### 🔍 Legal Research Workflow

1. **Navigate to Legal Research Tab**: Click "⚖️ Legal Research" in the web interface
2. **Describe Your Case**: Provide detailed case description and circumstances
3. **Configure Search**: Set search terms, date ranges, and jurisdictions
4. **Enable AI Analysis**: Turn on LLM-powered legal analysis
5. **Run Research**: Start the comprehensive research process
6. **Review Results**: Analyze similar cases and AI-generated strategies
7. **Generate Documents**: Create legal documents based on findings

### 🌐 General Research

1. **Task Description**: Clearly describe your research objective
2. **Select Model**: Choose appropriate LLM for your task
3. **Configure Browser**: Set up browsing preferences and persistence
4. **Execute Research**: Let the AI navigate and gather information
5. **Review & Export**: Analyze results and export findings

### 🧠 Advanced AI Features

- **Deep Thinking**: Enable DeepSeek-r1 for complex reasoning tasks
- **Multi-Step Analysis**: Break down complex research into manageable steps
- **Source Verification**: Cross-reference information across multiple sources
- **Automated Documentation**: Generate comprehensive research reports

## 🏗️ Architecture

### Core Components

```
├── src/browser_use_web_ui/
│   ├── agent/
│   │   ├── legal_research/          # Specialized legal research agent
│   │   ├── deep_research/           # Advanced research capabilities
│   │   └── browser_use/             # Core browsing agent
│   ├── browser/                     # Browser management
│   ├── controller/                  # Task orchestration
│   ├── utils/                       # Utilities and LLM providers
│   └── webui/                       # Web interface components
├── legal_templates/                 # Legal document templates
├── plans/                          # Research planning templates
└── tmp/                            # Temporary files and cache
```

### Key Technologies

- **Browser Automation**: Playwright for reliable web interaction
- **AI Integration**: LangChain for LLM orchestration
- **Database**: SQLite for efficient case storage
- **Web Interface**: Gradio for user-friendly interaction
- **Document Generation**: Template-based legal document creation

## 🔧 Configuration

### Environment Variables

```bash
# Core Settings
WCAT_DATABASE_PATH="F:\WcatDB\cases.db"

# LLM API Keys
OPENAI_API_KEY="your-openai-key"
ANTHROPIC_API_KEY="your-anthropic-key"
GOOGLE_API_KEY="your-google-key"
DEEPSEEK_API_KEY="your-deepseek-key"

# Browser Settings (Optional)
BROWSER_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
BROWSER_USER_DATA="C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data"
```

### Advanced Configuration

```python
# Legal Research Agent
agent = LegalCaseResearchAgent(
    browser=browser,
    context=context,
    enable_llm_analysis=True,
    llm_provider="openai",
    enable_document_generation=True,
    enable_multi_jurisdictional=True
)

# Multi-LLM Setup
llm_config = {
    "primary": "openai",
    "reasoning": "deepseek",
    "research": "anthropic"
}
```

## 📊 Examples

### Legal Case Research

```python
# Case research example
case_summary = """
Warehouse employee with 3 years of repetitive heavy lifting (40-60 lbs).
Developed L4-L5 spinal stenosis with radiculopathy causing right leg
pain and numbness.
"""

results = await agent.run_legal_research(
    search_queries=["stenosis", "warehouse injury", "repetitive lifting"],
    user_case_summary=case_summary,
    date_range={"start_date": "2020-01-01", "end_date": "2024-12-31"},
    max_cases_per_query=20
)
```

### Document Generation

```python
# Generate legal documents
documents = await agent.generate_legal_documents(
    case_details={
        "appellant_name": "John Smith",
        "appellant_address": "123 Main St, Vancouver, BC",
        "summary": case_summary
    },
    precedent_cases=similar_cases
)
```

## 🛡️ Best Practices

### Legal Research
- Use specific, relevant search terms
- Set appropriate date ranges for recent precedents
- Review AI-generated content before use
- Maintain professional documentation standards

### Data Management
- Regular database backups
- Secure API key storage
- Monitor system performance
- Keep templates updated

## 🤝 Contributing

We welcome contributions! This project has evolved significantly from its browser-use origins and continues to improve.

### Development Setup

```bash
git clone https://github.com/savagelysubtle/ai-research-assistant.git
cd ai-research-assistant
uv sync
uv run ty check src/  # Type checking
```

### Code Standards
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include type hints for all functions
- Write unit tests for new features

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

**Key License Benefits:**
- ✅ Commercial use allowed
- ✅ Modification and distribution permitted
- ✅ Patent protection included
- ⚠️ **Attribution required** - Give credit to SavagelySubtle
- ⚠️ **Notice of changes required** - Document modifications

## 🙏 Acknowledgments

- **Original Foundation**: Built upon the browser-use framework
- **Legal Data Sources**: WCAT and CanLII for case access
- **AI Providers**: OpenAI, Anthropic, Google, DeepSeek for model access
- **Community**: Contributors and users who have shaped this project

## 🆘 Support

- **Documentation**: Comprehensive guides in `/docs`
- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Community discussions for questions and ideas
- **Examples**: Demo scripts in `/examples`

## 🚨 Legal Disclaimer

This tool assists with legal research and document preparation. **Always consult qualified legal professionals** for legal advice and review all generated content before use in legal proceedings.

---

**Created and maintained by [SavagelySubtle](https://github.com/savagelysubtle)**

*Transforming AI research capabilities one case at a time* 🔬⚖️
