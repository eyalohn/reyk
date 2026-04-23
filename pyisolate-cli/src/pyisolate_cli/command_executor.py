import subprocess
import logging
import typer


LOGGER = logging.getLogger(__name__)


def run_command_exit_on_fail(cmd: list[str]) -> None:
    result = subprocess.run(cmd, check=False)  # noqa: S603
    LOGGER.debug(f"Executed {cmd=} -> {result.returncode=}")
    if result.returncode != 0:
        raise typer.Exit(result.returncode)
