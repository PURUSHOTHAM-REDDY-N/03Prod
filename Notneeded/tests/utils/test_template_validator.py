import pytest
import os
import tempfile
from app.utils.template_validator import (
    check_unquoted_variables,
    check_missing_csrf_token,
    check_large_inline_scripts,
    check_improper_json_serialization,
    check_missing_data_attributes
)

class TestTemplateValidator:
    
    def create_temp_template(self, content):
        """Helper to create a temporary template file for testing."""
        fd, path = tempfile.mkstemp(suffix='.html')
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        self.temp_files.append(path)
        return path
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup before and teardown after each test."""
        self.temp_files = []
        yield
        # Cleanup temporary files
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_unquoted_variables(self):
        """Test detection of unquoted template variables in event handlers."""
        # Template with unquoted variable
        template_with_issue = """
        <button onclick="completeTask({{ task.id }})">Complete</button>
        """
        
        # Template with properly quoted variable
        template_without_issue = """
        <button onclick="completeTask('{{ task.id }}')">Complete</button>
        """
        
        # Create temp files
        path_with_issue = self.create_temp_template(template_with_issue)
        path_without_issue = self.create_temp_template(template_without_issue)
        
        # Check for issues
        issues_found = check_unquoted_variables(path_with_issue)
        issues_not_found = check_unquoted_variables(path_without_issue)
        
        # Verify results
        assert any(issue['type'] == 'unquoted_variable' for issue in issues_found)
        assert not any(issue['type'] == 'unquoted_variable' for issue in issues_not_found)
    
    def test_inline_style_with_variable(self):
        """Test detection of template variables in style attributes."""
        # Template with style variable
        template_with_issue = """
        <div style="width: {{ completion_percentage }}%">Progress</div>
        """
        
        # Template with data attribute approach
        template_without_issue = """
        <div id="progress-bar" data-percentage="{{ completion_percentage }}">Progress</div>
        <script>
            document.getElementById('progress-bar').style.width = 
                document.getElementById('progress-bar').getAttribute('data-percentage') + '%';
        </script>
        """
        
        # Create temp files
        path_with_issue = self.create_temp_template(template_with_issue)
        path_without_issue = self.create_temp_template(template_without_issue)
        
        # Check for issues
        issues_found = check_unquoted_variables(path_with_issue)
        issues_not_found = check_unquoted_variables(path_without_issue)
        
        # Verify results
        assert any(issue['type'] == 'inline_style_with_var' for issue in issues_found)
        assert not any(issue['type'] == 'inline_style_with_var' for issue in issues_not_found)
    
    def test_duplicate_class_attributes(self):
        """Test detection of duplicate class attributes."""
        # Template with duplicate class
        template_with_issue = """
        <div class="card" class="selected">Content</div>
        """
        
        # Template with combined classes
        template_without_issue = """
        <div class="card selected">Content</div>
        """
        
        # Create temp files
        path_with_issue = self.create_temp_template(template_with_issue)
        path_without_issue = self.create_temp_template(template_without_issue)
        
        # Check for issues
        issues_found = check_unquoted_variables(path_with_issue)
        issues_not_found = check_unquoted_variables(path_without_issue)
        
        # Verify results
        assert any(issue['type'] == 'duplicate_class' for issue in issues_found)
        assert not any(issue['type'] == 'duplicate_class' for issue in issues_not_found)
    
    def test_complex_conditional_in_handler(self):
        """Test detection of complex conditionals in event handlers."""
        # Template with complex conditional
        template_with_issue = """
        <button onclick="{% if user.is_admin %}deleteItem({{ item.id }}){% else %}viewItem({{ item.id }}){% endif %}">
            Action
        </button>
        """
        
        # Template with data attribute approach
        template_without_issue = """
        <button 
            data-action="{% if user.is_admin %}delete{% else %}view{% endif %}"
            data-id="{{ item.id }}">
            Action
        </button>
        <script>
            document.querySelector('button').addEventListener('click', function() {
                const action = this.getAttribute('data-action');
                const id = this.getAttribute('data-id');
                if (action === 'delete') {
                    deleteItem(id);
                } else {
                    viewItem(id);
                }
            });
        </script>
        """
        
        # Create temp files
        path_with_issue = self.create_temp_template(template_with_issue)
        path_without_issue = self.create_temp_template(template_without_issue)
        
        # Check for issues
        issues_found = check_unquoted_variables(path_with_issue)
        issues_not_found = check_unquoted_variables(path_without_issue)
        
        # Verify results
        assert any(issue['type'] == 'complex_conditional' for issue in issues_found)
        assert not any(issue['type'] == 'complex_conditional' for issue in issues_not_found)
    
    def test_id_in_loop(self):
        """Test detection of static IDs in loops."""
        # Template with ID in loop
        template_with_issue = """
        {% for item in items %}
            <div id="item-card">{{ item.name }}</div>
        {% endfor %}
        """
        
        # Template with dynamic ID
        template_without_issue = """
        {% for item in items %}
            <div id="item-{{ item.id }}">{{ item.name }}</div>
        {% endfor %}
        """
        
        # Create temp files
        path_with_issue = self.create_temp_template(template_with_issue)
        path_without_issue = self.create_temp_template(template_without_issue)
        
        # Check for issues
        issues_found = check_unquoted_variables(path_with_issue)
        issues_not_found = check_unquoted_variables(path_without_issue)
        
        # Verify results
        assert any(issue['type'] == 'id_in_loop' for issue in issues_found)
        assert not any(issue['type'] == 'id_in_loop' for issue in issues_not_found)
    
    def test_missing_csrf_token(self):
        """Test detection of missing CSRF tokens in POST forms."""
        # Form without CSRF token
        form_with_issue = """
        <form method="POST" action="/submit">
            <input type="text" name="username">
            <button type="submit">Submit</button>
        </form>
        """
        
        # Form with Flask-WTF CSRF token
        form_with_wtf_token = """
        <form method="POST" action="/submit">
            {{ form.csrf_token() }}
            <input type="text" name="username">
            <button type="submit">Submit</button>
        </form>
        """
        
        # Form with manual CSRF token
        form_with_manual_token = """
        <form method="POST" action="/submit">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <input type="text" name="username">
            <button type="submit">Submit</button>
        </form>
        """
        
        # Form with GET method (no CSRF needed)
        form_with_get = """
        <form method="GET" action="/search">
            <input type="text" name="query">
            <button type="submit">Search</button>
        </form>
        """
        
        # Check for issues
        issues_with_issue = check_missing_csrf_token(form_with_issue)
        issues_with_wtf_token = check_missing_csrf_token(form_with_wtf_token)
        issues_with_manual_token = check_missing_csrf_token(form_with_manual_token)
        issues_with_get = check_missing_csrf_token(form_with_get)
        
        # Verify results
        assert len(issues_with_issue) > 0
        assert len(issues_with_wtf_token) == 0
        assert len(issues_with_manual_token) == 0
        assert len(issues_with_get) == 0
    
    def test_large_inline_scripts(self):
        """Test detection of large inline scripts."""
        # Small inline script
        small_script = """
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                console.log('Page loaded');
            });
        </script>
        """
        
        # Large inline script
        large_script = """
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                console.log('Page loaded');
                
                // Line 1
                const elements = document.querySelectorAll('.item');
                
                // Line 2
                for (let i = 0; i < elements.length; i++) {
                    elements[i].addEventListener('click', function() {
                        console.log('Clicked', i);
                    });
                }
                
                // Line 3
                function processData(data) {
                    return data.map(item => item * 2);
                }
                
                // Line 4
                const result = processData([1, 2, 3, 4]);
                
                // Line 5
                console.log(result);
                
                // Line 6
                if (window.innerWidth > 768) {
                    console.log('Large screen');
                } else {
                    console.log('Small screen');
                }
                
                // Lines 7-15
                let counter = 0;
                function incrementCounter() {
                    counter++;
                    console.log(counter);
                    if (counter < 10) {
                        setTimeout(incrementCounter, 1000);
                    }
                }
                incrementCounter();
            });
        </script>
        """
        
        # External script
        external_script = """
        <script src="/static/js/main.js"></script>
        """
        
        # Check for issues
        issues_small = check_large_inline_scripts(small_script)
        issues_large = check_large_inline_scripts(large_script)
        issues_external = check_large_inline_scripts(external_script)
        
        # Verify results
        assert len(issues_small) == 0
        assert len(issues_large) > 0
        assert len(issues_external) == 0
    
    def test_improper_json_serialization(self):
        """Test detection of improper JSON serialization for complex data."""
        # Improper serialization
        improper_serialization = """
        <script>
            const subjectData = {
                {% for subject_id, stats in subject_stats.items() %}
                    "{{ subject_id }}": {
                        name: "{{ stats.name }}",
                        completed: {{ stats.completed }},
                        total: {{ stats.total }}
                    }{% if not loop.last %},{% endif %}
                {% endfor %}
            };
        </script>
        """
        
        # Proper serialization with tojson filter
        proper_serialization = """
        <script>
            const subjectDataJson = '{{ subject_stats|tojson|safe }}';
            const subjectData = JSON.parse(subjectDataJson);
        </script>
        """
        
        # Check for issues
        issues_improper = check_improper_json_serialization(improper_serialization)
        issues_proper = check_improper_json_serialization(proper_serialization)
        
        # Verify results
        assert len(issues_improper) > 0
        assert len(issues_proper) == 0
    
    def test_complex_data_in_attributes(self):
        """Test detection of complex data in attributes that should use data attributes."""
        # Complex data in attribute
        complex_data_attribute = """
        <button onclick="processItems({{ items|map(attribute='id')|list }})">Process Items</button>
        """
        
        # Data attribute approach
        data_attribute_approach = """
        <button class="process-btn" data-items='{{ items|map(attribute="id")|list|tojson }}'>Process Items</button>
        <script>
            document.querySelector('.process-btn').addEventListener('click', function() {
                const items = JSON.parse(this.getAttribute('data-items'));
                processItems(items);
            });
        </script>
        """
        
        # Check for issues
        issues_complex = check_missing_data_attributes(complex_data_attribute)
        issues_data_attr = check_missing_data_attributes(data_attribute_approach)
        
        # Verify results
        assert len(issues_complex) > 0
        assert len(issues_data_attr) == 0
    
    def test_complete_validator_check(self):
        """Integration test checking that all validators work together."""
        # Template with multiple issues
        template_with_issues = """
        <form method="POST" action="/submit">
            <input type="text" name="username">
            <button onclick="submitForm({{ form.id }})">Submit</button>
        </form>
        
        <div style="width: {{ progress }}%"></div>
        
        <div class="card" class="selected">Content</div>
        
        {% for item in items %}
            <div id="item-card">{{ item.name }}</div>
        {% endfor %}
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                // This is a large script with many lines
                // Line 1
                const elements = document.querySelectorAll('.item');
                // Line 2
                for (let i = 0; i < elements.length; i++) {
                    elements[i].addEventListener('click', function() {
                        console.log('Clicked', i);
                    });
                }
                // Line 3-15 with more code...
                function processData(data) { return data.map(item => item * 2); }
                const result = processData([1, 2, 3, 4]);
                console.log(result);
                if (window.innerWidth > 768) {
                    console.log('Large screen');
                } else {
                    console.log('Small screen');
                }
                let counter = 0;
                function incrementCounter() {
                    counter++;
                    console.log(counter);
                    if (counter < 10) {
                        setTimeout(incrementCounter, 1000);
                    }
                }
                incrementCounter();
            });
            
            const subjectData = {
                {% for subject_id, stats in subject_stats.items() %}
                    "{{ subject_id }}": {
                        name: "{{ stats.name }}",
                        completed: {{ stats.completed }},
                        total: {{ stats.total }}
                    }{% if not loop.last %},{% endif %}
                {% endfor %}
            };
        </script>
        """
        
        # Create temp file
        path_with_issues = self.create_temp_template(template_with_issues)
        
        # Check for issues
        issues = check_unquoted_variables(path_with_issues)
        
        # Verify results - should find at least 6 different types of issues
        issue_types = set(issue['type'] for issue in issues)
        assert len(issue_types) >= 6
        
        # Check specific issue types
        assert 'unquoted_variable' in issue_types
        assert 'inline_style_with_var' in issue_types
        assert 'duplicate_class' in issue_types
        assert 'id_in_loop' in issue_types
        assert 'missing_csrf_token' in issue_types
        assert 'large_inline_script' in issue_types

if __name__ == "__main__":
    pytest.main(['-xvs', __file__])
