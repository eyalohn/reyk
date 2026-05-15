# pyright: reportMissingImports=false
import sys
from collections.abc import Callable
from importlib.metadata import Distribution
from pathlib import Path

import pytest

from tests.blackbox.distributions_finder import assert_distribution_names
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager
from tests.blackbox.libraries_manager import LibrariesManager
from tests.blackbox.predefined_tests.variable_access_statement_generator import (
    ALL_IMPORT_TECHNIQUES,
    ALL_IMPORT_TECHNIQUES_BUT_RELATIVE,
    generate_variable_access_statement_params,
)
from tests.blackbox.project_paths import EXAMPLE_PROJECT_LIBRARIES_PATH

# Terminology:
# Project - Isolated project that uses Reyk
# Library - a library that the project uses

# Note: We are able to import inside the example project because of
# the fixture in conftest.py


MY_STRING_DECLARATION_MODULE = """
MY_STRING = "Imported"
"""
MY_STRING_NAME = "MY_STRING"
MY_STRING_EXPECTED_VALUE = "Imported"


@pytest.mark.parametrize(
    "variable_access_statement",
    generate_variable_access_statement_params(
        ALL_IMPORT_TECHNIQUES,
        "example_project.other_module",
        MY_STRING_NAME,
    ),
)
def test_import_project_module_from_project(
    variable_access_statement: str,
    files_manager: ExampleProjectFileManager,
) -> None:
    files_manager.create_project_module(
        module_name="other_module",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=variable_access_statement,
    )
    _assert_my_string_in_module()


@pytest.mark.parametrize(
    "variable_access_statement",
    generate_variable_access_statement_params(
        ALL_IMPORT_TECHNIQUES_BUT_RELATIVE,
        "example_library.library_module",
        MY_STRING_NAME,
    ),
)
def test_import_library_module_from_project(
    variable_access_statement: str,
    files_manager: ExampleProjectFileManager,
) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="library_module",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=variable_access_statement,
    )
    _assert_my_string_in_module()


@pytest.mark.parametrize(
    "variable_access_statement",
    generate_variable_access_statement_params(
        ALL_IMPORT_TECHNIQUES,
        "example_project.example_package",
        MY_STRING_NAME,
    ),
)
def test_import_project_package_from_project(
    variable_access_statement: str,
    files_manager: ExampleProjectFileManager,
) -> None:
    files_manager.create_project_module(
        module_name="example_package.__init__",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=variable_access_statement,
    )
    _assert_my_string_in_module()


@pytest.mark.parametrize(
    "variable_access_statement",
    generate_variable_access_statement_params(
        ALL_IMPORT_TECHNIQUES_BUT_RELATIVE,
        "example_library",
        MY_STRING_NAME,
    ),
)
def test_import_library_package_from_project(
    variable_access_statement: str,
    files_manager: ExampleProjectFileManager,
) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="__init__",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=variable_access_statement,
    )
    _assert_my_string_in_module()


@pytest.mark.parametrize(
    "variable_access_statement",
    generate_variable_access_statement_params(
        ALL_IMPORT_TECHNIQUES_BUT_RELATIVE,
        "example_library.module",
        MY_STRING_NAME,
    ),
)
@pytest.mark.parametrize(
    "library_internal_import_statement",
    [
        pytest.param(f"from example_library.other_module import {MY_STRING_NAME}", id="From entire module"),
        pytest.param(f"from .other_module import {MY_STRING_NAME}", id="From relative module"),
        pytest.param(
            f"""
import importlib
other_module = importlib.import_module(".other_module", package=__package__)
{MY_STRING_NAME} = other_module.{MY_STRING_NAME}
""",
            id="From relative module with importlib",
        ),
    ],
)
def test_import_library_module_from_library(
    variable_access_statement: str,
    library_internal_import_statement: str,
    files_manager: ExampleProjectFileManager,
) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="module",
        content=library_internal_import_statement,
    )
    files_manager.create_library_module(
        library_name="example_library",
        module_name="other_module",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=variable_access_statement,
    )
    _assert_my_string_in_module()


@pytest.mark.parametrize(
    "variable_access_statement",
    generate_variable_access_statement_params(
        ALL_IMPORT_TECHNIQUES_BUT_RELATIVE,
        "example_library.module",
        MY_STRING_NAME,
    ),
)
def test_import_library_package_from_library(
    variable_access_statement: str,
    files_manager: ExampleProjectFileManager,
) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="module",
        content=f"from example_library.example_package import {MY_STRING_NAME}",
    )
    files_manager.create_library_module(
        library_name="example_library",
        module_name="example_package.__init__",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=variable_access_statement,
    )
    _assert_my_string_in_module()


