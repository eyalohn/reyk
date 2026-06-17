from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[reportMissingImports]


TOOLS_CONFIGURATION_NAME = "tool"
REYK_CONFIGURATION_NAME = "reyk"

DEFAULT_LIBRARIES_TARGET_PATH = "libs"  # Path the vendored libraries will be in
DEFAULT_VENDOR_GROUP = "vendor-libs"
DEFAULT_VENDOR_GROUPS = {DEFAULT_VENDOR_GROUP}


@dataclass
class ReykConfiguration:
    libraries_path: str
    vendor_groups: set[str]
    vendor_exclusions: set[str]


def read_reyk_configuration(toml_path: Path) -> ReykConfiguration:
    toml_data = tomllib.loads(toml_path.read_text())
    configuration = cast(
        dict[str, Any],
        toml_data.get(TOOLS_CONFIGURATION_NAME, {}).get(REYK_CONFIGURATION_NAME, {}),
    )
    configuration["libraries_path"] = configuration.pop("libraries-path", DEFAULT_LIBRARIES_TARGET_PATH)
    configuration["vendor_groups"] = set(configuration.pop("vendor-groups", DEFAULT_VENDOR_GROUPS))
    configuration["vendor_exclusions"] = set(configuration.pop("vendor-exclusions", set()))
    return ReykConfiguration(**configuration)
