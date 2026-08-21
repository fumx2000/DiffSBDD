#!/usr/bin/env python3
"""Fail-closed checker for the batch-001 completed-decision successor V1."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_bulk_500_event_executor_v1 as executor  # noqa: E402
from covalent_ext import (  # noqa: E402
    covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_cumulative_500_supported_post_only_two_rule_routing_v1 as cumulative,
)


BASELINE_COMMIT = "a2c47314eea20bdadf93c20faf08b3c1c68d4bd6"
PRECOMMIT_PROFILE = "BATCH001_COMPLETED_SUCCESSOR_PRECOMMIT_EXACT7_UNTRACKED"
PUBLISHED_PROFILE = "BATCH001_COMPLETED_SUCCESSOR_PUBLISHED_CLEAN_DESCENDANT"
PROTECTED_PATH_PREFIXES = (
    "data/raw/",
    "checkpoints/",
    "equivariant_diffusion/",
    "lightning_modules.py",
    "dataset.py",
    "data/prepare_crossdocked.py",
)
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".tmp", ".part",
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git(repo_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _git_bytes(repo_root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
    ).stdout


def verify_label_snapshot_baseline_mask_runtime_v1(
    repo_root: Path,
) -> dict[str, object]:
    """Verify the immutable a2c runtime blob, never the live runtime file."""

    object_name = (
        subject.LABEL_SNAPSHOT_BASELINE_COMMIT
        + ":"
        + subject.LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_PATH
    )
    subprocess.run(
        ["git", "cat-file", "-e", object_name],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    payload = _git_bytes(repo_root, "show", object_name)
    _assert(
        _sha256(payload) == subject.LABEL_SNAPSHOT_BASELINE_MASK_RUNTIME_SHA256,
        "label-snapshot baseline mask runtime SHA",
    )
    subject.validate_mask_runtime_observation_blob_v1(payload)
    return dict(subject.MASK_RUNTIME_OBSERVATION_AT_LABEL_SNAPSHOT_BASELINE)


def observe_repository_state_v1(repo_root: Path) -> dict[str, object]:
    head = _git(repo_root, "rev-parse", "HEAD")
    origin_main = _git(repo_root, "rev-parse", "origin/main")
    behind_text, ahead_text = _git(
        repo_root, "rev-list", "--left-right", "--count", "origin/main...HEAD"
    ).split()
    modified = tuple(
        line for line in _git(repo_root, "diff", "--name-only").splitlines() if line
    )
    staged = tuple(
        line
        for line in _git(repo_root, "diff", "--cached", "--name-only").splitlines()
        if line
    )
    untracked = tuple(
        sorted(
            line
            for line in _git(
                repo_root, "ls-files", "--others", "--exclude-standard"
            ).splitlines()
            if line
        )
    )
    tracked_candidates = tuple(
        sorted(
            line
            for line in _git(
                repo_root,
                "ls-files",
                "--",
                *sorted(subject.AUTHORIZED_PUBLICATION_PATHS),
            ).splitlines()
            if line
        )
    )
    return {
        "branch": _git(repo_root, "branch", "--show-current"),
        "head": head,
        "origin_main": origin_main,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "baseline_ancestor_of_head": subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, head],
            cwd=repo_root,
            check=False,
        ).returncode
        == 0,
        "baseline_ancestor_of_origin_main": subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, origin_main],
            cwd=repo_root,
            check=False,
        ).returncode
        == 0,
        "modified_tracked_paths": modified,
        "staged_paths": staged,
        "untracked_paths": untracked,
        "tracked_candidate_paths": tracked_candidates,
    }


def validate_repository_observation_v1(observation: Mapping[str, object]) -> str:
    if observation.get("branch") != "main":
        raise ValueError("BRANCH_NOT_MAIN")
    if observation.get("head") != observation.get("origin_main"):
        raise ValueError("HEAD_ORIGIN_MAIN_MISMATCH")
    if observation.get("ahead") != 0 or observation.get("behind") != 0:
        raise ValueError("AHEAD_BEHIND_NOT_ZERO_ZERO")
    if observation.get("baseline_ancestor_of_head") is not True:
        raise ValueError("BASELINE_NOT_ANCESTOR_OF_HEAD")
    if observation.get("baseline_ancestor_of_origin_main") is not True:
        raise ValueError("BASELINE_NOT_ANCESTOR_OF_ORIGIN_MAIN")
    if observation.get("modified_tracked_paths") != ():
        raise ValueError("MODIFIED_EXISTING_TRACKED_FILES_PRESENT")
    if observation.get("staged_paths") != ():
        raise ValueError("STAGED_FILES_PRESENT")

    untracked = tuple(observation.get("untracked_paths", ()))
    tracked = tuple(observation.get("tracked_candidate_paths", ()))
    exact = tuple(sorted(subject.AUTHORIZED_PUBLICATION_PATHS))
    if untracked == exact and tracked == ():
        return PRECOMMIT_PROFILE
    if (
        untracked == ()
        and tracked == exact
        and observation.get("head") != BASELINE_COMMIT
    ):
        return PUBLISHED_PROFILE
    raise ValueError("CANDIDATE_LIFECYCLE_PROFILE_INVALID")


def verify_repository_state_v1(repo_root: Path) -> str:
    return validate_repository_observation_v1(observe_repository_state_v1(repo_root))


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _assert(tuple(reader.fieldnames or ()) == subject.MATRIX_HEADER, "matrix header")
        rows = list(reader)
    _assert(
        all(tuple(row) == subject.MATRIX_HEADER and None not in row.values() for row in rows),
        "matrix row schema",
    )
    return rows


def _contains_absolute_path(value: object) -> bool:
    if isinstance(value, str):
        return os.path.isabs(value)
    if isinstance(value, list):
        return any(_contains_absolute_path(item) for item in value)
    if isinstance(value, Mapping):
        return any(
            _contains_absolute_path(key) or _contains_absolute_path(item)
            for key, item in value.items()
        )
    return False


def _contains_forbidden_runtime_key(value: object) -> bool:
    forbidden = {
        "head", "origin_main", "ahead", "behind", "build_timestamp",
        "runtime_timestamp", "mtime", "stat_tree_sha256", "current_wall_clock",
    }
    if isinstance(value, Mapping):
        return any(
            key in forbidden or _contains_forbidden_runtime_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_runtime_key(item) for item in value)
    return False


def _snapshot_attempt_001(repo_root: Path) -> dict[str, str]:
    attempt_root = repo_root.parent / cumulative.ATTEMPT_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    observed: dict[str, str] = {}
    _assert(
        {path.name for path in attempt_root.iterdir() if path.is_file()}
        == set(cumulative.ATTEMPT_BINDINGS),
        "attempt-001 exact file set",
    )
    for name, expected in cumulative.ATTEMPT_BINDINGS.items():
        payload = (attempt_root / name).read_bytes()
        _assert(len(payload) == expected["byte_count"], "attempt-001 byte count: " + name)
        digest = _sha256(payload)
        _assert(digest == expected["sha256"], "attempt-001 SHA: " + name)
        observed[name] = digest
    return observed


def _direct_matrix_checks(rows: Sequence[Mapping[str, str]]) -> dict[str, int]:
    _assert(len(rows) == 37, "matrix exact row count")
    _assert(len({row["canonical_event_id"] for row in rows}) == 37, "unique events")
    _assert(not any(":ONL:" in row["canonical_event_id"] for row in rows), "ONL absent")
    positive = [row for row in rows if row["completed_lane"] == "COMPLETED_POSITIVE_CHEMISTRY"]
    negative = [row for row in rows if row["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"]
    _assert((len(positive), len(negative)) == (13, 24), "13/24 lane split")

    for row in positive:
        _assert(row["task_domain_relevance_label_available"] == "true", "positive relevance available")
        _assert(row["task_domain_relevance_label"] == subject.RELEVANT, "positive relevance")
        _assert(row["positive_generative_supervision_eligible"] == "true", "positive eligible")
        _assert(row["reactive_atom_pair_label_available"] == "true", "positive pair available")
        _assert(row["protein_reactive_atom"] == "SG", "positive protein atom")
        _assert(row["ligand_reactive_atom"], "positive ligand atom")
        _assert(row["warhead_atom_set_label_available"] == "true", "positive warhead set")
        _assert(row["role_partition_label_available"] == "true", "positive roles")
        _assert(row["post_geometry_usability_label_available"] == "true", "positive post label")
        _assert(row["post_geometry_training_usable"] == "YES", "positive post usable")
        _assert(row["post_geometry_supervision_available"] == "true", "positive post supervision")
        _assert(row["event_training_use_label_available"] == "true", "positive use label")
        _assert(row["event_training_use_decision"] == "INCLUDE", "positive included")
        _assert(row["approved_canonical_reaction_family_target_available"] == "false", "family masked")
        _assert(row["canonical_reaction_family_id"] == "", "family id blank")
        _assert(row["proposed_family_label_non_authoritative"], "proposal provenance")
        _assert(row["proposed_family_label_is_training_class_target"] == "false", "proposal not class")
        _assert(row["warhead_type_classification_target_available"] == "false", "warhead type masked")
        _assert(row["warhead_type_classification_target_id"] == "", "warhead type id blank")
        _assert(row["production_family_authority_created"] == "false", "no family authority")
        _assert(row["experimental_pre_geometry_target_available"] == "false", "PRE unavailable")

    chemistry_fields = (
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
        "warhead_type_classification_target_id",
        "experimental_pre_geometry_target",
    )
    availability_fields = (
        "positive_generative_supervision_eligible",
        "reactive_atom_pair_label_available",
        "warhead_atom_set_label_available",
        "role_partition_label_available",
        "post_geometry_usability_label_available",
        "post_geometry_supervision_available",
        "event_training_use_label_available",
        "approved_canonical_reaction_family_target_available",
        "warhead_type_classification_target_available",
        "mask_A_warhead_only_available",
        "mask_B_linker_plus_warhead_available",
        "mask_B2_scaffold_plus_warhead_available",
        "mask_B3_scaffold_only_available",
        "mask_C_scaffold_plus_linker_plus_warhead_available",
    )
    for row in negative:
        _assert(row["task_domain_relevance_label_available"] == "true", "negative relevance available")
        _assert(row["task_domain_relevance_label"] == subject.NOT_RELEVANT, "negative relevance")
        _assert(all(row[field] == "false" for field in availability_fields), "negative masks false")
        _assert(all(row[field] == "" for field in chemistry_fields), "negative chemistry blank")
        _assert(row["label_availability_status"] == "NOT_APPLICABLE_TASK_DOMAIN_NEGATIVE", "negative status")

    px5 = [row for row in positive if ":PX5:" in row["canonical_event_id"]]
    _assert(len(px5) == 2, "PX5 exact two events")
    for row in px5:
        _assert(json.loads(row["warhead_atom_ids_json"]) == ["C10", "C11", "C12", "C13", "C14", "C15", "O16", "O17"], "PX5 warhead frozen")
        _assert(json.loads(row["linker_atom_ids_json"]) == [], "PX5 empty linker frozen")
        _assert(json.loads(row["scaffold_atom_ids_json"]) == ["C1", "C2", "C3", "C4", "C5", "C6", "C8", "N9", "S7"], "PX5 scaffold frozen")
        _assert(all(row[field] == "false" for field in availability_fields[-5:]), "PX5 masks fail closed")
        _assert(row["five_mask_derivation_status"] == "UNAVAILABLE_CURRENT_EXACT3_CONTRACT_REQUIRES_EACH_PRIMARY_ROLE_NONEMPTY", "PX5 mask status")
    other_positive = [row for row in positive if ":PX5:" not in row["canonical_event_id"]]
    _assert(len(other_positive) == 11, "other positive exact eleven events")
    _assert(
        all(
            all(row[field] == "true" for field in availability_fields[-5:])
            for row in other_positive
        ),
        "other positive all five masks available",
    )

    mask_columns = {
        "mask_A_available_event_count": "mask_A_warhead_only_available",
        "mask_B_available_event_count": "mask_B_linker_plus_warhead_available",
        "mask_B2_available_event_count": "mask_B2_scaffold_plus_warhead_available",
        "mask_B3_available_event_count": "mask_B3_scaffold_only_available",
        "mask_C_available_event_count": "mask_C_scaffold_plus_linker_plus_warhead_available",
    }
    return {
        name: sum(row[column] == "true" for row in rows)
        for name, column in mask_columns.items()
    }


def check_v1(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    profile = verify_repository_state_v1(repo_root)
    baseline_mask_runtime = verify_label_snapshot_baseline_mask_runtime_v1(
        repo_root
    )
    output_root = repo_root / subject.OUTPUT_ROOT_RELATIVE
    _assert(output_root.is_dir(), "output root missing")
    _assert(
        {path.name for path in output_root.iterdir() if path.is_file()}
        == set(subject.OUTPUT_FILENAMES),
        "exact four output files",
    )
    _assert(
        not any(path.suffix in {".tmp", ".part"} for path in output_root.iterdir()),
        "temporary output remains",
    )

    batch_root = repo_root.parent / subject.BATCH_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    external_before = subject.snapshot_external_workspace_v1(batch_root)
    attempt_before = _snapshot_attempt_001(repo_root)
    cache_root = executor.canonical_controlled_cache_root_v1(repo_root)
    cache_before = executor.snapshot_cache_tree_v1(cache_root)
    cache_ledger_before = _sha256((cache_root / "cache_manifest_v1.json").read_bytes())
    _assert(cache_ledger_before == cumulative.CACHE_LEDGER_SHA256, "canonical cache ledger")
    predecessor_before = {
        path: _sha256((repo_root / path).read_bytes())
        for path in subject.PUBLISHED_REPOSITORY_BINDINGS
    }

    expected_first = subject.build_artifacts_v1(repo_root)
    expected_second = subject.build_artifacts_v1(repo_root)
    _assert(expected_first == expected_second, "deterministic double build")
    for name in subject.OUTPUT_FILENAMES:
        _assert(
            (output_root / name).read_bytes() == expected_first[name],
            "persisted artifact replay mismatch: " + name,
        )

    snapshot = json.loads((output_root / subject.SNAPSHOT).read_bytes())
    manifest = json.loads((output_root / subject.MANIFEST).read_bytes())
    summary = json.loads((output_root / subject.SUMMARY).read_bytes())
    rows = _csv(output_root / subject.MATRIX)
    for artifact in (snapshot, manifest, summary):
        _assert(not _contains_absolute_path(artifact), "absolute path persisted")
        _assert(not _contains_forbidden_runtime_key(artifact), "runtime state persisted")
        subject.reject_stale_feature_semantics_claims_v1(artifact)

    _assert(
        _sha256((output_root / subject.SNAPSHOT).read_bytes())
        == subject.PRE_REVISION_SNAPSHOT_SHA256,
        "snapshot not byte-identical to pre-revision",
    )
    _assert(
        _sha256((output_root / subject.MATRIX).read_bytes())
        == subject.PRE_REVISION_MATRIX_SHA256,
        "matrix not byte-identical to pre-revision",
    )

    _assert(snapshot["schema_version"] == subject.SNAPSHOT_SCHEMA_VERSION, "snapshot schema")
    decisions = snapshot["completed_human_decisions"]
    _assert(len(decisions) == 9, "exact nine completed decisions")
    _assert(len({item["review_unit_id"] for item in decisions}) == 9, "unique units")
    _assert(all(item["review_unit_id"] != subject.HELD_OUT_UNIT_ID for item in decisions), "ONL not ingested")
    bound = subject.verify_bound_inputs_v1(repo_root)
    for item in decisions:
        unit_id = item["review_unit_id"]
        _assert(item["source_template_sha256"] == subject.TEMPLATE_SHA256[unit_id], "template SHA")
        _assert(item["human_decision"] == bound["templates"][unit_id], "decision copied exactly")
    _assert(snapshot["counts"] == {
        "unit_count": 9,
        "event_count": 37,
        "completed_positive_unit_count": 5,
        "completed_positive_event_count": 13,
        "completed_negative_unit_count": 4,
        "completed_negative_event_count": 24,
        "in_progress_units_ingested": 0,
        "duplicate_unit_count": 0,
        "duplicate_event_count": 0,
    }, "snapshot exact counts")
    held = snapshot["held_out_in_progress"]
    _assert(held["held_out_in_progress_unit_count"] == 1, "held unit count")
    _assert(held["held_out_in_progress_event_count"] == 9, "held event count")
    _assert(held["held_out_reason"] == subject.HELD_OUT_REASON, "held reason")
    _assert(held["ONL_ingested"] is False, "ONL held")

    mask_counts = _direct_matrix_checks(rows)
    expected_availability = manifest["availability_counts"]
    _assert(expected_availability["row_count"] == len(rows), "manifest direct row evidence")
    _assert(expected_availability["unique_event_count"] == len({row["canonical_event_id"] for row in rows}), "manifest direct unique evidence")
    _assert(expected_availability["positive_rows"] == 13, "manifest positive rows")
    _assert(expected_availability["negative_rows"] == 24, "manifest negative rows")
    _assert(expected_availability["approved_canonical_reaction_family_available_rows"] == 0, "manifest family rows")
    _assert(expected_availability["negative_rows_with_fabricated_chemistry_label"] == 0, "manifest no fabricated negative")
    _assert(all(expected_availability[name] == count == 11 for name, count in mask_counts.items()), "manifest mask counts")
    _assert(
        manifest["current_feature_semantics_resolution_bindings"]
        == bound["current_feature_semantics_resolution_bindings"],
        "current feature-resolution bindings",
    )
    _assert(
        manifest["mask_runtime_observation_at_label_snapshot_baseline"]
        == baseline_mask_runtime,
        "label-snapshot baseline mask-runtime observation",
    )
    _assert(
        manifest["current_feature_semantics_resolution"]
        == {
            **subject.CURRENT_FEATURE_SEMANTICS_RESOLUTION,
            "feature_semantics_reopened": False,
        },
        "current feature-resolution semantics",
    )
    readiness = {
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
    }
    for artifact_name, artifact in (("manifest", manifest), ("summary", summary)):
        _assert(
            all(artifact.get(field) == expected for field, expected in readiness.items()),
            artifact_name + " readiness semantics",
        )
        _assert(
            all(artifact.get(field) == 11 for field in mask_counts),
            artifact_name + " exact five mask counts",
        )
    mask_interpretation = manifest["mask_derivation_interpretation"]
    _assert(
        mask_interpretation
        == {
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
        },
        "PX5 runtime-gap interpretation",
    )
    local_targets = manifest["stage_local_unavailable_target_accounting"]
    _assert(
        [row["status_id"] for row in local_targets]
        == [
            "FAMILY_DEPENDENT_CLASSIFICATION_AUTHORITY_UNAVAILABLE",
            "PX5_LABEL_SNAPSHOT_BASELINE_FIVE_MASK_RUNTIME_REQUIRES_NONEMPTY_LINKER_REGION",
        ],
        "stage-local unavailable target IDs",
    )
    _assert(local_targets[0]["other_positive_supervision_blocked"] is False, "family masking preserves supervision")
    _assert(local_targets[1]["human_role_partition_valid"] is True, "PX5 human roles valid")
    _assert(local_targets[1]["all_five_masks_available_at_label_snapshot"] is False, "PX5 masks unavailable at snapshot")
    _assert(local_targets[1]["gap_type"] == "MODEL_CONTRACT_EMPTY_LINKER_COMPATIBILITY_GAP", "PX5 model-contract gap")
    model_contract = manifest["model_integration_contract"]
    _assert(model_contract["all_five_mask_runtime_compatible_at_label_snapshot_event_count"] == 11, "snapshot-compatible mask count")
    _assert(model_contract["empty_linker_runtime_gap_at_label_snapshot_event_count"] == 2, "snapshot empty-linker gap count")
    _assert(model_contract["future_live_masking_runtime_may_change_without_invalidating_snapshot"] is True, "future masking successor allowed")
    _assert(manifest["ready_for_model_integration_design"] is True, "model integration design ready")
    _assert(manifest["ready_for_training"] is False, "training not ready")
    _assert(manifest["safety"]["family_authority_created"] is False, "no family authority")
    _assert(manifest["safety"]["production_authority_created"] is False, "no production authority")
    _assert(manifest["safety"]["batch_002_created"] is False, "no batch-002")
    _assert(manifest["safety"]["tensorization_performed"] is False, "no tensorization")
    _assert(manifest["safety"]["training_performed"] is False, "no training")
    _assert(manifest["safety"]["network_performed"] is False, "no network")
    _assert(manifest["safety"]["checkpoint_read"] is False, "no checkpoint read")
    _assert(manifest["safety"]["model_forward_performed"] is False, "no model forward")
    _assert(manifest["safety"]["loss_computation_performed"] is False, "no loss")
    _assert(manifest["safety"]["optimizer_step_performed"] is False, "no optimizer")
    _assert("sha256" not in manifest.get("artifact_bindings", {}).get(subject.MANIFEST, {}), "manifest does not self-hash")
    _assert(summary["artifact_sha256_excluding_summary"] == {
        subject.SNAPSHOT: _sha256((output_root / subject.SNAPSHOT).read_bytes()),
        subject.MATRIX: _sha256((output_root / subject.MATRIX).read_bytes()),
        subject.MANIFEST: _sha256((output_root / subject.MANIFEST).read_bytes()),
    }, "summary artifact hashes")
    _assert(summary["completed_positive_event_count"] == 13, "positive count unchanged")
    _assert(summary["completed_negative_event_count"] == 24, "negative count unchanged")
    _assert(summary["positive_generative_supervision_eligible_event_count"] == 13, "positive eligibility unchanged")
    _assert(summary["approved_family_target_available_event_count"] == 0, "family target count")
    _assert(summary["warhead_type_classification_available_event_count"] == 0, "warhead type target count")
    _assert(summary["snapshot_byte_identical_to_pre_revision"] is True, "snapshot identity marker")
    _assert(summary["matrix_byte_identical_to_pre_revision"] is True, "matrix identity marker")
    _assert(summary["PX5_mask_incompatible_at_label_snapshot_event_count"] == 2, "snapshot PX5 mask gap count")
    _assert(
        all(
            summary["snapshot_mask_" + alias + "_available_event_count"] == 11
            for alias in ("A", "B", "B2", "B3", "C")
        ),
        "snapshot mask availability counts",
    )

    _assert(subject.snapshot_external_workspace_v1(batch_root) == external_before, "external batch changed")
    _assert(_snapshot_attempt_001(repo_root) == attempt_before, "attempt-001 changed")
    _assert(executor.snapshot_cache_tree_v1(cache_root) == cache_before, "canonical cache changed")
    _assert(_sha256((cache_root / "cache_manifest_v1.json").read_bytes()) == cache_ledger_before, "cache ledger changed")
    _assert({path: _sha256((repo_root / path).read_bytes()) for path in subject.PUBLISHED_REPOSITORY_BINDINGS} == predecessor_before, "published predecessor changed")
    _assert(not (batch_root.parent / "batch-002").exists(), "batch-002 exists")

    changed_paths = set(observe_repository_state_v1(repo_root)["modified_tracked_paths"])
    changed_paths.update(observe_repository_state_v1(repo_root)["staged_paths"])
    _assert(not any(path.startswith(PROTECTED_PATH_PREFIXES) for path in changed_paths), "protected source changed")
    _assert(not any(path.endswith(FORBIDDEN_SUFFIXES) for path in subject.AUTHORIZED_PUBLICATION_PATHS), "forbidden candidate suffix")
    return {
        "repository_profile": profile,
        "completed_unit_snapshot_count": len(decisions),
        "task_label_matrix_row_count": len(rows),
        "mask_counts": mask_counts,
        "stale_feature_semantics_blockers_removed": True,
        "current_feature_semantics_resolution_bound": True,
        "batch001_successor_mask_runtime_binding_is_snapshot_scoped": True,
        "future_masking_runtime_successor_can_change_without_invalidating_snapshot": True,
        "snapshot_byte_identical_to_pre_revision": True,
        "matrix_byte_identical_to_pre_revision": True,
        "ready_for_model_integration_design": True,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    arguments = parser.parse_args(argv)
    result = check_v1(arguments.repo_root)
    print("batch001_completed_decision_successor_built=true")
    print("predecessor_human_overlay_modified=false")
    print("predecessor_human_progress_modified=false")
    print("completed_unit_snapshot_count=" + str(result["completed_unit_snapshot_count"]))
    print("completed_event_snapshot_count=37")
    print("ONL_ingested=false")
    print("task_label_matrix_row_count=" + str(result["task_label_matrix_row_count"]))
    print("stale_feature_semantics_blockers_removed=true")
    print("current_feature_semantics_resolution_bound=true")
    print("feature_semantics_audit_completed=true")
    print("feature_semantics_known=true")
    print("unknown_atom_feature_policy_resolved=true")
    print("unknown_atom_policy_contract_resolved=true")
    print("feature_semantics_reopened=false")
    print("snapshot_byte_identical_to_pre_revision=true")
    print("matrix_byte_identical_to_pre_revision=true")
    print("PX5_empty_linker_human_label_preserved=true")
    print("PX5_five_mask_runtime_compatible_at_label_snapshot=false")
    print("PX5_mask_unavailable_event_count=2")
    print("PX5_mask_incompatible_at_label_snapshot_event_count=2")
    for name, count in result["mask_counts"].items():
        print(name + "=" + str(count))
    print("approved_family_target_available_event_count=0")
    print("warhead_type_classification_available_event_count=0")
    print("global_training_readiness_adjudicated_by_this_stage=false")
    print("family_authority_created=false")
    print("production_authority_created=false")
    print("batch_002_created=false")
    print("tensorization_performed=false")
    print("training_performed=false")
    print("network_performed=false")
    print("ready_for_gpt_review=true")
    print("ready_for_model_integration_design=true")
    print("ready_for_training=false")
    print("precommit_candidate_profile_supported=true")
    print("published_clean_descendant_profile_supported=true")
    print("batch001_successor_mask_runtime_binding_is_snapshot_scoped=true")
    print("future_masking_runtime_successor_can_change_without_invalidating_snapshot=true")
    print(
        "recommended_next_step_exactly="
        "new_codex_conversation_design_empty_linker_compatible_five_module_"
        "model_integration_v1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
