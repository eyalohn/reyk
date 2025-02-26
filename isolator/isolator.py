import sys
import builtins
import importlib
from isolator.caller_finder import get_caller_path
from isolator.vendor_importer import VendorImporter, invalidate_all_finder_caches
from isolator.sys_modules_wrapper import SysModulesWrapper


def isolate_library(library_name: str | None = None, vendorized_libs_dir_name: str = "_vendor") -> None:
    if library_name is None:
        library_name = get_caller_path().parent.name

    sys.modules = SysModulesWrapper(sys.modules, library_name)
    invalidate_all_finder_caches()
    VendorImporter(library_name, vendorized_libs_dir_name).install()

    # Cannot use C-implementation as it doesn't use the same sys-modules
    builtins.__import__ = importlib.__import__
