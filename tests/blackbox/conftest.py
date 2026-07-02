import functools
import sys
from collections.abc import Callable, Iterable
from importlib.metadata import Distribution
from pathlib import Path
from typing import cast

import pytest
from reyk.isolator import PackageInfo, isolate_package
from reyk.vendor_importer import get_installed_vendor_importer

from tests.blackbox.test_distributions_finder import find_distributions_from_library, find_distributions_from_project
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager
from tests.blackbox.libraries_manager import LibrariesManager
from tests.blackbox.project_paths import (
    EXAMPLE_PROJECT_LIBRARIES_DIRECTORY_RELATIVE_PATH,
    EXAMPLE_PROJECT_NAME,
    EXAMPLE_PROJECT_PATH,
    TEST_LIBRARIES_DIRECTORY_PATH,
)


@pytest.fixture(scope="package", autouse=True)
def install_project_in_path() -> Iterable[None]:
    # Tests will be able to import as if in the example project
    project_path_parent = str(EXAMPLE_PROJECT_PATH.parent)
    sys.path.append(project_path_parent)
    yield
    sys.path.remove(project_path_parent)


@pytest.fixture(autouse=True)
def setup_vendor_importer() -> Iterable[None]:
    isolate_package(PackageInfo(package_name=EXAMPLE_PROJECT_NAME, package_path=EXAMPLE_PROJECT_PATH))
    yield
    vendor_importer = get_installed_vendor_importer()
    assert vendor_importer is not None
    vendor_importer.uninstall()


@pytest.fixture
def files_manager() -> Iterable[ExampleProjectFileManager]:
    files_manager = ExampleProjectFileManager(
        project_path=EXAMPLE_PROJECT_PATH,
        libraries_dir_relative_path=EXAMPLE_PROJECT_LIBRARIES_DIRECTORY_RELATIVE_PATH,
    )
    try:
        yield files_manager
    finally:
        files_manager.cleanup_files()


@pytest.fixture
def libraries_manager() -> Iterable[LibrariesManager]:
    libraries_manager = LibrariesManager(TEST_LIBRARIES_DIRECTORY_PATH)
    libraries_manager.install_libraries_in_path()
    yield libraries_manager
    libraries_manager.remove_libraries_from_path()
    libraries_manager.cleanup_libraries_dir()


@pytest.fixture(
    params=[
        pytest.param(find_distributions_from_project, id="Find distributions inside project module"),
        pytest.param(find_distributions_from_library, id="Find distributions inside library module"),
    ]
)
def distributions_finder(
    request: pytest.FixtureRequest,
    files_manager: ExampleProjectFileManager,
) -> Callable[[], list[Distribution]]:
    return functools.partial(request.param, files_manager)


@pytest.fixture(autouse=True)
def clear_sys_imported_modules_cache() -> Iterable[None]:
    vendor_sys_modules = sys.modules.copy()
    yield
    sys.modules.clear()
    sys.modules.update(vendor_sys_modules)
