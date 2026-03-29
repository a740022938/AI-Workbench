# Contributing to AI Workbench

Thank you for your interest in contributing to AI Workbench! This document provides guidelines and instructions for contributing to the project.

## Project Status & Philosophy

### Current Release: v1.0.0-stage (Technical Preview)
- **Stage Release**: This is a stage public development release, not a final production version
- **Architecture First**: Core architecture and business logic are complete and stable
- **Developer Focused**: Intended for developers, collaborators, and architecture reviewers
- **Feedback Driven**: This release is specifically for gathering community feedback
- **Optimization Ongoing**: Installation and runtime experience are being refined

### Development Philosophy
1. **MainWindow Zero-Bloat**: Keep MainWindow as a pure coordination layer with minimal business logic
2. **Layered Architecture**: Data layer → Business layer → Interface layer separation
3. **Extension Points**: Design for extensibility via plugins, trainers, inspectors, exporters
4. **Safety-First Culture**: Auto-backup before modifications, comprehensive testing

## Getting Started for Contributors

### Prerequisites
- **Python**: 3.8 or higher
- **Git**: Basic familiarity with version control
- **Development Environment**: Your preferred IDE or editor
- **Basic Knowledge**: Python, tkinter (for UI contributions), PyTorch/YOLO (for ML contributions)

### Setup Development Environment
1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/AI-Workbench.git
   cd AI-Workbench
   ```
3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Verify the project runs:
   ```bash
   python main.py
   ```

## Code Organization & Architecture

### Directory Structure
```
AI_Workbench_MASTER/
├── core/                    # Core business logic (all data and service layers)
│   ├── ui_style_manager.py     # UI theme manager (3 styles + callback system)
│   ├── language_manager.py     # Bilingual manager (200+ text resources)
│   ├── action_system.py        # AI collaboration action system (32 actions)
│   ├── training_center_manager.py  # Training center core (14-phase features)
│   ├── data_health_manager.py  # Quality inspection manager
│   ├── dataset_exporter.py     # Dataset export manager
│   └── closed_loop_manager.py  # Closed-loop correction manager
├── ui/                      # User interface layer (all windows and panels)
│   ├── main_window.py          # Main application window (coordination layer only)
│   ├── canvas_panel.py         # Annotation canvas
│   ├── training_center_window.py  # Training center UI
│   ├── data_health_window.py   # Quality inspection UI
│   ├── dataset_export_window.py # Dataset export UI
│   ├── closed_loop_window.py   # Closed-loop correction UI
│   └── settings_window.py      # Settings window (theme/language切换)
├── config/                  # Configuration files
├── tests/                  # Test scripts and examples
└── utils/                  # Utility functions
```

### Key Architectural Principles
1. **Business Logic in Core**: All complex business logic belongs in `core/`, not in UI files
2. **UI Layer is Thin**: UI files should focus on presentation and event handling
3. **Extension via Adapters**: New functionality (trainers, inspectors) should use adapter patterns
4. **State Management via Context**: Use `WorkbenchContext` for shared application state

## Contribution Areas

### High-Priority Areas (Stage Release Focus)
1. **Dependency Management**: Improving `requirements.txt` and installation experience
2. **GUI Launch Reliability**: Fixing PIL/Pillow issues and startup problems
3. **UI Polish**: Theme switching details, language refresh consistency
4. **Documentation**: Installation guides, troubleshooting resources, API documentation

### Feature Development Areas
1. **New Trainer Adapters**: Segmentation, pose estimation, other model types
2. **Enhanced Export Formats**: COCO, Pascal VOC, other dataset formats
3. **Plugin System**: Extending the plugin API and marketplace foundation
4. **Performance Optimization**: Large dataset handling, memory efficiency

### Bug Fixes & Improvements
1. **Installation Issues**: PIL/Pillow dependencies, environment setup
2. **Runtime Errors**: Module imports, configuration loading, path handling
3. **UI Bugs**: Theme switching, language updates, layout issues
4. **Documentation Updates**: Clarifications, examples, troubleshooting guides

## Development Workflow

### 1. Before You Start
- Check existing issues to avoid duplication
- Discuss major changes via GitHub Issues before implementation
- For new features, consider if they fit the project architecture

### 2. Making Changes
1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes following coding standards
3. Add or update tests as needed
4. Update documentation if required

### 3. Coding Standards
- **Python Style**: Follow PEP 8, use `black` for formatting
- **Documentation**: Include docstrings for public functions and classes
- **Imports**: Group imports: standard library, third-party, local
- **Naming**: Use descriptive names, follow existing project conventions
- **Error Handling**: Use appropriate exception handling with helpful messages

### 4. Testing
- Run existing tests: `pytest tests/`
- Add tests for new functionality
- Test UI changes manually (automated UI testing is limited)
- Verify backward compatibility when possible

### 5. Committing
- Write clear, descriptive commit messages
- Reference issue numbers when applicable: `fixes #123`
- Keep commits focused and logically grouped

### 6. Submitting a Pull Request
1. Push your branch to GitHub
2. Create a Pull Request against the `main` branch
3. Fill out the PR template (if available)
4. Describe your changes and any testing performed
5. Link related issues
6. Request review from maintainers

## Review Process

### What Reviewers Look For
1. **Architecture Fit**: Does the change align with project architecture principles?
2. **Code Quality**: Is the code clean, well-documented, and maintainable?
3. **Testing**: Are there adequate tests for the changes?
4. **Documentation**: Is documentation updated as needed?
5. **Backward Compatibility**: Does the change break existing functionality?

### Response Time
- Initial review typically within 3-7 days
- Feedback will be provided for required changes
- Once approved, maintainers will merge your PR

## Community Guidelines

### Communication
- **Be Respectful**: Treat all community members with respect
- **Be Constructive**: Provide helpful, specific feedback
- **Be Patient**: Remember this is a volunteer-driven project

### Issue Reporting
When reporting issues, please include:
1. Clear description of the problem
2. Steps to reproduce
3. Expected vs. actual behavior
4. Environment details (OS, Python version, dependency versions)
5. Relevant logs or error messages

### Feature Requests
When requesting features, please:
1. Explain the use case and benefit
2. Consider if it aligns with project goals
3. Suggest implementation approach if possible
4. Be open to discussion and alternative solutions

## Getting Help

- **GitHub Issues**: For bugs, feature requests, and questions
- **Documentation**: Check README.md and RELEASE_NOTES.md first
- **Code Review**: PR reviews include feedback and guidance
- **Community**: Planned Discord community for real-time discussion

## Acknowledgments

Thank you for contributing to AI Workbench! Your contributions help make AI vision development more accessible, efficient, and collaborative.

---

*This document is part of the v1.0.0-stage Technical Preview and will evolve based on community feedback.*