from __future__ import annotations

import ast
import csv
from dataclasses import fields, replace
import hashlib
import inspect
import io
import json
from pathlib import Path

import pytest
import torch

from covalent_ext import (
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as subject,
)
from covalent_ext import covapie_batch001_positive_structural_input_v1 as structural_owner
from covalent_ext import (
    covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1
    as preview_owner,
)
from covalent_ext import (
    covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1
    as train5_predecessor,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)
from scripts import (
    check_covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as checker,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = (
    REPOSITORY_ROOT.parent / "covapie-state/bulk-multisource-cys-sg-v1/rcsb"
)
SOURCE_PATH = REPOSITORY_ROOT / checker.AUTHORIZED_CANDIDATE_FILES_V1[0]


@pytest.fixture(scope="module")
def authority():
    return subject.load_covapie_batch001_formal_split_authority_v1(
        repository_root=REPOSITORY_ROOT
    )


@pytest.fixture(scope="module")
def batches():
    return tuple(
        subject.build_covapie_batch001_model_usable_split_batch_v1(
            split=split,
            epoch=0,
            task_schedule_seed=0,
            repository_root=REPOSITORY_ROOT,
            cache_root=CACHE_ROOT,
        )
        for split in ("train", "validation", "test")
    )


@pytest.fixture(scope="module")
def independent_previews():
    records = structural_owner.build_covapie_batch001_positive_structural_records_v1(
        repository_root=REPOSITORY_ROOT, cache_root=CACHE_ROOT
    )
    by_id = {record.sample_identity: record for record in records}
    result = []
    for event_ids in (
        subject.FORMAL_TRAIN_EVENT_IDS_V1,
        subject.FORMAL_VALIDATION_EVENT_IDS_V1,
        subject.FORMAL_TEST_EVENT_IDS_V1,
    ):
        tasks = tuple(
            preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
                sample_identity=event_id,
                epoch=0,
                task_schedule_seed=0,
            )
            for event_id in event_ids
        )
        result.append(preview_owner._tensorize_records_v1(
            records=tuple(by_id[event_id] for event_id in event_ids),
            task_ids=tasks,
            epoch=0,
            task_schedule_seed=0,
        ))
    return tuple(result)


@pytest.fixture(scope="module")
def artifacts():
    return subject.build_covapie_batch001_model_usable_split_artifacts_v1(
        repository_root=REPOSITORY_ROOT, cache_root=CACHE_ROOT
    )


def _same_tensor(left: torch.Tensor, right: torch.Tensor) -> bool:
    if left.dtype != right.dtype or left.shape != right.shape:
        return False
    if left.dtype.is_floating_point:
        return bool(
            torch.equal(torch.isnan(left), torch.isnan(right))
            and torch.equal(torch.nan_to_num(left), torch.nan_to_num(right))
        )
    return bool(torch.equal(left, right))


def _assert_supervision_equal(left, right) -> None:
    assert len(fields(CovapieCurrent11TrainingSupervisionTensorsV1)) == 37
    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        assert _same_tensor(getattr(left, field.name), getattr(right, field.name)), field.name


def _assert_model_input_equal(left, right) -> None:
    assert tuple(left) == tuple(right)
    for name in left:
        if isinstance(left[name], torch.Tensor):
            assert isinstance(right[name], torch.Tensor)
            assert _same_tensor(left[name], right[name]), name
        else:
            assert left[name] == right[name], name


def _clone_supervision_with(supervision, **changes):
    values = {
        field.name: getattr(supervision, field.name).clone()
        for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    }
    values.update(changes)
    return CovapieCurrent11TrainingSupervisionTensorsV1(**values)


def _canonical_json_bytes(value) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _csv_bytes(fieldnames, rows) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _replace_artifact_and_binding(artifacts, name: str, payload: bytes):
    result = dict(artifacts)
    result[name] = payload
    manifest = json.loads(result[subject.MANIFEST_V1])
    if name != subject.MANIFEST_V1:
        manifest["artifact_bindings"][name]["sha256"] = hashlib.sha256(payload).hexdigest()
        result[subject.MANIFEST_V1] = _canonical_json_bytes(manifest)
    return result


