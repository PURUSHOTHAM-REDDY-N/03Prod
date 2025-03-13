# Timetable Documentation

This directory contains comprehensive documentation for the Timetable application. These guides provide standards, best practices, and tools to ensure code quality and maintainability.

## Available Documentation

### [Template Best Practices](./template_best_practices.md)

A comprehensive guide on handling JavaScript interactions with Jinja2 template variables to avoid syntax errors and ensure proper data handling. Includes:

- Common issues and their solutions
- Best practices for template-JavaScript interactions
- Implementation examples for common scenarios
- Testing and validation recommendations

### [Linting Guide](./linting_guide.md)

Instructions for setting up linting tools to automatically catch template syntax issues and other common errors:

- Python linting with Flake8
- JavaScript/HTML linting with ESLint
- Custom template validation script
- VSCode integration
- Pre-commit hooks setup
- Continuous integration configuration

### [Testing Guide](./testing_guide.md)

Testing procedures to ensure template syntax issues and other common errors are caught early:

- Frontend testing with Jest
- Backend testing with Pytest
- Template validation testing
- Integration testing
- Continuous integration setup
- Pre-commit testing hooks
- Testing best practices

## Tools

The documentation references several tools that have been created to support development:

- **Template Validator**: Located at `app/utils/template_validator.py`, this script automatically scans HTML templates for common syntax issues.

## Quick Start

1. Read the [Template Best Practices](./template_best_practices.md) guide to understand proper patterns for template-JavaScript interactions.
2. Set up linting by following the [Linting Guide](./linting_guide.md).
3. Implement testing procedures from the [Testing Guide](./testing_guide.md).
4. Run the template validator to check existing templates:
   ```bash
   python app/utils/template_validator.py
   ```

## Keeping Documentation Up to Date

These documentation files should be maintained alongside the codebase. When making significant changes to the application, consider:

1. Updating relevant documentation to reflect new patterns or practices
2. Extending the template validator for new edge cases discovered
3. Adding new tests to cover additional scenarios

## Contribution Guidelines

When contributing to the documentation:

1. Keep examples clear and focused on specific issues
2. Include both incorrect and correct code samples
3. Explain the "why" behind recommendations, not just the "how"
4. Test any code examples to ensure they work as described
