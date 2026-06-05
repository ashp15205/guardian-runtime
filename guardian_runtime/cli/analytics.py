import click
from datetime import datetime, timezone
from guardian_runtime.core.storage import LocalStorage

@click.command("analytics")
@click.option("--all", "show_all", is_flag=True, help="Show all-time analytics instead of just today.")
def analytics_command(show_all: bool) -> None:
    """View session analytics and cost tracking for your local tools."""
    storage = LocalStorage()
    
    date_filter = None
    if not show_all:
        date_filter = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
    analytics = storage.get_analytics(date_filter=date_filter)
    
    time_label = "All-Time" if show_all else "Today"
    
    click.echo("\n")
    click.secho(f"  ⛨  GuardianRuntime Session Analytics ({time_label})", fg="green", bold=True)
    click.echo("  ──────────────────────────────────────────────")
    
    if not analytics:
        click.echo("\n  No analytics data found for this period.")
        click.echo("  Run `guardian_runtime proxy` and connect an agent to see usage.")
        click.echo("\n")
        return

    for tool, data in analytics.items():
        click.secho(f"\n  {tool}", fg="cyan", bold=True)
        click.echo(f"  Cost:       ${data['cost']:.4f}")
        click.echo(f"  Requests:   {data['requests']}")
        
        blocked_count = data['blocked']
        if blocked_count > 0:
            reasons = ", ".join(f"{count} {r}" for r, count in data['block_reasons'].items())
            click.secho(f"  Blocked:    {blocked_count} ({reasons})", fg="red")
        else:
            click.echo(f"  Blocked:    0")
            
        click.echo(f"  Tokens:     {data['tokens']:,}")

    click.echo("\n")
