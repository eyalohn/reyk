# pyright: reportMissingImports=false
from typing import Optional, cast
import pytest
from importlib.metadata import Distribution, DistributionFinder
from pyisolate.vendor_importer import get_installed_vendor_importer
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager


@pytest.mark.parametrize("library_names", [pytest.param(set(), id="")])
def test_find_distributions(
    files_manager: ExampleProjectFileManager,
    library_names: set[str],
) -> None:
    for library_name in library_names:
        files_manager.create_library_module(
            library_name=library_name,
            module_name="library_module",
            content="",
        )

    files_manager.create_project_module(
        module_name="module",
        content="""
vendor_importer = get_installed_vendor_importer()
DISTRIBUTIONS = list(vendor_importer.find_distributions())
""",
    )
    import example_project.module

    actual_distribution_names = {
        distribution.name for distribution in cast(list[Distribution], example_project.module.DISTRIBUTIONS)
    }
    assert actual_distribution_names == library_names
