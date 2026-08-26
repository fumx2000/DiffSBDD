"""Ingest the frozen ONL Exact9 human decision as deterministic metadata.

This additive successor validates an exactly bound formal human decision and
projects authority that already exists in that source.  It does not interpret
chemistry, create reusable authority, update reconciliation or census state,
admit training samples, tensorize data, execute a model, or train parameters.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from typing import Any


__all__ = (
    "ONLIngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = (
    "covapie_onl_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT_SCHEMA_VERSION = "covapie_onl_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_onl_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_onl_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_onl_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_onl_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_onl_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_onl_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_onl_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_onl_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_onl_event_task_label_availability_v1.csv"
SUMMARY = "covapie_onl_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_onl_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

# Frozen V1 derived-projection contract digests.  These close standalone
# output validation; they do not create human, chemistry, reusable, geometry,
# training, or admission authority.  The manifest is deliberately excluded
# because its candidate source bindings change when production or tests change.
_EXPECTED_SNAPSHOT_SHA256_V1 = (
    "3ad211c80345130b7238fbae6046d61749c2f81784b359ecd2b71af6f06ae536"
)
_EXPECTED_MATRIX_SHA256_V1 = (
    "175f2f070967fb33e0133501a488cf30022818dbbadcd4b85f3ab497afda969c"
)
_EXPECTED_SUMMARY_SHA256_V1 = (
    "def73b5efef357c43a2796ffe9b1c660cf70c506baaa7e05523bf53894525d80"
)

FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "ONL_COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74/"
    "formal-human-decision-v1/onl_formal_human_decision_v1.json"
)
FORMAL_DECISION_BYTE_COUNT = 28678
FORMAL_DECISION_SHA256 = (
    "eb68b63046b561e857ae84640843914960c974ce7807be1ee18aba3f107581d5"
)
FORMAL_DECISION_SCHEMA = "covapie_onl_exact9_formal_human_decision_v1"
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74"
EXPECTED_APPROVED_AT_UTC = "2026-08-26T01:26:01Z"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
EXPECTED_D6 = (
    "productized DON/ONL context; no event-specific disposition exception"
)
AUTHORITY_SOURCE = "FORMAL_ONL_HUMAN_DECISION"
AUTHORITY_SCOPE = "SAMPLE_LEVEL_EXACT9"

EXPECTED_EVENTS = (
    ("COVAPIE_CYS_SG_EVENT_V1:1ECC:A:CYS:1-:SG:E:ONL:CE", 24, "1ECC", "A", "1-", "E", None, "covale1", 1.811783),
    ("COVAPIE_CYS_SG_EVENT_V1:1ECC:B:CYS:1-:SG:J:ONL:CE", 25, "1ECC", "B", "1-", "J", None, "covale2", 1.793403),
    ("COVAPIE_CYS_SG_EVENT_V1:1ECG:A:CYS:1-:SG:C:ONL:CE", 26, "1ECG", "A", "1-", "C", None, "covale1", 1.79727),
    ("COVAPIE_CYS_SG_EVENT_V1:1ECG:B:CYS:1-:SG:G:ONL:CE", 27, "1ECG", "B", "1-", "G", None, "covale2", 1.782853),
    ("COVAPIE_CYS_SG_EVENT_V1:1OFE:A:CYS:1-:SG:F:ONL:CE", 134, "1OFE", "A", "1-", "F", None, "covale1", 1.717089),
    ("COVAPIE_CYS_SG_EVENT_V1:3DLA:A:CYS:176-:SG:I:ONL:CE", 434, "3DLA", "A", "176-", "I", None, "covale1", 1.597732),
    ("COVAPIE_CYS_SG_EVENT_V1:3DLA:B:CYS:176-:SG:F:ONL:CE", 435, "3DLA", "B", "176-", "F", "B", "covale3", 1.624263),
    ("COVAPIE_CYS_SG_EVENT_V1:3DLA:C:CYS:176-:SG:G:ONL:CE", 436, "3DLA", "C", "176-", "G", None, "covale4", 1.62833),
    ("COVAPIE_CYS_SG_EVENT_V1:3DLA:D:CYS:176-:SG:H:ONL:CE", 437, "3DLA", "D", "176-", "H", None, "covale5", 1.624157),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)

EXPECTED_HEAVY_ATOMS = ("C", "CA", "CB", "CD", "CE", "CG", "N", "O", "OD", "OXT")
EXPECTED_WARHEAD = ("CD", "CE", "OD")
EXPECTED_LINKER: tuple[str, ...] = ()
EXPECTED_SCAFFOLD = ("C", "CA", "CB", "CG", "N", "O", "OXT")

CANONICAL_TASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (4, "scaffold_plus_linker_plus_warhead", "C", ("scaffold", "linker", "warhead"), ("minimal_seed",)),
)
DIRECT_VALID_TASK_IDS = (0, 3, 4)
DIRECT_PROFILE_TASK_APPLICABILITY = (
    (0, "warhead_only", "A", True, EXPECTED_ROLE_PROFILE),
    (1, "linker_plus_warhead", "B", False, EXPECTED_ROLE_PROFILE),
    (2, "scaffold_plus_warhead", "B2", False, EXPECTED_ROLE_PROFILE),
    (3, "scaffold_only", "B3", True, EXPECTED_ROLE_PROFILE),
    (4, "scaffold_plus_linker_plus_warhead", "C", True, EXPECTED_ROLE_PROFILE),
)

RUNTIME_SOURCE_RELATIVE = Path(
    "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"
)
CANONICAL_TASK_SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
IMMUTABLE_SEMANTIC_OWNER_BINDINGS = (
    (RUNTIME_SOURCE_RELATIVE, 37255, "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535", "direct_profile_runtime_contract"),
    (CANONICAL_TASK_SOURCE_RELATIVE, 67274, "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b", "canonical_role_and_task_semantics_owner"),
)

FROZEN_REVIEW_PACKAGE_BINDINGS = (
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/ONL_COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74/review-preparation-v1/onl_machine_evidence_manifest_v1.json"), 13219, "59648956a8eb984852e03fdce7d5495f08954a3bbbbcc7e3725f2bc8e8b5ef71", "ONL_MACHINE_EVIDENCE_MANIFEST"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/ONL_COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74/review-preparation-v1/onl_exact9_event_review_v1.csv"), 5029, "3c2819fac3f01cbad60c1ccc49e818ec2bb67d33c29580f6a6d8eaa7495c7e83", "ONL_EXACT9_EVENT_REVIEW"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/ONL_COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74/review-preparation-v1/onl_graph_and_role_candidates_v1.json"), 18113, "42597e2fa043a3e4e4ce8179b0b00ef3dd13b946516ca409e60df5482fcdecaf", "ONL_GRAPH_AND_ROLE_CANDIDATES"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/ONL_COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74/review-preparation-v1/HUMAN_REVIEW_GUIDE.md"), 6585, "3a9bfeee5e6d2045db1f3eed3b7e7f202dccddd5dc65a8e4aee6b9c0b4f31e2a", "ONL_HUMAN_REVIEW_GUIDE"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/ONL_COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74/review-preparation-v1/onl_unsigned_human_decision_template_v1.json"), 7336, "c04e39b840bb027f6d47cd7fa112320067289db9373e5de6d4df37b6880a0616", "ONL_UNSIGNED_HUMAN_DECISION_TEMPLATE"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/ONL_COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74/review-preparation-v1/onl_review_package_v1.py"), 97246, "fc08a7b6181c7a7046ac76142ca06daa8c12fbe4a91e0c1c54dccb8f342785e9", "ONL_REVIEW_PACKAGE_VALIDATOR"),
)

MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "pdb_id", "protein_chain",
    "cys_residue_id", "protein_altloc", "ligand_chain_or_asym", "ligand_altloc",
    "selected_connection_id", "POST_distance_angstrom", "POST_source_provenance",
    "human_task_relevance_decision", "chemistry_known_positive",
    "negative_chemistry", "task_domain_negative",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "protein_reactive_atom", "ligand_reactive_atom",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "selected_role_candidate_index_0based", "role_profile", "warhead_atoms_json",
    "linker_atoms_json", "scaffold_atoms_json", "boundary_bonds_json",
    "global_canonical_task_count", "canonical_task_applicability_json",
    "direct_profile_applicable_task_ids_json",
    "formal_event_training_use_decision", "training_use_human_decision_available",
    "human_training_excluded", "training_use_allowed", "POST_source_evidence_available",
    "POST_geometry_training_label_available_now", "PRE_geometry_authority_available",
    "PRE_geometry_training_label_available_now", "reaction_family_target_available",
    "warhead_rule_target_available", "warhead_type_target_available",
    "candidate_for_future_training_admission", "training_admitted",
    "training_materialization_allowed_now", "current_runtime_model_usable",
    "model_bound_pair_target_created_by_ingestion", "tensor_target_created",
    "observed_product_graph_is_authoritative_PRE_precursor",
    "PRE_precursor_reconstruction_performed", "event_specific_disposition_exception",
    "authority_source", "authority_ingested", "authority_created_by_this_successor",
)


class ONLIngestionSafetyError(ValueError):
    """Raised when the frozen ONL ingestion contract cannot be proven."""


def _fail(reason: str) -> None:
    raise ONLIngestionSafetyError(reason)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, extrasaction="raise", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _verify_payload(path: Path, expected_bytes: int, expected_sha256: str, label: str) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise ONLIngestionSafetyError("BOUND_SOURCE_READ_FAILED:" + label) from error
    if len(payload) != expected_bytes:
        _fail("BOUND_SOURCE_BYTE_COUNT_MISMATCH:" + label)
    if _sha(payload) != expected_sha256:
        _fail("BOUND_SOURCE_SHA256_MISMATCH:" + label)
    return payload


def _literal_assignments(path: Path, names: Sequence[str]) -> dict[str, object]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise ONLIngestionSafetyError("SOURCE_AST_READ_FAILED:" + path.name) from error
    wanted = set(names)
    values: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError) as error:
                    raise ONLIngestionSafetyError("SOURCE_CONTRACT_NOT_LITERAL:" + target.id) from error
    if set(values) != wanted:
        _fail("SOURCE_CONTRACT_ASSIGNMENTS_MISSING")
    return values


def _formal_binding() -> dict[str, object]:
    return {
        "path": FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": FORMAL_DECISION_BYTE_COUNT,
        "sha256": FORMAL_DECISION_SHA256,
        "sha256_scope": "file_bytes",
        "schema_version": FORMAL_DECISION_SCHEMA,
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "ONL",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "verification_status": "MATCHED",
    }


def _expected_evidence_provenance() -> list[dict[str, object]]:
    return [
        {
            "artifact_role": role,
            "byte_count": byte_count,
            "path": path.as_posix(),
            "path_namespace": "repository_parent_relative",
            "sha256": sha256,
            "sha256_scope": "file_bytes",
        }
        for path, byte_count, sha256, role in FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _formal_authority_boundary() -> dict[str, bool]:
    return {
        "POST_geometry_training_authority_created": False,
        "PRE_geometry_authority_created": False,
        "auxiliary_head_executed": False,
        "backward_performed": False,
        "batch_modified": False,
        "chemistry_sample_level_human_authority_created": True,
        "commit_performed": False,
        "completed_decision_ingestion_performed": False,
        "fine_tune_performed": False,
        "formal_sample_level_authority_created": True,
        "global_census_updated": False,
        "global_reconciliation_updated": False,
        "human_sample_level_reactive_pair_authority_created": True,
        "human_sample_level_role_partition_authority_created": True,
        "human_sample_level_task_relevance_authority_created": True,
        "human_sample_level_training_use_authority_created": True,
        "loader_modified": False,
        "loss_executed": False,
        "machine_auto_selection_performed": False,
        "model_forward_performed": False,
        "model_training_activation_authorized": False,
        "network_accessed": False,
        "optimizer_created": False,
        "optimizer_step_performed": False,
        "parameter_update_performed": False,
        "push_performed": False,
        "reaction_family_authority_created": False,
        "reactive_pair_human_authoritative": True,
        "ready_for_training": False,
        "repository_modified": False,
        "reusable_chemistry_authority_created": False,
        "role_partition_human_authoritative": True,
        "scientific_network_acquisition_performed": False,
        "task_relevance_sample_level_human_authority_created": True,
        "tensor_integration_performed": False,
        "training_admission_created": False,
        "training_admitted": False,
        "training_dataset_changed": False,
        "training_performed": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
    }


def _expected_role_partition() -> dict[str, object]:
    return {
        "applicable_canonical_task_ids": [0, 3, 4],
        "applicable_semantic_names": ["warhead_only", "scaffold_only", "scaffold_plus_linker_plus_warhead"],
        "boundary_bonds": [{"atom_id_1": "CD", "atom_id_2": "CG", "bond_order": "SING", "boundary_between_roles": ["warhead", "scaffold"]}],
        "candidate_index_0based": 1,
        "exact_heavy_atom_count": 10,
        "exact_heavy_atom_ids": list(EXPECTED_HEAVY_ATOMS),
        "global_canonical_Exact5": {
            "B3_present": True,
            "sixth_task_present": False,
            "task_count": 5,
            "tasks": [
                {"display_alias": alias, "semantic_name": semantic, "task_id": task_id}
                for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
            ],
        },
        "heavy_atom_disjoint": True,
        "heavy_atom_exhaustive": True,
        "human_role_partition_choice": "SELECT_CANDIDATE_1",
        "human_selected": True,
        "linker_atoms": [],
        "linker_empty": True,
        "machine_auto_selection_performed": False,
        "machine_recommended_candidate": None,
        "machine_selected": False,
        "role_partition_human_authoritative": True,
        "role_partition_human_authoritative_event_count": 9,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "sample_structurally_inapplicable_canonical_task_ids": [1, 2],
        "sample_structurally_inapplicable_semantic_names": ["linker_plus_warhead", "scaffold_plus_warhead"],
        "scaffold_atoms": list(EXPECTED_SCAFFOLD),
        "scaffold_connected": True,
        "source_candidate_graph_binding": {
            "byte_count": 18113,
            "path": FROZEN_REVIEW_PACKAGE_BINDINGS[2][0].as_posix(),
            "sha256": FROZEN_REVIEW_PACKAGE_BINDINGS[2][2],
        },
        "warhead_atoms": list(EXPECTED_WARHEAD),
        "warhead_connected": True,
    }


def _expected_raw_event(row: tuple[object, ...]) -> dict[str, object]:
    event_id, rank, pdb_id, protein_chain, residue_id, ligand_chain, ligand_altloc, connection, distance = row
    return {
        "D1_human_task_relevance_decision": "RELEVANT",
        "D2_human_chemistry_support_disposition": "POSITIVE",
        "D3_human_reactive_pair_decision": "CONFIRM_OBSERVED_PAIR",
        "D4_human_role_partition_choice": "SELECT_CANDIDATE_1",
        "D5_human_training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "D6_human_context": EXPECTED_D6,
        "POST_distance_angstrom": distance,
        "canonical_event_id": event_id,
        "cys_residue_id": residue_id,
        "decision_finalized": True,
        "event_specific_disposition_exception": False,
        "human_training_excluded": True,
        "ligand_altloc": ligand_altloc,
        "ligand_chain_or_asym": ligand_chain,
        "ligand_component_id": "ONL",
        "ligand_reactive_atom": "CE",
        "negative_chemistry": False,
        "pdb_id": pdb_id,
        "protein_altloc": None,
        "protein_chain": protein_chain,
        "protein_reactive_atom": "SG",
        "reactive_pair_human_authoritative": True,
        "role_partition_human_authoritative": True,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "scaleup_rank": rank,
        "selected_connection_id": connection,
        "selected_role_candidate_index_0based": 1,
        "task_domain_negative": False,
        "training_admitted": False,
    }


def _event_projection(raw: Mapping[str, object]) -> dict[str, object]:
    projected = dict(raw)
    projected.update(
        {
            "task_relevant": True,
            "chemistry_known_positive": True,
            "reactive_pair_human_decision_available": True,
            "role_partition_human_decision_available": True,
            "training_use_human_decision_available": True,
            "training_use_allowed": False,
            "POST_source_evidence_available": True,
            "POST_source_provenance": "FROZEN_FORMAL_EVENT_AND_BOUND_REVIEW_PACKAGE",
            "POST_geometry_training_label_available_now": False,
            "PRE_geometry_authority_available": False,
            "PRE_geometry_training_label_available_now": False,
            "reaction_family_target_available": False,
            "warhead_rule_target_available": False,
            "warhead_type_target_available": False,
            "candidate_for_future_training_admission": False,
            "training_materialization_allowed_now": False,
            "current_runtime_model_usable": False,
            "model_bound_pair_target_created_by_ingestion": False,
            "tensor_target_created": False,
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_this_successor": False,
        }
    )
    return projected


def _validate_formal_decision_v1(formal: Mapping[str, Any]) -> dict[str, object]:
    expected_top = {
        "schema_version": FORMAL_DECISION_SCHEMA,
        "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "ONL",
        "exact_event_count": 9,
        "unique_event_count": 9,
        "duplicate_event_count": 0,
        "omitted_event_count": 0,
        "extra_event_count": 0,
        "human_review_completed": True,
        "human_decision_created": True,
        "human_review_decision_created": True,
        "human_approval_recorded": True,
        "formal_authority_created": True,
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved": True,
        "unsigned": False,
        "training_admitted": False,
        "feature_semantics_status": "AUDIT_REQUIRED_LATER",
    }
    for field, expected in expected_top.items():
        if formal.get(field) != expected:
            _fail("FORMAL_TOP_LEVEL_SEMANTICS_INVALID:" + field)

    approval = formal.get("human_approval")
    expected_approval = {
        "approval_recorded": True,
        "approved": True,
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "attestation": "D1-D6_EXPLICITLY_AUTHORIZED_AS_RECORDED",
        "attestor_id": "fmx",
        "authorization_source": "EXTERNAL_EXPLICIT_HUMAN_APPROVAL_FOR_ONL_EXACT9_FORMAL_DECISION_V1",
        "overall_decision": "APPROVE_ONL_EXACT9_D1_D6_SAMPLE_LEVEL_DECISIONS",
        "reviewer_id": "fmx",
        "reviewer_provenance_attested": True,
        "unsigned": False,
    }
    if approval != expected_approval:
        _fail("FORMAL_HUMAN_APPROVAL_FIELDS_INVALID")

    canonical_ids = formal.get("canonical_event_ids")
    if type(canonical_ids) is not list or len(canonical_ids) != 9:
        _fail("FORMAL_CANONICAL_EVENT_EXACT9_INVALID")
    if len(set(canonical_ids)) != 9:
        _fail("FORMAL_CANONICAL_EVENT_DUPLICATE")
    if tuple(canonical_ids) != EXPECTED_EVENT_IDS:
        _fail("FORMAL_CANONICAL_EVENT_COVERAGE_INVALID")

    expected_unit = {
        "D1_task_relevance_decision": "RELEVANT",
        "D2_chemistry_support_disposition": "POSITIVE",
        "D3_reactive_pair_decision": "CONFIRM_OBSERVED_PAIR",
        "D4_role_partition_decision": "SELECT_CANDIDATE_1",
        "D5_training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "D6_context": EXPECTED_D6,
        "chemistry_negative_event_count": 0,
        "chemistry_positive_event_count": 9,
        "completed_human_review_event_count": 9,
        "event_specific_disposition_exception_count": 0,
        "exact_event_count": 9,
        "human_training_excluded_positive_event_count": 9,
        "negative_chemistry": False,
        "reactive_pair_human_authoritative_event_count": 9,
        "role_partition_human_authoritative_event_count": 9,
        "task_domain_negative": False,
        "task_relevant_event_count": 9,
        "training_admission_created": False,
        "training_dataset_changed": False,
        "training_include_event_count": 0,
    }
    if formal.get("unit_level_human_decisions") != expected_unit:
        _fail("FORMAL_UNIT_DECISION_SEMANTICS_INVALID")

    raw_events = formal.get("event_level_human_decisions")
    if type(raw_events) is not list or len(raw_events) != 9:
        _fail("FORMAL_EXACT9_EVENT_COUNT_INVALID")
    if any(type(event) is not dict for event in raw_events):
        _fail("FORMAL_EVENT_NOT_OBJECT")
    raw_ids = [event.get("canonical_event_id") for event in raw_events]
    if len(set(raw_ids)) != 9:
        _fail("FORMAL_EVENT_ID_DUPLICATE")
    if tuple(raw_ids) != EXPECTED_EVENT_IDS:
        _fail("FORMAL_EVENT_ID_COVERAGE_INVALID")
    expected_raw = [_expected_raw_event(row) for row in EXPECTED_EVENTS]
    for observed, expected in zip(raw_events, expected_raw, strict=True):
        if observed != expected:
            differing = sorted(key for key in set(observed) | set(expected) if observed.get(key) != expected.get(key))
            _fail("FORMAL_EVENT_SEMANTICS_INVALID:" + (differing[0] if differing else "schema"))

    if formal.get("reactive_pair_human_decision") != {
        "D3_human_choice": "CONFIRM_OBSERVED_PAIR",
        "exact_event_count": 9,
        "ligand_reactive_atom": "CE",
        "protein_reactive_atom": "SG",
        "reactive_pair_human_authoritative": True,
        "reactive_pair_human_authoritative_event_count": 9,
    }:
        _fail("FORMAL_REACTIVE_PAIR_SEMANTICS_DRIFT")
    if formal.get("selected_role_partition") != _expected_role_partition():
        _fail("FORMAL_SELECTED_ROLE_PARTITION_DRIFT")

    scaffold, linker, warhead = set(EXPECTED_SCAFFOLD), set(EXPECTED_LINKER), set(EXPECTED_WARHEAD)
    if scaffold & linker or scaffold & warhead or linker & warhead:
        _fail("ONL_ROLE_PARTITION_OVERLAP")
    if scaffold | linker | warhead != set(EXPECTED_HEAVY_ATOMS):
        _fail("ONL_ROLE_PARTITION_NOT_EXHAUSTIVE")

    if formal.get("training_use_human_decision") != {
        "D5_human_choice": "EXCLUDE_FROM_TRAINING_ONLY",
        "human_training_excluded_positive_event_count": 9,
        "training_admitted_count": 0,
        "training_dataset_changed": False,
        "training_exclusion_is_chemistry_negative": False,
        "training_include_event_count": 0,
    }:
        _fail("FORMAL_TRAINING_USE_SEMANTICS_INVALID")
    if formal.get("geometry_boundary") != {
        "POST_evidence_provenance_preserved": True,
        "POST_geometry_status": "OBSERVED_POST_COVALENT_REVIEW_EVIDENCE",
        "POST_geometry_training_authority_created": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_geometry_authority_created": False,
        "PRE_geometry_status": "PRE_REACTION_UNRESOLVED",
        "PRE_precursor_atom_reconstruction_authority_created": False,
        "PRE_zero_fill_performed": False,
    }:
        _fail("FORMAL_GEOMETRY_BOUNDARY_INVALID")
    if formal.get("reusable_authority_boundary") != {
        "cross_sample_reusable_rule_created": False,
        "reaction_family_authority_created": False,
        "reusable_chemistry_authority_created": False,
        "reusable_reactive_pair_authority_created": False,
        "reusable_role_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
    }:
        _fail("FORMAL_REUSABLE_AUTHORITY_BOUNDARY_INVALID")
    for field in ("reaction_family_authority", "warhead_rule_authority", "warhead_type_authority"):
        if formal.get(field) != {"authority_created": False, "authority_value": None, "status": "NOT_CREATED"}:
            _fail("FORMAL_AUXILIARY_AUTHORITY_INVALID:" + field)
    context = formal.get("human_approved_context")
    if type(context) is not dict or context.get("D6_exact_choice") != EXPECTED_D6 or context.get("event_specific_disposition_exception") is not False or context.get("scope") != "SAMPLE_SPECIFIC_ONL_EXACT9_ONLY":
        _fail("FORMAL_D6_CONTEXT_INVALID")
    scientific_context = context.get("human_approved_scientific_context")
    if type(scientific_context) is not str or "observed ONL product graph as an authoritative pre-reaction precursor topology" not in scientific_context or "No reusable reaction-family, warhead-rule, or warhead-type authority" not in scientific_context:
        _fail("FORMAL_PRODUCTIZED_CONTEXT_BOUNDARY_INVALID")
    if formal.get("authority_boundary") != _formal_authority_boundary():
        _fail("FORMAL_AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    if formal.get("evidence_provenance") != _expected_evidence_provenance():
        _fail("FORMAL_EVIDENCE_PROVENANCE_DRIFT")
    if formal.get("downstream_status") != {
        "completed_decision_ingestion": "NOT_DONE",
        "formal_human_decision_created": True,
        "global_census_update": "NOT_DONE",
        "global_reconciliation_update": "NOT_DONE",
        "training": "NOT_STARTED",
    }:
        _fail("FORMAL_DOWNSTREAM_STATUS_INVALID")
    return {
        "approval": dict(approval),
        "events": [_event_projection(event) for event in expected_raw],
        "role": _role_snapshot(),
        "formal_authority_boundary": _formal_authority_boundary(),
    }


def _semantic_owner_bindings(repo_root: Path, overrides: Mapping[Path, Path]) -> tuple[list[dict[str, object]], dict[str, object]]:
    bindings: list[dict[str, object]] = []
    for relative, byte_count, sha256, role in IMMUTABLE_SEMANTIC_OWNER_BINDINGS:
        payload = _verify_payload(overrides.get(relative, repo_root / relative), byte_count, sha256, role)
        bindings.append({"path": relative.as_posix(), "path_namespace": "repository_relative", "byte_count": len(payload), "sha256": _sha(payload), "sha256_scope": "file_bytes", "source_role": role, "verification_status": "MATCHED"})
    runtime_values = _literal_assignments(
        overrides.get(RUNTIME_SOURCE_RELATIVE, repo_root / RUNTIME_SOURCE_RELATIVE),
        ("DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1", "DIRECT_VALID_CANONICAL_TASK_IDS_V1", "DIRECT_PROFILE_TASK_APPLICABILITY_V1", "CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1", "DIRECT_PROFILE_RUNTIME_PRIMITIVES_READY_V1", "EXPANDED_TENSORIZER_INTEGRATION_PENDING_V1", "MODEL_ARCHITECTURE_CHANGE_REQUIRED_V1"),
    )
    canonical_values = _literal_assignments(overrides.get(CANONICAL_TASK_SOURCE_RELATIVE, repo_root / CANONICAL_TASK_SOURCE_RELATIVE), ("EXACT3_ROLES", "CANONICAL_TASKS"))
    expected_runtime = {
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": EXPECTED_ROLE_PROFILE,
        "DIRECT_VALID_CANONICAL_TASK_IDS_V1": DIRECT_VALID_TASK_IDS,
        "DIRECT_PROFILE_TASK_APPLICABILITY_V1": (
            (0, "warhead_only", "A", True, "generate_W_condition_on_S"),
            (1, "linker_plus_warhead", "B", False, "not_applicable_empty_linker_redundant_with_A"),
            (2, "scaffold_plus_warhead", "B2", False, "not_applicable_empty_non_C_fixed_context"),
            (3, "scaffold_only", "B3", True, "generate_S_condition_on_W"),
            (4, "scaffold_plus_linker_plus_warhead", "C", True, "generate_whole_ligand_preserve_Task_C_seed_semantics"),
        ),
        "CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1": False,
        "DIRECT_PROFILE_RUNTIME_PRIMITIVES_READY_V1": True,
        "EXPANDED_TENSORIZER_INTEGRATION_PENDING_V1": True,
        "MODEL_ARCHITECTURE_CHANGE_REQUIRED_V1": False,
    }
    if canonical_values.get("EXACT3_ROLES") != ("scaffold", "linker", "warhead") or canonical_values.get("CANONICAL_TASKS") != CANONICAL_TASKS:
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")
    for field, expected in expected_runtime.items():
        if runtime_values.get(field) != expected:
            _fail("DIRECT_PROFILE_RUNTIME_CONTRACT_DRIFT:" + field)
    runtime = {
        "role_profile": EXPECTED_ROLE_PROFILE,
        "direct_valid_canonical_task_ids": [0, 3, 4],
        "current11_tensorizer_direct_profile_supported": False,
        "direct_profile_runtime_primitives_ready": True,
        "expanded_tensorizer_integration_pending": True,
        "model_architecture_change_required": False,
    }
    return bindings, runtime


def _frozen_review_bindings(repository_parent: Path, overrides: Mapping[Path, Path]) -> list[dict[str, object]]:
    bindings: list[dict[str, object]] = []
    for relative, byte_count, sha256, role in FROZEN_REVIEW_PACKAGE_BINDINGS:
        payload = _verify_payload(overrides.get(relative, repository_parent / relative), byte_count, sha256, role)
        bindings.append({"path": relative.as_posix(), "path_namespace": "repository_parent_relative", "byte_count": len(payload), "sha256": _sha(payload), "sha256_scope": "file_bytes", "source_role": role, "verification_status": "MATCHED"})
    return bindings


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Load and validate the frozen formal decision and its semantic sources."""

    repo_root = repo_root.resolve()
    overrides = repository_path_overrides or {}
    formal_path = formal_decision_path.resolve() if formal_decision_path is not None else repo_root.parent / FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
    payload = _verify_payload(formal_path, FORMAL_DECISION_BYTE_COUNT, FORMAL_DECISION_SHA256, "formal_ONL_human_decision")
    try:
        formal = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ONLIngestionSafetyError("FORMAL_DECISION_JSON_INVALID") from error
    if type(formal) is not dict:
        _fail("FORMAL_DECISION_TOP_LEVEL_NOT_OBJECT")
    normalized = _validate_formal_decision_v1(formal)
    owner_bindings, runtime = _semantic_owner_bindings(repo_root, overrides)
    frozen_bindings = _frozen_review_bindings(repo_root.parent, overrides)
    return {
        "formal": formal,
        "normalized": normalized,
        "formal_decision_binding": _formal_binding(),
        "immutable_semantic_owner_bindings": owner_bindings,
        "frozen_review_package_bindings": frozen_bindings,
        "runtime_contract": runtime,
    }


