# pyright: reportMissingImports=false
import shutil
import sys
from collections.abc import Callable, Iterable
from importlib.metadata import Distribution
from pathlib import Path
from types import ModuleType

import pytest

from tests.blackbox.test_distributions_finder import assert_distribution_names_subset
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager
from tests.blackbox.project_paths import EXAMPLE_PROJECT_LIBRARIES_PATH, LOCKED_FILES_PENDING_DELETION_PATH

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
        "boto3",  # Lots of absolute imports
        "sqlalchemy",  # Accesses sys modules from inside partially-initialized module
    ],
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


def test_import_kafka(files_manager: ExampleProjectFileManager) -> None:
    confluent_kafka = _import_module_in_project(files_manager, "confluent_kafka.cimpl")
    assert confluent_kafka.cimpl.version() == "2.14.0"


def test_find_distributions_with_specific_libraries(
    distributions_finder: Callable[[], list[Distribution]],
) -> None:
    distributions = distributions_finder()
    assert_distribution_names_subset(
        distributions,
        {
            "SQLAlchemy",
            "aiormq",
            "boto3",
            "botocore",
            "confluent-kafka",
            "importlib_metadata",
            "opentelemetry-api",
            "opentelemetry-sdk",
            "pamqp",
            "pika",
            "protobuf",
            "pydantic",
            "pydantic_core",
            "pymongo",
        },
    )


def test_select_opentelemetry_entry_points(
    files_manager: ExampleProjectFileManager,
    distributions_finder: Callable[[], list[Distribution]],
) -> None:
    distributions = distributions_finder()

    # We use distributions old api to still support Python 3.9
    opentelemetry_sdk_distribution = next(
        dist for dist in distributions if dist.metadata["Name"] == "opentelemetry-sdk"
    )
    console_entry_points = [
        entry_point
        for entry_point in opentelemetry_sdk_distribution.entry_points
        if entry_point.value == "opentelemetry.sdk._logs.export:ConsoleLogRecordExporter"
    ]

    assert len(console_entry_points) == 1
    files_manager.create_project_module(
        module_name="loader_module",
        content="""
def load_entry_point(entry_point):
    return entry_point.load()
""",
    )
    import example_project.loader_module

    # Must be loaded in vendored context
    console_entry_point = example_project.loader_module.load_entry_point(console_entry_points[0])
    # Ensure it successfully loads (imports module)
    assert console_entry_point is not None


def _import_module_in_project(files_manager: ExampleProjectFileManager, library_name: str) -> ModuleType:
    files_manager.create_project_module(
        module_name="module", content=f"imported_library = __import__('{library_name}')"
    )
    from example_project.module import imported_library

    return imported_library
