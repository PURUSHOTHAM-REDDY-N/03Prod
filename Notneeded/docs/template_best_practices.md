# Template Best Practices

## JavaScript Interaction in Templates

This guide documents best practices for handling JavaScript interactions with template variables to avoid syntax errors and ensure proper data handling.

### Common Issues

1. **Unquoted Template Variables**: Using template variables directly in JavaScript contexts without proper quoting
2. **Complex Data Structures**: Embedding complex data structures directly in JavaScript
3. **Inline Event Handlers**: Using complex template expressions in onclick and other event attributes
4. **Multiple HTML Attributes**: Accidentally duplicating attributes on elements

### Best Practices

#### 1. Quoting Template Variables in JavaScript

Always properly quote template variables used in JavaScript function calls:

```html
<!-- INCORRECT ❌ -->
onclick="completeTask({{ task.id }})"

<!-- CORRECT ✅ -->
onclick="completeTask('{{ task.id }}')"
```

#### 2. Use Data Attributes for Complex Data or Values

For more complex data or when direct embedding causes syntax issues:

```html
<!-- INCORRECT ❌ -->
<div style="width: {{ completion_percentage }}%"></div>

<!-- CORRECT ✅ -->
<div id="progress-bar-fill" data-percentage="{{ completion_percentage }}" style="width: 0%"></div>
```

Then in JavaScript:

```js
const progressBarFill = document.getElementById('progress-bar-fill');
if (progressBarFill) {
    const percentage = progressBarFill.getAttribute('data-percentage');
    progressBarFill.style.width = percentage + '%';
}
```

#### 3. Use JSON Serialization for Complex Data Structures

For complex data structures, use the `|tojson` filter:

```html
<!-- INCORRECT ❌ -->
const subjectData = {
    {% for subject_id, stats in subject_stats.items() %}
        "{{ subject_id }}": {
            name: "{{ stats.name }}",
            completed: {{ stats.completed }},
            total: {{ stats.total }}
        }{% if not loop.last %},{% endif %}
    {% endfor %}
};

<!-- CORRECT ✅ -->
const subjectDataJson = '{{ subject_stats|tojson|safe }}';
const subjectData = JSON.parse(subjectDataJson);
```

#### 4. Move Logic to Event Listeners

For DOM interactions with Jinja variables, use the data attribute pattern with event listeners:

```html
<!-- INCORRECT ❌ -->
<div onclick="updateValue({{ item.id }}, {{ item.value }})">Click me</div>

<!-- CORRECT ✅ -->
<div class="update-trigger" data-id="{{ item.id }}" data-value="{{ item.value }}">Click me</div>
```

Then in JavaScript:

```js
document.querySelectorAll('.update-trigger').forEach(function(element) {
    element.addEventListener('click', function() {
        const id = this.getAttribute('data-id');
        const value = this.getAttribute('data-value');
        updateValue(id, value);
    });
});
```

#### 5. Avoid Duplicate HTML Attributes

Always ensure HTML elements don't have duplicate attributes:

```html
<!-- INCORRECT ❌ -->
<div class="item-card" class="selected">Content</div>

<!-- CORRECT ✅ -->
<div class="item-card selected">Content</div>
```

### Implementation Examples

#### Example: Progress Bar with Data Attributes

```html
<div class="progress-bar">
    <div id="progress-bar-fill" data-percentage="{{ completion_percentage }}" style="width: 0%"></div>
</div>

<script>
    document.addEventListener('DOMContentLoaded', function() {
        const progressBarFill = document.getElementById('progress-bar-fill');
        if (progressBarFill) {
            const percentage = progressBarFill.getAttribute('data-percentage');
            progressBarFill.style.width = percentage + '%';
        }
    });
</script>
```

#### Example: Chart Data with JSON Serialization

```html
<canvas id="data-chart"></canvas>

<script>
    document.addEventListener('DOMContentLoaded', function() {
        // Convert data from Jinja to JSON, then parse it
        const chartDataJson = '{{ chart_data|tojson|safe }}';
        const chartData = JSON.parse(chartDataJson);
        
        // Use the data with Chart.js
        const ctx = document.getElementById('data-chart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'bar',
            data: chartData
        });
    });
</script>
```

#### Example: Interactive Elements with Event Listeners

```html
<div class="interactive-grid">
    {% for item in items %}
        <div class="grid-item" data-id="{{ item.id }}" data-name="{{ item.name }}">
            {{ item.display_name }}
        </div>
    {% endfor %}
</div>

<script>
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.grid-item').forEach(function(element) {
            element.addEventListener('click', function() {
                const id = this.getAttribute('data-id');
                const name = this.getAttribute('data-name');
                processSelection(id, name);
            });
        });
    });
    
    function processSelection(id, name) {
        console.log(`Selected item: ${name} (ID: ${id})`);
        // Additional processing here
    }
</script>
```

### Testing & Validation

Consider implementing these testing practices to catch template-JavaScript issues:

1. **Template Linting**: Use a linter that can check templates for JavaScript syntax issues
2. **Frontend Tests**: Create tests that validate JavaScript interactions with dynamic content
3. **Code Reviews**: Specifically review JavaScript-template interactions during code reviews

By following these best practices consistently across all templates, we can minimize the risk of template syntax issues and improve the maintainability of our code.
