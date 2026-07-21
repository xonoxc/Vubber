import typer
from dotenv import load_dotenv

from cli.cmd import register
from utils.logging import configure_logging

load_dotenv()
configure_logging()

app = typer.Typer(name="vubber", help="YouTube video dubbing pipeline")
register(app)
