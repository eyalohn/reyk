import builtins
from typing import Optional, cast

from reyk.isolator_definition import DEFAULT_VENDOR_LIBS_IMPORT_PATH, ReykIsolator, ReykIsolatorFactory, VendorPackage
from reyk.caller_finder import get_caller_frame_outside_reyk
from reyk.vendor_importer import VendorImporterFactory

REYK_COMMUNICATION_ATTRIBUTE_NAME = "_reyk_communication"
"""
This attribute is set in `builtins` to facilitate 'communication' between reyk instances.
We intentionally don't use the `__import__` override to not depend on the reyk
implementation (which might in the future not depend on overriding `__import__`).
"""

FACTORY_IMPLEMENTATION: type[ReykIsolatorFactory] = VendorImporterFactory


def isolate_package(vendor_package: VendorPackage) -> None:
    reyk = get_installed_reyk()
    if reyk is None:
        reyk = FACTORY_IMPLEMENTATION.create_isolator()
        install_reyk(reyk)
    else:
        installed_reyk_version = reyk.factory.version()
        current_reyk_version = FACTORY_IMPLEMENTATION.version()
        if installed_reyk_version.major != current_reyk_version.major:
            raise ValueError(
                f"Cannot install {vendor_package.package_name=} because the currently installed Reyk has "
                f"a different major version. "
                f"(Installed Version: {installed_reyk_version} / (Library Version: {current_reyk_version=}). "
                "Consider installing reyk with a similar ReykIsolator major."
            )

    reyk.add_package(vendor_package=vendor_package)


def install_reyk(reyk_isolator: ReykIsolator) -> None:
    if hasattr(builtins, REYK_COMMUNICATION_ATTRIBUTE_NAME):
        raise ValueError("Cannot install Reyk communication module when one already exists")

    reyk_isolator.install()
    setattr(builtins, REYK_COMMUNICATION_ATTRIBUTE_NAME, reyk_isolator)


def uninstall_reyk() -> None:
    communication_module = get_installed_reyk()
    if communication_module is None:
        raise ValueError(f"No communication module installed {communication_module=}")

    communication_module.uninstall()
    delattr(builtins, REYK_COMMUNICATION_ATTRIBUTE_NAME)


def get_installed_reyk() -> Optional[ReykIsolator]:
    return cast(Optional[ReykIsolator], getattr(builtins, REYK_COMMUNICATION_ATTRIBUTE_NAME, None))


def get_caller_vendor_package() -> VendorPackage:
    caller = get_caller_frame_outside_reyk()
    package, _, _ = caller.module_name.rpartition(".")
    return VendorPackage(
        package_name=package,
        vendor_libs_path=caller.filename.parent / DEFAULT_VENDOR_LIBS_IMPORT_PATH,
    )
