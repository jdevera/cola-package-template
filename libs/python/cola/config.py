"""Configuration management for Command Launcher packages.

Provides YAML-backed configuration storage with dot-notation key access,
a registry for declaring valid configuration keys, and a declarative
ConfigClient for commands to request configuration values.

Usage:
    # In a command that needs config values:
    from cola.config import ConfigClient

    client = ConfigClient()
    client.wants_entry("mail.server", description="SMTP server", default="localhost")
    client.wants_entry("mail.port", description="SMTP port", default="587")
    cfg = client.get(with_death=True)  # dies with error if required key is missing
    print(cfg.mail_server, cfg.mail_port)

    # Direct config access:
    from cola.config import Config, get_config

    config = get_config()
    value = config.get("mail.server")        # returns None if missing
    value = config.get_strict("mail.server")  # raises KeyError if missing
    config.set("mail.server", "smtp.example.com")  # auto-saves
    config.delete("mail.server")              # auto-saves

    # Registry validation:
    from cola.config import ConfigRegistry

    registry = ConfigRegistry.load(Path("config_registry.yml"))
    if registry.has_key("mail.server"):
        key = registry.get_key("mail.server")
        print(key.description, key.example)
"""

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from cola import settings


@dataclass
class RegistryKey:
    """A leaf configuration key in the registry."""

    name: str
    description: str = ""
    example: str = ""

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "RegistryKey":
        return cls(
            name=name,
            description=data.get("description", ""),
            example=data.get("example", ""),
        )


@dataclass
class RegistryGroup:
    """A group of configuration keys in the registry."""

    name: str
    description: str = ""
    keys: dict[str, RegistryKey] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "RegistryGroup":
        keys = {}
        for key_name, key_data in data.get("keys", {}).items():
            keys[key_name] = RegistryKey.from_dict(key_name, key_data)
        return cls(
            name=name,
            description=data.get("description", ""),
            keys=keys,
        )

    def full_key(self, key_name: str) -> str:
        """Return the full dotted key name."""
        return f"{self.name}.{key_name}"


@dataclass
class ConfigRegistry:
    """Registry of all expected configuration keys.

    Loaded from a YAML file (typically config_registry.yml at the package root).
    Used to validate that config keys are recognized and to provide introspection.
    """

    version: int = 1
    top_level_keys: dict[str, RegistryKey] = field(default_factory=dict)
    groups: dict[str, RegistryGroup] = field(default_factory=dict)
    file: Path | None = None

    @classmethod
    def load(cls, file: Path) -> "ConfigRegistry":
        if not file.exists():
            return cls(file=file)
        with file.open() as f:
            data = yaml.safe_load(f) or {}
        version = data.get("version", 1)
        top_level_keys = {}
        groups = {}
        for name, entry_data in data.get("keys", {}).items():
            if "keys" in entry_data:
                groups[name] = RegistryGroup.from_dict(name, entry_data)
            else:
                top_level_keys[name] = RegistryKey.from_dict(name, entry_data)
        return cls(version=version, top_level_keys=top_level_keys, groups=groups, file=file)

    def get_group(self, name: str) -> RegistryGroup | None:
        return self.groups.get(name)

    def get_key(self, full_key: str) -> RegistryKey | None:
        """Get a registry key by full dotted name (e.g., 'mail.server') or top-level name."""
        if full_key in self.top_level_keys:
            return self.top_level_keys[full_key]
        parts = full_key.split(".", 1)
        if len(parts) != 2:
            return None
        group = self.groups.get(parts[0])
        if group is None:
            return None
        return group.keys.get(parts[1])

    def has_key(self, full_key: str) -> bool:
        return self.get_key(full_key) is not None

    def all_top_level_keys(self) -> list[RegistryKey]:
        return list(self.top_level_keys.values())

    def all_groups(self) -> list[RegistryGroup]:
        return list(self.groups.values())

    def all_keys(self) -> list[tuple[RegistryGroup, RegistryKey]]:
        result = []
        for group in self.groups.values():
            for key in group.keys.values():
                result.append((group, key))
        return result


def _validate_config(config: dict):
    if not isinstance(config, dict):
        raise ValueError("Invalid configuration content")
    for key, value in config.items():
        if not isinstance(key, str):
            raise ValueError("Invalid config: all keys must be strings")
        if isinstance(value, dict):
            _validate_config(value)


def _load_config(file: Path):
    if not file.exists():
        return {}
    with file.open() as f:
        return yaml.safe_load(f) or {}


def _flatten_config(config: dict) -> dict:
    def _flatten(d, parent_key="", sep="."):
        items = []
        for key, val in d.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(val, dict):
                items.extend(_flatten(val, new_key, sep=sep).items())
            else:
                items.append((new_key, val))
        return dict(items)

    return _flatten(config)


