from collections import UserDict
from collections.abc import MutableMapping
from dataclasses import dataclass
import itertools
from types import ModuleType
from collections.abc import Iterable
from typing import Optional
from reyk.caller_finder import get_caller_matching_package
from reyk.isolator_definition import VendorPackage
from reyk.stdlib_finder import is_part_of_stdlib


@dataclass(kw_only=True)
class VendorPackageModules:
    vendor_package: VendorPackage
    modules: dict[str, ModuleType]


class VendorPackages:
    def __init__(self) -> None:
        self._package_to_vendor_modules: dict[str, VendorPackageModules] = {}
        self._cached_package_trees: set[str] = set()

    def add_package(self, package_modules: VendorPackageModules) -> None:
        self._package_to_vendor_modules[package_modules.vendor_package.package_name] = package_modules
        self._cached_package_trees = self.calculate_package_trees()

    def add_module_to_all_packages(self, module_name: str, module: ModuleType) -> None:
        for modules in self.get_all_packages_modules():
            modules[module_name] = module

    def get_package_by_name(self, package_name: str) -> VendorPackageModules:
        return self._package_to_vendor_modules[package_name]

    def get_package_names(self) -> Iterable[str]:
        return self._package_to_vendor_modules.keys()

    def get_all_packages_modules(self) -> Iterable[dict[str, ModuleType]]:
        return (vendor_modules.modules for vendor_modules in self._package_to_vendor_modules.values())

    def get_package_name_trees(self) -> set[str]:
        return self._cached_package_trees

    def calculate_package_trees(self) -> set[str]:
        return set.union(*(_calculate_package_tree(package) for package in self.get_package_names()))


class PackagesVendorContext:
    def __init__(self) -> None:
        self._current_packages_context: list[str] = []

    def enter_context(self, package_name: str) -> None:
        if package_name in self._current_packages_context:
            self._current_packages_context.remove(package_name)  # Make sure its the top-most package in the list
        self._current_packages_context.append(package_name)

    def exit_context(self) -> str:
        """Exits the current package context and returns the removed package name"""
        return self._current_packages_context.pop()

    def is_empty(self) -> bool:
        return len(self._current_packages_context) == 0

    @property
    def package_name_in_context(self) -> str | None:
        return None if len(self._current_packages_context) == 0 else self._current_packages_context[-1]