def test_exact_formal_authority_is_mechanically_derived_and_disjoint(authority) -> None:
    assert authority.train_event_ids == subject.FORMAL_TRAIN_EVENT_IDS_V1
    assert authority.validation_event_ids == subject.FORMAL_VALIDATION_EVENT_IDS_V1
    assert authority.test_event_ids == subject.FORMAL_TEST_EVENT_IDS_V1
    assert len(authority.rows) == 13
    assert dict(authority.event_identity_intersection_counts) == {
        "train_validation": 0,
        "train_test": 0,
        "validation_test": 0,
    }
    assert authority.formal_leakage_group_cross_split_violation_count == 0
    ndu = [row for row in authority.rows if row.ligand_component_id == "NDU"]
    assert len(ndu) == 4
    assert all(row.formal_split == "test" for row in ndu)
    assert all(row.formal_leakage_group_id == "COVAPIE_LEAKAGE_GROUP_000005" for row in ndu)
    assert all(row.leakage_classification == "HISTORICAL_BASELINE_COMPONENT" for row in ndu)
    assert subject.validate_covapie_batch001_formal_split_authority_v1(authority)


def test_exact_source_sha_bindings_are_current(authority) -> None:
    expected = {
        relative: sha for _, relative, sha, _ in subject._SOURCE_BINDING_SPECS_V1
    }
    observed = {
        binding.relative_path: binding.sha256 for binding in authority.source_bindings
    }
    assert observed == expected
    assert all(binding.sha256_verified for binding in authority.source_bindings)
    assert observed[subject._FORMAL_EVENT_PATH_V1.as_posix()] == (
        "944fd8447aead448a6f825296872dfb7a2d4e24733dfeede5c93553b45bcdff5"
    )


def test_public_api_returns_exact_split_batches_and_activation_policy(
    batches, authority
) -> None:
    train, validation, test = batches
    assert tuple(batch.formal_split for batch in batches) == (
        "train", "validation", "test",
    )
    assert tuple(batch.sample_identities for batch in batches) == (
        subject.FORMAL_TRAIN_EVENT_IDS_V1,
        subject.FORMAL_VALIDATION_EVENT_IDS_V1,
        subject.FORMAL_TEST_EVENT_IDS_V1,
    )
    assert [len(batch.sample_identities) for batch in batches] == [5, 4, 4]
    assert sum(sum(batch.model_usable) for batch in batches) == 13
    assert sum(sum(batch.sample_training_admitted) for batch in batches) == 5
    assert sum(sum(batch.model_training_activation_authorized) for batch in batches) == 5
    assert sum(sum(batch.optimizer_population_eligible) for batch in batches) == 5
    assert all(value is not None for value in train.training_scheduled_task_ids)
    assert validation.training_scheduled_task_ids == (None,) * 4
    assert test.training_scheduled_task_ids == (None,) * 4
    for batch in batches:
        assert subject.validate_covapie_batch001_model_usable_split_batch_v1(
            batch, authority=authority
        )


def test_train5_exact_supervision_counts_and_formula(batches) -> None:
    train = batches[0]
    supervision = train.supervision
    assert supervision.sample_training_admitted.tolist() == [True] * 5
    assert bool(supervision.canonical_task_valid.all().item())
    assert bool(supervision.ligand_role_valid.all().item())
    expected_diffusion = (
        supervision.ligand_base_generation_mask
        & supervision.canonical_task_valid[train.model_input_batch["lig_mask"]].unsqueeze(1)
        & supervision.sample_training_admitted[train.model_input_batch["lig_mask"]].unsqueeze(1)
    )
    assert torch.equal(supervision.ligand_active_diffusion_loss_mask, expected_diffusion)
    assert len(supervision.pair_candidate_batch_index) == 690
    assert int(supervision.pair_candidate_is_positive.sum().item()) == 5
    assert bool(supervision.pair_head_candidate_loss_mask.all().item())
    assert supervision.pair_contrastive_sample_loss_mask.tolist() == [True] * 5
    assert supervision.pre_post_geometry_component_valid_mask.tolist() == [[False, True]] * 5
    assert supervision.pre_post_geometry_component_loss_mask.tolist() == [[False, True]] * 5


