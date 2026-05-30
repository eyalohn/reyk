from packaging.version import parse as parse_version

import reyk


def test_standard_version() -> None:
    v = parse_version(reyk.VERSION)
    assert str(v) == reyk.VERSION


def test_version_attribute_is_present() -> None:
    assert hasattr(reyk, "__version__")
    assert isinstance(reyk.__version__, str)
