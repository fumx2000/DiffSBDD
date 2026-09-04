"""Project frozen 4LH Exact4 human authority into metadata-only artifacts.

The formal JSON is parsed and independently validated.  Its frozen validator
is provenance identity only and is never imported, executed, or subprocessed.
This additive stage creates availability metadata only: it does not reconcile,
refresh the census or queue, materialize labels/tensors, or train a model.
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
    "FourLHIngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = "covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_4lh_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_4lh_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_4lh_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_4lh_completed_decision_ingestion_manifest_v1"
BASELINE_COMMIT = "71c73243447aa321f4cbe84ef2b929b8d2ddffb3"

SOURCE_RELATIVE = Path("src/covalent_ext/covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1.py")
CHECKER_RELATIVE = Path("scripts/check_covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1.py")
TEST_RELATIVE = Path("tests/test_covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1.py")
OUTPUT_ROOT_RELATIVE = Path("data/derived/covalent_small/covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1")
SNAPSHOT = "covapie_4lh_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_4lh_event_task_label_availability_v1.csv"
SUMMARY = "covapie_4lh_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_4lh_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE, *OUTPUT_RELATIVE_PATHS)

STATE_ROOT = Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/4LH_COVAPIE_BULK_REVIEW_UNIT_C4EFE734A5B0CF57")
FORMAL_DECISION_RELATIVE = STATE_ROOT / "formal-human-decision-v1/4lh_formal_human_decision_v1.json"
FORMAL_VALIDATOR_RELATIVE = STATE_ROOT / "formal-human-decision-v1/validate_4lh_formal_human_decision_v1.py"
EVENT_EVIDENCE_RELATIVE = STATE_ROOT / "review-preparation-v1/4lh_exact4_event_evidence_v1.csv"
GRAPH_EVIDENCE_RELATIVE = STATE_ROOT / "review-preparation-v1/4lh_graph_and_review_evidence_v1.json"
CCD_RELATIVE = Path("covapie-state/bulk-model-usable-auto-admission-scaleup-v1/ranks-0501-1000/attempt-001/cache/rcsb/ccd/4LH.cif")
SOURCE_BINDING_POLICY_RELATIVE = Path("src/covalent_ext/covapie_source_binding_policy_v2.py")
DIRECT_RUNTIME_OWNER_RELATIVE = Path("src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py")
CANONICAL_TASK_OWNER_RELATIVE = Path("src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py")
CENSUS_OWNER_RELATIVE = Path("src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_0d8_v1.py")
CENSUS_ROOT_RELATIVE = Path("data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_0d8_v1")
CENSUS_MATRIX_RELATIVE = CENSUS_ROOT_RELATIVE / "covapie_cumulative1000_current_global_readiness_census_with_0d8_v1.csv"
CENSUS_SUMMARY_RELATIVE = CENSUS_ROOT_RELATIVE / "covapie_cumulative1000_current_global_readiness_summary_with_0d8_v1.json"
CENSUS_MANIFEST_RELATIVE = CENSUS_ROOT_RELATIVE / "covapie_cumulative1000_current_global_readiness_manifest_with_0d8_v1.json"

FORMAL_DECISION_SCHEMA = "covapie_4lh_exact4_formal_human_decision_v1"
FORMAL_SEMANTIC_CANONICAL_SHA256 = "20e60e66a31c429e38faabeddd045b44ade527ddaa20f9429486042e23c4fe8f"
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_C4EFE734A5B0CF57"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
AUTHORITY_SOURCE = "FORMAL_4LH_HUMAN_DECISION"
PAIR_AUTHORITY_SCOPE = "CURRENT_4LH_4Z16_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
ROLE_AUTHORITY_SCOPE = "CURRENT_4LH_EXACT4_SAMPLE_REVIEW_UNIT_ONLY"
FUTURE_STATUS = "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS"
PRE_STATUS = "PRE_REACTION_UNRESOLVED"

EXPECTED_D6 = (
    "Confirm the current 4LH/4Z16 Exact4 as task-relevant, chemistry-positive "
    "medicinal covalent inhibitor evidence for the present CovaPIE target-directed "
    "small-molecule domain. The four explicit model-1 CYS909-SG ↔ 4LH-CAP covale "
    "connections and reproduced POST distances support the sample-specific observed "
    "pair; this decision creates no reusable CAP regiochemistry, reaction-family, "
    "warhead-rule, warhead-type, or cross-structure authority. Select DIRECT candidate "
    "0 as the sample-level role partition: W=[CAP,CAQ,CBE,OAE,NBA], L=[], "
    "S=[C2,C4,C5,C6,CAA,CAB,CAH,CAI,CAJ,CAK,CAL,CAN,CAO,CAR,CAS,CAT,CAU,CAV,"
    "CBF,CBH,CBI,CBK,CBL,CL5,N1,N3,NAZ,NBB,NBO,NBP,OBC], with the CBH-NBA "
    "scaffold/warhead boundary and minimal seed [CAJ,CAN,CBH], primary anchor CBH. "
    "Candidate B is runtime-valid but is not selected because it splits the acrylamide "
    "amide C-N bond between warhead and linker. The selected DIRECT profile has "
    "sample-applicable canonical tasks [0,3,4]: warhead_only, scaffold_only, and "
    "scaffold_plus_linker_plus_warhead; B3 is present and no sixth task exists. PRE "
    "remains PRE_SOURCE_GRAPH_MAPPING_AMBIGUOUS / PRE_REACTION_UNRESOLVED; do not copy "
    "POST to PRE, zero-fill PRE, infer leaving groups, reagents, reaction edits, PRE "
    "topology, or PRE coordinates. Set human training use to INCLUDE as a disposition "
    "only. This does not create formal training admission, tensor or mask targets, "
    "training materialization permission, current-runtime usability, parameter-update "
    "authority, or training readiness."
)
EXPECTED_D6_BYTE_COUNT = 1501
EXPECTED_D6_SHA256 = "afd811a97e38df26020185c8a8500cca58584e5b70b7e974804fcc41b0ed1f2c"

# event id, rank, protein asym, ligand asym, connection, exact lexeme, reported lexeme
EXPECTED_EVENTS = (
    ("COVAPIE_CYS_SG_EVENT_V1:4Z16:A:CYS:909-:SG:E:4LH:CAP", 950, "A", "E", "covale1", "1.831618", "1.832"),
    ("COVAPIE_CYS_SG_EVENT_V1:4Z16:B:CYS:909-:SG:F:4LH:CAP", 951, "B", "F", "covale5", "1.831660", "1.832"),
    ("COVAPIE_CYS_SG_EVENT_V1:4Z16:C:CYS:909-:SG:G:4LH:CAP", 952, "C", "G", "covale9", "1.825137", "1.825"),
    ("COVAPIE_CYS_SG_EVENT_V1:4Z16:D:CYS:909-:SG:H:4LH:CAP", 953, "D", "H", "covale13", "1.834640", "1.835"),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)
WARHEAD_ATOMS = ("CAP", "CAQ", "CBE", "OAE", "NBA")
LINKER_ATOMS: tuple[str, ...] = ()
SCAFFOLD_ATOMS = (
    "C2", "C4", "C5", "C6", "CAA", "CAB", "CAH", "CAI", "CAJ", "CAK", "CAL", "CAN", "CAO",
    "CAR", "CAS", "CAT", "CAU", "CAV", "CBF", "CBH", "CBI", "CBK", "CBL", "CL5", "N1", "N3",
    "NAZ", "NBB", "NBO", "NBP", "OBC",
)
HEAVY_ATOMS = tuple(sorted((*WARHEAD_ATOMS, *SCAFFOLD_ATOMS)))
MINIMAL_SEED = ("CAJ", "CAN", "CBH")
PRIMARY_ANCHOR = "CBH"
BOUNDARY = {"scaffold_atom_id": "CBH", "warhead_atom_id": "NBA", "bond_order": "SING"}

CANONICAL_TASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (4, "scaffold_plus_linker_plus_warhead", "C", ("scaffold", "linker", "warhead"), ("minimal_seed",)),
)
DIRECT_APPLICABILITY = (
    (0, "warhead_only", "A", True, "generate_W_condition_on_S"),
    (1, "linker_plus_warhead", "B", False, "not_applicable_empty_linker_redundant_with_A"),
    (2, "scaffold_plus_warhead", "B2", False, "not_applicable_empty_non_C_fixed_context"),
    (3, "scaffold_only", "B3", True, "generate_S_condition_on_W"),
    (4, "scaffold_plus_linker_plus_warhead", "C", True, "generate_whole_ligand_preserve_Task_C_seed_semantics"),
)

# path, namespace, bytes, SHA256, executable, role, validation method
_Binding = tuple[Path, str, int, str, bool, str, str]
FORMAL_BINDINGS: tuple[_Binding, ...] = (
    (FORMAL_DECISION_RELATIVE, "project_parent_relative", 18475, "bbcf803ec3dbb13267cb580185ad6ed209c4eff2f373361511c6b641ffede203", False, "4LH_FROZEN_FORMAL_HUMAN_DECISION", "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY"),
    (FORMAL_VALIDATOR_RELATIVE, "project_parent_relative", 38299, "18a35d13cb1e5a11d5a0e25137d4b59dfaebc0b37056c0d876016d3bcb7901dc", False, "4LH_FROZEN_FORMAL_VALIDATOR", "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"),
)
SUPPORTING_BINDINGS: tuple[_Binding, ...] = (
    (EVENT_EVIDENCE_RELATIVE, "project_parent_relative", 8512, "ee8e772c4a79dc3028c2c6874ae47e24f6190f2a05f659a47107e31ad268c72e", False, "4LH_EXACT4_EVENT_EVIDENCE", "PARSED_CSV_SUPPORTING_EVIDENCE"),
    (GRAPH_EVIDENCE_RELATIVE, "project_parent_relative", 28785, "e2c89e3846b5961df2a6bf1bb3c6ac89943a0bbb59e33832da637248fc9c7e2a", False, "4LH_GRAPH_AND_REVIEW_EVIDENCE", "PARSED_JSON_STRUCTURAL_VALIDATION"),
    (CCD_RELATIVE, "project_parent_relative", 13501, "cc7338eb2c5da88cf2147b3ce815990eb1e754bdceaa1f2c3034df64f81060bf", False, "4LH_FROZEN_CCD", "CONTENT_IDENTITY_SUPPORTING_GRAPH_PROVENANCE"),
)
POLICY_BINDING: _Binding = (SOURCE_BINDING_POLICY_RELATIVE, "repository_relative", 3704, "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee", False, "PUBLISHED_SOURCE_BINDING_POLICY_V2", "IMPORTED_CONTENT_IDENTITY_AND_SECURITY_POLICY")
SEMANTIC_OWNER_BINDINGS: tuple[_Binding, ...] = (
    (DIRECT_RUNTIME_OWNER_RELATIVE, "repository_relative", 37255, "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535", False, "PUBLISHED_DIRECT_ROLE_RUNTIME_OWNER", "IMPORTED_AND_CALLED_FOR_PARTITION_PROFILE_BOUNDARY_SEED_PAYLOAD_AND_TASKS"),
    (CANONICAL_TASK_OWNER_RELATIVE, "repository_relative", 67274, "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b", False, "PUBLISHED_CANONICAL_EXACT5_OWNER", "PARSED_AST_LITERAL_CONTRACT_ONLY"),
)
CENSUS_BINDINGS: tuple[_Binding, ...] = (
    (CENSUS_OWNER_RELATIVE, "repository_relative", 70158, "5529b963bd2792eb66bd9073a67fd8c0c7c08f1bb29a64faf5459e4c52b2f71c", False, "CURRENT_WITH_0D8_CENSUS_OWNER", "CONTENT_IDENTITY_READ_ONLY"),
    (CENSUS_MATRIX_RELATIVE, "repository_relative", 547666, "dd7cb0e923dcfdfe464b9ffc4cf0b17c569fa8c3ca33ac23fbda7103dbe9d273", False, "CURRENT_WITH_0D8_CENSUS_MATRIX", "PARSED_CSV_PREFORMAL_STATE_READ_ONLY"),
    (CENSUS_SUMMARY_RELATIVE, "repository_relative", 20778, "479528564feb0ab67685408aab2e404162d48474331492688d986fae0bf2a4bc", False, "CURRENT_WITH_0D8_CENSUS_SUMMARY", "PARSED_JSON_PENDING_RANK_READ_ONLY"),
    (CENSUS_MANIFEST_RELATIVE, "repository_relative", 73718, "36910e9779603b5545953ee503ed8573dbc1bb55926d095e0d5d4f84b9075ca6", False, "CURRENT_WITH_0D8_CENSUS_MANIFEST", "PARSED_JSON_CONTENT_IDENTITY_READ_ONLY"),
)
ACTIVE_BINDINGS = (*FORMAL_BINDINGS, *SUPPORTING_BINDINGS, POLICY_BINDING, *SEMANTIC_OWNER_BINDINGS, *CENSUS_BINDINGS)


class FourLHIngestionSafetyError(ValueError):
    """Raised when the frozen 4LH projection contract cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise FourLHIngestionSafetyError("COVAPIE_4LH_INGESTION_V1_ERROR:" + reason)


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
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("JSON_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise FourLHIngestionSafetyError("COVAPIE_4LH_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label) from error

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
        raise FourLHIngestionSafetyError("COVAPIE_4LH_INGESTION_V1_ERROR:JSON_PARSE_FAILED:" + label) from error
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _parse_csv(payload: bytes, label: str) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise FourLHIngestionSafetyError("COVAPIE_4LH_INGESTION_V1_ERROR:CSV_UTF8_INVALID:" + label) from error
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
        "path": path.as_posix(), "namespace": namespace, "byte_count": byte_count,
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
        raise FourLHIngestionSafetyError("COVAPIE_4LH_INGESTION_V1_ERROR:SOURCE_BINDING_FAILED:" + relative.as_posix()) from error


