"""COLA environment and directory helpers.

Lazy accessors for Command Launcher environment variables. All functions are
safe to import anywhere — they only fail when actually called outside a
launcher context, with a clear error message.

Directory helpers use platformdirs to follow OS conventions
(XDG on Linux, Library/Application Support on macOS, etc.).

Usage in commands:
    from cola.settings import package_dir, launcher_name, config_dir

    pkg = package_dir()           # Path to the package root
    name = launcher_name()        # e.g., "vht", "dht"
    cfg = config_dir()            # e.g., ~/.config/vht/
"""

import os
from pathlib import Path

from platformdirs import user_cache_dir, user_config_dir, user_data_dir


def _require_env(name: str) -> str:
    var = f"COLA_{name}"
    value = os.environ.get(var)
    if not value:
        raise RuntimeError(f"{var} not set — are you running outside the Command Launcher?")
    return value


def package_dir() -> Path:
    """Package root directory. From COLA_PACKAGE_DIR."""
    return Path(_require_env("PACKAGE_DIR"))


def full_command_name() -> str:
    """Full command invocation (e.g., 'vht cfg get'). From COLA_FULL_COMMAND_NAME."""
    return _require_env("FULL_COMMAND_NAME")


def log_level() -> str:
    """Log level from launcher configuration. From COLA_LOG_LEVEL."""
    return _require_env("LOG_LEVEL")


def debug_flags() -> str:
    """Debug flags from launcher configuration. From COLA_DEBUG_FLAGS."""
    return _require_env("DEBUG_FLAGS")


def launcher_name() -> str:
    """Launcher name (first word of the full command, e.g., 'vht')."""
    return full_command_name().split()[0]


def config_dir(ensure_exists: bool = True) -> Path:
    """Config directory following OS conventions (e.g., ~/.config/<launcher>/)."""
    path = Path(user_config_dir(launcher_name()))
    if ensure_exists:
        path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir(ensure_exists: bool = True) -> Path:
    """Data directory following OS conventions (e.g., ~/.local/share/<launcher>/)."""
    path = Path(user_data_dir(launcher_name()))
    if ensure_exists:
        path.mkdir(parents=True, exist_ok=True)
    return path


def cache_dir(ensure_exists: bool = True) -> Path:
    """Cache directory following OS conventions (e.g., ~/.cache/<launcher>/)."""
    path = Path(user_cache_dir(launcher_name()))
    if ensure_exists:
        path.mkdir(parents=True, exist_ok=True)
    return path
