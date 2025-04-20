# Canvas CLI Testing Guide

## Overview

This document explains the testing approach used in Canvas CLI, how the tests were written, and how to run and maintain them. The test suite is designed to verify the functionality of the code without requiring an actual Canvas LMS instance.

> [!NOTE]
> Testing is a personal weakness of mine as writing tests came up the least in my CS degree. I am working on improving this skill, but this was quickly spun up by Copilot so I could just get the code out there. I will be working on improving this in the future, but I wanted to get this out there for now. If you have any suggestions or improvements, please feel free to reach out!

## Test Structure

The test suite follows a hierarchical structure:

```
test/
  ├── test_base.py       # Base test class with common utilities and mock data
  ├── test_config.py     # Tests for configuration management
  ├── test_api.py        # Tests for Canvas API client
  ├── test_cli.py        # Tests for command-line interface
  ├── test_args.py       # Tests for argument parsing
  ├── test_tui_utils.py  # Tests for terminal UI utilities
  └── test_tui.py        # Tests for terminal UI functionality
```

### Base Test Class

All test modules extend the `CanvasCliTestCase` class in `test_base.py`, which:

- Provides mock data for courses, assignments, and other Canvas objects
    - This mock data is either hardcoded or loaded from JSON already present
    - This allows `record_api_responses.py` to be used to record the API responses to use sanitized real data
- Defines helper functions for creating mock API responses
- Sets up a consistent testing environment

## Key Testing Concepts

### Mocking

The tests use Python's `unittest.mock` library to replace real objects with controlled test doubles:

- **API Responses**: Instead of making real HTTP requests to Canvas, we mock the responses
- **File System**: We use temporary directories to avoid modifying real configuration files
- **User Input**: We simulate user input through patched functions

### Example of Mocking

```python
# Mock the API client
with patch('canvas_cli.cli.CanvasAPI') as mock_api_class:
    mock_api = mock_api_class.return_value
    mock_api.get_courses.return_value = [{"id": 12345, "name": "Test Course"}]
    
    # Call function that uses the API
    result = some_function_that_uses_api()
    
    # Verify it made the expected API call
    mock_api.get_courses.assert_called_once()
```

## Running Tests

### Running All Tests

To run the complete test suite:

```
python -m unittest discover test
```

### Running Tests for a Specific Module

To test a single module:

```
python -m unittest test.test_config
```

### Running a Specific Test

To run an individual test case:

```
python -m unittest test.test_config.ConfigTests.test_load_global_config
```

## Adding New Tests

When adding new features to Canvas CLI, follow these steps to create corresponding tests:

1. **Identify the Module**: Determine which module your feature belongs to
2. **Add Mock Data**: If needed, add relevant mock data to `test_base.py`
3. **Write Test Methods**: Create test methods that verify your feature works as expected
4. **Test Edge Cases**: Include tests for unusual or boundary conditions

### Test Method Template

```python
def test_my_new_feature(self):
    """Test description - explain what aspect you're testing"""
    # Setup - prepare any necessary test conditions
    
    # Execute - call the function being tested
    result = function_to_test()
    
    # Verify - check that the results are as expected
    self.assertEqual(result, expected_value)
```

## Best Practices

1. **One Assertion per Test**: Focus each test on verifying a single behavior
2. **Descriptive Names**: Use clear test method names that describe what's being tested
3. **Independence**: Tests should not depend on each other or on system state
4. **Clean Up**: Always clean up temporary files or patched functions in `tearDown()`
5. **Readable Assertions**: Make assertions that clearly show what's expected vs. actual

## Testing New Canvas-CLI Features

When implementing a new feature in Canvas CLI:

1. **Write Tests First**: Consider writing tests before implementing the feature (Test-Driven Development)
2. **Run Tests Frequently**: Test as you develop to catch issues early
3. **Update Existing Tests**: Modify existing tests if your changes affect their behavior
4. **Document Test Coverage**: Note any areas that aren't yet covered by tests

## Troubleshooting Tests

If tests are failing:

1. **Check Mock Data**: Ensure mock data matches what the code expects
2. **Verify Patches**: Make sure patches are applied to the correct paths
3. **Debug with Print Statements**: Add temporary print statements to understand test flow
4. **Inspect Test Independence**: Ensure tests aren't interfering with each other
