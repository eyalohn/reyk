import os
from pathlib import Path
import sys

from tests.blackbox.example_project_file_manager import ExampleProjectFileManager


class LibrariesManager:
    def __init__(self, libraries_path: Path) -> None:
        self._libraries_path = libraries_path

    def install_libraries_in_path(self) -> None:
        sys.path.append(str(self._libraries_path))

    def remove_libraries_from_path(self) -> None:
        sys.path.remove(str(self._libraries_path))

    def create_library(self, library_name: str) -> ExampleProjectFileManager:
        project_path = self._libraries_path / library_name
        project_path.mkdir(parents=True, exist_ok=True)
        return ExampleProjectFileManager(
            project_path=project_path,
            libraries_dir_relative_path=Path(os.pardir),
        )
