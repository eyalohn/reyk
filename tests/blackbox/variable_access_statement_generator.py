from typing import TypeAlias
from collections.abc import Sequence
from abc import ABC, abstractmethod
import pytest

from tests.blackbox.import_path_extractor import extract_module_name, extract_first_package_name


PytestParam: TypeAlias = object  # Sadly there is no type-hint for pytest params


class VariableAccessStatementGenerator(ABC):
    @staticmethod
    @abstractmethod
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam:
        ...


class AbsoluteImportModuleStatement(VariableAccessStatementGenerator):
    @staticmethod
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam:
        return pytest.param(
            f"""
import {containing_module_import_path}
{variable_name} = {containing_module_import_path}.{variable_name}
            """,
            id="Import entire module then extract variable"
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
    def generate(containing_module_import_path: str, variable_name: str) -> PytestParam:
        return pytest.param(
            f"""
from {containing_module_import_path} import *
            """,
            id="Import ALL variables using star-import"
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


ALL_IMPORT_TECHNIQUES_BUT_RELATIVE = (
    AbsoluteImportModuleStatement,
    FromImportStatement,
    StarImportStatement,
    ImportFunctionStatement,
    ImportLibFunctionStatement,
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
    return [
        statement.generate(containing_module_import_path, variable_name)
        for statement in statements
    ]
