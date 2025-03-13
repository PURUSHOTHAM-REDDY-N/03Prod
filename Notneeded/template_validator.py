#!/usr/bin/env python
"""
Template syntax validator for Jinja2 templates.

This script checks HTML template files for common issues related to 
Jinja2 template variables in JavaScript contexts, particularly:
- Unquoted template variables in event handlers
- Template variables in inline styles
- Duplicate HTML attributes
- Complex inline conditionals
- Duplicate IDs in loops
- Missing CSRF tokens in forms
- Large inline scripts
- Improper JSON serialization
- Missing data-attributes for complex data
"""

import os
import re
import glob
import sys
from pathlib import Path

def find_template_files(template_dir='app/templates'):
    """Find all template files in the given directory."""
    return glob.glob(f"{template_dir}/**/*.html", recursive=True)

def check_missing_csrf_token(content):
    """Check for forms without CSRF protection."""
    issues = []
    
    # Find all forms in the template
    forms = re.findall(r'<form[^>]*>.*?</form>', content, re.DOTALL)
    
    for form in forms:
        # Skip forms with method="GET" or no method (defaults to GET)
        if re.search(r'method=[\'"](post|POST)[\'"]', form):
            # Check if the form has a CSRF token
            if not re.search(r'<input[^>]*name=[\'"]csrf_token[\'"]', form) and \
               not re.search(r'\{\{\s*csrf_token\(\)\s*\}\}', form) and \
               not re.search(r'\{\{\s*form\.csrf_token\s*\}\}', form):
                issues.append({
                    'type': 'missing_csrf_token',
                    'content': form[:100] + '...' if len(form) > 100 else form
                })
    
    return issues

def check_large_inline_scripts(content):
    """Check for large inline scripts that should be in external files."""
    issues = []
    
    # Find all script tags in the template
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    
    for script in scripts:
        # Skip scripts with src attribute
        if script.strip() and len(script.strip().split('\n')) > 15:  # If more than 15 lines
            issues.append({
                'type': 'large_inline_script',
                'content': script[:100] + '...' if len(script) > 100 else script
            })
    
    return issues

def check_improper_json_serialization(content):
    """Check for complex data structures without proper JSON serialization."""
    issues = []
    
    # Find JavaScript variable assignments with template for loops
    complex_data_assignments = re.findall(r'(const|let|var)\s+(\w+)\s*=\s*\{[^}]*\{%\s*for\s+[^}]+\s*%\}[^}]*\{%\s*endfor\s*%\}[^}]*\}', content)
    
    for var_type, var_name in complex_data_assignments:
        # Check if |tojson filter is used elsewhere for this variable
        if not re.search(fr'{var_name}\s*=\s*JSON\.parse\([^)]*tojson[^)]*\)', content):
            issues.append({
                'type': 'improper_json_serialization',
                'variable': var_name,
                'content': f"{var_type} {var_name} = {{...}}"
            })
    
    return issues

def check_missing_data_attributes(content):
    """Check for pattern where complex data should use data attributes."""
    issues = []
    
    # Look for inline template variables in attributes other than data-* attributes
    attr_with_vars = re.findall(r'(\w+)=["\']((?:[^"\']*\{\{[^}]+\}\}[^"\']*)+)["\']', content)
    
    for attr_name, attr_value in attr_with_vars:
        if not attr_name.startswith('data-') and \
           attr_name not in ['class', 'id', 'for', 'name', 'value', 'placeholder', 'title', 'alt'] and \
           attr_name.find('on') == 0:  # It's an event handler
            
            # Check if value is complex (contains objects or operators)
            if re.search(r'\{\{[^}]*[\[\]{}()+\-*/%][^}]*\}\}', attr_value):
                issues.append({
                    'type': 'complex_data_in_attribute',
                    'attribute': attr_name,
                    'content': f'{attr_name}="{attr_value}"'
                })
    
    return issues

def check_unquoted_variables(template_path):
    """Check for various template syntax issues."""
    with open(template_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    issues = []
    
    # Look for onclick and other event handlers with unquoted template variables
    handlers = re.findall(r'(on\w+)="([^"]*\{\{[^}]+\}\}[^"]*)"', content)
    
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
    
    # Look for complex inline conditionals in event handlers
    complex_conditionals = re.findall(r'(on\w+)="[^"]*\{%\s*if[^%]+%\}[^"]*"', content)
    for handler in complex_conditionals:
        issues.append({
            'type': 'complex_conditional',
            'handler': handler
        })
    
    # Check for template loops creating multiple elements with the same ID
    id_in_loops = re.findall(r'\{%\s*for\s+[^}]+\s*%\}[^{]*id="[^"]+[^{]*\{%\s*endfor\s*%\}', content)
    for loop in id_in_loops:
        if not re.search(r'id="[^"]*\{\{[^}]+\}\}[^"]*"', loop):  # Allow if ID has a template var
            issues.append({
                'type': 'id_in_loop',
                'content': loop[:50] + '...' if len(loop) > 50 else loop
            })
    
    # Run additional checks
    issues.extend(check_missing_csrf_token(content))
    issues.extend(check_large_inline_scripts(content))
    issues.extend(check_improper_json_serialization(content))
    issues.extend(check_missing_data_attributes(content))
    
    return issues

def main():
    """Main function to run the validator."""
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
                    print(f"    Fix: Add quotes around the template variable")
                
                elif issue['type'] == 'inline_style_with_var':
                    print(f"  - Template variable in inline style: {issue['content']}")
                    print(f"    Fix: Use data attribute and set style with JavaScript")
                
                elif issue['type'] == 'duplicate_class':
                    print(f"  - Duplicate class attribute: {issue['content']}")
                    print(f"    Fix: Combine classes into a single attribute")
                
                elif issue['type'] == 'complex_conditional':
                    print(f"  - Complex conditional in {issue['handler']}")
                    print(f"    Fix: Use data attributes and handle logic in JavaScript")
                
                elif issue['type'] == 'id_in_loop':
                    print(f"  - ID attribute in a loop (may cause duplicate IDs): {issue['content']}")
                    print(f"    Fix: Use dynamic IDs with template variables or use classes instead")
                
                elif issue['type'] == 'missing_csrf_token':
                    print(f"  - POST form missing CSRF token: {issue['content']}")
                    print(f"    Fix: Add {{ form.csrf_token() }} or <input name='csrf_token' value='{{ csrf_token() }}'>")
                
                elif issue['type'] == 'large_inline_script':
                    print(f"  - Large inline script detected (consider moving to external file): {issue['content'][:50]}...")
                    print(f"    Fix: Move to an external .js file and include with <script src=''></script>")
                
                elif issue['type'] == 'improper_json_serialization':
                    print(f"  - Complex data structure without proper JSON serialization: {issue['variable']}")
                    print(f"    Fix: Use const {issue['variable']} = JSON.parse('{{ data|tojson|safe }}')")
                
                elif issue['type'] == 'complex_data_in_attribute':
                    print(f"  - Complex data in attribute {issue['attribute']}: {issue['content']}")
                    print(f"    Fix: Use data attributes and access via JavaScript")
    
    if not issues_found:
        print("✓ No template syntax issues found!")
    
    return 0 if not issues_found else 1

if __name__ == "__main__":
    sys.exit(main())
