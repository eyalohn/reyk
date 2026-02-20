import os
import sys
from pathlib import Path
from functools import cache
from collections.abc import Iterator


@cache
def list_stdlib_modules() -> list[str]:
    return list(_list_stdlib_modules_iter())


def _list_stdlib_modules_iter() -> Iterator[str]:
    standard_lib_dir = Path(os.__file__).parent
    for std_lib_file in standard_lib_dir.iterdir():
        if _is_package(std_lib_file) or (std_lib_file.suffix == ".py"):
            yield std_lib_file.stem

    yield from sys.builtin_module_names


def _is_package(path: Path) -> bool:
    return path.is_dir() and (path / "__init__.py").exists()


def is_part_of_stdlib(module_name: str) -> bool:
    library_name, _, _ = module_name.partition(".")
    return library_name in list_stdlib_modules()
