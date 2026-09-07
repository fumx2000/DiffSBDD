"""Project frozen PYR Exact4 human authority into metadata-only artifacts.

The formal JSON is parsed and independently validated.  Its frozen validator
is provenance identity only and is never parsed, imported, executed, or
subprocessed.  This additive stage performs no reconciliation, census/queue
refresh, task-label or tensor materialization, dataset mutation, or training.
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
    "PYRIngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = "covapie_pyr_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_pyr_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_pyr_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_pyr_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_pyr_completed_decision_ingestion_manifest_v1"
BASELINE_COMMIT = "f202885d3469dfae489ecb8b024e308798634c0f"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_pyr_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_pyr_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_pyr_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_pyr_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_pyr_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_pyr_event_task_label_availability_v1.csv"
SUMMARY = "covapie_pyr_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_pyr_completed_decision_ingestion_manifest_v1.json"
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
    "PYR_COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4"
)
FORMAL_DECISION_RELATIVE = (
    STATE_ROOT / "formal-human-decision-v1/pyr_formal_human_decision_v1.json"
)
FORMAL_VALIDATOR_RELATIVE = (
    STATE_ROOT
    / "formal-human-decision-v1/validate_pyr_formal_human_decision_v1.py"
)
EVENT_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/pyr_exact4_event_evidence_v1.csv"
)
GRAPH_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/pyr_graph_and_review_evidence_v1.json"
)
CCD_RELATIVE = Path(
    "covapie-state/bulk-multisource-cys-sg-v1/rcsb/ccd/PYR.cif"
)
SOURCE_BINDING_POLICY_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
DIRECT_RUNTIME_OWNER_RELATIVE = Path(
    "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"
)
CANONICAL_TASK_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
GENERIC_OWNER_RELATIVE = Path(
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py"
)
CENSUS_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1.py"
)
CENSUS_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1"
)
CENSUS_MATRIX_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1.csv"
)
CENSUS_SUMMARY_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_summary_with_6oa_v1.json"
)
CENSUS_MANIFEST_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_manifest_with_6oa_v1.json"
)

FORMAL_DECISION_SCHEMA = "covapie_pyr_exact4_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4"
EXPECTED_SCOPE = "CURRENT_PYR_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
EXPECTED_LEGACY_STATUS = "COMPLETED_HUMAN_POSITIVE"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
SELECTED_CANDIDATE = "CANDIDATE_A_DIRECT_ALPHA_KETOCARBOXYL_POST_CENTER"
ALTERNATIVE_CANDIDATE = "CANDIDATE_B_STRICT_TERMINAL_ELECTROPHILE_POST_CENTER"
SOURCE_D2 = "IN_DOMAIN"
NORMALIZED_TASK_RELEVANCE = "RELEVANT"
SOURCE_D6 = "EXCLUDE"
NORMALIZED_TRAINING_DISPOSITION = "EXCLUDE_FROM_TRAINING_ONLY"
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
PRE_STATUS = "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"

# Event ID, rank, protein asym, ligand asym, ligand auth chain, connection,
# exact POST lexeme, reported POST lexeme.
EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:1F8M:A:CYS:191-:SG:F:PYR:CB",
        46,
        "A",
        "F",
        "A",
        "covale1",
        "1.780689",
        "1.781",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:1F8M:B:CYS:191-:SG:H:PYR:CB",
        47,
        "B",
        "H",
        "B",
        "covale2",
        "1.804200",
        "1.804",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:1F8M:C:CYS:191-:SG:J:PYR:CB",
        48,
        "C",
        "J",
        "C",
        "covale3",
        "1.787779",
        "1.788",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:1F8M:D:CYS:191-:SG:L:PYR:CB",
        49,
        "D",
        "L",
        "D",
        "covale4",
        "1.770279",
        "1.770",
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)

WARHEAD_ATOMS = ("CB", "CA", "O3")
LINKER_ATOMS: tuple[str, ...] = ()
SCAFFOLD_ATOMS = ("C", "O", "OXT")
HEAVY_ATOMS = ("C", "CA", "CB", "O", "O3", "OXT")
HEAVY_BONDS = (
    ("C", "CA", "SING"),
    ("C", "O", "DOUB"),
    ("C", "OXT", "SING"),
    ("CA", "CB", "SING"),
    ("CA", "O3", "DOUB"),
)
MINIMAL_SEED = ("C", "O")
PRIMARY_ANCHOR = "C"
BOUNDARY = {
    "scaffold_atom_id": "C",
    "warhead_atom_id": "CA",
    "bond_order": "SING",
}
ALTERNATIVE_WARHEAD_ATOMS = ("CB",)
ALTERNATIVE_LINKER_ATOMS = ("CA", "O3")
ALTERNATIVE_SCAFFOLD_ATOMS = SCAFFOLD_ATOMS
ALTERNATIVE_SEED = ("C", "OXT")

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
DIRECT_APPLICABILITY = (
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
DIRECT_APPLICABLE_TASK_IDS = (0, 3, 4)
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
    "human_training_excluded": True,
}

# path, namespace, bytes, SHA256, executable, role, validation method
_Binding = tuple[Path, str, int, str, bool, str, str]
FORMAL_BINDINGS: tuple[_Binding, ...] = (
    (
        FORMAL_DECISION_RELATIVE,
        "project_parent_relative",
        17975,
        "58736b2b9dda6078e2e57495d698af110b13f42eec6668cbdb358820dfb66e2d",
        False,
        "PYR_FROZEN_FORMAL_HUMAN_DECISION",
        "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE,
        "project_parent_relative",
        75613,
        "003a1e6f85616bc8d5f255bd2333f0b61ee0144afaed32a3e7ba64114cdc543c",
        False,
        "PYR_FROZEN_FORMAL_VALIDATOR",
        "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED",
    ),
)
SUPPORTING_BINDINGS: tuple[_Binding, ...] = (
    (
        EVENT_EVIDENCE_RELATIVE,
        "project_parent_relative",
        12452,
        "20292f757470d5b423c85a01067536bdc09099956ae3d3fc791dfe6aeb6da174",
        False,
        "PYR_EXACT4_EVENT_EVIDENCE",
        "PARSED_CSV_SUPPORTING_EVIDENCE_WITH_FROZEN_1F8M_IDENTITY",
    ),
    (
        GRAPH_EVIDENCE_RELATIVE,
        "project_parent_relative",
        38379,
        "4697252320487560da6b239aef69d6855632f4d9e03b6f102ebe26a811e9ab28",
        False,
        "PYR_GRAPH_AND_REVIEW_EVIDENCE",
        "PARSED_JSON_EXACT6_GRAPH_AND_PRE_BOUNDARY_PROOF",
    ),
    (
        CCD_RELATIVE,
        "project_parent_relative",
        6538,
        "cb79f4b4d65c6aab3d17e69acdf77bf46b79b2a9dd1457eea7ebc763f5ce88ad",
        False,
        "PYR_FROZEN_CCD",
        "CONTENT_IDENTITY_SUPPORTING_GRAPH_PROVENANCE",
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
SEMANTIC_OWNER_BINDINGS: tuple[_Binding, ...] = (
    (
        DIRECT_RUNTIME_OWNER_RELATIVE,
        "repository_relative",
        37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        False,
        "PUBLISHED_DIRECT_ROLE_RUNTIME_OWNER",
        "IMPORTED_AND_CALLED_FOR_PARTITION_BOUNDARY_SEED_AND_TASKS",
    ),
    (
        CANONICAL_TASK_OWNER_RELATIVE,
        "repository_relative",
        67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        False,
        "PUBLISHED_CANONICAL_EXACT5_OWNER",
        "PARSED_AST_LITERAL_CONTRACT_ONLY",
    ),
    (
        GENERIC_OWNER_RELATIVE,
        "repository_relative",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
        False,
        "PUBLISHED_GENERIC_COMPLETED_DECISION_OWNER",
        "IMPORTED_READ_ONLY_FOR_ACTUAL_EXACT11_COMPATIBILITY",
    ),
)
CENSUS_BINDINGS: tuple[_Binding, ...] = (
    (
        CENSUS_OWNER_RELATIVE,
        "repository_relative",
        77260,
        "7211246fc5bf52f1c47a903e4207f288bb828bcd1c746385d2aa1ddc4566822b",
        False,
        "CURRENT_WITH_6OA_CENSUS_OWNER",
        "CONTENT_IDENTITY_READ_ONLY",
    ),
    (
        CENSUS_MATRIX_RELATIVE,
        "repository_relative",
        555850,
        "440bebc49aefd2a7b920063f5fca949f8f9930b76b6cca496bd8942b83d88a1b",
        False,
        "CURRENT_WITH_6OA_CENSUS_MATRIX",
        "PARSED_CSV_PREINGESTION_STATE_READ_ONLY",
    ),
    (
        CENSUS_SUMMARY_RELATIVE,
        "repository_relative",
        22749,
        "f3bbdae930e4115e0bf0a51119ad3c5863064cf1fa68670d2ea1e610983dccd8",
        False,
        "CURRENT_WITH_6OA_CENSUS_SUMMARY",
        "PARSED_JSON_PENDING_RANK_READ_ONLY",
    ),
    (
        CENSUS_MANIFEST_RELATIVE,
        "repository_relative",
        85531,
        "e20eaddb68035f06cf910fc6aef9dbb87f10f260f62fad09e76afef11c44bf69",
        False,
        "CURRENT_WITH_6OA_CENSUS_MANIFEST",
        "PARSED_JSON_CONTENT_IDENTITY_READ_ONLY",
    ),
)
ACTIVE_BINDINGS = (
    *FORMAL_BINDINGS,
    *SUPPORTING_BINDINGS,
    POLICY_BINDING,
    *SEMANTIC_OWNER_BINDINGS,
    *CENSUS_BINDINGS,
)


class PYRIngestionSafetyError(ValueError):
    """Raised when the frozen PYR projection contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise PYRIngestionSafetyError("COVAPIE_PYR_INGESTION_V1_ERROR:" + reason)


def _expect(actual: object, expected: object, reason: str) -> None:
    if type(actual) is not type(expected) or actual != expected:
        _fail(reason)


