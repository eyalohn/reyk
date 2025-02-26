import sys
from collections.abc import Sequence
from types import ModuleType
from pathlib import Path
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from isolator.caller_finder import is_caller_part_of_library


class VendorImporterModuleSpec(ModuleSpec):
    def __init__(self, loader: "VendorImporter", fullname: str, module: ModuleType):
        super().__init__(fullname, loader)
        self.module = module


class VendorImporter(MetaPathFinder, Loader):
    def __init__(self, package_name: str, vendorized_libs_dir_name: str) -> None:
        self._library_name = package_name
        self._vendorized_libs_dir_name = vendorized_libs_dir_name

    def find_spec(self, fullname: str, path: Sequence[str] | None, target: ModuleType | None = None) -> ModuleSpec | None:
        print(f"Importing in find_spec: {fullname}")
        if fullname.startswith(self.vendor_prefix):
            # Cannot import actual path - another metapath finder should do that
            print("Cannot import because it starts with vendor prefix (full import)")
            return None

        if not is_caller_part_of_library(self._library_name):
            print("Cannot import because it's not part of library")
            return None

        try:
            vendored_import_path = f"{self.vendor_prefix}.{fullname}"
            print(f"Importing: {vendored_import_path}")
            module = __import__(vendored_import_path, fromlist=[fullname.split(".")[0]])
        except ModuleNotFoundError:
            print(f"Failed to import: {fullname}")
            return None

        print(f"Imported: {module}")
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