def test_validation4_and_test4_retain_labels_but_all_training_masks_are_false(
    batches,
) -> None:
    expected_pairs = (360, 460)
    for batch, pair_count in zip(batches[1:], expected_pairs):
        supervision = batch.supervision
        assert len(supervision.pair_candidate_batch_index) == pair_count
        assert int(supervision.pair_candidate_is_positive.sum().item()) == 4
        assert bool(supervision.pair_positive_candidate_valid.all().item())
        assert supervision.pre_post_geometry_component_valid_mask.tolist() == [[False, True]] * 4
        assert not bool(supervision.sample_training_admitted.any().item())
        assert not bool(supervision.ligand_active_diffusion_loss_mask.any().item())
        assert not bool(supervision.pair_head_candidate_loss_mask.any().item())
        assert not bool(supervision.pair_contrastive_sample_loss_mask.any().item())
        assert not bool(supervision.pre_post_geometry_component_loss_mask.any().item())


def test_train5_all_37_fields_match_published_activation_predecessor(
    batches, independent_previews
) -> None:
    preview = independent_previews[0]
    snapshot = _clone_supervision_with(preview.supervision)
    expected = train5_predecessor._clone_admitted_supervision(
        preview.supervision, preview.model_input_batch["lig_mask"]
    )
    _assert_supervision_equal(batches[0].supervision, expected)
    _assert_supervision_equal(preview.supervision, snapshot)
    assert not bool(preview.supervision.sample_training_admitted.any().item())
    assert not bool(preview.supervision.ligand_active_diffusion_loss_mask.any().item())


def test_validation_and_test_exact_37_field_preview_parity(
    batches, independent_previews
) -> None:
    _assert_supervision_equal(batches[1].supervision, independent_previews[1].supervision)
    _assert_supervision_equal(batches[2].supervision, independent_previews[2].supervision)


def test_all_split_model_inputs_have_exact_preview_owner_parity(
    batches, independent_previews
) -> None:
    for batch, preview in zip(batches, independent_previews):
        _assert_model_input_equal(batch.model_input_batch, preview.model_input_batch)


def test_role_profiles_and_applicable_task_domains_are_exact(batches) -> None:
    by_id = {
        event_id: (profile, tasks)
        for batch in batches
        for event_id, profile, tasks in zip(
            batch.sample_identities, batch.role_profiles, batch.applicable_task_ids
        )
    }
    for event_id, (profile, tasks) in by_id.items():
        if ":PX5:" in event_id:
            assert profile == preview_owner.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
            assert tasks == (0, 3, 4)
        else:
            assert profile == preview_owner.STRICT_LINKER_PRESENT_V1
            assert tasks == (0, 1, 2, 3, 4)


def test_train5_five_epoch_scheduler_cycle_remains_complete() -> None:
    for event_id in subject.FORMAL_TRAIN_EVENT_IDS_V1:
        cycle = tuple(
            preview_owner.canonical_task_id_for_covapie_batch001_sample_v1(
                sample_identity=event_id,
                epoch=epoch,
                task_schedule_seed=0,
            )
            for epoch in range(5)
        )
        assert set(cycle) == set(range(5))


def test_independent_activation_oracle_has_exact_13_of_13_parity(
    batches, artifacts
) -> None:
    authority_path = REPOSITORY_ROOT / subject._FORMAL_EVENT_PATH_V1
    with authority_path.open(newline="", encoding="utf-8") as handle:
        source_rows = list(csv.DictReader(handle))
    oracle = {
        row["canonical_event_id"]: (
            row["assigned_split"] == "train"
            and row["split_admission_authoritative"] == "true"
        )
        for row in source_rows
    }
    index_rows = list(csv.DictReader(io.StringIO(
        artifacts[subject.SPLIT_INDEX_V1].decode("utf-8"), newline=""
    )))
    assert len(oracle) == len(index_rows) == 13
    assert all(
        (row["sample_training_admitted"] == "true")
        == oracle[row["canonical_event_id"]]
        and (row["model_training_activation_authorized"] == "true")
        == oracle[row["canonical_event_id"]]
        for row in index_rows
    )
    assert all(
        batch.sample_training_admitted[index] == oracle[event_id]
        for batch in batches
        for index, event_id in enumerate(batch.sample_identities)
    )


