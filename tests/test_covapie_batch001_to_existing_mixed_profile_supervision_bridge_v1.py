from __future__ import annotations

from dataclasses import fields, replace
import json

import pytest
import torch

from covalent_ext import covapie_batch001_positive_structural_input_v1 as structural
from covalent_ext import covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1 as subject
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


@pytest.fixture(scope="module")
def records():
    return structural.build_covapie_batch001_positive_structural_records_v1()


@pytest.fixture(scope="module")
def population():
    return subject.collate_covapie_batch001_preview_population_v1(
        epoch=0, task_schedule_seed=0
    )


def _assert_tensor_equal(left: torch.Tensor, right: torch.Tensor) -> None:
    assert left.dtype == right.dtype
    assert left.shape == right.shape
    if left.dtype.is_floating_point:
        assert torch.equal(torch.isnan(left), torch.isnan(right))
        assert torch.equal(torch.nan_to_num(left), torch.nan_to_num(right))
    else:
        assert torch.equal(left, right)


def _mutated_batch(population, **supervision_changes):
    supervision = replace(population.supervision, **supervision_changes)
    return replace(population, supervision=supervision)


def test_exact13_structural_population_and_reconciliation(records) -> None:
    assert tuple(row.canonical_event_id for row in records) == (
        structural.BATCH001_POSITIVE_EVENT_IDS_V1
    )
    assert sum(row.role_profile == "STRICT_LINKER_PRESENT_V1" for row in records) == 11
    assert sum(
        row.role_profile == "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        for row in records
    ) == 2
    assert all(structural.validate_covapie_batch001_positive_structural_record_v1(row) for row in records)
    assert [len(row.ligand_retained_heavy_atoms) for row in records] == [
        23, 23, 13, 13, 17, 17, 23, 23, 23, 23, 23, 23, 23
    ]
    assert [len(row.pocket_retained_heavy_atoms) for row in records] == [
        103, 118, 129, 124, 64, 69, 115, 131, 132, 112, 124, 110, 123
    ]
    assert all(row.feature_projection_status == "EXACT10_PASS" for row in records)
    assert all(row.protein_reactive_atom_id == "SG" for row in records)


def test_px5_human_roles_and_historical_vs_effective_state(records) -> None:
    px5 = [row for row in records if row.ligand_component_id == "PX5"]
    assert len(px5) == 2
    for row in px5:
        assert row.scaffold_atom_ids == (
            "C1", "C2", "C3", "C4", "C5", "C6", "C8", "N9", "S7"
        )
        assert row.linker_atom_ids == ()
        assert row.warhead_atom_ids == (
            "C10", "C11", "C12", "C13", "C14", "C15", "O16", "O17"
        )
        assert row.ligand_reactive_atom_id == "C15"
        assert row.direct_scaffold_warhead_boundary == ("C8", "C10", "SING")
        assert row.historical_snapshot_mask_compatibility is False
        assert row.applicable_canonical_task_ids == (0, 3, 4)
        assert row.not_applicable_canonical_task_ids == (1, 2)


def test_profile_scheduler_is_exact_order_independent_and_rejects_bool() -> None:
    identities = structural.BATCH001_POSITIVE_EVENT_IDS_V1
    forward = {
        identity: subject.canonical_task_id_for_covapie_batch001_sample_v1(
            sample_identity=identity, epoch=7, task_schedule_seed=31
        )
        for identity in identities
    }
    reverse = {
        identity: subject.canonical_task_id_for_covapie_batch001_sample_v1(
            sample_identity=identity, epoch=7, task_schedule_seed=31
        )
        for identity in reversed(identities)
    }
    assert forward == reverse
    assert set(forward[identity] for identity in identities[4:6]) <= {0, 3, 4}
    with pytest.raises(ValueError):
        subject.canonical_task_id_for_covapie_batch001_sample_v1(
            sample_identity=identities[0], epoch=True, task_schedule_seed=0
        )
    with pytest.raises(ValueError):
        subject.canonical_task_id_for_covapie_batch001_sample_v1(
            sample_identity=identities[0], epoch=0, task_schedule_seed=False
        )


