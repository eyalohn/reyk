from collections.abc import Iterable
from pathlib import Path
import os
import pytest
from typer.testing import CliRunner
from tests.example_project import ExampleProject


@pytest.fixture(scope="session")
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def example_project(request: pytest.FixtureRequest, tmpdir: Path) -> Iterable[ExampleProject]:
    example_project = ExampleProject(Path(tmpdir), getattr(request, "param", None))
    example_project.write_pyproject_toml()
    previous_cwd = Path.cwd()
    os.chdir(tmpdir)
    yield example_project
    os.chdir(previous_cwd)
