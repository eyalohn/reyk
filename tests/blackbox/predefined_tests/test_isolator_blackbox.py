from pathlib import Path
import sys
import pytest
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager
from tests.blackbox.predefined_tests.variable_access_statement_generator import (
    generate_variable_access_statement_params,
    ALL_IMPORT_TECHNIQUES_BUT_RELATIVE,
    ALL_IMPORT_TECHNIQUES,
)
from tests.blackbox.project_paths import LIBRARIES_PATH


# Terminology:
# Project - Isolated project that uses PyIsolator
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
def test_import_library_module_from_project(variable_access_statement: str, files_manager: ExampleProjectFileManager) -> None:
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
def test_import_project_package_from_project(variable_access_statement: str, files_manager: ExampleProjectFileManager) -> None:
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
def test_import_library_package_from_project(variable_access_statement: str, files_manager: ExampleProjectFileManager) -> None:
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
    )
)
@pytest.mark.parametrize(
    "library_internal_import_statement",
    [
        pytest.param(f"from example_library.other_module import {MY_STRING_NAME}", id="From entire module"),
        pytest.param(f"from .other_module import {MY_STRING_NAME}", id="From relative module"),
        pytest.param(f"""
import importlib
other_module = importlib.import_module(".other_module", package=__package__)
{MY_STRING_NAME} = other_module.{MY_STRING_NAME}
""", id="From relative module with importlib"),
    ]
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
def test_import_library_package_from_library(variable_access_statement: str, files_manager: ExampleProjectFileManager) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="module",
        content=f"from example_library.example_package import {MY_STRING_NAME}"
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
        "example_library.module",
        MY_STRING_NAME,
    ),
)
def test_import_library_module_from_library_package(variable_access_statement: str, files_manager: ExampleProjectFileManager) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="module",
        content=f"from example_library.example_package import {MY_STRING_NAME}"
    )
    files_manager.create_library_module(
        library_name="example_library",
        module_name="example_package.__init__",
        content=f"""
import example_library.example_package.module
{MY_STRING_NAME} = example_library.example_package.module.{MY_STRING_NAME}
""",
    )
    files_manager.create_library_module(
        library_name="example_library",
        module_name="example_package.module",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=variable_access_statement,
    )
    _assert_my_string_in_module()


def test_import_sys_module_in_project(files_manager: ExampleProjectFileManager) -> None:
    files_manager.create_project_module(
        module_name="module",
        content="import sys"
    )
    import example_project.module
    assert example_project.module.sys.__name__ == "sys"


def test_import_sys_module_in_library(files_manager: ExampleProjectFileManager) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="library_module",
        content="import sys"
    )
    files_manager.create_project_module(
        module_name="module",
        content="from example_library.library_module import sys"
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
def test_import_different_library_in_library(variable_access_statement: str, files_manager: ExampleProjectFileManager) -> None:
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
        content=f"from example_library.library_module import {MY_STRING_NAME}"
    )
    _assert_my_string_in_module()


def test_file_attribute_correct(files_manager: ExampleProjectFileManager) -> None:
    library_name = "example_library"
    library_module_name = "library_module"
    files_manager.create_library_module(
        library_name=library_name,
        module_name=library_module_name,
        content="MY_FILE_PATH = __file__",
    )
    files_manager.create_project_module(
        module_name="module",
        content="from example_library.library_module import MY_FILE_PATH"
    )
    from example_project.module import MY_FILE_PATH
    expected_module_path = (LIBRARIES_PATH / library_name / f"{library_module_name}.py")
    assert Path(MY_FILE_PATH) == expected_module_path


def test_import_same_name_library(files_manager: ExampleProjectFileManager) -> None:
    sys.modules.pop("pytest")
    files_manager.create_library_module(
        library_name="pytest",
        module_name="__init__",
        content=MY_STRING_DECLARATION_MODULE,
    )
    files_manager.create_project_module(
        module_name="module",
        content=f"from pytest import {MY_STRING_NAME}"
    )
    _assert_my_string_in_module()
    import pytest
    assert not hasattr(pytest, MY_STRING_NAME)


def _assert_my_string_in_module() -> None:
    import example_project.module
    assert example_project.module.MY_STRING == MY_STRING_EXPECTED_VALUE
