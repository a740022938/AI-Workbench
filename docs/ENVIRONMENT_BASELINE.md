# Environment Baseline

This document describes the most reasonable baseline expectations for running the current technical preview.

## Recommended Baseline

For the smoothest experience, the recommended baseline is:
- Windows 11
- Python 3.10 or 3.11
- virtual environment enabled
- local write permission to the project directory
- optional NVIDIA GPU for training workflows

## Minimum Practical Expectations

Users should be prepared to:
- install Python packages manually
- create or activate a virtual environment
- resolve local dependency conflicts if needed
- review logs and terminal output during setup

## Platform Guidance

### Windows
This is the primary validation target for the current public stage.
It is the best-supported environment for onboarding and troubleshooting.

### macOS
May work for parts of the project, but small rendering or environment differences should still be expected.

### Linux
Should be treated as experimental unless tested in a specific environment.
Additional package setup may be required.

## Python Guidance

Recommended:
- Python 3.10
- Python 3.11

Use caution with:
- older Python versions
- very new Python versions that may expose dependency breakage

## GPU Guidance

GPU acceleration is helpful but not required.
At this stage, users should treat CUDA setup as an advanced path rather than a default expectation.

## Configuration Guidance

Before launch, verify:
- `config.example.json` exists
- `config.json` has been created when needed
- the project is launched from the repository root

## Best-Practice Setup Pattern

A good default setup pattern is:
1. clone repository
2. create virtual environment
3. install dependencies
4. create configuration file
5. launch from project root
6. review logs if startup fails

## Why This Document Exists

The goal is to reduce avoidable confusion by making the current technical preview baseline explicit.
This is not yet a zero-friction installer experience.
