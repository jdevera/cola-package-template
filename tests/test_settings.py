import os

import pytest

from cola.settings import (
    cache_dir,
    config_dir,
    data_dir,
    debug_flags,
    full_command_name,
    launcher_name,
    log_level,
    package_dir,
)


@pytest.fixture
def cola_env(monkeypatch, tmp_path):
    monkeypatch.setenv("COLA_PACKAGE_DIR", str(tmp_path))
    monkeypatch.setenv("COLA_FULL_COMMAND_NAME", "testpkg cfg get")
    monkeypatch.setenv("COLA_LOG_LEVEL", "debug")
    monkeypatch.setenv("COLA_DEBUG_FLAGS", "verbose")
    return tmp_path


def test_package_dir(cola_env):
    assert package_dir() == cola_env


def test_full_command_name(cola_env):
    assert full_command_name() == "testpkg cfg get"


def test_log_level(cola_env):
    assert log_level() == "debug"


def test_debug_flags(cola_env):
    assert debug_flags() == "verbose"


def test_launcher_name(cola_env):
    assert launcher_name() == "testpkg"


def test_missing_env_raises(monkeypatch):
    monkeypatch.delenv("COLA_PACKAGE_DIR", raising=False)
    with pytest.raises(RuntimeError, match="COLA_PACKAGE_DIR not set"):
        package_dir()


def test_config_dir(cola_env, tmp_path, monkeypatch):
    # Override platformdirs to use tmp_path
    monkeypatch.setattr("cola.settings.user_config_dir", lambda name: str(tmp_path / "config" / name))
    path = config_dir()
    assert path.name == "testpkg"
    assert path.exists()


def test_data_dir(cola_env, tmp_path, monkeypatch):
    monkeypatch.setattr("cola.settings.user_data_dir", lambda name: str(tmp_path / "data" / name))
    path = data_dir()
    assert path.name == "testpkg"
    assert path.exists()


def test_cache_dir(cola_env, tmp_path, monkeypatch):
    monkeypatch.setattr("cola.settings.user_cache_dir", lambda name: str(tmp_path / "cache" / name))
    path = cache_dir()
    assert path.name == "testpkg"
    assert path.exists()
