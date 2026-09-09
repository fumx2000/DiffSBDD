"""Project frozen EI3 Exact3 human authority into metadata-only artifacts.

The formal JSON is parsed and independently validated.  Its validator is an
identity-only provenance input and is never imported, executed, or
subprocessed.  This stage creates no role, seed, task-label row, geometry
authority, tensor target, training admission, reconciliation, census refresh,
queue refresh, commit, or push authority.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
import csv
from dataclasses import fields
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, NoReturn

from covalent_ext.covapie_source_binding_policy_v2 import (
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


__all__ = (
    "EI3IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

ERROR_PREFIX = "COVAPIE_EI3_INGESTION_V1_ERROR"
BASELINE_COMMIT = "6c22eb41d55f7d08ff076a928070258700b335d9"
SCHEMA_VERSION = "covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_ei3_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_ei3_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_ei3_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_ei3_completed_decision_ingestion_manifest_v1"
FORMAL_DECISION_SCHEMA = "covapie_ei3_exact3_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
FORMAL_STAGE = "EI3_FORMAL_HUMAN_DECISION_V1"
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_79526304E5FB38A6"
EXPECTED_SCOPE = "CURRENT_EI3_EXACT3_TARGET_REVIEW_UNIT_ONLY"
EXPECTED_COMPLETED_LANE = "COMPLETED_TASK_DOMAIN_NEGATIVE"
EXPECTED_LEGACY_STATUS = "COMPLETED_HUMAN_NEGATIVE"
SOURCE_D2 = "OUT_OF_DOMAIN"
NORMALIZED_TASK_RELEVANCE = "NOT_RELEVANT"
SOURCE_D6 = "NOT_APPLICABLE"
NORMALIZED_TRAINING_DISPOSITION = "NOT_APPLICABLE"
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_NOT_AVAILABLE"
PRE_STATUS = "PRE_REACTION_UNRESOLVED"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_ei3_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_ei3_event_task_label_availability_v1.csv"
SUMMARY = "covapie_ei3_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_ei3_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

STATE_ROOT = Path(
    "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/"
    "EI3_COVAPIE_BULK_REVIEW_UNIT_79526304E5FB38A6"
)
FORMAL_DECISION_RELATIVE = (
    STATE_ROOT / "formal-human-decision-v1/ei3_formal_human_decision_v1.json"
)
FORMAL_VALIDATOR_RELATIVE = STATE_ROOT / (
    "formal-human-decision-v1/validate_ei3_formal_human_decision_v1.py"
)
EVENT_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/ei3_exact3_event_evidence_v1.csv"
)
GRAPH_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/ei3_graph_and_review_evidence_v1.json"
)
SOURCE_BINDING_POLICY_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
CANONICAL_TASK_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
GENERIC_OWNER_RELATIVE = Path(
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py"
)
CENSUS_MATRIX_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_me7_v1/"
    "covapie_cumulative1000_current_global_readiness_census_with_me7_v1.csv"
)
PRIORITY_QUEUE_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1/"
    "covapie_bulk_cys_sg_priority_human_review_queue_v1.csv"
)

EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:5ARB:A:CYS:217-:SG:F:EI3:C1",
        967,
        "5ARB",
        "F",
        1280,
        "0.70",
        "1.778",
        "1.778354",
        "0.000354",
        ("14.035", "-30.791", "-18.591"),
        ("15.744", "-31.176", "-18.897"),
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:5ARC:A:CYS:217-:SG:C:EI3:C1",
        968,
        "5ARC",
        "C",
        1277,
        "0.50",
        "1.848",
        "1.847656",
        "0.000344",
        ("12.181", "0.194", "-18.668"),
        ("12.037", "-1.102", "-17.359"),
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:5ARD:A:CYS:217-:SG:E:EI3:C1",
        969,
        "5ARD",
        "E",
        1279,
        "0.50",
        "1.787",
        "1.787376",
        "0.000376",
        ("13.926", "-30.734", "-18.626"),
        ("15.673", "-31.050", "-18.833"),
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)
EXPECTED_PDB_IDS = tuple(row[2] for row in EXPECTED_EVENTS)
TARGET_COUNTS = {pdb_id: 1 for pdb_id in EXPECTED_PDB_IDS}
METAL_COUNTS = {"5ARB": 0, "5ARC": 0, "5ARD": 2}

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
GENERIC_FACT_FIELDS = (
    "canonical_event_id",
    "review_unit_id",
    "human_review_completed",
    "legacy_completed_review_status",
    "task_relevance_disposition",
    "chemistry_disposition",
    "training_disposition",
    "human_training_excluded",
    "source_decision_schema",
    "source_decision_sha256",
    "source_binding_path",
)

# path, namespace, bytes, SHA256, executable, source role, validation method
_Binding = tuple[Path, str, int, str, bool, str, str]
FORMAL_BINDINGS: tuple[_Binding, ...] = (
    (
        FORMAL_DECISION_RELATIVE,
        "project_parent_relative",
        68366,
        "f0cf2e1703a327d2ace42bb0aba900e1f4a5ef46de96cc2c5f4acf93add2f5f7",
        False,
        "EI3_FROZEN_FORMAL_HUMAN_DECISION",
        "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE,
        "project_parent_relative",
        69828,
        "90773895c5a74ffb65a7f59d50cfcc5766355d74b98e269ebc1848acf184ae9b",
        False,
        "EI3_FROZEN_FORMAL_VALIDATOR",
        "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED",
    ),
)
SUPPORTING_BINDINGS: tuple[_Binding, ...] = (
    (
        EVENT_EVIDENCE_RELATIVE,
        "project_parent_relative",
        2702,
        "0a942726c4b2dd30ded1ec3225ab9b8ffbb253e76ddfc14be4f420da92d48323",
        False,
        "EI3_EXACT3_EVENT_EVIDENCE",
        "PARSED_CSV_TARGET_EXACT3_OBSERVED_GEOMETRY_AND_SOURCE_RECORDS",
    ),
    (
        GRAPH_EVIDENCE_RELATIVE,
        "project_parent_relative",
        82960,
        "851eb35b2845e7d06cd90136ff1d8bf59fdfcbdf9049a8380d14ee69c967b4a4",
        False,
        "EI3_GRAPH_AND_REVIEW_EVIDENCE",
        "PARSED_JSON_TARGET_METAL_CONTEXT_PRE_POST_AND_ENTITY_EVIDENCE",
    ),
)
POLICY_BINDING: _Binding = (
    SOURCE_BINDING_POLICY_RELATIVE,
    "repository_relative",
    3704,
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    False,
    "PUBLISHED_SOURCE_BINDING_POLICY_V2",
    "IMPORTED_CONTENT_IDENTITY_AND_SECURITY_POLICY",
)
CANONICAL_TASK_BINDING: _Binding = (
    CANONICAL_TASK_OWNER_RELATIVE,
    "repository_relative",
    67274,
    "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
    False,
    "PUBLISHED_CANONICAL_EXACT5_OWNER",
    "PARSED_AST_LITERAL_CONTRACT_ONLY_NO_ROLE_OR_TASK_RUNTIME",
)
GENERIC_BINDING: _Binding = (
    GENERIC_OWNER_RELATIVE,
    "repository_relative",
    35925,
    "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    False,
    "PUBLISHED_GENERIC_COMPLETED_DECISION_OWNER",
    "IMPORTED_READ_ONLY_FOR_ACTUAL_EXACT11_COMPATIBILITY",
)
CENSUS_BINDING: _Binding = (
    CENSUS_MATRIX_RELATIVE,
    "repository_relative",
    559446,
    "9e45211a66a003be7f5f8c8b49b0a7f6f22bce362a06601708affff6a0ce4b4a",
    False,
    "CURRENT_WITH_ME7_CENSUS_MATRIX",
    "PARSED_CSV_PREINGESTION_PENDING_STATE_READ_ONLY",
)
QUEUE_BINDING: _Binding = (
    PRIORITY_QUEUE_RELATIVE,
    "repository_relative",
    50116,
    "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2",
    False,
    "FROZEN_PRIORITY_QUEUE",
    "PARSED_CSV_PENDING_UNIT_STATE_READ_ONLY",
)
ACTIVE_BINDINGS = (
    *FORMAL_BINDINGS,
    *SUPPORTING_BINDINGS,
    POLICY_BINDING,
    CANONICAL_TASK_BINDING,
    GENERIC_BINDING,
    CENSUS_BINDING,
    QUEUE_BINDING,
)


class EI3IngestionSafetyError(ValueError):
    """Raised when the frozen EI3 projection contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise EI3IngestionSafetyError(ERROR_PREFIX + ":" + reason)


def _expect(actual: object, expected: object, reason: str) -> None:
    if type(actual) is not type(expected) or actual != expected:
        _fail(reason)


def _required(mapping: object, key: str, path: str) -> object:
    if type(mapping) is not dict:
        _fail("REQUIRED_PATH_PARENT_NOT_OBJECT:" + path)
    if key not in mapping:
        _fail("REQUIRED_PATH_MISSING:" + path + "." + key)
    return mapping[key]


def _path(mapping: object, dotted: str) -> object:
    value = mapping
    walked = "$"
    for key in dotted.split("."):
        value = _required(value, key, walked)
        walked += "." + key
    return value


def _expect_fields(
    mapping: object, expected: Mapping[str, object], reason: str
) -> Mapping[str, object]:
    if type(mapping) is not dict:
        _fail(reason + ":NOT_OBJECT")
    for key, value in expected.items():
        if key not in mapping:
            _fail("REQUIRED_PATH_MISSING:" + reason + "." + key)
        _expect(mapping[key], value, reason + ":" + key)
    return mapping


def _expect_exact(
    mapping: object, expected: Mapping[str, object], reason: str
) -> Mapping[str, object]:
    result = _expect_fields(mapping, expected, reason)
    if set(result) != set(expected):
        _fail(reason + ":FIELD_SET")
    return result


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _json_bytes(value: object) -> bytes:
    return _canonical_json(value) + b"\n"


def _json_cell(value: object) -> str:
    return _canonical_json(value).decode("utf-8")


def _strict_json(payload: bytes, label: str) -> dict[str, Any]:
    if type(payload) is not bytes:
        _fail("JSON_PAYLOAD_NOT_BYTES:" + label)
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload or b"\r" in payload:
        _fail("JSON_TEXT_INVARIANT_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise EI3IngestionSafetyError(
            ERROR_PREFIX + ":JSON_UTF8_INVALID:" + label
        ) from error

    def pairs_hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                _fail("JSON_DUPLICATE_KEY:" + label + ":" + key)
            result[key] = value
        return result

    def reject_constant(value: str) -> NoReturn:
        _fail("JSON_NONFINITE:" + label + ":" + value)

    try:
        value = json.loads(
            text, object_pairs_hook=pairs_hook, parse_constant=reject_constant
        )
    except json.JSONDecodeError as error:
        raise EI3IngestionSafetyError(
            ERROR_PREFIX + ":JSON_PARSE_FAILED:" + label
        ) from error
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _parse_csv(payload: bytes, label: str) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    if type(payload) is not bytes:
        _fail("CSV_PAYLOAD_NOT_BYTES:" + label)
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload or b"\r" in payload:
        _fail("CSV_TEXT_INVARIANT_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise EI3IngestionSafetyError(
            ERROR_PREFIX + ":CSV_UTF8_INVALID:" + label
        ) from error
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        header = tuple(reader.fieldnames or ())
        if not header or len(header) != len(set(header)):
            _fail("CSV_HEADER_DUPLICATE_OR_EMPTY:" + label)
        rows = list(reader)
    except csv.Error as error:
        raise EI3IngestionSafetyError(
            ERROR_PREFIX + ":CSV_PARSE_FAILED:" + label
        ) from error
    if any(None in row or set(row) != set(header) for row in rows):
        _fail("CSV_ROW_WIDTH_INVALID:" + label)
    return header, rows


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=header, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _binding_record(binding: _Binding) -> dict[str, object]:
    path, namespace, byte_count, digest, executable, role, method = binding
    return {
        "path": path.as_posix(),
        "path_namespace": namespace,
        "byte_count": byte_count,
        "SHA256": digest,
        "semantic_source_identity": f"{namespace}:{path.as_posix()}@{digest}",
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "EXECUTABLE" if executable else "NON_EXECUTABLE",
        "source_role": role,
        "validation_method": method,
    }


