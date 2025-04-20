"""
Base test module for Canvas CLI tests
Provides common utilities and mock data for testing
"""

import unittest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Test data directory for mock responses
TEST_DATA_DIR = Path(__file__).parent / "mock_data"

# Constants for test data
TEST_TOKEN="mock_token_12345"
TEST_HOST="test.mockcanvas.edu"

class CanvasCliTestCase(unittest.TestCase):
    """Base test case for Canvas CLI tests"""

    
    def setUp(self):
        """Set up test environment"""
        # Create test data directory if it doesn't exist
        if not TEST_DATA_DIR.exists():
            TEST_DATA_DIR.mkdir(parents=True)
        
        # Create mock config for testing
        self.mock_config = {
            "token": TEST_TOKEN,
            "host": TEST_HOST
        }
        
        # Mock API responses
        self.mock_courses = self._load_mock_data("courses.json", [
            {
                "id": 12345,
                "name": "Test Course 101",
                "course_code": "TEST101",
                "is_favorite": True
            },
            {
                "id": 67890,
                "name": "Advanced Testing 202",
                "course_code": "TEST202",
                "is_favorite": False
            }
        ])
        
        self.mock_assignments = self._load_mock_data("assignments.json", [
            {
                "id": 11111,
                "description": "<p>This is a <strong>test</strong> assignment.</p><p>Submit your work as a Python file.</p>",
                "name": "Test Assignment 1",
                "due_at": "2023-12-31T23:59:59Z",
                "has_submitted_submissions": False,
                "submission_types": ["online_upload"],
            },
            {
                "id": 22222,
                "description": "",
                "name": "Test Assignment 2",
                "due_at": "2023-11-15T23:59:59Z",
                "has_submitted_submissions": True,
                "submission_types": ["online_upload"],
                "allowed_extensions": ["pdf", "docx"]
            }
        ])
        
        self.mock_assignment_details = self._load_mock_data("assignment_details.json", {
            "id": 11111,
            "description": "<p>This is a <strong>test</strong> assignment.</p><p>Submit your work as a Python file.</p>",
            "name": "Test Assignment Details",
            "due_at": "2023-12-31T23:59:59Z",
            "has_submitted_submissions": False,
            "submission_types": ["online_upload"]
        })
        
        self.mock_course_details = self._load_mock_data("course_details.json", {
            "id": 12345,
            "name": "Test Course 101",
            "course_code": "TEST101",
        })

    def _load_mock_data(self, filename, default_data):
        """Load mock data from file or create it if it doesn't exist"""
        file_path = TEST_DATA_DIR / filename
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            # Create mock data file with provided defaults
            # Note: For more realistic data, run record_api_responses.py script
            print(f"Warning: Using default mock data for {filename}.")
            print(f"For more realistic data, run 'python test/record_api_responses.py'")
            with open(file_path, "w") as f:
                json.dump(default_data, f, indent=2)
            return default_data
    
    def _mock_api_response(self, status_code=200, json_data=None):
        """Create a mock requests.Response object"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data
        mock_response.raise_for_status = MagicMock()
        if status_code >= 400:
            mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        return mock_response
