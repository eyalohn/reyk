from collections import UserDict
from collections.abc import MutableMapping
from dataclasses import dataclass
import itertools
from types import ModuleType
from collections.abc import Iterable
from typing import Optional
from reyk.caller_finder import get_caller_matching_package
from reyk.reyk_isolator import VendorPackage
from reyk.stdlib_finder import is_part_of_stdlib


@dataclass(kw_only=True)
class VendorPackageModules:
    vendor_package: VendorPackage
    modules: dict[str, ModuleType]


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
        self._package_to_vendor_modules: dict[str, VendorPackageModules] = {}
        self._current_installed_package_name: Optional[str] = None

    def add_package(self, package: VendorPackage) -> None:
        self._package_to_vendor_modules[package.package_name] = VendorPackageModules(
            vendor_package=package,
            modules=self._user_modules.copy(),
        )
        self._update_modules_with_package_tree(package)

    def install_vendored_sys_modules(self, package_name: str) -> None:
        if self._current_installed_package_name == package_name:
            return

        vendor_modules = self._package_to_vendor_modules[package_name]
        if self._current_installed_package_name is not None:
            self._switch_original_sys_modules_state(
                vendor_modules.modules,
                self._package_to_vendor_modules[package_name].modules,
            )

        self._switch_original_sys_modules_state(vendor_modules.modules, self._user_modules)
        self._current_installed_package_name = package_name

    def remove_vendored_sys_modules(self) -> None:
        if self._current_installed_package_name is None:
            return

        # TODO(Eyal): Add fallback to latest installed package name ie (if you're in reyk then entered reyk.cli and you exit reyk.cli you should return to reyk)  # noqa: E501, FIX002, TD003
        vendor_modules = self._package_to_vendor_modules[self._current_installed_package_name]
        self._switch_original_sys_modules_state(self._user_modules, vendor_modules.modules)
        self._current_installed_package_name = None

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
        if is_part_of_stdlib(module_name) or module_name in self._get_vendored_package_trees():
            # Standard libraries should be registered as both package & user modules
            self.original_sys_modules[key] = value
            self._user_modules[key] = value
            for vendor_modules in self._package_to_vendor_modules.values():
                vendor_modules.modules[key] = value
            return

        dicts_to_update: list[MutableMapping[str, ModuleType]] = [super()]
        matching_package = get_caller_matching_package(self._package_to_vendor_modules.keys())
        if matching_package == self._current_installed_package_name:
            dicts_to_update.append(self.original_sys_modules)

        vendor_prefix = (
            None
            if matching_package is None
            else self._package_to_vendor_modules[matching_package].vendor_package.vendor_prefix
        )
        # The setitem will be directed to package modules/user modules
        for dict_to_update in dicts_to_update:
            if vendor_prefix is not None and key.startswith(vendor_prefix) and key != vendor_prefix:
                dict_to_update.__setitem__(key.removeprefix(vendor_prefix).removeprefix("."), value)

            dict_to_update.__setitem__(key, value)

    def __getattribute__(self, name: str) -> object:
        if name == VendoredSysModules.DICT_INTERNAL_DATA_FIELD_NAME:
            matching_package = get_caller_matching_package(self._package_to_vendor_modules.keys())
            if matching_package is None:
                return self._user_modules

            # TODO(Eyal): Should we only return the modules if the current active package is the modules?  # noqa: E501, FIX002, TD003
            # If not - should we even track the current active package?
            return self._package_to_vendor_modules[matching_package].modules

        return super().__getattribute__(name)

    def _update_modules_with_package_tree(self, package: VendorPackage) -> None:
        """
        When installing a new package we need to ensure all other vendored packages should be able to access
        its basic tree.
        Ie if the package is 'example_project' and we have another package named 'another_project' inside
        the 'libs' of 'example_project' ('example_project.libs.another_project') then 'another_project' needs to
        be able to access 'example_project' in its vendored context.
        """
        for vendored_package_node_name in self._get_package_tree(package.package_name):
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
            *(vendor_modules.modules for vendor_modules in self._package_to_vendor_modules.values()),
        )

    def _get_vendored_package_trees(self) -> set[str]:
        # TODO(Eyal): Can this be faster/cached?  # noqa: FIX002, TD003
        return self._get_package_trees(set(self._package_to_vendor_modules.keys()))

    def _get_package_trees(self, packages: set[str]) -> set[str]:
        return set.union(*(self._get_package_tree(package) for package in packages))

    def _get_package_tree(self, module_name: str) -> set[str]:
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
