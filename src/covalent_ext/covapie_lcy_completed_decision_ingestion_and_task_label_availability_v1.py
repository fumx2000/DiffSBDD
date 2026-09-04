"""Ingest frozen LCY Exact4 human authority as deterministic metadata only.

The frozen formal validator is provenance identity only: this owner binds its
content identity but never imports, parses, executes, or subprocesses it.  The
formal JSON is independently validated together with the two necessary LCY
preparation artifacts, the canonical Exact5 owner, the generic completed-
decision owner, the published task-domain-negative lane precedent, and the
current with-GVE census.

This module performs no reconciliation, census or queue refresh, role
selection, task-label materialization, dataset mutation, tensorization,
training admission, model operation, training, or parameter update.
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
    "LCYIngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)


SCHEMA_VERSION = "covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_lcy_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_lcy_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_lcy_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_lcy_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_lcy_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_lcy_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_lcy_event_task_label_availability_v1.csv"
SUMMARY = "covapie_lcy_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_lcy_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

LCY_ROOT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "LCY_COVAPIE_BULK_REVIEW_UNIT_BA488AF51EDD8ED6"
)
FORMAL_DECISION_RELATIVE = (
    LCY_ROOT / "formal-human-decision-v1/lcy_formal_human_decision_v1.json"
)
FORMAL_VALIDATOR_RELATIVE = (
    LCY_ROOT / "formal-human-decision-v1/validate_lcy_formal_human_decision_v1.py"
)
EVENT_EVIDENCE_RELATIVE = (
    LCY_ROOT / "review-preparation-v1/lcy_exact4_event_evidence_v1.csv"
)
GRAPH_CANDIDATES_RELATIVE = (
    LCY_ROOT / "review-preparation-v1/lcy_graph_and_role_candidates_v1.json"
)
SOURCE_BINDING_POLICY_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
CANONICAL_TASK_OWNER_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
GENERIC_RECONCILIATION_RELATIVE = Path(
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py"
)
TASK_DOMAIN_NEGATIVE_MATRIX_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1/"
    "covapie_batch001_event_task_label_availability_v1.csv"
)
CENSUS_MATRIX_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_gve_v1/"
    "covapie_cumulative1000_current_global_readiness_census_with_gve_v1.csv"
)

BASELINE_COMMIT = "d292dd806a740cbdc25ef12aad44ff9fffeda5c9"
FORMAL_DECISION_SCHEMA = "covapie_lcy_exact4_formal_human_decision_v1"
FORMAL_RECORD_ROLE = "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "3383814e97c6a29318d3a38890e32cbdaf170a461dbacfbc2f7b9a9c2fd6492e"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_BA488AF51EDD8ED6"
EXPECTED_COMPLETED_LANE = "COMPLETED_TASK_DOMAIN_NEGATIVE"
EXPECTED_ROLE_PROFILE = "NOT_ESTABLISHED"
PAIR_AUTHORITY_SCOPE = "CURRENT_LCY_4R0O_EXACT4_ONLY"
AUTHORITY_SOURCE = "FORMAL_LCY_HUMAN_DECISION"
PRE_MAPPING_STATUS = "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
PRE_STATUS = "PRE_REACTION_UNRESOLVED"

EXPECTED_D6 = (
    "Treat the current LCY 4R0O Exact4 as task-domain negative for the current "
    "CovaPIE "
    "target-directed medicinal covalent small-molecule training domain while "
    "preserving chemistry-positive sample-level evidence: 4R0O is a PEGylated "
    "plastocyanin structure produced in a cysteine/maleimide polymer-bioconjugation "
    "context, and the deposited LCY component is a local saturated succinimide-like "
    "post-adduct fragment rather than the full PEG conjugate or a standalone "
    "medicinal ligand. Confirm the source-observed Cys-SG ↔ LCY-C1 covalent "
    "endpoints for all four Exact4 events. D4 remains UNRESOLVED and no "
    "role-partition or Exact5 sample applicability authority is created: the "
    "isolated LCY graph lacks the full PEG/polymer context, the frozen review policy "
    "has zero selectable candidates, and although three singleton-scaffold DIRECT "
    "partitions are formally valid under the published role runtime, all have S=1 "
    "and cannot support the published 2/3-node minimal-seed cardinality. Do not "
    "force NO_MACHINE_VALID_ROLE_CANDIDATE or REVISE_ROLE_PARTITION merely from the "
    "policy-scoped zero-candidate result. The separate 3A2G LCY event is supporting "
    "same-component context only and transfers no authority. Set training use to "
    "NOT_APPLICABLE, not EXCLUDE_FROM_TRAINING_ONLY; human_training_excluded remains "
    "false. PRE remains PRE_REACTION_UNRESOLVED because the available candidate "
    "PRE/free graph has no compatible mapping; do not reconstruct PRE from maleimide "
    "chemistry, copy POST to PRE, or infer leaving groups, reagents, reaction-family "
    "labels, or bond edits. This decision creates no reusable chemistry/pair/role "
    "authority, reaction-family or warhead-rule/type authority, formal training "
    "admission, tensor target, runtime usability, or parameter-update authority."
)
EXPECTED_D6_BYTE_COUNT = 1754
EXPECTED_D6_SHA256 = "db6fdb1ca13c1bbbfce111e251c0ceba011a770317edd92ff12c8042a2ee884b"

# Event ID, rank, PDB, protein asym, Cys residue, ligand asym, connection,
# exact distance lexeme, reported distance lexeme.
EXPECTED_EVENTS = (
    (
        "COVAPIE_CYS_SG_EVENT_V1:4R0O:A:CYS:45-:SG:F:LCY:C1",
        898, "4R0O", "A", "CYS:45-", "F", "covale1", "1.699831", "1.700",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4R0O:B:CYS:45-:SG:H:LCY:C1",
        899, "4R0O", "B", "CYS:45-", "H", "covale2", "1.696052", "1.696",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4R0O:C:CYS:45-:SG:J:LCY:C1",
        900, "4R0O", "C", "CYS:45-", "J", "covale3", "1.696490", "1.696",
    ),
    (
        "COVAPIE_CYS_SG_EVENT_V1:4R0O:D:CYS:45-:SG:L:LCY:C1",
        901, "4R0O", "D", "CYS:45-", "L", "covale4", "1.700175", "1.700",
    ),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)

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
        32277,
        "d7c7b427b87b13fa61188bd6b14a3e9dd3a37e4a170176222685065d419a3387",
        False,
        "LCY_FROZEN_FORMAL_HUMAN_DECISION",
        "PARSED_JSON_AND_INDEPENDENTLY_VALIDATED",
    ),
    (
        FORMAL_VALIDATOR_RELATIVE,
        "project_parent_relative",
        84087,
        "b8e33358c80ebb1356a9af8ab2cd9db86033adfdb31fc05f32061b57eab68c85",
        False,
        "LCY_FROZEN_FORMAL_VALIDATOR_PROVENANCE_IDENTITY_ONLY",
        "PROVENANCE_IDENTITY_ONLY_NOT_PARSED_IMPORTED_EXECUTED_OR_SUBPROCESSED",
    ),
)
SUPPORTING_BINDINGS: tuple[_Binding, ...] = (
    (
        EVENT_EVIDENCE_RELATIVE,
        "project_parent_relative",
        8633,
        "53864911c20a3671a1fec9382519dde033bcc0e4700513a4837952160c496388",
        False,
        "LCY_EXACT4_EVENT_EVIDENCE",
        "PARSED_CSV_SUPPORTING_EVIDENCE",
    ),
    (
        GRAPH_CANDIDATES_RELATIVE,
        "project_parent_relative",
        23983,
        "6780cccbd83157fabe7962f0471a5e1278dcefa8aac013357b57690d20d88e7f",
        False,
        "LCY_GRAPH_AND_MACHINE_ROLE_CANDIDATES_EVIDENCE_ONLY",
        "PARSED_JSON_WITH_NO_CANDIDATE_SELECTION",
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
        GENERIC_RECONCILIATION_RELATIVE,
        "repository_relative",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
        False,
        "PUBLISHED_GENERIC_COMPLETED_DECISION_RECONCILIATION_OWNER",
        "IMPORTED_READ_ONLY_FOR_SYNTHETIC_EXACT11_COMPATIBILITY_PROBE",
    ),
    (
        TASK_DOMAIN_NEGATIVE_MATRIX_RELATIVE,
        "repository_relative",
        35603,
        "f8481147babbad02215c3c3f767fe22ba6a511b8a076482a9635fec5d5cf8e82",
        False,
        "PUBLISHED_TASK_DOMAIN_NEGATIVE_COMPLETED_LANE_PRECEDENT",
        "PARSED_CSV_LANE_AND_UNAVAILABLE_LABEL_VOCABULARY",
    ),
)
CENSUS_BINDING: _Binding = (
    CENSUS_MATRIX_RELATIVE,
    "repository_relative",
    543602,
    "540b072d45924688a640e5ca16484500b3815bc66267d73ceead81246b226557",
    False,
    "CURRENT_WITH_GVE_GLOBAL_CENSUS_PREFORMAL_READ_ONLY",
    "PARSED_CSV_PREFORMAL_STATE_READ_ONLY",
)
ACTIVE_BINDINGS = (
    *FORMAL_BINDINGS,
    *SUPPORTING_BINDINGS,
    POLICY_BINDING,
    *SEMANTIC_OWNER_BINDINGS,
    CENSUS_BINDING,
)


class LCYIngestionSafetyError(ValueError):
    """Raised when LCY ingestion safety or semantics cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise LCYIngestionSafetyError("COVAPIE_LCY_INGESTION_V1_ERROR:" + reason)


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
    if not isinstance(payload, bytes) or payload.startswith(b"\xef\xbb\xbf"):
        _fail("JSON_BYTES_OR_BOM_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise LCYIngestionSafetyError(
            "COVAPIE_LCY_INGESTION_V1_ERROR:JSON_UTF8_INVALID:" + label
        ) from error

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
        raise LCYIngestionSafetyError(
            "COVAPIE_LCY_INGESTION_V1_ERROR:JSON_PARSE:" + label
        ) from error
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _binding_record(binding: _Binding) -> dict[str, object]:
    relative, namespace, byte_count, digest, executable, role, method = binding
    return {
        "path": relative.as_posix(),
        "namespace": namespace,
        "byte_count": byte_count,
        "SHA256": digest,
        "semantic_source_identity": (
            namespace + ":" + relative.as_posix() + "@" + digest
        ),
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
    return {Path(key): Path(path) for key, path in value.items()}


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
        raise LCYIngestionSafetyError(
            "COVAPIE_LCY_INGESTION_V1_ERROR:SOURCE_BINDING_FAILED:"
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
        raise LCYIngestionSafetyError(
            "COVAPIE_LCY_INGESTION_V1_ERROR:SEMANTIC_OWNER_AST_INVALID:" + label
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
                    raise LCYIngestionSafetyError(
                        "COVAPIE_LCY_INGESTION_V1_ERROR:"
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
            "D4_role_candidate": "UNRESOLVED",
            "D5_training_use": "NOT_APPLICABLE",
            "D6_inherited_exact": True,
            "canonical_event_id": event_id,
            "event_exception": False,
            "event_index_0based": index,
            "formal_decision_applies": True,
            "ligand_reactive_atom": "C1",
            "protein_reactive_atom": "SG",
            "role_partition_sample_authority": False,
            "sample_positive_chemistry_authority": True,
            "sample_reactive_pair_authority": True,
            "sample_task_relevance_authority": True,
            "scaleup_rank": rank,
        }
        for index, (
            event_id,
            rank,
            pdb_id,
            protein_asym,
            _cys,
            ligand_asym,
            _connection,
            distance,
            _reported,
        ) in enumerate(EXPECTED_EVENTS)
    ]


def _expected_pre_event_rows() -> list[dict[str, object]]:
    return [
        {
            "PRE_mapping_status": PRE_MAPPING_STATUS,
            "candidate_PRE_free_graph_count": 1,
            "canonical_event_id": event_id,
            "compatible_mapping_count": 0,
            "final_PRE_reaction_status": PRE_STATUS,
            "supporting_adduct_graph_count": 1,
        }
        for event_id in EXPECTED_EVENT_IDS
    ]


def _expected_formal_tasks() -> dict[str, object]:
    return {
        "B3_present": True,
        "canonical_mask_structural_labels_available_for_sample": False,
        "global_contract_modified": False,
        "sample_authoritative_role_partition": False,
        "sample_authoritative_task_applicability": False,
        "sixth_task": False,
        "task_count": 5,
        "tasks": [
            {
                "display_alias": alias,
                "semantic_long_name": semantic,
                "task_id": task_id,
            }
            for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
        ],
    }


def _validate_formal_document(formal: Mapping[str, Any]) -> None:
    """Independently validate the frozen LCY D1-D6 and authority boundaries."""

    _expect(formal.get("schema_version"), FORMAL_DECISION_SCHEMA, "FORMAL_SCHEMA_DRIFT")
    _expect(formal.get("record_role"), FORMAL_RECORD_ROLE, "FORMAL_RECORD_ROLE_DRIFT")
    _expect(formal.get("stage"), "FORMAL_HUMAN_DECISION", "FORMAL_STAGE_DRIFT")
    _expect(
        formal.get("formal_decision_semantic_canonical_sha256"),
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
        ("formal_decision_created", True),
        ("formal_authority_created", True),
        ("formal_authority_is_human", True),
        ("machine_approval", False),
        ("reviewer_id", "fmx"),
        ("attestor_id", "fmx"),
        ("authorization_origin", "EXTERNAL_HUMAN_CHAT_AUTHORIZATION"),
    ):
        _expect(formal.get(key), expected, "FORMAL_FINALIZATION_DRIFT:" + key)

    _expect(
        formal.get("approval_and_finalization"),
        {
            "approved": True,
            "decision_finalized": True,
            "formal_authority_created": True,
            "formal_authority_is_human": True,
            "formal_decision_created": True,
            "human_decision_created": True,
            "human_review_completed": True,
            "machine_approval": False,
            "machine_is_formal_decision_maker": False,
            "machine_is_scientific_decision_maker": False,
            "unsigned": False,
        },
        "FORMAL_APPROVAL_AND_FINALIZATION_DRIFT",
    )
    _expect(
        formal.get("human_identity_and_attestation"),
        {
            "attestor_id": "fmx",
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_AUTHORIZATION",
            "formal_authority_source": "HUMAN",
            "invented_signature": False,
            "invented_timestamp": False,
            "new_scientific_choice_authorized": False,
            "reviewer_id": "fmx",
        },
        "FORMAL_HUMAN_IDENTITY_DRIFT",
    )
    d6_bytes = EXPECTED_D6.encode("utf-8")
    if len(d6_bytes) != EXPECTED_D6_BYTE_COUNT or _sha256(d6_bytes) != EXPECTED_D6_SHA256:
        _fail("INTERNAL_D6_IDENTITY_INVALID")
    _expect(
        formal.get("inherited_human_scientific_decision"),
        {
            "D1_task_relevance": "NOT_RELEVANT",
            "D2_chemistry": "POSITIVE",
            "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
            "D4_role_candidate": "UNRESOLVED",
            "D5_training_use": "NOT_APPLICABLE",
            "D6_scientific_context": EXPECTED_D6,
            "D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT,
            "D6_utf8_sha256": EXPECTED_D6_SHA256,
            "inheritance_byte_exact": True,
            "scientific_choice_reconsidered": False,
        },
        "FORMAL_D1_D6_DRIFT",
    )
    _expect(formal.get("event_level_formal_decision_count"), 4, "FORMAL_EVENT_COUNT_DRIFT")
    _expect(
        formal.get("event_level_formal_decisions"),
        _expected_formal_events(),
        "FORMAL_EVENT_DECISION_DRIFT",
    )
    _expect(
        formal.get("target_Exact4"),
        {
            "3A2G_event_included": False,
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "event_count": 4,
            "ligand_wide_selection": False,
            "raw_priority_rank": 24,
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "scaleup_ranks": list(EXPECTED_RANKS),
        },
        "FORMAL_EXACT4_IDENTITY_DRIFT",
    )
    _expect(
        formal.get("canonical_Exact5"),
        _expected_formal_tasks(),
        "FORMAL_CANONICAL_EXACT5_DRIFT",
    )
    _expect(
        formal.get("sample_task_relevance"),
        {
            "all_LCY_rule_created": False,
            "authority_scope": PAIR_AUTHORITY_SCOPE,
            "sample_task_relevance_authority": True,
            "task_domain_negative": True,
            "task_relevance_disposition": "NOT_RELEVANT",
            "universal_generalization_created": False,
        },
        "FORMAL_TASK_RELEVANCE_AUTHORITY_DRIFT",
    )
    _expect(
        formal.get("sample_chemistry"),
        {
            "CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE": True,
            "D1_NOT_RELEVANT_DOES_NOT_COLLAPSE_D2_POSITIVE": True,
            "chemistry_disposition": "POSITIVE",
            "reusable_chemistry_authority": False,
            "sample_positive_chemistry_authority": True,
        },
        "FORMAL_POSITIVE_CHEMISTRY_AUTHORITY_DRIFT",
    )
    _expect(
        formal.get("sample_reactive_pair"),
        {
            "3A2G_pair_promoted": False,
            "all_LCY_C1_authority": False,
            "authority_scope": PAIR_AUTHORITY_SCOPE,
            "ligand_reactive_atom": "C1",
            "observed_POST_distances_angstrom": [
                float(row[7]) for row in EXPECTED_EVENTS
            ],
            "protein_reactive_atom": "SG",
            "reusable_pair_authority": False,
            "sample_reactive_pair_authority": True,
        },
        "FORMAL_PAIR_AUTHORITY_DRIFT",
    )
    _expect(
        formal.get("D4_role_boundary"),
        {
            "D4_human_choice": "UNRESOLVED",
            "canonical_mask_structural_labels_sample_authority": False,
            "formal_valid_singleton_diagnostic_count": 3,
            "formal_valid_singleton_diagnostic_indices": [0, 1, 2],
            "formal_valid_singleton_diagnostics": [
                {
                    "S_atom_ids": ["O2"],
                    "S_count": 1,
                    "cut_bond": {"atom_id_1": "C3", "atom_id_2": "O2"},
                    "diagnostic_index": 0,
                    "minimal_seed_2_or_3_possible": False,
                    "published_runtime_valid": True,
                    "review_policy_eligible": False,
                    "selected": False,
                },
                {
                    "S_atom_ids": ["O1"],
                    "S_count": 1,
                    "cut_bond": {"atom_id_1": "C4", "atom_id_2": "O1"},
                    "diagnostic_index": 1,
                    "minimal_seed_2_or_3_possible": False,
                    "published_runtime_valid": True,
                    "review_policy_eligible": False,
                    "selected": False,
                },
                {
                    "S_atom_ids": ["C5"],
                    "S_count": 1,
                    "cut_bond": {"atom_id_1": "C5", "atom_id_2": "N1"},
                    "diagnostic_index": 2,
                    "minimal_seed_2_or_3_possible": False,
                    "published_runtime_valid": True,
                    "review_policy_eligible": False,
                    "selected": False,
                },
            ],
            "formal_valid_singleton_diagnostics_are_selectable": False,
            "human_selected_role_candidate": None,
            "review_policy_candidate_count": 0,
            "review_policy_selectable_candidate_indices": [],
            "role_partition_sample_authority": False,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "selected_role_partition": None,
            "structurally_applicable_task_ids": None,
            "task_applicability_sample_authority": False,
        },
        "FORMAL_UNRESOLVED_ROLE_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("training_boundary"),
        {
            "NOT_APPLICABLE_is_EXCLUDE_FROM_TRAINING_ONLY": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
            "current_runtime_model_usable": False,
            "formal_training_admitted": False,
            "future_training_admission_candidate": False,
            "human_training_excluded": False,
            "human_training_use_disposition_authority": True,
            "parameter_update_authorization": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
            "training_use_disposition": "NOT_APPLICABLE",
            "training_use_include": False,
        },
        "FORMAL_TRAINING_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("POST_boundary"),
        {
            "D3_formalizes_only_sample_reactive_pair": True,
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
            "POST_source_evidence_count": 4,
            "observed_distances_angstrom": [float(row[7]) for row in EXPECTED_EVENTS],
        },
        "FORMAL_POST_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("PRE_boundary"),
        {
            "POST_to_PRE_copy": False,
            "PRE_authority": False,
            "PRE_coordinates": None,
            "PRE_geometry_authority": False,
            "PRE_reconstruction": False,
            "PRE_status": PRE_STATUS,
            "PRE_topology": None,
            "PRE_zero_fill": False,
            "bond_edit_inference": False,
            "leaving_group_inference": False,
            "literature_derived_PRE_graph": False,
            "per_event": _expected_pre_event_rows(),
            "reagent_inference": False,
        },
        "FORMAL_PRE_BOUNDARY_DRIFT",
    )
    _expect(
        formal.get("future_generic_Exact11_projection"),
        {
            "chemistry_disposition": "POSITIVE",
            "generic_fact_materialized_now": False,
            "generic_facts_created": False,
            "generic_owner_import_path_exact": True,
            "generic_reconciliation_outputs_created": False,
            "human_review_completed": True,
            "human_training_excluded": False,
            "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
            "reconciliation_performed_now": False,
            "synthetic_future_Exact11_accepted": True,
            "task_relevance_disposition": "NOT_RELEVANT",
            "training_disposition": "NOT_APPLICABLE",
        },
        "FORMAL_GENERIC_PROJECTION_DRIFT",
    )
    current = formal.get("current_with_GVE_census_preformal_snapshot")
    if type(current) is not dict:
        _fail("FORMAL_CURRENT_CENSUS_BOUNDARY_INVALID")
    required_current = {
        "canonical_event_ids": list(EXPECTED_EVENT_IDS),
        "canonical_mask_structural_labels_available": False,
        "census_modified_by_this_step": False,
        "chemistry_disposition": "UNRESOLVED",
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "current_runtime_model_usable": False,
        "event_count": 4,
        "formal_training_admitted": False,
        "human_review_completed": False,
        "human_training_excluded": False,
        "orthogonal_combination_supporting_row_count": 4,
        "published_census": "with-GVE",
        "reactive_pair_sample_authoritative": False,
        "role_partition_sample_authoritative": False,
        "task_relevance_disposition": "UNRESOLVED",
        "schema_column_count": 47,
        "schema_row_count": 1000,
        "training_use_disposition": "UNRESOLVED",
    }
    _expect(current, required_current, "FORMAL_CURRENT_CENSUS_BOUNDARY_DRIFT")
    debt = formal.get("census_crossfield_compatibility")
    if type(debt) is not dict:
        _fail("FORMAL_CENSUS_DEBT_INVALID")
    for key, expected in (
        ("47_COLUMN_SCHEMA_CHANGE_REQUIRED", False),
        ("CURRENT_WITH_GVE_CENSUS_SUPPORTS_ORTHOGONAL_COMBINATION", True),
        ("GENERIC_SCHEMA_CHANGE_REQUIRED", False),
        ("HUMAN_D2_POSITIVE_PRESERVED", True),
        ("LEGACY_BASE_CENSUS_ASSUMPTION_HISTORICAL_ONLY", True),
        ("NEW_CENSUS_CROSSFIELD_AUDIT_REQUIRED", False),
        ("NEW_CROSSFIELD_DEBT_CREATED", False),
        ("base_census_modified", False),
        ("with_GVE_census_modified", False),
    ):
        _expect(debt.get(key), expected, "FORMAL_CENSUS_DEBT_DRIFT:" + key)
    _expect(
        debt,
        formal.get("census_crossfield_compatibility"),
        "FORMAL_CROSSFIELD_EXACTNESS_INTERNAL",
    )
    same_component = formal.get("same_component_3A2G_boundary")
    if type(same_component) is not dict:
        _fail("FORMAL_3A2G_BOUNDARY_INVALID")
    for key, expected in (
        ("canonical_event_id", "COVAPIE_CYS_SG_EVENT_V1:3A2G:A:CYS:102-:SG:G:LCY:C1"),
        ("current_Exact4_authority", False),
        ("decision_transferred", False),
        ("pair_promoted", False),
        ("role_transferred", False),
        ("PRE_transferred", False),
        ("training_transferred", False),
    ):
        _expect(same_component.get(key), expected, "FORMAL_3A2G_DRIFT:" + key)
    operations = formal.get("downstream_operations")
    if type(operations) is not dict or any(value is not False for value in operations.values()):
        _fail("FORMAL_DOWNSTREAM_OPERATION_OCCURRED")
    authority = formal.get("formal_authority_boundary")
    if type(authority) is not dict:
        _fail("FORMAL_AUTHORITY_BOUNDARY_INVALID")
    true_set = [
        "formal_authority_created",
        "formal_authority_is_human",
        "human_training_use_disposition_authority",
        "sample_positive_chemistry_authority",
        "sample_reactive_pair_authority",
        "sample_task_relevance_authority",
    ]
    _expect(authority.get("formal_authority_true_set"), true_set, "FORMAL_TRUE_SET_DRIFT")
    observed_true = sorted(
        key for key, value in authority.items()
        if value is True and key != "formal_authority_true_set"
    )
    _expect(observed_true, sorted(true_set), "FORMAL_TRUE_AUTHORITY_EXACT6_DRIFT")
    if any(value is not False for key, value in authority.items() if key not in (*true_set, "formal_authority_true_set")):
        _fail("FORMAL_UNAUTHORIZED_AUTHORITY")


EVENT_EVIDENCE_HEADER = (
    "package_role", "event_index_0based", "canonical_event_id", "scaleup_rank",
    "raw_priority_rank", "review_unit_id", "pdb_id", "model_number",
    "protein_chain_or_asym", "cys_residue_id", "protein_reactive_atom",
    "protein_altloc", "protein_occupancy", "ligand_component_id",
    "ligand_chain_or_asym", "ligand_reactive_atom", "ligand_reactive_element",
    "ligand_altloc", "ligand_occupancy", "selected_connection_id",
    "selected_connection_type", "explicit_covalent_evidence",
    "distance_only_inference",
    "protein_atom_coordinates_json", "ligand_atom_coordinates_json",
    "reported_POST_distance_angstrom", "recomputed_POST_distance_angstrom",
    "POST_distance_absolute_difference_angstrom", "POST_distance_recomputed",
    "raw_structure_available", "exact_cys_sg_event_recovered",
    "full_coordinate_POST_evidence_available",
    "CCD_graph_complete", "feature_compatible", "structural_processing_success",
    "post_geometry_source_evidence_available", "representation_gap",
    "feature_incompatible", "priority_review_in_scope",
    "reactive_pair_raw_structural_evidence", "reactive_pair_sample_authoritative",
    "role_partition_sample_authoritative",
    "canonical_mask_structural_labels_available", "formal_training_admitted",
    "human_confirmed_pair", "supporting_adduct_graph_count",
    "candidate_PRE_free_source_graph_count", "compatible_atom_mapping_count",
    "PRE_source_mapping_status", "final_PRE_reaction_status",
    "PRE_topology_created", "PRE_coordinates_created", "POST_to_PRE_copy",
    "PRE_zero_fill", "current_human_review_status", "chemistry_disposition",
    "task_relevance_disposition", "training_use_disposition",
    "source_structure_binding_json", "CCD_source_binding_json",
    "processing_source_binding_json",
)


def _parse_csv(payload: bytes, label: str) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise LCYIngestionSafetyError(
            "COVAPIE_LCY_INGESTION_V1_ERROR:CSV_PARSE_FAILED:" + label
        ) from error
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        _fail("CSV_HEADER_INVALID:" + label)
    if any(None in row for row in rows):
        _fail("CSV_ROW_WIDTH_INVALID:" + label)
    return rows


def _validate_event_evidence(payload: bytes) -> dict[str, object]:
    rows = _parse_csv(payload, "LCY_EVENT_EVIDENCE")
    if not rows or tuple(rows[0]) != EVENT_EVIDENCE_HEADER or len(rows) != 4:
        _fail("EVENT_EVIDENCE_HEADER_OR_COUNT_INVALID")
    for index, (row, expected) in enumerate(zip(rows, EXPECTED_EVENTS)):
        event_id, rank, pdb_id, protein_asym, cys, ligand_asym, connection, distance, reported = expected
        exact = {
            "package_role": "UNSIGNED_NON_AUTHORITATIVE_MACHINE_REVIEW_AID_PREPARATION",
            "event_index_0based": str(index),
            "canonical_event_id": event_id,
            "scaleup_rank": str(rank),
            "raw_priority_rank": "24",
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "pdb_id": pdb_id,
            "model_number": "1",
            "protein_chain_or_asym": protein_asym,
            "cys_residue_id": cys,
            "protein_reactive_atom": "SG",
            "ligand_component_id": "LCY",
            "ligand_chain_or_asym": ligand_asym,
            "ligand_reactive_atom": "C1",
            "selected_connection_id": connection,
            "recomputed_POST_distance_angstrom": distance,
            "reported_POST_distance_angstrom": reported,
            "explicit_covalent_evidence": "true",
            "distance_only_inference": "false",
            "post_geometry_source_evidence_available": "true",
            "reactive_pair_sample_authoritative": "false",
            "role_partition_sample_authoritative": "false",
            "canonical_mask_structural_labels_available": "false",
            "formal_training_admitted": "false",
            "human_confirmed_pair": "false",
            "supporting_adduct_graph_count": "1",
            "candidate_PRE_free_source_graph_count": "1",
            "compatible_atom_mapping_count": "0",
            "PRE_source_mapping_status": PRE_MAPPING_STATUS,
            "final_PRE_reaction_status": PRE_STATUS,
            "PRE_topology_created": "false",
            "PRE_coordinates_created": "false",
            "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false",
            "current_human_review_status": "CURRENTLY_UNREVIEWED",
            "task_relevance_disposition": "UNRESOLVED",
            "chemistry_disposition": "UNRESOLVED",
            "training_use_disposition": "UNRESOLVED",
        }
        if any(row.get(key) != value for key, value in exact.items()):
            _fail("EVENT_EVIDENCE_ROW_DRIFT:" + event_id)
    return {
        "event_count": 4,
        "event_ids": list(EXPECTED_EVENT_IDS),
        "scaleup_ranks": list(EXPECTED_RANKS),
        "POST_source_evidence_event_count": 4,
        "PRE_source_graph_present_event_count": 4,
        "PRE_mapping_count": 0,
        "same_component_3A2G_included": False,
    }


def _validate_graph_candidates(payload: bytes) -> dict[str, object]:
    graph = _strict_json_loads(payload, "LCY_GRAPH_CANDIDATES")
    _expect(
        graph.get("canonical_Exact5"),
        {
            "B3_present": True,
            "sixth_task": False,
            "task_count": 5,
            "tasks": [
                {
                    "display_alias": alias,
                    "semantic_long_name": semantic,
                    "task_id": task_id,
                }
                for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
            ],
        },
        "GRAPH_CANONICAL_EXACT5_DRIFT",
    )
    _expect(graph.get("review_policy_candidate_count"), 0, "GRAPH_REVIEW_CANDIDATE_COUNT_DRIFT")
    _expect(graph.get("review_policy_candidate_indices"), [], "GRAPH_REVIEW_CANDIDATE_INDICES_DRIFT")
    _expect(graph.get("review_policy_candidates"), [], "GRAPH_REVIEW_CANDIDATES_DRIFT")
    authority = graph.get("authority_boundary")
    if type(authority) is not dict:
        _fail("GRAPH_AUTHORITY_BOUNDARY_INVALID")
    if authority.get("best_candidate") is not None or any(
        value is not False for key, value in authority.items() if key != "best_candidate"
    ):
        _fail("GRAPH_UNAUTHORIZED_AUTHORITY")
    reactive = graph.get("reactive_atom_evidence")
    if type(reactive) is not dict or (
        reactive.get("atom_id") != "C1"
        or reactive.get("reactive_atom_present_in_graph") is not True
        or reactive.get("all_Exact4_source_observed_ligand_endpoints_are_C1") is not True
        or reactive.get("human_confirmed_pair") is not False
        or reactive.get("automatic_all_LCY_C1_reusable_authority") is not False
    ):
        _fail("GRAPH_C1_SOURCE_IDENTITY_INVALID")
    pre_rows = graph.get("PRE_evidence_by_event")
    if type(pre_rows) is not list or len(pre_rows) != 4:
        _fail("GRAPH_PRE_EVIDENCE_INVALID")
    for expected_id, row in zip(EXPECTED_EVENT_IDS, pre_rows):
        if type(row) is not dict or (
            row.get("canonical_event_id") != expected_id
            or row.get("compatible_atom_mapping_count") != 0
            or row.get("PRE_source_mapping_status") != PRE_MAPPING_STATUS
            or row.get("candidate_PRE_free_source_graph_count") != 1
            or row.get("final_PRE_reaction_status") != PRE_STATUS
        ):
            _fail("GRAPH_PRE_EVENT_DRIFT:" + expected_id)
    audit = graph.get("candidate_scope_audit")
    if type(audit) is not dict:
        _fail("GRAPH_DIAGNOSTIC_AUDIT_INVALID")
    diagnostics = audit.get("per_partition_diagnostic_inventory")
    if type(diagnostics) is not list or len(diagnostics) != 3:
        _fail("GRAPH_DIAGNOSTIC_COUNT_INVALID")
    expected_diagnostics = (
        (0, {"atom_id_1": "C3", "atom_id_2": "O2"}, ["O2"]),
        (1, {"atom_id_1": "C4", "atom_id_2": "O1"}, ["O1"]),
        (2, {"atom_id_1": "C5", "atom_id_2": "N1"}, ["C5"]),
    )
    for diagnostic, (index, cut, scaffold) in zip(diagnostics, expected_diagnostics):
        if type(diagnostic) is not dict or (
            diagnostic.get("prefilter_partition_index_0based") != index
            or diagnostic.get("cut_bonds") != [cut]
            or diagnostic.get("S_atom_ids") != scaffold
            or diagnostic.get("S_count") != 1
            or diagnostic.get("published_role_profile_valid") is not True
            or diagnostic.get("minimal_seed_cardinality_2_or_3_possible") is not False
            or diagnostic.get("review_candidate_eligible") is not False
            or diagnostic.get("diagnostic_evidence_only") is not True
            or diagnostic.get("role_authority_created") is not False
        ):
            _fail("GRAPH_SINGLETON_DIAGNOSTIC_DRIFT")
    same = graph.get("same_ligand_context")
    if type(same) is not dict or type(same.get("non_target_event")) is not dict:
        _fail("GRAPH_3A2G_CONTEXT_INVALID")
    non_target = same["non_target_event"]
    if (
        non_target.get("canonical_event_id")
        != "COVAPIE_CYS_SG_EVENT_V1:3A2G:A:CYS:102-:SG:G:LCY:C1"
        or non_target.get("current_target") is not False
        or non_target.get("decision_transfer") is not False
        or non_target.get("pair_transfer") is not False
        or non_target.get("role_transfer") is not False
        or non_target.get("PRE_transfer") is not False
        or non_target.get("training_transfer") is not False
    ):
        _fail("GRAPH_3A2G_TRANSFER_BOUNDARY_DRIFT")
    return {
        "review_policy_candidate_count": 0,
        "review_policy_selectable_candidate_indices": [],
        "formal_valid_singleton_diagnostic_count": 3,
        "formal_valid_singleton_diagnostic_indices": [0, 1, 2],
        "formal_valid_singleton_diagnostics_are_selectable": False,
        "machine_candidate_selected": False,
        "human_candidate_selected_in_preparation": False,
        "role_authority_created": False,
        "task_applicability_authority_created": False,
        "PRE_mapping_count": 0,
        "same_component_3A2G_included": False,
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
        if (
            row.get("positive_generative_supervision_eligible") != "false"
            or row.get("reactive_atom_pair_label_available") != "false"
            or row.get("role_partition_label_available") != "false"
            or row.get("event_training_use_label_available") != "false"
            or row.get("label_availability_status")
            != "NOT_APPLICABLE_TASK_DOMAIN_NEGATIVE"
        ):
            _fail("PUBLISHED_TASK_DOMAIN_NEGATIVE_LANE_DRIFT")
    return {
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "unavailable_label_token": "NOT_APPLICABLE_TASK_DOMAIN_NEGATIVE",
        "negative_precedent_event_count": len(negative),
    }


def _validate_generic_owner_compatibility(repo_root: Path) -> dict[str, object]:
    module = importlib.import_module(
        "covalent_ext.covapie_completed_human_decision_reconciliation_v1"
    )
    module_path = Path(module.__file__).resolve()
    if module_path != (repo_root / GENERIC_RECONCILIATION_RELATIVE).resolve():
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
    accepted = 0
    for event_id in EXPECTED_EVENT_IDS:
        fact = module.NormalizedCompletedDecisionFact(
            canonical_event_id=event_id,
            review_unit_id=EXPECTED_REVIEW_UNIT_ID,
            **GENERIC_PROJECTION,
            source_decision_schema=FORMAL_DECISION_SCHEMA,
            source_decision_sha256=FORMAL_BINDINGS[0][3],
            source_binding_path=FORMAL_DECISION_RELATIVE.as_posix(),
        )
        module._validate_fact(fact, binding)
        accepted += 1
    if accepted != 4:
        _fail("GENERIC_OWNER_SYNTHETIC_FACT_ACCEPTANCE_INVALID")
    return {
        "generic_exact11_accepts_LCY_combination": True,
        "synthetic_fact_count_validated": 4,
        "source_binding_path_namespace": "repository_parent_relative",
        "GENERIC_SOURCE_NAMESPACE_REPOSITORY_PARENT_RELATIVE": True,
        "reconciliation_performed": False,
        "generic_fact_materialized": False,
        **copy.deepcopy(GENERIC_PROJECTION),
    }


def _validate_current_census(payload: bytes) -> dict[str, object]:
    rows = _parse_csv(payload, "CURRENT_WITH_GVE_CENSUS")
    target = [row for row in rows if row.get("canonical_event_id") in EXPECTED_EVENT_IDS]
    if (
        len(rows) != 1000
        or tuple(row["canonical_event_id"] for row in target) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in target) != EXPECTED_RANKS
    ):
        _fail("CURRENT_CENSUS_LCY_EXACT4_IDENTITY_INVALID")
    for row in target:
        expected = {
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
            "formal_training_admitted": "false",
            "current_runtime_model_usable": "false",
        }
        if any(row.get(key) != value for key, value in expected.items()):
            _fail("CURRENT_CENSUS_LCY_PREFORMAL_STATE_DRIFT")
    return {
        "source_SHA256": CENSUS_BINDING[3],
        "event_count": 4,
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": False,
        "chemistry": "UNRESOLVED",
        "task_relevance": "UNRESOLVED",
        "training_use": "UNRESOLVED",
        "reactive_pair_sample_authority": False,
        "role_partition_sample_authority": False,
        "sample_mask_labels": False,
        "formal_training_admitted": False,
        "CENSUS_REFRESH": False,
        "current_census_changed": False,
    }


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    formal_validator_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Bind all necessary sources and independently validate frozen LCY truth."""

    repo_root = Path(repo_root).resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if formal_decision_path is not None:
        overrides[FORMAL_DECISION_RELATIVE] = Path(formal_decision_path)
    if formal_validator_path is not None:
        overrides[FORMAL_VALIDATOR_RELATIVE] = Path(formal_validator_path)
    allowed = {binding[0] for binding in ACTIVE_BINDINGS}
    if set(overrides) - allowed:
        _fail("SOURCE_OVERRIDE_NOT_AUTHORIZED")
    payloads = _verify_bindings(repo_root, ACTIVE_BINDINGS, overrides)
    identities = {
        (binding[0].as_posix(), binding[1], binding[3]) for binding in ACTIVE_BINDINGS
    }
    if len(ACTIVE_BINDINGS) != 9 or len(identities) != 9:
        _fail("ACTIVE_SOURCE_BINDING_IDENTITIES_NOT_EXACT9_UNIQUE")
    formal = _strict_json_loads(
        payloads[FORMAL_DECISION_RELATIVE], "LCY_FROZEN_FORMAL_DECISION"
    )
    _validate_formal_document(formal)
    evidence = _validate_event_evidence(payloads[EVENT_EVIDENCE_RELATIVE])
    graph = _validate_graph_candidates(payloads[GRAPH_CANDIDATES_RELATIVE])
    canonical = _validate_canonical_owner(payloads[CANONICAL_TASK_OWNER_RELATIVE])
    lane = _validate_task_domain_negative_precedent(
        payloads[TASK_DOMAIN_NEGATIVE_MATRIX_RELATIVE]
    )
    generic = _validate_generic_owner_compatibility(repo_root)
    census = _validate_current_census(payloads[CENSUS_MATRIX_RELATIVE])
    return {
        "active_source_bindings": _binding_records(ACTIVE_BINDINGS),
        "active_source_binding_count": 9,
        "duplicate_source_binding_identity_count": 0,
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "event_evidence_validation": evidence,
        "graph_candidate_validation": graph,
        "canonical_task_validation": canonical,
        "completed_lane_validation": lane,
        "generic_owner_compatibility": generic,
        "current_census_boundary": census,
        "formal_semantics_independently_validated": True,
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_parsed": False,
        "formal_validator_executed": False,
        "formal_validator_subprocessed": False,
        "formal_validator_runtime_dependency": False,
        "formal": formal,
    }


def _metadata_only_boundary() -> dict[str, object]:
    return {
        "metadata_only": True,
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
    }


def _canonical_task_applicability() -> list[dict[str, object]]:
    return [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "role_profile": None,
            "structurally_applicable": None,
            "training_mask_target_available_now": False,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]


def _canonical_task_contract() -> dict[str, object]:
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
        "task_applicability": _canonical_task_applicability(),
        "task_applicability_determined": False,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "sample_authoritative_applicable_task_ids": None,
        "direct_profile_applicable_task_ids": None,
        "sample_canonical_mask_structural_labels_available": False,
        "training_mask_targets_available_now": False,
    }


def _role_boundary() -> dict[str, object]:
    return {
        "D4": "UNRESOLVED",
        "role_decision_field_present": True,
        "role_partition_human_decision_available": False,
        "usable_role_partition_label_available": False,
        "role_partition_human_authoritative": False,
        "selected_candidate_index_0based": None,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "warhead_atoms": None,
        "linker_atoms": None,
        "scaffold_atoms": None,
        "W_L_S_counts": None,
        "boundary_bonds": None,
        "reusable_role_authority": False,
        "review_policy_candidate_count": 0,
        "review_policy_selectable_candidate_indices": [],
        "formal_valid_singleton_diagnostic_count": 3,
        "formal_valid_singleton_diagnostic_indices": [0, 1, 2],
        "formal_valid_singleton_diagnostics_are_selectable": False,
        "formal_valid_singleton_diagnostics": [
            {
                "diagnostic_index": 0,
                "cut_bond": {"atom_id_1": "C3", "atom_id_2": "O2"},
                "S_atom_ids": ["O2"],
                "S_count": 1,
                "published_runtime_valid": True,
                "minimal_seed_2_or_3_possible": False,
                "review_policy_eligible": False,
                "selected": False,
            },
            {
                "diagnostic_index": 1,
                "cut_bond": {"atom_id_1": "C4", "atom_id_2": "O1"},
                "S_atom_ids": ["O1"],
                "S_count": 1,
                "published_runtime_valid": True,
                "minimal_seed_2_or_3_possible": False,
                "review_policy_eligible": False,
                "selected": False,
            },
            {
                "diagnostic_index": 2,
                "cut_bond": {"atom_id_1": "C5", "atom_id_2": "N1"},
                "S_atom_ids": ["C5"],
                "S_count": 1,
                "published_runtime_valid": True,
                "minimal_seed_2_or_3_possible": False,
                "review_policy_eligible": False,
                "selected": False,
            },
        ],
    }


def _pair_boundary() -> dict[str, object]:
    return {
        "D3": "CONFIRM_OBSERVED_PAIR",
        "reactive_pair_human_decision_available": True,
        "reactive_pair_human_authoritative": True,
        "reactive_pair_sample_authority": True,
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C1",
        "pair_authority_scope": PAIR_AUTHORITY_SCOPE,
        "observed_distances_angstrom": [float(row[7]) for row in EXPECTED_EVENTS],
        "reusable_pair_rule_created": False,
        "cross_structure_regiochemistry_generalization": False,
        "all_LCY_C1_authority": False,
        "3A2G_pair_promoted": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "D5": "NOT_APPLICABLE",
        "formal_event_training_use_decision": "NOT_APPLICABLE",
        "event_training_use_human_decision_available": True,
        "training_use_allowed": False,
        "training_use_include": False,
        "human_training_excluded": False,
        "training_exclusion_reason": None,
        "candidate_for_future_training_admission": False,
        "future_training_admission_candidate": False,
        "future_training_admission_status": None,
        "training_admitted": False,
        "formal_training_admitted": False,
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
        "PRE_reconstruction": False,
        "POST_to_PRE_copy": False,
        "PRE_zero_fill": False,
        "leaving_group_inferred": False,
        "reagent_inferred": False,
        "bond_edit_inferred": False,
        "PRE_label_or_target_created": False,
    }


def _post_boundary() -> dict[str, object]:
    return {
        "POST_source_evidence_available": True,
        "POST_source_evidence_count": 4,
        "explicit_covalent_evidence": True,
        "distance_only_inference": False,
        "POST_geometry_training_authority": False,
        "POST_geometry_training_target_created": False,
        "POST_geometry_training_label_available_now": False,
    }


def _reusable_boundary() -> dict[str, object]:
    return {
        "reusable_chemistry_authority": False,
        "reusable_pair_rule_created": False,
        "reusable_role_authority": False,
        "cross_structure_regiochemistry_generalization": False,
        "reaction_family_authority": False,
        "warhead_rule_authority": False,
        "warhead_type_authority": False,
        "reaction_family_training_class_target_available": False,
        "warhead_rule_training_class_target_available": False,
        "warhead_type_target_available": False,
        "reusable_authority_label_available": False,
    }


def _census_debt() -> dict[str, object]:
    return {
        "CURRENT_WITH_GVE_CENSUS_SUPPORTS_ORTHOGONAL_COMBINATION": True,
        "LEGACY_BASE_CENSUS_ASSUMPTION_HISTORICAL_ONLY": True,
        "NEW_CROSSFIELD_DEBT_CREATED": False,
        "NEW_CENSUS_CROSSFIELD_AUDIT_REQUIRED": False,
        "47_COLUMN_SCHEMA_CHANGE_REQUIRED": False,
        "GENERIC_SCHEMA_CHANGE_REQUIRED": False,
        "HUMAN_D2_POSITIVE_PRESERVED": True,
        "INGESTION_DOES_NOT_MODIFY_CENSUS": True,
    }


def _operation_boundary() -> dict[str, object]:
    return {
        "INGESTION_COMPLETE": True,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "ROLE_SELECTION": False,
        "MASK_LABEL_AUTHORITY_CREATED": False,
        "TRAINING_STARTED": False,
        "COMMIT": False,
        "PUSH": False,
        **_metadata_only_boundary(),
    }


def _precedent_boundary() -> dict[str, object]:
    return {
        "GVE_owner_imported_at_runtime": False,
        "GVE_checker_executed": False,
        "GVE_tests_executed": False,
        "GVE_outputs_copied_byte_for_byte": False,
    }


def _readiness() -> dict[str, object]:
    return {
        "LCY_INGESTION_CANDIDATE_PASS": True,
        "LCY_FORMAL_DECISION_BOUND": True,
        "LCY_FORMAL_VALIDATOR_PROVENANCE_ONLY": True,
        "LCY_FORMAL_SEMANTICS_INDEPENDENTLY_VALIDATED": True,
        "LCY_COMPLETED_DECISION_METADATA_PROJECTED": True,
        "LCY_COMPLETED_LANE_TASK_DOMAIN_NEGATIVE": True,
        "LCY_TASK_NOT_RELEVANT": True,
        "LCY_CHEMISTRY_POSITIVE": True,
        "LCY_CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE": True,
        "LCY_SAMPLE_SG_C1_AUTHORITY_AVAILABLE": True,
        "LCY_SAMPLE_ROLE_AUTHORITY_AVAILABLE": False,
        "LCY_TASK_APPLICABILITY_AUTHORITY_AVAILABLE": False,
        "LCY_SAMPLE_MASK_LABELS_AVAILABLE": False,
        "LCY_D4_UNRESOLVED": True,
        "LCY_REVIEW_POLICY_CANDIDATE_COUNT_ZERO": True,
        "LCY_FORMAL_VALID_SINGLETON_DIAGNOSTIC_COUNT_3": True,
        "LCY_D5_NOT_APPLICABLE": True,
        "LCY_HUMAN_TRAINING_EXCLUDED": False,
        "LCY_FUTURE_TRAINING_ADMISSION_CANDIDATE": False,
        "LCY_FORMAL_TRAINING_ADMITTED": False,
        "LCY_TENSOR_TARGET_CREATED": False,
        "LCY_CURRENT_RUNTIME_MODEL_USABLE": False,
        "PRE_REACTION_UNRESOLVED": True,
        "EXACT5_B3_PRESENT": True,
        "SIXTH_TASK": False,
        "EXPECTED_GENERIC_LEGACY_STATUS_NEGATIVE": True,
        "EXPECTED_GENERIC_CHEMISTRY_POSITIVE": True,
        "EXPECTED_GENERIC_TRAINING_NOT_APPLICABLE": True,
        "GENERIC_EXACT11_COMPATIBILITY_PASS": True,
        "GENERIC_SOURCE_NAMESPACE_REPOSITORY_PARENT_RELATIVE": True,
        "CURRENT_WITH_GVE_CENSUS_SUPPORTS_ORTHOGONAL_COMBINATION": True,
        "NEW_CROSSFIELD_DEBT_CREATED": False,
        "NEW_CENSUS_CROSSFIELD_AUDIT_REQUIRED": False,
        "FUTURE_RECONCILIATION_SOURCE_CHAIN_21_127": True,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "RECONCILIATION": False,
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "READY_FOR_EXTERNAL_REVIEW": True,
        "COMMIT": False,
        "PUSH": False,
    }


def _event_projection(row: tuple[object, ...]) -> dict[str, object]:
    event_id, rank, pdb_id, protein_asym, cys, ligand_asym, connection, distance, reported = row
    return {
        "canonical_event_id": event_id,
        "scaleup_rank": rank,
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "pdb_id": pdb_id,
        "model_number": 1,
        "protein_chain_or_asym": protein_asym,
        "cys_residue_id": cys,
        "ligand_component_id": "LCY",
        "ligand_chain_or_asym": ligand_asym,
        "selected_connection_id": connection,
        "POST_distance_angstrom": float(distance),
        "POST_distance_frozen_lexeme": distance,
        "reported_POST_distance_angstrom": float(reported),
        "reported_POST_distance_frozen_lexeme": reported,
        "completed": True,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "human_review_completed": True,
        "task_relevance": "NOT_RELEVANT",
        "task_relevance_human_authority": True,
        "human_task_relevance_decision": "NOT_RELEVANT",
        "task_relevance_human_authoritative": True,
        "task_domain_negative": True,
        "chemistry": "POSITIVE",
        "chemistry_known_positive": True,
        "chemistry_human_authority": True,
        "human_chemistry_decision": "POSITIVE",
        "chemistry_human_authoritative": True,
        "negative_chemistry": False,
        "chemistry_negative": False,
        "CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE": True,
        "TASK_DOMAIN_NEGATIVE_DOES_NOT_COLLAPSE_POSITIVE_CHEMISTRY": True,
        "positive_generative_supervision_eligible": False,
        **_pair_boundary(),
        **_role_boundary(),
        **_canonical_task_contract(),
        **_training_boundary(),
        **_pre_boundary(),
        **_post_boundary(),
        **_reusable_boundary(),
        "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "authority_source": AUTHORITY_SOURCE,
        "projection_of_frozen_formal_human_authority": True,
        **_metadata_only_boundary(),
    }


def _same_component_boundary() -> dict[str, object]:
    return {
        "canonical_event_id": "COVAPIE_CYS_SG_EVENT_V1:3A2G:A:CYS:102-:SG:G:LCY:C1",
        "current_target": False,
        "decision_transfer": False,
        "pair_transfer": False,
        "role_transfer": False,
        "PRE_transfer": False,
        "training_transfer": False,
        "current_Exact4_authority": False,
    }


def _future_reconciliation_arithmetic() -> dict[str, object]:
    return {
        "future_arithmetic_only": True,
        "reconciliation_performed": False,
        "reconciliation_output_files": 0,
        "current": {
            "source_count": 20,
            "fact_count": 123,
            "completed_positive_events": 115,
            "completed_positive_units": 18,
            "completed_negative_events": 32,
            "completed_negative_units": 6,
            "completed_total_events": 147,
            "completed_total_units": 24,
            "unreviewed_events": 191,
            "unreviewed_units": 107,
            "in_progress_events": 0,
            "in_progress_units": 0,
        },
        "expected_future_with_LCY": {
            "source_count": 21,
            "fact_count": 127,
            "completed_positive_events": 115,
            "completed_positive_units": 18,
            "completed_negative_events": 36,
            "completed_negative_units": 7,
            "completed_total_events": 151,
            "completed_total_units": 25,
            "unreviewed_events": 187,
            "unreviewed_units": 106,
            "in_progress_events": 0,
            "in_progress_units": 0,
        },
        "LCY_adds_generic_completed_negative_facts": 4,
        "LCY_chemistry_disposition": "POSITIVE",
    }


def _snapshot(bound: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "LCY_COMPLETED_DECISION_METADATA_ONLY_PROJECTION",
        "active_source_binding_count": len(ACTIVE_BINDINGS),
        "duplicate_source_binding_identity_count": 0,
        "active_source_bindings": bound["active_source_bindings"],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "formal_semantic_digest": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_semantics_independently_validated": True,
        "formal_validator_lifecycle": {
            "formal_validator_provenance_identity_only": True,
            "formal_validator_imported": False,
            "formal_validator_parsed": False,
            "formal_validator_executed": False,
            "formal_validator_subprocessed": False,
            "formal_validator_runtime_dependency": False,
        },
        "identity": {
            "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
            "ligand_component_id": "LCY",
            "event_count": 4,
            "canonical_event_ids": list(EXPECTED_EVENT_IDS),
            "scaleup_ranks": list(EXPECTED_RANKS),
        },
        "completed": True,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "task_relevance": "NOT_RELEVANT",
        "chemistry": "POSITIVE",
        "chemistry_negative": False,
        "CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE": True,
        "TASK_DOMAIN_NEGATIVE_DOES_NOT_COLLAPSE_POSITIVE_CHEMISTRY": True,
        "reactive_pair_sample_authority": True,
        "role_partition_sample_authority": False,
        "task_applicability_sample_authority": False,
        "training_use": "NOT_APPLICABLE",
        "human_training_excluded": False,
        "future_training_admission_candidate": False,
        "formal_training_admitted": False,
        "training_materialization_allowed": False,
        "tensor_target_created": False,
        "current_runtime_model_usable": False,
        "READY_FOR_TRAINING": False,
        "formal_projection": {
            "D1": "NOT_RELEVANT",
            "D2": "POSITIVE",
            "D3": "CONFIRM_OBSERVED_PAIR",
            "D4": "UNRESOLVED",
            "D5": "NOT_APPLICABLE",
            "D6_scientific_context": EXPECTED_D6,
            "D6_utf8_byte_count": EXPECTED_D6_BYTE_COUNT,
            "D6_utf8_sha256": EXPECTED_D6_SHA256,
        },
        "task_relevance_authority": {
            "human_review_completed": True,
            "task_relevance": "NOT_RELEVANT",
            "task_relevance_human_authority": True,
            "human_task_relevance_decision": "NOT_RELEVANT",
            "task_relevance_human_authoritative": True,
            "task_domain_negative": True,
            "scope": PAIR_AUTHORITY_SCOPE,
            "universal_task_domain_rule_created": False,
        },
        "chemistry_authority": {
            "chemistry": "POSITIVE",
            "chemistry_known_positive": True,
            "chemistry_human_authority": True,
            "human_chemistry_decision": "POSITIVE",
            "chemistry_human_authoritative": True,
            "negative_chemistry": False,
            "positive_generative_supervision_eligible": False,
        },
        "reactive_pair_authority": _pair_boundary(),
        "role_partition_boundary": _role_boundary(),
        "canonical_task_contract": _canonical_task_contract(),
        "training_boundary": _training_boundary(),
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(),
        "reusable_authority_boundary": _reusable_boundary(),
        "events": [_event_projection(row) for row in EXPECTED_EVENTS],
        "generic_Exact11_projection_preview": bound["generic_owner_compatibility"],
        "future_reconciliation_arithmetic": _future_reconciliation_arithmetic(),
        "same_component_3A2G_boundary": _same_component_boundary(),
        "current_census_boundary": bound["current_census_boundary"],
        "census_crossfield_compatibility": _census_debt(),
        "GVE_implementation_precedent_only": _precedent_boundary(),
        "operation_boundary": _operation_boundary(),
        "readiness": _readiness(),
    }


# Generic modern SR2/GD1 fields are retained.  No LCY-only role, task, or
# completed-lane vocabulary is added; unavailable values use published null or
# false conventions.
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
                "protein_altloc": "",
                "ligand_altloc": "",
                "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
                "reported_POST_distance_angstrom": event[
                    "reported_POST_distance_frozen_lexeme"
                ],
                "selected_candidate_index_0based": "null",
                "warhead_atoms_json": "null",
                "linker_atoms_json": "null",
                "scaffold_atoms_json": "null",
                "W_L_S_counts_json": "null",
                "boundary_bonds_json": "null",
                "global_canonical_task_count": "5",
                "B3_present": "true",
                "sixth_task": "false",
                "canonical_task_applicability_json": _json_cell(
                    _canonical_task_applicability()
                ),
                "direct_profile_applicable_task_ids_json": "null",
                "training_exclusion_reason": "",
                "future_training_admission_status": "",
                "projection_of_frozen_formal_human_authority": "true",
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
        "review_unit": "LCY",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "formal_completed_event_count": count("completed", True),
        "task_NOT_RELEVANT_event_count": count("task_relevance", "NOT_RELEVANT"),
        "chemistry_POSITIVE_event_count": count("chemistry", "POSITIVE"),
        "chemistry_negative_event_count": count("negative_chemistry", True),
        "pair_sample_authority_event_count": count(
            "reactive_pair_human_authoritative", True
        ),
        "role_sample_authority_event_count": count(
            "role_partition_human_authoritative", True
        ),
        "task_applicability_authority_event_count": count(
            "task_applicability_determined", True
        ),
        "sample_mask_label_authority_event_count": count(
            "training_mask_targets_available_now", True
        ),
        "training_NOT_APPLICABLE_event_count": count(
            "formal_event_training_use_decision", "NOT_APPLICABLE"
        ),
        "training_INCLUDE_event_count": count(
            "formal_event_training_use_decision", "INCLUDE"
        ),
        "training_EXCLUDE_event_count": count(
            "formal_event_training_use_decision", "EXCLUDE_FROM_TRAINING_ONLY"
        ),
        "human_training_excluded_event_count": count("human_training_excluded", True),
        "future_training_candidate_event_count": count(
            "future_training_admission_candidate", True
        ),
        "formal_training_admitted_event_count": count("formal_training_admitted", True),
        "tensor_target_event_count": count("tensor_target_created", True),
        "runtime_usable_event_count": count("current_runtime_model_usable", True),
        "POST_source_evidence_event_count": count("POST_source_evidence_available", True),
        "POST_training_authority_event_count": count(
            "POST_geometry_training_authority", True
        ),
        "POST_training_target_event_count": count(
            "POST_geometry_training_target_created", True
        ),
        "PRE_source_graph_present_event_count": count("PRE_source_graph_present", True),
        "PRE_compatible_mapping_event_count": sum(
            event.get("PRE_mapping_count_per_event", 0) > 0 for event in events
        ),
        "PRE_resolved_event_count": sum(
            event.get("PRE_status") != PRE_STATUS for event in events
        ),
        "PRE_training_authority_event_count": count("PRE_geometry_authority", True),
        "review_policy_candidate_count": 0,
        "formal_valid_singleton_diagnostic_count": 3,
        "selectable_role_candidate_count": 0,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task": False,
        "CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE": True,
        "generic_future_fact_count": 4,
        "generic_legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "generic_chemistry": "POSITIVE",
        "generic_task_relevance": "NOT_RELEVANT",
        "generic_training": "NOT_APPLICABLE",
        "generic_source_namespace": "repository_parent_relative",
        "GENERIC_SOURCE_NAMESPACE_REPOSITORY_PARENT_RELATIVE": True,
        "future_reconciliation_arithmetic": _future_reconciliation_arithmetic(),
        "census_crossfield_compatibility": _census_debt(),
        "GVE_implementation_precedent_only": _precedent_boundary(),
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "RECONCILIATION": False,
        "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "metadata_only_boundary": _metadata_only_boundary(),
        "readiness": _readiness(),
    }


def _validate_text_payload(label: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes
        or not payload
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail("TEXT_PAYLOAD_HYGIENE_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise LCYIngestionSafetyError(
            "COVAPIE_LCY_INGESTION_V1_ERROR:TEXT_UTF8_INVALID:" + label
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
            raise LCYIngestionSafetyError(
                "COVAPIE_LCY_INGESTION_V1_ERROR:CANDIDATE_SOURCE_READ_FAILED:"
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


def _standalone_bound() -> dict[str, object]:
    return {
        "active_source_bindings": _binding_records(ACTIVE_BINDINGS),
        "formal_decision_binding": _binding_record(FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(FORMAL_BINDINGS[1]),
        "generic_owner_compatibility": {
            "generic_exact11_accepts_LCY_combination": True,
            "synthetic_fact_count_validated": 4,
            "source_binding_path_namespace": "repository_parent_relative",
            "GENERIC_SOURCE_NAMESPACE_REPOSITORY_PARENT_RELATIVE": True,
            "reconciliation_performed": False,
            "generic_fact_materialized": False,
            **copy.deepcopy(GENERIC_PROJECTION),
        },
        "current_census_boundary": {
            "source_SHA256": CENSUS_BINDING[3],
            "event_count": 4,
            "current_global_status": "CURRENTLY_UNREVIEWED",
            "human_review_completed": False,
            "chemistry": "UNRESOLVED",
            "task_relevance": "UNRESOLVED",
            "training_use": "UNRESOLVED",
            "reactive_pair_sample_authority": False,
            "role_partition_sample_authority": False,
            "sample_mask_labels": False,
            "formal_training_admitted": False,
            "CENSUS_REFRESH": False,
            "current_census_changed": False,
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
            "LCY_COMPLETED_DECISION_METADATA_ONLY_INGESTION_NOT_RECONCILIATION_"
            "CENSUS_REFRESH_ROLE_SELECTION_TASK_LABEL_MATERIALIZATION_OR_TRAINING"
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
        "active_source_binding_count": len(ACTIVE_BINDINGS),
        "duplicate_source_binding_identity_count": 0,
        "active_source_bindings": bound["active_source_bindings"],
        "formal_decision_binding": bound["formal_decision_binding"],
        "formal_validator_binding": bound["formal_validator_binding"],
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_parsed": False,
        "formal_validator_executed": False,
        "formal_validator_subprocessed": False,
        "formal_validator_runtime_dependency": False,
        "formal_semantic_digest": FORMAL_SEMANTIC_CANONICAL_SHA256,
        "formal_semantics_independently_validated": True,
        "generic_owner_compatibility": bound["generic_owner_compatibility"],
        "completed_lane": EXPECTED_COMPLETED_LANE,
        "CHEMISTRY_POSITIVE_BUT_TASK_DOMAIN_NEGATIVE": True,
        "TASK_DOMAIN_NEGATIVE_DOES_NOT_COLLAPSE_POSITIVE_CHEMISTRY": True,
        "canonical_task_contract": _canonical_task_contract(),
        "role_partition_boundary": _role_boundary(),
        "training_boundary": _training_boundary(),
        "PRE_boundary": _pre_boundary(),
        "POST_boundary": _post_boundary(),
        "reusable_authority_boundary": _reusable_boundary(),
        "same_component_3A2G_boundary": _same_component_boundary(),
        "future_reconciliation_arithmetic": _future_reconciliation_arithmetic(),
        "current_census_boundary": bound["current_census_boundary"],
        "census_crossfield_compatibility": _census_debt(),
        "GVE_implementation_precedent_only": _precedent_boundary(),
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
        "determinism": {
            "source_derived_only": True,
            "UTF8": True,
            "LF": True,
            "single_final_LF": True,
            "dynamic_metadata_absent": True,
            "double_build_required": True,
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
    """Fail closed unless the four LCY metadata projections are exact."""

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
    if not rows or tuple(rows[0]) != MATRIX_HEADER:
        _fail("MATRIX_HEADER_INVALID")
    if artifacts[MATRIX] != _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot)):
        _fail("MATRIX_EXACT_PROJECTION_INVALID")
    if (
        len(rows) != 4
        or tuple(row["canonical_event_id"] for row in rows) != EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in rows) != EXPECTED_RANKS
        or len({row["canonical_event_id"] for row in rows}) != 4
        or any("3A2G" in row["canonical_event_id"] for row in rows)
    ):
        _fail("MATRIX_EXACT4_IDENTITY_INVALID")
    required_true = (
        "human_review_completed", "task_relevance_human_authority",
        "task_relevance_human_authoritative", "chemistry_known_positive",
        "chemistry_human_authority", "chemistry_human_authoritative",
        "task_domain_negative", "reactive_pair_human_decision_available",
        "reactive_pair_human_authoritative", "B3_present",
        "event_training_use_human_decision_available", "PRE_source_graph_present",
        "POST_source_evidence_available", "explicit_covalent_evidence",
        "projection_of_frozen_formal_human_authority", "metadata_only",
    )
    required_false = (
        "negative_chemistry", "positive_generative_supervision_eligible",
        "reusable_pair_rule_created", "cross_structure_regiochemistry_generalization",
        "role_partition_human_decision_available", "role_partition_human_authoritative",
        "reusable_role_authority", "sixth_task", "task_applicability_determined",
        "authoritative_task_labels_created", "event_task_label_rows_materialized",
        "training_use_allowed", "human_training_excluded",
        "candidate_for_future_training_admission", "future_training_admission_candidate",
        "training_admitted", "formal_training_admitted",
        "training_materialization_allowed_now", "training_materialization_allowed",
        "tensor_target_created", "model_supervision_usable",
        "training_mask_targets_available_now", "current_runtime_model_usable",
        "parameter_update_authorization", "READY_FOR_TRAINING",
        "PRE_topology_authority", "PRE_geometry_authority", "PRE_coordinates_authority",
        "PRE_reconstruction", "POST_to_PRE_copy", "PRE_zero_fill",
        "leaving_group_inferred", "reagent_inferred", "bond_edit_inferred",
        "distance_only_inference", "POST_geometry_training_authority",
        "POST_geometry_training_target_created",
        "POST_geometry_training_label_available_now", "reusable_chemistry_authority",
        "reaction_family_authority", "warhead_rule_authority", "warhead_type_authority",
        "reaction_family_training_class_target_available",
        "warhead_rule_training_class_target_available", "warhead_type_target_available",
        "reusable_authority_label_available", "new_human_authority_created_by_ingestion",
        "dataset_mutated", "training_dataset_changed", "tensorization",
        "loader_modified", "batch_modified", "model_forward", "loss", "backward",
        "optimizer", "parameter_update", "training",
    )
    for row in rows:
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["completed_lane"] != EXPECTED_COMPLETED_LANE
            or row["task_relevance"] != "NOT_RELEVANT"
            or row["human_task_relevance_decision"] != "NOT_RELEVANT"
            or row["chemistry"] != "POSITIVE"
            or row["human_chemistry_decision"] != "POSITIVE"
            or row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "C1"
            or row["pair_authority_scope"] != PAIR_AUTHORITY_SCOPE
            or row["selected_candidate_index_0based"] != "null"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or any(row[key] != "null" for key in (
                "warhead_atoms_json", "linker_atoms_json", "scaffold_atoms_json",
                "W_L_S_counts_json", "boundary_bonds_json",
                "direct_profile_applicable_task_ids_json",
            ))
            or row["global_canonical_task_count"] != "5"
            or [item["task_id"] for item in applicability] != [0, 1, 2, 3, 4]
            or any(item["structurally_applicable"] is not None for item in applicability)
            or any(item["training_mask_target_available_now"] for item in applicability)
            or row["formal_event_training_use_decision"] != "NOT_APPLICABLE"
            or row["training_exclusion_reason"] != ""
            or row["future_training_admission_status"] != ""
            or row["supporting_PRE_source_graph_count_per_event"] != "1"
            or row["PRE_source_graph_count_per_event"] != "1"
            or row["PRE_mapping_count_per_event"] != "0"
            or row["PRE_mapping_status"] != PRE_MAPPING_STATUS
            or row["PRE_status"] != PRE_STATUS
            or row["authority_source"] != AUTHORITY_SOURCE
            or any(row[key] != "true" for key in required_true)
            or any(row[key] != "false" for key in required_false)
        ):
            _fail("MATRIX_AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    sources = manifest.get("candidate_source_bindings")
    if type(sources) is not list or len(sources) != 3:
        _fail("CANDIDATE_SOURCE_BINDINGS_INVALID")
    expected_paths = [
        SOURCE_RELATIVE.as_posix(), CHECKER_RELATIVE.as_posix(), TEST_RELATIVE.as_posix()
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
    """Build deterministic bytes for the four authorized LCY artifacts."""

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
    descriptor, temporary = tempfile.mkstemp(prefix=".covapie_lcy_write_", dir=path.parent)
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
    """Write only the four artifacts under the authorized repository output root."""

    repo_root = Path(repo_root).resolve()
    destination = (
        repo_root / OUTPUT_ROOT_RELATIVE if target_root is None else Path(target_root)
    )
    _validate_materialization_destination_v1(repo_root, destination)
    destination.mkdir(parents=True, exist_ok=True)
    artifacts = build_artifacts_v1(repo_root)
    for name in OUTPUT_FILENAMES:
        _atomic_write(destination / name, artifacts[name])
    return artifacts


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    """Rebuild and compare all materialized LCY artifacts byte for byte."""

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
            raise LCYIngestionSafetyError(
                "COVAPIE_LCY_INGESTION_V1_ERROR:MATERIALIZED_READ_FAILED:" + name
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