def _expect_fields(
    mapping: object, expected: Mapping[str, object], reason: str
) -> Mapping[str, object]:
    if type(mapping) is not dict:
        _fail(reason + ":NOT_OBJECT")
    for key, expected_value in expected.items():
        _expect(mapping.get(key), expected_value, reason + ":" + key)  # type: ignore[union-attr]
    return mapping  # type: ignore[return-value]


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
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload:
        _fail("JSON_TEXT_INVARIANT_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PYRIngestionSafetyError(
            "COVAPIE_PYR_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label
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
        raise PYRIngestionSafetyError(
            "COVAPIE_PYR_INGESTION_V1_ERROR:JSON_PARSE_FAILED:" + label
        ) from error
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _parse_csv(payload: bytes, label: str) -> list[dict[str, str]]:
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload:
        _fail("CSV_TEXT_INVARIANT_INVALID:" + label)
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise PYRIngestionSafetyError(
            "COVAPIE_PYR_INGESTION_V1_ERROR:CSV_UTF8_INVALID:" + label
        ) from error
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        _fail("CSV_HEADER_INVALID:" + label)
    rows = list(reader)
    if any(None in row for row in rows):
        _fail("CSV_ROW_WIDTH_INVALID:" + label)
    return rows


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


def _normalize_overrides(
    value: Mapping[Path, Path] | None,
) -> dict[Path, Path]:
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
        raise PYRIngestionSafetyError(
            "COVAPIE_PYR_INGESTION_V1_ERROR:SOURCE_BINDING_FAILED:"
            + relative.as_posix()
        ) from error


def _verify_bindings(
    repo_root: Path, overrides: Mapping[Path, Path]
) -> dict[Path, bytes]:
    identities = [
        (binding[1], binding[0].as_posix(), binding[3]) for binding in ACTIVE_BINDINGS
    ]
    if len(ACTIVE_BINDINGS) != 13 or len(set(identities)) != 13:
        _fail("ACTIVE_SOURCE_BINDINGS_NOT_UNIQUE_EXACT13")
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
        raise PYRIngestionSafetyError(
            "COVAPIE_PYR_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
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
                    raise PYRIngestionSafetyError(
                        "COVAPIE_PYR_INGESTION_V1_ERROR:"
                        "SEMANTIC_OWNER_LITERAL_INVALID:" + target.id
                    ) from error
    if set(values) != set(names):
        _fail("SEMANTIC_OWNER_LITERAL_MISSING:" + label)
    return values


def _formal_task_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "generated_roles": list(generated),
            "fixed_or_seed_roles": list(fixed),
            "minimal_seed_or_anchor_retained": task_id == 4,
            "sample_structurally_applicable": task_id in DIRECT_APPLICABLE_TASK_IDS,
            "task_label_authority": False,
        }
        for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
    ]


def _formal_source_rows() -> list[dict[str, object]]:
    rows = (
        (
            "review-preparation-v1/pyr_review_preparation_manifest_v1.json",
            25973,
            "7e241334306c43dff83892057346c906d64356da20fddd768d0cf845b07aa14e",
            "0644",
            "frozen_review_preparation_v1_pyr_review_preparation_manifest_v1.json",
            "pyr_review_unit_relative",
        ),
        (
            "review-preparation-v1/pyr_exact4_event_evidence_v1.csv",
            12452,
            "20292f757470d5b423c85a01067536bdc09099956ae3d3fc791dfe6aeb6da174",
            "0644",
            "frozen_review_preparation_v1_pyr_exact4_event_evidence_v1.csv",
            "pyr_review_unit_relative",
        ),
        (
            "review-preparation-v1/pyr_graph_and_review_evidence_v1.json",
            38379,
            "4697252320487560da6b239aef69d6855632f4d9e03b6f102ebe26a811e9ab28",
            "0644",
            "frozen_review_preparation_v1_pyr_graph_and_review_evidence_v1.json",
            "pyr_review_unit_relative",
        ),
        (
            "review-preparation-v1/HUMAN_REVIEW_GUIDE.md",
            6073,
            "e7ad4faa3303699d8673fd7b3e8983248da707a1fdb1d0663c9ca3ddce3f008b",
            "0644",
            "frozen_review_preparation_v1_HUMAN_REVIEW_GUIDE.md",
            "pyr_review_unit_relative",
        ),
        (
            "review-preparation-v1/pyr_unsigned_human_decision_template_v1.json",
            7410,
            "f7d66e61d9573c6ea664c00e83e5f3c2aba635b580c0129fd8bf1e655264dd28",
            "0644",
            "frozen_review_preparation_v1_pyr_unsigned_human_decision_template_v1.json",
            "pyr_review_unit_relative",
        ),
        (
            "review-preparation-v1/build_and_check_pyr_review_preparation_v1.py",
            137314,
            "8562ac64cb7888dba1a999f32a6003ddda98be69c053becec4421a15fb5f0691",
            "0644",
            "frozen_review_preparation_v1_build_and_check_pyr_review_preparation_v1.py",
            "pyr_review_unit_relative",
        ),
        (
            "scientific-validation-v1/pyr_scientific_validation_v1.json",
            35650,
            "d5f49cf6dfc1d0332b978c90c344ff7baf5b8cba855444803dc39727d037c63c",
            "0644",
            "frozen_scientific_validation_v1_pyr_scientific_validation_v1.json",
            "pyr_review_unit_relative",
        ),
        (
            "scientific-validation-v1/validate_pyr_scientific_validation_v1.py",
            97453,
            "028cab6488444a841927c43e7e2b521dec83ed43a2864a2f5bc9b0099ed69ded",
            "0664",
            "frozen_scientific_validation_v1_validate_pyr_scientific_validation_v1.py",
            "pyr_review_unit_relative",
        ),
        (
            "human-decision-candidate-v1/pyr_filled_unsigned_human_decision_candidate_v1.json",
            26674,
            "db81fe86ac264fb9eed5ef5d1ac40eaffb0896b48429cfe7471b2d0669f56b69",
            "0664",
            "frozen_human_decision_candidate_v1_pyr_filled_unsigned_human_decision_candidate_v1.json",
            "pyr_review_unit_relative",
        ),
        (
            "human-decision-candidate-v1/validate_pyr_filled_unsigned_human_decision_candidate_v1.py",
            71349,
            "b68feb0b6ac6939de2c431ae19e5406be450f9e37100185eb64babba6058ac4d",
            "0664",
            "frozen_human_decision_candidate_v1_validate_pyr_filled_unsigned_human_decision_candidate_v1.py",
            "pyr_review_unit_relative",
        ),
        (
            "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py",
            37255,
            "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
            "0644",
            "published_role_runtime",
            "repository_relative",
        ),
    )
    return [
        {
            "SHA256": digest,
            "bytes": byte_count,
            "mode": mode,
            "path_namespace": namespace,
            "relative_path": relative,
            "source_role": role,
        }
        for relative, byte_count, digest, mode, role, namespace in rows
    ]


