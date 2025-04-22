"""
Tests for the API module
"""

import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from test_base import CanvasCliTestCase
from canvas_cli.api import CanvasAPI, format_date, download_file, submit_assignment

class APITests(CanvasCliTestCase):
    """Tests for the CanvasAPI class"""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        
        # Create patcher for Config.load_global
        self.config_patcher = patch("canvas_cli.api.Config.load_global", return_value=self.mock_config)
        self.mock_config_load = self.config_patcher.start()
        
        # Create patcher for requests.get
        self.requests_get_patcher = patch("canvas_cli.api.requests.get")
        self.mock_requests_get = self.requests_get_patcher.start()
        
        # Create patcher for requests.post
        self.requests_post_patcher = patch("canvas_cli.api.requests.post")
        self.mock_requests_post = self.requests_post_patcher.start()
        
    def tearDown(self):
        """Clean up test environment"""
        self.config_patcher.stop()
        self.requests_get_patcher.stop()
        self.requests_post_patcher.stop()
    
    def test_init(self):
        """Test initializing the API client"""
        # Create API client
        api = CanvasAPI()
        
        # Verify it was initialized correctly
        self.assertEqual(api.token, self.mock_config["token"])
        self.assertEqual(api.host, self.mock_config["host"])
        self.assertEqual(api.base_url, f"https://{self.mock_config['host']}/api/v1")
        self.assertEqual(api.headers["Authorization"], f"Bearer {self.mock_config['token']}")
    
    def test_get_courses(self):
        """Test getting courses from the API"""
        # Mock the response
        self.mock_requests_get.return_value = self._mock_api_response(json_data=self.mock_courses)
        
        # Create API client and get courses
        api = CanvasAPI()
        courses = api.get_courses()
        
        # Verify the correct endpoint was called
        self.mock_requests_get.assert_called_once()
        args, kwargs = self.mock_requests_get.call_args
        self.assertEqual(args[0], f"https://{self.mock_config['host']}/api/v1/courses")
        
        # Verify we got the courses
        self.assertEqual(len(courses), len(self.mock_courses))
        self.assertEqual(courses[0]["id"], self.mock_courses[0]["id"])
        self.assertEqual(courses[1]["name"], self.mock_courses[1]["name"])
    
    def test_get_assignments(self):
        """Test getting assignments from the API"""
        # Mock the response
        self.mock_requests_get.return_value = self._mock_api_response(json_data=self.mock_assignments)
        
        # Create API client and get assignments
        api = CanvasAPI()
        course_id = 12345
        assignments = api.get_assignments(course_id)
        
        # Verify the correct endpoint was called
        self.mock_requests_get.assert_called_once()
        args, kwargs = self.mock_requests_get.call_args
        self.assertEqual(args[0], f"https://{self.mock_config['host']}/api/v1/courses/{course_id}/assignments")
        
        # Verify we got the assignments
        self.assertEqual(len(assignments), len(self.mock_assignments))
        for i, assignment in enumerate(assignments):
            self.assertIn("id", assignment)
            self.assertIn("name", assignment)
            self.assertEqual(assignment["id"], self.mock_assignments[i]["id"])
    
    def test_get_course_details(self):
        """Test getting course details from the API"""
        # Mock the response
        self.mock_requests_get.return_value = self._mock_api_response(json_data=self.mock_course_details)
        
        # Create API client and get course details
        api = CanvasAPI()
        course_id = 12345
        course = api.get_course_details(course_id)
        
        # Verify the correct endpoint was called
        self.mock_requests_get.assert_called_once()
        args, kwargs = self.mock_requests_get.call_args
        self.assertEqual(args[0], f"https://{self.mock_config['host']}/api/v1/courses/{course_id}")
        
        # Verify we got the course details
        self.assertEqual(course["id"], self.mock_course_details["id"])
        self.assertEqual(course["name"], self.mock_course_details["name"])
    
    def test_get_assignment_details(self):
        """Test getting assignment details from the API"""
        # Mock the response
        self.mock_requests_get.return_value = self._mock_api_response(json_data=self.mock_assignment_details)
        
        # Create API client and get assignment details
        api = CanvasAPI()
        course_id = 12345
        assignment_id = 11111
        assignment = api.get_assignment_details(course_id, assignment_id)
        
        # Verify the correct endpoint was called
        self.mock_requests_get.assert_called_once()
        args, kwargs = self.mock_requests_get.call_args
        self.assertEqual(args[0], f"https://{self.mock_config['host']}/api/v1/courses/{course_id}/assignments/{assignment_id}")
        
        # Verify we got the assignment details
        self.assertEqual(assignment["id"], self.mock_assignment_details["id"])
        self.assertEqual(assignment["name"], self.mock_assignment_details["name"])
    
    @patch("canvas_cli.api.Config.get_headers")
    def test_submit_assignment(self, mock_get_headers):
        """Test submitting an assignment"""
        # Mock API responses
        session_response = {"upload_url": "https://example.com/upload", "upload_params": {"key": "value"}}
        upload_response = {"id": 99999}
        submit_response = {"id": 88888, "submission": {"id": 77777}}
        
        # Configure the mocks
        mock_get_headers.return_value = {"Authorization": f"Bearer {self.mock_config['token']}"}
        self.mock_requests_post.side_effect = [
            self._mock_api_response(json_data=session_response),
            self._mock_api_response(json_data=upload_response),
            self._mock_api_response(json_data=submit_response)
        ]
        
        # Test with a temporary file
        with patch("builtins.open", MagicMock()), \
             patch("os.path.getsize", return_value=1024), \
             patch("os.path.basename", return_value="test_file.py"):
            
            # Call the submit method
            course_id = 12345
            assignment_id = 11111
            file_path = "test_file.py"
            api = CanvasAPI()
            submit_assignment(course_id, assignment_id, file_path)
            
            # Verify the correct API endpoints were called
            self.assertEqual(self.mock_requests_post.call_count, 3)
    
    def test_format_date(self):
        """Test date formatting helper function"""
        # Test with valid date string
        date_str = "2023-12-31T23:59:59Z"
        formatted = format_date(date_str)
        self.assertEqual(formatted, "2023-12-31 23:59:59")
        
        # Test with None
        self.assertEqual(format_date(None), "No date specified")
        
        # Test with invalid format
        # This should not raise an exception
        formatted = format_date("invalid-date")
        self.assertEqual(formatted, "invalid-date")
        
    def test_download_file(self):
        """Test downloading a file"""
        test_url = "https://example.com/testfile.txt"
        test_file_path = "test_download.txt"
        test_content = b"This is test content"
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content.return_value = [test_content]
        self.mock_requests_get.return_value = mock_response
        
        # Mock open function
        mock_file = MagicMock()
        mock_open = MagicMock(return_value=mock_file)
        
        # Test with a new file (not existing)
        with patch("builtins.open", mock_open), \
                patch("os.path.exists", return_value=False):
            download_file(test_url, test_file_path)
            
            # Check that requests.get was called with the correct URL
            self.mock_requests_get.assert_called_once_with(test_url, stream=True)
            
            # Check that the file was opened for writing
            mock_open.assert_called_once_with(test_file_path, 'wb')
            
            # Check that content was written to the file
            mock_file.__enter__().write.assert_called_once_with(test_content)

    def test_download_file_existing_overwrite(self):
        """Test downloading a file with overwrite option"""
        test_url = "https://example.com/testfile.txt"
        test_file_path = "test_download.txt"
        test_content = b"New content"
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content.return_value = [test_content]
        self.mock_requests_get.return_value = mock_response
        
        # Mock open function
        mock_file = MagicMock()
        mock_open = MagicMock(return_value=mock_file)
        
        # Test with existing file and overwrite=True
        with patch("builtins.open", mock_open), \
                patch("os.path.exists", return_value=True):
            download_file(test_url, test_file_path, overwrite=True)
            
            # Check that requests.get was called with the correct URL
            self.mock_requests_get.assert_called_once_with(test_url, stream=True)
            
            # Check that the file was opened for writing
            mock_open.assert_called_once_with(test_file_path, 'wb')
            
            # Check that content was written to the file
            mock_file.__enter__().write.assert_called_once_with(test_content)

    def test_download_file_existing_no_overwrite(self):
        """Test downloading a file with no overwrite"""
        test_url = "https://example.com/testfile.txt"
        test_file_path = "test_download.txt"
        
        # Test with existing file, overwrite=False, and user says no
        with patch("os.path.exists", return_value=True), \
                patch("builtins.input", return_value="n"):
            result = download_file(test_url, test_file_path)
            
            # Check that requests.get was not called
            self.mock_requests_get.assert_not_called()
            
            # Check that function returned None
            self.assertIsNone(result)

    def test_download_file_existing_yes_overwrite(self):
        """Test downloading a file with user confirming overwrite"""
        test_url = "https://example.com/testfile.txt"
        test_file_path = "test_download.txt"
        test_content = b"This is test content"
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content.return_value = [test_content]
        self.mock_requests_get.return_value = mock_response
        
        # Mock open function
        mock_file = MagicMock()
        mock_open = MagicMock(return_value=mock_file)
        
        # Test with existing file, overwrite=False, and user says yes
        with patch("os.path.exists", return_value=True), \
                patch("builtins.input", return_value="y"), \
                patch("builtins.open", mock_open):
            download_file(test_url, test_file_path)
            
            # Check that requests.get was called with the correct URL
            self.mock_requests_get.assert_called_once_with(test_url, stream=True)
            
            # Check that the file was opened for writing
            mock_open.assert_called_once_with(test_file_path, 'wb')

if __name__ == "__main__":
    import unittest
    from unittest.mock import patch, MagicMock
    unittest.main()