# Known Issues

This document tracks known limitations and common friction points for the current technical preview.

## 1. Environment Setup Still Requires Manual Attention

At the current stage, users may still need to:
- install dependencies manually
- resolve local Python environment conflicts
- adjust GPU / CUDA setup on their own machine

## 2. Startup Reliability Can Differ by Machine

Different machines may behave differently depending on:
- Python version
- tkinter availability
- Pillow / OpenCV installation state
- local path and permission setup

## 3. Documentation May Still Lag Behind the Latest Code Snapshot

Some public-facing documentation may require ongoing tightening as the project evolves.
The project is in an active refinement stage, so release-facing wording should be read together with the technical preview scope note.

## 4. Cross-Platform Experience Is Not Yet Fully Hardened

Windows is the main validation target at this stage.
macOS and Linux compatibility may improve over time, but edge cases should still be expected.

## 5. Some Workflows Are More Mature Than Others

The architecture is broad, but different centers may currently have different levels of polish in:
- onboarding experience
- validation depth
- UI refinement
- troubleshooting coverage

## 6. Runtime Integration Paths Still Need More Real-World Feedback

The most valuable issues to report are:
- install failures
- launch failures
- broken workflow links
- mismatches between docs and actual behavior
- platform-specific UI/runtime problems

## Reporting Guidance

Before opening an issue:
1. check the troubleshooting guide
2. check the technical preview scope note
3. include environment details and reproduction steps
