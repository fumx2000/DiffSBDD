from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
import torch

from covalent_ext import (
    covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
    as current11_smoke,
)
from covalent_ext import (
    covapie_current11_trainable_supervision_materializer_v1 as materializer,
)
from covalent_ext import (
    covapie_exact16_post_geometry_partial_supervision_authority_v1 as subject,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1
    as scheduler,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed_tensorizer,
)
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11LossWeightsV1,
    compute_covapie_current11_training_losses_v1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = (ROOT.parent / "covapie-state").resolve()
ERROR = subject.COVAPIE_EXACT16_POST_GEOMETRY_PARTIAL_SUPERVISION_AUTHORITY_V1_ERROR
EXPECTED_POST = (
    1.670,
    1.800,
    1.718,
    1.802,
    1.809,
    1.762,
    1.807,
    1.799,
    1.806,
    1.794,
    1.717,
    1.887900,
    1.894489,
    1.809903,
    1.765181,
    1.638083,
)


@pytest.fixture(scope="module")
def exact16_authority_context(tmp_path_factory: pytest.TempPathFactory):
    temporary = tmp_path_factory.mktemp("covapie_exact16_post_authority")
    clone = temporary / "repository"
    scheduler._clone_head_v1(ROOT, clone)
    real = current11_smoke._build_real_current11_batch_v1(
        repo_root=clone,
        state_root=STATE,
    )
    machine_payload = (
        materializer.load_covapie_current11_machine_authority_payload_v1(
            repo_root=clone,
            state_root=STATE,
            runtime_output17=real["runtime"]["remap_output17_or_none"],
        )
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
            sample = (
                mixed_tensorizer.tensorize_covapie_expanded_cys_sg_sample_v1(
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
            )
        else:
            sample = (
                mixed_tensorizer.tensorize_covapie_expanded_cys_sg_sample_v1(
                    sample_identity=identity,
                    task_id=task_id,
                    device="cpu",
                    repository_root=ROOT,
                    state_root=STATE,
                )
            )
        samples.append(sample)
    mixed_batch = (
        scheduler.collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1(
            samples,
            epoch=0,
            task_schedule_seed=0,
        )
    )
    evidence = subject.derive_covapie_exact16_post_geometry_authority_evidence_v1(
        mixed_batch=mixed_batch,
        current11_machine_authority_payload=machine_payload,
        repository_root=ROOT,
        state_root=STATE,
    )
    result = subject.bind_covapie_exact16_post_geometry_partial_supervision_authority_v1(
        mixed_batch=mixed_batch,
        authority_evidence=evidence,
    )
    return {
        "mixed_batch": mixed_batch,
        "machine_payload": machine_payload,
        "evidence": evidence,
        "result": result,
    }


def _assert_error(callable_object, reason: str) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}:{reason}$"):
        callable_object()


def _replace_evidence(context, index: int, **changes):
    evidence = list(context["evidence"])
    evidence[index] = replace(evidence[index], **changes)
    return tuple(evidence)


def test_registry_exact16_counts_source_values_and_semantic_separation(
    exact16_authority_context,
) -> None:
    context = exact16_authority_context
    mixed_batch = context["mixed_batch"]
    result = context["result"]
    supervision = result.supervision
    assert subject.GEOMETRY_COMPONENT_REGISTRY_V1 == (
        subject.CovapieExact16GeometryComponentV1(
            component_index=0,
            semantic_name=(
                "PRE_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM"
            ),
            unit="angstrom",
            formal_definition=(
                "distance between the exact authoritative protein reactive atom "
                "and exact authoritative ligand reactive atom in a canonical "
                "authoritative pre-covalent state"
            ),
        ),
        subject.CovapieExact16GeometryComponentV1(
            component_index=1,
            semantic_name=(
                "POST_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM"
            ),
            unit="angstrom",
            formal_definition=(
                "distance between the same exact authoritative reactive pair in "
                "a resolved authoritative post-covalent state"
            ),
        ),
    )
    assert result.sample_identities == scheduler.EXACT16_MEMBER_IDENTITIES_V1
    assert len(result.authority_evidence) == 16
    assert sum(item.sample_identity.startswith("CYS_SG_") for item in result.authority_evidence) == 11
    assert sum(item.ligand_endpoint_comp_id == "K36" for item in result.authority_evidence) == 5
    assert torch.isnan(supervision.pre_post_geometry_target_angstrom[:, 0]).all()
    assert not supervision.pre_post_geometry_component_valid_mask[:, 0].any()
    assert not supervision.pre_post_geometry_component_loss_mask[:, 0].any()
    assert torch.isfinite(supervision.pre_post_geometry_target_angstrom[:, 1]).all()
    assert supervision.pre_post_geometry_component_valid_mask[:, 1].all()
    assert supervision.pre_post_geometry_component_loss_mask[:, 1].all()
    torch.testing.assert_close(
        supervision.pre_post_geometry_target_angstrom[:, 1],
        torch.tensor(EXPECTED_POST, dtype=torch.float32),
        rtol=0,
        atol=subject.OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1,
    )
    torch.testing.assert_close(
        supervision.pre_post_geometry_target_angstrom[:, 1],
        mixed_batch.supervision.observed_complex_pair_distance_angstrom[:, 0],
        rtol=0,
        atol=subject.OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1,
    )
    assert (
        supervision.pre_post_geometry_target_angstrom.untyped_storage().data_ptr()
        != supervision.observed_complex_pair_distance_angstrom.untyped_storage().data_ptr()
    )
    assert (
        supervision.observed_complex_pair_distance_angstrom
        is mixed_batch.supervision.observed_complex_pair_distance_angstrom
    )
    assert torch.isnan(
        mixed_batch.supervision.pre_post_geometry_target_angstrom
    ).all()
    assert not mixed_batch.supervision.pre_post_geometry_component_valid_mask.any()
    assert not mixed_batch.supervision.pre_post_geometry_component_loss_mask.any()
    subject.validate_covapie_exact16_post_geometry_partial_supervision_authority_v1(
        result=result
    )


def test_real_source_evidence_is_sha_bound_unique_and_k36_altloc_preserved(
    exact16_authority_context,
) -> None:
    context = exact16_authority_context
    evidence = context["evidence"]
    assert all(item.explicit_event_valid for item in evidence)
    assert all(item.source_bindings for item in evidence)
    assert all(
        binding.sha256_verified
        for item in evidence
        for binding in item.source_bindings
    )
    assert all(item.protein_endpoint_mapping_count == 1 for item in evidence)
    assert all(item.ligand_endpoint_mapping_count == 1 for item in evidence)
    assert all(item.protein_endpoint_comp_id == "CYS" for item in evidence)
    assert all(item.protein_endpoint_atom_id == "SG" for item in evidence)
    altloc = {item.sample_identity: item.ligand_endpoint_altloc_identity for item in evidence[11:]}
    assert altloc == {
        "4DCD/K36": "NONE",
        "4F49/K36": "NONE",
        "5WKJ/K36": "B",
        "6L70/K36": "NONE",
        "6WTT/K36": "NONE",
    }
    assert all(
        item.ligand_endpoint_altloc_identity
        == item.event_selected_ligand_altloc_identity
        for item in evidence[11:]
    )
    repeated = subject.derive_covapie_exact16_post_geometry_authority_evidence_v1(
        mixed_batch=context["mixed_batch"],
        current11_machine_authority_payload=context["machine_payload"],
        repository_root=ROOT,
        state_root=STATE,
    )
    assert repeated == evidence


@pytest.mark.parametrize(
    ("index", "changes", "reason"),
    (
        (0, {"explicit_event_valid": False}, "EXPLICIT_EVENT_OR_SOURCE_IDENTITY_INVALID"),
        (0, {"ligand_endpoint_atom_id": "WRONG"}, "REACTIVE_ENDPOINT_IDENTITY_INVALID"),
        (0, {"protein_endpoint_atom_id": "CB"}, "REACTIVE_ENDPOINT_IDENTITY_INVALID"),
        (0, {"ligand_endpoint_retained_flat_index": -1}, "REACTIVE_ENDPOINT_NOT_RETAINED_OR_CROSS_SAMPLE"),
        (0, {"ligand_endpoint_mapping_count": 2}, "REACTIVE_ENDPOINT_MAPPING_NOT_UNIQUE"),
        (0, {"positive_pair_ligand_flat_index": 1}, "POSITIVE_PAIR_IDENTITY_MISMATCH"),
        (0, {"positive_pair_sample_index": 1}, "CROSS_SAMPLE_PAIR_MISMATCH"),
        (0, {"recorded_observed_distance_angstrom": 9.0}, "OBSERVED_DISTANCE_COORDINATE_INCONSISTENT"),
        (0, {"ligand_endpoint_coordinate_angstrom": (float("nan"), 0.0, 0.0)}, "REACTIVE_ENDPOINT_COORDINATE_NONFINITE"),
        (13, {"ligand_endpoint_altloc_identity": "A"}, "K36_EVENT_SELECTED_ALTLOC_IDENTITY_INVALID"),
        (0, {"sample_training_admitted": False}, "SAMPLE_NOT_TRAINING_ADMITTED"),
    ),
)
def test_observed_numeric_value_cannot_bypass_invalid_authority(
    exact16_authority_context,
    index: int,
    changes: dict[str, object],
    reason: str,
) -> None:
    context = exact16_authority_context
    assert torch.isfinite(
        context["mixed_batch"].supervision.observed_complex_pair_distance_angstrom[
            index, 0
        ]
    )
    corrupted = _replace_evidence(context, index, **changes)
    _assert_error(
        lambda: subject.bind_covapie_exact16_post_geometry_partial_supervision_authority_v1(
            mixed_batch=context["mixed_batch"],
            authority_evidence=corrupted,
        ),
        reason,
    )


def test_unverified_source_sha_binding_fails_closed(
    exact16_authority_context,
) -> None:
    context = exact16_authority_context
    first = context["evidence"][0]
    bindings = list(first.source_bindings)
    bindings[0] = replace(bindings[0], sha256_verified=False)
    corrupted = _replace_evidence(
        context, 0, source_bindings=tuple(bindings)
    )
    _assert_error(
        lambda: subject.bind_covapie_exact16_post_geometry_partial_supervision_authority_v1(
            mixed_batch=context["mixed_batch"],
            authority_evidence=corrupted,
        ),
        "SOURCE_SHA256_BINDING_INVALID",
    )


def test_tensor_training_admission_false_fails_even_with_valid_source_evidence(
    exact16_authority_context,
) -> None:
    context = exact16_authority_context
    batch = context["mixed_batch"]
    admitted = batch.supervision.sample_training_admitted.clone()
    admitted[0] = False
    corrupted_supervision = replace(
        batch.supervision, sample_training_admitted=admitted
    )
    corrupted_batch = replace(batch, supervision=corrupted_supervision)
    _assert_error(
        lambda: subject.bind_covapie_exact16_post_geometry_partial_supervision_authority_v1(
            mixed_batch=corrupted_batch,
            authority_evidence=context["evidence"],
        ),
        "HISTORICAL_EXACT16_BATCH_INVALID",
    )


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("target", 2.0, "PRE_FINITE_TARGET_WITHOUT_AUTHORITY"),
        ("valid", True, "PRE_VALID_WITHOUT_AUTHORITY"),
        ("loss", True, "PRE_LOSS_WITHOUT_AUTHORITY"),
    ),
)
def test_pre_authority_attempts_fail_closed(
    exact16_authority_context,
    field: str,
    value: object,
    reason: str,
) -> None:
    context = exact16_authority_context
    batch = context["mixed_batch"]
    changes = {}
    if field == "target":
        tensor = batch.supervision.pre_post_geometry_target_angstrom.clone()
        tensor[0, 0] = value
        changes["pre_post_geometry_target_angstrom"] = tensor
    elif field == "valid":
        tensor = batch.supervision.pre_post_geometry_component_valid_mask.clone()
        tensor[0, 0] = value
        changes["pre_post_geometry_component_valid_mask"] = tensor
    else:
        tensor = batch.supervision.pre_post_geometry_component_loss_mask.clone()
        tensor[0, 0] = value
        changes["pre_post_geometry_component_loss_mask"] = tensor
    corrupted_batch = replace(
        batch,
        supervision=replace(batch.supervision, **changes),
    )
    _assert_error(
        lambda: subject.bind_covapie_exact16_post_geometry_partial_supervision_authority_v1(
            mixed_batch=corrupted_batch,
            authority_evidence=context["evidence"],
        ),
        reason,
    )


