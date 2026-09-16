"""Scoped, data-only Exact2 candidate verification; no model execution."""

from __future__ import annotations

import copy
from collections import Counter
from dataclasses import fields, replace
import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
import torch


COUNTS = {"train10_prepare": 0, "ready2_prepare": 0,
          "train10_build": 0, "ready2_build": 0,
          "primary_epoch_batches": 0, "primary_event_epoch": 0,
          "reference_builds_explicit": 0}


def _roots():
    return (Path(os.environ["COVAPIE_TEST_REPOSITORY_ROOT"]),
            Path(os.environ["COVAPIE_TEST_STATE_ROOT"]),
            Path(os.environ["COVAPIE_TEST_CACHE_ROOT"]))


def _production():
    candidate = os.environ.get("COVAPIE_TRAIN12_TEST_PRODUCTION_PATH")
    if candidate:
        path = Path(candidate)
        assert path.is_absolute() and path.name == "covapie_train12_cpu_batch_composer_v1.py"
        spec = importlib.util.spec_from_file_location(
            "covapie_train12_cpu_batch_composer_v1_external_candidate", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module("covalent_ext.covapie_train12_cpu_batch_composer_v1")


@pytest.fixture(scope="session")
def subject():
    return _production()


@pytest.fixture(scope="session")
def session_data(subject):
    """Owner prepares once each; main 60 rows come from five real epochs."""
    first, second = subject.train10, subject.ready2
    owner_first, owner_second = first.prepare_covapie_train10_cpu_batch_composer_v1, second.prepare_covapie_jug_gjj_ready2_data_adapter_v1
    build_first, build_second = first.build_covapie_train10_cpu_epoch_batch_v1, second.build_covapie_jug_gjj_ready2_canonical_task_data_v1

    def counted_first(*args, **kwargs):
        COUNTS["train10_prepare"] += 1
        return owner_first(*args, **kwargs)

    def counted_second(*args, **kwargs):
        COUNTS["ready2_prepare"] += 1
        return owner_second(*args, **kwargs)

    def counted_build_first(*args, **kwargs):
        COUNTS["train10_build"] += 1
        return build_first(*args, **kwargs)

    def counted_build_second(*args, **kwargs):
        COUNTS["ready2_build"] += 1
        return build_second(*args, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(first, "prepare_covapie_train10_cpu_batch_composer_v1", counted_first)
        patch.setattr(second, "prepare_covapie_jug_gjj_ready2_data_adapter_v1", counted_second)
        patch.setattr(first, "build_covapie_train10_cpu_epoch_batch_v1", counted_build_first)
        patch.setattr(second, "build_covapie_jug_gjj_ready2_canonical_task_data_v1", counted_build_second)
        prepared = subject.prepare_covapie_train12_cpu_batch_composer_v1(*_roots())
        batches = tuple(subject.build_covapie_train12_cpu_epoch_batch_v1(prepared, epoch, 0)
                        for epoch in range(5))
        COUNTS["primary_epoch_batches"] = len(batches)
        COUNTS["primary_event_epoch"] = sum(len(batch.sample_identities) for batch in batches)
        yield prepared, batches
    print("TRAIN12_SESSION_ACTUAL_COUNTS=" + str(COUNTS))


def _same(left, right):
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        assert left.device == right.device and left.dtype == right.dtype and left.shape == right.shape
        torch.testing.assert_close(left, right, rtol=0, atol=0, equal_nan=True)
    elif type(left) is dict and type(right) is dict:
        assert left.keys() == right.keys()
        for name in left:
            _same(left[name], right[name])
    elif type(left) in (tuple, list) and type(left) is type(right):
        assert len(left) == len(right)
        for a, b in zip(left, right):
            _same(a, b)
    elif type(left) is type(right) and hasattr(left, "__dataclass_fields__"):
        for field in fields(left):
            _same(getattr(left, field.name), getattr(right, field.name))
    else:
        assert left == right


def _failure(subject, call, reason):
    with pytest.raises(ValueError, match=subject.TRAIN12_CPU_BATCH_COMPOSER_ERROR_V1) as caught:
        call()
    assert reason in str(caught.value)


def _reseal(subject, batch):
    return replace(batch, payload_sha256=subject._batch_seal(batch))


def _reblock(subject, batch, ordinal, **changes):
    blocks = list(copy.deepcopy(batch.source_audit_blocks))
    blocks[ordinal] = replace(blocks[ordinal], **changes)
    blocks[ordinal] = replace(blocks[ordinal], payload_sha256=subject._block_seal(blocks[ordinal]))
    return _reseal(subject, replace(batch, source_audit_blocks=tuple(blocks)))


def test_candidate_identity_source_pins_and_no_side_effects(subject):
    repo, _, _ = _roots()
    assert subject.__all__[-3:] == (
        "prepare_covapie_train12_cpu_batch_composer_v1",
        "build_covapie_train12_cpu_epoch_batch_v1",
        "validate_covapie_train12_cpu_epoch_batch_v1",
    )
    assert subject._verify_direct_helpers(repo) == subject._SOURCE_SPECS
    for name, length, expected in subject._SOURCE_SPECS:
        payload = (repo / name).read_bytes()
        assert len(payload) == length and hashlib.sha256(payload).hexdigest() == expected
    assert tuple(subject.CANONICAL_TASKS_V1) == subject._EXPECTED_TASKS
    assert subject._EXPECTED_TASKS[3][1] == "scaffold_only"
    assert len(subject.train10._SUPERVISION_FIELD_DOMAINS_V1) == 5
    assert sum(len(names) for names in subject.train10._SUPERVISION_FIELD_DOMAINS_V1.values()) == 37


def test_once_prepared_exact12_five_formal_groups_and_owner_scope(session_data, subject):
    prepared, batches = session_data
    assert (COUNTS["train10_prepare"], COUNTS["ready2_prepare"]) == (1, 1)
    assert (COUNTS["primary_epoch_batches"], COUNTS["primary_event_epoch"]) == (5, 60)
    assert prepared.schema_version == "covapie_train12_cpu_batch_composer_prepared_v1"
    assert prepared.sample_identities == subject.TRAIN12_SAMPLE_IDENTITIES_V1
    assert prepared.canonical_event_ids == subject.TRAIN12_CANONICAL_EVENT_IDS_V1
    assert prepared.verified_distinct_leakage_group_count == 5
    assert prepared.leakage_group_ids[10:] == tuple(row[2] for row in subject.ready2.TARGETS_V1)
    assert len(set(prepared.leakage_group_ids[:10])) == 3
    assert subject._formal_groups(prepared._train10, prepared._ready2) == prepared.leakage_group_ids
    assert prepared._ready2.upstream_construction_scope == {
        "current11_runtime_samples": 11, "positive_closure_runtime_samples": 7,
        "positive_closure_task_checks": 35, "positive_closure_default_task_builds": 7,
        "returned_target_events": 2,
    }
    assert not prepared.ready_for_training
    assert prepared.feature_semantics_audit_required_later
    assert prepared.step12d_is_only_smoke_legality_check
    assert len(batches) == 5


def test_real_sixty_event_epoch_five_tasks_and_native_gjj_schedule(session_data, subject):
    prepared, batches = session_data
    coverage = {event: [] for event in subject.TRAIN12_CANONICAL_EVENT_IDS_V1}
    for epoch, batch in enumerate(batches):
        assert subject.validate_covapie_train12_cpu_epoch_batch_v1(batch, prepared)
        assert batch.epoch == epoch and batch.task_schedule_seed == 0
        assert len(batch.sample_identities) == len(batch.canonical_event_ids) == 12
        assert batch.leakage_group_ids == prepared.leakage_group_ids
        assert len(set(batch.leakage_group_ids)) == 5
        assert set(batch.model_input_batch) == set(subject.train10._MODEL_CORE_FIELDS_V1)
        assert len(batch.source_audit_blocks) == 3
        assert batch.source_audit_blocks[0].source_object.scheduled_task_ids == batch.scheduled_task_ids[:10]
        for event, task in zip(batch.canonical_event_ids, batch.scheduled_task_ids):
            coverage[event].append(task)
        for ordinal in (1, 2):
            block = batch.source_audit_blocks[ordinal]
            binding = block.scheduler_binding
            assert binding.canonical_task_id == block.scheduled_task_ids[0]
            assert binding.identity_key == block.sample_identities[0]
            assert binding.canonical_event_id == block.canonical_event_ids[0]
            assert binding.valid_task_ids == tuple(range(5))
            assert block.source_object.native_owner == block.native_owner
            assert block.source_object.canonical_task_name == subject._EXPECTED_TASKS[binding.canonical_task_id][1]
            assert block.source_object.sample_identity == binding.identity_key
            assert block.native_source_bindings == block.source_object.native_source_bindings
            assert block.offsets_slpq[0] in (10, 11)
        assert batch.source_audit_blocks[1].scheduler_binding.scheduler_owner == subject._JUG_SCHEDULER
        assert batch.source_audit_blocks[2].scheduler_binding.scheduler_owner == subject._GJJ_SCHEDULER
        assert batch.source_audit_blocks[2].scheduler_binding.identity_key == "6DI9/GJJ"
    assert len(coverage) == 12 and all(len(tasks) == 5 and set(tasks) == set(range(5))
                                       for tasks in coverage.values())
    assert Counter(task for tasks in coverage.values() for task in tasks) == Counter({i: 12 for i in range(5)})
    assert Counter(coverage[subject.ready2.TARGETS_V1[1][0]]) == Counter({i: 1 for i in range(5)})
    assert subject._EXPECTED_TASKS[3][1] == "scaffold_only"


def test_prefix_ready2_native_all_37_fields_and_slpq_roundtrip(session_data, subject):
    prepared, batches = session_data
    for batch in batches:
        a, jug, gjj = batch.source_audit_blocks
        assert subject.train10.validate_covapie_train10_cpu_epoch_batch_v1(a.source_object)
        for key in subject.train10._MODEL_CORE_FIELDS_V1:
            expected = a.source_object.model_input_batch[key]
            count = len(expected) if key in ("names", "receptors") else expected.shape[0]
            _same(batch.model_input_batch[key][:count], expected)
        for field in fields(batch.supervision):
            name = field.name
            source = getattr(a.source_object.supervision, name)
            # Pair offsets have an extra terminal element, but the train10 first block has no shift.
            _same(getattr(batch.supervision, name)[:len(source)], source)
        for block in (jug, gjj):
            source = block.source_object
            _same(block.supervision_snapshot, source.supervision)
            assert len(fields(block.supervision_snapshot)) == 37
            for key in subject.train10._MODEL_CORE_FIELDS_V1:
                _same(block.core_snapshot[key], source.model_input_batch[key])
            assert block.native_source_bindings == source.native_source_bindings
        assert set(jug.source_object.model_input_batch) == (set(subject.train10._MODEL_CORE_FIELDS_V1)
                                                           | set(subject._JUG_SIDE_FIELDS))
        assert set(gjj.source_object.model_input_batch) == set(subject.train10._MODEL_CORE_FIELDS_V1)
        assert "covapie_current11_task2_runtime_result_v1" not in batch.model_input_batch
        assert jug.source_object.model_input_batch["covapie_current11_task2_runtime_result_v1"]
        assert jug.source_object.model_input_batch["covapie_current11_authoritative_training_supervision_v1"]
        assert jug.offsets_slpq[0] == 10 and gjj.offsets_slpq[0] == 11
        assert all(value > 0 for value in jug.offsets_slpq[1:])
        assert all(gjj.offsets_slpq[i] > jug.offsets_slpq[i] for i in range(4))
        assert subject._roundtrip(batch) is None
        assert subject._batch_seal(batch) == batch.payload_sha256
        for b in batch.source_audit_blocks:
            assert subject._block_seal(b) == b.payload_sha256


def test_source_specific_post_seed_pair_denominators_and_sentinels(session_data, subject):
    _, batches = session_data
    for batch in batches:
        s = batch.supervision
        for position, expected_post in ((10, False), (11, True)):
            native = batch.source_audit_blocks[position - 9].supervision_snapshot
            _same(s.pre_post_geometry_target_angstrom[position], native.pre_post_geometry_target_angstrom[0])
            _same(s.pre_post_geometry_component_valid_mask[position], native.pre_post_geometry_component_valid_mask[0])
            _same(s.pre_post_geometry_component_loss_mask[position], native.pre_post_geometry_component_loss_mask[0])
            assert not s.pre_post_geometry_component_valid_mask[position, 0].item()
            assert bool(s.pre_post_geometry_component_valid_mask[position, 1]) == expected_post
            assert s.observed_complex_pair_distance_valid[position, 0].item()
            assert s.pair_positive_candidate_valid[position].item()
            assert int(s.pair_positive_candidate_index[position]) >= int(s.pair_candidate_offsets[position])
            assert int(s.pair_positive_candidate_index[position]) < int(s.pair_candidate_offsets[position + 1])
            index = int(s.pair_positive_candidate_index[position])
            assert int(s.pair_candidate_pocket_flat_index[index]) == int(s.target_residue_reactive_atom_flat_index[position])
            assert s.ligand_minimal_seed_or_anchor_valid[position].item() == native.ligand_minimal_seed_or_anchor_valid[0].item()
        _same(s.pair_candidate_offsets[10:12] - int(s.pair_candidate_offsets[10]),
              batch.source_audit_blocks[1].supervision_snapshot.pair_candidate_offsets)
        _same(s.pair_candidate_offsets[11:13] - int(s.pair_candidate_offsets[11]),
              batch.source_audit_blocks[2].supervision_snapshot.pair_candidate_offsets)
        for block in batch.source_audit_blocks[1:]:
            native = block.supervision_snapshot
            idx, valid = native.target_residue_reactive_atom_flat_index, native.target_residue_condition_valid
            assert torch.equal(subject.train10._offset_valid_indices_v1(idx, offset=block.offsets_slpq[2], valid=valid),
                               s.target_residue_reactive_atom_flat_index[block.sample_start:block.sample_end])
        assert int(s.pre_post_geometry_component_valid_mask[:, 1].sum()) == int(
            sum(int(block.supervision_snapshot.pre_post_geometry_component_valid_mask[:, 1].sum())
                for block in batch.source_audit_blocks))


@pytest.mark.parametrize("epoch,seed", [
    (True, 0), (False, 0), (0.0, 0), (-1, 0), (5, 0), ("3", 0),
    (0, True), (0, False), (0, 0.0), (0, -1), (0, 1), (0, "0"),
])
def test_invalid_epoch_seed_fail_before_owner_build(session_data, subject, epoch, seed):
    prepared, batches = session_data
    _failure(subject, lambda: subject.build_covapie_train12_cpu_epoch_batch_v1(prepared, epoch, seed),
             "EPOCH_OR_SEED_OUTSIDE_CPU_V1_DOMAIN")
    forged = replace(batches[0], epoch=epoch, task_schedule_seed=seed)
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared),
             "EPOCH_OR_SEED_OUTSIDE_CPU_V1_DOMAIN")


