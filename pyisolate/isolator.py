from typing import cast, Optional
import builtins
import importlib
import logging
from pathlib import Path
from pyisolate.caller_finder import get_caller_frame_outside_pyisolate
from pyisolate.vendor_importer import BuiltinsImporter, VendorImporter


LOGGER = logging.getLogger(__name__)


def isolate_package(package_path: Optional[Path] = None, vendorized_libs_directory_import_path: str = "libs") -> None:
    vendor_importer = create_vendor_importer(package_path, vendorized_libs_directory_import_path)
    LOGGER.debug(f"Isolating library: {vendor_importer.package_name} ({vendorized_libs_directory_import_path=})")
    vendor_importer.install()


def create_vendor_importer(
    package_path: Optional[Path] = None,
    vendorized_libs_directory_import_path: str = "libs",
) -> VendorImporter:
    """
    Isolates a package dependencies - everything imported from the specified package_path
    will prefer to import libraries inside the specified vendorized_libs_directory_import_path
    instead of the default PYTHONPATH/site-packages.
    The package_path can be unspecified/None to default to the caller's parent package.
    vendorized_libs_directory_import_path should be the path to import the dependencies
    from the package.
    For example if the dependencies are in 'libs' it should be 'libs' as well as we need to perform:
    `import libs` but if it's a subdirectory like 'my/libs' it should be 'my.libs' for
    `import my.libs`.
    """
    if package_path is None:
        package_path = get_caller_frame_outside_pyisolate().filename.parent

    package_name = package_path.name
    vendorized_libs_path = package_path / vendorized_libs_directory_import_path
    return VendorImporter(
        package_name,
        vendorized_libs_directory_import_path,
        vendorized_libs_path,
        # Cast as for some reason the definition of __import__ thinks fromlist is not nullable
        cast(BuiltinsImporter, builtins.__import__),
        importlib.import_module,
    )
