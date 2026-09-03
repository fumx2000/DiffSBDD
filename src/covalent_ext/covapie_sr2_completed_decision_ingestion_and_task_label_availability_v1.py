"""Project frozen SR2 human authority into deterministic metadata-only artifacts.

The frozen formal validator is provenance identity only.  This owner binds its
bytes but never imports, parses, executes, or invokes it.  Formal semantics are
strict-parsed and independently validated against the bound SR2 structural
graph, the published DIRECT runtime, the canonical Exact5 owner, the published
positive-INCLUDE completed-lane precedent, and the current with-GD1 census.

This module performs no reconciliation, census or queue refresh, dataset
mutation, tensorization, loader/batch/model/loss/backward/optimizer operation,
training admission, training, or parameter update.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
import copy
import csv
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
    "SR2IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)


SCHEMA_VERSION = "covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_sr2_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_sr2_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_sr2_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_sr2_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_sr2_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_sr2_event_task_label_availability_v1.csv"
SUMMARY = "covapie_sr2_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_sr2_completed_decision_ingestion_manifest_v1.json"
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
    "SR2_COVAPIE_BULK_REVIEW_UNIT_A9BBD5309D7A5C08/"
    "formal-human-decision-v1"
)
FORMAL_DECISION_RELATIVE = FORMAL_ROOT / "sr2_formal_human_decision_v1.json"
FORMAL_VALIDATOR_RELATIVE = FORMAL_ROOT / "validate_sr2_formal_human_decision_v1.py"
STRUCTURAL_GRAPH_RELATIVE = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "SR2_COVAPIE_BULK_REVIEW_UNIT_A9BBD5309D7A5C08/"
    "review-preparation-v1/sr2_graph_and_role_candidates_v1.json"
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
COMPLETED_LANE_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CENSUS_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_with_gd1_v1.py"
)
CENSUS_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_gd1_v1"
)
CENSUS_MATRIX_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_census_with_gd1_v1.csv"
)
CENSUS_SUMMARY_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_summary_with_gd1_v1.json"
)
CENSUS_MANIFEST_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_manifest_with_gd1_v1.json"
)

BASELINE_COMMIT = "362c469b98bcd49d7ac0e4acfa99d2a2bae0f1dd"
FORMAL_DECISION_SCHEMA = "covapie_sr2_exact4_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "529800d94f1cbaf0b38e8f09ead254671e19cd18cf1246deea3f9b38246ea547"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_A9BBD5309D7A5C08"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
EXPECTED_COMPLETED_LANE = "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
TRAINING_USE_DECISION = "INCLUDE"
FUTURE_STATUS = "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"
FUTURE_INCLUSION_REASON = (
    "HUMAN_INCLUDE_DISPOSITION_WITH_SAMPLE_AUTHORITY_REQUIRES_"
    "INDEPENDENT_FUTURE_ADMISSION"
)
AUTHORITY_SOURCE = "FORMAL_SR2_HUMAN_DECISION"
PAIR_AUTHORITY_SCOPE = "CURRENT_SR2_2QLQ_2QQ7_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
ROLE_AUTHORITY_SCOPE = "CURRENT_SR2_EXACT4_REVIEW_UNIT_ONLY"
PRE_STATUS = "PRE_REACTION_UNRESOLVED"
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"

EXPECTED_D6 = (
    "Confirm the sample-specific observed CYS345-SG ↔ SR2-C51 covalent pair "
    "for the 2QLQ/2QQ7 Exact4 and select DIRECT candidate 15 as the sample-level "
    "scaffold/warhead partition, with W containing the complete source-graph "
    "unsaturated-amide/Michael-acceptor side chain through amide N11 and an "
    "empty linker. Treat SR2 as task-relevant and chemistry-positive medicinal "
    "covalent-inhibitor evidence and INCLUDE it for current V1 training-use "
    "disposition despite the engineered Src S345C / T338M-S345C surrogate "
    "context, because these structures were designed as a structural model for "
    "EGFR covalent-inhibitor chemistry. Freeze that engineered-surrogate status "
    "as a sample caveat: it creates no native Src-site authority, no EGFR C797 "
    "event-specific authority, no cross-structure regiochemistry authority, and "
    "no reusable reaction-family, warhead-rule, or warhead-type authority. PRE "
    "remains PRE_REACTION_UNRESOLVED because the available PRE source graph has "
    "no compatible mapping; do not reconstruct PRE, copy POST to PRE, or infer "
    "leaving groups, reagents, or bond edits. D5=INCLUDE is a training-use "
    "disposition only and does not create formal training admission, tensor "
    "targets, runtime-model usability, or parameter-update authorization."
)
EXPECTED_D6_BYTE_COUNT = 1236
EXPECTED_D6_SHA256 = "532f50bf3fe296ea76a548d9e6dc9b38b6d4ec9b8b3535e75f0c0b4e377e6cfa"

# event ID, rank, PDB, protein asym, ligand asym, connection, exact distance,
# frozen distance lexeme, reported distance
EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:2QLQ:A:CYS:345-:SG:C:SR2:C51",
        321, "2QLQ", "A", "C", "covale2", 1.676815, "1.676815", 1.677,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:2QLQ:B:CYS:345-:SG:E:SR2:C51",
        323, "2QLQ", "B", "E", "covale4", 1.867313, "1.867313", 1.867,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:2QQ7:A:CYS:345-:SG:C:SR2:C51",
        337, "2QQ7", "A", "C", "covale1", 1.856140, "1.856140", 1.856,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:2QQ7:B:CYS:345-:SG:D:SR2:C51",
        338, "2QQ7", "B", "D", "covale2", 1.864642, "1.864642", 1.865,
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)

WARHEAD_ROLE = ("C10", "C11", "C51", "C61", "C65", "C67", "N11", "N63", "O61")
LINKER_ROLE: tuple[str, ...] = ()
SCAFFOLD_ROLE = (
    "BRR1", "C13", "C17", "C18", "C19", "C20", "C21", "C22", "C3",
    "C4", "C5", "C6", "C7", "C8", "C9", "N1", "N2", "N3",
)
HEAVY_ATOMS = (
    "BRR1", "C10", "C11", "C13", "C17", "C18", "C19", "C20", "C21",
    "C22", "C3", "C4", "C5", "C51", "C6", "C61", "C65", "C67", "C7",
    "C8", "C9", "N1", "N11", "N2", "N3", "N63", "O61",
)
HEAVY_BONDS = (
    ("BRR1", "C3", "SING"), ("C10", "C11", "SING"),
    ("C10", "N11", "SING"), ("C10", "O61", "DOUB"),
    ("C11", "C51", "DOUB"), ("C13", "C17", "SING"),
    ("C13", "C9", "DOUB"), ("C17", "C18", "DOUB"),
    ("C18", "C7", "SING"), ("C18", "N2", "SING"),
    ("C19", "N2", "DOUB"), ("C19", "N3", "SING"),
    ("C20", "C21", "DOUB"), ("C20", "C5", "SING"),
    ("C21", "C22", "SING"), ("C22", "C3", "DOUB"),
    ("C3", "C4", "SING"), ("C4", "C5", "DOUB"),
    ("C5", "N1", "SING"), ("C51", "C61", "SING"),
    ("C6", "C7", "SING"), ("C6", "N1", "SING"),
    ("C6", "N3", "DOUB"), ("C61", "N63", "SING"),
    ("C65", "N63", "SING"), ("C67", "N63", "SING"),
    ("C7", "C8", "DOUB"), ("C8", "C9", "SING"),
    ("C9", "N11", "SING"),
)
BOUNDARY_BONDS = (
    {
        "aromatic_flag": "N",
        "atom_id_1": "C9",
        "atom_id_2": "N11",
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
        4, "scaffold_plus_linker_plus_warhead", "C",
        ("scaffold", "linker", "warhead"), ("minimal_seed",),
    ),
)
DIRECT_VALID_TASK_IDS = (0, 3, 4)
DIRECT_APPLICABILITY = (
    (0, "warhead_only", "A", True, "generate_W_condition_on_S"),
    (
        1, "linker_plus_warhead", "B", False,
        "not_applicable_empty_linker_redundant_with_A",
    ),
    (
        2, "scaffold_plus_warhead", "B2", False,
        "not_applicable_empty_non_C_fixed_context",
    ),
    (3, "scaffold_only", "B3", True, "generate_S_condition_on_W"),
    (
        4, "scaffold_plus_linker_plus_warhead", "C", True,
        "generate_whole_ligand_preserve_Task_C_seed_semantics",
    ),
)

# path, namespace, bytes, SHA256, expected executable, source role
FORMAL_BINDINGS = (
    (
        FORMAL_DECISION_RELATIVE, "project_parent_relative", 34106,
        "b41c84d6519efce267410d5e95b017366c9b5b8820a6f5878c9a893404b6defa",
        False, "SR2_FROZEN_FORMAL_HUMAN_DECISION",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE, "project_parent_relative", 86374,
        "5526d2205c5cc2da494e0263d33d2bf5a275fa9c5e18d51c3b3e1ec918b89e57",
        False, "SR2_FROZEN_FORMAL_VALIDATOR_PROVENANCE_IDENTITY_ONLY",
    ),
)
STRUCTURAL_GRAPH_BINDING = (
    STRUCTURAL_GRAPH_RELATIVE, "project_parent_relative", 142747,
    "a370deed014ec8a304b74ea0120e0c3615e72a4f391f8854c96e6a4284290ea4",
    False, "SR2_BOUND_SUPPORTING_GRAPH_FOR_STRUCTURAL_VALIDATION",
)
POLICY_BINDING = (
    SOURCE_BINDING_POLICY_RELATIVE, "repository_relative", 3704,
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    False, "PUBLISHED_SOURCE_BINDING_POLICY_V2",
)
SEMANTIC_OWNER_BINDINGS = (
    (
        DIRECT_RUNTIME_OWNER_RELATIVE, "repository_relative", 37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        False, "PUBLISHED_DIRECT_ROLE_RUNTIME_SEMANTIC_OWNER",
    ),
    (
        CANONICAL_TASK_OWNER_RELATIVE, "repository_relative", 67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        False, "PUBLISHED_CANONICAL_EXACT5_SEMANTIC_OWNER",
    ),
    (
        COMPLETED_LANE_OWNER_RELATIVE, "repository_relative", 66788,
        "2e71c3132a15f500d54430075688c37dc79469b096328943795c98a728fca7ce",
        False, "PUBLISHED_POSITIVE_INCLUDE_COMPLETED_LANE_SEMANTIC_OWNER",
    ),
)
CENSUS_BINDINGS = (
    (
        CENSUS_OWNER_RELATIVE, "repository_relative", 70328,
        "b2ae78b391f03427687e1c75c418347ea4d053e1a0a1c4a98bb6813d769a6e5b",
        False, "CURRENT_WITH_GD1_GLOBAL_CENSUS_OWNER",
    ),
    (
        CENSUS_MATRIX_RELATIVE, "repository_relative", 539590,
        "90b8038047e08b0c43537ec8738a46b741468ee7a66633a863f244039485264c",
        False, "CURRENT_WITH_GD1_GLOBAL_CENSUS_MATRIX",
    ),
    (
        CENSUS_SUMMARY_RELATIVE, "repository_relative", 18845,
        "6b96964f77321ffa07504d8a6c06b974ba6525bba2d5acb3bc3298c697d4058c",
        False, "CURRENT_WITH_GD1_GLOBAL_CENSUS_SUMMARY",
    ),
    (
        CENSUS_MANIFEST_RELATIVE, "repository_relative", 62352,
        "7d7a070b39268d2b2c6147387e516151de67cbfd67b65d69017852530d7fb78d",
        False, "CURRENT_WITH_GD1_GLOBAL_CENSUS_MANIFEST",
    ),
)

_Binding = tuple[Path, str, int, str, bool, str]
_FORBIDDEN_LIVE_IDENTITY_FIELDS = {
    "mode", "required_mode", "expected_mode", "filesystem_mode", "posix_mode",
}


class SR2IngestionSafetyError(ValueError):
    """Raised when frozen SR2 ingestion safety cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise SR2IngestionSafetyError("COVAPIE_SR2_INGESTION_V1_ERROR:" + reason)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
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
        stream, fieldnames=header, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _expect(actual: object, expected: object, reason: str) -> None:
    if type(actual) is not type(expected) or actual != expected:
        _fail(reason)


