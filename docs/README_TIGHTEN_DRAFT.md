# AI Vision Data & Training Workbench

A desktop workbench for AI vision workflows, covering annotation, training, inspection, dataset preparation, closed-loop correction, and AI-assisted collaboration.

This repository is currently published as a **Technical Preview / Stage Public Development Release**. It is intended primarily for developers, collaborators, and architecture reviewers rather than end users expecting a polished plug-and-play product.

## Project Status

**Current version:** `v1.0.0-stage`  
**Release type:** Technical Preview / Stage Public Development Release

### Best fit for
- Developers
- Contributors
- Architecture reviewers
- AI/ML users comfortable with Python environment setup

### Current focus
- Installation reliability
- Dependency clarity
- Startup consistency
- Public-facing documentation accuracy
- Cross-platform validation

### Important note
This is not yet a polished end-user release. The core architecture and major workflow directions are in place, but installation experience, runtime consistency, and public onboarding are still being refined.

## Core Capabilities

- **Annotation Workbench**: image labeling, box editing, and category management
- **Training Center**: experiment configuration, execution, and result monitoring
- **Inspection Center**: annotation quality checks and repair workflows
- **Dataset Center**: dataset splitting, validation, and export preparation
- **Closed-Loop Center**: bad-case collection and correction workflow support
- **AI Collaboration Layer**: structured actions and OpenClaw-oriented integration foundation

## Quick Start

```bash
git clone https://github.com/a740022938/AI-Workbench.git
cd AI-Workbench
pip install -r requirements.txt
python main.py
```

### Recommended entry point
Use `python main.py` as the primary launch method.

### Alternative entry point
`python run.py` is available as a secondary launcher, but `main.py` should be treated as the main documented entry.

## Documentation

- [Windows 11 Installation Guide](WIN11_INSTALL_GUIDE.md)
- [Quick Start for Windows 11](QUICK_START_WIN11.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Technical Preview Scope](TECHNICAL_PREVIEW_SCOPE.md)
- [Known Issues](KNOWN_ISSUES.md)
- [Environment Baseline](ENVIRONMENT_BASELINE.md)
- [Support](../SUPPORT.md)

## Environment Baseline

Recommended:
- Windows 11
- Python 3.10 or 3.11
- Virtual environment enabled

Notes:
- GPU acceleration is optional
- Windows is the current primary validation target
- macOS and Linux may work, but should still be treated with caution at this stage

## Current Boundaries

At the current technical preview stage, users should expect:
- manual environment setup
- occasional dependency troubleshooting
- startup behavior that may vary by machine
- documentation that is still being tightened alongside the codebase

## Screenshots

> Screenshots of the main window, annotation workflow, training center, and settings/theme system will be added here.

## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md).

## License
MIT. See [LICENSE](../LICENSE).
