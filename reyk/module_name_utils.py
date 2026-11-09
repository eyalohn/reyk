import inspect
import itertools
from dataclasses import dataclass
from enum import Enum
from functools import cached_property, partial
from abc import ABC, abstractmethod
from pathlib import Path
from types import FrameType
from collections.abc import Callable, Iterator, Sequence, Iterable
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


def is_relative_module_name(module_name: str) -> bool:
    return module_name.startswith(_MODULE_PACKAGE_SEPARATOR)


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


@dataclass
class LazyModuleName:
    extract: Callable[[], Optional[str]]

    @cached_property
    def value(self) -> Optional[str]:
        return self.extract()


@dataclass
class ModuleNameCandidates:
    candidates: dict["ModuleNameSource", LazyModuleName]

    def get(self, source: "ModuleNameSource") -> Optional[str]:
        """Retrieve a source's name, evaluating it only on first access."""
        return self.candidates[source].value

    def iter_declared_names(self) -> Iterator[str]:
        return self._iterate_unique((ModuleNameSource.DECLARED, ModuleNameSource.SPEC))

    def iter_all_names(self) -> Iterator[str]:
        has_module_name = False
        for name in self._iterate_unique(ModuleNameSource):
            has_module_name = True
            yield name

        if not has_module_name:
            raise ReykModuleNameExtractionError("Unable to extract module name from frame")

    def _iterate_unique(self, sources: Iterable["ModuleNameSource"]) -> Iterator[str]:
        seen: set[str] = set()
        for source in sources:
            name = self.get(source)
            if name is not None and name not in seen:
                seen.add(name)
                yield name


def extract_module_names_from_frame(
    frame: FrameType,
    potential_packages: Optional[Sequence[VendorPackage]],
) -> ModuleNameCandidates:
    """Create reusable candidates, evaluating and caching each extractor only when requested."""
    return ModuleNameCandidates(
        candidates={source: source.value.as_lazy_name(frame, potential_packages) for source in ModuleNameSource},
    )


class _ModuleNameExtractor(ABC):
    @classmethod
    def as_lazy_name(
        cls,
        frame: FrameType,
        potential_packages: Optional[Sequence[VendorPackage]],
    ) -> LazyModuleName:
        return LazyModuleName(partial(cls.extract, frame, potential_packages))

    @staticmethod
    @abstractmethod
    def extract(
        frame: FrameType,
        potential_packages: Optional[Sequence[VendorPackage]],
    ) -> Optional[str]: ...


class _DeclaredModuleNameExtractor(_ModuleNameExtractor):
    @staticmethod
    def extract(
        frame: FrameType,
        potential_packages: Optional[Sequence[VendorPackage]],  # noqa: ARG004
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
    @staticmethod
    def extract(
        frame: FrameType,
        potential_packages: Optional[Sequence[VendorPackage]],  # noqa: ARG004
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
    @staticmethod
    def extract(
        frame: FrameType,
        potential_packages: Optional[Sequence[VendorPackage]],
    ) -> Optional[str]:
        if potential_packages is None or len(potential_packages) == 0:
            return None

        module_path = _FilePathModuleNameExtractor._get_module_file_path(frame)
        if module_path is None:
            return None

        return _FilePathModuleNameExtractor._try_extract_module_name_from_path(module_path, potential_packages)

    @staticmethod
    def _get_module_file_path(frame: FrameType) -> Optional[Path]:
        filename = frame.f_code.co_filename
        if len(filename) == 0 or _is_virtual_value(filename):
            return None

        return Path(filename).resolve()

    @staticmethod
    def _try_extract_module_name_from_path(
        module_path: Path,
        potential_packages: Sequence[VendorPackage],
    ) -> Optional[str]:
        return min(
            _FilePathModuleNameExtractor._get_potential_module_names_from_path(module_path, potential_packages),
            key=get_module_packages_count,
            default=None,
        )

    @staticmethod
    def _get_potential_module_names_from_path(
        module_path: Path,
        potential_packages: Sequence[VendorPackage],
    ) -> Iterable[str]:
        for potential_package in potential_packages:
            potential_module_name = _FilePathModuleNameExtractor._try_build_module_name_from_path(
                potential_package, module_path
            )
            if potential_module_name is not None:
                yield potential_module_name

    @staticmethod
    def _try_build_module_name_from_path(potential_package: VendorPackage, module_path: Path) -> Optional[str]:
        try:
            relative_path = module_path.relative_to(potential_package.package_directory)
        except ValueError:
            # Module path is not relative to package
            return None

        relative_module_name = _FilePathModuleNameExtractor._try_build_module_name_from_relative_path(relative_path)
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


class ModuleNameSource(Enum):
    """Sources module names can be retrieved from. Sorted by reliability"""

    DECLARED = _DeclaredModuleNameExtractor
    SPEC = _ModuleSpecNameExtractor
    PATH = _FilePathModuleNameExtractor
