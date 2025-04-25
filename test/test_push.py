import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import typer
from typer.testing import CliRunner
from handlers.push_handler import handle_push

# ──────────────────────
# HANDLE PUSH TESTS
# ──────────────────────

@patch('handlers.push_handler.get_key')
@patch('handlers.push_handler.get_api')
@patch('handlers.push_handler.echo')
def test_handle_push_missing_course_id(mock_echo, mock_get_api, mock_get_key):
    """Test handle_push with missing course_id"""
    # Setup
    ctx = MagicMock()
    mock_get_key.side_effect = [None, 123, "file.py"]  # course_id=None, assignment_id=123, file="file.py"
    
    # Execute
    handle_push(ctx, None, None, None)
    
    # Assert
    mock_echo.assert_called_once_with("Error: Missing course_id, assignment_id.", ctx=ctx, level="error")
    mock_get_api.assert_not_called()

@patch('handlers.push_handler.get_key')
@patch('handlers.push_handler.get_api')
@patch('handlers.push_handler.echo')
def test_handle_push_missing_assignment_id(mock_echo, mock_get_api, mock_get_key):
    """Test handle_push with missing assignment_id"""
    # Setup
    ctx = MagicMock()
    mock_get_key.side_effect = [123, None, "file.py"]  # course_id=123, assignment_id=None, file="file.py"
    
    # Execute
    handle_push(ctx, None, None, None)
    
    # Assert
    mock_echo.assert_called_once_with("Error: Missing course_id, assignment_id.", ctx=ctx, level="error")
    mock_get_api.assert_not_called()

@patch('handlers.push_handler.get_key')
@patch('handlers.push_handler.get_api')
@patch('handlers.push_handler.echo')
@patch('handlers.push_handler.typer.echo')
def test_handle_push_missing_file(mock_typer_echo, mock_echo, mock_get_api, mock_get_key):
    """Test handle_push with missing file"""
    # Setup
    ctx = MagicMock()
    mock_get_key.side_effect = [123, 456, None]  # course_id=123, assignment_id=456, file=None
    
    # Execute
    handle_push(ctx, None, None, None)
    
    # Assert
    mock_typer_echo.assert_called_once_with("Error: File path must be provided.")
    mock_get_api.assert_not_called()

@patch('handlers.push_handler.get_key')
@patch('handlers.push_handler.get_api')
@patch('handlers.push_handler.echo')
@patch('handlers.push_handler.os.path.exists')
def test_handle_push_file_not_exists(mock_exists, mock_echo, mock_get_api, mock_get_key):
    """Test handle_push with non-existent file"""
    # Setup
    ctx = MagicMock()
    mock_get_key.side_effect = [123, 456, "nonexistent.py"]  # course_id=123, assignment_id=456, file="nonexistent.py"
    mock_exists.return_value = False
    
    # Execute
    handle_push(ctx, None, None, None)
    
    # Assert
    mock_echo.assert_called_once_with("Error: File 'nonexistent.py' does not exist.", ctx=ctx, level="error")
    mock_get_api.assert_not_called()

@patch('handlers.push_handler.get_key')
@patch('handlers.push_handler.get_api')
@patch('handlers.push_handler.echo')
@patch('handlers.push_handler.os.path.exists')
def test_handle_push_api_failure(mock_exists, mock_echo, mock_get_api, mock_get_key):
    """Test handle_push with API failure"""
    # Setup
    ctx = MagicMock()
    mock_get_key.side_effect = [123, 456, "file.py"]  # course_id=123, assignment_id=456, file="file.py"
    mock_exists.return_value = True
    mock_get_api.return_value = None
    
    # Execute
    handle_push(ctx, None, None, None)
    
    # Assert
    mock_echo.assert_called_once_with("Error: Failed to get API instance.", ctx=ctx, level="error")

@patch('handlers.push_handler.get_key')
@patch('handlers.push_handler.get_api')
@patch('handlers.push_handler.os.path.exists')
def test_handle_push_success(mock_exists, mock_get_api, mock_get_key):
    """Test handle_push with successful submission"""
    # Setup
    ctx = MagicMock()
    mock_get_key.side_effect = [123, 456, "file.py"]  # course_id=123, assignment_id=456, file="file.py"
    mock_exists.return_value = True
    
    # Mock API
    mock_api = MagicMock()
    mock_api.submit_assignment.return_value = {"id": 789, "status": "submitted"}
    mock_get_api.return_value = mock_api
    
    # Execute
    handle_push(ctx, None, None, None)
    
    # Assert
    mock_api.submit_assignment.assert_called_once_with(123, 456, "file.py")

@patch('handlers.push_handler.get_key')
@patch('handlers.push_handler.get_api')
@patch('handlers.push_handler.os.path.exists')
def test_handle_push_with_explicit_params(mock_exists, mock_get_api, mock_get_key):
    """Test handle_push with explicitly provided parameters"""
    # Setup
    ctx = MagicMock()
    explicit_course_id = 111
    explicit_assignment_id = 222
    explicit_file = "explicit.py"
    
    # Mock exists
    mock_exists.return_value = True
    
    # Mock API
    mock_api = MagicMock()
    mock_get_api.return_value = mock_api
    
    # Execute
    handle_push(ctx, explicit_course_id, explicit_assignment_id, explicit_file)
    
    # Assert - get_key should still be called to get values
    assert mock_get_key.call_count == 3
    
    # If get_key was implemented to use passed values, the explicit values would be used
    # This test ensures we're calling get_key which would handle the precedence logic