def test_artifacts_are_exact_deterministic_bound_and_materialized(
    artifacts, authority
) -> None:
    repeated = subject.build_covapie_batch001_model_usable_split_artifacts_v1(
        repository_root=REPOSITORY_ROOT, cache_root=CACHE_ROOT
    )
    assert artifacts == repeated
    assert tuple(artifacts) == subject.OUTPUT_FILENAMES_V1
    assert subject.validate_covapie_batch001_model_usable_split_artifacts_v1(
        artifacts, authority=authority
    )
    output_root = REPOSITORY_ROOT / subject.OUTPUT_ROOT_RELATIVE_V1
    assert {path.name for path in output_root.iterdir()} == set(subject.OUTPUT_FILENAMES_V1)
    for name in subject.OUTPUT_FILENAMES_V1:
        assert (output_root / name).read_bytes() == artifacts[name]
    index_rows = list(csv.DictReader(io.StringIO(
        artifacts[subject.SPLIT_INDEX_V1].decode("utf-8"), newline=""
    )))
    assert len(index_rows) == 13
    assert sum(row["model_usable"] == "true" for row in index_rows) == 13
    assert sum(row["sample_training_admitted"] == "true" for row in index_rows) == 5
    assert sum(row["formal_validation_population_member"] == "true" for row in index_rows) == 4
    assert sum(row["formal_test_population_member"] == "true" for row in index_rows) == 4
    manifest = json.loads(artifacts[subject.MANIFEST_V1])
    assert subject.MANIFEST_V1 not in manifest["artifact_bindings"]
    assert manifest["production_geometry_weight_finalized"] is False
    assert manifest["full_training_authorized"] is False
    assert "feature_semantics_audit_required_before_formal_training" not in manifest
    assert "feature_semantics_warning" not in manifest


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong_population",
        "train_validation_overlap",
        "train_test_overlap",
        "validation_test_overlap",
        "train_marked_validation",
        "ndu_marked_train",
        "non_authoritative",
        "source_binding_drift",
    ),
)
def test_formal_authority_mutations_fail_closed(authority, mutation) -> None:
    candidate = authority
    if mutation == "wrong_population":
        candidate = replace(candidate, rows=candidate.rows[:-1])
    elif mutation == "train_validation_overlap":
        candidate = replace(
            candidate,
            validation_event_ids=(candidate.train_event_ids[0], *candidate.validation_event_ids[1:]),
        )
    elif mutation == "train_test_overlap":
        candidate = replace(
            candidate,
            test_event_ids=(candidate.train_event_ids[0], *candidate.test_event_ids[1:]),
        )
    elif mutation == "validation_test_overlap":
        candidate = replace(
            candidate,
            test_event_ids=(candidate.validation_event_ids[0], *candidate.test_event_ids[1:]),
        )
    elif mutation in {"train_marked_validation", "ndu_marked_train", "non_authoritative"}:
        target = (
            candidate.train_event_ids[0]
            if mutation == "train_marked_validation"
            else candidate.test_event_ids[0]
        )
        rows = []
        for row in candidate.rows:
            if row.canonical_event_id == target:
                changes = (
                    {"formal_split": "validation"}
                    if mutation == "train_marked_validation"
                    else {"formal_split": "train"}
                    if mutation == "ndu_marked_train"
                    else {"split_admission_authoritative": False}
                )
                row = replace(row, **changes)
            rows.append(row)
        candidate = replace(candidate, rows=tuple(rows))
    elif mutation == "source_binding_drift":
        binding = replace(candidate.source_bindings[0], sha256="0" * 64)
        candidate = replace(candidate, source_bindings=(binding, *candidate.source_bindings[1:]))
    with pytest.raises(ValueError) as captured:
        subject.validate_covapie_batch001_formal_split_authority_v1(candidate)
    assert str(captured.value).startswith(subject.BATCH001_13EVENT_MODEL_USABLE_SPLIT_BOUNDARY_ERROR_V1)


