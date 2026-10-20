from dataclasses import dataclass
from types import ModuleType
from collections.abc import Iterable, Sequence
from reyk.isolator_definition import VendorPackage
from reyk.module_name_utils import calculate_package_tree


class PackageEntryAlreadyExistsError(Exception): ...


@dataclass
class VendorPackageModules:
    vendor_package: VendorPackage
    modules: dict[str, ModuleType]


class VendorPackagesStore:
    """Stores vendor modules mappings by packages and facilitates utilities for changing and accessing the mapping."""

    def __init__(self) -> None:
        self._package_to_vendor_modules: dict[str, VendorPackageModules] = {}
        self._cached_package_trees: set[str] = set()

    def add_package(self, package_modules: VendorPackageModules) -> None:
        package_name = package_modules.vendor_package.package_name
        if package_name in self._package_to_vendor_modules:
            raise PackageEntryAlreadyExistsError(f"{package_name} is already registered")
        self._package_to_vendor_modules[package_modules.vendor_package.package_name] = package_modules
        self._cached_package_trees = self._calculate_package_trees()

    def add_module_to_all_packages(self, module_name: str, module: ModuleType) -> None:
        for modules in self.get_all_packages_modules():
            modules[module_name] = module

    def get_package_by_name(self, package_name: str) -> VendorPackageModules:
        return self._package_to_vendor_modules[package_name]

    def is_package_in_store(self, package_name: str) -> bool:
        return package_name in self._package_to_vendor_modules

    def get_package_names(self) -> Iterable[str]:
        return self._package_to_vendor_modules.keys()

    def get_vendor_packages(self) -> Sequence[VendorPackage]:
        return [
            package_vendor_modules.vendor_package for package_vendor_modules in self._package_to_vendor_modules.values()
        ]

    def get_all_packages_modules(self) -> Iterable[dict[str, ModuleType]]:
        return (vendor_modules.modules for vendor_modules in self._package_to_vendor_modules.values())

    def get_package_name_trees(self) -> set[str]:
        return self._cached_package_trees

    def _calculate_package_trees(self) -> set[str]:
        """
        Calculates the package tree for mapped packages.
        See `_calculate_package_tree` for more info.
        """
        return set.union(*(calculate_package_tree(package) for package in self.get_package_names()))
