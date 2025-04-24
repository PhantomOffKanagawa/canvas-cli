import pytest
from unittest.mock import MagicMock, patch, call
import typer
from canvas_cli.cli import app
from typer.testing import CliRunner
from handlers.config_handler import handle_config_set, load_config, save_config, GLOBAL_CONFIG_PATH, LOCAL_CONFIG_PATH

# ──────────────────────
# CONFIG GET HANDLER TESTS
# ──────────────────────

def test_config_set_local_default():
    """Test setting a value in local config (default)"""
    with patch('handlers.config_handler.echo') as mock_echo:
        # Set a config value in local file
        save_config(LOCAL_CONFIG_PATH, {})
        handle_config_set(MagicMock(), "api_key", "test-key", False, False)
        
        # Verify the config was updated
        local_config = load_config(LOCAL_CONFIG_PATH)
        assert local_config["api_key"] == "test-key"
        mock_echo.assert_called_once()

def test_config_set_global():
    """Test setting a value in global config"""
    with patch('handlers.config_handler.echo') as mock_echo:
        # Set a config value in global file
        save_config(GLOBAL_CONFIG_PATH, {})
        handle_config_set(MagicMock(), "api_key", "global-key", True, False)
        
        # Verify the config was updated
        global_config = load_config(GLOBAL_CONFIG_PATH)
        assert global_config["api_key"] == "global-key"
        mock_echo.assert_called_once()

def test_config_set_local_explicit():
    """Test setting a value in local config explicitly"""
    with patch('handlers.config_handler.echo') as mock_echo:
        # Set a config value in local file
        save_config(LOCAL_CONFIG_PATH, {})
        handle_config_set(MagicMock(), "api_key", "local-key", False, True)
        
        # Verify the config was updated
        local_config = load_config(LOCAL_CONFIG_PATH)
        assert local_config["api_key"] == "local-key"
        mock_echo.assert_called_once()

def test_config_set_update_existing():
    """Test updating an existing value"""
    with patch('handlers.config_handler.echo') as mock_echo:
        # Setup existing config
        save_config(LOCAL_CONFIG_PATH, {"api_key": "old-key"})
        
        # Update existing config value
        handle_config_set(MagicMock(), "api_key", "new-key", False, False)
        
        # Verify the config was updated
        local_config = load_config(LOCAL_CONFIG_PATH)
        assert local_config["api_key"] == "new-key"
        mock_echo.assert_called_once()

def test_config_set_both_scopes_raises_error():
    """Test that setting both global and local flags raises an error"""
    with pytest.raises(typer.BadParameter):
        handle_config_set(MagicMock(), "api_key", "test-key", True, True)