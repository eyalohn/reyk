from pathlib import Path
from typer.testing import CliRunner
from pyisolate_cli.cli import app


def test_sync_no_vendor_libs_specified(runner: CliRunner, example_project_path: Path) -> None:
    result = runner.invoke(app, "sync")
    assert result.exit_code != 0, "Vendor libs does not exist in pyproject toml but sync works."


def test_add(runner: CliRunner, example_project_path: Path) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0
    assert (example_project_path / DEFAULT_LIBRARIES_TARGET_PATH / "tomli").exists()


def test_remove_existing_package(runner: CliRunner, example_project_path: Path) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["remove", "tomli"])
    assert result.exit_code == 0
    assert not (example_project_path / DEFAULT_LIBRARIES_TARGET_PATH / "tomli").exists()


def test_remove_non_existing_package(runner: CliRunner, example_project_path: Path) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["remove", "pytest"])
    assert result.exit_code != 0
    assert (example_project_path / DEFAULT_LIBRARIES_TARGET_PATH / "tomli").exists()
    assert not (example_project_path / DEFAULT_LIBRARIES_TARGET_PATH / "pytest").exists()


def test_add_then_sync_multiple_times(runner: CliRunner, example_project_path: Path) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0

    for _ in range(10):
        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0
    assert (example_project_path / DEFAULT_LIBRARIES_TARGET_PATH / "tomli").exists()


def test_add_to_unrelated_group(runner: CliRunner, example_project_path: Path) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["add", "requests", "--group", "unrelated-group"])
    assert result.exit_code != 0, (
        "Adding to a group with pyisolate-cli that isn't in 'vendor-groups' should result in an error"
    )

    assert (example_project_path / DEFAULT_LIBRARIES_TARGET_PATH / "tomli").exists()
    assert not (example_project_path / DEFAULT_LIBRARIES_TARGET_PATH / "requests").exists()


def test_add_to_unrelated_group(runner: CliRunner, example_project_path: Path) -> None:
    result = runner.invoke(app, ["add", "tomli"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["add", "requests", "--group", "unrelated-group"])
    assert result.exit_code != 0, (
        "Adding to a group with pyisolate-cli that isn't in 'vendor-groups' should result in an error"
    )

    assert (example_project_path / DEFAULT_LIBRARIES_TARGET_PATH / "tomli").exists()
    assert not (example_project_path / DEFAULT_LIBRARIES_TARGET_PATH / "requests").exists()


def test_add_then_remove_multiple_groups(runner: CliRunner, example_project_path: Path) -> None:
    ...
