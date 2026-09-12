"""Opt-in real-checkpoint Batch001 single-optimizer-step integration V1.

Collection and ordinary execution are metadata-only: they do not deserialize
the checkpoint, construct the real model/optimizer, or run forward/backward.
The real path is technically gated by
``COVAPIE_RUN_BATCH001_CHECKPOINT_SINGLE_OPTIMIZER_STEP=1`` and must only be
invoked under separate, explicit parameter-update authorization.  The
environment variable is an entry switch, not that authorization.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
import hashlib
import importlib.util
import inspect
import io
import math
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
from typing import Callable, Mapping, NoReturn, Sequence
from unittest import mock

import pytest


TASK_ID_V1 = "validate_covapie_batch001_checkpoint_single_optimizer_step_v1"
REAL_SINGLE_STEP_OPT_IN_V1 = (
    "COVAPIE_RUN_BATCH001_CHECKPOINT_SINGLE_OPTIMIZER_STEP"
)
EXPECTED_CHECKPOINT_SIZE_BYTES_V1 = 17_861_341
EXPECTED_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
EXPECTED_EPOCH0_TASK_IDS_V1 = (4, 4, 2, 0, 4)
EXPECTED_CANONICAL_TASK_NAMES_V1 = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
EXPECTED_BACKWARD_TEST_SIZE_BYTES_V1 = 58_548
EXPECTED_BACKWARD_TEST_SHA256_V1 = (
    "6a9590c9ed5f87f0fddad2a0844a1c9b2e02f7b9c1aee5a80fa0e4621ef8640f"
)
PUBLISHED_BACKWARD_TASK_ID_V1 = (
    "validate_covapie_batch001_checkpoint_backward_no_update_v1"
)
PUBLISHED_BACKWARD_ITERATION_V1 = 9
PUBLISHED_BACKWARD_OUTPUT_ID_V1 = 589
FEATURE_SEMANTICS_USE_AUDIT_SCOPE_V1 = (
    "batch001_train5_epoch0_exact10_hidden_post_production_loss_v1"
)
FEATURE_SEMANTICS_RESOLUTION_SHA256_V1 = (
    "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241"
)
FEATURE_POST_USE_PREFLIGHT_SHA256_V1 = (
    "9e91e119a63867e7eda4ac76e0e8080ec774b2ee66e6b2ed8b4f4d9b07a6bf7c"
)
EXPECTED_TORCH_VERSION_V1 = "2.5.1+cu124"

ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = ROOT.parent / "covapie-state"
CACHE_ROOT = STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
PUBLISHED_BACKWARD_TEST_PATH_V1 = (
    ROOT / "tests/test_covapie_batch001_checkpoint_backward_no_update_v1.py"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_file_identity(path: Path) -> tuple[int, str, int]:
    metadata = path.lstat()
    assert stat.S_ISREG(metadata.st_mode)
    assert not path.is_symlink()
    return metadata.st_size, _sha256(path), stat.S_IMODE(metadata.st_mode)


def _load_published_backward_helpers_v1() -> ModuleType:
    """Load the fixed helper module without calling one of its test functions."""

    size, sha256, _mode = _safe_file_identity(PUBLISHED_BACKWARD_TEST_PATH_V1)
    assert size == EXPECTED_BACKWARD_TEST_SIZE_BYTES_V1
    assert sha256 == EXPECTED_BACKWARD_TEST_SHA256_V1
    spec = importlib.util.spec_from_file_location(
        "_covapie_published_checkpoint_backward_no_update_helpers_v1",
        PUBLISHED_BACKWARD_TEST_PATH_V1,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    stdout = io.StringIO()
    stderr = io.StringIO()
    previous = sys.modules.get(spec.name)
    sys.modules[spec.name] = module
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(spec.name, None)
        else:
            sys.modules[spec.name] = previous
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""
    return module


# The pinned module and its pinned forward-helper dependency import neither
# torch nor a CovaPIE model/checkpoint owner at module scope.
PUBLISHED_BACKWARD_HELPERS_V1 = _load_published_backward_helpers_v1()
PUBLISHED_FORWARD_HELPERS_V1 = (
    PUBLISHED_BACKWARD_HELPERS_V1.PUBLISHED_FORWARD_HELPERS_V1
)


def _evidence(message: str) -> None:
    print(f"COVAPIE_EVIDENCE {message}", flush=True)


@dataclass(frozen=True)
class _ApplicablePrerequisitesV1:
    feature_semantics_use_audit_scope: str
    feature_semantics_resolution_sha256: str
    feature_post_use_preflight_sha256: str
    scoped_feature_post_use_preflight_passed: bool
    published_backward_task_id: str
    published_backward_iteration: int
    published_backward_output_id: int
    published_backward_real_forward_count: int
    published_backward_real_backward_count: int
    published_backward_parameter_update_count: int
    feature_semantics_audit_required_later: bool
    step12d_is_only_smoke_legality_check: bool


PUBLISHED_APPLICABLE_PREREQUISITES_V1 = _ApplicablePrerequisitesV1(
    feature_semantics_use_audit_scope=FEATURE_SEMANTICS_USE_AUDIT_SCOPE_V1,
    feature_semantics_resolution_sha256=FEATURE_SEMANTICS_RESOLUTION_SHA256_V1,
    feature_post_use_preflight_sha256=FEATURE_POST_USE_PREFLIGHT_SHA256_V1,
    scoped_feature_post_use_preflight_passed=True,
    published_backward_task_id=PUBLISHED_BACKWARD_TASK_ID_V1,
    published_backward_iteration=PUBLISHED_BACKWARD_ITERATION_V1,
    published_backward_output_id=PUBLISHED_BACKWARD_OUTPUT_ID_V1,
    published_backward_real_forward_count=1,
    published_backward_real_backward_count=1,
    published_backward_parameter_update_count=0,
    feature_semantics_audit_required_later=True,
    step12d_is_only_smoke_legality_check=True,
)


def _require_applicable_prerequisites_v1(
    prerequisites: object,
) -> _ApplicablePrerequisitesV1:
    if prerequisites != PUBLISHED_APPLICABLE_PREREQUISITES_V1:
        raise AssertionError("applicable_single_step_prerequisites_missing")
    assert isinstance(prerequisites, _ApplicablePrerequisitesV1)
    return prerequisites


def _dispatch_real_runner_if_opted_in_v1(
    *,
    environ: Mapping[str, str],
    prerequisites: object,
    runner: Callable[[], object],
) -> tuple[bool, object | None]:
    """Keep the technical opt-in and evidence prerequisites independent."""

    if environ.get(REAL_SINGLE_STEP_OPT_IN_V1) != "1":
        return False, None
    _require_applicable_prerequisites_v1(prerequisites)
    return True, runner()


class _SingleStepBudgetV1:
    def __init__(self) -> None:
        self.request_count = 0
        self.completed_count = 0
        self.in_progress = False

    def run_once(self, callback: Callable[[], object]) -> object:
        if self.request_count != 0 or self.completed_count != 0 or self.in_progress:
            raise AssertionError("duplicate_optimizer_step_request")
        self.request_count = 1
        self.in_progress = True
        try:
            result = callback()
        finally:
            self.in_progress = False
        self.completed_count = 1
        return result


@dataclass(frozen=True)
class _OptimizerParameterIdentityV1:
    model_parameter_count: int
    optimizer_parameter_count: int
    frozen_parameter_count: int


def _validate_optimizer_parameter_identity_v1(
    *,
    named_parameters: Mapping[str, object],
    optimizer_parameter_groups: Sequence[Mapping[str, object]],
) -> _OptimizerParameterIdentityV1:
    if not named_parameters or not optimizer_parameter_groups:
        raise AssertionError("optimizer_parameter_identity_empty")
    model_parameters = tuple(named_parameters.values())
    model_ids = tuple(id(parameter) for parameter in model_parameters)
    if len(model_ids) != len(set(model_ids)):
        raise AssertionError("model_parameter_identity_duplicate")
    optimizer_parameters: list[object] = []
    for group in optimizer_parameter_groups:
        parameters = group.get("params")
        if not isinstance(parameters, (tuple, list)):
            raise AssertionError("optimizer_parameter_group_invalid")
        optimizer_parameters.extend(parameters)
    optimizer_ids = tuple(id(parameter) for parameter in optimizer_parameters)
    if len(optimizer_ids) != len(set(optimizer_ids)):
        raise AssertionError("optimizer_parameter_identity_duplicate")
    if set(optimizer_ids) != set(model_ids):
        raise AssertionError("optimizer_parameter_identity_coverage_mismatch")
    frozen_count = sum(
        getattr(parameter, "requires_grad", None) is False
        for parameter in model_parameters
    )
    return _OptimizerParameterIdentityV1(
        model_parameter_count=len(model_parameters),
        optimizer_parameter_count=len(optimizer_parameters),
        frozen_parameter_count=frozen_count,
    )


@dataclass(frozen=True)
class _OptimizerConfigurationV1:
    optimizer_type: str
    parameter_count: int
    frozen_parameter_count: int
    learning_rate: float
    betas: tuple[float, float]
    epsilon: float
    amsgrad: bool
    weight_decay: float
    foreach: object
    capturable: bool
    differentiable: bool
    fused: object


def _validate_real_optimizer_v1(
    *, model: object, optimizer: object, torch: ModuleType, training_owner: ModuleType
) -> _OptimizerConfigurationV1:
    assert getattr(type(model), "configure_optimizers") is (
        training_owner.CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    )
    assert type(optimizer) is torch.optim.AdamW
    assert len(optimizer.param_groups) == 1
    identity = _validate_optimizer_parameter_identity_v1(
        named_parameters=dict(model.named_parameters()),
        optimizer_parameter_groups=optimizer.param_groups,
    )
    group = optimizer.param_groups[0]
    assert identity.frozen_parameter_count > 0
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
    return _OptimizerConfigurationV1(
        optimizer_type=f"{type(optimizer).__module__}.{type(optimizer).__qualname__}",
        parameter_count=identity.optimizer_parameter_count,
        frozen_parameter_count=identity.frozen_parameter_count,
        learning_rate=float(group["lr"]),
        betas=group["betas"],
        epsilon=float(group["eps"]),
        amsgrad=group["amsgrad"],
        weight_decay=float(group["weight_decay"]),
        foreach=group["foreach"],
        capturable=group["capturable"],
        differentiable=group["differentiable"],
        fused=group["fused"],
    )


@dataclass(frozen=True)
class _AdamWImplementationContractV1:
    torch_version: str
    source_sha256: str
    grad_none_skipped_before_functional_update: bool
    zero_gradients_remain_in_functional_update: bool
    decoupled_weight_decay_present: bool


def _validate_installed_adamw_implementation_v1(
    torch: ModuleType,
) -> _AdamWImplementationContractV1:
    """Bind the grad/state/delta interpretation to installed AdamW source."""

    from torch.optim import adamw as adamw_owner

    assert torch.__version__ == EXPECTED_TORCH_VERSION_V1
    step_source = inspect.getsource(torch.optim.AdamW.step)
    init_group_source = inspect.getsource(torch.optim.AdamW._init_group)
    single_source = inspect.getsource(adamw_owner._single_tensor_adamw)
    multi_source = inspect.getsource(adamw_owner._multi_tensor_adamw)
    assert "self._init_group(" in step_source and "adamw(" in step_source
    assert "if p.grad is None:" in init_group_source
    assert "params_with_grad.append(p)" in init_group_source
    assert "param.mul_(1 - lr * weight_decay)" in single_source
    assert "torch._foreach_mul_(device_params, 1 - lr * weight_decay)" in multi_source
    combined = "\n".join((step_source, init_group_source, single_source, multi_source))
    return _AdamWImplementationContractV1(
        torch_version=torch.__version__,
        source_sha256=hashlib.sha256(combined.encode("utf-8")).hexdigest(),
        grad_none_skipped_before_functional_update=True,
        zero_gradients_remain_in_functional_update=True,
        decoupled_weight_decay_present=True,
    )


class _RealExecutionGuardV1:
    def __init__(self) -> None:
        self.phase = "before_real_operations"
        self.forward_call_count = 0
        self.backward_call_count = 0
        self.internal_autograd_backward_call_count = 0
        self.optimizer_init_count = 0
        self.expected_loss: object | None = None
        self.expected_optimizer: object | None = None
        self.backward_in_progress = False
        self.optimizer_step_budget = _SingleStepBudgetV1()
        self.forbidden_calls: list[str] = []

    def reject(self, name: str) -> NoReturn:
        self.forbidden_calls.append(name)
        raise AssertionError(f"forbidden operation invoked: {name}")


def _install_real_operation_guards_v1(
    stack: contextlib.ExitStack,
    *,
    torch: ModuleType,
    lightning: ModuleType,
    guard: _RealExecutionGuardV1,
) -> None:
    original_tensor_backward = torch.Tensor.backward
    original_autograd_backward = torch.autograd.backward
    original_adamw_init = torch.optim.AdamW.__init__
    original_adamw_step = torch.optim.AdamW.step

    def forbidden(name: str):
        def tripwire(*_args: object, **_kwargs: object) -> None:
            guard.reject(name)

        return tripwire

    def guarded_backward(
        tensor: object, *args: object, **kwargs: object
    ) -> None:
        if guard.phase != "backward" or tensor is not guard.expected_loss:
            guard.reject("Tensor.backward.unbound_loss_or_phase")
        if args or kwargs or guard.backward_call_count != 0:
            guard.reject("Tensor.backward.options_or_duplicate")
        guard.backward_call_count = 1
        guard.backward_in_progress = True
        try:
            original_tensor_backward(tensor)
        finally:
            guard.backward_in_progress = False

    def guarded_autograd_backward(*args: object, **kwargs: object) -> None:
        if not guard.backward_in_progress:
            guard.reject("torch.autograd.backward.outside_authorized_call")
        retain_graph = kwargs.get(
            "retain_graph", args[2] if len(args) > 2 else None
        )
        create_graph = kwargs.get(
            "create_graph", args[3] if len(args) > 3 else False
        )
        if retain_graph not in (None, False) or create_graph not in (None, False):
            guard.reject("torch.autograd.backward.graph_retention_requested")
        guard.internal_autograd_backward_call_count += 1
        if guard.internal_autograd_backward_call_count != 1:
            guard.reject("torch.autograd.backward.unexpected_internal_count")
        original_autograd_backward(*args, **kwargs)

    def guarded_adamw_init(
        optimizer: object, *args: object, **kwargs: object
    ) -> None:
        if guard.phase != "optimizer_construction" or guard.optimizer_init_count != 0:
            guard.reject("AdamW.__init__.unbound_or_duplicate")
        guard.optimizer_init_count = 1
        original_adamw_init(optimizer, *args, **kwargs)
        guard.expected_optimizer = optimizer

    def guarded_adamw_step(
        optimizer: object, closure: object = None
    ) -> object:
        if (
            guard.phase != "optimizer_step"
            or optimizer is not guard.expected_optimizer
            or closure is not None
        ):
            guard.reject("AdamW.step.unbound_optimizer_phase_or_closure")

        def perform() -> object:
            return original_adamw_step(optimizer, closure=None)

        return guard.optimizer_step_budget.run_once(perform)

    direct_targets = (
        (torch.Tensor, "backward", guarded_backward),
        (torch.autograd, "backward", guarded_autograd_backward),
        (torch.autograd, "grad", forbidden("torch.autograd.grad")),
        (torch, "save", forbidden("torch.save")),
        (lightning.Trainer, "__init__", forbidden("Trainer.__init__")),
        (lightning.Trainer, "fit", forbidden("Trainer.fit")),
        (lightning.Trainer, "validate", forbidden("Trainer.validate")),
        (lightning.Trainer, "test", forbidden("Trainer.test")),
        (lightning.Trainer, "predict", forbidden("Trainer.predict")),
        (
            lightning.Trainer,
            "save_checkpoint",
            forbidden("Trainer.save_checkpoint"),
        ),
        (
            lightning.LightningModule,
            "load_from_checkpoint",
            forbidden("LightningModule.load_from_checkpoint"),
        ),
        (torch.optim.AdamW, "__init__", guarded_adamw_init),
        (torch.optim.AdamW, "step", guarded_adamw_step),
    )
    for owner, attribute, replacement in direct_targets:
        stack.enter_context(mock.patch.object(owner, attribute, new=replacement))

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


def _install_model_and_forward_guards_v1(
    stack: contextlib.ExitStack,
    *,
    model: object,
    carrier: object,
    torch: ModuleType,
    guard: _RealExecutionGuardV1,
) -> None:
    original_forward = model.forward

    def forbidden(name: str):
        def tripwire(*_args: object, **_kwargs: object) -> None:
            guard.reject(name)

        return tripwire

    def guarded_forward(data: object) -> object:
        if (
            guard.phase != "forward"
            or data is not carrier
            or guard.forward_call_count != 0
        ):
            guard.reject("model.forward.unbound_carrier_phase_or_duplicate")
        guard.forward_call_count = 1
        return original_forward(data)

    stack.enter_context(mock.patch.object(model, "forward", new=guarded_forward))
    for attribute in (
        "training_step",
        "validation_step",
        "test_step",
        "load_state_dict",
    ):
        stack.enter_context(mock.patch.object(
            model, attribute, new=forbidden(f"model.{attribute}")
        ))

    protected_storage_pointers = {
        tensor.untyped_storage().data_ptr()
        for tensor in tuple(model.parameters()) + tuple(model.buffers())
        if tensor.numel()
    }

    def protect_inplace_method(name: str, original: object):
        def guarded(tensor: object, *args: object, **kwargs: object):
            protected = (
                tensor.numel()
                and tensor.untyped_storage().data_ptr()
                in protected_storage_pointers
            )
            if protected and not guard.optimizer_step_budget.in_progress:
                guard.reject(f"model_state_write.{name}")
            return original(tensor, *args, **kwargs)

        return guarded

    for attribute in (
        "copy_",
        "set_",
        "add_",
        "sub_",
        "mul_",
        "div_",
        "zero_",
        "fill_",
        "index_copy_",
        "scatter_",
        "__setitem__",
    ):
        original = getattr(torch.Tensor, attribute)
        stack.enter_context(mock.patch.object(
            torch.Tensor,
            attribute,
            new=protect_inplace_method(attribute, original),
        ))


@dataclass(frozen=True)
class _ParameterDeltaGroupStatsV1:
    group_name: str
    parameter_tensor_count: int
    changed_parameter_tensor_count: int
    unchanged_parameter_tensor_count: int
    all_parameters_finite: bool
    delta_l2_norm: float
    delta_max_abs: float


def _parameter_delta_group_stats_v1(
    *,
    group_name: str,
    parameter_names: Sequence[str],
    before: Mapping[str, object],
    named_parameters: Mapping[str, object],
) -> _ParameterDeltaGroupStatsV1:
    import torch

    names = tuple(parameter_names)
    assert names and len(names) == len(set(names))
    assert set(names) <= set(before) and set(names) <= set(named_parameters)
    deltas = tuple(
        named_parameters[name].detach().double() - before[name].detach().double()
        for name in names
    )
    changed_count = sum(int(torch.count_nonzero(delta).item()) > 0 for delta in deltas)
    squared_l2 = sum(float(delta.square().sum().item()) for delta in deltas)
    maximum = max(
        (float(delta.abs().max().item()) for delta in deltas if delta.numel()),
        default=0.0,
    )
    finite = all(
        bool(torch.isfinite(named_parameters[name]).all().item()) for name in names
    ) and all(bool(torch.isfinite(delta).all().item()) for delta in deltas)
    return _ParameterDeltaGroupStatsV1(
        group_name=group_name,
        parameter_tensor_count=len(names),
        changed_parameter_tensor_count=changed_count,
        unchanged_parameter_tensor_count=len(names) - changed_count,
        all_parameters_finite=finite,
        delta_l2_norm=math.sqrt(squared_l2),
        delta_max_abs=maximum,
    )


def _emit_parameter_delta_stats_v1(stats: _ParameterDeltaGroupStatsV1) -> None:
    _evidence(
        f"parameter_delta_group={stats.group_name} "
        f"parameter_tensors={stats.parameter_tensor_count} "
        f"changed={stats.changed_parameter_tensor_count} "
        f"unchanged={stats.unchanged_parameter_tensor_count} "
        f"all_parameters_finite={str(stats.all_parameters_finite).lower()} "
        f"l2_norm={stats.delta_l2_norm:.17g} "
        f"max_abs={stats.delta_max_abs:.17g}"
    )


def _parameter_groups_v1(
    *, named_parameters: Mapping[str, object], checkpoint_state: Mapping[str, object]
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    legacy_names = tuple(name for name in named_parameters if name in checkpoint_state)
    target_names = (PUBLISHED_BACKWARD_HELPERS_V1.TARGET_RESIDUE_PARAMETER_NAME_V1,)
    encoding_names = PUBLISHED_BACKWARD_HELPERS_V1._names_with_prefixes(
        named_parameters,
        PUBLISHED_BACKWARD_HELPERS_V1.ROLE_TASK_GENERATION_SEED_ANCHOR_PREFIXES_V1,
    )
    pair_names = PUBLISHED_BACKWARD_HELPERS_V1._names_with_prefixes(
        named_parameters, PUBLISHED_BACKWARD_HELPERS_V1.PAIR_PREFIXES_V1
    )
    geometry_names = PUBLISHED_BACKWARD_HELPERS_V1._names_with_prefixes(
        named_parameters, PUBLISHED_BACKWARD_HELPERS_V1.GEOMETRY_PREFIX_V1
    )
    groups = (
        ("legacy_ddpm_egnn", legacy_names),
        ("target_residue_condition_embedding", target_names),
        ("role_task_generation_seed_anchor_encoding", encoding_names),
        ("pair_embedding_pair_logit", pair_names),
        ("pre_post_geometry_head", geometry_names),
    )
    flattened = tuple(name for _group, names in groups for name in names)
    assert all(names for _group, names in groups)
    assert len(flattened) == len(set(flattened)) == len(named_parameters)
    assert set(flattened) == set(named_parameters)
    return groups


def _validate_optimizer_state_after_one_step_v1(
    *, optimizer: object, named_parameters: Mapping[str, object], torch: ModuleType
) -> tuple[int, int, int]:
    with_gradient = tuple(
        parameter for parameter in named_parameters.values() if parameter.grad is not None
    )
    without_gradient = tuple(
        parameter for parameter in named_parameters.values() if parameter.grad is None
    )
    assert {id(parameter) for parameter in optimizer.state} == {
        id(parameter) for parameter in with_gradient
    }
    assert not ({id(parameter) for parameter in optimizer.state} & {
        id(parameter) for parameter in without_gradient
    })
    for parameter in with_gradient:
        state = optimizer.state[parameter]
        assert set(state) == {"step", "exp_avg", "exp_avg_sq", "max_exp_avg_sq"}
        assert float(state["step"].item()) == 1.0
        assert all(
            bool(torch.isfinite(value).all().item())
            for value in state.values()
            if isinstance(value, torch.Tensor)
        )
    zero_gradient_count = sum(
        int(torch.count_nonzero(parameter.grad).item()) == 0
        for parameter in with_gradient
    )
    return len(with_gradient), len(without_gradient), zero_gradient_count


def _run_real_checkpoint_single_optimizer_step_v1(tmp_path: Path) -> None:
    """Run only after an independently authorized invocation of the opt-in test."""

    import pytorch_lightning as lightning
    import torch
    from covalent_ext import (
        covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
        as activation_owner,
    )
    from covalent_ext import (
        covapie_batch001_feature_post_use_preflight_v1 as preflight_owner,
    )
    from covalent_ext import covapie_batch001_hidden_post_forward_adapter_v1 as adapter
    from covalent_ext import (
        covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
        as checkpoint_locator,
    )
    from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration_owner
    from covalent_ext import covapie_current11_training_lightning_module_v1 as training_owner
    from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
        CovapieCurrent11LossWeightsV1,
    )

    guard = _RealExecutionGuardV1()
    stage = "source_checkpoint_and_adamw_identity"
    exact1_identity = _safe_file_identity(Path(__file__).resolve())
    backward_identity = _safe_file_identity(PUBLISHED_BACKWARD_TEST_PATH_V1)
    assert backward_identity[:2] == (
        EXPECTED_BACKWARD_TEST_SIZE_BYTES_V1,
        EXPECTED_BACKWARD_TEST_SHA256_V1,
    )
    source_identity_before = (
        adapter.verify_covapie_batch001_hidden_post_forward_adapter_sources_v1(
            repository_root=ROOT
        )
        + PUBLISHED_FORWARD_HELPERS_V1._verify_additional_bound_sources()
    )
    assert _sha256(
        ROOT
        / "src/covalent_ext/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py"
    ) == FEATURE_SEMANTICS_RESOLUTION_SHA256_V1
    assert _sha256(
        ROOT / "src/covalent_ext/covapie_batch001_feature_post_use_preflight_v1.py"
    ) == FEATURE_POST_USE_PREFLIGHT_SHA256_V1
    adamw_contract = _validate_installed_adamw_implementation_v1(torch)
    checkpoint_path = ROOT / checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1
    checkpoint_identity = _safe_file_identity(checkpoint_path)
    assert checkpoint_identity[:2] == (
        EXPECTED_CHECKPOINT_SIZE_BYTES_V1,
        EXPECTED_CHECKPOINT_SHA256_V1,
    )
    _evidence(
        f"real_run=START stage={stage} exact1_bytes={exact1_identity[0]} "
        f"exact1_sha256={exact1_identity[1]} "
        f"published_backward_iteration={PUBLISHED_BACKWARD_ITERATION_V1} "
        f"published_backward_output={PUBLISHED_BACKWARD_OUTPUT_ID_V1} "
        f"torch_version={adamw_contract.torch_version} "
        f"adamw_source_sha256={adamw_contract.source_sha256} "
        "forward_budget=1 backward_budget=1 optimizer_init_budget=1 step_budget=1"
    )

    try:
        with contextlib.ExitStack() as safety_stack:
            _install_real_operation_guards_v1(
                safety_stack, torch=torch, lightning=lightning, guard=guard
            )

            stage = "checkpoint_load"
            guard.phase = stage
            checkpoint = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
                checkpoint_path=checkpoint_path
            )
            checkpoint_state = checkpoint["state_dict"]
            assert checkpoint["checkpoint_size_bytes"] == checkpoint_identity[0]
            assert checkpoint["checkpoint_sha256"] == checkpoint_identity[1]

            stage = "model_construction_and_strict_migration"
            guard.phase = stage
            model = PUBLISHED_FORWARD_HELPERS_V1._instantiate_exact_adapter(
                checkpoint=checkpoint, runtime_root=tmp_path
            )
            migration = migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
                model=model, checkpoint_state_dict=checkpoint_state
            )
            assert type(model) is adapter.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1
            assert model.device == torch.device("cpu")
            assert migration["checkpoint_only_key_count"] == 0
            assert migration["shared_shape_mismatch_count"] == 0
            assert migration["migration_missing_keys"] == ()
            assert migration["migration_unexpected_keys"] == ()
            assert migration["full_target_strict_load"] is True
            migrated_state = model.state_dict()
            shared_keys = set(migrated_state) & set(checkpoint_state)
            assert migration["shared_checkpoint_tensor_equality_count"] == len(shared_keys)
            assert all(
                migrated_state[key].detach().cpu().equal(
                    checkpoint_state[key].detach().cpu()
                )
                for key in shared_keys
            )
            model.train()
            assert model.training is True and model.current_epoch == 0
            named_parameters = dict(model.named_parameters())
            requires_grad_at_a = {
                name: parameter.requires_grad
                for name, parameter in named_parameters.items()
            }
            parameter_identity_at_a = {
                name: id(parameter) for name, parameter in named_parameters.items()
            }
            buffer_identity_at_a = {
                name: id(buffer) for name, buffer in model.named_buffers()
            }
            assert tuple(
                name for name, parameter in named_parameters.items()
                if not parameter.requires_grad
            ) == PUBLISHED_BACKWARD_HELPERS_V1.FROZEN_PARAMETER_CONTRACT_V1
            parameters_at_a = PUBLISHED_FORWARD_HELPERS_V1._snapshot_named_tensors(
                model.named_parameters()
            )
            buffers_at_a = PUBLISHED_FORWARD_HELPERS_V1._snapshot_named_tensors(
                model.named_buffers()
            )
            assert PUBLISHED_FORWARD_HELPERS_V1._all_gradients_none(model)

            stage = "optimizer_construction"
            guard.phase = stage
            optimizer = model.configure_optimizers()
            assert optimizer is guard.expected_optimizer
            optimizer_configuration = _validate_real_optimizer_v1(
                model=model,
                optimizer=optimizer,
                torch=torch,
                training_owner=training_owner,
            )
            assert optimizer.state == {}
            assert guard.optimizer_init_count == 1
            _evidence(
                f"optimizer_configuration=PASS {optimizer_configuration} "
                "owner_method_identity_exact=true frozen_schedule_included=true "
                "state_entries_before_step=0"
            )

            stage = "real_train5_carrier"
            guard.phase = stage
            carrier = activation_owner.build_covapie_batch001_model_usable_split_batch_v1(
                split="train",
                epoch=0,
                task_schedule_seed=0,
                repository_root=ROOT,
                cache_root=CACHE_ROOT,
            )
            carrier_fingerprint_before, preflight_rows = (
                preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(
                    carrier
                )
            )
            assert carrier.formal_split == "train"
            assert carrier.epoch == 0 and carrier.task_schedule_seed == 0
            assert carrier.training_scheduled_task_ids == EXPECTED_EPOCH0_TASK_IDS_V1
            assert tuple(carrier.supervision.canonical_task_id.tolist()) == (
                EXPECTED_EPOCH0_TASK_IDS_V1
            )
            assert tuple(
                row[1] for row in preflight_owner.CANONICAL_TASKS_V1
            ) == EXPECTED_CANONICAL_TASK_NAMES_V1
            assert len(preflight_rows) == 5
            carrier_tensor_snapshot = PUBLISHED_FORWARD_HELPERS_V1._snapshot_named_tensors(
                PUBLISHED_BACKWARD_HELPERS_V1._named_carrier_tensors(carrier)
            )
            carrier_metadata_before = PUBLISHED_BACKWARD_HELPERS_V1._carrier_metadata(
                carrier
            )
            _install_model_and_forward_guards_v1(
                safety_stack,
                model=model,
                carrier=carrier,
                torch=torch,
                guard=guard,
            )

            stage = "forward"
            guard.phase = stage
            weights = model.covapie_current11_loss_weights
            assert weights == CovapieCurrent11LossWeightsV1(
                base_diffusion=1.0,
                covalent_pair_prediction=1.0,
                pre_post_geometry=0.0,
                covalent_pair_contrastive=0.1,
            )
            output = model(carrier)
            assert guard.forward_call_count == 1
            loss_total = output.loss_output.loss_total
            assert loss_total.ndim == 0
            assert bool(torch.isfinite(loss_total).item())
            assert loss_total.requires_grad is True and loss_total.grad_fn is not None
            assert output.supervision is carrier.supervision

            stage = "backward"
            guard.phase = stage
            guard.expected_loss = loss_total
            loss_total.backward()
            assert guard.backward_call_count == 1
            assert guard.internal_autograd_backward_call_count == 1
            named_parameters = dict(model.named_parameters())
            assert {
                name: id(parameter) for name, parameter in named_parameters.items()
            } == parameter_identity_at_a
            assert {
                name: id(buffer) for name, buffer in model.named_buffers()
            } == buffer_identity_at_a
            assert {
                name: parameter.requires_grad
                for name, parameter in named_parameters.items()
            } == requires_grad_at_a
            PUBLISHED_FORWARD_HELPERS_V1._assert_snapshot_unchanged(
                parameters_at_a, model.named_parameters()
            )
            PUBLISHED_FORWARD_HELPERS_V1._assert_snapshot_unchanged(
                buffers_at_a, model.named_buffers()
            )
            PUBLISHED_BACKWARD_HELPERS_V1._assert_carrier_tensor_snapshot_unchanged(
                carrier_tensor_snapshot,
                PUBLISHED_BACKWARD_HELPERS_V1._named_carrier_tensors(carrier),
            )
            assert PUBLISHED_BACKWARD_HELPERS_V1._carrier_metadata(carrier) == (
                carrier_metadata_before
            )
            groups = _parameter_groups_v1(
                named_parameters=named_parameters,
                checkpoint_state=checkpoint_state,
            )
            group_map = dict(groups)
            seed_branch_active = bool(
                carrier.supervision.ligand_minimal_seed_or_anchor_valid[
                    carrier.model_input_batch["lig_mask"]
                ].any().item()
            )
            inactive_names = set(group_map["pre_post_geometry_head"]) | {
                name
                for name in group_map["legacy_ddpm_egnn"]
                if name.startswith(
                    PUBLISHED_BACKWARD_HELPERS_V1.LEGACY_INACTIVE_RESIDUE_DECODER_PREFIX_V1
                )
            }
            if not seed_branch_active:
                inactive_names.update(
                    name
                    for name in group_map[
                        "role_task_generation_seed_anchor_encoding"
                    ]
                    if name.startswith(
                        "covapie_current11_auxiliary_model_v1."
                        "seed_indicator_embedding."
                    )
                )
            classification = (
                PUBLISHED_BACKWARD_HELPERS_V1._validate_parameter_gradient_classification_v1(
                    PUBLISHED_BACKWARD_HELPERS_V1._parameter_gradient_metadata_v1(
                        named_parameters
                    ),
                    frozen_parameter_contract=(
                        PUBLISHED_BACKWARD_HELPERS_V1.FROZEN_PARAMETER_CONTRACT_V1
                    ),
                    inactive_trainable_parameter_names=tuple(sorted(inactive_names)),
                    active_zero_gradient_parameter_names=(
                        PUBLISHED_BACKWARD_HELPERS_V1.ACTIVE_ZERO_GRADIENT_CONTRACT_V1
                    ),
                )
            )
            parameters_at_b = PUBLISHED_FORWARD_HELPERS_V1._snapshot_named_tensors(
                model.named_parameters()
            )
            buffers_at_b = PUBLISHED_FORWARD_HELPERS_V1._snapshot_named_tensors(
                model.named_buffers()
            )
            _evidence(
                "stage_a_to_b=PASS parameters_unchanged=true buffers_unchanged=true "
                "requires_grad_unchanged=true carrier_unchanged=true "
                f"frozen={len(classification.frozen_parameter_names)} "
                f"inactive={len(classification.inactive_trainable_parameter_names)} "
                f"active={len(classification.active_parameter_names)}"
            )

            stage = "optimizer_step"
            guard.phase = stage
            optimizer.step()
            assert guard.optimizer_step_budget.request_count == 1
            assert guard.optimizer_step_budget.completed_count == 1
            assert not guard.optimizer_step_budget.in_progress

            stage = "post_step_validation"
            guard.phase = stage
            named_parameters = dict(model.named_parameters())
            assert {
                name: id(parameter) for name, parameter in named_parameters.items()
            } == parameter_identity_at_a
            assert {
                name: id(buffer) for name, buffer in model.named_buffers()
            } == buffer_identity_at_a
            assert {
                name: parameter.requires_grad
                for name, parameter in named_parameters.items()
            } == requires_grad_at_a
            frozen_name = PUBLISHED_BACKWARD_HELPERS_V1.FROZEN_PARAMETER_CONTRACT_V1[0]
            frozen_gamma = named_parameters[frozen_name]
            assert frozen_gamma.requires_grad is False and frozen_gamma.grad is None
            assert frozen_gamma.detach().equal(parameters_at_b[frozen_name])
            PUBLISHED_FORWARD_HELPERS_V1._assert_snapshot_unchanged(
                buffers_at_b, model.named_buffers()
            )
            PUBLISHED_BACKWARD_HELPERS_V1._assert_carrier_tensor_snapshot_unchanged(
                carrier_tensor_snapshot,
                PUBLISHED_BACKWARD_HELPERS_V1._named_carrier_tensors(carrier),
            )
            assert PUBLISHED_BACKWARD_HELPERS_V1._carrier_metadata(carrier) == (
                carrier_metadata_before
            )
            carrier_fingerprint_after, _rows = (
                preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(
                    carrier
                )
            )
            assert carrier_fingerprint_after == carrier_fingerprint_before
            for name, parameter in named_parameters.items():
                if parameter.grad is None:
                    assert parameter.detach().equal(parameters_at_b[name]), name
            state_with_grad, state_without_grad, zero_gradient_count = (
                _validate_optimizer_state_after_one_step_v1(
                    optimizer=optimizer,
                    named_parameters=named_parameters,
                    torch=torch,
                )
            )
            delta_stats = tuple(
                _parameter_delta_group_stats_v1(
                    group_name=group_name,
                    parameter_names=names,
                    before=parameters_at_b,
                    named_parameters=named_parameters,
                )
                for group_name, names in groups
            )
            stats_map = {stats.group_name: stats for stats in delta_stats}
            for stats in delta_stats:
                _emit_parameter_delta_stats_v1(stats)
                assert stats.all_parameters_finite
                assert math.isfinite(stats.delta_l2_norm)
                assert math.isfinite(stats.delta_max_abs)
            for expected_active_group in (
                "legacy_ddpm_egnn",
                "target_residue_condition_embedding",
                "role_task_generation_seed_anchor_encoding",
                "pair_embedding_pair_logit",
            ):
                assert stats_map[
                    expected_active_group
                ].changed_parameter_tensor_count > 0
            assert guard.forbidden_calls == []
            assert guard.forward_call_count == 1
            assert guard.backward_call_count == 1
            assert guard.optimizer_init_count == 1
            assert guard.optimizer_step_budget.completed_count == 1

            stage = "final_integrity"
            guard.phase = stage
            source_identity_after = (
                adapter.verify_covapie_batch001_hidden_post_forward_adapter_sources_v1(
                    repository_root=ROOT
                )
                + PUBLISHED_FORWARD_HELPERS_V1._verify_additional_bound_sources()
            )
            assert source_identity_after == source_identity_before
            assert _safe_file_identity(PUBLISHED_BACKWARD_TEST_PATH_V1) == (
                backward_identity
            )
            assert _safe_file_identity(Path(__file__).resolve()) == exact1_identity
            assert _safe_file_identity(checkpoint_path) == checkpoint_identity
            _evidence(
                "stage_b_to_c=PASS optimizer_step_count=1 "
                f"optimizer_state_with_grad={state_with_grad} "
                f"optimizer_state_without_grad={state_without_grad} "
                f"zero_gradient_parameter_count={zero_gradient_count} "
                "all_parameters_finite=true frozen_gamma_unchanged=true "
                "buffers_unchanged=true carrier_unchanged=true "
                "sources_unchanged=true checkpoint_unchanged=true "
                "second_step=false parameter_reload=false manual_write=false"
            )

        stage = "complete"
        _evidence(
            "real_run=PASS forward_count=1 backward_count=1 "
            "optimizer_created_count=1 optimizer_step_count=1 "
            "parameter_update_performed=true Trainer=false loop=false save=false "
            "post_step_forward=false loss_decrease_claimed=false "
            "geometry_supervision_learning_claimed=false training_ready=false"
        )
    except BaseException as error:
        _evidence(
            f"real_run=FAIL stage={stage} error_type={type(error).__name__} "
            f"forward_count={guard.forward_call_count} "
            f"backward_count={guard.backward_call_count} "
            f"optimizer_created_count={guard.optimizer_init_count} "
            f"optimizer_step_requested={guard.optimizer_step_budget.request_count} "
            f"optimizer_step_completed={guard.optimizer_step_budget.completed_count}"
        )
        raise


def test_non_opt_in_and_missing_prerequisites_fail_before_real_runner() -> None:
    runner_calls: list[str] = []

    def runner() -> str:
        runner_calls.append("real_runner")
        return "unexpected"

    entered, result = _dispatch_real_runner_if_opted_in_v1(
        environ={},
        prerequisites=PUBLISHED_APPLICABLE_PREREQUISITES_V1,
        runner=runner,
    )
    assert entered is False and result is None and runner_calls == []
    entered, result = _dispatch_real_runner_if_opted_in_v1(
        environ={REAL_SINGLE_STEP_OPT_IN_V1: "0"},
        prerequisites=PUBLISHED_APPLICABLE_PREREQUISITES_V1,
        runner=runner,
    )
    assert entered is False and result is None and runner_calls == []

    incomplete = _ApplicablePrerequisitesV1(
        **dict(
            PUBLISHED_APPLICABLE_PREREQUISITES_V1.__dict__,
            scoped_feature_post_use_preflight_passed=False,
        )
    )
    with pytest.raises(
        AssertionError, match="applicable_single_step_prerequisites_missing"
    ):
        _dispatch_real_runner_if_opted_in_v1(
            environ={REAL_SINGLE_STEP_OPT_IN_V1: "1"},
            prerequisites=incomplete,
            runner=runner,
        )
    assert runner_calls == []


def test_single_step_budget_rejects_duplicate_metadata_callback() -> None:
    callback_calls: list[str] = []
    budget = _SingleStepBudgetV1()

    def metadata_callback() -> str:
        callback_calls.append("called")
        return "complete"

    assert budget.run_once(metadata_callback) == "complete"
    assert callback_calls == ["called"]
    assert budget.request_count == budget.completed_count == 1
    with pytest.raises(AssertionError, match="duplicate_optimizer_step_request"):
        budget.run_once(metadata_callback)
    assert callback_calls == ["called"]
    assert budget.request_count == budget.completed_count == 1


def test_gradient_roles_and_optimizer_parameter_identity_fail_closed() -> None:
    record_type = PUBLISHED_BACKWARD_HELPERS_V1._ParameterGradientMetadataV1
    records = (
        record_type("frozen.gamma", False, "none", True),
        record_type("inactive.weight", True, "none", True),
        record_type("active.weight", True, "nonzero", True),
    )
    classification = (
        PUBLISHED_BACKWARD_HELPERS_V1._validate_parameter_gradient_classification_v1(
            records,
            frozen_parameter_contract=("frozen.gamma",),
            inactive_trainable_parameter_names=("inactive.weight",),
            active_zero_gradient_parameter_names=(),
        )
    )
    assert classification.frozen_parameter_names == ("frozen.gamma",)
    assert classification.inactive_trainable_parameter_names == ("inactive.weight",)
    assert classification.active_parameter_names == ("active.weight",)
    with pytest.raises(AssertionError, match="frozen_parameter_contract_mismatch"):
        PUBLISHED_BACKWARD_HELPERS_V1._validate_parameter_gradient_classification_v1(
            records,
            frozen_parameter_contract=("active.weight",),
            inactive_trainable_parameter_names=("inactive.weight",),
            active_zero_gradient_parameter_names=(),
        )
    with pytest.raises(AssertionError):
        PUBLISHED_BACKWARD_HELPERS_V1._validate_parameter_gradient_classification_v1(
            records,
            frozen_parameter_contract=("frozen.gamma",),
            inactive_trainable_parameter_names=("active.weight",),
            active_zero_gradient_parameter_names=(),
        )
    with pytest.raises(AssertionError, match="active_parameter_gradient_none"):
        PUBLISHED_BACKWARD_HELPERS_V1._validate_parameter_gradient_classification_v1(
            records,
            frozen_parameter_contract=("frozen.gamma",),
            inactive_trainable_parameter_names=(),
            active_zero_gradient_parameter_names=(),
        )

    class ParameterIdentityFixture:
        def __init__(self, requires_grad: bool) -> None:
            self.requires_grad = requires_grad

    frozen = ParameterIdentityFixture(False)
    inactive = ParameterIdentityFixture(True)
    active = ParameterIdentityFixture(True)
    named = {"frozen.gamma": frozen, "inactive.weight": inactive, "active.weight": active}
    accepted = _validate_optimizer_parameter_identity_v1(
        named_parameters=named,
        optimizer_parameter_groups=({"params": [frozen, inactive, active]},),
    )
    assert accepted == _OptimizerParameterIdentityV1(3, 3, 1)

    with pytest.raises(
        AssertionError, match="optimizer_parameter_identity_duplicate"
    ):
        _validate_optimizer_parameter_identity_v1(
            named_parameters=named,
            optimizer_parameter_groups=({"params": [frozen, inactive, active, active]},),
        )
    with pytest.raises(
        AssertionError, match="optimizer_parameter_identity_coverage_mismatch"
    ):
        _validate_optimizer_parameter_identity_v1(
            named_parameters=named,
            optimizer_parameter_groups=({"params": [frozen, active]},),
        )
    foreign = ParameterIdentityFixture(True)
    with pytest.raises(
        AssertionError, match="optimizer_parameter_identity_coverage_mismatch"
    ):
        _validate_optimizer_parameter_identity_v1(
            named_parameters=named,
            optimizer_parameter_groups=({"params": [frozen, inactive, foreign]},),
        )


def test_real_checkpoint_train5_single_optimizer_step(tmp_path: Path) -> None:
    """Execute only after separate explicit authorization; opt-in alone is insufficient."""

    if os.environ.get(REAL_SINGLE_STEP_OPT_IN_V1) != "1":
        pytest.skip(
            f"{REAL_SINGLE_STEP_OPT_IN_V1}=1 is only the technical entry switch; "
            "separate explicit parameter-update authorization is required"
        )
    entered, result = _dispatch_real_runner_if_opted_in_v1(
        environ=os.environ,
        prerequisites=PUBLISHED_APPLICABLE_PREREQUISITES_V1,
        runner=lambda: _run_real_checkpoint_single_optimizer_step_v1(tmp_path),
    )
    assert entered is True and result is None
