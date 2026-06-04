"""CLI command: guardian_runtime dashboard — open local observability dashboard."""
from __future__ import annotations

import click


@click.command("dashboard")
@click.option(
    "--port", "-p",
    default=3001,
    show_default=True,
    help="Port to serve the dashboard on.",
)
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Host to bind the dashboard to.",
)
@click.option(
    "--no-browser",
    is_flag=True,
    default=False,
    help="Don't auto-open the browser.",
)
def dashboard_command(port: int, host: str, no_browser: bool):
    """
    Start the GuardianRuntime local observability dashboard.

    Opens a dark-mode web UI at http://localhost:3001 showing:
    real-time requests, violations, token usage, and costs.
    Reads from ~/.guardian_runtime/logs/ — no data ever leaves your machine.
    """
    import sys
    import threading
    import time
    import webbrowser

    try:
        import uvicorn
    except ImportError:
        click.echo("❌ uvicorn is not installed. Run: pip install guardian-runtime", err=True)
        sys.exit(1)

    url = f"http://{host}:{port}"

    click.echo("\n")
    click.echo("  ⛨  GuardianRuntime Dashboard")
    click.echo(f"  ─────────────────────────────────────────")
    click.echo(f"  URL          : {url}")
    click.echo(f"  Data source  : ~/.guardian_runtime/logs/")
    click.echo(f"  Auto-refresh : every 5 seconds")
    click.echo(f"")
    click.echo(f"  Press Ctrl+C to stop.\n")

    if not no_browser:
        def _open():
            time.sleep(1.2)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    from guardian_runtime.dashboard.server import create_dashboard_app

    app = create_dashboard_app()
    uvicorn.run(app, host=host, port=port, log_level="warning")