def _verify_bindings(repo_root: Path, bindings: Sequence[_Binding], overrides: Mapping[Path, Path]) -> dict[Path, bytes]:
    return {binding[0]: _verify_binding(repo_root, binding, overrides) for binding in bindings}


def _literal_assignments(payload: bytes, names: Sequence[str], label: str) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8"), filename=label)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise FourLHIngestionSafetyError("COVAPIE_4LH_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label) from error
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
                    raise FourLHIngestionSafetyError("COVAPIE_4LH_INGESTION_V1_ERROR:SEMANTIC_OWNER_LITERAL_INVALID:" + target.id) from error
    if set(values) != set(names):
        _fail("SEMANTIC_OWNER_LITERAL_MISSING:" + label)
    return values


def _semantic_digest(formal: Mapping[str, Any]) -> str:
    clone = copy.deepcopy(dict(formal))
    digest = clone.pop("formal_semantic_canonical_sha256", None)
    if type(digest) is not str:
        _fail("FORMAL_SEMANTIC_DIGEST_FIELD_INVALID")
    return _sha256(_canonical_json(clone))


def _validate_formal(formal: Mapping[str, Any]) -> None:
    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    for key, expected in (
        ("record_role", "FORMAL_COMPLETED_EXTERNAL_HUMAN_AUTHORIZED_SAMPLE_LEVEL_DECISION"),
        ("approved", True), ("unsigned", False), ("decision_finalized", True),
        ("human_review_completed", True), ("human_decision_created", True),
        ("formal_authority_created", True),
    ):
        _expect(formal.get(key), expected, "FORMAL_LIFECYCLE_DRIFT:" + key)
    _expect(formal.get("formal_semantic_canonical_sha256"), FORMAL_SEMANTIC_CANONICAL_SHA256, "FORMAL_SEMANTIC_DIGEST_LITERAL_DRIFT")
    if _semantic_digest(formal) != FORMAL_SEMANTIC_CANONICAL_SHA256:
        _fail("FORMAL_SEMANTIC_DIGEST_RECOMPUTE_FAILED")

    d6 = formal.get("human_approved_context")
    if type(d6) is not dict:
        _fail("FORMAL_D6_MISSING")
    for key, expected in (
        ("D6_context_verbatim", EXPECTED_D6), ("D6_utf8_bytes", EXPECTED_D6_BYTE_COUNT),
        ("D6_sha256", EXPECTED_D6_SHA256), ("human_accepted", True),
        ("human_authorized", True), ("human_reviewed", True), ("human_authored", False),
        ("assistant_draft_creates_authority", False),
    ):
        _expect(d6.get(key), expected, "FORMAL_D6_DRIFT:" + key)
    if len(EXPECTED_D6.encode("utf-8")) != EXPECTED_D6_BYTE_COUNT or _sha256(EXPECTED_D6.encode("utf-8")) != EXPECTED_D6_SHA256:
        _fail("INTERNAL_D6_IDENTITY_INVALID")

    decisions = formal.get("formal_human_decision")
    if type(decisions) is not dict:
        _fail("FORMAL_DECISIONS_MISSING")
    expected_decisions = {
        "D1_task_relevance": ("value", "RELEVANT"),
        "D2_chemistry": ("value", "POSITIVE"),
        "D3_reactive_pair": ("value", "CONFIRM_OBSERVED_PAIR"),
        "D4_role_candidate": ("value", "SELECT_CANDIDATE_0"),
        "D5_training_use": ("value", "INCLUDE"),
    }
    for decision, (field, expected) in expected_decisions.items():
        row = decisions.get(decision)
        if type(row) is not dict:
            _fail("FORMAL_DECISION_MISSING:" + decision)
        _expect(row.get(field), expected, "FORMAL_DECISION_DRIFT:" + decision)
        _expect(row.get("human_authority"), True, "FORMAL_DECISION_NOT_HUMAN:" + decision)
    _expect(decisions["D3_reactive_pair"].get("protein_atom"), "SG", "FORMAL_PAIR_PROTEIN_DRIFT")
    _expect(decisions["D3_reactive_pair"].get("ligand_atom"), "CAP", "FORMAL_PAIR_LIGAND_DRIFT")
    _expect(decisions["D3_reactive_pair"].get("scope"), PAIR_AUTHORITY_SCOPE, "FORMAL_PAIR_SCOPE_DRIFT")
    _expect(decisions["D4_role_candidate"].get("role_profile"), EXPECTED_ROLE_PROFILE, "FORMAL_ROLE_PROFILE_DRIFT")
    _expect(decisions["D5_training_use"].get("formal_training_admitted"), False, "FORMAL_D5_ADMISSION_DRIFT")

    identity = formal.get("identity")
    if type(identity) is not dict:
        _fail("FORMAL_IDENTITY_MISSING")
    expected_identity = {
        "canonical_event_ids": list(EXPECTED_EVENT_IDS), "exact4_event_count": 4,
        "ligand_ccd_code": "4LH", "pdb_id": "4Z16", "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "scope": PAIR_AUTHORITY_SCOPE,
    }
    _expect(identity, expected_identity, "FORMAL_IDENTITY_DRIFT")

    exact4 = formal.get("Exact4")
    if type(exact4) is not dict or type(exact4.get("events")) is not list:
        _fail("FORMAL_EXACT4_INVALID")
    events = exact4["events"]
    _expect(len(events), 4, "FORMAL_EXACT4_COUNT_DRIFT")
    for event, expected in zip(events, EXPECTED_EVENTS):
        required = {
            "canonical_event_id": expected[0], "scaleup_rank": expected[1], "pdb_id": "4Z16",
            "model_number": 1, "connection_id": expected[4], "connection_type": "covale",
            "explicit_covalent_evidence": True, "distance_only_inference": False,
            "formal_sample_reactive_pair_authority": True, "formal_training_admitted": False,
            "POST_training_target_authority": False,
        }
        for key, value in required.items():
            _expect(event.get(key), value, "FORMAL_EXACT4_EVENT_DRIFT:" + key)
        _expect(format(event.get("exact_POST_distance_angstrom"), ".6f"), expected[5], "FORMAL_EXACT_DISTANCE_DRIFT")
        _expect(format(event.get("reported_POST_distance_angstrom"), ".3f"), expected[6], "FORMAL_REPORTED_DISTANCE_DRIFT")
        _expect(event.get("protein_endpoint"), {"atom": "SG", "label_asym_id": expected[2], "residue": "CYS:909-"}, "FORMAL_PROTEIN_ENDPOINT_DRIFT")
        _expect(event.get("ligand_endpoint"), {"atom": "CAP", "component": "4LH", "label_asym_id": expected[3]}, "FORMAL_LIGAND_ENDPOINT_DRIFT")

    role = formal.get("selected_role_partition")
    if type(role) is not dict:
        _fail("FORMAL_ROLE_MISSING")
    expected_role_fields = {
        "W": list(WARHEAD_ATOMS), "L": [], "S": list(SCAFFOLD_ATOMS),
        "counts": {"Exact": 36, "L": 0, "S": 31, "W": 5},
        "direct_scaffold_warhead_boundary": BOUNDARY,
        "minimal_seed_atom_ids": list(MINIMAL_SEED), "primary_anchor_atom_id": PRIMARY_ANCHOR,
        "role_profile": EXPECTED_ROLE_PROFILE, "selected_candidate_index": 0,
        "pairwise_disjoint": True, "exhaustive_over_frozen_heavy_atoms": True,
        "sample_level_human_role_authority": True, "reusable_role_authority": False,
    }
    for key, expected in expected_role_fields.items():
        _expect(role.get(key), expected, "FORMAL_ROLE_DRIFT:" + key)

    tasks = formal.get("canonical_Exact5_task_applicability")
    if type(tasks) is not dict:
        _fail("FORMAL_TASKS_MISSING")
    for key, expected in (
        ("task_count", 5), ("B3_present", True), ("sixth_task", False),
        ("applicable_task_ids", [0, 3, 4]), ("event_task_label_rows_materialized", False),
        ("tensor_masks_materialized", False),
    ):
        _expect(tasks.get(key), expected, "FORMAL_TASK_DRIFT:" + key)
    expected_task_rows = [
        {"task_id": task_id, "semantic_long_name": semantic, "display_alias": alias,
         "applicable": applicable, "not_applicable_reason": None if applicable else reason}
        for task_id, semantic, alias, applicable, reason in DIRECT_APPLICABILITY
    ]
    _expect(tasks.get("tasks"), expected_task_rows, "FORMAL_EXACT5_ROWS_DRIFT")

    pre = formal.get("PRE_boundary")
    if type(pre) is not dict:
        _fail("FORMAL_PRE_MISSING")
    for key, expected in (
        ("per_event_adduct_graph_count", 1), ("per_event_candidate_PRE_graph_count", 1),
        ("per_event_mapping_count", 2), ("PRE_source_mapping_status", PRE_MAPPING_STATUS),
        ("PRE_status", PRE_STATUS), ("PRE_authority", False), ("PRE_topology_created", False),
        ("PRE_geometry_created", False), ("PRE_coordinates_created", False),
        ("POST_to_PRE_copy", False), ("PRE_zero_fill", False), ("leaving_group_inferred", False),
        ("reagent_inferred", False), ("reaction_edit_inferred", False),
    ):
        _expect(pre.get(key), expected, "FORMAL_PRE_DRIFT:" + key)

    post = formal.get("POST_boundary")
    if type(post) is not dict:
        _fail("FORMAL_POST_MISSING")
    for key, expected in (("source_evidence_present", True), ("explicit_event_count", 4), ("distance_reproduced_event_count", 4), ("POST_training_authority", False), ("POST_training_target", False)):
        _expect(post.get(key), expected, "FORMAL_POST_DRIFT:" + key)

    training = formal.get("training_boundary")
    if type(training) is not dict:
        _fail("FORMAL_TRAINING_MISSING")
    required_training = {
        "human_training_use_disposition": "INCLUDE", "human_training_use_authority": True,
        "future_training_admission_candidate": True, "formal_training_admitted": False,
        "training_admission_created": False, "training_materialization_allowed": False,
        "split_assignment_created": False, "tensor_targets_created": False, "mask_targets_created": False,
        "current_runtime_usable": False, "parameter_update_authority": False,
        "training_started": False, "READY_FOR_TRAINING": False,
    }
    for key, expected in required_training.items():
        _expect(training.get(key), expected, "FORMAL_TRAINING_DRIFT:" + key)

    authority = formal.get("authority_boundary")
    if type(authority) is not dict:
        _fail("FORMAL_AUTHORITY_MISSING")
    for key in ("sample_level_task_relevance_authority", "sample_level_chemistry_authority", "sample_level_reactive_pair_authority", "sample_level_canonical_role_authority", "sample_level_role_profile_applicability_authority", "training_use_human_authority"):
        _expect(authority.get(key), True, "FORMAL_REQUIRED_AUTHORITY_FALSE:" + key)
    for key in ("reusable_chemistry_authority", "reusable_pair_authority", "reusable_role_authority", "reaction_family_authority", "warhead_rule_authority", "warhead_type_authority", "formal_training_authority", "training_materialization_authority", "parameter_update_authority"):
        _expect(authority.get(key), False, "FORMAL_FORBIDDEN_AUTHORITY_TRUE:" + key)
    operations = formal.get("operation_boundary")
    if type(operations) is not dict or any(value is not False for value in operations.values()):
        _fail("FORMAL_OPERATION_ALREADY_OCCURRED")