def _normalize_overrides(value: Mapping[Path, Path] | None) -> dict[Path, Path]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        _fail("SOURCE_OVERRIDES_NOT_MAPPING")
    result = {Path(key): Path(path) for key, path in value.items()}
    if not set(result).issubset({binding[0] for binding in ACTIVE_BINDINGS}):
        _fail("SOURCE_OVERRIDE_UNKNOWN_BINDING")
    return result


def _resolve(repo_root: Path, binding: _Binding, overrides: Mapping[Path, Path]) -> Path:
    relative, namespace, *_rest = binding
    if relative in overrides:
        return overrides[relative]
    if namespace == "repository_relative":
        return repo_root / relative
    if namespace == "project_parent_relative":
        return repo_root.parent / relative
    _fail("SOURCE_NAMESPACE_INVALID:" + relative.as_posix())


def _verify_binding(
    repo_root: Path, binding: _Binding, overrides: Mapping[Path, Path]
) -> bytes:
    relative, _namespace, byte_count, digest, executable, role, _method = binding
    try:
        return verify_bound_source_v2(
            path=_resolve(repo_root, binding, overrides),
            expected_byte_count=byte_count,
            expected_sha256=digest,
            label=role + ":" + relative.as_posix(),
            expected_executable=executable,
        )
    except SourceBindingPolicyV2Error as error:
        raise EI3IngestionSafetyError(
            ERROR_PREFIX + ":SOURCE_BINDING_FAILED:" + relative.as_posix()
        ) from error


def _verify_bindings(
    repo_root: Path, overrides: Mapping[Path, Path]
) -> dict[Path, bytes]:
    identities = [
        (binding[1], binding[0].as_posix(), binding[3]) for binding in ACTIVE_BINDINGS
    ]
    if len(ACTIVE_BINDINGS) != 9 or len(set(identities)) != 9:
        _fail("ACTIVE_SOURCE_BINDINGS_NOT_UNIQUE_EXACT9")
    return {
        binding[0]: _verify_binding(repo_root, binding, overrides)
        for binding in ACTIVE_BINDINGS
    }


FORMAL_INTERNAL_BINDINGS = (
    (
        "human-decision-candidate-v1/ei3_filled_unsigned_human_decision_candidate_v1.json",
        63189,
        "7d492e3ed231c4dbbcdb157530b6b33f02cf25a1201486c441b9f3872241c095",
        "0664",
        "frozen_candidate_ei3_filled_unsigned_human_decision_candidate_v1.json",
    ),
    (
        "human-decision-candidate-v1/validate_ei3_filled_unsigned_human_decision_candidate_v1.py",
        65209,
        "7f4246fbfb08da419792e9164ee9ea9f1e8f8478d61790b9cf34f1d9b34e8a43",
        "0664",
        "frozen_candidate_validate_ei3_filled_unsigned_human_decision_candidate_v1.py",
    ),
    (
        "review-preparation-v1/ei3_review_preparation_manifest_v1.json",
        12993,
        "18568ccfa6cbca050e871f1ebbff689ba8cd0873a3f3ee68642c241e7e274dd0",
        "0644",
        "frozen_preparation_ei3_review_preparation_manifest_v1.json",
    ),
    (
        "review-preparation-v1/ei3_exact3_event_evidence_v1.csv",
        2702,
        "0a942726c4b2dd30ded1ec3225ab9b8ffbb253e76ddfc14be4f420da92d48323",
        "0644",
        "frozen_preparation_ei3_exact3_event_evidence_v1.csv",
    ),
    (
        "review-preparation-v1/ei3_graph_and_review_evidence_v1.json",
        82960,
        "851eb35b2845e7d06cd90136ff1d8bf59fdfcbdf9049a8380d14ee69c967b4a4",
        "0644",
        "frozen_preparation_ei3_graph_and_review_evidence_v1.json",
    ),
    (
        "review-preparation-v1/HUMAN_REVIEW_GUIDE.md",
        3781,
        "1c3d2654b7ec6ed802ceecf90bb26e2096934b7b7d1a289ad6709ce949bf2c79",
        "0644",
        "frozen_preparation_HUMAN_REVIEW_GUIDE.md",
    ),
    (
        "review-preparation-v1/ei3_unsigned_human_decision_template_v1.json",
        6102,
        "ae0200ca553cbe58e0431462eea0b1e139fb2acb5aa197296e895660e83f5a0d",
        "0644",
        "frozen_preparation_ei3_unsigned_human_decision_template_v1.json",
    ),
    (
        "review-preparation-v1/build_and_check_ei3_review_preparation_v1.py",
        115556,
        "7a95f78baec89f9fa767c3d81a98da55515f7be20a050832732502df2577d071",
        "0664",
        "frozen_preparation_build_and_check_ei3_review_preparation_v1.py",
    ),
    (
        "scientific-validation-v1/ei3_scientific_validation_v1.json",
        60743,
        "98ca106529bd27afd46714167e7af2a5c418f795244a48ce327c25911aae1d36",
        "0664",
        "frozen_scientific_ei3_scientific_validation_v1.json",
    ),
    (
        "scientific-validation-v1/validate_ei3_scientific_validation_v1.py",
        83014,
        "d3b3de6122f256048f1f6efda931bbb4f91bc9f06dd7925e39a3c003136513bf",
        "0664",
        "frozen_scientific_validate_ei3_scientific_validation_v1.py",
    ),
)


def _formal_source_rows() -> list[dict[str, object]]:
    return [
        {
            "SHA256": digest,
            "bytes": byte_count,
            "mode": mode,
            "path_namespace": "review_unit_relative",
            "relative_path": relative,
            "source_role": role,
        }
        for relative, byte_count, digest, mode, role in FORMAL_INTERNAL_BINDINGS
    ]


def _formal_task_rows() -> list[dict[str, object]]:
    return [
        {"display_alias": alias, "semantic_long_name": semantic, "task_id": task_id}
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]


