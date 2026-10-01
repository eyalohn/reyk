from packaging.version import parse as parse_version

from reyk_cli.version import VERSION


def test_standard_version() -> None:
    v = parse_version(VERSION)
    assert str(v) == VERSION
