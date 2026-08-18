from __future__ import annotations

import hashlib
import os
import platform
import subprocess
from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytorch_lightning
import torch
from Bio.PDB import Polypeptide as _polypeptide


if not hasattr(_polypeptide, "three_to_one"):
    _polypeptide.three_to_one = lambda name: (
        _polypeptide.protein_letters_3to1[name]
    )

import lightning_modules
from covalent_ext import (
    covapie_current11_auxiliary_model_and_loss_v1 as auxiliary_owner,
)
from covalent_ext import (
    covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
    as current11_smoke,
)
from covalent_ext import (
    covapie_current11_training_lightning_module_v1 as current11_owner,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1
    as scheduler,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_lightning_training_bridge_v1
    as subject,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed_tensorizer,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    CovapieCurrent11TrainingForwardOutputV1,
    CovapieCurrent11TrainingLigandPocketDDPM,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
ERROR = (
    subject.COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_LIGHTNING_TRAINING_BRIDGE_V1_ERROR
)
CHECKPOINT_SHA256 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
EXPECTED_TASKS = (3, 2, 3, 0, 2, 4, 0, 0, 4, 4, 1, 3, 0, 0, 0, 0)


class _Params(SimpleNamespace):
    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


def _constructor_kwargs() -> dict[str, object]:
    return {
        "outdir": Path("/tmp/covapie-mixed-lightning-test-output"),
        "dataset": "crossdock",
        "datadir": "/tmp/covapie-mixed-lightning-test-data",
        "batch_size": 16,
        "lr": 1e-3,
        "egnn_params": _Params(
            joint_nf=4,
            device="cpu",
            hidden_nf=8,
            n_layers=1,
            attention=False,
            tanh=False,
            norm_constant=1,
            inv_sublayers=1,
            sin_embedding=False,
            normalization_factor=1,
            aggregation_method="sum",
            edge_cutoff_ligand=None,
            edge_cutoff_pocket=None,
            edge_cutoff_interaction=None,
            reflection_equivariant=True,
            edge_embedding_dim=None,
        ),
        "diffusion_params": _Params(
            diffusion_loss_type="l2",
            diffusion_steps=4,
            diffusion_noise_schedule="polynomial_2",
            diffusion_noise_precision=1e-4,
            normalize_factors=[1.0, 1.0],
        ),
        "num_workers": 0,
        "augment_noise": 0,
        "augment_rotation": False,
        "clip_grad": False,
        "eval_epochs": 1,
        "eval_params": _Params(eval_batch_size=16, smiles_file=None),
        "visualize_sample_epoch": 1,
        "visualize_chain_epoch": 1,
        "auxiliary_loss": False,
        "loss_params": _Params(),
        "mode": "pocket_conditioning",
        "node_histogram": [[1] * 8 for _ in range(8)],
        "pocket_representation": "full-atom",
        "virtual_nodes": False,
        "target_residue_atom_conditioning": True,
    }


def _patch_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        lightning_modules, "BasicMolecularMetrics", lambda *args: object()
    )
    monkeypatch.setattr(
        lightning_modules, "MoleculeProperties", lambda: object()
    )
    monkeypatch.setattr(
        lightning_modules, "CategoricalDistribution", lambda *args: object()
    )


