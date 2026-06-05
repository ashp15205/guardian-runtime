"""CLI command: guardian_runtime proxy — start the local HTTP proxy server."""
from __future__ import annotations

import click


@click.command("proxy")
@click.option(
    "--port", "-p",
    default=8080,
    show_default=True,
    help="Port to listen on.",
)
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Host to bind to. Use 0.0.0.0 to expose on your network.",
)
@click.option(
    "--policy",
    default=None,
    help="Path to the GuardianRuntime policy YAML file (optional).",
)
@click.option(
    "--reload",
    is_flag=True,
    default=False,
    help="Enable auto-reload on policy file changes (dev mode).",
)
def proxy_command(port: int, host: str, policy: str | None, reload: bool):
    """
    Start the GuardianRuntime local proxy server.

    Point your AI agent at it by setting an environment variable:

    \b
    Claude Code:  ANTHROPIC_BASE_URL=http://localhost:8080 claude
    Aider:        OPENAI_BASE_URL=http://localhost:8080 aider
    Cursor:       Settings → API Base → http://localhost:8080
    """
    import pathlib
    import sys

    try:
        import uvicorn
    except ImportError:
        click.echo("❌ uvicorn is not installed. Run: pip install guardian-runtime", err=True)
        sys.exit(1)

    if policy:
        policy_path = pathlib.Path(policy)
        if not policy_path.exists():
            click.echo(f"❌ Policy file not found: {policy}", err=True)
            click.echo("   Create one with: guardian_runtime validate --help", err=True)
            sys.exit(1)
        policy_arg = str(policy_path)
        policy_display = str(policy_path)
    else:
        policy_arg = None
        policy_display = "Default (Zero-Config)"

    click.echo("\n")
    click.echo("  ⛨  GuardianRuntime Runtime Proxy")
    click.echo(f"  ─────────────────────────────────────────")
    click.echo(f"  Listening on : http://{host}:{port}")
    click.echo(f"  Policy       : {policy_display}")
    click.echo(f"  Dashboard    : guardian_runtime dashboard (run in another terminal)")
    click.echo(f"")
    click.echo(f"  Agent setup:")
    click.echo(f"    Claude Code  →  ANTHROPIC_BASE_URL=http://localhost:{port} claude")
    click.echo(f"    Aider        →  OPENAI_BASE_URL=http://localhost:{port} aider")
    click.echo(f"    Cursor       →  Settings → API Base → http://localhost:{port}")
    click.echo(f"")
    click.echo(f"  Press Ctrl+C to stop.\n")

    from guardian_runtime.proxy.server import create_proxy_app

    app = create_proxy_app(policy_arg)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",  # suppress verbose uvicorn logs; GuardianRuntime logs what matters
        reload=reload,
    )
