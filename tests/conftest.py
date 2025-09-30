from collections.abc import Iterable
import sys

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_max_recursion_depth() -> None:
    # Speed up tests in case of recursion errors:
    sys.setrecursionlimit(200)


@pytest.fixture(autouse=True)
def cleanup_modules() -> Iterable:
    original = sys.modules.copy()
    yield
    sys.modules.clear()
    sys.modules.update(original)
