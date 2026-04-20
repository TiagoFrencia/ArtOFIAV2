# GitHub Actions Workflows

This directory contains automated CI/CD workflows for ArtOfIAV2.

## Workflows

### 1. Lint & Type Check (`lint.yml`)
**Runs on**: Push and PRs to main/develop

Validates code quality and type safety:
- Black formatting
- Pylint score (minimum 8.0)
- MyPy strict type checking
- Import sorting (isort)

### 2. Tests (`test.yml`)
**Runs on**: Push and PRs to main/develop

Executes test suite with dependencies:
- PostgreSQL 15 (vector DB)
- Neo4j 5.23 (knowledge graph)
- Coverage reporting to Codecov

### 3. Docker Build (`docker.yml`)
**Runs on**: Push, PRs, and version tags

Builds and publishes Docker images:
- Multi-stage build (optimized size)
- Automatic tagging (branch, version, SHA)
- Caching for faster builds

### 4. Security Checks (`security.yml`)
**Runs on**: Push, PRs, and weekly schedule

Scans for security issues:
- Dependency vulnerabilities (Safety)
- Code security issues (Bandit)
- Hardcoded secrets (TruffleHog)

## Quick Reference

```bash
# Check local lint before pushing
black src/ tests/
pylint src/
mypy src/ --strict

# Run tests locally
pytest tests/ -v

# Build Docker image locally
docker build -t artofiah:local .
```

## Status

View workflow runs: Repository → Actions

## Documentation

See `../P1.1_CICD_COMPLETE.md` for full documentation.