def _small_model(
    monkeypatch: pytest.MonkeyPatch,
    *,
    mixed: bool = True,
) -> CovapieCurrent11TrainingLigandPocketDDPM:
    _patch_metrics(monkeypatch)
    owner = (
        subject.CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1
        if mixed
        else CovapieCurrent11TrainingLigandPocketDDPM
    )
    return owner(
        **_constructor_kwargs(),
        covapie_current11_task2_runtime_enabled=True,
        covapie_repository_root=str(ROOT),
        covapie_state_root=str(STATE),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_tensor_exact_with_nan(
    actual: torch.Tensor, expected: torch.Tensor
) -> None:
    if actual.dtype.is_floating_point or actual.dtype.is_complex:
        torch.testing.assert_close(
            actual,
            expected,
            rtol=0,
            atol=0,
            equal_nan=True,
        )
    else:
        assert torch.equal(actual, expected)


@pytest.fixture(scope="module")
def exact16_mixed_batch(tmp_path_factory: pytest.TempPathFactory):
    temporary = tmp_path_factory.mktemp("covapie_mixed_lightning_exact16")
    normalized_repository = temporary / "normalized_repository"
    scheduler._clone_head_v1(ROOT, normalized_repository)
    real = current11_smoke._build_real_current11_batch_v1(
        repo_root=normalized_repository,
        state_root=STATE,
    )
    samples = []
    for identity in scheduler.EXACT16_MEMBER_IDENTITIES_V1:
        task_id = (
            scheduler.canonical_task_id_for_covapie_expanded_cys_sg_sample_v1(
                sample_identity=identity,
                epoch=0,
                task_schedule_seed=0,
            )
        )
        if identity in mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1:
            sample = mixed_tensorizer.tensorize_covapie_expanded_cys_sg_sample_v1(
                sample_identity=identity,
                task_id=task_id,
                device="cpu",
                epoch=0,
                task_schedule_seed=0,
                current11_batch=real["model_batch"],
                current11_runtime_result=real["runtime"],
                current11_authoritative_supervision=(
                    real["authoritative_supervision"]
                ),
            )
        else:
            sample = mixed_tensorizer.tensorize_covapie_expanded_cys_sg_sample_v1(
                sample_identity=identity,
                task_id=task_id,
                device="cpu",
                repository_root=ROOT,
                state_root=STATE,
            )
        samples.append(sample)
    return scheduler.collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1(
        samples,
        epoch=0,
        task_schedule_seed=0,
    )


def _real_mixed_model():
    with patch.object(
        current11_smoke,
        "CovapieCurrent11TrainingLigandPocketDDPM",
        subject.CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1,
    ):
        model = current11_smoke._instantiate_current11_model_v1(
            repo_root=ROOT,
            state_root=STATE,
            device="cpu",
        )
    assert type(model) is (
        subject.CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1
    )
    return model


def _assert_bridge_error(callable_object) -> None:
    with pytest.raises(ValueError) as error:
        callable_object()
    assert str(error.value) == ERROR


def _manual_lower_level_forward(model, mixed_batch, *, seed: int):
    ligand, pocket = model.get_ligand_and_pocket(
        mixed_batch.model_input_batch
    )
    supervision = mixed_batch.supervision
    role_delta = (
        model.covapie_current11_auxiliary_model_v1
        .encode_role_mask_anchor_v1(
            supervision=supervision,
            ligand_batch_index=ligand["mask"],
        )
    )
    torch.manual_seed(seed)
    trace = (
        current11_owner
        .run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
            ddpm=model.ddpm,
            ligand=ligand,
            pocket=pocket,
            supervision=supervision,
            role_mask_anchor_hidden_delta=role_delta,
            pocket_target_residue_atom_condition_indicator=(
                supervision.target_residue_reactive_atom_mask[:, 0]
            ),
        )
    )
    model_output = model.covapie_current11_auxiliary_model_v1(
        diffusion_trace=trace,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
    )
    loss_output = auxiliary_owner.compute_covapie_current11_training_losses_v1(
        model_output=model_output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=model.covapie_current11_loss_weights,
        pair_contrastive_temperature=(
            model.covapie_current11_pair_contrastive_temperature
        ),
        geometry_smooth_l1_beta=1.0,
    )
    return CovapieCurrent11TrainingForwardOutputV1(
        model_output=model_output,
        loss_output=loss_output,
        supervision=supervision,
        diffusion_trace=trace,
    )


def _nonzero_finite_gradient(parameter: torch.nn.Parameter) -> bool:
    gradient = parameter.grad
    return bool(
        gradient is not None
        and torch.isfinite(gradient).all().item()
        and torch.count_nonzero(gradient).item() > 0
    )


