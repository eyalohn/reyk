import builtins
import importlib
import sys
from pathlib import Path

from reyk.caller_finder import get_caller_frame_outside_reyk
from reyk.isolator import create_vendor_importer, isolate_package
from reyk.vendor_importer import VendorImporter, get_installed_vendor_importer


def test_get_caller() -> None:
    caller = get_caller_frame_outside_reyk()
    assert caller.module_name == "tests.internals.test_internals"


def test_get_vendor_importer_nothing_installed() -> None:
    assert get_installed_vendor_importer() is None


def test_get_vendor_importer_install_and_uninstall() -> None:
    isolate_package(Path("fake_package_for_fake_installation"))
    vendor_importer = get_installed_vendor_importer()
    assert vendor_importer in sys.meta_path
    assert vendor_importer is not None
    vendor_importer.uninstall()
    assert vendor_importer not in sys.meta_path
    assert get_installed_vendor_importer() is None


def test_get_vendor_importer_install_and_uninstall_with_meta_path_manipulation() -> None:
    vendor_importer = create_vendor_importer(Path("fake_package_for_fake_installation"))
    sys.meta_path.append(vendor_importer)
    vendor_importer.install()
    assert sys.meta_path.count(vendor_importer) == 1

    vendor_importer = get_installed_vendor_importer()
    assert vendor_importer is not None

    sys.meta_path.remove(vendor_importer)
    vendor_importer.uninstall()
    assert vendor_importer not in sys.meta_path

    assert get_installed_vendor_importer() is None
