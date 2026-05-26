import builtins
import functools
import importlib
import logging
import sys
from collections.abc import Iterable, Mapping, Sequence
from importlib.metadata import Distribution, DistributionFinder, MetadataPathFinder
from pathlib import Path
from types import ModuleType
from typing import Optional, Protocol

from reyk.caller_finder import is_caller_part_of_library
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


class VendorImporter(DistributionFinder):
    def __init__(
        self,
        package_name: str,
        vendorized_libs_relative_import_path: str,
        vendorized_libs_path: Path,
        original_builtins_import_method: BuiltinsImporter,
        original_importlib_import_method: ImportLibImporter,
    ) -> None:
        self.package_name = package_name
        self.vendorized_libs_relative_import_path = vendorized_libs_relative_import_path
        self.vendorized_libs_path = vendorized_libs_path
        self._original_builtins_import_method = original_builtins_import_method
        self._original_importlib_import_method = original_importlib_import_method
        self._sys_modules_wrapper = VendoredSysModules(sys.modules, self.package_name, self.vendor_prefix)

    def builtins_import_override(
        self,
        name: str,
        globals: Optional[Mapping[str, object]] = None,
        locals: Optional[Mapping[str, object]] = None,
        fromlist: Optional[Sequence[str]] = (),
        level: int = 0,
    ) -> ModuleType:
        # Note: ALL import calls should be in this function as to not increase the call stack significantly
        if not self._should_import_vendorized(name):
            # If importing a module which shouldn't be vendorized
            # we need to exit the context to ensure we don't retrieve
            # a vendorized module
            self._sys_modules_wrapper.remove_vendored_sys_modules()
            return self._original_builtins_import_method(name, globals, locals, fromlist, level)

        vendorized_import_path = self._vendor_import(name)
        self._sys_modules_wrapper.install_vendored_sys_modules()
        imported_vendorized: bool
        try:
            LOGGER.debug(f"Importing: {vendorized_import_path}")
            # Install vendorized modules to save us from importing the same module twice
            # if it already exists in the sys.modules
            module = self._original_builtins_import_method(vendorized_import_path, globals, locals, fromlist, level)
            imported_vendorized = True
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import vendorized: {name}: {exc!s}")
            self._sys_modules_wrapper.remove_vendored_sys_modules()
            module = self._original_builtins_import_method(name, globals, locals, fromlist, level)
            imported_vendorized = False

        if imported_vendorized:
            is_absolute_import = fromlist is None or len(fromlist) == 0
            if is_absolute_import:
                module = self._retrieve_absolute_import_module(name, module)
                self._add_imported_sub_modules_to_vendorized(name, module)
            else:
                # Add the non-vendored name to sys modules as well (its in the vendored
                # sys modules so this should go to `package_modules` only)
                sys.modules[name] = module

            # It's important at the end to return to vendorized sys module if we imported
            # a vendorized package in case an import was made inside this import which changed the state
            self._sys_modules_wrapper.install_vendored_sys_modules()

        LOGGER.debug(f"Imported: {module}")
        return module

    def importlib_import_override(
        self,
        name: str,
        package: Optional[str] = None,
    ) -> ModuleType:
        # If package is not None it's a relative import
        if not self._should_import_vendorized(name) or package is not None:
            self._sys_modules_wrapper.remove_vendored_sys_modules()
            return self._original_importlib_import_method(name, package)

        vendorized_import_path = self._vendor_import(name)
        try:
            self._sys_modules_wrapper.install_vendored_sys_modules()
            return self._original_importlib_import_method(vendorized_import_path, None)
        except ModuleNotFoundError as exc:
            self._sys_modules_wrapper.remove_vendored_sys_modules()
            LOGGER.debug(f"Failed to import vendorized: {name}: {exc!s}")
            return self._original_importlib_import_method(name, None)

    def _retrieve_absolute_import_module(
        self,
        module_name: str,
        module_with_vendor_prefix: ModuleType,
    ) -> ModuleType:
        module_without_vendor_prefix = self._try_retrieving_imported_module_by_getattr(
            module_name=module_name,
            returned_module=module_with_vendor_prefix,
        )
        if module_without_vendor_prefix is None:
            self._sys_modules_wrapper.install_vendored_sys_modules()
            module_without_vendor_prefix = self._retrieve_imported_module_from_sys_modules(
                self._vendor_import(self._extract_returned_module_name(module_name))
            )

        return module_without_vendor_prefix

    def _add_imported_sub_modules_to_vendorized(
        self,
        module_name: str,
        returned_module: ModuleType,
    ) -> None:
        """
        Adds the imported sub-packages of the returned module to the vendorized modules state.
        For example if we perform a vendorized: `import example_library.module` then we
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
                        self._vendor_import(".".join(packages[: index + 1]))
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
        packages = self.vendor_prefix.split(".")[1:]
        returned_module_name = self._extract_returned_module_name(module_name)
        packages.append(returned_module_name)

        return functools.reduce(
            lambda module, package: getattr(module, package, None),
            packages,
            returned_module,
        )

    def _vendor_import(self, import_path: str) -> str:
        return f"{self.vendor_prefix}.{import_path}"

    def _extract_returned_module_name(self, module_name: str) -> str:
        returned_module_attribute, _, _ = module_name.partition(".")
        return returned_module_attribute

    def _should_import_vendorized(
        self,
        name: str,
    ) -> bool:
        if name.startswith(RELATIVE_IMPORT_PREFIX):
            LOGGER.debug("Relative imports don't require changing the import path for vendorized packages")
            return False

        if name.startswith(self.vendor_prefix):
            LOGGER.debug(
                "The attempted import is already for a vendorized package therefore there's "
                "no need to change the import path"
            )
            return False

        if name == self.package_name:
            LOGGER.debug(f"Cannot re-import the library: {self.package_name}")
            return False

        if not is_caller_part_of_library(self.package_name):
            LOGGER.debug("Cannot import because it's not part of library")
            return False

        if is_part_of_stdlib(name):
            LOGGER.debug(f"Skipping vendor import attempt for {name} because the same name exists in stdlib")
            return False

        return True

    def find_distributions(
        self,
        context: Optional[DistributionFinder.Context] = None,
    ) -> Iterable[Distribution]:
        if context is None:
            context = DistributionFinder.Context()

        LOGGER.debug(f"Finding distributions in VendorImporter for context: {context}")
        if not is_caller_part_of_library(self.package_name):
            LOGGER.debug("Returning empty list in find_distributions because not part of library")
            return []

        LOGGER.debug(f"Returning all distributions in vendorized path: {self.vendorized_libs_path}")
        vars(context).update({"path": [str(self.vendorized_libs_path)]})
        return MetadataPathFinder.find_distributions(context)

    @property
    def vendor_prefix(self) -> str:
        return f"{self.package_name}.{self.vendorized_libs_relative_import_path}"

    def install(self) -> None:
        builtins.__import__ = self.builtins_import_override
        importlib.import_module = self.importlib_import_override
        if self not in sys.meta_path:
            # For distribution finder
            sys.meta_path.append(self)

        sys.modules = self._sys_modules_wrapper

    def uninstall(self) -> None:
        builtins.__import__ = self._original_builtins_import_method
        importlib.import_module = self._original_importlib_import_method
        if self in sys.meta_path:
            sys.meta_path.remove(self)

        sys.modules = self._sys_modules_wrapper.original_sys_modules


def get_installed_vendor_importer() -> Optional[VendorImporter]:
    import_owner = getattr(builtins.__import__, "__self__", None)
    if (import_owner is None) or (not isinstance(import_owner, VendorImporter)):
        return None

    return import_owner