def _strict_json_loads(payload: bytes, label: str) -> dict[str, Any]:
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("JSON_BOM:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SR2IngestionSafetyError(
            "COVAPIE_SR2_INGESTION_V1_ERROR:JSON_UTF8:" + label
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
        raise SR2IngestionSafetyError(
            "COVAPIE_SR2_INGESTION_V1_ERROR:JSON_PARSE:" + label
        ) from error
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _binding_record(binding: _Binding) -> dict[str, object]:
    relative, namespace, byte_count, digest, executable, role = binding
    return {
        "path": relative.as_posix(),
        "namespace": namespace,
        "byte_count": byte_count,
        "SHA256": digest,
        "expected_executable_class": "EXECUTABLE" if executable else "NON_EXECUTABLE",
        "source_role": role,
    }


def _binding_records(bindings: Sequence[_Binding]) -> list[dict[str, object]]:
    return [_binding_record(binding) for binding in bindings]


def _normalize_overrides(value: Mapping[Path, Path] | None) -> dict[Path, Path]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        _fail("SOURCE_OVERRIDES_NOT_MAPPING")
    return {Path(key): Path(path) for key, path in value.items()}


def _resolve_binding_path(
    repo_root: Path, binding: _Binding, overrides: Mapping[Path, Path]
) -> Path:
    relative, namespace, *_rest = binding
    if relative in overrides:
        return Path(overrides[relative])
    if namespace == "repository_relative":
        return repo_root / relative
    if namespace == "project_parent_relative":
        return repo_root.parent / relative
    _fail("SOURCE_NAMESPACE_INVALID:" + relative.as_posix())


def _verify_binding(
    repo_root: Path, binding: _Binding, overrides: Mapping[Path, Path]
) -> bytes:
    relative, _namespace, byte_count, digest, executable, role = binding
    try:
        return verify_bound_source_v2(
            path=_resolve_binding_path(repo_root, binding, overrides),
            expected_byte_count=byte_count,
            expected_sha256=digest,
            label=role + ":" + relative.as_posix(),
            expected_executable=executable,
        )
    except SourceBindingPolicyV2Error as error:
        raise SR2IngestionSafetyError(
            "COVAPIE_SR2_INGESTION_V1_ERROR:SOURCE_BINDING_FAILED:"
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
        raise SR2IngestionSafetyError(
            "COVAPIE_SR2_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
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
                    raise SR2IngestionSafetyError(
                        "COVAPIE_SR2_INGESTION_V1_ERROR:"
                        "SEMANTIC_OWNER_LITERAL_INVALID:" + target.id
                    ) from error
    if set(values) != wanted:
        _fail("SEMANTIC_OWNER_LITERAL_MISSING:" + label)
    return values


def _validate_semantic_owners(payloads: Mapping[Path, bytes]) -> dict[str, object]:
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
    lane_tree = ast.parse(
        payloads[COMPLETED_LANE_OWNER_RELATIVE].decode("utf-8"),
        filename=COMPLETED_LANE_OWNER_RELATIVE.as_posix(),
    )
    lane_literals = {
        node.value for node in ast.walk(lane_tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    _expect(
        direct["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"],
        EXPECTED_ROLE_PROFILE,
        "DIRECT_ROLE_PROFILE_OWNER_DRIFT",
    )
    _expect(
        direct["DIRECT_VALID_CANONICAL_TASK_IDS_V1"],
        DIRECT_VALID_TASK_IDS,
        "DIRECT_TASK_ID_OWNER_DRIFT",
    )
    _expect(
        direct["DIRECT_PROFILE_TASK_APPLICABILITY_V1"],
        DIRECT_APPLICABILITY,
        "DIRECT_APPLICABILITY_OWNER_DRIFT",
    )
    _expect(
        canonical["EXACT3_ROLES"],
        ("scaffold", "linker", "warhead"),
        "EXACT3_ROLE_OWNER_DRIFT",
    )
    _expect(
        canonical["CANONICAL_TASKS"], CANONICAL_TASKS,
        "CANONICAL_EXACT5_OWNER_DRIFT",
    )
    if EXPECTED_COMPLETED_LANE not in lane_literals:
        _fail("PUBLISHED_POSITIVE_INCLUDE_COMPLETED_LANE_MISSING")
    return {
        "role_profile": EXPECTED_ROLE_PROFILE,
        "global_canonical_task_count": 5,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "B3_present": True,
        "sixth_task_present": False,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "completed_lane_source_bound": True,
    }


def _semantic_digest(formal: Mapping[str, Any]) -> str:
    clone = copy.deepcopy(dict(formal))
    digest = clone.pop("formal_decision_semantic_canonical_sha256", None)
    if type(digest) is not str:
        _fail("FORMAL_SEMANTIC_DIGEST_FIELD_INVALID")
    return _sha256(_canonical_json(clone))


def _expected_formal_events() -> list[dict[str, object]]:
    return [
        {
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_candidate": "SELECT_CANDIDATE_15",
            "D5_training_use": TRAINING_USE_DECISION,
            "D6_context_reference": "UNIT_LEVEL_EXACT_AUTHORIZED_D6",
            "POST_distance_angstrom": row[6],
            "POST_geometry_training_authority": False,
            "canonical_event_id": row[0],
            "cys_residue_id": "CYS:345-",
            "distance_only_inference": False,
            "event_index": index,
            "explicit_covalent_evidence": True,
            "formal_training_admitted": False,
            "ligand_asym": row[4],
            "ligand_component_id": "SR2",
            "ligand_reactive_atom": "C51",
            "model_number": 1,
            "pdb_id": row[2],
            "protein_asym": row[3],
            "protein_reactive_atom": "SG",
            "reported_POST_distance_angstrom": row[8],
            "sample_level_formal_authority": True,
            "scaleup_rank": row[1],
            "selected_connection_id": row[5],
        }
        for index, row in enumerate(EXPECTED_EVENTS)
    ]


def _expected_contexts() -> dict[str, object]:
    return {
        "context_specific_exception_count": 0,
        "contexts": [
            {
                "authorized_exceptions": [],
                "canonical_event_id": row[0],
                "cys_residue_id": "CYS:345-",
                "ligand_asym": row[4],
                "pdb_id": row[2],
                "protein_asym": row[3],
            }
            for row in EXPECTED_EVENTS
        ],
        "contexts_collapsed": False,
        "event_specific_exception_count": 0,
    }


def _expected_tasks() -> dict[str, object]:
    return {
        "B3_present": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "global_canonical_Exact5": [
            {"display_alias": alias, "semantic_name": semantic, "task_id": task_id}
            for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "global_mask_contract_modified": False,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "sample_applicable_semantic_names": [
            "warhead_only", "scaffold_only", "scaffold_plus_linker_plus_warhead",
        ],
        "sample_applicable_task_ids": [0, 3, 4],
        "sample_not_applicable_tasks": [
            {
                "reason": "not_applicable_empty_linker_redundant_with_A",
                "semantic_name": "linker_plus_warhead",
                "task_id": 1,
            },
            {
                "reason": "not_applicable_empty_non_C_fixed_context",
                "semantic_name": "scaffold_plus_warhead",
                "task_id": 2,
            },
        ],
        "sixth_task_present": False,
    }


def _validate_formal_document(formal: Mapping[str, Any]) -> None:
    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(formal.get("record_role"), FORMAL_RECORD_ROLE, "FORMAL_RECORD_ROLE_DRIFT")
    _expect(
        formal.get("formal_decision_semantic_canonical_sha256"),
        FORMAL_SEMANTIC_CANONICAL_SHA256,
        "FORMAL_SEMANTIC_DIGEST_LITERAL_DRIFT",
    )
    if _semantic_digest(formal) != FORMAL_SEMANTIC_CANONICAL_SHA256:
        _fail("FORMAL_SEMANTIC_DIGEST_RECOMPUTE_FAILED")
    for key, expected in (
        ("unsigned", False), ("approved", True), ("decision_finalized", True),
        ("human_review_completed", True), ("human_decision_created", True),
        ("formal_authority_created", True), ("formal_authority_is_human", True),
        ("machine_approval", False),
    ):
        _expect(formal.get(key), expected, "FORMAL_FINALIZATION_DRIFT:" + key)

    human = formal.get("human_authorization")
    if type(human) is not dict:
        _fail("FORMAL_HUMAN_AUTHORIZATION_INVALID")
    expected_human = {
        "D1_task_relevance": "RELEVANT",
        "D2_chemistry": "POSITIVE",
        "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
        "D4_role_candidate": "SELECT_CANDIDATE_15",
        "D5_training_use": TRAINING_USE_DECISION,
        "D6_scientific_context": EXPECTED_D6,
        "attestor_id": "fmx",
        "authorization_origin": "EXTERNAL_HUMAN_CHAT_AUTHORIZATION",
        "formal_decision_authority_is_human": True,
        "human_choices_externally_authorized": True,
        "human_selected_role_candidate_index_0based": 15,
        "human_selected_role_profile": EXPECTED_ROLE_PROFILE,
        "machine_approval_claimed": False,
        "machine_roles": ["RECORD", "VALIDATE", "FREEZE"],
        "machine_scientific_authority_created": False,
        "reviewer_id": "fmx",
        "scientific_decision_authority_source": "EXTERNAL_HUMAN_REVIEWER_AUTHORIZATION",
    }
    _expect(human, expected_human, "FORMAL_HUMAN_AUTHORIZATION_DRIFT")
    d6_bytes = EXPECTED_D6.encode("utf-8")
    if len(d6_bytes) != EXPECTED_D6_BYTE_COUNT or _sha256(d6_bytes) != EXPECTED_D6_SHA256:
        _fail("INTERNAL_D6_IDENTITY_INVALID")
    d6 = formal.get("human_approved_context")
    if type(d6) is not dict:
        _fail("FORMAL_D6_PROVENANCE_INVALID")
    for key, expected in (
        ("D6_scientific_context", EXPECTED_D6),
        ("D6_utf8_byte_count", EXPECTED_D6_BYTE_COUNT),
        ("D6_utf8_sha256", EXPECTED_D6_SHA256),
        ("D6_human_reviewed_and_accepted", True),
        ("D6_human_authorized", True),
        ("formal_decision_authority_is_human", True),
        ("machine_scientific_authority_created", False),
    ):
        _expect(d6.get(key), expected, "FORMAL_D6_PROVENANCE_DRIFT:" + key)
    _expect(
        formal.get("unit_human_decision"),
        {
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_candidate": "SELECT_CANDIDATE_15",
            "D5_training_use": TRAINING_USE_DECISION,
            "D6_scientific_context": EXPECTED_D6,
            "completed_human_review_event_count": 4,
            "exact_event_count": 4,
            "seventh_decision_present": False,
        },
        "FORMAL_UNIT_DECISION_DRIFT",
    )
    _expect(
        formal.get("identity"),
        {
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "contexts_collapsed": False,
            "distance_only_inference": False,
            "exact_event_count": 4,
            "explicit_covalent_evidence": True,
            "ligand_component_id": "SR2",
            "ligand_reactive_atom": "C51",
            "pdb_ids": ["2QLQ", "2QQ7"],
            "protein_reactive_atom": "SG",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scaleup_ranks": list(EXPECTED_RANKS),
        },
        "FORMAL_EXACT4_IDENTITY_DRIFT",
    )
    _expect(formal.get("context_preservation"), _expected_contexts(), "FORMAL_CONTEXT_DRIFT")
    _expect(
        formal.get("event_level_formal_human_decisions"),
        _expected_formal_events(),
        "FORMAL_EVENT_DECISION_OR_EVIDENCE_DRIFT",
    )
    _expect(
        formal.get("canonical_Exact5_and_sample_applicability"),
        _expected_tasks(),
        "FORMAL_CANONICAL_EXACT5_DRIFT",
    )
    role = formal.get("selected_role_partition")
    if type(role) is not dict:
        _fail("FORMAL_ROLE_INVALID")
    role_expected = {
        "D4_human_choice": "SELECT_CANDIDATE_15",
        "L": [], "S": list(SCAFFOLD_ROLE), "W": list(WARHEAD_ROLE),
        "W_L_S_counts": [9, 0, 18],
        "applicable_task_ids": [0, 3, 4],
        "boundary_bonds": list(BOUNDARY_BONDS),
        "canonical_role_partition_sample_authority": True,
        "heavy_atom_count": 27,
        "human_selected": True,
        "machine_recommended": False,
        "machine_selected": False,
        "reusable_role_rule_created": False,
        "role_authority_scope": ROLE_AUTHORITY_SCOPE,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "selected_candidate_index_0based": 15,
    }
    for key, expected in role_expected.items():
        _expect(role.get(key), expected, "FORMAL_ROLE_DRIFT:" + key)
    pair = formal.get("reactive_pair_authority")
    if type(pair) is not dict:
        _fail("FORMAL_PAIR_AUTHORITY_INVALID")
    pair_expected = {
        "D3_human_choice": "CONFIRM_OBSERVED_PAIR",
        "EGFR_C797_event_specific_authority": False,
        "all_EGFR_covalent_inhibitors_use_C51_authority": False,
        "all_SR2_uses_C51_authority": False,
        "all_engineered_Src_surrogates_use_C51_authority": False,
        "authority_scope": PAIR_AUTHORITY_SCOPE,
        "cross_structure_regiochemistry_generalization": False,
        "ligand_reactive_atom": "C51",
        "protein_reactive_atom": "SG",
        "reactive_pair_sample_authority": True,
        "reusable_pair_rule_created": False,
    }
    _expect(pair, pair_expected, "FORMAL_PAIR_AUTHORITY_DRIFT")
    _expect(
        formal.get("task_relevance_authority"),
        {
            "D1_human_choice": "RELEVANT",
            "formal_training_admission_created_by_D1": False,
            "task_relevance_sample_authority": True,
        },
        "FORMAL_TASK_RELEVANCE_AUTHORITY_DRIFT",
    )
    _expect(
        formal.get("chemistry_authority_boundary"),
        {
            "D2_human_choice": "POSITIVE",
            "positive_chemistry_sample_authority": True,
            "reaction_family_authority_created": False,
            "reusable_chemistry_authority_created": False,
            "reusable_chemistry_rule_created": False,
            "warhead_rule_authority_created": False,
            "warhead_type_authority_created": False,
        },
        "FORMAL_CHEMISTRY_AUTHORITY_DRIFT",
    )
    _expect(
        formal.get("PRE_POST_boundary"),
        {
            "POST_to_PRE_copy_performed": False,
            "PRE_coordinates_authority": False,
            "PRE_geometry_authority": False,
            "PRE_mapping_count_per_event": 0,
            "PRE_mapping_status": PRE_MAPPING_STATUS,
            "PRE_reconstruction_performed": False,
            "PRE_source_graph_count_per_event": 1,
            "PRE_source_graph_present": True,
            "PRE_status": PRE_STATUS,
            "PRE_topology_authority": False,
            "PRE_zero_fill_performed": False,
            "leaving_group_inferred": False,
            "pre_reaction_bond_edit_inferred": False,
            "reagent_inferred": False,
            "supporting_PRE_source_graph_count_per_event": 1,
        },
        "FORMAL_PRE_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("POST_evidence_boundary"),
        {
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
            "POST_source_evidence_available": True,
            "POST_source_evidence_count": 4,
            "distance_only_inference": False,
            "explicit_covalent_evidence": True,
            "observed_distances_angstrom": [row[6] for row in EXPECTED_EVENTS],
        },
        "FORMAL_POST_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("training_use_boundary"),
        {
            "D5_human_choice": TRAINING_USE_DECISION,
            "READY_FOR_TRAINING": False,
            "current_runtime_model_usable": False,
            "feature_semantics_finalized": False,
            "formal_split_authority": False,
            "formal_training_admitted": False,
            "future_training_admission_candidate": True,
            "human_training_excluded": False,
            "human_training_use_disposition": TRAINING_USE_DECISION,
            "human_training_use_disposition_authority": True,
            "parameter_update_authorization": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
        },
        "FORMAL_TRAINING_BOUNDARY_DRIFT",
    )
    engineered = formal.get("engineered_surrogate_caveat")
    expected_engineered = {
        "EGFR_C797_event_specific_authority": False,
        "EGFR_T790M_event_specific_structure_authority": False,
        "ENGINEERED_SURROGATE_CONTEXT": True,
        "TARGET_DIRECTED_MEDICINAL_COVALENT_CONTEXT": True,
        "cross_target_transfer_authority": False,
        "formal_D5_INCLUDE_preserves_engineered_surrogate_limitation": True,
        "native_Src_S345_authority": False,
        "native_Src_site_training_authority": False,
        "per_structure_context": [
            {"engineered_context": "engineered Src S345C", "pdb_id": "2QLQ"},
            {"engineered_context": "engineered Src T338M/S345C", "pdb_id": "2QQ7"},
        ],
    }
    _expect(engineered, expected_engineered, "FORMAL_ENGINEERED_CAVEAT_DRIFT")
    authority = formal.get("authority_boundary")
    if type(authority) is not dict:
        _fail("FORMAL_AUTHORITY_BOUNDARY_INVALID")
    required_true = (
        "canonical_role_partition_sample_authority", "formal_authority_created",
        "formal_authority_is_human", "human_decision_created", "human_review_completed",
        "human_training_use_disposition_authority", "positive_chemistry_sample_authority",
        "reactive_pair_sample_authority", "role_profile_task_applicability_sample_authority",
        "sample_level_formal_human_decision_authority_created",
        "task_relevance_sample_authority",
    )
    required_false = (
        "POST_geometry_training_authority", "PRE_geometry_authority",
        "PRE_topology_authority", "READY_FOR_TRAINING", "authoritative_task_labels_created",
        "chemical_warhead_reusable_authority", "cross_structure_regiochemistry_generalization",
        "current_runtime_model_usable", "event_task_label_rows_materialized",
        "formal_split_authority", "formal_training_admitted", "machine_approval",
        "machine_scientific_authority_created", "parameter_update_authorization",
        "reaction_family_authority", "reusable_chemistry_authority",
        "reusable_pair_authority", "reusable_role_authority", "tensor_target_created",
        "training_admission_created", "training_materialization_allowed", "training_started",
        "warhead_rule_authority", "warhead_type_authority",
    )
    for key in required_true:
        _expect(authority.get(key), True, "FORMAL_REQUIRED_AUTHORITY_MISSING:" + key)
    for key in required_false:
        _expect(authority.get(key), False, "FORMAL_UNAUTHORIZED_AUTHORITY:" + key)
    _expect(
        formal.get("current_published_census_preformal_provenance"),
        {
            "HEAD": BASELINE_COMMIT,
            "census_modified_by_this_step": False,
            "chemistry_disposition": "UNRESOLVED",
            "current_global_status": "CURRENTLY_UNREVIEWED",
            "current_review_status": "CURRENTLY_UNREVIEWED",
            "event_count": 4,
            "formal_training_admitted": False,
            "human_review_completed": False,
            "task_relevance_disposition": "UNRESOLVED",
            "training_use_disposition": "UNRESOLVED",
        },
        "FORMAL_CURRENT_CENSUS_PROVENANCE_DRIFT",
    )
    lifecycle = formal.get("validator_lifecycle")
    if type(lifecycle) is not dict:
        _fail("FORMAL_VALIDATOR_LIFECYCLE_INVALID")
    lifecycle_expected = {
        "baseline_commit": BASELINE_COMMIT,
        "validator_baseline_locked_creation_and_self_test_only": True,
        "validator_postbaseline_runtime_dependency_allowed": False,
        "future_ingestion_must_bind_formal_JSON_and_validator_bytes_SHA256": True,
        "future_ingestion_must_independently_validate_formal_semantics": True,
        "future_ingestion_must_not_execute_this_validator_after_HEAD_advances": True,
    }
    _expect(lifecycle, lifecycle_expected, "FORMAL_VALIDATOR_LIFECYCLE_DRIFT")
    operation = formal.get("operation_boundary")
    if type(operation) is not dict:
        _fail("FORMAL_OPERATION_BOUNDARY_INVALID")
    for key in (
        "CENSUS_REFRESH", "COMMIT", "INGESTION_PERFORMED", "PUSH", "QUEUE_REFRESH",
        "READY_FOR_TRAINING", "RECONCILIATION", "TRAINING_STARTED", "backward",
        "loader", "loss", "model_forward", "optimizer", "parameter_update",
        "repository_modified", "task_label_materialization", "tensorization",
        "training_admission",
    ):
        _expect(operation.get(key), False, "FORMAL_OPERATION_BOUNDARY_DRIFT:" + key)
    identity = formal.get("semantic_identity_contract")
    if type(identity) is not dict:
        _fail("FORMAL_SEMANTIC_IDENTITY_INVALID")
    for key in ("PID_present", "hostname_present", "machine_absolute_path_present",
                "random_UUID_present", "timestamp_present"):
        _expect(identity.get(key), False, "FORMAL_DYNAMIC_IDENTITY_PRESENT:" + key)


def _connected(atom_ids: Sequence[str], bonds: Sequence[tuple[str, str, str]]) -> bool:
    if not atom_ids:
        return True
    allowed = set(atom_ids)
    adjacency = {atom: set() for atom in allowed}
    for left, right, _order in bonds:
        if left in allowed and right in allowed:
            adjacency[left].add(right)
            adjacency[right].add(left)
    seen = {atom_ids[0]}
    pending = [atom_ids[0]]
    while pending:
        current = pending.pop()
        for neighbor in adjacency[current] - seen:
            seen.add(neighbor)
            pending.append(neighbor)
    return seen == allowed


def _validate_structural_graph(payload: bytes) -> dict[str, object]:
    graph = _strict_json_loads(payload, "SR2_BOUND_STRUCTURAL_GRAPH")
    expected_scalars = {
        "schema_version": "covapie_sr2_graph_and_role_candidates_v1",
        "record_role": "MACHINE_GRAPH_EVIDENCE_AND_UNSELECTED_GRAPH_CANDIDATES_ONLY",
        "package_role": "UNSIGNED_NON_AUTHORITATIVE_MACHINE_REVIEW_AID_PREPARATION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "SR2",
        "heavy_atom_count": 27,
        "heavy_bond_count": 29,
        "connected_component_count": 1,
        "canonical_heavy_graph_digest": (
            "6c286d272d3847bddd75bc2c14d4dc9a0cf11eb249b3f35bfba29ccda629d1e6"
        ),
        "candidate_inventory_truncated": False,
        "full_candidate_count": 24,
        "retained_candidate_count": 8,
        "DIRECT_candidate_count": 8,
        "STRICT_candidate_count": 16,
        "human_selected": False,
        "machine_selected": False,
        "machine_recommended_candidate": None,
        "selected_candidate": None,
        "reaction_family_authority": False,
        "reusable_chemistry_authority": False,
        "reusable_pair_authority": False,
        "reusable_role_authority": False,
        "warhead_rule_authority": False,
        "warhead_type_authority": False,
    }
    for key, expected in expected_scalars.items():
        _expect(graph.get(key), expected, "STRUCTURAL_GRAPH_DRIFT:" + key)
    atoms = graph.get("heavy_atoms")
    bonds = graph.get("heavy_bonds")
    if type(atoms) is not list or type(bonds) is not list:
        _fail("STRUCTURAL_GRAPH_ATOMS_OR_BONDS_INVALID")
    atom_ids = tuple(row.get("atom_id") for row in atoms if type(row) is dict)
    normalized_bonds = tuple(
        (row.get("atom_id_1"), row.get("atom_id_2"), row.get("bond_order"))
        for row in bonds if type(row) is dict
    )
    if atom_ids != HEAVY_ATOMS or normalized_bonds != HEAVY_BONDS:
        _fail("STRUCTURAL_GRAPH_EXACT27_OR_BONDS_DRIFT")
    inventory = graph.get("full_candidate_inventory")
    if type(inventory) is not list or len(inventory) != 24:
        _fail("STRUCTURAL_GRAPH_FULL_CANDIDATE_INVENTORY_INVALID")
    candidate = inventory[15]
    if type(candidate) is not dict:
        _fail("STRUCTURAL_GRAPH_CANDIDATE15_INVALID")
    candidate_expected = {
        "index_0based": 15,
        "profile": EXPECTED_ROLE_PROFILE,
        "W": list(WARHEAD_ROLE), "L": [], "S": list(SCAFFOLD_ROLE),
        "boundary_bonds": list(BOUNDARY_BONDS),
        "disjoint": True, "exhaustive": True, "W_connected": True,
        "L_connected_or_empty": True, "S_connected": True,
        "reactive_atom_in_W": True, "applicable_task_ids": [0, 3, 4],
        "candidate_index_is_ranking": False,
        "candidate_index_is_recommendation": False,
        "human_selected": False, "machine_selected": False,
        "machine_recommended": False,
    }
    for key, expected in candidate_expected.items():
        _expect(candidate.get(key), expected, "STRUCTURAL_GRAPH_CANDIDATE15_DRIFT:" + key)
    sets = (set(WARHEAD_ROLE), set(LINKER_ROLE), set(SCAFFOLD_ROLE))
    if (
        sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]
        or set().union(*sets) != set(atom_ids)
        or not _connected(WARHEAD_ROLE, normalized_bonds)  # type: ignore[arg-type]
        or not _connected(LINKER_ROLE, normalized_bonds)  # type: ignore[arg-type]
        or not _connected(SCAFFOLD_ROLE, normalized_bonds)  # type: ignore[arg-type]
    ):
        _fail("STRUCTURAL_GRAPH_PARTITION_OR_CONNECTIVITY_INVALID")
    cross_role = [
        bond for bond in normalized_bonds
        if (bond[0] in sets[0] and bond[1] in sets[2])
        or (bond[1] in sets[0] and bond[0] in sets[2])
    ]
    if cross_role != [("C9", "N11", "SING")]:
        _fail("STRUCTURAL_GRAPH_BOUNDARY_INVALID")
    return {
        "atom_ids": atom_ids,
        "bonds": normalized_bonds,
        "Exact27_count": 27,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "missing_atom_ids": [], "extra_atom_ids": [],
        "W_connected": True, "L_connected_or_empty": True, "S_connected": True,
        "C51_in_W": True,
        "boundary": "C9-N11 SING S-W",
    }


def _validate_published_direct_runtime(
    structural: Mapping[str, object],
) -> dict[str, object]:
    runtime = importlib.import_module(
        "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"
    )
    result = runtime.validate_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE,
        retained_heavy_atoms=structural["atom_ids"],
        scaffold_atoms=SCAFFOLD_ROLE,
        linker_atoms=LINKER_ROLE,
        warhead_atoms=WARHEAD_ROLE,
        reactive_atom_id="C51",
        direct_scaffold_warhead_boundaries=(("C9", "N11", "SING"),),
        explicit_graph_bonds=structural["bonds"],
    )
    boundary = result.direct_scaffold_warhead_boundary
    if (
        result.role_profile != EXPECTED_ROLE_PROFILE or result.valid is not True
        or tuple(result.reasons) != () or result.scaffold_count != 18
        or result.linker_count != 0 or result.warhead_count != 9
        or result.scaffold_linker_boundary_applicable is not False
        or result.linker_warhead_boundary_applicable is not False
        or result.direct_scaffold_warhead_boundary_applicable is not True
        or boundary is None or boundary.boundary_valid is not True
        or boundary.scaffold_atom_id != "C9" or boundary.warhead_atom_id != "N11"
        or boundary.bond_order != "SING"
    ):
        _fail("PUBLISHED_DIRECT_RUNTIME_VALIDATION_FAILED")
    return {
        "validator": "validate_role_profile_v1", "valid": True, "reasons": [],
        "profile": EXPECTED_ROLE_PROFILE,
        "scaffold_count": 18, "linker_count": 0, "warhead_count": 9,
        "applicable_task_ids": [0, 3, 4],
        "direct_scaffold_warhead_boundary_applicable": True,
        "scaffold_linker_boundary_applicable": False,
        "linker_warhead_boundary_applicable": False,
        "direct_scaffold_warhead_boundary": {
            "scaffold_atom_id": "C9", "warhead_atom_id": "N11",
            "bond_order": "SING", "boundary_valid": True,
        },
    }


def _current_census_boundary(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    summary = _strict_json_loads(payloads[CENSUS_SUMMARY_RELATIVE], "CURRENT_CENSUS_SUMMARY")
    _strict_json_loads(payloads[CENSUS_MANIFEST_RELATIVE], "CURRENT_CENSUS_MANIFEST")
    try:
        rows = list(csv.DictReader(io.StringIO(payloads[CENSUS_MATRIX_RELATIVE].decode("utf-8"))))
    except UnicodeDecodeError as error:
        raise SR2IngestionSafetyError(
            "COVAPIE_SR2_INGESTION_V1_ERROR:CURRENT_CENSUS_UTF8_INVALID"
        ) from error
    if len(rows) != 1000 or len({row.get("canonical_event_id") for row in rows}) != 1000:
        _fail("CURRENT_CENSUS_UNIVERSE_DRIFT")
    target = [row for row in rows if row.get("canonical_event_id") in set(EXPECTED_EVENT_IDS)]
    unit = [row for row in rows if row.get("review_unit_id") == EXPECTED_REVIEW_UNIT_ID]
    if (
        len(target) != 4 or len(unit) != 4
        or tuple(row.get("canonical_event_id") for row in target) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in target) != EXPECTED_RANKS
        or {row.get("canonical_event_id") for row in unit} != set(EXPECTED_EVENT_IDS)
    ):
        _fail("CURRENT_CENSUS_SR2_EXACT4_DRIFT")
    prior = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false",
        "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "structurally_applicable_task_ids_json": "null",
    }
    for row in target:
        if any(row.get(key) != value for key, value in prior.items()):
            _fail("CURRENT_CENSUS_SR2_PRIOR_STATE_DRIFT")
    human = summary.get("human_review")
    if type(human) is not dict:
        _fail("CURRENT_CENSUS_HUMAN_REVIEW_COUNTS_MISSING")
    expected_counts = {
        "completed_positive_event_count": 111,
        "completed_positive_unit_count": 17,
        "completed_event_count": 139,
        "completed_unit_count": 22,
        "unreviewed_event_count": 199,
        "unreviewed_unit_count": 109,
    }
    for key, expected in expected_counts.items():
        _expect(human.get(key), expected, "CURRENT_CENSUS_COUNT_DRIFT:" + key)
    exact5 = summary.get("canonical_exact5")
    if type(exact5) is not dict:
        _fail("CURRENT_CENSUS_EXACT5_MISSING")
    for key, expected in (("task_count", 5), ("B3_present", True),
                          ("sixth_task_present", False)):
        _expect(exact5.get(key), expected, "CURRENT_CENSUS_EXACT5_DRIFT:" + key)
    return {
        **expected_counts,
        "SR2_current_global_status": "CURRENTLY_UNREVIEWED",
        "SR2_current_review_status": "CURRENTLY_UNREVIEWED",
        "SR2_human_review_completed": False,
        "SR2_event_count": 4,
        "SR2_chemistry_disposition": "UNRESOLVED",
        "SR2_task_relevance_disposition": "UNRESOLVED",
        "SR2_training_use_disposition": "UNRESOLVED",
        "SR2_formal_training_admitted": False,
        "reconciliation_performed": False,
        "current_census_changed": False,
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
    """Bind and independently validate frozen SR2 authority and owners."""

    repo_root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    allowed = {
        POLICY_BINDING[0], STRUCTURAL_GRAPH_BINDING[0],
        *(binding[0] for binding in FORMAL_BINDINGS),
        *(binding[0] for binding in SEMANTIC_OWNER_BINDINGS),
        *(binding[0] for binding in CENSUS_BINDINGS),
    }
    if set(overrides) - allowed:
        _fail("SOURCE_OVERRIDE_NOT_AUTHORIZED")
    _verify_binding(repo_root, POLICY_BINDING, overrides)
    formal_payloads = _verify_bindings(repo_root, FORMAL_BINDINGS, overrides)
    semantic_payloads = _verify_bindings(repo_root, SEMANTIC_OWNER_BINDINGS, overrides)
    structural_payload = _verify_binding(repo_root, STRUCTURAL_GRAPH_BINDING, overrides)
    census_payloads = _verify_bindings(repo_root, CENSUS_BINDINGS, overrides)
    formal = _strict_json_loads(
        formal_payloads[FORMAL_DECISION_RELATIVE], "SR2_FROZEN_FORMAL_DECISION"
    )
    _validate_formal_document(formal)
    semantic_contract = _validate_semantic_owners(semantic_payloads)
    structural_validation = _validate_structural_graph(structural_payload)
    runtime_validation = _validate_published_direct_runtime(structural_validation)
    census_boundary = _current_census_boundary(census_payloads)
    return {
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "structural_graph_binding": _binding_record(STRUCTURAL_GRAPH_BINDING),
        "source_binding_policy_binding": _binding_record(POLICY_BINDING),
        "semantic_owner_bindings": _binding_records(SEMANTIC_OWNER_BINDINGS),
        "current_census_bindings": _binding_records(CENSUS_BINDINGS),
        "semantic_contract": semantic_contract,
        "structural_validation": {
            key: value for key, value in structural_validation.items()
            if key not in {"atom_ids", "bonds"}
        },
        "published_DIRECT_runtime_validation": runtime_validation,
        "current_census_boundary": census_boundary,
        "formal_semantics_independently_validated": True,
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_executed": False,
        "formal_validator_subprocess_called": False,
        "formal_validator_runtime_dependency": False,
        "formal": formal,
    }


def _metadata_only_boundary() -> dict[str, object]:
    return {
        "metadata_only": True,
        "dataset_mutated": False,
        "training_dataset_changed": False,
        "tensorization_performed": False,
        "loader_modified": False,
        "batch_modified": False,
        "model_forward": False,
        "loss": False,
        "backward": False,
        "optimizer": False,
        "parameter_update": False,
        "training": False,
    }


def _chemistry_boundary() -> dict[str, object]:
    return {
        "task_relevance": "RELEVANT",
        "task_relevance_human_authority": True,
        "human_task_relevance_decision": "RELEVANT",
        "task_relevance_human_authoritative": True,
        "chemistry": "POSITIVE",
        "chemistry_known_positive": True,
        "chemistry_human_authority": True,
        "human_chemistry_decision": "POSITIVE",
        "chemistry_human_authoritative": True,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "distance_only_rejection": False,
    }


def _pair_boundary() -> dict[str, object]:
    return {
        "reactive_pair_human_decision_available": True,
        "reactive_pair_human_authoritative": True,
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C51",
        "pair_authority_scope": PAIR_AUTHORITY_SCOPE,
        "sample_pair_authority": True,
        "reusable_pair_rule_created": False,
        "cross_structure_regiochemistry_generalization": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "formal_event_training_use_decision": TRAINING_USE_DECISION,
        "event_training_use_human_decision_available": True,
        "training_use_allowed": True,
        "human_training_excluded": False,
        "training_exclusion_reason": "",
        "candidate_for_future_training_admission": True,
        "future_training_admission_candidate": True,
        "future_training_admission_status": FUTURE_STATUS,
        "future_training_admission_inclusion_reason": FUTURE_INCLUSION_REASON,
        "future_training_admission_candidate_is_not_training_admission": True,
        "D5_INCLUDE_DOES_NOT_GRANT_TRAINING_ADMISSION": True,
        "D5_INCLUDE_DOES_NOT_GRANT_PARAMETER_UPDATE_AUTHORIZATION": True,
        "training_admitted": False,
        "formal_training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed_now": False,
        "training_materialization_allowed": False,
        "tensor_target_created": False,
        "model_supervision_usable": False,
        "training_mask_targets_available_now": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "READY_FOR_TRAINING": False,
    }


def _pre_boundary() -> dict[str, object]:
    return {
        "supporting_PRE_source_graph_count_per_event": 1,
        "PRE_source_graph_present": True,
        "PRE_source_graph_count_per_event": 1,
        "PRE_mapping_count_per_event": 0,
        "PRE_mapping_status": PRE_MAPPING_STATUS,
        "PRE_status": PRE_STATUS,
        "PRE_topology_authority": False,
        "PRE_geometry_authority": False,
        "PRE_coordinates_authority": False,
        "PRE_training_target": False,
        "PRE_geometry_training_label_available_now": False,
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
    }


def _engineered_surrogate_caveat() -> dict[str, object]:
    return {
        "ENGINEERED_SURROGATE_CONTEXT": True,
        "TARGET_DIRECTED_MEDICINAL_COVALENT_CONTEXT": True,
        "per_structure_context": [
            {"pdb_id": "2QLQ", "engineered_context": "engineered Src S345C"},
            {
                "pdb_id": "2QQ7",
                "engineered_context": "engineered Src T338M/S345C",
            },
        ],
        "formal_D5_INCLUDE_preserves_engineered_surrogate_limitation": True,
        "native_Src_S345_authority": False,
        "native_Src_site_training_authority": False,
        "EGFR_C797_event_specific_authority": False,
        "EGFR_T790M_event_specific_structure_authority": False,
        "cross_target_transfer_authority": False,
    }


def _reusable_boundary() -> dict[str, object]:
    return {
        "reusable_chemistry_authority": False,
        "reusable_pair_authority": False,
        "reusable_role_authority": False,
        "reaction_family_authority": False,
        "warhead_rule_authority": False,
        "warhead_type_authority": False,
        "reaction_family_training_class_target_available": False,
        "warhead_rule_training_class_target_available": False,
        "warhead_type_target_available": False,
        "reusable_authority_label_available": False,
        "reusable_training_target_created": False,
    }


def _authority_boundary() -> dict[str, object]:
    return {
        "authority_source": AUTHORITY_SOURCE,
        "pair_authority_scope": PAIR_AUTHORITY_SCOPE,
        "role_authority_scope": ROLE_AUTHORITY_SCOPE,
        "scientific_sample_authority_available": True,
        "training_eligibility": False,
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
        "new_scientific_authority_created_by_ingestion": False,
        "formal_semantics_independently_validated": True,
        "frozen_formal_validator_imported": False,
        "frozen_formal_validator_executed": False,
        "frozen_formal_validator_subprocess_called": False,
        "reconciliation_performed": False,
        "current_census_changed": False,
        "census_refreshed": False,
        "queue_updated": False,
        **_metadata_only_boundary(),
        "training_started": False,
        "ready_for_training": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "Step12D": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
    }


def _canonical_task_contract() -> dict[str, object]:
    applicability = [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "structurally_applicable": applicable,
            "reason": reason,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "training_mask_target_available_now": False,
        }
        for task_id, semantic, alias, applicable, reason in DIRECT_APPLICABILITY
    ]
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
        "sixth_task": False,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "direct_profile_applicable_task_count": 3,
        "task_applicability": applicability,
        "task_applicability_determined": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "structural_applicability_does_not_create_training_targets": True,
    }


def _role_projection(runtime_validation: Mapping[str, object]) -> dict[str, object]:
    return {
        "D4_human_choice": "SELECT_CANDIDATE_15",
        "selected_candidate_index_0based": 15,
        "profile": EXPECTED_ROLE_PROFILE,
        "W": list(WARHEAD_ROLE),
        "L": [],
        "S": list(SCAFFOLD_ROLE),
        "W_L_S_counts": [9, 0, 18],
        "boundary_bonds": list(BOUNDARY_BONDS),
        "Exact27_count": 27,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "missing_atom_ids": [],
        "extra_atom_ids": [],
        "W_connected": True,
        "L_connected_or_empty": True,
        "S_connected": True,
        "C51_in_W": True,
        "published_DIRECT_runtime_validation": dict(runtime_validation),
        "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True,
        "sample_role_authority": True,
        "reusable_role_authority": False,
        "authority_scope": ROLE_AUTHORITY_SCOPE,
    }


def _event_projection(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "canonical_event_id": row[0],
        "scaleup_rank": row[1],
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": row[2],
        "model_number": 1,
        "protein_chain_or_asym": row[3],
        "cys_residue_id": "CYS:345-",
        "protein_altloc": None,
        "ligand_component_id": "SR2",
        "ligand_chain_or_asym": row[4],
        "ligand_altloc": None,
        "selected_connection_id": row[5],
        "POST_distance_angstrom": row[6],
        "POST_distance_frozen_lexeme": row[7],
        "reported_POST_distance_angstrom": row[8],
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "authority_source": AUTHORITY_SOURCE,
        "human_review_completed": True,
        "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True,
        "selected_candidate_index_0based": 15,
        "role_profile": EXPECTED_ROLE_PROFILE,
        **_chemistry_boundary(),
        **_pair_boundary(),
        **_training_boundary(),
        **_pre_boundary(),
        **_post_boundary(),
        **_reusable_boundary(),
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    runtime = bound["published_DIRECT_runtime_validation"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "SR2_FROZEN_HUMAN_AUTHORITY_METADATA_ONLY_PROJECTION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "completed_lane_source_bound": True,
        "scientific_sample_authority_available": True,
        "training_eligibility": False,
        "human_review_completed": True,
        "task_relevance": "RELEVANT",
        "chemistry": "POSITIVE",
        "human_training_excluded": False,
        "future_training_admission_candidate": True,
        "formal_semantic_canonical_sha256": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "structural_graph_binding": bound["structural_graph_binding"],
        "source_binding_policy_binding": bound["source_binding_policy_binding"],
        "semantic_owner_bindings": bound["semantic_owner_bindings"],
        "human_authorization": {
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_AUTHORIZATION",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "formal_decision_authority_is_human": True,
            "machine_approval": False,
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_candidate": "SELECT_CANDIDATE_15",
            "D5_training_use": TRAINING_USE_DECISION,
            "D6_scientific_context": EXPECTED_D6,
        },
        "D6_provenance": {
            "D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT,
            "D6_utf8_sha256": EXPECTED_D6_SHA256,
            "D6_human_reviewed_and_accepted": True,
            "D6_human_authorized": True,
            "D6_human_authored": False,
            "formal_decision_authority_is_human": True,
            "machine_scientific_authority_created": False,
        },
        "context_preservation": _expected_contexts(),
        "events": [_event_projection(row) for row in EXPECTED_EVENTS],
        "reactive_pair_authority": _pair_boundary(),
        "chemistry_boundary": _chemistry_boundary(),
        "selected_role_partition": _role_projection(runtime),  # type: ignore[arg-type]
        "structural_validation": bound["structural_validation"],
        "canonical_task_contract": _canonical_task_contract(),
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": {
            **_post_boundary(),
            "POST_source_evidence_count": 4,
            "observed_distances_angstrom": [row[6] for row in EXPECTED_EVENTS],
        },
        "engineered_surrogate_caveat": _engineered_surrogate_caveat(),
        "training_boundary": _training_boundary(),
        "reusable_authority_boundary": _reusable_boundary(),
        "current_census_boundary": bound["current_census_boundary"],
        "metadata_only_boundary": _metadata_only_boundary(),
        "authority_boundary": _authority_boundary(),
    }


# Modern GD1 ingestion matrix fields are retained wherever they are generic.
# Its GD1-only bound-preQ0/4FGC columns are intentionally not repurposed for
# SR2; the engineered-surrogate caveat remains in rich JSON metadata.
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
    "task_domain_negative", "distance_only_rejection",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "protein_reactive_atom", "ligand_reactive_atom", "pair_authority_scope",
    "reusable_pair_rule_created", "cross_structure_regiochemistry_generalization",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "selected_candidate_index_0based", "role_profile", "warhead_atoms_json",
    "linker_atoms_json", "scaffold_atoms_json", "W_L_S_counts_json",
    "boundary_bonds_json", "Exact27_count", "reusable_role_authority",
    "global_canonical_task_count", "B3_present", "sixth_task",
    "canonical_task_applicability_json", "direct_profile_applicable_task_ids_json",
    "task_applicability_determined", "authoritative_task_labels_created",
    "event_task_label_rows_materialized", "formal_event_training_use_decision",
    "event_training_use_human_decision_available", "training_use_allowed",
    "human_training_excluded", "training_exclusion_reason",
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
    "new_human_authority_created_by_ingestion",
    "metadata_only", "dataset_mutated", "training_dataset_changed",
    "tensorization_performed", "loader_modified", "batch_modified",
    "model_forward", "loss", "backward", "optimizer", "parameter_update",
    "training",
)


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    applicability = snapshot["canonical_task_contract"]["task_applicability"]
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        row: dict[str, object] = {
            key: "true" if value is True else "false" if value is False else value
            for key, value in event.items() if key in MATRIX_HEADER
        }
        row.update(
            {
                "scaleup_rank": str(event["scaleup_rank"]),
                "model_number": "1",
                "protein_altloc": "",
                "ligand_altloc": "",
                "pair_authority_scope": PAIR_AUTHORITY_SCOPE,
                "warhead_atoms_json": _json_cell(list(WARHEAD_ROLE)),
                "linker_atoms_json": "[]",
                "scaffold_atoms_json": _json_cell(list(SCAFFOLD_ROLE)),
                "W_L_S_counts_json": "[9,0,18]",
                "boundary_bonds_json": _json_cell(list(BOUNDARY_BONDS)),
                "Exact27_count": "27",
                "reusable_role_authority": "false",
                "global_canonical_task_count": "5",
                "B3_present": "true",
                "sixth_task": "false",
                "canonical_task_applicability_json": _json_cell(applicability),
                "direct_profile_applicable_task_ids_json": "[0,3,4]",
                "task_applicability_determined": "true",
                "authoritative_task_labels_created": "false",
                "event_task_label_rows_materialized": "false",
                "projection_of_frozen_formal_human_authority": "true",
                "new_human_authority_created_by_ingestion": "false",
                **{
                    key: "true" if value is True else "false"
                    for key, value in _metadata_only_boundary().items()
                },
            }
        )
        if set(row) != set(MATRIX_HEADER):
            _fail("INTERNAL_MATRIX_ROW_SHAPE_INVALID")
        rows.append(row)
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "review_unit": "SR2",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "completed_lane_source_bound": True,
        "ingested_event_count": 4,
        "human_completed_event_count": 4,
        "task_relevant_event_count": 4,
        "positive_chemistry_event_count": 4,
        "sample_pair_authority_event_count": 4,
        "role_authority_event_count": 4,
        "DIRECT_event_count": 4,
        "training_use_INCLUDE_event_count": 4,
        "human_training_excluded_event_count": 0,
        "training_use_allowed_event_count": 4,
        "future_training_admission_candidate_count": 4,
        "formal_training_admitted_count": 0,
        "training_admission_created_event_count": 0,
        "training_materialization_allowed_event_count": 0,
        "tensor_target_created_event_count": 0,
        "model_supervision_usable_event_count": 0,
        "canonical_Exact5_applicable_event_counts": {
            "warhead_only": 4,
            "linker_plus_warhead": 0,
            "scaffold_plus_warhead": 0,
            "scaffold_only": 4,
            "scaffold_plus_linker_plus_warhead": 4,
        },
        "applicable_task_set_counts": {"[0,3,4]": 4},
        "PRE_source_graph_present_event_count": 4,
        "PRE_source_graph_count_per_event": 1,
        "PRE_mapping_available_event_count": 0,
        "PRE_training_target_event_count": 0,
        "PRE_authority_event_count": 0,
        "POST_source_evidence_event_count": 4,
        "POST_training_authority_event_count": 0,
        "POST_training_target_event_count": 0,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "reusable_chemistry_authority_event_count": 0,
        "reusable_pair_authority_event_count": 0,
        "reusable_role_authority_event_count": 0,
        "reaction_family_target_count": 0,
        "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task": False,
        "engineered_surrogate_caveat": _engineered_surrogate_caveat(),
        "metadata_only_boundary": _metadata_only_boundary(),
        "SR2_COMPLETED_DECISION_INGESTED": True,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "current_census_changed": False,
        "QUEUE_REFRESH": False,
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "authority_boundary": _authority_boundary(),
    }


