"""Project frozen NWJ Exact4 human authority into metadata-only artifacts.

The formal JSON is parsed and independently validated.  Its frozen validator
is provenance identity only and is never parsed, imported, executed, or
subprocessed.  This additive stage does not reconcile, refresh a census or
queue, materialize labels/tensors, alter a dataset, or train a model.
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
    "NWJIngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = "covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_nwj_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_nwj_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_nwj_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_nwj_completed_decision_ingestion_manifest_v1"
BASELINE_COMMIT = "a97c23cc89e98a92a1c1338f8587b2269a422636"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_nwj_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_nwj_event_task_label_availability_v1.csv"
SUMMARY = "covapie_nwj_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_nwj_completed_decision_ingestion_manifest_v1.json"
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
    "NWJ_COVAPIE_BULK_REVIEW_UNIT_DE7AFABE9D079CDF"
)
FORMAL_DECISION_RELATIVE = (
    STATE_ROOT / "formal-human-decision-v1/nwj_formal_human_decision_v1.json"
)
FORMAL_VALIDATOR_RELATIVE = (
    STATE_ROOT / "formal-human-decision-v1/validate_nwj_formal_human_decision_v1.py"
)
EVENT_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/nwj_exact4_event_evidence_v1.csv"
)
GRAPH_EVIDENCE_RELATIVE = (
    STATE_ROOT / "review-preparation-v1/nwj_graph_and_review_evidence_v1.json"
)
CCD_RELATIVE = Path(
    "covapie-state/bulk-model-usable-auto-admission-scaleup-v1/"
    "ranks-0501-1000/attempt-001/cache/rcsb/ccd/NWJ.cif"
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
    "covapie_cumulative1000_current_global_readiness_census_with_tp2_v1.py"
)
CENSUS_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_tp2_v1"
)
CENSUS_MATRIX_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_census_with_tp2_v1.csv"
)
CENSUS_SUMMARY_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_summary_with_tp2_v1.json"
)
CENSUS_MANIFEST_RELATIVE = (
    CENSUS_ROOT_RELATIVE
    / "covapie_cumulative1000_current_global_readiness_manifest_with_tp2_v1.json"
)

FORMAL_DECISION_SCHEMA = "covapie_nwj_exact4_formal_human_decision_v1"
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_DE7AFABE9D079CDF"
EXPECTED_SCOPE = "CURRENT_NWJ_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
SELECTED_CANDIDATE = "CANDIDATE_A_DIRECT_FORMYL"
NONSELECTED_CANDIDATE = "CANDIDATE_B_PHENYL_LINKER"
AUTHORITY_SOURCE = "FORMAL_NWJ_HUMAN_DECISION"
FUTURE_STATUS = (
    "CURRENT_HUMAN_DECISION_ALLOWS_ONLY_CANDIDACY_FOR_A_LATER_"
    "TRAINING_ADMISSION_FLOW"
)
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
PRE_STATUS = "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"

# event id, rank, protein asym, ligand asym, connection, exact lexeme, reported lexeme
EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:4CM5:A:CYS:168-:SG:F:NWJ:CAV",
        674,
        "A",
        "F",
        "covale1",
        "1.799966",
        "1.800",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4CM5:B:CYS:168-:SG:H:NWJ:CAV",
        675,
        "B",
        "H",
        "covale2",
        "1.822254",
        "1.822",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4CM5:C:CYS:168-:SG:J:NWJ:CAV",
        676,
        "C",
        "J",
        "covale3",
        "1.818468",
        "1.818",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4CM5:D:CYS:168-:SG:L:NWJ:CAV",
        677,
        "D",
        "L",
        "covale4",
        "1.828650",
        "1.829",
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)
WARHEAD_ATOMS = ("CAV", "OAE")
LINKER_ATOMS: tuple[str, ...] = ()
SCAFFOLD_ATOMS = (
    "C2",
    "C4",
    "C5",
    "C6",
    "CAG",
    "CAH",
    "CAI",
    "CAJ",
    "CAK",
    "CAL",
    "CAM",
    "CAN",
    "CAO",
    "CAX",
    "CAY",
    "CAZ",
    "CBA",
    "N1",
    "N3",
    "NAA",
    "NAB",
    "NAS",
    "NBF",
)
HEAVY_ATOMS = tuple(sorted((*WARHEAD_ATOMS, *SCAFFOLD_ATOMS)))
MINIMAL_SEED = ("CAX", "CAI", "CAK")
PRIMARY_ANCHOR = "CAX"
BOUNDARY = {
    "scaffold_atom_id": "CAX",
    "warhead_atom_id": "CAV",
    "bond_order": "SING",
}

CANDIDATE_B_WARHEAD = ("CAV", "OAE")
CANDIDATE_B_LINKER = ("CAH", "CAI", "CAJ", "CAK", "CAX", "CAY")
CANDIDATE_B_SCAFFOLD = (
    "C2",
    "C4",
    "C5",
    "C6",
    "CAG",
    "CAL",
    "CAM",
    "CAN",
    "CAO",
    "CAZ",
    "CBA",
    "N1",
    "N3",
    "NAA",
    "NAB",
    "NAS",
    "NBF",
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

# path, namespace, bytes, SHA256, executable, role, validation method
_Binding = tuple[Path, str, int, str, bool, str, str]
FORMAL_BINDINGS: tuple[_Binding, ...] = (
    (
        FORMAL_DECISION_RELATIVE,
        "project_parent_relative",
        24265,
        "1e53df67e44b61d8103148036cf59d976974d7481754af700cc0cd89dfadeaff",
        False,
        "NWJ_FROZEN_FORMAL_HUMAN_DECISION",
        "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE,
        "project_parent_relative",
        68924,
        "1cc1bb5ea615bcf662ac1410dc15ef3aa82991e6243dec461cb8ada20078336d",
        False,
        "NWJ_FROZEN_FORMAL_VALIDATOR",
        "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED",
    ),
)
SUPPORTING_BINDINGS: tuple[_Binding, ...] = (
    (
        EVENT_EVIDENCE_RELATIVE,
        "project_parent_relative",
        8973,
        "b19881efa97e8f61e6ae3dab9f44f6343c32fcc3c721929ab91f00b484136b2c",
        False,
        "NWJ_EXACT4_EVENT_EVIDENCE",
        "PARSED_CSV_SUPPORTING_EVIDENCE",
    ),
    (
        GRAPH_EVIDENCE_RELATIVE,
        "project_parent_relative",
        33453,
        "f12d9132b47e1390aad1fa14dbd0f76c74be64730a42b89f6691eade3833a8a4",
        False,
        "NWJ_GRAPH_AND_REVIEW_EVIDENCE",
        "PARSED_JSON_INDEPENDENT_EXACT25_GRAPH_PROOF",
    ),
    (
        CCD_RELATIVE,
        "project_parent_relative",
        10154,
        "938d3d511360aecf600222289e6cd436aee223c52da62d0e0c613e558d912c3e",
        False,
        "NWJ_FROZEN_CCD",
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
        "IMPORTED_AND_CALLED_FOR_PARTITION_PROFILE_BOUNDARY_SEED_AND_TASKS",
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
)
CENSUS_BINDINGS: tuple[_Binding, ...] = (
    (
        CENSUS_OWNER_RELATIVE,
        "repository_relative",
        75962,
        "e0fe9e02407cc6aff82d904b93856b82fa88e33f913dd6b5a3a13f332130dee0",
        False,
        "CURRENT_WITH_TP2_CENSUS_OWNER",
        "CONTENT_IDENTITY_READ_ONLY",
    ),
    (
        CENSUS_MATRIX_RELATIVE,
        "repository_relative",
        551742,
        "634f2f2d1c5a7f63d11f30bfe49eb5881edc681cfd94321a5cb5047f574b467a",
        False,
        "CURRENT_WITH_TP2_CENSUS_MATRIX",
        "PARSED_CSV_PREFORMAL_STATE_READ_ONLY",
    ),
    (
        CENSUS_SUMMARY_RELATIVE,
        "repository_relative",
        21281,
        "9862d0a4434560c12c0573a7076732192d15f6b24fe73e515b049d5bcb5fc1b4",
        False,
        "CURRENT_WITH_TP2_CENSUS_SUMMARY",
        "PARSED_JSON_PENDING_RANK_READ_ONLY",
    ),
    (
        CENSUS_MANIFEST_RELATIVE,
        "repository_relative",
        79341,
        "75f969219f83d823a9b4e30037f3afd56da76fb62119d9b17c9901ff46de1b1d",
        False,
        "CURRENT_WITH_TP2_CENSUS_MANIFEST",
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


class NWJIngestionSafetyError(ValueError):
    """Raised when the frozen NWJ projection contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise NWJIngestionSafetyError("COVAPIE_NWJ_INGESTION_V1_ERROR:" + reason)


