"""guardian_runtime init — store license key locally."""

import click

from guardian_runtime.core.storage import LocalStorage


@click.command("init")
@click.option("--key", required=True, help="GuardianRuntime license key")
@click.option("--plan", default="free", show_default=True)
@click.option("--limit", default=10000, show_default=True, type=int)
def init_command(key: str, plan: str, limit: int) -> None:
    """Initialize GuardianRuntime with a license key."""
    storage = LocalStorage()
    storage.save_license(key=key, plan=plan, limit=limit)
    click.echo(f"GuardianRuntime initialized. Plan: {plan}. Run `guardian_runtime status` to verify.")
