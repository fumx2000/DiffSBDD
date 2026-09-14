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
    candidate = os.environ.get("COVAPIE_TRAIN10_FORWARD_ADAPTER_CANDIDATE")
    if candidate is None:
        from covalent_ext import (
            covapie_train10_hidden_post_forward_adapter_v1 as installed,
        )

        return installed
    path = Path(candidate).resolve(strict=True)
    specification = importlib.util.spec_from_file_location(
        "covapie_train10_hidden_post_forward_adapter_v1_candidate", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


# The subject applies the published Biopython compatibility entry point before
# importing the real training owner.  Do not pre-import that owner in the test.
subject = _load_subject()

from covalent_ext import (
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as batch001_owner,
)
from covalent_ext import covapie_train10_cpu_batch_composer_v1 as composer_owner
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


ERROR = subject.COVAPIE_TRAIN10_HIDDEN_POST_FORWARD_ADAPTER_ERROR_V1
POST = 1


def _required_root(name: str) -> Path:
    configured = os.environ.get(name)
    assert configured is not None
    return Path(configured).resolve(strict=True)


ROOT = _required_root("COVAPIE_TEST_REPOSITORY_ROOT")
STATE_ROOT = _required_root("COVAPIE_TEST_STATE_ROOT")
CACHE_ROOT = _required_root("COVAPIE_TEST_CACHE_ROOT")


def _forbidden(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("forbidden checkpoint/model/training operation was invoked")


@pytest.fixture(autouse=True)
def no_real_model_or_training_operations(monkeypatch: pytest.MonkeyPatch) -> None:
    """The suite executes production loss only, using synthetic predictions."""

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
    monkeypatch.setattr(CovapieCurrent11AuxiliaryModelV1, "forward", _forbidden)
    monkeypatch.setattr(LigandPocketDDPM, "configure_optimizers", _forbidden)
    monkeypatch.setattr(LigandPocketDDPM, "training_step", _forbidden)
    monkeypatch.setattr(LigandPocketDDPM, "load_from_checkpoint", _forbidden)
    monkeypatch.setattr(pl.Trainer, "__init__", _forbidden)
    monkeypatch.setattr(pl.Trainer, "fit", _forbidden)
    monkeypatch.setattr(pl.Trainer, "validate", _forbidden)
    monkeypatch.setattr(pl.Trainer, "test", _forbidden)
    monkeypatch.setattr(pl.Trainer, "save_checkpoint", _forbidden)


@pytest.fixture(scope="module")
def prepared():
    return composer_owner.prepare_covapie_train10_cpu_batch_composer_v1(
        ROOT, STATE_ROOT, CACHE_ROOT
    )


@pytest.fixture(scope="module")
def carriers(prepared):
    return tuple(
        composer_owner.build_covapie_train10_cpu_epoch_batch_v1(
            prepared, epoch, 0
        )
        for epoch in range(5)
    )


@pytest.fixture(scope="module")
def real_batch001_train5():
    return batch001_owner.build_covapie_batch001_model_usable_split_batch_v1(
        split="train",
        epoch=0,
        task_schedule_seed=0,
        repository_root=ROOT,
        cache_root=CACHE_ROOT,
    )


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
    excluded_post_overrides: dict[int, float] | None = None,
    corrupt_output_membership: bool = False,
) -> CovapieCurrent11ModelOutputV1:
    supervision = carrier.supervision
    candidate_count = len(supervision.pair_candidate_batch_index)
    pair_logits = torch.linspace(-1.75, 2.25, candidate_count)
    # Every prediction starts finite.  Targets are read only where the original
    # carrier declares that component valid and finite.
    geometry = torch.stack(
        (
            torch.linspace(0.65, 2.65, candidate_count),
            torch.linspace(1.05, 3.95, candidate_count),
        ),
        dim=1,
    )
    for sample in range(len(carrier.sample_identities)):
        positive = int(supervision.pair_positive_candidate_index[sample].item())
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
    for sample, value in (excluded_post_overrides or {}).items():
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        geometry[positive, POST] = value
    assert bool(torch.isfinite(geometry).all().item())
    ligand_flat = supervision.pair_candidate_ligand_flat_index.clone()
    if corrupt_output_membership:
        ligand_flat[0] = ligand_flat[0] + 1
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
        target_pair_consistency=torch.ones(10, dtype=torch.bool),
        canonical_task_id=supervision.canonical_task_id.clone(),
        pair_candidate_offsets=supervision.pair_candidate_offsets.clone(),
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
        excluded_post_overrides: dict[int, float] | None = None,
        corrupt_output_membership: bool = False,
    ) -> None:
        self.carrier = carrier
        self.trace = trace
        self.excluded_post_overrides = excluded_post_overrides
        self.corrupt_output_membership = corrupt_output_membership
        self.encode_calls: list[dict[str, object]] = []
        self.forward_calls: list[dict[str, object]] = []

    def encode_role_mask_anchor_v1(self, **kwargs: object) -> torch.Tensor:
        self.encode_calls.append(kwargs)
        return self.trace.role_mask_anchor_hidden_delta

    def __call__(self, **kwargs: object) -> CovapieCurrent11ModelOutputV1:
        self.forward_calls.append(kwargs)
        return _synthetic_model_output(
            self.carrier,
            self.trace,
            excluded_post_overrides=self.excluded_post_overrides,
            corrupt_output_membership=self.corrupt_output_membership,
        )


