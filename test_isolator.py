# For debugging
import builtins
import importlib
print(builtins.__import__)

import pytest

from tester_get_caller import call_get_caller


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
