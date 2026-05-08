import sys

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_max_recursion_depth() -> None:
    # Speed up tests in case of recursion errors:
    sys.setrecursionlimit(500)