class _ForwardHarness:
    """Lightweight CPU self for the adapter's real orchestration method."""

    forward = subject.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1.forward

    def __init__(
        self,
        carrier,
        *,
        enabled: bool = True,
        training: object = True,
        current_epoch: object = None,
        task_schedule_seed: object = None,
        device: torch.device = torch.device("cpu"),
        loss_weights: CovapieCurrent11LossWeightsV1 | None = None,
        excluded_post_overrides: dict[int, float] | None = None,
        corrupt_output_membership: bool = False,
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
        self.covapie_train10_hidden_post_forward_enabled = enabled
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
            excluded_post_overrides=excluded_post_overrides,
            corrupt_output_membership=corrupt_output_membership,
        )
        self.transport_corruption = transport_corruption
        self.transport_calls: list[tuple[dict[str, object], dict[str, object]]] = []
        self.bridge_calls: list[dict[str, object]] = []
        self.loss_calls: list[dict[str, object]] = []

    def get_ligand_and_pocket(self, data: object):
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
        self.transport_calls.append((ligand, pocket))
        return ligand, pocket


def _install_synthetic_boundaries(
    monkeypatch: pytest.MonkeyPatch, harness: _ForwardHarness
) -> None:
    def bridge(**kwargs: object) -> CovapieCurrent11DiffusionForwardTraceV1:
        harness.bridge_calls.append(kwargs)
        return harness.trace

    def loss_spy(**kwargs: object):
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
    """Independent scalar oracle for production hidden-POST eligibility."""

    supervision = carrier.supervision
    ligand_membership = carrier.model_input_batch["lig_mask"]
    pocket_membership = carrier.model_input_batch["pocket_mask"]
    eligible = []
    for sample in range(10):
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        ligand_flat = int(
            supervision.pair_candidate_ligand_flat_index[positive].item()
        )
        pocket_flat = int(
            supervision.pair_candidate_pocket_flat_index[positive].item()
        )
        checks = (
            bool(supervision.sample_training_admitted[sample].item()),
            bool(supervision.canonical_task_valid[sample].item()),
            bool(supervision.target_residue_condition_valid[sample].item()),
            bool(supervision.pair_positive_candidate_valid[sample].item()),
            bool(
                supervision.pre_post_geometry_component_valid_mask[
                    sample, POST
                ].item()
            ),
            bool(
                supervision.pre_post_geometry_component_loss_mask[
                    sample, POST
                ].item()
            ),
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


def _assert_no_model_boundaries(harness: _ForwardHarness) -> None:
    assert not harness.transport_calls
    assert not harness.bridge_calls
    assert not harness.loss_calls
    assert not harness.covapie_current11_auxiliary_model_v1.encode_calls
    assert not harness.covapie_current11_auxiliary_model_v1.forward_calls


def test_fixed_sources_and_external_candidate_root_binding_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = subject.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(
        repository_root=ROOT
    )
    assert observed == subject.DIRECT_BOUND_SOURCE_SHA256_V1
    assert subject._PUBLISHED_REPOSITORY_ROOT == ROOT
    drifted = list(subject.DIRECT_BOUND_SOURCE_SHA256_V1)
    drifted[0] = (drifted[0][0], "0" * 64)
    monkeypatch.setattr(subject, "DIRECT_BOUND_SOURCE_SHA256_V1", tuple(drifted))
    with pytest.raises(ValueError, match="DIRECT_BOUND_SOURCE_SHA256_MISMATCH"):
        subject.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(
            repository_root=ROOT
        )
    with pytest.raises(
        ValueError, match="REPOSITORY_ROOT_NOT_PUBLISHED_COMPOSER_ROOT"
    ):
        subject.verify_covapie_train10_hidden_post_forward_adapter_sources_v1(
            repository_root=STATE_ROOT
        )


def test_surface_is_thin_no_new_registered_state_and_forward_signature_exact() -> None:
    adapter = subject.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1
    assert issubclass(
        adapter,
        CovapieCurrent11TrainingLigandPocketDDPM,
    )
    assert tuple(inspect.signature(adapter.forward).parameters) == ("self", "data")
    opt_in = inspect.signature(adapter.__init__).parameters[
        "covapie_train10_hidden_post_forward_enabled"
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
        "backward",
        "step",
        "fit",
        "save",
        "load",
    } & called_attributes
    assert "nn.Parameter" not in source_text
    assert "synthetic_fixture_mode" not in source_text
    assert "tensorize_covapie_current11_training_supervision_v1" not in source_text
    assert "super().forward" not in source_text


def test_default_opt_in_rejects_before_parent_constructor_or_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        CovapieCurrent11TrainingLigandPocketDDPM, "__init__", _forbidden
    )
    monkeypatch.setattr(LigandPocketDDPM, "get_ligand_and_pocket", _forbidden)
    cls = subject.CovapieTrain10HiddenPostForwardLigandPocketDDPMV1
    with pytest.raises(ValueError, match="EXPLICIT_OPT_IN_REQUIRED"):
        cls()
    with pytest.raises(ValueError, match="EXPLICIT_OPT_IN_REQUIRED"):
        cls(covapie_train10_hidden_post_forward_enabled=False)


