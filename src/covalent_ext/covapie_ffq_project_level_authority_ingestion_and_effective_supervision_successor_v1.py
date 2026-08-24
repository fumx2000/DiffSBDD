"""Bind published FFQ project authorities to exact event supervision.

This successor consumes byte or mapping inputs supplied by its caller and
returns deterministic in-memory metadata.  It performs no filesystem I/O,
registry update, tensorization, geometry promotion, runtime admission, or
training operation.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1
    as completed_ingestion,
)
from covalent_ext import (
    covapie_ffq_reaction_family_authority_creator_v1 as family_creator,
)
from covalent_ext import (
    covapie_ffq_warhead_rule_authority_creator_v1 as rule_creator,
)
from covalent_ext import (
    covapie_k36_w1_reaction_family_and_warhead_rule_authority_creator_v1
    as k36_authority_creator,
)


__all__ = (
    "FFQEffectiveSupervisionValidationError",
    "SUCCESSOR_SCHEMA_VERSION",
    "EFFECTIVE_SUPERVISION_RECORD_SCHEMA_VERSION",
    "COMPLETED_DECISION_SNAPSHOT_SHA256",
    "EVENT_TASK_LABEL_AVAILABILITY_SHA256",
    "REACTION_FAMILY_AUTHORITY_FILE_SHA256",
    "REACTION_FAMILY_AUTHORITY_CANONICAL_PAYLOAD_SHA256",
    "REACTION_FAMILY_AUTHORITY_ID",
    "REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256",
    "WARHEAD_RULE_AUTHORITY_FILE_SHA256",
    "WARHEAD_RULE_AUTHORITY_CANONICAL_PAYLOAD_SHA256",
    "WARHEAD_RULE_AUTHORITY_ID",
    "WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256",
    "K36_PUBLISHED_AUTHORITY_SOURCES_V1",
    "strict_parse_authority_json_v1",
    "effective_supervision_record_sha256_v1",
    "validate_covapie_ffq_project_level_authority_effective_supervision_v1",
    "build_covapie_ffq_project_level_authority_effective_supervision_v1",
)


SUCCESSOR_SCHEMA_VERSION = (
    "covapie_ffq_project_level_authority_ingestion_and_"
    "effective_supervision_successor_v1"
)
EFFECTIVE_SUPERVISION_RECORD_SCHEMA_VERSION = (
    "covapie_ffq_project_level_authority_effective_supervision_record_v1"
)

COMPLETED_DECISION_SNAPSHOT_BYTE_COUNT = 18032
COMPLETED_DECISION_SNAPSHOT_SHA256 = (
    "6b7c7f4f4c93782d4b61b43cc698372981ec078000fd28207b97294a3694f977"
)
EVENT_TASK_LABEL_AVAILABILITY_BYTE_COUNT = 21239
EVENT_TASK_LABEL_AVAILABILITY_SHA256 = (
    "781972cbee68403805bb0266db65221b0973cb61e666925264dc0d50524090a0"
)

REACTION_FAMILY_AUTHORITY_FILE_BYTE_COUNT = 7778
REACTION_FAMILY_AUTHORITY_FILE_SHA256 = (
    "d79658a33d910e7ca828247706d2690697c9e988f66fac53c8265fae020b7f62"
)
REACTION_FAMILY_AUTHORITY_CANONICAL_PAYLOAD_SHA256 = (
    "6007c9419d51799f33e5cd948a9228abc34f4a6fbea283f94375b1e9b126a6ca"
)
REACTION_FAMILY_AUTHORITY_ID = (
    "COVAPIE_CYS_SG_REACTION_FAMILY_2FEF2EDDFC385C78"
)
REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256 = (
    "2fef2eddfc385c78f9386b5973984fd6df992416a950d5fa9cdfd6a07d485bc7"
)

WARHEAD_RULE_AUTHORITY_FILE_BYTE_COUNT = 8131
WARHEAD_RULE_AUTHORITY_FILE_SHA256 = (
    "d98b47697c1607369e46113325dd19757aa3e548d99b2f0845701c3c48ffdb07"
)
WARHEAD_RULE_AUTHORITY_CANONICAL_PAYLOAD_BYTE_COUNT = 8130
WARHEAD_RULE_AUTHORITY_CANONICAL_PAYLOAD_SHA256 = (
    "1a8d8751e50ad6eb427c02fb49731e00a2d688d4dee7dd7e936f694b569953b6"
)
WARHEAD_RULE_AUTHORITY_ID = "COVAPIE_CYS_SG_WARHEAD_RULE_8162EFF17624BD4A"
WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256 = (
    "8162eff17624bd4a080e24e0a2537a840baa68c6c2f28cd78a91fbf23cc8998a"
)

FAMILY_CREATOR_SOURCE_SHA256 = (
    "f426d58696b6a15acaf5a4e09ddeed63512c3398b8fab2a182ba5ed50ada1496"
)
WARHEAD_RULE_CREATOR_SOURCE_SHA256 = (
    "d7ad9866f5311ff6b534a9331f23c69e26db02bdea3463311fb04e74e4b86a82"
)
FAMILY_AUTHORITY_RECEIPT_FILE_SHA256 = (
    "e8d2b03ddde42cc60bb2833861e1f7f26e7f87c751e4486bc16d9af48bde3780"
)
WARHEAD_RULE_AUTHORITY_RECEIPT_FILE_SHA256 = (
    "1412dc3893f6e7e3d9bba70c8365e34d79fa84f8521a0789a2be9f9b516f8c99"
)

K36_PUBLISHED_AUTHORITY_SOURCES_V1 = (
    {
        "source_path": (
            "covapie-state/manual-review/recovered7-targeted-chemistry-review-v1/"
            "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
            "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92/"
            "reaction_family_authority_v1.json"
        ),
        "source_sha256": (
            "5eb39ac01770dbb8721a48d7ae6bf77fc6cb07493ca00a0eb5756ebf10921461"
        ),
        "authority_kind": "reaction_family",
        "authority_id": "COVAPIE_CYS_SG_REACTION_FAMILY_A06FD171EB8080D8",
        "semantic_signature_sha256": (
            "a06fd171eb8080d8cea9caf5001f7862fd60410d53a87b908aa8cc40117db52e"
        ),
    },
    {
        "source_path": (
            "covapie-state/manual-review/recovered7-targeted-chemistry-review-v1/"
            "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_"
            "83E9C7B9D43444D7E50FBFD7E6C3DAFEF5E0DC92CF1A7C571E3F4E3FE4E08D92/"
            "warhead_rule_authority_v1.json"
        ),
        "source_sha256": (
            "1b8927693386aa8c72fed8677d59bdb3b5b56d4e89a09d88a908341fec0a19b2"
        ),
        "authority_kind": "warhead_rule",
        "authority_id": "COVAPIE_CYS_SG_WARHEAD_RULE_855163C772D500C7",
        "semantic_signature_sha256": (
            "855163c772d500c7ed5471bdf510316d2cdbd3ebbcabde9a859d5a17031ac1c9"
        ),
    },
)

_CANONICAL_EVENT_IDS = (
    "COVAPIE_CYS_SG_EVENT_V1:3VCY:A:CYS:116-:SG:E:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:3VCY:B:CYS:116-:SG:J:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:3VCY:C:CYS:116-:SG:O:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:3VCY:D:CYS:116-:SG:T:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4R7U:A:CYS:116-:SG:F:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4R7U:B:CYS:116-:SG:J:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4R7U:C:CYS:116-:SG:M:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4R7U:D:CYS:116-:SG:Q:FFQ:C1",
)
_GLOBAL_TASKS = (
    (0, "warhead_only", "A"),
    (1, "linker_plus_warhead", "B"),
    (2, "scaffold_plus_warhead", "B2"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)
_VALID_TASK_IDS = (0, 3, 4)
_NOT_APPLICABLE_TASK_IDS = (1, 2)
_SCAFFOLD_ATOM_IDS = ("O2", "O3", "O4", "P1")
_LINKER_ATOM_IDS: tuple[str, ...] = ()
_WARHEAD_ATOM_IDS = ("C1", "C2", "C3", "O1")
_ACTIVE_WARHEAD_SEMANTICS = "REACTION_COMPETENT_ACTIVE_WARHEAD_V1"
_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
_NOT_ESTABLISHED = "NOT_ESTABLISHED"
_SOURCE_FAMILY_CANDIDATE_ID = (
    "COVAPIE_CYS_SG_REACTION_FAMILY_B1FD795D4D442304"
)
_SOURCE_RULE_CANDIDATE_ID = (
    "COVAPIE_CYS_SG_WARHEAD_RULE_B96D4E846C704691"
)

_RESULT_FIELDS = frozenset(
    (
        "effective_supervision_records",
        "ingestion_effective_authority_summary",
        "source_authority_provenance",
    )
)
_RECORD_FIELDS = frozenset(
    (
        "effective_supervision_schema_version",
        "canonical_event_id",
        "pdb_id",
        "completed_lane",
        "reaction_family_authority_id",
        "reaction_family_semantic_signature_sha256",
        "reaction_family_authority_established",
        "warhead_rule_authority_id",
        "warhead_rule_semantic_signature_sha256",
        "warhead_rule_authority_established",
        "project_level_chemistry_authority_linkage_complete",
        "target_residue_name",
        "target_residue_atom_id",
        "ligand_component_id",
        "ligand_reactive_atom_id",
        "precursor_component_id",
        "precursor_reactive_atom_id",
        "active_warhead_semantics",
        "reviewed_warhead_atom_ids",
        "reviewed_scaffold_atom_ids",
        "reviewed_linker_atom_ids",
        "role_profile",
        "formal_event_training_use_decision",
        "training_use_allowed",
        "human_training_exclusion_preserved",
        "non_geometry_chemistry_supervision_authority_available",
        "non_geometry_training_candidate",
        "candidate_for_future_training_admission",
        "independent_POST_geometry_human_decision_available",
        "POST_geometry_training_label_available_now",
        "POST_geometry_supervision_authority_status",
        "PRE_geometry_supervision_authority_status",
        "reaction_family_authority_target_available",
        "warhead_rule_authority_target_available",
        "warhead_type_target_available",
        "valid_task_ids",
        "not_applicable_task_ids",
        "training_mask_targets_available_now",
        "current11_tensorizer_direct_profile_supported",
        "training_admitted",
        "training_materialization_allowed_now",
        "model_supervision_usable",
        "current_runtime_model_usable",
        "effective_supervision_record_sha256",
    )
)


class FFQEffectiveSupervisionValidationError(ValueError):
    """Raised unless exact FFQ authority linkage is proven."""


def _fail(reason: str) -> None:
    raise FFQEffectiveSupervisionValidationError(reason)


def _require_exact_dict_fields(
    value: object, fields: frozenset[str], reason: str
) -> dict[str, Any]:
    if type(value) is not dict or frozenset(value) != fields:
        _fail(reason)
    return value


def _reject_nonfinite_json_constant(value: str) -> None:
    _fail("JSON_NONFINITE_NUMBER_REJECTED:" + value)


def _parse_finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        _fail("JSON_NONFINITE_NUMBER_REJECTED")
    return parsed


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("JSON_DUPLICATE_KEY:" + key)
        result[key] = value
    return result


def _strict_parse_json_value(payload: bytes, label: str) -> Any:
    if type(payload) is not bytes:
        _fail(label + "_BYTES_REQUIRED")
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload:
        _fail(label + "_TEXT_SAFETY_INVALID")
    try:
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_nonfinite_json_constant,
            parse_float=_parse_finite_json_float,
        )
    except FFQEffectiveSupervisionValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as error:
        raise FFQEffectiveSupervisionValidationError(label + "_JSON_INVALID") from error


def strict_parse_authority_json_v1(payload: bytes) -> dict[str, Any]:
    """Strictly parse authority JSON while treating object order as semantic-free."""

    value = _strict_parse_json_value(payload, "AUTHORITY")
    if type(value) is not dict:
        _fail("AUTHORITY_JSON_TOP_LEVEL_OBJECT_REQUIRED")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise FFQEffectiveSupervisionValidationError(
            "EFFECTIVE_SUPERVISION_CANONICAL_JSON_INVALID"
        ) from error


def effective_supervision_record_sha256_v1(record: Mapping[str, Any]) -> str:
    """Hash one record canonically, excluding its declared hash field."""

    if not isinstance(record, Mapping):
        _fail("EFFECTIVE_SUPERVISION_RECORD_MAPPING_REQUIRED")
    if "effective_supervision_record_sha256" not in record:
        _fail("EFFECTIVE_SUPERVISION_RECORD_SHA256_FIELD_MISSING")
    payload = {
        key: value
        for key, value in record.items()
        if key != "effective_supervision_record_sha256"
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _validate_published_snapshot(payload: bytes) -> dict[str, Any]:
    snapshot = _strict_parse_json_value(payload, "COMPLETED_DECISION_SNAPSHOT")
    if type(snapshot) is not dict:
        _fail("COMPLETED_DECISION_SNAPSHOT_OBJECT_REQUIRED")
    events = snapshot.get("events")
    if type(events) is not list or len(events) != 8:
        _fail("COMPLETED_DECISION_SNAPSHOT_EXACT8_REQUIRED")
    ids = [event.get("canonical_event_id") for event in events if type(event) is dict]
    if len(ids) != 8 or len(set(ids)) != 8 or tuple(ids) != _CANONICAL_EVENT_IDS:
        _fail("COMPLETED_DECISION_SNAPSHOT_EVENT_INVENTORY_INVALID")
    if (
        snapshot.get("schema_version") != completed_ingestion.SNAPSHOT_SCHEMA_VERSION
        or snapshot.get("review_unit_id") != completed_ingestion.EXPECTED_REVIEW_UNIT_ID
        or snapshot.get("ligand_component_id") != "FFQ"
        or snapshot.get("reactive_pair")
        != {
            "status": "CONFIRMED",
            "protein": {"residue_name": "CYS", "atom_id": "SG"},
            "post_ligand": {"component_id": "FFQ", "atom_id": "C1"},
            "precursor_context": {"component_id": "FCN", "atom_id": "C2"},
            "human_decision_exists_in_source": True,
            "human_decision_created_by_ingestion": False,
            "reusable_project_level_rule_created": False,
        }
    ):
        _fail("COMPLETED_DECISION_SNAPSHOT_IDENTITY_INVALID")
    role = snapshot.get("role_decision")
    if not isinstance(role, Mapping) or (
        tuple(role.get("scaffold_atom_ids", ())) != _SCAFFOLD_ATOM_IDS
        or tuple(role.get("linker_atom_ids", ())) != _LINKER_ATOM_IDS
        or tuple(role.get("warhead_atom_ids", ())) != _WARHEAD_ATOM_IDS
        or role.get("role_profile") != _ROLE_PROFILE
    ):
        _fail("COMPLETED_DECISION_SNAPSHOT_ROLE_PARTITION_INVALID")
    family = snapshot.get("reaction_family_candidate")
    rule = snapshot.get("warhead_rule_candidate")
    if not isinstance(family, Mapping) or (
        family.get("candidate_id") != _SOURCE_FAMILY_CANDIDATE_ID
        or family.get("human_accepted_candidate_for_review") is not True
    ):
        _fail("COMPLETED_DECISION_SNAPSHOT_FAMILY_LINEAGE_INVALID")
    if not isinstance(rule, Mapping) or (
        rule.get("candidate_id") != _SOURCE_RULE_CANDIDATE_ID
        or rule.get("human_accepted_candidate_for_review") is not True
    ):
        _fail("COMPLETED_DECISION_SNAPSHOT_RULE_LINEAGE_INVALID")
    tasks = snapshot.get("canonical_task_contract")
    runtime = snapshot.get("direct_profile_runtime_contract")
    if not isinstance(tasks, Mapping) or (
        tasks.get("global_canonical_task_count") != 5
        or tasks.get("direct_profile_applicable_task_ids") != [0, 3, 4]
        or [row.get("semantic_name") for row in tasks.get("global_canonical_tasks", [])]
        != [row[1] for row in _GLOBAL_TASKS]
    ):
        _fail("COMPLETED_DECISION_SNAPSHOT_TASK_CONTRACT_INVALID")
    if not isinstance(runtime, Mapping) or (
        runtime.get("role_profile") != _ROLE_PROFILE
        or runtime.get("current11_tensorizer_direct_profile_supported") is not False
        or runtime.get("direct_valid_canonical_task_ids") != [0, 3, 4]
    ):
        _fail("COMPLETED_DECISION_SNAPSHOT_RUNTIME_CONTRACT_INVALID")
    for event in events:
        if type(event) is not dict:
            _fail("COMPLETED_DECISION_SNAPSHOT_EVENT_OBJECT_REQUIRED")
        include = event.get("pdb_id") == "3VCY"
        expected = {
            "completed_lane": (
                "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
                if include
                else "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
            ),
            "formal_event_training_use_decision": (
                "INCLUDE" if include else "EXCLUDE_FROM_TRAINING_ONLY"
            ),
            "training_use_allowed": include,
            "candidate_for_future_training_admission": include,
            "independent_POST_geometry_human_decision_available": not include,
            "model_supervision_usable": None if include else False,
        }
        if event.get("pdb_id") not in ("3VCY", "4R7U") or any(
            event.get(key) != value for key, value in expected.items()
        ):
            _fail("COMPLETED_DECISION_SNAPSHOT_TRAINING_DECISION_INVALID")
        for field, expected_value in (
            ("chemistry_known_positive", True),
            ("negative_chemistry", False),
            ("task_domain_negative", False),
            ("distance_threshold_rejection", False),
            ("runtime_negative", False),
            ("POST_geometry_training_label_available_now", False),
            ("training_admitted", False),
            ("training_materialization_allowed_now", False),
            ("current_runtime_model_usable", False),
        ):
            if event.get(field) is not expected_value:
                _fail("COMPLETED_DECISION_SNAPSHOT_EVENT_BOUNDARY_INVALID:" + field)
    if len(payload) != COMPLETED_DECISION_SNAPSHOT_BYTE_COUNT or (
        hashlib.sha256(payload).hexdigest() != COMPLETED_DECISION_SNAPSHOT_SHA256
    ):
        _fail("COMPLETED_DECISION_SNAPSHOT_FILE_BINDING_INVALID")
    return snapshot


def _strict_json_cell(value: str, label: str) -> Any:
    return _strict_parse_json_value(value.encode("utf-8"), label)


def _validate_published_matrix(payload: bytes) -> list[dict[str, str]]:
    if type(payload) is not bytes:
        _fail("EVENT_TASK_LABEL_AVAILABILITY_BYTES_REQUIRED")
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload or b"\r" in payload:
        _fail("EVENT_TASK_LABEL_AVAILABILITY_TEXT_SAFETY_INVALID")
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""), strict=True)
        rows = [dict(row) for row in reader]
    except (UnicodeDecodeError, csv.Error) as error:
        raise FFQEffectiveSupervisionValidationError(
            "EVENT_TASK_LABEL_AVAILABILITY_CSV_INVALID"
        ) from error
    if reader.fieldnames != list(completed_ingestion.MATRIX_HEADER):
        _fail("EVENT_TASK_LABEL_AVAILABILITY_HEADER_INVALID")
    if len(rows) != 8:
        _fail("EVENT_TASK_LABEL_AVAILABILITY_EXACT8_REQUIRED")
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        _fail("EVENT_TASK_LABEL_AVAILABILITY_ROW_SHAPE_INVALID")
    ids = tuple(row["canonical_event_id"] for row in rows)
    if len(set(ids)) != 8 or ids != _CANONICAL_EVENT_IDS:
        _fail("EVENT_TASK_LABEL_AVAILABILITY_EVENT_INVENTORY_INVALID")
    expected_task_applicability = [
        {
            "task_id": task_id,
            "semantic_name": semantic,
            "display_alias": alias,
            "profile_applicable": task_id in _VALID_TASK_IDS,
        }
        for task_id, semantic, alias in _GLOBAL_TASKS
    ]
    for row in rows:
        include = row["pdb_id"] == "3VCY"
        if row["pdb_id"] not in ("3VCY", "4R7U"):
            _fail("EVENT_TASK_LABEL_AVAILABILITY_PDB_INVALID")
        exact_values = {
            "completed_lane": (
                "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
                if include
                else "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
            ),
            "formal_event_training_use_decision": (
                "INCLUDE" if include else "EXCLUDE_FROM_TRAINING_ONLY"
            ),
            "training_use_allowed": str(include).lower(),
            "candidate_for_future_training_admission": str(include).lower(),
            "independent_POST_geometry_human_decision_available": str(not include).lower(),
            "model_supervision_usable": "" if include else "false",
            "chemistry_known_positive": "true",
            "negative_chemistry": "false",
            "task_domain_negative": "false",
            "distance_threshold_rejection": "false",
            "runtime_negative": "false",
            "protein_reactive_atom": "CYS:SG",
            "post_ligand_reactive_atom": "FFQ:C1",
            "precursor_reactive_atom_context": "FCN:C2",
            "role_profile": _ROLE_PROFILE,
            "reaction_family_candidate_id": _SOURCE_FAMILY_CANDIDATE_ID,
            "reaction_family_candidate_human_accepted_for_review": "true",
            "warhead_rule_candidate_id": _SOURCE_RULE_CANDIDATE_ID,
            "warhead_rule_candidate_human_accepted_for_review": "true",
            "warhead_type_target_available": "false",
            "global_canonical_task_count": "5",
            "direct_profile_applicable_task_ids_json": "[0,3,4]",
            "training_mask_targets_available_now": "false",
            "current11_tensorizer_direct_profile_supported": "false",
            "training_admitted": "false",
            "training_materialization_allowed_now": "false",
            "current_runtime_model_usable": "false",
            "POST_geometry_training_label_available_now": "false",
        }
        for field, expected in exact_values.items():
            if row[field] != expected:
                _fail("EVENT_TASK_LABEL_AVAILABILITY_SEMANTIC_DRIFT:" + field)
        if tuple(_strict_json_cell(row["scaffold_atom_ids_json"], "SCAFFOLD_CELL")) != _SCAFFOLD_ATOM_IDS:
            _fail("EVENT_TASK_LABEL_AVAILABILITY_SCAFFOLD_INVALID")
        if tuple(_strict_json_cell(row["linker_atom_ids_json"], "LINKER_CELL")) != _LINKER_ATOM_IDS:
            _fail("EVENT_TASK_LABEL_AVAILABILITY_LINKER_INVALID")
        if tuple(_strict_json_cell(row["warhead_atom_ids_json"], "WARHEAD_CELL")) != _WARHEAD_ATOM_IDS:
            _fail("EVENT_TASK_LABEL_AVAILABILITY_WARHEAD_INVALID")
        applicability = _strict_json_cell(
            row["canonical_task_applicability_json"], "TASK_APPLICABILITY_CELL"
        )
        if type(applicability) is not list or len(applicability) != 5:
            _fail("EVENT_TASK_LABEL_AVAILABILITY_TASK_INVENTORY_INVALID")
        for observed, expected in zip(applicability, expected_task_applicability):
            if not isinstance(observed, Mapping) or any(
                observed.get(key) != value for key, value in expected.items()
            ):
                _fail("EVENT_TASK_LABEL_AVAILABILITY_TASK_APPLICABILITY_INVALID")
        if applicability[1].get("profile_applicable") is not False or (
            applicability[2].get("profile_applicable") is not False
        ):
            _fail("EVENT_TASK_LABEL_AVAILABILITY_B_OR_B2_APPLICABLE")
    if len(payload) != EVENT_TASK_LABEL_AVAILABILITY_BYTE_COUNT or (
        hashlib.sha256(payload).hexdigest() != EVENT_TASK_LABEL_AVAILABILITY_SHA256
    ):
        _fail("EVENT_TASK_LABEL_AVAILABILITY_FILE_BINDING_INVALID")
    return rows


def _validate_snapshot_matrix_cross_binding(
    snapshot: Mapping[str, Any], rows: Sequence[Mapping[str, str]]
) -> None:
    events = snapshot["events"]
    if len(events) != len(rows):
        _fail("SNAPSHOT_MATRIX_EVENT_COUNT_MISMATCH")
    for event, row in zip(events, rows):
        for field in (
            "canonical_event_id",
            "pdb_id",
            "completed_lane",
            "formal_event_training_use_decision",
        ):
            if str(event[field]) != row[field]:
                _fail("SNAPSHOT_MATRIX_EVENT_BINDING_MISMATCH:" + field)
        for field in (
            "chemistry_known_positive",
            "negative_chemistry",
            "task_domain_negative",
            "distance_threshold_rejection",
            "runtime_negative",
            "training_use_allowed",
            "independent_POST_geometry_human_decision_available",
            "POST_geometry_training_label_available_now",
            "training_admitted",
            "candidate_for_future_training_admission",
            "training_materialization_allowed_now",
            "current_runtime_model_usable",
        ):
            if str(event[field]).lower() != row[field]:
                _fail("SNAPSHOT_MATRIX_BOOLEAN_BINDING_MISMATCH:" + field)


def _validate_materialized_authorities_against_fresh_creators(
    *,
    family: dict[str, Any],
    rule: dict[str, Any],
    reaction_family_human_decision_payload: bytes,
    warhead_rule_human_decision_payload: bytes,
) -> None:
    try:
        fresh_family_result = family_creator.build_covapie_ffq_reaction_family_authority_v1(
            reaction_family_human_decision_payload
        )
        fresh_rule_result = rule_creator.build_covapie_ffq_warhead_rule_authority_v1(
            warhead_rule_human_decision_payload
        )
        fresh_family = fresh_family_result["reaction_family_authority"]
        fresh_rule = fresh_rule_result["warhead_rule_authority"]
        family_creator.validate_covapie_ffq_reaction_family_authority_payload_v2(
            fresh_family
        )
        rule_creator.validate_covapie_ffq_warhead_rule_authority_payload_v2(rule)
        rule_creator.validate_covapie_ffq_warhead_rule_authority_payload_v2(
            fresh_rule
        )
    except (TypeError, KeyError, ValueError) as error:
        raise FFQEffectiveSupervisionValidationError(
            "FRESH_FFQ_AUTHORITY_CREATOR_VALIDATION_FAILED"
        ) from error
    if family != fresh_family:
        _fail("DISK_REACTION_FAMILY_AUTHORITY_NOT_EXACT_FRESH_CREATOR_OUTPUT")
    if rule != fresh_rule:
        _fail("DISK_WARHEAD_RULE_AUTHORITY_NOT_EXACT_FRESH_CREATOR_OUTPUT")
    family_signature = family.get("canonical_semantic_signature")
    rule_signature = rule.get("canonical_semantic_signature")
    if not isinstance(family_signature, Mapping) or not isinstance(rule_signature, Mapping):
        _fail("DISK_AUTHORITY_SEMANTIC_SIGNATURE_MAPPING_REQUIRED")
    if (
        family_creator.authority_semantic_signature_sha256_v1(family_signature)
        != REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256
        or family_creator.authority_id_from_semantic_signature_v1(family_signature)
        != REACTION_FAMILY_AUTHORITY_ID
        or family.get("authority_id") != REACTION_FAMILY_AUTHORITY_ID
        or family.get("canonical_semantic_signature_sha256")
        != REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256
    ):
        _fail("DISK_REACTION_FAMILY_AUTHORITY_IDENTITY_INVALID")
    if (
        rule_creator.authority_semantic_signature_sha256_v1(rule_signature)
        != WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256
        or rule_creator.authority_id_from_semantic_signature_v1(rule_signature)
        != WARHEAD_RULE_AUTHORITY_ID
        or rule.get("authority_id") != WARHEAD_RULE_AUTHORITY_ID
        or rule.get("canonical_semantic_signature_sha256")
        != WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256
    ):
        _fail("DISK_WARHEAD_RULE_AUTHORITY_IDENTITY_INVALID")
    if rule_signature.get("reaction_family_authority_id") != family.get("authority_id"):
        _fail("DISK_FAMILY_RULE_LINKAGE_INVALID")


def _validate_collision_and_k36_coexistence(
    *,
    approved_authority_baseline_source_payloads: Mapping[str, bytes],
    k36_published_authority_payloads: Mapping[str, bytes],
) -> None:
    try:
        k36_authority_creator._validate_baseline_authority_source_payloads_v1(
            approved_authority_baseline_source_payloads,
            generated_family_id=REACTION_FAMILY_AUTHORITY_ID,
            generated_rule_id=WARHEAD_RULE_AUTHORITY_ID,
        )
    except (TypeError, KeyError, ValueError) as error:
        raise FFQEffectiveSupervisionValidationError(
            "APPROVED_AUTHORITY_BASELINE_COLLISION_AUDIT_FAILED"
        ) from error
    expected_paths = tuple(source["source_path"] for source in K36_PUBLISHED_AUTHORITY_SOURCES_V1)
    if not isinstance(k36_published_authority_payloads, Mapping) or (
        set(k36_published_authority_payloads) != set(expected_paths)
    ):
        _fail("K36_PUBLISHED_AUTHORITY_SOURCE_INVENTORY_INVALID")
    parsed: dict[str, dict[str, Any]] = {}
    for source in K36_PUBLISHED_AUTHORITY_SOURCES_V1:
        path = source["source_path"]
        payload = k36_published_authority_payloads[path]
        if type(payload) is not bytes or hashlib.sha256(payload).hexdigest() != source["source_sha256"]:
            _fail("K36_PUBLISHED_AUTHORITY_SOURCE_SHA256_INVALID:" + path)
        authority = strict_parse_authority_json_v1(payload)
        signature = authority.get("canonical_semantic_signature")
        kind = source["authority_kind"]
        if not isinstance(signature, Mapping) or (
            authority.get("authority_kind") != kind
            or authority.get("authority_id") != source["authority_id"]
            or authority.get("canonical_semantic_signature_sha256")
            != source["semantic_signature_sha256"]
            or k36_authority_creator.authority_semantic_signature_sha256_v1(signature)
            != source["semantic_signature_sha256"]
            or k36_authority_creator.authority_id_from_semantic_signature_v1(kind, signature)
            != source["authority_id"]
        ):
            _fail("K36_PUBLISHED_AUTHORITY_IDENTITY_INVALID:" + kind)
        parsed[kind] = authority
    if parsed["warhead_rule"]["canonical_semantic_signature"].get(
        "reaction_family_authority_id"
    ) != parsed["reaction_family"]["authority_id"]:
        _fail("K36_PUBLISHED_FAMILY_RULE_LINKAGE_INVALID")
    if (
        parsed["reaction_family"]["authority_id"] == REACTION_FAMILY_AUTHORITY_ID
        or parsed["warhead_rule"]["authority_id"] == WARHEAD_RULE_AUTHORITY_ID
        or parsed["reaction_family"]["canonical_semantic_signature_sha256"]
        == REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256
        or parsed["warhead_rule"]["canonical_semantic_signature_sha256"]
        == WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256
    ):
        _fail("FFQ_K36_AUTHORITY_COLLISION")


def _expected_record(event: Mapping[str, Any]) -> dict[str, Any]:
    include = event["pdb_id"] == "3VCY"
    record = {
        "effective_supervision_schema_version": EFFECTIVE_SUPERVISION_RECORD_SCHEMA_VERSION,
        "canonical_event_id": event["canonical_event_id"],
        "pdb_id": event["pdb_id"],
        "completed_lane": event["completed_lane"],
        "reaction_family_authority_id": REACTION_FAMILY_AUTHORITY_ID,
        "reaction_family_semantic_signature_sha256": REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256,
        "reaction_family_authority_established": True,
        "warhead_rule_authority_id": WARHEAD_RULE_AUTHORITY_ID,
        "warhead_rule_semantic_signature_sha256": WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256,
        "warhead_rule_authority_established": True,
        "project_level_chemistry_authority_linkage_complete": True,
        "target_residue_name": "CYS",
        "target_residue_atom_id": "SG",
        "ligand_component_id": "FFQ",
        "ligand_reactive_atom_id": "C1",
        "precursor_component_id": "FCN",
        "precursor_reactive_atom_id": "C2",
        "active_warhead_semantics": _ACTIVE_WARHEAD_SEMANTICS,
        "reviewed_warhead_atom_ids": list(_WARHEAD_ATOM_IDS),
        "reviewed_scaffold_atom_ids": list(_SCAFFOLD_ATOM_IDS),
        "reviewed_linker_atom_ids": [],
        "role_profile": _ROLE_PROFILE,
        "formal_event_training_use_decision": (
            "INCLUDE" if include else "EXCLUDE_FROM_TRAINING_ONLY"
        ),
        "training_use_allowed": include,
        "human_training_exclusion_preserved": not include,
        "non_geometry_chemistry_supervision_authority_available": True,
        "non_geometry_training_candidate": include,
        "candidate_for_future_training_admission": include,
        "independent_POST_geometry_human_decision_available": not include,
        "POST_geometry_training_label_available_now": False,
        "POST_geometry_supervision_authority_status": _NOT_ESTABLISHED,
        "PRE_geometry_supervision_authority_status": _NOT_ESTABLISHED,
        "reaction_family_authority_target_available": True,
        "warhead_rule_authority_target_available": True,
        "warhead_type_target_available": False,
        "valid_task_ids": list(_VALID_TASK_IDS),
        "not_applicable_task_ids": list(_NOT_APPLICABLE_TASK_IDS),
        "training_mask_targets_available_now": False,
        "current11_tensorizer_direct_profile_supported": False,
        "training_admitted": False,
        "training_materialization_allowed_now": False,
        "model_supervision_usable": None if include else False,
        "current_runtime_model_usable": False,
        "effective_supervision_record_sha256": "",
    }
    record["effective_supervision_record_sha256"] = effective_supervision_record_sha256_v1(record)
    return record


def _expected_summary() -> dict[str, Any]:
    return {
        "successor_schema_version": SUCCESSOR_SCHEMA_VERSION,
        "effective_supervision_record_count": 8,
        "chemistry_positive_event_count": 8,
        "project_level_family_authority_linked_event_count": 8,
        "project_level_warhead_rule_authority_linked_event_count": 8,
        "project_level_chemistry_authority_linkage_complete_event_count": 8,
        "3VCY_event_count": 4,
        "3VCY_human_training_include_count": 4,
        "4R7U_event_count": 4,
        "4R7U_human_training_excluded_count": 4,
        "future_non_geometry_training_candidate_count": 4,
        "training_admitted_count": 0,
        "training_materialization_allowed_now_count": 0,
        "POST_geometry_training_label_available_count": 0,
        "current_runtime_model_usable_count": 0,
        "ffq_effective_authority_linkage_complete": True,
        "reaction_family_authority_established": True,
        "warhead_rule_authority_established": True,
        "disk_authorities_equal_fresh_creator_output": True,
        "disk_family_authority_equals_fresh_creator_output": True,
        "disk_warhead_rule_authority_equals_fresh_creator_output": True,
        "disk_authority_key_order_treated_as_semantically_irrelevant": True,
        "existing_approved_authority_collision_status": "NO_APPROVED_AUTHORITY_COLLISION",
        "K36_published_authorities_coexist_without_collision": True,
        "K36_authority_overwritten": False,
        "human_training_use_decisions_preserved": True,
        "4R7U_training_exclusion_preserved": True,
        "ffq_non_geometry_chemistry_authority_complete": True,
        "ffq_non_geometry_training_candidate_count": 4,
        "POST_geometry_supervision_authority_complete": False,
        "PRE_geometry_supervision_authority_complete": False,
        "training_supervision_authority_complete": False,
        "effective_supervision_built_in_memory": True,
        "effective_supervision_materialized": False,
        "state_modified": False,
        "project_level_authorities_consumed_read_only": True,
        "reaction_family_authority_created": True,
        "persisted_reaction_family_authority_created": True,
        "warhead_rule_authority_created": True,
        "persisted_warhead_rule_authority_created": True,
        "reaction_family_registration_performed": False,
        "warhead_rule_registration_performed": False,
        "family_rule_registration_performed": False,
        "global_authority_registry_modified": False,
        "effective_authority_persisted": False,
        "runtime_authority_updated": False,
        "runtime_authority_created": False,
        "runtime_auto_admission_authorized": False,
        "SMARTS_generation_performed": False,
        "reusable_chemistry_authority_created": False,
        "reconciliation_changed": False,
        "tensorizer_integration_performed": False,
        "training_admission_created": False,
        "training_dataset_changed": False,
        "runtime_admission_changed": False,
        "split_changed": False,
        "ready_for_training": False,
        "feature_semantics_audit_required_before_formal_training": True,
        "feature_semantics_audit_performed": False,
        "historical_UNKNOWN_ATOM_FEATURE_POLICY_resolved": False,
        "CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1": False,
        "Step12D": "SMOKE_LEGALITY_CHECK_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "training_performed": False,
        "network_performed": False,
        "model_forward": False,
        "backward": False,
        "optimizer_step": False,
        "Trainer.fit": False,
        "RL": False,
    }


def _expected_provenance() -> dict[str, Any]:
    return {
        "completed_decision_snapshot_byte_count": COMPLETED_DECISION_SNAPSHOT_BYTE_COUNT,
        "completed_decision_snapshot_sha256": COMPLETED_DECISION_SNAPSHOT_SHA256,
        "event_task_label_availability_byte_count": EVENT_TASK_LABEL_AVAILABILITY_BYTE_COUNT,
        "event_task_label_availability_sha256": EVENT_TASK_LABEL_AVAILABILITY_SHA256,
        "reaction_family_authority_file_byte_count": REACTION_FAMILY_AUTHORITY_FILE_BYTE_COUNT,
        "reaction_family_authority_file_sha256": REACTION_FAMILY_AUTHORITY_FILE_SHA256,
        "reaction_family_authority_canonical_payload_sha256": REACTION_FAMILY_AUTHORITY_CANONICAL_PAYLOAD_SHA256,
        "reaction_family_authority_receipt_file_sha256": FAMILY_AUTHORITY_RECEIPT_FILE_SHA256,
        "reaction_family_authority_id": REACTION_FAMILY_AUTHORITY_ID,
        "reaction_family_semantic_signature_sha256": REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256,
        "warhead_rule_authority_file_byte_count": WARHEAD_RULE_AUTHORITY_FILE_BYTE_COUNT,
        "warhead_rule_authority_file_sha256": WARHEAD_RULE_AUTHORITY_FILE_SHA256,
        "warhead_rule_authority_canonical_payload_byte_count": WARHEAD_RULE_AUTHORITY_CANONICAL_PAYLOAD_BYTE_COUNT,
        "warhead_rule_authority_canonical_payload_sha256": WARHEAD_RULE_AUTHORITY_CANONICAL_PAYLOAD_SHA256,
        "warhead_rule_authority_receipt_file_sha256": WARHEAD_RULE_AUTHORITY_RECEIPT_FILE_SHA256,
        "warhead_rule_authority_id": WARHEAD_RULE_AUTHORITY_ID,
        "warhead_rule_semantic_signature_sha256": WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256,
        "published_family_creator_schema_version": family_creator.CREATOR_SCHEMA_VERSION,
        "published_family_creator_source_sha256": FAMILY_CREATOR_SOURCE_SHA256,
        "published_warhead_rule_creator_schema_version": rule_creator.CREATOR_SCHEMA_VERSION,
        "published_warhead_rule_creator_source_sha256": WARHEAD_RULE_CREATOR_SOURCE_SHA256,
        "source_reaction_family_candidate_id": _SOURCE_FAMILY_CANDIDATE_ID,
        "source_warhead_rule_candidate_id": _SOURCE_RULE_CANDIDATE_ID,
        "existing_approved_authority_baseline_sources": [
            dict(source)
            for source in k36_authority_creator.EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1
        ],
        "coexisting_K36_published_authority_sources": [
            dict(source) for source in K36_PUBLISHED_AUTHORITY_SOURCES_V1
        ],
    }


def validate_covapie_ffq_project_level_authority_effective_supervision_v1(
    result: object,
) -> None:
    """Fail closed unless ``result`` is the exact deterministic successor."""

    validated = _require_exact_dict_fields(
        result, _RESULT_FIELDS, "EFFECTIVE_SUPERVISION_RESULT_FIELDS_INVALID"
    )
    records = validated["effective_supervision_records"]
    if type(records) is not list or len(records) != 8:
        _fail("EFFECTIVE_SUPERVISION_EXACT8_RECORDS_REQUIRED")
    ids: list[str] = []
    for record in records:
        item = _require_exact_dict_fields(
            record, _RECORD_FIELDS, "EFFECTIVE_SUPERVISION_RECORD_FIELDS_INVALID"
        )
        event_id = item.get("canonical_event_id")
        if event_id not in _CANONICAL_EVENT_IDS:
            _fail("EFFECTIVE_SUPERVISION_EVENT_ID_INVALID")
        expected_pdb = "3VCY" if ":3VCY:" in event_id else "4R7U"
        expected_event = {
            "canonical_event_id": event_id,
            "pdb_id": expected_pdb,
            "completed_lane": (
                "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
                if expected_pdb == "3VCY"
                else "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
            ),
        }
        expected_record = _expected_record(expected_event)
        if item != expected_record:
            _fail("EFFECTIVE_SUPERVISION_RECORD_INVALID:" + str(event_id))
        if item["effective_supervision_record_sha256"] != effective_supervision_record_sha256_v1(item):
            _fail("EFFECTIVE_SUPERVISION_RECORD_SHA256_INVALID:" + str(event_id))
        ids.append(event_id)
    if tuple(ids) != _CANONICAL_EVENT_IDS or len(set(ids)) != 8:
        _fail("EFFECTIVE_SUPERVISION_RECORD_ORDER_OR_POPULATION_INVALID")
    summary = validated["ingestion_effective_authority_summary"]
    if type(summary) is not dict or summary != _expected_summary():
        _fail("EFFECTIVE_SUPERVISION_SUMMARY_INVALID")
    provenance = validated["source_authority_provenance"]
    if type(provenance) is not dict or provenance != _expected_provenance():
        _fail("EFFECTIVE_SUPERVISION_SOURCE_PROVENANCE_INVALID")


def build_covapie_ffq_project_level_authority_effective_supervision_v1(
    *,
    completed_decision_snapshot_payload: bytes,
    event_task_label_availability_payload: bytes,
    reaction_family_authority_payload: bytes,
    warhead_rule_authority_payload: bytes,
    reaction_family_human_decision_payload: bytes,
    warhead_rule_human_decision_payload: bytes,
    approved_authority_baseline_source_payloads: Mapping[str, bytes],
    k36_published_authority_payloads: Mapping[str, bytes],
) -> dict[str, Any]:
    """Build Exact8 FFQ effective supervision without reading or writing state."""

    snapshot = _validate_published_snapshot(completed_decision_snapshot_payload)
    rows = _validate_published_matrix(event_task_label_availability_payload)
    _validate_snapshot_matrix_cross_binding(snapshot, rows)
    family = strict_parse_authority_json_v1(reaction_family_authority_payload)
    rule = strict_parse_authority_json_v1(warhead_rule_authority_payload)
    _validate_materialized_authorities_against_fresh_creators(
        family=family,
        rule=rule,
        reaction_family_human_decision_payload=reaction_family_human_decision_payload,
        warhead_rule_human_decision_payload=warhead_rule_human_decision_payload,
    )
    _validate_collision_and_k36_coexistence(
        approved_authority_baseline_source_payloads=(
            approved_authority_baseline_source_payloads
        ),
        k36_published_authority_payloads=k36_published_authority_payloads,
    )
    records = [_expected_record(event) for event in snapshot["events"]]
    result = {
        "effective_supervision_records": records,
        "ingestion_effective_authority_summary": _expected_summary(),
        "source_authority_provenance": _expected_provenance(),
    }
    validate_covapie_ffq_project_level_authority_effective_supervision_v1(result)
    return result
