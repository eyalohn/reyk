import sys
from collections.abc import Sequence
from types import ModuleType
import logging
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
from isolator.caller_finder import is_caller_part_of_library


LOGGER = logging.getLogger(__name__)


class VendorImporterModuleSpec(ModuleSpec):
    def __init__(self, loader: "VendorImporter", fullname: str, module: ModuleType):
        super().__init__(fullname, loader)
        self.module = module


class VendorImporter(MetaPathFinder, Loader):
    def __init__(self, package_name: str, vendorized_libs_dir_name: str) -> None:
        self._library_name = package_name
        self._vendorized_libs_dir_name = vendorized_libs_dir_name

    def find_spec(self, fullname: str, path: Sequence[str] | None, target: ModuleType | None = None) -> ModuleSpec | None:
        LOGGER.debug(f"Importing in vendorized find_spec: {fullname}")
        if fullname.startswith(self.vendor_prefix):
            # Cannot import actual path - another metapath finder should do that
            LOGGER.debug("Cannot import because it starts with vendor prefix (full import)")
            return None

        if not is_caller_part_of_library(self._library_name):
            LOGGER.debug("Cannot import because it's not part of library")
            return None

        vendored_import_path = f"{self.vendor_prefix}.{fullname}"
        try:
            LOGGER.debug(f"Importing: {vendored_import_path}")
            module = __import__(vendored_import_path, fromlist=[fullname.split(".")[0]])
        except ModuleNotFoundError:
            LOGGER.debug(f"Failed to import: {fullname}")
            return None

        # mysterious hack:
        # Remove the reference to the extant package/module
        # on later Python versions to cause relative imports
        # in the vendor package to resolve the same modules
        # as those going through this importer.
        if sys.version_info > (3, 3):
            del sys.modules[vendored_import_path]
        LOGGER.debug(f"Imported: {module}")
        return VendorImporterModuleSpec(loader=self, fullname=fullname, module=module)
    
    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        # Caller must be part of library if this is called
        assert isinstance(spec, VendorImporterModuleSpec), "Spec must be from VendorImporter!"
        return spec.module
    
    def exec_module(self, module: ModuleType) -> None:
        # Nothing to execute in module
        pass

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