def _inflate_config(config: dict) -> dict:
    inflated = {}
    for key, value in config.items():
        keys = key.split(".")
        current = inflated
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = value
    return inflated


def _merge_dicts(d1, d2):
    for k, v in d2.items():
        if isinstance(v, dict):
            d1[k] = _merge_dicts(d1.get(k, {}), v)
        else:
            d1[k] = v
    return d1


class Config:
    """YAML-backed configuration store with dot-notation key access.

    Supports nested keys via dot notation (e.g., "mail.server"),
    auto-saves on mutation, and can operate in-memory without a file.
    """

    def __init__(self, *, config_data: dict = None, file: Path = None, read_only=False):
        if config_data is not None and file is not None:
            raise ValueError("Only one of config_data or file can be provided")

        self.file = file
        if file is not None:
            self.config = _load_config(file)
        elif config_data is not None:
            self.config = config_data
        else:
            self.config = {}

        if read_only:
            self.file = None

    @property
    def flat(self):
        return _flatten_config(self.config)

    def has(self, key):
        try:
            self.get_strict(key)
        except KeyError:
            return False
        return True

    def get(self, key):
        try:
            return self.get_strict(key)
        except KeyError:
            return None

    def get_strict(self, key):
        parts = key.split(".")
        current = self.config
        for part in parts:
            try:
                current = current[part]
            except (KeyError, TypeError):
                raise KeyError(key)
        return current

    def set(self, key, value):
        new_config = _inflate_config({key: value})
        self.config = _merge_dicts(self.config, new_config)
        self.save()

    def delete(self, key):
        if not self.has(key):
            raise KeyError(f"'{key}' not found")
        parts = key.split(".")
        current = self.config
        for part in parts[:-1]:
            current = current[part]
        del current[parts[-1]]
        self.save()

    def keys(self):
        return self.config.keys()

    def trim(self):
        """Remove entries that are empty dictionaries."""

        def _trim(d):
            for key, value in list(d.items()):
                if isinstance(value, dict):
                    if not value:
                        del d[key]
                    else:
                        d[key] = _trim(value)
            return d

        self.config = _trim(self.config)

    def save(self):
        self.trim()
        _validate_config(self.config)
        if not self.file:
            return
        self.file.parent.mkdir(parents=True, exist_ok=True)
        with self.file.open("w") as f:
            yaml.dump(self.config, f)


CONFIG_DEFAULT_MISSING = object()


def get_config(read_only=False) -> Config:
    """Get the package configuration, stored at config_dir()/config.yml."""
    config_file = settings.config_dir() / "config.yml"
    return Config(file=config_file, read_only=read_only)


@dataclass
class ConfigEntryRequest:
    key: str
    description: str | None = None
    default: Any = CONFIG_DEFAULT_MISSING
    dest: str | None = None
    converter: Callable[[str], Any] = str

    def __post_init__(self):
        if self.dest is None:
            self.dest = self.key.replace(".", "_")

    def resolve(self, config: Config, with_death=False) -> Any:
        try:
            value = config.get_strict(self.key)
        except KeyError:
            if self.default is CONFIG_DEFAULT_MISSING:
                if with_death:
                    import click

                    raise click.ClickException(f"Missing configuration key: {self.key}")
                raise KeyError(self.key)
            value = self.default
        return self.converter(value) if value is not None else value


class ConfigClient:
    """Declarative configuration requests for commands.

    Commands declare which config keys they need, then resolve them all at once.

    Usage:
        client = ConfigClient()
        client.wants_entry("dns.server", description="DNS server IP", default="8.8.8.8")
        client.wants_entry("dns.port", default="53")
        cfg = client.get(with_death=True)
        print(cfg.dns_server, cfg.dns_port)
    """

    def __init__(self):
        self.requests = []

    def wants_entry(self, key, *, description=None, default=CONFIG_DEFAULT_MISSING, dest=None, converter=str):
        self.requests.append(
            ConfigEntryRequest(key=key, description=description, default=default, dest=dest, converter=converter)
        )
        return self

    def get(self, *, config: Config | None = None, with_death=False) -> argparse.Namespace:
        if config is None:
            config = get_config()
        result = argparse.Namespace()
        for req in self.requests:
            value = req.resolve(config, with_death=with_death)
            setattr(result, req.dest, value)
        return result

    def help_text(self):
        if not self.requests:
            return ""
        lines = ["configuration:"]
        for req in self.requests:
            lines.append(f"  {req.key}:")
            if req.description:
                lines.append(f"    {req.description}")
            if req.default is not CONFIG_DEFAULT_MISSING:
                lines.append(f"    default: {req.default}")
            lines.append("")
        return "\n".join(lines)
