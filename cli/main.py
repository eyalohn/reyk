import subprocess
from pathlib import Path

import typer

app = typer.Typer(
    help="Manage isolated environment dependencies.",
    no_args_is_help=True,
)

DEFAULT_LIBS_PATH = Path("libs")
DEFAULT_LIBS_DEP_GROUP = "libs"


@app.command()
def vendor(
    group: str = typer.Option(
        default=DEFAULT_LIBS_DEP_GROUP, help="The dependency group to vendor."
    ),
    libs_path: Path = typer.Option(
        default=DEFAULT_LIBS_PATH, help="The directory to vendor the dependencies into."
    ),
):
    """Install the isolated environment dependencies."""
    cmd = [
        "uv",
        "pip",
        "install",
        "--group",
        group,
        "--target",
        str(libs_path),
    ]
    raise typer.Exit(subprocess.call(cmd))


@app.command(
    add_help_option=False,
    # Allow passing arbitrary extra arguments to the underlying command
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def add(ctx: typer.Context):
    """Add packages to the isolated environment."""
    cmd = ["uv", "add", *ctx.args]
    if "--group" not in ctx.args:
        cmd += ["--group", DEFAULT_LIBS_DEP_GROUP]
    raise typer.Exit(subprocess.call(cmd))


@app.command(
    add_help_option=False,
    # Allow passing arbitrary extra arguments to the underlying command
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    },
)
def remove(ctx: typer.Context):
    """Remove packages from the isolated environment."""
    cmd = ["uv", "remove", *ctx.args]
    if "--group" not in ctx.args:
        cmd += ["--group", DEFAULT_LIBS_DEP_GROUP]
    raise typer.Exit(subprocess.call(cmd))


if __name__ == "__main__":
    app()
