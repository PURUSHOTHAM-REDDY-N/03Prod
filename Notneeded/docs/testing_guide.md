# Testing Guide for Timetable Application

This guide outlines testing procedures to ensure template syntax issues and other common errors are caught early in the development process.

## Frontend Testing

### Setting Up Jest for JavaScript Testing

Jest is a JavaScript testing framework that can be used to test your frontend code:

```bash
# Install Jest and related packages
npm install --save-dev jest babel-jest @babel/core @babel/preset-env

# Create a basic Jest configuration file
echo "module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['./jest.setup.js'],
  testPathIgnorePatterns: ['/node_modules/'],
  transform: {
    '^.+\\.js$': 'babel-jest',
  },
};" > jest.config.js

# Create Jest setup file
echo "// Add any global test setup here" > jest.setup.js
```

### Writing Tests for Template-Generated JavaScript

Create a test directory:

```bash
mkdir -p tests/js
```

Example test for dynamic content handling (tests/js/template-data.test.js):

```javascript
describe('Template Data Processing', () => {
  // Mock the document body with elements that would be 
  // created by your template
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="progress-bar-fill" data-percentage="75"></div>
      <div class="update-trigger" data-id="123" data-value="test"></div>
    `;
  });

  test('Progress bar should be updated based on data attribute', () => {
    // Simulate the code that would run in your template
    const progressBarFill = document.getElementById('progress-bar-fill');
    if (progressBarFill) {
        const percentage = progressBarFill.getAttribute('data-percentage');
        progressBarFill.style.width = percentage + '%';
    }
    
    // Assert the result
    expect(progressBarFill.style.width).toBe('75%');
  });

  test('Update trigger should pass correct data to event handler', () => {
    // Mock update function
    const updateValue = jest.fn();
    
    // Add the event listener as your code would
    document.querySelectorAll('.update-trigger').forEach(function(element) {
        element.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const value = this.getAttribute('data-value');
            updateValue(id, value);
        });
    });
    
    // Trigger the event
    document.querySelector('.update-trigger').click();
    
    // Assert the mock was called with the right arguments
    expect(updateValue).toHaveBeenCalledWith('123', 'test');
  });
});
```

## Python Backend Testing

### Setting Up Pytest for Python Testing

```bash
# Install pytest and related packages
pip install pytest pytest-cov

# Add to requirements-dev.txt
echo "pytest==7.4.0" >> requirements-dev.txt
echo "pytest-cov==4.1.0" >> requirements-dev.txt
```

### Create a Basic Test Configuration (conftest.py)

```python
import pytest
from app import create_app
from app import db as _db

@pytest.fixture
def app():
    """Create a Flask app context for testing."""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    with app.test_client() as client:
        yield client

@pytest.fixture
def db(app):
    """Access to the database."""
    return _db
```

### Example Test for Template Rendering (tests/test_templates.py)

```python
from bs4 import BeautifulSoup

def test_index_template_structure(client):
    """Test that the index template is structured correctly."""
    response = client.get('/')
    assert response.status_code == 200
    
    # Parse the HTML
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check for proper structure
    assert soup.title.string == 'Dashboard | Timetable'
    
    # Check for problematic patterns
    onclick_handlers = [element.get('onclick') for element in soup.select('[onclick]')]
    for handler in onclick_handlers:
        # Ensure template variables are properly quoted
        assert '{{' not in handler, f"Unquoted template variable in onclick: {handler}"
    
    # Check for duplicate class attributes
    elements = soup.find_all(lambda tag: tag.attrs.get('class', None))
    for element in elements:
        assert isinstance(element.get('class'), (list, str)), f"Duplicate class attribute in {element}"

def test_data_attribute_usage(client):
    """Test proper use of data attributes for passing data to JavaScript."""
    response = client.get('/progress')
    assert response.status_code == 200
    
    soup = BeautifulSoup(response.data, 'html.parser')
    
    # Check progress bar implementation
    progress_bar = soup.select_one('#progress-bar-fill')
    assert progress_bar is not None, "Progress bar element not found"
    assert 'data-percentage' in progress_bar.attrs, "Progress bar missing data-percentage attribute"
    assert progress_bar['style'] != "", "Progress bar style should be set"
```

## Template Validator Testing

Test the template validator script itself to ensure it can identify issues correctly:

```python
# tests/test_template_validator.py
import pytest
from app.utils.template_validator import check_unquoted_variables
import tempfile
import os

def test_validator_finds_unquoted_variables():
    """Test that the validator can find unquoted template variables."""
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        f.write(b"""
        <div onclick="completeTask({{ task.id }})">Click me</div>
        """)
        file_path = f.name
    
    try:
        issues = check_unquoted_variables(file_path)
        assert len(issues) > 0
        assert any(issue['type'] == 'unquoted_variable' for issue in issues)
    finally:
        os.unlink(file_path)

def test_validator_approves_quoted_variables():
    """Test that the validator accepts properly quoted template variables."""
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        f.write(b"""
        <div onclick="completeTask('{{ task.id }}')">Click me</div>
        """)
        file_path = f.name
    
    try:
        issues = check_unquoted_variables(file_path)
        assert not any(issue['type'] == 'unquoted_variable' for issue in issues)
    finally:
        os.unlink(file_path)
```

## Integration Testing

Integration tests should verify that frontend and backend components work together correctly:

```python
# tests/test_integration.py
def test_task_completion_integration(client, db):
    """Test task completion flow from UI to database."""
    # Create a test task
    from app.models.task import Task
    
    task = Task(title="Test Task", description="Test Description")
    db.session.add(task)
    db.session.commit()
    
    # Complete the task through API (simulating the JS ajax call)
    response = client.post(f'/api/tasks/complete/{task.id}', 
                          headers={"Content-Type": "application/json"})
    
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] == True
    
    # Verify task is marked as completed in database
    updated_task = Task.query.get(task.id)
    assert updated_task.completed_at is not None
```

## Continuous Integration Setup

Create a GitHub Actions workflow file (`.github/workflows/tests.yml`):

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run template validator
      run: |
        python app/utils/template_validator.py
    - name: Run pytest
      run: |
        pytest
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    - name: Install Node dependencies
      run: |
        npm install
    - name: Run Jest tests
      run: |
        npm test
```

## Pre-commit Testing Hooks

Add testing to pre-commit hooks (update `.pre-commit-config.yaml`):

```yaml
repos:
# ... (existing hooks) ...
-   repo: local
    hooks:
    -   id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Running Tests

```bash
# Run all Python tests
pytest

# Run with coverage report
pytest --cov=app

# Run specific test file
pytest tests/test_templates.py

# Run JavaScript tests
npm test
```

## Testing Best Practices

1. **Test Template-JavaScript Interactions**:
   - Test event handlers receive correct data from data attributes
   - Verify dynamic DOM manipulation works as expected
   - Test JSON serialization and parsing

2. **Validate Template Rendering**:
   - Ensure templates render without errors
   - Check for expected DOM structure
   - Verify data is correctly passed to the template

3. **Test Frontend-Backend Communication**:
   - Test API endpoints with both valid and invalid data
   - Verify error handling works correctly
   - Test that frontend can parse and use API responses

4. **Isolate JavaScript Tests**:
   - Mock DOM elements that would be created by templates
   - Test specific functionality in isolation
   - Use JSDOM for more complex DOM interactions

By implementing these testing procedures, you can catch template syntax issues and other bugs early in the development process, ensuring a more stable and maintainable application.
