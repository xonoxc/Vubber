import typer

app = typer.Typer(name="vubber", help="YouTube video dubbing pipeline")


@app.command()
def dub(url: str = typer.Argument(help="YouTube video URL")) -> None:
    """Download, transcribe, translate, and dub a YouTube video."""
    typer.echo(f"Processing: {url}")


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("vubber 0.1.0")
