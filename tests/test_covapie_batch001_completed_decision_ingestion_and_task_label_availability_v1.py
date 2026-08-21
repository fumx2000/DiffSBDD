from __future__ import annotations

import ast
import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from covalent_ext import covapie_bulk_500_event_executor_v1 as executor
from covalent_ext import (
    covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)
from covalent_ext import (
    covapie_cumulative_500_supported_post_only_two_rule_routing_v1 as cumulative,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / subject.OUTPUT_ROOT_RELATIVE
BATCH_ROOT = ROOT.parent / subject.BATCH_ROOT_RELATIVE_TO_REPOSITORY_PARENT

CHECKER_SPEC = importlib.util.spec_from_file_location(
    "check_batch001_successor_v1",
    ROOT
    / "scripts/"
    "check_covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1.py",
)
assert CHECKER_SPEC is not None and CHECKER_SPEC.loader is not None
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _repository_observation(**overrides: object) -> dict[str, object]:
    observation: dict[str, object] = {
        "branch": "main",
        "head": checker.BASELINE_COMMIT,
        "origin_main": checker.BASELINE_COMMIT,
        "ahead": 0,
        "behind": 0,
        "baseline_ancestor_of_head": True,
        "baseline_ancestor_of_origin_main": True,
        "modified_tracked_paths": (),
        "staged_paths": (),
        "untracked_paths": tuple(sorted(subject.AUTHORIZED_PUBLICATION_PATHS)),
        "tracked_candidate_paths": (),
    }
    observation.update(overrides)
    return observation


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return subject.build_artifacts_v1(ROOT)


@pytest.fixture(scope="module")
def state(artifacts: dict[str, bytes]) -> dict[str, object]:
    return {
        "snapshot": json.loads(artifacts[subject.SNAPSHOT]),
        "manifest": json.loads(artifacts[subject.MANIFEST]),
        "summary": json.loads(artifacts[subject.SUMMARY]),
        "rows": _rows(artifacts[subject.MATRIX]),
    }


def test_exact_seven_file_publication_scope() -> None:
    assert len(subject.AUTHORIZED_PUBLICATION_PATHS) == 7
    assert subject.AUTHORIZED_PUBLICATION_PATHS == {
        subject.SOURCE_PATH,
        subject.CHECKER_PATH,
        subject.TEST_PATH,
        *(path.as_posix() for path in (
            subject.OUTPUT_ROOT_RELATIVE / subject.SNAPSHOT,
            subject.OUTPUT_ROOT_RELATIVE / subject.MATRIX,
            subject.OUTPUT_ROOT_RELATIVE / subject.MANIFEST,
            subject.OUTPUT_ROOT_RELATIVE / subject.SUMMARY,
        )),
    }
    assert {path.name for path in OUTPUT.iterdir() if path.is_file()} == set(
        subject.OUTPUT_FILENAMES
    )


def test_current_repository_has_exact_lifecycle_profile() -> None:
    observation = checker.observe_repository_state_v1(ROOT)
    expected = (
        checker.PRECOMMIT_PROFILE
        if observation["head"] == checker.BASELINE_COMMIT
        else checker.PUBLISHED_PROFILE
    )
    assert checker.verify_repository_state_v1(ROOT) == expected


def test_synthetic_published_clean_descendant_is_accepted() -> None:
    descendant = "d" * 40
    assert checker.validate_repository_observation_v1(
        _repository_observation(
            head=descendant,
            origin_main=descendant,
            untracked_paths=(),
            tracked_candidate_paths=tuple(sorted(subject.AUTHORIZED_PUBLICATION_PATHS)),
        )
    ) == checker.PUBLISHED_PROFILE


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"branch": "feature"}, "BRANCH_NOT_MAIN"),
        ({"origin_main": "e" * 40}, "HEAD_ORIGIN_MAIN_MISMATCH"),
        ({"ahead": 1}, "AHEAD_BEHIND_NOT_ZERO_ZERO"),
        ({"behind": 1}, "AHEAD_BEHIND_NOT_ZERO_ZERO"),
        ({"baseline_ancestor_of_head": False}, "BASELINE_NOT_ANCESTOR_OF_HEAD"),
        ({"modified_tracked_paths": ("tracked.py",)}, "MODIFIED_EXISTING_TRACKED_FILES_PRESENT"),
        ({"staged_paths": ("staged.py",)}, "STAGED_FILES_PRESENT"),
        ({"untracked_paths": ("extra.txt",)}, "CANDIDATE_LIFECYCLE_PROFILE_INVALID"),
    ),
)
def test_repository_lifecycle_fails_closed(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match="^" + message + "$"):
        checker.validate_repository_observation_v1(
            _repository_observation(**overrides)
        )


