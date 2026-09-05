"""Project frozen TP2 Exact4 human authority into metadata-only artifacts.

The formal JSON is parsed and independently validated.  Its frozen validator
is provenance identity only and is never parsed, imported, executed, or
subprocessed.  This additive stage creates availability metadata only; it does
not reconcile, refresh a census or queue, materialize labels/tensors, or train.
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
    "TP2IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = "covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_tp2_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_tp2_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_tp2_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_tp2_completed_decision_ingestion_manifest_v1"
BASELINE_COMMIT = "d5eae86a063a4a034b983dfa64ccfbe7ab1cd13b"

SOURCE_RELATIVE = Path("src/covalent_ext/covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1.py")
CHECKER_RELATIVE = Path("scripts/check_covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1.py")
TEST_RELATIVE = Path("tests/test_covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1.py")
OUTPUT_ROOT_RELATIVE = Path("data/derived/covalent_small/covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1")
SNAPSHOT = "covapie_tp2_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_tp2_event_task_label_availability_v1.csv"
SUMMARY = "covapie_tp2_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_tp2_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE, *OUTPUT_RELATIVE_PATHS)

STATE_ROOT = Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/TP2_COVAPIE_BULK_REVIEW_UNIT_C750E9F706F9E0AF")
FORMAL_DECISION_RELATIVE = STATE_ROOT / "formal-human-decision-v1/tp2_formal_human_decision_v1.json"
FORMAL_VALIDATOR_RELATIVE = STATE_ROOT / "formal-human-decision-v1/validate_tp2_formal_human_decision_v1.py"
PREPARATION_MANIFEST_RELATIVE = STATE_ROOT / "review-preparation-v1/tp2_review_preparation_manifest_v1.json"
EVENT_EVIDENCE_RELATIVE = STATE_ROOT / "review-preparation-v1/tp2_exact4_event_evidence_v1.csv"
GRAPH_EVIDENCE_RELATIVE = STATE_ROOT / "review-preparation-v1/tp2_graph_and_review_evidence_v1.json"
SOURCE_BINDING_POLICY_RELATIVE = Path("src/covalent_ext/covapie_source_binding_policy_v2.py")
CANONICAL_TASK_OWNER_RELATIVE = Path("src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py")
ROLE_RUNTIME_OWNER_RELATIVE = Path("src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py")
GENERIC_OWNER_RELATIVE = Path("src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py")
TASK_DOMAIN_NEGATIVE_PRECEDENT_RELATIVE = Path("src/covalent_ext/covapie_0d8_completed_decision_ingestion_and_task_label_availability_v1.py")
CENSUS_OWNER_RELATIVE = Path("src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_4lh_v1.py")
CENSUS_ROOT_RELATIVE = Path("data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_4lh_v1")
CENSUS_MATRIX_RELATIVE = CENSUS_ROOT_RELATIVE / "covapie_cumulative1000_current_global_readiness_census_with_4lh_v1.csv"
CENSUS_SUMMARY_RELATIVE = CENSUS_ROOT_RELATIVE / "covapie_cumulative1000_current_global_readiness_summary_with_4lh_v1.json"
CENSUS_MANIFEST_RELATIVE = CENSUS_ROOT_RELATIVE / "covapie_cumulative1000_current_global_readiness_manifest_with_4lh_v1.json"

FORMAL_DECISION_SCHEMA = "covapie_tp2_exact4_formal_human_decision_v1"
FORMAL_SEMANTIC_CANONICAL_SHA256 = "d1090a6073f5af89a82fcb204edc5854b901233fe435931ed83459ee4485e352"
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_C750E9F706F9E0AF"
EXPECTED_ROLE_PROFILE = "STRICT_LINKER_PRESENT_V1"
EXPECTED_COMPLETED_LANE = "COMPLETED_TASK_DOMAIN_NEGATIVE"
EXPECTED_LEGACY_STATUS = "COMPLETED_HUMAN_NEGATIVE"
AUTHORITY_SOURCE = "FORMAL_TP2_HUMAN_DECISION"
AUTHORITY_SCOPE = "CURRENT_TP2_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_NOT_AVAILABLE"
PRE_STATUS = "PRE_REACTION_UNRESOLVED"

EXPECTED_D6 = (
    "Treat the current TP2 Exact4 as chemistry-positive but task-domain negative for the present CovaPIE target-directed medicinal covalent small-molecule generation domain. The frozen 1F4C and 1F4D structures contain four explicit model-1 CYS-SG ↔ TP2-S1 covale connections with independently reproduced POST S-S distances of approximately 2.039–2.094 Å. These structures therefore support genuine sample-specific protein-ligand disulfide chemistry, but they do not establish a conventional medicinal electrophilic warhead or reusable thiol/disulfide warhead rule. The associated Erlanson et al. tethering context supports interpreting TP2 as a reversible disulfide capture fragment; 1F4D additionally uses an engineered L143C,C146S construct. For the current CovaPIE V1 objective, classify the Exact4 as NOT_RELEVANT while preserving chemistry POSITIVE and confirm the observed SG-S1 pair for these four events only. Select STRICT candidate 0 as the sample-level role partition: W=[S1], L=[C2,C3,N4], S=[C5,O21,C6,C20,C19,C18,N7,S8,O16,O17,C9,C10,C11,C12,C13,C14,C15], with S1-C2 as the warhead/linker boundary and N4-C5 as the linker/scaffold boundary. Record minimal seed [C5,O21,C6] with primary anchor C5. The selected STRICT profile has structural applicability to the canonical Exact5 tasks [0,1,2,3,4]: warhead_only, linker_plus_warhead, scaffold_plus_warhead, scaffold_only, and scaffold_plus_linker_plus_warhead; B3 is present and no sixth task exists. This role and task-applicability decision is sample-bound and creates no reusable chemistry, pair, role, reaction-family, warhead-rule, warhead-type, engineered-Cys, or cross-structure authority. PRE remains PRE_SOURCE_GRAPH_NOT_AVAILABLE / PRE_REACTION_UNRESOLVED; do not copy POST to PRE, zero-fill PRE, invent PRE coordinates or topology, infer leaving groups, reagents, or reaction edits. Set training use to NOT_APPLICABLE, not EXCLUDE_FROM_TRAINING_ONLY; human_training_excluded remains false and future_training_admission_candidate remains false. No formal training admission, tensor or mask target, current-runtime model usability, training materialization permission, parameter-update authority, or training readiness is created."
)
EXPECTED_D6_BYTE_COUNT = 2202
EXPECTED_D6_SHA256 = "92d77b46a67bdc489292c2417d268b94fa86eff3a2b4cbb68a35c4d687426cf5"

# event id, rank, pdb, protein asym, residue, ligand asym, connection, exact distance, reported distance
EXPECTED_EVENTS = (
    ("COVAPIE_CYS_SG_EVENT_V1:1F4C:A:CYS:146-:SG:F:TP2:S1", 42, "1F4C", "A", "CYS:146-", "F", "covale2", "2.072801", "2.073"),
    ("COVAPIE_CYS_SG_EVENT_V1:1F4C:B:CYS:146-:SG:I:TP2:S1", 43, "1F4C", "B", "CYS:146-", "I", "covale4", "2.039319", "2.039"),
    ("COVAPIE_CYS_SG_EVENT_V1:1F4D:A:CYS:143-:SG:E:TP2:S1", 44, "1F4D", "A", "CYS:143-", "E", "covale2", "2.039057", "2.039"),
    ("COVAPIE_CYS_SG_EVENT_V1:1F4D:B:CYS:143-:SG:I:TP2:S1", 45, "1F4D", "B", "CYS:143-", "I", "covale4", "2.094063", "2.094"),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)
WARHEAD_ATOMS = ("S1",)
LINKER_ATOMS = ("C2", "C3", "N4")
SCAFFOLD_ATOMS = ("C5", "O21", "C6", "C20", "C19", "C18", "N7", "S8", "O16", "O17", "C9", "C10", "C11", "C12", "C13", "C14", "C15")
HEAVY_ATOMS = tuple(sorted((*WARHEAD_ATOMS, *LINKER_ATOMS, *SCAFFOLD_ATOMS)))
MINIMAL_SEED = ("C5", "O21", "C6")
PRIMARY_ANCHOR = "C5"
BOUNDARY_BONDS = (
    {"atom_id_1": "S1", "atom_id_2": "C2", "bond_order": "SING", "role_pair": "warhead-linker"},
    {"atom_id_1": "N4", "atom_id_2": "C5", "bond_order": "SING", "role_pair": "linker-scaffold"},
)

CANONICAL_TASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (4, "scaffold_plus_linker_plus_warhead", "C", ("scaffold", "linker", "warhead"), ("minimal_seed",)),
)
GENERIC_FACT_FIELDS = (
    "canonical_event_id", "review_unit_id", "human_review_completed",
    "legacy_completed_review_status", "task_relevance_disposition",
    "chemistry_disposition", "training_disposition", "human_training_excluded",
    "source_decision_schema", "source_decision_sha256", "source_binding_path",
)
GENERIC_PROJECTION = {
    "human_review_completed": True,
    "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
    "task_relevance_disposition": "NOT_RELEVANT",
    "chemistry_disposition": "POSITIVE",
    "training_disposition": "NOT_APPLICABLE",
    "human_training_excluded": False,
}

# path, namespace, bytes, SHA256, executable, role, validation method
_Binding = tuple[Path, str, int, str, bool, str, str]
FORMAL_BINDINGS: tuple[_Binding, ...] = (
    (FORMAL_DECISION_RELATIVE, "project_parent_relative", 17825, "95fc125eefe09dd7ed81c9e95f2b76a084b889ece239aed5eb96215409315dc0", False, "TP2_FROZEN_FORMAL_HUMAN_DECISION", "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY"),
    (FORMAL_VALIDATOR_RELATIVE, "project_parent_relative", 38756, "3953a2e2f8915fff7a034716fc361b952daaccf8f167a4abb9d433a473284566", True, "TP2_FROZEN_FORMAL_VALIDATOR", "PROVENANCE_IDENTITY_ONLY_NOT_PARSED_IMPORTED_EXECUTED_OR_SUBPROCESSED"),
)
SUPPORTING_BINDINGS: tuple[_Binding, ...] = (
    (PREPARATION_MANIFEST_RELATIVE, "project_parent_relative", 13676, "bb3c7499390cbceaa0af18232aa61a5b250c31eeab52eaf926357c381680a64d", False, "TP2_REVIEW_PREPARATION_MANIFEST", "PARSED_JSON_SUPPORTING_EVIDENCE_IDENTITY"),
    (EVENT_EVIDENCE_RELATIVE, "project_parent_relative", 7981, "91ba5adb19fb5873bf6e203cf50c90e9787e96b183a713abbbf7b27906087510", False, "TP2_EXACT4_EVENT_EVIDENCE", "PARSED_CSV_SUPPORTING_EVIDENCE"),
    (GRAPH_EVIDENCE_RELATIVE, "project_parent_relative", 27352, "556513eced9b57254b2c53c14c0d121fd66c15f9f93b3a62ddc08a257e04dcf1", False, "TP2_GRAPH_AND_REVIEW_EVIDENCE", "PARSED_JSON_INDEPENDENT_EXACT21_GRAPH_PROOF"),
)
POLICY_BINDING: _Binding = (SOURCE_BINDING_POLICY_RELATIVE, "repository_relative", 3704, "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee", False, "PUBLISHED_SOURCE_BINDING_POLICY_V2", "IMPORTED_CONTENT_IDENTITY_AND_SECURITY_POLICY")
SEMANTIC_OWNER_BINDINGS: tuple[_Binding, ...] = (
    (CANONICAL_TASK_OWNER_RELATIVE, "repository_relative", 67274, "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b", False, "PUBLISHED_CANONICAL_EXACT5_OWNER", "PARSED_AST_LITERAL_CONTRACT_ONLY"),
    (ROLE_RUNTIME_OWNER_RELATIVE, "repository_relative", 37255, "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535", False, "PUBLISHED_STRICT_ROLE_RUNTIME_OWNER", "IMPORTED_AND_CALLED_FOR_ROLE_AND_SEED_VALIDATION"),
    (GENERIC_OWNER_RELATIVE, "repository_relative", 35925, "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548", False, "PUBLISHED_GENERIC_COMPLETED_DECISION_OWNER", "IMPORTED_READ_ONLY_FOR_EXACT11_COMPATIBILITY"),
    (TASK_DOMAIN_NEGATIVE_PRECEDENT_RELATIVE, "repository_relative", 106540, "1be00e2d03d7eb709fbe3ba11c577bd48308a77c03c795d77226da50599b2579", False, "PUBLISHED_0D8_TASK_DOMAIN_NEGATIVE_PRECEDENT", "PARSED_AST_GENERIC_CLASSIFICATION_AND_COMPLETED_LANE"),
)
CENSUS_BINDINGS: tuple[_Binding, ...] = (
    (CENSUS_OWNER_RELATIVE, "repository_relative", 71935, "932ae9aad18a3eeaed0071cb85b4758a529f1764f280a57e838dcff0061a6e42", False, "CURRENT_WITH_4LH_CENSUS_OWNER", "CONTENT_IDENTITY_READ_ONLY"),
    (CENSUS_MATRIX_RELATIVE, "repository_relative", 549694, "a8166f4c000dbeaa8c5672900fa1838748ad32c0b2810c1a132616d5c675e1aa", False, "CURRENT_WITH_4LH_CENSUS_MATRIX", "PARSED_CSV_PREFORMAL_STATE_READ_ONLY"),
    (CENSUS_SUMMARY_RELATIVE, "repository_relative", 21020, "7ad61675927467d4f1b5ab7e54a42649815b98bb2835201397f30432fcf1716b", False, "CURRENT_WITH_4LH_CENSUS_SUMMARY", "PARSED_JSON_PENDING_RANK_READ_ONLY"),
    (CENSUS_MANIFEST_RELATIVE, "repository_relative", 76244, "df3bd20c873834ef0f47a0f4eb0f0223edef3d83f74ae9959077994d9299e447", False, "CURRENT_WITH_4LH_CENSUS_MANIFEST", "PARSED_JSON_CONTENT_IDENTITY_READ_ONLY"),
)
ACTIVE_BINDINGS = (*FORMAL_BINDINGS, *SUPPORTING_BINDINGS, POLICY_BINDING, *SEMANTIC_OWNER_BINDINGS, *CENSUS_BINDINGS)


class TP2IngestionSafetyError(ValueError):
    """Raised when the frozen TP2 projection contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise TP2IngestionSafetyError("COVAPIE_TP2_INGESTION_V1_ERROR:" + reason)


