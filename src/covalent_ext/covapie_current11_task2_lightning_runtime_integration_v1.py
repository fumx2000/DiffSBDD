"""Fail-closed Lightning transport helpers for Current11 Task 2 V1."""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as _compiler_context_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_context_v1
    as _remap_context_owner,
)
from covalent_ext import covapie_current11_task2_runtime_caller_v1 as _caller_owner


__all__ = (
    "validate_covapie_current11_task2_lightning_runtime_configuration_v1",
    "build_or_reuse_covapie_current11_task2_lightning_runtime_context_pair_v1",
    "attach_covapie_current11_task2_lightning_runtime_result_v1",
)

INTEGRATION_ERROR = (
    "COVAPIE_CURRENT11_TASK2_LIGHTNING_RUNTIME_INTEGRATION_V1_ERROR"
)
STRUCTURED_RUNTIME_FAILURE = (
    "COVAPIE_CURRENT11_TASK2_LIGHTNING_RUNTIME_INTEGRATION_V1_"
    "STRUCTURED_RUNTIME_FAILURE"
)
VIRTUAL_NODES_UNSUPPORTED = (
    "COVAPIE_CURRENT11_TASK2_LIGHTNING_RUNTIME_INTEGRATION_V1_"
    "VIRTUAL_NODES_UNSUPPORTED"
)
SIDECAR_FIELD = "covapie_current11_task2_runtime_result_v1"

_STRUCTURED_FAILURE_STATUSES = (
    "extractor_failure",
    "compiler_failure",
    "remap_failure",
)


def _fail() -> NoReturn:
    raise ValueError(INTEGRATION_ERROR)


def _validated_paths(
    *,
    enabled: object,
    repository_root: object,
    state_root: object,
) -> tuple[Path | None, Path | None]:
    if type(enabled) is not bool:
        _fail()
    if enabled is False:
        if repository_root is not None or state_root is not None:
            _fail()
        return None, None
    if (
        type(repository_root) is not str
        or not repository_root
        or not Path(repository_root).is_absolute()
        or type(state_root) is not str
        or not state_root
        or not Path(state_root).is_absolute()
    ):
        _fail()
    return Path(repository_root), Path(state_root)


def validate_covapie_current11_task2_lightning_runtime_configuration_v1(
    *,
    enabled: object,
    repository_root: object,
    state_root: object,
    virtual_nodes: object,
) -> None:
    """Validate explicit activation and root configuration without I/O."""

    _validated_paths(
        enabled=enabled,
        repository_root=repository_root,
        state_root=state_root,
    )
    if enabled is True:
        if type(virtual_nodes) is not bool:
            _fail()
        if virtual_nodes is True:
            raise ValueError(VIRTUAL_NODES_UNSUPPORTED)


def build_or_reuse_covapie_current11_task2_lightning_runtime_context_pair_v1(
    *,
    repository_root: object,
    state_root: object,
    remap_context: object,
    compiler_context: object,
) -> tuple[object, object]:
    """Build both contexts atomically, or reuse one complete retained pair."""

    repository, state = _validated_paths(
        enabled=True,
        repository_root=repository_root,
        state_root=state_root,
    )
    if (remap_context is None) != (compiler_context is None):
        _fail()
    if remap_context is not None:
        return remap_context, compiler_context
    try:
        new_remap_context = (
            _remap_context_owner.build_covapie_current11_task2_batch_index_remap_adapter_context_v1(
                repo_root=repository,
                state_root=state,
            )
        )
        if new_remap_context is None:
            _fail()
        new_compiler_context = (
            _compiler_context_owner.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
                remap_context=new_remap_context,
            )
        )
        if new_compiler_context is None:
            _fail()
    except Exception as error:
        if type(error) is ValueError and str(error) == INTEGRATION_ERROR:
            raise
        raise ValueError(INTEGRATION_ERROR) from error
    return new_remap_context, new_compiler_context


def attach_covapie_current11_task2_lightning_runtime_result_v1(
    *,
    enabled: object,
    batch: object,
    remap_context: object,
    compiler_context: object,
) -> object:
    """Attach one full-success caller result to a shallow batch wrapper."""

    if enabled is False:
        return batch
    if enabled is not True:
        _fail()
    if (
        type(batch) is not dict
        or remap_context is None
        or compiler_context is None
        or SIDECAR_FIELD in batch
    ):
        _fail()
    result = _caller_owner.run_covapie_current11_task2_runtime_caller_v1(
        batch=batch,
        remap_context=remap_context,
        compiler_context=compiler_context,
    )
    if type(result) is not dict:
        _fail()
    runtime_status = result.get("runtime_status")
    if runtime_status in _STRUCTURED_FAILURE_STATUSES:
        raise RuntimeError(STRUCTURED_RUNTIME_FAILURE)
    if runtime_status != "full_success":
        _fail()
    wrapped = dict(batch)
    wrapped[SIDECAR_FIELD] = result
    return wrapped
