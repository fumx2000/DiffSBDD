from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from collections import Counter
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import covapie_legacy_pipeline_retirement_policy as policy


LEGACY_ROOT_NAMES = (
    "covapie_sample_index_smoke_v0",
    "covapie_split_leakage_design_gate_v0",
    "covapie_split_leakage_smoke_v0",
    "covapie_split_leakage_qa_gate_v0",
    "covapie_final_dataset_smoke_v0",
    "covapie_final_dataset_qa_gate_v0",
    "covapie_dataloader_interface_design_gate_v0",
    "covapie_dataloader_interface_smoke_v0",
    "covapie_dataloader_interface_qa_gate_v0",
    "covapie_dataloader_smoke_design_gate_v0",
    "covapie_metadata_dataloader_smoke_v0",
    "covapie_metadata_dataloader_smoke_qa_gate_v0",
    "covapie_actual_dataloader_design_gate_v0",
)
INDEPENDENT_STAGE_NAMES = (
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0",
    "covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0",
)
STEP14AR_FILES = (
    Path("data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0"),
    Path("docs/covapie_final_dataset_materialization_smoke_v0_summary.md"),
    Path("scripts/check_covapie_final_dataset_materialization_smoke_v0.py"),
    Path("src/covalent_ext/covapie_final_dataset_materialization_smoke.py"),
    Path("tests/test_covapie_final_dataset_materialization_smoke_v0.py"),
)
STAGE_CHECK_SCRIPTS = tuple(
    Path("scripts") / f"check_{stage}.py" for stage in LEGACY_ROOT_NAMES
)


def _policies() -> tuple[policy.LegacyStageRetirementPolicy, ...]:
    return policy.build_all_legacy_stage_retirement_policies()


def _by_stage() -> dict[str, policy.LegacyStageRetirementPolicy]:
    return {item.stage: item for item in _policies()}


def _tracked_path_result() -> dict[str, object]:
    return policy.validate_tracked_successor_manifest_paths(
        _policies(),
        repo_root=REPO_ROOT,
    )


