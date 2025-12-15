import typer
import subprocess

app = typer.Typer(
    help="Manage isolated environment dependencies.",
    no_args_is_help=True,
)

@app.command()
def vendor():
    """Install the isolated environment dependencies."""
    cmd = ["uv", "pip", "install", "--group", "libs", "--target", "libs/"]
    raise typer.Exit(subprocess.call(cmd))

@app.command(
    add_help_option=False,
    # Allow passing arbitrary extra arguments to the underlying command
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
def add(ctx: typer.Context):
    """Add packages to the isolated environment."""
    cmd = ["uv", "add", *ctx.args, "--group", "libs"]
    raise typer.Exit(subprocess.call(cmd))


@app.command(
    add_help_option=False,
    # Allow passing arbitrary extra arguments to the underlying command
    context_settings={
        "allow_extra_args": True,
        "ignore_unknown_options": True,
    }
)
def remove(ctx: typer.Context):
    """Remove packages from the isolated environment."""
    cmd = ["uv", "remove", *ctx.args, "--group", "libs"]
    raise typer.Exit(subprocess.call(cmd))


if __name__ == "__main__":
    app()
