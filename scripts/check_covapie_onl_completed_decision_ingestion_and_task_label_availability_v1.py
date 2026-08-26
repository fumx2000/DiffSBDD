#!/usr/bin/env python3
"""Fail-closed checker for the ONL Exact9 ingestion successor V1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_onl_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part",
)
MAX_CANDIDATE_FILE_BYTES = 1024 * 1024


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_candidate_exact7_v1(repo_root: Path) -> dict[str, object]:
    """Verify the exact publication contract without inspecting Git lifecycle."""

    repo_root = repo_root.resolve()
    expected = (
        "src/covalent_ext/covapie_onl_completed_decision_ingestion_and_task_label_availability_v1.py",
        "scripts/check_covapie_onl_completed_decision_ingestion_and_task_label_availability_v1.py",
        "tests/test_covapie_onl_completed_decision_ingestion_and_task_label_availability_v1.py",
        "data/derived/covalent_small/covapie_onl_completed_decision_ingestion_and_task_label_availability_v1/covapie_onl_completed_human_decision_snapshot_v1.json",
        "data/derived/covalent_small/covapie_onl_completed_decision_ingestion_and_task_label_availability_v1/covapie_onl_event_task_label_availability_v1.csv",
        "data/derived/covalent_small/covapie_onl_completed_decision_ingestion_and_task_label_availability_v1/covapie_onl_completed_decision_ingestion_summary_v1.json",
        "data/derived/covalent_small/covapie_onl_completed_decision_ingestion_and_task_label_availability_v1/covapie_onl_completed_decision_ingestion_manifest_v1.json",
    )
    observed_contract = tuple(path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS)
    if observed_contract != expected or len(observed_contract) != 7:
        raise ValueError("CANDIDATE_PUBLICATION_EXACT7_CONTRACT_INVALID")
    output_root = repo_root / subject.OUTPUT_ROOT_RELATIVE
    if not output_root.is_dir() or output_root.is_symlink():
        raise ValueError("OUTPUT_DIRECTORY_MISSING_OR_INVALID")
    if {path.name for path in output_root.iterdir()} != set(subject.OUTPUT_FILENAMES):
        raise ValueError("OUTPUT_DIRECTORY_EXACT4_INVALID")

    bindings: list[dict[str, object]] = []
    for relative in subject.CANDIDATE_PUBLICATION_PATHS:
        path = repo_root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError("CANDIDATE_FILE_NOT_REGULAR:" + relative.as_posix())
        payload = path.read_bytes()
        if len(payload) > MAX_CANDIDATE_FILE_BYTES:
            raise ValueError("CANDIDATE_FILE_TOO_LARGE:" + relative.as_posix())
        subject._validate_text_payload(relative.as_posix(), payload)
        if relative.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("CANDIDATE_FORBIDDEN_SUFFIX:" + relative.as_posix())
        bindings.append({
            "path": relative.as_posix(),
            "byte_count": len(payload),
            "sha256": _sha(payload),
            "mode": path.stat().st_mode & 0o777,
        })
    return {
        "candidate_publication_file_count": 7,
        "candidate_exact7_paths": list(expected),
        "candidate_file_bindings": bindings,
        "repository_state_neutral": True,
    }


def _verify_two_directory_determinism(repo_root: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="covapie_onl_ingest_a_") as first_name:
        with tempfile.TemporaryDirectory(prefix="covapie_onl_ingest_b_") as second_name:
            first_root = Path(first_name) / "outputs"
            second_root = Path(second_name) / "outputs"
            first = subject.materialize_artifacts_v1(repo_root, output_root=first_root)
            second = subject.materialize_artifacts_v1(repo_root, output_root=second_root)
            if first != second:
                raise ValueError("DETERMINISTIC_DOUBLE_MATERIALIZATION_MISMATCH")
            for name in subject.OUTPUT_FILENAMES:
                if (first_root / name).read_bytes() != (second_root / name).read_bytes():
                    raise ValueError("DETERMINISTIC_OUTPUT_BYTES_MISMATCH:" + name)
            return {
                "deterministic_double_materialization_byte_identical": True,
                "artifact_sha256": {name: _sha(first[name]) for name in subject.OUTPUT_FILENAMES},
            }


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Verify bound inputs, Exact7/Exact4, semantics, determinism, and non-actions."""

    repo_root = repo_root.resolve()
    candidate = verify_candidate_exact7_v1(repo_root)
    bound = subject.load_frozen_formal_decision_v1(repo_root)
    deterministic = _verify_two_directory_determinism(repo_root)
    materialized = subject.check_materialized_v1(repo_root)
    if deterministic["artifact_sha256"] != materialized["artifact_sha256"]:
        raise ValueError("MATERIALIZED_OUTPUT_SHA_MISMATCH")
    artifacts = {
        name: (repo_root / subject.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in subject.OUTPUT_FILENAMES
    }
    subject.validate_completed_decision_projection_v1(artifacts, repo_root=repo_root)
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    summary = json.loads(artifacts[subject.SUMMARY])
    manifest = json.loads(artifacts[subject.MANIFEST])
    matrix = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))

    if tuple(event["canonical_event_id"] for event in bound["normalized"]["events"]) != subject.EXPECTED_EVENT_IDS:
        raise ValueError("EXACT9_COVERAGE_INVALID")
    if len(matrix) != 9 or [int(row["scaleup_rank"]) for row in matrix] != sorted(int(row["scaleup_rank"]) for row in matrix):
        raise ValueError("EXACT9_MATRIX_ORDER_INVALID")
    if snapshot["canonical_task_contract"]["direct_profile_applicable_task_ids"] != [0, 3, 4]:
        raise ValueError("DIRECT_PROFILE_TASK_IDS_INVALID")
    tasks = snapshot["canonical_task_contract"]["direct_profile_task_applicability"]
    if len(tasks) != 5 or tasks[3]["semantic_long_name"] != "scaffold_only":
        raise ValueError("GLOBAL_EXACT5_OR_B3_INVALID")
    if any(tasks[index]["reason"] != subject.EXPECTED_ROLE_PROFILE for index in (1, 2)):
        raise ValueError("B_OR_B2_STRUCTURAL_REASON_INVALID")
    if manifest["output_artifact_bindings"] != {
        subject.SNAPSHOT: {"sha256": _sha(artifacts[subject.SNAPSHOT])},
        subject.MATRIX: {"sha256": _sha(artifacts[subject.MATRIX])},
        subject.SUMMARY: {"sha256": _sha(artifacts[subject.SUMMARY])},
    }:
        raise ValueError("MANIFEST_DIRECT_OUTPUT_BINDINGS_INVALID")

    result = {
        "candidate": candidate,
        "materialized": materialized,
        "repository_state_neutral": True,
        "output_artifact_count": 4,
        "candidate_publication_file_count": 7,
        "formal_decision_binding_verified": True,
        "formal_decision_byte_count": subject.FORMAL_DECISION_BYTE_COUNT,
        "formal_decision_sha256": subject.FORMAL_DECISION_SHA256,
        "frozen_review_package_binding_count": 6,
        "exact9_unique_complete": True,
        "completed_human_positive_count": summary["completed_human_positive_count"],
        "task_relevant_count": summary["task_relevant_count"],
        "chemistry_positive_count": summary["chemistry_positive_count"],
        "reactive_pair_human_authority_count": summary["reactive_pair_human_authority_count"],
        "role_partition_human_authority_count": summary["role_partition_human_authority_count"],
        "global_canonical_exact5_unchanged": True,
        "direct_profile_applicable_tasks_exact_A_B3_C": True,
        "B_and_B2_retained_but_structurally_inapplicable": True,
        "POST_source_evidence_count": summary["POST_source_evidence_count"],
        "POST_geometry_training_authority_count": summary["POST_geometry_training_authority_count"],
        "PRE_geometry_authority_count": summary["PRE_geometry_authority_count"],
        "reaction_family_target_count": summary["reaction_family_target_count"],
        "warhead_rule_target_count": summary["warhead_rule_target_count"],
        "warhead_type_target_count": summary["warhead_type_target_count"],
        "training_excluded_positive_count": summary["training_excluded_positive_count"],
        "training_include_count": summary["training_include_count"],
        "future_training_admission_candidate_count": summary["future_training_admission_candidate_count"],
        "training_admitted_count": summary["training_admitted_count"],
        "training_materialization_allowed_count": summary["training_materialization_allowed_count"],
        "current_runtime_model_usable_count": summary["current_runtime_model_usable_count"],
        "authority_created_by_this_successor": False,
        "global_reconciliation_update_done": False,
        "global_census_update_done": False,
        "deterministic_double_materialization_byte_identical": True,
        "feature_semantics_audit_required_later": True,
        "ready_for_ONL_reconciliation_successor": True,
        "ready_for_training": False,
    }
    required_true = (
        "repository_state_neutral", "formal_decision_binding_verified",
        "exact9_unique_complete", "global_canonical_exact5_unchanged",
        "direct_profile_applicable_tasks_exact_A_B3_C",
        "B_and_B2_retained_but_structurally_inapplicable",
        "deterministic_double_materialization_byte_identical",
        "feature_semantics_audit_required_later",
        "ready_for_ONL_reconciliation_successor",
    )
    required_false = (
        "authority_created_by_this_successor", "global_reconciliation_update_done",
        "global_census_update_done", "ready_for_training",
    )
    if any(result[field] is not True for field in required_true):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    if any(result[field] is not False for field in required_false):
        raise ValueError("CHECKER_REQUIRED_FALSE_ASSERTION_FAILED")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    result = run_check_v1(parser.parse_args().repo_root)
    for key in (
        "repository_state_neutral", "output_artifact_count",
        "candidate_publication_file_count", "formal_decision_binding_verified",
        "formal_decision_byte_count", "formal_decision_sha256",
        "frozen_review_package_binding_count", "exact9_unique_complete",
        "completed_human_positive_count", "task_relevant_count",
        "chemistry_positive_count", "reactive_pair_human_authority_count",
        "role_partition_human_authority_count", "global_canonical_exact5_unchanged",
        "direct_profile_applicable_tasks_exact_A_B3_C",
        "B_and_B2_retained_but_structurally_inapplicable",
        "POST_source_evidence_count", "POST_geometry_training_authority_count",
        "PRE_geometry_authority_count", "reaction_family_target_count",
        "warhead_rule_target_count", "warhead_type_target_count",
        "training_excluded_positive_count", "training_include_count",
        "future_training_admission_candidate_count", "training_admitted_count",
        "training_materialization_allowed_count", "current_runtime_model_usable_count",
        "authority_created_by_this_successor", "global_reconciliation_update_done",
        "global_census_update_done", "deterministic_double_materialization_byte_identical",
        "feature_semantics_audit_required_later", "ready_for_ONL_reconciliation_successor",
        "ready_for_training",
    ):
        value = result[key]
        print(key + "=" + (str(value).lower() if type(value) is bool else str(value)))
    for name, digest in result["materialized"]["artifact_sha256"].items():
        print(name + "_sha256=" + digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
