import sys
from collections.abc import Iterator
import pytest

from tester_get_caller import call_get_caller


@pytest.fixture(autouse=True)
def cleanup_modules() -> Iterator:
    original = sys.modules.copy()
    yield
    sys.modules.clear()
    sys.modules.update(original)


def test_get_caller() -> None:
    caller = call_get_caller()
    assert caller.stem == "test_isolator"


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


def test_relative_import() -> None:
    import my_other_package
    assert my_other_package.relative_import_me.RELATIVE_IMPORT_VALUE == 0xEFEF
