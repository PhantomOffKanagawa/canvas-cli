from functools import wraps
import typer
from typing import Any, Optional
import json
import os
from pathlib import Path
from canvas_cli.handler_helper import echo
from canvas_cli.constants import GLOBAL_CONFIG_PATH, LOCAL_CONFIG_PATH

# ──────────────────────
# UTILITY FUNCTIONS
# ──────────────────────

def load_config(path: Path) -> dict:
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_config(path: Path, config: dict):
    with open(path, "w") as f:
        json.dump(config, f, indent=2)

def get_config_path(global_: bool, local: bool) -> Path:
    if global_:
        return GLOBAL_CONFIG_PATH
    if local or LOCAL_CONFIG_PATH.exists():
        return LOCAL_CONFIG_PATH
    return LOCAL_CONFIG_PATH

def get_cascading_config_value(key: str, override: Optional[str] = None) -> Optional[Any]:
    if override is not None:
        return override
    local_config = load_config(LOCAL_CONFIG_PATH)
    global_config = load_config(GLOBAL_CONFIG_PATH)
    return local_config.get(key) or global_config.get(key)

get_key = lambda key, ctx: get_cascading_config_value(key, ctx.params.get(key))
get_key_static = lambda key: get_cascading_config_value(key)

# ──────────────────────
# HANDLER FUNCTIONS
# ──────────────────────

# Read from all available files and return the first value found
# Order is local, then global
def handle_config_get(ctx: typer.Context, key: str, global_: bool, local: bool):
    value = None
    
    if (global_ and local) or not (global_ or local):
        # Check if all scopes or none are set
        # If so cascade through all configs for the key
        config_path = "global or local"
        value = get_cascading_config_value(key)
    else:
        # Check the specified scope (global/local) for the key
        config_path = get_config_path(global_, local)
        config = load_config(config_path)
        value = config.get(key)
        
    # Print result
    if value is None:
        echo(f"Key '{key}' not found in {config_path}", ctx=ctx)
    else:
        echo(f"{key}={value}", ctx=ctx)

# Write to specified scope (global/local) or default to local
def handle_config_set(ctx: typer.Context, key: str, value: str, global_: bool, local: bool):
    # Get the config path based on the specified scope
    # (default) local
    
    if global_ and local:
        # If both global and local are set, abort
        echo("Cannot set config in both global and local scope at the same time.", ctx=ctx)
        raise typer.BadParameter("Cannot set config in both global and local scope at the same time.")
    else:
        # Check the specified scope (global/local) for the key
        # (default) local
        config_path = get_config_path(global_, local)
        config = load_config(config_path)
        config[key] = value
        save_config(config_path, config)
        echo(f"Set {key} to {value} in {config_path}", ctx=ctx)

# Remove the key from the specified scope (global/local) or default to local
def handle_config_unset(ctx: typer.Context, key: str, global_: bool, local: bool):
    if global_ and local:
        # If both global and local are set, abort
        raise typer.BadParameter("Cannot set config in both --global and --local scope at the same time.")
    else:
        # Check the specified scope (global/local) for the key
        # (default) local
        config_path = get_config_path(global_, local)
        config = load_config(config_path)
        if key in config:
            # Remove the key from the config
            del config[key]
            save_config(config_path, config)
            echo(f"Unset {key} in {config_path}", ctx=ctx)
        else:
            # Key not found in the config
            echo(f"Key '{key}' not found in {config_path}", ctx=ctx)

# List all keys and values in the specified scope (global/local) or default to cascading both
def handle_config_list(ctx: typer.Context, global_: bool, local: bool, show_origin: bool, show_scope: bool):
    if global_ and local or not (global_ or local):
        # Check if all scopes or none are set
        # If so cascade through all configs for the key
        globalConfig = load_config(get_config_path(True, False))
        localConfig = load_config(get_config_path(False, True))
        
        # Combine configs but track origin and path
        config = {}
        origins = {}
        file_paths = {}
        
        # Add global values first
        for k, v in globalConfig.items():
            config[k] = v
            origins[k] = "global"
            file_paths[k] = str(GLOBAL_CONFIG_PATH)
            
        # Add local values (overriding globals)
        for k, v in localConfig.items():
            config[k] = v
            origins[k] = "local"
            file_paths[k] = str(LOCAL_CONFIG_PATH)
            
        scope_text = "cascaded (global and local)"
    else:
        # Check the specified scope (global/local) for the key
        config_path = get_config_path(global_, local)
        config = load_config(config_path)
        scope_text = "global" if global_ else "local"
        origins = {k: scope_text for k in config.keys()}
        file_paths = {k: str(config_path) for k in config.keys()}

    if not config:
        echo("No config found in global or local scope", ctx=ctx)
        return

    # Print the config for the specified scope
    for k, v in config.items():
        output = f"{k}={v}"
        if show_origin and show_scope:
            output = f"{output} (from {origins[k]} config at {file_paths[k]})"
        elif show_origin:
            output = f"{output} (from {file_paths[k]})"
        elif show_scope:
            output = f"{output} ({origins[k]})"
        echo(output, ctx=ctx)
            
    echo(f"Listed config from {scope_text} scope", ctx=ctx)

