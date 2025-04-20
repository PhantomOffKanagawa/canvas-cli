"""
Tests for the TUI utils module
"""

from unittest.mock import patch, MagicMock
from datetime import datetime

from test_base import CanvasCliTestCase
from canvas_cli.tui_utils import FuzzySearch, Formatter

class TUIUtilsTests(CanvasCliTestCase):
    """Tests for the TUI utilities"""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        
        # Sample test items
        self.course_items = [
            {
                "id": 12345,
                "name": "Introduction to Testing",
                "course_code": "TEST101",
                "is_favorite": True
            },
            {
                "id": 67890,
                "name": "Advanced Python Testing",
                "course_code": "PY302",
                "is_favorite": False
            },
            {
                "id": 54321,
                "name": "Programming with Python",
                "course_code": "CS220",
                "is_favorite": False
            }
        ]
        
        self.assignment_items = [
            {
                "id": 11111,
                "name": "Unit Test Assignment",
                "due_at": "2023-12-31T23:59:59Z",
                "has_submitted_submissions": False,
                "submission_types": ["online_upload"]
            },
            {
                "id": 22222,
                "name": "Integration Test Project",
                "due_at": "2023-11-15T23:59:59Z",
                "has_submitted_submissions": True,
                "locked_for_user": False,
                "submission_types": ["online_upload"]
            }
        ]
    
    def test_fuzzy_contains(self):
        """Test the fuzzy text matching algorithm"""
        # Test exact match
        score = FuzzySearch.fuzzy_contains("test", "test")
        self.assertGreater(score, 0)
        
        # Test substring match
        score = FuzzySearch.fuzzy_contains("testing", "test")
        self.assertGreater(score, 0)
        
        # Test non-consecutive match
        score = FuzzySearch.fuzzy_contains("texting", "test")
        self.assertGreater(score, 0)
        
        # Test non-match
        score = FuzzySearch.fuzzy_contains("abc", "xyz")
        self.assertEqual(score, 0)
        
        # Test empty strings
        self.assertEqual(FuzzySearch.fuzzy_contains("", "test"), 0)
        self.assertEqual(FuzzySearch.fuzzy_contains("test", ""), 0)
    
    def test_score_match(self):
        """Test the item matching score calculation"""
        # Test name match
        course = self.course_items[0]
        score = FuzzySearch.score_match("testing", course)
        self.assertGreater(score, 0)
        
        # Test course code match
        score = FuzzySearch.score_match("test", course)
        self.assertGreater(score, 0)
        
        # Test exact name match (should have high score)
        score = FuzzySearch.score_match("introduction to testing", course)
        self.assertGreater(score, 70)  # High priority match
        
        # Test with non-matching term
        score = FuzzySearch.score_match("nonexistent", course)
        self.assertEqual(score, 0)
    
    def test_filter_and_sort_items(self):
        """Test filtering and sorting items by search text"""
        # Test with single match term
        filtered_courses = FuzzySearch.filter_and_sort_items(self.course_items, "python")
        self.assertEqual(len(filtered_courses), 2)
        # Python courses should be first
        self.assertEqual(filtered_courses[0]["name"], "Advanced Python Testing")
        
        # Test with no matches
        filtered_courses = FuzzySearch.filter_and_sort_items(self.course_items, "nonexistent")
        self.assertEqual(len(filtered_courses), 0)
        
        # Test with empty search text (should return all items)
        filtered_courses = FuzzySearch.filter_and_sort_items(self.course_items, "")
        self.assertEqual(len(filtered_courses), len(self.course_items))
        
        # Test with multiple search terms
        filtered_courses = FuzzySearch.filter_and_sort_items(self.course_items, "python testing")
        self.assertEqual(len(filtered_courses), 1)
        self.assertEqual(filtered_courses[0]["name"], "Advanced Python Testing")
    
    def test_format_item_course(self):
        """Test formatting a course item for display"""
        # Test formatting a favorite course
        course = self.course_items[0]
        formatted = Formatter.format_item(course, "courses")
        self.assertIn(course["name"], formatted)
        self.assertIn(course["course_code"], formatted)
        self.assertIn(Formatter.ICON_FAVORITE, formatted)
        
        # Test formatting a non-favorite course
        course = self.course_items[1]
        formatted = Formatter.format_item(course, "courses")
        self.assertIn(course["name"], formatted)
        self.assertIn(course["course_code"], formatted)
        self.assertNotIn(Formatter.ICON_FAVORITE, formatted)
    
    def test_format_item_assignment(self):
        """Test formatting an assignment item for display"""
        # Test formatting a non-submitted assignment
        assignment = self.assignment_items[0]
        formatted = Formatter.format_item(assignment, "assignments")
        self.assertIn(assignment["name"], formatted)
        self.assertIn("Due:", formatted)
        self.assertNotIn(Formatter.ICON_SUBMITTED, formatted)
        
        # Test formatting a submitted assignment
        assignment = self.assignment_items[1]
        formatted = Formatter.format_item(assignment, "assignments")
        self.assertIn(assignment["name"], formatted)
        self.assertIn("Due:", formatted)
        self.assertIn(Formatter.ICON_SUBMITTED, formatted)
    
    @patch('canvas_cli.tui_utils.curses')
    def test_get_color(self, mock_curses):
        """Test getting the color for an item based on status"""
        # Mock curses color pairs
        mock_curses.color_pair.side_effect = lambda x: x
        
        # Test locked item
        item = {
            "locked_for_user": True,
            "due_at": "2023-12-31T23:59:59Z",
            "has_submitted_submissions": False
        }
        color = Formatter.get_color(item)
        self.assertEqual(color, Formatter.COLORS_LOCKED)
        
        # Test past due and submitted
        item = {
            "locked_for_user": False,
            "due_at": "2000-01-01T00:00:00Z",  # Past date
            "has_submitted_submissions": True
        }
        color = Formatter.get_color(item)
        self.assertEqual(color, Formatter.COLORS_COMPLETED)
        
        # Test past due and not submitted
        item = {
            "locked_for_user": False,
            "due_at": "2000-01-01T00:00:00Z",  # Past date
            "has_submitted_submissions": False
        }
        color = Formatter.get_color(item)
        self.assertEqual(color, Formatter.COLORS_PAST_DUE)
        
        # Test not due and submitted
        item = {
            "locked_for_user": False,
            "due_at": "2099-01-01T00:00:00Z",  # Future date
            "has_submitted_submissions": True
        }
        color = Formatter.get_color(item)
        self.assertEqual(color, Formatter.COLORS_SUBMITTED)
        
        # Test favorite
        item = {
            "locked_for_user": False,
            "due_at": "2099-01-01T00:00:00Z",  # Future date
            "has_submitted_submissions": False,
            "is_favorite": True
        }
        color = Formatter.get_color(item)
        self.assertEqual(color, Formatter.COLORS_FAVORITE)
        
        # Test normal item
        item = {
            "locked_for_user": False,
            "due_at": "2099-01-01T00:00:00Z",  # Future date
            "has_submitted_submissions": False,
            "is_favorite": False
        }
        color = Formatter.get_color(item)
        self.assertEqual(color, Formatter.COLORS_NORMAL)

if __name__ == "__main__":
    import unittest
    unittest.main()
