import sys
from typing import Sequence
from types import ModuleType
from pathlib import Path
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from isolator.caller_finder import get_caller


class VendorImporterModuleSpec(ModuleSpec):
    def __init__(self, loader: "VendorImporter", fullname: str, path: Sequence[str] | None, target: ModuleType | None = None) -> None:
        super().__init__(fullname, loader)
        self.path = path
        self.target = target


class VendorImporter(MetaPathFinder, Loader):
    def __init__(self, package_name: str, vendorized_libs_dir_name: str) -> None:
        self._library_name = package_name
        self._vendorized_libs_dir_name = vendorized_libs_dir_name
        # To avoid recursion because we try to import in create_module
        self._is_importing: bool = False

    def find_spec(self, fullname: str, path: Sequence[str] | None, target: ModuleType | None = None) -> ModuleSpec | None:
        if self._is_importing:
            return None

        if not self._is_caller_part_of_library():
            return None

        return VendorImporterModuleSpec(loader=self, fullname=fullname, path=path, target=target)
    
    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        # Caller must be part of library if this is called
        assert isinstance(spec, VendorImporterModuleSpec), "Spec must be from VendorImporter!"
        vendored_import_path = f"{self._library_name}.{self._vendorized_libs_dir_name}.{spec.name}"
        self._is_importing = True
        try:
            module = __import__(vendored_import_path, fromlist=[spec.name.split(".")[0]])
        finally:
            self._is_importing = False

        if module is None:
            return None
        # mysterious hack:
        # Remove the reference to the extant package/module
        # on later Python versions to cause relative imports
        # in the vendor package to resolve the same modules
        # as those going through this importer.
        if sys.version_info >= (3, 4):
            del sys.modules[vendored_import_path]
        
        return module
    
    def _try_import_with_other_finders(self, vendored_import_path: str, spec: VendorImporterModuleSpec) -> ModuleType | None:
        for finder in sys.meta_path:
            if finder is self:
                continue
            
            other_finder_spec = finder.find_spec(vendored_import_path, spec.path, spec.target)
            if other_finder_spec is None:
                continue
            
            return module_from_spec(other_finder_spec)
        
        return None

    def exec_module(self, module: ModuleType) -> None:
        # Nothing to execute in module
        pass

    def _is_caller_part_of_library(self) -> bool:
        caller = get_caller()
        path = Path(caller.filename)
        return any(
            parent.name == self._library_name
            for parent in path.parents
        )
    
    def install(self) -> None:
        if self not in sys.meta_path:
            sys.meta_path.insert(0, self)
