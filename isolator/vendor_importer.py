import builtins
import importlib
import sys
from types import ModuleType
from typing import Protocol
from collections.abc import Sequence, Iterable, Mapping
from pathlib import Path
import functools
import logging
from importlib.metadata import Distribution, DistributionFinder, MetadataPathFinder
from isolator.caller_finder import is_caller_part_of_library
from isolator.sys_modules_state_handler import SysModulesStateHandler


LOGGER = logging.getLogger(__name__)

RELATIVE_IMPORT_PREFIX = "."


class BuiltinsImporter(Protocol):
    def __call__(
        self,
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> ModuleType:
        ...


class ImportLibImporter(Protocol):
    def __call__(
        self,
        name: str,
        package: str | None = None,
    ) -> ModuleType:
        ...


class VendorImporter(DistributionFinder):
    def __init__(
        self,
        package_name: str,
        vendorized_libs_dir_name: str,
        vendorized_libs_path: Path,
        original_builtins_import_method: BuiltinsImporter,
        original_importlib_import_method: ImportLibImporter,
    ) -> None:
        self._package_name = package_name
        self._vendorized_libs_dir_name = vendorized_libs_dir_name
        self._vendorized_libs_path = vendorized_libs_path
        self._original_builtins_import_method = original_builtins_import_method
        self._original_importlib_import_method = original_importlib_import_method
        self._sys_modules_state_handler = SysModulesStateHandler()

    def builtins_import_override(
        self,
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> ModuleType:
        # Note: ALL import calls should be in this function as to not increase the call stack significantly
        if not self._should_import_vendorized(name):
            # If importing a module which shouldn't be vendorized
            # we need to exit the context to ensure we don't retrieve
            # a vendorized module
            self._sys_modules_state_handler.remove_vendorized_sys_modules()
            return self._original_builtins_import_method(name, globals, locals, fromlist, level)

        vendorized_import_path = f"{self.vendor_prefix}.{name}"
        self._sys_modules_state_handler.install_vendorized_sys_modules()
        imported_vendorized: bool
        try:
            LOGGER.debug(f"Importing: {vendorized_import_path}")
            # Install vendorized modules to save us from importing the same module twice
            # if it already exists in the sys.modules
            module = self._original_builtins_import_method(vendorized_import_path, globals, locals, fromlist, level)
            imported_vendorized = True
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import vendorized: {name}: {exc!s}")
            self._sys_modules_state_handler.remove_vendorized_sys_modules()
            module = self._original_builtins_import_method(name, globals, locals, fromlist, level)
            imported_vendorized = False
        
        if imported_vendorized:
            is_absolute_import = fromlist is None or len(fromlist) == 0
            if is_absolute_import:
                module = self._retrieve_absolute_import_module(name, module)
                self._add_imported_sub_modules_to_vendorized(name, module)
            else:
                self._sys_modules_state_handler.add_only_vendorized_module(name, module)

            # It's important at the end to return to vendorized sys module if we imported
            # a vendorized package in case an import was made inside this import which changed the state
            self._sys_modules_state_handler.install_vendorized_sys_modules()

        LOGGER.debug(f"Imported: {module}")
        return module
    
    def importlib_import_override(
        self,
        name: str,
        package: str | None = None,
    ) -> ModuleType:
        # If package is not None it's a relative import
        if not self._should_import_vendorized(name) or package is not None:
            self._sys_modules_state_handler.remove_vendorized_sys_modules()
            return self._original_importlib_import_method(name, package)

        vendorized_import_path = f"{self.vendor_prefix}.{name}"
        try:
            self._sys_modules_state_handler.install_vendorized_sys_modules()
            return self._original_importlib_import_method(vendorized_import_path, None)
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import vendorized: {name}: {exc!s}")
            self._sys_modules_state_handler.remove_vendorized_sys_modules()
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
            self._sys_modules_state_handler.install_vendorized_sys_modules()
            returned_module_name_with_prefix = f"{self.vendor_prefix}.{self._extract_returned_module_name(module_name)}"
            module_without_vendor_prefix = sys.modules.get(returned_module_name_with_prefix)
            if module_without_vendor_prefix is None:
                raise ModuleNotFoundError(f"No module named: '{returned_module_name_with_prefix}'")
        
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
                current_module = getattr(current_module, path_component)
            current_module_name = ".".join(packages[:index + 1])
            self._sys_modules_state_handler.add_only_vendorized_module(current_module_name, current_module)

    def _try_retrieving_imported_module_by_getattr(
        self,
        module_name: str,
        returned_module: ModuleType,
    ) -> ModuleType | None:
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
            # Cannot import actual path - another metapath finder should do that
            LOGGER.debug(
                "The attempted import is already for a vendorized package therefore there's "
                "no need to change the import path"
            )
            return False
        
        if name == self._package_name:
            LOGGER.debug(f"Cannot re-import the library: {self._package_name}")
            return False

        if not is_caller_part_of_library(self._package_name):
            LOGGER.debug("Cannot import because it's not part of library")
            return False

        return True
    
    def find_distributions(
        self,
        context: DistributionFinder.Context | None = None,
    ) -> Iterable[Distribution]:
        if context is None:
            context = DistributionFinder.Context()

        LOGGER.debug(f"Finding distributions in VendorImporter for context: {context}")
        if not is_caller_part_of_library(self._package_name):
            LOGGER.debug("Returning empty list in find_distributions because not part of library")
            return []

        LOGGER.debug(f"Returning all distributions in vendorized path: {self._vendorized_libs_path}")
        vars(context).update({"path": [str(self._vendorized_libs_path)]})
        return MetadataPathFinder.find_distributions(context)

    @property
    def vendor_prefix(self) -> str:
        return f"{self._package_name}.{self._vendorized_libs_dir_name}"
    
    def install(self) -> None:
        builtins.__import__ = self.builtins_import_override
        importlib.import_module = self.importlib_import_override
        if self not in sys.meta_path:
            # For distribution finder
            sys.meta_path.append(self)
    
    def uninstall(self) -> None:
        builtins.__import__ = self._original_builtins_import_method
        importlib.import_module = self._original_importlib_import_method
        if self in sys.meta_path:
            sys.meta_path.remove(self)
    
    def clear_vendorized_cache(self) -> None:
        self._sys_modules_state_handler.clear_state()


def get_installed_vendor_importer() -> VendorImporter | None:
    import_owner = getattr(builtins.__import__, "__self__", None)
    if (import_owner is None) or (not isinstance(import_owner, VendorImporter)):
        return None
    
    return import_owner
