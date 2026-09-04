"""Project frozen 0D8 Exact4 human authority into metadata-only artifacts.

The formal JSON is parsed and independently validated here.  Its validator is
bound as provenance identity only and is never parsed, imported, executed, or
subprocessed.  This owner performs no reconciliation, census/queue refresh,
dataset mutation, tensorization, model operation, training, or parameter
update.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
import copy
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
    "ZeroD8IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)


SCHEMA_VERSION = "covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_0d8_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_0d8_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_0d8_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_0d8_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_0d8_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_0d8_event_task_label_availability_v1.csv"
SUMMARY = "covapie_0d8_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_0d8_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

STATE_ROOT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "0D8_COVAPIE_BULK_REVIEW_UNIT_BF1809E89D22D405"
)
FORMAL_DECISION_RELATIVE = (
    STATE_ROOT / "formal-human-decision-v1/0d8_formal_human_decision_v1.json"
)
FORMAL_VALIDATOR_RELATIVE = (
    STATE_ROOT / "formal-human-decision-v1/validate_0d8_formal_human_decision_v1.py"
)
EVENT_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/0d8_exact4_event_evidence_v1.csv"
)
GRAPH_CANDIDATES_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/0d8_graph_and_role_candidates_v1.json"
)
SOURCE_BINDING_POLICY_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
CANONICAL_TASK_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
DIRECT_RUNTIME_OWNER_RELATIVE = Path(
    "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"
)
GENERIC_OWNER_RELATIVE = Path(
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py"
)
TASK_DOMAIN_NEGATIVE_MATRIX_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1/"
    "covapie_batch001_event_task_label_availability_v1.csv"
)
CENSUS_MATRIX_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_lcy_v1/"
    "covapie_cumulative1000_current_global_readiness_census_with_lcy_v1.csv"
)

BASELINE_COMMIT = "4387f9db73bf048f1a112ef44e289f7a784522b6"
FORMAL_DECISION_SCHEMA = "covapie_0d8_exact4_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "1e08ecef57fb9ca8e6316498f0b4a1270b063cafe9f5ca91fa71ed2045d452d9"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_BF1809E89D22D405"
EXPECTED_COMPLETED_LANE = "COMPLETED_TASK_DOMAIN_NEGATIVE"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
PAIR_AUTHORITY_SCOPE = "CURRENT_0D8_4V37_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
ROLE_AUTHORITY_SCOPE = "CURRENT_0D8_EXACT4_REVIEW_UNIT_ONLY"
AUTHORITY_SOURCE = "FORMAL_0D8_HUMAN_DECISION"
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_NOT_AVAILABLE"
PRE_STATUS = "PRE_REACTION_UNRESOLVED"

EXPECTED_D6 = (
    "Treat the current 0D8 4V37 Exact4 as task-domain negative for the present "
    "CovaPIE target-directed medicinal covalent small-molecule domain while "
    "preserving chemistry-positive sample-level evidence. The frozen structure "
    "contains four explicit CYS-SG ↔ 0D8-C8 covalent connections with independently "
    "reproduced POST distances, and the reviewer-supplied 4V37 context describes a "
    "cysteine thiohemiacetal with 3-aminopropionaldehyde; confirm the observed SG-C8 "
    "pair for the current Exact4 only. Select DIRECT candidate 0 as the sample-level "
    "role partition: W=[C8,OH], L=[], S=[C7,CA3,N3], with the C7-C8 scaffold/warhead "
    "boundary. This selection is a human scientific assignment for the current "
    "review unit only; it does not create a reusable role rule, reusable C8 "
    "regiochemistry, reaction-family, warhead-rule, or warhead-type authority. The "
    "deposited 0D8 CCD graph remains the source-derived 3-aminopropan-1-ol graph; "
    "interpreting it as a local post-thiohemiacetal representation is supporting "
    "scientific inference only and not PRE ground truth. PRE remains "
    "PRE_SOURCE_GRAPH_NOT_AVAILABLE / PRE_REACTION_UNRESOLVED; do not reconstruct a "
    "C8=O aldehyde, delete OH, copy POST to PRE, infer bond edits, reagents, leaving "
    "groups, or PRE coordinates. The additional 0D8 instance Q is supporting "
    "same-structure context only and receives no target or authority transfer. Set "
    "training use to NOT_APPLICABLE, not EXCLUDE_FROM_TRAINING_ONLY; "
    "human_training_excluded remains false. No formal training admission, tensor "
    "target, runtime usability, or parameter-update authority is created."
)
EXPECTED_D6_BYTE_COUNT = 1575
EXPECTED_D6_SHA256 = "1a7ffcde15d740dda7309dcc372f727faa23c203c0432ae9f24235389b3a2a44"

# Event ID, rank, protein asym, ligand asym, connection, exact POST, reported POST.
EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:4V37:A:CYS:450-:SG:F:0D8:C8",
        909, "A", "F", "covale1", "1.708043", "1.708",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4V37:B:CYS:450-:SG:K:0D8:C8",
        910, "B", "K", "covale2", "1.730046", "1.730",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4V37:C:CYS:450-:SG:P:0D8:C8",
        911, "C", "P", "covale3", "1.722747", "1.723",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4V37:D:CYS:450-:SG:V:0D8:C8",
        912, "D", "V", "covale4", "1.703643", "1.704",
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)
WARHEAD_ATOMS = ("C8", "OH")
LINKER_ATOMS: tuple[str, ...] = ()
SCAFFOLD_ATOMS = ("C7", "CA3", "N3")
HEAVY_ATOMS = ("C7", "C8", "CA3", "N3", "OH")
HEAVY_BONDS = (
    ("C7", "C8", "SING"),
    ("C7", "CA3", "SING"),
    ("C8", "OH", "SING"),
    ("CA3", "N3", "SING"),
)
BOUNDARY_BONDS = (
    {
        "atom_id_1": "C7",
        "atom_id_2": "C8",
        "bond_order": "SING",
        "role_1": "S",
        "role_2": "W",
    },
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
    "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
    "task_relevance_disposition": "NOT_RELEVANT",
    "chemistry_disposition": "POSITIVE",
    "training_disposition": "NOT_APPLICABLE",
    "human_training_excluded": False,
}

# path, namespace, bytes, SHA256, expected executable, source role, method
_Binding = tuple[Path, str, int, str, bool, str, str]
FORMAL_BINDINGS: tuple[_Binding, ...] = (
    (
        FORMAL_DECISION_RELATIVE,
        "project_parent_relative",
        36906,
        "089ee969c9a82d6fea86135623189dfc88a7aa26b78d6846407b294389b0de41",
        False,
        "0D8_FROZEN_FORMAL_HUMAN_DECISION",
        "PARSED_JSON_AND_INDEPENDENTLY_VALIDATED",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE,
        "project_parent_relative",
        88809,
        "29063521874b92a91f9bf03caad3d0f58c2f31bbb2323d45fcd2d6bcd0b4ce83",
        False,
        "0D8_FROZEN_FORMAL_VALIDATOR_PROVENANCE_IDENTITY_ONLY",
        "PROVENANCE_IDENTITY_ONLY_NOT_PARSED_IMPORTED_EXECUTED_OR_SUBPROCESSED",
    ),
)
SUPPORTING_BINDINGS: tuple[_Binding, ...] = (
    (
        EVENT_EVIDENCE_RELATIVE,
        "project_parent_relative",
        9751,
        "28c7eb818d66a6ce7e8b2bf34fcf8c3d1beb260a15cf78b1a3af7d8079f1217a",
        False,
        "0D8_EXACT4_EVENT_EVIDENCE",
        "PARSED_CSV_SUPPORTING_EVIDENCE",
    ),
    (
        GRAPH_CANDIDATES_RELATIVE,
        "project_parent_relative",
        35206,
        "3c215c05e45be5ab725600c15179e6c1ca352be5c19b015ae0b013528b165dda",
        False,
        "0D8_GRAPH_AND_ROLE_CANDIDATES_EVIDENCE",
        "PARSED_JSON_SELECTED_CANDIDATE_CROSS_CHECK",
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
        CANONICAL_TASK_OWNER_RELATIVE,
        "repository_relative",
        67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        False,
        "PUBLISHED_CANONICAL_EXACT5_SEMANTIC_OWNER",
        "PARSED_AST_LITERAL_CONTRACT_ONLY",
    ),
    (
        DIRECT_RUNTIME_OWNER_RELATIVE,
        "repository_relative",
        37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        False,
        "PUBLISHED_DIRECT_ROLE_RUNTIME_OWNER",
        "IMPORTED_AND_CALLED_FOR_SELECTED_PARTITION",
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
    (
        TASK_DOMAIN_NEGATIVE_MATRIX_RELATIVE,
        "repository_relative",
        35603,
        "f8481147babbad02215c3c3f767fe22ba6a511b8a076482a9635fec5d5cf8e82",
        False,
        "PUBLISHED_TASK_DOMAIN_NEGATIVE_LANE_PRECEDENT",
        "PARSED_CSV_LANE_AND_UNAVAILABLE_LABEL_VOCABULARY",
    ),
)
CENSUS_BINDING: _Binding = (
    CENSUS_MATRIX_RELATIVE,
    "repository_relative",
    545586,
    "a393fc8e2419d354f73863b389a64a12874ec500282b61986bfefe51f10b12ce",
    False,
    "CURRENT_WITH_LCY_GLOBAL_CENSUS_PREFORMAL_READ_ONLY",
    "PARSED_CSV_PREFORMAL_STATE_READ_ONLY",
)
ACTIVE_BINDINGS = (
    *FORMAL_BINDINGS,
    *SUPPORTING_BINDINGS,
    POLICY_BINDING,
    *SEMANTIC_OWNER_BINDINGS,
    CENSUS_BINDING,
)


class ZeroD8IngestionSafetyError(ValueError):
    """Raised when 0D8 ingestion safety or semantics cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise ZeroD8IngestionSafetyError("COVAPIE_0D8_INGESTION_V1_ERROR:" + reason)


