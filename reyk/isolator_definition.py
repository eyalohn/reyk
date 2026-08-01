"""
Module for facilitating communication between Reyk versions.
This module should aim to stay relatively unchanged to not break the protocol
between versions.
"""

from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from packaging.version import Version


DEFAULT_VENDOR_LIBS_IMPORT_PATH = "libs"


@dataclass
class VendorPackage:
    package_name: str
    """
    Package to isolate - should be like `reyk` or like `reyk.sub_package`
    """
    vendor_libs_path: Path
    """
    Path to the vendor libs (defined by `vendor_libs_import_path`)
    """
    vendor_libs_import_name: Optional[str] = None
    """
    The import name for the vendored libraries ie: `reyk.libs` or `libs`.
    The default (if `None`) will be the `{package_name}.libs`.
    """

    @property
    def vendor_prefix(self) -> str:
        if self.vendor_libs_import_name is None:
            return f"{self.package_name}.{DEFAULT_VENDOR_LIBS_IMPORT_PATH}"

        return self.vendor_libs_import_name


class ReykIsolator(ABC):
    """
    An abstract definition of operations an isolator can perform.
    If any definition changes in the class then the version property should increase by a "major".
    """

    @abstractmethod
    def add_package(self, *, vendor_package: VendorPackage) -> None: ...

    @abstractmethod
    def install(self) -> None: ...

    @abstractmethod
    def uninstall(self) -> None: ...

    @property
    @abstractmethod
    def package_names(self) -> set[str]: ...

    @property
    @abstractmethod
    def factory(self) -> type["ReykIsolatorFactory"]: ...


class ReykIsolatorFactory(ABC):
    @classmethod
    @abstractmethod
    def create_isolator(cls) -> ReykIsolator: ...

    @classmethod
    @abstractmethod
    def version(cls) -> Version: ...