def test_fresh_process_import_only_uses_published_biopython_compat() -> None:
    code = r'''
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys
from Bio.PDB import Polypeptide
before = hasattr(Polypeptide, "three_to_one")
candidate = os.environ.get("COVAPIE_TRAIN10_FORWARD_ADAPTER_CANDIDATE")
if candidate:
    path = Path(candidate).resolve(strict=True)
    spec = importlib.util.spec_from_file_location("fresh_train10_adapter_candidate", path)
    assert spec is not None and spec.loader is not None
    subject = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = subject
    spec.loader.exec_module(subject)
else:
    from covalent_ext import covapie_train10_hidden_post_forward_adapter_v1 as subject
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
        filter(None, (str(ROOT / "src"), environment.get("PYTHONPATH", "")))
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


def test_real_train10_epoch_cycle_routes_each_boundary_once_and_matches_oracles(
    carriers, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed_hidden_post_counts = []
    oracle_hidden_post_counts = []
    for epoch, carrier in enumerate(carriers):
        assert carrier.epoch == epoch
        assert composer_owner.validate_covapie_train10_cpu_epoch_batch_v1(carrier)
        before = copy.deepcopy(carrier)
        harness = _ForwardHarness(carrier)
        with monkeypatch.context() as context:
            _install_synthetic_boundaries(context, harness)
            output = _run_forward(harness, carrier)
        eligible = _hidden_post_oracle(carrier)
        observed_hidden_post_counts.append(
            output.loss_output.pre_post_geometry_valid_sample_count
        )
        oracle_hidden_post_counts.append(len(eligible))
        assert type(output) is CovapieCurrent11TrainingForwardOutputV1
        assert output.supervision is carrier.supervision
        assert output.diffusion_trace is harness.trace
        assert output.loss_output.base_diffusion_valid_sample_count == int(
            carrier.supervision.sample_training_admitted.sum().item()
        )
        assert output.loss_output.covalent_pair_prediction_valid_sample_count == int(
            carrier.supervision.pair_positive_candidate_valid.sum().item()
        )
        assert output.loss_output.covalent_pair_contrastive_valid_sample_count == int(
            carrier.supervision.pair_contrastive_sample_loss_mask.sum().item()
        )
        assert output.loss_output.pre_post_geometry_valid_sample_count == len(
            eligible
        )
        oracle_terms = []
        for sample in eligible:
            positive = int(
                carrier.supervision.pair_positive_candidate_index[sample].item()
            )
            oracle_terms.append(
                _smooth_l1_oracle(
                    output.model_output.pre_post_geometry_predictions_angstrom[
                        positive, POST
                    ],
                    carrier.supervision.pre_post_geometry_target_angstrom[
                        sample, POST
                    ],
                )
            )
        torch.testing.assert_close(
            output.loss_output.loss_pre_post_geometry,
            torch.stack(oracle_terms).mean(),
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
        assert bridge_call["ligand"]["mask"] is ligand["mask"]
        assert bridge_call["pocket"]["mask"] is pocket["mask"]
        assert loss_call["ligand_batch_index"] is ligand["mask"]
        assert loss_call["pocket_batch_index"] is pocket["mask"]
        assert loss_call["post_geometry_loss_purpose"] == (
            "independent_hidden_post_distance_v1"
        )
        indicator = carrier.supervision.target_residue_reactive_atom_mask
        passed_indicator = bridge_call[
            "pocket_target_residue_atom_condition_indicator"
        ]
        assert passed_indicator.data_ptr() == indicator.data_ptr()
        torch.testing.assert_close(passed_indicator, indicator[:, 0])
        _assert_exact(carrier, before)
    assert tuple(observed_hidden_post_counts) == tuple(oracle_hidden_post_counts)
    assert tuple(oracle_hidden_post_counts) == (5, 4, 5, 4, 2)
    print(
        "HIDDEN_POST_VALID_COUNTS_BY_EPOCH="
        + "/".join(str(value) for value in observed_hidden_post_counts)
    )


def test_source_specific_post_b3_and_task_c_seed_semantics_are_preserved(
    carriers,
) -> None:
    for carrier in carriers:
        supervision = carrier.supervision
        assert supervision.pre_post_geometry_component_valid_mask[:5].tolist() == [
            [False, True]
        ] * 5
        assert supervision.pre_post_geometry_component_loss_mask[:5].tolist() == [
            [False, True]
        ] * 5
        assert supervision.pre_post_geometry_component_valid_mask[5:].tolist() == [
            [False, False]
        ] * 5
        assert supervision.pre_post_geometry_component_loss_mask[5:].tolist() == [
            [False, False]
        ] * 5
        assert torch.isfinite(
            supervision.pre_post_geometry_target_angstrom[:5, POST]
        ).all()
        assert torch.isnan(
            supervision.pre_post_geometry_target_angstrom[5:, POST]
        ).all()
        assert torch.isfinite(
            supervision.observed_complex_pair_distance_angstrom
        ).all()
        assert carrier.legacy_post_overlay_applied is False
        hidden_eligible = set(_hidden_post_oracle(carrier))
        for sample, task in enumerate(carrier.scheduled_task_ids):
            ligand_rows = carrier.model_input_batch["lig_mask"] == sample
            generation = supervision.ligand_base_generation_mask[
                ligand_rows, 0
            ]
            seed_count = int(
                supervision.ligand_minimal_seed_or_anchor_mask[
                    ligand_rows
                ].sum().item()
            )
            seed_valid = bool(
                supervision.ligand_minimal_seed_or_anchor_valid[sample].item()
            )
            if task == 3:
                assert bool(
                    supervision.pre_post_geometry_component_valid_mask[
                        sample, POST
                    ].item()
                ) == (sample < 5)
                assert bool(
                    supervision.pre_post_geometry_component_loss_mask[
                        sample, POST
                    ].item()
                ) == (sample < 5)
                assert bool(generation.any().item())
                assert bool((~generation).any().item())
                assert sample not in hidden_eligible
            if sample < 5:
                assert not seed_valid and seed_count == 0
            elif task == 4:
                assert seed_valid and seed_count > 0
            else:
                assert not seed_valid and seed_count == 0


@pytest.mark.parametrize(
    ("case", "error"),
    (
        ("disabled", "EXPLICIT_OPT_IN_REQUIRED"),
        ("evaluation", "LIFECYCLE_TRAINING_MODE_REQUIRED"),
        ("epoch", "LIFECYCLE_EPOCH_MISMATCH"),
        ("epoch_bool", "LIFECYCLE_EPOCH_MISMATCH"),
        ("seed", "LIFECYCLE_TASK_SCHEDULE_SEED_MISMATCH"),
        ("seed_bool", "LIFECYCLE_TASK_SCHEDULE_SEED_MISMATCH"),
        ("device", "LIFECYCLE_CPU_DEVICE_REQUIRED"),
    ),
)
def test_opt_in_lifecycle_epoch_seed_and_cpu_fail_before_transport(
    carriers,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    error: str,
) -> None:
    carrier = carriers[0]
    harness = _ForwardHarness(
        carrier,
        enabled=case != "disabled",
        training=False if case == "evaluation" else True,
        current_epoch=(
            carrier.epoch + 1
            if case == "epoch"
            else True
            if case == "epoch_bool"
            else None
        ),
        task_schedule_seed=(
            carrier.task_schedule_seed + 1
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


@pytest.mark.parametrize("input_kind", ("dict", "exact16", "batch001"))
def test_non_train10_carrier_types_reject_before_transport(
    carriers,
    real_batch001_train5,
    monkeypatch: pytest.MonkeyPatch,
    input_kind: str,
) -> None:
    harness = _ForwardHarness(carriers[0])
    invalid = (
        {}
        if input_kind == "dict"
        else SimpleNamespace(sample_identities=tuple(range(16)))
        if input_kind == "exact16"
        else real_batch001_train5
    )
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        with pytest.raises(ValueError, match="CARRIER_BOUNDARY_TYPE_INVALID"):
            _run_forward(harness, invalid)
    _assert_no_model_boundaries(harness)


@pytest.mark.parametrize(
    "changes",
    (
        {"sample_identities": ("FORGED",) + composer_owner.TRAIN10_SAMPLE_IDENTITIES_V1[1:]},
        {"formal_splits": ("validation",) + ("train",) * 9},
        {"source_branches": ("FORGED_SOURCE",) + ("BATCH001_FORMAL_TRAIN5_V1",) * 4 + ("CURRENT11_LEGACY_TRAIN5_V1",) * 5},
    ),
)
def test_identity_holdout_and_source_metadata_drift_rejected_by_real_validator(
    carriers,
    monkeypatch: pytest.MonkeyPatch,
    changes: dict[str, object],
) -> None:
    carrier = replace(copy.deepcopy(carriers[0]), **changes)
    harness = _ForwardHarness(carrier)
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        with pytest.raises(
            ValueError, match="PUBLISHED_COMPOSER_VALIDATOR_REJECTED"
        ) as captured:
            _run_forward(harness, carrier)
    assert str(captured.value.__cause__).startswith(
        composer_owner.TRAIN10_CPU_BATCH_COMPOSER_ERROR_V1
    )
    _assert_no_model_boundaries(harness)


def test_core_tensor_and_seal_drift_rejected_by_real_validator_before_transport(
    carriers, monkeypatch: pytest.MonkeyPatch
) -> None:
    carrier = copy.deepcopy(carriers[0])
    carrier.model_input_batch["lig_coords"][0, 0] += 100.0
    harness = _ForwardHarness(carrier)
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        with pytest.raises(
            ValueError, match="PUBLISHED_COMPOSER_VALIDATOR_REJECTED"
        ):
            _run_forward(harness, carrier)
    _assert_no_model_boundaries(harness)


@pytest.mark.parametrize("corruption", ("membership", "size", "node_count"))
def test_transport_membership_size_and_node_corruption_reject_before_bridge(
    carriers, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    carrier = carriers[0]
    harness = _ForwardHarness(carrier, transport_corruption=corruption)
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, harness)
        with pytest.raises(ValueError, match="TRANSPORT_BOUNDARY_"):
            _run_forward(harness, carrier)
    assert len(harness.transport_calls) == 1
    assert not harness.bridge_calls
    assert not harness.loss_calls
    assert not harness.covapie_current11_auxiliary_model_v1.encode_calls
    assert not harness.covapie_current11_auxiliary_model_v1.forward_calls


def test_output_pair_metadata_mismatch_reaches_production_loss_and_fails_closed(
    carriers, monkeypatch: pytest.MonkeyPatch
) -> None:
    carrier = carriers[0]
    harness = _ForwardHarness(carrier, corrupt_output_membership=True)
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


def test_b3_excluded_finite_predictions_do_not_change_geometry_loss(
    carriers, monkeypatch: pytest.MonkeyPatch
) -> None:
    carrier = next(
        value
        for value in carriers
        if bool((value.supervision.canonical_task_id == 3).any().item())
    )
    b3_samples = torch.nonzero(
        carrier.supervision.canonical_task_id == 3, as_tuple=False
    ).flatten().tolist()
    assert b3_samples
    baseline = _ForwardHarness(carrier)
    changed = _ForwardHarness(
        carrier,
        excluded_post_overrides={sample: 25.0 + sample for sample in b3_samples},
    )
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, baseline)
        first = _run_forward(baseline, carrier)
    with monkeypatch.context() as context:
        _install_synthetic_boundaries(context, changed)
        second = _run_forward(changed, carrier)
    for sample in b3_samples:
        assert sample not in _hidden_post_oracle(carrier)
        assert torch.isnan(
            first.loss_output.pre_post_geometry_per_sample_detached[sample]
        )
        assert torch.isnan(
            second.loss_output.pre_post_geometry_per_sample_detached[sample]
        )
    torch.testing.assert_close(
        first.loss_output.loss_pre_post_geometry,
        second.loss_output.loss_pre_post_geometry,
    )


@pytest.mark.parametrize(
    "weights",
    (
        CovapieCurrent11LossWeightsV1(),
        CovapieCurrent11LossWeightsV1(
            base_diffusion=1.0,
            covalent_pair_prediction=0.0,
            pre_post_geometry=0.0,
            covalent_pair_contrastive=0.0,
        ),
    ),
)
def test_existing_joint_and_diffusion_only_weights_route_raw_losses(
    carriers,
    monkeypatch: pytest.MonkeyPatch,
    weights: CovapieCurrent11LossWeightsV1,
) -> None:
    carrier = carriers[0]
    harness = _ForwardHarness(carrier, loss_weights=weights)
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
    assert bool(torch.isfinite(losses.loss_covalent_pair_prediction).item())
    assert bool(torch.isfinite(losses.loss_pre_post_geometry).item())
    assert bool(torch.isfinite(losses.loss_covalent_pair_contrastive).item())
    assert losses.pre_post_geometry_valid_sample_count == len(
        _hidden_post_oracle(carrier)
    )


def test_adapter_policy_cannot_be_overridden_by_forward_keyword(carriers) -> None:
    harness = _ForwardHarness(carriers[0])
    with pytest.raises(TypeError):
        harness.forward(
            carriers[0],
            post_geometry_loss_purpose="existing_component_masks_v1",
        )
    _assert_no_model_boundaries(harness)


def test_execution_fact_markers_are_explicit() -> None:
    print(
        "LOSS_TEST_INPUT_KIND="
        "REAL_TRAIN10_CARRIER_WITH_SYNTHETIC_PREDICTIONS"
    )
    print("PRODUCTION_LOSS_EXECUTED_WITH_SYNTHETIC_PREDICTIONS=true")
    print("REAL_DDPM_EGNN_FORWARD_EXECUTED=false")
