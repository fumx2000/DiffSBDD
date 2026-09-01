"""Ingest frozen 1N0 task-domain-negative authority as deterministic metadata.

This additive owner independently validates the finalized 1N0 Exact4 human
decision.  It preserves raw structural evidence separately from the narrow
sample-level task-relevance authority.  It does not execute the frozen formal
validator, create chemistry/pair/role/mask/training authority, reconcile or
refresh global state, admit or tensorize samples, or train a model.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
import copy
import csv
import hashlib
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
    "OneN0IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)


SCHEMA_VERSION = "covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_1n0_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_1n0_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_1n0_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_1n0_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_1n0_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_1n0_event_task_label_availability_v1.csv"
SUMMARY = "covapie_1n0_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_1n0_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

FORMAL_ROOT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "1N0_COVAPIE_BULK_REVIEW_UNIT_80FE8023FD901B01/"
    "formal-human-decision-v1"
)
FORMAL_DECISION_RELATIVE = FORMAL_ROOT / "1n0_formal_human_decision_v1.json"
FORMAL_VALIDATOR_RELATIVE = FORMAL_ROOT / "validate_1n0_formal_human_decision_v1.py"

SOURCE_BINDING_POLICY_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
CANONICAL_TASK_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
GENERIC_RECONCILIATION_RELATIVE = Path(
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py"
)
CENSUS_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_with_i12_v1.py"
)
CENSUS_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_i12_v1"
)
CENSUS_MATRIX_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_census_with_i12_v1.csv"
)
CENSUS_SUMMARY_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_summary_with_i12_v1.json"
)
CENSUS_MANIFEST_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_manifest_with_i12_v1.json"
)

FORMAL_DECISION_SCHEMA = (
    "covapie_1n0_exact4_task_domain_negative_formal_human_decision_v1"
)
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "672c75f73e526f66f738695cc451c02381a68ba460cb8e8939173179f94b79a5"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_80FE8023FD901B01"
AUTHORITY_SOURCE = "FORMAL_1N0_TASK_DOMAIN_NEGATIVE_HUMAN_DECISION"
AUTHORITY_SCOPE = "1N0_EXACT4_TASK_RELEVANCE_ONLY"
PRE_STATUS = "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"

EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:4JWS:C:CYS:73-:SG:G:1N0:C16",
        775, "4JWS", "C", "CYS:73-", "G", "covale2",
        1.793126, "1.793126", 1.793,
        "covale1", "A", "HIS:355-", "NE2", "HIS_NE2", 1.508,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4JWS:D:CYS:73-:SG:J:1N0:C16",
        776, "4JWS", "D", "CYS:73-", "J", "covale4",
        1.798644, "1.798644", 1.799,
        "covale3", "B", "HIS:355-", "NE2", "HIS_NE2", 1.508,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4JWU:C:CYS:19-:SG:G:1N0:C16",
        778, "4JWU", "C", "CYS:19-", "G", "covale2",
        1.800281, "1.800281", 1.8,
        "covale1", "A", "CYS:344-", "SG", "CYS_SG", 1.819,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4JX1:G:CYS:19-:SG:U:1N0:C16",
        780, "4JX1", "G", "CYS:19-", "U", "covale2",
        1.794709, "1.794709", 1.795,
        "covale1", "E", "CYS:344-", "SG", "CYS_SG", 1.815,
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)
EXCLUDED_C2_RANKS = (777, 779)

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

GENERIC_PROJECTION = {
    "human_review_completed": True,
    "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
    "task_relevance_disposition": "NOT_RELEVANT",
    "chemistry_disposition": "NOT_ESTABLISHED",
    "training_disposition": "NOT_APPLICABLE",
    "human_training_excluded": False,
}
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

# path, namespace, byte count, SHA256, executable class, source role
FORMAL_BINDINGS = (
    (
        FORMAL_DECISION_RELATIVE,
        "project_parent_relative",
        26236,
        "45c337b2b8e0f85ea7a06eb16bd5f55ec729429285226a77bbb0c4a2f1301a34",
        False,
        "ONE_N0_FROZEN_FORMAL_HUMAN_DECISION",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE,
        "project_parent_relative",
        53387,
        "3006362e511ae09beaab1e5c38d73e90961795b4bfcccb0740cb91b0b3a4c434",
        False,
        "ONE_N0_FROZEN_FORMAL_VALIDATOR_PROVENANCE_IDENTITY_ONLY",
    ),
)
POLICY_BINDING = (
    SOURCE_BINDING_POLICY_RELATIVE,
    "repository_relative",
    3704,
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    False,
    "PUBLISHED_SOURCE_BINDING_POLICY_V2",
)
SEMANTIC_BINDINGS = (
    (
        CANONICAL_TASK_OWNER_RELATIVE,
        "repository_relative",
        67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        False,
        "PUBLISHED_CANONICAL_EXACT5_SEMANTIC_OWNER",
    ),
    (
        GENERIC_RECONCILIATION_RELATIVE,
        "repository_relative",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
        False,
        "PUBLISHED_GENERIC_COMPLETED_DECISION_RECONCILIATION_CONTRACT",
    ),
)
CENSUS_BINDINGS = (
    (
        CENSUS_OWNER_RELATIVE,
        "repository_relative",
        71565,
        "42b01060024cf4c92e19bf3804c6440522019082ab6ec5fda89f5b7258e243b4",
        False,
        "CURRENT_WITH_I12_CENSUS_OWNER",
    ),
    (
        CENSUS_MATRIX_RELATIVE,
        "repository_relative",
        532022,
        "f659b6c9d9475c94aa4bf2234053627d28a58d4b7f6ae424f49a18924c1ac3bf",
        False,
        "CURRENT_WITH_I12_CENSUS_MATRIX",
    ),
    (
        CENSUS_SUMMARY_RELATIVE,
        "repository_relative",
        17549,
        "76d91f101898d8ba6c46de69be866e1408cbb9e630562906a52435a18e31d6b1",
        False,
        "CURRENT_WITH_I12_CENSUS_SUMMARY",
    ),
    (
        CENSUS_MANIFEST_RELATIVE,
        "repository_relative",
        51041,
        "d22c388f7da5fecede11df15e3bc188196328e24009ad9363932bebc971da150",
        False,
        "CURRENT_WITH_I12_CENSUS_MANIFEST",
    ),
)
ACTIVE_BINDINGS = (*FORMAL_BINDINGS, POLICY_BINDING, *SEMANTIC_BINDINGS, *CENSUS_BINDINGS)

_Binding = tuple[Path, str, int, str, bool, str]
_FORBIDDEN_LIVE_IDENTITY_FIELDS = {
    "mode", "required_mode", "expected_mode", "filesystem_mode", "posix_mode",
}


class OneN0IngestionSafetyError(ValueError):
    """Raised whenever the 1N0 ingestion contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise OneN0IngestionSafetyError("COVAPIE_1N0_INGESTION_V1_ERROR:" + reason)


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


