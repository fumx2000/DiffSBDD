#!/usr/bin/env python3
"""Fail-closed checker for the FFQ warhead-rule authority creator V1."""

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
    covapie_ffq_reaction_family_authority_creator_v1 as family_creator,
)
from covalent_ext import (  # noqa: E402
    covapie_ffq_warhead_rule_authority_creator_v1 as creator,
)


BASELINE_COMMIT = "f719f4480a9556bd5d47bf17954692403043131b"
PRECOMMIT_PROFILE = (
    "FFQ_WARHEAD_RULE_AUTHORITY_CREATOR_PRECOMMIT_EXACT3_UNTRACKED"
)
PUBLISHED_PROFILE = (
    "FFQ_WARHEAD_RULE_AUTHORITY_CREATOR_PUBLISHED_CLEAN_DESCENDANT"
)
LIFECYCLE_ERROR = "FFQ_WARHEAD_RULE_AUTHORITY_CREATOR_LIFECYCLE_INVALID"
CANDIDATE_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_ffq_warhead_rule_authority_creator_v1.py"
    ),
    Path("scripts/check_covapie_ffq_warhead_rule_authority_creator_v1.py"),
    Path("tests/test_covapie_ffq_warhead_rule_authority_creator_v1.py"),
)
WARHEAD_HUMAN_DECISION_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D/"
    "project-level-warhead-rule-human-decision-v1/"
    "ffq_project_level_warhead_rule_human_decision_v1.json"
)
FAMILY_HUMAN_DECISION_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D/"
    "project-level-reaction-family-human-decision-v1/"
    "ffq_project_level_reaction_family_human_decision_v1.json"
)
FAMILY_AUTHORITY_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review/"
    "cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D/"
    "project-level-reaction-family-authority-v2/"
    "reaction_family_authority_v2.json"
)
FAMILY_RECEIPT_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review/"
    "cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D/"
    "project-level-reaction-family-authority-v2/"
    "reaction_family_authority_materialization_receipt_v1.json"
)
FAMILY_AUTHORITY_BYTE_COUNT = 7778
FAMILY_AUTHORITY_FILE_SHA256 = (
    "d79658a33d910e7ca828247706d2690697c9e988f66fac53c8265fae020b7f62"
)
FAMILY_AUTHORITY_CANONICAL_PAYLOAD_SHA256 = (
    "6007c9419d51799f33e5cd948a9228abc34f4a6fbea283f94375b1e9b126a6ca"
)
FAMILY_RECEIPT_BYTE_COUNT = 3581
FAMILY_RECEIPT_FILE_SHA256 = (
    "e8d2b03ddde42cc60bb2833861e1f7f26e7f87c751e4486bc16d9af48bde3780"
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
    """Observe all Git facts needed for either supported lifecycle."""

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
        line
        for line in _git(repo_root, "diff", "--name-only").splitlines()
        if line
    )
    staged = tuple(
        line
        for line in _git(
            repo_root, "diff", "--cached", "--name-only"
        ).splitlines()
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
            for line in _git(
                repo_root, "ls-files", "--", *exact
            ).splitlines()
            if line
        )
    )

    def is_ancestor(reference: str) -> bool:
        return subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASELINE_COMMIT, reference],
            cwd=repo_root,
            check=False,
            capture_output=True,
        ).returncode == 0

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


def validate_repository_observation_v1(
    observation: Mapping[str, object],
) -> str:
    """Return the sole valid lifecycle profile or fail closed."""

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
    """Verify exact candidate inventory, lifecycle, and text safety."""

    repo_root = repo_root.resolve()
    observation = observe_repository_state_v1(repo_root)
    lifecycle = validate_repository_observation_v1(observation)
    exact = tuple(sorted(path.as_posix() for path in CANDIDATE_PATHS))
    if len(CANDIDATE_PATHS) != 3 or len(set(CANDIDATE_PATHS)) != 3:
        raise ValueError("CANDIDATE_EXACT3_INVENTORY_INVALID")
    file_sha256: dict[str, str] = {}
    file_bytes: dict[str, int] = {}
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
            raise ValueError(
                "CANDIDATE_TEXT_OR_LF_INVARIANT_INVALID:"
                + relative.as_posix()
            )
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(
                "CANDIDATE_UTF8_INVALID:" + relative.as_posix()
            ) from error
        if relative.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("CANDIDATE_FORBIDDEN_SUFFIX:" + relative.as_posix())
        file_sha256[relative.as_posix()] = hashlib.sha256(payload).hexdigest()
        file_bytes[relative.as_posix()] = len(payload)
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
        "baseline_ancestor_of_HEAD": observation["baseline_ancestor_of_head"],
        "baseline_ancestor_of_origin_main": observation[
            "baseline_ancestor_of_origin_main"
        ],
        "modified_tracked_path_count": len(
            observation["modified_tracked_paths"]
        ),
        "staged_path_count": len(observation["staged_paths"]),
        "untracked_paths": list(observation["untracked_paths"]),
    }


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