def _validate_formal(formal: Mapping[str, Any]) -> None:
    """Independently validate the complete critical PYR formal contract."""
    _expect(
        set(formal),
        {
            "approved_D1_D6",
            "authorization_record",
            "file_inventory",
            "frozen_candidate_binding",
            "frozen_preparation_bindings",
            "frozen_scientific_binding",
            "non_created_authority",
            "operation_boundary",
            "readiness",
            "record_role",
            "sample_identity",
            "sample_level_authority",
            "schema_version",
            "selected_role_partition",
            "selected_seed_and_anchor",
            "selected_task_ids",
            "source_bindings",
            "unselected_alternatives",
        },
        "FORMAL_TOP_LEVEL_FIELDS_DRIFT",
    )
    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(formal.get("record_role"), FORMAL_RECORD_ROLE, "FORMAL_RECORD_ROLE_DRIFT")
    _expect(
        formal.get("authorization_record"),
        {
            "approval_time": None,
            "approval_time_status": "NOT_PROVIDED_VERIFIABLY",
            "attestor_id": "fmx",
            "authorization_complete": True,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "authorization_text": "我选择 Candidate A，批准建议确认值；reviewer_id=fmx；attestor_id=fmx。",
            "electronic_signature_claimed": False,
            "independent_identity_authentication_claimed": False,
            "machine_generated_human_authorization": False,
            "platform_identity_verification_claimed": False,
            "reviewer_and_attestor_same_user_supplied_identifier": True,
            "reviewer_id": "fmx",
            "two_independent_platform_verified_people_claimed": False,
        },
        "FORMAL_AUTHORIZATION_DRIFT",
    )
    _expect(
        formal.get("file_inventory"),
        {
            "file_count": 2,
            "files": [
                "pyr_formal_human_decision_v1.json",
                "validate_pyr_formal_human_decision_v1.py",
            ],
            "formal_JSON_self_SHA256_recorded": False,
        },
        "FORMAL_FILE_INVENTORY_DRIFT",
    )
    _expect(
        formal.get("sample_identity"),
        {
            "PDB": "1F8M",
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "cross_structure_authority": False,
            "event_count": 4,
            "ligand_component_id": "PYR",
            "ligand_wide_authority": False,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scaleup_event_ranks": list(EXPECTED_RANKS),
            "scope": EXPECTED_SCOPE,
        },
        "FORMAL_SAMPLE_IDENTITY_DRIFT",
    )
    _expect(
        formal.get("sample_level_authority"),
        {
            "approved": True,
            "formal_decision_created": True,
            "formal_sample_level_authority_created": True,
            "human_decision_created": True,
            "human_review_completed": True,
            "human_selected": True,
            "sample_chemistry_authority": True,
            "sample_pair_authority": True,
            "sample_role_authority": True,
            "sample_seed_authority": True,
            "sample_task_applicability_authority": True,
            "sample_task_relevance_authority": True,
            "sample_training_use_decision_authority": True,
            "unsigned": False,
        },
        "FORMAL_SAMPLE_AUTHORITY_DRIFT",
    )
    decisions = formal.get("approved_D1_D6")
    if type(decisions) is not dict:
        _fail("FORMAL_APPROVED_D1_D6_MISSING")
    _expect(
        decisions.get("D1_observed_covalent_chemistry"),
        {"decision": "POSITIVE", "human_approved": True},
        "FORMAL_D1_DRIFT",
    )
    _expect(
        decisions.get("D2_task_generation_domain_relevance"),
        {"decision": SOURCE_D2, "human_approved": True},
        "FORMAL_D2_DRIFT",
    )
    _expect(
        decisions.get("D3_reactive_atom_pair"),
        {
            "component_atom": "CB",
            "decision": "CONFIRM_OBSERVED_PAIR",
            "human_approved": True,
            "pair": "SG:CB",
            "protein_atom": "SG",
        },
        "FORMAL_D3_DRIFT",
    )
    _expect(
        decisions.get("D4_role_partition_and_minimal_seed"),
        {
            "decision": "PROVIDE_ROLE_PARTITION",
            "human_approved": True,
            "selected_candidate_id": SELECTED_CANDIDATE,
        },
        "FORMAL_D4_DRIFT",
    )
    _expect(
        decisions.get("D5_structural_task_applicability"),
        {
            "decision": "PROVIDE_APPLICABLE_TASK_IDS",
            "human_approved": True,
            "selected_task_ids": list(DIRECT_APPLICABLE_TASK_IDS),
        },
        "FORMAL_D5_DRIFT",
    )
    _expect(
        decisions.get("D6_later_training_use_disposition"),
        {
            "D6_is_chemistry_negative": False,
            "D6_is_formal_training_admission": False,
            "D6_is_out_of_domain": False,
            "decision": SOURCE_D6,
            "formal_training_admitted": False,
            "future_training_admission_candidate": False,
            "human_approved": True,
            "human_training_excluded": True,
        },
        "FORMAL_D6_DRIFT",
    )
    _expect(
        formal.get("frozen_candidate_binding"),
        {
            "SHA256": "db81fe86ac264fb9eed5ef5d1ac40eaffb0896b48429cfe7471b2d0669f56b69",
            "authorization_bound_to_exact_SHA256": (
                "db81fe86ac264fb9eed5ef5d1ac40eaffb0896b48429cfe7471b2d0669f56b69"
            ),
            "bytes": 26674,
            "candidate_human_fields_remained_unset": True,
            "candidate_is_human_authority": False,
            "candidate_modified": False,
            "candidate_was_unsigned": True,
            "mode": "0664",
            "path_namespace": "pyr_review_unit_relative",
            "relative_path": (
                "human-decision-candidate-v1/"
                "pyr_filled_unsigned_human_decision_candidate_v1.json"
            ),
            "source_role": (
                "frozen_human_decision_candidate_v1_"
                "pyr_filled_unsigned_human_decision_candidate_v1.json"
            ),
        },
        "FORMAL_FROZEN_CANDIDATE_DRIFT",
    )
    source_rows = _formal_source_rows()
    _expect(formal.get("source_bindings"), source_rows, "FORMAL_SOURCE_BINDINGS_DRIFT")
    _expect(
        formal.get("frozen_preparation_bindings"),
        source_rows[:6],
        "FORMAL_PREPARATION_BINDINGS_DRIFT",
    )
    _expect(
        formal.get("frozen_scientific_binding"),
        {
            **source_rows[6],
            "scientific_authority_created": False,
            "scientific_modified": False,
        },
        "FORMAL_SCIENTIFIC_BINDING_DRIFT",
    )
    _expect(
        formal.get("selected_role_partition"),
        {
            "human_selected": True,
            "runtime_revalidation": {
                "candidate_id": SELECTED_CANDIDATE,
                "direct_boundary": "C--CA/SING",
                "returned_task_ids": [0, 3, 4],
                "role_profile": EXPECTED_ROLE_PROFILE,
                "role_validator": "validate_role_profile_v1",
                "runtime_diagnostics": [],
                "runtime_valid": True,
                "task_function": "valid_canonical_task_ids_for_role_profile_v1",
            },
            "selected_boundary": "C--CA/SING",
            "selected_candidate_id": SELECTED_CANDIDATE,
            "selected_group_L": [],
            "selected_group_S": list(SCAFFOLD_ATOMS),
            "selected_group_W": list(WARHEAD_ATOMS),
            "selected_role_profile": EXPECTED_ROLE_PROFILE,
        },
        "FORMAL_SELECTED_ROLE_DRIFT",
    )
    _expect(
        formal.get("selected_seed_and_anchor"),
        {
            "human_selected": True,
            "runtime_revalidation": {
                "minimal_seed_validator": "validate_minimal_seed_for_role_profile_v1",
                "primary_anchor_atom_id": PRIMARY_ANCHOR,
                "runtime_diagnostics": [],
                "runtime_valid": True,
                "seed_atom_ids": list(MINIMAL_SEED),
            },
            "selected_primary_anchor": PRIMARY_ANCHOR,
            "selected_seed_atom_ids": list(MINIMAL_SEED),
        },
        "FORMAL_SELECTED_SEED_DRIFT",
    )
    formal_tasks = [
        {"display_alias": alias, "semantic_long_name": semantic, "task_id": task_id}
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]
    _expect(
        formal.get("selected_task_ids"),
        {
            "canonical_V1_contract": {
                "B3_present": True,
                "event_task_label_rows_materialized": False,
                "mask_tensor_targets_created": False,
                "sixth_task": False,
                "task_count": 5,
                "tasks": formal_tasks,
            },
            "decision": "PROVIDE_APPLICABLE_TASK_IDS",
            "event_task_label_rows_materialized": False,
            "human_selected": True,
            "runtime_returned_task_ids": [0, 3, 4],
            "selected_task_ids": [0, 3, 4],
            "task_label_authority": False,
        },
        "FORMAL_SELECTED_TASKS_DRIFT",
    )
    _expect(
        formal.get("unselected_alternatives"),
        {
            "alternate_seed_formal_selected": False,
            "alternate_seed_human_selected": False,
            "alternate_seed_proposal": list(ALTERNATIVE_SEED),
            "alternative_authority_created": False,
            "alternative_boundaries": ["CB--CA/SING", "CA--C/SING"],
            "alternative_candidate_id": ALTERNATIVE_CANDIDATE,
            "alternative_formal_selected": False,
            "alternative_group_L": list(ALTERNATIVE_LINKER_ATOMS),
            "alternative_group_S": list(ALTERNATIVE_SCAFFOLD_ATOMS),
            "alternative_group_W": list(ALTERNATIVE_WARHEAD_ATOMS),
            "alternative_human_selected": False,
            "alternative_machine_proposed": True,
            "alternative_role_profile": "STRICT_LINKER_PRESENT_V1",
            "alternative_task_ids": [0, 1, 2, 3, 4],
            "runtime_revalidation": {
                "alternate_seed_atom_ids": list(ALTERNATIVE_SEED),
                "alternate_seed_primary_anchor_atom_id": PRIMARY_ANCHOR,
                "alternate_seed_runtime_valid": True,
                "candidate_id": ALTERNATIVE_CANDIDATE,
                "returned_task_ids": [0, 1, 2, 3, 4],
                "role_profile": "STRICT_LINKER_PRESENT_V1",
                "runtime_diagnostics": [],
                               "runtime_valid": True,
            },
        },
        "FORMAL_UNSELECTED_ALTERNATIVE_DRIFT",
    )
    _expect(
        formal.get("non_created_authority"),
        {
            "POST_geometry_training_authority": False,
            "PRE_authority": False,
            "cross_structure_authority": False,
            "event_task_label_rows_materialized": False,
            "formal_training_admitted": False,
            "ligand_wide_authority": False,
            "mask_tensor_targets_created": False,
            "parameter_update_authorization": False,
            "reaction_family_authority": False,
            "reusable_authority_created": False,
            "scientific_authority_created": False,
            "task_label_authority": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
            "warhead_rule_authority": False,
            "warhead_type_authority": False,
        },
        "FORMAL_NON_CREATED_AUTHORITY_DRIFT",
    )
    pre_formal_replay = {
        "D1_D6_match": True,
        "candidate_authority_flags_remained_false": True,
        "candidate_human_fields_remained_blank": True,
        "candidate_strict_mutation_probes": "33/33",
        "candidate_validator_child_returncode": 0,
        "candidate_validator_executed_unmodified": True,
        "candidate_validator_mode": "READ_ONLY_CHECK",
        "candidate_validator_passed": True,
        "copied_predecessors_unchanged": True,
        "direct_live_candidate_execution": False,
        "execution_context": "ISOLATED_READ_ONLY_PRE_FORMAL_SNAPSHOT",
        "formal_directory_copied_into_snapshot": False,
        "preparation_isolated_replay_count": 2,
        "primary_candidate_seed_anchor_tasks_match": True,
        "real_sources_unchanged": True,
        "scientific_source_schema_probes": "5/5",
        "scientific_strict_mutation_probes": "41/41",
        "snapshot_bulk_read_view_count": 2,
        "snapshot_candidate_regular_Exact2": True,
        "snapshot_manual_review_dependency_regular_copy_count": 5,
        "snapshot_preparation_regular_Exact6": True,
        "snapshot_repository_clean_read_view": True,
        "snapshot_scientific_regular_Exact2": True,
        "temporary_snapshot_cleanup_automatic": True,
    }
    _expect(
        formal.get("operation_boundary"),
        {
            "candidate_modified": False,
            "census_performed": False,
            "commit_performed": False,
            "formalization_of_external_human_approval": True,
            "ingestion_performed": False,
            "machine_generated_human_authorization": False,
            "mask_tensor_materialization_performed": False,
            "network_acquisition_performed": False,
            "parameter_update_performed": False,
            "pre_formal_replay": pre_formal_replay,
            "preparation_modified": False,
            "push_performed": False,
            "reconciliation_performed": False,
            "repository_modified": False,
            "scientific_modified": False,
            "task_label_materialization_performed": False,
            "training_preparation_performed": False,
        },
        "FORMAL_OPERATION_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("readiness"),
        {
            "AUTHORIZATION_COMPLETE": True,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "FORMAL_DECISION_CREATED": True,
            "FORMAL_SAMPLE_LEVEL_AUTHORITY_CREATED": True,
            "FORMAL_TRAINING_ADMITTED": False,
            "HUMAN_DECISION_CREATED": True,
            "HUMAN_REVIEW_COMPLETED": True,
            "READY_FOR_TRAINING": False,
            "STEP12D_STATUS": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
            "TRAINING_STARTED": False,
        },
        "FORMAL_READINESS_DRIFT",
    )


