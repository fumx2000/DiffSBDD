from __future__ import annotations

import ast
import importlib.util
import os
import sys
from collections import Counter, defaultdict
from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from covalent_ext import (
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as batch001_owner,
)
from covalent_ext import covapie_current11_legacy_train5_data_adapter_v1 as legacy_owner
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


def _load_subject():
    candidate = os.environ.get("COVAPIE_TRAIN10_COMPOSER_CANDIDATE")
    if candidate is None:
        from covalent_ext import covapie_train10_cpu_batch_composer_v1 as installed

        return installed
    path = Path(candidate)
    specification = importlib.util.spec_from_file_location(
        "covapie_train10_cpu_batch_composer_v1_candidate", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


subject = _load_subject()
ERROR = subject.TRAIN10_CPU_BATCH_COMPOSER_ERROR_V1


@pytest.fixture(scope="session")
def repository_root() -> Path:
    configured = os.environ.get("COVAPIE_TEST_REPOSITORY_ROOT")
    assert configured is not None
    return Path(configured).resolve(strict=True)


@pytest.fixture(scope="session")
def state_root() -> Path:
    configured = os.environ.get("COVAPIE_TEST_STATE_ROOT")
    assert configured is not None
    return Path(configured).resolve(strict=True)


@pytest.fixture(scope="session")
def cache_root() -> Path:
    configured = os.environ.get("COVAPIE_TEST_CACHE_ROOT")
    assert configured is not None
    return Path(configured).resolve(strict=True)


@pytest.fixture(scope="session")
def prepared(repository_root: Path, state_root: Path, cache_root: Path):
    return subject.prepare_covapie_train10_cpu_batch_composer_v1(
        repository_root, state_root, cache_root
    )


@pytest.fixture(scope="session")
def epoch0_4(prepared):
    return tuple(
        subject.build_covapie_train10_cpu_epoch_batch_v1(prepared, epoch, 0)
        for epoch in range(5)
    )


def _assert_public_failure(call) -> None:
    with pytest.raises(ValueError) as error:
        call()
    assert str(error.value).startswith(ERROR)


def _assert_tensor_exact(left: torch.Tensor, right: torch.Tensor) -> None:
    assert left.dtype == right.dtype
    assert left.shape == right.shape
    assert left.device == right.device
    torch.testing.assert_close(left, right, rtol=0, atol=0, equal_nan=True)


def _assert_supervision_exact(left, right) -> None:
    assert type(left) is type(right) is CovapieCurrent11TrainingSupervisionTensorsV1
    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        _assert_tensor_exact(getattr(left, field.name), getattr(right, field.name))


def _assert_batch_payload_exact(left, right) -> None:
    assert left.sample_identities == right.sample_identities
    assert left.canonical_event_ids == right.canonical_event_ids
    assert left.source_branches == right.source_branches
    assert left.formal_splits == right.formal_splits
    assert left.leakage_group_ids == right.leakage_group_ids
    assert left.scheduled_task_ids == right.scheduled_task_ids
    assert set(left.model_input_batch) == set(right.model_input_batch)
    for name, left_value in left.model_input_batch.items():
        right_value = right.model_input_batch[name]
        if isinstance(left_value, torch.Tensor):
            _assert_tensor_exact(left_value, right_value)
        else:
            assert left_value == right_value
    _assert_supervision_exact(left.supervision, right.supervision)


def test_public_surface_is_data_only_and_exact5_contract_is_canonical() -> None:
    assert subject.__all__ == (
        "TRAIN10_CPU_BATCH_COMPOSER_ERROR_V1",
        "TRAIN10_SAMPLE_IDENTITIES_V1",
        "TRAIN10_CANONICAL_EVENT_IDS_V1",
        "CovapieTrain10SourceBindingV1",
        "CovapieTrain10SourceBlockAuditV1",
        "CovapieTrain10CpuBatchPreparedV1",
        "CovapieTrain10CpuEpochBatchV1",
        "prepare_covapie_train10_cpu_batch_composer_v1",
        "build_covapie_train10_cpu_epoch_batch_v1",
        "validate_covapie_train10_cpu_epoch_batch_v1",
    )
    assert tuple(CANONICAL_TASKS_V1) == (
        (0, "warhead_only", "A", (2,)),
        (1, "linker_plus_warhead", "B", (1, 2)),
        (2, "scaffold_plus_warhead", "B2", (0, 2)),
        (3, "scaffold_only", "B3", (0,)),
        (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
    )
    tree = ast.parse(Path(subject.__file__).read_text(encoding="utf-8"))
    forbidden_modules = {
        "equivariant_diffusion",
        "lightning_modules",
        "pytorch_lightning",
    }
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    called = {
        node.func.id.lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not forbidden_modules & imported
    assert not {"trainer", "optimizer", "forward", "backward", "fit", "step"} & called
    assert "collate_covapie_expanded_cys_sg_exact16_tensorized_samples_v1" not in Path(
        subject.__file__
    ).read_text(encoding="utf-8")


def test_real_prepare_binds_exact_population_groups_and_owner_chains(prepared) -> None:
    expected_batch = (
        "COVAPIE_CYS_SG_EVENT_V1:3LOK:A:CYS:345-:SG:C:DJK:C51",
        "COVAPIE_CYS_SG_EVENT_V1:3LOK:B:CYS:345-:SG:D:DJK:C51",
        "COVAPIE_CYS_SG_EVENT_V1:2ZK1:A:CYS:285-:SG:C:PTG:C8",
        "COVAPIE_CYS_SG_EVENT_V1:2ZK1:B:CYS:285-:SG:D:PTG:C8",
        "COVAPIE_CYS_SG_EVENT_V1:2ZK2:A:CYS:285-:SG:D:PTG:C8",
    )
    expected_legacy_samples = tuple(
        f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(6, 11)
    )
    expected_legacy_events = (
        "COVAPIE_CYS_SG_EVENT_V1:1AU3:A:CYS:25-:SG:B:PCM:C22",
        "COVAPIE_CYS_SG_EVENT_V1:1AU4:A:CYS:25-:SG:B:INP:C17",
        "COVAPIE_CYS_SG_EVENT_V1:1AYU:A:CYS:25-:SG:B:INA:C21",
        "COVAPIE_CYS_SG_EVENT_V1:1AYV:A:CYS:25-:SG:B:IN6:C21",
        "COVAPIE_CYS_SG_EVENT_V1:1AYW:A:CYS:25-:SG:B:IN3:C21",
    )
    assert type(prepared) is subject.CovapieTrain10CpuBatchPreparedV1
    assert prepared.schema_version == "covapie_train10_cpu_batch_composer_prepared_v1"
    assert prepared.sample_identities == expected_batch + expected_legacy_samples
    assert prepared.canonical_event_ids == expected_batch + expected_legacy_events
    assert prepared.formal_splits == ("train",) * 10
    assert prepared.source_branches == (
        ("BATCH001_FORMAL_TRAIN5_V1",) * 5
        + ("CURRENT11_LEGACY_TRAIN5_V1",) * 5
    )
    assert prepared.verified_distinct_leakage_group_count == 3
    assert len(prepared.source_bindings) == 4
    assert all(binding.git_head_equal for binding in prepared.source_bindings)
    assert prepared._batch001_authority.formal_leakage_group_cross_split_violation_count == 0
    assert prepared._batch001_authority.event_identity_intersection_counts == (
        ("train_validation", 0),
        ("train_test", 0),
        ("validation_test", 0),
    )
    assert len(prepared._legacy_prepared.source_bindings) == 27
    assert prepared.training_session_active is False
    assert prepared.ready_for_training is False
    assert prepared.feature_semantics_audit_required_later is True
    assert prepared.step12d_is_only_smoke_legality_check is True


def test_real_epoch0_4_are_exact_train10_and_temporal_exact5(epoch0_4) -> None:
    assert len(epoch0_4) == 5
    event_tasks: dict[str, list[int]] = defaultdict(list)
    task_counts: Counter[int] = Counter()
    for epoch, batch in enumerate(epoch0_4):
        assert type(batch) is subject.CovapieTrain10CpuEpochBatchV1
        assert batch.epoch == epoch
        assert batch.task_schedule_seed == 0
        assert batch.sample_identities == subject.TRAIN10_SAMPLE_IDENTITIES_V1
        assert batch.canonical_event_ids == subject.TRAIN10_CANONICAL_EVENT_IDS_V1
        assert subject.validate_covapie_train10_cpu_epoch_batch_v1(batch)
        for event_id, task_id in zip(batch.canonical_event_ids, batch.scheduled_task_ids):
            event_tasks[event_id].append(task_id)
            task_counts[task_id] += 1
    assert sum(len(values) for values in event_tasks.values()) == 50
    assert set(event_tasks) == set(subject.TRAIN10_CANONICAL_EVENT_IDS_V1)
    assert all(set(values) == set(range(5)) for values in event_tasks.values())
    assert task_counts == Counter({0: 10, 1: 10, 2: 10, 3: 10, 4: 10})
    assert task_counts[3] == 10


def test_real_node_membership_offsets_and_all_index_spaces(epoch0_4) -> None:
    for batch in epoch0_4:
        model = batch.model_input_batch
        supervision = batch.supervision
        lig_counts = model["num_lig_atoms"]
        pocket_counts = model["num_pocket_nodes"]
        assert lig_counts.shape == pocket_counts.shape == (10,)
        assert int(lig_counts.sum()) == len(model["lig_coords"])
        assert int(pocket_counts.sum()) == len(model["pocket_coords"])
        assert torch.equal(torch.bincount(model["lig_mask"], minlength=10), lig_counts)
        assert torch.equal(
            torch.bincount(model["pocket_mask"], minlength=10), pocket_counts
        )
        offsets = supervision.pair_candidate_offsets
        assert offsets.shape == (11,)
        assert offsets[0].item() == 0
        assert bool((offsets[1:] > offsets[:-1]).all())
        assert offsets[-1].item() == len(supervision.pair_candidate_batch_index)
        assert torch.equal(
            model["lig_mask"][supervision.pair_candidate_ligand_flat_index],
            supervision.pair_candidate_batch_index,
        )
        assert torch.equal(
            model["pocket_mask"][supervision.pair_candidate_pocket_flat_index],
            supervision.pair_candidate_batch_index,
        )
        lig_offsets = torch.cat((torch.zeros(1, dtype=torch.long), lig_counts.cumsum(0)))
        pocket_offsets = torch.cat(
            (torch.zeros(1, dtype=torch.long), pocket_counts.cumsum(0))
        )
        for sample in range(10):
            start, end = int(offsets[sample]), int(offsets[sample + 1])
            segment = slice(start, end)
            assert supervision.pair_candidate_batch_index[segment].tolist() == [sample] * (
                end - start
            )
            assert torch.equal(
                supervision.pair_candidate_ligand_flat_index[segment]
                - lig_offsets[sample],
                supervision.pair_candidate_ligand_local_index[segment],
            )
            assert torch.equal(
                supervision.pair_candidate_pocket_flat_index[segment]
                - pocket_offsets[sample],
                supervision.pair_candidate_residue_local_index[segment],
            )
            target = int(supervision.target_residue_reactive_atom_flat_index[sample])
            assert target == int(pocket_offsets[sample]) + int(
                supervision.target_residue_reactive_atom_local_index[sample]
            )
            positive = int(supervision.pair_positive_candidate_index[sample])
            assert start <= positive < end
            assert bool(supervision.pair_candidate_is_positive[positive])
            assert int(supervision.pair_candidate_pocket_flat_index[positive]) == target


def test_source_blocks_round_trip_exact_and_sidecars_are_audit_only(epoch0_4) -> None:
    batch = epoch0_4[0]
    assert len(batch.source_audit_blocks) == 6
    assert set(batch.model_input_batch) == set(subject._MODEL_CORE_FIELDS_V1)
    assert not set(batch.model_input_batch) & set(subject._LEGACY_AUDIT_ONLY_FIELDS_V1)
    first, *legacy = batch.source_audit_blocks
    assert first.sample_start == 0 and first.sample_end == 5
    assert set(first.model_input_batch) == set(subject._MODEL_CORE_FIELDS_V1)
    for offset, block in enumerate(legacy, 5):
        assert block.sample_start == offset and block.sample_end == offset + 1
        assert set(block.model_input_batch) == (
            set(subject._MODEL_CORE_FIELDS_V1)
            | set(subject._LEGACY_AUDIT_ONLY_FIELDS_V1)
        )
        assert all(
            type(block.model_input_batch[name]) is dict
            for name in subject._LEGACY_AUDIT_ONLY_FIELDS_V1
        )
    subject._validate_source_roundtrip_v1(batch)


def test_pre_post_validity_observed_distance_and_loss_masks_are_source_preserved(
    epoch0_4,
) -> None:
    for batch in epoch0_4:
        supervision = batch.supervision
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
        assert torch.isnan(supervision.pre_post_geometry_target_angstrom[:, 0]).all()
        assert torch.isfinite(supervision.pre_post_geometry_target_angstrom[:5, 1]).all()
        assert torch.isnan(supervision.pre_post_geometry_target_angstrom[5:, 1]).all()
        assert supervision.observed_complex_pair_distance_valid.tolist() == [[True]] * 10
        assert torch.isfinite(supervision.observed_complex_pair_distance_angstrom).all()
        assert supervision.sample_training_admitted.tolist() == [True] * 10
        assert supervision.pair_contrastive_sample_loss_mask.tolist() == [True] * 10
        assert batch.legacy_post_overlay_applied is False


def test_b3_generation_fixed_post_and_task_c_seed_are_not_normalized(epoch0_4) -> None:
    task_rows = [
        (batch, sample, task)
        for batch in epoch0_4
        for sample, task in enumerate(batch.scheduled_task_ids)
    ]
    for batch, sample, task in task_rows:
        model = batch.model_input_batch
        supervision = batch.supervision
        indices = model["lig_mask"] == sample
        roles = supervision.ligand_role_id[indices]
        generation = supervision.ligand_base_generation_mask[indices, 0]
        expected_roles = set(CANONICAL_TASKS_V1[task][3])
        assert torch.equal(
            generation,
            torch.tensor([int(role) in expected_roles for role in roles]),
        )
        if task == 3:
            assert expected_roles == {0}
            assert bool(generation.any())
            assert bool((~generation).any())
        seed_count = int(supervision.ligand_minimal_seed_or_anchor_mask[indices].sum())
        seed_valid = bool(supervision.ligand_minimal_seed_or_anchor_valid[sample])
        if sample < 5:
            # Batch001's published preview owner has no minimal-seed authority,
            # including for C.  The composer must not synthesize one.
            assert not seed_valid and seed_count == 0
        elif task == 4:
            # The legacy Current11 owner does provide its task-C seed.
            assert seed_valid and seed_count > 0
        else:
            assert not seed_valid and seed_count == 0


def test_determinism_and_return_mutation_isolation(prepared, epoch0_4) -> None:
    repeated = subject.build_covapie_train10_cpu_epoch_batch_v1(prepared, 3, 0)
    _assert_batch_payload_exact(epoch0_4[3], repeated)
    mutable = subject.build_covapie_train10_cpu_epoch_batch_v1(prepared, 1, 0)
    baseline_coordinate = epoch0_4[1].model_input_batch["lig_coords"][0, 0].item()
    mutable.model_input_batch["lig_coords"][0, 0] += 1000
    mutable.supervision.ligand_role_id[0] = -1
    mutable.source_audit_blocks[1].model_input_batch["lig_coords"][0, 0] += 2000
    _assert_public_failure(
        lambda: subject.validate_covapie_train10_cpu_epoch_batch_v1(mutable)
    )
    rebuilt = subject.build_covapie_train10_cpu_epoch_batch_v1(prepared, 1, 0)
    assert rebuilt.model_input_batch["lig_coords"][0, 0].item() == baseline_coordinate
    _assert_batch_payload_exact(epoch0_4[1], rebuilt)


@pytest.mark.parametrize(
    "field,replacement",
    (
        ("_sample_identities", subject.TRAIN10_SAMPLE_IDENTITIES_V1[:-1] + (subject.TRAIN10_SAMPLE_IDENTITIES_V1[0],)),
        ("_formal_splits", ("validation",) + ("train",) * 9),
        ("_source_branches", ("WRONG_SOURCE",) + subject._SOURCE_BRANCHES_V1[1:]),
        ("_leakage_group_ids", ("FORGED_GROUP",) + ("COVAPIE_LEAKAGE_GROUP_000004",) * 9),
    ),
)
def test_prepared_population_split_source_and_group_tampering_fail_closed(
    prepared, field, replacement
) -> None:
    original = getattr(prepared, field)
    object.__setattr__(prepared, field, replacement)
    try:
        _assert_public_failure(
            lambda: subject.build_covapie_train10_cpu_epoch_batch_v1(prepared, 0, 0)
        )
    finally:
        object.__setattr__(prepared, field, original)


@pytest.mark.parametrize(
    "changes",
    (
        {"sample_identities": subject.TRAIN10_SAMPLE_IDENTITIES_V1[:-1] + (subject.TRAIN10_SAMPLE_IDENTITIES_V1[0],)},
        {"sample_identities": subject.TRAIN10_SAMPLE_IDENTITIES_V1[:-1] + (batch001_owner.FORMAL_VALIDATION_EVENT_IDS_V1[0],)},
        {"source_branches": ("CURRENT11_LEGACY_TRAIN5_V1",) + subject._SOURCE_BRANCHES_V1[1:]},
        {"formal_splits": ("test",) + ("train",) * 9},
    ),
)
def test_duplicate_non_target_holdout_and_wrong_source_batch_metadata_rejected(
    epoch0_4, changes
) -> None:
    _assert_public_failure(
        lambda: subject.validate_covapie_train10_cpu_epoch_batch_v1(
            replace(epoch0_4[0], **changes)
        )
    )


def test_owner_batch_population_tampering_is_rejected(
    prepared, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_builder = subject._batch001_owner.build_covapie_batch001_model_usable_split_batch_v1

    def forged_builder(**arguments):
        built = real_builder(**arguments)
        return replace(
            built,
            sample_identities=built.sample_identities[:-1] + (built.sample_identities[0],),
        )

    monkeypatch.setattr(
        subject._batch001_owner,
        "build_covapie_batch001_model_usable_split_batch_v1",
        forged_builder,
    )
    _assert_public_failure(
        lambda: subject.build_covapie_train10_cpu_epoch_batch_v1(prepared, 0, 0)
    )


def _synthetic_core_block(
    prefix: str,
    ligand_counts: tuple[int, ...],
    pocket_counts: tuple[int, ...],
    candidate_counts: tuple[int, ...],
):
    batch_size = len(ligand_counts)
    assert len(pocket_counts) == len(candidate_counts) == batch_size
    ligand_total, pocket_total = sum(ligand_counts), sum(pocket_counts)
    ligand_offsets = [0]
    pocket_offsets = [0]
    candidate_offsets = [0]
    for ligand, pocket, candidate in zip(ligand_counts, pocket_counts, candidate_counts):
        ligand_offsets.append(ligand_offsets[-1] + ligand)
        pocket_offsets.append(pocket_offsets[-1] + pocket)
        candidate_offsets.append(candidate_offsets[-1] + candidate)
    model = {
        "names": [f"{prefix}_{index}" for index in range(batch_size)],
        "receptors": [f"R_{prefix}_{index}" for index in range(batch_size)],
        "lig_coords": torch.arange(ligand_total * 3, dtype=torch.float32).reshape(-1, 3),
        "pocket_coords": torch.arange(pocket_total * 3, dtype=torch.float32).reshape(-1, 3),
        "lig_one_hot": torch.nn.functional.one_hot(torch.zeros(ligand_total, dtype=torch.long), 10).float(),
        "pocket_one_hot": torch.nn.functional.one_hot(torch.zeros(pocket_total, dtype=torch.long), 10).float(),
        "lig_source_row_index": torch.arange(ligand_total),
        "pocket_source_row_index": torch.arange(pocket_total),
        "lig_parser_local_index": torch.cat([torch.arange(value) for value in ligand_counts]),
        "pocket_parser_local_index": torch.cat([torch.arange(value) for value in pocket_counts]),
        "num_lig_atoms": torch.tensor(ligand_counts, dtype=torch.long),
        "num_pocket_nodes": torch.tensor(pocket_counts, dtype=torch.long),
        "lig_mask": torch.repeat_interleave(torch.arange(batch_size), torch.tensor(ligand_counts)),
        "pocket_mask": torch.repeat_interleave(torch.arange(batch_size), torch.tensor(pocket_counts)),
    }
    pair_batch = []
    ligand_local = []
    pocket_local = []
    positive = []
    positive_indices = []
    target_local = []
    target_flat = []
    target_reactive = torch.zeros(pocket_total, 1, dtype=torch.bool)
    for sample, (ligand_count, pocket_count, candidate_count) in enumerate(
        zip(ligand_counts, pocket_counts, candidate_counts)
    ):
        target = min(1, pocket_count - 1)
        target_local.append(target)
        target_flat.append(pocket_offsets[sample] + target)
        target_reactive[pocket_offsets[sample] + target] = True
        positive_indices.append(candidate_offsets[sample])
        for candidate in range(candidate_count):
            pair_batch.append(sample)
            ligand_local.append(candidate % ligand_count)
            pocket_local.append(target if candidate == 0 else candidate % pocket_count)
            positive.append(candidate == 0)
    pair_batch_tensor = torch.tensor(pair_batch, dtype=torch.long)
    ligand_local_tensor = torch.tensor(ligand_local, dtype=torch.long)
    pocket_local_tensor = torch.tensor(pocket_local, dtype=torch.long)
    positive_tensor = torch.tensor(positive, dtype=torch.bool)
    roles = torch.arange(ligand_total, dtype=torch.long) % 3
    generation = (roles == 2).unsqueeze(1)
    values = {
        "sample_training_admitted": torch.ones(batch_size, dtype=torch.bool),
        "canonical_task_id": torch.zeros(batch_size, dtype=torch.long),
        "canonical_task_valid": torch.ones(batch_size, dtype=torch.bool),
        "ligand_role_id": roles,
        "ligand_role_valid": torch.ones(ligand_total, dtype=torch.bool),
        "ligand_base_generation_mask": generation,
        "ligand_base_fixed_mask": ~generation,
        "ligand_base_target_mask": generation.clone(),
        "ligand_base_context_mask": (~generation).clone(),
        "ligand_active_diffusion_loss_mask": generation.clone(),
        "ligand_minimal_seed_or_anchor_mask": torch.zeros(ligand_total, 1, dtype=torch.bool),
        "ligand_minimal_seed_or_anchor_valid": torch.zeros(batch_size, dtype=torch.bool),
        "ligand_anchor_distance_angstrom": torch.zeros(ligand_total, 1),
        "ligand_anchor_distance_valid": torch.ones(ligand_total, 1, dtype=torch.bool),
        "target_residue_membership_mask": torch.ones(pocket_total, 1, dtype=torch.bool),
        "target_residue_reactive_atom_mask": target_reactive,
        "target_residue_reactive_atom_local_index": torch.tensor(target_local),
        "target_residue_reactive_atom_flat_index": torch.tensor(target_flat),
        "target_residue_condition_valid": torch.ones(batch_size, dtype=torch.bool),
        "pair_candidate_offsets": torch.tensor(candidate_offsets),
        "pair_candidate_batch_index": pair_batch_tensor,
        "pair_candidate_ligand_local_index": ligand_local_tensor,
        "pair_candidate_residue_local_index": pocket_local_tensor,
        "pair_candidate_ligand_flat_index": ligand_local_tensor
        + torch.tensor([ligand_offsets[index] for index in pair_batch]),
        "pair_candidate_pocket_flat_index": pocket_local_tensor
        + torch.tensor([pocket_offsets[index] for index in pair_batch]),
        "pair_candidate_is_positive": positive_tensor,
        "pair_candidate_is_negative": ~positive_tensor,
        "pair_positive_candidate_index": torch.tensor(positive_indices),
        "pair_positive_candidate_valid": torch.ones(batch_size, dtype=torch.bool),
        "pair_negative_count": torch.tensor([value - 1 for value in candidate_counts]),
        "pair_head_candidate_loss_mask": torch.ones(sum(candidate_counts), dtype=torch.bool),
        "pair_contrastive_sample_loss_mask": torch.ones(batch_size, dtype=torch.bool),
        "observed_complex_pair_distance_angstrom": torch.ones(batch_size, 1),
        "observed_complex_pair_distance_valid": torch.ones(batch_size, 1, dtype=torch.bool),
        "pre_post_geometry_target_angstrom": torch.full((batch_size, 2), float("nan")),
        "pre_post_geometry_component_valid_mask": torch.zeros(batch_size, 2, dtype=torch.bool),
        "pre_post_geometry_component_loss_mask": torch.zeros(batch_size, 2, dtype=torch.bool),
    }
    return model, CovapieCurrent11TrainingSupervisionTensorsV1(**values)


def test_asymmetric_synthetic_blocks_use_independent_s_l_p_q_offsets() -> None:
    first = _synthetic_core_block("left", (2, 4), (5, 3), (3, 5))
    second = _synthetic_core_block("right", (3,), (7,), (4,))
    model, supervision = subject._collate_core_blocks_v1((first, second))
    subject._validate_collated_domains_v1(model, supervision)
    assert model["num_lig_atoms"].tolist() == [2, 4, 3]
    assert model["num_pocket_nodes"].tolist() == [5, 3, 7]
    assert supervision.pair_candidate_offsets.tolist() == [0, 3, 8, 12]
    assert supervision.pair_candidate_batch_index.tolist() == [0] * 3 + [1] * 5 + [2] * 4
    assert supervision.pair_candidate_ligand_flat_index[8:].min().item() >= 6
    assert supervision.pair_candidate_pocket_flat_index[8:].min().item() >= 8
    assert supervision.pair_positive_candidate_index.tolist() == [0, 3, 8]


@pytest.mark.parametrize(
    "mutation",
    ("ligand_flat", "pocket_flat", "target_flat", "positive_index", "offsets", "local_index"),
)
def test_synthetic_cross_sample_and_wrong_offset_corruptions_fail_closed(mutation) -> None:
    first = _synthetic_core_block("left", (2, 4), (5, 3), (3, 5))
    second = _synthetic_core_block("right", (3,), (7,), (4,))
    model, supervision = subject._collate_core_blocks_v1((first, second))
    values = {
        field.name: getattr(supervision, field.name).clone()
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    }
    if mutation == "ligand_flat":
        values["pair_candidate_ligand_flat_index"][0] = 2
    elif mutation == "pocket_flat":
        values["pair_candidate_pocket_flat_index"][0] = 5
    elif mutation == "target_flat":
        values["target_residue_reactive_atom_flat_index"][1] = 1
    elif mutation == "positive_index":
        values["pair_positive_candidate_index"][0] = 3
    elif mutation == "offsets":
        values["pair_candidate_offsets"][1] = 4
    elif mutation == "local_index":
        values["pair_candidate_ligand_local_index"][0] = 2
    corrupted = CovapieCurrent11TrainingSupervisionTensorsV1(**values)
    with pytest.raises(subject._ComposerInvariantError):
        subject._validate_collated_domains_v1(model, corrupted)


def test_invalid_index_sentinel_is_preserved_and_never_offset_to_valid() -> None:
    value = torch.tensor([2, -1], dtype=torch.long)
    valid = torch.tensor([True, False], dtype=torch.bool)
    assert subject._offset_valid_indices_v1(
        value, offset=11, valid=valid
    ).tolist() == [13, -1]
    with pytest.raises(subject._ComposerInvariantError):
        subject._offset_valid_indices_v1(
            torch.tensor([2, 0], dtype=torch.long), offset=11, valid=valid
        )


def test_unknown_source_model_sidecar_is_not_silently_filtered(epoch0_4) -> None:
    legacy_model = dict(epoch0_4[0].source_audit_blocks[1].model_input_batch)
    legacy_model["future_unknown_sidecar"] = {"status": "forged"}
    with pytest.raises(subject._ComposerInvariantError):
        subject._core_model_input_v1(
            legacy_model, source_branch=subject._LEGACY_BRANCH_V1
        )


def test_supervision_field_domain_contract_rejects_unknown_future_field(
    monkeypatch: pytest.MonkeyPatch,
    repository_root: Path,
    state_root: Path,
    cache_root: Path,
) -> None:
    real_fields = subject.fields

    def future_fields(value):
        result = real_fields(value)
        if value is CovapieCurrent11TrainingSupervisionTensorsV1:
            return result + (SimpleNamespace(name="future_unknown_field"),)
        return result

    monkeypatch.setattr(subject, "fields", future_fields)
    _assert_public_failure(
        lambda: subject.prepare_covapie_train10_cpu_batch_composer_v1(
            repository_root, state_root, cache_root
        )
    )


@pytest.mark.parametrize(
    "epoch,seed",
    ((True, 0), (-1, 0), (0.0, 0), (0, True), (0, -1), (0, 2**63), (0, 0.0)),
)
def test_epoch_and_seed_validation_fail_closed(prepared, epoch, seed) -> None:
    _assert_public_failure(
        lambda: subject.build_covapie_train10_cpu_epoch_batch_v1(prepared, epoch, seed)
    )


def test_cli_is_cpu_build_only_and_reports_no_execution(
    capsys: pytest.CaptureFixture[str],
    repository_root: Path,
    state_root: Path,
    cache_root: Path,
) -> None:
    assert subject.main([
        "--repository-root", str(repository_root),
        "--state-root", str(state_root),
        "--cache-root", str(cache_root),
        "--epoch", "2",
        "--task-schedule-seed", "7",
    ]) == 0
    output = capsys.readouterr().out.strip()
    assert "BUILD_STATUS=PASS" in output
    assert "EPOCH=2" in output
    assert "TASK_SCHEDULE_SEED=7" in output
    assert "TARGET_EVENT_COUNT=10" in output
    assert "DISTINCT_LEAKAGE_GROUP_COUNT=3" in output
    assert "MODEL_CONSUMER_INTEGRATED=false" in output
    assert "TRAINER_INTEGRATED=false" in output
    assert "REAL_MODEL_EXECUTED=false" in output
    assert "TRAINING_OR_VALIDATION_EXECUTED=false" in output
    assert "PARAMETER_UPDATE_PERFORMED=false" in output
    assert "READY_FOR_TRAINING=false" in output
    assert "tensor(" not in output and "[[" not in output