def _role_snapshot() -> dict[str, object]:
    return {
        "selected_candidate_index_0based": 1,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "exact_heavy_atom_count": 10,
        "exact_heavy_atom_ids": list(EXPECTED_HEAVY_ATOMS),
        "warhead_atoms": list(EXPECTED_WARHEAD),
        "linker_atoms": [],
        "scaffold_atoms": list(EXPECTED_SCAFFOLD),
        "boundary_bonds": [{"atom_id_1": "CD", "atom_id_2": "CG", "bond_order": "SING", "boundary_between_roles": ["warhead", "scaffold"]}],
        "heavy_atom_disjoint": True,
        "heavy_atom_exhaustive": True,
        "warhead_connected": True,
        "scaffold_connected": True,
        "linker_empty": True,
        "sample_level_role_decision_exists_in_source": True,
        "sample_level_role_decision_created_by_ingestion": False,
    }


def _canonical_task_contract() -> dict[str, object]:
    return {
        "global_canonical_tasks": [
            {"task_id": task_id, "semantic_long_name": semantic, "display_alias": alias, "generated_roles": list(generated), "fixed_or_seed_roles": list(fixed)}
            for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_created": False,
        "canonical_task_vocabulary_changed": False,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "direct_profile_applicable_task_count": 3,
        "direct_profile_task_applicability": [
            {"task_id": task_id, "semantic_long_name": semantic, "display_alias": alias, "structurally_applicable": applicable, "reason": reason}
            for task_id, semantic, alias, applicable, reason in DIRECT_PROFILE_TASK_APPLICABILITY
        ],
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "formal_human_decision_modified": False,
        "sample_level_human_authority_created_by_ingestion": False,
        "sample_level_human_authority_ingested": True,
        "snapshot_created_by_ingestion": True,
        "new_reusable_authority_created": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "PRE_geometry_authority_created": False,
        "POST_geometry_training_authority_created": False,
        "tensor_integration_performed": False,
        "tensor_target_created": False,
        "model_bound_pair_target_created_by_ingestion": False,
        "model_forward_performed": False,
        "training_admission_created": False,
        "training_dataset_changed": False,
        "training_performed": False,
        "global_reconciliation_updated": False,
        "global_census_updated": False,
    }


def _snapshot(bound: Mapping[str, Any]) -> dict[str, object]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_role": "ADDITIVE_IMMUTABLE_ONL_COMPLETED_HUMAN_DECISION_SUCCESSOR",
        "snapshot_created_by_ingestion": True,
        "human_authority_created_by_ingestion": False,
        "formal_decision_binding": bound["formal_decision_binding"],
        "frozen_review_package_bindings": bound["frozen_review_package_bindings"],
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "ONL",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "authority_provenance": {
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_ingestion": False,
            "sample_level_human_authority_exists_in_source": True,
            "sample_level_human_authority_created_by_ingestion": False,
        },
        "unit_level_D1_D6": {
            "D1": "RELEVANT", "D2": "POSITIVE", "D3": "CONFIRM_OBSERVED_PAIR",
            "D4": "SELECT_CANDIDATE_1", "D5": "EXCLUDE_FROM_TRAINING_ONLY", "D6": EXPECTED_D6,
        },
        "events": bound["normalized"]["events"],
        "reactive_pair": {
            "protein_reactive_atom": "SG", "ligand_reactive_atom": "CE",
            "human_decision_available": True, "human_authoritative": True,
            "human_authority_created_by_ingestion": False,
            "model_bound_pair_target_created_by_ingestion": False,
            "tensor_target_created": False,
        },
        "selected_role_partition": bound["normalized"]["role"],
        "canonical_task_contract": _canonical_task_contract(),
        "direct_profile_runtime_contract": bound["runtime_contract"],
        "geometry_boundary": {
            "POST_source_evidence_count": 9,
            "POST_geometry_training_authority_count": 0,
            "POST_geometry_training_label_available_now": False,
            "PRE_geometry_status": "PRE_REACTION_UNRESOLVED",
            "PRE_geometry_authority_count": 0,
            "PRE_geometry_training_target_count": 0,
            "POST_to_PRE_copy_performed": False,
            "PRE_zero_fill_performed": False,
            "observed_product_graph_is_authoritative_PRE_precursor": False,
            "PRE_precursor_reconstruction_performed": False,
        },
        "productized_DON_ONL_context": {
            "observed_component": "ONL",
            "observed_component_description": "observed post-reaction 5-oxo-L-norleucine productized component derived from DON",
            "precursor_diazo_atoms_present_in_observed_product_graph": False,
            "observed_product_graph_is_authoritative_PRE_precursor": False,
            "PRE_precursor_reconstruction_performed": False,
            "reaction_family_authority_created": False,
            "warhead_rule_authority_created": False,
            "warhead_type_authority_created": False,
        },
        "reusable_authority_boundary": {
            "reaction_family_target_available": False,
            "warhead_rule_target_available": False,
            "warhead_type_target_available": False,
            "reusable_chemistry_authority_available": False,
            "new_reusable_authority_created": False,
        },
        "training_boundary": {
            "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
            "chemistry_positive_count": 9,
            "training_excluded_positive_count": 9,
            "training_include_count": 0,
            "candidate_for_future_training_admission_count": 0,
            "training_admitted_count": 0,
            "training_materialization_allowed_count": 0,
            "current_runtime_model_usable_count": 0,
            "ready_for_training": False,
            "feature_semantics": "AUDIT_REQUIRED_LATER",
        },
        "authority_boundary": _authority_boundary(),
        "formal_authority_boundary_source": bound["normalized"]["formal_authority_boundary"],
    }


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    boundary = _json_cell(_role_snapshot()["boundary_bonds"])
    applicability = _json_cell(
        _canonical_task_contract()["direct_profile_task_applicability"]
    )
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        rows.append({
            "canonical_event_id": event["canonical_event_id"],
            "scaleup_rank": str(event["scaleup_rank"]),
            "pdb_id": event["pdb_id"],
            "protein_chain": event["protein_chain"],
            "cys_residue_id": event["cys_residue_id"],
            "protein_altloc": "" if event["protein_altloc"] is None else event["protein_altloc"],
            "ligand_chain_or_asym": event["ligand_chain_or_asym"],
            "ligand_altloc": "" if event["ligand_altloc"] is None else event["ligand_altloc"],
            "selected_connection_id": event["selected_connection_id"],
            "POST_distance_angstrom": str(event["POST_distance_angstrom"]),
            "POST_source_provenance": event["POST_source_provenance"],
            "human_task_relevance_decision": "RELEVANT",
            "chemistry_known_positive": "true", "negative_chemistry": "false", "task_domain_negative": "false",
            "reactive_pair_human_decision_available": "true", "reactive_pair_human_authoritative": "true",
            "protein_reactive_atom": "SG", "ligand_reactive_atom": "CE",
            "role_partition_human_decision_available": "true", "role_partition_human_authoritative": "true",
            "selected_role_candidate_index_0based": "1", "role_profile": EXPECTED_ROLE_PROFILE,
            "warhead_atoms_json": _json_cell(list(EXPECTED_WARHEAD)), "linker_atoms_json": "[]",
            "scaffold_atoms_json": _json_cell(list(EXPECTED_SCAFFOLD)), "boundary_bonds_json": boundary,
            "global_canonical_task_count": "5", "canonical_task_applicability_json": applicability,
            "direct_profile_applicable_task_ids_json": "[0,3,4]",
            "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
            "training_use_human_decision_available": "true", "human_training_excluded": "true", "training_use_allowed": "false",
            "POST_source_evidence_available": "true", "POST_geometry_training_label_available_now": "false",
            "PRE_geometry_authority_available": "false", "PRE_geometry_training_label_available_now": "false",
            "reaction_family_target_available": "false", "warhead_rule_target_available": "false", "warhead_type_target_available": "false",
            "candidate_for_future_training_admission": "false", "training_admitted": "false",
            "training_materialization_allowed_now": "false", "current_runtime_model_usable": "false",
            "model_bound_pair_target_created_by_ingestion": "false", "tensor_target_created": "false",
            "observed_product_graph_is_authoritative_PRE_precursor": "false", "PRE_precursor_reconstruction_performed": "false",
            "event_specific_disposition_exception": "false", "authority_source": AUTHORITY_SOURCE,
            "authority_ingested": "true", "authority_created_by_this_successor": "false",
        })
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "event_count": 9,
        "task_relevant_count": 9,
        "chemistry_positive_count": 9,
        "ONL_source_local_positive_count": 9,
        "completed_human_positive_count": 9,
        "reactive_pair_human_authority_count": 9,
        "role_partition_human_authority_count": 9,
        "direct_profile_count": 9,
        "strict_profile_count": 0,
        "global_canonical_task_count": 5,
        "direct_profile_applicable_task_count_per_event": 3,
        "POST_source_evidence_count": 9,
        "POST_geometry_training_authority_count": 0,
        "PRE_geometry_authority_count": 0,
        "PRE_geometry_training_target_count": 0,
        "reaction_family_target_count": 0,
        "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
        "training_excluded_positive_count": 9,
        "training_include_count": 0,
        "future_training_admission_candidate_count": 0,
        "training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "ready_for_training": False,
        "formal_human_decision_ingested": True,
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
        "published_global_positive_count_remains": 49,
        "ready_for_ONL_reconciliation_successor": True,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "authority_boundary": _authority_boundary(),
    }


