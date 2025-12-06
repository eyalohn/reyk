# TODO:
# 1. pymongo
# 2. aiormq
# 3. pika
# 4. protobuf
# 5. pydantic

from pathlib import Path
import shutil
from collections.abc import Iterable
import pytest
from tests.blackbox.project_paths import EXAMPLE_PROJECT_LIBRARIES_PATH, LOCKED_FILES_PENDING_DELETION_PATH
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager


TEST_LIBS_PATH = Path(__file__).parent / "test_libs"


@pytest.fixture(autouse=True, scope="module")
def install_test_libs() -> Iterable[None]:
    if LOCKED_FILES_PENDING_DELETION_PATH.exists():
        shutil.rmtree(LOCKED_FILES_PENDING_DELETION_PATH, ignore_errors=True)

    shutil.copytree(TEST_LIBS_PATH, EXAMPLE_PROJECT_LIBRARIES_PATH, dirs_exist_ok=True)
    yield
    shutil.rmtree(EXAMPLE_PROJECT_LIBRARIES_PATH, ignore_errors=True)
    # If there are any remaining files in the directory because they're in use
    if EXAMPLE_PROJECT_LIBRARIES_PATH.exists():
        shutil.move(EXAMPLE_PROJECT_LIBRARIES_PATH, LOCKED_FILES_PENDING_DELETION_PATH)

    EXAMPLE_PROJECT_LIBRARIES_PATH.mkdir(parents=True, exist_ok=True)


@pytest.mark.parametrize(
    "library_name",
    [
        "bson",  # Has C module
        "pydantic",
        "pymongo",
        "aiormq",
        "pika",
        "google.protobuf",
    ]
)
def test_import_library(files_manager: ExampleProjectFileManager, library_name: str) -> None:
    files_manager.create_project_module(
        module_name="module",
        content=f"import {library_name}"
    )
    import example_project.module
