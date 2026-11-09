from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from enum import Enum, auto
from functools import cached_property
from importlib.util import resolve_name
import logging
from typing import Optional, Union

from reyk.caller_finder import get_caller_matching_package_from_store
from reyk.isolator_definition import VendorPackage
from reyk.module_name_utils import is_module_from_package
from reyk.stdlib_finder import is_part_of_stdlib
from reyk.vendor_packages_store import VendorPackagesStore

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PackageFromGlobals:
    pass


@dataclass(frozen=True)
class PackageFromArgument:
    package: Optional[str]


RelativePackage = Union[PackageFromGlobals, PackageFromArgument]


class ErrorPolicy(Enum):
    RAISE_ERROR = auto()
    IGNORE_IF_ANCESTOR = auto()


@dataclass(frozen=True)
class ImportTarget:
    name: str
    package: Optional[str]

    @cached_property
    def absolute_target(self) -> str:
        return resolve_name(self.name, self.package)

    def with_vendor_prefix(self, vendor_prefix: str, *, is_relative_import: bool) -> "ImportTarget":
        if is_relative_import:
            # Keep the relative name and let Python resolve it against the new anchor.
            return ImportTarget(name=self.name, package=f"{vendor_prefix}.{self.package}")

        return ImportTarget(name=f"{vendor_prefix}.{self.name}", package=self.package)


@dataclass
class ImportCandidate:
    target: ImportTarget
    vendor_package: Optional[VendorPackage]
    modules_context: Callable[[Optional[str]], AbstractContextManager[None]]
    error_policy: ErrorPolicy = ErrorPolicy.RAISE_ERROR
    rewritten: bool = False

    @contextmanager
    def context(self) -> Iterator[ImportTarget]:
        package_name = None if self.vendor_package is None else self.vendor_package.package_name
        try:
            with self.modules_context(package_name):
                yield self.target
        except ModuleNotFoundError as error:
            # Only a missing target or ancestor permits fallback. A dependency missing
            # inside an existing target must propagate to the caller.
            if (
                self.error_policy is ErrorPolicy.RAISE_ERROR
                or error.name is None
                or not is_module_from_package(self.target.absolute_target, error.name)
            ):
                raise
            LOGGER.debug(f"Failed to import vendored: {self.target.absolute_target}: {error!s}")


def generate_import_candidates(
    *,
    name: str,
    package_store: VendorPackagesStore,
    modules_context: Callable[[Optional[str]], AbstractContextManager[None]],
    relative_package: Optional[RelativePackage] = None,
) -> Iterator[ImportCandidate]:
    """Yield candidates in order, with a final candidate that propagates import errors."""
    is_relative_import = relative_package is not None
    package = relative_package.package if isinstance(relative_package, PackageFromArgument) else None
    original_target = ImportTarget(name=name, package=package)
    # Builtins resolves relative names from globals. Other targets can be checked
    # against stdlib using their resolved absolute names.
    if not isinstance(relative_package, PackageFromGlobals) and is_part_of_stdlib(original_target.absolute_target):
        yield ImportCandidate(target=original_target, vendor_package=None, modules_context=modules_context)
        return

    matching_package = get_caller_matching_package_from_store(package_store)
    vendor_package = None if matching_package is None else matching_package.vendor_package
    if vendor_package is None or isinstance(relative_package, PackageFromGlobals):
        # Builtins resolves relative imports using globals and level, without a package argument.
        yield ImportCandidate(target=original_target, vendor_package=vendor_package, modules_context=modules_context)
        return

    absolute_target = original_target.absolute_target
    if is_module_from_package(absolute_target, vendor_package.vendor_prefix) or package_store.is_package_in_store(
        absolute_target
    ):
        yield ImportCandidate(target=original_target, vendor_package=vendor_package, modules_context=modules_context)
        return

    vendored_target = original_target.with_vendor_prefix(
        vendor_package.vendor_prefix, is_relative_import=is_relative_import
    )

    yield ImportCandidate(
        target=vendored_target,
        vendor_package=vendor_package,
        modules_context=modules_context,
        error_policy=ErrorPolicy.IGNORE_IF_ANCESTOR,
        rewritten=True,
    )
    yield ImportCandidate(target=original_target, vendor_package=None, modules_context=modules_context)
