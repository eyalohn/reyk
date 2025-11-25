import builtins
import importlib
import sys
import types
from typing import Protocol
from collections.abc import Sequence, Iterable, Mapping
from pathlib import Path
import logging
from importlib.metadata import Distribution, DistributionFinder, MetadataPathFinder
from isolator.caller_finder import is_caller_part_of_library


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
    ) -> types.ModuleType:
        ...


class ImportLibImporter(Protocol):
    def __call__(
        self,
        name: str,
        package: str | None = None,
    ) -> types.ModuleType:
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

    def builtins_import_override(
        self,
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] | None = (),
        level: int = 0,
    ) -> types.ModuleType:
        # Note: ALL import calls should be in this function as to not increase the call stack significantly
        LOGGER.debug(f"Importing in vendorized find_spec: {name}")
        if not self._should_import_vendorized(name):
            return self._original_builtins_import_method(name, globals, locals, fromlist, level)

        vendorized_import_path = f"{self.vendor_prefix}.{name}"
        imported_vendorized: bool
        try:
            LOGGER.debug(f"Importing: {vendorized_import_path}")
            module = self._original_builtins_import_method(vendorized_import_path, globals, locals, fromlist, level)
            imported_vendorized = True
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import vendorized: {name}: {exc!s}")
            module = self._original_builtins_import_method(name, globals, locals, fromlist, level)
            imported_vendorized = False
            
        if imported_vendorized and (fromlist is None or len(fromlist) == 0):
            # module = self._get_actual_imported_module(vendorized_module=module, originally_imported_name=name)
            packages = self.vendor_prefix.split(".")[1:]
            returned_module_attribute, _, _ = name.partition(".")
            packages.append(returned_module_attribute)

            actual_imported_module = module
            for index, package in enumerate(packages):
                actual_imported_module = getattr(actual_imported_module, package, None)
                if actual_imported_module is None:
                    actual_imported_module = self._original_builtins_import_method(
                        f"{self.vendor_prefix}.{returned_module_attribute}",
                        globals,
                        locals,
                        [""],
                        level,
                    )
                    break
                    # raise ModuleNotFoundError(f"No module named: '{'.'.join(packages[:index + 1])}'")
            
            module = actual_imported_module
        
        LOGGER.debug(f"Imported: {module}")
        sys.modules[name] = module
        return module
    
    def importlib_import_override(
        self,
        name: str,
        package: str | None = None,
    ) -> types.ModuleType:
        # If package is not None it's a relative import
        if not self._should_import_vendorized(name) or package is not None:
            return self._original_importlib_import_method(name, package)

        vendorized_import_path = f"{self.vendor_prefix}.{name}"
        try:
            return self._original_importlib_import_method(vendorized_import_path, None)
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import vendorized: {name}: {exc!s}")
            return self._original_importlib_import_method(name, None)
    
    def _get_actual_imported_module(
        self,
        vendorized_module: types.ModuleType,
        originally_imported_name: str,
    ) -> types.ModuleType:
        """
        If we perform the following from example_project:
        `import example_library.library_module`
        This will re route us to:
        `import example_project.libs.example_library.library_module`
        therefore instead of accessing the variable by using `example_library.library_module.MY_STRING`
        we have to use `example_project.libs.example_library.library_module`.
        To avoid this we have to return the `example_library` module instead of the `example_project` module.
        """
        packages = self.vendor_prefix.split(".")[1:]
        returned_module_attribute, _, _ = originally_imported_name.partition(".")
        packages.append(returned_module_attribute)

        actual_imported_module = vendorized_module
        for index, package in enumerate(packages):
            actual_imported_module = getattr(actual_imported_module, package, None)
            if actual_imported_module is None:
                raise ModuleNotFoundError(f"No module named: '{'.'.join(packages[:index + 1])}'")
        
        return actual_imported_module
    
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
        if self not in sys.meta_path:
            sys.meta_path.insert(0, self)
        
        builtins.__import__ = self.builtins_import_override
        importlib.import_module = self.importlib_import_override


def invalidate_all_finder_caches() -> None:
    for finder in sys.meta_path:
        invalidate_caches = getattr(finder, "invalidate_caches", None)
        if invalidate_caches is not None:
            invalidate_caches()
