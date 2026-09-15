"""Opt-in train10 checkpoint single-optimizer-step validation V1.

Ordinary import, collection, and execution are non-model-only.  The sole real
node is disabled unless
``COVAPIE_RUN_TRAIN10_CHECKPOINT_SINGLE_OPTIMIZER_STEP=1``.  That variable is
only a technical entry switch: a future invocation still requires separate,
explicit parameter-update authorization.  The bounded real path is one CPU
checkpoint/model/migration, one epoch0/seed0 train10 carrier, one grad-enabled
forward, one original ``loss_total.backward()``, one production optimizer,
and one ``optimizer.step()``.  It has no second forward or training loop.
"""

from __future__ import annotations

import ast
import contextlib
from dataclasses import dataclass, fields
import hashlib
import importlib.util
import inspect
import io
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from typing import Callable, Iterator, Mapping, Sequence
from unittest import mock

import pytest
import torch


TASK_ID_V1 = "validate_covapie_train10_checkpoint_single_optimizer_step_v1"
REAL_SINGLE_STEP_OPT_IN_V1 = (
    "COVAPIE_RUN_TRAIN10_CHECKPOINT_SINGLE_OPTIMIZER_STEP"
)
EXPECTED_REPOSITORY_BASELINE_V1 = (
    "3216841ade2bffafb07008ab41610af7e1fb4a5d"
)
EXPECTED_CHECKPOINT_SIZE_BYTES_V1 = 17_861_341
EXPECTED_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
EXPECTED_TORCH_VERSION_V1 = "2.5.1+cu124"
MODEL_INITIALIZATION_SEED_V1 = 20_260_821
DIFFUSION_FORWARD_SEED_V1 = 11_030_037
EXPECTED_EPOCH0_TASK_IDS_V1 = (4, 4, 2, 0, 4, 4, 0, 0, 4, 4)
CANONICAL_EXACT5_V1 = (
    (0, "warhead_only", "A", (2,)),
    (1, "linker_plus_warhead", "B", (1, 2)),
    (2, "scaffold_plus_warhead", "B2", (0, 2)),
    (3, "scaffold_only", "B3", (0,)),
    (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
)

PUBLISHED_TRAIN10_BACKWARD_RELATIVE_V1 = (
    "tests/test_covapie_train10_checkpoint_backward_no_update_v1.py"
)
PUBLISHED_TRAIN10_FORWARD_RELATIVE_V1 = (
    "tests/test_covapie_train10_checkpoint_forward_no_update_v1.py"
)
PUBLISHED_TRAIN10_ADAPTER_RELATIVE_V1 = (
    "src/covalent_ext/covapie_train10_hidden_post_forward_adapter_v1.py"
)
PUBLISHED_OLD_SINGLE_STEP_RELATIVE_V1 = (
    "tests/test_covapie_batch001_checkpoint_single_optimizer_step_v1.py"
)
PUBLISHED_TRAINING_OWNER_RELATIVE_V1 = (
    "src/covalent_ext/covapie_current11_training_lightning_module_v1.py"
)
PUBLISHED_TRAIN10_BACKWARD_SIZE_V1 = 67_691
PUBLISHED_TRAIN10_BACKWARD_SHA256_V1 = (
    "151bb2ccd74c3c3e9e78cc0dfb928e199ceb729cefdcd422657706f2d4e35d3d"
)
PUBLISHED_TRAIN10_FORWARD_SIZE_V1 = 127_015
PUBLISHED_TRAIN10_FORWARD_SHA256_V1 = (
    "d602987f0a4d76799427213e62205cb70505064c93e126fd3c8a3bae80b46b79"
)
PUBLISHED_TRAIN10_ADAPTER_SIZE_V1 = 13_686
PUBLISHED_TRAIN10_ADAPTER_SHA256_V1 = (
    "5beaa700e2e5af87265c022a919dddfe1c8054114a45415adc416e5fe25fa40d"
)
PUBLISHED_OLD_SINGLE_STEP_SIZE_V1 = 49_785
PUBLISHED_OLD_SINGLE_STEP_SHA256_V1 = (
    "e13924f6f144dd1e34e8b5545b311637aacb8d67053bac03036d4013e78da749"
)
PUBLISHED_TRAINING_OWNER_SIZE_V1 = 35_218
PUBLISHED_TRAINING_OWNER_SHA256_V1 = (
    "a61041ef44e79c0622645965461bf4cc0275e5f3bec9a756fcf7d36a4c9c391b"
)


def _required_canonical_directory_v1(environment_name: str) -> Path:
    configured = os.environ.get(environment_name)
    assert configured is not None, environment_name
    path = Path(configured)
    assert path.is_absolute(), environment_name
    metadata = path.lstat()
    assert stat.S_ISDIR(metadata.st_mode) and not path.is_symlink()
    assert path.resolve(strict=True) == path
    return path


# This candidate is deliberately outside the repository.  Explicit roots are
# also retained after a possible later publication; __file__ never selects a
# repository or state tree.
ROOT = _required_canonical_directory_v1("COVAPIE_TEST_REPOSITORY_ROOT")
STATE_ROOT = _required_canonical_directory_v1("COVAPIE_TEST_STATE_ROOT")
CACHE_ROOT = _required_canonical_directory_v1("COVAPIE_TEST_CACHE_ROOT")
assert CACHE_ROOT == STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"


DIRECT_BOUND_SOURCE_IDENTITIES_V1 = (
    (
        PUBLISHED_TRAIN10_BACKWARD_RELATIVE_V1,
        PUBLISHED_TRAIN10_BACKWARD_SIZE_V1,
        PUBLISHED_TRAIN10_BACKWARD_SHA256_V1,
    ),
    (
        PUBLISHED_TRAIN10_FORWARD_RELATIVE_V1,
        PUBLISHED_TRAIN10_FORWARD_SIZE_V1,
        PUBLISHED_TRAIN10_FORWARD_SHA256_V1,
    ),
    (
        PUBLISHED_TRAIN10_ADAPTER_RELATIVE_V1,
        PUBLISHED_TRAIN10_ADAPTER_SIZE_V1,
        PUBLISHED_TRAIN10_ADAPTER_SHA256_V1,
    ),
    (
        PUBLISHED_OLD_SINGLE_STEP_RELATIVE_V1,
        PUBLISHED_OLD_SINGLE_STEP_SIZE_V1,
        PUBLISHED_OLD_SINGLE_STEP_SHA256_V1,
    ),
    (
        PUBLISHED_TRAINING_OWNER_RELATIVE_V1,
        PUBLISHED_TRAINING_OWNER_SIZE_V1,
        PUBLISHED_TRAINING_OWNER_SHA256_V1,
    ),
)


def _sha256_v1(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file_identity_v1(path: Path) -> tuple[int, str, int]:
    metadata = path.lstat()
    assert stat.S_ISREG(metadata.st_mode) and not path.is_symlink(), path
    return metadata.st_size, _sha256_v1(path), stat.S_IMODE(metadata.st_mode)


def _verify_direct_bound_sources_v1() -> tuple[tuple[str, int, str], ...]:
    observed = []
    for relative, expected_size, expected_sha256 in DIRECT_BOUND_SOURCE_IDENTITIES_V1:
        size, sha256, _mode = _safe_file_identity_v1(ROOT / relative)
        assert (size, sha256) == (expected_size, expected_sha256), relative
        observed.append((relative, size, sha256))
    return tuple(observed)


def _load_published_test_module_v1(
    *, relative: str, size: int, sha256: str, module_name: str
) -> ModuleType:
    """Silently load a pinned helper module after sys.modules registration."""

    path = ROOT / relative
    assert _safe_file_identity_v1(path)[:2] == (size, sha256)
    existing = sys.modules.get(module_name)
    if existing is not None:
        assert Path(existing.__file__).resolve(strict=True) == path
        return existing
    specification = importlib.util.spec_from_file_location(module_name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    stdout = io.StringIO()
    stderr = io.StringIO()
    sys.modules[module_name] = module
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    assert stdout.getvalue() == "" and stderr.getvalue() == ""
    assert Path(module.__file__).resolve(strict=True) == path
    return module


def _train10_backward_tools_v1() -> ModuleType:
    module = _load_published_test_module_v1(
        relative=PUBLISHED_TRAIN10_BACKWARD_RELATIVE_V1,
        size=PUBLISHED_TRAIN10_BACKWARD_SIZE_V1,
        sha256=PUBLISHED_TRAIN10_BACKWARD_SHA256_V1,
        module_name="_covapie_published_train10_backward_tools_for_single_step_v1",
    )
    for helper in (
        "_forward_tools_v1",
        "_backward_tools_v1",
        "_semantic_gradient_contract_before_backward_v1",
        "_validate_gradient_records_v1",
        "_assert_model_and_carrier_unchanged_allow_grad_v1",
        "_train10_seed_branch_active_v1",
        "_validate_grad_enabled_forward_output_v1",
        "_BackwardInvocationGuardV1",
        "_merge_secondary_failure_v1",
    ):
        assert hasattr(module, helper), helper
    return module


def _old_single_step_tools_v1() -> ModuleType:
    module = _load_published_test_module_v1(
        relative=PUBLISHED_OLD_SINGLE_STEP_RELATIVE_V1,
        size=PUBLISHED_OLD_SINGLE_STEP_SIZE_V1,
        sha256=PUBLISHED_OLD_SINGLE_STEP_SHA256_V1,
        module_name="_covapie_published_batch001_single_step_tools_for_train10_v1",
    )
    for helper in (
        "_SingleStepBudgetV1",
        "_validate_optimizer_parameter_identity_v1",
        "_validate_installed_adamw_implementation_v1",
        "_parameter_delta_group_stats_v1",
    ):
        assert hasattr(module, helper), helper
    return module


def _evidence_v1(message: str) -> None:
    print(f"COVAPIE_EVIDENCE {message}", flush=True)


@dataclass(frozen=True)
class _ApplicablePrerequisitesV1:
    published_backward_task_id: str
    real_backward_output_id: int
    real_backward_protection_output_id: int
    publication_commit_output_id: int
    installed_non_opt_in_output_id: int
    publication_closure_output_id: int
    train10_real_forward_count: int
    train10_real_backward_count: int
    train10_parameter_update_count: int
    feature_semantics_audit_required_later: bool
    unknown_atom_runtime_enforcement_integrated: bool
    step12d_is_only_smoke_legality_check: bool


PUBLISHED_APPLICABLE_PREREQUISITES_V1 = _ApplicablePrerequisitesV1(
    published_backward_task_id=(
        "validate_covapie_train10_checkpoint_backward_no_update_v1"
    ),
    real_backward_output_id=863,
    real_backward_protection_output_id=865,
    publication_commit_output_id=868,
    installed_non_opt_in_output_id=869,
    publication_closure_output_id=873,
    train10_real_forward_count=1,
    train10_real_backward_count=1,
    train10_parameter_update_count=0,
    feature_semantics_audit_required_later=True,
    unknown_atom_runtime_enforcement_integrated=False,
    step12d_is_only_smoke_legality_check=True,
)


def _require_applicable_prerequisites_v1(
    prerequisites: object,
) -> _ApplicablePrerequisitesV1:
    if prerequisites != PUBLISHED_APPLICABLE_PREREQUISITES_V1:
        raise AssertionError("applicable_train10_single_step_prerequisites_missing")
    assert isinstance(prerequisites, _ApplicablePrerequisitesV1)
    return prerequisites


def _dispatch_real_runner_if_opted_in_v1(
    *,
    environ: Mapping[str, str],
    prerequisites: object,
    runner: Callable[[], object],
) -> tuple[bool, object | None]:
    if environ.get(REAL_SINGLE_STEP_OPT_IN_V1) != "1":
        return False, None
    _require_applicable_prerequisites_v1(prerequisites)
    return True, runner()


class _RealExecutionGuardV1:
    """Phase-bound future-real call budgets plus explicit progress counters."""

    def __init__(self) -> None:
        train10 = _train10_backward_tools_v1()
        old_step = _old_single_step_tools_v1()
        self.phase = "before_real_operations"
        self.backward = train10._BackwardInvocationGuardV1()
        self.step_budget = old_step._SingleStepBudgetV1()
        self.configure_requested_count = 0
        self.configure_returned_count = 0
        self.adamw_init_requested_count = 0
        self.adamw_init_returned_count = 0
        self.expected_optimizer: object | None = None
        self.authorized_parameter_storage_pointers: set[int] = set()
        self.parameter_delta_observed = False
        self.changed_parameter_count: int | None = None
        self.forbidden_calls: list[str] = []

    def reject(self, name: str) -> None:
        self.forbidden_calls.append(name)
        raise AssertionError(f"forbidden operation invoked: {name}")

    def invoke_forward(
        self, data: object, carrier: object, delegate: Callable[[object], object]
    ) -> object:
        if self.phase != "forward" or data is not carrier:
            self.reject("model.forward.unbound_carrier_or_phase")
        if self.backward.forward_requested_count != 0:
            self.reject("model.forward.second_call")
        self.backward.forward_requested_count = 1
        result = delegate(data)
        self.backward.forward_returned_count = 1
        return result

    def invoke_configure(
        self, args: tuple[object, ...], kwargs: Mapping[str, object],
        delegate: Callable[[], object]
    ) -> object:
        if self.phase != "optimizer_construction" or args or kwargs:
            self.reject("configure_optimizers.options_or_phase")
        if self.configure_requested_count != 0:
            self.reject("configure_optimizers.second_call")
        self.configure_requested_count = 1
        result = delegate()
        self.configure_returned_count = 1
        if result is not self.expected_optimizer:
            self.reject("configure_optimizers.returned_unbound_optimizer")
        return result

    def invoke_adamw_init(
        self,
        optimizer: object,
        args: tuple[object, ...],
        kwargs: Mapping[str, object],
        delegate: Callable[[], None],
    ) -> None:
        if self.phase != "optimizer_construction":
            self.reject("AdamW.__init__.wrong_phase")
        if self.adamw_init_requested_count != 0:
            self.reject("AdamW.__init__.second_call")
        self.adamw_init_requested_count = 1
        delegate()
        self.adamw_init_returned_count = 1
        self.expected_optimizer = optimizer

    def invoke_optimizer_step(
        self,
        *,
        optimizer: object,
        closure: object,
        delegate: Callable[[], object],
    ) -> object:
        if self.phase != "optimizer_step":
            self.reject("AdamW.step.wrong_phase")
        if optimizer is not self.expected_optimizer:
            self.reject("AdamW.step.wrong_optimizer")
        if closure is not None:
            self.reject("AdamW.step.closure_forbidden")
        return self.step_budget.run_once(delegate)

    def bind_optimizer_parameter_storage(
        self, optimizer_parameter_groups: Sequence[Mapping[str, object]]
    ) -> None:
        if self.authorized_parameter_storage_pointers:
            self.reject("optimizer_parameter_storage_already_bound")
        parameters = []
        for group in optimizer_parameter_groups:
            values = group.get("params")
            if not isinstance(values, (tuple, list)):
                self.reject("optimizer_parameter_group_invalid_at_bind")
            parameters.extend(values)
        self.authorized_parameter_storage_pointers = {
            value.untyped_storage().data_ptr()
            for value in parameters
            if value.numel()
        }


def _step_progress_summary_v1(guard: _RealExecutionGuardV1) -> dict[str, object]:
    requested = guard.step_budget.request_count
    completed = guard.step_budget.completed_count
    assert requested in (0, 1) and completed in (0, 1) and completed <= requested
    if requested == 0:
        state = "step_not_requested"
        update: object = False
    elif completed == 0:
        state = "step_requested_not_returned_partial_update_unknown"
        update = "unknown"
    elif not guard.parameter_delta_observed:
        state = "step_returned_delta_not_observed"
        update = "unknown"
    else:
        state = "step_returned_parameter_delta_observed"
        assert guard.changed_parameter_count is not None
        update = guard.changed_parameter_count > 0
    return {
        "step_state": state,
        "step_requested": requested,
        "step_completed": completed,
        "parameter_delta_observed": guard.parameter_delta_observed,
        "parameter_update_performed": update,
    }


@dataclass(frozen=True)
class _GradientSnapshotV1:
    name: str
    parameter_object_id: int
    state: str
    gradient_object_id: int | None
    gradient: torch.Tensor | None


def _capture_pre_step_gradients_v1(
    named_parameters: Mapping[str, torch.Tensor],
) -> tuple[_GradientSnapshotV1, ...]:
    snapshots = []
    for name, parameter in named_parameters.items():
        gradient = parameter.grad
        if gradient is None:
            state = "none"
            clone = None
            gradient_id = None
        else:
            assert gradient.shape == parameter.shape, name
            assert gradient.device == parameter.device, name
            assert bool(torch.isfinite(gradient).all().item()), name
            state = (
                "zero" if int(torch.count_nonzero(gradient).item()) == 0
                else "nonzero"
            )
            clone = gradient.detach().clone()
            gradient_id = id(gradient)
        snapshots.append(_GradientSnapshotV1(
            name=name,
            parameter_object_id=id(parameter),
            state=state,
            gradient_object_id=gradient_id,
            gradient=clone,
        ))
    assert snapshots
    return tuple(snapshots)


def _assert_gradients_preserved_after_step_v1(
    *,
    snapshots: Sequence[_GradientSnapshotV1],
    named_parameters: Mapping[str, torch.Tensor],
) -> None:
    assert tuple(item.name for item in snapshots) == tuple(named_parameters)
    for item in snapshots:
        parameter = named_parameters[item.name]
        assert id(parameter) == item.parameter_object_id, item.name
        if item.state == "none":
            assert parameter.grad is None, item.name
        else:
            assert parameter.grad is not None, item.name
            assert id(parameter.grad) == item.gradient_object_id, item.name
            assert torch.equal(parameter.grad, item.gradient), item.name


@dataclass(frozen=True)
class _OptimizerStateSummaryV1:
    expected_state_count: int
    none_gradient_count: int
    zero_gradient_count: int
    nonzero_gradient_count: int


def _validate_optimizer_state_after_one_step_v1(
    *,
    optimizer: object,
    named_parameters: Mapping[str, torch.Tensor],
    pre_step_gradients: Sequence[_GradientSnapshotV1],
) -> _OptimizerStateSummaryV1:
    """Validate state against the independently frozen B-time gradient set."""

    optimizer_identity = _old_single_step_tools_v1()._validate_optimizer_parameter_identity_v1(
        named_parameters=named_parameters,
        optimizer_parameter_groups=optimizer.param_groups,
    )
    assert optimizer_identity.optimizer_parameter_count == len(named_parameters)
    snapshot_by_name = {item.name: item for item in pre_step_gradients}
    assert set(snapshot_by_name) == set(named_parameters)
    parameter_by_id = {id(value): value for value in named_parameters.values()}
    name_by_id = {id(value): name for name, value in named_parameters.items()}
    assert len(parameter_by_id) == len(named_parameters)
    state_ids = {id(value) for value in optimizer.state}
    assert state_ids <= set(parameter_by_id), "optimizer_state_foreign_parameter"
    expected_names = {
        item.name for item in pre_step_gradients if item.state != "none"
    }
    expected_ids = {id(named_parameters[name]) for name in expected_names}
    assert state_ids == expected_ids, "optimizer_state_gradient_membership_mismatch"

    for parameter, state in optimizer.state.items():
        name = name_by_id[id(parameter)]
        assert snapshot_by_name[name].state in ("zero", "nonzero")
        assert set(state) == {"step", "exp_avg", "exp_avg_sq", "max_exp_avg_sq"}, name
        step = state["step"]
        assert isinstance(step, torch.Tensor) and step.ndim == 0, name
        assert step.dtype == torch.float32 and step.device == parameter.device, name
        assert bool(torch.isfinite(step).item()) and float(step.item()) == 1.0, name
        for key in ("exp_avg", "exp_avg_sq", "max_exp_avg_sq"):
            value = state[key]
            assert isinstance(value, torch.Tensor), (name, key)
            assert value.shape == parameter.shape, (name, key)
            assert value.device == parameter.device, (name, key)
            assert value.dtype == parameter.dtype, (name, key)
            assert bool(torch.isfinite(value).all().item()), (name, key)

    none_count = sum(item.state == "none" for item in pre_step_gradients)
    zero_count = sum(item.state == "zero" for item in pre_step_gradients)
    nonzero_count = sum(item.state == "nonzero" for item in pre_step_gradients)
    assert len(optimizer.state) == zero_count + nonzero_count
    return _OptimizerStateSummaryV1(
        expected_state_count=len(optimizer.state),
        none_gradient_count=none_count,
        zero_gradient_count=zero_count,
        nonzero_gradient_count=nonzero_count,
    )


@dataclass(frozen=True)
class _StepBoundarySnapshotV1:
    parameter_values: dict[str, torch.Tensor]
    buffer_values: dict[str, torch.Tensor]
    parameter_object_ids: tuple[tuple[str, int], ...]
    buffer_object_ids: tuple[tuple[str, int], ...]
    state_dict_keys: tuple[str, ...]
    requires_grad_flags: tuple[tuple[str, bool], ...]
    gradients: tuple[_GradientSnapshotV1, ...]
    configuration_fingerprint: str
    carrier_fingerprint: str


def _capture_step_boundary_v1(
    *,
    model: object,
    carrier: object,
    configuration_snapshotter: Callable[[object], object],
    carrier_fingerprinter: Callable[[object], str],
) -> _StepBoundarySnapshotV1:
    named_parameters = dict(model.named_parameters())
    named_buffers = dict(model.named_buffers())
    forward = _train10_backward_tools_v1()._forward_tools_v1()
    return _StepBoundarySnapshotV1(
        parameter_values={
            name: value.detach().clone() for name, value in named_parameters.items()
        },
        buffer_values={
            name: value.detach().clone() for name, value in named_buffers.items()
        },
        parameter_object_ids=tuple(
            (name, id(value)) for name, value in named_parameters.items()
        ),
        buffer_object_ids=tuple(
            (name, id(value)) for name, value in named_buffers.items()
        ),
        state_dict_keys=tuple(model.state_dict()),
        requires_grad_flags=tuple(
            (name, bool(value.requires_grad))
            for name, value in named_parameters.items()
        ),
        gradients=_capture_pre_step_gradients_v1(named_parameters),
        configuration_fingerprint=forward._fingerprint_value_v1(
            configuration_snapshotter(model)
        ),
        carrier_fingerprint=carrier_fingerprinter(carrier),
    )


def _assert_post_step_invariants_v1(
    *,
    snapshot: _StepBoundarySnapshotV1,
    model: object,
    carrier: object,
    frozen_parameter_names: Sequence[str],
    configuration_snapshotter: Callable[[object], object],
    carrier_fingerprinter: Callable[[object], str],
) -> None:
    """Allow parameter deltas only; preserve all B-time protected state."""

    forward = _train10_backward_tools_v1()._forward_tools_v1()
    named_parameters = dict(model.named_parameters())
    named_buffers = dict(model.named_buffers())
    assert tuple((name, id(value)) for name, value in named_parameters.items()) == (
        snapshot.parameter_object_ids
    ), "parameter_identity_changed"
    assert tuple((name, id(value)) for name, value in named_buffers.items()) == (
        snapshot.buffer_object_ids
    ), "buffer_identity_changed"
    assert tuple(model.state_dict()) == snapshot.state_dict_keys, "state_dict_keys_changed"
    assert tuple(
        (name, bool(value.requires_grad)) for name, value in named_parameters.items()
    ) == snapshot.requires_grad_flags, "requires_grad_flags_changed"
    assert forward._fingerprint_value_v1(configuration_snapshotter(model)) == (
        snapshot.configuration_fingerprint
    ), "configuration_or_node_prior_changed"
    assert carrier_fingerprinter(carrier) == snapshot.carrier_fingerprint, "carrier_changed"
    assert set(named_buffers) == set(snapshot.buffer_values)
    for name, value in named_buffers.items():
        assert torch.equal(value, snapshot.buffer_values[name]), name
    assert all(
        bool(torch.isfinite(value).all().item())
        for value in named_parameters.values()
    ), "nonfinite_parameter_after_step"
    _assert_gradients_preserved_after_step_v1(
        snapshots=snapshot.gradients, named_parameters=named_parameters
    )
    frozen = set(frozen_parameter_names)
    assert frozen and frozen <= set(named_parameters)
    gradient_by_name = {item.name: item for item in snapshot.gradients}
    for name in frozen:
        parameter = named_parameters[name]
        assert parameter.requires_grad is False and parameter.grad is None, name
        assert torch.equal(parameter, snapshot.parameter_values[name]), name
    for name, item in gradient_by_name.items():
        if item.state == "none":
            assert torch.equal(
                named_parameters[name], snapshot.parameter_values[name]
            ), name


def _validate_parameter_groups_v1(
    *,
    groups: Sequence[tuple[str, Sequence[str]]],
    named_parameters: Mapping[str, object],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    normalized = tuple((name, tuple(members)) for name, members in groups)
    group_names = tuple(name for name, _members in normalized)
    assert normalized and len(group_names) == len(set(group_names)), "duplicate_delta_group"
    flattened = tuple(name for _group, members in normalized for name in members)
    assert all(members for _group, members in normalized), "empty_delta_group"
    assert len(flattened) == len(set(flattened)), "duplicate_parameter_delta_group"
    assert set(flattened) == set(named_parameters), "parameter_delta_group_coverage"
    return normalized


@dataclass(frozen=True)
class _TotalDeltaObservationV1:
    parameter_count: int
    changed_parameter_count: int
    delta_l2_norm: float
    delta_max_abs: float
    all_finite: bool


def _observe_total_parameter_delta_v1(
    *,
    before: Mapping[str, torch.Tensor],
    named_parameters: Mapping[str, torch.Tensor],
) -> _TotalDeltaObservationV1:
    assert tuple(before) == tuple(named_parameters), "parameter_keys_changed_before_delta"
    deltas = tuple(
        named_parameters[name].detach().double() - before[name].detach().double()
        for name in before
    )
    changed = sum(int(torch.count_nonzero(value).item()) > 0 for value in deltas)
    squared = sum(float(value.square().sum().item()) for value in deltas)
    maximum = max(
        (float(value.abs().max().item()) for value in deltas if value.numel()),
        default=0.0,
    )
    finite = all(bool(torch.isfinite(value).all().item()) for value in deltas)
    finite = finite and all(
        bool(torch.isfinite(value).all().item())
        for value in named_parameters.values()
    )
    return _TotalDeltaObservationV1(
        parameter_count=len(deltas),
        changed_parameter_count=changed,
        delta_l2_norm=math.sqrt(squared),
        delta_max_abs=maximum,
        all_finite=finite,
    )


def _validate_real_optimizer_v1(
    *, model: object, optimizer: object, training_owner: ModuleType
) -> object:
    old_step = _old_single_step_tools_v1()
    assert getattr(type(model), "configure_optimizers") is (
        training_owner.CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    )
    assert type(optimizer) is torch.optim.AdamW
    assert len(optimizer.param_groups) == 1
    identity = old_step._validate_optimizer_parameter_identity_v1(
        named_parameters=dict(model.named_parameters()),
        optimizer_parameter_groups=optimizer.param_groups,
    )
    group = optimizer.param_groups[0]
    assert identity.frozen_parameter_count == 1
    assert group["lr"] == model.lr
    assert group["betas"] == (0.9, 0.999)
    assert group["eps"] == 1.0e-8
    assert group["amsgrad"] is True
    assert group["weight_decay"] == 1.0e-12
    assert group["maximize"] is False
    assert group["foreach"] is None
    assert group["capturable"] is False
    assert group["differentiable"] is False
    assert group["fused"] is None
    assert optimizer.state == {}
    return identity


def _install_real_execution_guards_v1(
    stack: contextlib.ExitStack,
    *,
    model: object,
    carrier: object,
    guard: _RealExecutionGuardV1,
    lightning: ModuleType,
) -> None:
    """Permit one bound AdamW step while protecting buffers and other writes."""

    original_forward = model.forward
    original_configure = model.configure_optimizers
    original_tensor_backward = torch.Tensor.backward
    original_autograd_backward = torch.autograd.backward
    original_adamw_init = torch.optim.AdamW.__init__
    original_adamw_step = torch.optim.AdamW.step

    def forbidden(name: str) -> Callable[..., None]:
        def tripwire(*_args: object, **_kwargs: object) -> None:
            guard.reject(name)
        return tripwire

    def guarded_forward(data: object) -> object:
        return guard.invoke_forward(data, carrier, original_forward)

    def guarded_configure() -> object:
        return guard.invoke_configure((), {}, original_configure)

    def guarded_tensor_backward(
        tensor: object, *args: object, **kwargs: object
    ) -> None:
        if guard.phase != "backward":
            guard.reject("Tensor.backward.wrong_phase")
        guard.backward.invoke_tensor_backward(
            tensor,
            args,
            kwargs,
            lambda bound: original_tensor_backward(bound),
        )

    def guarded_autograd_backward(*args: object, **kwargs: object) -> None:
        if guard.phase != "backward":
            guard.reject("torch.autograd.backward.wrong_phase")
        guard.backward.invoke_internal_autograd_backward(
            args,
            kwargs,
            lambda: original_autograd_backward(*args, **kwargs),
        )

    def guarded_adamw_init(
        optimizer: object, *args: object, **kwargs: object
    ) -> None:
        guard.invoke_adamw_init(
            optimizer,
            args,
            kwargs,
            lambda: original_adamw_init(optimizer, *args, **kwargs),
        )

    def guarded_adamw_step(optimizer: object, closure: object = None) -> object:
        return guard.invoke_optimizer_step(
            optimizer=optimizer,
            closure=closure,
            delegate=lambda: original_adamw_step(optimizer, closure=None),
        )

    for owner, attribute, replacement in (
        (model, "forward", guarded_forward),
        (model, "configure_optimizers", guarded_configure),
        (torch.Tensor, "backward", guarded_tensor_backward),
        (torch.autograd, "backward", guarded_autograd_backward),
        (torch.autograd, "grad", forbidden("torch.autograd.grad")),
        (torch, "load", forbidden("torch.load.after_checkpoint")),
        (torch, "save", forbidden("torch.save")),
        (torch.jit, "load", forbidden("torch.jit.load")),
        (torch.jit, "save", forbidden("torch.jit.save")),
        (torch.optim.AdamW, "__init__", guarded_adamw_init),
        (torch.optim.AdamW, "step", guarded_adamw_step),
        (torch.optim.Optimizer, "step", forbidden("Optimizer.step")),
        (lightning.Trainer, "__init__", forbidden("Trainer.__init__")),
        (lightning.Trainer, "fit", forbidden("Trainer.fit")),
        (lightning.Trainer, "validate", forbidden("Trainer.validate")),
        (lightning.Trainer, "test", forbidden("Trainer.test")),
        (lightning.Trainer, "predict", forbidden("Trainer.predict")),
        (lightning.Trainer, "save_checkpoint", forbidden("Trainer.save_checkpoint")),
        (
            lightning.LightningModule,
            "load_from_checkpoint",
            forbidden("LightningModule.load_from_checkpoint"),
        ),
    ):
        stack.enter_context(mock.patch.object(owner, attribute, new=replacement))

    for attribute in ("training_step", "validation_step", "test_step", "load_state_dict"):
        stack.enter_context(mock.patch.object(
            model, attribute, new=forbidden(f"model.{attribute}")
        ))

    optimizer_classes = {
        value
        for value in vars(torch.optim).values()
        if isinstance(value, type)
        and issubclass(value, torch.optim.Optimizer)
        and value not in (torch.optim.Optimizer, torch.optim.AdamW)
    }
    for optimizer_class in optimizer_classes:
        if "__init__" in optimizer_class.__dict__:
            stack.enter_context(mock.patch.object(
                optimizer_class,
                "__init__",
                new=forbidden(f"{optimizer_class.__name__}.__init__"),
            ))
        if "step" in optimizer_class.__dict__:
            stack.enter_context(mock.patch.object(
                optimizer_class,
                "step",
                new=forbidden(f"{optimizer_class.__name__}.step"),
            ))

    parameter_pointers = {
        value.untyped_storage().data_ptr()
        for value in model.parameters()
        if value.numel()
    }
    buffer_pointers = {
        value.untyped_storage().data_ptr()
        for value in model.buffers()
        if value.numel()
    }
    assert not (parameter_pointers & buffer_pointers)

    def protect_inplace(name: str, original: Callable[..., object]):
        def guarded(tensor: torch.Tensor, *args: object, **kwargs: object) -> object:
            pointer = tensor.untyped_storage().data_ptr() if tensor.numel() else None
            if pointer in buffer_pointers:
                guard.reject(f"model_buffer_write.{name}")
            if pointer in parameter_pointers:
                allowed = (
                    guard.phase == "optimizer_step"
                    and guard.step_budget.in_progress
                    and pointer in guard.authorized_parameter_storage_pointers
                )
                if not allowed:
                    guard.reject(f"model_parameter_write.{name}")
            return original(tensor, *args, **kwargs)
        return guarded

    for attribute in (
        "copy_", "set_", "add_", "sub_", "mul_", "div_", "zero_",
        "fill_", "index_copy_", "scatter_", "__setitem__",
    ):
        original = getattr(torch.Tensor, attribute)
        stack.enter_context(mock.patch.object(
            torch.Tensor, attribute, new=protect_inplace(attribute, original)
        ))


def _report_real_failure_v1(
    *, primary: BaseException, phase: str, guard: _RealExecutionGuardV1,
    operation_counts: Mapping[str, Mapping[str, int]]
) -> None:
    payload = {
        "phase": phase,
        "error_type": type(primary).__name__,
        "error_message": str(primary),
        "operation_counts": operation_counts,
        "forward_requested": guard.backward.forward_requested_count,
        "forward_returned": guard.backward.forward_returned_count,
        "backward_requested": guard.backward.top_level_backward_requested_count,
        "backward_returned": guard.backward.top_level_backward_returned_count,
        "internal_backward_requested": guard.backward.internal_autograd_requested_count,
        "internal_backward_returned": guard.backward.internal_autograd_returned_count,
        "configure_requested": guard.configure_requested_count,
        "configure_returned": guard.configure_returned_count,
        "adamw_init_requested": guard.adamw_init_requested_count,
        "adamw_init_returned": guard.adamw_init_returned_count,
        **_step_progress_summary_v1(guard),
    }
    _evidence_v1("REAL_TRAIN10_SINGLE_OPTIMIZER_STEP=FAIL " + json.dumps(
        payload, sort_keys=True
    ))


def _run_real_checkpoint_single_optimizer_step_v1() -> None:
    """Future-authorized one-model/one-batch/one-step CPU path."""

    import pytorch_lightning as lightning

    phase = "dependency_import"
    primary: BaseException | None = None
    primary_traceback = None
    runtime_stack = contextlib.ExitStack()
    rng_before = torch.random.get_rng_state().clone()
    guard = _RealExecutionGuardV1()
    operation_counts = {
        name: {"requested": 0, "returned": 0}
        for name in (
            "checkpoint_load", "model_construction", "migration",
            "composer_prepare", "carrier_build", "production_loss",
        )
    }
    summary: dict[str, object] = {}
    try:
        train10 = _train10_backward_tools_v1()
        forward = train10._forward_tools_v1()
        backward = train10._backward_tools_v1()
        dependencies = forward._load_real_path_dependencies_v1()
        adapter = dependencies["adapter"]
        checkpoint_locator = dependencies["checkpoint_locator"]
        compatible_owner = dependencies["compatible_owner"]
        migration_owner = dependencies["migration_owner"]
        training_owner = dependencies["training_owner"]
        tensorizer_owner = dependencies["tensorizer_owner"]
        composer_owner = dependencies["composer_owner"]

        phase = "fixed_sources_feature_semantics_and_optimizer_owner"
        candidate_identity = _safe_file_identity_v1(Path(__file__).resolve(strict=True))
        direct_sources_before = _verify_direct_bound_sources_v1()
        forward_sources_before = forward._verify_bound_sources_v1()
        adapter_sources_before = (
            adapter.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(
                repository_root=ROOT
            )
        )
        forward._assert_scoped_feature_use_prerequisites_v1()
        adamw_contract = _old_single_step_tools_v1()._validate_installed_adamw_implementation_v1(
            torch
        )
        assert adamw_contract.torch_version == EXPECTED_TORCH_VERSION_V1
        assert getattr(
            adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1,
            "configure_optimizers",
        ) is training_owner.CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers

        phase = "checkpoint_identity_and_load"
        assert checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1 == compatible_owner.CHECKPOINT_PATH
        checkpoint_path = ROOT / checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1
        checkpoint_identity = forward._safe_file_identity_v1(checkpoint_path)
        assert checkpoint_identity == (
            EXPECTED_CHECKPOINT_SIZE_BYTES_V1,
            EXPECTED_CHECKPOINT_SHA256_V1,
        )
        operation_counts["checkpoint_load"]["requested"] = 1
        checkpoint = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=checkpoint_path
        )
        operation_counts["checkpoint_load"]["returned"] = 1
        checkpoint_state = checkpoint["state_dict"]

        phase = "model_construction_and_strict_migration"
        runtime_root = Path(tempfile.mkdtemp(
            prefix=TASK_ID_V1 + "-", dir=STATE_ROOT / "review-scratch"
        ))
        operation_counts["model_construction"]["requested"] = 1
        model = forward._instantiate_train10_model_v1(
            checkpoint=checkpoint, runtime_root=runtime_root
        )
        operation_counts["model_construction"]["returned"] = 1
        operation_counts["migration"]["requested"] = 1
        migration = migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
            model=model, checkpoint_state_dict=checkpoint_state
        )
        operation_counts["migration"]["returned"] = 1
        assert migration["full_target_strict_load"] is True
        assert migration["checkpoint_only_key_count"] == 0
        assert migration["shared_shape_mismatch_count"] == 0
        assert migration["migration_missing_keys"] == ()
        assert migration["migration_unexpected_keys"] == ()
        model.train()
        assert model.training is True and model.ddpm.training is True
        assert model.batch_size == 10
        assert model.pocket_representation == "full-atom"
        assert model.virtual_nodes is False
        assert model.ddpm.T == 500
        assert model.ddpm.dynamics.target_residue_atom_conditioning is True
        assert model._trainer is None

        phase = "single_epoch0_seed0_carrier"
        operation_counts["composer_prepare"]["requested"] = 1
        prepared = composer_owner.prepare_covapie_train10_cpu_batch_composer_v1(
            ROOT, STATE_ROOT, CACHE_ROOT
        )
        operation_counts["composer_prepare"]["returned"] = 1
        operation_counts["carrier_build"]["requested"] = 1
        carrier = composer_owner.build_covapie_train10_cpu_epoch_batch_v1(
            prepared, 0, 0
        )
        operation_counts["carrier_build"]["returned"] = 1
        carrier_measurements = forward._assert_train10_carrier_contract_v1(carrier)
        assert carrier_measurements["tasks"] == EXPECTED_EPOCH0_TASK_IDS_V1
        carrier_fingerprint = forward._fingerprint_value_v1(carrier)

        phase = "a_snapshot_and_pre_backward_semantics"
        snapshot_a = forward._capture_model_snapshot_v1(model)
        buffer_identity_a = tuple(
            (name, id(value)) for name, value in model.named_buffers()
        )
        named_parameters = dict(model.named_parameters())
        weights = model.covapie_current11_loss_weights
        actual_weights = {
            field.name: getattr(weights, field.name) for field in fields(weights)
        }
        assert actual_weights == {
            "base_diffusion": 1.0,
            "covalent_pair_prediction": 1.0,
            "pre_post_geometry": 0.0,
            "covalent_pair_contrastive": 0.1,
        }
        seed_branch_active = train10._train10_seed_branch_active_v1(carrier)
        semantics = train10._semantic_gradient_contract_before_backward_v1(
            named_parameters=named_parameters,
            checkpoint_parameter_names=tuple(checkpoint_state),
            seed_branch_active=seed_branch_active,
            geometry_weight=actual_weights["pre_post_geometry"],
        )
        assert semantics.seed_branch_active is True

        phase = "guard_installation"
        _install_real_execution_guards_v1(
            runtime_stack,
            model=model,
            carrier=carrier,
            guard=guard,
            lightning=lightning,
        )

        phase = "optimizer_construction"
        guard.phase = phase
        optimizer = model.configure_optimizers()
        optimizer_identity = _validate_real_optimizer_v1(
            model=model, optimizer=optimizer, training_owner=training_owner
        )
        guard.bind_optimizer_parameter_storage(optimizer.param_groups)
        assert guard.configure_requested_count == guard.configure_returned_count == 1
        assert guard.adamw_init_requested_count == guard.adamw_init_returned_count == 1
        forward._assert_model_snapshot_unchanged_v1(snapshot_a, model)
        assert tuple((name, id(value)) for name, value in model.named_buffers()) == buffer_identity_a
        assert forward._fingerprint_value_v1(carrier) == carrier_fingerprint
        _evidence_v1(
            "A_OPTIMIZER_CONSTRUCTION=PASS owner=current11 AdamW=true "
            f"parameters={optimizer_identity.optimizer_parameter_count} "
            f"frozen={optimizer_identity.frozen_parameter_count} lr={model.lr!r} "
            f"state_entries=0 torch={adamw_contract.torch_version} "
            f"adamw_source_observed_sha256={adamw_contract.source_sha256}"
        )

        transport: dict[str, object] = {"requested": 0, "returned": 0}
        original_transport = model.get_ligand_and_pocket

        def observed_transport(data: object) -> object:
            assert data is carrier.model_input_batch
            transport["requested"] = int(transport["requested"]) + 1
            assert transport["requested"] == 1
            result = original_transport(data)
            transport["value"] = forward._clone_transport_v1(result)
            transport["returned"] = int(transport["returned"]) + 1
            return result

        runtime_stack.enter_context(mock.patch.object(
            model, "get_ligand_and_pocket", new=observed_transport
        ))
        original_loss = adapter.compute_covapie_current11_training_losses_v1

        def observed_production_loss(*args: object, **kwargs: object) -> object:
            counts = operation_counts["production_loss"]
            counts["requested"] += 1
            assert counts["requested"] == 1
            result = original_loss(*args, **kwargs)
            counts["returned"] += 1
            return result

        runtime_stack.enter_context(mock.patch.object(
            adapter,
            "compute_covapie_current11_training_losses_v1",
            new=observed_production_loss,
        ))

        def forbidden_tensorization(*_args: object, **_kwargs: object) -> None:
            guard.reject("secondary_tensorization")

        runtime_stack.enter_context(mock.patch.object(
            tensorizer_owner,
            "tensorize_covapie_current11_training_supervision_v1",
            new=forbidden_tensorization,
        ))
        runtime_stack.enter_context(mock.patch.object(
            training_owner,
            "tensorize_covapie_current11_training_supervision_v1",
            new=forbidden_tensorization,
        ))

        phase = "single_grad_enabled_forward"
        guard.phase = "forward"
        torch.manual_seed(DIFFUSION_FORWARD_SEED_V1)
        assert torch.is_grad_enabled() is True
        assert torch.is_inference_mode_enabled() is False
        output = model(carrier)
        measurements = train10._validate_grad_enabled_forward_output_v1(
            output=output, carrier=carrier, model=model
        )
        assert operation_counts["production_loss"] == {"requested": 1, "returned": 1}
        assert guard.backward.forward_requested_count == 1
        assert guard.backward.forward_returned_count == 1
        assert optimizer.state == {}
        _old_single_step_tools_v1()._validate_optimizer_parameter_identity_v1(
            named_parameters=dict(model.named_parameters()),
            optimizer_parameter_groups=optimizer.param_groups,
        )

        phase = "a_to_f_invariance_and_coordinate_oracle"
        guard.phase = phase
        forward._assert_model_snapshot_unchanged_v1(snapshot_a, model)
        assert tuple((name, id(value)) for name, value in model.named_buffers()) == buffer_identity_a
        assert forward._fingerprint_value_v1(carrier) == carrier_fingerprint
        assert transport["requested"] == transport["returned"] == 1
        with torch.no_grad():
            forward._assert_train10_centering_and_fixed_node_contract_v1(
                model=model,
                carrier=carrier,
                transported=transport["value"],
                output=output,
            )
        _evidence_v1(
            "A_TO_F=PASS parameters=true buffers=true identity=true keys=true "
            "requires_grad=true configuration_and_node_prior=true carrier=true "
            "gradients_none=true optimizer_state_empty=true coordinate_oracle=true"
        )

        phase = "single_total_loss_backward"
        guard.phase = "backward"
        loss_total = measurements["loss_total"]
        assert loss_total is output.loss_output.loss_total
        guard.backward.expected_loss = loss_total
        loss_total.backward()
        assert guard.backward.top_level_backward_requested_count == 1
        assert guard.backward.top_level_backward_returned_count == 1
        assert guard.backward.internal_autograd_requested_count == 1
        assert guard.backward.internal_autograd_returned_count == 1

        phase = "a_to_b_invariance_gradient_classification"
        guard.phase = phase
        train10._assert_model_and_carrier_unchanged_allow_grad_v1(
            snapshot=snapshot_a,
            model=model,
            carrier_fingerprint=carrier_fingerprint,
            carrier=carrier,
        )
        assert tuple((name, id(value)) for name, value in model.named_buffers()) == buffer_identity_a
        named_parameters = dict(model.named_parameters())
        records = backward._parameter_gradient_metadata_v1(named_parameters)
        classification = train10._validate_gradient_records_v1(
            records=records, semantics=semantics
        )
        assert classification.frozen_parameter_names == ("ddpm.gamma.gamma",)
        assert optimizer.state == {}
        _old_single_step_tools_v1()._validate_optimizer_parameter_identity_v1(
            named_parameters=named_parameters,
            optimizer_parameter_groups=optimizer.param_groups,
        )
        snapshot_b = _capture_step_boundary_v1(
            model=model,
            carrier=carrier,
            configuration_snapshotter=forward._model_configuration_snapshot_v1,
            carrier_fingerprinter=forward._fingerprint_value_v1,
        )
        groups = _validate_parameter_groups_v1(
            groups=semantics.groups, named_parameters=named_parameters
        )
        gradient_stats = {}
        for group_name, parameter_names in groups:
            item = backward._gradient_group_stats(
                group_name=group_name,
                named_parameters=named_parameters,
                parameter_names=parameter_names,
            )
            backward._emit_gradient_stats(item)
            assert item.all_produced_gradients_finite
            gradient_stats[group_name] = item
        assert gradient_stats["geometry_head"].grad_nonzero_count == 0
        _evidence_v1(
            "A_TO_B=PASS parameters=true buffers=true identity=true keys=true "
            "requires_grad=true configuration_and_node_prior=true carrier=true "
            "gradients_finite=true gradients_frozen_before_observation=true "
            "optimizer_state_empty=true"
        )

        phase = "single_optimizer_step"
        guard.phase = "optimizer_step"
        optimizer.step()
        # Record the returned-step fact and compact actual delta before any
        # complex state/group summary can fail.
        named_parameters = dict(model.named_parameters())
        total_delta = _observe_total_parameter_delta_v1(
            before=snapshot_b.parameter_values,
            named_parameters=named_parameters,
        )
        guard.parameter_delta_observed = True
        guard.changed_parameter_count = total_delta.changed_parameter_count
        _evidence_v1(
            "STEP_RETURNED_DELTA_OBSERVED "
            f"requested={guard.step_budget.request_count} "
            f"completed={guard.step_budget.completed_count} "
            f"changed_parameters={total_delta.changed_parameter_count} "
            f"parameter_count={total_delta.parameter_count} "
            f"delta_l2={total_delta.delta_l2_norm:.17g} "
            f"delta_max_abs={total_delta.delta_max_abs:.17g} "
            f"all_finite={str(total_delta.all_finite).lower()}"
        )

        phase = "b_to_c_post_step_validation"
        guard.phase = phase
        assert guard.step_budget.request_count == guard.step_budget.completed_count == 1
        assert total_delta.all_finite and total_delta.changed_parameter_count > 0
        _assert_post_step_invariants_v1(
            snapshot=snapshot_b,
            model=model,
            carrier=carrier,
            frozen_parameter_names=semantics.frozen_parameter_names,
            configuration_snapshotter=forward._model_configuration_snapshot_v1,
            carrier_fingerprinter=forward._fingerprint_value_v1,
        )
        state_summary = _validate_optimizer_state_after_one_step_v1(
            optimizer=optimizer,
            named_parameters=named_parameters,
            pre_step_gradients=snapshot_b.gradients,
        )
        delta_stats = tuple(
            _old_single_step_tools_v1()._parameter_delta_group_stats_v1(
                group_name=group_name,
                parameter_names=parameter_names,
                before=snapshot_b.parameter_values,
                named_parameters=named_parameters,
            )
            for group_name, parameter_names in groups
        )
        stats_by_name = {item.group_name: item for item in delta_stats}
        for item in delta_stats:
            assert item.all_parameters_finite
            assert math.isfinite(item.delta_l2_norm)
            assert math.isfinite(item.delta_max_abs)
            _evidence_v1(
                f"parameter_delta_group={item.group_name} "
                f"parameter_tensors={item.parameter_tensor_count} "
                f"changed={item.changed_parameter_tensor_count} "
                f"unchanged={item.unchanged_parameter_tensor_count} "
                f"l2_norm={item.delta_l2_norm:.17g} "
                f"max_abs={item.delta_max_abs:.17g}"
            )
        for group_name in (
            "legacy_ddpm_egnn",
            "target_residue_conditioning",
            "role_task_generation_seed_anchor_encoding",
            "pair_embedding_logit",
        ):
            assert stats_by_name[group_name].changed_parameter_tensor_count > 0
        assert guard.forbidden_calls == [] and guard.backward.forbidden_calls == []
        _evidence_v1(
            "B_TO_C=PASS buffers=true identity=true keys=true requires_grad=true "
            "configuration_and_node_prior=true carrier=true frozen_gamma=true "
            "grad_none_parameters_unchanged=true gradients_preserved=true "
            f"state_entries={state_summary.expected_state_count} "
            f"grad_none={state_summary.none_gradient_count} "
            f"grad_zero={state_summary.zero_gradient_count} "
            f"grad_nonzero={state_summary.nonzero_gradient_count}"
        )

        phase = "final_integrity"
        guard.phase = phase
        assert _verify_direct_bound_sources_v1() == direct_sources_before
        assert forward._verify_bound_sources_v1() == forward_sources_before
        assert adapter.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(
            repository_root=ROOT
        ) == adapter_sources_before
        assert _safe_file_identity_v1(Path(__file__).resolve(strict=True)) == candidate_identity
        assert forward._safe_file_identity_v1(checkpoint_path) == checkpoint_identity
        summary = {
            "runtime": str(runtime_root),
            "tasks": carrier_measurements["tasks"],
            "timesteps": measurements["timesteps"],
            "raw_losses": measurements["raw_losses"],
            "weights": actual_weights,
            "model_lr": float(model.lr),
            "optimizer_group_lr": float(optimizer.param_groups[0]["lr"]),
            "operation_counts": operation_counts,
            "forward_requested": guard.backward.forward_requested_count,
            "forward_returned": guard.backward.forward_returned_count,
            "backward_requested": guard.backward.top_level_backward_requested_count,
            "backward_returned": guard.backward.top_level_backward_returned_count,
            "internal_backward_requested": guard.backward.internal_autograd_requested_count,
            "internal_backward_returned": guard.backward.internal_autograd_returned_count,
            "optimizer_configure_requested": guard.configure_requested_count,
            "optimizer_configure_returned": guard.configure_returned_count,
            "optimizer_step_requested": guard.step_budget.request_count,
            "optimizer_step_completed": guard.step_budget.completed_count,
            "changed_parameter_count": total_delta.changed_parameter_count,
            "state_summary": state_summary.__dict__,
            "geometry": {
                "weight": actual_weights["pre_post_geometry"],
                "raw_loss": measurements["raw_losses"]["geometry"],
                "gradient_nonzero_count": gradient_stats["geometry_head"].grad_nonzero_count,
                "gradient_zero_count": gradient_stats["geometry_head"].grad_all_zero_count,
                "optimizer_state_entry_count": sum(
                    item.state != "none"
                    for item in snapshot_b.gradients
                    if item.name in dict(groups)["geometry_head"]
                ),
                "delta_changed_count": stats_by_name["geometry_head"].changed_parameter_tensor_count,
                "training_gradient_accepted": False,
            },
            "post_step_forward": False,
            "trainer": False,
            "checkpoint_saved": False,
            "training_ready": False,
        }
    except BaseException as error:
        primary = error
        primary_traceback = error.__traceback__

    merge = _train10_backward_tools_v1()._merge_secondary_failure_v1
    primary = merge(
        primary, phase="observer_and_guard_cleanup", callback=runtime_stack.close
    )
    primary = merge(
        primary,
        phase="caller_rng_restore",
        callback=lambda: torch.random.set_rng_state(rng_before),
    )
    if primary is not None:
        primary = merge(
            primary,
            phase="primary_failure_reporting",
            callback=lambda: _report_real_failure_v1(
                primary=primary,
                phase=phase,
                guard=guard,
                operation_counts=operation_counts,
            ),
        )
        raise primary.with_traceback(primary_traceback)
    _evidence_v1(
        "REAL_TRAIN10_SINGLE_OPTIMIZER_STEP=PASS "
        + json.dumps(summary, sort_keys=True)
    )


def _execute_real_path_if_enabled_v1() -> None:
    if os.environ.get(REAL_SINGLE_STEP_OPT_IN_V1) != "1":
        pytest.skip(
            f"set {REAL_SINGLE_STEP_OPT_IN_V1}=1 only after separate explicit "
            "parameter-update authorization"
        )
    _evidence_v1(
        "real_opt_in=1 checkpoint_load_budget=1 model_budget=1 migration_budget=1 "
        "carrier_budget=1 configure_optimizers_budget=1 optimizer_budget=1 "
        "forward_budget=1 total_backward_budget=1 optimizer_step_budget=1 "
        "post_step_forward_budget=0 trainer_budget=0 checkpoint_save_budget=0"
    )
    _require_applicable_prerequisites_v1(PUBLISHED_APPLICABLE_PREREQUISITES_V1)
    _run_real_checkpoint_single_optimizer_step_v1()


@pytest.fixture(autouse=True)
def _non_model_execution_tripwires_v1(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Iterator[list[str]]:
    """Fail closed before every real operation in ordinary nodes."""

    calls: list[str] = []
    if (
        request.node.name == "test_real_checkpoint_train10_single_optimizer_step"
        and os.environ.get(REAL_SINGLE_STEP_OPT_IN_V1) == "1"
    ):
        yield calls
        return

    import pytorch_lightning as lightning

    forward = _train10_backward_tools_v1()._forward_tools_v1()
    dependencies = forward._load_real_path_dependencies_v1()
    adapter = dependencies["adapter"]
    composer = dependencies["composer_owner"]
    training_owner = dependencies["training_owner"]

    def forbidden(name: str) -> Callable[..., None]:
        def tripwire(*_args: object, **_kwargs: object) -> None:
            calls.append(name)
            raise AssertionError(f"non-model node crossed boundary: {name}")
        return tripwire

    for owner, attribute, name in (
        (torch, "load", "torch.load"),
        (torch, "save", "torch.save"),
        (torch.Tensor, "backward", "Tensor.backward"),
        (torch.autograd, "backward", "torch.autograd.backward"),
        (torch.autograd, "grad", "torch.autograd.grad"),
        (torch.optim.Optimizer, "__init__", "Optimizer.__init__"),
        (torch.optim.Optimizer, "step", "Optimizer.step"),
        (torch.optim.AdamW, "__init__", "AdamW.__init__"),
        (torch.optim.AdamW, "step", "AdamW.step"),
        (lightning.Trainer, "__init__", "Trainer.__init__"),
        (lightning.Trainer, "fit", "Trainer.fit"),
        (
            adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1,
            "__init__",
            "train10_model.__init__",
        ),
        (
            adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1,
            "forward",
            "train10_model.forward",
        ),
        (
            training_owner.CovapieCurrent11TrainingLigandPocketDDPM,
            "configure_optimizers",
            "production_configure_optimizers",
        ),
        (
            adapter,
            "compute_covapie_current11_training_losses_v1",
            "production_loss",
        ),
        (
            composer,
            "prepare_covapie_train10_cpu_batch_composer_v1",
            "composer_prepare",
        ),
        (
            composer,
            "build_covapie_train10_cpu_epoch_batch_v1",
            "carrier_build",
        ),
    ):
        monkeypatch.setattr(owner, attribute, forbidden(name))
    monkeypatch.setattr(tempfile, "mkdtemp", forbidden("model_runtime_mkdtemp"))
    yield calls
    assert calls == []


def test_published_helpers_static_feature_semantics_and_optimizer_owner() -> None:
    assert len(_verify_direct_bound_sources_v1()) == 5
    train10 = _train10_backward_tools_v1()
    forward = train10._forward_tools_v1()
    old_step = _old_single_step_tools_v1()
    assert forward._verify_bound_sources_v1()
    forward._assert_scoped_feature_use_prerequisites_v1()
    assert forward.CANONICAL_EXACT5_V1 == CANONICAL_EXACT5_V1
    assert train10.EXPECTED_EPOCH0_TASK_IDS_V1 == EXPECTED_EPOCH0_TASK_IDS_V1
    assert train10.MODEL_INITIALIZATION_SEED_V1 == MODEL_INITIALIZATION_SEED_V1
    assert train10.DIFFUSION_FORWARD_SEED_V1 == DIFFUSION_FORWARD_SEED_V1

    dependencies = forward._load_real_path_dependencies_v1()
    adapter = dependencies["adapter"]
    training_owner = dependencies["training_owner"]
    adapter_class = adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1
    owner_class = training_owner.CovapieCurrent11TrainingLigandPocketDDPM
    assert adapter_class.__bases__ == (owner_class,)
    assert "configure_optimizers" not in adapter_class.__dict__
    assert getattr(adapter_class, "configure_optimizers") is owner_class.configure_optimizers
    # The autouse non-model guard deliberately replaces the live method before
    # this test runs.  Bind the production implementation through the pinned
    # source AST rather than inspecting that temporary tripwire.
    training_source = (ROOT / PUBLISHED_TRAINING_OWNER_RELATIVE_V1).read_text(
        encoding="utf-8"
    )
    training_tree = ast.parse(training_source)
    owner_nodes = [
        node
        for node in training_tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CovapieCurrent11TrainingLigandPocketDDPM"
    ]
    assert len(owner_nodes) == 1
    configure_nodes = [
        node
        for node in owner_nodes[0].body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "configure_optimizers"
    ]
    assert len(configure_nodes) == 1
    owner_source = ast.get_source_segment(training_source, configure_nodes[0])
    assert owner_source is not None
    assert "list(self.ddpm.parameters())" in owner_source
    assert "list(self.covapie_current11_auxiliary_model_v1.parameters())" in owner_source
    assert "torch.optim.AdamW(" in owner_source
    assert "lr=self.lr" in owner_source
    assert "amsgrad=True" in owner_source
    assert "weight_decay=1e-12" in owner_source
    # Read the installed owner file directly because its live methods are also
    # protected by the ordinary-node tripwire.  The future real runner calls
    # the published helper before installing that guard.
    from torch.optim import adamw as adamw_owner

    assert torch.__version__ == EXPECTED_TORCH_VERSION_V1
    adamw_source_path = Path(adamw_owner.__file__).resolve(strict=True)
    adamw_source = adamw_source_path.read_text(encoding="utf-8")
    assert "if p.grad is None:" in adamw_source
    assert "params_with_grad.append(p)" in adamw_source
    assert "param.mul_(1 - lr * weight_decay)" in adamw_source
    assert "torch._foreach_mul_(device_params, 1 - lr * weight_decay)" in adamw_source

    real_tree = ast.parse(inspect.getsource(_run_real_checkpoint_single_optimizer_step_v1))
    backward_calls = [
        node for node in ast.walk(real_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "backward"
    ]
    step_calls = [
        node for node in ast.walk(real_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "step"
    ]
    configure_calls = [
        node for node in ast.walk(real_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "configure_optimizers"
    ]
    assert len(backward_calls) == len(step_calls) == len(configure_calls) == 1
    assert isinstance(backward_calls[0].func.value, ast.Name)
    assert backward_calls[0].func.value.id == "loss_total"
    assert backward_calls[0].args == [] and backward_calls[0].keywords == []
    assert isinstance(step_calls[0].func.value, ast.Name)
    assert step_calls[0].func.value.id == "optimizer"
    assert step_calls[0].args == [] and step_calls[0].keywords == []
    prohibited_calls = {
        node.func.attr for node in ast.walk(real_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"zero_grad", "training_step", "fit", "save_checkpoint"}
    }
    assert prohibited_calls == set()


def test_default_gate_and_prerequisites_precede_real_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched = []

    def forbidden_real_runner() -> None:
        touched.append("real_runner")
        raise AssertionError("default-disabled runner reached")

    monkeypatch.delenv(REAL_SINGLE_STEP_OPT_IN_V1, raising=False)
    monkeypatch.setattr(
        sys.modules[__name__],
        "_run_real_checkpoint_single_optimizer_step_v1",
        forbidden_real_runner,
    )
    with pytest.raises(pytest.skip.Exception, match=REAL_SINGLE_STEP_OPT_IN_V1):
        _execute_real_path_if_enabled_v1()
    assert touched == []

    incomplete = _ApplicablePrerequisitesV1(
        **dict(
            PUBLISHED_APPLICABLE_PREREQUISITES_V1.__dict__,
            publication_closure_output_id=0,
        )
    )
    with pytest.raises(
        AssertionError,
        match="applicable_train10_single_step_prerequisites_missing",
    ):
        _dispatch_real_runner_if_opted_in_v1(
            environ={REAL_SINGLE_STEP_OPT_IN_V1: "1"},
            prerequisites=incomplete,
            runner=forbidden_real_runner,
        )
    assert touched == []


class _IdentityParameterV1:
    def __init__(self, *, requires_grad: bool, value: float) -> None:
        self.requires_grad = requires_grad
        self.value = value


def test_optimizer_parameter_identity_complete_and_fail_closed() -> None:
    validator = _old_single_step_tools_v1()._validate_optimizer_parameter_identity_v1
    frozen = _IdentityParameterV1(requires_grad=False, value=1.0)
    zero = _IdentityParameterV1(requires_grad=True, value=2.0)
    active = _IdentityParameterV1(requires_grad=True, value=3.0)
    named = {"frozen": frozen, "zero": zero, "active": active}
    accepted = validator(
        named_parameters=named,
        optimizer_parameter_groups=({"params": [frozen, zero, active]},),
    )
    assert accepted.model_parameter_count == accepted.optimizer_parameter_count == 3
    assert accepted.frozen_parameter_count == 1
    cases = (
        [frozen, active],
        [frozen, zero, active, active],
        [frozen, zero, _IdentityParameterV1(requires_grad=True, value=3.0)],
        [frozen, zero, _IdentityParameterV1(requires_grad=True, value=active.value)],
    )
    for parameters in cases:
        with pytest.raises(AssertionError, match="optimizer_parameter_identity"):
            validator(
                named_parameters=named,
                optimizer_parameter_groups=({"params": parameters},),
            )


def test_single_step_budget_phase_object_closure_recursion_and_failure() -> None:
    optimizer = object()
    guard = _RealExecutionGuardV1()
    guard.expected_optimizer = optimizer
    with pytest.raises(AssertionError, match="wrong_phase"):
        guard.invoke_optimizer_step(
            optimizer=optimizer, closure=None, delegate=lambda: None
        )
    assert guard.step_budget.request_count == 0
    guard.phase = "optimizer_step"
    with pytest.raises(AssertionError, match="wrong_optimizer"):
        guard.invoke_optimizer_step(
            optimizer=object(), closure=None, delegate=lambda: None
        )
    with pytest.raises(AssertionError, match="closure_forbidden"):
        guard.invoke_optimizer_step(
            optimizer=optimizer, closure=lambda: None, delegate=lambda: None
        )
    assert guard.step_budget.request_count == 0

    def recursive() -> None:
        guard.invoke_optimizer_step(
            optimizer=optimizer, closure=None, delegate=lambda: None
        )

    with pytest.raises(AssertionError, match="duplicate_optimizer_step_request"):
        guard.invoke_optimizer_step(
            optimizer=optimizer, closure=None, delegate=recursive
        )
    assert guard.step_budget.request_count == 1
    assert guard.step_budget.completed_count == 0
    assert _step_progress_summary_v1(guard)["parameter_update_performed"] == "unknown"
    with pytest.raises(AssertionError, match="duplicate_optimizer_step_request"):
        guard.invoke_optimizer_step(
            optimizer=optimizer, closure=None, delegate=lambda: None
        )


def test_single_backward_top_level_and_internal_delegation_stub_counts() -> None:
    guard = _train10_backward_tools_v1()._BackwardInvocationGuardV1()
    loss = object()
    guard.expected_loss = loss

    def top_delegate(_loss: object) -> None:
        guard.invoke_internal_autograd_backward((), {}, lambda: None)

    guard.invoke_tensor_backward(loss, (), {}, top_delegate)
    assert guard.top_level_backward_requested_count == 1
    assert guard.top_level_backward_returned_count == 1
    assert guard.internal_autograd_requested_count == 1
    assert guard.internal_autograd_returned_count == 1
    with pytest.raises(AssertionError, match="second_top_level_call"):
        guard.invoke_tensor_backward(loss, (), {}, top_delegate)
    wrong = _train10_backward_tools_v1()._BackwardInvocationGuardV1()
    wrong.expected_loss = loss
    with pytest.raises(AssertionError, match="unbound_loss"):
        wrong.invoke_tensor_backward(object(), (), {}, lambda _loss: None)
    with pytest.raises(AssertionError, match="nondefault_options"):
        wrong.invoke_tensor_backward(loss, (), {"retain_graph": True}, lambda _loss: None)


def _synthetic_optimizer_state_fixture_v1() -> tuple[
    dict[str, torch.nn.Parameter], tuple[_GradientSnapshotV1, ...], object
]:
    """SYNTHETIC_OPTIMIZER_METADATA: no optimizer is constructed or stepped."""

    none = torch.nn.Parameter(torch.tensor([1.0, 2.0]))
    zero = torch.nn.Parameter(torch.tensor([3.0, 4.0]))
    active = torch.nn.Parameter(torch.tensor([5.0, 6.0]))
    zero.grad = torch.zeros_like(zero)
    active.grad = torch.tensor([0.25, -0.5])
    named = {"none": none, "zero": zero, "active": active}
    gradients = _capture_pre_step_gradients_v1(named)

    def state_for(parameter: torch.Tensor, gradient: torch.Tensor) -> dict[str, torch.Tensor]:
        return {
            "step": torch.tensor(1.0, dtype=torch.float32, device=parameter.device),
            "exp_avg": gradient.detach().clone().to(dtype=parameter.dtype),
            "exp_avg_sq": gradient.detach().square().clone().to(dtype=parameter.dtype),
            "max_exp_avg_sq": gradient.detach().square().clone().to(dtype=parameter.dtype),
        }

    optimizer = SimpleNamespace(
        param_groups=[{"params": [none, zero, active]}],
        state={zero: state_for(zero, zero.grad), active: state_for(active, active.grad)},
    )
    return named, gradients, optimizer


def test_synthetic_none_zero_nonzero_optimizer_state_metadata() -> None:
    named, gradients, optimizer = _synthetic_optimizer_state_fixture_v1()
    summary = _validate_optimizer_state_after_one_step_v1(
        optimizer=optimizer,
        named_parameters=named,
        pre_step_gradients=gradients,
    )
    assert summary == _OptimizerStateSummaryV1(2, 1, 1, 1)
    assert named["none"] not in optimizer.state
    assert named["zero"] in optimizer.state


@pytest.mark.parametrize(
    "mutation",
    ["foreign", "step", "nan", "inf", "shape", "missing_zero"],
)
def test_synthetic_optimizer_state_metadata_rejects_corruption(mutation: str) -> None:
    named, gradients, optimizer = _synthetic_optimizer_state_fixture_v1()
    if mutation == "foreign":
        foreign = torch.nn.Parameter(torch.tensor([7.0, 8.0]))
        optimizer.state[foreign] = {
            key: value.clone() for key, value in optimizer.state[named["active"]].items()
        }
    elif mutation == "step":
        optimizer.state[named["active"]]["step"] = torch.tensor(2.0)
    elif mutation == "nan":
        optimizer.state[named["active"]]["exp_avg"][0] = float("nan")
    elif mutation == "inf":
        optimizer.state[named["active"]]["exp_avg_sq"][0] = float("inf")
    elif mutation == "shape":
        optimizer.state[named["active"]]["exp_avg"] = torch.zeros(3)
    elif mutation == "missing_zero":
        optimizer.state.pop(named["zero"])
    with pytest.raises(AssertionError):
        _validate_optimizer_state_after_one_step_v1(
            optimizer=optimizer,
            named_parameters=named,
            pre_step_gradients=gradients,
        )


class _SyntheticStepModelV1(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.active = torch.nn.Parameter(torch.tensor([1.0, -1.0]))
        self.zero = torch.nn.Parameter(torch.tensor([2.0]))
        self.frozen_gamma = torch.nn.Parameter(
            torch.tensor([3.0]), requires_grad=False
        )
        self.register_buffer("stable_buffer", torch.tensor([4.0]))
        self.config_marker = "stable"


def _synthetic_configuration_v1(model: _SyntheticStepModelV1) -> object:
    return {"config_marker": model.config_marker}


def _synthetic_step_boundaries_v1() -> tuple[
    _SyntheticStepModelV1, dict[str, object], object, _StepBoundarySnapshotV1
]:
    model = _SyntheticStepModelV1()
    carrier = {"tasks": EXPECTED_EPOCH0_TASK_IDS_V1, "payload": torch.tensor([5, 8])}
    forward = _train10_backward_tools_v1()._forward_tools_v1()
    snapshot_a = _train10_backward_tools_v1()._capture_synthetic_compatible_snapshot_v1(
        model, configuration_snapshotter=_synthetic_configuration_v1
    )
    model.active.grad = torch.tensor([0.5, -0.25])
    model.zero.grad = torch.zeros_like(model.zero)
    carrier_fingerprint = forward._fingerprint_value_v1(carrier)
    _train10_backward_tools_v1()._assert_model_and_carrier_unchanged_allow_grad_v1(
        snapshot=snapshot_a,
        model=model,
        carrier_fingerprint=carrier_fingerprint,
        carrier=carrier,
        configuration_snapshotter=_synthetic_configuration_v1,
    )
    snapshot_b = _capture_step_boundary_v1(
        model=model,
        carrier=carrier,
        configuration_snapshotter=_synthetic_configuration_v1,
        carrier_fingerprinter=forward._fingerprint_value_v1,
    )
    return model, carrier, snapshot_a, snapshot_b


def test_synthetic_pre_step_invariance_and_legal_post_step_delta() -> None:
    """SYNTHETIC_OPTIMIZER_METADATA: after-values are prewritten, never stepped."""

    model, carrier, _snapshot_a, snapshot_b = _synthetic_step_boundaries_v1()
    with torch.no_grad():
        model.active.add_(torch.tensor([-0.01, 0.02]))
        model.zero.mul_(0.999)
    _assert_post_step_invariants_v1(
        snapshot=snapshot_b,
        model=model,
        carrier=carrier,
        frozen_parameter_names=("frozen_gamma",),
        configuration_snapshotter=_synthetic_configuration_v1,
        carrier_fingerprinter=_train10_backward_tools_v1()._forward_tools_v1()._fingerprint_value_v1,
    )
    delta = _observe_total_parameter_delta_v1(
        before=snapshot_b.parameter_values,
        named_parameters=dict(model.named_parameters()),
    )
    assert delta.changed_parameter_count == 2 and delta.all_finite


def test_synthetic_pre_step_parameter_change_is_rejected() -> None:
    model = _SyntheticStepModelV1()
    carrier = {"tasks": EXPECTED_EPOCH0_TASK_IDS_V1}
    forward = _train10_backward_tools_v1()._forward_tools_v1()
    snapshot_a = _train10_backward_tools_v1()._capture_synthetic_compatible_snapshot_v1(
        model, configuration_snapshotter=_synthetic_configuration_v1
    )
    with torch.no_grad():
        model.active.add_(1.0)
    with pytest.raises(AssertionError):
        _train10_backward_tools_v1()._assert_model_and_carrier_unchanged_allow_grad_v1(
            snapshot=snapshot_a,
            model=model,
            carrier_fingerprint=forward._fingerprint_value_v1(carrier),
            carrier=carrier,
            configuration_snapshotter=_synthetic_configuration_v1,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "buffer", "identity", "keys", "requires_grad", "carrier",
        "frozen_gamma", "grad", "nonfinite_parameter",
    ],
)
def test_synthetic_post_step_rejects_protected_state_changes(mutation: str) -> None:
    model, carrier, _snapshot_a, snapshot_b = _synthetic_step_boundaries_v1()
    if mutation == "buffer":
        model.stable_buffer.add_(1.0)
    elif mutation == "identity":
        model.active = torch.nn.Parameter(model.active.detach().clone())
    elif mutation == "keys":
        model.register_buffer("new_buffer", torch.tensor([9.0]))
    elif mutation == "requires_grad":
        model.zero.requires_grad_(False)
    elif mutation == "carrier":
        carrier["tasks"] = (0,)
    elif mutation == "frozen_gamma":
        with torch.no_grad():
            model.frozen_gamma.add_(1.0)
    elif mutation == "grad":
        model.active.grad = model.active.grad.clone()
    elif mutation == "nonfinite_parameter":
        with torch.no_grad():
            model.active[0] = float("nan")
    with pytest.raises(AssertionError):
        _assert_post_step_invariants_v1(
            snapshot=snapshot_b,
            model=model,
            carrier=carrier,
            frozen_parameter_names=("frozen_gamma",),
            configuration_snapshotter=_synthetic_configuration_v1,
            carrier_fingerprinter=_train10_backward_tools_v1()._forward_tools_v1()._fingerprint_value_v1,
        )


def test_synthetic_delta_groups_report_and_reject_bad_partition() -> None:
    """SYNTHETIC_OPTIMIZER_METADATA: deterministic before/after values only."""

    first = torch.nn.Parameter(torch.tensor([1.0]))
    second = torch.nn.Parameter(torch.tensor([2.0]))
    named = {"first": first, "second": second}
    before = {name: value.detach().clone() for name, value in named.items()}
    with torch.no_grad():
        first.add_(0.25)
    groups = _validate_parameter_groups_v1(
        groups=(("changed", ("first",)), ("unchanged", ("second",))),
        named_parameters=named,
    )
    stats = tuple(
        _old_single_step_tools_v1()._parameter_delta_group_stats_v1(
            group_name=group_name,
            parameter_names=members,
            before=before,
            named_parameters=named,
        )
        for group_name, members in groups
    )
    assert stats[0].changed_parameter_tensor_count == 1
    assert stats[1].unchanged_parameter_tensor_count == 1
    bad = (
        (("only", ("first",)),),
        (("a", ("first",)), ("b", ("first", "second"))),
        (("same", ("first",)), ("same", ("second",))),
    )
    for item in bad:
        with pytest.raises(AssertionError):
            _validate_parameter_groups_v1(groups=item, named_parameters=named)


def test_step_failure_progress_never_backfills_false() -> None:
    before = _RealExecutionGuardV1()
    assert _step_progress_summary_v1(before) == {
        "step_state": "step_not_requested",
        "step_requested": 0,
        "step_completed": 0,
        "parameter_delta_observed": False,
        "parameter_update_performed": False,
    }

    failing = _RealExecutionGuardV1()
    failing.phase = "optimizer_step"
    failing.expected_optimizer = object()
    with pytest.raises(RuntimeError, match="step failed"):
        failing.invoke_optimizer_step(
            optimizer=failing.expected_optimizer,
            closure=None,
            delegate=lambda: (_ for _ in ()).throw(RuntimeError("step failed")),
        )
    failed_summary = _step_progress_summary_v1(failing)
    assert failed_summary["step_state"] == (
        "step_requested_not_returned_partial_update_unknown"
    )
    assert failed_summary["parameter_update_performed"] == "unknown"

    returned = _RealExecutionGuardV1()
    returned.phase = "optimizer_step"
    returned.expected_optimizer = object()
    returned.invoke_optimizer_step(
        optimizer=returned.expected_optimizer,
        closure=None,
        delegate=lambda: None,
    )
    assert _step_progress_summary_v1(returned)["parameter_update_performed"] == "unknown"
    returned.parameter_delta_observed = True
    returned.changed_parameter_count = 3
    complete = _step_progress_summary_v1(returned)
    assert complete["step_state"] == "step_returned_parameter_delta_observed"
    assert complete["parameter_update_performed"] is True


def test_primary_error_survives_summary_and_cleanup_failures() -> None:
    primary = RuntimeError("primary")
    merge = _train10_backward_tools_v1()._merge_secondary_failure_v1

    def summary_failure() -> None:
        raise ValueError("summary")

    def cleanup_failure() -> None:
        raise OSError("cleanup")

    observed: BaseException | None = primary
    observed = merge(observed, phase="summary", callback=summary_failure)
    observed = merge(observed, phase="cleanup", callback=cleanup_failure)
    assert observed is primary
    assert len(primary.__notes__) == 2
    assert "summary" in primary.__notes__[0]
    assert "cleanup" in primary.__notes__[1]


def test_wrong_checkpoint_identity_rejected_before_deserialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    migration = (
        _train10_backward_tools_v1()._forward_tools_v1()
        ._load_real_path_dependencies_v1()["migration_owner"]
    )
    candidate = tmp_path / "SYNTHETIC_WRONG_CHECKPOINT_IDENTITY.bin"
    candidate.write_bytes(b"not-the-published-checkpoint")
    deserialization_calls = []

    def forbidden_load(*_args: object, **_kwargs: object) -> None:
        deserialization_calls.append("torch.load")
        raise AssertionError("identity mismatch reached deserialization")

    monkeypatch.setattr(migration.torch, "load", forbidden_load)
    with pytest.raises(
        ValueError, match="^COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR$"
    ):
        migration.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=candidate
        )
    assert deserialization_calls == []


def test_fresh_process_dependency_helper_adapter_first_no_model() -> None:
    child_code = r'''
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from unittest import mock

candidate = Path(os.environ["COVAPIE_FRESH_PROCESS_CANDIDATE"])
repo = Path(os.environ["COVAPIE_TEST_REPOSITORY_ROOT"])
state = Path(os.environ["COVAPIE_TEST_STATE_ROOT"])
runtime_parent = state / "review-scratch"
runtime_pattern = "validate_covapie_train10_checkpoint_single_optimizer_step_v1-*"
runtime_before = tuple(sorted(runtime_parent.glob(runtime_pattern)))
adapter_name = "covalent_ext.covapie_train10_hidden_post_forward_adapter_v1"
training_name = "covalent_ext.covapie_current11_training_lightning_module_v1"
assert adapter_name not in sys.modules and training_name not in sys.modules
assert "COVAPIE_RUN_TRAIN10_CHECKPOINT_SINGLE_OPTIMIZER_STEP" not in os.environ

spec = importlib.util.spec_from_file_location("cold_train10_single_step_candidate", candidate)
assert spec is not None and spec.loader is not None
subject = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = subject
spec.loader.exec_module(subject)
assert adapter_name not in sys.modules and training_name not in sys.modules
train10 = subject._train10_backward_tools_v1()
old_step = subject._old_single_step_tools_v1()
assert train10 is subject._train10_backward_tools_v1()
assert old_step is subject._old_single_step_tools_v1()
assert adapter_name not in sys.modules and training_name not in sys.modules
forward = train10._forward_tools_v1()

from Bio.PDB import Polypeptide
compat_before = hasattr(Polypeptide, "three_to_one")
assert compat_before is False
import pytorch_lightning as pl
import torch
from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration
from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer

calls = []
def forbidden(name):
    def tripwire(*_args, **_kwargs):
        calls.append(name)
        raise AssertionError("cold dependency boundary: " + name)
    return tripwire

profile_targets = {
    "CovapieTrain10HiddenPostForwardLigandPocketDDPMV1.__init__",
    "CovapieTrain10HiddenPostForwardLigandPocketDDPMV1.forward",
    "CovapieCurrent11TrainingLigandPocketDDPM.__init__",
    "CovapieCurrent11TrainingLigandPocketDDPM.forward",
    "LigandPocketDDPM.__init__",
    "LigandPocketDDPM.forward",
    "compute_covapie_current11_training_losses_v1",
}
def profiler(frame, event, _arg):
    if event == "call" and frame.f_code.co_qualname in profile_targets:
        calls.append("profile:" + frame.f_code.co_qualname)
        raise AssertionError("cold dependency executed model path")

def audit_hook(event, arguments):
    if event == "open" and arguments:
        path = arguments[0]
        if isinstance(path, (str, bytes, os.PathLike)):
            rendered = os.fsdecode(path)
            if "/checkpoints/" in rendered or rendered.endswith(".ckpt"):
                calls.append("checkpoint_open:" + rendered)
                raise AssertionError("cold dependency opened checkpoint")
    if event == "os.mkdir" and arguments:
        path = arguments[0]
        if isinstance(path, (str, bytes, os.PathLike)):
            created = Path(os.fsdecode(path))
            if not created.is_absolute():
                created = Path.cwd() / created
            if created.parent == runtime_parent and created.match(runtime_pattern):
                calls.append("runtime_mkdir:" + str(created))
                raise AssertionError("cold dependency created model runtime")

sys.addaudithook(audit_hook)
with contextlib.ExitStack() as stack:
    for owner, attribute, name in (
        (torch, "load", "torch.load"),
        (torch, "save", "torch.save"),
        (torch.Tensor, "backward", "Tensor.backward"),
        (torch.autograd, "backward", "torch.autograd.backward"),
        (torch.autograd, "grad", "torch.autograd.grad"),
        (torch.optim.Optimizer, "__init__", "Optimizer.__init__"),
        (torch.optim.Optimizer, "step", "Optimizer.step"),
        (torch.optim.AdamW, "__init__", "AdamW.__init__"),
        (torch.optim.AdamW, "step", "AdamW.step"),
        (pl.Trainer, "__init__", "Trainer.__init__"),
        (pl.Trainer, "fit", "Trainer.fit"),
        (migration, "load_covapie_current11_legacy_checkpoint_v1", "checkpoint_loader"),
        (composer, "prepare_covapie_train10_cpu_batch_composer_v1", "composer_prepare"),
        (composer, "build_covapie_train10_cpu_epoch_batch_v1", "carrier_build"),
    ):
        stack.enter_context(mock.patch.object(owner, attribute, new=forbidden(name)))
    sys.setprofile(profiler)
    try:
        first = forward._load_real_path_dependencies_v1()
        second = forward._load_real_path_dependencies_v1()
    finally:
        sys.setprofile(None)

assert calls == []
assert tuple(sorted(runtime_parent.glob(runtime_pattern))) == runtime_before
assert first.keys() == second.keys()
assert all(first[key] is second[key] for key in first)
assert first["adapter"] is sys.modules[adapter_name]
assert first["training_owner"] is sys.modules[training_name]
assert hasattr(Polypeptide, "three_to_one")
assert first["adapter"].BIOPYTHON_COMPAT_APPLIED_V1 is True
print(json.dumps({
    "compat_before": compat_before,
    "compat_after": hasattr(Polypeptide, "three_to_one"),
    "same_modules_on_second_call": True,
    "tripwire_calls": len(calls),
    "checkpoint_read": False,
    "carrier_built": False,
    "runtime_created": False,
    "model_instantiated": False,
    "forward_executed": False,
    "loss_executed": False,
    "backward_executed": False,
    "optimizer_constructed": False,
    "optimizer_step_executed": False,
}, sort_keys=True))
'''
    environment = os.environ.copy()
    for name in (
        REAL_SINGLE_STEP_OPT_IN_V1,
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_BACKWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_FORWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_BACKWARD_NO_UPDATE",
        "COVAPIE_RUN_BATCH001_CHECKPOINT_SINGLE_OPTIMIZER_STEP",
        "COVAPIE_TRAIN10_FORWARD_ADAPTER_CANDIDATE",
        "COVAPIE_TRAIN10_COMPOSER_CANDIDATE",
        "COVAPIE_CURRENT11_LEGACY_TRAIN5_DATA_ADAPTER_CANDIDATE",
        "COVAPIE_LEGACY_TRAIN5_ADAPTER_CANDIDATE",
        "COVAPIE_ADAPTER_CANDIDATE",
        "PYTHONOPTIMIZE",
        "PYTEST_ADDOPTS",
    ):
        environment.pop(name, None)
    environment.update({
        "COVAPIE_FRESH_PROCESS_CANDIDATE": str(Path(__file__).resolve(strict=True)),
        "COVAPIE_TEST_REPOSITORY_ROOT": str(ROOT),
        "COVAPIE_TEST_STATE_ROOT": str(STATE_ROOT),
        "COVAPIE_TEST_CACHE_ROOT": str(CACHE_ROOT),
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT}",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    })
    completed = subprocess.run(
        [sys.executable, "-B", "-c", child_code],
        cwd=ROOT,
        env=environment,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    assert len(lines) == 1, completed.stdout
    result = json.loads(lines[0])
    assert result == {
        "compat_before": False,
        "compat_after": True,
        "same_modules_on_second_call": True,
        "tripwire_calls": 0,
        "checkpoint_read": False,
        "carrier_built": False,
        "runtime_created": False,
        "model_instantiated": False,
        "forward_executed": False,
        "loss_executed": False,
        "backward_executed": False,
        "optimizer_constructed": False,
        "optimizer_step_executed": False,
    }
    print("FRESH_PROCESS_DEPENDENCY_IMPORT=" + lines[0], flush=True)


def test_real_checkpoint_train10_single_optimizer_step() -> None:
    _execute_real_path_if_enabled_v1()