def test_exact_external_batch_top_level_and_template_sha_bindings() -> None:
    snapshot = subject.snapshot_external_workspace_v1(BATCH_ROOT)
    assert len(snapshot) == 23
    assert sum(path.endswith("review_packet_v1.json") for path in snapshot) == 10
    assert sum(path.endswith("review_template_v1.json") for path in snapshot) == 10
    for name, expected in subject.BATCH_TOP_LEVEL_BINDINGS.items():
        assert snapshot[name] == expected
    for unit_id, expected in subject.TEMPLATE_SHA256.items():
        assert snapshot[f"{unit_id}/review_template_v1.json"] == expected
    for unit_id, expected in subject.PACKET_SHA256.items():
        assert snapshot[f"{unit_id}/review_packet_v1.json"] == expected


def test_changed_external_template_sha_fails_closed(tmp_path: Path) -> None:
    copy_root = tmp_path / "batch-001"
    shutil.copytree(BATCH_ROOT, copy_root)
    target = (
        copy_root
        / "COVAPIE_BULK_REVIEW_UNIT_5720D0B933DA07F1"
        / "review_template_v1.json"
    )
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(
        ValueError,
        match="^BOUND_INPUT_SHA256_MISMATCH:"
        "COVAPIE_BULK_REVIEW_UNIT_5720D0B933DA07F1:template$",
    ):
        subject.verify_bound_inputs_v1(ROOT, batch_root=copy_root)


def test_deterministic_double_build_and_persisted_bytes(
    artifacts: dict[str, bytes]
) -> None:
    assert subject.build_artifacts_v1(ROOT) == artifacts
    assert subject.build_artifacts_v1(ROOT) == artifacts
    for name in subject.OUTPUT_FILENAMES:
        assert (OUTPUT / name).read_bytes() == artifacts[name]


def test_snapshot_and_matrix_are_byte_identical_to_pre_revision(
    artifacts: dict[str, bytes]
) -> None:
    assert _sha256(artifacts[subject.SNAPSHOT]) == subject.PRE_REVISION_SNAPSHOT_SHA256
    assert _sha256(artifacts[subject.MATRIX]) == subject.PRE_REVISION_MATRIX_SHA256
    assert _sha256((OUTPUT / subject.SNAPSHOT).read_bytes()) == (
        "c0c887b9026638484ae453d68a6fc654e3bd1b3bce7aa222f8a285d4878e0200"
    )
    assert _sha256((OUTPUT / subject.MATRIX).read_bytes()) == (
        "f8481147babbad02215c3c3f767fe22ba6a511b8a076482a9635fec5d5cf8e82"
    )


def test_exact_nine_completed_units_and_onl_exclusion(
    state: dict[str, object]
) -> None:
    snapshot = state["snapshot"]
    decisions = snapshot["completed_human_decisions"]
    assert len(decisions) == 9
    assert [item["review_unit_id"] for item in decisions] == [
        unit_id
        for unit_id in subject.EXPECTED_SELECTION_ORDER
        if unit_id != subject.HELD_OUT_UNIT_ID
    ]
    assert sum(len(item["human_decision"]["events"]) for item in decisions) == 37
    assert subject.HELD_OUT_UNIT_ID not in {item["review_unit_id"] for item in decisions}
    assert snapshot["held_out_in_progress"] == {
        "review_unit_id": subject.HELD_OUT_UNIT_ID,
        "source_template_sha256": subject.TEMPLATE_SHA256[subject.HELD_OUT_UNIT_ID],
        "workflow_status": "IN_PROGRESS",
        "task_domain_relevance_decision_preserved_externally": subject.RELEVANT,
        "held_out_in_progress_unit_count": 1,
        "held_out_in_progress_event_count": 9,
        "held_out_reason": subject.HELD_OUT_REASON,
        "ONL_ingested": False,
    }
    assert not any(":ONL:" in row["canonical_event_id"] for row in state["rows"])


def test_completed_decisions_are_exact_template_copies(
    state: dict[str, object]
) -> None:
    bound = subject.verify_bound_inputs_v1(ROOT)
    for item in state["snapshot"]["completed_human_decisions"]:
        unit_id = item["review_unit_id"]
        assert item["source_template_sha256"] == subject.TEMPLATE_SHA256[unit_id]
        assert item["human_decision"] == bound["templates"][unit_id]
        assert item["human_decision"]["reviewer_id"]
        assert item["human_decision"]["reviewed_at_utc"]
        assert item["human_decision"]["review_rationale"]


