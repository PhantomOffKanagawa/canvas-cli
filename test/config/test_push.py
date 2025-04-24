import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from handlers.push_handler import handle_push

# Create fixture for typer context
@pytest.fixture
def mock_context():
    context = MagicMock()
    context.obj = {"verbose": True}
    return context

# Create patched get_key function
@pytest.fixture
def mock_get_key():
    with patch("handlers.push_handler.get_key") as mock:
        yield mock

# Create patched echo function
@pytest.fixture
def mock_echo():
    with patch("handlers.push_handler.echo") as mock:
        yield mock

def test_handle_push_with_all_parameters(mock_context, mock_get_key, mock_echo):
    # Setup
    mock_get_key.side_effect = lambda key, _: {
        "course_id": 12345,
        "assignment_id": 67890,
        "file": "test.py"
    }[key]
    
    # Call function
    handle_push(mock_context, course_id=12345, assignment_id=67890, file="test.py")
    
    # Assertions
    mock_get_key.assert_any_call("course_id", mock_context)
    mock_get_key.assert_any_call("assignment_id", mock_context)
    mock_get_key.assert_any_call("file", mock_context)
    
    assert mock_echo.call_count == 3
    mock_echo.assert_any_call("Course ID: 12345", ctx=mock_context)
    mock_echo.assert_any_call("Assignment ID: 67890", ctx=mock_context)
    mock_echo.assert_any_call("File: test.py", ctx=mock_context)

def test_handle_push_with_missing_parameters(mock_context, mock_get_key, mock_echo):
    # Setup
    mock_get_key.side_effect = lambda key, _: {
        "course_id": 12345,
        "assignment_id": 67890,
        "file": "test.py"
    }[key]
    
    # Call function with None parameters
    handle_push(mock_context, course_id=None, assignment_id=None, file=None)
    
    # Assertions
    mock_get_key.assert_any_call("course_id", mock_context)
    mock_get_key.assert_any_call("assignment_id", mock_context)
    mock_get_key.assert_any_call("file", mock_context)
    
    # Values from get_key should be used, not the None parameters
    mock_echo.assert_any_call("Course ID: 12345", ctx=mock_context)
    mock_echo.assert_any_call("Assignment ID: 67890", ctx=mock_context)
    mock_echo.assert_any_call("File: test.py", ctx=mock_context)

def test_handle_push_different_values(mock_context, mock_get_key, mock_echo):
    # Setup with different values
    mock_get_key.side_effect = lambda key, _: {
        "course_id": 99999,
        "assignment_id": 88888,
        "file": "assignment.pdf"
    }[key]
    
    # Call function
    handle_push(mock_context, course_id=None, assignment_id=None, file=None)
    
    # Assertions
    mock_echo.assert_any_call("Course ID: 99999", ctx=mock_context)
    mock_echo.assert_any_call("Assignment ID: 88888", ctx=mock_context)
    mock_echo.assert_any_call("File: assignment.pdf", ctx=mock_context)