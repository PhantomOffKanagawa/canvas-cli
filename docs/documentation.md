# Canvas CLI Documentation Guidelines

## Overview

This document outlines the documentation standards for the Canvas CLI project, covering both in-code documentation and external documentation. Following these guidelines ensures consistency and helps maintain high-quality, accessible documentation.

## Documentation Structure

```
canvas-cli/
  ├── canvas_cli/               # Source code with in-code documentation
  ├── docs/                     # Documentation directory
  │   ├── testing_guide.md      # Guide for running and writing tests
  │   ├── documentation.md      # This file - documentation standards
  │   └── learning.md           # Things I learned while working on this project
  ├── tests/                    # Tests directory
  └── README.md                 # Project overview and quick start
```

## In-Code Documentation

### Module Docstrings

Each Python module should begin with a docstring that explains its purpose:

```python
"""
Canvas API module
Handles communication with the Canvas REST API
"""
```

### Class Docstrings

Every class should have a docstring explaining its purpose and functionality:

```python
class CanvasAPI:
    """Main class for interacting with the Canvas API
    
    This class provides methods to communicate with the Canvas LMS API,
    handling authentication, requests, and response parsing.
    """
```

### Function/Method Docstrings

Document all functions and methods using the following format:

```python
def submit_assignment(course_id, assignment_id, file_path):
    """Submit an assignment file to Canvas
    
    Args:
        course_id (int): The Canvas course ID
        assignment_id (int): The Canvas assignment ID
        file_path (str): Path to the file to submit
        
    Returns:
        dict: The submission response from Canvas
        
    Raises:
        ValueError: If the file doesn't exist or can't be read
        RequestException: If the API request fails
    """
```

### Code Comments

Use comments to explain complex logic, workarounds, or non-obvious decisions:

```python
# Use a fallback method for Windows systems where curses is not available
if not CURSES_AVAILABLE:
    return text_select_course_and_assignment()
```

### TODOs

Mark incomplete functionality with TODO comments that include context:

```python
# TODO: Add support for quiz submissions (waiting for API endpoint documentation)
```

## External Documentation

### README.md

The project README should include:

- Brief project description
- Installation instructions
- Quick start guide
- Basic usage examples
- Links to more detailed documentation

### Feature Documentation

For each major feature, provide:

1. Overview of what the feature does
2. Command syntax and options
3. Example usages
4. Common issues and solutions

Example:

```markdown
## Pull Command

The `pull` command downloads assignment descriptions and related files from Canvas.

### Basic Usage

`canvas pull -cid 12345 -aid 67890`

### Options

- `-cid, --course_id` - Canvas course ID
- `-aid, --assignment_id` - Canvas assignment ID
- `-o, --output` - Output filename (default: README.md)
- `-pdf` - Download linked PDFs
- `-cdl, --convert_links` - Add clean download links
```

## API Documentation

Document the Canvas API endpoints used by the application:

```markdown
### Canvas API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /courses` | List user's courses |
| `GET /courses/{course_id}/assignments` | List assignments in course |
| `POST /courses/{course_id}/assignments/{assignment_id}/submissions` | Submit assignment |
```

## Maintaining Documentation

### When to Update

Documentation should be updated when:

1. Adding a new feature
2. Changing existing functionality
3. Fixing bugs that affect user experience
4. Improving or clarifying existing documentation

### Documentation Review Checklist

Before submitting changes, ensure:

- [ ] All new functionality is documented
- [ ] Affected existing documentation is updated
- [ ] Code examples are accurate and tested
- [ ] Spelling and grammar are correct
- [ ] Formatting is consistent

## Documentation Tools

Consider using these tools to enhance documentation:

1. **Sphinx** - For generating comprehensive HTML documentation
2. **mkdocs** - For simple, readable documentation sites
3. **doctest** - For testing code examples in docstrings

## Docstring Style Guide

We use Google-style docstrings for consistency:

```python
def function_with_types_in_docstring(param1, param2):
    """Example function with types documented in the docstring.
    
    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.
    
    Returns:
        bool: The return value. True for success, False otherwise.
    """
```
