from pathlib import Path

import typer

from .utils import run_command

app = typer.Typer(
    help="Manage isolated environment dependencies.",
    no_args_is_help=True,
)

DEFAULT_LIBS_PATH = Path("libs")
DEFAULT_LIBS_DEP_GROUP = "libs"


@app.command(
    # Allow any extra args to be passed to `uv`
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def vendor(
    group: str = typer.Option(
        default=DEFAULT_LIBS_DEP_GROUP,
        help="Dependency group to to vendor.",
    ),
    libs_path: Path = typer.Option(
        default=DEFAULT_LIBS_PATH,
        help="Directory to vendor the dependencies into.",
    ),
):
    """Install the isolated environment dependencies."""
    lock_file = libs_path / "vednor.txt"
    run_command(
        [
            "uv",
            "export",
            "--group",
            group,
            "--no-header",
            "--quiet",
            "--output-file",
            str(lock_file),
        ]
    )
    run_command(
        [
            "uv",
            "pip",
            "sync",
            lock_file,
            "--target",
            str(libs_path),
        ]
    )


@app.command(
    add_help_option=False,
    # Allow any extra args to be passed to `uv`
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def add(
    ctx: typer.Context,
    group: str = typer.Option(
        default=DEFAULT_LIBS_DEP_GROUP,
        help="Dependency group to to vendor.",
    ),
    libs_path: Path = typer.Option(
        default=DEFAULT_LIBS_PATH,
        help="Directory to vendor the dependencies into.",
    ),
):
    """Add packages to the isolated environment."""
    run_command(["uv", "add", "--frozen", "--group", group, *ctx.args])
    vendor(group=group, libs_path=libs_path)


@app.command(
    add_help_option=False,
    # Allow any extra args to be passed to `uv`
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def remove(
    ctx: typer.Context,
    group: str = typer.Option(
        default=DEFAULT_LIBS_DEP_GROUP,
        help="Dependency group to to vendor.",
    ),
    libs_path: Path = typer.Option(
        default=DEFAULT_LIBS_PATH,
        help="Directory to vendor the dependencies into.",
    ),
):
    """Remove packages from the isolated environment."""
    run_command(["uv", "remove", "--frozen", "--group", group, *ctx.args])
    vendor(group=group, libs_path=libs_path)


if __name__ == "__main__":
    app()
