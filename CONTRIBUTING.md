# Contributing to Vibemap

Thank you for your interest in contributing to Vibemap! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, constructive, and collaborative. We're building infrastructure for the Agentic Era together.

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or request features
- Provide clear reproduction steps for bugs
- Include environment details (OS, Python version, etc.)

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/vibemap.git
cd vibemap

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

### Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

```bash
# Format code
black .

# Run linter
ruff check .

# Type check
mypy .
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test
pytest tests/test_vibe_service.py
```

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add new agent persona (Foodie)
fix: Correct weather modifier calculation
docs: Update API reference for /v1/global-pulse
refactor: Split sentiment service into modules
test: Add tests for predictive clusters
```

## Architecture Guidelines

### Adding New Data Sources

1. Create a service in `services/`
2. Implement async methods with proper error handling
3. Add fallback to simulated data if API unavailable
4. Update documentation

Example:
```python
# services/new_source_service.py
class NewSourceService:
    async def fetch_data(self, location: GeoPoint) -> Dict:
        try:
            # Real API call
            return await self._api_call(location)
        except Exception:
            # Graceful fallback
            return self._simulate_data(location)
```

### Adding New Endpoints

1. Define schema in `schemas/schemas.py`
2. Implement handler in `main.py`
3. Add service logic in `services/`
4. Update documentation

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Questions?

- Open a GitHub Discussion for questions
- Tag `@ramezyo` for urgent issues

Thank you for contributing to the Semantic Nervous System! 🌐