from pathlib import Path

CONFIG_FILE_NAME = ".gitconfig.json"
GLOBAL_CONFIG_PATH = Path.home() / CONFIG_FILE_NAME
LOCAL_CONFIG_PATH = Path.cwd() / CONFIG_FILE_NAME
