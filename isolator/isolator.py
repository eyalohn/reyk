from isolator.caller_finder import get_caller_dir_name
from isolator.vendor_importer import VendorImporter


def isolate_library(library_name: str | None = None, vendorized_libs_dir_name: str = "_vendor") -> None:
    if library_name is None:
        library_name = get_caller_dir_name()
    
    VendorImporter(library_name, vendorized_libs_dir_name).install()
