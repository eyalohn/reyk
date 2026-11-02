import logging
import sys
from itertools import chain
from typing import Optional, cast
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable, Iterator, Sequence

from reyk.isolator_definition import VendorPackage
from reyk.stdlib_finder import is_part_of_stdlib
from reyk.module_name_utils import extract_module_name_from_frame, is_module_from_package, get_module_packages_count
from reyk.vendor_packages_store import VendorPackageModules, VendorPackagesStore

LOGGER = logging.getLogger(__name__)
MY_PACKAGE_NAME = cast(str, __package__)


class NoCallerOutsideLibFoundError(RuntimeError): ...


@dataclass
class StackFrame:
    filename: Path
    module_names_iter: Iterator[str]


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
    """
    try:
        caller_frame = get_caller_frame_outside_reyk(packages)
    except NoCallerOutsideLibFoundError:
        return None

    return _get_matching_package_from_module_names(caller_frame.module_names_iter, packages)


def _get_matching_package_from_module_names(
    module_names: Iterable[str],
    packages: Sequence[VendorPackage],
) -> Optional[str]:
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
    for frame in _iterate_over_stack(packages):
        module_name = next(frame.module_names_iter, None)
        if module_name is None:
            return frame

        if is_part_of_stdlib(module_name):
            continue

        if is_module_from_package(module_name, MY_PACKAGE_NAME):
            # This function
            continue

        frame.module_names_iter = chain((module_name,), frame.module_names_iter)
        return frame

    raise NoCallerOutsideLibFoundError("Failed to find caller outside builtin")


def _iterate_over_stack(packages: Optional[Sequence[VendorPackage]]) -> Iterable[StackFrame]:
    current_frame = sys._getframe(1)  # noqa: SLF001
    while current_frame is not None:
        yield StackFrame(
            filename=Path(current_frame.f_code.co_filename),
            module_names_iter=extract_module_name_from_frame(current_frame, packages),
        )
        current_frame = current_frame.f_back
