# pyright: reportMissingImports=false
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import FrameType, ModuleType
from typing import Optional

import pytest

from reyk.isolator_definition import VendorPackage, ContextDetectionConfig, CodeLocation
from reyk.module_name_utils import _FilePathModuleNameExtractor
from tests.blackbox.example_project_file_manager import ExampleProjectFileManager
from tests.blackbox.libraries_manager import LibrariesManager


EXTERNAL_PROXY_MODULE = """
from reyk.caller_finder import get_caller_matching_package

def forward(packages):
    return get_caller_matching_package(packages)

def find_spec(packages):
    return get_caller_matching_package(packages)

def other_function(packages):
    return get_caller_matching_package(packages)
"""

CALLER_MODULE = """
from reyk.caller_finder import get_caller_matching_package

def find_package(packages):
    return get_caller_matching_package(packages)

def call_forward(proxy, packages):
    return proxy.forward(packages)

def call_find_spec(proxy, packages):
    return proxy.find_spec(packages)

def call_other_function(proxy, packages):
    return proxy.other_function(packages)
"""


@pytest.fixture
def external_proxy_module(libraries_manager: LibrariesManager) -> ModuleType:
    library_files_manager = libraries_manager.create_library("external_proxy")
    library_files_manager.create_project_module(module_name="__init__", content=EXTERNAL_PROXY_MODULE)

    import external_proxy

    return external_proxy


@pytest.fixture
def caller_module(files_manager: ExampleProjectFileManager) -> ModuleType:
    files_manager.create_project_module(module_name="module", content=CALLER_MODULE)

    import example_project.module

    return example_project.module