def _validate_event_evidence(payload: bytes) -> list[dict[str, object]]:
    rows = _parse_csv(payload, "PYR_EVENT_EVIDENCE")
    if len(rows) != 4:
        _fail("EVENT_EVIDENCE_NOT_EXACT4")
    projected: list[dict[str, object]] = []
    frozen_structure = {
        "SHA256": "017be82776f7c1410eb84b107bf29394e2aa2499dfde7998233f47cebd148ae1",
        "bytes": 359041,
        "decompressed_SHA256": (
            "15677d3160d144d7e87676ccb14f9bfece442dee1a3ca201c2bb5a10c06c6dd8"
        ),
        "relative_path": (
            "covapie-state/bulk-multisource-cys-sg-v1/"
            "rcsb/structures/1F8M.cif.gz"
        ),
    }
    for index, (row, expected) in enumerate(zip(rows, EXPECTED_EVENTS, strict=True)):
        (
            event_id,
            rank,
            protein,
            ligand,
            ligand_auth_chain,
            connection,
            exact,
            reported,
        ) = expected
        required = {
            "artifact_role": "UNSIGNED_NONAUTHORITATIVE_MACHINE_REVIEW_AID_PREPARATION",
            "event_index_0based": str(index),
            "canonical_event_id": event_id,
            "scaleup_event_rank": str(rank),
            "raw_review_unit_priority_rank": "30",
            "current_pending_rank": "1",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "pdb_id": "1F8M",
            "model_number": "1",
            "protein_label_asym_id": protein,
            "protein_auth_chain": protein,
            "protein_label_comp_id": "CYS",
            "protein_label_seq_id": "192",
            "protein_auth_seq_id": "191",
            "protein_reactive_atom": "SG",
            "ligand_component_id": "PYR",
            "ligand_label_asym_id": ligand,
            "ligand_auth_chain": ligand_auth_chain,
            "ligand_auth_seq_id": "500",
            "ligand_reactive_atom": "CB",
            "connection_id": connection,
            "connection_type": "covale",
            "connection_source": "FROZEN_WWPDB_MMCIF_STRUCT_CONN_EXPLICIT",
            "explicit_covalent_evidence": "true",
            "distance_only_inference_used": "false",
            "reported_POST_distance_angstrom": reported,
            "exact_POST_distance_angstrom": exact,
            "coordinates_available": "true",
            "raw_structure_available": "true",
            "exact_cys_sg_event_recovered": "true",
            "CCD_graph_complete": "true",
            "feature_compatible": "true",
            "unknown_atom_feature_fallback_used": "false",
            "structural_processing_status": "PASSED",
            "POST_source_evidence_available": "true",
            "reactive_pair_raw_structural_evidence": "true",
            "source_observed_pair_is_human_authority": "false",
            "approved_warhead_atom": "false",
            "supporting_adduct_graph_count": "1",
            "candidate_PRE_free_source_graph_count": "1",
            "source_PRE_mapping_count": "0",
            "PRE_source_mapping_status": PRE_MAPPING_STATUS,
            "final_PRE_reaction_status": PRE_STATUS,
            "PRE_topology_created": "false",
            "PRE_coordinates_created": "false",
            "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false",
            "human_review_completed": "false",
            "chemistry_disposition": "UNRESOLVED",
            "task_relevance_disposition": "UNRESOLVED",
            "training_use_disposition": "UNRESOLVED",
            "formal_training_admitted": "false",
        }
        for key, expected_value in required.items():
            if row.get(key) != expected_value:
                _fail("EVENT_EVIDENCE_DRIFT:" + str(rank) + ":" + key)
        try:
            structure_binding = json.loads(row["source_structure_binding_json"])
            ccd_binding = json.loads(row["CCD_source_binding_json"])
            source_datasets = json.loads(row["source_datasets_json"])
            source_record_ids = json.loads(row["source_record_ids_json"])
        except (KeyError, json.JSONDecodeError) as error:
            raise PYRIngestionSafetyError(
                "COVAPIE_PYR_INGESTION_V1_ERROR:EVENT_SOURCE_FIELD_INVALID"
            ) from error
        for key, expected_value in frozen_structure.items():
            if structure_binding.get(key) != expected_value:
                _fail("FROZEN_1F8M_IDENTITY_DRIFT:" + key)
        if (
            ccd_binding.get("SHA256") != SUPPORTING_BINDINGS[2][3]
            or ccd_binding.get("bytes") != SUPPORTING_BINDINGS[2][2]
            or ccd_binding.get("relative_path") != CCD_RELATIVE.as_posix()
        ):
            _fail("EVENT_CCD_IDENTITY_DRIFT")
        if source_datasets != ["SOURCE_COVBINDERINPDB", "SOURCE_RCSB_PDB_DIRECT"]:
            _fail("EVENT_SOURCE_DATASETS_DRIFT")
        if type(source_record_ids) is not list or len(source_record_ids) != 2:
            _fail("EVENT_SOURCE_RECORD_IDS_DRIFT")
        projected.append(
            {
                "canonical_event_id": event_id,
                "scaleup_rank": rank,
                "protein_chain_or_asym": protein,
                "ligand_chain_or_asym": ligand,
                "ligand_auth_chain": ligand_auth_chain,
                "selected_connection_id": connection,
                "POST_distance_frozen_lexeme": exact,
                "reported_POST_distance_frozen_lexeme": reported,
                "source_datasets": source_datasets,
                "source_record_ids": source_record_ids,
                "source_structure_binding": structure_binding,
                "source_CCD_binding": ccd_binding,
            }
        )
    return projected


def _validate_graph_evidence(payload: bytes) -> dict[str, object]:
    document = _strict_json(payload, "PYR_GRAPH_EVIDENCE")
    graph = _expect_fields(
        document.get("CCD_complete_heavy_atom_graph"),
        {
            "component_id": "PYR",
            "component_name": "PYRUVIC ACID",
            "heavy_atom_count": 6,
            "heavy_heavy_bond_count": 5,
            "connected": True,
            "connected_component_count": 1,
            "CCD_component_graph_SHA256": (
                "af16574b4629c4095d3c2999050d9d9f890cb47d3b14a04bd5a12bb967a04cb9"
            ),
            "canonical_heavy_graph_SHA256": (
                "f72ed3b88a9e2191bd16667fcea942bb2738d1bf23dc71605c63079f197074ff"
            ),
        },
        "GRAPH_ROOT_DRIFT",
    )
    atoms = graph.get("atom_inventory")
    bonds = graph.get("bond_inventory")
    if type(atoms) is not list or type(bonds) is not list:
        _fail("GRAPH_INVENTORY_MISSING")
    atom_ids = tuple(row.get("atom_id") for row in atoms if type(row) is dict)
    bond_rows = tuple(
        (row.get("atom_id_1"), row.get("atom_id_2"), row.get("bond_order"))
        for row in bonds
        if type(row) is dict
    )
    if atom_ids != HEAVY_ATOMS:
        _fail("GRAPH_EXACT6_ATOMS_DRIFT")
    if len(bond_rows) != 5 or set(bond_rows) != set(HEAVY_BONDS):
        _fail("GRAPH_EXACT5_BONDS_DRIFT")
    _expect(
        graph.get("CB_local_topology"),
        {
            "approved_reaction_family": None,
            "approved_role_partition": None,
            "approved_warhead_atom": False,
            "approved_warhead_type": None,
            "exact_two_hop_heavy_atom_shell": ["C", "O3"],
            "one_hop_heavy_atom_shell": ["CA"],
            "source_observed_endpoint_exists_in_complete_graph": True,
            "source_observed_reactive_endpoint": "CB",
        },
        "GRAPH_CB_LOCAL_TOPOLOGY_DRIFT",
    )
    _expect_fields(
        document,
        {
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "ligand_component_id": "PYR",
            "pdb_ids": ["1F8M"],
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scaleup_event_ranks": list(EXPECTED_RANKS),
            "source_observed_pair": "SG:CB",
            "source_observed_pair_is_human_authority": False,
            "source_observed_reactive_endpoint": "CB",
            "source_structural_evidence_only": True,
            "target_event_count": 4,
        },
        "GRAPH_IDENTITY_DRIFT",
    )
    _expect(
        document.get("POST_PRE_representation_boundary"),
        {
            "C_Br_bond_created": False,
            "PYR_POST_component_is_authoritative_free_3_bromopyruvate_PRE_graph": False,
            "bromine_added_to_PYR_CCD_graph": False,
            "experimental_free_electrophile_context": "3-bromopyruvate",
            "free_3_bromopyruvate_coordinates_created": False,
            "leaving_group_authority_created": False,
            "observed_PDB_CCD_component": "PYR",
            "reaction_family_authority_created": False,
            "warhead_atom_authority_created": False,
            "warhead_type_authority_created": False,
        },
        "GRAPH_POST_PRE_BOUNDARY_DRIFT",
    )
    pre = _expect_fields(
        document.get("PRE_evidence"),
        {
            "availability": (
                "SUPPORTING_ADDUCT_AND_CANDIDATE_PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
            ),
            "mapping_status": PRE_MAPPING_STATUS,
            "reaction_status": PRE_STATUS,
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
            "PRE_topology_created": False,
            "PRE_coordinates_created": False,
            "PRE_fabricated": False,
            "leaving_group_inferred": False,
            "reagent_inferred": False,
            "reaction_edit_inferred": False,
            "source_graphs_are_supporting_not_sample_specific_PRE_authority": True,
        },
        "GRAPH_PRE_BOUNDARY_DRIFT",
    )
    audit = pre.get("event_audit")
    if type(audit) is not list or len(audit) != 4:
        _fail("GRAPH_PRE_AUDIT_NOT_EXACT4")
    projected_audit: list[dict[str, object]] = []
    for row, event_id in zip(audit, EXPECTED_EVENT_IDS, strict=True):
        expected = {
            "canonical_event_id": event_id,
            "supporting_adduct_graph_count": 1,
            "supporting_adduct_graph_SHA256": (
                "0b768daa07ecce9dc8a01db879373898bfdb82721082c1d76ea33ce217634ff9"
            ),
            "candidate_PRE_free_source_graph_count": 1,
            "candidate_PRE_free_source_graph_SHA256": (
                "39da817bd08cdc712ac58bf04ef5e7ff5be8557a86845fb0601ac8c6d73a6673"
            ),
            "source_PRE_mapping_count": 0,
            "source_mapping_status": PRE_MAPPING_STATUS,
            "final_PRE_reaction_status": PRE_STATUS,
            "evidence_source_role": "first500_processing",
        }
        _expect(row, expected, "GRAPH_PRE_EVENT_DRIFT:" + event_id)
        projected_audit.append(dict(expected))
    return {
        "atom_ids": atom_ids,
        "bonds": bond_rows,
        "pre_event_audit": projected_audit,
        "graph_digest_namespaces": {
            "CCD_COMPONENT_GRAPH": graph["CCD_component_graph_SHA256"],
            "CANONICAL_HEAVY_GRAPH": graph["canonical_heavy_graph_SHA256"],
            "SUPPORTING_ADDUCT_SOURCE_GRAPH": (
                "0b768daa07ecce9dc8a01db879373898bfdb82721082c1d76ea33ce217634ff9"
            ),
            "CANDIDATE_PRE_FREE_SOURCE_GRAPH": (
                "39da817bd08cdc712ac58bf04ef5e7ff5be8557a86845fb0601ac8c6d73a6673"
            ),
            "cross_namespace_hash_equality_required": False,
        },
    }


