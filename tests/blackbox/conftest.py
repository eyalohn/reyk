import sys
from collections.abc import Iterable
import pytest

from tests.blackbox.project_paths import PROJECT_PATH, LIBRARIES_DIRECTORY_RELATIVE_PATH
from tests.blackbox.files_manager import ExampleProjectFileManager


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