def test_wrong_formal_authority_sha_and_owner_binding_drift_fail_closed(
    monkeypatch,
) -> None:
    specs = list(subject._SOURCE_BINDING_SPECS_V1)
    specs[0] = (*specs[0][:2], "0" * 64, specs[0][3])
    monkeypatch.setattr(subject, "_SOURCE_BINDING_SPECS_V1", tuple(specs))
    with pytest.raises(ValueError):
        subject.verify_covapie_batch001_model_usable_source_bindings_v1(
            repository_root=REPOSITORY_ROOT
        )
    monkeypatch.undo()
    specs = list(subject._SOURCE_BINDING_SPECS_V1)
    specs[-1] = (*specs[-1][:2], "f" * 64, specs[-1][3])
    monkeypatch.setattr(subject, "_SOURCE_BINDING_SPECS_V1", tuple(specs))
    with pytest.raises(ValueError):
        subject.verify_covapie_batch001_model_usable_source_bindings_v1(
            repository_root=REPOSITORY_ROOT
        )


@pytest.mark.parametrize(
    "identities,splits",
    (
        (subject.FORMAL_TRAIN_EVENT_IDS_V1[:-1], ("train",) * 4),
        (subject.FORMAL_TRAIN_EVENT_IDS_V1 + (subject.FORMAL_VALIDATION_EVENT_IDS_V1[0],), ("train",) * 6),
        (subject.FORMAL_TRAIN_EVENT_IDS_V1 + (subject.FORMAL_TEST_EVENT_IDS_V1[0],), ("train",) * 6),
        (subject.FORMAL_VALIDATION_EVENT_IDS_V1, ("validation",) * 4),
        (subject.FORMAL_TEST_EVENT_IDS_V1, ("test",) * 4),
        (subject.FORMAL_TRAIN_EVENT_IDS_V1 + subject.FORMAL_VALIDATION_EVENT_IDS_V1 + subject.FORMAL_TEST_EVENT_IDS_V1, ("train",) * 13),
        (tuple(reversed(subject.FORMAL_TRAIN_EVENT_IDS_V1)), ("train",) * 5),
    ),
)
def test_no_cross_split_training_activation_gate_rejects_every_nonexact_population(
    identities, splits
) -> None:
    with pytest.raises(ValueError):
        subject.validate_covapie_batch001_training_activation_population_v1(
            sample_identities=identities, formal_splits=splits
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "train_omitted",
        "validation_admitted",
        "test_admitted",
        "extra_optimizer_eligible",
        "px5_task1",
        "pre_geometry_active",
        "train_activation_tensor_mismatch",
        "heldout_tensor_mismatch",
    ),
)
def test_split_batch_mutations_fail_closed(batches, authority, mutation) -> None:
    train, validation, test = batches
    if mutation == "train_omitted":
        candidate = replace(train, sample_identities=train.sample_identities[:-1])
    elif mutation == "validation_admitted":
        flags = (True, *validation.sample_training_admitted[1:])
        supervision = _clone_supervision_with(
            validation.supervision,
            sample_training_admitted=torch.tensor(flags, dtype=torch.bool),
        )
        candidate = replace(validation, sample_training_admitted=flags, supervision=supervision)
    elif mutation == "test_admitted":
        flags = (True, *test.sample_training_admitted[1:])
        supervision = _clone_supervision_with(
            test.supervision,
            sample_training_admitted=torch.tensor(flags, dtype=torch.bool),
        )
        candidate = replace(test, sample_training_admitted=flags, supervision=supervision)
    elif mutation == "extra_optimizer_eligible":
        candidate = replace(validation, optimizer_population_eligible=(True, False, False, False))
    elif mutation == "px5_task1":
        tasks = list(validation.preview_tensorization_task_ids)
        tasks[2] = 1
        canonical = validation.supervision.canonical_task_id.clone()
        canonical[2] = 1
        candidate = replace(
            validation,
            preview_tensorization_task_ids=tuple(tasks),
            supervision=_clone_supervision_with(
                validation.supervision, canonical_task_id=canonical
            ),
        )
    elif mutation == "pre_geometry_active":
        mask = train.supervision.pre_post_geometry_component_loss_mask.clone()
        mask[0, 0] = True
        candidate = replace(
            train,
            supervision=_clone_supervision_with(
                train.supervision, pre_post_geometry_component_loss_mask=mask
            ),
        )
    elif mutation == "train_activation_tensor_mismatch":
        mask = train.supervision.pair_head_candidate_loss_mask.clone()
        mask[0] = False
        candidate = replace(
            train,
            supervision=_clone_supervision_with(
                train.supervision, pair_head_candidate_loss_mask=mask
            ),
        )
    elif mutation == "heldout_tensor_mismatch":
        labels = test.supervision.pair_candidate_is_positive.clone()
        labels[test.supervision.pair_positive_candidate_index[0]] = False
        candidate = replace(
            test,
            supervision=_clone_supervision_with(
                test.supervision, pair_candidate_is_positive=labels
            ),
        )
    with pytest.raises(ValueError):
        subject.validate_covapie_batch001_model_usable_split_batch_v1(
            candidate, authority=authority
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "sample_training_admitted",
        "model_training_activation_authorized",
        "optimizer_population_eligible",
        "training_scheduler_eligible",
    ),
)
def test_ndu4_each_training_or_optimizer_flag_is_hard_rejected(
    batches, authority, field_name
) -> None:
    test = batches[2]
    candidate = replace(test, **{field_name: (True, False, False, False)})
    with pytest.raises(ValueError):
        subject.validate_covapie_batch001_model_usable_split_batch_v1(
            candidate, authority=authority
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "sample_training_admitted",
        "model_training_activation_authorized",
        "optimizer_population_eligible",
        "training_scheduler_eligible",
    ),
)
def test_validation4_each_training_or_optimizer_flag_is_hard_rejected(
    batches, authority, field_name
) -> None:
    validation = batches[1]
    candidate = replace(
        validation, **{field_name: (True, False, False, False)}
    )
    with pytest.raises(ValueError):
        subject.validate_covapie_batch001_model_usable_split_batch_v1(
            candidate, authority=authority
        )


