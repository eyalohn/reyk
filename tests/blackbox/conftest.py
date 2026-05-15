import sys
from collections.abc import Iterable, Callable
from pathlib import Path
import functools
from importlib.metadata import Distribution
import pytest

from pyisolate.isolator import isolate_package
from pyisolate.vendor_importer import get_installed_vendor_importer
from tests.blackbox.libraries_manager import LibrariesManager
from tests.blackbox.project_paths import (
    EXAMPLE_PROJECT_PATH,
    EXAMPLE_PROJECT_LIBRARIES_DIRECTORY_RELATIVE_PATH,
    TEST_LIBRARIES_DIRECTORY_PATH,
)
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager
from tests.blackbox.distributions_finder import find_distributions_from_project, find_distributions_from_library


@pytest.fixture(scope="package", autouse=True)
def install_project_in_path() -> Iterable[None]:
    # Tests will be able to import as if in the example project
    project_path_parent = str(EXAMPLE_PROJECT_PATH.parent)
    sys.path.insert(0, project_path_parent)
    yield
    sys.path.remove(project_path_parent)


@pytest.fixture(scope="package", autouse=True)
def setup_vendor_importer() -> Iterable[None]:
    isolate_package(Path(__file__).parent / "example_project")
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


@pytest.fixture(scope="package", autouse=True)
def import_example_project(install_project_in_path: None) -> None:  # noqa: ARG001
    # This is crucial to happen before `clear_imported_modules_cache` as it will isolate
    # the project every test as the `__init__` will be reloaded (because its removed from sys modules)

    import example_project


@pytest.fixture(autouse=True)
def clear_vendorized_modules_cache() -> None:
    # Must be before `clear_sys_imported_modules_cache` because by clearing the cache
    # it also returns the removed `sys.modules` back (returns to an non-vendorized state)
    vendor_importer = get_installed_vendor_importer()
    if vendor_importer is not None:
        vendor_importer.clear_vendorized_cache()


@pytest.fixture(autouse=True)
def clear_sys_imported_modules_cache() -> Iterable[None]:
    imported_modules_before_test = sys.modules.copy()
    yield
    sys.modules.clear()
    sys.modules.update(imported_modules_before_test)