def _validate_semantic_owners(payloads: Mapping[Path, bytes]) -> None:
    direct = _literal_assignments(
        payloads[DIRECT_RUNTIME_OWNER_RELATIVE],
        (
            "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "DIRECT_VALID_CANONICAL_TASK_IDS_V1",
            "DIRECT_PROFILE_TASK_APPLICABILITY_V1",
        ),
        DIRECT_RUNTIME_OWNER_RELATIVE.as_posix(),
    )
    canonical = _literal_assignments(
        payloads[CANONICAL_TASK_OWNER_RELATIVE],
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
        CANONICAL_TASK_OWNER_RELATIVE.as_posix(),
    )
    _expect(
        direct["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"],
        EXPECTED_ROLE_PROFILE,
        "DIRECT_PROFILE_OWNER_DRIFT",
    )
    _expect(
        direct["DIRECT_VALID_CANONICAL_TASK_IDS_V1"],
        DIRECT_APPLICABLE_TASK_IDS,
        "DIRECT_TASK_IDS_OWNER_DRIFT",
    )
    _expect(
        direct["DIRECT_PROFILE_TASK_APPLICABILITY_V1"],
        DIRECT_APPLICABILITY,
        "DIRECT_APPLICABILITY_OWNER_DRIFT",
    )
    _expect(
        canonical["EXACT3_ROLES"],
        ("scaffold", "linker", "warhead"),
        "EXACT3_OWNER_DRIFT",
    )
    _expect(canonical["CANONICAL_TASKS"], CANONICAL_TASKS, "EXACT5_OWNER_DRIFT")


def _runtime_validation(repo_root: Path, graph: Mapping[str, object]) -> dict[str, object]:
    runtime = importlib.import_module(
        "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"
    )
    if Path(runtime.__file__).resolve() != (repo_root / DIRECT_RUNTIME_OWNER_RELATIVE).resolve():
        _fail("DIRECT_RUNTIME_IMPORT_PATH_INVALID")
    selected_role = runtime.validate_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE,
        retained_heavy_atoms=graph["atom_ids"],
        scaffold_atoms=SCAFFOLD_ATOMS,
        linker_atoms=LINKER_ATOMS,
        warhead_atoms=WARHEAD_ATOMS,
        reactive_atom_id="CB",
        direct_scaffold_warhead_boundaries=(("C", "CA", "SING"),),
        explicit_graph_bonds=graph["bonds"],
    )
    boundary = selected_role.direct_scaffold_warhead_boundary
    if not (
        selected_role.valid is True
        and tuple(selected_role.reasons) == ()
        and selected_role.scaffold_count == 3
        and selected_role.linker_count == 0
        and selected_role.warhead_count == 3
        and boundary is not None
        and boundary.boundary_valid is True
        and boundary.scaffold_atom_id == "C"
        and boundary.warhead_atom_id == "CA"
        and boundary.bond_order == "SING"
    ):
        _fail("PUBLISHED_SELECTED_ROLE_RUNTIME_FAILED")
    selected_seed = runtime.validate_minimal_seed_for_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE,
        seed_atoms=MINIMAL_SEED,
        scaffold_atoms=SCAFFOLD_ATOMS,
        linker_atoms=LINKER_ATOMS,
        warhead_atoms=WARHEAD_ATOMS,
        explicit_graph_bonds=graph["bonds"],
        direct_boundary=boundary,
    )
    selected_tasks = tuple(
        runtime.valid_canonical_task_ids_for_role_profile_v1(EXPECTED_ROLE_PROFILE)
    )
    if not (
        selected_seed.valid is True
        and tuple(selected_seed.reasons) == ()
        and selected_seed.primary_anchor_atom_id == PRIMARY_ANCHOR
        and selected_tasks == DIRECT_APPLICABLE_TASK_IDS
    ):
        _fail("PUBLISHED_SELECTED_SEED_OR_TASK_RUNTIME_FAILED")
    alternative_role = runtime.validate_role_profile_v1(
        role_profile="STRICT_LINKER_PRESENT_V1",
        retained_heavy_atoms=graph["atom_ids"],
        scaffold_atoms=ALTERNATIVE_SCAFFOLD_ATOMS,
        linker_atoms=ALTERNATIVE_LINKER_ATOMS,
        warhead_atoms=ALTERNATIVE_WARHEAD_ATOMS,
        reactive_atom_id="CB",
        explicit_graph_bonds=graph["bonds"],
    )
    alternative_seed = runtime.validate_minimal_seed_for_role_profile_v1(
        role_profile="STRICT_LINKER_PRESENT_V1",
        seed_atoms=ALTERNATIVE_SEED,
        scaffold_atoms=ALTERNATIVE_SCAFFOLD_ATOMS,
        linker_atoms=ALTERNATIVE_LINKER_ATOMS,
        warhead_atoms=ALTERNATIVE_WARHEAD_ATOMS,
        explicit_graph_bonds=graph["bonds"],
        primary_anchor_atom_id=PRIMARY_ANCHOR,
    )
    alternative_tasks = tuple(
        runtime.valid_canonical_task_ids_for_role_profile_v1("STRICT_LINKER_PRESENT_V1")
    )
    if not (
        alternative_role.valid is True
        and tuple(alternative_role.reasons) == ()
        and alternative_seed.valid is True
        and tuple(alternative_seed.reasons) == ()
        and alternative_seed.primary_anchor_atom_id == PRIMARY_ANCHOR
        and alternative_tasks == (0, 1, 2, 3, 4)
    ):
        _fail("PUBLISHED_ALTERNATIVE_RUNTIME_FAILED")
    return {
        "selected": {
            "valid": True,
            "reasons": [],
            "candidate_id": SELECTED_CANDIDATE,
            "profile": EXPECTED_ROLE_PROFILE,
            "counts": {"W": 3, "L": 0, "S": 3},
            "boundary": BOUNDARY,
            "minimal_seed_atom_ids": list(MINIMAL_SEED),
            "primary_anchor_atom_id": PRIMARY_ANCHOR,
            "applicable_task_ids": list(selected_tasks),
        },
        "unselected_alternative": {
            "valid": True,
            "reasons": [],
            "candidate_id": ALTERNATIVE_CANDIDATE,
            "profile": "STRICT_LINKER_PRESENT_V1",
            "counts": {"W": 1, "L": 2, "S": 3},
            "minimal_seed_atom_ids": list(ALTERNATIVE_SEED),
            "primary_anchor_atom_id": PRIMARY_ANCHOR,
            "applicable_task_ids": list(alternative_tasks),
            "human_selected": False,
            "authoritative_event_labels_created": False,
        },
        "partition_validator": "validate_role_profile_v1",
        "seed_validator": "validate_minimal_seed_for_role_profile_v1",
        "task_applicability_owner": "valid_canonical_task_ids_for_role_profile_v1",
    }


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
    source = generic.NormalizedDecisionSource(
        binding=binding, facts=tuple(fact_objects)
    )
    if type(source) is not generic.NormalizedDecisionSource or len(source.facts) != 4:
        _fail("GENERIC_NORMALIZED_SOURCE_INVALID")
    return {
        "generic_exact11_compatibility_pass": True,
        "generic_fact_field_count": 11,
        "generic_fact_fields": list(GENERIC_FACT_FIELDS),
        "accepted_fact_count": 4,
        "source_formal_generation_domain_decision": SOURCE_D2,
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "source_formal_training_use_decision": SOURCE_D6,
        "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "facts": projected,
        "rich_fields_leaked": False,
        "NormalizedDecisionSource_constructed": True,
        "reconciliation_performed": False,
    }