def test_activation_successor_rejects_any_preview_tensor_mutation(
    monkeypatch, authority
) -> None:
    original = train5_predecessor._clone_admitted_supervision

    def mutating_clone(preview, ligand_batch_index):
        result = original(preview, ligand_batch_index)
        preview.sample_training_admitted[0] = True
        return result

    monkeypatch.setattr(
        train5_predecessor, "_clone_admitted_supervision", mutating_clone
    )
    with pytest.raises(ValueError) as captured:
        subject.build_covapie_batch001_model_usable_split_batch_v1(
            split="train",
            epoch=0,
            task_schedule_seed=0,
            repository_root=REPOSITORY_ROOT,
            cache_root=CACHE_ROOT,
        )
    assert "PUBLISHED_PREVIEW_TENSORS_MUTATED" in str(captured.value)


@pytest.mark.parametrize(
    "mutation",
    (
        "index_count",
        "ndu_split",
        "registry_count",
        "manifest_count",
        "source_inventory_drift",
    ),
)
def test_artifact_mutations_fail_closed(artifacts, authority, mutation) -> None:
    candidate = dict(artifacts)
    if mutation in {"index_count", "ndu_split"}:
        reader = csv.DictReader(io.StringIO(
            candidate[subject.SPLIT_INDEX_V1].decode("utf-8"), newline=""
        ))
        rows = list(reader)
        if mutation == "index_count":
            rows.pop()
        else:
            ndu = next(row for row in rows if row["ligand_component_id"] == "NDU")
            ndu["formal_split"] = "train"
        candidate = _replace_artifact_and_binding(
            candidate,
            subject.SPLIT_INDEX_V1,
            _csv_bytes(reader.fieldnames, rows),
        )
    elif mutation == "registry_count":
        registry = json.loads(candidate[subject.SPLIT_REGISTRY_V1])
        registry["formal_split_populations"]["counts"]["train"] = 4
        candidate = _replace_artifact_and_binding(
            candidate, subject.SPLIT_REGISTRY_V1, _canonical_json_bytes(registry)
        )
    elif mutation == "manifest_count":
        manifest = json.loads(candidate[subject.MANIFEST_V1])
        manifest["population_counts"]["formal_train_event_count"] = 4
        candidate[subject.MANIFEST_V1] = _canonical_json_bytes(manifest)
    elif mutation == "source_inventory_drift":
        reader = csv.DictReader(io.StringIO(
            candidate[subject.SOURCE_BINDING_INVENTORY_V1].decode("utf-8"),
            newline="",
        ))
        rows = list(reader)
        rows[0]["sha256"] = "0" * 64
        candidate = _replace_artifact_and_binding(
            candidate,
            subject.SOURCE_BINDING_INVENTORY_V1,
            _csv_bytes(reader.fieldnames, rows),
        )
    with pytest.raises(ValueError):
        subject.validate_covapie_batch001_model_usable_split_artifacts_v1(
            candidate, authority=authority
        )