@pytest.mark.parametrize(
    "variable_access_statement",
    generate_variable_access_statement_params(
        ALL_IMPORT_TECHNIQUES_BUT_RELATIVE,
        "example_library",
        MY_STRING_NAME,
    ),
)
def test_import_recursive_library_module_in_init(
    variable_access_statement: str,
    files_manager: ExampleProjectFileManager,
) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="__init__",
        content=f"from example_library.first_module import {MY_STRING_NAME}",
    )
    files_manager.create_library_module(
        library_name="example_library",
        module_name="first_module",
        content=f"""
import example_library.second_module
{MY_STRING_NAME} = example_library.second_module.{MY_STRING_NAME}
""",
    )
    files_manager.create_library_module(
        library_name="example_library",
        module_name="second_module",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=variable_access_statement,
    )
    _assert_my_string_in_module()


def test_import_sys_module_in_project(files_manager: ExampleProjectFileManager) -> None:
    files_manager.create_project_module(module_name="module", content="import sys")
    import example_project.module

    assert example_project.module.sys.__name__ == "sys"


def test_import_sys_module_in_library(files_manager: ExampleProjectFileManager) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="library_module",
        content="import sys",
    )
    files_manager.create_project_module(
        module_name="module",
        content="from example_library.library_module import sys",
    )
    import example_project.module

    assert example_project.module.sys.__name__ == "sys"


@pytest.mark.parametrize(
    "variable_access_statement",
    generate_variable_access_statement_params(
        ALL_IMPORT_TECHNIQUES_BUT_RELATIVE,
        "another_library.another_module",
        MY_STRING_NAME,
    ),
)
def test_import_different_library_in_library(
    variable_access_statement: str,
    files_manager: ExampleProjectFileManager,
) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="library_module",
        content=variable_access_statement,
    )
    files_manager.create_library_module(
        library_name="another_library",
        module_name="another_module",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=f"from example_library.library_module import {MY_STRING_NAME}",
    )
    _assert_my_string_in_module()


def test_import_project_with_library_in_same_name(
    files_manager: ExampleProjectFileManager,
    libraries_manager: LibrariesManager,
) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="library_module",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=f"from example_library.library_module import {MY_STRING_NAME}",
    )
    library_files_manager = libraries_manager.create_library("example_library")
    library_files_manager.create_project_module(
        module_name="module",
        content=MY_STRING_DECLARATION_MODULE,
    )
    library_files_manager.create_project_module(module_name="__init__", content="")
    _assert_my_string_in_module()
    import example_library.module

    assert example_library.module.MY_STRING == MY_STRING_EXPECTED_VALUE


def test_import_real_library_with_same_name(files_manager: ExampleProjectFileManager) -> None:
    sys.modules.pop("pytest")
    files_manager.create_library_module(
        library_name="pytest",
        module_name="__init__",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=f"from pytest import {MY_STRING_NAME}",
    )
    _assert_my_string_in_module()
    import pytest

    assert not hasattr(pytest, MY_STRING_NAME)


def test_file_attribute_correct(files_manager: ExampleProjectFileManager) -> None:
    library_name = "example_library"
    library_module_name = "library_module"
    files_manager.create_library_module(
        library_name=library_name,
        module_name=library_module_name,
        content="MY_FILE_PATH = __file__",
    )
    files_manager.create_project_module(
        module_name="module", content="from example_library.library_module import MY_FILE_PATH"
    )
    from example_project.module import MY_FILE_PATH

    expected_module_path = EXAMPLE_PROJECT_LIBRARIES_PATH / library_name / f"{library_module_name}.py"
    assert Path(MY_FILE_PATH) == expected_module_path


def test_import_non_existent_module(files_manager: ExampleProjectFileManager) -> None:
    files_manager.create_project_module(module_name="module", content="import fake_module")
    with pytest.raises(ModuleNotFoundError):
        import example_project.module


@pytest.mark.parametrize(
    "library_names",
    [
        pytest.param(set(), id="No libraries"),
        pytest.param({"example_library", "another_example_library"}, id="Two libraries"),
    ],
)
def test_find_distributions(
    files_manager: ExampleProjectFileManager,
    library_names: set[str],
    distributions_finder: Callable[[], list[Distribution]],
) -> None:
    for library_name in library_names:
        files_manager.create_fake_dist_info(library_name)

    distributions = distributions_finder()
    assert_distribution_names(distributions, library_names)


def _assert_my_string_in_module() -> None:
    import example_project.module

    assert example_project.module.MY_STRING == MY_STRING_EXPECTED_VALUE
