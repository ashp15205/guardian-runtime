"""guardian_runtime status — show current usage and system state."""

import json
import click

from guardian_runtime.core.storage import LocalStorage


@click.command("status")
def status_command() -> None:
    """Show current usage analytics and active guards."""
    storage = LocalStorage()

    click.echo("⛨  GuardianRuntime — System Status")
    click.echo("─" * 40)
    click.echo(f"Status:       ACTIVE (open source, no limits)")

    # Aggregate tokens and cost from logs
    from guardian_runtime.logging.local import LOGS_DIR

    total_original_in = 0
    total_in = 0
    total_saved = 0
    total_out = 0
    total_cost = 0.0

    if LOGS_DIR.exists():
        for log_file in LOGS_DIR.glob("*.jsonl"):
            try:
                for line in log_file.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    meta = data.get("metadata", {})

                    in_tok = meta.get("input_tokens", 0)
                    total_in += in_tok
                    total_out += meta.get("output_tokens", 0)
                    total_cost += meta.get("estimated_cost_usd", 0.0)

                    total_original_in += meta.get("original_input_tokens", in_tok)
                    total_saved += meta.get("saved_tokens", 0)
            except Exception:
                pass

    click.echo("\n--- Usage Analytics ---")
    click.echo(f"Original Input Tokens:  {total_original_in:,}")
    click.echo(f"Optimized Input Tokens: {total_in:,} (-{total_saved:,} saved)")
    click.echo(f"Total Output Tokens:    {total_out:,}")
    click.echo(f"Estimated Cost:         ${total_cost:.6f} USD")
