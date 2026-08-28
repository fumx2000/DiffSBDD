#!/usr/bin/env python3
"""Fail-closed checker for CHT Exact5 completed-decision ingestion V1."""

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
    covapie_cht_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
)


FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".pyc", ".tmp", ".part",
)
MAX_CANDIDATE_FILE_BYTES = 1024 * 1024


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_candidate_exact7_v1(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    expected = (
        "src/covalent_ext/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1.py",
        "scripts/check_covapie_cht_completed_decision_ingestion_and_task_label_availability_v1.py",
        "tests/test_covapie_cht_completed_decision_ingestion_and_task_label_availability_v1.py",
        "data/derived/covalent_small/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1/covapie_cht_completed_human_decision_snapshot_v1.json",
        "data/derived/covalent_small/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1/covapie_cht_event_task_label_availability_v1.csv",
        "data/derived/covalent_small/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1/covapie_cht_completed_decision_ingestion_summary_v1.json",
        "data/derived/covalent_small/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1/covapie_cht_completed_decision_ingestion_manifest_v1.json",
    )
    observed = tuple(path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS)
    if observed != expected or len(observed) != 7:
        raise ValueError("CANDIDATE_PUBLICATION_EXACT7_CONTRACT_INVALID")
    output_root = repo_root / subject.OUTPUT_ROOT_RELATIVE
    if not output_root.is_dir() or output_root.is_symlink():
        raise ValueError("OUTPUT_DIRECTORY_MISSING_OR_INVALID")
    if {path.name for path in output_root.iterdir()} != set(subject.OUTPUT_FILENAMES):
        raise ValueError("OUTPUT_DIRECTORY_EXACT4_INVALID")
    bindings = []
    for relative in subject.CANDIDATE_PUBLICATION_PATHS:
        path = repo_root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError("CANDIDATE_FILE_NOT_REGULAR:" + relative.as_posix())
        payload = path.read_bytes()
        if len(payload) >= MAX_CANDIDATE_FILE_BYTES:
            raise ValueError("CANDIDATE_FILE_TOO_LARGE:" + relative.as_posix())
        if path.suffix in FORBIDDEN_SUFFIXES:
            raise ValueError("CANDIDATE_FORBIDDEN_SUFFIX:" + relative.as_posix())
        subject._validate_text_payload(relative.as_posix(), payload)
        bindings.append({
            "path": relative.as_posix(),
            "byte_count": len(payload),
            "sha256": _sha(payload),
            "mode": format(path.stat().st_mode & 0o7777, "04o"),
        })
    return {
        "candidate_publication_file_count": 7,
        "candidate_exact7_paths": list(expected),
        "candidate_file_bindings": bindings,
        "repository_state_neutral": True,
    }


def _verify_two_directory_determinism(repo_root: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="covapie_cht_ingest_a_") as first_name:
        with tempfile.TemporaryDirectory(prefix="covapie_cht_ingest_b_") as second_name:
            first_root = Path(first_name) / "outputs"
            second_root = Path(second_name) / "outputs"
            first = subject.materialize_artifacts_v1(repo_root, output_root=first_root)
            second = subject.materialize_artifacts_v1(repo_root, output_root=second_root)
            if first != second or any(
                (first_root / name).read_bytes() != (second_root / name).read_bytes()
                for name in subject.OUTPUT_FILENAMES
            ):
                raise ValueError("DETERMINISTIC_DOUBLE_MATERIALIZATION_MISMATCH")
            return {
                "deterministic_double_materialization_byte_identical": True,
                "artifact_sha256": {name: _sha(first[name]) for name in subject.OUTPUT_FILENAMES},
            }


def run_check_v1(repo_root: Path) -> dict[str, object]:
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

    binding = bound["formal_decision_binding"]
    if (
        binding["byte_count"] != 33307
        or binding["sha256"] != "0f8b48d08a116aa6fa2b30a67d89a51ae2b730f68514b0ce2e0985189dd1ea2b"
        or binding["schema_version"] != "covapie_cht_exact5_formal_human_decision_v1"
        or binding["reviewer_id"] != "fmx"
        or binding["attestor_id"] != "fmx"
        or binding["approved_at_utc"] != "2026-08-28T08:07:26Z"
    ):
        raise ValueError("FORMAL_CHT_BINDING_INVALID")
    if (
        len(bound["frozen_review_package_bindings"]) != 6
        or [row["mode"] for row in bound["frozen_review_package_bindings"]]
        != ["0644", "0644", "0644", "0644", "0644", "0755"]
        or len(bound["architecture_precedent_bindings"]) != 2
        or len(bound["exclude_semantic_precedent_bindings"]) != 4
        or len(bound["immutable_semantic_owner_bindings"]) != 2
        or len(bound["current_published_census_bindings"]) != 4
    ):
        raise ValueError("FROZEN_PROVENANCE_OR_PRECEDENT_BINDING_INVALID")

    events = bound["normalized"]["events"]
    if (
        len(events) != 5
        or len({event["canonical_event_id"] for event in events}) != 5
        or tuple(event["canonical_event_id"] for event in events) != subject.EXPECTED_EVENT_IDS
        or [event["scaleup_rank"] for event in events] != list(subject.EXPECTED_RANKS)
    ):
        raise ValueError("EXACT5_COVERAGE_INVALID")
    if len(matrix) != 5 or [int(row["scaleup_rank"]) for row in matrix] != list(subject.EXPECTED_RANKS):
        raise ValueError("EXACT5_MATRIX_ORDER_INVALID")
    for index, row in enumerate(matrix):
        expected = subject.EXPECTED_EVENTS[index]
        expected_altloc = "" if expected[6] is None else expected[6]
        if (
            row["canonical_event_id"] != expected[0]
            or row["pdb_id"] != expected[2]
            or row["model_number"] != "1"
            or row["protein_chain_or_asym"] != expected[4]
            or row["cys_residue_id"] != "CYS:450-"
            or row["protein_altloc"] != expected_altloc
            or row["ligand_component_id"] != "CHT"
            or row["ligand_chain_or_asym"] != expected[7]
            or row["ligand_altloc"] != ""
            or row["selected_connection_id"] != expected[9]
            or row["POST_distance_angstrom"] != expected[11]
            or row["human_task_relevance_decision"] != "RELEVANT"
            or row["chemistry_known_positive"] != "true"
            or row["negative_chemistry"] != "false"
            or row["task_domain_negative"] != "false"
            or row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "C4"
            or row["ligand_reactive_atom_element"] != "C"
            or row["selected_role_candidate_index_0based"] != "2"
            or row["role_profile"] != "STRICT_LINKER_PRESENT_V1"
            or row["strict_profile_applicable_task_ids_json"] != "[0,1,2,3,4]"
            or row["formal_event_training_use_decision"] != "EXCLUDE_FROM_TRAINING_ONLY"
            or row["human_training_excluded"] != "true"
            or row["training_use_allowed"] != "false"
            or row["candidate_for_future_training_admission"] != "false"
            or row["future_training_admission_status"] != ""
            or row["training_admitted"] != "false"
            or row["current_runtime_model_usable"] != "false"
        ):
            raise ValueError("CHT_EVENT_OR_EXCLUDE_PROJECTION_INVALID")

    role = snapshot["selected_role_partition"]
    tasks = snapshot["canonical_task_contract"]
    topology = snapshot["source_CCD_and_event_topology_boundary"]
    geometry = snapshot["geometry_boundary"]
    reusable = snapshot["auxiliary_and_reusable_boundary"]
    training = snapshot["training_boundary"]
    if (
        role["selected_candidate_index_0based"] != 2
        or role["role_profile"] != "STRICT_LINKER_PRESENT_V1"
        or role["warhead_atoms"] != ["C4", "O6"]
        or role["linker_atoms"] != ["C5"]
        or role["scaffold_atoms"] != ["C6", "C7", "C8", "N1"]
        or role["heavy_atom_disjoint"] is not True
        or role["heavy_atom_exhaustive"] is not True
        or role["warhead_connected"] is not True
        or role["linker_connected"] is not True
        or role["scaffold_connected"] is not True
        or role["reactive_C4_in_warhead"] is not True
        or tasks["global_canonical_task_count"] != 5
        or tasks["B3_present"] is not True
        or tasks["sixth_task_created"] is not False
        or tasks["strict_profile_applicable_task_ids"] != [0, 1, 2, 3, 4]
    ):
        raise ValueError("CANDIDATE2_STRICT_EXACT5_INVALID")
    if (
        topology["source_CCD_C4_O6_bond_order"] != "SING"
        or topology["explicit_observed_SG_C4_connection_event_count"] != 5
        or topology["complete_POST_topology_authority_available"] is not False
        or topology["PRE_C4_O6_double_bond_authority_available"] is not False
        or topology["PRE_topology_authority_available"] is not False
        or topology["PRE_geometry_authority_available"] is not False
        or geometry["POST_source_evidence_count"] != 5
        or geometry["POST_geometry_training_authority_count"] != 0
        or geometry["PRE_geometry_authority_count"] != 0
        or reusable["reaction_family_target_count"] != 0
        or reusable["warhead_rule_target_count"] != 0
        or reusable["warhead_type_target_count"] != 0
        or reusable["new_reusable_authority_created"] is not False
        or training["formal_event_training_use_decision"] != "EXCLUDE_FROM_TRAINING_ONLY"
        or training["human_training_excluded"] is not True
        or training["training_use_allowed"] is not False
        or training["candidate_for_future_training_admission"] is not False
        or training["training_admitted"] is not False
        or training["current_runtime_model_usable"] is not False
    ):
        raise ValueError("TOPOLOGY_GEOMETRY_REUSABLE_OR_TRAINING_BOUNDARY_INVALID")

    if manifest["output_artifact_bindings"] != {
        subject.SNAPSHOT: {"sha256": _sha(artifacts[subject.SNAPSHOT])},
        subject.MATRIX: {"sha256": _sha(artifacts[subject.MATRIX])},
        subject.SUMMARY: {"sha256": _sha(artifacts[subject.SUMMARY])},
    } or manifest["manifest_self_sha256_recorded"] is not False:
        raise ValueError("MANIFEST_OUTPUT_BINDINGS_INVALID")
    if (
        _sha(artifacts[subject.SNAPSHOT]) != subject._EXPECTED_SNAPSHOT_SHA256_V1
        or _sha(artifacts[subject.MATRIX]) != subject._EXPECTED_MATRIX_SHA256_V1
        or _sha(artifacts[subject.SUMMARY]) != subject._EXPECTED_SUMMARY_SHA256_V1
    ):
        raise ValueError("DERIVED_PROJECTION_DIGEST_INVALID")
    future = summary["expected_future_census_derivation_informational_only"]
    if (
        summary["event_count"] != 5
        or summary["task_relevant_count"] != 5
        or summary["chemistry_positive_count"] != 5
        or summary["human_training_EXCLUDE_count"] != 5
        or summary["published_global_positive_count_remains"] != 95
        or summary["published_task_relevant_count_remains"] != 96
        or summary["published_training_INCLUDE_count_remains"] != 36
        or summary["published_training_EXCLUDE_count_remains"] != 59
        or summary["published_future_training_candidate_count_remains"] != 19
        or summary["current_published_CHT_status"] != "CURRENTLY_UNREVIEWED"
        or future["chemistry_positive"] != 100
        or future["task_relevant"] != 101
        or future["training_EXCLUDE"] != 64
        or future["STRICT"] != 44
        or future["DIRECT"] != 56
    ):
        raise ValueError("CURRENT_OR_INFORMATIONAL_FUTURE_CENSUS_BOUNDARY_INVALID")

    result = {
        "candidate": candidate,
        "materialized": materialized,
        "repository_state_neutral": True,
        "output_artifact_count": 4,
        "candidate_publication_file_count": 7,
        "formal_decision_binding_verified": True,
        "formal_decision_byte_count": subject.FORMAL_DECISION_BYTE_COUNT,
        "formal_decision_sha256": subject.FORMAL_DECISION_SHA256,
        "formal_decision_schema": subject.FORMAL_DECISION_SCHEMA,
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": subject.EXPECTED_APPROVED_AT_UTC,
        "formal_evidence_provenance_binding_count": 6,
        "architecture_precedents_verified": True,
        "exclude_semantic_precedents_verified": True,
        "exact5_unique_complete": True,
        "completed_human_positive_count": 5,
        "task_relevant_count": 5,
        "chemistry_positive_count": 5,
        "reactive_pair_human_authority_count": 5,
        "role_partition_human_authority_count": 5,
        "candidate2_strict_role_projection_verified": True,
        "strict_profile_applicable_tasks_exact_0_1_2_3_4": True,
        "exclude_positive_separation_verified": True,
        "source_CCD_and_topology_boundary_verified": True,
        "POST_source_evidence_count": 5,
        "POST_geometry_training_authority_count": 0,
        "PRE_geometry_authority_count": 0,
        "reaction_family_target_count": 0,
        "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
        "human_training_EXCLUDE_count": 5,
        "training_use_allowed_count": 0,
        "future_training_admission_candidate_count": 0,
        "training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "published_global_positive_count_remains": 95,
        "published_task_relevant_count_remains": 96,
        "published_training_INCLUDE_count_remains": 36,
        "published_training_EXCLUDE_count_remains": 59,
        "published_future_training_candidate_count_remains": 19,
        "authority_created_by_this_ingestion": False,
        "global_reconciliation_update_done": False,
        "global_census_update_done": False,
        "deterministic_double_materialization_byte_identical": True,
        "derived_projection_digests_verified": True,
        "current_census_preserved_and_bound": True,
        "future_100_64_informational_only_verified": True,
        "no_model_or_training_work_verified": True,
        "feature_semantics_audit_required_later": True,
        "ready_for_CHT_reconciliation_successor": True,
        "ready_for_training": False,
    }
    true_fields = (
        "repository_state_neutral", "formal_decision_binding_verified",
        "architecture_precedents_verified", "exclude_semantic_precedents_verified",
        "exact5_unique_complete", "candidate2_strict_role_projection_verified",
        "strict_profile_applicable_tasks_exact_0_1_2_3_4",
        "exclude_positive_separation_verified", "source_CCD_and_topology_boundary_verified",
        "deterministic_double_materialization_byte_identical",
        "derived_projection_digests_verified", "current_census_preserved_and_bound",
        "future_100_64_informational_only_verified", "no_model_or_training_work_verified",
        "feature_semantics_audit_required_later", "ready_for_CHT_reconciliation_successor",
    )
    false_fields = (
        "authority_created_by_this_ingestion", "global_reconciliation_update_done",
        "global_census_update_done", "ready_for_training",
    )
    if any(result[field] is not True for field in true_fields):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    if any(result[field] is not False for field in false_fields):
        raise ValueError("CHECKER_REQUIRED_FALSE_ASSERTION_FAILED")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    result = run_check_v1(parser.parse_args().repo_root)
    keys = (
        "repository_state_neutral", "output_artifact_count",
        "candidate_publication_file_count", "formal_decision_binding_verified",
        "formal_decision_byte_count", "formal_decision_sha256",
        "formal_decision_schema", "reviewer_id", "attestor_id", "approved_at_utc",
        "formal_evidence_provenance_binding_count", "architecture_precedents_verified",
        "exclude_semantic_precedents_verified", "exact5_unique_complete",
        "completed_human_positive_count", "task_relevant_count",
        "chemistry_positive_count", "reactive_pair_human_authority_count",
        "role_partition_human_authority_count", "candidate2_strict_role_projection_verified",
        "strict_profile_applicable_tasks_exact_0_1_2_3_4",
        "exclude_positive_separation_verified", "source_CCD_and_topology_boundary_verified",
        "POST_source_evidence_count", "POST_geometry_training_authority_count",
        "PRE_geometry_authority_count", "reaction_family_target_count",
        "warhead_rule_target_count", "warhead_type_target_count",
        "human_training_EXCLUDE_count", "training_use_allowed_count",
        "future_training_admission_candidate_count", "training_admitted_count",
        "training_materialization_allowed_count", "current_runtime_model_usable_count",
        "published_global_positive_count_remains", "published_task_relevant_count_remains",
        "published_training_INCLUDE_count_remains", "published_training_EXCLUDE_count_remains",
        "published_future_training_candidate_count_remains",
        "authority_created_by_this_ingestion", "global_reconciliation_update_done",
        "global_census_update_done", "deterministic_double_materialization_byte_identical",
        "derived_projection_digests_verified", "current_census_preserved_and_bound",
        "future_100_64_informational_only_verified", "no_model_or_training_work_verified",
        "feature_semantics_audit_required_later", "ready_for_CHT_reconciliation_successor",
        "ready_for_training",
    )
    for key in keys:
        value = result[key]
        print(key + "=" + (str(value).lower() if type(value) is bool else str(value)))
    for name, digest in result["materialized"]["artifact_sha256"].items():
        print(name + "_sha256=" + digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
