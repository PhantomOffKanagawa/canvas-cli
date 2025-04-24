from _pytest import runner
import pytest
from unittest.mock import MagicMock, patch, call
import typer
from canvas_cli.cli import app
from typer.testing import CliRunner
from handlers.config_handler import handle_config_unset, load_config, save_config, GLOBAL_CONFIG_PATH, LOCAL_CONFIG_PATH

# ──────────────────────
# CONFIG UNSET HANDLER TESTS
# ──────────────────────

def test_handle_config_unset_non_existent_key():
    """Test unsetting a key that doesn't exist"""
    
    # Setup
    ctx = MagicMock()
    
    # Execute
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_unset(ctx=ctx, key="non_existent_key", global_=False, local=False)
        
        # Assert
        mock_echo.assert_called_once_with(f"Key 'non_existent_key' not found in {LOCAL_CONFIG_PATH}", ctx=ctx)

def test_handle_config_unset_from_local():
    """Test unsetting a key from local config"""
    
    # Setup
    ctx = MagicMock()
    local_config = {"api_key": "local_key", "user": "testuser"}
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_unset(ctx=ctx, key="api_key", global_=False, local=True)
        
        # Assert
        mock_echo.assert_called_once_with(f"Unset api_key in {LOCAL_CONFIG_PATH}", ctx=ctx)
        
        # Verify key was removed
        updated_config = load_config(LOCAL_CONFIG_PATH)
        assert "api_key" not in updated_config
        assert "user" in updated_config

def test_handle_config_unset_from_global():
    """Test unsetting a key from global config"""
    
    # Setup
    ctx = MagicMock()
    global_config = {"api_key": "global_key", "domain": "example.com"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    
    # Execute
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_unset(ctx=ctx, key="domain", global_=True, local=False)
        
        # Assert
        mock_echo.assert_called_once_with(f"Unset domain in {GLOBAL_CONFIG_PATH}", ctx=ctx)
        
        # Verify key was removed
        updated_config = load_config(GLOBAL_CONFIG_PATH)
        assert "domain" not in updated_config
        assert "api_key" in updated_config

def test_handle_config_unset_default_to_local():
    """Test unsetting a key with default scope (local)"""
    
    # Setup
    ctx = MagicMock()
    local_config = {"api_key": "local_key", "user": "testuser"}
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_unset(ctx=ctx, key="user", global_=False, local=False)
        
        # Assert
        mock_echo.assert_called_once_with(f"Unset user in {LOCAL_CONFIG_PATH}", ctx=ctx)
        
        # Verify key was removed
        updated_config = load_config(LOCAL_CONFIG_PATH)
        assert "user" not in updated_config
        assert "api_key" in updated_config

def test_handle_config_unset_both_scopes_raises_error():
    """Test that unsetting a key from both scopes raises an error"""
    
    # Setup
    ctx = MagicMock()
    
    # Execute & Assert
    with pytest.raises(typer.BadParameter) as excinfo:
        handle_config_unset(ctx=ctx, key="test_key", global_=True, local=True)
    
    assert "Cannot set config in both --global and --local scope at the same time" in str(excinfo.value)

@pytest.mark.parametrize("command,key,expected_message", [
    (["config", "unset", "api_key", "--local"], "api_key", "Unset api_key in"),
    (["config", "unset", "domain", "--global"], "domain", "Unset domain in"),
    (["config", "unset", "non_existent", "--local"], "non_existent", "Key 'non_existent' not found in")
])
def test_config_unset_cli(command, key, expected_message):
    """Test config unset CLI commands"""
    
    # Setup
    runner = CliRunner()
    local_config = {"api_key": "local_key", "user": "testuser"}
    global_config = {"domain": "example.com", "api_key": "global_key"}
    save_config(LOCAL_CONFIG_PATH, local_config)
    save_config(GLOBAL_CONFIG_PATH, global_config)
    
    # Execute
    result = runner.invoke(app, command)
    
    # Assert
    assert result.exit_code == 0
    assert expected_message in result.stdout