"""Opt-in real-checkpoint Batch001 train5 backward-without-update V1.

Collection and ordinary test execution do not deserialize the real checkpoint,
instantiate the model, or run a real forward/backward.  The authorized path is
guarded by ``COVAPIE_RUN_BATCH001_CHECKPOINT_BACKWARD_NO_UPDATE=1``.
"""

from __future__ import annotations

import ast
import contextlib
from dataclasses import dataclass, fields
import hashlib
import importlib.util
import io
import math
import os
from pathlib import Path
import stat
from types import ModuleType
from typing import Iterator, Mapping, Sequence
from unittest import mock

import pytest


TASK_ID_V1 = "validate_covapie_batch001_checkpoint_backward_no_update_v1"
REAL_BACKWARD_OPT_IN_V1 = (
    "COVAPIE_RUN_BATCH001_CHECKPOINT_BACKWARD_NO_UPDATE"
)
EXPECTED_CHECKPOINT_SIZE_BYTES_V1 = 17_861_341
EXPECTED_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
EXPECTED_EPOCH0_TASK_IDS_V1 = (4, 4, 2, 0, 4)
EXPECTED_FORWARD_TEST_SIZE_BYTES_V1 = 51_136
EXPECTED_FORWARD_TEST_SHA256_V1 = (
    "2bac1568af875b200829f9854497a07587339c2587b501bf3d54ef7720bc2bdb"
)

ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = ROOT.parent / "covapie-state"
CACHE_ROOT = STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
PUBLISHED_FORWARD_TEST_PATH_V1 = (
    ROOT / "tests/test_covapie_batch001_checkpoint_forward_no_update_v1.py"
)

