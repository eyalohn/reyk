from collections.abc import Sequence
from pathlib import Path
import itertools

import typer
from pyisolate_cli.command_executor import run_command_exit_on_fail


LOCK_FILE_NAME = "vendor.lock"


class UVBasedVendorizer:
    def __init__(self, project_root: Path, vendor_groups: set[str], libraries_target_path: Path) -> None:
        self._project_root = project_root
        self._vendor_groups = vendor_groups
        self._libraries_target_path = libraries_target_path

    def add_new_requirement_to_pyproject(self, vendor_group: str, command_args: Sequence[str]) -> None:
        # The `uv add` command doesn't support installing to a custom target,
        # so we use `--frozen` just to append the package to the `pyproject.toml`.
        self._ensure_group_exists(vendor_group)
        run_command_exit_on_fail(["uv", "add", "--frozen", "--group", vendor_group, *command_args])

    def remove_requirement_from_pyproject(self, vendor_group: str, command_args: Sequence[str]) -> None:
        # The `uv remove` command doesn't support installing to a custom target,
        # so we use `--frozen` just to remove the package from the `pyproject.toml`.
        self._ensure_group_exists(vendor_group)
        run_command_exit_on_fail(["uv", "remove", "--frozen", "--group", vendor_group, *command_args])

    def _ensure_group_exists(self, vendor_group: str) -> None:
        if vendor_group not in self._vendor_groups:
            raise typer.BadParameter(f"{vendor_group!s} not in {self._vendor_groups=}")

    def sync_from_group_to_target_path(self) -> None:
        # `uv pip sync` is the only command that supports installing to a custom target,
        # but it requires a lock file. Therefore, we first export the lock file of the libs group
        # and then use it to install the packages to the desired target.
        self.create_lock_file_on_group()
        self.install_requirements_from_lock_file()

    def create_lock_file_on_group(self) -> None:
        run_command_exit_on_fail(
            [
                "uv",
                "export",
                *itertools.chain.from_iterable([("--group", group) for group in self._vendor_groups]),
                "--no-header",
                "--quiet",
                "--no-emit-project",
                "--output-file",
                str(self.lock_file_path),
            ]
        )

    def install_requirements_from_lock_file(self) -> None:
        run_command_exit_on_fail(
            [
                "uv",
                "pip",
                "sync",
                str(self.lock_file_path),
                "--target",
                str(self._libraries_target_path),
                "--allow-empty-requirements",
            ]
        )

    @property
    def lock_file_path(self) -> Path:
        return self._project_root / LOCK_FILE_NAME
