# Contributing to PyResolvers

Thank you for considering contributing to PyResolvers! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment
- Respect differing viewpoints and experiences

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pyresolvers.git
   cd pyresolvers
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/PigeonSec/pyresolvers.git
   ```

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Git
- Virtual environment tool (venv)

### Installation

1. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # venv\Scripts\activate   # On Windows
   ```

2. **Install in development mode**:
   ```bash
   pip install -e .
   pip install pytest flake8
   ```

3. **Verify installation**:
   ```bash
   pyresolvers -t 1.1.1.1
   pytest tests/ -v
   ```

## How to Contribute

### Types of Contributions

- **Bug fixes**: Fix issues in the existing code
- **New features**: Add new functionality
- **Documentation**: Improve README, docstrings, or examples
- **Tests**: Add or improve test coverage
- **Performance**: Optimize existing code
- **Refactoring**: Improve code quality without changing behavior

### Workflow

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Make your changes** following the [coding standards](#coding-standards)

3. **Test your changes**:
   ```bash
   pytest tests/ -v
   flake8 pyresolvers --count --select=E9,F63,F7,F82
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add concise description of your changes"
   ```

5. **Keep your fork updated**:
   ```bash
   git fetch upstream
   git rebase upstream/master
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 127 characters
- Use meaningful variable and function names

### Code Structure

- **Imports**: Standard library → Third-party → Local imports
- **Docstrings**: Use for all public classes, methods, and functions
- **Type hints**: Preferred for function signatures
- **Comments**: Explain "why", not "what"

### Example

```python
from typing import List, Optional
import asyncio


async def validate_servers(
    servers: List[str],
    timeout: int = 5,
    concurrency: int = 50
) -> List[str]:
    """
    Validate a list of DNS servers asynchronously.

    Args:
        servers: List of DNS server IP addresses
        timeout: Query timeout in seconds
        concurrency: Number of concurrent validations

    Returns:
        List of valid DNS server IPs ordered by latency
    """
    # Implementation here
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_validator.py -v

# Run specific test
pytest tests/test_cli.py::TestCLI::test_single_server -v

# Run with coverage
pytest tests/ -v --cov=pyresolvers --cov-report=html
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names
- Test both success and failure cases

### Test Example

```python
import unittest
from pyresolvers import Validator


class TestValidator(unittest.TestCase):
    """Test Validator class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = Validator(concurrency=10)
        self.test_servers = ['1.1.1.1', '8.8.8.8']

    def test_validate_returns_results(self):
        """Test that validate() returns ValidationResult objects."""
        results = self.validator.validate(self.test_servers)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
```

## Submitting Changes

### Pull Request Process

1. **Fill out the PR template** completely
2. **Link related issues** using "Fixes #123" or "Relates to #456"
3. **Provide clear description** of what changed and why
4. **Include test results** showing all tests pass
5. **Add screenshots** if the change affects CLI output
6. **Update documentation** if adding/changing features
7. **Wait for review** - maintainers will review and provide feedback

### PR Requirements

- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] New code has appropriate tests
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts with master branch

### Review Process

- Maintainers will review your PR within a few days
- Address any feedback or requested changes
- Once approved, a maintainer will merge your PR
- Your contribution will be included in the next release!

## Reporting Bugs

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Test with latest version** to see if bug still exists
3. **Gather information** about your environment

### Bug Report Template

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:

- **Clear title**: `[BUG] Brief description`
- **Steps to reproduce**: Exact commands and inputs
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, PyResolvers version
- **Error output**: Full error messages and stack traces

### Example Bug Report

```markdown
## Bug Description
Verbose mode doesn't show rejected servers when using --max-speed filter

## To Reproduce
pyresolvers -tL servers.txt --max-speed 10 -v

## Expected Behavior
Should see [REJECTED] lines for servers exceeding 10ms

## Environment
- OS: Ubuntu 22.04
- Python: 3.12.0
- PyResolvers: 2.0.2
```

## Requesting Features

### Feature Request Template

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) and include:

- **Clear description** of the proposed feature
- **Use case**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Examples**: CLI/API usage examples
- **Alternatives**: Other solutions considered

### Example Feature Request

```markdown
## Feature Description
Add support for IPv6 DNS servers

## Use Case
Many networks now use IPv6 DNS servers, but pyresolvers only supports IPv4

## Proposed Solution
pyresolvers -t 2001:4860:4860::8888
validator = Validator()
results = validator.validate(['2001:4860:4860::8888'])
```

## Project Structure

```
pyresolvers/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── workflows/
│   │   └── test-and-publish.yml
│   └── pull_request_template.md
├── pyresolvers/
│   ├── __init__.py
│   ├── __main__.py
│   ├── validator.py
│   └── lib/core/
│       ├── input.py
│       ├── output.py
│       └── __version__.py
├── tests/
│   ├── test_validator.py
│   └── test_cli.py
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── requirements.txt
└── setup.py
```

## Questions?

- **Check existing issues**: Someone may have asked already
- **Open a discussion**: Use GitHub Discussions for questions
- **Be patient**: Maintainers are volunteers with limited time

## Recognition

All contributors will be recognized in:
- GitHub contributors list
- Release notes for their contributions
- Project acknowledgments

Thank you for contributing to PyResolvers! 🚀
