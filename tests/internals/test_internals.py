from importlib.abc import MetaPathFinder
from importlib.metadata import MetadataPathFinder
import sys
from pathlib import Path
from typing import Optional, cast

import pytest

from reyk.caller_finder import get_caller_frame_outside_reyk, get_caller_matching_package
from reyk.isolator import (
    FACTORY_IMPLEMENTATION,
    get_installed_reyk,
    isolate_package,
    uninstall_reyk,
    get_caller_vendor_package,
)
from reyk.isolator_definition import VendorPackage


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
def test_get_caller_matching_package(package_names: list[str], expected_output: Optional[str]) -> None:
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
    isolator = FACTORY_IMPLEMENTATION.create_isolator()
    isolator.add_package(vendor_package=FAKE_VENDOR_PACKAGE)
    assert isinstance(isolator, MetaPathFinder)
    sys.meta_path.append(isolator)
    isolator.install()
    assert sys.meta_path.count(isolator) == 1

    sys.meta_path.remove(isolator)
    isolator.uninstall()
    assert isolator not in sys.meta_path

    assert get_installed_reyk() is None


def test_get_caller_vendor_package() -> None:
    vendor_package = get_caller_vendor_package()
    assert vendor_package == VendorPackage(
        package_name="tests.internals",
        vendor_libs_path=Path(__file__).parent / "libs",
    )