def _validate_formal(formal: Mapping[str, Any]) -> None:
    """Validate EI3's real Exact3 schema without executing its validator."""
    expected_top = {
        "PRE_boundary",
        "approved_D1_D6",
        "authorization_record",
        "event_context_boundary",
        "frozen_candidate_binding",
        "frozen_candidate_evidence_snapshot",
        "non_created_authority",
        "operation_boundary",
        "output_inventory",
        "readiness",
        "record_role",
        "role_and_task_disposition",
        "sample_identity",
        "sample_level_authority",
        "schema_version",
        "source_bindings",
        "stage",
    }
    if type(formal) is not dict or set(formal) != expected_top:
        _fail("FORMAL_TOP_LEVEL_FIELDS_DRIFT")
    _expect(_path(formal, "schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(_path(formal, "stage"), FORMAL_STAGE, "FORMAL_STAGE_DRIFT")
    _expect(_path(formal, "record_role"), FORMAL_RECORD_ROLE, "FORMAL_RECORD_ROLE_DRIFT")
    _expect_exact(
        _path(formal, "sample_identity"),
        {
            "all_EI3_authority": False,
            "all_Savinase_authority": False,
            "canonical_target_event_ids": list(EXPECTED_EVENT_IDS),
            "ligand_component_id": "EI3",
            "other_structure_authority": False,
            "pdb_ids": list(EXPECTED_PDB_IDS),
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scaleup_ranks": list(EXPECTED_RANKS),
            "scope": EXPECTED_SCOPE,
            "target_event_count": 3,
        },
        "$.sample_identity",
    )
    authorization = _path(formal, "authorization_record")
    _expect_fields(
        authorization,
        {
            "approval_time": None,
            "attestor_id": "fmx",
            "authorization_bound_candidate_SHA256": (
                "7d492e3ed231c4dbbcdb157530b6b33f02cf25a1201486c441b9f3872241c095"
            ),
            "authorization_complete": True,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "formalization_of_external_human_approval": True,
            "machine_generated_human_authorization": False,
            "reviewer_id": "fmx",
        },
        "$.authorization_record",
    )
    authorization_text = _path(formal, "authorization_record.authorization_text")
    if type(authorization_text) is not str or not authorization_text.startswith(
        "批准本轮 EI3 Exact3 的建议确认值。"
    ) or "5ARD的metalc8/metalc9仅为金属配位上下文" not in authorization_text:
        _fail("FORMAL_AUTHORIZATION_TEXT_DRIFT")
    _expect_exact(
        _path(formal, "frozen_candidate_binding"),
        {
            "SHA256": "7d492e3ed231c4dbbcdb157530b6b33f02cf25a1201486c441b9f3872241c095",
            "authorization_bound_to_exact_SHA256": (
                "7d492e3ed231c4dbbcdb157530b6b33f02cf25a1201486c441b9f3872241c095"
            ),
            "bytes": 63189,
            "candidate_human_fields_remained_unset": True,
            "candidate_is_human_authority": False,
            "candidate_modified": False,
            "candidate_was_unsigned": True,
            "mode": "0664",
            "path_namespace": "review_unit_relative",
            "relative_path": (
                "human-decision-candidate-v1/"
                "ei3_filled_unsigned_human_decision_candidate_v1.json"
            ),
            "source_role": (
                "frozen_candidate_ei3_filled_unsigned_human_decision_candidate_v1.json"
            ),
        },
        "$.frozen_candidate_binding",
    )
    _expect_exact(
        _path(formal, "approved_D1_D6"),
        {
            "D1_observed_covalent_chemistry": {
                "chemistry_positive": True,
                "decision": "POSITIVE",
                "human_answered": True,
                "human_approved": True,
                "scope": (
                    "THREE_SOURCE_OBSERVATIONS_ONLY_NO_GENERAL_MECHANISM_OR_TRAINING_INFERENCE"
                ),
            },
            "D2_task_generation_domain_relevance": {
                "chemistry_negative": False,
                "chemistry_positive_preserved": True,
                "decision": SOURCE_D2,
                "human_answered": True,
                "human_approved": True,
                "scope": "CURRENT_UNIT_AND_CURRENT_PROJECT_TASK_DEFINITION_ONLY",
            },
            "D3_reactive_atom_pair_confirmation_or_revision": {
                "component_atom": "C1",
                "decision": "CONFIRM_OBSERVED_PAIR",
                "human_answered": True,
                "human_approved": True,
                "metal_context_connection_count_by_pdb": METAL_COUNTS,
                "pair": "SG:C1",
                "protein_atom": "SG",
                "target_covalent_connection_count_by_pdb": TARGET_COUNTS,
            },
            "D4_role_partition_and_minimal_seed": {
                "decision": "CANNOT_DETERMINE",
                "human_answered": True,
                "human_approved": True,
                "role_candidate_count": 0,
                "selected_candidate_id": None,
            },
            "D5_structural_task_applicability": {
                "decision": "NOT_DETERMINABLE",
                "human_answered": True,
                "human_approved": True,
                "task_ids": None,
            },
            "D6_later_training_use_disposition": {
                "chemistry_negative": False,
                "decision": SOURCE_D6,
                "formal_training_admitted": False,
                "future_training_admission_candidate": False,
                "human_answered": True,
                "human_approved": True,
                "human_training_excluded": False,
            },
        },
        "$.approved_D1_D6",
    )
    _expect_exact(
        _path(formal, "sample_level_authority"),
        {
            "approved": True,
            "formal_decision_created": True,
            "formal_sample_level_authority_created": True,
            "human_decision_created": True,
            "human_review_completed": True,
            "minimal_seed_sample_authoritative": False,
            "role_partition_sample_authoritative": False,
            "sample_D6_disposition_authority": True,
            "sample_chemistry_authority": True,
            "sample_observed_pair_authority": True,
            "sample_task_domain_authority": True,
            "task_applicability_sample_authoritative": False,
            "unsigned": False,
        },
        "$.sample_level_authority",
    )
    _expect_exact(
        _path(formal, "event_context_boundary"),
        {
            "covalent_and_metal_context_distinguished": True,
            "metal_context_connection_count_by_pdb": METAL_COUNTS,
            "metal_context_connection_ids": ["metalc8", "metalc9"],
            "metal_context_promoted_to_target_event": False,
            "metal_context_received_geometry_training_authority": False,
            "metal_context_received_independent_pair_authority": False,
            "metal_context_supporting_context_only": True,
            "source_observed_pair": "SG:C1",
            "target_covalent_connection_count_by_pdb": TARGET_COUNTS,
            "target_event_ids": list(EXPECTED_EVENT_IDS),
            "target_pair_confirmed_as_observed_record": True,
            "target_scaleup_ranks": list(EXPECTED_RANKS),
            "unqualified_unique_attachment_claim_created": False,
        },
        "$.event_context_boundary",
    )
    role = _path(formal, "role_and_task_disposition")
    expected_nulls = (
        "applicable_task_ids",
        "linker_atom_ids",
        "minimal_seed",
        "minimal_seed_atom_ids",
        "primary_anchor",
        "role_partitions",
        "role_profile",
        "scaffold_atom_ids",
        "selected_candidate_id",
        "selected_role_candidate",
        "warhead_atom_ids",
    )
    for key in expected_nulls:
        _expect(_required(role, key, "$.role_and_task_disposition"), None, "ROLE_TASK_NULL_DRIFT:" + key)
    _expect_fields(
        role,
        {
            "B3_present": True,
            "D4_formally_answered": True,
            "D5_formally_answered": True,
            "canonical_v1_task_count": 5,
            "canonical_v1_tasks": _formal_task_rows(),
            "combination_search_executed": False,
            "role_candidate_count": 0,
            "role_runtime_executed": False,
            "sixth_task_created": False,
            "task_runtime_executed": False,
        },
        "$.role_and_task_disposition",
    )
    pre = _path(formal, "PRE_boundary")
    _expect_fields(
        pre,
        {
            "accurate_PRE_is_not_V1_global_hard_prerequisite": True,
            "accurate_PRE_required_before_training_feature_contract": False,
            "sample_cannot_determine_generalized_to_all_samples": False,
            "sample_role_task_or_training_conditions_satisfied": False,
        },
        "$.PRE_boundary",
    )
    _expect_exact(
        _path(formal, "PRE_boundary.frozen_source_projection"),
        {
            "POST_to_PRE_copy": False,
            "PRE_authority_created": False,
            "PRE_coordinates_created": False,
            "PRE_geometry_authoritative_count": 0,
            "PRE_source_graph_count_per_event": [0, 0, 0],
            "PRE_source_graph_mapping_count_per_event": [0, 0, 0],
            "PRE_source_graph_mapping_status_per_event": [PRE_MAPPING_STATUS] * 3,
            "PRE_status_per_event": [PRE_STATUS] * 3,
            "PRE_topology_created": False,
            "PRE_zero_fill": False,
            "accurate_PRE_required_before_training_feature_contract": False,
            "missing_precursor_atoms_or_leaving_groups_added": False,
        },
        "$.PRE_boundary.frozen_source_projection",
    )
    _expect_fields(
        _path(formal, "readiness"),
        {
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "FORMAL_TRAINING_ADMITTED": False,
            "MASK_TENSOR_TARGETS_CREATED": False,
            "READY_FOR_TRAINING": False,
            "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
            "TASK_LABEL_AUTHORITY": False,
            "TRAINING_MATERIALIZATION_ALLOWED": False,
            "TRAINING_STARTED": False,
        },
        "$.readiness",
    )
    _expect_fields(
        _path(formal, "non_created_authority"),
        {
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
            "MASK_TENSOR_TARGETS_CREATED": False,
            "POST_geometry_training_authority": False,
            "PRE_authority": False,
            "READY_FOR_TRAINING": False,
            "TASK_LABEL_AUTHORITY": False,
            "TRAINING_ADMISSION_CREATED": False,
            "TRAINING_MATERIALIZATION_ALLOWED": False,
            "TRAINING_STARTED": False,
            "reusable_authority_created": False,
        },
        "$.non_created_authority",
    )
    frozen = _path(formal, "frozen_candidate_evidence_snapshot")
    _expect_fields(
        frozen,
        {
            "historical_no_human_authority_fields_are_source_snapshot_only": True,
            "machine_confidences_not_changed_by_human_approval": True,
            "snapshot_scope": (
                "FROZEN_PREFORMAL_MACHINE_PROPOSALS_AND_EVIDENCE_NOT_CURRENT_AUTHORITY_STATE"
            ),
        },
        "$.frozen_candidate_evidence_snapshot",
    )
    machine = _path(formal, "frozen_candidate_evidence_snapshot.source_machine_proposals")
    if type(machine) is not dict or set(machine) != set(_path(formal, "approved_D1_D6")):
        _fail("FROZEN_MACHINE_PROPOSAL_KEYS_DRIFT")
    for key, proposal in machine.items():
        _expect_fields(
            proposal,
            {"formal_selected": False, "human_selected": False, "proposal_only": True},
            "$.frozen_candidate_evidence_snapshot.source_machine_proposals." + key,
        )
    _expect(_path(formal, "source_bindings"), _formal_source_rows(), "FORMAL_SOURCE_BINDINGS_DRIFT")


EVENT_EVIDENCE_HEADER = (
    "scaleup_rank", "canonical_event_id", "review_unit_id", "pdb_id", "model_number",
    "protein_label_asym_id", "protein_auth_asym_id", "protein_label_comp_id",
    "protein_auth_comp_id", "protein_label_seq_id", "protein_auth_seq_id",
    "protein_insertion_code", "protein_atom_id", "protein_altloc", "protein_occupancy",
    "component_label_asym_id", "component_auth_asym_id", "component_label_comp_id",
    "component_auth_comp_id", "component_label_seq_id", "component_auth_seq_id",
    "component_insertion_code", "component_atom_id", "component_altloc",
    "component_occupancy", "connection_id", "connection_type", "connection_value_order",
    "protein_symmetry", "component_symmetry", "source_observed_pair",
    "explicit_covalent_evidence", "distance_only_event_inference_used",
    "reported_distance_angstrom", "recalculated_distance_angstrom",
    "absolute_difference_angstrom", "protein_x", "protein_y", "protein_z",
    "component_x", "component_y", "component_z", "source_datasets_json",
    "source_record_ids_json", "processing_pre_status", "pre_source_graph_count",
    "pre_source_graph_mapping_count", "pre_geometry_authoritative",
    "pre_geometry_training_target_available", "post_geometry_source_evidence_available",
    "post_geometry_sample_authoritative", "post_geometry_training_target_available",
    "target_event", "human_selected",
)


def _strict_json_cell(value: str, label: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise EI3IngestionSafetyError(
            ERROR_PREFIX + ":CSV_JSON_CELL_INVALID:" + label
        ) from error


def _validate_event_evidence(payload: bytes) -> list[dict[str, object]]:
    header, rows = _parse_csv(payload, "EI3_EVENT_EVIDENCE")
    if header != EVENT_EVIDENCE_HEADER:
        _fail("EVENT_EVIDENCE_HEADER_DRIFT")
    if len(rows) != 3:
        _fail("EVENT_EVIDENCE_NOT_EXACT3")
    projected: list[dict[str, object]] = []
    for row, expected in zip(rows, EXPECTED_EVENTS, strict=True):
        event_id, rank, pdb_id, component_label, component_auth_seq, component_occ, reported, recalculated, difference, protein_xyz, component_xyz = expected
        expected_fields = {
            "scaleup_rank": str(rank), "canonical_event_id": event_id,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID, "pdb_id": pdb_id,
            "model_number": "1", "protein_label_asym_id": "A",
            "protein_auth_asym_id": "A", "protein_label_comp_id": "CYS",
            "protein_auth_comp_id": "CYS", "protein_label_seq_id": "211",
            "protein_auth_seq_id": "217", "protein_insertion_code": "null",
            "protein_atom_id": "SG", "protein_altloc": "null", "protein_occupancy": "1.00",
            "component_label_asym_id": component_label, "component_auth_asym_id": "A",
            "component_label_comp_id": "EI3", "component_auth_comp_id": "EI3",
            "component_label_seq_id": "null", "component_auth_seq_id": str(component_auth_seq),
            "component_insertion_code": "null", "component_atom_id": "C1",
            "component_altloc": "null", "component_occupancy": component_occ,
            "connection_id": "covale1", "connection_type": "covale",
            "connection_value_order": "null", "protein_symmetry": "1_555",
            "component_symmetry": "1_555", "source_observed_pair": "SG:C1",
            "explicit_covalent_evidence": "true", "distance_only_event_inference_used": "false",
            "reported_distance_angstrom": reported, "recalculated_distance_angstrom": recalculated,
            "absolute_difference_angstrom": difference,
            "protein_x": protein_xyz[0], "protein_y": protein_xyz[1], "protein_z": protein_xyz[2],
            "component_x": component_xyz[0], "component_y": component_xyz[1], "component_z": component_xyz[2],
            "processing_pre_status": PRE_STATUS, "pre_source_graph_count": "0",
            "pre_source_graph_mapping_count": "0", "pre_geometry_authoritative": "false",
            "pre_geometry_training_target_available": "false",
            "post_geometry_source_evidence_available": "true",
            "post_geometry_sample_authoritative": "false",
            "post_geometry_training_target_available": "false", "target_event": "true",
            "human_selected": "false",
        }
        for key, value in expected_fields.items():
            if row[key] != value:
                _fail("EVENT_EVIDENCE_FIELD_DRIFT:" + event_id + ":" + key)
        datasets = _strict_json_cell(row["source_datasets_json"], event_id + ":datasets")
        records = _strict_json_cell(row["source_record_ids_json"], event_id + ":records")
        if datasets != ["SOURCE_COVPDB", "SOURCE_RCSB_PDB_DIRECT"]:
            _fail("EVENT_SOURCE_DATASETS_DRIFT:" + event_id)
        if type(records) is not list or len(records) != 2 or not records[1].endswith(":" + pdb_id + ":covale1"):
            _fail("EVENT_SOURCE_RECORDS_DRIFT:" + event_id)
        projected.append(
            {
                "canonical_event_id": event_id,
                "scaleup_rank": rank,
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
                "pdb_id": pdb_id,
                "model_number": 1,
                "protein_endpoint": {
                    "label_asym_id": "A", "auth_asym_id": "A", "label_comp_id": "CYS",
                    "label_seq_id": 211, "auth_seq_id": 217, "atom_id": "SG",
                    "occupancy_lexeme": "1.00", "coordinates_lexemes": list(protein_xyz),
                },
                "component_endpoint": {
                    "label_asym_id": component_label, "auth_asym_id": "A",
                    "label_comp_id": "EI3", "label_seq_id": None,
                    "auth_seq_id": component_auth_seq, "atom_id": "C1",
                    "occupancy_lexeme": component_occ, "coordinates_lexemes": list(component_xyz),
                },
                "connection_id": "covale1", "connection_type": "covale",
                "source_observed_pair": "SG:C1", "reported_distance_angstrom_lexeme": reported,
                "recalculated_distance_angstrom_lexeme": recalculated,
                "absolute_difference_angstrom_lexeme": difference,
                "source_datasets": datasets, "source_record_ids": records,
                "processing_pre_status": PRE_STATUS, "pre_source_graph_count": 0,
                "pre_source_graph_mapping_count": 0, "pre_geometry_authoritative": False,
                "pre_geometry_training_target_available": False,
                "post_geometry_source_evidence_available": True,
                "post_geometry_sample_authoritative": False,
                "post_geometry_training_target_available": False,
                "target_event": True, "evidence_human_selected": False,
            }
        )
    return projected


def _validate_graph_evidence(
    payload: bytes, events: list[dict[str, object]]
) -> dict[str, object]:
    graph = _strict_json(payload, "EI3_GRAPH_EVIDENCE")
    _expect_fields(
        graph,
        {
            "schema_version": "covapie_ei3_graph_and_review_evidence_v1",
            "stage": "EI3_REVIEW_PREPARATION_V1",
            "artifact_role": "FROZEN_EVIDENCE_REVIEW_AID_NOT_HUMAN_AUTHORITY",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "cache_payload_is_review_unit": False,
        },
        "GRAPH_ROOT",
    )
    _expect_exact(
        graph.get("target_scope"),
        {
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "current_pending_rank": 1,
            "ligand_component_id": "EI3",
            "pdb_ids": list(EXPECTED_PDB_IDS),
            "raw_priority_rank": 33,
            "scaleup_ranks": list(EXPECTED_RANKS),
            "source_observed_pair": "SG:C1",
            "target_event_count": 3,
        },
        "GRAPH_TARGET_SCOPE_DRIFT",
    )
    target_events = graph.get("target_events")
    if type(target_events) is not list or len(target_events) != 3:
        _fail("GRAPH_TARGET_EVENTS_NOT_EXACT3")
    for source, event, expected in zip(target_events, events, EXPECTED_EVENTS, strict=True):
        event_id, rank, pdb_id, component_label, component_auth_seq, component_occ, reported, recalculated, difference, protein_xyz, component_xyz = expected
        _expect_fields(
            source,
            {
                "canonical_event_id": event_id,
                "scaleup_rank": rank,
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
                "pdb_id": pdb_id,
                "model_number": 1,
                "connection_id": "covale1",
                "connection_type": "covale",
                "source_observed_pair": "SG:C1",
                "source_datasets": ["SOURCE_COVPDB", "SOURCE_RCSB_PDB_DIRECT"],
                "explicit_covalent_evidence": True,
                "distance_only_event_inference_used": False,
                "target_event": True,
                "supporting_context_only": False,
                "human_selected": False,
                "reported_distance_angstrom": float(reported),
                "recalculated_distance_angstrom": float(recalculated),
                "absolute_difference_angstrom": float(difference),
            },
            "GRAPH_TARGET_EVENT:" + event_id,
        )
        _expect_fields(
            source.get("protein_endpoint"),
            {
                "label_asym_id": "A", "auth_asym_id": "A", "label_seq_id": 211,
                "auth_seq_id": 217, "atom_id": "SG", "occupancy": 1.0,
                "coordinates": [float(value) for value in protein_xyz],
            },
            "GRAPH_PROTEIN_ENDPOINT:" + event_id,
        )
        _expect_fields(
            source.get("component_endpoint"),
            {
                "label_asym_id": component_label, "auth_asym_id": "A",
                "label_seq_id": None, "auth_seq_id": component_auth_seq,
                "atom_id": "C1", "occupancy": float(component_occ),
                "coordinates": [float(value) for value in component_xyz],
            },
            "GRAPH_COMPONENT_ENDPOINT:" + event_id,
        )
        pre = _path(source, "processing_observation.pre")
        _expect_fields(
            pre,
            {
                "pre_source_graph_count": 0,
                "pre_source_graph_mapping_count": 0,
                "pre_source_graph_mapping_status": PRE_MAPPING_STATUS,
                "status": PRE_STATUS,
            },
            "GRAPH_PRE_EVENT:" + event_id,
        )
        post = _path(source, "processing_observation.post")
        _expect_exact(
            post,
            {
                "full_coordinate_evidence_available": True,
                "sample_authoritative": False,
                "source_evidence_available": True,
                "training_target_available": False,
            },
            "GRAPH_POST_EVENT:" + event_id,
        )
        event["frozen_graph_target_event"] = source
    context = graph.get("additional_instance_connection_context")
    if type(context) is not list or [row.get("connection_id") for row in context] != ["metalc8", "metalc9"]:
        _fail("GRAPH_METAL_CONTEXT_EXACT2_DRIFT")
    for row in context:
        _expect_fields(
            row,
            {
                "authority_created": False,
                "canonical_event_id": None,
                "connection_type": "metalc",
                "context_classification": "STRUCTURE_EXTERNAL_CONNECTION_SUPPORTING_CONTEXT_ONLY",
                "human_selected": False,
                "model_number": 1,
                "pdb_id": "5ARD",
                "scaleup_rank": None,
                "supporting_context_only": True,
                "target_event": False,
            },
            "GRAPH_METAL_CONTEXT:" + str(row.get("connection_id")),
        )
        endpoints = (row.get("endpoint_1"), row.get("endpoint_2"))
        if not any(type(value) is dict and value.get("label_comp_id") == "NI" for value in endpoints):
            _fail("GRAPH_METAL_ENDPOINT_MISSING:" + str(row.get("connection_id")))
        if not any(type(value) is dict and value.get("label_comp_id") == "EI3" for value in endpoints):
            _fail("GRAPH_EI3_CONTEXT_ENDPOINT_MISSING:" + str(row.get("connection_id")))
    _expect_exact(
        graph.get("supporting_context_summary"),
        {
            "connection_count_by_pdb": METAL_COUNTS,
            "context_is_not_automatically_added_to_target_exact3": True,
            "total_supporting_context_connection_count": 2,
        },
        "GRAPH_SUPPORTING_CONTEXT_SUMMARY_DRIFT",
    )
    _expect_exact(
        graph.get("pre_post_observation_summary"),
        {
            "CCD_reference_graph_is_not_experimental_PRE_source_graph": True,
            "POST_full_coordinate_evidence_available_count": 3,
            "POST_sample_authoritative_count": 0,
            "POST_source_evidence_available_count": 3,
            "POST_to_PRE_copy_performed": False,
            "POST_training_target_available_count": 0,
            "PRE_geometry_authoritative_count": 0,
            "PRE_geometry_available_count": 0,
            "PRE_geometry_training_target_available_count": 0,
            "PRE_source_graph_count_per_event": [0, 0, 0],
            "PRE_source_graph_mapping_count_per_event": [0, 0, 0],
            "PRE_source_graph_mapping_status_per_event": [PRE_MAPPING_STATUS] * 3,
            "PRE_status_counts": {PRE_STATUS: 3},
            "PRE_zero_fill_performed": False,
            "target_event_count": 3,
            "unresolved_PRE_is_preserved_not_a_preparation_failure": True,
        },
        "GRAPH_PRE_POST_SUMMARY_DRIFT",
    )
    canonical = graph.get("canonical_Exact5")
    _expect_fields(
        canonical,
        {
            "B3_present": True,
            "sample_applicable_task_ids": None,
            "sixth_task_present": False,
            "task_count": 5,
        },
        "GRAPH_CANONICAL_EXACT5_DRIFT",
    )
    if [row.get("semantic_long_name") for row in canonical.get("tasks", [])] != [
        row[1] for row in CANONICAL_TASKS
    ]:
        _fail("GRAPH_CANONICAL_TASK_NAMES_DRIFT")
    mappings = graph.get("target_instance_atom_mappings")
    if type(mappings) is not list or len(mappings) != 3:
        _fail("GRAPH_INSTANCE_MAPPINGS_NOT_EXACT3")
    for mapping, expected in zip(mappings, EXPECTED_EVENTS, strict=True):
        _event_id, _rank, pdb_id, component_label, auth_seq, *_rest = expected
        _expect_fields(
            mapping,
            {
                "pdb_id": pdb_id,
                "component_label_asym_id": component_label,
                "component_auth_asym_id": "A",
                "component_auth_seq_id": auth_seq,
                "model_number": 1,
                "target_connection_ids": ["covale1"],
                "context_only_connection_ids": ["metalc8", "metalc9"] if pdb_id == "5ARD" else [],
                "exact_atom_id_mapping": True,
            },
            "GRAPH_INSTANCE_MAPPING:" + pdb_id,
        )
    ccd = graph.get("ccd_component_graph")
    if type(ccd) is not dict or ccd.get("component_metadata", {}).get("component_id") != "EI3":
        _fail("GRAPH_CCD_COMPONENT_DRIFT")
    atoms = ccd.get("full_atom_records")
    if type(atoms) is not list or any(row.get("element") == "NI" for row in atoms):
        _fail("GRAPH_NI_LEAKED_INTO_EI3_REFERENCE_COMPONENT")
    return {
        "target_graph_events": target_events,
        "metal_supporting_context": context,
        "target_instance_atom_mappings": mappings,
        "ccd_component_graph": ccd,
        "pre_post_observation_summary": graph["pre_post_observation_summary"],
        "target_scope": graph["target_scope"],
    }


def _literal_assignment(payload: bytes, name: str) -> object:
    try:
        tree = ast.parse(payload.decode("utf-8"), filename=name)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise EI3IngestionSafetyError(ERROR_PREFIX + ":CANONICAL_OWNER_AST_INVALID") from error
    found: list[object] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            try:
                found.append(ast.literal_eval(value))
            except (ValueError, TypeError) as error:
                raise EI3IngestionSafetyError(ERROR_PREFIX + ":CANONICAL_OWNER_LITERAL_INVALID") from error
    if found != [CANONICAL_TASKS]:
        _fail("CANONICAL_EXACT5_OWNER_DRIFT")
    return found[0]


def _generic_compatibility(repo_root: Path) -> dict[str, object]:
    generic = importlib.import_module(
        "covalent_ext.covapie_completed_human_decision_reconciliation_v1"
    )
    if Path(generic.__file__).resolve() != (repo_root / GENERIC_OWNER_RELATIVE).resolve():
        _fail("GENERIC_OWNER_IMPORT_PATH_DRIFT")
    binding = generic.SourceBinding(
        source_path=FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=FORMAL_BINDINGS[0][2],
        sha256=FORMAL_BINDINGS[0][3],
        schema_version=FORMAL_DECISION_SCHEMA,
        review_unit_id=EXPECTED_REVIEW_UNIT_ID,
    )
    generic._validate_source_binding(binding)
    facts: list[dict[str, object]] = []
    objects = []
    for event_id in EXPECTED_EVENT_IDS:
        fact = generic.NormalizedCompletedDecisionFact(
            canonical_event_id=event_id,
            review_unit_id=EXPECTED_REVIEW_UNIT_ID,
            human_review_completed=True,
            legacy_completed_review_status=EXPECTED_LEGACY_STATUS,
            task_relevance_disposition=NORMALIZED_TASK_RELEVANCE,
            chemistry_disposition="POSITIVE",
            training_disposition=NORMALIZED_TRAINING_DISPOSITION,
            human_training_excluded=False,
            source_decision_schema=FORMAL_DECISION_SCHEMA,
            source_decision_sha256=FORMAL_BINDINGS[0][3],
            source_binding_path=FORMAL_DECISION_RELATIVE.as_posix(),
        )
        generic._validate_fact(fact, binding)
        row = {field.name: getattr(fact, field.name) for field in fields(fact)}
        if tuple(row) != GENERIC_FACT_FIELDS:
            _fail("GENERIC_EXACT11_FIELD_ORDER_DRIFT")
        facts.append(row)
        objects.append(fact)
    source = generic.NormalizedDecisionSource(binding=binding, facts=tuple(objects))
    if type(source) is not generic.NormalizedDecisionSource or len(source.facts) != 3:
        _fail("GENERIC_NORMALIZED_SOURCE_INVALID")
    return {
        "generic_exact11_compatibility_pass": True,
        "generic_fact_field_count": 11,
        "generic_fact_fields": list(GENERIC_FACT_FIELDS),
        "accepted_fact_count": 3,
        "facts": facts,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "source_formal_D2": SOURCE_D2,
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "source_formal_D6": SOURCE_D6,
        "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "rich_fields_leaked": False,
        "NormalizedDecisionSource_constructed": True,
        "path_namespace_conversion": {
            "ingestion_binding_namespace": "project_parent_relative",
            "generic_binding_namespace": "repository_parent_relative",
            "stable_source_path": FORMAL_DECISION_RELATIVE.as_posix(),
            "strings_not_interchanged_without_explicit_conversion": True,
        },
        "reconciliation_performed": False,
    }


def _validate_current_census_and_queue(
    census_payload: bytes, queue_payload: bytes
) -> dict[str, object]:
    census_header, census_rows = _parse_csv(census_payload, "CURRENT_WITH_ME7_CENSUS")
    if "canonical_event_id" not in census_header:
        _fail("CENSUS_EVENT_COLUMN_MISSING")
    selected = [row for row in census_rows if row["canonical_event_id"] in EXPECTED_EVENT_IDS]
    if len(selected) != 3 or [row["canonical_event_id"] for row in selected] != list(EXPECTED_EVENT_IDS):
        _fail("CENSUS_EI3_EXACT3_DRIFT")
    for row in selected:
        expected = {
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "current_global_status": "CURRENTLY_UNREVIEWED",
            "current_review_status": "CURRENTLY_UNREVIEWED",
            "human_review_completed": "false",
            "chemistry_disposition": "UNRESOLVED",
            "task_relevance_disposition": "UNRESOLVED",
            "training_use_disposition": "UNRESOLVED",
            "reactive_pair_sample_authoritative": "false",
            "role_partition_sample_authoritative": "false",
            "canonical_mask_structural_labels_available": "false",
            "structurally_applicable_task_ids_json": "null",
        }
        for key, value in expected.items():
            if row.get(key) != value:
                _fail("CENSUS_PENDING_BOUNDARY_DRIFT:" + row["canonical_event_id"] + ":" + key)
    queue_header, queue_rows = _parse_csv(queue_payload, "FROZEN_PRIORITY_QUEUE")
    if "review_unit_id" not in queue_header:
        _fail("QUEUE_UNIT_COLUMN_MISSING")
    units = [row for row in queue_rows if row["review_unit_id"] == EXPECTED_REVIEW_UNIT_ID]
    if len(units) != 1:
        _fail("QUEUE_EI3_UNIT_DRIFT")
    queue = units[0]
    expected_queue = {
        "priority_rank": "33", "event_count": "3", "potential_event_yield_per_unit": "3",
        "human_decision_created": "false",
        "canonical_event_ids_json": _json_cell(list(EXPECTED_EVENT_IDS)),
        "pdb_ids_json": _json_cell(list(EXPECTED_PDB_IDS)),
        "ligand_component_ids_json": '["EI3"]',
    }
    for key, value in expected_queue.items():
        if queue.get(key) != value:
            _fail("QUEUE_PENDING_BOUNDARY_DRIFT:" + key)
    return {
        "EI3_event_count": 3,
        "EI3_current_global_status": "CURRENTLY_UNREVIEWED",
        "EI3_current_review_status": "CURRENTLY_UNREVIEWED",
        "EI3_human_review_completed": False,
        "EI3_structurally_applicable_task_ids": None,
        "EI3_current_pending_rank": 1,
        "EI3_raw_priority_rank": 33,
        "census_row_count": len(census_rows),
        "queue_row_count": len(queue_rows),
        "historical_pending_state_is_expected_until_refresh": True,
        "census_refresh_performed": False,
        "queue_refresh_performed": False,
    }


def _validate_formal_evidence_snapshot(
    formal: Mapping[str, Any], events: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    evidence = _path(
        formal,
        "frozen_candidate_evidence_snapshot.source_evidence_projection",
    )
    _expect_fields(
        evidence,
        {
            "frozen_scientific_JSON_SHA256": (
                "98ca106529bd27afd46714167e7af2a5c418f795244a48ce327c25911aae1d36"
            ),
            "projection_is_not_new_scientific_analysis": True,
        },
        "$.frozen_candidate_evidence_snapshot.source_evidence_projection",
    )
    event_validation = _path(
        formal,
        "frozen_candidate_evidence_snapshot.source_evidence_projection.event_validation",
    )
    _expect_fields(
        event_validation,
        {
            "covalent_and_metal_context_distinguished": True,
            "external_connection_count_by_pdb": {"5ARB": 1, "5ARC": 1, "5ARD": 3},
            "metal_context_connection_count_by_pdb": METAL_COUNTS,
            "metal_context_promoted_to_target_event": False,
            "supporting_context_connection_count": 2,
            "target_connection_type": "covale",
            "target_covalent_connection_count_by_pdb": TARGET_COUNTS,
            "target_event_count": 3,
        },
        "FORMAL_EVIDENCE_EVENT_VALIDATION_DRIFT",
    )
    formal_events = event_validation.get("target_events")
    if type(formal_events) is not list or len(formal_events) != 3:
        _fail("FORMAL_EVIDENCE_TARGET_EVENTS_NOT_EXACT3")
    for source, event in zip(formal_events, events, strict=True):
        event_id = str(event["canonical_event_id"])
        _expect_fields(
            source,
            {
                "canonical_event_id": event_id,
                "scaleup_rank": event["scaleup_rank"],
                "pdb_id": event["pdb_id"],
                "model_number": 1,
                "connection_id": "covale1",
                "connection_type": "covale",
                "source_observed_pair": "SG:C1",
                "source_datasets": ["SOURCE_COVPDB", "SOURCE_RCSB_PDB_DIRECT"],
                "explicit_covalent_evidence": True,
                "distance_only_inference_used": False,
            },
            "FORMAL_EVIDENCE_TARGET_EVENT:" + event_id,
        )
        _expect_fields(
            source.get("protein_endpoint"),
            {
                "label_asym_id": "A", "auth_asym_id": "A", "auth_seq_id": 217,
                "atom_id": "SG", "occupancy": 1.0,
            },
            "FORMAL_EVIDENCE_PROTEIN_ENDPOINT:" + event_id,
        )
        _expect_fields(
            source.get("component_endpoint"),
            {
                "label_asym_id": event["component_endpoint"]["label_asym_id"],
                "auth_asym_id": "A",
                "auth_seq_id": event["component_endpoint"]["auth_seq_id"],
                "atom_id": "C1",
                "occupancy": float(event["component_endpoint"]["occupancy_lexeme"]),
            },
            "FORMAL_EVIDENCE_COMPONENT_ENDPOINT:" + event_id,
        )
    context = event_validation.get("supporting_context_connections")
    if type(context) is not list or [row.get("connection_id") for row in context] != ["metalc8", "metalc9"]:
        _fail("FORMAL_EVIDENCE_METAL_CONTEXT_DRIFT")
    if any(
        row.get("pdb_id") != "5ARD"
        or row.get("canonical_event_id") is not None
        or row.get("connection_type") != "metalc"
        or row.get("supporting_context_only") is not True
        or row.get("target_event") is not False
        for row in context
    ):
        _fail("FORMAL_EVIDENCE_METAL_CONTEXT_PROMOTED")
    pre = evidence.get("PRE_boundary")
    _expect_fields(
        pre,
        {
            "POST_to_PRE_copy": False,
            "PRE_authority_created": False,
            "PRE_coordinates_created": False,
            "PRE_geometry_authoritative_count": 0,
            "PRE_source_graph_count_per_event": [0, 0, 0],
            "PRE_source_graph_mapping_count_per_event": [0, 0, 0],
            "PRE_source_graph_mapping_status_per_event": [PRE_MAPPING_STATUS] * 3,
            "PRE_status_per_event": [PRE_STATUS] * 3,
            "PRE_topology_created": False,
            "PRE_zero_fill": False,
            "accurate_PRE_required_before_training_feature_contract": False,
        },
        "FORMAL_EVIDENCE_PRE_DRIFT",
    )
    metadata = evidence.get("source_metadata_analysis")
    if type(metadata) is not dict or metadata.get("record_count") != 3:
        _fail("FORMAL_SOURCE_METADATA_RECORD_COUNT_DRIFT")
    records = metadata.get("records")
    if type(records) is not list or [row.get("pdb_id") for row in records] != list(EXPECTED_PDB_IDS):
        _fail("FORMAL_SOURCE_METADATA_PDB_DRIFT")
    entity_ids = {"5ARB": "4", "5ARC": "3", "5ARD": "4"}
    entity_locators: list[dict[str, object]] = []
    for record, expected in zip(records, EXPECTED_EVENTS, strict=True):
        _event_id, _rank, pdb_id, component_label, *_rest = expected
        mapping = record.get("related_entity_mapping")
        _expect_exact(
            mapping,
            {
                "component_entity_id": entity_ids[pdb_id],
                "component_label_asym_id": component_label,
                "mapping_category": "_struct_asym",
                "mapping_record_locators": ["id=A", "id=" + component_label],
                "protein_entity_id": "1",
                "protein_label_asym_id": "A",
            },
            "FORMAL_ENTITY_MAPPING:" + pdb_id,
        )
        field_evidence = record.get("field_evidence")
        component_fields = [
            row for row in field_evidence
            if row.get("evidence_id") in {pdb_id + ":EI3.description", pdb_id + ":EI3.mutation"}
        ] if type(field_evidence) is list else []
        if len(component_fields) != 2 or any(
            row.get("category") != "_entity" or row.get("record_locator") != "id=" + entity_ids[pdb_id]
            for row in component_fields
        ):
            _fail("FORMAL_ENTITY_DESCRIPTION_MUTATION_LOCATOR_DRIFT:" + pdb_id)
        entity_locators.append(
            {
                "pdb_id": pdb_id,
                "struct_asym_mapping": mapping,
                "component_entity_description_and_mutation": component_fields,
            }
        )
    return {
        "source_evidence_projection": evidence,
        "entity_locator_projection": entity_locators,
    }


def schema_preflight_v1(formal: Mapping[str, Any]) -> dict[str, object]:
    """Report the real EI3 schema paths consumed by this stage."""
    _validate_formal(formal)
    paths = [
        "$.sample_identity.review_unit_id",
        "$.sample_identity.scaleup_ranks",
        "$.sample_identity.canonical_target_event_ids",
        "$.sample_identity.pdb_ids",
        "$.sample_level_authority.sample_observed_pair_authority",
        "$.approved_D1_D6.D1_observed_covalent_chemistry",
        "$.approved_D1_D6.D2_task_generation_domain_relevance",
        "$.approved_D1_D6.D3_reactive_atom_pair_confirmation_or_revision",
        "$.approved_D1_D6.D4_role_partition_and_minimal_seed",
        "$.approved_D1_D6.D5_structural_task_applicability",
        "$.approved_D1_D6.D6_later_training_use_disposition",
        "$.PRE_boundary.frozen_source_projection.PRE_source_graph_count_per_event",
        "$.PRE_boundary.frozen_source_projection.PRE_source_graph_mapping_count_per_event",
        "$.PRE_boundary.frozen_source_projection.PRE_source_graph_mapping_status_per_event",
        "$.PRE_boundary.frozen_source_projection.PRE_status_per_event",
        "$.role_and_task_disposition",
        "$.authorization_record",
        "$.frozen_candidate_binding",
        "$.frozen_candidate_evidence_snapshot.source_evidence_projection",
        "$.frozen_candidate_evidence_snapshot.source_machine_proposals",
        "$.non_created_authority",
        "$.readiness",
    ]
    return {
        "status": "PASS",
        "formal_schema": formal["schema_version"],
        "formal_stage": formal["stage"],
        "formal_record_role": formal["record_role"],
        "actual_consumed_paths": paths,
        "actual_consumed_path_count": len(paths),
        "uses_sample_observed_pair_authority": True,
        "uses_ME7_sample_pair_authority": False,
        "uses_nested_PRE_frozen_source_projection": True,
        "uses_ME7_top_level_PRE_source_mapping_count_per_event": False,
    }


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Bind sources and independently validate frozen EI3 authority."""
    root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    payloads = _verify_bindings(root, overrides)
    formal = _strict_json(payloads[FORMAL_DECISION_RELATIVE], "EI3_FORMAL_DECISION")
    preflight = schema_preflight_v1(formal)
    events = _validate_event_evidence(payloads[EVENT_EVIDENCE_RELATIVE])
    graph = _validate_graph_evidence(payloads[GRAPH_EVIDENCE_RELATIVE], events)
    formal_evidence = _validate_formal_evidence_snapshot(formal, events)
    _literal_assignment(payloads[CANONICAL_TASK_OWNER_RELATIVE], "CANONICAL_TASKS")
    generic = _generic_compatibility(root)
    current = _validate_current_census_and_queue(
        payloads[CENSUS_MATRIX_RELATIVE], payloads[PRIORITY_QUEUE_RELATIVE]
    )
    return {
        "formal_document": formal,
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "active_source_bindings": [_binding_record(binding) for binding in ACTIVE_BINDINGS],
        "active_source_binding_count": 9,
        "formal_internal_source_bindings": _formal_source_rows(),
        "formal_internal_source_binding_count": 10,
        "schema_preflight": preflight,
        "events": events,
        **graph,
        **formal_evidence,
        "generic_Exact11_compatibility": generic,
        "current_census_and_queue_boundary": current,
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
                "human_applicability": None,
                "structurally_applicable": None,
                "authority_created": False,
            }
            for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task": False,
        "role_profile": None,
        "sample_applicable_task_ids": None,
        "task_applicability_determined": False,
        "task_applicability_sample_authority": False,
        "canonical_mask_structural_labels_available": False,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "mask_tensor_targets_created": False,
        "task_label_authority": False,
        "training_mask_targets_available_now": False,
    }


def _operation_boundary() -> dict[str, object]:
    return {
        "formal_source_modified": False,
        "candidate_modified": False,
        "preparation_modified": False,
        "scientific_modified": False,
        "new_human_authority_created": False,
        "new_formal_authority_created": False,
        "new_reusable_authority_created": False,
        "role_runtime_executed": False,
        "seed_runtime_executed": False,
        "task_runtime_executed": False,
        "event_task_label_rows_materialized": False,
        "mask_tensor_targets_created": False,
        "reconciliation_performed": False,
        "census_refresh_performed": False,
        "queue_refresh_performed": False,
        "next_review_started": False,
        "training_preparation_performed": False,
        "training_performed": False,
        "parameter_update_performed": False,
        "network_acquisition_performed": False,
        "commit_performed": False,
        "push_performed": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "chemistry_disposition": "POSITIVE",
        "negative_chemistry": False,
        "task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "human_training_excluded": False,
        "future_training_admission_candidate": False,
        "formal_training_admitted": False,
        "training_materialization_allowed": False,
        "task_label_authority": False,
        "event_task_label_rows_materialized": False,
        "mask_tensor_targets_created": False,
        "ready_for_training": False,
        "training_started": False,
    }


def _readiness() -> dict[str, object]:
    return {
        "HUMAN_REVIEW_COMPLETED": True,
        "PAIR_SAMPLE_AUTHORITY": True,
        "ROLE_PARTITION_SAMPLE_AUTHORITATIVE": False,
        "MINIMAL_SEED_SAMPLE_AUTHORITATIVE": False,
        "TASK_APPLICABILITY_SAMPLE_AUTHORITATIVE": False,
        "TASK_LABEL_AUTHORITY": False,
        "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "MASK_TENSOR_TARGETS_CREATED": False,
        "FORMAL_TRAINING_ADMITTED": False,
        "TRAINING_MATERIALIZATION_ALLOWED": False,
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
        "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
        "remaining_readiness_blockers": [
            "ROLE_PARTITION_SAMPLE_AUTHORITY_NOT_CREATED",
            "TASK_APPLICABILITY_SAMPLE_AUTHORITY_NOT_CREATED",
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING",
            "NO_FORMAL_TRAINING_ADMISSION",
        ],
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    formal = bound["formal_document"]
    role = formal["role_and_task_disposition"]
    events = []
    for event in bound["events"]:
        row = dict(event)
        pdb_id = row["pdb_id"]
        row.update(
            {
                "human_review_completed": True,
                "completed_lane": EXPECTED_COMPLETED_LANE,
                "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
                "source_formal_D1": "POSITIVE",
                "chemistry_disposition": "POSITIVE",
                "negative_chemistry": False,
                "source_formal_D2": SOURCE_D2,
                "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
                "task_domain_negative": True,
                "source_formal_D3": "CONFIRM_OBSERVED_PAIR",
                "pair_sample_authority": True,
                "target_covalent_connection_count": TARGET_COUNTS[pdb_id],
                "metal_context_connection_count": METAL_COUNTS[pdb_id],
                "source_formal_D4": "CANNOT_DETERMINE",
                "D4_formally_answered": True,
                "source_formal_D5": "NOT_DETERMINABLE",
                "D5_formally_answered": True,
                "source_formal_D6": SOURCE_D6,
                "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
                "human_training_excluded": False,
                "future_training_admission_candidate": False,
                "formal_training_admitted": False,
                "training_materialization_allowed": False,
            }
        )
        events.append(row)
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": "EI3_COMPLETED_DECISION_INGESTION_V1",
        "artifact_role": "PROJECTION_OF_FROZEN_FORMAL_HUMAN_AUTHORITY",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "sample_identity": formal["sample_identity"],
        "formal_source_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "active_source_bindings": bound["active_source_bindings"],
        "active_source_binding_count": 9,
        "formal_internal_source_chain": {
            "path_namespace": "review_unit_relative",
            "source_binding_count": 10,
            "source_bindings": bound["formal_internal_source_bindings"],
            "distinct_from_ingestion_active_bindings": True,
        },
        "schema_preflight": bound["schema_preflight"],
        "authorization_record": formal["authorization_record"],
        "approved_D1_D6": formal["approved_D1_D6"],
        "sample_level_authority": formal["sample_level_authority"],
        "role_and_task_disposition": formal["role_and_task_disposition"],
        "normalization": {
            "source_D2": SOURCE_D2,
            "normalized_task_relevance": NORMALIZED_TASK_RELEVANCE,
            "source_D6": SOURCE_D6,
            "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "chemistry_disposition": "POSITIVE",
            "negative_chemistry": False,
        },
        "events": events,
        "event_count": 3,
        "covalent_and_metal_context_boundary": {
            **formal["event_context_boundary"],
            "metal_supporting_context_records": bound["metal_supporting_context"],
            "metal_context_is_not_generic_fact": True,
            "metal_context_is_not_pair_or_geometry_authority": True,
        },
        "frozen_candidate_evidence_snapshot": formal[
            "frozen_candidate_evidence_snapshot"
        ],
        "entity_locator_projection": bound["entity_locator_projection"],
        "target_instance_atom_mappings": bound["target_instance_atom_mappings"],
        "ccd_component_graph": bound["ccd_component_graph"],
        "PRE_boundary": {
            **formal["PRE_boundary"],
            "graph_pre_post_observation_summary": bound[
                "pre_post_observation_summary"
            ],
        },
        "canonical_task_contract": _canonical_task_contract(),
        "generic_Exact11_compatibility": bound["generic_Exact11_compatibility"],
        "current_with_ME7_census_and_queue_preingestion_boundary": bound[
            "current_census_and_queue_boundary"
        ],
        "historical_source_snapshot_human_authority_false_does_not_override_formal": True,
        "operation_boundary": _operation_boundary(),
        "training_boundary": _training_boundary(),
        "readiness": _readiness(),
    }


MATRIX_HEADER = (
    "artifact_role", "canonical_event_id", "scaleup_rank", "review_unit_id", "pdb_id",
    "protein_label_asym_id", "component_label_asym_id", "component_auth_asym_id",
    "connection_id", "source_observed_pair",
    "reported_distance_angstrom", "recalculated_distance_angstrom",
    "absolute_difference_angstrom", "protein_coordinates_json", "component_coordinates_json",
    "source_datasets_json",
    "source_record_ids_json", "evidence_human_selected", "human_review_completed",
    "D4_formally_answered", "D5_formally_answered", "completed_lane",
    "legacy_completed_review_status", "source_formal_D1", "chemistry_disposition",
    "negative_chemistry", "source_formal_D2", "normalized_task_relevance_disposition",
    "task_domain_negative", "source_formal_D3", "pair_sample_authority",
    "target_covalent_connection_count", "metal_context_connection_count",
    "source_formal_D4", "D4_source_proposal_field", "role_candidate_count",
    "selected_role_candidate_json",
    "role_profile_raw_json", "role_profile_derived_state", "warhead_atom_ids_json",
    "linker_atom_ids_json", "scaffold_atom_ids_json", "minimal_seed_json",
    "minimal_seed_atom_ids_json", "primary_anchor_json", "role_partition_sample_authoritative",
    "minimal_seed_sample_authoritative", "role_runtime_executed", "seed_runtime_executed",
    "source_formal_D5", "structurally_applicable_task_ids_json",
    "task_applicability_sample_authoritative", "task_runtime_executed",
    "canonical_task_count", "B3_present", "sixth_task",
    "canonical_mask_structural_labels_available", "task_label_authority",
    "event_task_label_rows_materialized", "mask_tensor_targets_created", "source_formal_D6",
    "training_disposition", "human_training_excluded", "future_training_admission_candidate",
    "formal_training_admitted", "training_materialization_allowed",
    "POST_source_evidence_available", "POST_sample_geometry_authority",
    "POST_geometry_training_authority", "PRE_source_graph_count", "PRE_source_mapping_count",
    "PRE_source_graph_mapping_status", "PRE_mapping_auto_selected", "PRE_authority",
    "POST_to_PRE_copy", "PRE_zero_fill", "accurate_PRE_required_before_training_feature_contract",
    "FEATURE_SEMANTICS_AUDIT_PERFORMED", "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING",
    "READY_FOR_TRAINING", "TRAINING_STARTED",
)
MATRIX_JSON_COLUMNS = frozenset(
    {
        "protein_coordinates_json", "component_coordinates_json", "source_datasets_json",
        "source_record_ids_json", "selected_role_candidate_json", "role_profile_raw_json",
        "warhead_atom_ids_json", "linker_atom_ids_json", "scaffold_atom_ids_json",
        "minimal_seed_json", "minimal_seed_atom_ids_json", "primary_anchor_json",
        "structurally_applicable_task_ids_json",
    }
)
MATRIX_INTEGER_COLUMNS = frozenset(
    {
        "scaleup_rank", "target_covalent_connection_count", "metal_context_connection_count",
        "role_candidate_count", "canonical_task_count", "PRE_source_graph_count",
        "PRE_source_mapping_count",
    }
)
MATRIX_BOOLEAN_COLUMNS = frozenset(set(MATRIX_HEADER) - MATRIX_JSON_COLUMNS - MATRIX_INTEGER_COLUMNS - {
    "artifact_role", "canonical_event_id", "review_unit_id", "pdb_id",
    "protein_label_asym_id", "component_label_asym_id",
    "component_auth_asym_id", "connection_id", "source_observed_pair",
    "reported_distance_angstrom", "recalculated_distance_angstrom",
    "absolute_difference_angstrom",
    "completed_lane", "legacy_completed_review_status", "source_formal_D1",
    "chemistry_disposition", "source_formal_D2", "normalized_task_relevance_disposition",
    "source_formal_D3", "source_formal_D4", "D4_source_proposal_field",
    "role_profile_derived_state",
    "source_formal_D5", "source_formal_D6", "training_disposition",
    "PRE_source_graph_mapping_status",
})


def _matrix_column_types() -> list[dict[str, str]]:
    result = []
    for column in MATRIX_HEADER:
        if column in MATRIX_JSON_COLUMNS:
            value_type = "canonical_json"
        elif column in MATRIX_INTEGER_COLUMNS:
            value_type = "integer"
        elif column in MATRIX_BOOLEAN_COLUMNS:
            value_type = "boolean"
        else:
            value_type = "string"
        result.append({"column": column, "value_type": value_type})
    return result


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    rows = []
    for event in snapshot["events"]:
        protein = event["protein_endpoint"]
        component = event["component_endpoint"]
        rows.append(
            {
                "artifact_role": "TASK_LABEL_AVAILABILITY_METADATA_ONLY_NOT_LABEL_ROWS",
                "canonical_event_id": event["canonical_event_id"],
                "scaleup_rank": event["scaleup_rank"],
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
                "pdb_id": event["pdb_id"],
                "protein_label_asym_id": protein["label_asym_id"],
                "component_label_asym_id": component["label_asym_id"],
                "component_auth_asym_id": component["auth_asym_id"],
                "connection_id": event["connection_id"],
                "source_observed_pair": "SG:C1",
                "reported_distance_angstrom": event["reported_distance_angstrom_lexeme"],
                "recalculated_distance_angstrom": event["recalculated_distance_angstrom_lexeme"],
                "absolute_difference_angstrom": event["absolute_difference_angstrom_lexeme"],
                "protein_coordinates_json": _json_cell(protein["coordinates_lexemes"]),
                "component_coordinates_json": _json_cell(component["coordinates_lexemes"]),
                "source_datasets_json": _json_cell(event["source_datasets"]),
                "source_record_ids_json": _json_cell(event["source_record_ids"]),
                "evidence_human_selected": "false", "human_review_completed": "true",
                "D4_formally_answered": "true", "D5_formally_answered": "true",
                "completed_lane": EXPECTED_COMPLETED_LANE,
                "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
                "source_formal_D1": "POSITIVE", "chemistry_disposition": "POSITIVE",
                "negative_chemistry": "false", "source_formal_D2": SOURCE_D2,
                "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
                "task_domain_negative": "true", "source_formal_D3": "CONFIRM_OBSERVED_PAIR",
                "pair_sample_authority": "true",
                "target_covalent_connection_count": event["target_covalent_connection_count"],
                "metal_context_connection_count": event["metal_context_connection_count"],
                "source_formal_D4": "CANNOT_DETERMINE",
                "D4_source_proposal_field": "D4_role_partition_and_minimal_seed",
                "role_candidate_count": 0,
                "selected_role_candidate_json": "null", "role_profile_raw_json": "null",
                "role_profile_derived_state": "NOT_ESTABLISHED", "warhead_atom_ids_json": "null",
                "linker_atom_ids_json": "null", "scaffold_atom_ids_json": "null",
                "minimal_seed_json": "null", "minimal_seed_atom_ids_json": "null",
                "primary_anchor_json": "null", "role_partition_sample_authoritative": "false",
                "minimal_seed_sample_authoritative": "false", "role_runtime_executed": "false",
                "seed_runtime_executed": "false", "source_formal_D5": "NOT_DETERMINABLE",
                "structurally_applicable_task_ids_json": "null",
                "task_applicability_sample_authoritative": "false",
                "task_runtime_executed": "false", "canonical_task_count": 5,
                "B3_present": "true", "sixth_task": "false",
                "canonical_mask_structural_labels_available": "false",
                "task_label_authority": "false", "event_task_label_rows_materialized": "false",
                "mask_tensor_targets_created": "false", "source_formal_D6": SOURCE_D6,
                "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
                "human_training_excluded": "false", "future_training_admission_candidate": "false",
                "formal_training_admitted": "false", "training_materialization_allowed": "false",
                "POST_source_evidence_available": "true", "POST_sample_geometry_authority": "false",
                "POST_geometry_training_authority": "false", "PRE_source_graph_count": 0,
                "PRE_source_mapping_count": 0,
                "PRE_source_graph_mapping_status": PRE_MAPPING_STATUS,
                "PRE_mapping_auto_selected": "false", "PRE_authority": "false",
                "POST_to_PRE_copy": "false", "PRE_zero_fill": "false",
                "accurate_PRE_required_before_training_feature_contract": "false",
                "FEATURE_SEMANTICS_AUDIT_PERFORMED": "false",
                "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": "true",
                "READY_FOR_TRAINING": "false", "TRAINING_STARTED": "false",
            }
        )
    return rows


def _summary(snapshot: Mapping[str, Any]) -> dict[str, object]:
    rows = _matrix_rows(snapshot)

    def count(column: str, value: object) -> int:
        expected = _bool(value) if type(value) is bool else value
        return sum(row[column] == expected for row in rows)

    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": "EI3_COMPLETED_DECISION_INGESTION_V1",
        "artifact_role": "COUNTS_COMPUTED_FROM_EXACT3_AVAILABILITY_METADATA",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": len(rows),
        "human_review_completed_count": count("human_review_completed", True),
        "chemistry_positive_count": count("chemistry_disposition", "POSITIVE"),
        "negative_chemistry_count": count("negative_chemistry", True),
        "task_not_relevant_count": count(
            "normalized_task_relevance_disposition", NORMALIZED_TASK_RELEVANCE
        ),
        "training_not_applicable_count": count(
            "training_disposition", NORMALIZED_TRAINING_DISPOSITION
        ),
        "pair_sample_authority_count": count("pair_sample_authority", True),
        "role_partition_sample_authority_count": count(
            "role_partition_sample_authoritative", True
        ),
        "minimal_seed_sample_authority_count": count(
            "minimal_seed_sample_authoritative", True
        ),
        "task_applicability_sample_authority_count": count(
            "task_applicability_sample_authoritative", True
        ),
        "role_candidate_count": sum(int(row["role_candidate_count"]) for row in rows),
        "role_runtime_execution_count": count("role_runtime_executed", True),
        "seed_runtime_execution_count": count("seed_runtime_executed", True),
        "task_runtime_execution_count": count("task_runtime_executed", True),
        "generic_exact11_fact_count": len(
            snapshot["generic_Exact11_compatibility"]["facts"]
        ),
        "generic_exact11_field_count": snapshot[
            "generic_Exact11_compatibility"
        ]["generic_fact_field_count"],
        "rich_fields_leaked_to_generic_facts": False,
        "human_training_excluded_count": count("human_training_excluded", True),
        "future_training_admission_candidate_count": count(
            "future_training_admission_candidate", True
        ),
        "formal_training_admitted_count": count("formal_training_admitted", True),
        "training_materialization_allowed_count": count(
            "training_materialization_allowed", True
        ),
        "task_label_authority_count": count("task_label_authority", True),
        "event_task_label_rows_materialized_count": count(
            "event_task_label_rows_materialized", True
        ),
        "mask_tensor_targets_created_count": count("mask_tensor_targets_created", True),
        "canonical_structural_label_available_count": count(
            "canonical_mask_structural_labels_available", True
        ),
        "target_covalent_connection_count": sum(
            int(row["target_covalent_connection_count"]) for row in rows
        ),
        "metal_context_connection_count": sum(
            int(row["metal_context_connection_count"]) for row in rows
        ),
        "operation_boundary": _operation_boundary(),
        "training_boundary": _training_boundary(),
        "readiness": _readiness(),
    }


def _candidate_source_records(repo_root: Path) -> list[dict[str, object]]:
    records = []
    for relative in (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE):
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise EI3IngestionSafetyError(
                ERROR_PREFIX + ":CANDIDATE_SOURCE_READ_FAILED:" + relative.as_posix()
            ) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("CANDIDATE_SOURCE_CLASS_INVALID:" + relative.as_posix())
        if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            _fail("CANDIDATE_SOURCE_EXECUTABLE:" + relative.as_posix())
        records.append(
            {
                "path": relative.as_posix(),
                "path_namespace": "repository_relative",
                "byte_count": len(payload),
                "SHA256": _sha256(payload),
                "expected_path_class": "REGULAR_NON_SYMLINK",
                "expected_executable_class": "NON_EXECUTABLE",
            }
        )
    return records


def _output_binding(name: str, payload: bytes) -> dict[str, object]:
    return {
        "path": (OUTPUT_ROOT_RELATIVE / name).as_posix(),
        "path_namespace": "repository_relative",
        "byte_count": len(payload),
        "SHA256": _sha256(payload),
    }


def _manifest(
    repo_root: Path,
    bound: Mapping[str, object],
    snapshot_bytes: bytes,
    matrix_bytes: bytes,
    summary_bytes: bytes,
) -> dict[str, object]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": "EI3_COMPLETED_DECISION_INGESTION_V1",
        "artifact_role": "DETERMINISTIC_SOURCE_CODE_AND_OUTPUT_BINDING_NO_SELF_HASH",
        "baseline_commit": BASELINE_COMMIT,
        "output_inventory": {
            "file_count": 4,
            "files": list(OUTPUT_FILENAMES),
            "directory": OUTPUT_ROOT_RELATIVE.as_posix(),
            "directory_exact4": True,
            "manifest_self_SHA256_recorded": False,
        },
        "serialization_contract": {
            "encoding": "UTF-8",
            "line_endings": "LF",
            "single_terminal_LF": True,
            "json_serialization": "canonical_compact_json",
            "csv_header": list(MATRIX_HEADER),
            "csv_column_count": len(MATRIX_HEADER),
            "csv_column_types": _matrix_column_types(),
            "nullable_json_literal": "null",
        },
        "candidate_source_bindings": _candidate_source_records(repo_root),
        "output_artifact_bindings_excluding_manifest_self": [
            _output_binding(SNAPSHOT, snapshot_bytes),
            _output_binding(MATRIX, matrix_bytes),
            _output_binding(SUMMARY, summary_bytes),
        ],
        "active_source_binding_count": 9,
        "formal_internal_source_binding_count": 10,
        "duplicate_source_binding_identity_count": 0,
        "active_source_bindings": bound["active_source_bindings"],
        "formal_internal_source_bindings": bound["formal_internal_source_bindings"],
        "formal_source_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "source_binding_namespace_contract": {
            "state_inputs": "project_parent_relative",
            "repository_inputs": "repository_relative",
            "formal_internal_chain": "review_unit_relative",
            "generic_projection": "repository_parent_relative",
            "namespace_strings_not_interchangeable": True,
        },
        "schema_preflight": bound["schema_preflight"],
        "normalization": {
            "source_D2": SOURCE_D2,
            "normalized_task_relevance": NORMALIZED_TASK_RELEVANCE,
            "source_D6": SOURCE_D6,
            "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        },
        "generic_Exact11_compatibility": bound["generic_Exact11_compatibility"],
        "canonical_task_contract": _canonical_task_contract(),
        "current_census_and_queue_boundary": bound[
            "current_census_and_queue_boundary"
        ],
        "operation_boundary": _operation_boundary(),
        "training_boundary": _training_boundary(),
        "readiness": _readiness(),
    }


def _build_raw(
    repo_root: Path,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    bound = load_frozen_formal_decision_v1(
        repo_root, repository_path_overrides=repository_path_overrides
    )
    snapshot = _snapshot(bound)
    snapshot_bytes = _json_bytes(snapshot)
    matrix_bytes = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    summary_bytes = _json_bytes(_summary(snapshot))
    manifest_bytes = _json_bytes(
        _manifest(repo_root, bound, snapshot_bytes, matrix_bytes, summary_bytes)
    )
    return {
        SNAPSHOT: snapshot_bytes,
        MATRIX: matrix_bytes,
        SUMMARY: summary_bytes,
        MANIFEST: manifest_bytes,
    }


def _validate_text_payload(name: str, payload: bytes) -> None:
    if (
        payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail("OUTPUT_TEXT_INVARIANT_INVALID:" + name)
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise EI3IngestionSafetyError(
            ERROR_PREFIX + ":OUTPUT_UTF8_INVALID:" + name
        ) from error


def _validate_snapshot_semantics(snapshot: Mapping[str, Any]) -> None:
    _expect_fields(
        snapshot,
        {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "stage": "EI3_COMPLETED_DECISION_INGESTION_V1",
            "artifact_role": "PROJECTION_OF_FROZEN_FORMAL_HUMAN_AUTHORITY",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "event_count": 3,
            "active_source_binding_count": 9,
            "historical_source_snapshot_human_authority_false_does_not_override_formal": True,
            "operation_boundary": _operation_boundary(),
            "training_boundary": _training_boundary(),
            "readiness": _readiness(),
        },
        "SNAPSHOT_ROOT_DRIFT",
    )
    sample_authority = snapshot.get("sample_level_authority")
    _expect_fields(
        sample_authority,
        {
            "human_review_completed": True,
            "sample_observed_pair_authority": True,
            "role_partition_sample_authoritative": False,
            "minimal_seed_sample_authoritative": False,
            "task_applicability_sample_authoritative": False,
        },
        "SNAPSHOT_AUTHORITY_DRIFT",
    )
    role = snapshot.get("role_and_task_disposition")
    for key in (
        "applicable_task_ids", "linker_atom_ids", "minimal_seed", "minimal_seed_atom_ids",
        "primary_anchor", "role_partitions", "role_profile", "scaffold_atom_ids",
        "selected_candidate_id", "selected_role_candidate", "warhead_atom_ids",
    ):
        if type(role) is not dict or role.get(key, object()) is not None:
            _fail("SNAPSHOT_ROLE_TASK_NULL_DRIFT:" + key)
    events = snapshot.get("events")
    if type(events) is not list or [row.get("canonical_event_id") for row in events] != list(EXPECTED_EVENT_IDS):
        _fail("SNAPSHOT_EVENTS_NOT_EXACT3")
    for row, expected in zip(events, EXPECTED_EVENTS, strict=True):
        event_id, _rank, pdb_id, *_rest = expected
        _expect_fields(
            row,
            {
                "canonical_event_id": event_id,
                "human_review_completed": True,
                "completed_lane": EXPECTED_COMPLETED_LANE,
                "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
                "source_formal_D1": "POSITIVE",
                "chemistry_disposition": "POSITIVE",
                "negative_chemistry": False,
                "source_formal_D2": SOURCE_D2,
                "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
                "task_domain_negative": True,
                "source_formal_D3": "CONFIRM_OBSERVED_PAIR",
                "pair_sample_authority": True,
                "target_covalent_connection_count": 1,
                "metal_context_connection_count": METAL_COUNTS[pdb_id],
                "source_formal_D4": "CANNOT_DETERMINE",
                "D4_formally_answered": True,
                "source_formal_D5": "NOT_DETERMINABLE",
                "D5_formally_answered": True,
                "source_formal_D6": SOURCE_D6,
                "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
                "human_training_excluded": False,
                "future_training_admission_candidate": False,
                "formal_training_admitted": False,
                "training_materialization_allowed": False,
                "evidence_human_selected": False,
                "post_geometry_sample_authoritative": False,
                "post_geometry_training_target_available": False,
                "pre_geometry_authoritative": False,
                "pre_geometry_training_target_available": False,
            },
            "SNAPSHOT_EVENT_DRIFT:" + event_id,
        )
    generic = snapshot.get("generic_Exact11_compatibility")
    _expect_fields(
        generic,
        {
            "generic_exact11_compatibility_pass": True,
            "generic_fact_field_count": 11,
            "accepted_fact_count": 3,
            "rich_fields_leaked": False,
        },
        "SNAPSHOT_GENERIC_DRIFT",
    )
    facts = generic.get("facts") if type(generic) is dict else None
    if type(facts) is not list or len(facts) != 3:
        _fail("SNAPSHOT_GENERIC_FACT_COUNT_DRIFT")
    rich = {
        "role_profile", "coordinates", "occupancy", "source_datasets", "source_record_ids",
        "pair_sample_authority", "PRE_source_graph_count", "task_ids",
    }
    for fact, event_id in zip(facts, EXPECTED_EVENT_IDS, strict=True):
        if type(fact) is not dict or set(fact) != set(GENERIC_FACT_FIELDS):
            _fail("GENERIC_EXACT11_FIELD_SET_DRIFT:" + event_id)
        if set(fact) & rich:
            _fail("GENERIC_RICH_FIELD_LEAK:" + event_id)
        expected_fact = {
            "canonical_event_id": event_id,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "human_review_completed": True,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "chemistry_disposition": "POSITIVE",
            "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
            "human_training_excluded": False,
            "source_decision_schema": FORMAL_DECISION_SCHEMA,
            "source_decision_sha256": FORMAL_BINDINGS[0][3],
            "source_binding_path": FORMAL_DECISION_RELATIVE.as_posix(),
        }
        if fact != expected_fact:
            _fail("GENERIC_EXACT11_FACT_DRIFT:" + event_id)


def _expected_summary(snapshot: Mapping[str, Any]) -> dict[str, object]:
    return _summary(snapshot)


def _validate_manifest_semantics(
    manifest: Mapping[str, Any], repo_root: Path, artifacts: Mapping[str, bytes]
) -> None:
    _expect_fields(
        manifest,
        {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "stage": "EI3_COMPLETED_DECISION_INGESTION_V1",
            "artifact_role": "DETERMINISTIC_SOURCE_CODE_AND_OUTPUT_BINDING_NO_SELF_HASH",
            "baseline_commit": BASELINE_COMMIT,
            "active_source_binding_count": 9,
            "formal_internal_source_binding_count": 10,
            "duplicate_source_binding_identity_count": 0,
            "operation_boundary": _operation_boundary(),
            "training_boundary": _training_boundary(),
            "readiness": _readiness(),
        },
        "MANIFEST_ROOT_DRIFT",
    )
    if manifest.get("candidate_source_bindings") != _candidate_source_records(repo_root):
        _fail("MANIFEST_CANDIDATE_SOURCE_BINDING_DRIFT")
    expected_outputs = [
        _output_binding(name, artifacts[name]) for name in (SNAPSHOT, MATRIX, SUMMARY)
    ]
    if manifest.get("output_artifact_bindings_excluding_manifest_self") != expected_outputs:
        _fail("MANIFEST_OUTPUT_BINDING_DRIFT")
    if any(key.lower() in {"self_sha256", "manifest_sha256"} for key in manifest):
        _fail("MANIFEST_SELF_HASH_FORBIDDEN")
    encoded = _canonical_json(manifest).decode("utf-8")
    for token in ("timestamp", "hostname", "pid", "/tmp/"):
        if token in encoded.lower():
            _fail("MANIFEST_DYNAMIC_METADATA_FORBIDDEN:" + token)


def _compare_artifacts(
    actual: Mapping[str, bytes], expected: Mapping[str, bytes], token: str
) -> None:
    for name in OUTPUT_FILENAMES:
        if actual[name] != expected[name]:
            _fail(token + ":" + name)


def _raw_comparator_control_probe(repo_root: Path) -> bool:
    expected = _build_raw(repo_root)
    corrupted = dict(expected)
    corrupted[SUMMARY] = corrupted[SUMMARY][:-1] + b" \n"
    try:
        _compare_artifacts(corrupted, expected, "RAW_COMPARATOR_CONTROL")
    except EI3IngestionSafetyError as error:
        if str(error) == ERROR_PREFIX + ":RAW_COMPARATOR_CONTROL:" + SUMMARY:
            return True
        raise
    _fail("RAW_COMPARATOR_CONTROL_DID_NOT_REJECT")


def validate_completed_decision_projection_v1(
    artifacts: Mapping[str, bytes],
    repo_root: Path,
    *,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Fail closed unless artifacts are the exact deterministic EI3 projection."""
    if (
        type(artifacts) is not dict
        or set(artifacts) != set(OUTPUT_FILENAMES)
        or any(type(payload) is not bytes for payload in artifacts.values())
    ):
        _fail("OUTPUT_INVENTORY_NOT_EXACT4_BYTES")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    snapshot = _strict_json(artifacts[SNAPSHOT], "SNAPSHOT")
    matrix_header, matrix_rows = _parse_csv(artifacts[MATRIX], "MATRIX")
    summary = _strict_json(artifacts[SUMMARY], "SUMMARY")
    manifest = _strict_json(artifacts[MANIFEST], "MANIFEST")
    _validate_snapshot_semantics(snapshot)
    if matrix_header != MATRIX_HEADER or len(matrix_rows) != 3:
        _fail("MATRIX_EXACT3_OR_HEADER_DRIFT")
    expected_matrix = _parse_csv(
        _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot)), "EXPECTED_MATRIX"
    )[1]
    if matrix_rows != expected_matrix:
        _fail("MATRIX_SEMANTICS_DRIFT")
    null_columns = {
        "selected_role_candidate_json", "role_profile_raw_json", "warhead_atom_ids_json",
        "linker_atom_ids_json", "scaffold_atom_ids_json", "minimal_seed_json",
        "minimal_seed_atom_ids_json", "primary_anchor_json",
        "structurally_applicable_task_ids_json",
    }
    if any(row[column] != "null" for row in matrix_rows for column in null_columns):
        _fail("MATRIX_NULL_SERIALIZATION_DRIFT")
    expected_summary = _expected_summary(snapshot)
    if summary != expected_summary:
        _fail("SUMMARY_SEMANTICS_DRIFT")
    _validate_manifest_semantics(manifest, Path(repo_root).resolve(), artifacts)
    expected = _build_raw(Path(repo_root).resolve(), repository_path_overrides)
    _compare_artifacts(artifacts, expected, "ARTIFACT_PROJECTION_DRIFT")
    return {
        "status": "PASS", "event_count": 3, "matrix_column_count": len(MATRIX_HEADER),
        "output_artifact_count": 4, "generic_exact11_fact_count": 3,
        "generic_exact11_field_count": 11, "raw_comparator_control_probe": True,
        "FORMAL_SOURCE_D2": SOURCE_D2,
        "NORMALIZED_TASK_RELEVANCE": NORMALIZED_TASK_RELEVANCE,
        "COMPLETED_LANE": EXPECTED_COMPLETED_LANE,
        "LEGACY_COMPLETED_REVIEW_STATUS": EXPECTED_LEGACY_STATUS,
        "CHEMISTRY_DISPOSITION": "POSITIVE", "NEGATIVE_CHEMISTRY": False,
        "TRAINING_DISPOSITION": NORMALIZED_TRAINING_DISPOSITION,
        "HUMAN_TRAINING_EXCLUDED": False,
        "FUTURE_TRAINING_ADMISSION_CANDIDATE": False,
        "PAIR_SAMPLE_AUTHORITY": True,
        "ROLE_PARTITION_SAMPLE_AUTHORITATIVE": False,
        "TASK_APPLICABILITY_SAMPLE_AUTHORITATIVE": False,
        "STRUCTURALLY_APPLICABLE_TASK_IDS": None,
        "TASK_LABEL_AUTHORITY": False, "READY_FOR_TRAINING": False,
    }


def build_artifacts_v1(
    repo_root: Path,
    *,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    artifacts = _build_raw(Path(repo_root).resolve(), repository_path_overrides)
    validate_completed_decision_projection_v1(
        artifacts,
        repo_root,
        repository_path_overrides=repository_path_overrides,
    )
    return artifacts


def _validate_destination(path: Path) -> None:
    if path.exists() and (path.is_symlink() or not path.is_dir()):
        _fail("OUTPUT_ROOT_NOT_REAL_DIRECTORY")
    cursor = path
    while not cursor.exists() and cursor != cursor.parent:
        cursor = cursor.parent
    if cursor.is_symlink():
        _fail("OUTPUT_ANCESTOR_SYMLINK")


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".covapie_ei3_", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def materialize_artifacts_v1(repo_root: Path) -> dict[str, object]:
    root = Path(repo_root).resolve()
    target = root / OUTPUT_ROOT_RELATIVE
    _validate_destination(target)
    if target.exists() and {path.name for path in target.iterdir()} - set(OUTPUT_FILENAMES):
        _fail("OUTPUT_ROOT_CONTAMINATED")
    target.mkdir(parents=True, exist_ok=True)
    artifacts = build_artifacts_v1(root)
    for name in OUTPUT_FILENAMES:
        _atomic_write(target / name, artifacts[name])
    return check_materialized_v1(root)


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    root = Path(repo_root).resolve()
    target = root / OUTPUT_ROOT_RELATIVE
    if (
        not target.is_dir()
        or target.is_symlink()
        or {path.name for path in target.iterdir()} != set(OUTPUT_FILENAMES)
    ):
        _fail("MATERIALIZED_OUTPUT_INVENTORY_NOT_EXACT4")
    live: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = target / name
        metadata = path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        ):
            _fail("MATERIALIZED_OUTPUT_CLASS_INVALID:" + name)
        live[name] = path.read_bytes()
    result = validate_completed_decision_projection_v1(live, root)
    fresh = build_artifacts_v1(root)
    _compare_artifacts(live, fresh, "MATERIALIZED_BYTES_NOT_FRESH_BUILD")
    return {
        **result,
        "materialized_bytes_equal_fresh_build": True,
        "deterministic_double_build": fresh == build_artifacts_v1(root),
        "raw_comparator_control_probe": _raw_comparator_control_probe(root),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--materialize", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    if args.preflight:
        bound = load_frozen_formal_decision_v1(repo_root)
        report = {
            "status": "PASS",
            "operation": "PREFLIGHT",
            "public_api": list(__all__),
            "schema_preflight": bound["schema_preflight"],
            "event_count": len(bound["events"]),
            "active_source_binding_count": bound["active_source_binding_count"],
            "matrix_header": list(MATRIX_HEADER),
            "matrix_column_count": len(MATRIX_HEADER),
        }
    elif args.check:
        report = {"operation": "CHECK", **check_materialized_v1(repo_root)}
    else:
        report = {"operation": "MATERIALIZE", **materialize_artifacts_v1(repo_root)}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if args.preflight:
        print("COVAPIE_EI3_INGESTION_SCHEMA_PREFLIGHT_V1_PASS=true")
    elif args.check:
        print("COVAPIE_EI3_COMPLETED_DECISION_INGESTION_V1_CHECK_PASS=true")
    else:
        print("COVAPIE_EI3_COMPLETED_DECISION_INGESTION_V1_MATERIALIZE_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