def test_determinism_and_batch_vs_prepared_other_epoch_isolation(session_data, subject):
    prepared, batches = session_data
    seal = subject._prepared_seal(prepared)
    other = subject.build_covapie_train12_cpu_epoch_batch_v1(prepared, 3, 0)
    _same(other.model_input_batch, batches[3].model_input_batch)
    _same(other.supervision, batches[3].supervision)
    assert other.payload_sha256 == batches[3].payload_sha256
    other.model_input_batch["lig_coords"][0, 0] += 12
    other.source_audit_blocks[1].source_object.model_input_batch["lig_coords"][0, 0] += 15
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(other, prepared),
             "BATCH_OR_METADATA_MUTATION_SEAL_INVALID")
    assert subject._prepared_seal(prepared) == seal
    assert subject.validate_covapie_train12_cpu_epoch_batch_v1(batches[3], prepared)
    assert subject.validate_covapie_train12_cpu_epoch_batch_v1(batches[4], prepared)
    again = subject.build_covapie_train12_cpu_epoch_batch_v1(prepared, 3, 0)
    _same(again.model_input_batch, batches[3].model_input_batch)
    _same(again.supervision, batches[3].supervision)
    assert again.payload_sha256 == batches[3].payload_sha256


@pytest.mark.parametrize("field,new,reason", [
    ("canonical_event_ids", lambda b: b.canonical_event_ids[:11] + (b.canonical_event_ids[10],), "BATCH_POPULATION_SOURCE_OR_READINESS_INVALID"),
    ("canonical_event_ids", lambda b: b.canonical_event_ids[:11] + ("6BV6/NOT_TARGET",), "BATCH_POPULATION_SOURCE_OR_READINESS_INVALID"),
    ("sample_identities", lambda b: b.sample_identities[:11] + (b.sample_identities[10],), "BATCH_POPULATION_SOURCE_OR_READINESS_INVALID"),
    ("leakage_group_ids", lambda b: b.leakage_group_ids[:10] + ("HELDOUT", b.leakage_group_ids[11]), "BATCH_POPULATION_SOURCE_OR_READINESS_INVALID"),
    ("formal_splits", lambda b: b.formal_splits[:10] + ("validation", "train"), "BATCH_POPULATION_SOURCE_OR_READINESS_INVALID"),
    ("scheduled_task_ids", lambda b: b.scheduled_task_ids[:11] + ((b.scheduled_task_ids[11] + 1) % 5,), "THREE_SOURCE_TASK_SCHEDULE_NOT_PRESERVED"),
])
def test_resealed_metadata_event_group_split_task_invalid(session_data, subject, field, new, reason):
    prepared, batches = session_data
    forged = _reseal(subject, replace(copy.deepcopy(batches[0]), **{field: new(batches[0])}))
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared), reason)


