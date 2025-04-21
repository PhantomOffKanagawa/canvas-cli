"""
Tests for the args module
"""

import sys
from unittest.mock import patch, MagicMock

from test_base import CanvasCliTestCase
from canvas_cli.args import create_parser, parse_args_and_dispatch

class ArgsTests(CanvasCliTestCase):
    """Tests for the args module"""
    
    def test_create_parser(self):
        """Test creating the argument parser"""
        # Create parser
        parser = create_parser()
        
        # Verify it contains the expected commands
        subparsers = [action for action in parser._actions 
                     if action.dest == 'command'][0]
        choices = subparsers.choices
        
        # Check for required commands
        self.assertIn('config', choices)
        self.assertIn('init', choices)
        self.assertIn('push', choices)
        # self.assertIn('pull', choices)
        self.assertIn('status', choices)
    
    def test_config_parser(self):
        """Test the config command parser"""
        # Create parser
        parser = create_parser()
        
        # Test with list subcommand
        with patch('sys.argv', ['canvas', 'config', 'list', '--global']):
            args = parser.parse_args()
            self.assertEqual(args.command, 'config')
            self.assertEqual(args.config_command, 'list')
            self.assertEqual(args.scope, 'global')
        
        # Test with get subcommand
        with patch('sys.argv', ['canvas', 'config', 'get', 'token', '--global']):
            args = parser.parse_args()
            self.assertEqual(args.command, 'config')
            self.assertEqual(args.config_command, 'get')
            self.assertEqual(args.name, 'token')
            self.assertEqual(args.scope, 'global')
        
        # Test with set subcommand
        with patch('sys.argv', ['canvas', 'config', 'set', 'host', 'canvas.example.com', '--global']):
            args = parser.parse_args()
            self.assertEqual(args.command, 'config')
            self.assertEqual(args.config_command, 'set')
            self.assertEqual(args.name, 'host')
            self.assertEqual(args.value, 'canvas.example.com')
            self.assertEqual(args.scope, 'global')
    
    def test_init_parser(self):
        """Test the init command parser"""
        # Create parser
        parser = create_parser()
        
        # Test with all arguments
        with patch('sys.argv', [
            'canvas', 'init', 
            '-cid', '12345', 
            '-aid', '67890',
            '-cn', 'Test Course',
            '-an', 'Test Assignment',
            '-f', 'test.py',
            '-t'
        ]):
            args = parser.parse_args()
            self.assertEqual(args.command, 'init')
            self.assertEqual(args.course_id, '12345')
            self.assertEqual(args.assignment_id, '67890')
            self.assertEqual(args.course_name, 'Test Course')
            self.assertEqual(args.assignment_name, 'Test Assignment')
            self.assertEqual(args.file, 'test.py')
            self.assertTrue(args.tui)
    
    def test_push_parser(self):
        """Test the push command parser"""
        # Create parser
        parser = create_parser()
        
        # Test with all arguments
        with patch('sys.argv', [
            'canvas', 'push',
            '-cid', '12345',
            '-aid', '67890',
            '-f', 'test.py'
        ]):
            args = parser.parse_args()
            self.assertEqual(args.command, 'push')
            self.assertEqual(args.course_id, 12345)
            self.assertEqual(args.assignment_id, 67890)
            self.assertEqual(args.file, 'test.py')
    
    # def test_pull_parser(self):
    #     """Test the pull command parser"""
    #     # Create parser
    #     parser = create_parser()
        
    #     # Test with basic arguments
    #     with patch('sys.argv', [
    #         'canvas', 'pull',
    #         '-cid', '12345',
    #         '-aid', '67890'
    #     ]):
    #         args = parser.parse_args()
    #         self.assertEqual(args.command, 'pull')
    #         self.assertEqual(args.course_id, 12345)
    #         self.assertEqual(args.assignment_id, 67890)
    #         self.assertEqual(args.output, 'README.md')  # Default value
        
    #     # Test with all arguments
    #     with patch('sys.argv', [
    #         'canvas', 'pull',
    #         '-cid', '12345',
    #         '-aid', '67890',
    #         '-o', 'custom.md',
    #         '-od', './downloads',
    #         '-f',
    #         '-html',
    #         '-pdf',
    #         '-cdl',
    #         '-dla'
    #     ]):
    #         args = parser.parse_args()
    #         self.assertEqual(args.output, 'custom.md')
    #         self.assertEqual(args.output_directory, './downloads')
    #         self.assertTrue(args.force)
    #         self.assertTrue(args.html)
    #         self.assertTrue(args.pdf)
    #         self.assertTrue(args.convert_links)
    #         self.assertTrue(args.download_all)
    
    def test_status_parser(self):
        """Test the status command parser"""
        # Create parser
        parser = create_parser()
        
        # Test with basic arguments
        with patch('sys.argv', [
            'canvas', 'status',
            '-cid', '12345',
            '-aid', '67890'
        ]):
            args = parser.parse_args()
            self.assertEqual(args.command, 'status')
            self.assertEqual(args.course_id, 12345)
            self.assertEqual(args.assignment_id, 67890)
        
        # Test with global view
        with patch('sys.argv', ['canvas', 'status', 'all']):
            args = parser.parse_args()
            self.assertEqual(args.global_view, 'all')
    
    def test_parse_args_and_dispatch(self):
        """Test parsing arguments and dispatching to handler functions"""
        # Create mock handler functions
        mock_handlers = {
            'config': MagicMock(),
            'init': MagicMock(),
            'push': MagicMock(),
            'status': MagicMock()
        }
        
        # Test with config command
        with patch('sys.argv', ['canvas', 'config', 'list']):
            parse_args_and_dispatch(mock_handlers)
            mock_handlers['config'].assert_called_once()
            mock_handlers['init'].assert_not_called()
        
        # Reset mocks
        for mock in mock_handlers.values():
            mock.reset_mock()
        
        # Test with init command
        with patch('sys.argv', ['canvas', 'init']):
            parse_args_and_dispatch(mock_handlers)
            mock_handlers['config'].assert_not_called()
            mock_handlers['init'].assert_called_once()

if __name__ == "__main__":
    import unittest
    unittest.main()
