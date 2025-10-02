import builtins
import sys
import types
from typing import NamedTuple, Protocol
from collections.abc import Sequence, Iterable, Mapping
from pathlib import Path
import logging
from importlib.metadata import Distribution, DistributionFinder, MetadataPathFinder
from isolator.caller_finder import is_caller_part_of_library


LOGGER = logging.getLogger(__name__)


class ImportPath(NamedTuple):
    import_name: str
    fullback_import_name: str | None = None


class Importer(Protocol):
    def __call__(
        self,
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> types.ModuleType:
        ...


class VendorImporter(Importer, DistributionFinder):
    def __init__(
        self,
        package_name: str,
        vendorized_libs_dir_name: str,
        vendorized_libs_path: Path,
        original_import_method: Importer,
    ) -> None:
        self._library_name = package_name
        self._vendorized_libs_dir_name = vendorized_libs_dir_name
        self._vendorized_libs_path = vendorized_libs_path
        self._original_import_method = original_import_method

    def __call__(
        self,
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> types.ModuleType:
        LOGGER.debug(f"Importing in vendorized find_spec: {name}")
        import_path = self._get_import_path(name)

        # if "." in fullname:
        #     imported_name, package = fullname.rsplit(".", maxsplit=1)
        #     vendored_import_path += f".{package}"
        # else:
        #     imported_name = fullname
        #     vendored_import_path += f".{imported_name}"

        try:
            LOGGER.debug(f"Importing: {import_path}")
            module = self._original_import_method(import_path.import_name, globals, locals, fromlist, level)
            if len(fromlist) == 0:
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
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import: {name}: {exc!s}")
            if import_path.fullback_import_name is None:
                raise

            module = self._original_import_method(import_path.fullback_import_name, globals, locals, fromlist, level)

        LOGGER.debug(f"Imported: {module} ({[x for x in dir(module) if "__" not in x]})")
        return module
    
    def _get_import_path(
        self,
        name: str,
    ) -> ImportPath:
        if name.startswith(self.vendor_prefix):
            # Cannot import actual path - another metapath finder should do that
            LOGGER.debug("Cannot import because it starts with vendor prefix (full import)")
            return ImportPath(name)
        
        if name == self._library_name:
            LOGGER.debug(f"Cannot re-import the library: {self._library_name}")
            return ImportPath(name)

        if not is_caller_part_of_library(self._library_name):
            LOGGER.debug("Cannot import because it's not part of library")
            return ImportPath(name)

        return ImportPath(
            f"{self.vendor_prefix}.{name}",
            name,
        )
    
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
        
        builtins.__import__ = self.__call__


def invalidate_all_finder_caches() -> None:
    for finder in sys.meta_path:
        invalidate_caches = getattr(finder, "invalidate_caches", None)
        if invalidate_caches is not None:
            invalidate_caches()
