from collections.abc import Sequence
from abc import ABC, abstractmethod
import pytest

from tests.blackbox.predefined_tests.import_path_extractor import extract_module_name, extract_first_package_name


PytestParam = object  # Sadly there is no type-hint for pytest params


class VariableAccessStatementGenerator(ABC):
    @staticmethod
    @abstractmethod
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam: ...


class AbsoluteImportModuleStatement(VariableAccessStatementGenerator):
    @staticmethod
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam:
        return pytest.param(
            f"""
import {containing_module_import_path}
{variable_name} = {containing_module_import_path}.{variable_name}
            """,
            id="Import entire module then extract variable",
        )


class FromImportStatement(VariableAccessStatementGenerator):
    @staticmethod
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam:
        return pytest.param(
            f"""
from {containing_module_import_path} import {variable_name}
            """,
            id="Import only the variable using from import statement",
        )


class RelativeImportStatement(VariableAccessStatementGenerator):
    @staticmethod
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam:
        module_name = extract_module_name(containing_module_import_path)
        return pytest.param(
            f"""
from .{module_name} import {variable_name}
            """,
            id="Relative from import module",
        )


class StarImportStatement(VariableAccessStatementGenerator):
    @staticmethod
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam:  # noqa: ARG004
        return pytest.param(
            f"""
from {containing_module_import_path} import *
            """,
            id="Import ALL variables using star-import",
        )


class ImportFunctionStatement(VariableAccessStatementGenerator):
    @staticmethod
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam:
        first_package_name = extract_first_package_name(containing_module_import_path)
        return pytest.param(
            f"""
{first_package_name} = __import__("{containing_module_import_path}")
{variable_name} = {containing_module_import_path}.{variable_name}
            """,
            id="Import entire module using __import__ then extract variable",
        )


class ImportLibFunctionStatement(VariableAccessStatementGenerator):
    @staticmethod
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam:
        return pytest.param(
            f"""
import importlib
imported_module = importlib.import_module("{containing_module_import_path}")
{variable_name} = imported_module.{variable_name}
            """,
            id="Import entire module using importlib.import_module then extract variable",
        )


class MimicCPythonImportStatement(VariableAccessStatementGenerator):
    @staticmethod
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam:
        """
        An import in C is usually done with `PyImport_ImportModule` which is basically short for:
        1. Import the module you want to access for example: 'collections.abc' by using builtins.__import__
        2. Retrieve the module from the sys modules
        The second part is done because the first part retrieves the top-level module: for `collections.abc`
        it will be `collections` instead of `collections.abc`.
        """
        return pytest.param(
            f"""
import sys
__import__("{containing_module_import_path}")
imported_module = sys.modules["{containing_module_import_path}"]
{variable_name} = imported_module.{variable_name}
            """,
            id="Mimic C Import by importing then retrieving from sys modules",
        )


ALL_IMPORT_TECHNIQUES_BUT_RELATIVE = (
    AbsoluteImportModuleStatement,
    FromImportStatement,
    StarImportStatement,
    ImportFunctionStatement,
    ImportLibFunctionStatement,
    MimicCPythonImportStatement,
)
ALL_IMPORT_TECHNIQUES = (
    *ALL_IMPORT_TECHNIQUES_BUT_RELATIVE,
    RelativeImportStatement,
)


def generate_variable_access_statement_params(
    statements: Sequence[type[VariableAccessStatementGenerator]],
    containing_module_import_path: str,
    variable_name: str,
) -> Sequence[PytestParam]:
    return [statement.generate(containing_module_import_path, variable_name) for statement in statements]
