def extract_module_name(module_import_path: str) -> str:
    return module_import_path.rpartition(".")[-1]


def extract_first_package_name(module_import_path: str) -> str:
    return module_import_path.partition(".")[0]
