from typing import Any, cast
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib


TOOLS_CONFIGURATION_NAME = "tool"
PYISOLATE_CONFIGURATION_NAME = "pyisolate"

DEFAULT_LIBRARIES_TARGET_PATH = "libs"  # Path the vendorized libraries will be in
DEFAULT_VENDOR_GROUP = "vendor-libs"
DEFAULT_VENDOR_GROUPS = {DEFAULT_VENDOR_GROUP}


@dataclass
class PyIsolateConfiguration:
    libraries_path: str
    vendor_groups: set[str]


def read_pyisolate_configuration(toml_path: Path) -> PyIsolateConfiguration:
    toml_data = tomllib.loads(toml_path.read_text())
    configuration = cast(
        dict[str, Any],
        toml_data.get(TOOLS_CONFIGURATION_NAME, {}).get(PYISOLATE_CONFIGURATION_NAME, {}),
    )
    configuration["libraries_path"] = configuration.pop("libraries-path", DEFAULT_LIBRARIES_TARGET_PATH)
    configuration["vendor_groups"] = set(configuration.pop("vendor-groups", DEFAULT_VENDOR_GROUPS))
    return PyIsolateConfiguration(**configuration)
