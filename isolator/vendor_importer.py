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
        self._library_name = package_name
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
        LOGGER.debug(f"Importing in vendorized find_spec: {name}")
        if not self._should_import_vendorized(name) or name.startswith("."):
            return self._original_builtins_import_method(name, globals, locals, fromlist, level)

        # if "." in fullname:
        #     imported_name, package = fullname.rsplit(".", maxsplit=1)
        #     vendored_import_path += f".{package}"
        # else:
        #     imported_name = fullname
        #     vendored_import_path += f".{imported_name}"

        vendorized_import_path = f"{self.vendor_prefix}.{name}"
        try:
            LOGGER.debug(f"Importing: {vendorized_import_path}")
            module = self._original_builtins_import_method(vendorized_import_path, globals, locals, fromlist, level)
            
            if fromlist is None or len(fromlist) == 0:
               """
               TODO:
               If we perform the following from example_project:
               `import example_library.library_module`
               This will re route us to:
               `import example_project.libs.example_library.library_module`
               therefore instead of accessing the variable by using `example_library.library_module.MY_STRING`
               we have to use `example_project.libs.example_library.library_module`.
               To avoid this we have to return the `example_library` module instead of the `example_project` module.
               """
               packages = self.vendor_prefix.split(".")[1:]
               returned_module_attribute, _, _ = name.partition(".")
               packages.append(returned_module_attribute)

               for package in packages:
                   module = getattr(module, package, None)
                   if module is None:
                       # TODO: Raise custom error if module is None
                       raise ValueError(f"Missing {package} in {self.vendor_prefix}")
            
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import vendorized: {name}: {exc!s}")
            module = self._original_builtins_import_method(name, globals, locals, fromlist, level)

        LOGGER.debug(f"Imported: {module} ({[x for x in dir(module) if "__" not in x]})")
        return module
    
    def importlib_import_override(
        self,
        name: str,
        package: str | None = None,
    ) -> types.ModuleType:
        if not self._should_import_vendorized(name) or package is not None:
            return self._original_importlib_import_method(name, package)

        vendorized_import_path = f"{self.vendor_prefix}.{name}"
        try:
            return self._original_importlib_import_method(vendorized_import_path, None)
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import vendorized: {name}: {exc!s}")
            return self._original_importlib_import_method(name, None)
    
    def _import_if_vendorized(self, name: str, is_relative_import: bool) -> types.ModuleType:
        # if 
        pass
    
    def _should_import_vendorized(
        self,
        name: str,
    ) -> bool:
        if name.startswith(self.vendor_prefix):
            # Cannot import actual path - another metapath finder should do that
            LOGGER.debug("Cannot import because it starts with vendor prefix (full import)")
            return False
        
        if name == self._library_name:
            LOGGER.debug(f"Cannot re-import the library: {self._library_name}")
            return False

        if not is_caller_part_of_library(self._library_name):
            LOGGER.debug("Cannot import because it's not part of library")
            return False

        return True
    
    def find_distributions(
        self,
        context: DistributionFinder.Context = DistributionFinder.Context()
    ) -> Iterable[Distribution]:
        LOGGER.debug(f"Finding distributions in VendorImporter for context: {context}")
        if not is_caller_part_of_library(self._library_name):
            LOGGER.debug("Returning empty list in find_distributions because not part of library")
            return []

        LOGGER.debug(f"Returning all distributions in vendorized path: {self._vendorized_libs_path}")
        vars(context).update({"path": [str(self._vendorized_libs_path)]})
        return MetadataPathFinder.find_distributions(context)

    @property
    def vendor_prefix(self) -> str:
        return f"{self._library_name}.{self._vendorized_libs_dir_name}"
    
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