def _strict_unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("MATERIALIZED_FAMILY_JSON_DUPLICATE_KEY:" + key)
        result[key] = value
    return result


def _strict_reject_nonfinite(value: str) -> None:
    raise ValueError("MATERIALIZED_FAMILY_JSON_NONFINITE:" + value)


def strict_parse_canonical_json_file_v1(
    payload: bytes,
    *,
    expected_byte_count: int,
    expected_file_sha256: str,
    source_name: str,
) -> dict[str, object]:
    """Strictly parse one frozen LF-terminated canonical JSON object."""

    if type(payload) is not bytes:
        raise ValueError(source_name + "_BYTES_REQUIRED")
    if len(payload) != expected_byte_count:
        raise ValueError(source_name + "_BYTE_COUNT_MISMATCH")
    if hashlib.sha256(payload).hexdigest() != expected_file_sha256:
        raise ValueError(source_name + "_FILE_SHA256_MISMATCH")
    if (
        payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        raise ValueError(source_name + "_TEXT_SAFETY_INVALID")
    try:
        parsed = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_strict_unique_object,
            parse_constant=_strict_reject_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError(source_name + "_JSON_INVALID") from error
    if type(parsed) is not dict:
        raise ValueError(source_name + "_JSON_OBJECT_REQUIRED")
    canonical = _canonical_json_bytes(parsed)
    if payload != canonical + b"\n":
        raise ValueError(source_name + "_CANONICAL_SERIALIZATION_MISMATCH")
    return parsed


def _verify_materialized_family_dependency_v1(
    repo_root: Path,
) -> dict[str, object]:
    family_path = repo_root.parent / FAMILY_AUTHORITY_RELATIVE_TO_REPOSITORY_PARENT
    receipt_path = repo_root.parent / FAMILY_RECEIPT_RELATIVE_TO_REPOSITORY_PARENT
    family_decision_path = (
        repo_root.parent / FAMILY_HUMAN_DECISION_RELATIVE_TO_REPOSITORY_PARENT
    )
    family_bytes = family_path.read_bytes()
    receipt_bytes = receipt_path.read_bytes()
    family_decision_before = family_decision_path.read_bytes()
    disk_family = strict_parse_canonical_json_file_v1(
        family_bytes,
        expected_byte_count=FAMILY_AUTHORITY_BYTE_COUNT,
        expected_file_sha256=FAMILY_AUTHORITY_FILE_SHA256,
        source_name="MATERIALIZED_FAMILY_AUTHORITY",
    )
    receipt = strict_parse_canonical_json_file_v1(
        receipt_bytes,
        expected_byte_count=FAMILY_RECEIPT_BYTE_COUNT,
        expected_file_sha256=FAMILY_RECEIPT_FILE_SHA256,
        source_name="MATERIALIZED_FAMILY_RECEIPT",
    )
    family_canonical_sha = hashlib.sha256(
        _canonical_json_bytes(disk_family)
    ).hexdigest()
    if family_canonical_sha != FAMILY_AUTHORITY_CANONICAL_PAYLOAD_SHA256:
        raise ValueError("MATERIALIZED_FAMILY_CANONICAL_PAYLOAD_SHA256_MISMATCH")

    family_creator.validate_covapie_ffq_project_level_reaction_family_human_decision_v1(
        family_decision_before
    )
    fresh_result = family_creator.build_covapie_ffq_reaction_family_authority_v1(
        family_decision_before
    )
    family_decision_after = family_decision_path.read_bytes()
    if family_decision_before != family_decision_after:
        raise ValueError("FAMILY_HUMAN_DECISION_SOURCE_MODIFIED")
    fresh_family = fresh_result["reaction_family_authority"]
    if disk_family != fresh_family:
        raise ValueError("DISK_FAMILY_AUTHORITY_NOT_FRESH_CREATOR_OUTPUT")
    family_creator.validate_covapie_ffq_reaction_family_authority_payload_v2(
        fresh_family
    )
    if (
        fresh_family["authority_id"]
        != creator.FINAL_REACTION_FAMILY_AUTHORITY_ID
        or fresh_family["canonical_semantic_signature_sha256"]
        != creator.FAMILY_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
        or receipt.get("authority_file_byte_count")
        != FAMILY_AUTHORITY_BYTE_COUNT
        or receipt.get("authority_file_sha256") != FAMILY_AUTHORITY_FILE_SHA256
        or receipt.get("authority_payload_canonical_sha256")
        != FAMILY_AUTHORITY_CANONICAL_PAYLOAD_SHA256
        or receipt.get("authority_id")
        != creator.FINAL_REACTION_FAMILY_AUTHORITY_ID
        or receipt.get("authority_semantic_signature_sha256")
        != creator.FAMILY_AUTHORITY_SEMANTIC_SIGNATURE_SHA256
        or receipt.get("materialization_status")
        != (
            "IMMUTABLE_PROJECT_LEVEL_REACTION_FAMILY_AUTHORITY_FILE_"
            "MATERIALIZED_NOT_REGISTERED"
        )
    ):
        raise ValueError("MATERIALIZED_FAMILY_OR_RECEIPT_DIRECT_EVIDENCE_INVALID")
    return {
        "reaction_family_authority_dependency_verified": True,
        "family_authority_file_byte_count": len(family_bytes),
        "family_authority_file_sha256": hashlib.sha256(family_bytes).hexdigest(),
        "family_authority_receipt_byte_count": len(receipt_bytes),
        "family_authority_receipt_sha256": hashlib.sha256(
            receipt_bytes
        ).hexdigest(),
        "family_authority_canonical_payload_sha256": family_canonical_sha,
        "family_authority_id": fresh_family["authority_id"],
        "family_authority_semantic_signature_sha256": fresh_family[
            "canonical_semantic_signature_sha256"
        ],
        "disk_family_authority_equals_fresh_creator_output": True,
        "fresh_family_creator_payload_validator_passed": True,
        "disk_family_authority_key_order_treated_as_semantically_irrelevant": True,
    }


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Run lifecycle, family binding, semantics, and determinism checks."""

    repo_root = repo_root.resolve()
    candidate = verify_candidate_exact3_v1(repo_root)
    family = _verify_materialized_family_dependency_v1(repo_root)
    decision_path = (
        repo_root.parent / WARHEAD_HUMAN_DECISION_RELATIVE_TO_REPOSITORY_PARENT
    )
    before = decision_path.read_bytes()
    validated = (
        creator.validate_covapie_ffq_project_level_warhead_rule_human_decision_v1(
            before
        )
    )
    first = creator.build_covapie_ffq_warhead_rule_authority_v1(before)
    second = creator.build_covapie_ffq_warhead_rule_authority_v1(before)
    after = decision_path.read_bytes()
    if before != after:
        raise ValueError("HUMAN_DECISION_SOURCE_MODIFIED")
    if first != second:
        raise ValueError("DETERMINISTIC_DOUBLE_BUILD_DEEP_EQUAL_MISMATCH")
    first_bytes = _canonical_json_bytes(first)
    second_bytes = _canonical_json_bytes(second)
    if first_bytes != second_bytes:
        raise ValueError("DETERMINISTIC_DOUBLE_BUILD_BYTES_MISMATCH")
    authority = first["warhead_rule_authority"]
    creator.validate_covapie_ffq_warhead_rule_authority_payload_v2(authority)
    canonical_authority_bytes = _canonical_json_bytes(authority)
    parsed_canonical_authority = json.loads(
        canonical_authority_bytes.decode("ascii"),
        object_pairs_hook=_strict_unique_object,
        parse_constant=_strict_reject_nonfinite,
    )
    if (
        type(parsed_canonical_authority) is not dict
        or parsed_canonical_authority != authority
        or tuple(parsed_canonical_authority) == tuple(authority)
        or tuple(parsed_canonical_authority["canonical_semantic_signature"])
        == tuple(authority["canonical_semantic_signature"])
        or tuple(
            parsed_canonical_authority[
                "source_candidate_to_authority_provenance"
            ]
        )
        == tuple(authority["source_candidate_to_authority_provenance"])
        or tuple(parsed_canonical_authority["source_human_review_provenance"])
        == tuple(authority["source_human_review_provenance"])
    ):
        raise ValueError("CANONICAL_ROUNDTRIP_KEY_ORDER_EVIDENCE_INVALID")
    creator.validate_covapie_ffq_warhead_rule_authority_payload_v2(
        parsed_canonical_authority
    )
    semantic = authority["canonical_semantic_signature"]
    local_rule = semantic["canonical_local_warhead_rule_contract"][
        "canonical_local_rule"
    ]
    local_sha = creator.authority_semantic_signature_sha256_v1(local_rule)
    summary = first["creation_readiness_summary"]
    if (
        validated["decision_status"]
        != "HUMAN_APPROVED_PROJECT_LEVEL_WARHEAD_RULE_DECISION"
        or local_sha != creator.CANDIDATE_CANONICAL_LOCAL_RULE_SHA256
        or summary["reaction_family_authority_dependency_verified"] is not True
        or summary["warhead_rule_authority_payload_ready"] is not True
        or summary["warhead_rule_authority_payload_built_in_memory"] is not True
        or summary["persisted_warhead_rule_authority_created"] is not False
        or summary["warhead_rule_registration_performed"] is not False
        or summary["effective_authority_updated"] is not False
        or summary["runtime_authority_created"] is not False
        or summary["authority_file_materialized"] is not False
        or summary["ready_for_training"] is not False
        or summary[
            "feature_semantics_audit_required_before_formal_training"
        ]
        is not True
        or summary["feature_semantics_audit_performed"] is not False
    ):
        raise ValueError("AUTHORITY_OR_READINESS_DIRECT_EVIDENCE_INVALID")
    forbidden_api_names = {
        "materialize_to_disk",
        "write_authority",
        "register_authority",
        "update_registry",
        "update_effective_authority",
        "runtime_admit",
    }
    if forbidden_api_names.intersection(vars(creator)):
        raise ValueError("DISK_REGISTRY_OR_RUNTIME_WRITE_API_EXPOSED")
    return {
        "lifecycle_profile": candidate["lifecycle_profile"],
        "candidate": candidate,
        "human_decision_byte_count": len(before),
        "human_decision_sha256": hashlib.sha256(before).hexdigest(),
        **family,
        "authority_schema_version": authority["authority_schema_version"],
        "source_candidate_warhead_rule_id": (
            creator.SOURCE_CANDIDATE_WARHEAD_RULE_ID
        ),
        "candidate_canonical_local_rule_sha256": local_sha,
        "approved_authority_semantic_signature_sha256": (
            creator.authority_semantic_signature_sha256_v1(semantic)
        ),
        "final_warhead_rule_authority_id": authority["authority_id"],
        "authority_payload_canonical_sha256": hashlib.sha256(
            canonical_authority_bytes
        ).hexdigest(),
        "build_result_canonical_sha256": hashlib.sha256(first_bytes).hexdigest(),
        "canonical_roundtrip_payload_v2_validator_passed": True,
        "disk_key_order_semantically_irrelevant_by_public_validator": True,
        "deterministic_double_build_deep_equal": True,
        "deterministic_double_build_canonical_bytes_equal": True,
        "project_level_warhead_rule_human_decision_consumed": True,
        "human_decision_modified": False,
        "warhead_rule_authority_payload_built_in_memory": True,
        "warhead_rule_authority_payload_ready": True,
        "persisted_warhead_rule_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_rule_registration_performed": False,
        "authority_file_materialized": False,
        "effective_authority_updated": False,
        "runtime_authority_created": False,
        "SMARTS_generation_performed": False,
        "reusable_chemistry_authority_created": False,
        "tensorizer_integration_performed": False,
        "training_admission_created": False,
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
        "human_decision_byte_count",
        "human_decision_sha256",
        "reaction_family_authority_dependency_verified",
        "family_authority_file_sha256",
        "family_authority_receipt_sha256",
        "family_authority_canonical_payload_sha256",
        "disk_family_authority_equals_fresh_creator_output",
        "disk_family_authority_key_order_treated_as_semantically_irrelevant",
        "authority_schema_version",
        "source_candidate_warhead_rule_id",
        "candidate_canonical_local_rule_sha256",
        "family_authority_id",
        "approved_authority_semantic_signature_sha256",
        "final_warhead_rule_authority_id",
        "authority_payload_canonical_sha256",
        "build_result_canonical_sha256",
        "canonical_roundtrip_payload_v2_validator_passed",
        "disk_key_order_semantically_irrelevant_by_public_validator",
        "warhead_rule_authority_payload_ready",
        "persisted_warhead_rule_authority_created",
        "warhead_rule_registration_performed",
        "authority_file_materialized",
        "effective_authority_updated",
        "runtime_authority_created",
        "training_performed",
        "network_performed",
    ):
        print(f"{key}={result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
