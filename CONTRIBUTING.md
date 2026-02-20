# Contributing to lifecycle-allocation

Thank you for your interest in contributing! This document covers the development workflow.

## Development Setup

```bash
git clone https://github.com/engineerinvestor/lifecycle-allocation.git
cd lifecycle-allocation
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Code Style

This project uses:

- **ruff** for linting
- **black** for formatting (line length 99)
- **mypy** for type checking

Run all checks:

```bash
ruff check .
black --check .
mypy lifecycle_allocation/
```

Format code before committing:

```bash
black .
ruff check . --fix
```

## Testing

```bash
pytest tests/ -v
pytest tests/ -v --cov=lifecycle_allocation   # with coverage
```

All new code should include tests. Aim for high coverage of edge cases, especially around the mathematical functions.

## Git Configuration

This project uses a shared identity for commits:

```bash
git -c user.name="Engineer Investor" -c user.email="egr.investor@gmail.com" commit -m "your message"
```

## Pull Request Process

1. **Fork** the repository and create a feature branch
2. **Write** your changes with tests
3. **Run** the full check suite: `ruff check . && black --check . && mypy lifecycle_allocation/ && pytest tests/ -v`
4. **Submit** a pull request against `main`

Please keep PRs focused -- one feature or fix per PR. Include a clear description of what changed and why.

## Reporting Issues

Use [GitHub Issues](https://github.com/engineerinvestor/lifecycle-allocation/issues) to report bugs or request features. Include:

- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