def _expect(actual: object, expected: object, reason: str) -> None:
    if type(actual) is not type(expected) or actual != expected:
        _fail(reason)


def _expect_fields(
    mapping: object, expected: Mapping[str, object], reason: str
) -> Mapping[str, object]:
    if type(mapping) is not dict:
        _fail(reason + ":NOT_OBJECT")
    for key, value in expected.items():
        _expect(mapping.get(key), value, reason + ":" + key)  # type: ignore[union-attr]
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
        raise NWJIngestionSafetyError(
            "COVAPIE_NWJ_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label
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
        raise NWJIngestionSafetyError(
            "COVAPIE_NWJ_INGESTION_V1_ERROR:JSON_PARSE_FAILED:" + label
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
        raise NWJIngestionSafetyError(
            "COVAPIE_NWJ_INGESTION_V1_ERROR:CSV_UTF8_INVALID:" + label
        ) from error
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        _fail("CSV_HEADER_INVALID:" + label)
    rows = list(reader)
    if any(None in row for row in rows):
        _fail("CSV_ROW_WIDTH_INVALID:" + label)
    return rows


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


def _binding_record(binding: _Binding) -> dict[str, object]:
    path, namespace, byte_count, digest, executable, role, method = binding
    return {
        "path": path.as_posix(),
        "path_namespace": namespace,
        "byte_count": byte_count,
        "SHA256": digest,
        "semantic_source_identity": f"{namespace}:{path.as_posix()}@{digest}",
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": (
            "EXECUTABLE" if executable else "NON_EXECUTABLE"
        ),
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
        raise NWJIngestionSafetyError(
            "COVAPIE_NWJ_INGESTION_V1_ERROR:SOURCE_BINDING_FAILED:"
            + relative.as_posix()
        ) from error


def _verify_bindings(
    repo_root: Path, overrides: Mapping[Path, Path]
) -> dict[Path, bytes]:
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
        raise NWJIngestionSafetyError(
            "COVAPIE_NWJ_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
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
                    raise NWJIngestionSafetyError(
                        "COVAPIE_NWJ_INGESTION_V1_ERROR:"
                        "SEMANTIC_OWNER_LITERAL_INVALID:" + target.id
                    ) from error
    if set(values) != set(names):
        _fail("SEMANTIC_OWNER_LITERAL_MISSING:" + label)
    return values


def _validate_formal(formal: Mapping[str, Any]) -> None:
    """Independently validate the critical frozen formal semantics."""
    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(
        formal.get("record_role"),
        "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        "FORMAL_RECORD_ROLE_DRIFT",
    )
    _expect_fields(
        formal.get("formal_state"),
        {
            "approved": True,
            "unsigned": False,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "decision_finalized": True,
            "human_authority_created": True,
            "human_decision_created": True,
            "human_review_completed": True,
            "formal_authority_created": True,
            "formal_decision_created": True,
            "machine_human_approval": False,
            "machine_scientific_authority": False,
        },
        "FORMAL_STATE_DRIFT",
    )
    _expect_fields(
        formal.get("sample_identity"),
        {
            "PDB": "4CM5",
            "ligand_component_id": "NWJ",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scope": EXPECTED_SCOPE,
            "event_count": 4,
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "scaleup_event_ranks": list(EXPECTED_RANKS),
            "raw_priority_rank": 28,
            "current_pending_rank": 1,
            "rank_systems_are_distinct": True,
            "ligand_wide_authority": False,
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
            "D2_generation_domain_relevance": "IN_DOMAIN",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D3_protein_atom": "SG",
            "D3_ligand_atom": "CAV",
            "D3_scope": EXPECTED_SCOPE,
            "D4_role_partition": SELECTED_CANDIDATE,
            "HUMAN_SELECTION": SELECTED_CANDIDATE,
            "D5_structural_task_applicability": [0, 3, 4],
            "D6_later_training_use": "INCLUDE",
        },
        "FORMAL_EXTERNAL_DECISION_INPUT_DRIFT",
    )

    decisions = formal.get("formal_decisions")
    if type(decisions) is not dict:
        _fail("FORMAL_DECISIONS_MISSING")
    _expect_fields(
        decisions.get("D1_observed_covalent_chemistry"),
        {
            "decision": "POSITIVE",
            "chemistry_human_authoritative": True,
            "human_authoritative_sample_conclusion": "stable Cys168 thioester linkage",
            "observed_product": "STABLE_CYS168_THIOESTER_LINKAGE",
            "initial_thioacetal_then_oxidation": (
                "AUTHOR_PROPOSED_PRESUMED_MECHANISM_ONLY"
            ),
            "asserted_as_proven_mechanism": False,
            "scope": EXPECTED_SCOPE,
        },
        "FORMAL_D1_DRIFT",
    )
    _expect_fields(
        decisions.get("D2_generation_domain_relevance"),
        {
            "decision": "IN_DOMAIN",
            "task_relevance_human_authoritative": True,
            "objective": "TARGET_DIRECTED_SMALL_MOLECULE_COVALENT_INHIBITOR_GENERATION",
            "reason": (
                "target-directed small-molecule TbPTR1 inhibitor designed for "
                "covalent capture of native Cys168"
            ),
            "designed_for_covalent_capture_of": "native Cys168",
            "TbPTR1_Ki_app_micromolar": 0.2,
            "T_b_brucei_IC50_micromolar": 7.75,
            "scope": EXPECTED_SCOPE,
        },
        "FORMAL_D2_DRIFT",
    )
    _expect_fields(
        decisions.get("D3_reactive_pair"),
        {
            "decision": "CONFIRM_OBSERVED_PAIR",
            "protein_atom": "SG",
            "ligand_atom": "CAV",
            "scope": EXPECTED_SCOPE,
            "reactive_pair_human_authoritative": True,
            "reactive_pair_sample_authoritative": True,
            "reusable_pair_authority": False,
            "ligand_wide_authority": False,
            "cross_structure_generalization": False,
        },
        "FORMAL_D3_DRIFT",
    )
    _expect_fields(
        decisions.get("D4_role_partition"),
        {
            "decision": SELECTED_CANDIDATE,
            "selected_candidate": SELECTED_CANDIDATE,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "role_partition_sample_authoritative": True,
            "role_profile_sample_authoritative": True,
            "minimal_seed_sample_authoritative": True,
            "candidate_B_runtime_valid_nonselected_alternative": True,
            "candidate_B_selected": False,
            "candidate_B_authoritative": False,
        },
        "FORMAL_D4_DRIFT",
    )
    _expect_fields(
        decisions.get("D5_structural_task_applicability"),
        {
            "decision": [0, 3, 4],
            "role_profile": EXPECTED_ROLE_PROFILE,
            "task_applicability_determined": True,
            "task_applicability_sample_authoritative": True,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
            "training_mask_targets_available_now": False,
            "applicable_tasks": [
                {"task_id": 0, "semantic_long_name": "warhead_only"},
                {"task_id": 3, "semantic_long_name": "scaffold_only"},
                {
                    "task_id": 4,
                    "semantic_long_name": "scaffold_plus_linker_plus_warhead",
                },
            ],
        },
        "FORMAL_D5_DRIFT",
    )
    _expect_fields(
        decisions.get("D6_later_training_use"),
        {
            "decision": "INCLUDE",
            "human_training_use_disposition": "INCLUDE",
            "training_use_human_authoritative": True,
            "future_training_admission_candidate": True,
            "include_semantics": (
                "CURRENT_SAMPLE_MAY_ENTER_A_LATER_TRAINING_ADMISSION_"
                "CANDIDATE_FLOW_ONLY"
            ),
            "formal_training_admitted": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
            "parameter_update_authorization": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "FORMAL_D6_DRIFT",
    )

    selected = _expect_fields(
        formal.get("selected_role_context"),
        {
            "candidate_id": SELECTED_CANDIDATE,
            "candidate_A_selected": True,
            "candidate_A_authoritative": True,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "role_partition_sample_authoritative": True,
            "role_profile_sample_authoritative": True,
            "warhead_atom_ids": list(WARHEAD_ATOMS),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(SCAFFOLD_ATOMS),
            "counts": {"warhead": 2, "linker": 0, "scaffold": 23, "total": 25},
            "task_ids": [0, 3, 4],
            "phenyl_assignment": "SCAFFOLD",
        },
        "FORMAL_SELECTED_ROLE_DRIFT",
    )
    _expect_fields(
        selected.get("minimal_seed"),
        {
            "atom_ids": list(MINIMAL_SEED),
            "primary_scaffold_side_anchor": PRIMARY_ANCHOR,
            "runtime_valid": True,
            "runtime_reasons": [],
            "minimal_seed_sample_authoritative": True,
            "reusable_minimal_seed_authority": False,
        },
        "FORMAL_SELECTED_SEED_DRIFT",
    )
    _expect_fields(
        selected.get("published_runtime"),
        {
            "runtime_valid": True,
            "runtime_reasons": [],
            "derived_task_ids": [0, 3, 4],
            "derived_primary_anchor": PRIMARY_ANCHOR,
            "direct_boundary": {**BOUNDARY, "boundary_valid": True},
            "role_validator": "validate_role_profile_v1",
            "minimal_seed_validator": "validate_minimal_seed_for_role_profile_v1",
        },
        "FORMAL_SELECTED_RUNTIME_DRIFT",
    )
    _expect_fields(
        selected.get("structural_validation"),
        {
            "pairwise_disjoint": True,
            "exhaustive_over_Exact25": True,
            "warhead_connected": True,
            "linker_connected_or_empty": True,
            "scaffold_connected": True,
            "observed_CAV_in_warhead": True,
            "complete_formyl_CAV_OAE_in_warhead": True,
            "cross_role_boundaries": [
                {
                    "atom_id_1": "CAV",
                    "atom_id_2": "CAX",
                    "bond_order": "SING",
                    "role_pair": "warhead-scaffold",
                }
            ],
        },
        "FORMAL_SELECTED_STRUCTURE_DRIFT",
    )

    alternative = _expect_fields(
        formal.get("retained_nonselected_alternative"),
        {
            "candidate_id": NONSELECTED_CANDIDATE,
            "candidate_B_runtime_valid_nonselected_alternative": True,
            "candidate_B_selected": False,
            "candidate_B_authoritative": False,
            "not_asserted_wrong": True,
            "role_profile": "STRICT_LINKER_PRESENT_V1",
            "warhead_atom_ids": list(CANDIDATE_B_WARHEAD),
            "linker_atom_ids": list(CANDIDATE_B_LINKER),
            "scaffold_atom_ids": list(CANDIDATE_B_SCAFFOLD),
            "task_ids": [0, 1, 2, 3, 4],
            "counts": {"warhead": 2, "linker": 6, "scaffold": 17, "total": 25},
        },
        "FORMAL_CANDIDATE_B_DRIFT",
    )
    _expect_fields(
        alternative.get("published_runtime"),
        {
            "runtime_valid": True,
            "runtime_reasons": [],
            "derived_task_ids": [0, 1, 2, 3, 4],
        },
        "FORMAL_CANDIDATE_B_RUNTIME_DRIFT",
    )

    exact5 = formal.get("canonical_Exact5")
    if type(exact5) is not dict:
        _fail("FORMAL_EXACT5_MISSING")
    _expect_fields(
        exact5,
        {
            "task_count": 5,
            "B3_present": True,
            "sixth_task": False,
            "selected_structural_applicability_task_ids": [0, 3, 4],
            "task_applicability_determined": True,
            "task_applicability_sample_authoritative": True,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
            "training_mask_targets_available_now": False,
        },
        "FORMAL_EXACT5_DRIFT",
    )
    expected_task_rows = [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "generated_roles": list(generated),
            "fixed_or_seed_roles": list(fixed),
            "minimal_seed_or_anchor_retained": task_id == 4,
            "task_label_authority": False,
        }
        for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
    ]
    _expect(exact5.get("tasks"), expected_task_rows, "FORMAL_EXACT5_TASK_ROWS_DRIFT")

    _expect_fields(
        formal.get("PRE_boundary"),
        {
            "candidate_PRE_free_source_graph_count_per_event": 1,
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
        },
        "FORMAL_PRE_DRIFT",
    )
    _expect_fields(
        formal.get("POST_boundary"),
        {
            "Exact4_observed_POST_geometry": True,
            "explicit_covalent_evidence": True,
            "distance_only": False,
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
        },
        "FORMAL_POST_DRIFT",
    )
    _expect_fields(
        formal.get("training_boundary"),
        {
            "human_training_use_disposition": "INCLUDE",
            "training_use_human_authoritative": True,
            "future_training_admission_candidate": True,
            "future_training_admission_candidate_semantics": FUTURE_STATUS,
            "formal_training_admitted": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
            "training_dataset_altered": False,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
            "training_mask_targets_available_now": False,
            "parameter_update_authorization": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "FORMAL_TRAINING_DRIFT",
    )

    reusable = formal.get("reusable_authority_map")
    if type(reusable) is not dict or not reusable or any(
        value is not False for value in reusable.values()
    ):
        _fail("FORMAL_REUSABLE_AUTHORITY_FORGED")
    sample_authority = formal.get("sample_authority_map")
    if type(sample_authority) is not dict or not sample_authority or any(
        value is not True for value in sample_authority.values()
    ):
        _fail("FORMAL_SAMPLE_AUTHORITY_DRIFT")
    _expect_fields(
        formal.get("readiness"),
        {
            "NWJ_FORMAL_HUMAN_DECISION_V1_PASS": True,
            "HUMAN_AUTHORITY_CREATED": True,
            "HUMAN_DECISION_CREATED": True,
            "HUMAN_REVIEW_COMPLETED": True,
            "FORMAL_AUTHORITY_CREATED": True,
            "FORMAL_DECISION_CREATED": True,
            "SELECTED_ROLE_CANDIDATE": SELECTED_CANDIDATE,
            "FORMAL_TRAINING_ADMITTED": False,
            "TRAINING_ADMISSION_CREATED": False,
            "TRAINING_MATERIALIZATION_ALLOWED": False,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "STEP12D_STATUS": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "FORMAL_READINESS_DRIFT",
    )
    operations = formal.get("operation_boundary")
    if type(operations) is not dict or not operations or any(
        value is not False for value in operations.values()
    ):
        _fail("FORMAL_OPERATION_ALREADY_OCCURRED")
    _expect_fields(
        formal.get("output_inventory"),
        {
            "file_count": 2,
            "files": [
                "nwj_formal_human_decision_v1.json",
                "validate_nwj_formal_human_decision_v1.py",
            ],
            "formal_JSON_self_SHA256_recorded": False,
        },
        "FORMAL_OUTPUT_INVENTORY_DRIFT",
    )
    provenance = formal.get("provenance")
    if type(provenance) is not dict:
        _fail("FORMAL_PROVENANCE_MISSING")
    _expect_fields(
        provenance,
        {
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "machine_made_human_decision": False,
            "candidate_artifact_is_human_authority": False,
            "Codex_inference_is_human_authority": False,
            "upstream_artifacts_byte_identical_before_after_revalidation": True,
        },
        "FORMAL_PROVENANCE_DRIFT",
    )
    source_bindings = provenance.get("source_bindings")
    if type(source_bindings) is not list:
        _fail("FORMAL_PROVENANCE_BINDINGS_MISSING")
    validator_matches = [
        row
        for row in source_bindings
        if type(row) is dict
        and row.get("relative_path") == "validate_nwj_formal_human_decision_v1.py"
    ]
    if len(validator_matches) != 1:
        _fail("FORMAL_VALIDATOR_PROVENANCE_NOT_EXACT1")
    _expect_fields(
        validator_matches[0],
        {
            "bytes": 68924,
            "SHA256": FORMAL_BINDINGS[1][3],
            "mode": "0664",
            "path_namespace": "formal_human_decision_relative",
            "source_role": "formal_validator",
        },
        "FORMAL_VALIDATOR_PROVENANCE_DRIFT",
    )


def _validate_event_evidence(payload: bytes) -> list[dict[str, object]]:
    rows = _parse_csv(payload, "NWJ_EVENT_EVIDENCE")
    if len(rows) != 4 or tuple(row.get("canonical_event_id") for row in rows) != EXPECTED_EVENT_IDS:
        _fail("EVENT_EVIDENCE_EXACT4_DRIFT")
    projected: list[dict[str, object]] = []
    for index, (row, expected) in enumerate(zip(rows, EXPECTED_EVENTS)):
        required = {
            "package_role": "UNSIGNED_NON_AUTHORITATIVE_MACHINE_REVIEW_AID_PREPARATION",
            "event_index_0based": str(index),
            "scaleup_event_rank": str(expected[1]),
            "raw_review_unit_priority_rank": "28",
            "current_pending_rank": "1",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "pdb_id": "4CM5",
            "model_number": "1",
            "protein_label_asym_id": expected[2],
            "protein_auth_chain": expected[2],
            "protein_label_comp_id": "CYS",
            "protein_auth_seq_id": "168",
            "protein_insertion_code": "",
            "protein_reactive_atom": "SG",
            "ligand_component_id": "NWJ",
            "ligand_label_asym_id": expected[3],
            "ligand_auth_chain": expected[2],
            "ligand_reactive_atom": "CAV",
            "connection_id": expected[4],
            "connection_type": "covale",
            "connection_source": "FROZEN_WWPDB_MMCIF_STRUCT_CONN_EXPLICIT",
            "explicit_covalent_evidence": "true",
            "distance_only_inference": "false",
            "reported_POST_distance_angstrom": expected[6],
            "exact_POST_distance_angstrom": expected[5],
            "POST_source_evidence_available": "true",
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
        for key, value in required.items():
            if row.get(key) != value:
                _fail("EVENT_EVIDENCE_DRIFT:" + key)
        projected.append(
            {
                "canonical_event_id": expected[0],
                "scaleup_rank": expected[1],
                "PDB": "4CM5",
                "model_number": 1,
                "protein_chain_or_asym": expected[2],
                "cys_residue_id": "CYS:168-",
                "ligand_chain_or_asym": expected[3],
                "selected_connection_id": expected[4],
                "POST_distance_frozen_lexeme": expected[5],
                "reported_POST_distance_frozen_lexeme": expected[6],
            }
        )
    return projected


def _connected(
    atom_ids: Sequence[str], bonds: Sequence[tuple[str, str, str]]
) -> bool:
    if not atom_ids:
        return True
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


def _validate_partition_graph(
    atom_ids: Sequence[str], bonds: Sequence[tuple[str, str, str]]
) -> dict[str, object]:
    atom_set = set(atom_ids)
    role_sets = {"W": set(WARHEAD_ATOMS), "L": set(), "S": set(SCAFFOLD_ATOMS)}
    pairwise_disjoint = not (
        role_sets["W"] & role_sets["L"]
        or role_sets["W"] & role_sets["S"]
        or role_sets["L"] & role_sets["S"]
    )
    exhaustive = set().union(*role_sets.values()) == atom_set
    if not pairwise_disjoint:
        _fail("GRAPH_PARTITION_NOT_PAIRWISE_DISJOINT")
    if not exhaustive:
        _fail("GRAPH_PARTITION_NOT_EXHAUSTIVE")
    if any(
        left not in atom_set or right not in atom_set or left == right
        for left, right, _order in bonds
    ):
        _fail("GRAPH_BOND_ENDPOINT_INVALID")
    W_connected = _connected(WARHEAD_ATOMS, bonds)
    L_connected_or_empty = True
    S_connected = _connected(SCAFFOLD_ATOMS, bonds)
    reactive_CAV_in_W = "CAV" in role_sets["W"]
    if not W_connected:
        _fail("GRAPH_W_DISCONNECTED")
    if not S_connected:
        _fail("GRAPH_S_DISCONNECTED")
    if not reactive_CAV_in_W:
        _fail("GRAPH_REACTIVE_CAV_NOT_IN_W")
    role_by_atom = {
        atom_id: role for role, members in role_sets.items() for atom_id in members
    }
    boundaries: list[tuple[str, str, str]] = []
    for left, right, order in bonds:
        if role_by_atom[left] == role_by_atom[right]:
            continue
        if (role_by_atom[left], role_by_atom[right]) == ("S", "W"):
            boundaries.append((left, right, order))
        elif (role_by_atom[left], role_by_atom[right]) == ("W", "S"):
            boundaries.append((right, left, order))
        else:
            _fail("GRAPH_UNEXPECTED_CROSS_ROLE_CLASS")
    if boundaries != [("CAX", "CAV", "SING")]:
        _fail("GRAPH_DIRECT_BOUNDARY_NOT_UNIQUE_EXACT")
    return {
        "Exact25_count": 25,
        "partition_pairwise_disjoint": pairwise_disjoint,
        "partition_exhaustive": exhaustive,
        "W_connected": W_connected,
        "L_connected_or_empty": L_connected_or_empty,
        "S_connected": S_connected,
        "reactive_CAV_in_W": reactive_CAV_in_W,
        "cross_role_boundary_count": 1,
        "cross_role_boundary": BOUNDARY,
        "W_count": 2,
        "L_count": 0,
        "S_count": 23,
    }


def _validate_graph_evidence(payload: bytes) -> dict[str, object]:
    document = _strict_json(payload, "NWJ_GRAPH_EVIDENCE")
    _expect_fields(
        document,
        {
            "schema_version": "covapie_nwj_graph_and_review_evidence_v1",
            "package_role": "UNSIGNED_NON_AUTHORITATIVE_MACHINE_REVIEW_AID_PREPARATION",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "pdb_ids": ["4CM5"],
            "ligand_component_id": "NWJ",
            "target_event_count": 4,
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "scaleup_event_ranks": list(EXPECTED_RANKS),
            "source_structural_evidence_only": True,
            "PREPARATION_ONLY": True,
            "sample_task_applicability": None,
        },
        "GRAPH_IDENTITY_DRIFT",
    )
    graph = document.get("CCD_complete_heavy_atom_graph")
    if type(graph) is not dict:
        _fail("GRAPH_MISSING")
    _expect_fields(
        graph,
        {
            "component_id": "NWJ",
            "heavy_atom_count": 25,
            "heavy_heavy_bond_count": 28,
            "connected": True,
            "connected_component_count": 1,
            "canonical_heavy_graph_sha256": (
                "cdd4fe1c52d7aae45ea7cb0f18041a6e10f89dc1543e14d7eddc377d0f05b671"
            ),
        },
        "GRAPH_METADATA_DRIFT",
    )
    atoms = graph.get("atom_inventory")
    raw_bonds = graph.get("bond_inventory")
    if type(atoms) is not list or type(raw_bonds) is not list:
        _fail("GRAPH_INVENTORY_INVALID")
    if len(atoms) != 25 or any(type(row) is not dict for row in atoms):
        _fail("GRAPH_ATOM_ROWS_INVALID")
    atom_ids = tuple(sorted(row.get("atom_id") for row in atoms))
    _expect(atom_ids, HEAVY_ATOMS, "GRAPH_EXACT25_ATOMS_DRIFT")
    if len(raw_bonds) != 28 or any(type(row) is not dict for row in raw_bonds):
        _fail("GRAPH_BOND_ROWS_INVALID")
    bonds = tuple(
        (row.get("atom_id_1"), row.get("atom_id_2"), row.get("bond_order"))
        for row in raw_bonds
    )
    if any(
        type(left) is not str or type(right) is not str or type(order) is not str
        for left, right, order in bonds
    ):
        _fail("GRAPH_BOND_VALUE_INVALID")
    proof = _validate_partition_graph(atom_ids, bonds)  # type: ignore[arg-type]
    pre = document.get("PRE_evidence")
    if type(pre) is not dict:
        _fail("GRAPH_PRE_EVIDENCE_MISSING")
    _expect_fields(
        pre,
        {
            "availability": "CANDIDATE_SOURCE_GRAPH_PRESENT_MAPPING_INCOMPATIBLE",
            "mapping_status": PRE_MAPPING_STATUS,
            "reaction_status": PRE_STATUS,
            "PRE_fabricated": False,
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
            "PRE_topology_created": False,
            "PRE_coordinates_created": False,
            "leaving_group_inferred": False,
            "reagent_inferred": False,
            "reaction_edit_inferred": False,
        },
        "GRAPH_PRE_DRIFT",
    )
    event_audit = pre.get("event_audit")
    if type(event_audit) is not list or len(event_audit) != 4:
        _fail("GRAPH_PRE_EVENT_AUDIT_NOT_EXACT4")
    for row, event_id in zip(event_audit, EXPECTED_EVENT_IDS):
        _expect_fields(
            row,
            {
                "canonical_event_id": event_id,
                "supporting_adduct_graph_count": 1,
                "candidate_PRE_free_source_graph_count": 1,
                "source_PRE_mapping_count": 0,
                "source_mapping_status": PRE_MAPPING_STATUS,
                "final_PRE_reaction_status": PRE_STATUS,
            },
            "GRAPH_PRE_EVENT_DRIFT",
        )
    return {
        "atom_ids": atom_ids,
        "bonds": bonds,
        "atom_rows": atoms,
        **proof,
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
        (0, 3, 4),
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


def _runtime_validation(structural: Mapping[str, object]) -> dict[str, object]:
    runtime = importlib.import_module(
        "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"
    )
    role = runtime.validate_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE,
        retained_heavy_atoms=structural["atom_ids"],
        scaffold_atoms=SCAFFOLD_ATOMS,
        linker_atoms=LINKER_ATOMS,
        warhead_atoms=WARHEAD_ATOMS,
        reactive_atom_id="CAV",
        direct_scaffold_warhead_boundaries=(("CAX", "CAV", "SING"),),
        explicit_graph_bonds=structural["bonds"],
    )
    boundary = role.direct_scaffold_warhead_boundary
    if not (
        role.valid is True
        and tuple(role.reasons) == ()
        and role.scaffold_count == 23
        and role.linker_count == 0
        and role.warhead_count == 2
        and boundary is not None
        and boundary.boundary_valid is True
        and boundary.scaffold_atom_id == "CAX"
        and boundary.warhead_atom_id == "CAV"
        and boundary.bond_order == "SING"
    ):
        _fail("PUBLISHED_DIRECT_ROLE_RUNTIME_FAILED")
    seed = runtime.validate_minimal_seed_for_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE,
        seed_atoms=MINIMAL_SEED,
        scaffold_atoms=SCAFFOLD_ATOMS,
        linker_atoms=LINKER_ATOMS,
        warhead_atoms=WARHEAD_ATOMS,
        explicit_graph_bonds=structural["bonds"],
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
    if task_ids != (0, 3, 4):
        _fail("PUBLISHED_DIRECT_TASK_RUNTIME_FAILED")
    return {
        "valid": True,
        "reasons": [],
        "profile": EXPECTED_ROLE_PROFILE,
        "counts": {"W": 2, "L": 0, "S": 23},
        "boundary": BOUNDARY,
        "minimal_seed_atom_ids": list(MINIMAL_SEED),
        "primary_anchor_atom_id": PRIMARY_ANCHOR,
        "applicable_task_ids": list(task_ids),
        "partition_validator": "validate_role_profile_v1",
        "seed_validator": "validate_minimal_seed_for_role_profile_v1",
        "task_applicability_owner": "valid_canonical_task_ids_for_role_profile_v1",
    }


def _current_census(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    rows = _parse_csv(payloads[CENSUS_MATRIX_RELATIVE], "CURRENT_WITH_TP2_CENSUS")
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
        _fail("CURRENT_CENSUS_NWJ_EXACT4_DRIFT")
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
    for row in targets:
        for key, value in prior.items():
            if row.get(key) != value:
                _fail("CURRENT_CENSUS_NWJ_PRIOR_STATE_DRIFT:" + key)
    summary = _strict_json(
        payloads[CENSUS_SUMMARY_RELATIVE], "CURRENT_WITH_TP2_SUMMARY"
    )
    _strict_json(payloads[CENSUS_MANIFEST_RELATIVE], "CURRENT_WITH_TP2_MANIFEST")
    pending = summary.get("top_pending_review_units_by_event_yield")
    if type(pending) is not list or not pending or type(pending[0]) is not dict:
        _fail("CURRENT_CENSUS_PENDING_QUEUE_MISSING")
    _expect_fields(
        pending[0],
        {
            "rank": 1,
            "raw_priority_rank": 28,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "event_count": 4,
            "ligand_component_ids": ["NWJ"],
            "pdb_ids": ["4CM5"],
            "current_review_status": "CURRENTLY_UNREVIEWED",
        },
        "CURRENT_CENSUS_PENDING_RANK1_DRIFT",
    )
    authority = summary.get("authority_boundary")
    _expect_fields(
        authority,
        {
            "next_priority_review_current_pending_rank": 1,
            "next_priority_review_ligand": "NWJ",
            "next_priority_review_raw_priority_rank": 28,
            "next_priority_review_unit": EXPECTED_REVIEW_UNIT_ID,
        },
        "CURRENT_CENSUS_NEXT_PRIORITY_DRIFT",
    )
    return {
        "row_count": 1000,
        "NWJ_event_count": 4,
        "NWJ_current_global_status": "CURRENTLY_UNREVIEWED",
        "NWJ_task_relevance": "UNRESOLVED",
        "NWJ_chemistry": "UNRESOLVED",
        "NWJ_training_use": "UNRESOLVED",
        "current_pending_rank": 1,
        "raw_priority_rank": 28,
        "next_priority_review_ligand": "NWJ",
        "census_modified_by_ingestion": False,
    }


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Bind and independently validate the frozen NWJ authority and evidence."""
    root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    payloads = _verify_bindings(root, overrides)
    formal = _strict_json(payloads[FORMAL_DECISION_RELATIVE], "NWJ_FORMAL_DECISION")
    _validate_formal(formal)
    events = _validate_event_evidence(payloads[EVENT_EVIDENCE_RELATIVE])
    structural = _validate_graph_evidence(payloads[GRAPH_EVIDENCE_RELATIVE])
    _validate_semantic_owners(payloads)
    runtime = _runtime_validation(structural)
    census = _current_census(payloads)
    return {
        "formal_document": formal,
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "supporting_bindings": [
            _binding_record(binding) for binding in SUPPORTING_BINDINGS
        ],
        "source_binding_policy_binding": _binding_record(POLICY_BINDING),
        "semantic_owner_bindings": [
            _binding_record(binding) for binding in SEMANTIC_OWNER_BINDINGS
        ],
        "current_census_bindings": [
            _binding_record(binding) for binding in CENSUS_BINDINGS
        ],
        "events": events,
        "graph_structural_proof": {
            key: structural[key]
            for key in (
                "Exact25_count",
                "partition_pairwise_disjoint",
                "partition_exhaustive",
                "W_connected",
                "L_connected_or_empty",
                "S_connected",
                "reactive_CAV_in_W",
                "cross_role_boundary_count",
                "cross_role_boundary",
                "W_count",
                "L_count",
                "S_count",
            )
        },
        "published_DIRECT_runtime_validation": runtime,
        "current_census_boundary": census,
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
            }
            for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task": False,
        "direct_profile_applicable_task_ids": [0, 3, 4],
        "task_applicability": [
            {
                "task_id": task_id,
                "semantic_long_name": semantic,
                "display_alias": alias,
                "structurally_applicable": applicable,
                "reason": reason,
            }
            for task_id, semantic, alias, applicable, reason in DIRECT_APPLICABILITY
        ],
        "task_applicability_determined": True,
        "task_applicability_is_structural_metadata_only": True,
        "task_label_authority": False,
        "event_task_label_rows_materialized": False,
        "mask_tensor_targets_created": False,
        "training_mask_targets_available_now": False,
    }


def _pre_boundary() -> dict[str, object]:
    return {
        "candidate_PRE_free_source_graph_count_per_event": 1,
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
    }


def _post_boundary() -> dict[str, object]:
    return {
        "Exact4_observed_POST_geometry": True,
        "explicit_covalent_evidence": True,
        "distance_only": False,
        "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "human_training_use_disposition": "INCLUDE",
        "training_use_human_authoritative": True,
        "future_training_admission_candidate": True,
        "future_training_admission_candidate_semantics": FUTURE_STATUS,
        "formal_training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed": False,
        "split_assignment_created": False,
        "task_label_authority": False,
        "event_task_label_rows_materialized": False,
        "mask_tensor_targets_created": False,
        "training_mask_targets_available_now": False,
        "parameter_update_authorization": False,
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
        "STEP12D_STATUS": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    events = []
    for event in bound["events"]:  # type: ignore[assignment]
        events.append(
            {
                **event,
                "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
                "human_review_completed": True,
                "human_task_relevance_decision": "IN_DOMAIN",
                "human_chemistry_decision": "POSITIVE",
                "protein_reactive_atom": "SG",
                "ligand_reactive_atom": "CAV",
                "explicit_covalent_evidence": True,
                "distance_only_inference": False,
                "formal_sample_reactive_pair_authority": True,
                "formal_training_admitted": False,
                "ready_for_training": False,
            }
        )
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
        "network_required": False,
        "sample_identity": {
            "ligand": "NWJ",
            "PDB": "4CM5",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "authority_scope": EXPECTED_SCOPE,
            "event_count": 4,
            "scaleup_ranks": list(EXPECTED_RANKS),
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
        },
        "formal_human_authority": {
            "approved": True,
            "unsigned": False,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "human_authority_created": True,
            "human_decision_created": True,
            "human_review_completed": True,
            "formal_authority_created": True,
            "formal_decision_created": True,
        },
        "events": events,
        "chemistry_authority": {
            "D1": "POSITIVE",
            "sample_conclusion": "stable Cys168 thioester linkage",
            "initial_thioacetal_then_oxidation": (
                "AUTHOR_PROPOSED_PRESUMED_MECHANISM_ONLY"
            ),
            "asserted_as_proven_mechanism": False,
            "scope": EXPECTED_SCOPE,
        },
        "domain_relevance_authority": {
            "D2": "IN_DOMAIN",
            "reason": (
                "target-directed small-molecule TbPTR1 inhibitor designed for "
                "covalent capture of native Cys168"
            ),
            "designed_for_covalent_capture_of": "native Cys168",
            "TbPTR1_Ki_app_micromolar": 0.2,
            "T_b_brucei_IC50_micromolar": 7.75,
            "scope": EXPECTED_SCOPE,
        },
        "reactive_pair_authority": {
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CAV",
            "pair_authority_scope": EXPECTED_SCOPE,
            "sample_level_authoritative": True,
            "reusable_pair_authority": False,
            "ligand_wide_authority": False,
            "cross_structure_generalization": False,
        },
        "selected_role_partition": {
            "selected_role_candidate": SELECTED_CANDIDATE,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "warhead_atom_ids": list(WARHEAD_ATOMS),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(SCAFFOLD_ATOMS),
            "counts": {"warhead": 2, "linker": 0, "scaffold": 23, "Exact": 25},
            "minimal_seed_atom_ids": list(MINIMAL_SEED),
            "primary_anchor": PRIMARY_ANCHOR,
            "boundary": BOUNDARY,
            "sample_level_authoritative": True,
            "authority_scope": EXPECTED_SCOPE,
            "reusable_role_authority": False,
            "published_runtime_validation": bound[
                "published_DIRECT_runtime_validation"
            ],
        },
        "retained_nonselected_alternative": {
            "candidate_id": NONSELECTED_CANDIDATE,
            "role_profile": "STRICT_LINKER_PRESENT_V1",
            "runtime_valid_nonselected_alternative": True,
            "selected": False,
            "authoritative": False,
            "warhead_atom_ids": list(CANDIDATE_B_WARHEAD),
            "linker_atom_ids": list(CANDIDATE_B_LINKER),
            "scaffold_atom_ids": list(CANDIDATE_B_SCAFFOLD),
            "event_labels_created": False,
        },
        "structural_validation": bound["graph_structural_proof"],
        "canonical_task_contract": _task_contract(),
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(),
        "training_boundary": _training_boundary(),
        "current_census_boundary": bound["current_census_boundary"],
        "authority_boundary": {
            "projection_of_frozen_formal_human_authority": True,
            "new_human_authority_created_by_ingestion": False,
            "authority_source": AUTHORITY_SOURCE,
            "reusable_chemistry_authority": False,
            "reusable_pair_authority": False,
            "reusable_role_authority": False,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
            "formal_training_admitted": False,
            "training_materialization_allowed": False,
            "reconciliation_performed": False,
            "census_refresh_performed": False,
            "queue_refresh_performed": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
    }


MATRIX_HEADER = (
    "canonical_event_id",
    "scaleup_rank",
    "PDB",
    "review_unit_id",
    "model_number",
    "protein_chain_or_asym",
    "cys_residue_id",
    "ligand_component_id",
    "ligand_chain_or_asym",
    "selected_connection_id",
    "POST_distance_angstrom",
    "reported_POST_distance_angstrom",
    "human_review_completed",
    "human_task_relevance_decision",
    "human_chemistry_decision",
    "protein_reactive_atom",
    "ligand_reactive_atom",
    "explicit_covalent_evidence",
    "distance_only_inference",
    "pair_authority_scope",
    "reusable_pair_authority",
    "ligand_wide_authority",
    "cross_structure_generalization",
    "role_profile",
    "selected_role_candidate",
    "warhead_atom_ids_json",
    "linker_atom_ids_json",
    "scaffold_atom_ids_json",
    "minimal_seed_atom_ids_json",
    "primary_anchor",
    "boundary_json",
    "partition_pairwise_disjoint",
    "partition_exhaustive",
    "warhead_connected",
    "linker_connected_or_empty",
    "scaffold_connected",
    "reactive_CAV_in_W",
    "reusable_role_authority",
    "canonical_task_count",
    "B3_present",
    "sixth_task",
    "canonical_task_applicability_json",
    "direct_profile_applicable_task_ids_json",
    "task_applicability_determined",
    "task_label_authority",
    "event_task_label_rows_materialized",
    "mask_tensor_targets_created",
    "training_mask_targets_available_now",
    "human_training_use_disposition",
    "training_use_human_authoritative",
    "future_training_admission_candidate",
    "future_training_admission_candidate_semantics",
    "candidate_PRE_free_source_graph_count_per_event",
    "source_mapping_count_per_event",
    "PRE_source_mapping_status",
    "final_PRE_reaction_status",
    "PRE_authority",
    "POST_to_PRE_copy",
    "PRE_zero_fill",
    "PRE_coordinates_invented",
    "PRE_topology_invented",
    "leaving_group_invented",
    "reagent_invented",
    "reaction_edit_invented",
    "Exact4_observed_POST_geometry",
    "POST_geometry_training_authority",
    "POST_geometry_training_target_created",
    "formal_training_admitted",
    "training_admission_created",
    "training_materialization_allowed",
    "parameter_update_authorization",
    "FEATURE_SEMANTICS_AUDIT_PERFORMED",
    "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING",
    "ready_for_training",
    "TRAINING_STARTED",
    "projection_of_frozen_formal_human_authority",
    "new_human_authority_created_by_ingestion",
)


def _matrix_rows(
    snapshot: Mapping[str, Any], proof: Mapping[str, object]
) -> list[dict[str, object]]:
    expected_proof = {
        "Exact25_count": 25,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "W_connected": True,
        "L_connected_or_empty": True,
        "S_connected": True,
        "reactive_CAV_in_W": True,
        "cross_role_boundary_count": 1,
        "cross_role_boundary": BOUNDARY,
        "W_count": 2,
        "L_count": 0,
        "S_count": 23,
    }
    if dict(proof) != expected_proof:
        _fail("MATRIX_STRUCTURAL_CLAIMS_NOT_SOURCE_VERIFIED")
    applicability = snapshot["canonical_task_contract"]["task_applicability"]
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        row: dict[str, object] = {
            "canonical_event_id": event["canonical_event_id"],
            "scaleup_rank": event["scaleup_rank"],
            "PDB": "4CM5",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "model_number": 1,
            "protein_chain_or_asym": event["protein_chain_or_asym"],
            "cys_residue_id": "CYS:168-",
            "ligand_component_id": "NWJ",
            "ligand_chain_or_asym": event["ligand_chain_or_asym"],
            "selected_connection_id": event["selected_connection_id"],
            "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
            "reported_POST_distance_angstrom": event[
                "reported_POST_distance_frozen_lexeme"
            ],
            "human_review_completed": "true",
            "human_task_relevance_decision": "IN_DOMAIN",
            "human_chemistry_decision": "POSITIVE",
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CAV",
            "explicit_covalent_evidence": "true",
            "distance_only_inference": "false",
            "pair_authority_scope": EXPECTED_SCOPE,
            "reusable_pair_authority": "false",
            "ligand_wide_authority": "false",
            "cross_structure_generalization": "false",
            "role_profile": EXPECTED_ROLE_PROFILE,
            "selected_role_candidate": SELECTED_CANDIDATE,
            "warhead_atom_ids_json": _json_cell(list(WARHEAD_ATOMS)),
            "linker_atom_ids_json": "[]",
            "scaffold_atom_ids_json": _json_cell(list(SCAFFOLD_ATOMS)),
            "minimal_seed_atom_ids_json": _json_cell(list(MINIMAL_SEED)),
            "primary_anchor": PRIMARY_ANCHOR,
            "boundary_json": _json_cell(BOUNDARY),
            "partition_pairwise_disjoint": "true",
            "partition_exhaustive": "true",
            "warhead_connected": "true",
            "linker_connected_or_empty": "true",
            "scaffold_connected": "true",
            "reactive_CAV_in_W": "true",
            "reusable_role_authority": "false",
            "canonical_task_count": 5,
            "B3_present": "true",
            "sixth_task": "false",
            "canonical_task_applicability_json": _json_cell(applicability),
            "direct_profile_applicable_task_ids_json": "[0,3,4]",
            "task_applicability_determined": "true",
            "task_label_authority": "false",
            "event_task_label_rows_materialized": "false",
            "mask_tensor_targets_created": "false",
            "training_mask_targets_available_now": "false",
            "human_training_use_disposition": "INCLUDE",
            "training_use_human_authoritative": "true",
            "future_training_admission_candidate": "true",
            "future_training_admission_candidate_semantics": FUTURE_STATUS,
            "candidate_PRE_free_source_graph_count_per_event": 1,
            "source_mapping_count_per_event": 0,
            "PRE_source_mapping_status": PRE_MAPPING_STATUS,
            "final_PRE_reaction_status": PRE_STATUS,
            "PRE_authority": "false",
            "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false",
            "PRE_coordinates_invented": "false",
            "PRE_topology_invented": "false",
            "leaving_group_invented": "false",
            "reagent_invented": "false",
            "reaction_edit_invented": "false",
            "Exact4_observed_POST_geometry": "true",
            "POST_geometry_training_authority": "false",
            "POST_geometry_training_target_created": "false",
            "formal_training_admitted": "false",
            "training_admission_created": "false",
            "training_materialization_allowed": "false",
            "parameter_update_authorization": "false",
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": "false",
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": "true",
            "ready_for_training": "false",
            "TRAINING_STARTED": "false",
            "projection_of_frozen_formal_human_authority": "true",
            "new_human_authority_created_by_ingestion": "false",
        }
        if set(row) != set(MATRIX_HEADER):
            _fail("MATRIX_ROW_HEADER_MISMATCH")
        rows.append(row)
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "review_unit": "NWJ",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "event_count": 4,
        "selected_role_candidate": SELECTED_CANDIDATE,
        "selected_role_profile": EXPECTED_ROLE_PROFILE,
        "applicable_task_ids": [0, 3, 4],
        "human_training_use_disposition": "INCLUDE",
        "training_use_human_authoritative": True,
        "future_training_admission_candidate": True,
        "formal_training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed": False,
        "ready_for_training": False,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task": False,
        "W_count": 2,
        "L_count": 0,
        "S_count": 23,
        "direct_boundary": "CAX-CAV/SING",
        "minimal_seed_atom_ids": list(MINIMAL_SEED),
        "primary_anchor": PRIMARY_ANCHOR,
        "PRE_source_mapping_status": PRE_MAPPING_STATUS,
        "final_PRE_reaction_status": PRE_STATUS,
        "POST_observed_geometry_event_count": 4,
        "POST_geometry_training_authority": False,
        "task_label_authority": False,
        "event_task_label_rows_materialized": False,
        "mask_tensor_targets_created": False,
        "training_mask_targets_available_now": False,
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
        "reconciliation_performed": False,
        "census_refresh_performed": False,
        "queue_refresh_performed": False,
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
    }


def _candidate_source_records(repo_root: Path) -> list[dict[str, object]]:
    records = []
    for relative in (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE):
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise NWJIngestionSafetyError(
                "COVAPIE_NWJ_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
                + relative.as_posix()
            ) from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        ):
            _fail("CANDIDATE_SOURCE_CLASS_INVALID:" + relative.as_posix())
        records.append(
            {
                "path": relative.as_posix(),
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
    output_bindings = []
    for name, payload in (
        (SNAPSHOT, snapshot_bytes),
        (MATRIX, matrix_bytes),
        (SUMMARY, summary_bytes),
    ):
        output_bindings.append(
            {
                "path": (OUTPUT_ROOT_RELATIVE / name).as_posix(),
                "byte_count": len(payload),
                "SHA256": _sha256(payload),
            }
        )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "DETERMINISTIC_SOURCE_DERIVED_NWJ_INGESTION_MANIFEST",
        "candidate_publication_file_count": 7,
        "candidate_publication_paths": [
            path.as_posix() for path in CANDIDATE_PUBLICATION_PATHS
        ],
        "output_artifact_count": 4,
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "candidate_source_bindings": _candidate_source_records(repo_root),
        "output_artifact_bindings_excluding_manifest_self": output_bindings,
        "active_source_binding_count": len(ACTIVE_BINDINGS),
        "active_source_bindings": [
            _binding_record(binding) for binding in ACTIVE_BINDINGS
        ],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_executed_by_production": False,
        "formal_validator_subprocessed_by_production": False,
        "formal_semantics_independently_validated": True,
        "published_DIRECT_runtime_validation": bound[
            "published_DIRECT_runtime_validation"
        ],
        "current_census_boundary": bound["current_census_boundary"],
        "canonical_task_contract": _task_contract(),
        "determinism": {
            "canonical_JSON": True,
            "LF_only": True,
            "timestamps": False,
            "hostname": False,
            "pid": False,
            "absolute_machine_paths": False,
        },
        "manifest_self_SHA256_recorded": False,
        "MANIFEST_SELF_SHA256_PROHIBITED": True,
        "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
        "operation_boundary": {
            "reconciliation_performed": False,
            "census_refresh_performed": False,
            "queue_refresh_performed": False,
            "dataset_materialization_performed": False,
            "tensor_materialization_performed": False,
            "training_performed": False,
            "commit_performed": False,
            "push_performed": False,
        },
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
        "READY_FOR_EXTERNAL_REVIEW": True,
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
    }


def _build_raw(
    repo_root: Path, overrides: Mapping[Path, Path] | None = None
) -> dict[str, bytes]:
    bound = load_frozen_formal_decision_v1(
        repo_root, repository_path_overrides=overrides
    )
    snapshot_bytes = _json_bytes(_snapshot(bound))
    matrix_bytes = _csv_bytes(
        MATRIX_HEADER,
        _matrix_rows(
            _strict_json(snapshot_bytes, "BUILT_SNAPSHOT"),
            bound["graph_structural_proof"],  # type: ignore[arg-type]
        ),
    )
    summary_bytes = _json_bytes(_summary())
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


def _reject_dynamic_metadata(value: object, path: str = "root") -> None:
    if type(value) is dict:
        for key, child in value.items():
            if key.lower() in {
                "timestamp",
                "hostname",
                "pid",
                "absolute_path",
                "self_sha256",
            } and child is not False:
                _fail("MANIFEST_DYNAMIC_OR_SELF_METADATA:" + path + "." + key)
            _reject_dynamic_metadata(child, path + "." + key)
    elif type(value) is list:
        for index, child in enumerate(value):
            _reject_dynamic_metadata(child, f"{path}[{index}]")
    elif type(value) is str and value.startswith("/"):
        _fail("MANIFEST_ABSOLUTE_PATH_VALUE:" + path)


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
    expected = _build_raw(
        Path(repo_root).resolve(), repository_path_overrides
    )
    for name in OUTPUT_FILENAMES:
        if artifacts[name] != expected[name]:
            _fail("ARTIFACT_PROJECTION_DRIFT:" + name)
        if (
            not artifacts[name].endswith(b"\n")
            or b"\r" in artifacts[name]
            or b"\x00" in artifacts[name]
        ):
            _fail("ARTIFACT_TEXT_HYGIENE_INVALID:" + name)
    snapshot = _strict_json(artifacts[SNAPSHOT], "SNAPSHOT")
    matrix_rows = _parse_csv(artifacts[MATRIX], "MATRIX")
    summary = _strict_json(artifacts[SUMMARY], "SUMMARY")
    manifest = _strict_json(artifacts[MANIFEST], "MANIFEST")
    if len(matrix_rows) != 4 or tuple(matrix_rows[0]) != MATRIX_HEADER:
        _fail("MATRIX_EXACT4_OR_HEADER_DRIFT")
    if (
        snapshot["canonical_task_contract"]["B3_present"] is not True
        or snapshot["canonical_task_contract"]["sixth_task"] is not False
        or snapshot["canonical_task_contract"][
            "direct_profile_applicable_task_ids"
        ]
        != [0, 3, 4]
    ):
        _fail("EXACT5_CONTRACT_DRIFT")
    if (
        summary.get("READY_FOR_TRAINING") is not False
        or manifest.get("READY_FOR_EXTERNAL_REVIEW") is not True
    ):
        _fail("READINESS_BOUNDARY_DRIFT")
    _reject_dynamic_metadata(manifest)
    return {
        "status": "PASS",
        "event_count": 4,
        "matrix_column_count": len(MATRIX_HEADER),
        "output_artifact_count": 4,
        "READY_FOR_EXTERNAL_REVIEW": True,
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
    descriptor, temporary = tempfile.mkstemp(prefix=".covapie_nwj_", dir=path.parent)
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
    if target.exists() and {
        path.name for path in target.iterdir()
    } - set(OUTPUT_FILENAMES):
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
