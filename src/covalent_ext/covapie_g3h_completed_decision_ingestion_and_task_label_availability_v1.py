"""Compile the additive G3H completed-decision ingestion successor V1.

This metadata-only owner reads an exactly bound formal G3H human decision,
validates its already-created sample-level authority, and deterministically
projects that authority into a frozen snapshot and an event label-availability
matrix.  It does not create or reinterpret human, chemistry, reusable, role,
reaction-family, warhead-rule, warhead-type, geometry-training, training-use,
or training-admission authority.  It does not mutate review preparation,
formal decisions, reconciliation, splits, datasets, tensors, loaders, models,
forward/loss paths, optimizers, or parameters, and it performs no download.
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


SCHEMA_VERSION = (
    "covapie_g3h_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT_SCHEMA_VERSION = "covapie_g3h_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_g3h_event_task_label_availability_v1"
MANIFEST_SCHEMA_VERSION = "covapie_g3h_completed_decision_ingestion_manifest_v1"
SUMMARY_SCHEMA_VERSION = "covapie_g3h_completed_decision_ingestion_summary_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_g3h_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_g3h_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_g3h_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_g3h_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_g3h_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_g3h_event_task_label_availability_v1.csv"
MANIFEST = "covapie_g3h_completed_decision_ingestion_manifest_v1.json"
SUMMARY = "covapie_g3h_completed_decision_ingestion_summary_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, MANIFEST, SUMMARY)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "G3H_COVAPIE_BULK_REVIEW_UNIT_5C788252BB9BA078/"
    "formal-human-decision-v1/g3h_formal_human_decision_v1.json"
)
FORMAL_DECISION_BYTE_COUNT = 22456
FORMAL_DECISION_SHA256 = (
    "872ac01500180f752928aeb2fb44287b7fa9cad7070e1b17a45f0d19b25d5203"
)
FORMAL_DECISION_SCHEMA = "covapie_g3h_formal_human_decision_v1"
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_5C788252BB9BA078"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
EXPECTED_COMPLETED_LANE = (
    "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
)
EXPECTED_EVENT_IDS = (
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:A:CYS:291-:SG:I:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:B:CYS:291-:SG:K:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:C:CYS:291-:SG:M:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:D:CYS:291-:SG:O:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:E:CYS:291-:SG:Q:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:F:CYS:291-:SG:S:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:G:CYS:291-:SG:U:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:H:CYS:291-:SG:W:G3H:C1",
)
H_W_EVENT_ID = EXPECTED_EVENT_IDS[-1]

EXPECTED_HEAVY_ATOMS = (
    "C1",
    "C2",
    "C3",
    "O1",
    "O1P",
    "O2",
    "O2P",
    "O3P",
    "O4P",
    "P",
)
EXPECTED_SCAFFOLD = ("C2", "C3", "O1P", "O2", "O2P", "O3P", "O4P", "P")
EXPECTED_LINKER: tuple[str, ...] = ()
EXPECTED_WARHEAD = ("C1", "O1")

CANONICAL_TASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (
        4,
        "scaffold_plus_linker_plus_warhead",
        "C",
        ("scaffold", "linker", "warhead"),
        ("minimal_seed",),
    ),
)
DIRECT_PROFILE_TASK_APPLICABILITY = (
    (0, "warhead_only", "A", True, "generate_W_condition_on_S"),
    (
        1,
        "linker_plus_warhead",
        "B",
        False,
        "not_applicable_empty_linker_redundant_with_A",
    ),
    (
        2,
        "scaffold_plus_warhead",
        "B2",
        False,
        "not_applicable_empty_non_C_fixed_context",
    ),
    (3, "scaffold_only", "B3", True, "generate_S_condition_on_W"),
    (
        4,
        "scaffold_plus_linker_plus_warhead",
        "C",
        True,
        "generate_whole_ligand_preserve_Task_C_seed_semantics",
    ),
)
DIRECT_VALID_TASK_IDS = (0, 3, 4)

RUNTIME_SOURCE_RELATIVE = Path(
    "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"
)
CANONICAL_TASK_SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
IMMUTABLE_REPOSITORY_BINDINGS = (
    (
        RUNTIME_SOURCE_RELATIVE,
        37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        "direct_profile_runtime_contract",
    ),
    (
        CANONICAL_TASK_SOURCE_RELATIVE,
        67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        "canonical_role_and_task_semantics_owner",
    ),
)

MATRIX_HEADER = (
    "canonical_event_id",
    "review_unit_id",
    "pdb_id",
    "completed_lane",
    "formal_decision_sha256",
    "training_domain_human_decision_available",
    "training_domain_relevance_label",
    "chemistry_identity_human_decision_available",
    "chemistry_identity_label",
    "chemistry_known_positive",
    "negative_chemistry",
    "task_domain_negative",
    "distance_threshold_rejection",
    "runtime_negative",
    "reactive_pair_human_decision_available",
    "protein_reactive_atom",
    "post_ligand_reactive_atom",
    "precursor_reactive_atom_context",
    "scaffold_role_human_decision_available",
    "scaffold_atom_ids_json",
    "linker_role_human_decision_available",
    "linker_atom_ids_json",
    "warhead_role_human_decision_available",
    "warhead_atom_ids_json",
    "role_profile_human_decision_available",
    "role_profile",
    "formal_event_training_use_decision",
    "event_training_use_human_decision_available",
    "training_use_allowed",
    "human_training_excluded",
    "independent_POST_geometry_human_decision_available",
    "POST_geometry_source_evidence_status",
    "model_supervision_usable",
    "POST_geometry_training_label_available_now",
    "reaction_family_training_class_target_available",
    "warhead_rule_training_class_target_available",
    "warhead_type_target_available",
    "reusable_authority_label_available",
    "canonical_task_applicability_json",
    "global_canonical_task_count",
    "direct_profile_applicable_task_ids_json",
    "direct_profile_applicable_task_count",
    "training_mask_targets_available_now",
    "current11_tensorizer_direct_profile_supported",
    "training_admitted",
    "candidate_for_future_training_admission",
    "future_training_admission_status",
    "training_materialization_allowed_now",
    "current_runtime_model_usable",
    "event_specific_context_note",
    "event_specific_disposition_exception",
    "authority_source",
    "authority_scope",
    "authority_ingested",
    "authority_created_by_this_successor",
)


class G3HIngestionSafetyError(ValueError):
    """Raised when the G3H ingestion contract cannot be proven exactly."""


def _fail(reason: str) -> None:
    raise G3HIngestionSafetyError(reason)


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
        raise G3HIngestionSafetyError("BOUND_SOURCE_READ_FAILED:" + label) from error
    if len(payload) != expected_bytes:
        _fail("BOUND_SOURCE_BYTE_COUNT_MISMATCH:" + label)
    if _sha(payload) != expected_sha256:
        _fail("BOUND_SOURCE_SHA256_MISMATCH:" + label)
    return payload


def _literal_assignments(path: Path, names: Sequence[str]) -> dict[str, object]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise G3HIngestionSafetyError("SOURCE_AST_READ_FAILED:" + path.name) from error
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
                    raise G3HIngestionSafetyError(
                        "SOURCE_CONTRACT_NOT_LITERAL:" + target.id
                    ) from error
    if set(values) != wanted:
        _fail("SOURCE_CONTRACT_ASSIGNMENTS_MISSING")
    return values


def _expected_formal_decision_binding_v1() -> dict[str, object]:
    return {
        "path": FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": FORMAL_DECISION_BYTE_COUNT,
        "sha256": FORMAL_DECISION_SHA256,
        "sha256_scope": "file_bytes",
        "schema_version": FORMAL_DECISION_SCHEMA,
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": "2026-08-25T10:27:31Z",
        "verification_status": "MATCHED",
        "formal_authority_scope_interpretation": (
            "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION"
        ),
        "reusable_or_training_authority_interpretation": False,
    }


def _expected_runtime_contract_v1() -> dict[str, object]:
    return {
        "role_profile": EXPECTED_ROLE_PROFILE,
        "current11_tensorizer_direct_profile_supported": False,
        "direct_profile_runtime_primitives_ready": True,
        "expanded_tensorizer_integration_pending": True,
        "model_architecture_change_required": False,
        "direct_valid_canonical_task_ids": list(DIRECT_VALID_TASK_IDS),
        "direct_profile_task_applicability": [
            {
                "task_id": task_id,
                "semantic_name": semantic,
                "display_alias": alias,
                "applicable": applicable,
                "reason": reason,
            }
            for task_id, semantic, alias, applicable, reason in (
                DIRECT_PROFILE_TASK_APPLICABILITY
            )
        ],
    }


def _expected_role_snapshot_v1() -> dict[str, object]:
    return {
        "selected_candidate_index": 1,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "scaffold_atom_ids": list(EXPECTED_SCAFFOLD),
        "linker_atom_ids": [],
        "warhead_atom_ids": list(EXPECTED_WARHEAD),
        "exact_ccd_heavy_atom_ids": list(EXPECTED_HEAVY_ATOMS),
        "partition_pairwise_disjoint": True,
        "partition_union_equals_exact_ccd_heavy_atom_set": True,
        "scaffold_connected": True,
        "warhead_connected": True,
        "linker_exactly_empty": True,
        "direct_scaffold_warhead_boundary": {
            "warhead_atom_id": "C1",
            "scaffold_atom_id": "C2",
            "CCD_bond_order": "SING",
        },
        "sample_level_role_decision_exists_in_source": True,
        "sample_level_role_decision_created_by_ingestion": False,
        "reusable_role_authority_available": False,
    }


def _expected_event_projection_v1(event_id: str) -> dict[str, object]:
    if event_id not in EXPECTED_EVENT_IDS:
        _fail("EXPECTED_EVENT_PROJECTION_ID_INVALID")
    is_h_w = event_id == H_W_EVENT_ID
    return {
        "canonical_event_id": event_id,
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": "4I3W",
        "ligand_component_id": "G3H",
        "human_review_completed": True,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "task_relevance": "RELEVANT",
        "chemistry": "POSITIVE",
        "chemistry_known_positive": True,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "reactive_pair_human_decision_available": True,
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C1",
        "role_partition_human_decision_available": True,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "scaffold_atom_ids": list(EXPECTED_SCAFFOLD),
        "linker_atom_ids": [],
        "warhead_atom_ids": list(EXPECTED_WARHEAD),
        "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
        "training_use_allowed": False,
        "human_training_excluded": True,
        "model_supervision_usable": False,
        "training_admitted": False,
        "event_specific_context_difference": is_h_w,
        "event_specific_context_note": (
            "NAD_NOT_MODELED_CONTEXT_ONLY" if is_h_w else ""
        ),
        "event_specific_disposition_exception": False,
        "authority_source": "FORMAL_G3H_HUMAN_DECISION",
        "authority_scope": "SAMPLE_LEVEL_EXACT8",
        "authority_ingested": True,
        "authority_created_by_this_successor": False,
    }


def _expected_formal_authority_boundary_source_v1() -> dict[str, bool]:
    return {
        "formal_sample_level_authority_created": True,
        "human_sample_level_task_relevance_decision_created": True,
        "human_sample_level_chemistry_decision_created": True,
        "human_sample_level_training_use_decision_created": True,
        "human_sample_level_reactive_pair_decision_created": True,
        "human_sample_level_role_decision_created": True,
        "sample_specific_chemistry_authority_created": True,
        "reactive_pair_human_authoritative": True,
        "role_partition_human_authoritative": True,
        "reusable_chemistry_authority_created": False,
        "reusable_reactive_pair_authority_created": False,
        "reaction_family_authority_created": False,
        "reaction_family_training_target_available": False,
        "warhead_rule_authority_created": False,
        "warhead_rule_training_target_available": False,
        "warhead_type_target_available": False,
        "reusable_role_authority_created": False,
        "POST_geometry_training_authority_available": False,
        "training_admitted": False,
        "training_admission_created": False,
        "training_dataset_changed": False,
        "model_training_activation_authorized": False,
        "ready_for_training": False,
        "tensor_preview_implemented": False,
        "model_forward_executed": False,
        "loss_executed": False,
        "backward_executed": False,
        "optimizer_created": False,
        "optimizer_step_executed": False,
        "parameter_update_executed": False,
        "training_performed": False,
        "finetune_performed": False,
        "network_accessed": False,
        "bulk_download_performed": False,
        "cryptographic_signature_created": False,
        "repository_modified": False,
        "commit_performed": False,
        "push_performed": False,
    }


def _expected_manifest_identity_v1() -> dict[str, object]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": (
            "G3H_COMPLETED_DECISION_AND_EVENT_LABEL_AVAILABILITY_NOT_ADMISSION"
        ),
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
    }


def validate_runtime_contract_v1(
    canonical_values: Mapping[str, object], runtime_values: Mapping[str, object]
) -> dict[str, object]:
    if canonical_values.get("EXACT3_ROLES") != ("scaffold", "linker", "warhead"):
        _fail("CANONICAL_EXACT3_ROLE_VOCABULARY_DRIFT")
    if canonical_values.get("CANONICAL_TASKS") != CANONICAL_TASKS:
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")
    expected_runtime = {
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": EXPECTED_ROLE_PROFILE,
        "DIRECT_VALID_CANONICAL_TASK_IDS_V1": DIRECT_VALID_TASK_IDS,
        "DIRECT_PROFILE_TASK_APPLICABILITY_V1": DIRECT_PROFILE_TASK_APPLICABILITY,
        "CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1": False,
        "DIRECT_PROFILE_RUNTIME_PRIMITIVES_READY_V1": True,
        "EXPANDED_TENSORIZER_INTEGRATION_PENDING_V1": True,
        "MODEL_ARCHITECTURE_CHANGE_REQUIRED_V1": False,
    }
    for field, expected in expected_runtime.items():
        if runtime_values.get(field) != expected:
            _fail("DIRECT_PROFILE_RUNTIME_CONTRACT_DRIFT:" + field)
    return _expected_runtime_contract_v1()


def _validate_role_decision(role: object) -> dict[str, object]:
    if type(role) is not dict:
        _fail("FORMAL_ROLE_DECISION_NOT_OBJECT")
    if role.get("human_role_partition_decision") != "SELECT_CANDIDATE_1":
        _fail("FORMAL_ROLE_SELECTION_DRIFT")
    if role.get("selected_candidate_index") != 1:
        _fail("FORMAL_ROLE_SELECTED_CANDIDATE_INDEX_DRIFT")
    if role.get("selected_role_profile") != EXPECTED_ROLE_PROFILE:
        _fail("FORMAL_ROLE_PROFILE_DRIFT")
    if tuple(role.get("warhead_atom_ids", ())) != EXPECTED_WARHEAD:
        _fail("FORMAL_WARHEAD_ROLE_ATOM_DRIFT")
    if tuple(role.get("linker_atom_ids", ())) != EXPECTED_LINKER:
        _fail("FORMAL_G3H_LINKER_NOT_EXACTLY_EMPTY")
    if tuple(role.get("scaffold_atom_ids", ())) != EXPECTED_SCAFFOLD:
        _fail("FORMAL_SCAFFOLD_ROLE_ATOM_DRIFT")
    if tuple(role.get("exact_ccd_heavy_atom_ids", ())) != EXPECTED_HEAVY_ATOMS:
        _fail("FORMAL_G3H_HEAVY_ATOM_UNIVERSE_DRIFT")
    boundary = role.get("direct_scaffold_warhead_boundary")
    if boundary != {
        "warhead_atom_id": "C1",
        "scaffold_atom_id": "C2",
        "CCD_bond_order": "SING",
    }:
        _fail("FORMAL_DIRECT_BOUNDARY_SEMANTICS_DRIFT")
    validation = role.get("partition_validation")
    required_true = (
        "pairwise_disjoint",
        "union_equals_exact_ccd_heavy_atom_set",
        "warhead_connected",
        "linker_exactly_empty",
        "linker_connected_when_nonempty",
        "scaffold_connected",
        "whole_role_graph_valid",
        "exact_one_direct_scaffold_warhead_boundary",
        "role_partition_identical_for_all_exact8",
    )
    if type(validation) is not dict or any(
        validation.get(field) is not True for field in required_true
    ):
        _fail("FORMAL_ROLE_PARTITION_VALIDATION_DRIFT")
    if validation.get("direct_scaffold_warhead_boundary_count") != 1:
        _fail("FORMAL_DIRECT_BOUNDARY_COUNT_INVALID")
    if role.get("applies_to_exact_event_count") != 8:
        _fail("FORMAL_ROLE_EXACT8_SCOPE_INVALID")
    if role.get("sample_specific_role_decision_created") is not True:
        _fail("FORMAL_SAMPLE_ROLE_DECISION_MISSING")
    if role.get("role_partition_human_authoritative") is not True:
        _fail("FORMAL_ROLE_PARTITION_NOT_AUTHORITATIVE")
    if role.get("reusable_role_authority_created") is not False:
        _fail("FORMAL_REUSABLE_ROLE_AUTHORITY_PROMOTED")
    scaffold = set(EXPECTED_SCAFFOLD)
    linker = set(EXPECTED_LINKER)
    warhead = set(EXPECTED_WARHEAD)
    if scaffold & linker or scaffold & warhead or linker & warhead:
        _fail("G3H_ROLE_PARTITION_OVERLAP")
    if scaffold | linker | warhead != set(EXPECTED_HEAVY_ATOMS):
        _fail("G3H_ROLE_PARTITION_NOT_EXHAUSTIVE")
    return _expected_role_snapshot_v1()


def _expected_formal_mask_tasks() -> list[dict[str, object]]:
    reasons = (
        "GENERATE_WARHEAD_WITH_SCAFFOLD_FIXED",
        "NOT_STRUCTURALLY_APPLICABLE_LINKER_EXACTLY_EMPTY",
        "NOT_STRUCTURALLY_APPLICABLE_LINKER_EXACTLY_EMPTY",
        "GENERATE_SCAFFOLD_WITH_WARHEAD_FIXED",
        "WHOLE_LIGAND_TASK_PRESERVED",
    )
    return [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "structurally_applicable": task_id in DIRECT_VALID_TASK_IDS,
            "reason": reasons[task_id],
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]


def validate_formal_decision_v1(formal: Mapping[str, Any]) -> dict[str, object]:
    expected_top = {
        "schema_version": FORMAL_DECISION_SCHEMA,
        "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": "4I3W",
        "ligand_component_id": "G3H",
        "exact_event_count": 8,
        "human_review_completed": True,
        "human_decision_created": True,
        "human_review_decision_created": True,
        "human_approval_recorded": True,
        "formal_authority_created": True,
    }
    for field, expected in expected_top.items():
        if formal.get(field) != expected:
            _fail("FORMAL_TOP_LEVEL_SEMANTICS_INVALID:" + field)
    approval = formal.get("human_approval")
    if type(approval) is not dict or any(
        approval.get(field) != expected
        for field, expected in {
            "approval_recorded": True,
            "approved_at_utc": "2026-08-25T10:27:31Z",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "reviewer_provenance_attested": True,
            "attestation": "D1-D6_EXPLICITLY_AUTHORIZED_AS_RECORDED",
            "overall_decision": "APPROVE_G3H_EXACT8_D1_D6_SAMPLE_LEVEL_DECISIONS",
        }.items()
    ):
        _fail("FORMAL_HUMAN_APPROVAL_FIELDS_INVALID")

    canonical_ids = formal.get("canonical_event_ids")
    if type(canonical_ids) is not list or len(canonical_ids) != 8:
        _fail("FORMAL_CANONICAL_EVENT_EXACT8_INVALID")
    if len(set(canonical_ids)) != len(canonical_ids):
        _fail("FORMAL_CANONICAL_EVENT_DUPLICATE")
    if tuple(canonical_ids) != EXPECTED_EVENT_IDS:
        _fail("FORMAL_CANONICAL_EVENT_COVERAGE_INVALID")

    unit = formal.get("unit_level_human_decisions")
    expected_unit = {
        "exact_event_count": 8,
        "completed_human_review_event_count": 8,
        "task_relevance_decision": "RELEVANT",
        "task_relevant_event_count": 8,
        "chemistry_support_disposition": "POSITIVE",
        "chemistry_positive_event_count": 8,
        "chemistry_negative_event_count": 0,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "interpretation_scope": "SAMPLE_SPECIFIC_G3H_EXACT8_ONLY",
        "human_training_excluded_positive_event_count": 8,
        "training_admission_created": False,
        "training_dataset_changed": False,
    }
    if type(unit) is not dict or any(
        unit.get(field) != expected for field, expected in expected_unit.items()
    ):
        _fail("FORMAL_UNIT_DECISION_SEMANTICS_INVALID")

    raw_events = formal.get("event_level_human_decisions")
    if type(raw_events) is not list or len(raw_events) != 8:
        _fail("FORMAL_EXACT8_EVENT_COUNT_INVALID")
    raw_ids = [event.get("canonical_event_id") for event in raw_events if type(event) is dict]
    if len(raw_ids) != 8:
        _fail("FORMAL_EVENT_NOT_OBJECT")
    if len(set(raw_ids)) != 8:
        _fail("FORMAL_EVENT_ID_DUPLICATE")
    if tuple(raw_ids) != EXPECTED_EVENT_IDS:
        _fail("FORMAL_EVENT_ID_COVERAGE_INVALID")

    events: list[dict[str, object]] = []
    for raw in raw_events:
        event_id = raw["canonical_event_id"]
        expected_context = event_id == H_W_EVENT_ID
        exact = {
            "pdb_id": "4I3W",
            "human_task_relevance_decision": "RELEVANT",
            "human_chemistry_support_disposition": "POSITIVE",
            "negative_chemistry": False,
            "task_domain_negative": False,
            "human_reactive_pair_acceptance": "CONFIRM",
            "protein_reactive_endpoint": "CYS:291-:SG",
            "ligand_reactive_endpoint": "G3H:C1",
            "reactive_pair_human_authoritative": True,
            "human_role_partition_acceptance": "SELECT_CANDIDATE_1",
            "selected_candidate_index": 1,
            "role_partition_human_authoritative": True,
            "human_event_training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
            "human_training_excluded": True,
            "event_specific_context_difference": expected_context,
            "context_notes": (["NAD_NOT_MODELED_CONTEXT_ONLY"] if expected_context else []),
            "event_specific_disposition_exception": False,
            "decision_finalized": True,
            "training_admitted": False,
        }
        for field, expected in exact.items():
            if raw.get(field) != expected:
                _fail("FORMAL_EVENT_SEMANTICS_INVALID:" + field)
        events.append(_expected_event_projection_v1(event_id))

    reactive = formal.get("reactive_pair_human_decision")
    if type(reactive) is not dict or any(
        reactive.get(field) != expected
        for field, expected in {
            "applies_to_exact_event_count": 8,
            "human_reactive_pair_decision": "CONFIRM",
            "protein_component_id": "CYS",
            "protein_residue_id": "291-",
            "protein_reactive_atom_id": "SG",
            "protein_endpoint": "CYS:291-:SG",
            "ligand_component_id": "G3H",
            "ligand_reactive_atom_id": "C1",
            "ligand_endpoint": "G3H:C1",
            "reactive_pair_human_decision_created": True,
            "reactive_pair_human_authoritative": True,
            "reactive_pair_authority_scope": "SAMPLE_LEVEL_EXACT8",
            "reusable_reactive_pair_authority_created": False,
        }.items()
    ):
        _fail("FORMAL_REACTIVE_PAIR_SEMANTICS_DRIFT")
    role = _validate_role_decision(formal.get("role_human_decision"))

    masks = formal.get("canonical_exact5_mask_boundary")
    if type(masks) is not dict or any(
        masks.get(field) != expected
        for field, expected in {
            "role_profile": EXPECTED_ROLE_PROFILE,
            "global_canonical_task_count": 5,
            "current_role_profile_structurally_applicable_task_count": 3,
            "structurally_applicable_task_ids": [0, 3, 4],
            "tasks": _expected_formal_mask_tasks(),
            "linker_fabricated": False,
            "sixth_task_created": False,
            "canonical_task_vocabulary_changed": False,
            "training_admission_granted": False,
            "geometry_supervision_granted": False,
        }.items()
    ):
        _fail("FORMAL_CANONICAL_EXACT5_MASK_BOUNDARY_INVALID")

    training_use = formal.get("training_use_human_decision")
    if type(training_use) is not dict or any(
        training_use.get(field) != expected
        for field, expected in {
            "applies_to_exact_event_count": 8,
            "event_training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
            "human_training_excluded": True,
            "training_excluded_event_count": 8,
            "structure_quality_exclusion_claimed": False,
            "global_reusable_exclusion_policy_created": False,
            "training_admission_created": False,
        }.items()
    ):
        _fail("FORMAL_TRAINING_USE_SEMANTICS_INVALID")

    context = formal.get("event_specific_context")
    if type(context) is not dict or any(
        context.get(field) != expected
        for field, expected in {
            "canonical_event_id": H_W_EVENT_ID,
            "context_note": "NAD_NOT_MODELED_CONTEXT_ONLY",
            "event_specific_context_difference": True,
            "event_specific_disposition_exception": False,
            "task_relevance_decision": "RELEVANT",
            "chemistry_support_disposition": "POSITIVE",
            "reactive_pair_decision": "CONFIRM",
            "role_partition_decision": "SELECT_CANDIDATE_1",
            "event_training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
            "context_changes_task_relevance": False,
            "context_changes_chemistry": False,
            "context_changes_reactive_pair": False,
            "context_changes_role_partition": False,
            "context_changes_training_use": False,
            "chemistry_subgroup_authority_created": False,
        }.items()
    ):
        _fail("FORMAL_H_W_CONTEXT_BOUNDARY_INVALID")

    geometry = formal.get("geometry_authority_boundary")
    if type(geometry) is not dict or any(
        geometry.get(field) != expected
        for field, expected in {
            "PRE_geometry_status": "PRE_REACTION_UNRESOLVED",
            "PRE_reaction_graph_authority_available": False,
            "PRE_reaction_bond_order_authority_available": False,
            "PRE_geometry_authority_available": False,
            "POST_to_PRE_copy_performed": False,
            "PRE_zero_fill_performed": False,
            "POST_geometry_status": "OBSERVED_POST_COVALENT_REVIEW_EVIDENCE",
            "POST_geometry_training_authority_available": False,
            "new_POST_geometry_training_target_created": False,
        }.items()
    ):
        _fail("FORMAL_GEOMETRY_AUTHORITY_BOUNDARY_INVALID")

    reusable = formal.get("reusable_authority_boundary")
    if type(reusable) is not dict or any(
        reusable.get(field) != expected
        for field, expected in {
            "sample_specific_chemistry_authority_created": True,
            "sample_specific_reactive_pair_authority_created": True,
            "sample_specific_role_partition_authority_created": True,
            "reusable_chemistry_authority_created": False,
            "reusable_reactive_pair_authority_created": False,
            "reusable_role_authority_created": False,
            "reaction_family_authority_created": False,
            "reaction_family_training_target_available": False,
            "warhead_rule_authority_created": False,
            "warhead_rule_training_target_available": False,
            "warhead_type_target_available": False,
        }.items()
    ):
        _fail("FORMAL_REUSABLE_AUTHORITY_BOUNDARY_INVALID")

    prerequisite = formal.get("feature_semantics_training_prerequisite")
    if type(prerequisite) is not dict or any(
        prerequisite.get(field) != expected
        for field, expected in {
            "status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
            "feature_semantics_audit_completed": False,
            "feature_semantics_known": False,
            "UNKNOWN_ATOM_FEATURE_POLICY_resolved": False,
            "Step12D_scope": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        }.items()
    ):
        _fail("FORMAL_FEATURE_SEMANTICS_BOUNDARY_INVALID")

    authority = formal.get("authority_boundary")
    if authority != _expected_formal_authority_boundary_source_v1():
        _fail("FORMAL_AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    if formal.get("training_admitted") is not False:
        _fail("FORMAL_TRAINING_ADMITTED_INVALID")
    if formal.get("model_training_activation_authorized") is not False:
        _fail("FORMAL_MODEL_ACTIVATION_INVALID")
    if formal.get("ready_for_training") is not False:
        _fail("FORMAL_READY_FOR_TRAINING_INVALID")

    validation_summary = formal.get("validation_summary")
    if type(validation_summary) is not dict or any(
        validation_summary.get(field) != expected
        for field, expected in {
            "exact_event_count": 8,
            "unique_event_count": 8,
            "duplicate_event_count": 0,
            "omitted_event_count": 0,
            "task_relevant_event_count": 8,
            "chemistry_positive_event_count": 8,
            "reactive_pair_authoritative_event_count": 8,
            "role_partition_authoritative_event_count": 8,
            "training_excluded_event_count": 8,
            "event_specific_disposition_exception_count": 0,
            "PRE_authority_event_count": 0,
            "POST_geometry_training_authority_event_count": 0,
            "training_admitted_event_count": 0,
            "all_required_invariants_pass": True,
        }.items()
    ):
        _fail("FORMAL_VALIDATION_SUMMARY_INVALID")

    return {
        "approval": dict(approval),
        "events": events,
        "role": role,
        "formal_authority_boundary": (
            _expected_formal_authority_boundary_source_v1()
        ),
    }


def verify_bound_inputs_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Verify the formal source and current immutable semantic owners."""

    repo_root = repo_root.resolve()
    formal_path = (
        formal_decision_path.resolve()
        if formal_decision_path is not None
        else repo_root.parent / FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
    )
    formal_payload = _verify_payload(
        formal_path,
        FORMAL_DECISION_BYTE_COUNT,
        FORMAL_DECISION_SHA256,
        "formal_G3H_human_decision",
    )
    try:
        formal = json.loads(formal_payload)
    except json.JSONDecodeError as error:
        raise G3HIngestionSafetyError("FORMAL_DECISION_JSON_INVALID") from error
    if type(formal) is not dict:
        _fail("FORMAL_DECISION_TOP_LEVEL_NOT_OBJECT")
    normalized = validate_formal_decision_v1(formal)

    overrides = repository_path_overrides or {}
    immutable_bindings: list[dict[str, object]] = []
    for relative, byte_count, expected_sha, role in IMMUTABLE_REPOSITORY_BINDINGS:
        observed_path = overrides.get(relative, repo_root / relative)
        payload = _verify_payload(observed_path, byte_count, expected_sha, role)
        immutable_bindings.append(
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

    runtime_path = overrides.get(
        RUNTIME_SOURCE_RELATIVE, repo_root / RUNTIME_SOURCE_RELATIVE
    )
    canonical_path = overrides.get(
        CANONICAL_TASK_SOURCE_RELATIVE, repo_root / CANONICAL_TASK_SOURCE_RELATIVE
    )
    runtime_values = _literal_assignments(
        runtime_path,
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
        canonical_path, ("EXACT3_ROLES", "CANONICAL_TASKS")
    )
    runtime_contract = validate_runtime_contract_v1(canonical_values, runtime_values)
    return {
        "formal": formal,
        "normalized": normalized,
        "formal_decision_binding": _expected_formal_decision_binding_v1(),
        "immutable_repository_bindings": immutable_bindings,
        "runtime_contract": runtime_contract,
    }


def _canonical_task_contract() -> dict[str, object]:
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
        "canonical_task_vocabulary_changed": False,
        "sixth_task_created": False,
        "direct_profile_applicable_task_ids": list(DIRECT_VALID_TASK_IDS),
        "direct_profile_applicable_task_count": 3,
        "direct_profile_task_applicability": [
            {
                "task_id": task_id,
                "semantic_long_name": semantic,
                "display_alias": alias,
                "structurally_applicable": applicable,
                "reason": reason,
            }
            for task_id, semantic, alias, applicable, reason in (
                DIRECT_PROFILE_TASK_APPLICABILITY
            )
        ],
    }


