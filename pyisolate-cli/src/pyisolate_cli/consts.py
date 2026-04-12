from pathlib import Path

import typer

DEFAULT_LIBS_PATH = Path("./libs")
DEFAULT_LIBS_DEPS_GROUP = "libs"

LOCK_FILE_NAME = "vendor.lock"


option_group = typer.Option(
    default=DEFAULT_LIBS_DEPS_GROUP,
    help="Dependency group to to vendor.",  # https://docs.astral.sh/uv/concepts/projects/dependencies/#dependency-groups
)
option_libs_path = typer.Option(
    default=DEFAULT_LIBS_PATH,
    help="Directory to vendor the dependencies into.",
)