def test_strict_all_five_and_direct_exact_three_task_tensorization(records) -> None:
    strict = records[0]
    direct = records[4]
    for task_id in range(5):
        batch = subject._tensorize_records_v1(
            records=(strict,), task_ids=(task_id,), epoch=0, task_schedule_seed=0
        )
        assert batch.canonical_task_ids == (task_id,)
        assert subject.validate_covapie_batch001_preview_batch_v1(batch)
    for task_id in (0, 3, 4):
        batch = subject._tensorize_records_v1(
            records=(direct,), task_ids=(task_id,), epoch=0, task_schedule_seed=0
        )
        assert batch.canonical_task_ids == (task_id,)
        assert subject.validate_covapie_batch001_preview_batch_v1(batch)
    for task_id in (1, 2):
        with pytest.raises(ValueError, match="TASK_NOT_APPLICABLE_FOR_ROLE_PROFILE"):
            subject.tensorize_covapie_batch001_positive_sample_v1(
                sample_identity=direct.sample_identity,
                canonical_task_id=task_id,
                epoch=0,
                task_schedule_seed=0,
            )
    assert direct.linker_atom_ids == ()


def test_model_input_and_existing_supervision_dataclass_shapes(population) -> None:
    model = population.model_input_batch
    assert model["lig_coords"].shape == (267, 3)
    assert model["pocket_coords"].shape == (1454, 3)
    assert model["lig_one_hot"].shape == (267, 10)
    assert model["pocket_one_hot"].shape == (1454, 10)
    assert model["num_lig_atoms"].shape == (13,)
    assert model["num_pocket_nodes"].shape == (13,)
    assert isinstance(
        population.supervision, CovapieCurrent11TrainingSupervisionTensorsV1
    )
    assert len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) == 37
    assert subject.validate_covapie_batch001_preview_batch_v1(
        population, require_exact13_population=True
    )


def test_labels_available_but_all_admission_gated_losses_inactive(population) -> None:
    supervision = population.supervision
    assert supervision.sample_training_admitted.tolist() == [False] * 13
    assert supervision.canonical_task_valid.tolist() == [True] * 13
    assert supervision.ligand_role_valid.all()
    assert supervision.target_residue_condition_valid.all()
    assert supervision.pair_positive_candidate_valid.all()
    assert supervision.observed_complex_pair_distance_valid.all()
    assert supervision.ligand_anchor_distance_valid.all()
    assert not supervision.ligand_active_diffusion_loss_mask.any()
    assert not supervision.pair_head_candidate_loss_mask.any()
    assert not supervision.pair_contrastive_sample_loss_mask.any()
    assert not supervision.pre_post_geometry_component_loss_mask.any()


def test_minimal_seed_disabled_anchor_ready_and_post_only_geometry(population) -> None:
    supervision = population.supervision
    assert not supervision.ligand_minimal_seed_or_anchor_mask.any()
    assert supervision.ligand_minimal_seed_or_anchor_valid.tolist() == [False] * 13
    assert torch.isfinite(supervision.ligand_anchor_distance_angstrom).all()
    assert (supervision.ligand_anchor_distance_angstrom >= 0).all()
    assert supervision.ligand_anchor_distance_valid.all()
    assert torch.isnan(supervision.pre_post_geometry_target_angstrom[:, 0]).all()
    assert torch.isfinite(supervision.pre_post_geometry_target_angstrom[:, 1]).all()
    assert supervision.pre_post_geometry_component_valid_mask.tolist() == [
        [False, True]
    ] * 13


def test_pair_candidate_domain_and_collation_consistency(population) -> None:
    supervision = population.supervision
    assert supervision.pair_candidate_offsets.tolist() == [
        0, 138, 276, 354, 432, 534, 636, 751, 866, 981, 1096, 1234, 1372, 1510
    ]
    assert supervision.pair_candidate_is_positive.sum().item() == 13
    assert supervision.pair_negative_count.tolist() == [
        137, 137, 77, 77, 101, 101, 114, 114, 114, 114, 137, 137, 137
    ]
    assert supervision.pair_candidate_is_negative.sum().item() == 1497
    assert subject.validate_covapie_batch001_preview_batch_v1(
        population, require_exact13_population=True
    )


