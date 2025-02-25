from typing import Any
import functools


class SysModulesWrapper(dict):
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
    def __init__(self, package_name: str, vendorized_libs_dir_name: str) -> None:
        self._package_name = package_name
        self._vendorized_libs_dir_name = vendorized_libs_dir_name
        self._library_modules = {}
        self._user_modules = {}
    
    def __getattribute__(self, name: str) -> Any:
        if name in ("_library_modules", "_user_modules"):
            return super().__getattribute__(name)

        
        return 
