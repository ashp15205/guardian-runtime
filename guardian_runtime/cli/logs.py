"""guardian_runtime logs — view local JSONL logs."""

import json

import click

from guardian_runtime.logging.local import LocalLogger


@click.command("logs")
@click.option("--tail", default=20, show_default=True, help="Number of recent log entries")
def logs_command(tail: int) -> None:
    """View local GuardianRuntime violation logs."""
    logger = LocalLogger()
    entries = logger.read_logs(tail=tail)
    if not entries:
        click.echo("No logs found for today.")
        return

    for entry in entries:
        click.echo(json.dumps(entry, ensure_ascii=False))
