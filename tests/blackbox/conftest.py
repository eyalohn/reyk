import sys
from collections.abc import Iterable
import pytest

from tests.blackbox.project_paths import PROJECT_PATH, LIBRARIES_DIRECTORY_RELATIVE_PATH
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager


@pytest.fixture(scope="session", autouse=True)
def install_project_in_path() -> None:
    # Tests will be able to import as if  in the example project
    sys.path.insert(0, str(PROJECT_PATH.parent))


@pytest.fixture
def files_manager() -> Iterable[ExampleProjectFileManager]:
    files_manager = ExampleProjectFileManager(
        project_path=PROJECT_PATH,
        libraries_dir_relative_path=LIBRARIES_DIRECTORY_RELATIVE_PATH,
    )
    try:
        yield files_manager
    finally:
        files_manager.cleanup_files()
        
@pytest.fixture(scope="session", autouse=True)
def import_example_project(install_project_in_path) -> None:
    # This is crucial to happen before `clear_imported_modules_cache` as it will isolate
    # the project every test as the `__init__` will be reloaded (as its removed from sys modules)

    import example_project
        
        
@pytest.fixture(autouse=True)
def clear_imported_modules_cache() -> Iterable[None]:
    imported_modules_before_test = sys.modules.copy()
    yield
    sys.modules.clear()
    sys.modules.update(imported_modules_before_test)