def test_split_prediction_is_metadata_only_and_ndu_is_retained(records) -> None:
    assert sum(row.predicted_split_if_any == "train" for row in records) == 6
    assert sum(row.predicted_split_if_any == "validation" for row in records) == 3
    ndu = [row for row in records if row.ligand_component_id == "NDU"]
    assert len(ndu) == 4
    assert all(row.predicted_split_if_any == "" for row in ndu)
    assert all(
        row.split_prediction_status
        == "LEAKAGE_EVIDENCE_INCOMPLETE_UNASSIGNED_READ_ONLY"
        for row in ndu
    )
    assert all(not row.split_admission_authoritative for row in records)
    assert all(not row.sample_training_admitted for row in records)


@pytest.mark.parametrize(
    "identity",
    (
        "UNKNOWN",
        "COVAPIE_CYS_SG_EVENT_V1:2JU4:A:CYS:10-:SG:B:RCY:C1S",
        "COVAPIE_CYS_SG_EVENT_V1:XXXX:A:CYS:1-:SG:B:ONL:C1",
    ),
)
def test_unknown_negative_and_onl_population_rejected(identity) -> None:
    with pytest.raises(ValueError):
        subject.valid_task_ids_for_covapie_batch001_sample_v1(identity)


def test_wrong_structure_and_ccd_sha_fail_closed(monkeypatch) -> None:
    monkeypatch.setitem(
        structural.BATCH001_STRUCTURE_SHA256_BY_PDB_V1, "3LOK", "0" * 64
    )
    with pytest.raises(ValueError, match="STRUCTURE_CACHE_MANIFEST_BINDING_INVALID"):
        structural.build_covapie_batch001_positive_structural_records_v1()
    monkeypatch.undo()
    monkeypatch.setitem(
        structural.BATCH001_CCD_SHA256_BY_COMPONENT_V1, "DJK", "0" * 64
    )
    with pytest.raises(ValueError, match="CCD_CACHE_MANIFEST_BINDING_INVALID"):
        structural.build_covapie_batch001_positive_structural_records_v1()


@pytest.mark.parametrize("mutation", ("reactive", "sg", "overlap", "gap", "px5_linker", "strict_linker"))
def test_structural_mapping_and_role_mutations_fail_closed(records, mutation) -> None:
    row = records[4] if mutation == "px5_linker" else records[0]
    if mutation == "reactive":
        changed = replace(
            row,
            ligand_reactive_retained_local_index=(
                row.ligand_reactive_retained_local_index + 1
            ) % len(row.ligand_retained_heavy_atoms),
        )
    elif mutation == "sg":
        alternative = next(
            index
            for index in row.target_cys_pocket_local_indices
            if index != row.target_sg_pocket_local_index
        )
        changed = replace(row, target_sg_pocket_local_index=alternative)
    elif mutation == "overlap":
        changed = replace(
            row,
            scaffold_retained_local_indices=(
                *row.scaffold_retained_local_indices,
                row.warhead_retained_local_indices[0],
            ),
        )
    elif mutation == "gap":
        changed = replace(
            row,
            scaffold_retained_local_indices=row.scaffold_retained_local_indices[:-1],
        )
    elif mutation == "px5_linker":
        changed = replace(
            row,
            linker_atom_ids=(row.scaffold_atom_ids[0],),
            linker_retained_local_indices=(row.scaffold_retained_local_indices[0],),
        )
    else:
        changed = replace(row, linker_atom_ids=(), linker_retained_local_indices=())
    with pytest.raises(ValueError):
        structural.validate_covapie_batch001_positive_structural_record_v1(changed)


def test_unsupported_non_h_symbol_fails_closed(records) -> None:
    row = records[0]
    changed_atom = replace(row.ligand_retained_heavy_atoms[0], type_symbol="Se")
    changed = replace(
        row,
        ligand_retained_heavy_atoms=(
            changed_atom,
            *row.ligand_retained_heavy_atoms[1:],
        ),
    )
    with pytest.raises(ValueError, match="FEATURE_PROJECTION_INVALID"):
        structural.validate_covapie_batch001_positive_structural_record_v1(changed)