def _validate_text_payload(label: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes or not payload or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload
        or b"\r" in payload or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail("TEXT_PAYLOAD_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SR2IngestionSafetyError(
            "COVAPIE_SR2_INGESTION_V1_ERROR:TEXT_UTF8_INVALID:" + label
        ) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TEXT_TRAILING_WHITESPACE:" + label)


def _reject_dynamic_or_forbidden_metadata(value: object, path: str = "root") -> None:
    if type(value) is dict:
        for key, item in value.items():  # type: ignore[union-attr]
            if type(key) is not str:
                _fail("NON_STRING_METADATA_KEY:" + path)
            lowered = key.lower()
            if key in _FORBIDDEN_LIVE_IDENTITY_FIELDS or any(
                token in lowered for token in ("timestamp", "hostname", "random_uuid")
            ) or lowered in {"pid", "process_id"}:
                _fail("DYNAMIC_METADATA_FIELD:" + path + "." + key)
            _reject_dynamic_or_forbidden_metadata(item, path + "." + key)
    elif type(value) is list:
        for index, item in enumerate(value):  # type: ignore[arg-type]
            _reject_dynamic_or_forbidden_metadata(item, path + f"[{index}]")
    elif type(value) is str:
        text = value  # type: ignore[assignment]
        if text.startswith(("/", "\\\\")) or (
            len(text) >= 3 and text[1:3] in {":\\", ":/"}
        ):
            _fail("ABSOLUTE_MACHINE_PATH:" + path)


def _candidate_source_bindings(repo_root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for relative, role in (
        (SOURCE_RELATIVE, "production_owner"),
        (CHECKER_RELATIVE, "fail_closed_checker"),
        (TEST_RELATIVE, "targeted_test_contract"),
    ):
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise SR2IngestionSafetyError(
                "COVAPIE_SR2_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
                + relative.as_posix()
            ) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("CANDIDATE_SOURCE_NOT_REGULAR:" + relative.as_posix())
        try:
            verify_bound_source_v2(
                path=path,
                expected_byte_count=len(payload),
                expected_sha256=_sha256(payload),
                label="SR2_CANDIDATE_SOURCE:" + relative.as_posix(),
                expected_executable=False,
            )
        except SourceBindingPolicyV2Error as error:
            raise SR2IngestionSafetyError(
                "COVAPIE_SR2_INGESTION_V1_ERROR:CANDIDATE_SOURCE_REJECTED:"
                + relative.as_posix()
            ) from error
        _validate_text_payload(relative.as_posix(), payload)
        result.append(
            {
                "path": relative.as_posix(),
                "namespace": "repository_relative",
                "byte_count": len(payload),
                "SHA256": _sha256(payload),
                "expected_executable_class": "NON_EXECUTABLE",
                "source_role": role,
            }
        )
    return result


def _expected_runtime_validation() -> dict[str, object]:
    return {
        "validator": "validate_role_profile_v1", "valid": True, "reasons": [],
        "profile": EXPECTED_ROLE_PROFILE,
        "scaffold_count": 18, "linker_count": 0, "warhead_count": 9,
        "applicable_task_ids": [0, 3, 4],
        "direct_scaffold_warhead_boundary_applicable": True,
        "scaffold_linker_boundary_applicable": False,
        "linker_warhead_boundary_applicable": False,
        "direct_scaffold_warhead_boundary": {
            "scaffold_atom_id": "C9", "warhead_atom_id": "N11",
            "bond_order": "SING", "boundary_valid": True,
        },
    }


def _standalone_bound() -> dict[str, object]:
    return {
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "structural_graph_binding": _binding_record(STRUCTURAL_GRAPH_BINDING),
        "source_binding_policy_binding": _binding_record(POLICY_BINDING),
        "semantic_owner_bindings": _binding_records(SEMANTIC_OWNER_BINDINGS),
        "current_census_bindings": _binding_records(CENSUS_BINDINGS),
        "published_DIRECT_runtime_validation": _expected_runtime_validation(),
        "structural_validation": {
            "Exact27_count": 27,
            "partition_pairwise_disjoint": True,
            "partition_exhaustive": True,
            "missing_atom_ids": [], "extra_atom_ids": [],
            "W_connected": True, "L_connected_or_empty": True,
            "S_connected": True, "C51_in_W": True,
            "boundary": "C9-N11 SING S-W",
        },
        "current_census_boundary": {
            "completed_positive_event_count": 111,
            "completed_positive_unit_count": 17,
            "completed_event_count": 139,
            "completed_unit_count": 22,
            "unreviewed_event_count": 199,
            "unreviewed_unit_count": 109,
            "SR2_current_global_status": "CURRENTLY_UNREVIEWED",
            "SR2_current_review_status": "CURRENTLY_UNREVIEWED",
            "SR2_human_review_completed": False,
            "SR2_event_count": 4,
            "SR2_chemistry_disposition": "UNRESOLVED",
            "SR2_task_relevance_disposition": "UNRESOLVED",
            "SR2_training_use_disposition": "UNRESOLVED",
            "SR2_formal_training_admitted": False,
            "reconciliation_performed": False,
            "current_census_changed": False,
            "census_refreshed": False,
            "queue_updated": False,
        },
    }


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
            "SR2_COMPLETED_DECISION_METADATA_ONLY_INGESTION_NOT_RECONCILIATION_"
            "OR_TASK_LABEL_MATERIALIZATION_OR_ADMISSION"
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
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "structural_graph_binding": bound["structural_graph_binding"],
        "source_binding_policy_binding": bound["source_binding_policy_binding"],
        "semantic_owner_bindings": bound["semantic_owner_bindings"],
        "current_census_bindings": bound["current_census_bindings"],
        "current_census_boundary": bound["current_census_boundary"],
        "candidate_source_bindings": candidate_sources,
        "formal_semantic_canonical_sha256": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_semantics_independently_validated": True,
        "frozen_formal_validator_provenance_identity_only": True,
        "frozen_formal_validator_imported": False,
        "frozen_formal_validator_executed": False,
        "frozen_formal_validator_subprocess_called": False,
        "formal_validator_runtime_dependency": False,
        "NEVER_IMPORT_FORMAL_VALIDATOR": True,
        "NEVER_EXECUTE_FORMAL_VALIDATOR": True,
        "completed_lane_source_binding": _binding_record(SEMANTIC_OWNER_BINDINGS[2]),
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "published_DIRECT_runtime_validation": bound["published_DIRECT_runtime_validation"],
        "structural_validation": bound["structural_validation"],
        "canonical_task_contract": _canonical_task_contract(),
        "formal_projection": {
            "D1": "RELEVANT", "D2": "POSITIVE",
            "D3": "CONFIRM_OBSERVED_PAIR", "D4": "SELECT_CANDIDATE_15",
            "D5": TRAINING_USE_DECISION,
            "D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT,
            "D6_utf8_sha256": EXPECTED_D6_SHA256,
            "event_count": 4, "contexts_collapsed": False,
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "W_L_S_counts": [9, 0, 18],
            "boundary": "C9-N11 SING",
            "applicable_task_ids": [0, 3, 4],
        },
        "reactive_pair_authority": _pair_boundary(),
        "chemistry_boundary": _chemistry_boundary(),
        "selected_role_partition": _role_projection(
            bound["published_DIRECT_runtime_validation"]  # type: ignore[arg-type]
        ),
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": {
            **_post_boundary(),
            "POST_source_evidence_count": 4,
            "observed_distances_angstrom": [row[6] for row in EXPECTED_EVENTS],
        },
        "engineered_surrogate_caveat": _engineered_surrogate_caveat(),
        "reusable_authority_boundary": _reusable_boundary(),
        "training_boundary": _training_boundary(),
        "metadata_only_boundary": _metadata_only_boundary(),
        "authority_projection_boundary": _authority_boundary(),
        "operation_boundary": {
            "INGESTION_COMPLETE": True,
            "RECONCILIATION": False,
            "CENSUS_REFRESH": False,
            "QUEUE_REFRESH": False,
            **_metadata_only_boundary(),
            "TRAINING_STARTED": False,
        },
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
        "MANIFEST_SELF_SHA256_PROHIBITED": True,
        "determinism": {
            "source_derived_only": True,
            "UTF8": True,
            "LF": True,
            "single_final_LF": True,
            "dynamic_metadata_absent": True,
        },
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "human_training_excluded": False,
        "future_training_admission_candidate": True,
        "FORMAL_TRAINING_ADMITTED": False,
        "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
    }


