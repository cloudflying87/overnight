# Code Quality Guide

This project uses modern Python development tools to ensure code quality, consistency, and security.

## 🛠️ Tools Included

### Code Formatting
- **Black**: Automatic code formatting (PEP 8 compliant)
- **isort**: Import statement sorting

### Linting
- **Flake8**: Style guide enforcement
- **Pylint**: Comprehensive code analysis
- **flake8-django**: Django-specific linting
- **flake8-bugbear**: Additional bug detection

### Type Checking
- **mypy**: Static type checking
- **django-stubs**: Type stubs for Django

### Security
- **Bandit**: Security vulnerability scanner
- **Safety**: Dependency vulnerability checker

### Testing
- **pytest**: Modern testing framework
- **pytest-django**: Django integration
- **pytest-cov**: Code coverage reporting
- **factory-boy**: Test fixture generation

### Git Hooks
- **pre-commit**: Automatic checks before commits

## 📦 Installation

Install all development tools:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

Or use the Makefile:

```bash
make install
make install-hooks
```

## 🎯 Quick Commands

### Using Make (Recommended)

```bash
# See all available commands
make help

# Format code automatically
make format

# Run all linters
make lint

# Type check
make type-check

# Security scan
make security

# Run tests
make test

# Run tests with coverage
make coverage

# Run ALL checks at once
make check-all

# Clean up generated files
make clean
```

### Manual Commands

```bash
# Format code
black apps config
isort apps config

# Lint code
flake8 apps config
pylint apps config

# Type check
mypy apps config

# Security scan
bandit -r apps config
safety check

# Run tests
pytest

# Coverage report
pytest --cov --cov-report=html
```

## 🔧 Configuration Files

All tools are configured in these files:

- **`pyproject.toml`**: Black, isort, pylint, mypy, pytest, coverage, bandit
- **`.flake8`**: Flake8 configuration
- **`.pre-commit-config.yaml`**: Pre-commit hooks
- **`Makefile`**: Quick command shortcuts

## 🎨 Code Formatting

### Automatic Formatting

```bash
# Format all Python files
make format
```

This runs:
1. **Black** - Formats code to PEP 8 standards
2. **isort** - Organizes imports

### What Gets Formatted

- Line length: 100 characters
- Import order: stdlib → django → third-party → first-party → local
- Trailing commas for better diffs
- Consistent quote style

### Excluded Directories

- `migrations/` - Django migrations are auto-generated
- `venv/` - Virtual environment
- `staticfiles/` - Collected static files

## 🔍 Linting

### Run All Linters

```bash
make lint
```

### Individual Linters

```bash
# Flake8 - Style guide
flake8 apps config

# Pylint - Comprehensive analysis
pylint apps config
```

### What's Checked

- PEP 8 compliance
- Code complexity
- Unused imports/variables
- Django best practices
- Potential bugs
- Code smells

## 🔬 Type Checking

```bash
make type-check
```

Benefits:
- Catch type errors before runtime
- Better IDE autocomplete
- Self-documenting code
- Easier refactoring

Example with type hints:

```python
from typing import List
from apps.care_tracking.models import EventOption

def get_active_options(user) -> List[EventOption]:
    """Get active event options for a user."""
    return EventOption.objects.filter(user=user, is_active=True)
```

## 🔒 Security Scanning

### Run Security Checks

```bash
make security
```

This runs:
1. **Bandit** - Scans code for security issues
2. **Safety** - Checks dependencies for known vulnerabilities

### Common Issues Detected

- SQL injection risks
- Hardcoded passwords
- Insecure cryptography
- Shell injection vulnerabilities
- Vulnerable dependencies

## 🧪 Testing

### Run Tests

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test file
pytest apps/users/tests/test_models.py

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Coverage Report

After running `make coverage`, open:
```
htmlcov/index.html
```

### Writing Tests

Example test:

```python
import pytest
from django.contrib.auth import get_user_model
from apps.care_tracking.models import EventOption

User = get_user_model()

@pytest.mark.django_db
def test_create_event_option():
    """Test creating an event option."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

    option = EventOption.objects.create(
        user=user,
        name='Test Option',
        color_code='#FF0000'
    )

    assert option.name == 'Test Option'
    assert option.is_active is True
    assert str(option) == 'testuser - Test Option'
```

## 🪝 Git Hooks (Pre-commit)

### What Happens on Commit

When you run `git commit`, these checks run automatically:

1. ✅ Remove trailing whitespace
2. ✅ Fix end-of-file formatting
3. ✅ Check YAML/JSON/TOML syntax
4. ✅ Detect large files
5. ✅ Check for merge conflicts
6. ✅ Detect private keys
7. ✅ Format with Black
8. ✅ Sort imports with isort
9. ✅ Lint with Flake8
10. ✅ Scan with Bandit
11. ✅ Django system check
12. ✅ Check for missing migrations

### Skip Hooks (Emergency Only)

```bash
git commit --no-verify -m "Emergency fix"
```

**⚠️ Use sparingly!** The hooks are there to help.

### Run Hooks Manually

```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

## 📊 Continuous Integration

Add these to your CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run code quality checks
  run: |
    pip install -r requirements-dev.txt
    make format
    make lint
    make type-check
    make security
    make test
```

## 🎯 Development Workflow

### Recommended Workflow

1. **Before coding**: Pull latest code
   ```bash
   git pull origin main
   ```

2. **During coding**: Format as you go
   ```bash
   make format
   ```

3. **Before committing**: Run all checks
   ```bash
   make check-all
   ```

4. **Commit**: Hooks run automatically
   ```bash
   git add .
   git commit -m "Add feature X"
   ```

5. **Push**: Code is clean!
   ```bash
   git push origin main
   ```

## 🔧 Customization

### Disable Specific Rules

**Flake8** (in `.flake8`):
```ini
extend-ignore = E203,E501,W503
```

**Pylint** (in `pyproject.toml`):
```toml
[tool.pylint.messages_control]
disable = ["C0111", "C0103"]
```

**Black** (in `pyproject.toml`):
```toml
[tool.black]
line-length = 120  # Change from 100
```

### Ignore Specific Lines

```python
# Flake8
x = some_long_function()  # noqa: E501

# Pylint
x = some_var  # pylint: disable=invalid-name

# Mypy
x = some_var  # type: ignore

# Bandit
os.system(cmd)  # nosec B605
```

## 📈 Metrics and Goals

### Current Status

- **Code Coverage**: Aim for 80%+
- **Linting**: Zero errors
- **Type Coverage**: Gradually increase
- **Security**: Zero high-severity issues

### Check Project Health

```bash
# Run everything
make check-all

# Check coverage percentage
pytest --cov --cov-report=term

# Check complexity
flake8 --max-complexity=10 apps
```

## 🆘 Troubleshooting

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt -r requirements-dev.txt
```

### Pre-commit Issues

```bash
# Update hooks
pre-commit autoupdate

# Clean and reinstall
pre-commit clean
pre-commit install
```

### Type Checking Errors

```bash
# Install stubs
pip install django-stubs types-redis
```

## 📚 Learning Resources

- **Black**: https://black.readthedocs.io/
- **Flake8**: https://flake8.pycqa.org/
- **Pylint**: https://pylint.readthedocs.io/
- **mypy**: https://mypy.readthedocs.io/
- **pytest**: https://docs.pytest.org/
- **pre-commit**: https://pre-commit.com/

## ✅ Best Practices

1. ✅ Run `make format` often
2. ✅ Run `make check-all` before committing
3. ✅ Write tests for new features
4. ✅ Add type hints to new functions
5. ✅ Keep coverage above 80%
6. ✅ Fix linting errors immediately
7. ✅ Review security scan results
8. ✅ Update dependencies regularly

---

**Remember**: These tools are here to help you write better code faster. Use them!