def _validate_event_evidence(payload: bytes) -> dict[str, object]:
    rows = _parse_csv(payload, "4LH_EVENT_EVIDENCE")
    if len(rows) != 4 or tuple(row.get("canonical_event_id") for row in rows) != EXPECTED_EVENT_IDS:
        _fail("EVENT_EVIDENCE_EXACT4_DRIFT")
    for index, (row, expected) in enumerate(zip(rows, EXPECTED_EVENTS)):
        required = {
            "event_index_0based": str(index), "scaleup_rank": str(expected[1]), "raw_priority_rank": "26",
            "current_pending_rank": "1", "review_unit_id": EXPECTED_REVIEW_UNIT_ID, "pdb_id": "4Z16",
            "model_number": "1", "protein_label_asym_id": expected[2], "cys_residue_id": "CYS:909-",
            "protein_reactive_atom": "SG", "ligand_component_id": "4LH", "ligand_label_asym_id": expected[3],
            "ligand_reactive_atom": "CAP", "connection_id": expected[4], "connection_type": "covale",
            "explicit_covalent_evidence": "true", "distance_only_inference": "false",
            "reported_POST_distance_angstrom": expected[6], "exact_POST_distance_angstrom": expected[5],
            "POST_source_evidence_available": "true", "supporting_adduct_graph_count": "1",
            "candidate_PRE_free_source_graph_count": "1", "source_PRE_mapping_count": "2",
            "PRE_source_mapping_status": PRE_MAPPING_STATUS, "final_PRE_reaction_status": PRE_STATUS,
            "PRE_topology_created": "false", "PRE_coordinates_created": "false", "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false", "human_review_completed": "false", "chemistry_disposition": "UNRESOLVED",
            "task_relevance_disposition": "UNRESOLVED", "training_use_disposition": "UNRESOLVED",
            "formal_training_admitted": "false",
        }
        for key, value in required.items():
            if row.get(key) != value:
                _fail("EVENT_EVIDENCE_DRIFT:" + key)
    return {"event_count": 4, "event_ids": list(EXPECTED_EVENT_IDS), "ranks": list(EXPECTED_RANKS), "POST_distances": [row[5] for row in EXPECTED_EVENTS]}


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
    role_sets = {
        "W": set(WARHEAD_ATOMS),
        "L": set(LINKER_ATOMS),
        "S": set(SCAFFOLD_ATOMS),
    }
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
    L_connected_or_empty = not LINKER_ATOMS or _connected(LINKER_ATOMS, bonds)
    S_connected = _connected(SCAFFOLD_ATOMS, bonds)
    reactive_CAP_in_W = "CAP" in role_sets["W"]
    if not W_connected:
        _fail("GRAPH_W_DISCONNECTED")
    if not L_connected_or_empty:
        _fail("GRAPH_L_DISCONNECTED")
    if not S_connected:
        _fail("GRAPH_S_DISCONNECTED")
    if not reactive_CAP_in_W:
        _fail("GRAPH_REACTIVE_CAP_NOT_IN_W")

    role_by_atom = {
        atom_id: role for role, members in role_sets.items() for atom_id in members
    }
    cross_role_bonds: list[tuple[str, str, str]] = []
    for left, right, order in bonds:
        left_role = role_by_atom[left]
        right_role = role_by_atom[right]
        if left_role == right_role:
            continue
        if (left_role, right_role) == ("S", "W"):
            cross_role_bonds.append((left, right, order))
        elif (left_role, right_role) == ("W", "S"):
            cross_role_bonds.append((right, left, order))
        else:
            _fail("GRAPH_UNEXPECTED_CROSS_ROLE_CLASS")
    if cross_role_bonds != [("CBH", "NBA", "SING")]:
        _fail("GRAPH_DIRECT_BOUNDARY_NOT_UNIQUE_EXACT")
    return {
        "Exact36_count": 36,
        "partition_pairwise_disjoint": pairwise_disjoint,
        "partition_exhaustive": exhaustive,
        "W_connected": W_connected,
        "L_connected_or_empty": L_connected_or_empty,
        "S_connected": S_connected,
        "reactive_CAP_in_W": reactive_CAP_in_W,
        "cross_role_boundary_count": len(cross_role_bonds),
        "cross_role_boundary": {
            "scaffold_atom_id": cross_role_bonds[0][0],
            "warhead_atom_id": cross_role_bonds[0][1],
            "bond_order": cross_role_bonds[0][2],
            "scaffold_role": "S",
            "warhead_role": "W",
        },
        "W_count": len(WARHEAD_ATOMS),
        "L_count": len(LINKER_ATOMS),
        "S_count": len(SCAFFOLD_ATOMS),
    }


