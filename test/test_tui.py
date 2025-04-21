"""
Tests for the TUI module
"""

from pathlib import Path
from random import randint
import sys
from unittest.mock import ANY, patch, MagicMock, call

from test_base import CanvasCliTestCase
from canvas_cli.tui import run_tui, select_file, select_from_options

class TUITests(CanvasCliTestCase):
    """Tests for the TUI module"""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        
        # Patch CURSES_AVAILABLE
        self.curses_patcher = patch('canvas_cli.tui.CURSES_AVAILABLE', True)
        self.mock_curses_available = self.curses_patcher.start()
        
        # Mock API client and responses
        self.api_patcher = patch('canvas_cli.tui.CanvasAPI')
        self.mock_api_class = self.api_patcher.start()
        self.mock_api = self.mock_api_class.return_value
        self.mock_api.get_courses.return_value = self.mock_courses
        self.mock_api.get_assignments.return_value = self.mock_assignments
        
        # Mock curses
        self.curses_patcher2 = patch('canvas_cli.tui.curses')
        self.mock_curses = self.curses_patcher2.start()
        
        # Mock curses wrapper function
        self.wrapper_patcher = patch('canvas_cli.tui.curses.wrapper')
        self.mock_wrapper = self.wrapper_patcher.start()
        self.mock_wrapper.return_value = (self.mock_courses[0], self.mock_assignments[0])
    
    def tearDown(self):
        """Clean up after tests"""
        self.curses_patcher.stop()
        self.api_patcher.stop()
        self.curses_patcher2.stop()
        self.wrapper_patcher.stop()
    
    def test_run_tui_with_curses(self):
        """Test running the TUI with curses available"""
        # Run TUI
        course_id, assignment_id, course_name, assignment_name = run_tui()
        
        # Verify curses wrapper was called
        self.mock_wrapper.assert_called_once()
        
        # Verify returned values match mock data
        self.assertEqual(course_id, self.mock_courses[0]['id'])
        self.assertEqual(assignment_id, self.mock_assignments[0]['id'])
        self.assertEqual(course_name, self.mock_courses[0]['name'])
        self.assertEqual(assignment_name, self.mock_assignments[0]['name'])
    
    def test_run_tui_with_fallback(self):
        """Test running the TUI with fallback option"""
        # Ensure valid mock data index
        course_count = len(self.mock_courses)
        assignment_count = len(self.mock_assignments)
        
        if course_count == 0 or assignment_count == 0:
            raise ValueError("Mock data for courses or assignments is empty")
        
        checked_course_index = 0 if course_count > 1 else 0
        checked_assignment_index = 1 if assignment_count > 2 else 0

        # Mock the text-based interface
        with patch('canvas_cli.tui.text_select_course_and_assignment') as mock_text_select:
            mock_text_select.return_value = (self.mock_courses[checked_course_index], self.mock_assignments[checked_assignment_index])
            
            # Run TUI with fallback
            course_id, assignment_id, course_name, assignment_name = run_tui(fallback=True)
            
            # Verify text interface was used
            mock_text_select.assert_called_once()
            
            # Verify returned values match mock data
            self.assertEqual(course_id, self.mock_courses[checked_course_index]['id'])
            self.assertEqual(assignment_id, self.mock_assignments[checked_assignment_index]['id'])
            self.assertEqual(course_name, self.mock_courses[checked_course_index]['name'])
            self.assertEqual(assignment_name, self.mock_assignments[checked_assignment_index]['name'])
    
    def test_run_tui_curses_not_available(self):
        """Test running the TUI when curses is not available"""
        # Mock curses as not available
        self.mock_curses_available = False
        with patch('canvas_cli.tui.CURSES_AVAILABLE', False), \
             patch('canvas_cli.tui.text_select_course_and_assignment') as mock_text_select:
            mock_text_select.return_value = (self.mock_courses[0], self.mock_assignments[0])
            
            # Run TUI
            course_id, assignment_id, course_name, assignment_name = run_tui()
            
            # Verify text interface was used
            mock_text_select.assert_called_once()
            
            # Verify returned values
            self.assertEqual(course_id, self.mock_courses[0]['id'])
            self.assertEqual(assignment_id, self.mock_assignments[0]['id'])
    
    def test_text_select_course_and_assignment(self):
        """Test the text-based selection interface"""
        # Mock the input function to simulate user selections
        with patch('builtins.input', side_effect=['1', '1']), \
             patch('canvas_cli.tui.text_select_course_and_assignment') as mock_text_select:
            mock_text_select.return_value = (self.mock_courses[0], self.mock_assignments[0])
            
            # Run TUI with fallback
            course_id, assignment_id, course_name, assignment_name = run_tui(fallback=True)
            
            # Verify correct selections
            self.assertEqual(course_id, self.mock_courses[0]['id'])
            self.assertEqual(assignment_id, self.mock_assignments[0]['id'])
    
    def test_run_tui_cancelled(self):
        """Test running the TUI when selection is cancelled"""
        # Mock the wrapper to return None values (cancelled selection)
        self.mock_wrapper.return_value = (None, None)
        
        # Run TUI
        course_id, assignment_id, course_name, assignment_name = run_tui()
        
        # Verify all returned values are None
        self.assertIsNone(course_id)
        self.assertIsNone(assignment_id)
        self.assertIsNone(course_name)
        self.assertIsNone(assignment_name)
    
    def test_run_tui_error(self):
        """Test running the TUI when an error occurs"""
        # Mock the wrapper to raise an exception
        self.mock_wrapper.side_effect = Exception("Test error")
        
        # Run TUI
        with patch('builtins.print') as mock_print:
            course_id, assignment_id, course_name, assignment_name = run_tui()
            
            # Verify error was printed
            mock_print.assert_any_call("An error occurred: Test error")
        
        # Verify all returned values are None
        self.assertIsNone(course_id)
        self.assertIsNone(assignment_id)
        self.assertIsNone(course_name) 
        self.assertIsNone(assignment_name)
        
    def test_select_from_options_curses(self):
        """Test select_from_options with curses available"""
        # Patch CURSES_AVAILABLE to True and patch curses.wrapper
        with patch('canvas_cli.tui.CURSES_AVAILABLE', True), \
                patch('canvas_cli.tui.curses.wrapper') as mock_wrapper:
            # Prepare mock options
            options = [
                {'id': 1, 'label': 'Option 1'},
                {'id': 2, 'label': 'Option 2'},
            ]
            # Simulate user selecting the first option
            mock_wrapper.return_value = options[0]
            result = select_from_options(options, label_key='label', title="Test Options")
            self.assertEqual(result, options[0])
            mock_wrapper.assert_called_once()

    def test_select_from_options_text_fallback(self):
        """Test select_from_options with fallback to text interface"""
        # Patch CURSES_AVAILABLE to False and patch select_from_list
        with patch('canvas_cli.tui.CURSES_AVAILABLE', False), \
                patch('canvas_cli.tui.select_from_list') as mock_select_from_list:
            options = [
                {'id': 1, 'label': 'Option 1'},
                {'id': 2, 'label': 'Option 2'},
            ]
            mock_select_from_list.return_value = options[1]
            result = select_from_options(options, label_key='label', title="Test Options")
            self.assertEqual(result, options[1])
            mock_select_from_list.assert_called_once_with(options, ANY, "Test Options")

    def test_select_from_options_empty(self):
        """Test select_from_options with empty options list"""
        with patch('builtins.print') as mock_print:
            result = select_from_options([], label_key='label', title="Empty Options")
            self.assertIsNone(result)
            mock_print.assert_any_call("No options available.")

    def test_select_from_options_exception(self):
        """Test select_from_options handles exceptions gracefully"""
        # Patch CURSES_AVAILABLE to True and patch curses.wrapper to raise
        with patch('canvas_cli.tui.CURSES_AVAILABLE', True), \
                patch('canvas_cli.tui.curses.wrapper', side_effect=Exception("Boom")), \
                patch('builtins.print') as mock_print:
            options = [{'id': 1, 'label': 'Option 1'}]
            result = select_from_options(options, label_key='label', title="Test Options")
            self.assertIsNone(result)
            mock_print.assert_any_call("Error during selection: Boom")
            
if __name__ == "__main__":
    import unittest
    unittest.main()
