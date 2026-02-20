from pathlib import Path
from pyisolate_cli.command_executor import run_command


class UVBasedVendorizer:
    def create_lock_file_on_group(self, group: str, lock_file: str | Path) -> None:
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
                str(lock_file),
            ]
        )