def _task_applicability_with_targets() -> list[dict[str, object]]:
    role_atoms = {
        "scaffold": EXPECTED_SCAFFOLD,
        "linker": EXPECTED_LINKER,
        "warhead": EXPECTED_WARHEAD,
    }
    generated_by_task = {row[0]: row[3] for row in CANONICAL_TASKS}
    return [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "structurally_applicable": applicable,
            "applicability_reason": reason,
            "metadata_derived_target_atom_ids": [
                atom
                for role in generated_by_task[task_id]
                for atom in role_atoms[role]
            ],
            "training_mask_target_available_now": False,
        }
        for task_id, semantic, alias, applicable, reason in (
            DIRECT_PROFILE_TASK_APPLICABILITY
        )
    ]


def _authority_boundary() -> dict[str, bool]:
    return {
        "formal_human_decision_modified": False,
        "review_preparation_modified": False,
        "historical_reconciliation_modified": False,
        "formal_split_modified": False,
        "sample_level_human_authority_exists_in_source": True,
        "sample_level_human_authority_created_by_ingestion": False,
        "sample_decision_ingestion_snapshot_created": True,
        "reusable_chemistry_authority_created": False,
        "reusable_role_authority_created": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "PRE_geometry_authority_created": False,
        "POST_geometry_training_authority_created": False,
        "tensor_preview_created": False,
        "tensorizer_integration_performed": False,
        "training_admission_created": False,
        "training_dataset_changed": False,
        "model_forward_executed": False,
        "loss_executed": False,
        "backward_executed": False,
        "optimizer_created": False,
        "optimizer_step_executed": False,
        "parameter_update_executed": False,
        "training_performed": False,
        "finetune_performed": False,
        "network_performed": False,
        "download_performed": False,
        "commit_performed": False,
        "push_performed": False,
    }


