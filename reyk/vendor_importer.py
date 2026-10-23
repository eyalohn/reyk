from contextlib import contextmanager
from typing import cast
import builtins
import functools
import importlib
import importlib.metadata
import logging
import sys
from collections.abc import Iterable, Iterator, Mapping, Sequence
from importlib.metadata import Distribution, DistributionFinder, MetadataPathFinder
from types import ModuleType
from typing import Optional, Protocol

from packaging.version import Version
from reyk.caller_finder import get_caller_matching_package_from_store
from reyk.isolator_definition import ReykIsolator, ReykIsolatorFactory, VendorPackage
from reyk.module_name_utils import is_module_from_package
from reyk.stdlib_finder import is_part_of_stdlib
from reyk.vendor_packages_store import VendorPackagesStore
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
    def __init__(
        self,
        original_builtins_import_method: BuiltinsImporter,
        original_importlib_import_method: ImportLibImporter,
    ) -> None:
        self._is_installed = False
        self._original_builtins_import_method = original_builtins_import_method
        self._original_importlib_import_method = original_importlib_import_method
        self._package_store = VendorPackagesStore()
        self._sys_modules_wrapper = VendoredSysModules(sys.modules, self._package_store)

    def add_package(self, *, vendor_package: VendorPackage) -> None:
        self._sys_modules_wrapper.add_package_to_store(vendor_package)

    def builtins_import_override(
        self,
        name: str,
        globals: Optional[Mapping[str, object]] = None,
        locals: Optional[Mapping[str, object]] = None,
        fromlist: Optional[Sequence[str]] = (),
        level: int = 0,
    ) -> ModuleType:
        # Note: ALL import calls should be in this function as to not increase the call stack significantly

        is_relative_import = level > 0
        vendor_package = self._get_package_to_vendor(import_name=name, is_relative_import=is_relative_import)
        if vendor_package is None:
            # If importing a module which shouldn't be vendored
            # we need to exit the context to ensure we don't retrieve
            # a vendored module
            with self._with_modules_context(None):
                return self._original_builtins_import_method(name, globals, locals, fromlist, level)

        if is_relative_import:
            # If we do have a vendor package and its a relative import then we install vendored sys modules
            # then import it as usual because relative imports don't need any changes
            with self._with_modules_context(vendor_package.package_name):
                module = self._original_builtins_import_method(name, globals, locals, fromlist, level)
        else:
            vendored_import_path = self._vendor_import(vendor_package, name)
            try:
                LOGGER.debug(f"Importing: {vendored_import_path}")
                with self._with_modules_context(vendor_package.package_name):
                    module = self._original_builtins_import_method(
                        vendored_import_path, globals, locals, fromlist, level
                    )
            except ModuleNotFoundError as exc:
                LOGGER.debug(f"Failed to import vendored: {name}: {exc!s}")
                if self._is_error_because_of_nonexistent_module(exc, vendored_import_path):
                    raise
                # Likely trying to import a module in the importing package/a non-vendored library
                with self._with_modules_context(None):
                    module = self._original_builtins_import_method(name, globals, locals, fromlist, level)
            else:
                is_plain_import = fromlist is None or len(fromlist) == 0
                if is_plain_import:
                    module = self._retrieve_absolute_import_module(vendor_package, name, module)
                    self._add_imported_sub_modules_to_vendored(vendor_package, name, module)

        LOGGER.debug(f"Imported: {module}")
        return module

    def importlib_import_override(
        self,
        name: str,
        package: Optional[str] = None,
    ) -> ModuleType:
        # If package is not None it's a relative import
        is_relative_import = package is not None
        vendor_package = self._get_package_to_vendor(import_name=name, is_relative_import=is_relative_import)
        if vendor_package is None:
            self._sys_modules_wrapper.remove_vendored_sys_modules()
            return self._original_importlib_import_method(name, package)

        # Relative imports need fix - see https://github.com/eyalohn/reyk/issues/53
        vendored_import_path = name if is_relative_import else self._vendor_import(vendor_package, name)
        self._sys_modules_wrapper.install_vendored_sys_modules(vendor_package.package_name)
        try:
            imported_module = self._original_importlib_import_method(vendored_import_path, package)
        except ModuleNotFoundError as exc:
            LOGGER.debug(f"Failed to import vendored: {name}: {exc!s}")
            if self._is_error_because_of_nonexistent_module(exc, vendored_import_path):
                raise
            self._sys_modules_wrapper.remove_vendored_sys_modules()
            return self._original_importlib_import_method(name, package)

        # It's important at the end to return to vendored sys module if we imported
        # a vendored package in case an import was made inside this import which changed the state
        self._sys_modules_wrapper.install_vendored_sys_modules(vendor_package.package_name)
        return imported_module

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
        *,
        import_name: str,
        is_relative_import: bool,
    ) -> Optional[VendorPackage]:
        if not is_relative_import:
            # Can't be a relative import to stdlib or directly to a package
            if is_part_of_stdlib(import_name):
                LOGGER.debug(f"Skipping vendor import attempt for {import_name} because the same name exists in stdlib")
                return None

            if self._package_store.is_package_in_store(import_name):
                LOGGER.debug(f"Cannot re-import the library: {import_name=}")
                return None

        matching_vendor_package_modules = get_caller_matching_package_from_store(self._package_store)
        if matching_vendor_package_modules is None:
            LOGGER.debug("Cannot import because it's not part of library")
            return None

        matching_vendor_package = matching_vendor_package_modules.vendor_package
        if import_name.startswith(matching_vendor_package.vendor_prefix):
            LOGGER.debug(
                "The attempted import is already for a vendored package therefore there's "
                "no need to change the import path"
            )
            return None

        return matching_vendor_package

    def _is_error_because_of_nonexistent_module(self, error: ModuleNotFoundError, imported_module_name: str) -> bool:
        # We should only try to re-import if the failed module is the vendored_import_path or one of its
        # ancestors. If it's not the case then it means the vendored import path was imported but it
        # ran an unsuccessful import itself
        return error.name is not None and not is_module_from_package(imported_module_name, error.name)

    @contextmanager
    def _with_modules_context(self, package_name_in_context: str | None) -> Iterator[None]:
        package_before_context_change = self._sys_modules_wrapper.current_package_in_context
        self._sys_modules_wrapper.set_current_package_in_context(package_name_in_context)
        try:
            yield
        except Exception:
            # Return to the previous state as we are returning to try-except without having imported the module
            self._sys_modules_wrapper.set_current_package_in_context(package_before_context_change)
            raise

        # It's important at the end to return to vendored sys module if we imported
        # a vendored package in case an import was made inside this import which changed the state
        self._sys_modules_wrapper.set_current_package_in_context(package_name_in_context)

    def find_distributions(
        self,
        context: Optional[DistributionFinder.Context] = None,
    ) -> Iterable[Distribution]:
        if context is None:
            context = DistributionFinder.Context()

        LOGGER.debug(f"Finding distributions in VendorImporter for context: {context}")
        vendor_package_modules = get_caller_matching_package_from_store(self._package_store)
        if vendor_package_modules is None:
            LOGGER.debug("Returning empty list in find_distributions because not part of library")
            return []

        vendor_package = vendor_package_modules.vendor_package
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
    def package_names(self) -> set[str]:
        return set(self._package_store.get_package_names())

    @property
    def factory(self) -> type["VendorImporterFactory"]:
        return VendorImporterFactory


class VendorImporterFactory(ReykIsolatorFactory):
    VENDOR_IMPORTER_VERSION = Version.from_parts(release=(1, 0, 0))

    @classmethod
    def create_isolator(cls) -> ReykIsolator:
        return VendorImporter(
            original_builtins_import_method=cast(BuiltinsImporter, builtins.__import__),
            original_importlib_import_method=importlib.import_module,
        )

    @classmethod
    def version(cls) -> Version:
        return cls.VENDOR_IMPORTER_VERSION
