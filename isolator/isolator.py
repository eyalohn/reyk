import sys
from isolator.caller_finder import get_caller_path
from isolator.vendor_importer import VendorImporter
from isolator.sys_modules_wrapper import SysModulesWrapper


def isolate_library(library_name: str | None = None, vendorized_libs_dir_name: str = "_vendor") -> None:
    if library_name is None:
        library_name = get_caller_path().parent.name
    
    sys.modules = SysModulesWrapper(sys.modules, library_name)
    VendorImporter(library_name, vendorized_libs_dir_name).install()
