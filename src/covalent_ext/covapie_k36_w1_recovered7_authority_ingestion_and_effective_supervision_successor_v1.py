"""Ingest reviewed K36 authorities into deterministic in-memory supervision.

This successor binds the exact five recovered K36 samples to the published
reaction-family and warhead-rule authorities.  It deliberately performs no
filesystem I/O, state materialization, tensorization, geometry reconstruction,
or model execution.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1
    as published_review_packages,
)
from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime,
)
from covalent_ext import (
    covapie_k36_w1_reaction_family_and_warhead_rule_authority_creator_v1
    as authority_creator,
)
from covalent_ext import (
    covapie_recovered7_direct_attachment_completed_review_submission_successor_v1
    as review_successor,
)


__all__ = (
    "EffectiveSupervisionValidationError",
    "SUCCESSOR_SCHEMA_VERSION",
    "EFFECTIVE_SUPERVISION_RECORD_SCHEMA_VERSION",
    "PUBLISHED_AUTHORITY_CREATOR_SOURCE_SHA256",
    "PUBLISHED_REACTION_FAMILY_AUTHORITY_FILE_SHA256",
    "PUBLISHED_WARHEAD_RULE_AUTHORITY_FILE_SHA256",
    "REACTION_FAMILY_AUTHORITY_ID",
    "REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256",
    "WARHEAD_RULE_AUTHORITY_ID",
    "WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256",
    "strict_parse_authority_json_v1",
    "effective_supervision_record_sha256_v1",
    "validate_covapie_k36_w1_recovered7_effective_supervision_v1",
    "build_covapie_k36_w1_recovered7_effective_supervision_v1",
)


SUCCESSOR_SCHEMA_VERSION = (
    "covapie_k36_w1_recovered7_authority_ingestion_and_"
    "effective_supervision_successor_v1"
)
EFFECTIVE_SUPERVISION_RECORD_SCHEMA_VERSION = (
    "covapie_k36_w1_recovered7_effective_supervision_record_v1"
)
PUBLISHED_AUTHORITY_CREATOR_SOURCE_SHA256 = (
    "7c0f68d298fd80d6427126cf6148af7593c18a5163f2aa8a7b3fa5fe1c8789e0"
)
PUBLISHED_REACTION_FAMILY_AUTHORITY_FILE_SHA256 = (
    "5eb39ac01770dbb8721a48d7ae6bf77fc6cb07493ca00a0eb5756ebf10921461"
)
PUBLISHED_WARHEAD_RULE_AUTHORITY_FILE_SHA256 = (
    "1b8927693386aa8c72fed8677d59bdb3b5b56d4e89a09d88a908341fec0a19b2"
)
REACTION_FAMILY_AUTHORITY_ID = (
    "COVAPIE_CYS_SG_REACTION_FAMILY_A06FD171EB8080D8"
)
REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256 = (
    "a06fd171eb8080d8cea9caf5001f7862fd60410d53a87b908aa8cc40117db52e"
)
WARHEAD_RULE_AUTHORITY_ID = "COVAPIE_CYS_SG_WARHEAD_RULE_855163C772D500C7"
WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256 = (
    "855163c772d500c7ed5471bdf510316d2cdbd3ebbcabde9a859d5a17031ac1c9"
)

_NOT_ESTABLISHED = "NOT_ESTABLISHED"
_NOT_CLAIMED = "NOT_CLAIMED"
_ACTIVE_WARHEAD_SEMANTICS = "REACTION_COMPETENT_ACTIVE_WARHEAD_V1"

_K36_APPLICABILITY_RECORD_SHA256_BY_IDENTITY = {
    "4DCD/K36": (
        "b567edd4312cd26e0ad9ca47aa742a231ac48385e7401388ec4c6c490350ea90"
    ),
    "4F49/K36": (
        "c83bb39badf1a55159845a8351e903fb52d25b7ef05f3930e51c1e27fbac780d"
    ),
    "5WKJ/K36": (
        "16341569acc1dce6747072ce7e9d1545a9ad43e9edb712d65329d202514cb60b"
    ),
    "6L70/K36": (
        "ed9bc89a6a6396a8c4732269278ae0f2a8f7e95c3cbb2afb3df347c8611347f6"
    ),
    "6WTT/K36": (
        "e97c3a81854e110577d879a4d20c366e17d2ae474c514ddd41eef541788b8c5b"
    ),
}
_K36_RETAINED_HEAVY_ATOM_IDS = (
    "C1",
    "C12",
    "C13",
    "C14",
    "C15",
    "C16",
    "C17",
    "C2",
    "C20",
    "C21",
    "C24",
    "C25",
    "C26",
    "C27",
    "C29",
    "C3",
    "C4",
    "C5",
    "C6",
    "C7",
    "C9",
    "N11",
    "N19",
    "N28",
    "O10",
    "O18",
    "O22",
    "O30",
    "O8",
)
_K36_SCAFFOLD_ATOM_IDS = tuple(
    atom_id
    for atom_id in _K36_RETAINED_HEAVY_ATOM_IDS
    if atom_id not in review_successor.K36_ACTIVE_WARHEAD_ATOM_IDS_V1
)
_K36_MINIMAL_SEED_ATOM_IDS = ("C20", "N19")
_DIRECT_BOUNDARY_SEMANTICS = {
    "boundary_profile": "DIRECT_SCAFFOLD_WARHEAD_SINGLE_BOUNDARY_V1",
    "boundary_count": 1,
    "scaffold_side_atom_id": "C20",
    "warhead_side_atom_id": "C21",
    "bond_order": "single",
    "linker_present": False,
}
_PROTEIN_LIGAND_EVENT_SEMANTICS = {
    "edge_kind": "PROTEIN_LIGAND_FORMED_COVALENT_EVENT",
    "protein_endpoint": "CYS:SG",
    "ligand_endpoint": "K36:C21",
    "component_internal_topology_edge": False,
}
_GLOBAL_TASKS = (
    (0, "warhead_only", "A"),
    (1, "linker_plus_warhead", "B"),
    (2, "scaffold_plus_warhead", "B2"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)
_DIRECT_VALID_TASK_IDS = (0, 3, 4)
_DIRECT_NOT_APPLICABLE_TASK_IDS = (1, 2)

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
        "sample_identity",
        "review_class_id",
        "chemistry_review_signature_sha256",
        "sample_applicability_record_sha256",
        "source_completed_review_record_sha256",
        "source_submission_schema_version",
        "reaction_family_authority_id",
        "reaction_family_semantic_signature_sha256",
        "reaction_family_authority_established",
        "warhead_rule_authority_id",
        "warhead_rule_semantic_signature_sha256",
        "warhead_rule_authority_established",
        "target_residue_name",
        "target_residue_atom_id",
        "ligand_reactive_atom_id",
        "active_warhead_semantics",
        "reviewed_active_warhead_atom_ids",
        "masked_precursor_provenance_atom_ids",
        "protein_ligand_event_semantics",
        "protein_ligand_formed_bond_order_authority_status",
        "pre_reaction_graph_authority_status",
        "pre_reaction_bond_order_authority_status",
        "mechanism_claim_status",
        "reversibility_claim_status",
        "role_profile",
        "retained_heavy_atom_ids",
        "retained_heavy_atom_count",
        "reviewed_scaffold_atom_ids",
        "reviewed_scaffold_atom_count",
        "reviewed_linker_atom_ids",
        "reviewed_linker_atom_count",
        "reviewed_warhead_role_atom_ids",
        "reviewed_warhead_role_atom_count",
        "minimal_seed_atom_ids",
        "direct_boundary_semantics",
        "valid_task_ids",
        "not_applicable_task_ids",
        "exact10_status",
        "pocket_status",
        "mechanical_closure_status",
        "PRE_geometry_supervision_authority_status",
        "effective_supervision_record_sha256",
    )
)
_SUMMARY_FIELDS = frozenset(
    (
        "successor_schema_version",
        "effective_supervision_record_count",
        "effective_supervision_member_identities",
        "global_task_vocabulary",
        "direct_profile_task_applicability",
        "reaction_family_authority_established",
        "warhead_rule_authority_established",
        "disk_authorities_equal_fresh_creator_output",
        "disk_authority_key_order_treated_as_semantically_irrelevant",
        "mandatory_live_exact3_collision_baseline_status",
        "k36_effective_authority_linkage_complete",
        "k36_non_geometry_training_supervision_authority_complete",
        "k36_PRE_geometry_supervision_authority_complete",
        "training_supervision_authority_complete",
        "ready_for_expanded_tensorizer_integration",
        "expanded_tensorizer_integration_pending",
        "ready_for_training",
        "training_readiness_blockers",
        "effective_supervision_materialized",
        "state_modified",
        "K2Z_status",
        "1ZB_status",
        "exact10_feature_semantics_reopened",
        "tensorizer_executed",
        "network_request_executed",
        "raw_downloaded",
        "topology_downloaded",
        "distance_bond_inference_used",
        "PRE_geometry_reconstruction_executed",
        "model_forward",
        "backward",
        "optimizer_step",
        "Trainer.fit",
        "RL",
    )
)
_SOURCE_PROVENANCE_FIELDS = frozenset(
    (
        "authority_creator_schema_version",
        "authority_creator_source_sha256",
        "published_reaction_family_authority_file_sha256",
        "published_warhead_rule_authority_file_sha256",
        "source_completed_review_record_sha256",
        "source_submission_schema_version",
        "source_review_class_id",
        "source_chemistry_signature_sha256",
        "source_member_identities",
        "reaction_family_authority_id",
        "reaction_family_semantic_signature_sha256",
        "warhead_rule_authority_id",
        "warhead_rule_semantic_signature_sha256",
        "existing_approved_authority_collision_status",
        "existing_approved_authority_baseline_sources",
    )
)


class EffectiveSupervisionValidationError(ValueError):
    """Raised when effective K36 supervision cannot be proven exact."""


def _fail(reason: str) -> None:
    raise EffectiveSupervisionValidationError(reason)


def _require_exact_dict_fields(
    value: object, fields: frozenset[str], reason: str
) -> dict[str, Any]:
    if type(value) is not dict or frozenset(value) != fields:
        _fail(reason)
    return value


def _reject_nonfinite_json_constant(value: str) -> None:
    _fail(f"AUTHORITY_JSON_NONFINITE_NUMBER_REJECTED:{value}")


def _parse_finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        _fail("AUTHORITY_JSON_NONFINITE_NUMBER_REJECTED")
    return parsed


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(f"AUTHORITY_JSON_DUPLICATE_KEY:{key}")
        result[key] = value
    return result


def strict_parse_authority_json_v1(payload: bytes) -> dict[str, Any]:
    """Parse one authority JSON payload without weakening JSON semantics."""

    if type(payload) is not bytes:
        _fail("AUTHORITY_JSON_BYTES_REQUIRED")
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("AUTHORITY_JSON_BOM_FORBIDDEN")
    if b"\x00" in payload:
        _fail("AUTHORITY_JSON_NUL_FORBIDDEN")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise EffectiveSupervisionValidationError(
            "AUTHORITY_JSON_UTF8_REQUIRED"
        ) from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_nonfinite_json_constant,
            parse_float=_parse_finite_json_float,
        )
    except EffectiveSupervisionValidationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError, RecursionError) as error:
        raise EffectiveSupervisionValidationError(
            "AUTHORITY_JSON_INVALID"
        ) from error
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
        raise EffectiveSupervisionValidationError(
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


def _global_task_vocabulary() -> list[dict[str, Any]]:
    return [
        {
            "task_id": task_id,
            "semantic_name": semantic_name,
            "display_alias": display_alias,
        }
        for task_id, semantic_name, display_alias in _GLOBAL_TASKS
    ]


def _direct_profile_task_applicability() -> list[dict[str, Any]]:
    return [
        {
            "task_id": task_id,
            "semantic_name": semantic_name,
            "display_alias": display_alias,
            "applicable": applicable,
            "applicability_reason": reason,
        }
        for task_id, semantic_name, display_alias, applicable, reason in (
            direct_runtime.DIRECT_PROFILE_TASK_APPLICABILITY_V1
        )
    ]


def _expected_source_authority_provenance() -> dict[str, Any]:
    return {
        "authority_creator_schema_version": authority_creator.CREATOR_SCHEMA_VERSION,
        "authority_creator_source_sha256": (
            PUBLISHED_AUTHORITY_CREATOR_SOURCE_SHA256
        ),
        "published_reaction_family_authority_file_sha256": (
            PUBLISHED_REACTION_FAMILY_AUTHORITY_FILE_SHA256
        ),
        "published_warhead_rule_authority_file_sha256": (
            PUBLISHED_WARHEAD_RULE_AUTHORITY_FILE_SHA256
        ),
        "source_completed_review_record_sha256": (
            authority_creator.K36_SOURCE_REVIEW_RECORD_SHA256_V1
        ),
        "source_submission_schema_version": review_successor.SUBMISSION_SCHEMA_VERSION,
        "source_review_class_id": review_successor.K36_REVIEW_CLASS_ID_V1,
        "source_chemistry_signature_sha256": (
            review_successor.K36_CHEMISTRY_SIGNATURE_SHA256_V1
        ),
        "source_member_identities": list(
            review_successor.K36_MEMBER_IDENTITIES_V1
        ),
        "reaction_family_authority_id": REACTION_FAMILY_AUTHORITY_ID,
        "reaction_family_semantic_signature_sha256": (
            REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256
        ),
        "warhead_rule_authority_id": WARHEAD_RULE_AUTHORITY_ID,
        "warhead_rule_semantic_signature_sha256": (
            WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256
        ),
        "existing_approved_authority_collision_status": (
            "NO_APPROVED_AUTHORITY_COLLISION"
        ),
        "existing_approved_authority_baseline_sources": [
            dict(source)
            for source in (
                authority_creator.EXISTING_APPROVED_AUTHORITY_BASELINE_SOURCES_V1
            )
        ],
    }


def _expected_summary() -> dict[str, Any]:
    return {
        "successor_schema_version": SUCCESSOR_SCHEMA_VERSION,
        "effective_supervision_record_count": 5,
        "effective_supervision_member_identities": list(
            review_successor.K36_MEMBER_IDENTITIES_V1
        ),
        "global_task_vocabulary": _global_task_vocabulary(),
        "direct_profile_task_applicability": (
            _direct_profile_task_applicability()
        ),
        "reaction_family_authority_established": True,
        "warhead_rule_authority_established": True,
        "disk_authorities_equal_fresh_creator_output": True,
        "disk_authority_key_order_treated_as_semantically_irrelevant": True,
        "mandatory_live_exact3_collision_baseline_status": (
            "NO_APPROVED_AUTHORITY_COLLISION"
        ),
        "k36_effective_authority_linkage_complete": True,
        "k36_non_geometry_training_supervision_authority_complete": True,
        "k36_PRE_geometry_supervision_authority_complete": False,
        "training_supervision_authority_complete": False,
        "ready_for_expanded_tensorizer_integration": True,
        "expanded_tensorizer_integration_pending": True,
        "ready_for_training": False,
        "training_readiness_blockers": [
            "EXPANDED_TENSORIZER_DOES_NOT_YET_CONSUME_RECOVERED_K36",
            "MIXED_PROFILE_BATCH_SCHEDULING_NOT_TESTED",
            "EXPANDED_DATALOADER_LIGHTNING_TRAINING_SMOKE_ABSENT",
            "PRE_GEOMETRY_SUPERVISION_AUTHORITY_NOT_ESTABLISHED",
        ],
        "effective_supervision_materialized": False,
        "state_modified": False,
        "K2Z_status": "PENDING_EMBEDDED_WARHEAD_MULTI_BOUNDARY_RUNTIME",
        "1ZB_status": "READY_FOR_HUMAN_APPROVAL",
        "exact10_feature_semantics_reopened": False,
        "tensorizer_executed": False,
        "network_request_executed": False,
        "raw_downloaded": False,
        "topology_downloaded": False,
        "distance_bond_inference_used": False,
        "PRE_geometry_reconstruction_executed": False,
        "model_forward": False,
        "backward": False,
        "optimizer_step": False,
        "Trainer.fit": False,
        "RL": False,
    }


def _expected_record(
    sample_identity: str, applicability_record_sha256: str
) -> dict[str, Any]:
    record = {
        "effective_supervision_schema_version": (
            EFFECTIVE_SUPERVISION_RECORD_SCHEMA_VERSION
        ),
        "sample_identity": sample_identity,
        "review_class_id": review_successor.K36_REVIEW_CLASS_ID_V1,
        "chemistry_review_signature_sha256": (
            review_successor.K36_CHEMISTRY_SIGNATURE_SHA256_V1
        ),
        "sample_applicability_record_sha256": applicability_record_sha256,
        "source_completed_review_record_sha256": (
            authority_creator.K36_SOURCE_REVIEW_RECORD_SHA256_V1
        ),
        "source_submission_schema_version": review_successor.SUBMISSION_SCHEMA_VERSION,
        "reaction_family_authority_id": REACTION_FAMILY_AUTHORITY_ID,
        "reaction_family_semantic_signature_sha256": (
            REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256
        ),
        "reaction_family_authority_established": True,
        "warhead_rule_authority_id": WARHEAD_RULE_AUTHORITY_ID,
        "warhead_rule_semantic_signature_sha256": (
            WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256
        ),
        "warhead_rule_authority_established": True,
        "target_residue_name": "CYS",
        "target_residue_atom_id": "SG",
        "ligand_reactive_atom_id": "C21",
        "active_warhead_semantics": _ACTIVE_WARHEAD_SEMANTICS,
        "reviewed_active_warhead_atom_ids": list(
            review_successor.K36_ACTIVE_WARHEAD_ATOM_IDS_V1
        ),
        "masked_precursor_provenance_atom_ids": list(
            review_successor.K36_MASKED_PRECURSOR_PROVENANCE_ATOM_IDS_V1
        ),
        "protein_ligand_event_semantics": dict(
            _PROTEIN_LIGAND_EVENT_SEMANTICS
        ),
        "protein_ligand_formed_bond_order_authority_status": (
            _NOT_ESTABLISHED
        ),
        "pre_reaction_graph_authority_status": _NOT_ESTABLISHED,
        "pre_reaction_bond_order_authority_status": _NOT_ESTABLISHED,
        "mechanism_claim_status": _NOT_CLAIMED,
        "reversibility_claim_status": _NOT_CLAIMED,
        "role_profile": direct_runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        "retained_heavy_atom_ids": list(_K36_RETAINED_HEAVY_ATOM_IDS),
        "retained_heavy_atom_count": 29,
        "reviewed_scaffold_atom_ids": list(_K36_SCAFFOLD_ATOM_IDS),
        "reviewed_scaffold_atom_count": 27,
        "reviewed_linker_atom_ids": [],
        "reviewed_linker_atom_count": 0,
        "reviewed_warhead_role_atom_ids": list(
            review_successor.K36_ACTIVE_WARHEAD_ATOM_IDS_V1
        ),
        "reviewed_warhead_role_atom_count": 2,
        "minimal_seed_atom_ids": list(_K36_MINIMAL_SEED_ATOM_IDS),
        "direct_boundary_semantics": dict(_DIRECT_BOUNDARY_SEMANTICS),
        "valid_task_ids": list(_DIRECT_VALID_TASK_IDS),
        "not_applicable_task_ids": list(_DIRECT_NOT_APPLICABLE_TASK_IDS),
        "exact10_status": "EXACT10_PASS",
        "pocket_status": "POCKET_PASS",
        "mechanical_closure_status": "MECHANICAL_CLOSURE_PASS",
        "PRE_geometry_supervision_authority_status": _NOT_ESTABLISHED,
        "effective_supervision_record_sha256": "",
    }
    record["effective_supervision_record_sha256"] = (
        effective_supervision_record_sha256_v1(record)
    )
    return record


def _validate_materialized_authorities_against_fresh_creator(
    family: dict[str, Any],
    rule: dict[str, Any],
    fresh: dict[str, Any],
) -> None:
    fresh_family = fresh["reaction_family_authority"]
    fresh_rule = fresh["warhead_rule_authority"]
    if family != fresh_family:
        _fail("DISK_REACTION_FAMILY_AUTHORITY_NOT_EXACT_FRESH_CREATOR_OUTPUT")
    if rule != fresh_rule:
        _fail("DISK_WARHEAD_RULE_AUTHORITY_NOT_EXACT_FRESH_CREATOR_OUTPUT")

    expected = (
        (
            family,
            "reaction_family",
            REACTION_FAMILY_AUTHORITY_ID,
            REACTION_FAMILY_SEMANTIC_SIGNATURE_SHA256,
        ),
        (
            rule,
            "warhead_rule",
            WARHEAD_RULE_AUTHORITY_ID,
            WARHEAD_RULE_SEMANTIC_SIGNATURE_SHA256,
        ),
    )
    for payload, kind, expected_id, expected_sha256 in expected:
        signature = payload.get("canonical_semantic_signature")
        if not isinstance(signature, Mapping):
            _fail(f"DISK_{kind.upper()}_SEMANTIC_SIGNATURE_MAPPING_REQUIRED")
        actual_sha256 = (
            authority_creator.authority_semantic_signature_sha256_v1(
                signature
            )
        )
        actual_id = authority_creator.authority_id_from_semantic_signature_v1(
            kind, signature
        )
        if (
            payload.get("canonical_semantic_signature_sha256")
            != actual_sha256
            or actual_sha256 != expected_sha256
        ):
            _fail(f"DISK_{kind.upper()}_SEMANTIC_SIGNATURE_SHA256_INVALID")
        if payload.get("authority_id") != actual_id or actual_id != expected_id:
            _fail(f"DISK_{kind.upper()}_AUTHORITY_ID_INVALID")
    if (
        rule["canonical_semantic_signature"].get(
            "reaction_family_authority_id"
        )
        != family["authority_id"]
    ):
        _fail("DISK_FAMILY_RULE_LINKAGE_INVALID")


def _validate_exact_applicability_and_inventory(
    *,
    review_class: Mapping[str, Any],
    sample_applicability: Sequence[Mapping[str, Any]],
    compiled_submission: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    applicability_by_identity: dict[str, Mapping[str, Any]] = {}
    for record in sample_applicability:
        identity = record.get("sample_identity")
        if type(identity) is not str:
            _fail("K36_APPLICABILITY_SAMPLE_IDENTITY_INVALID")
        if identity in applicability_by_identity:
            _fail("K36_APPLICABILITY_SAMPLE_IDENTITY_DUPLICATE")
        applicability_by_identity[identity] = record
    if tuple(
        sorted(applicability_by_identity, key=lambda value: value.encode("utf-8"))
    ) != review_successor.K36_MEMBER_IDENTITIES_V1:
        _fail("K36_APPLICABILITY_EXACT5_POPULATION_INVALID")
    for identity, expected_sha256 in (
        _K36_APPLICABILITY_RECORD_SHA256_BY_IDENTITY.items()
    ):
        record = applicability_by_identity[identity]
        if (
            record.get("applicability_record_sha256") != expected_sha256
            or published_review_packages.sample_applicability_record_sha256_v1(
                record
            )
            != expected_sha256
        ):
            _fail(f"K36_PUBLISHED_APPLICABILITY_RECORD_MISMATCH:{identity}")

    try:
        retained_atom_ids = tuple(
            row["atom_id"]
            for row in review_class["chemistry_review_signature"][
                "canonical_model_bound_ligand_heavy_atom_inventory"
            ]
        )
    except (KeyError, TypeError) as error:
        raise EffectiveSupervisionValidationError(
            "K36_RETAINED_HEAVY_ATOM_INVENTORY_INVALID"
        ) from error
    if retained_atom_ids != _K36_RETAINED_HEAVY_ATOM_IDS:
        _fail("K36_RETAINED_HEAVY_ATOM_INVENTORY_NOT_EXACT")
    if (
        tuple(compiled_submission.get("reviewed_scaffold_atom_ids", ()))
        != _K36_SCAFFOLD_ATOM_IDS
        or compiled_submission.get("reviewed_linker_atom_ids") != []
        or tuple(compiled_submission.get("reviewed_warhead_role_atom_ids", ()))
        != review_successor.K36_ACTIVE_WARHEAD_ATOM_IDS_V1
        or set(_K36_SCAFFOLD_ATOM_IDS)
        | set(review_successor.K36_ACTIVE_WARHEAD_ATOM_IDS_V1)
        != set(_K36_RETAINED_HEAVY_ATOM_IDS)
    ):
        _fail("K36_DIRECT_ROLE_INVENTORY_NOT_EXACT_27_0_2")
    return applicability_by_identity


def validate_covapie_k36_w1_recovered7_effective_supervision_v1(
    result: Mapping[str, Any],
) -> None:
    """Fail closed unless an in-memory result is the exact K36 successor."""

    validated_result = _require_exact_dict_fields(
        result, _RESULT_FIELDS, "EFFECTIVE_SUPERVISION_RESULT_FIELDS_INVALID"
    )
    records = validated_result["effective_supervision_records"]
    if type(records) is not list or len(records) != 5:
        _fail("EFFECTIVE_SUPERVISION_EXACT5_RECORDS_REQUIRED")
    identities: list[str] = []
    for record in records:
        validated_record = _require_exact_dict_fields(
            record, _RECORD_FIELDS, "EFFECTIVE_SUPERVISION_RECORD_FIELDS_INVALID"
        )
        identity = validated_record.get("sample_identity")
        if identity not in _K36_APPLICABILITY_RECORD_SHA256_BY_IDENTITY:
            _fail("EFFECTIVE_SUPERVISION_MEMBER_IDENTITY_INVALID")
        expected_record = _expected_record(
            identity,
            _K36_APPLICABILITY_RECORD_SHA256_BY_IDENTITY[identity],
        )
        if validated_record != expected_record:
            _fail(f"EFFECTIVE_SUPERVISION_RECORD_INVALID:{identity}")
        if (
            validated_record["effective_supervision_record_sha256"]
            != effective_supervision_record_sha256_v1(validated_record)
        ):
            _fail(f"EFFECTIVE_SUPERVISION_RECORD_SHA256_INVALID:{identity}")
        identities.append(identity)
    if tuple(identities) != review_successor.K36_MEMBER_IDENTITIES_V1:
        _fail("EFFECTIVE_SUPERVISION_RECORD_ORDER_OR_POPULATION_INVALID")

    summary = _require_exact_dict_fields(
        validated_result["ingestion_effective_authority_summary"],
        _SUMMARY_FIELDS,
        "EFFECTIVE_SUPERVISION_SUMMARY_FIELDS_INVALID",
    )
    if summary != _expected_summary():
        _fail("EFFECTIVE_SUPERVISION_SUMMARY_INVALID")

    provenance = _require_exact_dict_fields(
        validated_result["source_authority_provenance"],
        _SOURCE_PROVENANCE_FIELDS,
        "EFFECTIVE_SUPERVISION_SOURCE_PROVENANCE_FIELDS_INVALID",
    )
    if provenance != _expected_source_authority_provenance():
        _fail("EFFECTIVE_SUPERVISION_SOURCE_PROVENANCE_INVALID")


def build_covapie_k36_w1_recovered7_effective_supervision_v1(
    *,
    completed_review_record: Mapping[str, Any],
    review_class: Mapping[str, Any],
    sample_applicability: Sequence[Mapping[str, Any]],
    compiled_submission: Mapping[str, Any],
    reaction_family_authority: bytes,
    warhead_rule_authority: bytes,
    existing_approved_authority_baseline_source_payloads: Mapping[str, bytes],
) -> dict[str, Any]:
    """Build exact5 K36 effective supervision without writing any state."""

    parsed_family = strict_parse_authority_json_v1(reaction_family_authority)
    parsed_rule = strict_parse_authority_json_v1(warhead_rule_authority)
    try:
        build_authorities = getattr(
            authority_creator,
            "build_covapie_k36_w1_reaction_family_and_warhead_rule_"
            "authority_v1",
        )
        validate_authorities = getattr(
            authority_creator,
            "validate_covapie_k36_w1_reaction_family_and_warhead_rule_"
            "authority_payload_v1",
        )
        fresh = build_authorities(
            completed_review_record=completed_review_record,
            review_class=review_class,
            sample_applicability=sample_applicability,
            compiled_submission=compiled_submission,
            existing_approved_authority_baseline_source_payloads=(
                existing_approved_authority_baseline_source_payloads
            ),
        )
        validate_authorities(fresh)
    except (TypeError, KeyError, ValueError) as error:
        raise EffectiveSupervisionValidationError(
            "FRESH_K36_AUTHORITY_CREATOR_VALIDATION_FAILED"
        ) from error

    _validate_materialized_authorities_against_fresh_creator(
        parsed_family, parsed_rule, fresh
    )
    applicability_by_identity = _validate_exact_applicability_and_inventory(
        review_class=review_class,
        sample_applicability=sample_applicability,
        compiled_submission=compiled_submission,
    )

    collision = fresh["creation_provenance_readiness_summary"][
        "existing_approved_authority_collision_check"
    ]
    if collision.get("status") != "NO_APPROVED_AUTHORITY_COLLISION":
        _fail("MANDATORY_LIVE_EXACT3_AUTHORITY_COLLISION_CHECK_NOT_PASS")

    records = [
        _expected_record(
            identity,
            applicability_by_identity[identity][
                "applicability_record_sha256"
            ],
        )
        for identity in review_successor.K36_MEMBER_IDENTITIES_V1
    ]
    result = {
        "effective_supervision_records": records,
        "ingestion_effective_authority_summary": _expected_summary(),
        "source_authority_provenance": (
            _expected_source_authority_provenance()
        ),
    }
    validate_covapie_k36_w1_recovered7_effective_supervision_v1(result)
    return result
