import sys
from collections.abc import Sequence, Iterable
from types import ModuleType
from pathlib import Path
import logging
from importlib.abc import MetaPathFinder, Loader
from importlib.metadata import Distribution, DistributionFinder, MetadataPathFinder
from importlib.machinery import ModuleSpec
from isolator.caller_finder import is_caller_part_of_library


LOGGER = logging.getLogger(__name__)


class VendorImporterModuleSpec(ModuleSpec):
    def __init__(self, loader: "VendorImporter", fullname: str, module: ModuleType):
        super().__init__(fullname, loader)
        self.module = module


class VendorImporter(DistributionFinder, MetaPathFinder, Loader):
    def __init__(
        self,
        package_name: str,
        vendorized_libs_dir_name: str,
        vendorized_libs_path: Path,
    ) -> None:
        self._library_name = package_name
        self._vendorized_libs_dir_name = vendorized_libs_dir_name
        self._vendorized_libs_path = vendorized_libs_path

    def find_spec(self, fullname: str, path: Sequence[str] | None, target: ModuleType | None = None) -> ModuleSpec | None:
        LOGGER.debug(f"Importing in vendorized find_spec: {fullname}")
        if fullname.startswith(self.vendor_prefix):
            # Cannot import actual path - another metapath finder should do that
            LOGGER.debug("Cannot import because it starts with vendor prefix (full import)")
            return None
        
        if fullname == self._library_name:
            LOGGER.debug(f"Cannot re-import the library: {self._library_name}")
            return None

        if not is_caller_part_of_library(self._library_name):
            LOGGER.debug("Cannot import because it's not part of library")
            return None

        vendored_import_path = f"{self.vendor_prefix}.{fullname}"
        try:
            LOGGER.debug(f"Importing: {vendored_import_path}")
            module = __import__(vendored_import_path, fromlist=[fullname.split(".")[0]])
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import: {fullname}: {exc!s}")
            return None

        LOGGER.debug(f"Imported: {module}")
        return VendorImporterModuleSpec(loader=self, fullname=fullname, module=module)
    
    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        # Caller must be part of library if this is called
        assert isinstance(spec, VendorImporterModuleSpec), "Spec must be from VendorImporter!"
        return spec.module
    
    def exec_module(self, module: ModuleType) -> None:
        # Nothing to execute in module
        pass
    
    def find_distributions(
        self,
        context: DistributionFinder.Context = DistributionFinder.Context()
    ) -> Iterable[Distribution]:
        LOGGER.debug(f"Finding distributions in VendorImporter for context: {context}")
        if not is_caller_part_of_library(self._library_name):
            from isolator.caller_finder import get_caller_path_outside_pyisolate, _iterate_over_stack
            x = get_caller_path_outside_pyisolate()
            y = list(_iterate_over_stack())
            print(x)
            print(y)
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


def invalidate_all_finder_caches() -> None:
    for finder in sys.meta_path:
        invalidate_caches = getattr(finder, "invalidate_caches", None)
        if invalidate_caches is not None:
            invalidate_caches()
