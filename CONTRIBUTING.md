# Contributing to Tapo Exporter

Thank you for your interest in contributing to Tapo Exporter! This document provides guidelines and steps for contributing to this project.

## Development Environment Setup

1. Fork and clone the repository
2. Choose your development environment:

   ### Option 1: Local Development

   Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

   Install development dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

   ### Option 2: Docker Development

   Build and start the development environment:

   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. Copy `.env.example` to `.env` and configure your environment variables
4. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

## Code Style

We use several tools to maintain code quality:

- Black for code formatting
- isort for import sorting
- mypy for type checking
- flake8 for linting

Run these tools before committing:

```bash
black .
isort .
mypy .
flake8
```

## Testing

1. Run tests locally:

   ```bash
   pytest
   ```

2. Run tests with coverage:

   ```bash
   pytest --cov=tapo_exporter
   ```

3. Run tests in Docker:

   ```bash
   docker-compose -f docker-compose.dev.yml run tapo-exporter pytest
   ```

4. Run tests with coverage in Docker:

   ```bash
   docker-compose -f docker-compose.dev.yml run tapo-exporter pytest --cov=tapo_exporter
   ```

## Pull Request Process

1. Create a new branch for your feature/fix
2. Make your changes
3. Run all tests and checks
4. Update documentation if needed
5. Submit a pull request with a clear description of changes

## Documentation

- Update README.md for user-facing changes
- Add docstrings for new functions/classes
- Update CHANGELOG.md for significant changes

## Release Process

1. Update version in pyproject.toml
2. Update CHANGELOG.md
3. Create a new release tag
4. Build and publish to PyPI

## Questions?

Feel free to open an issue for any questions or concerns.
