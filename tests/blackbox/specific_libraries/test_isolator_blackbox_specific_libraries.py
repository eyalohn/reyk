from pathlib import Path
import shutil
from collections.abc import Iterable
from types import ModuleType
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
        "pydantic",  # Rust pyd
        "aiormq",  # Lots of relative imports
        "pika",  # Large library with lots of builtins usage
    ]
)
def test_import_library(files_manager: ExampleProjectFileManager, library_name: str) -> None:
    _import_module_in_project(files_manager, library_name)


def test_import_bson(files_manager: ExampleProjectFileManager) -> None:
    bson = _import_module_in_project(files_manager, "bson")
    assert bson._cbson._C_API is not None


def test_import_pymongo(files_manager: ExampleProjectFileManager) -> None:
    pymongo = _import_module_in_project(files_manager, "pymongo")
    assert pymongo.has_c()


def test_import_protobuf(files_manager: ExampleProjectFileManager) -> None:
    google = _import_module_in_project(files_manager, "google.protobuf.internal.api_implementation")
    assert google.protobuf.internal.api_implementation.Type() != "python"


def _import_module_in_project(files_manager: ExampleProjectFileManager, library_name: str) -> ModuleType:
    files_manager.create_project_module(
        module_name="module",
        content=f"imported_library = __import__('{library_name}')"
    )
    from example_project.module import imported_library
    return imported_library