class VendoredSysModules(UserDict[str, ModuleType]):
    """
    Wrapper for overriding python-direct access to return vendored modules based on
    stack trace context. This will usually not effect the actual import mechanism as it access
    the original `sys.modules`.

    Therefore we are doing best-effort here:
    1. If there's access from C/the original sys modules then we ensure to take the vendored module only if we're in
       in a vendored context (in the middle of a vendored import), otherwise we'll use the
       original user imported module/no module with the same name
    2. If we access from Python to the sys modules wrapper then we'll never access the original
       sys modules and therefore use the appropriate modules based on the vendor context (user module if outside vendor
       and vendor module if inside vendor)
    """

    DICT_INTERNAL_DATA_FIELD_NAME = "data"

    def __init__(self, original_sys_modules: dict[str, ModuleType]) -> None:
        self.original_sys_modules = original_sys_modules
        self._user_modules: dict[str, ModuleType] = original_sys_modules.copy()
        self._vendor_packages = VendorPackages()
        self._vendor_context = PackagesVendorContext()

    def add_package(self, package: VendorPackage) -> None:
        self._vendor_packages.add_package(
            VendorPackageModules(
                vendor_package=package,
                modules=self._user_modules.copy(),
            ),
        )
        self._update_modules_with_package_tree(package)

    def install_vendored_sys_modules(self, package_name: str) -> None:
        if self._vendor_context.package_name_in_context == package_name:
            return

        vendor_modules = self._vendor_packages.get_package_by_name(package_name)
        if self._vendor_context.package_name_in_context is not None:
            self._switch_original_sys_modules_state(
                vendor_modules.modules,
                self._vendor_packages.get_package_by_name(self._vendor_context.package_name_in_context).modules,
            )

        self._switch_original_sys_modules_state(vendor_modules.modules, self._user_modules)
        self._vendor_context.enter_context(package_name)

    def remove_vendored_sys_modules(self) -> None:
        if self._vendor_context.is_empty():
            return

        removed_context = self._vendor_context.exit_context()
        modules_to_remove = self._vendor_packages.get_package_by_name(removed_context)
        new_modules_after_removal = (
            self._user_modules
            if self._vendor_context.package_name_in_context is None
            else self._vendor_packages.get_package_by_name(self._vendor_context.package_name_in_context).modules
        )
        self._switch_original_sys_modules_state(new_modules_after_removal, modules_to_remove.modules)

    def _switch_original_sys_modules_state(
        self,
        new_sys_modules: dict[str, ModuleType],
        previous_sys_modules: dict[str, ModuleType],
    ) -> None:
        for module_name in previous_sys_modules.keys():
            self.original_sys_modules.pop(module_name, None)

        self.original_sys_modules.update(new_sys_modules)

    def __setitem__(self, key: str, value: ModuleType) -> None:
        module_name = value.__name__
        if is_part_of_stdlib(module_name) or module_name in self._vendor_packages.get_package_name_trees():
            # Standard libraries should be registered as both package & user modules
            self.original_sys_modules[key] = value
            self._user_modules[key] = value
            self._vendor_packages.add_module_to_all_packages(key, value)
            return

        dicts_to_update: list[MutableMapping[str, ModuleType]] = [super()]
        matching_package = get_caller_matching_package(self._vendor_packages.get_package_names())
        if matching_package == self._vendor_context.package_name_in_context:
            dicts_to_update.append(self.original_sys_modules)

        vendor_prefix = (
            None
            if matching_package is None
            else self._vendor_packages.get_package_by_name(matching_package).vendor_package.vendor_prefix
        )
        # The setitem will be directed to package modules/user modules
        for dict_to_update in dicts_to_update:
            if vendor_prefix is not None and key.startswith(vendor_prefix) and key != vendor_prefix:
                dict_to_update.__setitem__(key.removeprefix(vendor_prefix).removeprefix("."), value)

            dict_to_update.__setitem__(key, value)

    def __getattribute__(self, name: str) -> object:
        if name == VendoredSysModules.DICT_INTERNAL_DATA_FIELD_NAME:
            matching_package = get_caller_matching_package(self._vendor_packages.get_package_names())
            if matching_package is None:
                return self._user_modules

            # The package may not necessarily correspond to the currently
            # installed package (_current_installed_package_name) if the import arrived from
            # a function which occurred unrelated to the module vendored module initial loading.
            # (ie an import from within a function which occurs outside of the initial startup imports)
            return self._vendor_packages.get_package_by_name(matching_package).modules

        return super().__getattribute__(name)

    def _update_modules_with_package_tree(self, package: VendorPackage) -> None:
        """
        When installing a new package we need to ensure all other vendored packages should be able to access
        its basic tree.
        Ie if the package is 'example_project' and we have another package named 'another_project' inside
        the 'libs' of 'example_project' ('example_project.libs.another_project') then 'another_project' needs to
        be able to access 'example_project' in its vendored context.
        """
        for vendored_package_node_name in _calculate_package_tree(package.package_name):
            package_mod = self._find_module_from_all_module_dicts(vendored_package_node_name)
            if package_mod is None:
                continue

            for modules in self._all_module_dicts:
                if vendored_package_node_name not in modules:
                    modules[vendored_package_node_name] = package_mod

    def _find_module_from_all_module_dicts(self, module_name: str) -> Optional[ModuleType]:
        for module_dict in self._all_module_dicts:
            mod = module_dict.get(module_name)
            if mod is not None:
                return module_dict[module_name]

        return None

    @property
    def _all_module_dicts(self) -> Iterable[dict[str, ModuleType]]:
        return (
            self._user_modules,
            *self._vendor_packages.get_all_packages_modules(),
        )


def _calculate_package_tree(module_name: str) -> set[str]:
    """
    Returns all parents and module itself.

    Example:
        parent_package.child_package.module -> {
            'parent_package',
            'parent_package.child_package',
            'parent_package.child_package.module',
        }

    """
    return set(itertools.accumulate(module_name.split("."), lambda part1, part2: f"{part1}.{part2}"))