def _validate_graph_evidence(payload: bytes) -> dict[str, object]:
    document = _strict_json(payload, "4LH_GRAPH_EVIDENCE")
    for key, expected in (("schema_version", "covapie_4lh_graph_and_review_evidence_v1"), ("review_unit_id", EXPECTED_REVIEW_UNIT_ID), ("pdb_id", "4Z16"), ("ligand_component_id", "4LH")):
        _expect(document.get(key), expected, "GRAPH_IDENTITY_DRIFT:" + key)
    graph = document.get("canonical_heavy_atom_graph")
    if type(graph) is not dict:
        _fail("GRAPH_MISSING")
    atoms = graph.get("atom_inventory")
    bonds = graph.get("bond_inventory")
    if type(atoms) is not list or type(bonds) is not list:
        _fail("GRAPH_INVENTORY_INVALID")
    atom_ids = tuple(sorted(row.get("atom_id") for row in atoms if type(row) is dict))
    _expect(atom_ids, HEAVY_ATOMS, "GRAPH_EXACT36_ATOMS_DRIFT")
    _expect(graph.get("heavy_atom_count"), 36, "GRAPH_HEAVY_COUNT_DRIFT")
    _expect(graph.get("heavy_heavy_bond_count"), 39, "GRAPH_BOND_COUNT_DRIFT")
    normalized_bonds = tuple((row["atom_id_1"], row["atom_id_2"], row["bond_order"]) for row in bonds if type(row) is dict)
    if len(normalized_bonds) != 39:
        _fail("GRAPH_BOND_INVENTORY_DRIFT")
    structural_proof = _validate_partition_graph(atom_ids, normalized_bonds)
    pre = document.get("PRE_evidence")
    if type(pre) is not dict or type(pre.get("per_event")) is not list:
        _fail("GRAPH_PRE_INVALID")
    for row in pre["per_event"]:
        if type(row) is not dict:
            _fail("GRAPH_PRE_ROW_INVALID")
        required = {"supporting_adduct_graph_count": 1, "candidate_PRE_free_source_graph_count": 1, "source_PRE_mapping_count": 2, "source_mapping_status": PRE_MAPPING_STATUS, "final_PRE_reaction_status": PRE_STATUS}
        for key, value in required.items():
            _expect(row.get(key), value, "GRAPH_PRE_DRIFT:" + key)
    post = document.get("event_POST_evidence")
    if type(post) is not list or len(post) != 4:
        _fail("GRAPH_POST_COUNT_DRIFT")
    for row, expected in zip(post, EXPECTED_EVENTS):
        if type(row) is not dict:
            _fail("GRAPH_POST_ROW_INVALID")
        _expect(row.get("canonical_event_id"), expected[0], "GRAPH_POST_ID_DRIFT")
        _expect(format(row.get("exact_POST_distance_angstrom"), ".6f"), expected[5], "GRAPH_POST_DISTANCE_DRIFT")
        _expect(row.get("explicit_covalent_evidence"), True, "GRAPH_POST_EXPLICIT_DRIFT")
        _expect(row.get("distance_only_inference"), False, "GRAPH_POST_DISTANCE_ONLY_DRIFT")
    return {
        "atom_rows": atoms,
        "atom_ids": atom_ids,
        "bonds": normalized_bonds,
        "semantic_topology_sha256": graph.get("canonical_graph_sha256"),
        **structural_proof,
    }


