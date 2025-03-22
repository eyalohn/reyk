import sys
import builtins
import importlib
import logging
from pathlib import Path
from isolator.caller_finder import get_caller_frame_outside_pyisolate
from isolator.vendor_importer import VendorImporter, invalidate_all_finder_caches
from isolator.sys_modules_wrapper import SysModulesWrapper


LOGGER = logging.getLogger(__name__)


def isolate_library(library_path: Path | None = None, vendorized_libs_dir_name: str = "_vendor") -> None:
    if library_path is None:
        library_path = get_caller_frame_outside_pyisolate().filename.parent

    library_name = library_path.name
    vendorized_libs_path = library_path / vendorized_libs_dir_name
    LOGGER.debug(f"Isolating library: {library_name} ({vendorized_libs_dir_name=})")
    sys.modules = SysModulesWrapper(sys.modules, library_name)
    invalidate_all_finder_caches()
    VendorImporter(library_name, vendorized_libs_dir_name, vendorized_libs_path).install()

    # Cannot use C-implementation as it doesn't use the same sys-modules
    def debug_import(name, globals=None, locals=None, fromlist=(), level=0):
        LOGGER.debug(f"DEBUG IMPORT: {name} {fromlist} {level}")
        mod = importlib.__import__(name, globals, locals, fromlist, level)
        LOGGER.debug(f"DEBUG IMPORTED: {mod} from {name} {fromlist} {level}")
        return mod
    
    builtins.__import__ = debug_import
    # builtins.__import__ = importlib.__import__
