# pyright: reportMissingImports=false
import shutil
from collections.abc import Callable, Iterable
from importlib.metadata import Distribution
from pathlib import Path
from types import ModuleType

import pytest
from reyk.vendor_importer import get_installed_vendor_importer

from tests.blackbox.test_distributions_finder import assert_distribution_names
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


def test_find_distributions_with_specific_libraries(
    distributions_finder: Callable[[], list[Distribution]],
) -> None:
    distributions = distributions_finder()
    assert_distribution_names(
        distributions,
        {
            "aiormq",
            "annotated-types",
            "boto3",
            "botocore",
            "dnspython",
            "idna",
            "importlib_metadata",
            "jmespath",
            "multidict",
            "opentelemetry-api",
            "opentelemetry-sdk",
            "opentelemetry-semantic-conventions",
            "pamqp",
            "pika",
            "propcache",
            "protobuf",
            "pydantic",
            "pydantic_core",
            "pymongo",
            "python-dateutil",
            "s3transfer",
            "six",
            "typing-inspection",
            "typing_extensions",
            "urllib3",
            "yarl",
            "zipp",
        },
    )

    opentelemetry_sdk_distribution = next(d for d in distributions if "opentelemetry-sdk" in d.name)
    console_entry_points = list(
        opentelemetry_sdk_distribution.entry_points.select(
            value="opentelemetry.sdk._logs.export:ConsoleLogRecordExporter"  # Arbitrary entrypoint
        )
    )
    assert len(console_entry_points) == 1
    console_entry_point = console_entry_points[0].load()
    # Ensure it successfully loads (imports module)
    assert console_entry_point is not None


def _import_module_in_project(files_manager: ExampleProjectFileManager, library_name: str) -> ModuleType:
    files_manager.create_project_module(
        module_name="module", content=f"imported_library = __import__('{library_name}')"
    )
    from example_project.module import imported_library

    return imported_library