def _validate_semantic_owners(payloads: Mapping[Path, bytes]) -> None:
    direct = _literal_assignments(payloads[DIRECT_RUNTIME_OWNER_RELATIVE], ("DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1", "DIRECT_VALID_CANONICAL_TASK_IDS_V1", "DIRECT_PROFILE_TASK_APPLICABILITY_V1"), DIRECT_RUNTIME_OWNER_RELATIVE.as_posix())
    canonical = _literal_assignments(payloads[CANONICAL_TASK_OWNER_RELATIVE], ("EXACT3_ROLES", "CANONICAL_TASKS"), CANONICAL_TASK_OWNER_RELATIVE.as_posix())
    _expect(direct["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"], EXPECTED_ROLE_PROFILE, "DIRECT_PROFILE_OWNER_DRIFT")
    _expect(direct["DIRECT_VALID_CANONICAL_TASK_IDS_V1"], (0, 3, 4), "DIRECT_TASK_IDS_OWNER_DRIFT")
    _expect(direct["DIRECT_PROFILE_TASK_APPLICABILITY_V1"], DIRECT_APPLICABILITY, "DIRECT_APPLICABILITY_OWNER_DRIFT")
    _expect(canonical["EXACT3_ROLES"], ("scaffold", "linker", "warhead"), "EXACT3_OWNER_DRIFT")
    _expect(canonical["CANONICAL_TASKS"], CANONICAL_TASKS, "EXACT5_OWNER_DRIFT")


def _runtime_validation(structural: Mapping[str, object]) -> dict[str, object]:
    runtime = importlib.import_module("covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1")
    role = runtime.validate_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE, retained_heavy_atoms=structural["atom_ids"],
        scaffold_atoms=SCAFFOLD_ATOMS, linker_atoms=LINKER_ATOMS, warhead_atoms=WARHEAD_ATOMS,
        reactive_atom_id="CAP", direct_scaffold_warhead_boundaries=(("CBH", "NBA", "SING"),),
        explicit_graph_bonds=structural["bonds"],
    )
    boundary = role.direct_scaffold_warhead_boundary
    if not (role.valid is True and tuple(role.reasons) == () and role.scaffold_count == 31 and role.linker_count == 0 and role.warhead_count == 5 and boundary is not None and boundary.boundary_valid is True and boundary.scaffold_atom_id == "CBH" and boundary.warhead_atom_id == "NBA" and boundary.bond_order == "SING"):
        _fail("PUBLISHED_DIRECT_ROLE_RUNTIME_FAILED")
    seed = runtime.validate_minimal_seed_for_role_profile_v1(
        role_profile=EXPECTED_ROLE_PROFILE, seed_atoms=MINIMAL_SEED, scaffold_atoms=SCAFFOLD_ATOMS,
        linker_atoms=LINKER_ATOMS, warhead_atoms=WARHEAD_ATOMS, explicit_graph_bonds=structural["bonds"],
        direct_boundary=boundary,
    )
    if seed.valid is not True or tuple(seed.reasons) != () or seed.primary_anchor_atom_id != PRIMARY_ANCHOR:
        _fail("PUBLISHED_DIRECT_SEED_RUNTIME_FAILED")
    if tuple(runtime.valid_canonical_task_ids_for_role_profile_v1(EXPECTED_ROLE_PROFILE)) != (0, 3, 4):
        _fail("PUBLISHED_DIRECT_TASK_RUNTIME_FAILED")

    atom_inventory = [{"atom_id": row["atom_id"], "element": row["element"]} for row in structural["atom_rows"]]  # type: ignore[index]
    bond_inventory = [{"atom_id_1": row[0], "atom_id_2": row[1], "bond_order": row[2]} for row in structural["bonds"]]  # type: ignore[index]
    signature = {
        "canonical_internal_heavy_heavy_bond_graph_with_bond_orders": bond_inventory,
        "canonical_model_bound_ligand_heavy_atom_inventory": atom_inventory,
        "chemistry_review_signature_version": "covapie_recovered7_chemistry_review_signature_v1",
        "explicit_covalent_event": {"component_internal_topology_edge": False, "event_type": "CYS_SG_TO_LIGAND_REACTIVE_ATOM_EXPLICIT_COVALENT_EDGE", "evidence_kind": "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR", "ligand_atom_element": "C", "ligand_atom_id": "CAP", "ligand_component_id": "4LH", "residue_atom_element": "S", "residue_atom_id": "SG", "residue_component_id": "CYS"},
        "ligand_component_id": "4LH", "reaction_specific_post_graph_proven": False,
        "reactive_ligand_atom": "CAP", "reactive_ligand_atom_element": "C", "reactive_residue": "CYS",
        "reactive_residue_atom": "SG", "reactive_residue_atom_element": "S",
        "semantic_topology_sha256": structural["semantic_topology_sha256"],
        "topology_heavy_atom_inventory": atom_inventory, "topology_heavy_atoms_not_observed": [],
    }
    signature_sha = "14e341061480aec0f18524fea5b8290fb5007daeeb8bd9827c4eb32768aa9b27"
    review_record = {
        "chemistry_review_signature_sha256": signature_sha, "review_scope": "SAMPLE_BOUND_ONLY",
        "reviewed_scaffold_atom_ids": list(SCAFFOLD_ATOMS), "reviewed_linker_atom_ids": [],
        "reviewed_warhead_role_atom_ids": list(WARHEAD_ATOMS), "reviewed_minimal_seed_atom_ids": list(MINIMAL_SEED),
        "reviewed_warhead_attachment_atom_id": "NBA", "reviewed_nonwarhead_boundary_atom_id": "CBH",
        "reviewed_attachment_boundary_bond_order": "SING",
    }
    complete = runtime.validate_direct_attachment_review_role_payload_v1(
        review_record=review_record, chemistry_review_signature=signature,
        expected_review_signature_sha256=signature_sha,
    )
    if not (complete.valid is True and tuple(complete.reasons) == () and complete.review_signature_bound is True and complete.reusable_scope_applicability_signatures_valid is True):
        _fail("PUBLISHED_DIRECT_COMPLETE_PAYLOAD_RUNTIME_FAILED")
    return {
        "valid": True, "reasons": [], "profile": EXPECTED_ROLE_PROFILE,
        "counts": {"W": 5, "L": 0, "S": 31}, "boundary": BOUNDARY,
        "minimal_seed_atom_ids": list(MINIMAL_SEED), "primary_anchor_atom_id": PRIMARY_ANCHOR,
        "applicable_task_ids": [0, 3, 4], "partition_validator": "validate_role_profile_v1",
        "seed_validator": "validate_minimal_seed_for_role_profile_v1",
        "complete_payload_validator": "validate_direct_attachment_review_role_payload_v1",
        "complete_payload_review_signature_bound": True,
    }


def _current_census(payloads: Mapping[Path, bytes]) -> dict[str, object]:
    rows = _parse_csv(payloads[CENSUS_MATRIX_RELATIVE], "CURRENT_WITH_0D8_CENSUS")
    if len(rows) != 1000 or len({row.get("canonical_event_id") for row in rows}) != 1000:
        _fail("CURRENT_CENSUS_UNIVERSE_DRIFT")
    targets = [row for row in rows if row.get("canonical_event_id") in set(EXPECTED_EVENT_IDS)]
    unit_rows = [row for row in rows if row.get("review_unit_id") == EXPECTED_REVIEW_UNIT_ID]
    if len(targets) != 4 or len(unit_rows) != 4 or tuple(row.get("canonical_event_id") for row in targets) != EXPECTED_EVENT_IDS or tuple(int(row["scaleup_rank"]) for row in targets) != EXPECTED_RANKS:
        _fail("CURRENT_CENSUS_4LH_EXACT4_DRIFT")
    prior = {
        "current_global_status": "CURRENTLY_UNREVIEWED", "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false", "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED", "training_use_disposition": "UNRESOLVED",
        "reactive_pair_sample_authoritative": "false", "role_partition_sample_authoritative": "false",
        "formal_training_admitted": "false", "current_runtime_model_usable": "false",
        "structurally_applicable_task_ids_json": "null",
    }
    for row in targets:
        for key, value in prior.items():
            if row.get(key) != value:
                _fail("CURRENT_CENSUS_4LH_PRIOR_STATE_DRIFT:" + key)
    summary = _strict_json(payloads[CENSUS_SUMMARY_RELATIVE], "CURRENT_WITH_0D8_SUMMARY")
    _strict_json(payloads[CENSUS_MANIFEST_RELATIVE], "CURRENT_WITH_0D8_MANIFEST")
    pending = summary.get("top_pending_review_units_by_event_yield")
    if type(pending) is not list or not pending or type(pending[0]) is not dict:
        _fail("CURRENT_CENSUS_PENDING_QUEUE_MISSING")
    expected_pending = {"rank": 1, "raw_priority_rank": 26, "review_unit_id": EXPECTED_REVIEW_UNIT_ID, "event_count": 4, "ligand_component_ids": ["4LH"], "pdb_ids": ["4Z16"], "current_review_status": "CURRENTLY_UNREVIEWED"}
    for key, value in expected_pending.items():
        _expect(pending[0].get(key), value, "CURRENT_CENSUS_PENDING_RANK1_DRIFT:" + key)
    authority = summary.get("authority_boundary")
    if type(authority) is not dict:
        _fail("CURRENT_CENSUS_AUTHORITY_BOUNDARY_MISSING")
    for key, value in (("next_priority_review_current_pending_rank", 1), ("next_priority_review_ligand", "4LH"), ("next_priority_review_raw_priority_rank", 26)):
        _expect(authority.get(key), value, "CURRENT_CENSUS_NEXT_PRIORITY_DRIFT:" + key)
    return {"row_count": 1000, "4LH_event_count": 4, "4LH_current_global_status": "CURRENTLY_UNREVIEWED", "4LH_task_relevance": "UNRESOLVED", "4LH_chemistry": "UNRESOLVED", "4LH_training_use": "UNRESOLVED", "current_pending_rank": 1, "raw_priority_rank": 26, "census_modified_by_ingestion": False}


