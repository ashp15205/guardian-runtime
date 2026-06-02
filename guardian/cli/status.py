"""guardian status — show license and usage."""

import click

from guardian.core.storage import LocalStorage


@click.command("status")
def status_command() -> None:
    """Show current license, plan, and usage."""
    storage = LocalStorage()
    config = storage.load_license()
    usage = storage.get_usage()
    allowed, used, limit = storage.check_usage_limit()

    if config:
        key = config.get("license_key", "")
        masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else key
        click.echo(f"License: {masked}")
        click.echo(f"Plan: {config.get('plan', 'free')}")
    else:
        click.echo("License: not configured (offline free tier)")
        click.echo("Plan: free")

    click.echo(f"Checks this month: {used} / {limit}")
    click.echo(f"Last sync: {usage.get('last_sync') or 'never'}")
    click.echo(f"Status: {'ACTIVE' if allowed else 'LIMIT REACHED'}")
