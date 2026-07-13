import builtins
import functools
import importlib
import importlib.metadata
import logging
import sys
from collections.abc import Iterable, Mapping, Sequence
from importlib.metadata import Distribution, DistributionFinder, MetadataPathFinder
from types import ModuleType
from typing import Optional, Protocol

from reyk.caller_finder import get_caller_matching_package
from reyk.reyk_isolator import ReykIsolator, VendorPackage, Version
from reyk.stdlib_finder import is_part_of_stdlib
from reyk.vendored_sys_modules import VendoredSysModules

LOGGER = logging.getLogger(__name__)

RELATIVE_IMPORT_PREFIX = "."


class BuiltinsImporter(Protocol):
    def __call__(
        self,
        name: str,
        globals: Optional[Mapping[str, object]] = None,
        locals: Optional[Mapping[str, object]] = None,
        fromlist: Optional[Sequence[str]] = (),
        level: int = 0,
    ) -> ModuleType: ...


class ImportLibImporter(Protocol):
    def __call__(
        self,
        name: str,
        package: Optional[str] = None,
    ) -> ModuleType: ...


class VendorImporter(ReykIsolator, DistributionFinder):
    VENDOR_IMPORTER_VERSION = Version(major=1, minor=0, patch=0)

    def __init__(
        self,
        original_builtins_import_method: BuiltinsImporter,
        original_importlib_import_method: ImportLibImporter,
    ) -> None:
        self._is_installed = False
        self._original_builtins_import_method = original_builtins_import_method
        self._original_importlib_import_method = original_importlib_import_method
        self._package_name_to_vendor_package: dict[str, VendorPackage] = {}
        self._sys_modules_wrapper = VendoredSysModules(sys.modules)

    def add_package(self, *, vendor_package: VendorPackage) -> None:
        if vendor_package.package_name in self._package_name_to_vendor_package:
            raise ValueError(f"{vendor_package.package_name} is already vendored")
        self._package_name_to_vendor_package[vendor_package.package_name] = vendor_package
        self._sys_modules_wrapper.add_package(vendor_package)

    def builtins_import_override(
        self,
        name: str,
        globals: Optional[Mapping[str, object]] = None,
        locals: Optional[Mapping[str, object]] = None,
        fromlist: Optional[Sequence[str]] = (),
        level: int = 0,
    ) -> ModuleType:
        # Note: ALL import calls should be in this function as to not increase the call stack significantly
        vendor_package = self._get_package_to_vendor(name)
        if vendor_package is None:
            # If importing a module which shouldn't be vendored
            # we need to exit the context to ensure we don't retrieve
            # a vendored module
            self._sys_modules_wrapper.remove_vendored_sys_modules()
            return self._original_builtins_import_method(name, globals, locals, fromlist, level)

        vendored_import_path = self._vendor_import(vendor_package, name)
        self._sys_modules_wrapper.install_vendored_sys_modules(vendor_package.package_name)
        imported_vendored: bool
        try:
            LOGGER.debug(f"Importing: {vendored_import_path}")
            # Install vendored modules to save us from importing the same module twice
            # if it already exists in the sys.modules
            module = self._original_builtins_import_method(vendored_import_path, globals, locals, fromlist, level)
            imported_vendored = True
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import vendored: {name}: {exc!s}")
            self._sys_modules_wrapper.remove_vendored_sys_modules()
            module = self._original_builtins_import_method(name, globals, locals, fromlist, level)
            imported_vendored = False

        if imported_vendored:
            is_absolute_import = fromlist is None or len(fromlist) == 0
            if is_absolute_import:
                module = self._retrieve_absolute_import_module(vendor_package, name, module)
                self._add_imported_sub_modules_to_vendored(vendor_package, name, module)
            else:
                # Add the non-vendored name to sys modules as well (its in the vendored
                # sys modules so this should go to `package_modules` only)
                sys.modules[name] = module

            # It's important at the end to return to vendored sys module if we imported
            # a vendored package in case an import was made inside this import which changed the state
            self._sys_modules_wrapper.install_vendored_sys_modules(vendor_package.package_name)

        LOGGER.debug(f"Imported: {module}")
        return module

    def importlib_import_override(
        self,
        name: str,
        package: Optional[str] = None,
    ) -> ModuleType:
        # If package is not None it's a relative import
        vendor_package = self._get_package_to_vendor(name)
        if vendor_package is None or package is not None:
            self._sys_modules_wrapper.remove_vendored_sys_modules()
            return self._original_importlib_import_method(name, package)

        vendored_import_path = self._vendor_import(vendor_package, name)
        try:
            self._sys_modules_wrapper.install_vendored_sys_modules(vendor_package.package_name)
            return self._original_importlib_import_method(vendored_import_path, None)
        except ModuleNotFoundError as exc:
            self._sys_modules_wrapper.remove_vendored_sys_modules()
            LOGGER.debug(f"Failed to import vendored: {name}: {exc!s}")
            return self._original_importlib_import_method(name, None)

    def _retrieve_absolute_import_module(
        self,
        vendor_package: VendorPackage,
        module_name: str,
        module_with_vendor_prefix: ModuleType,
    ) -> ModuleType:
        module_without_vendor_prefix = self._try_retrieving_imported_module_by_getattr(
            vendor_package=vendor_package,
            module_name=module_name,
            returned_module=module_with_vendor_prefix,
        )
        if module_without_vendor_prefix is None:
            self._sys_modules_wrapper.install_vendored_sys_modules(vendor_package.package_name)
            module_without_vendor_prefix = self._retrieve_imported_module_from_sys_modules(
                self._vendor_import(vendor_package, self._extract_returned_module_name(module_name))
            )

        return module_without_vendor_prefix

    def _add_imported_sub_modules_to_vendored(
        self,
        vendor_package: VendorPackage,
        module_name: str,
        returned_module: ModuleType,
    ) -> None:
        """
        Adds the imported sub-packages of the returned module to the vendored modules state.
        For example if we perform a vendored: `import example_library.module` then we
        return `example_library` but in the sys modules there will only be:
        1. `example_project.libs.example_library`
        2. `example_project.libs.example_library.module`
        Meanwhile this function will also add the following:
        1. `example_library`
        2. `example_library.module`
        """
        packages = module_name.split(".")
        current_module = returned_module
        for index, path_component in enumerate(packages):
            if index > 0:
                try:
                    current_module = getattr(current_module, path_component)
                except AttributeError:
                    current_module = self._retrieve_imported_module_from_sys_modules(
                        self._vendor_import(vendor_package, ".".join(packages[: index + 1]))
                    )
            current_module_name = ".".join(packages[: index + 1])
            sys.modules[current_module_name] = current_module

    def _retrieve_imported_module_from_sys_modules(
        self,
        module_name: str,
    ) -> ModuleType:
        module = sys.modules.get(module_name)
        if module is None:
            raise ModuleNotFoundError(f"No module named: '{module_name}'")

        return module

    def _try_retrieving_imported_module_by_getattr(
        self,
        vendor_package: VendorPackage,
        module_name: str,
        returned_module: ModuleType,
    ) -> Optional[ModuleType]:
        """
        If we perform the following from example_project:
        `import example_library.library_module`
        This will reroute us to:
        `import example_project.libs.example_library.library_module`
        therefore instead of accessing the variable by using `example_library.library_module.MY_STRING`
        we have to use `example_project.libs.example_library.library_module`.
        To avoid this we have to return the `example_library` module instead of the `example_project` module.

        This may fail sometimes due to circular imports not able to retrieve the object yet.
        Ie: If you are already inside `example_library.__init__` and importing `example_library.library_module`
        it might fail because this will try to access an attribute of a partially-initialized module.
        """
        packages = vendor_package.vendor_prefix.split(".")[1:]
        returned_module_name = self._extract_returned_module_name(module_name)
        packages.append(returned_module_name)

        return functools.reduce(
            lambda module, package: getattr(module, package, None),
            packages,
            returned_module,
        )

    def _vendor_import(self, vendor_package: VendorPackage, import_path: str) -> str:
        return f"{vendor_package.vendor_prefix}.{import_path}"

    def _extract_returned_module_name(self, module_name: str) -> str:
        returned_module_attribute, _, _ = module_name.partition(".")
        return returned_module_attribute

    def _get_package_to_vendor(
        self,
        name: str,
    ) -> Optional[VendorPackage]:
        if name.startswith(RELATIVE_IMPORT_PREFIX):
            LOGGER.debug("Relative imports don't require changing the import path for vendored packages")
            return None

        if is_part_of_stdlib(name):
            LOGGER.debug(f"Skipping vendor import attempt for {name} because the same name exists in stdlib")
            return None

        if name in self._package_name_to_vendor_package:
            LOGGER.debug(f"Cannot re-import the library: {self._package_name_to_vendor_package}")
            return None

        matching_vendor_package = self._get_caller_matching_vendor_package()
        if matching_vendor_package is None:
            LOGGER.debug("Cannot import because it's not part of library")
            return None

        if name.startswith(matching_vendor_package.vendor_prefix):
            LOGGER.debug(
                "The attempted import is already for a vendored package therefore there's "
                "no need to change the import path"
            )
            return None

        return matching_vendor_package

    def _get_caller_matching_vendor_package(self) -> Optional[VendorPackage]:
        matching_package_name = get_caller_matching_package(self._package_name_to_vendor_package.keys())
        if matching_package_name is None:
            return None

        return self._package_name_to_vendor_package[matching_package_name]

    def find_distributions(
        self,
        context: Optional[DistributionFinder.Context] = None,
    ) -> Iterable[Distribution]:
        if context is None:
            context = DistributionFinder.Context()

        LOGGER.debug(f"Finding distributions in VendorImporter for context: {context}")
        vendor_package_name = get_caller_matching_package(self._package_name_to_vendor_package.keys())
        if vendor_package_name is None:
            LOGGER.debug("Returning empty list in find_distributions because not part of library")
            return []

        vendor_package = self._package_name_to_vendor_package[vendor_package_name]
        LOGGER.debug(f"Returning all distributions in vendored path: {vendor_package.vendor_libs_path}")
        vars(context).update({"path": [str(vendor_package.vendor_libs_path)]})
        return MetadataPathFinder.find_distributions(context)

    def install(self) -> None:
        if self._is_installed:
            raise ValueError("Vendor importer is already installed")

        builtins.__import__ = self.builtins_import_override
        importlib.import_module = self.importlib_import_override
        # Distribution entrypoint loading uses the import_module in `importlib.metadata`
        # and therefore needs to be overridden as well
        importlib.metadata.import_module = self.importlib_import_override  # pyright: ignore[reportAttributeAccessIssue]

        if self not in sys.meta_path:
            # For distribution finder
            sys.meta_path.append(self)

        sys.modules = self._sys_modules_wrapper
        self._is_installed = True

    def uninstall(self) -> None:
        if not self._is_installed:
            raise ValueError("Vendor importer is not currently installed therefore cannot be uninstalled")
        builtins.__import__ = self._original_builtins_import_method
        importlib.import_module = self._original_importlib_import_method
        importlib.metadata.import_module = self._original_importlib_import_method  # pyright: ignore[reportAttributeAccessIssue]

        if self in sys.meta_path:
            sys.meta_path.remove(self)

        sys.modules = self._sys_modules_wrapper.original_sys_modules
        self._is_installed = False

    @property
    def version(self) -> Version:
        return VendorImporter.VENDOR_IMPORTER_VERSION

    @property
    def package_names(self) -> set[str]:
        return set(self._package_name_to_vendor_package.keys())
