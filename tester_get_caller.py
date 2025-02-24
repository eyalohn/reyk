import inspect
from isolator import caller_finder


def call_get_caller() -> inspect.FrameInfo:
    return caller_finder.get_caller()
