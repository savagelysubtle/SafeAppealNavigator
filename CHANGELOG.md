# Changelog

All notable changes to SafeAppealNavigator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete rebranding from AI Research Assistant to SafeAppealNavigator
- PayPal donation support link
- Modern React + FastAPI architecture
- Multi-agent system for legal research
- WCAT case similarity search
- Document organization and categorization
- Case timeline visualization
- Appeal letter generation
- Medical summary compilation
- WorkSafe BC policy analysis

### Changed
- Replaced Gradio interface with React frontend
- Updated all documentation to focus on WorkSafe/WCAT use cases
- Improved file organization capabilities
- Enhanced AI-powered case analysis

### Security
- All API keys stored in environment variables
- Local data storage for privacy
- Encrypted API communications

## [0.2.0] - 2025-01-28

### Added
- CONTRIBUTING.md guide for developers
- CODE_OF_CONDUCT.md for community standards
- Comprehensive React hooks documentation
- API documentation structure
- Development setup guide

### Changed
- Restructured README.md as standalone application
- Moved technical acknowledgments to bottom of README
- Focused documentation on injured workers and advocates

### Removed
- Browser-use foundation language
- WebUI/Gradio references
- Docker installation option from main README

## [0.1.0] - 2025-01-15

### Added
- Initial release of SafeAppealNavigator
- Basic WCAT case search functionality
- Document upload and management
- AI chat interface
- Legal research capabilities
- Multi-LLM support (OpenAI, Anthropic, Google)
- A2A agent communication protocol
- AG-UI WebSocket interface

### Known Issues
- Frontend and backend integration in progress
- Some agent communication features still being refined

[Unreleased]: https://github.com/savagelysubtle/safeappealnavigator/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/savagelysubtle/safeappealnavigator/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/savagelysubtle/safeappealnavigator/releases/tag/v0.1.0