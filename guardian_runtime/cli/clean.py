"""guardian_runtime clean — delete all local tracking data and policies."""

import shutil
import click
from pathlib import Path

@click.command("clean")
def clean_command() -> None:
    """Delete all local tracking data, logs, and policies (~/.guardian_runtime)."""
    guardian_dir = Path.home() / ".guardian_runtime"
    
    if not guardian_dir.exists():
        click.echo("✨ System is already clean. (No ~/.guardian_runtime directory found)")
        return
        
    click.confirm(
        f"⚠️  WARNING: This will permanently delete your local analytics, logs, and custom policies in {guardian_dir}.\nDo you want to continue?",
        abort=True
    )
    
    try:
        shutil.rmtree(guardian_dir)
        click.echo("🗑️  Successfully deleted ~/.guardian_runtime.")
    except Exception as e:
        click.echo(f"❌ Failed to delete directory: {e}", err=True)