def test_resealed_wrong_offsets_sentinel_pair_and_target_semantics(session_data, subject):
    prepared, batches = session_data
    original = batches[0]
    bad_offset = _reblock(subject, original, 1,
                         offsets_slpq=(10, 0, 0, 0))
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(bad_offset, prepared),
             "SOURCE_SLPQ_OFFSET_BOUNDARY_INVALID")
    for name, sample, reason in (
        ("lig_mask", 0, "MODEL_MEMBERSHIP_INVALID"),
        ("pair_candidate_offsets", 11, "PAIR_CANDIDATE_OFFSETS_INVALID"),
        ("pair_candidate_batch_index", 0, "PAIR_CANDIDATE_MEMBERSHIP_INVALID"),
        ("pair_candidate_ligand_flat_index", 0, "PAIR_CANDIDATE_MEMBERSHIP_INVALID"),
        ("pair_candidate_pocket_flat_index", 0, "PAIR_CANDIDATE_MEMBERSHIP_INVALID"),
        ("pair_positive_candidate_index", 11, "POSITIVE_CANDIDATE_INDEX_INVALID"),
        ("target_residue_reactive_atom_flat_index", 11, "TARGET_REACTIVE_INDEX_INVALID"),
    ):
        forged = copy.deepcopy(original)
        if name == "lig_mask":
            forged.model_input_batch[name][forged.source_audit_blocks[1].offsets_slpq[1]] = 0
        else:
            sup = forged.supervision
            tensor = getattr(sup, name)
            if name == "pair_candidate_offsets":
                tensor[sample] = tensor[sample - 1]
            elif name == "pair_candidate_batch_index":
                tensor[sup.pair_candidate_offsets[10]] = 0
            elif name in ("pair_candidate_ligand_flat_index", "pair_candidate_pocket_flat_index"):
                tensor[sup.pair_candidate_offsets[10]] = 0
            elif name == "pair_positive_candidate_index":
                tensor[sample] = -1
            else:
                tensor[sample] = 0
        forged = _reseal(subject, forged)
        _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared), reason)


