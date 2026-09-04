#!/usr/bin/env python3
"""Fail-closed checker for the 4LH completed-decision reconciliation Exact4."""

from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, NoReturn


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1
    as ingestion,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_4lh_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_0d8_v1 as predecessor,
)


BASELINE_COMMIT = "dd8968608796fd2c2b458d4d0f98cf4ea97d4cf5"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
DEPENDENCY_BINDINGS = (
    (
        "GENERIC_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "WITH_0D8_PREDECESSOR_OWNER",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_0d8_v1.py",
        28275,
        "a5f804db8f8fedcfed7e8035e15ea496179ba9c347985c571ca49ac05b38a8d1",
    ),
    (
        "4LH_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1.py",
        72317,
        "d0baeb39806d9da79989aea90f3d96419ea9f794c8bdef55202405086560f425",
    ),
    (
        "4LH_INGESTION_CHECKER",
        "scripts/check_covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1.py",
        21355,
        "4a4e1308271b2b9f77240662b528f0a13e7365a872cf90019c67c7a9a10ae5ae",
    ),
    (
        "4LH_INGESTION_TESTS",
        "tests/test_covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1.py",
        20955,
        "1f05083aac7cace14d3cfd1acb836e57edae3aed369a7497ee9780b81fbdd80a",
    ),
    (
        "4LH_INGESTION_SNAPSHOT",
        "data/derived/covalent_small/covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1/covapie_4lh_completed_human_decision_snapshot_v1.json",
        28635,
        "7c8ec1fee6cd532367cbe149fc9ac0e1a383c3b0d5671c233f06473f126c4d40",
    ),
    (
        "4LH_INGESTION_MATRIX",
        "data/derived/covalent_small/covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1/covapie_4lh_event_task_label_availability_v1.csv",
        10647,
        "5f72b7f78d5a2859b340c5592fb26b95c7e7a1a4ba3e6ba4174159adee209284",
    ),
    (
        "4LH_INGESTION_SUMMARY",
        "data/derived/covalent_small/covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1/covapie_4lh_completed_decision_ingestion_summary_v1.json",
        1489,
        "d31b1c2f3ed87ab3c5cd7b8cb7927b74d317c9dca58add961830e59ad0ed31f7",
    ),
    (
        "4LH_INGESTION_MANIFEST",
        "data/derived/covalent_small/covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1/covapie_4lh_completed_decision_ingestion_manifest_v1.json",
        17764,
        "e04669c7060ce87fd5e7daed8fb8805d9687d3720772006ca3ba1acfe1fc2b26",
    ),
    (
        "WITH_0D8_PREDECESSOR_ARTIFACT",
        "data/derived/covalent_small/covapie_completed_human_decision_reconciliation_with_0d8_v1/covapie_completed_human_decision_reconciliation_with_0d8_v1.json",
        327651,
        "53bc6d6591e07b66224d40a64757953a93200f86909611e600d964955210bf6f",
    ),
)
FORBIDDEN_SUFFIXES = (
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".pyc",
    ".tmp",
    ".part",
)
PROTECTED_PREFIXES = (
    "data/raw/",
    "checkpoints/",
    "equivariant_diffusion/",
    "covapie-state/",
)
PROTECTED_FILES = {
    "lightning_modules.py",
    "dataset.py",
    "data/prepare_crossdocked.py",
}
MAX_FILE_BYTES = 1024 * 1024
EXPECTED_PREDECESSOR_COVERAGE = {
    "accepted_fact_count": 131,
    "accepted_review_unit_count": 22,
    "stable_source_identity_count": 22,
    "remaining_unreviewed_chemistry_event_count": 207,
    "remaining_unreviewed_review_unit_upper_bound": 109,
    "decision_category_distribution": {
        "chemistry_positive": 91,
        "chemistry_negative": 20,
        "task_domain_negative": 20,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
EXPECTED_SUCCESSOR_COVERAGE = {
    "accepted_fact_count": 135,
    "accepted_review_unit_count": 23,
    "stable_source_identity_count": 23,
    "remaining_unreviewed_chemistry_event_count": 203,
    "remaining_unreviewed_review_unit_upper_bound": 108,
    "decision_category_distribution": {
        "chemistry_positive": 95,
        "chemistry_negative": 20,
        "task_domain_negative": 20,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}


def _fail(token: str) -> NoReturn:
    raise ValueError("COVAPIE_4LH_RECONCILIATION_V1_ERROR:" + token)


def _git(root: Path, *arguments: str) -> str:
    allowed = {
        "branch",
        "diff",
        "ls-files",
        "merge-base",
        "rev-list",
        "rev-parse",
        "status",
    }
    if not arguments or arguments[0] not in allowed:
        _fail("GIT_SUBCOMMAND_FORBIDDEN")
    process = subprocess.run(
        ("git", *arguments), cwd=root, text=True, capture_output=True, check=False
    )
    if process.returncode:
        _fail("GIT_COMMAND_FAILED:" + arguments[0])
    return process.stdout.rstrip("\n")


def _git_is_ancestor(root: Path, older: str, newer: str) -> bool:
    process = subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer),
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode not in (0, 1):
        _fail("GIT_ANCESTRY_CHECK_FAILED")
    return process.returncode == 0


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_regular(path: Path, label: str) -> bytes:
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise ValueError("READ_FAILED:" + label) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail("NOT_REGULAR_FILE:" + label)
    return payload


def classify_repository_profile(
    *,
    expected_paths: tuple[str, ...],
    tracked_paths: set[str],
    ordinary_untracked: set[str],
    status_lines: tuple[str, ...],
    working_diff: set[str],
    cached_diff: set[str],
) -> str:
    """Classify only the strict untracked or tracked-clean lifecycle profile."""

    expected = set(expected_paths)
    if len(expected_paths) != 4 or len(expected) != 4:
        _fail("EXPECTED_INVENTORY_NOT_EXACT4")
    tracked_candidate = expected & tracked_paths
    if tracked_candidate and tracked_candidate != expected:
        _fail("MIXED_TRACKING_STATE")
    if working_diff:
        _fail("TRACKED_WORKTREE_MODIFICATION_PRESENT")
    if cached_diff:
        _fail("STAGED_INDEX_CHANGE_PRESENT")
    if len(status_lines) != len(set(status_lines)):
        _fail("DUPLICATE_STATUS_ENTRY")
    if not tracked_candidate:
        if ordinary_untracked != expected:
            _fail("ORDINARY_UNTRACKED_NOT_STRICT_EXACT4")
        if set(status_lines) != {"?? " + path for path in expected}:
            _fail("CANDIDATE_STATUS_NOT_STRICT_EXACT4")
        return CANDIDATE_UNTRACKED
    if ordinary_untracked or status_lines:
        _fail("TRACKED_CLEAN_STATE_DIRTY")
    return TRACKED_CLEAN


def validate_repository_relation_values(
    *,
    profile: str,
    expected_paths: set[str],
    head: str,
    origin_main: str,
    ahead: int,
    behind: int,
    baseline_is_ancestor_of_head: bool,
    baseline_is_ancestor_of_origin: bool,
    origin_is_ancestor_of_head: bool,
    changed_since_baseline: set[str],
) -> None:
    """Validate publication ancestry without pinning a future commit hash."""

    if profile == CANDIDATE_UNTRACKED:
        if not (
            head == BASELINE_COMMIT
            and origin_main == BASELINE_COMMIT
            and (ahead, behind) == (0, 0)
            and baseline_is_ancestor_of_head
            and baseline_is_ancestor_of_origin
            and origin_is_ancestor_of_head
            and not changed_since_baseline
        ):
            _fail("CANDIDATE_BASELINE_RELATION_INVALID")
        return
    if profile != TRACKED_CLEAN:
        _fail("REPOSITORY_PROFILE_INVALID")
    if (
        not baseline_is_ancestor_of_head
        or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head
        or head == BASELINE_COMMIT
        or behind != 0
        or ahead < 0
        or not expected_paths <= changed_since_baseline
    ):
        _fail("TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID")
    if (ahead == 0) != (origin_main == head):
        _fail("TRACKED_CLEAN_ORIGIN_RELATION_INVALID")


def _repository_observations(root: Path) -> dict[str, object]:
    return {
        "tracked_paths": set(filter(None, _git(root, "ls-files").splitlines())),
        "ordinary_untracked": set(
            filter(
                None,
                _git(root, "ls-files", "--others", "--exclude-standard").splitlines(),
            )
        ),
        "status_lines": tuple(
            filter(
                None,
                _git(root, "status", "--short", "--untracked-files=all").splitlines(),
            )
        ),
        "working_diff": set(
            filter(None, _git(root, "diff", "--name-only").splitlines())
        ),
        "cached_diff": set(
            filter(None, _git(root, "diff", "--cached", "--name-only").splitlines())
        ),
    }


def _validate_history_scope(changed_since_baseline: set[str]) -> None:
    protected = sorted(
        path
        for path in changed_since_baseline
        if path in PROTECTED_FILES
        or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
    )
    forbidden = sorted(
        path
        for path in changed_since_baseline
        if Path(path).suffix.lower() in FORBIDDEN_SUFFIXES
    )
    if protected:
        _fail("PROTECTED_PATH_CHANGED_SINCE_BASELINE:" + protected[0])
    if forbidden:
        _fail("FORBIDDEN_SUFFIX_CHANGED_SINCE_BASELINE:" + forbidden[0])


def _verify_repository_relation(
    root: Path, profile: str, expected_paths: set[str]
) -> dict[str, object]:
    head = _git(root, "rev-parse", "HEAD")
    origin_main = _git(root, "rev-parse", "origin/main")
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    relation = _git(
        root, "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).split()
    if branch != "main" or len(relation) != 2 or any(
        not value.isdigit() for value in relation
    ):
        _fail("REPOSITORY_IDENTITY_OR_RELATION_INVALID")
    ahead, behind = (int(value) for value in relation)
    if profile == TRACKED_CLEAN:
        baseline_head = _git_is_ancestor(root, BASELINE_COMMIT, "HEAD")
        baseline_origin = _git_is_ancestor(root, BASELINE_COMMIT, "origin/main")
        origin_head = _git_is_ancestor(root, "origin/main", "HEAD")
        changed = set(
            filter(
                None,
                _git(
                    root, "diff", "--name-only", BASELINE_COMMIT + "..HEAD"
                ).splitlines(),
            )
        )
    else:
        baseline_head = baseline_origin = origin_head = True
        changed = set()
    validate_repository_relation_values(
        profile=profile,
        expected_paths=expected_paths,
        head=head,
        origin_main=origin_main,
        ahead=ahead,
        behind=behind,
        baseline_is_ancestor_of_head=baseline_head,
        baseline_is_ancestor_of_origin=baseline_origin,
        origin_is_ancestor_of_head=origin_head,
        changed_since_baseline=changed,
    )
    _validate_history_scope(changed)
    return {
        "branch": branch,
        "HEAD": head,
        "origin_main": origin_main,
        "ahead": ahead,
        "behind": behind,
        "changed_since_baseline": tuple(sorted(changed)),
    }


def _verify_repository(root: Path) -> dict[str, object]:
    observations = _repository_observations(root)
    expected_paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    profile = classify_repository_profile(
        expected_paths=expected_paths,
        tracked_paths=observations["tracked_paths"],  # type: ignore[arg-type]
        ordinary_untracked=observations["ordinary_untracked"],  # type: ignore[arg-type]
        status_lines=observations["status_lines"],  # type: ignore[arg-type]
        working_diff=observations["working_diff"],  # type: ignore[arg-type]
        cached_diff=observations["cached_diff"],  # type: ignore[arg-type]
    )
    relation = _verify_repository_relation(root, profile, set(expected_paths))
    return {
        **relation,
        "lifecycle": profile,
        "staged_count": 0,
        "tracked_modification_count": 0,
        "untracked_count": len(observations["ordinary_untracked"]),  # type: ignore[arg-type]
    }


def _verify_exact4_files(root: Path) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for relative in subject.EXACT4_PATHS:
        path = root / relative
        payload = _read_regular(path, relative.as_posix())
        if len(payload) > MAX_FILE_BYTES:
            _fail("EXACT4_FILE_TOO_LARGE:" + relative.as_posix())
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("EXACT4_NOT_UTF8:" + relative.as_posix()) from error
        if text.startswith("\ufeff") or "\x00" in text or "\r" in text:
            _fail("EXACT4_TEXT_INVARIANT_INVALID:" + relative.as_posix())
        mode = stat.S_IMODE(path.lstat().st_mode)
        if mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            _fail("EXACT4_FILE_EXECUTABLE:" + relative.as_posix())
        reports.append(
            {
                "path": relative.as_posix(),
                "bytes": len(payload),
                "LOC": len(text.splitlines()),
                "SHA256": _sha256(payload),
                "git_mode": "100644",
            }
        )
    return reports


def _verify_dependencies(root: Path) -> list[dict[str, object]]:
    reports: list[dict[str, object]] = []
    for role, relative, expected_bytes, expected_sha in DEPENDENCY_BINDINGS:
        payload = _read_regular(root / relative, role)
        if len(payload) != expected_bytes or _sha256(payload) != expected_sha:
            _fail("PUBLISHED_DEPENDENCY_DRIFT:" + role)
        reports.append(
            {
                "role": role,
                "path": relative,
                "bytes": len(payload),
                "SHA256": _sha256(payload),
            }
        )
    return reports


def _strict_json(payload: bytes) -> dict[str, Any]:
    try:
        value = generic._strict_json_object(payload, "4LH_RECONCILIATION_ARTIFACT")
    except generic.CompletedDecisionReconciliationError as error:
        raise ValueError("ARTIFACT_JSON_INVALID:" + str(error)) from error
    return value


def _stable_identity(binding: dict[str, object]) -> str:
    return (
        str(binding["path_namespace"])
        + ":"
        + str(binding["source_path"])
        + "@"
        + str(binding["sha256"])
    )


def _verify_artifact_byte_identity(expected_payload: bytes, observed_payload: bytes) -> None:
    if observed_payload != expected_payload:
        _fail("MATERIALIZED_ARTIFACT_BYTES_MISMATCH")


def _verify_artifact_semantics(
    artifact: dict[str, Any],
    *,
    expected_predecessor_artifact: dict[str, Any],
    expected_projection: list[dict[str, object]],
) -> dict[str, object]:
    """Validate structure and semantics independently of serialized bytes."""

    if tuple(artifact) != subject._ARTIFACT_FIELDS:
        _fail("ARTIFACT_TOP_LEVEL_SCHEMA_INVALID")
    if tuple(expected_predecessor_artifact) != subject._ARTIFACT_FIELDS:
        _fail("PREDECESSOR_ARTIFACT_TOP_LEVEL_SCHEMA_INVALID")
    bindings = artifact.get("source_bindings")
    facts = artifact.get("normalized_facts")
    rows = artifact.get("reconciled_rows")
    predecessor_bindings = expected_predecessor_artifact.get("source_bindings")
    predecessor_facts = expected_predecessor_artifact.get("normalized_facts")
    predecessor_rows = expected_predecessor_artifact.get("reconciled_rows")
    if not isinstance(bindings, list) or not isinstance(facts, list) or not isinstance(rows, list):
        _fail("ARTIFACT_COLLECTION_TYPE_INVALID")
    if (
        not isinstance(predecessor_bindings, list)
        or not isinstance(predecessor_facts, list)
        or not isinstance(predecessor_rows, list)
        or len(predecessor_bindings) != 22
        or len(predecessor_facts) != 131
        or len(predecessor_rows) != 338
        or expected_predecessor_artifact.get("review_summary")
        != subject._PREDECESSOR_REVIEW_SUMMARY
    ):
        _fail("PUBLISHED_PREDECESSOR_ARTIFACT_INVALID")
    if len(bindings) != 23 or len(facts) != 135 or len(rows) != 338:
        _fail("ARTIFACT_EXACT_COUNTS_INVALID")
    if any(
        type(binding) is not dict
        or set(binding) != set(subject._SOURCE_BINDING_FIELDS)
        or binding.get("path_namespace") != "repository_parent_relative"
        or str(binding.get("source_path", "")).startswith("/")
        for binding in bindings
    ):
        _fail("ARTIFACT_SOURCE_BINDING_SCHEMA_OR_NAMESPACE_INVALID")
    identities = [_stable_identity(binding) for binding in bindings]
    review_units = [str(binding["review_unit_id"]) for binding in bindings]
    if len(set(identities)) != 23 or len(set(review_units)) != 23:
        _fail("ARTIFACT_SOURCE_IDENTITY_DUPLICATE")
    if any(
        type(fact) is not dict
        or set(fact) != set(subject._GENERIC_FACT_FIELDS)
        or subject._FORBIDDEN_RICH_FACT_FIELDS & set(fact)
        for fact in facts
    ):
        _fail("ARTIFACT_GENERIC_FACT_NOT_EXACT11")

    if bindings[:-1] != predecessor_bindings:
        _fail("PREDECESSOR_SOURCE_BINDING_PREFIX_INVALID")
    expected_binding = {
        "source_path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": ingestion.FORMAL_BINDINGS[0][2],
        "sha256": ingestion.FORMAL_BINDINGS[0][3],
        "schema_version": ingestion.FORMAL_DECISION_SCHEMA,
        "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
    }
    if bindings[-1] != expected_binding:
        _fail("4LH_SOURCE_BINDING_INVALID")
    new_facts = facts[-4:]
    if facts[:131] != predecessor_facts:
        _fail("PREDECESSOR_FACT_PREFIX_INVALID")
    if new_facts != expected_projection:
        _fail("4LH_FACTS_NOT_EXACT_INGESTION_PROJECTION")
    if any(
        fact.get("task_relevance_disposition") != generic.TASK_RELEVANT
        or fact.get("chemistry_disposition") != generic.CHEMISTRY_POSITIVE
        or fact.get("legacy_completed_review_status")
        != generic.COMPLETED_HUMAN_POSITIVE
        or fact.get("training_disposition") != generic.TRAINING_INCLUDE
        or fact.get("human_training_excluded") is not False
        for fact in new_facts
    ):
        _fail("4LH_CLASSIFICATION_OR_TRAINING_BOUNDARY_INVALID")
    if artifact.get("review_summary") != subject._SUCCESSOR_REVIEW_SUMMARY:
        _fail("ARTIFACT_GENERIC_REVIEW_SUMMARY_INVALID")
    target_ids = set(ingestion.EXPECTED_EVENT_IDS)
    changed_targets = 0
    changed_non_targets = 0
    for old, new in zip(predecessor_rows, rows, strict=True):
        if old.get("canonical_event_id") not in target_ids:
            changed_non_targets += old != new
            continue
        changed_fields = {key for key in old if old.get(key) != new.get(key)}
        if (
            changed_fields != subject._ALLOWED_RECONCILIATION_FIELDS
            or old.get("raw_priority_rank") != "26"
            or old.get("raw_review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
            or old.get("raw_unit_event_count") != "4"
            or old.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
            or old.get("calibration_eligible") != "true"
            or old.get("calibration_exclusion_reason") != ""
            or new.get("current_review_status") != generic.COMPLETED_HUMAN_POSITIVE
            or new.get("current_status_authority_sources_json")
            != generic._canonical_json([ingestion.FORMAL_DECISION_RELATIVE.as_posix()])
            or new.get("calibration_eligible") != "false"
            or new.get("calibration_exclusion_reason")
            != generic.COMPLETED_HUMAN_POSITIVE
        ):
            _fail("4LH_RECONCILIATION_TRANSITION_INVALID")
        changed_targets += 1
    if changed_targets != 4 or changed_non_targets != 0:
        _fail("RECONCILIATION_DELTA_NOT_EXACT4_ONLY")
    if len({str(fact["canonical_event_id"]) for fact in facts}) != 135:
        _fail("NORMALIZED_EVENT_ID_DUPLICATE")
    return {
        "source_count": 23,
        "review_unit_count": 23,
        "stable_source_identity_count": 23,
        "accepted_fact_count": 135,
        "duplicate_count": 0,
        "source_namespace": "repository_parent_relative",
        "generic_fact_field_count": 11,
        "rich_key_leakage": False,
        "predecessor_prefix_count": 131,
        "4LH_appended_fact_count": 4,
        "changed_target_row_count": changed_targets,
        "changed_non_target_row_count": changed_non_targets,
    }


def _verify_coverage_contract() -> dict[str, object]:
    before = subject.PREDECESSOR_COVERAGE_SUMMARY
    after = subject.SUCCESSOR_COVERAGE_SUMMARY
    if before != EXPECTED_PREDECESSOR_COVERAGE or after != EXPECTED_SUCCESSOR_COVERAGE:
        _fail("COVERAGE_SUMMARY_CONTRACT_DRIFT")
    before_distribution = before["decision_category_distribution"]
    after_distribution = after["decision_category_distribution"]
    if not isinstance(before_distribution, dict) or not isinstance(after_distribution, dict):
        _fail("DECISION_DISTRIBUTION_NOT_OBJECT")
    if (
        sum(before_distribution.values()) != 131
        or sum(after_distribution.values()) != 135
        or after_distribution["chemistry_positive"]
        - before_distribution["chemistry_positive"]
        != 4
        or any(
            after_distribution[key] != before_distribution[key]
            for key in ("chemistry_negative", "task_domain_negative", "task_domain_positive")
        )
        or after["label_ready_event_count"] != before["label_ready_event_count"]
        or after["training_mask_target_count"] != 0
        or after["training_authority"] is not False
    ):
        _fail("COVERAGE_DELTA_NOT_EXACT_4LH_CHEMISTRY_POSITIVE_4")
    return {"predecessor": copy.deepcopy(before), "successor": copy.deepcopy(after)}


def _verify_upstream_4lh_boundary(bound: dict[str, object]) -> dict[str, object]:
    subject._validate_rich_4lh_boundary_v1(bound)
    formal = bound["formal_document"]
    decisions = formal["formal_human_decision"]
    tasks = formal["canonical_Exact5_task_applicability"]
    d3 = decisions["D3_reactive_pair"]
    d4 = decisions["D4_role_candidate"]
    d5 = decisions["D5_training_use"]
    role = formal["selected_role_partition"]
    pre = formal["PRE_boundary"]
    post = formal["POST_boundary"]
    training = formal["training_boundary"]
    return {
        "chemistry_positive_evidence": decisions["D2_chemistry"]["value"] == "POSITIVE",
        "human_review_completed": formal["human_review_completed"],
        "task": decisions["D1_task_relevance"]["value"],
        "training": d5["value"],
        "pair": d3["protein_atom"] + "-" + d3["ligand_atom"],
        "pair_authority_count": 4,
        "role_authority_count": 4,
        "role_profile": d4["role_profile"],
        "W": role["W"],
        "L": role["L"],
        "S": role["S"],
        "boundary": role["direct_scaffold_warhead_boundary"],
        "minimal_seed": role["minimal_seed_atom_ids"],
        "primary_anchor": role["primary_anchor_atom_id"],
        "canonical_task_count": tasks["task_count"],
        "B3_present": tasks["B3_present"],
        "sixth_task": tasks["sixth_task"],
        "applicable_task_ids": tasks["applicable_task_ids"],
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": tasks["event_task_label_rows_materialized"],
        "training_mask_targets_available": training["mask_targets_created"],
        "PRE_mapping_count": pre["per_event_mapping_count"],
        "PRE_mapping_status": pre["PRE_source_mapping_status"],
        "PRE_status": pre["PRE_status"],
        "PRE_authority": pre["PRE_authority"],
        "POST_source_evidence_count": post["explicit_event_count"],
        "POST_training_authority": post["POST_training_authority"],
        "formal_training_admitted": training["formal_training_admitted"],
        "future_training_admission_candidate": training["future_training_admission_candidate"],
        "parameter_update_authorization": training["parameter_update_authority"],
        "training_authority": False,
    }


def _expected_projection_from_ingestion(
    bound: dict[str, object],
) -> list[dict[str, object]]:
    """Construct the Exact11 expectation without calling the candidate owner."""

    upstream = _verify_upstream_4lh_boundary(bound)
    if (
        upstream["human_review_completed"] is not True
        or upstream["task"] != "RELEVANT"
        or upstream["chemistry_positive_evidence"] is not True
        or upstream["training"] != "INCLUDE"
    ):
        _fail("4LH_UPSTREAM_CLASSIFICATION_INVALID")
    binding = ingestion.FORMAL_BINDINGS[0]
    return [
        {
            "canonical_event_id": event_id,
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "human_review_completed": True,
            "legacy_completed_review_status": generic.COMPLETED_HUMAN_POSITIVE,
            "task_relevance_disposition": generic.TASK_RELEVANT,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_INCLUDE,
            "human_training_excluded": False,
            "source_decision_schema": ingestion.FORMAL_DECISION_SCHEMA,
            "source_decision_sha256": binding[3],
            "source_binding_path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        }
        for event_id in ingestion.EXPECTED_EVENT_IDS
    ]


def _expect_failure(callable_: object, token: str) -> str:
    try:
        callable_()  # type: ignore[operator]
    except ValueError as error:
        if token not in str(error):
            _fail("TAMPER_FAILURE_TOKEN_INVALID:" + token)
        return token
    _fail("TAMPER_PROBE_DID_NOT_FAIL:" + token)


def _verify_tamper_probes(
    artifact: dict[str, Any],
    *,
    expected_payload: bytes,
    expected_predecessor_artifact: dict[str, Any],
    expected_projection: list[dict[str, object]],
) -> dict[str, str]:
    def verify(candidate: dict[str, Any]) -> None:
        _verify_artifact_semantics(
            candidate,
            expected_predecessor_artifact=expected_predecessor_artifact,
            expected_projection=expected_projection,
        )

    prefix = copy.deepcopy(artifact)
    prefix["normalized_facts"][0], prefix["normalized_facts"][1] = (
        prefix["normalized_facts"][1], prefix["normalized_facts"][0]
    )
    prefix_token = _expect_failure(
        lambda: verify(prefix), "PREDECESSOR_FACT_PREFIX_INVALID"
    )
    fact = copy.deepcopy(artifact)
    fact["normalized_facts"][-1]["chemistry_disposition"] = "NEGATIVE"
    fact_token = _expect_failure(
        lambda: verify(fact), "4LH_FACTS_NOT_EXACT_INGESTION_PROJECTION"
    )
    duplicate = copy.deepcopy(artifact)
    duplicate["source_bindings"][-1] = copy.deepcopy(duplicate["source_bindings"][0])
    duplicate_token = _expect_failure(
        lambda: verify(duplicate), "ARTIFACT_SOURCE_IDENTITY_DUPLICATE"
    )
    count = copy.deepcopy(artifact)
    count["normalized_facts"].pop()
    count_token = _expect_failure(
        lambda: verify(count), "ARTIFACT_EXACT_COUNTS_INVALID"
    )
    category = copy.deepcopy(artifact)
    category["normalized_facts"][-1]["task_relevance_disposition"] = "NOT_RELEVANT"
    category_token = _expect_failure(
        lambda: verify(category), "4LH_FACTS_NOT_EXACT_INGESTION_PROJECTION"
    )
    source_sha = copy.deepcopy(artifact)
    source_sha["normalized_facts"][-1]["source_decision_sha256"] = "0" * 64
    source_sha_token = _expect_failure(
        lambda: verify(source_sha), "4LH_FACTS_NOT_EXACT_INGESTION_PROJECTION"
    )
    leakage = copy.deepcopy(artifact)
    leakage["normalized_facts"][-1]["role_profile"] = ingestion.EXPECTED_ROLE_PROFILE
    leakage_token = _expect_failure(
        lambda: verify(leakage), "ARTIFACT_GENERIC_FACT_NOT_EXACT11"
    )
    target_row = copy.deepcopy(artifact)
    for row in target_row["reconciled_rows"]:
        if row["canonical_event_id"] in ingestion.EXPECTED_EVENT_IDS:
            row["current_review_status"] = generic.CURRENTLY_UNREVIEWED
            break
    target_row_token = _expect_failure(
        lambda: verify(target_row), "4LH_RECONCILIATION_TRANSITION_INVALID"
    )
    non_target = copy.deepcopy(artifact)
    for row in non_target["reconciled_rows"]:
        if row["canonical_event_id"] not in ingestion.EXPECTED_EVENT_IDS:
            row["calibration_eligible"] = "tampered"
            break
    non_target_token = _expect_failure(
        lambda: verify(non_target), "RECONCILIATION_DELTA_NOT_EXACT4_ONLY"
    )
    summary = copy.deepcopy(artifact)
    summary["review_summary"]["completed_positive_event_count"] = 118
    summary_token = _expect_failure(
        lambda: verify(summary), "ARTIFACT_GENERIC_REVIEW_SUMMARY_INVALID"
    )
    byte_token = _expect_failure(
        lambda: _verify_artifact_byte_identity(
            expected_payload, expected_payload + b" "
        ),
        "MATERIALIZED_ARTIFACT_BYTES_MISMATCH",
    )
    return {
        "predecessor_order_tamper": prefix_token,
        "4LH_fact_tamper": fact_token,
        "duplicate_source_tamper": duplicate_token,
        "count_tamper": count_token,
        "decision_category_tamper": category_token,
        "formal_source_sha_tamper": source_sha_token,
        "rich_field_leak_tamper": leakage_token,
        "target_status_tamper": target_row_token,
        "non_target_row_tamper": non_target_token,
        "review_summary_tamper": summary_token,
        "artifact_bytes_tamper": byte_token,
    }


def _verify_no_forbidden_or_large_files(root: Path) -> dict[str, object]:
    status_paths = [
        line[3:]
        for line in _git(root, "status", "--short", "--untracked-files=all").splitlines()
        if line
    ]
    forbidden = [path for path in status_paths if Path(path).suffix.lower() in FORBIDDEN_SUFFIXES]
    large = [path for path in status_paths if (root / path).stat().st_size > MAX_FILE_BYTES]
    if forbidden or large:
        _fail("FORBIDDEN_OR_LARGE_CANDIDATE_FILE")
    return {"forbidden_files": forbidden, "large_files": large}


def check_lifecycle_simulations() -> dict[str, bool]:
    """Prove supported publication states with pure lifecycle inputs."""

    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    expected = set(paths)
    if classify_repository_profile(
        expected_paths=paths,
        tracked_paths=set(),
        ordinary_untracked=expected,
        status_lines=tuple("?? " + path for path in paths),
        working_diff=set(),
        cached_diff=set(),
    ) != CANDIDATE_UNTRACKED:
        _fail("CANDIDATE_UNTRACKED_SIMULATION_FAILED")
    if classify_repository_profile(
        expected_paths=paths,
        tracked_paths=expected,
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    ) != TRACKED_CLEAN:
        _fail("TRACKED_CLEAN_SIMULATION_FAILED")
    for head, origin, ahead, changed in (
        ("publication-head", BASELINE_COMMIT, 1, expected),
        ("pushed-head", "pushed-head", 0, expected),
        ("later-head", "later-origin", 2, {*expected, "docs/later.md"}),
    ):
        validate_repository_relation_values(
            profile=TRACKED_CLEAN,
            expected_paths=expected,
            head=head,
            origin_main=origin,
            ahead=ahead,
            behind=0,
            baseline_is_ancestor_of_head=True,
            baseline_is_ancestor_of_origin=True,
            origin_is_ancestor_of_head=True,
            changed_since_baseline=changed,
        )
        _validate_history_scope(changed)
    return {
        "candidate_untracked": True,
        "tracked_clean": True,
        "committed_unpushed": True,
        "pushed_successor": True,
        "later_clean_descendant": True,
    }


def run_check_v1(repo_root: Path = ROOT) -> dict[str, object]:
    """Run the bounded, read-only 4LH reconciliation gate."""

    root = Path(repo_root).resolve()
    repository = _verify_repository(root)
    exact4 = _verify_exact4_files(root)
    dependencies = _verify_dependencies(root)
    predecessor_artifact = _strict_json(
        _read_regular(
            root / predecessor.OUTPUT_RELATIVE,
            "WITH_0D8_PREDECESSOR_ARTIFACT",
        )
    )
    expected = subject.build_artifact_v1(root)
    observed = _read_regular(root / subject.OUTPUT_RELATIVE, "4LH_ARTIFACT")
    artifact = _strict_json(observed)
    expected_artifact = _strict_json(expected)
    expected_facts = expected_artifact.get("normalized_facts")
    if not isinstance(expected_facts, list) or len(expected_facts) != 135:
        _fail("REBUILT_EXPECTED_FACTS_INVALID")
    bound = ingestion.load_frozen_formal_decision_v1(root)
    expected_projection = _expected_projection_from_ingestion(bound)
    _verify_artifact_byte_identity(expected, observed)
    semantics = {
        **_verify_artifact_semantics(
            artifact,
            expected_predecessor_artifact=predecessor_artifact,
            expected_projection=expected_projection,
        ),
        "artifact_bytes": len(observed),
        "artifact_SHA256": _sha256(observed),
    }
    coverage = _verify_coverage_contract()
    upstream = _verify_upstream_4lh_boundary(bound)
    tamper = _verify_tamper_probes(
        artifact,
        expected_payload=expected,
        expected_predecessor_artifact=predecessor_artifact,
        expected_projection=expected_projection,
    )
    lifecycle_simulations = check_lifecycle_simulations()
    safety = _verify_no_forbidden_or_large_files(root)
    return {
        "status": "PASS",
        "repository": repository,
        "Exact4": exact4,
        "dependencies": dependencies,
        "artifact": semantics,
        "coverage": coverage,
        "4LH_boundary": upstream,
        "tamper_probes": tamper,
        "lifecycle_simulations": lifecycle_simulations,
        "safety": safety,
        "repo_root_global_ROOT_dependency_removed": True,
        "current_census_refresh": False,
        "queue_refresh": False,
        "formal_refresh": False,
        "scientific_state_refresh": False,
        "preparation_refresh": False,
        "preview_refresh": False,
        "training_started": False,
        "ready_for_training": False,
        "feature_semantics_audit_required_later": True,
        "commit": False,
        "push": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    report = run_check_v1(parser.parse_args(argv).repo_root)
    if (
        report["status"] != "PASS"
        or report["current_census_refresh"] is not False
        or report["queue_refresh"] is not False
        or report["training_started"] is not False
        or report["ready_for_training"] is not False
        or report["feature_semantics_audit_required_later"] is not True
        or report["commit"] is not False
        or report["push"] is not False
    ):
        _fail("FINAL_OPERATION_BOUNDARY_INVALID")
    print("PASS")
    for record in report["Exact4"]:
        print(
            "EXACT4 "
            f"path={record['path']} bytes={record['bytes']} LOC={record['LOC']} "
            f"SHA256={record['SHA256']} git_mode={record['git_mode']}"
        )
    print("4LH_RECONCILIATION_V1_PASS=true")
    print("4LH_RECONCILIATION_REVISED1_PASS=true")
    print("4LH_RECONCILIATION_EXACT4_LOCAL=true")
    print(f"CHECKER_LIFECYCLE_PROFILE={report['repository']['lifecycle']}")
    print("CHECKER_CANDIDATE_UNTRACKED_SUPPORTED=true")
    print("CHECKER_TRACKED_CLEAN_SUPPORTED=true")
    print("CHECKER_COMMITTED_UNPUSHED_SIMULATION_PASS=true")
    print("CHECKER_PUSHED_SUCCESSOR_SIMULATION_PASS=true")
    print("CHECKER_SEMANTIC_TAMPER_PROBES_REAL=true")
    print("CHECKER_BYTE_TAMPER_PROBE_SEPARATE=true")
    print("CHECKER_REPO_ROOT_CONSISTENT=true")
    print("4LH_GENERIC_FACTS_ADDED=4")
    print("4LH_GENERIC_TOTAL_ACCEPTED_FACTS=135")
    print("4LH_CHEMISTRY_POSITIVE_DELTA=4")
    print("4LH_AUTHORITATIVE_TASK_LABELS_CREATED=false")
    print("4LH_EVENT_TASK_LABEL_ROWS_MATERIALIZED=false")
    print("4LH_TRAINING_MASK_TARGETS_AVAILABLE=false")
    print("EXACT5_B3_PRESENT=true")
    print("SIXTH_TASK=false")
    print("CURRENT_CENSUS_REFRESH=false")
    print("QUEUE_REFRESH=false")
    print("TRAINING_STARTED=false")
    print("READY_FOR_TRAINING=false")
    print("FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER=true")
    print("COMMIT=false")
    print("PUSH=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
