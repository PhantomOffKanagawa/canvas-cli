"""
Configuration Module for Canvas CLI
Handles loading, saving, and managing configuration settings for the Canvas CLI.
"""

import json
from pathlib import Path
from typing import Literal

# Global config path
USER_CONFIG_PATH = Path.home() / ".canvascli" / "config.json"

class Config:
    """Configuration class for Canvas CLI"""
    
    @staticmethod
    def load_global() -> dict:
        """Load global API configuration"""
        if USER_CONFIG_PATH.exists():
            with open(USER_CONFIG_PATH, "r") as f:
                return json.load(f)
        else:
            raise FileNotFoundError("Canvas CLI not configured. Run 'canvas config --set-token <token> --set-host <host>'")

    @staticmethod
    def save_global(json_data: dict) -> None:
        """Save global API configuration"""
        USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(USER_CONFIG_PATH, "w") as f:
            json.dump(json_data, f, indent=4)

    @staticmethod
    def set_value(key: str, value: str, scope: Literal["global", "local"]) -> None:
        """Set a configuration value"""
        if not key or not value:
            raise ValueError("Key and value must be provided")

        if scope == "global":
            try:
                config = Config.load_global()
            except FileNotFoundError as e:
                config = {}
            config[key] = value
            Config.save_global(config)
        elif scope == "local":
            config = Config.load_project_config() or {}
            config[key] = value
            Config.save_project_config(config)
        else:
            raise ValueError("Invalid scope. Use 'global' or 'local'.")
        
    @staticmethod
    def get_value(key: str, scope: Literal["local", "global"] | list[str] | str) -> str | None:
        """
        Get a configuration value for a given scope or list of scopes.
        If a list is provided, return the first non-None value found.
        """
        if isinstance(scope, list):
            for s in scope:
                value = Config.get_value(key, s)
                if value is not None:
                    return value
            return None
        elif scope == "global":
            config = Config.load_global()
            return config.get(key, None)
        elif scope == "local":
            config = Config.load_project_config()
            return config.get(key, None) if config else None
        else:
            raise ValueError("Invalid scope. Use 'global' or 'local'.")
        
    @staticmethod
    def unset_value(key: str, scope: Literal["global", "local"]) -> bool:
        """Unset a configuration value"""
        if scope == "global":
            config = Config.load_global()
            if key in config:
                del config[key]
                Config.save_global(config)
                return True
            else:
                return False
        elif scope == "local":
            config = Config.load_project_config()
            if config and key in config:
                del config[key]
                Config.save_project_config(config)
                return True
            else:
                return False
        else:
            raise ValueError("Invalid scope. Use 'global' or 'local'.")
    
    @staticmethod
    def get_headers() -> dict[str, str]:
        """Get authorization headers for API requests"""
        config = Config.load_global()
        return {
            "Authorization": f"Bearer {config['token']}"
        }
    
    @staticmethod
    def load_project_config(config_dir: Path | None = None) -> dict | None:
        """Load local project configuration"""
        if config_dir is None:
            config_dir = Path.cwd()

        local_config_path = config_dir / "canvas.json"
        if local_config_path.exists():
            with open(local_config_path, "r") as f:
                return json.load(f)
        else:
            return None
    
    @staticmethod
    def save_project_config(config: dict = {}, config_dir: Path | None = None) -> None:
        """Save local project configuration"""
        if config_dir is None:
            config_dir = Path.cwd()

        config_dir.mkdir(exist_ok=True)
        
        # Store the file path in the config
        if config_dir:
            config["file_path"] = str(config_dir)
            
        with open(config_dir / "canvas.json", "w") as f:
            json.dump(config, f, indent=4)