def _tree_hash(paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        absolute = REPO_ROOT / relative
        candidates = [absolute] if absolute.is_file() else sorted(absolute.rglob("*"))
        for path in candidates:
            if path.is_file():
                digest.update(path.relative_to(REPO_ROOT).as_posix().encode())
                digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def test_registry_has_exactly_thirteen_entries() -> None:
    assert len(policy.LEGACY_STAGE_RETIREMENT_REGISTRY) == 13
    assert policy.EXPECTED_LEGACY_STAGE_COUNT == 13


def test_stage_order_is_frozen() -> None:
    assert policy.LEGACY_STAGE_ORDER == LEGACY_ROOT_NAMES


def test_registry_stages_are_unique() -> None:
    assert len(policy.LEGACY_STAGE_ORDER) == len(set(policy.LEGACY_STAGE_ORDER))


def test_availability_values_are_exact() -> None:
    assert policy.SUCCESSOR_AVAILABILITY_VALUES == (
        "tracked",
        "pending_commit",
        "not_materialized",
        "redesign_pending",
    )


def test_availability_counts_are_exact() -> None:
    counts = Counter(item.successor_availability for item in _policies())
    assert {name: counts[name] for name in policy.SUCCESSOR_AVAILABILITY_VALUES} == {
        "tracked": 5,
        "pending_commit": 0,
        "not_materialized": 1,
        "redesign_pending": 7,
    }
    assert policy.EXPECTED_SUCCESSOR_AVAILABILITY_COUNTS == (
        ("tracked", 5),
        ("pending_commit", 0),
        ("not_materialized", 1),
        ("redesign_pending", 7),
    )


def test_all_stages_are_retired() -> None:
    assert all(item.legacy_stage_retired for item in _policies())


def test_all_stages_are_non_executable() -> None:
    assert not any(item.legacy_stage_executable for item in _policies())


def test_all_training_readiness_is_false() -> None:
    assert all(
        not item.ready_for_training and not item.ready_to_train_now
        for item in _policies()
    )


def test_feature_semantics_audit_remains_required() -> None:
    assert all(
        item.feature_semantics_audit_required_before_training
        for item in _policies()
    )


def test_all_historical_artifacts_are_read_only() -> None:
    assert all(item.historical_artifacts_read_only for item in _policies())


def test_all_legacy_artifact_regeneration_is_forbidden() -> None:
    assert all(
        item.legacy_artifact_regeneration_forbidden for item in _policies()
    )


def test_sample_index_smoke_successor_is_exact() -> None:
    item = _by_stage()["covapie_sample_index_smoke_v0"]
    assert item.superseded_by_stage == "covapie_sample_index_materialization_smoke_v0"
    assert item.recommended_next_step == "covapie_sample_index_materialization_smoke"
    assert item.successor_availability == "tracked"


def test_split_design_successor_is_exact() -> None:
    item = _by_stage()["covapie_split_leakage_design_gate_v0"]
    assert item.superseded_by_stage == "covapie_leakage_split_design_gate_v0"
    assert item.recommended_next_step == "covapie_leakage_split_design_gate"


def test_split_smoke_and_qa_share_unified_successor() -> None:
    items = _by_stage()
    for stage in (
        "covapie_split_leakage_smoke_v0",
        "covapie_split_leakage_qa_gate_v0",
    ):
        assert (
            items[stage].superseded_by_stage
            == "covapie_unified_leakage_split_materialization_smoke_v0"
        )
        assert (
            items[stage].recommended_next_step
            == "covapie_unified_leakage_split_materialization_smoke"
        )


def test_final_dataset_smoke_successor_is_tracked() -> None:
    item = _by_stage()["covapie_final_dataset_smoke_v0"]
    assert item.superseded_by_stage == "covapie_final_dataset_materialization_smoke_v0"
    assert item.successor_availability == "tracked"
    assert item.superseded_by_manifest_path == (
        "data/derived/covalent_small/"
        "covapie_final_dataset_materialization_smoke_v0/"
        "covapie_final_dataset_materialization_smoke_manifest.json"
    )


def test_canonical_final_dataset_qa_stage_is_v1() -> None:
    assert policy.CANONICAL_FINAL_DATASET_QA_STAGE == "covapie_final_dataset_qa_gate_v1"
    item = _by_stage()["covapie_final_dataset_qa_gate_v0"]
    assert item.superseded_by_stage == policy.CANONICAL_FINAL_DATASET_QA_STAGE


def test_final_dataset_qa_manifest_path_is_none() -> None:
    item = _by_stage()["covapie_final_dataset_qa_gate_v0"]
    assert item.superseded_by_manifest_path is None
    assert item.successor_availability == "not_materialized"
    assert item.blocking_reasons == (
        "legacy_stage_superseded",
        "canonical_successor_not_materialized",
    )


def test_dataloader_successors_are_none() -> None:
    items = _by_stage()
    for stage in LEGACY_ROOT_NAMES[-7:]:
        assert items[stage].superseded_by_stage is None
        assert items[stage].superseded_by_manifest_path is None
        assert items[stage].successor_availability == "redesign_pending"


def test_dataloader_smoke_design_is_registry_item_ten() -> None:
    assert policy.LEGACY_STAGE_ORDER[9] == (
        "covapie_dataloader_smoke_design_gate_v0"
    )
    assert policy.LEGACY_STAGE_RETIREMENT_REGISTRY[9].stage == (
        "covapie_dataloader_smoke_design_gate_v0"
    )


def test_metadata_smoke_and_qa_are_registry_items_eleven_and_twelve() -> None:
    assert policy.LEGACY_STAGE_ORDER[10:12] == (
        "covapie_metadata_dataloader_smoke_v0",
        "covapie_metadata_dataloader_smoke_qa_gate_v0",
    )


def test_actual_dataloader_design_is_registry_item_thirteen() -> None:
    assert policy.LEGACY_STAGE_ORDER[12] == (
        "covapie_actual_dataloader_design_gate_v0"
    )


def test_dataloader_smoke_design_policy_is_exact() -> None:
    item = _by_stage()["covapie_dataloader_smoke_design_gate_v0"]
    assert item.legacy_stage_retired is True
    assert item.legacy_stage_executable is False
    assert item.superseded_by_stage is None
    assert item.superseded_by_manifest_path is None
    assert item.successor_availability == "redesign_pending"
    assert item.recommended_next_step == "covapie_final_dataset_qa_gate_v1"
    assert item.blocking_reasons == (
        "legacy_stage_superseded",
        "dataloader_interface_redesign_pending",
    )


def test_dataloader_smoke_design_training_boundary_is_exact() -> None:
    item = _by_stage()["covapie_dataloader_smoke_design_gate_v0"]
    assert item.historical_artifacts_read_only is True
    assert item.legacy_artifact_regeneration_forbidden is True
    assert item.ready_for_training is False
    assert item.ready_to_train_now is False
    assert item.feature_semantics_audit_required_before_training is True


def test_removing_dataloader_smoke_design_blocks_registry() -> None:
    items = list(_policies())
    del items[9]
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.registry_count_passed is False
    assert result.stage_order_passed is False


def test_reordering_dataloader_smoke_design_blocks_registry() -> None:
    items = list(_policies())
    items[8], items[9] = items[9], items[8]
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.stage_order_passed is False


def test_dataloader_smoke_design_wrong_successor_blocks_registry() -> None:
    items = list(_policies())
    items[9] = replace(
        items[9],
        superseded_by_stage="unexpected_stage",
        superseded_by_manifest_path="unexpected.json",
    )
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.successor_contract_passed is False


@pytest.mark.parametrize(
    "stage",
    (
        "covapie_metadata_dataloader_smoke_v0",
        "covapie_metadata_dataloader_smoke_qa_gate_v0",
    ),
)
def test_metadata_dataloader_retirement_policies_are_exact(stage: str) -> None:
    item = _by_stage()[stage]
    assert item.legacy_stage_retired is True
    assert item.legacy_stage_executable is False
    assert item.superseded_by_stage is None
    assert item.superseded_by_manifest_path is None
    assert item.successor_availability == "redesign_pending"
    assert item.recommended_next_step == "covapie_final_dataset_qa_gate_v1"
    assert item.blocking_reasons == (
        "legacy_stage_superseded",
        "dataloader_interface_redesign_pending",
    )


@pytest.mark.parametrize(
    "stage",
    (
        "covapie_metadata_dataloader_smoke_v0",
        "covapie_metadata_dataloader_smoke_qa_gate_v0",
    ),
)
def test_metadata_dataloader_training_boundaries_are_exact(stage: str) -> None:
    item = _by_stage()[stage]
    assert item.historical_artifacts_read_only is True
    assert item.legacy_artifact_regeneration_forbidden is True
    assert item.ready_for_training is False
    assert item.ready_to_train_now is False
    assert item.feature_semantics_audit_required_before_training is True


@pytest.mark.parametrize("index", (10, 11))
def test_removing_metadata_dataloader_stage_blocks_registry(index: int) -> None:
    items = list(_policies())
    del items[index]
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.registry_count_passed is False
    assert result.stage_order_passed is False


def test_swapping_metadata_dataloader_stages_blocks_registry() -> None:
    items = list(_policies())
    items[10], items[11] = items[11], items[10]
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.stage_order_passed is False


@pytest.mark.parametrize("index", (10, 11))
def test_metadata_dataloader_wrong_successor_blocks_registry(index: int) -> None:
    items = list(_policies())
    items[index] = replace(items[index], superseded_by_stage="unexpected_stage")
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.successor_contract_passed is False


def test_actual_dataloader_design_policy_is_exact() -> None:
    item = _by_stage()["covapie_actual_dataloader_design_gate_v0"]
    assert item.legacy_stage_retired is True
    assert item.legacy_stage_executable is False
    assert item.superseded_by_stage is None
    assert item.superseded_by_manifest_path is None
    assert item.successor_availability == "redesign_pending"
    assert item.recommended_next_step == "covapie_final_dataset_qa_gate_v1"
    assert item.blocking_reasons == (
        "legacy_stage_superseded",
        "dataloader_interface_redesign_pending",
    )


def test_actual_dataloader_design_training_boundary_is_exact() -> None:
    item = _by_stage()["covapie_actual_dataloader_design_gate_v0"]
    assert item.historical_artifacts_read_only is True
    assert item.legacy_artifact_regeneration_forbidden is True
    assert item.ready_for_training is False
    assert item.ready_to_train_now is False
    assert item.feature_semantics_audit_required_before_training is True


def test_removing_actual_dataloader_design_blocks_registry() -> None:
    items = list(_policies())
    del items[12]
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.registry_count_passed is False
    assert result.stage_order_passed is False


def test_swapping_s3_and_s4_blocks_registry() -> None:
    items = list(_policies())
    items[11], items[12] = items[12], items[11]
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.stage_order_passed is False


def test_actual_dataloader_design_wrong_successor_blocks_registry() -> None:
    items = list(_policies())
    items[12] = replace(items[12], superseded_by_stage="unexpected_stage")
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.successor_contract_passed is False


def test_step14z_independent_stages_are_not_registered() -> None:
    registered = set(policy.LEGACY_STAGE_ORDER)
    assert registered.isdisjoint(INDEPENDENT_STAGE_NAMES)


def test_unknown_stage_raises_key_error() -> None:
    with pytest.raises(KeyError, match="unknown_stage"):
        policy.build_legacy_stage_retirement_policy("unknown_stage")


def test_retired_stage_raises_dedicated_exception_type() -> None:
    with pytest.raises(policy.LegacyStageRetiredError):
        policy.raise_legacy_stage_retired("covapie_sample_index_smoke_v0")


def test_retired_stage_exception_attributes_are_exact() -> None:
    with pytest.raises(policy.LegacyStageRetiredError) as caught:
        policy.raise_legacy_stage_retired("covapie_sample_index_smoke_v0")
    error = caught.value
    assert error.stage == "covapie_sample_index_smoke_v0"
    assert error.superseded_by_stage == "covapie_sample_index_materialization_smoke_v0"
    assert error.successor_availability == "tracked"
    assert error.recommended_next_step == "covapie_sample_index_materialization_smoke"
    assert error.blocking_reasons == ("legacy_stage_superseded",)


def test_retired_stage_exception_message_is_deterministic() -> None:
    expected = (
        "legacy_stage_retired:covapie_sample_index_smoke_v0:"
        "superseded_by=covapie_sample_index_materialization_smoke_v0:"
        "recommended_next_step=covapie_sample_index_materialization_smoke"
    )
    messages = []
    for _ in range(2):
        with pytest.raises(policy.LegacyStageRetiredError) as caught:
            policy.raise_legacy_stage_retired("covapie_sample_index_smoke_v0")
        messages.append(str(caught.value))
    assert messages == [expected, expected]


def test_raise_retired_stage_preserves_unknown_stage_key_error() -> None:
    with pytest.raises(KeyError, match="unknown_stage"):
        policy.raise_legacy_stage_retired("unknown_stage")


def test_raise_retired_stage_creates_no_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    before = tuple(tmp_path.rglob("*"))
    with pytest.raises(policy.LegacyStageRetiredError):
        policy.raise_legacy_stage_retired("covapie_sample_index_smoke_v0")
    after = tuple(tmp_path.rglob("*"))
    assert before == after == ()


def test_builders_are_deterministic() -> None:
    assert _policies() == _policies()


def test_builder_returns_independent_policy_objects() -> None:
    built = policy.build_legacy_stage_retirement_policy(LEGACY_ROOT_NAMES[0])
    assert built == policy.LEGACY_STAGE_RETIREMENT_REGISTRY[0]
    assert built is not policy.LEGACY_STAGE_RETIREMENT_REGISTRY[0]


def test_returned_policy_is_immutable() -> None:
    item = _policies()[0]
    with pytest.raises(FrozenInstanceError):
        item.ready_for_training = True  # type: ignore[misc]


def test_dataclass_field_order_is_frozen() -> None:
    assert tuple(item.name for item in fields(policy.LegacyStageRetirementPolicy)) == (
        "stage",
        "legacy_stage_retired",
        "legacy_stage_executable",
        "superseded_by_stage",
        "superseded_by_manifest_path",
        "successor_availability",
        "historical_artifacts_read_only",
        "legacy_artifact_regeneration_forbidden",
        "ready_for_training",
        "ready_to_train_now",
        "feature_semantics_audit_required_before_training",
        "recommended_next_step",
        "blocking_reasons",
    )


def test_normal_registry_validation_passes() -> None:
    result = policy.validate_legacy_pipeline_retirement_registry(_policies())
    assert result.passed is True
    assert result.blocking_reasons == ()
    assert all(
        (
            result.registry_count_passed,
            result.stage_order_passed,
            result.stage_uniqueness_passed,
            result.availability_contract_passed,
            result.successor_contract_passed,
            result.retirement_boundary_passed,
            result.training_boundary_passed,
        )
    )


def test_duplicate_stage_blocks_validation() -> None:
    items = list(_policies())
    items[-1] = replace(items[-1], stage=items[0].stage)
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.stage_uniqueness_passed is False


def test_invalid_availability_blocks_validation() -> None:
    items = list(_policies())
    items[0] = replace(items[0], successor_availability="invalid")
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.availability_contract_passed is False


def test_tracked_successor_missing_path_blocks_registry_validation() -> None:
    items = list(_policies())
    items[4] = replace(items[4], superseded_by_manifest_path=None)
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.successor_contract_passed is False


def test_not_materialized_non_none_path_blocks_validation() -> None:
    items = list(_policies())
    items[5] = replace(items[5], superseded_by_manifest_path="unexpected.json")
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.successor_contract_passed is False


def test_redesign_pending_successor_blocks_validation() -> None:
    items = list(_policies())
    items[6] = replace(items[6], superseded_by_stage="unexpected_stage")
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.successor_contract_passed is False


def test_training_readiness_true_blocks_validation() -> None:
    items = list(_policies())
    items[0] = replace(items[0], ready_for_training=True)
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.training_boundary_passed is False


def test_legacy_executable_true_blocks_validation() -> None:
    items = list(_policies())
    items[0] = replace(items[0], legacy_stage_executable=True)
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.retirement_boundary_passed is False


def test_missing_first_superseded_blocker_blocks_validation() -> None:
    items = list(_policies())
    items[0] = replace(items[0], blocking_reasons=("other",))
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.retirement_boundary_passed is False


def test_duplicate_blocker_blocks_validation() -> None:
    items = list(_policies())
    items[0] = replace(
        items[0],
        blocking_reasons=("legacy_stage_superseded", "legacy_stage_superseded"),
    )
    result = policy.validate_legacy_pipeline_retirement_registry(items)
    assert result.passed is False
    assert result.retirement_boundary_passed is False


def test_tracked_successor_paths_validate_five_of_five() -> None:
    result = _tracked_path_result()
    assert result == {
        "tracked_successor_paths_passed": True,
        "tracked_successor_reference_count": 5,
        "validated_reference_count": 5,
        "unique_manifest_path_count": 4,
        "unique_regular_file_count": 4,
        "shared_manifest_reference_count": 1,
        "shared_manifest_reference_contract_passed": True,
        "blocking_reasons": (),
    }


def test_tracked_successor_reference_count_is_five() -> None:
    assert policy.EXPECTED_TRACKED_SUCCESSOR_REFERENCE_COUNT == 5
    assert _tracked_path_result()["tracked_successor_reference_count"] == 5


def test_validated_successor_reference_count_is_five() -> None:
    assert _tracked_path_result()["validated_reference_count"] == 5


def test_unique_successor_manifest_path_count_is_four() -> None:
    assert policy.EXPECTED_UNIQUE_TRACKED_SUCCESSOR_MANIFEST_COUNT == 4
    assert _tracked_path_result()["unique_manifest_path_count"] == 4


def test_unique_regular_successor_manifest_count_is_four() -> None:
    assert _tracked_path_result()["unique_regular_file_count"] == 4


def test_shared_manifest_reference_count_is_one() -> None:
    assert _tracked_path_result()["shared_manifest_reference_count"] == 1


def test_expected_shared_manifest_stage_set_is_exact() -> None:
    expected_path = next(
        iter(policy.EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES)
    )
    assert policy.EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES == {
        expected_path: (
            "covapie_split_leakage_smoke_v0",
            "covapie_split_leakage_qa_gate_v0",
        )
    }
    assert _tracked_path_result()[
        "shared_manifest_reference_contract_passed"
    ] is True


def test_unexpected_second_shared_manifest_is_blocked() -> None:
    items = list(_policies())
    items[0] = replace(
        items[0],
        superseded_by_manifest_path=items[1].superseded_by_manifest_path,
    )
    result = policy.validate_tracked_successor_manifest_paths(
        items,
        repo_root=REPO_ROOT,
    )
    assert result["tracked_successor_paths_passed"] is False
    assert any(
        reason.startswith("tracked_successor_unexpected_shared_manifest:")
        for reason in result["blocking_reasons"]
    )


def test_third_stage_joining_step14aq_share_is_blocked() -> None:
    items = list(_policies())
    items[0] = replace(
        items[0],
        superseded_by_manifest_path=items[2].superseded_by_manifest_path,
    )
    result = policy.validate_tracked_successor_manifest_paths(
        items,
        repo_root=REPO_ROOT,
    )
    expected_path = items[2].superseded_by_manifest_path
    assert result["tracked_successor_paths_passed"] is False
    assert (
        f"tracked_successor_shared_stage_set_mismatch:{expected_path}"
        in result["blocking_reasons"]
    )


def test_shared_stages_moved_to_different_path_are_blocked() -> None:
    items = list(_policies())
    replacement_path = items[1].superseded_by_manifest_path
    items[2] = replace(items[2], superseded_by_manifest_path=replacement_path)
    items[3] = replace(items[3], superseded_by_manifest_path=replacement_path)
    result = policy.validate_tracked_successor_manifest_paths(
        items,
        repo_root=REPO_ROOT,
    )
    assert result["tracked_successor_paths_passed"] is False
    assert any(
        reason.startswith("tracked_successor_unexpected_shared_manifest:")
        for reason in result["blocking_reasons"]
    )
    assert any(
        reason.startswith("tracked_successor_shared_stage_set_mismatch:")
        for reason in result["blocking_reasons"]
    )


def test_step14ar_manifest_missing_blocks_tracked_path_validation() -> None:
    items = list(_policies())
    items[4] = replace(
        items[4],
        superseded_by_manifest_path=(
            "data/derived/covalent_small/"
            "covapie_final_dataset_materialization_smoke_v0/missing.json"
        ),
    )
    result = policy.validate_tracked_successor_manifest_paths(
        items,
        repo_root=REPO_ROOT,
    )
    assert result["tracked_successor_paths_passed"] is False
    assert (
        "covapie_final_dataset_smoke_v0:manifest_path_missing"
        in result["blocking_reasons"]
    )


def test_step14ar_manifest_not_regular_file_blocks_validation() -> None:
    items = list(_policies())
    items[4] = replace(
        items[4],
        superseded_by_manifest_path=(
            "data/derived/covalent_small/"
            "covapie_final_dataset_materialization_smoke_v0"
        ),
    )
    result = policy.validate_tracked_successor_manifest_paths(
        items,
        repo_root=REPO_ROOT,
    )
    assert result["tracked_successor_paths_passed"] is False
    assert (
        "covapie_final_dataset_smoke_v0:manifest_path_not_regular_file"
        in result["blocking_reasons"]
    )


def test_stage_specific_checks_do_not_freeze_global_counts() -> None:
    forbidden_patterns = (
        *(rf'\["{field}"\]\s*==\s*\d+' for field in (
            "tracked_successor_reference_count",
            "validated_reference_count",
            "unique_manifest_path_count",
            "unique_regular_file_count",
        )),
        r"len\(policies\)\s*==\s*\d+",
    )
    for script in STAGE_CHECK_SCRIPTS:
        text = script.read_text(encoding="utf-8")
        assert all(re.search(pattern, text) is None for pattern in forbidden_patterns)


def test_stage_specific_checks_require_registry_count_validation() -> None:
    for script in STAGE_CHECK_SCRIPTS:
        text = script.read_text(encoding="utf-8")
        assert "validation.registry_count_passed is True" in text


def test_tracked_parent_reference_is_rejected() -> None:
    items = list(_policies())
    items[0] = replace(items[0], superseded_by_manifest_path="../outside.json")
    result = policy.validate_tracked_successor_manifest_paths(
        items,
        repo_root=REPO_ROOT,
    )
    assert result["tracked_successor_paths_passed"] is False
    assert any("parent_reference" in reason for reason in result["blocking_reasons"])


def test_tracked_absolute_path_is_rejected() -> None:
    items = list(_policies())
    items[0] = replace(items[0], superseded_by_manifest_path="/tmp/outside.json")
    result = policy.validate_tracked_successor_manifest_paths(
        items,
        repo_root=REPO_ROOT,
    )
    assert result["tracked_successor_paths_passed"] is False
    assert any("not_relative" in reason for reason in result["blocking_reasons"])


def test_builder_and_registry_validation_create_no_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    before = tuple(tmp_path.rglob("*"))
    built = policy.build_all_legacy_stage_retirement_policies()
    result = policy.validate_legacy_pipeline_retirement_registry(built)
    after = tuple(tmp_path.rglob("*"))
    assert result.passed is True
    assert before == after == ()


def test_legacy_derived_roots_remain_unchanged() -> None:
    paths = tuple(Path("data/derived/covalent_small") / name for name in LEGACY_ROOT_NAMES)
    before = _tree_hash(paths)
    policy.validate_legacy_pipeline_retirement_registry(_policies())
    after = _tree_hash(paths)
    assert before == after


def test_step14ar_files_remain_unchanged() -> None:
    before = _tree_hash(STEP14AR_FILES)
    policy.validate_legacy_pipeline_retirement_registry(_policies())
    after = _tree_hash(STEP14AR_FILES)
    assert before == after


def test_policy_module_does_not_import_legacy_or_runtime_modules() -> None:
    module_text = Path(
        "src/covalent_ext/covapie_legacy_pipeline_retirement_policy.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "equivariant_diffusion",
        "lightning_modules",
        "dataset.py",
        "torch",
        "rdkit",
        "gemmi",
        "Bio.PDB",
        "subprocess",
    ):
        assert forbidden not in module_text


def test_check_script_is_read_only() -> None:
    script = Path("scripts/check_covapie_legacy_pipeline_retirement_policy_v0.py")
    text = script.read_text(encoding="utf-8")
    for forbidden in (
        "write_text",
        "write_bytes",
        "open(",
        "mkdir",
        "subprocess",
    ):
        assert forbidden not in text


def test_check_script_reports_success_without_data_outputs() -> None:
    data_root = REPO_ROOT / "data/derived/covalent_small"
    before = _tree_hash((data_root,))
    result = subprocess.run(
        [sys.executable, "scripts/check_covapie_legacy_pipeline_retirement_policy_v0.py"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    after = _tree_hash((data_root,))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "covapie_legacy_pipeline_retirement_policy_v0_passed" in result.stdout
    assert before == after


def test_check_script_reports_reference_and_unique_counts_truthfully() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_covapie_legacy_pipeline_retirement_policy_v0.py"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "legacy_retirement_stage_count=13" in result.stdout
    assert "tracked_count=5" in result.stdout
    assert "pending_commit_count=0" in result.stdout
    assert "not_materialized_count=1" in result.stdout
    assert "redesign_pending_count=7" in result.stdout
    assert "tracked_successor_reference_count=5" in result.stdout
    assert "validated_successor_reference_count=5" in result.stdout
    assert "unique_successor_manifest_count=4" in result.stdout
    assert "unique_regular_successor_manifest_count=4" in result.stdout
    assert "shared_manifest_reference_count=1" in result.stdout
    assert "shared_manifest_reference_contract_passed=true" in result.stdout
    assert "regular_file_count" not in result.stdout