def test_additive_architecture_state_parameter_buffer_and_optimizer_parity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    torch.manual_seed(101)
    parent = _small_model(monkeypatch, mixed=False)
    torch.manual_seed(101)
    mixed = _small_model(monkeypatch, mixed=True)
    parent_state = parent.state_dict()
    mixed_state = mixed.state_dict()
    assert tuple(parent_state) == tuple(mixed_state)
    assert len(mixed_state) > 0
    for name in parent_state:
        assert parent_state[name].shape == mixed_state[name].shape
        assert torch.equal(parent_state[name], mixed_state[name])
    assert tuple(dict(parent.named_parameters())) == tuple(
        dict(mixed.named_parameters())
    )
    assert tuple(dict(parent.named_buffers())) == tuple(
        dict(mixed.named_buffers())
    )
    owner = subject.CovapieExpandedCysSgMixedProfileTrainingLigandPocketDDPMV1
    assert owner.__bases__ == (CovapieCurrent11TrainingLigandPocketDDPM,)
    assert set(owner.__dict__) & {
        "forward",
        "transfer_batch_to_device",
        "_shared_covapie_training_step_v1",
        "training_step",
        "validation_step",
        "test_step",
        "configure_optimizers",
    } == {"forward", "transfer_batch_to_device"}
    assert (
        owner.configure_optimizers
        is CovapieCurrent11TrainingLigandPocketDDPM.configure_optimizers
    )
    assert (
        owner._shared_covapie_training_step_v1
        is CovapieCurrent11TrainingLigandPocketDDPM._shared_covapie_training_step_v1
    )
    assert owner.training_step is CovapieCurrent11TrainingLigandPocketDDPM.training_step
    assert owner.validation_step is CovapieCurrent11TrainingLigandPocketDDPM.validation_step
    assert owner.test_step is CovapieCurrent11TrainingLigandPocketDDPM.test_step

    model_parameters = list(mixed.parameters())
    optimizer = mixed.configure_optimizers()
    optimizer_parameters = [
        parameter
        for group in optimizer.param_groups
        for parameter in group["params"]
    ]
    model_ids = [id(parameter) for parameter in model_parameters]
    optimizer_ids = [id(parameter) for parameter in optimizer_parameters]
    assert isinstance(optimizer, torch.optim.AdamW)
    assert len(model_ids) == len(set(model_ids))
    assert len(optimizer_ids) == len(set(optimizer_ids))
    assert set(optimizer_ids) == set(model_ids)


def test_custom_transfer_preserves_frozen_types_metadata_dtypes_and_values(
    monkeypatch: pytest.MonkeyPatch,
    exact16_mixed_batch,
) -> None:
    model = _small_model(monkeypatch)
    batch = exact16_mixed_batch
    model_tensor_before = {
        key: value.detach().clone()
        for key, value in batch.model_input_batch.items()
        if isinstance(value, torch.Tensor)
    }
    supervision_before = {
        field.name: getattr(batch.supervision, field.name).detach().clone()
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    }
    transferred = model.transfer_batch_to_device(
        batch, torch.device("cpu"), 0
    )
    assert type(transferred) is scheduler.CovapieExpandedCysSgMixedBatchV1
    assert type(transferred.supervision) is (
        CovapieCurrent11TrainingSupervisionTensorsV1
    )
    assert transferred is not batch
    assert transferred.supervision is not batch.supervision
    assert transferred.model_input_batch is not batch.model_input_batch
    for name in (
        "sample_identities",
        "role_profiles",
        "scheduled_task_ids",
        "current11_batch_indices",
        "k36_batch_indices",
    ):
        assert getattr(transferred, name) is getattr(batch, name)
    assert transferred.epoch == batch.epoch
    assert transferred.task_schedule_seed == batch.task_schedule_seed
    for key, expected in model_tensor_before.items():
        actual = transferred.model_input_batch[key]
        assert actual.device.type == "cpu"
        assert actual.dtype == expected.dtype
        assert torch.equal(actual, expected)
        assert torch.equal(batch.model_input_batch[key], expected)
    for name, expected in supervision_before.items():
        actual = getattr(transferred.supervision, name)
        assert actual.device.type == "cpu"
        assert actual.dtype == expected.dtype
        _assert_tensor_exact_with_nan(actual, expected)
        _assert_tensor_exact_with_nan(
            getattr(batch.supervision, name), expected
        )
    assert transferred.model_input_batch["names"] == list(
        batch.sample_identities
    )
    assert transferred.model_input_batch["receptors"] == (
        batch.model_input_batch["receptors"]
    )


