import click
import pytest
from click.testing import CliRunner

from cola.output import OutputFormat, OutputFormatSpec, output_format_options, resolve_format_from_options


def make_test_command(*formats, default):
    """Helper to create a Click command with output_format_options for testing."""

    @click.command()
    @click.pass_context
    @output_format_options(*formats, default=default)
    def cmd(ctx, output_format, **kwargs):
        fmt = resolve_format_from_options(ctx, output_format=output_format, **kwargs)
        click.echo(f"format={fmt.name}")

    return cmd


def test_default_format():
    cmd = make_test_command(OutputFormat.JSON, OutputFormat.TABLE, default=OutputFormat.TABLE)
    result = CliRunner().invoke(cmd, [])
    assert result.exit_code == 0
    assert "format=table" in result.output


def test_explicit_format_flag():
    cmd = make_test_command(OutputFormat.JSON, OutputFormat.TABLE, default=OutputFormat.TABLE)
    result = CliRunner().invoke(cmd, ["--json"])
    assert result.exit_code == 0
    assert "format=json" in result.output


def test_output_format_option():
    cmd = make_test_command(OutputFormat.JSON, OutputFormat.TABLE, default=OutputFormat.TABLE)
    result = CliRunner().invoke(cmd, ["-f", "json"])
    assert result.exit_code == 0
    assert "format=json" in result.output


def test_multiple_flags_error():
    cmd = make_test_command(OutputFormat.JSON, OutputFormat.TABLE, OutputFormat.CSV, default=OutputFormat.TABLE)
    result = CliRunner().invoke(cmd, ["--json", "--csv"])
    assert result.exit_code != 0
    assert "Only one output format" in result.output


def test_individual_flag_precedence():
    cmd = make_test_command(OutputFormat.JSON, OutputFormat.TABLE, default=OutputFormat.TABLE)
    result = CliRunner().invoke(cmd, ["--json", "-f", "table"])
    assert result.exit_code == 0
    assert "format=json" in result.output


def test_custom_format():
    RAW = OutputFormatSpec("raw", "--raw", "Raw output")
    cmd = make_test_command(OutputFormat.JSON, RAW, default=RAW)
    result = CliRunner().invoke(cmd, [])
    assert "format=raw" in result.output

    result = CliRunner().invoke(cmd, ["--json"])
    assert "format=json" in result.output


def test_no_formats_raises():
    with pytest.raises(ValueError, match="At least one format"):
        output_format_options(default=OutputFormat.JSON)


def test_default_not_in_formats_raises():
    with pytest.raises(ValueError, match="must be in supported formats"):
        output_format_options(OutputFormat.JSON, default=OutputFormat.TABLE)
