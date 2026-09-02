"""Project frozen CER human authority into deterministic ingestion metadata.

The frozen formal validator is provenance identity only: this owner binds its
bytes but never imports or executes it.  Formal JSON semantics are parsed and
validated independently.  This additive step does not reconcile or refresh
the global census and does not admit, tensorize, or train any sample.
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
    "CERIngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)


SCHEMA_VERSION = "covapie_cer_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_cer_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_cer_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_cer_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_cer_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cer_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_cer_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_cer_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cer_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_cer_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_cer_event_task_label_availability_v1.csv"
SUMMARY = "covapie_cer_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_cer_completed_decision_ingestion_manifest_v1.json"
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
    "CER_COVAPIE_BULK_REVIEW_UNIT_946339D19F961B4A/"
    "formal-human-decision-v1"
)
FORMAL_DECISION_RELATIVE = FORMAL_ROOT / "cer_formal_human_decision_v1.json"
FORMAL_VALIDATOR_RELATIVE = FORMAL_ROOT / "validate_cer_formal_human_decision_v1.py"

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
    "covapie_cumulative1000_current_global_readiness_census_with_1n0_v1.py"
)
CENSUS_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_1n0_v1"
)
CENSUS_MATRIX_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_census_with_1n0_v1.csv"
)
CENSUS_SUMMARY_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_summary_with_1n0_v1.json"
)
CENSUS_MANIFEST_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_manifest_with_1n0_v1.json"
)

FORMAL_DECISION_SCHEMA = "covapie_cer_exact4_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "39ecc8a4aa0db21c691deaa5befa97ef745311f42d663ce443d987bfdba79412"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_946339D19F961B4A"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
EXPECTED_D6 = (
    "Confirm the sample-specific observed CYS-SG ↔ CER-C2 covalent pair for "
    "the 1FJ8 Exact4. PRE-reaction topology remains unresolved. Do not "
    "generalize the observed C2 regiochemistry or create reusable "
    "reaction-family/warhead-rule authority from this review alone. Select "
    "DIRECT candidate 3 as the CER head-tail role partition."
)
EXPECTED_D6_BYTE_COUNT = 325
EXPECTED_D6_SHA256 = "bb7720e708c13833dcd0bd5f55135130a21269e077f4ef386b7bb86e3b272242"

AUTHORITY_SOURCE = "FORMAL_CER_HUMAN_DECISION"
AUTHORITY_SCOPE = "CURRENT_CER_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
FUTURE_STATUS = "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"
PRE_STATUS = "PRE_REACTION_UNRESOLVED"

# event id, rank, protein asym, ligand asym, connection, distance, frozen lexeme,
# reported distance
EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:1FJ8:A:CYS:163-:SG:E:CER:C2",
        52,
        "A",
        "E",
        "covale1",
        1.902635,
        "1.902635",
        1.903,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:1FJ8:B:CYS:163-:SG:F:CER:C2",
        53,
        "B",
        "F",
        "covale2",
        1.889924,
        "1.889924",
        1.89,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:1FJ8:C:CYS:163-:SG:G:CER:C2",
        54,
        "C",
        "G",
        "covale3",
        1.860698,
        "1.860698",
        1.861,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:1FJ8:D:CYS:163-:SG:H:CER:C2",
        55,
        "D",
        "H",
        "covale4",
        1.899047,
        "1.899047",
        1.899,
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)

WARHEAD_ROLE = ("C1", "C2", "C3", "C4", "N1", "O1", "O2", "O3")
LINKER_ROLE: tuple[str, ...] = ()
SCAFFOLD_ROLE = ("C10", "C11", "C12", "C5", "C6", "C7", "C8", "C9")
HEAVY_ATOMS = tuple((*WARHEAD_ROLE, *LINKER_ROLE, *SCAFFOLD_ROLE))
BOUNDARY_BONDS = (
    {
        "atom_id_1": "C4",
        "atom_id_2": "C5",
        "bond_order": "SING",
        "boundary_between_roles": ["warhead", "scaffold"],
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

# path, namespace, byte count, SHA256, expected executable, source role
FORMAL_BINDINGS = (
    (
        FORMAL_DECISION_RELATIVE,
        "project_parent_relative",
        26123,
        "380d54ba35cf8eff1760d540e0874c8a7e920dac9473a002dac156812164fb2c",
        False,
        "CER_FROZEN_FORMAL_HUMAN_DECISION",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE,
        "project_parent_relative",
        72368,
        "db4236586eb97bfd6d9486056f955d545de5d552f814a2c91a61596813d2da5a",
        False,
        "CER_FROZEN_FORMAL_VALIDATOR_PROVENANCE_IDENTITY_ONLY",
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
        65131,
        "8b5df9a718d9a42eb9372c68a466deb2b595fc6285dc02719b68390c96041ee5",
        False,
        "CURRENT_WITH_1N0_GLOBAL_CENSUS_OWNER",
    ),
    (
        CENSUS_MATRIX_RELATIVE,
        "repository_relative",
        533426,
        "ac63ced99e77212e5952b41169369c5e5c77967f9409e2e1fec25f99808eaf35",
        False,
        "CURRENT_WITH_1N0_GLOBAL_CENSUS_MATRIX",
    ),
    (
        CENSUS_SUMMARY_RELATIVE,
        "repository_relative",
        17728,
        "516ab4c1ed9196c2233695566be9976d8f9f8dc5b13bb88b364b15eee8d08459",
        False,
        "CURRENT_WITH_1N0_GLOBAL_CENSUS_SUMMARY",
    ),
    (
        CENSUS_MANIFEST_RELATIVE,
        "repository_relative",
        53527,
        "e70b084c0a1f8ecdb35de9092a3d5cc1987d50ec18d0528610a6968faf2e173b",
        False,
        "CURRENT_WITH_1N0_GLOBAL_CENSUS_MANIFEST",
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
_FORBIDDEN_AMBIGUOUS_FORMAL_FIELDS = {
    "human_authored_free_text",
    "machine_generated_token",
}


class CERIngestionSafetyError(ValueError):
    """Raised when the frozen CER ingestion contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise CERIngestionSafetyError("COVAPIE_CER_INGESTION_V1_ERROR:" + reason)


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
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("JSON_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CERIngestionSafetyError(
            "COVAPIE_CER_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label
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
        raise CERIngestionSafetyError(
            "COVAPIE_CER_INGESTION_V1_ERROR:JSON_PARSE_FAILED:" + label
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
        raise CERIngestionSafetyError(
            "COVAPIE_CER_INGESTION_V1_ERROR:BOUND_SOURCE_REJECTED:" + source_role
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
        raise CERIngestionSafetyError(
            "COVAPIE_CER_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
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
                    raise CERIngestionSafetyError(
                        "COVAPIE_CER_INGESTION_V1_ERROR:"
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
            "D4_role_partition": "SELECT_CANDIDATE_3",
            "D5_training_use": "INCLUDE",
            "D6_context_reference": "UNIT_LEVEL_EXACT_AUTHORIZED_D6",
            "POST_distance_angstrom": row[5],
            "POST_sample_authority": False,
            "POST_source_evidence": True,
            "POST_training_target_authority": False,
            "canonical_event_id": row[0],
            "chemistry_human_authoritative": True,
            "distance_only_inference_used": False,
            "explicit_covalent_evidence": True,
            "formal_training_admitted": False,
            "ligand_asym": row[3],
            "ligand_component_id": "CER",
            "ligand_reactive_atom": "C2",
            "model_number": 1,
            "pdb_id": "1FJ8",
            "protein_asym": row[2],
            "protein_reactive_atom": "SG",
            "protein_residue": "CYS:163-",
            "reactive_pair_human_authoritative": True,
            "reported_POST_distance_angstrom": row[7],
            "role_partition_human_authoritative": True,
            "scaleup_rank": row[1],
            "selected_connection_id": row[4],
            "task_relevance_human_authoritative": True,
            "training_use_human_authoritative": True,
        }
        for row in EXPECTED_EVENTS
    ]


def _expected_formal_role() -> dict[str, object]:
    return {
        "D4_human_choice": "SELECT_CANDIDATE_3",
        "W_L_S_counts": [8, 0, 8],
        "applicable_semantic_names": [
            "warhead_only",
            "scaffold_only",
            "scaffold_plus_linker_plus_warhead",
        ],
        "applicable_task_ids": [0, 3, 4],
        "boundary_bonds": [
            {
                "aromatic_flag": "N",
                "atom_id_1": "C4",
                "atom_id_2": "C5",
                "bond_order": "SING",
                "role_1": "W",
                "role_2": "S",
            }
        ],
        "candidate_index_is_rank": False,
        "candidate_index_is_recommendation": False,
        "current_review_unit_role_partition_human_authority": True,
        "human_selected": True,
        "independent_structural_validation": {
            "Exact16_count": 16,
            "L_connected_or_empty": True,
            "L_count": 0,
            "S_connected": True,
            "S_count": 8,
            "W_connected": True,
            "W_count": 8,
            "direct_boundary_C4_C5_SING": True,
            "extra_atom_ids": [],
            "linker_empty_allowed_by_DIRECT_profile": True,
            "missing_atom_ids": [],
            "partition_exhaustive": True,
            "partition_pairwise_disjoint": True,
            "reactive_C2_in_W": True,
        },
        "linker_atom_ids": [],
        "linker_empty_allowed_by_DIRECT_profile": True,
        "linker_role_connected_or_empty": True,
        "machine_candidate_provenance_preserved": True,
        "machine_recommended": False,
        "machine_selected": False,
        "partition_exhaustive": True,
        "partition_pairwise_disjoint": True,
        "published_role_runtime_validation": {
            "applicable_task_ids": [0, 3, 4],
            "direct_scaffold_warhead_boundary": {
                "bond_order": "SING",
                "boundary_valid": True,
                "scaffold_atom_id": "C5",
                "warhead_atom_id": "C4",
            },
            "direct_scaffold_warhead_boundary_applicable": True,
            "linker_count": 0,
            "linker_warhead_boundary_applicable": False,
            "profile": EXPECTED_ROLE_PROFILE,
            "reasons": [],
            "scaffold_count": 8,
            "scaffold_linker_boundary_applicable": False,
            "valid": True,
            "validator": "validate_role_profile_v1",
            "warhead_count": 8,
        },
        "reactive_C2_in_W": True,
        "reusable_role_rule_created": False,
        "role_authority_scope": "CURRENT_CER_EXACT4_REVIEW_UNIT_ONLY",
        "role_profile": EXPECTED_ROLE_PROFILE,
        "scaffold_atom_ids": list(SCAFFOLD_ROLE),
        "scaffold_role_connected": True,
        "selected_candidate_index_0based": 3,
        "source_candidate_preview_was_nonauthoritative": True,
        "warhead_role_atom_ids": list(WARHEAD_ROLE),
        "warhead_role_connected": True,
    }


def _expected_formal_tasks() -> dict[str, object]:
    return {
        "B3_present": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "global_canonical_Exact5": [
            {"semantic_name": semantic, "short_alias": alias, "task_id": task_id}
            for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "global_mask_contract_modified": False,
        "sample_applicability_scope": "CURRENT_CER_EXACT4_REVIEW_UNIT_ONLY",
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
        "sample_role_profile": EXPECTED_ROLE_PROFILE,
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
        "D4_role_candidate": "SELECT_CANDIDATE_3",
        "D5_training_use": "INCLUDE",
        "D6_scientific_context": EXPECTED_D6,
        "attestor_id": "fmx",
        "human_authorization_origin": "EXTERNAL_HUMAN_CHAT_AUTHORIZATION",
        "human_choices_externally_authorized": True,
        "human_selected_role_candidate_index_0based": 3,
        "human_selected_role_profile": EXPECTED_ROLE_PROFILE,
        "machine_approval_claimed": False,
        "reviewer_id": "fmx",
    }
    _expect(formal.get("human_authorization"), expected_human, "FORMAL_HUMAN_AUTHORIZATION_DRIFT")
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
    _expect(formal.get("human_approved_context"), expected_context, "FORMAL_D6_PROVENANCE_DRIFT")
    d6_bytes = EXPECTED_D6.encode("utf-8")
    if len(d6_bytes) != EXPECTED_D6_BYTE_COUNT or _sha256(d6_bytes) != EXPECTED_D6_SHA256:
        _fail("INTERNAL_D6_IDENTITY_INVALID")
    _expect(
        formal.get("unit_human_decision"),
        {
            **{key: expected_human[key] for key in (
                "D1_task_relevance",
                "D2_chemistry",
                "D3_reactive_pair",
                "D4_role_candidate",
                "D5_training_use",
                "D6_scientific_context",
            )},
            "completed_human_review_event_count": 4,
            "exact_event_count": 4,
        },
        "FORMAL_UNIT_DECISION_DRIFT",
    )
    _expect(
        formal.get("identity"),
        {
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "distance_only_inference": False,
            "exact_event_count": 4,
            "explicit_covalent_evidence": True,
            "ligand_component_id": "CER",
            "ligand_reactive_atom": "C2",
            "pdb_ids": ["1FJ8"],
            "protein_reactive_atom": "SG",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scaleup_ranks": list(EXPECTED_RANKS),
        },
        "FORMAL_EXACT4_IDENTITY_DRIFT",
    )
    _expect(
        formal.get("event_level_human_decisions"),
        _expected_formal_events(),
        "FORMAL_EVENT_DECISION_OR_EVIDENCE_DRIFT",
    )
    _expect(
        formal.get("selected_role_partition"),
        _expected_formal_role(),
        "FORMAL_CANDIDATE3_ROLE_DRIFT",
    )
    if (
        len(HEAVY_ATOMS) != 16
        or len(set(HEAVY_ATOMS)) != 16
        or set(WARHEAD_ROLE) & set(SCAFFOLD_ROLE)
        or set(WARHEAD_ROLE) & set(LINKER_ROLE)
        or set(SCAFFOLD_ROLE) & set(LINKER_ROLE)
        or "C2" not in WARHEAD_ROLE
        or "C4" not in WARHEAD_ROLE
        or "C5" not in SCAFFOLD_ROLE
    ):
        _fail("INTERNAL_EXACT16_ROLE_PARTITION_INVALID")
    _expect(
        formal.get("canonical_Exact5_and_sample_applicability"),
        _expected_formal_tasks(),
        "FORMAL_CANONICAL_EXACT5_DRIFT",
    )
    _expect(
        formal.get("reactive_pair_authority"),
        {
            "D3_human_choice": "CONFIRM_OBSERVED_PAIR",
            "all_CER_uses_C2_authority_created": False,
            "all_cerulenin_reaction_family_uses_C2_authority_created": False,
            "all_ketosynthase_CER_pairs_use_C2_authority_created": False,
            "cross_structure_regiochemistry_generalization": False,
            "ligand_reactive_atom": "C2",
            "observed_pair_authority_created": True,
            "pair_scope": AUTHORITY_SCOPE,
            "protein_reactive_atom": "SG",
            "reusable_pair_rule_created": False,
        },
        "FORMAL_PAIR_AUTHORITY_DRIFT",
    )
    _expect(
        formal.get("chemistry_authority_boundary"),
        {
            "D2_human_choice": "POSITIVE",
            "chemical_warhead_human_authority": False,
            "chemistry_negative_authority": False,
            "current_review_unit_chemistry_positive_authority": True,
            "reaction_family_authority_created": False,
            "reusable_chemistry_authority_created": False,
            "reusable_chemistry_rule_created": False,
            "reusable_pair_rule_created": False,
            "warhead_family_authority_created": False,
            "warhead_rule_authority_created": False,
            "warhead_type_reusable_authority_created": False,
        },
        "FORMAL_CHEMISTRY_AUTHORITY_DRIFT",
    )
    _expect(
        formal.get("training_use_boundary"),
        {
            "D5_human_choice": "INCLUDE",
            "current_runtime_model_usable": False,
            "feature_semantics_finalized": False,
            "formal_split_authority": False,
            "formal_training_admitted": False,
            "future_training_admission_candidate": True,
            "human_training_use_disposition": "INCLUDE",
            "human_training_use_disposition_authority_created": True,
            "tensor_target_created": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
        },
        "FORMAL_TRAINING_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("PRE_POST_boundary"),
        {
            "POST_to_PRE_copy_performed": False,
            "PRE_geometry_authority": False,
            "PRE_mapping_count": 0,
            "PRE_source_graph_count": 0,
            "PRE_source_graph_present": False,
            "PRE_status": PRE_STATUS,
            "PRE_topology_authority": False,
            "PRE_zero_fill_performed": False,
            "leaving_group_inferred": False,
            "pre_reaction_bond_edit_inferred": False,
            "reagent_inferred": False,
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
        },
        "FORMAL_POST_BOUNDARY_DRIFT",
    )
    authority = formal.get("authority_boundary")
    if type(authority) is not dict:
        _fail("FORMAL_AUTHORITY_BOUNDARY_INVALID")
    required_true = (
        "formal_authority_created",
        "human_choices_externally_authorized",
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
        _expect(authority.get(key), False, "FORMAL_UNAUTHORIZED_AUTHORITY_PRESENT:" + key)
    _expect(
        formal.get("current_published_census_provenance"),
        {
            "CER_current_status": "CURRENTLY_UNREVIEWED",
            "CER_event_count": 4,
            "CER_human_review_completed": False,
            "HEAD": "146caa0a2d8dc93f048b52d34d34a8c893954b6b",
            "current_census_modified_by_this_step": False,
        },
        "FORMAL_CURRENT_CENSUS_PROVENANCE_DRIFT",
    )
    operation = formal.get("operation_boundary")
    if type(operation) is not dict:
        _fail("FORMAL_OPERATION_BOUNDARY_INVALID")
    for key in (
        "CENSUS_REFRESH",
        "INGESTION_PERFORMED",
        "QUEUE_REFRESH",
        "READY_FOR_TRAINING",
        "RECONCILIATION",
        "TRAINING_STARTED",
        "backward_performed",
        "loader_modified",
        "loss_executed",
        "model_forward_performed",
        "network_acquisition_performed",
        "optimizer_step_performed",
        "parameter_update_performed",
        "tensorization_performed",
    ):
        _expect(operation.get(key), False, "FORMAL_OPERATION_BOUNDARY_DRIFT:" + key)
    lifecycle = formal.get("validator_lifecycle")
    if type(lifecycle) is not dict:
        _fail("FORMAL_VALIDATOR_LIFECYCLE_INVALID")
    for key, expected in (
        ("baseline_commit", "146caa0a2d8dc93f048b52d34d34a8c893954b6b"),
        ("baseline_locked_creation_and_self_test_only", True),
        ("future_ingestion_must_bind_formal_json_and_validator_bytes_sha256", True),
        ("future_ingestion_must_independently_validate_semantics", True),
        ("future_ingestion_must_not_execute_this_validator_after_HEAD_advances", True),
        ("validator_postbaseline_runtime_dependency_allowed", False),
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
        _expect(prerequisite.get(key), expected, "FORMAL_TRAINING_PREREQUISITE_DRIFT:" + key)


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


def _current_census_boundary(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    summary = _strict_json_loads(
        payloads[CENSUS_SUMMARY_RELATIVE], "CURRENT_WITH_1N0_CENSUS_SUMMARY"
    )
    _strict_json_loads(
        payloads[CENSUS_MANIFEST_RELATIVE], "CURRENT_WITH_1N0_CENSUS_MANIFEST"
    )
    try:
        rows = list(
            csv.DictReader(
                io.StringIO(payloads[CENSUS_MATRIX_RELATIVE].decode("utf-8"))
            )
        )
    except UnicodeDecodeError as error:
        raise CERIngestionSafetyError(
            "COVAPIE_CER_INGESTION_V1_ERROR:CURRENT_CENSUS_UTF8_INVALID"
        ) from error
    if len(rows) != 1000 or len({row.get("canonical_event_id") for row in rows}) != 1000:
        _fail("CURRENT_CENSUS_UNIVERSE_DRIFT")
    expected_set = set(EXPECTED_EVENT_IDS)
    cer_rows = [row for row in rows if row.get("canonical_event_id") in expected_set]
    unit_rows = [row for row in rows if row.get("review_unit_id") == EXPECTED_REVIEW_UNIT_ID]
    if (
        len(cer_rows) != 4
        or len(unit_rows) != 4
        or {row.get("canonical_event_id") for row in cer_rows} != expected_set
        or {row.get("canonical_event_id") for row in unit_rows} != expected_set
        or tuple(int(row["scaleup_rank"]) for row in cer_rows) != EXPECTED_RANKS
    ):
        _fail("CURRENT_CENSUS_CER_EXACT4_DRIFT")
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
    for row in cer_rows:
        if any(row.get(key) != value for key, value in prior.items()):
            _fail("CURRENT_CENSUS_CER_PRIOR_STATE_DRIFT")
    human = summary.get("human_review")
    if type(human) is not dict:
        _fail("CURRENT_CENSUS_HUMAN_REVIEW_COUNTS_MISSING")
    expected_counts = {
        "completed_positive_event_count": 99,
        "completed_positive_unit_count": 14,
        "completed_event_count": 127,
        "completed_unit_count": 19,
        "unreviewed_event_count": 211,
        "unreviewed_unit_count": 112,
    }
    for key, expected in expected_counts.items():
        _expect(human.get(key), expected, "CURRENT_CENSUS_COUNT_DRIFT:" + key)
    exact5 = summary.get("canonical_exact5")
    if type(exact5) is not dict:
        _fail("CURRENT_CENSUS_EXACT5_MISSING")
    for key, expected in (
        ("task_count", 5),
        ("B3_present", True),
        ("sixth_task_present", False),
    ):
        _expect(exact5.get(key), expected, "CURRENT_CENSUS_EXACT5_DRIFT:" + key)
    return {
        **expected_counts,
        "CER_current_status": "CURRENTLY_UNREVIEWED",
        "CER_human_review_completed": False,
        "CER_event_count": 4,
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
    """Bind, parse, and independently validate the frozen CER authority."""

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
        formal_payloads[FORMAL_DECISION_RELATIVE], "CER_FROZEN_FORMAL_DECISION"
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
        "formal_semantics_independently_validated": True,
        "formal": formal,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "human_training_use_disposition": "INCLUDE",
        "human_training_use_disposition_authoritative": True,
        "future_training_admission_candidate": True,
        "future_training_admission_status": FUTURE_STATUS,
        "formal_training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed": False,
        "formal_split_authority": False,
        "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "parameter_update_authorization": False,
        "READY_FOR_TRAINING": False,
    }


def _geometry_boundary() -> dict[str, object]:
    return {
        "PRE_status": PRE_STATUS,
        "PRE_source_graph_present": False,
        "PRE_source_graph_count": 0,
        "PRE_mapping_count": 0,
        "PRE_topology_authority": False,
        "PRE_geometry_authority": False,
        "PRE_reconstruction_performed": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_zero_fill_performed": False,
        "POST_source_evidence_available": True,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
    }


def _pair_authority_boundary() -> dict[str, object]:
    return {
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C2",
        "reactive_pair_human_authoritative": True,
        "authority_scope": AUTHORITY_SCOPE,
        "cross_structure_regiochemistry_generalization": False,
        "all_CER_uses_C2": False,
        "all_cerulenin_reaction_family_uses_C2": False,
        "all_ketosynthase_CER_pairs_use_C2": False,
        "reusable_pair_rule_created": False,
    }


def _reusable_authority_boundary() -> dict[str, object]:
    return {
        "reusable_chemistry_authority": False,
        "reusable_pair_authority": False,
        "reusable_role_authority": False,
        "reaction_family_authority": False,
        "warhead_family_authority": False,
        "warhead_rule_authority": False,
        "warhead_type_authority": False,
    }


def _authority_boundary() -> dict[str, object]:
    return {
        "authority_source": AUTHORITY_SOURCE,
        "authority_scope": AUTHORITY_SCOPE,
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
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "Step12D": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
    }


def _role_projection() -> dict[str, object]:
    return {
        "D4_human_choice": "SELECT_CANDIDATE_3",
        "selected_role_candidate_index_0based": 3,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "warhead_role_atom_ids": list(WARHEAD_ROLE),
        "linker_atom_ids": [],
        "scaffold_atom_ids": list(SCAFFOLD_ROLE),
        "boundary_bonds": list(BOUNDARY_BONDS),
        "warhead_atom_count": 8,
        "linker_atom_count": 0,
        "scaffold_atom_count": 8,
        "Exact16_count": 16,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "warhead_connected": True,
        "linker_connected_or_empty": True,
        "scaffold_connected": True,
        "reactive_C2_in_W": True,
        "sample_level_authoritative": True,
        "reusable": False,
        "authority_scope": AUTHORITY_SCOPE,
    }


def _event_projection(row: tuple[object, ...]) -> dict[str, object]:
    return {
        "canonical_event_id": row[0],
        "scaleup_rank": row[1],
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": "1FJ8",
        "model_number": 1,
        "protein_chain_or_asym": row[2],
        "cys_residue_id": "CYS:163-",
        "protein_altloc": None,
        "ligand_component_id": "CER",
        "ligand_chain_or_asym": row[3],
        "ligand_altloc": None,
        "selected_connection_id": row[4],
        "POST_distance_angstrom": row[5],
        "POST_distance_frozen_lexeme": row[6],
        "human_review_completed": True,
        "human_task_relevance_decision": "RELEVANT",
        "task_relevance_human_authoritative": True,
        "human_chemistry_decision": "POSITIVE",
        "chemistry_known_positive": True,
        "chemistry_human_authoritative": True,
        "negative_chemistry": False,
        "task_domain_negative": False,
        "reactive_pair_human_decision_available": True,
        "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True,
        "explicit_covalent_evidence": True,
        "distance_only_inference_used": False,
        **_pair_authority_boundary(),
        **_training_boundary(),
        **_geometry_boundary(),
        **_reusable_authority_boundary(),
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "CER_FROZEN_HUMAN_AUTHORITY_DETERMINISTIC_INGESTION_PROJECTION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "formal_semantic_canonical_sha256": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "source_binding_policy_binding": bound["source_binding_policy_binding"],
        "semantic_owner_bindings": bound["semantic_owner_bindings"],
        "human_authorization": {
            "authorization_source": "EXTERNAL_HUMAN_CHAT_AUTHORIZATION",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "human_choices_externally_authorized": True,
            "machine_approval_claimed": False,
            "D1_task_relevance": "RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_candidate": "SELECT_CANDIDATE_3",
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
        "events": [_event_projection(row) for row in EXPECTED_EVENTS],
        "reactive_pair_authority": _pair_authority_boundary(),
        "selected_role_partition": _role_projection(),
        "canonical_task_contract": _canonical_task_contract(),
        "training_boundary": _training_boundary(),
        "geometry_boundary": _geometry_boundary(),
        "reusable_authority_boundary": _reusable_authority_boundary(),
        "current_census_boundary": bound["current_census_boundary"],
        "authority_boundary": _authority_boundary(),
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "review_unit_id", "pdb_id",
    "model_number", "protein_chain_or_asym", "cys_residue_id", "protein_altloc",
    "ligand_component_id", "ligand_chain_or_asym", "ligand_altloc",
    "selected_connection_id", "POST_distance_angstrom", "human_review_completed",
    "human_task_relevance_decision", "task_relevance_human_authoritative",
    "human_chemistry_decision", "chemistry_known_positive",
    "chemistry_human_authoritative", "negative_chemistry", "task_domain_negative",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "protein_reactive_atom", "ligand_reactive_atom", "explicit_covalent_evidence",
    "distance_only_inference_used", "pair_authority_scope",
    "cross_structure_regiochemistry_generalization", "all_CER_uses_C2",
    "all_cerulenin_reaction_family_uses_C2",
    "all_ketosynthase_CER_pairs_use_C2", "reusable_pair_rule_created",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "selected_role_candidate_index_0based", "role_profile", "warhead_atoms_json",
    "linker_atoms_json", "scaffold_atoms_json", "boundary_bonds_json",
    "global_canonical_task_count", "canonical_task_applicability_json",
    "direct_profile_applicable_task_ids_json", "task_applicability_determined",
    "authoritative_task_labels_created", "event_task_label_rows_materialized",
    "human_training_use_disposition", "training_use_human_authoritative",
    "future_training_admission_candidate", "future_training_admission_status",
    "formal_training_admitted", "training_admission_created",
    "training_materialization_allowed", "formal_split_authority",
    "tensor_target_created", "current_runtime_model_usable",
    "parameter_update_authorization", "ready_for_training", "PRE_status",
    "PRE_source_graph_present", "PRE_source_graph_count", "PRE_mapping_count",
    "PRE_topology_authority", "PRE_geometry_authority",
    "POST_to_PRE_copy_performed", "PRE_zero_fill_performed",
    "POST_source_evidence_available", "POST_source_evidence_count",
    "POST_geometry_training_authority", "POST_geometry_training_target_created",
    "reusable_chemistry_authority", "reusable_role_authority",
    "reaction_family_authority", "authority_source", "authority_scope",
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
                "pdb_id": "1FJ8",
                "model_number": "1",
                "protein_chain_or_asym": event["protein_chain_or_asym"],
                "cys_residue_id": "CYS:163-",
                "protein_altloc": "",
                "ligand_component_id": "CER",
                "ligand_chain_or_asym": event["ligand_chain_or_asym"],
                "ligand_altloc": "",
                "selected_connection_id": event["selected_connection_id"],
                "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
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
                "ligand_reactive_atom": "C2",
                "explicit_covalent_evidence": "true",
                "distance_only_inference_used": "false",
                "pair_authority_scope": AUTHORITY_SCOPE,
                "cross_structure_regiochemistry_generalization": "false",
                "all_CER_uses_C2": "false",
                "all_cerulenin_reaction_family_uses_C2": "false",
                "all_ketosynthase_CER_pairs_use_C2": "false",
                "reusable_pair_rule_created": "false",
                "role_partition_human_decision_available": "true",
                "role_partition_human_authoritative": "true",
                "selected_role_candidate_index_0based": "3",
                "role_profile": EXPECTED_ROLE_PROFILE,
                "warhead_atoms_json": _json_cell(list(WARHEAD_ROLE)),
                "linker_atoms_json": "[]",
                "scaffold_atoms_json": _json_cell(list(SCAFFOLD_ROLE)),
                "boundary_bonds_json": _json_cell(list(BOUNDARY_BONDS)),
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
                "PRE_status": PRE_STATUS,
                "PRE_source_graph_present": "false",
                "PRE_source_graph_count": "0",
                "PRE_mapping_count": "0",
                "PRE_topology_authority": "false",
                "PRE_geometry_authority": "false",
                "POST_to_PRE_copy_performed": "false",
                "PRE_zero_fill_performed": "false",
                "POST_source_evidence_available": "true",
                "POST_source_evidence_count": "4",
                "POST_geometry_training_authority": "false",
                "POST_geometry_training_target_created": "false",
                "reusable_chemistry_authority": "false",
                "reusable_role_authority": "false",
                "reaction_family_authority": "false",
                "authority_source": AUTHORITY_SOURCE,
                "authority_scope": AUTHORITY_SCOPE,
                "projection_of_frozen_formal_human_authority": "true",
                "new_human_authority_created_by_ingestion": "false",
            }
        )
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "review_unit": "CER",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": 4,
        "human_review_completed_count": 4,
        "task_relevant_count": 4,
        "chemistry_positive_count": 4,
        "reactive_pair_human_authoritative_count": 4,
        "role_partition_human_authoritative_count": 4,
        "DIRECT_event_count": 4,
        "STRICT_event_count": 0,
        "training_use_INCLUDE_count": 4,
        "applicable_task_set_counts": {"[0,3,4]": 4},
        "authoritative_task_labels_created_count": 0,
        "event_task_label_rows_materialized_count": 0,
        "PRE_topology_authority_count": 0,
        "PRE_geometry_authority_count": 0,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_count": 0,
        "formal_training_admitted_count": 0,
        "reusable_chemistry_authority_count": 0,
        "reusable_pair_authority_count": 0,
        "reusable_role_authority_count": 0,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "INGESTION_COMPLETE": True,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
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
        raise CERIngestionSafetyError(
            "COVAPIE_CER_INGESTION_V1_ERROR:UTF8_INVALID:" + label
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
            raise CERIngestionSafetyError(
                "COVAPIE_CER_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
                + relative.as_posix()
            ) from error
        _validate_text_payload(relative.as_posix(), payload)
        digest = _sha256(payload)
        try:
            verified = verify_bound_source_v2(
                path=path,
                expected_byte_count=len(payload),
                expected_sha256=digest,
                label="CER_CANDIDATE_SOURCE:" + relative.as_posix(),
                expected_executable=False,
            )
        except SourceBindingPolicyV2Error as error:
            raise CERIngestionSafetyError(
                "COVAPIE_CER_INGESTION_V1_ERROR:CANDIDATE_SOURCE_REJECTED:"
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
            "completed_positive_event_count": 99,
            "completed_positive_unit_count": 14,
            "completed_event_count": 127,
            "completed_unit_count": 19,
            "unreviewed_event_count": 211,
            "unreviewed_unit_count": 112,
            "CER_current_status": "CURRENTLY_UNREVIEWED",
            "CER_human_review_completed": False,
            "CER_event_count": 4,
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
        "artifact_role": "CER_COMPLETED_DECISION_INGESTION_NOT_RECONCILIATION_OR_ADMISSION",
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
        "canonical_task_contract": _canonical_task_contract(),
        "formal_projection": {
            "D1": "RELEVANT",
            "D2": "POSITIVE",
            "D3": "CONFIRM_OBSERVED_PAIR",
            "D4": "SELECT_CANDIDATE_3",
            "D5": "INCLUDE",
            "role_profile": EXPECTED_ROLE_PROFILE,
            "W_L_S_counts": [8, 0, 8],
            "boundary": "C4-C5 SING",
            "applicable_task_ids": [0, 3, 4],
        },
        "reactive_pair_authority": _pair_authority_boundary(),
        "selected_role_partition": _role_projection(),
        "reusable_authority_boundary": _reusable_authority_boundary(),
        "training_boundary": _training_boundary(),
        "geometry_boundary": _geometry_boundary(),
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
        "new_human_authority_created_by_ingestion": False,
        "projection_of_frozen_formal_human_authority": True,
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
    """Validate the deterministic CER projection and authority boundaries."""

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
        raise CERIngestionSafetyError(
            "COVAPIE_CER_INGESTION_V1_ERROR:MATRIX_UTF8_INVALID"
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
            or row["ligand_reactive_atom"] != "C2"
            or row["pair_authority_scope"] != AUTHORITY_SCOPE
            or row["cross_structure_regiochemistry_generalization"] != "false"
            or row["all_CER_uses_C2"] != "false"
            or row["reusable_pair_rule_created"] != "false"
            or row["selected_role_candidate_index_0based"] != "3"
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
            or row["task_applicability_determined"] != "true"
            or row["authoritative_task_labels_created"] != "false"
            or row["event_task_label_rows_materialized"] != "false"
            or row["human_training_use_disposition"] != "INCLUDE"
            or row["future_training_admission_candidate"] != "true"
            or row["formal_training_admitted"] != "false"
            or row["training_materialization_allowed"] != "false"
            or row["PRE_status"] != PRE_STATUS
            or row["PRE_source_graph_present"] != "false"
            or row["PRE_topology_authority"] != "false"
            or row["POST_source_evidence_available"] != "true"
            or row["POST_geometry_training_authority"] != "false"
            or row["reusable_chemistry_authority"] != "false"
            or row["reusable_role_authority"] != "false"
            or row["new_human_authority_created_by_ingestion"] != "false"
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
    try:
        root_metadata = target_root.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise CERIngestionSafetyError(
            "COVAPIE_CER_INGESTION_V1_ERROR:OUTPUT_ROOT_LSTAT_FAILED"
        ) from error
    if stat.S_ISLNK(root_metadata.st_mode):
        _fail("OUTPUT_ROOT_SYMLINK_FORBIDDEN")
    if not stat.S_ISDIR(root_metadata.st_mode):
        _fail("OUTPUT_ROOT_NOT_DIRECTORY")
    try:
        entries = tuple(target_root.iterdir())
    except OSError as error:
        raise CERIngestionSafetyError(
            "COVAPIE_CER_INGESTION_V1_ERROR:OUTPUT_ROOT_INVENTORY_READ_FAILED"
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
            raise CERIngestionSafetyError(
                "COVAPIE_CER_INGESTION_V1_ERROR:OUTPUT_ENTRY_LSTAT_FAILED:"
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
    """Write only the four deterministic CER output artifacts."""

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
            raise CERIngestionSafetyError(
                "COVAPIE_CER_INGESTION_V1_ERROR:OUTPUT_READ_FAILED:" + name
            ) from error
        try:
            verified = verify_bound_source_v2(
                path=path,
                expected_byte_count=len(payload),
                expected_sha256=_sha256(payload),
                label="CER_MATERIALIZED_OUTPUT:" + name,
                expected_executable=False,
            )
        except SourceBindingPolicyV2Error as error:
            raise CERIngestionSafetyError(
                "COVAPIE_CER_INGESTION_V1_ERROR:OUTPUT_REJECTED:" + name
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
        "CER_COMPLETED_DECISION_INGESTED": True,
        "new_human_authority_created_by_ingestion": False,
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
