from __future__ import annotations

import ast
import copy
from dataclasses import fields, is_dataclass, replace
import importlib.metadata
import importlib.util
import inspect
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import pytorch_lightning as pl
import torch


def _load_subject():
    candidate = os.environ.get("COVAPIE_TRAIN12_FORWARD_ADAPTER_CANDIDATE")
    if candidate is None:
        from covalent_ext import (
            covapie_train12_hidden_post_forward_adapter_v1 as installed,
        )

        return installed
    path = Path(candidate).resolve(strict=True)
    specification = importlib.util.spec_from_file_location(
        "covapie_train12_hidden_post_forward_adapter_v1_candidate", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


# The subject applies the published Biopython compatibility entry point before
# importing the real training owner.  Do not pre-import that owner in the test.
subject = _load_subject()

from covalent_ext import covapie_train12_cpu_batch_composer_v1 as composer_owner
from covalent_ext import covapie_train10_cpu_batch_composer_v1 as train10_owner
from covalent_ext import (
    covapie_current11_auxiliary_model_and_loss_v1 as loss_owner,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    AUXILIARY_ERROR,
    CovapieCurrent11AuxiliaryModelV1,
    CovapieCurrent11LossWeightsV1,
    CovapieCurrent11ModelOutputV1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11DiffusionForwardTraceV1,
    CovapieCurrent11TrainingForwardOutputV1,
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from equivariant_diffusion.conditional_model import ConditionalDDPM
from lightning_modules import LigandPocketDDPM


ERROR = subject.COVAPIE_TRAIN12_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1
POST = 1
FACTS = {
    "train12_prepare": 0,
    "train10_prepare": 0,
    "ready2_prepare": 0,
    "train12_build": 0,
    "train10_build": 0,
    "ready2_build_including_fresh_validator_references": 0,
    "train12_public_validator": 0,
    "transport": 0,
    "synthetic_role_encoding": 0,
    "synthetic_diffusion_bridge": 0,
    "synthetic_auxiliary_prediction": 0,
    "production_loss": 0,
}
EPOCH_FACTS: list[dict[str, object]] = []


def _required_root(name: str) -> Path:
    configured = os.environ.get(name)
    assert configured is not None
    return Path(configured).resolve(strict=True)


ROOT = _required_root("COVAPIE_TEST_REPOSITORY_ROOT")
STATE_ROOT = _required_root("COVAPIE_TEST_STATE_ROOT")
CACHE_ROOT = _required_root("COVAPIE_TEST_CACHE_ROOT")


def _forbidden(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("forbidden checkpoint/model/training operation was invoked")


def _is_checkpoint_path(value: object) -> bool:
    try:
        path = Path(value)
    except TypeError:
        return False
    return "checkpoints" in path.parts or path.suffix in {".pt", ".ckpt", ".pth"}


_ORIGINAL_PATH_OPEN = Path.open
_ORIGINAL_PATH_READ_BYTES = Path.read_bytes
_ORIGINAL_PATH_STAT = Path.stat
_ORIGINAL_PATH_LSTAT = Path.lstat


@pytest.fixture(autouse=True, scope="module")
def no_real_model_or_training_operations():
    """Execute real transport/loss only, with synthetic neural predictions."""

    monkeypatch = pytest.MonkeyPatch()

    def guarded_path_open(path: Path, *args: object, **kwargs: object):
        if _is_checkpoint_path(path):
            _forbidden()
        return _ORIGINAL_PATH_OPEN(path, *args, **kwargs)

    def guarded_read_bytes(path: Path) -> bytes:
        if _is_checkpoint_path(path):
            _forbidden()
        return _ORIGINAL_PATH_READ_BYTES(path)

    def guarded_stat(path: Path, *args: object, **kwargs: object):
        if _is_checkpoint_path(path):
            _forbidden()
        return _ORIGINAL_PATH_STAT(path, *args, **kwargs)

    def guarded_lstat(path: Path, *args: object, **kwargs: object):
        if _is_checkpoint_path(path):
            _forbidden()
        return _ORIGINAL_PATH_LSTAT(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_path_open)
    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(Path, "stat", guarded_stat)
    monkeypatch.setattr(Path, "lstat", guarded_lstat)
    monkeypatch.setattr(torch, "load", _forbidden)
    monkeypatch.setattr(torch, "save", _forbidden)
    monkeypatch.setattr(torch.jit, "load", _forbidden)
    monkeypatch.setattr(torch.Tensor, "backward", _forbidden)
    monkeypatch.setattr(torch.autograd, "backward", _forbidden)
    monkeypatch.setattr(torch.autograd, "grad", _forbidden)
    monkeypatch.setattr(torch.optim.Optimizer, "__init__", _forbidden)
    monkeypatch.setattr(torch.optim.Optimizer, "step", _forbidden)
    monkeypatch.setattr(ConditionalDDPM, "__init__", _forbidden)
    monkeypatch.setattr(ConditionalDDPM, "forward", _forbidden)
    monkeypatch.setattr(CovapieCurrent11AuxiliaryModelV1, "__init__", _forbidden)
    monkeypatch.setattr(CovapieCurrent11AuxiliaryModelV1, "forward", _forbidden)
    monkeypatch.setattr(LigandPocketDDPM, "configure_optimizers", _forbidden)
    monkeypatch.setattr(LigandPocketDDPM, "training_step", _forbidden)
    monkeypatch.setattr(LigandPocketDDPM, "load_from_checkpoint", _forbidden)
    monkeypatch.setattr(pl.Trainer, "__init__", _forbidden)
    monkeypatch.setattr(pl.Trainer, "fit", _forbidden)
    monkeypatch.setattr(pl.Trainer, "validate", _forbidden)
    monkeypatch.setattr(pl.Trainer, "test", _forbidden)
    monkeypatch.setattr(pl.Trainer, "save_checkpoint", _forbidden)
    yield
    monkeypatch.undo()


@pytest.fixture(scope="module")
def train12_runtime():
    patcher = pytest.MonkeyPatch()
    real_validator = composer_owner.validate_covapie_train12_cpu_epoch_batch_v1
    real_train10_prepare = (
        composer_owner.train10.prepare_covapie_train10_cpu_batch_composer_v1
    )
    real_ready2_prepare = (
        composer_owner.ready2.prepare_covapie_jug_gjj_ready2_data_adapter_v1
    )
    real_train10_build = (
        composer_owner.train10.build_covapie_train10_cpu_epoch_batch_v1
    )
    real_ready2_build = (
        composer_owner.ready2
        .build_covapie_jug_gjj_ready2_canonical_task_data_v1
    )

    def validator_spy(batch: object, prepared: object) -> bool:
        FACTS["train12_public_validator"] += 1
        return real_validator(batch, prepared)

    def train10_prepare_spy(*args: object, **kwargs: object):
        FACTS["train10_prepare"] += 1
        return real_train10_prepare(*args, **kwargs)

    def ready2_prepare_spy(*args: object, **kwargs: object):
        FACTS["ready2_prepare"] += 1
        return real_ready2_prepare(*args, **kwargs)

    def train10_build_spy(*args: object, **kwargs: object):
        FACTS["train10_build"] += 1
        return real_train10_build(*args, **kwargs)

    def ready2_build_spy(*args: object, **kwargs: object):
        FACTS["ready2_build_including_fresh_validator_references"] += 1
        return real_ready2_build(*args, **kwargs)

    patcher.setattr(
        composer_owner,
        "validate_covapie_train12_cpu_epoch_batch_v1",
        validator_spy,
    )
    patcher.setattr(
        composer_owner.train10,
        "prepare_covapie_train10_cpu_batch_composer_v1",
        train10_prepare_spy,
    )
    patcher.setattr(
        composer_owner.ready2,
        "prepare_covapie_jug_gjj_ready2_data_adapter_v1",
        ready2_prepare_spy,
    )
    patcher.setattr(
        composer_owner.train10,
        "build_covapie_train10_cpu_epoch_batch_v1",
        train10_build_spy,
    )
    patcher.setattr(
        composer_owner.ready2,
        "build_covapie_jug_gjj_ready2_canonical_task_data_v1",
        ready2_build_spy,
    )
    FACTS["train12_prepare"] += 1
    prepared = composer_owner.prepare_covapie_train12_cpu_batch_composer_v1(
        ROOT, STATE_ROOT, CACHE_ROOT
    )
    carriers = []
    for epoch in range(5):
        FACTS["train12_build"] += 1
        carriers.append(
            composer_owner.build_covapie_train12_cpu_epoch_batch_v1(
                prepared, epoch, 0
            )
        )
    yield prepared, tuple(carriers)
    patcher.undo()


def _assert_exact(left: object, right: object) -> None:
    assert type(left) is type(right)
    if isinstance(left, torch.Tensor):
        assert left.dtype == right.dtype
        assert left.shape == right.shape
        assert left.device == right.device
        torch.testing.assert_close(left, right, rtol=0, atol=0, equal_nan=True)
    elif is_dataclass(left):
        for field in fields(left):
            _assert_exact(getattr(left, field.name), getattr(right, field.name))
    elif isinstance(left, dict):
        assert tuple(left) == tuple(right)
        for key in left:
            _assert_exact(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert len(left) == len(right)
        for left_item, right_item in zip(left, right):
            _assert_exact(left_item, right_item)
    elif isinstance(left, float) and math.isnan(left):
        assert math.isnan(right)
    else:
        assert left == right


def _prepared_fingerprint(prepared: object) -> tuple[object, ...]:
    return (
        id(prepared),
        prepared._repo,
        prepared._state,
        prepared._cache,
        prepared._seal,
        prepared._helper_bindings,
        prepared._train10._seal,
        prepared._ready2._seal,
        composer_owner._prepared_seal(prepared),
    )


def _synthetic_trace(carrier) -> CovapieCurrent11DiffusionForwardTraceV1:
    supervision = carrier.supervision
    ligand_count = len(carrier.model_input_batch["lig_mask"])
    pocket_count = len(carrier.model_input_batch["pocket_mask"])
    batch_size = len(carrier.sample_identities)
    ligand_hidden = (
        torch.arange(ligand_count * 4, dtype=torch.float32).reshape(-1, 4)
        / 97.0
    )
    pocket_hidden = (
        torch.arange(pocket_count * 4, dtype=torch.float32).reshape(-1, 4)
        / 131.0
    )
    ligand_xh = torch.cat(
        (
            carrier.model_input_batch["lig_coords"].clone(),
            torch.zeros((ligand_count, 10)),
        ),
        dim=1,
    )
    pocket_xh = torch.cat(
        (
            carrier.model_input_batch["pocket_coords"].clone(),
            torch.zeros((pocket_count, 10)),
        ),
        dim=1,
    )
    return CovapieCurrent11DiffusionForwardTraceV1(
        diffusion_epsilon_prediction_ligand=torch.full_like(ligand_xh, 0.125),
        diffusion_epsilon_prediction_pocket=torch.full_like(pocket_xh, -0.25),
        diffusion_timestep_int=torch.arange(batch_size, dtype=torch.long) + 2,
        noised_ligand_xh=ligand_xh + 0.1,
        sampled_epsilon_ligand=torch.full_like(ligand_xh, 0.25),
        clean_centered_ligand_xh=ligand_xh.clone(),
        clean_centered_pocket_xh=pocket_xh,
        denoised_ligand_xh=ligand_xh + 0.2,
        ligand_node_hidden=ligand_hidden,
        pocket_node_hidden=pocket_hidden,
        role_mask_anchor_hidden_delta=torch.zeros_like(ligand_hidden),
        ligand_coordinate_update_mask=(
            supervision.ligand_base_generation_mask.clone()
        ),
        masked_t_gt_0_error_per_sample=torch.linspace(0.2, 0.6, batch_size),
        masked_t0_x_per_sample=torch.linspace(0.1, 0.5, batch_size),
        masked_t0_h_per_sample=torch.linspace(0.3, 0.7, batch_size),
        masked_kl_prior_per_sample=torch.linspace(0.05, 0.25, batch_size),
        base_objective_per_sample=torch.linspace(0.4, 0.8, batch_size),
        coordinate_normalization=1.0,
    )


def _synthetic_model_output(
    carrier,
    trace: CovapieCurrent11DiffusionForwardTraceV1,
    *,
    post_overrides: dict[int, float] | None = None,
    output_corruption: str | None = None,
) -> CovapieCurrent11ModelOutputV1:
    supervision = carrier.supervision
    candidate_count = len(supervision.pair_candidate_batch_index)
    batch_size = len(carrier.sample_identities)
    pair_logits = torch.linspace(-1.75, 2.25, candidate_count)
    geometry = torch.stack(
        (
            torch.linspace(0.65, 2.65, candidate_count),
            torch.linspace(1.05, 3.95, candidate_count),
        ),
        dim=1,
    )
    for sample in range(batch_size):
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        if not bool(supervision.pair_positive_candidate_valid[sample].item()):
            continue
        for component in range(2):
            target = supervision.pre_post_geometry_target_angstrom[
                sample, component
            ]
            if (
                bool(
                    supervision.pre_post_geometry_component_valid_mask[
                        sample, component
                    ].item()
                )
                and bool(torch.isfinite(target).item())
            ):
                geometry[positive, component] = (
                    target + 0.2 + 0.07 * sample + 0.03 * component
                )
    for sample, value in (post_overrides or {}).items():
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        assert bool(supervision.pair_positive_candidate_valid[sample].item())
        geometry[positive, POST] = value
    ligand_flat = supervision.pair_candidate_ligand_flat_index.clone()
    offsets = supervision.pair_candidate_offsets.clone()
    task_ids = supervision.canonical_task_id.clone()
    if output_corruption == "flat_membership":
        ligand_flat[0] = ligand_flat[0] + 1
    elif output_corruption == "offsets":
        offsets[1] = offsets[1] + 1
    elif output_corruption == "task":
        task_ids[0] = (task_ids[0] + 1) % 5
    assert bool(torch.isfinite(geometry).all().item())
    return CovapieCurrent11ModelOutputV1(
        diffusion_epsilon_prediction_ligand=(
            trace.diffusion_epsilon_prediction_ligand
        ),
        denoised_ligand_xh=trace.denoised_ligand_xh,
        diffusion_timestep_int=trace.diffusion_timestep_int,
        ligand_node_hidden=trace.ligand_node_hidden,
        pocket_node_hidden=trace.pocket_node_hidden,
        role_mask_anchor_hidden_delta=trace.role_mask_anchor_hidden_delta,
        pair_embeddings=(
            torch.arange(candidate_count * 4, dtype=torch.float32).reshape(-1, 4)
            / 83.0
        ),
        pair_logits=pair_logits,
        pre_post_geometry_predictions_angstrom=geometry,
        target_pair_consistency=torch.ones(batch_size, dtype=torch.bool),
        canonical_task_id=task_ids,
        pair_candidate_offsets=offsets,
        pair_candidate_batch_index=(
            supervision.pair_candidate_batch_index.clone()
        ),
        pair_candidate_ligand_local_index=(
            supervision.pair_candidate_ligand_local_index.clone()
        ),
        pair_candidate_residue_local_index=(
            supervision.pair_candidate_residue_local_index.clone()
        ),
        pair_candidate_ligand_flat_index=ligand_flat,
        pair_candidate_pocket_flat_index=(
            supervision.pair_candidate_pocket_flat_index.clone()
        ),
    )


class _SyntheticAuxiliaryBoundary:
    def __init__(
        self,
        carrier,
        trace: CovapieCurrent11DiffusionForwardTraceV1,
        *,
        post_overrides: dict[int, float] | None = None,
        output_corruption: str | None = None,
    ) -> None:
        self.carrier = carrier
        self.trace = trace
        self.post_overrides = post_overrides
        self.output_corruption = output_corruption
        self.encode_calls: list[dict[str, object]] = []
        self.forward_calls: list[dict[str, object]] = []

    def encode_role_mask_anchor_v1(self, **kwargs: object) -> torch.Tensor:
        FACTS["synthetic_role_encoding"] += 1
        self.encode_calls.append(kwargs)
        return self.trace.role_mask_anchor_hidden_delta

    def __call__(self, **kwargs: object) -> CovapieCurrent11ModelOutputV1:
        FACTS["synthetic_auxiliary_prediction"] += 1
        self.forward_calls.append(kwargs)
        return _synthetic_model_output(
            self.carrier,
            self.trace,
            post_overrides=self.post_overrides,
            output_corruption=self.output_corruption,
        )


class _ForwardHarness:
    """Lightweight CPU receiver for the adapter's real orchestration methods."""

    bind_covapie_train12_prepared_context_v1 = (
        subject.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1
        .bind_covapie_train12_prepared_context_v1
    )
    forward = subject.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1.forward

    def __init__(
        self,
        carrier,
        prepared,
        *,
        enabled: bool = True,
        bind: bool = True,
        training: object = True,
        current_epoch: object = None,
        task_schedule_seed: object = None,
        device: torch.device = torch.device("cpu"),
        loss_weights: CovapieCurrent11LossWeightsV1 | None = None,
        post_overrides: dict[int, float] | None = None,
        output_corruption: str | None = None,
        transport_corruption: str | None = None,
    ) -> None:
        self.training = training
        self.current_epoch = (
            carrier.epoch if current_epoch is None else current_epoch
        )
        self.covapie_current11_task_schedule_seed = (
            carrier.task_schedule_seed
            if task_schedule_seed is None
            else task_schedule_seed
        )
        self.covapie_train12_hidden_post_forward_enabled = enabled
        self._covapie_train12_bound_prepared_v1 = None
        self._covapie_train12_bound_prepared_identity_v1 = None
        self._covapie_train12_bound_prepared_seal_v1 = None
        self._covapie_train12_bound_repository_root_v1 = None
        self.covapie_current11_pair_contrastive_temperature = 1.0
        self.covapie_current11_loss_weights = loss_weights or (
            CovapieCurrent11LossWeightsV1(
                base_diffusion=0.0,
                covalent_pair_prediction=0.0,
                pre_post_geometry=1.0,
                covalent_pair_contrastive=0.0,
            )
        )
        self.virtual_nodes = False
        self.device = device
        self.ddpm = object()
        self.trace = _synthetic_trace(carrier)
        self.covapie_current11_auxiliary_model_v1 = _SyntheticAuxiliaryBoundary(
            carrier,
            self.trace,
            post_overrides=post_overrides,
            output_corruption=output_corruption,
        )
        self.transport_corruption = transport_corruption
        self.transport_calls: list[tuple[dict[str, object], dict[str, object]]] = []
        self.bridge_calls: list[dict[str, object]] = []
        self.loss_calls: list[dict[str, object]] = []
        if bind:
            self.bind_covapie_train12_prepared_context_v1(prepared)

    def get_ligand_and_pocket(self, data: object):
        FACTS["transport"] += 1
        ligand, pocket = LigandPocketDDPM.get_ligand_and_pocket(self, data)
        if self.transport_corruption == "membership":
            ligand = dict(ligand)
            ligand["mask"] = ligand["mask"].clone()
            ligand["mask"][0] = 1
        elif self.transport_corruption == "size":
            pocket = dict(pocket)
            pocket["size"] = pocket["size"].clone()
            pocket["size"][0] += 1
        elif self.transport_corruption == "node_count":
            ligand = dict(ligand)
            ligand["x"] = ligand["x"][:-1]
        elif self.transport_corruption == "order":
            pocket = dict(pocket)
            pocket["x"] = pocket["x"].clone()
            pocket["x"][[0, 1]] = pocket["x"][[1, 0]]
        self.transport_calls.append((ligand, pocket))
        return ligand, pocket


def _install_synthetic_boundaries(
    monkeypatch: pytest.MonkeyPatch, harness: _ForwardHarness
) -> None:
    def bridge(**kwargs: object) -> CovapieCurrent11DiffusionForwardTraceV1:
        FACTS["synthetic_diffusion_bridge"] += 1
        harness.bridge_calls.append(kwargs)
        return harness.trace

    def loss_spy(**kwargs: object):
        FACTS["production_loss"] += 1
        harness.loss_calls.append(kwargs)
        return loss_owner.compute_covapie_current11_training_losses_v1(**kwargs)

    monkeypatch.setattr(
        subject,
        "run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
        bridge,
    )
    monkeypatch.setattr(
        subject, "compute_covapie_current11_training_losses_v1", loss_spy
    )


def _run_forward(harness: _ForwardHarness, carrier):
    with torch.no_grad():
        return harness.forward(carrier)


def _hidden_post_oracle(carrier) -> tuple[int, ...]:
    """Independent scalar oracle; never calls the production mask helper."""

    supervision = carrier.supervision
    ligand_membership = carrier.model_input_batch["lig_mask"]
    pocket_membership = carrier.model_input_batch["pocket_mask"]
    eligible = []
    for sample in range(12):
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        if not bool(supervision.pair_positive_candidate_valid[sample].item()):
            continue
        ligand_flat = int(
            supervision.pair_candidate_ligand_flat_index[positive].item()
        )
        pocket_flat = int(
            supervision.pair_candidate_pocket_flat_index[positive].item()
        )
        # The component loss mask is the authoritative native POST request.
        checks = (
            bool(supervision.sample_training_admitted[sample].item()),
            bool(supervision.canonical_task_valid[sample].item()),
            bool(
                supervision.pre_post_geometry_component_loss_mask[
                    sample, POST
                ].item()
            ),
            bool(
                supervision.pre_post_geometry_component_valid_mask[
                    sample, POST
                ].item()
            ),
            bool(supervision.target_residue_condition_valid[sample].item()),
            bool(supervision.pair_candidate_is_positive[positive].item()),
            int(supervision.pair_candidate_batch_index[positive].item())
            == sample,
            int(ligand_membership[ligand_flat].item()) == sample,
            int(pocket_membership[pocket_flat].item()) == sample,
            pocket_flat
            == int(
                supervision.target_residue_reactive_atom_flat_index[
                    sample
                ].item()
            ),
            bool(supervision.ligand_role_valid[ligand_flat].item()),
            int(supervision.ligand_role_id[ligand_flat].item()) == 2,
            bool(
                supervision.ligand_base_generation_mask[ligand_flat, 0].item()
            ),
            not bool(supervision.ligand_base_fixed_mask[ligand_flat, 0].item()),
        )
        if all(checks):
            eligible.append(sample)
    return tuple(eligible)


def _smooth_l1_oracle(prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    error = torch.abs(prediction - target)
    return torch.where(error < 1.0, 0.5 * error.square(), error - 0.5)


def _geometry_oracle(carrier, model_output) -> tuple[torch.Tensor, torch.Tensor]:
    eligible = _hidden_post_oracle(carrier)
    diagnostic = torch.full((12,), float("nan"), dtype=torch.float32)
    terms = []
    for sample in eligible:
        positive = int(
            carrier.supervision.pair_positive_candidate_index[sample].item()
        )
        term = _smooth_l1_oracle(
            model_output.pre_post_geometry_predictions_angstrom[positive, POST],
            carrier.supervision.pre_post_geometry_target_angstrom[sample, POST],
        )
        diagnostic[sample] = term
        terms.append(term)
    return torch.stack(terms).mean(), diagnostic


def _assert_no_model_boundaries(harness: _ForwardHarness) -> None:
    assert not harness.transport_calls
    assert not harness.bridge_calls
    assert not harness.loss_calls
    assert not harness.covapie_current11_auxiliary_model_v1.encode_calls
    assert not harness.covapie_current11_auxiliary_model_v1.forward_calls


def test_fixed_sources_and_external_candidate_root_binding_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = subject.verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
        repository_root=ROOT
    )
    assert observed == subject.DIRECT_BOUND_SOURCE_SHA256_V1
    assert subject._PUBLISHED_REPOSITORY_ROOT == ROOT
    drifted = list(subject.DIRECT_BOUND_SOURCE_SHA256_V1)
    drifted[0] = (drifted[0][0], "0" * 64)
    monkeypatch.setattr(subject, "DIRECT_BOUND_SOURCE_SHA256_V1", tuple(drifted))
    with pytest.raises(ValueError, match="DIRECT_BOUND_SOURCE_SHA256_MISMATCH"):
        subject.verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
            repository_root=ROOT
        )
    with pytest.raises(
        ValueError, match="REPOSITORY_ROOT_NOT_PUBLISHED_COMPOSER_ROOT"
    ):
        subject.verify_covapie_train12_hidden_post_forward_adapter_sources_v1(
            repository_root=STATE_ROOT
        )


def test_surface_is_thin_inherited_and_prepared_is_not_registered_state(
    train12_runtime,
) -> None:
    prepared, _ = train12_runtime
    adapter = subject.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1
    assert issubclass(adapter, CovapieCurrent11TrainingLigandPocketDDPM)
    assert tuple(inspect.signature(adapter.forward).parameters) == ("self", "data")
    opt_in = inspect.signature(adapter.__init__).parameters[
        "covapie_train12_hidden_post_forward_enabled"
    ]
    assert opt_in.kind is inspect.Parameter.KEYWORD_ONLY
    assert opt_in.default is False
    assert adapter.training_step is CovapieCurrent11TrainingLigandPocketDDPM.training_step
    assert (
        adapter.configure_optimizers
        is CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    )
    source_text = Path(subject.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert not {
        "register_parameter",
        "register_buffer",
        "add_module",
        "save_hyperparameters",
        "backward",
        "step",
        "fit",
        "save",
        "load",
    } & called_attributes
    assert "nn.Parameter" not in source_text
    assert "tensorize_covapie_current11_training_supervision_v1" not in source_text
    assert "super().forward" not in source_text
    assert source_text.count("self.get_ligand_and_pocket(") == 1

    instance = adapter.__new__(adapter)
    torch.nn.Module.__init__(instance)
    instance.covapie_train12_hidden_post_forward_enabled = True
    instance._covapie_train12_bound_prepared_v1 = None
    instance.bind_covapie_train12_prepared_context_v1(prepared)
    assert instance._covapie_train12_bound_prepared_v1 is prepared
    assert tuple(instance.state_dict()) == ()
    assert not instance._parameters and not instance._buffers and not instance._modules


def test_default_opt_in_rejects_before_parent_constructor_or_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        CovapieCurrent11TrainingLigandPocketDDPM, "__init__", _forbidden
    )
    monkeypatch.setattr(LigandPocketDDPM, "get_ligand_and_pocket", _forbidden)
    cls = subject.CovapieTrain12HiddenPostForwardLigandPocketDDPMV1
    with pytest.raises(ValueError, match="EXPLICIT_OPT_IN_REQUIRED"):
        cls()
    with pytest.raises(ValueError, match="EXPLICIT_OPT_IN_REQUIRED"):
        cls(covapie_train12_hidden_post_forward_enabled=False)


def test_fresh_process_adapter_first_import_uses_published_compatibility() -> None:
    code = r'''
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys
from Bio.PDB import Polypeptide
before = hasattr(Polypeptide, "three_to_one")
candidate = os.environ.get("COVAPIE_TRAIN12_FORWARD_ADAPTER_CANDIDATE")
if candidate:
    path = Path(candidate).resolve(strict=True)
    spec = importlib.util.spec_from_file_location("fresh_train12_adapter_candidate", path)
    assert spec is not None and spec.loader is not None
    subject = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = subject
    spec.loader.exec_module(subject)
else:
    from covalent_ext import covapie_train12_hidden_post_forward_adapter_v1 as subject
print(json.dumps({
    "subject_file": str(Path(subject.__file__).resolve(strict=True)),
    "python": sys.version.split()[0],
    "torch": importlib.metadata.version("torch"),
    "biopython": importlib.metadata.version("biopython"),
    "pytorch_lightning": importlib.metadata.version("pytorch-lightning"),
    "torch_scatter": importlib.metadata.version("torch-scatter"),
    "compat_applied": subject.BIOPYTHON_COMPAT_APPLIED_V1,
    "three_to_one_before": before,
    "three_to_one_after": hasattr(Polypeptide, "three_to_one"),
}))
'''
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(ROOT / "src"), str(ROOT)))
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    record = json.loads(completed.stdout.strip().splitlines()[-1])
    assert record["python"] == sys.version.split()[0]
    assert record["torch"] == importlib.metadata.version("torch")
    assert record["biopython"] == importlib.metadata.version("biopython")
    assert record["pytorch_lightning"] == importlib.metadata.version(
        "pytorch-lightning"
    )
    assert record["torch_scatter"] == importlib.metadata.version("torch-scatter")
    assert record["three_to_one_before"] is False
    assert record["compat_applied"] is True
    assert record["three_to_one_after"] is True
    assert Path(record["subject_file"]) == Path(subject.__file__).resolve()


def test_real_train12_epoch_cycle_routes_once_and_matches_independent_oracles(
    train12_runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepared, carriers = train12_runtime
    prepared_before = _prepared_fingerprint(prepared)
    for epoch, carrier in enumerate(carriers):
        assert carrier.epoch == epoch
        before = copy.deepcopy(carrier)
        harness = _ForwardHarness(carrier, prepared)
        with monkeypatch.context() as context:
            _install_synthetic_boundaries(context, harness)
            output = _run_forward(harness, carrier)
        eligible = _hidden_post_oracle(carrier)
        oracle_loss, oracle_diagnostic = _geometry_oracle(
            carrier, output.model_output
        )
        assert type(output) is CovapieCurrent11TrainingForwardOutputV1
        assert output.supervision is carrier.supervision
        assert output.diffusion_trace is harness.trace
        assert output.loss_output.pre_post_geometry_valid_sample_count == len(
            eligible
        )
        torch.testing.assert_close(
            output.loss_output.loss_pre_post_geometry, oracle_loss
        )
        torch.testing.assert_close(
            output.loss_output.pre_post_geometry_per_sample_detached,
            oracle_diagnostic,
            equal_nan=True,
        )
        assert len(harness.transport_calls) == 1
        assert len(harness.covapie_current11_auxiliary_model_v1.encode_calls) == 1
        assert len(harness.bridge_calls) == 1
        assert len(harness.covapie_current11_auxiliary_model_v1.forward_calls) == 1
        assert len(harness.loss_calls) == 1
        ligand, pocket = harness.transport_calls[0]
        role_call = harness.covapie_current11_auxiliary_model_v1.encode_calls[0]
        bridge_call = harness.bridge_calls[0]
        loss_call = harness.loss_calls[0]
        assert role_call["ligand_batch_index"] is ligand["mask"]
        assert bridge_call["ligand"] is ligand
        assert bridge_call["pocket"] is pocket
        assert loss_call["ligand_batch_index"] is ligand["mask"]
        assert loss_call["pocket_batch_index"] is pocket["mask"]
        assert loss_call["post_geometry_loss_purpose"] == (
            "independent_hidden_post_distance_v1"
        )
        assert loss_call["supervision"] is carrier.supervision
        indicator = carrier.supervision.target_residue_reactive_atom_mask
        passed_indicator = bridge_call[
            "pocket_target_residue_atom_condition_indicator"
        ]
        assert passed_indicator.data_ptr() == indicator.data_ptr()
        torch.testing.assert_close(passed_indicator, indicator[:, 0])
        source_counts = {
            "train10": sum(sample < 10 for sample in eligible),
            "JUG": sum(sample == 10 for sample in eligible),
            "GJJ": sum(sample == 11 for sample in eligible),
        }
        EPOCH_FACTS.append(
            {
                "epoch": epoch,
                "tasks": carrier.scheduled_task_ids,
                "eligible_samples": eligible,
                "eligible_events": tuple(
                    carrier.canonical_event_ids[sample] for sample in eligible
                ),
                "eligible_identities": tuple(
                    carrier.sample_identities[sample] for sample in eligible
                ),
                "source_counts": source_counts,
            }
        )
        _assert_exact(carrier, before)
        assert _prepared_fingerprint(prepared) == prepared_before
    assert len(EPOCH_FACTS) == 5
    print("HIDDEN_POST_EPOCH_FACTS=" + repr(EPOCH_FACTS))


def test_jug_post_inactive_and_gjj_native_labels_with_b3_exclusion(
    train12_runtime,
) -> None:
    _, carriers = train12_runtime
    gjj_b3_seen = False
    for carrier in carriers:
        supervision = carrier.supervision
        eligible = set(_hidden_post_oracle(carrier))
        assert not bool(
            supervision.pre_post_geometry_component_valid_mask[:, 0]
            .any()
            .item()
        )
        assert not bool(
            supervision.pre_post_geometry_component_loss_mask[:, 0]
            .any()
            .item()
        )
        assert bool(
            torch.isnan(
                supervision.pre_post_geometry_target_angstrom[:, 0]
            )
            .all()
            .item()
        )
        assert not bool(
            supervision.pre_post_geometry_component_valid_mask[10, POST].item()
        )
        assert not bool(
            supervision.pre_post_geometry_component_loss_mask[10, POST].item()
        )
        assert torch.isnan(
            supervision.pre_post_geometry_target_angstrom[10, POST]
        )
        assert 10 not in eligible
        assert bool(
            supervision.pre_post_geometry_component_valid_mask[11, POST].item()
        )
        assert bool(
            supervision.pre_post_geometry_component_loss_mask[11, POST].item()
        )
        assert torch.isfinite(
            supervision.pre_post_geometry_target_angstrom[11, POST]
        )
        positive = int(supervision.pair_positive_candidate_index[11].item())
        ligand_flat = int(
            supervision.pair_candidate_ligand_flat_index[positive].item()
        )
        hidden_endpoint = bool(
            supervision.ligand_base_generation_mask[ligand_flat, 0].item()
            and not supervision.ligand_base_fixed_mask[ligand_flat, 0].item()
        )
        assert (11 in eligible) == hidden_endpoint
        if carrier.scheduled_task_ids[11] == 3:
            gjj_b3_seen = True
            assert not hidden_endpoint
            assert 11 not in eligible
            assert bool(
                supervision.pre_post_geometry_component_valid_mask[
                    11, POST
                ].item()
            )
            assert bool(
                supervision.pre_post_geometry_component_loss_mask[
                    11, POST
                ].item()
            )
    assert gjj_b3_seen


def test_excluded_predictions_are_inert_and_eligible_prediction_changes_loss(
    train12_runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepared, carriers = train12_runtime
    carrier = next(value for value in carriers if _hidden_post_oracle(value))
    eligible = _hidden_post_oracle(carrier)
    excluded = tuple(
        sample
        for sample in range(12)
        if sample not in eligible
        and bool(
            carrier.supervision.pair_positive_candidate_valid[sample].item()
        )
    )
    assert excluded
    baseline = _ForwardHarness(carrier, prepared)
    excluded_changed = _ForwardHarness(
        carrier,
        prepared,
        post_overrides={sample: 40.0 + sample for sample in excluded},
    )
    participant_changed = _ForwardHarness(
        carrier,
        prepared,
        post_overrides={eligible[0]: 55.0},
    )
    outputs = []
    for harness in (baseline, excluded_changed, participant_changed):
        with monkeypatch.context() as context:
            _install_synthetic_boundaries(context, harness)
            outputs.append(_run_forward(harness, carrier))
    first, second, third = outputs
    torch.testing.assert_close(
        first.loss_output.loss_pre_post_geometry,
        second.loss_output.loss_pre_post_geometry,
    )
    assert not torch.equal(
        first.loss_output.loss_pre_post_geometry,
        third.loss_output.loss_pre_post_geometry,
    )
    third_oracle, third_diagnostic = _geometry_oracle(carrier, third.model_output)
    torch.testing.assert_close(third.loss_output.loss_pre_post_geometry, third_oracle)
    torch.testing.assert_close(
        third.loss_output.pre_post_geometry_per_sample_detached,
        third_diagnostic,
        equal_nan=True,
    )


def test_prepared_binding_gate_type_root_source_seal_and_rebinding(
    train12_runtime,
) -> None:
    prepared, carriers = train12_runtime
    carrier = carriers[0]
    disabled = _ForwardHarness(carrier, prepared, enabled=False, bind=False)
    with pytest.raises(ValueError, match="EXPLICIT_OPT_IN_REQUIRED"):
        disabled.bind_covapie_train12_prepared_context_v1(prepared)
    harness = _ForwardHarness(carrier, prepared, bind=False)
    with pytest.raises(ValueError, match="PREPARED_CONTEXT_TYPE_INVALID"):
        harness.bind_covapie_train12_prepared_context_v1(object())

    wrong_root = copy.deepcopy(prepared)
    wrong_root._repo = STATE_ROOT
    with pytest.raises(ValueError, match="REPOSITORY_ROOT_NOT_PUBLISHED"):
        harness.bind_covapie_train12_prepared_context_v1(wrong_root)
    wrong_source = copy.deepcopy(prepared)
    wrong_source._helper_bindings = ()
    with pytest.raises(ValueError, match="PUBLISHED_PREPARED_VALIDATOR_REJECTED"):
        harness.bind_covapie_train12_prepared_context_v1(wrong_source)
    wrong_seal = copy.deepcopy(prepared)
    wrong_seal._seal = "0" * 64
    with pytest.raises(ValueError, match="PUBLISHED_PREPARED_VALIDATOR_REJECTED"):
        harness.bind_covapie_train12_prepared_context_v1(wrong_seal)

    harness.bind_covapie_train12_prepared_context_v1(prepared)
    assert harness._covapie_train12_bound_prepared_v1 is prepared
    with pytest.raises(ValueError, match="PREPARED_CONTEXT_ALREADY_BOUND"):
        harness.bind_covapie_train12_prepared_context_v1(prepared)
    with pytest.raises(ValueError, match="PREPARED_CONTEXT_ALREADY_BOUND"):
        harness.bind_covapie_train12_prepared_context_v1(copy.deepcopy(prepared))


@pytest.mark.parametrize(
    ("case", "error"),
    (
        ("disabled", "EXPLICIT_OPT_IN_REQUIRED"),
        ("unbound", "PREPARED_CONTEXT_REQUIRED"),
        ("evaluation", "LIFECYCLE_TRAINING_MODE_REQUIRED"),
        ("epoch", "LIFECYCLE_EPOCH_MISMATCH"),
        ("epoch_bool", "LIFECYCLE_EPOCH_MISMATCH"),
        ("epoch_range", "LIFECYCLE_EPOCH_MISMATCH"),
        ("seed", "LIFECYCLE_TASK_SCHEDULE_SEED_MISMATCH"),
        ("seed_bool", "LIFECYCLE_TASK_SCHEDULE_SEED_MISMATCH"),
        ("device", "LIFECYCLE_CPU_DEVICE_REQUIRED"),
    ),
)
def test_opt_in_binding_lifecycle_epoch_seed_and_cpu_fail_before_transport(
    train12_runtime,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    error: str,
) -> None:
    prepared, carriers = train12_runtime
    carrier = carriers[0]
    harness = _ForwardHarness(
        carrier,
        prepared,
        enabled=case != "disabled",
        bind=case not in ("disabled", "unbound"),
        training=False if case == "evaluation" else True,
        current_epoch=(
            carrier.epoch + 1
            if case == "epoch"
            else True
            if case == "epoch_bool"
            else 5
            if case == "epoch_range"
            else None
        ),
        task_schedule_seed=(
            1
            if case == "seed"
            else True
            if case == "seed_bool"
            else None
        ),
        device=torch.device("meta") if case == "device" else torch.device("cpu"),
    )
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        with pytest.raises(ValueError, match=error):
            _run_forward(harness, carrier)
    _assert_no_model_boundaries(harness)


def test_bound_prepared_identity_and_post_bind_mutation_fail_before_transport(
    train12_runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepared, carriers = train12_runtime
    carrier = carriers[0]
    first = _ForwardHarness(carrier, prepared)
    first._covapie_train12_bound_prepared_v1 = copy.deepcopy(prepared)
    second_prepared = copy.deepcopy(prepared)
    second = _ForwardHarness(carrier, second_prepared)
    second_prepared._seal = "f" * 64
    for harness in (first, second):
        with monkeypatch.context() as context:
            _install_synthetic_boundaries(context, harness)
            with pytest.raises(
                ValueError, match="PREPARED_CONTEXT_IDENTITY_OR_SEAL_CHANGED"
            ):
                _run_forward(harness, carrier)
        _assert_no_model_boundaries(harness)


@pytest.mark.parametrize("input_kind", ("dict", "namespace", "train10"))
def test_non_train12_carrier_types_reject_before_transport(
    train12_runtime,
    monkeypatch: pytest.MonkeyPatch,
    input_kind: str,
) -> None:
    prepared, carriers = train12_runtime
    harness = _ForwardHarness(carriers[0], prepared)
    invalid = (
        {}
        if input_kind == "dict"
        else SimpleNamespace(sample_identities=tuple(range(12)))
        if input_kind == "namespace"
        else carriers[0].source_audit_blocks[0].source_object
    )
    assert input_kind != "train10" or type(invalid) is train10_owner.CovapieTrain10CpuEpochBatchV1
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        with pytest.raises(ValueError, match="CARRIER_BOUNDARY_TYPE_INVALID"):
            _run_forward(harness, invalid)
    _assert_no_model_boundaries(harness)


@pytest.mark.parametrize(
    "changes",
    (
        {
            "sample_identities": ("FORGED",)
            + composer_owner.TRAIN12_SAMPLE_IDENTITIES_V1[1:]
        },
        {"formal_splits": ("validation",) + ("train",) * 11},
        {"prepared_source_seal": "0" * 64},
    ),
)
def test_carrier_source_metadata_drift_rejected_by_published_validator(
    train12_runtime,
    monkeypatch: pytest.MonkeyPatch,
    changes: dict[str, object],
) -> None:
    prepared, carriers = train12_runtime
    carrier = replace(copy.deepcopy(carriers[0]), **changes)
    harness = _ForwardHarness(carrier, prepared)
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        with pytest.raises(
            ValueError, match="PUBLISHED_COMPOSER_VALIDATOR_REJECTED"
        ) as captured:
            _run_forward(harness, carrier)
    assert str(captured.value.__cause__).startswith(
        composer_owner.TRAIN12_CPU_BATCH_COMPOSER_ERROR_V1
    )
    _assert_no_model_boundaries(harness)


def test_carrier_core_and_seal_drift_rejected_before_transport(
    train12_runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepared, carriers = train12_runtime
    carrier = copy.deepcopy(carriers[0])
    carrier.model_input_batch["lig_coords"][0, 0] += 100.0
    harness = _ForwardHarness(carrier, prepared)
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        with pytest.raises(
            ValueError, match="PUBLISHED_COMPOSER_VALIDATOR_REJECTED"
        ):
            _run_forward(harness, carrier)
    _assert_no_model_boundaries(harness)


@pytest.mark.parametrize(
    "corruption", ("membership", "size", "node_count", "order")
)
def test_transport_corruption_rejects_before_neural_boundary(
    train12_runtime,
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    prepared, carriers = train12_runtime
    carrier = carriers[0]
    harness = _ForwardHarness(
        carrier, prepared, transport_corruption=corruption
    )
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        with pytest.raises(ValueError, match="TRANSPORT_BOUNDARY_"):
            _run_forward(harness, carrier)
    assert len(harness.transport_calls) == 1
    assert not harness.bridge_calls
    assert not harness.loss_calls
    assert not harness.covapie_current11_auxiliary_model_v1.encode_calls
    assert not harness.covapie_current11_auxiliary_model_v1.forward_calls


@pytest.mark.parametrize(
    "corruption", ("task", "offsets", "flat_membership")
)
def test_synthetic_output_metadata_mismatch_reaches_real_loss_and_rejects(
    train12_runtime,
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    prepared, carriers = train12_runtime
    carrier = carriers[0]
    harness = _ForwardHarness(
        carrier, prepared, output_corruption=corruption
    )
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        with pytest.raises(
            ValueError, match="PRODUCTION_LOSS_GATE_REJECTED"
        ) as captured:
            _run_forward(harness, carrier)
    assert len(harness.transport_calls) == 1
    assert len(harness.covapie_current11_auxiliary_model_v1.encode_calls) == 1
    assert len(harness.bridge_calls) == 1
    assert len(harness.covapie_current11_auxiliary_model_v1.forward_calls) == 1
    assert len(harness.loss_calls) == 1
    assert type(captured.value.__cause__) is ValueError
    assert str(captured.value.__cause__) == AUXILIARY_ERROR


@pytest.mark.parametrize(
    "weights",
    (
        CovapieCurrent11LossWeightsV1(),
        CovapieCurrent11LossWeightsV1(
            base_diffusion=0.0,
            covalent_pair_prediction=0.0,
            pre_post_geometry=2.0,
            covalent_pair_contrastive=0.0,
        ),
    ),
)
def test_default_and_synthetic_loss_weights_route_existing_raw_losses(
    train12_runtime,
    monkeypatch: pytest.MonkeyPatch,
    weights: CovapieCurrent11LossWeightsV1,
) -> None:
    prepared, carriers = train12_runtime
    assert CovapieCurrent11LossWeightsV1() == CovapieCurrent11LossWeightsV1(
        1.0, 1.0, 0.0, 0.1
    )
    carrier = carriers[0]
    harness = _ForwardHarness(carrier, prepared, loss_weights=weights)
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        output = _run_forward(harness, carrier)
    losses = output.loss_output
    expected = (
        weights.base_diffusion * losses.loss_base_diffusion
        + weights.covalent_pair_prediction * losses.loss_covalent_pair_prediction
        + weights.pre_post_geometry * losses.loss_pre_post_geometry
        + weights.covalent_pair_contrastive
        * losses.loss_covalent_pair_contrastive
    )
    torch.testing.assert_close(losses.loss_total, expected)
    assert losses.pre_post_geometry_valid_sample_count == len(
        _hidden_post_oracle(carrier)
    )


def test_adapter_policy_cannot_be_overridden_by_forward_keyword(
    train12_runtime,
) -> None:
    prepared, carriers = train12_runtime
    harness = _ForwardHarness(carriers[0], prepared)
    with pytest.raises(TypeError):
        harness.forward(
            carriers[0],
            post_geometry_loss_purpose="existing_component_masks_v1",
        )
    _assert_no_model_boundaries(harness)


def test_execution_fact_markers_are_explicit(train12_runtime) -> None:
    prepared, carriers = train12_runtime
    assert FACTS["train12_prepare"] == 1
    assert FACTS["train10_prepare"] == 1
    assert FACTS["ready2_prepare"] == 1
    assert FACTS["train12_build"] == 5
    assert FACTS["train10_build"] == 5
    assert len(carriers) == 5
    assert prepared.ready_for_training is False
    print("ACTUAL_PREPARE_BUILD_TRANSPORT_LOSS_COUNTS=" + repr(FACTS))
    print("LOSS_TEST_INPUT_KIND=REAL_TRAIN12_CARRIER_WITH_SYNTHETIC_PREDICTIONS")
    print("PRODUCTION_LOSS_EXECUTED_WITH_SYNTHETIC_PREDICTIONS=true")
    print("REAL_DDPM_EGNN_FORWARD_EXECUTED=false")
    print("REAL_AUXILIARY_NEURAL_FORWARD_EXECUTED=false")
    print("CHECKPOINT_ACCESSED=false")
    print("BACKWARD_EXECUTED=false")
    print("OPTIMIZER_CREATED=false")
    print("TRAINER_CREATED=false")
    print("PARAMETER_UPDATE_PERFORMED_THIS_ROUND=false")
