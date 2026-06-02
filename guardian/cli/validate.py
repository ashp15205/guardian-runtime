"""guardian validate — validate a YAML policy file."""

import click

from guardian.core.policy import PolicyValidationError, load_policy


@click.command("validate")
@click.argument("policy_file", type=click.Path(exists=True))
def validate_command(policy_file: str) -> None:
    """Validate a Guardian YAML policy file."""
    try:
        policy = load_policy(policy_file)
    except PolicyValidationError as exc:
        click.echo(f"Policy invalid: {exc}", err=True)
        raise SystemExit(1) from exc

    agent_count = len(policy.agents)
    click.echo(f"Policy valid: {policy.name} ({agent_count} agent(s) configured).")
