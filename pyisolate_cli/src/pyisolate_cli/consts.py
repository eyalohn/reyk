from pathlib import Path

import typer

DEFAULT_LIBS_PATH = Path("libs")
DEFAULT_LIBS_DEP_GROUP = "libs"

LOCK_FILE_NAME = "vendor.txt"


option_group = typer.Option(
    default=DEFAULT_LIBS_DEP_GROUP,
    help="Dependency group to to vendor.",
)
option_libs_path = typer.Option(
    default=DEFAULT_LIBS_PATH,
    help="Directory to vendor the dependencies into.",
)