TARGET_RESIDUE_PARAMETER_NAME_V1 = (
    "ddpm.dynamics.target_residue_atom_condition_embedding"
)
ROLE_TASK_GENERATION_SEED_ANCHOR_PREFIXES_V1 = (
    "covapie_current11_auxiliary_model_v1.role_embedding.",
    "covapie_current11_auxiliary_model_v1.task_embedding.",
    "covapie_current11_auxiliary_model_v1.generation_state_embedding.",
    "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.",
    "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.",
)
PAIR_PREFIXES_V1 = (
    "covapie_current11_auxiliary_model_v1.pair_embedding.",
    "covapie_current11_auxiliary_model_v1.pair_logit.",
)
GEOMETRY_PREFIX_V1 = (
    "covapie_current11_auxiliary_model_v1.pre_post_geometry_head."
)
LEGACY_INACTIVE_RESIDUE_DECODER_PREFIX_V1 = "ddpm.dynamics.residue_decoder."
PREDEFINED_NOISE_SCHEDULE_SOURCE_PATH_V1 = (
    ROOT / "equivariant_diffusion/en_diffusion.py"
)
PUBLISHED_CONFIG_PATH_V1 = ROOT / "configs/crossdock_fullatom_joint.yml"
EXPECTED_NOISE_SCHEDULE_CLASS_NAME_V1 = "PredefinedNoiseSchedule"
EXPECTED_NOISE_SCHEDULE_NAME_V1 = "polynomial_2"
EXPECTED_NOISE_SCHEDULE_TIMESTEPS_V1 = 500
EXPECTED_NOISE_SCHEDULE_PRECISION_V1 = 5.0e-4
EXPECTED_NOISE_SCHEDULE_LOSS_TYPE_V1 = "l2"
FROZEN_PARAMETER_CONTRACT_V1 = ("ddpm.gamma.gamma",)
ACTIVE_ZERO_GRADIENT_CONTRACT_V1 = (
    "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.0.weight",
    "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.0.bias",
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


def _load_published_forward_helpers_v1() -> ModuleType:
    """Import the pinned helper module without importing any model owner."""

    size, sha256, _mode = _safe_file_identity(PUBLISHED_FORWARD_TEST_PATH_V1)
    assert size == EXPECTED_FORWARD_TEST_SIZE_BYTES_V1
    assert sha256 == EXPECTED_FORWARD_TEST_SHA256_V1
    spec = importlib.util.spec_from_file_location(
        "_covapie_published_checkpoint_forward_no_update_helpers_v1",
        PUBLISHED_FORWARD_TEST_PATH_V1,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        spec.loader.exec_module(module)
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""
    return module


# The pinned module imports only standard-library helpers and pytest at module
# scope.  Its torch/model/checkpoint imports remain inside test/helper calls.
PUBLISHED_FORWARD_HELPERS_V1 = _load_published_forward_helpers_v1()


def _evidence(message: str) -> None:
    print(f"COVAPIE_EVIDENCE {message}", flush=True)


def _names_with_prefixes(
    named_parameters: Mapping[str, object], prefixes: str | tuple[str, ...]
) -> tuple[str, ...]:
    return tuple(name for name in named_parameters if name.startswith(prefixes))


def _named_carrier_tensors(carrier: object) -> Iterator[tuple[str, object]]:
    import torch

    for name, value in carrier.model_input_batch.items():
        if isinstance(value, torch.Tensor):
            yield f"model_input_batch.{name}", value
    for field in fields(carrier.supervision):
        value = getattr(carrier.supervision, field.name)
        assert isinstance(value, torch.Tensor)
        yield f"supervision.{field.name}", value


def _assert_carrier_tensor_snapshot_unchanged(
    snapshot: Mapping[str, object], current: Iterator[tuple[str, object]]
) -> None:
    import torch

    current_map = dict(current)
    assert tuple(current_map) == tuple(snapshot)
    for name, before in snapshot.items():
        after = current_map[name]
        assert isinstance(before, torch.Tensor)
        assert isinstance(after, torch.Tensor)
        assert after.device.type == before.device.type == "cpu"
        assert after.dtype == before.dtype
        assert after.shape == before.shape
        before_bytes = before.detach().contiguous().view(torch.uint8)
        after_bytes = after.detach().contiguous().view(torch.uint8)
        assert after_bytes.equal(before_bytes), name


def _carrier_metadata(carrier: object) -> tuple[object, ...]:
    return (
        carrier.formal_split,
        carrier.epoch,
        carrier.task_schedule_seed,
        carrier.sample_identities,
        carrier.sample_training_admitted,
        carrier.model_training_activation_authorized,
        carrier.optimizer_population_eligible,
        carrier.training_scheduler_eligible,
        carrier.formal_validation_population_member,
        carrier.formal_test_population_member,
        carrier.training_scheduled_task_ids,
        carrier.preview_tensorization_task_ids,
    )


@dataclass(frozen=True)
class _PredefinedNoiseScheduleContractV1:
    schedule_class_name: str
    schedule_name: str
    timesteps: int
    precision: float
    loss_type: str
    frozen_parameter_names: tuple[str, ...]
    source_sha256: str
    config_sha256: str


def _published_predefined_noise_schedule_contract_v1(
) -> _PredefinedNoiseScheduleContractV1:
    """Read the published source/config contract without constructing a model."""

    import yaml

    source_size, source_sha256, _source_mode = _safe_file_identity(
        PREDEFINED_NOISE_SCHEDULE_SOURCE_PATH_V1
    )
    config_size, config_sha256, _config_mode = _safe_file_identity(
        PUBLISHED_CONFIG_PATH_V1
    )
    assert source_size > 0 and config_size > 0
    source_tree = ast.parse(
        PREDEFINED_NOISE_SCHEDULE_SOURCE_PATH_V1.read_text(encoding="utf-8")
    )
    schedule_classes = tuple(
        node
        for node in source_tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == EXPECTED_NOISE_SCHEDULE_CLASS_NAME_V1
    )
    assert len(schedule_classes) == 1
    gamma_assignments = []
    for node in ast.walk(schedule_classes[0]):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr == "gamma"
            and isinstance(node.value, ast.Call)
        ):
            continue
        function = node.value.func
        if not (
            isinstance(function, ast.Attribute)
            and function.attr == "Parameter"
            and isinstance(function.value, ast.Attribute)
            and function.value.attr == "nn"
            and isinstance(function.value.value, ast.Name)
            and function.value.value.id == "torch"
        ):
            continue
        requires_grad = tuple(
            keyword.value
            for keyword in node.value.keywords
            if keyword.arg == "requires_grad"
        )
        if (
            len(requires_grad) == 1
            and isinstance(requires_grad[0], ast.Constant)
            and requires_grad[0].value is False
        ):
            gamma_assignments.append(node)
    assert len(gamma_assignments) == 1

    config = yaml.safe_load(PUBLISHED_CONFIG_PATH_V1.read_text(encoding="utf-8"))
    diffusion = config["diffusion_params"]
    assert diffusion == {
        "diffusion_steps": EXPECTED_NOISE_SCHEDULE_TIMESTEPS_V1,
        "diffusion_noise_schedule": EXPECTED_NOISE_SCHEDULE_NAME_V1,
        "diffusion_noise_precision": EXPECTED_NOISE_SCHEDULE_PRECISION_V1,
        "diffusion_loss_type": EXPECTED_NOISE_SCHEDULE_LOSS_TYPE_V1,
        "normalize_factors": [1, 4],
    }
    assert EXPECTED_NOISE_SCHEDULE_NAME_V1 != "learned"
    return _PredefinedNoiseScheduleContractV1(
        schedule_class_name=EXPECTED_NOISE_SCHEDULE_CLASS_NAME_V1,
        schedule_name=EXPECTED_NOISE_SCHEDULE_NAME_V1,
        timesteps=EXPECTED_NOISE_SCHEDULE_TIMESTEPS_V1,
        precision=EXPECTED_NOISE_SCHEDULE_PRECISION_V1,
        loss_type=EXPECTED_NOISE_SCHEDULE_LOSS_TYPE_V1,
        frozen_parameter_names=FROZEN_PARAMETER_CONTRACT_V1,
        source_sha256=source_sha256,
        config_sha256=config_sha256,
    )


@dataclass(frozen=True)
class _ParameterGradientMetadataV1:
    name: str
    requires_grad: bool
    gradient_state: str
    produced_gradient_finite: bool


@dataclass(frozen=True)
class _ParameterGradientClassificationV1:
    frozen_parameter_names: tuple[str, ...]
    inactive_trainable_parameter_names: tuple[str, ...]
    active_parameter_names: tuple[str, ...]


def _parameter_gradient_metadata_v1(
    named_parameters: Mapping[str, object],
) -> tuple[_ParameterGradientMetadataV1, ...]:
    import torch

    records = []
    for name, parameter in named_parameters.items():
        gradient = parameter.grad
        if gradient is None:
            state = "none"
            finite = True
        else:
            state = (
                "all_zero"
                if int(torch.count_nonzero(gradient).item()) == 0
                else "nonzero"
            )
            finite = bool(torch.isfinite(gradient).all().item())
        records.append(_ParameterGradientMetadataV1(
            name=name,
            requires_grad=bool(parameter.requires_grad),
            gradient_state=state,
            produced_gradient_finite=finite,
        ))
    return tuple(records)


def _validate_parameter_gradient_classification_v1(
    records: Sequence[_ParameterGradientMetadataV1],
    *,
    frozen_parameter_contract: Sequence[str],
    inactive_trainable_parameter_names: Sequence[str],
    active_zero_gradient_parameter_names: Sequence[str],
) -> _ParameterGradientClassificationV1:
    """Fail closed across frozen, explicitly inactive, and active parameters."""

    record_map = {record.name: record for record in records}
    assert len(record_map) == len(records) and record_map
    frozen_contract = tuple(frozen_parameter_contract)
    inactive = tuple(inactive_trainable_parameter_names)
    active_zero_allowed = tuple(active_zero_gradient_parameter_names)
    assert len(set(frozen_contract)) == len(frozen_contract)
    assert len(set(inactive)) == len(inactive)
    assert len(set(active_zero_allowed)) == len(active_zero_allowed)
    assert set(frozen_contract) <= set(record_map)
    assert set(inactive) <= set(record_map)
    assert not (set(frozen_contract) & set(inactive))

    actual_frozen = tuple(
        name for name, record in record_map.items() if not record.requires_grad
    )
    assert set(actual_frozen) == set(frozen_contract), (
        "frozen_parameter_contract_mismatch",
        actual_frozen,
        frozen_contract,
    )
    for name in frozen_contract:
        record = record_map[name]
        assert record.gradient_state == "none", (
            "frozen_parameter_received_gradient",
            name,
        )

    for name in inactive:
        record = record_map[name]
        assert record.requires_grad is True
        assert record.gradient_state in ("none", "all_zero")
        assert record.produced_gradient_finite is True

    active = tuple(
        name
        for name in record_map
        if name not in set(frozen_contract) | set(inactive)
    )
    assert set(active_zero_allowed) <= set(active)
    for name in active:
        record = record_map[name]
        assert record.requires_grad is True
        assert record.gradient_state != "none", (
            "active_parameter_gradient_none",
            name,
        )
        assert record.produced_gradient_finite is True, (
            "active_parameter_gradient_nonfinite",
            name,
        )
        assert (
            record.gradient_state == "nonzero"
            or name in set(active_zero_allowed)
        ), ("unexpected_active_zero_gradient", name)
    return _ParameterGradientClassificationV1(
        frozen_parameter_names=tuple(sorted(frozen_contract)),
        inactive_trainable_parameter_names=tuple(sorted(inactive)),
        active_parameter_names=tuple(sorted(active)),
    )


@dataclass(frozen=True)
class _GradientGroupStatsV1:
    group_name: str
    parameter_tensor_count: int
    grad_none_count: int
    grad_all_zero_count: int
    grad_nonzero_count: int
    all_produced_gradients_finite: bool
    gradient_l2_norm: float
    gradient_max_abs: float
    none_parameter_names: tuple[str, ...]
    all_zero_parameter_names: tuple[str, ...]


def _gradient_group_stats(
    *,
    group_name: str,
    named_parameters: Mapping[str, object],
    parameter_names: Sequence[str],
) -> _GradientGroupStatsV1:
    import torch

    names = tuple(parameter_names)
    assert names
    assert len(names) == len(set(names))
    assert all(name in named_parameters for name in names)
    none_names = tuple(
        name for name in names if named_parameters[name].grad is None
    )
    produced = tuple(
        (name, named_parameters[name].grad)
        for name in names
        if named_parameters[name].grad is not None
    )
    zero_names = tuple(
        name
        for name, gradient in produced
        if int(torch.count_nonzero(gradient).item()) == 0
    )
    nonzero_count = len(produced) - len(zero_names)
    finite = all(
        bool(torch.isfinite(gradient).all().item())
        for _name, gradient in produced
    )
    squared_l2 = sum(
        float(gradient.detach().double().square().sum().item())
        for _name, gradient in produced
    )
    maximum = max(
        (
            float(gradient.detach().abs().max().item())
            for _name, gradient in produced
            if gradient.numel()
        ),
        default=0.0,
    )
    return _GradientGroupStatsV1(
        group_name=group_name,
        parameter_tensor_count=len(names),
        grad_none_count=len(none_names),
        grad_all_zero_count=len(zero_names),
        grad_nonzero_count=nonzero_count,
        all_produced_gradients_finite=finite,
        gradient_l2_norm=math.sqrt(squared_l2),
        gradient_max_abs=maximum,
        none_parameter_names=none_names,
        all_zero_parameter_names=zero_names,
    )


def _emit_gradient_stats(stats: _GradientGroupStatsV1) -> None:
    _evidence(
        f"gradient_group={stats.group_name} "
        f"parameter_tensors={stats.parameter_tensor_count} "
        f"grad_none={stats.grad_none_count} "
        f"grad_all_zero={stats.grad_all_zero_count} "
        f"grad_nonzero={stats.grad_nonzero_count} "
        f"all_produced_finite={str(stats.all_produced_gradients_finite).lower()} "
        f"l2_norm={stats.gradient_l2_norm:.17g} "
        f"max_abs={stats.gradient_max_abs:.17g} "
        f"none_names={stats.none_parameter_names} "
        f"all_zero_names={stats.all_zero_parameter_names}"
    )


class _ExecutionGuardV1:
    def __init__(self) -> None:
        self.forward_call_count = 0
        self.top_level_backward_call_count = 0
        self.internal_autograd_backward_call_count = 0
        self.backward_completed_count = 0
        self.backward_in_progress = False
        self.expected_loss: object | None = None
        self.forbidden_calls: list[str] = []

    def reject(self, name: str) -> None:
        self.forbidden_calls.append(name)
        raise AssertionError(f"forbidden operation invoked: {name}")


def _install_global_tripwires(
    stack: contextlib.ExitStack, *, guard: _ExecutionGuardV1
) -> None:
    import pytorch_lightning as pl
    import torch

    original_tensor_backward = torch.Tensor.backward
    original_autograd_backward = torch.autograd.backward

    def guarded_tensor_backward(
        tensor: object, *args: object, **kwargs: object
    ) -> None:
        if tensor is not guard.expected_loss:
            guard.reject("Tensor.backward.unbound_loss")
        if args or kwargs:
            guard.reject("Tensor.backward.nondefault_options")
        if guard.top_level_backward_call_count != 0:
            guard.reject("Tensor.backward.second_top_level_call")
        guard.top_level_backward_call_count = 1
        guard.backward_in_progress = True
        try:
            original_tensor_backward(tensor)
        finally:
            guard.backward_in_progress = False
        guard.backward_completed_count = 1

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

    def forbidden(name: str):
        def tripwire(*_args: object, **_kwargs: object) -> None:
            guard.reject(name)

        return tripwire

    direct_targets = (
        (torch.Tensor, "backward", guarded_tensor_backward),
        (torch.autograd, "backward", guarded_autograd_backward),
        (torch.autograd, "grad", forbidden("torch.autograd.grad")),
        (torch, "save", forbidden("torch.save")),
        (pl.Trainer, "__init__", forbidden("Trainer.__init__")),
        (pl.Trainer, "fit", forbidden("Trainer.fit")),
        (pl.Trainer, "validate", forbidden("Trainer.validate")),
        (pl.Trainer, "test", forbidden("Trainer.test")),
        (pl.Trainer, "predict", forbidden("Trainer.predict")),
        (
            pl.Trainer,
            "save_checkpoint",
            forbidden("Trainer.save_checkpoint"),
        ),
        (
            pl.LightningModule,
            "load_from_checkpoint",
            forbidden("LightningModule.load_from_checkpoint"),
        ),
    )
    for owner, attribute, replacement in direct_targets:
        stack.enter_context(mock.patch.object(owner, attribute, new=replacement))

    optimizer_classes = {
        value
        for value in vars(torch.optim).values()
        if isinstance(value, type)
        and issubclass(value, torch.optim.Optimizer)
    }
    for optimizer_class in optimizer_classes:
        if "__init__" in optimizer_class.__dict__:
            stack.enter_context(
                mock.patch.object(
                    optimizer_class,
                    "__init__",
                    new=forbidden(f"{optimizer_class.__name__}.__init__"),
                )
            )
        if "step" in optimizer_class.__dict__:
            stack.enter_context(
                mock.patch.object(
                    optimizer_class,
                    "step",
                    new=forbidden(f"{optimizer_class.__name__}.step"),
                )
            )


def _install_model_and_state_write_tripwires(
    stack: contextlib.ExitStack,
    *,
    model: object,
    guard: _ExecutionGuardV1,
) -> None:
    import torch

    def forbidden(name: str):
        def tripwire(*_args: object, **_kwargs: object) -> None:
            guard.reject(name)

        return tripwire

    for attribute in (
        "configure_optimizers",
        "training_step",
        "validation_step",
        "test_step",
        "load_state_dict",
    ):
        stack.enter_context(
            mock.patch.object(
                model,
                attribute,
                new=forbidden(f"model.{attribute}"),
            )
        )

    protected_storage_pointers = {
        tensor.untyped_storage().data_ptr()
        for tensor in tuple(model.parameters()) + tuple(model.buffers())
        if tensor.numel()
    }

    def protect_inplace_method(name: str, original: object):
        def guarded(tensor: object, *args: object, **kwargs: object):
            if (
                tensor.numel()
                and tensor.untyped_storage().data_ptr()
                in protected_storage_pointers
            ):
                guard.reject(f"model_state_write.{name}")
            return original(tensor, *args, **kwargs)

        return guarded

    # Loading/migration occurs before this point.  From the completed-load
    # snapshots onward, common direct and .data-based in-place writes to model
    # parameter/buffer storage fail immediately; exact snapshots remain the
    # definitive post-backward no-update check.
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
        stack.enter_context(
            mock.patch.object(
                torch.Tensor,
                attribute,
                new=protect_inplace_method(attribute, original),
            )
        )


def _install_exact_forward_guard(
    stack: contextlib.ExitStack,
    *,
    model: object,
    carrier: object,
    guard: _ExecutionGuardV1,
) -> None:
    original_forward = model.forward

    def guarded_forward(data: object):
        if data is not carrier:
            guard.reject("model.forward.unbound_carrier")
        if guard.forward_call_count != 0:
            guard.reject("model.forward.second_call")
        guard.forward_call_count = 1
        return original_forward(data)

    stack.enter_context(mock.patch.object(model, "forward", new=guarded_forward))


def test_parameter_gradient_classification_fail_closed_without_backward() -> None:
    """Regress classification with hand-authored metadata and no autograd."""

    contract = _published_predefined_noise_schedule_contract_v1()
    assert contract == _PredefinedNoiseScheduleContractV1(
        schedule_class_name="PredefinedNoiseSchedule",
        schedule_name="polynomial_2",
        timesteps=500,
        precision=5.0e-4,
        loss_type="l2",
        frozen_parameter_names=("ddpm.gamma.gamma",),
        source_sha256=contract.source_sha256,
        config_sha256=contract.config_sha256,
    )
    gamma = _ParameterGradientMetadataV1(
        name="ddpm.gamma.gamma",
        requires_grad=False,
        gradient_state="none",
        produced_gradient_finite=True,
    )
    inactive = _ParameterGradientMetadataV1(
        name="inactive.weight",
        requires_grad=True,
        gradient_state="none",
        produced_gradient_finite=True,
    )
    active = _ParameterGradientMetadataV1(
        name="active.weight",
        requires_grad=True,
        gradient_state="nonzero",
        produced_gradient_finite=True,
    )
    accepted = _validate_parameter_gradient_classification_v1(
        (gamma, inactive, active),
        frozen_parameter_contract=contract.frozen_parameter_names,
        inactive_trainable_parameter_names=(inactive.name,),
        active_zero_gradient_parameter_names=(),
    )
    assert accepted.frozen_parameter_names == (gamma.name,)
    assert accepted.inactive_trainable_parameter_names == (inactive.name,)
    assert accepted.active_parameter_names == (active.name,)

    gamma_unexpectedly_trainable = _ParameterGradientMetadataV1(
        name=gamma.name,
        requires_grad=True,
        gradient_state="none",
        produced_gradient_finite=True,
    )
    with pytest.raises(AssertionError, match="frozen_parameter_contract_mismatch"):
        _validate_parameter_gradient_classification_v1(
            (gamma_unexpectedly_trainable, active),
            frozen_parameter_contract=contract.frozen_parameter_names,
            inactive_trainable_parameter_names=(),
            active_zero_gradient_parameter_names=(),
        )

    undeclared_frozen_active = _ParameterGradientMetadataV1(
        name=active.name,
        requires_grad=False,
        gradient_state="none",
        produced_gradient_finite=True,
    )
    with pytest.raises(AssertionError, match="frozen_parameter_contract_mismatch"):
        _validate_parameter_gradient_classification_v1(
            (gamma, undeclared_frozen_active),
            frozen_parameter_contract=contract.frozen_parameter_names,
            inactive_trainable_parameter_names=(),
            active_zero_gradient_parameter_names=(),
        )

    active_none = _ParameterGradientMetadataV1(
        name=active.name,
        requires_grad=True,
        gradient_state="none",
        produced_gradient_finite=True,
    )
    with pytest.raises(AssertionError, match="active_parameter_gradient_none"):
        _validate_parameter_gradient_classification_v1(
            (gamma, active_none),
            frozen_parameter_contract=contract.frozen_parameter_names,
            inactive_trainable_parameter_names=(),
            active_zero_gradient_parameter_names=(),
        )

    for nonfinite_kind in ("nan", "inf"):
        nonfinite_active = _ParameterGradientMetadataV1(
            name=f"active_{nonfinite_kind}.weight",
            requires_grad=True,
            gradient_state="nonzero",
            produced_gradient_finite=False,
        )
        with pytest.raises(
            AssertionError, match="active_parameter_gradient_nonfinite"
        ):
            _validate_parameter_gradient_classification_v1(
                (gamma, nonfinite_active),
                frozen_parameter_contract=contract.frozen_parameter_names,
                inactive_trainable_parameter_names=(),
                active_zero_gradient_parameter_names=(),
            )

    _evidence(
        "gradient_classification_fixture=PASS "
        "real_checkpoint_loaded=false real_model_constructed=false "
        "backward_calls=0 autograd_grad_calls=0 "
        "legal_frozen_gamma_accepted=true "
        "trainable_gamma_rejected=true undeclared_frozen_rejected=true "
        "active_none_rejected=true nan_gradient_rejected=true "
        "inf_gradient_rejected=true"
    )


def test_checkpoint_identity_mismatch_rejects_before_deserialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The failure path cannot deserialize an identity-mismatched candidate."""

    from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration

    candidate = tmp_path / "identity-mismatch.ckpt"
    candidate.write_bytes(b"not-the-published-checkpoint")
    deserialization_calls = 0

    def forbidden_load(*_args: object, **_kwargs: object) -> None:
        nonlocal deserialization_calls
        deserialization_calls += 1
        raise AssertionError("mismatched checkpoint reached torch.load")

    monkeypatch.setattr(migration.torch, "load", forbidden_load)
    with pytest.raises(
        ValueError,
        match="^COVAPIE_CURRENT11_CHECKPOINT_MIGRATION_V1_ERROR$",
    ):
        migration.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=candidate
        )
    assert deserialization_calls == 0


def test_real_checkpoint_train5_forward_backward_without_update(
    tmp_path: Path,
) -> None:
    """Run one real train5 forward and one total-loss backward, with no update."""

    if os.environ.get(REAL_BACKWARD_OPT_IN_V1) != "1":
        pytest.skip(
            f"set {REAL_BACKWARD_OPT_IN_V1}=1 for real checkpoint backward"
        )

    stage = "real_imports"
    guard = _ExecutionGuardV1()
    invariance_reached = False
    _evidence(
        "opt_in=1 run=START real_forward_budget=1 "
        "total_loss_backward_budget=1 optimizer_budget=0"
    )
    try:
        import torch
        from covalent_ext import (
            covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
            as activation_owner,
        )
        from covalent_ext import (
            covapie_batch001_feature_post_use_preflight_v1 as preflight_owner,
        )
        from covalent_ext import (
            covapie_batch001_hidden_post_forward_adapter_v1 as adapter,
        )
        from covalent_ext import (
            covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
            as checkpoint_locator,
        )
        from covalent_ext import (
            covapie_current11_checkpoint_migration_v1 as migration_owner,
        )
        from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
            CovapieCurrent11LossWeightsV1,
        )
        from equivariant_diffusion.en_diffusion import PredefinedNoiseSchedule

        stage = "source_and_checkpoint_identity"
        schedule_contract = _published_predefined_noise_schedule_contract_v1()
        exact1_size, exact1_sha, exact1_mode = _safe_file_identity(
            Path(__file__).resolve()
        )
        published_forward_identity = _safe_file_identity(
            PUBLISHED_FORWARD_TEST_PATH_V1
        )
        assert published_forward_identity[:2] == (
            EXPECTED_FORWARD_TEST_SIZE_BYTES_V1,
            EXPECTED_FORWARD_TEST_SHA256_V1,
        )
        source_identity_before = (
            adapter.verify_covapie_batch001_hidden_post_forward_adapter_sources_v1(
                repository_root=ROOT
            )
            + PUBLISHED_FORWARD_HELPERS_V1._verify_additional_bound_sources()
        )
        checkpoint_path = ROOT / checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1
        checkpoint_size, checkpoint_sha, checkpoint_mode = _safe_file_identity(
            checkpoint_path
        )
        assert checkpoint_size == EXPECTED_CHECKPOINT_SIZE_BYTES_V1
        assert checkpoint_sha == EXPECTED_CHECKPOINT_SHA256_V1
        assert checkpoint_size == (
            migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SIZE_BYTES_V1
        )
        assert checkpoint_sha == (
            migration_owner.COVAPIE_CURRENT11_LEGACY_CHECKPOINT_SHA256_V1
        )
        _evidence(
            f"exact1_candidate_identity=PASS bytes={exact1_size} "
            f"sha256={exact1_sha} mode={exact1_mode:04o}"
        )
        _evidence(
            "source_bindings=PASS "
            f"published_forward_sha256={published_forward_identity[1]} "
            f"bound_source_count={len(source_identity_before)} "
            f"noise_schedule_source_sha256={schedule_contract.source_sha256} "
            f"noise_schedule_config_sha256={schedule_contract.config_sha256}"
        )
        _evidence(
            "checkpoint_candidate_identity=PASS "
            f"path={checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1} "
            f"bytes={checkpoint_size} sha256={checkpoint_sha} "
            f"mode={checkpoint_mode:04o} deserialized=false"
        )

        with contextlib.ExitStack() as safety_stack:
            stage = "global_tripwire_install"
            _install_global_tripwires(safety_stack, guard=guard)
            _evidence(
                "global_tripwires=INSTALLED optimizer=true step=true "
                "Trainer=true save=true autograd_grad=true "
                "exact_loss_backward_only=true"
            )

            stage = "checkpoint_load"
            checkpoint = (
                migration_owner.load_covapie_current11_legacy_checkpoint_v1(
                    checkpoint_path=checkpoint_path
                )
            )
            checkpoint_state = checkpoint["state_dict"]
            checkpoint_diffusion = checkpoint["legacy_constructor"][
                "diffusion_params"
            ]
            assert checkpoint["checkpoint_size_bytes"] == checkpoint_size
            assert checkpoint["checkpoint_sha256"] == checkpoint_sha
            assert checkpoint["checkpoint_state_dict_key_count"] == len(
                checkpoint_state
            )
            assert checkpoint_diffusion["diffusion_steps"] == (
                schedule_contract.timesteps
            )
            assert checkpoint_diffusion["diffusion_noise_schedule"] == (
                schedule_contract.schedule_name
            )
            assert checkpoint_diffusion["diffusion_noise_precision"] == (
                schedule_contract.precision
            )
            assert checkpoint_diffusion["diffusion_loss_type"] == (
                schedule_contract.loss_type
            )
            _evidence(
                "checkpoint_load=PASS "
                f"payload_type={checkpoint['checkpoint_payload_type']} "
                f"legacy_state_keys={len(checkpoint_state)} "
                f"noise_schedule={schedule_contract.schedule_name} "
                f"noise_schedule_precision={schedule_contract.precision}"
            )

            stage = "model_construction_and_strict_migration"
            model = PUBLISHED_FORWARD_HELPERS_V1._instantiate_exact_adapter(
                checkpoint=checkpoint, runtime_root=tmp_path
            )
            migration = migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
                model=model,
                checkpoint_state_dict=checkpoint_state,
            )
            migrated_state = model.state_dict()
            target_keys = set(migrated_state)
            checkpoint_keys = set(checkpoint_state)
            shared_keys = target_keys & checkpoint_keys
            target_only = target_keys - checkpoint_keys
            assert migration["checkpoint_key_count"] == len(checkpoint_keys)
            assert migration["target_model_key_count"] == len(target_keys)
            assert migration["shared_key_count"] == len(shared_keys)
            assert migration["target_only_key_count"] == len(target_only)
            assert migration["checkpoint_only_key_count"] == 0
            assert migration["shared_shape_mismatch_count"] == 0
            assert migration["shared_checkpoint_tensor_equality_count"] == len(
                shared_keys
            )
            assert migration["migration_missing_keys"] == ()
            assert migration["migration_unexpected_keys"] == ()
            assert migration["full_target_strict_load"] is True
            assert set(migration["target_only_exact_keys"]) == set(
                migration_owner.LEGACY_ALLOWED_NEW_EXACT_KEYS_V1
            )
            assert set(migration["target_only_auxiliary_keys"]) == {
                key
                for key in target_only
                if key.startswith(
                    migration_owner.LEGACY_ALLOWED_NEW_PREFIXES_V1
                )
            }
            assert target_only == (
                set(migration["target_only_exact_keys"])
                | set(migration["target_only_auxiliary_keys"])
            )
            for key in shared_keys:
                assert migrated_state[key].detach().cpu().equal(
                    checkpoint_state[key].detach().cpu()
                ), key
            _evidence(
                "checkpoint_migration=PASS "
                f"checkpoint_keys={migration['checkpoint_key_count']} "
                f"target_keys={migration['target_model_key_count']} "
                f"shared_keys={migration['shared_key_count']} "
                f"shared_equal={migration['shared_checkpoint_tensor_equality_count']} "
                f"target_only={migration['target_only_key_count']} "
                f"new_exact={len(migration['target_only_exact_keys'])} "
                f"new_auxiliary={len(migration['target_only_auxiliary_keys'])} "
                "checkpoint_only=0 shape_mismatch=0 strict=true"
            )

            stage = "model_configuration_and_loaded_state_snapshot"
            dynamics = model.ddpm.dynamics
            assert type(model) is (
                adapter.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1
            )
            assert model.device == torch.device("cpu")
            assert model.mode == "pocket_conditioning"
            assert model.pocket_representation == "full-atom"
            assert model.atom_nf == model.aa_nf == 10
            assert model.virtual_nodes is False
            assert model.auxiliary_loss is False
            assert model.ddpm.loss_type == "l2"
            assert model.ddpm.T == 500
            assert model.ddpm.norm_values == [1, 4]
            assert type(model.ddpm.gamma) is PredefinedNoiseSchedule
            assert type(model.ddpm.gamma).__name__ == (
                schedule_contract.schedule_class_name
            )
            assert model.ddpm.gamma.timesteps == schedule_contract.timesteps
            assert dynamics.target_residue_atom_conditioning is True
            assert dynamics.egnn.hidden_nf == 128
            assert dynamics.egnn.n_layers == 5
            assert model.covapie_current11_auxiliary_model_v1.joint_nf == 32
            assert model._trainer is None
            assert model.current_epoch == 0
            model.train()
            assert model.training is True and model.ddpm.training is True
            named_parameters_after_loading = dict(model.named_parameters())
            frozen_names_after_loading = tuple(
                name
                for name, parameter in named_parameters_after_loading.items()
                if not parameter.requires_grad
            )
            assert set(frozen_names_after_loading) == set(
                schedule_contract.frozen_parameter_names
            )
            frozen_gamma = named_parameters_after_loading[
                FROZEN_PARAMETER_CONTRACT_V1[0]
            ]
            assert frozen_gamma.requires_grad is False
            assert frozen_gamma.grad is None
            requires_grad_flags_after_loading = {
                name: parameter.requires_grad
                for name, parameter in named_parameters_after_loading.items()
            }
            parameters_after_loading = (
                PUBLISHED_FORWARD_HELPERS_V1._snapshot_named_tensors(
                    model.named_parameters()
                )
            )
            buffers_after_loading = (
                PUBLISHED_FORWARD_HELPERS_V1._snapshot_named_tensors(
                    model.named_buffers()
                )
            )
            state_fingerprint_after_loading = (
                PUBLISHED_FORWARD_HELPERS_V1._model_state_fingerprint(
                    parameters_after_loading, buffers_after_loading
                )
            )
            assert PUBLISHED_FORWARD_HELPERS_V1._all_gradients_none(model)
            _install_model_and_state_write_tripwires(
                safety_stack, model=model, guard=guard
            )
            _evidence(
                "loaded_state_snapshot=PASS "
                f"parameter_tensors={len(parameters_after_loading)} "
                f"registered_buffers={len(buffers_after_loading)} "
                f"fingerprint={state_fingerprint_after_loading} "
                "all_grad_none=true no_update_boundary=START "
                f"noise_schedule_type={type(model.ddpm.gamma).__name__} "
                f"frozen_parameter_count={len(frozen_names_after_loading)} "
                f"frozen_parameter_names={frozen_names_after_loading} "
                "frozen_gamma_requires_grad=false frozen_gamma_grad_none=true"
            )

            stage = "real_train5_carrier"
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
            assert carrier.epoch == 0
            assert carrier.task_schedule_seed == 0
            assert carrier.training_scheduled_task_ids == EXPECTED_EPOCH0_TASK_IDS_V1
            assert carrier.preview_tensorization_task_ids == EXPECTED_EPOCH0_TASK_IDS_V1
            assert tuple(carrier.supervision.canonical_task_id.tolist()) == (
                EXPECTED_EPOCH0_TASK_IDS_V1
            )
            assert len(carrier.sample_identities) == 5
            assert sum(
                row.preflight_effective_hidden_post_eligible
                for row in preflight_rows
            ) == 5
            carrier_tensor_snapshot = (
                PUBLISHED_FORWARD_HELPERS_V1._snapshot_named_tensors(
                    _named_carrier_tensors(carrier)
                )
            )
            carrier_metadata_before = _carrier_metadata(carrier)
            _install_exact_forward_guard(
                safety_stack,
                model=model,
                carrier=carrier,
                guard=guard,
            )
            _evidence(
                "train5_carrier=PASS "
                f"epoch={carrier.epoch} "
                f"task_schedule_seed={carrier.task_schedule_seed} "
                f"tasks={carrier.training_scheduled_task_ids} "
                f"carrier_tensor_count={len(carrier_tensor_snapshot)} "
                f"carrier_fingerprint={carrier_fingerprint_before}"
            )

            stage = "pre_forward_gradient_context"
            assert torch.is_grad_enabled() is True
            assert torch.is_inference_mode_enabled() is False
            assert all(parameter.grad is None for parameter in model.parameters())
            weights = model.covapie_current11_loss_weights
            assert weights == CovapieCurrent11LossWeightsV1(
                base_diffusion=1.0,
                covalent_pair_prediction=1.0,
                pre_post_geometry=0.0,
                covalent_pair_contrastive=0.1,
            )
            _evidence(
                "pre_forward_gradient_context=PASS grad_enabled=true "
                "inference_mode=false all_parameter_grad_none=true "
                f"loss_weights={weights}"
            )

            stage = "real_forward"
            _evidence("real_train5_forward=START completed=0 budget=1")
            output = model(carrier)
            _evidence("real_train5_forward=COMPLETED completed=1 budget=1")
            assert guard.forward_call_count == 1

            stage = "loss_validation"
            loss_total = output.loss_output.loss_total
            assert loss_total.ndim == 0
            assert bool(torch.isfinite(loss_total).item())
            assert loss_total.requires_grad is True
            assert loss_total.grad_fn is not None
            raw_losses = dict(PUBLISHED_FORWARD_HELPERS_V1._loss_values(output))
            valid_counts = dict(PUBLISHED_FORWARD_HELPERS_V1._loss_counts(output))
            assert all(math.isfinite(value) for value in raw_losses.values())
            assert valid_counts == {
                "base": 5,
                "pair": 5,
                "geometry": 5,
                "contrastive": 5,
            }
            timesteps = output.diffusion_trace.diffusion_timestep_int
            assert timesteps.dtype == torch.long
            assert tuple(timesteps.shape) == (5,)
            assert bool(((timesteps >= 0) & (timesteps <= model.ddpm.T)).all().item())
            assert output.supervision is carrier.supervision
            diagnostics = (
                output.loss_output.pair_prediction_per_sample_detached,
                output.loss_output.pre_post_geometry_per_sample_detached,
                output.loss_output.pair_contrastive_per_sample_detached,
            )
            assert all(not value.requires_grad for value in diagnostics)
            assert all(value.grad_fn is None for value in diagnostics)
            _evidence(
                "loss_total_contract=PASS scalar=true finite=true "
                "requires_grad=true grad_fn_nonempty=true "
                f"tasks={tuple(carrier.supervision.canonical_task_id.tolist())} "
                f"timesteps={tuple(timesteps.tolist())} "
                f"raw_losses={raw_losses} valid_counts={valid_counts} "
                f"loss_weights={weights} diagnostics_detached=true"
            )

            stage = "real_total_loss_backward"
            guard.expected_loss = loss_total
            _evidence(
                "real_total_loss_backward=START top_level_completed=0 budget=1 "
                "entry=output.loss_output.loss_total.backward"
            )
            output.loss_output.loss_total.backward()
            _evidence(
                "real_total_loss_backward=COMPLETED top_level_completed=1 "
                "budget=1 retain_graph=false create_graph=false"
            )
            assert guard.top_level_backward_call_count == 1
            assert guard.internal_autograd_backward_call_count == 1
            assert guard.backward_completed_count == 1

            stage = "post_backward_state_invariance"
            named_parameters = dict(model.named_parameters())
            assert {
                name: parameter.requires_grad
                for name, parameter in named_parameters.items()
            } == requires_grad_flags_after_loading
            frozen_gamma_after_backward = named_parameters[
                FROZEN_PARAMETER_CONTRACT_V1[0]
            ]
            assert frozen_gamma_after_backward.requires_grad is False
            assert frozen_gamma_after_backward.grad is None
            PUBLISHED_FORWARD_HELPERS_V1._assert_snapshot_unchanged(
                parameters_after_loading, model.named_parameters()
            )
            PUBLISHED_FORWARD_HELPERS_V1._assert_snapshot_unchanged(
                buffers_after_loading, model.named_buffers()
            )
            final_parameters = (
                PUBLISHED_FORWARD_HELPERS_V1._snapshot_named_tensors(
                    model.named_parameters()
                )
            )
            final_buffers = PUBLISHED_FORWARD_HELPERS_V1._snapshot_named_tensors(
                model.named_buffers()
            )
            assert PUBLISHED_FORWARD_HELPERS_V1._model_state_fingerprint(
                final_parameters, final_buffers
            ) == state_fingerprint_after_loading
            _assert_carrier_tensor_snapshot_unchanged(
                carrier_tensor_snapshot, _named_carrier_tensors(carrier)
            )
            assert _carrier_metadata(carrier) == carrier_metadata_before
            carrier_fingerprint_after, _rows = (
                preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(
                    carrier
                )
            )
            assert carrier_fingerprint_after == carrier_fingerprint_before
            assert guard.forbidden_calls == []
            assert guard.forward_call_count == 1
            assert guard.top_level_backward_call_count == 1
            assert guard.internal_autograd_backward_call_count == 1
            assert guard.backward_completed_count == 1
            invariance_reached = True
            _evidence(
                "post_backward_state_invariance=PASS "
                "parameters_unchanged=true buffers_unchanged=true "
                "requires_grad_flags_unchanged=true "
                "frozen_gamma_requires_grad=false frozen_gamma_grad_none=true "
                "carrier_tensors_unchanged=true carrier_metadata_unchanged=true "
                "carrier_fingerprint_unchanged=true "
                "parameter_reload=false manual_state_write=false "
                "optimizer_created=false optimizer_step=false "
                "gradients_preserved_for_classification=true"
            )

            stage = "gradient_groups"
            legacy_names = tuple(
                name for name in named_parameters if name in checkpoint_state
            )
            target_names = (TARGET_RESIDUE_PARAMETER_NAME_V1,)
            encoding_names = _names_with_prefixes(
                named_parameters,
                ROLE_TASK_GENERATION_SEED_ANCHOR_PREFIXES_V1,
            )
            pair_names = _names_with_prefixes(named_parameters, PAIR_PREFIXES_V1)
            geometry_names = _names_with_prefixes(
                named_parameters, GEOMETRY_PREFIX_V1
            )
            groups = (
                ("legacy_ddpm_egnn", legacy_names),
                ("target_residue_condition_embedding", target_names),
                ("role_task_generation_seed_anchor_encoding", encoding_names),
                ("pair_embedding_pair_logit", pair_names),
                ("pre_post_geometry_head", geometry_names),
            )
            assert tuple(len(names) for _group, names in groups) == (
                116,
                1,
                8,
                6,
                4,
            )
            flattened = tuple(name for _group, names in groups for name in names)
            assert len(flattened) == len(set(flattened)) == len(named_parameters) == 135
            assert set(flattened) == set(named_parameters)
            stats = tuple(
                _gradient_group_stats(
                    group_name=group_name,
                    named_parameters=named_parameters,
                    parameter_names=names,
                )
                for group_name, names in groups
            )
            for item in stats:
                _emit_gradient_stats(item)
                assert item.all_produced_gradients_finite
                assert math.isfinite(item.gradient_l2_norm)
                assert math.isfinite(item.gradient_max_abs)
            stats_by_name = {item.group_name: item for item in stats}
            assert stats_by_name["legacy_ddpm_egnn"].grad_nonzero_count > 0
            assert stats_by_name[
                "target_residue_condition_embedding"
            ].grad_nonzero_count == 1
            assert stats_by_name[
                "role_task_generation_seed_anchor_encoding"
            ].grad_nonzero_count > 0
            assert stats_by_name["pair_embedding_pair_logit"].grad_none_count == 0
            assert stats_by_name["pair_embedding_pair_logit"].grad_nonzero_count > 0
            assert stats_by_name["pre_post_geometry_head"].grad_nonzero_count == 0

            seed_branch_active = bool(
                carrier.supervision.ligand_minimal_seed_or_anchor_valid[
                    carrier.model_input_batch["lig_mask"]
                ].any().item()
            )
            inactive_trainable_names = set(geometry_names) | {
                name
                for name in legacy_names
                if name.startswith(LEGACY_INACTIVE_RESIDUE_DECODER_PREFIX_V1)
            }
            if not seed_branch_active:
                inactive_trainable_names.update(
                    name
                    for name in encoding_names
                    if name.startswith(
                        "covapie_current11_auxiliary_model_v1."
                        "seed_indicator_embedding."
                    )
                )
            gradient_classification = (
                _validate_parameter_gradient_classification_v1(
                    _parameter_gradient_metadata_v1(named_parameters),
                    frozen_parameter_contract=(
                        schedule_contract.frozen_parameter_names
                    ),
                    inactive_trainable_parameter_names=tuple(
                        sorted(inactive_trainable_names)
                    ),
                    active_zero_gradient_parameter_names=(
                        ACTIVE_ZERO_GRADIENT_CONTRACT_V1
                    ),
                )
            )
            assert gradient_classification.frozen_parameter_names == (
                FROZEN_PARAMETER_CONTRACT_V1
            )
            assert len(gradient_classification.active_parameter_names) > 0
            produced_gradients = tuple(
                parameter.grad
                for parameter in named_parameters.values()
                if parameter.grad is not None
            )
            assert produced_gradients
            assert all(
                bool(torch.isfinite(gradient).all().item())
                for gradient in produced_gradients
            )
            _evidence(
                "gradient_interpretation=PASS "
                "base_model_path_nonzero=true pair_prediction_path_nonzero=true "
                f"seed_branch_active={str(seed_branch_active).lower()} "
                f"frozen_parameter_count={len(gradient_classification.frozen_parameter_names)} "
                f"inactive_trainable_parameter_count={len(gradient_classification.inactive_trainable_parameter_names)} "
                f"active_parameter_count={len(gradient_classification.active_parameter_names)} "
                f"frozen_parameter_names={gradient_classification.frozen_parameter_names} "
                "legacy_residue_decoder_none_allowed_because_pocket_decoder_output_is_not_consumed_by_total_loss=true "
                "zero_initialized_anchor_upstream_zero_allowed=true "
                "geometry_weight_zero=true geometry_nonzero_gradients=0 "
                "geometry_training_gradient_accepted=false "
                "unexpected_active_path_none=false all_actual_gradients_finite=true"
            )

            stage = "final_source_checkpoint_tripwire_integrity"
            source_identity_after = (
                adapter.verify_covapie_batch001_hidden_post_forward_adapter_sources_v1(
                    repository_root=ROOT
                )
                + PUBLISHED_FORWARD_HELPERS_V1._verify_additional_bound_sources()
            )
            assert source_identity_after == source_identity_before
            assert _safe_file_identity(PUBLISHED_FORWARD_TEST_PATH_V1) == (
                published_forward_identity
            )
            assert _safe_file_identity(Path(__file__).resolve()) == (
                exact1_size,
                exact1_sha,
                exact1_mode,
            )
            assert _safe_file_identity(checkpoint_path) == (
                checkpoint_size,
                checkpoint_sha,
                checkpoint_mode,
            )
            _evidence(
                "final_integrity=PASS "
                "sources_unchanged=true checkpoint_unchanged=true "
                "exact1_unchanged_during_run=true"
            )
            _evidence(
                "tripwire_result=PASS forbidden_invocations=0 "
                "forward_calls=1 top_level_backward_calls=1 "
                "internal_autograd_backward_calls=1 optimizer_created=false "
                "optimizer_step=false Trainer=false checkpoint_saved=false "
                "manual_state_write=false training_loop=false"
            )

        stage = "complete"
        _evidence(
            "run=PASS real_forward_count=1 total_loss_backward_count=1 "
            "lifecycle_real_forward_count=2 "
            "lifecycle_total_loss_backward_count=2 "
            "parameter_update_count=0 geometry_gradient_acceptance=not_claimed"
        )
        print(f"TASK_ID={TASK_ID_V1}", flush=True)
        print(
            "execution=forward:1,total_loss_backward:1,optimizer_created:false,"
            "optimizer_step:false,Trainer:false,training_loop:false,save:false",
            flush=True,
        )
        print(
            "state=parameters_unchanged:true,buffers_unchanged:true,"
            "carrier_unchanged:true,sources_unchanged:true,"
            "checkpoint_unchanged:true",
            flush=True,
        )
        print(
            "interpretation=backward_connectivity_and_finiteness_validated:true,"
            "formal_training:false,production_loss_weights_finalized:false,"
            "geometry_supervision_gradient_accepted:false",
            flush=True,
        )
        print(
            "validation_flags=corrected_backward_opt_in_test_pass:true,"
            "frozen_parameter_classification_pass:true,"
            "active_gradient_path_check_pass:true,"
            "all_observed_gradients_finite:true,"
            "post_backward_invariance_executed:true,"
            "requires_grad_flags_unchanged:true",
            flush=True,
        )
        print(
            "lifecycle=this_round_forward:1,this_round_backward:1,"
            "task_total_forward:2,task_total_backward:2",
            flush=True,
        )
    except BaseException as error:
        _evidence(
            f"run=FAIL stage={stage} error_type={type(error).__name__} "
            f"real_forward_count={guard.forward_call_count} "
            "real_forward_remaining="
            f"{1 - min(guard.forward_call_count, 1)} "
            "top_level_backward_count="
            f"{guard.top_level_backward_call_count} "
            "backward_completed_count="
            f"{guard.backward_completed_count} "
            "lifecycle_real_forward_count="
            f"{1 + min(guard.forward_call_count, 1)} "
            "lifecycle_total_loss_backward_count="
            f"{1 + min(guard.backward_completed_count, 1)} "
            "post_backward_invariance="
            f"{'reached' if invariance_reached else 'not_reached'}"
        )
        raise