@pytest.mark.parametrize("bad_input", ({}, object()))
def test_forward_rejects_non_mixed_input_exact_type(
    monkeypatch: pytest.MonkeyPatch,
    bad_input: object,
) -> None:
    model = _small_model(monkeypatch)
    _assert_bridge_error(lambda: model.forward(bad_input))


@pytest.mark.parametrize("field,value", (("epoch", 1), ("task_schedule_seed", 9)))
def test_epoch_and_seed_mismatch_fail_before_validation_or_model_execution(
    monkeypatch: pytest.MonkeyPatch,
    exact16_mixed_batch,
    field: str,
    value: int,
) -> None:
    model = _small_model(monkeypatch)
    corrupted = replace(exact16_mixed_batch, **{field: value})
    validation_calls = 0
    transport_calls = 0

    def forbidden_validation(*unused):
        nonlocal validation_calls
        del unused
        validation_calls += 1
        raise AssertionError("schedule mismatch entered validation")

    def forbidden_transport(*unused):
        nonlocal transport_calls
        del unused
        transport_calls += 1
        raise AssertionError("schedule mismatch entered model transport")

    monkeypatch.setattr(
        subject,
        "validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1",
        forbidden_validation,
    )
    monkeypatch.setattr(model, "get_ligand_and_pocket", forbidden_transport)
    _assert_bridge_error(lambda: model.forward(corrupted))
    assert validation_calls == 0
    assert transport_calls == 0


def test_eval_mode_fails_before_mixed_validation_or_transport(
    monkeypatch: pytest.MonkeyPatch,
    exact16_mixed_batch,
) -> None:
    model = _small_model(monkeypatch)
    calls = {"validation": 0, "transport": 0}

    def forbidden_validation(*unused):
        del unused
        calls["validation"] += 1
        raise AssertionError("eval entered mixed validation")

    def forbidden_transport(*unused):
        del unused
        calls["transport"] += 1
        raise AssertionError("eval entered transport")

    monkeypatch.setattr(
        subject,
        "validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1",
        forbidden_validation,
    )
    monkeypatch.setattr(model, "get_ligand_and_pocket", forbidden_transport)
    model.eval()
    _assert_bridge_error(lambda: model.forward(exact16_mixed_batch))
    assert calls == {"validation": 0, "transport": 0}
    assert model.training is False
    assert model.ddpm.training is False


@pytest.mark.parametrize("step_name", ("validation_step", "test_step"))
def test_inherited_evaluation_steps_remain_fail_closed_before_forward(
    monkeypatch: pytest.MonkeyPatch,
    exact16_mixed_batch,
    step_name: str,
) -> None:
    model = _small_model(monkeypatch)
    forward_calls = 0

    def forbidden_forward(*unused):
        nonlocal forward_calls
        del unused
        forward_calls += 1
        raise AssertionError("unsupported evaluation step entered forward")

    monkeypatch.setattr(model, "forward", forbidden_forward)
    with pytest.raises(ValueError) as error:
        getattr(model, step_name)(exact16_mixed_batch, 0)
    assert str(error.value) == current11_owner.TRAINING_MODULE_ERROR
    assert forward_calls == 0


