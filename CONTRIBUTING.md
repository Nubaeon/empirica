# Contributing to Empirica

Thank you for your interest in contributing to Empirica! This document outlines our development workflow and guidelines.

## Development Workflow

We use **Git Flow** for version management with the following branch structure:

```
main (stable, production-ready)
  ├── develop (integration branch)
  │   ├── feature/your-feature-name
  │   ├── bugfix/issue-description
  │   └── experimental/research-idea
  └── hotfix/critical-bug (emergency fixes from main)
```

## Branch Strategy

### Main Branch
- **Purpose**: Production-ready, stable code that users install
- **Protection**: Requires PR review + passing tests
- **Direct commits**: Not allowed
- **Install from**: `pip install git+https://github.com/Nubaeon/empirica.git@main`

### Develop Branch
- **Purpose**: Integration and testing of new features
- **Protection**: Requires passing tests
- **Direct commits**: Allowed for maintainers
- **Install from**: `pip install git+https://github.com/Nubaeon/empirica.git@develop`

See full branching workflow and contribution guidelines in the file.
