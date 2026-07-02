from collections import UserDict
from collections.abc import MutableMapping
from types import ModuleType
from reyk.caller_finder import is_caller_part_of_library
from reyk.stdlib_finder import is_part_of_stdlib


class VendoredSysModules(UserDict[str, ModuleType]):
    """
    Wrapper for overriding python-direct access to return vendored modules based on
    stack trace context. This will usually not effect the actual import mechanism as it access
    the original `sys.modules`.

    Therefore we are doing best-effort here:
    1. If there's access from C/the original sys modules then we ensure to take the vendored module only if we're in
       in a vendored context (in the middle of a vendored import), otherwise we'll use the
       original user imported module/no module with the same name
    2. If we access from Python to the sys modules wrapper then we'll never access the original
       sys modules and therefore use the appropriate modules based on the vendor context (user module if outside vendor
       and vendor module if inside vendor)
    """

    DICT_INTERNAL_DATA_FIELD_NAME = "data"

    def __init__(self, original_sys_modules: dict[str, ModuleType], package_name: str, vendor_prefix: str) -> None:
        self._package_name = package_name
        self._vendor_prefix = vendor_prefix
        self.original_sys_modules = original_sys_modules
        self._package_modules: dict[str, ModuleType] = original_sys_modules.copy()
        self._user_modules: dict[str, ModuleType] = original_sys_modules.copy()
        self._are_vendored_modules_installed = False

    def install_vendored_sys_modules(self) -> None:
        if self._are_vendored_modules_installed:
            return

        self._switch_original_sys_modules_state(self._package_modules, self._user_modules)
        self._are_vendored_modules_installed = True

    def remove_vendored_sys_modules(self) -> None:
        if not self._are_vendored_modules_installed:
            return

        self._switch_original_sys_modules_state(self._user_modules, self._package_modules)
        self._are_vendored_modules_installed = False

    def _switch_original_sys_modules_state(
        self,
        new_sys_modules: dict[str, ModuleType],
        previous_sys_modules: dict[str, ModuleType],
    ) -> None:
        for module_name in previous_sys_modules.keys():
            self.original_sys_modules.pop(module_name, None)

        self.original_sys_modules.update(new_sys_modules)

    def __setitem__(self, key: str, value: ModuleType) -> None:
        module_name = value.__name__
        if is_part_of_stdlib(module_name) or module_name == self._package_name:
            # Standard libraries should be registered as both package & user modules
            self.original_sys_modules[key] = value
            self._package_modules[key] = value
            self._user_modules[key] = value
            return

        dicts_to_update: list[MutableMapping[str, ModuleType]] = [super()]
        if is_caller_part_of_library(self._package_name) == self._are_vendored_modules_installed:
            dicts_to_update.append(self.original_sys_modules)

        # The setitem will be directed to package modules/user modules
        for dict_to_update in dicts_to_update:
            if key.startswith(self._vendor_prefix) and key != self._vendor_prefix:
                dict_to_update.__setitem__(key.removeprefix(self._vendor_prefix).removeprefix("."), value)

            dict_to_update.__setitem__(key, value)

    def __getattribute__(self, name: str) -> object:
        if name == VendoredSysModules.DICT_INTERNAL_DATA_FIELD_NAME:
            if is_caller_part_of_library(self._package_name):
                return self._package_modules

            return self._user_modules

        return super().__getattribute__(name)