def _build_artifacts_unvalidated(repo_root: Path) -> dict[str, bytes]:
    repo_root = Path(repo_root).resolve()
    bound = load_frozen_formal_decision_v1(repo_root)
    snapshot_payload = _json_bytes(_snapshot(bound))
    snapshot = _strict_json_loads(snapshot_payload, "BUILT_SNAPSHOT")
    matrix_payload = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    summary_payload = _json_bytes(_summary())
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
    """Fail closed unless all SR2 projection and non-admission semantics are exact."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    snapshot = _strict_json_loads(artifacts[SNAPSHOT], "SNAPSHOT")
    summary = _strict_json_loads(artifacts[SUMMARY], "SUMMARY")
    manifest = _strict_json_loads(artifacts[MANIFEST], "MANIFEST")
    try:
        matrix = list(csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8"))))
    except UnicodeDecodeError as error:
        raise SR2IngestionSafetyError(
            "COVAPIE_SR2_INGESTION_V1_ERROR:MATRIX_UTF8_INVALID"
        ) from error
    for document in (snapshot, summary, manifest):
        _reject_dynamic_or_forbidden_metadata(document)
    standalone = _standalone_bound()
    _expect(snapshot, _snapshot(standalone), "SNAPSHOT_EXACT_PROJECTION_INVALID")
    _expect(summary, _summary(), "SUMMARY_EXACT_COUNTS_INVALID")
    if (list(matrix[0]) if matrix else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    if artifacts[MATRIX] != _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot)):
        _fail("MATRIX_EXACT_PROJECTION_INVALID")
    if (
        len(matrix) != 4
        or tuple(row["canonical_event_id"] for row in matrix) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in matrix) != EXPECTED_RANKS
        or len({row["canonical_event_id"] for row in matrix}) != 4
        or {row["pdb_id"] for row in matrix} != {"2QLQ", "2QQ7"}
    ):
        _fail("MATRIX_EXACT4_IDENTITY_OR_CONTEXT_INVALID")
    forbidden_true = (
        "training_admitted", "formal_training_admitted",
        "training_materialization_allowed_now", "training_materialization_allowed",
        "tensor_target_created", "model_supervision_usable",
        "training_mask_targets_available_now", "current_runtime_model_usable",
        "parameter_update_authorization", "READY_FOR_TRAINING",
        "POST_geometry_training_authority", "POST_geometry_training_target_created",
        "POST_geometry_training_label_available_now", "PRE_topology_authority",
        "PRE_geometry_authority", "PRE_coordinates_authority", "PRE_reconstruction",
        "POST_to_PRE_copy", "PRE_zero_fill", "leaving_group_inferred",
        "reagent_inferred", "bond_edit_inferred", "reusable_pair_rule_created",
        "cross_structure_regiochemistry_generalization", "reusable_role_authority",
        "authoritative_task_labels_created", "event_task_label_rows_materialized",
        "sixth_task", "reusable_chemistry_authority", "reaction_family_authority",
        "warhead_rule_authority", "warhead_type_authority",
        "reaction_family_training_class_target_available",
        "warhead_rule_training_class_target_available", "warhead_type_target_available",
        "reusable_authority_label_available", "new_human_authority_created_by_ingestion",
        "dataset_mutated", "training_dataset_changed", "tensorization_performed",
        "loader_modified", "batch_modified", "model_forward", "loss", "backward",
        "optimizer", "parameter_update", "training",
    )
    required_true = (
        "human_review_completed", "task_relevance_human_authority",
        "chemistry_known_positive", "chemistry_human_authority",
        "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
        "role_partition_human_decision_available", "role_partition_human_authoritative",
        "B3_present", "task_applicability_determined",
        "event_training_use_human_decision_available", "training_use_allowed",
        "candidate_for_future_training_admission", "future_training_admission_candidate",
        "PRE_source_graph_present", "POST_source_evidence_available",
        "explicit_covalent_evidence", "projection_of_frozen_formal_human_authority",
        "metadata_only",
    )
    for row in matrix:
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["review_unit_id"] != EXPECTED_REVIEW_UNIT_ID
            or row["completed_lane"] != EXPECTED_COMPLETED_LANE
            or row["task_relevance"] != "RELEVANT"
            or row["chemistry"] != "POSITIVE"
            or row["negative_chemistry"] != "false"
            or row["task_domain_negative"] != "false"
            or row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "C51"
            or row["pair_authority_scope"] != PAIR_AUTHORITY_SCOPE
            or row["selected_candidate_index_0based"] != "15"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or json.loads(row["warhead_atoms_json"]) != list(WARHEAD_ROLE)
            or json.loads(row["linker_atoms_json"]) != []
            or json.loads(row["scaffold_atoms_json"]) != list(SCAFFOLD_ROLE)
            or row["W_L_S_counts_json"] != "[9,0,18]"
            or json.loads(row["boundary_bonds_json"]) != list(BOUNDARY_BONDS)
            or row["Exact27_count"] != "27"
            or row["global_canonical_task_count"] != "5"
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or [item["task_id"] for item in applicability if item["structurally_applicable"]]
            != [0, 3, 4]
            or any(item["training_mask_target_available_now"] for item in applicability)
            or row["formal_event_training_use_decision"] != TRAINING_USE_DECISION
            or row["human_training_excluded"] != "false"
            or row["training_exclusion_reason"] != ""
            or row["future_training_admission_status"] != FUTURE_STATUS
            or row["supporting_PRE_source_graph_count_per_event"] != "1"
            or row["PRE_source_graph_count_per_event"] != "1"
            or row["PRE_mapping_count_per_event"] != "0"
            or row["PRE_mapping_status"] != PRE_MAPPING_STATUS
            or row["PRE_status"] != PRE_STATUS
            or row["authority_source"] != AUTHORITY_SOURCE
            or any(row[key] != "false" for key in forbidden_true)
            or any(row[key] != "true" for key in required_true)
        ):
            _fail("MATRIX_AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    sources = manifest.get("candidate_source_bindings")
    if type(sources) is not list or len(sources) != 3:
        _fail("CANDIDATE_SOURCE_BINDINGS_INVALID")
    expected_source_paths = [
        SOURCE_RELATIVE.as_posix(), CHECKER_RELATIVE.as_posix(), TEST_RELATIVE.as_posix()
    ]
    if [record.get("path") for record in sources] != expected_source_paths:
        _fail("CANDIDATE_SOURCE_BINDING_PATHS_INVALID")
    for record in sources:
        if (
            type(record) is not dict
            or record.get("namespace") != "repository_relative"
            or record.get("expected_executable_class") != "NON_EXECUTABLE"
            or type(record.get("byte_count")) is not int
            or type(record.get("SHA256")) is not str
            or len(record["SHA256"]) != 64
        ):
            _fail("CANDIDATE_SOURCE_BINDING_RECORD_INVALID")
    expected_manifest = _manifest(
        standalone,
        sources,  # type: ignore[arg-type]
        artifacts[SNAPSHOT], artifacts[MATRIX], artifacts[SUMMARY],
    )
    _expect(manifest, expected_manifest, "MANIFEST_CLOSURE_INVALID")
    if repo_root is not None and dict(artifacts) != _build_artifacts_unvalidated(Path(repo_root)):
        _fail("DIRECT_SOURCE_DERIVED_PROJECTION_INVALID")


def build_artifacts_v1(repo_root: Path) -> dict[str, bytes]:
    """Build pure deterministic bytes for the four authorized output artifacts."""

    artifacts = _build_artifacts_unvalidated(Path(repo_root).resolve())
    validate_completed_decision_projection_v1(artifacts)
    return artifacts


def _validate_materialization_destination_v1(target_root: Path) -> None:
    try:
        metadata = target_root.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise SR2IngestionSafetyError(
            "COVAPIE_SR2_INGESTION_V1_ERROR:OUTPUT_ROOT_LSTAT_FAILED"
        ) from error
    if stat.S_ISLNK(metadata.st_mode):
        _fail("OUTPUT_ROOT_SYMLINK_FORBIDDEN")
    if not stat.S_ISDIR(metadata.st_mode):
        _fail("OUTPUT_ROOT_NOT_DIRECTORY")
    entries = tuple(target_root.iterdir())
    if any(entry.name not in OUTPUT_FILENAMES for entry in entries):
        _fail("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES")
    for entry in entries:
        entry_metadata = entry.lstat()
        if stat.S_ISLNK(entry_metadata.st_mode) or not stat.S_ISREG(entry_metadata.st_mode):
            _fail("OUTPUT_ENTRY_NOT_REGULAR:" + entry.name)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".atomic-write", dir=path.parent
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
    """Write only the four deterministic SR2 output artifacts."""

    repo_root = Path(repo_root).resolve()
    artifacts = build_artifacts_v1(repo_root)
    target = Path(output_root) if output_root is not None else repo_root / OUTPUT_ROOT_RELATIVE
    _validate_materialization_destination_v1(target)
    for name, payload in artifacts.items():
        _atomic_write(target / name, payload)
    return artifacts


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    """Compare the Exact4 materialization with a fresh source-derived build."""

    repo_root = Path(repo_root).resolve()
    expected = build_artifacts_v1(repo_root)
    root = repo_root / OUTPUT_ROOT_RELATIVE
    if not root.is_dir() or root.is_symlink():
        _fail("OUTPUT_ROOT_NOT_REGULAR_DIRECTORY")
    if tuple(sorted(path.name for path in root.iterdir())) != tuple(sorted(OUTPUT_FILENAMES)):
        _fail("OUTPUT_INVENTORY_NOT_EXACT4")
    actual: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = root / name
        payload = path.read_bytes()
        try:
            actual[name] = verify_bound_source_v2(
                path=path,
                expected_byte_count=len(payload),
                expected_sha256=_sha256(payload),
                label="SR2_MATERIALIZED_OUTPUT:" + name,
                expected_executable=False,
            )
        except SourceBindingPolicyV2Error as error:
            raise SR2IngestionSafetyError(
                "COVAPIE_SR2_INGESTION_V1_ERROR:OUTPUT_REJECTED:" + name
            ) from error
    validate_completed_decision_projection_v1(actual, repo_root=repo_root)
    if actual != expected:
        _fail("MATERIALIZED_OUTPUT_BYTES_DRIFT")
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "exact_output_count": 4,
        "event_count": 4,
        "deterministic": True,
        "SR2_COMPLETED_DECISION_INGESTED": True,
        "SR2_COMPLETED_LANE": EXPECTED_COMPLETED_LANE,
        "SR2_FORMAL_VALIDATOR_PROVENANCE_ONLY": True,
        "SR2_FORMAL_SEMANTICS_INDEPENDENTLY_VALIDATED": True,
        "SR2_HUMAN_TRAINING_EXCLUDED": False,
        "SR2_TRAINING_USE_ALLOWED": True,
        "SR2_FUTURE_TRAINING_ADMISSION_CANDIDATE": True,
        "SR2_FORMAL_TRAINING_ADMITTED": False,
        "SR2_TRAINING_MATERIALIZATION_ALLOWED": False,
        "SR2_TENSOR_TARGET_CREATED": False,
        "SR2_PRE_REACTION_UNRESOLVED": True,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    materialize_artifacts_v1(repo_root)
    print(json.dumps(check_materialized_v1(repo_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
