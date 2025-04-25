import pytest
import canvas_cli.constants

@pytest.fixture(autouse=True)
def isolate_configs(monkeypatch, tmp_path):
    global_config = tmp_path / "test_global_config.json"
    local_config = tmp_path / "test_local_config.json"

    # Show in output
    print(f"Global config path: {global_config}")
    print(f"Local config path: {local_config}")

    monkeypatch.setattr("canvas_cli.constants.GLOBAL_CONFIG_PATH", global_config)
    monkeypatch.setattr("canvas_cli.constants.LOCAL_CONFIG_PATH", local_config)


@pytest.fixture
@pytest.fixture
def clean_config():
    # Ensure config doesn't exist before tests
    if canvas_cli.constants.LOCAL_CONFIG_PATH.exists():
        canvas_cli.constants.LOCAL_CONFIG_PATH.unlink()
    yield
    # Clean up after tests
    if canvas_cli.constants.LOCAL_CONFIG_PATH.exists():
        canvas_cli.constants.LOCAL_CONFIG_PATH.unlink()