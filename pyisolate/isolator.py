from typing import cast, Optional
import builtins
import importlib
import logging
from pathlib import Path
from pyisolate.caller_finder import get_caller_frame_outside_pyisolate
from pyisolate.vendor_importer import BuiltinsImporter, VendorImporter


LOGGER = logging.getLogger(__name__)


def isolate_package(package_path: Optional[Path] = None, vendorized_libs_dir_name: str = "libs") -> None:
    if package_path is None:
        package_path = get_caller_frame_outside_pyisolate().filename.parent

    package_name = package_path.name
    vendorized_libs_path = package_path / vendorized_libs_dir_name
    LOGGER.debug(f"Isolating library: {package_name} ({vendorized_libs_dir_name=})")
    VendorImporter(
        package_name,
        vendorized_libs_dir_name,
        vendorized_libs_path,
        # Cast as for some reason the definition of __import__ thinks fromlist is not nullable
        cast(BuiltinsImporter, builtins.__import__),
        importlib.import_module,
    ).install()
