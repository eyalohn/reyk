import inspect
from pathlib import Path


MY_PACKAGE = Path(__file__).parent


def get_caller() -> inspect.FrameInfo:
    stack: list[inspect.FrameInfo] = inspect.stack()
    caller_to_get_caller: inspect.FrameInfo | None = None
    for frame in stack:
        if frame.filename.startswith("<"):
            # builtin
            continue
        
        if Path(frame.filename).stem == "caller_finder":
            # This function
            continue

        if caller_to_get_caller is None or caller_to_get_caller.filename == frame.filename:
            caller_to_get_caller = frame
            continue

        return frame
    
    raise ValueError(f"Failed to find caller outside builtin: {stack=}")


def get_caller_dir_name() -> str:
    caller_frame = get_caller()
    return Path(caller_frame.filename).parent.name
