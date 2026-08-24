"""Build the additive FFQ completed-decision ingestion successor V1.

This metadata-only owner SHA-binds the completed external FFQ human decision,
snapshots its existing sample-level decisions, and exposes event-level label
availability.  It does not create human authority, mutate predecessor review
state, admit training samples, update runtime/split state, register chemistry,
tensorize data, or train a model.
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
    "covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT_SCHEMA_VERSION = "covapie_ffq_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_ffq_event_task_label_availability_v1"
MANIFEST_SCHEMA_VERSION = "covapie_ffq_completed_decision_ingestion_manifest_v1"
SUMMARY_SCHEMA_VERSION = "covapie_ffq_completed_decision_ingestion_summary_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_ffq_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_ffq_event_task_label_availability_v1.csv"
MANIFEST = "covapie_ffq_completed_decision_ingestion_manifest_v1.json"
SUMMARY = "covapie_ffq_completed_decision_ingestion_summary_v1.json"
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
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D/"
    "formal-human-decision-v1/ffq_formal_human_decision_v1.json"
)
FORMAL_DECISION_BYTE_COUNT = 14197
FORMAL_DECISION_SHA256 = (
    "ba0670519064399b2ecb0c73631009c8c6c4d3c14512377ecfaad0d87388e149"
)

# Immutable repository inputs.  Tuples are used deliberately: this is a
# closed source contract, not a mutable registry.
IMMUTABLE_REPOSITORY_BINDINGS = (
    (
        Path(
            "data/derived/covalent_small/"
            "covapie_bulk_post_only_cys_sg_human_review_v1/"
            "covapie_post_only_human_review_decisions_v1.json"
        ),
        91133,
        "c2060a8b0a8123fbc6b9c11f2e70a9443367b63467bf9f9cf913a4c780168441",
        "legacy_human_review_overlay_read_only",
    ),
    (
        Path(
            "data/derived/covalent_small/"
            "covapie_bulk_post_only_cys_sg_human_review_v1/"
            "covapie_post_only_human_review_progress_v1.json"
        ),
        621,
        "e1e93ff28e823c1f52b306623bbf20c06f2c0c95cca90bb1e61ee4d1b7cea216",
        "legacy_human_review_progress_read_only",
    ),
    (
        Path(
            "data/derived/covalent_small/"
            "covapie_cumulative1000_high_yield_human_review_authority_calibration_v1/"
            "covapie_cumulative1000_current_review_status_reconciliation_v1.csv"
        ),
        99335,
        "4eb608e2d97b60230ae1e0ca4e4be6a7fe8b3dc45af3467cbc98f685c385862f",
        "historical_reconciliation_read_only",
    ),
    (
        Path("src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"),
        37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        "direct_profile_runtime_contract",
    ),
    (
        Path(
            "src/covalent_ext/"
            "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
        ),
        67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        "canonical_role_and_task_semantics_owner",
    ),
    (
        Path(
            "src/covalent_ext/"
            "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1.py"
        ),
        60187,
        "66c0e46a96084f1ea5da4f8175ec8ae01164b211395d89eafde1f2e44f50c372",
        "batch001_additive_successor_precedent_owner",
    ),
    (
        Path(
            "data/derived/covalent_small/"
            "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1/"
            "covapie_batch001_completed_human_decision_snapshot_v1.json"
        ),
        33764,
        "c0c887b9026638484ae453d68a6fc654e3bd1b3bce7aa222f8a285d4878e0200",
        "batch001_additive_snapshot_precedent",
    ),
    (
        Path(
            "data/derived/covalent_small/"
            "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1/"
            "covapie_batch001_event_task_label_availability_v1.csv"
        ),
        35603,
        "f8481147babbad02215c3c3f767fe22ba6a511b8a076482a9635fec5d5cf8e82",
        "batch001_event_matrix_precedent",
    ),
)

RUNTIME_SOURCE_RELATIVE = Path(
    "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"
)
CANONICAL_TASK_SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)

EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D"
EXPECTED_DOMAIN = "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
EXPECTED_CHEMISTRY = "COVALENT_CHEMISTRY_SUPPORTED"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
EXPECTED_EXCLUSION_REASON = (
    "FROZEN_COORDINATE_GEOMETRY_NOT_RECOMMENDED_FOR_MODEL_SUPERVISION"
)
EXPECTED_REACTION_FAMILY_CANDIDATE_ID = (
    "COVAPIE_CYS_SG_REACTION_FAMILY_B1FD795D4D442304"
)
EXPECTED_WARHEAD_RULE_CANDIDATE_ID = (
    "COVAPIE_CYS_SG_WARHEAD_RULE_B96D4E846C704691"
)

EXPECTED_HEAVY_ATOMS = ("C1", "C2", "C3", "O1", "O2", "O3", "O4", "P1")
EXPECTED_SCAFFOLD = ("O2", "O3", "O4", "P1")
EXPECTED_LINKER: tuple[str, ...] = ()
EXPECTED_WARHEAD = ("C1", "C2", "C3", "O1")

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
    "independent_POST_geometry_human_decision_available",
    "POST_geometry_source_evidence_status",
    "model_supervision_usable",
    "POST_geometry_training_label_available_now",
    "POST_geometry_training_label_blocking_reason",
    "reaction_family_candidate_id",
    "reaction_family_candidate_human_accepted_for_review",
    "reaction_family_training_class_target_available",
    "warhead_rule_candidate_id",
    "warhead_rule_candidate_human_accepted_for_review",
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
    "authority_source",
    "authority_scope",
    "authority_ingested",
    "authority_created_by_this_successor",
)


class FFQIngestionSafetyError(ValueError):
    """Raised whenever the FFQ ingestion contract cannot be proven."""


def _fail(reason: str) -> None:
    raise FFQIngestionSafetyError(reason)


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


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise FFQIngestionSafetyError("JSON_SOURCE_READ_FAILED:" + path.name) from error
    if type(value) is not dict:
        _fail("JSON_SOURCE_TOP_LEVEL_NOT_OBJECT:" + path.name)
    return value


def _verify_payload(
    path: Path, expected_bytes: int, expected_sha256: str, label: str
) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise FFQIngestionSafetyError("BOUND_SOURCE_READ_FAILED:" + label) from error
    if len(payload) != expected_bytes:
        _fail("BOUND_SOURCE_BYTE_COUNT_MISMATCH:" + label)
    if _sha(payload) != expected_sha256:
        _fail("BOUND_SOURCE_SHA256_MISMATCH:" + label)
    return payload


def _literal_assignments(path: Path, names: Sequence[str]) -> dict[str, object]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise FFQIngestionSafetyError("SOURCE_AST_READ_FAILED:" + path.name) from error
    wanted = set(names)
    values: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value_node = node.value
        for target in targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    values[target.id] = ast.literal_eval(value_node)
                except (ValueError, TypeError) as error:
                    raise FFQIngestionSafetyError(
                        "SOURCE_CONTRACT_NOT_LITERAL:" + target.id
                    ) from error
    if set(values) != wanted:
        _fail("SOURCE_CONTRACT_ASSIGNMENTS_MISSING")
    return values


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


def _validate_role_decision(role: object) -> dict[str, object]:
    if type(role) is not dict:
        _fail("FORMAL_ROLE_DECISION_NOT_OBJECT")
    if tuple(role.get("scaffold_atom_ids", ())) != EXPECTED_SCAFFOLD:
        _fail("FORMAL_SCAFFOLD_ROLE_ATOM_DRIFT")
    if tuple(role.get("linker_atom_ids", ())) != EXPECTED_LINKER:
        _fail("FORMAL_FFQ_LINKER_NOT_EXACTLY_EMPTY")
    if tuple(role.get("warhead_atom_ids", ())) != EXPECTED_WARHEAD:
        _fail("FORMAL_WARHEAD_ROLE_ATOM_DRIFT")
    if role.get("role_profile") != EXPECTED_ROLE_PROFILE:
        _fail("FORMAL_ROLE_PROFILE_DRIFT")
    if tuple(role.get("FFQ_exact8_heavy_atom_set", ())) != EXPECTED_HEAVY_ATOMS:
        _fail("FORMAL_FFQ_HEAVY_ATOM_UNIVERSE_DRIFT")
    for field in (
        "partition_pairwise_disjoint",
        "partition_exhaustive",
        "partition_union_equals_FFQ_exact8_heavy_atom_set",
        "warhead_connected",
        "scaffold_connected",
        "linker_empty",
        "exact_one_direct_scaffold_warhead_boundary",
        "sample_level_role_human_decision_created",
    ):
        if role.get(field) is not True:
            _fail("FORMAL_ROLE_INVARIANT_NOT_TRUE:" + field)
    if role.get("direct_scaffold_warhead_boundary_count") != 1:
        _fail("FORMAL_DIRECT_BOUNDARY_COUNT_INVALID")
    if role.get("boundary") != {
        "atom_id_1": "C2",
        "atom_id_2": "P1",
        "bond_order": "SING",
    }:
        _fail("FORMAL_DIRECT_BOUNDARY_SEMANTICS_DRIFT")
    scaffold = set(EXPECTED_SCAFFOLD)
    linker = set(EXPECTED_LINKER)
    warhead = set(EXPECTED_WARHEAD)
    if scaffold & linker or scaffold & warhead or linker & warhead:
        _fail("FFQ_ROLE_PARTITION_OVERLAP")
    if scaffold | linker | warhead != set(EXPECTED_HEAVY_ATOMS):
        _fail("FFQ_ROLE_PARTITION_NOT_EXHAUSTIVE")
    return {
        "scaffold_atom_ids": list(EXPECTED_SCAFFOLD),
        "linker_atom_ids": [],
        "warhead_atom_ids": list(EXPECTED_WARHEAD),
        "role_profile": EXPECTED_ROLE_PROFILE,
        "FFQ_exact8_heavy_atom_set": list(EXPECTED_HEAVY_ATOMS),
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "scaffold_connected": True,
        "warhead_connected": True,
        "linker_exactly_empty": True,
        "direct_scaffold_warhead_boundary": {
            "warhead_atom_id": "C2",
            "scaffold_atom_id": "P1",
            "bond_order": "SING",
        },
        "sample_level_role_decision_exists_in_source": True,
        "sample_level_role_decision_created_by_ingestion": False,
    }


def validate_formal_decision_v1(formal: Mapping[str, Any]) -> dict[str, object]:
    if formal.get("schema_version") != "covapie_ffq_formal_human_decision_v1":
        _fail("FORMAL_DECISION_SCHEMA_VERSION_INVALID")
    if formal.get("decision_status") != "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION":
        _fail("FORMAL_DECISION_STATUS_INVALID")
    if formal.get("human_review_decision_created") is not True:
        _fail("FORMAL_HUMAN_DECISION_NOT_CREATED")
    if formal.get("human_approval_recorded") is not True:
        _fail("FORMAL_HUMAN_APPROVAL_NOT_RECORDED")
    if formal.get("review_unit_id") != EXPECTED_REVIEW_UNIT_ID:
        _fail("FORMAL_REVIEW_UNIT_ID_INVALID")
    if formal.get("ligand_component_id") != "FFQ":
        _fail("FORMAL_LIGAND_COMPONENT_INVALID")
    approval = formal.get("human_approval")
    if type(approval) is not dict or (
        approval.get("approval_recorded") is not True
        or approval.get("reviewer_id") != "fmx"
        or approval.get("attestation") != "A–J 全部批准，按推荐值执行"
        or approval.get("overall_decision")
        != "APPROVE_ALL_RECOMMENDED_SAMPLE_LEVEL_DECISIONS"
        or type(approval.get("approved_at_utc")) is not str
    ):
        _fail("FORMAL_HUMAN_APPROVAL_FIELDS_INVALID")
    unit = formal.get("unit_level_human_decisions")
    if type(unit) is not dict or (
        unit.get("training_domain_relevance_decision") != EXPECTED_DOMAIN
        or unit.get("chemistry_identity_decision") != EXPECTED_CHEMISTRY
        or unit.get("chemistry_negative") is not False
        or unit.get("task_domain_negative") is not False
        or unit.get("distance_only_inference") is not False
    ):
        _fail("FORMAL_UNIT_DECISION_SEMANTICS_INVALID")

    raw_events = formal.get("event_level_human_decisions")
    if type(raw_events) is not list or len(raw_events) != 8:
        _fail("FORMAL_EXACT8_EVENT_COUNT_INVALID")
    event_ids = [event.get("canonical_event_id") for event in raw_events]
    if any(type(event_id) is not str or not event_id for event_id in event_ids):
        _fail("FORMAL_EVENT_ID_INVALID")
    if len(set(event_ids)) != 8:
        _fail("FORMAL_EVENT_ID_DUPLICATE")
    events: list[dict[str, object]] = []
    counts = {"3VCY": 0, "4R7U": 0}
    for raw in raw_events:
        if type(raw) is not dict:
            _fail("FORMAL_EVENT_NOT_OBJECT")
        pdb_id = raw.get("pdb_id")
        if pdb_id not in counts:
            _fail("FORMAL_EVENT_PDB_OUTSIDE_EXACT_TWO")
        counts[str(pdb_id)] += 1
        if raw.get("chemistry_identity") != EXPECTED_CHEMISTRY:
            if pdb_id == "4R7U":
                _fail("FFQ_4R7U_CHEMISTRY_POSITIVE_SEMANTICS_LOST")
            _fail("FORMAL_EVENT_CHEMISTRY_IDENTITY_DRIFT")
        include = pdb_id == "3VCY"
        expected_token = "INCLUDE" if include else "EXCLUDE_FROM_TRAINING_ONLY"
        if raw.get("event_training_use_decision") != expected_token:
            _fail("FORMAL_EVENT_TRAINING_USE_TOKEN_DRIFT:" + str(pdb_id))
        if not include:
            if not (
                raw.get("negative_chemistry") is False
                and raw.get("task_domain_negative") is False
                and raw.get("distance_threshold_rejection") is False
                and raw.get("exclusion_reason") == EXPECTED_EXCLUSION_REASON
            ):
                _fail("FFQ_4R7U_CHEMISTRY_POSITIVE_SEMANTICS_LOST")
        events.append(
            {
                "canonical_event_id": raw["canonical_event_id"],
                "pdb_id": pdb_id,
                "completed_lane": (
                    "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
                    if include
                    else "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
                ),
                "formal_event_training_use_decision": expected_token,
                "chemistry_identity": EXPECTED_CHEMISTRY,
                "chemistry_known_positive": True,
                "negative_chemistry": False,
                "task_domain_negative": False,
                "distance_threshold_rejection": False,
                "runtime_negative": False,
                "training_use_allowed": include,
                "model_supervision_usable": None if include else False,
                "training_exclusion_scope": (
                    "NONE" if include else "EXCLUDE_FROM_TRAINING_ONLY"
                ),
                "training_exclusion_reason": (
                    "" if include else EXPECTED_EXCLUSION_REASON
                ),
                "independent_POST_geometry_human_decision_available": not include,
                "POST_geometry_source_evidence_status": (
                    "PRESENT_IN_UPSTREAM_EVIDENCE_LINEAGE_NOT_REAUTHORIZED_HERE"
                ),
                "POST_geometry_training_label_available_now": False,
                "POST_geometry_training_label_blocking_reasons": [
                    "TRAINING_ADMISSION_ABSENT",
                    "CURRENT11_DIRECT_PROFILE_TENSORIZER_INTEGRATION_ABSENT",
                ],
                "training_admitted": False,
                "training_materialization_allowed_now": False,
                "candidate_for_future_training_admission": include,
                "future_training_admission_status": (
                    "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"
                    if include
                    else "HUMAN_EXCLUDE_FROM_TRAINING_ONLY"
                ),
                "current_runtime_model_usable": False,
            }
        )
    if counts != {"3VCY": 4, "4R7U": 4}:
        _fail("FORMAL_EXACT4_BY_PDB_COUNT_INVALID")
    events.sort(key=lambda event: str(event["canonical_event_id"]))

    reactive = formal.get("reactive_pair_human_decision")
    precursor = formal.get("precursor_mapping_context")
    if type(reactive) is not dict or reactive != {
        "protein_residue": "CYS",
        "protein_atom": "SG",
        "post_ligand_component": "FFQ",
        "post_ligand_atom": "C1",
        "reactive_pair_decision": "CONFIRMED",
        "sample_level_reactive_pair_human_decision_created": True,
        "reusable_project_level_rule_created": False,
    }:
        _fail("FORMAL_REACTIVE_PAIR_SEMANTICS_DRIFT")
    if type(precursor) is not dict or (
        precursor.get("precursor_component") != "FCN"
        or precursor.get("precursor_reactive_atom") != "C2"
        or precursor.get("post_component") != "FFQ"
        or precursor.get("post_reactive_atom") != "C1"
        or precursor.get("mapping_authority_created") is not False
    ):
        _fail("FORMAL_PRECURSOR_CONTEXT_DRIFT")
    role = _validate_role_decision(formal.get("role_human_decision"))

    family = formal.get("reaction_family_candidate_human_decision")
    if type(family) is not dict or (
        family.get("reaction_family_candidate_id")
        != EXPECTED_REACTION_FAMILY_CANDIDATE_ID
        or family.get("sample_level_reaction_family_candidate_decision")
        != "ACCEPTED_FOR_PROJECT_LEVEL_AUTHORITY_REVIEW"
        or family.get("candidate_status")
        != "HUMAN_ACCEPTED_CANDIDATE_NOT_REGISTERED"
        or family.get("reaction_family_authority_created") is not False
        or family.get("reaction_family_registration_performed") is not False
        or family.get("reusable_reaction_family_authority_created") is not False
    ):
        _fail("FORMAL_REACTION_FAMILY_CANDIDATE_BOUNDARY_INVALID")
    rule = formal.get("warhead_rule_candidate_human_decision")
    if type(rule) is not dict or (
        rule.get("warhead_rule_candidate_id") != EXPECTED_WARHEAD_RULE_CANDIDATE_ID
        or rule.get("sample_level_warhead_rule_candidate_decision")
        != "ACCEPTED_FOR_PROJECT_LEVEL_AUTHORITY_REVIEW"
        or rule.get("candidate_status")
        != "HUMAN_ACCEPTED_CANDIDATE_NOT_REGISTERED"
        or rule.get("warhead_rule_authority_created") is not False
        or rule.get("warhead_rule_registration_performed") is not False
        or rule.get("approved_warhead_rule_created") is not False
    ):
        _fail("FORMAL_WARHEAD_RULE_CANDIDATE_BOUNDARY_INVALID")
    warhead_family = formal.get("warhead_family_human_decision")
    reusable = formal.get("reusable_authority_scope_human_decision")
    if type(warhead_family) is not dict or (
        warhead_family.get("warhead_family_decision") != "DEFERRED"
        or warhead_family.get("warhead_family_authority_created") is not False
    ):
        _fail("FORMAL_WARHEAD_FAMILY_NOT_DEFERRED")
    if type(reusable) is not dict or (
        reusable.get("reusable_authority_scope_decision") != "DEFERRED"
        or reusable.get("reusable_chemistry_authority_created") is not False
    ):
        _fail("FORMAL_REUSABLE_AUTHORITY_NOT_DEFERRED")
    if (
        formal.get("SMARTS_status") != "NOT_MATERIALIZED"
        or formal.get("approved_warhead_smarts") != ""
        or formal.get("SMARTS_generation_performed") is not False
    ):
        _fail("FORMAL_SMARTS_BOUNDARY_INVALID")
    masks = formal.get("canonical_V1_mask_boundary")
    if type(masks) is not dict or (
        masks.get("semantic_long_names")
        != [row[1] for row in CANONICAL_TASKS]
        or masks.get("task_count") != 5
        or masks.get("mask_changed") is not False
        or masks.get("new_mask_added") is not False
    ):
        _fail("FORMAL_CANONICAL_EXACT5_MASK_BOUNDARY_INVALID")
    return {
        "approval": dict(approval),
        "events": events,
        "role": role,
    }


def verify_bound_inputs_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
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
        "formal_FFQ_human_decision",
    )
    formal = json.loads(formal_payload)
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
                "verified": True,
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
    approval = normalized["approval"]
    return {
        "formal": formal,
        "normalized": normalized,
        "formal_decision_binding": {
            "path": FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
            "path_namespace": "repository_parent_relative",
            "byte_count": len(formal_payload),
            "sha256": _sha(formal_payload),
            "sha256_scope": "file_bytes",
            "decision_status": formal["decision_status"],
            "reviewer_id": approval["reviewer_id"],
            "approved_at_utc": approval["approved_at_utc"],
            "attestation": approval["attestation"],
            "overall_decision": approval["overall_decision"],
            "verification_status": "MATCHED",
        },
        "immutable_repository_bindings": immutable_bindings,
        "runtime_contract": runtime_contract,
        "dry_run_artifact_is_authority": False,
        "dry_run_artifact_consumed": False,
    }


def _canonical_task_contract() -> dict[str, object]:
    return {
        "global_canonical_tasks": [
            {
                "task_id": task_id,
                "semantic_name": semantic,
                "display_alias": alias,
                "generated_roles": list(generated),
                "fixed_or_seed_roles": list(fixed),
            }
            for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "canonical_task_vocabulary_changed": False,
        "new_task_added": False,
        "direct_profile_applicable_task_ids": list(DIRECT_VALID_TASK_IDS),
        "direct_profile_applicable_task_count": 3,
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


def _task_applicability_with_targets() -> list[dict[str, object]]:
    role_atoms = {
        "scaffold": EXPECTED_SCAFFOLD,
        "linker": EXPECTED_LINKER,
        "warhead": EXPECTED_WARHEAD,
    }
    generated_by_task = {row[0]: row[3] for row in CANONICAL_TASKS}
    rows: list[dict[str, object]] = []
    for task_id, semantic, alias, applicable, reason in (
        DIRECT_PROFILE_TASK_APPLICABILITY
    ):
        target = [
            atom
            for role in generated_by_task[task_id]
            for atom in role_atoms[role]
        ]
        rows.append(
            {
                "task_id": task_id,
                "semantic_name": semantic,
                "display_alias": alias,
                "profile_applicable": applicable,
                "applicability_reason": reason,
                "metadata_derived_target_atom_ids": target,
                "training_mask_target_available_now": False,
            }
        )
    return rows


def _authority_boundary() -> dict[str, bool]:
    return {
        "formal_human_decision_modified": False,
        "sample_level_human_decision_exists_in_source": True,
        "sample_level_human_decision_created_by_ingestion": False,
        "legacy_human_overlay_modified": False,
        "sample_decision_ingestion_snapshot_created": True,
        "training_admission_created": False,
        "training_dataset_changed": False,
        "positive_runtime_authority_created": False,
        "negative_runtime_authority_created": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_family_authority_created": False,
        "reusable_chemistry_authority_created": False,
        "SMARTS_generation_performed": False,
        "split_changed": False,
        "runtime_admission_changed": False,
        "tensorizer_integration_performed": False,
        "model_architecture_changed": False,
        "training_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "network_performed": False,
    }


def _build_snapshot(bound: Mapping[str, Any]) -> dict[str, object]:
    normalized = bound["normalized"]
    formal = bound["formal"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_role": "ADDITIVE_IMMUTABLE_FFQ_COMPLETED_HUMAN_DECISION_SUCCESSOR",
        "formal_decision_binding": bound["formal_decision_binding"],
        "dry_run_artifact_is_authority": False,
        "dry_run_artifact_consumed": False,
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "FFQ",
        "authority_provenance": {
            "authority_source": "FORMAL_FFQ_HUMAN_DECISION",
            "authority_scope": "SAMPLE_LEVEL_EXACT8",
            "authority_ingested": True,
            "authority_created_by_this_successor": False,
            "sample_level_human_decision_exists_in_source": True,
            "sample_level_human_decision_created_by_ingestion": False,
            "chemistry_identity_human_decision_exists_in_source": True,
            "chemistry_identity_human_decision_created_by_ingestion": False,
            "reactive_pair_human_decision_exists_in_source": True,
            "reactive_pair_human_decision_created_by_ingestion": False,
            "sample_level_role_decision_exists_in_source": True,
            "sample_level_role_decision_created_by_ingestion": False,
            "event_training_use_human_decision_exists_in_source": True,
            "event_training_use_human_decision_created_by_ingestion": False,
            "successor_provenance_strategy": "SHA_BIND_FORMAL_HUMAN_DECISION",
            "legacy_decision_history_continued": False,
            "overlay_mutation_history_fabricated": False,
        },
        "training_domain_relevance": {
            "value": EXPECTED_DOMAIN,
            "human_decision_exists_in_source": True,
            "human_decision_created_by_ingestion": False,
        },
        "chemistry_identity": {
            "value": EXPECTED_CHEMISTRY,
            "chemistry_known_positive": True,
            "negative_chemistry": False,
            "task_domain_negative": False,
            "human_decision_exists_in_source": True,
            "human_decision_created_by_ingestion": False,
        },
        "events": normalized["events"],
        "reactive_pair": {
            "status": "CONFIRMED",
            "protein": {"residue_name": "CYS", "atom_id": "SG"},
            "post_ligand": {"component_id": "FFQ", "atom_id": "C1"},
            "precursor_context": {"component_id": "FCN", "atom_id": "C2"},
            "human_decision_exists_in_source": True,
            "human_decision_created_by_ingestion": False,
            "reusable_project_level_rule_created": False,
        },
        "role_decision": normalized["role"],
        "reaction_family_candidate": {
            "candidate_id": EXPECTED_REACTION_FAMILY_CANDIDATE_ID,
            "human_decision": "ACCEPTED_FOR_PROJECT_LEVEL_AUTHORITY_REVIEW",
            "human_accepted_candidate_for_review": True,
            "project_level_authority_available": False,
            "training_class_target_available": False,
            "reaction_family_authority_created_by_ingestion": False,
        },
        "warhead_rule_candidate": {
            "candidate_id": EXPECTED_WARHEAD_RULE_CANDIDATE_ID,
            "human_decision": "ACCEPTED_FOR_PROJECT_LEVEL_AUTHORITY_REVIEW",
            "human_accepted_candidate_for_review": True,
            "project_level_authority_available": False,
            "training_class_target_available": False,
            "warhead_rule_authority_created_by_ingestion": False,
        },
        "deferred_semantics": {
            "warhead_family": "DEFERRED",
            "reusable_project_level_authority": "DEFERRED",
            "SMARTS_status": "NOT_MATERIALIZED",
            "approved_warhead_smarts": "",
        },
        "canonical_task_contract": _canonical_task_contract(),
        "direct_profile_runtime_contract": bound["runtime_contract"],
        "authority_boundary": _authority_boundary(),
        "formal_authority_boundary_source": formal["authority_boundary"],
    }


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    task_cell = _json_cell(_task_applicability_with_targets())
    roles = snapshot["role_decision"]
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        include = event["pdb_id"] == "3VCY"
        rows.append(
            {
                "canonical_event_id": event["canonical_event_id"],
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
                "pdb_id": event["pdb_id"],
                "completed_lane": event["completed_lane"],
                "formal_decision_sha256": FORMAL_DECISION_SHA256,
                "training_domain_human_decision_available": "true",
                "training_domain_relevance_label": EXPECTED_DOMAIN,
                "chemistry_identity_human_decision_available": "true",
                "chemistry_identity_label": EXPECTED_CHEMISTRY,
                "chemistry_known_positive": "true",
                "negative_chemistry": "false",
                "task_domain_negative": "false",
                "distance_threshold_rejection": "false",
                "runtime_negative": "false",
                "reactive_pair_human_decision_available": "true",
                "protein_reactive_atom": "CYS:SG",
                "post_ligand_reactive_atom": "FFQ:C1",
                "precursor_reactive_atom_context": "FCN:C2",
                "scaffold_role_human_decision_available": "true",
                "scaffold_atom_ids_json": _json_cell(list(EXPECTED_SCAFFOLD)),
                "linker_role_human_decision_available": "true",
                "linker_atom_ids_json": "[]",
                "warhead_role_human_decision_available": "true",
                "warhead_atom_ids_json": _json_cell(list(EXPECTED_WARHEAD)),
                "role_profile_human_decision_available": "true",
                "role_profile": EXPECTED_ROLE_PROFILE,
                "formal_event_training_use_decision": event[
                    "formal_event_training_use_decision"
                ],
                "event_training_use_human_decision_available": "true",
                "training_use_allowed": str(include).lower(),
                "independent_POST_geometry_human_decision_available": str(
                    not include
                ).lower(),
                "POST_geometry_source_evidence_status": event[
                    "POST_geometry_source_evidence_status"
                ],
                "model_supervision_usable": "" if include else "false",
                "POST_geometry_training_label_available_now": "false",
                "POST_geometry_training_label_blocking_reason": (
                    "TRAINING_ADMISSION_ABSENT;"
                    "CURRENT11_DIRECT_PROFILE_TENSORIZER_INTEGRATION_ABSENT"
                ),
                "reaction_family_candidate_id": (
                    EXPECTED_REACTION_FAMILY_CANDIDATE_ID
                ),
                "reaction_family_candidate_human_accepted_for_review": "true",
                "reaction_family_training_class_target_available": "false",
                "warhead_rule_candidate_id": EXPECTED_WARHEAD_RULE_CANDIDATE_ID,
                "warhead_rule_candidate_human_accepted_for_review": "true",
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
                "candidate_for_future_training_admission": str(include).lower(),
                "future_training_admission_status": event[
                    "future_training_admission_status"
                ],
                "training_materialization_allowed_now": "false",
                "current_runtime_model_usable": "false",
                "authority_source": "FORMAL_FFQ_HUMAN_DECISION",
                "authority_scope": "SAMPLE_LEVEL_EXACT8",
                "authority_ingested": "true",
                "authority_created_by_this_successor": "false",
            }
        )
    return rows


def build_artifacts_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    bound = verify_bound_inputs_v1(
        repo_root,
        formal_decision_path=formal_decision_path,
        repository_path_overrides=repository_path_overrides,
    )
    snapshot = _build_snapshot(bound)
    snapshot_payload = _json_bytes(snapshot)
    matrix_rows = _matrix_rows(snapshot)
    matrix_payload = _csv_bytes(MATRIX_HEADER, matrix_rows)
    counts = {
        "event_count": 8,
        "3VCY_event_count": 4,
        "4R7U_event_count": 4,
        "3VCY_include_count": 4,
        "4R7U_training_excluded_count": 4,
        "chemistry_positive_count": 8,
        "negative_chemistry_count": 0,
        "task_domain_negative_count": 0,
        "runtime_negative_count": 0,
        "training_admitted_count": 0,
        "runtime_model_usable_count": 0,
        "project_level_family_authority_count": 0,
        "project_level_rule_authority_count": 0,
        "canonical_global_task_count": 5,
        "direct_profile_applicable_task_count": 3,
    }
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "FFQ_COMPLETED_DECISION_AND_EVENT_LABEL_AVAILABILITY_NOT_ADMISSION",
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "immutable_predecessor_and_source_bindings": bound[
            "immutable_repository_bindings"
        ],
        "dry_run_artifact_is_authority": False,
        "dry_run_artifact_consumed": False,
        "canonical_task_contract": _canonical_task_contract(),
        "direct_profile_runtime_contract": bound["runtime_contract"],
        "counts": counts,
        "human_authority_ingestion_semantics": {
            "sample_level_human_decision_exists_in_source": True,
            "sample_level_human_decision_created_by_ingestion": False,
            "authority_source": "FORMAL_FFQ_HUMAN_DECISION",
            "authority_scope": "SAMPLE_LEVEL_EXACT8",
            "authority_ingested": True,
            "authority_created_by_this_successor": False,
        },
        "POST_geometry_semantic_guard": {
            "3VCY_independent_POST_geometry_human_decision_available": False,
            "3VCY_POST_geometry_source_evidence_status": (
                "PRESENT_IN_UPSTREAM_EVIDENCE_LINEAGE_NOT_REAUTHORIZED_HERE"
            ),
            "3VCY_POST_geometry_training_label_available_now": False,
            "4R7U_human_model_supervision_exclusion_preserved": True,
            "distance_threshold_rule_created": False,
        },
        "artifact_bindings": {
            SNAPSHOT: {"sha256": _sha(snapshot_payload)},
            MATRIX: {"sha256": _sha(matrix_payload)},
        },
        "deterministic": True,
        "feature_semantics_audit_required_before_formal_training": True,
        "future_boundaries": {
            "future_reconciliation_successor_required": True,
            "current_historical_reconciliation_modified": False,
            "future_training_admission_required_for_eligible_3VCY_events": True,
            "project_level_family_authority_review_required": True,
            "project_level_warhead_rule_authority_review_required": True,
            "direct_profile_tensorizer_integration_required": True,
        },
        "authority_boundary": _authority_boundary(),
        "ready_for_training": False,
        "ready_for_training_reason": (
            "METADATA_INGESTION_IS_NOT_TRAINING_ADMISSION_AND_CURRENT11_"
            "DIRECT_PROFILE_TENSORIZER_SUPPORT_IS_ABSENT"
        ),
    }
    manifest_payload = _json_bytes(manifest)
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "sample_decision_ingestion_snapshot_created": True,
        "exact8_ingested_snapshot_count": 8,
        "3VCY_future_training_admission_candidate_count": 4,
        "4R7U_chemistry_positive_training_excluded_count": 4,
        "sample_level_human_decisions_available": True,
        "sample_level_human_decisions_created_by_ingestion": False,
        "reaction_family_project_authority_available": False,
        "warhead_rule_project_authority_available": False,
        "warhead_family_deferred": True,
        "reusable_authority_deferred": True,
        "SMARTS_materialized": False,
        "direct_profile_role_labels_ingested": True,
        "current11_tensorizer_direct_profile_supported": False,
        "canonical_global_exact5_retained": True,
        "direct_profile_applicable_tasks": ["A", "B3", "C"],
        "training_admitted_count": 0,
        "runtime_model_usable_count": 0,
        "future_reconciliation_successor_required": True,
        "current_historical_reconciliation_modified": False,
        "feature_semantics_audit_required_before_formal_training": True,
        "ready_for_training": False,
        "ready_for_training_reason": manifest["ready_for_training_reason"],
        "next_boundaries_remain_independent": [
            "reconciliation_successor",
            "project_level_family_and_rule_review",
            "direct_profile_tensorizer_integration",
            "training_admission_and_split",
        ],
        "artifact_sha256_excluding_summary": {
            SNAPSHOT: _sha(snapshot_payload),
            MATRIX: _sha(matrix_payload),
            MANIFEST: _sha(manifest_payload),
        },
        "authority_boundary": _authority_boundary(),
    }
    artifacts = {
        SNAPSHOT: snapshot_payload,
        MATRIX: matrix_payload,
        MANIFEST: manifest_payload,
        SUMMARY: _json_bytes(summary),
    }
    validate_artifacts_v1(artifacts)
    return artifacts


def _require_exact_keys(value: object, keys: Sequence[str], reason: str) -> dict[str, Any]:
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
    }
    if type(value) is dict:
        for key, child in value.items():
            if key in forbidden:
                _fail("DYNAMIC_METADATA_FORBIDDEN:" + key)
            _reject_dynamic_metadata(child)
    elif type(value) is list:
        for child in value:
            _reject_dynamic_metadata(child)


def validate_artifacts_v1(artifacts: Mapping[str, bytes]) -> None:
    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        if (
            type(payload) is not bytes
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or b"\r" in payload
        ):
            _fail("OUTPUT_TEXT_INVARIANT_INVALID:" + name)
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise FFQIngestionSafetyError("OUTPUT_UTF8_INVALID:" + name) from error
    try:
        snapshot = json.loads(artifacts[SNAPSHOT])
        manifest = json.loads(artifacts[MANIFEST])
        summary = json.loads(artifacts[SUMMARY])
        matrix = list(
            csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8")))
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise FFQIngestionSafetyError("OUTPUT_PARSE_FAILED") from error
    _reject_dynamic_metadata(snapshot)
    _reject_dynamic_metadata(manifest)
    _reject_dynamic_metadata(summary)

    snapshot = _require_exact_keys(
        snapshot,
        (
            "schema_version",
            "snapshot_role",
            "formal_decision_binding",
            "dry_run_artifact_is_authority",
            "dry_run_artifact_consumed",
            "review_unit_id",
            "ligand_component_id",
            "authority_provenance",
            "training_domain_relevance",
            "chemistry_identity",
            "events",
            "reactive_pair",
            "role_decision",
            "reaction_family_candidate",
            "warhead_rule_candidate",
            "deferred_semantics",
            "canonical_task_contract",
            "direct_profile_runtime_contract",
            "authority_boundary",
            "formal_authority_boundary_source",
        ),
        "SNAPSHOT_TOP_LEVEL_SCHEMA_INVALID",
    )
    if (
        snapshot["schema_version"] != SNAPSHOT_SCHEMA_VERSION
        or snapshot["snapshot_role"]
        != "ADDITIVE_IMMUTABLE_FFQ_COMPLETED_HUMAN_DECISION_SUCCESSOR"
        or snapshot["review_unit_id"] != EXPECTED_REVIEW_UNIT_ID
        or snapshot["dry_run_artifact_is_authority"] is not False
        or snapshot["dry_run_artifact_consumed"] is not False
    ):
        _fail("SNAPSHOT_IDENTITY_OR_AUTHORITY_INVALID")
    provenance = snapshot["authority_provenance"]
    if (
        provenance.get("authority_ingested") is not True
        or provenance.get("authority_created_by_this_successor") is not False
        or provenance.get("sample_level_human_decision_exists_in_source") is not True
        or provenance.get("sample_level_human_decision_created_by_ingestion")
        is not False
        or provenance.get("successor_provenance_strategy")
        != "SHA_BIND_FORMAL_HUMAN_DECISION"
        or provenance.get("legacy_decision_history_continued") is not False
        or provenance.get("overlay_mutation_history_fabricated") is not False
    ):
        _fail("SNAPSHOT_HUMAN_AUTHORITY_PROVENANCE_INVALID")
    if snapshot["formal_decision_binding"].get("sha256") != FORMAL_DECISION_SHA256:
        _fail("SNAPSHOT_FORMAL_BINDING_INVALID")
    if snapshot["chemistry_identity"] != {
        "value": EXPECTED_CHEMISTRY,
        "chemistry_known_positive": True,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "human_decision_exists_in_source": True,
        "human_decision_created_by_ingestion": False,
    }:
        _fail("SNAPSHOT_CHEMISTRY_IDENTITY_INVALID")
    reactive = snapshot["reactive_pair"]
    if not (
        reactive.get("status") == "CONFIRMED"
        and reactive.get("protein") == {"residue_name": "CYS", "atom_id": "SG"}
        and reactive.get("post_ligand") == {"component_id": "FFQ", "atom_id": "C1"}
        and reactive.get("precursor_context") == {"component_id": "FCN", "atom_id": "C2"}
        and reactive.get("human_decision_created_by_ingestion") is False
    ):
        _fail("SNAPSHOT_REACTIVE_PAIR_INVALID")
    role = snapshot["role_decision"]
    if (
        role.get("scaffold_atom_ids") != list(EXPECTED_SCAFFOLD)
        or role.get("linker_atom_ids") != []
        or role.get("warhead_atom_ids") != list(EXPECTED_WARHEAD)
        or role.get("role_profile") != EXPECTED_ROLE_PROFILE
        or role.get("FFQ_exact8_heavy_atom_set") != list(EXPECTED_HEAVY_ATOMS)
        or role.get("direct_scaffold_warhead_boundary")
        != {"warhead_atom_id": "C2", "scaffold_atom_id": "P1", "bond_order": "SING"}
    ):
        _fail("SNAPSHOT_ROLE_DECISION_INVALID")
    family = snapshot["reaction_family_candidate"]
    if (
        family.get("candidate_id") != EXPECTED_REACTION_FAMILY_CANDIDATE_ID
        or family.get("human_accepted_candidate_for_review") is not True
        or family.get("project_level_authority_available") is not False
        or family.get("training_class_target_available") is not False
        or family.get("reaction_family_authority_created_by_ingestion") is not False
    ):
        _fail("SNAPSHOT_REACTION_FAMILY_BOUNDARY_INVALID")
    rule = snapshot["warhead_rule_candidate"]
    if (
        rule.get("candidate_id") != EXPECTED_WARHEAD_RULE_CANDIDATE_ID
        or rule.get("human_accepted_candidate_for_review") is not True
        or rule.get("project_level_authority_available") is not False
        or rule.get("training_class_target_available") is not False
        or rule.get("warhead_rule_authority_created_by_ingestion") is not False
    ):
        _fail("SNAPSHOT_WARHEAD_RULE_BOUNDARY_INVALID")
    if snapshot["deferred_semantics"] != {
        "warhead_family": "DEFERRED",
        "reusable_project_level_authority": "DEFERRED",
        "SMARTS_status": "NOT_MATERIALIZED",
        "approved_warhead_smarts": "",
    }:
        _fail("SNAPSHOT_DEFERRED_SEMANTICS_INVALID")
    task_contract = snapshot["canonical_task_contract"]
    if (
        task_contract.get("global_canonical_task_count") != 5
        or task_contract.get("direct_profile_applicable_task_ids") != [0, 3, 4]
        or task_contract.get("direct_profile_applicable_task_count") != 3
        or task_contract.get("canonical_task_vocabulary_changed") is not False
        or [row["semantic_name"] for row in task_contract["global_canonical_tasks"]]
        != [row[1] for row in CANONICAL_TASKS]
    ):
        _fail("SNAPSHOT_CANONICAL_TASK_CONTRACT_INVALID")
    runtime = snapshot["direct_profile_runtime_contract"]
    if (
        runtime.get("current11_tensorizer_direct_profile_supported") is not False
        or runtime.get("direct_profile_runtime_primitives_ready") is not True
        or runtime.get("expanded_tensorizer_integration_pending") is not True
        or runtime.get("model_architecture_change_required") is not False
        or runtime.get("direct_valid_canonical_task_ids") != [0, 3, 4]
    ):
        _fail("SNAPSHOT_RUNTIME_CONTRACT_INVALID")
    events = snapshot["events"]
    if type(events) is not list or len(events) != 8:
        _fail("SNAPSHOT_EXACT8_INVALID")
    ids = [event.get("canonical_event_id") for event in events]
    if len(set(ids)) != 8:
        _fail("SNAPSHOT_EVENT_DUPLICATE")
    for event in events:
        include = event.get("pdb_id") == "3VCY"
        if event.get("pdb_id") not in {"3VCY", "4R7U"}:
            _fail("SNAPSHOT_EVENT_PDB_INVALID")
        if (
            event.get("chemistry_identity") != EXPECTED_CHEMISTRY
            or event.get("chemistry_known_positive") is not True
            or event.get("negative_chemistry") is not False
            or event.get("task_domain_negative") is not False
            or event.get("distance_threshold_rejection") is not False
            or event.get("runtime_negative") is not False
            or event.get("training_admitted") is not False
            or event.get("training_materialization_allowed_now") is not False
            or event.get("current_runtime_model_usable") is not False
        ):
            _fail("SNAPSHOT_EVENT_SAFETY_SEMANTICS_INVALID")
        if include:
            if (
                event.get("formal_event_training_use_decision") != "INCLUDE"
                or event.get("completed_lane")
                != "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
                or event.get("training_use_allowed") is not True
                or event.get("model_supervision_usable") is not None
                or event.get("independent_POST_geometry_human_decision_available")
                is not False
                or event.get("candidate_for_future_training_admission") is not True
            ):
                _fail("SNAPSHOT_3VCY_EVENT_INVALID")
        else:
            if (
                event.get("formal_event_training_use_decision")
                != "EXCLUDE_FROM_TRAINING_ONLY"
                or event.get("completed_lane")
                != "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
                or event.get("training_use_allowed") is not False
                or event.get("model_supervision_usable") is not False
                or event.get("training_exclusion_reason")
                != EXPECTED_EXCLUSION_REASON
                or event.get("candidate_for_future_training_admission") is not False
            ):
                _fail("FFQ_4R7U_CHEMISTRY_POSITIVE_SEMANTICS_LOST")
    if sum(event["pdb_id"] == "3VCY" for event in events) != 4:
        _fail("SNAPSHOT_3VCY_COUNT_INVALID")
    if sum(event["pdb_id"] == "4R7U" for event in events) != 4:
        _fail("SNAPSHOT_4R7U_COUNT_INVALID")
    boundary = snapshot["authority_boundary"]
    expected_boundary = _authority_boundary()
    if boundary != expected_boundary:
        _fail("SNAPSHOT_AUTHORITY_BOUNDARY_INVALID")

    if (list(matrix[0].keys()) if matrix else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    if len(matrix) != 8 or len({row["canonical_event_id"] for row in matrix}) != 8:
        _fail("MATRIX_EXACT8_INVALID")
    for row in matrix:
        include = row["pdb_id"] == "3VCY"
        for field in (
            "chemistry_known_positive",
            "training_domain_human_decision_available",
            "chemistry_identity_human_decision_available",
            "reactive_pair_human_decision_available",
            "scaffold_role_human_decision_available",
            "linker_role_human_decision_available",
            "warhead_role_human_decision_available",
            "role_profile_human_decision_available",
            "event_training_use_human_decision_available",
            "authority_ingested",
        ):
            if row[field] != "true":
                _fail("MATRIX_REQUIRED_HUMAN_LABEL_UNAVAILABLE:" + field)
        for field in (
            "negative_chemistry",
            "task_domain_negative",
            "distance_threshold_rejection",
            "runtime_negative",
            "reaction_family_training_class_target_available",
            "warhead_rule_training_class_target_available",
            "warhead_type_target_available",
            "reusable_authority_label_available",
            "POST_geometry_training_label_available_now",
            "training_mask_targets_available_now",
            "current11_tensorizer_direct_profile_supported",
            "training_admitted",
            "training_materialization_allowed_now",
            "current_runtime_model_usable",
            "authority_created_by_this_successor",
        ):
            if row[field] != "false":
                _fail("MATRIX_SAFETY_FLAG_INVALID:" + field)
        if (
            row["global_canonical_task_count"] != "5"
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or row["direct_profile_applicable_task_count"] != "3"
            or json.loads(row["linker_atom_ids_json"]) != []
        ):
            _fail("MATRIX_DIRECT_PROFILE_CONTRACT_INVALID")
        applicability = json.loads(row["canonical_task_applicability_json"])
        if len(applicability) != 5:
            _fail("MATRIX_GLOBAL_TASK_COUNT_INVALID")
        if [item["task_id"] for item in applicability if item["profile_applicable"]] != [0, 3, 4]:
            _fail("MATRIX_DIRECT_APPLICABLE_TASKS_INVALID")
        if applicability[1]["applicability_reason"] != (
            "not_applicable_empty_linker_redundant_with_A"
        ) or applicability[2]["applicability_reason"] != (
            "not_applicable_empty_non_C_fixed_context"
        ):
            _fail("MATRIX_B_OR_B2_NOT_APPLICABLE_REASON_INVALID")
        if row["candidate_for_future_training_admission"] != str(include).lower():
            _fail("MATRIX_FUTURE_ADMISSION_CANDIDATE_INVALID")

    if (
        manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION
        or manifest.get("candidate_publication_file_count") != 7
        or manifest.get("output_artifact_count") != 4
        or manifest.get("deterministic") is not True
        or manifest.get("dry_run_artifact_is_authority") is not False
        or manifest.get("dry_run_artifact_consumed") is not False
        or manifest.get("ready_for_training") is not False
        or manifest.get("feature_semantics_audit_required_before_formal_training")
        is not True
    ):
        _fail("MANIFEST_BOUNDARY_INVALID")
    counts = manifest.get("counts")
    if counts != {
        "event_count": 8,
        "3VCY_event_count": 4,
        "4R7U_event_count": 4,
        "3VCY_include_count": 4,
        "4R7U_training_excluded_count": 4,
        "chemistry_positive_count": 8,
        "negative_chemistry_count": 0,
        "task_domain_negative_count": 0,
        "runtime_negative_count": 0,
        "training_admitted_count": 0,
        "runtime_model_usable_count": 0,
        "project_level_family_authority_count": 0,
        "project_level_rule_authority_count": 0,
        "canonical_global_task_count": 5,
        "direct_profile_applicable_task_count": 3,
    }:
        _fail("MANIFEST_COUNTS_INVALID")
    if manifest.get("authority_boundary") != expected_boundary:
        _fail("MANIFEST_AUTHORITY_BOUNDARY_INVALID")
    bindings = manifest.get("artifact_bindings")
    if bindings != {
        SNAPSHOT: {"sha256": _sha(artifacts[SNAPSHOT])},
        MATRIX: {"sha256": _sha(artifacts[MATRIX])},
    }:
        _fail("MANIFEST_ARTIFACT_BINDINGS_INVALID")
    if (
        summary.get("schema_version") != SUMMARY_SCHEMA_VERSION
        or summary.get("exact8_ingested_snapshot_count") != 8
        or summary.get("3VCY_future_training_admission_candidate_count") != 4
        or summary.get("4R7U_chemistry_positive_training_excluded_count") != 4
        or summary.get("training_admitted_count") != 0
        or summary.get("runtime_model_usable_count") != 0
        or summary.get("ready_for_training") is not False
        or summary.get("authority_boundary") != expected_boundary
    ):
        _fail("SUMMARY_BOUNDARY_INVALID")
    if summary.get("artifact_sha256_excluding_summary") != {
        SNAPSHOT: _sha(artifacts[SNAPSHOT]),
        MATRIX: _sha(artifacts[MATRIX]),
        MANIFEST: _sha(artifacts[MANIFEST]),
    }:
        _fail("SUMMARY_ARTIFACT_BINDINGS_INVALID")


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


def materialize_artifacts_v1(repo_root: Path) -> dict[str, bytes]:
    artifacts = build_artifacts_v1(repo_root)
    output_root = repo_root.resolve() / OUTPUT_ROOT_RELATIVE
    if output_root.exists():
        unexpected = {
            path.name for path in output_root.iterdir() if path.name not in OUTPUT_FILENAMES
        }
        if unexpected:
            _fail("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES")
    for name in OUTPUT_FILENAMES:
        _atomic_write(output_root / name, artifacts[name])
    return artifacts


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    expected = build_artifacts_v1(repo_root)
    output_root = repo_root / OUTPUT_ROOT_RELATIVE
    if not output_root.is_dir():
        _fail("OUTPUT_DIRECTORY_MISSING")
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
    validate_artifacts_v1(observed)
    return {
        "materialized_output_valid": True,
        "output_artifact_count": 4,
        "candidate_publication_file_count": 7,
        "artifact_sha256": {name: _sha(observed[name]) for name in OUTPUT_FILENAMES},
        "formal_decision_sha256": FORMAL_DECISION_SHA256,
        "event_count": 8,
        "3VCY_include_count": 4,
        "4R7U_training_excluded_count": 4,
        "chemistry_positive_count": 8,
        "training_admitted_count": 0,
        "runtime_model_usable_count": 0,
        "legacy_human_overlay_modified": False,
        "current_historical_reconciliation_modified": False,
        "deterministic_rebuild_matches_materialized": True,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    artifacts = materialize_artifacts_v1(repo_root)
    print("sample_decision_ingestion_snapshot_created=true")
    print("output_artifact_count=4")
    print("candidate_publication_file_count=7")
    print("event_count=8")
    print("3VCY_include_count=4")
    print("4R7U_training_excluded_count=4")
    print("training_admitted_count=0")
    print("runtime_model_usable_count=0")
    for name in OUTPUT_FILENAMES:
        print(name + "_sha256=" + _sha(artifacts[name]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
