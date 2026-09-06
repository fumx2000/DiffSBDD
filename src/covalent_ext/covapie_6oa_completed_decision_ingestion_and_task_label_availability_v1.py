"""Project frozen 6OA Exact4 human authority into metadata-only artifacts.

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
    "SixOAIngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = "covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_6oa_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_6oa_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_6oa_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_6oa_completed_decision_ingestion_manifest_v1"
BASELINE_COMMIT = "7694815387e786f954ac677042250a361e806adc"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_6oa_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_6oa_event_task_label_availability_v1.csv"
SUMMARY = "covapie_6oa_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_6oa_completed_decision_ingestion_manifest_v1.json"
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
    "6OA_COVAPIE_BULK_REVIEW_UNIT_E800FEC791DFDA72"
)
FORMAL_DECISION_RELATIVE = (
    STATE_ROOT / "formal-human-decision-v1/6oa_formal_human_decision_v1.json"
)
FORMAL_VALIDATOR_RELATIVE = (
    STATE_ROOT
    / "formal-human-decision-v1/validate_6oa_formal_human_decision_v1.py"
)
EVENT_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/6oa_exact4_event_evidence_v1.csv"
)
GRAPH_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/6oa_graph_and_review_evidence_v1.json"
)
CCD_RELATIVE = Path(
    "covapie-state/bulk-model-usable-auto-admission-scaleup-v1/"
    "ranks-0501-1000/attempt-001/cache/rcsb/ccd/6OA.cif"
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
    "covapie_cumulative1000_current_global_readiness_census_with_nwj_v1.py"
)
CENSUS_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_nwj_v1"
)
CENSUS_MATRIX_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_census_with_nwj_v1.csv"
)
CENSUS_SUMMARY_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_summary_with_nwj_v1.json"
)
CENSUS_MANIFEST_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_manifest_with_nwj_v1.json"
)

FORMAL_DECISION_SCHEMA = "covapie_6oa_exact4_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_E800FEC791DFDA72"
EXPECTED_SCOPE = "CURRENT_6OA_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
EXPECTED_COMPLETED_LANE = "COMPLETED_TASK_DOMAIN_NEGATIVE"
EXPECTED_LEGACY_STATUS = "COMPLETED_HUMAN_NEGATIVE"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
SELECTED_CANDIDATE = "CANDIDATE_A_DIRECT_POST_REACTION_CENTER"
SOURCE_D2 = "OUT_OF_DOMAIN"
NORMALIZED_TASK_RELEVANCE = "NOT_RELEVANT"
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_NOT_AVAILABLE"
PRE_STATUS = "PRE_REACTION_UNRESOLVED"

# Event ID, rank, protein asym, ligand asym, connection, exact POST, reported POST.
EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:4OU2:A:CYS:302-:SG:G:6OA:C5",
        855,
        "A",
        "G",
        "covale1",
        "1.853206",
        "1.853",
        False,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4OU2:B:CYS:302-:SG:J:6OA:C5",
        856,
        "B",
        "J",
        "covale2",
        "1.674652",
        "1.675",
        False,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4OU2:C:CYS:302-:SG:M:6OA:C5",
        857,
        "C",
        "M",
        "covale3",
        "1.347977",
        "1.348",
        True,
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4OU2:D:CYS:302-:SG:P:6OA:C5",
        858,
        "D",
        "P",
        "covale4",
        "1.677347",
        "1.677",
        False,
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)

WARHEAD_ATOMS = ("C5", "O3")
LINKER_ATOMS: tuple[str, ...] = ()
SCAFFOLD_ATOMS = ("C", "C1", "C2", "C3", "C4", "O", "O1", "O2")
HEAVY_ATOMS = (*SCAFFOLD_ATOMS, *WARHEAD_ATOMS)
HEAVY_BONDS = (
    ("C", "C1", "SING"),
    ("C", "O", "SING"),
    ("C", "O1", "DOUB"),
    ("C1", "C2", "DOUB"),
    ("C1", "O2", "SING"),
    ("C2", "C3", "SING"),
    ("C3", "C4", "DOUB"),
    ("C4", "C5", "SING"),
    ("C5", "O3", "SING"),
)
MINIMAL_SEED = ("C3", "C4")
PRIMARY_ANCHOR = "C4"
BOUNDARY = {
    "scaffold_atom_id": "C4",
    "warhead_atom_id": "C5",
    "bond_order": "SING",
}

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
    "training_disposition": "NOT_APPLICABLE",
    "human_training_excluded": False,
}

# path, namespace, bytes, SHA256, executable, role, validation method
_Binding = tuple[Path, str, int, str, bool, str, str]
FORMAL_BINDINGS: tuple[_Binding, ...] = (
    (
        FORMAL_DECISION_RELATIVE,
        "project_parent_relative",
        33043,
        "c79a0f03b0bb9847c190befd351c4c323e1243b10e30655c3b4f61c2f9034218",
        False,
        "6OA_FROZEN_FORMAL_HUMAN_DECISION",
        "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE,
        "project_parent_relative",
        96246,
        "77800ac2056df2b0770967be15bb89c67d2be089d6c54180361f4922ee73731e",
        False,
        "6OA_FROZEN_FORMAL_VALIDATOR",
        "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED",
    ),
)
SUPPORTING_BINDINGS: tuple[_Binding, ...] = (
    (
        EVENT_EVIDENCE_RELATIVE,
        "project_parent_relative",
        12443,
        "322434764911133ea51815e7ce45531423c84106bb618f5cbac033043bb8f31e",
        False,
        "6OA_EXACT4_EVENT_EVIDENCE",
        "PARSED_CSV_SUPPORTING_EVIDENCE_WITH_FROZEN_4OU2_IDENTITY",
    ),
    (
        GRAPH_EVIDENCE_RELATIVE,
        "project_parent_relative",
        31059,
        "370569f68a3ff935695bffb5959413fff8382773780965fddd79d88ab5e53e6a",
        False,
        "6OA_GRAPH_AND_REVIEW_EVIDENCE",
        "PARSED_JSON_EXACT10_GRAPH_AND_PRE_BOUNDARY_PROOF",
    ),
    (
        CCD_RELATIVE,
        "project_parent_relative",
        6723,
        "2a5bcd59744ad76e127c09c308380e2fbe882c237b8f20f3f29f0adbfd006cf6",
        False,
        "6OA_FROZEN_CCD",
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
        75148,
        "aca86bfacf0811d3aca70a2c2d21e7ca8c1b2cb0382d847a03372339eec899a7",
        False,
        "CURRENT_WITH_NWJ_CENSUS_OWNER",
        "CONTENT_IDENTITY_READ_ONLY",
    ),
    (
        CENSUS_MATRIX_RELATIVE,
        "repository_relative",
        553770,
        "5e527a258f8589677c71c5271f3d305540ace8d87e8b647282f02856fd356a9e",
        False,
        "CURRENT_WITH_NWJ_CENSUS_MATRIX",
        "PARSED_CSV_PREINGESTION_STATE_READ_ONLY",
    ),
    (
        CENSUS_SUMMARY_RELATIVE,
        "repository_relative",
        21523,
        "a9dfa8d763c1a8c746f9ff9ec16d684a5dccfa581afd078090f2ab17a82c6bf4",
        False,
        "CURRENT_WITH_NWJ_CENSUS_SUMMARY",
        "PARSED_JSON_PENDING_RANK_READ_ONLY",
    ),
    (
        CENSUS_MANIFEST_RELATIVE,
        "repository_relative",
        81923,
        "504134d0e0a92b8ffe4147992b1c0869c5e2289eb9161d6b2bdf079f0a19911f",
        False,
        "CURRENT_WITH_NWJ_CENSUS_MANIFEST",
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


class SixOAIngestionSafetyError(ValueError):
    """Raised when the frozen 6OA projection contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise SixOAIngestionSafetyError("COVAPIE_6OA_INGESTION_V1_ERROR:" + reason)


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
        raise SixOAIngestionSafetyError(
            "COVAPIE_6OA_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label
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
        raise SixOAIngestionSafetyError(
            "COVAPIE_6OA_INGESTION_V1_ERROR:JSON_PARSE_FAILED:" + label
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
        raise SixOAIngestionSafetyError(
            "COVAPIE_6OA_INGESTION_V1_ERROR:CSV_UTF8_INVALID:" + label
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
        raise SixOAIngestionSafetyError(
            "COVAPIE_6OA_INGESTION_V1_ERROR:SOURCE_BINDING_FAILED:"
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
        raise SixOAIngestionSafetyError(
            "COVAPIE_6OA_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
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
                    raise SixOAIngestionSafetyError(
                        "COVAPIE_6OA_INGESTION_V1_ERROR:"
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


def _validate_formal(formal: Mapping[str, Any]) -> None:
    """Independently validate all critical 6OA formal semantics."""
    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(formal.get("record_role"), FORMAL_RECORD_ROLE, "FORMAL_RECORD_ROLE_DRIFT")
    _expect_fields(
        formal.get("formal_state"),
        {
            "approved": True,
            "unsigned": False,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "human_review_completed": True,
            "formal_decision_created": True,
            "formal_sample_level_authority_created": True,
            "machine_generated_human_authorization": False,
            "machine_is_human_reviewer_or_attestor": False,
        },
        "FORMAL_STATE_DRIFT",
    )
    authorization = _expect_fields(
        formal.get("human_authorization"),
        {
            "approval_time": None,
            "approval_time_status": "NOT_PROVIDED_VERIFIABLY",
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "machine_generated_human_authorization": False,
            "platform_identity_verification_claimed": False,
        },
        "FORMAL_AUTHORIZATION_DRIFT",
    )
    _expect_fields(
        authorization.get("candidate_binding"),
        {
            "SHA256": "8eff75e7e23bc68013ac1549524c77b9d2731e376cc6b0ba0157e733d864d1c9",
            "binding_transfers_to_other_candidate_versions": False,
        },
        "FORMAL_CANDIDATE_BINDING_DRIFT",
    )
    _expect_fields(
        authorization.get("authorization_scope"),
        {
            "PDB": "4OU2",
            "ligand_component_id": "6OA",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scaleup_event_ranks": list(EXPECTED_RANKS),
            "sample_level_exact4_formalization_authorized": True,
            "task_label_or_tensor_materialization_authorized": False,
            "training_preparation_or_training_authorized": False,
            "cross_sample_rule_authorized": False,
            "ligand_wide_rule_authorized": False,
            "reusable_warhead_or_reaction_family_authorized": False,
        },
        "FORMAL_AUTHORIZATION_SCOPE_DRIFT",
    )
    _expect_fields(
        formal.get("sample_identity"),
        {
            "PDB": "4OU2",
            "ligand_component_id": "6OA",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scope": EXPECTED_SCOPE,
            "event_count": 4,
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "scaleup_event_ranks": list(EXPECTED_RANKS),
            "raw_priority_rank": 29,
            "current_pending_rank": 1,
            "ligand_wide_authority": False,
            "cross_sample_authority": False,
            "cross_structure_authority": False,
        },
        "FORMAL_SAMPLE_IDENTITY_DRIFT",
    )
    _expect_fields(
        formal.get("external_human_decision_input"),
        {
            "AUTHORIZATION_ORIGIN": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "D1_observed_covalent_chemistry": "POSITIVE",
            "D2_task_generation_domain_relevance": SOURCE_D2,
            "D3_reactive_atom_pair_confirmation_or_revision": "CONFIRM_OBSERVED_PAIR",
            "D3_protein_reactive_atom": "SG",
            "D3_ligand_reactive_atom": "C5",
            "D3_observed_pair": "SG:C5",
            "D4_role_partition_and_minimal_seed": "PROVIDE_ROLE_PARTITION",
            "D4_selected_candidate": SELECTED_CANDIDATE,
            "D4_role_profile": EXPECTED_ROLE_PROFILE,
            "D4_warhead_atoms": list(WARHEAD_ATOMS),
            "D4_linker_atoms": [],
            "D4_scaffold_atoms": list(SCAFFOLD_ATOMS),
            "D4_boundary": "C4--C5/SING",
            "D4_minimal_seed": list(MINIMAL_SEED),
            "D4_primary_anchor": PRIMARY_ANCHOR,
            "D5_structural_task_applicability": "PROVIDE_APPLICABLE_TASK_IDS",
            "D5_applicable_task_ids": list(DIRECT_APPLICABLE_TASK_IDS),
            "D6_later_training_use_disposition": "NOT_APPLICABLE",
            "scope": EXPECTED_SCOPE,
        },
        "FORMAL_EXTERNAL_INPUT_DRIFT",
    )
    decisions = formal.get("formal_decisions")
    if type(decisions) is not dict:
        _fail("FORMAL_DECISIONS_MISSING")
    _expect_fields(
        decisions.get("D1_observed_covalent_chemistry"),
        {
            "decision": "POSITIVE",
            "chemistry_human_authoritative_for_current_sample": True,
            "chemistry_negative": False,
            "observed_pair": "SG:C5",
            "scope": EXPECTED_SCOPE,
        },
        "FORMAL_D1_DRIFT",
    )
    _expect_fields(
        decisions.get("D2_task_generation_domain_relevance"),
        {
            "decision": SOURCE_D2,
            "chemistry_positive_preserved": True,
            "task_relevance_human_authoritative_for_current_sample": True,
            "scope": EXPECTED_SCOPE,
        },
        "FORMAL_D2_DRIFT",
    )
    _expect_fields(
        decisions.get("D3_reactive_atom_pair_confirmation_or_revision"),
        {
            "decision": "CONFIRM_OBSERVED_PAIR",
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "C5",
            "observed_pair": "SG:C5",
            "reactive_pair_sample_authoritative": True,
            "reusable_pair_authority": False,
            "ligand_wide_authority": False,
            "cross_structure_generalization": False,
            "scope": EXPECTED_SCOPE,
        },
        "FORMAL_D3_DRIFT",
    )
    _expect_fields(
        decisions.get("D4_role_partition_and_minimal_seed"),
        {
            "decision": "PROVIDE_ROLE_PARTITION",
            "selected_candidate": SELECTED_CANDIDATE,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "role_partition_sample_authoritative": True,
            "minimal_seed_sample_authoritative": True,
            "PRE_precursor_role_authority": False,
            "reusable_role_authority": False,
        },
        "FORMAL_D4_DRIFT",
    )
    _expect_fields(
        decisions.get("D5_structural_task_applicability"),
        {
            "decision": "PROVIDE_APPLICABLE_TASK_IDS",
            "applicable_task_ids": list(DIRECT_APPLICABLE_TASK_IDS),
            "task_applicability_sample_authoritative": True,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
        },
        "FORMAL_D5_DRIFT",
    )
    _expect_fields(
        decisions.get("D6_later_training_use_disposition"),
        {
            "decision": "NOT_APPLICABLE",
            "consistent_with_D2": SOURCE_D2,
            "chemistry_negative": False,
            "formal_training_decision": False,
            "formal_training_admitted": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "FORMAL_D6_DRIFT",
    )
    selected = _expect_fields(
        formal.get("selected_role_context"),
        {
            "candidate_id": SELECTED_CANDIDATE,
            "formal_selected": True,
            "human_selected": True,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "warhead_atom_ids": list(WARHEAD_ATOMS),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(SCAFFOLD_ATOMS),
            "counts": {"warhead": 2, "linker": 0, "scaffold": 8, "total": 10},
            "boundary": "C4--C5/SING",
            "task_ids": list(DIRECT_APPLICABLE_TASK_IDS),
            "role_partition_sample_authoritative": True,
            "role_profile_sample_authoritative": True,
            "PRE_precursor_authority": False,
            "reusable_warhead_rule_authority": False,
        },
        "FORMAL_SELECTED_ROLE_DRIFT",
    )
    _expect_fields(
        selected.get("minimal_seed"),
        {
            "atom_ids": list(MINIMAL_SEED),
            "primary_scaffold_side_anchor": PRIMARY_ANCHOR,
            "minimal_seed_sample_authoritative": True,
            "reusable_minimal_seed_authority": False,
        },
        "FORMAL_SELECTED_SEED_DRIFT",
    )
    _expect_fields(
        selected.get("published_runtime"),
        {
            "role_profile": EXPECTED_ROLE_PROFILE,
            "role_runtime_valid": True,
            "role_runtime_reasons": [],
            "minimal_seed_runtime_valid": True,
            "minimal_seed_runtime_reasons": [],
            "derived_task_ids": list(DIRECT_APPLICABLE_TASK_IDS),
            "derived_primary_anchor": PRIMARY_ANCHOR,
            "direct_boundary": {**BOUNDARY, "boundary_valid": True},
            "task_runtime_valid": True,
        },
        "FORMAL_SELECTED_RUNTIME_DRIFT",
    )
    exact5 = _expect_fields(
        formal.get("canonical_Exact5"),
        {
            "task_count": 5,
            "B3_present": True,
            "sixth_task": False,
            "selected_structural_applicability_task_ids": list(
                DIRECT_APPLICABLE_TASK_IDS
            ),
            "task_applicability_determined": True,
            "task_applicability_sample_authoritative": True,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
            "training_mask_targets_available_now": False,
        },
        "FORMAL_EXACT5_DRIFT",
    )
    _expect(exact5.get("tasks"), _formal_task_rows(), "FORMAL_EXACT5_TASK_ROWS_DRIFT")
    _expect_fields(
        formal.get("training_boundary"),
        {
            "out_of_domain": True,
            "chemistry_negative": False,
            "human_training_use_disposition": "NOT_APPLICABLE",
            "future_training_admission_candidate": False,
            "formal_training_admitted": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
            "parameter_update_authorization": False,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "FORMAL_TRAINING_BOUNDARY_DRIFT",
    )
    _expect_fields(
        formal.get("PRE_boundary"),
        {
            "supporting_adduct_source_graph_count_per_event": 0,
            "candidate_PRE_free_source_graph_count_per_event": 0,
            "source_mapping_count_per_event": 0,
            "PRE_source_mapping_status": PRE_MAPPING_STATUS,
            "final_PRE_reaction_status": PRE_STATUS,
            "PRE_authority": False,
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
            "PRE_coordinates_invented": False,
            "PRE_topology_invented": False,
            "leaving_group_invented": False,
            "reagent_invented": False,
            "reaction_edit_invented": False,
            "C5_O3_free_precursor_double_bond_authority": False,
            "2VS_substituted_for_6OA_PRE": False,
        },
        "FORMAL_PRE_BOUNDARY_DRIFT",
    )
    geometry = _expect_fields(
        formal.get("geometry_boundary"),
        {
            "representation": "OBSERVED_POST",
            "distances_modified_or_averaged": False,
            "new_bond_order_inferred": False,
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
            "pair_identity_approval_is_exact_geometry_training_target_approval": False,
        },
        "FORMAL_GEOMETRY_BOUNDARY_DRIFT",
    )
    expected_geometry = [
        {
            "canonical_event_id": event_id,
            "scaleup_event_rank": rank,
            "exact_POST_distance_angstrom": float(exact),
            "geometry_outlier": outlier,
            "distance_retained_not_averaged_or_normalized": True,
            "new_bond_order_inferred": False,
        }
        for event_id, rank, _protein, _ligand, _connection, exact, _reported, outlier
        in EXPECTED_EVENTS
    ]
    _expect(geometry.get("events"), expected_geometry, "FORMAL_GEOMETRY_EVENTS_DRIFT")
    _expect_fields(
        geometry.get("rank857_caveat"),
        {
            "scaleup_event_rank": 857,
            "protein_chain": "C",
            "exact_POST_distance_angstrom": 1.347977,
            "geometry_outlier": True,
            "distance_normalized": False,
            "distance_retained": True,
            "event_removed": False,
            "new_bond_order_inferred": False,
        },
        "FORMAL_RANK857_CAVEAT_DRIFT",
    )
    formal_events = formal.get("event_level_projection")
    if type(formal_events) is not list or len(formal_events) != 4:
        _fail("FORMAL_EVENT_PROJECTION_NOT_EXACT4")
    for event, expected in zip(formal_events, EXPECTED_EVENTS, strict=True):
        event_id, rank, _protein, _ligand, _connection, exact, _reported, outlier = expected
        _expect_fields(
            event,
            {
                "canonical_event_id": event_id,
                "scaleup_event_rank": rank,
                "D1_observed_covalent_chemistry": "POSITIVE",
                "D2_task_generation_domain_relevance": SOURCE_D2,
                "D3_reactive_atom_pair_confirmation_or_revision": "CONFIRM_OBSERVED_PAIR",
                "D4_role_partition_and_minimal_seed": "PROVIDE_ROLE_PARTITION",
                "D5_structural_task_applicability": "PROVIDE_APPLICABLE_TASK_IDS",
                "D6_later_training_use_disposition": "NOT_APPLICABLE",
                "observed_pair": "SG:C5",
                "protein_reactive_atom": "SG",
                "ligand_reactive_atom": "C5",
                "selected_role_candidate": SELECTED_CANDIDATE,
                "applicable_task_ids": list(DIRECT_APPLICABLE_TASK_IDS),
                "exact_POST_distance_angstrom": float(exact),
                "geometry_outlier": outlier,
                "new_bond_order_inferred": False,
                "task_label_row_materialized": False,
                "exact_geometry_training_target_created": False,
            },
            "FORMAL_EVENT_PROJECTION_DRIFT:" + str(rank),
        )
    _expect_fields(
        formal.get("same_enzyme_2VS_precedent_boundary"),
        {
            "2VS_authority_applies_to_6OA": False,
            "2VS_substituted_for_6OA_PRE": False,
            "2VS_values_copied_to_6OA": False,
            "cross_sample_authority_created": False,
        },
        "FORMAL_2VS_BOUNDARY_DRIFT",
    )
    for section_name in ("reusable_authority_map", "readiness"):
        section = formal.get(section_name)
        if type(section) is not dict:
            _fail("FORMAL_BOUNDARY_SECTION_MISSING:" + section_name)
    _expect_fields(
        formal["reusable_authority_map"],
        {
            "reusable_chemistry_authority": False,
            "reusable_pair_authority": False,
            "reusable_role_authority": False,
            "reusable_minimal_seed_authority": False,
            "reaction_family_authority": False,
            "warhead_rule_authority": False,
            "warhead_type_authority": False,
            "PRE_authority": False,
            "POST_geometry_training_authority": False,
        },
        "FORMAL_REUSABLE_AUTHORITY_DRIFT",
    )
    _expect_fields(
        formal["readiness"],
        {
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
        },
        "FORMAL_READINESS_DRIFT",
    )


def _validate_event_evidence(payload: bytes) -> list[dict[str, object]]:
    rows = _parse_csv(payload, "6OA_EVENT_EVIDENCE")
    if len(rows) != 4:
        _fail("EVENT_EVIDENCE_NOT_EXACT4")
    projected: list[dict[str, object]] = []
    frozen_structure = {
        "SHA256": "f3de681dabd3fde72156fe03b0cf92afec9242f6fefa6c24ad76232eae1a992a",
        "bytes": 406996,
        "relative_path": (
            "covapie-state/bulk-model-usable-auto-admission-scaleup-v1/"
            "ranks-0501-1000/attempt-001/cache/rcsb/structures/4OU2.cif.gz"
        ),
    }
    for index, (row, expected) in enumerate(zip(rows, EXPECTED_EVENTS, strict=True)):
        event_id, rank, protein, ligand, connection, exact, reported, outlier = expected
        required = {
            "artifact_role": "UNSIGNED_NONAUTHORITATIVE_MACHINE_REVIEW_AID_PREPARATION",
            "event_index_0based": str(index),
            "canonical_event_id": event_id,
            "scaleup_event_rank": str(rank),
            "raw_review_unit_priority_rank": "29",
            "current_pending_rank": "1",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "pdb_id": "4OU2",
            "model_number": "1",
            "protein_label_asym_id": protein,
            "protein_auth_chain": protein,
            "protein_label_comp_id": "CYS",
            "protein_auth_seq_id": "302",
            "protein_reactive_atom": "SG",
            "ligand_component_id": "6OA",
            "ligand_label_asym_id": ligand,
            "ligand_auth_chain": protein,
            "ligand_reactive_atom": "C5",
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
            "structural_processing_status": "PASSED",
            "POST_source_evidence_available": "true",
            "reactive_pair_raw_structural_evidence": "true",
            "source_observed_pair_is_human_authority": "false",
            "approved_warhead_atom": "false",
            "supporting_adduct_graph_count": "0",
            "candidate_PRE_free_source_graph_count": "0",
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
        except (KeyError, json.JSONDecodeError) as error:
            raise SixOAIngestionSafetyError(
                "COVAPIE_6OA_INGESTION_V1_ERROR:EVENT_SOURCE_BINDING_INVALID"
            ) from error
        for key, expected_value in frozen_structure.items():
            if structure_binding.get(key) != expected_value:
                _fail("FROZEN_4OU2_IDENTITY_DRIFT:" + key)
        if (
            ccd_binding.get("SHA256") != SUPPORTING_BINDINGS[2][3]
            or ccd_binding.get("bytes") != SUPPORTING_BINDINGS[2][2]
        ):
            _fail("EVENT_CCD_IDENTITY_DRIFT")
        projected.append(
            {
                "canonical_event_id": event_id,
                "scaleup_rank": rank,
                "protein_chain_or_asym": protein,
                "ligand_chain_or_asym": ligand,
                "selected_connection_id": connection,
                "POST_distance_frozen_lexeme": exact,
                "reported_POST_distance_frozen_lexeme": reported,
                "geometry_outlier": outlier,
            }
        )
    return projected


def _validate_graph_evidence(payload: bytes) -> dict[str, object]:
    document = _strict_json(payload, "6OA_GRAPH_EVIDENCE")
    graph = _expect_fields(
        document.get("CCD_complete_heavy_atom_graph"),
        {
            "component_id": "6OA",
            "heavy_atom_count": 10,
            "heavy_heavy_bond_count": 9,
            "connected": True,
            "connected_component_count": 1,
            "canonical_heavy_graph_SHA256": (
                "81e0b749761668712d6061824c004262eef0c733375542a4487b3496f149c5b0"
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
    if len(atom_ids) != 10 or set(atom_ids) != set(HEAVY_ATOMS):
        _fail("GRAPH_EXACT10_ATOMS_DRIFT")
    if len(bond_rows) != 9 or set(bond_rows) != set(HEAVY_BONDS):
        _fail("GRAPH_EXACT9_BONDS_DRIFT")
    local = _expect_fields(
        graph.get("C5_local_topology"),
        {
            "source_observed_reactive_endpoint": "C5",
            "source_observed_endpoint_exists_in_complete_graph": True,
            "one_hop_heavy_atom_shell": ["C4", "O3"],
            "exact_two_hop_heavy_atom_shell": ["C3"],
            "approved_warhead_atom": False,
            "approved_reaction_family": None,
            "approved_role_partition": None,
            "approved_warhead_type": None,
        },
        "GRAPH_C5_LOCAL_TOPOLOGY_DRIFT",
    )
    del local
    pre = _expect_fields(
        document.get("PRE_evidence"),
        {
            "availability": "NO_SUPPORTING_ADDUCT_OR_CANDIDATE_PRE_SOURCE_GRAPH",
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
        },
        "GRAPH_PRE_BOUNDARY_DRIFT",
    )
    audit = pre.get("event_audit")
    if type(audit) is not list or len(audit) != 4:
        _fail("GRAPH_PRE_AUDIT_NOT_EXACT4")
    for row, event_id in zip(audit, EXPECTED_EVENT_IDS, strict=True):
        _expect_fields(
            row,
            {
                "canonical_event_id": event_id,
                "supporting_adduct_graph_count": 0,
                "candidate_PRE_free_source_graph_count": 0,
                "source_PRE_mapping_count": 0,
                "source_mapping_status": PRE_MAPPING_STATUS,
                "final_PRE_reaction_status": PRE_STATUS,
            },
            "GRAPH_PRE_EVENT_DRIFT",
        )
    return {"atom_ids": atom_ids, "bonds": bond_rows}


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
    role = runtime.validate_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE,
        retained_heavy_atoms=graph["atom_ids"],
        scaffold_atoms=SCAFFOLD_ATOMS,
        linker_atoms=LINKER_ATOMS,
        warhead_atoms=WARHEAD_ATOMS,
        reactive_atom_id="C5",
        direct_scaffold_warhead_boundaries=(("C4", "C5", "SING"),),
        explicit_graph_bonds=graph["bonds"],
    )
    boundary = role.direct_scaffold_warhead_boundary
    if not (
        role.valid is True
        and tuple(role.reasons) == ()
        and role.scaffold_count == 8
        and role.linker_count == 0
        and role.warhead_count == 2
        and boundary is not None
        and boundary.boundary_valid is True
        and boundary.scaffold_atom_id == "C4"
        and boundary.warhead_atom_id == "C5"
        and boundary.bond_order == "SING"
    ):
        _fail("PUBLISHED_DIRECT_ROLE_RUNTIME_FAILED")
    seed = runtime.validate_minimal_seed_for_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE,
        seed_atoms=MINIMAL_SEED,
        scaffold_atoms=SCAFFOLD_ATOMS,
        linker_atoms=LINKER_ATOMS,
        warhead_atoms=WARHEAD_ATOMS,
        explicit_graph_bonds=graph["bonds"],
        direct_boundary=boundary,
    )
    if not (
        seed.valid is True
        and tuple(seed.reasons) == ()
        and seed.primary_anchor_atom_id == PRIMARY_ANCHOR
    ):
        _fail("PUBLISHED_DIRECT_SEED_RUNTIME_FAILED")
    task_ids = tuple(
        runtime.valid_canonical_task_ids_for_role_profile_v1(EXPECTED_ROLE_PROFILE)
    )
    if task_ids != DIRECT_APPLICABLE_TASK_IDS:
        _fail("PUBLISHED_DIRECT_TASK_RUNTIME_FAILED")
    return {
        "valid": True,
        "reasons": [],
        "profile": EXPECTED_ROLE_PROFILE,
        "counts": {"W": 2, "L": 0, "S": 8},
        "boundary": BOUNDARY,
        "minimal_seed_atom_ids": list(MINIMAL_SEED),
        "primary_anchor_atom_id": PRIMARY_ANCHOR,
        "applicable_task_ids": list(task_ids),
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
        fact_objects.append(fact)
        row = {field.name: getattr(fact, field.name) for field in fields(fact)}
        if set(row) != set(GENERIC_FACT_FIELDS):
            _fail("GENERIC_RICH_FIELD_FIREWALL_FAILED")
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
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "source_formal_generation_domain_decision": SOURCE_D2,
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "facts": projected,
        "rich_fields_leaked": False,
        "NormalizedDecisionSource_constructed": True,
        "reconciliation_performed": False,
    }


def _current_census(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    rows = _parse_csv(payloads[CENSUS_MATRIX_RELATIVE], "CURRENT_WITH_NWJ_CENSUS")
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
        _fail("CURRENT_CENSUS_6OA_EXACT4_DRIFT")
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
                _fail("CURRENT_CENSUS_6OA_PRIOR_STATE_DRIFT:" + key)
    summary = _strict_json(payloads[CENSUS_SUMMARY_RELATIVE], "CURRENT_WITH_NWJ_SUMMARY")
    manifest = _strict_json(payloads[CENSUS_MANIFEST_RELATIVE], "CURRENT_WITH_NWJ_MANIFEST")
    _expect(
        summary.get("schema_version"),
        "covapie_cumulative1000_current_global_readiness_census_with_nwj_v1",
        "CURRENT_CENSUS_SUMMARY_SCHEMA_DRIFT",
    )
    _expect(
        manifest.get("schema_version"),
        "covapie_cumulative1000_current_global_readiness_census_with_nwj_v1",
        "CURRENT_CENSUS_MANIFEST_SCHEMA_DRIFT",
    )
    authority = _expect_fields(
        summary.get("authority_boundary"),
        {
            "next_priority_review_current_pending_rank": 1,
            "next_priority_review_event_count": 4,
            "next_priority_review_ligand": "6OA",
            "next_priority_review_raw_priority_rank": 29,
            "next_priority_review_unit": EXPECTED_REVIEW_UNIT_ID,
            "NEXT_REVIEW_STARTED": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "CURRENT_CENSUS_NEXT_PRIORITY_DRIFT",
    )
    del authority
    pending = summary.get("top_pending_review_units_by_event_yield")
    if type(pending) is not list or not pending:
        _fail("CURRENT_CENSUS_PENDING_LIST_MISSING")
    _expect_fields(
        pending[0],
        {
            "rank": 1,
            "raw_priority_rank": 29,
            "event_count": 4,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "current_review_status": "CURRENTLY_UNREVIEWED",
            "ligand_component_ids": ["6OA"],
            "pdb_ids": ["4OU2"],
        },
        "CURRENT_CENSUS_PENDING_RANK1_DRIFT",
    )
    return {
        "row_count": 1000,
        "6OA_event_count": 4,
        "6OA_current_global_status": "CURRENTLY_UNREVIEWED",
        "6OA_current_review_status": "CURRENTLY_UNREVIEWED",
        "6OA_human_review_completed": False,
        "6OA_chemistry": "UNRESOLVED",
        "6OA_task_relevance": "UNRESOLVED",
        "6OA_training_use": "UNRESOLVED",
        "current_pending_rank": 1,
        "raw_priority_rank": 29,
        "next_priority_review_ligand": "6OA",
        "census_modified_by_ingestion": False,
    }


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Bind sources and independently validate frozen 6OA authority."""
    root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    payloads = _verify_bindings(root, overrides)
    formal = _strict_json(payloads[FORMAL_DECISION_RELATIVE], "6OA_FORMAL_DECISION")
    _validate_formal(formal)
    events = _validate_event_evidence(payloads[EVENT_EVIDENCE_RELATIVE])
    graph = _validate_graph_evidence(payloads[GRAPH_EVIDENCE_RELATIVE])
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
            "Exact10_count": 10,
            "Exact9_bond_count": 9,
            "partition_pairwise_disjoint": True,
            "partition_exhaustive": True,
            "W_connected": True,
            "L_connected_or_empty": True,
            "S_connected": True,
            "reactive_C5_in_W": True,
            "cross_role_boundary_count": 1,
            "cross_role_boundary": BOUNDARY,
        },
        "published_DIRECT_runtime_validation": runtime,
        "generic_Exact11_compatibility": generic,
        "current_census_boundary": census,
    }


def _normalization_contract() -> dict[str, object]:
    return {
        "source_field": "D2_task_generation_domain_relevance",
        "source_formal_generation_domain_decision": SOURCE_D2,
        "target_field": "task_relevance_disposition",
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "mapping": "OUT_OF_DOMAIN_TO_NOT_RELEVANT",
        "direction": "FORMAL_SOURCE_TO_GENERIC_RECONCILIATION_VOCABULARY",
        "source_value_preserved": True,
        "chemistry_disposition_changed_by_normalization": False,
        "training_exclusion_created_by_normalization": False,
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
        "formal_event_training_use_decision": "NOT_APPLICABLE",
        "training_use_allowed": False,
        "human_training_excluded": False,
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
        "supporting_adduct_source_graph_count_per_event": 0,
        "candidate_PRE_free_source_graph_count_per_event": 0,
        "mapping_count_per_event": 0,
        "PRE_source_mapping_status": PRE_MAPPING_STATUS,
        "final_PRE_reaction_status": PRE_STATUS,
        "PRE_authority": False,
        "POST_to_PRE_copy": False,
        "PRE_zero_fill": False,
        "PRE_coordinates_created": False,
        "PRE_topology_created": False,
        "C5_O3_free_precursor_double_bond_authority": False,
        "leaving_group_inferred": False,
        "reagent_inferred": False,
        "reaction_edit_inferred": False,
        "2VS_substituted_for_sample_specific_PRE": False,
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
        "observed_distances_angstrom": [float(row[5]) for row in EXPECTED_EVENTS],
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
        "pdb_id": "4OU2",
        "ligand_component_id": "6OA",
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "human_review_completed": True,
        "source_formal_generation_domain_decision": SOURCE_D2,
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "chemistry_disposition": "POSITIVE",
        "negative_chemistry": False,
        "task_domain_negative": True,
        "positive_generative_supervision_eligible": False,
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C5",
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
        "supporting_adduct_source_graph_count": 0,
        "candidate_PRE_free_source_graph_count": 0,
        "mapping_count": 0,
        "PRE_source_mapping_status": PRE_MAPPING_STATUS,
        "final_PRE_reaction_status": PRE_STATUS,
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
            "PDB": "4OU2",
            "ligand_component_id": "6OA",
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
        },
        "source_formal_D1_D6": {
            "D1_observed_covalent_chemistry": "POSITIVE",
            "D2_task_generation_domain_relevance": SOURCE_D2,
            "D3_reactive_atom_pair_confirmation_or_revision": "CONFIRM_OBSERVED_PAIR",
            "D3_observed_pair": "SG:C5",
            "D4_role_partition_and_minimal_seed_action": "PROVIDE_ROLE_PARTITION",
            "D4_selected_candidate": SELECTED_CANDIDATE,
            "D5_structural_task_applicability_action": "PROVIDE_APPLICABLE_TASK_IDS",
            "D5_applicable_task_ids": list(DIRECT_APPLICABLE_TASK_IDS),
            "D6_later_training_use_disposition": "NOT_APPLICABLE",
        },
        "task_relevance_normalization": _normalization_contract(),
        "completed_lane": EXPECTED_COMPLETED_LANE,
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
            "ligand_reactive_atom": "C5",
            "observed_pair": "SG:C5",
            "scope": EXPECTED_SCOPE,
            "sample_level_authoritative": True,
            "reusable_pair_authority": False,
            "ligand_wide_authority": False,
            "cross_structure_generalization": False,
        },
        "selected_role_partition": {
            "selected_candidate": SELECTED_CANDIDATE,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "warhead_atom_ids": list(WARHEAD_ATOMS),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(SCAFFOLD_ATOMS),
            "counts": {"W": 2, "L": 0, "S": 8, "Exact": 10},
            "boundary": BOUNDARY,
            "minimal_seed_atom_ids": list(MINIMAL_SEED),
            "primary_anchor": PRIMARY_ANCHOR,
            "sample_level_authoritative": True,
            "reusable_role_authority": False,
            "PRE_precursor_role_authority": False,
            "published_runtime_validation": bound[
                "published_DIRECT_runtime_validation"
            ],
        },
        "structural_validation": bound["graph_proof"],
        "canonical_task_contract": _task_contract(),
        "generic_Exact11_compatibility": bound["generic_Exact11_compatibility"],
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(),
        "training_boundary": _training_boundary(),
        "reusable_authority_boundary": {
            "reusable_chemistry_authority": False,
            "reusable_pair_authority": False,
            "reusable_role_authority": False,
            "reusable_minimal_seed_authority": False,
            "reaction_family_authority": False,
            "warhead_rule_authority": False,
            "warhead_type_authority": False,
            "2VS_authority_extended_to_6OA": False,
        },
        "current_with_NWJ_census_preingestion_boundary": bound[
            "current_census_boundary"
        ],
        "operation_boundary": _operation_boundary(),
        "readiness": _readiness(),
    }


MATRIX_HEADER = (
    "canonical_event_id",
    "scaleup_rank",
    "review_unit_id",
    "pdb_id",
    "protein_chain_or_asym",
    "ligand_component_id",
    "ligand_chain_or_asym",
    "selected_connection_id",
    "POST_distance_angstrom",
    "reported_POST_distance_angstrom",
    "geometry_outlier",
    "distance_normalized",
    "event_removed",
    "new_bond_order_inferred",
    "completed_lane",
    "legacy_completed_review_status",
    "human_review_completed",
    "source_formal_generation_domain_decision",
    "normalized_task_relevance_disposition",
    "chemistry_disposition",
    "negative_chemistry",
    "task_domain_negative",
    "positive_generative_supervision_eligible",
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
    "canonical_task_applicability_json",
    "structurally_applicable_task_ids_json",
    "task_applicability_sample_authority",
    "task_label_authority",
    "authoritative_task_labels_created",
    "event_task_label_rows_materialized",
    "mask_tensor_targets_created",
    "formal_event_training_use_decision",
    "training_use_allowed",
    "human_training_excluded",
    "candidate_for_future_training_admission",
    "future_training_admission_candidate",
    "training_admitted",
    "formal_training_admitted",
    "training_materialization_allowed",
    "tensor_target_created",
    "model_supervision_usable",
    "current_runtime_model_usable",
    "POST_source_evidence_available",
    "explicit_covalent_evidence",
    "distance_only_inference",
    "POST_geometry_training_authority",
    "POST_geometry_training_target_created",
    "supporting_adduct_source_graph_count",
    "candidate_PRE_free_source_graph_count",
    "mapping_count",
    "PRE_source_mapping_status",
    "final_PRE_reaction_status",
    "PRE_authority",
    "POST_to_PRE_copy",
    "PRE_zero_fill",
    "C5_O3_free_precursor_double_bond_authority",
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
    applicability = snapshot["canonical_task_contract"]["global_canonical_tasks"]
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        row: dict[str, object] = {
            "canonical_event_id": event["canonical_event_id"],
            "scaleup_rank": event["scaleup_rank"],
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "pdb_id": "4OU2",
            "protein_chain_or_asym": event["protein_chain_or_asym"],
            "ligand_component_id": "6OA",
            "ligand_chain_or_asym": event["ligand_chain_or_asym"],
            "selected_connection_id": event["selected_connection_id"],
            "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
            "reported_POST_distance_angstrom": event[
                "reported_POST_distance_frozen_lexeme"
            ],
            "geometry_outlier": str(event["geometry_outlier"]).lower(),
            "distance_normalized": "false",
            "event_removed": "false",
            "new_bond_order_inferred": "false",
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "human_review_completed": "true",
            "source_formal_generation_domain_decision": SOURCE_D2,
            "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "chemistry_disposition": "POSITIVE",
            "negative_chemistry": "false",
            "task_domain_negative": "true",
            "positive_generative_supervision_eligible": "false",
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "C5",
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
            "canonical_task_applicability_json": _json_cell(applicability),
            "structurally_applicable_task_ids_json": "[0,3,4]",
            "task_applicability_sample_authority": "true",
            "task_label_authority": "false",
            "authoritative_task_labels_created": "false",
            "event_task_label_rows_materialized": "false",
            "mask_tensor_targets_created": "false",
            "formal_event_training_use_decision": "NOT_APPLICABLE",
            "training_use_allowed": "false",
            "human_training_excluded": "false",
            "candidate_for_future_training_admission": "false",
            "future_training_admission_candidate": "false",
            "training_admitted": "false",
            "formal_training_admitted": "false",
            "training_materialization_allowed": "false",
            "tensor_target_created": "false",
            "model_supervision_usable": "false",
            "current_runtime_model_usable": "false",
            "POST_source_evidence_available": "true",
            "explicit_covalent_evidence": "true",
            "distance_only_inference": "false",
            "POST_geometry_training_authority": "false",
            "POST_geometry_training_target_created": "false",
            "supporting_adduct_source_graph_count": 0,
            "candidate_PRE_free_source_graph_count": 0,
            "mapping_count": 0,
            "PRE_source_mapping_status": PRE_MAPPING_STATUS,
            "final_PRE_reaction_status": PRE_STATUS,
            "PRE_authority": "false",
            "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false",
            "C5_O3_free_precursor_double_bond_authority": "false",
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
        "review_unit": "6OA",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": 4,
        "completed_review_unit_count": 1,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "source_formal_generation_domain_decision": SOURCE_D2,
        "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
        "task_not_relevant_count": count(
            "normalized_task_relevance_disposition", NORMALIZED_TASK_RELEVANCE
        ),
        "chemistry_positive_count": count("chemistry_disposition", "POSITIVE"),
        "negative_chemistry_count": count("negative_chemistry", True),
        "pair_authority_event_count": count("pair_sample_authority", True),
        "role_authority_event_count": count("role_sample_authority", True),
        "task_applicability_determined_event_count": count(
            "task_applicability_sample_authority", True
        ),
        "authoritative_task_label_event_count": count("task_label_authority", True),
        "event_task_label_rows_materialized_count": count(
            "event_task_label_rows_materialized", True
        ),
        "mask_tensor_target_count": count("mask_tensor_targets_created", True),
        "training_NOT_APPLICABLE_event_count": count(
            "formal_event_training_use_decision", "NOT_APPLICABLE"
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
        "rank857_geometry_outlier_retained": True,
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
        raise SixOAIngestionSafetyError(
            "COVAPIE_6OA_INGESTION_V1_ERROR:TEXT_UTF8_INVALID:" + label
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
            raise SixOAIngestionSafetyError(
                "COVAPIE_6OA_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
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
        "artifact_role": "6OA_COMPLETED_DECISION_METADATA_ONLY_INGESTION_MANIFEST",
        "candidate_publication_file_count": 7,
        "candidate_publication_paths": [
            path.as_posix() for path in CANDIDATE_PUBLICATION_PATHS
        ],
        "output_artifact_count": 4,
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
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
        "task_relevance_normalization": _normalization_contract(),
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        "generic_Exact11_compatibility": bound["generic_Exact11_compatibility"],
        "published_DIRECT_runtime_validation": bound[
            "published_DIRECT_runtime_validation"
        ],
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
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "projection_of_frozen_formal_human_authority": True,
            "new_human_authority_created_by_ingestion": False,
            "network_required": False,
        },
        "SNAPSHOT_ROOT_DRIFT",
    )
    _expect_fields(
        snapshot.get("task_relevance_normalization"),
        _normalization_contract(),
        "SNAPSHOT_NORMALIZATION_DRIFT",
    )
    _expect_fields(
        snapshot.get("canonical_task_contract"),
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
    events = snapshot.get("events")
    if type(events) is not list or len(events) != 4:
        _fail("SNAPSHOT_EVENTS_NOT_EXACT4")
    for event, expected in zip(events, EXPECTED_EVENTS, strict=True):
        event_id, rank, _protein, _ligand, _connection, exact, _reported, outlier = expected
        _expect_fields(
            event,
            {
                "canonical_event_id": event_id,
                "scaleup_rank": rank,
                "POST_distance_frozen_lexeme": exact,
                "geometry_outlier": outlier,
                "distance_normalized": False,
                "event_removed": False,
                "new_bond_order_inferred": False,
                "source_formal_generation_domain_decision": SOURCE_D2,
                "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
                "chemistry_disposition": "POSITIVE",
                "negative_chemistry": False,
                "task_domain_negative": True,
                "positive_generative_supervision_eligible": False,
                "pair_sample_authority": True,
                "role_sample_authority": True,
                "task_applicability_sample_authority": True,
                "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
                "formal_event_training_use_decision": "NOT_APPLICABLE",
                "human_training_excluded": False,
                "future_training_admission_candidate": False,
                "task_label_authority": False,
                "event_task_label_rows_materialized": False,
                "mask_tensor_targets_created": False,
                "PRE_source_mapping_status": PRE_MAPPING_STATUS,
                "final_PRE_reaction_status": PRE_STATUS,
                "POST_geometry_training_authority": False,
                "formal_training_admitted": False,
                "training_materialization_allowed": False,
                "parameter_update_authorization": False,
                "READY_FOR_TRAINING": False,
                "TRAINING_STARTED": False,
            },
            "SNAPSHOT_EVENT_DRIFT:" + str(rank),
        )
    _expect_fields(
        snapshot.get("selected_role_partition"),
        {
            "selected_candidate": SELECTED_CANDIDATE,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "warhead_atom_ids": list(WARHEAD_ATOMS),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(SCAFFOLD_ATOMS),
            "boundary": BOUNDARY,
            "minimal_seed_atom_ids": list(MINIMAL_SEED),
            "primary_anchor": PRIMARY_ANCHOR,
            "sample_level_authoritative": True,
            "reusable_role_authority": False,
        },
        "SNAPSHOT_ROLE_DRIFT",
    )
    authority = snapshot.get("sample_authority_map")
    _expect_fields(
        authority,
        {
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
        "SNAPSHOT_SAMPLE_AUTHORITY_DRIFT",
    )
    task_rows = snapshot["canonical_task_contract"].get("global_canonical_tasks")
    if type(task_rows) is not list or [
        row.get("semantic_long_name") for row in task_rows if type(row) is dict
    ] != [row[1] for row in CANONICAL_TASKS]:
        _fail("SNAPSHOT_CANONICAL_TASK_LONG_NAMES_DRIFT")
    reusable = snapshot.get("reusable_authority_boundary")
    _expect_fields(
        reusable,
        {
            "reusable_chemistry_authority": False,
            "reusable_pair_authority": False,
            "reusable_role_authority": False,
            "reusable_minimal_seed_authority": False,
            "reaction_family_authority": False,
            "warhead_rule_authority": False,
            "warhead_type_authority": False,
            "2VS_authority_extended_to_6OA": False,
        },
        "SNAPSHOT_REUSABLE_AUTHORITY_DRIFT",
    )
    _expect_fields(
        snapshot.get("PRE_boundary"), _pre_boundary(), "SNAPSHOT_PRE_DRIFT"
    )
    _expect_fields(
        snapshot.get("POST_boundary"), _post_boundary(), "SNAPSHOT_POST_DRIFT"
    )
    _expect_fields(
        snapshot.get("training_boundary"),
        _training_boundary(),
        "SNAPSHOT_TRAINING_DRIFT",
    )
    _expect_fields(
        snapshot.get("operation_boundary"),
        _operation_boundary(),
        "SNAPSHOT_OPERATION_DRIFT",
    )
    _expect_fields(
        snapshot.get("readiness"), _readiness(), "SNAPSHOT_READINESS_DRIFT"
    )
    generic = snapshot.get("generic_Exact11_compatibility")
    _expect_fields(
        generic,
        {
            "accepted_fact_count": 4,
            "generic_fact_field_count": 11,
            "rich_fields_leaked": False,
            "reconciliation_performed": False,
        },
        "SNAPSHOT_GENERIC_DRIFT",
    )
    facts = generic.get("facts") if type(generic) is dict else None
    if type(facts) is not list or len(facts) != 4:
        _fail("SNAPSHOT_GENERIC_FACTS_NOT_EXACT4")
    if any(set(fact) != set(GENERIC_FACT_FIELDS) for fact in facts):
        _fail("SNAPSHOT_GENERIC_FACT_NOT_EXACT11")


def _validate_summary_semantics(summary: Mapping[str, Any]) -> None:
    _expect_fields(
        summary,
        {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "event_count": 4,
            "completed_review_unit_count": 1,
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
            "source_formal_generation_domain_decision": SOURCE_D2,
            "normalized_task_relevance_disposition": NORMALIZED_TASK_RELEVANCE,
            "task_not_relevant_count": 4,
            "chemistry_positive_count": 4,
            "negative_chemistry_count": 0,
            "pair_authority_event_count": 4,
            "role_authority_event_count": 4,
            "task_applicability_determined_event_count": 4,
            "authoritative_task_label_event_count": 0,
            "event_task_label_rows_materialized_count": 0,
            "mask_tensor_target_count": 0,
            "training_NOT_APPLICABLE_event_count": 4,
            "human_training_excluded_count": 0,
            "future_training_admission_candidate_count": 0,
            "formal_training_admitted_count": 0,
            "PRE_authority_count": 0,
            "POST_training_authority_count": 0,
            "generic_exact11_accepted_count": 4,
            "generic_exact11_fact_count": 4,
            "rich_fields_leaked_to_generic_facts": False,
            "rank857_geometry_outlier_retained": True,
        },
        "SUMMARY_SEMANTICS_DRIFT",
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
            "candidate_publication_file_count": 7,
            "candidate_publication_paths": [
                path.as_posix() for path in CANDIDATE_PUBLICATION_PATHS
            ],
            "output_artifact_count": 4,
            "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
            "active_source_binding_count": 13,
            "semantic_source_identity_count": 13,
            "duplicate_source_binding_identity_count": 0,
            "formal_validator_provenance_identity_only": True,
            "formal_validator_imported": False,
            "formal_validator_executed_by_production": False,
            "formal_validator_subprocessed_by_production": False,
            "manifest_self_SHA256_recorded": False,
            "completed_lane": EXPECTED_COMPLETED_LANE,
            "legacy_completed_review_status": EXPECTED_LEGACY_STATUS,
        },
        "MANIFEST_ROOT_DRIFT",
    )
    _expect_fields(
        manifest.get("task_relevance_normalization"),
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
    _expect_fields(
        manifest.get("operation_boundary"),
        _operation_boundary(),
        "MANIFEST_OPERATION_DRIFT",
    )
    _expect_fields(
        manifest.get("training_boundary"),
        _training_boundary(),
        "MANIFEST_TRAINING_DRIFT",
    )
    _expect_fields(
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
    descriptor, temporary = tempfile.mkstemp(prefix=".covapie_6oa_", dir=path.parent)
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
