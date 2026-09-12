from __future__ import annotations

from dataclasses import fields, replace
import builtins
from pathlib import Path
import shutil
from unittest import mock

import pytest
import torch

from covalent_ext import covapie_batch001_feature_post_use_preflight_v1 as subject
from covalent_ext import covapie_current11_auxiliary_model_and_loss_v1 as loss_owner
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = (
    REPOSITORY_ROOT.parent / "covapie-state/bulk-multisource-cys-sg-v1/rcsb"
)


@pytest.fixture(scope="module")
def carriers():
    _authority, values = subject._build_carriers_v1(
        repository_root=REPOSITORY_ROOT, cache_root=CACHE_ROOT
    )
    return values


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


def _carrier(carriers, split: str, epoch: int):
    return next(
        value
        for value in carriers
        if value.formal_split == split and value.epoch == epoch
    )


def _forbidden(*_args, **_kwargs):
    raise AssertionError("forbidden model/training operation was invoked")


def test_fixed_source_bindings_compare_current_bytes_to_frozen_legacy_pins() -> None:
    bindings = (
        subject.verify_covapie_batch001_feature_post_use_preflight_sources_v1(
            repository_root=REPOSITORY_ROOT
        )
    )
    by_path = {binding.relative_path: binding for binding in bindings}
    assert tuple((item.relative_path, item.observed_sha256) for item in bindings) == tuple(
        subject.BOUND_SOURCE_SHA256_V1
    )
    for relative, current_sha in subject.CURRENT_SOURCE_SHA256_V1.items():
        binding = by_path[relative]
        assert binding.observed_sha256 == current_sha
        assert (
            binding.legacy_formal_integration_sha256
            == subject.LEGACY_FORMAL_INTEGRATION_PINS_V1[relative]
        )
        assert binding.differs_from_legacy_formal_integration


def test_source_binding_drift_fails_closed(tmp_path: Path) -> None:
    for relative, _sha256 in subject.BOUND_SOURCE_SHA256_V1:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY_ROOT / relative, target)
    drifted = tmp_path / subject.CURRENT_LOSS_SOURCE_V1
    drifted.write_bytes(drifted.read_bytes() + b"\n# unexpected drift\n")
    with pytest.raises(ValueError, match="BOUND_SOURCE_SHA256_MISMATCH"):
        subject.verify_covapie_batch001_feature_post_use_preflight_sources_v1(
            repository_root=tmp_path.resolve()
        )


def test_exact10_h_filter_and_unsupported_non_h_policy() -> None:
    assert subject.validate_covapie_batch001_feature_projection_policy_v1()
    passed = subject.feature_owner.project_type_symbols_to_checkpoint_heavy_v1(
        ("C", "H", "O")
    )
    assert passed.keep_mask == (True, False, True)
    assert passed.checkpoint_channel_indices == (0, None, 2)
    rejected = subject.feature_owner.project_type_symbols_to_checkpoint_heavy_v1(
        ("C", "Se", "O")
    )
    assert rejected.sample_rejected
    assert rejected.keep_mask == (False, False, False)
    assert rejected.checkpoint_channel_indices == (None, None, None)