def _expect(actual: object, expected: object, reason: str) -> None:
    if type(actual) is not type(expected) or actual != expected:
        _fail(reason)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


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
        raise TP2IngestionSafetyError("COVAPIE_TP2_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label) from error

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
        value = json.loads(text, object_pairs_hook=pairs_hook, parse_constant=reject_constant)
    except json.JSONDecodeError as error:
        raise TP2IngestionSafetyError("COVAPIE_TP2_INGESTION_V1_ERROR:JSON_PARSE_FAILED:" + label) from error
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _parse_csv(payload: bytes, label: str) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise TP2IngestionSafetyError("COVAPIE_TP2_INGESTION_V1_ERROR:CSV_UTF8_INVALID:" + label) from error
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        _fail("CSV_HEADER_INVALID:" + label)
    rows = list(reader)
    if any(None in row for row in rows):
        _fail("CSV_ROW_WIDTH_INVALID:" + label)
    return rows


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, extrasaction="raise", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _binding_record(binding: _Binding) -> dict[str, object]:
    path, namespace, byte_count, digest, executable, role, method = binding
    return {
        "path": path.as_posix(), "path_namespace": namespace, "byte_count": byte_count,
        "SHA256": digest, "semantic_source_identity": f"{namespace}:{path.as_posix()}@{digest}",
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "EXECUTABLE" if executable else "NON_EXECUTABLE",
        "source_role": role, "validation_method": method,
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


def _verify_binding(repo_root: Path, binding: _Binding, overrides: Mapping[Path, Path]) -> bytes:
    relative, _namespace, byte_count, digest, executable, role, _method = binding
    try:
        return verify_bound_source_v2(
            path=_resolve(repo_root, binding, overrides), expected_byte_count=byte_count,
            expected_sha256=digest, label=role + ":" + relative.as_posix(), expected_executable=executable,
        )
    except SourceBindingPolicyV2Error as error:
        raise TP2IngestionSafetyError("COVAPIE_TP2_INGESTION_V1_ERROR:SOURCE_BINDING_FAILED:" + relative.as_posix()) from error


def _verify_bindings(repo_root: Path, overrides: Mapping[Path, Path]) -> dict[Path, bytes]:
    return {binding[0]: _verify_binding(repo_root, binding, overrides) for binding in ACTIVE_BINDINGS}


def _literal_assignments(payload: bytes, names: Sequence[str], label: str) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8"), filename=label)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise TP2IngestionSafetyError("COVAPIE_TP2_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label) from error
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
                    raise TP2IngestionSafetyError("COVAPIE_TP2_INGESTION_V1_ERROR:SEMANTIC_OWNER_LITERAL_INVALID:" + target.id) from error
    if set(values) != set(names):
        _fail("SEMANTIC_OWNER_LITERAL_MISSING:" + label)
    return values


def _semantic_digest(formal: Mapping[str, Any]) -> str:
    semantic_keys = (
        "POST_boundary", "PRE_boundary", "canonical_Exact5", "formal_decisions",
        "formal_state", "record_role", "reusable_authority_map", "sample_authority_map",
        "sample_identity", "schema_version", "selected_role_context", "training_boundary",
    )
    if any(key not in formal for key in semantic_keys):
        _fail("FORMAL_SEMANTIC_VIEW_MISSING")
    return _sha256(_canonical_json({key: formal[key] for key in semantic_keys}))


def _validate_formal(formal: Mapping[str, Any]) -> None:
    expected_top = {
        "POST_boundary", "PRE_boundary", "canonical_Exact5", "formal_decisions",
        "formal_state", "operation_boundary", "output_inventory", "provenance", "readiness",
        "record_role", "reusable_authority_map", "sample_authority_map", "sample_identity",
        "schema_version", "selected_role_context", "semantic_freeze", "training_boundary",
    }
    if set(formal) != expected_top:
        _fail("FORMAL_TOP_LEVEL_FIELD_SET_DRIFT")
    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(formal.get("record_role"), "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY", "FORMAL_RECORD_ROLE_DRIFT")
    freeze = formal.get("semantic_freeze")
    if type(freeze) is not dict:
        _fail("FORMAL_SEMANTIC_FREEZE_MISSING")
    _expect(freeze.get("algorithm"), "SHA256_UTF8_SORTED_COMPACT_JSON_NO_TRAILING_LF", "FORMAL_SEMANTIC_ALGORITHM_DRIFT")
    _expect(freeze.get("semantic_canonical_SHA256"), FORMAL_SEMANTIC_CANONICAL_SHA256, "FORMAL_SEMANTIC_LITERAL_DRIFT")
    if _semantic_digest(formal) != FORMAL_SEMANTIC_CANONICAL_SHA256:
        _fail("FORMAL_SEMANTIC_DIGEST_RECOMPUTE_FAILED")

    state = formal.get("formal_state")
    if type(state) is not dict:
        _fail("FORMAL_STATE_MISSING")
    for key, expected in (
        ("unsigned", False), ("approved", True), ("decision_finalized", True),
        ("reviewer_id", "fmx"), ("attestor_id", "fmx"),
        ("authorization_origin", "EXTERNAL_HUMAN_CHAT_REVIEW"),
        ("human_review_completed", True), ("human_decision_created", True),
        ("formal_authority_created", True), ("machine_scientific_authority", False),
        ("machine_human_approval", False),
    ):
        _expect(state.get(key), expected, "FORMAL_STATE_DRIFT:" + key)

    decisions = formal.get("formal_decisions")
    if type(decisions) is not dict or set(decisions) != {
        "D1_task_relevance", "D2_chemistry", "D3_reactive_pair",
        "D4_role_candidate", "D5_training_use", "D6_human_scientific_context",
    }:
        _fail("FORMAL_DECISIONS_INVALID")
    for key, expected in (
        ("D1_task_relevance", "NOT_RELEVANT"), ("D2_chemistry", "POSITIVE"),
        ("D3_reactive_pair", "CONFIRM_OBSERVED_PAIR"),
        ("D4_role_candidate", "SELECT_CANDIDATE_0"),
        ("D5_training_use", "NOT_APPLICABLE"),
    ):
        row = decisions.get(key)
        if type(row) is not dict:
            _fail("FORMAL_DECISION_MISSING:" + key)
        _expect(row.get("decision"), expected, "FORMAL_DECISION_DRIFT:" + key)
    d3 = decisions["D3_reactive_pair"]
    for key, expected in (
        ("protein_atom", "SG"), ("ligand_atom", "S1"), ("scope", AUTHORITY_SCOPE),
        ("reactive_pair_sample_authoritative", True), ("reusable_pair_authority", False),
        ("all_TP2_uses_S1_authority", False),
        ("cross_structure_regiochemistry_generalization", False),
        ("engineered_Cys_generalization_authority", False),
    ):
        _expect(d3.get(key), expected, "FORMAL_D3_DRIFT:" + key)
    d4 = decisions["D4_role_candidate"]
    for key, expected in (
        ("candidate_id", "CANDIDATE_A"), ("role_profile", EXPECTED_ROLE_PROFILE),
        ("role_partition_sample_authoritative", True),
        ("candidate_B_runtime_valid_nonselected_alternative", True),
        ("candidate_B_authoritative", False),
    ):
        _expect(d4.get(key), expected, "FORMAL_D4_DRIFT:" + key)
    d5 = decisions["D5_training_use"]
    for key, expected in (
        ("because_D1_task_relevance", "NOT_RELEVANT"),
        ("future_training_admission_candidate", False),
        ("human_training_excluded", False), ("is_EXCLUDE_FROM_TRAINING_ONLY", False),
    ):
        _expect(d5.get(key), expected, "FORMAL_D5_DRIFT:" + key)
    d6 = decisions["D6_human_scientific_context"]
    if type(d6) is not dict:
        _fail("FORMAL_D6_MISSING")
    for key, expected in (
        ("text", EXPECTED_D6), ("UTF8_byte_count", EXPECTED_D6_BYTE_COUNT),
        ("SHA256", EXPECTED_D6_SHA256), ("frozen_exact_text", True),
        ("paraphrase_used", False),
    ):
        _expect(d6.get(key), expected, "FORMAL_D6_DRIFT:" + key)
    encoded_d6 = EXPECTED_D6.encode("utf-8")
    if len(encoded_d6) != EXPECTED_D6_BYTE_COUNT or _sha256(encoded_d6) != EXPECTED_D6_SHA256:
        _fail("INTERNAL_D6_IDENTITY_INVALID")

    identity = formal.get("sample_identity")
    if type(identity) is not dict:
        _fail("FORMAL_IDENTITY_MISSING")
    for key, expected in (
        ("canonical_event_ids", list(EXPECTED_EVENT_IDS)), ("event_count", 4),
        ("ligand_component_id", "TP2"), ("review_unit_id", EXPECTED_REVIEW_UNIT_ID),
        ("scaleup_ranks", list(EXPECTED_RANKS)), ("raw_priority_rank", 27),
        ("rank_systems_are_distinct", True), ("cross_structure_authority", False),
        ("ligand_wide_authority", False),
    ):
        _expect(identity.get(key), expected, "FORMAL_IDENTITY_DRIFT:" + key)

    authority = formal.get("sample_authority_map")
    if type(authority) is not dict or any(value is not True for value in authority.values()):
        _fail("FORMAL_SAMPLE_AUTHORITY_MAP_INVALID")
    role = formal.get("selected_role_context")
    if type(role) is not dict:
        _fail("FORMAL_ROLE_MISSING")
    expected_role = {
        "warhead_atom_ids": list(WARHEAD_ATOMS), "linker_atom_ids": list(LINKER_ATOMS),
        "scaffold_atom_ids": list(SCAFFOLD_ATOMS),
        "counts": {"warhead": 1, "linker": 3, "scaffold": 17, "total": 21},
        "boundaries": list(BOUNDARY_BONDS), "role_profile": EXPECTED_ROLE_PROFILE,
        "role_derived_task_ids": [0, 1, 2, 3, 4],
    }
    for key, expected in expected_role.items():
        _expect(role.get(key), expected, "FORMAL_ROLE_DRIFT:" + key)
    seed = role.get("minimal_seed")
    if type(seed) is not dict:
        _fail("FORMAL_SEED_MISSING")
    for key, expected in (
        ("atom_ids", list(MINIMAL_SEED)), ("primary_anchor", PRIMARY_ANCHOR),
        ("runtime_valid", True), ("runtime_reasons", []),
        ("reusable_minimal_seed_rule", False), ("cross_sample_seed_authority", False),
    ):
        _expect(seed.get(key), expected, "FORMAL_SEED_DRIFT:" + key)
    partition = role.get("partition_validation")
    if type(partition) is not dict or any(value is not True for value in partition.values()):
        _fail("FORMAL_PARTITION_CLAIMS_INVALID")
    runtime = role.get("published_runtime")
    if type(runtime) is not dict or runtime.get("runtime_valid") is not True or runtime.get("runtime_reasons") != []:
        _fail("FORMAL_RUNTIME_CLAIM_INVALID")

    exact5 = formal.get("canonical_Exact5")
    if type(exact5) is not dict:
        _fail("FORMAL_EXACT5_MISSING")
    for key, expected in (
        ("task_count", 5), ("B3_present", True), ("sixth_task", False),
        ("role_derived_structural_applicability_task_ids", [0, 1, 2, 3, 4]),
        ("task_applicability_determined", True),
        ("authoritative_task_labels_created", False),
        ("event_task_label_rows_materialized", False),
        ("tensor_target_created", False), ("training_mask_targets_available_now", False),
    ):
        _expect(exact5.get(key), expected, "FORMAL_EXACT5_DRIFT:" + key)
    _expect(
        exact5.get("tasks"),
        [{"task_id": task_id, "semantic_long_name": semantic, "display_alias": alias} for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS],
        "FORMAL_EXACT5_TASK_ROWS_DRIFT",
    )

    pre = formal.get("PRE_boundary")
    if type(pre) is not dict:
        _fail("FORMAL_PRE_MISSING")
    for key, expected in (
        ("supporting_adduct_graph_count", 0), ("candidate_PRE_free_source_graph_count", 0),
        ("mapping_count", 0), ("PRE_MAPPING_STATUS", PRE_MAPPING_STATUS),
        ("PRE_STATUS", PRE_STATUS), ("PRE_topology_authority", False),
        ("PRE_geometry_authority", False), ("PRE_coordinates_authority", False),
        ("PRE_reconstruction_performed", False), ("POST_to_PRE_copy", False),
        ("PRE_zero_fill", False), ("leaving_group_inferred", False),
        ("reagent_inferred", False), ("reaction_edit_inferred", False),
    ):
        _expect(pre.get(key), expected, "FORMAL_PRE_DRIFT:" + key)
    post = formal.get("POST_boundary")
    if type(post) is not dict:
        _fail("FORMAL_POST_MISSING")
    for key, expected in (
        ("POST_source_evidence_available", True), ("explicit_covalent_evidence", True),
        ("distance_only", False), ("POST_geometry_training_authority", False),
        ("POST_geometry_training_target_created", False),
    ):
        _expect(post.get(key), expected, "FORMAL_POST_DRIFT:" + key)
    training = formal.get("training_boundary")
    if type(training) is not dict:
        _fail("FORMAL_TRAINING_MISSING")
    required_training = {
        "human_training_use": "NOT_APPLICABLE", "human_training_excluded": False,
        "future_training_admission_candidate": False, "formal_training_admitted": False,
        "training_admission_created": False, "training_materialization_allowed": False,
        "formal_split_authority": False, "tensor_target_created": False,
        "training_mask_targets_available_now": False, "current_runtime_model_usable": False,
        "parameter_update_authorization": False, "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
    }
    for key, expected in required_training.items():
        _expect(training.get(key), expected, "FORMAL_TRAINING_DRIFT:" + key)
    reusable = formal.get("reusable_authority_map")
    if type(reusable) is not dict or any(value is not False for value in reusable.values()):
        _fail("FORMAL_REUSABLE_AUTHORITY_TRUE")
    operations = formal.get("operation_boundary")
    if type(operations) is not dict or any(value is not False for value in operations.values()):
        _fail("FORMAL_OPERATION_ALREADY_OCCURRED")


def _validate_preparation_manifest(payload: bytes) -> dict[str, object]:
    document = _strict_json(payload, "TP2_PREPARATION_MANIFEST")
    _expect(document.get("canonical_event_ids"), list(EXPECTED_EVENT_IDS), "PREPARATION_EVENT_IDS_DRIFT")
    _expect(document.get("raw_priority_rank"), 27, "PREPARATION_RAW_RANK_DRIFT")
    _expect(document.get("current_pending_rank"), 1, "PREPARATION_PENDING_RANK_DRIFT")
    graph = document.get("CCD_topology")
    if type(graph) is not dict:
        _fail("PREPARATION_GRAPH_SUMMARY_MISSING")
    required = {
        "component_identity": "TP2", "heavy_atom_count": 21,
        "heavy_heavy_bond_count": 22, "graph_connected": True,
        "source_observed_reactive_atom": "S1",
        "canonical_heavy_graph_SHA256": "a284be2c21489729884095627c663e7713b9e9d3019c9af84bb2badc48f083b5",
    }
    for key, expected in required.items():
        _expect(graph.get(key), expected, "PREPARATION_GRAPH_SUMMARY_DRIFT:" + key)
    pre = document.get("PRE_evidence")
    if type(pre) is not dict:
        _fail("PREPARATION_PRE_SUMMARY_MISSING")
    for key, expected in (
        ("supporting_adduct_graph_count_per_event", 0),
        ("candidate_PRE_free_source_graph_count_per_event", 0),
        ("source_mapping_count_per_event", 0),
        ("source_mapping_status", PRE_MAPPING_STATUS),
        ("final_reaction_status", PRE_STATUS), ("PRE_fabricated", False),
    ):
        _expect(pre.get(key), expected, "PREPARATION_PRE_DRIFT:" + key)
    return {"event_count": 4, "raw_priority_rank": 27, "current_pending_rank": 1}


def _validate_event_evidence(payload: bytes) -> dict[str, object]:
    rows = _parse_csv(payload, "TP2_EVENT_EVIDENCE")
    if len(rows) != 4 or tuple(row.get("canonical_event_id") for row in rows) != EXPECTED_EVENT_IDS:
        _fail("EVENT_EVIDENCE_EXACT4_DRIFT")
    for index, (row, expected) in enumerate(zip(rows, EXPECTED_EVENTS, strict=True)):
        required = {
            "package_role": "UNSIGNED_NON_AUTHORITATIVE_MACHINE_REVIEW_AID_PREPARATION",
            "event_index_0based": str(index), "scaleup_rank": str(expected[1]),
            "raw_priority_rank": "27", "current_pending_rank": "1",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID, "pdb_id": expected[2],
            "model_number": "1", "protein_label_asym_id": expected[3],
            "cys_residue_id": expected[4], "protein_reactive_atom": "SG",
            "ligand_component_id": "TP2", "ligand_label_asym_id": expected[5],
            "ligand_reactive_atom": "S1", "connection_id": expected[6],
            "connection_type": "covale", "explicit_covalent_evidence": "true",
            "distance_only_inference": "false", "exact_POST_distance_angstrom": expected[7],
            "reported_POST_distance_angstrom": expected[8], "POST_source_evidence_available": "true",
            "supporting_adduct_graph_count": "0", "candidate_PRE_free_source_graph_count": "0",
            "source_PRE_mapping_count": "0", "PRE_source_mapping_status": PRE_MAPPING_STATUS,
            "final_PRE_reaction_status": PRE_STATUS, "PRE_topology_created": "false",
            "PRE_coordinates_created": "false", "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false", "human_review_completed": "false",
            "chemistry_disposition": "UNRESOLVED", "task_relevance_disposition": "UNRESOLVED",
            "training_use_disposition": "UNRESOLVED", "formal_training_admitted": "false",
        }
        for key, value in required.items():
            if row.get(key) != value:
                _fail("EVENT_EVIDENCE_DRIFT:" + key)
    return {"event_count": 4, "event_ids": list(EXPECTED_EVENT_IDS), "scaleup_ranks": list(EXPECTED_RANKS), "raw_priority_rank": 27}


def _connected(atom_ids: Sequence[str], bonds: Sequence[tuple[str, str, str]]) -> bool:
    if not atom_ids:
        return False
    allowed = set(atom_ids)
    adjacency = {atom_id: set() for atom_id in allowed}
    for left, right, _order in bonds:
        if left in allowed and right in allowed:
            adjacency[left].add(right)
            adjacency[right].add(left)
    visited: set[str] = set()
    pending = [atom_ids[0]]
    while pending:
        atom_id = pending.pop()
        if atom_id in visited:
            continue
        visited.add(atom_id)
        pending.extend(adjacency[atom_id] - visited)
    return visited == allowed


def _validate_partition_graph(atom_ids: Sequence[str], bonds: Sequence[tuple[str, str, str]]) -> dict[str, object]:
    atom_set = set(atom_ids)
    roles = {"W": set(WARHEAD_ATOMS), "L": set(LINKER_ATOMS), "S": set(SCAFFOLD_ATOMS)}
    pairwise = not (roles["W"] & roles["L"] or roles["W"] & roles["S"] or roles["L"] & roles["S"])
    exhaustive = set().union(*roles.values()) == atom_set
    if not pairwise:
        _fail("GRAPH_PARTITION_NOT_PAIRWISE_DISJOINT")
    if not exhaustive:
        _fail("GRAPH_PARTITION_NOT_EXHAUSTIVE")
    seen_pairs: set[frozenset[str]] = set()
    for left, right, order in bonds:
        pair = frozenset((left, right))
        if left not in atom_set or right not in atom_set or left == right or not order:
            _fail("GRAPH_BOND_ENDPOINT_INVALID")
        if pair in seen_pairs:
            _fail("GRAPH_DUPLICATE_OR_PARALLEL_BOND")
        seen_pairs.add(pair)
    connectivity = {name: _connected(tuple(values), bonds) for name, values in roles.items()}
    for name, valid in connectivity.items():
        if not valid:
            _fail("GRAPH_" + name + "_DISCONNECTED")
    if "S1" not in roles["W"]:
        _fail("GRAPH_REACTIVE_S1_NOT_IN_W")
    role_by_atom = {atom_id: role for role, members in roles.items() for atom_id in members}
    boundaries: list[tuple[str, str, str, str]] = []
    for left, right, order in bonds:
        left_role, right_role = role_by_atom[left], role_by_atom[right]
        if left_role == right_role:
            continue
        if {left_role, right_role} == {"W", "L"}:
            warhead = left if left_role == "W" else right
            linker = right if left_role == "W" else left
            boundaries.append(("warhead-linker", warhead, linker, order))
        elif {left_role, right_role} == {"L", "S"}:
            linker = left if left_role == "L" else right
            scaffold = right if left_role == "L" else left
            boundaries.append(("linker-scaffold", linker, scaffold, order))
        else:
            _fail("GRAPH_UNEXPECTED_CROSS_ROLE_CLASS")
    expected = [
        ("warhead-linker", "S1", "C2", "SING"),
        ("linker-scaffold", "N4", "C5", "SING"),
    ]
    if sorted(boundaries) != sorted(expected) or len(boundaries) != 2:
        _fail("GRAPH_BOUNDARIES_NOT_EXACT2")
    return {
        "Exact21_count": 21, "partition_pairwise_disjoint": pairwise,
        "partition_exhaustive": exhaustive, "W_connected": connectivity["W"],
        "L_connected": connectivity["L"], "S_connected": connectivity["S"],
        "reactive_S1_in_W": True, "cross_role_boundary_count": 2,
        "cross_role_boundaries": [dict(boundary) for boundary in BOUNDARY_BONDS],
        "W_count": 1, "L_count": 3, "S_count": 17,
    }


def _validate_graph_evidence(payload: bytes) -> dict[str, object]:
    document = _strict_json(payload, "TP2_GRAPH_EVIDENCE")
    for key, expected in (
        ("review_unit_id", EXPECTED_REVIEW_UNIT_ID), ("ligand_component_id", "TP2"),
        ("canonical_event_ids", list(EXPECTED_EVENT_IDS)),
    ):
        _expect(document.get(key), expected, "GRAPH_IDENTITY_DRIFT:" + key)
    graph = document.get("canonical_heavy_atom_graph")
    if type(graph) is not dict:
        _fail("GRAPH_MISSING")
    atoms, raw_bonds = graph.get("atom_inventory"), graph.get("bond_inventory")
    if type(atoms) is not list or type(raw_bonds) is not list:
        _fail("GRAPH_INVENTORY_INVALID")
    atom_ids = tuple(sorted(row.get("atom_id") for row in atoms if type(row) is dict))
    _expect(atom_ids, HEAVY_ATOMS, "GRAPH_EXACT21_ATOMS_DRIFT")
    _expect(graph.get("heavy_atom_count"), 21, "GRAPH_HEAVY_COUNT_DRIFT")
    _expect(graph.get("heavy_heavy_bond_count"), 22, "GRAPH_BOND_COUNT_DRIFT")
    _expect(graph.get("canonical_heavy_graph_sha256"), "a284be2c21489729884095627c663e7713b9e9d3019c9af84bb2badc48f083b5", "GRAPH_CANONICAL_SHA_DRIFT")
    bonds = tuple((row.get("atom_id_1"), row.get("atom_id_2"), row.get("bond_order")) for row in raw_bonds if type(row) is dict)
    if len(bonds) != 22 or any(type(value) is not str for bond in bonds for value in bond):
        _fail("GRAPH_BOND_INVENTORY_DRIFT")
    proof = _validate_partition_graph(atom_ids, bonds)  # type: ignore[arg-type]
    return {**proof, "heavy_atoms": list(atom_ids), "heavy_bonds": [list(bond) for bond in bonds]}


def _validate_semantic_owners(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    canonical = _literal_assignments(payloads[CANONICAL_TASK_OWNER_RELATIVE], ("EXACT3_ROLES", "CANONICAL_TASKS"), CANONICAL_TASK_OWNER_RELATIVE.as_posix())
    _expect(canonical["EXACT3_ROLES"], ("scaffold", "linker", "warhead"), "CANONICAL_EXACT3_OWNER_DRIFT")
    _expect(canonical["CANONICAL_TASKS"], CANONICAL_TASKS, "CANONICAL_EXACT5_OWNER_DRIFT")
    precedent = _literal_assignments(payloads[TASK_DOMAIN_NEGATIVE_PRECEDENT_RELATIVE], ("EXPECTED_COMPLETED_LANE", "GENERIC_FACT_FIELDS", "GENERIC_PROJECTION"), TASK_DOMAIN_NEGATIVE_PRECEDENT_RELATIVE.as_posix())
    _expect(precedent["EXPECTED_COMPLETED_LANE"], EXPECTED_COMPLETED_LANE, "TASK_DOMAIN_NEGATIVE_LANE_PRECEDENT_DRIFT")
    _expect(precedent["GENERIC_FACT_FIELDS"], GENERIC_FACT_FIELDS, "GENERIC_EXACT11_PRECEDENT_DRIFT")
    _expect(precedent["GENERIC_PROJECTION"], GENERIC_PROJECTION, "GENERIC_CLASSIFICATION_PRECEDENT_DRIFT")
    return {"global_canonical_task_count": 5, "B3_present": True, "sixth_task": False, "completed_lane": EXPECTED_COMPLETED_LANE}


def _runtime_validation(repo_root: Path, graph: Mapping[str, object]) -> dict[str, object]:
    module = importlib.import_module("covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1")
    if Path(module.__file__).resolve() != (repo_root / ROLE_RUNTIME_OWNER_RELATIVE).resolve():
        _fail("ROLE_RUNTIME_IMPORT_PATH_INVALID")
    bonds = tuple(tuple(bond) for bond in graph["heavy_bonds"])
    role = module.validate_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE, retained_heavy_atoms=tuple(graph["heavy_atoms"]),
        scaffold_atoms=SCAFFOLD_ATOMS, linker_atoms=LINKER_ATOMS, warhead_atoms=WARHEAD_ATOMS,
        reactive_atom_id="S1", explicit_graph_bonds=bonds,
    )
    if (
        role.role_profile != EXPECTED_ROLE_PROFILE or role.valid is not True
        or tuple(role.reasons) != () or role.warhead_count != 1
        or role.linker_count != 3 or role.scaffold_count != 17
        or role.scaffold_linker_boundary_applicable is not True
        or role.linker_warhead_boundary_applicable is not True
        or role.direct_scaffold_warhead_boundary_applicable is not False
    ):
        _fail("PUBLISHED_STRICT_RUNTIME_VALIDATION_FAILED")
    seed = module.validate_minimal_seed_for_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE, seed_atoms=MINIMAL_SEED,
        scaffold_atoms=SCAFFOLD_ATOMS, linker_atoms=LINKER_ATOMS,
        warhead_atoms=WARHEAD_ATOMS, explicit_graph_bonds=bonds,
        primary_anchor_atom_id=PRIMARY_ANCHOR,
    )
    if seed.valid is not True or tuple(seed.reasons) != () or seed.primary_anchor_atom_id != PRIMARY_ANCHOR:
        _fail("PUBLISHED_SEED_RUNTIME_VALIDATION_FAILED")
    applicable = tuple(module.valid_canonical_task_ids_for_role_profile_v1(EXPECTED_ROLE_PROFILE))
    _expect(applicable, (0, 1, 2, 3, 4), "PUBLISHED_STRICT_TASK_IDS_DRIFT")
    return {
        "role_validator": "validate_role_profile_v1", "role_valid": True,
        "role_reasons": [], "counts": {"W": 1, "L": 3, "S": 17},
        "seed_validator": "validate_minimal_seed_for_role_profile_v1",
        "seed_valid": True, "seed_reasons": [], "primary_anchor": PRIMARY_ANCHOR,
        "applicable_task_ids": list(applicable), "runtime_import_path_exact": True,
    }


