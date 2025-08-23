# ⚖️ SafeAppealNavigator

*Support this project: [paypal.me/safeappealnavigator](https://paypal.me/safeappealnavigator)*

[![GitHub stars](https://img.shields.io/github/stars/savagelysubtle/safeappealnavigator?style=social)](https://github.com/savagelysubtle/safeappealnavigator/stargazers)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

**Your intelligent companion for navigating WorkSafe BC and WCAT appeals. Organize case files, research legal precedents, and build compelling appeals with AI-powered document management and legal research.**

SafeAppealNavigator helps injured workers, legal advocates, and their representatives tackle the complex world of Workers' Compensation appeals. Whether you're dealing with a denied claim, preparing for a WCAT hearing, or organizing years of medical documentation, this tool transforms overwhelming legal processes into manageable, organized workflows.

## 🎯 Who This Helps

- **Injured Workers**: Organize your case, understand your rights, and build stronger appeals
- **Legal Advocates**: Streamline case research and document preparation for clients
- **Family Members**: Help loved ones navigate complex WorkSafe and WCAT processes
- **Support Organizations**: Assist multiple clients with consistent, professional case management

## ✨ Key Features

### 📁 Smart Case Organization
- **Document Management**: Automatically organize medical reports, correspondence, and legal documents
- **Timeline Builder**: Create visual timelines of your case progression and key milestones
- **Deadline Tracking**: Never miss critical deadlines or hearing dates
- **Evidence Categorization**: Smart tagging and organization of supporting documentation

### ⚖️ WCAT & WorkSafe Research
- **Precedent Discovery**: Find WCAT decisions with circumstances similar to your case
- **Policy Analysis**: Search and understand relevant WorkSafe BC policies and procedures
- **Case Strength Assessment**: AI analysis of your position based on similar successful cases
- **Gap Identification**: Discover what evidence or documentation might strengthen your case

### 📝 Professional Document Creation
- **Appeal Letters**: Generate well-structured appeal submissions with proper legal formatting
- **Medical Summaries**: Transform complex medical records into clear, compelling narratives
- **Case Briefs**: Create comprehensive overviews for legal representatives or hearings
- **Evidence Packages**: Organize supporting documentation for maximum impact

### 🤖 AI-Powered Insights
- **Plain Language Explanations**: Complex legal concepts explained in understandable terms
- **Strategic Recommendations**: Next steps and strategies based on case analysis
- **Document Analysis**: AI review of your documents to identify strengths and weaknesses
- **Research Assistance**: Intelligent search across legal databases and precedent cases

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.11 or higher**
- **Node.js 18+** with npm
- **Windows, macOS, or Linux**

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/savagelysubtle/safeappealnavigator.git
   cd safeappealnavigator
   ```

2. **Set Up Python Environment**
   We recommend using [uv](https://docs.astral.sh/uv/) for managing dependencies:
   ```bash
   uv venv --python 3.13
   ```

   Activate the virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```cmd
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

3. **Install Dependencies**
   ```bash
   # Install Python dependencies
   uv sync

   # Install frontend dependencies
   cd frontend
   npm install
   cd ..

   # Install browser automation capabilities
   playwright install chromium --with-deps
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   ```

   Open `.env` in your text editor and add your API keys (optional but recommended for enhanced AI features):
   ```env
   OPENAI_API_KEY="your-openai-key"
   ANTHROPIC_API_KEY="your-anthropic-key"
   GOOGLE_API_KEY="your-google-key"
   ```

5. **Launch SafeAppealNavigator**
   ```bash
   python run_app.py
   ```

   The application will start both the backend and frontend. Open your browser and navigate to `http://localhost:5173`

6. **Optional: Configure Additional Tools**

   SafeAppealNavigator supports extensible tool integration through MCP (Model Context Protocol). You can configure additional research databases, document processing services, or legal research tools by editing `data/mcp.json`. The system comes pre-configured with essential file management and vector database tools for case organization and similarity search.

## 📖 How to Use

### 🏥 Starting Your Case

1. **Create New Case**: Set up a new case file with basic information about your injury and claim
2. **Upload Documents**: Import medical reports, WorkSafe correspondence, and any legal documents
3. **Build Timeline**: Add key dates like injury date, claim submission, decisions, and deadlines
4. **Describe Situation**: Provide details about your injury, treatment, and WorkSafe interactions

### 🔍 Research & Analysis

1. **Find Similar Cases**: Search WCAT decisions for cases with circumstances like yours
2. **Analyze Outcomes**: Understand how similar cases were decided and what factors were important
3. **Review Policies**: Research relevant WorkSafe BC policies that apply to your situation
4. **Identify Precedents**: Discover favorable legal arguments and supporting case law

### 📋 Building Your Appeal

1. **Assess Your Position**: Get AI analysis of your case strength based on precedents
2. **Identify Gaps**: Discover what additional evidence or documentation you might need
3. **Draft Documents**: Generate professional appeal letters and supporting documents
4. **Organize Evidence**: Structure your supporting documentation for maximum impact

### 📅 Case Management

1. **Track Progress**: Monitor deadlines, hearing dates, and case milestones
2. **Manage Communications**: Organize all correspondence with WorkSafe, medical providers, and legal representatives
3. **Prepare for Hearings**: Get talking points and evidence organization for WCAT hearings
4. **Document Everything**: Maintain detailed records of all case-related activities

## 📊 Real-World Success Stories

### 🏗️ Construction Worker - Denied Surgery Coverage
**Challenge**: Back injury from lifting, surgery coverage denied
**Solution**: Found 12 similar WCAT cases where surgery was approved, generated appeal emphasizing medical necessity
**Outcome**: Surgery coverage approved on appeal

### 🏥 Healthcare Worker - "Not Work-Related" Claim
**Challenge**: Repetitive strain injury denied as non-work related
**Solution**: Organized evidence linking injury to work duties, found precedents for similar injuries
**Outcome**: Claim accepted after comprehensive appeal submission

### 🚛 Driver - Mental Health Benefits
**Challenge**: PTSD after workplace accident, mental health benefits denied
**Solution**: Research showed precedents for psychological injury acceptance, organized witness statements
**Outcome**: Mental health claim recognized and benefits approved

## 🛡️ Privacy & Security

- **Local Data Storage**: All your case information stays on your computer
- **Secure API Connections**: All AI interactions use encrypted connections
- **No Data Sharing**: Your personal and legal information is never shared or stored externally
- **Open Source**: Full transparency - review the code yourself

## 🤝 Contributing

SafeAppealNavigator is open source and welcomes contributions from the community. Whether you're a developer, legal professional, or someone who has navigated the WorkSafe system, your insights can help others.

### Development Setup

```bash
git clone https://github.com/savagelysubtle/safeappealnavigator.git
cd safeappealnavigator
uv sync
```

### Code Standards
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include type hints for all functions
- Write tests for new features

## 📄 License

Licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

- ✅ Commercial use allowed
- ✅ Modification and distribution permitted
- ✅ Patent protection included
- ⚠️ Attribution required
- ⚠️ Notice of changes required

## 🆘 Support & Resources

- **Documentation**: Comprehensive guides in `/docs`
- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Community support and questions
- **Legal Disclaimer**: This tool assists with legal research and document preparation. Always consult qualified legal professionals for legal advice.

---

**Created and maintained by [SavagelySubtle](https://github.com/savagelysubtle)**

*Empowering injured workers to navigate the legal system with confidence* ⚖️

---

## 🔧 Technical Architecture & Acknowledgments

SafeAppealNavigator is built using modern web technologies and incorporates several open-source libraries to provide its functionality:

### Core Technologies
- **Frontend**: React + TypeScript with Tailwind CSS for modern, responsive UI
- **Backend**: FastAPI with WebSocket support for real-time communication
- **Database**: SQLite with vector search capabilities for case storage and similarity analysis
- **AI Integration**: Support for multiple LLM providers (OpenAI, Anthropic, Google, DeepSeek, Ollama)

### Key Libraries & Components

**Browser Automation**: Utilizes browser automation agents for intelligent web navigation and legal database research. These components enable automated interaction with WCAT, CanLII, and other legal research platforms.

**Model Context Protocol (MCP) Integration**: Implements standardized MCP client patterns for extensible tool integration. This allows SafeAppealNavigator to seamlessly connect with external services, databases, and specialized legal research tools through a unified protocol, enhancing document analysis and case research capabilities.

**Agent Communication (A2A)**: Implements an Agent-to-Agent communication protocol that allows specialized AI agents to coordinate complex legal research tasks, document analysis, and case preparation workflows.

**AG-UI Protocol**: Custom WebSocket-based protocol for real-time communication between the React frontend and Python backend, enabling seamless user interaction with the multi-agent system.

**Multi-Agent Architecture**: Employs specialized agents including:
- Document Processing Coordinator (with file system and database tools)
- Legal Research Coordinator (with web research and precedent analysis tools)
- Database Query Coordinator (with vector search and data analysis tools)
- Chief Legal Orchestrator (coordinating all specialized agents)

### Open Source Foundations

SafeAppealNavigator leverages and builds upon excellent open-source projects:
- **Playwright**: For reliable browser automation
- **LangChain**: For LLM orchestration and prompt management
- **AutoGen**: For multi-agent conversation patterns
- **FastAPI**: For high-performance API development
- **React**: For modern user interface development

This application represents a specialized legal research tool that combines these technologies to serve the specific needs of WorkSafe BC and WCAT case management.
