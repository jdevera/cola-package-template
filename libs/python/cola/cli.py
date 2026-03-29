"""CLI utilities for Click-based commands.

Provides reusable Click utilities for Command Launcher packages,
including dynamic completion support.
"""

import click


def add_cola_completion_command(group: click.Group) -> click.Group:
    """Add a _cola_completion subcommand to a Click group.

    The launcher uses validArgsCmd to call this for dynamic shell completion.
    It introspects the Click group and outputs all valid subcommands and options.

    Usage:
        @click.group()
        def main():
            pass

        add_cola_completion_command(main)

    In the manifest, wire it up with:
        validArgsCmd: ['{{.PackageDir}}/pyrun.sh', 'commands/path/to/cmd.py', '_cola_completion']

    Args:
        group: A Click group to add the completion command to.

    Returns:
        The same group (for chaining).
    """

    @group.command(name="_cola_completion", hidden=True)
    @click.argument("subcommand", required=False)
    def completion(subcommand: str | None) -> None:
        """Output completion data for COLA launcher integration."""
        commands = {name: cmd for name, cmd in group.commands.items() if not getattr(cmd, "hidden", False)}

        def output_command_params(cmd: click.Command) -> None:
            for param in cmd.params:
                if isinstance(param, click.Option):
                    for opt in param.opts:
                        click.echo(opt)
                    for opt in param.secondary_opts:
                        click.echo(opt)
                elif isinstance(param, click.Argument):
                    click.echo(f"<{param.name}>")

        if subcommand is None:
            for name in sorted(commands.keys()):
                click.echo(name)
            seen: set[str] = set()
            for cmd in commands.values():
                for param in cmd.params:
                    if isinstance(param, click.Option):
                        for opt in param.opts:
                            if opt not in seen:
                                seen.add(opt)
                                click.echo(opt)
                        for opt in param.secondary_opts:
                            if opt not in seen:
                                seen.add(opt)
                                click.echo(opt)
        elif subcommand in commands:
            output_command_params(commands[subcommand])
        else:
            click.echo(f"Unknown subcommand: {subcommand}", err=True)
            raise SystemExit(1)

    return group
