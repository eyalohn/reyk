import pytest
from reyk_cli.cli import app
from reyk_cli.configuration_reader import (
    DEFAULT_LIBRARIES_TARGET_PATH,
    DEFAULT_VENDOR_GROUP,
    DEFAULT_VENDOR_GROUPS,
    ReykConfiguration,
)
from typer.testing import CliRunner

from tests.blackbox.project_paths import EXAMPLE_PROJECT_NAME
from tests.example_project import ExampleProject


def test_add(runner: CliRunner, example_project: ExampleProject) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0
    assert example_project.get_existing_libraries() == {"tomli"}


def test_remove_existing_package(runner: CliRunner, example_project: ExampleProject) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["remove", "tomli"])
    assert result.exit_code == 0
    assert example_project.get_existing_libraries() == set()


def test_remove_non_existing_package(runner: CliRunner, example_project: ExampleProject) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["remove", "pytest"])
    assert result.exit_code != 0
    assert example_project.get_existing_libraries() == {"tomli"}


def test_add_then_sync_multiple_times(runner: CliRunner, example_project: ExampleProject) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0

    for _ in range(10):
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0

    assert example_project.get_existing_libraries() == {"tomli"}


def test_add_to_unrelated_group(runner: CliRunner, example_project: ExampleProject) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["add", "tomli-w", "--group", "unrelated-group"])
    assert result.exit_code != 0, (
        "Adding to a group with reyk-cli that isn't in 'vendor-groups' should result in an error"
    )

    assert example_project.get_existing_libraries() == {"tomli"}


@pytest.mark.parametrize(
    EXAMPLE_PROJECT_NAME,
    [
        ReykConfiguration(
            libraries_path=DEFAULT_LIBRARIES_TARGET_PATH,
            vendor_groups={DEFAULT_VENDOR_GROUP, "another-vendored-group"},
            vendor_exclusions=set(),
        ),
    ],
    indirect=True,
)
def test_add_to_new_vendor_groups(runner: CliRunner, example_project: ExampleProject) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code != 0  # Because another-vendored-group does not exist
    result = runner.invoke(app, ["add", "tomli-w", "--group", "another-vendored-group"])
    assert result.exit_code == 0

    assert example_project.get_existing_libraries() == {"tomli", "tomli_w"}


@pytest.mark.parametrize(
    EXAMPLE_PROJECT_NAME,
    [
        ReykConfiguration(
            libraries_path=DEFAULT_LIBRARIES_TARGET_PATH,
            vendor_groups={"different-vendored-group"},
            vendor_exclusions=set(),
        ),
    ],
    indirect=True,
)
def test_change_vendor_libs(runner: CliRunner, example_project: ExampleProject) -> None:
    result = runner.invoke(app, ["add", "tomli", "--group", "different-vendored-group"])
    assert result.exit_code == 0

    assert example_project.get_existing_libraries() == {"tomli"}


def test_sync_no_vendor_groups(runner: CliRunner, example_project: ExampleProject) -> None:
    result = runner.invoke(app, "sync")
    assert result.exit_code != 0, "Vendor groups does not exist in pyproject toml but sync works."
    assert not example_project.has_libs_directory()  # sync did not work


@pytest.mark.parametrize(
    EXAMPLE_PROJECT_NAME,
    [
        ReykConfiguration(
            libraries_path="different_libs",
            vendor_groups=DEFAULT_VENDOR_GROUPS,
            vendor_exclusions=set(),
        ),
    ],
    indirect=True,
)
def test_change_vendor_target(runner: CliRunner, example_project: ExampleProject) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0

    assert example_project.get_existing_libraries() == {"tomli"}


@pytest.mark.parametrize(
    EXAMPLE_PROJECT_NAME,
    [
        ReykConfiguration(
            libraries_path=DEFAULT_LIBRARIES_TARGET_PATH,
            vendor_groups=DEFAULT_VENDOR_GROUPS,
            vendor_exclusions={"colorama"},
        ),
    ],
    indirect=True,
)
def test_vendor_exclusions(runner: CliRunner, example_project: ExampleProject) -> None:
    result = runner.invoke(app, ["add", "tqdm"])
    assert result.exit_code == 0

    assert example_project.get_existing_libraries() == {"tqdm"}