def _corrupt_mixed_batch(batch, mutation: str):
    supervision = batch.supervision
    if mutation == "sample_identities":
        return replace(
            batch,
            sample_identities=("CORRUPTED",) + batch.sample_identities[1:],
        )
    if mutation == "role_profile":
        return replace(
            batch,
            role_profiles=("CORRUPTED",) + batch.role_profiles[1:],
        )
    if mutation == "scheduled_task":
        tasks = list(batch.scheduled_task_ids)
        tasks[0] = (tasks[0] + 1) % 5
        return replace(batch, scheduled_task_ids=tuple(tasks))
    if mutation in ("k36_task_1", "k36_task_2"):
        invalid = 1 if mutation.endswith("1") else 2
        tasks = list(batch.scheduled_task_ids)
        tasks[11] = invalid
        canonical = supervision.canonical_task_id.clone()
        canonical[11] = invalid
        return replace(
            batch,
            scheduled_task_ids=tuple(tasks),
            supervision=replace(supervision, canonical_task_id=canonical),
        )
    if mutation == "cross_sample_pair":
        ligand_flat = supervision.pair_candidate_ligand_flat_index.clone()
        ligand_flat[0] = int(batch.model_input_batch["num_lig_atoms"][0])
        return replace(
            batch,
            supervision=replace(
                supervision,
                pair_candidate_ligand_flat_index=ligand_flat,
            ),
        )
    raise AssertionError(mutation)


@pytest.mark.parametrize(
    "mutation",
    (
        "sample_identities",
        "role_profile",
        "scheduled_task",
        "k36_task_1",
        "k36_task_2",
        "cross_sample_pair",
    ),
)
def test_published_mixed_validator_corruptions_fail_before_transport(
    monkeypatch: pytest.MonkeyPatch,
    exact16_mixed_batch,
    mutation: str,
) -> None:
    model = _small_model(monkeypatch)
    corrupted = _corrupt_mixed_batch(exact16_mixed_batch, mutation)
    transport_calls = 0

    def forbidden_transport(*unused):
        nonlocal transport_calls
        del unused
        transport_calls += 1
        raise AssertionError("invalid mixed batch entered transport")

    monkeypatch.setattr(model, "get_ligand_and_pocket", forbidden_transport)
    _assert_bridge_error(lambda: model.forward(corrupted))
    assert transport_calls == 0


@pytest.mark.parametrize("malformation", ("dtype", "rank", "length"))
def test_malformed_canonical_reactive_indicator_fails_before_model_execution(
    monkeypatch: pytest.MonkeyPatch,
    exact16_mixed_batch,
    malformation: str,
) -> None:
    model = _small_model(monkeypatch)
    indicator = (
        exact16_mixed_batch.supervision
        .target_residue_reactive_atom_mask
    )
    if malformation == "dtype":
        malformed = indicator.long()
    elif malformation == "rank":
        malformed = indicator[:, 0]
    else:
        malformed = indicator[:-1]
    corrupted = replace(
        exact16_mixed_batch,
        supervision=replace(
            exact16_mixed_batch.supervision,
            target_residue_reactive_atom_mask=malformed,
        ),
    )
    encoder_calls = 0

    def forbidden_encoder(**unused):
        nonlocal encoder_calls
        del unused
        encoder_calls += 1
        raise AssertionError("malformed indicator entered role encoder")

    monkeypatch.setattr(
        model.covapie_current11_auxiliary_model_v1,
        "encode_role_mask_anchor_v1",
        forbidden_encoder,
    )
    _assert_bridge_error(lambda: model.forward(corrupted))
    assert encoder_calls == 0


@pytest.mark.parametrize("exception_type", (KeyboardInterrupt, SystemExit))
def test_process_control_exceptions_from_published_validator_propagate(
    monkeypatch: pytest.MonkeyPatch,
    exact16_mixed_batch,
    exception_type: type[BaseException],
) -> None:
    model = _small_model(monkeypatch)

    def interrupt(*unused):
        del unused
        raise exception_type()

    monkeypatch.setattr(
        subject,
        "validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1",
        interrupt,
    )
    with pytest.raises(exception_type):
        model.forward(exact16_mixed_batch)


