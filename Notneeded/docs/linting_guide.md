# Linting Setup Guide

This guide explains how to set up linting tools for the Timetable application to help catch template syntax issues and other common errors automatically.

## Python Linting

### Installing Flake8

Flake8 is a Python linting tool that combines PyFlakes, pycodestyle, and McCabe complexity checker.

```bash
# Install flake8
pip install flake8

# Add to requirements-dev.txt (if you have one)
echo "flake8==7.1.2" >> requirements-dev.txt
```

### Configure Flake8

Create a `.flake8` configuration file in the project root:

```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,migrations,venv,env
ignore = E203,W503
# E203: whitespace before ':' (conflicts with black)
# W503: line break before binary operator (conflicts with black)
```

### Running Flake8

```bash
# Run flake8 on the app directory
flake8 app/

# Run with detailed output
flake8 app/ --statistics --count --show-source
```

## JavaScript/HTML Linting

For template-specific linting, we can use a combination of tools:

### ESLint for JavaScript

```bash
# Install ESLint locally
npm install eslint --save-dev

# Initialize ESLint configuration
npx eslint --init
```

Create a custom `.eslintrc.js` configuration file:

```javascript
module.exports = {
  "env": {
    "browser": true,
    "es2021": true
  },
  "extends": "eslint:recommended",
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "script"
  },
  "rules": {
    "quotes": ["error", "single"],
    "semi": ["error", "always"],
    "no-unused-vars": "warn",
    "no-undef": "error"
  },
  "globals": {
    // Add globals that might appear in your templates
    "Chart": "readonly",
    // Add other global variables used in your JavaScript
  }
};
```

### HTML Template Validation

For validating Jinja templates, we can use a custom script that checks for common issues:

1. Create a script to extract JavaScript from templates and validate it
2. Look for common patterns that cause issues with template variables in JavaScript

## Template Syntax Checker Script

Create a basic template syntax checker (app/utils/template_validator.py):

```python
import os
import re
import glob
from pathlib import Path

def find_template_files(template_dir='app/templates'):
    """Find all template files in the given directory."""
    return glob.glob(f"{template_dir}/**/*.html", recursive=True)

def check_unquoted_variables(template_path):
    """Check for unquoted template variables in JavaScript contexts."""
    with open(template_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Look for onclick and other event handlers with unquoted template variables
    handlers = re.findall(r'(on\w+)="([^"]*\{\{[^}]+\}\}[^"]*)"', content)
    issues = []
    
    for handler_type, handler_content in handlers:
        # Check for unquoted template variables
        if re.search(r'(\W|^)\{\{[^}]+\}\}(\W|$)', handler_content):
            # Make sure they're not already quoted properly
            if not re.search(r"'[^']*\{\{[^}]+\}\}[^']*'", handler_content) and \
               not re.search(r'"[^"]*\{\{[^}]+\}\}[^"]*"', handler_content):
                issues.append({
                    'type': 'unquoted_variable',
                    'handler': handler_type,
                    'content': handler_content.strip()
                })
    
    # Look for style attributes with direct template variables
    style_issues = re.findall(r'style="[^"]*\{\{[^}]+\}\}[^"]*"', content)
    for style in style_issues:
        issues.append({
            'type': 'inline_style_with_var',
            'content': style.strip()
        })
    
    # Look for duplicate class attributes
    class_duplicates = re.findall(r'class="[^"]*"\s+class="[^"]*"', content)
    for duplicate in class_duplicates:
        issues.append({
            'type': 'duplicate_class',
            'content': duplicate.strip()
        })
    
    return issues

def main():
    templates = find_template_files()
    issues_found = False
    
    for template in templates:
        issues = check_unquoted_variables(template)
        
        if issues:
            issues_found = True
            print(f"\n{'-' * 50}")
            print(f"Issues in {template}:")
            for issue in issues:
                if issue['type'] == 'unquoted_variable':
                    print(f"  - Unquoted variable in {issue['handler']}: {issue['content']}")
                elif issue['type'] == 'inline_style_with_var':
                    print(f"  - Template variable in inline style: {issue['content']}")
                elif issue['type'] == 'duplicate_class':
                    print(f"  - Duplicate class attribute: {issue['content']}")
    
    if not issues_found:
        print("No template syntax issues found!")
    
    return 0 if not issues_found else 1

if __name__ == "__main__":
    exit(main())
```

## Integrating with VSCode

For VS Code users, you can add linting extensions and configure them to work with the project:

1. Install the "ESLint" extension for JavaScript linting
2. Install the "Python" extension with linting capabilities
3. Configure settings.json in .vscode folder:

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": [
    "--max-line-length=100"
  ],
  "eslint.validate": [
    "javascript"
  ]
}
```

## Pre-commit Hooks (Optional)

You can set up pre-commit hooks to automatically run linting before each commit:

1. Install pre-commit: `pip install pre-commit`
2. Create a `.pre-commit-config.yaml` file:

```yaml
repos:
-   repo: https://github.com/pycqa/flake8
    rev: 7.1.2
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-docstrings]
-   repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
    -   id: eslint
        files: \.(js)$
        args: [--fix]
-   repo: local
    hooks:
    -   id: template-validator
        name: Check template syntax
        entry: python app/utils/template_validator.py
        language: python
        types: [file]
        files: \.html$
```

3. Install the hooks: `pre-commit install`

## Continuous Integration

Consider setting up these linting checks in your CI pipeline to automatically check code quality on each pull request.

## Running Linting Checks

To check for template syntax issues:

```bash
python app/utils/template_validator.py
```

To run all linting checks (requires pre-commit):

```bash
pre-commit run --all-files
```

By implementing these linting tools, you'll catch most of the template syntax issues automatically, allowing you to fix them before they cause problems in production.
