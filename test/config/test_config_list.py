import pytest
from unittest.mock import MagicMock, patch, call
from canvas_cli.cli import app
from typer.testing import CliRunner
from handlers.config_handler import handle_config_list, save_config, GLOBAL_CONFIG_PATH, LOCAL_CONFIG_PATH

# ──────────────────────
# CONFIG LIST HANDLER TESTS
# ──────────────────────

def test_handle_config_list_no_configs_exist():
    """Test listing config when no configs exist"""
    
    # Delete any existing config files
    if GLOBAL_CONFIG_PATH.exists():
        GLOBAL_CONFIG_PATH.unlink()
    if LOCAL_CONFIG_PATH.exists():
        LOCAL_CONFIG_PATH.unlink()
    
    # Setup
    ctx = MagicMock()
    
    # Execute
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_list(ctx=ctx, global_=False, local=False, show_origin=False, show_scope=False)
        
        # Assert
        mock_echo.assert_called_once_with("No config found in global or local scope", ctx=ctx)

def test_handle_config_list_only_global():
    """Test listing config from global scope only"""
    
    # Setup
    ctx = MagicMock()
    global_config = {"api_key": "test_key", "domain": "example.com"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    
    # Execute
    # Test with global scope only
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_list(ctx=ctx, global_=True, local=False, show_origin=False, show_scope=False)
        
        # Assert multiple calls
        calls = [
            call("api_key=test_key", ctx=ctx),
            call("domain=example.com", ctx=ctx),
            call("Listed config from global scope", ctx=ctx)
        ]
        mock_echo.assert_has_calls(calls, any_order=True)

def test_handle_config_list_only_local(monkeypatch):
    """Test listing config from local scope only"""
    
    # Setup
    ctx = MagicMock()
    local_config = {"api_key": "local_key", "user": "testuser"}
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute
    # Test with local scope only
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_list(ctx=ctx, global_=False, local=True, show_origin=False, show_scope=False)
        
        # Assert multiple calls
        calls = [
            call("api_key=local_key", ctx=ctx),
            call("user=testuser", ctx=ctx),
            call("Listed config from local scope", ctx=ctx)
        ]
        mock_echo.assert_has_calls(calls, any_order=True)

# Test listing config with different scope flags when both global and local configs exist
# Test with different combinations of global and local flags
@pytest.mark.parametrize("global_flag,local_flag,expected_config,expected_message", [
    (True, False, {"api_key": "global_key", "domain": "example.com"}, "global"),
    (False, True, {"api_key": "local_key", "user": "testuser"}, "local"),
    (True, True, {"api_key": "local_key", "domain": "example.com", "user": "testuser"}, "cascaded (global and local)"),
    (False, False, {"api_key": "local_key", "domain": "example.com", "user": "testuser"}, "cascaded (global and local)")
])
def test_handle_config_list_different_scopes(monkeypatch, global_flag, local_flag, expected_config, expected_message):
    """Test listing config with different scope flags"""
    
    # Setup
    ctx = MagicMock()
    global_config = {"api_key": "global_key", "domain": "example.com"}
    local_config = {"api_key": "local_key", "user": "testuser"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_list(ctx=ctx, global_=global_flag, local=local_flag, show_origin=False, show_scope=False)
        
        # Assert config items are shown
        for key, value in expected_config.items():
            mock_echo.assert_any_call(f"{key}={value}", ctx=ctx)
            
        # Assert scope message is shown
        mock_echo.assert_any_call(f"Listed config from {expected_message} scope", ctx=ctx)
        
def test_handle_config_list_cascading(monkeypatch):
    """Test listing config with cascading (both global and local)"""
    
    # Setup
    ctx = MagicMock()
    global_config = {"api_key": "global_key", "domain": "example.com"}
    local_config = {"api_key": "local_key", "user": "testuser"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    with patch('handlers.config_handler.echo') as mock_echo:
        # Execute
        handle_config_list(ctx=ctx, global_=True, local=True, show_origin=False, show_scope=False)
        
        # Assert multiple calls
        calls = [
            call("api_key=local_key", ctx=ctx),
            call("domain=example.com", ctx=ctx),
            call("user=testuser", ctx=ctx),
            call("Listed config from cascaded (global and local) scope", ctx=ctx)
        ]
        mock_echo.assert_has_calls(calls, any_order=True)
        
# Test on CLI
# Test listing config with different scope flags when both global and local configs exist
# Test with different combinations of global and local flags
@pytest.mark.parametrize("command,expected_config,expected_message", [
    (["config", "list", "--global"], {"api_key": "global_key", "domain": "example.com"}, "global"),
    (["config", "list", "--local"], {"api_key": "local_key", "user": "testuser"}, "local"),
    (["config", "list", "--global", "--local"], {"api_key": "local_key", "domain": "example.com", "user": "testuser"}, "cascaded (global and local)"),
    (["config", "list"], {"api_key": "local_key", "domain": "example.com", "user": "testuser"}, "cascaded (global and local)")
])
def test_handle_config_list_different_scopes_CLI(monkeypatch, command, expected_config, expected_message):
    """Test listing config command with different scope flags"""
    
    # Setup
    runner = CliRunner()
    global_config = {"api_key": "global_key", "domain": "example.com"}
    local_config = {"api_key": "local_key", "user": "testuser"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Simulate CLI command execution
    result = runner.invoke(app, command)

    # Assert exit
    assert result.exit_code == 0

    # Assert config items are shown
    for key, value in expected_config.items():
        assert f"{key}={value}" in result.stdout
        
    # Assert scope message is shown
    assert f"Listed config from {expected_message} scope" in result.stdout

def test_handle_config_list_with_show_scope(monkeypatch):
    """Test listing config with show_scope enabled"""
    
    # Setup
    ctx = MagicMock()
    global_config = {"domain": "example.com"}
    local_config = {"api_key": "local_key"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_list(ctx=ctx, global_=False, local=False, show_origin=False, show_scope=True)
        
        # Assert
        calls = [
            call("domain=example.com (global)", ctx=ctx),
            call("api_key=local_key (local)", ctx=ctx),
            call("Listed config from cascaded (global and local) scope", ctx=ctx)
        ]
        mock_echo.assert_has_calls(calls, any_order=True)

def test_handle_config_list_with_show_origin(monkeypatch):
    """Test listing config with show_origin enabled"""
    
    # Setup
    ctx = MagicMock()
    global_config = {"domain": "example.com"}
    local_config = {"api_key": "local_key"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_list(ctx=ctx, global_=False, local=False, show_origin=True, show_scope=False)
        
        # Assert
        calls = [
            call(f"domain=example.com (from {str(GLOBAL_CONFIG_PATH)})", ctx=ctx),
            call(f"api_key=local_key (from {str(LOCAL_CONFIG_PATH)})", ctx=ctx),
            call(f"Listed config from cascaded (global and local) scope", ctx=ctx)
        ]
        mock_echo.assert_has_calls(calls, any_order=True)

def test_handle_config_list_with_all_flags(monkeypatch):
    """Test listing config with both show_origin and show_scope enabled"""
    
    # Setup
    ctx = MagicMock()
    global_config = {"domain": "example.com"}
    local_config = {"api_key": "local_key"}
    save_config(GLOBAL_CONFIG_PATH, global_config)
    save_config(LOCAL_CONFIG_PATH, local_config)
    
    # Execute
    with patch('handlers.config_handler.echo') as mock_echo:
        handle_config_list(ctx=ctx, global_=False, local=False, show_origin=True, show_scope=True)
        
        # Assert
        mock_echo.assert_any_call(f"domain=example.com (from global config at {str(GLOBAL_CONFIG_PATH)})", ctx=ctx)
        mock_echo.assert_any_call(f"api_key=local_key (from local config at {str(LOCAL_CONFIG_PATH)})", ctx=ctx)
        mock_echo.assert_any_call("Listed config from cascaded (global and local) scope", ctx=ctx)