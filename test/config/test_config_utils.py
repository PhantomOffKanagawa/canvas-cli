from _pytest import runner
import json
import pytest
from unittest.mock import MagicMock, patch, call
import typer
from canvas_cli.cli import app
from typer.testing import CliRunner
from handlers.config_handler import get_cascading_config_value, get_config_path, load_config, save_config, GLOBAL_CONFIG_PATH, LOCAL_CONFIG_PATH

# ──────────────────────
# GET CASCADING CONFIG VALUE TESTS
# ──────────────────────

def test_get_cascading_config_value_with_override():
    """Test getting config value with override"""
    
    # Setup
    global_config = {"api_key": "global_key", "domain": "example.com"}
    local_config = {"api_key": "local_key", "user": "testuser"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute with override
    result = get_cascading_config_value("api_key", override="override_key")
    
    # Assert
    assert result == "override_key"

def test_get_cascading_config_value_local_priority():
    """Test getting config value from local config when it exists in both"""
    
    # Setup
    global_config = {"api_key": "global_key", "domain": "example.com"}
    local_config = {"api_key": "local_key", "user": "testuser"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute
    result = get_cascading_config_value("api_key")
    
    # Assert
    assert result == "local_key"

def test_get_cascading_config_value_fallback_to_global():
    """Test getting config value from global when it doesn't exist in local"""
    
    # Setup
    global_config = {"api_key": "global_key", "domain": "example.com"}
    local_config = {"user": "testuser"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute
    result = get_cascading_config_value("domain")
    
    # Assert
    assert result == "example.com"

def test_get_cascading_config_value_missing_key():
    """Test getting config value when key doesn't exist in either config"""
    
    # Setup
    global_config = {"api_key": "global_key", "domain": "example.com"}
    local_config = {"user": "testuser"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute
    result = get_cascading_config_value("missing_key")
    
    # Assert
    assert result is None

def test_get_cascading_config_value_no_configs():
    """Test getting config value when no configs exist"""
    
    # Setup - ensure no configs exist
    if GLOBAL_CONFIG_PATH.exists():
        GLOBAL_CONFIG_PATH.unlink()
    if LOCAL_CONFIG_PATH.exists():
        LOCAL_CONFIG_PATH.unlink()
    
    # Execute
    result = get_cascading_config_value("api_key")
    
    # Assert
    assert result is None

def test_get_cascading_config_value_empty_configs():
    """Test getting config value when configs exist but are empty"""
    
    # Setup
    save_config(GLOBAL_CONFIG_PATH, {})
    save_config(LOCAL_CONFIG_PATH, {})
    
    # Execute
    result = get_cascading_config_value("api_key")
    
    # Assert
    assert result is None

# ──────────────────────
# GET CONFIG PATH TESTS
# ──────────────────────

def test_get_config_path_global():
    """Test that get_config_path returns global path when global flag is True"""
    path = get_config_path(global_=True, local=False)
    assert path == GLOBAL_CONFIG_PATH

def test_get_config_path_local_flag():
    """Test that get_config_path returns local path when local flag is True"""
    path = get_config_path(global_=False, local=True)
    assert path == LOCAL_CONFIG_PATH

def test_get_config_path_local_exists(monkeypatch, tmp_path):
    """Test that get_config_path returns local path when it exists"""
    local_path = tmp_path / "local.json"
    local_path.touch()
    
    monkeypatch.setattr('handlers.config_handler.LOCAL_CONFIG_PATH', local_path)
    
    path = get_config_path(global_=False, local=False)
    assert path == local_path

def test_get_config_path_default():
    """Test that get_config_path returns local path by default"""
    path = get_config_path(global_=False, local=False)
    assert path == LOCAL_CONFIG_PATH

def test_get_config_path_precedence():
    """Test that global flag takes precedence over local flag when both are True"""
    path = get_config_path(global_=True, local=True)
    assert path == GLOBAL_CONFIG_PATH
    
# ──────────────────────
# LOAD CONFIG TESTS
# ──────────────────────

def test_load_config_empty_file(tmp_path):
    """Test loading config from a non-existent file returns empty dict"""
    # Use a path that doesn't exist
    non_existent_path = tmp_path / "non_existent.json"
    result = load_config(non_existent_path)
    assert result == {}

def test_load_config_with_content():
    """Test loading config from a file with content"""
    # Create a test file with content
    test_config = {"api_key": "test123", "server": "example.com"}
    save_config(GLOBAL_CONFIG_PATH, test_config)
    
    # Load the config
    result = load_config(GLOBAL_CONFIG_PATH)
    
    # Verify the content matches
    assert result == test_config
    assert result["api_key"] == "test123"
    assert result["server"] == "example.com"

def test_load_config_invalid_json(tmp_path):
    """Test loading config from a file with invalid JSON"""
    invalid_json_path = tmp_path / "invalid.json"
    
    # Create a file with invalid JSON
    with open(invalid_json_path, "w") as f:
        f.write("{This is not valid JSON")
    
    # Test that loading raises a JSONDecodeError
    with pytest.raises(json.JSONDecodeError):
        load_config(invalid_json_path)

def test_load_config_permission_error(tmp_path, monkeypatch):
    """Test loading config with permission error"""
    test_path = tmp_path / "permission_denied.json"
    
    # Create a test file
    with open(test_path, "w") as f:
        f.write('{"test": "data"}')
    
    # Mock open to raise a PermissionError
    def mock_open(*args, **kwargs):
        raise PermissionError("Permission denied")
    
    monkeypatch.setattr("builtins.open", mock_open)
    
    # Test that loading raises a PermissionError
    with pytest.raises(PermissionError):
        load_config(test_path)
        
# ──────────────────────
# SAVE CONFIG TESTS
# ──────────────────────

def test_save_config(tmp_path):
    """Test saving config to a file"""
    config_path = tmp_path / "test_config.json"
    test_config = {"api_key": "test123", "endpoint": "https://example.com"}
    
    # Save the config
    save_config(config_path, test_config)
    
    # Verify the file was created
    assert config_path.exists()
    
    # Verify the contents
    with open(config_path, "r") as f:
        saved_config = json.load(f)
    
    assert saved_config == test_config
    assert "api_key" in saved_config
    assert saved_config["api_key"] == "test123"
    assert saved_config["endpoint"] == "https://example.com"

def test_save_config_overwrites_existing(tmp_path):
    """Test saving config overwrites existing file"""
    config_path = tmp_path / "test_config.json"
    
    # Create initial config
    initial_config = {"api_key": "initial", "endpoint": "https://initial.com"}
    save_config(config_path, initial_config)
    
    # Update with new config
    updated_config = {"api_key": "updated", "new_setting": "value"}
    save_config(config_path, updated_config)
    
    # Verify the contents were overwritten
    with open(config_path, "r") as f:
        saved_config = json.load(f)
    
    assert saved_config == updated_config
    assert saved_config["api_key"] == "updated"
    assert "endpoint" not in saved_config
    assert saved_config["new_setting"] == "value"

def test_save_config_creates_parent_directories(tmp_path):
    """Test saving config creates parent directories if they don't exist"""
    nested_path = tmp_path / "deeply" / "nested" / "directory" / "config.json"
    test_config = {"test_key": "test_value"}
    
    # Save to a path that doesn't exist yet
    nested_path.parent.mkdir(parents=True, exist_ok=True)
    save_config(nested_path, test_config)
    
    # Verify the file was created
    assert nested_path.exists()
    
    # Verify the contents
    with open(nested_path, "r") as f:
        saved_config = json.load(f)
    
    assert saved_config == test_config