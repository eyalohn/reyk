from typing import cast
import builtins
import importlib
import logging
from pathlib import Path
from isolator.caller_finder import get_caller_frame_outside_pyisolate
from isolator.vendor_importer import BuiltinsImporter, VendorImporter, invalidate_all_finder_caches


LOGGER = logging.getLogger(__name__)


def isolate_library(library_path: Path | None = None, vendorized_libs_dir_name: str = "libs") -> None:
    if library_path is None:
        library_path = get_caller_frame_outside_pyisolate().filename.parent

    library_name = library_path.name
    vendorized_libs_path = library_path / vendorized_libs_dir_name
    LOGGER.debug(f"Isolating library: {library_name} ({vendorized_libs_dir_name=})")
    # sys.modules = SysModulesWrapper(sys.modules, library_name)
    invalidate_all_finder_caches()
    VendorImporter(
        library_name,
        vendorized_libs_dir_name,
        vendorized_libs_path,
        # Cast as for some reason the definition of __import__ thinks fromlist is not nullable
        cast(BuiltinsImporter, builtins.__import__),
        importlib.import_module,
    ).install()
