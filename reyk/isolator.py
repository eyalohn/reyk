import builtins
import importlib
import logging
from typing import Optional, cast

from reyk.reyk_isolator import DEFAULT_VENDOR_LIBS_IMPORT_PATH, ReykIsolator
from reyk.caller_finder import get_caller_frame_outside_reyk
from reyk.reyk_isolator import VendorPackage, get_installed_reyk, install_reyk
from reyk.vendor_importer import BuiltinsImporter, VendorImporter

LOGGER = logging.getLogger(__name__)


def isolate_package(vendor_package: Optional[VendorPackage] = None) -> ReykIsolator:
    reyk_isolator = get_installed_reyk()
    if reyk_isolator is not None:
        # TODO(Eyal): This code that creates the vendor package repeats itself!! remove it  # noqa: FIX002, TD003
        caller = get_caller_frame_outside_reyk()
        package, _, _ = caller.module_name.rpartition(".")
        vendor_package = VendorPackage(
            package_name=package,
            vendor_libs_path=caller.filename.parent / DEFAULT_VENDOR_LIBS_IMPORT_PATH,
        )
        assert vendor_package is not None
        reyk_isolator.add_package(vendor_package=vendor_package)
        return reyk_isolator

    vendor_importer = create_vendor_importer(vendor_package)
    LOGGER.debug(f"Isolating library: {vendor_importer.package_names}")
    install_reyk(vendor_importer)
    return vendor_importer


def create_vendor_importer(
    vendor_package: Optional[VendorPackage] = None,
) -> ReykIsolator:
    """
    Isolates a package dependencies - everything imported from the specified vendor package
    will prefer to import libraries inside the specified vendor package libs import path
    instead of the default PYTHONPATH/site-packages.
    """
    if vendor_package is None:
        caller = get_caller_frame_outside_reyk()
        package, _, _ = caller.module_name.rpartition(".")
        vendor_package = VendorPackage(
            package_name=package,
            vendor_libs_path=caller.filename.parent / DEFAULT_VENDOR_LIBS_IMPORT_PATH,
        )

    vendor_importer = VendorImporter(
        # Cast as for some reason the definition of __import__ thinks fromlist is not nullable
        cast(BuiltinsImporter, builtins.__import__),
        importlib.import_module,
    )
    vendor_importer.add_package(vendor_package=vendor_package)
    return vendor_importer
