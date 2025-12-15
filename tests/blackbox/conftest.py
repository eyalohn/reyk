import sys
from collections.abc import Iterable
import pytest

from pyisolator.vendor_importer import get_installed_vendor_importer
from tests.blackbox.libraries_manager import LibrariesManager
from tests.blackbox.project_paths import EXAMPLE_PROJECT_PATH, EXAMPLE_PROJECT_LIBRARIES_DIRECTORY_RELATIVE_PATH, TEST_LIBRARIES_DIRECTORY_PATH
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager


@pytest.fixture(scope="session", autouse=True)
def install_project_in_path() -> None:
    # Tests will be able to import as if  in the example project
    sys.path.insert(0, str(EXAMPLE_PROJECT_PATH.parent))


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
        

@pytest.fixture(scope="session", autouse=True)
def import_example_project(install_project_in_path) -> None:
    # This is crucial to happen before `clear_imported_modules_cache` as it will isolate
    # the project every test as the `__init__` will be reloaded (as its removed from sys modules)

    import example_project
        

@pytest.fixture(autouse=True)
def clear_vendorized_modules_cache() -> None:
    # Must be before `clear_sys_imported_modules_cache` because by clearing the cache
    # it also returns the removed `sys.modules` back (returns to an unvendorized state)
    vendor_importer = get_installed_vendor_importer()
    if vendor_importer is not None:
        vendor_importer.clear_vendorized_cache()


@pytest.fixture(autouse=True)
def clear_sys_imported_modules_cache() -> Iterable[None]:
    imported_modules_before_test = sys.modules.copy()
    yield
    sys.modules.clear()
    sys.modules.update(imported_modules_before_test)