def _build_snapshot(bound: Mapping[str, Any]) -> dict[str, object]:
    normalized = bound["normalized"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_role": "ADDITIVE_IMMUTABLE_G3H_COMPLETED_HUMAN_DECISION_SUCCESSOR",
        "formal_decision_binding": bound["formal_decision_binding"],
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": "4I3W",
        "ligand_component_id": "G3H",
        "authority_provenance": {
            "authority_source": "FORMAL_G3H_HUMAN_DECISION",
            "authority_scope": "SAMPLE_LEVEL_EXACT8",
            "authority_ingested": True,
            "authority_created_by_this_successor": False,
            "sample_level_human_decision_exists_in_source": True,
            "sample_level_human_decision_created_by_ingestion": False,
            "successor_provenance_strategy": "SHA_BIND_FORMAL_HUMAN_DECISION",
            "reusable_authority_created": False,
            "training_authority_created": False,
        },
        "training_domain_relevance": {
            "value": "RELEVANT",
            "human_decision_available": True,
            "human_decision_created_by_ingestion": False,
        },
        "chemistry_identity": {
            "value": "POSITIVE",
            "chemistry_known_positive": True,
            "negative_chemistry": False,
            "task_domain_negative": False,
            "human_decision_available": True,
            "human_decision_created_by_ingestion": False,
        },
        "events": normalized["events"],
        "reactive_pair": {
            "status": "CONFIRM",
            "protein_endpoint": "CYS:291-:SG",
            "protein_reactive_atom": "SG",
            "post_ligand_endpoint": "G3H:C1",
            "post_ligand_reactive_atom": "C1",
            "precursor_reactive_atom_context": "PRE_REACTION_UNRESOLVED",
            "human_decision_available": True,
            "human_decision_created_by_ingestion": False,
            "reusable_authority_available": False,
        },
        "role_decision": normalized["role"],
        "canonical_task_contract": _canonical_task_contract(),
        "direct_profile_runtime_contract": bound["runtime_contract"],
        "geometry_authority_boundary": {
            "PRE_geometry_status": "PRE_REACTION_UNRESOLVED",
            "PRE_geometry_authority_available": False,
            "POST_geometry_source_evidence_status": (
                "OBSERVED_POST_COVALENT_REVIEW_EVIDENCE"
            ),
            "independent_POST_geometry_human_decision_available": False,
            "POST_geometry_training_authority_available": False,
            "POST_geometry_training_label_available_now": False,
            "POST_to_PRE_copy_performed": False,
            "PRE_zero_fill_performed": False,
        },
        "auxiliary_authority_boundary": {
            "reaction_family_training_class_target_available": False,
            "warhead_rule_training_class_target_available": False,
            "warhead_type_target_available": False,
            "reusable_authority_label_available": False,
        },
        "training_boundary": {
            "event_training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
            "training_include_count": 0,
            "training_excluded_positive_count": 8,
            "training_admitted_count": 0,
            "training_materialization_allowed_count": 0,
            "current_runtime_model_usable_count": 0,
            "current11_tensorizer_direct_profile_supported": False,
            "training_mask_targets_available_now": False,
            "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
            "ready_for_training": False,
        },
        "authority_boundary": _authority_boundary(),
        "formal_authority_boundary_source": normalized[
            "formal_authority_boundary"
        ],
    }


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    task_cell = _json_cell(_task_applicability_with_targets())
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        rows.append(
            {
                "canonical_event_id": event["canonical_event_id"],
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
                "pdb_id": "4I3W",
                "completed_lane": EXPECTED_COMPLETED_LANE,
                "formal_decision_sha256": FORMAL_DECISION_SHA256,
                "training_domain_human_decision_available": "true",
                "training_domain_relevance_label": "RELEVANT",
                "chemistry_identity_human_decision_available": "true",
                "chemistry_identity_label": "POSITIVE",
                "chemistry_known_positive": "true",
                "negative_chemistry": "false",
                "task_domain_negative": "false",
                "distance_threshold_rejection": "false",
                "runtime_negative": "false",
                "reactive_pair_human_decision_available": "true",
                "protein_reactive_atom": "SG",
                "post_ligand_reactive_atom": "C1",
                "precursor_reactive_atom_context": "PRE_REACTION_UNRESOLVED",
                "scaffold_role_human_decision_available": "true",
                "scaffold_atom_ids_json": _json_cell(list(EXPECTED_SCAFFOLD)),
                "linker_role_human_decision_available": "true",
                "linker_atom_ids_json": "[]",
                "warhead_role_human_decision_available": "true",
                "warhead_atom_ids_json": _json_cell(list(EXPECTED_WARHEAD)),
                "role_profile_human_decision_available": "true",
                "role_profile": EXPECTED_ROLE_PROFILE,
                "formal_event_training_use_decision": (
                    "EXCLUDE_FROM_TRAINING_ONLY"
                ),
                "event_training_use_human_decision_available": "true",
                "training_use_allowed": "false",
                "human_training_excluded": "true",
                "independent_POST_geometry_human_decision_available": "false",
                "POST_geometry_source_evidence_status": (
                    "OBSERVED_POST_COVALENT_REVIEW_EVIDENCE"
                ),
                "model_supervision_usable": "false",
                "POST_geometry_training_label_available_now": "false",
                "reaction_family_training_class_target_available": "false",
                "warhead_rule_training_class_target_available": "false",
                "warhead_type_target_available": "false",
                "reusable_authority_label_available": "false",
                "canonical_task_applicability_json": task_cell,
                "global_canonical_task_count": "5",
                "direct_profile_applicable_task_ids_json": "[0,3,4]",
                "direct_profile_applicable_task_count": "3",
                "training_mask_targets_available_now": "false",
                "current11_tensorizer_direct_profile_supported": "false",
                "training_admitted": "false",
                "candidate_for_future_training_admission": "false",
                "future_training_admission_status": (
                    "HUMAN_EXCLUDE_FROM_TRAINING_ONLY"
                ),
                "training_materialization_allowed_now": "false",
                "current_runtime_model_usable": "false",
                "event_specific_context_note": event[
                    "event_specific_context_note"
                ],
                "event_specific_disposition_exception": "false",
                "authority_source": "FORMAL_G3H_HUMAN_DECISION",
                "authority_scope": "SAMPLE_LEVEL_EXACT8",
                "authority_ingested": "true",
                "authority_created_by_this_successor": "false",
            }
        )
    return rows