def test_real_preflight_is_deterministic_and_trips_no_forbidden_operation() -> None:
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "lightning" or name.startswith("lightning."):
            _forbidden()
        if name == "pytorch_lightning" or name.startswith("pytorch_lightning."):
            _forbidden()
        return original_import(name, *args, **kwargs)

    with (
        mock.patch.object(torch, "load", side_effect=_forbidden),
        mock.patch.object(torch.nn.Module, "__init__", side_effect=_forbidden),
        mock.patch.object(torch.nn.Module, "__call__", side_effect=_forbidden),
        mock.patch.object(
            loss_owner,
            "compute_covapie_current11_training_losses_v1",
            side_effect=_forbidden,
        ),
        mock.patch.object(torch.Tensor, "backward", side_effect=_forbidden),
        mock.patch.object(torch.optim.Optimizer, "step", side_effect=_forbidden),
        mock.patch.object(builtins, "__import__", side_effect=guarded_import),
    ):
        first = subject.run_covapie_batch001_feature_post_use_preflight_v1(
            repository_root=REPOSITORY_ROOT, cache_root=CACHE_ROOT
        )
        second = subject.run_covapie_batch001_feature_post_use_preflight_v1(
            repository_root=REPOSITORY_ROOT, cache_root=CACHE_ROOT
        )
    assert (
        subject.serialize_covapie_batch001_feature_post_use_preflight_result_v1(first)
        == subject.serialize_covapie_batch001_feature_post_use_preflight_result_v1(second)
    )
    assert first.train_hidden_post_eligible_counts == (5, 4, 5, 4, 2)
    assert first.validation_hidden_post_eligible_counts == (0, 0, 0, 0, 0)
    assert first.actual_carrier_split_count == 10
    assert first.actual_carrier_event_epoch_count == 45
    assert not first.test_carrier_constructed
    assert first.scoped_carrier_feature_preflight_pass
    assert first.scoped_hidden_post_eligibility_preflight_pass
    assert first.current_source_bindings_verified
    assert not first.legacy_trainer_routing_updated
    assert not first.production_loss_gate_called
    assert not first.checkpoint_loaded
    assert not first.model_instantiated
    assert not first.model_or_loss_executed
    assert not first.parameter_update_performed_this_round
    assert not first.training_started
    assert not first.ready_for_training
    assert first.feature_semantics_audit_required_later
    assert first.step12d_is_only_smoke_legality_check


def test_real_rows_report_exact5_and_b3_excludes_only_hidden_post(carriers) -> None:
    all_rows = []
    for carrier in carriers:
        _fingerprint, rows = subject.audit_covapie_batch001_feature_post_use_carrier_v1(
            carrier
        )
        all_rows.extend(rows)
    assert {row.canonical_task_semantic_name for row in all_rows} == {
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    }
    train_b3 = [
        row
        for row in all_rows
        if row.formal_split == "train" and row.canonical_task_id == 3
    ]
    assert len(train_b3) == 5
    assert all(row.original_post_request for row in train_b3)
    assert all(row.original_post_component_valid for row in train_b3)
    assert all(not row.positive_endpoint_generated for row in train_b3)
    assert all(row.positive_endpoint_fixed for row in train_b3)
    assert all(not row.preflight_effective_hidden_post_eligible for row in train_b3)
    assert all(row.exclusion_reasons == ("positive_endpoint_not_generated", "positive_endpoint_fixed") for row in train_b3)


def test_atom_reorder_and_index_misalignment_are_rejected(carriers) -> None:
    candidate = _clone_carrier(_carrier(carriers, "train", 0))
    index = candidate.model_input_batch["lig_parser_local_index"]
    index[0], index[1] = index[1].clone(), index[0].clone()
    with pytest.raises(ValueError, match="INDEX_OR_MEMBERSHIP_MISMATCH"):
        subject.audit_covapie_batch001_feature_post_use_carrier_v1(candidate)


def test_cross_sample_pair_and_wrong_cys_sg_anchor_are_rejected(carriers) -> None:
    cross_sample = _clone_carrier(_carrier(carriers, "train", 0))
    positive = int(cross_sample.supervision.pair_positive_candidate_index[0].item())
    sample_one_first = int(
        torch.nonzero(
            cross_sample.model_input_batch["lig_mask"] == 1, as_tuple=False
        )[0].item()
    )
    cross_sample.supervision.pair_candidate_ligand_flat_index[positive] = sample_one_first
    with pytest.raises(ValueError, match="INDEPENDENT_MEMBERSHIP_INVALID"):
        subject.audit_covapie_batch001_feature_post_use_carrier_v1(cross_sample)

    wrong_anchor = _clone_carrier(_carrier(carriers, "train", 0))
    wrong_anchor.supervision.target_residue_reactive_atom_flat_index[0] += 1
    with pytest.raises(ValueError, match="TARGET_CYS_SG_CONDITION"):
        subject.audit_covapie_batch001_feature_post_use_carrier_v1(wrong_anchor)


