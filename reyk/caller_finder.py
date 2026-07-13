import logging
import sys
from typing import Optional
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable

from reyk.stdlib_finder import is_part_of_stdlib

LOGGER = logging.getLogger(__name__)
MY_PACKAGE_NAME = __package__
MAIN_MODULE_NAME = "__main__"


class NoCallerOutsideLibFoundError(RuntimeError): ...


@dataclass
class StackFrame:
    filename: Path
    module_name: str


def get_caller_matching_package(package_names: Iterable[str]) -> Optional[str]:
    """Returns the deepest matching package name to the caller"""
    try:
        caller_frame = get_caller_frame_outside_reyk()
    except NoCallerOutsideLibFoundError:
        return None

    matching_package_names = [
        package_name for package_name in package_names if is_frame_from_package(package_name, caller_frame)
    ]
    if len(matching_package_names) == 0:
        return None
    return max(
        matching_package_names,
        key=get_package_depth,
    )


def get_package_depth(package_name: str) -> int:
    return package_name.count(".")


def is_frame_from_package(package_name: str, frame: StackFrame) -> bool:
    caller_module_name = frame.module_name
    return (caller_module_name == package_name) or (caller_module_name.startswith(f"{package_name}."))


def get_caller_frame_outside_reyk() -> StackFrame:
    for frame in _iterate_over_stack():
        if is_part_of_stdlib(frame.module_name):
            continue

        if frame.module_name == MY_PACKAGE_NAME or frame.module_name.startswith(f"{MY_PACKAGE_NAME}."):
            # This function
            continue

        return frame

    raise NoCallerOutsideLibFoundError("Failed to find caller outside builtin")


def _iterate_over_stack() -> Iterable[StackFrame]:
    current_frame = sys._getframe(1)  # noqa: SLF001
    while current_frame is not None:
        module_name = current_frame.f_globals["__name__"]
        if module_name == MAIN_MODULE_NAME:
            module_name = current_frame.f_globals["__spec__"].name

        yield StackFrame(
            filename=Path(current_frame.f_code.co_filename),
            module_name=module_name,
        )
        current_frame = current_frame.f_back
