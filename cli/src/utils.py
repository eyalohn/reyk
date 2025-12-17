import subprocess

import typer


def run_command(cmd: list[str]) -> None:
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)