def test_nonzero_offset_invalid_sentinel_and_source_local_indices_not_renumbered(session_data, subject):
    prepared, batches = session_data
    original = batches[0]
    for sample in (10, 11):
        forged = copy.deepcopy(original)
        s = forged.supervision
        s.pair_positive_candidate_valid[sample] = False
        s.pair_positive_candidate_index[sample] = -1
        # The positive pair still exists: a forged invalid sentinel cannot
        # silence an owner-produced positive candidate.
        forged = _reseal(subject, forged)
        _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared),
                 "POSITIVE_CANDIDATE_SENTINEL_INVALID")
        forged = copy.deepcopy(original)
        s = forged.supervision
        s.target_residue_condition_valid[sample] = False
        s.target_residue_reactive_atom_local_index[sample] = -1
        p = original.source_audit_blocks[sample - 9].offsets_slpq[2]
        s.target_residue_reactive_atom_flat_index[sample] = p - 1
        pocket_start = int(forged.model_input_batch["num_pocket_nodes"][:sample].sum())
        pocket_end = pocket_start + int(forged.model_input_batch["num_pocket_nodes"][sample])
        s.target_residue_reactive_atom_mask[pocket_start:pocket_end] = False
        forged = _reseal(subject, forged)
        _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared),
                 "TARGET_REACTIVE_SENTINEL_INVALID")
    for name, offset, reason in (
        ("lig_source_row_index", original.source_audit_blocks[1].offsets_slpq[1], "SOURCE_LIGAND_CORE_ROUNDTRIP:lig_source_row_index"),
        ("pocket_source_row_index", original.source_audit_blocks[2].offsets_slpq[2], "SOURCE_POCKET_CORE_ROUNDTRIP:pocket_source_row_index"),
        ("lig_parser_local_index", original.source_audit_blocks[1].offsets_slpq[1], "PARSER_LOCAL_INDEX_SEMANTICS_INVALID"),
    ):
        forged = copy.deepcopy(original)
        forged.model_input_batch[name][offset] += 1
        forged = _reseal(subject, forged)
        _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared), reason)


