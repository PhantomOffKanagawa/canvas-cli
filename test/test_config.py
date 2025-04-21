"""
Tests for the config module
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from test_base import CanvasCliTestCase
from canvas_cli.config import Config

class ConfigTests(CanvasCliTestCase):
    """Tests for the Config class"""
    
    def setUp(self):
        """Set up test environment"""
        super().setUp()
        
        # Create temporary directory for test configs
        self.temp_dir = tempfile.mkdtemp()
        self.temp_global_config = Path(self.temp_dir) / "config.json"
        self.temp_project_config = Path(self.temp_dir) / "canvas.json"
        
        # Save mock config to temporary file
        with open(self.temp_global_config, "w") as f:
            json.dump(self.mock_config, f)
        
        # Patch the USER_CONFIG_PATH to use our temp file
        self.global_path_patcher = patch("canvas_cli.config.USER_CONFIG_PATH", self.temp_global_config)
        self.mock_global_path = self.global_path_patcher.start()
        
    def tearDown(self):
        """Clean up test environment"""
        self.global_path_patcher.stop()
        shutil.rmtree(self.temp_dir)
    
    def test_load_global_config(self):
        """Test loading global configuration"""
        # Load the global config
        config = Config.load_global()
        
        # Verify it contains our mock data
        self.assertEqual(config["token"], self.mock_config["token"])
        self.assertEqual(config["host"], self.mock_config["host"])
    
    def test_save_global_config(self):
        """Test saving global configuration"""
        # Modify the config and save it
        updated_config = self.mock_config.copy()
        updated_config["new_key"] = "new_value"
        
        Config.save_global(updated_config)
        
        # Reload and verify changes were saved
        config = Config.load_global()
        self.assertEqual(config["new_key"], "new_value")
    
    def test_set_get_value_global(self):
        """Test setting and getting values in global config"""
        # Set a new value
        Config.set_value("test_key", "test_value", "global")
        
        # Verify it was set correctly
        value = Config.get_value("test_key", "global")
        self.assertEqual(value, "test_value")
    
    def test_unset_value_global(self):
        """Test unsetting values from global config"""
        # Set then unset a value
        Config.set_value("temp_key", "temp_value", "global")
        result = Config.unset_value("temp_key", "global")
        
        # Verify it was unset
        self.assertTrue(result)
        self.assertIsNone(Config.get_value("temp_key", "global"))
    
    def test_get_headers(self):
        """Test getting API headers"""
        # Get headers from config
        headers = Config.get_headers()
        
        # Verify header format
        self.assertEqual(headers["Authorization"], f"Bearer {self.mock_config['token']}")
    
    @patch("canvas_cli.config.Path.cwd")
    def test_load_project_config(self, mock_cwd):
        """Test loading project configuration"""
        # Create a project config in our temp directory
        project_config = {"course_id": "12345", "assignment_id": "67890", "default_upload": "test.py"}
        with open(self.temp_project_config, "w") as f:
            json.dump(project_config, f)
        
        # Mock the current working directory to our temp dir
        mock_cwd.return_value = Path(self.temp_dir)
        
        # Load the project config
        config = Config.load_project_config()
        
        # Verify it contains our project data
        self.assertEqual(config["course_id"], project_config["course_id"])
        self.assertEqual(config["assignment_id"], project_config["assignment_id"])
    
    @patch("canvas_cli.config.Path.cwd")
    def test_save_project_config(self, mock_cwd):
        """Test saving project configuration"""
        # Mock the current working directory to our temp dir
        mock_cwd.return_value = Path(self.temp_dir)
        
        # Save a project config
        project_config = {"course_id": "12345", "assignment_id": "67890"}
        Config.save_project_config(project_config)
        
        # Verify file was created with correct content
        with open(self.temp_project_config, "r") as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config["course_id"], project_config["course_id"])
        self.assertEqual(saved_config["assignment_id"], project_config["assignment_id"])

    def test_get_values_returns_first_non_none(self):
        """Test get_values returns first non-None value from scopes"""
        Config.set_value("multi_key", "global_val", "global")
        with patch("canvas_cli.config.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path(self.temp_dir)
            Config.set_value("multi_key", "local_val", "local")
            # Should return local first
            val = Config.get_value("multi_key", ["local", "global"])
            self.assertEqual(val, "local_val")
            # Remove local, should return global
            Config.unset_value("multi_key", "local")
            val2 = Config.get_value("multi_key", ["local", "global"])
            self.assertEqual(val2, "global_val")

    def test_get_values_returns_none_if_not_found(self):
        """Test get_values returns None if key not found in any scope"""
        val = Config.get_value("notfound", ["local", "global"])
        self.assertIsNone(val)
        
if __name__ == "__main__":
    import unittest
    unittest.main()
