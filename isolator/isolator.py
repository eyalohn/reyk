import sys
import builtins
import importlib
from isolator.caller_finder import get_caller_path
from isolator.vendor_importer import VendorImporter
from isolator.sys_modules_wrapper import SysModulesWrapper


def isolate_library(library_name: str | None = None, vendorized_libs_dir_name: str = "_vendor") -> None:
    if library_name is None:
        library_name = get_caller_path().parent.name
    
    for finder in sys.meta_path:
        invalidate_caches = getattr(finder, "invalidate_caches", None)
        if invalidate_caches is not None:
            invalidate_caches()
    wrapper = SysModulesWrapper(sys.modules, library_name)
    sys.modules = wrapper
    VendorImporter(library_name, vendorized_libs_dir_name).install()

    # Cannot use C-implementation as it doesn't use the same sys-modules
    builtins.__import__ = importlib.__import__
