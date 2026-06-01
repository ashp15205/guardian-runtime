"""Guardian CLI — entry point for all `guardian` commands."""

import click


@click.group()
@click.version_option(package_name="guardian-runtime")
def cli():
    """⛨ Guardian Runtime — Local-first AI governance."""
    pass


# Commands will be registered here as they are built
# from guardian.cli.init import init_command
# from guardian.cli.validate import validate_command
# from guardian.cli.status import status_command
# from guardian.cli.logs import logs_command