def _candidate_source_bindings(repo_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    roles = (
        (SOURCE_RELATIVE, "production_owner"),
        (CHECKER_RELATIVE, "fail_closed_checker"),
        (TEST_RELATIVE, "targeted_test_contract"),
    )
    for relative, role in roles:
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


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "event_count": 8,
        "completed_human_positive_count": 8,
        "training_include_count": 0,
        "training_excluded_positive_count": 8,
        "task_relevant_count": 8,
        "chemistry_positive_count": 8,
        "reactive_pair_human_authority_count": 8,
        "role_partition_human_authority_count": 8,
        "direct_profile_count": 8,
        "global_canonical_task_count": 5,
        "direct_profile_applicable_task_count_per_event": 3,
        "PRE_geometry_authority_count": 0,
        "POST_geometry_training_authority_count": 0,
        "reaction_family_target_count": 0,
        "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
        "reusable_authority_count": 0,
        "training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "H_W_context_difference_count": 1,
        "event_specific_disposition_exception_count": 0,
        "formal_human_decision_ingested": True,
        "cumulative1000_reconciliation_status": "NOT_DONE_THIS_STEP",
        "tensor_integration_status": "NOT_DONE",
        "training_admission_status": "NOT_DONE",
        "feature_semantics_status": "AUDIT_REQUIRED_LATER",
        "ready_for_training": False,
        "authority_boundary": _authority_boundary(),
    }


