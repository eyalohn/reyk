import sys
from types import ModuleType


class SysModulesStateHandler:
    def __init__(self) -> None:
        self._are_vendorized_modules_installed: bool = False
        self._vendorized_sys_modules: dict[str, ModuleType] = {}
        # Retain cache of sys modules with same name as vendorized sys modules
        self._previous_sys_modules: dict[str, ModuleType] = {}

    def install_vendorized_sys_modules(self) -> None:
        if self._are_vendorized_modules_installed:
            return

        for vendorized_module_name in self._vendorized_sys_modules.keys():
            current_module = sys.modules.get(vendorized_module_name)
            if current_module is not None:
                self._previous_sys_modules[vendorized_module_name] = current_module

        sys.modules.update(self._vendorized_sys_modules)
        self._are_vendorized_modules_installed = True

    def remove_vendorized_sys_modules(self) -> None:
        if not self._are_vendorized_modules_installed:
            return

        for vendorized_module_name in self._vendorized_sys_modules.keys():
            sys.modules.pop(vendorized_module_name, None)

        sys.modules.update(self._previous_sys_modules)
        self._are_vendorized_modules_installed = False

    def add_only_vendorized_module(self, name: str, module: ModuleType) -> None:
        self._vendorized_sys_modules[name] = module
        if self._are_vendorized_modules_installed:
            sys.modules[name] = module

    def get_vendorized_module_by_name(self, name: str) -> ModuleType | None:
        return self._vendorized_sys_modules.get(name)

    def clear_state(self) -> None:
        self._previous_sys_modules.clear()
        # Remove vendorized sys modules but don't return previous sys modules (because they're empty)
        self.remove_vendorized_sys_modules()
        self._vendorized_sys_modules.clear()
        self._are_vendorized_modules_installed = False
