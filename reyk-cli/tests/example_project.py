from pathlib import Path
from typing import Any, Optional

import tomli_w
from reyk_cli.configuration_reader import (
    DEFAULT_LIBRARIES_TARGET_PATH,
    DEFAULT_VENDOR_GROUPS,
    ReykConfiguration,
)

PYPROJECT_TOML_NAME = "pyproject.toml"
DIST_INFO_SUBSTRING = "dist-info"
IGNORED_DIRECTORIES_IN_LIBS = {"bin", "images"}  # Directories which aren't packages

PYPROJECT_EXAMPLE: dict[str, Any] = {
    "project": {
        "name": "project-example",
        "version": "0.0.1",
        "description": "Example Pyproject",
        "readme": "README.md",
        "requires-python": ">=3.8",
        "dependencies": [],
    }
}


class ExampleProject:
    def __init__(self, project_path: Path, configuration: Optional[ReykConfiguration]) -> None:
        self._project_path = project_path
        self._configuration = (
            ReykConfiguration(DEFAULT_LIBRARIES_TARGET_PATH, DEFAULT_VENDOR_GROUPS, set())
            if configuration is None
            else configuration
        )

    def write_pyproject_toml(self) -> None:
        pyproject = PYPROJECT_EXAMPLE.copy()
        # Only add values if any are not the default:
        if (
            self._configuration.libraries_path != DEFAULT_LIBRARIES_TARGET_PATH
            or self._configuration.vendor_groups != DEFAULT_VENDOR_GROUPS
            or len(self._configuration.vendor_exclusions) > 0
        ):
            pyproject["tool"] = {
                "reyk": {
                    "libraries-path": self._configuration.libraries_path,
                    "vendor-groups": list(self._configuration.vendor_groups),
                    "vendor-exclusions": list(self._configuration.vendor_exclusions),
                },
            }

        with (self._project_path / PYPROJECT_TOML_NAME).open("wb") as fp:
            tomli_w.dump(pyproject, fp)

    def get_existing_libraries(self) -> set[str]:
        return {
            library_path.name
            for library_path in (self._project_path / self._configuration.libraries_path).iterdir()
            if (
                library_path.is_dir()
                and library_path.name not in IGNORED_DIRECTORIES_IN_LIBS
                and DIST_INFO_SUBSTRING not in library_path.name
            )
        }

    def has_libs_directory(self) -> bool:
        return (self._project_path / self._configuration.libraries_path).exists()
