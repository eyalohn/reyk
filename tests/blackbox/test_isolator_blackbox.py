from pathlib import Path
import pytest
from tests.blackbox.files_manager import ExampleProjectFileManager
from tests.blackbox.variable_access_statement_generator import generate_variable_access_statement_params
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
        "example_library.library_module",
        MY_STRING_NAME,
        relative_import=None,
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
        "example_library",
        MY_STRING_NAME,
        relative_import=None,
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
        "example_library.module",
        MY_STRING_NAME,
        relative_import=None,
    ),
)
def test_import_library_module_from_library(variable_access_statement: str, files_manager: ExampleProjectFileManager) -> None:
    files_manager.create_library_module(
        library_name="example_library",
        module_name="module",
        content=f"from example_library.other_module import {MY_STRING_NAME}",
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
        "example_library.module",
        MY_STRING_NAME,
        relative_import=None,
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
        "another_library.another_module",
        MY_STRING_NAME,
        relative_import=None,
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


# def test_file_attribute_correct(files_manager: ExampleProjectFileManager) -> None:
#     library_name = "example_library"
#     library_module_name = "library_module"
#     files_manager.create_library_module(
#         library_name=library_name,
#         module_name=library_module_name,
#         content="MY_FILE_PATH = __file__",
#     )
#     files_manager.create_project_module(
#         module_name="module",
#         content="from example_library.library_module import MY_FILE_PATH"
#     )
#     from example_project.module import MY_FILE_PATH
#     assert MY_FILE_PATH == (LIBRARIES_PATH / library_name / f"{library_module_name}.py")


def test_import_same_name_library() -> None:
    ...


def _assert_my_string_in_module() -> None:
    import example_project.module
    assert example_project.module.MY_STRING == MY_STRING_EXPECTED_VALUE
