import pytest
from pathlib import Path

@pytest.fixture(autouse=True)
def isolate_configs(monkeypatch, tmp_path):
    global_config = tmp_path / "global_config.json"
    local_config = tmp_path / "local_config.json"

    monkeypatch.setattr("canvas_cli.constants.GLOBAL_CONFIG_PATH", global_config)
    monkeypatch.setattr("canvas_cli.constants.LOCAL_CONFIG_PATH", local_config)

