# Contributing to SafeAppealNavigator

First off, thank you for considering contributing to SafeAppealNavigator! It's people like you who help make this tool better for injured workers navigating the WorkSafe BC and WCAT system.

## 🤝 Code of Conduct

By participating in this project, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to simpleflowworks@gmail.com.

## 🎯 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Screenshots if applicable**
- **Environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Use case description**
- **Current limitations**
- **Proposed solution**
- **Alternative solutions considered**

### Pull Requests

1. **Fork the repo** and create your branch from `main`
2. **Follow our coding standards** (see below)
3. **Write meaningful commit messages**
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

## 🛠️ Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/safeappealnavigator.git
cd safeappealnavigator

# Create virtual environment
uv venv --python 3.13
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1

# Install all Python dependencies from pyproject.toml
uv sync

# Install frontend dependencies
cd frontend
npm install
cd ..

# Install development dependencies
uv sync --all-groups

# Set up pre-commit hooks (included in dev dependencies)
pre-commit install
```

## 📋 Coding Standards

### Python Code Style

- Follow **PEP 8** guidelines
- Use **type hints** for all functions
- Write **docstrings** for classes and functions
- Use **meaningful variable names**

```python
def process_wcat_case(case_id: str, user_summary: str) -> CaseAnalysis:
    """
    Process a WCAT case for similarity analysis.

    Args:
        case_id: The WCAT case identifier
        user_summary: User's case description

    Returns:
        CaseAnalysis object with similarity scores and recommendations
    """
    # Implementation here
```

### TypeScript/React Style

- Use **functional components** with hooks
- Implement **proper TypeScript types**
- Follow **ESLint** rules
- Use **meaningful component names**

```typescript
interface CaseTimelineProps {
  caseId: string;
  events: TimelineEvent[];
  onEventClick: (event: TimelineEvent) => void;
}

export const CaseTimeline: React.FC<CaseTimelineProps> = ({ caseId, events, onEventClick }) => {
  // Component implementation
};
```

### Commit Messages

Follow the conventional commits format:

```
feat: add WCAT case similarity search
fix: correct date parsing in case timeline
docs: update API documentation for legal research agent
test: add tests for document categorization
```

## 🧪 Testing

### Python Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ai_research_assistant

# Run specific test file
pytest tests/test_legal_research.py
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

## 📚 Documentation

- Update **README.md** for user-facing changes
- Update **API docs** for new endpoints
- Add **inline comments** for complex logic
- Update **type definitions** when changing interfaces

## 🔄 Pull Request Process

1. **Update CHANGELOG.md** with your changes
2. **Ensure all tests pass**
3. **Update documentation**
4. **Request review** from maintainers
5. **Address feedback** promptly

### PR Title Format

```
[Component] Brief description

Examples:
[Frontend] Add case document upload progress indicator
[Legal Agent] Implement WCAT policy search functionality
[Docs] Update installation guide for macOS
```

## 🏗️ Project Structure

Key areas for contribution:

```
src/ai_research_assistant/
├── agents/              # AI agent implementations
├── ag_ui_backend/       # FastAPI backend
├── a2a_services/        # Agent communication
├── browser/             # Web automation
├── core/                # Core utilities
└── mcp_intergration/    # Tool integrations

frontend/
├── components/          # React components
├── hooks/              # Custom React hooks
├── services/           # API services
└── contexts/           # React contexts
```

## 🎯 Priority Areas

We especially welcome contributions in:

1. **Legal Database Integration** - Adding new legal data sources
2. **Document Analysis** - Improving AI document understanding
3. **UI/UX Improvements** - Making the tool more accessible
4. **Test Coverage** - Adding more comprehensive tests
5. **Documentation** - Improving guides and examples

## 📮 Getting Help

- **Discord**: [Join our community](https://discord.gg/safeappealnavigator) (if applicable)
- **GitHub Discussions**: Ask questions and share ideas
- **Email**: simpleflowworks@gmail.com for sensitive matters

## 🙏 Recognition

Contributors will be:
- Listed in our [Contributors](#) section
- Mentioned in release notes
- Given credit in relevant documentation

Thank you for helping make SafeAppealNavigator better for everyone! 💙