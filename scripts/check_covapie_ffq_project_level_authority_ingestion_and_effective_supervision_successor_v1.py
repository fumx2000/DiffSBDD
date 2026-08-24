#!/usr/bin/env python3
"""Fail-closed checker for FFQ project-authority effective supervision V1."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1
    as owner,
)
from covalent_ext import (  # noqa: E402
    covapie_k36_w1_reaction_family_and_warhead_rule_authority_creator_v1
    as k36_authority_creator,
)


BASELINE_COMMIT = "dd852e431d3826df39cfc06767f25b4a8b1fe3a0"
PRECOMMIT_PROFILE = (
    "FFQ_PROJECT_LEVEL_AUTHORITY_EFFECTIVE_SUPERVISION_"
    "PRECOMMIT_EXACT3_UNTRACKED"
)
PUBLISHED_PROFILE = (
    "FFQ_PROJECT_LEVEL_AUTHORITY_EFFECTIVE_SUPERVISION_"
    "PUBLISHED_CLEAN_DESCENDANT"
)
LIFECYCLE_ERROR = "FFQ_PROJECT_LEVEL_AUTHORITY_EFFECTIVE_SUPERVISION_LIFECYCLE_INVALID"
CANDIDATE_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_ffq_project_level_authority_ingestion_and_"
        "effective_supervision_successor_v1.py"
    ),
    Path(
        "scripts/check_covapie_ffq_project_level_authority_ingestion_and_"
        "effective_supervision_successor_v1.py"
    ),
    Path(
        "tests/test_covapie_ffq_project_level_authority_ingestion_and_"
        "effective_supervision_successor_v1.py"
    ),
)

FFQ_PUBLISHED_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT_PATH = FFQ_PUBLISHED_ROOT / "covapie_ffq_completed_human_decision_snapshot_v1.json"
MATRIX_PATH = FFQ_PUBLISHED_ROOT / "covapie_ffq_event_task_label_availability_v1.csv"
MANIFEST_PATH = FFQ_PUBLISHED_ROOT / "covapie_ffq_completed_decision_ingestion_manifest_v1.json"

FFQ_STATE_ROOT = Path(
    "covapie-state/manual-review/cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D"
)
FFQ_AIDS_ROOT = Path(
    "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D"
)
FAMILY_AUTHORITY_PATH = FFQ_STATE_ROOT / (
    "project-level-reaction-family-authority-v2/reaction_family_authority_v2.json"
)
FAMILY_RECEIPT_PATH = FFQ_STATE_ROOT / (
    "project-level-reaction-family-authority-v2/"
    "reaction_family_authority_materialization_receipt_v1.json"
)
RULE_AUTHORITY_PATH = FFQ_STATE_ROOT / (
    "project-level-warhead-rule-authority-v2/warhead_rule_authority_v2.json"
)
RULE_RECEIPT_PATH = FFQ_STATE_ROOT / (
    "project-level-warhead-rule-authority-v2/"
    "warhead_rule_authority_materialization_receipt_v1.json"
)
FAMILY_DECISION_PATH = FFQ_AIDS_ROOT / (
    "project-level-reaction-family-human-decision-v1/"
    "ffq_project_level_reaction_family_human_decision_v1.json"
)
RULE_DECISION_PATH = FFQ_AIDS_ROOT / (
    "project-level-warhead-rule-human-decision-v1/"
    "ffq_project_level_warhead_rule_human_decision_v1.json"
)

FAMILY_RECEIPT_BYTE_COUNT = 3581
FAMILY_RECEIPT_SHA256 = (
    "e8d2b03ddde42cc60bb2833861e1f7f26e7f87c751e4486bc16d9af48bde3780"
)
RULE_RECEIPT_BYTE_COUNT = 6119
RULE_RECEIPT_SHA256 = (
    "1412dc3893f6e7e3d9bba70c8365e34d79fa84f8521a0789a2be9f9b516f8c99"
)
FAMILY_CREATOR_PATH = Path(
    "src/covalent_ext/covapie_ffq_reaction_family_authority_creator_v1.py"
)
RULE_CREATOR_PATH = Path(
    "src/covalent_ext/covapie_ffq_warhead_rule_authority_creator_v1.py"
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


def _git(repo_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _lifecycle_fail(reason: str) -> None:
    raise ValueError(f"{LIFECYCLE_ERROR}:{reason}")


def observe_repository_state_v1(repo_root: Path) -> dict[str, object]:
    """Observe Git facts used by both supported lifecycle profiles."""

    repo_root = repo_root.resolve()
    head = _git(repo_root, "rev-parse", "HEAD")
    origin_main = _git(repo_root, "rev-parse", "refs/remotes/origin/main")
    behind_text, ahead_text = _git(
        repo_root,
        "rev-list",
        "--left-right",
        "--count",
        "refs/remotes/origin/main...HEAD",
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
    exact = tuple(sorted(path.as_posix() for path in CANDIDATE_PATHS))
    tracked_candidates = tuple(
        sorted(
            line
            for line in _git(repo_root, "ls-files", "--", *exact).splitlines()
            if line
        )
    )

    def is_ancestor(reference: str) -> bool:
        return (
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, reference],
                cwd=repo_root,
                check=False,
                capture_output=True,
            ).returncode
            == 0
        )

    return {
        "branch": _git(repo_root, "branch", "--show-current"),
        "head": head,
        "origin_main": origin_main,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "baseline_ancestor_of_head": is_ancestor(head),
        "baseline_ancestor_of_origin_main": is_ancestor(origin_main),
        "modified_tracked_paths": modified,
        "staged_paths": staged,
        "untracked_paths": untracked,
        "tracked_candidate_paths": tracked_candidates,
    }


def validate_repository_observation_v1(observation: Mapping[str, object]) -> str:
    """Return the one valid lifecycle profile or fail closed."""

    if observation.get("branch") != "main":
        _lifecycle_fail("BRANCH_NOT_MAIN")
    if observation.get("head") != observation.get("origin_main"):
        _lifecycle_fail("HEAD_ORIGIN_MAIN_MISMATCH")
    if observation.get("ahead") != 0 or observation.get("behind") != 0:
        _lifecycle_fail("AHEAD_BEHIND_NOT_ZERO_ZERO")
    if observation.get("baseline_ancestor_of_head") is not True:
        _lifecycle_fail("BASELINE_NOT_ANCESTOR_OF_HEAD")
    if observation.get("baseline_ancestor_of_origin_main") is not True:
        _lifecycle_fail("BASELINE_NOT_ANCESTOR_OF_ORIGIN_MAIN")
    if observation.get("modified_tracked_paths") != ():
        _lifecycle_fail("MODIFIED_TRACKED_FILES_PRESENT")
    if observation.get("staged_paths") != ():
        _lifecycle_fail("STAGED_FILES_PRESENT")
    exact = tuple(sorted(path.as_posix() for path in CANDIDATE_PATHS))
    untracked = tuple(observation.get("untracked_paths", ()))
    tracked = tuple(observation.get("tracked_candidate_paths", ()))
    head = observation.get("head")
    if head == BASELINE_COMMIT and untracked == exact and tracked == ():
        return PRECOMMIT_PROFILE
    if head != BASELINE_COMMIT and untracked == () and tracked == exact:
        return PUBLISHED_PROFILE
    _lifecycle_fail("UNSUPPORTED_OR_MIXED_CANDIDATE_PATH_STATE")


def verify_candidate_exact3_v1(repo_root: Path) -> dict[str, object]:
    """Verify exact inventory, lifecycle, regular-file status, and text safety."""

    repo_root = repo_root.resolve()
    observation = observe_repository_state_v1(repo_root)
    lifecycle = validate_repository_observation_v1(observation)
    exact = tuple(sorted(path.as_posix() for path in CANDIDATE_PATHS))
    if len(CANDIDATE_PATHS) != 3 or len(set(CANDIDATE_PATHS)) != 3:
        raise ValueError("CANDIDATE_EXACT3_INVENTORY_INVALID")
    file_bytes: dict[str, int] = {}
    file_sha256: dict[str, str] = {}
    for relative in CANDIDATE_PATHS:
        path = repo_root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError("CANDIDATE_FILE_NOT_REGULAR:" + relative.as_posix())
        payload = path.read_bytes()
        if (
            payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
        ):
            raise ValueError("CANDIDATE_TEXT_SAFETY_INVALID:" + relative.as_posix())
        payload.decode("utf-8")
        if relative.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("CANDIDATE_FORBIDDEN_SUFFIX:" + relative.as_posix())
        file_bytes[relative.as_posix()] = len(payload)
        file_sha256[relative.as_posix()] = hashlib.sha256(payload).hexdigest()
    candidate_stem = "covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1"
    pyc = tuple(repo_root.rglob(candidate_stem + "*.pyc"))
    if pyc:
        raise ValueError("CANDIDATE_NAMED_PYC_PRESENT")
    return {
        "lifecycle_profile": lifecycle,
        "candidate_publication_file_count": 3,
        "candidate_exact3_paths": list(exact),
        "candidate_file_bytes": file_bytes,
        "candidate_file_sha256": file_sha256,
        "branch": observation["branch"],
        "HEAD": observation["head"],
        "origin_main": observation["origin_main"],
        "ahead": observation["ahead"],
        "behind": observation["behind"],
        "modified_tracked_path_count": len(observation["modified_tracked_paths"]),
        "staged_path_count": len(observation["staged_paths"]),
        "untracked_paths": list(observation["untracked_paths"]),
        "candidate_named_pyc_count": 0,
    }


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


def _tree_content_snapshot(root: Path) -> tuple[tuple[str, str, int, str], ...]:
    """Capture path/type/bytes/hash evidence without using filesystem metadata."""

    if not root.is_dir() or root.is_symlink():
        raise ValueError("WATCHED_SOURCE_DIRECTORY_INVALID:" + root.as_posix())
    rows: list[tuple[str, str, int, str]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            target = path.readlink().as_posix().encode("utf-8")
            rows.append((relative, "symlink", len(target), hashlib.sha256(target).hexdigest()))
        elif path.is_dir():
            rows.append((relative, "directory", 0, ""))
        elif path.is_file():
            payload = path.read_bytes()
            rows.append((relative, "file", len(payload), hashlib.sha256(payload).hexdigest()))
        else:
            raise ValueError("WATCHED_SOURCE_SPECIAL_FILE_PRESENT:" + path.as_posix())
    return tuple(rows)


def _read_bound_regular(
    path: Path, *, byte_count: int, sha256: str, label: str
) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError(label + "_NOT_REGULAR")
    payload = path.read_bytes()
    if len(payload) != byte_count:
        raise ValueError(label + "_BYTE_COUNT_MISMATCH")
    if hashlib.sha256(payload).hexdigest() != sha256:
        raise ValueError(label + "_SHA256_MISMATCH")
    return payload


def _read_inputs(repo_root: Path) -> dict[str, Any]:
    parent = repo_root.parent
    snapshot = _read_bound_regular(
        repo_root / SNAPSHOT_PATH,
        byte_count=owner.COMPLETED_DECISION_SNAPSHOT_BYTE_COUNT,
        sha256=owner.COMPLETED_DECISION_SNAPSHOT_SHA256,
        label="PUBLISHED_FFQ_SNAPSHOT",
    )
    matrix = _read_bound_regular(
        repo_root / MATRIX_PATH,
        byte_count=owner.EVENT_TASK_LABEL_AVAILABILITY_BYTE_COUNT,
        sha256=owner.EVENT_TASK_LABEL_AVAILABILITY_SHA256,
        label="PUBLISHED_FFQ_MATRIX",
    )
    family = _read_bound_regular(
        parent / FAMILY_AUTHORITY_PATH,
        byte_count=owner.REACTION_FAMILY_AUTHORITY_FILE_BYTE_COUNT,
        sha256=owner.REACTION_FAMILY_AUTHORITY_FILE_SHA256,
        label="MATERIALIZED_FFQ_FAMILY_AUTHORITY",
    )
    rule = _read_bound_regular(
        parent / RULE_AUTHORITY_PATH,
        byte_count=owner.WARHEAD_RULE_AUTHORITY_FILE_BYTE_COUNT,
        sha256=owner.WARHEAD_RULE_AUTHORITY_FILE_SHA256,
        label="MATERIALIZED_FFQ_WARHEAD_RULE_AUTHORITY",
    )
    family_receipt = _read_bound_regular(
        parent / FAMILY_RECEIPT_PATH,
        byte_count=FAMILY_RECEIPT_BYTE_COUNT,
        sha256=FAMILY_RECEIPT_SHA256,
        label="MATERIALIZED_FFQ_FAMILY_RECEIPT",
    )
    rule_receipt = _read_bound_regular(
        parent / RULE_RECEIPT_PATH,
        byte_count=RULE_RECEIPT_BYTE_COUNT,
        sha256=RULE_RECEIPT_SHA256,
        label="MATERIALIZED_FFQ_RULE_RECEIPT",
    )
    family_decision = _read_bound_regular(
        parent / FAMILY_DECISION_PATH,
        byte_count=32668,
        sha256="eb2e98e25459759b4b40588310ad16a42cb280f1155d599e340f5863574d0d51",
        label="FFQ_FAMILY_HUMAN_DECISION",
    )
    rule_decision = _read_bound_regular(
        parent / RULE_DECISION_PATH,
        byte_count=37455,
        sha256="d03d2d3d3d414beb195c8bddb0d11835661d88a43f813f1e3d86787b852737ea",
        label="FFQ_RULE_HUMAN_DECISION",
    )
    baseline: dict[str, bytes] = {}
    for source in k36_authority_creator.EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1:
        path = parent / source["source_path"]
        if source["source_path"].startswith("data/"):
            path = repo_root / source["source_path"]
        baseline[source["source_path"]] = _read_bound_regular(
            path,
            byte_count=path.stat().st_size,
            sha256=source["source_sha256"],
            label="APPROVED_AUTHORITY_BASELINE_SOURCE",
        )
    k36: dict[str, bytes] = {}
    for source in owner.K36_PUBLISHED_AUTHORITY_SOURCES_V1:
        path = parent / source["source_path"]
        k36[source["source_path"]] = _read_bound_regular(
            path,
            byte_count=path.stat().st_size,
            sha256=source["source_sha256"],
            label="K36_PUBLISHED_AUTHORITY_SOURCE",
        )
    return {
        "completed_decision_snapshot_payload": snapshot,
        "event_task_label_availability_payload": matrix,
        "reaction_family_authority_payload": family,
        "warhead_rule_authority_payload": rule,
        "reaction_family_human_decision_payload": family_decision,
        "warhead_rule_human_decision_payload": rule_decision,
        "approved_authority_baseline_source_payloads": baseline,
        "k36_published_authority_payloads": k36,
        "family_receipt": family_receipt,
        "rule_receipt": rule_receipt,
    }


def _validate_receipts_and_canonical_authorities(inputs: Mapping[str, Any]) -> None:
    family = owner.strict_parse_authority_json_v1(inputs["reaction_family_authority_payload"])
    rule = owner.strict_parse_authority_json_v1(inputs["warhead_rule_authority_payload"])
    family_canonical = _canonical_json_bytes(family)
    rule_canonical = _canonical_json_bytes(rule)
    if (
        hashlib.sha256(family_canonical).hexdigest()
        != owner.REACTION_FAMILY_AUTHORITY_CANONICAL_PAYLOAD_SHA256
        or hashlib.sha256(rule_canonical).hexdigest()
        != owner.WARHEAD_RULE_AUTHORITY_CANONICAL_PAYLOAD_SHA256
        or len(rule_canonical) != owner.WARHEAD_RULE_AUTHORITY_CANONICAL_PAYLOAD_BYTE_COUNT
    ):
        raise ValueError("AUTHORITY_CANONICAL_PAYLOAD_BINDING_INVALID")
    family_receipt = owner.strict_parse_authority_json_v1(inputs["family_receipt"])
    rule_receipt = owner.strict_parse_authority_json_v1(inputs["rule_receipt"])
    if (
        family_receipt.get("authority_file_byte_count")
        != owner.REACTION_FAMILY_AUTHORITY_FILE_BYTE_COUNT
        or family_receipt.get("authority_file_sha256")
        != owner.REACTION_FAMILY_AUTHORITY_FILE_SHA256
        or family_receipt.get("authority_payload_canonical_sha256")
        != owner.REACTION_FAMILY_AUTHORITY_CANONICAL_PAYLOAD_SHA256
        or family_receipt.get("authority_id") != owner.REACTION_FAMILY_AUTHORITY_ID
        or family_receipt.get("authority_semantic_signature_sha256")
        != owner.REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256
        or family_receipt.get("materialization_boundary", {}).get(
            "reaction_family_registration_performed"
        )
        is not False
    ):
        raise ValueError("FAMILY_RECEIPT_DIRECT_EVIDENCE_INVALID")
    if (
        rule_receipt.get("authority_file_byte_count")
        != owner.WARHEAD_RULE_AUTHORITY_FILE_BYTE_COUNT
        or rule_receipt.get("authority_file_sha256")
        != owner.WARHEAD_RULE_AUTHORITY_FILE_SHA256
        or rule_receipt.get("authority_payload_canonical_sha256")
        != owner.WARHEAD_RULE_AUTHORITY_CANONICAL_PAYLOAD_SHA256
        or rule_receipt.get("warhead_rule_authority_id")
        != owner.WARHEAD_RULE_AUTHORITY_ID
        or rule_receipt.get("warhead_rule_semantic_signature_sha256")
        != owner.WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256
        or rule_receipt.get("final_reaction_family_authority_id")
        != owner.REACTION_FAMILY_AUTHORITY_ID
        or rule_receipt.get("materialization_boundary", {}).get(
            "family_rule_registration_performed"
        )
        is not False
    ):
        raise ValueError("RULE_RECEIPT_DIRECT_EVIDENCE_INVALID")


def _reverse_mapping_order(value: Any) -> Any:
    if type(value) is dict:
        return {
            key: _reverse_mapping_order(item)
            for key, item in reversed(tuple(value.items()))
        }
    if type(value) is list:
        return [_reverse_mapping_order(item) for item in value]
    return value


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Run lifecycle, real-source, semantics, collision, and determinism gates."""

    repo_root = repo_root.resolve()
    candidate = verify_candidate_exact3_v1(repo_root)
    watched_roots = (
        repo_root / FFQ_PUBLISHED_ROOT,
        repo_root.parent / FFQ_STATE_ROOT,
        repo_root.parent / FFQ_AIDS_ROOT,
    )
    watched_before = {
        path.as_posix(): _tree_content_snapshot(path) for path in watched_roots
    }
    inputs = _read_inputs(repo_root)
    _validate_receipts_and_canonical_authorities(inputs)
    family_creator_payload = (repo_root / FAMILY_CREATOR_PATH).read_bytes()
    rule_creator_payload = (repo_root / RULE_CREATOR_PATH).read_bytes()
    if hashlib.sha256(family_creator_payload).hexdigest() != owner.FAMILY_CREATOR_SOURCE_SHA256:
        raise ValueError("PUBLISHED_FAMILY_CREATOR_SOURCE_SHA256_MISMATCH")
    if hashlib.sha256(rule_creator_payload).hexdigest() != owner.WARHEAD_RULE_CREATOR_SOURCE_SHA256:
        raise ValueError("PUBLISHED_RULE_CREATOR_SOURCE_SHA256_MISMATCH")

    build_inputs = {
        key: value
        for key, value in inputs.items()
        if key not in ("family_receipt", "rule_receipt")
    }
    source_snapshot = {
        key: (
            dict(value) if isinstance(value, Mapping) else value
        )
        for key, value in build_inputs.items()
    }
    first = owner.build_covapie_ffq_project_level_authority_effective_supervision_v1(
        **build_inputs
    )
    second = owner.build_covapie_ffq_project_level_authority_effective_supervision_v1(
        **build_inputs
    )
    if first != second:
        raise ValueError("DETERMINISTIC_DOUBLE_BUILD_DEEP_EQUAL_MISMATCH")
    if _canonical_json_bytes(first) != _canonical_json_bytes(second):
        raise ValueError("DETERMINISTIC_DOUBLE_BUILD_CANONICAL_BYTES_MISMATCH")
    if source_snapshot != build_inputs:
        raise ValueError("BUILDER_INPUT_MUTATION_DETECTED")
    owner.validate_covapie_ffq_project_level_authority_effective_supervision_v1(first)

    reordered_inputs = dict(build_inputs)
    reordered_inputs["reaction_family_authority_payload"] = _canonical_json_bytes(
        _reverse_mapping_order(
            owner.strict_parse_authority_json_v1(
                inputs["reaction_family_authority_payload"]
            )
        )
    )
    reordered_inputs["warhead_rule_authority_payload"] = _canonical_json_bytes(
        _reverse_mapping_order(
            owner.strict_parse_authority_json_v1(inputs["warhead_rule_authority_payload"])
        )
    )
    reordered = owner.build_covapie_ffq_project_level_authority_effective_supervision_v1(
        **reordered_inputs
    )
    if reordered != first:
        raise ValueError("AUTHORITY_KEY_ORDER_CHANGED_EFFECTIVE_RESULT")
    watched_after = {
        path.as_posix(): _tree_content_snapshot(path) for path in watched_roots
    }
    if watched_after != watched_before:
        raise ValueError("WATCHED_PUBLISHED_OR_STATE_SOURCE_MODIFIED")

    records = first["effective_supervision_records"]
    summary = first["ingestion_effective_authority_summary"]
    family_count = sum(record["reaction_family_authority_established"] for record in records)
    rule_count = sum(record["warhead_rule_authority_established"] for record in records)
    candidate_count = sum(record["non_geometry_training_candidate"] for record in records)
    excluded_count = sum(record["human_training_exclusion_preserved"] for record in records)
    if (
        len(records) != 8
        or family_count != 8
        or rule_count != 8
        or candidate_count != 4
        or excluded_count != 4
        or sum(record["training_admitted"] for record in records) != 0
        or sum(record["POST_geometry_training_label_available_now"] for record in records) != 0
        or any(record["warhead_type_target_available"] for record in records)
        or any(record["training_mask_targets_available_now"] for record in records)
        or summary.get("ffq_effective_authority_linkage_complete") is not True
        or summary.get("state_modified") is not False
        or summary.get("training_performed") is not False
        or summary.get("network_performed") is not False
    ):
        raise ValueError("EFFECTIVE_SUPERVISION_DIRECT_EVIDENCE_INVALID")
    return {
        "lifecycle_profile": candidate["lifecycle_profile"],
        "candidate": candidate,
        "effective_supervision_record_count": len(records),
        "reaction_family_authority_id": owner.REACTION_FAMILY_AUTHORITY_ID,
        "warhead_rule_authority_id": owner.WARHEAD_RULE_AUTHORITY_ID,
        "family_linked_event_count": family_count,
        "rule_linked_event_count": rule_count,
        "3VCY_training_candidate_count": candidate_count,
        "4R7U_training_excluded_count": excluded_count,
        "training_admitted_count": 0,
        "POST_geometry_training_label_available_count": 0,
        "warhead_type_target_available": False,
        "training_mask_targets_available_now": False,
        "ffq_effective_authority_linkage_complete": True,
        "approved_authority_collision_status": "NO_APPROVED_AUTHORITY_COLLISION",
        "K36_authority_coexistence_verified": True,
        "disk_family_authority_equals_fresh_creator_output": True,
        "disk_warhead_rule_authority_equals_fresh_creator_output": True,
        "disk_authority_key_order_treated_as_semantically_irrelevant": True,
        "deterministic_double_build_deep_equal": True,
        "deterministic_double_build_canonical_bytes_equal": True,
        "effective_supervision_materialized": False,
        "watched_source_trees_byte_identical_after_build": True,
        "state_modified": False,
        "training_performed": False,
        "network_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    arguments = parser.parse_args()
    result = run_check_v1(arguments.repo_root)
    for key in (
        "lifecycle_profile",
        "effective_supervision_record_count",
        "reaction_family_authority_id",
        "warhead_rule_authority_id",
        "family_linked_event_count",
        "rule_linked_event_count",
        "3VCY_training_candidate_count",
        "4R7U_training_excluded_count",
        "training_admitted_count",
        "POST_geometry_training_label_available_count",
        "warhead_type_target_available",
        "training_mask_targets_available_now",
        "ffq_effective_authority_linkage_complete",
        "approved_authority_collision_status",
        "K36_authority_coexistence_verified",
        "disk_family_authority_equals_fresh_creator_output",
        "disk_warhead_rule_authority_equals_fresh_creator_output",
        "disk_authority_key_order_treated_as_semantically_irrelevant",
        "effective_supervision_materialized",
        "watched_source_trees_byte_identical_after_build",
        "state_modified",
        "training_performed",
        "network_performed",
    ):
        value = result[key]
        print(f"{key}={str(value).lower() if type(value) is bool else value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