def test_resealed_valid_shape_wrong_channel_and_invalid_one_hot(session_data, subject):
    prepared, batches = session_data
    original = batches[0]
    start = original.source_audit_blocks[1].offsets_slpq[1]
    for pattern, reason in (
        ("zeros", "MODEL_ONE_HOT_INVALID"),
        ("multi", "MODEL_ONE_HOT_INVALID"),
        ("eleven", "MODEL_NODE_TENSOR_INVALID"),
        ("channel", "SOURCE_LIGAND_CORE_ROUNDTRIP:lig_one_hot"),
    ):
        forged = copy.deepcopy(original)
        vector = forged.model_input_batch["lig_one_hot"]
        if pattern == "eleven":
            forged.model_input_batch["lig_one_hot"] = torch.nn.functional.pad(vector, (0, 1))
        elif pattern == "channel":
            idx = int(vector[start].argmax())
            vector[start, idx] = 0
            vector[start, (idx + 1) % 10] = 1
        else:
            vector[start, :] = 0
            if pattern == "multi":
                vector[start, :2] = 1
        forged = _reseal(subject, forged)
        _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared), reason)
    forged = copy.deepcopy(original)
    vector = forged.model_input_batch["lig_one_hot"]
    idx = int(vector[start].argmax())
    vector[start, idx] = 0
    vector[start, (idx + 1) % 10] = 1
    # First the original seal detects mutation; after recalculation, native
    # equivalence detects the semantically valid but wrong checkpoint channel.
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared),
             "BATCH_OR_METADATA_MUTATION_SEAL_INVALID")
    forged = _reseal(subject, forged)
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared),
             "SOURCE_LIGAND_CORE_ROUNDTRIP:lig_one_hot")