def test_exact_five_positive_chemistry_labels(state: dict[str, object]) -> None:
    decisions = {
        item["review_unit_id"]: item["human_decision"]
        for item in state["snapshot"]["completed_human_decisions"]
    }
    assert set(subject.POSITIVE_UNITS) <= set(decisions)
    for unit_id, expected in subject.POSITIVE_UNITS.items():
        decision = decisions[unit_id]
        assert decision["workflow_status"] == "COMPLETED"
        assert decision["training_domain_relevance_decision"] == subject.RELEVANT
        assert decision["reactive_atom_confirmation"] == {
            "status": "CONFIRMED",
            "confirmed_atom_id": expected["ligand_reactive_atom"],
        }
        assert decision["roles"] == expected["roles"]
        assert decision["warhead_atom_ids"] == expected["roles"]["warhead_atom_ids"]
        assert decision["warhead_family_decision"]["decision"] == (
            "NEW_WARHEAD_FAMILY_REQUIRES_AUTHORITY_REVIEW"
        )
        assert decision["warhead_family_decision"]["canonical_reaction_family_id"] == ""
        assert all(
            event["post_geometry_training_usable"] == "YES"
            and event["event_training_use_decision"] == "INCLUDE"
            for event in decision["events"]
        )


def test_px5_corrected_partition_is_frozen(state: dict[str, object]) -> None:
    px5_unit = "COVAPIE_BULK_REVIEW_UNIT_F02164FD5061B6D5"
    decision = next(
        item["human_decision"]
        for item in state["snapshot"]["completed_human_decisions"]
        if item["review_unit_id"] == px5_unit
    )
    assert decision["roles"] == {
        "warhead_atom_ids": ["C10", "C11", "C12", "C13", "C14", "C15", "O16", "O17"],
        "linker_atom_ids": [],
        "scaffold_atom_ids": ["C1", "C2", "C3", "C4", "C5", "C6", "C8", "N9", "S7"],
    }
    assert decision["roles"]["warhead_atom_ids"] != ["C11", "C12", "C13", "C14", "C15", "O17"]
    assert decision["roles"]["linker_atom_ids"] != ["C10", "O16"]


def test_px5_severed_ring_regression_fails_validation(
    state: dict[str, object]
) -> None:
    unit_id = "COVAPIE_BULK_REVIEW_UNIT_F02164FD5061B6D5"
    bound = subject.verify_bound_inputs_v1(ROOT)
    altered = copy.deepcopy(bound["templates"][unit_id])
    altered["roles"] = {
        "warhead_atom_ids": ["C11", "C12", "C13", "C14", "C15", "O17"],
        "linker_atom_ids": ["C10", "O16"],
        "scaffold_atom_ids": altered["roles"]["scaffold_atom_ids"],
    }
    with pytest.raises(
        ValueError, match="^COMPLETED_POSITIVE_TEMPLATE_INVALID:"
        + unit_id
        + "$"
    ):
        subject._validate_positive_template(
            unit_id, altered, bound["packets"][unit_id], bound["inventory"]
        )


def test_negative_decisions_preserve_blank_chemistry(
    state: dict[str, object]
) -> None:
    decisions = {
        item["review_unit_id"]: item["human_decision"]
        for item in state["snapshot"]["completed_human_decisions"]
    }
    for unit_id in subject.NEGATIVE_UNITS:
        decision = decisions[unit_id]
        assert decision["workflow_status"] == "COMPLETED"
        assert decision["training_domain_relevance_decision"] == subject.NOT_RELEVANT
        assert decision["reactive_atom_confirmation"] is None
        assert decision["warhead_family_decision"] is None
        assert decision["warhead_atom_ids"] == []
        assert decision["roles"] == {
            "linker_atom_ids": [],
            "scaffold_atom_ids": [],
            "warhead_atom_ids": [],
        }
        assert all(
            event["event_exclusion_reason"] is None
            and event["event_training_use_decision"] is None
            and event["post_geometry_training_usable"] is None
            for event in decision["events"]
        )


def test_fabricated_negative_event_decision_fails_validation() -> None:
    unit_id = "COVAPIE_BULK_REVIEW_UNIT_BE9EC76A77B78516"
    bound = subject.verify_bound_inputs_v1(ROOT)
    altered = copy.deepcopy(bound["templates"][unit_id])
    altered["events"][0]["event_training_use_decision"] = "EXCLUDE"
    with pytest.raises(
        ValueError,
        match="^NEGATIVE_EVENT_FIELDS_NOT_BLANK:",
    ):
        subject._validate_negative_template(
            unit_id, altered, bound["packets"][unit_id], bound["inventory"]
        )


