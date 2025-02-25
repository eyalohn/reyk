from collections.abc import Iterator
import sys
from pathlib import Path


MY_PACKAGE = Path(__file__).parent


def get_caller_path() -> Path:
    caller_to_get_caller_filename: str | None = None
    for filename in _iterate_over_stack_filenames():
        if filename.startswith("<"):
            # builtin
            continue
        
        if Path(filename).stem == "caller_finder":
            # This function
            continue

        if caller_to_get_caller_filename is None or caller_to_get_caller_filename == filename:
            caller_to_get_caller_filename = filename
            continue

        return Path(filename)
    
    raise ValueError("Failed to find caller outside builtin")


def _iterate_over_stack_filenames() -> Iterator[str]:
    current_frame = sys._getframe(1)
    while current_frame is not None:
        yield current_frame.f_code.co_filename
        current_frame = current_frame.f_back


def is_caller_part_of_library(library_name: str) -> bool:
    caller_path = get_caller_path()
    return any(
        parent.name == library_name
        for parent in caller_path.parents
    )
