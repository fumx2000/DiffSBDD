"""Project frozen ME7 Exact3 human authority into metadata-only artifacts.

The formal JSON is parsed and independently validated.  Its frozen validator
is content identity only and is never imported, executed, or subprocessed.
This additive stage creates no role, seed, anchor, task-label, geometry, mask,
tensor, training, reconciliation, census, queue, commit, or push authority.
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
    "ME7IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = "covapie_me7_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_me7_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_me7_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_me7_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_me7_completed_decision_ingestion_manifest_v1"
BASELINE_COMMIT = "68975a259d6c8c3c3d82dd6901975c141311475e"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_me7_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_me7_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_me7_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_me7_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_me7_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_me7_event_task_label_availability_v1.csv"
SUMMARY = "covapie_me7_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_me7_completed_decision_ingestion_manifest_v1.json"
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
    "ME7_COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129"
)
FORMAL_DECISION_RELATIVE = (
    STATE_ROOT / "formal-human-decision-v1/me7_formal_human_decision_v1.json"
)
FORMAL_VALIDATOR_RELATIVE = (
    STATE_ROOT
    / "formal-human-decision-v1/validate_me7_formal_human_decision_v1.py"
)
EVENT_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/me7_exact3_event_evidence_v1.csv"
)
GRAPH_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/me7_graph_and_review_evidence_v1.json"
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
    "covapie_cumulative1000_current_global_readiness_census_with_pyr_v1/"
    "covapie_cumulative1000_current_global_readiness_census_with_pyr_v1.csv"
)
PRIORITY_QUEUE_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1/"
    "covapie_bulk_cys_sg_priority_human_review_queue_v1.csv"
)

FORMAL_DECISION_SCHEMA = "covapie_me7_exact3_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_3CF0AB1696EEA129"
EXPECTED_SCOPE = "CURRENT_ME7_EXACT3_TARGET_REVIEW_UNIT_ONLY"
EXPECTED_COMPLETED_LANE = "COMPLETED_TASK_DOMAIN_NEGATIVE"
EXPECTED_LEGACY_STATUS = "COMPLETED_HUMAN_NEGATIVE"
SOURCE_D2 = "OUT_OF_DOMAIN"
NORMALIZED_TASK_RELEVANCE = "NOT_RELEVANT"
SOURCE_D6 = "NOT_APPLICABLE"
NORMALIZED_TRAINING_DISPOSITION = "NOT_APPLICABLE"
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS"

# Event ID, rank, PDB, protein label/auth asym, component label/auth asym,
# connection, reported/recalculated/difference lexemes, protein/component xyz.
EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:3QVY:B:CYS:82-:SG:U:ME7:CAE",
        528,
        "3QVY",
        "B",
        "B",
        "U",
        "D",
        "covale4",
        "1.805",
        "1.804924",
        "0.000076",
        ("3.386", "28.991", "4.856"),
        ("2.899", "29.486", "3.190"),
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:3QVY:C:CYS:82-:SG:O:ME7:CAE",
        529,
        "3QVY",
        "C",
        "C",
        "O",
        "C",
        "covale7",
        "1.816",
        "1.816389",
        "0.000389",
        ("-36.443", "7.373", "-3.728"),
        ("-36.518", "7.255", "-1.917"),
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:3QVZ:A:CYS:82-:SG:F:ME7:CAE",
        531,
        "3QVZ",
        "A",
        "A",
        "F",
        "A",
        "covale1",
        "1.831",
        "1.831178",
        "0.000178",
        ("-36.770", "7.699", "-4.471"),
        ("-37.606", "7.725", "-2.842"),
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)
EXPECTED_PDB_IDS = ("3QVY", "3QVZ")
CONTEXT_ONLY_RANKS = (527, 530, 533)
EXPECTED_CONTEXT = (
    (
        527,
        "COVAPIE_CYS_SG_EVENT_V1:3QVY:A:CYS:82-:SG:O:ME7:CAG",
        "COVAPIE_BULK_REVIEW_UNIT_8C17238B54AACE80",
        "3QVY",
        "SG:CAG",
        EXPECTED_EVENT_IDS[1],
        "covale1",
    ),
    (
        530,
        "COVAPIE_CYS_SG_EVENT_V1:3QVY:D:CYS:82-:SG:U:ME7:CAH",
        "COVAPIE_BULK_REVIEW_UNIT_06A012CB91AC4F3B",
        "3QVY",
        "SG:CAH",
        EXPECTED_EVENT_IDS[0],
        "covale10",
    ),
    (
        533,
        "COVAPIE_CYS_SG_EVENT_V1:3QVZ:C:CYS:82-:SG:F:ME7:CAH",
        "COVAPIE_BULK_REVIEW_UNIT_06A012CB91AC4F3B",
        "3QVZ",
        "SG:CAH",
        EXPECTED_EVENT_IDS[2],
        "covale4",
    ),
)

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
GENERIC_PROJECTION = {
    "human_review_completed": True,
    "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
    "task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
    "chemistry_disposition": "POSITIVE",
    "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
    "human_training_excluded": False,
}

# path, namespace, bytes, SHA256, executable, role, validation method
_Binding = tuple[Path, str, int, str, bool, str, str]
FORMAL_BINDINGS: tuple[_Binding, ...] = (
    (
        FORMAL_DECISION_RELATIVE,
        "project_parent_relative",
        13344,
        "9641bee4a40c9501a494fdd76ee086b7c5dbc97130a176261575d3ad1e306407",
        False,
        "ME7_FROZEN_FORMAL_HUMAN_DECISION",
        "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE,
        "project_parent_relative",
        52865,
        "67a68f9b1c14cb90591a6e377c4fc680cc816c53e138995adf0c1544eaf91009",
        False,
        "ME7_FROZEN_FORMAL_VALIDATOR",
        "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED",
    ),
)
SUPPORTING_BINDINGS: tuple[_Binding, ...] = (
    (
        EVENT_EVIDENCE_RELATIVE,
        "project_parent_relative",
        2674,
        "94bf6660ce6458f93dd3ac6ff5e58648b3e5357fe4706b606af195c14f98f2e5",
        False,
        "ME7_EXACT3_EVENT_EVIDENCE",
        "PARSED_CSV_TARGET_EXACT3_OBSERVED_GEOMETRY_AND_SOURCE_RECORDS",
    ),
    (
        GRAPH_EVIDENCE_RELATIVE,
        "project_parent_relative",
        89828,
        "02861ec451e4dcddbdb00c8e4b22540b438308bfcfef50177f5624a64cb191e1",
        False,
        "ME7_GRAPH_AND_REVIEW_EVIDENCE",
        "PARSED_JSON_TARGET_CONTEXT_AND_PRE_POST_BOUNDARY_EVIDENCE",
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
    557958,
    "e1c2b9c465401f544fe91d2641e10274cc2dd489fbb0b9a4c197779f55f405e2",
    False,
    "CURRENT_WITH_PYR_CENSUS_MATRIX",
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


class ME7IngestionSafetyError(ValueError):
    """Raised when the frozen ME7 projection contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise ME7IngestionSafetyError("COVAPIE_ME7_INGESTION_V1_ERROR:" + reason)


def _expect(actual: object, expected: object, reason: str) -> None:
    if type(actual) is not type(expected) or actual != expected:
        _fail(reason)


def _expect_fields(
    mapping: object, expected: Mapping[str, object], reason: str
) -> Mapping[str, object]:
    if type(mapping) is not dict:
        _fail(reason + ":NOT_OBJECT")
    for key, expected_value in expected.items():
        if key not in mapping:  # type: ignore[operator]
            _fail(reason + ":MISSING:" + key)
        _expect(mapping[key], expected_value, reason + ":" + key)  # type: ignore[index]
    return mapping  # type: ignore[return-value]


