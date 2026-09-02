"""Project frozen 4M5 human authority into deterministic ingestion metadata.

The frozen formal validator is provenance identity only: this owner binds its
bytes but never imports or executes it. The formal JSON is strict-parsed and
independently validated, including its Exact25 DIRECT role partition against
the bound preparation graph and published DIRECT runtime. This additive step
does not reconcile or refresh global state, create task-label rows, admit or
tensorize samples, or train a model.
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
    "FourM5IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)


SCHEMA_VERSION = "covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_4m5_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_4m5_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_4m5_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_4m5_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_4m5_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_4m5_event_task_label_availability_v1.csv"
SUMMARY = "covapie_4m5_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_4m5_completed_decision_ingestion_manifest_v1.json"
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
    "4M5_COVAPIE_BULK_REVIEW_UNIT_9E98765987D25C42/"
    "formal-human-decision-v1"
)
FORMAL_DECISION_RELATIVE = FORMAL_ROOT / "4m5_formal_human_decision_v1.json"
FORMAL_VALIDATOR_RELATIVE = FORMAL_ROOT / "validate_4m5_formal_human_decision_v1.py"
STRUCTURAL_GRAPH_RELATIVE = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "4M5_COVAPIE_BULK_REVIEW_UNIT_9E98765987D25C42/"
    "review-preparation-v1/4m5_graph_and_role_candidates_v1.json"
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
CENSUS_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_with_cer_v1.py"
)
CENSUS_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_cer_v1"
)
CENSUS_MATRIX_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_census_with_cer_v1.csv"
)
CENSUS_SUMMARY_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_summary_with_cer_v1.json"
)
CENSUS_MANIFEST_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_manifest_with_cer_v1.json"
)

FORMAL_DECISION_SCHEMA = "covapie_4m5_exact4_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "c2a18158dd9c841f8022150edbf42de74b84016bb8566c112bd63aa1b3badfa9"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_9E98765987D25C42"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
EXPECTED_D6 = (
    "Confirm the sample-specific observed CYS-SG ↔ 4M5-C15 covalent pair for "
    "the 5AZT/5AZV Exact4. The 4M5/17-oxoDHA literature supports covalent "
    "modification of PPARalpha Cys275 and PPARgamma Cys285, but this review "
    "does not create reusable C15 regiochemistry, reaction-family, warhead-rule, "
    "warhead-type, or cross-structure authority. Select DIRECT candidate 0 as "
    "the sample-level scaffold/warhead role partition with an empty linker. The "
    "frozen PDB/CCD ligand representation must not be treated as authoritative "
    "free-ligand PRE topology; PRE remains PRE_REACTION_UNRESOLVED. D5 INCLUDE "
    "is a human training-use disposition only and does not constitute formal "
    "training admission or training readiness."
)
EXPECTED_D6_BYTE_COUNT = 699
EXPECTED_D6_SHA256 = "21d0c0558174f2da548a1430333b639da273399bd020d2a64cde8a8e1511a254"

AUTHORITY_SOURCE = "FORMAL_4M5_HUMAN_DECISION"
PAIR_AUTHORITY_SCOPE = "CURRENT_4M5_5AZT_5AZV_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
ROLE_AUTHORITY_SCOPE = "CURRENT_4M5_EXACT4_REVIEW_UNIT_ONLY"
FUTURE_STATUS = "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"
PRE_STATUS = "PRE_REACTION_UNRESOLVED"
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"

# event id, rank, PDB, protein asym, residue, ligand asym, connection,
# computed distance, frozen lexeme, reported distance, context
EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:5AZT:A:CYS:275-:SG:D:4M5:C15",
        973, "5AZT", "A", "CYS:275-", "D", "covale1",
        1.785022, "1.785022", 1.785, "PPARalpha",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:5AZT:B:CYS:275-:SG:E:4M5:C15",
        974, "5AZT", "B", "CYS:275-", "E", "covale2",
        1.829385, "1.829385", 1.829, "PPARalpha",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:5AZV:A:CYS:285-:SG:C:4M5:C15",
        975, "5AZV", "A", "CYS:285-", "C", "covale1",
        1.766225, "1.766225", 1.766, "PPARgamma",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:5AZV:B:CYS:285-:SG:D:4M5:C15",
        976, "5AZV", "B", "CYS:285-", "D", "covale2",
        1.755127, "1.755127", 1.755, "PPARgamma",
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)

WARHEAD_ROLE = ("C15", "C16", "C17", "C18", "C19", "C20", "C21", "C22", "O23")
LINKER_ROLE: tuple[str, ...] = ()
SCAFFOLD_ROLE = (
    "C1", "C10", "C11", "C12", "C13", "C14", "C2", "C3",
    "C4", "C5", "C6", "C7", "C8", "C9", "O24", "O25",
)
HEAVY_ATOMS = (
    "C1", "C10", "C11", "C12", "C13", "C14", "C15", "C16",
    "C17", "C18", "C19", "C2", "C20", "C21", "C22", "C3",
    "C4", "C5", "C6", "C7", "C8", "C9", "O23", "O24", "O25",
)
HEAVY_BONDS = (
    ("C1", "C2", "SING"), ("C1", "O24", "DOUB"),
    ("C1", "O25", "SING"), ("C10", "C11", "DOUB"),
    ("C10", "C9", "SING"), ("C11", "C12", "SING"),
    ("C12", "C13", "SING"), ("C13", "C14", "DOUB"),
    ("C14", "C15", "SING"), ("C15", "C16", "SING"),
    ("C16", "C17", "SING"), ("C17", "C18", "SING"),
    ("C17", "O23", "DOUB"), ("C18", "C19", "SING"),
    ("C19", "C20", "DOUB"), ("C2", "C3", "SING"),
    ("C20", "C21", "SING"), ("C21", "C22", "SING"),
    ("C3", "C4", "SING"), ("C4", "C5", "DOUB"),
    ("C5", "C6", "SING"), ("C6", "C7", "SING"),
    ("C7", "C8", "DOUB"), ("C8", "C9", "SING"),
)
BOUNDARY_BONDS = (
    {
        "atom_id_1": "C14", "atom_id_2": "C15", "bond_order": "SING",
        "boundary_between_roles": ["scaffold", "warhead"],
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

# path, namespace, byte count, SHA256, expected executable, source role
FORMAL_BINDINGS = (
    (
        FORMAL_DECISION_RELATIVE, "project_parent_relative", 29089,
        "5e37540220ac44b281b20bfb796f5c2994d0ab402fb5f65acc03fb6f6b1febfb",
        False, "FOUR_M5_FROZEN_FORMAL_HUMAN_DECISION",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE, "project_parent_relative", 56100,
        "098b0d783dc098632ebd7d67a4e3d74f9f61f96452c50b2e8d3cc14057bd3d84",
        False, "FOUR_M5_FROZEN_FORMAL_VALIDATOR_PROVENANCE_IDENTITY_ONLY",
    ),
)
STRUCTURAL_GRAPH_BINDING = (
    STRUCTURAL_GRAPH_RELATIVE, "project_parent_relative", 42741,
    "5de352bef4c235b777fa80b4a8fb1d3d38019bb1db78193100b7cfebd7004df5",
    False, "FOUR_M5_BOUND_SUPPORTING_GRAPH_FOR_STRUCTURAL_VALIDATION",
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
)
CENSUS_BINDINGS = (
    (
        CENSUS_OWNER_RELATIVE, "repository_relative", 74431,
        "dba9110cda9ec62b540f3bdefee0c3df78a58dc571407994d8b594ae9d9ccd1b",
        False, "CURRENT_WITH_CER_GLOBAL_CENSUS_OWNER",
    ),
    (
        CENSUS_MATRIX_RELATIVE, "repository_relative", 535454,
        "9da898c15da0dad45dd37a33ca2665e5e1634d588b566f824fe688c6cc49e71a",
        False, "CURRENT_WITH_CER_GLOBAL_CENSUS_MATRIX",
    ),
    (
        CENSUS_SUMMARY_RELATIVE, "repository_relative", 18341,
        "12187f4067b5b5f07e364c6e4f9fe74a7b44e0819d4afcaa24c1b6db1fb12d2b",
        False, "CURRENT_WITH_CER_GLOBAL_CENSUS_SUMMARY",
    ),
    (
        CENSUS_MANIFEST_RELATIVE, "repository_relative", 57195,
        "88ed6521fd7925018280876acd9c6743abb620dc6fa9131fe0a4b134c545dd76",
        False, "CURRENT_WITH_CER_GLOBAL_CENSUS_MANIFEST",
    ),
)
POLICY_BINDING = (
    SOURCE_BINDING_POLICY_RELATIVE, "repository_relative", 3704,
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    False, "PUBLISHED_SOURCE_BINDING_POLICY_V2",
)

_Binding = tuple[Path, str, int, str, bool, str]
_FORBIDDEN_AMBIGUOUS_FORMAL_FIELDS = {
    "human_authored_free_text", "machine_generated_token",
}
_FORBIDDEN_LIVE_IDENTITY_FIELDS = {
    "mode", "required_mode", "expected_mode", "filesystem_mode", "posix_mode",
}


class FourM5IngestionSafetyError(ValueError):
    """Raised when the frozen 4M5 ingestion contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise FourM5IngestionSafetyError("COVAPIE_4M5_INGESTION_V1_ERROR:" + reason)


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
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("JSON_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise FourM5IngestionSafetyError(
            "COVAPIE_4M5_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label
        ) from error

    def pairs_hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
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
            text, object_pairs_hook=pairs_hook, parse_constant=reject_constant
        )
    except json.JSONDecodeError as error:
        raise FourM5IngestionSafetyError(
            "COVAPIE_4M5_INGESTION_V1_ERROR:JSON_PARSE_FAILED:" + label
        ) from error
    if type(parsed) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return parsed


