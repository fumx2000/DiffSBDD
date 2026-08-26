"""Ingest the frozen 2VS Exact8 human decision as deterministic metadata.

This additive projection validates and ingests authority already present in the
formal human decision.  It does not reinterpret 2VS chemistry, create reusable
authority, reconstruct PRE topology or geometry, reconcile global state, admit
training samples, tensorize data, execute a model, or train parameters.
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
    "TwoVSIngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = (
    "covapie_2vs_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT_SCHEMA_VERSION = "covapie_2vs_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_2vs_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_2vs_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_2vs_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_2vs_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_2vs_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_2vs_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_2vs_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_2vs_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_2vs_event_task_label_availability_v1.csv"
SUMMARY = "covapie_2vs_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_2vs_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

# Frozen only after semantic validation of the fully source-derived projection.
# These are projection-contract digests, never human or chemistry authority.
_EXPECTED_SNAPSHOT_SHA256_V1 = (
    "be230bd1beae6ef868a29bfb3c02343b15a1a88cc5c013ff60f3ba05091dbe7c"
)
_EXPECTED_MATRIX_SHA256_V1 = (
    "b5c08fecbd5a68408cea6b7ce4747734f3d6c3ea37d81aef939a634d6439c5cc"
)
_EXPECTED_SUMMARY_SHA256_V1 = (
    "ee54ac822829d6f835ecf35978d2d9d05a48f8afeb485cc63b274902e2bbeed3"
)

FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "2VS_COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22/"
    "formal-human-decision-v1/2vs_formal_human_decision_v1.json"
)
FORMAL_DECISION_BYTE_COUNT = 28640
FORMAL_DECISION_SHA256 = (
    "49f33bb2a21669ddb7ab8e98cfa710380e031b280855d5f3ebe6796cde2d06aa"
)
FORMAL_DECISION_SCHEMA = "covapie_2vs_exact8_formal_human_decision_v1"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "bd99be3cd4b2c3a04ffae2939acd5e635fb8ac8f20ec3c8579cb3b62240df53d"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22"
EXPECTED_APPROVED_AT_UTC = "2026-08-26T12:21:56Z"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
EXPECTED_CANDIDATE_ID = "2VS_GRAPH_LOCAL_CANDIDATE_00"
EXPECTED_D6 = (
    "AMSDH catalytic thioacyl context; 4NPI = wild-type thioacyl intermediate; "
    "4OUB = E268A thioacyl intermediate; no event-specific disposition exception"
)
AUTHORITY_SOURCE = "FORMAL_2VS_HUMAN_DECISION"
AUTHORITY_SCOPE = "SAMPLE_LEVEL_2VS_EXACT8_ONLY"
HUMAN_CONTEXT_SCOPE = "SAMPLE_SPECIFIC_2VS_EXACT8_ONLY"

EXPECTED_EVENTS = (
    ("COVAPIE_CYS_SG_EVENT_V1:4NPI:A:CYS:302-:SG:G:2VS:CA6", 848, "4NPI", 1, "A", "CYS:302-", None, "G", None, "covale1", 1.864996, "1.864996"),
    ("COVAPIE_CYS_SG_EVENT_V1:4NPI:B:CYS:302-:SG:J:2VS:CA6", 849, "4NPI", 1, "B", "CYS:302-", None, "J", None, "covale2", 1.81187, "1.811870"),
    ("COVAPIE_CYS_SG_EVENT_V1:4NPI:C:CYS:302-:SG:M:2VS:CA6", 850, "4NPI", 1, "C", "CYS:302-", None, "M", None, "covale3", 1.86213, "1.862130"),
    ("COVAPIE_CYS_SG_EVENT_V1:4NPI:D:CYS:302-:SG:P:2VS:CA6", 851, "4NPI", 1, "D", "CYS:302-", None, "P", None, "covale4", 1.846188, "1.846188"),
    ("COVAPIE_CYS_SG_EVENT_V1:4OUB:A:CYS:302-:SG:G:2VS:CA6", 859, "4OUB", 1, "A", "CYS:302-", None, "G", None, "covale1", 1.922091, "1.922091"),
    ("COVAPIE_CYS_SG_EVENT_V1:4OUB:B:CYS:302-:SG:J:2VS:CA6", 860, "4OUB", 1, "B", "CYS:302-", None, "J", None, "covale2", 1.771051, "1.771051"),
    ("COVAPIE_CYS_SG_EVENT_V1:4OUB:C:CYS:302-:SG:M:2VS:CA6", 861, "4OUB", 1, "C", "CYS:302-", None, "M", None, "covale3", 1.905611, "1.905611"),
    ("COVAPIE_CYS_SG_EVENT_V1:4OUB:D:CYS:302-:SG:P:2VS:CA6", 862, "4OUB", 1, "D", "CYS:302-", None, "P", None, "covale4", 1.89111, "1.891110"),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)

EXPECTED_HEAVY_ATOMS = (
    "CA1", "CA2", "CA3", "CA4", "CA5", "CA6", "OA1", "OA2", "OA3", "OA4",
)
EXPECTED_WARHEAD = ("CA6", "OA4")
EXPECTED_LINKER: tuple[str, ...] = ()
EXPECTED_SCAFFOLD = ("CA1", "CA2", "CA3", "CA4", "CA5", "OA1", "OA2", "OA3")

CANONICAL_TASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (4, "scaffold_plus_linker_plus_warhead", "C", ("scaffold", "linker", "warhead"), ("minimal_seed",)),
)
DIRECT_VALID_TASK_IDS = (0, 3, 4)

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
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/2VS_COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22/review-preparation-v1/2vs_machine_evidence_manifest_v1.json"), 15847, "0947bad44d54dd216ce3c1bf393fe1fecd3efd881d30dca236c3adf6139566a8", "2VS_MACHINE_EVIDENCE_MANIFEST_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/2VS_COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22/review-preparation-v1/2vs_exact8_event_review_v1.csv"), 6976, "197ce41df93cabfb05f78d4f7d556a7a5bc5bd61f4f4ec85492b901d916b340d", "2VS_EXACT8_EVENT_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/2VS_COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22/review-preparation-v1/2vs_graph_and_role_candidates_v1.json"), 18072, "acb915b6a6580dc7760aac3cb9577f2317696d23bd6d650593b173d5faa4f749", "2VS_GRAPH_AND_ROLE_CANDIDATES_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/2VS_COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22/review-preparation-v1/HUMAN_REVIEW_GUIDE.md"), 5027, "04049636ee68584009868b3289822cbaf2311b8be08e097d14cf62e2a7d397d0", "2VS_HUMAN_REVIEW_GUIDE_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/2VS_COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22/review-preparation-v1/2vs_unsigned_human_decision_template_v1.json"), 8110, "f12ad5f4980adb8f87ae96ce5ca7747a4a52baa96a8aea640fe003181391d355", "2VS_UNSIGNED_DECISION_TEMPLATE_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/2VS_COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22/review-preparation-v1/ligand_2vs_review_package_v1.py"), 102684, "6788274c9b3fa15adcc4b298c76133047741c61c5d5afc302824e1ad93d7fa1a", "2VS_REVIEW_PACKAGE_VALIDATOR_REVIEWED_BYTES", "0755"),
)


class TwoVSIngestionSafetyError(ValueError):
    """Raised when the frozen 2VS ingestion contract cannot be proven."""


def _fail(reason: str) -> None:
    raise TwoVSIngestionSafetyError(reason)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _csv_bytes(
    header: Sequence[str], rows: Sequence[Mapping[str, object]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=header,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _verify_payload(
    path: Path, expected_bytes: int, expected_sha256: str, label: str
) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise TwoVSIngestionSafetyError(
            "BOUND_SOURCE_READ_FAILED:" + label
        ) from error
    if len(payload) != expected_bytes:
        _fail("BOUND_SOURCE_BYTE_COUNT_MISMATCH:" + label)
    if _sha(payload) != expected_sha256:
        _fail("BOUND_SOURCE_SHA256_MISMATCH:" + label)
    return payload


def _literal_assignments(path: Path, names: Sequence[str]) -> dict[str, object]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise TwoVSIngestionSafetyError(
            "SOURCE_AST_READ_FAILED:" + path.name
        ) from error
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
                    raise TwoVSIngestionSafetyError(
                        "SOURCE_CONTRACT_NOT_LITERAL:" + target.id
                    ) from error
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
        "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "2VS",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "verification_status": "MATCHED",
    }


def _expected_evidence_provenance() -> list[dict[str, object]]:
    # This namespace is frozen inside the reviewed formal payload.  It is not
    # normalized to the namespace used by the ingestion's formal-file binding.
    return [
        {
            "path": path.as_posix(),
            "path_namespace": "project_parent_relative",
            "byte_count": byte_count,
            "sha256": sha256,
            "sha256_scope": "file_bytes",
            "mode": mode,
            "source_role": role,
            "verification_status": "MATCHED",
            "predecessor_immutable": True,
        }
        for path, byte_count, sha256, role, mode in FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _expected_human_approval() -> dict[str, object]:
    return {
        "approval_recorded": True,
        "approved": True,
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "reviewer_provenance_attested": True,
        "attestation": "D1-D6_EXPLICITLY_AUTHORIZED_AS_RECORDED",
        "authorization_source": "EXTERNAL_EXPLICIT_HUMAN_APPROVAL",
        "overall_decision": "APPROVE_2VS_EXACT8_D1_D6_SAMPLE_LEVEL_DECISIONS",
        "human_choices_externally_authorized": True,
        "unsigned": False,
    }


def _formal_authority_boundary() -> dict[str, object]:
    return {
        "formal_sample_level_authority_created": True,
        "task_relevance_sample_level_human_authority_created": True,
        "chemistry_sample_level_human_authority_created": True,
        "human_sample_level_reactive_pair_authority_created": True,
        "human_sample_level_role_partition_authority_created": True,
        "human_sample_level_training_use_authority_created": True,
        "reactive_pair_human_authoritative": True,
        "role_partition_human_authoritative": True,
        "human_choices_externally_authorized": True,
        "machine_auto_selection_performed": False,
        "machine_recommended_candidate": None,
        "POST_geometry_training_authority_created": False,
        "PRE_geometry_authority_created": False,
        "PRE_precursor_topology_authority_created": False,
        "PRE_precursor_reconstruction_performed": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "reusable_chemistry_authority_created": False,
        "reusable_reactive_pair_authority_created": False,
        "reusable_role_authority_created": False,
        "training_admission_created": False,
        "training_admitted": False,
        "training_dataset_changed": False,
        "completed_decision_ingestion_performed": False,
        "global_reconciliation_updated": False,
        "global_census_updated": False,
        "tensor_integration_performed": False,
        "loader_modified": False,
        "batch_modified": False,
        "model_forward_performed": False,
        "auxiliary_head_executed": False,
        "loss_executed": False,
        "backward_performed": False,
        "optimizer_created": False,
        "optimizer_step_performed": False,
        "parameter_update_performed": False,
        "fine_tune_performed": False,
        "training_performed": False,
        "model_training_activation_authorized": False,
        "ready_for_training": False,
        "repository_modified": False,
        "network_accessed": False,
        "scientific_network_acquisition_performed": False,
        "commit_performed": False,
        "push_performed": False,
    }


def _expected_formal_role_partition() -> dict[str, object]:
    return {
        "human_role_partition_choice": "SELECT_CANDIDATE_0",
        "candidate_index_0based": 0,
        "candidate_id": EXPECTED_CANDIDATE_ID,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "exact_heavy_atom_count": 10,
        "exact_heavy_atom_ids": list(EXPECTED_HEAVY_ATOMS),
        "warhead_atoms": list(EXPECTED_WARHEAD),
        "linker_atoms": [],
        "scaffold_atoms": list(EXPECTED_SCAFFOLD),
        "boundary_bonds": [
            {
                "atom_id_1": "CA5",
                "atom_id_2": "CA6",
                "bond_order": "SING",
                "role_1": "scaffold",
                "role_2": "warhead",
            }
        ],
        "boundary_atoms": ["CA5", "CA6"],
        "boundary_bond_order": "SING",
        "heavy_atom_disjoint": True,
        "heavy_atom_exhaustive": True,
        "warhead_connected": True,
        "linker_empty": True,
        "linker_connected_or_empty": True,
        "scaffold_connected": True,
        "applicable_canonical_task_ids": [0, 3, 4],
        "applicable_semantic_names": [
            "warhead_only",
            "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
        ],
        "sample_structurally_inapplicable_canonical_task_ids": [1, 2],
        "sample_structurally_inapplicable_semantic_names": [
            "linker_plus_warhead",
            "scaffold_plus_warhead",
        ],
        "global_canonical_Exact5": {
            "B3_present": True,
            "sixth_task_present": False,
            "task_count": 5,
            "tasks": [
                {
                    "display_alias": alias,
                    "semantic_name": semantic,
                    "task_id": task_id,
                }
                for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
            ],
        },
        "source_candidate_graph_binding": {
            "path": FROZEN_REVIEW_PACKAGE_BINDINGS[2][0].as_posix(),
            "byte_count": FROZEN_REVIEW_PACKAGE_BINDINGS[2][1],
            "sha256": FROZEN_REVIEW_PACKAGE_BINDINGS[2][2],
        },
        "role_partition_human_authoritative": True,
        "role_partition_human_authoritative_event_count": 8,
        "human_selected": True,
        "machine_selected": False,
        "machine_auto_selection_performed": False,
        "machine_recommended_candidate": None,
    }


def _expected_raw_event(row: tuple[object, ...]) -> dict[str, object]:
    (
        event_id,
        rank,
        pdb_id,
        model_number,
        protein_chain,
        residue_id,
        protein_altloc,
        ligand_chain,
        ligand_altloc,
        connection,
        distance,
        distance_lexeme,
    ) = row
    return {
        "canonical_event_id": event_id,
        "scaleup_rank": rank,
        "pdb_id": pdb_id,
        "model_number": model_number,
        "protein_chain_or_asym": protein_chain,
        "cys_residue_id": residue_id,
        "protein_altloc": protein_altloc,
        "ligand_component_id": "2VS",
        "ligand_chain_or_asym": ligand_chain,
        "ligand_altloc": ligand_altloc,
        "selected_connection_id": connection,
        "POST_distance_angstrom": distance,
        "POST_distance_frozen_lexeme": distance_lexeme,
        "D1_human_task_relevance_decision": "RELEVANT",
        "D2_human_chemistry_support_disposition": "POSITIVE",
        "negative_chemistry": False,
        "task_domain_negative": False,
        "D3_human_reactive_pair_decision": "CONFIRM_OBSERVED_PAIR",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "CA6",
        "reactive_pair_human_authoritative": True,
        "D4_human_role_partition_choice": "SELECT_CANDIDATE_0",
        "selected_role_candidate_index_0based": 0,
        "role_partition_human_authoritative": True,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "D5_human_training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "human_training_excluded": True,
        "training_admitted": False,
        "D6_context_reference": "UNIT_LEVEL_HUMAN_APPROVED_CONTEXT",
        "event_specific_disposition_exception": False,
        "decision_finalized": True,
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
            "PRE_precursor_topology_authority_available": False,
            "PRE_precursor_reconstruction_performed": False,
            "observed_graph_is_authoritative_PRE_precursor_topology": False,
            "reaction_family_target_available": False,
            "warhead_rule_target_available": False,
            "warhead_type_target_available": False,
            "reusable_chemistry_authority_available": False,
            "reusable_pair_authority_available": False,
            "reusable_role_authority_available": False,
            "candidate_for_future_training_admission": False,
            "training_materialization_allowed_now": False,
            "current_runtime_model_usable": False,
            "model_bound_pair_target_created_by_ingestion": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_this_ingestion": False,
        }
    )
    return projected


def _validate_formal_decision_v1(formal: Mapping[str, Any]) -> dict[str, object]:
    expected_keys = {
        "schema_version", "record_role", "decision_status", "review_unit_id",
        "ligand_component_id", "exact_event_count", "unique_event_count",
        "duplicate_event_count", "omitted_event_count", "extra_event_count",
        "ranks", "pdb_ids", "canonical_event_ids", "reviewer_id", "attestor_id",
        "approved", "unsigned", "human_review_completed", "human_decision_created",
        "human_review_decision_created", "human_approval_recorded",
        "formal_authority_created", "human_approval", "evidence_provenance",
        "prior_review_state", "unit_level_human_decisions",
        "event_level_human_decisions", "reactive_pair_human_decision",
        "selected_role_partition", "human_approved_context",
        "observed_graph_pre_boundary", "geometry_boundary",
        "training_use_human_decision", "reaction_family_authority",
        "warhead_rule_authority", "warhead_type_authority",
        "reusable_authority_boundary", "authority_boundary", "downstream_status",
        "feature_semantics_status", "training_admitted", "ready_for_training",
    }
    if set(formal) != expected_keys:
        _fail("FORMAL_TOP_LEVEL_FIELD_SET_INVALID")

    expected_top = {
        "schema_version": FORMAL_DECISION_SCHEMA,
        "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "2VS",
        "exact_event_count": 8,
        "unique_event_count": 8,
        "duplicate_event_count": 0,
        "omitted_event_count": 0,
        "extra_event_count": 0,
        "ranks": list(EXPECTED_RANKS),
        "pdb_ids": ["4NPI", "4OUB"],
        "canonical_event_ids": list(EXPECTED_EVENT_IDS),
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved": True,
        "unsigned": False,
        "human_review_completed": True,
        "human_decision_created": True,
        "human_review_decision_created": True,
        "human_approval_recorded": True,
        "formal_authority_created": True,
        "feature_semantics_status": "AUDIT_REQUIRED_LATER",
        "training_admitted": False,
        "ready_for_training": False,
    }
    for field, expected in expected_top.items():
        if formal.get(field) != expected:
            _fail("FORMAL_TOP_LEVEL_SEMANTICS_INVALID:" + field)

    approval = formal.get("human_approval")
    if approval != _expected_human_approval():
        _fail("FORMAL_HUMAN_APPROVAL_FIELDS_INVALID")
    if formal.get("evidence_provenance") != _expected_evidence_provenance():
        _fail("FORMAL_EVIDENCE_PROVENANCE_DRIFT")
    prior_review_state = {
        "prior_review_status": "CURRENTLY_UNREVIEWED",
        "prior_review_inventory_status": (
            "CURRENTLY_UNREVIEWED_NO_PRIOR_2VS_REVIEW_WORK_FOUND"
        ),
        "prior_formal_human_decision_found": False,
        "prior_signed_human_decision_found": False,
        "prior_partial_authority_found": False,
        "prior_authority_source_paths": [],
        "current_authorization_source": "EXTERNAL_EXPLICIT_HUMAN_APPROVAL",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "current_human_decision": "FINALIZED_BY_CURRENT_EXPLICIT_HUMAN_AUTHORIZATION",
    }
    if formal.get("prior_review_state") != prior_review_state:
        _fail("FORMAL_PRIOR_REVIEW_STATE_INVALID")

    expected_unit = {
        "exact_event_count": 8,
        "completed_human_review_event_count": 8,
        "D1_task_relevance_decision": "RELEVANT",
        "task_relevant_event_count": 8,
        "D2_chemistry_support_disposition": "POSITIVE",
        "chemistry_positive_event_count": 8,
        "chemistry_negative_event_count": 0,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "D3_reactive_pair_decision": "CONFIRM_OBSERVED_PAIR",
        "reactive_pair_human_authoritative_event_count": 8,
        "D4_role_partition_decision": "SELECT_CANDIDATE_0",
        "role_partition_human_authoritative_event_count": 8,
        "D5_training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "human_training_excluded_positive_event_count": 8,
        "training_include_event_count": 0,
        "D6_context": EXPECTED_D6,
        "event_specific_disposition_exception_count": 0,
        "training_admission_created": False,
        "training_admitted_count": 0,
        "training_dataset_changed": False,
        "human_choices_externally_authorized": True,
        "machine_auto_selection_performed": False,
        "machine_recommended_candidate": None,
        "human_role_partition_choice": "SELECT_CANDIDATE_0",
    }
    if formal.get("unit_level_human_decisions") != expected_unit:
        _fail("FORMAL_UNIT_DECISION_SEMANTICS_INVALID")

    raw_events = formal.get("event_level_human_decisions")
    if type(raw_events) is not list or len(raw_events) != 8:
        _fail("FORMAL_EXACT8_EVENT_COUNT_INVALID")
    if any(type(event) is not dict for event in raw_events):
        _fail("FORMAL_EVENT_NOT_OBJECT")
    raw_ids = [event.get("canonical_event_id") for event in raw_events]
    if len(set(raw_ids)) != 8:
        _fail("FORMAL_EVENT_ID_DUPLICATE")
    if tuple(raw_ids) != EXPECTED_EVENT_IDS:
        _fail("FORMAL_EVENT_ID_COVERAGE_INVALID")
    expected_raw = [_expected_raw_event(row) for row in EXPECTED_EVENTS]
    for observed, expected in zip(raw_events, expected_raw, strict=True):
        if observed != expected:
            differing = sorted(
                key
                for key in set(observed) | set(expected)
                if observed.get(key) != expected.get(key)
            )
            _fail(
                "FORMAL_EVENT_SEMANTICS_INVALID:"
                + (differing[0] if differing else "schema")
            )

    expected_pair = {
        "D3_human_choice": "CONFIRM_OBSERVED_PAIR",
        "exact_event_count": 8,
        "protein_component_id": "CYS",
        "protein_residue_id": "302-",
        "protein_reactive_atom": "SG",
        "protein_endpoint": "CYS302 SG",
        "ligand_component_id": "2VS",
        "ligand_reactive_atom": "CA6",
        "ligand_endpoint": "2VS CA6",
        "human_authoritative_pair": "CYS302 SG ↔ 2VS CA6",
        "reactive_pair_human_authoritative": True,
        "reactive_pair_human_authoritative_event_count": 8,
        "reactive_pair_authority_scope": AUTHORITY_SCOPE,
        "model_bound_pair_integration_created": False,
        "tensor_target_created": False,
        "training_admission_created": False,
        "reusable_reactive_pair_authority_created": False,
    }
    if formal.get("reactive_pair_human_decision") != expected_pair:
        _fail("FORMAL_REACTIVE_PAIR_SEMANTICS_DRIFT")
    if formal.get("selected_role_partition") != _expected_formal_role_partition():
        _fail("FORMAL_SELECTED_ROLE_PARTITION_DRIFT")

    scaffold = set(EXPECTED_SCAFFOLD)
    linker = set(EXPECTED_LINKER)
    warhead = set(EXPECTED_WARHEAD)
    if scaffold & linker or scaffold & warhead or linker & warhead:
        _fail("2VS_ROLE_PARTITION_OVERLAP")
    if scaffold | linker | warhead != set(EXPECTED_HEAVY_ATOMS):
        _fail("2VS_ROLE_PARTITION_NOT_EXHAUSTIVE")

    scientific_context_text = (
        "2VS Exact8 represents observed covalent thioacyl enzyme-substrate "
        "intermediates of 2-aminomuconate-6-semialdehyde dehydrogenase (AMSDH). "
        "The reactive chemistry is the catalytic Cys302 attack at the aldehydic C6 "
        "center represented by the frozen 2VS CA6 atom. PDB 4NPI represents the "
        "wild-type thioacyl intermediate. PDB 4OUB represents the E268A mutant "
        "thioacyl intermediate. These structures arise from substrate turnover or "
        "catalytic intermediate trapping rather than a medicinal covalent-inhibitor "
        "design context. The frozen 2VS heavy-atom graph retains the aldehydic "
        "CA6=OA4 motif compatible with the observed reaction center. This human "
        "decision does not create authoritative PRE geometry or a reusable PRE "
        "precursor-topology contract. No event-specific disposition exception is "
        "applied. No reusable reaction-family, warhead-rule, warhead-type, "
        "PRE-geometry, cross-sample reusable chemistry, or training-admission "
        "authority is created."
    )
    expected_context = {
        "D6_exact_choice": EXPECTED_D6,
        "scope": HUMAN_CONTEXT_SCOPE,
        "human_approved_scientific_context": scientific_context_text,
        "pdb_context": {
            "4NPI": "WILD_TYPE_THIOACYL_INTERMEDIATE",
            "4OUB": "E268A_THIOACYL_INTERMEDIATE",
        },
        "medicinal_covalent_inhibitor_design_context": False,
        "event_specific_disposition_exception": False,
        "event_specific_disposition_exception_count": 0,
    }
    if formal.get("human_approved_context") != expected_context:
        _fail("FORMAL_SCIENTIFIC_CONTEXT_BOUNDARY_INVALID")

    observed_pre_boundary = {
        "observed_graph_identity": "2VS_FROZEN_OBSERVED_HEAVY_ATOM_GRAPH",
        "observed_reactive_motif": "CA6=OA4",
        "observed_reactive_motif_atoms": ["CA6", "OA4"],
        "observed_reactive_motif_bond_order": "DOUB",
        "observed_graph_is_authoritative_PRE_geometry": False,
        "observed_graph_is_authoritative_PRE_precursor_topology": False,
        "authoritative_PRE_precursor_topology": None,
        "PRE_precursor_topology_authority_created": False,
        "PRE_precursor_reconstruction_performed": False,
        "PRE_geometry_authority_created": False,
    }
    if formal.get("observed_graph_pre_boundary") != observed_pre_boundary:
        _fail("FORMAL_OBSERVED_GRAPH_PRE_BOUNDARY_INVALID")
    geometry_boundary = {
        "POST_evidence_provenance_preserved": True,
        "POST_geometry_status": "OBSERVED_POST_COVALENT_REVIEW_EVIDENCE",
        "POST_geometry_training_authority_created": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_geometry_status": "PRE_REACTION_UNRESOLVED",
        "PRE_geometry_authority_created": False,
        "PRE_geometry_training_target_created": False,
        "PRE_precursor_topology_authority_created": False,
        "PRE_zero_fill_performed": False,
        "PRE_coordinate_reconstruction_performed": False,
        "PRE_precursor_reconstruction_performed": False,
    }
    if formal.get("geometry_boundary") != geometry_boundary:
        _fail("FORMAL_GEOMETRY_BOUNDARY_INVALID")
    training_boundary = {
        "D5_human_choice": "EXCLUDE_FROM_TRAINING_ONLY",
        "exact_event_count": 8,
        "chemistry_positive_event_count": 8,
        "human_training_excluded_positive_event_count": 8,
        "training_include_event_count": 0,
        "training_admitted_count": 0,
        "training_exclusion_is_chemistry_negative": False,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "training_admission_created": False,
        "training_dataset_changed": False,
    }
    if formal.get("training_use_human_decision") != training_boundary:
        _fail("FORMAL_TRAINING_USE_SEMANTICS_INVALID")

    empty_authority = {
        "status": "NOT_CREATED",
        "authority_created": False,
        "authority_value": None,
    }
    for field in (
        "reaction_family_authority",
        "warhead_rule_authority",
        "warhead_type_authority",
    ):
        if formal.get(field) != empty_authority:
            _fail("FORMAL_AUXILIARY_AUTHORITY_INVALID:" + field)
    reusable_boundary = {
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "reusable_chemistry_authority_created": False,
        "reusable_reactive_pair_authority_created": False,
        "reusable_role_authority_created": False,
        "cross_sample_reusable_rule_created": False,
        "aldehyde_reusable_warhead_rule_created": False,
        "AMSDH_reusable_reaction_family_authority_created": False,
    }
    if formal.get("reusable_authority_boundary") != reusable_boundary:
        _fail("FORMAL_REUSABLE_AUTHORITY_BOUNDARY_INVALID")
    if formal.get("authority_boundary") != _formal_authority_boundary():
        _fail("FORMAL_AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    if formal.get("downstream_status") != {
        "formal_human_decision_created": True,
        "completed_decision_ingestion": "NOT_DONE",
        "global_reconciliation_update": "NOT_DONE",
        "global_census_update": "NOT_DONE",
        "training": "NOT_STARTED",
    }:
        _fail("FORMAL_DOWNSTREAM_STATUS_INVALID")

    # This canonicalized digest covers every nested lexeme-independent JSON
    # semantic field, complementing the exact file-byte binding above.
    if _sha(_json_bytes(dict(formal))) != FORMAL_SEMANTIC_CANONICAL_SHA256:
        _fail("FORMAL_COMPLETE_NESTED_SEMANTIC_DIGEST_INVALID")
    return {
        "approval": dict(approval),
        "events": [_event_projection(event) for event in expected_raw],
        "role": _role_snapshot(),
        "scientific_context": expected_context,
        "observed_graph_pre_boundary": observed_pre_boundary,
        "geometry_boundary": geometry_boundary,
        "formal_authority_boundary": _formal_authority_boundary(),
        "prior_review_state": prior_review_state,
    }


def _semantic_owner_bindings(
    repo_root: Path, overrides: Mapping[Path, Path]
) -> tuple[list[dict[str, object]], dict[str, object]]:
    bindings: list[dict[str, object]] = []
    for relative, byte_count, sha256, role in IMMUTABLE_SEMANTIC_OWNER_BINDINGS:
        payload = _verify_payload(
            overrides.get(relative, repo_root / relative),
            byte_count,
            sha256,
            role,
        )
        bindings.append(
            {
                "path": relative.as_posix(),
                "path_namespace": "repository_relative",
                "byte_count": len(payload),
                "sha256": _sha(payload),
                "sha256_scope": "file_bytes",
                "source_role": role,
                "verification_status": "MATCHED",
            }
        )
    runtime_values = _literal_assignments(
        overrides.get(RUNTIME_SOURCE_RELATIVE, repo_root / RUNTIME_SOURCE_RELATIVE),
        (
            "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "DIRECT_VALID_CANONICAL_TASK_IDS_V1",
            "DIRECT_PROFILE_TASK_APPLICABILITY_V1",
            "CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1",
            "DIRECT_PROFILE_RUNTIME_PRIMITIVES_READY_V1",
            "EXPANDED_TENSORIZER_INTEGRATION_PENDING_V1",
            "MODEL_ARCHITECTURE_CHANGE_REQUIRED_V1",
        ),
    )
    canonical_values = _literal_assignments(
        overrides.get(
            CANONICAL_TASK_SOURCE_RELATIVE,
            repo_root / CANONICAL_TASK_SOURCE_RELATIVE,
        ),
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
    )
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
    if (
        canonical_values.get("EXACT3_ROLES")
        != ("scaffold", "linker", "warhead")
        or canonical_values.get("CANONICAL_TASKS") != CANONICAL_TASKS
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")
    for field, expected in expected_runtime.items():
        if runtime_values.get(field) != expected:
            _fail("DIRECT_PROFILE_RUNTIME_CONTRACT_DRIFT:" + field)
    return bindings, _runtime_contract()


def _frozen_review_bindings(
    repository_parent: Path, overrides: Mapping[Path, Path]
) -> list[dict[str, object]]:
    for relative, byte_count, sha256, role, _mode in FROZEN_REVIEW_PACKAGE_BINDINGS:
        _verify_payload(
            overrides.get(relative, repository_parent / relative),
            byte_count,
            sha256,
            role,
        )
    return _expected_evidence_provenance()


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Load and strictly validate the formal decision and every bound source."""

    repo_root = repo_root.resolve()
    overrides = repository_path_overrides or {}
    formal_path = (
        formal_decision_path.resolve()
        if formal_decision_path is not None
        else repo_root.parent / FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
    )
    payload = _verify_payload(
        formal_path,
        FORMAL_DECISION_BYTE_COUNT,
        FORMAL_DECISION_SHA256,
        "formal_2VS_human_decision",
    )
    try:
        formal = json.loads(payload)
    except json.JSONDecodeError as error:
        raise TwoVSIngestionSafetyError("FORMAL_DECISION_JSON_INVALID") from error
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
        "selected_candidate_index_0based": 0,
        "selected_candidate_id": EXPECTED_CANDIDATE_ID,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "exact_heavy_atom_count": 10,
        "exact_heavy_atom_ids": list(EXPECTED_HEAVY_ATOMS),
        "warhead_atoms": list(EXPECTED_WARHEAD),
        "linker_atoms": [],
        "scaffold_atoms": list(EXPECTED_SCAFFOLD),
        "boundary_bonds": [
            {
                "atom_id_1": "CA5",
                "atom_id_2": "CA6",
                "bond_order": "SING",
                "boundary_between_roles": ["scaffold", "warhead"],
            }
        ],
        "heavy_atom_disjoint": True,
        "heavy_atom_exhaustive": True,
        "warhead_connected": True,
        "linker_empty": True,
        "scaffold_connected": True,
        "sample_level_role_decision_exists_in_source": True,
        "sample_level_role_decision_created_by_ingestion": False,
        "machine_selected": False,
        "machine_recommended_candidate": None,
    }


