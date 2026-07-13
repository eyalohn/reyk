from typing import cast
from abc import abstractmethod
import builtins
from dataclasses import dataclass
from pathlib import Path
# Module for facilitating communication between Reyk versions.


REYK_COMMUNICATION_ATTRIBUTE_NAME = "_reyk_communication"
DEFAULT_VENDOR_LIBS_IMPORT_PATH = "libs"


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(kw_only=True)
class VendorPackage:
    package_name: str
    """
    Package to isolate - should be like `reyk` or like `reyk.sub_package`
    """
    vendor_libs_import_path: str | None = None
    """
    The import path for the vendored libraries ie: `reyk.libs` or `libs`.
    The default (if `None`) will be the `{package_name}.libs`.
    """
    vendor_libs_path: Path
    """
    Path to the vendor libs (defined by `vendor_libs_import_path`)
    """

    @property
    def vendor_prefix(self) -> str:
        if self.vendor_libs_import_path is None:
            return f"{self.package_name}.{DEFAULT_VENDOR_LIBS_IMPORT_PATH}"

        return self.vendor_libs_import_path


class ReykIsolator:
    @abstractmethod
    def add_package(self, *, vendor_package: VendorPackage) -> None: ...

    @abstractmethod
    def install(self) -> None: ...

    @abstractmethod
    def uninstall(self) -> None: ...

    @property
    @abstractmethod
    def version(self) -> Version: ...

    @property
    @abstractmethod
    def package_names(self) -> set[str]: ...


def install_reyk(reyk_isolator: ReykIsolator) -> None:
    if hasattr(builtins, REYK_COMMUNICATION_ATTRIBUTE_NAME):
        raise ValueError("Cannot install reyk communication module when one already exists")

    reyk_isolator.install()
    setattr(builtins, REYK_COMMUNICATION_ATTRIBUTE_NAME, reyk_isolator)


def uninstall_reyk() -> None:
    communication_module = get_installed_reyk()
    if communication_module is None:
        raise ValueError(f"No communication module installed {communication_module=}")

    communication_module.uninstall()
    delattr(builtins, REYK_COMMUNICATION_ATTRIBUTE_NAME)


def get_installed_reyk() -> ReykIsolator | None:
    return cast(ReykIsolator | None, getattr(builtins, REYK_COMMUNICATION_ATTRIBUTE_NAME, None))
