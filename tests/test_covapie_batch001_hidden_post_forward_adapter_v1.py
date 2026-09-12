from __future__ import annotations

from dataclasses import fields, replace
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import pytorch_lightning as pl
import torch

from covalent_ext import (
    covapie_batch001_feature_post_use_preflight_v1 as preflight_owner,
)
from covalent_ext import (
    covapie_batch001_hidden_post_forward_adapter_v1 as subject,
)
from covalent_ext import (
    covapie_current11_auxiliary_model_and_loss_v1 as loss_owner,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    AUXILIARY_ERROR,
    CovapieCurrent11LossWeightsV1,
    CovapieCurrent11ModelOutputV1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11DiffusionForwardTraceV1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)
from lightning_modules import LigandPocketDDPM
from equivariant_diffusion.conditional_model import ConditionalDDPM


ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT.parent / "covapie-state/bulk-multisource-cys-sg-v1/rcsb"
POST = 1


def _forbidden(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("forbidden training/model operation was invoked")


@pytest.fixture(autouse=True)
def no_training_operations(monkeypatch: pytest.MonkeyPatch) -> None:
    """This suite executes the production loss, never DDPM/training APIs."""

    monkeypatch.setattr(torch, "load", _forbidden)
    monkeypatch.setattr(torch.Tensor, "backward", _forbidden)
    monkeypatch.setattr(torch.autograd, "backward", _forbidden)
    monkeypatch.setattr(torch.autograd, "grad", _forbidden)
    monkeypatch.setattr(torch.optim.Optimizer, "__init__", _forbidden)
    monkeypatch.setattr(torch.optim.Optimizer, "step", _forbidden)
    monkeypatch.setattr(ConditionalDDPM, "forward", _forbidden)
    monkeypatch.setattr(LigandPocketDDPM, "configure_optimizers", _forbidden)
    monkeypatch.setattr(LigandPocketDDPM, "training_step", _forbidden)
    monkeypatch.setattr(LigandPocketDDPM, "load_from_checkpoint", _forbidden)
    monkeypatch.setattr(pl.Trainer, "fit", _forbidden)


@pytest.fixture(scope="module")
def carriers():
    _authority, values = preflight_owner._build_carriers_v1(
        repository_root=ROOT, cache_root=CACHE_ROOT
    )
    return values


def _carrier(carriers, split: str, epoch: int):
    return next(
        value
        for value in carriers
        if value.formal_split == split and value.epoch == epoch
    )


def _clone_carrier(carrier):
    model_input = {
        name: value.clone()
        if isinstance(value, torch.Tensor)
        else list(value)
        if type(value) is list
        else value
        for name, value in carrier.model_input_batch.items()
    }
    supervision = CovapieCurrent11TrainingSupervisionTensorsV1(**{
        field.name: getattr(carrier.supervision, field.name).clone()
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    })
    return replace(
        carrier, model_input_batch=model_input, supervision=supervision
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
    ligand_xh = torch.cat((
        carrier.model_input_batch["lig_coords"].clone(),
        torch.zeros((ligand_count, 10)),
    ), dim=1)
    pocket_xh = torch.cat((
        carrier.model_input_batch["pocket_coords"].clone(),
        torch.zeros((pocket_count, 10)),
    ), dim=1)
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
    geometry = torch.stack((
        torch.linspace(0.65, 2.65, candidate_count),
        torch.linspace(1.05, 3.95, candidate_count),
    ), dim=1)
    for sample in range(len(carrier.sample_identities)):
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        target = supervision.pre_post_geometry_target_angstrom[sample, POST]
        geometry[positive, POST] = target + 0.2 + 0.11 * sample
    for sample, value in (excluded_post_overrides or {}).items():
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        geometry[positive, POST] = value
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
        target_pair_consistency=torch.ones(5, dtype=torch.bool),
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
    """CPU self for the adapter's real forward orchestration method."""

    forward = subject.CovapieBatch001HiddenPostForwardLigandPocketDDPMV1.forward

    def __init__(
        self,
        carrier,
        *,
        training: bool = True,
        current_epoch: int | None = None,
        task_schedule_seed: int | None = None,
        excluded_post_overrides: dict[int, float] | None = None,
        corrupt_output_membership: bool = False,
        corrupt_transport_membership: bool = False,
    ) -> None:
        self.training = training
        self.current_epoch = carrier.epoch if current_epoch is None else current_epoch
        self.covapie_current11_task_schedule_seed = (
            carrier.task_schedule_seed
            if task_schedule_seed is None
            else task_schedule_seed
        )
        self.covapie_batch001_hidden_post_forward_enabled = True
        self.covapie_current11_pair_contrastive_temperature = 1.0
        # Test-only nonzero geometry weight; this is not a training-weight choice.
        self.covapie_current11_loss_weights = CovapieCurrent11LossWeightsV1(
            base_diffusion=0.0,
            covalent_pair_prediction=0.0,
            pre_post_geometry=1.0,
            covalent_pair_contrastive=0.0,
        )
        self.virtual_nodes = False
        self.device = torch.device("cpu")
        self.ddpm = object()
        self.trace = _synthetic_trace(carrier)
        self.covapie_current11_auxiliary_model_v1 = _SyntheticAuxiliaryBoundary(
            carrier,
            self.trace,
            excluded_post_overrides=excluded_post_overrides,
            corrupt_output_membership=corrupt_output_membership,
        )
        self.corrupt_transport_membership = corrupt_transport_membership
        self.transport_calls: list[tuple[dict[str, object], dict[str, object]]] = []
        self.bridge_calls: list[dict[str, object]] = []
        self.loss_calls: list[dict[str, object]] = []

    def get_ligand_and_pocket(self, data: object):
        ligand, pocket = LigandPocketDDPM.get_ligand_and_pocket(self, data)
        if self.corrupt_transport_membership:
            ligand = dict(ligand)
            ligand["mask"] = ligand["mask"].clone()
            ligand["mask"][0] = 1
        self.transport_calls.append((ligand, pocket))
        return ligand, pocket


def _install_boundaries(
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


def _smooth_l1_oracle(prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    error = torch.abs(prediction - target)
    return torch.where(error < 1.0, 0.5 * error.square(), error - 0.5)


def test_fixed_source_bindings_and_drift_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = (
        subject.verify_covapie_batch001_hidden_post_forward_adapter_sources_v1(
            repository_root=ROOT
        )
    )
    assert observed == subject.DIRECT_BOUND_SOURCE_SHA256_V1
    drifted = list(subject.DIRECT_BOUND_SOURCE_SHA256_V1)
    drifted[0] = (drifted[0][0], "0" * 64)
    monkeypatch.setattr(subject, "DIRECT_BOUND_SOURCE_SHA256_V1", tuple(drifted))
    with pytest.raises(ValueError, match="DIRECT_BOUND_SOURCE_SHA256_MISMATCH"):
        subject.verify_covapie_batch001_hidden_post_forward_adapter_sources_v1(
            repository_root=ROOT
        )


def test_fresh_process_import_only_uses_published_biopython_compat() -> None:
    code = r'''
import importlib.metadata
import json
import sys
from Bio.PDB import Polypeptide
before = hasattr(Polypeptide, "three_to_one")
from covalent_ext import covapie_batch001_hidden_post_forward_adapter_v1 as subject
print(json.dumps({
    "executable": sys.executable,
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
    assert record["executable"] == sys.executable
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


def test_real_train5_five_epoch_cycle_routes_hidden_post_and_matches_oracle(
    carriers, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed_counts = []
    for epoch in range(5):
        carrier = _carrier(carriers, "train", epoch)
        before = preflight_owner._carrier_fingerprint(carrier)
        harness = _ForwardHarness(carrier)
        with monkeypatch.context() as context:
            _install_boundaries(context, harness)
            output = _run_forward(harness, carrier)
        _fingerprint, rows = (
            preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(
                carrier
            )
        )
        eligible = [
            index
            for index, row in enumerate(rows)
            if row.preflight_effective_hidden_post_eligible
        ]
        observed_counts.append(
            output.loss_output.pre_post_geometry_valid_sample_count
        )
        assert output.loss_output.pre_post_geometry_valid_sample_count == len(eligible)
        oracle_terms = []
        for sample in eligible:
            positive = int(
                carrier.supervision.pair_positive_candidate_index[sample].item()
            )
            oracle_terms.append(_smooth_l1_oracle(
                output.model_output.pre_post_geometry_predictions_angstrom[
                    positive, POST
                ],
                carrier.supervision.pre_post_geometry_target_angstrom[sample, POST],
            ))
        oracle = torch.stack(oracle_terms).mean()
        torch.testing.assert_close(
            output.loss_output.loss_pre_post_geometry, oracle
        )
        assert torch.isfinite(output.loss_output.loss_pre_post_geometry)
        assert float(output.loss_output.loss_pre_post_geometry) > 0.0
        assert len(harness.transport_calls) == 1
        assert len(harness.bridge_calls) == 1
        assert len(harness.loss_calls) == 1
        ligand, pocket = harness.transport_calls[0]
        loss_call = harness.loss_calls[0]
        assert loss_call["post_geometry_loss_purpose"] == (
            "independent_hidden_post_distance_v1"
        )
        assert loss_call["ligand_batch_index"] is ligand["mask"]
        assert loss_call["pocket_batch_index"] is pocket["mask"]
        assert output.supervision is carrier.supervision
        assert output.diffusion_trace is harness.trace
        assert preflight_owner._carrier_fingerprint(carrier) == before
    assert tuple(observed_counts) == (5, 4, 5, 4, 2)


def test_b3_excluded_predictions_do_not_change_hidden_post_loss(
    carriers, monkeypatch: pytest.MonkeyPatch
) -> None:
    carrier = next(
        value
        for value in carriers
        if value.formal_split == "train"
        and bool((value.supervision.canonical_task_id == 3).any().item())
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
        _install_boundaries(context, baseline)
        first = _run_forward(baseline, carrier)
    with monkeypatch.context() as context:
        _install_boundaries(context, changed)
        second = _run_forward(changed, carrier)
    supervision = carrier.supervision
    for sample in b3_samples:
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        assert bool(supervision.pre_post_geometry_component_valid_mask[sample, POST])
        assert bool(supervision.pre_post_geometry_component_loss_mask[sample, POST])
        assert bool(supervision.ligand_base_fixed_mask[
            supervision.pair_candidate_ligand_flat_index[positive], 0
        ])
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
    assert first.loss_output.pre_post_geometry_valid_sample_count == (
        second.loss_output.pre_post_geometry_valid_sample_count
    )
    assert first.loss_output.covalent_pair_prediction_valid_sample_count == 5
    assert first.loss_output.covalent_pair_contrastive_valid_sample_count == 5


def test_generated_false_post_request_is_not_reopened(
    carriers, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _carrier(carriers, "train", 0)
    candidate = _clone_carrier(original)
    _fingerprint, rows = (
        preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(candidate)
    )
    sample = next(
        index
        for index, row in enumerate(rows)
        if row.preflight_effective_hidden_post_eligible
    )
    candidate.supervision.pre_post_geometry_component_loss_mask[sample, POST] = False
    _fingerprint, changed_rows = (
        preflight_owner.audit_covapie_batch001_feature_post_use_carrier_v1(candidate)
    )
    assert not changed_rows[sample].original_post_request
    assert not changed_rows[sample].preflight_effective_hidden_post_eligible
    harness = _ForwardHarness(candidate)
    with monkeypatch.context() as context:
        _install_boundaries(context, harness)
        output = _run_forward(harness, candidate)
    assert output.loss_output.pre_post_geometry_valid_sample_count == 4
    assert torch.isnan(
        output.loss_output.pre_post_geometry_per_sample_detached[sample]
    )


@pytest.mark.parametrize(
    ("case", "error"),
    (
        ("validation", "LIFECYCLE_FORMAL_TRAIN_ONLY"),
        ("test_label", "LIFECYCLE_FORMAL_TRAIN_ONLY"),
        ("evaluation", "LIFECYCLE_TRAINING_MODE_REQUIRED"),
        ("epoch", "LIFECYCLE_EPOCH_MISMATCH"),
        ("seed", "LIFECYCLE_TASK_SCHEDULE_SEED_MISMATCH"),
        ("identity", "CARRIER_BOUNDARY_EXACT_TRAIN5_IDENTITY_REJECTED"),
    ),
)
def test_lifecycle_and_identity_fail_before_model_boundaries(
    carriers, monkeypatch: pytest.MonkeyPatch, case: str, error: str
) -> None:
    carrier = _carrier(
        carriers, "validation" if case == "validation" else "train", 0
    )
    if case == "test_label":
        # Deliberately relabel train5; no test4 input is built or executed.
        carrier = replace(_clone_carrier(carrier), formal_split="test")
    if case == "identity":
        carrier = replace(
            _clone_carrier(carrier),
            sample_identities=("wrong-event",) + carrier.sample_identities[1:],
        )
    harness = _ForwardHarness(
        carrier,
        training=case != "evaluation",
        current_epoch=carrier.epoch + (1 if case == "epoch" else 0),
        task_schedule_seed=(
            carrier.task_schedule_seed + (1 if case == "seed" else 0)
        ),
    )
    with monkeypatch.context() as context:
        _install_boundaries(context, harness)
        with pytest.raises(ValueError, match=error):
            _run_forward(harness, carrier)
    assert not harness.transport_calls
    assert not harness.bridge_calls
    assert not harness.loss_calls
    assert not harness.covapie_current11_auxiliary_model_v1.encode_calls
    assert not harness.covapie_current11_auxiliary_model_v1.forward_calls


@pytest.mark.parametrize("case", ("cross_sample_flat_local", "wrong_cys_sg"))
def test_carrier_metadata_corruption_is_rejected_by_published_preflight(
    carriers, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    carrier = _clone_carrier(_carrier(carriers, "train", 0))
    if case == "cross_sample_flat_local":
        positive = int(carrier.supervision.pair_positive_candidate_index[0])
        sample_one_ligand = int(torch.nonzero(
            carrier.model_input_batch["lig_mask"] == 1, as_tuple=False
        )[0])
        carrier.supervision.pair_candidate_ligand_flat_index[
            positive
        ] = sample_one_ligand
    else:
        carrier.supervision.target_residue_reactive_atom_flat_index[0] += 1
    harness = _ForwardHarness(carrier)
    with monkeypatch.context() as context:
        _install_boundaries(context, harness)
        with pytest.raises(
            ValueError, match="CARRIER_BOUNDARY_PUBLISHED_PREFLIGHT_REJECTED"
        ) as captured:
            _run_forward(harness, carrier)
    assert "COVAPIE_BATCH001_FEATURE_POST_USE_PREFLIGHT_V1_ERROR" in str(
        captured.value.__cause__
    )
    assert not harness.transport_calls
    assert not harness.bridge_calls
    assert not harness.loss_calls


def test_transport_membership_mismatch_is_rejected_before_bridge_and_loss(
    carriers, monkeypatch: pytest.MonkeyPatch
) -> None:
    carrier = _carrier(carriers, "train", 0)
    harness = _ForwardHarness(carrier, corrupt_transport_membership=True)
    with monkeypatch.context() as context:
        _install_boundaries(context, harness)
        with pytest.raises(ValueError, match="TRANSPORT_BOUNDARY_MEMBERSHIP_MISMATCH"):
            _run_forward(harness, carrier)
    assert len(harness.transport_calls) == 1
    assert not harness.bridge_calls
    assert not harness.loss_calls


def test_output_membership_mismatch_reaches_and_is_rejected_by_production_loss(
    carriers, monkeypatch: pytest.MonkeyPatch
) -> None:
    carrier = _carrier(carriers, "train", 0)
    harness = _ForwardHarness(carrier, corrupt_output_membership=True)
    with monkeypatch.context() as context:
        _install_boundaries(context, harness)
        with pytest.raises(
            ValueError, match="PRODUCTION_LOSS_GATE_REJECTED"
        ) as captured:
            _run_forward(harness, carrier)
    assert len(harness.transport_calls) == 1
    assert len(harness.bridge_calls) == 1
    assert len(harness.loss_calls) == 1
    assert type(captured.value.__cause__) is ValueError
    assert str(captured.value.__cause__) == AUXILIARY_ERROR


def test_batch_purpose_field_and_call_keyword_cannot_override_adapter_policy(
    carriers, monkeypatch: pytest.MonkeyPatch
) -> None:
    carrier = _clone_carrier(_carrier(carriers, "train", 0))
    carrier.model_input_batch["post_geometry_loss_purpose"] = (
        "existing_component_masks_v1"
    )
    harness = _ForwardHarness(carrier)
    with monkeypatch.context() as context:
        _install_boundaries(context, harness)
        with pytest.raises(
            ValueError, match="CARRIER_BOUNDARY_PUBLISHED_PREFLIGHT_REJECTED"
        ):
            _run_forward(harness, carrier)
    assert not harness.transport_calls
    assert not harness.loss_calls

    clean = _carrier(carriers, "train", 0)
    clean_harness = _ForwardHarness(clean)
    with pytest.raises(TypeError):
        clean_harness.forward(
            clean, post_geometry_loss_purpose="existing_component_masks_v1"
        )
    assert not clean_harness.transport_calls
