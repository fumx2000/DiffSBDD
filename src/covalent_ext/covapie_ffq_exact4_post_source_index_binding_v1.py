"""Bind approved FFQ Exact4 POST sources to structural batch indices.

This module is deliberately read-only.  Callers provide already-read bytes and
sample records; the public builder validates their frozen identities, assembles
the published fixed-scaffold CPU alignment, and returns source/index metadata.
It does not emit an approved distance value, a geometry target, a loss request,
an admission decision, or a model input sidecar.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Mapping, NoReturn, Sequence

import torch

from covalent_ext import (
    covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1
    as effective_owner,
)
from covalent_ext import (
    covapie_ffq_real_structure_microbatch_alignment_v1 as alignment_owner,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as feature_owner,
)


__all__ = (
    "FFQExact4PostSourceIndexBindingError",
    "FFQExact4RawAtomSiteIdentityV1",
    "FFQExact4EndpointSourceIndexBindingV1",
    "FFQExact4PostEventSourceIndexBindingV1",
    "FFQExact4PostSourceIndexBindingResultV1",
    "build_covapie_ffq_exact4_post_source_index_binding_v1",
)


_ERROR = "COVAPIE_FFQ_EXACT4_POST_SOURCE_INDEX_BINDING_V1_ERROR"
LABEL_USE_FORMAL_SHA256_V1 = (
    "8f3297435525ab68501046f811aa32ae7dbd8ab30c6bcafcafc988aada89468d"
)
POST_OBSERVATION_FORMAL_SHA256_V1 = (
    "6f63963487d4d049fd06d1723c52fc4a6408be8e0bf7af73067fdd8fc0d85955"
)
STRUCTURE_PAYLOAD_SHA256_V1 = (
    "80f00b3dfd6a743ef4cb768cb2959261920a071d362cafa7ce083fc78194bc00"
)
STRUCTURE_PAYLOAD_BYTE_COUNT_V1 = 353235
POCKET_SEED_POLICY_V1 = (
    alignment_owner.POCKET_SEED_POLICY_FIXED_SCAFFOLD_WARHEAD_ONLY_V1
)

_EVENT_IDS = (
    "COVAPIE_CYS_SG_EVENT_V1:3VCY:A:CYS:116-:SG:E:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:3VCY:B:CYS:116-:SG:J:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:3VCY:C:CYS:116-:SG:O:FFQ:C1",
    "COVAPIE_CYS_SG_EVENT_V1:3VCY:D:CYS:116-:SG:T:FFQ:C1",
)
_EVENT_ID_SET = frozenset(_EVENT_IDS)
_EFFECTIVE_RECORD_SHA256_BY_EVENT = {
    _EVENT_IDS[0]: "5084653736ca480a274a52f5139df2b4fa3f5dc6405d12c5cf9cc4c0c4b671f8",
    _EVENT_IDS[1]: "53490ff00cd0ff1d37329f0eea44ca23b6957b7cd41fc0f1dbd4ab33238614a3",
    _EVENT_IDS[2]: "792c5ed7174419b79637275f56d3ebec06236c94aa303277b60a2bb334a736b0",
    _EVENT_IDS[3]: "975dae43d392eb039a6f7736b88d7590dc731318101945fe05d194eee3f28f13",
}
_TASKS = (
    ("A", "warhead_only"),
    ("B", "linker_plus_warhead"),
    ("B2", "scaffold_plus_warhead"),
    ("B3", "scaffold_only"),
    ("C", "scaffold_plus_linker_plus_warhead"),
)
_SAMPLE_FIELDS = frozenset(
    {"cif_gz_payload", "effective_supervision_record", "canonical_task_id"}
)
_MODEL_INPUT_FIELDS = frozenset(
    {
        "lig_coords",
        "pocket_coords",
        "lig_one_hot",
        "pocket_one_hot",
        "lig_source_row_index",
        "pocket_source_row_index",
        "lig_parser_local_index",
        "pocket_parser_local_index",
        "num_lig_atoms",
        "num_pocket_nodes",
        "lig_mask",
        "pocket_mask",
    }
)
_RAW_MMCIF_FIELDS = frozenset(
    {
        "B_iso_or_equiv",
        "Cartn_x",
        "Cartn_y",
        "Cartn_z",
        "auth_asym_id",
        "auth_atom_id",
        "auth_comp_id",
        "auth_seq_id",
        "group_PDB",
        "id",
        "label_alt_id",
        "label_asym_id",
        "label_atom_id",
        "label_comp_id",
        "label_entity_id",
        "label_seq_id",
        "occupancy",
        "pdbx_PDB_ins_code",
        "pdbx_PDB_model_num",
        "type_symbol",
    }
)
_FRAME = "DEPOSITED_3VCY_MODEL_1_CARTESIAN_FRAME_UNTRANSFORMED"
_PURPOSE = "independent_hidden_post_distance_v1"
_SOURCE_ROLE = "approved_ffq_post_observation_source_use"
_UNIT = "angstrom"
_SEMANTIC_NAME = "POST_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM"


class FFQExact4PostSourceIndexBindingError(ValueError):
    """Raised unless every frozen source and batch-index invariant is proven."""


@dataclass(frozen=True)
class FFQExact4RawAtomSiteIdentityV1:
    group_PDB: str
    atom_site_id: str
    type_symbol: str
    label_atom_id: str
    label_alt_id: str
    label_comp_id: str
    label_asym_id: str
    label_entity_id: str
    label_seq_id: str
    auth_atom_id: str
    auth_comp_id: str
    auth_asym_id: str
    auth_seq_id: str
    pdbx_PDB_ins_code: str
    pdbx_PDB_model_num: str


@dataclass(frozen=True)
class FFQExact4EndpointSourceIndexBindingV1:
    endpoint_semantic_name: str
    source_identity: FFQExact4RawAtomSiteIdentityV1
    source_atom_site_row_index_0based: int
    node_domain: str
    local_node_index: int
    flat_node_index: int
    sample_segment_start_inclusive: int
    sample_segment_end_exclusive: int


@dataclass(frozen=True)
class FFQExact4PostEventSourceIndexBindingV1:
    canonical_event_id: str
    batch_ordinal: int
    task_semantic_name: str
    canonical_task_id: int
    purpose: str
    component_index: int
    unit: str
    label_use_formal_sha256: str
    label_use_event_decision_locator: str
    post_observation_formal_sha256: str
    post_observation_event_locator: str
    post_observation_distance_field_locator: str
    ligand_C1: FFQExact4EndpointSourceIndexBindingV1
    protein_SG: FFQExact4EndpointSourceIndexBindingV1
    effective_supervision_schema_version: str
    effective_supervision_record_sha256: str
    pocket_seed_policy: str


@dataclass(frozen=True)
class FFQExact4PostSourceIndexBindingResultV1:
    structural_alignment: alignment_owner.FFQRealStructureMicrobatchAlignmentV1
    source_index_bindings: tuple[FFQExact4PostEventSourceIndexBindingV1, ...]


@dataclass(frozen=True)
class _FormalEventSourceV1:
    canonical_event_id: str
    label_use_event_locator: str
    observation_event_locator: str
    observation_distance_field_locator: str
    ligand_raw_fields: Mapping[str, str]
    protein_raw_fields: Mapping[str, str]


@dataclass(frozen=True)
class _ResolvedEndpointV1:
    source_identity: FFQExact4RawAtomSiteIdentityV1
    source_row_index: int


@dataclass(frozen=True)
class _ResolvedEventSourceV1:
    formal: _FormalEventSourceV1
    ligand: _ResolvedEndpointV1
    protein: _ResolvedEndpointV1


def _fail(reason: str) -> NoReturn:
    raise FFQExact4PostSourceIndexBindingError(f"{_ERROR}:{reason}")


def _mapping(value: object, reason: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(reason)
    return value  # type: ignore[return-value]


def _list(value: object, reason: str) -> list[Any]:
    if type(value) is not list:
        _fail(reason)
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("FORMAL_JSON_DUPLICATE_KEY:" + key)
        result[key] = value
    return result


def _finite_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        _fail("FORMAL_JSON_NONFINITE_NUMBER")
    return parsed


def _reject_json_constant(value: str) -> NoReturn:
    _fail("FORMAL_JSON_NONFINITE_CONSTANT:" + value)


def _strict_frozen_json(
    payload: object, *, expected_sha256: str, label: str
) -> Mapping[str, Any]:
    if type(payload) is not bytes:
        _fail(label + "_EXACT_BYTES_REQUIRED")
    if hashlib.sha256(payload).hexdigest() != expected_sha256:
        _fail(label + "_SHA256_MISMATCH")
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_float=_finite_json_float,
            parse_constant=_reject_json_constant,
        )
    except FFQExact4PostSourceIndexBindingError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, OverflowError, RecursionError) as error:
        raise FFQExact4PostSourceIndexBindingError(
            f"{_ERROR}:{label}_STRICT_JSON_INVALID"
        ) from error
    return _mapping(value, label + "_ROOT_OBJECT_REQUIRED")


def _expect(mapping: Mapping[str, Any], expected: Mapping[str, object], reason: str) -> None:
    if any(mapping.get(key) != value for key, value in expected.items()):
        _fail(reason)


def _validate_mask_contract(document: Mapping[str, Any], *, label: str) -> None:
    contract = _mapping(document.get("canonical_V1_mask_contract"), label + "_MASK_CONTRACT_INVALID")
    tasks = _list(contract.get("tasks"), label + "_MASK_TASKS_INVALID")
    observed = tuple(
        (item.get("display_alias"), item.get("semantic_name"))
        for item in (_mapping(value, label + "_MASK_TASK_INVALID") for value in tasks)
    )
    if (
        contract.get("task_count") != 5
        or observed != _TASKS
        or contract.get("B3_scaffold_only_retained") is not True
        or contract.get("sixth_or_seventh_mask_added") is not False
    ):
        _fail(label + "_CANONICAL_EXACT5_MASK_CONTRACT_INVALID")


def _exact_event_map(events: object, *, label: str) -> tuple[list[Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    values = _list(events, label + "_EVENT_LIST_REQUIRED")
    if len(values) != 4:
        _fail(label + "_EXACT4_EVENTS_REQUIRED")
    mapped_values = [_mapping(value, label + "_EVENT_OBJECT_REQUIRED") for value in values]
    ids = [value.get("canonical_event_id") for value in mapped_values]
    if any(type(event_id) is not str for event_id in ids):
        _fail(label + "_EVENT_ID_EXACT_STRING_REQUIRED")
    if len(set(ids)) != 4 or frozenset(ids) != _EVENT_ID_SET:
        _fail(label + "_EVENT_POPULATION_INVALID")
    return mapped_values, {str(value["canonical_event_id"]): value for value in mapped_values}


def _finite_number(value: object, reason: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        _fail(reason)
    return float(value)


def _finite_numeric_text(value: object, reason: str) -> float:
    if type(value) is not str:
        _fail(reason)
    try:
        parsed = float(value)
    except (ValueError, OverflowError) as error:
        raise FFQExact4PostSourceIndexBindingError(
            f"{_ERROR}:{reason}"
        ) from error
    if not math.isfinite(parsed):
        _fail(reason)
    return parsed


def _finite_coordinates(value: object, reason: str) -> tuple[float, float, float]:
    values = _list(value, reason)
    if len(values) != 3:
        _fail(reason)
    result = tuple(_finite_number(item, reason) for item in values)
    return result  # type: ignore[return-value]


def _event_parts(event_id: str) -> dict[str, str]:
    match = alignment_owner._EVENT_ID.fullmatch(event_id)
    if match is None:
        _fail("EVENT_ID_GRAMMAR_INVALID")
    parts = match.groupdict()
    locator = alignment_owner._RESIDUE_LOCATOR.fullmatch(parts["residue_locator"])
    if locator is None:
        _fail("EVENT_RESIDUE_LOCATOR_INVALID")
    parts["sequence"] = locator.group("sequence")
    parts["insertion"] = "?" if locator.group("insertion") == "-" else locator.group("insertion")
    return parts


def _resolve_observation_locator(
    observation_events: Sequence[Mapping[str, Any]], locator: object, *, distance: bool
) -> tuple[int, Mapping[str, Any], object | None]:
    if type(locator) is not str:
        _fail("OBSERVATION_LOCATOR_EXACT_STRING_REQUIRED")
    parts = locator.split("/")
    expected_length = 5 if distance else 3
    if len(parts) != expected_length or parts[:2] != ["", "formal_event_decisions"]:
        _fail("OBSERVATION_LOCATOR_GRAMMAR_INVALID")
    index_token = parts[2]
    if not index_token.isdecimal() or str(int(index_token)) != index_token:
        _fail("OBSERVATION_LOCATOR_INDEX_INVALID")
    index = int(index_token)
    if not 0 <= index < len(observation_events):
        _fail("OBSERVATION_LOCATOR_OUT_OF_RANGE")
    event = observation_events[index]
    if distance:
        if parts[3:] != ["approved_observations", "SG_C1_observed_distance"]:
            _fail("OBSERVATION_DISTANCE_LOCATOR_INVALID")
        approved = _mapping(event.get("approved_observations"), "OBSERVATION_APPROVED_VALUES_INVALID")
        return index, event, approved.get("SG_C1_observed_distance")
    return index, event, None


def _validate_endpoint_formal(
    endpoint: object,
    *,
    canonical_expected: Mapping[str, object],
    endpoint_coordinates: tuple[float, float, float],
    reason_prefix: str,
) -> Mapping[str, str]:
    value = _mapping(endpoint, reason_prefix + "_ENDPOINT_INVALID")
    if value.get("coordinate_candidate_count") != 1:
        _fail(reason_prefix + "_COORDINATE_CANDIDATE_COUNT_INVALID")
    canonical = _mapping(value.get("canonical_identity"), reason_prefix + "_CANONICAL_IDENTITY_INVALID")
    if canonical != canonical_expected:
        _fail(reason_prefix + "_CANONICAL_IDENTITY_MISMATCH")
    selected = _mapping(value.get("selected_atom_site"), reason_prefix + "_SELECTED_ATOM_SITE_INVALID")
    if _finite_coordinates(selected.get("coordinates_angstrom"), reason_prefix + "_COORDINATES_INVALID") != endpoint_coordinates:
        _fail(reason_prefix + "_SELECTED_COORDINATES_MISMATCH")
    raw = _mapping(selected.get("raw_mmcif_fields"), reason_prefix + "_RAW_FIELDS_INVALID")
    if frozenset(raw) != _RAW_MMCIF_FIELDS or any(type(item) is not str for item in raw.values()):
        _fail(reason_prefix + "_RAW_FIELDS_SCHEMA_INVALID")
    raw_coordinates = tuple(
        _finite_numeric_text(
            raw["Cartn_" + axis], reason_prefix + "_RAW_COORDINATES_INVALID"
        )
        for axis in ("x", "y", "z")
    )
    if raw_coordinates != endpoint_coordinates:
        _fail(reason_prefix + "_RAW_COORDINATES_MISMATCH")
    return raw  # type: ignore[return-value]


def _validate_formal_documents_v1(
    label_use: Mapping[str, Any], observation: Mapping[str, Any]
) -> dict[str, _FormalEventSourceV1]:
    """Validate parsed frozen documents; kept separate for scoped negative tests."""

    _expect(
        label_use,
        {
            "schema_version": "covapie_ffq_exact4_post_label_use_formal_human_decision_v1",
            "stage": "FFQ_EXACT4_POST_LABEL_DEFINITION_AND_USE_FORMAL_HUMAN_DECISION_V1",
            "task_id": "covapie_ffq_exact4_post_label_use_formal_decision_v1",
            "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D",
            "decision_status": "HUMAN_APPROVED_SCOPED_POST_LABEL_DEFINITION_AND_USE",
        },
        "LABEL_USE_FORMAL_SCOPE_INVALID",
    )
    _expect(
        observation,
        {
            "schema_version": "covapie_ffq_exact4_post_geometry_formal_human_decision_v1",
            "stage": "FFQ_EXACT4_POST_OBSERVATION_SOURCE_USE_FORMAL_DECISION_V1",
            "task_id": "covapie_ffq_exact4_post_geometry_formal_decision_v1",
            "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D",
            "decision_status": "HUMAN_APPROVED_LIMITED_POST_OBSERVATION_SOURCE_USE",
            "formal_event_count": 4,
        },
        "OBSERVATION_FORMAL_SCOPE_INVALID",
    )
    _validate_mask_contract(label_use, label="LABEL_USE")
    _validate_mask_contract(observation, label="OBSERVATION")

    label_boundaries = _mapping(
        label_use.get("authority_and_execution_boundaries"),
        "LABEL_USE_BOUNDARIES_INVALID",
    )
    _expect(
        label_boundaries,
        {
            "FORMAL_LABEL_USE_SUPPLEMENT_CREATED": True,
            "NEW_SCOPED_POST_LABEL_USE_AUTHORITY_CREATED": True,
            "REAL_GEOMETRY_TRAINING_TARGET_CREATED": False,
            "REAL_SAMPLE_LOSS_MASKS_ENABLED": False,
            "SPLIT_OR_ADMISSION_CREATED": False,
            "CONSUMER_INTEGRATION_PERFORMED": False,
            "MODEL_OR_LOSS_EXECUTED": False,
            "PARAMETER_UPDATE_PERFORMED": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "LABEL_USE_CLOSED_EXECUTION_BOUNDARY_INVALID",
    )
    observation_boundaries = _mapping(
        observation.get("authority_and_readiness_boundaries"),
        "OBSERVATION_BOUNDARIES_INVALID",
    )
    _expect(
        observation_boundaries,
        {
            "HUMAN_APPROVAL_RECEIVED_FOR_THIS_SUPPLEMENT": True,
            "NEW_POST_SAMPLE_AUTHORITY_CREATED": True,
            "NEW_GEOMETRY_TRAINING_TARGET_CREATED": False,
            "LOSS_MASKS_ENABLED_BY_THIS_STAGE": False,
            "SPLIT_AUTHORITY_CREATED_BY_THIS_STAGE": False,
            "FORMAL_TRAINING_ADMITTED_BY_THIS_STAGE": False,
            "CONSUMER_INTEGRATION_PERFORMED": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "OBSERVATION_CLOSED_EXECUTION_BOUNDARY_INVALID",
    )
    scope = _mapping(observation.get("new_POST_sample_authority_scope"), "OBSERVATION_AUTHORITY_SCOPE_INVALID")
    if (
        scope.get("canonical_event_ids") != list(_EVENT_IDS)
        or scope.get("approved_quantities")
        != [
            "protein_SG_observed_coordinates",
            "ligand_C1_observed_coordinates",
            "SG_C1_observed_distance",
        ]
        or scope.get("event_specific_only") is not True
        or scope.get("cross_event_cross_structure_family_reuse_authorized") is not False
        or scope.get("later_process_execution_authorized_by_this_stage") is not False
    ):
        _fail("OBSERVATION_EVENT_SPECIFIC_SCOPE_INVALID")

    label_events, _ = _exact_event_map(label_use.get("formal_event_decisions"), label="LABEL_USE")
    observation_events, _ = _exact_event_map(observation.get("formal_event_decisions"), label="OBSERVATION")
    result: dict[str, _FormalEventSourceV1] = {}
    for label_index, label_event in enumerate(label_events):
        event_id = str(label_event["canonical_event_id"])
        parts = _event_parts(event_id)
        decision = _mapping(
            label_event.get("scoped_label_definition_and_use_decision"),
            "LABEL_USE_EVENT_DECISION_INVALID",
        )
        history = _mapping(
            label_event.get("historical_post_observation_source_readback"),
            "LABEL_USE_HISTORICAL_SOURCE_INVALID",
        )
        _expect(
            decision,
            {
                "component_index": 1,
                "decision": "ACCEPT",
                "status": "HUMAN_APPROVED",
                "purpose": _PURPOSE,
                "pilot_task": "warhead_only",
                "semantic_name": _SEMANTIC_NAME,
                "source_role": _SOURCE_ROLE,
                "unit": _UNIT,
                "event_specific_only": True,
                "cross_event_cross_structure_or_family_reuse_authorized": False,
                "not_averaged_or_reestimated": True,
                "real_training_target_or_tensor_materialized": False,
            },
            "LABEL_USE_EVENT_APPROVAL_INVALID:" + event_id,
        )
        _expect(
            history,
            {
                "existing_authority_decision": "ACCEPT",
                "existing_authority_status": "HUMAN_APPROVED",
                "source_role": _SOURCE_ROLE,
                "unit": _UNIT,
                "model_number": "1",
                "coordinate_frame": _FRAME,
                "not_an_approved_training_target": True,
            },
            "LABEL_USE_HISTORICAL_SOURCE_STATUS_INVALID:" + event_id,
        )
        if (
            label_event.get("historical_source_caveats_readback_only") is not True
            or label_event.get("historical_supplement_human_approval_UNSET_is_not_current_decision_state") is not True
            or decision.get("source_event_locator") != history.get("source_event_locator")
            or decision.get("source_distance_field_locator")
            != history.get("source_distance_field_locator")
        ):
            _fail("LABEL_USE_SOURCE_LOCATOR_RELATION_INVALID:" + event_id)
        _, source_event, _ = _resolve_observation_locator(
            observation_events, decision.get("source_event_locator"), distance=False
        )
        _, distance_event, observation_distance = _resolve_observation_locator(
            observation_events,
            decision.get("source_distance_field_locator"),
            distance=True,
        )
        if (
            source_event is not distance_event
            or source_event.get("canonical_event_id") != event_id
        ):
            _fail("CROSS_FORMAL_EVENT_LOCATOR_BINDING_INVALID:" + event_id)
        approved_value = _finite_number(decision.get("value"), "LABEL_USE_VALUE_INVALID")
        historical_value = _finite_number(
            history.get("SG_C1_observed_distance"), "LABEL_USE_HISTORICAL_VALUE_INVALID"
        )
        observation_value = _finite_number(observation_distance, "OBSERVATION_DISTANCE_INVALID")
        if approved_value != historical_value or approved_value != observation_value:
            _fail("CROSS_FORMAL_APPROVED_VALUE_MISMATCH:" + event_id)

        observation_approved = _mapping(
            source_event.get("approved_observations"),
            "OBSERVATION_APPROVED_VALUES_INVALID",
        )
        _expect(
            observation_approved,
            {"model_number": "1", "coordinate_unit": _UNIT, "coordinate_frame": _FRAME},
            "OBSERVATION_FRAME_OR_UNIT_INVALID:" + event_id,
        )
        protein_coordinates = _finite_coordinates(
            observation_approved.get("protein_SG_observed_coordinates"),
            "OBSERVATION_PROTEIN_COORDINATES_INVALID",
        )
        ligand_coordinates = _finite_coordinates(
            observation_approved.get("ligand_C1_observed_coordinates"),
            "OBSERVATION_LIGAND_COORDINATES_INVALID",
        )
        if not math.isclose(
            math.dist(protein_coordinates, ligand_coordinates),
            observation_value,
            rel_tol=0.0,
            abs_tol=5e-12,
        ):
            _fail("OBSERVATION_DISTANCE_COORDINATE_REPRODUCTION_INVALID:" + event_id)
        _expect(
            source_event,
            {
                "decision": "ACCEPT",
                "status": "HUMAN_APPROVED",
                "scope": "LIMITED_EVENT_SPECIFIC_POST_OBSERVATION_SOURCE_USE_ONLY",
            },
            "OBSERVATION_EVENT_APPROVAL_INVALID:" + event_id,
        )
        current = _mapping(
            source_event.get("current_supplement_authority"),
            "OBSERVATION_CURRENT_AUTHORITY_INVALID",
        )
        _expect(
            current,
            {
                "approved": True,
                "authority_created": True,
                "training_admitted": False,
                "training_target_created": False,
                "consumer_integration_performed": False,
            },
            "OBSERVATION_EVENT_CLOSED_BOUNDARY_INVALID:" + event_id,
        )
        endpoints = _mapping(
            source_event.get("endpoint_identity_and_source_quality"),
            "OBSERVATION_ENDPOINTS_INVALID",
        )
        ligand_raw = _validate_endpoint_formal(
            endpoints.get("ligand_endpoint"),
            canonical_expected={
                "atom_id": "C1",
                "atom_id_namespace": "WWPDB_CCD_ATOM_ID",
                "component_id": "FFQ",
                "label_asym_id": parts["ligand_asym"],
            },
            endpoint_coordinates=ligand_coordinates,
            reason_prefix="LIGAND_C1",
        )
        protein_raw = _validate_endpoint_formal(
            endpoints.get("protein_endpoint"),
            canonical_expected={
                "atom_id": "SG",
                "auth_residue_number": "116",
                "component_id": "CYS",
                "label_asym_id": parts["protein_chain"],
            },
            endpoint_coordinates=protein_coordinates,
            reason_prefix="PROTEIN_SG",
        )
        if (
            ligand_raw["group_PDB"] != "HETATM"
            or ligand_raw["type_symbol"] != "C"
            or ligand_raw["label_atom_id"] != parts["ligand_atom"]
            or ligand_raw["auth_atom_id"] != parts["ligand_atom"]
            or ligand_raw["label_comp_id"] != parts["ligand"]
            or ligand_raw["auth_comp_id"] != parts["ligand"]
            or ligand_raw["label_asym_id"] != parts["ligand_asym"]
            or ligand_raw["auth_asym_id"] != parts["protein_chain"]
            or ligand_raw["pdbx_PDB_model_num"] != "1"
            or ligand_raw["label_alt_id"] not in {".", "?"}
            or protein_raw["group_PDB"] != "ATOM"
            or protein_raw["type_symbol"] != "S"
            or protein_raw["label_atom_id"] != parts["protein_atom"]
            or protein_raw["auth_atom_id"] != parts["protein_atom"]
            or protein_raw["label_comp_id"] != parts["residue"]
            or protein_raw["auth_comp_id"] != parts["residue"]
            or protein_raw["label_asym_id"] != parts["protein_chain"]
            or protein_raw["auth_asym_id"] != parts["protein_chain"]
            or protein_raw["auth_seq_id"] != parts["sequence"]
            or protein_raw["pdbx_PDB_ins_code"] != parts["insertion"]
            or protein_raw["pdbx_PDB_model_num"] != "1"
            or protein_raw["label_alt_id"] not in {".", "?"}
        ):
            _fail("OBSERVATION_ENDPOINT_EVENT_IDENTITY_MISMATCH:" + event_id)
        result[event_id] = _FormalEventSourceV1(
            canonical_event_id=event_id,
            label_use_event_locator=f"/formal_event_decisions/{label_index}",
            observation_event_locator=str(decision["source_event_locator"]),
            observation_distance_field_locator=str(decision["source_distance_field_locator"]),
            ligand_raw_fields=ligand_raw,
            protein_raw_fields=protein_raw,
        )
    return result


def _validate_effective_record(record: Mapping[str, Any], event_id: str) -> None:
    expected_sha = _EFFECTIVE_RECORD_SHA256_BY_EVENT[event_id]
    declared_sha = record.get("effective_supervision_record_sha256")
    try:
        computed_sha = effective_owner.effective_supervision_record_sha256_v1(record)
    except Exception as error:
        raise FFQExact4PostSourceIndexBindingError(
            f"{_ERROR}:EFFECTIVE_RECORD_CANONICAL_IDENTITY_INVALID:{event_id}"
        ) from error
    if declared_sha != expected_sha or computed_sha != expected_sha:
        _fail("EFFECTIVE_RECORD_SHA256_MISMATCH:" + event_id)
    _expect(
        record,
        {
            "effective_supervision_schema_version": effective_owner.EFFECTIVE_SUPERVISION_RECORD_SCHEMA_VERSION,
            "canonical_event_id": event_id,
            "pdb_id": "3VCY",
            "target_residue_name": "CYS",
            "target_residue_atom_id": "SG",
            "ligand_component_id": "FFQ",
            "ligand_reactive_atom_id": "C1",
            "formal_event_training_use_decision": "INCLUDE",
            "training_use_allowed": True,
            "human_training_exclusion_preserved": False,
            "POST_geometry_training_label_available_now": False,
            "POST_geometry_supervision_authority_status": "NOT_ESTABLISHED",
            "PRE_geometry_supervision_authority_status": "NOT_ESTABLISHED",
            "warhead_type_target_available": False,
            "training_mask_targets_available_now": False,
            "training_admitted": False,
            "training_materialization_allowed_now": False,
            "current_runtime_model_usable": False,
        },
        "EFFECTIVE_RECORD_SCOPE_OR_BOUNDARY_INVALID:" + event_id,
    )
    if record.get("valid_task_ids") != [0, 3, 4]:
        _fail("EFFECTIVE_RECORD_TASK_CONTRACT_INVALID:" + event_id)


def _validate_samples(samples: object) -> tuple[Mapping[str, Any], ...]:
    if type(samples) not in (list, tuple) or len(samples) != 4:
        _fail("SAMPLES_EXACT4_LIST_OR_TUPLE_REQUIRED")
    validated: list[Mapping[str, Any]] = []
    event_ids: list[str] = []
    for ordinal, raw_sample in enumerate(samples):
        sample = _mapping(raw_sample, f"SAMPLE_{ordinal}_EXACT_DICT_REQUIRED")
        if frozenset(sample) != _SAMPLE_FIELDS:
            _fail(f"SAMPLE_{ordinal}_FIELDS_INVALID")
        if type(sample.get("canonical_task_id")) is not int or sample["canonical_task_id"] != 0:
            _fail(f"SAMPLE_{ordinal}_TASK_ID_0_REQUIRED")
        payload = sample.get("cif_gz_payload")
        if type(payload) is not bytes:
            _fail(f"SAMPLE_{ordinal}_STRUCTURE_PAYLOAD_EXACT_BYTES_REQUIRED")
        if (
            len(payload) != STRUCTURE_PAYLOAD_BYTE_COUNT_V1
            or hashlib.sha256(payload).hexdigest() != STRUCTURE_PAYLOAD_SHA256_V1
        ):
            _fail(f"SAMPLE_{ordinal}_FROZEN_STRUCTURE_PAYLOAD_MISMATCH")
        record = _mapping(
            sample.get("effective_supervision_record"),
            f"SAMPLE_{ordinal}_EFFECTIVE_RECORD_EXACT_DICT_REQUIRED",
        )
        event_id = record.get("canonical_event_id")
        if type(event_id) is not str or event_id not in _EVENT_ID_SET:
            _fail(f"SAMPLE_{ordinal}_EVENT_ID_NOT_EXACT4")
        _validate_effective_record(record, event_id)
        event_ids.append(event_id)
        validated.append(sample)
    if len(set(event_ids)) != 4 or frozenset(event_ids) != _EVENT_ID_SET:
        _fail("SAMPLE_EVENT_POPULATION_MUST_EQUAL_EXACT4")
    return tuple(validated)


def _raw_row_value(row: Mapping[str, Any], field: str) -> str:
    value = row.get("_atom_site." + field)
    return value if type(value) is str else str(value)


def _raw_field_matches_parser(actual: str, formal_raw: str) -> bool:
    # The published atom-site row parser normalizes both mmCIF missing-value
    # markers to an empty string.  Preserve the Formal's raw marker in returned
    # identity metadata while accepting only this explicit normalization.
    return actual == formal_raw or (actual == "" and formal_raw in {".", "?"})


def _public_identity(raw: Mapping[str, str]) -> FFQExact4RawAtomSiteIdentityV1:
    return FFQExact4RawAtomSiteIdentityV1(
        group_PDB=raw["group_PDB"],
        atom_site_id=raw["id"],
        type_symbol=raw["type_symbol"],
        label_atom_id=raw["label_atom_id"],
        label_alt_id=raw["label_alt_id"],
        label_comp_id=raw["label_comp_id"],
        label_asym_id=raw["label_asym_id"],
        label_entity_id=raw["label_entity_id"],
        label_seq_id=raw["label_seq_id"],
        auth_atom_id=raw["auth_atom_id"],
        auth_comp_id=raw["auth_comp_id"],
        auth_asym_id=raw["auth_asym_id"],
        auth_seq_id=raw["auth_seq_id"],
        pdbx_PDB_ins_code=raw["pdbx_PDB_ins_code"],
        pdbx_PDB_model_num=raw["pdbx_PDB_model_num"],
    )


def _resolve_endpoint_row(
    atom_rows: Sequence[Mapping[str, Any]], raw: Mapping[str, str], *, reason_prefix: str
) -> _ResolvedEndpointV1:
    # Source row is derived from actual parser order.  Atom-site IDs are only
    # matching evidence and are never converted with ``id - 1``.
    matches = [
        (index, row)
        for index, row in enumerate(atom_rows)
        if _raw_row_value(row, "id") == raw["id"]
    ]
    if len(matches) != 1:
        _fail(reason_prefix + "_ATOM_SITE_ID_NOT_UNIQUE")
    source_row, actual = matches[0]
    if any(
        not _raw_field_matches_parser(_raw_row_value(actual, field), value)
        for field, value in raw.items()
    ):
        _fail(reason_prefix + "_RAW_ATOM_SITE_CROSSCHECK_FAILED")
    return _ResolvedEndpointV1(
        source_identity=_public_identity(raw), source_row_index=source_row
    )


def _parse_structure_payload_v1(
    payload: bytes, *, expected_pdb_id: str
) -> Sequence[Mapping[str, Any]]:
    return alignment_owner._parse_and_crosscheck_atom_site(
        payload, expected_pdb_id=expected_pdb_id
    )


def _resolve_structure_sources(
    samples: Sequence[Mapping[str, Any]],
    formal_sources: Mapping[str, _FormalEventSourceV1],
) -> dict[str, _ResolvedEventSourceV1]:
    parsed_by_sha: dict[str, Sequence[Mapping[str, Any]]] = {}
    result: dict[str, _ResolvedEventSourceV1] = {}
    for sample in samples:
        payload = sample["cif_gz_payload"]
        digest = hashlib.sha256(payload).hexdigest()
        if digest not in parsed_by_sha:
            try:
                parsed_by_sha[digest] = _parse_structure_payload_v1(
                    payload, expected_pdb_id="3VCY"
                )
            except Exception as error:
                raise FFQExact4PostSourceIndexBindingError(
                    f"{_ERROR}:FROZEN_STRUCTURE_PARSE_OR_IDENTITY_FAILED"
                ) from error
        record = sample["effective_supervision_record"]
        event_id = str(record["canonical_event_id"])
        formal = formal_sources[event_id]
        atom_rows = parsed_by_sha[digest]
        result[event_id] = _ResolvedEventSourceV1(
            formal=formal,
            ligand=_resolve_endpoint_row(
                atom_rows, formal.ligand_raw_fields, reason_prefix="LIGAND_C1"
            ),
            protein=_resolve_endpoint_row(
                atom_rows, formal.protein_raw_fields, reason_prefix="PROTEIN_SG"
            ),
        )
    if frozenset(result) != _EVENT_ID_SET:
        _fail("RESOLVED_STRUCTURE_SOURCE_POPULATION_INVALID")
    return result


def _tensor(
    value: object,
    *,
    dtype: torch.dtype,
    shape: tuple[int, ...],
    reason: str,
) -> torch.Tensor:
    if (
        type(value) is not torch.Tensor
        or value.device.type != "cpu"
        or value.dtype != dtype
        or tuple(value.shape) != shape
    ):
        _fail(reason)
    return value


def _single_local_match(values: torch.Tensor, source_row: int, reason: str) -> int:
    matches = torch.nonzero(values == source_row, as_tuple=False).flatten().tolist()
    if len(matches) != 1:
        _fail(reason)
    return int(matches[0])


def _validate_alignment_and_build_bindings_v1(
    *,
    samples: Sequence[Mapping[str, Any]],
    resolved_sources: Mapping[str, _ResolvedEventSourceV1],
    alignment: object,
) -> tuple[FFQExact4PostEventSourceIndexBindingV1, ...]:
    """Accept one assembled alignment and return metadata after full cross-check."""

    if type(alignment) is not alignment_owner.FFQRealStructureMicrobatchAlignmentV1:
        _fail("STRUCTURAL_ALIGNMENT_TYPE_INVALID")
    if (
        alignment.sample_identities
        != tuple(str(sample["effective_supervision_record"]["canonical_event_id"]) for sample in samples)
        or alignment.structural_coordinates_centered is not True
        or alignment.model_forward is not False
        or alignment.training_performed is not False
    ):
        _fail("STRUCTURAL_ALIGNMENT_SCOPE_OR_IDENTITY_INVALID")
    batch = alignment.model_input_batch
    if type(batch) is not dict or frozenset(batch) != _MODEL_INPUT_FIELDS:
        _fail("MODEL_INPUT_BATCH_FIELDS_INVALID")

    ligand_offsets = alignment.ligand_node_offsets
    pocket_offsets = alignment.pocket_node_offsets
    if (
        type(ligand_offsets) is not tuple
        or type(pocket_offsets) is not tuple
        or len(ligand_offsets) != 5
        or len(pocket_offsets) != 5
        or ligand_offsets[0] != 0
        or pocket_offsets[0] != 0
        or any(type(value) is not int for value in ligand_offsets + pocket_offsets)
        or any(left >= right for left, right in zip(ligand_offsets, ligand_offsets[1:]))
        or any(left >= right for left, right in zip(pocket_offsets, pocket_offsets[1:]))
    ):
        _fail("STRUCTURAL_NODE_OFFSETS_INVALID")
    total_ligand = ligand_offsets[-1]
    total_pocket = pocket_offsets[-1]

    lig_coords = _tensor(batch["lig_coords"], dtype=torch.float32, shape=(total_ligand, 3), reason="LIGAND_COORDINATE_TENSOR_INVALID")
    pocket_coords = _tensor(batch["pocket_coords"], dtype=torch.float32, shape=(total_pocket, 3), reason="POCKET_COORDINATE_TENSOR_INVALID")
    lig_one_hot = _tensor(batch["lig_one_hot"], dtype=torch.float32, shape=(total_ligand, 10), reason="LIGAND_EXACT10_TENSOR_INVALID")
    pocket_one_hot = _tensor(batch["pocket_one_hot"], dtype=torch.float32, shape=(total_pocket, 10), reason="POCKET_EXACT10_TENSOR_INVALID")
    if (
        not torch.isfinite(lig_coords).all().item()
        or not torch.isfinite(pocket_coords).all().item()
        or not torch.all(lig_one_hot.sum(dim=1) == 1).item()
        or not torch.all(pocket_one_hot.sum(dim=1) == 1).item()
    ):
        _fail("STRUCTURAL_COORDINATE_OR_EXACT10_VALUES_INVALID")
    lig_sources = _tensor(batch["lig_source_row_index"], dtype=torch.long, shape=(total_ligand,), reason="LIGAND_SOURCE_ROW_TENSOR_INVALID")
    pocket_sources = _tensor(batch["pocket_source_row_index"], dtype=torch.long, shape=(total_pocket,), reason="POCKET_SOURCE_ROW_TENSOR_INVALID")
    lig_parser = _tensor(batch["lig_parser_local_index"], dtype=torch.long, shape=(total_ligand,), reason="LIGAND_PARSER_INDEX_TENSOR_INVALID")
    pocket_parser = _tensor(batch["pocket_parser_local_index"], dtype=torch.long, shape=(total_pocket,), reason="POCKET_PARSER_INDEX_TENSOR_INVALID")
    lig_mask = _tensor(batch["lig_mask"], dtype=torch.long, shape=(total_ligand,), reason="LIGAND_BATCH_MASK_INVALID")
    pocket_mask = _tensor(batch["pocket_mask"], dtype=torch.long, shape=(total_pocket,), reason="POCKET_BATCH_MASK_INVALID")
    ligand_counts = _tensor(batch["num_lig_atoms"], dtype=torch.long, shape=(4,), reason="LIGAND_COUNT_TENSOR_INVALID")
    pocket_counts = _tensor(batch["num_pocket_nodes"], dtype=torch.long, shape=(4,), reason="POCKET_COUNT_TENSOR_INVALID")
    if ligand_counts.tolist() != [ligand_offsets[i + 1] - ligand_offsets[i] for i in range(4)] or pocket_counts.tolist() != [pocket_offsets[i + 1] - pocket_offsets[i] for i in range(4)]:
        _fail("STRUCTURAL_COUNTS_OFFSETS_MISMATCH")

    _tensor(alignment.canonical_task_ids, dtype=torch.long, shape=(4,), reason="TASK_ID_TENSOR_INVALID")
    if alignment.canonical_task_ids.tolist() != [0, 0, 0, 0]:
        _fail("TASK_ID_TENSOR_NOT_WARHEAD_ONLY")
    for value, reason in (
        (alignment.sample_training_admitted, "TRAINING_ADMISSION_UPGRADE_FORBIDDEN"),
        (alignment.geometry_target_available, "GEOMETRY_AVAILABILITY_UPGRADE_FORBIDDEN"),
        (alignment.warhead_type_target_available, "WARHEAD_TYPE_AVAILABILITY_UPGRADE_FORBIDDEN"),
    ):
        tensor = _tensor(value, dtype=torch.bool, shape=(4,), reason=reason)
        if torch.any(tensor).item():
            _fail(reason)
    if torch.any(alignment.ligand_fixed_mask & alignment.ligand_generation_mask).item():
        _fail("FIXED_GENERATED_MASK_CONFLICT")

    one_dimensional = (
        (alignment.target_reactive_local_indices, torch.long, "TARGET_LOCAL_INDICES_INVALID"),
        (alignment.target_reactive_flat_indices, torch.long, "TARGET_FLAT_INDICES_INVALID"),
        (alignment.ligand_reactive_local_indices, torch.long, "LIGAND_LOCAL_INDICES_INVALID"),
        (alignment.ligand_reactive_flat_indices, torch.long, "LIGAND_FLAT_INDICES_INVALID"),
        (alignment.positive_pair_batch_indices, torch.long, "PAIR_BATCH_INDICES_INVALID"),
        (alignment.positive_pair_ligand_local_indices, torch.long, "PAIR_LIGAND_LOCAL_INDICES_INVALID"),
        (alignment.positive_pair_pocket_local_indices, torch.long, "PAIR_POCKET_LOCAL_INDICES_INVALID"),
        (alignment.positive_pair_ligand_flat_indices, torch.long, "PAIR_LIGAND_FLAT_INDICES_INVALID"),
        (alignment.positive_pair_pocket_flat_indices, torch.long, "PAIR_POCKET_FLAT_INDICES_INVALID"),
    )
    for value, dtype, reason in one_dimensional:
        _tensor(value, dtype=dtype, shape=(4,), reason=reason)
    for value, reason in (
        (alignment.ligand_role_valid, "LIGAND_ROLE_VALID_TENSOR_INVALID"),
        (alignment.ligand_generation_mask, "LIGAND_GENERATION_MASK_INVALID"),
        (alignment.ligand_fixed_mask, "LIGAND_FIXED_MASK_INVALID"),
        (alignment.ligand_target_mask, "LIGAND_TARGET_MASK_INVALID"),
        (alignment.ligand_context_mask, "LIGAND_CONTEXT_MASK_INVALID"),
    ):
        expected_shape = (total_ligand,) if value is alignment.ligand_role_valid else (total_ligand, 1)
        _tensor(value, dtype=torch.bool, shape=expected_shape, reason=reason)
    _tensor(alignment.ligand_role_id, dtype=torch.long, shape=(total_ligand,), reason="LIGAND_ROLE_ID_TENSOR_INVALID")
    _tensor(alignment.target_residue_membership_mask, dtype=torch.bool, shape=(total_pocket, 1), reason="TARGET_MEMBERSHIP_MASK_INVALID")
    _tensor(alignment.target_residue_reactive_atom_mask, dtype=torch.bool, shape=(total_pocket, 1), reason="TARGET_REACTIVE_MASK_INVALID")

    carbon_channel = feature_owner.CHECKPOINT_TOKEN_TO_INDEX["C"]
    sulfur_channel = feature_owner.CHECKPOINT_TOKEN_TO_INDEX["S"]
    bindings: list[FFQExact4PostEventSourceIndexBindingV1] = []
    for ordinal, sample in enumerate(samples):
        record = sample["effective_supervision_record"]
        event_id = str(record["canonical_event_id"])
        source = resolved_sources[event_id]
        lig_start, lig_end = ligand_offsets[ordinal : ordinal + 2]
        pocket_start, pocket_end = pocket_offsets[ordinal : ordinal + 2]
        if (
            not torch.all(lig_mask[lig_start:lig_end] == ordinal).item()
            or not torch.all(pocket_mask[pocket_start:pocket_end] == ordinal).item()
            or len(torch.unique(lig_sources[lig_start:lig_end])) != lig_end - lig_start
            or len(torch.unique(pocket_sources[pocket_start:pocket_end])) != pocket_end - pocket_start
        ):
            _fail("SAMPLE_SEGMENT_OR_SOURCE_INSTANCE_INVALID:" + event_id)
        ligand_local = _single_local_match(
            lig_sources[lig_start:lig_end],
            source.ligand.source_row_index,
            "LIGAND_C1_SOURCE_ROW_NOT_UNIQUE_IN_SAMPLE:" + event_id,
        )
        protein_local = _single_local_match(
            pocket_sources[pocket_start:pocket_end],
            source.protein.source_row_index,
            "PROTEIN_SG_SOURCE_ROW_NOT_UNIQUE_IN_SAMPLE:" + event_id,
        )
        ligand_flat = lig_start + ligand_local
        protein_flat = pocket_start + protein_local
        if (
            lig_parser[ligand_flat].item() != ligand_local
            or pocket_parser[protein_flat].item() != protein_local
            or lig_mask[ligand_flat].item() != ordinal
            or pocket_mask[protein_flat].item() != ordinal
        ):
            _fail("ENDPOINT_LOCAL_FLAT_SEGMENT_BINDING_INVALID:" + event_id)
        if (
            alignment.ligand_reactive_local_indices[ordinal].item() != ligand_local
            or alignment.ligand_reactive_flat_indices[ordinal].item() != ligand_flat
            or alignment.target_reactive_local_indices[ordinal].item() != protein_local
            or alignment.target_reactive_flat_indices[ordinal].item() != protein_flat
            or alignment.positive_pair_batch_indices[ordinal].item() != ordinal
            or alignment.positive_pair_ligand_local_indices[ordinal].item() != ligand_local
            or alignment.positive_pair_ligand_flat_indices[ordinal].item() != ligand_flat
            or alignment.positive_pair_pocket_local_indices[ordinal].item() != protein_local
            or alignment.positive_pair_pocket_flat_indices[ordinal].item() != protein_flat
        ):
            _fail("POSITIVE_PAIR_ENDPOINT_BINDING_INVALID:" + event_id)
        if (
            alignment.ligand_role_valid[ligand_flat].item() is not True
            or alignment.ligand_generation_mask[ligand_flat, 0].item() is not True
            or alignment.ligand_fixed_mask[ligand_flat, 0].item() is not False
            or alignment.ligand_target_mask[ligand_flat, 0].item() is not True
            or alignment.ligand_context_mask[ligand_flat, 0].item() is not False
            or torch.argmax(lig_one_hot[ligand_flat]).item() != carbon_channel
            or alignment.target_residue_membership_mask[protein_flat, 0].item() is not True
            or alignment.target_residue_reactive_atom_mask[protein_flat, 0].item() is not True
            or torch.argmax(pocket_one_hot[protein_flat]).item() != sulfur_channel
        ):
            _fail("ENDPOINT_ROLE_OR_ELEMENT_CHANNEL_INVALID:" + event_id)

        bindings.append(
            FFQExact4PostEventSourceIndexBindingV1(
                canonical_event_id=event_id,
                batch_ordinal=ordinal,
                task_semantic_name="warhead_only",
                canonical_task_id=0,
                purpose=_PURPOSE,
                component_index=1,
                unit=_UNIT,
                label_use_formal_sha256=LABEL_USE_FORMAL_SHA256_V1,
                label_use_event_decision_locator=source.formal.label_use_event_locator,
                post_observation_formal_sha256=POST_OBSERVATION_FORMAL_SHA256_V1,
                post_observation_event_locator=source.formal.observation_event_locator,
                post_observation_distance_field_locator=source.formal.observation_distance_field_locator,
                ligand_C1=FFQExact4EndpointSourceIndexBindingV1(
                    endpoint_semantic_name="ligand_C1",
                    source_identity=source.ligand.source_identity,
                    source_atom_site_row_index_0based=source.ligand.source_row_index,
                    node_domain="ligand",
                    local_node_index=ligand_local,
                    flat_node_index=ligand_flat,
                    sample_segment_start_inclusive=lig_start,
                    sample_segment_end_exclusive=lig_end,
                ),
                protein_SG=FFQExact4EndpointSourceIndexBindingV1(
                    endpoint_semantic_name="protein_SG",
                    source_identity=source.protein.source_identity,
                    source_atom_site_row_index_0based=source.protein.source_row_index,
                    node_domain="pocket",
                    local_node_index=protein_local,
                    flat_node_index=protein_flat,
                    sample_segment_start_inclusive=pocket_start,
                    sample_segment_end_exclusive=pocket_end,
                ),
                effective_supervision_schema_version=str(
                    record["effective_supervision_schema_version"]
                ),
                effective_supervision_record_sha256=str(
                    record["effective_supervision_record_sha256"]
                ),
                pocket_seed_policy=POCKET_SEED_POLICY_V1,
            )
        )
    return tuple(bindings)


def build_covapie_ffq_exact4_post_source_index_binding_v1(
    *,
    samples: object,
    label_use_formal_bytes: object,
    post_observation_formal_bytes: object,
) -> FFQExact4PostSourceIndexBindingResultV1:
    """Build the frozen Exact4 source-to-index binding without filesystem I/O."""

    label_use = _strict_frozen_json(
        label_use_formal_bytes,
        expected_sha256=LABEL_USE_FORMAL_SHA256_V1,
        label="LABEL_USE_FORMAL",
    )
    observation = _strict_frozen_json(
        post_observation_formal_bytes,
        expected_sha256=POST_OBSERVATION_FORMAL_SHA256_V1,
        label="POST_OBSERVATION_FORMAL",
    )
    formal_sources = _validate_formal_documents_v1(label_use, observation)
    validated_samples = _validate_samples(samples)
    resolved_sources = _resolve_structure_sources(validated_samples, formal_sources)
    try:
        alignment = alignment_owner.assemble_covapie_ffq_real_structure_microbatch_alignment_v1(
            samples=validated_samples,
            device="cpu",
            pocket_seed_policy="fixed_scaffold_warhead_only_v1",
        )
    except Exception as error:
        raise FFQExact4PostSourceIndexBindingError(
            f"{_ERROR}:STRUCTURAL_ASSEMBLER_REJECTED:{type(error).__name__}:{error}"
        ) from error
    bindings = _validate_alignment_and_build_bindings_v1(
        samples=validated_samples,
        resolved_sources=resolved_sources,
        alignment=alignment,
    )
    return FFQExact4PostSourceIndexBindingResultV1(
        structural_alignment=alignment, source_index_bindings=bindings
    )
