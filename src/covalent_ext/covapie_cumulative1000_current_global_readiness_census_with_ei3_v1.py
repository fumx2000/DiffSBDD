"""Cumulative1000 readiness census refreshed by the published EI3 Exact3.

This metadata-only successor reproduces the published with-ME7 census, consumes
the published EI3 reconciliation and its 81-column event matrix, and overlays
only the three approved EI3 events.  It does not create human, scientific,
reusable, task-label, tensor, admission, or training authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
import csv
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile
from typing import Any, NoReturn

from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import covapie_completed_human_decision_reconciliation_with_ei3_v1 as reconciliation_owner
from . import covapie_cumulative1000_current_global_readiness_census_with_me7_v1 as predecessor
from . import covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1 as ingestion
from .covapie_source_binding_policy_v2 import SourceBindingPolicyV2Error, verify_bound_source_v2


__all__ = (
    "Cumulative1000CurrentGlobalReadinessCensusWithEI3Error",
    "compute_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1",
    "validate_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1",
    "build_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1",
    "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1",
)

BASELINE_COMMIT = "75fe03bad8acd0816e0b0206fd541628888d7844"
SCHEMA_VERSION = "covapie_cumulative1000_current_global_readiness_census_with_ei3_v1"
STAGE = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_EI3_V1"
ERROR_TOKEN = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_EI3_V1_ERROR"

OUTPUT_DIRECTORY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_ei3_v1"
)
CENSUS_FILE = "covapie_cumulative1000_current_global_readiness_census_with_ei3_v1.csv"
SUMMARY_FILE = "covapie_cumulative1000_current_global_readiness_summary_with_ei3_v1.json"
MANIFEST_FILE = "covapie_cumulative1000_current_global_readiness_manifest_with_ei3_v1.json"
PRODUCTION_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_with_ei3_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1.py"
)
GUIDE_RELATIVE = Path(
    "docs/covapie_cumulative1000_current_global_readiness_census_with_ei3_v1_guide.md"
)
EXACT7_PATHS_V1 = (
    PRODUCTION_RELATIVE.as_posix(),
    CHECKER_RELATIVE.as_posix(),
    TEST_RELATIVE.as_posix(),
    GUIDE_RELATIVE.as_posix(),
    (OUTPUT_DIRECTORY_RELATIVE / CENSUS_FILE).as_posix(),
    (OUTPUT_DIRECTORY_RELATIVE / SUMMARY_FILE).as_posix(),
    (OUTPUT_DIRECTORY_RELATIVE / MANIFEST_FILE).as_posix(),
)

CENSUS_COLUMNS_V1 = predecessor.CENSUS_COLUMNS_V1
CANONICAL_EXACT5_V1 = predecessor.CANONICAL_EXACT5_V1
base = predecessor.base
historical = predecessor.predecessor

EI3_EXACT3_EVENT_IDS_V1 = ingestion.EXPECTED_EVENT_IDS
EI3_EXACT3_RANKS_V1 = ingestion.EXPECTED_RANKS
EI3_REVIEW_UNIT_ID_V1 = ingestion.EXPECTED_REVIEW_UNIT_ID
EI3_HUMAN_DECISION_SOURCE = ingestion.FORMAL_DECISION_RELATIVE.as_posix()
EI3_EVENT_MATRIX_RELATIVE = ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MATRIX
EI3_EVENT_MATRIX_SOURCE = EI3_EVENT_MATRIX_RELATIVE.as_posix()

PREDECESSOR_OWNER_RELATIVE = predecessor.PRODUCTION_RELATIVE
PREDECESSOR_CENSUS_RELATIVE = predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.CENSUS_FILE
PREDECESSOR_SUMMARY_RELATIVE = predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.SUMMARY_FILE
PREDECESSOR_MANIFEST_RELATIVE = predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.MANIFEST_FILE
EI3_RECONCILIATION_OWNER_RELATIVE = reconciliation_owner.SOURCE_RELATIVE
EI3_RECONCILIATION_ARTIFACT_RELATIVE = reconciliation_owner.OUTPUT_RELATIVE
EI3_INGESTION_OWNER_RELATIVE = ingestion.SOURCE_RELATIVE
PRIORITY_QUEUE_RELATIVE = predecessor.PRIORITY_QUEUE_RELATIVE

NEXT_PENDING_REVIEW_UNIT_ID_V1 = "COVAPIE_BULK_REVIEW_UNIT_7FB64BA2D198B24F"
NEXT_PENDING_EVENT_COUNT_V1 = 3
NEXT_PENDING_RAW_PRIORITY_RANK_V1 = 34
NEXT_PENDING_PDB_IDS_V1 = ("2A5I", "2A5K")

_AUTHORIZED_EI3_OVERLAY_FIELDS_V1 = frozenset(
    {
        "current_global_status",
        "current_review_status",
        "human_review_completed",
        "human_review_authority_source",
        "chemistry_disposition",
        "chemistry_authority_source",
        "positive_authority_source",
        "task_relevance_disposition",
        "task_relevance_authority_source",
        "training_use_disposition",
        "human_training_excluded",
        "reactive_pair_sample_authoritative",
        "role_partition_sample_authoritative",
        "role_profile",
        "canonical_mask_structural_labels_available",
        "structurally_applicable_task_ids_json",
        "training_use_include",
        "future_training_admission_candidate",
        "training_materialization_allowed_current_source",
    }
)
_AUTHORIZED_BUT_UNCHANGED_EI3_FIELDS_V1 = frozenset(
    {
        "human_training_excluded",
        "role_partition_sample_authoritative",
        "role_profile",
        "canonical_mask_structural_labels_available",
        "structurally_applicable_task_ids_json",
        "training_use_include",
        "future_training_admission_candidate",
    }
)
_ACTUAL_CHANGED_EI3_FIELDS_V1 = (
    _AUTHORIZED_EI3_OVERLAY_FIELDS_V1 - _AUTHORIZED_BUT_UNCHANGED_EI3_FIELDS_V1
)

_EXPECTED_REFRESHED_CENSUS_SHA256_V1: str | None = (
    "459c92f27883d9d47fc5d5c6ccdb6969943f9fcf9194da0399900cd06e3f2966"
)
_EXPECTED_REFRESHED_SUMMARY_SHA256_V1: str | None = (
    "0180f217680bdd6c55821ca7d9128395a34a5d7e2cb149e883cd89689b2a8b46"
)
_EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1: str | None = (
    "4061900a08ba8c424b43b8575bce8cf44bd7c59c9526d2855aa49069ae9f8782"
)

_SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_ADDITIVE_SOURCE_SPECS_V1 = (
    (
        "PREDECESSOR_WITH_ME7_CENSUS_OWNER",
        PREDECESSOR_OWNER_RELATIVE,
        "repository_relative",
        67017,
        "05ea1c40eff023336f47b9e5755d145f6060348c6104e361f71810d8c32a8bc5",
        False,
    ),
    (
        "PREDECESSOR_WITH_ME7_MATERIALIZED_CENSUS",
        PREDECESSOR_CENSUS_RELATIVE,
        "repository_relative",
        559446,
        "9e45211a66a003be7f5f8c8b49b0a7f6f22bce362a06601708affff6a0ce4b4a",
        False,
    ),
    (
        "PREDECESSOR_WITH_ME7_MATERIALIZED_SUMMARY",
        PREDECESSOR_SUMMARY_RELATIVE,
        "repository_relative",
        23857,
        "3d2d887490f92c0bd447ecb76707ee0b403ebfd3a52630c4150d525059b81d45",
        False,
    ),
    (
        "EI3_RECONCILIATION_OWNER",
        EI3_RECONCILIATION_OWNER_RELATIVE,
        "repository_relative",
        51350,
        "dd9477ad99347a0efbdb5c78d1b8353aebb1477215bd189b32fe4a8d6e612062",
        False,
    ),
    (
        "EI3_INGESTION_OWNER",
        EI3_INGESTION_OWNER_RELATIVE,
        "repository_relative",
        107409,
        "5a1e9be0e9d0791c021c4e9f173c49a2f273bbb42ddb7a0fe24b4be1d62f3d33",
        False,
    ),
    (
        "EI3_EVENT_TASK_LABEL_AVAILABILITY",
        EI3_EVENT_MATRIX_RELATIVE,
        "repository_relative",
        4847,
        "e5a80902f1b4ffc887b2f99d642cf82c6c6acb77c52f0a78ae1960282ec67238",
        False,
    ),
)
_PREDECESSOR_MANIFEST_SPEC_V1 = (
    90766,
    "7c2a53db1628845980b9742f54f4ec1d49b263bbc53e7f902200df8a5cf900e5",
    False,
)
_EI3_RECONCILIATION_ARTIFACT_SPEC_V1 = (
    354873,
    "e7d316e71d4c6caca60dfc36c2df872770f64894324f087d709d2118c552f5f5",
    False,
)
_PRIORITY_QUEUE_SPEC_V1 = (
    50116,
    "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2",
    False,
)
_QUEUE_HEADER_V1 = predecessor._QUEUE_HEADER_V1


class Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(ValueError):
    """Raised unless the EI3 census is exactly source-derived."""


def _fail(reason: str) -> NoReturn:
    raise Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(
        f"{ERROR_TOKEN}:{reason}"
    )


_sha256 = predecessor._sha256
_canonical_json = predecessor._canonical_json
_json_bytes = predecessor._json_bytes
_event_set_sha256 = predecessor._event_set_sha256
_csv_bytes = predecessor._csv_bytes


def _read_regular_file(path: Path, label: str) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(
            f"{ERROR_TOKEN}:SOURCE_READ_FAILED:{label}"
        ) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail("SOURCE_NOT_REGULAR_FILE:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(
            f"{ERROR_TOKEN}:SOURCE_READ_FAILED:{label}"
        ) from error


def _verify_bound(
    root: Path,
    role: str,
    relative: Path,
    namespace: str,
    byte_count: int,
    sha256: str,
    executable: bool,
) -> bytes:
    path = root / relative if namespace == "repository_relative" else root.parent / relative
    try:
        return verify_bound_source_v2(
            path=path,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=role + ":" + relative.as_posix(),
            expected_executable=executable,
        )
    except SourceBindingPolicyV2Error as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(
            f"{ERROR_TOKEN}:BOUND_SOURCE_REJECTED:{role}"
        ) from error


def _baseline_blob(root: Path, relative: Path, label: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{BASELINE_COMMIT}:{relative.as_posix()}"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0 or completed.stderr:
        _fail("BASELINE_GIT_BLOB_READ_FAILED:" + label)
    return completed.stdout


def _verify_repository_blob(root: Path, relative: Path, expected: bytes, label: str) -> None:
    if _baseline_blob(root, relative, label) != expected:
        _fail("WORKING_BYTES_NOT_BASELINE_GIT_BLOB:" + label)


def _verify_additive_sources(root: Path) -> tuple[dict[str, object], ...]:
    bindings: list[dict[str, object]] = []
    for role, relative, namespace, byte_count, digest, executable in _ADDITIVE_SOURCE_SPECS_V1:
        payload = _verify_bound(
            root, role, relative, namespace, byte_count, digest, executable
        )
        if namespace == "repository_relative":
            _verify_repository_blob(root, relative, payload, role)
        bindings.append(
            {
                "artifact_role": role,
                "path": relative.as_posix(),
                "path_namespace": namespace,
                "byte_count": byte_count,
                "sha256": digest,
                "expected_executable": executable,
            }
        )
    return tuple(bindings)


def _verify_validation_identities(root: Path) -> None:
    for role, relative, spec in (
        (
            "PREDECESSOR_WITH_ME7_MANIFEST",
            PREDECESSOR_MANIFEST_RELATIVE,
            _PREDECESSOR_MANIFEST_SPEC_V1,
        ),
        (
            "EI3_RECONCILIATION_ARTIFACT_VALIDATION_IDENTITY",
            EI3_RECONCILIATION_ARTIFACT_RELATIVE,
            _EI3_RECONCILIATION_ARTIFACT_SPEC_V1,
        ),
        ("FROZEN_PRIORITY_QUEUE", PRIORITY_QUEUE_RELATIVE, _PRIORITY_QUEUE_SPEC_V1),
    ):
        payload = _verify_bound(
            root, role, relative, "repository_relative", *spec
        )
        _verify_repository_blob(root, relative, payload, role)


def _verify_predecessor(
    root: Path,
) -> base.Cumulative1000CurrentGlobalReadinessComputationV1:
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_me7_v1(
        root
    )
    census_payload = _read_regular_file(root / PREDECESSOR_CENSUS_RELATIVE, "PREDECESSOR_CENSUS")
    summary_payload = _read_regular_file(root / PREDECESSOR_SUMMARY_RELATIVE, "PREDECESSOR_SUMMARY")
    manifest_payload = _read_regular_file(root / PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_MANIFEST")
    try:
        manifest = json.loads(manifest_payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(
            f"{ERROR_TOKEN}:PREDECESSOR_MANIFEST_JSON_INVALID"
        ) from error
    if (
        len(frozen.rows) != 1000
        or len(CENSUS_COLUMNS_V1) != 47
        or _csv_bytes(frozen.rows) != census_payload
        or _json_bytes(frozen.summary) != summary_payload
        or manifest.get("semantic_source_binding_count") != 198
        or manifest.get("semantic_source_bindings")
        != list(frozen.semantic_source_bindings)
        or manifest.get("output_bindings_excluding_manifest_self")
        != [
            {
                "artifact_role": "REFRESHED_CENSUS_CSV",
                "path": PREDECESSOR_CENSUS_RELATIVE.as_posix(),
                "byte_count": len(census_payload),
                "sha256": _sha256(census_payload),
            },
            {
                "artifact_role": "REFRESHED_SUMMARY_JSON",
                "path": PREDECESSOR_SUMMARY_RELATIVE.as_posix(),
                "byte_count": len(summary_payload),
                "sha256": _sha256(summary_payload),
            },
        ]
        or manifest.get("manifest_self_SHA256_recorded") is not False
    ):
        _fail("PREDECESSOR_COMPUTATION_OR_MATERIALIZED_OUTPUT_DRIFT")
    repository_paths = {
        Path(item["path"])
        for item in frozen.semantic_source_bindings
        if item.get("path_namespace") == "repository_relative"
    }
    for relative in sorted(repository_paths):
        payload = _read_regular_file(root / relative, "PREDECESSOR_BINDING:" + relative.as_posix())
        _verify_repository_blob(root, relative, payload, "PREDECESSOR_BINDING:" + relative.as_posix())
    return frozen


def _validate_ei3_matrix_rows_v1(
    rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    normalized = tuple(dict(row) for row in rows)
    required = {
        "pair_sample_authority",
        "target_covalent_connection_count",
        "metal_context_connection_count",
        "role_partition_sample_authoritative",
        "role_profile_raw_json",
        "role_profile_derived_state",
        "task_applicability_sample_authoritative",
        "canonical_mask_structural_labels_available",
        "structurally_applicable_task_ids_json",
        "training_disposition",
        "human_training_excluded",
        "future_training_admission_candidate",
        "training_materialization_allowed",
    }
    forbidden = {
        "role_sample_authority",
        "task_applicability_sample_authority",
        "role_profile",
        "training_use_allowed",
    }
    if (
        len(ingestion.MATRIX_HEADER) != 81
        or len(normalized) != 3
        or any(tuple(row) != ingestion.MATRIX_HEADER for row in normalized)
        or not required.issubset(ingestion.MATRIX_HEADER)
        or not forbidden.isdisjoint(ingestion.MATRIX_HEADER)
        or tuple(row["canonical_event_id"] for row in normalized)
        != EI3_EXACT3_EVENT_IDS_V1
        or tuple(int(row["scaleup_rank"]) for row in normalized)
        != EI3_EXACT3_RANKS_V1
        or len({row["canonical_event_id"] for row in normalized}) != 3
    ):
        _fail("EI3_EVENT_MATRIX_IDENTITY_NOT_EXACT3_X_81")
    expected_pdbs = tuple(event[2] for event in ingestion.EXPECTED_EVENTS)
    expected_metal_counts = ("0", "0", "2")
    nullable_fields = (
        "selected_role_candidate_json",
        "role_profile_raw_json",
        "warhead_atom_ids_json",
        "linker_atom_ids_json",
        "scaffold_atom_ids_json",
        "minimal_seed_json",
        "minimal_seed_atom_ids_json",
        "primary_anchor_json",
        "structurally_applicable_task_ids_json",
    )
    for row, pdb_id, metal_count in zip(
        normalized, expected_pdbs, expected_metal_counts, strict=True
    ):
        event_id = row["canonical_event_id"]
        expected_cells = {
            "review_unit_id": EI3_REVIEW_UNIT_ID_V1,
            "pdb_id": pdb_id,
            "human_review_completed": "true",
            "D4_formally_answered": "true",
            "D5_formally_answered": "true",
            "legacy_completed_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
            "source_formal_D2": "OUT_OF_DOMAIN",
            "normalized_task_relevance_disposition": generic.TASK_NOT_RELEVANT,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "negative_chemistry": "false",
            "task_domain_negative": "true",
            "pair_sample_authority": "true",
            "target_covalent_connection_count": "1",
            "metal_context_connection_count": metal_count,
            "role_candidate_count": "0",
            "source_formal_D4": "CANNOT_DETERMINE",
            "role_profile_raw_json": "null",
            "role_profile_derived_state": base.ROLE_NOT_ESTABLISHED,
            "role_partition_sample_authoritative": "false",
            "minimal_seed_sample_authoritative": "false",
            "role_runtime_executed": "false",
            "seed_runtime_executed": "false",
            "structurally_applicable_task_ids_json": "null",
            "task_applicability_sample_authoritative": "false",
            "task_runtime_executed": "false",
            "canonical_task_count": "5",
            "B3_present": "true",
            "sixth_task": "false",
            "canonical_mask_structural_labels_available": "false",
            "task_label_authority": "false",
            "event_task_label_rows_materialized": "false",
            "mask_tensor_targets_created": "false",
            "source_formal_D6": "NOT_APPLICABLE",
            "training_disposition": generic.TRAINING_NOT_APPLICABLE,
            "human_training_excluded": "false",
            "future_training_admission_candidate": "false",
            "formal_training_admitted": "false",
            "training_materialization_allowed": "false",
            "PRE_authority": "false",
            "POST_to_PRE_copy": "false",
            "PRE_zero_fill": "false",
            "accurate_PRE_required_before_training_feature_contract": "false",
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": "false",
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": "true",
            "READY_FOR_TRAINING": "false",
            "TRAINING_STARTED": "false",
        }
        if any(row[key] != value for key, value in expected_cells.items()):
            _fail("EI3_EVENT_MATRIX_SEMANTICS_INVALID:" + event_id)
        try:
            nullable_values = [json.loads(row[field]) for field in nullable_fields]
        except json.JSONDecodeError as error:
            raise Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(
                f"{ERROR_TOKEN}:EI3_MATRIX_JSON_INVALID:{event_id}"
            ) from error
        if any(value is not None for value in nullable_values):
            _fail("EI3_UNKNOWN_ROLE_OR_TASK_IDS_NOT_JSON_NULL:" + event_id)
    if (
        len(ingestion.CANONICAL_TASKS) != 5
        or tuple(item[1] for item in ingestion.CANONICAL_TASKS)
        != tuple(item[1] for item in CANONICAL_EXACT5_V1)
        or ingestion.CANONICAL_TASKS[3][2] != "B3"
    ):
        _fail("EI3_CANONICAL_EXACT5_BOUNDARY_INVALID")
    return normalized


def _load_and_validate_ei3_event_matrix_v1(root: Path) -> tuple[dict[str, str], ...]:
    payload = _verify_bound(
        root,
        "EI3_EVENT_TASK_LABEL_AVAILABILITY",
        EI3_EVENT_MATRIX_RELATIVE,
        "repository_relative",
        4847,
        "e5a80902f1b4ffc887b2f99d642cf82c6c6acb77c52f0a78ae1960282ec67238",
        False,
    )
    _verify_repository_blob(
        root, EI3_EVENT_MATRIX_RELATIVE, payload, "EI3_EVENT_TASK_LABEL_AVAILABILITY"
    )
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(
            f"{ERROR_TOKEN}:EI3_EVENT_MATRIX_NOT_UTF8"
        ) from error
    if tuple(reader.fieldnames or ()) != ingestion.MATRIX_HEADER:
        _fail("EI3_EVENT_MATRIX_HEADER_INVALID")
    return _validate_ei3_matrix_rows_v1(tuple(dict(row) for row in reader))


def _validate_ei3_reconciliation_v1(root: Path) -> generic.ReconciliationResult:
    result = reconciliation_owner.reconcile_real_completed_human_decisions_with_ei3_v1(root)
    expected_summary = {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 127,
        "completed_positive_unit_count": 21,
        "completed_negative_event_count": 54,
        "completed_negative_unit_count": 12,
        "completed_total_event_count": 181,
        "completed_total_unit_count": 33,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 157,
        "unreviewed_unit_count": 98,
    }
    if (
        result.review_summary != expected_summary
        or len(result.reconciled_rows) != 338
        or len(result.source_bindings) != 29
        or len(result.normalized_facts) != 157
        or len({binding.stable_identity for binding in result.source_bindings}) != 29
        or reconciliation_owner.PREDECESSOR_COVERAGE_SUMMARY["accepted_fact_count"] != 154
        or reconciliation_owner.SUCCESSOR_COVERAGE_SUMMARY["accepted_fact_count"] != 157
    ):
        _fail("EI3_RECONCILIATION_EXACT29_157_INVALID")
    target = set(EI3_EXACT3_EVENT_IDS_V1)
    facts = [fact for fact in result.normalized_facts if fact.canonical_event_id in target]
    if len(facts) != 3 or any(
        fact.review_unit_id != EI3_REVIEW_UNIT_ID_V1
        or fact.human_review_completed is not True
        or fact.legacy_completed_review_status != generic.COMPLETED_HUMAN_NEGATIVE
        or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
        or fact.human_training_excluded is not False
        or fact.source_binding_path != EI3_HUMAN_DECISION_SOURCE
        for fact in facts
    ):
        _fail("EI3_RECONCILIATION_EXACT3_POSITIVE_NOT_APPLICABLE_INVALID")
    target_rows = [
        row for row in result.reconciled_rows if row["canonical_event_id"] in target
    ]
    if len(target_rows) != 3 or any(
        row["current_review_status"] != generic.COMPLETED_HUMAN_NEGATIVE
        or row["raw_review_unit_id"] != EI3_REVIEW_UNIT_ID_V1
        for row in target_rows
    ):
        _fail("EI3_RECONCILIATION_TARGET_STATUS_INVALID")
    return result


def _assert_predecessor_ei3_state_v1(
    computation: base.Cumulative1000CurrentGlobalReadinessComputationV1,
    root: Path,
) -> None:
    if (
        len(computation.rows) != 1000
        or len(CENSUS_COLUMNS_V1) != 47
        or _csv_bytes(computation.rows)
        != _read_regular_file(root / PREDECESSOR_CENSUS_RELATIVE, "PREDECESSOR_CENSUS")
    ):
        _fail("PREDECESSOR_WITH_ME7_CENSUS_IDENTITY_INVALID")
    target = set(EI3_EXACT3_EVENT_IDS_V1)
    rows = [row for row in computation.rows if row["canonical_event_id"] in target]
    expected = {
        "ligand_component_id": "EI3",
        "current_global_status": generic.CURRENTLY_UNREVIEWED,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "human_review_completed": "false",
        "chemistry_disposition": base.CHEMISTRY_UNRESOLVED,
        "task_relevance_disposition": base.TASK_UNRESOLVED,
        "training_use_disposition": base.TRAINING_UNRESOLVED,
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "role_profile": base.ROLE_NOT_ESTABLISHED,
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
        "training_use_include": "false",
        "human_training_excluded": "false",
        "future_training_admission_candidate": "false",
        "training_materialization_allowed_current_source": "",
    }
    if (
        len(rows) != 3
        or tuple(row["canonical_event_id"] for row in rows) != EI3_EXACT3_EVENT_IDS_V1
        or tuple(int(row["scaleup_rank"]) for row in rows) != EI3_EXACT3_RANKS_V1
        or tuple(row["pdb_id"] for row in rows) != ("5ARB", "5ARC", "5ARD")
        or any(row["review_unit_id"] != EI3_REVIEW_UNIT_ID_V1 for row in rows)
        or any(any(row[key] != value for key, value in expected.items()) for row in rows)
    ):
        _fail("PREDECESSOR_EI3_EXACT3_STATE_INVALID")


def _overlay_ei3_exact3_v1(
    predecessor_rows: Sequence[Mapping[str, str]],
    matrix_rows: Sequence[Mapping[str, str]],
    reconciliation: generic.ReconciliationResult,
) -> tuple[dict[str, str], ...]:
    matrix_by_event = {
        row["canonical_event_id"]: row
        for row in _validate_ei3_matrix_rows_v1(matrix_rows)
    }
    facts = {
        fact.canonical_event_id: fact
        for fact in reconciliation.normalized_facts
        if fact.canonical_event_id in matrix_by_event
    }
    if set(facts) != set(EI3_EXACT3_EVENT_IDS_V1):
        _fail("EI3_RECONCILIATION_MATRIX_IDENTITY_MISMATCH")
    rows = deepcopy([dict(row) for row in predecessor_rows])
    for row in rows:
        event_id = row["canonical_event_id"]
        if event_id not in matrix_by_event:
            continue
        matrix = matrix_by_event[event_id]
        fact = facts[event_id]
        if (
            row["scaleup_rank"] != matrix["scaleup_rank"]
            or row["pdb_id"] != matrix["pdb_id"]
            or row["review_unit_id"] != EI3_REVIEW_UNIT_ID_V1
        ):
            _fail("EI3_MATRIX_PREDECESSOR_IDENTITY_MISMATCH:" + event_id)
        training_include = matrix["training_disposition"] == generic.TRAINING_INCLUDE
        row.update(
            {
                "current_global_status": fact.legacy_completed_review_status,
                "current_review_status": fact.legacy_completed_review_status,
                "human_review_completed": "true",
                "human_review_authority_source": fact.source_binding_path,
                "chemistry_disposition": fact.chemistry_disposition,
                "chemistry_authority_source": EI3_EVENT_MATRIX_SOURCE,
                "positive_authority_source": EI3_EVENT_MATRIX_SOURCE,
                "task_relevance_disposition": fact.task_relevance_disposition,
                "task_relevance_authority_source": EI3_EVENT_MATRIX_SOURCE,
                "training_use_disposition": fact.training_disposition,
                "human_training_excluded": matrix["human_training_excluded"],
                "reactive_pair_sample_authoritative": matrix["pair_sample_authority"],
                "role_partition_sample_authoritative": matrix[
                    "role_partition_sample_authoritative"
                ],
                "role_profile": matrix["role_profile_derived_state"],
                "canonical_mask_structural_labels_available": matrix[
                    "canonical_mask_structural_labels_available"
                ],
                "structurally_applicable_task_ids_json": matrix[
                    "structurally_applicable_task_ids_json"
                ],
                "training_use_include": str(training_include).lower(),
                "future_training_admission_candidate": matrix[
                    "future_training_admission_candidate"
                ],
                "training_materialization_allowed_current_source": matrix[
                    "training_materialization_allowed"
                ],
            }
        )
    return tuple(rows)


def _top_pending_review_units_v1(
    root: Path, reconciliation: generic.ReconciliationResult
) -> list[dict[str, object]]:
    payload = _verify_bound(
        root,
        "FROZEN_PRIORITY_QUEUE",
        PRIORITY_QUEUE_RELATIVE,
        "repository_relative",
        *_PRIORITY_QUEUE_SPEC_V1,
    )
    _verify_repository_blob(root, PRIORITY_QUEUE_RELATIVE, payload, "FROZEN_PRIORITY_QUEUE")
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    queue_rows = [dict(row) for row in reader]
    if tuple(reader.fieldnames or ()) != _QUEUE_HEADER_V1 or len(queue_rows) != 131:
        _fail("PRIORITY_QUEUE_IDENTITY_INVALID")
    statuses: dict[str, set[str]] = defaultdict(set)
    events: dict[str, list[str]] = defaultdict(list)
    for row in reconciliation.reconciled_rows:
        unit = row["raw_review_unit_id"]
        statuses[unit].add(row["current_review_status"])
        events[unit].append(row["canonical_event_id"])
    candidates: list[tuple[int, int, str, dict[str, str], str]] = []
    for row in queue_rows:
        unit = row["review_unit_id"]
        unit_statuses = statuses.get(unit)
        if unit_statuses is None or len(unit_statuses) != 1:
            _fail("PRIORITY_QUEUE_UNIT_STATUS_INVALID:" + unit)
        if json.loads(row["canonical_event_ids_json"]) != events[unit]:
            _fail("PRIORITY_QUEUE_EVENT_SET_OR_ORDER_INVALID:" + unit)
        status_value = next(iter(unit_statuses))
        if status_value in {generic.CURRENTLY_UNREVIEWED, generic.CURRENTLY_IN_PROGRESS}:
            candidates.append(
                (-int(row["event_count"]), int(row["priority_rank"]), unit, row, status_value)
            )
    candidates.sort(key=lambda item: item[:3])
    if len(candidates) != 98 or any(
        unit == EI3_REVIEW_UNIT_ID_V1 for _n, _p, unit, _row, _status in candidates
    ):
        _fail("CURRENT_PENDING_REVIEW_UNIT_SET_INVALID")
    top: list[dict[str, object]] = []
    for rank, (_negative, _priority, unit, row, status_value) in enumerate(
        candidates[:10], 1
    ):
        top.append(
            {
                "rank": rank,
                "raw_priority_rank": int(row["priority_rank"]),
                "review_unit_id": unit,
                "event_count": int(row["event_count"]),
                "pdb_ids": json.loads(row["pdb_ids_json"]),
                "ligand_component_ids": json.loads(row["ligand_component_ids_json"]),
                "full_coordinate_count": int(row["full_coordinate_event_count"]),
                "exact_pair_count": int(row["exact_reactive_pair_event_count"]),
                "ccd_complete_count": int(row["CCD_graph_complete_event_count"]),
                "post_source_evidence_count": int(row["POST_geometry_available_event_count"]),
                "current_review_status": status_value,
            }
        )
    expected_next = {
        "rank": 1,
        "raw_priority_rank": NEXT_PENDING_RAW_PRIORITY_RANK_V1,
        "review_unit_id": NEXT_PENDING_REVIEW_UNIT_ID_V1,
        "event_count": NEXT_PENDING_EVENT_COUNT_V1,
        "pdb_ids": list(NEXT_PENDING_PDB_IDS_V1),
        "ligand_component_ids": ["AZP"],
        "full_coordinate_count": 3,
        "exact_pair_count": 3,
        "ccd_complete_count": 3,
        "post_source_evidence_count": 3,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
    }
    if not top or top[0] != expected_next:
        _fail("NEXT_PENDING_SOURCE_DRIFT")
    return top


def _event_set(rows: Sequence[Mapping[str, str]], field: str, value: str) -> set[str]:
    return {row["canonical_event_id"] for row in rows if row[field] == value}


def _build_summary_v1(
    rows: Sequence[Mapping[str, str]], top_pending: list[dict[str, object]]
) -> dict[str, Any]:
    summary = deepcopy(predecessor._build_summary_v1(rows, top_pending))
    chemistry_positive = _event_set(rows, "chemistry_disposition", base.CHEMISTRY_POSITIVE)
    training_include = _event_set(rows, "training_use_disposition", generic.TRAINING_INCLUDE)
    training_exclude = _event_set(rows, "training_use_disposition", generic.TRAINING_EXCLUDE)
    positive_rows = [row for row in rows if row["canonical_event_id"] in chemistry_positive]
    missing_tensor_rows = [
        row
        for row in positive_rows
        if row["reactive_pair_training_target_available"] == "false"
    ]
    orthogonal = {
        row["canonical_event_id"]
        for row in rows
        if (
            row["task_relevance_disposition"],
            row["chemistry_disposition"],
            row["training_use_disposition"],
        )
        == (
            generic.TASK_NOT_RELEVANT,
            generic.CHEMISTRY_POSITIVE,
            generic.TRAINING_NOT_APPLICABLE,
        )
    }
    historical_orthogonal = (
        set(historical.GVE_EXACT4_EVENT_IDS_V1)
        | set(historical.LCY_EXACT4_EVENT_IDS_V1)
        | set(historical.ZERO_D8_EXACT4_EVENT_IDS_V1)
        | set(historical.TP2_EXACT4_EVENT_IDS_V1)
        | set(historical.SIX_OA_EXACT4_EVENT_IDS_V1)
        | set(predecessor.ME7_EXACT3_EVENT_IDS_V1)
    )
    summary["schema_version"] = SCHEMA_VERSION
    summary["stage"] = STAGE
    summary["refresh_delta"] = {
        "frozen_predecessor_positive_count": 167,
        "EI3_exact3_positive_delta_count": 3,
        "refreshed_positive_count": len(chemistry_positive),
        "frozen_predecessor_training_include_count": 68,
        "EI3_training_include_delta_count": 0,
        "refreshed_training_include_count": len(training_include),
        "frozen_predecessor_training_exclude_count": 76,
        "EI3_training_exclude_delta_count": 0,
        "refreshed_training_exclude_count": len(training_exclude),
        "frozen_predecessor_training_not_applicable_count": 113,
        "EI3_training_not_applicable_delta_count": 3,
        "refreshed_training_not_applicable_count": 116,
        "frozen_predecessor_future_candidate_count": 51,
        "EI3_future_candidate_delta_count": 0,
        "refreshed_future_candidate_count": sum(
            row["future_training_admission_candidate"] == "true" for row in rows
        ),
        "changed_event_count": 3,
        "non_target_changed_event_count": 0,
        "unchanged_event_count": 997,
        "derived_refresh_not_new_authority": True,
    }
    summary["chemistry"]["positive_source_composition"]["EI3"] = sum(
        row["positive_authority_source"] == EI3_EVENT_MATRIX_SOURCE for row in rows
    )
    summary["reactive_pair"].update(
        {
            "ei3_sample_authority_contribution_count": sum(
                row["positive_authority_source"] == EI3_EVENT_MATRIX_SOURCE
                and row["reactive_pair_sample_authoritative"] == "true"
                for row in rows
            ),
            "ei3_training_target_contribution_count": sum(
                row["positive_authority_source"] == EI3_EVENT_MATRIX_SOURCE
                and row["reactive_pair_training_target_available"] == "true"
                for row in rows
            ),
        }
    )
    summary["blockers"]["missing_tensor_integration"]["missing_source_composition"][
        "EI3"
    ] = sum(
        row["positive_authority_source"] == EI3_EVENT_MATRIX_SOURCE
        for row in missing_tensor_rows
    )
    summary["orthogonal_task_negative_chemistry_positive"] = {
        "task_negative_chemistry_positive_population_count": len(orthogonal),
        "historical_exact23_population_count": len(historical_orthogonal),
        "ei3_orthogonal_population_count": len(set(EI3_EXACT3_EVENT_IDS_V1) & orthogonal),
        "population_equals_historical_exact23_union_ei3_exact3": orthogonal
        == historical_orthogonal | set(EI3_EXACT3_EVENT_IDS_V1),
        "gve_orthogonal_population_count": len(
            set(historical.GVE_EXACT4_EVENT_IDS_V1) & orthogonal
        ),
        "lcy_orthogonal_population_count": len(
            set(historical.LCY_EXACT4_EVENT_IDS_V1) & orthogonal
        ),
        "0d8_orthogonal_population_count": len(
            set(historical.ZERO_D8_EXACT4_EVENT_IDS_V1) & orthogonal
        ),
        "tp2_orthogonal_population_count": len(
            set(historical.TP2_EXACT4_EVENT_IDS_V1) & orthogonal
        ),
        "6oa_orthogonal_population_count": len(
            set(historical.SIX_OA_EXACT4_EVENT_IDS_V1) & orthogonal
        ),
        "me7_orthogonal_population_count": len(
            set(predecessor.ME7_EXACT3_EVENT_IDS_V1) & orthogonal
        ),
        "pyr_orthogonal_population_count": len(
            set(historical.PYR_EXACT4_EVENT_IDS_V1) & orthogonal
        ),
    }
    boundary = summary["authority_boundary"]
    next_pending = top_pending[0]
    boundary.update(
        {
            "next_priority_review_unit": next_pending["review_unit_id"],
            "next_priority_review_ligand": next_pending["ligand_component_ids"][0],
            "next_priority_review_pdb_ids": list(next_pending["pdb_ids"]),
            "next_priority_review_event_count": next_pending["event_count"],
            "next_priority_review_current_pending_rank": next_pending["rank"],
            "next_priority_review_raw_priority_rank": next_pending["raw_priority_rank"],
            "EI3_REVIEW_STATE_CREATED": True,
            "EI3_REVIEW_COMPLETED": True,
            "EI3_RECONCILIATION_CONSUMED": True,
            "EI3_CENSUS_SOURCE_BINDING_V2_CLEAN_FROM_BIRTH": True,
            "review_state_created_by_this_refresh": False,
            "NEW_HUMAN_AUTHORITY_CREATED": False,
            "NEW_SCIENTIFIC_AUTHORITY_CREATED": False,
            "NEW_REUSABLE_AUTHORITY_CREATED": False,
            "TASK_LABEL_AUTHORITY": False,
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
            "MASK_TENSOR_TARGETS_CREATED": False,
            "FORMAL_TRAINING_ADMITTED": False,
            "TRAINING_MATERIALIZATION_ALLOWED": False,
            "READY_FOR_TRAINING": False,
            "READY_FOR_FORMAL_TRAINING": False,
            "TRAINING_STARTED": False,
            "QUEUE_REFRESH": False,
            "QUEUE_REFRESH_PERFORMED": False,
            "NEXT_REVIEW_STARTED": False,
            "next_review_started": False,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
            "derived_refresh_not_new_authority": True,
            "formal_decision_read_directly": False,
            "formal_decision_bound_directly": False,
            "formal_validator_executed": False,
        }
    )
    return summary


def _merge_semantic_bindings_v1(
    predecessor_bindings: Sequence[Mapping[str, object]],
    additive_bindings: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    merged = tuple(dict(item) for item in (*predecessor_bindings, *additive_bindings))
    identities = [(item["path_namespace"], item["path"]) for item in merged]
    predecessor_roles = {item["artifact_role"] for item in predecessor_bindings}
    additive_roles = [item["artifact_role"] for item in additive_bindings]
    if (
        len(predecessor_bindings) != 198
        or len(additive_bindings) != 6
        or len(merged) != 204
        or len(set(identities)) != 204
        or len(additive_roles) != len(set(additive_roles))
        or predecessor_roles & set(additive_roles)
    ):
        _fail("SEMANTIC_SOURCE_BINDING_COLLISION_OR_COUNT_INVALID")
    return merged


def _compute_components_v1(
    repo_root: Path,
) -> tuple[
    base.Cumulative1000CurrentGlobalReadinessComputationV1,
    base.Cumulative1000CurrentGlobalReadinessComputationV1,
    generic.ReconciliationResult,
    tuple[dict[str, str], ...],
]:
    root = Path(repo_root).resolve()
    additive = _verify_additive_sources(root)
    _verify_validation_identities(root)
    frozen = _verify_predecessor(root)
    _assert_predecessor_ei3_state_v1(frozen, root)
    reconciliation = _validate_ei3_reconciliation_v1(root)
    matrix_rows = _load_and_validate_ei3_event_matrix_v1(root)
    rows = _overlay_ei3_exact3_v1(frozen.rows, matrix_rows, reconciliation)
    top_pending = _top_pending_review_units_v1(root, reconciliation)
    summary = _build_summary_v1(rows, top_pending)
    bindings = _merge_semantic_bindings_v1(frozen.semantic_source_bindings, additive)
    computation = base.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=rows, summary=summary, semantic_source_bindings=bindings
    )
    validate_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1(
        computation,
        repo_root=root,
        predecessor_computation=frozen,
        reconciliation_result=reconciliation,
        matrix_rows=matrix_rows,
    )
    return computation, frozen, reconciliation, matrix_rows


def compute_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1(
    repo_root: Path,
) -> base.Cumulative1000CurrentGlobalReadinessComputationV1:
    """Compute the additive EI3 successor entirely from published sources."""

    return _compute_components_v1(repo_root)[0]


def _assert_no_stale_summary_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {
                "population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_plus_6oa_exact20",
                "orthogonal_population_frozen_exact20",
                "historical_exact20_population_count",
                "population_equals_historical_exact20_union_me7_exact3",
                "next_priority_review_pdb",
            }:
                _fail("SUMMARY_STALE_KEY:" + key)
            _assert_no_stale_summary_keys(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_stale_summary_keys(item)


def validate_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1(
    computation: object,
    *,
    repo_root: Path | None = None,
    predecessor_computation: base.Cumulative1000CurrentGlobalReadinessComputationV1 | None = None,
    reconciliation_result: generic.ReconciliationResult | None = None,
    matrix_rows: Sequence[Mapping[str, str]] | None = None,
) -> bool:
    """Fail closed unless rows, summary, bindings, and Exact3 delta all agree."""

    if not isinstance(computation, base.Cumulative1000CurrentGlobalReadinessComputationV1):
        _fail("COMPUTATION_TYPE_INVALID")
    if repo_root is None:
        _fail("REPO_ROOT_REQUIRED")
    root = Path(repo_root).resolve()
    if predecessor_computation is None:
        predecessor_computation = _verify_predecessor(root)
    if reconciliation_result is None:
        reconciliation_result = _validate_ei3_reconciliation_v1(root)
    if matrix_rows is None:
        matrix_rows = _load_and_validate_ei3_event_matrix_v1(root)
    rows = computation.rows
    summary = computation.summary
    bindings = computation.semantic_source_bindings
    if (
        len(rows) != 1000
        or len(CENSUS_COLUMNS_V1) != 47
        or CENSUS_COLUMNS_V1 != predecessor.CENSUS_COLUMNS_V1
        or any(type(row) is not dict or tuple(row) != CENSUS_COLUMNS_V1 for row in rows)
        or type(summary) is not dict
        or type(bindings) is not tuple
    ):
        _fail("CENSUS_SUMMARY_OR_BINDINGS_SCHEMA_INVALID")
    if (
        len(_AUTHORIZED_EI3_OVERLAY_FIELDS_V1) != 19
        or len(_AUTHORIZED_BUT_UNCHANGED_EI3_FIELDS_V1) != 7
        or len(_ACTUAL_CHANGED_EI3_FIELDS_V1) != 12
        or not _AUTHORIZED_BUT_UNCHANGED_EI3_FIELDS_V1.issubset(
            _AUTHORIZED_EI3_OVERLAY_FIELDS_V1
        )
    ):
        _fail("AUTHORIZED_EI3_OVERLAY_CONTRACT_INVALID")
    event_ids = [row["canonical_event_id"] for row in rows]
    try:
        ranks = [int(row["scaleup_rank"]) for row in rows]
    except ValueError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(
            f"{ERROR_TOKEN}:CENSUS_RANK_INVALID"
        ) from error
    if len(set(event_ids)) != 1000 or ranks != list(range(1, 1001)):
        _fail("CENSUS_EVENT_OR_RANK_IDENTITY_INVALID")
    predecessor_by_event = {
        row["canonical_event_id"]: row for row in predecessor_computation.rows
    }
    rows_by_event = {row["canonical_event_id"]: row for row in rows}
    if set(rows_by_event) != set(predecessor_by_event):
        _fail("CENSUS_EVENT_SET_IDENTITY_INVALID")
    target = set(EI3_EXACT3_EVENT_IDS_V1)
    changed_events = {
        event_id
        for event_id in rows_by_event
        if rows_by_event[event_id] != predecessor_by_event[event_id]
    }
    if changed_events != target:
        _fail("PREDECESSOR_DELTA_NOT_EXACT_EI3_EXACT3")
    matrix_by_event = {
        row["canonical_event_id"]: row
        for row in _validate_ei3_matrix_rows_v1(matrix_rows)
    }
    facts = {
        fact.canonical_event_id: fact
        for fact in reconciliation_result.normalized_facts
        if fact.canonical_event_id in target
    }
    if set(matrix_by_event) != target or set(facts) != target:
        _fail("EI3_SOURCE_MAPPING_NOT_EXACT3")
    for event_id in EI3_EXACT3_EVENT_IDS_V1:
        old = predecessor_by_event[event_id]
        new = rows_by_event[event_id]
        matrix = matrix_by_event[event_id]
        fact = facts[event_id]
        changed_fields = {
            field for field in CENSUS_COLUMNS_V1 if old[field] != new[field]
        }
        unchanged_authorized = {
            field
            for field in _AUTHORIZED_EI3_OVERLAY_FIELDS_V1
            if old[field] == new[field]
        }
        if changed_fields != _ACTUAL_CHANGED_EI3_FIELDS_V1:
            _fail("EI3_CHANGED_FIELD_SET_NOT_EXACT12:" + event_id)
        if unchanged_authorized != _AUTHORIZED_BUT_UNCHANGED_EI3_FIELDS_V1:
            _fail("EI3_AUTHORIZED_BUT_UNCHANGED_SET_NOT_EXACT7:" + event_id)
        expected = {
            "current_global_status": generic.COMPLETED_HUMAN_NEGATIVE,
            "current_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
            "human_review_completed": "true",
            "human_review_authority_source": fact.source_binding_path,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "chemistry_authority_source": EI3_EVENT_MATRIX_SOURCE,
            "positive_authority_source": EI3_EVENT_MATRIX_SOURCE,
            "task_relevance_disposition": generic.TASK_NOT_RELEVANT,
            "task_relevance_authority_source": EI3_EVENT_MATRIX_SOURCE,
            "training_use_disposition": generic.TRAINING_NOT_APPLICABLE,
            "human_training_excluded": "false",
            "reactive_pair_sample_authoritative": "true",
            "role_partition_sample_authoritative": "false",
            "role_profile": base.ROLE_NOT_ESTABLISHED,
            "canonical_mask_structural_labels_available": "false",
            "structurally_applicable_task_ids_json": "null",
            "training_use_include": "false",
            "future_training_admission_candidate": "false",
            "training_materialization_allowed_current_source": "false",
        }
        if any(new[key] != value for key, value in expected.items()):
            _fail("EI3_REFRESHED_SEMANTICS_INVALID:" + event_id)
        if (
            new["scaleup_rank"] != matrix["scaleup_rank"]
            or new["pdb_id"] != matrix["pdb_id"]
            or new["review_unit_id"] != matrix["review_unit_id"]
            or new["training_use_include"]
            != str(matrix["training_disposition"] == generic.TRAINING_INCLUDE).lower()
            or matrix["role_profile_raw_json"] != "null"
            or matrix["task_applicability_sample_authoritative"] != "false"
        ):
            _fail("EI3_MATRIX_CENSUS_SEMANTIC_MISMATCH:" + event_id)
    orthogonal = {
        row["canonical_event_id"]
        for row in rows
        if (
            row["task_relevance_disposition"],
            row["chemistry_disposition"],
            row["training_use_disposition"],
        )
        == (
            generic.TASK_NOT_RELEVANT,
            generic.CHEMISTRY_POSITIVE,
            generic.TRAINING_NOT_APPLICABLE,
        )
    }
    expected_orthogonal = (
        set(historical.GVE_EXACT4_EVENT_IDS_V1)
        | set(historical.LCY_EXACT4_EVENT_IDS_V1)
        | set(historical.ZERO_D8_EXACT4_EVENT_IDS_V1)
        | set(historical.TP2_EXACT4_EVENT_IDS_V1)
        | set(historical.SIX_OA_EXACT4_EVENT_IDS_V1)
        | set(predecessor.ME7_EXACT3_EVENT_IDS_V1)
        | target
    )
    if orthogonal != expected_orthogonal or len(orthogonal) != 26:
        _fail("ORTHOGONAL_POPULATION_NOT_HISTORICAL23_UNION_EI3_EXACT3")
    expected_distributions = (
        (
            "GLOBAL",
            Counter(row["current_global_status"] for row in rows),
            Counter(
                {
                    **historical._EXPECTED_GLOBAL_STATUS_COUNTS_V1,
                    generic.CURRENTLY_UNREVIEWED: 157,
                    generic.COMPLETED_HUMAN_NEGATIVE: 84,
                    generic.COMPLETED_HUMAN_POSITIVE: 127,
                }
            ),
        ),
        (
            "CHEMISTRY",
            Counter(row["chemistry_disposition"] for row in rows),
            Counter({"POSITIVE": 170, "NOT_ESTABLISHED": 90, "UNRESOLVED": 740}),
        ),
        (
            "TASK",
            Counter(row["task_relevance_disposition"] for row in rows),
            Counter({"RELEVANT": 145, "NOT_RELEVANT": 116, "UNRESOLVED": 739}),
        ),
        (
            "TRAINING",
            Counter(row["training_use_disposition"] for row in rows),
            Counter(
                {
                    "INCLUDE": 68,
                    "EXCLUDE_FROM_TRAINING_ONLY": 76,
                    "NOT_APPLICABLE": 116,
                    "UNRESOLVED": 740,
                }
            ),
        ),
    )
    for label, actual, expected in expected_distributions:
        if actual != expected:
            _fail("CENSUS_" + label + "_DISTRIBUTION_INVALID")
    boolean_counts = {
        "reactive_pair_sample_authoritative": 170,
        "role_partition_sample_authoritative": 156,
        "canonical_mask_structural_labels_available": 156,
        "human_training_excluded": 76,
        "training_use_include": 68,
        "future_training_admission_candidate": 51,
    }
    for field, expected in boolean_counts.items():
        if sum(row[field] == "true" for row in rows) != expected:
            _fail("CENSUS_BOOLEAN_COUNT_INVALID:" + field)
    applicability: Counter[int] = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability.update(json.loads(row["structurally_applicable_task_ids_json"]))
        elif (
            row["role_profile"] != base.ROLE_NOT_ESTABLISHED
            or row["canonical_mask_structural_labels_available"] != "false"
            or row["structurally_applicable_task_ids_json"] != "null"
        ):
            _fail("ROLELESS_ROW_FALSE_APPLICABILITY_NOT_UNKNOWN:" + row["canonical_event_id"])
    if applicability != Counter({0: 156, 1: 56, 2: 56, 3: 156, 4: 156}):
        _fail("CANONICAL_EXACT5_APPLICABILITY_COUNTS_INVALID")
    if (
        len(CANONICAL_EXACT5_V1) != 5
        or CANONICAL_EXACT5_V1[3][1:] != ("scaffold_only", "B3")
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_INVALID")
    geometry = {
        field: sum(row[field] == "true" for row in rows)
        for field in (
            "post_geometry_sample_authoritative",
            "post_geometry_training_target_available",
            "pre_geometry_authoritative",
            "pre_geometry_training_target_available",
            "current_runtime_model_usable",
            "formal_training_admitted",
        )
    }
    if geometry != {
        "post_geometry_sample_authoritative": 21,
        "post_geometry_training_target_available": 17,
        "pre_geometry_authoritative": 0,
        "pre_geometry_training_target_available": 0,
        "current_runtime_model_usable": 17,
        "formal_training_admitted": 5,
    }:
        _fail("GLOBAL_RUNTIME_PRE_POST_TRAINING_COUNTS_INVALID")
    top_pending = _top_pending_review_units_v1(root, reconciliation_result)
    if summary != _build_summary_v1(rows, top_pending):
        _fail("SUMMARY_NOT_EXACTLY_SOURCE_DERIVED")
    _assert_no_stale_summary_keys(summary)
    blockers = summary["blockers"]
    expected_blockers = {
        "chemistry_unresolved": {"all_1000": 740},
        "pair_authority_absent": {"all_1000": 830, "within_chemistry_positive": 0},
        "role_authority_absent": {"all_1000": 844, "within_chemistry_positive": 14},
        "human_training_exclusion": {"within_chemistry_positive": 76},
        "missing_split_authority": {
            "within_chemistry_positive": 129,
            "within_training_include": 43,
        },
        "missing_POST_training_authority": {
            "within_chemistry_positive": 153,
            "within_training_include": 51,
        },
        "missing_training_admission": {
            "within_chemistry_positive": 165,
            "within_training_include": 63,
        },
        "feature_semantics_pending": {"within_chemistry_positive": 170},
    }
    if any(blockers[key] != value for key, value in expected_blockers.items()):
        _fail("SUMMARY_BLOCKER_COUNTS_INVALID")
    tensor = blockers["missing_tensor_integration"]
    if (
        tensor["within_chemistry_positive"] != 129
        or tensor["within_training_include"] != 39
        or tensor["missing_source_composition"].get("EI3") != 3
        or summary["chemistry"]["positive_source_composition"].get("EI3") != 3
        or summary["reactive_pair"]["ei3_sample_authority_contribution_count"] != 3
        or summary["reactive_pair"]["ei3_training_target_contribution_count"] != 0
        or summary["training_stage"]["formal_training_admitted_count"] != 5
        or summary["training_stage"]["ready_for_formal_training_event_count"] != 0
    ):
        _fail("SUMMARY_EI3_SOURCE_OR_ADMISSION_COMPOSITION_INVALID")
    expected_bindings = _merge_semantic_bindings_v1(
        predecessor_computation.semantic_source_bindings, _verify_additive_sources(root)
    )
    if bindings != expected_bindings:
        _fail("SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6")
    for binding in bindings:
        keys = {"artifact_role", "path", "path_namespace", "byte_count", "sha256"}
        if "expected_executable" in binding:
            keys.add("expected_executable")
        path = binding.get("path")
        if (
            type(binding) is not dict
            or set(binding) != keys
            or type(path) is not str
            or not path
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
            or binding.get("path_namespace")
            not in {"repository_relative", "repository_parent_relative"}
            or type(binding.get("byte_count")) is not int
            or binding["byte_count"] <= 0
            or type(binding.get("sha256")) is not str
            or not _SHA_PATTERN.fullmatch(binding["sha256"])
        ):
            _fail("SEMANTIC_SOURCE_BINDING_INVALID")
    census_digest = _sha256(_csv_bytes(rows))
    summary_digest = _sha256(_json_bytes(summary))
    bindings_digest = _sha256(_canonical_json(list(bindings)).encode("utf-8"))
    expected_digests = (
        (_EXPECTED_REFRESHED_CENSUS_SHA256_V1, census_digest, "CENSUS"),
        (_EXPECTED_REFRESHED_SUMMARY_SHA256_V1, summary_digest, "SUMMARY"),
        (
            _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1,
            bindings_digest,
            "SEMANTIC_BINDINGS",
        ),
    )
    for expected, actual, label in expected_digests:
        if expected is not None and expected != actual:
            _fail("REFRESHED_" + label + "_EXACT_SHA256_INVALID")
    return True


def _validate_text_payload(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("OUTPUT_UTF8_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(
            f"{ERROR_TOKEN}:OUTPUT_NOT_UTF8:{label}"
        ) from error
    if "\x00" in text or "\r" in text:
        _fail("OUTPUT_TEXT_INVARIANT_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        _fail("OUTPUT_FINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("OUTPUT_TRAILING_WHITESPACE:" + label)


def _candidate_contract_bindings_v1(root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for role, relative in (
        ("PRODUCTION_OWNER", PRODUCTION_RELATIVE),
        ("CHECKER", CHECKER_RELATIVE),
        ("TARGETED_TESTS", TEST_RELATIVE),
        ("GUIDE", GUIDE_RELATIVE),
    ):
        payload = _read_regular_file(root / relative, role)
        _validate_text_payload(payload, relative.as_posix())
        result.append(
            {
                "artifact_role": role,
                "path": relative.as_posix(),
                "byte_count": len(payload),
                "sha256": _sha256(payload),
            }
        )
    return result


def _build_artifacts_from_computation_v1(
    root: Path,
    computation: base.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> dict[str, bytes]:
    census_payload = _csv_bytes(computation.rows)
    summary_payload = _json_bytes(computation.summary)
    _validate_text_payload(census_payload, CENSUS_FILE)
    _validate_text_payload(summary_payload, SUMMARY_FILE)
    if len(census_payload) > 1024 * 1024:
        _fail("CENSUS_OUTPUT_EXCEEDS_1_MIB")
    output_bindings = [
        {
            "artifact_role": "REFRESHED_CENSUS_CSV",
            "path": (OUTPUT_DIRECTORY_RELATIVE / CENSUS_FILE).as_posix(),
            "byte_count": len(census_payload),
            "sha256": _sha256(census_payload),
        },
        {
            "artifact_role": "REFRESHED_SUMMARY_JSON",
            "path": (OUTPUT_DIRECTORY_RELATIVE / SUMMARY_FILE).as_posix(),
            "byte_count": len(summary_payload),
            "sha256": _sha256(summary_payload),
        },
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "candidate_inventory": {"exact_file_count": 7, "paths": list(EXACT7_PATHS_V1)},
        "candidate_contract_bindings": _candidate_contract_bindings_v1(root),
        "semantic_source_bindings": list(computation.semantic_source_bindings),
        "semantic_source_binding_count": len(computation.semantic_source_bindings),
        "predecessor_manifest_validation_binding": {
            "artifact_role": "PREDECESSOR_WITH_ME7_MANIFEST_VALIDATION_IDENTITY",
            "path": PREDECESSOR_MANIFEST_RELATIVE.as_posix(),
            "path_namespace": "repository_relative",
            "byte_count": _PREDECESSOR_MANIFEST_SPEC_V1[0],
            "sha256": _PREDECESSOR_MANIFEST_SPEC_V1[1],
            "expected_executable": _PREDECESSOR_MANIFEST_SPEC_V1[2],
        },
        "ei3_reconciliation_artifact_validation_binding": {
            "artifact_role": "EI3_RECONCILIATION_ARTIFACT_VALIDATION_IDENTITY",
            "path": EI3_RECONCILIATION_ARTIFACT_RELATIVE.as_posix(),
            "path_namespace": "repository_relative",
            "byte_count": _EI3_RECONCILIATION_ARTIFACT_SPEC_V1[0],
            "sha256": _EI3_RECONCILIATION_ARTIFACT_SPEC_V1[1],
            "expected_executable": _EI3_RECONCILIATION_ARTIFACT_SPEC_V1[2],
            "computational_source": False,
        },
        "frozen_priority_queue_validation_binding": {
            "artifact_role": "CURRENT_FROZEN_PRIORITY_QUEUE",
            "path": PRIORITY_QUEUE_RELATIVE.as_posix(),
            "path_namespace": "repository_relative",
            "byte_count": _PRIORITY_QUEUE_SPEC_V1[0],
            "sha256": _PRIORITY_QUEUE_SPEC_V1[1],
            "expected_executable": _PRIORITY_QUEUE_SPEC_V1[2],
        },
        "derived_projection_contract_digests": {
            "refreshed_census_sha256": _EXPECTED_REFRESHED_CENSUS_SHA256_V1,
            "refreshed_summary_sha256": _EXPECTED_REFRESHED_SUMMARY_SHA256_V1,
            "semantic_source_bindings_sha256": _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1,
            "authority_created": False,
        },
        "output_inventory": {
            "exact_output_count": 3,
            "paths": [
                (OUTPUT_DIRECTORY_RELATIVE / name).as_posix()
                for name in (CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE)
            ],
        },
        "output_bindings_excluding_manifest_self": output_bindings,
        "manifest_self_binding": {
            "path": (OUTPUT_DIRECTORY_RELATIVE / MANIFEST_FILE).as_posix(),
            "sha256_recorded_inside_self": False,
            "policy": "MANIFEST_SELF_SHA256_PROHIBITED",
        },
        "manifest_self_SHA256_recorded": False,
        "determinism_contract": {
            "utf8": True,
            "lf_only": True,
            "single_final_lf": True,
            "timestamps_recorded": False,
            "machine_absolute_paths_recorded": False,
            "live_git_state_recorded": False,
            "source_derived": True,
        },
        "source_binding_policy_contract": {
            "policy": "covapie_source_binding_policy_v2",
            "content_identity_and_executable_class_required": True,
            "numeric_posix_mode_is_not_semantic_identity": True,
        },
        "refresh_contract": {
            "row_count": 1000,
            "column_count": 47,
            "ei3_overlay_event_count": 3,
            "non_ei3_changed_row_count": 0,
            "unchanged_event_count": 997,
            "authorized_overlay_field_count": 19,
            "authorized_but_unchanged_field_count": 7,
            "actual_changed_field_count_per_ei3_row": 12,
            "semantic_source_binding_count": 204,
            "predecessor_semantic_source_binding_count": 198,
            "additive_semantic_source_binding_count": 6,
            "semantic_identity_collision_count": 0,
            "new_source_role_collision_count": 0,
            "historical_role_constraint_strengthened": False,
            "task_negative_chemistry_positive_population_count": 26,
            "historical_orthogonal_population_count": 23,
            "ei3_orthogonal_population_count": 3,
            "census_refreshed": True,
            "census_refresh_performed": True,
            "queue_refreshed": False,
            "next_review_started": False,
            "review_state_created_by_this_refresh": False,
            "ei3_review_state_exists": True,
            "ei3_review_completed": True,
            "ei3_reconciliation_consumed": True,
            "new_human_authority_created": False,
            "new_scientific_authority_created": False,
            "new_reusable_authority_created": False,
            "derived_refresh_not_new_authority": True,
            "formal_decision_read_directly": False,
            "formal_decision_bound_directly": False,
            "formal_validator_executed": False,
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "training_mask_targets_created": False,
            "training_dataset_changed": False,
            "tensor_integration_performed": False,
            "training_materialization_allowed": False,
            "formal_training_admitted_by_refresh": False,
            "historical_formal_training_admitted_count": 5,
            "ready_for_training": False,
            "ready_for_formal_training": False,
            "training_started": False,
            "feature_semantics_audit_performed": False,
            "feature_semantics_audit_required_before_training": True,
            "step12d_is_only_smoke_legality_check": True,
            "source_binding_v2_clean_from_birth": True,
        },
        "authority_boundary": computation.summary["authority_boundary"],
    }
    manifest_payload = _json_bytes(manifest)
    _validate_text_payload(manifest_payload, MANIFEST_FILE)
    lowered = manifest_payload.decode("utf-8").lower()
    for token in (
        '"hostname"',
        '"pid"',
        '"timestamp"',
        '"head"',
        '"commit_subject"',
        '"ahead"',
        '"behind"',
        '"lifecycle_profile"',
    ):
        if token in lowered:
            _fail("MANIFEST_LIFECYCLE_FIELD_FORBIDDEN")
    return {
        CENSUS_FILE: census_payload,
        SUMMARY_FILE: summary_payload,
        MANIFEST_FILE: manifest_payload,
    }


def build_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1(
    repo_root: Path,
) -> dict[str, bytes]:
    """Build deterministic Exact3 outputs without repository writes."""

    if None in (
        _EXPECTED_REFRESHED_CENSUS_SHA256_V1,
        _EXPECTED_REFRESHED_SUMMARY_SHA256_V1,
        _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1,
    ):
        _fail("DERIVED_PROJECTION_DIGESTS_NOT_FROZEN")
    root = Path(repo_root).resolve()
    computation = compute_covapie_cumulative1000_current_global_readiness_census_with_ei3_v1(
        root
    )
    return _build_artifacts_from_computation_v1(root, computation)


def _validate_materialization_destination_v1(root: Path, output: Path) -> None:
    if output.resolve() != (root / OUTPUT_DIRECTORY_RELATIVE).resolve():
        _fail("OUTPUT_DIRECTORY_NOT_AUTHORIZED")
    try:
        metadata = output.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _fail("OUTPUT_ROOT_NOT_REAL_DIRECTORY")
    allowed = {CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE}
    unexpected = sorted(entry.name for entry in output.iterdir() if entry.name not in allowed)
    if unexpected:
        _fail("OUTPUT_DIRECTORY_UNEXPECTED_ENTRY:" + unexpected[0])
    for entry in output.iterdir():
        metadata = entry.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("OUTPUT_ENTRY_NOT_REGULAR:" + entry.name)


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(
            prefix=path.name + ".", suffix=".tmp", dir=path.parent
        )
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithEI3Error(
            f"{ERROR_TOKEN}:OUTPUT_WRITE_FAILED:{path.name}"
        ) from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1(
    repo_root: Path, output_directory: Path | None = None
) -> dict[str, bytes]:
    """Write only the authorized Exact3 files under the exact EI3 output root."""

    root = Path(repo_root).resolve()
    output = root / OUTPUT_DIRECTORY_RELATIVE if output_directory is None else Path(output_directory)
    _validate_materialization_destination_v1(root, output)
    artifacts = build_covapie_cumulative1000_current_global_readiness_artifacts_with_ei3_v1(
        root
    )
    output.mkdir(parents=True, exist_ok=True)
    for filename in (CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE):
        _atomic_write(output / filename, artifacts[filename])
    return artifacts
