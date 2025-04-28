import pytest
from unittest.mock import MagicMock, patch, call
from canvas_cli.cli import app
from typer.testing import CliRunner
from handlers.config_handler import handle_config_tui, save_config
from canvas_cli.constants import GLOBAL_CONFIG_PATH, LOCAL_CONFIG_PATH

class TestHandleConfigTUI:

    @pytest.fixture
    def mock_ctx(self):
        ctx = MagicMock()
        return ctx

    @pytest.fixture
    def mock_config_path(self, tmp_path):
        return tmp_path / "config.json"
    
    @patch("builtins.input")
    @patch("importlib.util.find_spec")
    @patch("handlers.config_handler.get_config_path")
    @patch("handlers.config_handler.load_config")
    @patch("handlers.config_handler.save_config")
    @patch("handlers.config_handler.echo")
    def test_handle_config_tui_no_curses_fallback(
        self, mock_echo, mock_save_config, mock_load_config, 
        mock_get_config_path, mock_find_spec, mock_input, 
        mock_ctx, mock_config_path
    ):
        # Setup mocks
        mock_find_spec.return_value = None  # No curses available
        mock_get_config_path.return_value = mock_config_path
        mock_load_config.return_value = {}
        mock_input.side_effect = ["n", "2"]  # Use fallback and select basic symbols
        
        # Call function
        handle_config_tui(mock_ctx, global_=True, local=False)
        
        # Verify config was saved with correct values
        mock_save_config.assert_called_once()
        args = mock_save_config.call_args[0]
        assert args[0] == mock_config_path
        assert args[1]["tui_fallback"] == True
        assert args[1]["tui_emoji_level"] == 1  # Basic symbols
    
    @patch("builtins.input")
    @patch("importlib.util.find_spec")
    @patch("handlers.config_handler.get_config_path")
    @patch("handlers.config_handler.load_config")
    @patch("handlers.config_handler.save_config")
    @patch("handlers.config_handler.echo")
    def test_handle_config_tui_no_curses_install_suggestion(
        self, mock_echo, mock_save_config, mock_load_config, 
        mock_get_config_path, mock_find_spec, mock_input, 
        mock_ctx
    ):
        # Setup mocks
        mock_find_spec.return_value = None  # No curses available
        mock_input.return_value = "y"  # User wants to install curses
        
        # Call function and expect exit
        with pytest.raises(SystemExit):
            handle_config_tui(mock_ctx, global_=True, local=False)
        
        # Verify correct message
        mock_echo.assert_any_call("Please run: pip install windows-curses", ctx=mock_ctx)
    
    @patch("builtins.input")
    @patch("importlib.util.find_spec")
    @patch("curses.wrapper")
    @patch("handlers.config_handler.get_config_path")
    @patch("handlers.config_handler.load_config")
    @patch("handlers.config_handler.save_config")
    @patch("handlers.config_handler.echo")
    def test_handle_config_tui_with_curses(
        self, mock_echo, mock_save_config, mock_load_config, 
        mock_get_config_path, mock_curses_wrapper, mock_find_spec,
        mock_input, mock_ctx, mock_config_path
    ):
        # Setup mocks
        mock_find_spec.return_value = True  # Curses available
        mock_get_config_path.return_value = mock_config_path
        mock_load_config.return_value = {}
        mock_input.return_value = "y"  # User wants to use fancy TUI
        mock_curses_wrapper.return_value = "1"  # User selects full emoji
        
        # Call function
        handle_config_tui(mock_ctx, global_=True, local=False)
        
        # Verify config was saved with correct values
        mock_save_config.assert_called_once()
        args = mock_save_config.call_args[0]
        assert args[0] == mock_config_path
        assert args[1]["tui_fallback"] == False
        assert args[1]["tui_emoji_level"] == 2  # Full emoji level
    
    @patch("builtins.input")
    @patch("importlib.util.find_spec")
    @patch("handlers.config_handler.get_config_path")
    @patch("handlers.config_handler.load_config")
    @patch("handlers.config_handler.save_config")
    @patch("handlers.config_handler.echo")
    def test_handle_config_tui_curses_but_user_prefers_fallback(
        self, mock_echo, mock_save_config, mock_load_config, 
        mock_get_config_path, mock_find_spec, mock_input, 
        mock_ctx, mock_config_path
    ):
        # Setup mocks
        mock_find_spec.return_value = True  # Curses available
        mock_get_config_path.return_value = mock_config_path
        mock_load_config.return_value = {}
        mock_input.side_effect = ["n", "3"]  # User prefers fallback and selects plain text
        
        # Call function
        handle_config_tui(mock_ctx, global_=True, local=False)
        
        # Verify config was saved with correct values
        mock_save_config.assert_called_once()
        args = mock_save_config.call_args[0]
        assert args[0] == mock_config_path
        assert args[1]["tui_fallback"] == True
        assert args[1]["tui_emoji_level"] == 0  # Plain text
    
    @patch("builtins.input")
    @patch("importlib.util.find_spec")
    @patch("handlers.config_handler.get_config_path")
    @patch("handlers.config_handler.load_config")
    @patch("handlers.config_handler.save_config")
    @patch("handlers.config_handler.echo")
    def test_handle_config_tui_both_global_local_error(
        self, mock_echo, mock_save_config, mock_load_config, 
        mock_get_config_path, mock_find_spec, mock_input, 
        mock_ctx
    ):
        # Test that error is raised when both global and local are True
        with pytest.raises(Exception):
            handle_config_tui(mock_ctx, global_=True, local=True)