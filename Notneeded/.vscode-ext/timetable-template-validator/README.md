# Timetable Template Validator Extension

A Visual Studio Code extension that provides real-time validation for Jinja2 templates in the Timetable project.

## Features

- Real-time validation of Jinja2 templates
- Highlights common template syntax issues:
  - Unquoted template variables in JavaScript contexts
  - Template variables in inline styles
  - Duplicate HTML attributes
  - Missing CSRF tokens in forms
  - Large inline scripts
  - Improper JSON serialization
  - Complex data in attributes
  - Duplicate IDs in loops
- Integration with the Python template validator script
- Configurable validation frequency (on save or while typing)
- Clear explanation of issues and recommended fixes

## Installation

This extension is designed for local development on the Timetable project:

1. Install Node.js and npm if you don't have them already
2. From the extension directory, run:
   ```
   npm install
   npm run package
   ```
3. Install the generated .vsix file in VS Code:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
   - Type "Install from VSIX" and select the command
   - Choose the generated .vsix file

## Usage

The extension automatically validates HTML files when they are saved. You can also:

- Run validation manually with the command "Validate Current Template"
- Configure validation settings in VS Code settings under "Timetable Template Validator"

## Configuration

The following settings can be customized:

- `timetableTemplateValidator.enable`: Enable/disable the template validator
- `timetableTemplateValidator.validateOnSave`: Run validator automatically when saving HTML files
- `timetableTemplateValidator.validateOnType`: Run validator automatically while typing (may be resource intensive)

## Development

This extension works alongside the Python validator script. The extension handles:

1. Watching for file changes
2. Invoking the Python validator script
3. Parsing the validator output
4. Displaying diagnostics in the editor

To modify validation rules, update the Python validator script at `app/utils/template_validator.py`.

## How It Works

When an HTML file is saved (or edited, if enabled), the extension:

1. Creates a temporary copy of the current file
2. Passes it to the Python validator script
3. Parses the output for issues
4. Displays the issues as diagnostics in VS Code
5. Provides suggested fixes for each issue

This approach leverages the power of the Python validator while providing real-time feedback in the editor.
