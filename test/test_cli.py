"""
Tests for the CLI module
"""

import sys
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from test_base import CanvasCliTestCase
from canvas_cli.cli import config_command, init_command, push_command, status_command, help_command, main

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
    
    @patch('canvas_cli.cli.CanvasAPI')
    @patch('canvas_cli.cli.Config')
    @patch('pathlib.Path.resolve')
    def test_push_command(self, mock_resolve, mock_config, mock_api_class):
        """Test the push command"""
        # Set up args
        self.args.course_id = 12345
        self.args.assignment_id = 67890
        self.args.file = "test_file.py"
        
        # Set up mocks
        mock_resolve.return_value = Path(self.temp_dir) / "test_file.py"
        mock_api = mock_api_class.return_value
        
        # Create a test file
        test_file = Path(self.temp_dir) / "test_file.py"
        with open(test_file, "w") as f:
            f.write("print('Hello, world!')")
        
        # Call the function
        with patch('builtins.open', create=True) as mock_open:
            push_command(self.args)
        
        # Verify correct API call
        mock_api.submit_assignment.assert_called_with(12345, 67890, mock_resolve.return_value)
    
    # @patch('canvas_cli.cli.CanvasAPI')
    # def test_pull_command_basic(self, mock_api_class):
    #     """Test the pull command with basic arguments"""
    #     # Set up args
    #     self.args.course_id = 12345
    #     self.args.assignment_id = 67890
    #     self.args.tui = False
    #     self.args.output = "README.md"
    #     self.args.output_directory = "./canvas-page"
    #     self.args.force = True
    #     self.args.html = False
    #     self.args.pdf = False
    #     self.args.pages = False
    #     self.args.convert = False
    #     self.args.integrated = False
    #     self.args.delete_after = False
    #     self.args.convert_links = False
    #     self.args.download_all = False
        
    #     # Set up mocks
    #     mock_api = mock_api_class.return_value
    #     mock_api.get_assignment_details.return_value = self.mock_assignment_details
    #     mock_api.get_course_details.return_value = self.mock_course_details
        
    #     # Mock Path.exists and open
    #     with patch('pathlib.Path.exists', return_value=False), \
    #          patch('builtins.open', create=True), \
    #          patch('canvas_cli.cli.markdownify', return_value="Converted Markdown"):
            
    #         # Call the function
    #         pull_command(self.args)
        
    #     # Verify API calls
    #     mock_api.get_assignment_details.assert_called_with(12345, 67890)
    #     mock_api.get_course_details.assert_called_with(12345)
    
    # @patch('canvas_cli.cli.CanvasAPI')
    # def test_pull_command_with_convert_links(self, mock_api_class):
    #     """Test the pull command with convert_links option"""
    #     # Set up args
    #     self.args.course_id = 12345
    #     self.args.assignment_id = 67890
    #     self.args.tui = False
    #     self.args.output = "README.md"
    #     self.args.output_directory = "./canvas-page"
    #     self.args.force = True
    #     self.args.html = False
    #     self.args.pdf = False
    #     self.args.pages = False
    #     self.args.convert = False
    #     self.args.integrated = False
    #     self.args.delete_after = False
    #     self.args.convert_links = True
    #     self.args.download_all = False
        
    #     # Set up mocks
    #     mock_api = mock_api_class.return_value
    #     assignment_with_links = self.mock_assignment_details.copy()
    #     assignment_with_links["description"] = """<p>Assignment with links:</p>
    #     <a href="https://mockcanvas.edu/courses/12345/files/99999?verifier=abcdef&amp;wrap=1">Download file</a>"""
        
    #     mock_api.get_assignment_details.return_value = assignment_with_links
    #     mock_api.get_course_details.return_value = self.mock_course_details
        
    #     # Mock necessary functions and modules
    #     with patch('pathlib.Path.exists', return_value=False), \
    #          patch('builtins.open', create=True), \
    #          patch('canvas_cli.cli.markdownify', return_value="Converted Markdown"), \
    #          patch('canvas_cli.cli.Config.get_value', return_value="mockcanvas.edu"), \
    #          patch('re.findall', return_value=[("https://mockcanvas.edu/courses/12345/files/99999?verifier=abcdef&amp;wrap=1", "Download file")]), \
    #          patch('re.match', return_value=MagicMock(groups=lambda: ["https://mockcanvas.edu/courses/12345/files/99999", "abcdef"])), \
    #          patch('re.search', return_value=MagicMock(group=lambda: '<a href="https://mockcanvas.edu/courses/12345/files/99999?verifier=abcdef&amp;wrap=1">Download file</a>')):
             
    #         # Call the function
    #         pull_command(self.args)
        
    #     # Check that output contains indication of conversion
    #     output = self.mock_stdout.getvalue()
    #     self.assertIn("Converting Canvas file links", output)
    
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
    
    @patch('canvas_cli.cli.parse_args_and_dispatch')
    def test_main(self, mock_parse):
        """Test the main function"""
        # Call the function
        main()
        
        # Verify args parsing function was called
        mock_parse.assert_called_once()
        call_args = mock_parse.call_args[0][0]
        self.assertIn("config", call_args)
        self.assertIn("init", call_args)
        self.assertIn("push", call_args)
        self.assertIn("status", call_args)
        self.assertIn("help", call_args)

if __name__ == "__main__":
    import unittest
    unittest.main()
