from contextlib import contextmanager
import functools
import sys
from collections.abc import Callable, Iterable, Iterator
from importlib.metadata import Distribution
from pathlib import Path
from typing import cast

import pytest
from reyk.isolator import isolate_package
from reyk.vendored_sys_modules import VendoredSysModules
from reyk.vendor_importer import get_installed_vendor_importer

from tests.blackbox.test_distributions_finder import find_distributions_from_library, find_distributions_from_project
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager
from tests.blackbox.libraries_manager import LibrariesManager
from tests.blackbox.project_paths import (
    EXAMPLE_PROJECT_LIBRARIES_DIRECTORY_RELATIVE_PATH,
    EXAMPLE_PROJECT_NAME,
    TEST_LIBRARIES_DIRECTORY_PATH,
)


def _create_files_manager_in_tmp(tmp_path: Path) -> ExampleProjectFileManager:
    project_path = tmp_path / EXAMPLE_PROJECT_NAME
    return ExampleProjectFileManager(
        project_path=project_path,
        libraries_dir_relative_path=EXAMPLE_PROJECT_LIBRARIES_DIRECTORY_RELATIVE_PATH,
    )


@contextmanager
def _with_project_in_sys_path_context(project_path: Path) -> Iterator[None]:
    project_path_parent = str(project_path.parent)
    # Tests will be able to import as if in the example project
    sys.path.append(project_path_parent)
    yield
    sys.path.remove(project_path_parent)


@contextmanager
def _isolate_project_in_context(project_path: Path) -> Iterator[None]:
    isolate_package(project_path)
    yield
    vendor_importer = get_installed_vendor_importer()
    assert vendor_importer is not None
    vendor_importer.uninstall()


@pytest.fixture
def files_manager(tmp_path: Path) -> Iterable[ExampleProjectFileManager]:
    files_manager = _create_files_manager_in_tmp(tmp_path)
    with (
        _with_project_in_sys_path_context(files_manager.project_path),
        _isolate_project_in_context(files_manager.project_path),
    ):
        yield files_manager


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