def test_native_source_forgery_sidecar_unknown_fields_and_reseal_fail(session_data, subject):
    prepared, batches = session_data
    original = batches[0]
    native_model = copy.deepcopy(original.source_audit_blocks[1].source_object.model_input_batch)
    native_model["unexpected_owner_extra"] = True
    _failure(subject, lambda: subject._native_core(native_model,
             kind=subject._BLOCK_KINDS[1], identity=subject.ready2.TARGETS_V1[0][1]),
             "NATIVE_EXACT_FIELD_SET_OR_UNKNOWN_FIELD_INVALID")
    native_model.pop("unexpected_owner_extra")
    native_model.pop("covapie_current11_task2_runtime_result_v1")
    _failure(subject, lambda: subject._native_core(native_model,
             kind=subject._BLOCK_KINDS[1], identity=subject.ready2.TARGETS_V1[0][1]),
             "JUG_AUDIT_SIDECAR_MISSING_OR_INVALID")
    block = copy.deepcopy(original.source_audit_blocks[1])
    block.source_object.model_input_batch.pop("covapie_current11_task2_runtime_result_v1")
    bad = _reblock(subject, original, 1, source_object=block.source_object)
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(bad, prepared),
             "SOURCE_NATIVE_REFERENCE_OR_SNAPSHOT_EQUIVALENCE_INVALID")
    for ordinal, key in ((1, "unknown_model_field"), (2, "Batch001_fake_branch")):
        block = copy.deepcopy(original.source_audit_blocks[ordinal])
        block.source_object.model_input_batch[key] = "unexpected"
        bad = _reblock(subject, original, ordinal, source_object=block.source_object)
        _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(bad, prepared),
                 "SOURCE_NATIVE_REFERENCE_OR_SNAPSHOT_EQUIVALENCE_INVALID")
    bad = _reblock(subject, original, 2, native_owner="BATCH001_FORMAL_TRAIN5_V1")
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(bad, prepared),
             "SOURCE_NATIVE_REFERENCE_OR_SNAPSHOT_EQUIVALENCE_INVALID")
    bad = _reblock(subject, original, 2, native_source_bindings=tuple())
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(bad, prepared),
             "SOURCE_NATIVE_REFERENCE_OR_SNAPSHOT_EQUIVALENCE_INVALID")
    bad = _reblock(subject, original, 2, scheduler_binding=replace(
        original.source_audit_blocks[2].scheduler_binding, identity_key="CYS_SG_SAMPLE_INDEX_000003"))
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(bad, prepared),
             "SOURCE_NATIVE_REFERENCE_OR_SNAPSHOT_EQUIVALENCE_INVALID")