def test_matrix_exact_split_and_core_availability(state: dict[str, object]) -> None:
    rows = state["rows"]
    assert len(rows) == 37
    assert len({row["canonical_event_id"] for row in rows}) == 37
    positive = [row for row in rows if row["completed_lane"] == "COMPLETED_POSITIVE_CHEMISTRY"]
    negative = [row for row in rows if row["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"]
    assert (len(positive), len(negative)) == (13, 24)
    assert all(row["positive_generative_supervision_eligible"] == "true" for row in positive)
    assert all(row["reactive_atom_pair_label_available"] == "true" for row in positive)
    assert all(row["protein_reactive_atom"] == "SG" for row in positive)
    assert all(row["warhead_atom_set_label_available"] == "true" for row in positive)
    assert all(row["role_partition_label_available"] == "true" for row in positive)
    assert all(row["post_geometry_usability_label_available"] == "true" for row in positive)
    assert all(row["post_geometry_training_usable"] == "YES" for row in positive)
    assert all(row["event_training_use_label_available"] == "true" for row in positive)
    assert all(row["event_training_use_decision"] == "INCLUDE" for row in positive)
    assert all(row["task_domain_relevance_label"] == subject.NOT_RELEVANT for row in negative)


def test_negative_matrix_rows_have_no_fabricated_chemistry(
    state: dict[str, object]
) -> None:
    negative = [
        row
        for row in state["rows"]
        if row["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
    ]
    blank_fields = (
        "protein_reactive_atom",
        "ligand_reactive_atom",
        "warhead_atom_ids_json",
        "scaffold_atom_ids_json",
        "linker_atom_ids_json",
        "role_warhead_atom_ids_json",
        "post_geometry_training_usable",
        "event_training_use_decision",
        "canonical_reaction_family_id",
        "proposed_family_label_non_authoritative",
    )
    false_fields = (
        "reactive_atom_pair_label_available",
        "warhead_atom_set_label_available",
        "role_partition_label_available",
        "post_geometry_usability_label_available",
        "event_training_use_label_available",
    )
    assert all(all(row[field] == "" for field in blank_fields) for row in negative)
    assert all(all(row[field] == "false" for field in false_fields) for row in negative)


def test_family_and_warhead_type_targets_fail_closed(
    state: dict[str, object]
) -> None:
    rows = state["rows"]
    assert all(row["approved_canonical_reaction_family_target_available"] == "false" for row in rows)
    assert all(row["canonical_reaction_family_id"] == "" for row in rows)
    assert all(row["proposed_family_label_is_training_class_target"] == "false" for row in rows)
    assert all(row["warhead_type_classification_target_available"] == "false" for row in rows)
    assert all(row["warhead_type_classification_target_id"] == "" for row in rows)
    manifest = state["manifest"]
    interpretation = manifest["warhead_type_classification_interpretation"]
    assert interpretation["approved_family_target_available_event_count"] == 0
    assert interpretation["current_warhead_type_vocabulary_frozen"] is False
    assert interpretation["proposed_family_label_is_sufficient_training_class_authority"] is False
    assert interpretation["new_class_ids_created"] is False


def test_current_feature_semantics_resolution_is_bound_and_resolved(
    state: dict[str, object]
) -> None:
    manifest = state["manifest"]
    expected_bindings = {
        path: {"path": path, "sha256": sha256}
        for path, sha256 in subject.CURRENT_FEATURE_SEMANTICS_RESOLUTION_BINDINGS.items()
    }
    assert manifest["current_feature_semantics_resolution_bindings"] == expected_bindings
    owner_path = ROOT / (
        "data/derived/covalent_small/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json"
    )
    owner = json.loads(owner_path.read_bytes())
    assert {
        field: owner[field]
        for field in subject.CURRENT_FEATURE_SEMANTICS_RESOLUTION
    } == subject.CURRENT_FEATURE_SEMANTICS_RESOLUTION
    assert manifest["current_feature_semantics_resolution"] == {
        **subject.CURRENT_FEATURE_SEMANTICS_RESOLUTION,
        "feature_semantics_reopened": False,
    }
    subject._validate_current_feature_semantics_resolution(ROOT)


@pytest.mark.parametrize(
    "claim",
    subject.STALE_FEATURE_SEMANTICS_CLAIMS[:7],
)
def test_stale_feature_semantics_claims_are_absent_and_rejected(
    artifacts: dict[str, bytes], claim: str
) -> None:
    for name in subject.OUTPUT_FILENAMES:
        assert claim not in artifacts[name].decode("utf-8")
    with pytest.raises(
        ValueError, match="^STALE_FEATURE_SEMANTICS_CLAIM_PRESENT:"
    ):
        subject.reject_stale_feature_semantics_claims_v1({"invalid_claim": claim})


def test_feature_semantics_known_cannot_regress_false(
    state: dict[str, object]
) -> None:
    altered = copy.deepcopy(state["manifest"])
    altered["feature_semantics_known"] = False
    with pytest.raises(
        ValueError, match="^STALE_FEATURE_SEMANTICS_CLAIM_PRESENT:"
    ):
        subject.reject_stale_feature_semantics_claims_v1(altered)


def test_unknown_atom_policy_cannot_regress_false(
    state: dict[str, object]
) -> None:
    altered = copy.deepcopy(state["manifest"])
    altered["unknown_atom_feature_policy_resolved"] = False
    with pytest.raises(
        ValueError, match="^STALE_FEATURE_SEMANTICS_CLAIM_PRESENT:"
    ):
        subject.reject_stale_feature_semantics_claims_v1(altered)


def test_label_snapshot_baseline_mask_runtime_binding_and_nonempty_guard(
    state: dict[str, object]
) -> None:
    manifest = state["manifest"]
    expected = dict(subject.MASK_RUNTIME_OBSERVATION_AT_LABEL_SNAPSHOT_BASELINE)
    assert manifest["mask_runtime_observation_at_label_snapshot_baseline"] == expected
    assert checker.verify_label_snapshot_baseline_mask_runtime_v1(ROOT) == expected
    object_name = (
        subject.LABEL_SNAPSHOT_BASELINE_COMMIT
        + ":"
        + subject.LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_PATH
    )
    payload = subprocess.run(
        ["git", "show", object_name],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    assert _sha256(payload) == subject.LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_SHA256
    subject.validate_mask_runtime_observation_blob_v1(payload)
    tree = ast.parse(payload)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "build_long_form_mask"
    )
    call = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_validate_partition"
    )
    keyword = next(
        keyword
        for keyword in call.keywords
        if keyword.arg == "require_nonempty_regions"
    )
    assert isinstance(keyword.value, ast.Constant)
    assert keyword.value.value is True


def test_label_snapshot_baseline_mask_runtime_validation_fails_closed() -> None:
    object_name = (
        subject.LABEL_SNAPSHOT_BASELINE_COMMIT
        + ":"
        + subject.LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_PATH
    )
    payload = subprocess.run(
        ["git", "show", object_name],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    altered = payload.replace(
        b"require_nonempty_regions=True,",
        b"require_nonempty_regions=False,",
        1,
    )
    assert altered != payload
    with pytest.raises(
        ValueError,
        match="^LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_NONEMPTY_REGION_GUARD_MISSING$",
    ):
        subject.validate_mask_runtime_observation_blob_v1(altered)
    with pytest.raises(
        ValueError,
        match="^LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_BLOB_INVALID$",
    ):
        subject.validate_mask_runtime_observation_blob_v1(
            b"def build_long_form_mask():\n    return None\n"
        )


def test_future_masking_runtime_successor_does_not_invalidate_snapshot(
    artifacts: dict[str, bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    descendant = "d" * 40
    assert checker.validate_repository_observation_v1(
        _repository_observation(
            head=descendant,
            origin_main=descendant,
            untracked_paths=(),
            tracked_candidate_paths=tuple(sorted(subject.AUTHORIZED_PUBLICATION_PATHS)),
        )
    ) == checker.PUBLISHED_PROFILE

    live_masking_path = (
        ROOT / subject.LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_PATH
    ).resolve()
    original_read_bytes = Path.read_bytes
    original_read_text = Path.read_text

    def guarded_read_bytes(path: Path) -> bytes:
        if path.resolve() == live_masking_path:
            raise AssertionError("builder read future live masking.py bytes")
        return original_read_bytes(path)

    def guarded_read_text(
        path: Path, encoding: str | None = None, errors: str | None = None
    ) -> str:
        if path.resolve() == live_masking_path:
            raise AssertionError("builder read future live masking.py text")
        return original_read_text(path, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    replayed = subject.build_artifacts_v1(ROOT)
    assert replayed == artifacts
    manifest = json.loads(replayed[subject.MANIFEST])
    assert manifest["PX5_five_mask_runtime_compatible_at_label_snapshot"] is False
    assert (
        manifest[
            "future_masking_runtime_successor_can_change_without_invalidating_snapshot"
        ]
        is True
    )
    assert manifest["mask_runtime_observation_at_label_snapshot_baseline"] == dict(
        subject.MASK_RUNTIME_OBSERVATION_AT_LABEL_SNAPSHOT_BASELINE
    )


def test_stage_local_unavailable_target_accounting_is_narrow(
    state: dict[str, object]
) -> None:
    rows = state["manifest"]["stage_local_unavailable_target_accounting"]
    assert [row["status_id"] for row in rows] == [
        "FAMILY_DEPENDENT_CLASSIFICATION_AUTHORITY_UNAVAILABLE",
        "PX5_LABEL_SNAPSHOT_BASELINE_FIVE_MASK_RUNTIME_REQUIRES_NONEMPTY_LINKER_REGION",
    ]
    assert rows[0]["positive_event_count"] == 13
    assert rows[0]["approved_family_target_available_event_count"] == 0
    assert rows[0]["warhead_type_classification_available_event_count"] == 0
    assert rows[0]["handled_by_per_task_masking"] is True
    assert rows[0]["other_positive_supervision_blocked"] is False
    assert rows[1]["ligand_component_id"] == "PX5"
    assert rows[1]["event_count"] == 2
    assert rows[1]["linker_atom_ids"] == []
    assert rows[1]["human_role_partition_valid"] is True
    assert rows[1]["all_five_masks_available_at_label_snapshot"] is False
    assert rows[1]["gap_type"] == "MODEL_CONTRACT_EMPTY_LINKER_COMPATIBILITY_GAP"
    assert rows[1]["chemistry_invalid"] is False
    assert rows[1]["training_domain_invalid"] is False
    assert rows[1]["family_problem"] is False
    assert rows[1]["ONL_problem"] is False


def test_current_five_mask_contract_binding_and_availability(
    state: dict[str, object]
) -> None:
    manifest = state["manifest"]
    assert [
        (row["semantic_name"], row["display_alias"])
        for row in manifest["canonical_five_mask_semantics"]
    ] == [
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    ]
    rows = state["rows"]
    columns = (
        "mask_A_warhead_only_available",
        "mask_B_linker_plus_warhead_available",
        "mask_B2_scaffold_plus_warhead_available",
        "mask_B3_scaffold_only_available",
        "mask_C_scaffold_plus_linker_plus_warhead_available",
    )
    assert [sum(row[column] == "true" for row in rows) for column in columns] == [11] * 5
    px5 = [row for row in rows if ":PX5:" in row["canonical_event_id"]]
    assert len(px5) == 2
    assert all(all(row[column] == "false" for column in columns) for row in px5)
    other_positive = [
        row
        for row in rows
        if row["completed_lane"] == "COMPLETED_POSITIVE_CHEMISTRY"
        and ":PX5:" not in row["canonical_event_id"]
    ]
    assert len(other_positive) == 11
    assert all(all(row[column] == "true" for column in columns) for row in other_positive)
    assert manifest["mask_derivation_interpretation"] == {
        "primary_role_regions_nonempty_required_at_label_snapshot_baseline": True,
        "label_snapshot_baseline_build_long_form_mask_require_nonempty_regions": True,
        "PX5_human_role_partition_valid_for_chemistry_snapshot": True,
        "PX5_linker_atom_ids": [],
        "PX5_five_mask_runtime_compatible_at_label_snapshot": False,
        "PX5_failure_reason": (
            "LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_REQUIRES_ALL_PRIMARY_ROLE_REGIONS_NONEMPTY"
        ),
        "PX5_human_role_labels_modified": False,
        "PX5_mask_unavailable_event_count": 2,
        "other_positive_event_all_five_mask_targets_available_at_label_snapshot_count": 11,
        "future_mask_runtime_may_legitimately_support_empty_linker": True,
        "historical_snapshot_dictates_future_runtime_semantics": False,
    }


def test_available_mask_targets_are_exact_role_unions(
    state: dict[str, object]
) -> None:
    decisions = {
        item["review_unit_id"]: item["human_decision"]
        for item in state["snapshot"]["completed_human_decisions"]
    }
    fields = {
        "A": "mask_A_warhead_only_target_atom_ids_json",
        "B": "mask_B_linker_plus_warhead_target_atom_ids_json",
        "B2": "mask_B2_scaffold_plus_warhead_target_atom_ids_json",
        "B3": "mask_B3_scaffold_only_target_atom_ids_json",
        "C": "mask_C_scaffold_plus_linker_plus_warhead_target_atom_ids_json",
    }
    for row in state["rows"]:
        if row["mask_A_warhead_only_available"] != "true":
            continue
        expected = subject._mask_targets(decisions[row["review_unit_id"]]["roles"])
        assert {alias: json.loads(row[field]) for alias, field in fields.items()} == expected


def test_post_only_positive_is_not_blocked_by_unavailable_pre_or_family(
    state: dict[str, object]
) -> None:
    positive = [
        row
        for row in state["rows"]
        if row["completed_lane"] == "COMPLETED_POSITIVE_CHEMISTRY"
    ]
    assert all(row["positive_generative_supervision_eligible"] == "true" for row in positive)
    assert all(row["experimental_pre_geometry_target_available"] == "false" for row in positive)
    assert all(row["approved_canonical_reaction_family_target_available"] == "false" for row in positive)
    contract = state["manifest"]["model_integration_contract"]
    assert contract["missing_family_class_authority_handled_by_per_task_masking"] is True
    assert contract["valid_positive_post_samples_removed_for_missing_family_authority"] is False
    assert contract["valid_positive_post_samples_removed_for_missing_experimental_PRE"] is False
    assert contract["valid_positive_post_only_model_integration_design_input_count"] == 13
    assert (
        contract[
            "all_five_mask_runtime_compatible_at_label_snapshot_event_count"
        ]
        == 11
    )
    assert contract["empty_linker_runtime_gap_at_label_snapshot_event_count"] == 2
    assert (
        contract[
            "future_live_masking_runtime_may_change_without_invalidating_snapshot"
        ]
        is True
    )
    assert contract["batch_002_required_before_model_integration_design"] is False


def test_snapshot_counts_and_manifest_direct_evidence(state: dict[str, object]) -> None:
    assert state["snapshot"]["counts"] == {
        "unit_count": 9,
        "event_count": 37,
        "completed_positive_unit_count": 5,
        "completed_positive_event_count": 13,
        "completed_negative_unit_count": 4,
        "completed_negative_event_count": 24,
        "in_progress_units_ingested": 0,
        "duplicate_unit_count": 0,
        "duplicate_event_count": 0,
    }
    availability = state["manifest"]["availability_counts"]
    assert availability["row_count"] == 37
    assert availability["unique_event_count"] == 37
    assert availability["positive_rows"] == 13
    assert availability["negative_rows"] == 24
    assert availability["approved_canonical_reaction_family_available_rows"] == 0
    assert availability["negative_rows_with_fabricated_chemistry_label"] == 0


def test_no_runtime_git_state_timestamps_or_absolute_paths(
    artifacts: dict[str, bytes]
) -> None:
    forbidden_keys = {
        "head", "origin_main", "ahead", "behind", "build_timestamp",
        "runtime_timestamp", "mtime", "stat_tree_sha256", "current_wall_clock",
    }

    def walk(value: object) -> None:
        if isinstance(value, dict):
            assert not (set(value) & forbidden_keys)
            for key, item in value.items():
                assert not (isinstance(key, str) and key.startswith("/"))
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            assert not value.startswith(str(ROOT.parent))

    for name in (subject.SNAPSHOT, subject.MANIFEST, subject.SUMMARY):
        walk(json.loads(artifacts[name]))


def test_manifest_does_not_hash_itself_and_summary_hashes_outputs(
    artifacts: dict[str, bytes], state: dict[str, object]
) -> None:
    assert subject.MANIFEST not in state["manifest"]["artifact_bindings"]
    assert state["summary"]["artifact_sha256_excluding_summary"] == {
        subject.SNAPSHOT: _sha256(artifacts[subject.SNAPSHOT]),
        subject.MATRIX: _sha256(artifacts[subject.MATRIX]),
        subject.MANIFEST: _sha256(artifacts[subject.MANIFEST]),
    }


def test_predecessor_overlay_progress_and_routing_are_exact() -> None:
    for path, expected in subject.PUBLISHED_REPOSITORY_BINDINGS.items():
        assert _sha256((ROOT / path).read_bytes()) == expected


def test_attempt_001_and_canonical_cache_bound_read_only() -> None:
    attempt_root = ROOT.parent / cumulative.ATTEMPT_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    for name, expected in cumulative.ATTEMPT_BINDINGS.items():
        payload = (attempt_root / name).read_bytes()
        assert len(payload) == expected["byte_count"]
        assert _sha256(payload) == expected["sha256"]
    cache_root = executor.canonical_controlled_cache_root_v1(ROOT)
    before = executor.snapshot_cache_tree_v1(cache_root)
    assert _sha256((cache_root / "cache_manifest_v1.json").read_bytes()) == (
        cumulative.CACHE_LEDGER_SHA256
    )
    assert executor.snapshot_cache_tree_v1(cache_root) == before


def test_builder_has_no_git_network_or_training_runtime_dependency() -> None:
    source = (ROOT / subject.SOURCE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not ({"subprocess", "requests", "urllib", "socket", "torch"} & imports)
    assert "git rev-parse" not in source
    assert "CURRENT_MASK_RUNTIME_BINDINGS" not in source
    assert "_validate_current_mask_runtime" not in source
    assert "optimizer.step" not in source
    assert "backward(" not in source


def test_revised_readiness_markers_are_exact(state: dict[str, object]) -> None:
    expected = {
        "feature_semantics_audit_completed": True,
        "feature_semantics_known": True,
        "unknown_atom_feature_policy_resolved": True,
        "unknown_atom_policy_contract_resolved": True,
        "feature_semantics_reopened": False,
        "stale_feature_semantics_blocker_count": 0,
        "global_training_readiness_adjudicated_by_this_stage": False,
        "ready_for_training": False,
        "ready_for_training_reason": (
            "THIS_LABEL_AVAILABILITY_STAGE_DOES_NOT_AUTHORIZE_TRAINING"
        ),
        "ready_for_model_integration_design": True,
        "family_dependent_classification_target_available_event_count": 0,
        "PX5_empty_linker_human_label_preserved": True,
        "PX5_five_mask_runtime_compatible_at_label_snapshot": False,
        "PX5_mask_unavailable_event_count": 2,
        "batch001_successor_mask_runtime_binding_is_snapshot_scoped": True,
        "future_masking_runtime_successor_can_change_without_invalidating_snapshot": True,
        "mask_A_available_event_count": 11,
        "mask_B_available_event_count": 11,
        "mask_B2_available_event_count": 11,
        "mask_B3_available_event_count": 11,
        "mask_C_available_event_count": 11,
    }
    for artifact in (state["manifest"], state["summary"]):
        assert {field: artifact[field] for field in expected} == expected
    summary = state["summary"]
    assert summary["PX5_mask_incompatible_at_label_snapshot_event_count"] == 2
    for alias in ("A", "B", "B2", "B3", "C"):
        assert summary[f"snapshot_mask_{alias}_available_event_count"] == 11
    assert summary["stale_feature_semantics_blockers_removed"] is True
    assert summary["current_feature_semantics_resolution_bound"] is True
    assert summary["snapshot_byte_identical_to_pre_revision"] is True
    assert summary["matrix_byte_identical_to_pre_revision"] is True
    assert summary["precommit_candidate_profile_supported"] is True
    assert summary["published_clean_descendant_profile_supported"] is True
    assert summary["recommended_next_step_exactly"] == (
        "new_codex_conversation_design_empty_linker_compatible_five_module_"
        "model_integration_v1"
    )


def test_no_authority_batch002_tensorization_or_training(state: dict[str, object]) -> None:
    safety = state["manifest"]["safety"]
    assert safety == {
        "predecessor_human_overlay_modified": False,
        "predecessor_human_progress_modified": False,
        "external_batch_workspace_modified": False,
        "canonical_cache_modified": False,
        "attempt_001_modified": False,
        "family_authority_created": False,
        "production_authority_created": False,
        "batch_002_created": False,
        "tensorization_performed": False,
        "training_performed": False,
        "network_performed": False,
        "GPU_used": False,
        "checkpoint_read": False,
        "model_forward_performed": False,
        "loss_computation_performed": False,
        "optimizer_step_performed": False,
    }
    assert not (BATCH_ROOT.parent / "batch-002").exists()
    assert state["manifest"]["ready_for_gpt_review"] is True
    assert state["manifest"]["ready_for_model_integration_design"] is True
    assert state["manifest"]["ready_for_training"] is False
    assert state["manifest"]["ready_for_training_reason"] == (
        "THIS_LABEL_AVAILABILITY_STAGE_DOES_NOT_AUTHORIZE_TRAINING"
    )


def test_full_checker_passes() -> None:
    result = checker.check_v1(ROOT)
    assert result["repository_profile"] == checker.verify_repository_state_v1(ROOT)
    assert result["repository_profile"] in {
        checker.PRECOMMIT_PROFILE,
        checker.PUBLISHED_PROFILE,
    }
    assert result["completed_unit_snapshot_count"] == 9
    assert result["task_label_matrix_row_count"] == 37
    assert set(result["mask_counts"].values()) == {11}
    assert result["stale_feature_semantics_blockers_removed"] is True
    assert result["current_feature_semantics_resolution_bound"] is True
    assert result["snapshot_byte_identical_to_pre_revision"] is True
    assert result["matrix_byte_identical_to_pre_revision"] is True
    assert result["ready_for_model_integration_design"] is True
