from pyisolate.caller_finder import get_caller_frame_outside_pyisolate


def test_get_caller() -> None:
    caller = get_caller_frame_outside_pyisolate()
    assert caller.module_name == "tests.internals.test_internals"
