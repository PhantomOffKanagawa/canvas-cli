from unittest.mock import MagicMock, patch
import pytest
import json
from canvas_cli.constants import GLOBAL_CONFIG_PATH, LOCAL_CONFIG_PATH
from handlers.config_handler import save_config, handle_config_get

# ──────────────────────
# CONFIG GET HANDLER TESTS
# ──────────────────────

def test_handle_config_get_no_scopes_key_found_in_local(monkeypatch):
    """Test that when no scope is specified, it checks local first and returns the value if found"""
    # Setup
    local_config = {"api_key": "local_value"}
    global_config = {"api_key": "global_value", "other_key": "other_value"}
    
    # Save test configs
    save_config(LOCAL_CONFIG_PATH, local_config)
    save_config(GLOBAL_CONFIG_PATH, global_config)
    
    # Mock context and echo
    ctx = MagicMock()
    mock_echo = MagicMock()
    monkeypatch.setattr('handlers.config_handler.echo', mock_echo)
    
    # Execute
    handle_config_get(ctx, "api_key", False, False)
    
    # Verify
    mock_echo.assert_called_once_with("api_key=local_value", ctx=ctx)

def test_handle_config_get_no_scopes_key_found_in_global(monkeypatch):
    """Test that when no scope is specified and key not in local, it checks global"""
    # Setup
    local_config = {"local_key": "local_value"}
    global_config = {"api_key": "global_value"}
    
    save_config(LOCAL_CONFIG_PATH, local_config)
    save_config(GLOBAL_CONFIG_PATH, global_config)
    
    ctx = MagicMock()
    mock_echo = MagicMock()
    monkeypatch.setattr('handlers.config_handler.echo', mock_echo)
    
    # Execute
    handle_config_get(ctx, "api_key", False, False)
    
    # Verify
    mock_echo.assert_called_once_with("api_key=global_value", ctx=ctx)

def test_handle_config_get_no_scopes_key_not_found(monkeypatch):
    """Test that when no scope is specified and key not in any config, it returns not found"""
    # Setup
    local_config = {"local_key": "local_value"}
    global_config = {"global_key": "global_value"}
    
    save_config(LOCAL_CONFIG_PATH, local_config)
    save_config(GLOBAL_CONFIG_PATH, global_config)
    
    ctx = MagicMock()
    mock_echo = MagicMock()
    monkeypatch.setattr('handlers.config_handler.echo', mock_echo)
    
    # Execute
    handle_config_get(ctx, "missing_key", False, False)
    
    # Verify
    mock_echo.assert_called_once_with("Key 'missing_key' not found in global or local", ctx=ctx)

def test_handle_config_get_global_scope_key_found(monkeypatch):
    """Test that when global scope is specified, it only checks global config"""
    # Setup
    local_config = {"api_key": "local_value"}
    global_config = {"api_key": "global_value"}
    
    save_config(LOCAL_CONFIG_PATH, local_config)
    save_config(GLOBAL_CONFIG_PATH, global_config)
    
    ctx = MagicMock()
    mock_echo = MagicMock()
    monkeypatch.setattr('handlers.config_handler.echo', mock_echo)
    
    # Execute
    handle_config_get(ctx, "api_key", True, False)
    
    # Verify
    mock_echo.assert_called_once_with("api_key=global_value", ctx=ctx)

def test_handle_config_get_local_scope_key_found(monkeypatch):
    """Test that when local scope is specified, it only checks local config"""
    # Setup
    local_config = {"api_key": "local_value"}
    global_config = {"api_key": "global_value"}
    
    save_config(LOCAL_CONFIG_PATH, local_config)
    save_config(GLOBAL_CONFIG_PATH, global_config)
    
    ctx = MagicMock()
    mock_echo = MagicMock()
    monkeypatch.setattr('handlers.config_handler.echo', mock_echo)
    
    # Execute
    handle_config_get(ctx, "api_key", False, True)
    
    # Verify
    mock_echo.assert_called_once_with("api_key=local_value", ctx=ctx)

def test_handle_config_get_both_scopes(monkeypatch):
    """Test that when both scopes are specified, it cascades through configs"""
    # Setup
    local_config = {"api_key": "local_value"}
    global_config = {"api_key": "global_value"}
    
    save_config(LOCAL_CONFIG_PATH, local_config)
    save_config(GLOBAL_CONFIG_PATH, global_config)
    
    ctx = MagicMock()
    mock_echo = MagicMock()
    monkeypatch.setattr('handlers.config_handler.echo', mock_echo)
    
    # Execute
    handle_config_get(ctx, "api_key", True, True)
    
    # Verify - should cascade and find local value first
    mock_echo.assert_called_once_with("api_key=local_value", ctx=ctx)