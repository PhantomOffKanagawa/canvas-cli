from _pytest import runner
import json
import pytest
from unittest.mock import MagicMock, patch, call
import typer
from canvas_cli.cli import app
from typer.testing import CliRunner
from handlers.init_handler import init_handler
from handlers.config_handler import save_config, load_config, GLOBAL_CONFIG_PATH, LOCAL_CONFIG_PATH

@pytest.fixture
def mock_context():
    return MagicMock()

def test_init_handler_new_config_with_defaults(mock_context, clean_config):
    """Test init handler with new config and provided defaults"""
    
    # Setup
    course_id = 12345
    assignment_id = 67890
    file = "homework.py"
    
    # Mock user inputs
    user_inputs = [
        "Test Course",  # Course Name
        "",             # Course ID (use default)
        "Assignment 1", # Assignment Name
        "",             # Assignment ID (use default)
        "",             # File (use default)
        "yes"           # Is this OK?
    ]
    
    with patch('builtins.input', side_effect=user_inputs), \
         patch('handlers.init_handler.get_key', side_effect=[course_id, assignment_id, file]), \
         patch('handlers.init_handler.echo') as mock_echo, \
         patch('builtins.print') as mock_print:
        
        # Execute
        init_handler(mock_context, course_id, assignment_id, file)
        
        # Assert
        mock_echo.assert_any_call(f"Configuration saved to {LOCAL_CONFIG_PATH}", ctx=mock_context)
        
        # Check the saved config
        config = load_config(LOCAL_CONFIG_PATH)
        assert config["course_name"] == "Test Course"
        assert config["course_id"] == course_id
        assert config["assignment_name"] == "Assignment 1"
        assert config["assignment_id"] == assignment_id
        assert config["file"] == file

def test_init_handler_existing_config(mock_context, clean_config):
    """Test init handler with existing config"""
    
    # Setup - create an existing config
    existing_config = {
        "course_name": "Existing Course",
        "course_id": 98765,
        "assignment_name": "Old Assignment",
        "assignment_id": 43210,
        "file": "old.py"
    }
    save_config(LOCAL_CONFIG_PATH, existing_config)
    
    # Mock user inputs
    user_inputs = [
        "",             # Course Name (keep existing)
        "12345",        # Course ID (override)
        "",             # Assignment Name (keep existing)
        "",             # Assignment ID (keep existing)
        "new.py",       # File (override)
        "yes"           # Is this OK?
    ]
    
    with patch('builtins.input', side_effect=user_inputs), \
         patch('handlers.init_handler.get_key', return_value=None), \
         patch('handlers.init_handler.echo') as mock_echo:
        
        # Execute
        init_handler(mock_context, None, None, None)
        
        # Assert
        mock_echo.assert_any_call(f"Configuration saved to {LOCAL_CONFIG_PATH}", ctx=mock_context)
        
        # Check the saved config
        config = load_config(LOCAL_CONFIG_PATH)
        assert config["course_name"] == "Existing Course"
        assert config["course_id"] == 12345  # Updated
        assert config["assignment_name"] == "Old Assignment"
        assert config["assignment_id"] == 43210
        assert config["file"] == "new.py"  # Updated
        
def test_init_handler_keyboard_interrupt(mock_context, clean_config):
    """Test init handler with keyboard interrupt"""
    
    with patch('builtins.input', side_effect=KeyboardInterrupt()), \
         patch('handlers.init_handler.echo') as mock_echo, \
         patch('handlers.init_handler.typer.Abort', Exception):  # Replace Abort with a real exception
        
        # Execute and verify it raises an exception
        with pytest.raises(Exception):
            init_handler(mock_context, None, None, None)
        
        # Verify the echo was called with the expected message
        mock_echo.assert_any_call("\n\nExiting...", ctx=mock_context)

def test_init_handler_user_aborts(mock_context, clean_config):
    """Test init handler when user aborts the configuration"""
    
    # Setup
    runner = CliRunner()
    
    # Mock user inputs, but say "no" at the confirmation
    user_inputs = [
        "Test Course",
        "12345",
        "Test Assignment",
        "67890",
        "test.py",
        "no"  # User does not confirm
    ]
    
    with patch('builtins.input', side_effect=user_inputs):
        # Execute using CLI runner to capture output
        result = runner.invoke(app, ["init"], obj=mock_context)
        
        # Assert
        assert "Aborted." in result.output
        assert not LOCAL_CONFIG_PATH.exists()

def test_init_handler_save_error(mock_context, clean_config):
    """Test init handler when there is an error saving the configuration"""
    
    user_inputs = [
        "Test Course",
        "12345",
        "Test Assignment",
        "67890",
        "test.py",
        "yes"
    ]
    
    # Create a real exception class to be raised
    class MockAbort(Exception):
        pass
    
    with patch('builtins.input', side_effect=user_inputs), \
            patch('handlers.init_handler.save_config', side_effect=Exception("Save error")), \
            patch('handlers.init_handler.echo') as mock_echo, \
            patch('typer.Abort', MockAbort):  # Replace typer.Abort with our exception
        
        # Execute with expectation to raise MockAbort
        with pytest.raises(MockAbort):
            init_handler(mock_context, None, None, None)
        
        # Verify the error message was echoed
        mock_echo.assert_any_call("Error saving configuration: Save error", ctx=mock_context)

def test_init_handler_with_empty_inputs(mock_context, clean_config):
    """Test init handler with empty inputs that should revert to defaults"""
    
    # Setup with default values
    course_id = 12345
    assignment_id = 67890
    file = "homework.py"
    
    # Mock user inputs (all empty to test default fallback)
    user_inputs = [
        "",  # Course Name (will be empty)
        "",  # Course ID (use default)
        "",  # Assignment Name (will be empty)
        "",  # Assignment ID (use default)
        "",  # File (use default)
        "yes"  # Is this OK?
    ]
    
    with patch('builtins.input', side_effect=user_inputs), \
            patch('handlers.init_handler.get_key', side_effect=[course_id, assignment_id, file]), \
            patch('handlers.init_handler.echo'), \
            patch('builtins.print'):
        
        # Execute
        init_handler(mock_context, course_id, assignment_id, file)
        
        # Check the saved config has the default values
        config = load_config(LOCAL_CONFIG_PATH)
        assert "course_name" not in config  # Should not be set when empty
        assert config["course_id"] == course_id
        assert "assignment_name" not in config  # Should not be set when empty
        assert config["assignment_id"] == assignment_id
        assert config["file"] == file