def test_generation_fixed_overlap_and_task_role_conflict_are_rejected(carriers) -> None:
    overlap = _clone_carrier(_carrier(carriers, "train", 0))
    generated_flat = int(
        torch.nonzero(
            overlap.supervision.ligand_base_generation_mask[:, 0], as_tuple=False
        )[0].item()
    )
    overlap.supervision.ligand_base_fixed_mask[generated_flat, 0] = True
    with pytest.raises(ValueError, match="GENERATION_FIXED_OR_TASK_ROLE"):
        subject.audit_covapie_batch001_feature_post_use_carrier_v1(overlap)

    task_conflict = _clone_carrier(_carrier(carriers, "train", 0))
    task_conflict.supervision.canonical_task_id[0] = 3
    with pytest.raises(ValueError, match="CARRIER_TASK_OR_ADMISSION_TENSOR_INVALID"):
        subject.audit_covapie_batch001_feature_post_use_carrier_v1(task_conflict)


def test_validation_training_activation_is_rejected(carriers) -> None:
    validation = _clone_carrier(_carrier(carriers, "validation", 0))
    validation.supervision.sample_training_admitted[0] = True
    with pytest.raises(ValueError, match="TASK_OR_ADMISSION_TENSOR_INVALID"):
        subject.audit_covapie_batch001_feature_post_use_carrier_v1(validation)

    metadata_activation = replace(
        _clone_carrier(_carrier(carriers, "validation", 0)),
        optimizer_population_eligible=(True, False, False, False),
    )
    with pytest.raises(ValueError, match="SPLIT_ACTIVATION_BOUNDARY_INVALID"):
        subject.audit_covapie_batch001_feature_post_use_carrier_v1(
            metadata_activation
        )


def test_false_post_request_is_not_upgraded(carriers) -> None:
    candidate = _clone_carrier(_carrier(carriers, "train", 0))
    assert bool(candidate.supervision.ligand_base_generation_mask[
        candidate.supervision.pair_candidate_ligand_flat_index[
            candidate.supervision.pair_positive_candidate_index[0]
        ],
        0,
    ].item())
    candidate.supervision.pre_post_geometry_component_loss_mask[0, 1] = False
    _fingerprint, rows = subject.audit_covapie_batch001_feature_post_use_carrier_v1(
        candidate
    )
    assert not rows[0].original_post_request
    assert not rows[0].preflight_effective_hidden_post_eligible
    assert rows[0].exclusion_reasons == ("post_request_false",)


def test_pre_and_unavailable_seed_cannot_be_fabricated(carriers) -> None:
    fabricated_pre = _clone_carrier(_carrier(carriers, "train", 0))
    fabricated_pre.supervision.pre_post_geometry_target_angstrom[0, 0] = 1.0
    with pytest.raises(ValueError, match="PRE_POST_OR_DIAGNOSTIC_CONTRACT_INVALID"):
        subject.audit_covapie_batch001_feature_post_use_carrier_v1(fabricated_pre)

    fabricated_seed = _clone_carrier(_carrier(carriers, "train", 0))
    fabricated_seed.supervision.ligand_minimal_seed_or_anchor_valid[0] = True
    with pytest.raises(ValueError, match="UNAVAILABLE_MINIMAL_SEED_WAS_UPGRADED"):
        subject.audit_covapie_batch001_feature_post_use_carrier_v1(fabricated_seed)


def test_carrier_audit_does_not_mutate_inputs(carriers) -> None:
    candidate = _carrier(carriers, "validation", 4)
    before = subject._carrier_fingerprint(candidate)
    reported, _rows = subject.audit_covapie_batch001_feature_post_use_carrier_v1(
        candidate
    )
    after = subject._carrier_fingerprint(candidate)
    assert before == reported == after
