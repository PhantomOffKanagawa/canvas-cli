import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import typer
from typer.testing import CliRunner
from handlers.pull_handler import handle_pull
from canvas_cli.cli import app

# ──────────────────────
# HANDLE PULL TESTS
# ──────────────────────
@pytest.fixture
def mock_api():
    api = MagicMock()
    api.format_date.return_value = "2023-01-01"
    return api


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.params = {}
    return ctx


@pytest.fixture
def single_submission_response():
    return {
        "submission_history": [
            {
                "id": "12345",
                "submitted_at": "2023-01-01T12:00:00Z",
                "submission_type": "online_upload",
                "attachments": [
                    {
                        "filename": "test_file.py",
                        "display_name": "test_file.py",
                        "url": "http://example.com/test_file.py"
                    }
                ]
            }
        ],
        "assignment": {"points_possible": "100"}
    }


@pytest.fixture
def multiple_submissions_response():
    return {
        "submission_history": [
            {
                "id": "12345",
                "submitted_at": "2023-01-01T12:00:00Z",
                "submission_type": "online_upload",
                "score": "80",
                "attachments": [
                    {
                        "filename": "submission1.py",
                        "display_name": "submission1.py",
                        "url": "http://example.com/submission1.py"
                    }
                ]
            },
            {
                "id": "67890",
                "submitted_at": "2023-01-02T12:00:00Z",
                "submission_type": "online_upload",
                "score": "90",
                "attachments": [
                    {
                        "filename": "submission2.py",
                        "display_name": "submission2.py",
                        "url": "http://example.com/submission2.py"
                    }
                ]
            },
            {
                "id": "01234",
                "submitted_at": "2023-01-02T12:00:00Z",
                "submission_type": "online_upload",
                "score": "90",
                "attachments": [
                    {
                        "filename": "submission3.py",
                        "display_name": "submission3.py",
                        "url": "http://example.com/submission3.py"
                    }
                ]
            }
        ],
        "assignment": {"points_possible": "100"}
    }


def test_handle_pull_missing_parameters(mock_context, mock_api):
    """Test handling missing course_id or assignment_id"""
    with patch('handlers.pull_handler.get_key', return_value=None), \
         patch('handlers.pull_handler.get_api', return_value=mock_api), \
         patch('handlers.pull_handler.echo') as mock_echo:
        
        handle_pull(mock_context, None, None, None)
        
        mock_echo.assert_called_with(
            "Error: Missing course_id, assignment_id", 
            ctx=mock_context, 
            level="error"
        )


def test_handle_pull_no_api(mock_context):
    """Test handling when API retrieval fails"""
    with patch('handlers.pull_handler.get_key', return_value=123), \
         patch('handlers.pull_handler.get_api', return_value=None), \
         patch('handlers.pull_handler.echo') as mock_echo:
        
        handle_pull(mock_context, 123, 456, None)
        
        mock_echo.assert_called_with(
            "Error: Failed to get API instance", 
            ctx=mock_context, 
            level="error"
        )


def test_handle_pull_invalid_output_dir(mock_context, mock_api, tmp_path):
    """Test handling invalid output directory"""
    # Create a file instead of a directory to cause the error
    invalid_dir = tmp_path / "not_a_directory"
    invalid_dir.touch()
    
    with patch('handlers.pull_handler.get_key', return_value=123), \
         patch('handlers.pull_handler.get_api', return_value=mock_api), \
         patch('handlers.pull_handler.echo') as mock_echo, \
         patch('os.makedirs', side_effect=FileExistsError):
        
        with pytest.raises(typer.Exit) as excinfo:
            handle_pull(mock_context, 123, 456, str(invalid_dir))
            
        mock_echo.assert_called_with(
            f"Error: '{invalid_dir}' is not a valid directory", 
            ctx=mock_context, 
            level="error"
        )
        assert excinfo.value.exit_code == 1


def test_handle_pull_no_submissions(mock_context, mock_api):
    """Test handling when no submissions are found"""
    mock_api.get_submissions.return_value = None
    
    with patch('handlers.pull_handler.get_key', return_value=123), \
         patch('handlers.pull_handler.get_api', return_value=mock_api), \
         patch('handlers.pull_handler.echo') as mock_echo:
        
        handle_pull(mock_context, 123, 456, None)
        
        mock_echo.assert_called_with(
            "Error: No submissions found", 
            ctx=mock_context, 
            level="error"
        )


