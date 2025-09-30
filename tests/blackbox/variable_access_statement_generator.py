from typing import TypeAlias
from collections.abc import Sequence
import pytest


PytestParam: TypeAlias = object  # Sadly there is no type-hint for pytest params


class UseDefault:
    ...


def generate_variable_access_statement_params(
    containing_module_name: str,
    variable_name: str,
    relative_import: str | type[UseDefault] | None = UseDefault,
) -> Sequence[PytestParam]:
    variable_access_statements = [
        pytest.param(
            f"""
import {containing_module_name}
{variable_name} = {containing_module_name}.{variable_name}
            """,
            id="Import entire module then extract variable"
        ),
        pytest.param(
            f"""
from {containing_module_name} import {variable_name}
            """,
            id="Import only the variable using from import statement",
        ),
        pytest.param(
            f"""
from {containing_module_name} import *
            """,
            id="Import ALL variables using star-import"
        ),
        pytest.param(
            f"""
imported_module = __import__("{containing_module_name}")
{variable_name} = imported_module.{containing_module_name.partition(".")[-1]}.{variable_name}
            """,
            id="Import entire module using __import__ then extract variable",
        ),
    ]
    if relative_import is not None:
        default_relative_import = containing_module_name.rpartition(".")[-1]
        variable_access_statements.append(
            pytest.param(
            f"""
from .{(
    default_relative_import if relative_import is UseDefault else relative_import
)} import {variable_name}
                """,
                id="Relative from import module",
            )
        )
    
    return tuple(variable_access_statements)