def test_controlled_nonzero_geometry_weight_real_exact16_backward(
    exact16_authority_context,
) -> None:
    context = exact16_authority_context
    mixed_batch = context["mixed_batch"]
    supervision = context["result"].supervision
    torch.manual_seed(20260818)
    model = current11_smoke._instantiate_current11_model_v1(
        repo_root=ROOT,
        state_root=STATE,
        device="cpu",
    )
    model.train()
    ligand, pocket = model.get_ligand_and_pocket(
        mixed_batch.model_input_batch
    )
    role_delta = (
        model.covapie_current11_auxiliary_model_v1.encode_role_mask_anchor_v1(
            supervision=supervision,
            ligand_batch_index=ligand["mask"],
        )
    )
    torch.manual_seed(20260818)
    trace = run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1(
        ddpm=model.ddpm,
        ligand=ligand,
        pocket=pocket,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
        pocket_target_residue_atom_condition_indicator=(
            supervision.target_residue_reactive_atom_mask[:, 0]
        ),
    )
    model_output = model.covapie_current11_auxiliary_model_v1(
        diffusion_trace=trace,
        supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
    )
    controlled_weights = CovapieCurrent11LossWeightsV1(
        base_diffusion=1.0,
        covalent_pair_prediction=1.0,
        pre_post_geometry=1.0,
        covalent_pair_contrastive=0.1,
    )
    losses = compute_covapie_current11_training_losses_v1(
        model_output=model_output,
        supervision=supervision,
        diffusion_trace=trace,
        loss_weights=controlled_weights,
        pair_contrastive_temperature=1.0,
        geometry_smooth_l1_beta=1.0,
    )
    assert losses.pre_post_geometry_valid_sample_count == 16
    assert torch.isfinite(losses.loss_pre_post_geometry)
    assert losses.loss_pre_post_geometry.item() > 0
    assert torch.isfinite(
        losses.pre_post_geometry_per_sample_detached[
            list(mixed_batch.k36_batch_indices)
        ]
    ).all()
    assert not supervision.pre_post_geometry_component_loss_mask[:, 0].any()
    assert supervision.pre_post_geometry_component_loss_mask[:, 1].sum().item() == 16
    model.zero_grad(set_to_none=True)
    losses.loss_total.backward()
    named_parameters = dict(model.named_parameters())
    geometry_parameters = {
        name: parameter
        for name, parameter in named_parameters.items()
        if name.startswith(
            "covapie_current11_auxiliary_model_v1.pre_post_geometry_head."
        )
    }
    shared_parameters = {
        name: parameter
        for name, parameter in named_parameters.items()
        if not name.startswith("covapie_current11_auxiliary_model_v1.")
    }
    geometry_gradients = [
        parameter.grad
        for parameter in geometry_parameters.values()
        if parameter.grad is not None
    ]
    shared_gradients = [
        parameter.grad
        for parameter in shared_parameters.values()
        if parameter.grad is not None
    ]
    all_gradients = [
        parameter.grad
        for parameter in named_parameters.values()
        if parameter.grad is not None
    ]
    assert geometry_gradients
    assert shared_gradients
    assert all_gradients
    assert all(torch.isfinite(gradient).all() for gradient in all_gradients)
    assert any(torch.count_nonzero(gradient).item() > 0 for gradient in geometry_gradients)
    assert any(torch.count_nonzero(gradient).item() > 0 for gradient in shared_gradients)


def test_successor_contains_no_pre_reconstruction_or_training_execution() -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8").lower()
    assert "import rdkit" not in source
    assert "from rdkit" not in source
    assert "import openmm" not in source
    assert "delete_bond" not in source
    assert "restrained_minim" not in source
    assert "docking" not in source
    assert ".backward(" not in source
    assert ".step(" not in source
    assert "trainer.fit(" not in source