def load_frozen_formal_decision_v1(
    repo_root: Path, *, formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Bind and independently validate the frozen 4LH authority and evidence."""
    root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    payloads = _verify_bindings(root, ACTIVE_BINDINGS, overrides)
    formal = _strict_json(payloads[FORMAL_DECISION_RELATIVE], "4LH_FORMAL_DECISION")
    _validate_formal(formal)
    event_validation = _validate_event_evidence(payloads[EVENT_EVIDENCE_RELATIVE])
    structural = _validate_graph_evidence(payloads[GRAPH_EVIDENCE_RELATIVE])
    _validate_semantic_owners(payloads)
    runtime = _runtime_validation(structural)
    census = _current_census(payloads)
    return {
        "formal_document": formal,
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "supporting_bindings": [_binding_record(value) for value in SUPPORTING_BINDINGS],
        "source_binding_policy_binding": _binding_record(POLICY_BINDING),
        "semantic_owner_bindings": [_binding_record(value) for value in SEMANTIC_OWNER_BINDINGS],
        "current_census_bindings": [_binding_record(value) for value in CENSUS_BINDINGS],
        "event_evidence_validation": event_validation,
        "structural_validation": {
            "Exact36_count": structural["Exact36_count"],
            "W_count": structural["W_count"],
            "L_count": structural["L_count"],
            "S_count": structural["S_count"],
            "partition_pairwise_disjoint": structural["partition_pairwise_disjoint"],
            "partition_exhaustive": structural["partition_exhaustive"],
            "boundary": BOUNDARY,
            "minimal_seed_atom_ids": list(MINIMAL_SEED),
            "primary_anchor_atom_id": PRIMARY_ANCHOR,
        },
        "graph_structural_proof": {
            key: structural[key]
            for key in (
                "Exact36_count", "partition_pairwise_disjoint",
                "partition_exhaustive", "W_connected", "L_connected_or_empty",
                "S_connected", "reactive_CAP_in_W", "cross_role_boundary_count",
                "cross_role_boundary", "W_count", "L_count", "S_count",
            )
        },
        "published_DIRECT_runtime_validation": runtime, "current_census_boundary": census,
    }


def _task_contract() -> dict[str, object]:
    applicability = [{"task_id": task_id, "semantic_long_name": semantic, "display_alias": alias, "structurally_applicable": applicable, "reason": reason} for task_id, semantic, alias, applicable, reason in DIRECT_APPLICABILITY]
    return {
        "global_canonical_tasks": [{"task_id": task_id, "semantic_long_name": semantic, "display_alias": alias, "generated_roles": list(generated), "fixed_or_seed_roles": list(fixed)} for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS],
        "global_canonical_task_count": 5, "B3_present": True, "sixth_task": False,
        "direct_profile_applicable_task_ids": [0, 3, 4], "task_applicability": applicability,
        "task_applicability_determined": True, "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False, "training_mask_targets_available_now": False,
    }


def _event_projection(event: tuple[object, ...]) -> dict[str, object]:
    return {
        "canonical_event_id": event[0], "scaleup_rank": event[1], "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": "4Z16", "model_number": 1, "protein_chain_or_asym": event[2], "cys_residue_id": "CYS:909-",
        "protein_altloc": None, "ligand_component_id": "4LH", "ligand_chain_or_asym": event[3], "ligand_altloc": None,
        "selected_connection_id": event[4], "POST_distance_angstrom": float(event[5]), "POST_distance_frozen_lexeme": event[5],
        "reported_POST_distance_angstrom": float(event[6]), "human_review_completed": True,
        "human_task_relevance_decision": "RELEVANT", "task_relevance_human_authoritative": True,
        "human_chemistry_decision": "POSITIVE", "chemistry_known_positive": True, "chemistry_human_authoritative": True,
        "negative_chemistry": False, "task_domain_negative": False,
        "reactive_pair_human_decision_available": True, "reactive_pair_human_authoritative": True,
        "protein_reactive_atom": "SG", "ligand_reactive_atom": "CAP", "pair_authority_scope": PAIR_AUTHORITY_SCOPE,
        "cross_structure_regiochemistry_generalization": False, "reusable_pair_rule_created": False,
        "all_4LH_uses_CAP_authority": False, "role_partition_human_decision_available": True,
        "role_partition_human_authoritative": True, "role_authority_scope": ROLE_AUTHORITY_SCOPE,
        "human_training_use_disposition": "INCLUDE", "training_use_human_authoritative": True,
        "future_training_admission_candidate": True, "future_training_admission_status": FUTURE_STATUS,
        "formal_training_admitted": False, "training_admission_created": False,
        "training_materialization_allowed": False, "formal_split_authority": False, "tensor_target_created": False,
        "training_mask_targets_available_now": False, "current_runtime_model_usable": False,
        "parameter_update_authorization": False, "ready_for_training": False,
        "supporting_PRE_source_graph_count": 1, "PRE_source_graph_present": True, "PRE_source_graph_count": 1,
        "PRE_mapping_count": 2, "PRE_mapping_status": PRE_MAPPING_STATUS, "PRE_status": PRE_STATUS,
        "PRE_topology_authority": False, "PRE_geometry_authority": False, "PRE_coordinates_authority": False,
        "PRE_reconstruction_performed": False, "POST_to_PRE_copy": False, "PRE_zero_fill": False,
        "leaving_group_inferred": False, "reagent_inferred": False, "reaction_edit_inferred": False,
        "POST_source_evidence_available": True, "explicit_covalent_evidence": True, "distance_only_inference": False,
        "POST_geometry_training_authority": False, "POST_geometry_training_target_created": False,
        "reusable_chemistry_authority": False, "reusable_pair_authority": False, "reusable_role_authority": False,
        "reaction_family_authority": False, "warhead_rule_authority": False, "warhead_type_authority": False,
        "authority_source": AUTHORITY_SOURCE, "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False,
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION, "stage": SCHEMA_VERSION,
        "artifact_role": "4LH_FROZEN_HUMAN_AUTHORITY_DETERMINISTIC_METADATA_PROJECTION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID, "formal_semantic_canonical_sha256": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_decision_binding": bound["formal_decision_binding"], "formal_validator_binding": bound["formal_validator_binding"],
        "supporting_bindings": bound["supporting_bindings"], "source_binding_policy_binding": bound["source_binding_policy_binding"],
        "semantic_owner_bindings": bound["semantic_owner_bindings"], "current_census_bindings": bound["current_census_bindings"],
        "human_authorization": {"D1_task_relevance": "RELEVANT", "D2_chemistry": "POSITIVE", "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR", "D4_role_candidate": "SELECT_CANDIDATE_0", "D5_training_use": "INCLUDE", "D6_scientific_context": EXPECTED_D6, "formal_decision_authority_is_human": True},
        "D6_provenance": {"D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT, "D6_utf8_sha256": EXPECTED_D6_SHA256, "human_authorized": True, "human_reviewed": True, "human_authored": False, "assistant_draft_creates_authority": False},
        "events": [_event_projection(event) for event in EXPECTED_EVENTS],
        "reactive_pair_authority": {"protein_reactive_atom": "SG", "ligand_reactive_atom": "CAP", "pair_authority_scope": PAIR_AUTHORITY_SCOPE, "sample_level_authoritative": True, "cross_structure_regiochemistry_generalization": False, "reusable_pair_rule_created": False, "all_4LH_uses_CAP_authority": False},
        "selected_role_partition": {"selected_role_candidate_index_0based": 0, "role_profile": EXPECTED_ROLE_PROFILE, "W": list(WARHEAD_ATOMS), "L": [], "S": list(SCAFFOLD_ATOMS), "counts": {"W": 5, "L": 0, "S": 31, "Exact": 36}, "direct_scaffold_warhead_boundary": BOUNDARY, "minimal_seed_atom_ids": list(MINIMAL_SEED), "primary_anchor_atom_id": PRIMARY_ANCHOR, "sample_level_authoritative": True, "authority_scope": ROLE_AUTHORITY_SCOPE, "reusable_role_authority": False, "published_DIRECT_runtime_validation": bound["published_DIRECT_runtime_validation"]},
        "structural_validation": bound["structural_validation"], "canonical_task_contract": _task_contract(),
        "PRE_boundary": {"supporting_PRE_source_graph_count": 1, "PRE_source_graph_present": True, "PRE_source_graph_count": 1, "PRE_mapping_count": 2, "PRE_mapping_status": PRE_MAPPING_STATUS, "PRE_status": PRE_STATUS, "PRE_topology_authority": False, "PRE_geometry_authority": False, "PRE_coordinates_authority": False, "PRE_reconstruction_performed": False, "POST_to_PRE_copy": False, "PRE_zero_fill": False, "leaving_group_inferred": False, "reagent_inferred": False, "reaction_edit_inferred": False},
        "POST_boundary": {"POST_source_evidence_available": True, "explicit_covalent_evidence": True, "distance_only_inference": False, "POST_geometry_training_authority": False, "POST_geometry_training_target_created": False},
        "training_boundary": {"human_training_use_disposition": "INCLUDE", "training_use_human_authoritative": True, "future_training_admission_candidate": True, "future_training_admission_status": FUTURE_STATUS, "formal_training_admitted": False, "training_admission_created": False, "training_materialization_allowed": False, "formal_split_authority": False, "tensor_target_created": False, "training_mask_targets_available_now": False, "current_runtime_model_usable": False, "parameter_update_authorization": False, "ready_for_training": False},
        "reusable_authority_boundary": {"reusable_chemistry_authority": False, "reusable_pair_authority": False, "reusable_role_authority": False, "reaction_family_authority": False, "warhead_rule_authority": False, "warhead_type_authority": False},
        "current_census_boundary": bound["current_census_boundary"],
        "authority_boundary": {"projection_of_frozen_formal_human_authority": True, "new_human_authority_created_by_ingestion": False, "authority_source": AUTHORITY_SOURCE, "authoritative_task_labels_created": False, "event_task_label_rows_materialized": False, "training_mask_targets_available_now": False, "formal_training_admitted": False, "ready_for_training": False, "reconciliation": False, "census_refresh": False, "queue_refresh": False, "training": False},
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "review_unit_id", "pdb_id", "model_number", "protein_chain_or_asym",
    "cys_residue_id", "protein_altloc", "ligand_component_id", "ligand_chain_or_asym", "ligand_altloc",
    "selected_connection_id", "POST_distance_angstrom", "reported_POST_distance_angstrom", "human_review_completed",
    "human_task_relevance_decision", "task_relevance_human_authoritative", "human_chemistry_decision",
    "chemistry_known_positive", "chemistry_human_authoritative", "negative_chemistry", "task_domain_negative",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative", "protein_reactive_atom",
    "ligand_reactive_atom", "pair_authority_scope", "cross_structure_regiochemistry_generalization",
    "all_4LH_uses_CAP_authority", "reusable_pair_rule_created", "role_partition_human_decision_available",
    "role_partition_human_authoritative", "selected_role_candidate_index_0based", "role_profile", "warhead_atoms_json",
    "linker_atoms_json", "scaffold_atoms_json", "W_L_S_counts_json", "boundary_bonds_json", "Exact36_count",
    "partition_pairwise_disjoint", "partition_exhaustive", "warhead_connected", "linker_connected_or_empty",
    "scaffold_connected", "reactive_CAP_in_W", "role_authority_scope", "reusable_role_authority",
    "global_canonical_task_count", "B3_present", "sixth_task", "canonical_task_applicability_json",
    "direct_profile_applicable_task_ids_json", "task_applicability_determined", "authoritative_task_labels_created",
    "event_task_label_rows_materialized", "human_training_use_disposition", "training_use_human_authoritative",
    "future_training_admission_candidate", "future_training_admission_status", "formal_training_admitted",
    "training_admission_created", "training_materialization_allowed", "formal_split_authority", "tensor_target_created",
    "training_mask_targets_available_now", "current_runtime_model_usable", "parameter_update_authorization",
    "ready_for_training", "supporting_PRE_source_graph_count", "PRE_source_graph_present", "PRE_source_graph_count",
    "PRE_mapping_count", "PRE_mapping_status", "PRE_status", "PRE_topology_authority", "PRE_geometry_authority",
    "PRE_coordinates_authority", "PRE_reconstruction_performed", "POST_to_PRE_copy", "PRE_zero_fill",
    "leaving_group_inferred", "reagent_inferred", "reaction_edit_inferred", "POST_source_evidence_available",
    "explicit_covalent_evidence", "distance_only_inference", "POST_geometry_training_authority",
    "POST_geometry_training_target_created", "reusable_chemistry_authority", "reusable_pair_authority",
    "reaction_family_authority", "warhead_rule_authority", "warhead_type_authority",
    "authority_source", "projection_of_frozen_formal_human_authority", "new_human_authority_created_by_ingestion",
)


def _matrix_rows(
    snapshot: Mapping[str, Any], structural_proof: Mapping[str, object]
) -> list[dict[str, object]]:
    expected_proof = {
        "Exact36_count": 36,
        "partition_pairwise_disjoint": True,
        "partition_exhaustive": True,
        "W_connected": True,
        "L_connected_or_empty": True,
        "S_connected": True,
        "reactive_CAP_in_W": True,
        "cross_role_boundary_count": 1,
        "cross_role_boundary": {
            "scaffold_atom_id": "CBH",
            "warhead_atom_id": "NBA",
            "bond_order": "SING",
            "scaffold_role": "S",
            "warhead_role": "W",
        },
        "W_count": 5,
        "L_count": 0,
        "S_count": 31,
    }
    if dict(structural_proof) != expected_proof:
        _fail("MATRIX_STRUCTURAL_CLAIMS_NOT_SOURCE_VERIFIED")
    boundary = {
        key: structural_proof["cross_role_boundary"][key]  # type: ignore[index]
        for key in ("scaffold_atom_id", "warhead_atom_id", "bond_order")
    }
    rows: list[dict[str, object]] = []
    applicability = snapshot["canonical_task_contract"]["task_applicability"]
    for event in snapshot["events"]:
        row = {key: "" for key in MATRIX_HEADER}
        for key in MATRIX_HEADER:
            if key in event:
                value = event[key]
                if type(value) is bool:
                    row[key] = "true" if value else "false"
                elif value is None:
                    row[key] = ""
                else:
                    row[key] = str(value)
        row.update({
            "model_number": "1", "protein_altloc": "", "ligand_altloc": "",
            "warhead_atoms_json": _json_cell(list(WARHEAD_ATOMS)), "linker_atoms_json": "[]",
            "scaffold_atoms_json": _json_cell(list(SCAFFOLD_ATOMS)),
            "W_L_S_counts_json": _json_cell([
                structural_proof["W_count"], structural_proof["L_count"],
                structural_proof["S_count"],
            ]),
            "boundary_bonds_json": _json_cell([boundary]),
            "Exact36_count": str(structural_proof["Exact36_count"]),
            "partition_pairwise_disjoint": str(structural_proof["partition_pairwise_disjoint"]).lower(),
            "partition_exhaustive": str(structural_proof["partition_exhaustive"]).lower(),
            "warhead_connected": str(structural_proof["W_connected"]).lower(),
            "linker_connected_or_empty": str(structural_proof["L_connected_or_empty"]).lower(),
            "scaffold_connected": str(structural_proof["S_connected"]).lower(),
            "reactive_CAP_in_W": str(structural_proof["reactive_CAP_in_W"]).lower(),
            "selected_role_candidate_index_0based": "0", "role_profile": EXPECTED_ROLE_PROFILE,
            "role_authority_scope": ROLE_AUTHORITY_SCOPE, "global_canonical_task_count": "5", "B3_present": "true",
            "sixth_task": "false", "canonical_task_applicability_json": _json_cell(applicability),
            "direct_profile_applicable_task_ids_json": "[0,3,4]", "task_applicability_determined": "true",
            "authoritative_task_labels_created": "false", "event_task_label_rows_materialized": "false",
        })
        rows.append(row)
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION, "stage": SCHEMA_VERSION, "review_unit": "4LH",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID, "event_count": 4, "human_review_completed": 4,
        "task_relevant": 4, "chemistry_positive": 4, "pair_authoritative": 4, "role_authoritative": 4,
        "DIRECT_profile": 4, "human_training_INCLUDE": 4, "future_training_candidates": 4,
        "formal_training_admitted": 0, "ready_for_training": 0, "PRE_authority": 0,
        "POST_training_authority": 0, "POST_source_evidence_count": 4,
        "canonical_Exact5_applicable_event_counts": {"warhead_only": 4, "linker_plus_warhead": 0, "scaffold_plus_warhead": 0, "scaffold_only": 4, "scaffold_plus_linker_plus_warhead": 4},
        "applicable_task_set_counts": {"[0,3,4]": 4}, "global_canonical_task_count": 5,
        "B3_present": True, "sixth_task": False, "W_count": 5, "L_count": 0, "S_count": 31,
        "direct_boundary": "CBH-NBA/SING", "minimal_seed_atom_ids": list(MINIMAL_SEED), "primary_anchor_atom_id": PRIMARY_ANCHOR,
        "PRE_mapping_status": PRE_MAPPING_STATUS, "PRE_status": PRE_STATUS,
        "authoritative_task_labels_created": False, "event_task_label_rows_materialized": False,
        "training_mask_targets_available_now": False, "projection_of_frozen_formal_human_authority": True,
        "new_human_authority_created_by_ingestion": False, "RECONCILIATION": False, "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False, "TRAINING_STARTED": False, "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
    }


def _candidate_source_records(repo_root: Path) -> list[dict[str, object]]:
    records = []
    for relative in (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE):
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise FourLHIngestionSafetyError("COVAPIE_4LH_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:" + relative.as_posix()) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            _fail("CANDIDATE_SOURCE_CLASS_INVALID:" + relative.as_posix())
        records.append({"path": relative.as_posix(), "byte_count": len(payload), "SHA256": _sha256(payload), "expected_path_class": "REGULAR_NON_SYMLINK", "expected_executable_class": "NON_EXECUTABLE"})
    return records


def _manifest(repo_root: Path, bound: Mapping[str, object], snapshot_bytes: bytes, matrix_bytes: bytes, summary_bytes: bytes) -> dict[str, object]:
    outputs = []
    for name, payload in ((SNAPSHOT, snapshot_bytes), (MATRIX, matrix_bytes), (SUMMARY, summary_bytes)):
        outputs.append({"path": (OUTPUT_ROOT_RELATIVE / name).as_posix(), "byte_count": len(payload), "SHA256": _sha256(payload)})
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION, "stage": SCHEMA_VERSION,
        "artifact_role": "DETERMINISTIC_SOURCE_DERIVED_4LH_INGESTION_MANIFEST",
        "candidate_publication_file_count": 7, "candidate_publication_paths": [path.as_posix() for path in CANDIDATE_PUBLICATION_PATHS],
        "output_artifact_count": 4, "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "candidate_source_bindings": _candidate_source_records(repo_root), "output_artifact_bindings": outputs,
        "active_source_binding_count": len(ACTIVE_BINDINGS), "active_source_bindings": [_binding_record(value) for value in ACTIVE_BINDINGS],
        "formal_decision_binding": bound["formal_decision_binding"], "formal_validator_binding": bound["formal_validator_binding"],
        "frozen_formal_validator_provenance_identity_only": True, "frozen_formal_validator_imported": False,
        "frozen_formal_validator_executed": False, "frozen_formal_validator_subprocessed": False,
        "formal_semantic_canonical_sha256": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_semantics_independently_validated": True, "published_DIRECT_runtime_validation": bound["published_DIRECT_runtime_validation"],
        "current_census_boundary": bound["current_census_boundary"], "canonical_task_contract": _task_contract(),
        "determinism": {"canonical_JSON": True, "LF_only": True, "timestamps": False, "hostname": False, "pid": False, "absolute_machine_paths": False},
        "manifest_self_SHA256_recorded": False, "MANIFEST_SELF_SHA256_PROHIBITED": True,
        "projection_of_frozen_formal_human_authority": True, "new_human_authority_created_by_ingestion": False,
        "operation_boundary": {"reconciliation": False, "census_refresh": False, "queue_refresh": False, "training": False, "tensorization": False, "dataset_mutation": False, "commit": False, "push": False},
        "READY_FOR_EXTERNAL_REVIEW": True, "READY_FOR_TRAINING": False,
    }


def _build_raw(repo_root: Path, overrides: Mapping[Path, Path] | None = None) -> dict[str, bytes]:
    bound = load_frozen_formal_decision_v1(repo_root, repository_path_overrides=overrides)
    snapshot_bytes = _json_bytes(_snapshot(bound))
    matrix_bytes = _csv_bytes(
        MATRIX_HEADER,
        _matrix_rows(
            _strict_json(snapshot_bytes, "BUILT_SNAPSHOT"),
            bound["graph_structural_proof"],  # type: ignore[arg-type]
        ),
    )
    summary_bytes = _json_bytes(_summary())
    manifest_bytes = _json_bytes(_manifest(Path(repo_root).resolve(), bound, snapshot_bytes, matrix_bytes, summary_bytes))
    return {SNAPSHOT: snapshot_bytes, MATRIX: matrix_bytes, SUMMARY: summary_bytes, MANIFEST: manifest_bytes}


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
    matrix_rows = _parse_csv(artifacts[MATRIX], "MATRIX")
    summary = _strict_json(artifacts[SUMMARY], "SUMMARY")
    manifest = _strict_json(artifacts[MANIFEST], "MANIFEST")
    if len(matrix_rows) != 4 or tuple(matrix_rows[0]) != MATRIX_HEADER:
        _fail("MATRIX_EXACT4_OR_HEADER_DRIFT")
    if snapshot["canonical_task_contract"]["B3_present"] is not True or snapshot["canonical_task_contract"]["sixth_task"] is not False:
        _fail("EXACT5_CONTRACT_DRIFT")
    if summary.get("READY_FOR_TRAINING") is not False or manifest.get("READY_FOR_EXTERNAL_REVIEW") is not True:
        _fail("READINESS_BOUNDARY_DRIFT")
    def reject_dynamic(value: object) -> None:
        if type(value) is dict:
            for key, child in value.items():
                if key.lower() in {"timestamp", "hostname", "pid", "absolute_path", "self_sha256"} and child is not False:
                    _fail("MANIFEST_DYNAMIC_OR_SELF_METADATA:" + key)
                reject_dynamic(child)
        elif type(value) is list:
            for child in value:
                reject_dynamic(child)
        elif type(value) is str and value.startswith("/"):
            _fail("MANIFEST_ABSOLUTE_PATH_VALUE")
    reject_dynamic(manifest)
    return {"status": "PASS", "event_count": 4, "matrix_column_count": len(MATRIX_HEADER), "output_artifact_count": 4, "READY_FOR_EXTERNAL_REVIEW": True, "READY_FOR_TRAINING": False}


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
    descriptor, temporary = tempfile.mkstemp(prefix=".covapie_4lh_", dir=path.parent)
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
    if live != fresh:
        _fail("MATERIALIZED_BYTES_NOT_FRESH_BUILD")
    return {**result, "materialized_bytes_equal_fresh_build": True, "deterministic_double_build": fresh == build_artifacts_v1(root)}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    print(json.dumps(materialize_artifacts_v1(repo_root), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
