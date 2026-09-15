"""Opt-in train10 checkpoint backward-without-update validation V1.

Collection and ordinary execution are non-model-only.  The sole real node is
guarded by ``COVAPIE_RUN_TRAIN10_CHECKPOINT_BACKWARD_NO_UPDATE=1`` before any
checkpoint, carrier, model, or runtime-directory operation.  A separately
authorized real run is bounded to one checkpoint load, one train10 carrier,
one grad-enabled forward, and one ``loss_total.backward()``.  It never creates
an optimizer or Trainer and never updates or saves model state.
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


TASK_ID_V1 = "validate_covapie_train10_checkpoint_backward_no_update_v1"
REAL_BACKWARD_OPT_IN_V1 = (
    "COVAPIE_RUN_TRAIN10_CHECKPOINT_BACKWARD_NO_UPDATE"
)
EXPECTED_REPOSITORY_BASELINE_V1 = (
    "945ed56b98e0d7f21e0362377b548eb45be01e35"
)
EXPECTED_CHECKPOINT_SIZE_BYTES_V1 = 17_861_341
EXPECTED_CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
MODEL_INITIALIZATION_SEED_V1 = 20_260_821
DIFFUSION_FORWARD_SEED_V1 = 11_030_037
EXPECTED_EPOCH0_TASK_IDS_V1 = (4, 4, 2, 0, 4, 4, 0, 0, 4, 4)

PUBLISHED_TRAIN10_FORWARD_RELATIVE_V1 = (
    "tests/test_covapie_train10_checkpoint_forward_no_update_v1.py"
)
PUBLISHED_BATCH001_BACKWARD_RELATIVE_V1 = (
    "tests/test_covapie_batch001_checkpoint_backward_no_update_v1.py"
)
PUBLISHED_TRAIN10_FORWARD_SIZE_V1 = 127_015
PUBLISHED_TRAIN10_FORWARD_SHA256_V1 = (
    "d602987f0a4d76799427213e62205cb70505064c93e126fd3c8a3bae80b46b79"
)
PUBLISHED_BATCH001_BACKWARD_SIZE_V1 = 58_548
PUBLISHED_BATCH001_BACKWARD_SHA256_V1 = (
    "6a9590c9ed5f87f0fddad2a0844a1c9b2e02f7b9c1aee5a80fa0e4621ef8640f"
)

CANONICAL_EXACT5_V1 = (
    (0, "warhead_only", "A", (2,)),
    (1, "linker_plus_warhead", "B", (1, 2)),
    (2, "scaffold_plus_warhead", "B2", (0, 2)),
    (3, "scaffold_only", "B3", (0,)),
    (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
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


# This file is prepared outside the repository and must not infer roots from
# __file__.  The same explicit roots remain valid after eventual publication.
ROOT = _required_canonical_directory_v1("COVAPIE_TEST_REPOSITORY_ROOT")
STATE_ROOT = _required_canonical_directory_v1("COVAPIE_TEST_STATE_ROOT")
CACHE_ROOT = _required_canonical_directory_v1("COVAPIE_TEST_CACHE_ROOT")
assert CACHE_ROOT == STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"


DIRECT_BOUND_SOURCE_SHA256_V1 = (
    (
        PUBLISHED_TRAIN10_FORWARD_RELATIVE_V1,
        PUBLISHED_TRAIN10_FORWARD_SHA256_V1,
    ),
    (
        PUBLISHED_BATCH001_BACKWARD_RELATIVE_V1,
        PUBLISHED_BATCH001_BACKWARD_SHA256_V1,
    ),
    (
        "src/covalent_ext/covapie_train10_hidden_post_forward_adapter_v1.py",
        "5beaa700e2e5af87265c022a919dddfe1c8054114a45415adc416e5fe25fa40d",
    ),
    (
        "src/covalent_ext/covapie_train10_cpu_batch_composer_v1.py",
        "5c5e7fee4804586e0c6d2a9bdf39a301dd154da92ff2d029f971d6b2b77d2ddd",
    ),
    (
        "src/covalent_ext/covapie_current11_checkpoint_migration_v1.py",
        "fc36fb23844e6e5d2be2e1e43fcd0afe580d8b86faacca31bd69b8fe70f75ef3",
    ),
    (
        "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py",
        "bb797fdb0c96ce669a348a3ddf3975771398263cdfa2a22f3d9c55b0011271cd",
    ),
    (
        "equivariant_diffusion/en_diffusion.py",
        "46a00db84d05ea568786b99b42b1b20c448cec8a99638d162b23b59794172b10",
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


def _verify_direct_bound_sources_v1() -> tuple[tuple[str, str], ...]:
    observed = []
    for relative, expected_sha256 in DIRECT_BOUND_SOURCE_SHA256_V1:
        size, actual_sha256, _mode = _safe_file_identity_v1(ROOT / relative)
        assert size > 0 and actual_sha256 == expected_sha256, relative
        observed.append((relative, actual_sha256))
    return tuple(observed)


def _load_published_test_module_v1(
    *, relative: str, size: int, sha256: str, module_name: str
) -> ModuleType:
    """Load a pinned test helper silently and register it before execution."""

    existing = sys.modules.get(module_name)
    if existing is not None:
        assert Path(existing.__file__).resolve(strict=True) == ROOT / relative
        return existing
    path = ROOT / relative
    assert _safe_file_identity_v1(path)[:2] == (size, sha256)
    specification = importlib.util.spec_from_file_location(module_name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    assert stdout.getvalue() == "" and stderr.getvalue() == ""
    assert Path(module.__file__).resolve(strict=True) == path
    return module


def _forward_tools_v1() -> ModuleType:
    module = _load_published_test_module_v1(
        relative=PUBLISHED_TRAIN10_FORWARD_RELATIVE_V1,
        size=PUBLISHED_TRAIN10_FORWARD_SIZE_V1,
        sha256=PUBLISHED_TRAIN10_FORWARD_SHA256_V1,
        module_name="_covapie_published_train10_forward_tools_for_backward_v1",
    )
    for helper in (
        "_load_real_path_dependencies_v1",
        "_instantiate_train10_model_v1",
        "_assert_scoped_feature_use_prerequisites_v1",
        "_assert_train10_carrier_contract_v1",
        "_capture_model_snapshot_v1",
        "_assert_model_snapshot_unchanged_v1",
        "_assert_train10_centering_and_fixed_node_contract_v1",
        "_fingerprint_value_v1",
    ):
        assert callable(getattr(module, helper)), helper
    return module


def _backward_tools_v1() -> ModuleType:
    module = _load_published_test_module_v1(
        relative=PUBLISHED_BATCH001_BACKWARD_RELATIVE_V1,
        size=PUBLISHED_BATCH001_BACKWARD_SIZE_V1,
        sha256=PUBLISHED_BATCH001_BACKWARD_SHA256_V1,
        module_name="_covapie_published_batch001_backward_tools_for_train10_v1",
    )
    for helper in (
        "_published_predefined_noise_schedule_contract_v1",
        "_parameter_gradient_metadata_v1",
        "_validate_parameter_gradient_classification_v1",
        "_gradient_group_stats",
        "_emit_gradient_stats",
        "_install_model_and_state_write_tripwires",
    ):
        assert callable(getattr(module, helper)), helper
    return module


def _evidence_v1(message: str) -> None:
    print(f"COVAPIE_EVIDENCE {message}", flush=True)


@dataclass(frozen=True)
class _GradientSemanticsV1:
    groups: tuple[tuple[str, tuple[str, ...]], ...]
    frozen_parameter_names: tuple[str, ...]
    inactive_trainable_parameter_names: tuple[str, ...]
    active_zero_gradient_parameter_names: tuple[str, ...]
    seed_branch_active: bool


def _semantic_gradient_contract_before_backward_v1(
    *,
    named_parameters: Mapping[str, object],
    checkpoint_parameter_names: Sequence[str],
    seed_branch_active: bool,
    geometry_weight: float,
) -> _GradientSemanticsV1:
    """Classify names from source/input semantics, never observed gradients."""

    backward = _backward_tools_v1()
    names = tuple(named_parameters)
    assert names and len(names) == len(set(names)), "duplicate_parameter_name"
    assert type(seed_branch_active) is bool
    assert geometry_weight == 0.0, "geometry_weight_contract_mismatch"
    checkpoint_names = set(checkpoint_parameter_names)

    group_members: dict[str, list[str]] = {
        "legacy_ddpm_egnn": [],
        "target_residue_conditioning": [],
        "role_task_generation_seed_anchor_encoding": [],
        "pair_embedding_logit": [],
        "geometry_head": [],
    }
    for name in names:
        matches = []
        if name in checkpoint_names:
            matches.append("legacy_ddpm_egnn")
        if name == backward.TARGET_RESIDUE_PARAMETER_NAME_V1:
            matches.append("target_residue_conditioning")
        if name.startswith(backward.ROLE_TASK_GENERATION_SEED_ANCHOR_PREFIXES_V1):
            matches.append("role_task_generation_seed_anchor_encoding")
        if name.startswith(backward.PAIR_PREFIXES_V1):
            matches.append("pair_embedding_logit")
        if name.startswith(backward.GEOMETRY_PREFIX_V1):
            matches.append("geometry_head")
        assert len(matches) == 1, ("unknown_or_multiply_grouped_parameter", name, matches)
        group_members[matches[0]].append(name)

    assert all(group_members.values()), "empty_required_gradient_group"
    flattened = tuple(
        name for members in group_members.values() for name in members
    )
    assert len(flattened) == len(set(flattened)) == len(names)
    assert set(flattened) == set(names)

    frozen = tuple(backward.FROZEN_PARAMETER_CONTRACT_V1)
    assert set(frozen) <= set(names)
    inactive = {
        name
        for name in group_members["legacy_ddpm_egnn"]
        if name.startswith(backward.LEGACY_INACTIVE_RESIDUE_DECODER_PREFIX_V1)
    }
    inactive.update(group_members["geometry_head"])
    seed_prefix = (
        "covapie_current11_auxiliary_model_v1.seed_indicator_embedding."
    )
    seed_names = {
        name
        for name in group_members[
            "role_task_generation_seed_anchor_encoding"
        ]
        if name.startswith(seed_prefix)
    }
    assert seed_names, "seed_parameter_names_missing"
    if not seed_branch_active:
        inactive.update(seed_names)

    active_zero = tuple(backward.ACTIVE_ZERO_GRADIENT_CONTRACT_V1)
    assert set(active_zero) <= set(names)
    assert not (set(active_zero) & inactive)
    return _GradientSemanticsV1(
        groups=tuple(
            (group_name, tuple(members))
            for group_name, members in group_members.items()
        ),
        frozen_parameter_names=tuple(sorted(frozen)),
        inactive_trainable_parameter_names=tuple(sorted(inactive)),
        active_zero_gradient_parameter_names=tuple(sorted(active_zero)),
        seed_branch_active=seed_branch_active,
    )


def _validate_gradient_records_v1(
    *, records: Sequence[object], semantics: _GradientSemanticsV1
) -> object:
    backward = _backward_tools_v1()
    return backward._validate_parameter_gradient_classification_v1(
        records,
        frozen_parameter_contract=semantics.frozen_parameter_names,
        inactive_trainable_parameter_names=(
            semantics.inactive_trainable_parameter_names
        ),
        active_zero_gradient_parameter_names=(
            semantics.active_zero_gradient_parameter_names
        ),
    )


@dataclass(frozen=True)
class _SyntheticCompatibleSnapshotV1:
    parameter_values: dict[str, object]
    buffer_values: dict[str, object]
    parameter_object_ids: tuple[tuple[str, int], ...]
    state_dict_keys: tuple[str, ...]
    requires_grad_flags: tuple[tuple[str, bool], ...]
    state_fingerprint: str
    configuration_fingerprint: str


def _capture_synthetic_compatible_snapshot_v1(
    model: object, *, configuration_snapshotter: Callable[[object], object]
) -> _SyntheticCompatibleSnapshotV1:
    """Synthetic-only adapter for the published low-level snapshot tools."""

    forward = _forward_tools_v1()
    tools = forward._load_published_legacy_tools_v1()
    named_parameters = tuple(model.named_parameters())
    named_buffers = tuple(model.named_buffers())
    assert named_parameters and all(value.grad is None for _, value in named_parameters)
    parameter_values = tools._snapshot_named_tensors(iter(named_parameters))
    buffer_values = tools._snapshot_named_tensors(iter(named_buffers))
    return _SyntheticCompatibleSnapshotV1(
        parameter_values=parameter_values,
        buffer_values=buffer_values,
        parameter_object_ids=tuple((name, id(value)) for name, value in named_parameters),
        state_dict_keys=tuple(model.state_dict()),
        requires_grad_flags=tuple(
            (name, bool(value.requires_grad)) for name, value in named_parameters
        ),
        state_fingerprint=tools._model_state_fingerprint(
            parameter_values, buffer_values
        ),
        configuration_fingerprint=forward._fingerprint_value_v1(
            configuration_snapshotter(model)
        ),
    )


def _assert_model_and_carrier_unchanged_allow_grad_v1(
    *,
    snapshot: object,
    model: object,
    carrier_fingerprint: str,
    carrier: object,
    configuration_snapshotter: Callable[[object], object] | None = None,
    carrier_fingerprinter: Callable[[object], str] | None = None,
) -> None:
    """Assert S0->S2 invariance without requiring parameter grads to be None."""

    forward = _forward_tools_v1()
    tools = forward._load_published_legacy_tools_v1()
    if configuration_snapshotter is None:
        configuration_snapshotter = forward._model_configuration_snapshot_v1
    if carrier_fingerprinter is None:
        carrier_fingerprinter = forward._fingerprint_value_v1
    named_parameters = tuple(model.named_parameters())
    named_buffers = tuple(model.named_buffers())
    assert tuple((name, id(value)) for name, value in named_parameters) == (
        snapshot.parameter_object_ids
    ), "parameter_identity_changed"
    assert tuple(model.state_dict()) == snapshot.state_dict_keys, "state_dict_keys_changed"
    assert tuple(
        (name, bool(value.requires_grad)) for name, value in named_parameters
    ) == snapshot.requires_grad_flags, "requires_grad_flags_changed"
    tools._assert_snapshot_unchanged(
        snapshot.parameter_values, iter(named_parameters)
    )
    tools._assert_snapshot_unchanged(snapshot.buffer_values, iter(named_buffers))
    current_parameters = tools._snapshot_named_tensors(iter(named_parameters))
    current_buffers = tools._snapshot_named_tensors(iter(named_buffers))
    assert tools._model_state_fingerprint(
        current_parameters, current_buffers
    ) == snapshot.state_fingerprint, "model_state_fingerprint_changed"
    assert forward._fingerprint_value_v1(
        configuration_snapshotter(model)
    ) == snapshot.configuration_fingerprint, "configuration_or_node_prior_changed"
    assert carrier_fingerprinter(carrier) == carrier_fingerprint, "carrier_changed"


class _BackwardInvocationGuardV1:
    """Single top-level backward guard, parameterized for synthetic regression."""

    def __init__(self) -> None:
        self.forward_requested_count = 0
        self.forward_returned_count = 0
        self.top_level_backward_requested_count = 0
        self.top_level_backward_returned_count = 0
        self.internal_autograd_requested_count = 0
        self.internal_autograd_returned_count = 0
        self.backward_in_progress = False
        self.expected_loss: object | None = None
        self.forbidden_calls: list[str] = []

    def reject(self, name: str) -> None:
        self.forbidden_calls.append(name)
        raise AssertionError(f"forbidden operation invoked: {name}")

    def invoke_tensor_backward(
        self,
        tensor: object,
        args: tuple[object, ...],
        kwargs: Mapping[str, object],
        delegate: Callable[[object], None],
    ) -> None:
        if tensor is not self.expected_loss:
            self.reject("Tensor.backward.unbound_loss")
        if args or kwargs:
            self.reject("Tensor.backward.nondefault_options")
        if self.top_level_backward_requested_count != 0:
            self.reject("Tensor.backward.second_top_level_call")
        self.top_level_backward_requested_count = 1
        self.backward_in_progress = True
        try:
            delegate(tensor)
        finally:
            self.backward_in_progress = False
        self.top_level_backward_returned_count = 1

    def invoke_internal_autograd_backward(
        self,
        args: tuple[object, ...],
        kwargs: Mapping[str, object],
        delegate: Callable[[], None],
    ) -> None:
        if not self.backward_in_progress:
            self.reject("torch.autograd.backward.outside_authorized_call")
        retain_graph = kwargs.get(
            "retain_graph", args[2] if len(args) > 2 else None
        )
        create_graph = kwargs.get(
            "create_graph", args[3] if len(args) > 3 else False
        )
        if retain_graph not in (None, False) or create_graph not in (None, False):
            self.reject("torch.autograd.backward.graph_retention_requested")
        self.internal_autograd_requested_count += 1
        if self.internal_autograd_requested_count != 1:
            self.reject("torch.autograd.backward.unexpected_internal_count")
        delegate()
        self.internal_autograd_returned_count = 1


def _install_real_backward_tripwires_v1(
    stack: contextlib.ExitStack,
    *,
    model: object,
    carrier: object,
    guard: _BackwardInvocationGuardV1,
) -> None:
    """Install future-real guards without constructing an optimizer or Trainer."""

    import pytorch_lightning as pl

    original_forward = model.forward
    original_tensor_backward = torch.Tensor.backward
    original_autograd_backward = torch.autograd.backward

    def guarded_forward(data: object) -> object:
        if data is not carrier:
            guard.reject("model.forward.unbound_carrier")
        if guard.forward_requested_count != 0:
            guard.reject("model.forward.second_call")
        guard.forward_requested_count = 1
        result = original_forward(data)
        guard.forward_returned_count = 1
        return result

    def guarded_tensor_backward(
        tensor: object, *args: object, **kwargs: object
    ) -> None:
        guard.invoke_tensor_backward(
            tensor,
            args,
            kwargs,
            lambda bound: original_tensor_backward(bound),
        )

    def guarded_autograd_backward(*args: object, **kwargs: object) -> None:
        guard.invoke_internal_autograd_backward(
            args,
            kwargs,
            lambda: original_autograd_backward(*args, **kwargs),
        )

    def forbidden(name: str) -> Callable[..., None]:
        def tripwire(*_args: object, **_kwargs: object) -> None:
            guard.reject(name)

        return tripwire

    for owner, attribute, replacement in (
        (model, "forward", guarded_forward),
        (torch.Tensor, "backward", guarded_tensor_backward),
        (torch.autograd, "backward", guarded_autograd_backward),
        (torch.autograd, "grad", forbidden("torch.autograd.grad")),
        (torch, "load", forbidden("torch.load.after_single_checkpoint_load")),
        (torch, "save", forbidden("torch.save")),
        (torch.jit, "load", forbidden("torch.jit.load")),
        (torch.jit, "save", forbidden("torch.jit.save")),
        (pl.Trainer, "__init__", forbidden("Trainer.__init__")),
        (pl.Trainer, "fit", forbidden("Trainer.fit")),
        (pl.Trainer, "validate", forbidden("Trainer.validate")),
        (pl.Trainer, "test", forbidden("Trainer.test")),
        (pl.Trainer, "predict", forbidden("Trainer.predict")),
        (pl.Trainer, "save_checkpoint", forbidden("Trainer.save_checkpoint")),
        (
            pl.LightningModule,
            "load_from_checkpoint",
            forbidden("LightningModule.load_from_checkpoint"),
        ),
    ):
        stack.enter_context(mock.patch.object(owner, attribute, new=replacement))

    optimizer_classes = {
        value
        for value in vars(torch.optim).values()
        if isinstance(value, type) and issubclass(value, torch.optim.Optimizer)
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

    # Reuse the published storage-aware post-migration write protection.
    _backward_tools_v1()._install_model_and_state_write_tripwires(
        stack, model=model, guard=guard
    )


def _merge_secondary_failure_v1(
    primary: BaseException | None,
    *,
    phase: str,
    callback: Callable[[], None],
) -> BaseException | None:
    """Run reporting/cleanup without replacing an existing primary error."""

    try:
        callback()
    except BaseException as secondary:
        if primary is None:
            return secondary
        primary.add_note(
            f"secondary_failure phase={phase} "
            f"type={type(secondary).__name__} message={secondary}"
        )
    return primary


def _train10_seed_branch_active_v1(carrier: object) -> bool:
    valid = carrier.supervision.ligand_minimal_seed_or_anchor_valid
    tasks = carrier.supervision.canonical_task_id
    assert valid.dtype == torch.bool and valid.shape == tasks.shape
    task_c = tasks == 4
    assert bool(task_c.any().item())
    assert not bool(valid[~task_c].any().item())
    return bool(valid[task_c].any().item())


def _validate_grad_enabled_forward_output_v1(
    *, output: object, carrier: object, model: object
) -> dict[str, object]:
    """Minimal delta over the published forward validator for grad-enabled use."""

    from covalent_ext.covapie_current11_training_lightning_module_v1 import (
        CovapieCurrent11TrainingForwardOutputV1,
    )

    forward = _forward_tools_v1()
    assert type(output) is CovapieCurrent11TrainingForwardOutputV1
    assert output.supervision is carrier.supervision
    loss_output = output.loss_output
    loss_total = loss_output.loss_total
    assert loss_total is output.loss_output.loss_total
    assert loss_total.ndim == 0 and bool(torch.isfinite(loss_total).item())
    assert loss_total.requires_grad is True and loss_total.grad_fn is not None
    raw_losses = forward._loss_values_v1(output)
    assert all(math.isfinite(value) for value in raw_losses.values())
    valid_counts = forward._loss_counts_v1(output)
    eligible = forward._hidden_post_eligibility_oracle_v1(carrier)
    supervision = carrier.supervision
    assert valid_counts == {
        "base": int(supervision.sample_training_admitted.sum().item()),
        "pair": int(supervision.pair_positive_candidate_valid.sum().item()),
        "geometry": len(eligible),
        "contrastive": int(
            supervision.pair_contrastive_sample_loss_mask.sum().item()
        ),
    }
    for diagnostic in (
        loss_output.pair_prediction_per_sample_detached,
        loss_output.pre_post_geometry_per_sample_detached,
        loss_output.pair_contrastive_per_sample_detached,
    ):
        assert diagnostic.requires_grad is False and diagnostic.grad_fn is None
    timesteps = output.diffusion_trace.diffusion_timestep_int
    assert timesteps.dtype == torch.long and tuple(timesteps.shape) == (10,)
    assert bool(((timesteps >= 0) & (timesteps <= model.ddpm.T)).all().item())
    assert tuple(int(value) for value in supervision.canonical_task_id.tolist()) == (
        EXPECTED_EPOCH0_TASK_IDS_V1
    )
    return {
        "timesteps": tuple(int(value) for value in timesteps.tolist()),
        "raw_losses": raw_losses,
        "valid_counts": valid_counts,
        "loss_total": loss_total,
    }


def _run_real_checkpoint_validation_v1() -> None:
    """Future-authorized one-forward/one-backward path; never run by default."""

    phase = "dependency_import"
    primary: BaseException | None = None
    primary_traceback = None
    runtime_stack = contextlib.ExitStack()
    rng_before = torch.random.get_rng_state().clone()
    summary: dict[str, object] = {}
    guard = _BackwardInvocationGuardV1()
    try:
        forward = _forward_tools_v1()
        backward = _backward_tools_v1()
        dependencies = forward._load_real_path_dependencies_v1()
        adapter = dependencies["adapter"]
        checkpoint_locator = dependencies["checkpoint_locator"]
        compatible_owner = dependencies["compatible_owner"]
        migration_owner = dependencies["migration_owner"]
        training_owner = dependencies["training_owner"]
        tensorizer_owner = dependencies["tensorizer_owner"]
        composer_owner = dependencies["composer_owner"]

        phase = "fixed_source_and_feature_semantics"
        direct_sources_before = _verify_direct_bound_sources_v1()
        forward_sources_before = forward._verify_bound_sources_v1()
        adapter_sources_before = (
            adapter.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(
                repository_root=ROOT
            )
        )
        forward._assert_scoped_feature_use_prerequisites_v1()
        schedule = backward._published_predefined_noise_schedule_contract_v1()
        assert schedule.schedule_class_name == "PredefinedNoiseSchedule"
        assert schedule.schedule_name == "polynomial_2"
        assert schedule.timesteps == 500
        assert schedule.frozen_parameter_names == ("ddpm.gamma.gamma",)

        phase = "checkpoint_identity_and_load"
        assert checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1 == (
            compatible_owner.CHECKPOINT_PATH
        )
        checkpoint_path = ROOT / checkpoint_locator.CHECKPOINT_RELATIVE_PATH_V1
        checkpoint_identity = forward._safe_file_identity_v1(checkpoint_path)
        assert checkpoint_identity == (
            EXPECTED_CHECKPOINT_SIZE_BYTES_V1,
            EXPECTED_CHECKPOINT_SHA256_V1,
        )
        checkpoint = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
            checkpoint_path=checkpoint_path
        )
        checkpoint_state = checkpoint["state_dict"]

        phase = "model_construction_and_strict_migration"
        runtime_root = Path(tempfile.mkdtemp(
            prefix=TASK_ID_V1 + "-", dir=STATE_ROOT / "review-scratch"
        ))
        model = forward._instantiate_train10_model_v1(
            checkpoint=checkpoint, runtime_root=runtime_root
        )
        migration = migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
            model=model, checkpoint_state_dict=checkpoint_state
        )
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
        prepared = composer_owner.prepare_covapie_train10_cpu_batch_composer_v1(
            ROOT, STATE_ROOT, CACHE_ROOT
        )
        carrier = composer_owner.build_covapie_train10_cpu_epoch_batch_v1(
            prepared, 0, 0
        )
        carrier_measurements = forward._assert_train10_carrier_contract_v1(carrier)
        assert carrier_measurements["tasks"] == EXPECTED_EPOCH0_TASK_IDS_V1
        carrier_fingerprint = forward._fingerprint_value_v1(carrier)

        phase = "s0_snapshot_and_semantics"
        snapshot = forward._capture_model_snapshot_v1(model)
        named_parameters = dict(model.named_parameters())
        assert tuple(
            name for name, parameter in named_parameters.items()
            if not parameter.requires_grad
        ) == schedule.frozen_parameter_names
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
        seed_branch_active = _train10_seed_branch_active_v1(carrier)
        assert seed_branch_active is True
        semantics = _semantic_gradient_contract_before_backward_v1(
            named_parameters=named_parameters,
            checkpoint_parameter_names=tuple(checkpoint_state),
            seed_branch_active=seed_branch_active,
            geometry_weight=actual_weights["pre_post_geometry"],
        )
        _evidence_v1(
            "gradient_semantics_frozen_before_backward=PASS "
            f"seed_branch_active={str(seed_branch_active).lower()} "
            f"groups={tuple((name, len(members)) for name, members in semantics.groups)} "
            f"frozen={semantics.frozen_parameter_names} "
            f"inactive={semantics.inactive_trainable_parameter_names} "
            f"active_zero_allowed={semantics.active_zero_gradient_parameter_names}"
        )

        phase = "guard_and_observer_installation"
        _install_real_backward_tripwires_v1(
            runtime_stack, model=model, carrier=carrier, guard=guard
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
        production_loss: dict[str, object] = {"requested": 0, "returned": 0}
        original_loss = adapter.compute_covapie_current11_training_losses_v1

        def observed_production_loss(*args: object, **kwargs: object) -> object:
            production_loss["requested"] = int(production_loss["requested"]) + 1
            assert production_loss["requested"] == 1
            result = original_loss(*args, **kwargs)
            production_loss["value"] = result
            production_loss["returned"] = int(production_loss["returned"]) + 1
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
        torch.manual_seed(DIFFUSION_FORWARD_SEED_V1)
        assert torch.is_grad_enabled() is True
        assert torch.is_inference_mode_enabled() is False
        assert all(parameter.grad is None for parameter in model.parameters())
        output = model(carrier)
        measurements = _validate_grad_enabled_forward_output_v1(
            output=output, carrier=carrier, model=model
        )
        assert production_loss == {
            "requested": 1,
            "returned": 1,
            "value": output.loss_output,
        }
        assert guard.forward_requested_count == guard.forward_returned_count == 1

        phase = "s1_post_forward_invariance"
        forward._assert_model_snapshot_unchanged_v1(snapshot, model)
        assert forward._fingerprint_value_v1(carrier) == carrier_fingerprint
        _evidence_v1(
            "S1_POST_FORWARD_INVARIANCE=PASS parameters=true buffers=true "
            "identity=true keys=true requires_grad_flags=true gradients_none=true "
            "configuration_and_node_prior=true carrier=true"
        )

        phase = "coordinate_and_fixed_node_oracle"
        assert transport["requested"] == transport["returned"] == 1
        with torch.no_grad():
            forward._assert_train10_centering_and_fixed_node_contract_v1(
                model=model,
                carrier=carrier,
                transported=transport["value"],
                output=output,
            )

        phase = "single_total_loss_backward"
        loss_total = measurements["loss_total"]
        assert loss_total is output.loss_output.loss_total
        assert loss_total.requires_grad is True and loss_total.grad_fn is not None
        guard.expected_loss = loss_total
        loss_total.backward()
        assert guard.top_level_backward_requested_count == 1
        assert guard.top_level_backward_returned_count == 1
        assert guard.internal_autograd_requested_count == 1
        assert guard.internal_autograd_returned_count == 1

        phase = "s2_post_backward_state_invariance"
        _assert_model_and_carrier_unchanged_allow_grad_v1(
            snapshot=snapshot,
            model=model,
            carrier_fingerprint=carrier_fingerprint,
            carrier=carrier,
        )
        _evidence_v1(
            "S2_POST_BACKWARD_STATE_INVARIANCE=PASS parameters=true buffers=true "
            "identity=true keys=true requires_grad_flags=true "
            "configuration_and_node_prior=true carrier=true gradients_preserved=true"
        )

        phase = "post_s2_gradient_classification"
        named_parameters = dict(model.named_parameters())
        group_stats = []
        for group_name, parameter_names in semantics.groups:
            item = backward._gradient_group_stats(
                group_name=group_name,
                named_parameters=named_parameters,
                parameter_names=parameter_names,
            )
            backward._emit_gradient_stats(item)
            assert item.all_produced_gradients_finite
            assert math.isfinite(item.gradient_l2_norm)
            assert math.isfinite(item.gradient_max_abs)
            group_stats.append(item)
        stats_by_name = {item.group_name: item for item in group_stats}
        for active_group in (
            "legacy_ddpm_egnn",
            "target_residue_conditioning",
            "role_task_generation_seed_anchor_encoding",
            "pair_embedding_logit",
        ):
            assert stats_by_name[active_group].grad_nonzero_count > 0
        assert stats_by_name["geometry_head"].grad_nonzero_count == 0
        classification = _validate_gradient_records_v1(
            records=backward._parameter_gradient_metadata_v1(named_parameters),
            semantics=semantics,
        )
        assert classification.frozen_parameter_names == ("ddpm.gamma.gamma",)
        assert guard.forbidden_calls == []

        phase = "final_source_and_checkpoint_integrity"
        assert _verify_direct_bound_sources_v1() == direct_sources_before
        assert forward._verify_bound_sources_v1() == forward_sources_before
        assert adapter.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(
            repository_root=ROOT
        ) == adapter_sources_before
        assert forward._safe_file_identity_v1(checkpoint_path) == checkpoint_identity
        summary = {
            "runtime": str(runtime_root),
            "tasks": carrier_measurements["tasks"],
            "timesteps": measurements["timesteps"],
            "raw_losses": measurements["raw_losses"],
            "valid_counts": measurements["valid_counts"],
            "weights": actual_weights,
            "forward_requested": guard.forward_requested_count,
            "forward_returned": guard.forward_returned_count,
            "backward_requested": guard.top_level_backward_requested_count,
            "backward_returned": guard.top_level_backward_returned_count,
            "internal_backward_requested": guard.internal_autograd_requested_count,
            "internal_backward_returned": guard.internal_autograd_returned_count,
        }
    except BaseException as error:
        primary = error
        primary_traceback = error.__traceback__

    primary = _merge_secondary_failure_v1(
        primary, phase="observer_and_tripwire_cleanup", callback=runtime_stack.close
    )
    primary = _merge_secondary_failure_v1(
        primary,
        phase="caller_rng_restore",
        callback=lambda: torch.random.set_rng_state(rng_before),
    )
    if primary is not None:
        forward = _forward_tools_v1()
        primary = _merge_secondary_failure_v1(
            primary,
            phase="primary_failure_reporting",
            callback=lambda: forward._report_primary_failure_v1(
                primary=primary,
                phase=phase,
                call_counts={
                    "forward_requested": guard.forward_requested_count,
                    "forward_returned": guard.forward_returned_count,
                    "backward_requested": guard.top_level_backward_requested_count,
                    "backward_returned": guard.top_level_backward_returned_count,
                    "internal_backward_requested": guard.internal_autograd_requested_count,
                    "internal_backward_returned": guard.internal_autograd_returned_count,
                },
            ),
        )
        raise primary.with_traceback(primary_traceback)
    _evidence_v1("REAL_TRAIN10_FORWARD_BACKWARD_NO_UPDATE=PASS " + json.dumps(
        summary, sort_keys=True
    ))


def _execute_real_path_if_enabled_v1() -> None:
    if os.environ.get(REAL_BACKWARD_OPT_IN_V1) != "1":
        pytest.skip(
            f"set {REAL_BACKWARD_OPT_IN_V1}=1 for the bounded real backward path"
        )
    _evidence_v1(
        "real_opt_in=1 checkpoint_load_budget=1 model_budget=1 "
        "carrier_budget=1 forward_budget=1 total_backward_budget=1 "
        "optimizer_budget=0 trainer_budget=0 parameter_update_budget=0"
    )
    _run_real_checkpoint_validation_v1()


@pytest.fixture(autouse=True)
def _non_model_execution_tripwires_v1(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Iterator[list[str]]:
    """Keep ordinary nodes outside checkpoint/model/training runtime."""

    calls: list[str] = []
    if (
        request.node.name
        == "test_real_checkpoint_train10_forward_backward_without_update"
        and os.environ.get(REAL_BACKWARD_OPT_IN_V1) == "1"
    ):
        yield calls
        return

    import pytorch_lightning as pl
    from covalent_ext import covapie_train10_hidden_post_forward_adapter_v1 as adapter
    from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer

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
        (pl.Trainer, "__init__", "Trainer.__init__"),
        (pl.Trainer, "fit", "Trainer.fit"),
        (composer, "prepare_covapie_train10_cpu_batch_composer_v1", "composer_prepare"),
        (composer, "build_covapie_train10_cpu_epoch_batch_v1", "carrier_build"),
        (
            adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1,
            "__init__",
            "train10_model_init",
        ),
        (
            adapter.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1,
            "forward",
            "train10_model_forward",
        ),
        (
            adapter,
            "compute_covapie_current11_training_losses_v1",
            "production_loss",
        ),
    ):
        monkeypatch.setattr(owner, attribute, forbidden(name))
    yield calls
    assert calls == []


def test_published_identities_helpers_and_static_feature_semantics() -> None:
    direct = _verify_direct_bound_sources_v1()
    assert len(direct) == len(DIRECT_BOUND_SOURCE_SHA256_V1)
    forward = _forward_tools_v1()
    backward = _backward_tools_v1()
    assert forward._verify_bound_sources_v1()
    forward._assert_scoped_feature_use_prerequisites_v1()
    assert forward.MODEL_INITIALIZATION_SEED_V1 == MODEL_INITIALIZATION_SEED_V1
    assert forward.DIFFUSION_FORWARD_SEED_V1 == DIFFUSION_FORWARD_SEED_V1
    assert forward.EXPECTED_CHECKPOINT_SIZE_BYTES_V1 == EXPECTED_CHECKPOINT_SIZE_BYTES_V1
    assert forward.EXPECTED_CHECKPOINT_SHA256_V1 == EXPECTED_CHECKPOINT_SHA256_V1
    schedule = backward._published_predefined_noise_schedule_contract_v1()
    assert (
        schedule.schedule_class_name,
        schedule.schedule_name,
        schedule.timesteps,
        schedule.frozen_parameter_names,
    ) == (
        "PredefinedNoiseSchedule",
        "polynomial_2",
        500,
        ("ddpm.gamma.gamma",),
    )

    auxiliary_source = (
        ROOT / "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py"
    ).read_text(encoding="utf-8")
    training_source = (
        ROOT / "src/covalent_ext/covapie_current11_training_lightning_module_v1.py"
    ).read_text(encoding="utf-8")
    assert "seed_valid_by_node = supervision.ligand_minimal_seed_or_anchor_valid[" in auxiliary_source
    assert "final_anchor.weight.zero_()" in auxiliary_source
    assert "final_anchor.bias.zero_()" in auxiliary_source
    assert "float(weights.pre_post_geometry) * loss_geometry" in auxiliary_source
    assert "decoded_residues = dynamics.residue_decoder(h_final_residues)" in training_source
    assert CANONICAL_EXACT5_V1 == forward.CANONICAL_EXACT5_V1

    real_tree = ast.parse(inspect.getsource(_run_real_checkpoint_validation_v1))
    backward_calls = [
        node
        for node in ast.walk(real_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "backward"
    ]
    assert len(backward_calls) == 1
    assert isinstance(backward_calls[0].func.value, ast.Name)
    assert backward_calls[0].func.value.id == "loss_total"
    assert backward_calls[0].args == [] and backward_calls[0].keywords == []
    source = inspect.getsource(_run_real_checkpoint_validation_v1)
    assert "autograd.grad" not in source
    assert "retain_graph" not in source and "create_graph" not in source
    assert ".step(" not in source and "Trainer(" not in source


def test_default_opt_in_gate_precedes_entire_real_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched = []

    def forbidden_real_path() -> None:
        touched.append("real_path")
        raise AssertionError("default-disabled path was reached")

    monkeypatch.delenv(REAL_BACKWARD_OPT_IN_V1, raising=False)
    monkeypatch.setattr(
        sys.modules[__name__], "_run_real_checkpoint_validation_v1", forbidden_real_path
    )
    with pytest.raises(pytest.skip.Exception, match=REAL_BACKWARD_OPT_IN_V1):
        _execute_real_path_if_enabled_v1()
    assert touched == []


def test_wrong_checkpoint_identity_rejected_before_deserialization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration

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


def _synthetic_parameter_name_contract_v1() -> tuple[tuple[str, ...], tuple[str, ...]]:
    names = (
        "ddpm.gamma.gamma",
        "ddpm.dynamics.egnn.weight",
        "ddpm.dynamics.residue_decoder.weight",
        "ddpm.dynamics.target_residue_atom_condition_embedding",
        "covapie_current11_auxiliary_model_v1.role_embedding.weight",
        "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.weight",
        "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.0.weight",
        "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.0.bias",
        "covapie_current11_auxiliary_model_v1.pair_embedding.0.weight",
        "covapie_current11_auxiliary_model_v1.pre_post_geometry_head.0.weight",
    )
    checkpoint_names = names[:3]
    return names, checkpoint_names


def _synthetic_named_parameters_v1() -> dict[str, object]:
    names, _checkpoint = _synthetic_parameter_name_contract_v1()
    return {
        name: SimpleNamespace(requires_grad=(name != "ddpm.gamma.gamma"))
        for name in names
    }


def _synthetic_records_v1(
    semantics: _GradientSemanticsV1,
    *,
    geometry_state: str = "none",
    active_override: tuple[str, str, bool] | None = None,
) -> tuple[object, ...]:
    backward = _backward_tools_v1()
    names, _checkpoint = _synthetic_parameter_name_contract_v1()
    inactive = set(semantics.inactive_trainable_parameter_names)
    frozen = set(semantics.frozen_parameter_names)
    zero_allowed = set(semantics.active_zero_gradient_parameter_names)
    records = []
    for name in names:
        if name in frozen:
            state, finite, requires_grad = "none", True, False
        elif name.startswith(backward.GEOMETRY_PREFIX_V1):
            state, finite, requires_grad = geometry_state, True, True
        elif name in inactive:
            state, finite, requires_grad = "none", True, True
        elif name in zero_allowed:
            state, finite, requires_grad = "all_zero", True, True
        else:
            state, finite, requires_grad = "nonzero", True, True
        if active_override is not None and name == active_override[0]:
            state, finite = active_override[1], active_override[2]
        records.append(backward._ParameterGradientMetadataV1(
            name=name,
            requires_grad=requires_grad,
            gradient_state=state,
            produced_gradient_finite=finite,
        ))
    return tuple(records)


@pytest.mark.parametrize("seed_branch_active", [False, True])
def test_synthetic_gradient_semantics_seed_branches_and_legal_geometry(
    seed_branch_active: bool,
) -> None:
    """SYNTHETIC_GRADIENT_METADATA: no autograd/backward is invoked."""

    names, checkpoint_names = _synthetic_parameter_name_contract_v1()
    semantics = _semantic_gradient_contract_before_backward_v1(
        named_parameters=_synthetic_named_parameters_v1(),
        checkpoint_parameter_names=checkpoint_names,
        seed_branch_active=seed_branch_active,
        geometry_weight=0.0,
    )
    seed_name = (
        "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.weight"
    )
    assert (seed_name in semantics.inactive_trainable_parameter_names) is (
        not seed_branch_active
    )
    assert {name for group, members in semantics.groups for name in members} == set(names)
    for geometry_state in ("none", "all_zero"):
        classification = _validate_gradient_records_v1(
            records=_synthetic_records_v1(
                semantics, geometry_state=geometry_state
            ),
            semantics=semantics,
        )
        assert classification.frozen_parameter_names == ("ddpm.gamma.gamma",)


def test_synthetic_gradient_classifier_fail_closed_cases() -> None:
    """SYNTHETIC_GRADIENT_METADATA covers active, finite, duplicate and freeze errors."""

    _names, checkpoint_names = _synthetic_parameter_name_contract_v1()
    semantics = _semantic_gradient_contract_before_backward_v1(
        named_parameters=_synthetic_named_parameters_v1(),
        checkpoint_parameter_names=checkpoint_names,
        seed_branch_active=True,
        geometry_weight=0.0,
    )
    active_name = "ddpm.dynamics.egnn.weight"
    with pytest.raises(AssertionError, match="active_parameter_gradient_none"):
        _validate_gradient_records_v1(
            records=_synthetic_records_v1(
                semantics, active_override=(active_name, "none", True)
            ),
            semantics=semantics,
        )
    backward = _backward_tools_v1()
    for value in (float("nan"), float("inf")):
        synthetic_parameter = torch.nn.Parameter(torch.ones(1))
        synthetic_parameter.grad = torch.tensor([value])
        observed_nonfinite = backward._parameter_gradient_metadata_v1(
            {active_name: synthetic_parameter}
        )[0]
        assert observed_nonfinite.gradient_state == "nonzero"
        assert observed_nonfinite.produced_gradient_finite is False
        records = list(_synthetic_records_v1(semantics))
        active_index = next(
            index for index, record in enumerate(records)
            if record.name == active_name
        )
        records[active_index] = observed_nonfinite
        with pytest.raises(AssertionError, match="active_parameter_gradient_nonfinite"):
            _validate_gradient_records_v1(
                records=records,
                semantics=semantics,
            )
    with pytest.raises(AssertionError):
        _validate_gradient_records_v1(
            records=_synthetic_records_v1(semantics, geometry_state="nonzero"),
            semantics=semantics,
        )
    duplicate = _synthetic_records_v1(semantics)
    with pytest.raises(AssertionError):
        _validate_gradient_records_v1(
            records=duplicate + (duplicate[-1],), semantics=semantics
        )

    extra_frozen = list(_synthetic_records_v1(semantics))
    extra_frozen[1] = backward._ParameterGradientMetadataV1(
        name=active_name,
        requires_grad=False,
        gradient_state="none",
        produced_gradient_finite=True,
    )
    with pytest.raises(AssertionError, match="frozen_parameter_contract_mismatch"):
        _validate_gradient_records_v1(records=extra_frozen, semantics=semantics)

    unknown = _synthetic_named_parameters_v1()
    unknown["unclassified_new_module.weight"] = SimpleNamespace(requires_grad=True)
    with pytest.raises(AssertionError, match="unknown_or_multiply_grouped_parameter"):
        _semantic_gradient_contract_before_backward_v1(
            named_parameters=unknown,
            checkpoint_parameter_names=checkpoint_names,
            seed_branch_active=True,
            geometry_weight=0.0,
        )


def test_synthetic_direct_grad_metadata_and_group_statistics() -> None:
    """SYNTHETIC_GRADIENT_METADATA uses direct .grad fixtures, never autograd."""

    backward = _backward_tools_v1()
    names, checkpoint_names = _synthetic_parameter_name_contract_v1()
    named_parameters = {
        name: torch.nn.Parameter(
            torch.ones(2), requires_grad=(name != "ddpm.gamma.gamma")
        )
        for name in names
    }
    semantics = _semantic_gradient_contract_before_backward_v1(
        named_parameters=named_parameters,
        checkpoint_parameter_names=checkpoint_names,
        seed_branch_active=True,
        geometry_weight=0.0,
    )
    inactive = set(semantics.inactive_trainable_parameter_names)
    zero_allowed = set(semantics.active_zero_gradient_parameter_names)
    for name, parameter in named_parameters.items():
        # Direct assignment is synthetic test data, never a real-model action.
        if not parameter.requires_grad or name in inactive:
            continue
        parameter.grad = (
            torch.zeros_like(parameter)
            if name in zero_allowed
            else torch.ones_like(parameter)
        )
    records = backward._parameter_gradient_metadata_v1(named_parameters)
    _validate_gradient_records_v1(records=records, semantics=semantics)
    stats = {
        group: backward._gradient_group_stats(
            group_name=group,
            named_parameters=named_parameters,
            parameter_names=members,
        )
        for group, members in semantics.groups
    }
    assert stats["geometry_head"].grad_nonzero_count == 0
    assert stats["legacy_ddpm_egnn"].grad_nonzero_count > 0
    assert all(item.all_produced_gradients_finite for item in stats.values())


class _SyntheticStateModelV1(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.weight = torch.nn.Parameter(torch.tensor([1.0, 2.0]))
        self.register_buffer("node_prior", torch.tensor([0.25, 0.75]))
        self.config_tag = "stable"


def _synthetic_config_v1(model: _SyntheticStateModelV1) -> object:
    return {"config_tag": model.config_tag, "node_prior": model.node_prior.clone()}


def _synthetic_state_fixture_v1() -> tuple[object, object, str, dict[str, object]]:
    model = _SyntheticStateModelV1()
    carrier = {"tasks": EXPECTED_EPOCH0_TASK_IDS_V1, "payload": torch.tensor([3, 5])}
    snapshot = _capture_synthetic_compatible_snapshot_v1(
        model, configuration_snapshotter=_synthetic_config_v1
    )
    carrier_fingerprint = _forward_tools_v1()._fingerprint_value_v1(carrier)
    return model, snapshot, carrier_fingerprint, carrier


def test_synthetic_state_invariance_allows_only_grad_change() -> None:
    """SYNTHETIC_GRADIENT_METADATA separates gradient state from model state."""

    model, snapshot, carrier_fingerprint, carrier = _synthetic_state_fixture_v1()
    model.weight.grad = torch.tensor([0.5, -0.5])
    _assert_model_and_carrier_unchanged_allow_grad_v1(
        snapshot=snapshot,
        model=model,
        carrier_fingerprint=carrier_fingerprint,
        carrier=carrier,
        configuration_snapshotter=_synthetic_config_v1,
    )


@pytest.mark.parametrize(
    "mutation",
    ["parameter", "buffer", "identity", "keys", "requires_grad", "config", "carrier"],
)
def test_synthetic_state_invariance_rejects_non_gradient_changes(
    mutation: str,
) -> None:
    model, snapshot, carrier_fingerprint, carrier = _synthetic_state_fixture_v1()
    if mutation == "parameter":
        with torch.no_grad():
            model.weight.add_(1.0)
    elif mutation == "buffer":
        model.node_prior.add_(0.1)
    elif mutation == "identity":
        model.weight = torch.nn.Parameter(model.weight.detach().clone())
    elif mutation == "keys":
        model.register_buffer("unexpected", torch.ones(1))
    elif mutation == "requires_grad":
        model.weight.requires_grad_(False)
    elif mutation == "config":
        model.config_tag = "changed"
    elif mutation == "carrier":
        carrier["tasks"] = (0,)
    with pytest.raises(AssertionError):
        _assert_model_and_carrier_unchanged_allow_grad_v1(
            snapshot=snapshot,
            model=model,
            carrier_fingerprint=carrier_fingerprint,
            carrier=carrier,
            configuration_snapshotter=_synthetic_config_v1,
        )


def test_synthetic_single_backward_guard_and_nested_delegation() -> None:
    """SYNTHETIC_CALL_GUARD: delegates are stubs, never torch autograd."""

    loss = object()
    guard = _BackwardInvocationGuardV1()
    guard.expected_loss = loss
    delegate_events = []

    def top_delegate(_loss: object) -> None:
        guard.invoke_internal_autograd_backward(
            (loss,), {}, lambda: delegate_events.append("internal_return")
        )

    guard.invoke_tensor_backward(loss, (), {}, top_delegate)
    assert delegate_events == ["internal_return"]
    assert guard.top_level_backward_requested_count == 1
    assert guard.top_level_backward_returned_count == 1
    assert guard.internal_autograd_requested_count == 1
    assert guard.internal_autograd_returned_count == 1
    with pytest.raises(AssertionError, match="second_top_level_call"):
        guard.invoke_tensor_backward(loss, (), {}, top_delegate)

    wrong = _BackwardInvocationGuardV1()
    wrong.expected_loss = loss
    with pytest.raises(AssertionError, match="unbound_loss"):
        wrong.invoke_tensor_backward(object(), (), {}, lambda _value: None)
    with pytest.raises(AssertionError, match="nondefault_options"):
        wrong.invoke_tensor_backward(loss, (), {"retain_graph": True}, lambda _value: None)

    outside = _BackwardInvocationGuardV1()
    with pytest.raises(AssertionError, match="outside_authorized_call"):
        outside.invoke_internal_autograd_backward((), {}, lambda: None)

    for internal_args, internal_kwargs in (
        ((loss, None, True), {}),
        ((loss,), {"create_graph": True}),
    ):
        retained = _BackwardInvocationGuardV1()
        retained.expected_loss = loss
        with pytest.raises(AssertionError, match="graph_retention_requested"):
            retained.invoke_tensor_backward(
                loss,
                (),
                {},
                lambda _value, args=internal_args, kwargs=internal_kwargs: (
                    retained.invoke_internal_autograd_backward(
                        args, kwargs, lambda: None
                    )
                ),
            )

    repeated_internal = _BackwardInvocationGuardV1()
    repeated_internal.expected_loss = loss

    def twice(_value: object) -> None:
        repeated_internal.invoke_internal_autograd_backward(
            (loss,), {}, lambda: None
        )
        repeated_internal.invoke_internal_autograd_backward(
            (loss,), {}, lambda: None
        )
    with pytest.raises(AssertionError, match="unexpected_internal_count"):
        repeated_internal.invoke_tensor_backward(loss, (), {}, twice)


def test_primary_error_survives_summary_and_cleanup_failures() -> None:
    class PrimaryFailure(RuntimeError):
        pass

    primary = PrimaryFailure("primary-model-path-failure")

    def summary_failure() -> None:
        raise ValueError("summary-failure")

    def cleanup_failure() -> None:
        raise OSError("cleanup-failure")

    observed: BaseException | None = primary
    observed = _merge_secondary_failure_v1(
        observed, phase="summary", callback=summary_failure
    )
    observed = _merge_secondary_failure_v1(
        observed, phase="cleanup", callback=cleanup_failure
    )
    assert observed is primary
    assert len(primary.__notes__) == 2
    assert "summary-failure" in primary.__notes__[0]
    assert "cleanup-failure" in primary.__notes__[1]


def test_fresh_process_dependency_helper_adapter_first_no_model() -> None:
    """Cold-load the exact future-real dependency helper under tripwires."""

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
runtime_pattern = "validate_covapie_train10_checkpoint_backward_no_update_v1-*"
runtime_before = tuple(sorted(runtime_parent.glob(runtime_pattern)))
adapter_name = "covalent_ext.covapie_train10_hidden_post_forward_adapter_v1"
training_name = "covalent_ext.covapie_current11_training_lightning_module_v1"
assert adapter_name not in sys.modules and training_name not in sys.modules
assert "COVAPIE_RUN_TRAIN10_CHECKPOINT_BACKWARD_NO_UPDATE" not in os.environ

spec = importlib.util.spec_from_file_location("cold_train10_backward_candidate", candidate)
assert spec is not None and spec.loader is not None
subject = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = subject
spec.loader.exec_module(subject)
assert adapter_name not in sys.modules and training_name not in sys.modules
forward = subject._forward_tools_v1()
assert adapter_name not in sys.modules and training_name not in sys.modules

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
}, sort_keys=True))
'''
    environment = os.environ.copy()
    for name in (
        REAL_BACKWARD_OPT_IN_V1,
        "COVAPIE_RUN_TRAIN10_CHECKPOINT_FORWARD_NO_UPDATE",
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
    }
    print("FRESH_PROCESS_DEPENDENCY_IMPORT=" + lines[0], flush=True)


def test_real_checkpoint_train10_forward_backward_without_update() -> None:
    _execute_real_path_if_enabled_v1()