def test_real_exact16_checkpoint_forward_parity_training_step_backward_and_optimizer(
    monkeypatch: pytest.MonkeyPatch,
    exact16_mixed_batch,
) -> None:
    assert platform.python_version()
    assert torch.__version__
    assert pytorch_lightning.__version__
    assert _sha256(CHECKPOINT) == CHECKPOINT_SHA256
    checkpoint_before = CHECKPOINT.read_bytes()
    checkpoint = current11_smoke.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=CHECKPOINT
    )
    assert checkpoint["checkpoint_sha256"] == CHECKPOINT_SHA256
    assert checkpoint["checkpoint_state_dict_key_count"] == 122
    checkpoint_state = checkpoint["state_dict"]

    torch.manual_seed(20260818)
    model = _real_mixed_model()
    migration = (
        current11_smoke
        .migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
            model=model,
            checkpoint_state_dict=checkpoint_state,
        )
    )
    assert migration["checkpoint_key_count"] == 122
    assert migration["target_model_key_count"] == 141
    assert migration["shared_key_count"] == 122
    assert migration["checkpoint_only_key_count"] == 0
    assert migration["shared_shape_mismatch_count"] == 0
    assert migration["full_target_strict_load"] is True
    assert migration["migration_missing_keys"] == ()
    assert migration["migration_unexpected_keys"] == ()
    assert len(model.state_dict()) == 141

    batch = exact16_mixed_batch
    scheduler.validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(batch)
    assert batch.sample_identities == scheduler.EXACT16_MEMBER_IDENTITIES_V1
    assert batch.scheduled_task_ids == EXPECTED_TASKS
    assert batch.current11_batch_indices == tuple(range(11))
    assert batch.k36_batch_indices == tuple(range(11, 16))
    assert len(batch.model_input_batch["lig_coords"]) == 468
    assert len(batch.model_input_batch["pocket_coords"]) == 3335
    assert len(batch.supervision.pair_candidate_batch_index) == 2808
    assert int(batch.supervision.pair_candidate_is_positive.sum()) == 16

    tensorizer_calls = 0

    def forbidden_current11_tensorizer(**unused):
        nonlocal tensorizer_calls
        del unused
        tensorizer_calls += 1
        raise AssertionError("mixed bridge called Current11 tensorizer")

    monkeypatch.setattr(
        current11_owner,
        "tensorize_covapie_current11_training_supervision_v1",
        forbidden_current11_tensorizer,
    )
    validation_calls = 0
    published_validator = (
        scheduler.validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1
    )

    def counted_validation(value):
        nonlocal validation_calls
        validation_calls += 1
        return published_validator(value)

    monkeypatch.setattr(
        subject,
        "validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1",
        counted_validation,
    )
    model.train()
    parity_seed = 20260818
    manual = _manual_lower_level_forward(model, batch, seed=parity_seed)
    torch.manual_seed(parity_seed)
    bridged = model.forward(batch)
    assert type(bridged) is CovapieCurrent11TrainingForwardOutputV1
    assert bridged.supervision is batch.supervision
    assert tensorizer_calls == 0
    assert validation_calls == 1
    assert torch.equal(
        bridged.supervision.canonical_task_id,
        manual.supervision.canonical_task_id,
    )
    assert torch.equal(
        bridged.supervision.ligand_base_generation_mask,
        manual.supervision.ligand_base_generation_mask,
    )
    assert torch.equal(
        bridged.diffusion_trace.base_objective_per_sample,
        manual.diffusion_trace.base_objective_per_sample,
    )
    assert torch.equal(
        bridged.model_output.pair_logits,
        manual.model_output.pair_logits,
    )
    assert torch.equal(
        bridged.model_output.pre_post_geometry_predictions_angstrom,
        manual.model_output.pre_post_geometry_predictions_angstrom,
    )
    for name in (
        "loss_total",
        "loss_base_diffusion",
        "loss_covalent_pair_prediction",
        "loss_pre_post_geometry",
        "loss_covalent_pair_contrastive",
    ):
        assert torch.equal(
            getattr(bridged.loss_output, name),
            getattr(manual.loss_output, name),
        )
    for name in (
        "base_diffusion_valid_sample_count",
        "covalent_pair_prediction_valid_sample_count",
        "pre_post_geometry_valid_sample_count",
        "covalent_pair_contrastive_valid_sample_count",
    ):
        assert getattr(bridged.loss_output, name) == getattr(
            manual.loss_output, name
        )

    k36 = list(batch.k36_batch_indices)
    losses = bridged.loss_output
    assert tuple(batch.scheduled_task_ids[index] for index in k36) == (
        3, 0, 0, 0, 0
    )
    assert torch.isfinite(
        bridged.diffusion_trace.base_objective_per_sample[k36]
    ).all()
    assert torch.isfinite(
        losses.pair_prediction_per_sample_detached[k36]
    ).all()
    assert torch.isfinite(
        losses.pair_contrastive_per_sample_detached[k36]
    ).all()
    for index in k36:
        ligand_rows = batch.model_input_batch["lig_mask"] == index
        assert bool(batch.supervision.sample_training_admitted[index])
        assert bool(batch.supervision.canonical_task_valid[index])
        assert int(batch.supervision.canonical_task_id[index]) in (0, 3, 4)
        assert bool(
            batch.supervision.ligand_active_diffusion_loss_mask[
                ligand_rows, 0
            ].any()
        )
        assert bool(batch.supervision.pair_positive_candidate_valid[index])
        assert int(batch.supervision.pair_negative_count[index]) > 0

    logged: dict[str, object] = {}

    def capture_log(metrics, split, *, batch_size, sync_dist):
        logged.update({
            "metrics": metrics,
            "split": split,
            "batch_size": batch_size,
            "sync_dist": sync_dist,
        })

    monkeypatch.setattr(model, "log_metrics", capture_log)
    optimizer = model.configure_optimizers()
    named_parameters = dict(model.named_parameters())
    model_parameters = list(model.parameters())
    optimizer_parameters = [
        parameter
        for group in optimizer.param_groups
        for parameter in group["params"]
    ]
    assert isinstance(optimizer, torch.optim.AdamW)
    assert len({id(parameter) for parameter in optimizer_parameters}) == len(
        optimizer_parameters
    )
    assert {id(parameter) for parameter in optimizer_parameters} == {
        id(parameter) for parameter in model_parameters
    }
    parameter_before = {
        name: parameter.detach().clone()
        for name, parameter in named_parameters.items()
    }
    torch.manual_seed(20260819)
    metrics = model.training_step(batch, 0)
    expected_metric_keys = {
        "loss",
        "loss_base_diffusion",
        "loss_covalent_pair_prediction",
        "loss_pre_post_geometry",
        "loss_covalent_pair_contrastive",
    }
    assert set(metrics) == expected_metric_keys
    assert all(torch.isfinite(value).item() for value in metrics.values())
    assert logged == {
        "metrics": metrics,
        "split": "train",
        "batch_size": 16,
        "sync_dist": False,
    }
    assert tensorizer_calls == 0
    assert validation_calls == 2
    loss = metrics["loss"]
    assert loss.ndim == 0
    assert loss.requires_grad
    assert torch.isfinite(loss)
    assert metrics["loss_pre_post_geometry"].item() == 0.0

    shared_names = {
        name for name in named_parameters if name in checkpoint_state
    }
    new_names = set(named_parameters) - shared_names
    target_name = current11_smoke.LEGACY_ALLOWED_NEW_EXACT_KEYS_V1[0]
    role_names = {
        name
        for name in named_parameters
        if name.startswith((
            "covapie_current11_auxiliary_model_v1.role_embedding.",
            "covapie_current11_auxiliary_model_v1.task_embedding.",
            "covapie_current11_auxiliary_model_v1.generation_state_embedding.",
            "covapie_current11_auxiliary_model_v1.seed_indicator_embedding.",
            "covapie_current11_auxiliary_model_v1.anchor_distance_encoder.",
        ))
    }
    pair_names = {
        name
        for name in named_parameters
        if name.startswith((
            "covapie_current11_auxiliary_model_v1.pair_embedding.",
            "covapie_current11_auxiliary_model_v1.pair_logit.",
        ))
    }
    geometry_names = {
        name
        for name in named_parameters
        if name.startswith(
            "covapie_current11_auxiliary_model_v1.pre_post_geometry_head."
        )
    }
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    gradients = [
        parameter.grad
        for parameter in model_parameters
        if parameter.grad is not None
    ]
    assert gradients
    assert all(torch.isfinite(gradient).all() for gradient in gradients)
    assert any(
        _nonzero_finite_gradient(named_parameters[name])
        for name in shared_names
    )
    assert _nonzero_finite_gradient(named_parameters[target_name])
    assert any(
        _nonzero_finite_gradient(named_parameters[name])
        for name in role_names
    )
    assert any(
        _nonzero_finite_gradient(named_parameters[name])
        for name in pair_names
    )
    assert not any(
        _nonzero_finite_gradient(named_parameters[name])
        for name in geometry_names
    )
    optimizer.step()
    changed = {
        name
        for name, parameter in named_parameters.items()
        if not torch.equal(parameter.detach(), parameter_before[name])
    }
    assert changed & shared_names
    assert changed & new_names
    assert target_name in changed
    assert all(
        torch.isfinite(parameter).all() for parameter in model_parameters
    )
    assert losses.base_diffusion_valid_sample_count == 16
    assert losses.covalent_pair_prediction_valid_sample_count == 16
    assert losses.pre_post_geometry_valid_sample_count == 0
    assert losses.covalent_pair_contrastive_valid_sample_count == 16
    assert losses.loss_pre_post_geometry.item() == 0.0
    assert checkpoint_before == CHECKPOINT.read_bytes()
    assert _sha256(CHECKPOINT) == CHECKPOINT_SHA256


