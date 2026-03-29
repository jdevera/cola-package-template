#!/usr/bin/env python3
"""Example Python/Click command.

Demonstrates:
    - Click group with subcommands
    - @output_format_options for multi-format output
    - resolve_format_from_options for format resolution
    - ConfigClient for reading configuration values
    - cola.settings for launcher context
    - add_cola_completion_command for launcher completion
"""

import json
import os

import click
from rich.console import Console

from cola.cli import add_cola_completion_command
from cola.config import ConfigClient
from cola.output import OutputFormat, output_format_options, resolve_format_from_options
from cola.settings import full_command_name


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def main():
    """Example greeting command showing template patterns."""
    pass


add_cola_completion_command(main)


@main.command()
@click.pass_context
@output_format_options(
    OutputFormat.PLAIN,
    OutputFormat.JSON,
    OutputFormat.RICH,
    default=OutputFormat.PLAIN,
)
@click.argument("name", default="World")
def say(ctx, name, output_format, output_plain, output_json, output_rich):
    """Greet someone using the configured greeting."""
    # Read greeting from config (with a sensible default)
    client = ConfigClient()
    client.wants_entry("example.greeting", description="Greeting word", default="Hello")
    cfg = client.get()

    fmt = resolve_format_from_options(
        ctx,
        output_format=output_format,
        output_plain=output_plain,
        output_json=output_json,
        output_rich=output_rich,
    )

    greeting = f"{cfg.example_greeting}, {name}!"

    if fmt == OutputFormat.JSON:
        click.echo(json.dumps({"greeting": cfg.example_greeting, "name": name, "message": greeting}))
    elif fmt == OutputFormat.RICH:
        Console().print(f"[bold green]{greeting}[/bold green]")
    else:
        click.echo(greeting)


if __name__ == "__main__":
    prog_name = full_command_name() if "COLA_FULL_COMMAND_NAME" in os.environ else "mypkg examples greet"
    main(prog_name=prog_name)
