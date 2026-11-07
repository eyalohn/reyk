from typing import Optional
from unittest.mock import Mock

import pytest

from reyk.module_name_utils import LazyModuleName, ModuleNameCandidates, ModuleNameSource, ReykModuleNameExtractionError


@pytest.mark.parametrize("value", [None, "example.module"])
def test_lazy_module_name_caches_result(value: Optional[str]) -> None:
    extract = Mock(return_value=value)
    candidate = LazyModuleName(extract)
    extract.assert_not_called()

    assert candidate.value == value
    assert candidate.value == value
    extract.assert_called_once_with()


def test_candidate_iteration_is_lazy_cached_and_unique() -> None:
    declared = Mock(return_value="declared.module")
    spec = Mock(return_value="declared.module")
    path = Mock(return_value="owned.module")
    candidates = ModuleNameCandidates(
        {
            ModuleNameSource.PATH: LazyModuleName(path),
            ModuleNameSource.SPEC: LazyModuleName(spec),
            ModuleNameSource.DECLARED: LazyModuleName(declared),
        }
    )
    declared.assert_not_called()
    spec.assert_not_called()
    path.assert_not_called()

    assert next(candidates.iter_all_names()) == "declared.module"
    spec.assert_not_called()
    path.assert_not_called()

    assert list(candidates.iter_declared_names()) == ["declared.module"]
    path.assert_not_called()

    assert list(candidates.iter_all_names()) == ["declared.module", "owned.module"]
    assert list(candidates.iter_all_names()) == ["declared.module", "owned.module"]
    declared.assert_called_once_with()
    spec.assert_called_once_with()
    path.assert_called_once_with()


def test_missing_declared_names_allow_path_fallback() -> None:
    path = Mock(return_value="owned.module")
    candidates = ModuleNameCandidates(
        {
            ModuleNameSource.DECLARED: LazyModuleName(lambda: None),
            ModuleNameSource.SPEC: LazyModuleName(lambda: None),
            ModuleNameSource.PATH: LazyModuleName(path),
        }
    )
    assert list(candidates.iter_declared_names()) == []
    path.assert_not_called()
    assert list(candidates.iter_all_names()) == ["owned.module"]


def test_all_missing_candidates_raise_extraction_error() -> None:
    candidates = ModuleNameCandidates({source: LazyModuleName(lambda: None) for source in ModuleNameSource})
    assert list(candidates.iter_declared_names()) == []
    with pytest.raises(ReykModuleNameExtractionError):
        list(candidates.iter_all_names())


@pytest.mark.parametrize("source", list(ModuleNameSource))
@pytest.mark.parametrize("value", [None, "example.module"])
def test_retrieve_source_evaluates_only_that_source(source: ModuleNameSource, value: Optional[str]) -> None:
    extractors = {candidate_source: Mock(return_value=value) for candidate_source in ModuleNameSource}
    candidates = ModuleNameCandidates(
        {candidate_source: LazyModuleName(extract) for candidate_source, extract in extractors.items()}
    )
    assert candidates.get(source) == value
    assert candidates.get(source) == value
    for candidate_source, extract in extractors.items():
        if candidate_source == source:
            extract.assert_called_once_with()
        else:
            extract.assert_not_called()
