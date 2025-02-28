import sys
import logging
from collections.abc import Iterator
from pathlib import Path


LOGGER = logging.getLogger(__name__)
MY_PACKAGE = Path(__file__).parent


def get_caller_path_outside_pyisolate() -> Path:
    for filename in _iterate_over_stack_filenames():
        
        if MY_PACKAGE in Path(filename).parents:
            # This function
            continue

        return Path(filename)
    
    raise ValueError("Failed to find caller outside builtin")


def _is_python_lib(filename: str) -> bool:
    if filename.startswith("<"):
        # frozen builtin
        continue


def _iterate_over_stack_filenames() -> Iterator[str]:
    current_frame = sys._getframe(1)
    while current_frame is not None:
        yield current_frame.f_code.co_filename
        current_frame = current_frame.f_back


def is_caller_part_of_library(library_name: str) -> bool:
    caller_path = get_caller_path_outside_pyisolate()
    return any(
        parent.name == library_name
        for parent in caller_path.parents
    )