def _current_census(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    rows = _parse_csv(payloads[CENSUS_MATRIX_RELATIVE], "CURRENT_WITH_6OA_CENSUS")
    if len(rows) != 1000 or len({row.get("canonical_event_id") for row in rows}) != 1000:
        _fail("CURRENT_CENSUS_UNIVERSE_DRIFT")
    targets = [row for row in rows if row.get("canonical_event_id") in set(EXPECTED_EVENT_IDS)]
    unit_rows = [row for row in rows if row.get("review_unit_id") == EXPECTED_REVIEW_UNIT_ID]
    if (
        len(targets) != 4
        or len(unit_rows) != 4
        or tuple(row.get("canonical_event_id") for row in targets) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in targets) != EXPECTED_RANKS
    ):
        _fail("CURRENT_CENSUS_PYR_EXACT4_DRIFT")
    expected_prior = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false",
        "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
        "human_training_excluded": "false",
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
    }
    for row in targets:
        for key, value in expected_prior.items():
            if row.get(key) != value:
                _fail("CURRENT_CENSUS_PYR_PRIOR_STATE_DRIFT:" + key)
    summary = _strict_json(payloads[CENSUS_SUMMARY_RELATIVE], "CURRENT_WITH_6OA_SUMMARY")
    manifest = _strict_json(payloads[CENSUS_MANIFEST_RELATIVE], "CURRENT_WITH_6OA_MANIFEST")
    for document, label in ((summary, "SUMMARY"), (manifest, "MANIFEST")):
        _expect(
            document.get("schema_version"),
            "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1",
            "CURRENT_CENSUS_" + label + "_SCHEMA_DRIFT",
        )
    _expect_fields(
        summary.get("authority_boundary"),
        {
            "next_priority_review_current_pending_rank": 1,
            "next_priority_review_event_count": 4,
            "next_priority_review_ligand": "PYR",
            "next_priority_review_pdb": "1F8M",
            "next_priority_review_raw_priority_rank": 30,
            "next_priority_review_unit": EXPECTED_REVIEW_UNIT_ID,
            "NEXT_REVIEW_STARTED": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "CURRENT_CENSUS_NEXT_PRIORITY_DRIFT",
    )
    pending = summary.get("top_pending_review_units_by_event_yield")
    if type(pending) is not list or not pending:
        _fail("CURRENT_CENSUS_PENDING_LIST_MISSING")
    _expect_fields(
        pending[0],
        {
            "rank": 1,
            "raw_priority_rank": 30,
            "event_count": 4,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "current_review_status": "CURRENTLY_UNREVIEWED",
            "ligand_component_ids": ["PYR"],
            "pdb_ids": ["1F8M"],
        },
        "CURRENT_CENSUS_PENDING_RANK1_DRIFT",
    )
    return {
        "row_count": 1000,
        "PYR_event_count": 4,
        "PYR_current_global_status": "CURRENTLY_UNREVIEWED",
        "PYR_current_review_status": "CURRENTLY_UNREVIEWED",
        "PYR_human_review_completed": False,
        "PYR_chemistry": "UNRESOLVED",
        "PYR_task_relevance": "UNRESOLVED",
        "PYR_training_use": "UNRESOLVED",
        "current_pending_rank": 1,
        "raw_priority_rank": 30,
        "next_priority_review_ligand": "PYR",
        "census_modified_by_ingestion": False,
    }


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Bind sources and independently validate frozen PYR authority."""
    root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    payloads = _verify_bindings(root, overrides)
    formal = _strict_json(payloads[FORMAL_DECISION_RELATIVE], "PYR_FORMAL_DECISION")
    _validate_formal(formal)
    events = _validate_event_evidence(payloads[EVENT_EVIDENCE_RELATIVE])
    graph = _validate_graph_evidence(payloads[GRAPH_EVIDENCE_RELATIVE])
    audit = {
        row["canonical_event_id"]: row
        for row in graph["pre_event_audit"]  # type: ignore[union-attr]
    }
    for event in events:
        event.update(audit[event["canonical_event_id"]])
    _validate_semantic_owners(payloads)
    runtime = _runtime_validation(root, graph)
    generic = _generic_compatibility(root)
    census = _current_census(payloads)
    return {
        "formal_document": formal,
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "active_source_bindings": [_binding_record(binding) for binding in ACTIVE_BINDINGS],
        "active_source_binding_count": 13,
        "events": events,
        "graph_proof": {
            "Exact6_count": 6,
            "Exact5_bond_count": 5,
            "partition_pairwise_disjoint": True,
            "partition_exhaustive": True,
            "W_connected": True,
            "L_connected_or_empty": True,
            "S_connected": True,
            "reactive_CB_in_W": True,
            "cross_role_boundary_count": 1,
            "cross_role_boundary": BOUNDARY,
            "graph_digest_namespaces": graph["graph_digest_namespaces"],
        },
        "published_runtime_validation": runtime,
        "generic_Exact11_compatibility": generic,
        "current_census_boundary": census,
    }


def _normalization_contract() -> dict[str, object]:
    return {
        "task_relevance": {
            "source_field": "D2_task_generation_domain_relevance",
            "source_formal_generation_domain_decision": SOURCE_D2,
            "target_field": "task_relevance_disposition",
            "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "mapping": "IN_DOMAIN_TO_RELEVANT",
            "source_value_preserved": True,
        },
        "training_disposition": {
            "source_field": "D6_later_training_use_disposition",
            "source_formal_training_use_decision": SOURCE_D6,
            "target_field": "training_disposition",
            "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
            "mapping": "EXCLUDE_TO_EXCLUDE_FROM_TRAINING_ONLY",
            "source_value_preserved": True,
        },
        "direction": "FORMAL_SOURCE_TO_GENERIC_RECONCILIATION_VOCABULARY",
        "chemistry_disposition_changed_by_normalization": False,
        "human_training_excluded_preserved": True,
        "EXCLUDE_mapped_to_NOT_APPLICABLE": False,
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
                "structurally_applicable": task_id in DIRECT_APPLICABLE_TASK_IDS,
            }
            for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task": False,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "sample_applicable_task_ids": list(DIRECT_APPLICABLE_TASK_IDS),
        "task_applicability_determined": True,
        "task_applicability_sample_authority": True,
        "task_applicability_is_structural_metadata_only": True,
        "task_label_authority": False,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "mask_tensor_targets_created": False,
        "training_mask_targets_available_now": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "source_formal_training_use_decision": SOURCE_D6,
        "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "training_use_allowed": False,
        "human_training_excluded": True,
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
        "exclusion_is_chemistry_negative": False,
        "EXCLUDE_is_NOT_APPLICABLE": False,
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
    }


def _pre_boundary() -> dict[str, object]:
    return {
        "supporting_adduct_source_graph_count_per_event": 1,
        "candidate_PRE_free_source_graph_count_per_event": 1,
        "mapping_count_per_event": 0,
        "PRE_source_mapping_status": PRE_MAPPING_STATUS,
        "final_PRE_reaction_status": PRE_STATUS,
        "PRE_authority": False,
        "POST_to_PRE_copy": False,
        "PRE_zero_fill": False,
        "PRE_coordinates_created": False,
        "PRE_topology_created": False,
        "C_Br_bond_created": False,
        "leaving_group_inferred": False,
        "reagent_inferred": False,
        "reaction_edit_inferred": False,
        "source_graphs_supporting_not_sample_specific_PRE_authority": True,
    }


def _post_boundary() -> dict[str, object]:
    return {
        "representation": "OBSERVED_POST",
        "POST_source_evidence_available": True,
        "explicit_covalent_evidence": True,
        "distance_only_inference": False,
        "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
        "pair_identity_authority_is_exact_geometry_training_authority": False,
        "observed_distances_angstrom": [float(row[6]) for row in EXPECTED_EVENTS],
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
        "HUMAN_TRAINING_EXCLUDED": True,
        "FUTURE_TRAINING_ADMISSION_CANDIDATE": False,
        "FORMAL_TRAINING_ADMITTED": False,
        "TASK_LABEL_AUTHORITY": False,
        "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "MASK_TENSOR_TARGETS_CREATED": False,
        "TRAINING_ADMISSION_CREATED": False,
        "TRAINING_MATERIALIZATION_ALLOWED": False,
        "PARAMETER_UPDATE_AUTHORIZATION": False,
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
        "STEP12D_STATUS": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
    }


def _event_projection(event: Mapping[str, object]) -> dict[str, object]:
    return {
        **event,
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": "1F8M",
        "ligand_component_id": "PYR",
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "human_review_completed": True,
        "source_formal_generation_domain_decision": SOURCE_D2,
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "source_formal_training_use_decision": SOURCE_D6,
        "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "chemistry_disposition": "POSITIVE",
        "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "positive_generative_supervision_eligible": False,
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "CB",
        "pair_sample_authority": True,
        "role_sample_authority": True,
        "task_applicability_sample_authority": True,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "applicable_task_ids": list(DIRECT_APPLICABLE_TASK_IDS),
        "task_label_authority": False,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "mask_tensor_targets_created": False,
        "POST_source_evidence_available": True,
        "explicit_covalent_evidence": True,
        "distance_only_inference": False,
        "distance_normalized": False,
        "event_removed": False,
        "new_bond_order_inferred": False,
        "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
        "mapping_count": 0,
        "PRE_source_mapping_status": PRE_MAPPING_STATUS,
        "final_PRE_reaction_status": PRE_STATUS,
        "PRE_authority": False,
        "POST_to_PRE_copy": False,
        "PRE_zero_fill": False,
        **_training_boundary(),
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "DETERMINISTIC_METADATA_ONLY_COMPLETED_DECISION_PROJECTION",
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
        "network_required": False,
        "sample_identity": {
            "PDB": "1F8M",
            "ligand_component_id": "PYR",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "authority_scope": EXPECTED_SCOPE,
            "event_count": 4,
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
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "approval_time": None,
            "approval_time_status": "NOT_PROVIDED_VERIFIABLY",
            "formal_sample_level_authority_created": True,
            "human_review_completed": True,
            "formal_decision_created": True,
            "machine_generated_human_authorization": False,
            "platform_identity_verification_claimed": False,
            "independent_identity_authentication_claimed": False,
            "authorization_bound_candidate_SHA256": (
                "db81fe86ac264fb9eed5ef5d1ac40eaffb0896b48429cfe7471b2d0669f56b69"
            ),
        },
        "source_formal_D1_D6": {
            "D1_observed_covalent_chemistry": "POSITIVE",
            "D2_task_generation_domain_relevance": SOURCE_D2,
            "D3_reactive_atom_pair": "CONFIRM_OBSERVED_PAIR",
            "D3_observed_pair": "SG:CB",
            "D4_role_partition_and_minimal_seed_action": "PROVIDE_ROLE_PARTITION",
            "D4_selected_candidate": SELECTED_CANDIDATE,
            "D5_structural_task_applicability_action": "PROVIDE_APPLICABLE_TASK_IDS",
            "D5_applicable_task_ids": list(DIRECT_APPLICABLE_TASK_IDS),
            "D6_later_training_use_disposition": SOURCE_D6,
        },
        "normalization_contract": _normalization_contract(),
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "sample_authority_map": {
            "chemistry_sample_authority": True,
            "task_relevance_sample_authority": True,
            "pair_sample_authority": True,
            "role_sample_authority": True,
            "minimal_seed_sample_authority": True,
            "task_applicability_sample_authority": True,
            "training_use_disposition_sample_authority": True,
            "task_label_authority": False,
            "POST_geometry_training_authority": False,
            "PRE_authority": False,
        },
        "events": [_event_projection(event) for event in bound["events"]],
        "reactive_pair_authority": {
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CB",
            "observed_pair": "SG:CB",
            "scope": EXPECTED_SCOPE,
            "sample_level_authoritative": True,
            "reusable_pair_authority": False,
            "ligand_wide_authority": False,
            "cross_structure_generalization": False,
        },
        "selected_role_partition": {
            "selected_candidate_id": SELECTED_CANDIDATE,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "warhead_atom_ids": list(WARHEAD_ATOMS),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(SCAFFOLD_ATOMS),
            "counts": {"W": 3, "L": 0, "S": 3, "Exact": 6},
            "boundary": BOUNDARY,
            "minimal_seed_atom_ids": list(MINIMAL_SEED),
            "primary_anchor": PRIMARY_ANCHOR,
            "sample_level_authoritative": True,
            "reusable_role_authority": False,
            "PRE_precursor_role_authority": False,
            "published_runtime_validation": bound["published_runtime_validation"]["selected"],
        },
        "unselected_alternatives": {
            "alternative_candidate_id": ALTERNATIVE_CANDIDATE,
            "alternative_human_selected": False,
            "alternative_formal_selected": False,
            "alternative_authority_created": False,
            "warhead_atom_ids": list(ALTERNATIVE_WARHEAD_ATOMS),
            "linker_atom_ids": list(ALTERNATIVE_LINKER_ATOMS),
            "scaffold_atom_ids": list(ALTERNATIVE_SCAFFOLD_ATOMS),
            "minimal_seed_atom_ids": list(ALTERNATIVE_SEED),
            "primary_anchor": PRIMARY_ANCHOR,
            "authoritative_event_labels_created": False,
            "published_runtime_validation": bound[
                "published_runtime_validation"
            ]["unselected_alternative"],
        },
        "structural_validation": bound["graph_proof"],
        "canonical_task_contract": _task_contract(),
        "generic_Exact11_compatibility": bound["generic_Exact11_compatibility"],
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(),
        "training_boundary": _training_boundary(),
        "non_created_authority": {
            "reusable_authority_created": False,
            "reaction_family_authority": False,
            "warhead_rule_authority": False,
            "warhead_type_authority": False,
            "PRE_authority": False,
            "POST_geometry_training_authority": False,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
            "formal_training_admitted": False,
            "training_materialization_allowed": False,
            "parameter_update_authorization": False,
        },
        "current_with_6OA_census_preingestion_boundary": bound[
            "current_census_boundary"
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
    "protein_chain_or_asym",
    "ligand_component_id",
    "ligand_chain_or_asym",
    "ligand_auth_chain",
    "selected_connection_id",
    "POST_distance_angstrom",
    "reported_POST_distance_angstrom",
    "distance_normalized",
    "event_removed",
    "new_bond_order_inferred",
    "legacy_completed_review_status",
    "human_review_completed",
    "source_formal_generation_domain_decision",
    "normalized_task_relevance_disposition",
    "source_formal_training_use_decision",
    "normalized_training_disposition",
    "chemistry_disposition",
    "negative_chemistry",
    "task_domain_negative",
    "protein_reactive_atom",
    "ligand_reactive_atom",
    "pair_sample_authority",
    "role_profile",
    "role_sample_authority",
    "warhead_atom_ids_json",
    "linker_atom_ids_json",
    "scaffold_atom_ids_json",
    "boundary_json",
    "minimal_seed_atom_ids_json",
    "primary_anchor",
    "canonical_task_count",
    "B3_present",
    "sixth_task",
    "structurally_applicable_task_ids_json",
    "task_applicability_sample_authority",
    "task_label_authority",
    "authoritative_task_labels_created",
    "event_task_label_rows_materialized",
    "mask_tensor_targets_created",
    "training_use_allowed",
    "human_training_excluded",
    "future_training_admission_candidate",
    "formal_training_admitted",
    "training_materialization_allowed",
    "model_supervision_usable",
    "POST_source_evidence_available",
    "explicit_covalent_evidence",
    "distance_only_inference",
    "POST_geometry_training_authority",
    "POST_geometry_training_target_created",
    "supporting_adduct_source_graph_count",
    "supporting_adduct_graph_SHA256",
    "candidate_PRE_free_source_graph_count",
    "candidate_PRE_free_source_graph_SHA256",
    "mapping_count",
    "PRE_source_mapping_status",
    "final_PRE_reaction_status",
    "PRE_authority",
    "POST_to_PRE_copy",
    "PRE_zero_fill",
    "reusable_pair_authority",
    "reusable_role_authority",
    "reaction_family_authority",
    "warhead_rule_authority",
    "warhead_type_authority",
    "parameter_update_authorization",
    "FEATURE_SEMANTICS_AUDIT_PERFORMED",
    "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING",
    "READY_FOR_TRAINING",
    "TRAINING_STARTED",
)


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        row: dict[str, object] = {
            "artifact_role": "TASK_LABEL_AVAILABILITY_METADATA_ONLY",
            "canonical_event_id": event["canonical_event_id"],
            "scaleup_rank": event["scaleup_rank"],
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "pdb_id": "1F8M",
            "protein_chain_or_asym": event["protein_chain_or_asym"],
            "ligand_component_id": "PYR",
            "ligand_chain_or_asym": event["ligand_chain_or_asym"],
            "ligand_auth_chain": event["ligand_auth_chain"],
            "selected_connection_id": event["selected_connection_id"],
            "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
            "reported_POST_distance_angstrom": event[
                "reported_POST_distance_frozen_lexeme"
            ],
            "distance_normalized": "false",
            "event_removed": "false",
            "new_bond_order_inferred": "false",
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "human_review_completed": "true",
            "source_formal_generation_domain_decision": SOURCE_D2,
            "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "source_formal_training_use_decision": SOURCE_D6,
            "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
            "chemistry_disposition": "POSITIVE",
            "negative_chemistry": "false",
            "task_domain_negative": "false",
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CB",
            "pair_sample_authority": "true",
            "role_profile": EXPECTED_ROLE_PROFILE,
            "role_sample_authority": "true",
            "warhead_atom_ids_json": _json_cell(list(WARHEAD_ATOMS)),
            "linker_atom_ids_json": "[]",
            "scaffold_atom_ids_json": _json_cell(list(SCAFFOLD_ATOMS)),
            "boundary_json": _json_cell(BOUNDARY),
            "minimal_seed_atom_ids_json": _json_cell(list(MINIMAL_SEED)),
            "primary_anchor": PRIMARY_ANCHOR,
            "canonical_task_count": 5,
            "B3_present": "true",
            "sixth_task": "false",
            "structurally_applicable_task_ids_json": "[0,3,4]",
            "task_applicability_sample_authority": "true",
            "task_label_authority": "false",
            "authoritative_task_labels_created": "false",
            "event_task_label_rows_materialized": "false",
            "mask_tensor_targets_created": "false",
            "training_use_allowed": "false",
            "human_training_excluded": "true",
            "future_training_admission_candidate": "false",
            "formal_training_admitted": "false",
            "training_materialization_allowed": "false",
            "model_supervision_usable": "false",
            "POST_source_evidence_available": "true",
            "explicit_covalent_evidence": "true",
            "distance_only_inference": "false",
            "POST_geometry_training_authority": "false",
            "POST_geometry_training_target_created": "false",
            "supporting_adduct_source_graph_count": 1,
            "supporting_adduct_graph_SHA256": event[
                "supporting_adduct_graph_SHA256"
            ],
            "candidate_PRE_free_source_graph_count": 1,
            "candidate_PRE_free_source_graph_SHA256": event[
                "candidate_PRE_free_source_graph_SHA256"
            ],
            "mapping_count": 0,
            "PRE_source_mapping_status": PRE_MAPPING_STATUS,
            "final_PRE_reaction_status": PRE_STATUS,
            "PRE_authority": "false",
            "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false",
            "reusable_pair_authority": "false",
            "reusable_role_authority": "false",
            "reaction_family_authority": "false",
            "warhead_rule_authority": "false",
            "warhead_type_authority": "false",
            "parameter_update_authorization": "false",
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": "false",
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": "true",
            "READY_FOR_TRAINING": "false",
            "TRAINING_STARTED": "false",
        }
        if set(row) != set(MATRIX_HEADER):
            _fail("MATRIX_ROW_HEADER_MISMATCH")
        rows.append(row)
    return rows


def _summary(snapshot: Mapping[str, Any]) -> dict[str, object]:
    events = snapshot["events"]
    count = lambda key, value: sum(event.get(key) == value for event in events)
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "review_unit": "PYR",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": len(events),
        "review_unit_count": len({event["review_unit_id"] for event in events}),
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "source_formal_generation_domain_decision": SOURCE_D2,
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "source_formal_training_use_decision": SOURCE_D6,
        "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
        "task_relevant_count": count(
            "normalized_task_relevance_disposition", NORMALIZED_TASK_RELEVANCE
        ),
        "chemistry_positive_count": count("chemistry_disposition", "POSITIVE"),
        "negative_chemistry_count": count("negative_chemistry", True),
        "pair_authority_event_count": count("pair_sample_authority", True),
        "role_authority_event_count": count("role_sample_authority", True),
        "task_applicability_determined_event_count": count(
            "task_applicability_sample_authority", True
        ),
        "task_label_authority_count": count("task_label_authority", True),
        "event_task_label_rows_materialized_count": count(
            "event_task_label_rows_materialized", True
        ),
        "mask_tensor_target_count": count("mask_tensor_targets_created", True),
        "training_EXCLUDE_FROM_TRAINING_ONLY_count": count(
            "normalized_training_disposition", NORMALIZED_TRAINING_DISPOSITION
        ),
        "human_training_excluded_count": count("human_training_excluded", True),
        "future_training_admission_candidate_count": count(
            "future_training_admission_candidate", True
        ),
        "formal_training_admitted_count": count("formal_training_admitted", True),
        "PRE_authority_count": count("PRE_authority", True),
        "POST_training_authority_count": count(
            "POST_geometry_training_authority", True
        ),
        "generic_exact11_accepted_count": 4,
        "generic_exact11_fact_count": 4,
        "rich_fields_leaked_to_generic_facts": False,
        "normalization_contract": _normalization_contract(),
        "canonical_task_contract": _task_contract(),
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
        raise PYRIngestionSafetyError(
            "COVAPIE_PYR_INGESTION_V1_ERROR:TEXT_UTF8_INVALID:" + label
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
            raise PYRIngestionSafetyError(
                "COVAPIE_PYR_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
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
        "artifact_role": "PYR_COMPLETED_DECISION_METADATA_ONLY_INGESTION_MANIFEST",
        "candidate_publication_file_count": 7,
        "candidate_publication_paths": [
            path.as_posix() for path in CANDIDATE_PUBLICATION_PATHS
        ],
        "output_artifact_count": 4,
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "matrix_header_frozen": True,
        "matrix_header": list(MATRIX_HEADER),
        "candidate_source_bindings": _candidate_source_records(repo_root),
        "output_artifact_bindings_excluding_manifest_self": output_bindings,
        "active_source_binding_count": 13,
        "semantic_source_identity_count": 13,
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
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "generic_Exact11_compatibility": bound["generic_Exact11_compatibility"],
        "published_runtime_validation": bound["published_runtime_validation"],
        "current_census_boundary": bound["current_census_boundary"],
        "canonical_task_contract": _task_contract(),
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
            "PDB": "1F8M",
            "ligand_component_id": "PYR",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "authority_scope": EXPECTED_SCOPE,
            "event_count": 4,
            "scaleup_event_ranks": list(EXPECTED_RANKS),
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
        },
        "SNAPSHOT_SAMPLE_IDENTITY_DRIFT",
    )
    events = snapshot.get("events")
    if type(events) is not list or len(events) != 4:
        _fail("SNAPSHOT_EVENTS_NOT_EXACT4")
    if len({event.get("canonical_event_id") for event in events}) != 4:
        _fail("SNAPSHOT_EVENTS_NOT_UNIQUE_EXACT4")
    for event, expected in zip(events, EXPECTED_EVENTS, strict=True):
        event_id, rank, protein, ligand, ligand_auth, connection, exact, reported = expected
        _expect_fields(
            event,
            {
                "canonical_event_id": event_id,
                "scaleup_rank": rank,
                "protein_chain_or_asym": protein,
                "ligand_chain_or_asym": ligand,
                "ligand_auth_chain": ligand_auth,
                "selected_connection_id": connection,
                "POST_distance_frozen_lexeme": exact,
                "reported_POST_distance_frozen_lexeme": reported,
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
                "pdb_id": "1F8M",
                "ligand_component_id": "PYR",
                "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
                "human_review_completed": True,
                "source_formal_generation_domain_decision": SOURCE_D2,
                "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
                "source_formal_training_use_decision": SOURCE_D6,
                "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
                "task_relevance_disposition": "RELEVANT",
                "chemistry_disposition": "POSITIVE",
                "training_disposition": NORMALIZED_TRAINING_DISPOSITION,
                "negative_chemistry": False,
                "task_domain_negative": False,
                "positive_generative_supervision_eligible": False,
                "protein_reactive_atom": "SG",
                "ligand_reactive_atom": "CB",
                "pair_sample_authority": True,
                "role_sample_authority": True,
                "task_applicability_sample_authority": True,
                "applicable_task_ids": [0, 3, 4],
                "task_label_authority": False,
                "authoritative_task_labels_created": False,
                "event_task_label_rows_materialized": False,
                "mask_tensor_targets_created": False,
                "distance_normalized": False,
                "event_removed": False,
                "new_bond_order_inferred": False,
                "supporting_adduct_graph_count": 1,
                "candidate_PRE_free_source_graph_count": 1,
                "source_PRE_mapping_count": 0,
                "mapping_count": 0,
                "PRE_source_mapping_status": PRE_MAPPING_STATUS,
                "final_PRE_reaction_status": PRE_STATUS,
                "PRE_authority": False,
                "POST_to_PRE_copy": False,
                "PRE_zero_fill": False,
                "human_training_excluded": True,
                "future_training_admission_candidate": False,
                "formal_training_admitted": False,
                "training_materialization_allowed": False,
                "POST_geometry_training_authority": False,
                "READY_FOR_TRAINING": False,
                "TRAINING_STARTED": False,
            },
            "SNAPSHOT_EVENT_DRIFT:" + str(rank),
        )
        if event.get("supporting_adduct_graph_SHA256") != (
            "0b768daa07ecce9dc8a01db879373898bfdb82721082c1d76ea33ce217634ff9"
        ):
            _fail("SNAPSHOT_SUPPORTING_GRAPH_DIGEST_DRIFT:" + str(rank))
        if event.get("candidate_PRE_free_source_graph_SHA256") != (
            "39da817bd08cdc712ac58bf04ef5e7ff5be8557a86845fb0601ac8c6d73a6673"
        ):
            _fail("SNAPSHOT_CANDIDATE_PRE_GRAPH_DIGEST_DRIFT:" + str(rank))
    _expect_fields(
        snapshot.get("selected_role_partition"),
        {
            "selected_candidate_id": SELECTED_CANDIDATE,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "warhead_atom_ids": list(WARHEAD_ATOMS),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(SCAFFOLD_ATOMS),
            "counts": {"W": 3, "L": 0, "S": 3, "Exact": 6},
            "boundary": BOUNDARY,
            "minimal_seed_atom_ids": list(MINIMAL_SEED),
            "primary_anchor": PRIMARY_ANCHOR,
            "sample_level_authoritative": True,
            "reusable_role_authority": False,
        },
        "SNAPSHOT_SELECTED_ROLE_DRIFT",
    )
    alternative = snapshot.get("unselected_alternatives")
    _expect_fields(
        alternative,
        {
            "alternative_candidate_id": ALTERNATIVE_CANDIDATE,
            "alternative_human_selected": False,
            "alternative_formal_selected": False,
            "alternative_authority_created": False,
            "warhead_atom_ids": list(ALTERNATIVE_WARHEAD_ATOMS),
            "linker_atom_ids": list(ALTERNATIVE_LINKER_ATOMS),
            "scaffold_atom_ids": list(ALTERNATIVE_SCAFFOLD_ATOMS),
            "minimal_seed_atom_ids": list(ALTERNATIVE_SEED),
            "authoritative_event_labels_created": False,
        },
        "SNAPSHOT_ALTERNATIVE_DRIFT",
    )
    tasks = snapshot.get("canonical_task_contract")
    _expect_fields(
        tasks,
        {
            "global_canonical_task_count": 5,
            "B3_present": True,
            "sixth_task": False,
            "sample_applicable_task_ids": [0, 3, 4],
            "task_applicability_sample_authority": True,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
        },
        "SNAPSHOT_TASK_CONTRACT_DRIFT",
    )
    task_rows = tasks.get("global_canonical_tasks") if type(tasks) is dict else None
    if type(task_rows) is not list or [
        row.get("semantic_long_name") for row in task_rows if type(row) is dict
    ] != [row[1] for row in CANONICAL_TASKS]:
        _fail("SNAPSHOT_CANONICAL_TASK_LONG_NAMES_DRIFT")
    _expect(
        snapshot.get("PRE_boundary"), _pre_boundary(), "SNAPSHOT_PRE_DRIFT"
    )
    _expect(
        snapshot.get("POST_boundary"), _post_boundary(), "SNAPSHOT_POST_DRIFT"
    )
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
    _expect(
        snapshot.get("readiness"), _readiness(), "SNAPSHOT_READINESS_DRIFT"
    )
    generic = snapshot.get("generic_Exact11_compatibility")
    _expect_fields(
        generic,
        {
            "accepted_fact_count": 4,
            "generic_fact_field_count": 11,
            "source_formal_generation_domain_decision": SOURCE_D2,
            "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "source_formal_training_use_decision": SOURCE_D6,
            "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
            "rich_fields_leaked": False,
            "NormalizedDecisionSource_constructed": True,
            "reconciliation_performed": False,
        },
        "SNAPSHOT_GENERIC_DRIFT",
    )
    facts = generic.get("facts") if type(generic) is dict else None
    if type(facts) is not list or len(facts) != 4:
        _fail("SNAPSHOT_GENERIC_FACTS_NOT_EXACT4")
    if any(type(fact) is not dict or set(fact) != set(GENERIC_FACT_FIELDS) for fact in facts):
        _fail("SNAPSHOT_GENERIC_FACT_NOT_EXACT11")
    if [fact["canonical_event_id"] for fact in facts] != list(EXPECTED_EVENT_IDS):
        _fail("SNAPSHOT_GENERIC_EVENT_IDS_DRIFT")
    for fact in facts:
        _expect_fields(fact, GENERIC_PROJECTION, "SNAPSHOT_GENERIC_FACT_DRIFT")


def _validate_summary_semantics(summary: Mapping[str, Any]) -> None:
    _expect_fields(
        summary,
        {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "event_count": 4,
            "review_unit_count": 1,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "source_formal_generation_domain_decision": SOURCE_D2,
            "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "source_formal_training_use_decision": SOURCE_D6,
            "normalized_training_disposition": NORMALIZED_TRAINING_DISPOSITION,
            "task_relevant_count": 4,
            "chemistry_positive_count": 4,
            "negative_chemistry_count": 0,
            "pair_authority_event_count": 4,
            "role_authority_event_count": 4,
            "task_applicability_determined_event_count": 4,
            "task_label_authority_count": 0,
            "event_task_label_rows_materialized_count": 0,
            "mask_tensor_target_count": 0,
            "training_EXCLUDE_FROM_TRAINING_ONLY_count": 4,
            "human_training_excluded_count": 4,
            "future_training_admission_candidate_count": 0,
            "formal_training_admitted_count": 0,
            "PRE_authority_count": 0,
            "POST_training_authority_count": 0,
            "generic_exact11_accepted_count": 4,
            "generic_exact11_fact_count": 4,
            "rich_fields_leaked_to_generic_facts": False,
        },
        "SUMMARY_SEMANTICS_DRIFT",
    )
    _expect(
        summary.get("normalization_contract"),
        _normalization_contract(),
        "SUMMARY_NORMALIZATION_DRIFT",
    )
    _expect(
        summary.get("operation_boundary"),
        _operation_boundary(),
        "SUMMARY_OPERATION_BOUNDARY_DRIFT",
    )
    _expect(
        summary.get("readiness"), _readiness(), "SUMMARY_READINESS_DRIFT"
    )


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
            "matrix_header_frozen": True,
            "matrix_header": list(MATRIX_HEADER),
            "active_source_binding_count": 13,
            "semantic_source_identity_count": 13,
            "duplicate_source_binding_identity_count": 0,
            "formal_validator_provenance_identity_only": True,
            "formal_validator_imported": False,
            "formal_validator_executed_by_production": False,
            "formal_validator_subprocessed_by_production": False,
            "formal_semantics_independently_validated": True,
            "manifest_self_SHA256_recorded": False,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        },
        "MANIFEST_ROOT_DRIFT",
    )
    _expect(
        manifest.get("normalization_contract"),
        _normalization_contract(),
        "MANIFEST_NORMALIZATION_DRIFT",
    )
    active = manifest.get("active_source_bindings")
    expected_active = [_binding_record(binding) for binding in ACTIVE_BINDINGS]
    if active != expected_active:
        _fail("MANIFEST_ACTIVE_SOURCE_BINDINGS_DRIFT")
    identities = [row["semantic_source_identity"] for row in active]
    if len(set(identities)) != 13:
        _fail("MANIFEST_DUPLICATE_SOURCE_IDENTITY")
    candidate = manifest.get("candidate_source_bindings")
    if candidate != _candidate_source_records(repo_root):
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
        manifest.get("operation_boundary"),
        _operation_boundary(),
        "MANIFEST_OPERATION_DRIFT",
    )
    _expect(
        manifest.get("training_boundary"),
        _training_boundary(),
        "MANIFEST_TRAINING_DRIFT",
    )
    _expect(
        manifest.get("readiness"), _readiness(), "MANIFEST_READINESS_DRIFT"
    )
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
    matrix_rows = _parse_csv(artifacts[MATRIX], "MATRIX")
    summary = _strict_json(artifacts[SUMMARY], "SUMMARY")
    manifest = _strict_json(artifacts[MANIFEST], "MANIFEST")
    _validate_snapshot_semantics(snapshot)
    _validate_summary_semantics(summary)
    if len(matrix_rows) != 4 or tuple(matrix_rows[0]) != MATRIX_HEADER:
        _fail("MATRIX_EXACT4_OR_HEADER_DRIFT")
    expected_rows = _matrix_rows(snapshot)
    expected_matrix = _parse_csv(_csv_bytes(MATRIX_HEADER, expected_rows), "EXPECTED_MATRIX")
    if matrix_rows != expected_matrix:
        _fail("MATRIX_SEMANTICS_DRIFT")
    _validate_manifest_semantics(manifest, Path(repo_root).resolve(), artifacts)
    expected = _build_raw(Path(repo_root).resolve(), repository_path_overrides)
    for name in OUTPUT_FILENAMES:
        if artifacts[name] != expected[name]:
            _fail("ARTIFACT_PROJECTION_DRIFT:" + name)
    return {
        "status": "PASS",
        "event_count": 4,
        "matrix_column_count": len(MATRIX_HEADER),
        "output_artifact_count": 4,
        "generic_exact11_fact_count": 4,
        "FORMAL_SOURCE_D2": SOURCE_D2,
        "NORMALIZED_TASK_RELEVANCE": NORMALIZED_TASK_RELEVANCE,
        "FORMAL_SOURCE_D6": SOURCE_D6,
        "NORMALIZED_TRAINING_DISPOSITION": NORMALIZED_TRAINING_DISPOSITION,
        "HUMAN_TRAINING_EXCLUDED": True,
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
    descriptor, temporary = tempfile.mkstemp(prefix=".covapie_pyr_", dir=path.parent)
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
