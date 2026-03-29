# Security Policy

## Supported Release Status
This repository is currently published as a **Technical Preview / Stage Release**.

At this stage:
- security fixes are handled on a best-effort basis
- the `main` branch is the primary maintained branch
- older snapshots or temporary branches may not receive fixes

## Reporting a Vulnerability
Please **do not** open a public issue for a suspected security vulnerability.

Instead, report it privately by using one of these paths:
1. GitHub security reporting tools, if enabled for the repository
2. A private maintainer contact channel listed by the project owner

## What to Include
Please include:
- affected file or module
- steps to reproduce
- impact description
- proof of concept, if available
- environment details

## Scope Notes
Because this is a desktop technical preview, the highest-priority reports are:
- arbitrary code execution paths
- unsafe file handling
- path traversal
- credential or token exposure
- insecure plugin or external-process execution

## Disclosure Process
The maintainer will review the report, assess severity, and prepare a fix when confirmed.
Public disclosure should wait until a fix or mitigation is available.
