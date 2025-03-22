from typing import Any
from types import ModuleType
from isolator.caller_finder import is_caller_part_of_library
from isolator.stdlib_finder import is_part_of_stdlib


import sys


class SysModulesWrapper(dict[str, ModuleType]):
    """
    The sys.modules attribute contains cached modules.
    When we import a package that then imports a vendorized package - the sys modules
    will contain the vendorized package under the name of the value we tried to import ie:
    ```
    import my_package
    ```
    resolves to
    ```
    import my_lib._vendor.my_package
    ```
    Yet the `sys.modules` will contain: `{"my_package": my_lib._vendor.my_package}`.
    To mitigate this we create a wrapper around `sys.modules` which will include a different
    result based on the call stack.
    """
    def __init__(self, original_sys_modules: dict[str, ModuleType], library_name: str) -> None:
        self._original_sys_modules = original_sys_modules
        self._library_name = library_name
        self._library_modules: dict[str, ModuleType] = original_sys_modules.copy()
        self._user_modules: dict[str, ModuleType] = original_sys_modules
    
    def __setitem__(self, key: str, value: ModuleType) -> None:
        module_name = value.__name__
        if is_part_of_stdlib(module_name):
            self._library_modules[key] = value
            self._user_modules[key] = value
            return None

        return getattr(self, "__setitem__")(key, value)
    
    def get(self, key, default=None) -> ModuleType:
        lib = is_caller_part_of_library(self._library_name)
        if lib:
            frames = []
            f = sys._getframe(1)
            while f:
                frames.append(f)
                f = f.f_back
            print(f"Getting key: {key} {default} {lib} from ")
        if lib:
            val = self._library_modules.get(key, default)
            print(f"Returned user module: {val}")
            return val

        return self._user_modules.get(key, default)
    
    def __getitem__(self, key: str) -> ModuleType:
        return getattr(self, "__getitem__")(key)
    
    def __delitem__(self, key: str) -> None:
        return getattr(self, "__contains__")(key)
    
    def __contains__(self, key: object) -> bool:
        return getattr(self, "__contains__")(key)
    
    def __len__(self) -> int:
        return getattr(self, "__len__")()
    
    def __str__(self) -> str:
        return getattr(self, "__str__")()
    
    def __repr__(self) -> str:
        return getattr(self, "__repr__")()

    def __getattribute__(self, name: str) -> Any:
        if name in ("_library_name", "_library_modules", "_user_modules", "get"):
            return super().__getattribute__(name)
        
        lib = is_caller_part_of_library(self._library_name)
        if not lib:
            frames = []
            f = sys._getframe(1)
            while f:
                frames.append(f)
                f = f.f_back
            print(f"Getting attribute: {name} {lib} from {frames}")
        if lib:
            return getattr(self._library_modules, name)

        return getattr(self._user_modules, name)
