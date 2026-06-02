"""Guardian CLI — entry point for all `guardian` commands."""

import click

from guardian.cli.init import init_command
from guardian.cli.logs import logs_command
from guardian.cli.status import status_command
from guardian.cli.validate import validate_command


@click.group()
@click.version_option(package_name="guardian-runtime")
def cli() -> None:
    """Guardian Runtime — Local-first AI governance."""


cli.add_command(init_command, "init")
cli.add_command(validate_command, "validate")
cli.add_command(status_command, "status")
cli.add_command(logs_command, "logs")
