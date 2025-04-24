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
