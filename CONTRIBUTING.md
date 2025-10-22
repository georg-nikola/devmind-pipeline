# Contributing to DevMind Pipeline

Thank you for your interest in contributing to DevMind Pipeline! This document provides guidelines for contributing to the project.

## 🔀 Contribution Workflow

We use a **fork-based workflow** to keep the main repository clean and organized. All external contributions must come through pull requests from forked repositories.

### Getting Started

1. **Fork the Repository**
   ```bash
   # Click the "Fork" button on GitHub or use gh CLI
   gh repo fork georg-nikola/devmind-pipeline --clone
   cd devmind-pipeline
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Write clear, documented code
   - Follow the project's coding standards
   - Add tests for new features
   - Update documentation as needed

4. **Run Tests Locally**
   ```bash
   # Python tests and linting
   cd src
   pip install -r requirements.txt
   pip install pytest black isort mypy

   black --check .
   pytest tests/ -v

   # Check for security issues
   pip install safety bandit
   safety check -r requirements.txt
   bandit -r . -f json
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

6. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   ```bash
   # Using gh CLI
   gh pr create --base main --head your-username:feature/your-feature-name

   # Or visit GitHub and click "New Pull Request"
   ```

## 📋 Pull Request Guidelines

### Branch Protection Rules

The `main` branch is protected with the following requirements:

- ✅ **Required Status Checks**: All CI tests must pass
  - Test Python ML Services (3.11)
  - Test Python ML Services (3.12)
  - Security Scan
- ✅ **Pull Request Reviews**: At least 1 approving review required
- ✅ **Linear History**: Merge commits or squash merges only
- ✅ **Conversation Resolution**: All comments must be resolved
- ✅ **Branch Up-to-Date**: Branch must be current with main before merging
- ❌ **Force Pushes**: Not allowed on main
- ❌ **Direct Commits**: All changes must go through PRs

### PR Checklist

Before submitting your pull request, ensure:

- [ ] Code follows Python PEP 8 style guide
- [ ] All tests pass locally
- [ ] Black formatting is applied (`black .`)
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains the changes

### PR Template

Please use this template for your pull request:

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

## 🔧 Development Guidelines

### Code Style

- **Python**: Follow PEP 8, use Black for formatting
- **Line Length**: 100 characters maximum
- **Imports**: Group by standard library, third-party, local (Black handles this)
- **Type Hints**: Use type hints for function signatures
- **Docstrings**: Use Google-style docstrings

Example:
```python
def optimize_build(
    project_name: str,
    dependencies: List[str],
    historical_data: Optional[Dict[str, Any]] = None
) -> BuildOptimizationResponse:
    """
    Optimize build configuration using ML models.

    Args:
        project_name: Name of the project to optimize
        dependencies: List of project dependencies
        historical_data: Optional historical build data

    Returns:
        BuildOptimizationResponse with recommendations

    Raises:
        ValueError: If project_name is empty
    """
    pass
```

### Testing

- Write tests for all new features
- Maintain test coverage above 80%
- Use pytest for Python tests
- Mock external dependencies

### Documentation

- Update README.md for user-facing changes
- Update API documentation for endpoint changes
- Add comments for complex logic
- Update CHANGELOG.md for notable changes

## 🐛 Reporting Issues

### Bug Reports

Please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)
- Relevant logs or error messages

### Feature Requests

Please include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if any)
- Potential impact on existing functionality

## 📝 Commit Message Guidelines

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add ML model for test selection optimization"
git commit -m "Fix cache invalidation bug in build optimizer"
git commit -m "Update API documentation for /predict endpoints"

# Bad
git commit -m "fix bug"
git commit -m "updates"
git commit -m "wip"
```

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## 🔒 Security

- Never commit secrets, API keys, or credentials
- Use environment variables for configuration
- Report security vulnerabilities privately to the maintainers
- Follow security best practices for Python code

## 📞 Getting Help

- **Documentation**: Check [README.md](README.md) and [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers for sensitive issues

## 📄 License

By contributing to DevMind Pipeline, you agree that your contributions will be licensed under the MIT License.

## 🙏 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the technical merits
- Help create a welcoming environment

---

Thank you for contributing to DevMind Pipeline! 🚀
