# pyright: reportMissingImports=false
import sys
from importlib.metadata import Distribution

from tests.blackbox.example_project_file_manager import ExampleProjectFileManager

DEFINE_DISTRIBUTIONS_STRING = """
import importlib.metadata
DISTRIBUTIONS = list(importlib.metadata.distributions())
"""


def find_distributions_from_project(files_manager: ExampleProjectFileManager) -> list[Distribution]:
    files_manager.create_project_module(
        module_name="module",
        content=DEFINE_DISTRIBUTIONS_STRING,
    )
    import example_project.module

    return example_project.module.DISTRIBUTIONS


def find_distributions_from_library(files_manager: ExampleProjectFileManager) -> list[Distribution]:
    files_manager.create_library_module(
        library_name="my_library",
        module_name="library_module",
        content=DEFINE_DISTRIBUTIONS_STRING,
    )
    files_manager.create_project_module(
        module_name="module",
        content="from my_library.library_module import DISTRIBUTIONS",
    )
    import example_project.module

    return example_project.module.DISTRIBUTIONS


def assert_distribution_names_subset(distributions: list[Distribution], expected_distributions: set[str]) -> None:
    # We use distributions old api to still support Python 3.9
    distribution_names = {dist.metadata["Name"] for dist in distributions}
    assert expected_distributions.issubset(distribution_names)
