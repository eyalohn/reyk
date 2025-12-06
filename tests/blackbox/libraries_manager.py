import os
from pathlib import Path
import shutil
import sys

from tests.blackbox.example_project_file_manager import ExampleProjectFileManager


class LibrariesManager:
    def __init__(self, libraries_path: Path) -> None:
        self._libraries_path = libraries_path
        self._created_libraries: set[Path] = set()
    
    def create_library(self, library_name: str) -> ExampleProjectFileManager:
        project_path = self._libraries_path / library_name
        project_path.mkdir(parents=True, exist_ok=True)
        sys.path.insert(0, str(project_path))
        self._created_libraries.add(project_path)
        return ExampleProjectFileManager(
            project_path=project_path,
            libraries_dir_relative_path=Path(os.pardir),
        )
    
    def cleanup_libraries_dir(self) -> None:
        for library in self._created_libraries:
            sys.path.remove(str(library))
            shutil.rmtree(library, ignore_errors=True)

        self._created_libraries.clear()