def _manifest_counts() -> dict[str, int]:
    summary = _summary()
    excluded = {
        "schema_version",
        "stage",
        "formal_human_decision_ingested",
        "cumulative1000_reconciliation_status",
        "tensor_integration_status",
        "training_admission_status",
        "feature_semantics_status",
        "ready_for_training",
        "authority_boundary",
    }
    return {key: value for key, value in summary.items() if key not in excluded}


def build_artifacts_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Build the exact four deterministic metadata artifacts in memory."""

    repo_root = repo_root.resolve()
    bound = verify_bound_inputs_v1(
        repo_root,
        formal_decision_path=formal_decision_path,
        repository_path_overrides=repository_path_overrides,
    )
    candidate_bindings = _candidate_source_bindings(repo_root)
    snapshot = _build_snapshot(bound)
    snapshot_payload = _json_bytes(snapshot)
    matrix_payload = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    summary = _summary()
    summary_payload = _json_bytes(summary)
    manifest = {
        **_expected_manifest_identity_v1(),
        "formal_decision_binding": bound["formal_decision_binding"],
        "immutable_semantic_owner_bindings": bound[
            "immutable_repository_bindings"
        ],
        "candidate_source_bindings": candidate_bindings,
        "canonical_task_contract": _canonical_task_contract(),
        "direct_profile_runtime_contract": bound["runtime_contract"],
        "counts": _manifest_counts(),
        "human_authority_ingestion_semantics": {
            "authority_source": "FORMAL_G3H_HUMAN_DECISION",
            "authority_scope": "SAMPLE_LEVEL_EXACT8",
            "authority_ingested": True,
            "authority_created_by_this_successor": False,
            "formal_authority_scope_interpretation": (
                "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION"
            ),
        },
        "output_artifact_bindings": {
            SNAPSHOT: {"sha256": _sha(snapshot_payload)},
            MATRIX: {"sha256": _sha(matrix_payload)},
            SUMMARY: {"sha256": _sha(summary_payload)},
        },
        "manifest_self_sha256_recorded": False,
        "manifest_self_sha256_policy": "SELF_SHA256_PROHIBITED",
        "deterministic": True,
        "feature_semantics_audit_required_before_formal_training": True,
        "ready_for_training": False,
        "authority_boundary": _authority_boundary(),
    }
    manifest_payload = _json_bytes(manifest)
    artifacts = {
        SNAPSHOT: snapshot_payload,
        MATRIX: matrix_payload,
        MANIFEST: manifest_payload,
        SUMMARY: summary_payload,
    }
    validate_artifacts_v1(artifacts, repo_root=repo_root)
    return artifacts


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
        raise G3HIngestionSafetyError("UTF8_INVALID:" + label) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TRAILING_WHITESPACE_INVALID:" + label)


def _require_exact_keys(
    value: object, keys: Sequence[str], reason: str
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(keys):
        _fail(reason)
    return value


def _reject_dynamic_metadata(value: object) -> None:
    forbidden = {
        "generated_at",
        "generated_at_utc",
        "hostname",
        "host_name",
        "pid",
        "process_id",
        "uuid",
        "git_head",
        "git_parent",
        "commit_subject",
        "origin_main",
        "ahead",
        "behind",
    }
    if type(value) is dict:
        for key, child in value.items():
            if key in forbidden:
                _fail("DYNAMIC_OR_LIFECYCLE_METADATA_FORBIDDEN:" + key)
            _reject_dynamic_metadata(child)
    elif type(value) is list:
        for child in value:
            _reject_dynamic_metadata(child)


def _validate_snapshot_events(events: object) -> None:
    if type(events) is not list or len(events) != 8:
        _fail("SNAPSHOT_EXACT8_EVENT_COUNT_INVALID")
    event_ids = [event.get("canonical_event_id") for event in events if type(event) is dict]
    if len(event_ids) != 8:
        _fail("SNAPSHOT_EVENT_NOT_OBJECT")
    if len(set(event_ids)) != 8:
        _fail("SNAPSHOT_EVENT_DUPLICATE")
    if tuple(event_ids) != EXPECTED_EVENT_IDS:
        _fail("SNAPSHOT_EVENT_COVERAGE_INVALID")
    for event in events:
        if event != _expected_event_projection_v1(event["canonical_event_id"]):
            _fail("SNAPSHOT_EVENT_EXACT_SCHEMA_OR_SEMANTICS_INVALID")


def _validate_task_contract(contract: object, reason: str) -> None:
    if contract != _canonical_task_contract():
        _fail(reason)


def validate_artifacts_v1(
    artifacts: Mapping[str, bytes], *, repo_root: Path | None = None
) -> None:
    """Validate direct artifact evidence without trusting manifest booleans."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    try:
        snapshot = json.loads(artifacts[SNAPSHOT])
        manifest = json.loads(artifacts[MANIFEST])
        summary = json.loads(artifacts[SUMMARY])
        matrix = list(csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8"))))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise G3HIngestionSafetyError("OUTPUT_PARSE_FAILED") from error
    for document in (snapshot, manifest, summary):
        _reject_dynamic_metadata(document)

    snapshot = _require_exact_keys(
        snapshot,
        (
            "schema_version",
            "snapshot_role",
            "formal_decision_binding",
            "review_unit_id",
            "pdb_id",
            "ligand_component_id",
            "authority_provenance",
            "training_domain_relevance",
            "chemistry_identity",
            "events",
            "reactive_pair",
            "role_decision",
            "canonical_task_contract",
            "direct_profile_runtime_contract",
            "geometry_authority_boundary",
            "auxiliary_authority_boundary",
            "training_boundary",
            "authority_boundary",
            "formal_authority_boundary_source",
        ),
        "SNAPSHOT_TOP_LEVEL_SCHEMA_INVALID",
    )
    if (
        snapshot["schema_version"] != SNAPSHOT_SCHEMA_VERSION
        or snapshot["snapshot_role"]
        != "ADDITIVE_IMMUTABLE_G3H_COMPLETED_HUMAN_DECISION_SUCCESSOR"
        or snapshot["review_unit_id"] != EXPECTED_REVIEW_UNIT_ID
        or snapshot["pdb_id"] != "4I3W"
        or snapshot["ligand_component_id"] != "G3H"
    ):
        _fail("SNAPSHOT_IDENTITY_INVALID")
    binding = snapshot["formal_decision_binding"]
    if binding != _expected_formal_decision_binding_v1():
        _fail("SNAPSHOT_FORMAL_BINDING_INVALID")
    provenance = snapshot["authority_provenance"]
    if provenance != {
        "authority_source": "FORMAL_G3H_HUMAN_DECISION",
        "authority_scope": "SAMPLE_LEVEL_EXACT8",
        "authority_ingested": True,
        "authority_created_by_this_successor": False,
        "sample_level_human_decision_exists_in_source": True,
        "sample_level_human_decision_created_by_ingestion": False,
        "successor_provenance_strategy": "SHA_BIND_FORMAL_HUMAN_DECISION",
        "reusable_authority_created": False,
        "training_authority_created": False,
    }:
        _fail("SNAPSHOT_AUTHORITY_PROVENANCE_INVALID")
    if snapshot["training_domain_relevance"] != {
        "value": "RELEVANT",
        "human_decision_available": True,
        "human_decision_created_by_ingestion": False,
    }:
        _fail("SNAPSHOT_TASK_RELEVANCE_INVALID")
    if snapshot["chemistry_identity"] != {
        "value": "POSITIVE",
        "chemistry_known_positive": True,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "human_decision_available": True,
        "human_decision_created_by_ingestion": False,
    }:
        _fail("SNAPSHOT_CHEMISTRY_INVALID")
    _validate_snapshot_events(snapshot["events"])
    reactive = snapshot["reactive_pair"]
    if reactive != {
        "status": "CONFIRM",
        "protein_endpoint": "CYS:291-:SG",
        "protein_reactive_atom": "SG",
        "post_ligand_endpoint": "G3H:C1",
        "post_ligand_reactive_atom": "C1",
        "precursor_reactive_atom_context": "PRE_REACTION_UNRESOLVED",
        "human_decision_available": True,
        "human_decision_created_by_ingestion": False,
        "reusable_authority_available": False,
    }:
        _fail("SNAPSHOT_REACTIVE_PAIR_INVALID")
    role = snapshot["role_decision"]
    if role != _expected_role_snapshot_v1():
        _fail("SNAPSHOT_ROLE_DECISION_INVALID")
    _validate_task_contract(
        snapshot["canonical_task_contract"], "SNAPSHOT_CANONICAL_TASK_CONTRACT_INVALID"
    )
    runtime = snapshot["direct_profile_runtime_contract"]
    if runtime != _expected_runtime_contract_v1():
        _fail("SNAPSHOT_RUNTIME_CONTRACT_INVALID")
    geometry = snapshot["geometry_authority_boundary"]
    if geometry != {
        "PRE_geometry_status": "PRE_REACTION_UNRESOLVED",
        "PRE_geometry_authority_available": False,
        "POST_geometry_source_evidence_status": "OBSERVED_POST_COVALENT_REVIEW_EVIDENCE",
        "independent_POST_geometry_human_decision_available": False,
        "POST_geometry_training_authority_available": False,
        "POST_geometry_training_label_available_now": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_zero_fill_performed": False,
    }:
        _fail("SNAPSHOT_GEOMETRY_BOUNDARY_INVALID")
    auxiliary = snapshot["auxiliary_authority_boundary"]
    if auxiliary != {
        "reaction_family_training_class_target_available": False,
        "warhead_rule_training_class_target_available": False,
        "warhead_type_target_available": False,
        "reusable_authority_label_available": False,
    }:
        _fail("SNAPSHOT_AUXILIARY_AUTHORITY_INVALID")
    training = snapshot["training_boundary"]
    if training != {
        "event_training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "training_include_count": 0,
        "training_excluded_positive_count": 8,
        "training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "current11_tensorizer_direct_profile_supported": False,
        "training_mask_targets_available_now": False,
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
        "ready_for_training": False,
    }:
        _fail("SNAPSHOT_TRAINING_BOUNDARY_INVALID")
    if snapshot["authority_boundary"] != _authority_boundary():
        _fail("SNAPSHOT_AUTHORITY_BOUNDARY_INVALID")
    if snapshot["formal_authority_boundary_source"] != (
        _expected_formal_authority_boundary_source_v1()
    ):
        _fail("SNAPSHOT_FORMAL_AUTHORITY_BOUNDARY_SOURCE_INVALID")

    if (list(matrix[0].keys()) if matrix else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    if len(matrix) != 8 or len({row["canonical_event_id"] for row in matrix}) != 8:
        _fail("MATRIX_EXACT8_INVALID")
    if tuple(row["canonical_event_id"] for row in matrix) != EXPECTED_EVENT_IDS:
        _fail("MATRIX_EVENT_COVERAGE_INVALID")
    expected_matrix_payload = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    if artifacts[MATRIX] != expected_matrix_payload:
        _fail("MATRIX_DIRECT_EVIDENCE_INVALID")
    for row in matrix:
        for field in (
            "training_domain_human_decision_available",
            "chemistry_identity_human_decision_available",
            "chemistry_known_positive",
            "reactive_pair_human_decision_available",
            "scaffold_role_human_decision_available",
            "linker_role_human_decision_available",
            "warhead_role_human_decision_available",
            "role_profile_human_decision_available",
            "event_training_use_human_decision_available",
            "human_training_excluded",
            "authority_ingested",
        ):
            if row[field] != "true":
                _fail("MATRIX_REQUIRED_AUTHORITY_UNAVAILABLE:" + field)
        for field in (
            "negative_chemistry",
            "task_domain_negative",
            "distance_threshold_rejection",
            "runtime_negative",
            "training_use_allowed",
            "independent_POST_geometry_human_decision_available",
            "model_supervision_usable",
            "POST_geometry_training_label_available_now",
            "reaction_family_training_class_target_available",
            "warhead_rule_training_class_target_available",
            "warhead_type_target_available",
            "reusable_authority_label_available",
            "training_mask_targets_available_now",
            "current11_tensorizer_direct_profile_supported",
            "training_admitted",
            "candidate_for_future_training_admission",
            "training_materialization_allowed_now",
            "current_runtime_model_usable",
            "event_specific_disposition_exception",
            "authority_created_by_this_successor",
        ):
            if row[field] != "false":
                _fail("MATRIX_SAFETY_FLAG_INVALID:" + field)
        applicability = json.loads(row["canonical_task_applicability_json"])
        if len(applicability) != 5:
            _fail("MATRIX_GLOBAL_CANONICAL_EXACT5_INVALID")
        if [
            item["task_id"]
            for item in applicability
            if item["structurally_applicable"]
        ] != [0, 3, 4]:
            _fail("MATRIX_DIRECT_APPLICABLE_TASK_IDS_INVALID")
        if applicability[3]["semantic_long_name"] != "scaffold_only":
            _fail("MATRIX_B3_OMITTED")
        if applicability[1]["structurally_applicable"] is not False:
            _fail("MATRIX_B_MUST_BE_STRUCTURALLY_INAPPLICABLE")
        if applicability[2]["structurally_applicable"] is not False:
            _fail("MATRIX_B2_MUST_BE_STRUCTURALLY_INAPPLICABLE")

    manifest = _require_exact_keys(
        manifest,
        (
            "schema_version",
            "stage",
            "artifact_role",
            "candidate_publication_file_count",
            "output_artifact_count",
            "source_path",
            "checker_path",
            "test_path",
            "output_paths",
            "formal_decision_binding",
            "immutable_semantic_owner_bindings",
            "candidate_source_bindings",
            "canonical_task_contract",
            "direct_profile_runtime_contract",
            "counts",
            "human_authority_ingestion_semantics",
            "output_artifact_bindings",
            "manifest_self_sha256_recorded",
            "manifest_self_sha256_policy",
            "deterministic",
            "feature_semantics_audit_required_before_formal_training",
            "ready_for_training",
            "authority_boundary",
        ),
        "MANIFEST_TOP_LEVEL_SCHEMA_INVALID",
    )
    expected_manifest_identity = _expected_manifest_identity_v1()
    if (
        any(
            manifest[field] != expected
            for field, expected in expected_manifest_identity.items()
        )
        or manifest["deterministic"] is not True
        or manifest["manifest_self_sha256_recorded"] is not False
        or manifest["manifest_self_sha256_policy"] != "SELF_SHA256_PROHIBITED"
        or manifest["feature_semantics_audit_required_before_formal_training"]
        is not True
        or manifest["ready_for_training"] is not False
    ):
        _fail("MANIFEST_BOUNDARY_INVALID")
    if manifest["formal_decision_binding"] != (
        _expected_formal_decision_binding_v1()
    ):
        _fail("MANIFEST_FORMAL_BINDING_INVALID")
    expected_owner_bindings = [
        {
            "path": relative.as_posix(),
            "path_namespace": "repository_relative",
            "byte_count": byte_count,
            "sha256": sha256,
            "sha256_scope": "file_bytes",
            "source_role": role,
            "verification_status": "MATCHED",
        }
        for relative, byte_count, sha256, role in IMMUTABLE_REPOSITORY_BINDINGS
    ]
    if manifest["immutable_semantic_owner_bindings"] != expected_owner_bindings:
        _fail("MANIFEST_SEMANTIC_OWNER_BINDINGS_INVALID")
    if repo_root is not None and manifest["candidate_source_bindings"] != (
        _candidate_source_bindings(repo_root.resolve())
    ):
        _fail("MANIFEST_CANDIDATE_SOURCE_BINDINGS_INVALID")
    _validate_task_contract(
        manifest["canonical_task_contract"], "MANIFEST_CANONICAL_TASK_CONTRACT_INVALID"
    )
    if manifest["direct_profile_runtime_contract"] != (
        _expected_runtime_contract_v1()
    ):
        _fail("MANIFEST_RUNTIME_CONTRACT_INVALID")
    if manifest["direct_profile_runtime_contract"] != runtime:
        _fail("MANIFEST_SNAPSHOT_RUNTIME_CONTRACT_MISMATCH")
    if manifest["counts"] != _manifest_counts():
        _fail("MANIFEST_COUNTS_INVALID")
    if manifest["human_authority_ingestion_semantics"] != {
        "authority_source": "FORMAL_G3H_HUMAN_DECISION",
        "authority_scope": "SAMPLE_LEVEL_EXACT8",
        "authority_ingested": True,
        "authority_created_by_this_successor": False,
        "formal_authority_scope_interpretation": (
            "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION"
        ),
    }:
        _fail("MANIFEST_AUTHORITY_INGESTION_INVALID")
    if manifest["output_artifact_bindings"] != {
        SNAPSHOT: {"sha256": _sha(artifacts[SNAPSHOT])},
        MATRIX: {"sha256": _sha(artifacts[MATRIX])},
        SUMMARY: {"sha256": _sha(artifacts[SUMMARY])},
    }:
        _fail("MANIFEST_OUTPUT_BINDINGS_INVALID")
    if manifest["authority_boundary"] != _authority_boundary():
        _fail("MANIFEST_AUTHORITY_BOUNDARY_INVALID")

    if summary != _summary():
        _fail("SUMMARY_EXACT_COUNTS_OR_BOUNDARY_INVALID")


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
    artifacts = build_artifacts_v1(repo_root)
    destination = (
        output_root.resolve()
        if output_root is not None
        else repo_root.resolve() / OUTPUT_ROOT_RELATIVE
    )
    if destination.exists():
        unexpected = {
            path.name for path in destination.iterdir() if path.name not in OUTPUT_FILENAMES
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
    observed_names = {path.name for path in output_root.iterdir()}
    if observed_names != set(OUTPUT_FILENAMES):
        _fail("MATERIALIZED_OUTPUT_EXACT4_INVALID")
    observed: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = output_root / name
        if not path.is_file() or path.is_symlink():
            _fail("MATERIALIZED_OUTPUT_NOT_REGULAR:" + name)
        observed[name] = path.read_bytes()
        if observed[name] != expected[name]:
            _fail("MATERIALIZED_OUTPUT_BYTES_MISMATCH:" + name)
    validate_artifacts_v1(observed, repo_root=repo_root)
    return {
        "materialized_output_valid": True,
        "output_artifact_count": 4,
        "candidate_publication_file_count": 7,
        "artifact_sha256": {name: _sha(observed[name]) for name in OUTPUT_FILENAMES},
        "formal_decision_sha256": FORMAL_DECISION_SHA256,
        "event_count": 8,
        "chemistry_positive_count": 8,
        "training_excluded_positive_count": 8,
        "training_include_count": 0,
        "training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "deterministic_rebuild_matches_materialized": True,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    artifacts = materialize_artifacts_v1(repo_root)
    print("formal_human_decision_ingested=true")
    print("output_artifact_count=4")
    print("candidate_publication_file_count=7")
    print("event_count=8")
    print("chemistry_positive_count=8")
    print("training_excluded_positive_count=8")
    print("training_include_count=0")
    print("training_admitted_count=0")
    for name in OUTPUT_FILENAMES:
        print(name + "_sha256=" + _sha(artifacts[name]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