def test_handle_pull_empty_submissions(mock_context, mock_api):
    """Test handling when submissions array is empty"""
    mock_api.get_submissions.return_value = {"submission_history": []}
    
    with patch('handlers.pull_handler.get_key', return_value=123), \
         patch('handlers.pull_handler.get_api', return_value=mock_api), \
         patch('handlers.pull_handler.echo') as mock_echo:
        
        handle_pull(mock_context, 123, 456, None)
        
        mock_echo.assert_called_with(
            "Error: No submissions found", 
            ctx=mock_context, 
            level="error"
        )


def test_handle_pull_single_submission(mock_context, mock_api, single_submission_response, tmp_path):
    """Test successful handling of a single submission"""
    mock_api.get_submissions.return_value = single_submission_response
    
    with patch('handlers.pull_handler.get_key', return_value=123), \
         patch('handlers.pull_handler.get_api', return_value=mock_api), \
         patch('handlers.pull_handler.echo') as mock_echo, \
         patch('builtins.print') as mock_print:
        
        handle_pull(mock_context, 123, 456, str(tmp_path))
        
        # Check that the correct debug message was shown
        mock_echo.assert_any_call(
            "Found one submission: 12345", 
            ctx=mock_context, 
            level="debug"
        )
        
        # Check that file was downloaded
        mock_api.download_file.assert_called_with(
            "http://example.com/test_file.py", 
            os.path.join(str(tmp_path), "test_file.py"), 
            overwrite=False
        )
        
        # Check the final print statement
        mock_echo.assert_called_with(
            f"Downloaded 1 attachments from the latest submission to {str(tmp_path)}",
            ctx=mock_context,
        )


def test_handle_pull_multiple_submissions_with_selection(mock_context, mock_api, multiple_submissions_response, tmp_path):
    """Test handling multiple submissions with user selection"""
    mock_api.get_submissions.return_value = multiple_submissions_response
    mock_context.params = {'submission_number': 2}
    
    with patch('handlers.pull_handler.get_key', return_value=123), \
         patch('handlers.pull_handler.get_api', return_value=mock_api), \
         patch('handlers.pull_handler.echo') as mock_echo, \
         patch('builtins.print') as mock_print:
        
        handle_pull(mock_context, 123, 456, str(tmp_path))
        
        # Check that the selected submission was indicated
        mock_echo.assert_any_call(
            "Selected submission: 2 - Display Name: submission2.py", 
            ctx=mock_context, 
            level="debug"
        )
        
        # Check that the right file was downloaded (from the second submission)
        mock_api.download_file.assert_called_with(
            "http://example.com/submission2.py", 
            os.path.join(str(tmp_path), "submission2.py"), 
            overwrite=False
        )


@patch('typer.prompt', return_value='2')
def test_handle_pull_multiple_submissions_with_prompt(mock_prompt, mock_context, mock_api, multiple_submissions_response, tmp_path):
    """Test handling multiple submissions with prompted user selection"""
    mock_api.get_submissions.return_value = multiple_submissions_response
    mock_context.params = {}  # No pre-set

def test_handle_pull_with_positive_submission_number(mock_context, mock_api, multiple_submissions_response, tmp_path):
    """Test handling when a positive submission_number param is passed"""
    mock_api.get_submissions.return_value = multiple_submissions_response
    # User selects the first submission (index 1)
    mock_context.params = {'submission_number': 1}

    with patch('handlers.pull_handler.get_key', return_value=123), \
         patch('handlers.pull_handler.get_api', return_value=mock_api), \
         patch('handlers.pull_handler.echo') as mock_echo, \
         patch('builtins.print') as mock_print:

        handle_pull(mock_context, 123, 456, str(tmp_path))

        # Should select the first submission
        mock_echo.assert_any_call(
            "Selected submission: 1 - Display Name: submission1.py",
            ctx=mock_context,
            level="debug"
        )
        mock_api.download_file.assert_called_with(
            "http://example.com/submission1.py",
            os.path.join(str(tmp_path), "submission1.py"),
            overwrite=False
        )
        mock_echo.assert_called_with(
            f"Downloaded 1 attachments from the latest submission to {str(tmp_path)}",
            ctx=mock_context,
        )

def test_handle_pull_with_negative_submission_number(mock_context, mock_api, multiple_submissions_response, tmp_path):
    """Test handling when a negative submission_number param is passed (from the end)"""
    mock_api.get_submissions.return_value = multiple_submissions_response
    # User selects the last submission (index -1)
    mock_context.params = {'submission_number': -1}

    with patch('handlers.pull_handler.get_key', return_value=123), \
         patch('handlers.pull_handler.get_api', return_value=mock_api), \
         patch('handlers.pull_handler.echo') as mock_echo, \
         patch('builtins.print') as mock_print:

        handle_pull(mock_context, 123, 456, str(tmp_path))

        # Should select the last submission
        mock_echo.assert_any_call(
            "Selected submission: 2 - Display Name: submission2.py",
            ctx=mock_context,
            level="debug"
        )
        mock_api.download_file.assert_called_with(
            "http://example.com/submission2.py",
            os.path.join(str(tmp_path), "submission2.py"),
            overwrite=False
        )
        mock_echo.assert_called_with(
            f"Downloaded 1 attachments from the latest submission to {str(tmp_path)}",
            ctx=mock_context,
        )
        
