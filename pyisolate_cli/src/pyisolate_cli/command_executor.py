import subprocess

import typer


def run_command(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False)  # noqa: S603
    if result.returncode != 0:
        raise typer.Exit(result.returncode)