def test_product_source_has_no_forbidden_operations_or_broad_heldout_activation() -> None:
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not ({"requests", "urllib", "subprocess", "pytorch_lightning"} & imports)
    called = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            called.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            called.add(node.func.attr)
    assert not ({"Trainer", "fit", "backward", "step", "AdamW", "save"} & called)
    source = SOURCE_PATH.read_text(encoding="utf-8")
    assert "sample_training_admitted=torch.ones" not in source.replace(" ", "")
    assert "if split in {\"validation\", \"test\"}" not in source


def _candidate_snapshot() -> checker.RepositoryGitSnapshotV1:
    return checker.collect_repository_git_snapshot_v1(
        repository_root=REPOSITORY_ROOT
    )


def _valid_successor_snapshot() -> checker.RepositoryGitSnapshotV1:
    current = _candidate_snapshot()
    successor = "1" * 40
    return replace(
        current,
        head=successor,
        origin_main=successor,
        status_entries=(),
        head_parent_ids=(checker.EXPECTED_BASELINE_HEAD_V1,),
        head_subject=checker.PUBLISHED_SUCCESSOR_SUBJECT_V1,
        head_tree="2" * 40,
        head_changed_entries=tuple(
            ("A", path) for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ),
        head_candidate_path_modes=tuple(
            (path, "100644") for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ),
    )