def _generic_compatibility(repo_root: Path) -> dict[str, object]:
    module = importlib.import_module("covalent_ext.covapie_completed_human_decision_reconciliation_v1")
    if Path(module.__file__).resolve() != (repo_root / GENERIC_OWNER_RELATIVE).resolve():
        _fail("GENERIC_OWNER_IMPORT_PATH_INVALID")
    binding = module.SourceBinding(
        source_path=FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative", byte_count=FORMAL_BINDINGS[0][2],
        sha256=FORMAL_BINDINGS[0][3], schema_version=FORMAL_DECISION_SCHEMA,
        review_unit_id=EXPECTED_REVIEW_UNIT_ID,
    )
    module._validate_source_binding(binding)
    facts: list[dict[str, object]] = []
    for event_id in EXPECTED_EVENT_IDS:
        fact = module.NormalizedCompletedDecisionFact(
            canonical_event_id=event_id, review_unit_id=EXPECTED_REVIEW_UNIT_ID,
            **GENERIC_PROJECTION, source_decision_schema=FORMAL_DECISION_SCHEMA,
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
    return {
        "generic_exact11_compatibility_pass": True, "generic_fact_field_count": 11,
        "generic_fact_fields": list(GENERIC_FACT_FIELDS), "accepted_fact_count": 4,
        "facts": facts, "rich_fields_leaked": False, "reconciliation_performed": False,
        "actual_source_binding": {
            "source_path": binding.source_path, "path_namespace": binding.path_namespace,
            "byte_count": binding.byte_count, "sha256": binding.sha256,
            "schema_version": binding.schema_version, "review_unit_id": binding.review_unit_id,
        },
    }


def _current_census(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    rows = _parse_csv(payloads[CENSUS_MATRIX_RELATIVE], "CURRENT_WITH_4LH_CENSUS")
    if len(rows) != 1000 or len({row.get("canonical_event_id") for row in rows}) != 1000:
        _fail("CURRENT_CENSUS_UNIVERSE_DRIFT")
    targets = [row for row in rows if row.get("canonical_event_id") in set(EXPECTED_EVENT_IDS)]
    unit_rows = [row for row in rows if row.get("review_unit_id") == EXPECTED_REVIEW_UNIT_ID]
    if len(targets) != 4 or len(unit_rows) != 4 or tuple(row.get("canonical_event_id") for row in targets) != EXPECTED_EVENT_IDS:
        _fail("CURRENT_CENSUS_TP2_EXACT4_DRIFT")
    prior = {
        "current_global_status": "CURRENTLY_UNREVIEWED", "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false", "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED", "training_use_disposition": "UNRESOLVED",
        "reactive_pair_sample_authoritative": "false", "role_partition_sample_authoritative": "false",
        "formal_training_admitted": "false", "current_runtime_model_usable": "false",
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
    }
    for row in targets:
        for key, expected in prior.items():
            if row.get(key) != expected:
                _fail("CURRENT_CENSUS_TP2_PRIOR_STATE_DRIFT:" + key)
    summary = _strict_json(payloads[CENSUS_SUMMARY_RELATIVE], "CURRENT_WITH_4LH_SUMMARY")
    _strict_json(payloads[CENSUS_MANIFEST_RELATIVE], "CURRENT_WITH_4LH_MANIFEST")
    pending = summary.get("top_pending_review_units_by_event_yield")
    if type(pending) is not list or not pending or type(pending[0]) is not dict:
        _fail("CURRENT_CENSUS_PENDING_QUEUE_MISSING")
    expected_pending = {
        "rank": 1, "raw_priority_rank": 27, "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": 4, "ligand_component_ids": ["TP2"], "pdb_ids": ["1F4C", "1F4D"],
        "current_review_status": "CURRENTLY_UNREVIEWED",
    }
    for key, expected in expected_pending.items():
        _expect(pending[0].get(key), expected, "CURRENT_CENSUS_PENDING_RANK1_DRIFT:" + key)
    return {
        "row_count": 1000, "TP2_event_count": 4,
        "TP2_current_global_status": "CURRENTLY_UNREVIEWED",
        "TP2_human_review_completed": False, "TP2_task_relevance": "UNRESOLVED",
        "TP2_chemistry": "UNRESOLVED", "TP2_training_use": "UNRESOLVED",
        "TP2_pair_authority": False, "TP2_role_authority": False,
        "TP2_formal_training_admitted": False, "current_pending_rank": 1,
        "raw_priority_rank": 27, "census_modified_by_ingestion": False,
    }


def load_frozen_formal_decision_v1(
    repo_root: Path, *, formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Bind and independently validate the frozen TP2 authority and evidence."""
    root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    payloads = _verify_bindings(root, overrides)
    formal = _strict_json(payloads[FORMAL_DECISION_RELATIVE], "TP2_FORMAL_DECISION")
    _validate_formal(formal)
    preparation = _validate_preparation_manifest(payloads[PREPARATION_MANIFEST_RELATIVE])
    events = _validate_event_evidence(payloads[EVENT_EVIDENCE_RELATIVE])
    graph = _validate_graph_evidence(payloads[GRAPH_EVIDENCE_RELATIVE])
    owners = _validate_semantic_owners(payloads)
    runtime = _runtime_validation(root, graph)
    generic = _generic_compatibility(root)
    census = _current_census(payloads)
    return {
        "formal_document": formal, "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "supporting_bindings": [_binding_record(value) for value in SUPPORTING_BINDINGS],
        "source_binding_policy_binding": _binding_record(POLICY_BINDING),
        "semantic_owner_bindings": [_binding_record(value) for value in SEMANTIC_OWNER_BINDINGS],
        "current_census_bindings": [_binding_record(value) for value in CENSUS_BINDINGS],
        "preparation_validation": preparation, "event_evidence_validation": events,
        "graph_structural_proof": {key: graph[key] for key in (
            "Exact21_count", "partition_pairwise_disjoint", "partition_exhaustive",
            "W_connected", "L_connected", "S_connected", "reactive_S1_in_W",
            "cross_role_boundary_count", "cross_role_boundaries", "W_count", "L_count", "S_count",
        )},
        "published_runtime_validation": runtime, "semantic_owner_validation": owners,
        "generic_Exact11_compatibility": generic, "current_census_boundary": census,
    }


def _task_contract() -> dict[str, object]:
    return {
        "global_canonical_tasks": [
            {"task_id": task_id, "semantic_long_name": semantic, "display_alias": alias,
             "generated_roles": list(generated), "fixed_or_seed_roles": list(fixed)}
            for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5, "B3_present": True, "sixth_task": False,
        "strict_profile_applicable_task_ids": [0, 1, 2, 3, 4],
        "strict_profile_task_applicability": [
            {"task_id": task_id, "semantic_long_name": semantic, "display_alias": alias,
             "role_profile": EXPECTED_ROLE_PROFILE, "structurally_applicable": True}
            for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
        ],
        "task_applicability_determined": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "training_mask_targets_available_now": False,
        "tensor_target_created": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "human_training_use_disposition": "NOT_APPLICABLE",
        "training_use_human_authoritative": True, "human_training_excluded": False,
        "future_training_admission_candidate": False, "formal_training_admitted": False,
        "training_admission_created": False, "training_materialization_allowed": False,
        "formal_split_authority": False, "tensor_target_created": False,
        "training_mask_targets_available_now": False, "current_runtime_model_usable": False,
        "parameter_update_authorization": False, "ready_for_training": False,
    }


def _pre_boundary() -> dict[str, object]:
    return {
        "supporting_PRE_source_graph_count": 0, "PRE_source_graph_present": False,
        "PRE_source_graph_count": 0, "PRE_mapping_count": 0,
        "PRE_mapping_status": PRE_MAPPING_STATUS, "PRE_status": PRE_STATUS,
        "PRE_topology_authority": False, "PRE_geometry_authority": False,
        "PRE_coordinates_authority": False, "PRE_reconstruction_performed": False,
        "POST_to_PRE_copy": False, "PRE_zero_fill": False,
        "leaving_group_inferred": False, "reagent_inferred": False,
        "reaction_edit_inferred": False,
    }


def _post_boundary() -> dict[str, object]:
    return {
        "POST_source_evidence_available": True, "explicit_covalent_evidence": True,
        "distance_only_inference": False, "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
    }


def _reusable_boundary() -> dict[str, bool]:
    return {key: False for key in (
        "reusable_chemistry_authority", "reusable_pair_authority", "reusable_role_authority",
        "reaction_family_authority", "warhead_rule_authority", "warhead_type_authority",
        "generic_thiol_disulfide_warhead_authority", "all_TP2_uses_S1_authority",
        "engineered_Cys_generalization_authority", "cross_structure_authority",
        "ligand_wide_authority", "reusable_minimal_seed_rule", "cross_sample_seed_authority",
    )}


def _event_projection(event: tuple[object, ...]) -> dict[str, object]:
    return {
        "canonical_event_id": event[0], "scaleup_rank": event[1],
        "raw_review_unit_priority_rank": 27, "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": event[2], "model_number": 1, "protein_chain_or_asym": event[3],
        "cys_residue_id": event[4], "protein_altloc": None,
        "ligand_component_id": "TP2", "ligand_chain_or_asym": event[5],
        "ligand_altloc": None, "selected_connection_id": event[6],
        "POST_distance_angstrom": float(event[7]), "POST_distance_frozen_lexeme": event[7],
        "reported_POST_distance_angstrom": float(event[8]),
        "reported_POST_distance_frozen_lexeme": event[8],
        "completed_lane": EXPECTED_COMPLETED_LANE, "human_review_completed": True,
        "task_relevance": "NOT_RELEVANT", "task_relevance_human_authority": True,
        "human_task_relevance_decision": "NOT_RELEVANT", "task_relevance_human_authoritative": True,
        "chemistry": "POSITIVE", "chemistry_known_positive": True,
        "chemistry_human_authority": True, "human_chemistry_decision": "POSITIVE",
        "chemistry_human_authoritative": True, "negative_chemistry": False,
        "task_domain_negative": True, "positive_generative_supervision_eligible": False,
        "reactive_pair_human_decision_available": True, "reactive_pair_human_authoritative": True,
        "protein_reactive_atom": "SG", "ligand_reactive_atom": "S1",
        "pair_authority_scope": AUTHORITY_SCOPE, "reusable_pair_rule_created": False,
        "cross_structure_regiochemistry_generalization": False,
        "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True, "selected_candidate_index_0based": 0,
        "role_profile": EXPECTED_ROLE_PROFILE, "role_authority_scope": AUTHORITY_SCOPE,
        "reusable_role_authority": False, "task_applicability_determined": True,
        "canonical_mask_structural_labels_available": True,
        "authoritative_task_labels_created": False, "event_task_label_rows_materialized": False,
        "formal_event_training_use_decision": "NOT_APPLICABLE",
        "event_training_use_human_decision_available": True,
        "human_training_use_disposition": "NOT_APPLICABLE",
        "training_use_human_authoritative": True, "training_use_allowed": False,
        "human_training_excluded": False, "candidate_for_future_training_admission": False,
        "future_training_admission_candidate": False, "training_admitted": False,
        "formal_training_admitted": False, "training_admission_created": False,
        "formal_split_authority": False, "training_materialization_allowed_now": False,
        "training_materialization_allowed": False, "tensor_target_created": False,
        "model_supervision_usable": False, "training_mask_targets_available_now": False,
        "current_runtime_model_usable": False, "parameter_update_authorization": False,
        "READY_FOR_TRAINING": False, **_pre_boundary(), **_post_boundary(),
        **_reusable_boundary(), "authority_source": AUTHORITY_SOURCE,
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False, "metadata_only": True,
        "dataset_mutated": False, "training_dataset_changed": False,
        "tensorization": False, "loader_modified": False, "batch_modified": False,
        "model_forward": False, "loss": False, "backward": False,
        "optimizer": False, "parameter_update": False, "training": False,
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION, "stage": SCHEMA_VERSION,
        "artifact_role": "TP2_FROZEN_HUMAN_AUTHORITY_DETERMINISTIC_METADATA_PROJECTION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "formal_identity": {
            "schema_version": FORMAL_DECISION_SCHEMA, "byte_count": FORMAL_BINDINGS[0][2],
            "SHA256": FORMAL_BINDINGS[0][3],
            "semantic_canonical_SHA256": FORMAL_SEMANTIC_CANONICAL_SHA256,
            "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
            "unsigned": False, "approved": True, "decision_finalized": True,
            "reviewer_id": "fmx", "attestor_id": "fmx",
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "human_review_completed": True, "human_decision_created": True,
            "formal_authority_created": True, "machine_scientific_authority": False,
            "machine_human_approval": False,
        },
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "supporting_bindings": bound["supporting_bindings"],
        "source_binding_policy_binding": bound["source_binding_policy_binding"],
        "semantic_owner_bindings": bound["semantic_owner_bindings"],
        "current_census_bindings": bound["current_census_bindings"],
        "human_authorization": {
            "D1_task_relevance": "NOT_RELEVANT", "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR", "D4_role_candidate": "SELECT_CANDIDATE_0",
            "D5_training_use": "NOT_APPLICABLE", "D6_scientific_context": EXPECTED_D6,
            "formal_decision_authority_is_human": True,
        },
        "D6_provenance": {"D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT, "D6_utf8_sha256": EXPECTED_D6_SHA256, "exact_text_verified": True, "paraphrase_used": False},
        "events": [_event_projection(event) for event in EXPECTED_EVENTS],
        "generic_Exact11_compatibility": bound["generic_Exact11_compatibility"],
        "reactive_pair_authority": {
            "protein_reactive_atom": "SG", "ligand_reactive_atom": "S1",
            "scope": AUTHORITY_SCOPE, "sample_level_authoritative": True,
            "reusable_pair_authority": False, "all_TP2_uses_S1_authority": False,
            "cross_structure_regiochemistry_generalization": False,
            "engineered_Cys_generalization_authority": False,
        },
        "selected_role_partition": {
            "selected_role_candidate_index_0based": 0, "role_profile": EXPECTED_ROLE_PROFILE,
            "W": list(WARHEAD_ATOMS), "L": list(LINKER_ATOMS), "S": list(SCAFFOLD_ATOMS),
            "counts": {"W": 1, "L": 3, "S": 17, "Exact": 21},
            "boundary_bonds": list(BOUNDARY_BONDS), "minimal_seed_atom_ids": list(MINIMAL_SEED),
            "primary_anchor_atom_id": PRIMARY_ANCHOR, "sample_level_authoritative": True,
            "authority_scope": AUTHORITY_SCOPE, "reusable_role_authority": False,
            "candidate_B_runtime_valid_nonselected_alternative": True,
            "candidate_B_authoritative": False,
            "published_runtime_validation": bound["published_runtime_validation"],
        },
        "structural_validation": bound["graph_structural_proof"],
        "canonical_task_contract": _task_contract(), "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(), "training_boundary": _training_boundary(),
        "reusable_authority_boundary": _reusable_boundary(),
        "current_census_boundary": bound["current_census_boundary"],
        "authority_boundary": {
            "projection_of_frozen_formal_human_authority": True,
            "new_human_authority_created_by_ingestion": False,
            "authoritative_task_labels_created": False,
            "event_task_label_rows_materialized": False,
            "training_mask_targets_available_now": False,
            "formal_training_admitted": False, "ready_for_training": False,
            "reconciliation": False, "census_refresh": False,
            "queue_refresh": False, "training": False,
        },
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "raw_review_unit_priority_rank", "review_unit_id",
    "pdb_id", "model_number", "protein_chain_or_asym", "cys_residue_id", "protein_altloc",
    "ligand_component_id", "ligand_chain_or_asym", "ligand_altloc", "selected_connection_id",
    "POST_distance_angstrom", "reported_POST_distance_angstrom", "completed_lane",
    "legacy_completed_review_status", "human_review_completed", "task_relevance",
    "task_relevance_human_authority", "human_task_relevance_decision",
    "task_relevance_human_authoritative", "chemistry", "chemistry_known_positive",
    "chemistry_human_authority", "human_chemistry_decision", "chemistry_human_authoritative",
    "negative_chemistry", "task_domain_negative", "positive_generative_supervision_eligible",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "protein_reactive_atom", "ligand_reactive_atom", "pair_authority_scope",
    "reusable_pair_rule_created", "cross_structure_regiochemistry_generalization",
    "all_TP2_uses_S1_authority", "engineered_Cys_generalization_authority",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "selected_candidate_index_0based", "role_profile", "warhead_atoms_json",
    "linker_atoms_json", "scaffold_atoms_json", "W_L_S_counts_json", "boundary_bonds_json",
    "Exact21_count", "partition_pairwise_disjoint", "partition_exhaustive", "warhead_connected",
    "linker_connected", "scaffold_connected", "reactive_S1_in_W", "minimal_seed_atoms_json",
    "primary_anchor_atom_id", "role_authority_scope", "reusable_role_authority",
    "global_canonical_task_count", "B3_present", "sixth_task",
    "canonical_task_applicability_json", "structurally_applicable_task_ids_json",
    "strict_profile_applicable_task_ids_json", "task_applicability_determined",
    "canonical_mask_structural_labels_available", "authoritative_task_labels_created",
    "event_task_label_rows_materialized", "formal_event_training_use_decision",
    "event_training_use_human_decision_available", "human_training_use_disposition",
    "training_use_human_authoritative", "training_use_allowed", "human_training_excluded",
    "candidate_for_future_training_admission", "future_training_admission_candidate",
    "training_admitted", "formal_training_admitted", "training_admission_created",
    "formal_split_authority", "training_materialization_allowed_now",
    "training_materialization_allowed", "tensor_target_created", "model_supervision_usable",
    "training_mask_targets_available_now", "current_runtime_model_usable",
    "parameter_update_authorization", "READY_FOR_TRAINING", "supporting_PRE_source_graph_count",
    "PRE_source_graph_present", "PRE_source_graph_count", "PRE_mapping_count",
    "PRE_mapping_status", "PRE_status", "PRE_topology_authority", "PRE_geometry_authority",
    "PRE_coordinates_authority", "PRE_reconstruction_performed", "POST_to_PRE_copy",
    "PRE_zero_fill", "leaving_group_inferred", "reagent_inferred", "reaction_edit_inferred",
    "POST_source_evidence_available", "explicit_covalent_evidence", "distance_only_inference",
    "POST_geometry_training_authority", "POST_geometry_training_target_created",
    "reusable_chemistry_authority", "reusable_pair_authority",
    "reaction_family_authority", "warhead_rule_authority", "warhead_type_authority",
    "generic_thiol_disulfide_warhead_authority", "cross_structure_authority",
    "ligand_wide_authority", "reusable_minimal_seed_rule", "cross_sample_seed_authority",
    "authority_source", "projection_of_frozen_formal_human_authority",
    "new_human_authority_created_by_ingestion", "metadata_only", "dataset_mutated",
    "training_dataset_changed", "tensorization", "loader_modified", "batch_modified",
    "model_forward", "loss", "backward", "optimizer", "parameter_update", "training",
)


def _matrix_rows(snapshot: Mapping[str, Any], proof: Mapping[str, object]) -> list[dict[str, object]]:
    expected_proof = {
        "Exact21_count": 21, "partition_pairwise_disjoint": True,
        "partition_exhaustive": True, "W_connected": True, "L_connected": True,
        "S_connected": True, "reactive_S1_in_W": True, "cross_role_boundary_count": 2,
        "cross_role_boundaries": [dict(boundary) for boundary in BOUNDARY_BONDS],
        "W_count": 1, "L_count": 3, "S_count": 17,
    }
    if dict(proof) != expected_proof:
        _fail("MATRIX_STRUCTURAL_CLAIMS_NOT_SOURCE_VERIFIED")
    rows: list[dict[str, object]] = []
    applicability = snapshot["canonical_task_contract"]["strict_profile_task_applicability"]
    for event in snapshot["events"]:
        row: dict[str, object] = {key: "" for key in MATRIX_HEADER}
        for key, value in event.items():
            if key in row:
                row[key] = "true" if value is True else "false" if value is False else "" if value is None else str(value)
        row.update({
            "scaleup_rank": str(event["scaleup_rank"]), "raw_review_unit_priority_rank": "27",
            "model_number": "1", "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
            "reported_POST_distance_angstrom": event["reported_POST_distance_frozen_lexeme"],
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "warhead_atoms_json": _json_cell(list(WARHEAD_ATOMS)),
            "linker_atoms_json": _json_cell(list(LINKER_ATOMS)),
            "scaffold_atoms_json": _json_cell(list(SCAFFOLD_ATOMS)),
            "W_L_S_counts_json": "[1,3,17]", "boundary_bonds_json": _json_cell(list(BOUNDARY_BONDS)),
            "Exact21_count": "21", "partition_pairwise_disjoint": "true",
            "partition_exhaustive": "true", "warhead_connected": "true",
            "linker_connected": "true", "scaffold_connected": "true", "reactive_S1_in_W": "true",
            "minimal_seed_atoms_json": _json_cell(list(MINIMAL_SEED)),
            "primary_anchor_atom_id": PRIMARY_ANCHOR, "global_canonical_task_count": "5",
            "B3_present": "true", "sixth_task": "false",
            "canonical_task_applicability_json": _json_cell(applicability),
            "structurally_applicable_task_ids_json": "[0,1,2,3,4]",
            "strict_profile_applicable_task_ids_json": "[0,1,2,3,4]",
        })
        rows.append(row)
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION, "stage": SCHEMA_VERSION,
        "review_unit": "TP2", "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": 4, "completed_lane": EXPECTED_COMPLETED_LANE,
        "chemistry_positive_event_count": 4, "task_not_relevant_event_count": 4,
        "task_domain_negative_chemistry_positive_event_count": 4,
        "pair_authoritative_event_count": 4, "role_authoritative_event_count": 4,
        "STRICT_profile_event_count": 4,
        "canonical_mask_structural_labels_available_event_count": 4,
        "task_applicability_determined_event_count": 4,
        "authoritative_task_label_event_count": 0,
        "event_task_label_rows_materialized_count": 0,
        "training_NOT_APPLICABLE_event_count": 4, "human_training_excluded_count": 0,
        "future_training_admission_candidate_count": 0, "formal_training_admitted_count": 0,
        "POST_source_evidence_count": 4, "POST_training_authority_count": 0,
        "PRE_authority_count": 0, "global_canonical_task_count": 5,
        "B3_present": True, "sixth_task": False, "applicable_task_ids": [0, 1, 2, 3, 4],
        "W_count": 1, "L_count": 3, "S_count": 17,
        "role_boundaries": ["S1-C2/SING", "N4-C5/SING"],
        "minimal_seed": list(MINIMAL_SEED), "primary_anchor": PRIMARY_ANCHOR,
        "generic_legacy_status": EXPECTED_LEGACY_STATUS,
        "generic_training_disposition": "NOT_APPLICABLE", "human_training_excluded": False,
        "PRE_mapping_status": PRE_MAPPING_STATUS, "PRE_status": PRE_STATUS,
        "authoritative_task_labels_created": False, "event_task_label_rows_materialized": False,
        "training_mask_targets_available_now": False,
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
        "RECONCILIATION": False, "CENSUS_REFRESH": False, "QUEUE_REFRESH": False,
        "TRAINING_STARTED": False, "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "STEP12D_STATUS": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
    }


def _candidate_source_records(repo_root: Path) -> list[dict[str, object]]:
    records = []
    for relative in (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE):
        path = repo_root / relative
        try:
            metadata, payload = path.lstat(), path.read_bytes()
        except OSError as error:
            raise TP2IngestionSafetyError("COVAPIE_TP2_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:" + relative.as_posix()) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            _fail("CANDIDATE_SOURCE_CLASS_INVALID:" + relative.as_posix())
        records.append({"path": relative.as_posix(), "byte_count": len(payload), "SHA256": _sha256(payload), "expected_path_class": "REGULAR_NON_SYMLINK", "expected_executable_class": "NON_EXECUTABLE"})
    return records


def _manifest(repo_root: Path, bound: Mapping[str, object], snapshot_bytes: bytes, matrix_bytes: bytes, summary_bytes: bytes) -> dict[str, object]:
    outputs = [
        {"path": (OUTPUT_ROOT_RELATIVE / name).as_posix(), "byte_count": len(payload), "SHA256": _sha256(payload)}
        for name, payload in ((SNAPSHOT, snapshot_bytes), (MATRIX, matrix_bytes), (SUMMARY, summary_bytes))
    ]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION, "stage": SCHEMA_VERSION,
        "artifact_role": "DETERMINISTIC_SOURCE_DERIVED_TP2_INGESTION_MANIFEST",
        "candidate_publication_file_count": 7,
        "candidate_publication_paths": [path.as_posix() for path in CANDIDATE_PUBLICATION_PATHS],
        "output_artifact_count": 4, "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "candidate_source_bindings": _candidate_source_records(repo_root),
        "output_artifact_bindings": outputs, "active_source_binding_count": len(ACTIVE_BINDINGS),
        "active_source_bindings": [_binding_record(value) for value in ACTIVE_BINDINGS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "frozen_formal_validator_provenance_identity_only": True,
        "frozen_formal_validator_parsed": False, "frozen_formal_validator_imported": False,
        "frozen_formal_validator_executed": False, "frozen_formal_validator_subprocessed": False,
        "formal_semantic_canonical_SHA256": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_semantics_independently_validated": True,
        "independent_Exact21_structural_proof": bound["graph_structural_proof"],
        "published_runtime_validation": bound["published_runtime_validation"],
        "generic_Exact11_compatibility": bound["generic_Exact11_compatibility"],
        "current_census_boundary": bound["current_census_boundary"],
        "canonical_task_contract": _task_contract(),
        "determinism": {"canonical_JSON": True, "LF_only": True, "timestamps": False, "hostname": False, "pid": False, "absolute_machine_paths": False},
        "manifest_self_SHA256_recorded": False, "MANIFEST_SELF_SHA256_PROHIBITED": True,
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
        "operation_boundary": {"reconciliation": False, "census_refresh": False, "queue_refresh": False, "training": False, "tensorization": False, "dataset_mutation": False, "commit": False, "push": False},
        "READY_FOR_EXTERNAL_REVIEW": True, "READY_FOR_TRAINING": False,
    }


def _build_raw(repo_root: Path, overrides: Mapping[Path, Path] | None = None) -> dict[str, bytes]:
    bound = load_frozen_formal_decision_v1(repo_root, repository_path_overrides=overrides)
    snapshot_bytes = _json_bytes(_snapshot(bound))
    snapshot = _strict_json(snapshot_bytes, "BUILT_SNAPSHOT")
    matrix_bytes = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot, bound["graph_structural_proof"]))  # type: ignore[arg-type]
    summary_bytes = _json_bytes(_summary())
    manifest_bytes = _json_bytes(_manifest(Path(repo_root).resolve(), bound, snapshot_bytes, matrix_bytes, summary_bytes))
    return {SNAPSHOT: snapshot_bytes, MATRIX: matrix_bytes, SUMMARY: summary_bytes, MANIFEST: manifest_bytes}


def _reject_dynamic_metadata(value: object, path: str = "root") -> None:
    if type(value) is dict:
        for key, child in value.items():
            if key.lower() in {"timestamp", "hostname", "pid", "absolute_path", "self_sha256"} and child is not False:
                _fail("MANIFEST_DYNAMIC_OR_SELF_METADATA:" + path + "." + key)
            _reject_dynamic_metadata(child, path + "." + key)
    elif type(value) is list:
        for index, child in enumerate(value):
            _reject_dynamic_metadata(child, f"{path}[{index}]")
    elif type(value) is str and value.startswith("/"):
        _fail("MANIFEST_ABSOLUTE_PATH_VALUE:" + path)


def validate_completed_decision_projection_v1(
    artifacts: Mapping[str, bytes], repo_root: Path,
    *, repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Fail closed unless an artifact mapping is the exact deterministic projection."""
    if type(artifacts) is not dict or set(artifacts) != set(OUTPUT_FILENAMES) or any(type(value) is not bytes for value in artifacts.values()):
        _fail("OUTPUT_INVENTORY_NOT_EXACT4_BYTES")
    expected = _build_raw(Path(repo_root).resolve(), repository_path_overrides)
    for name in OUTPUT_FILENAMES:
        if artifacts[name] != expected[name]:
            _fail("ARTIFACT_PROJECTION_DRIFT:" + name)
        if not artifacts[name].endswith(b"\n") or b"\r" in artifacts[name] or b"\x00" in artifacts[name]:
            _fail("ARTIFACT_TEXT_HYGIENE_INVALID:" + name)
    snapshot = _strict_json(artifacts[SNAPSHOT], "SNAPSHOT")
    rows = _parse_csv(artifacts[MATRIX], "MATRIX")
    summary = _strict_json(artifacts[SUMMARY], "SUMMARY")
    manifest = _strict_json(artifacts[MANIFEST], "MANIFEST")
    if len(rows) != 4 or not rows or tuple(rows[0]) != MATRIX_HEADER:
        _fail("MATRIX_EXACT4_OR_HEADER_DRIFT")
    if snapshot["canonical_task_contract"]["B3_present"] is not True or snapshot["canonical_task_contract"]["sixth_task"] is not False:
        _fail("EXACT5_CONTRACT_DRIFT")
    if summary.get("completed_lane") != EXPECTED_COMPLETED_LANE or summary.get("READY_FOR_TRAINING") is not False:
        _fail("SUMMARY_BOUNDARY_DRIFT")
    if manifest.get("READY_FOR_EXTERNAL_REVIEW") is not True or manifest.get("manifest_self_SHA256_recorded") is not False:
        _fail("MANIFEST_BOUNDARY_DRIFT")
    _reject_dynamic_metadata(manifest)
    return {
        "status": "PASS", "event_count": 4, "matrix_column_count": len(MATRIX_HEADER),
        "output_artifact_count": 4, "active_source_binding_count": len(ACTIVE_BINDINGS),
        "generic_Exact11_accepted_count": 4, "READY_FOR_EXTERNAL_REVIEW": True,
        "READY_FOR_TRAINING": False,
    }


def build_artifacts_v1(repo_root: Path, *, repository_path_overrides: Mapping[Path, Path] | None = None) -> dict[str, bytes]:
    artifacts = _build_raw(Path(repo_root).resolve(), repository_path_overrides)
    validate_completed_decision_projection_v1(artifacts, repo_root, repository_path_overrides=repository_path_overrides)
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
    descriptor, temporary = tempfile.mkstemp(prefix=".covapie_tp2_", dir=path.parent)
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
    if not target.is_dir() or target.is_symlink() or {path.name for path in target.iterdir()} != set(OUTPUT_FILENAMES):
        _fail("MATERIALIZED_OUTPUT_INVENTORY_NOT_EXACT4")
    live: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = target / name
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            _fail("MATERIALIZED_OUTPUT_CLASS_INVALID:" + name)
        live[name] = path.read_bytes()
    result = validate_completed_decision_projection_v1(live, root)
    fresh = build_artifacts_v1(root)
    return {**result, "materialized_bytes_equal_fresh_build": live == fresh, "deterministic_double_build": fresh == build_artifacts_v1(root)}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    print(json.dumps(materialize_artifacts_v1(repo_root), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
