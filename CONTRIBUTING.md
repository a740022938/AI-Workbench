# Contributing to AI Vision Data & Training Workbench

Thanks for helping improve the project.

## Before you start

This repository is currently a **Technical Preview / Stage Public Development Release**. Please treat contributions as architecture-aware improvements rather than cosmetic drive-by edits.

Recommended first steps:
1. Read `README.md`
2. Read `RELEASE_NOTES.md`
3. Open an issue before making large architectural changes
4. Keep changes scoped and reviewable

## Development principles

- Prefer **small, focused pull requests**
- Do not hard-code machine-specific paths, credentials, or local environment assumptions
- Preserve extension points and avoid making modules more tightly coupled
- Keep runtime behavior stable unless the PR explicitly targets behavior changes
- Prefer reusable abstractions over one-off fixes when touching shared infrastructure

## Environment setup

1. Create a Python 3.8+ virtual environment
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the app:
   ```bash
   python main.py
   ```

If you need GPU training, install the PyTorch build that matches your CUDA environment before running training workflows.

## Pull request checklist

Before opening a PR, please verify:

- [ ] The app still starts successfully
- [ ] You did not commit private paths, generated outputs, model weights, or backup artifacts
- [ ] New files follow the existing project structure
- [ ] User-facing text is consistent with the language/theme system where applicable
- [ ] Documentation is updated when behavior changes

## Preferred contribution areas

At the current stage, the most valuable contributions are:

- Dependency chain hardening
- Startup reliability and better error reporting
- Theme and language consistency
- Trainer adapter expansion
- Quality inspection and dataset workflow improvements
- Documentation and onboarding clarity

## What to avoid in PRs

Please avoid bundling unrelated work into a single PR, especially combinations like:

- UI redesign + training backend changes
- Refactor + feature addition + repo cleanup in one PR
- Large renames without a clear migration rationale

## Reporting bugs

When filing an issue, include:

- Operating system
- Python version
- Installation steps attempted
- Full error message or screenshot
- Whether the problem affects launch, annotation, training, inspection, or export

## Code style

Follow the existing code style in the area you are modifying. Prioritize readability, maintainability, and low-risk integration with the current architecture.

## Review note

Maintainers may ask for scope reduction if a PR is too broad for the current technical preview stage.