def _exact(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        return set(actual) == set(expected) and all(  # type: ignore[arg-type]
            _exact(actual[key], expected[key]) for key in expected  # type: ignore[index]
        )
    if type(expected) is list:
        return len(actual) == len(expected) and all(  # type: ignore[arg-type]
            _exact(left, right)
            for left, right in zip(actual, expected)  # type: ignore[arg-type]
        )
    return actual == expected


def _expect(actual: object, expected: object, reason: str) -> None:
    if not _exact(actual, expected):
        _fail(reason)


def _strict_json_loads(payload: bytes, label: str) -> dict[str, Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise OneN0IngestionSafetyError(
            "COVAPIE_1N0_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label
        ) from error

    def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                _fail("JSON_DUPLICATE_KEY:" + label + ":" + key)
            result[key] = value
        return result

    def reject_constant(value: str) -> NoReturn:
        _fail("JSON_NONFINITE_NUMBER:" + label + ":" + value)

    try:
        parsed = json.loads(
            text,
            object_pairs_hook=unique_pairs,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as error:
        raise OneN0IngestionSafetyError(
            "COVAPIE_1N0_INGESTION_V1_ERROR:JSON_PARSE_FAILED:" + label
        ) from error
    if type(parsed) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return parsed


def _binding_record(binding: _Binding) -> dict[str, object]:
    relative, namespace, byte_count, digest, executable, source_role = binding
    return {
        "path": relative.as_posix(),
        "namespace": namespace,
        "byte_count": byte_count,
        "SHA256": digest,
        "expected_executable_class": "EXECUTABLE" if executable else "NON_EXECUTABLE",
        "source_role": source_role,
    }


def _binding_records(bindings: Sequence[_Binding]) -> list[dict[str, object]]:
    return [_binding_record(binding) for binding in bindings]


def _normalize_overrides(
    overrides: Mapping[Path, Path] | None,
) -> dict[Path, Path]:
    normalized: dict[Path, Path] = {}
    for raw_relative, raw_replacement in (overrides or {}).items():
        relative = Path(raw_relative)
        if relative.is_absolute() or ".." in relative.parts or relative in normalized:
            _fail("SOURCE_OVERRIDE_KEY_INVALID")
        normalized[relative] = Path(raw_replacement)
    return normalized


def _resolve_binding_path(
    repo_root: Path,
    binding: _Binding,
    overrides: Mapping[Path, Path],
) -> Path:
    relative, namespace, _count, _digest, _executable, _role = binding
    if relative.is_absolute() or ".." in relative.parts:
        _fail("SOURCE_BINDING_PATH_INVALID")
    if relative in overrides:
        replacement = overrides[relative]
        return replacement if replacement.is_absolute() else repo_root / replacement
    if namespace == "repository_relative":
        return repo_root / relative
    if namespace == "project_parent_relative":
        return repo_root.parent / relative
    _fail("SOURCE_BINDING_NAMESPACE_INVALID:" + namespace)


def _verify_binding(
    repo_root: Path,
    binding: _Binding,
    overrides: Mapping[Path, Path],
) -> bytes:
    relative, _namespace, byte_count, digest, executable, source_role = binding
    path = _resolve_binding_path(repo_root, binding, overrides)
    try:
        return verify_bound_source_v2(
            path=path,
            expected_byte_count=byte_count,
            expected_sha256=digest,
            label=source_role + ":" + relative.as_posix(),
            expected_executable=executable,
        )
    except SourceBindingPolicyV2Error as error:
        raise OneN0IngestionSafetyError(
            "COVAPIE_1N0_INGESTION_V1_ERROR:BOUND_SOURCE_REJECTED:" + source_role
        ) from error


def _verify_bindings(
    repo_root: Path,
    bindings: Sequence[_Binding],
    overrides: Mapping[Path, Path],
) -> dict[Path, bytes]:
    return {
        binding[0]: _verify_binding(repo_root, binding, overrides)
        for binding in bindings
    }


def _literal_assignments(
    payload: bytes, names: Sequence[str], label: str
) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8"), filename=label)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise OneN0IngestionSafetyError(
            "COVAPIE_1N0_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
        ) from error
    wanted = set(names)
    values: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
            value = node.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    values[target.id] = ast.literal_eval(value)
                except (TypeError, ValueError) as error:
                    raise OneN0IngestionSafetyError(
                        "COVAPIE_1N0_INGESTION_V1_ERROR:"
                        "SEMANTIC_OWNER_LITERAL_INVALID:" + target.id
                    ) from error
    if set(values) != wanted:
        _fail("SEMANTIC_OWNER_LITERAL_MISSING:" + label)
    return values


def _generic_fact_fields(payload: bytes) -> tuple[str, ...]:
    try:
        tree = ast.parse(
            payload.decode("utf-8"),
            filename=GENERIC_RECONCILIATION_RELATIVE.as_posix(),
        )
    except (UnicodeDecodeError, SyntaxError) as error:
        raise OneN0IngestionSafetyError(
            "COVAPIE_1N0_INGESTION_V1_ERROR:GENERIC_OWNER_AST_INVALID"
        ) from error
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "NormalizedCompletedDecisionFact":
            return tuple(
                item.target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
            )
    _fail("GENERIC_FACT_CLASS_MISSING")


def _validate_semantic_owners(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    canonical = _literal_assignments(
        payloads[CANONICAL_TASK_OWNER_RELATIVE],
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
        CANONICAL_TASK_OWNER_RELATIVE.as_posix(),
    )
    _expect(
        canonical["EXACT3_ROLES"],
        ("scaffold", "linker", "warhead"),
        "EXACT3_ROLE_OWNER_DRIFT",
    )
    _expect(canonical["CANONICAL_TASKS"], CANONICAL_TASKS, "CANONICAL_EXACT5_OWNER_DRIFT")

    generic = _literal_assignments(
        payloads[GENERIC_RECONCILIATION_RELATIVE],
        (
            "COMPLETED_HUMAN_NEGATIVE",
            "TASK_NOT_RELEVANT",
            "CHEMISTRY_NOT_ESTABLISHED",
            "TRAINING_NOT_APPLICABLE",
        ),
        GENERIC_RECONCILIATION_RELATIVE.as_posix(),
    )
    _expect(
        generic,
        {
            "COMPLETED_HUMAN_NEGATIVE": "COMPLETED_HUMAN_NEGATIVE",
            "TASK_NOT_RELEVANT": "NOT_RELEVANT",
            "CHEMISTRY_NOT_ESTABLISHED": "NOT_ESTABLISHED",
            "TRAINING_NOT_APPLICABLE": "NOT_APPLICABLE",
        },
        "GENERIC_COMPLETED_NEGATIVE_VOCABULARY_DRIFT",
    )
    _expect(
        _generic_fact_fields(payloads[GENERIC_RECONCILIATION_RELATIVE]),
        GENERIC_FACT_FIELDS,
        "GENERIC_FACT_SCHEMA_DRIFT",
    )
    return {
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "sample_authoritative_applicable_task_ids": None,
        "generic_completed_negative_projection": copy.deepcopy(GENERIC_PROJECTION),
    }


def _semantic_digest(formal: Mapping[str, Any]) -> str:
    clone = copy.deepcopy(dict(formal))
    digest = clone.pop("formal_semantic_canonical_sha256", None)
    if type(digest) is not str:
        _fail("FORMAL_SEMANTIC_DIGEST_FIELD_INVALID")
    return _sha256(_canonical_json(clone))


def _validate_formal_document(formal: Mapping[str, Any]) -> None:
    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(
        formal.get("formal_semantic_canonical_sha256"),
        FORMAL_SEMANTIC_CANONICAL_SHA256,
        "FORMAL_SEMANTIC_DIGEST_LITERAL_DRIFT",
    )
    if _semantic_digest(formal) != FORMAL_SEMANTIC_CANONICAL_SHA256:
        _fail("FORMAL_SEMANTIC_DIGEST_RECOMPUTE_FAILED")
    for key, expected in (
        ("approved", True),
        ("unsigned", False),
        ("decision_finalized", True),
        ("human_review_completed", True),
        ("human_decision_created", True),
        ("formal_authority_created", True),
    ):
        _expect(formal.get(key), expected, "FORMAL_FINALIZATION_DRIFT:" + key)

    human = formal.get("human_authorization")
    unit = formal.get("unit_human_decision")
    context = formal.get("human_approved_context")
    if type(human) is not dict or type(unit) is not dict or type(context) is not dict:
        _fail("FORMAL_HUMAN_DECISION_SECTION_INVALID")
    decisions = {
        "D1_task_relevance": "NOT_RELEVANT",
        "D2_chemistry": "UNRESOLVED",
        "D3_reactive_pair": "UNRESOLVED",
        "D4_role_candidate": "UNRESOLVED",
        "D5_training_use": "UNRESOLVED",
    }
    for key, expected in decisions.items():
        _expect(human.get(key), expected, "FORMAL_HUMAN_DECISION_DRIFT:" + key)
        _expect(unit.get(key), expected, "FORMAL_UNIT_DECISION_DRIFT:" + key)
    if human.get("reviewer_id") != "fmx" or human.get("attestor_id") != "fmx":
        _fail("FORMAL_REVIEWER_OR_ATTESTOR_DRIFT")
    d6 = human.get("D6_scientific_context")
    if type(d6) is not str or d6 != unit.get("D6_scientific_context") or d6 != context.get(
        "D6_scientific_context"
    ):
        _fail("FORMAL_D6_TEXT_DRIFT")
    d6_bytes = d6.encode("utf-8")
    if len(d6_bytes) != 657 or _sha256(d6_bytes) != (
        "d51bd3139a9ad85d285ce81e26caf4e6c9b45e447f8e3f90e6c6612d14c7d689"
    ):
        _fail("FORMAL_D6_IDENTITY_DRIFT")

    identity = formal.get("identity")
    if type(identity) is not dict:
        _fail("FORMAL_IDENTITY_INVALID")
    expected_identity = {
        "canonical_event_ids": list(EXPECTED_EVENT_IDS),
        "completed_human_review_event_count": 4,
        "duplicate_event_count": 0,
        "exact_event_count": 4,
        "extra_event_count": 0,
        "ligand_component_id": "1N0",
        "missing_event_count": 0,
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "scaleup_ranks": list(EXPECTED_RANKS),
        "separate_review_unit_C2_event_ranks": list(EXCLUDED_C2_RANKS),
        "target_ligand_atom": "C16",
        "target_protein_atom": "SG",
        "unique_event_count": 4,
    }
    for key, expected in expected_identity.items():
        _expect(identity.get(key), expected, "FORMAL_IDENTITY_DRIFT:" + key)

    events = formal.get("event_level_human_decisions")
    if type(events) is not list or len(events) != 4:
        _fail("FORMAL_EVENT_COUNT_NOT_EXACT4")
    for event, expected in zip(events, EXPECTED_EVENTS):
        if type(event) is not dict:
            _fail("FORMAL_EVENT_NOT_OBJECT")
        checks = {
            "canonical_event_id": expected[0],
            "scaleup_rank": expected[1],
            "pdb_id": expected[2],
            "target_protein_asym": expected[3],
            "target_cys_residue_id": expected[4],
            "ligand_asym": expected[5],
            "primary_connection_id": expected[6],
            "calculated_POST_distance_angstrom": expected[7],
            "reported_POST_distance_angstrom": expected[9],
            "second_endpoint_connection_id": expected[10],
            "second_endpoint_protein_asym": expected[11],
            "second_endpoint_residue_id": expected[12],
            "second_endpoint_protein_atom": expected[13],
            "second_endpoint_protein_chemistry_class": expected[14],
            "second_endpoint_reported_distance_angstrom": expected[15],
            "model_number": 1,
            "ligand_component_id": "1N0",
            "target_protein_atom": "SG",
            "target_ligand_atom": "C16",
            "task_relevance_decision": "NOT_RELEVANT",
            "D2_chemistry": "UNRESOLVED",
            "D3_reactive_pair": "UNRESOLVED",
            "D4_role_candidate": "UNRESOLVED",
            "D5_training_use": "UNRESOLVED",
            "explicit_covalent_evidence": True,
            "task_relevance_human_authoritative": True,
            "chemistry_human_authoritative": False,
            "reactive_pair_human_authoritative": False,
            "role_partition_human_authoritative": False,
            "training_only_exclusion_human_authoritative": False,
            "formal_training_admitted": False,
        }
        for key, value in checks.items():
            _expect(event.get(key), value, "FORMAL_EVENT_DRIFT:" + key)

    crosslink = formal.get("bifunctional_crosslinker_context")
    if type(crosslink) is not dict:
        _fail("FORMAL_CROSSLINK_CONTEXT_INVALID")
    for key, expected in (
        ("BIFUNCTIONAL_CROSSLINKER_CONTEXT", True),
        ("SECOND_EXPLICIT_COVALENT_ENDPOINT_PRESENT_IN_ALL_4_EVENTS", True),
        ("C2_events_added_to_target_C16_Exact4", False),
        ("second_endpoint_evidence_count", 4),
        ("second_endpoint_ligand_atom", "C2"),
        ("separate_review_unit_C2_event_ranks", list(EXCLUDED_C2_RANKS)),
    ):
        _expect(crosslink.get(key), expected, "FORMAL_CROSSLINK_DRIFT:" + key)

    projection = formal.get("expected_downstream_normalized_projection")
    if type(projection) is not dict:
        _fail("FORMAL_GENERIC_PROJECTION_INVALID")
    projection_keys = {
        "human_review_completed": True,
        "legacy_completed_status": "COMPLETED_HUMAN_NEGATIVE",
        "task_relevance_disposition": "NOT_RELEVANT",
        "chemistry_disposition": "NOT_ESTABLISHED",
        "training_disposition": "NOT_APPLICABLE",
        "human_training_excluded": False,
    }
    for key, expected in projection_keys.items():
        _expect(projection.get(key), expected, "FORMAL_GENERIC_PROJECTION_DRIFT:" + key)

    authority = formal.get("authority_boundary")
    if type(authority) is not dict:
        _fail("FORMAL_AUTHORITY_BOUNDARY_INVALID")
    true_authorities = (
        "sample_level_formal_human_decision_authority_created",
        "sample_level_task_relevance_authority_created",
        "sample_level_task_domain_negative_authority_created",
    )
    false_authorities = (
        "canonical_mask_structural_labels_human_authority",
        "chemical_warhead_human_authority",
        "chemistry_negative_authority",
        "chemistry_positive_authority",
        "formal_split_authority",
        "formal_training_admitted",
        "future_training_admission_candidate",
        "POST_geometry_training_authority_created",
        "PRE_geometry_authority_created",
        "PRE_topology_authority_created",
        "reaction_family_authority",
        "reactive_pair_human_authority",
        "reusable_chemistry_authority",
        "role_partition_human_authority",
        "task_applicability_authority",
        "tensor_target_created",
        "training_admission_created",
        "training_only_exclusion_authority",
        "warhead_family_authority",
        "warhead_rule_authority",
        "warhead_type_authority",
    )
    for key in true_authorities:
        _expect(authority.get(key), True, "FORMAL_REQUIRED_AUTHORITY_MISSING:" + key)
    for key in false_authorities:
        _expect(authority.get(key), False, "FORMAL_UNAUTHORIZED_AUTHORITY_PRESENT:" + key)

    chemistry = formal.get("chemistry_authority_boundary")
    reactive = formal.get("reactive_pair_boundary")
    role = formal.get("role_authority_boundary")
    training = formal.get("training_boundary")
    prepost = formal.get("PRE_POST_boundary")
    lifecycle = formal.get("validator_lifecycle")
    if any(type(section) is not dict for section in (chemistry, reactive, role, training, prepost, lifecycle)):
        _fail("FORMAL_BOUNDARY_SECTION_INVALID")
    if (
        chemistry.get("task_domain_negative") is not True
        or chemistry.get("negative_chemistry") is not False
        or reactive.get("reactive_pair_raw_structural_evidence") is not True
        or reactive.get("reactive_pair_human_authority") is not False
        or role.get("global_canonical_mask_task_count") != 5
        or role.get("B3_present") is not True
        or role.get("sixth_task_present") is not False
        or role.get("sample_authoritative_applicable_task_ids") is not None
        or role.get("role_partition_human_authority") is not False
        or training.get("human_training_excluded") is not False
        or training.get("training_use_include") is not False
        or training.get("future_training_admission_candidate") is not False
        or training.get("training_materialization_allowed_now") is not False
        or prepost.get("POST_source_evidence_available") is not True
        or prepost.get("POST_geometry_training_authority_created") is not False
        or prepost.get("PRE_status") != PRE_STATUS
        or prepost.get("PRE_topology_authority_created") is not False
        or prepost.get("PRE_geometry_authority_created") is not False
        or lifecycle.get("validator_postbaseline_runtime_dependency_allowed") is not False
        or lifecycle.get("future_ingestion_must_independently_validate_semantics") is not True
    ):
        _fail("FORMAL_NEGATIVE_AUTHORITY_BOUNDARY_DRIFT")


def _current_census_boundary(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    summary = _strict_json_loads(
        payloads[CENSUS_SUMMARY_RELATIVE], "CURRENT_WITH_I12_CENSUS_SUMMARY"
    )
    _strict_json_loads(
        payloads[CENSUS_MANIFEST_RELATIVE], "CURRENT_WITH_I12_CENSUS_MANIFEST"
    )
    try:
        rows = list(
            csv.DictReader(
                io.StringIO(payloads[CENSUS_MATRIX_RELATIVE].decode("utf-8"))
            )
        )
    except UnicodeDecodeError as error:
        raise OneN0IngestionSafetyError(
            "COVAPIE_1N0_INGESTION_V1_ERROR:CURRENT_CENSUS_UTF8_INVALID"
        ) from error
    if len(rows) != 1000 or len({row.get("canonical_event_id") for row in rows}) != 1000:
        _fail("CURRENT_CENSUS_UNIVERSE_DRIFT")
    one_n0_rows = [row for row in rows if row.get("ligand_component_id") == "1N0"]
    if len(one_n0_rows) != 6:
        _fail("CURRENT_CENSUS_1N0_EXACT6_DRIFT")
    target_rows = [row for row in one_n0_rows if row.get("review_unit_id") == EXPECTED_REVIEW_UNIT_ID]
    if (
        tuple(row.get("canonical_event_id") for row in target_rows) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in target_rows) != EXPECTED_RANKS
    ):
        _fail("CURRENT_CENSUS_1N0_TARGET_EXACT4_DRIFT")
    excluded_rows = [row for row in one_n0_rows if int(row["scaleup_rank"]) in EXCLUDED_C2_RANKS]
    if len(excluded_rows) != 2 or any(
        row.get("review_unit_id") == EXPECTED_REVIEW_UNIT_ID for row in excluded_rows
    ):
        _fail("CURRENT_CENSUS_1N0_C2_BOUNDARY_DRIFT")
    prior = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false",
        "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "structurally_applicable_task_ids_json": "null",
    }
    for row in one_n0_rows:
        if any(row.get(key) != value for key, value in prior.items()):
            _fail("CURRENT_CENSUS_1N0_PRIOR_STATE_DRIFT")
    human = summary.get("human_review")
    exact5 = summary.get("canonical_exact5")
    if type(human) is not dict or type(exact5) is not dict:
        _fail("CURRENT_CENSUS_SUMMARY_BOUNDARY_INVALID")
    if (
        human.get("completed_event_count") != 123
        or human.get("completed_unit_count") != 18
        or human.get("unreviewed_event_count") != 215
        or human.get("unreviewed_unit_count") != 113
        or exact5.get("task_count") != 5
        or exact5.get("B3_present") is not True
        or exact5.get("sixth_task_present") is not False
    ):
        _fail("CURRENT_CENSUS_SUMMARY_DRIFT")
    return {
        "universe_event_count": 1000,
        "one_n0_total_event_count": 6,
        "one_n0_target_review_unit_event_count": 4,
        "one_n0_separate_C2_review_unit_event_count": 2,
        "one_n0_target_prior_status": "CURRENTLY_UNREVIEWED",
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
    }


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Bind Exact9 inputs and independently validate the frozen 1N0 decision."""

    root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    allowed = {binding[0] for binding in ACTIVE_BINDINGS}
    if set(overrides) - allowed:
        _fail("SOURCE_OVERRIDE_NOT_AUTHORIZED")
    payloads = _verify_bindings(root, ACTIVE_BINDINGS, overrides)
    formal = _strict_json_loads(
        payloads[FORMAL_DECISION_RELATIVE], "ONE_N0_FROZEN_FORMAL_DECISION"
    )
    _validate_formal_document(formal)
    semantics = _validate_semantic_owners(payloads)
    census = _current_census_boundary(payloads)
    return {
        "active_source_bindings": _binding_records(ACTIVE_BINDINGS),
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "source_binding_policy_binding": _binding_record(POLICY_BINDING),
        "semantic_owner_bindings": _binding_records(SEMANTIC_BINDINGS),
        "current_census_bindings": _binding_records(CENSUS_BINDINGS),
        "semantic_contract": semantics,
        "current_census_boundary": census,
        "formal": formal,
    }


def _task_authority_vector() -> list[dict[str, object]]:
    return [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "authoritative_label_available": False,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]


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
        "B3_present": True,
        "sixth_task_present": False,
        "sample_authoritative_applicable_task_ids": None,
        "event_task_authority_availability": _task_authority_vector(),
        "role_partition_human_authority": False,
        "canonical_mask_structural_labels_human_authority": False,
    }


def _chemistry_boundary() -> dict[str, object]:
    return {
        "D2_human_choice": "UNRESOLVED",
        "chemistry_disposition": "NOT_ESTABLISHED",
        "chemistry_known_positive": False,
        "negative_chemistry": False,
        "sample_level_chemistry_positive_authority": False,
        "sample_level_chemistry_negative_authority": False,
        "chemical_warhead_human_authoritative": False,
        "chemical_warhead_atom_ids": None,
        "reaction_family_authority": False,
        "warhead_family_authority": False,
        "warhead_rule_authority": False,
        "warhead_type_authority": False,
        "reusable_chemistry_authority": False,
        "supporting_source_labels": ["Crosslinker", "linker", "Acrylamide"],
        "supporting_source_labels_are_evidence_only": True,
    }


def _role_boundary() -> dict[str, object]:
    return {
        "D4_human_choice": "UNRESOLVED",
        "role_partition_human_decision_available": False,
        "role_partition_human_authoritative": False,
        "selected_role_candidate_index_0based": None,
        "role_profile": None,
        "warhead_atom_ids": None,
        "linker_atom_ids": None,
        "scaffold_atom_ids": None,
        "boundary_bonds": None,
        "sample_authoritative_applicable_task_ids": None,
        "canonical_mask_structural_labels_human_authority": False,
    }


def _geometry_boundary() -> dict[str, object]:
    return {
        "POST_source_evidence_available": True,
        "POST_source_evidence_count": 4,
        "POST_sample_authority": False,
        "POST_geometry_training_authority_available": False,
        "POST_geometry_training_target_available_now": False,
        "PRE_status": PRE_STATUS,
        "PRE_source_graph_mapping_count": 0,
        "PRE_topology_authority_available": False,
        "PRE_geometry_authority_available": False,
        "PRE_reconstruction_performed": False,
        "PRE_mapping_repair_performed": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_zero_fill_performed": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "D5_human_choice": "UNRESOLVED",
        "training_disposition": "NOT_APPLICABLE",
        "training_use_human_decision_available": False,
        "training_use_allowed": False,
        "training_use_include": False,
        "human_training_excluded": False,
        "training_only_exclusion_human_authoritative": False,
        "candidate_for_future_training_admission": False,
        "future_training_admission_candidate": False,
        "training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed_now": False,
        "formal_split_authority_created": False,
        "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "ready_for_training": False,
    }


def _authority_boundary() -> dict[str, object]:
    return {
        "authority_source": AUTHORITY_SOURCE,
        "authority_scope": AUTHORITY_SCOPE,
        "authority_ingested": True,
        "authority_created_by_this_ingestion": False,
        "human_authority_created_by_this_ingestion": False,
        "scientific_authority_created_by_this_ingestion": False,
        "sample_level_task_relevance_authority": True,
        "sample_level_task_domain_negative_authority": True,
        "whole_row_scientific_authority": False,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "training_started": False,
        "ready_for_training": False,
        "feature_semantics_audit_required_later": True,
        "Step12D": "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "commit_performed": False,
        "push_performed": False,
    }


def _generic_fact(event_id: str) -> dict[str, object]:
    return {
        "canonical_event_id": event_id,
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        **copy.deepcopy(GENERIC_PROJECTION),
        "source_decision_schema": FORMAL_DECISION_SCHEMA,
        "source_decision_sha256": FORMAL_BINDINGS[0][3],
        "source_binding_path": FORMAL_DECISION_RELATIVE.as_posix(),
    }


def _event_projection(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "canonical_event_id": row[0],
        "scaleup_rank": row[1],
        "pdb_id": row[2],
        "model_number": 1,
        "protein_chain_or_asym": row[3],
        "cys_residue_id": row[4],
        "ligand_component_id": "1N0",
        "ligand_chain_or_asym": row[5],
        "primary_connection_id": row[6],
        "observed_POST_distance_angstrom": row[7],
        "observed_POST_distance_frozen_lexeme": row[8],
        "reported_POST_distance_angstrom": row[9],
        "explicit_covalent_evidence": True,
        "raw_structural_reactive_pair_evidence": True,
        "observed_protein_reactive_atom": "SG",
        "observed_ligand_reactive_atom": "C16",
        "second_endpoint_present": True,
        "second_endpoint_ligand_atom": "C2",
        "second_endpoint_connection_id": row[10],
        "second_endpoint_protein_asym": row[11],
        "second_endpoint_residue_id": row[12],
        "second_endpoint_protein_atom": row[13],
        "second_endpoint_protein_chemistry_class": row[14],
        "second_endpoint_reported_distance_angstrom": row[15],
        "second_endpoint_is_target_event": False,
        "human_task_relevance_decision": "NOT_RELEVANT",
        "task_relevance_human_authoritative": True,
        "task_domain_negative": True,
        "D2_human_choice": "UNRESOLVED",
        "D3_human_choice": "UNRESOLVED",
        "D4_human_choice": "UNRESOLVED",
        "D5_human_choice": "UNRESOLVED",
        "chemistry_human_authoritative": False,
        "reactive_pair_human_decision_available": False,
        "reactive_pair_human_authoritative": False,
        "role_partition_human_decision_available": False,
        "role_partition_human_authoritative": False,
        "training_use_human_decision_available": False,
        "training_only_exclusion_human_authoritative": False,
        "selected_role_candidate_index_0based": None,
        "role_profile": None,
        "warhead_atom_ids": None,
        "linker_atom_ids": None,
        "scaffold_atom_ids": None,
        "boundary_bonds": None,
        "sample_authoritative_applicable_task_ids": None,
        "task_authority_availability": _task_authority_vector(),
        **copy.deepcopy(GENERIC_PROJECTION),
        **_chemistry_boundary(),
        **_geometry_boundary(),
        **_training_boundary(),
        **_authority_boundary(),
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    formal = bound["formal"]
    human = formal["human_authorization"]  # type: ignore[index]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "ONE_N0_TASK_DOMAIN_NEGATIVE_COMPLETED_DECISION_INGESTION_PROJECTION",
        "active_source_binding_count": 9,
        "active_source_bindings": bound["active_source_bindings"],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "source_binding_policy_binding": bound["source_binding_policy_binding"],
        "semantic_owner_bindings": bound["semantic_owner_bindings"],
        "current_census_bindings": bound["current_census_bindings"],
        "identity": {
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "ligand_component_id": "1N0",
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "scaleup_ranks": list(EXPECTED_RANKS),
            "event_count": 4,
            "unique_event_count": 4,
            "duplicate_event_count": 0,
            "missing_event_count": 0,
            "extra_event_count": 0,
            "separate_review_unit_C2_event_ranks": list(EXCLUDED_C2_RANKS),
        },
        "human_decision": {
            "approved": True,
            "approved_is_formal_decision_finalization_only": True,
            "approved_is_chemistry_approval": False,
            "approved_is_pair_approval": False,
            "approved_is_role_approval": False,
            "approved_is_training_approval": False,
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "D1_task_relevance": "NOT_RELEVANT",
            "D2_chemistry": "UNRESOLVED",
            "D3_reactive_pair": "UNRESOLVED",
            "D4_role_candidate": "UNRESOLVED",
            "D5_training_use": "UNRESOLVED",
            "D6_scientific_context": human["D6_scientific_context"],  # type: ignore[index]
            "D6_utf8_byte_count": 657,
            "D6_utf8_sha256": (
                "d51bd3139a9ad85d285ce81e26caf4e6c9b45e447f8e3f90e6c6612d14c7d689"
            ),
        },
        "events": [_event_projection(row) for row in EXPECTED_EVENTS],
        "normalized_completed_negative_facts": [
            _generic_fact(event_id) for event_id in EXPECTED_EVENT_IDS
        ],
        "raw_structural_evidence_boundary": {
            "raw_structural_evidence_available": True,
            "raw_structural_evidence_event_count": 4,
            "raw_structural_reactive_pair_evidence": True,
            "raw_evidence_promoted_to_human_authority": False,
            "POST_source_evidence_available": True,
        },
        "bifunctional_crosslinker_context": {
            "BIFUNCTIONAL_CROSSLINKER_CONTEXT": True,
            "SECOND_EXPLICIT_COVALENT_ENDPOINT_PRESENT_IN_ALL_4_EVENTS": True,
            "second_endpoint_ligand_atom": "C2",
            "second_endpoint_protein_chemistry_classes": [
                "HIS_NE2", "HIS_NE2", "CYS_SG", "CYS_SG"
            ],
            "second_endpoint_is_separate_target_event_set": False,
            "separate_review_unit_C2_event_ranks": list(EXCLUDED_C2_RANKS),
        },
        "canonical_task_contract": _canonical_task_contract(),
        "chemistry_authority_boundary": _chemistry_boundary(),
        "role_authority_boundary": _role_boundary(),
        "geometry_boundary": _geometry_boundary(),
        "training_boundary": _training_boundary(),
        "authority_boundary": _authority_boundary(),
        "current_census_boundary": bound["current_census_boundary"],
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "pdb_id", "model_number",
    "protein_chain_or_asym", "cys_residue_id", "ligand_component_id",
    "ligand_chain_or_asym", "primary_connection_id",
    "observed_POST_distance_angstrom", "explicit_covalent_evidence",
    "raw_structural_reactive_pair_evidence", "observed_protein_reactive_atom",
    "observed_ligand_reactive_atom", "second_endpoint_present",
    "second_endpoint_ligand_atom", "second_endpoint_protein_asym",
    "second_endpoint_residue_id", "second_endpoint_protein_atom",
    "second_endpoint_protein_chemistry_class", "second_endpoint_connection_id",
    "second_endpoint_reported_distance_angstrom", "second_endpoint_is_target_event",
    "human_task_relevance_decision", "task_relevance_human_authoritative",
    "task_domain_negative", "D2_human_choice", "D3_human_choice",
    "D4_human_choice", "D5_human_choice", "chemistry_human_authoritative",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "training_use_human_decision_available",
    "training_only_exclusion_human_authoritative",
    "legacy_completed_review_status", "task_relevance_disposition",
    "chemistry_disposition", "training_disposition", "human_training_excluded",
    "selected_role_candidate_index_0based", "role_profile", "warhead_atoms_json",
    "linker_atoms_json", "scaffold_atoms_json", "boundary_bonds_json",
    "sample_authoritative_applicable_task_ids_json", "global_canonical_task_count",
    "canonical_task_authority_availability_json", "B3_present", "sixth_task_present",
    "chemistry_known_positive", "negative_chemistry",
    "sample_level_chemistry_positive_authority",
    "sample_level_chemistry_negative_authority",
    "chemical_warhead_human_authoritative", "chemical_warhead_atoms_json",
    "reaction_family_authority", "warhead_family_authority",
    "warhead_rule_authority", "warhead_type_authority",
    "reusable_chemistry_authority", "POST_source_evidence_available",
    "POST_sample_authority", "POST_geometry_training_authority_available",
    "POST_geometry_training_target_available_now", "PRE_status",
    "PRE_source_graph_mapping_count", "PRE_topology_authority_available",
    "PRE_geometry_authority_available", "PRE_reconstruction_performed",
    "PRE_mapping_repair_performed", "POST_to_PRE_copy_performed",
    "PRE_zero_fill_performed", "training_use_allowed", "training_use_include",
    "candidate_for_future_training_admission", "future_training_admission_candidate",
    "training_admitted", "training_admission_created",
    "training_materialization_allowed_now", "formal_split_authority_created",
    "tensor_target_created", "current_runtime_model_usable",
    "parameter_update_authorization", "ready_for_training", "authority_source",
    "authority_scope", "authority_ingested", "authority_created_by_this_ingestion",
)


def _bool_cell(value: bool) -> str:
    return "true" if value else "false"


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    null = "null"
    for event in snapshot["events"]:
        rows.append(
            {
                "canonical_event_id": event["canonical_event_id"],
                "scaleup_rank": str(event["scaleup_rank"]),
                "pdb_id": event["pdb_id"],
                "model_number": "1",
                "protein_chain_or_asym": event["protein_chain_or_asym"],
                "cys_residue_id": event["cys_residue_id"],
                "ligand_component_id": "1N0",
                "ligand_chain_or_asym": event["ligand_chain_or_asym"],
                "primary_connection_id": event["primary_connection_id"],
                "observed_POST_distance_angstrom": event[
                    "observed_POST_distance_frozen_lexeme"
                ],
                "explicit_covalent_evidence": "true",
                "raw_structural_reactive_pair_evidence": "true",
                "observed_protein_reactive_atom": "SG",
                "observed_ligand_reactive_atom": "C16",
                "second_endpoint_present": "true",
                "second_endpoint_ligand_atom": "C2",
                "second_endpoint_protein_asym": event["second_endpoint_protein_asym"],
                "second_endpoint_residue_id": event["second_endpoint_residue_id"],
                "second_endpoint_protein_atom": event["second_endpoint_protein_atom"],
                "second_endpoint_protein_chemistry_class": event[
                    "second_endpoint_protein_chemistry_class"
                ],
                "second_endpoint_connection_id": event["second_endpoint_connection_id"],
                "second_endpoint_reported_distance_angstrom": str(
                    event["second_endpoint_reported_distance_angstrom"]
                ),
                "second_endpoint_is_target_event": "false",
                "human_task_relevance_decision": "NOT_RELEVANT",
                "task_relevance_human_authoritative": "true",
                "task_domain_negative": "true",
                "D2_human_choice": "UNRESOLVED",
                "D3_human_choice": "UNRESOLVED",
                "D4_human_choice": "UNRESOLVED",
                "D5_human_choice": "UNRESOLVED",
                "chemistry_human_authoritative": "false",
                "reactive_pair_human_decision_available": "false",
                "reactive_pair_human_authoritative": "false",
                "role_partition_human_decision_available": "false",
                "role_partition_human_authoritative": "false",
                "training_use_human_decision_available": "false",
                "training_only_exclusion_human_authoritative": "false",
                "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
                "task_relevance_disposition": "NOT_RELEVANT",
                "chemistry_disposition": "NOT_ESTABLISHED",
                "training_disposition": "NOT_APPLICABLE",
                "human_training_excluded": "false",
                "selected_role_candidate_index_0based": null,
                "role_profile": null,
                "warhead_atoms_json": null,
                "linker_atoms_json": null,
                "scaffold_atoms_json": null,
                "boundary_bonds_json": null,
                "sample_authoritative_applicable_task_ids_json": null,
                "global_canonical_task_count": "5",
                "canonical_task_authority_availability_json": _json_cell(
                    _task_authority_vector()
                ),
                "B3_present": "true",
                "sixth_task_present": "false",
                "chemistry_known_positive": "false",
                "negative_chemistry": "false",
                "sample_level_chemistry_positive_authority": "false",
                "sample_level_chemistry_negative_authority": "false",
                "chemical_warhead_human_authoritative": "false",
                "chemical_warhead_atoms_json": null,
                "reaction_family_authority": "false",
                "warhead_family_authority": "false",
                "warhead_rule_authority": "false",
                "warhead_type_authority": "false",
                "reusable_chemistry_authority": "false",
                "POST_source_evidence_available": "true",
                "POST_sample_authority": "false",
                "POST_geometry_training_authority_available": "false",
                "POST_geometry_training_target_available_now": "false",
                "PRE_status": PRE_STATUS,
                "PRE_source_graph_mapping_count": "0",
                "PRE_topology_authority_available": "false",
                "PRE_geometry_authority_available": "false",
                "PRE_reconstruction_performed": "false",
                "PRE_mapping_repair_performed": "false",
                "POST_to_PRE_copy_performed": "false",
                "PRE_zero_fill_performed": "false",
                "training_use_allowed": "false",
                "training_use_include": "false",
                "candidate_for_future_training_admission": "false",
                "future_training_admission_candidate": "false",
                "training_admitted": "false",
                "training_admission_created": "false",
                "training_materialization_allowed_now": "false",
                "formal_split_authority_created": "false",
                "tensor_target_created": "false",
                "current_runtime_model_usable": "false",
                "parameter_update_authorization": "false",
                "ready_for_training": "false",
                "authority_source": AUTHORITY_SOURCE,
                "authority_scope": AUTHORITY_SCOPE,
                "authority_ingested": "true",
                "authority_created_by_this_ingestion": "false",
            }
        )
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "review_unit": "1N0",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": 4,
        "task_domain_negative": True,
        "completed_negative_event_count": 4,
        "task_relevance_authority_event_count": 4,
        "task_relevant_event_count": 0,
        "chemistry_positive_authority_count": 0,
        "chemistry_negative_authority_count": 0,
        "reactive_pair_human_authority_count": 0,
        "role_partition_human_authority_count": 0,
        "canonical_mask_label_authority_count": 0,
        "training_include_count": 0,
        "training_only_exclusion_count": 0,
        "future_training_candidate_count": 0,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_count": 0,
        "PRE_geometry_authority_count": 0,
        "normalized_disposition_counts": {
            "COMPLETED_HUMAN_NEGATIVE": 4,
            "NOT_RELEVANT": 4,
            "NOT_ESTABLISHED": 4,
            "NOT_APPLICABLE": 4,
        },
        "raw_evidence_preserved": True,
        "raw_evidence_promoted_to_human_authority": False,
        "second_endpoint_context_preserved": True,
        "C2_events_ingested": False,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "active_source_binding_count": 9,
        "authority_ingested": True,
        "authority_created_by_this_ingestion": False,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "training_started": False,
        "ready_for_training": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "authority_boundary": _authority_boundary(),
    }


def _validate_text_payload(label: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= 1024 * 1024
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
        raise OneN0IngestionSafetyError(
            "COVAPIE_1N0_INGESTION_V1_ERROR:UTF8_INVALID:" + label
        ) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TRAILING_WHITESPACE_INVALID:" + label)


def _reject_dynamic_or_forbidden_metadata(value: object, path: str = "root") -> None:
    dynamic = {
        "generated_at", "created_at", "validated_at", "timestamp", "hostname",
        "host", "pid", "uuid", "cwd", "temporary_directory", "temporary_path",
        "output_path", "live_git_status", "git_head", "git_tree",
    }
    if type(value) is dict:
        for key, child in value.items():
            lowered = key.lower()
            if lowered in _FORBIDDEN_LIVE_IDENTITY_FIELDS:
                _fail("NUMERIC_POSIX_SEMANTIC_FIELD_FORBIDDEN:" + path + "." + key)
            if lowered in dynamic or "timestamp" in lowered:
                _fail("DYNAMIC_METADATA_KEY:" + path + "." + key)
            _reject_dynamic_or_forbidden_metadata(child, path + "." + key)
    elif type(value) is list:
        for index, child in enumerate(value):
            _reject_dynamic_or_forbidden_metadata(child, f"{path}[{index}]")
    elif type(value) is str and (
        value.startswith("/cpfs")
        or value.startswith("/home/")
        or value.startswith("/tmp/")
        or value.startswith("file://")
    ):
        _fail("ABSOLUTE_OR_MACHINE_PATH:" + path)


def _candidate_source_bindings(repo_root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for relative, source_role in (
        (SOURCE_RELATIVE, "production_owner"),
        (CHECKER_RELATIVE, "fail_closed_checker"),
        (TEST_RELATIVE, "targeted_test_contract"),
    ):
        path = repo_root / relative
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise OneN0IngestionSafetyError(
                "COVAPIE_1N0_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
                + relative.as_posix()
            ) from error
        _validate_text_payload(relative.as_posix(), payload)
        digest = _sha256(payload)
        try:
            verified = verify_bound_source_v2(
                path=path,
                expected_byte_count=len(payload),
                expected_sha256=digest,
                label="ONE_N0_CANDIDATE_SOURCE:" + relative.as_posix(),
                expected_executable=False,
            )
        except SourceBindingPolicyV2Error as error:
            raise OneN0IngestionSafetyError(
                "COVAPIE_1N0_INGESTION_V1_ERROR:CANDIDATE_SOURCE_REJECTED:"
                + relative.as_posix()
            ) from error
        if verified != payload:
            _fail("CANDIDATE_SOURCE_UNSTABLE:" + relative.as_posix())
        records.append(
            {
                "path": relative.as_posix(),
                "namespace": "repository_relative",
                "byte_count": len(payload),
                "SHA256": digest,
                "expected_executable_class": "NON_EXECUTABLE",
                "source_role": source_role,
            }
        )
    return records


def _validate_binding_records(value: object, expected_count: int) -> None:
    if type(value) is not list or len(value) != expected_count:
        _fail("BINDING_RECORD_COUNT_INVALID")
    required = {
        "path", "namespace", "byte_count", "SHA256",
        "expected_executable_class", "source_role",
    }
    for record in value:
        if (
            type(record) is not dict
            or set(record) != required
            or record.get("namespace") not in {
                "repository_relative", "project_parent_relative"
            }
            or type(record.get("byte_count")) is not int
            or record["byte_count"] <= 0
            or type(record.get("SHA256")) is not str
            or len(record["SHA256"]) != 64
            or record.get("expected_executable_class") != "NON_EXECUTABLE"
        ):
            _fail("BINDING_RECORD_SHAPE_INVALID")


def _manifest(
    bound: Mapping[str, object],
    candidate_source_bindings: list[dict[str, object]],
    snapshot_payload: bytes,
    matrix_payload: bytes,
    summary_payload: bytes,
) -> dict[str, object]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "ONE_N0_COMPLETED_DECISION_INGESTION_NOT_RECONCILIATION_OR_ADMISSION",
        "candidate_file_count": 7,
        "output_file_count": 4,
        "event_count": 4,
        "active_source_binding_count": 9,
        "active_source_bindings": bound["active_source_bindings"],
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "candidate_source_bindings": candidate_source_bindings,
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "source_binding_policy_binding": bound["source_binding_policy_binding"],
        "semantic_owner_bindings": bound["semantic_owner_bindings"],
        "current_census_bindings": bound["current_census_bindings"],
        "current_census_boundary": bound["current_census_boundary"],
        "generic_completed_negative_projection": copy.deepcopy(GENERIC_PROJECTION),
        "canonical_task_contract": _canonical_task_contract(),
        "task_domain_negative": True,
        "raw_evidence_preserved": True,
        "raw_evidence_promoted_to_human_authority": False,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "source_binding_V2_clean_from_birth": True,
        "numeric_POSIX_semantic_identity": False,
        "separate_V2_successor_required": False,
        "formal_validator_runtime_dependency": False,
        "output_artifact_bindings": {
            SNAPSHOT: {
                "byte_count": len(snapshot_payload),
                "SHA256": _sha256(snapshot_payload),
                "expected_executable_class": "NON_EXECUTABLE",
            },
            MATRIX: {
                "byte_count": len(matrix_payload),
                "SHA256": _sha256(matrix_payload),
                "expected_executable_class": "NON_EXECUTABLE",
            },
            SUMMARY: {
                "byte_count": len(summary_payload),
                "SHA256": _sha256(summary_payload),
                "expected_executable_class": "NON_EXECUTABLE",
            },
        },
        "manifest_self_SHA256_recorded": False,
        "manifest_self_SHA256_policy": "SELF_SHA256_PROHIBITED",
        "deterministic": True,
        "authority_boundary": _authority_boundary(),
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "training_started": False,
        "ready_for_training": False,
    }


def _build_artifacts_unvalidated(repo_root: Path) -> dict[str, bytes]:
    root = Path(repo_root).resolve()
    bound = load_frozen_formal_decision_v1(root)
    snapshot_payload = _json_bytes(_snapshot(bound))
    snapshot = _strict_json_loads(snapshot_payload, "BUILT_SNAPSHOT")
    matrix_payload = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    summary_payload = _json_bytes(_summary())
    manifest_payload = _json_bytes(
        _manifest(
            bound,
            _candidate_source_bindings(root),
            snapshot_payload,
            matrix_payload,
            summary_payload,
        )
    )
    return {
        SNAPSHOT: snapshot_payload,
        MATRIX: matrix_payload,
        SUMMARY: summary_payload,
        MANIFEST: manifest_payload,
    }


def _validate_matrix_rows(rows: list[dict[str, str]]) -> None:
    if (
        len(rows) != 4
        or tuple(row.get("canonical_event_id") for row in rows) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in rows) != EXPECTED_RANKS
        or len({row["canonical_event_id"] for row in rows}) != 4
        or any(int(row["scaleup_rank"]) in EXCLUDED_C2_RANKS for row in rows)
    ):
        _fail("MATRIX_EXACT4_IDENTITY_INVALID")
    false_fields = (
        "second_endpoint_is_target_event",
        "chemistry_human_authoritative",
        "reactive_pair_human_decision_available",
        "reactive_pair_human_authoritative",
        "role_partition_human_decision_available",
        "role_partition_human_authoritative",
        "training_use_human_decision_available",
        "training_only_exclusion_human_authoritative",
        "human_training_excluded",
        "chemistry_known_positive",
        "negative_chemistry",
        "sample_level_chemistry_positive_authority",
        "sample_level_chemistry_negative_authority",
        "chemical_warhead_human_authoritative",
        "reaction_family_authority",
        "warhead_family_authority",
        "warhead_rule_authority",
        "warhead_type_authority",
        "reusable_chemistry_authority",
        "POST_sample_authority",
        "POST_geometry_training_authority_available",
        "POST_geometry_training_target_available_now",
        "PRE_topology_authority_available",
        "PRE_geometry_authority_available",
        "PRE_reconstruction_performed",
        "PRE_mapping_repair_performed",
        "POST_to_PRE_copy_performed",
        "PRE_zero_fill_performed",
        "training_use_allowed",
        "training_use_include",
        "candidate_for_future_training_admission",
        "future_training_admission_candidate",
        "training_admitted",
        "training_admission_created",
        "training_materialization_allowed_now",
        "formal_split_authority_created",
        "tensor_target_created",
        "current_runtime_model_usable",
        "parameter_update_authorization",
        "ready_for_training",
        "authority_created_by_this_ingestion",
    )
    null_fields = (
        "selected_role_candidate_index_0based",
        "role_profile",
        "warhead_atoms_json",
        "linker_atoms_json",
        "scaffold_atoms_json",
        "boundary_bonds_json",
        "sample_authoritative_applicable_task_ids_json",
        "chemical_warhead_atoms_json",
    )
    for index, row in enumerate(rows):
        vector = json.loads(row["canonical_task_authority_availability_json"])
        if (
            row["observed_POST_distance_angstrom"] != EXPECTED_EVENTS[index][8]
            or row["explicit_covalent_evidence"] != "true"
            or row["raw_structural_reactive_pair_evidence"] != "true"
            or row["observed_protein_reactive_atom"] != "SG"
            or row["observed_ligand_reactive_atom"] != "C16"
            or row["second_endpoint_present"] != "true"
            or row["second_endpoint_ligand_atom"] != "C2"
            or row["human_task_relevance_decision"] != "NOT_RELEVANT"
            or row["task_relevance_human_authoritative"] != "true"
            or row["task_domain_negative"] != "true"
            or [row[f"D{number}_human_choice"] for number in (2, 3, 4, 5)]
            != ["UNRESOLVED"] * 4
            or row["legacy_completed_review_status"] != "COMPLETED_HUMAN_NEGATIVE"
            or row["task_relevance_disposition"] != "NOT_RELEVANT"
            or row["chemistry_disposition"] != "NOT_ESTABLISHED"
            or row["training_disposition"] != "NOT_APPLICABLE"
            or any(row[field] != "false" for field in false_fields)
            or any(row[field] != "null" for field in null_fields)
            or row["global_canonical_task_count"] != "5"
            or row["B3_present"] != "true"
            or row["sixth_task_present"] != "false"
            or vector != _task_authority_vector()
            or any(item["authoritative_label_available"] is not False for item in vector)
            or row["POST_source_evidence_available"] != "true"
            or row["PRE_status"] != PRE_STATUS
            or row["PRE_source_graph_mapping_count"] != "0"
            or row["authority_source"] != AUTHORITY_SOURCE
            or row["authority_scope"] != AUTHORITY_SCOPE
            or row["authority_ingested"] != "true"
        ):
            _fail("MATRIX_NEGATIVE_AUTHORITY_BOUNDARY_INVALID")


def validate_completed_decision_projection_v1(
    artifacts: Mapping[str, bytes], *, repo_root: Path | None = None
) -> None:
    """Validate all four deterministic outputs and negative authority boundaries."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    snapshot = _strict_json_loads(artifacts[SNAPSHOT], "SNAPSHOT")
    summary = _strict_json_loads(artifacts[SUMMARY], "SUMMARY")
    manifest = _strict_json_loads(artifacts[MANIFEST], "MANIFEST")
    try:
        rows = list(csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8"))))
    except UnicodeDecodeError as error:
        raise OneN0IngestionSafetyError(
            "COVAPIE_1N0_INGESTION_V1_ERROR:MATRIX_UTF8_INVALID"
        ) from error
    for document in (snapshot, summary, manifest):
        _reject_dynamic_or_forbidden_metadata(document)
    if (list(rows[0]) if rows else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    _validate_matrix_rows(rows)
    _expect(summary, _summary(), "SUMMARY_EXACT_COUNTS_INVALID")
    identity = snapshot.get("identity")
    human = snapshot.get("human_decision")
    facts = snapshot.get("normalized_completed_negative_facts")
    if (
        type(identity) is not dict
        or identity.get("canonical_event_ids") != list(EXPECTED_EVENT_IDS)
        or identity.get("scaleup_ranks") != list(EXPECTED_RANKS)
        or identity.get("separate_review_unit_C2_event_ranks") != list(EXCLUDED_C2_RANKS)
        or type(human) is not dict
        or human.get("D1_task_relevance") != "NOT_RELEVANT"
        or [human.get(key) for key in (
            "D2_chemistry", "D3_reactive_pair", "D4_role_candidate", "D5_training_use"
        )] != ["UNRESOLVED"] * 4
        or human.get("approved_is_chemistry_approval") is not False
        or type(human.get("D6_scientific_context")) is not str
        or len(human["D6_scientific_context"].encode("utf-8")) != 657
        or _sha256(human["D6_scientific_context"].encode("utf-8"))
        != "d51bd3139a9ad85d285ce81e26caf4e6c9b45e447f8e3f90e6c6612d14c7d689"
        or type(facts) is not list
        or facts != [_generic_fact(event_id) for event_id in EXPECTED_EVENT_IDS]
        or snapshot.get("canonical_task_contract") != _canonical_task_contract()
        or snapshot.get("chemistry_authority_boundary") != _chemistry_boundary()
        or snapshot.get("role_authority_boundary") != _role_boundary()
        or snapshot.get("geometry_boundary") != _geometry_boundary()
        or snapshot.get("training_boundary") != _training_boundary()
        or snapshot.get("authority_boundary") != _authority_boundary()
    ):
        _fail("SNAPSHOT_NEGATIVE_PROJECTION_INVALID")
    _validate_binding_records(snapshot.get("active_source_bindings"), 9)
    _validate_binding_records(manifest.get("active_source_bindings"), 9)
    _validate_binding_records(manifest.get("candidate_source_bindings"), 3)
    if snapshot["active_source_bindings"] != _binding_records(ACTIVE_BINDINGS):
        _fail("SNAPSHOT_ACTIVE_BINDINGS_NOT_EXACT9")
    if manifest.get("active_source_bindings") != _binding_records(ACTIVE_BINDINGS):
        _fail("MANIFEST_ACTIVE_BINDINGS_NOT_EXACT9")
    output_bindings = manifest.get("output_artifact_bindings")
    if type(output_bindings) is not dict or set(output_bindings) != {
        SNAPSHOT, MATRIX, SUMMARY
    }:
        _fail("MANIFEST_OUTPUT_BINDING_SET_INVALID")
    for name in (SNAPSHOT, MATRIX, SUMMARY):
        expected = {
            "byte_count": len(artifacts[name]),
            "SHA256": _sha256(artifacts[name]),
            "expected_executable_class": "NON_EXECUTABLE",
        }
        if output_bindings.get(name) != expected:
            _fail("MANIFEST_OUTPUT_BINDING_INVALID:" + name)
    required_manifest = {
        "candidate_file_count": 7,
        "output_file_count": 4,
        "event_count": 4,
        "active_source_binding_count": 9,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "task_domain_negative": True,
        "source_binding_V2_clean_from_birth": True,
        "numeric_POSIX_semantic_identity": False,
        "separate_V2_successor_required": False,
        "formal_validator_runtime_dependency": False,
        "manifest_self_SHA256_recorded": False,
        "training_started": False,
        "ready_for_training": False,
    }
    if any(manifest.get(key) != value for key, value in required_manifest.items()):
        _fail("MANIFEST_REQUIRED_BOUNDARY_INVALID")
    candidate_bindings = manifest["candidate_source_bindings"]
    expected_manifest = _manifest(
        {
            "active_source_bindings": _binding_records(ACTIVE_BINDINGS),
            "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
            "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
            "source_binding_policy_binding": _binding_record(POLICY_BINDING),
            "semantic_owner_bindings": _binding_records(SEMANTIC_BINDINGS),
            "current_census_bindings": _binding_records(CENSUS_BINDINGS),
            "current_census_boundary": manifest["current_census_boundary"],
        },
        candidate_bindings,  # type: ignore[arg-type]
        artifacts[SNAPSHOT],
        artifacts[MATRIX],
        artifacts[SUMMARY],
    )
    _expect(manifest, expected_manifest, "MANIFEST_CLOSURE_INVALID")
    if repo_root is not None:
        expected_artifacts = _build_artifacts_unvalidated(Path(repo_root).resolve())
        if dict(artifacts) != expected_artifacts:
            _fail("DIRECT_SOURCE_DERIVED_PROJECTION_INVALID")


def build_artifacts_v1(repo_root: Path) -> dict[str, bytes]:
    """Build pure deterministic bytes for the four authorized outputs."""

    artifacts = _build_artifacts_unvalidated(Path(repo_root).resolve())
    validate_completed_decision_projection_v1(artifacts)
    return artifacts


def _validate_materialization_destination_v1(target_root: Path) -> None:
    """Reject unsafe destination state before any mkdir, temp file, or write."""

    try:
        metadata = target_root.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise OneN0IngestionSafetyError(
            "COVAPIE_1N0_INGESTION_V1_ERROR:OUTPUT_ROOT_LSTAT_FAILED"
        ) from error
    if stat.S_ISLNK(metadata.st_mode):
        _fail("OUTPUT_ROOT_SYMLINK_FORBIDDEN")
    if not stat.S_ISDIR(metadata.st_mode):
        _fail("OUTPUT_ROOT_NOT_DIRECTORY")
    try:
        entries = tuple(target_root.iterdir())
    except OSError as error:
        raise OneN0IngestionSafetyError(
            "COVAPIE_1N0_INGESTION_V1_ERROR:OUTPUT_ROOT_INVENTORY_READ_FAILED"
        ) from error
    unexpected = sorted(
        entry.name for entry in entries if entry.name not in OUTPUT_FILENAMES
    )
    if unexpected:
        _fail("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_ENTRIES")
    for entry in entries:
        try:
            entry_metadata = entry.lstat()
        except OSError as error:
            raise OneN0IngestionSafetyError(
                "COVAPIE_1N0_INGESTION_V1_ERROR:OUTPUT_ENTRY_LSTAT_FAILED:"
                + entry.name
            ) from error
        if stat.S_ISLNK(entry_metadata.st_mode) or not stat.S_ISREG(
            entry_metadata.st_mode
        ):
            _fail("OUTPUT_ENTRY_NOT_REGULAR:" + entry.name)


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_artifacts_v1(
    repo_root: Path, *, output_root: Path | None = None
) -> dict[str, bytes]:
    """Materialize exactly four outputs after the complete pre-write gate."""

    root = Path(repo_root).resolve()
    artifacts = build_artifacts_v1(root)
    target = Path(output_root) if output_root is not None else root / OUTPUT_ROOT_RELATIVE
    _validate_materialization_destination_v1(target)
    if not target.exists():
        target.mkdir(parents=True)
    for name, payload in artifacts.items():
        _atomic_write(target / name, payload)
    return artifacts


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    """Compare materialized Exact4 outputs with a fresh deterministic build."""

    root = Path(repo_root).resolve()
    expected = build_artifacts_v1(root)
    output_root = root / OUTPUT_ROOT_RELATIVE
    _validate_materialization_destination_v1(output_root)
    if tuple(sorted(path.name for path in output_root.iterdir())) != tuple(
        sorted(OUTPUT_FILENAMES)
    ):
        _fail("OUTPUT_INVENTORY_NOT_EXACT4")
    actual: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = output_root / name
        payload = path.read_bytes()
        try:
            actual[name] = verify_bound_source_v2(
                path=path,
                expected_byte_count=len(payload),
                expected_sha256=_sha256(payload),
                label="ONE_N0_MATERIALIZED_OUTPUT:" + name,
                expected_executable=False,
            )
        except SourceBindingPolicyV2Error as error:
            raise OneN0IngestionSafetyError(
                "COVAPIE_1N0_INGESTION_V1_ERROR:OUTPUT_REJECTED:" + name
            ) from error
    validate_completed_decision_projection_v1(actual, repo_root=root)
    if actual != expected:
        _fail("MATERIALIZED_OUTPUT_BYTES_DRIFT")
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "exact_output_count": 4,
        "event_count": 4,
        "task_domain_negative": True,
        "completed_negative_projection_exact": True,
        "raw_structural_evidence_preserved": True,
        "raw_evidence_promoted_to_human_authority": False,
        "authority_ingested": True,
        "authority_created_by_this_ingestion": False,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "training_started": False,
        "ready_for_training": False,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    materialize_artifacts_v1(repo_root)
    print(json.dumps(check_materialized_v1(repo_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
