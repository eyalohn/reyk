from pathlib import Path
from isolator import caller_finder


def call_get_caller() -> Path:
    return caller_finder.get_caller_path()
