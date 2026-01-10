from collections.abc import Iterator
import sys
import logging
from pathlib import Path
from dataclasses import dataclass
from pyisolate.stdlib_finder import is_part_of_stdlib


LOGGER = logging.getLogger(__name__)
MY_PACKAGE_NAME = __package__


class NoCallerOutsideLibFoundError(RuntimeError): ...


@dataclass
class StackFrame:
    filename: Path
    module_name: str


def get_caller_frame_outside_pyisolate() -> StackFrame:
    for frame in _iterate_over_stack():
        print(f"Frame in stack: {frame}")
        if is_part_of_stdlib(frame.module_name):
            continue

        if frame.module_name == MY_PACKAGE_NAME or frame.module_name.startswith(f"{MY_PACKAGE_NAME}."):
            # This function
            continue

        return frame

    raise NoCallerOutsideLibFoundError("Failed to find caller outside builtin")


def _iterate_over_stack() -> Iterator[StackFrame]:
    current_frame = sys._getframe(1)  # noqa: SLF001
    while current_frame is not None:
        yield StackFrame(
            filename=Path(current_frame.f_code.co_filename),
            module_name=current_frame.f_globals["__name__"],
        )
        current_frame = current_frame.f_back


def is_caller_part_of_library(library_name: str) -> bool:
    try:
        caller_frame = get_caller_frame_outside_pyisolate()
    except NoCallerOutsideLibFoundError:
        return False
    caller_module_name = caller_frame.module_name
    return (caller_module_name == library_name) or (caller_module_name.startswith(f"{library_name}."))
