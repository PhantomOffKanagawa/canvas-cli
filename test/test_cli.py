"""
Tests for the CLI module
"""

import io
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from test_base import CanvasCliTestCase
from canvas_cli.cli import config_command, init_command, pull_command, push_command, status_command, help_command, main

class CLITests(CanvasCliTestCase):
    """
    Test suite for the Canvas CLI module.
    This class contains unit tests for the main CLI commands, including:
    - config (list, get, set)
    - init
    - push
    - status (local and global)
    - help
    - main entrypoint
    Each test sets up the necessary mocks and arguments to simulate CLI usage and verifies correct behavior, output, and interactions with configuration and API classes. The tests ensure that command-line arguments are handled properly, configuration is read and written as expected, and API calls are made with the correct parameters.
    """
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Patch stdout to capture printed output
        self.stdout_patcher = patch('sys.stdout', new_callable=io.StringIO)
        self.mock_stdout = self.stdout_patcher.start()
        
        # Create mock arguments object for commands
        self.args = MagicMock()
    
    def tearDown(self):
        """Clean up after tests"""
        self.stdout_patcher.stop()
    
    @patch('canvas_cli.cli.Config')
    def test_config_command_list(self, mock_config):
        """Test the config command with list subcommand"""
        # Set up args
        self.args.config_command = "list"
        self.args.scope = "global"
        self.args.name_only = False
        
        # Set up mock config
        mock_config.load_global.return_value = self.mock_config
        
        # Call the function
        config_command(self.args)
        
        # Verify correct output
        output = self.mock_stdout.getvalue()
        self.assertIn("token", output)
        self.assertIn("host", output)
        self.assertIn(self.mock_config["token"], output)
        self.assertIn(self.mock_config["host"], output)
    
    @patch('canvas_cli.cli.Config')
    def test_config_command_get(self, mock_config):
        """Test the config command with get subcommand"""
        # Set up args
        self.args.config_command = "get"
        self.args.scope = "global"
        self.args.name = "token"
        self.args.name_only = False
        
        # Set up mock config
        mock_config.get_value.return_value = self.mock_config["token"]
        
        # Call the function
        config_command(self.args)
        
        # Verify correct output and method calls
        mock_config.get_value.assert_called_with("token", "global")
        output = self.mock_stdout.getvalue()
        self.assertIn("token", output)
        self.assertIn(self.mock_config["token"], output)
    
    @patch('canvas_cli.cli.Config')
    def test_config_command_set(self, mock_config):
        """Test the config command with set subcommand"""
        # Set up args
        self.args.config_command = "set"
        self.args.scope = "global"
        self.args.name = "new_key"
        self.args.value = "new_value"
        
        # Call the function
        config_command(self.args)
        
        # Verify correct method calls
        mock_config.set_value.assert_called_with("new_key", "new_value", "global")
    
    @patch('canvas_cli.cli.input', side_effect=["Test Assignment", "Test Course", "12345", "67890", "test_file.py", "yes"])
    @patch('canvas_cli.cli.Config')
    def test_init_command(self, mock_config, mock_input):
        """Test the init command"""
        # Set up args
        self.args.tui = False
        self.args.assignment_name = None
        self.args.course_name = None
        self.args.assignment_id = None
        self.args.course_id = None
        self.args.file = None
        
        # Set up mocks
        mock_config.load_project_config.return_value = {}
        
        # Call the function
        with patch('pathlib.Path.cwd', return_value=Path(self.temp_dir)):
            init_command(self.args)
        
        # Verify correct method calls
        mock_config.save_project_config.assert_called_once()
        args, kwargs = mock_config.save_project_config.call_args
        config = args[0]
        self.assertEqual(config["assignment_name"], "Test Assignment")
        self.assertEqual(config["course_name"], "Test Course")
        self.assertEqual(config["assignment_id"], "12345")
        self.assertEqual(config["course_id"], "67890")
        self.assertEqual(config["default_upload"], "test_file.py")
    
    @patch('canvas_cli.cli.submit_assignment')  # Patch directly where it's imported in cli.py
    @patch('canvas_cli.cli.Config')
    @patch('pathlib.Path.resolve')
    def test_push_command(self, mock_resolve, mock_config, mock_submit_assignment):
        """Test the push command"""
        # Set up args
        self.args.course_id = 12345
        self.args.assignment_id = 67890
        self.args.file = "test_file.py"
        
        # Set up mocks
        mock_resolve.return_value = Path(self.temp_dir) / "test_file.py"
        
        # Create a test file
        test_file = Path(self.temp_dir) / "test_file.py"
        with open(test_file, "w") as f:
            f.write("print('Hello, world!')")
        
        # Call the function
        push_command(self.args)
        
        # Verify correct API call
        mock_submit_assignment.assert_called_with(12345, 67890, mock_resolve.return_value)
        
    
    @patch('canvas_cli.cli.CanvasAPI')
    def test_status_command(self, mock_api_class):
        """Test the status command"""
        # Set up args
        self.args.global_view = None
        self.args.course_id = 12345
        self.args.assignment_id = 67890
        self.args.tui = False
        
        # Set up mocks
        mock_api = mock_api_class.return_value
        
        # Call the function with mocked show_local_status
        with patch('canvas_cli.cli.show_local_status') as mock_show_status:
            status_command(self.args)
            mock_show_status.assert_called_with(self.args, mock_api, 12345, 67890)
    
    @patch('canvas_cli.cli.show_global_status')
    @patch('canvas_cli.cli.CanvasAPI')
    def test_status_command_global(self, mock_api_class, mock_show_global):
        """Test the status command with global view"""
        # Set up args
        self.args.global_view = "all"
        
        # Call the function
        status_command(self.args)
        
        # Verify correct function was called
        mock_show_global.assert_called_with(mock_api_class.return_value, self.args)
    
    def test_help_command(self):
        """Test the help command"""
        # Set up args
        self.args.help_command = None
        
        # Call the function
        help_command(self.args)
        
        # Check output contains command descriptions
        output = self.mock_stdout.getvalue()
        self.assertIn("config", output)
        self.assertIn("init", output)
        self.assertIn("push", output)
        self.assertIn("status", output)
        
    @patch('canvas_cli.cli.select_from_options')
    @patch('canvas_cli.cli.download_file')
    @patch('canvas_cli.cli.CanvasAPI')
    @patch('canvas_cli.cli.Path')
    def test_pull_command_latest_download(self, mock_path, mock_api_class, mock_download_file, mock_select_from_options):
        # Setup args
        args = MagicMock()
        args.course_id = 123
        args.assignment_id = 456
        args.download_latest = True
        args.output_directory = "output"
        args.overwrite_file = True

        # Setup mocks
        mock_api = mock_api_class.return_value
        attachments = [
            {"url": "http://file.url/1", "filename": "file1.txt", "display_name": "file1.txt"},
            {"url": "http://file.url/2", "filename": "file2.txt", "display_name": "file2.txt"}
        ]
        submission = {"attachments": attachments}
        submissions_resp = {
            "submission_history": [submission],
            "assignment": {"points_possible": "100"}
        }
        mock_api.get_submissions.return_value = submissions_resp
        mock_path.cwd.return_value.joinpath.return_value.resolve.return_value = "/abs/output"

        # Call function
        pull_command(args)

        # Assert download_file called for each attachment
        expected_calls = [
            ((a["url"], os.path.join("/abs/output", a["filename"])),)
            for a in attachments
        ]
        # Compare only the first two arguments of each call
        actual_calls = [tuple(call.args[:2]) for call in mock_download_file.call_args_list]
        for expected, actual in zip(expected_calls, actual_calls):
            # expected is a tuple of one tuple, so flatten
            assert expected[0] == actual

    @patch('canvas_cli.cli.select_from_options')
    @patch('canvas_cli.cli.download_file')
    @patch('canvas_cli.cli.CanvasAPI')
    @patch('canvas_cli.cli.Path')
    def test_pull_command_select_submission(self, mock_path, mock_api_class, mock_download_file, mock_select_from_options):
        # Setup args
        args = MagicMock()
        args.course_id = 123
        args.assignment_id = 456
        args.download_latest = False
        args.output_directory = "output"
        args.overwrite_file = False

        # Setup mocks
        mock_api = mock_api_class.return_value
        attachments1 = [{"url": "http://file.url/1", "filename": "file1.txt", "display_name": "file1.txt"}]
        attachments2 = [{"url": "http://file.url/2", "filename": "file2.txt", "display_name": "file2.txt"}]
        submission1 = {"attachments": attachments1, "submitted_at": "2024-01-01T00:00:00Z", "submission_type": "online_upload", "score": "90"}
        submission2 = {"attachments": attachments2, "submitted_at": "2024-01-02T00:00:00Z", "submission_type": "online_upload", "score": "100"}
        submissions_resp = {
            "submission_history": [submission1, submission2],
            "assignment": {"points_possible": "100"}
        }
        mock_api.get_submissions.return_value = submissions_resp
        mock_path.cwd.return_value.joinpath.return_value.resolve.return_value = "/abs/output"
        mock_select_from_options.return_value = submission2

        # Call function
        pull_command(args)

        # Assert download_file called for the selected submission's attachment
        mock_download_file.assert_called_once_with(
            "http://file.url/2", os.path.join("/abs/output", "file2.txt"), overwrite=False
        )

    @patch('canvas_cli.cli.CanvasAPI')
    def test_pull_command_no_submissions(self, mock_api_class):
        args = MagicMock()
        args.course_id = 123
        args.assignment_id = 456
        args.download_latest = True
        args.output_directory = "output"
        args.overwrite_file = True

        mock_api = mock_api_class.return_value
        mock_api.get_submissions.return_value = None

        pull_command(args)
        output = self.mock_stdout.getvalue()
        self.assertIn("No submissions found for assignment", output)
        
    @patch('canvas_cli.cli.CanvasAPI')
    def test_pull_command_missing_args(self, mock_api_class):
            args = MagicMock()
            args.course_id = None
            args.assignment_id = None
            args.download_latest = True
            args.output_directory = "output"
            args.overwrite_file = True

            # Ensure get_submissions returns None, not a MagicMock
            mock_api_class.return_value.get_submissions.return_value = None

            # Patch Path.cwd to a temp directory to avoid accessing the real cwd
            with patch('pathlib.Path.cwd', return_value=Path(self.temp_dir)):
                pull_command(args)
            output = self.mock_stdout.getvalue()
            self.assertIn("Please provide all requirements", output)

    @patch('canvas_cli.cli.CanvasAPI')
    def test_pull_command_api_error(self, mock_api_class):
        args = MagicMock()
        args.course_id = 123
        args.assignment_id = 456
        args.download_latest = True
        args.output_directory = "output"
        args.overwrite_file = True

        mock_api_class.side_effect = ValueError("API error")

        pull_command(args)
        output = self.mock_stdout.getvalue()
        self.assertIn("Error: API error", output)

    @patch('canvas_cli.cli.CanvasAPI')
    def test_pull_command_empty_submission_history(self, mock_api_class):
        """Test pull command when submission history is empty"""
        args = MagicMock()
        args.course_id = 123
        args.assignment_id = 456
        args.download_latest = True
        args.output_directory = "output"
        args.overwrite_file = True

        mock_api = mock_api_class.return_value
        mock_api.get_submissions.return_value = {"submission_history": []}

        pull_command(args)
        output = self.mock_stdout.getvalue()
        self.assertIn("No submissions found for assignment", output)

    @patch('canvas_cli.cli.select_from_options')
    @patch('canvas_cli.cli.download_file')
    @patch('canvas_cli.cli.CanvasAPI')
    @patch('canvas_cli.cli.Path')
    def test_pull_command_single_submission(self, mock_path, mock_api_class, mock_download_file, mock_select_from_options):
        """Test pull command with a single submission (no selection needed)"""
        args = MagicMock()
        args.course_id = 123
        args.assignment_id = 456
        args.download_latest = False  # Even with this False, it should download the only submission
        args.output_directory = "output"
        args.overwrite_file = True

        mock_api = mock_api_class.return_value
        attachments = [{"url": "http://file.url/1", "filename": "file1.txt", "display_name": "File 1"}]
        submission = {"attachments": attachments}
        submissions_resp = {
            "submission_history": [submission],
            "assignment": {"points_possible": "100"}
        }
        mock_api.get_submissions.return_value = submissions_resp
        mock_path.cwd.return_value.joinpath.return_value.resolve.return_value = Path("/abs/output")

        pull_command(args)

        # Verify no selection was made since there's only one submission
        mock_select_from_options.assert_not_called()
        # Verify file was downloaded
        mock_download_file.assert_called_with(
            "http://file.url/1", os.path.join("/abs/output", "file1.txt"), overwrite=True
        )
        
if __name__ == "__main__":
    import unittest
    unittest.main()