def _expect(actual: object, expected: object, reason: str) -> None:
    if actual != expected or type(actual) is not type(expected):
        _fail(reason)


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
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _json_cell(value: object) -> str:
    return _canonical_json(value).decode("utf-8")


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(header), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if set(row) != set(header):
            _fail("INTERNAL_MATRIX_ROW_SHAPE_INVALID")
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _strict_json_loads(payload: bytes, label: str) -> dict[str, Any]:
    if type(payload) is not bytes or payload.startswith(b"\xef\xbb\xbf"):
        _fail("JSON_BYTES_OR_BOM_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ZeroD8IngestionSafetyError(
            "COVAPIE_0D8_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label
        ) from error
    if "\x00" in text:
        _fail("JSON_NUL_INVALID:" + label)

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                _fail("JSON_DUPLICATE_KEY:" + label + ":" + key)
            result[key] = value
        return result

    def reject_constant(value: str) -> NoReturn:
        _fail("JSON_NONFINITE:" + label + ":" + value)

    try:
        value = json.loads(
            text,
            object_pairs_hook=pairs_hook,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as error:
        raise ZeroD8IngestionSafetyError(
            "COVAPIE_0D8_INGESTION_V1_ERROR:JSON_PARSE:" + label
        ) from error
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _parse_csv(payload: bytes, label: str) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ZeroD8IngestionSafetyError(
            "COVAPIE_0D8_INGESTION_V1_ERROR:CSV_UTF8_INVALID:" + label
        ) from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        _fail("CSV_HEADER_INVALID:" + label)
    rows = list(reader)
    if any(None in row for row in rows):
        _fail("CSV_ROW_WIDTH_INVALID:" + label)
    return rows


def _binding_record(binding: _Binding) -> dict[str, object]:
    relative, namespace, byte_count, digest, executable, role, method = binding
    return {
        "path": relative.as_posix(),
        "namespace": namespace,
        "byte_count": byte_count,
        "SHA256": digest,
        "semantic_source_identity": namespace + ":" + relative.as_posix() + "@" + digest,
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "EXECUTABLE" if executable else "NON_EXECUTABLE",
        "source_role": role,
        "validation_method": method,
    }


def _binding_records(bindings: Sequence[_Binding]) -> list[dict[str, object]]:
    return [_binding_record(binding) for binding in bindings]


def _normalize_overrides(value: Mapping[Path, Path] | None) -> dict[Path, Path]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        _fail("SOURCE_OVERRIDES_NOT_MAPPING")
    result = {Path(key): Path(path) for key, path in value.items()}
    if not set(result).issubset({binding[0] for binding in ACTIVE_BINDINGS}):
        _fail("SOURCE_OVERRIDE_UNKNOWN_BINDING")
    return result


def _resolve_binding_path(
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
            path=_resolve_binding_path(repo_root, binding, overrides),
            expected_byte_count=byte_count,
            expected_sha256=digest,
            label=role + ":" + relative.as_posix(),
            expected_executable=executable,
        )
    except SourceBindingPolicyV2Error as error:
        raise ZeroD8IngestionSafetyError(
            "COVAPIE_0D8_INGESTION_V1_ERROR:SOURCE_BINDING_FAILED:"
            + relative.as_posix()
        ) from error


def _verify_bindings(
    repo_root: Path, bindings: Sequence[_Binding], overrides: Mapping[Path, Path]
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
        raise ZeroD8IngestionSafetyError(
            "COVAPIE_0D8_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
        ) from error
    values: dict[str, object] = {}
    wanted = set(names)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    values[target.id] = ast.literal_eval(value)
                except (TypeError, ValueError) as error:
                    raise ZeroD8IngestionSafetyError(
                        "COVAPIE_0D8_INGESTION_V1_ERROR:"
                        "SEMANTIC_OWNER_LITERAL_INVALID:" + target.id
                    ) from error
    if set(values) != wanted:
        _fail("SEMANTIC_OWNER_LITERAL_MISSING:" + label)
    return values


def _semantic_digest(formal: Mapping[str, Any]) -> str:
    clone = copy.deepcopy(dict(formal))
    digest = clone.pop("formal_decision_semantic_canonical_sha256", None)
    if type(digest) is not str:
        _fail("FORMAL_SEMANTIC_DIGEST_FIELD_INVALID")
    return _sha256(_canonical_json(clone))


def _expected_formal_events() -> list[dict[str, object]]:
    return [
        {
            "D1_task_relevance": "NOT_RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_candidate": "SELECT_CANDIDATE_0",
            "D5_training_use": "NOT_APPLICABLE",
            "D6_context_reference": "UNIT_LEVEL_EXACT_AUTHORIZED_D6",
            "POST_geometry_training_authority": False,
            "canonical_event_id": event_id,
            "distance_only_inference": False,
            "event_index_0based": index,
            "event_specific_exception": False,
            "explicit_covalent_evidence": True,
            "formal_training_admitted": False,
            "ligand_reactive_atom": "C8",
            "protein_reactive_atom": "SG",
            "recomputed_POST_distance_angstrom": float(distance),
            "sample_level_formal_authority": True,
            "scaleup_rank": rank,
        }
        for index, (event_id, rank, _protein, _ligand, _connection, distance, _reported)
        in enumerate(EXPECTED_EVENTS)
    ]


def _formal_task_contract() -> dict[str, object]:
    return {
        "B3_present": True,
        "additional_mask_created": False,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "global_mask_contract_modified": False,
        "global_task_count": 5,
        "not_applicable_tasks": [
            {
                "reason": "not_applicable_empty_linker_redundant_with_A",
                "semantic_long_name": "linker_plus_warhead",
                "task_id": 1,
            },
            {
                "reason": "not_applicable_empty_non_C_fixed_context",
                "semantic_long_name": "scaffold_plus_warhead",
                "task_id": 2,
            },
        ],
        "sample_applicable_semantic_names": [
            "warhead_only",
            "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
        ],
        "sample_applicable_task_ids": [0, 3, 4],
        "sample_role_profile_task_applicability_determined": True,
        "sixth_task": False,
        "tasks": [
            {
                "display_alias": alias,
                "semantic_long_name": semantic,
                "task_id": task_id,
            }
            for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
        ],
    }


def _formal_pre_boundary() -> dict[str, object]:
    return {
        "C8_equals_O_PRE_topology_reconstructed": False,
        "OH_deleted_to_fabricate_aldehyde_PRE": False,
        "POST_to_PRE_copy": False,
        "PRE_coordinates": None,
        "PRE_coordinates_authority": False,
        "PRE_geometry_authority": False,
        "PRE_reconstruction": False,
        "PRE_topology": None,
        "PRE_topology_authority": False,
        "PRE_zero_fill": False,
        "hydrogen_atoms_added_or_removed": False,
        "leaving_group_inferred": False,
        "per_event": [
            {
                "PRE_mapping_count": 0,
                "PRE_mapping_status": PRE_MAPPING_STATUS,
                "PRE_source_graph_count": 0,
                "PRE_source_graph_present": False,
                "PRE_status": PRE_STATUS,
                "canonical_event_id": event_id,
                "supporting_PRE_source_graph_count": 0,
            }
            for event_id in EXPECTED_EVENT_IDS
        ],
        "pre_reaction_bond_edit_inferred": False,
        "reagent_inferred": False,
    }


def _validate_formal_document(formal: Mapping[str, Any]) -> None:
    """Independently validate frozen 0D8 lifecycle, D1-D6, and authority."""

    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(formal.get("record_role"), FORMAL_RECORD_ROLE, "FORMAL_RECORD_ROLE_DRIFT")
    _expect(formal.get("stage"), "FORMAL_HUMAN_DECISION", "FORMAL_STAGE_DRIFT")
    for key, expected in (
        ("approved", True),
        ("unsigned", False),
        ("decision_finalized", True),
        ("human_review_completed", True),
        ("human_decision_created", True),
        ("formal_decision_created", True),
        ("formal_authority_created", True),
        ("formal_authority_is_human", True),
        ("machine_approval_claimed", False),
        ("reviewer_id", "fmx"),
        ("attestor_id", "fmx"),
        ("authorization_origin", "EXTERNAL_HUMAN_CHAT_AUTHORIZATION"),
    ):
        _expect(formal.get(key), expected, "FORMAL_FINALIZATION_DRIFT:" + key)

    d6_bytes = EXPECTED_D6.encode("utf-8")
    if len(d6_bytes) != EXPECTED_D6_BYTE_COUNT or _sha256(d6_bytes) != EXPECTED_D6_SHA256:
        _fail("INTERNAL_D6_IDENTITY_INVALID")
    _expect(
        formal.get("inherited_scientific_decision"),
        {
            "D1_task_relevance": "NOT_RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_candidate": "SELECT_CANDIDATE_0",
            "D5_training_use": "NOT_APPLICABLE",
            "D6_draft_origin": "ASSISTANT_DRAFT_ACCEPTED_BY_HUMAN",
            "D6_exact": True,
            "D6_human_authored": False,
            "D6_human_authorized": True,
            "D6_human_reviewed_and_accepted": True,
            "D6_scientific_context": EXPECTED_D6,
            "D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT,
            "D6_utf8_sha256": EXPECTED_D6_SHA256,
            "assistant_draft_does_not_create_authority": True,
            "inheritance_byte_and_semantic_exact": True,
            "scientific_decision_semantic_canonical_sha256": (
                "f6a454cc781ca54947810d7d16e266e04bb5e5849103ed3633b8f15585d2ee74"
            ),
        },
        "FORMAL_D1_D6_DRIFT",
    )
    _expect(
        formal.get("D1_formal_task_relevance"),
        {
            "D1": "NOT_RELEVANT",
            "all_0D8_task_negative": False,
            "all_aldehydes_task_negative": False,
            "all_enzyme_substrates_task_negative": False,
            "all_thiohemiacetals_task_negative": False,
            "sample_task_relevance_authority": True,
            "scope": "CURRENT_0D8_4V37_EXACT4_REVIEW_UNIT_ONLY",
        },
        "FORMAL_D1_DRIFT",
    )
    _expect(
        formal.get("D2_formal_chemistry"),
        {
            "D2": "POSITIVE",
            "TASK_NOT_RELEVANT_DOES_NOT_COLLAPSE_D2_POSITIVE": True,
            "distance_only_count": 0,
            "explicit_event_count": 4,
            "reaction_family_authority": False,
            "reusable_chemistry_authority": False,
            "sample_positive_chemistry_authority": True,
            "warhead_rule_authority": False,
            "warhead_type_authority": False,
        },
        "FORMAL_D2_DRIFT",
    )
    _expect(
        formal.get("D3_formal_reactive_pair"),
        {
            "D3": "CONFIRM_OBSERVED_PAIR",
            "Q_authority_transfer": False,
            "all_0D8_uses_C8_authority": False,
            "all_3_aminopropionaldehyde_uses_C8_authority": False,
            "all_BADH_thiohemiacetal_pairs_use_C8_authority": False,
            "cross_structure_regiochemistry_generalization": False,
            "ligand_atom": "C8",
            "protein_atom": "SG",
            "reusable_pair_rule_created": False,
            "sample_reactive_pair_authority": True,
            "scope": PAIR_AUTHORITY_SCOPE,
        },
        "FORMAL_D3_DRIFT",
    )
    _expect(
        formal.get("D4_formal_role_partition"),
        {
            "D4": "SELECT_CANDIDATE_0",
            "L_atom_ids": [],
            "L_connected_or_empty": True,
            "S_atom_ids": list(SCAFFOLD_ATOMS),
            "S_connected": True,
            "W_L_S_counts": [2, 0, 3],
            "W_atom_ids": list(WARHEAD_ATOMS),
            "W_connected": True,
            "boundary": {
                "atom_id_1": "C7",
                "atom_id_2": "C8",
                "bond_order": "SING",
                "role_1": "S",
                "role_2": "W",
            },
            "candidate_index_is_rank": False,
            "candidate_index_is_recommendation": False,
            "cross_role_boundary_count": 1,
            "extra_atom_ids": [],
            "heavy_atom_count": 5,
            "human_selected": True,
            "machine_ranked": False,
            "machine_recommended": False,
            "machine_selected": False,
            "missing_atom_ids": [],
            "partition_exhaustive": True,
            "partition_pairwise_disjoint": True,
            "reactive_C8_in_W": True,
            "reusable_role_authority": False,
            "role_authority_scope": ROLE_AUTHORITY_SCOPE,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "sample_role_partition_authority": True,
            "selected_candidate_index_0based": 0,
        },
        "FORMAL_D4_DRIFT",
    )
    _expect(
        formal.get("D5_formal_training_use"),
        {
            "D5": "NOT_APPLICABLE",
            "NOT_APPLICABLE_is_EXCLUDE_FROM_TRAINING_ONLY": False,
            "READY_FOR_TRAINING": False,
            "current_runtime_model_usable": False,
            "formal_split_authority": False,
            "formal_training_admitted": False,
            "future_training_admission_candidate": False,
            "human_training_excluded": False,
            "human_training_use_disposition": "NOT_APPLICABLE",
            "human_training_use_disposition_authority": True,
            "parameter_update_authorization": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
            "training_use_include": False,
        },
        "FORMAL_D5_DRIFT",
    )
    _expect(formal.get("event_level_formal_decision_count"), 4, "FORMAL_EVENT_COUNT_DRIFT")
    _expect(
        formal.get("event_level_formal_decisions"),
        _expected_formal_events(),
        "FORMAL_EVENT_DECISIONS_DRIFT",
    )
    _expect(
        formal.get("target_selection"),
        {
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "exact_event_count": 4,
            "ligand_component_id": "0D8",
            "ligand_reactive_atom": "C8",
            "ligand_wide_selection": False,
            "pdb_id": "4V37",
            "protein_reactive_atom": "SG",
            "raw_priority_rank": 25,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scaleup_ranks": list(EXPECTED_RANKS),
            "selection_scope": "CURRENT_0D8_4V37_EXACT4_REVIEW_UNIT_ONLY",
        },
        "FORMAL_EXACT4_TARGET_DRIFT",
    )
    _expect(
        formal.get("canonical_Exact5_and_sample_applicability"),
        _formal_task_contract(),
        "FORMAL_EXACT5_OR_APPLICABILITY_DRIFT",
    )

    authority = formal.get("formal_authority_boundary")
    if type(authority) is not dict:
        _fail("FORMAL_AUTHORITY_BOUNDARY_INVALID")
    true_set = [
        "formal_authority_created",
        "formal_authority_is_human",
        "sample_task_relevance_authority",
        "sample_positive_chemistry_authority",
        "sample_reactive_pair_authority",
        "sample_role_partition_authority",
        "human_training_use_disposition_authority",
    ]
    _expect(authority.get("formal_core_authority_true_set"), true_set, "FORMAL_TRUE_SET_DRIFT")
    for key in true_set:
        _expect(authority.get(key), True, "FORMAL_REQUIRED_AUTHORITY_FALSE:" + key)
    false_authorities = (
        "POST_geometry_training_authority",
        "PRE_geometry_authority",
        "PRE_topology_authority",
        "formal_split_authority",
        "machine_authority",
        "parameter_update_authorization",
        "reaction_family_authority",
        "reusable_chemistry_authority",
        "reusable_pair_authority",
        "reusable_role_authority",
        "runtime_usability_authority",
        "tensor_target_created",
        "training_admission_created",
        "warhead_rule_authority",
        "warhead_type_authority",
    )
    for key in false_authorities:
        _expect(authority.get(key), False, "FORMAL_FORBIDDEN_AUTHORITY_TRUE:" + key)
    if len(true_set) != 7 or sum(authority.get(key) is True for key in true_set) != 7:
        _fail("FORMAL_CORE_AUTHORITY_NOT_EXACT7")

    _expect(formal.get("PRE_boundary"), _formal_pre_boundary(), "FORMAL_PRE_DRIFT")
    _expect(
        formal.get("POST_boundary"),
        {
            "D3_formalizes_the_pair_only": True,
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
            "POST_source_evidence_available": True,
            "POST_source_evidence_count": 4,
            "distance_only_inference": False,
            "explicit_covalent_evidence": True,
            "observed_distances_angstrom": [float(row[5]) for row in EXPECTED_EVENTS],
        },
        "FORMAL_POST_DRIFT",
    )
    _expect(
        formal.get("same_structure_Q_boundary"),
        {
            "Q_PRE_source_claimed": False,
            "Q_authority_transfer": False,
            "Q_covalent_ligand_claimed": False,
            "Q_current_target": False,
            "Q_free_ligand_claimed": False,
            "Q_noncovalent_ligand_claimed": False,
            "Q_target_widened": False,
            "formal_Exact4_instance_labels": ["F", "K", "P", "V"],
            "structure_instance_labels": ["F", "K", "P", "Q", "V"],
        },
        "FORMAL_Q_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("formal_validator_lifecycle"),
        {
            "future_ingestion_must_bind_formal_JSON_and_validator_bytes_SHA256": True,
            "future_ingestion_must_independently_validate_formal_semantics": True,
            "future_ingestion_must_not_execute_this_validator_after_HEAD_advances": True,
            "validator_baseline_commit": BASELINE_COMMIT,
            "validator_postbaseline_runtime_dependency_allowed": False,
        },
        "FORMAL_VALIDATOR_LIFECYCLE_DRIFT",
    )
    operations = formal.get("operation_boundary")
    if type(operations) is not dict or any(value is not False for value in operations.values()):
        _fail("FORMAL_OPERATION_ALREADY_OCCURRED")
    warning = formal.get("training_prerequisite_warning")
    _expect(
        warning,
        {
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
            "READY_FOR_TRAINING": False,
            "Step12D": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
            "UNKNOWN_ATOM_FEATURE_POLICY": "UNRESOLVED",
            "feature_semantics_known": False,
        },
        "FORMAL_TRAINING_WARNING_DRIFT",
    )
    generic = formal.get("future_generic_Exact11_projection")
    if type(generic) is not dict:
        _fail("FORMAL_GENERIC_PROJECTION_INVALID")
    for key, expected in (
        ("human_review_completed", True),
        ("legacy_completed_review_status", "COMPLETED_HUMAN_NEGATIVE"),
        ("task_relevance_disposition", "NOT_RELEVANT"),
        ("chemistry_disposition", "POSITIVE"),
        ("training_disposition", "NOT_APPLICABLE"),
        ("human_training_excluded", False),
        ("source_decision_schema", FORMAL_DECISION_SCHEMA),
        ("synthetic_accepted_fact_count", 4),
        ("generic_fact_materialized_now", False),
        ("reconciliation_performed_now", False),
        ("rich_fields_leaked", False),
        ("scientific_synthetic_probe_path_used_as_formal_or_real_provenance", False),
    ):
        _expect(generic.get(key), expected, "FORMAL_GENERIC_PROJECTION_DRIFT:" + key)
    _expect(
        generic.get("generic_fact_field_contract"),
        list(GENERIC_FACT_FIELDS),
        "FORMAL_GENERIC_EXACT11_FIELD_CONTRACT_DRIFT",
    )
    _expect(
        generic.get("future_actual_binding"),
        {
            "path_namespace": "repository_parent_relative",
            "real_bytes_and_SHA256_required_after_materialization": True,
            "relative_path": FORMAL_DECISION_RELATIVE.as_posix(),
        },
        "FORMAL_GENERIC_ACTUAL_BINDING_DRIFT",
    )

    census = formal.get("current_with_LCY_census_preformal_state")
    if type(census) is not dict:
        _fail("FORMAL_CURRENT_CENSUS_BOUNDARY_INVALID")
    required_census = {
        "bound_census_is_preformal": True,
        "canonical_mask_structural_labels_available": False,
        "census_modified_by_this_step": False,
        "chemistry_disposition": "UNRESOLVED",
        "column_count": 47,
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "current_orthogonal_population_claimed_12": False,
        "current_orthogonal_population_count": 8,
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "current_runtime_model_usable": False,
        "formal_training_admitted": False,
        "human_review_completed": False,
        "reactive_pair_sample_authoritative": False,
        "role_partition_sample_authoritative": False,
        "role_profile": "NOT_ESTABLISHED",
        "row_count": 1000,
        "target_event_count": 4,
        "target_event_ids": list(EXPECTED_EVENT_IDS),
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
    }
    for key, expected in required_census.items():
        _expect(census.get(key), expected, "FORMAL_CURRENT_CENSUS_DRIFT:" + key)
    _expect(
        census.get("current_orthogonal_population_breakdown"),
        {"GVE": 4, "LCY": 4},
        "FORMAL_CURRENT_ORTHOGONAL_BREAKDOWN_DRIFT",
    )

    readiness = formal.get("readiness")
    if type(readiness) is not dict:
        _fail("FORMAL_READINESS_INVALID")
    required_readiness = {
        "D1_NOT_RELEVANT": True,
        "D2_POSITIVE": True,
        "D3_SAMPLE_SPECIFIC_SG_C8_CONFIRMED": True,
        "D4_DIRECT_CANDIDATE_0_SELECTED": True,
        "D5_NOT_APPLICABLE": True,
        "0D8_SAMPLE_ROLE_PARTITION_AUTHORITY": True,
        "0D8_SAMPLE_APPLICABLE_TASK_IDS_0_3_4": True,
        "0D8_AUTHORITATIVE_TASK_LABELS_CREATED": False,
        "0D8_EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "READY_FOR_TRAINING": False,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "TRAINING_STARTED": False,
    }
    for key, expected in required_readiness.items():
        _expect(readiness.get(key), expected, "FORMAL_READINESS_DRIFT:" + key)
    _expect(
        formal.get("formal_decision_semantic_canonical_sha256"),
        FORMAL_SEMANTIC_CANONICAL_SHA256,
        "FORMAL_SEMANTIC_DIGEST_LITERAL_DRIFT",
    )
    if _semantic_digest(formal) != FORMAL_SEMANTIC_CANONICAL_SHA256:
        _fail("FORMAL_SEMANTIC_DIGEST_RECOMPUTE_FAILED")


EVENT_EVIDENCE_HEADER = tuple(
    "package_role,event_index_0based,canonical_event_id,scaleup_rank,raw_priority_rank,"
    "review_unit_id,pdb_id,model_number,protein_chain_or_asym,cys_residue_id,"
    "protein_reactive_atom,protein_altloc,protein_occupancy,ligand_component_id,"
    "ligand_chain_or_asym,ligand_reactive_atom,ligand_reactive_element,ligand_altloc,"
    "ligand_occupancy,selected_connection_id,selected_connection_type,"
    "explicit_covalent_evidence,distance_only_inference,protein_atom_coordinates_json,"
    "ligand_atom_coordinates_json,reported_POST_distance_angstrom,"
    "recomputed_POST_distance_angstrom,POST_distance_absolute_difference_angstrom,"
    "POST_distance_recomputed,raw_structure_available,exact_cys_sg_event_recovered,"
    "full_coordinate_POST_evidence_available,CCD_graph_complete,feature_compatible,"
    "structural_processing_success,post_geometry_source_evidence_available,"
    "representation_gap,feature_incompatible,priority_review_in_scope,"
    "reactive_pair_raw_structural_evidence,reactive_pair_sample_authoritative,"
    "role_partition_sample_authoritative,canonical_mask_structural_labels_available,"
    "formal_training_admitted,human_confirmed_pair,supporting_adduct_graph_count,"
    "candidate_PRE_free_source_graph_count,compatible_atom_mapping_count,"
    "PRE_source_mapping_status,final_PRE_reaction_status,PRE_topology_created,"
    "PRE_coordinates_created,POST_to_PRE_copy,PRE_zero_fill,current_human_review_status,"
    "chemistry_disposition,task_relevance_disposition,training_use_disposition,"
    "source_structure_binding_json,CCD_source_binding_json,processing_source_binding_json"
    .split(",")
)


def _validate_event_evidence(payload: bytes) -> dict[str, object]:
    rows = _parse_csv(payload, "0D8_EVENT_EVIDENCE")
    if not rows or tuple(rows[0]) != EVENT_EVIDENCE_HEADER or len(rows) != 4:
        _fail("EVENT_EVIDENCE_SCHEMA_OR_COUNT_DRIFT")
    for index, (row, expected) in enumerate(zip(rows, EXPECTED_EVENTS, strict=True)):
        event_id, rank, protein_asym, ligand_asym, connection, distance, reported = expected
        required = {
            "package_role": "UNSIGNED_NON_AUTHORITATIVE_MACHINE_REVIEW_AID_PREPARATION",
            "event_index_0based": str(index),
            "canonical_event_id": event_id,
            "scaleup_rank": str(rank),
            "raw_priority_rank": "25",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "pdb_id": "4V37",
            "model_number": "1",
            "protein_chain_or_asym": protein_asym,
            "cys_residue_id": "CYS:450-",
            "protein_reactive_atom": "SG",
            "ligand_component_id": "0D8",
            "ligand_chain_or_asym": ligand_asym,
            "ligand_reactive_atom": "C8",
            "selected_connection_id": connection,
            "explicit_covalent_evidence": "true",
            "distance_only_inference": "false",
            "reported_POST_distance_angstrom": reported,
            "recomputed_POST_distance_angstrom": distance,
            "POST_distance_recomputed": "true",
            "post_geometry_source_evidence_available": "true",
            "reactive_pair_sample_authoritative": "false",
            "role_partition_sample_authoritative": "false",
            "canonical_mask_structural_labels_available": "false",
            "formal_training_admitted": "false",
            "human_confirmed_pair": "false",
            "supporting_adduct_graph_count": "0",
            "candidate_PRE_free_source_graph_count": "0",
            "compatible_atom_mapping_count": "0",
            "PRE_source_mapping_status": PRE_MAPPING_STATUS,
            "final_PRE_reaction_status": PRE_STATUS,
            "PRE_topology_created": "false",
            "PRE_coordinates_created": "false",
            "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false",
            "current_human_review_status": "CURRENTLY_UNREVIEWED",
            "chemistry_disposition": "UNRESOLVED",
            "task_relevance_disposition": "UNRESOLVED",
            "training_use_disposition": "UNRESOLVED",
        }
        if any(row.get(key) != value for key, value in required.items()):
            _fail("EVENT_EVIDENCE_SEMANTICS_DRIFT:" + event_id)
    return {
        "event_count": 4,
        "event_ids": list(EXPECTED_EVENT_IDS),
        "POST_distances_angstrom": [float(row[5]) for row in EXPECTED_EVENTS],
        "PRE_source_graph_count": 0,
        "PRE_mapping_count": 0,
        "PRE_mapping_status": PRE_MAPPING_STATUS,
        "PRE_status": PRE_STATUS,
    }


def _validate_graph_candidates(payload: bytes) -> dict[str, object]:
    graph = _strict_json_loads(payload, "0D8_GRAPH_AND_ROLE_CANDIDATES")
    for key, expected in (
        ("schema_version", "covapie_0d8_graph_and_role_candidates_v1"),
        ("record_role", "MACHINE_GRAPH_EVIDENCE_AND_REVIEW_POLICY_SCOPED_UNSELECTED_CANDIDATES_ONLY"),
        ("package_role", "UNSIGNED_NON_AUTHORITATIVE_MACHINE_REVIEW_AID_PREPARATION"),
        ("review_unit_id", EXPECTED_REVIEW_UNIT_ID),
        ("ligand_component_id", "0D8"),
        ("review_policy_candidate_count", 1),
        ("review_policy_candidate_indices", [0]),
        ("review_policy_candidate_inventory_complete", True),
        ("human_candidate_selected", False),
        ("machine_candidate_ranked", False),
        ("machine_candidate_recommended", False),
        ("machine_candidate_selected", False),
    ):
        _expect(graph.get(key), expected, "GRAPH_CANDIDATE_DRIFT:" + key)
    candidates = graph.get("review_policy_candidates")
    if type(candidates) is not list or len(candidates) != 1 or type(candidates[0]) is not dict:
        _fail("GRAPH_CANDIDATE_EXACT1_INVALID")
    candidate = candidates[0]
    required_candidate = {
        "candidate_index_0based": 0,
        "candidate_index_is_quality_rank": False,
        "candidate_index_is_recommendation": False,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "W_atom_ids": list(WARHEAD_ATOMS),
        "L_atom_ids": [],
        "S_atom_ids": list(SCAFFOLD_ATOMS),
        "W_count": 2,
        "L_count": 0,
        "S_count": 3,
        "heavy_atom_count": 5,
        "W_connected": True,
        "L_connected_or_empty": True,
        "S_connected": True,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "reactive_atom": "C8",
        "reactive_atom_in_W": True,
        "human_selected": False,
        "machine_recommended": False,
        "machine_selected": False,
        "canonical_Exact5_structurally_applicable_task_ids": [0, 3, 4],
        "cross_role_boundary_bonds": [
            {**BOUNDARY_BONDS[0], "aromatic_flag": "N"}
        ],
    }
    for key, expected in required_candidate.items():
        _expect(candidate.get(key), expected, "GRAPH_SELECTED_CANDIDATE_DRIFT:" + key)
    expected_applicability = [
        {
            "display_alias": alias,
            "semantic_long_name": semantic,
            "structurally_applicable": task_id in DIRECT_APPLICABLE_TASK_IDS,
            "task_id": task_id,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]
    _expect(
        candidate.get("canonical_Exact5_task_applicability"),
        expected_applicability,
        "GRAPH_TASK_APPLICABILITY_DRIFT",
    )
    published_validation = candidate.get("published_role_profile_validation")
    _expect(
        published_validation,
        {
            "reasons": [],
            "source_role": "direct_and_strict_profile_runtime_semantics_owner",
            "valid": True,
            "validator": "validate_role_profile_v1",
        },
        "GRAPH_PRIOR_RUNTIME_VALIDATION_DRIFT",
    )
    heavy = graph.get("canonical_heavy_atom_graph")
    if type(heavy) is not dict:
        _fail("GRAPH_HEAVY_GRAPH_INVALID")
    _expect(heavy.get("heavy_atom_count"), 5, "GRAPH_HEAVY_ATOM_COUNT_DRIFT")
    _expect(heavy.get("heavy_heavy_bond_count"), 4, "GRAPH_HEAVY_BOND_COUNT_DRIFT")
    atoms = heavy.get("atom_inventory")
    bonds = heavy.get("bond_inventory")
    if type(atoms) is not list or type(bonds) is not list:
        _fail("GRAPH_HEAVY_INVENTORY_INVALID")
    _expect(
        tuple(atom.get("atom_id") for atom in atoms if type(atom) is dict),
        HEAVY_ATOMS,
        "GRAPH_HEAVY_ATOM_IDS_DRIFT",
    )
    _expect(
        tuple(
            (bond.get("atom_id_1"), bond.get("atom_id_2"), bond.get("bond_order"))
            for bond in bonds
            if type(bond) is dict
        ),
        HEAVY_BONDS,
        "GRAPH_HEAVY_BONDS_DRIFT",
    )
    pre = graph.get("PRE_evidence_by_event")
    if type(pre) is not list or len(pre) != 4:
        _fail("GRAPH_PRE_EVIDENCE_INVALID")
    for event_id, event in zip(EXPECTED_EVENT_IDS, pre, strict=True):
        _expect(
            event,
            {
                "PRE_source_mapping_status": PRE_MAPPING_STATUS,
                "candidate_PRE_free_source_graph_count": 0,
                "canonical_event_id": event_id,
                "compatible_atom_mapping_count": 0,
                "final_PRE_reaction_status": PRE_STATUS,
                "supporting_adduct_graph_count": 0,
            },
            "GRAPH_PRE_EVENT_DRIFT:" + event_id,
        )
    return {
        "candidate_index_0based": 0,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "warhead_atoms": list(WARHEAD_ATOMS),
        "linker_atoms": [],
        "scaffold_atoms": list(SCAFFOLD_ATOMS),
        "W_L_S_counts": [2, 0, 3],
        "boundary_bonds": copy.deepcopy(list(BOUNDARY_BONDS)),
        "heavy_atoms": list(HEAVY_ATOMS),
        "heavy_bonds": [list(bond) for bond in HEAVY_BONDS],
        "applicable_task_ids": [0, 3, 4],
    }


def _validate_canonical_owner(payload: bytes) -> dict[str, object]:
    values = _literal_assignments(
        payload,
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
        CANONICAL_TASK_OWNER_RELATIVE.as_posix(),
    )
    _expect(values["EXACT3_ROLES"], ("scaffold", "linker", "warhead"), "EXACT3_ROLE_OWNER_DRIFT")
    _expect(values["CANONICAL_TASKS"], CANONICAL_TASKS, "CANONICAL_EXACT5_OWNER_DRIFT")
    return {"global_canonical_task_count": 5, "B3_present": True, "sixth_task": False}


def _validate_task_domain_negative_precedent(payload: bytes) -> dict[str, object]:
    rows = _parse_csv(payload, "TASK_DOMAIN_NEGATIVE_PRECEDENT")
    negative = [row for row in rows if row.get("completed_lane") == EXPECTED_COMPLETED_LANE]
    if not negative:
        _fail("PUBLISHED_TASK_DOMAIN_NEGATIVE_LANE_MISSING")
    for row in negative:
        required = {
            "positive_generative_supervision_eligible": "false",
            "reactive_atom_pair_label_available": "false",
            "role_partition_label_available": "false",
            "event_training_use_label_available": "false",
            "label_availability_status": "NOT_APPLICABLE_TASK_DOMAIN_NEGATIVE",
        }
        if any(row.get(key) != value for key, value in required.items()):
            _fail("PUBLISHED_TASK_DOMAIN_NEGATIVE_LANE_DRIFT")
    return {
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "unavailable_label_token": "NOT_APPLICABLE_TASK_DOMAIN_NEGATIVE",
        "precedent_event_count": len(negative),
    }


def _validate_published_direct_runtime(
    repo_root: Path, graph: Mapping[str, object]
) -> dict[str, object]:
    module = importlib.import_module(
        "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"
    )
    if Path(module.__file__).resolve() != (repo_root / DIRECT_RUNTIME_OWNER_RELATIVE).resolve():
        _fail("DIRECT_RUNTIME_IMPORT_PATH_INVALID")
    result = module.validate_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE,
        retained_heavy_atoms=tuple(graph["heavy_atoms"]),
        scaffold_atoms=SCAFFOLD_ATOMS,
        linker_atoms=LINKER_ATOMS,
        warhead_atoms=WARHEAD_ATOMS,
        reactive_atom_id="C8",
        direct_scaffold_warhead_boundaries=(("C7", "C8", "SING"),),
        explicit_graph_bonds=tuple(tuple(bond) for bond in graph["heavy_bonds"]),
    )
    boundary = result.direct_scaffold_warhead_boundary
    if (
        result.role_profile != EXPECTED_ROLE_PROFILE
        or result.valid is not True
        or tuple(result.reasons) != ()
        or result.warhead_count != 2
        or result.linker_count != 0
        or result.scaffold_count != 3
        or result.scaffold_linker_boundary_applicable is not False
        or result.linker_warhead_boundary_applicable is not False
        or result.direct_scaffold_warhead_boundary_applicable is not True
        or boundary is None
        or boundary.boundary_valid is not True
        or boundary.scaffold_atom_id != "C7"
        or boundary.warhead_atom_id != "C8"
        or boundary.bond_order != "SING"
    ):
        _fail("PUBLISHED_DIRECT_RUNTIME_VALIDATION_FAILED")
    return {
        "validator": "validate_role_profile_v1",
        "runtime_import_path_exact": True,
        "call_count_for_selected_partition": 1,
        "valid": True,
        "reasons": [],
        "profile": EXPECTED_ROLE_PROFILE,
        "warhead_count": 2,
        "linker_count": 0,
        "scaffold_count": 3,
        "sample_applicable_task_ids": [0, 3, 4],
        "direct_scaffold_warhead_boundary": {
            "scaffold_atom_id": "C7",
            "warhead_atom_id": "C8",
            "bond_order": "SING",
            "boundary_valid": True,
        },
    }


def _validate_generic_owner_compatibility(repo_root: Path) -> dict[str, object]:
    module = importlib.import_module(
        "covalent_ext.covapie_completed_human_decision_reconciliation_v1"
    )
    if Path(module.__file__).resolve() != (repo_root / GENERIC_OWNER_RELATIVE).resolve():
        _fail("GENERIC_OWNER_IMPORT_PATH_INVALID")
    binding = module.SourceBinding(
        source_path=FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=FORMAL_BINDINGS[0][2],
        sha256=FORMAL_BINDINGS[0][3],
        schema_version=FORMAL_DECISION_SCHEMA,
        review_unit_id=EXPECTED_REVIEW_UNIT_ID,
    )
    module._validate_source_binding(binding)
    facts: list[dict[str, object]] = []
    for event_id in EXPECTED_EVENT_IDS:
        fact = module.NormalizedCompletedDecisionFact(
            canonical_event_id=event_id,
            review_unit_id=EXPECTED_REVIEW_UNIT_ID,
            **GENERIC_PROJECTION,
            source_decision_schema=FORMAL_DECISION_SCHEMA,
            source_decision_sha256=FORMAL_BINDINGS[0][3],
            source_binding_path=FORMAL_DECISION_RELATIVE.as_posix(),
        )
        if tuple(field.name for field in fields(fact)) != GENERIC_FACT_FIELDS:
            _fail("GENERIC_FACT_NOT_EXACT11")
        module._validate_fact(fact, binding)
        projected = {field.name: getattr(fact, field.name) for field in fields(fact)}
        if set(projected) != set(GENERIC_FACT_FIELDS):
            _fail("GENERIC_RICH_FIELD_FIREWALL_FAILED")
        facts.append(projected)
    if len(facts) != 4:
        _fail("GENERIC_EXACT11_ACCEPTED_COUNT_INVALID")
    return {
        "generic_exact11_compatibility_pass": True,
        "generic_fact_field_count": 11,
        "generic_fact_fields": list(GENERIC_FACT_FIELDS),
        "accepted_fact_count": 4,
        "actual_source_binding": {
            "source_path": binding.source_path,
            "path_namespace": binding.path_namespace,
            "byte_count": binding.byte_count,
            "sha256": binding.sha256,
            "schema_version": binding.schema_version,
            "review_unit_id": binding.review_unit_id,
        },
        "facts": facts,
        "rich_fields_leaked": False,
        "scientific_synthetic_probe_used": False,
        "reconciliation_performed": False,
    }


def _validate_current_census(payload: bytes) -> dict[str, object]:
    rows = _parse_csv(payload, "CURRENT_WITH_LCY_CENSUS")
    if len(rows) != 1000 or not rows or len(rows[0]) != 47:
        _fail("CURRENT_CENSUS_SHAPE_DRIFT")
    target = [row for row in rows if row.get("canonical_event_id") in EXPECTED_EVENT_IDS]
    if (
        tuple(row["canonical_event_id"] for row in target) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in target) != EXPECTED_RANKS
    ):
        _fail("CURRENT_CENSUS_0D8_EXACT4_IDENTITY_DRIFT")
    required = {
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
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
    }
    for row in target:
        if any(row.get(key) != value for key, value in required.items()):
            _fail("CURRENT_CENSUS_0D8_PREFORMAL_STATE_DRIFT")
    orthogonal = [
        row for row in rows
        if row.get("current_global_status") == "COMPLETED_HUMAN_NEGATIVE"
        and row.get("chemistry_disposition") == "POSITIVE"
        and row.get("task_relevance_disposition") == "NOT_RELEVANT"
    ]
    if (
        len(orthogonal) != 8
        or sum(row.get("ligand_component_id") == "GVE" for row in orthogonal) != 4
        or sum(row.get("ligand_component_id") == "LCY" for row in orthogonal) != 4
    ):
        _fail("CURRENT_ORTHOGONAL_POPULATION_NOT_GVE4_PLUS_LCY4")
    return {
        "source_SHA256": CENSUS_BINDING[3],
        "row_count": 1000,
        "column_count": 47,
        "target_event_count": 4,
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": False,
        "chemistry": "UNRESOLVED",
        "task_relevance": "UNRESOLVED",
        "training_use": "UNRESOLVED",
        "pair_authority": False,
        "role_authority": False,
        "role_profile": "NOT_ESTABLISHED",
        "mask_labels_available": False,
        "current_orthogonal_population": 8,
        "current_orthogonal_breakdown": {"GVE": 4, "LCY": 4},
        "future_with_0D8_orthogonal_count_preview": 12,
        "future_arithmetic_only": True,
        "census_refresh_performed": False,
        "current_census_modified": False,
    }


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    source_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Bind Exact10, independently validate formal semantics, and return metadata."""

    repo_root = Path(repo_root).resolve()
    overrides = _normalize_overrides(source_overrides)
    payloads = _verify_bindings(repo_root, ACTIVE_BINDINGS, overrides)
    identities = [
        (binding[1], binding[0].as_posix(), binding[3]) for binding in ACTIVE_BINDINGS
    ]
    if len(ACTIVE_BINDINGS) != 10 or len(set(identities)) != 10:
        _fail("ACTIVE_SOURCE_BINDINGS_NOT_UNIQUE_EXACT10")
    formal = _strict_json_loads(payloads[FORMAL_DECISION_RELATIVE], "0D8_FORMAL_DECISION")
    _validate_formal_document(formal)
    event_evidence = _validate_event_evidence(payloads[EVENT_EVIDENCE_RELATIVE])
    graph = _validate_graph_candidates(payloads[GRAPH_CANDIDATES_RELATIVE])
    canonical = _validate_canonical_owner(payloads[CANONICAL_TASK_OWNER_RELATIVE])
    precedent = _validate_task_domain_negative_precedent(
        payloads[TASK_DOMAIN_NEGATIVE_MATRIX_RELATIVE]
    )
    census = _validate_current_census(payloads[CENSUS_MATRIX_RELATIVE])
    # The runtime and generic owners are imported only after their V2 bindings above pass.
    runtime = _validate_published_direct_runtime(repo_root, graph)
    generic = _validate_generic_owner_compatibility(repo_root)
    return {
        "active_source_bindings": _binding_records(ACTIVE_BINDINGS),
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "formal": formal,
        "event_evidence": event_evidence,
        "graph": graph,
        "canonical_task_owner": canonical,
        "task_domain_negative_precedent": precedent,
        "runtime_validation": runtime,
        "generic_owner_compatibility": generic,
        "current_census_boundary": census,
    }


def _metadata_only_boundary() -> dict[str, object]:
    return {
        "metadata_only": True,
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
        "dataset_mutated": False,
        "training_dataset_changed": False,
        "tensorization": False,
        "loader_modified": False,
        "batch_modified": False,
        "model_forward": False,
        "loss": False,
        "backward": False,
        "optimizer": False,
        "parameter_update": False,
        "training": False,
        "reconciliation": False,
        "census_refresh": False,
        "queue_refresh": False,
    }


def _canonical_task_applicability() -> list[dict[str, object]]:
    return [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "structurally_applicable": task_id in DIRECT_APPLICABLE_TASK_IDS,
            "training_mask_target_available_now": False,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]


def _canonical_task_contract() -> dict[str, object]:
    return {
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task": False,
        "tasks": _canonical_task_applicability(),
        "role_profile": EXPECTED_ROLE_PROFILE,
        "sample_applicable_task_ids": [0, 3, 4],
        "task_applicability_determined": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "all_training_mask_targets_available_now": False,
        "mask_authority_created": False,
    }


def _pair_boundary() -> dict[str, object]:
    return {
        "reactive_pair_human_decision_available": True,
        "reactive_pair_human_authoritative": True,
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C8",
        "pair_authority_scope": PAIR_AUTHORITY_SCOPE,
        "reusable_pair_rule_created": False,
        "cross_structure_regiochemistry_generalization": False,
        "Q_authority_transfer": False,
        "ligand_wide_selection": False,
    }


def _role_boundary() -> dict[str, object]:
    return {
        "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True,
        "selected_candidate_index_0based": 0,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "warhead_atoms": list(WARHEAD_ATOMS),
        "linker_atoms": [],
        "scaffold_atoms": list(SCAFFOLD_ATOMS),
        "W_L_S_counts": [2, 0, 3],
        "boundary_bonds": copy.deepcopy(list(BOUNDARY_BONDS)),
        "role_authority_scope": ROLE_AUTHORITY_SCOPE,
        "reusable_role_authority": False,
        "independent_mask_authority_created": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "formal_event_training_use_decision": "NOT_APPLICABLE",
        "event_training_use_human_decision_available": True,
        "training_use_allowed": False,
        "human_training_excluded": False,
        "training_exclusion_reason": "",
        "candidate_for_future_training_admission": False,
        "future_training_admission_candidate": False,
        "future_training_admission_status": "",
        "training_admitted": False,
        "formal_training_admitted": False,
        "training_materialization_allowed_now": False,
        "training_materialization_allowed": False,
        "tensor_target_created": False,
        "model_supervision_usable": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "READY_FOR_TRAINING": False,
        "NOT_APPLICABLE_is_EXCLUDE_FROM_TRAINING_ONLY": False,
    }


def _pre_boundary() -> dict[str, object]:
    return {
        "supporting_PRE_source_graph_count_per_event": 0,
        "PRE_source_graph_present": False,
        "PRE_source_graph_count_per_event": 0,
        "PRE_mapping_count_per_event": 0,
        "PRE_mapping_status": PRE_MAPPING_STATUS,
        "PRE_status": PRE_STATUS,
        "PRE_topology_authority": False,
        "PRE_geometry_authority": False,
        "PRE_coordinates_authority": False,
        "PRE_reconstruction": False,
        "POST_to_PRE_copy": False,
        "PRE_zero_fill": False,
        "leaving_group_inferred": False,
        "reagent_inferred": False,
        "bond_edit_inferred": False,
    }


def _post_boundary() -> dict[str, object]:
    return {
        "POST_source_evidence_available": True,
        "explicit_covalent_evidence": True,
        "distance_only_inference": False,
        "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
        "POST_geometry_training_label_available_now": False,
        "observed_distances_angstrom": [float(row[5]) for row in EXPECTED_EVENTS],
    }


def _reusable_boundary() -> dict[str, object]:
    return {
        "reusable_chemistry_authority": False,
        "reaction_family_authority": False,
        "warhead_rule_authority": False,
        "warhead_type_authority": False,
        "reaction_family_training_class_target_available": False,
        "warhead_rule_training_class_target_available": False,
        "warhead_type_target_available": False,
        "reusable_authority_label_available": False,
    }


def _q_boundary() -> dict[str, object]:
    return {
        "formal_Exact4_instance_labels": ["F", "K", "P", "V"],
        "same_structure_extra_instance_label": "Q",
        "Q_current_target": False,
        "Q_authority_transfer": False,
        "Q_row_materialized": False,
        "ligand_wide_projection": False,
    }


def _operation_boundary() -> dict[str, object]:
    return {
        **_metadata_only_boundary(),
        "formal_state_modified": False,
        "formal_validator_imported": False,
        "formal_validator_executed": False,
        "formal_validator_subprocessed": False,
        "formal_validator_parsed": False,
        "formal_validator_ast_parsed": False,
        "formal_validator_runtime_dependency": False,
        "scientific_validator_executed": False,
        "preparation_builder_executed": False,
        "actual_training_task_label_dataset_created": False,
        "network_accessed": False,
        "commit": False,
        "push": False,
    }


def _readiness() -> dict[str, object]:
    return {
        "0D8_INGESTION_CANDIDATE_PASS": True,
        "0D8_FORMAL_DECISION_BOUND": True,
        "0D8_FORMAL_VALIDATOR_PROVENANCE_ONLY": True,
        "0D8_FORMAL_SEMANTICS_INDEPENDENTLY_VALIDATED": True,
        "0D8_COMPLETED_LANE_TASK_DOMAIN_NEGATIVE": True,
        "0D8_TASK_NOT_RELEVANT": True,
        "0D8_CHEMISTRY_POSITIVE": True,
        "0D8_CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE": True,
        "0D8_SAMPLE_SG_C8_AUTHORITY_AVAILABLE": True,
        "0D8_SAMPLE_ROLE_AUTHORITY_AVAILABLE": True,
        "0D8_ROLE_PROFILE_DIRECT": True,
        "0D8_SAMPLE_TASK_APPLICABILITY_DETERMINED": True,
        "0D8_SAMPLE_APPLICABLE_TASK_IDS_0_3_4": True,
        "0D8_AUTHORITATIVE_TASK_LABELS_CREATED": False,
        "0D8_EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "0D8_TRAINING_MASK_TARGETS_AVAILABLE": False,
        "0D8_D5_NOT_APPLICABLE": True,
        "0D8_HUMAN_TRAINING_EXCLUDED": False,
        "0D8_FUTURE_TRAINING_ADMISSION_CANDIDATE": False,
        "PRE_SOURCE_GRAPH_NOT_AVAILABLE": True,
        "PRE_REACTION_UNRESOLVED": True,
        "POST_TRAINING_AUTHORITY": False,
        "GENERIC_EXACT11_COMPATIBILITY_PASS": True,
        "GENERIC_SOURCE_NAMESPACE_REPOSITORY_PARENT_RELATIVE": True,
        "ACTIVE_SOURCE_BINDINGS_10": True,
        "CURRENT_ORTHOGONAL_POPULATION_8": True,
        "FUTURE_ORTHOGONAL_POPULATION_12_PREVIEW_ONLY": True,
        "CURRENT_CENSUS_REFRESH": False,
        "RECONCILIATION": False,
        "QUEUE_REFRESH": False,
        "EXACT5_B3_PRESENT": True,
        "SIXTH_TASK": False,
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "READY_FOR_EXTERNAL_REVIEW": True,
        "COMMIT": False,
        "PUSH": False,
    }


def _event_projection(row: tuple[object, ...]) -> dict[str, object]:
    event_id, rank, protein_asym, ligand_asym, connection, distance, reported = row
    return {
        "canonical_event_id": event_id,
        "scaleup_rank": rank,
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": "4V37",
        "model_number": 1,
        "protein_chain_or_asym": protein_asym,
        "cys_residue_id": "CYS:450-",
        "protein_altloc": "",
        "ligand_component_id": "0D8",
        "ligand_chain_or_asym": ligand_asym,
        "ligand_altloc": "",
        "selected_connection_id": connection,
        "POST_distance_frozen_lexeme": distance,
        "reported_POST_distance_frozen_lexeme": reported,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "human_review_completed": True,
        "task_relevance": "NOT_RELEVANT",
        "task_relevance_human_authority": True,
        "human_task_relevance_decision": "NOT_RELEVANT",
        "task_relevance_human_authoritative": True,
        "chemistry": "POSITIVE",
        "chemistry_known_positive": True,
        "chemistry_human_authority": True,
        "human_chemistry_decision": "POSITIVE",
        "chemistry_human_authoritative": True,
        "negative_chemistry": False,
        "task_domain_negative": True,
        "positive_generative_supervision_eligible": False,
        **_pair_boundary(),
        **_role_boundary(),
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task": False,
        "task_applicability_determined": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        **_training_boundary(),
        "training_mask_targets_available_now": False,
        **_pre_boundary(),
        **_post_boundary(),
        **_reusable_boundary(),
        "authority_source": AUTHORITY_SOURCE,
        **_metadata_only_boundary(),
    }


def _standalone_bound() -> dict[str, object]:
    generic_facts = [
        {
            "canonical_event_id": event_id,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            **GENERIC_PROJECTION,
            "source_decision_schema": FORMAL_DECISION_SCHEMA,
            "source_decision_sha256": FORMAL_BINDINGS[0][3],
            "source_binding_path": FORMAL_DECISION_RELATIVE.as_posix(),
        }
        for event_id in EXPECTED_EVENT_IDS
    ]
    return {
        "active_source_bindings": _binding_records(ACTIVE_BINDINGS),
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "runtime_validation": {
            "validator": "validate_role_profile_v1",
            "runtime_import_path_exact": True,
            "call_count_for_selected_partition": 1,
            "valid": True,
            "reasons": [],
            "profile": EXPECTED_ROLE_PROFILE,
            "warhead_count": 2,
            "linker_count": 0,
            "scaffold_count": 3,
            "sample_applicable_task_ids": [0, 3, 4],
            "direct_scaffold_warhead_boundary": {
                "scaffold_atom_id": "C7",
                "warhead_atom_id": "C8",
                "bond_order": "SING",
                "boundary_valid": True,
            },
        },
        "generic_owner_compatibility": {
            "generic_exact11_compatibility_pass": True,
            "generic_fact_field_count": 11,
            "generic_fact_fields": list(GENERIC_FACT_FIELDS),
            "accepted_fact_count": 4,
            "actual_source_binding": {
                "source_path": FORMAL_DECISION_RELATIVE.as_posix(),
                "path_namespace": "repository_parent_relative",
                "byte_count": FORMAL_BINDINGS[0][2],
                "sha256": FORMAL_BINDINGS[0][3],
                "schema_version": FORMAL_DECISION_SCHEMA,
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            },
            "facts": generic_facts,
            "rich_fields_leaked": False,
            "scientific_synthetic_probe_used": False,
            "reconciliation_performed": False,
        },
        "current_census_boundary": {
            "source_SHA256": CENSUS_BINDING[3],
            "row_count": 1000,
            "column_count": 47,
            "target_event_count": 4,
            "current_global_status": "CURRENTLY_UNREVIEWED",
            "human_review_completed": False,
            "chemistry": "UNRESOLVED",
            "task_relevance": "UNRESOLVED",
            "training_use": "UNRESOLVED",
            "pair_authority": False,
            "role_authority": False,
            "role_profile": "NOT_ESTABLISHED",
            "mask_labels_available": False,
            "current_orthogonal_population": 8,
            "current_orthogonal_breakdown": {"GVE": 4, "LCY": 4},
            "future_with_0D8_orthogonal_count_preview": 12,
            "future_arithmetic_only": True,
            "census_refresh_performed": False,
            "current_census_modified": False,
        },
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "FROZEN_0D8_FORMAL_HUMAN_DECISION_METADATA_ONLY_PROJECTION",
        "formal_decision_identity": bound["formal_decision_binding"],
        "formal_semantic_canonical_sha256": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_semantics_independently_validated": True,
        "formal_validator_identity": bound["formal_validator_binding"],
        "formal_validator_lifecycle": {
            "lifecycle": "PROVENANCE_IDENTITY_ONLY",
            "imported": False,
            "executed": False,
            "subprocessed": False,
            "parsed": False,
            "ast_parsed": False,
            "runtime_dependency": False,
        },
        "formal_lifecycle": {
            "approved": True,
            "unsigned": False,
            "decision_finalized": True,
            "human_review_completed": True,
            "human_decision_created": True,
            "formal_decision_created": True,
            "formal_authority_created": True,
            "formal_authority_is_human": True,
            "machine_approval_claimed": False,
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_AUTHORIZATION",
        },
        "formal_D1_D6": {
            "D1": "NOT_RELEVANT",
            "D2": "POSITIVE",
            "D3": "CONFIRM_OBSERVED_PAIR",
            "D4": "SELECT_CANDIDATE_0",
            "D5": "NOT_APPLICABLE",
            "D6": EXPECTED_D6,
            "D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT,
            "D6_utf8_sha256": EXPECTED_D6_SHA256,
        },
        "formal_core_authority": {
            "true_set": [
                "formal_authority_created",
                "formal_authority_is_human",
                "sample_task_relevance_authority",
                "sample_positive_chemistry_authority",
                "sample_reactive_pair_authority",
                "sample_role_partition_authority",
                "human_training_use_disposition_authority",
            ],
            "true_count": 7,
            "eighth_authority": False,
            "reusable_authority_created": False,
        },
        "target_Exact4": {
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "event_count": 4,
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "scaleup_ranks": list(EXPECTED_RANKS),
            "pdb_id": "4V37",
            "ligand_component_id": "0D8",
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "C8",
            "ligand_wide_selector": False,
        },
        "events": [_event_projection(row) for row in EXPECTED_EVENTS],
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "task_chemistry_boundary": {
            "task_relevance": "NOT_RELEVANT",
            "chemistry": "POSITIVE",
            "task_domain_negative": True,
            "negative_chemistry": False,
            "chemistry_positive_preserved": True,
        },
        "reactive_pair_authority": _pair_boundary(),
        "selected_role_partition": _role_boundary(),
        "published_DIRECT_runtime_revalidation": bound["runtime_validation"],
        "canonical_task_contract": _canonical_task_contract(),
        "training_boundary": _training_boundary(),
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(),
        "reusable_authority_boundary": _reusable_boundary(),
        "same_structure_Q_boundary": _q_boundary(),
        "generic_Exact11_compatibility": bound["generic_owner_compatibility"],
        "current_with_LCY_census_preformal_boundary": bound["current_census_boundary"],
        "active_source_binding_count": 10,
        "semantic_source_identity_count": 10,
        "duplicate_source_binding_identity_count": 0,
        "operation_boundary": _operation_boundary(),
        "readiness": _readiness(),
    }


# Exact header/order copied from the published LCY modern 115-column matrix.
MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "review_unit_id", "pdb_id",
    "model_number", "protein_chain_or_asym", "cys_residue_id", "protein_altloc",
    "ligand_component_id", "ligand_chain_or_asym", "ligand_altloc",
    "selected_connection_id", "POST_distance_angstrom",
    "reported_POST_distance_angstrom", "completed_lane", "human_review_completed",
    "task_relevance", "task_relevance_human_authority",
    "human_task_relevance_decision", "task_relevance_human_authoritative",
    "chemistry", "chemistry_known_positive", "chemistry_human_authority",
    "human_chemistry_decision", "chemistry_human_authoritative", "negative_chemistry",
    "task_domain_negative", "positive_generative_supervision_eligible",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "protein_reactive_atom", "ligand_reactive_atom", "pair_authority_scope",
    "reusable_pair_rule_created", "cross_structure_regiochemistry_generalization",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "selected_candidate_index_0based", "role_profile", "warhead_atoms_json",
    "linker_atoms_json", "scaffold_atoms_json", "W_L_S_counts_json",
    "boundary_bonds_json", "reusable_role_authority", "global_canonical_task_count",
    "B3_present", "sixth_task", "canonical_task_applicability_json",
    "direct_profile_applicable_task_ids_json", "task_applicability_determined",
    "authoritative_task_labels_created", "event_task_label_rows_materialized",
    "formal_event_training_use_decision", "event_training_use_human_decision_available",
    "training_use_allowed", "human_training_excluded", "training_exclusion_reason",
    "candidate_for_future_training_admission", "future_training_admission_candidate",
    "future_training_admission_status", "training_admitted", "formal_training_admitted",
    "training_materialization_allowed_now", "training_materialization_allowed",
    "tensor_target_created", "model_supervision_usable",
    "training_mask_targets_available_now", "current_runtime_model_usable",
    "parameter_update_authorization", "READY_FOR_TRAINING",
    "supporting_PRE_source_graph_count_per_event", "PRE_source_graph_present",
    "PRE_source_graph_count_per_event", "PRE_mapping_count_per_event",
    "PRE_mapping_status", "PRE_status", "PRE_topology_authority",
    "PRE_geometry_authority", "PRE_coordinates_authority", "PRE_reconstruction",
    "POST_to_PRE_copy", "PRE_zero_fill", "leaving_group_inferred",
    "reagent_inferred", "bond_edit_inferred", "POST_source_evidence_available",
    "explicit_covalent_evidence", "distance_only_inference",
    "POST_geometry_training_authority", "POST_geometry_training_target_created",
    "POST_geometry_training_label_available_now", "reusable_chemistry_authority",
    "reaction_family_authority", "warhead_rule_authority", "warhead_type_authority",
    "reaction_family_training_class_target_available",
    "warhead_rule_training_class_target_available", "warhead_type_target_available",
    "reusable_authority_label_available", "authority_source",
    "projection_of_frozen_formal_human_authority",
    "new_human_authority_created_by_ingestion", "metadata_only", "dataset_mutated",
    "training_dataset_changed", "tensorization", "loader_modified", "batch_modified",
    "model_forward", "loss", "backward", "optimizer", "parameter_update", "training",
)


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    if len(MATRIX_HEADER) != 115:
        _fail("INTERNAL_MATRIX_HEADER_NOT_EXACT115")
    applicability = snapshot["canonical_task_contract"]["tasks"]
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        row: dict[str, object] = {
            key: "true" if value is True else "false" if value is False else value
            for key, value in event.items()
            if key in MATRIX_HEADER
        }
        row.update(
            {
                "scaleup_rank": str(event["scaleup_rank"]),
                "model_number": "1",
                "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
                "reported_POST_distance_angstrom": event[
                    "reported_POST_distance_frozen_lexeme"
                ],
                "selected_candidate_index_0based": "0",
                "warhead_atoms_json": _json_cell(list(WARHEAD_ATOMS)),
                "linker_atoms_json": "[]",
                "scaffold_atoms_json": _json_cell(list(SCAFFOLD_ATOMS)),
                "W_L_S_counts_json": "[2,0,3]",
                "boundary_bonds_json": _json_cell(list(BOUNDARY_BONDS)),
                "global_canonical_task_count": "5",
                "B3_present": "true",
                "sixth_task": "false",
                "canonical_task_applicability_json": _json_cell(applicability),
                "direct_profile_applicable_task_ids_json": "[0,3,4]",
                "training_exclusion_reason": "",
                "future_training_admission_status": "",
            }
        )
        if set(row) != set(MATRIX_HEADER):
            _fail("INTERNAL_MATRIX_ROW_SHAPE_INVALID")
        rows.append(row)
    return rows


def _summary(snapshot: Mapping[str, Any]) -> dict[str, object]:
    events = snapshot["events"]
    if type(events) is not list:
        _fail("SUMMARY_SOURCE_EVENTS_INVALID")
    count = lambda key, value: sum(event.get(key) == value for event in events)
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "review_unit": "0D8",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": len(events),
        "completed_review_unit_count": 1,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "task_not_relevant_count": count("task_relevance", "NOT_RELEVANT"),
        "chemistry_positive_count": count("chemistry", "POSITIVE"),
        "negative_chemistry_count": count("negative_chemistry", True),
        "pair_authority_event_count": count("reactive_pair_human_authoritative", True),
        "role_authority_event_count": count("role_partition_human_authoritative", True),
        "task_applicability_determined_event_count": count("task_applicability_determined", True),
        "authoritative_task_label_event_count": count("authoritative_task_labels_created", True),
        "event_task_label_rows_materialized_count": count("event_task_label_rows_materialized", True),
        "training_not_applicable_count": count("formal_event_training_use_decision", "NOT_APPLICABLE"),
        "human_training_excluded_count": count("human_training_excluded", True),
        "future_training_candidate_count": count("future_training_admission_candidate", True),
        "formal_training_admitted_count": count("formal_training_admitted", True),
        "tensor_target_count": count("tensor_target_created", True),
        "runtime_usable_count": count("current_runtime_model_usable", True),
        "PRE_source_graph_present_count": count("PRE_source_graph_present", True),
        "PRE_mapping_count": sum(event["PRE_mapping_count_per_event"] for event in events),
        "PRE_resolved_count": sum(event["PRE_status"] != PRE_STATUS for event in events),
        "POST_source_evidence_count": count("POST_source_evidence_available", True),
        "POST_training_authority_count": count("POST_geometry_training_authority", True),
        "reaction_family_target_count": count("reaction_family_training_class_target_available", True),
        "warhead_rule_target_count": count("warhead_rule_training_class_target_available", True),
        "warhead_type_target_count": count("warhead_type_target_available", True),
        "training_mask_target_available_count": count("training_mask_targets_available_now", True),
        "generic_exact11_accepted_count": 4,
        "active_source_binding_count": 10,
        "duplicate_source_binding_identity_count": 0,
        "current_global_census_modified": False,
        "current_orthogonal_population": 8,
        "future_orthogonal_population_preview": 12,
        "future_arithmetic_only": True,
        "census_refresh_performed": False,
        "canonical_task_contract": _canonical_task_contract(),
        "role_partition": _role_boundary(),
        "training_boundary": _training_boundary(),
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(),
        "generic_Exact11": snapshot["generic_Exact11_compatibility"],
        "operation_boundary": _operation_boundary(),
        "readiness": _readiness(),
    }


def _validate_text_payload(label: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes
        or not payload
        or b"\r" in payload
        or b"\x00" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail("TEXT_PAYLOAD_HYGIENE_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ZeroD8IngestionSafetyError(
            "COVAPIE_0D8_INGESTION_V1_ERROR:TEXT_UTF8_INVALID:" + label
        ) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TEXT_TRAILING_WHITESPACE:" + label)


_DYNAMIC_KEYS = {"timestamp", "hostname", "pid", "uuid"}


def _reject_dynamic_or_forbidden_metadata(value: object, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in _DYNAMIC_KEYS):
                _fail("DYNAMIC_METADATA_KEY:" + path + "." + str(key))
            if lowered in {"self_sha256", "manifest_sha256"}:
                _fail("SELF_SHA256_FORBIDDEN:" + path + "." + str(key))
            _reject_dynamic_or_forbidden_metadata(item, path + "." + str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_dynamic_or_forbidden_metadata(item, f"{path}[{index}]")
    elif isinstance(value, str) and value.startswith("/"):
        _fail("ABSOLUTE_PATH_FORBIDDEN:" + path)


def _candidate_source_bindings(repo_root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for relative in (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE):
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ZeroD8IngestionSafetyError(
                "COVAPIE_0D8_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
                + relative.as_posix()
            ) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("CANDIDATE_SOURCE_NOT_REGULAR:" + relative.as_posix())
        if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            _fail("CANDIDATE_SOURCE_EXECUTABLE:" + relative.as_posix())
        _validate_text_payload(relative.as_posix(), payload)
        records.append(
            {
                "path": relative.as_posix(),
                "namespace": "repository_relative",
                "byte_count": len(payload),
                "SHA256": _sha256(payload),
                "expected_path_class": "REGULAR_NON_SYMLINK",
                "expected_executable_class": "NON_EXECUTABLE",
            }
        )
    return records


def _manifest(
    bound: Mapping[str, object],
    candidate_sources: list[dict[str, object]],
    snapshot_payload: bytes,
    matrix_payload: bytes,
    summary_payload: bytes,
) -> dict[str, object]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": (
            "0D8_COMPLETED_DECISION_METADATA_ONLY_INGESTION_NOT_RECONCILIATION_"
            "CENSUS_QUEUE_REFRESH_TASK_LABEL_MATERIALIZATION_OR_TRAINING"
        ),
        "schemas": {
            "snapshot": SNAPSHOT_SCHEMA_VERSION,
            "matrix": MATRIX_SCHEMA_VERSION,
            "summary": SUMMARY_SCHEMA_VERSION,
            "manifest": MANIFEST_SCHEMA_VERSION,
        },
        "candidate_publication_file_count": 7,
        "candidate_publication_paths": [
            path.as_posix() for path in CANDIDATE_PUBLICATION_PATHS
        ],
        "output_artifact_count": 4,
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "candidate_source_bindings": candidate_sources,
        "active_source_binding_count": 10,
        "semantic_source_identity_count": 10,
        "duplicate_source_binding_identity_count": 0,
        "active_source_bindings": bound["active_source_bindings"],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_executed": False,
        "formal_validator_subprocessed": False,
        "formal_validator_parsed": False,
        "formal_validator_ast_parsed": False,
        "formal_validator_runtime_dependency": False,
        "formal_semantic_digest": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_semantics_independently_validated": True,
        "task_domain_negative_role_authority_hybrid_contract": {
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "task_relevance": "NOT_RELEVANT",
            "chemistry": "POSITIVE",
            "chemistry_positive_preserved": True,
            "sample_pair_authority": True,
            "sample_role_authority": True,
            "sample_task_applicability_determined": True,
            "authoritative_task_labels_created": False,
            "event_task_label_rows_materialized": False,
            "training_mask_targets_available": False,
        },
        "matrix_contract": {
            "column_count": 115,
            "header": list(MATRIX_HEADER),
            "header_matches_published_LCY_modern_matrix": True,
            "row_count": 4,
            "additional_116th_column_added": False,
        },
        "canonical_task_contract": _canonical_task_contract(),
        "reactive_pair_authority": _pair_boundary(),
        "selected_role_partition": _role_boundary(),
        "published_DIRECT_runtime_revalidation": bound["runtime_validation"],
        "generic_Exact11_contract": bound["generic_owner_compatibility"],
        "training_boundary": _training_boundary(),
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(),
        "reusable_authority_boundary": _reusable_boundary(),
        "same_structure_Q_boundary": _q_boundary(),
        "current_census_preformal_boundary": bound["current_census_boundary"],
        "future_arithmetic_preview_only_boundary": {
            "current_orthogonal_population": 8,
            "future_with_0D8_orthogonal_population_preview": 12,
            "future_arithmetic_only": True,
            "current_census_refresh_performed": False,
            "current_global_orthogonal_count_claimed_12": False,
        },
        "operation_boundary": _operation_boundary(),
        **_metadata_only_boundary(),
        "output_artifact_bindings": {
            SNAPSHOT: {
                "byte_count": len(snapshot_payload),
                "SHA256": _sha256(snapshot_payload),
                "expected_path_class": "REGULAR_NON_SYMLINK",
                "expected_executable_class": "NON_EXECUTABLE",
            },
            MATRIX: {
                "byte_count": len(matrix_payload),
                "SHA256": _sha256(matrix_payload),
                "expected_path_class": "REGULAR_NON_SYMLINK",
                "expected_executable_class": "NON_EXECUTABLE",
            },
            SUMMARY: {
                "byte_count": len(summary_payload),
                "SHA256": _sha256(summary_payload),
                "expected_path_class": "REGULAR_NON_SYMLINK",
                "expected_executable_class": "NON_EXECUTABLE",
            },
        },
        "manifest_self_SHA256_recorded": False,
        "MANIFEST_SELF_SHA256_PROHIBITED": True,
        "determinism_contract": {
            "source_derived_only": True,
            "UTF8": True,
            "LF": True,
            "single_final_LF": True,
            "dynamic_metadata_absent": True,
            "absolute_machine_paths_absent": True,
            "live_git_state_absent": True,
            "independent_double_build_required": True,
        },
        "readiness": _readiness(),
    }


def _build_artifacts_unvalidated(repo_root: Path) -> dict[str, bytes]:
    repo_root = Path(repo_root).resolve()
    bound = load_frozen_formal_decision_v1(repo_root)
    snapshot_payload = _json_bytes(_snapshot(bound))
    snapshot = _strict_json_loads(snapshot_payload, "BUILT_SNAPSHOT")
    matrix_payload = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    summary_payload = _json_bytes(_summary(snapshot))
    manifest_payload = _json_bytes(
        _manifest(
            bound,
            _candidate_source_bindings(repo_root),
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


def validate_completed_decision_projection_v1(
    artifacts: Mapping[str, bytes], *, repo_root: Path | None = None
) -> None:
    """Fail closed unless all four 0D8 metadata projections are exact."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    snapshot = _strict_json_loads(artifacts[SNAPSHOT], "SNAPSHOT")
    summary = _strict_json_loads(artifacts[SUMMARY], "SUMMARY")
    manifest = _strict_json_loads(artifacts[MANIFEST], "MANIFEST")
    rows = _parse_csv(artifacts[MATRIX], "MATRIX")
    for document in (snapshot, summary, manifest):
        _reject_dynamic_or_forbidden_metadata(document)
    standalone = _standalone_bound()
    _expect(snapshot, _snapshot(standalone), "SNAPSHOT_EXACT_PROJECTION_INVALID")
    _expect(summary, _summary(snapshot), "SUMMARY_EXACT_COUNTS_INVALID")
    if not rows or tuple(rows[0]) != MATRIX_HEADER or len(MATRIX_HEADER) != 115:
        _fail("MATRIX_HEADER_NOT_PUBLISHED_EXACT115")
    if artifacts[MATRIX] != _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot)):
        _fail("MATRIX_EXACT_PROJECTION_INVALID")
    if (
        len(rows) != 4
        or tuple(row["canonical_event_id"] for row in rows) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in rows) != EXPECTED_RANKS
        or len({row["canonical_event_id"] for row in rows}) != 4
        or any(":Q:" in row["canonical_event_id"] for row in rows)
    ):
        _fail("MATRIX_EXACT4_IDENTITY_OR_Q_BOUNDARY_INVALID")
    required_true = (
        "human_review_completed",
        "task_relevance_human_authority",
        "task_relevance_human_authoritative",
        "chemistry_known_positive",
        "chemistry_human_authority",
        "chemistry_human_authoritative",
        "task_domain_negative",
        "reactive_pair_human_decision_available",
        "reactive_pair_human_authoritative",
        "role_partition_human_decision_available",
        "role_partition_human_authoritative",
        "B3_present",
        "task_applicability_determined",
        "event_training_use_human_decision_available",
        "POST_source_evidence_available",
        "explicit_covalent_evidence",
        "projection_of_frozen_formal_human_authority",
        "metadata_only",
    )
    required_false = (
        "negative_chemistry",
        "positive_generative_supervision_eligible",
        "reusable_pair_rule_created",
        "cross_structure_regiochemistry_generalization",
        "reusable_role_authority",
        "sixth_task",
        "authoritative_task_labels_created",
        "event_task_label_rows_materialized",
        "training_use_allowed",
        "human_training_excluded",
        "candidate_for_future_training_admission",
        "future_training_admission_candidate",
        "training_admitted",
        "formal_training_admitted",
        "training_materialization_allowed_now",
        "training_materialization_allowed",
        "tensor_target_created",
        "model_supervision_usable",
        "training_mask_targets_available_now",
        "current_runtime_model_usable",
        "parameter_update_authorization",
        "READY_FOR_TRAINING",
        "PRE_source_graph_present",
        "PRE_topology_authority",
        "PRE_geometry_authority",
        "PRE_coordinates_authority",
        "PRE_reconstruction",
        "POST_to_PRE_copy",
        "PRE_zero_fill",
        "leaving_group_inferred",
        "reagent_inferred",
        "bond_edit_inferred",
        "distance_only_inference",
        "POST_geometry_training_authority",
        "POST_geometry_training_target_created",
        "POST_geometry_training_label_available_now",
        "reusable_chemistry_authority",
        "reaction_family_authority",
        "warhead_rule_authority",
        "warhead_type_authority",
        "reaction_family_training_class_target_available",
        "warhead_rule_training_class_target_available",
        "warhead_type_target_available",
        "reusable_authority_label_available",
        "new_human_authority_created_by_ingestion",
        "dataset_mutated",
        "training_dataset_changed",
        "tensorization",
        "loader_modified",
        "batch_modified",
        "model_forward",
        "loss",
        "backward",
        "optimizer",
        "parameter_update",
        "training",
    )
    for row in rows:
        try:
            applicability = json.loads(row["canonical_task_applicability_json"])
            boundary = json.loads(row["boundary_bonds_json"])
        except json.JSONDecodeError as error:
            raise ZeroD8IngestionSafetyError(
                "COVAPIE_0D8_INGESTION_V1_ERROR:MATRIX_JSON_CELL_INVALID"
            ) from error
        if (
            row["completed_lane"] != EXPECTED_COMPLETED_LANE
            or row["task_relevance"] != "NOT_RELEVANT"
            or row["human_task_relevance_decision"] != "NOT_RELEVANT"
            or row["chemistry"] != "POSITIVE"
            or row["human_chemistry_decision"] != "POSITIVE"
            or row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "C8"
            or row["pair_authority_scope"] != PAIR_AUTHORITY_SCOPE
            or row["selected_candidate_index_0based"] != "0"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or json.loads(row["warhead_atoms_json"]) != list(WARHEAD_ATOMS)
            or json.loads(row["linker_atoms_json"]) != []
            or json.loads(row["scaffold_atoms_json"]) != list(SCAFFOLD_ATOMS)
            or json.loads(row["W_L_S_counts_json"]) != [2, 0, 3]
            or boundary != list(BOUNDARY_BONDS)
            or row["global_canonical_task_count"] != "5"
            or [item["task_id"] for item in applicability] != [0, 1, 2, 3, 4]
            or [item["structurally_applicable"] for item in applicability]
            != [True, False, False, True, True]
            or any(item["training_mask_target_available_now"] for item in applicability)
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or row["formal_event_training_use_decision"] != "NOT_APPLICABLE"
            or row["training_exclusion_reason"] != ""
            or row["future_training_admission_status"] != ""
            or row["supporting_PRE_source_graph_count_per_event"] != "0"
            or row["PRE_source_graph_count_per_event"] != "0"
            or row["PRE_mapping_count_per_event"] != "0"
            or row["PRE_mapping_status"] != PRE_MAPPING_STATUS
            or row["PRE_status"] != PRE_STATUS
            or row["authority_source"] != AUTHORITY_SOURCE
            or any(row[key] != "true" for key in required_true)
            or any(row[key] != "false" for key in required_false)
        ):
            _fail("MATRIX_AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    generic = snapshot.get("generic_Exact11_compatibility")
    if type(generic) is not dict or generic.get("accepted_fact_count") != 4:
        _fail("GENERIC_EXACT11_ACCEPTANCE_INVALID")
    facts_value = generic.get("facts")
    if type(facts_value) is not list or any(
        type(fact) is not dict
        or len(fact) != 11
        or set(fact) != set(GENERIC_FACT_FIELDS)
        for fact in facts_value
    ):
        _fail("GENERIC_RICH_TO_EXACT11_FIREWALL_INVALID")
    source = generic.get("actual_source_binding")
    if type(source) is not dict or (
        source.get("path_namespace") != "repository_parent_relative"
        or source.get("source_path") != FORMAL_DECISION_RELATIVE.as_posix()
        or source.get("sha256") != FORMAL_BINDINGS[0][3]
    ):
        _fail("GENERIC_ACTUAL_SOURCE_BINDING_INVALID")
    sources = manifest.get("candidate_source_bindings")
    if type(sources) is not list or len(sources) != 3:
        _fail("CANDIDATE_SOURCE_BINDINGS_INVALID")
    expected_paths = [
        SOURCE_RELATIVE.as_posix(),
        CHECKER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
    ]
    if [record.get("path") for record in sources if type(record) is dict] != expected_paths:
        _fail("CANDIDATE_SOURCE_BINDING_PATHS_INVALID")
    for record in sources:
        if type(record) is not dict or (
            record.get("namespace") != "repository_relative"
            or record.get("expected_path_class") != "REGULAR_NON_SYMLINK"
            or record.get("expected_executable_class") != "NON_EXECUTABLE"
            or type(record.get("byte_count")) is not int
            or type(record.get("SHA256")) is not str
            or len(record["SHA256"]) != 64
        ):
            _fail("CANDIDATE_SOURCE_BINDING_RECORD_INVALID")
    expected_manifest = _manifest(
        standalone,
        sources,
        artifacts[SNAPSHOT],
        artifacts[MATRIX],
        artifacts[SUMMARY],
    )
    _expect(manifest, expected_manifest, "MANIFEST_CLOSURE_INVALID")
    if repo_root is not None and dict(artifacts) != _build_artifacts_unvalidated(repo_root):
        _fail("DIRECT_SOURCE_DERIVED_PROJECTION_INVALID")


def build_artifacts_v1(repo_root: Path) -> dict[str, bytes]:
    """Build deterministic bytes for the four authorized 0D8 artifacts."""

    artifacts = _build_artifacts_unvalidated(Path(repo_root).resolve())
    validate_completed_decision_projection_v1(artifacts)
    return artifacts


def _validate_materialization_destination_v1(repo_root: Path, target_root: Path) -> None:
    expected = (repo_root / OUTPUT_ROOT_RELATIVE).resolve()
    if target_root.resolve() != expected:
        _fail("OUTPUT_ROOT_OUTSIDE_AUTHORIZED_DESTINATION")
    try:
        metadata = target_root.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _fail("OUTPUT_ROOT_NOT_REAL_DIRECTORY")
    unexpected = {path.name for path in target_root.iterdir()} - set(OUTPUT_FILENAMES)
    if unexpected:
        _fail("OUTPUT_ROOT_CONTAINS_UNAUTHORIZED_FILES")


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".covapie_0d8_write_", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, path)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def materialize_artifacts_v1(
    repo_root: Path, *, target_root: Path | None = None
) -> dict[str, bytes]:
    """Write only Exact4 under the authorized repository output root."""

    repo_root = Path(repo_root).resolve()
    destination = repo_root / OUTPUT_ROOT_RELATIVE if target_root is None else Path(target_root)
    _validate_materialization_destination_v1(repo_root, destination)
    destination.mkdir(parents=True, exist_ok=True)
    artifacts = build_artifacts_v1(repo_root)
    for name in OUTPUT_FILENAMES:
        _atomic_write(destination / name, artifacts[name])
    return artifacts


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    """Rebuild and compare all materialized 0D8 artifacts byte for byte."""

    repo_root = Path(repo_root).resolve()
    output_root = repo_root / OUTPUT_ROOT_RELATIVE
    _validate_materialization_destination_v1(repo_root, output_root)
    expected = build_artifacts_v1(repo_root)
    observed: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = output_root / name
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ZeroD8IngestionSafetyError(
                "COVAPIE_0D8_INGESTION_V1_ERROR:MATERIALIZED_READ_FAILED:" + name
            ) from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        ):
            _fail("MATERIALIZED_FILE_SECURITY_INVALID:" + name)
        observed[name] = payload
    if observed != expected:
        _fail("MATERIALIZED_BYTES_MISMATCH")
    validate_completed_decision_projection_v1(observed, repo_root=repo_root)
    return {
        "status": "PASS",
        "output_artifact_count": 4,
        "matrix_rows": 4,
        "matrix_columns": 115,
        "generic_exact11_accepted_count": 4,
        "active_source_binding_count": 10,
        "byte_identical_to_rebuild": True,
        "READY_FOR_TRAINING": False,
        "READY_FOR_EXTERNAL_REVIEW": True,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    materialize_artifacts_v1(repo_root)
    print(json.dumps(check_materialized_v1(repo_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