def _validate_text_payload(label: str, payload: bytes) -> None:
    if type(payload) is not bytes or payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload or b"\r" in payload or not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        _fail("TEXT_INVARIANT_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ONLIngestionSafetyError("UTF8_INVALID:" + label) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TRAILING_WHITESPACE_INVALID:" + label)


def _candidate_source_bindings(repo_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative, role in ((SOURCE_RELATIVE, "production_owner"), (CHECKER_RELATIVE, "fail_closed_checker"), (TEST_RELATIVE, "targeted_test_contract")):
        path = repo_root / relative
        if not path.is_file() or path.is_symlink():
            _fail("CANDIDATE_SOURCE_NOT_REGULAR:" + relative.as_posix())
        payload = path.read_bytes()
        _validate_text_payload(relative.as_posix(), payload)
        rows.append({"path": relative.as_posix(), "path_namespace": "repository_relative", "byte_count": len(payload), "sha256": _sha(payload), "sha256_scope": "file_bytes", "source_role": role})
    return rows


def build_artifacts_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Build the deterministic Exact4 projection in memory."""

    repo_root = repo_root.resolve()
    bound = load_frozen_formal_decision_v1(repo_root, formal_decision_path=formal_decision_path, repository_path_overrides=repository_path_overrides)
    snapshot_payload = _json_bytes(_snapshot(bound))
    matrix_payload = _csv_bytes(MATRIX_HEADER, _matrix_rows(_snapshot(bound)))
    summary_payload = _json_bytes(_summary())
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "ONL_COMPLETED_DECISION_AND_EVENT_TASK_LABEL_AVAILABILITY_NOT_ADMISSION",
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "frozen_review_package_bindings": bound["frozen_review_package_bindings"],
        "immutable_semantic_owner_bindings": bound["immutable_semantic_owner_bindings"],
        "candidate_source_bindings": _candidate_source_bindings(repo_root),
        "canonical_task_contract": _canonical_task_contract(),
        "counts": {key: value for key, value in _summary().items() if type(value) is int and type(value) is not bool},
        "human_authority_ingestion_semantics": {
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_ingestion": False,
            "sample_level_human_authority_exists_in_source": True,
        },
        "output_artifact_bindings": {
            SNAPSHOT: {"sha256": _sha(snapshot_payload)},
            MATRIX: {"sha256": _sha(matrix_payload)},
            SUMMARY: {"sha256": _sha(summary_payload)},
        },
        "manifest_self_sha256_recorded": False,
        "manifest_self_sha256_policy": "SELF_SHA256_PROHIBITED",
        "deterministic": True,
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
        "feature_semantics_audit_required_before_formal_training": True,
        "ready_for_training": False,
        "authority_boundary": _authority_boundary(),
    }
    artifacts = {
        SNAPSHOT: snapshot_payload,
        MATRIX: matrix_payload,
        SUMMARY: summary_payload,
        MANIFEST: _json_bytes(manifest),
    }
    validate_completed_decision_projection_v1(artifacts, repo_root=repo_root)
    return artifacts


def _reject_dynamic_metadata(value: object) -> None:
    forbidden = {"generated_at", "generated_at_utc", "hostname", "host_name", "pid", "process_id", "uuid", "git_head", "git_parent", "commit_subject", "origin_main", "ahead", "behind"}
    if type(value) is dict:
        for key, child in value.items():
            if key in forbidden:
                _fail("DYNAMIC_OR_LIFECYCLE_METADATA_FORBIDDEN:" + key)
            _reject_dynamic_metadata(child)
    elif type(value) is list:
        for child in value:
            _reject_dynamic_metadata(child)


def validate_completed_decision_projection_v1(
    artifacts: Mapping[str, bytes], *, repo_root: Path | None = None
) -> None:
    """Validate direct Exact4 evidence without trusting manifest booleans."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    try:
        snapshot = json.loads(artifacts[SNAPSHOT])
        summary = json.loads(artifacts[SUMMARY])
        manifest = json.loads(artifacts[MANIFEST])
        matrix = list(csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8"))))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ONLIngestionSafetyError("OUTPUT_PARSE_FAILED") from error
    for document in (snapshot, summary, manifest):
        _reject_dynamic_metadata(document)
    if summary != _summary():
        _fail("SUMMARY_EXACT_COUNTS_OR_BOUNDARY_INVALID")
    if type(snapshot) is not dict or snapshot.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        _fail("SNAPSHOT_SCHEMA_INVALID")
    if snapshot.get("snapshot_created_by_ingestion") is not True or snapshot.get("human_authority_created_by_ingestion") is not False:
        _fail("SNAPSHOT_AUTHORITY_CREATION_BOUNDARY_INVALID")
    events = snapshot.get("events")
    if type(events) is not list or len(events) != 9:
        _fail("SNAPSHOT_EXACT9_EVENT_COUNT_INVALID")
    ids = [event.get("canonical_event_id") for event in events if type(event) is dict]
    if len(ids) != 9 or len(set(ids)) != 9 or tuple(ids) != EXPECTED_EVENT_IDS:
        _fail("SNAPSHOT_EXACT9_COVERAGE_INVALID")
    if [event.get("scaleup_rank") for event in events] != sorted(event.get("scaleup_rank") for event in events):
        _fail("SNAPSHOT_SCALEUP_RANK_ORDER_INVALID")
    if snapshot.get("selected_role_partition") != _role_snapshot() or snapshot.get("canonical_task_contract") != _canonical_task_contract():
        _fail("SNAPSHOT_ROLE_OR_EXACT5_CONTRACT_INVALID")
    if snapshot.get("authority_boundary") != _authority_boundary():
        _fail("SNAPSHOT_AUTHORITY_BOUNDARY_INVALID")
    geometry = snapshot.get("geometry_boundary")
    if type(geometry) is not dict or geometry.get("POST_source_evidence_count") != 9 or geometry.get("POST_geometry_training_authority_count") != 0 or geometry.get("PRE_geometry_authority_count") != 0 or geometry.get("observed_product_graph_is_authoritative_PRE_precursor") is not False or geometry.get("PRE_precursor_reconstruction_performed") is not False:
        _fail("SNAPSHOT_GEOMETRY_BOUNDARY_INVALID")
    training = snapshot.get("training_boundary")
    if type(training) is not dict or training.get("training_excluded_positive_count") != 9 or training.get("training_include_count") != 0 or training.get("candidate_for_future_training_admission_count") != 0 or training.get("training_admitted_count") != 0 or training.get("ready_for_training") is not False:
        _fail("SNAPSHOT_TRAINING_BOUNDARY_INVALID")

    if (list(matrix[0].keys()) if matrix else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    if len(matrix) != 9 or tuple(row["canonical_event_id"] for row in matrix) != EXPECTED_EVENT_IDS or len({row["canonical_event_id"] for row in matrix}) != 9:
        _fail("MATRIX_EXACT9_INVALID")
    if artifacts[MATRIX] != _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot)):
        _fail("MATRIX_DIRECT_EVIDENCE_INVALID")
    for row in matrix:
        for field in ("chemistry_known_positive", "reactive_pair_human_decision_available", "reactive_pair_human_authoritative", "role_partition_human_decision_available", "role_partition_human_authoritative", "training_use_human_decision_available", "human_training_excluded", "POST_source_evidence_available", "authority_ingested"):
            if row[field] != "true":
                _fail("MATRIX_REQUIRED_AUTHORITY_UNAVAILABLE:" + field)
        for field in ("negative_chemistry", "task_domain_negative", "training_use_allowed", "POST_geometry_training_label_available_now", "PRE_geometry_authority_available", "PRE_geometry_training_label_available_now", "reaction_family_target_available", "warhead_rule_target_available", "warhead_type_target_available", "candidate_for_future_training_admission", "training_admitted", "training_materialization_allowed_now", "current_runtime_model_usable", "model_bound_pair_target_created_by_ingestion", "tensor_target_created", "observed_product_graph_is_authoritative_PRE_precursor", "PRE_precursor_reconstruction_performed", "event_specific_disposition_exception", "authority_created_by_this_successor"):
            if row[field] != "false":
                _fail("MATRIX_SAFETY_FLAG_INVALID:" + field)
        if row["global_canonical_task_count"] != "5" or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]" or row["role_profile"] != EXPECTED_ROLE_PROFILE:
            _fail("MATRIX_DIRECT_PROFILE_CONTRACT_INVALID")
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            len(applicability) != 5
            or [item["task_id"] for item in applicability if item["structurally_applicable"]] != [0, 3, 4]
            or applicability[3]["semantic_long_name"] != "scaffold_only"
            or applicability[1]["reason"] != EXPECTED_ROLE_PROFILE
            or applicability[2]["reason"] != EXPECTED_ROLE_PROFILE
        ):
            _fail("MATRIX_EXACT5_APPLICABILITY_INVALID")

    if type(manifest) is not dict or manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION or manifest.get("candidate_publication_file_count") != 7 or manifest.get("output_artifact_count") != 4 or manifest.get("deterministic") is not True or manifest.get("manifest_self_sha256_recorded") is not False or manifest.get("ready_for_training") is not False:
        _fail("MANIFEST_BOUNDARY_INVALID")
    if manifest.get("formal_decision_binding") != _formal_binding() or manifest.get("canonical_task_contract") != _canonical_task_contract():
        _fail("MANIFEST_SOURCE_OR_EXACT5_BINDING_INVALID")
    if manifest.get("output_artifact_bindings") != {SNAPSHOT: {"sha256": _sha(artifacts[SNAPSHOT])}, MATRIX: {"sha256": _sha(artifacts[MATRIX])}, SUMMARY: {"sha256": _sha(artifacts[SUMMARY])}}:
        _fail("MANIFEST_OUTPUT_BINDINGS_INVALID")
    if manifest.get("authority_boundary") != _authority_boundary() or manifest.get("global_reconciliation_update_status") != "NOT_DONE_THIS_STEP" or manifest.get("global_census_update_status") != "NOT_DONE_THIS_STEP":
        _fail("MANIFEST_NON_ACTION_BOUNDARY_INVALID")
    if _sha(artifacts[SNAPSHOT]) != _EXPECTED_SNAPSHOT_SHA256_V1:
        _fail("SNAPSHOT_EXACT_PROJECTION_SHA256_INVALID")
    if _sha(artifacts[MATRIX]) != _EXPECTED_MATRIX_SHA256_V1:
        _fail("MATRIX_EXACT_PROJECTION_SHA256_INVALID")
    if _sha(artifacts[SUMMARY]) != _EXPECTED_SUMMARY_SHA256_V1:
        _fail("SUMMARY_EXACT_PROJECTION_SHA256_INVALID")
    if repo_root is not None:
        repo_root = repo_root.resolve()
        bound = load_frozen_formal_decision_v1(repo_root)
        if snapshot != _snapshot(bound):
            _fail("SNAPSHOT_DIRECT_SOURCE_PROJECTION_INVALID")
        if manifest.get("candidate_source_bindings") != _candidate_source_bindings(repo_root):
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDINGS_INVALID")
        if manifest.get("frozen_review_package_bindings") != bound["frozen_review_package_bindings"] or manifest.get("immutable_semantic_owner_bindings") != bound["immutable_semantic_owner_bindings"]:
            _fail("MANIFEST_FROZEN_SOURCE_BINDINGS_INVALID")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_artifacts_v1(repo_root: Path, *, output_root: Path | None = None) -> dict[str, bytes]:
    """Build and atomically materialize only the Exact4 outputs."""

    repo_root = repo_root.resolve()
    artifacts = build_artifacts_v1(repo_root)
    destination = output_root.resolve() if output_root is not None else repo_root / OUTPUT_ROOT_RELATIVE
    if destination.exists():
        unexpected = {path.name for path in destination.iterdir() if path.name not in OUTPUT_FILENAMES}
        if unexpected:
            _fail("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES")
    for name in OUTPUT_FILENAMES:
        _atomic_write(destination / name, artifacts[name])
    return artifacts


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    expected = build_artifacts_v1(repo_root)
    output_root = repo_root / OUTPUT_ROOT_RELATIVE
    if not output_root.is_dir() or output_root.is_symlink():
        _fail("OUTPUT_DIRECTORY_MISSING_OR_INVALID")
    if {path.name for path in output_root.iterdir()} != set(OUTPUT_FILENAMES):
        _fail("MATERIALIZED_OUTPUT_EXACT4_INVALID")
    observed: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = output_root / name
        if not path.is_file() or path.is_symlink():
            _fail("MATERIALIZED_OUTPUT_NOT_REGULAR:" + name)
        observed[name] = path.read_bytes()
        if observed[name] != expected[name]:
            _fail("MATERIALIZED_OUTPUT_BYTES_MISMATCH:" + name)
    validate_completed_decision_projection_v1(observed, repo_root=repo_root)
    return {
        "materialized_output_valid": True,
        "output_artifact_count": 4,
        "candidate_publication_file_count": 7,
        "artifact_sha256": {name: _sha(observed[name]) for name in OUTPUT_FILENAMES},
        "formal_decision_sha256": FORMAL_DECISION_SHA256,
        "event_count": 9,
        "chemistry_positive_count": 9,
        "training_excluded_positive_count": 9,
        "training_include_count": 0,
        "future_training_admission_candidate_count": 0,
        "training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "deterministic_rebuild_matches_materialized": True,
        "ready_for_training": False,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    artifacts = materialize_artifacts_v1(repo_root)
    print("formal_human_decision_ingested=true")
    print("event_count=9")
    print("chemistry_positive_count=9")
    print("training_excluded_positive_count=9")
    print("training_include_count=0")
    print("training_admitted_count=0")
    print("ready_for_training=false")
    for name in OUTPUT_FILENAMES:
        print(name + "_sha256=" + _sha(artifacts[name]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
