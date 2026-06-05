import click
import os
from guardian_runtime.optimizer.document_converter import DocumentConverter

@click.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--out", "-o", type=click.Path(), help="Output file path for the converted markdown.")
def convert_command(path: str, out: str | None) -> None:
    """Convert a PDF or DOCX file to pure Markdown to save tokens."""
    click.secho(f"⛨ GuardianRuntime Document Converter", fg="green", bold=True)
    click.echo(f"Processing: {path}...\n")
    
    try:
        converter = DocumentConverter()
        result = converter.convert(path)
        
        click.secho(f"✓ Conversion Complete!", fg="green")
        click.echo(f"  • Original File:  {os.path.basename(path)}")
        click.echo(f"  • Token Count:    {result.markdown_tokens:,}")
        
        if out:
            with open(out, "w", encoding="utf-8") as f:
                f.write(result.markdown)
            click.echo(f"  • Saved to:       {out}")
        else:
            # If no output file provided, print a preview and suggest using --out
            preview = result.markdown[:500].replace("\n", " ") + "..."
            click.echo(f"  • Preview:        {preview}")
            click.echo("\nTip: Use '--out filename.md' to save the output to a file.")
            
    except Exception as e:
        click.secho(f"\n✗ Conversion failed: {str(e)}", fg="red")
