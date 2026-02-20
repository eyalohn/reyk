from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib


TOOLS_CONFIGURATION_NAME = "tool"
PYISOLATE_CONFIGURATION_NAME = "pyisolate"


@dataclass
class PyIsolateConfiguration:
    libraries_path: str
    vendor_groups: list[str]


def read_pyisolate_configuration(toml_path: Path) -> PyIsolateConfiguration:
    toml_data = tomllib.loads(toml_path.read_text())
    configuration: dict[str, Any] = toml_data.get(TOOLS_CONFIGURATION_NAME, {}).get(PYISOLATE_CONFIGURATION_NAME, {})
    configuration["libraries_path"] = configuration.pop("libraries-path", None)
    configuration["vendor_groups"] = configuration.pop("vendor-groups", None)
    return PyIsolateConfiguration(**configuration)
