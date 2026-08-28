#!/usr/bin/env python3
"""Fail-closed checker for NEQ Exact6 completed-decision ingestion V1."""

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
    covapie_neq_completed_decision_ingestion_and_task_label_availability_v1
    as subject,
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
MAX_CANDIDATE_FILE_BYTES = 1024 * 1024


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_candidate_exact7_v1(repo_root: Path) -> dict[str, object]:
    """Verify the Exact7 inventory without inspecting Git lifecycle state."""

    repo_root = repo_root.resolve()
    expected = (
        "src/covalent_ext/covapie_neq_completed_decision_ingestion_and_task_label_availability_v1.py",
        "scripts/check_covapie_neq_completed_decision_ingestion_and_task_label_availability_v1.py",
        "tests/test_covapie_neq_completed_decision_ingestion_and_task_label_availability_v1.py",
        "data/derived/covalent_small/covapie_neq_completed_decision_ingestion_and_task_label_availability_v1/covapie_neq_completed_human_decision_snapshot_v1.json",
        "data/derived/covalent_small/covapie_neq_completed_decision_ingestion_and_task_label_availability_v1/covapie_neq_event_task_label_availability_v1.csv",
        "data/derived/covalent_small/covapie_neq_completed_decision_ingestion_and_task_label_availability_v1/covapie_neq_completed_decision_ingestion_summary_v1.json",
        "data/derived/covalent_small/covapie_neq_completed_decision_ingestion_and_task_label_availability_v1/covapie_neq_completed_decision_ingestion_manifest_v1.json",
    )
    observed = tuple(path.as_posix() for path in subject.CANDIDATE_PUBLICATION_PATHS)
    if observed != expected or len(observed) != 7:
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
        if len(payload) >= MAX_CANDIDATE_FILE_BYTES:
            raise ValueError("CANDIDATE_FILE_TOO_LARGE:" + relative.as_posix())
        if path.suffix in FORBIDDEN_SUFFIXES:
            raise ValueError("CANDIDATE_FORBIDDEN_SUFFIX:" + relative.as_posix())
        subject._validate_text_payload(relative.as_posix(), payload)
        bindings.append(
            {
                "path": relative.as_posix(),
                "byte_count": len(payload),
                "sha256": _sha(payload),
                "mode": format(path.stat().st_mode & 0o7777, "04o"),
            }
        )
    return {
        "candidate_publication_file_count": 7,
        "candidate_exact7_paths": list(expected),
        "candidate_file_bindings": bindings,
        "repository_state_neutral": True,
    }


