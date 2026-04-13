from collections.abc import Iterable
from pathlib import Path
import os
import pytest
from typer.testing import CliRunner


@pytest.fixture(scope="session")
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(scope="session")
def example_pyproject() -> str:
    return (Path(__file__).parent / "example_pyproject.toml").read_text()


@pytest.fixture
def example_project_path(tmpdir: Path, example_pyproject: str) -> Iterable[Path]:
    pyproject = tmpdir / "pyproject.toml"
    pyproject.write_text(example_pyproject, "utf8")
    previous_cwd = Path.cwd()
    os.chdir(tmpdir)
    yield tmpdir
    os.chdir(previous_cwd)
