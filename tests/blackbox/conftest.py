from contextlib import contextmanager
import functools
import sys
from collections.abc import Callable, Iterable, Iterator
from importlib.metadata import Distribution
from pathlib import Path

import pytest
from reyk.isolator import isolate_package, uninstall_reyk
from reyk.isolator_definition import VendorPackage, ContextDetectionConfig

from tests.blackbox.test_distributions_finder import find_distributions_from_library, find_distributions_from_project
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager
from tests.blackbox.libraries_manager import LibrariesManager
from tests.blackbox.project_paths import (
    EXAMPLE_PROJECT_LIBRARIES_DIRECTORY_RELATIVE_PATH,
    EXAMPLE_PROJECT_NAME,
    TEST_LIBRARIES_DIRECTORY_NAME,
)


@contextmanager
def _with_project_in_sys_path_context(project_path: Path) -> Iterator[None]:
    project_path_parent = str(project_path.parent)
    # Tests will be able to import as if in the example project
    sys.path.append(project_path_parent)
    yield
    sys.path.remove(project_path_parent)


@contextmanager
def _isolate_project_in_context(vendor_package: VendorPackage) -> Iterator[None]:
    isolate_package(vendor_package)
    yield
    uninstall_reyk()


@pytest.fixture
def context_detection_config(request: pytest.FixtureRequest) -> ContextDetectionConfig:
    return getattr(request, "param", ContextDetectionConfig())


@pytest.fixture
def vendor_package(tmp_path: Path, context_detection_config: ContextDetectionConfig) -> VendorPackage:
    project_path = tmp_path / EXAMPLE_PROJECT_NAME
    project_path.mkdir(parents=True, exist_ok=True)
    libraries_dir = project_path / EXAMPLE_PROJECT_LIBRARIES_DIRECTORY_RELATIVE_PATH
    libraries_dir.mkdir(parents=True, exist_ok=True)
    return VendorPackage(
        package_name=EXAMPLE_PROJECT_NAME,
        package_directory=project_path,
        vendor_libs_path=libraries_dir,
        context_detection=context_detection_config,
    )


@pytest.fixture
def files_manager(vendor_package: VendorPackage) -> Iterable[ExampleProjectFileManager]:
    files_manager = ExampleProjectFileManager(
        project_path=vendor_package.package_directory,
        libraries_dir_relative_path=vendor_package.vendor_libs_path.relative_to(vendor_package.package_directory),
    )
    with (
        _with_project_in_sys_path_context(files_manager.project_path),
        _isolate_project_in_context(vendor_package),
    ):
        yield files_manager


@pytest.fixture
def libraries_manager(tmp_path: Path) -> Iterable[LibrariesManager]:
    libraries_manager = LibrariesManager(tmp_path / TEST_LIBRARIES_DIRECTORY_NAME)
    libraries_manager.install_libraries_in_path()
    yield libraries_manager
    libraries_manager.remove_libraries_from_path()


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
