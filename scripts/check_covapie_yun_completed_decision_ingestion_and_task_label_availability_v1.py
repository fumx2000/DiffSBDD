#!/usr/bin/env python3
"""Fail-closed checker for YUN Exact7 completed-decision ingestion V1."""

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
    covapie_yun_completed_decision_ingestion_and_task_label_availability_v1
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
    """Verify the Exact7 inventory without inspecting Git lifecycle state."""

    repo_root = repo_root.resolve()
    expected = (
        "src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py",
        "scripts/check_covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py",
        "tests/test_covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py",
        "data/derived/covalent_small/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1/covapie_yun_completed_human_decision_snapshot_v1.json",
        "data/derived/covalent_small/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1/covapie_yun_event_task_label_availability_v1.csv",
        "data/derived/covalent_small/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1/covapie_yun_completed_decision_ingestion_summary_v1.json",
        "data/derived/covalent_small/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1/covapie_yun_completed_decision_ingestion_manifest_v1.json",
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
    with tempfile.TemporaryDirectory(prefix="covapie_yun_ingest_a_") as first_name:
        with tempfile.TemporaryDirectory(prefix="covapie_yun_ingest_b_") as second_name:
            first_root = Path(first_name) / "outputs"
            second_root = Path(second_name) / "outputs"
            first = subject.materialize_artifacts_v1(repo_root, output_root=first_root)
            second = subject.materialize_artifacts_v1(repo_root, output_root=second_root)
            if first != second:
                raise ValueError("DETERMINISTIC_DOUBLE_MATERIALIZATION_MISMATCH")
            if any(
                (first_root / name).read_bytes() != (second_root / name).read_bytes()
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
    subject.validate_completed_decision_projection_v1(artifacts, repo_root=repo_root)
    snapshot = json.loads(artifacts[subject.SNAPSHOT])
    summary = json.loads(artifacts[subject.SUMMARY])
    manifest = json.loads(artifacts[subject.MANIFEST])
    matrix = list(csv.DictReader(io.StringIO(artifacts[subject.MATRIX].decode("utf-8"))))

    if tuple(event["canonical_event_id"] for event in bound["normalized"]["events"]) != subject.EXPECTED_EVENT_IDS:
        raise ValueError("EXACT7_COVERAGE_INVALID")
    if (
        len(matrix) != 7
        or len({row["canonical_event_id"] for row in matrix}) != 7
        or [int(row["scaleup_rank"]) for row in matrix] != list(subject.EXPECTED_RANKS)
    ):
        raise ValueError("EXACT7_MATRIX_ORDER_OR_UNIQUENESS_INVALID")
    for index, row in enumerate(matrix):
        expected = subject.EXPECTED_EVENTS[index]
        if (
            row["pdb_id"] != expected[2]
            or row["model_number"] != "1"
            or row["protein_chain_or_asym"] != expected[4]
            or row["cys_residue_id"] != expected[5]
            or row["protein_altloc"] != ""
            or row["ligand_chain_or_asym"] != expected[7]
            or row["ligand_altloc"] != ""
            or row["selected_connection_id"] != expected[9]
            or row["POST_distance_angstrom"] != expected[11]
        ):
            raise ValueError("YUN_EVENT_PROVENANCE_INVALID")
    pair = snapshot["reactive_pair"]
    if (
        pair["protein_reactive_atom"] != "SG"
        or pair["ligand_reactive_atom"] != "CAN"
        or pair["ligand_reactive_atom_element"] != "C"
        or pair["human_authoritative"] is not True
        or pair["PDB_specific_pairs"] != {
            "4LL0": "CYS797_SG_TO_YUN_CAN", "4LRM": "CYS800_SG_TO_YUN_CAN"
        }
        or pair["model_bound_pair_target_created_by_ingestion"] is not False
        or pair["tensor_target_created"] is not False
        or pair["reusable_reactive_pair_authority"] is not False
    ):
        raise ValueError("YUN_REACTIVE_PAIR_PROJECTION_INVALID")
    role = snapshot["selected_role_partition"]
    if (
        role["selected_candidate_index_0based"] != 4
        or role["role_profile"] != subject.EXPECTED_ROLE_PROFILE
        or role["warhead_atoms"] != list(subject.EXPECTED_WARHEAD)
        or role["frozen_source_warhead_atoms_source_order"] != list(subject.EXPECTED_SOURCE_WARHEAD_ORDER)
        or set(role["warhead_atoms"]) != set(role["frozen_source_warhead_atoms_source_order"])
        or role["linker_atoms"] != []
        or role["scaffold_atoms"] != list(subject.EXPECTED_SCAFFOLD)
        or role["boundary_bonds"] != [{
            "atom_id_1": "CAZ", "atom_id_2": "NAS", "bond_order": "SING",
            "boundary_between_roles": ["scaffold", "warhead"],
        }]
        or role["heavy_atom_disjoint"] is not True
        or role["heavy_atom_exhaustive"] is not True
        or role["linker_empty"] is not True
        or role["machine_selected"] is not False
        or role["machine_recommended_candidate"] is not None
    ):
        raise ValueError("YUN_CANDIDATE4_ROLE_PROJECTION_INVALID")
    tasks = snapshot["canonical_task_contract"]
    if (
        tasks["global_canonical_task_count"] != 5
        or tasks["B3_present"] is not True
        or tasks["sixth_task_created"] is not False
        or tasks["direct_profile_applicable_task_ids"] != [0, 3, 4]
        or tasks["global_canonical_tasks"][3]["semantic_long_name"] != "scaffold_only"
    ):
        raise ValueError("GLOBAL_EXACT5_OR_B3_INVALID")
    context = snapshot["scientific_context"]
    observed = snapshot["observed_graph_PRE_boundary"]
    if (
        context["compound_context"] != "PD168393"
        or context["target_context"] != "EGFR"
        or context["acrylamide_scientific_context"] is not True
        or context["Michael_addition_scientific_context"] is not True
        or context["engineered_cysteine_site"] is not False
        or observed["observed_reactive_atom_element"] != "C"
        or observed["observed_CAO_CAN_bond_order"] != "SING"
        or observed["observed_graph_is_post_covalent_product_state"] is not True
        or observed["authoritative_PRE_precursor_topology"] is not None
        or observed["authoritative_PRE_acrylamide_bond_order_topology"] is not None
        or observed["PRE_CAO_CAN_bond_order_authority"] is not None
        or observed["PRE_CAO_CAN_double_bond_authority_created"] is not False
    ):
        raise ValueError("YUN_SCIENTIFIC_OR_OBSERVED_PRE_BOUNDARY_INVALID")
    training = snapshot["training_boundary"]
    if (
        training["formal_event_training_use_decision"] != "INCLUDE"
        or training["training_use_allowed"] is not True
        or training["candidate_for_future_training_admission"] is not True
        or training["future_training_admission_status"] != subject.FUTURE_STATUS
        or training["future_training_candidate_derived_by_ingestion"] is not True
        or training["future_training_candidate_is_training_admission"] is not False
        or training["training_admitted"] is not False
        or training["training_materialization_allowed_now"] is not False
        or training["current_runtime_model_usable"] is not False
    ):
        raise ValueError("YUN_INCLUDE_ADMISSION_SEPARATION_INVALID")
    if manifest["output_artifact_bindings"] != {
        subject.SNAPSHOT: {"sha256": _sha(artifacts[subject.SNAPSHOT])},
        subject.MATRIX: {"sha256": _sha(artifacts[subject.MATRIX])},
        subject.SUMMARY: {"sha256": _sha(artifacts[subject.SUMMARY])},
    }:
        raise ValueError("MANIFEST_DIRECT_OUTPUT_BINDINGS_INVALID")
    if (
        len(manifest["frozen_formal_evidence_provenance"]) != 6
        or len(manifest["include_semantic_precedent_bindings"]) != 4
        or len(manifest["immutable_semantic_owner_bindings"]) != 2
        or len(manifest["current_published_census_bindings"]) != 4
    ):
        raise ValueError("MANIFEST_SOURCE_BINDING_COUNTS_INVALID")

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
        "include_semantic_precedent_verified": True,
        "exact7_unique_complete": True,
        "completed_human_positive_count": summary["completed_human_positive_count"],
        "task_relevant_count": summary["task_relevant_count"],
        "chemistry_positive_count": summary["chemistry_positive_count"],
        "reactive_pair_human_authority_count": summary["reactive_pair_human_authority_count"],
        "role_partition_human_authority_count": summary["role_partition_human_authority_count"],
        "candidate4_direct_role_projection_verified": True,
        "global_canonical_exact5_unchanged": True,
        "direct_profile_applicable_tasks_exact_0_3_4": True,
        "scientific_context_projection_verified": True,
        "observed_product_PRE_boundary_verified": True,
        "POST_source_evidence_count": summary["POST_source_evidence_count"],
        "POST_geometry_training_authority_count": summary["POST_geometry_training_authority_count"],
        "PRE_geometry_authority_count": summary["PRE_geometry_authority_count"],
        "reaction_family_target_count": summary["reaction_family_target_count"],
        "warhead_rule_target_count": summary["warhead_rule_target_count"],
        "warhead_type_target_count": summary["warhead_type_target_count"],
        "training_include_count": summary["human_training_INCLUDE_count"],
        "training_use_allowed_count": summary["training_use_allowed_count"],
        "future_training_admission_candidate_count": summary["future_training_admission_candidate_count"],
        "training_admitted_count": summary["training_admitted_count"],
        "training_materialization_allowed_count": summary["training_materialization_allowed_count"],
        "current_runtime_model_usable_count": summary["current_runtime_model_usable_count"],
        "published_global_positive_count_remains": summary["published_global_positive_count_remains"],
        "published_future_candidate_count_remains": summary["published_future_training_admission_candidate_count_remains"],
        "authority_created_by_this_ingestion": False,
        "global_reconciliation_update_done": False,
        "global_census_update_done": False,
        "deterministic_double_materialization_byte_identical": True,
        "derived_projection_digests_verified": True,
        "current_census_preserved_and_bound": True,
        "feature_semantics_audit_required_later": True,
        "ready_for_YUN_reconciliation_successor": True,
        "ready_for_training": False,
    }
    required_true = (
        "repository_state_neutral", "formal_decision_binding_verified",
        "include_semantic_precedent_verified", "exact7_unique_complete",
        "candidate4_direct_role_projection_verified", "global_canonical_exact5_unchanged",
        "direct_profile_applicable_tasks_exact_0_3_4", "scientific_context_projection_verified",
        "observed_product_PRE_boundary_verified",
        "deterministic_double_materialization_byte_identical",
        "derived_projection_digests_verified", "current_census_preserved_and_bound",
        "feature_semantics_audit_required_later", "ready_for_YUN_reconciliation_successor",
    )
    required_false = (
        "authority_created_by_this_ingestion", "global_reconciliation_update_done",
        "global_census_update_done", "ready_for_training",
    )
    if any(result[field] is not True for field in required_true):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    if any(result[field] is not False for field in required_false):
        raise ValueError("CHECKER_REQUIRED_FALSE_ASSERTION_FAILED")
    if result["published_global_positive_count_remains"] != 82:
        raise ValueError("PUBLISHED_GLOBAL_POSITIVE_COUNT_BOUNDARY_INVALID")
    if result["published_future_candidate_count_remains"] != 12:
        raise ValueError("PUBLISHED_GLOBAL_FUTURE_CANDIDATE_BOUNDARY_INVALID")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    result = run_check_v1(parser.parse_args().repo_root)
    for key in (
        "repository_state_neutral", "output_artifact_count",
        "candidate_publication_file_count", "formal_decision_binding_verified",
        "formal_decision_byte_count", "formal_decision_sha256",
        "formal_decision_schema", "reviewer_id", "attestor_id", "approved_at_utc",
        "formal_evidence_provenance_binding_count", "include_semantic_precedent_verified",
        "exact7_unique_complete", "completed_human_positive_count", "task_relevant_count",
        "chemistry_positive_count", "reactive_pair_human_authority_count",
        "role_partition_human_authority_count", "candidate4_direct_role_projection_verified",
        "global_canonical_exact5_unchanged", "direct_profile_applicable_tasks_exact_0_3_4",
        "scientific_context_projection_verified", "observed_product_PRE_boundary_verified",
        "POST_source_evidence_count", "POST_geometry_training_authority_count",
        "PRE_geometry_authority_count", "reaction_family_target_count",
        "warhead_rule_target_count", "warhead_type_target_count", "training_include_count",
        "training_use_allowed_count", "future_training_admission_candidate_count",
        "training_admitted_count", "training_materialization_allowed_count",
        "current_runtime_model_usable_count", "published_global_positive_count_remains",
        "published_future_candidate_count_remains", "authority_created_by_this_ingestion",
        "global_reconciliation_update_done", "global_census_update_done",
        "deterministic_double_materialization_byte_identical",
        "derived_projection_digests_verified", "current_census_preserved_and_bound",
        "feature_semantics_audit_required_later", "ready_for_YUN_reconciliation_successor",
        "ready_for_training",
    ):
        value = result[key]
        print(key + "=" + (str(value).lower() if type(value) is bool else str(value)))
    for name, digest in result["materialized"]["artifact_sha256"].items():
        print(name + "_sha256=" + digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
