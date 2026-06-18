import click
import os
from pathlib import Path

try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None

from guardian_runtime.finops.token_counter import count_tokens
from guardian_runtime.finops.cost_calculator import estimate_cost

@click.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--out", "-o", type=click.Path(), help="Output file path for the converted markdown.")
def convert_command(path: str, out: str | None) -> None:
    """Convert a file to Markdown to save tokens."""
    if not MarkItDown:
        click.secho("✗ markitdown package not installed. Run: pip install markitdown", fg="red")
        return
        
    in_path = Path(path)
    if not out:
        out = str(in_path.with_suffix(".md"))
        
    try:
        md = MarkItDown()
        result = md.convert(str(in_path))
        md_text = result.text_content
        
        with open(out, "w", encoding="utf-8") as f:
            f.write(md_text)
            
        tokens = count_tokens(md_text)
        cost_gpt4o = estimate_cost(input_tokens=tokens, output_tokens=0, model="gpt-4o")
        cost_sonnet = estimate_cost(input_tokens=tokens, output_tokens=0, model="claude-3-5-sonnet")
        
        click.secho(f"✓ Converted: {in_path.name} → {Path(out).name}", fg="green")
        click.echo(f"  • Token count: ~{tokens:,} tokens")
        click.echo(f"  • Estimated cost if sent to GPT-4o: ${cost_gpt4o:.4f}")
        click.echo(f"  • Estimated cost if sent to Claude Sonnet: ${cost_sonnet:.4f}")
        
    except Exception as e:
        click.secho(f"✗ Conversion failed: {str(e)}", fg="red")
