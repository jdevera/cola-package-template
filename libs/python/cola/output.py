"""Output format handling for CLI commands.

Provides a decorator and resolver for standardizing output format options
across all CLI commands in a Command Launcher package.

Architecture:
    - OutputFormatSpec: frozen dataclass identifying a format (name, flag, help text)
    - OutputFormat: pre-defined constants for common formats (JSON, CSV, TABLE, etc.)
    - @output_format_options: decorator adding --output-format/-f and individual flags
    - resolve_format_from_options: resolves which format the user selected

Design decisions:
    - Each command explicitly declares which formats it supports and its default.
      There is no "auto" format — be explicit.
    - Individual flags (--json, --csv) take precedence over --output-format/-f.
    - Only one format can be active at a time — multiple flags is an error.
    - Commands implement their own output writing based on the resolved format.
      There is no centralized writer — each command knows its own data best.
    - Custom formats are supported: create an OutputFormatSpec for command-specific
      formats (e.g., RAW = OutputFormatSpec("raw", "--raw", "Output raw text")).

Usage:
    from cola.output import OutputFormat, output_format_options, resolve_format_from_options

    @click.command()
    @click.pass_context
    @output_format_options(OutputFormat.JSON, OutputFormat.TABLE, default=OutputFormat.TABLE)
    def main(ctx, output_format, output_json, output_table):
        fmt = resolve_format_from_options(ctx, output_format=output_format,
                                          output_json=output_json, output_table=output_table)
        data = get_data()
        if fmt == OutputFormat.JSON:
            click.echo(json.dumps(data, indent=2))
        else:
            # render a table with Rich, etc.
            ...
"""

from dataclasses import dataclass
from typing import Any, Callable, TypeVar

import click

F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class OutputFormatSpec:
    """Specification for an output format.

    Attributes:
        name: The format identifier (e.g., "json", "table")
        flag: The CLI flag (e.g., "--json", "--table")
        help: Help text shown in --help output
    """

    name: str
    flag: str
    help: str


class OutputFormat:
    """Pre-defined output formats.

    Use these constants in @output_format_options. For command-specific formats,
    create your own OutputFormatSpec:

        RAW = OutputFormatSpec("raw", "--raw", "Output raw Markdown")
    """

    TABLE = OutputFormatSpec("table", "--table", "Output as table")
    JSON = OutputFormatSpec("json", "--json", "Output as JSON")
    TSV = OutputFormatSpec("tsv", "--tsv", "Output as TSV")
    CSV = OutputFormatSpec("csv", "--csv", "Output as CSV")
    PLAIN = OutputFormatSpec("plain", "--plain", "Output as plain text")
    MARKDOWN = OutputFormatSpec("markdown", "--markdown", "Output as Markdown")
    RICH = OutputFormatSpec("rich", "--rich", "Pretty-print with Rich")


def resolve_format_from_options(
    ctx: click.Context,
    output_format: str | None = None,
    **format_flags: bool,
) -> OutputFormatSpec:
    """Resolve which output format the user selected.

    Retrieves supported formats and default from function metadata (set by
    @output_format_options), validates mutual exclusivity, and returns the
    resolved OutputFormatSpec.

    Individual flags (--json, --csv) take precedence over --output-format.
    If nothing is specified, returns the default.

    Args:
        ctx: Click context (must be from a command decorated with @output_format_options)
        output_format: Value of --output-format/-f option
        **format_flags: Individual flag values (e.g., output_json=True)

    Returns:
        The resolved OutputFormatSpec instance.

    Raises:
        click.UsageError: If multiple format flags are set simultaneously.
        click.BadParameter: If the specified format is not supported by this command.
    """
    callback = ctx.command.callback
    supported_formats: list[OutputFormatSpec] = getattr(callback, "__output_formats__", [])
    default_format: OutputFormatSpec | None = getattr(callback, "__output_default__", None)

    if not supported_formats:
        raise click.ClickException("Command not decorated with @output_format_options or metadata missing")
    if default_format is None:
        raise click.ClickException("Default format not set in decorator")

    format_by_name: dict[str, OutputFormatSpec] = {fmt.name: fmt for fmt in supported_formats}

    # Find which individual format flags are set
    set_flags: list[str] = []
    for fmt in supported_formats:
        param_name = f"output_{fmt.name}"
        if format_flags.get(param_name, False):
            set_flags.append(fmt.name)

    if len(set_flags) > 1:
        format_list = ", ".join(f"--{flag}" for flag in set_flags)
        raise click.UsageError(f"Only one output format can be specified. Found: {format_list}")

    # Individual flags take precedence over --output-format
    resolved_format_str: str | None = None
    if set_flags:
        resolved_format_str = set_flags[0]
    elif output_format is not None and output_format != default_format.name:
        resolved_format_str = output_format
    else:
        resolved_format_str = None

    if resolved_format_str is None:
        return default_format

    if resolved_format_str in format_by_name:
        return format_by_name[resolved_format_str]

    supported_names = [fmt.name for fmt in supported_formats]
    raise click.BadParameter(
        f"Format '{resolved_format_str}' is not supported. Supported: {', '.join(supported_names)}"
    )


def output_format_options(*formats: OutputFormatSpec, default: OutputFormatSpec) -> Callable[[F], F]:
    """Decorator adding output format options to a Click command.

    Adds:
    - --output-format / -f choice option listing supported formats
    - Individual flags for each format (e.g., --json, --csv, --table)
    - Metadata on the function for resolve_format_from_options to use

    The decorated function must use @click.pass_context.

    Args:
        *formats: Supported output format specifications (at least one required)
        default: Default format when nothing is specified (must be in formats)

    Example:
        @click.command()
        @click.pass_context
        @output_format_options(OutputFormat.JSON, OutputFormat.CSV, default=OutputFormat.JSON)
        def main(ctx, output_format, output_json, output_csv):
            fmt = resolve_format_from_options(ctx, output_format=output_format,
                                              output_json=output_json, output_csv=output_csv)
    """
    if not formats:
        raise ValueError("At least one format must be specified")

    supported_formats = list(formats)
    if default not in supported_formats:
        raise ValueError(f"Default format {default.name} must be in supported formats")

    def decorator(func: F) -> F:
        func.__output_formats__ = supported_formats  # type: ignore[attr-defined]
        func.__output_default__ = default  # type: ignore[attr-defined]

        format_names = [fmt.name for fmt in supported_formats]

        func = click.option(
            "--output-format",
            "-f",
            "output_format",
            type=click.Choice(format_names, case_sensitive=False),
            default=default.name,
            show_default=True,
            help=f"Output format. Supported: {', '.join(format_names)}",
        )(func)

        for fmt in supported_formats:
            param_name = f"output_{fmt.name}"
            func = click.option(
                fmt.flag,
                param_name,
                is_flag=True,
                default=False,
                help=fmt.help,
            )(func)

        return func

    return decorator