# Test the case where the user enters 'q' to quit
@patch('typer.prompt')
def test_handle_pull_with_quit(mock_prompt, mock_context, mock_api, multiple_submissions_response):
    """Test handling when the user enters 'q' to quit"""
    mock_api.get_submissions.return_value = multiple_submissions_response
    mock_context.params = {}
    mock_prompt.return_value = 'q'
    
    with patch('handlers.pull_handler.get_key', return_value=123), \
         patch('handlers.pull_handler.get_api', return_value=mock_api), \
         patch('handlers.pull_handler.echo') as mock_echo:
        
        with pytest.raises(typer.Exit) as excinfo:
            handle_pull(mock_context, 123, 456, None)
        
        mock_echo.assert_any_call(
            "Exiting...", 
            ctx=mock_context, 
            level="info"
        )
        assert excinfo.value.exit_code == 0
        # Verify no files were downloaded
        assert not mock_api.download_file.called
        
# Test on CLI
@pytest.fixture
def multiple_submissions_fixture(monkeypatch):
    """Fixture to mock submissions data for CLI tests"""
    def mock_get_submissions(*args, **kwargs):
        return {
            "submission_history": [
                {
                    "id": "12345",
                    "submitted_at": "2023-01-01T12:00:00Z",
                    "submission_type": "online_upload",
                    "score": "80",
                    "attachments": [
                        {
                            "filename": "submission1.py",
                            "display_name": "submission1.py",
                            "url": "http://example.com/submission1.py"
                        }
                    ]
                },
                {
                    "id": "67890",
                    "submitted_at": "2023-01-02T12:00:00Z",
                    "submission_type": "online_upload",
                    "score": "90",
                    "attachments": [
                        {
                            "filename": "submission2.py",
                            "display_name": "submission2.py",
                            "url": "http://example.com/submission2.py"
                        }
                    ]
                },
                {
                    "id": "01234",
                    "submitted_at": "2023-01-03T12:00:00Z",
                    "submission_type": "online_upload",
                    "score": "95",
                    "attachments": [
                        {
                            "filename": "submission3.py",
                            "display_name": "submission3.py",
                            "url": "http://example.com/submission3.py"
                        }
                    ]
                }
            ],
            "assignment": {"points_possible": "100"}
        }
    
    # Patch the CanvasAPI.get_submissions method
    with patch('canvas_cli.api.CanvasAPI.get_submissions', side_effect=mock_get_submissions):
        # Also patch get_api to return a real API instance or mock
        with patch('canvas_cli.handler_helper.get_api', return_value=MagicMock()):
            # And ensure get_key returns proper values
            with patch('handlers.config_handler.get_key', return_value=123):
                yield

@pytest.mark.parametrize("command,expected_message", [
    (["pull", "--course-id", "123", "--assignment-id", "456", "--submission-number", "2"], "Downloaded submission2.py to "),
    (["pull", "--course-id", "123", "--assignment-id", "456", "--submission-number", "-1"], "Downloaded submission2.py to "),
    (["pull", "--course-id", "123", "--assignment-id", "456", "--submission-number", "1"], "Downloaded submission1.py to "),
    (["pull", "--course-id", "123", "--assignment-id", "456", "--submission-number", "4"], "Error: Submission number must be between -2 and 3"),
    (["pull", "--course-id", "123", "--assignment-id", "456", "--submission-number", "0"], "Downloaded submission3.py to "),
    (["pull", "--course-id", "123", "--assignment-id", "456", "--submission-number", "-4"], "Error: Submission number must be between -2 and 3"),
])
def test_handle_pull_cli(multiple_submissions_fixture, command, expected_message):
    """Test the pull command via CLI with different submission numbers"""
    
    # Use CliRunner to invoke the app
    runner = CliRunner()
    
    # Mock file downloads to prevent actual network requests
    with patch('canvas_cli.api.CanvasAPI.download_file', return_value=True):
        with patch('os.makedirs', return_value=None):
            # Simulate CLI command execution
            result = runner.invoke(app, command)
    
    # Debug output if needed
    if result.exit_code != 0:
        print(f"Exit code: {result.exit_code}")
        print(f"Exception: {result.exception}")
    
    # Check that the expected message is in the output
    assert expected_message in result.stdout