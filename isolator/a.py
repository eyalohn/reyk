# Early bootstrap (e.g., sitecustomize.py)

import builtins
import importlib
import threading
import types

# --- You provide this ---
def is_project_or_library_frame(frame) -> bool:
    """
    Return True when an import originating from this frame should be rewritten
    to `example_project.libs.<import path>`. Implement with your own logic.
    """
    filename = frame.f_code.co_filename
    return "/your_project_root/" in filename
# -------------------------

_VENDOR_PREFIX = "example_project.libs"
_original_import = builtins.__import__
_tls = threading.local()


def _resolve_absolute_name(name: str, globals_dict, level: int) -> str:
    if level == 0:
        return name
    pkg = globals_dict.get("__package__")
    if pkg is None:
        pkg = globals_dict.get("__name__")
        if pkg and "__path__" not in globals_dict:
            pkg = pkg.rpartition(".")[0]
    if not pkg:
        return name
    parent = pkg
    for _ in range(level - 1):
        parent = parent.rpartition(".")[0]
    return f"{parent}.{name}" if name else parent


def _should_rewrite_for_caller() -> bool:
    if getattr(_tls, "in_import", False):
        return False
    import inspect
    for fi in inspect.stack()[2:]:
        f = fi.frame
        if f.f_globals.get("__name__") == __name__:
            continue
        if is_project_or_library_frame(f):
            return True
    return False


def _make_toplevel_proxy(orig_name: str, leaf_mod: types.ModuleType) -> types.ModuleType:
    """
    Build a lightweight, non-sys.modules-backed 'top-level' module object that exposes
    the dotted path as attributes, so:
        import pydantic.validators as v   # v is leaf_mod
        import pydantic.validators        # binds 'pydantic', with '.validators' attr
    This proxy is *not* registered under sys.modules['pydantic'].
    """
    # Example: orig_name='pydantic.validators._util'
    parts = orig_name.split(".")
    # Build nested module objects
    top = types.ModuleType(parts[0])
    cursor = top
    for part in parts[1:-1]:
        sub = types.ModuleType(f"{cursor.__name__}.{part}")
        setattr(cursor, part, sub)
        cursor = sub
    # Attach the leaf module on the last attribute
    if len(parts) > 1:
        setattr(cursor, parts[-1], leaf_mod)
    # Also help attribute access on top-level for simple 'import pkg as x'
    # If there was no dot, just return the vendored leaf directly
    return top


def _import_vendor_abs(vendor_abs: str):
    """
    Import vendored module and return the *leaf* module object (like importlib.import_module).
    """
    return importlib.import_module(vendor_abs)


def _import_with_vendor_choice(name, globals=None, locals=None, fromlist=(), level=0):
    if getattr(_tls, "in_import", False):
        return _original_import(name, globals, locals, fromlist, level)

    _tls.in_import = True
    try:
        abs_name = _resolve_absolute_name(name, globals or {}, level)
        rewrite = _should_rewrite_for_caller()

        if not rewrite:
            # Outside project/lib: normal behavior
            return _original_import(name, globals, locals, fromlist, level)

        # Inside project/lib: attempt vendored import first
        vendor_abs = f"{_VENDOR_PREFIX}.{abs_name}"

        try:
            vendored_leaf = _import_vendor_abs(vendor_abs)
        except ModuleNotFoundError:
            # No vendored version: fall back
            return _original_import(name, globals, locals, fromlist, level)

        # Match Python's binding expectations *without* aliasing plain names:
        # - If fromlist is non-empty, __import__ is expected to return the package indicated
        #   by 'name' (leaf is fine per CPython's behavior for fromlist) — we return the leaf.
        if fromlist:
            return vendored_leaf

        # - If 'name' has no dot (e.g., 'pydantic'): return the vendored leaf module directly.
        if "." not in abs_name:
            return vendored_leaf

        # - If 'name' is dotted (e.g., 'pydantic.validators'):
        #   Ensure the vendored submodule is imported so attribute access works,
        #   then return a *proxy* top-level module object with that attribute chain.
        #   This avoids touching sys.modules['pydantic'].
        # Also ensure intermediate vendored submodules are loaded for attribute access
        # (import_module is idempotent).
        # Note: If abs_name has multiple segments, load them so attributes are present.
        base_parts = abs_name.split(".")
        for i in range(1, len(base_parts)):
            _import_vendor_abs(f"{_VENDOR_PREFIX}." + ".".join(base_parts[: i + 1]))

        proxy_top = _make_toplevel_proxy(abs_name, vendored_leaf)
        return proxy_top

    finally:
        _tls.in_import = False


# Activate
builtins.__import__ = _import_with_vendor_choice