def handle_config_tui(ctx: typer.Context, global_: bool, local: bool):
    """
    Handler for 'canvas config tui' to set emoji level and fallback in the correct config file.
    """
    import importlib.util
    import sys
    import time
    from pathlib import Path
    # Determine config path
    if global_ and local:
        echo("Cannot set config in both global and local scope at the same time.", ctx=ctx)
        raise typer.BadParameter("Cannot set config in both global and local scope at the same time.")
    elif not global_ and not local:
        # If neither is set, default to global
        global_ = True
        local = False
    
    config_path = get_config_path(global_, local)
    config = load_config(config_path)
    
    # 1. Check for curses
    curses_spec = importlib.util.find_spec("curses")
    has_curses = curses_spec is not None
    fallback = False
    # Check if the user wants to use the fancy TUI or fallback to text TUI
    if not has_curses:
        echo("Curses (for the fancy TUI) is not installed on your system.", ctx=ctx)
        echo("If you want the fancier TUI, install windows-curses with: pip install windows-curses", ctx=ctx)
        echo("Otherwise, you can use the backup text TUI.", ctx=ctx)
        ans = input("Do you want to install windows-curses and use the fancy TUI? (y/n): ").strip().lower()
        if ans == "y":
            echo("Please run: pip install windows-curses", ctx=ctx)
            time.sleep(1)
            sys.exit(0)
        else:
            fallback = True
    else:
        echo("Curses is installed, you can use the fancy TUI. (Sometimes the fancy tui doesn't support emojis e.g. on some Windows terminals)", ctx=ctx)
        ans = input("Do you want to use the fancy TUI? (y/n): ").strip().lower()
        if ans == "n":
            fallback = True
            
    # 2. Emoji test (three levels)
    if not fallback:
        import curses
        # Use curses for the fancy TUI
        
        def curses_emoji_test(stdscr):
            stdscr.clear()
            curses.curs_set(1)  # Show cursor
            
            # Setup colors
            curses.start_color()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            
            # Display emoji test
            stdscr.addstr(1, 2, "Can you see this folder emoji? ->  📁  <- (should look like a folder)", curses.color_pair(1))
            stdscr.addstr(2, 2, "Can you see this checkmark? ->  ✔  <- (should look like a checkmark)", curses.color_pair(1))
            
            stdscr.addstr(4, 2, "Please choose your preferred display style:", curses.color_pair(1))
            stdscr.addstr(5, 2, "1. Full emoji: 📁 ✔ ❌ 🔄 📝", curses.color_pair(1))
            stdscr.addstr(6, 2, "2. Basic symbols: ✓ ✗ » ...", curses.color_pair(1))
            stdscr.addstr(7, 2, "3. Plain text: [DIR] [OK] [X] >>", curses.color_pair(1))
            
            stdscr.addstr(9, 2, "Enter your choice (1, 2, or 3): ", curses.color_pair(2))
            stdscr.refresh()
            
            # Get user input
            choice = ""
            while choice not in ["1", "2", "3"]:
                key = stdscr.getkey()
                if key in ["1", "2", "3"]:
                    choice = key
                    stdscr.addstr(9, 32, choice)
                    stdscr.refresh()
            
            return choice
        
        try:
            choice = curses.wrapper(curses_emoji_test)
        except Exception as e:
            echo(f"Error in curses UI: {e}", ctx=ctx)
            fallback = True
            # Fall back to regular input if curses fails
            choice = "2"  # Default to basic symbols
    else:
        # Regular terminal UI for emoji test
        echo("\nCan you see this folder emoji? ->  📁  <- (should look like a folder)", ctx=ctx)
        echo("Can you see this checkmark? ->  ✔  <- (should look like a checkmark)", ctx=ctx)
        
        echo("\nPlease choose your preferred display style:", ctx=ctx)
        echo("1. Full emoji: 📁 ✔ ❌ 🔄 📝", ctx=ctx)
        echo("2. Basic symbols: ✓ ✗ » ...", ctx=ctx)
        echo("3. Plain text: [DIR] [OK] [X] >>", ctx=ctx)
        
        choice = ""
        while choice not in ["1", "2", "3"]:
            choice = input("Enter your choice (1, 2, or 3): ").strip()
    
    emoji_level = 3 - int(choice)  # Map 1->2, 2->1, 3->0
    
    # Show example based on their choice
    if emoji_level == 2:
        echo("\nYou selected: Full emoji style (📁 ✔ ❌)", ctx=ctx)
    elif emoji_level == 1:
        echo("\nYou selected: Basic symbols style (✓ ✗ »)", ctx=ctx)
    else:
        echo("\nYou selected: Plain text style ([DIR] [OK] [X])", ctx=ctx)
            
    config['tui_fallback'] = fallback
    config['tui_emoji_level'] = emoji_level
    save_config(config_path, config)
    echo(f"TUI config updated in {config_path}", ctx=ctx)
    echo(f"tui_fallback: {config['tui_fallback']}, tui_emoji_level: {config['tui_emoji_level']}", ctx=ctx)
