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

    # Aggregate tokens and cost from logs
    from guardian.logging.local import LOGS_DIR
    import json
    
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
