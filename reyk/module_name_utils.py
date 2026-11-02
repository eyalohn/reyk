import inspect
import itertools
from abc import ABC, abstractmethod
from pathlib import Path
from types import FrameType
from collections.abc import Iterator, Sequence, Iterable
from typing import Optional

from reyk.isolator_definition import VendorPackage


class ReykModuleNameExtractionError(Exception): ...


_VIRTUAL_MODULE_NAME_PREFIX = "<"
_VIRTUAL_MODULE_NAME_SUFFIX = ">"
_INIT_MODULE_NAME = "__init__"
_MODULE_PACKAGE_SEPARATOR = "."

_MAIN_MODULE_NAMES = frozenset(
    {
        "__main__",
        "__mp_main__",  # multiprocessing
        "<run_path>",  # runpy.run_path
    }
)


def get_module_packages_count(module_name: str) -> int:
    return module_name.count(_MODULE_PACKAGE_SEPARATOR)


def is_module_from_package(module_name: str, package_name: str) -> bool:
    return (module_name == package_name) or (module_name.startswith(f"{package_name}."))


def calculate_package_tree(module_name: str) -> set[str]:
    """
    Returns all parents and module itself.

    Example:
        parent_package.child_package.module -> {
            'parent_package',
            'parent_package.child_package',
            'parent_package.child_package.module',
        }

    """
    return set(itertools.accumulate(module_name.split("."), lambda part1, part2: f"{part1}.{part2}"))


def extract_module_name_from_frame(
    frame: FrameType,
    potential_packages: Optional[Sequence[VendorPackage]],
) -> Iterator[str]:
    """Yield unique candidates in priority order, evaluating each method only when requested."""
    seen: set[str] = set()
    for extractor in _SORTED_EXTRACTION_METHODS_BY_PRIORITY:
        module_name = extractor.extract(frame, potential_packages)
        if module_name is not None and module_name not in seen:
            seen.add(module_name)
            yield module_name

    if len(seen) == 0:
        raise ReykModuleNameExtractionError(f"Unable to extract module name from: {frame=}")


class _ModuleNameExtractor(ABC):
    @abstractmethod
    def extract(
        self,
        frame: FrameType,
        potential_packages: Optional[Sequence[VendorPackage]],
    ) -> Optional[str]: ...


class _DeclaredModuleNameExtractor(_ModuleNameExtractor):
    def extract(
        self,
        frame: FrameType,
        potential_packages: Optional[Sequence[VendorPackage]],  # noqa: ARG002
    ) -> Optional[str]:
        module_name = frame.f_globals.get("__name__")

        if (
            not isinstance(module_name, str)
            or len(module_name) == 0
            or _is_main_module_name(module_name)
            or _is_virtual_value(module_name)
        ):
            return None

        return module_name


class _ModuleSpecNameExtractor(_ModuleNameExtractor):
    def extract(
        self,
        frame: FrameType,
        potential_packages: Optional[Sequence[VendorPackage]],  # noqa: ARG002
    ) -> Optional[str]:
        spec = frame.f_globals.get("__spec__")
        if spec is None:
            return None

        spec_name = getattr(spec, "name", None)
        if not isinstance(spec_name, str):
            return None

        if len(spec_name) == 0:
            return None

        if _is_main_module_name(spec_name):
            return None

        return spec_name


class _FilePathModuleNameExtractor(_ModuleNameExtractor):
    def extract(
        self,
        frame: FrameType,
        potential_packages: Optional[Sequence[VendorPackage]],
    ) -> Optional[str]:
        if potential_packages is None or len(potential_packages) == 0:
            return None

        module_path = self._get_module_file_path(frame)
        if module_path is None:
            return None

        return self._try_extract_module_name_from_path(module_path, potential_packages)

    @staticmethod
    def _get_module_file_path(frame: FrameType) -> Optional[Path]:
        filename = frame.f_code.co_filename
        if len(filename) == 0 or _is_virtual_value(filename):
            return None

        return Path(filename).resolve()

    def _try_extract_module_name_from_path(
        self,
        module_path: Path,
        potential_packages: Sequence[VendorPackage],
    ) -> Optional[str]:
        return min(
            self._get_potential_module_names_from_path(module_path, potential_packages),
            key=get_module_packages_count,
            default=None,
        )

    def _get_potential_module_names_from_path(
        self,
        module_path: Path,
        potential_packages: Sequence[VendorPackage],
    ) -> Iterable[str]:
        for potential_package in potential_packages:
            potential_module_name = self._try_build_module_name_from_path(potential_package, module_path)
            if potential_module_name is not None:
                yield potential_module_name

    def _try_build_module_name_from_path(self, potential_package: VendorPackage, module_path: Path) -> Optional[str]:
        try:
            relative_path = module_path.relative_to(potential_package.package_directory)
        except ValueError:
            # Module path is not relative to package
            return None

        relative_module_name = self._try_build_module_name_from_relative_path(relative_path)
        if relative_module_name is None:
            return None

        return potential_package.package_name + _MODULE_PACKAGE_SEPARATOR + relative_module_name

    @staticmethod
    def _try_build_module_name_from_relative_path(path: Path) -> Optional[str]:
        module_name = inspect.getmodulename(path.name)
        if module_name is None:
            return None

        parts = path.parent.parts
        if module_name == _INIT_MODULE_NAME:
            # Init must be a part of a package
            if len(parts) == 0:
                return None

            return _MODULE_PACKAGE_SEPARATOR.join(parts)

        return _MODULE_PACKAGE_SEPARATOR.join((*parts, module_name))


def _is_main_module_name(module_name: str) -> bool:
    return module_name in _MAIN_MODULE_NAMES


def _is_virtual_value(module_name: str) -> bool:
    return module_name.startswith(_VIRTUAL_MODULE_NAME_PREFIX) and module_name.endswith(_VIRTUAL_MODULE_NAME_SUFFIX)


_SORTED_EXTRACTION_METHODS_BY_PRIORITY: tuple[_ModuleNameExtractor, ...] = (
    _DeclaredModuleNameExtractor(),
    _ModuleSpecNameExtractor(),
    _FilePathModuleNameExtractor(),
)
