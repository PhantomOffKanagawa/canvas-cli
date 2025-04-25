import pytest
from pathlib import Path
from canvas_cli.constants import GLOBAL_CONFIG_PATH, LOCAL_CONFIG_PATH

@pytest.fixture(autouse=True)
def isolate_configs(monkeypatch, tmp_path):
    global_config = tmp_path / "test_global_config.json"
    local_config = tmp_path / "test_local_config.json"

    monkeypatch.setattr("canvas_cli.constants.GLOBAL_CONFIG_PATH", global_config)
    monkeypatch.setattr("canvas_cli.constants.LOCAL_CONFIG_PATH", local_config)

    yield
    
    # Cleanup
    if global_config.exists():
        global_config.unlink()
    if local_config.exists():
        local_config.unlink()
        

@pytest.fixture
def clean_config():
    # Ensure config doesn't exist before tests
    if LOCAL_CONFIG_PATH.exists():
        LOCAL_CONFIG_PATH.unlink()
    yield
    # Clean up after tests
    if LOCAL_CONFIG_PATH.exists():
        LOCAL_CONFIG_PATH.unlink()