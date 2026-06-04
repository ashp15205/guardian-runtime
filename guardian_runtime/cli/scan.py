"""guardian_runtime scan — quickly test a string against the InputGuard."""

import click
from guardian_runtime.guards.input_guard import InputGuard
from guardian_runtime.core.policy import AgentPolicy

@click.command("scan")
@click.argument("text")
def scan_command(text: str) -> None:
    """Quickly scan a string for PII or secrets."""
    guard = InputGuard()
    policy = AgentPolicy(name="CLI Test")
    result = guard.check(text, policy)
    
    if result.allowed:
        click.secho("✅ Scan passed: No threats detected.", fg="green")
    else:
        click.secho("🛑 Scan failed! Threats detected:", fg="red", bold=True)
        for v in result.violations:
            click.secho(f"  - [{v.severity.upper()}] {v.type}: {v.detail}", fg="yellow")