def test_import_has_no_stdout_or_stderr_side_effects() -> None:
    completed = subprocess.run(
        (
            os.environ.get("PYTHON", "python"),
            "-W",
            "ignore::SyntaxWarning",
            "-c",
            (
                "from Bio.PDB import Polypeptide as p; "
                "p.three_to_one = getattr(p, 'three_to_one', "
                "lambda name: p.protein_letters_3to1[name]); "
                "import covalent_ext."
                "covapie_expanded_cys_sg_mixed_profile_"
                "lightning_training_bridge_v1"
            ),
        ),
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": ".:src",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_source_is_additive_and_has_no_forbidden_training_or_io_paths() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    assert "strict" + "=False" not in source
    assert "Trainer" + ".fit" not in source
    assert "trainer" + ".fit" not in source
    assert "except BaseException" not in source
    assert "tensorize_covapie_current11_training_supervision_v1(" not in source
    assert "torch.save(" not in source
    assert ".save_checkpoint(" not in source
    assert "nn.Parameter" not in source
    assert "register_buffer" not in source
    assert "EGNNDynamics" not in source
    assert "binary_cross_entropy" not in source
    assert "smooth_l1_loss" not in source
    assert "data/raw" not in source
    assert "covapie-state" not in source
    declared = (ROOT / "environment.yaml").read_text(encoding="utf-8")
    assert "python=3.10.4" in declared
    assert "pytorch=2.0.1=*cuda11.8*" in declared
    assert "pytorch-lightning=1.8.4" in declared
