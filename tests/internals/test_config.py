from pathlib import Path

import pytest

from reyk.isolator_definition import CodeLocation, VendorPackage


@pytest.mark.parametrize(
    "location",
    [
        pytest.param({"module": ""}, id="empty-module-name"),
        pytest.param({"module": "proxy", "function": ""}, id="empty-function-name"),
    ],
)
def test_empty_code_location_names_are_rejected(location: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        CodeLocation(**location)


@pytest.mark.parametrize(
    ("package_directory", "vendor_libs_path", "invalid_directory_field"),
    [
        pytest.param("invalid_directory", ".", "package_directory", id="package-directory"),
        pytest.param(".", "invalid_directory", "vendor_libs_path", id="vendor-libraries-directory"),
    ],
)
@pytest.mark.parametrize(
    "should_create_file",
    [
        pytest.param(False, id="missing-path"),
        pytest.param(True, id="regular-file"),
    ],
)
def test_vendor_package_rejects_invalid_directories(
    *,
    tmp_path: Path,
    package_directory: str,
    vendor_libs_path: str,
    invalid_directory_field: str,
    should_create_file: bool,
) -> None:
    invalid_path = tmp_path / "invalid_directory"
    if should_create_file:
        invalid_path.write_text("")

    with pytest.raises(ValueError, match=rf"^{invalid_directory_field} "):
        VendorPackage(
            package_name="example_project",
            package_directory=tmp_path / package_directory,
            vendor_libs_path=tmp_path / vendor_libs_path,
        )