def test_real_repository_dual_profile_and_valid_published_successor_simulation() -> None:
    snapshot = _candidate_snapshot()
    profile = checker.classify_repository_snapshot_v1(snapshot)
    assert profile in {
        checker.CANDIDATE_PRECOMMIT_PROFILE_V1,
        checker.PUBLISHED_SUCCESSOR_PROFILE_V1,
    }
    if profile == checker.CANDIDATE_PRECOMMIT_PROFILE_V1:
        assert snapshot.head == checker.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.origin_main == checker.EXPECTED_BASELINE_HEAD_V1
        assert snapshot.ahead_behind == (0, 0)
        assert snapshot.tracked_modified_paths == ()
        assert snapshot.staged_modified_paths == ()
        assert tuple(sorted(snapshot.status_entries)) == tuple(sorted(
            ("??", path) for path in checker.AUTHORIZED_CANDIDATE_FILES_V1
        ))
    else:
        assert snapshot.head == snapshot.origin_main
        assert snapshot.status_entries == ()
        assert snapshot.head_parent_ids == (checker.EXPECTED_BASELINE_HEAD_V1,)
        assert snapshot.head_subject == checker.PUBLISHED_SUCCESSOR_SUBJECT_V1
    assert checker.classify_repository_snapshot_v1(_valid_successor_snapshot()) == (
        checker.PUBLISHED_SUCCESSOR_PROFILE_V1
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "wrong_parent",
        "wrong_subject",
        "extra_path",
        "missing_artifact",
        "wrong_change_type",
        "python_100755",
        "extra_untracked",
    ),
)
def test_invalid_published_successor_profiles_fail_closed(mutation) -> None:
    value = _valid_successor_snapshot()
    if mutation == "wrong_parent":
        value = replace(value, head_parent_ids=("3" * 40,))
    elif mutation == "wrong_subject":
        value = replace(value, head_subject="wrong")
    elif mutation == "extra_path":
        value = replace(
            value, head_changed_entries=value.head_changed_entries + (("A", "extra"),)
        )
    elif mutation == "missing_artifact":
        value = replace(
            value,
            head_changed_entries=value.head_changed_entries[:-1],
            head_candidate_path_modes=value.head_candidate_path_modes[:-1],
        )
    elif mutation == "wrong_change_type":
        value = replace(
            value,
            head_changed_entries=(
                ("M", checker.AUTHORIZED_CANDIDATE_FILES_V1[0]),
                *value.head_changed_entries[1:],
            ),
        )
    elif mutation == "python_100755":
        value = replace(
            value,
            head_candidate_path_modes=(
                (checker.AUTHORIZED_CANDIDATE_FILES_V1[0], "100755"),
                *value.head_candidate_path_modes[1:],
            ),
        )
    elif mutation == "extra_untracked":
        value = replace(value, status_entries=(("??", "extra"),))
    with pytest.raises(ValueError) as captured:
        checker.classify_repository_snapshot_v1(value)
    assert str(captured.value) == checker.CHECKER_ERROR_V1


def test_candidate_extra_untracked_and_tracked_change_fail_closed() -> None:
    value = _candidate_snapshot()
    with pytest.raises(ValueError):
        checker.classify_repository_snapshot_v1(
            replace(value, status_entries=value.status_entries + (("??", "extra"),))
        )
    with pytest.raises(ValueError):
        checker.classify_repository_snapshot_v1(
            replace(value, tracked_modified_paths=("existing.py",))
        )


def test_checker_executes_real_materialization_and_all_required_markers() -> None:
    result = checker.check_covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1(
        repository_root=REPOSITORY_ROOT
    )
    assert result.deterministic_artifact_bytes
    assert result.materialized_artifacts_match_recomputation
    assert result.cache_input_state_unchanged
    assert result.train_activation_matches_independent_split_oracle
    assert result.train_supervision_matches_published_train5_activation_semantics
    assert result.validation_preview_tensor_parity
    assert result.test_preview_tensor_parity
    assert result.preview_source_unchanged
    assert result.candidate_precommit_profile_passed or (
        result.repository_profile == checker.PUBLISHED_SUCCESSOR_PROFILE_V1
    )
    assert result.published_successor_profile_simulation_passed
    marker_source = inspect.getsource(checker.main)
    markers = (
        "batch001_model_usable_split_materialization_built",
        "formal_positive_event_count",
        "formal_train_event_count",
        "formal_validation_event_count",
        "formal_test_event_count",
        "model_usable_event_count",
        "sample_training_admitted_event_count",
        "model_training_activation_authorized_event_count",
        "optimizer_population_eligible_event_count",
        "validation_training_admitted_event_count",
        "test_training_admitted_event_count",
        "train5_exact_identity_match",
        "validation4_exact_identity_match",
        "test4_exact_identity_match",
        "train_activation_matches_independent_split_oracle",
        "train_supervision_matches_published_train5_activation_semantics",
        "validation_preview_tensor_parity",
        "test_preview_tensor_parity",
        "preview_source_unchanged",
        "PRE_geometry_training_active_count",
        "POST_geometry_train_active_count",
        "NDU4_formal_split",
        "deterministic_artifact_bytes",
        "candidate_precommit_profile_passed",
        "published_successor_profile_simulation_passed",
        "ready_for_gpt_review",
    )
    assert all(marker in marker_source for marker in markers)
