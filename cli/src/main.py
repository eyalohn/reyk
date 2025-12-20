from pathlib import Path

import typer

from .common_options import option_group, option_libs_path
from .consts import LOCK_FILE_NAME
from .utils import run_command

app = typer.Typer(
    help="Manage isolated environment dependencies.",
    no_args_is_help=True,
)


@app.command(
    help="Vendor the isolated environment dependencies.",
    # Allow any extra args to be passed to `uv`
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def vendor(group: str = option_group, libs_path: Path = option_libs_path):
    """Install the isolated environment dependencies."""
    # `uv pip sync` is the only command that supports installing to a custom target,
    # but it requires a lock file. Therefore, we first export the lock file of the libs group
    # and then use it to install the packages to the desired target.
    lock_file = libs_path / LOCK_FILE_NAME
    run_command(
        [
            "uv",
            "export",
            "--group",
            group,
            "--no-header",
            "--quiet",
            "--no-emit-project",
            "--output-file",
            lock_file,
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
    ctx: typer.Context, group: str = option_group, libs_path: Path = option_libs_path
):
    """Add packages to the isolated environment."""
    # The `uv add` command doesn't support installing to a custom target,
    # so we use `--frozen` just to append the package to the `pyproject.toml`.
    # Then we call `vendor` to actually install the packages to the desired libs target.
    run_command(["uv", "add", "--frozen", "--group", group, *ctx.args])
    vendor(group=group, libs_path=libs_path)


@app.command(
    add_help_option=False,
    # Allow any extra args to be passed to `uv`
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def remove(
    ctx: typer.Context, group: str = option_group, libs_path: Path = option_libs_path
):
    """Remove packages from the isolated environment."""
    # The `uv remove` command doesn't support installing to a custom target,
    # so we use `--frozen` just to remove the package from the `pyproject.toml`.
    # Then we call `vendor` to actually uninstall the package from the desired libs target.
    run_command(["uv", "remove", "--frozen", "--group", group, *ctx.args])
    vendor(group=group, libs_path=libs_path)


if __name__ == "__main__":
    app()
