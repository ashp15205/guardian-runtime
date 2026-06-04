"""guardian_runtime init — first-time environment setup."""

import click
from pathlib import Path


@click.command("init")
def init_command() -> None:
    """Set up GuardianRuntime local environment (creates log directory)."""
    log_dir = Path.home() / ".guardian_runtime" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    click.echo("✅ GuardianRuntime initialized.")
    click.echo(f"   Log directory: {log_dir}")
    click.echo("   Run `guardian_runtime status` to verify.")
