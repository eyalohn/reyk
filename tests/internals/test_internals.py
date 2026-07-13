from importlib.abc import MetaPathFinder
from importlib.metadata import MetadataPathFinder
import sys
from pathlib import Path
from typing import cast

import pytest

from reyk.caller_finder import get_caller_frame_outside_reyk, get_caller_matching_package
from reyk.isolator import create_vendor_importer, isolate_package
from reyk.reyk_isolator import VendorPackage, get_installed_reyk, uninstall_reyk


FAKE_VENDOR_PACKAGE = VendorPackage(
    package_name="fake_package_for_fake_installation",
    vendor_libs_path=Path("fake_package_for_fake_installation", "libs"),
)


def test_get_caller() -> None:
    caller = get_caller_frame_outside_reyk()
    assert caller.module_name == "tests.internals.test_internals"


@pytest.mark.parametrize(
    ("package_names", "expected_output"),
    [
        pytest.param(["tests"], "tests", id="root-package"),
        pytest.param(["tests.internals"], "tests.internals", id="sub-package"),
        pytest.param(["tests.internals.test_internals"], "tests.internals.test_internals", id="specific module"),
        pytest.param(["unrelated_package"], None, id="package-outside-of-library"),
        pytest.param(
            ["unrelated_package", "tests.internals"], "tests.internals", id="single matching package out of options"
        ),
        pytest.param(["tests", "tests.internals"], "tests.internals", id="two matching packages chooses max depth"),
    ],
)
def test_get_caller_matching_package(package_names: list[str], expected_output: str | None) -> None:
    matching_package = get_caller_matching_package(package_names)
    assert matching_package == expected_output


def test_get_vendor_importer_nothing_installed() -> None:
    assert get_installed_reyk() is None


def test_get_vendor_importer_install_and_uninstall() -> None:
    isolate_package(FAKE_VENDOR_PACKAGE)
    reyk = get_installed_reyk()
    assert reyk in sys.meta_path
    assert reyk is not None
    uninstall_reyk()
    assert reyk not in sys.meta_path
    assert get_installed_reyk() is None


def test_get_vendor_importer_install_and_uninstall_with_meta_path_manipulation() -> None:
    vendor_importer = create_vendor_importer(FAKE_VENDOR_PACKAGE)
    assert isinstance(vendor_importer, MetaPathFinder)
    sys.meta_path.append(vendor_importer)
    vendor_importer.install()
    assert sys.meta_path.count(vendor_importer) == 1

    sys.meta_path.remove(vendor_importer)
    vendor_importer.uninstall()
    assert vendor_importer not in sys.meta_path

    assert get_installed_reyk() is None