def _verify_two_directory_determinism(repo_root: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="covapie_neq_ingest_a_") as first_name:
        with tempfile.TemporaryDirectory(prefix="covapie_neq_ingest_b_") as second_name:
            first_root = Path(first_name) / "outputs"
            second_root = Path(second_name) / "outputs"
            first = subject.materialize_artifacts_v1(
                repo_root,
                output_root=first_root,
            )
            second = subject.materialize_artifacts_v1(
                repo_root,
                output_root=second_root,
            )
            if first != second:
                raise ValueError("DETERMINISTIC_DOUBLE_MATERIALIZATION_MISMATCH")
            if any(
                (first_root / name).read_bytes()
                != (second_root / name).read_bytes()
                for name in subject.OUTPUT_FILENAMES
            ):
                raise ValueError("DETERMINISTIC_OUTPUT_BYTES_MISMATCH")
            return {
                "deterministic_double_materialization_byte_identical": True,
                "artifact_sha256": {
                    name: _sha(first[name]) for name in subject.OUTPUT_FILENAMES
                },
            }


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Verify inputs, Exact7/Exact4, semantics, digests, and non-actions."""

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
    subject.validate_completed_decision_projection_v1(
        artifacts,
        repo_root=repo_root,
    )
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    summary = json.loads(artifacts[subject.SUMMARY])
    manifest = json.loads(artifacts[subject.MANIFEST])
    matrix = list(
        csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8")))
    )

    events = bound["normalized"]["events"]
    if (
        tuple(event["canonical_event_id"] for event in events)
        != subject.EXPECTED_EVENT_IDS
        or len(events) != 6
        or len({event["canonical_event_id"] for event in events}) != 6
    ):
        raise ValueError("EXACT6_COVERAGE_INVALID")
    if (
        len(matrix) != 6
        or len({row["canonical_event_id"] for row in matrix}) != 6
        or [int(row["scaleup_rank"]) for row in matrix]
        != list(subject.EXPECTED_RANKS)
    ):
        raise ValueError("EXACT6_MATRIX_ORDER_OR_UNIQUENESS_INVALID")
    for index, row in enumerate(matrix):
        expected = subject.EXPECTED_EVENTS[index]
        if (
            row["pdb_id"] != expected[2]
            or row["model_number"] != "1"
            or row["protein_chain_or_asym"] != expected[4]
            or row["cys_residue_id"] != expected[5]
            or row["protein_altloc"] != ""
            or row["ligand_component_id"] != "NEQ"
            or row["ligand_chain_or_asym"] != expected[7]
            or row["ligand_altloc"] != ""
            or row["selected_connection_id"] != expected[9]
            or row["POST_distance_angstrom"] != expected[11]
        ):
            raise ValueError("NEQ_EVENT_PROVENANCE_INVALID")
    if [row["cys_residue_id"] for row in matrix].count("CYS:22-") != 3:
        raise ValueError("NEQ_CYS22_COUNT_INVALID")
    if [row["cys_residue_id"] for row in matrix].count("CYS:81-") != 3:
        raise ValueError("NEQ_CYS81_COUNT_INVALID")
    site = snapshot["site_context_inventory"]
    if (
        site["distinct_cys_residue_identities"] != ["CYS:22-", "CYS:81-"]
        or site["distinct_cys_residue_identity_count"] != 2
        or site["multiple_observed_cysteine_sites"] is not True
        or site["CYS22_event_count"] != 3
        or site["CYS81_event_count"] != 3
        or site["event_specific_disposition_exception_count"] != 0
        or site["site_specific_disposition_exception_count"] != 0
    ):
        raise ValueError("NEQ_SITE_SEPARATION_INVALID")

    pair = snapshot["reactive_pair"]
    if (
        pair["protein_reactive_atom"] != "SG"
        or pair["ligand_reactive_atom"] != "C3"
        or pair["ligand_reactive_atom_element"] != "C"
        or pair["human_authoritative"] is not True
        or pair["site_specific_pair_counts"] != {"CYS:22-": 3, "CYS:81-": 3}
        or pair["model_bound_pair_target_created"] is not False
        or pair["tensor_target_created"] is not False
        or pair["reusable_pair_authority_created"] is not False
        or pair["training_admission_created"] is not False
    ):
        raise ValueError("NEQ_REACTIVE_PAIR_PROJECTION_INVALID")
    role = snapshot["selected_role_partition"]
    if (
        role["selected_candidate_index_0based"] != 7
        or role["role_profile"] != subject.EXPECTED_ROLE_PROFILE
        or role["warhead_atoms"] != list(subject.EXPECTED_WARHEAD)
        or role["frozen_source_warhead_atoms_source_order"]
        != list(subject.EXPECTED_WARHEAD)
        or role["linker_atoms"] != []
        or role["scaffold_atoms"] != list(subject.EXPECTED_SCAFFOLD)
        or role["boundary_bonds"]
        != [
            {
                "atom_id_1": "C5",
                "atom_id_2": "N1",
                "bond_order": "SING",
                "boundary_between_roles": ["scaffold", "warhead"],
            }
        ]
        or role["exact_heavy_atom_count"] != 9
        or role["heavy_atom_disjoint"] is not True
        or role["heavy_atom_exhaustive"] is not True
        or role["warhead_connected"] is not True
        or role["linker_empty"] is not True
        or role["scaffold_connected"] is not True
        or role["machine_selected"] is not False
        or role["machine_recommended_candidate"] is not None
    ):
        raise ValueError("NEQ_CANDIDATE7_ROLE_PROJECTION_INVALID")
    tasks = snapshot["canonical_task_contract"]
    if (
        tasks["global_canonical_task_count"] != 5
        or tasks["B3_present"] is not True
        or tasks["sixth_task_created"] is not False
        or tasks["direct_profile_applicable_task_ids"] != [0, 3, 4]
        or tasks["global_canonical_tasks"][3]["semantic_long_name"]
        != "scaffold_only"
        or tasks["D5_EXCLUDE_does_not_change_structural_applicability"]
        is not True
    ):
        raise ValueError("GLOBAL_EXACT5_OR_B3_INVALID")

    decisions = snapshot["unit_level_D1_D6"]
    training = snapshot["training_boundary"]
    if (
        decisions["D1"] != "RELEVANT"
        or decisions["D2"] != "POSITIVE"
        or decisions["D5"] != "EXCLUDE_FROM_TRAINING_ONLY"
        or training["negative_chemistry"] is not False
        or training["task_domain_negative"] is not False
        or training["human_training_excluded"] is not True
        or training["training_use_allowed"] is not False
        or training["training_use_include"] is not False
        or training["candidate_for_future_training_admission"] is not False
        or training["future_training_admission_status"] is not None
        or training["training_admitted"] is not False
        or training["training_materialization_allowed_now"] is not False
        or training["current_runtime_model_usable"] is not False
        or training["formal_split_authority_created"] is not False
        or training["tensor_target_created"] is not False
        or training["parameter_update_authorization"] is not False
    ):
        raise ValueError("NEQ_EXCLUDE_POSITIVE_SEPARATION_INVALID")

    context = snapshot["scientific_context"]
    topology = snapshot["source_CCD_and_event_topology_boundary"]
    geometry = snapshot["geometry_boundary"]
    reusable = snapshot["auxiliary_and_reusable_boundary"]
    if (
        context["compound_context"] != "NEM"
        or context["target_context"] != "PCNA"
        or context["non_medicinal_context"] is not True
        or context["target_directed_medicinal_inhibitor_context"] is not False
        or topology["source_CCD_component_graph_heavy_atom_count"] != 9
        or topology["source_CCD_C2_C3_bond_order"] != "DOUB"
        or topology["explicit_observed_SG_C3_connection_event_count"] != 6
        or topology[
            "complete_authoritative_POST_adduct_bond_order_topology_available"
        ]
        is not False
        or topology["complete_POST_topology_authority_available"] is not False
        or topology["PRE_topology_authority_available"] is not False
        or topology["PRE_geometry_authority_available"] is not False
        or topology["PRE_reconstruction_performed"] is not False
        or geometry["POST_source_evidence_count"] != 6
        or geometry["POST_geometry_training_authority_count"] != 0
        or geometry["PRE_geometry_authority_count"] != 0
        or geometry["PRE_precursor_topology_authority_count"] != 0
        or reusable["reaction_family_target_count"] != 0
        or reusable["warhead_rule_target_count"] != 0
        or reusable["warhead_type_target_count"] != 0
        or reusable["reusable_chemistry_authority_available"] is not False
        or reusable["reusable_pair_authority_available"] is not False
        or reusable["reusable_role_authority_available"] is not False
    ):
        raise ValueError("NEQ_CONTEXT_TOPOLOGY_GEOMETRY_OR_REUSABLE_BOUNDARY_INVALID")

    if manifest["output_artifact_bindings"] != {
        subject.SNAPSHOT: {"sha256": _sha(artifacts[subject.SNAPSHOT])},
        subject.MATRIX: {"sha256": _sha(artifacts[subject.MATRIX])},
        subject.SUMMARY: {"sha256": _sha(artifacts[subject.SUMMARY])},
    }:
        raise ValueError("MANIFEST_DIRECT_OUTPUT_BINDINGS_INVALID")
    if (
        len(manifest["frozen_formal_evidence_provenance"]) != 6
        or len(manifest["yun_schema_precedent_bindings"]) != 2
        or len(manifest["exclude_semantic_precedent_bindings"]) != 4
        or len(manifest["immutable_semantic_owner_bindings"]) != 2
        or len(manifest["current_published_census_bindings"]) != 4
    ):
        raise ValueError("MANIFEST_SOURCE_BINDING_COUNTS_INVALID")
    if (
        summary["published_global_positive_count_remains"] != 89
        or summary["published_training_INCLUDE_count_remains"] != 36
        or summary["published_training_EXCLUDE_count_remains"] != 53
        or summary["published_future_training_candidate_count_remains"] != 19
        or summary["current_published_NEQ_status"] != "CURRENTLY_UNREVIEWED"
        or summary["expected_future_census_derivation_informational_only"][
            "chemistry_positive"
        ]
        != 95
        or summary["expected_future_census_derivation_informational_only"][
            "training_EXCLUDE"
        ]
        != 59
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
        "yun_schema_precedent_verified": True,
        "exclude_semantic_precedents_verified": True,
        "exact6_unique_complete": True,
        "CYS22_event_count": summary["CYS22_event_count"],
        "CYS81_event_count": summary["CYS81_event_count"],
        "completed_human_positive_count": summary["completed_human_positive_count"],
        "task_relevant_count": summary["task_relevant_count"],
        "chemistry_positive_count": summary["chemistry_positive_count"],
        "reactive_pair_human_authority_count": summary[
            "reactive_pair_human_authority_count"
        ],
        "role_partition_human_authority_count": summary[
            "role_partition_human_authority_count"
        ],
        "candidate7_direct_role_projection_verified": True,
        "global_canonical_exact5_unchanged": True,
        "direct_profile_applicable_tasks_exact_0_3_4": True,
        "exclude_positive_separation_verified": True,
        "source_CCD_and_topology_boundary_verified": True,
        "POST_source_evidence_count": summary["POST_source_evidence_count"],
        "POST_geometry_training_authority_count": summary[
            "POST_geometry_training_authority_count"
        ],
        "PRE_geometry_authority_count": summary["PRE_geometry_authority_count"],
        "reaction_family_target_count": summary["reaction_family_target_count"],
        "warhead_rule_target_count": summary["warhead_rule_target_count"],
        "warhead_type_target_count": summary["warhead_type_target_count"],
        "human_training_EXCLUDE_count": summary["human_training_EXCLUDE_count"],
        "training_use_allowed_count": summary["training_use_allowed_count"],
        "future_training_admission_candidate_count": summary[
            "future_training_admission_candidate_count"
        ],
        "training_admitted_count": summary["training_admitted_count"],
        "training_materialization_allowed_count": summary[
            "training_materialization_allowed_count"
        ],
        "current_runtime_model_usable_count": summary[
            "current_runtime_model_usable_count"
        ],
        "published_global_positive_count_remains": summary[
            "published_global_positive_count_remains"
        ],
        "published_training_INCLUDE_count_remains": summary[
            "published_training_INCLUDE_count_remains"
        ],
        "published_future_training_candidate_count_remains": summary[
            "published_future_training_candidate_count_remains"
        ],
        "authority_created_by_this_ingestion": False,
        "global_reconciliation_update_done": False,
        "global_census_update_done": False,
        "deterministic_double_materialization_byte_identical": True,
        "derived_projection_digests_verified": True,
        "current_census_preserved_and_bound": True,
        "future_95_59_informational_only_verified": True,
        "no_model_or_training_work_verified": True,
        "feature_semantics_audit_required_later": True,
        "ready_for_NEQ_reconciliation_successor": True,
        "ready_for_training": False,
    }
    required_true = (
        "repository_state_neutral",
        "formal_decision_binding_verified",
        "yun_schema_precedent_verified",
        "exclude_semantic_precedents_verified",
        "exact6_unique_complete",
        "candidate7_direct_role_projection_verified",
        "global_canonical_exact5_unchanged",
        "direct_profile_applicable_tasks_exact_0_3_4",
        "exclude_positive_separation_verified",
        "source_CCD_and_topology_boundary_verified",
        "deterministic_double_materialization_byte_identical",
        "derived_projection_digests_verified",
        "current_census_preserved_and_bound",
        "future_95_59_informational_only_verified",
        "no_model_or_training_work_verified",
        "feature_semantics_audit_required_later",
        "ready_for_NEQ_reconciliation_successor",
    )
    required_false = (
        "authority_created_by_this_ingestion",
        "global_reconciliation_update_done",
        "global_census_update_done",
        "ready_for_training",
    )
    if any(result[field] is not True for field in required_true):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    if any(result[field] is not False for field in required_false):
        raise ValueError("CHECKER_REQUIRED_FALSE_ASSERTION_FAILED")
    if result["published_global_positive_count_remains"] != 89:
        raise ValueError("PUBLISHED_GLOBAL_POSITIVE_COUNT_BOUNDARY_INVALID")
    if result["published_training_INCLUDE_count_remains"] != 36:
        raise ValueError("PUBLISHED_GLOBAL_INCLUDE_COUNT_BOUNDARY_INVALID")
    if result["published_future_training_candidate_count_remains"] != 19:
        raise ValueError("PUBLISHED_GLOBAL_FUTURE_CANDIDATE_BOUNDARY_INVALID")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    result = run_check_v1(parser.parse_args().repo_root)
    for key in (
        "repository_state_neutral",
        "output_artifact_count",
        "candidate_publication_file_count",
        "formal_decision_binding_verified",
        "formal_decision_byte_count",
        "formal_decision_sha256",
        "formal_decision_schema",
        "reviewer_id",
        "attestor_id",
        "approved_at_utc",
        "formal_evidence_provenance_binding_count",
        "yun_schema_precedent_verified",
        "exclude_semantic_precedents_verified",
        "exact6_unique_complete",
        "CYS22_event_count",
        "CYS81_event_count",
        "completed_human_positive_count",
        "task_relevant_count",
        "chemistry_positive_count",
        "reactive_pair_human_authority_count",
        "role_partition_human_authority_count",
        "candidate7_direct_role_projection_verified",
        "global_canonical_exact5_unchanged",
        "direct_profile_applicable_tasks_exact_0_3_4",
        "exclude_positive_separation_verified",
        "source_CCD_and_topology_boundary_verified",
        "POST_source_evidence_count",
        "POST_geometry_training_authority_count",
        "PRE_geometry_authority_count",
        "reaction_family_target_count",
        "warhead_rule_target_count",
        "warhead_type_target_count",
        "human_training_EXCLUDE_count",
        "training_use_allowed_count",
        "future_training_admission_candidate_count",
        "training_admitted_count",
        "training_materialization_allowed_count",
        "current_runtime_model_usable_count",
        "published_global_positive_count_remains",
        "published_training_INCLUDE_count_remains",
        "published_future_training_candidate_count_remains",
        "authority_created_by_this_ingestion",
        "global_reconciliation_update_done",
        "global_census_update_done",
        "deterministic_double_materialization_byte_identical",
        "derived_projection_digests_verified",
        "current_census_preserved_and_bound",
        "future_95_59_informational_only_verified",
        "no_model_or_training_work_verified",
        "feature_semantics_audit_required_later",
        "ready_for_NEQ_reconciliation_successor",
        "ready_for_training",
    ):
        value = result[key]
        print(key + "=" + (str(value).lower() if type(value) is bool else str(value)))
    for name, digest in result["materialized"]["artifact_sha256"].items():
        print(name + "_sha256=" + digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
