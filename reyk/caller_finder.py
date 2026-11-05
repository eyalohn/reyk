import logging
import sys
from typing import Optional, cast
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable, Sequence

from reyk.isolator_definition import VendorPackage
from reyk.stdlib_finder import is_part_of_stdlib
from reyk.module_name_utils import (
    ModuleNameCandidates,
    ModuleNameSource,
    extract_module_names_from_frame,
    is_module_from_package,
    get_module_packages_count,
)
from reyk.vendor_packages_store import VendorPackageModules, VendorPackagesStore

LOGGER = logging.getLogger(__name__)
MY_PACKAGE_NAME = cast(str, __package__)


class NoCallerOutsideLibFoundError(RuntimeError): ...


@dataclass
class StackFrame:
    filename: Path
    module_names: ModuleNameCandidates
    function_name: str


@dataclass
class FrameIgnoreRulePartition:
    packages_to_check_at_current_frame: list[VendorPackage]
    packages_ignoring_current_frame: list[VendorPackage]


def get_caller_matching_package_from_store(
    packages_store: VendorPackagesStore,
) -> Optional[VendorPackageModules]:
    package_name = get_caller_matching_package(packages=packages_store.get_vendor_packages())
    if package_name is None:
        return None

    return packages_store.get_package_by_name(package_name)


def get_caller_matching_package(packages: Sequence[VendorPackage]) -> Optional[str]:
    """
    Returns the matching package name to the caller.
    Tries module name candidates in extraction order and returns on the first match.
    If there's multiple packages that may match then it picks the package with the most parents to the caller.
    Because the module imports are not relative (an isolated package inside another isolated package will
    be first_package.libs.second_package) - then picking the package with the most parents will
    result in the most inner package which initiated the import.
    A package may look past an external caller only when its own context detection rules ignore that location.
    """
    for caller_frame, packages_to_check_at_current_frame in _iterate_caller_frames_with_package_ignore_rules(packages):
        matching_package = _get_matching_package_from_module_names(
            caller_frame.module_names.iter_all_names(),
            packages_to_check_at_current_frame,
        )
        if matching_package is not None:
            return matching_package

    return None


def _get_matching_package_from_module_names(
    module_names: Iterable[str],
    packages: Sequence[VendorPackage],
) -> Optional[str]:
    if len(packages) == 0:
        return None

    for module_name in module_names:
        matching_package = _get_matching_package_from_module_name(module_name, packages)
        if matching_package is not None:
            return matching_package

    return None


def _get_matching_package_from_module_name(module_name: str, packages: Sequence[VendorPackage]) -> Optional[str]:
    matching_package_names = (
        package.package_name for package in packages if is_module_from_package(module_name, package.package_name)
    )
    return max(matching_package_names, key=get_module_packages_count, default=None)


def get_caller_frame_outside_reyk(packages: Optional[Sequence[VendorPackage]] = None) -> StackFrame:
    for frame in _iterate_caller_frames(packages):
        return frame

    raise NoCallerOutsideLibFoundError("Failed to find caller outside builtin")


def _iterate_caller_frames_with_package_ignore_rules(
    packages: Sequence[VendorPackage],
) -> Iterable[tuple[StackFrame, Sequence[VendorPackage]]]:
    """Yield frames with packages to check, skipping locations according to each package's rules."""
    packages_allowed_to_continue = packages
    for frame in _iterate_caller_frames(packages):
        partition = _partition_packages_by_frame_ignore_rules(frame, packages_allowed_to_continue)
        if len(partition.packages_to_check_at_current_frame) > 0:
            yield frame, partition.packages_to_check_at_current_frame

        packages_allowed_to_continue = partition.packages_ignoring_current_frame
        if len(packages_allowed_to_continue) == 0:
            return


def _partition_packages_by_frame_ignore_rules(
    frame: StackFrame, packages: Sequence[VendorPackage]
) -> FrameIgnoreRulePartition:
    """Return packages to check here and packages allowed to continue to callers."""
    packages_to_check_at_current_frame: list[VendorPackage] = []
    packages_ignoring_current_frame: list[VendorPackage] = []
    for package in packages:
        if _should_ignore_frame(frame, package):
            packages_ignoring_current_frame.append(package)
        else:
            packages_to_check_at_current_frame.append(package)
    return FrameIgnoreRulePartition(
        packages_to_check_at_current_frame=packages_to_check_at_current_frame,
        packages_ignoring_current_frame=packages_ignoring_current_frame,
    )


def _should_ignore_frame(frame: StackFrame, package: VendorPackage) -> bool:
    # We can eliminate more easily by function first before proceeding to module names
    modules_with_matching_ignore_rules = {
        rule.module
        for rule in package.context_detection.ignore
        if rule.function is None or rule.function == frame.function_name
    }
    return len(modules_with_matching_ignore_rules) > 0 and not modules_with_matching_ignore_rules.isdisjoint(
        frame.module_names.iter_declared_names()
    )


def _iterate_caller_frames(packages: Optional[Sequence[VendorPackage]]) -> Iterable[StackFrame]:
    for frame in _iterate_over_stack(packages):
        module_declared_name = frame.module_names.get(ModuleNameSource.DECLARED)
        if module_declared_name is not None:
            if is_part_of_stdlib(module_declared_name):
                continue

            if is_module_from_package(module_declared_name, MY_PACKAGE_NAME):
                # This function
                continue

        yield frame


def _iterate_over_stack(packages: Optional[Sequence[VendorPackage]]) -> Iterable[StackFrame]:
    current_frame = sys._getframe(1)  # noqa: SLF001
    while current_frame is not None:
        yield StackFrame(
            filename=Path(current_frame.f_code.co_filename),
            function_name=current_frame.f_code.co_name,
            module_names=extract_module_names_from_frame(current_frame, packages),
        )
        current_frame = current_frame.f_back
