import sys
from collections.abc import Iterator

import pytest
from isolator.caller_finder import get_caller_frame_outside_pyisolate


@pytest.fixture(scope="session", autouse=True)
def set_max_recursion_depth() -> None:
    # Speed up tests in case of recursion errors:
    sys.setrecursionlimit(200)


@pytest.fixture(autouse=True)
def cleanup_modules() -> Iterator:
    original = sys.modules.copy()
    yield
    sys.modules.clear()
    sys.modules.update(original)


def test_get_caller() -> None:
    caller = get_caller_frame_outside_pyisolate()
    assert caller.module_name == "test_isolator"


def test_import_my_package() -> None:
    import my_package


def test_import_my_other_package() -> None:
    import my_other_package


def test_speak_in_tests() -> None:
    import my_package
    sentence = my_package.speak()
    print(sentence)
    assert sentence == "Hello, this is in the tests directory"


def test_speak_in_venv() -> None:
    import my_other_package
    output = "This is inside my package"
    assert my_other_package.speak_my_package() == output


def test_packages_are_different() -> None:
    import my_package
    import my_other_package
    assert my_package is not my_other_package.my_package


def test_can_import_builtin() -> None:
    import my_other_package
    assert my_other_package.sys is sys


def test_another_package_import() -> None:
    import my_other_package
    assert my_other_package.another_package.ANOTHER_PACKAGE_VALUE == 0xABCD


def test_absolute_import() -> None:
    import my_other_package
    assert my_other_package.my_other_package.absolute_import_me.ABSOLUTE_IMPORT_ME == 0xAAAA


def test_from_import() -> None:
    import my_other_package
    assert my_other_package.from_import_me.FROM_IMPORT_ME == 0xBBBB


def test_relative_import() -> None:
    import my_other_package
    assert my_other_package.relative_import_me.RELATIVE_IMPORT_VALUE == 0xEFEF


sys.setrecursionlimit(500)
import logging
logging.basicConfig(level=logging.DEBUG)
import my_other_package