@pytest.mark.parametrize(
    "context_detection_config",
    [
        pytest.param(ContextDetectionConfig(), id="default-config"),
        pytest.param(ContextDetectionConfig(user_ignore_rules=()), id="empty-user-rules"),
        pytest.param(
            ContextDetectionConfig(user_ignore_rules=(CodeLocation(module="another_proxy"),)),
            id="custom-user-rules",
        ),
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "function_name",
    [
        pytest.param("find_spec", id="system-rule-matches"),
        pytest.param("other_function", id="system-rule-does-not-match-other-functions"),
    ],
)
def test_system_virtualenv_rule_always_applies_and_only_skips_find_spec(
    external_proxy_module: ModuleType,
    caller_module: ModuleType,
    vendor_package: VendorPackage,
    monkeypatch: pytest.MonkeyPatch,
    function_name: str,
) -> None:
    # Give the real helper module virtualenv's declared name without replacing the installed virtualenv hook.
    monkeypatch.setattr(external_proxy_module, "__name__", "_virtualenv")
    call_proxy = caller_module.call_find_spec if function_name == "find_spec" else caller_module.call_other_function
    expected_package_name = "example_project" if function_name == "find_spec" else None

    assert call_proxy(external_proxy_module, [vendor_package]) == expected_package_name


@pytest.mark.parametrize(
    ("context_detection_config", "expected_package_name"),
    [
        pytest.param(ContextDetectionConfig(), None, id="no-user-rules"),
        pytest.param(
            ContextDetectionConfig(user_ignore_rules=(CodeLocation(module="external_proxy"),)),
            "example_project",
            id="matching-module",
        ),
        pytest.param(
            ContextDetectionConfig(user_ignore_rules=(CodeLocation(module="external_proxy", function="forward"),)),
            "example_project",
            id="matching-function",
        ),
        pytest.param(
            ContextDetectionConfig(user_ignore_rules=(CodeLocation(module="external_proxy", function="other"),)),
            None,
            id="different-function",
        ),
        pytest.param(
            ContextDetectionConfig(user_ignore_rules=(CodeLocation(module="external"),)),
            None,
            id="parent-name-does-not-match",
        ),
        pytest.param(
            ContextDetectionConfig(user_ignore_rules=(CodeLocation(module="external_proxy.child"),)),
            None,
            id="child-name-does-not-match",
        ),
    ],
    indirect=["context_detection_config"],
)
def test_context_detection_ignores_only_matching_locations(
    external_proxy_module: ModuleType,
    caller_module: ModuleType,
    vendor_package: VendorPackage,
    expected_package_name: Optional[str],
) -> None:
    assert caller_module.call_forward(external_proxy_module, [vendor_package]) == expected_package_name


@pytest.mark.parametrize(
    "context_detection_config",
    [ContextDetectionConfig(user_ignore_rules=(CodeLocation(module="external_proxy"),))],
    indirect=True,
)
@pytest.mark.parametrize(
    ("caller_module_name", "expected_package_name"),
    [
        pytest.param("example_project.module", "example_project", id="example-project"),
        pytest.param("another_project", None, id="another-project"),
    ],
)
def test_context_detection_rules_do_not_leak_between_packages(  # noqa: PLR0913
    *,
    libraries_manager: LibrariesManager,
    external_proxy_module: ModuleType,
    caller_module: ModuleType,
    vendor_package: VendorPackage,
    caller_module_name: str,
    expected_package_name: Optional[str],
) -> None:
    library_files_manager = libraries_manager.create_library("another_project")
    library_files_manager.create_project_module(module_name="__init__", content=CALLER_MODULE)

    import another_project

    another_package = VendorPackage(
        package_name="another_project",
        package_directory=library_files_manager.project_path,
        vendor_libs_path=library_files_manager.project_path,
    )
    caller_modules_by_name = {module.__name__: module for module in (caller_module, another_project)}
    calling_module = caller_modules_by_name[caller_module_name]

    assert (
        calling_module.call_forward(external_proxy_module, [vendor_package, another_package]) == expected_package_name
    )


@pytest.mark.parametrize(
    "context_detection_config",
    [
        pytest.param(
            ContextDetectionConfig(user_ignore_rules=(CodeLocation(module="external_proxy"),)),
            id="declared-module-name",
        ),
        pytest.param(
            ContextDetectionConfig(user_ignore_rules=(CodeLocation(module="spec_proxy"),)),
            id="spec-module-name",
        ),
    ],
    indirect=True,
)
def test_ignore_matching_does_not_extract_file_paths(
    external_proxy_module: ModuleType,
    caller_module: ModuleType,
    vendor_package: VendorPackage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_path_extraction = _FilePathModuleNameExtractor._get_module_file_path

    def unexpected_path_extraction(frame: FrameType) -> Optional[Path]:
        if frame.f_globals.get("__name__") in ("external_proxy", "example_project.module"):
            raise AssertionError("Ignore matching must not trigger file-path extraction")
        return original_path_extraction(frame)

    monkeypatch.setattr(external_proxy_module, "__spec__", ModuleSpec("spec_proxy", loader=None))
    with monkeypatch.context() as path_guard:
        path_guard.setattr(
            _FilePathModuleNameExtractor, "_get_module_file_path", staticmethod(unexpected_path_extraction)
        )
        package_through_proxy = caller_module.call_forward(external_proxy_module, [vendor_package])
        package_without_proxy = caller_module.find_package([vendor_package])

    assert package_through_proxy == "example_project"
    assert package_without_proxy == "example_project"


@pytest.mark.parametrize(
    "context_detection_config",
    [ContextDetectionConfig(user_ignore_rules=(CodeLocation(module="example_project.proxy"),))],
    indirect=True,
)
def test_path_derived_names_determine_ownership_but_do_not_match_ignore_rules(
    files_manager: ExampleProjectFileManager, vendor_package: VendorPackage, monkeypatch: pytest.MonkeyPatch
) -> None:
    files_manager.create_project_module(module_name="proxy", content=EXTERNAL_PROXY_MODULE)

    import example_project.proxy

    monkeypatch.setattr(example_project.proxy, "__name__", "external_alias")
    monkeypatch.setattr(example_project.proxy, "__spec__", None)

    assert example_project.proxy.forward([vendor_package]) == "example_project"
