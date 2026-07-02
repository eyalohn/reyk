import builtins
import importlib
import logging
from pathlib import Path
from typing import Optional, cast
from dataclasses import dataclass

from reyk.caller_finder import get_caller_frame_outside_reyk
from reyk.vendor_importer import BuiltinsImporter, VendorImporter

LOGGER = logging.getLogger(__name__)


@dataclass
class PackageInfo:
    package_name: str
    package_path: Path


def isolate_package(
    package_info: Optional[PackageInfo] = None,
    vendored_libs_directory_import_path: str = "libs",
) -> VendorImporter:
    vendor_importer = create_vendor_importer(package_info, vendored_libs_directory_import_path)
    LOGGER.debug(f"Isolating library: {vendor_importer.package_name} ({vendored_libs_directory_import_path=})")
    vendor_importer.install()
    return vendor_importer


def create_vendor_importer(
    package_info: Optional[PackageInfo] = None,
    vendored_libs_directory_import_path: str = "libs",
) -> VendorImporter:
    """
    Isolates a package dependencies - everything imported from the specified package_path
    will prefer to import libraries inside the specified vendored_libs_directory_import_path
    instead of the default PYTHONPATH/site-packages.
    The package_path can be unspecified/None to default to the caller's parent package.
    vendored_libs_directory_import_path should be the path to import the dependencies
    from the package.
    For example if the dependencies are in 'libs' it should be 'libs' as well as we need to perform:
    `import libs` but if it's a subdirectory like 'my/libs' it should be 'my.libs' for
    `import my.libs`.
    """
    if package_info is None:
        caller = get_caller_frame_outside_reyk()
        package, _, _ = caller.module_name.rpartition(".")
        package_info = PackageInfo(
            package_name=package,
            package_path=caller.filename.parent,
        )

    vendored_libs_path = package_info.package_path / vendored_libs_directory_import_path
    return VendorImporter(
        package_info.package_name,
        vendored_libs_directory_import_path,
        vendored_libs_path,
        # Cast as for some reason the definition of __import__ thinks fromlist is not nullable
        cast(BuiltinsImporter, builtins.__import__),
        importlib.import_module,
    )