def _canonical_task_contract() -> dict[str, object]:
    applicability = []
    for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS:
        applicability.append(
            {
                "task_id": task_id,
                "semantic_long_name": semantic,
                "display_alias": alias,
                "structurally_applicable": task_id in DIRECT_VALID_TASK_IDS,
                "role_profile": EXPECTED_ROLE_PROFILE,
            }
        )
    return {
        "global_canonical_tasks": [
            {
                "task_id": task_id,
                "semantic_long_name": semantic,
                "display_alias": alias,
                "generated_roles": list(generated),
                "fixed_or_seed_roles": list(fixed),
            }
            for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_created": False,
        "canonical_task_vocabulary_changed": False,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "direct_profile_applicable_task_count": 3,
        "direct_profile_task_applicability": applicability,
    }


def _runtime_contract() -> dict[str, object]:
    return {
        "role_profile": EXPECTED_ROLE_PROFILE,
        "direct_valid_canonical_task_ids": [0, 3, 4],
        "current11_tensorizer_direct_profile_supported": False,
        "direct_profile_runtime_primitives_ready": True,
        "expanded_tensorizer_integration_pending": True,
        "model_architecture_change_required": False,
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "formal_human_decision_modified": False,
        "sample_level_human_authority_created_by_ingestion": False,
        "sample_level_human_authority_ingested": True,
        "snapshot_created_by_ingestion": True,
        "current_global_review_status_updated_by_ingestion": False,
        "new_reusable_authority_created": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "reusable_reactive_pair_authority_created": False,
        "reusable_role_authority_created": False,
        "PRE_geometry_authority_created": False,
        "PRE_precursor_topology_authority_created": False,
        "PRE_precursor_reconstruction_performed": False,
        "PRE_coordinate_reconstruction_performed": False,
        "POST_geometry_training_authority_created": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_zero_fill_performed": False,
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
    normalized = bound["normalized"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_role": "ADDITIVE_IMMUTABLE_2VS_COMPLETED_HUMAN_DECISION_INGESTION",
        "snapshot_created_by_ingestion": True,
        "human_authority_created_by_ingestion": False,
        "human_authority_ingested": True,
        "formal_decision_binding": bound["formal_decision_binding"],
        "frozen_formal_evidence_provenance": bound[
            "frozen_review_package_bindings"
        ],
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "2VS",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "formal_prior_review_status": "CURRENTLY_UNREVIEWED",
        "formal_prior_review_inventory_status": (
            "CURRENTLY_UNREVIEWED_NO_PRIOR_2VS_REVIEW_WORK_FOUND"
        ),
        "current_global_review_status_updated_by_ingestion": False,
        "authority_provenance": {
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_ingestion": False,
            "sample_level_human_authority_exists_in_source": True,
            "sample_level_human_authority_created_by_ingestion": False,
        },
        "unit_level_D1_D6": {
            "D1": "RELEVANT",
            "D2": "POSITIVE",
            "D3": "CONFIRM_OBSERVED_PAIR",
            "D4": "SELECT_CANDIDATE_0",
            "D5": "EXCLUDE_FROM_TRAINING_ONLY",
            "D6": EXPECTED_D6,
        },
        "events": normalized["events"],
        "reactive_pair": {
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CA6",
            "human_decision_available": True,
            "human_authoritative": True,
            "human_authority_event_count": 8,
            "human_authority_created_by_ingestion": False,
            "model_bound_pair_target_created_by_ingestion": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "reusable_reactive_pair_authority": False,
        },
        "selected_role_partition": normalized["role"],
        "canonical_task_contract": _canonical_task_contract(),
        "direct_profile_runtime_contract": bound["runtime_contract"],
        "scientific_context": normalized["scientific_context"],
        "observed_graph_PRE_boundary": normalized[
            "observed_graph_pre_boundary"
        ],
        "geometry_boundary": {
            "POST_source_evidence_count": 8,
            "POST_geometry_training_authority_count": 0,
            "POST_geometry_training_label_available_now": False,
            "PRE_geometry_status": "PRE_REACTION_UNRESOLVED",
            "PRE_geometry_authority_count": 0,
            "PRE_geometry_training_target_count": 0,
            "PRE_precursor_topology_authority_count": 0,
            "POST_to_PRE_copy_performed": False,
            "PRE_zero_fill_performed": False,
            "PRE_coordinate_reconstruction_performed": False,
            "observed_graph_is_authoritative_PRE_geometry": False,
            "observed_graph_is_authoritative_PRE_precursor_topology": False,
            "PRE_precursor_reconstruction_performed": False,
        },
        "reusable_authority_boundary": {
            "reaction_family_target_available": False,
            "reaction_family_target_count": 0,
            "warhead_rule_target_available": False,
            "warhead_rule_target_count": 0,
            "warhead_type_target_available": False,
            "warhead_type_target_count": 0,
            "reusable_chemistry_authority_available": False,
            "reusable_pair_authority_available": False,
            "reusable_role_authority_available": False,
            "new_reusable_authority_created": False,
        },
        "training_boundary": {
            "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
            "chemistry_positive_count": 8,
            "training_excluded_positive_count": 8,
            "training_include_count": 0,
            "candidate_for_future_training_admission_count": 0,
            "training_admitted_count": 0,
            "training_materialization_allowed_count": 0,
            "current_runtime_model_usable_count": 0,
            "ready_for_training": False,
            "feature_semantics": "AUDIT_REQUIRED_LATER",
        },
        "downstream_non_actions": {
            "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
            "global_census_update_status": "NOT_DONE_THIS_STEP",
            "tensorization_status": "NOT_DONE_THIS_STEP",
            "training_status": "NOT_DONE_THIS_STEP",
        },
        "authority_boundary": _authority_boundary(),
        "formal_authority_boundary_source": normalized[
            "formal_authority_boundary"
        ],
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "pdb_id", "model_number",
    "protein_chain_or_asym", "cys_residue_id", "protein_altloc",
    "ligand_chain_or_asym", "ligand_altloc", "selected_connection_id",
    "POST_distance_angstrom", "POST_distance_frozen_lexeme",
    "human_task_relevance_decision", "chemistry_known_positive",
    "negative_chemistry", "task_domain_negative",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "protein_reactive_atom", "ligand_reactive_atom",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "selected_role_candidate_index_0based", "role_profile", "warhead_atoms_json",
    "linker_atoms_json", "scaffold_atoms_json", "boundary_bonds_json",
    "global_canonical_task_count", "canonical_task_applicability_json",
    "direct_profile_applicable_task_ids_json", "formal_event_training_use_decision",
    "human_training_excluded", "training_use_allowed",
    "POST_source_evidence_available", "POST_geometry_training_label_available_now",
    "PRE_geometry_authority_available", "PRE_geometry_training_label_available_now",
    "PRE_precursor_topology_authority_available",
    "PRE_precursor_reconstruction_performed",
    "observed_graph_is_authoritative_PRE_precursor_topology",
    "reaction_family_target_available", "warhead_rule_target_available",
    "warhead_type_target_available", "candidate_for_future_training_admission",
    "training_admitted", "training_materialization_allowed_now",
    "current_runtime_model_usable", "authority_source", "authority_ingested",
    "authority_created_by_this_ingestion",
)


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    role = _role_snapshot()
    boundary = _json_cell(role["boundary_bonds"])
    applicability = _json_cell(
        _canonical_task_contract()["direct_profile_task_applicability"]
    )
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        rows.append(
            {
                "canonical_event_id": event["canonical_event_id"],
                "scaleup_rank": str(event["scaleup_rank"]),
                "pdb_id": event["pdb_id"],
                "model_number": str(event["model_number"]),
                "protein_chain_or_asym": event["protein_chain_or_asym"],
                "cys_residue_id": event["cys_residue_id"],
                "protein_altloc": "" if event["protein_altloc"] is None else event["protein_altloc"],
                "ligand_chain_or_asym": event["ligand_chain_or_asym"],
                "ligand_altloc": "" if event["ligand_altloc"] is None else event["ligand_altloc"],
                "selected_connection_id": event["selected_connection_id"],
                "POST_distance_angstrom": str(event["POST_distance_angstrom"]),
                "POST_distance_frozen_lexeme": event["POST_distance_frozen_lexeme"],
                "human_task_relevance_decision": "RELEVANT",
                "chemistry_known_positive": "true",
                "negative_chemistry": "false",
                "task_domain_negative": "false",
                "reactive_pair_human_decision_available": "true",
                "reactive_pair_human_authoritative": "true",
                "protein_reactive_atom": "SG",
                "ligand_reactive_atom": "CA6",
                "role_partition_human_decision_available": "true",
                "role_partition_human_authoritative": "true",
                "selected_role_candidate_index_0based": "0",
                "role_profile": EXPECTED_ROLE_PROFILE,
                "warhead_atoms_json": _json_cell(list(EXPECTED_WARHEAD)),
                "linker_atoms_json": "[]",
                "scaffold_atoms_json": _json_cell(list(EXPECTED_SCAFFOLD)),
                "boundary_bonds_json": boundary,
                "global_canonical_task_count": "5",
                "canonical_task_applicability_json": applicability,
                "direct_profile_applicable_task_ids_json": "[0,3,4]",
                "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
                "human_training_excluded": "true",
                "training_use_allowed": "false",
                "POST_source_evidence_available": "true",
                "POST_geometry_training_label_available_now": "false",
                "PRE_geometry_authority_available": "false",
                "PRE_geometry_training_label_available_now": "false",
                "PRE_precursor_topology_authority_available": "false",
                "PRE_precursor_reconstruction_performed": "false",
                "observed_graph_is_authoritative_PRE_precursor_topology": "false",
                "reaction_family_target_available": "false",
                "warhead_rule_target_available": "false",
                "warhead_type_target_available": "false",
                "candidate_for_future_training_admission": "false",
                "training_admitted": "false",
                "training_materialization_allowed_now": "false",
                "current_runtime_model_usable": "false",
                "authority_source": AUTHORITY_SOURCE,
                "authority_ingested": "true",
                "authority_created_by_this_ingestion": "false",
            }
        )
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "event_count": 8,
        "task_relevant_count": 8,
        "chemistry_positive_count": 8,
        "2VS_source_local_positive_count": 8,
        "source_local_positive_count": 8,
        "completed_human_positive_count": 8,
        "reactive_pair_human_authority_count": 8,
        "role_partition_human_authority_count": 8,
        "direct_profile_count": 8,
        "strict_profile_count": 0,
        "global_canonical_task_count": 5,
        "direct_profile_applicable_task_count_per_event": 3,
        "POST_source_evidence_count": 8,
        "POST_geometry_training_authority_count": 0,
        "PRE_geometry_authority_count": 0,
        "PRE_geometry_training_target_count": 0,
        "PRE_precursor_topology_authority_count": 0,
        "reaction_family_target_count": 0,
        "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
        "training_excluded_positive_count": 8,
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
        "published_global_positive_count_remains": 66,
        "ready_for_2VS_reconciliation_successor": True,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "authority_boundary": _authority_boundary(),
    }


def _validate_text_payload(label: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail("TEXT_INVARIANT_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise TwoVSIngestionSafetyError("UTF8_INVALID:" + label) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TRAILING_WHITESPACE_INVALID:" + label)


def _candidate_source_bindings(repo_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative, role in (
        (SOURCE_RELATIVE, "production_owner"),
        (CHECKER_RELATIVE, "fail_closed_checker"),
        (TEST_RELATIVE, "targeted_test_contract"),
    ):
        path = repo_root / relative
        if not path.is_file() or path.is_symlink():
            _fail("CANDIDATE_SOURCE_NOT_REGULAR:" + relative.as_posix())
        payload = path.read_bytes()
        _validate_text_payload(relative.as_posix(), payload)
        rows.append(
            {
                "path": relative.as_posix(),
                "path_namespace": "repository_relative",
                "byte_count": len(payload),
                "sha256": _sha(payload),
                "sha256_scope": "file_bytes",
                "source_role": role,
            }
        )
    return rows


def _standalone_owner_bindings() -> list[dict[str, object]]:
    return [
        {
            "path": relative.as_posix(),
            "path_namespace": "repository_relative",
            "byte_count": byte_count,
            "sha256": sha256,
            "sha256_scope": "file_bytes",
            "source_role": role,
            "verification_status": "MATCHED",
        }
        for relative, byte_count, sha256, role in IMMUTABLE_SEMANTIC_OWNER_BINDINGS
    ]


def _standalone_bound() -> dict[str, object]:
    scientific_context_text = (
        "2VS Exact8 represents observed covalent thioacyl enzyme-substrate "
        "intermediates of 2-aminomuconate-6-semialdehyde dehydrogenase (AMSDH). "
        "The reactive chemistry is the catalytic Cys302 attack at the aldehydic C6 "
        "center represented by the frozen 2VS CA6 atom. PDB 4NPI represents the "
        "wild-type thioacyl intermediate. PDB 4OUB represents the E268A mutant "
        "thioacyl intermediate. These structures arise from substrate turnover or "
        "catalytic intermediate trapping rather than a medicinal covalent-inhibitor "
        "design context. The frozen 2VS heavy-atom graph retains the aldehydic "
        "CA6=OA4 motif compatible with the observed reaction center. This human "
        "decision does not create authoritative PRE geometry or a reusable PRE "
        "precursor-topology contract. No event-specific disposition exception is "
        "applied. No reusable reaction-family, warhead-rule, warhead-type, "
        "PRE-geometry, cross-sample reusable chemistry, or training-admission "
        "authority is created."
    )
    return {
        "formal_decision_binding": _formal_binding(),
        "frozen_review_package_bindings": _expected_evidence_provenance(),
        "runtime_contract": _runtime_contract(),
        "normalized": {
            "events": [
                _event_projection(_expected_raw_event(row)) for row in EXPECTED_EVENTS
            ],
            "role": _role_snapshot(),
            "scientific_context": {
                "D6_exact_choice": EXPECTED_D6,
                "scope": HUMAN_CONTEXT_SCOPE,
                "human_approved_scientific_context": scientific_context_text,
                "pdb_context": {
                    "4NPI": "WILD_TYPE_THIOACYL_INTERMEDIATE",
                    "4OUB": "E268A_THIOACYL_INTERMEDIATE",
                },
                "medicinal_covalent_inhibitor_design_context": False,
                "event_specific_disposition_exception": False,
                "event_specific_disposition_exception_count": 0,
            },
            "observed_graph_pre_boundary": {
                "observed_graph_identity": "2VS_FROZEN_OBSERVED_HEAVY_ATOM_GRAPH",
                "observed_reactive_motif": "CA6=OA4",
                "observed_reactive_motif_atoms": ["CA6", "OA4"],
                "observed_reactive_motif_bond_order": "DOUB",
                "observed_graph_is_authoritative_PRE_geometry": False,
                "observed_graph_is_authoritative_PRE_precursor_topology": False,
                "authoritative_PRE_precursor_topology": None,
                "PRE_precursor_topology_authority_created": False,
                "PRE_precursor_reconstruction_performed": False,
                "PRE_geometry_authority_created": False,
            },
            "formal_authority_boundary": _formal_authority_boundary(),
        },
    }


def build_artifacts_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Build the deterministic Exact4 source projection in memory."""

    repo_root = repo_root.resolve()
    bound = load_frozen_formal_decision_v1(
        repo_root,
        formal_decision_path=formal_decision_path,
        repository_path_overrides=repository_path_overrides,
    )
    snapshot = _snapshot(bound)
    snapshot_payload = _json_bytes(snapshot)
    matrix_payload = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    summary_payload = _json_bytes(_summary())
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "2VS_COMPLETED_DECISION_AND_EVENT_TASK_LABEL_AVAILABILITY_NOT_ADMISSION",
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "frozen_formal_evidence_provenance": bound[
            "frozen_review_package_bindings"
        ],
        "immutable_semantic_owner_bindings": bound[
            "immutable_semantic_owner_bindings"
        ],
        "candidate_source_bindings": _candidate_source_bindings(repo_root),
        "canonical_task_contract": _canonical_task_contract(),
        "counts": {
            key: value
            for key, value in _summary().items()
            if type(value) is int and type(value) is not bool
        },
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
        "published_global_positive_count_remains": 66,
        "feature_semantics_audit_required_before_formal_training": True,
        "ready_for_2VS_reconciliation_successor": True,
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
    forbidden = {
        "generated_at", "generated_at_utc", "ingested_at", "ingested_at_utc",
        "hostname", "host_name", "pid", "process_id", "uuid", "git_head",
        "git_parent", "commit_subject", "origin_main", "ahead", "behind",
        "candidate_lifecycle_profile", "published_lifecycle_profile",
    }
    if type(value) is dict:
        for key, child in value.items():
            if key in forbidden:
                _fail("DYNAMIC_OR_LIFECYCLE_METADATA_FORBIDDEN:" + key)
            _reject_dynamic_metadata(child)
    elif type(value) is list:
        for child in value:
            _reject_dynamic_metadata(child)


def _validate_candidate_bindings_shape(value: object) -> None:
    if type(value) is not list or len(value) != 3:
        _fail("MANIFEST_CANDIDATE_SOURCE_BINDING_COUNT_INVALID")
    expected = (
        (SOURCE_RELATIVE.as_posix(), "production_owner"),
        (CHECKER_RELATIVE.as_posix(), "fail_closed_checker"),
        (TEST_RELATIVE.as_posix(), "targeted_test_contract"),
    )
    for observed, (path, role) in zip(value, expected, strict=True):
        if type(observed) is not dict or set(observed) != {
            "path", "path_namespace", "byte_count", "sha256", "sha256_scope",
            "source_role",
        }:
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDING_SCHEMA_INVALID")
        if (
            observed["path"] != path
            or observed["path_namespace"] != "repository_relative"
            or type(observed["byte_count"]) is not int
            or observed["byte_count"] <= 0
            or type(observed["sha256"]) is not str
            or len(observed["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in observed["sha256"])
            or observed["sha256_scope"] != "file_bytes"
            or observed["source_role"] != role
        ):
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDING_INVALID:" + path)


def _validate_derived_projection_digests(artifacts: Mapping[str, bytes]) -> None:
    expected = (
        (SNAPSHOT, _EXPECTED_SNAPSHOT_SHA256_V1),
        (MATRIX, _EXPECTED_MATRIX_SHA256_V1),
        (SUMMARY, _EXPECTED_SUMMARY_SHA256_V1),
    )
    for name, digest in expected:
        if (
            len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or digest == "0" * 64
        ):
            _fail("DERIVED_PROJECTION_CONTRACT_DIGEST_NOT_FROZEN:" + name)
        if _sha(artifacts[name]) != digest:
            _fail(name.upper() + "_EXACT_PROJECTION_SHA256_INVALID")


def validate_completed_decision_projection_v1(
    artifacts: Mapping[str, bytes], *, repo_root: Path | None = None
) -> None:
    """Validate Exact4 direct evidence, including standalone coordinated drift."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    try:
        snapshot = json.loads(artifacts[SNAPSHOT])
        summary = json.loads(artifacts[SUMMARY])
        manifest = json.loads(artifacts[MANIFEST])
        matrix = list(
            csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8")))
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise TwoVSIngestionSafetyError("OUTPUT_PARSE_FAILED") from error
    for document in (snapshot, summary, manifest):
        _reject_dynamic_metadata(document)

    if summary != _summary():
        _fail("SUMMARY_EXACT_COUNTS_OR_BOUNDARY_INVALID")
    standalone_bound = _standalone_bound()
    if snapshot != _snapshot(standalone_bound):
        _fail("SNAPSHOT_EXACT_SOURCE_PROJECTION_INVALID")
    events = snapshot["events"]
    if (
        len(events) != 8
        or tuple(event["canonical_event_id"] for event in events)
        != EXPECTED_EVENT_IDS
        or [event["scaleup_rank"] for event in events] != list(EXPECTED_RANKS)
        or len({event["canonical_event_id"] for event in events}) != 8
    ):
        _fail("SNAPSHOT_EXACT8_COVERAGE_INVALID")
    if snapshot["selected_role_partition"] != _role_snapshot():
        _fail("SNAPSHOT_CANDIDATE0_ROLE_CONTRACT_INVALID")
    if snapshot["canonical_task_contract"] != _canonical_task_contract():
        _fail("SNAPSHOT_GLOBAL_EXACT5_CONTRACT_INVALID")
    if snapshot["authority_boundary"] != _authority_boundary():
        _fail("SNAPSHOT_AUTHORITY_BOUNDARY_INVALID")

    if (list(matrix[0].keys()) if matrix else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    if (
        len(matrix) != 8
        or tuple(row["canonical_event_id"] for row in matrix) != EXPECTED_EVENT_IDS
        or len({row["canonical_event_id"] for row in matrix}) != 8
        or [int(row["scaleup_rank"]) for row in matrix] != list(EXPECTED_RANKS)
    ):
        _fail("MATRIX_EXACT8_INVALID")
    if artifacts[MATRIX] != _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot)):
        _fail("MATRIX_DIRECT_EVIDENCE_INVALID")
    true_fields = (
        "chemistry_known_positive", "reactive_pair_human_decision_available",
        "reactive_pair_human_authoritative", "role_partition_human_decision_available",
        "role_partition_human_authoritative", "human_training_excluded",
        "POST_source_evidence_available", "authority_ingested",
    )
    false_fields = (
        "negative_chemistry", "task_domain_negative", "training_use_allowed",
        "POST_geometry_training_label_available_now", "PRE_geometry_authority_available",
        "PRE_geometry_training_label_available_now",
        "PRE_precursor_topology_authority_available",
        "PRE_precursor_reconstruction_performed",
        "observed_graph_is_authoritative_PRE_precursor_topology",
        "reaction_family_target_available", "warhead_rule_target_available",
        "warhead_type_target_available", "candidate_for_future_training_admission",
        "training_admitted", "training_materialization_allowed_now",
        "current_runtime_model_usable", "authority_created_by_this_ingestion",
    )
    for index, row in enumerate(matrix):
        for field in true_fields:
            if row[field] != "true":
                _fail("MATRIX_REQUIRED_AUTHORITY_UNAVAILABLE:" + field)
        for field in false_fields:
            if row[field] != "false":
                _fail("MATRIX_SAFETY_FLAG_INVALID:" + field)
        expected_event = EXPECTED_EVENTS[index]
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["model_number"] != "1"
            or row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "CA6"
            or row["selected_role_candidate_index_0based"] != "0"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or row["POST_distance_angstrom"] != str(expected_event[10])
            or row["POST_distance_frozen_lexeme"] != expected_event[11]
            or row["global_canonical_task_count"] != "5"
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or len(applicability) != 5
            or [item["task_id"] for item in applicability if item["structurally_applicable"]]
            != [0, 3, 4]
            or applicability[3]["semantic_long_name"] != "scaffold_only"
        ):
            _fail("MATRIX_PROVENANCE_CANDIDATE0_OR_EXACT5_INVALID")

    expected_manifest_keys = {
        "schema_version", "stage", "artifact_role",
        "candidate_publication_file_count", "output_artifact_count", "source_path",
        "checker_path", "test_path", "output_paths", "formal_decision_binding",
        "frozen_formal_evidence_provenance", "immutable_semantic_owner_bindings",
        "candidate_source_bindings", "canonical_task_contract", "counts",
        "human_authority_ingestion_semantics", "output_artifact_bindings",
        "manifest_self_sha256_recorded", "manifest_self_sha256_policy",
        "deterministic", "completed_decision_ingestion_status",
        "global_reconciliation_update_status", "global_census_update_status",
        "published_global_positive_count_remains",
        "feature_semantics_audit_required_before_formal_training",
        "ready_for_2VS_reconciliation_successor", "ready_for_training",
        "authority_boundary",
    }
    if type(manifest) is not dict or set(manifest) != expected_manifest_keys:
        _fail("MANIFEST_SCHEMA_INVALID")
    if (
        manifest["schema_version"] != MANIFEST_SCHEMA_VERSION
        or manifest["stage"] != SCHEMA_VERSION
        or manifest["artifact_role"]
        != "2VS_COMPLETED_DECISION_AND_EVENT_TASK_LABEL_AVAILABILITY_NOT_ADMISSION"
        or manifest["candidate_publication_file_count"] != 7
        or manifest["output_artifact_count"] != 4
        or manifest["source_path"] != SOURCE_RELATIVE.as_posix()
        or manifest["checker_path"] != CHECKER_RELATIVE.as_posix()
        or manifest["test_path"] != TEST_RELATIVE.as_posix()
        or manifest["output_paths"]
        != [path.as_posix() for path in OUTPUT_RELATIVE_PATHS]
        or manifest["formal_decision_binding"] != _formal_binding()
        or manifest["frozen_formal_evidence_provenance"]
        != _expected_evidence_provenance()
        or manifest["immutable_semantic_owner_bindings"]
        != _standalone_owner_bindings()
        or manifest["canonical_task_contract"] != _canonical_task_contract()
        or manifest["authority_boundary"] != _authority_boundary()
        or manifest["manifest_self_sha256_recorded"] is not False
        or manifest["manifest_self_sha256_policy"] != "SELF_SHA256_PROHIBITED"
        or manifest["deterministic"] is not True
        or manifest["completed_decision_ingestion_status"] != "DONE_THIS_STEP"
        or manifest["global_reconciliation_update_status"] != "NOT_DONE_THIS_STEP"
        or manifest["global_census_update_status"] != "NOT_DONE_THIS_STEP"
        or manifest["published_global_positive_count_remains"] != 66
        or manifest["feature_semantics_audit_required_before_formal_training"] is not True
        or manifest["ready_for_2VS_reconciliation_successor"] is not True
        or manifest["ready_for_training"] is not False
    ):
        _fail("MANIFEST_BOUNDARY_OR_SOURCE_BINDING_INVALID")
    _validate_candidate_bindings_shape(manifest["candidate_source_bindings"])
    if manifest["output_artifact_bindings"] != {
        SNAPSHOT: {"sha256": _sha(artifacts[SNAPSHOT])},
        MATRIX: {"sha256": _sha(artifacts[MATRIX])},
        SUMMARY: {"sha256": _sha(artifacts[SUMMARY])},
    }:
        _fail("MANIFEST_OUTPUT_BINDINGS_INVALID")
    if manifest["counts"] != {
        key: value
        for key, value in _summary().items()
        if type(value) is int and type(value) is not bool
    }:
        _fail("MANIFEST_COUNTS_INVALID")
    if manifest["human_authority_ingestion_semantics"] != {
        "authority_source": AUTHORITY_SOURCE,
        "authority_scope": AUTHORITY_SCOPE,
        "authority_ingested": True,
        "authority_created_by_ingestion": False,
        "sample_level_human_authority_exists_in_source": True,
    }:
        _fail("MANIFEST_HUMAN_AUTHORITY_BOUNDARY_INVALID")

    _validate_derived_projection_digests(artifacts)
    if repo_root is not None:
        repo_root = repo_root.resolve()
        bound = load_frozen_formal_decision_v1(repo_root)
        if snapshot != _snapshot(bound):
            _fail("SNAPSHOT_DIRECT_FORMAL_SOURCE_PROJECTION_INVALID")
        if manifest["candidate_source_bindings"] != _candidate_source_bindings(repo_root):
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDINGS_INVALID")
        if (
            manifest["frozen_formal_evidence_provenance"]
            != bound["frozen_review_package_bindings"]
            or manifest["immutable_semantic_owner_bindings"]
            != bound["immutable_semantic_owner_bindings"]
        ):
            _fail("MANIFEST_FROZEN_SOURCE_BINDINGS_INVALID")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_artifacts_v1(
    repo_root: Path, *, output_root: Path | None = None
) -> dict[str, bytes]:
    """Build and atomically materialize only the Exact4 outputs."""

    repo_root = repo_root.resolve()
    artifacts = build_artifacts_v1(repo_root)
    destination = (
        output_root.resolve()
        if output_root is not None
        else repo_root / OUTPUT_ROOT_RELATIVE
    )
    if destination.exists():
        unexpected = {
            path.name
            for path in destination.iterdir()
            if path.name not in OUTPUT_FILENAMES
        }
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
        "artifact_sha256": {
            name: _sha(observed[name]) for name in OUTPUT_FILENAMES
        },
        "formal_decision_sha256": FORMAL_DECISION_SHA256,
        "event_count": 8,
        "chemistry_positive_count": 8,
        "training_excluded_positive_count": 8,
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
    print("event_count=8")
    print("chemistry_positive_count=8")
    print("training_excluded_positive_count=8")
    print("training_include_count=0")
    print("training_admitted_count=0")
    print("published_global_positive_count_remains=66")
    print("ready_for_training=false")
    for name in OUTPUT_FILENAMES:
        print(name + "_sha256=" + _sha(artifacts[name]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
