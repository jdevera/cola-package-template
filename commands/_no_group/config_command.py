#!/usr/bin/env python3
"""Configuration management command.

Provides get/set/delete/registry/status subcommands for managing
the package's YAML-backed configuration.
"""

import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.text import Text

from cola.config import Config, ConfigRegistry
from cola.settings import full_command_name, launcher_name, package_dir

stderr_console = Console(stderr=True)


def load_registry() -> ConfigRegistry:
    registry_file = package_dir() / "config_registry.yml"
    return ConfigRegistry.load(registry_file)


def config_file() -> Path:
    from cola.settings import config_dir

    return config_dir() / "config.yml"


def warn_unrecognized_keys(config: Config, registry: ConfigRegistry):
    for key in config.flat.keys():
        if not registry.has_key(key):
            stderr_console.print(f"[yellow]Warning:[/yellow] '{key}' is not a recognized configuration key")


def print_schema(registry: ConfigRegistry, config: Config | None = None):
    console = Console()

    if not registry.groups and not registry.top_level_keys:
        console.print("No configuration keys registered.")
        return

    def print_key(key, full_key, indent=""):
        if config is not None:
            current_value = config.get(full_key)
            if current_value is not None:
                console.print(f"{indent}[cyan]{full_key}[/cyan] = {current_value}")
            else:
                line = Text(f"{indent}{full_key}", style="cyan")
                line.append("  (not set)", style="dim")
                console.print(line)
                if key.example:
                    console.print(f"{indent}  [dim]example: {key.example}[/dim]")
        else:
            console.print(f"{indent}[cyan]{full_key}[/cyan]")
            console.print(f"{indent}  {key.description}")
            if key.example:
                console.print(f"{indent}  [dim]example: {key.example}[/dim]")

    top_level_keys = list(registry.all_top_level_keys())
    for key in top_level_keys:
        print_key(key, key.name)

    for group in registry.all_groups():
        if top_level_keys or group != list(registry.all_groups())[0]:
            console.print()
        console.print(f"[bold]{group.name}[/bold]: {group.description}")
        for key in group.keys.values():
            full_key = group.full_key(key.name)
            print_key(key, full_key, indent="  ")


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--file", "-f", "config_file_path", type=click.Path(path_type=Path), default=None, help="Configuration file path")
@click.pass_context
def cli(ctx, config_file_path: Path | None):
    """Manage the package configuration.

    Use subcommands to get, set, or delete configuration values.
    Use 'registry' to see all valid configuration keys.
    """
    ctx.ensure_object(dict)
    ctx.obj["config_file"] = config_file_path or config_file()
    ctx.obj["registry"] = load_registry()

    if ctx.invoked_subcommand is None:
        ctx.invoke(cmd_get)


@cli.command("get")
@click.argument("key", required=False)
@click.option("--format", "-F", "fmt", type=click.Choice(["plain", "yaml", "json"]), default="plain", help="Output format")
@click.option("--quiet", "-q", is_flag=True, help="Suppress error messages")
@click.pass_context
def cmd_get(ctx, key: str | None, fmt: str, quiet: bool):
    """Get configuration value(s).

    If KEY is provided, show that specific value.
    If no KEY is provided, show all configuration.
    """
    config = Config(file=ctx.obj["config_file"])
    registry = ctx.obj["registry"]
    prog_name = f"{launcher_name()} cfg"

    if key is None:
        warn_unrecognized_keys(config, registry)
        flat = config.flat
        if not flat:
            click.echo("No configuration set.")
            return

        if fmt == "yaml":
            click.echo(yaml.dump(config.config, explicit_start=True).strip())
        elif fmt == "json":
            import json

            click.echo(json.dumps(config.config, indent=2))
        else:
            width = max(len(k) for k in flat.keys()) + 1
            for k, v in flat.items():
                click.echo(f"{k:<{width}}: {v}")
    else:
        value = config.get(key)
        if value is None:
            if not registry.has_key(key):
                if quiet:
                    sys.exit(2)
                raise click.ClickException(f"Unknown config key: '{key}'. Run '{prog_name} registry' to see valid keys.")
            if quiet:
                sys.exit(1)
            raise click.ClickException(f"Key '{key}' not found in configuration")
        if isinstance(value, dict):
            if fmt == "yaml":
                click.echo(yaml.dump(value, explicit_start=True).strip())
            elif fmt == "json":
                import json

                click.echo(json.dumps(value, indent=2))
            else:
                sub_config = Config(config_data=value)
                width = max(len(k) for k in sub_config.flat.keys()) + 1
                for k, v in sub_config.flat.items():
                    click.echo(f"{key}.{k:<{width}}: {v}")
        else:
            click.echo(value)


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def cmd_set(ctx, key: str, value: str):
    """Set a configuration value.

    KEY must be a registered configuration key.
    """
    config = Config(file=ctx.obj["config_file"])
    registry = ctx.obj["registry"]

    if not registry.has_key(key):
        raise click.ClickException(
            f"'{key}' is not a recognized configuration key. " f"Run '{launcher_name()} cfg registry' to see valid keys."
        )
    config.set(key, value)


@cli.command("del")
@click.argument("key")
@click.pass_context
def cmd_del(ctx, key: str):
    """Delete a configuration key."""
    config = Config(file=ctx.obj["config_file"])
    try:
        config.delete(key)
    except KeyError:
        raise click.ClickException(f"Key '{key}' not found in configuration")


@cli.command("delete")
@click.argument("key")
@click.pass_context
def cmd_delete(ctx, key: str):
    """Delete a configuration key (alias for 'del')."""
    ctx.invoke(cmd_del, key=key)


@cli.command("registry")
@click.pass_context
def cmd_registry(ctx):
    """Show all registered configuration keys."""
    registry = ctx.obj["registry"]
    print_schema(registry)


@cli.command("status")
@click.pass_context
def cmd_status(ctx):
    """Show schema with current configuration values."""
    config = Config(file=ctx.obj["config_file"])
    registry = ctx.obj["registry"]
    print_schema(registry, config)


@cli.command("complete")
@click.pass_context
def cmd_complete(ctx):
    """Output valid options and subcommands for shell completion."""
    group = ctx.parent.command

    for param in group.params:
        for opt in param.opts:
            click.echo(opt)

    for opt in group.context_settings.get("help_option_names", ["--help"]):
        click.echo(opt)

    for name in group.commands:
        click.echo(name)


def main(argv=None):
    prog_name = full_command_name() if "COLA_FULL_COMMAND_NAME" in __import__("os").environ else "mypkg cfg"
    try:
        cli.main(args=argv, prog_name=prog_name, standalone_mode=False)
    except click.ClickException as e:
        click.echo(f"Error: {e.message}", err=True)
        sys.exit(1)
    except click.Abort:
        sys.exit(1)


if __name__ == "__main__":
    main()