def test_dtypes_dims_mutations_and_cpu_only_without_cuda_allocation(session_data, subject):
    prepared, batches = session_data
    original = batches[0]
    for field, change, reason in (
        ("num_lig_atoms", lambda t: t.to(dtype=torch.float32), "NUM_LIG_ATOMS_INVALID"),
        ("lig_one_hot", lambda t: t.view(1, -1), "MODEL_NODE_TENSOR_INVALID"),
        ("pocket_source_row_index", lambda t: t.to(dtype=torch.int32), "POCKET_SOURCE_ROW_INDEX_INVALID"),
        ("pocket_coords", lambda t: t.flatten(), "POCKET_COORDS_INVALID"),
    ):
        forged = copy.deepcopy(original)
        forged.model_input_batch[field] = change(forged.model_input_batch[field])
        forged = _reseal(subject, forged)
        _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared), reason)
    forged = copy.deepcopy(original)
    object.__setattr__(forged.supervision, "pair_candidate_offsets",
                       forged.supervision.pair_candidate_offsets.to(dtype=torch.float32))
    forged = _reseal(subject, forged)
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared),
             "PAIR_CANDIDATE_OFFSETS_INVALID")

    class CpuStorageClaimingGpu(torch.Tensor):
        @property
        def device(self):
            return torch.device("cuda")

    cpu_backed = torch.empty(1, dtype=torch.long, device="cpu")
    claimed = torch.Tensor._make_subclass(CpuStorageClaimingGpu, cpu_backed)
    assert cpu_backed.device.type == "cpu" and claimed.device.type == "cuda"
    # This exercises the CPU gate without allocating or initializing CUDA.
    with pytest.raises(subject.train10._ComposerInvariantError) as rejected:
        subject.train10._tensor_v1(claimed, name="num_lig_atoms", ndim=1, dtype=torch.long)
    assert rejected.value.reason == "NUM_LIG_ATOMS_INVALID"
    assert not torch.cuda.is_initialized()