def _expect_exact(
    mapping: object, expected: Mapping[str, object], reason: str
) -> Mapping[str, object]:
    value = _expect_fields(mapping, expected, reason)
    if set(value) != set(expected):
        _fail(reason + ":FIELD_SET")
    return value


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
        raise ME7IngestionSafetyError(
            "COVAPIE_ME7_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label
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
        raise ME7IngestionSafetyError(
            "COVAPIE_ME7_INGESTION_V1_ERROR:JSON_PARSE_FAILED:" + label
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
        raise ME7IngestionSafetyError(
            "COVAPIE_ME7_INGESTION_V1_ERROR:CSV_UTF8_INVALID:" + label
        ) from error
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        header = tuple(reader.fieldnames or ())
        if not header or len(header) != len(set(header)):
            _fail("CSV_HEADER_DUPLICATE_OR_EMPTY:" + label)
        rows = list(reader)
    except csv.Error as error:
        raise ME7IngestionSafetyError(
            "COVAPIE_ME7_INGESTION_V1_ERROR:CSV_PARSE_FAILED:" + label
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


def _resolve(
    repo_root: Path, binding: _Binding, overrides: Mapping[Path, Path]
) -> Path:
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
        raise ME7IngestionSafetyError(
            "COVAPIE_ME7_INGESTION_V1_ERROR:SOURCE_BINDING_FAILED:"
            + relative.as_posix()
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


def _literal_assignments(
    payload: bytes, names: Sequence[str], label: str
) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8"), filename=label)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ME7IngestionSafetyError(
            "COVAPIE_ME7_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
        ) from error
    values: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id in names:
                try:
                    values[target.id] = ast.literal_eval(value)
                except (TypeError, ValueError) as error:
                    raise ME7IngestionSafetyError(
                        "COVAPIE_ME7_INGESTION_V1_ERROR:"
                        "SEMANTIC_OWNER_LITERAL_INVALID:" + target.id
                    ) from error
    if set(values) != set(names):
        _fail("SEMANTIC_OWNER_LITERAL_MISSING:" + label)
    return values


def _formal_source_rows() -> list[dict[str, object]]:
    rows = (
        (
            "review-preparation-v1/me7_review_preparation_manifest_v1.json",
            11445,
            "b2331b2794f0ff74ff008949c786c1ece86fb96ffabf5e6814d905bcb10dea30",
            "0644",
            "frozen_preparation_me7_review_preparation_manifest_v1.json",
        ),
        (
            "review-preparation-v1/me7_exact3_event_evidence_v1.csv",
            2674,
            "94bf6660ce6458f93dd3ac6ff5e58648b3e5357fe4706b606af195c14f98f2e5",
            "0644",
            "frozen_preparation_me7_exact3_event_evidence_v1.csv",
        ),
        (
            "review-preparation-v1/me7_graph_and_review_evidence_v1.json",
            89828,
            "02861ec451e4dcddbdb00c8e4b22540b438308bfcfef50177f5624a64cb191e1",
            "0644",
            "frozen_preparation_me7_graph_and_review_evidence_v1.json",
        ),
        (
            "review-preparation-v1/HUMAN_REVIEW_GUIDE.md",
            4311,
            "83f0f5ea71c5dbde066818f50589f2c022b3f0cab9557e808229ec129519e1e5",
            "0644",
            "frozen_preparation_HUMAN_REVIEW_GUIDE.md",
        ),
        (
            "review-preparation-v1/me7_unsigned_human_decision_template_v1.json",
            4677,
            "c2b2e048f1055aa9323f552bcd88e45aadc58df5f6d51a99629fb0acddde83fd",
            "0644",
            "frozen_preparation_me7_unsigned_human_decision_template_v1.json",
        ),
        (
            "review-preparation-v1/build_and_check_me7_review_preparation_v1.py",
            120598,
            "52a7638450d91e0e6cb82fdad58efcc52d8a00a2c924ab97c5b791e42b10adf3",
            "0664",
            "frozen_preparation_build_and_check_me7_review_preparation_v1.py",
        ),
        (
            "scientific-validation-v1/me7_scientific_validation_v1.json",
            29310,
            "77284bc0baa6e16a43b1532aa3124c73e825cd1687eee1ef271a4c914586cb28",
            "0664",
            "frozen_scientific_me7_scientific_validation_v1.json",
        ),
        (
            "scientific-validation-v1/validate_me7_scientific_validation_v1.py",
            62832,
            "72007afde604e16efb639a163c222dcdb7d6b1fabe4d0c16bccf82189ade1c43",
            "0664",
            "frozen_scientific_validate_me7_scientific_validation_v1.py",
        ),
        (
            "human-decision-candidate-v1/"
            "me7_filled_unsigned_human_decision_candidate_v1.json",
            17668,
            "5e0604a86961937ece43779673b0f0d15e60aecd40f0f037058c00d8380afcf6",
            "0644",
            "frozen_candidate_me7_filled_unsigned_human_decision_candidate_v1.json",
        ),
        (
            "human-decision-candidate-v1/"
            "validate_me7_filled_unsigned_human_decision_candidate_v1.py",
            45578,
            "746914510fb6ad4f2cf9251a2423b5b8f35550acbcc63b4832096a78bd2188a2",
            "0644",
            "frozen_candidate_validate_me7_filled_unsigned_human_decision_candidate_v1.py",
        ),
    )
    return [
        {
            "SHA256": digest,
            "bytes": byte_count,
            "mode": mode,
            "path_namespace": "me7_review_unit_relative",
            "relative_path": relative,
            "source_role": role,
        }
        for relative, byte_count, digest, mode, role in rows
    ]


def _formal_task_rows() -> list[dict[str, object]]:
    return [
        {"display_alias": alias, "semantic_long_name": semantic, "task_id": task_id}
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]


def _validate_formal(formal: Mapping[str, Any]) -> None:
    """Validate every field of the frozen ME7 formal decision independently."""
    if set(formal) != {
        "PRE_boundary",
        "approved_D1_D6",
        "authorization_record",
        "event_context_boundary",
        "frozen_candidate_binding",
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
    }:
        _fail("FORMAL_TOP_LEVEL_FIELDS_DRIFT")
    _expect(formal["schema_version"], FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(formal["record_role"], FORMAL_RECORD_ROLE, "FORMAL_RECORD_ROLE_DRIFT")
    _expect_exact(
        formal["authorization_record"],
        {
            "approval_conveyance": "FORWARDED_BY_CURRENT_PROMPT_FROM_COVAPIE_MAIN_REVIEW_DIALOGUE",
            "approval_time": None,
            "approval_time_status": "NOT_PROVIDED_VERIFIABLY",
            "attestor_id": "fmx",
            "authorization_complete": True,
            "authorization_message_id": None,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "authorization_text": (
                "批准本轮 ME7 Exact3 的建议确认值：D1=POSITIVE，D2=OUT_OF_DOMAIN，"
                "D3=CONFIRM_OBSERVED_PAIR（SG:CAE，非唯一 attachment），"
                "D4=CANNOT_DETERMINE，D5=NOT_DETERMINABLE（task IDs=null），"
                "D6=NOT_APPLICABLE；reviewer_id=fmx；attestor_id=fmx。"
            ),
            "chat_backend_access_claimed": False,
            "electronic_signature_claimed": False,
            "machine_generated_human_authorization": False,
            "platform_identity_verification_claimed": False,
            "reviewer_and_attestor_same_user_supplied_identifier": True,
            "reviewer_id": "fmx",
            "two_independent_authenticated_people_claimed": False,
        },
        "FORMAL_AUTHORIZATION_DRIFT",
    )
    _expect_exact(
        formal["frozen_candidate_binding"],
        {
            "SHA256": "5e0604a86961937ece43779673b0f0d15e60aecd40f0f037058c00d8380afcf6",
            "authorization_bound_to_exact_SHA256": (
                "5e0604a86961937ece43779673b0f0d15e60aecd40f0f037058c00d8380afcf6"
            ),
            "bytes": 17668,
            "candidate_human_fields_remained_unset": True,
            "candidate_is_human_authority": False,
            "candidate_modified": False,
            "candidate_was_unsigned": True,
            "mode": "0644",
            "path_namespace": "me7_review_unit_relative",
            "relative_path": (
                "human-decision-candidate-v1/"
                "me7_filled_unsigned_human_decision_candidate_v1.json"
            ),
            "source_role": (
                "frozen_candidate_me7_filled_unsigned_human_decision_candidate_v1.json"
            ),
        },
        "FORMAL_FROZEN_CANDIDATE_DRIFT",
    )
    _expect_exact(
        formal["sample_identity"],
        {
            "canonical_target_event_ids": list(EXPECTED_EVENT_IDS),
            "cross_structure_authority": False,
            "ligand_component_id": "ME7",
            "ligand_wide_authority": False,
            "pdb_ids": list(EXPECTED_PDB_IDS),
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scope": EXPECTED_SCOPE,
            "target_event_count": 3,
            "target_scaleup_ranks": list(EXPECTED_RANKS),
        },
        "FORMAL_SAMPLE_IDENTITY_DRIFT",
    )
    _expect_exact(
        formal["event_context_boundary"],
        {
            "context_merged_into_target_exact3": False,
            "context_only_event_count": 3,
            "context_only_events_received_formal_decisions": False,
            "context_only_scaleup_ranks": list(CONTEXT_ONLY_RANKS),
            "multi_attachment_context_preserved": True,
            "source_observed_pair": "SG:CAE",
            "target_event_ids": list(EXPECTED_EVENT_IDS),
            "target_pair_confirmed_as_observed_record": True,
            "target_pair_is_only_attachment_for_component_instance": False,
            "target_scaleup_ranks": list(EXPECTED_RANKS),
        },
        "FORMAL_EVENT_CONTEXT_DRIFT",
    )
    _expect_exact(
        formal["approved_D1_D6"],
        {
            "D1_observation_record_judgment": {
                "chemistry_positive": True,
                "decision": "POSITIVE",
                "human_answered": True,
                "human_approved": True,
            },
            "D2_project_domain_relevance": {
                "chemistry_negative": False,
                "chemistry_positive_is_preserved": True,
                "decision": SOURCE_D2,
                "human_answered": True,
                "human_approved": True,
                "scope": "CURRENT_UNIT_AND_CURRENT_PROJECT_TASK_DEFINITION_ONLY",
            },
            "D3_recorded_endpoint_confirmation": {
                "component_atom": "CAE",
                "decision": "CONFIRM_OBSERVED_PAIR",
                "human_answered": True,
                "human_approved": True,
                "pair": "SG:CAE",
                "protein_atom": "SG",
                "target_pair_is_only_attachment_for_component_instance": False,
            },
            "D4_role_partition_and_retained_information": {
                "decision": "CANNOT_DETERMINE",
                "formal_question_field": "D4_role_partition_and_retained_information",
                "human_answered": True,
                "human_approved": True,
                "role_candidate_count": 0,
                "selected_candidate_id": None,
                "source_proposal_field": "D4_role_partition_and_minimal_seed",
            },
            "D5_structural_task_applicability": {
                "decision": "NOT_DETERMINABLE",
                "human_answered": True,
                "human_approved": True,
                "task_ids": None,
            },
            "D6_later_use_disposition": {
                "chemistry_negative": False,
                "decision": SOURCE_D6,
                "formal_training_admitted": False,
                "future_training_admission_candidate": False,
                "human_answered": True,
                "human_approved": True,
                "human_training_excluded": False,
            },
        },
        "FORMAL_APPROVED_D1_D6_DRIFT",
    )
    _expect_exact(
        formal["sample_level_authority"],
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
            "sample_pair_authority": True,
            "sample_task_domain_authority": True,
            "task_applicability_sample_authoritative": False,
            "unsigned": False,
        },
        "FORMAL_SAMPLE_AUTHORITY_DRIFT",
    )
    _expect_exact(
        formal["role_and_task_disposition"],
        {
            "B3_present": True,
            "D4_formally_answered": True,
            "D5_formally_answered": True,
            "applicable_task_ids": None,
            "canonical_v1_task_count": 5,
            "canonical_v1_tasks": _formal_task_rows(),
            "combination_search_executed": False,
            "linker_atom_ids": None,
            "minimal_seed": None,
            "minimal_seed_atom_ids": None,
            "primary_anchor": None,
            "role_candidate_count": 0,
            "role_profile": None,
            "role_runtime_executed": False,
            "runtime_not_executed_reason": (
                "D4_CANNOT_DETERMINE_AND_D5_NOT_DETERMINABLE"
            ),
            "scaffold_atom_ids": None,
            "selected_candidate_id": None,
            "selected_role_candidate": None,
            "sixth_task_created": False,
            "task_runtime_executed": False,
            "warhead_atom_ids": None,
        },
        "FORMAL_ROLE_TASK_DISPOSITION_DRIFT",
    )
    _expect_exact(
        formal["PRE_boundary"],
        {
            "POST_to_PRE_copy": False,
            "PRE_coordinates_created": False,
            "PRE_mapping_auto_selected": False,
            "PRE_source_graph_count_per_event": [1, 1, 1],
            "PRE_source_mapping_count_per_event": [8, 8, 8],
            "PRE_source_mapping_status": PRE_MAPPING_STATUS,
            "PRE_topology_created": False,
            "PRE_zero_fill": False,
        },
        "FORMAL_PRE_BOUNDARY_DRIFT",
    )
    _expect_exact(
        formal["non_created_authority"],
        {
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
            "FORMAL_TRAINING_ADMITTED": False,
            "MASK_TENSOR_TARGETS_CREATED": False,
            "PARAMETER_UPDATE_AUTHORIZATION": False,
            "POST_geometry_training_authority": False,
            "PRE_authority": False,
            "READY_FOR_TRAINING": False,
            "TASK_LABEL_AUTHORITY": False,
            "TRAINING_MATERIALIZATION_ALLOWED": False,
            "TRAINING_STARTED": False,
            "reusable_authority_created": False,
        },
        "FORMAL_NON_CREATED_AUTHORITY_DRIFT",
    )
    _expect_exact(
        formal["operation_boundary"],
        {
            "candidate_cli_before_formal_created_pass": True,
            "candidate_cli_executed_after_formal_created": False,
            "candidate_modified": False,
            "census_refresh_performed": False,
            "commit_performed": False,
            "formal_stage_inventory_validated": True,
            "frozen_candidate_content_revalidated": True,
            "ingestion_performed": False,
            "isolated_snapshot_used": False,
            "mask_tensor_materialization_performed": False,
            "parameter_update_performed": False,
            "preparation_modified": False,
            "push_performed": False,
            "queue_refresh_performed": False,
            "reconciliation_performed": False,
            "repository_modified": False,
            "scientific_modified": False,
            "task_label_materialization_performed": False,
            "training_performed": False,
            "training_preparation_performed": False,
        },
        "FORMAL_OPERATION_BOUNDARY_DRIFT",
    )
    _expect_exact(
        formal["readiness"],
        {
            "AUTHORIZATION_COMPLETE": True,
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "FORMAL_DECISION_CREATED": True,
            "FORMAL_SAMPLE_LEVEL_AUTHORITY_CREATED": True,
            "FORMAL_TRAINING_ADMITTED": False,
            "HUMAN_DECISION_CREATED": True,
            "HUMAN_REVIEW_COMPLETED": True,
            "MASK_TENSOR_TARGETS_CREATED": False,
            "PARAMETER_UPDATE_AUTHORIZATION": False,
            "READY_FOR_TRAINING": False,
            "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
            "TASK_LABEL_AUTHORITY": False,
            "TRAINING_MATERIALIZATION_ALLOWED": False,
            "TRAINING_STARTED": False,
            "remaining_readiness_blockers": [
                "ROLE_PARTITION_SAMPLE_AUTHORITY_NOT_CREATED",
                "TASK_APPLICABILITY_SAMPLE_AUTHORITY_NOT_CREATED",
                "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING",
                "NO_FORMAL_TRAINING_ADMISSION",
            ],
        },
        "FORMAL_READINESS_DRIFT",
    )
    _expect_exact(
        formal["output_inventory"],
        {
            "JSON_self_SHA256_recorded": False,
            "file_count": 2,
            "files": [
                "me7_formal_human_decision_v1.json",
                "validate_me7_formal_human_decision_v1.py",
            ],
        },
        "FORMAL_OUTPUT_INVENTORY_DRIFT",
    )
    _expect(formal["source_bindings"], _formal_source_rows(), "FORMAL_SOURCE_BINDINGS_DRIFT")


EVENT_EVIDENCE_HEADER = (
    "scaleup_rank",
    "canonical_event_id",
    "review_unit_id",
    "pdb_id",
    "model_number",
    "protein_label_asym_id",
    "protein_auth_asym_id",
    "protein_label_comp_id",
    "protein_auth_comp_id",
    "protein_label_seq_id",
    "protein_auth_seq_id",
    "protein_insertion_code",
    "protein_atom_id",
    "protein_altloc",
    "protein_occupancy",
    "component_label_asym_id",
    "component_auth_asym_id",
    "component_label_comp_id",
    "component_auth_comp_id",
    "component_label_seq_id",
    "component_auth_seq_id",
    "component_insertion_code",
    "component_atom_id",
    "component_altloc",
    "component_occupancy",
    "connection_id",
    "connection_type",
    "connection_value_order",
    "protein_symmetry",
    "component_symmetry",
    "source_observed_pair",
    "explicit_covalent_evidence",
    "distance_only_event_inference_used",
    "reported_distance_angstrom",
    "recalculated_distance_angstrom",
    "absolute_difference_angstrom",
    "protein_x",
    "protein_y",
    "protein_z",
    "component_x",
    "component_y",
    "component_z",
    "source_datasets_json",
    "source_record_ids_json",
    "processing_pre_status",
    "pre_source_graph_count",
    "pre_source_graph_mapping_count",
    "pre_geometry_authoritative",
    "pre_geometry_training_target_available",
    "post_geometry_source_evidence_available",
    "post_geometry_sample_authoritative",
    "post_geometry_training_target_available",
    "target_event",
    "human_selected",
)


def _strict_json_cell(value: str, label: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError as error:
        raise ME7IngestionSafetyError(
            "COVAPIE_ME7_INGESTION_V1_ERROR:CSV_JSON_CELL_INVALID:" + label
        ) from error


def _validate_event_evidence(payload: bytes) -> list[dict[str, object]]:
    header, rows = _parse_csv(payload, "ME7_EVENT_EVIDENCE")
    if header != EVENT_EVIDENCE_HEADER:
        _fail("EVENT_EVIDENCE_HEADER_DRIFT")
    if len(rows) != 3:
        _fail("EVENT_EVIDENCE_NOT_EXACT3")
    projected: list[dict[str, object]] = []
    for row, expected in zip(rows, EXPECTED_EVENTS, strict=True):
        (
            event_id,
            rank,
            pdb_id,
            protein_label,
            protein_auth,
            component_label,
            component_auth,
            connection,
            reported,
            recalculated,
            difference,
            protein_xyz,
            component_xyz,
        ) = expected
        required = {
            "scaleup_rank": str(rank),
            "canonical_event_id": event_id,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "pdb_id": pdb_id,
            "model_number": "1",
            "protein_label_asym_id": protein_label,
            "protein_auth_asym_id": protein_auth,
            "protein_label_comp_id": "CYS",
            "protein_auth_comp_id": "CYS",
            "protein_label_seq_id": "82",
            "protein_auth_seq_id": "82",
            "protein_insertion_code": "null",
            "protein_atom_id": "SG",
            "protein_altloc": "null",
            "protein_occupancy": "1.00",
            "component_label_asym_id": component_label,
            "component_auth_asym_id": component_auth,
            "component_label_comp_id": "ME7",
            "component_auth_comp_id": "ME7",
            "component_label_seq_id": "null",
            "component_auth_seq_id": "501",
            "component_insertion_code": "null",
            "component_atom_id": "CAE",
            "component_altloc": "null",
            "component_occupancy": "1.00",
            "connection_id": connection,
            "connection_type": "covale",
            "connection_value_order": "null",
            "protein_symmetry": "1_555",
            "component_symmetry": "1_555",
            "source_observed_pair": "SG:CAE",
            "explicit_covalent_evidence": "true",
            "distance_only_event_inference_used": "false",
            "reported_distance_angstrom": reported,
            "recalculated_distance_angstrom": recalculated,
            "absolute_difference_angstrom": difference,
            "protein_x": protein_xyz[0],
            "protein_y": protein_xyz[1],
            "protein_z": protein_xyz[2],
            "component_x": component_xyz[0],
            "component_y": component_xyz[1],
            "component_z": component_xyz[2],
            "processing_pre_status": PRE_MAPPING_STATUS,
            "pre_source_graph_count": "1",
            "pre_source_graph_mapping_count": "8",
            "pre_geometry_authoritative": "false",
            "pre_geometry_training_target_available": "false",
            "post_geometry_source_evidence_available": "true",
            "post_geometry_sample_authoritative": "false",
            "post_geometry_training_target_available": "false",
            "target_event": "true",
            "human_selected": "false",
        }
        for key, expected_value in required.items():
            if key not in row or row[key] != expected_value:
                _fail("EVENT_EVIDENCE_DRIFT:" + str(rank) + ":" + key)
        source_datasets = _strict_json_cell(
            row["source_datasets_json"], "SOURCE_DATASETS:" + str(rank)
        )
        source_record_ids = _strict_json_cell(
            row["source_record_ids_json"], "SOURCE_RECORD_IDS:" + str(rank)
        )
        expected_records = [
            {
                528: "SOURCE_COVBINDERINPDB:CBR002866",
                529: "SOURCE_COVBINDERINPDB:CBR002865",
                531: "SOURCE_COVBINDERINPDB:CBR002898",
            }[rank],
            f"SOURCE_RCSB_PDB_DIRECT:{pdb_id}:{connection}",
        ]
        if source_datasets != ["SOURCE_COVBINDERINPDB", "SOURCE_RCSB_PDB_DIRECT"]:
            _fail("EVENT_SOURCE_DATASETS_DRIFT:" + str(rank))
        if source_record_ids != expected_records:
            _fail("EVENT_SOURCE_RECORD_IDS_DRIFT:" + str(rank))
        projected.append(
            {
                "canonical_event_id": event_id,
                "scaleup_rank": rank,
                "pdb_id": pdb_id,
                "frozen_csv_record": dict(row),
                "source_datasets": source_datasets,
                "source_record_ids": source_record_ids,
            }
        )
    return projected


_GRAPH_TOP_LEVEL_FIELDS = {
    "additional_instance_connection_context",
    "all_me7_event_inventory_for_scope_distinction",
    "artifact_role",
    "authority_boundary",
    "cache_payload_is_review_unit",
    "canonical_Exact5",
    "ccd_component_graph",
    "feature_semantics_notice",
    "human_review_state",
    "pre_post_observation_summary",
    "review_questions",
    "review_unit_id",
    "schema_version",
    "selection_crosscheck",
    "source_bindings",
    "stage",
    "target_events",
    "target_instance_atom_mappings",
    "target_scope",
}
_GRAPH_EVENT_FIELDS = {
    "absolute_difference_angstrom",
    "canonical_event_id",
    "component_endpoint",
    "connection_id",
    "connection_source",
    "connection_type",
    "connection_value_order",
    "distance_only_event_inference_used",
    "distance_tolerance_angstrom",
    "explicit_covalent_evidence",
    "human_selected",
    "model_number",
    "pdb_id",
    "processing_observation",
    "protein_endpoint",
    "recalculated_distance_angstrom",
    "reported_distance_angstrom",
    "review_unit_id",
    "scaleup_rank",
    "source_datasets",
    "source_observed_pair",
    "source_record_ids",
    "supporting_context_only",
    "target_event",
}
_ENDPOINT_FIELDS = {
    "altloc",
    "atom_id",
    "auth_asym_id",
    "auth_comp_id",
    "auth_seq_id",
    "coordinates",
    "insertion_code",
    "label_asym_id",
    "label_comp_id",
    "label_seq_id",
    "occupancy",
    "symmetry",
}
_PROCESSING_FIELDS = {
    "effective_route",
    "post",
    "pre",
    "processing_ccd_component_graph_SHA256",
    "processing_ccd_component_graph_digest_namespace",
    "processing_ligand_atom_inventory_SHA256",
    "processing_ligand_atom_inventory_digest_namespace",
    "source_datasets",
    "terminal_outcome",
}
_PRE_FIELDS = {
    "adduct_reactive_center_radius2_sha256",
    "adduct_source_graph_sha256",
    "canonical_graph_fingerprint",
    "ccd_retained_atom_coverage_complete",
    "formal_charge_pattern_authoritative",
    "net_pre_adduct_local_transformation_sha256",
    "pre_heavy_atom_count",
    "pre_reactive_center_radius2_sha256",
    "pre_source_graph_count",
    "pre_source_graph_mapping_count",
    "pre_source_graph_mapping_status",
    "pre_source_graph_sha256",
    "status",
}


def _validate_graph_target_event(
    graph_event: Mapping[str, Any], evidence: Mapping[str, object], expected: tuple[object, ...]
) -> None:
    event_id, rank, pdb_id, protein_label, protein_auth, component_label, component_auth, connection, reported, recalculated, difference, protein_xyz, component_xyz = expected
    if set(graph_event) != _GRAPH_EVENT_FIELDS:
        _fail("GRAPH_TARGET_EVENT_FIELDS_DRIFT:" + str(rank))
    _expect_fields(
        graph_event,
        {
            "canonical_event_id": event_id,
            "scaleup_rank": rank,
            "pdb_id": pdb_id,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "model_number": 1,
            "source_observed_pair": "SG:CAE",
            "connection_id": connection,
            "connection_type": "covale",
            "connection_source": "FROZEN_WWPDB_MMCIF_STRUCT_CONN_EXPLICIT",
            "connection_value_order": None,
            "reported_distance_angstrom": float(reported),
            "recalculated_distance_angstrom": float(recalculated),
            "absolute_difference_angstrom": float(difference),
            "distance_tolerance_angstrom": 0.001,
            "explicit_covalent_evidence": True,
            "distance_only_event_inference_used": False,
            "human_selected": False,
            "target_event": True,
            "supporting_context_only": False,
            "source_datasets": evidence["source_datasets"],
            "source_record_ids": evidence["source_record_ids"],
        },
        "GRAPH_TARGET_EVENT_DRIFT:" + str(rank),
    )
    protein = graph_event["protein_endpoint"]
    component = graph_event["component_endpoint"]
    if type(protein) is not dict or set(protein) != _ENDPOINT_FIELDS:
        _fail("GRAPH_PROTEIN_ENDPOINT_FIELDS_DRIFT:" + str(rank))
    if type(component) is not dict or set(component) != _ENDPOINT_FIELDS:
        _fail("GRAPH_COMPONENT_ENDPOINT_FIELDS_DRIFT:" + str(rank))
    _expect_fields(
        protein,
        {
            "atom_id": "SG",
            "label_asym_id": protein_label,
            "auth_asym_id": protein_auth,
            "label_comp_id": "CYS",
            "auth_comp_id": "CYS",
            "label_seq_id": 82,
            "auth_seq_id": 82,
            "insertion_code": None,
            "altloc": None,
            "occupancy": 1.0,
            "symmetry": "1_555",
            "coordinates": [float(value) for value in protein_xyz],
        },
        "GRAPH_PROTEIN_ENDPOINT_DRIFT:" + str(rank),
    )
    _expect_fields(
        component,
        {
            "atom_id": "CAE",
            "label_asym_id": component_label,
            "auth_asym_id": component_auth,
            "label_comp_id": "ME7",
            "auth_comp_id": "ME7",
            "label_seq_id": None,
            "auth_seq_id": 501,
            "insertion_code": None,
            "altloc": None,
            "occupancy": 1.0,
            "symmetry": "1_555",
            "coordinates": [float(value) for value in component_xyz],
        },
        "GRAPH_COMPONENT_ENDPOINT_DRIFT:" + str(rank),
    )
    processing = graph_event["processing_observation"]
    if type(processing) is not dict or set(processing) != _PROCESSING_FIELDS:
        _fail("GRAPH_PROCESSING_FIELDS_DRIFT:" + str(rank))
    _expect_fields(
        processing,
        {
            "effective_route": "HUMAN_REVIEW_REQUIRED",
            "source_datasets": ["SOURCE_COVBINDERINPDB", "SOURCE_RCSB_PDB_DIRECT"],
            "terminal_outcome": "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY",
        },
        "GRAPH_PROCESSING_DRIFT:" + str(rank),
    )
    pre = processing["pre"]
    post = processing["post"]
    if type(pre) is not dict or set(pre) != _PRE_FIELDS:
        _fail("GRAPH_PRE_FIELDS_DRIFT:" + str(rank))
    _expect_fields(
        pre,
        {
            "pre_heavy_atom_count": 16,
            "pre_source_graph_count": 1,
            "pre_source_graph_mapping_count": 8,
            "pre_source_graph_mapping_status": PRE_MAPPING_STATUS,
            "status": PRE_MAPPING_STATUS,
            "formal_charge_pattern_authoritative": False,
            "ccd_retained_atom_coverage_complete": True,
            "adduct_reactive_center_radius2_sha256": None,
            "net_pre_adduct_local_transformation_sha256": None,
            "pre_reactive_center_radius2_sha256": None,
        },
        "GRAPH_PRE_DRIFT:" + str(rank),
    )
    _expect_exact(
        post,
        {
            "full_coordinate_evidence_available": True,
            "sample_authoritative": False,
            "source_evidence_available": True,
            "training_target_available": False,
        },
        "GRAPH_POST_DRIFT:" + str(rank),
    )


def _validate_graph_evidence(
    payload: bytes, events: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    document = _strict_json(payload, "ME7_GRAPH_EVIDENCE")
    if set(document) != _GRAPH_TOP_LEVEL_FIELDS:
        _fail("GRAPH_TOP_LEVEL_FIELDS_DRIFT")
    _expect_fields(
        document,
        {
            "schema_version": "covapie_me7_graph_and_review_evidence_v1",
            "stage": "ME7_REVIEW_PREPARATION_V1",
            "artifact_role": "FROZEN_EVIDENCE_REVIEW_AID_NOT_HUMAN_AUTHORITY",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "cache_payload_is_review_unit": False,
        },
        "GRAPH_ROOT_DRIFT",
    )
    _expect_exact(
        document["target_scope"],
        {
            "all_eight_me7_events_are_not_target": True,
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "ligand_component_id": "ME7",
            "pdb_ids": list(EXPECTED_PDB_IDS),
            "rank_selection_is_non_contiguous": True,
            "scaleup_ranks": list(EXPECTED_RANKS),
            "source_observed_pair": "SG:CAE",
            "target_event_count": 3,
        },
        "GRAPH_TARGET_SCOPE_DRIFT",
    )
    target_events = document["target_events"]
    if type(target_events) is not list or len(target_events) != 3:
        _fail("GRAPH_TARGET_EVENTS_NOT_EXACT3")
    by_id = {event["canonical_event_id"]: event for event in events}
    if set(by_id) != set(EXPECTED_EVENT_IDS):
        _fail("GRAPH_CSV_TARGET_EVENT_COVERAGE_DRIFT")
    for graph_event, expected in zip(target_events, EXPECTED_EVENTS, strict=True):
        if type(graph_event) is not dict:
            _fail("GRAPH_TARGET_EVENT_NOT_OBJECT")
        _validate_graph_target_event(graph_event, by_id[expected[0]], expected)

    context = document["additional_instance_connection_context"]
    if type(context) is not list or len(context) != 3:
        _fail("GRAPH_CONTEXT_EVENTS_NOT_EXACT3")
    for graph_event, expected in zip(context, EXPECTED_CONTEXT, strict=True):
        rank, event_id, unit_id, pdb_id, pair, supports, connection = expected
        if type(graph_event) is not dict or set(graph_event) != (
            _GRAPH_EVENT_FIELDS | {"supports_target_event_id"}
        ):
            _fail("GRAPH_CONTEXT_EVENT_FIELDS_DRIFT:" + str(rank))
        _expect_fields(
            graph_event,
            {
                "scaleup_rank": rank,
                "canonical_event_id": event_id,
                "review_unit_id": unit_id,
                "pdb_id": pdb_id,
                "source_observed_pair": pair,
                "supports_target_event_id": supports,
                "connection_id": connection,
                "connection_type": "covale",
                "connection_source": "FROZEN_WWPDB_MMCIF_STRUCT_CONN_EXPLICIT",
                "explicit_covalent_evidence": True,
                "distance_only_event_inference_used": False,
                "human_selected": False,
                "target_event": False,
                "supporting_context_only": True,
                "source_datasets": [
                    "SOURCE_COVBINDERINPDB",
                    "SOURCE_RCSB_PDB_DIRECT",
                ],
            },
            "GRAPH_CONTEXT_EVENT_DRIFT:" + str(rank),
        )
    if {event["canonical_event_id"] for event in context} & set(EXPECTED_EVENT_IDS):
        _fail("GRAPH_CONTEXT_MERGED_INTO_TARGET")

    scope_rows = document["all_me7_event_inventory_for_scope_distinction"]
    if type(scope_rows) is not list or len(scope_rows) != 8:
        _fail("GRAPH_ALL_ME7_SCOPE_NOT_EXACT8")
    if any(
        type(row) is not dict
        or set(row)
        != {
            "canonical_event_id",
            "review_unit_id",
            "same_target_component_instance_context",
            "scaleup_rank",
            "target_event",
        }
        for row in scope_rows
    ):
        _fail("GRAPH_ALL_ME7_SCOPE_ROW_FIELDS_DRIFT")
    target_scope_rows = [row for row in scope_rows if row["target_event"] is True]
    if (
        [row["canonical_event_id"] for row in target_scope_rows]
        != list(EXPECTED_EVENT_IDS)
        or [row["scaleup_rank"] for row in target_scope_rows] != list(EXPECTED_RANKS)
        or any(row["review_unit_id"] != EXPECTED_REVIEW_UNIT_ID for row in target_scope_rows)
    ):
        _fail("GRAPH_ALL_ME7_TARGET_SCOPE_DRIFT")

    mappings = document["target_instance_atom_mappings"]
    if type(mappings) is not list or len(mappings) != 3:
        _fail("GRAPH_TARGET_INSTANCE_MAPPINGS_NOT_EXACT3")
    for mapping in mappings:
        if type(mapping) is not dict:
            _fail("GRAPH_TARGET_INSTANCE_MAPPING_NOT_OBJECT")
        _expect_fields(
            mapping,
            {
                "ccd_heavy_atom_count": 16,
                "observed_heavy_atom_count": 16,
                "exact_atom_id_mapping": True,
                "ccd_atoms_missing_from_instance": [],
                "instance_atoms_missing_from_ccd": [],
                "explicit_external_connection_count": 2,
            },
            "GRAPH_TARGET_INSTANCE_MAPPING_DRIFT",
        )
        if (
            type(mapping.get("observed_heavy_atom_inventory")) is not list
            or len(mapping["observed_heavy_atom_inventory"]) != 16
            or
            type(mapping.get("target_connection_ids")) is not list
            or len(mapping["target_connection_ids"]) != 1
            or type(mapping.get("context_only_connection_ids")) is not list
            or len(mapping["context_only_connection_ids"]) != 1
        ):
            _fail("GRAPH_TARGET_CONTEXT_CONNECTION_BOUNDARY_DRIFT")

    _expect_exact(
        document["pre_post_observation_summary"],
        {
            "POST_full_coordinate_evidence_available_count": 3,
            "POST_sample_authoritative_count": 0,
            "POST_source_evidence_available_count": 3,
            "POST_to_PRE_copy_performed": False,
            "POST_training_target_available_count": 0,
            "PRE_geometry_authoritative_count": 0,
            "PRE_geometry_available_count": 0,
            "PRE_geometry_training_target_available_count": 0,
            "PRE_source_graph_count_per_event": [1, 1, 1],
            "PRE_source_graph_mapping_count_per_event": [8, 8, 8],
            "PRE_status_counts": {PRE_MAPPING_STATUS: 3},
            "PRE_zero_fill_performed": False,
            "target_event_count": 3,
        },
        "GRAPH_PRE_POST_SUMMARY_DRIFT",
    )
    _expect_exact(
        document["canonical_Exact5"],
        {
            "B3_present": True,
            "mask_semantics": "MASK_IDENTIFIES_THE_TO_BE_GENERATED_PART",
            "sample_applicable_task_ids": None,
            "sixth_task_present": False,
            "task_count": 5,
            "tasks": [
                {
                    "authority_created": False,
                    "display_alias": alias,
                    "generated_part": semantic,
                    "human_applicability": None,
                    "semantic_long_name": semantic,
                    "task_id": task_id,
                }
                for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
            ],
        },
        "GRAPH_CANONICAL_EXACT5_DRIFT",
    )
    _expect_exact(
        document["human_review_state"],
        {
            "applicable_task_ids": None,
            "approved": False,
            "attestor_id": None,
            "human_decision_created": False,
            "human_review_completed": False,
            "human_selected": False,
            "linker_atom_ids": None,
            "minimal_seed": None,
            "minimal_seed_atom_ids": None,
            "primary_anchor": None,
            "reviewer_id": None,
            "role_partitions": None,
            "role_profile": None,
            "scaffold_atom_ids": None,
            "selected_candidate_id": None,
            "selected_role_candidate": None,
            "unsigned": True,
            "warhead_atom_ids": None,
        },
        "GRAPH_PREPARATION_REVIEW_STATE_DRIFT",
    )
    _expect_exact(
        document["selection_crosscheck"],
        {
            "frozen_priority_queue": "PRIORITY_RANK_32_EXACT3_FOR_UNIT",
            "published_snapshot_ME7_REVIEW_STATE_CREATED": False,
            "published_snapshot_value_is_historical_not_live_state": True,
            "published_with_pyr_census": "EXACT3_CURRENTLY_UNREVIEWED_FOR_UNIT",
            "ranks_0501_1000_cohort_and_processing": (
                "EXACT3_IDENTITIES_AND_EXPLICIT_CONNECTION_RECORDS_MATCH"
            ),
        },
        "GRAPH_SELECTION_CROSSCHECK_DRIFT",
    )
    _expect_exact(
        document["feature_semantics_notice"],
        {
            "Step12D": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
            "audit_performed": False,
            "audit_required_before_training": True,
        },
        "GRAPH_FEATURE_SEMANTICS_NOTICE_DRIFT",
    )
    ccd = document["ccd_component_graph"]
    _expect_fields(
        ccd,
        {
            "authority": "FROZEN_WWPDB_CCD_COMPONENT_OBSERVATION",
            "heavy_atom_count": 16,
            "heavy_heavy_bond_count": 17,
            "connected_component_count": 1,
            "cycle_rank": 2,
            "canonical_heavy_graph_SHA256": (
                "9609703cb5a0d743a4dd1e927b561df36078e81f11b174057f1c820c94e52233"
            ),
        },
        "GRAPH_CCD_SUMMARY_DRIFT",
    )
    return {
        "target_graph_records": [dict(event) for event in target_events],
        "context_only_graph_records": [dict(event) for event in context],
        "all_me7_scope_rows": [dict(row) for row in scope_rows],
        "target_instance_atom_mappings": [dict(row) for row in mappings],
        "ccd_summary": {
            "heavy_atom_count": 16,
            "heavy_heavy_bond_count": 17,
            "connected_component_count": 1,
            "cycle_rank": 2,
            "canonical_heavy_graph_SHA256": ccd["canonical_heavy_graph_SHA256"],
        },
    }


CENSUS_HEADER = (
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
QUEUE_HEADER = (
    "priority_rank",
    "review_unit_id",
    "event_count",
    "potential_event_yield_per_unit",
    "canonical_event_ids_json",
    "pdb_ids_json",
    "ligand_component_ids_json",
    "full_coordinate_event_count",
    "exact_reactive_pair_event_count",
    "CCD_graph_complete_event_count",
    "POST_geometry_available_event_count",
    "shadow_exact_component_event_count",
    "representation_blocked_event_count",
    "leakage_conflict_event_count",
    "priority_score",
    "priority_reason",
    "human_decision_created",
)


def _validate_current_census_and_queue(
    census_payload: bytes, queue_payload: bytes
) -> dict[str, object]:
    census_header, census_rows = _parse_csv(census_payload, "CURRENT_WITH_PYR_CENSUS")
    if census_header != CENSUS_HEADER:
        _fail("CURRENT_CENSUS_HEADER_DRIFT")
    if len(census_rows) != 1000 or len({row["canonical_event_id"] for row in census_rows}) != 1000:
        _fail("CURRENT_CENSUS_UNIVERSE_DRIFT")
    targets = [row for row in census_rows if row["review_unit_id"] == EXPECTED_REVIEW_UNIT_ID]
    if (
        len(targets) != 3
        or [row["canonical_event_id"] for row in targets] != list(EXPECTED_EVENT_IDS)
        or [int(row["scaleup_rank"]) for row in targets] != list(EXPECTED_RANKS)
    ):
        _fail("CURRENT_CENSUS_ME7_EXACT3_DRIFT")
    prior = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false",
        "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
        "human_training_excluded": "false",
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "role_profile": "NOT_ESTABLISHED",
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    }
    for row in targets:
        for key, value in prior.items():
            if row[key] != value:
                _fail("CURRENT_CENSUS_ME7_PRIOR_STATE_DRIFT:" + key)

    queue_header, queue_rows = _parse_csv(queue_payload, "FROZEN_PRIORITY_QUEUE")
    if queue_header != QUEUE_HEADER or len(queue_rows) != 131:
        _fail("FROZEN_QUEUE_HEADER_OR_ROW_COUNT_DRIFT")
    unit_rows = [row for row in queue_rows if row["review_unit_id"] == EXPECTED_REVIEW_UNIT_ID]
    if len(unit_rows) != 1:
        _fail("FROZEN_QUEUE_ME7_UNIT_NOT_EXACT1")
    queue = unit_rows[0]
    expected_queue = {
        "priority_rank": "32",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": "3",
        "potential_event_yield_per_unit": "3",
        "canonical_event_ids_json": _json_cell(list(EXPECTED_EVENT_IDS)),
        "pdb_ids_json": _json_cell(list(EXPECTED_PDB_IDS)),
        "ligand_component_ids_json": '["ME7"]',
        "full_coordinate_event_count": "3",
        "exact_reactive_pair_event_count": "3",
        "CCD_graph_complete_event_count": "3",
        "POST_geometry_available_event_count": "3",
        "shadow_exact_component_event_count": "0",
        "representation_blocked_event_count": "0",
        "leakage_conflict_event_count": "0",
        "priority_score": "3033330",
        "priority_reason": (
            "EVENT_YIELD=3;FULL_COORDINATES=3;EXACT_PAIR=3;CCD_GRAPH=3;POST=3;"
            "SHADOW_EXACT_COMPONENT=0;NO_NAME_OR_GUESSED_BIOLOGY_PRIORITY"
        ),
        "human_decision_created": "false",
    }
    for key, value in expected_queue.items():
        if queue[key] != value:
            _fail("FROZEN_QUEUE_ME7_DRIFT:" + key)
    return {
        "census_row_count": 1000,
        "ME7_event_count": 3,
        "ME7_current_global_status": "CURRENTLY_UNREVIEWED",
        "ME7_current_review_status": "CURRENTLY_UNREVIEWED",
        "ME7_human_review_completed": False,
        "ME7_structurally_applicable_task_ids": None,
        "queue_row_count": 131,
        "ME7_priority_rank": 32,
        "census_refresh_performed": False,
        "queue_refresh_performed": False,
        "historical_pending_state_is_expected_until_refresh": True,
    }


def _validate_canonical_task_owner(payload: bytes) -> None:
    literals = _literal_assignments(
        payload,
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
        CANONICAL_TASK_OWNER_RELATIVE.as_posix(),
    )
    _expect(
        literals["EXACT3_ROLES"],
        ("scaffold", "linker", "warhead"),
        "CANONICAL_EXACT3_ROLES_DRIFT",
    )
    _expect(literals["CANONICAL_TASKS"], CANONICAL_TASKS, "CANONICAL_EXACT5_DRIFT")


def _generic_compatibility(repo_root: Path) -> dict[str, object]:
    generic = importlib.import_module(
        "covalent_ext.covapie_completed_human_decision_reconciliation_v1"
    )
    if Path(generic.__file__).resolve() != (repo_root / GENERIC_OWNER_RELATIVE).resolve():
        _fail("GENERIC_OWNER_IMPORT_PATH_INVALID")
    binding = generic.SourceBinding(
        source_path=FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=FORMAL_BINDINGS[0][2],
        sha256=FORMAL_BINDINGS[0][3],
        schema_version=FORMAL_DECISION_SCHEMA,
        review_unit_id=EXPECTED_REVIEW_UNIT_ID,
    )
    generic._validate_source_binding(binding)
    fact_objects = []
    projected = []
    for event_id in EXPECTED_EVENT_IDS:
        fact = generic.NormalizedCompletedDecisionFact(
            canonical_event_id=event_id,
            review_unit_id=EXPECTED_REVIEW_UNIT_ID,
            **GENERIC_PROJECTION,
            source_decision_schema=FORMAL_DECISION_SCHEMA,
            source_decision_sha256=FORMAL_BINDINGS[0][3],
            source_binding_path=FORMAL_DECISION_RELATIVE.as_posix(),
        )
        if tuple(field.name for field in fields(fact)) != GENERIC_FACT_FIELDS:
            _fail("GENERIC_FACT_NOT_EXACT11")
        generic._validate_fact(fact, binding)
        row = {field.name: getattr(fact, field.name) for field in fields(fact)}
        if set(row) != set(GENERIC_FACT_FIELDS):
            _fail("GENERIC_RICH_FIELD_FIREWALL_FAILED")
        fact_objects.append(fact)
        projected.append(row)
    source = generic.NormalizedDecisionSource(binding=binding, facts=tuple(fact_objects))
    if type(source) is not generic.NormalizedDecisionSource or len(source.facts) != 3:
        _fail("GENERIC_NORMALIZED_SOURCE_INVALID")
    return {
        "generic_exact11_compatibility_pass": True,
        "generic_fact_field_count": 11,
        "generic_fact_fields": list(GENERIC_FACT_FIELDS),
        "accepted_fact_count": 3,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "source_formal_D2": SOURCE_D2,
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "source_formal_D6": SOURCE_D6,
        "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "facts": projected,
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


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Bind sources and independently validate frozen ME7 authority."""
    root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    payloads = _verify_bindings(root, overrides)
    formal = _strict_json(payloads[FORMAL_DECISION_RELATIVE], "ME7_FORMAL_DECISION")
    _validate_formal(formal)
    events = _validate_event_evidence(payloads[EVENT_EVIDENCE_RELATIVE])
    graph = _validate_graph_evidence(payloads[GRAPH_EVIDENCE_RELATIVE], events)
    graph_by_id = {
        row["canonical_event_id"]: row for row in graph["target_graph_records"]
    }
    for event in events:
        event["frozen_graph_source_record"] = graph_by_id[event["canonical_event_id"]]
    _validate_canonical_task_owner(payloads[CANONICAL_TASK_OWNER_RELATIVE])
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
        "events": events,
        "context_only_graph_records": graph["context_only_graph_records"],
        "all_me7_scope_rows": graph["all_me7_scope_rows"],
        "target_instance_atom_mappings": graph["target_instance_atom_mappings"],
        "ccd_summary": graph["ccd_summary"],
        "generic_Exact11_compatibility": generic,
        "current_census_and_queue_boundary": current,
    }


def _normalization_contract() -> dict[str, object]:
    return {
        "task_relevance": {
            "source_field": "D2_project_domain_relevance",
            "source_formal_value": SOURCE_D2,
            "target_field": "task_relevance_disposition",
            "normalized_value": NORMALIZED_TASK_RELEVANCE,
            "mapping": "OUT_OF_DOMAIN_TO_NOT_RELEVANT",
            "source_value_preserved": True,
        },
        "training_disposition": {
            "source_field": "D6_later_use_disposition",
            "source_formal_value": SOURCE_D6,
            "target_field": "training_disposition",
            "normalized_value": NORMALIZED_TRAINING_DISPOSITION,
            "mapping": "NOT_APPLICABLE_TO_NOT_APPLICABLE",
            "source_value_preserved": True,
        },
        "direction": "FORMAL_SOURCE_TO_GENERIC_RECONCILIATION_VOCABULARY",
        "chemistry_disposition_changed_by_normalization": False,
        "legacy_negative_means_task_domain_negative_not_chemistry_negative": True,
        "human_training_exclusion_created_by_normalization": False,
    }


def _task_contract() -> dict[str, object]:
    return {
        "global_canonical_tasks": [
            {
                "task_id": task_id,
                "semantic_long_name": semantic,
                "display_alias": alias,
                "generated_roles": list(generated),
                "fixed_or_seed_roles": list(fixed),
                "structurally_applicable": None,
                "human_applicability": None,
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
        "task_label_authority": False,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "mask_tensor_targets_created": False,
        "training_mask_targets_available_now": False,
    }


def _runtime_non_execution_contract() -> dict[str, object]:
    return {
        "role_runtime_executed": False,
        "seed_runtime_executed": False,
        "task_runtime_executed": False,
        "combination_search_executed": False,
        "runtime_not_executed_reason": "D4_CANNOT_DETERMINE_AND_D5_NOT_DETERMINABLE",
        "runtime_result_fabricated": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "source_formal_training_use_decision": SOURCE_D6,
        "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "training_use_allowed": False,
        "human_training_excluded": False,
        "human_training_excluded_false_is_not_include_or_admission": True,
        "candidate_for_future_training_admission": False,
        "future_training_admission_candidate": False,
        "training_admitted": False,
        "formal_training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed": False,
        "tensor_target_created": False,
        "model_supervision_usable": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "NOT_APPLICABLE_is_EXCLUDE_FROM_TRAINING_ONLY": False,
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
    }


def _pre_boundary() -> dict[str, object]:
    return {
        "source_graph_count_per_event": 1,
        "mapping_count_per_event": 8,
        "PRE_source_mapping_status": PRE_MAPPING_STATUS,
        "PRE_authority": False,
        "PRE_mapping_auto_selected": False,
        "POST_to_PRE_copy": False,
        "PRE_zero_fill": False,
        "PRE_coordinates_created": False,
        "PRE_topology_created": False,
        "formal_charge_pattern_authoritative": False,
        "mapping_or_reaction_edit_inferred": False,
    }


def _post_boundary() -> dict[str, object]:
    return {
        "representation": "OBSERVED_POST",
        "POST_source_evidence_available": True,
        "explicit_covalent_evidence": True,
        "distance_only_inference": False,
        "POST_sample_geometry_authority_created": False,
        "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
        "pair_identity_authority_is_exact_geometry_training_authority": False,
        "source_distance_lexemes_preserved": True,
    }


def _operation_boundary() -> dict[str, object]:
    return {
        "metadata_only_ingestion": True,
        "reconciliation_performed": False,
        "census_refresh_performed": False,
        "queue_refresh_performed": False,
        "next_review_started": False,
        "event_task_label_row_materialization_performed": False,
        "mask_or_tensor_materialization_performed": False,
        "dataset_materialization_performed": False,
        "training_preparation_performed": False,
        "feature_semantics_audit_performed": False,
        "model_forward_performed": False,
        "loss_performed": False,
        "backward_performed": False,
        "optimizer_step_performed": False,
        "parameter_update_performed": False,
        "training_performed": False,
        "commit_performed": False,
        "push_performed": False,
    }


def _readiness() -> dict[str, object]:
    return {
        "PROJECTION_OF_FROZEN_FORMAL_HUMAN_AUTHORITY": True,
        "NEW_HUMAN_AUTHORITY_CREATED_BY_INGESTION": False,
        "HUMAN_REVIEW_COMPLETED": True,
        "PAIR_SAMPLE_AUTHORITY": True,
        "ROLE_PARTITION_SAMPLE_AUTHORITATIVE": False,
        "TASK_APPLICABILITY_SAMPLE_AUTHORITATIVE": False,
        "TASK_LABEL_AUTHORITY": False,
        "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "MASK_TENSOR_TARGETS_CREATED": False,
        "FORMAL_TRAINING_ADMITTED": False,
        "TRAINING_MATERIALIZATION_ALLOWED": False,
        "PARAMETER_UPDATE_AUTHORIZATION": False,
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
        "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
    }


def _event_projection(event: Mapping[str, object]) -> dict[str, object]:
    return {
        **event,
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "ME7",
        "target_event": True,
        "context_only": False,
        "human_review_completed": True,
        "D4_formally_answered": True,
        "D5_formally_answered": True,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "source_formal_D1": "POSITIVE",
        "chemistry_disposition": "POSITIVE",
        "negative_chemistry": False,
        "source_formal_D2": SOURCE_D2,
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "task_domain_negative": True,
        "source_formal_D3": "CONFIRM_OBSERVED_PAIR",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "CAE",
        "observed_pair": "SG:CAE",
        "pair_sample_authority": True,
        "target_pair_is_only_attachment_for_component_instance": False,
        "source_formal_D4": "CANNOT_DETERMINE",
        "D4_source_proposal_field": "D4_role_partition_and_minimal_seed",
        "role_candidate_count": 0,
        "selected_role_candidate": None,
        "role_profile": None,
        "role_profile_derived_state": "NOT_ESTABLISHED",
        "warhead_atom_ids": None,
        "linker_atom_ids": None,
        "scaffold_atom_ids": None,
        "minimal_seed": None,
        "minimal_seed_atom_ids": None,
        "primary_anchor": None,
        "role_partition_sample_authoritative": False,
        "minimal_seed_sample_authoritative": False,
        "source_formal_D5": "NOT_DETERMINABLE",
        "structurally_applicable_task_ids": None,
        "task_applicability_sample_authoritative": False,
        "canonical_mask_structural_labels_available": False,
        "task_label_authority": False,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "mask_tensor_targets_created": False,
        "source_formal_D6": SOURCE_D6,
        "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "human_training_excluded": False,
        "future_training_admission_candidate": False,
        "formal_training_admitted": False,
        "training_materialization_allowed": False,
        "POST_geometry_training_authority": False,
        "PRE_authority": False,
        **_runtime_non_execution_contract(),
        **_training_boundary(),
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    formal = bound["formal_document"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "DETERMINISTIC_METADATA_ONLY_COMPLETED_DECISION_PROJECTION",
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
        "network_required": False,
        "sample_identity": {
            "pdb_ids": list(EXPECTED_PDB_IDS),
            "ligand_component_id": "ME7",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "authority_scope": EXPECTED_SCOPE,
            "event_count": 3,
            "scaleup_event_ranks": list(EXPECTED_RANKS),
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
        },
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "formal_validator_provenance": {
            "formal_validator_imported": False,
            "formal_validator_executed_by_production": False,
            "formal_validator_subprocessed_by_production": False,
            "identity_only": True,
        },
        "formal_human_authority": {
            "approved": True,
            "unsigned": False,
            "authorization_complete": True,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "authorization_text": formal["authorization_record"]["authorization_text"],
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "approval_time": None,
            "approval_time_status": "NOT_PROVIDED_VERIFIABLY",
            "formal_sample_level_authority_created": True,
            "human_review_completed": True,
            "formal_decision_created": True,
            "machine_generated_human_authorization": False,
            "platform_identity_verification_claimed": False,
            "chat_backend_access_claimed": False,
            "electronic_signature_claimed": False,
            "authorization_bound_candidate_SHA256": (
                "5e0604a86961937ece43779673b0f0d15e60aecd40f0f037058c00d8380afcf6"
            ),
        },
        "source_formal_D1_D6": {
            "D1_observation_record_judgment": "POSITIVE",
            "D2_project_domain_relevance": SOURCE_D2,
            "D3_recorded_endpoint_confirmation": "CONFIRM_OBSERVED_PAIR",
            "D3_observed_pair": "SG:CAE",
            "D3_target_pair_is_only_attachment_for_component_instance": False,
            "D4_role_partition_and_retained_information": "CANNOT_DETERMINE",
            "D4_source_proposal_field": "D4_role_partition_and_minimal_seed",
            "D4_role_candidate_count": 0,
            "D4_selected_candidate_id": None,
            "D5_structural_task_applicability": "NOT_DETERMINABLE",
            "D5_task_ids": None,
            "D6_later_use_disposition": SOURCE_D6,
        },
        "normalization_contract": _normalization_contract(),
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "chemistry_and_task_domain_separation": {
            "chemistry_disposition": "POSITIVE",
            "task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "task_domain_negative": True,
            "negative_chemistry": False,
            "legacy_negative_is_task_domain_negative": True,
        },
        "sample_authority_map": {
            "chemistry_sample_authority": True,
            "task_relevance_sample_authority": True,
            "pair_sample_authority": True,
            "D6_disposition_sample_authority": True,
            "role_partition_sample_authoritative": False,
            "minimal_seed_sample_authoritative": False,
            "task_applicability_sample_authoritative": False,
            "task_label_authority": False,
            "POST_geometry_training_authority": False,
            "PRE_authority": False,
        },
        "events": [_event_projection(event) for event in bound["events"]],
        "reactive_pair_authority": {
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CAE",
            "observed_pair": "SG:CAE",
            "scope": EXPECTED_SCOPE,
            "sample_level_authoritative": True,
            "target_pair_is_only_attachment_for_component_instance": False,
            "reusable_pair_authority": False,
            "ligand_wide_authority": False,
            "cross_structure_generalization": False,
        },
        "context_boundary": {
            "context_merged_into_target_exact3": False,
            "context_only_event_count": 3,
            "context_only_scaleup_ranks": list(CONTEXT_ONLY_RANKS),
            "context_only_events_received_formal_decisions": False,
            "context_only_records": bound["context_only_graph_records"],
            "all_me7_scope_rows": bound["all_me7_scope_rows"],
        },
        "role_seed_and_task_null_state": {
            "D4_formally_answered": True,
            "D5_formally_answered": True,
            "selected_role_candidate": None,
            "role_profile": None,
            "role_profile_derived_state": "NOT_ESTABLISHED",
            "warhead_atom_ids": None,
            "linker_atom_ids": None,
            "scaffold_atom_ids": None,
            "minimal_seed": None,
            "minimal_seed_atom_ids": None,
            "primary_anchor": None,
            "structurally_applicable_task_ids": None,
            "role_partition_sample_authoritative": False,
            "minimal_seed_sample_authoritative": False,
            "task_applicability_sample_authoritative": False,
            "canonical_mask_structural_labels_available": False,
            **_runtime_non_execution_contract(),
        },
        "canonical_task_contract": _task_contract(),
        "generic_Exact11_compatibility": bound["generic_Exact11_compatibility"],
        "source_graph_context": {
            "target_instance_atom_mappings": bound["target_instance_atom_mappings"],
            "ccd_summary": bound["ccd_summary"],
            "no_mapping_selected": True,
            "no_role_or_task_authority_derived": True,
        },
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(),
        "training_boundary": _training_boundary(),
        "non_created_authority": {
            "reusable_authority_created": False,
            "reaction_family_authority": False,
            "warhead_rule_authority": False,
            "warhead_type_authority": False,
            "role_partition_sample_authority": False,
            "task_applicability_sample_authority": False,
            "PRE_authority": False,
            "POST_geometry_training_authority": False,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
            "formal_training_admitted": False,
            "training_materialization_allowed": False,
            "parameter_update_authorization": False,
        },
        "current_with_PYR_census_and_queue_preingestion_boundary": bound[
            "current_census_and_queue_boundary"
        ],
        "operation_boundary": _operation_boundary(),
        "readiness": _readiness(),
    }


MATRIX_HEADER = (
    "artifact_role",
    "canonical_event_id",
    "scaleup_rank",
    "review_unit_id",
    "pdb_id",
    "protein_label_asym_id",
    "component_label_asym_id",
    "component_auth_asym_id",
    "connection_id",
    "source_observed_pair",
    "reported_distance_angstrom",
    "recalculated_distance_angstrom",
    "absolute_difference_angstrom",
    "protein_coordinates_json",
    "component_coordinates_json",
    "source_datasets_json",
    "source_record_ids_json",
    "evidence_human_selected",
    "human_review_completed",
    "D4_formally_answered",
    "D5_formally_answered",
    "completed_lane",
    "legacy_completed_review_status",
    "source_formal_D1",
    "chemistry_disposition",
    "negative_chemistry",
    "source_formal_D2",
    "normalized_task_relevance_disposition",
    "task_domain_negative",
    "source_formal_D3",
    "pair_sample_authority",
    "target_pair_is_only_attachment",
    "source_formal_D4",
    "D4_source_proposal_field",
    "role_candidate_count",
    "selected_role_candidate_json",
    "role_profile_raw_json",
    "role_profile_derived_state",
    "warhead_atom_ids_json",
    "linker_atom_ids_json",
    "scaffold_atom_ids_json",
    "minimal_seed_json",
    "minimal_seed_atom_ids_json",
    "primary_anchor_json",
    "role_partition_sample_authoritative",
    "minimal_seed_sample_authoritative",
    "role_runtime_executed",
    "seed_runtime_executed",
    "source_formal_D5",
    "structurally_applicable_task_ids_json",
    "task_applicability_sample_authoritative",
    "task_runtime_executed",
    "canonical_task_count",
    "B3_present",
    "sixth_task",
    "canonical_mask_structural_labels_available",
    "task_label_authority",
    "event_task_label_rows_materialized",
    "mask_tensor_targets_created",
    "source_formal_D6",
    "training_disposition",
    "human_training_excluded",
    "future_training_admission_candidate",
    "formal_training_admitted",
    "training_materialization_allowed",
    "POST_source_evidence_available",
    "POST_sample_geometry_authority",
    "POST_geometry_training_authority",
    "PRE_source_graph_count",
    "PRE_source_mapping_count",
    "PRE_source_mapping_status",
    "PRE_mapping_auto_selected",
    "PRE_authority",
    "POST_to_PRE_copy",
    "PRE_zero_fill",
    "FEATURE_SEMANTICS_AUDIT_PERFORMED",
    "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING",
    "READY_FOR_TRAINING",
    "TRAINING_STARTED",
)
MATRIX_JSON_COLUMNS = frozenset(
    {
        "protein_coordinates_json",
        "component_coordinates_json",
        "source_datasets_json",
        "source_record_ids_json",
        "selected_role_candidate_json",
        "role_profile_raw_json",
        "warhead_atom_ids_json",
        "linker_atom_ids_json",
        "scaffold_atom_ids_json",
        "minimal_seed_json",
        "minimal_seed_atom_ids_json",
        "primary_anchor_json",
        "structurally_applicable_task_ids_json",
    }
)
MATRIX_INTEGER_COLUMNS = frozenset(
    {
        "scaleup_rank",
        "role_candidate_count",
        "canonical_task_count",
        "PRE_source_graph_count",
        "PRE_source_mapping_count",
    }
)
MATRIX_BOOLEAN_COLUMNS = frozenset(
    {
        "evidence_human_selected",
        "human_review_completed",
        "D4_formally_answered",
        "D5_formally_answered",
        "negative_chemistry",
        "task_domain_negative",
        "pair_sample_authority",
        "target_pair_is_only_attachment",
        "role_partition_sample_authoritative",
        "minimal_seed_sample_authoritative",
        "role_runtime_executed",
        "seed_runtime_executed",
        "task_applicability_sample_authoritative",
        "task_runtime_executed",
        "B3_present",
        "sixth_task",
        "canonical_mask_structural_labels_available",
        "task_label_authority",
        "event_task_label_rows_materialized",
        "mask_tensor_targets_created",
        "human_training_excluded",
        "future_training_admission_candidate",
        "formal_training_admitted",
        "training_materialization_allowed",
        "POST_source_evidence_available",
        "POST_sample_geometry_authority",
        "POST_geometry_training_authority",
        "PRE_mapping_auto_selected",
        "PRE_authority",
        "POST_to_PRE_copy",
        "PRE_zero_fill",
        "FEATURE_SEMANTICS_AUDIT_PERFORMED",
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING",
        "READY_FOR_TRAINING",
        "TRAINING_STARTED",
    }
)


def _matrix_column_types() -> list[dict[str, str]]:
    result = []
    for column in MATRIX_HEADER:
        if column in MATRIX_JSON_COLUMNS:
            value_type = "canonical_json"
        elif column in MATRIX_INTEGER_COLUMNS:
            value_type = "integer"
        elif column in MATRIX_BOOLEAN_COLUMNS:
            value_type = "lowercase_boolean"
        else:
            value_type = "string"
        result.append({"column": column, "type": value_type})
    return result


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        evidence = event["frozen_csv_record"]
        row: dict[str, object] = {
            "artifact_role": "TASK_LABEL_AVAILABILITY_METADATA_ONLY_NOT_LABEL_ROWS",
            "canonical_event_id": event["canonical_event_id"],
            "scaleup_rank": event["scaleup_rank"],
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "pdb_id": event["pdb_id"],
            "protein_label_asym_id": evidence["protein_label_asym_id"],
            "component_label_asym_id": evidence["component_label_asym_id"],
            "component_auth_asym_id": evidence["component_auth_asym_id"],
            "connection_id": evidence["connection_id"],
            "source_observed_pair": "SG:CAE",
            "reported_distance_angstrom": evidence["reported_distance_angstrom"],
            "recalculated_distance_angstrom": evidence["recalculated_distance_angstrom"],
            "absolute_difference_angstrom": evidence["absolute_difference_angstrom"],
            "protein_coordinates_json": _json_cell(
                [evidence["protein_x"], evidence["protein_y"], evidence["protein_z"]]
            ),
            "component_coordinates_json": _json_cell(
                [evidence["component_x"], evidence["component_y"], evidence["component_z"]]
            ),
            "source_datasets_json": _json_cell(event["source_datasets"]),
            "source_record_ids_json": _json_cell(event["source_record_ids"]),
            "evidence_human_selected": "false",
            "human_review_completed": "true",
            "D4_formally_answered": "true",
            "D5_formally_answered": "true",
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "source_formal_D1": "POSITIVE",
            "chemistry_disposition": "POSITIVE",
            "negative_chemistry": "false",
            "source_formal_D2": SOURCE_D2,
            "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "task_domain_negative": "true",
            "source_formal_D3": "CONFIRM_OBSERVED_PAIR",
            "pair_sample_authority": "true",
            "target_pair_is_only_attachment": "false",
            "source_formal_D4": "CANNOT_DETERMINE",
            "D4_source_proposal_field": "D4_role_partition_and_minimal_seed",
            "role_candidate_count": 0,
            "selected_role_candidate_json": "null",
            "role_profile_raw_json": "null",
            "role_profile_derived_state": "NOT_ESTABLISHED",
            "warhead_atom_ids_json": "null",
            "linker_atom_ids_json": "null",
            "scaffold_atom_ids_json": "null",
            "minimal_seed_json": "null",
            "minimal_seed_atom_ids_json": "null",
            "primary_anchor_json": "null",
            "role_partition_sample_authoritative": "false",
            "minimal_seed_sample_authoritative": "false",
            "role_runtime_executed": "false",
            "seed_runtime_executed": "false",
            "source_formal_D5": "NOT_DETERMINABLE",
            "structurally_applicable_task_ids_json": "null",
            "task_applicability_sample_authoritative": "false",
            "task_runtime_executed": "false",
            "canonical_task_count": 5,
            "B3_present": "true",
            "sixth_task": "false",
            "canonical_mask_structural_labels_available": "false",
            "task_label_authority": "false",
            "event_task_label_rows_materialized": "false",
            "mask_tensor_targets_created": "false",
            "source_formal_D6": SOURCE_D6,
            "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
            "human_training_excluded": "false",
            "future_training_admission_candidate": "false",
            "formal_training_admitted": "false",
            "training_materialization_allowed": "false",
            "POST_source_evidence_available": "true",
            "POST_sample_geometry_authority": "false",
            "POST_geometry_training_authority": "false",
            "PRE_source_graph_count": 1,
            "PRE_source_mapping_count": 8,
            "PRE_source_mapping_status": PRE_MAPPING_STATUS,
            "PRE_mapping_auto_selected": "false",
            "PRE_authority": "false",
            "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false",
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": "false",
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": "true",
            "READY_FOR_TRAINING": "false",
            "TRAINING_STARTED": "false",
        }
        if tuple(row) != MATRIX_HEADER:
            _fail("MATRIX_ROW_HEADER_ORDER_DRIFT")
        rows.append(row)
    return rows


def _summary(snapshot: Mapping[str, Any]) -> dict[str, object]:
    events = snapshot["events"]
    count = lambda key, value: sum(event[key] == value for event in events)
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "review_unit": "ME7",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": len(events),
        "review_unit_count": len({event["review_unit_id"] for event in events}),
        "human_review_completed_count": count("human_review_completed", True),
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "source_formal_D2": SOURCE_D2,
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "source_formal_D6": SOURCE_D6,
        "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "chemistry_positive_count": count("chemistry_disposition", "POSITIVE"),
        "negative_chemistry_count": count("negative_chemistry", True),
        "task_not_relevant_count": count(
            "task_relevance_disposition", NORMALIZED_TASK_RELEVANCE
        ),
        "task_domain_negative_count": count("task_domain_negative", True),
        "training_not_applicable_count": count(
            "training_disposition", NORMALIZED_TRAINING_DISPOSITION
        ),
        "human_training_excluded_count": count("human_training_excluded", True),
        "future_training_admission_candidate_count": count(
            "future_training_admission_candidate", True
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
        "canonical_structural_label_available_count": count(
            "canonical_mask_structural_labels_available", True
        ),
        "task_label_authority_count": count("task_label_authority", True),
        "event_task_label_rows_materialized_count": count(
            "event_task_label_rows_materialized", True
        ),
        "mask_tensor_target_count": count("mask_tensor_targets_created", True),
        "generic_exact11_accepted_count": len(
            snapshot["generic_Exact11_compatibility"]["facts"]
        ),
        "generic_exact11_fact_count": len(
            snapshot["generic_Exact11_compatibility"]["facts"]
        ),
        "rich_fields_leaked_to_generic_facts": False,
        "formal_training_admitted_count": count("formal_training_admitted", True),
        "PRE_authority_count": count("PRE_authority", True),
        "POST_training_authority_count": count(
            "POST_geometry_training_authority", True
        ),
        "context_only_event_count": snapshot["context_boundary"][
            "context_only_event_count"
        ],
        "normalization_contract": _normalization_contract(),
        "canonical_task_contract": _task_contract(),
        "runtime_non_execution_contract": _runtime_non_execution_contract(),
        "training_boundary": _training_boundary(),
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(),
        "operation_boundary": _operation_boundary(),
        "readiness": _readiness(),
    }


def _validate_text_payload(label: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes
        or not payload
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\r" in payload
        or b"\x00" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
        or len(payload) >= 1024 * 1024
    ):
        _fail("TEXT_PAYLOAD_HYGIENE_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ME7IngestionSafetyError(
            "COVAPIE_ME7_INGESTION_V1_ERROR:TEXT_UTF8_INVALID:" + label
        ) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TEXT_TRAILING_WHITESPACE:" + label)


def _candidate_source_records(repo_root: Path) -> list[dict[str, object]]:
    records = []
    for relative in (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE):
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ME7IngestionSafetyError(
                "COVAPIE_ME7_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
                + relative.as_posix()
            ) from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        ):
            _fail("CANDIDATE_SOURCE_CLASS_INVALID:" + relative.as_posix())
        _validate_text_payload(relative.as_posix(), payload)
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


def _manifest(
    repo_root: Path,
    bound: Mapping[str, object],
    snapshot_bytes: bytes,
    matrix_bytes: bytes,
    summary_bytes: bytes,
) -> dict[str, object]:
    output_bindings = [
        {
            "path": (OUTPUT_ROOT_RELATIVE / name).as_posix(),
            "byte_count": len(payload),
            "SHA256": _sha256(payload),
        }
        for name, payload in (
            (SNAPSHOT, snapshot_bytes),
            (MATRIX, matrix_bytes),
            (SUMMARY, summary_bytes),
        )
    ]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "ME7_COMPLETED_DECISION_METADATA_ONLY_INGESTION_MANIFEST",
        "candidate_publication_file_count": 7,
        "candidate_publication_paths": [
            path.as_posix() for path in CANDIDATE_PUBLICATION_PATHS
        ],
        "output_artifact_count": 4,
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "matrix_contract": {
            "schema_version": MATRIX_SCHEMA_VERSION,
            "header_frozen": True,
            "header": list(MATRIX_HEADER),
            "column_count": len(MATRIX_HEADER),
            "column_types": _matrix_column_types(),
            "boolean_serialization": "lowercase_true_false",
            "json_serialization": "canonical_compact_json",
            "null_json_serialization": "null",
            "nullable_json_empty_string_forbidden": True,
            "rows_are_availability_metadata_not_event_task_label_rows": True,
        },
        "candidate_source_bindings": _candidate_source_records(repo_root),
        "output_artifact_bindings_excluding_manifest_self": output_bindings,
        "active_source_binding_count": 9,
        "semantic_source_identity_count": 9,
        "duplicate_source_binding_identity_count": 0,
        "active_source_bindings": bound["active_source_bindings"],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_executed_by_production": False,
        "formal_validator_subprocessed_by_production": False,
        "formal_semantics_independently_validated": True,
        "normalization_contract": _normalization_contract(),
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "generic_Exact11_compatibility": bound["generic_Exact11_compatibility"],
        "canonical_task_contract": _task_contract(),
        "runtime_non_execution_contract": _runtime_non_execution_contract(),
        "current_census_and_queue_boundary": bound[
            "current_census_and_queue_boundary"
        ],
        "manifest_self_SHA256_recorded": False,
        "determinism": {
            "canonical_JSON": True,
            "LF_only": True,
            "dynamic_values_absent": True,
            "absolute_machine_paths_absent": True,
        },
        "operation_boundary": _operation_boundary(),
        "training_boundary": _training_boundary(),
        "readiness": _readiness(),
    }


def _build_raw(
    repo_root: Path, overrides: Mapping[Path, Path] | None = None
) -> dict[str, bytes]:
    bound = load_frozen_formal_decision_v1(
        repo_root, repository_path_overrides=overrides
    )
    snapshot_bytes = _json_bytes(_snapshot(bound))
    snapshot = _strict_json(snapshot_bytes, "BUILT_SNAPSHOT")
    matrix_bytes = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    summary_bytes = _json_bytes(_summary(snapshot))
    manifest_bytes = _json_bytes(
        _manifest(
            Path(repo_root).resolve(),
            bound,
            snapshot_bytes,
            matrix_bytes,
            summary_bytes,
        )
    )
    return {
        SNAPSHOT: snapshot_bytes,
        MATRIX: matrix_bytes,
        SUMMARY: summary_bytes,
        MANIFEST: manifest_bytes,
    }


def _validate_snapshot_semantics(snapshot: Mapping[str, Any]) -> None:
    _expect_fields(
        snapshot,
        {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "stage": SCHEMA_VERSION,
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "projection_of_frozen_formal_human_authority": True,
            "new_human_authority_created_by_ingestion": False,
            "network_required": False,
        },
        "SNAPSHOT_ROOT_DRIFT",
    )
    _expect(
        snapshot.get("normalization_contract"),
        _normalization_contract(),
        "SNAPSHOT_NORMALIZATION_DRIFT",
    )
    _expect_fields(
        snapshot.get("sample_identity"),
        {
            "pdb_ids": list(EXPECTED_PDB_IDS),
            "ligand_component_id": "ME7",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "authority_scope": EXPECTED_SCOPE,
            "event_count": 3,
            "scaleup_event_ranks": list(EXPECTED_RANKS),
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
        },
        "SNAPSHOT_SAMPLE_IDENTITY_DRIFT",
    )
    _expect_fields(
        snapshot.get("source_formal_D1_D6"),
        {
            "D1_observation_record_judgment": "POSITIVE",
            "D2_project_domain_relevance": SOURCE_D2,
            "D3_recorded_endpoint_confirmation": "CONFIRM_OBSERVED_PAIR",
            "D3_observed_pair": "SG:CAE",
            "D3_target_pair_is_only_attachment_for_component_instance": False,
            "D4_role_partition_and_retained_information": "CANNOT_DETERMINE",
            "D4_source_proposal_field": "D4_role_partition_and_minimal_seed",
            "D4_role_candidate_count": 0,
            "D4_selected_candidate_id": None,
            "D5_structural_task_applicability": "NOT_DETERMINABLE",
            "D5_task_ids": None,
            "D6_later_use_disposition": SOURCE_D6,
        },
        "SNAPSHOT_FORMAL_D1_D6_DRIFT",
    )
    events = snapshot.get("events")
    if type(events) is not list or len(events) != 3:
        _fail("SNAPSHOT_EVENTS_NOT_EXACT3")
    if [event.get("canonical_event_id") for event in events] != list(EXPECTED_EVENT_IDS):
        _fail("SNAPSHOT_EVENT_IDS_DRIFT")
    for event, expected in zip(events, EXPECTED_EVENTS, strict=True):
        event_id, rank, pdb_id, *_rest = expected
        _expect_fields(
            event,
            {
                "canonical_event_id": event_id,
                "scaleup_rank": rank,
                "pdb_id": pdb_id,
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
                "target_event": True,
                "context_only": False,
                "human_review_completed": True,
                "D4_formally_answered": True,
                "D5_formally_answered": True,
                "completed_lane": EXPECTED_COMPLETED_LANE,
                "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
                "source_formal_D1": "POSITIVE",
                "chemistry_disposition": "POSITIVE",
                "negative_chemistry": False,
                "source_formal_D2": SOURCE_D2,
                "task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
                "task_domain_negative": True,
                "source_formal_D3": "CONFIRM_OBSERVED_PAIR",
                "observed_pair": "SG:CAE",
                "pair_sample_authority": True,
                "target_pair_is_only_attachment_for_component_instance": False,
                "source_formal_D4": "CANNOT_DETERMINE",
                "D4_source_proposal_field": "D4_role_partition_and_minimal_seed",
                "role_candidate_count": 0,
                "selected_role_candidate": None,
                "role_profile": None,
                "role_profile_derived_state": "NOT_ESTABLISHED",
                "warhead_atom_ids": None,
                "linker_atom_ids": None,
                "scaffold_atom_ids": None,
                "minimal_seed": None,
                "minimal_seed_atom_ids": None,
                "primary_anchor": None,
                "role_partition_sample_authoritative": False,
                "minimal_seed_sample_authoritative": False,
                "source_formal_D5": "NOT_DETERMINABLE",
                "structurally_applicable_task_ids": None,
                "task_applicability_sample_authoritative": False,
                "canonical_mask_structural_labels_available": False,
                "task_label_authority": False,
                "event_task_label_rows_materialized": False,
                "mask_tensor_targets_created": False,
                "source_formal_D6": SOURCE_D6,
                "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
                "human_training_excluded": False,
                "future_training_admission_candidate": False,
                "formal_training_admitted": False,
                "training_materialization_allowed": False,
                "role_runtime_executed": False,
                "seed_runtime_executed": False,
                "task_runtime_executed": False,
                "POST_geometry_training_authority": False,
                "PRE_authority": False,
                "READY_FOR_TRAINING": False,
                "TRAINING_STARTED": False,
            },
            "SNAPSHOT_EVENT_DRIFT:" + str(rank),
        )
        if type(event.get("frozen_csv_record")) is not dict:
            _fail("SNAPSHOT_EVENT_CSV_RECORD_MISSING:" + str(rank))
        if type(event.get("frozen_graph_source_record")) is not dict:
            _fail("SNAPSHOT_EVENT_GRAPH_RECORD_MISSING:" + str(rank))
    _expect_fields(
        snapshot.get("reactive_pair_authority"),
        {
            "observed_pair": "SG:CAE",
            "sample_level_authoritative": True,
            "target_pair_is_only_attachment_for_component_instance": False,
            "reusable_pair_authority": False,
            "ligand_wide_authority": False,
            "cross_structure_generalization": False,
        },
        "SNAPSHOT_PAIR_AUTHORITY_DRIFT",
    )
    context = snapshot.get("context_boundary")
    _expect_fields(
        context,
        {
            "context_merged_into_target_exact3": False,
            "context_only_event_count": 3,
            "context_only_scaleup_ranks": list(CONTEXT_ONLY_RANKS),
            "context_only_events_received_formal_decisions": False,
        },
        "SNAPSHOT_CONTEXT_BOUNDARY_DRIFT",
    )
    context_records = context.get("context_only_records") if type(context) is dict else None
    if (
        type(context_records) is not list
        or [row.get("scaleup_rank") for row in context_records] != list(CONTEXT_ONLY_RANKS)
        or any(row.get("target_event") is not False for row in context_records)
    ):
        _fail("SNAPSHOT_CONTEXT_RECORDS_DRIFT")
    null_state = snapshot.get("role_seed_and_task_null_state")
    _expect_fields(
        null_state,
        {
            "D4_formally_answered": True,
            "D5_formally_answered": True,
            "selected_role_candidate": None,
            "role_profile": None,
            "role_profile_derived_state": "NOT_ESTABLISHED",
            "warhead_atom_ids": None,
            "linker_atom_ids": None,
            "scaffold_atom_ids": None,
            "minimal_seed": None,
            "minimal_seed_atom_ids": None,
            "primary_anchor": None,
            "structurally_applicable_task_ids": None,
            "role_partition_sample_authoritative": False,
            "minimal_seed_sample_authoritative": False,
            "task_applicability_sample_authoritative": False,
            "canonical_mask_structural_labels_available": False,
            "role_runtime_executed": False,
            "seed_runtime_executed": False,
            "task_runtime_executed": False,
        },
        "SNAPSHOT_NULL_AUTHORITY_DRIFT",
    )
    tasks = snapshot.get("canonical_task_contract")
    _expect(tasks, _task_contract(), "SNAPSHOT_TASK_CONTRACT_DRIFT")
    if [row["semantic_long_name"] for row in tasks["global_canonical_tasks"]] != [
        row[1] for row in CANONICAL_TASKS
    ]:
        _fail("SNAPSHOT_CANONICAL_TASK_LONG_NAMES_DRIFT")
    generic = snapshot.get("generic_Exact11_compatibility")
    _expect_fields(
        generic,
        {
            "accepted_fact_count": 3,
            "generic_fact_field_count": 11,
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "source_formal_D2": SOURCE_D2,
            "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "source_formal_D6": SOURCE_D6,
            "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
            "rich_fields_leaked": False,
            "NormalizedDecisionSource_constructed": True,
            "reconciliation_performed": False,
        },
        "SNAPSHOT_GENERIC_DRIFT",
    )
    facts = generic.get("facts") if type(generic) is dict else None
    if type(facts) is not list or len(facts) != 3:
        _fail("SNAPSHOT_GENERIC_FACTS_NOT_EXACT3")
    for fact, event_id in zip(facts, EXPECTED_EVENT_IDS, strict=True):
        if type(fact) is not dict or set(fact) != set(GENERIC_FACT_FIELDS):
            _fail("SNAPSHOT_GENERIC_FACT_NOT_EXACT11")
        _expect_fields(
            fact,
            {
                "canonical_event_id": event_id,
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
                **GENERIC_PROJECTION,
                "source_decision_schema": FORMAL_DECISION_SCHEMA,
                "source_decision_sha256": FORMAL_BINDINGS[0][3],
                "source_binding_path": FORMAL_DECISION_RELATIVE.as_posix(),
            },
            "SNAPSHOT_GENERIC_FACT_DRIFT",
        )
    _expect(snapshot.get("PRE_boundary"), _pre_boundary(), "SNAPSHOT_PRE_DRIFT")
    _expect(snapshot.get("POST_boundary"), _post_boundary(), "SNAPSHOT_POST_DRIFT")
    _expect(
        snapshot.get("training_boundary"),
        _training_boundary(),
        "SNAPSHOT_TRAINING_DRIFT",
    )
    _expect(
        snapshot.get("operation_boundary"),
        _operation_boundary(),
        "SNAPSHOT_OPERATION_DRIFT",
    )
    _expect(snapshot.get("readiness"), _readiness(), "SNAPSHOT_READINESS_DRIFT")


def _validate_summary_semantics(summary: Mapping[str, Any]) -> None:
    _expect_fields(
        summary,
        {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "stage": SCHEMA_VERSION,
            "review_unit": "ME7",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "event_count": 3,
            "review_unit_count": 1,
            "human_review_completed_count": 3,
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "source_formal_D2": SOURCE_D2,
            "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "source_formal_D6": SOURCE_D6,
            "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
            "chemistry_positive_count": 3,
            "negative_chemistry_count": 0,
            "task_not_relevant_count": 3,
            "task_domain_negative_count": 3,
            "training_not_applicable_count": 3,
            "human_training_excluded_count": 0,
            "future_training_admission_candidate_count": 0,
            "pair_sample_authority_count": 3,
            "role_partition_sample_authority_count": 0,
            "minimal_seed_sample_authority_count": 0,
            "task_applicability_sample_authority_count": 0,
            "canonical_structural_label_available_count": 0,
            "task_label_authority_count": 0,
            "event_task_label_rows_materialized_count": 0,
            "mask_tensor_target_count": 0,
            "generic_exact11_accepted_count": 3,
            "generic_exact11_fact_count": 3,
            "rich_fields_leaked_to_generic_facts": False,
            "formal_training_admitted_count": 0,
            "PRE_authority_count": 0,
            "POST_training_authority_count": 0,
            "context_only_event_count": 3,
        },
        "SUMMARY_SEMANTICS_DRIFT",
    )
    _expect(
        summary.get("normalization_contract"),
        _normalization_contract(),
        "SUMMARY_NORMALIZATION_DRIFT",
    )
    _expect(
        summary.get("runtime_non_execution_contract"),
        _runtime_non_execution_contract(),
        "SUMMARY_RUNTIME_BOUNDARY_DRIFT",
    )
    _expect(
        summary.get("operation_boundary"),
        _operation_boundary(),
        "SUMMARY_OPERATION_BOUNDARY_DRIFT",
    )
    _expect(summary.get("readiness"), _readiness(), "SUMMARY_READINESS_DRIFT")


def _reject_dynamic_metadata(value: object, path: str = "root") -> None:
    if type(value) is dict:
        for key, child in value.items():
            lowered = key.lower()
            if any(token in lowered for token in ("timestamp", "hostname", "pid", "uuid")):
                _fail("MANIFEST_DYNAMIC_METADATA_KEY:" + path + "." + key)
            if lowered in {"self_sha256", "manifest_sha256"}:
                _fail("MANIFEST_SELF_SHA256_KEY:" + path + "." + key)
            _reject_dynamic_metadata(child, path + "." + key)
    elif type(value) is list:
        for index, child in enumerate(value):
            _reject_dynamic_metadata(child, f"{path}[{index}]")
    elif type(value) is str and value.startswith("/"):
        _fail("MANIFEST_ABSOLUTE_PATH_VALUE:" + path)


def _validate_manifest_semantics(
    manifest: Mapping[str, Any], repo_root: Path, artifacts: Mapping[str, bytes]
) -> None:
    _expect_fields(
        manifest,
        {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "stage": SCHEMA_VERSION,
            "candidate_publication_file_count": 7,
            "candidate_publication_paths": [
                path.as_posix() for path in CANDIDATE_PUBLICATION_PATHS
            ],
            "output_artifact_count": 4,
            "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
            "active_source_binding_count": 9,
            "semantic_source_identity_count": 9,
            "duplicate_source_binding_identity_count": 0,
            "formal_validator_provenance_identity_only": True,
            "formal_validator_imported": False,
            "formal_validator_executed_by_production": False,
            "formal_validator_subprocessed_by_production": False,
            "formal_semantics_independently_validated": True,
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "manifest_self_SHA256_recorded": False,
        },
        "MANIFEST_ROOT_DRIFT",
    )
    _expect(
        manifest.get("normalization_contract"),
        _normalization_contract(),
        "MANIFEST_NORMALIZATION_DRIFT",
    )
    _expect_exact(
        manifest.get("matrix_contract"),
        {
            "schema_version": MATRIX_SCHEMA_VERSION,
            "header_frozen": True,
            "header": list(MATRIX_HEADER),
            "column_count": len(MATRIX_HEADER),
            "column_types": _matrix_column_types(),
            "boolean_serialization": "lowercase_true_false",
            "json_serialization": "canonical_compact_json",
            "null_json_serialization": "null",
            "nullable_json_empty_string_forbidden": True,
            "rows_are_availability_metadata_not_event_task_label_rows": True,
        },
        "MANIFEST_MATRIX_CONTRACT_DRIFT",
    )
    active = manifest.get("active_source_bindings")
    expected_active = [_binding_record(binding) for binding in ACTIVE_BINDINGS]
    if active != expected_active:
        _fail("MANIFEST_ACTIVE_SOURCE_BINDINGS_DRIFT")
    identities = [row["semantic_source_identity"] for row in active]
    if len(set(identities)) != 9:
        _fail("MANIFEST_DUPLICATE_SOURCE_IDENTITY")
    if manifest.get("candidate_source_bindings") != _candidate_source_records(repo_root):
        _fail("MANIFEST_CANDIDATE_SOURCE_BINDINGS_DRIFT")
    output = manifest.get("output_artifact_bindings_excluding_manifest_self")
    expected_output = [
        {
            "path": (OUTPUT_ROOT_RELATIVE / name).as_posix(),
            "byte_count": len(artifacts[name]),
            "SHA256": _sha256(artifacts[name]),
        }
        for name in (SNAPSHOT, MATRIX, SUMMARY)
    ]
    if output != expected_output:
        _fail("MANIFEST_OUTPUT_BINDINGS_DRIFT")
    if any(row.get("path", "").endswith(MANIFEST) for row in output):
        _fail("MANIFEST_SELF_SHA256_RECORDED")
    _expect(
        manifest.get("runtime_non_execution_contract"),
        _runtime_non_execution_contract(),
        "MANIFEST_RUNTIME_BOUNDARY_DRIFT",
    )
    _expect(
        manifest.get("operation_boundary"),
        _operation_boundary(),
        "MANIFEST_OPERATION_DRIFT",
    )
    _expect(
        manifest.get("training_boundary"),
        _training_boundary(),
        "MANIFEST_TRAINING_DRIFT",
    )
    _expect(manifest.get("readiness"), _readiness(), "MANIFEST_READINESS_DRIFT")
    _reject_dynamic_metadata(manifest)


def validate_completed_decision_projection_v1(
    artifacts: Mapping[str, bytes],
    repo_root: Path,
    *,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Fail closed unless artifacts are the exact deterministic projection."""
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
    _validate_summary_semantics(summary)
    if matrix_header != MATRIX_HEADER or len(matrix_rows) != 3:
        _fail("MATRIX_EXACT3_OR_HEADER_DRIFT")
    expected_matrix = _parse_csv(
        _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot)), "EXPECTED_MATRIX"
    )[1]
    if matrix_rows != expected_matrix:
        _fail("MATRIX_SEMANTICS_DRIFT")
    null_columns = {
        "selected_role_candidate_json",
        "role_profile_raw_json",
        "warhead_atom_ids_json",
        "linker_atom_ids_json",
        "scaffold_atom_ids_json",
        "minimal_seed_json",
        "minimal_seed_atom_ids_json",
        "primary_anchor_json",
        "structurally_applicable_task_ids_json",
    }
    if any(row[column] != "null" for row in matrix_rows for column in null_columns):
        _fail("MATRIX_NULL_SERIALIZATION_DRIFT")
    _validate_manifest_semantics(manifest, Path(repo_root).resolve(), artifacts)
    expected = _build_raw(Path(repo_root).resolve(), repository_path_overrides)
    for name in OUTPUT_FILENAMES:
        if artifacts[name] != expected[name]:
            _fail("ARTIFACT_PROJECTION_DRIFT:" + name)
    return {
        "status": "PASS",
        "event_count": 3,
        "matrix_column_count": len(MATRIX_HEADER),
        "output_artifact_count": 4,
        "generic_exact11_fact_count": 3,
        "FORMAL_SOURCE_D2": SOURCE_D2,
        "NORMALIZED_TASK_RELEVANCE": NORMALIZED_TASK_RELEVANCE,
        "COMPLETED_LANE": EXPECTED_COMPLETED_LANE,
        "LEGACY_COMPLETED_REVIEW_STATUS": EXPECTED_LEGACY_STATUS,
        "CHEMISTRY_DISPOSITION": "POSITIVE",
        "TRAINING_DISPOSITION": NORMALIZED_TRAINING_DISPOSITION,
        "HUMAN_TRAINING_EXCLUDED": False,
        "FUTURE_TRAINING_ADMISSION_CANDIDATE": False,
        "ROLE_PARTITION_SAMPLE_AUTHORITATIVE": False,
        "TASK_APPLICABILITY_SAMPLE_AUTHORITATIVE": False,
        "STRUCTURALLY_APPLICABLE_TASK_IDS": None,
        "TASK_LABEL_AUTHORITY": False,
        "READY_FOR_TRAINING": False,
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
    descriptor, temporary = tempfile.mkstemp(prefix=".covapie_me7_", dir=path.parent)
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
    if live != fresh:
        _fail("MATERIALIZED_BYTES_NOT_FRESH_BUILD")
    return {
        **result,
        "materialized_bytes_equal_fresh_build": True,
        "deterministic_double_build": fresh == build_artifacts_v1(root),
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    print(
        json.dumps(
            materialize_artifacts_v1(repo_root), ensure_ascii=False, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