def test_fabricated_pre_and_admission_promotion_fail_closed(population) -> None:
    geometry = population.supervision.pre_post_geometry_target_angstrom.clone()
    geometry[0, 0] = 3.0
    with pytest.raises(ValueError, match="POST_ONLY_GEOMETRY_CONTRACT_INVALID"):
        subject.validate_covapie_batch001_preview_batch_v1(
            _mutated_batch(population, pre_post_geometry_target_angstrom=geometry)
        )
    admitted = population.supervision.sample_training_admitted.clone()
    admitted[0] = True
    with pytest.raises(ValueError, match="SUPERVISION_SAMPLE_TASK_OR_ROLE_INVALID"):
        subject.validate_covapie_batch001_preview_batch_v1(
            _mutated_batch(population, sample_training_admitted=admitted)
        )


@pytest.mark.parametrize("positive_count", (0, 2))
def test_no_or_multiple_positive_pair_candidates_fail_closed(
    population, positive_count
) -> None:
    positive = population.supervision.pair_candidate_is_positive.clone()
    start = int(population.supervision.pair_candidate_offsets[0])
    if positive_count == 0:
        positive[start:] = positive[start:]  # preserve other samples
        positive[start] = False
        true_index = int(torch.nonzero(
            population.supervision.pair_candidate_is_positive[:
                int(population.supervision.pair_candidate_offsets[1])
            ], as_tuple=False
        )[0, 0])
        positive[true_index] = False
    else:
        false_index = int(torch.nonzero(~positive[:
            int(population.supervision.pair_candidate_offsets[1])
        ], as_tuple=False)[0, 0])
        positive[false_index] = True
    with pytest.raises(ValueError):
        subject.validate_covapie_batch001_preview_batch_v1(
            _mutated_batch(
                population,
                pair_candidate_is_positive=positive,
                pair_candidate_is_negative=~positive,
            )
        )


def test_cross_sample_flat_index_corruption_fails_closed(population) -> None:
    values = population.supervision.pair_candidate_ligand_flat_index.clone()
    values[0] += 23
    with pytest.raises(ValueError, match="CROSS_SAMPLE_FLAT_INDEX"):
        subject.validate_covapie_batch001_preview_batch_v1(
            _mutated_batch(population, pair_candidate_ligand_flat_index=values)
        )


def test_collator_rejects_population_rewrite() -> None:
    identities = list(structural.BATCH001_POSITIVE_EVENT_IDS_V1)
    identities[-1] = identities[0]
    with pytest.raises(ValueError, match="COLLATOR_REQUIRES_EXACT13"):
        subject.collate_covapie_batch001_preview_population_v1(
            epoch=0, task_schedule_seed=0, sample_identities=identities
        )


def test_structural_and_tensor_determinism(records, population) -> None:
    repeated_records = structural.build_covapie_batch001_positive_structural_records_v1()
    assert repeated_records == records
    repeated = subject.collate_covapie_batch001_preview_population_v1(
        epoch=0, task_schedule_seed=0
    )
    assert repeated.sample_identities == population.sample_identities
    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        _assert_tensor_equal(
            getattr(repeated.supervision, field.name),
            getattr(population.supervision, field.name),
        )
    for name, value in population.model_input_batch.items():
        if isinstance(value, torch.Tensor):
            _assert_tensor_equal(value, repeated.model_input_batch[name])
        else:
            assert value == repeated.model_input_batch[name]


def test_artifacts_are_exact_four_deterministic_and_have_no_runtime_metadata() -> None:
    first = subject.build_covapie_batch001_bridge_artifacts_v1()
    second = subject.build_covapie_batch001_bridge_artifacts_v1()
    assert tuple(first) == subject.OUTPUT_FILENAMES_V1
    assert first == second
    assert len(first) == 4
    evidence = json.loads(first[subject.STRUCTURAL_EVIDENCE_V1])
    manifest = json.loads(first[subject.MANIFEST_V1])
    assert evidence["event_count"] == 13
    assert len(evidence["events"]) == 13
    assert manifest["population_counts"]["sample_training_admitted_event_count"] == 0
    assert manifest["population_counts"]["family_target_ready_event_count"] == 0
    assert manifest["architecture_impact"]["supervision_dataclass_reused"] is True
    for payload in first.values():
        text = payload.decode("utf-8")
        assert "timestamp" not in text.lower()
        assert "mtime" not in text.lower()
        assert str(subject._DEFAULT_REPOSITORY_ROOT) not in text
        assert '"runtime_HEAD"' not in text
