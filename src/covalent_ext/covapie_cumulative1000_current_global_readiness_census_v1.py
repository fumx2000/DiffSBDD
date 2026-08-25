"""Materialize the cumulative1000 current global readiness census V1.

CURRENT GLOBAL READINESS CENSUS IS A DERIVED PROJECTION, NOT AN AUTHORITY
CREATION LAYER.  This metadata-only owner verifies frozen published inputs,
calls their published reconciliation/projection owners, and creates one
deterministic row per frozen event.  It creates no human or chemistry
decision, reusable authority, training admission, tensor, model call, loss,
optimizer action, parameter update, dataset mutation, or training run.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import csv
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any, NoReturn

from . import covapie_completed_human_decision_reconciliation_v1 as reconciliation
from . import covapie_completed_human_decision_reconciliation_with_g3h_v1 as current_reconciliation
from . import covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1 as exact5_owner
from . import covapie_poa_full_component_formal_split_authority_v1 as poa_split_owner
from . import covapie_poa_sample_level_effective_supervision_v1 as poa_owner


__all__ = (
    "Cumulative1000CurrentGlobalReadinessCensusError",
    "Cumulative1000CurrentGlobalReadinessComputationV1",
    "CENSUS_COLUMNS_V1",
    "CANONICAL_EXACT5_V1",
    "EXPECTED_CENSUS_PROJECTION_SHA256_V1",
    "EXPECTED_SUMMARY_PAYLOAD_SHA256_V1",
    "EXPECTED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1",
    "compute_covapie_cumulative1000_current_global_readiness_census_v1",
    "validate_covapie_cumulative1000_current_global_readiness_census_v1",
    "build_covapie_cumulative1000_current_global_readiness_artifacts_v1",
    "materialize_covapie_cumulative1000_current_global_readiness_artifacts_v1",
)


SCHEMA_VERSION = "covapie_cumulative1000_current_global_readiness_census_v1"
STAGE = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_V1"
ERROR_TOKEN = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_V1_ERROR"

OUTPUT_DIRECTORY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_v1"
)
CENSUS_FILE = "covapie_cumulative1000_current_global_readiness_census_v1.csv"
SUMMARY_FILE = "covapie_cumulative1000_current_global_readiness_summary_v1.json"
MANIFEST_FILE = "covapie_cumulative1000_current_global_readiness_manifest_v1.json"

PRODUCTION_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_cumulative1000_current_global_readiness_census_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_cumulative1000_current_global_readiness_census_v1.py"
)
GUIDE_RELATIVE = Path(
    "docs/covapie_cumulative1000_current_global_readiness_census_v1_guide.md"
)

EXACT7_PATHS_V1 = (
    PRODUCTION_RELATIVE.as_posix(),
    CHECKER_RELATIVE.as_posix(),
    TEST_RELATIVE.as_posix(),
    GUIDE_RELATIVE.as_posix(),
    (OUTPUT_DIRECTORY_RELATIVE / CENSUS_FILE).as_posix(),
    (OUTPUT_DIRECTORY_RELATIVE / SUMMARY_FILE).as_posix(),
    (OUTPUT_DIRECTORY_RELATIVE / MANIFEST_FILE).as_posix(),
)

CANONICAL_EXACT5_V1 = (
    (0, "warhead_only", "A"),
    (1, "linker_plus_warhead", "B"),
    (2, "scaffold_plus_warhead", "B2"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)
STRICT_PROFILE = "STRICT_LINKER_PRESENT_V1"
DIRECT_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
ROLE_NOT_ESTABLISHED = "NOT_ESTABLISHED"
STRICT_TASK_IDS = (0, 1, 2, 3, 4)
DIRECT_TASK_IDS = (0, 3, 4)

CHEMISTRY_POSITIVE = "POSITIVE"
CHEMISTRY_NEGATIVE = "NEGATIVE"
CHEMISTRY_NOT_ESTABLISHED = "NOT_ESTABLISHED"
CHEMISTRY_UNRESOLVED = "UNRESOLVED"
TASK_RELEVANT = "RELEVANT"
TASK_NOT_RELEVANT = "NOT_RELEVANT"
TASK_UNRESOLVED = "UNRESOLVED"
TRAINING_UNRESOLVED = "UNRESOLVED"

GLOBAL_STATUSES_V1 = (
    reconciliation.CURRENTLY_UNREVIEWED,
    reconciliation.CURRENTLY_IN_PROGRESS,
    reconciliation.COMPLETED_HUMAN_POSITIVE,
    reconciliation.COMPLETED_HUMAN_NEGATIVE,
    reconciliation.COMPLETED_PARTIAL_AUTHORITY,
    reconciliation.CURRENT_RUNTIME_MODEL_USABLE,
    reconciliation.PUBLISHED_EXACT_AUTO_NEGATIVE,
    "LEAKAGE_EXISTING_GROUP_CONFLICT",
    "STRUCTURAL_EVIDENCE_INCOMPLETE",
    "QUARANTINE_REPRESENTATION_GAP",
    "REJECTED_FEATURE_INCOMPATIBLE",
)

EXPECTED_GLOBAL_STATUS_COUNTS_V1 = {
    reconciliation.CURRENTLY_UNREVIEWED: 273,
    reconciliation.CURRENTLY_IN_PROGRESS: 9,
    reconciliation.COMPLETED_HUMAN_POSITIVE: 32,
    reconciliation.COMPLETED_HUMAN_NEGATIVE: 54,
    reconciliation.COMPLETED_PARTIAL_AUTHORITY: 1,
    reconciliation.CURRENT_RUNTIME_MODEL_USABLE: 17,
    reconciliation.PUBLISHED_EXACT_AUTO_NEGATIVE: 32,
    "LEAKAGE_EXISTING_GROUP_CONFLICT": 369,
    "STRUCTURAL_EVIDENCE_INCOMPLETE": 133,
    "QUARANTINE_REPRESENTATION_GAP": 78,
    "REJECTED_FEATURE_INCOMPATIBLE": 2,
}

EXPECTED_EVENT_SET_SHA256_V1 = {
    "universe": "f74d4e568d97ac23e2bc2cba2e8473e6705b726daf92204868efb1afbe0453ce",
    "chemistry_positive": "60407f93dca67d192d622aecb054d4016934e43a321295f413905ca6fa3b2bdc",
    "chemistry_not_established": "38cc71900a3a2158c2cf562123c4783360aac300873480ddc2f239315d730344",
    "chemistry_unresolved": "b958a01a8d7258950ae6dc80bbd4983ff297586b8c97d2a2ad184c773bd58a12",
    "task_relevant": "beb8b17508e71234f77c4731e6abbd23fd3e3d4cb2b373b5b15632b546811061",
    "training_include": "b10edcff066c41d1bbdce5314ed9ad5db948ccab5c769f6cbeef21c66416f0df",
    "training_exclude": "12b8d1520b51d1a06d2bd580e16925066539deeb6bd1bf6bdc2ad299efb22b12",
}

# These are derived V1 contract digests, not human, chemistry, reusable, or
# training authority.  The SHA-bound frozen semantic sources must map to one
# exact event-level projection, summary payload, and merged binding inventory.
EXPECTED_CENSUS_PROJECTION_SHA256_V1 = (
    "f4f44058a68f8161969b84a7e6b5efde08d6cd1d59520010c4f742d78b171dc9"
)
EXPECTED_SUMMARY_PAYLOAD_SHA256_V1 = (
    "569625aef3b22d12af528e2afe61ed5ebf381f84642a063a81970894b80dc74a"
)
EXPECTED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1 = (
    "d60abb26511d05f13f51656b9c8954794942b87babb514a8858262f13c54baaf"
)

CENSUS_COLUMNS_V1 = (
    "scaleup_rank",
    "canonical_event_id",
    "pdb_id",
    "ligand_component_id",
    "raw_structure_available",
    "exact_cys_sg_event_recovered",
    "explicit_covalent_evidence",
    "distance_only_event_inference_used",
    "full_coordinate_post_evidence_available",
    "ccd_graph_complete",
    "feature_compatible",
    "structural_processing_success",
    "post_geometry_source_evidence_available",
    "representation_gap",
    "feature_incompatible",
    "current_global_status",
    "priority_review_in_scope",
    "review_unit_id",
    "current_review_status",
    "human_review_completed",
    "human_review_authority_source",
    "chemistry_disposition",
    "chemistry_authority_source",
    "task_relevance_disposition",
    "task_relevance_authority_source",
    "training_use_disposition",
    "human_training_excluded",
    "reactive_pair_raw_structural_evidence",
    "reactive_pair_sample_authoritative",
    "reactive_pair_training_target_available",
    "role_partition_sample_authoritative",
    "role_profile",
    "canonical_mask_structural_labels_available",
    "structurally_applicable_task_ids_json",
    "post_geometry_sample_authoritative",
    "post_geometry_training_target_available",
    "pre_geometry_authoritative",
    "pre_geometry_training_target_available",
    "training_use_include",
    "future_training_admission_candidate",
    "formal_split_authoritative",
    "formal_split",
    "formal_training_admitted",
    "current_runtime_model_usable",
    "training_materialization_allowed_current_source",
    "positive_authority_source",
    "feature_semantics_status",
)

_BOOL_COLUMNS = frozenset(
    {
        "raw_structure_available",
        "exact_cys_sg_event_recovered",
        "explicit_covalent_evidence",
        "distance_only_event_inference_used",
        "full_coordinate_post_evidence_available",
        "ccd_graph_complete",
        "feature_compatible",
        "structural_processing_success",
        "post_geometry_source_evidence_available",
        "representation_gap",
        "feature_incompatible",
        "priority_review_in_scope",
        "human_review_completed",
        "human_training_excluded",
        "reactive_pair_raw_structural_evidence",
        "reactive_pair_sample_authoritative",
        "reactive_pair_training_target_available",
        "role_partition_sample_authoritative",
        "canonical_mask_structural_labels_available",
        "post_geometry_sample_authoritative",
        "post_geometry_training_target_available",
        "pre_geometry_authoritative",
        "pre_geometry_training_target_available",
        "training_use_include",
        "future_training_admission_candidate",
        "formal_split_authoritative",
        "formal_training_admitted",
        "current_runtime_model_usable",
    }
)


@dataclass(frozen=True, slots=True)
class _SourceSpecV1:
    artifact_role: str
    path: str
    path_namespace: str
    byte_count: int
    sha256: str


_UNIVERSE = (
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1/"
    "covapie_bulk_cys_sg_cumulative_1000_model_usable_census_v1.csv"
)
_STRUCTURAL_1_500 = (
    "covapie-state/bulk-500-controlled-execution-v1/attempt-001/"
    "cumulative_processing_view_v1.json"
)
_STRUCTURAL_501_1000 = (
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1/"
    "covapie_bulk_cys_sg_ranks_0501_1000_processing_outcomes_v1.json"
)
_QUEUE = (
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1/"
    "covapie_bulk_cys_sg_priority_human_review_queue_v1.csv"
)
_LEGACY_HUMAN = (
    "data/derived/covalent_small/covapie_bulk_post_only_cys_sg_human_review_v1/"
    "covapie_post_only_human_review_decisions_v1.json"
)
_BATCH_SNAPSHOT = (
    "data/derived/covalent_small/"
    "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1/"
    "covapie_batch001_completed_human_decision_snapshot_v1.json"
)
_RUNTIME_INDEX = (
    "data/derived/covalent_small/covapie_existing_positive_runtime_and_split_closure_v1/"
    "covapie_current_runtime_model_usable_positive_index_v1.csv"
)
_RUNTIME_INVENTORY = (
    "data/derived/covalent_small/covapie_existing_positive_runtime_and_split_closure_v1/"
    "covapie_existing_positive_runtime_binding_inventory_v1.csv"
)
_FFQ_EVENT = (
    "data/derived/covalent_small/"
    "covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1/"
    "covapie_ffq_event_task_label_availability_v1.csv"
)
_G3H_EVENT = (
    "data/derived/covalent_small/"
    "covapie_g3h_completed_decision_ingestion_and_task_label_availability_v1/"
    "covapie_g3h_event_task_label_availability_v1.csv"
)
_HISTORICAL_RECONCILIATION = reconciliation.HISTORICAL_RECONCILIATION_RELATIVE.as_posix()

_FFQ_FORMAL = reconciliation.FFQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
_POA_FORMAL = reconciliation.POA_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
_G3H_FORMAL = current_reconciliation._G3H_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()

_DIRECT_SOURCE_SPECS_V1 = (
    _SourceSpecV1("FROZEN_CUMULATIVE1000_UNIVERSE", _UNIVERSE, "repository_relative", 492899, "5998991f4a777dc8364d773e68a438837e656983aab805dae388b64c3619dbc5"),
    _SourceSpecV1("STRUCTURAL_RANKS_0001_0500", _STRUCTURAL_1_500, "repository_parent_relative", 6469651, "a27d4bf7977d5a175387af83021270c68f9cf3e8db391113dc6f1ff22f0bfc44"),
    _SourceSpecV1("STRUCTURAL_RANKS_0501_1000", _STRUCTURAL_501_1000, "repository_relative", 5988559, "4f5ee75a645ee560cb8e272fd3ead8ba7a446dadf9aece38f12f0eeecad16e5f"),
    _SourceSpecV1("CURRENT_G3H_RECONCILIATION_OWNER", "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_g3h_v1.py", "repository_relative", 12686, "2e1e0775b8123d7266bcc6d462a9b39c0ce3c0c9385e7aba4eee1f2fb5c367a6"),
    _SourceSpecV1("GENERIC_RECONCILIATION_OWNER", "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py", "repository_relative", 35925, "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548"),
    _SourceSpecV1("HISTORICAL_RECONCILIATION", _HISTORICAL_RECONCILIATION, "repository_relative", 99335, "4eb608e2d97b60230ae1e0ca4e4be6a7fe8b3dc45af3467cbc98f685c385862f"),
    _SourceSpecV1("PRIORITY_REVIEW_QUEUE", _QUEUE, "repository_relative", 50116, "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"),
    _SourceSpecV1("LEGACY_HUMAN_AUTHORITY", _LEGACY_HUMAN, "repository_relative", 91133, "c2060a8b0a8123fbc6b9c11f2e70a9443367b63467bf9f9cf913a4c780168441"),
    _SourceSpecV1("BATCH001_HUMAN_SNAPSHOT", _BATCH_SNAPSHOT, "repository_relative", 33764, "c0c887b9026638484ae453d68a6fc654e3bd1b3bce7aa222f8a285d4878e0200"),
    _SourceSpecV1("CURRENT_RUNTIME_POSITIVE_INDEX", _RUNTIME_INDEX, "repository_relative", 13511, "5485305a750129e437ef68b43c758f9f0586add41fe54ee1d621b6c5bde62410"),
    _SourceSpecV1("CURRENT_RUNTIME_BINDING_INVENTORY", _RUNTIME_INVENTORY, "repository_relative", 45567, "b8a0f4c2bc8ca46141775f0a5fa54322d12db685b37c930659f6f4a1ca3b4052"),
    _SourceSpecV1("CURRENT_RUNTIME_OWNER", "src/covalent_ext/covapie_existing_positive_runtime_and_split_closure_v1.py", "repository_relative", 103692, "dbca845ccaa7859e78301e413c676d40d28e49228471274f99e4d77c55d2816c"),
    _SourceSpecV1("FFQ_EVENT_PROJECTION", _FFQ_EVENT, "repository_relative", 21239, "781972cbee68403805bb0266db65221b0973cb61e666925264dc0d50524090a0"),
    _SourceSpecV1("FFQ_INGESTION_OWNER", "src/covalent_ext/covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1.py", "repository_relative", 66788, "2e71c3132a15f500d54430075688c37dc79469b096328943795c98a728fca7ce"),
    _SourceSpecV1("FFQ_ROLE_MASK_TENSORIZER_OWNER", "src/covalent_ext/covapie_ffq_direct_profile_role_mask_tensorizer_v1.py", "repository_relative", 12385, "aae4df0ee0b39d5a6ade2be4d98abc4daa03f03c929926a06ba3f7040f183252"),
    _SourceSpecV1("FFQ_MODEL_BOUND_PAIR_PROJECTION_OWNER", "src/covalent_ext/covapie_ffq_supervised_forward_adapter_v1.py", "repository_relative", 40954, "a5363fbc238debfee95626b805d439e8ee23232f5536f6aefa08a73e073efc4e"),
    _SourceSpecV1("POA_SAMPLE_EFFECTIVE_SUPERVISION_OWNER", "src/covalent_ext/covapie_poa_sample_level_effective_supervision_v1.py", "repository_relative", 42406, "f4656f414a5d31d5e967b39885dd5d89e9bf205135dbd29b3285e0d1e856367f"),
    _SourceSpecV1("POA_FORMAL_SPLIT_OWNER", "src/covalent_ext/covapie_poa_full_component_formal_split_authority_v1.py", "repository_relative", 83848, "fa466fc335b664bec5063711a6da9576b0781594f9818f7f34be9f6090d491a8"),
    _SourceSpecV1("POA_MODEL_BOUND_PAIR_PROJECTION_OWNER", "src/covalent_ext/covapie_poa_exact16_real_structure_tensor_preview_v1.py", "repository_relative", 61559, "91b26dd9e0aae8cbda34c769cf98d766910b9b497f5ca1133105f8858072f989"),
    _SourceSpecV1("G3H_EVENT_PROJECTION", _G3H_EVENT, "repository_relative", 20247, "f7afc5caf16bb81e18223258cfb39be79c7a18dd4938b756599ad228f6cffe10"),
    _SourceSpecV1("G3H_INGESTION_OWNER", "src/covalent_ext/covapie_g3h_completed_decision_ingestion_and_task_label_availability_v1.py", "repository_relative", 72232, "ce64741183a384a238ebd8e905b4fd14b03c662021aa1e3ba3a23828a803d418"),
    _SourceSpecV1("EXACT5_SEMANTIC_OWNER", "src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py", "repository_relative", 67274, "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b"),
    _SourceSpecV1("FFQ_FORMAL_HUMAN_DECISION", _FFQ_FORMAL, "repository_parent_relative", 14197, "ba0670519064399b2ecb0c73631009c8c6c4d3c14512377ecfaad0d87388e149"),
    _SourceSpecV1("POA_FORMAL_HUMAN_DECISION", _POA_FORMAL, "repository_parent_relative", 15675, "263eec2e33a7b50001f6c058959b9218601fc7fb122dc97e937b517f98c90ba8"),
    _SourceSpecV1("G3H_FORMAL_HUMAN_DECISION", _G3H_FORMAL, "repository_parent_relative", 22456, "872ac01500180f752928aeb2fb44287b7fa9cad7070e1b17a45f0d19b25d5203"),
)

_DIRECT_SPEC_BY_PATH = {spec.path: spec for spec in _DIRECT_SOURCE_SPECS_V1}
_SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class Cumulative1000CurrentGlobalReadinessComputationV1:
    rows: tuple[dict[str, str], ...]
    summary: dict[str, Any]
    semantic_source_bindings: tuple[dict[str, object], ...]


class Cumulative1000CurrentGlobalReadinessCensusError(ValueError):
    """Raised unless every V1 census invariant can be proven."""


def _fail(reason: str) -> NoReturn:
    raise Cumulative1000CurrentGlobalReadinessCensusError(
        f"{ERROR_TOKEN}:{reason}"
    )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _event_set_sha256(event_ids: Sequence[str] | set[str]) -> str:
    return _sha256(_canonical_json(sorted(event_ids)).encode("utf-8"))


def _bool_cell(value: bool) -> str:
    if type(value) is not bool:
        _fail("BOOLEAN_VALUE_REQUIRED")
    return "true" if value else "false"


def _parse_bool(value: str, label: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    _fail("BOOLEAN_CELL_INVALID:" + label)


def _resolve_source_path(repo_root: Path, spec: _SourceSpecV1) -> Path:
    if spec.path_namespace == "repository_relative":
        return repo_root / spec.path
    if spec.path_namespace == "repository_parent_relative":
        return repo_root.parent / spec.path
    _fail("SOURCE_PATH_NAMESPACE_INVALID:" + spec.artifact_role)


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        _fail("SOURCE_NOT_REGULAR_FILE:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusError(
            f"{ERROR_TOKEN}:SOURCE_READ_FAILED:{label}"
        ) from error


def _verify_source_payload(spec: _SourceSpecV1, payload: bytes) -> dict[str, object]:
    if type(payload) is not bytes:
        _fail("SOURCE_PAYLOAD_NOT_BYTES:" + spec.artifact_role)
    if len(payload) != spec.byte_count:
        _fail("SOURCE_BYTE_COUNT_MISMATCH:" + spec.artifact_role)
    observed = _sha256(payload)
    if observed != spec.sha256:
        _fail("SOURCE_SHA256_MISMATCH:" + spec.artifact_role)
    return {
        "artifact_role": spec.artifact_role,
        "path": spec.path,
        "path_namespace": spec.path_namespace,
        "byte_count": len(payload),
        "sha256": observed,
    }


def _load_direct_sources(
    repo_root: Path,
) -> tuple[dict[str, bytes], list[dict[str, object]]]:
    payloads: dict[str, bytes] = {}
    bindings: list[dict[str, object]] = []
    for spec in _DIRECT_SOURCE_SPECS_V1:
        payload = _read_regular_file(
            _resolve_source_path(repo_root, spec), spec.artifact_role
        )
        bindings.append(_verify_source_payload(spec, payload))
        payloads[spec.path] = payload
    return payloads, bindings


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("JSON_DUPLICATE_KEY:" + key)
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    _fail("JSON_NONFINITE_CONSTANT:" + value)


def _strict_json(payload: bytes, label: str) -> Any:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusError(
            f"{ERROR_TOKEN}:JSON_NOT_UTF8:{label}"
        ) from error
    if text.startswith("\ufeff") or "\x00" in text or "\r" in text:
        _fail("JSON_TEXT_INVARIANT_INVALID:" + label)
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusError(
            f"{ERROR_TOKEN}:JSON_PARSE_FAILED:{label}"
        ) from error


def _strict_json_object(payload: bytes, label: str) -> dict[str, Any]:
    value = _strict_json(payload, label)
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _parse_csv(payload: bytes, label: str) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusError(
            f"{ERROR_TOKEN}:CSV_NOT_UTF8:{label}"
        ) from error
    if text.startswith("\ufeff") or "\x00" in text or "\r" in text:
        _fail("CSV_TEXT_INVARIANT_INVALID:" + label)
    reader = csv.DictReader(io.StringIO(text, newline=""))
    header = tuple(reader.fieldnames or ())
    if not header or len(set(header)) != len(header):
        _fail("CSV_HEADER_INVALID:" + label)
    try:
        rows = [dict(row) for row in reader]
    except csv.Error as error:
        raise Cumulative1000CurrentGlobalReadinessCensusError(
            f"{ERROR_TOKEN}:CSV_PARSE_FAILED:{label}"
        ) from error
    if any(tuple(row) != header or None in row for row in rows):
        _fail("CSV_ROW_SCHEMA_INVALID:" + label)
    return header, rows


def _csv_bytes(rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=CENSUS_COLUMNS_V1,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != CENSUS_COLUMNS_V1:
            _fail("CENSUS_ROW_SCHEMA_INVALID")
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def _require_columns(header: Sequence[str], required: set[str], label: str) -> None:
    missing = required - set(header)
    if missing:
        _fail("SOURCE_REQUIRED_COLUMN_MISSING:" + label + ":" + sorted(missing)[0])


def _validate_exact5_contract(tasks: object = CANONICAL_EXACT5_V1) -> None:
    if type(tasks) not in (tuple, list):
        _fail("EXACT5_CONTRACT_CONTAINER_INVALID")
    normalized = tuple(tuple(item) for item in tasks)
    if normalized != CANONICAL_EXACT5_V1:
        if not any(len(item) >= 3 and item[2] == "B3" for item in normalized):
            _fail("EXACT5_B3_OMITTED")
        if len(normalized) != 5:
            _fail("EXACT5_TASK_COUNT_INVALID")
        _fail("EXACT5_CONTRACT_DRIFT")
    owner_tasks = tuple(
        (task_id, semantic_name, alias)
        for task_id, semantic_name, alias, _target, _context in exact5_owner.CANONICAL_TASKS
    )
    if owner_tasks != CANONICAL_EXACT5_V1:
        _fail("EXACT5_SEMANTIC_OWNER_DRIFT")


def _parse_universe(payload: bytes) -> tuple[dict[str, str], ...]:
    header, rows = _parse_csv(payload, "FROZEN_UNIVERSE")
    required = {
        "scaleup_rank",
        "canonical_event_id",
        "pdb_id",
        "ligand_component_id",
        "task_domain_authority_status",
        "role_profile",
        "role_label_available",
        "reactive_pair_label_authoritative",
        "POST_geometry_label_authoritative",
        "terminal_route",
    }
    _require_columns(header, required, "FROZEN_UNIVERSE")
    if len(rows) != 1000:
        _fail("UNIVERSE_EVENT_COUNT_INVALID")
    seen: set[str] = set()
    ranks: list[int] = []
    for row in rows:
        event_id = row["canonical_event_id"]
        if not event_id or event_id in seen:
            _fail("UNIVERSE_CANONICAL_EVENT_DUPLICATE_OR_EMPTY")
        seen.add(event_id)
        try:
            rank = int(row["scaleup_rank"])
        except ValueError as error:
            raise Cumulative1000CurrentGlobalReadinessCensusError(
                f"{ERROR_TOKEN}:UNIVERSE_RANK_INVALID:{event_id}"
            ) from error
        ranks.append(rank)
        if not row["pdb_id"] or not row["ligand_component_id"]:
            _fail("UNIVERSE_IDENTITY_FIELD_EMPTY:" + event_id)
    if ranks != list(range(1, 1001)):
        _fail("UNIVERSE_RANKS_NOT_EXACT_1_1000")
    if len({row["pdb_id"] for row in rows}) != 546:
        _fail("UNIVERSE_UNIQUE_PDB_COUNT_INVALID")
    if len({row["ligand_component_id"] for row in rows}) != 416:
        _fail("UNIVERSE_UNIQUE_LIGAND_COUNT_INVALID")
    if _event_set_sha256(seen) != EXPECTED_EVENT_SET_SHA256_V1["universe"]:
        _fail("UNIVERSE_EVENT_SET_SHA256_MISMATCH")
    return tuple(rows)


def _validate_stage_statuses(
    outcome: Mapping[str, Any], *, event_id: str
) -> Mapping[str, Any]:
    stages = outcome.get("stage_statuses")
    if type(stages) is not dict:
        _fail("STRUCTURAL_STAGE_STATUSES_INVALID:" + event_id)
    expected = {
        f"BULK_{number:02d}_{suffix}"
        for number, suffix in (
            (1, "SOURCE_ACCESS_RESOLUTION"),
            (2, "SOURCE_DISCOVERY"),
            (3, "SOURCE_ADAPTER_NORMALIZATION"),
            (4, "CROSS_SOURCE_EVENT_DEDUP"),
            (5, "STRUCTURE_ACQUISITION"),
            (6, "MMCIF_VALIDATION"),
            (7, "EXACT_CYS_SG_EVENT_RECOVERY"),
            (8, "COMPONENT_TOPOLOGY_AND_ATOM_MAPPING"),
            (9, "MODEL_AND_FEATURE_COMPATIBILITY"),
            (10, "PRE_REACTION_REPRESENTABILITY"),
            (11, "EXISTING_EXACT_AUTHORITY_MATCH"),
            (12, "LEAKAGE_AND_SPLIT_PREDICTION"),
            (13, "AUTOMATIC_ROUTING"),
            (14, "HUMAN_REVIEW_CLUSTERING"),
            (15, "SUMMARY"),
        )
    }
    if set(stages) != expected or any(type(value) is not str for value in stages.values()):
        _fail("STRUCTURAL_STAGE_SCHEMA_INVALID:" + event_id)
    return stages


def _structural_row(
    wrapper: Mapping[str, Any], *, expected_rank: int, lane: str
) -> dict[str, str]:
    if type(wrapper) is not dict:
        _fail("STRUCTURAL_EVENT_WRAPPER_INVALID")
    rank = wrapper.get("scaleup_rank")
    if type(rank) is not int or rank != expected_rank:
        _fail("STRUCTURAL_RANK_INVALID")
    outcome = wrapper.get("processing_outcome")
    if type(outcome) is not dict:
        _fail("STRUCTURAL_PROCESSING_OUTCOME_INVALID")
    event_id = outcome.get("canonical_event_id")
    if type(event_id) is not str or not event_id:
        _fail("STRUCTURAL_EVENT_ID_INVALID")
    if lane == "RANKS_0501_1000" and wrapper.get("canonical_event_id") != event_id:
        _fail("STRUCTURAL_WRAPPER_EVENT_ID_MISMATCH:" + event_id)
    if lane == "RANKS_0001_0500" and wrapper.get("lane") not in {
        "FROZEN_HISTORICAL_PREDECESSOR",
        "NEW_INCREMENTAL_EXECUTION",
    }:
        _fail("STRUCTURAL_LANE_INVALID:" + event_id)
    stages = _validate_stage_statuses(outcome, event_id=event_id)
    structural = outcome.get("structural_processing")
    if type(structural) is not dict:
        _fail("STRUCTURAL_PROCESSING_DETAILS_INVALID:" + event_id)
    terminal = outcome.get("terminal_outcome")
    allowed_terminal = {
        "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
        "LEAKAGE_EXISTING_GROUP_CONFLICT",
        "STRUCTURAL_EVIDENCE_INCOMPLETE",
        "QUARANTINE_REPRESENTATION_GAP",
        "REJECTED_FEATURE_INCOMPATIBLE",
    }
    if terminal not in allowed_terminal:
        _fail("STRUCTURAL_TERMINAL_OUTCOME_INVALID:" + event_id)

    raw = stages["BULK_05_STRUCTURE_ACQUISITION"] == "PASSED"
    recovered = stages["BULK_07_EXACT_CYS_SG_EVENT_RECOVERY"] == (
        "PASSED_EXPLICIT_EVENT"
    )
    feature = stages["BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"] == "PASSED"
    feature_incompatible = terminal == "REJECTED_FEATURE_INCOMPATIBLE"
    representation_gap = terminal == "QUARANTINE_REPRESENTATION_GAP"
    post_source = recovered and type(structural.get("post_distance_angstrom")) in {
        int,
        float,
    }
    if recovered != post_source:
        _fail("POST_SOURCE_EVIDENCE_PARITY_INVALID:" + event_id)
    if feature:
        if (
            structural.get("explicit_covalent_evidence") is not True
            or structural.get("distance_only_event_inference_used") is not False
            or structural.get("feature_projection_status") != "passed"
            or type(structural.get("ccd_component_graph")) is not dict
        ):
            _fail("STRUCTURAL_SUCCESS_DETAIL_INVALID:" + event_id)
    if feature_incompatible and (
        not recovered
        or stages["BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"] != "FAILED_CLOSED"
    ):
        _fail("FEATURE_INCOMPATIBLE_DETAIL_INVALID:" + event_id)
    return {
        "scaleup_rank": str(rank),
        "canonical_event_id": event_id,
        "pdb_id": str(outcome.get("pdb_id", "")),
        "ligand_component_id": str(outcome.get("ligand_component_id", "")),
        "raw_structure_available": _bool_cell(raw),
        "exact_cys_sg_event_recovered": _bool_cell(recovered),
        "explicit_covalent_evidence": _bool_cell(recovered),
        "distance_only_event_inference_used": "false",
        "full_coordinate_post_evidence_available": _bool_cell(post_source),
        "ccd_graph_complete": _bool_cell(feature),
        "feature_compatible": _bool_cell(feature),
        "structural_processing_success": _bool_cell(feature),
        "post_geometry_source_evidence_available": _bool_cell(post_source),
        "representation_gap": _bool_cell(representation_gap),
        "feature_incompatible": _bool_cell(feature_incompatible),
        "raw_terminal_outcome": str(terminal),
    }


def _parse_structural_sources(
    first_payload: bytes, second_payload: bytes, universe: Sequence[Mapping[str, str]]
) -> dict[str, dict[str, str]]:
    first = _strict_json_object(first_payload, "STRUCTURAL_RANKS_0001_0500")
    second = _strict_json_object(second_payload, "STRUCTURAL_RANKS_0501_1000")
    if (
        first.get("schema_version") != "covapie_bulk_500_event_executor_v1"
        or first.get("cumulative_new_event_count") != 500
        or first.get("production_authority_created") is not False
        or first.get("training_materialization_performed") is not False
    ):
        _fail("STRUCTURAL_FIRST_SOURCE_IDENTITY_INVALID")
    if (
        second.get("schema_version")
        != "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1"
        or second.get("rank_start") != 501
        or second.get("rank_end") != 1000
        or second.get("terminal_outcome_count") != 500
        or second.get("production_authority_created") is not False
        or second.get("training_performed") is not False
        or second.get("PRE_geometry_fabricated") is not False
    ):
        _fail("STRUCTURAL_SECOND_SOURCE_IDENTITY_INVALID")
    first_events = first.get("events")
    second_events = second.get("events")
    if type(first_events) is not list or len(first_events) != 500:
        _fail("STRUCTURAL_FIRST_EVENT_COUNT_INVALID")
    if type(second_events) is not list or len(second_events) != 500:
        _fail("STRUCTURAL_SECOND_EVENT_COUNT_INVALID")
    rows = [
        _structural_row(wrapper, expected_rank=index, lane="RANKS_0001_0500")
        for index, wrapper in enumerate(first_events, 1)
    ] + [
        _structural_row(wrapper, expected_rank=index, lane="RANKS_0501_1000")
        for index, wrapper in enumerate(second_events, 501)
    ]
    if len({row["canonical_event_id"] for row in rows}) != 1000:
        _fail("STRUCTURAL_CANONICAL_EVENT_DUPLICATE")
    for source, frozen in zip(rows, universe):
        if (
            source["scaleup_rank"] != frozen["scaleup_rank"]
            or source["canonical_event_id"] != frozen["canonical_event_id"]
            or source["pdb_id"] != frozen["pdb_id"]
            or source["ligand_component_id"] != frozen["ligand_component_id"]
        ):
            _fail("STRUCTURAL_UNIVERSE_IDENTITY_MISMATCH")
    expected = {
        "raw_structure_available": 997,
        "exact_cys_sg_event_recovered": 867,
        "explicit_covalent_evidence": 867,
        "distance_only_event_inference_used": 0,
        "full_coordinate_post_evidence_available": 867,
        "ccd_graph_complete": 865,
        "feature_compatible": 865,
        "structural_processing_success": 865,
        "post_geometry_source_evidence_available": 867,
        "representation_gap": 78,
        "feature_incompatible": 2,
    }
    for field, count in expected.items():
        if sum(row[field] == "true" for row in rows) != count:
            _fail("STRUCTURAL_COUNT_INVALID:" + field)
    return {row["canonical_event_id"]: row for row in rows}


def _parse_queue(
    payload: bytes,
) -> tuple[dict[str, dict[str, str]], dict[str, str], tuple[dict[str, str], ...]]:
    header, rows = _parse_csv(payload, "PRIORITY_REVIEW_QUEUE")
    required = {
        "priority_rank",
        "review_unit_id",
        "event_count",
        "canonical_event_ids_json",
        "pdb_ids_json",
        "ligand_component_ids_json",
        "full_coordinate_event_count",
        "exact_reactive_pair_event_count",
        "CCD_graph_complete_event_count",
        "POST_geometry_available_event_count",
    }
    _require_columns(header, required, "PRIORITY_REVIEW_QUEUE")
    if len(rows) != 131:
        _fail("PRIORITY_QUEUE_UNIT_COUNT_INVALID")
    by_unit: dict[str, dict[str, str]] = {}
    event_to_unit: dict[str, str] = {}
    for row in rows:
        unit = row["review_unit_id"]
        if not unit or unit in by_unit:
            _fail("PRIORITY_QUEUE_UNIT_DUPLICATE_OR_EMPTY")
        by_unit[unit] = row
        try:
            event_ids = json.loads(row["canonical_event_ids_json"])
            pdb_ids = json.loads(row["pdb_ids_json"])
            ligands = json.loads(row["ligand_component_ids_json"])
            event_count = int(row["event_count"])
        except (json.JSONDecodeError, ValueError) as error:
            raise Cumulative1000CurrentGlobalReadinessCensusError(
                f"{ERROR_TOKEN}:PRIORITY_QUEUE_FIELD_INVALID:{unit}"
            ) from error
        if (
            type(event_ids) is not list
            or len(event_ids) != event_count
            or len(set(event_ids)) != event_count
            or type(pdb_ids) is not list
            or type(ligands) is not list
        ):
            _fail("PRIORITY_QUEUE_UNIT_EVENT_INVENTORY_INVALID:" + unit)
        for event_id in event_ids:
            if type(event_id) is not str or event_id in event_to_unit:
                _fail("PRIORITY_QUEUE_EVENT_DUPLICATE_OR_INVALID")
            event_to_unit[event_id] = unit
    if len(event_to_unit) != 338:
        _fail("PRIORITY_QUEUE_EVENT_COUNT_INVALID")
    return by_unit, event_to_unit, tuple(rows)


def _legacy_human_sets(
    payload: bytes,
) -> tuple[
    set[str],
    set[str],
    set[str],
    dict[str, str],
]:
    source = _strict_json_object(payload, "LEGACY_HUMAN_AUTHORITY")
    if (
        source.get("schema_version") != "covapie_post_only_human_review_decisions_v1"
        or source.get("production_authority_created") is not False
        or source.get("production_materialization_performed") is not False
        or source.get("training_materialization_performed") is not False
    ):
        _fail("LEGACY_HUMAN_SOURCE_IDENTITY_INVALID")
    units = source.get("units")
    if type(units) is not list or len(units) != 36:
        _fail("LEGACY_HUMAN_UNIT_INVENTORY_INVALID")
    negative: set[str] = set()
    completed_positive: set[str] = set()
    partial: set[str] = set()
    event_to_unit: dict[str, str] = {}
    for unit in units:
        if type(unit) is not dict:
            _fail("LEGACY_HUMAN_UNIT_INVALID")
        unit_id = unit.get("review_unit_id")
        status = unit.get("workflow_status")
        relevance = unit.get("training_domain_relevance_decision")
        events = unit.get("events")
        if type(unit_id) is not str or not unit_id or type(events) is not list:
            _fail("LEGACY_HUMAN_UNIT_IDENTITY_INVALID")
        for event in events:
            if type(event) is not dict:
                _fail("LEGACY_HUMAN_EVENT_INVALID")
            event_id = event.get("canonical_event_id")
            if type(event_id) is not str or not event_id or event_id in event_to_unit:
                _fail("LEGACY_HUMAN_EVENT_DUPLICATE_OR_INVALID")
            event_to_unit[event_id] = unit_id
            if status == "COMPLETED" and relevance == (
                "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"
            ):
                if event.get("event_training_use_decision") not in {"", None}:
                    _fail("LEGACY_NEGATIVE_TRAINING_DISPOSITION_INVALID:" + event_id)
                negative.add(event_id)
            elif status == "COMPLETED" and relevance == (
                "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
            ):
                if (
                    event.get("event_training_use_decision") != "INCLUDE"
                    or event.get("post_geometry_training_usable") != "YES"
                ):
                    _fail("LEGACY_POSITIVE_DISPOSITION_INVALID:" + event_id)
                completed_positive.add(event_id)
            elif status == "IN_PROGRESS" and relevance == (
                "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
            ):
                if (
                    event.get("event_training_use_decision") not in {"", None}
                    or event.get("post_geometry_training_usable") not in {"", None}
                ):
                    _fail("LEGACY_PARTIAL_DISPOSITION_INVALID:" + event_id)
                partial.add(event_id)
    if (len(negative), len(completed_positive), len(partial)) != (30, 4, 1):
        _fail("LEGACY_HUMAN_CURRENT_SET_COUNTS_INVALID")
    return negative, completed_positive, partial, event_to_unit


def _batch_snapshot_sets(
    payload: bytes,
) -> tuple[set[str], set[str], dict[str, str]]:
    source = _strict_json_object(payload, "BATCH001_HUMAN_SNAPSHOT")
    if (
        source.get("schema_version")
        != "covapie_batch001_completed_human_decision_snapshot_v1"
        or source.get("counts")
        != {
            "completed_negative_event_count": 24,
            "completed_negative_unit_count": 4,
            "completed_positive_event_count": 13,
            "completed_positive_unit_count": 5,
            "duplicate_event_count": 0,
            "duplicate_unit_count": 0,
            "event_count": 37,
            "in_progress_units_ingested": 0,
            "unit_count": 9,
        }
    ):
        _fail("BATCH001_SNAPSHOT_IDENTITY_OR_COUNTS_INVALID")
    decisions = source.get("completed_human_decisions")
    if type(decisions) is not list or len(decisions) != 9:
        _fail("BATCH001_SNAPSHOT_DECISIONS_INVALID")
    negative: set[str] = set()
    positive: set[str] = set()
    event_to_unit: dict[str, str] = {}
    for decision in decisions:
        if type(decision) is not dict:
            _fail("BATCH001_SNAPSHOT_DECISION_INVALID")
        lane = decision.get("completed_lane")
        unit_id = decision.get("review_unit_id")
        human = decision.get("human_decision")
        if type(unit_id) is not str or type(human) is not dict:
            _fail("BATCH001_SNAPSHOT_DECISION_IDENTITY_INVALID")
        events = human.get("events")
        if type(events) is not list:
            _fail("BATCH001_SNAPSHOT_EVENTS_INVALID")
        target = negative if lane == "COMPLETED_TASK_DOMAIN_NEGATIVE" else positive
        if lane not in {
            "COMPLETED_TASK_DOMAIN_NEGATIVE",
            "COMPLETED_POSITIVE_CHEMISTRY",
        }:
            _fail("BATCH001_SNAPSHOT_LANE_INVALID")
        for event in events:
            if type(event) is not dict:
                _fail("BATCH001_SNAPSHOT_EVENT_INVALID")
            event_id = event.get("canonical_event_id")
            if type(event_id) is not str or event_id in event_to_unit:
                _fail("BATCH001_SNAPSHOT_EVENT_DUPLICATE_OR_INVALID")
            event_to_unit[event_id] = unit_id
            target.add(event_id)
    if (len(negative), len(positive), len(event_to_unit)) != (24, 13, 37):
        _fail("BATCH001_SNAPSHOT_EVENT_COUNTS_INVALID")
    return negative, positive, event_to_unit


def _current_review_state(
    repo_root: Path,
    event_to_queue_unit: Mapping[str, str],
) -> tuple[
    current_reconciliation.predecessor.ReconciliationResult,
    dict[str, dict[str, str]],
]:
    result = current_reconciliation.reconcile_real_completed_human_decisions_with_g3h_v1(
        repo_root
    )
    if result.review_summary != {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 32,
        "completed_positive_unit_count": 3,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 56,
        "completed_total_unit_count": 7,
        "in_progress_event_count": 9,
        "in_progress_unit_count": 1,
        "unreviewed_event_count": 273,
        "unreviewed_unit_count": 123,
    }:
        _fail("CURRENT_RECONCILIATION_SUMMARY_INVALID")
    by_event: dict[str, dict[str, str]] = {}
    for raw in result.reconciled_rows:
        row = dict(raw)
        event_id = row["canonical_event_id"]
        if event_id in by_event or event_to_queue_unit.get(event_id) != row["raw_review_unit_id"]:
            _fail("CURRENT_RECONCILIATION_QUEUE_IDENTITY_INVALID")
        by_event[event_id] = row
    if set(by_event) != set(event_to_queue_unit):
        _fail("CURRENT_RECONCILIATION_QUEUE_COVERAGE_INVALID")
    if len(result.normalized_facts) != 32:
        _fail("CURRENT_RECONCILIATION_NORMALIZED_FACT_COUNT_INVALID")
    return result, by_event


def _runtime_state(
    index_payload: bytes,
    inventory_payload: bytes,
    universe_by_event: Mapping[str, Mapping[str, str]],
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    index_header, index_rows = _parse_csv(index_payload, "CURRENT_RUNTIME_INDEX")
    inventory_header, inventory_rows = _parse_csv(
        inventory_payload, "CURRENT_RUNTIME_BINDING_INVENTORY"
    )
    _require_columns(
        index_header,
        {
            "canonical_event_id",
            "positive_authority_status",
            "role_authority_status",
            "reactive_pair_authority_status",
            "POST_authority_status",
            "PRE_authority_status",
            "current_runtime_model_usable",
            "formal_split_authoritative",
            "formal_split",
            "training_admission_readiness",
        },
        "CURRENT_RUNTIME_INDEX",
    )
    _require_columns(
        inventory_header,
        {
            "canonical_event_id",
            "role_profile",
            "valid_task_ids_json",
            "POST_geometry_authoritative",
            "PRE_geometry_authoritative",
        },
        "CURRENT_RUNTIME_BINDING_INVENTORY",
    )
    inventory_by_event = {row["canonical_event_id"]: row for row in inventory_rows}
    if len(inventory_by_event) != len(inventory_rows) or len(inventory_rows) != 7:
        _fail("CURRENT_RUNTIME_BINDING_INVENTORY_COUNT_INVALID")
    in_universe = [row for row in index_rows if row["canonical_event_id"] in universe_by_event]
    if len(in_universe) != 18 or len({row["canonical_event_id"] for row in in_universe}) != 18:
        _fail("CURRENT_RUNTIME_UNIVERSE_INTERSECTION_INVALID")
    runtime: dict[str, dict[str, Any]] = {}
    incomplete: set[str] = set()
    for row in in_universe:
        event_id = row["canonical_event_id"]
        usable = _parse_bool(row["current_runtime_model_usable"], "runtime_usable")
        if not usable:
            if (
                row["training_admission_readiness"] != "RUNTIME_BINDING_INCOMPLETE"
                or row["formal_split_authoritative"] != "false"
                or row["formal_split"] != ""
            ):
                _fail("RUNTIME_INCOMPLETE_ROW_INVALID:" + event_id)
            incomplete.add(event_id)
            continue
        if (
            row["positive_authority_status"] != "FULL_POSITIVE_SUPERVISION_AUTHORITY"
            or row["role_authority_status"] != "authoritative"
            or row["reactive_pair_authority_status"] != "authoritative"
            or row["POST_authority_status"] != "authoritative"
            or row["PRE_authority_status"] != "unavailable_not_loss_eligible"
            or row["formal_split_authoritative"] != "true"
            or row["formal_split"] not in {"train", "validation", "test"}
        ):
            _fail("CURRENT_RUNTIME_ROW_SEMANTICS_INVALID:" + event_id)
        frozen = universe_by_event[event_id]
        profile = frozen["role_profile"]
        if not profile:
            binding = inventory_by_event.get(event_id)
            if binding is None:
                _fail("CURRENT_RUNTIME_ROLE_PROFILE_SOURCE_MISSING:" + event_id)
            profile = binding["role_profile"]
            if (
                binding["POST_geometry_authoritative"] != "true"
                or binding["PRE_geometry_authoritative"] != "false"
            ):
                _fail("CURRENT_RUNTIME_BINDING_GEOMETRY_INVALID:" + event_id)
        if profile not in {STRICT_PROFILE, DIRECT_PROFILE}:
            _fail("CURRENT_RUNTIME_ROLE_PROFILE_INVALID:" + event_id)
        admitted = row["training_admission_readiness"] == "FORMAL_TRAIN_ADMITTED"
        if admitted != (row["formal_split"] == "train"):
            _fail("CURRENT_RUNTIME_TRAINING_ADMISSION_INVALID:" + event_id)
        runtime[event_id] = {
            "source_kind": "CURRENT_RUNTIME",
            "source": _RUNTIME_INDEX,
            "role_profile": profile,
            "training_use": reconciliation.TRAINING_INCLUDE,
            "human_training_excluded": False,
            "pair_target": True,
            "post_sample": True,
            "post_training": True,
            "future_candidate": False,
            "formal_split_authoritative": True,
            "formal_split": row["formal_split"],
            "training_admitted": admitted,
            "runtime_usable": True,
            "materialization_allowed": None,
        }
    if len(runtime) != 17 or len(incomplete) != 1:
        _fail("CURRENT_RUNTIME_COUNTS_INVALID")
    if Counter(record["role_profile"] for record in runtime.values()) != Counter(
        {STRICT_PROFILE: 15, DIRECT_PROFILE: 2}
    ):
        _fail("CURRENT_RUNTIME_ROLE_PROFILE_COUNTS_INVALID")
    if sum(record["training_admitted"] for record in runtime.values()) != 5:
        _fail("CURRENT_RUNTIME_TRAINING_ADMITTED_COUNT_INVALID")
    return runtime, incomplete


def _add_positive_record(
    records: dict[str, dict[str, Any]],
    event_id: str,
    record: dict[str, Any],
) -> None:
    if event_id in records:
        if records[event_id] != record:
            _fail("INCOMPATIBLE_AUTHORITY_STATE_COLLISION:" + event_id)
        _fail("AUTHORITY_PROVENANCE_MERGE_SCHEMA_NOT_AVAILABLE:" + event_id)
    records[event_id] = record


def _ffq_state(payload: bytes) -> dict[str, dict[str, Any]]:
    header, rows = _parse_csv(payload, "FFQ_EVENT_PROJECTION")
    _require_columns(
        header,
        {
            "canonical_event_id",
            "chemistry_known_positive",
            "negative_chemistry",
            "task_domain_negative",
            "reactive_pair_human_decision_available",
            "role_profile_human_decision_available",
            "role_profile",
            "formal_event_training_use_decision",
            "training_use_allowed",
            "independent_POST_geometry_human_decision_available",
            "POST_geometry_training_label_available_now",
            "global_canonical_task_count",
            "direct_profile_applicable_task_ids_json",
            "training_admitted",
            "candidate_for_future_training_admission",
            "training_materialization_allowed_now",
            "current_runtime_model_usable",
            "authority_ingested",
            "authority_created_by_this_successor",
        },
        "FFQ_EVENT_PROJECTION",
    )
    if len(rows) != 8 or len({row["canonical_event_id"] for row in rows}) != 8:
        _fail("FFQ_EXACT8_EVENT_INVENTORY_INVALID")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        event_id = row["canonical_event_id"]
        include = row["formal_event_training_use_decision"] == reconciliation.TRAINING_INCLUDE
        exclude = row["formal_event_training_use_decision"] == reconciliation.TRAINING_EXCLUDE
        if (
            not (include or exclude)
            or row["chemistry_known_positive"] != "true"
            or row["negative_chemistry"] != "false"
            or row["task_domain_negative"] != "false"
            or row["reactive_pair_human_decision_available"] != "true"
            or row["role_profile_human_decision_available"] != "true"
            or row["role_profile"] != DIRECT_PROFILE
            or row["global_canonical_task_count"] != "5"
            or json.loads(row["direct_profile_applicable_task_ids_json"])
            != list(DIRECT_TASK_IDS)
            or row["training_use_allowed"] != _bool_cell(include)
            or row["training_admitted"] != "false"
            or row["candidate_for_future_training_admission"] != _bool_cell(include)
            or row["training_materialization_allowed_now"] != "false"
            or row["current_runtime_model_usable"] != "false"
            or row["POST_geometry_training_label_available_now"] != "false"
            or row["authority_ingested"] != "true"
            or row["authority_created_by_this_successor"] != "false"
        ):
            _fail("FFQ_EVENT_SEMANTICS_INVALID:" + event_id)
        independent_post = row["independent_POST_geometry_human_decision_available"] == "true"
        if independent_post != exclude:
            _fail("FFQ_POST_SAMPLE_AUTHORITY_ROUTING_INVALID:" + event_id)
        result[event_id] = {
            "source_kind": "FFQ",
            "source": _FFQ_EVENT,
            "role_profile": DIRECT_PROFILE,
            "training_use": row["formal_event_training_use_decision"],
            "human_training_excluded": exclude,
            # The fixed FFQ role-mask and supervised-forward owners are bound
            # above.  This is target constructibility, not training admission.
            "pair_target": True,
            "post_sample": independent_post,
            "post_training": False,
            "future_candidate": include,
            "formal_split_authoritative": False,
            "formal_split": "",
            "training_admitted": False,
            "runtime_usable": False,
            "materialization_allowed": False,
        }
    if Counter(record["training_use"] for record in result.values()) != Counter(
        {reconciliation.TRAINING_INCLUDE: 4, reconciliation.TRAINING_EXCLUDE: 4}
    ):
        _fail("FFQ_TRAINING_DISPOSITION_COUNTS_INVALID")
    return result


def _g3h_state(payload: bytes) -> dict[str, dict[str, Any]]:
    header, rows = _parse_csv(payload, "G3H_EVENT_PROJECTION")
    _require_columns(
        header,
        {
            "canonical_event_id",
            "chemistry_known_positive",
            "negative_chemistry",
            "task_domain_negative",
            "reactive_pair_human_decision_available",
            "role_profile_human_decision_available",
            "role_profile",
            "formal_event_training_use_decision",
            "training_use_allowed",
            "human_training_excluded",
            "independent_POST_geometry_human_decision_available",
            "POST_geometry_training_label_available_now",
            "global_canonical_task_count",
            "direct_profile_applicable_task_ids_json",
            "training_admitted",
            "candidate_for_future_training_admission",
            "training_materialization_allowed_now",
            "current_runtime_model_usable",
            "authority_ingested",
            "authority_created_by_this_successor",
        },
        "G3H_EVENT_PROJECTION",
    )
    if len(rows) != 8 or len({row["canonical_event_id"] for row in rows}) != 8:
        _fail("G3H_EXACT8_EVENT_INVENTORY_INVALID")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        event_id = row["canonical_event_id"]
        if (
            row["formal_event_training_use_decision"] != reconciliation.TRAINING_EXCLUDE
            or row["chemistry_known_positive"] != "true"
            or row["negative_chemistry"] != "false"
            or row["task_domain_negative"] != "false"
            or row["reactive_pair_human_decision_available"] != "true"
            or row["role_profile_human_decision_available"] != "true"
            or row["role_profile"] != DIRECT_PROFILE
            or row["global_canonical_task_count"] != "5"
            or json.loads(row["direct_profile_applicable_task_ids_json"])
            != list(DIRECT_TASK_IDS)
            or row["training_use_allowed"] != "false"
            or row["human_training_excluded"] != "true"
            or row["independent_POST_geometry_human_decision_available"] != "false"
            or row["POST_geometry_training_label_available_now"] != "false"
            or row["training_admitted"] != "false"
            or row["candidate_for_future_training_admission"] != "false"
            or row["training_materialization_allowed_now"] != "false"
            or row["current_runtime_model_usable"] != "false"
            or row["authority_ingested"] != "true"
            or row["authority_created_by_this_successor"] != "false"
        ):
            _fail("G3H_EVENT_SEMANTICS_INVALID:" + event_id)
        result[event_id] = {
            "source_kind": "G3H",
            "source": _G3H_EVENT,
            "role_profile": DIRECT_PROFILE,
            "training_use": reconciliation.TRAINING_EXCLUDE,
            "human_training_excluded": True,
            # No published G3H model-bound pair projection exists in V1.
            "pair_target": False,
            "post_sample": False,
            "post_training": False,
            "future_candidate": False,
            "formal_split_authoritative": True,
            "formal_split": "train",
            "training_admitted": False,
            "runtime_usable": False,
            "materialization_allowed": False,
        }
    return result


def _poa_state(
    formal_payload: bytes,
    repo_root: Path,
) -> tuple[dict[str, dict[str, Any]], poa_split_owner.POAFullComponentFormalSplitAuthorityResultV1]:
    effective = poa_owner.build_covapie_poa_sample_level_effective_supervision_v1(
        formal_payload
    )
    poa_owner.validate_covapie_poa_sample_level_effective_supervision_v1(effective)
    split = poa_split_owner.build_covapie_poa_full_component_formal_split_authority_v1(
        repo_root=repo_root
    )
    poa_split_owner.validate_covapie_poa_full_component_formal_split_authority_v1(split)
    split_by_event = {record.canonical_event_id: record for record in split.records}
    if len(effective.records) != 16 or len(split_by_event) != 24:
        _fail("POA_PROJECTION_INVENTORY_INVALID")
    result: dict[str, dict[str, Any]] = {}
    for record in effective.records:
        event_id = record.canonical_event_id
        split_record = split_by_event.get(event_id)
        include = record.training_use_disposition == reconciliation.TRAINING_INCLUDE
        if (
            split_record is None
            or record.chemistry_disposition != reconciliation.CHEMISTRY_POSITIVE
            or record.task_relevance_disposition != reconciliation.TASK_RELEVANT
            or record.reactive_pair_authority_available is not True
            or record.role_partition_authority_available is not True
            or record.runtime_role_profile != STRICT_PROFILE
            or record.valid_task_ids != STRICT_TASK_IDS
            or record.task_structural_mask_labels_available is not True
            or record.POST_geometry_training_authority_available is not False
            or record.PRE_geometry_training_authority_available is not False
            or record.nongeometry_future_candidate is not include
            or record.split_authoritative is not False
            or record.training_admitted is not False
            or split_record.formal_split_authoritative is not True
            or split_record.formal_split != "train"
            or split_record.sample_training_admitted is not False
        ):
            _fail("POA_EVENT_SEMANTICS_INVALID:" + event_id)
        result[event_id] = {
            "source_kind": "POA",
            "source": "src/covalent_ext/covapie_poa_sample_level_effective_supervision_v1.py",
            "role_profile": STRICT_PROFILE,
            "training_use": record.training_use_disposition,
            "human_training_excluded": record.human_training_excluded,
            # The bound inactive POA preview proves constructibility only; it
            # does not create training authority or activate materialization.
            "pair_target": True,
            "post_sample": False,
            "post_training": False,
            "future_candidate": record.nongeometry_future_candidate,
            "formal_split_authoritative": True,
            "formal_split": "train",
            "training_admitted": False,
            "runtime_usable": False,
            "materialization_allowed": None,
        }
    if Counter(record["training_use"] for record in result.values()) != Counter(
        {reconciliation.TRAINING_INCLUDE: 8, reconciliation.TRAINING_EXCLUDE: 8}
    ):
        _fail("POA_TRAINING_DISPOSITION_COUNTS_INVALID")
    return result, split


def _merge_semantic_bindings(
    direct: Sequence[Mapping[str, object]],
    split: poa_split_owner.POAFullComponentFormalSplitAuthorityResultV1,
) -> tuple[dict[str, object], ...]:
    by_identity: dict[tuple[str, str], dict[str, object]] = {}
    for raw in direct:
        row = dict(raw)
        key = (str(row["path_namespace"]), str(row["path"]))
        by_identity[key] = row
    for binding in split.source_bindings:
        row = {
            "artifact_role": binding.artifact_role,
            "path": binding.repository_relative_path,
            "path_namespace": "repository_relative",
            "byte_count": binding.byte_count,
            "sha256": binding.sha256,
        }
        key = ("repository_relative", binding.repository_relative_path)
        prior = by_identity.get(key)
        if prior is not None:
            if (
                prior["byte_count"] != binding.byte_count
                or prior["sha256"] != binding.sha256
            ):
                _fail("SEMANTIC_SOURCE_BINDING_CONFLICT:" + binding.repository_relative_path)
            continue
        by_identity[key] = row
    return tuple(
        sorted(by_identity.values(), key=lambda row: (str(row["path_namespace"]), str(row["path"])))
    )


def _top_pending_review_units(
    queue_rows: Sequence[Mapping[str, str]],
    current_by_event: Mapping[str, Mapping[str, str]],
) -> list[dict[str, object]]:
    status_by_unit: dict[str, set[str]] = {}
    for row in current_by_event.values():
        status_by_unit.setdefault(row["raw_review_unit_id"], set()).add(
            row["current_review_status"]
        )
    candidates: list[tuple[int, int, str, Mapping[str, str], str]] = []
    for row in queue_rows:
        unit = row["review_unit_id"]
        statuses = status_by_unit.get(unit)
        if statuses is None or len(statuses) != 1:
            _fail("TOP_PENDING_UNIT_STATUS_INVALID:" + unit)
        status = next(iter(statuses))
        if status not in {
            reconciliation.CURRENTLY_UNREVIEWED,
            reconciliation.CURRENTLY_IN_PROGRESS,
        }:
            continue
        candidates.append(
            (
                -int(row["event_count"]),
                int(row["priority_rank"]),
                unit,
                row,
                status,
            )
        )
    if len(candidates) != 124:
        _fail("CURRENT_PENDING_REVIEW_UNIT_COUNT_INVALID")
    candidates.sort(key=lambda item: item[:3])
    result: list[dict[str, object]] = []
    for rank, (_neg_count, _priority, unit, row, status) in enumerate(
        candidates[:10], 1
    ):
        result.append(
            {
                "rank": rank,
                "review_unit_id": unit,
                "event_count": int(row["event_count"]),
                "pdb_ids": json.loads(row["pdb_ids_json"]),
                "ligand_component_ids": json.loads(
                    row["ligand_component_ids_json"]
                ),
                "full_coordinate_count": int(row["full_coordinate_event_count"]),
                "exact_pair_count": int(row["exact_reactive_pair_event_count"]),
                "ccd_complete_count": int(row["CCD_graph_complete_event_count"]),
                "post_source_evidence_count": int(
                    row["POST_geometry_available_event_count"]
                ),
                "current_review_status": status,
            }
        )
    expected_units = (
        "COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74",
        "COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58",
        "COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22",
        "COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81",
        "COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D",
        "COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62",
        "COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410",
        "COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450",
        "COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5",
        "COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6",
    )
    if tuple(row["review_unit_id"] for row in result) != expected_units:
        _fail("TOP_PENDING_REVIEW_RANKING_DRIFT")
    return result


def _primary_human_source(row: Mapping[str, str]) -> str:
    try:
        sources = json.loads(row["current_status_authority_sources_json"])
    except json.JSONDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusError(
            f"{ERROR_TOKEN}:CURRENT_HUMAN_SOURCE_JSON_INVALID"
        ) from error
    if type(sources) is not list or not sources or any(
        type(source) is not str or not source for source in sources
    ):
        _fail("CURRENT_HUMAN_SOURCE_INVENTORY_INVALID")
    return sources[0]


def _presentation_buckets(
    universe: Sequence[Mapping[str, str]],
    current_by_event: Mapping[str, Mapping[str, str]],
    legacy_negative: set[str],
    partial: set[str],
    runtime: set[str],
    auto_negative: set[str],
) -> dict[str, set[str]]:
    buckets: dict[str, set[str]] = {
        status: set() for status in GLOBAL_STATUSES_V1
    }
    for event_id, row in current_by_event.items():
        status = row["current_review_status"]
        if status not in {
            reconciliation.CURRENTLY_UNREVIEWED,
            reconciliation.CURRENTLY_IN_PROGRESS,
            reconciliation.COMPLETED_HUMAN_POSITIVE,
            reconciliation.COMPLETED_HUMAN_NEGATIVE,
        }:
            _fail("CURRENT_REVIEW_PRESENTATION_STATUS_INVALID:" + event_id)
        buckets[status].add(event_id)
    buckets[reconciliation.COMPLETED_HUMAN_NEGATIVE].update(legacy_negative)
    buckets[reconciliation.COMPLETED_PARTIAL_AUTHORITY].update(partial)
    buckets[reconciliation.CURRENT_RUNTIME_MODEL_USABLE].update(runtime)
    buckets[reconciliation.PUBLISHED_EXACT_AUTO_NEGATIVE].update(auto_negative)
    route_to_status = {
        "LEAKAGE_EXISTING_GROUP_CONFLICT": "LEAKAGE_EXISTING_GROUP_CONFLICT",
        "STRUCTURAL_EVIDENCE_INCOMPLETE": "STRUCTURAL_EVIDENCE_INCOMPLETE",
        "QUARANTINE_REPRESENTATION_GAP": "QUARANTINE_REPRESENTATION_GAP",
        "REJECTED_FEATURE_INCOMPATIBLE": "REJECTED_FEATURE_INCOMPATIBLE",
    }
    assigned = set().union(*buckets.values())
    for frozen in universe:
        event_id = frozen["canonical_event_id"]
        if event_id in assigned:
            continue
        route = frozen["terminal_route"]
        status = route_to_status.get(route)
        if status is None:
            _fail("PRESENTATION_SOURCE_ROUTE_UNACCOUNTED:" + event_id)
        buckets[status].add(event_id)
    membership: Counter[str] = Counter(
        event_id for values in buckets.values() for event_id in values
    )
    universe_ids = {row["canonical_event_id"] for row in universe}
    if set(membership) != universe_ids or any(value != 1 for value in membership.values()):
        _fail("PRESENTATION_STATUS_NOT_EXACTLY_ONE_PER_EVENT")
    if {status: len(values) for status, values in buckets.items()} != (
        EXPECTED_GLOBAL_STATUS_COUNTS_V1
    ):
        _fail("GLOBAL_STATUS_DISTRIBUTION_INVALID")
    return buckets


def _assert_disjoint_named_sets(named: Mapping[str, set[str]]) -> None:
    owners: dict[str, str] = {}
    for name, event_ids in named.items():
        for event_id in event_ids:
            prior = owners.get(event_id)
            if prior is not None:
                _fail(f"INCOMPATIBLE_AUTHORITY_STATE_COLLISION:{event_id}:{prior}:{name}")
            owners[event_id] = name


def _build_summary(
    rows: Sequence[Mapping[str, str]],
    top_pending: list[dict[str, object]],
) -> dict[str, Any]:
    event_sets = {
        "chemistry_positive": {
            row["canonical_event_id"]
            for row in rows
            if row["chemistry_disposition"] == CHEMISTRY_POSITIVE
        },
        "chemistry_not_established": {
            row["canonical_event_id"]
            for row in rows
            if row["chemistry_disposition"] == CHEMISTRY_NOT_ESTABLISHED
        },
        "chemistry_unresolved": {
            row["canonical_event_id"]
            for row in rows
            if row["chemistry_disposition"] == CHEMISTRY_UNRESOLVED
        },
        "task_relevant": {
            row["canonical_event_id"]
            for row in rows
            if row["task_relevance_disposition"] == TASK_RELEVANT
        },
        "task_not_relevant": {
            row["canonical_event_id"]
            for row in rows
            if row["task_relevance_disposition"] == TASK_NOT_RELEVANT
        },
        "task_unresolved": {
            row["canonical_event_id"]
            for row in rows
            if row["task_relevance_disposition"] == TASK_UNRESOLVED
        },
        "training_include": {
            row["canonical_event_id"]
            for row in rows
            if row["training_use_disposition"] == reconciliation.TRAINING_INCLUDE
        },
        "training_exclude": {
            row["canonical_event_id"]
            for row in rows
            if row["training_use_disposition"] == reconciliation.TRAINING_EXCLUDE
        },
        "training_not_applicable": {
            row["canonical_event_id"]
            for row in rows
            if row["training_use_disposition"] == reconciliation.TRAINING_NOT_APPLICABLE
        },
        "training_unresolved": {
            row["canonical_event_id"]
            for row in rows
            if row["training_use_disposition"] == TRAINING_UNRESOLVED
        },
    }
    positive_rows = [
        row for row in rows if row["chemistry_disposition"] == CHEMISTRY_POSITIVE
    ]
    include_rows = [
        row
        for row in rows
        if row["training_use_disposition"] == reconciliation.TRAINING_INCLUDE
    ]

    def count_true(field: str, population: Sequence[Mapping[str, str]] = rows) -> int:
        return sum(row[field] == "true" for row in population)

    global_counts = Counter(row["current_global_status"] for row in rows)
    profile_counts = Counter(
        row["role_profile"]
        for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    )
    applicability_counts = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] != "true":
            continue
        task_ids = json.loads(row["structurally_applicable_task_ids_json"])
        applicability_counts.update(task_ids)
    priority_rows = [row for row in rows if row["priority_review_in_scope"] == "true"]
    review_counts = Counter(row["current_review_status"] for row in priority_rows)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "universe": {
            "event_count": 1000,
            "unique_canonical_event_id_count": 1000,
            "duplicate_canonical_event_id_count": 0,
            "missing_rank_count": 0,
            "rank_start": 1,
            "rank_end": 1000,
            "unique_pdb_count": len({row["pdb_id"] for row in rows}),
            "unique_ligand_component_count": len(
                {row["ligand_component_id"] for row in rows}
            ),
            "canonical_event_set_sha256": _event_set_sha256(
                {row["canonical_event_id"] for row in rows}
            ),
        },
        "structural": {
            "raw_structure_available_count": count_true("raw_structure_available"),
            "exact_cys_sg_event_recovered_count": count_true(
                "exact_cys_sg_event_recovered"
            ),
            "explicit_covalent_evidence_count": count_true(
                "explicit_covalent_evidence"
            ),
            "distance_only_event_inference_used_count": count_true(
                "distance_only_event_inference_used"
            ),
            "full_coordinate_post_evidence_available_count": count_true(
                "full_coordinate_post_evidence_available"
            ),
            "ccd_graph_complete_count": count_true("ccd_graph_complete"),
            "feature_compatible_count": count_true("feature_compatible"),
            "structural_processing_success_count": count_true(
                "structural_processing_success"
            ),
            "post_geometry_source_evidence_available_count": count_true(
                "post_geometry_source_evidence_available"
            ),
            "representation_gap_count": count_true("representation_gap"),
            "feature_incompatible_count": count_true("feature_incompatible"),
        },
        "global_status_distribution": {
            "status_priority": list(GLOBAL_STATUSES_V1),
            "counts": {status: global_counts[status] for status in GLOBAL_STATUSES_V1},
            "total_count": sum(global_counts.values()),
            "exactly_one_status_per_event": True,
            "presentation_only_not_authority": True,
        },
        "human_review": {
            "priority_review_population_event_count": len(priority_rows),
            "review_unit_count": len(
                {row["review_unit_id"] for row in priority_rows}
            ),
            "completed_event_count": review_counts[
                reconciliation.COMPLETED_HUMAN_POSITIVE
            ]
            + review_counts[reconciliation.COMPLETED_HUMAN_NEGATIVE],
            "completed_positive_event_count": review_counts[
                reconciliation.COMPLETED_HUMAN_POSITIVE
            ],
            "completed_negative_event_count": review_counts[
                reconciliation.COMPLETED_HUMAN_NEGATIVE
            ],
            "unreviewed_event_count": review_counts[reconciliation.CURRENTLY_UNREVIEWED],
            "in_progress_event_count": review_counts[
                reconciliation.CURRENTLY_IN_PROGRESS
            ],
            "pending_event_count": review_counts[reconciliation.CURRENTLY_UNREVIEWED]
            + review_counts[reconciliation.CURRENTLY_IN_PROGRESS],
            "current_pending_review_unit_count": 124,
        },
        "chemistry": {
            "POSITIVE": {
                "count": len(event_sets["chemistry_positive"]),
                "event_set_sha256": _event_set_sha256(
                    event_sets["chemistry_positive"]
                ),
            },
            "NEGATIVE": {"count": 0, "event_set_sha256": _event_set_sha256(set())},
            "NOT_ESTABLISHED": {
                "count": len(event_sets["chemistry_not_established"]),
                "event_set_sha256": _event_set_sha256(
                    event_sets["chemistry_not_established"]
                ),
            },
            "UNRESOLVED": {
                "count": len(event_sets["chemistry_unresolved"]),
                "event_set_sha256": _event_set_sha256(
                    event_sets["chemistry_unresolved"]
                ),
            },
            "positive_source_composition": {
                "CURRENT_RUNTIME": sum(
                    row["positive_authority_source"] == _RUNTIME_INDEX for row in rows
                ),
                "FFQ": sum(row["positive_authority_source"] == _FFQ_EVENT for row in rows),
                "POA": sum(
                    row["positive_authority_source"]
                    == "src/covalent_ext/covapie_poa_sample_level_effective_supervision_v1.py"
                    for row in rows
                ),
                "G3H": sum(row["positive_authority_source"] == _G3H_EVENT for row in rows),
            },
            "positive_authority_collision_count": 0,
        },
        "task_relevance": {
            "RELEVANT": {
                "count": len(event_sets["task_relevant"]),
                "event_set_sha256": _event_set_sha256(event_sets["task_relevant"]),
            },
            "NOT_RELEVANT": {
                "count": len(event_sets["task_not_relevant"]),
                "event_set_sha256": _event_set_sha256(
                    event_sets["task_not_relevant"]
                ),
            },
            "UNRESOLVED": {
                "count": len(event_sets["task_unresolved"]),
                "event_set_sha256": _event_set_sha256(event_sets["task_unresolved"]),
            },
        },
        "reactive_pair": {
            "raw_structural_pair_evidence_count": count_true(
                "reactive_pair_raw_structural_evidence"
            ),
            "sample_level_authoritative_pair_count": count_true(
                "reactive_pair_sample_authoritative"
            ),
            "published_model_bound_target_constructible_count": count_true(
                "reactive_pair_training_target_available"
            ),
            "current_runtime_bound_target_count": count_true(
                "current_runtime_model_usable"
            ),
            "g3h_sample_authority_contribution_count": sum(
                row["positive_authority_source"] == _G3H_EVENT for row in rows
            ),
            "g3h_training_target_contribution_count": sum(
                row["positive_authority_source"] == _G3H_EVENT
                and row["reactive_pair_training_target_available"] == "true"
                for row in rows
            ),
        },
        "role": {
            "role_partition_sample_authoritative_count": count_true(
                "role_partition_sample_authoritative"
            ),
            "role_profile_counts": {
                STRICT_PROFILE: profile_counts[STRICT_PROFILE],
                DIRECT_PROFILE: profile_counts[DIRECT_PROFILE],
                "other": sum(
                    count
                    for profile, count in profile_counts.items()
                    if profile not in {STRICT_PROFILE, DIRECT_PROFILE}
                ),
            },
            "canonical_mask_structural_labels_available_count": count_true(
                "canonical_mask_structural_labels_available"
            ),
            "all_five_structurally_applicable_count": sum(
                row["structurally_applicable_task_ids_json"] == "[0,1,2,3,4]"
                for row in rows
            ),
            "direct_profile_A_B3_C_count": sum(
                row["structurally_applicable_task_ids_json"] == "[0,3,4]"
                for row in rows
            ),
            "unknown_role_rows_are_not_false_applicability": all(
                row["structurally_applicable_task_ids_json"] == "null"
                for row in rows
                if row["role_partition_sample_authoritative"] == "false"
            ),
        },
        "canonical_exact5": {
            "task_count": 5,
            "tasks": [
                {
                    "task_id": task_id,
                    "semantic_name": semantic_name,
                    "display_alias": alias,
                    "structurally_applicable_authoritative_role_count": (
                        applicability_counts[task_id]
                    ),
                }
                for task_id, semantic_name, alias in CANONICAL_EXACT5_V1
            ],
            "B3_present": True,
            "sixth_task_present": False,
        },
        "geometry": {
            "POST_source_evidence_available_count": count_true(
                "post_geometry_source_evidence_available"
            ),
            "POST_sample_authoritative_count": count_true(
                "post_geometry_sample_authoritative"
            ),
            "POST_training_target_available_count": count_true(
                "post_geometry_training_target_available"
            ),
            "PRE_source_evidence_available_count": 0,
            "PRE_sample_authoritative_count": count_true(
                "pre_geometry_authoritative"
            ),
            "PRE_training_target_available_count": count_true(
                "pre_geometry_training_target_available"
            ),
            "PRE_is_v1_hard_requirement": False,
            "POST_to_PRE_promotion_performed": False,
            "PRE_zero_fill_performed": False,
        },
        "training_use": {
            "INCLUDE": {
                "count": len(event_sets["training_include"]),
                "event_set_sha256": _event_set_sha256(event_sets["training_include"]),
            },
            "EXCLUDE_FROM_TRAINING_ONLY": {
                "count": len(event_sets["training_exclude"]),
                "event_set_sha256": _event_set_sha256(event_sets["training_exclude"]),
            },
            "NOT_APPLICABLE": {
                "count": len(event_sets["training_not_applicable"]),
                "event_set_sha256": _event_set_sha256(
                    event_sets["training_not_applicable"]
                ),
            },
            "UNRESOLVED": {
                "count": len(event_sets["training_unresolved"]),
                "event_set_sha256": _event_set_sha256(event_sets["training_unresolved"]),
            },
            "total_count": sum(
                len(event_sets[name])
                for name in (
                    "training_include",
                    "training_exclude",
                    "training_not_applicable",
                    "training_unresolved",
                )
            ),
            "excluded_positive_is_not_chemistry_negative": True,
        },
        "training_stage": {
            "training_use_include_count": count_true("training_use_include"),
            "future_training_admission_candidate_count": count_true(
                "future_training_admission_candidate"
            ),
            "future_candidate_source_composition": {"FFQ": 4, "POA": 8, "G3H": 0},
            "current_runtime_model_usable_count": count_true(
                "current_runtime_model_usable"
            ),
            "formal_training_admitted_count": count_true("formal_training_admitted"),
            "ready_for_formal_training_event_count": 0,
            "training_materialization_allowed_global_status": (
                "NOT_COMPUTABLE_FROM_CURRENT_PUBLISHED_AUTHORITY"
            ),
            "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
            "feature_semantics_audit_completed": False,
            "step12d_status": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        },
        "blockers": {
            "non_exclusive_counts_must_not_be_summed": True,
            "chemistry_unresolved": {"all_1000": 865},
            "pair_authority_absent": {"all_1000": 951, "within_positive_49": 0},
            "role_authority_absent": {"all_1000": 951, "within_positive_49": 0},
            "human_training_exclusion": {"within_positive_49": 20},
            "missing_split_authority": {
                "within_positive_49": sum(
                    row["formal_split_authoritative"] == "false"
                    for row in positive_rows
                ),
                "within_include_29": sum(
                    row["formal_split_authoritative"] == "false"
                    for row in include_rows
                ),
            },
            "missing_tensor_integration": {
                "within_positive_49": sum(
                    row["reactive_pair_training_target_available"] == "false"
                    for row in positive_rows
                ),
                "within_include_29": sum(
                    row["reactive_pair_training_target_available"] == "false"
                    for row in include_rows
                ),
                "all_missing_are_g3h_excluded_population": all(
                    row["positive_authority_source"] == _G3H_EVENT
                    and row["training_use_disposition"] == reconciliation.TRAINING_EXCLUDE
                    for row in positive_rows
                    if row["reactive_pair_training_target_available"] == "false"
                ),
            },
            "missing_POST_training_authority": {
                "within_positive_49": sum(
                    row["post_geometry_training_target_available"] == "false"
                    for row in positive_rows
                ),
                "within_include_29": sum(
                    row["post_geometry_training_target_available"] == "false"
                    for row in include_rows
                ),
            },
            "missing_training_admission": {
                "within_positive_49": sum(
                    row["formal_training_admitted"] == "false"
                    for row in positive_rows
                ),
                "within_include_29": sum(
                    row["formal_training_admitted"] == "false"
                    for row in include_rows
                ),
            },
            "feature_semantics_pending": {"within_positive_49": 49},
        },
        "top_pending_review_units_by_event_yield": top_pending,
        "authority_boundary": {
            "CURRENT_GLOBAL_RECONCILIATION_COMPLETE": True,
            "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE": True,
            "READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION": True,
            "READY_FOR_FORMAL_TRAINING": False,
            "NEXT_RECOMMENDED_MAINLINE": "HIGH_YIELD_HUMAN_REVIEW_EXPANSION",
            "next_priority_review_unit": (
                "COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74"
            ),
            "HUMAN_REVIEW_DECISION_NOT_PERFORMED": True,
            "new_human_authority_created": False,
            "new_chemistry_authority_created": False,
            "new_reusable_authority_created": False,
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
            "training_performed": False,
            "fine_tune_performed": False,
            "training_admission_created": False,
            "training_dataset_changed": False,
            "feature_semantics_audit_performed": False,
            "tensor_status": "NOT_STARTED",
            "training_admission_status": "NOT_STARTED",
            "feature_semantics_status": "AUDIT_REQUIRED_LATER",
            "training_status": "NOT_STARTED",
        },
    }
    return summary


def compute_covapie_cumulative1000_current_global_readiness_census_v1(
    repo_root: Path,
) -> Cumulative1000CurrentGlobalReadinessComputationV1:
    """Read all frozen sources and construct the deterministic 1000-row view."""

    root = repo_root.resolve()
    if not root.is_dir():
        _fail("REPOSITORY_ROOT_INVALID")
    _validate_exact5_contract()
    payloads, direct_bindings = _load_direct_sources(root)
    universe = _parse_universe(payloads[_UNIVERSE])
    universe_by_event = {row["canonical_event_id"]: row for row in universe}
    structural_by_event = _parse_structural_sources(
        payloads[_STRUCTURAL_1_500],
        payloads[_STRUCTURAL_501_1000],
        universe,
    )
    queue_by_unit, event_to_queue_unit, queue_rows = _parse_queue(payloads[_QUEUE])
    reconciliation_result, current_by_event = _current_review_state(
        root, event_to_queue_unit
    )
    legacy_negative, legacy_positive, partial, legacy_event_to_unit = (
        _legacy_human_sets(payloads[_LEGACY_HUMAN])
    )
    batch_negative, batch_positive, batch_event_to_unit = _batch_snapshot_sets(
        payloads[_BATCH_SNAPSHOT]
    )
    runtime_records, runtime_incomplete = _runtime_state(
        payloads[_RUNTIME_INDEX], payloads[_RUNTIME_INVENTORY], universe_by_event
    )
    if runtime_incomplete != partial:
        _fail("PARTIAL_AUTHORITY_RUNTIME_INCOMPLETE_SET_MISMATCH")
    frozen_legacy_negative = {
        row["canonical_event_id"]
        for row in universe
        if row["terminal_route"] == "HUMAN_NOT_RELEVANT_FINAL"
    }
    frozen_runtime13 = {
        row["canonical_event_id"]
        for row in universe
        if row["terminal_route"] == "MODEL_USABLE_AUTHORITATIVE_POSITIVE"
    }
    frozen_other_relevant = {
        row["canonical_event_id"]
        for row in universe
        if row["terminal_route"] == "HUMAN_RELEVANT_FINAL"
    }
    if (
        legacy_negative != frozen_legacy_negative
        or batch_positive != frozen_runtime13
        or legacy_positive | partial != frozen_other_relevant
        or batch_negative
        != {
            event_id
            for event_id, row in current_by_event.items()
            if row["current_review_status"]
            == reconciliation.COMPLETED_HUMAN_NEGATIVE
        }
    ):
        _fail("LEGACY_CURRENT_HUMAN_AUTHORITY_SET_MISMATCH")
    if set(runtime_records) != batch_positive | legacy_positive:
        _fail("CURRENT_RUNTIME_HUMAN_POSITIVE_SET_MISMATCH")

    ffq_records = _ffq_state(payloads[_FFQ_EVENT])
    poa_records, poa_split = _poa_state(payloads[_POA_FORMAL], root)
    g3h_records = _g3h_state(payloads[_G3H_EVENT])
    if set(poa_split.exact16_event_ids) != set(poa_records) or set(
        poa_split.external_g3h_event_ids
    ) != set(g3h_records):
        _fail("POA_SPLIT_EVENT_PROJECTION_SET_MISMATCH")

    positive_records: dict[str, dict[str, Any]] = {}
    for source_records in (
        runtime_records,
        ffq_records,
        poa_records,
        g3h_records,
    ):
        for event_id, record in source_records.items():
            if event_id not in universe_by_event:
                _fail("POSITIVE_EVENT_OUTSIDE_UNIVERSE:" + event_id)
            _add_positive_record(positive_records, event_id, record)
    if len(positive_records) != 49:
        _fail("CHEMISTRY_POSITIVE_COUNT_DRIFT")
    normalized_by_event = {
        fact.canonical_event_id: fact
        for fact in reconciliation_result.normalized_facts
    }
    if set(normalized_by_event) != set(ffq_records) | set(poa_records) | set(
        g3h_records
    ):
        _fail("CURRENT_RECONCILIATION_POSITIVE_PROJECTION_SET_MISMATCH")
    for event_id, fact in normalized_by_event.items():
        record = positive_records[event_id]
        if (
            fact.chemistry_disposition != reconciliation.CHEMISTRY_POSITIVE
            or fact.task_relevance_disposition != reconciliation.TASK_RELEVANT
            or fact.training_disposition != record["training_use"]
            or fact.human_training_excluded != record["human_training_excluded"]
        ):
            _fail("CURRENT_RECONCILIATION_POSITIVE_SEMANTICS_MISMATCH:" + event_id)

    auto_negative = {
        row["canonical_event_id"]
        for row in universe
        if row["terminal_route"] == "AUTO_NEGATIVE_EXACT_FINAL"
    }
    current_negative = {
        event_id
        for event_id, row in current_by_event.items()
        if row["current_review_status"] == reconciliation.COMPLETED_HUMAN_NEGATIVE
    }
    task_not_relevant = legacy_negative | current_negative | auto_negative
    positive = set(positive_records)
    _assert_disjoint_named_sets(
        {
            "CHEMISTRY_POSITIVE": positive,
            "TASK_NOT_RELEVANT": task_not_relevant,
            "PARTIAL_TASK_RELEVANT": partial,
        }
    )
    if (len(task_not_relevant), len(auto_negative)) != (86, 32):
        _fail("TASK_NOT_RELEVANT_COMPOSITION_INVALID")
    universe_ids = set(universe_by_event)
    chemistry_unresolved = universe_ids - positive - task_not_relevant
    task_relevant = positive | partial
    task_unresolved = universe_ids - task_relevant - task_not_relevant
    if (len(chemistry_unresolved), len(task_relevant), len(task_unresolved)) != (
        865,
        50,
        864,
    ):
        _fail("CHEMISTRY_OR_TASK_RELEVANCE_COUNTS_INVALID")
    if (
        _event_set_sha256(positive)
        != EXPECTED_EVENT_SET_SHA256_V1["chemistry_positive"]
        or _event_set_sha256(task_not_relevant)
        != EXPECTED_EVENT_SET_SHA256_V1["chemistry_not_established"]
        or _event_set_sha256(chemistry_unresolved)
        != EXPECTED_EVENT_SET_SHA256_V1["chemistry_unresolved"]
        or _event_set_sha256(task_relevant)
        != EXPECTED_EVENT_SET_SHA256_V1["task_relevant"]
    ):
        _fail("CHEMISTRY_OR_TASK_RELEVANCE_EVENT_SET_SHA256_MISMATCH")

    include = {
        event_id
        for event_id, record in positive_records.items()
        if record["training_use"] == reconciliation.TRAINING_INCLUDE
    }
    exclude = {
        event_id
        for event_id, record in positive_records.items()
        if record["training_use"] == reconciliation.TRAINING_EXCLUDE
    }
    if (
        len(include) != 29
        or len(exclude) != 20
        or _event_set_sha256(include)
        != EXPECTED_EVENT_SET_SHA256_V1["training_include"]
        or _event_set_sha256(exclude)
        != EXPECTED_EVENT_SET_SHA256_V1["training_exclude"]
    ):
        _fail("TRAINING_USE_POSITIVE_DISPOSITION_INVALID")

    buckets = _presentation_buckets(
        universe,
        current_by_event,
        legacy_negative,
        partial,
        set(runtime_records),
        auto_negative,
    )
    status_by_event = {
        event_id: status for status, event_ids in buckets.items() for event_id in event_ids
    }
    top_pending = _top_pending_review_units(queue_rows, current_by_event)

    rows: list[dict[str, str]] = []
    for frozen in universe:
        event_id = frozen["canonical_event_id"]
        structural = structural_by_event[event_id]
        priority = event_id in current_by_event
        human_status = "NOT_IN_HUMAN_REVIEW_POPULATION"
        human_completed = False
        review_unit_id = ""
        human_source = ""
        if priority:
            current = current_by_event[event_id]
            human_status = current["current_review_status"]
            human_completed = human_status in {
                reconciliation.COMPLETED_HUMAN_POSITIVE,
                reconciliation.COMPLETED_HUMAN_NEGATIVE,
            }
            review_unit_id = current["raw_review_unit_id"]
            human_source = _primary_human_source(current)
        elif event_id in batch_positive:
            human_status = reconciliation.COMPLETED_HUMAN_POSITIVE
            human_completed = True
            review_unit_id = batch_event_to_unit[event_id]
            human_source = _BATCH_SNAPSHOT
        elif event_id in legacy_positive:
            human_status = reconciliation.COMPLETED_HUMAN_POSITIVE
            human_completed = True
            review_unit_id = legacy_event_to_unit[event_id]
            human_source = _LEGACY_HUMAN
        elif event_id in legacy_negative:
            human_status = reconciliation.COMPLETED_HUMAN_NEGATIVE
            human_completed = True
            review_unit_id = legacy_event_to_unit[event_id]
            human_source = _LEGACY_HUMAN
        elif event_id in partial:
            human_status = reconciliation.CURRENTLY_IN_PROGRESS
            review_unit_id = legacy_event_to_unit[event_id]
            human_source = _LEGACY_HUMAN

        positive_record = positive_records.get(event_id)
        if positive_record is not None:
            chemistry = CHEMISTRY_POSITIVE
            task = TASK_RELEVANT
            training_use = str(positive_record["training_use"])
            authority_source = str(positive_record["source"])
            chemistry_source = authority_source
            task_source = authority_source
        elif event_id in task_not_relevant:
            chemistry = CHEMISTRY_NOT_ESTABLISHED
            task = TASK_NOT_RELEVANT
            training_use = reconciliation.TRAINING_NOT_APPLICABLE
            if event_id in current_negative:
                task_source = _BATCH_SNAPSHOT
            elif event_id in legacy_negative:
                task_source = _LEGACY_HUMAN
            else:
                task_source = _UNIVERSE
            chemistry_source = task_source
            authority_source = ""
        else:
            chemistry = CHEMISTRY_UNRESOLVED
            task = TASK_RELEVANT if event_id in partial else TASK_UNRESOLVED
            training_use = TRAINING_UNRESOLVED
            task_source = _LEGACY_HUMAN if event_id in partial else ""
            chemistry_source = ""
            authority_source = ""

        if positive_record is None:
            profile = ROLE_NOT_ESTABLISHED
            task_ids_cell = "null"
            pair_authoritative = False
            pair_target = False
            role_authoritative = False
            mask_labels = False
            post_sample = False
            post_training = False
            future_candidate = False
            formal_split_authoritative = False
            formal_split = ""
            admitted = False
            runtime_usable = False
            human_excluded = False
            materialization_cell = ""
        else:
            profile = str(positive_record["role_profile"])
            task_ids = STRICT_TASK_IDS if profile == STRICT_PROFILE else DIRECT_TASK_IDS
            task_ids_cell = _canonical_json(list(task_ids))
            pair_authoritative = True
            pair_target = bool(positive_record["pair_target"])
            role_authoritative = True
            mask_labels = True
            post_sample = bool(positive_record["post_sample"])
            post_training = bool(positive_record["post_training"])
            future_candidate = bool(positive_record["future_candidate"])
            formal_split_authoritative = bool(
                positive_record["formal_split_authoritative"]
            )
            formal_split = str(positive_record["formal_split"])
            admitted = bool(positive_record["training_admitted"])
            runtime_usable = bool(positive_record["runtime_usable"])
            human_excluded = bool(positive_record["human_training_excluded"])
            materialization = positive_record["materialization_allowed"]
            materialization_cell = (
                "" if materialization is None else _bool_cell(bool(materialization))
            )

        values: dict[str, str] = {
            "scaleup_rank": frozen["scaleup_rank"],
            "canonical_event_id": event_id,
            "pdb_id": frozen["pdb_id"],
            "ligand_component_id": frozen["ligand_component_id"],
            **{key: structural[key] for key in CENSUS_COLUMNS_V1 if key in structural},
            "current_global_status": status_by_event[event_id],
            "priority_review_in_scope": _bool_cell(priority),
            "review_unit_id": review_unit_id,
            "current_review_status": human_status,
            "human_review_completed": _bool_cell(human_completed),
            "human_review_authority_source": human_source,
            "chemistry_disposition": chemistry,
            "chemistry_authority_source": chemistry_source,
            "task_relevance_disposition": task,
            "task_relevance_authority_source": task_source,
            "training_use_disposition": training_use,
            "human_training_excluded": _bool_cell(human_excluded),
            "reactive_pair_raw_structural_evidence": structural[
                "structural_processing_success"
            ],
            "reactive_pair_sample_authoritative": _bool_cell(pair_authoritative),
            "reactive_pair_training_target_available": _bool_cell(pair_target),
            "role_partition_sample_authoritative": _bool_cell(role_authoritative),
            "role_profile": profile,
            "canonical_mask_structural_labels_available": _bool_cell(mask_labels),
            "structurally_applicable_task_ids_json": task_ids_cell,
            "post_geometry_sample_authoritative": _bool_cell(post_sample),
            "post_geometry_training_target_available": _bool_cell(post_training),
            "pre_geometry_authoritative": "false",
            "pre_geometry_training_target_available": "false",
            "training_use_include": _bool_cell(
                training_use == reconciliation.TRAINING_INCLUDE
            ),
            "future_training_admission_candidate": _bool_cell(future_candidate),
            "formal_split_authoritative": _bool_cell(formal_split_authoritative),
            "formal_split": formal_split,
            "formal_training_admitted": _bool_cell(admitted),
            "current_runtime_model_usable": _bool_cell(runtime_usable),
            "training_materialization_allowed_current_source": materialization_cell,
            "positive_authority_source": authority_source,
            "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
        }
        row = {column: values[column] for column in CENSUS_COLUMNS_V1}
        rows.append(row)

    summary = _build_summary(rows, top_pending)
    bindings = _merge_semantic_bindings(direct_bindings, poa_split)
    computation = Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=tuple(rows),
        summary=summary,
        semantic_source_bindings=bindings,
    )
    validate_covapie_cumulative1000_current_global_readiness_census_v1(computation)
    return computation


def validate_covapie_cumulative1000_current_global_readiness_census_v1(
    computation: object,
) -> bool:
    """Fail closed unless rows, summary, provenance, and boundaries are exact."""

    if type(computation) is not Cumulative1000CurrentGlobalReadinessComputationV1:
        _fail("COMPUTATION_TYPE_INVALID")
    rows = computation.rows
    summary = computation.summary
    bindings = computation.semantic_source_bindings
    if (
        type(rows) is not tuple
        or len(rows) != 1000
        or any(type(row) is not dict or tuple(row) != CENSUS_COLUMNS_V1 for row in rows)
    ):
        _fail("CENSUS_EXACT1000_ROW_SCHEMA_INVALID")
    if type(summary) is not dict:
        _fail("SUMMARY_TYPE_INVALID")
    if type(bindings) is not tuple or not bindings:
        _fail("SEMANTIC_SOURCE_BINDINGS_INVALID")

    binding_paths: set[str] = set()
    binding_identities: set[tuple[str, str]] = set()
    for binding in bindings:
        if type(binding) is not dict or set(binding) != {
            "artifact_role",
            "path",
            "path_namespace",
            "byte_count",
            "sha256",
        }:
            _fail("SEMANTIC_SOURCE_BINDING_SCHEMA_INVALID")
        path = binding["path"]
        namespace = binding["path_namespace"]
        if (
            type(path) is not str
            or not path
            or type(namespace) is not str
            or namespace not in {"repository_relative", "repository_parent_relative"}
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
            or type(binding["artifact_role"]) is not str
            or not binding["artifact_role"]
            or type(binding["byte_count"]) is not int
            or binding["byte_count"] <= 0
            or type(binding["sha256"]) is not str
            or not _SHA_PATTERN.fullmatch(binding["sha256"])
        ):
            _fail("SEMANTIC_SOURCE_BINDING_VALUE_INVALID")
        identity = (namespace, path)
        if identity in binding_identities:
            _fail("SEMANTIC_SOURCE_BINDING_DUPLICATE")
        binding_identities.add(identity)
        binding_paths.add(path)
    for spec in _DIRECT_SOURCE_SPECS_V1:
        matches = [
            binding
            for binding in bindings
            if binding["path"] == spec.path
            and binding["path_namespace"] == spec.path_namespace
        ]
        if len(matches) != 1 or matches[0] != {
            "artifact_role": spec.artifact_role,
            "path": spec.path,
            "path_namespace": spec.path_namespace,
            "byte_count": spec.byte_count,
            "sha256": spec.sha256,
        }:
            _fail("DIRECT_SEMANTIC_SOURCE_BINDING_INVALID:" + spec.artifact_role)

    seen: set[str] = set()
    ranks: list[int] = []
    for row in rows:
        event_id = row["canonical_event_id"]
        if not event_id or event_id in seen:
            _fail("CENSUS_CANONICAL_EVENT_DUPLICATE_OR_EMPTY")
        seen.add(event_id)
        try:
            ranks.append(int(row["scaleup_rank"]))
        except ValueError as error:
            raise Cumulative1000CurrentGlobalReadinessCensusError(
                f"{ERROR_TOKEN}:CENSUS_RANK_INVALID:{event_id}"
            ) from error
        for column in _BOOL_COLUMNS:
            _parse_bool(row[column], column)
        if row["training_materialization_allowed_current_source"] not in {
            "",
            "true",
            "false",
        }:
            _fail("TRAINING_MATERIALIZATION_SOURCE_VALUE_INVALID:" + event_id)
        for source_column in (
            "human_review_authority_source",
            "chemistry_authority_source",
            "task_relevance_authority_source",
            "positive_authority_source",
        ):
            source = row[source_column]
            if source and source not in binding_paths:
                _fail("ROW_SOURCE_PROVENANCE_UNKNOWN:" + source_column + ":" + event_id)
        if row["feature_semantics_status"] != (
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER"
        ):
            _fail("FEATURE_SEMANTICS_STATUS_INVALID:" + event_id)

        chemistry = row["chemistry_disposition"]
        task = row["task_relevance_disposition"]
        training = row["training_use_disposition"]
        if chemistry not in {
            CHEMISTRY_POSITIVE,
            CHEMISTRY_NOT_ESTABLISHED,
            CHEMISTRY_UNRESOLVED,
        }:
            _fail("CHEMISTRY_DISPOSITION_INVALID:" + event_id)
        if task not in {TASK_RELEVANT, TASK_NOT_RELEVANT, TASK_UNRESOLVED}:
            _fail("TASK_RELEVANCE_DISPOSITION_INVALID:" + event_id)
        if training not in {
            reconciliation.TRAINING_INCLUDE,
            reconciliation.TRAINING_EXCLUDE,
            reconciliation.TRAINING_NOT_APPLICABLE,
            TRAINING_UNRESOLVED,
        }:
            _fail("TRAINING_USE_DISPOSITION_INVALID:" + event_id)
        if task == TASK_NOT_RELEVANT and (
            chemistry != CHEMISTRY_NOT_ESTABLISHED
            or training != reconciliation.TRAINING_NOT_APPLICABLE
        ):
            _fail("TASK_NOT_RELEVANT_CHEMISTRY_SEMANTICS_INVALID:" + event_id)
        if chemistry == CHEMISTRY_NOT_ESTABLISHED and task != TASK_NOT_RELEVANT:
            _fail("CHEMISTRY_NOT_ESTABLISHED_SCOPE_INVALID:" + event_id)
        if training == reconciliation.TRAINING_EXCLUDE and chemistry != CHEMISTRY_POSITIVE:
            _fail("TRAINING_EXCLUSION_ACCIDENTALLY_NEGATIVE:" + event_id)
        if row["human_training_excluded"] == "true" and training != (
            reconciliation.TRAINING_EXCLUDE
        ):
            _fail("HUMAN_TRAINING_EXCLUSION_DISPOSITION_INVALID:" + event_id)
        if row["positive_authority_source"] == _G3H_EVENT and (
            training != reconciliation.TRAINING_EXCLUDE
            or row["human_training_excluded"] != "true"
            or row["reactive_pair_training_target_available"] != "false"
        ):
            _fail("G3H_TRAINING_EXCLUSION_OR_INTEGRATION_LOST:" + event_id)

        role_authoritative = row["role_partition_sample_authoritative"] == "true"
        if role_authoritative:
            if (
                chemistry != CHEMISTRY_POSITIVE
                or row["role_profile"] not in {STRICT_PROFILE, DIRECT_PROFILE}
                or row["canonical_mask_structural_labels_available"] != "true"
            ):
                _fail("AUTHORITATIVE_ROLE_ROW_INVALID:" + event_id)
            expected_task_ids = (
                list(STRICT_TASK_IDS)
                if row["role_profile"] == STRICT_PROFILE
                else list(DIRECT_TASK_IDS)
            )
            try:
                task_ids = json.loads(row["structurally_applicable_task_ids_json"])
            except json.JSONDecodeError as error:
                raise Cumulative1000CurrentGlobalReadinessCensusError(
                    f"{ERROR_TOKEN}:ROLE_TASK_IDS_JSON_INVALID:{event_id}"
                ) from error
            if task_ids != expected_task_ids or 3 not in task_ids:
                _fail("ROLE_EXACT5_APPLICABILITY_INVALID:" + event_id)
        elif (
            row["role_profile"] != ROLE_NOT_ESTABLISHED
            or row["canonical_mask_structural_labels_available"] != "false"
            or row["structurally_applicable_task_ids_json"] != "null"
        ):
            _fail("ROLELESS_ROW_FALSE_APPLICABILITY_NOT_UNKNOWN:" + event_id)

        if row["reactive_pair_sample_authoritative"] == "true" and chemistry != (
            CHEMISTRY_POSITIVE
        ):
            _fail("PAIR_AUTHORITY_WITHOUT_POSITIVE_CHEMISTRY:" + event_id)
        if row["reactive_pair_training_target_available"] == "true" and (
            row["reactive_pair_sample_authoritative"] != "true"
        ):
            _fail("PAIR_TARGET_WITHOUT_SAMPLE_AUTHORITY:" + event_id)
        if row["post_geometry_training_target_available"] == "true" and (
            row["post_geometry_sample_authoritative"] != "true"
            or row["post_geometry_source_evidence_available"] != "true"
        ):
            _fail("POST_EVIDENCE_PROMOTED_WITHOUT_AUTHORITY:" + event_id)
        if (
            row["pre_geometry_authoritative"] != "false"
            or row["pre_geometry_training_target_available"] != "false"
        ):
            _fail("POST_TO_PRE_OR_PRE_ZERO_FILL_DETECTED:" + event_id)
        if row["training_use_include"] != _bool_cell(
            training == reconciliation.TRAINING_INCLUDE
        ):
            _fail("TRAINING_USE_INCLUDE_BOOLEAN_INVALID:" + event_id)
        if row["formal_training_admitted"] == "true" and (
            row["current_runtime_model_usable"] != "true"
            or row["formal_split_authoritative"] != "true"
            or row["formal_split"] != "train"
        ):
            _fail("TRAINING_ADMISSION_PROMOTION_INVALID:" + event_id)
        if row["future_training_admission_candidate"] == "true" and (
            row["formal_training_admitted"] != "false"
            or row["current_runtime_model_usable"] != "false"
        ):
            _fail("FUTURE_CANDIDATE_PROMOTED_TO_ADMISSION:" + event_id)
        if row["formal_split_authoritative"] == "true" and row["formal_split"] not in {
            "train",
            "validation",
            "test",
        }:
            _fail("FORMAL_SPLIT_VALUE_INVALID:" + event_id)
        if row["formal_split_authoritative"] == "false" and row["formal_split"]:
            _fail("NONAUTHORITATIVE_FORMAL_SPLIT_POPULATED:" + event_id)
    if ranks != list(range(1, 1001)):
        _fail("CENSUS_RANK_GAP_OR_ORDER_INVALID")
    if _event_set_sha256(seen) != EXPECTED_EVENT_SET_SHA256_V1["universe"]:
        _fail("CENSUS_EVENT_SET_SHA256_INVALID")

    expected_counts = {
        "raw_structure_available": 997,
        "exact_cys_sg_event_recovered": 867,
        "explicit_covalent_evidence": 867,
        "distance_only_event_inference_used": 0,
        "full_coordinate_post_evidence_available": 867,
        "ccd_graph_complete": 865,
        "feature_compatible": 865,
        "structural_processing_success": 865,
        "post_geometry_source_evidence_available": 867,
        "representation_gap": 78,
        "feature_incompatible": 2,
        "priority_review_in_scope": 338,
        "reactive_pair_raw_structural_evidence": 865,
        "reactive_pair_sample_authoritative": 49,
        "reactive_pair_training_target_available": 41,
        "role_partition_sample_authoritative": 49,
        "canonical_mask_structural_labels_available": 49,
        "post_geometry_sample_authoritative": 21,
        "post_geometry_training_target_available": 17,
        "pre_geometry_authoritative": 0,
        "pre_geometry_training_target_available": 0,
        "training_use_include": 29,
        "future_training_admission_candidate": 12,
        "formal_training_admitted": 5,
        "current_runtime_model_usable": 17,
    }
    for column, expected in expected_counts.items():
        if sum(row[column] == "true" for row in rows) != expected:
            _fail("CENSUS_BOOLEAN_COUNT_INVALID:" + column)
    if Counter(row["current_global_status"] for row in rows) != Counter(
        EXPECTED_GLOBAL_STATUS_COUNTS_V1
    ):
        _fail("CENSUS_EXACT11_STATUS_DISTRIBUTION_INVALID")
    if Counter(row["chemistry_disposition"] for row in rows) != Counter(
        {CHEMISTRY_POSITIVE: 49, CHEMISTRY_NOT_ESTABLISHED: 86, CHEMISTRY_UNRESOLVED: 865}
    ):
        _fail("CENSUS_CHEMISTRY_DISTRIBUTION_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter(
        {TASK_RELEVANT: 50, TASK_NOT_RELEVANT: 86, TASK_UNRESOLVED: 864}
    ):
        _fail("CENSUS_TASK_RELEVANCE_DISTRIBUTION_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter(
        {
            reconciliation.TRAINING_INCLUDE: 29,
            reconciliation.TRAINING_EXCLUDE: 20,
            reconciliation.TRAINING_NOT_APPLICABLE: 86,
            TRAINING_UNRESOLVED: 865,
        }
    ):
        _fail("CENSUS_TRAINING_USE_DISTRIBUTION_INVALID")
    if Counter(
        row["role_profile"]
        for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    ) != Counter({STRICT_PROFILE: 31, DIRECT_PROFILE: 18}):
        _fail("CENSUS_ROLE_PROFILE_DISTRIBUTION_INVALID")

    top_pending = summary.get("top_pending_review_units_by_event_yield")
    if type(top_pending) is not list or len(top_pending) != 10:
        _fail("SUMMARY_TOP_PENDING_EXACT10_INVALID")
    expected_top = (
        "COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74",
        "COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58",
        "COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22",
        "COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81",
        "COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D",
        "COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62",
        "COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410",
        "COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450",
        "COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5",
        "COVAPIE_BULK_REVIEW_UNIT_6B422BBF7FAD44F6",
    )
    if tuple(item.get("review_unit_id") for item in top_pending) != expected_top or tuple(
        item.get("rank") for item in top_pending
    ) != tuple(range(1, 11)):
        _fail("SUMMARY_TOP_PENDING_RANKING_DRIFT")
    derived_summary = _build_summary(rows, top_pending)
    if summary != derived_summary:
        _fail("SUMMARY_NOT_DERIVED_FROM_CENSUS_ROWS")
    if summary["training_stage"][
        "training_materialization_allowed_global_status"
    ] != "NOT_COMPUTABLE_FROM_CURRENT_PUBLISHED_AUTHORITY":
        _fail("TRAINING_MATERIALIZATION_GLOBAL_STATUS_INVALID")
    if summary["blockers"] != {
        "non_exclusive_counts_must_not_be_summed": True,
        "chemistry_unresolved": {"all_1000": 865},
        "pair_authority_absent": {"all_1000": 951, "within_positive_49": 0},
        "role_authority_absent": {"all_1000": 951, "within_positive_49": 0},
        "human_training_exclusion": {"within_positive_49": 20},
        "missing_split_authority": {"within_positive_49": 8, "within_include_29": 4},
        "missing_tensor_integration": {
            "within_positive_49": 8,
            "within_include_29": 0,
            "all_missing_are_g3h_excluded_population": True,
        },
        "missing_POST_training_authority": {
            "within_positive_49": 32,
            "within_include_29": 12,
        },
        "missing_training_admission": {
            "within_positive_49": 44,
            "within_include_29": 24,
        },
        "feature_semantics_pending": {"within_positive_49": 49},
    }:
        _fail("SUMMARY_BLOCKER_COUNTS_INVALID")
    boundary = summary["authority_boundary"]
    if (
        boundary["CURRENT_GLOBAL_RECONCILIATION_COMPLETE"] is not True
        or boundary["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is not True
        or boundary["READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION"] is not True
        or boundary["READY_FOR_FORMAL_TRAINING"] is not False
        or any(
            boundary[key] is not False
            for key in (
                "new_human_authority_created",
                "new_chemistry_authority_created",
                "new_reusable_authority_created",
                "tensor_integration_performed",
                "loader_modified",
                "batch_modified",
                "model_forward_performed",
                "auxiliary_head_executed",
                "loss_executed",
                "backward_performed",
                "optimizer_created",
                "optimizer_step_performed",
                "parameter_update_performed",
                "training_performed",
                "fine_tune_performed",
                "training_admission_created",
                "training_dataset_changed",
                "feature_semantics_audit_performed",
            )
        )
    ):
        _fail("SUMMARY_AUTHORITY_BOUNDARY_INVALID")
    if _sha256(_csv_bytes(rows)) != EXPECTED_CENSUS_PROJECTION_SHA256_V1:
        _fail("CENSUS_EXACT_PROJECTION_SHA256_INVALID")
    if _sha256(_json_bytes(summary)) != EXPECTED_SUMMARY_PAYLOAD_SHA256_V1:
        _fail("SUMMARY_EXACT_PAYLOAD_SHA256_INVALID")
    if _sha256(
        _canonical_json(list(bindings)).encode("utf-8")
    ) != EXPECTED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1:
        _fail("SEMANTIC_SOURCE_BINDINGS_EXACT_SHA256_INVALID")
    return True


def _validate_text_payload(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("OUTPUT_UTF8_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusError(
            f"{ERROR_TOKEN}:OUTPUT_NOT_UTF8:{label}"
        ) from error
    if "\x00" in text or "\r" in text:
        _fail("OUTPUT_TEXT_INVARIANT_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        _fail("OUTPUT_FINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("OUTPUT_TRAILING_WHITESPACE:" + label)


def _candidate_contract_bindings(repo_root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for role, relative in (
        ("PRODUCTION_OWNER", PRODUCTION_RELATIVE),
        ("CHECKER", CHECKER_RELATIVE),
        ("TARGETED_TESTS", TEST_RELATIVE),
        ("GUIDE", GUIDE_RELATIVE),
    ):
        payload = _read_regular_file(repo_root / relative, role)
        _validate_text_payload(payload, relative.as_posix())
        result.append(
            {
                "artifact_role": role,
                "path": relative.as_posix(),
                "byte_count": len(payload),
                "sha256": _sha256(payload),
            }
        )
    return result


def build_covapie_cumulative1000_current_global_readiness_artifacts_v1(
    repo_root: Path,
) -> dict[str, bytes]:
    """Build the exact3 deterministic outputs without writing to the repository."""

    root = repo_root.resolve()
    computation = compute_covapie_cumulative1000_current_global_readiness_census_v1(
        root
    )
    census_payload = _csv_bytes(computation.rows)
    summary_payload = _json_bytes(computation.summary)
    _validate_text_payload(census_payload, CENSUS_FILE)
    _validate_text_payload(summary_payload, SUMMARY_FILE)
    if len(census_payload) > 1024 * 1024:
        _fail("CENSUS_OUTPUT_EXCEEDS_1_MIB")
    output_bindings = [
        {
            "artifact_role": "CENSUS_CSV",
            "path": (OUTPUT_DIRECTORY_RELATIVE / CENSUS_FILE).as_posix(),
            "byte_count": len(census_payload),
            "sha256": _sha256(census_payload),
        },
        {
            "artifact_role": "SUMMARY_JSON",
            "path": (OUTPUT_DIRECTORY_RELATIVE / SUMMARY_FILE).as_posix(),
            "byte_count": len(summary_payload),
            "sha256": _sha256(summary_payload),
        },
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "candidate_inventory": {
            "exact_file_count": 7,
            "paths": list(EXACT7_PATHS_V1),
        },
        "candidate_contract_bindings": _candidate_contract_bindings(root),
        "semantic_source_bindings": list(computation.semantic_source_bindings),
        "output_inventory": {
            "exact_output_count": 3,
            "paths": [
                (OUTPUT_DIRECTORY_RELATIVE / CENSUS_FILE).as_posix(),
                (OUTPUT_DIRECTORY_RELATIVE / SUMMARY_FILE).as_posix(),
                (OUTPUT_DIRECTORY_RELATIVE / MANIFEST_FILE).as_posix(),
            ],
        },
        "output_bindings_excluding_manifest_self": output_bindings,
        "manifest_self_binding": {
            "path": (OUTPUT_DIRECTORY_RELATIVE / MANIFEST_FILE).as_posix(),
            "sha256_recorded_inside_self": False,
            "policy": "MANIFEST_SELF_SHA256_PROHIBITED",
        },
        "determinism_contract": {
            "utf8": True,
            "lf_only": True,
            "single_final_lf": True,
            "timestamps_recorded": False,
            "machine_absolute_paths_recorded": False,
            "live_git_state_recorded": False,
        },
        "authority_boundary": computation.summary["authority_boundary"],
    }
    manifest_payload = _json_bytes(manifest)
    _validate_text_payload(manifest_payload, MANIFEST_FILE)
    manifest_text = manifest_payload.decode("utf-8")
    manifest_path = (OUTPUT_DIRECTORY_RELATIVE / MANIFEST_FILE).as_posix()
    for binding in output_bindings:
        if binding["path"] == manifest_path:
            _fail("MANIFEST_SELF_HASH_PROHIBITION_VIOLATED")
    forbidden_manifest_tokens = (
        '"hostname"',
        '"pid"',
        '"timestamp"',
        '"head"',
        '"commit_subject"',
        '"ahead"',
        '"behind"',
    )
    if any(token in manifest_text.lower() for token in forbidden_manifest_tokens):
        _fail("MANIFEST_LIFECYCLE_FIELD_FORBIDDEN")
    return {
        CENSUS_FILE: census_payload,
        SUMMARY_FILE: summary_payload,
        MANIFEST_FILE: manifest_payload,
    }


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise Cumulative1000CurrentGlobalReadinessCensusError(
            f"{ERROR_TOKEN}:OUTPUT_WRITE_FAILED:{path.name}"
        ) from error


def materialize_covapie_cumulative1000_current_global_readiness_artifacts_v1(
    repo_root: Path,
    output_directory: Path | None = None,
) -> dict[str, bytes]:
    """Write only the exact3 publication outputs after complete validation."""

    root = repo_root.resolve()
    output = (
        root / OUTPUT_DIRECTORY_RELATIVE
        if output_directory is None
        else output_directory.resolve()
    )
    try:
        output.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusError(
            f"{ERROR_TOKEN}:OUTPUT_DIRECTORY_CREATE_FAILED"
        ) from error
    artifacts = build_covapie_cumulative1000_current_global_readiness_artifacts_v1(
        root
    )
    existing = {path.name for path in output.iterdir() if path.is_file()}
    unexpected = existing - set(artifacts)
    if unexpected:
        _fail("OUTPUT_DIRECTORY_UNEXPECTED_FILE:" + sorted(unexpected)[0])
    for filename in (CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE):
        _atomic_write(output / filename, artifacts[filename])
    return artifacts
