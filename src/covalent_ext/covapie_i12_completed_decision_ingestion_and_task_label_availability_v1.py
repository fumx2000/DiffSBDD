"""Project frozen I12 human authority into deterministic ingestion metadata.

This owner consumes an already-finalized sample-level decision.  It creates no
human or reusable chemistry authority, does not reconcile or refresh the
global census, and does not admit, tensorize, or train any sample.  The frozen
formal validator is bound as provenance bytes only and is never imported or
executed here.
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
    "I12IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)


SCHEMA_VERSION = "covapie_i12_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_i12_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_i12_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_i12_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_i12_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_i12_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_i12_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_i12_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_i12_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_i12_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_i12_event_task_label_availability_v1.csv"
SUMMARY = "covapie_i12_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_i12_completed_decision_ingestion_manifest_v1.json"
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
    "I12_COVAPIE_BULK_REVIEW_UNIT_7D83F048AF8A2295/"
    "formal-human-decision-v1"
)
FORMAL_DECISION_RELATIVE = FORMAL_ROOT / "i12_formal_human_decision_v1.json"
FORMAL_VALIDATOR_RELATIVE = FORMAL_ROOT / "validate_i12_formal_human_decision_v1.py"

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
    "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1.py"
)
CENSUS_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1"
)
CENSUS_MATRIX_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1.csv"
)
CENSUS_SUMMARY_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_summary_with_2a2_v1.json"
)
CENSUS_MANIFEST_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_manifest_with_2a2_v1.json"
)

FORMAL_DECISION_SCHEMA = "covapie_i12_exact4_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "74b60a1dba0c706471a0a051b95bf8ab82bbe56490f44046319ef100a5e39a40"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_7D83F048AF8A2295"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
EXPECTED_APPROVED_AT_UTC = "2026-08-31T14:33:26Z"
EXPECTED_D6 = (
    "I12 is a peptidomimetic coronavirus Mpro covalent inhibitor represented "
    "by four explicit Cys-SG–C21 covalent events across 1WOF and 2AMP. C21 is "
    "the β-carbon of an ethyl α,β-unsaturated ester electrophilic warhead. The "
    "P1 γ-lactam-containing recognition moiety is retained as scaffold, "
    "supporting the direct-attachment role partition (Candidate 0) rather than "
    "assigning the P1 recognition element to linker. The Acrylate annotation "
    "is supporting evidence only and is not promoted to reusable "
    "reaction-family authority. PRE source graph mapping is incompatible and "
    "therefore no authoritative PRE topology or geometry is inferred; "
    "observed POST structural evidence is retained independently."
)

AUTHORITY_SOURCE = "FORMAL_I12_HUMAN_DECISION"
AUTHORITY_SCOPE = "I12_EXACT4_SAMPLE_LEVEL_ONLY"
FUTURE_STATUS = "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"
PRE_STATUS = "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"

EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:1WOF:A:CYS:145-:SG:C:I12:C21",
        187,
        "1WOF",
        "A",
        "CYS:145-",
        "C",
        "covale1",
        1.810632,
        "1.810632",
        1.811,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:1WOF:B:CYS:145-:SG:D:I12:C21",
        188,
        "1WOF",
        "B",
        "CYS:145-",
        "D",
        "covale2",
        1.803620,
        "1.803620",
        1.804,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:2AMP:A:CYS:144-:SG:C:I12:C21",
        222,
        "2AMP",
        "A",
        "CYS:144-",
        "C",
        "covale1",
        1.810317,
        "1.810317",
        1.810,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:2AMP:B:CYS:144-:SG:D:I12:C21",
        223,
        "2AMP",
        "B",
        "CYS:144-",
        "D",
        "covale2",
        1.821774,
        "1.821774",
        1.822,
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)

WARHEAD_ROLE = ("C21", "C22", "C23", "C24", "C25", "O6", "O7")
LINKER_ROLE: tuple[str, ...] = ()
SCAFFOLD_ROLE = (
    "C1", "C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17",
    "C18", "C19", "C2", "C20", "C26", "C27", "C28", "C29", "C3",
    "C30", "C4", "C5", "C6", "C7", "C8", "C9", "N1", "N2", "N3",
    "N4", "N5", "N6", "O1", "O2", "O3", "O4", "O5", "O8",
)
HEAVY_ATOMS = tuple((*WARHEAD_ROLE, *LINKER_ROLE, *SCAFFOLD_ROLE))
BOUNDARY_BONDS = (
    {
        "atom_id_1": "C20",
        "atom_id_2": "C21",
        "bond_order": "SING",
        "boundary_between_roles": ["scaffold", "warhead"],
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
DIRECT_VALID_TASK_IDS = (0, 3, 4)
DIRECT_APPLICABILITY = (
    (0, "warhead_only", "A", True, "generate_W_condition_on_S"),
    (1, "linker_plus_warhead", "B", False, "not_applicable_empty_linker_redundant_with_A"),
    (2, "scaffold_plus_warhead", "B2", False, "not_applicable_empty_non_C_fixed_context"),
    (3, "scaffold_only", "B3", True, "generate_S_condition_on_W"),
    (4, "scaffold_plus_linker_plus_warhead", "C", True, "generate_whole_ligand_preserve_Task_C_seed_semantics"),
)

# path, namespace, byte count, SHA256, expected executable, source role
FORMAL_BINDINGS = (
    (
        FORMAL_DECISION_RELATIVE,
        "project_parent_relative",
        26474,
        "e117da5c10c45603450eaab26ea6093ef07e70c4bf2ec2f0c7908aa38f531fa0",
        False,
        "I12_FROZEN_FORMAL_HUMAN_DECISION",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE,
        "project_parent_relative",
        65800,
        "05e1c27216b9f1e05b1f7114ff86f3103679931207344e44fd585fe097270f85",
        False,
        "I12_FROZEN_FORMAL_VALIDATOR_PROVENANCE_IDENTITY_ONLY",
    ),
)
SEMANTIC_OWNER_BINDINGS = (
    (
        DIRECT_RUNTIME_OWNER_RELATIVE,
        "repository_relative",
        37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        False,
        "PUBLISHED_DIRECT_ROLE_RUNTIME_SEMANTIC_OWNER",
    ),
    (
        CANONICAL_TASK_OWNER_RELATIVE,
        "repository_relative",
        67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        False,
        "PUBLISHED_CANONICAL_EXACT5_SEMANTIC_OWNER",
    ),
)
CENSUS_BINDINGS = (
    (
        CENSUS_OWNER_RELATIVE,
        "repository_relative",
        65504,
        "e27b71b0007cd09083b87a40fa2c9474285c479ed20f7300167a3da0d6bbcdc5",
        False,
        "CURRENT_2A2_GLOBAL_CENSUS_OWNER",
    ),
    (
        CENSUS_MATRIX_RELATIVE,
        "repository_relative",
        529994,
        "5b56422e9c8d0ec6c09fe71c49d51fff0c7e7a9720ccf3c4c20dc324e409c57d",
        False,
        "CURRENT_2A2_GLOBAL_CENSUS_MATRIX",
    ),
    (
        CENSUS_SUMMARY_RELATIVE,
        "repository_relative",
        17389,
        "3217bf5e45de40e66f1af22d000a48fef81548c6431c3e6d9349c4824b1c80f3",
        False,
        "CURRENT_2A2_GLOBAL_CENSUS_SUMMARY",
    ),
    (
        CENSUS_MANIFEST_RELATIVE,
        "repository_relative",
        47068,
        "c30f8f52fc20495a06f7bead98ac80197f434eeb0b4776a1ef2c152f13d1e2b7",
        False,
        "CURRENT_2A2_GLOBAL_CENSUS_MANIFEST",
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

_Binding = tuple[Path, str, int, str, bool, str]
_FORBIDDEN_LIVE_IDENTITY_FIELDS = {
    "mode",
    "required_mode",
    "expected_mode",
    "filesystem_mode",
    "posix_mode",
}


class I12IngestionSafetyError(ValueError):
    """Raised when the frozen I12 ingestion contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise I12IngestionSafetyError("COVAPIE_I12_INGESTION_V1_ERROR:" + reason)


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
        raise I12IngestionSafetyError(
            "COVAPIE_I12_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label
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
            text,
            object_pairs_hook=pairs_hook,
            parse_constant=reject_constant,
        )
    except json.JSONDecodeError as error:
        raise I12IngestionSafetyError(
            "COVAPIE_I12_INGESTION_V1_ERROR:JSON_PARSE_FAILED:" + label
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
        raise I12IngestionSafetyError(
            "COVAPIE_I12_INGESTION_V1_ERROR:BOUND_SOURCE_REJECTED:"
            + source_role
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
        raise I12IngestionSafetyError(
            "COVAPIE_I12_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
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
                    raise I12IngestionSafetyError(
                        "COVAPIE_I12_INGESTION_V1_ERROR:"
                        "SEMANTIC_OWNER_LITERAL_INVALID:"
                        + target.id
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
    _expect(canonical["EXACT3_ROLES"], ("scaffold", "linker", "warhead"), "EXACT3_ROLE_OWNER_DRIFT")
    _expect(canonical["CANONICAL_TASKS"], CANONICAL_TASKS, "CANONICAL_EXACT5_OWNER_DRIFT")
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


def _expected_formal_events() -> list[dict[str, object]]:
    return [
        {
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_partition": "SELECT_CANDIDATE_0",
            "D5_training_use": "INCLUDE",
            "D6_context_reference": "UNIT_LEVEL_EXACT_AUTHORIZED_D6",
            "POST_distance_angstrom": row[7],
            "POST_sample_authority": False,
            "POST_source_evidence": True,
            "POST_training_target_authority": False,
            "canonical_event_id": row[0],
            "chemistry_human_authoritative": True,
            "cys_residue_id": row[4],
            "distance_only_inference_used": False,
            "event_specific_exception": False,
            "explicit_covalent_evidence": True,
            "formal_training_admitted": False,
            "ligand_asym": row[5],
            "ligand_component_id": "I12",
            "ligand_reactive_atom": "C21",
            "model_number": 1,
            "pdb_id": row[2],
            "protein_asym": row[3],
            "protein_reactive_atom": "SG",
            "reactive_pair_human_authoritative": True,
            "reported_POST_distance_angstrom": row[9],
            "role_partition_human_authoritative": True,
            "scaleup_rank": row[1],
            "selected_connection_id": row[6],
            "task_relevance_human_authoritative": True,
            "training_use_human_authoritative": True,
        }
        for row in EXPECTED_EVENTS
    ]


def _expected_formal_role() -> dict[str, object]:
    return {
        "D4_human_choice": "SELECT_CANDIDATE_0",
        "applicable_semantic_names": [
            "warhead_only",
            "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
        ],
        "applicable_task_ids": [0, 3, 4],
        "authority_scope": AUTHORITY_SCOPE,
        "boundary_bonds": [
            {
                "aromatic_flag": "N",
                "atom_id_1": "C20",
                "atom_id_2": "C21",
                "bond_order": "SING",
                "role_1": "S",
                "role_2": "W",
            }
        ],
        "candidate_8_created": False,
        "candidate_index_is_ranking": False,
        "candidate_index_is_score": False,
        "human_selected": True,
        "human_selected_role_candidate_index_0based": 0,
        "independent_structural_validation": {
            "Exact44_count": 44,
            "L_connected_or_empty": True,
            "L_count": 0,
            "S_connected": True,
            "S_count": 37,
            "W_connected": True,
            "W_count": 7,
            "direct_boundary_exists": True,
            "exhaustive": True,
            "extra_atom_ids": [],
            "missing_atom_ids": [],
            "pairwise_disjoint": True,
            "reactive_C21_in_W": True,
        },
        "linker_atom_ids": [],
        "linker_role_connected_or_empty": True,
        "machine_recommended": False,
        "machine_recommended_candidate": None,
        "machine_selected": False,
        "partition_exhaustive": True,
        "partition_heavy_atom_count": 44,
        "partition_pairwise_disjoint": True,
        "published_role_runtime_validation": {
            "applicable_task_ids": [0, 3, 4],
            "direct_scaffold_warhead_boundary": {
                "bond_order": "SING",
                "boundary_valid": True,
                "scaffold_atom_id": "C20",
                "warhead_atom_id": "C21",
            },
            "direct_scaffold_warhead_boundary_applicable": True,
            "linker_count": 0,
            "linker_warhead_boundary_applicable": False,
            "profile": EXPECTED_ROLE_PROFILE,
            "reasons": [],
            "scaffold_count": 37,
            "scaffold_linker_boundary_applicable": False,
            "valid": True,
            "validator": "validate_role_profile_v1",
            "warhead_count": 7,
        },
        "reactive_atom_in_warhead_role": True,
        "reactive_ligand_atom": "C21",
        "retained_heavy_atom_count": 44,
        "role_counts": {"linker": 0, "scaffold": 37, "warhead": 7},
        "role_profile": EXPECTED_ROLE_PROFILE,
        "scaffold_atom_ids": list(SCAFFOLD_ROLE),
        "scaffold_role_connected": True,
        "selected_candidate_index_0based": 0,
        "semantic_boundaries": {
            "direct_scaffold_warhead": {
                "bond_order": "SING",
                "endpoint_set": ["C20", "C21"],
            }
        },
        "warhead_role_atom_ids": list(WARHEAD_ROLE),
        "warhead_role_connected": True,
    }


def _canonical_task_contract() -> dict[str, object]:
    applicability = [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "structurally_applicable": task_id in DIRECT_VALID_TASK_IDS,
            "role_profile": EXPECTED_ROLE_PROFILE,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
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
        "D5_INCLUDE_does_not_change_structural_applicability": True,
    }


def _validate_formal_document(formal: Mapping[str, Any]) -> None:
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
        ("approved", True),
        ("unsigned", False),
        ("decision_finalized", True),
        ("human_review_completed", True),
        ("formal_authority_created", True),
        ("human_decision_created", True),
    ):
        _expect(formal.get(key), expected, "FORMAL_FINALIZATION_DRIFT:" + key)

    _expect(
        formal.get("human_approval"),
        {
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_partition": "SELECT_CANDIDATE_0",
            "D5_training_use": "INCLUDE",
            "D6_scientific_context": EXPECTED_D6,
            "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
            "attestor_id": "fmx",
            "authorization_source": "EXTERNAL_HUMAN_CHAT_AUTHORIZATION",
            "chat_cryptographic_verification_claimed": False,
            "human_choices_externally_authorized": True,
            "human_selected_role_candidate_index_0based": 0,
            "human_selected_role_profile": EXPECTED_ROLE_PROFILE,
            "machine_approval_claimed": False,
            "reviewer_id": "fmx",
        },
        "FORMAL_D1_D6_OR_APPROVAL_DRIFT",
    )
    _expect(
        formal.get("human_approved_context"),
        {
            "D6_scientific_context": EXPECTED_D6,
            "D6_source": "EXTERNAL_HUMAN_CHAT_AUTHORIZATION",
            "exact_text_frozen": True,
            "formal_D6_equals_externally_authorized_text": True,
        },
        "FORMAL_D6_CONTEXT_DRIFT",
    )
    _expect(
        formal.get("identity"),
        {
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "duplicate_event_count": 0,
            "event_contexts_collapsed": False,
            "exact_event_count": 4,
            "extra_event_count": 0,
            "ligand_component_id": "I12",
            "missing_event_count": 0,
            "pdb_ids": ["1WOF", "2AMP"],
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scaleup_ranks": list(EXPECTED_RANKS),
            "unique_event_count": 4,
        },
        "FORMAL_EXACT4_IDENTITY_DRIFT",
    )
    _expect(
        formal.get("event_level_human_decisions"),
        _expected_formal_events(),
        "FORMAL_EVENT_DECISION_OR_EVIDENCE_DRIFT",
    )
    role = formal.get("selected_role_partition")
    _expect(role, _expected_formal_role(), "FORMAL_CANDIDATE0_ROLE_DRIFT")
    if (
        len(HEAVY_ATOMS) != 44
        or len(set(HEAVY_ATOMS)) != 44
        or set(WARHEAD_ROLE) & set(SCAFFOLD_ROLE)
        or set(WARHEAD_ROLE) & set(LINKER_ROLE)
        or set(SCAFFOLD_ROLE) & set(LINKER_ROLE)
        or "C21" not in WARHEAD_ROLE
        or "C20" not in SCAFFOLD_ROLE
    ):
        _fail("INTERNAL_EXACT44_ROLE_PARTITION_INVALID")

    expected_formal_tasks = [
        {
            "display_alias": alias,
            "semantic_name": semantic,
            "structurally_applicable_to_I12": task_id in DIRECT_VALID_TASK_IDS,
            "task_id": task_id,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]
    _expect(
        formal.get("canonical_Exact5_and_sample_applicability"),
        {
            "B3_present": True,
            "I12_authoritative_task_labels_created": False,
            "I12_role_profile_task_applicability_determined": True,
            "event_task_label_rows_materialized": False,
            "global_canonical_task_count": 5,
            "sample_applicable_semantic_names": [
                "warhead_only",
                "scaffold_only",
                "scaffold_plus_linker_plus_warhead",
            ],
            "sample_applicable_task_ids": [0, 3, 4],
            "sixth_task_present": False,
            "tasks": expected_formal_tasks,
        },
        "FORMAL_CANONICAL_EXACT5_DRIFT",
    )
    _expect(
        formal.get("training_use_human_decision"),
        {
            "D5_human_choice": "INCLUDE",
            "POST_geometry_training_target_authority": False,
            "candidate_for_future_training_admission": True,
            "chemistry": "POSITIVE",
            "completed_decision_ingested": False,
            "completed_decision_ingestion_started": False,
            "current_runtime_model_usable": False,
            "downstream_eligible_data_pool_inclusion_human_authorized": True,
            "feature_semantics_finalized": False,
            "formal_split_authority_created": False,
            "formal_training_admitted": False,
            "human_training_excluded": False,
            "parameter_update_authorization": False,
            "task_relevance": "RELEVANT",
            "tensor_target_created": False,
            "training_admission_created": False,
            "training_materialization_allowed_now": False,
        },
        "FORMAL_D5_OR_TRAINING_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("experimental_context_and_PRE_boundary"),
        {
            "POST_to_PRE_copy_performed": False,
            "PRE_geometry_authority_created": False,
            "PRE_mapped_graph_authority_created": False,
            "PRE_mapping_repair_performed": False,
            "PRE_source_graph_exists": True,
            "PRE_source_graph_heavy_atom_count": 44,
            "PRE_source_graph_mapping_count": 0,
            "PRE_status": PRE_STATUS,
            "PRE_topology_authority_created": False,
            "PRE_zero_fill_performed": False,
        },
        "FORMAL_PRE_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("POST_evidence_boundary"),
        {
            "POST_geometry_training_authority_created": False,
            "POST_geometry_training_target_created": False,
            "POST_sample_authority_created": False,
            "POST_source_evidence_available": True,
            "POST_source_evidence_count": 4,
        },
        "FORMAL_POST_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("chemical_warhead_boundary"),
        {
            "Acrylate_annotation_role": "SUPPORTING_EVIDENCE_ONLY",
            "Acrylate_promoted_to_reusable_authority": False,
            "D2_sample_level_chemistry_positive_authority_created": True,
            "chemical_warhead_atom_ids": None,
            "chemical_warhead_human_authoritative": False,
            "reaction_family_authority_created": False,
            "reusable_chemistry_rule_created": False,
            "selected_role_W_is_sample_level_canonical_role_region": True,
            "selected_role_warhead_atom_ids": list(WARHEAD_ROLE),
            "warhead_family_authority_created": False,
            "warhead_rule_authority_created": False,
        },
        "FORMAL_CHEMICAL_WARHEAD_NONAUTHORITY_DRIFT",
    )
    _expect(
        formal.get("reusable_authority_boundary"),
        {
            "Acrylate_annotation_use": "SUPPORTING_EVIDENCE_ONLY",
            "reaction_family_authority_created": False,
            "reusable_chemistry_authority_created": False,
            "reusable_pair_authority_created": False,
            "reusable_role_authority_created": False,
            "warhead_family_authority_created": False,
            "warhead_rule_authority_created": False,
        },
        "FORMAL_REUSABLE_AUTHORITY_DRIFT",
    )
    authority = formal.get("authority_boundary")
    if type(authority) is not dict:
        _fail("FORMAL_AUTHORITY_BOUNDARY_MISSING")
    for key, expected in (
        ("human_choices_externally_authorized", True),
        ("sample_level_chemistry_positive_authority_created", True),
        ("sample_level_canonical_role_partition_authority_created", True),
        ("candidate_for_future_training_admission", True),
        ("chemical_warhead_authority_created", False),
        ("reaction_family_authority_created", False),
        ("reusable_chemistry_authority_created", False),
        ("warhead_rule_authority_created", False),
        ("warhead_type_authority_created", False),
        ("PRE_topology_authority_created", False),
        ("PRE_geometry_authority_created", False),
        ("POST_geometry_training_authority_created", False),
        ("formal_training_admitted", False),
        ("training_admission_created", False),
        ("READY_FOR_TRAINING", False),
    ):
        _expect(authority.get(key), expected, "FORMAL_AUTHORITY_BOUNDARY_DRIFT:" + key)


def _current_census_boundary(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    summary = _strict_json_loads(
        payloads[CENSUS_SUMMARY_RELATIVE], "CURRENT_2A2_CENSUS_SUMMARY"
    )
    _strict_json_loads(
        payloads[CENSUS_MANIFEST_RELATIVE], "CURRENT_2A2_CENSUS_MANIFEST"
    )
    try:
        rows = list(
            csv.DictReader(
                io.StringIO(payloads[CENSUS_MATRIX_RELATIVE].decode("utf-8"))
            )
        )
    except UnicodeDecodeError as error:
        raise I12IngestionSafetyError(
            "COVAPIE_I12_INGESTION_V1_ERROR:CURRENT_CENSUS_UTF8_INVALID"
        ) from error
    if len(rows) != 1000 or len({row.get("canonical_event_id") for row in rows}) != 1000:
        _fail("CURRENT_CENSUS_UNIVERSE_DRIFT")
    i12_rows = [row for row in rows if row.get("ligand_component_id") == "I12"]
    if (
        len(i12_rows) != 4
        or tuple(row.get("canonical_event_id") for row in i12_rows) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in i12_rows) != EXPECTED_RANKS
    ):
        _fail("CURRENT_CENSUS_I12_EXACT4_DRIFT")
    expected_cells = {
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
    }
    for row in i12_rows:
        if any(row.get(key) != value for key, value in expected_cells.items()):
            _fail("CURRENT_CENSUS_I12_PRIOR_STATE_DRIFT")
    human = summary.get("human_review")
    if type(human) is not dict:
        _fail("CURRENT_CENSUS_HUMAN_REVIEW_COUNTS_MISSING")
    expected_counts = {
        "completed_positive_event_count": 95,
        "completed_positive_unit_count": 13,
        "completed_event_count": 119,
        "completed_unit_count": 17,
        "unreviewed_event_count": 219,
        "unreviewed_unit_count": 114,
    }
    for key, expected in expected_counts.items():
        _expect(human.get(key), expected, "CURRENT_CENSUS_COUNT_DRIFT:" + key)
    exact5 = summary.get("canonical_exact5")
    if type(exact5) is not dict:
        _fail("CURRENT_CENSUS_EXACT5_MISSING")
    for key, expected in (("task_count", 5), ("B3_present", True), ("sixth_task_present", False)):
        _expect(exact5.get(key), expected, "CURRENT_CENSUS_EXACT5_DRIFT:" + key)
    return {
        **expected_counts,
        "I12_current_status": "CURRENTLY_UNREVIEWED",
        "I12_event_count": 4,
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
    """Bind, parse, and independently validate the frozen I12 authority."""

    repo_root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    allowed = {
        POLICY_BINDING[0],
        *(binding[0] for binding in FORMAL_BINDINGS),
        *(binding[0] for binding in SEMANTIC_OWNER_BINDINGS),
        *(binding[0] for binding in CENSUS_BINDINGS),
    }
    if set(overrides) - allowed:
        _fail("SOURCE_OVERRIDE_NOT_AUTHORIZED")

    _verify_binding(repo_root, POLICY_BINDING, overrides)
    formal_payloads = _verify_bindings(repo_root, FORMAL_BINDINGS, overrides)
    semantic_payloads = _verify_bindings(repo_root, SEMANTIC_OWNER_BINDINGS, overrides)
    census_payloads = _verify_bindings(repo_root, CENSUS_BINDINGS, overrides)
    formal = _strict_json_loads(
        formal_payloads[FORMAL_DECISION_RELATIVE], "I12_FROZEN_FORMAL_DECISION"
    )
    _validate_formal_document(formal)
    semantic_contract = _validate_semantic_owners(semantic_payloads)
    census_boundary = _current_census_boundary(census_payloads)
    return {
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "source_binding_policy_binding": _binding_record(POLICY_BINDING),
        "semantic_owner_bindings": _binding_records(SEMANTIC_OWNER_BINDINGS),
        "current_census_bindings": _binding_records(CENSUS_BINDINGS),
        "semantic_contract": semantic_contract,
        "current_census_boundary": census_boundary,
        "formal": formal,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "formal_event_training_use_decision": "INCLUDE",
        "event_training_use_human_decision_available": True,
        "training_use_allowed": True,
        "training_use_include": True,
        "human_training_excluded": False,
        "candidate_for_future_training_admission": True,
        "future_training_admission_status": FUTURE_STATUS,
        "future_training_candidate_derived_by_ingestion": True,
        "future_training_candidate_is_training_admission": False,
        "training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed_now": False,
        "formal_split_authority_created": False,
        "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "ready_for_training": False,
    }


def _geometry_boundary() -> dict[str, object]:
    return {
        "PRE_status": PRE_STATUS,
        "PRE_source_graph_mapping_count": 0,
        "PRE_topology_authority_available": False,
        "PRE_geometry_authority_available": False,
        "PRE_reconstruction_performed": False,
        "PRE_mapping_repair_performed": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_zero_fill_performed": False,
        "POST_source_evidence_available": True,
        "POST_source_evidence_count": 4,
        "POST_sample_authority": False,
        "POST_geometry_training_authority_available": False,
        "POST_geometry_training_target_available_now": False,
    }


def _chemical_authority_boundary() -> dict[str, object]:
    return {
        "sample_level_chemistry_positive_authority": True,
        "selected_role_W_authoritative": True,
        "selected_role_W_scope": "sample-level canonical role region",
        "chemical_warhead_human_authoritative": False,
        "chemical_warhead_atom_ids": None,
        "reaction_family_authority": False,
        "warhead_family_authority": False,
        "warhead_rule_authority": False,
        "warhead_type_authority": False,
        "reusable_chemistry_authority": False,
    }


def _authority_boundary() -> dict[str, object]:
    return {
        "authority_source": AUTHORITY_SOURCE,
        "authority_scope": AUTHORITY_SCOPE,
        "authority_ingested": True,
        "authority_created_by_this_ingestion": False,
        "human_authority_created_by_this_ingestion": False,
        "scientific_authority_created_by_this_ingestion": False,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "training_admission_created": False,
        "training_admitted": False,
        "training_materialization_allowed_now": False,
        "ready_for_training": False,
        "feature_semantics_audit_required_later": True,
        "Step12D": "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "training_started": False,
        "commit_performed": False,
        "push_performed": False,
    }


def _role_projection() -> dict[str, object]:
    return {
        "D4_human_choice": "SELECT_CANDIDATE_0",
        "selected_role_candidate_index_0based": 0,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "warhead_role_atom_ids": list(WARHEAD_ROLE),
        "linker_atom_ids": [],
        "scaffold_atom_ids": list(SCAFFOLD_ROLE),
        "boundary_bonds": list(BOUNDARY_BONDS),
        "warhead_atom_count": 7,
        "linker_atom_count": 0,
        "scaffold_atom_count": 37,
        "Exact44_count": 44,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "warhead_connected": True,
        "linker_connected_or_empty": True,
        "scaffold_connected": True,
        "reactive_C21_in_W": True,
        **_chemical_authority_boundary(),
    }


def _event_projection(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "canonical_event_id": row[0],
        "scaleup_rank": row[1],
        "pdb_id": row[2],
        "model_number": 1,
        "protein_chain_or_asym": row[3],
        "cys_residue_id": row[4],
        "protein_altloc": None,
        "ligand_component_id": "I12",
        "ligand_chain_or_asym": row[5],
        "ligand_altloc": None,
        "selected_connection_id": row[6],
        "POST_distance_angstrom": row[7],
        "POST_distance_frozen_lexeme": row[8],
        "human_task_relevance_decision": "RELEVANT",
        "chemistry_known_positive": True,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "reactive_pair_human_decision_available": True,
        "reactive_pair_human_authoritative": True,
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C21",
        "ligand_reactive_atom_element": "C",
        "explicit_covalent_evidence": True,
        "event_specific_exception": False,
        "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True,
        **_training_boundary(),
        **_geometry_boundary(),
        **_chemical_authority_boundary(),
        **_authority_boundary(),
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "I12_FROZEN_HUMAN_AUTHORITY_INGESTION_PROJECTION",
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "source_binding_policy_binding": bound["source_binding_policy_binding"],
        "semantic_owner_bindings": bound["semantic_owner_bindings"],
        "human_approval": {
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
            "human_choices_externally_authorized": True,
            "approved": True,
            "decision_finalized": True,
            "human_review_completed": True,
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_partition": "SELECT_CANDIDATE_0",
            "D5_training_use": "INCLUDE",
            "D6_scientific_context": EXPECTED_D6,
        },
        "events": [_event_projection(row) for row in EXPECTED_EVENTS],
        "selected_role_partition": _role_projection(),
        "canonical_task_contract": _canonical_task_contract(),
        "training_boundary": _training_boundary(),
        "geometry_boundary": _geometry_boundary(),
        "chemical_authority_boundary": _chemical_authority_boundary(),
        "reusable_authority_boundary": {
            "reaction_family_authority": False,
            "warhead_family_authority": False,
            "warhead_rule_authority": False,
            "warhead_type_authority": False,
            "reusable_chemistry_authority": False,
            "reusable_pair_authority": False,
            "reusable_role_authority": False,
        },
        "current_census_boundary": bound["current_census_boundary"],
        "authority_boundary": _authority_boundary(),
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "pdb_id", "model_number",
    "protein_chain_or_asym", "cys_residue_id", "protein_altloc",
    "ligand_component_id", "ligand_chain_or_asym", "ligand_altloc",
    "selected_connection_id", "POST_distance_angstrom",
    "human_task_relevance_decision", "chemistry_known_positive",
    "negative_chemistry", "task_domain_negative",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "protein_reactive_atom", "ligand_reactive_atom", "ligand_reactive_atom_element",
    "explicit_covalent_evidence", "event_specific_exception",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "selected_role_candidate_index_0based", "role_profile",
    "warhead_atoms_json", "linker_atoms_json", "scaffold_atoms_json",
    "boundary_bonds_json", "global_canonical_task_count",
    "canonical_task_applicability_json", "direct_profile_applicable_task_ids_json",
    "formal_event_training_use_decision", "event_training_use_human_decision_available",
    "training_use_allowed", "training_use_include", "human_training_excluded",
    "candidate_for_future_training_admission", "future_training_admission_status",
    "future_training_candidate_derived_by_ingestion",
    "future_training_candidate_is_training_admission", "training_admitted",
    "training_admission_created", "training_materialization_allowed_now",
    "formal_split_authority_created", "tensor_target_created",
    "current_runtime_model_usable", "parameter_update_authorization",
    "ready_for_training", "POST_source_evidence_available",
    "POST_source_evidence_count", "POST_sample_authority",
    "POST_geometry_training_authority_available",
    "POST_geometry_training_target_available_now", "PRE_status",
    "PRE_source_graph_mapping_count", "PRE_topology_authority_available",
    "PRE_geometry_authority_available", "PRE_reconstruction_performed",
    "PRE_mapping_repair_performed", "POST_to_PRE_copy_performed",
    "PRE_zero_fill_performed", "sample_level_chemistry_positive_authority",
    "selected_role_W_authoritative", "selected_role_W_scope",
    "chemical_warhead_human_authoritative", "chemical_warhead_atoms_json",
    "reaction_family_authority", "warhead_family_authority",
    "warhead_rule_authority", "warhead_type_authority",
    "reusable_chemistry_authority", "authority_source", "authority_scope",
    "authority_ingested", "authority_created_by_this_ingestion",
)


def _bool_cell(value: bool) -> str:
    return "true" if value else "false"


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    applicability = _canonical_task_contract()["task_applicability"]
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        rows.append(
            {
                "canonical_event_id": event["canonical_event_id"],
                "scaleup_rank": str(event["scaleup_rank"]),
                "pdb_id": event["pdb_id"],
                "model_number": "1",
                "protein_chain_or_asym": event["protein_chain_or_asym"],
                "cys_residue_id": event["cys_residue_id"],
                "protein_altloc": "",
                "ligand_component_id": "I12",
                "ligand_chain_or_asym": event["ligand_chain_or_asym"],
                "ligand_altloc": "",
                "selected_connection_id": event["selected_connection_id"],
                "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
                "human_task_relevance_decision": "RELEVANT",
                "chemistry_known_positive": "true",
                "negative_chemistry": "false",
                "task_domain_negative": "false",
                "reactive_pair_human_decision_available": "true",
                "reactive_pair_human_authoritative": "true",
                "protein_reactive_atom": "SG",
                "ligand_reactive_atom": "C21",
                "ligand_reactive_atom_element": "C",
                "explicit_covalent_evidence": "true",
                "event_specific_exception": "false",
                "role_partition_human_decision_available": "true",
                "role_partition_human_authoritative": "true",
                "selected_role_candidate_index_0based": "0",
                "role_profile": EXPECTED_ROLE_PROFILE,
                "warhead_atoms_json": _json_cell(list(WARHEAD_ROLE)),
                "linker_atoms_json": "[]",
                "scaffold_atoms_json": _json_cell(list(SCAFFOLD_ROLE)),
                "boundary_bonds_json": _json_cell(list(BOUNDARY_BONDS)),
                "global_canonical_task_count": "5",
                "canonical_task_applicability_json": _json_cell(applicability),
                "direct_profile_applicable_task_ids_json": "[0,3,4]",
                "formal_event_training_use_decision": "INCLUDE",
                "event_training_use_human_decision_available": "true",
                "training_use_allowed": "true",
                "training_use_include": "true",
                "human_training_excluded": "false",
                "candidate_for_future_training_admission": "true",
                "future_training_admission_status": FUTURE_STATUS,
                "future_training_candidate_derived_by_ingestion": "true",
                "future_training_candidate_is_training_admission": "false",
                "training_admitted": "false",
                "training_admission_created": "false",
                "training_materialization_allowed_now": "false",
                "formal_split_authority_created": "false",
                "tensor_target_created": "false",
                "current_runtime_model_usable": "false",
                "parameter_update_authorization": "false",
                "ready_for_training": "false",
                "POST_source_evidence_available": "true",
                "POST_source_evidence_count": "4",
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
                "sample_level_chemistry_positive_authority": "true",
                "selected_role_W_authoritative": "true",
                "selected_role_W_scope": "sample-level canonical role region",
                "chemical_warhead_human_authoritative": "false",
                "chemical_warhead_atoms_json": "null",
                "reaction_family_authority": "false",
                "warhead_family_authority": "false",
                "warhead_rule_authority": "false",
                "warhead_type_authority": "false",
                "reusable_chemistry_authority": "false",
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
        "review_unit": "I12",
        "event_count": 4,
        "D1_RELEVANT_count": 4,
        "D2_POSITIVE_count": 4,
        "D3_CONFIRMED_count": 4,
        "DIRECT_event_count": 4,
        "applicable_warhead_only_count": 4,
        "applicable_linker_plus_warhead_count": 0,
        "applicable_scaffold_plus_warhead_count": 0,
        "applicable_scaffold_only_count": 4,
        "applicable_scaffold_plus_linker_plus_warhead_count": 4,
        "D5_INCLUDE_count": 4,
        "future_training_admission_candidate_count": 4,
        "future_training_candidate_derived_by_ingestion_count": 4,
        "training_admitted_count": 0,
        "PRE_topology_authority_count": 0,
        "PRE_geometry_authority_count": 0,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_count": 0,
        "chemical_warhead_human_authority_count": 0,
        "reusable_chemistry_authority_count": 0,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "authority_ingested": True,
        "authority_created_by_this_ingestion": False,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "training_materialization_allowed_now": False,
        "ready_for_training": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "TRAINING_STARTED": False,
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
        raise I12IngestionSafetyError(
            "COVAPIE_I12_INGESTION_V1_ERROR:UTF8_INVALID:" + label
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
            raise I12IngestionSafetyError(
                "COVAPIE_I12_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
                + relative.as_posix()
            ) from error
        _validate_text_payload(relative.as_posix(), payload)
        digest = _sha256(payload)
        try:
            verified = verify_bound_source_v2(
                path=path,
                expected_byte_count=len(payload),
                expected_sha256=digest,
                label="I12_CANDIDATE_SOURCE:" + relative.as_posix(),
                expected_executable=False,
            )
        except SourceBindingPolicyV2Error as error:
            raise I12IngestionSafetyError(
                "COVAPIE_I12_INGESTION_V1_ERROR:CANDIDATE_SOURCE_REJECTED:"
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


def _standalone_bound() -> dict[str, object]:
    return {
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "source_binding_policy_binding": _binding_record(POLICY_BINDING),
        "semantic_owner_bindings": _binding_records(SEMANTIC_OWNER_BINDINGS),
        "current_census_bindings": _binding_records(CENSUS_BINDINGS),
        "semantic_contract": {
            "role_profile": EXPECTED_ROLE_PROFILE,
            "global_canonical_task_count": 5,
            "direct_profile_applicable_task_ids": [0, 3, 4],
            "B3_present": True,
            "sixth_task_present": False,
        },
        "current_census_boundary": {
            "completed_positive_event_count": 95,
            "completed_positive_unit_count": 13,
            "completed_event_count": 119,
            "completed_unit_count": 17,
            "unreviewed_event_count": 219,
            "unreviewed_unit_count": 114,
            "I12_current_status": "CURRENTLY_UNREVIEWED",
            "I12_event_count": 4,
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
        "artifact_role": "I12_COMPLETED_DECISION_INGESTION_NOT_RECONCILIATION_OR_ADMISSION",
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "source_binding_policy_binding": bound["source_binding_policy_binding"],
        "semantic_owner_bindings": bound["semantic_owner_bindings"],
        "current_census_bindings": bound["current_census_bindings"],
        "current_census_boundary": bound["current_census_boundary"],
        "candidate_source_bindings": candidate_source_bindings,
        "canonical_task_contract": _canonical_task_contract(),
        "formal_projection": {
            "D1": "RELEVANT",
            "D2": "POSITIVE",
            "D3": "CONFIRM_OBSERVED_PAIR",
            "D4": "SELECT_CANDIDATE_0",
            "D5": "INCLUDE",
            "role_profile": EXPECTED_ROLE_PROFILE,
            "W_L_S_counts": [7, 0, 37],
            "boundary": "C20-C21 SING",
        },
        "chemical_authority_boundary": _chemical_authority_boundary(),
        "training_boundary": _training_boundary(),
        "geometry_boundary": _geometry_boundary(),
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
        "B1_B4_clean_from_birth": True,
        "numeric_POSIX_semantic_identity": False,
        "separate_I12_V2_successor_required": False,
        "formal_validator_runtime_dependency": False,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "ready_for_training": False,
        "authority_boundary": _authority_boundary(),
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
    """Validate the deterministic I12 projection and every authority boundary."""

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
        raise I12IngestionSafetyError(
            "COVAPIE_I12_INGESTION_V1_ERROR:MATRIX_UTF8_INVALID"
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
    ):
        _fail("MATRIX_EXACT4_IDENTITY_INVALID")
    for index, row in enumerate(matrix):
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["POST_distance_angstrom"] != EXPECTED_EVENTS[index][8]
            or row["selected_role_candidate_index_0based"] != "0"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or json.loads(row["warhead_atoms_json"]) != list(WARHEAD_ROLE)
            or json.loads(row["linker_atoms_json"]) != []
            or json.loads(row["scaffold_atoms_json"]) != list(SCAFFOLD_ROLE)
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or [
                item["task_id"]
                for item in applicability
                if item["structurally_applicable"]
            ]
            != [0, 3, 4]
            or row["chemical_warhead_human_authoritative"] != "false"
            or json.loads(row["chemical_warhead_atoms_json"]) is not None
            or row["future_training_candidate_is_training_admission"] != "false"
            or row["training_admitted"] != "false"
            or row["POST_geometry_training_authority_available"] != "false"
            or row["PRE_topology_authority_available"] != "false"
            or row["PRE_geometry_authority_available"] != "false"
            or row["authority_created_by_this_ingestion"] != "false"
        ):
            _fail("MATRIX_AUTHORITY_TASK_OR_GEOMETRY_BOUNDARY_INVALID")
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
    """Fail closed on an unsafe or contaminated destination before any write."""

    try:
        root_metadata = target_root.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise I12IngestionSafetyError(
            "COVAPIE_I12_INGESTION_V1_ERROR:OUTPUT_ROOT_LSTAT_FAILED"
        ) from error
    if stat.S_ISLNK(root_metadata.st_mode):
        _fail("OUTPUT_ROOT_SYMLINK_FORBIDDEN")
    if not stat.S_ISDIR(root_metadata.st_mode):
        _fail("OUTPUT_ROOT_NOT_DIRECTORY")
    try:
        entries = tuple(target_root.iterdir())
    except OSError as error:
        raise I12IngestionSafetyError(
            "COVAPIE_I12_INGESTION_V1_ERROR:OUTPUT_ROOT_INVENTORY_READ_FAILED"
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
            raise I12IngestionSafetyError(
                "COVAPIE_I12_INGESTION_V1_ERROR:OUTPUT_ENTRY_LSTAT_FAILED:"
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
    """Write only the four deterministic I12 output artifacts."""

    repo_root = Path(repo_root).resolve()
    artifacts = build_artifacts_v1(repo_root)
    target_root = Path(output_root) if output_root is not None else repo_root / OUTPUT_ROOT_RELATIVE
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
    if tuple(sorted(path.name for path in output_root.iterdir())) != tuple(sorted(OUTPUT_FILENAMES)):
        _fail("OUTPUT_INVENTORY_NOT_EXACT4")
    actual: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = output_root / name
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise I12IngestionSafetyError(
                "COVAPIE_I12_INGESTION_V1_ERROR:OUTPUT_READ_FAILED:" + name
            ) from error
        try:
            verified = verify_bound_source_v2(
                path=path,
                expected_byte_count=len(payload),
                expected_sha256=_sha256(payload),
                label="I12_MATERIALIZED_OUTPUT:" + name,
                expected_executable=False,
            )
        except SourceBindingPolicyV2Error as error:
            raise I12IngestionSafetyError(
                "COVAPIE_I12_INGESTION_V1_ERROR:OUTPUT_REJECTED:" + name
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
        "authority_ingested": True,
        "authority_created_by_this_ingestion": False,
        "reconciliation_performed": False,
        "census_refreshed": False,
        "queue_updated": False,
        "ready_for_training": False,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    materialize_artifacts_v1(repo_root)
    print(json.dumps(check_materialized_v1(repo_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