def test_prepared_and_original_source_mutation_vs_recomputed_seals_fail(session_data, subject):
    prepared, batches = session_data
    original = batches[0]
    disposable = copy.deepcopy(prepared)
    disposable._groups = disposable._groups[:10] + ("HELDOUT", disposable._groups[11])
    disposable._seal = subject._prepared_seal(disposable)
    _failure(subject, lambda: subject.build_covapie_train12_cpu_epoch_batch_v1(disposable, 0, 0),
             "PREPARED_SOURCE_OR_MUTATION_SEAL_INVALID")
    disposable = copy.deepcopy(prepared)
    native = disposable._ready2._gjj
    object.__setattr__(native, "sample_identity", "6BV8/GJJ")
    disposable._ready2._seal = subject.ready2._seal(disposable._ready2)
    disposable._seal = subject._prepared_seal(disposable)
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(original, disposable),
             "GJJ_NATIVE_IDENTITY_DRIFT")
    assert subject.validate_covapie_train12_cpu_epoch_batch_v1(original, prepared)
    forged = copy.deepcopy(original)
    forged.source_audit_blocks[0].source_object.model_input_batch["lig_coords"][0, 0] += 17
    forged = _reseal(subject, forged)
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared),
             "COVAPIE_TRAIN10_CPU_BATCH_COMPOSER_V1_ERROR")
    native = copy.deepcopy(original.source_audit_blocks[2].source_object)
    native.model_input_batch["lig_coords"][0, 0] += 1
    core = subject.train10._clone_model_input_v1(native.model_input_batch)
    forged = _reblock(subject, original, 2, source_object=native, core_snapshot=core)
    _failure(subject, lambda: subject.validate_covapie_train12_cpu_epoch_batch_v1(forged, prepared),
             "SOURCE_NATIVE_REFERENCE_OR_SNAPSHOT_EQUIVALENCE_INVALID")


def test_fresh_source_owner_comparison_not_only_a_seal(session_data, subject):
    prepared, batches = session_data
    original = batches[0]
    ready = subject.ready2
    reference = ready.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
        prepared._ready2, canonical_event_id=ready.TARGETS_V1[1][0],
        canonical_task_name=original.source_audit_blocks[2].source_object.canonical_task_name)
    COUNTS["reference_builds_explicit"] += 1
    _same(reference.model_input_batch, original.source_audit_blocks[2].source_object.model_input_batch)
    _same(reference.supervision, original.source_audit_blocks[2].source_object.supervision)
    assert reference.native_owner == "EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_V1"
    assert original.source_audit_blocks[1].source_object.native_owner == "CURRENT11_MIXED_PROFILE_TENSORIZER_V1"
    assert subject.validate_covapie_train12_cpu_epoch_batch_v1(original, prepared)