def _binding_record(binding: _Binding) -> dict[str, object]:
    relative, namespace, byte_count, digest, expected_executable, source_role = binding
    return {
        "path": relative.as_posix(),
        "namespace": namespace,
        "byte_count": byte_count,
        "SHA256": digest,
        "expected_executable_class": (
            "EXECUTABLE" if expected_executable else "NON_EXECUTABLE"
        ),
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
    relative, _namespace, byte_count, digest, expected_executable, source_role = binding
    path = _resolve_binding_path(repo_root, binding, overrides)
    try:
        return verify_bound_source_v2(
            path=path,
            expected_byte_count=byte_count,
            expected_sha256=digest,
            label=source_role + ":" + relative.as_posix(),
            expected_executable=expected_executable,
        )
    except SourceBindingPolicyV2Error as error:
        raise FourM5IngestionSafetyError(
            "COVAPIE_4M5_INGESTION_V1_ERROR:BOUND_SOURCE_REJECTED:" + source_role
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
        raise FourM5IngestionSafetyError(
            "COVAPIE_4M5_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
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
                    raise FourM5IngestionSafetyError(
                        "COVAPIE_4M5_INGESTION_V1_ERROR:"
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
        canonical["CANONICAL_TASKS"],
        CANONICAL_TASKS,
        "CANONICAL_EXACT5_OWNER_DRIFT",
    )
    return {
        "role_profile": EXPECTED_ROLE_PROFILE,
        "global_canonical_task_count": 5,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "B3_present": True,
        "sixth_task_present": False,
    }


def _semantic_digest(formal: Mapping[str, Any]) -> str:
    clone = copy.deepcopy(dict(formal))
    digest = clone.pop("formal_semantic_canonical_sha256", None)
    if type(digest) is not str:
        _fail("FORMAL_SEMANTIC_DIGEST_FIELD_INVALID")
    return _sha256(_canonical_json(clone))


def _reject_ambiguous_formal_fields(value: object, path: str = "root") -> None:
    if type(value) is dict:
        for key, child in value.items():
            if key in _FORBIDDEN_AMBIGUOUS_FORMAL_FIELDS:
                _fail("FORMAL_AMBIGUOUS_PROVENANCE_FIELD:" + path + "." + key)
            _reject_ambiguous_formal_fields(child, path + "." + key)
    elif type(value) is list:
        for index, child in enumerate(value):
            _reject_ambiguous_formal_fields(child, f"{path}[{index}]")


def _expected_formal_events() -> list[dict[str, object]]:
    return [
        {
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_candidate": "SELECT_CANDIDATE_0",
            "D5_training_use": "INCLUDE",
            "D6_context_reference": "UNIT_LEVEL_EXACT_AUTHORIZED_D6",
            "POST_distance_angstrom": row[7],
            "POST_geometry_training_authority": False,
            "canonical_event_id": row[0],
            "cys_residue_id": row[4],
            "distance_only_inference": False,
            "event_index": index,
            "explicit_covalent_evidence": True,
            "formal_training_admitted": False,
            "ligand_asym": row[5],
            "ligand_component_id": "4M5",
            "ligand_reactive_atom": "C15",
            "model_number": 1,
            "pdb_id": row[2],
            "protein_asym": row[3],
            "protein_reactive_atom": "SG",
            "reported_POST_distance_angstrom": row[9],
            "sample_level_formal_authority": True,
            "scaleup_rank": row[1],
            "selected_connection_id": row[6],
        }
        for index, row in enumerate(EXPECTED_EVENTS)
    ]


def _expected_contexts() -> dict[str, object]:
    return {
        "contexts": [
            {
                "canonical_event_ids": list(EXPECTED_EVENT_IDS[:2]),
                "cys_residue": "Cys275",
                "event_count": 2,
                "pdb_id": "5AZT",
                "protein_context": "PPARalpha",
            },
            {
                "canonical_event_ids": list(EXPECTED_EVENT_IDS[2:]),
                "cys_residue": "Cys285",
                "event_count": 2,
                "pdb_id": "5AZV",
                "protein_context": "PPARgamma",
            },
        ],
        "contexts_collapsed": False,
        "exception_count": 0,
    }


def _expected_formal_role() -> dict[str, object]:
    formal_boundary = {
        "aromatic_flag": "N",
        "atom_id_1": "C14",
        "atom_id_2": "C15",
        "bond_order": "SING",
        "role_1": "S",
        "role_2": "W",
    }
    runtime = {
        "applicable_task_ids": [0, 3, 4],
        "direct_scaffold_warhead_boundary": {
            "bond_order": "SING",
            "boundary_valid": True,
            "scaffold_atom_id": "C14",
            "warhead_atom_id": "C15",
        },
        "direct_scaffold_warhead_boundary_applicable": True,
        "linker_count": 0,
        "linker_warhead_boundary_applicable": False,
        "profile": EXPECTED_ROLE_PROFILE,
        "reasons": [],
        "scaffold_count": 16,
        "scaffold_linker_boundary_applicable": False,
        "valid": True,
        "validator": "validate_role_profile_v1",
        "warhead_count": 9,
    }
    return {
        "D4_human_choice": "SELECT_CANDIDATE_0",
        "Exact25_count": 25,
        "L": [],
        "S": list(SCAFFOLD_ROLE),
        "W": list(WARHEAD_ROLE),
        "W_L_S_counts": [9, 0, 16],
        "applicable_semantic_names": [
            "warhead_only",
            "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
        ],
        "applicable_task_ids": [0, 3, 4],
        "boundary_bonds": [formal_boundary],
        "candidate_index_is_rank": False,
        "candidate_index_is_recommendation": False,
        "current_review_unit_role_partition_human_authority": True,
        "human_selected": True,
        "independent_structural_validation": {
            "C15_in_W": True,
            "Exact25_count": 25,
            "L_connected_or_empty": True,
            "L_count": 0,
            "S_connected": True,
            "S_count": 16,
            "W_connected": True,
            "W_count": 9,
            "cross_role_boundary_bonds": [formal_boundary],
            "extra_atom_ids": [],
            "missing_atom_ids": [],
            "partition_exhaustive": True,
            "partition_pairwise_disjoint": True,
        },
        "machine_recommended": False,
        "machine_selected": False,
        "published_DIRECT_runtime_validation": runtime,
        "reusable_role_rule_created": False,
        "role_authority_scope": ROLE_AUTHORITY_SCOPE,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "selected_candidate_index_0based": 0,
    }


def _expected_formal_tasks() -> dict[str, object]:
    return {
        "B3_present": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "global_canonical_Exact5": [
            {
                "display_alias": alias,
                "semantic_name": semantic,
                "task_id": task_id,
            }
            for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "global_mask_contract_modified": False,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "sample_applicable_semantic_names": [
            "warhead_only",
            "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
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
    _reject_ambiguous_formal_fields(formal)
    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(formal.get("record_role"), FORMAL_RECORD_ROLE, "FORMAL_RECORD_ROLE_DRIFT")
    _expect(
        formal.get("formal_semantic_canonical_sha256"),
        FORMAL_SEMANTIC_CANONICAL_SHA256,
        "FORMAL_SEMANTIC_DIGEST_LITERAL_DRIFT",
    )
    if _semantic_digest(formal) != FORMAL_SEMANTIC_CANONICAL_SHA256:
        _fail("FORMAL_SEMANTIC_DIGEST_RECOMPUTE_FAILED")
    for key, expected in (
        ("unsigned", False),
        ("approved", True),
        ("decision_finalized", True),
        ("human_review_completed", True),
        ("human_decision_created", True),
        ("formal_authority_created", True),
    ):
        _expect(formal.get(key), expected, "FORMAL_FINALIZATION_DRIFT:" + key)

    expected_human = {
        "D1_task_relevance": "RELEVANT",
        "D2_chemistry": "POSITIVE",
        "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
        "D4_role_candidate": "SELECT_CANDIDATE_0",
        "D5_training_use": "INCLUDE",
        "D6_scientific_context": EXPECTED_D6,
        "attestor_id": "fmx",
        "authorization_origin": "EXTERNAL_HUMAN_CHAT_AUTHORIZATION",
        "formal_decision_authority_is_human": True,
        "human_choices_externally_authorized": True,
        "human_selected_role_candidate_index_0based": 0,
        "human_selected_role_profile": EXPECTED_ROLE_PROFILE,
        "machine_approval_claimed": False,
        "machine_roles": ["PROJECT", "FORMALIZE", "VALIDATE", "FREEZE"],
        "machine_scientific_authority_created": False,
        "reviewer_id": "fmx",
        "scientific_decision_authority_source": (
            "EXTERNAL_HUMAN_REVIEWER_AUTHORIZATION"
        ),
    }
    _expect(
        formal.get("human_authorization"),
        expected_human,
        "FORMAL_HUMAN_AUTHORIZATION_DRIFT",
    )
    expected_context = {
        "D6_draft_origin": "ASSISTANT_DRAFT_ACCEPTED_BY_HUMAN",
        "D6_exact": True,
        "D6_human_authored": False,
        "D6_human_authorized": True,
        "D6_human_reviewed_and_accepted": True,
        "D6_scientific_context": EXPECTED_D6,
        "D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT,
        "D6_utf8_sha256": EXPECTED_D6_SHA256,
        "assistant_draft_does_not_create_authority": True,
        "formal_decision_authority_is_human": True,
        "human_authorization_remains_authority_source": True,
        "machine_scientific_authority_created": False,
    }
    _expect(
        formal.get("human_approved_context"),
        expected_context,
        "FORMAL_D6_PROVENANCE_DRIFT",
    )
    d6_bytes = EXPECTED_D6.encode("utf-8")
    if (
        len(d6_bytes) != EXPECTED_D6_BYTE_COUNT
        or _sha256(d6_bytes) != EXPECTED_D6_SHA256
    ):
        _fail("INTERNAL_D6_IDENTITY_INVALID")
    _expect(
        formal.get("unit_human_decision"),
        {
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_candidate": "SELECT_CANDIDATE_0",
            "D5_training_use": "INCLUDE",
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
            "ligand_component_id": "4M5",
            "ligand_reactive_atom": "C15",
            "pdb_ids": ["5AZT", "5AZV"],
            "protein_reactive_atom": "SG",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scaleup_ranks": list(EXPECTED_RANKS),
        },
        "FORMAL_EXACT4_IDENTITY_DRIFT",
    )
    _expect(
        formal.get("context_preservation"),
        _expected_contexts(),
        "FORMAL_CONTEXT_PRESERVATION_DRIFT",
    )
    _expect(
        formal.get("event_level_formal_human_decisions"),
        _expected_formal_events(),
        "FORMAL_EVENT_DECISION_OR_EVIDENCE_DRIFT",
    )
    _expect(
        formal.get("selected_role_partition"),
        _expected_formal_role(),
        "FORMAL_CANDIDATE0_ROLE_DRIFT",
    )
    _expect(
        formal.get("canonical_Exact5_and_sample_applicability"),
        _expected_formal_tasks(),
        "FORMAL_CANONICAL_EXACT5_DRIFT",
    )
    _expect(
        formal.get("reactive_pair_authority"),
        {
            "D3_human_choice": "CONFIRM_OBSERVED_PAIR",
            "all_17_oxoDHA_uses_C15_authority_created": False,
            "all_4M5_uses_C15_authority_created": False,
            "all_PPAR_17_oxoDHA_pairs_use_C15_authority_created": False,
            "authority_scope": PAIR_AUTHORITY_SCOPE,
            "cross_structure_regiochemistry_generalization": False,
            "ligand_reactive_atom": "C15",
            "observed_pair_authority_created": True,
            "protein_reactive_atom": "SG",
            "reusable_pair_rule_created": False,
        },
        "FORMAL_PAIR_AUTHORITY_DRIFT",
    )
    _expect(
        formal.get("chemistry_authority_boundary"),
        {
            "D2_human_choice": "POSITIVE",
            "current_review_unit_chemistry_positive_authority": True,
            "reaction_family_authority_created": False,
            "reusable_chemistry_authority_created": False,
            "reusable_chemistry_rule_created": False,
            "warhead_family_authority_created": False,
            "warhead_rule_authority_created": False,
            "warhead_type_reusable_authority_created": False,
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
        formal.get("free_ligand_PDB_component_boundary"),
        {
            "PDB_component_representation_is_not_authoritative_PRE_free_ligand_topology": True,
            "corrected_PRE_graph_synthesized": False,
            "frozen_CCD_modified": False,
            "observed_C15_pair_authority_altered": False,
        },
        "FORMAL_FREE_LIGAND_BOUNDARY_DRIFT",
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
            "observed_distances_angstrom": [row[7] for row in EXPECTED_EVENTS],
        },
        "FORMAL_POST_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("training_use_boundary"),
        {
            "D5_human_choice": "INCLUDE",
            "READY_FOR_TRAINING": False,
            "current_runtime_model_usable": False,
            "feature_semantics_finalized": False,
            "formal_split_authority": False,
            "formal_training_admitted": False,
            "future_training_admission_candidate": True,
            "human_training_use_disposition": "INCLUDE",
            "human_training_use_disposition_authority_created": True,
            "parameter_update_authorization": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
        },
        "FORMAL_TRAINING_BOUNDARY_DRIFT",
    )

    authority = formal.get("authority_boundary")
    if type(authority) is not dict:
        _fail("FORMAL_AUTHORITY_BOUNDARY_INVALID")
    required_true = (
        "formal_authority_created",
        "human_decision_created",
        "human_review_completed",
        "sample_level_canonical_role_partition_authority_created",
        "sample_level_chemistry_positive_authority_created",
        "sample_level_formal_human_decision_authority_created",
        "sample_level_reactive_pair_authority_created",
        "sample_level_role_profile_task_applicability_determined",
        "sample_level_task_relevance_authority_created",
        "sample_level_training_use_human_decision_authority_created",
    )
    required_false = (
        "POST_geometry_training_authority_created",
        "PRE_geometry_authority_created",
        "PRE_topology_authority_created",
        "READY_FOR_TRAINING",
        "authoritative_task_labels_created",
        "chemical_warhead_authority_created",
        "current_runtime_model_usable",
        "event_task_label_rows_created",
        "formal_split_authority_created",
        "formal_training_admitted",
        "parameter_update_authorization",
        "reaction_family_authority_created",
        "reusable_chemistry_authority_created",
        "reusable_pair_authority_created",
        "reusable_role_authority_created",
        "tensor_target_created",
        "training_admission_created",
        "training_started",
        "warhead_family_authority_created",
        "warhead_rule_authority_created",
        "warhead_type_authority_created",
    )
    for key in required_true:
        _expect(authority.get(key), True, "FORMAL_REQUIRED_AUTHORITY_MISSING:" + key)
    for key in required_false:
        _expect(authority.get(key), False, "FORMAL_UNAUTHORIZED_AUTHORITY:" + key)

    _expect(
        formal.get("current_published_census_preformal_provenance"),
        {
            "HEAD": "4b59e3a1a9cd07cfb48c19df4ac50de740dc98a9",
            "census_modified_by_this_step": False,
            "chemistry_disposition": "UNRESOLVED",
            "current_status": "CURRENTLY_UNREVIEWED",
            "event_count": 4,
            "formal_training_admitted": False,
            "human_review_completed": False,
            "task_relevance_disposition": "UNRESOLVED",
            "training_use_disposition": "UNRESOLVED",
        },
        "FORMAL_CURRENT_CENSUS_PROVENANCE_DRIFT",
    )
    operation = formal.get("operation_boundary")
    if type(operation) is not dict:
        _fail("FORMAL_OPERATION_BOUNDARY_INVALID")
    for key in (
        "CENSUS_REFRESH", "INGESTION_PERFORMED", "QUEUE_REFRESH",
        "READY_FOR_TRAINING", "RECONCILIATION", "TRAINING_STARTED",
        "backward", "loader", "loss", "model_forward", "optimizer",
        "parameter_update", "tensorization", "training_admission",
    ):
        _expect(operation.get(key), False, "FORMAL_OPERATION_BOUNDARY_DRIFT:" + key)
    lifecycle = formal.get("validator_lifecycle")
    if type(lifecycle) is not dict:
        _fail("FORMAL_VALIDATOR_LIFECYCLE_INVALID")
    for key, expected in (
        ("baseline_commit", "4b59e3a1a9cd07cfb48c19df4ac50de740dc98a9"),
        ("validator_baseline_locked_creation_and_self_test_only", True),
        ("validator_postbaseline_runtime_dependency_allowed", False),
        ("future_ingestion_must_bind_formal_JSON_and_validator_bytes_SHA256", True),
        ("future_ingestion_must_independently_validate_formal_semantics", True),
        ("future_ingestion_must_not_execute_this_validator_after_HEAD_advances", True),
    ):
        _expect(lifecycle.get(key), expected, "FORMAL_VALIDATOR_LIFECYCLE_DRIFT:" + key)
    prerequisite = formal.get("training_prerequisite_warning")
    if type(prerequisite) is not dict:
        _fail("FORMAL_TRAINING_PREREQUISITE_INVALID")
    for key, expected in (
        ("FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER", True),
        ("READY_FOR_TRAINING", False),
        ("Step12D", "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT"),
        ("TRAINING_STARTED", False),
        ("UNKNOWN_ATOM_FEATURE_POLICY_REQUIRES_RESOLUTION_OR_FORMAL_AUDIT", True),
        ("feature_semantics_known_false_requires_resolution_or_formal_audit", True),
    ):
        _expect(prerequisite.get(key), expected, "FORMAL_TRAINING_PREREQUISITE:" + key)


def _connected(atom_ids: Sequence[str], bonds: Sequence[tuple[str, str, str]]) -> bool:
    if not atom_ids:
        return True
    allowed = set(atom_ids)
    adjacency = {atom: set() for atom in allowed}
    for left, right, _order in bonds:
        if left in allowed and right in allowed:
            adjacency[left].add(right)
            adjacency[right].add(left)
    visited: set[str] = set()
    pending = [atom_ids[0]]
    while pending:
        atom = pending.pop()
        if atom in visited:
            continue
        visited.add(atom)
        pending.extend(adjacency[atom] - visited)
    return visited == allowed


def _validate_structural_graph(payload: bytes) -> dict[str, object]:
    graph = _strict_json_loads(payload, "FOUR_M5_BOUND_STRUCTURAL_GRAPH")
    heavy_atoms = graph.get("heavy_atoms")
    heavy_bonds = graph.get("heavy_bonds")
    candidates = graph.get("candidates")
    if (
        type(heavy_atoms) is not list
        or type(heavy_bonds) is not list
        or type(candidates) is not list
        or not candidates
    ):
        _fail("STRUCTURAL_GRAPH_INVENTORY_INVALID")
    atom_ids = tuple(
        row.get("atom_id") for row in heavy_atoms if type(row) is dict
    )
    bonds = tuple(
        (row.get("atom_id_1"), row.get("atom_id_2"), row.get("bond_order"))
        for row in heavy_bonds
        if type(row) is dict
    )
    if (
        graph.get("schema_version") != "covapie_4m5_graph_and_role_candidates_v1"
        or graph.get("record_role")
        != "MACHINE_GRAPH_EVIDENCE_AND_UNSELECTED_GRAPH_CANDIDATES_ONLY"
        or graph.get("review_unit_id") != EXPECTED_REVIEW_UNIT_ID
        or graph.get("ligand_component_id") != "4M5"
        or graph.get("heavy_atom_count") != 25
        or graph.get("heavy_bond_count") != 24
        or atom_ids != HEAVY_ATOMS
        or bonds != HEAVY_BONDS
        or graph.get("machine_selected") is not False
        or graph.get("machine_candidate_selected") is not False
        or graph.get("human_selected") is not False
        or graph.get("selected_candidate") is not None
        or graph.get("human_selected_candidate") is not None
        or graph.get("machine_recommended_candidate") is not None
        or graph.get("retained_candidate_count") != 8
        or len(candidates) != 8
    ):
        _fail("STRUCTURAL_GRAPH_IDENTITY_OR_AUTHORITY_DRIFT")
    candidate0 = candidates[0]
    expected_boundary = {
        "aromatic_flag": "N",
        "atom_id_1": "C14",
        "atom_id_2": "C15",
        "bond_order": "SING",
        "role_1": "S",
        "role_2": "W",
    }
    if (
        type(candidate0) is not dict
        or candidate0.get("index_0based") != 0
        or candidate0.get("profile") != EXPECTED_ROLE_PROFILE
        or candidate0.get("W") != list(WARHEAD_ROLE)
        or candidate0.get("L") != []
        or candidate0.get("S") != list(SCAFFOLD_ROLE)
        or candidate0.get("boundary_bonds") != [expected_boundary]
        or candidate0.get("applicable_task_ids") != [0, 3, 4]
        or candidate0.get("disjoint") is not True
        or candidate0.get("exhaustive") is not True
        or candidate0.get("W_connected") is not True
        or candidate0.get("L_connected_or_empty") is not True
        or candidate0.get("S_connected") is not True
        or candidate0.get("reactive_atom_in_W") is not True
        or candidate0.get("machine_selected") is not False
        or candidate0.get("machine_recommended") is not False
        or candidate0.get("human_selected") is not False
    ):
        _fail("STRUCTURAL_GRAPH_CANDIDATE0_DRIFT")
    role_sets = (set(WARHEAD_ROLE), set(LINKER_ROLE), set(SCAFFOLD_ROLE))
    if (
        len(HEAVY_ATOMS) != 25
        or len(set(HEAVY_ATOMS)) != 25
        or any(role_sets[left] & role_sets[right] for left, right in ((0, 1), (0, 2), (1, 2)))
        or set().union(*role_sets) != set(HEAVY_ATOMS)
        or "C15" not in WARHEAD_ROLE
        or not _connected(WARHEAD_ROLE, HEAVY_BONDS)
        or not _connected(SCAFFOLD_ROLE, HEAVY_BONDS)
        or not _connected(LINKER_ROLE, HEAVY_BONDS)
    ):
        _fail("INDEPENDENT_EXACT25_PARTITION_VALIDATION_FAILED")
    cross_role = tuple(
        (left, right, order)
        for left, right, order in HEAVY_BONDS
        if (
            (left in set(SCAFFOLD_ROLE) and right in set(WARHEAD_ROLE))
            or (right in set(SCAFFOLD_ROLE) and left in set(WARHEAD_ROLE))
        )
    )
    if cross_role != (("C14", "C15", "SING"),):
        _fail("INDEPENDENT_DIRECT_BOUNDARY_VALIDATION_FAILED")
    return {
        "atom_ids": atom_ids,
        "bonds": bonds,
        "Exact25_count": 25,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "missing_atom_ids": [],
        "extra_atom_ids": [],
        "W_connected": True,
        "L_connected_or_empty": True,
        "S_connected": True,
        "C15_in_W": True,
        "boundary": "C14-C15 SING S-W",
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
        reactive_atom_id="C15",
        direct_scaffold_warhead_boundaries=(("C14", "C15", "SING"),),
        explicit_graph_bonds=structural["bonds"],
    )
    boundary = result.direct_scaffold_warhead_boundary
    if (
        result.role_profile != EXPECTED_ROLE_PROFILE
        or result.valid is not True
        or tuple(result.reasons) != ()
        or result.scaffold_count != 16
        or result.linker_count != 0
        or result.warhead_count != 9
        or result.scaffold_linker_boundary_applicable is not False
        or result.linker_warhead_boundary_applicable is not False
        or result.direct_scaffold_warhead_boundary_applicable is not True
        or boundary is None
        or boundary.boundary_valid is not True
        or boundary.scaffold_atom_id != "C14"
        or boundary.warhead_atom_id != "C15"
        or boundary.bond_order != "SING"
    ):
        _fail("PUBLISHED_DIRECT_RUNTIME_VALIDATION_FAILED")
    return {
        "validator": "validate_role_profile_v1",
        "valid": True,
        "reasons": [],
        "profile": EXPECTED_ROLE_PROFILE,
        "scaffold_count": 16,
        "linker_count": 0,
        "warhead_count": 9,
        "applicable_task_ids": [0, 3, 4],
        "direct_scaffold_warhead_boundary_applicable": True,
        "scaffold_linker_boundary_applicable": False,
        "linker_warhead_boundary_applicable": False,
        "direct_scaffold_warhead_boundary": {
            "scaffold_atom_id": "C14",
            "warhead_atom_id": "C15",
            "bond_order": "SING",
            "boundary_valid": True,
        },
    }


def _current_census_boundary(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    summary = _strict_json_loads(
        payloads[CENSUS_SUMMARY_RELATIVE], "CURRENT_WITH_CER_CENSUS_SUMMARY"
    )
    _strict_json_loads(
        payloads[CENSUS_MANIFEST_RELATIVE], "CURRENT_WITH_CER_CENSUS_MANIFEST"
    )
    try:
        rows = list(
            csv.DictReader(
                io.StringIO(payloads[CENSUS_MATRIX_RELATIVE].decode("utf-8"))
            )
        )
    except UnicodeDecodeError as error:
        raise FourM5IngestionSafetyError(
            "COVAPIE_4M5_INGESTION_V1_ERROR:CURRENT_CENSUS_UTF8_INVALID"
        ) from error
    if len(rows) != 1000 or len({row.get("canonical_event_id") for row in rows}) != 1000:
        _fail("CURRENT_CENSUS_UNIVERSE_DRIFT")
    expected_set = set(EXPECTED_EVENT_IDS)
    target_rows = [row for row in rows if row.get("canonical_event_id") in expected_set]
    unit_rows = [row for row in rows if row.get("review_unit_id") == EXPECTED_REVIEW_UNIT_ID]
    if (
        len(target_rows) != 4
        or len(unit_rows) != 4
        or {row.get("canonical_event_id") for row in target_rows} != expected_set
        or {row.get("canonical_event_id") for row in unit_rows} != expected_set
        or tuple(int(row["scaleup_rank"]) for row in target_rows) != EXPECTED_RANKS
    ):
        _fail("CURRENT_CENSUS_4M5_EXACT4_DRIFT")
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
    for row in target_rows:
        if any(row.get(key) != value for key, value in prior.items()):
            _fail("CURRENT_CENSUS_4M5_PRIOR_STATE_DRIFT")
    human = summary.get("human_review")
    if type(human) is not dict:
        _fail("CURRENT_CENSUS_HUMAN_REVIEW_COUNTS_MISSING")
    expected_counts = {
        "completed_positive_event_count": 103,
        "completed_positive_unit_count": 15,
        "completed_event_count": 131,
        "completed_unit_count": 20,
        "unreviewed_event_count": 207,
        "unreviewed_unit_count": 111,
    }
    for key, expected in expected_counts.items():
        _expect(human.get(key), expected, "CURRENT_CENSUS_COUNT_DRIFT:" + key)
    exact5 = summary.get("canonical_exact5")
    if type(exact5) is not dict:
        _fail("CURRENT_CENSUS_EXACT5_MISSING")
    for key, expected in (
        ("task_count", 5), ("B3_present", True), ("sixth_task_present", False)
    ):
        _expect(exact5.get(key), expected, "CURRENT_CENSUS_EXACT5_DRIFT:" + key)
    return {
        **expected_counts,
        "FOUR_M5_current_status": "CURRENTLY_UNREVIEWED",
        "FOUR_M5_human_review_completed": False,
        "FOUR_M5_event_count": 4,
        "FOUR_M5_chemistry_disposition": "UNRESOLVED",
        "FOUR_M5_task_relevance_disposition": "UNRESOLVED",
        "FOUR_M5_training_use_disposition": "UNRESOLVED",
        "FOUR_M5_formal_training_admitted": False,
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
    """Bind, parse, and independently validate the frozen 4M5 authority."""

    repo_root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    allowed = {
        POLICY_BINDING[0],
        STRUCTURAL_GRAPH_BINDING[0],
        *(binding[0] for binding in FORMAL_BINDINGS),
        *(binding[0] for binding in SEMANTIC_OWNER_BINDINGS),
        *(binding[0] for binding in CENSUS_BINDINGS),
    }
    if set(overrides) - allowed:
        _fail("SOURCE_OVERRIDE_NOT_AUTHORIZED")
    _verify_binding(repo_root, POLICY_BINDING, overrides)
    formal_payloads = _verify_bindings(repo_root, FORMAL_BINDINGS, overrides)
    semantic_payloads = _verify_bindings(
        repo_root, SEMANTIC_OWNER_BINDINGS, overrides
    )
    structural_payload = _verify_binding(
        repo_root, STRUCTURAL_GRAPH_BINDING, overrides
    )
    census_payloads = _verify_bindings(repo_root, CENSUS_BINDINGS, overrides)
    formal = _strict_json_loads(
        formal_payloads[FORMAL_DECISION_RELATIVE],
        "FOUR_M5_FROZEN_FORMAL_DECISION",
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
            key: value
            for key, value in structural_validation.items()
            if key not in {"atom_ids", "bonds"}
        },
        "published_DIRECT_runtime_validation": runtime_validation,
        "current_census_boundary": census_boundary,
        "formal_semantics_independently_validated": True,
        "formal": formal,
    }


def _pair_authority_boundary() -> dict[str, object]:
    return {
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C15",
        "reactive_pair_human_decision_available": True,
        "reactive_pair_human_authoritative": True,
        "authority_scope": PAIR_AUTHORITY_SCOPE,
        "cross_structure_regiochemistry_generalization": False,
        "all_4M5_uses_C15": False,
        "all_17_oxoDHA_uses_C15": False,
        "all_PPAR_17_oxoDHA_pairs_use_C15": False,
        "reusable_pair_rule_created": False,
    }


def _chemistry_boundary() -> dict[str, object]:
    return {
        "human_task_relevance_decision": "RELEVANT",
        "task_relevance_human_authoritative": True,
        "human_chemistry_decision": "POSITIVE",
        "chemistry_known_positive": True,
        "chemistry_human_authoritative": True,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "reaction_family_authority": False,
        "warhead_rule_authority": False,
        "warhead_type_authority": False,
        "reusable_chemistry_authority": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "human_training_use_disposition": "INCLUDE",
        "training_use_human_authoritative": True,
        "future_training_admission_candidate": True,
        "future_training_admission_status": FUTURE_STATUS,
        "formal_training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed": False,
        "formal_split_authority": False,
        "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "ready_for_training": False,
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
        "PRE_reconstruction_performed": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_zero_fill_performed": False,
        "leaving_group_inferred": False,
        "reagent_inferred": False,
        "pre_reaction_bond_edit_inferred": False,
    }


def _free_ligand_boundary() -> dict[str, object]:
    return {
        "PDB_component_representation_is_not_authoritative_PRE_free_ligand_topology": True,
        "frozen_CCD_modified": False,
        "corrected_PRE_graph_synthesized": False,
        "observed_C15_pair_authority_altered": False,
    }


def _post_boundary() -> dict[str, object]:
    return {
        "POST_source_evidence_available": True,
        "POST_source_evidence_count": 4,
        "explicit_covalent_evidence": True,
        "distance_only_inference": False,
        "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
    }


def _reusable_authority_boundary() -> dict[str, object]:
    return {
        "reusable_chemistry_authority": False,
        "reusable_pair_authority": False,
        "reusable_role_authority": False,
        "reaction_family_authority": False,
        "warhead_rule_authority": False,
        "warhead_type_authority": False,
    }


def _authority_boundary() -> dict[str, object]:
    return {
        "authority_source": AUTHORITY_SOURCE,
        "pair_authority_scope": PAIR_AUTHORITY_SCOPE,
        "role_authority_scope": ROLE_AUTHORITY_SCOPE,
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
        "new_scientific_authority_created_by_ingestion": False,
        "formal_semantics_independently_validated": True,
        "frozen_formal_validator_imported": False,
        "frozen_formal_validator_executed": False,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "tensorization_performed": False,
        "model_forward_performed": False,
        "loss_executed": False,
        "backward_performed": False,
        "optimizer_step_performed": False,
        "parameter_update_performed": False,
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
        "sixth_task_present": False,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "direct_profile_applicable_task_count": 3,
        "task_applicability": applicability,
        "task_applicability_determined": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "D5_INCLUDE_does_not_create_authoritative_task_labels": True,
    }


def _role_projection(runtime_validation: Mapping[str, object]) -> dict[str, object]:
    return {
        "D4_human_choice": "SELECT_CANDIDATE_0",
        "selected_role_candidate_index_0based": 0,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "warhead_role_atom_ids": list(WARHEAD_ROLE),
        "linker_atom_ids": [],
        "scaffold_atom_ids": list(SCAFFOLD_ROLE),
        "boundary_bonds": list(BOUNDARY_BONDS),
        "warhead_atom_count": 9,
        "linker_atom_count": 0,
        "scaffold_atom_count": 16,
        "Exact25_count": 25,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "missing_atom_ids": [],
        "extra_atom_ids": [],
        "warhead_connected": True,
        "linker_connected_or_empty": True,
        "scaffold_connected": True,
        "reactive_C15_in_W": True,
        "published_DIRECT_runtime_validation": dict(runtime_validation),
        "sample_level_authoritative": True,
        "reusable": False,
        "authority_scope": ROLE_AUTHORITY_SCOPE,
    }


def _event_projection(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "canonical_event_id": row[0],
        "scaleup_rank": row[1],
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": row[2],
        "protein_context": row[10],
        "model_number": 1,
        "protein_chain_or_asym": row[3],
        "cys_residue_id": row[4],
        "protein_altloc": None,
        "ligand_component_id": "4M5",
        "ligand_chain_or_asym": row[5],
        "ligand_altloc": None,
        "selected_connection_id": row[6],
        "POST_distance_angstrom": row[7],
        "POST_distance_frozen_lexeme": row[8],
        "reported_POST_distance_angstrom": row[9],
        "human_review_completed": True,
        "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True,
        **_chemistry_boundary(),
        **_pair_authority_boundary(),
        **_training_boundary(),
        **_pre_boundary(),
        **_post_boundary(),
        **_reusable_authority_boundary(),
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    runtime = bound["published_DIRECT_runtime_validation"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": (
            "FOUR_M5_FROZEN_HUMAN_AUTHORITY_DETERMINISTIC_INGESTION_PROJECTION"
        ),
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
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
            "human_choices_externally_authorized": True,
            "machine_approval_claimed": False,
            "machine_scientific_authority_created": False,
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_candidate": "SELECT_CANDIDATE_0",
            "D5_training_use": "INCLUDE",
            "D6_scientific_context": EXPECTED_D6,
        },
        "D6_provenance": {
            "D6_draft_origin": "ASSISTANT_DRAFT_ACCEPTED_BY_HUMAN",
            "D6_human_reviewed_and_accepted": True,
            "D6_human_authorized": True,
            "D6_human_authored": False,
            "D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT,
            "D6_utf8_sha256": EXPECTED_D6_SHA256,
            "formal_decision_authority_is_human": True,
            "machine_scientific_authority_created": False,
            "assistant_draft_does_not_create_authority": True,
            "human_authorization_remains_authority_source": True,
        },
        "context_preservation": _expected_contexts(),
        "events": [_event_projection(row) for row in EXPECTED_EVENTS],
        "reactive_pair_authority": _pair_authority_boundary(),
        "chemistry_boundary": _chemistry_boundary(),
        "selected_role_partition": _role_projection(runtime),  # type: ignore[arg-type]
        "structural_validation": bound["structural_validation"],
        "canonical_task_contract": _canonical_task_contract(),
        "PRE_boundary": _pre_boundary(),
        "free_ligand_PDB_component_boundary": _free_ligand_boundary(),
        "POST_boundary": _post_boundary(),
        "training_boundary": _training_boundary(),
        "reusable_authority_boundary": _reusable_authority_boundary(),
        "current_census_boundary": bound["current_census_boundary"],
        "authority_boundary": _authority_boundary(),
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "review_unit_id", "pdb_id",
    "protein_context", "model_number", "protein_chain_or_asym",
    "cys_residue_id", "protein_altloc", "ligand_component_id",
    "ligand_chain_or_asym", "ligand_altloc", "selected_connection_id",
    "POST_distance_angstrom", "reported_POST_distance_angstrom",
    "human_review_completed", "human_task_relevance_decision",
    "task_relevance_human_authoritative", "human_chemistry_decision",
    "chemistry_known_positive", "chemistry_human_authoritative",
    "negative_chemistry", "task_domain_negative",
    "reactive_pair_human_decision_available",
    "reactive_pair_human_authoritative", "protein_reactive_atom",
    "ligand_reactive_atom", "pair_authority_scope",
    "cross_structure_regiochemistry_generalization", "all_4M5_uses_C15",
    "all_17_oxoDHA_uses_C15", "all_PPAR_17_oxoDHA_pairs_use_C15",
    "reusable_pair_rule_created", "role_partition_human_decision_available",
    "role_partition_human_authoritative",
    "selected_role_candidate_index_0based", "role_profile",
    "warhead_atoms_json", "linker_atoms_json", "scaffold_atoms_json",
    "W_L_S_counts_json", "boundary_bonds_json", "Exact25_count",
    "partition_pairwise_disjoint", "partition_exhaustive",
    "warhead_connected", "linker_connected_or_empty", "scaffold_connected",
    "reactive_C15_in_W", "role_authority_scope", "reusable_role_authority",
    "global_canonical_task_count", "canonical_task_applicability_json",
    "direct_profile_applicable_task_ids_json", "task_applicability_determined",
    "authoritative_task_labels_created", "event_task_label_rows_materialized",
    "human_training_use_disposition", "training_use_human_authoritative",
    "future_training_admission_candidate", "future_training_admission_status",
    "formal_training_admitted", "training_admission_created",
    "training_materialization_allowed", "formal_split_authority",
    "tensor_target_created", "current_runtime_model_usable",
    "parameter_update_authorization", "ready_for_training",
    "supporting_PRE_source_graph_count_per_event", "PRE_source_graph_present",
    "PRE_source_graph_count_per_event", "PRE_mapping_count_per_event",
    "PRE_mapping_status", "PRE_status", "PRE_topology_authority",
    "PRE_geometry_authority", "PRE_coordinates_authority",
    "PRE_reconstruction_performed", "POST_to_PRE_copy_performed",
    "PRE_zero_fill_performed", "leaving_group_inferred", "reagent_inferred",
    "pre_reaction_bond_edit_inferred",
    "PDB_component_representation_is_not_authoritative_PRE_free_ligand_topology",
    "frozen_CCD_modified", "corrected_PRE_graph_synthesized",
    "observed_C15_pair_authority_altered", "POST_source_evidence_available",
    "explicit_covalent_evidence", "distance_only_inference",
    "POST_geometry_training_authority",
    "POST_geometry_training_target_created", "reusable_chemistry_authority",
    "reaction_family_authority", "warhead_rule_authority",
    "warhead_type_authority", "authority_source",
    "projection_of_frozen_formal_human_authority",
    "new_human_authority_created_by_ingestion",
)


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    applicability = snapshot["canonical_task_contract"]["task_applicability"]
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        rows.append(
            {
                "canonical_event_id": event["canonical_event_id"],
                "scaleup_rank": str(event["scaleup_rank"]),
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
                "pdb_id": event["pdb_id"],
                "protein_context": event["protein_context"],
                "model_number": "1",
                "protein_chain_or_asym": event["protein_chain_or_asym"],
                "cys_residue_id": event["cys_residue_id"],
                "protein_altloc": "",
                "ligand_component_id": "4M5",
                "ligand_chain_or_asym": event["ligand_chain_or_asym"],
                "ligand_altloc": "",
                "selected_connection_id": event["selected_connection_id"],
                "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
                "reported_POST_distance_angstrom": str(
                    event["reported_POST_distance_angstrom"]
                ),
                "human_review_completed": "true",
                "human_task_relevance_decision": "RELEVANT",
                "task_relevance_human_authoritative": "true",
                "human_chemistry_decision": "POSITIVE",
                "chemistry_known_positive": "true",
                "chemistry_human_authoritative": "true",
                "negative_chemistry": "false",
                "task_domain_negative": "false",
                "reactive_pair_human_decision_available": "true",
                "reactive_pair_human_authoritative": "true",
                "protein_reactive_atom": "SG",
                "ligand_reactive_atom": "C15",
                "pair_authority_scope": PAIR_AUTHORITY_SCOPE,
                "cross_structure_regiochemistry_generalization": "false",
                "all_4M5_uses_C15": "false",
                "all_17_oxoDHA_uses_C15": "false",
                "all_PPAR_17_oxoDHA_pairs_use_C15": "false",
                "reusable_pair_rule_created": "false",
                "role_partition_human_decision_available": "true",
                "role_partition_human_authoritative": "true",
                "selected_role_candidate_index_0based": "0",
                "role_profile": EXPECTED_ROLE_PROFILE,
                "warhead_atoms_json": _json_cell(list(WARHEAD_ROLE)),
                "linker_atoms_json": "[]",
                "scaffold_atoms_json": _json_cell(list(SCAFFOLD_ROLE)),
                "W_L_S_counts_json": "[9,0,16]",
                "boundary_bonds_json": _json_cell(list(BOUNDARY_BONDS)),
                "Exact25_count": "25",
                "partition_pairwise_disjoint": "true",
                "partition_exhaustive": "true",
                "warhead_connected": "true",
                "linker_connected_or_empty": "true",
                "scaffold_connected": "true",
                "reactive_C15_in_W": "true",
                "role_authority_scope": ROLE_AUTHORITY_SCOPE,
                "reusable_role_authority": "false",
                "global_canonical_task_count": "5",
                "canonical_task_applicability_json": _json_cell(applicability),
                "direct_profile_applicable_task_ids_json": "[0,3,4]",
                "task_applicability_determined": "true",
                "authoritative_task_labels_created": "false",
                "event_task_label_rows_materialized": "false",
                "human_training_use_disposition": "INCLUDE",
                "training_use_human_authoritative": "true",
                "future_training_admission_candidate": "true",
                "future_training_admission_status": FUTURE_STATUS,
                "formal_training_admitted": "false",
                "training_admission_created": "false",
                "training_materialization_allowed": "false",
                "formal_split_authority": "false",
                "tensor_target_created": "false",
                "current_runtime_model_usable": "false",
                "parameter_update_authorization": "false",
                "ready_for_training": "false",
                "supporting_PRE_source_graph_count_per_event": "1",
                "PRE_source_graph_present": "true",
                "PRE_source_graph_count_per_event": "1",
                "PRE_mapping_count_per_event": "0",
                "PRE_mapping_status": PRE_MAPPING_STATUS,
                "PRE_status": PRE_STATUS,
                "PRE_topology_authority": "false",
                "PRE_geometry_authority": "false",
                "PRE_coordinates_authority": "false",
                "PRE_reconstruction_performed": "false",
                "POST_to_PRE_copy_performed": "false",
                "PRE_zero_fill_performed": "false",
                "leaving_group_inferred": "false",
                "reagent_inferred": "false",
                "pre_reaction_bond_edit_inferred": "false",
                "PDB_component_representation_is_not_authoritative_PRE_free_ligand_topology": "true",
                "frozen_CCD_modified": "false",
                "corrected_PRE_graph_synthesized": "false",
                "observed_C15_pair_authority_altered": "false",
                "POST_source_evidence_available": "true",
                "explicit_covalent_evidence": "true",
                "distance_only_inference": "false",
                "POST_geometry_training_authority": "false",
                "POST_geometry_training_target_created": "false",
                "reusable_chemistry_authority": "false",
                "reaction_family_authority": "false",
                "warhead_rule_authority": "false",
                "warhead_type_authority": "false",
                "authority_source": AUTHORITY_SOURCE,
                "projection_of_frozen_formal_human_authority": "true",
                "new_human_authority_created_by_ingestion": "false",
            }
        )
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "review_unit": "4M5",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ingested_event_count": 4,
        "human_completed_event_count": 4,
        "positive_chemistry_event_count": 4,
        "sample_pair_authority_event_count": 4,
        "role_authority_event_count": 4,
        "DIRECT_event_count": 4,
        "training_use_INCLUDE_event_count": 4,
        "future_training_admission_candidate_count": 4,
        "formal_training_admitted_count": 0,
        "canonical_Exact5_applicable_event_counts": {
            "warhead_only": 4,
            "linker_plus_warhead": 0,
            "scaffold_plus_warhead": 0,
            "scaffold_only": 4,
            "scaffold_plus_linker_plus_warhead": 4,
        },
        "applicable_task_set_counts": {"[0,3,4]": 4},
        "PRE_source_graph_present_event_count": 4,
        "PRE_mapping_available_event_count": 0,
        "PRE_authority_event_count": 0,
        "POST_source_evidence_event_count": 4,
        "POST_training_authority_event_count": 0,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "reusable_chemistry_authority_event_count": 0,
        "reusable_pair_authority_event_count": 0,
        "reusable_role_authority_event_count": 0,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "FOUR_M5_COMPLETED_DECISION_INGESTED": True,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
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
        raise FourM5IngestionSafetyError(
            "COVAPIE_4M5_INGESTION_V1_ERROR:UTF8_INVALID:" + label
        ) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TRAILING_WHITESPACE_INVALID:" + label)


def _reject_dynamic_or_forbidden_metadata(
    value: object, path: str = "root"
) -> None:
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
            raise FourM5IngestionSafetyError(
                "COVAPIE_4M5_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
                + relative.as_posix()
            ) from error
        _validate_text_payload(relative.as_posix(), payload)
        digest = _sha256(payload)
        try:
            verified = verify_bound_source_v2(
                path=path,
                expected_byte_count=len(payload),
                expected_sha256=digest,
                label="FOUR_M5_CANDIDATE_SOURCE:" + relative.as_posix(),
                expected_executable=False,
            )
        except SourceBindingPolicyV2Error as error:
            raise FourM5IngestionSafetyError(
                "COVAPIE_4M5_INGESTION_V1_ERROR:CANDIDATE_SOURCE_REJECTED:"
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


def _validate_candidate_source_bindings(value: object) -> None:
    expected_paths = [
        SOURCE_RELATIVE.as_posix(),
        CHECKER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
    ]
    if type(value) is not list or len(value) != 3:
        _fail("CANDIDATE_SOURCE_BINDINGS_INVALID")
    if [row.get("path") for row in value if type(row) is dict] != expected_paths:
        _fail("CANDIDATE_SOURCE_BINDING_PATHS_INVALID")
    for row in value:
        if (
            type(row) is not dict
            or set(row)
            != {
                "path", "namespace", "byte_count", "SHA256",
                "expected_executable_class", "source_role",
            }
            or row.get("namespace") != "repository_relative"
            or type(row.get("byte_count")) is not int
            or row["byte_count"] <= 0
            or type(row.get("SHA256")) is not str
            or len(row["SHA256"]) != 64
            or row.get("expected_executable_class") != "NON_EXECUTABLE"
        ):
            _fail("CANDIDATE_SOURCE_BINDING_SHAPE_INVALID")


def _expected_runtime_validation() -> dict[str, object]:
    return {
        "validator": "validate_role_profile_v1",
        "valid": True,
        "reasons": [],
        "profile": EXPECTED_ROLE_PROFILE,
        "scaffold_count": 16,
        "linker_count": 0,
        "warhead_count": 9,
        "applicable_task_ids": [0, 3, 4],
        "direct_scaffold_warhead_boundary_applicable": True,
        "scaffold_linker_boundary_applicable": False,
        "linker_warhead_boundary_applicable": False,
        "direct_scaffold_warhead_boundary": {
            "scaffold_atom_id": "C14",
            "warhead_atom_id": "C15",
            "bond_order": "SING",
            "boundary_valid": True,
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
        "structural_validation": {
            "Exact25_count": 25,
            "partition_pairwise_disjoint": True,
            "partition_exhaustive": True,
            "missing_atom_ids": [],
            "extra_atom_ids": [],
            "W_connected": True,
            "L_connected_or_empty": True,
            "S_connected": True,
            "C15_in_W": True,
            "boundary": "C14-C15 SING S-W",
        },
        "published_DIRECT_runtime_validation": _expected_runtime_validation(),
        "current_census_boundary": {
            "completed_positive_event_count": 103,
            "completed_positive_unit_count": 15,
            "completed_event_count": 131,
            "completed_unit_count": 20,
            "unreviewed_event_count": 207,
            "unreviewed_unit_count": 111,
            "FOUR_M5_current_status": "CURRENTLY_UNREVIEWED",
            "FOUR_M5_human_review_completed": False,
            "FOUR_M5_event_count": 4,
            "FOUR_M5_chemistry_disposition": "UNRESOLVED",
            "FOUR_M5_task_relevance_disposition": "UNRESOLVED",
            "FOUR_M5_training_use_disposition": "UNRESOLVED",
            "FOUR_M5_formal_training_admitted": False,
            "reconciliation_performed": False,
            "census_refreshed": False,
            "queue_updated": False,
        },
    }


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
        "artifact_role": (
            "FOUR_M5_COMPLETED_DECISION_INGESTION_"
            "NOT_RECONCILIATION_OR_TASK_LABEL_MATERIALIZATION_OR_ADMISSION"
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
        "candidate_source_bindings": candidate_source_bindings,
        "formal_semantic_canonical_sha256": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_semantics_independently_validated": True,
        "frozen_formal_validator_provenance_identity_only": True,
        "frozen_formal_validator_imported": False,
        "frozen_formal_validator_executed": False,
        "formal_validator_runtime_dependency": False,
        "structural_validation": bound["structural_validation"],
        "published_DIRECT_runtime_validation": (
            bound["published_DIRECT_runtime_validation"]
        ),
        "canonical_task_contract": _canonical_task_contract(),
        "formal_projection": {
            "D1": "RELEVANT",
            "D2": "POSITIVE",
            "D3": "CONFIRM_OBSERVED_PAIR",
            "D4": "SELECT_CANDIDATE_0",
            "D5": "INCLUDE",
            "D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT,
            "D6_utf8_sha256": EXPECTED_D6_SHA256,
            "event_count": 4,
            "contexts_collapsed": False,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "W_L_S_counts": [9, 0, 16],
            "boundary": "C14-C15 SING",
            "applicable_task_ids": [0, 3, 4],
        },
        "reactive_pair_authority": _pair_authority_boundary(),
        "chemistry_boundary": _chemistry_boundary(),
        "selected_role_partition": _role_projection(
            bound["published_DIRECT_runtime_validation"]  # type: ignore[arg-type]
        ),
        "PRE_boundary": _pre_boundary(),
        "free_ligand_PDB_component_boundary": _free_ligand_boundary(),
        "POST_boundary": _post_boundary(),
        "reusable_authority_boundary": _reusable_authority_boundary(),
        "training_boundary": _training_boundary(),
        "authority_projection_boundary": _authority_boundary(),
        "operation_boundary": {
            "INGESTION_COMPLETE": True,
            "RECONCILIATION": False,
            "CENSUS_REFRESH": False,
            "QUEUE_REFRESH": False,
            "tensorization": False,
            "model_forward": False,
            "loss": False,
            "backward": False,
            "optimizer": False,
            "parameter_update": False,
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
        "numeric_POSIX_semantic_identity": False,
        "expected_executable_safety_class_used": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "new_human_authority_created_by_ingestion": False,
        "projection_of_frozen_formal_human_authority": True,
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
    """Validate the deterministic 4M5 projection and authority boundaries."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    snapshot = _strict_json_loads(artifacts[SNAPSHOT], "SNAPSHOT")
    summary = _strict_json_loads(artifacts[SUMMARY], "SUMMARY")
    manifest = _strict_json_loads(artifacts[MANIFEST], "MANIFEST")
    try:
        matrix = list(
            csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8")))
        )
    except UnicodeDecodeError as error:
        raise FourM5IngestionSafetyError(
            "COVAPIE_4M5_INGESTION_V1_ERROR:MATRIX_UTF8_INVALID"
        ) from error
    for document in (snapshot, summary, manifest):
        _reject_dynamic_or_forbidden_metadata(document)
    standalone = _standalone_bound()
    _expect(snapshot, _snapshot(standalone), "SNAPSHOT_EXACT_PROJECTION_INVALID")
    _expect(summary, _summary(), "SUMMARY_EXACT_COUNTS_INVALID")
    if (list(matrix[0]) if matrix else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    expected_matrix = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    if artifacts[MATRIX] != expected_matrix:
        _fail("MATRIX_EXACT_PROJECTION_INVALID")
    if (
        len(matrix) != 4
        or tuple(row["canonical_event_id"] for row in matrix) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in matrix) != EXPECTED_RANKS
        or len({row["canonical_event_id"] for row in matrix}) != 4
        or tuple(row["pdb_id"] for row in matrix)
        != ("5AZT", "5AZT", "5AZV", "5AZV")
        or tuple(row["protein_context"] for row in matrix)
        != ("PPARalpha", "PPARalpha", "PPARgamma", "PPARgamma")
    ):
        _fail("MATRIX_EXACT4_IDENTITY_OR_CONTEXT_INVALID")
    for row in matrix:
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["review_unit_id"] != EXPECTED_REVIEW_UNIT_ID
            or row["human_review_completed"] != "true"
            or row["human_task_relevance_decision"] != "RELEVANT"
            or row["task_relevance_human_authoritative"] != "true"
            or row["human_chemistry_decision"] != "POSITIVE"
            or row["chemistry_human_authoritative"] != "true"
            or row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "C15"
            or row["pair_authority_scope"] != PAIR_AUTHORITY_SCOPE
            or row["cross_structure_regiochemistry_generalization"] != "false"
            or row["all_4M5_uses_C15"] != "false"
            or row["all_17_oxoDHA_uses_C15"] != "false"
            or row["all_PPAR_17_oxoDHA_pairs_use_C15"] != "false"
            or row["reusable_pair_rule_created"] != "false"
            or row["selected_role_candidate_index_0based"] != "0"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or json.loads(row["warhead_atoms_json"]) != list(WARHEAD_ROLE)
            or json.loads(row["linker_atoms_json"]) != []
            or json.loads(row["scaffold_atoms_json"]) != list(SCAFFOLD_ROLE)
            or row["W_L_S_counts_json"] != "[9,0,16]"
            or json.loads(row["boundary_bonds_json"]) != list(BOUNDARY_BONDS)
            or row["Exact25_count"] != "25"
            or row["partition_pairwise_disjoint"] != "true"
            or row["partition_exhaustive"] != "true"
            or row["warhead_connected"] != "true"
            or row["linker_connected_or_empty"] != "true"
            or row["scaffold_connected"] != "true"
            or row["reactive_C15_in_W"] != "true"
            or row["role_authority_scope"] != ROLE_AUTHORITY_SCOPE
            or row["reusable_role_authority"] != "false"
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or [
                item["task_id"]
                for item in applicability
                if item["structurally_applicable"]
            ]
            != [0, 3, 4]
            or row["task_applicability_determined"] != "true"
            or row["authoritative_task_labels_created"] != "false"
            or row["event_task_label_rows_materialized"] != "false"
            or row["human_training_use_disposition"] != "INCLUDE"
            or row["future_training_admission_candidate"] != "true"
            or row["formal_training_admitted"] != "false"
            or row["training_materialization_allowed"] != "false"
            or row["ready_for_training"] != "false"
            or row["supporting_PRE_source_graph_count_per_event"] != "1"
            or row["PRE_source_graph_present"] != "true"
            or row["PRE_source_graph_count_per_event"] != "1"
            or row["PRE_mapping_count_per_event"] != "0"
            or row["PRE_mapping_status"] != PRE_MAPPING_STATUS
            or row["PRE_status"] != PRE_STATUS
            or row["PRE_topology_authority"] != "false"
            or row["PRE_geometry_authority"] != "false"
            or row["PRE_coordinates_authority"] != "false"
            or row["PRE_reconstruction_performed"] != "false"
            or row["POST_to_PRE_copy_performed"] != "false"
            or row["PRE_zero_fill_performed"] != "false"
            or row["PDB_component_representation_is_not_authoritative_PRE_free_ligand_topology"]
            != "true"
            or row["corrected_PRE_graph_synthesized"] != "false"
            or row["POST_source_evidence_available"] != "true"
            or row["explicit_covalent_evidence"] != "true"
            or row["distance_only_inference"] != "false"
            or row["POST_geometry_training_authority"] != "false"
            or row["POST_geometry_training_target_created"] != "false"
            or row["reusable_chemistry_authority"] != "false"
            or row["reaction_family_authority"] != "false"
            or row["warhead_rule_authority"] != "false"
            or row["warhead_type_authority"] != "false"
            or row["new_human_authority_created_by_ingestion"] != "false"
        ):
            _fail("MATRIX_AUTHORITY_TASK_PRE_OR_POST_BOUNDARY_INVALID")
    candidate_bindings = manifest.get("candidate_source_bindings")
    _validate_candidate_source_bindings(candidate_bindings)
    expected_manifest = _manifest(
        standalone,
        candidate_bindings,  # type: ignore[arg-type]
        artifacts[SNAPSHOT],
        artifacts[MATRIX],
        artifacts[SUMMARY],
    )
    _expect(manifest, expected_manifest, "MANIFEST_CLOSURE_INVALID")
    if repo_root is not None:
        expected = _build_artifacts_unvalidated(Path(repo_root).resolve())
        if dict(artifacts) != expected:
            _fail("DIRECT_SOURCE_DERIVED_PROJECTION_INVALID")


def build_artifacts_v1(repo_root: Path) -> dict[str, bytes]:
    """Build pure, deterministic bytes for the four authorized outputs."""

    artifacts = _build_artifacts_unvalidated(Path(repo_root).resolve())
    validate_completed_decision_projection_v1(artifacts)
    return artifacts


def _validate_materialization_destination_v1(target_root: Path) -> None:
    try:
        root_metadata = target_root.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise FourM5IngestionSafetyError(
            "COVAPIE_4M5_INGESTION_V1_ERROR:OUTPUT_ROOT_LSTAT_FAILED"
        ) from error
    if stat.S_ISLNK(root_metadata.st_mode):
        _fail("OUTPUT_ROOT_SYMLINK_FORBIDDEN")
    if not stat.S_ISDIR(root_metadata.st_mode):
        _fail("OUTPUT_ROOT_NOT_DIRECTORY")
    try:
        entries = tuple(target_root.iterdir())
    except OSError as error:
        raise FourM5IngestionSafetyError(
            "COVAPIE_4M5_INGESTION_V1_ERROR:OUTPUT_ROOT_INVENTORY_READ_FAILED"
        ) from error
    unexpected = sorted(
        entry.name for entry in entries if entry.name not in OUTPUT_FILENAMES
    )
    if unexpected:
        _fail("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES")
    for entry in entries:
        try:
            entry_metadata = entry.lstat()
        except OSError as error:
            raise FourM5IngestionSafetyError(
                "COVAPIE_4M5_INGESTION_V1_ERROR:OUTPUT_ENTRY_LSTAT_FAILED:"
                + entry.name
            ) from error
        if stat.S_ISLNK(entry_metadata.st_mode) or not stat.S_ISREG(
            entry_metadata.st_mode
        ):
            _fail("OUTPUT_ENTRY_NOT_REGULAR:" + entry.name)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".atomic-write",
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
    """Write only the four deterministic 4M5 output artifacts."""

    repo_root = Path(repo_root).resolve()
    artifacts = build_artifacts_v1(repo_root)
    target_root = (
        Path(output_root)
        if output_root is not None
        else repo_root / OUTPUT_ROOT_RELATIVE
    )
    _validate_materialization_destination_v1(target_root)
    for name, payload in artifacts.items():
        _atomic_write(target_root / name, payload)
    return artifacts


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    """Compare materialized Exact4 outputs against a fresh deterministic build."""

    repo_root = Path(repo_root).resolve()
    expected = build_artifacts_v1(repo_root)
    output_root = repo_root / OUTPUT_ROOT_RELATIVE
    if not output_root.is_dir() or output_root.is_symlink():
        _fail("OUTPUT_ROOT_NOT_REGULAR_DIRECTORY")
    if tuple(sorted(path.name for path in output_root.iterdir())) != tuple(
        sorted(OUTPUT_FILENAMES)
    ):
        _fail("OUTPUT_INVENTORY_NOT_EXACT4")
    actual: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = output_root / name
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise FourM5IngestionSafetyError(
                "COVAPIE_4M5_INGESTION_V1_ERROR:OUTPUT_READ_FAILED:" + name
            ) from error
        try:
            verified = verify_bound_source_v2(
                path=path,
                expected_byte_count=len(payload),
                expected_sha256=_sha256(payload),
                label="FOUR_M5_MATERIALIZED_OUTPUT:" + name,
                expected_executable=False,
            )
        except SourceBindingPolicyV2Error as error:
            raise FourM5IngestionSafetyError(
                "COVAPIE_4M5_INGESTION_V1_ERROR:OUTPUT_REJECTED:" + name
            ) from error
        actual[name] = verified
    validate_completed_decision_projection_v1(actual, repo_root=repo_root)
    if actual != expected:
        _fail("MATERIALIZED_OUTPUT_BYTES_DRIFT")
    return {
        "status": "PASS",
        "schema_version": SCHEMA_VERSION,
        "exact_output_count": 4,
        "event_count": 4,
        "deterministic": True,
        "FOUR_M5_COMPLETED_DECISION_INGESTED": True,
        "FOUR_M5_FORMAL_VALIDATOR_PROVENANCE_ONLY": True,
        "FOUR_M5_FORMAL_SEMANTICS_INDEPENDENTLY_VALIDATED": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "FORMAL_TRAINING_ADMITTED": False,
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
