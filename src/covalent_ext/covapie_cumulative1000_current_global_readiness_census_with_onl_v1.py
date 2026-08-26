"""Additive cumulative1000 readiness census refresh for published ONL Exact9.

This successor deliberately reuses the frozen predecessor computation.  It
validates the already-published ONL ingestion and reconciliation products,
deep-copies the predecessor rows, and overlays only the exact nine ONL events.
It creates no new human, chemistry, pair, role, split, tensor, or training
authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any, NoReturn

from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_reconciliation
from . import covapie_cumulative1000_current_global_readiness_census_v1 as predecessor
from . import covapie_onl_completed_decision_ingestion_and_task_label_availability_v1 as onl_ingestion


__all__ = (
    "Cumulative1000CurrentGlobalReadinessCensusWithONLError",
    "compute_covapie_cumulative1000_current_global_readiness_census_with_onl_v1",
    "validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1",
    "build_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1",
    "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1",
)


SCHEMA_VERSION = "covapie_cumulative1000_current_global_readiness_census_with_onl_v1"
STAGE = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_ONL_V1"
ERROR_TOKEN = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_ONL_V1_ERROR"

OUTPUT_DIRECTORY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_onl_v1"
)
CENSUS_FILE = "covapie_cumulative1000_current_global_readiness_census_with_onl_v1.csv"
SUMMARY_FILE = "covapie_cumulative1000_current_global_readiness_summary_with_onl_v1.json"
MANIFEST_FILE = "covapie_cumulative1000_current_global_readiness_manifest_with_onl_v1.json"

PRODUCTION_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_with_onl_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_onl_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_cumulative1000_current_global_readiness_census_with_onl_v1.py"
)
GUIDE_RELATIVE = Path(
    "docs/covapie_cumulative1000_current_global_readiness_census_with_onl_v1_guide.md"
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
ONL_EXACT9_EVENT_IDS_V1 = onl_ingestion.EXPECTED_EVENT_IDS
ONL_EXACT9_RANKS_V1 = (24, 25, 26, 27, 134, 434, 435, 436, 437)
ONL_REVIEW_UNIT_ID_V1 = onl_ingestion.EXPECTED_REVIEW_UNIT_ID
ONL_DIRECT_TASK_IDS_CELL_V1 = "[0,3,4]"

PREDECESSOR_OWNER_RELATIVE = predecessor.PRODUCTION_RELATIVE
PREDECESSOR_CENSUS_RELATIVE = (
    predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.CENSUS_FILE
)
PREDECESSOR_SUMMARY_RELATIVE = (
    predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.SUMMARY_FILE
)
ONL_RECONCILIATION_OWNER_RELATIVE = Path(
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_onl_v1.py"
)
ONL_INGESTION_OWNER_RELATIVE = Path(
    "src/covalent_ext/covapie_onl_completed_decision_ingestion_and_task_label_availability_v1.py"
)
ONL_EVENT_MATRIX_RELATIVE = onl_ingestion.OUTPUT_ROOT_RELATIVE / onl_ingestion.MATRIX
ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    onl_ingestion.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
)
PRIORITY_QUEUE_RELATIVE = Path(predecessor._QUEUE)

ONL_EVENT_MATRIX_SOURCE = ONL_EVENT_MATRIX_RELATIVE.as_posix()
ONL_FORMAL_DECISION_SOURCE = (
    ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
)

_EXPECTED_GLOBAL_STATUS_COUNTS_V1 = {
    generic.CURRENTLY_UNREVIEWED: 273,
    generic.CURRENTLY_IN_PROGRESS: 0,
    generic.COMPLETED_HUMAN_POSITIVE: 41,
    generic.COMPLETED_HUMAN_NEGATIVE: 54,
    generic.COMPLETED_PARTIAL_AUTHORITY: 1,
    generic.CURRENT_RUNTIME_MODEL_USABLE: 17,
    generic.PUBLISHED_EXACT_AUTO_NEGATIVE: 32,
    "LEAKAGE_EXISTING_GROUP_CONFLICT": 369,
    "STRUCTURAL_EVIDENCE_INCOMPLETE": 133,
    "QUARANTINE_REPRESENTATION_GAP": 78,
    "REJECTED_FEATURE_INCOMPATIBLE": 2,
}
_EXPECTED_BOOLEAN_COUNTS_V1 = {
    "raw_structure_available": 997,
    "exact_cys_sg_event_recovered": 867,
    "explicit_covalent_evidence": 867,
    "distance_only_event_inference_used": 0,
    "full_coordinate_post_evidence_available": 867,
    "ccd_graph_complete": 865,
    "feature_compatible": 865,
    "structural_processing_success": 865,
    "post_geometry_source_evidence_available": 867,
    "representation_gap": 78,
    "feature_incompatible": 2,
    "priority_review_in_scope": 338,
    "reactive_pair_raw_structural_evidence": 865,
    "reactive_pair_sample_authoritative": 58,
    "reactive_pair_training_target_available": 41,
    "role_partition_sample_authoritative": 58,
    "canonical_mask_structural_labels_available": 58,
    "post_geometry_sample_authoritative": 21,
    "post_geometry_training_target_available": 17,
    "pre_geometry_authoritative": 0,
    "pre_geometry_training_target_available": 0,
    "training_use_include": 29,
    "future_training_admission_candidate": 12,
    "formal_training_admitted": 5,
    "current_runtime_model_usable": 17,
}

# Frozen after the first fully source-derived build and semantic validation.
# They are derived projection contract digests, never authority.
_EXPECTED_REFRESHED_CENSUS_SHA256_V1 = (
    "57be12d7ed5d4e013dbd402ccf0ed49aa3d86067a952fdd339fcc945062894e4"
)
_EXPECTED_REFRESHED_SUMMARY_SHA256_V1 = (
    "3271df9a94bf72f8ae081735e07e132c4a7d0dfb389f3acfdf31789420f2c19b"
)
_EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1 = (
    "fc91c62933803f9ca7b7bdfe08f5880533d8a0b147925e6b5c1846785a8bedf1"
)

_SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_STRUCTURAL_IDENTITY_FIELDS_V1 = (
    "scaleup_rank",
    "canonical_event_id",
    "pdb_id",
    "ligand_component_id",
    "raw_structure_available",
    "exact_cys_sg_event_recovered",
    "explicit_covalent_evidence",
    "distance_only_event_inference_used",
    "full_coordinate_post_evidence_available",
    "ccd_graph_complete",
    "feature_compatible",
    "structural_processing_success",
    "post_geometry_source_evidence_available",
    "representation_gap",
    "feature_incompatible",
    "reactive_pair_raw_structural_evidence",
)
_AUTHORIZED_ONL_OVERLAY_FIELDS_V1 = frozenset(
    {
        "current_global_status",
        "current_review_status",
        "human_review_completed",
        "human_review_authority_source",
        "chemistry_disposition",
        "chemistry_authority_source",
        "task_relevance_disposition",
        "task_relevance_authority_source",
        "training_use_disposition",
        "human_training_excluded",
        "reactive_pair_sample_authoritative",
        "reactive_pair_training_target_available",
        "role_partition_sample_authoritative",
        "role_profile",
        "canonical_mask_structural_labels_available",
        "structurally_applicable_task_ids_json",
        "post_geometry_sample_authoritative",
        "post_geometry_training_target_available",
        "pre_geometry_authoritative",
        "pre_geometry_training_target_available",
        "training_use_include",
        "future_training_admission_candidate",
        "formal_split_authoritative",
        "formal_split",
        "formal_training_admitted",
        "current_runtime_model_usable",
        "training_materialization_allowed_current_source",
        "positive_authority_source",
        "feature_semantics_status",
    }
)

_ADDITIVE_SOURCE_SPECS_V1 = (
    ("PREDECESSOR_CENSUS_OWNER", PREDECESSOR_OWNER_RELATIVE, "repository_relative", 121594, "2c35400febf7a7e407614c0bc3aa7504db2117f40430f2e990d3d41ac4bef6fe"),
    ("PREDECESSOR_MATERIALIZED_CENSUS", PREDECESSOR_CENSUS_RELATIVE, "repository_relative", 497477, "f4f44058a68f8161969b84a7e6b5efde08d6cd1d59520010c4f742d78b171dc9"),
    ("PREDECESSOR_MATERIALIZED_SUMMARY", PREDECESSOR_SUMMARY_RELATIVE, "repository_relative", 13681, "569625aef3b22d12af528e2afe61ed5ebf381f84642a063a81970894b80dc74a"),
    ("ONL_RECONCILIATION_SUCCESSOR", ONL_RECONCILIATION_OWNER_RELATIVE, "repository_relative", 13046, "f2c94ac8b4fe8f3706d0de288e2d5bb24ef211cf56d39e8362b43bdb17a2f475"),
    ("ONL_INGESTION_OWNER", ONL_INGESTION_OWNER_RELATIVE, "repository_relative", 61281, "abbf2f2bbc5d144395f78b80ece5a7b52ebd2ddefd802b9cf023fe15beb23d7a"),
    ("ONL_EVENT_TASK_LABEL_AVAILABILITY", ONL_EVENT_MATRIX_RELATIVE, "repository_relative", 14822, "175f2f070967fb33e0133501a488cf30022818dbbadcd4b85f3ab497afda969c"),
    ("ONL_FORMAL_HUMAN_DECISION", ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT, "repository_parent_relative", 28678, "eb68b63046b561e857ae84640843914960c974ce7807be1ee18aba3f107581d5"),
)


class Cumulative1000CurrentGlobalReadinessCensusWithONLError(ValueError):
    """Raised unless the additive ONL refresh is exactly source-derived."""


def _fail(reason: str) -> NoReturn:
    raise Cumulative1000CurrentGlobalReadinessCensusWithONLError(
        f"{ERROR_TOKEN}:{reason}"
    )


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _event_set_sha256(event_ids: Sequence[str] | set[str]) -> str:
    return _sha256(_canonical_json(sorted(event_ids)).encode("utf-8"))


def _csv_bytes(rows: Sequence[Mapping[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=CENSUS_COLUMNS_V1,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        _fail("SOURCE_NOT_REGULAR_FILE:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithONLError(
            f"{ERROR_TOKEN}:SOURCE_READ_FAILED:{label}"
        ) from error


def _resolve_source(root: Path, namespace: str, relative: Path) -> Path:
    if namespace == "repository_relative":
        return root / relative
    if namespace == "repository_parent_relative":
        return root.parent / relative
    _fail("SOURCE_NAMESPACE_INVALID:" + namespace)


def _verify_additive_sources(root: Path) -> tuple[dict[str, object], ...]:
    bindings: list[dict[str, object]] = []
    for role, relative, namespace, byte_count, sha256 in _ADDITIVE_SOURCE_SPECS_V1:
        payload = _read_regular_file(
            _resolve_source(root, namespace, relative), role
        )
        if len(payload) != byte_count:
            _fail("SOURCE_BYTE_COUNT_MISMATCH:" + role)
        if _sha256(payload) != sha256:
            _fail("SOURCE_SHA256_MISMATCH:" + role)
        bindings.append(
            {
                "artifact_role": role,
                "path": relative.as_posix(),
                "path_namespace": namespace,
                "byte_count": byte_count,
                "sha256": sha256,
            }
        )
    return tuple(bindings)


def _strict_json_cell(cell: str, label: str) -> Any:
    try:
        return json.loads(cell)
    except json.JSONDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithONLError(
            f"{ERROR_TOKEN}:MATRIX_JSON_INVALID:{label}"
        ) from error


def _load_and_validate_onl_event_matrix_v1(root: Path) -> tuple[dict[str, str], ...]:
    payload = _read_regular_file(root / ONL_EVENT_MATRIX_RELATIVE, "ONL_EVENT_MATRIX")
    if len(payload) != 14822 or _sha256(payload) != _ADDITIVE_SOURCE_SPECS_V1[5][4]:
        _fail("ONL_EVENT_MATRIX_BINDING_INVALID")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithONLError(
            f"{ERROR_TOKEN}:ONL_EVENT_MATRIX_NOT_UTF8"
        ) from error
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != onl_ingestion.MATRIX_HEADER:
        _fail("ONL_EVENT_MATRIX_HEADER_INVALID")
    rows = tuple(dict(row) for row in reader)
    if len(rows) != 9 or any(tuple(row) != onl_ingestion.MATRIX_HEADER for row in rows):
        _fail("ONL_EVENT_MATRIX_NOT_EXACT9")
    event_ids = tuple(row["canonical_event_id"] for row in rows)
    if event_ids != ONL_EXACT9_EVENT_IDS_V1 or len(set(event_ids)) != 9:
        _fail("ONL_EVENT_MATRIX_EVENT_SET_OR_ORDER_INVALID")
    if tuple(int(row["scaleup_rank"]) for row in rows) != ONL_EXACT9_RANKS_V1:
        _fail("ONL_EVENT_MATRIX_RANKS_INVALID")

    expected_cells = {
        "human_task_relevance_decision": generic.TASK_RELEVANT,
        "chemistry_known_positive": "true",
        "negative_chemistry": "false",
        "task_domain_negative": "false",
        "reactive_pair_human_decision_available": "true",
        "reactive_pair_human_authoritative": "true",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "CE",
        "role_partition_human_decision_available": "true",
        "role_partition_human_authoritative": "true",
        "role_profile": predecessor.DIRECT_PROFILE,
        "global_canonical_task_count": "5",
        "formal_event_training_use_decision": generic.TRAINING_EXCLUDE,
        "training_use_human_decision_available": "true",
        "human_training_excluded": "true",
        "training_use_allowed": "false",
        "POST_source_evidence_available": "true",
        "POST_geometry_training_label_available_now": "false",
        "PRE_geometry_authority_available": "false",
        "PRE_geometry_training_label_available_now": "false",
        "candidate_for_future_training_admission": "false",
        "training_admitted": "false",
        "training_materialization_allowed_now": "false",
        "current_runtime_model_usable": "false",
        "model_bound_pair_target_created_by_ingestion": "false",
        "tensor_target_created": "false",
        "observed_product_graph_is_authoritative_PRE_precursor": "false",
        "PRE_precursor_reconstruction_performed": "false",
        "event_specific_disposition_exception": "false",
        "authority_source": onl_ingestion.AUTHORITY_SOURCE,
        "authority_ingested": "true",
        "authority_created_by_this_successor": "false",
    }
    expected_applicability = [
        {
            "task_id": task_id,
            "semantic_long_name": semantic_name,
            "display_alias": alias,
            "structurally_applicable": applicable,
            "reason": predecessor.DIRECT_PROFILE,
        }
        for task_id, semantic_name, alias, applicable, _reason
        in onl_ingestion.DIRECT_PROFILE_TASK_APPLICABILITY
    ]
    for row in rows:
        event_id = row["canonical_event_id"]
        if any(row[key] != value for key, value in expected_cells.items()):
            _fail("ONL_EVENT_MATRIX_SEMANTICS_INVALID:" + event_id)
        if _strict_json_cell(
            row["direct_profile_applicable_task_ids_json"], event_id
        ) != [0, 3, 4]:
            _fail("ONL_EVENT_MATRIX_DIRECT_TASK_IDS_INVALID:" + event_id)
        if _strict_json_cell(
            row["canonical_task_applicability_json"], event_id
        ) != expected_applicability:
            _fail("ONL_EVENT_MATRIX_EXACT5_APPLICABILITY_INVALID:" + event_id)
    return rows


def _validate_onl_reconciliation_v1(root: Path) -> generic.ReconciliationResult:
    result = onl_reconciliation.reconcile_real_completed_human_decisions_with_onl_v1(
        root
    )
    expected_summary = {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 41,
        "completed_positive_unit_count": 4,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 65,
        "completed_total_unit_count": 8,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 273,
        "unreviewed_unit_count": 123,
    }
    if result.review_summary != expected_summary:
        _fail("ONL_RECONCILIATION_SUMMARY_INVALID")
    if len(result.normalized_facts) != 41:
        _fail("ONL_RECONCILIATION_NORMALIZED_FACT_COUNT_INVALID")
    if Counter(fact.training_disposition for fact in result.normalized_facts) != Counter(
        {generic.TRAINING_INCLUDE: 12, generic.TRAINING_EXCLUDE: 29}
    ):
        _fail("ONL_RECONCILIATION_TRAINING_DISPOSITION_INVALID")
    onl_rows = [
        row
        for row in result.reconciled_rows
        if row["raw_review_unit_id"] == ONL_REVIEW_UNIT_ID_V1
    ]
    if (
        len(onl_rows) != 9
        or {row["canonical_event_id"] for row in onl_rows}
        != set(ONL_EXACT9_EVENT_IDS_V1)
        or any(
            row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
            for row in onl_rows
        )
    ):
        _fail("ONL_RECONCILIATION_EXACT9_INVALID")
    return result


def _assert_predecessor_onl_state_v1(
    computation: predecessor.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    rows = [
        row
        for row in computation.rows
        if row["canonical_event_id"] in set(ONL_EXACT9_EVENT_IDS_V1)
    ]
    if len(rows) != 9 or tuple(int(row["scaleup_rank"]) for row in rows) != ONL_EXACT9_RANKS_V1:
        _fail("PREDECESSOR_ONL_EXACT9_IDENTITY_INVALID")
    expected = {
        "current_global_status": generic.CURRENTLY_IN_PROGRESS,
        "priority_review_in_scope": "true",
        "review_unit_id": ONL_REVIEW_UNIT_ID_V1,
        "current_review_status": generic.CURRENTLY_IN_PROGRESS,
        "human_review_completed": "false",
        "chemistry_disposition": predecessor.CHEMISTRY_UNRESOLVED,
        "task_relevance_disposition": predecessor.TASK_UNRESOLVED,
        "training_use_disposition": predecessor.TRAINING_UNRESOLVED,
        "human_training_excluded": "false",
        "reactive_pair_sample_authoritative": "false",
        "reactive_pair_training_target_available": "false",
        "role_partition_sample_authoritative": "false",
        "role_profile": predecessor.ROLE_NOT_ESTABLISHED,
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
        "post_geometry_sample_authoritative": "false",
        "post_geometry_training_target_available": "false",
        "pre_geometry_authoritative": "false",
        "pre_geometry_training_target_available": "false",
        "future_training_admission_candidate": "false",
        "formal_split_authoritative": "false",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
    }
    if any(any(row[key] != value for key, value in expected.items()) for row in rows):
        _fail("PREDECESSOR_ONL_STATE_INVALID")
    if Counter(row["chemistry_disposition"] for row in computation.rows)[
        predecessor.CHEMISTRY_POSITIVE
    ] != 49:
        _fail("PREDECESSOR_OLD_49_POSITIVE_PROJECTION_INVALID")


def _overlay_onl_exact9_v1(
    predecessor_rows: Sequence[Mapping[str, str]],
    matrix_rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    matrix_by_event = {row["canonical_event_id"]: row for row in matrix_rows}
    if set(matrix_by_event) != set(ONL_EXACT9_EVENT_IDS_V1) or len(matrix_by_event) != 9:
        _fail("ONL_OVERLAY_MATRIX_SET_INVALID")
    rows = deepcopy([dict(row) for row in predecessor_rows])
    for row in rows:
        event_id = row["canonical_event_id"]
        if event_id not in matrix_by_event:
            continue
        matrix = matrix_by_event[event_id]
        if (
            row["scaleup_rank"] != matrix["scaleup_rank"]
            or row["pdb_id"] != matrix["pdb_id"]
            or row["ligand_component_id"] != "ONL"
        ):
            _fail("ONL_MATRIX_PREDECESSOR_IDENTITY_MISMATCH:" + event_id)
        row.update(
            {
                "current_global_status": generic.COMPLETED_HUMAN_POSITIVE,
                "current_review_status": generic.COMPLETED_HUMAN_POSITIVE,
                "human_review_completed": "true",
                "human_review_authority_source": ONL_FORMAL_DECISION_SOURCE,
                "chemistry_disposition": predecessor.CHEMISTRY_POSITIVE,
                "chemistry_authority_source": ONL_EVENT_MATRIX_SOURCE,
                "task_relevance_disposition": predecessor.TASK_RELEVANT,
                "task_relevance_authority_source": ONL_EVENT_MATRIX_SOURCE,
                "training_use_disposition": generic.TRAINING_EXCLUDE,
                "human_training_excluded": "true",
                "reactive_pair_sample_authoritative": "true",
                "reactive_pair_training_target_available": "false",
                "role_partition_sample_authoritative": "true",
                "role_profile": predecessor.DIRECT_PROFILE,
                "canonical_mask_structural_labels_available": "true",
                "structurally_applicable_task_ids_json": ONL_DIRECT_TASK_IDS_CELL_V1,
                "post_geometry_sample_authoritative": "false",
                "post_geometry_training_target_available": "false",
                "pre_geometry_authoritative": "false",
                "pre_geometry_training_target_available": "false",
                "training_use_include": "false",
                "future_training_admission_candidate": "false",
                "formal_split_authoritative": "false",
                "formal_split": "",
                "formal_training_admitted": "false",
                "current_runtime_model_usable": "false",
                "training_materialization_allowed_current_source": "false",
                "positive_authority_source": ONL_EVENT_MATRIX_SOURCE,
                "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
            }
        )
    return tuple(rows)


def _top_pending_review_units_v1(
    root: Path,
    reconciliation: generic.ReconciliationResult,
) -> list[dict[str, object]]:
    payload = _read_regular_file(root / PRIORITY_QUEUE_RELATIVE, "PRIORITY_QUEUE")
    if len(payload) != 50116 or _sha256(payload) != "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2":
        _fail("PRIORITY_QUEUE_BINDING_INVALID")
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    queue_rows = [dict(row) for row in reader]
    if len(queue_rows) != 131:
        _fail("PRIORITY_QUEUE_UNIT_COUNT_INVALID")
    status_by_unit: dict[str, set[str]] = defaultdict(set)
    for row in reconciliation.reconciled_rows:
        status_by_unit[row["raw_review_unit_id"]].add(row["current_review_status"])
    candidates: list[tuple[int, int, str, dict[str, str], str]] = []
    for row in queue_rows:
        unit = row["review_unit_id"]
        statuses = status_by_unit.get(unit)
        if statuses is None or len(statuses) != 1:
            _fail("PRIORITY_QUEUE_UNIT_STATUS_INVALID:" + unit)
        status = next(iter(statuses))
        if status not in {generic.CURRENTLY_UNREVIEWED, generic.CURRENTLY_IN_PROGRESS}:
            continue
        candidates.append(
            (-int(row["event_count"]), int(row["priority_rank"]), unit, row, status)
        )
    candidates.sort(key=lambda item: item[:3])
    if len(candidates) != 123:
        _fail("CURRENT_PENDING_REVIEW_UNIT_COUNT_INVALID")
    top: list[dict[str, object]] = []
    for rank, (_negative_count, _priority, unit, row, status) in enumerate(
        candidates[:10], 1
    ):
        top.append(
            {
                "rank": rank,
                "review_unit_id": unit,
                "event_count": int(row["event_count"]),
                "pdb_ids": json.loads(row["pdb_ids_json"]),
                "ligand_component_ids": json.loads(row["ligand_component_ids_json"]),
                "full_coordinate_count": int(row["full_coordinate_event_count"]),
                "exact_pair_count": int(row["exact_reactive_pair_event_count"]),
                "ccd_complete_count": int(row["CCD_graph_complete_event_count"]),
                "post_source_evidence_count": int(
                    row["POST_geometry_available_event_count"]
                ),
                "current_review_status": status,
            }
        )
    first = top[0]
    if first != {
        "rank": 1,
        "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58",
        "event_count": 8,
        "pdb_ids": ["3S19", "3UXJ"],
        "ligand_component_ids": ["PRF"],
        "full_coordinate_count": 8,
        "exact_pair_count": 8,
        "ccd_complete_count": 8,
        "post_source_evidence_count": 8,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
    }:
        _fail("NEXT_PRIORITY_REVIEW_UNIT_INVALID")
    return top


def _build_summary_v1(
    rows: Sequence[Mapping[str, str]],
    top_pending: list[dict[str, object]],
) -> dict[str, Any]:
    def event_set(field: str, value: str) -> set[str]:
        return {
            row["canonical_event_id"] for row in rows if row[field] == value
        }

    def disposition(label: str, values: set[str]) -> dict[str, object]:
        return {"count": len(values), "event_set_sha256": _event_set_sha256(values)}

    def count_true(field: str, population: Sequence[Mapping[str, str]] = rows) -> int:
        return sum(row[field] == "true" for row in population)

    chemistry_positive = event_set("chemistry_disposition", predecessor.CHEMISTRY_POSITIVE)
    chemistry_negative = event_set("chemistry_disposition", predecessor.CHEMISTRY_NEGATIVE)
    chemistry_not_established = event_set(
        "chemistry_disposition", predecessor.CHEMISTRY_NOT_ESTABLISHED
    )
    chemistry_unresolved = event_set(
        "chemistry_disposition", predecessor.CHEMISTRY_UNRESOLVED
    )
    task_relevant = event_set("task_relevance_disposition", predecessor.TASK_RELEVANT)
    task_not_relevant = event_set(
        "task_relevance_disposition", predecessor.TASK_NOT_RELEVANT
    )
    task_unresolved = event_set(
        "task_relevance_disposition", predecessor.TASK_UNRESOLVED
    )
    training_include = event_set("training_use_disposition", generic.TRAINING_INCLUDE)
    training_exclude = event_set("training_use_disposition", generic.TRAINING_EXCLUDE)
    training_not_applicable = event_set(
        "training_use_disposition", generic.TRAINING_NOT_APPLICABLE
    )
    training_unresolved = event_set(
        "training_use_disposition", predecessor.TRAINING_UNRESOLVED
    )
    positive_rows = [row for row in rows if row["canonical_event_id"] in chemistry_positive]
    include_rows = [row for row in rows if row["canonical_event_id"] in training_include]
    missing_tensor_rows = [
        row
        for row in positive_rows
        if row["reactive_pair_training_target_available"] == "false"
    ]

    applicability_counts: Counter[int] = Counter()
    profile_counts: Counter[str] = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] != "true":
            continue
        profile_counts[row["role_profile"]] += 1
        applicability_counts.update(json.loads(row["structurally_applicable_task_ids_json"]))

    priority_rows = [row for row in rows if row["priority_review_in_scope"] == "true"]
    review_counts = Counter(row["current_review_status"] for row in priority_rows)
    review_units_by_status: dict[str, set[str]] = defaultdict(set)
    for row in priority_rows:
        review_units_by_status[row["current_review_status"]].add(row["review_unit_id"])
    completed_units = (
        review_units_by_status[generic.COMPLETED_HUMAN_POSITIVE]
        | review_units_by_status[generic.COMPLETED_HUMAN_NEGATIVE]
    )
    pending_units = (
        review_units_by_status[generic.CURRENTLY_UNREVIEWED]
        | review_units_by_status[generic.CURRENTLY_IN_PROGRESS]
    )

    global_counts = Counter(row["current_global_status"] for row in rows)
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "refresh_delta": {
            "frozen_predecessor_positive_count": 49,
            "onl_exact9_delta_count": 9,
            "refreshed_positive_count": 58,
            "changed_event_count": 9,
            "unchanged_event_count": 991,
            "derived_refresh_not_new_authority": True,
        },
        "universe": {
            "event_count": len(rows),
            "unique_canonical_event_id_count": len(
                {row["canonical_event_id"] for row in rows}
            ),
            "duplicate_canonical_event_id_count": len(rows)
            - len({row["canonical_event_id"] for row in rows}),
            "missing_rank_count": 1000
            - len({int(row["scaleup_rank"]) for row in rows}),
            "rank_start": min(int(row["scaleup_rank"]) for row in rows),
            "rank_end": max(int(row["scaleup_rank"]) for row in rows),
            "unique_pdb_count": len({row["pdb_id"] for row in rows}),
            "unique_ligand_component_count": len(
                {row["ligand_component_id"] for row in rows}
            ),
            "canonical_event_set_sha256": _event_set_sha256(
                {row["canonical_event_id"] for row in rows}
            ),
        },
        "structural": {
            "raw_structure_available_count": count_true("raw_structure_available"),
            "exact_cys_sg_event_recovered_count": count_true(
                "exact_cys_sg_event_recovered"
            ),
            "explicit_covalent_evidence_count": count_true(
                "explicit_covalent_evidence"
            ),
            "distance_only_event_inference_used_count": count_true(
                "distance_only_event_inference_used"
            ),
            "full_coordinate_post_evidence_available_count": count_true(
                "full_coordinate_post_evidence_available"
            ),
            "ccd_graph_complete_count": count_true("ccd_graph_complete"),
            "feature_compatible_count": count_true("feature_compatible"),
            "structural_processing_success_count": count_true(
                "structural_processing_success"
            ),
            "post_geometry_source_evidence_available_count": count_true(
                "post_geometry_source_evidence_available"
            ),
            "representation_gap_count": count_true("representation_gap"),
            "feature_incompatible_count": count_true("feature_incompatible"),
        },
        "global_status_distribution": {
            "status_priority": list(predecessor.GLOBAL_STATUSES_V1),
            "counts": {status: global_counts[status] for status in predecessor.GLOBAL_STATUSES_V1},
            "total_count": len(rows),
            "exactly_one_status_per_event": True,
            "presentation_only_not_authority": True,
        },
        "human_review": {
            "priority_review_population_event_count": len(priority_rows),
            "review_unit_count": len({row["review_unit_id"] for row in priority_rows}),
            "completed_event_count": review_counts[generic.COMPLETED_HUMAN_POSITIVE]
            + review_counts[generic.COMPLETED_HUMAN_NEGATIVE],
            "completed_unit_count": len(completed_units),
            "completed_positive_event_count": review_counts[
                generic.COMPLETED_HUMAN_POSITIVE
            ],
            "completed_positive_unit_count": len(
                review_units_by_status[generic.COMPLETED_HUMAN_POSITIVE]
            ),
            "completed_negative_event_count": review_counts[
                generic.COMPLETED_HUMAN_NEGATIVE
            ],
            "completed_negative_unit_count": len(
                review_units_by_status[generic.COMPLETED_HUMAN_NEGATIVE]
            ),
            "unreviewed_event_count": review_counts[generic.CURRENTLY_UNREVIEWED],
            "unreviewed_unit_count": len(
                review_units_by_status[generic.CURRENTLY_UNREVIEWED]
            ),
            "in_progress_event_count": review_counts[generic.CURRENTLY_IN_PROGRESS],
            "in_progress_unit_count": len(
                review_units_by_status[generic.CURRENTLY_IN_PROGRESS]
            ),
            "pending_event_count": review_counts[generic.CURRENTLY_UNREVIEWED]
            + review_counts[generic.CURRENTLY_IN_PROGRESS],
            "current_pending_review_unit_count": len(pending_units),
        },
        "chemistry": {
            "POSITIVE": disposition("POSITIVE", chemistry_positive),
            "NEGATIVE": disposition("NEGATIVE", chemistry_negative),
            "NOT_ESTABLISHED": disposition("NOT_ESTABLISHED", chemistry_not_established),
            "UNRESOLVED": disposition("UNRESOLVED", chemistry_unresolved),
            "positive_source_composition": {
                "CURRENT_RUNTIME": sum(
                    row["positive_authority_source"] == predecessor._RUNTIME_INDEX
                    for row in rows
                ),
                "FFQ": sum(
                    row["positive_authority_source"] == predecessor._FFQ_EVENT
                    for row in rows
                ),
                "POA": sum(
                    row["positive_authority_source"]
                    == "src/covalent_ext/covapie_poa_sample_level_effective_supervision_v1.py"
                    for row in rows
                ),
                "G3H": sum(
                    row["positive_authority_source"] == predecessor._G3H_EVENT
                    for row in rows
                ),
                "ONL": sum(
                    row["positive_authority_source"] == ONL_EVENT_MATRIX_SOURCE
                    for row in rows
                ),
            },
            "positive_authority_collision_count": 0,
        },
        "task_relevance": {
            "RELEVANT": disposition("RELEVANT", task_relevant),
            "NOT_RELEVANT": disposition("NOT_RELEVANT", task_not_relevant),
            "UNRESOLVED": disposition("UNRESOLVED", task_unresolved),
        },
        "reactive_pair": {
            "raw_structural_pair_evidence_count": count_true(
                "reactive_pair_raw_structural_evidence"
            ),
            "sample_level_authoritative_pair_count": count_true(
                "reactive_pair_sample_authoritative"
            ),
            "published_model_bound_target_constructible_count": count_true(
                "reactive_pair_training_target_available"
            ),
            "current_runtime_bound_target_count": count_true(
                "current_runtime_model_usable"
            ),
            "g3h_sample_authority_contribution_count": 8,
            "g3h_training_target_contribution_count": 0,
            "onl_sample_authority_contribution_count": 9,
            "onl_model_bound_target_contribution_count": 0,
            "positive_without_sample_pair_authority_count": sum(
                row["reactive_pair_sample_authoritative"] == "false"
                for row in positive_rows
            ),
        },
        "role": {
            "role_partition_sample_authoritative_count": count_true(
                "role_partition_sample_authoritative"
            ),
            "role_profile_counts": {
                predecessor.STRICT_PROFILE: profile_counts[predecessor.STRICT_PROFILE],
                predecessor.DIRECT_PROFILE: profile_counts[predecessor.DIRECT_PROFILE],
                "other": sum(
                    value
                    for profile, value in profile_counts.items()
                    if profile not in {predecessor.STRICT_PROFILE, predecessor.DIRECT_PROFILE}
                ),
            },
            "canonical_mask_structural_labels_available_count": count_true(
                "canonical_mask_structural_labels_available"
            ),
            "all_five_structurally_applicable_count": sum(
                row["structurally_applicable_task_ids_json"] == "[0,1,2,3,4]"
                for row in rows
            ),
            "direct_profile_A_B3_C_count": sum(
                row["structurally_applicable_task_ids_json"] == "[0,3,4]"
                for row in rows
            ),
            "unknown_role_row_count": sum(
                row["role_partition_sample_authoritative"] == "false" for row in rows
            ),
            "unknown_role_rows_are_not_false_applicability": all(
                row["role_profile"] == predecessor.ROLE_NOT_ESTABLISHED
                and row["structurally_applicable_task_ids_json"] == "null"
                for row in rows
                if row["role_partition_sample_authoritative"] == "false"
            ),
        },
        "canonical_exact5": {
            "task_count": 5,
            "tasks": [
                {
                    "task_id": task_id,
                    "semantic_name": semantic_name,
                    "display_alias": alias,
                    "structurally_applicable_authoritative_role_count": applicability_counts[
                        task_id
                    ],
                }
                for task_id, semantic_name, alias in CANONICAL_EXACT5_V1
            ],
            "B3_present": True,
            "sixth_task_present": False,
        },
        "geometry": {
            "POST_source_evidence_available_count": count_true(
                "post_geometry_source_evidence_available"
            ),
            "POST_sample_authoritative_count": count_true(
                "post_geometry_sample_authoritative"
            ),
            "POST_training_target_available_count": count_true(
                "post_geometry_training_target_available"
            ),
            "PRE_source_evidence_available_count": 0,
            "PRE_sample_authoritative_count": count_true("pre_geometry_authoritative"),
            "PRE_training_target_available_count": count_true(
                "pre_geometry_training_target_available"
            ),
            "PRE_is_v1_hard_requirement": False,
            "POST_to_PRE_promotion_performed": False,
            "PRE_zero_fill_performed": False,
        },
        "training_use": {
            "INCLUDE": disposition("INCLUDE", training_include),
            "EXCLUDE_FROM_TRAINING_ONLY": disposition(
                "EXCLUDE_FROM_TRAINING_ONLY", training_exclude
            ),
            "NOT_APPLICABLE": disposition("NOT_APPLICABLE", training_not_applicable),
            "UNRESOLVED": disposition("UNRESOLVED", training_unresolved),
            "total_count": len(rows),
            "excluded_positive_is_not_chemistry_negative": True,
        },
        "training_stage": {
            "training_use_include_count": count_true("training_use_include"),
            "future_training_admission_candidate_count": count_true(
                "future_training_admission_candidate"
            ),
            "future_candidate_source_composition": {
                "FFQ": 4,
                "POA": 8,
                "G3H": 0,
                "ONL": 0,
            },
            "current_runtime_model_usable_count": count_true(
                "current_runtime_model_usable"
            ),
            "formal_training_admitted_count": count_true("formal_training_admitted"),
            "ready_for_formal_training_event_count": 0,
            "training_materialization_allowed_global_status": (
                "NOT_COMPUTABLE_FROM_CURRENT_PUBLISHED_AUTHORITY"
            ),
            "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
            "feature_semantics_audit_completed": False,
            "step12d_status": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        },
        "blockers": {
            "non_exclusive_counts_must_not_be_summed": True,
            "chemistry_unresolved": {"all_1000": len(chemistry_unresolved)},
            "pair_authority_absent": {
                "all_1000": sum(
                    row["reactive_pair_sample_authoritative"] == "false" for row in rows
                ),
                "within_positive_58": sum(
                    row["reactive_pair_sample_authoritative"] == "false"
                    for row in positive_rows
                ),
            },
            "role_authority_absent": {
                "all_1000": sum(
                    row["role_partition_sample_authoritative"] == "false" for row in rows
                ),
                "within_positive_58": sum(
                    row["role_partition_sample_authoritative"] == "false"
                    for row in positive_rows
                ),
            },
            "human_training_exclusion": {
                "within_positive_58": sum(
                    row["human_training_excluded"] == "true" for row in positive_rows
                )
            },
            "missing_split_authority": {
                "within_positive_58": sum(
                    row["formal_split_authoritative"] == "false" for row in positive_rows
                ),
                "within_include_29": sum(
                    row["formal_split_authoritative"] == "false" for row in include_rows
                ),
            },
            "missing_tensor_integration": {
                "within_positive_58": len(missing_tensor_rows),
                "within_include_29": sum(
                    row["reactive_pair_training_target_available"] == "false"
                    for row in include_rows
                ),
                "all_missing_are_training_excluded_population": all(
                    row["training_use_disposition"] == generic.TRAINING_EXCLUDE
                    for row in missing_tensor_rows
                ),
                "missing_source_composition": {
                    "G3H": sum(
                        row["positive_authority_source"] == predecessor._G3H_EVENT
                        for row in missing_tensor_rows
                    ),
                    "ONL": sum(
                        row["positive_authority_source"] == ONL_EVENT_MATRIX_SOURCE
                        for row in missing_tensor_rows
                    ),
                },
            },
            "missing_POST_training_authority": {
                "within_positive_58": sum(
                    row["post_geometry_training_target_available"] == "false"
                    for row in positive_rows
                ),
                "within_include_29": sum(
                    row["post_geometry_training_target_available"] == "false"
                    for row in include_rows
                ),
            },
            "missing_training_admission": {
                "within_positive_58": sum(
                    row["formal_training_admitted"] == "false" for row in positive_rows
                ),
                "within_include_29": sum(
                    row["formal_training_admitted"] == "false" for row in include_rows
                ),
            },
            "feature_semantics_pending": {"within_positive_58": len(positive_rows)},
        },
        "top_pending_review_units_by_event_yield": top_pending,
        "authority_boundary": {
            "CURRENT_GLOBAL_RECONCILIATION_COMPLETE": True,
            "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE": True,
            "READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION": True,
            "READY_FOR_FORMAL_TRAINING": False,
            "NEXT_RECOMMENDED_MAINLINE": "HIGH_YIELD_HUMAN_REVIEW_EXPANSION",
            "next_priority_review_unit": "COVAPIE_BULK_REVIEW_UNIT_1569D77F66026B58",
            "HUMAN_REVIEW_DECISION_NOT_PERFORMED": True,
            "new_human_authority_created": False,
            "new_chemistry_authority_created": False,
            "new_role_authority_created": False,
            "new_pair_authority_created": False,
            "new_reusable_authority_created": False,
            "tensor_integration_performed": False,
            "loader_modified": False,
            "batch_modified": False,
            "model_forward_performed": False,
            "auxiliary_head_executed": False,
            "loss_executed": False,
            "backward_performed": False,
            "optimizer_created": False,
            "optimizer_step_performed": False,
            "parameter_update_performed": False,
            "training_performed": False,
            "fine_tune_performed": False,
            "training_admission_created": False,
            "training_dataset_changed": False,
            "feature_semantics_audit_performed": False,
            "tensor_status": "NOT_STARTED",
            "training_admission_status": "NOT_STARTED",
            "feature_semantics_status": "AUDIT_REQUIRED_LATER",
            "training_status": "NOT_STARTED",
        },
    }
    return summary


def _merge_semantic_bindings_v1(
    predecessor_bindings: Sequence[Mapping[str, object]],
    additive_bindings: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    by_identity: dict[tuple[str, str], dict[str, object]] = {}
    for raw in (*predecessor_bindings, *additive_bindings):
        row = dict(raw)
        identity = (str(row["path_namespace"]), str(row["path"]))
        prior = by_identity.get(identity)
        if prior is not None and prior != row:
            _fail("SEMANTIC_SOURCE_BINDING_CONFLICT:" + identity[1])
        by_identity[identity] = row
    return tuple(
        sorted(
            by_identity.values(),
            key=lambda row: (str(row["path_namespace"]), str(row["path"])),
        )
    )


def compute_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
    repo_root: Path,
) -> predecessor.Cumulative1000CurrentGlobalReadinessComputationV1:
    """Compute the exact additive ONL refresh entirely from frozen sources."""

    root = repo_root.resolve()
    additive_bindings = _verify_additive_sources(root)
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_v1(
        root
    )
    _assert_predecessor_onl_state_v1(frozen)
    reconciliation = _validate_onl_reconciliation_v1(root)
    matrix_rows = _load_and_validate_onl_event_matrix_v1(root)
    rows = _overlay_onl_exact9_v1(frozen.rows, matrix_rows)
    top_pending = _top_pending_review_units_v1(root, reconciliation)
    summary = _build_summary_v1(rows, top_pending)
    bindings = _merge_semantic_bindings_v1(
        frozen.semantic_source_bindings, additive_bindings
    )
    computation = predecessor.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=rows,
        summary=summary,
        semantic_source_bindings=bindings,
    )
    validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
        computation,
        predecessor_computation=frozen,
    )
    return computation


def _sets_for_algebra_v1(
    rows: Sequence[Mapping[str, str]],
) -> dict[str, set[str]]:
    definitions = {
        "chemistry_positive": ("chemistry_disposition", predecessor.CHEMISTRY_POSITIVE),
        "chemistry_not_established": (
            "chemistry_disposition",
            predecessor.CHEMISTRY_NOT_ESTABLISHED,
        ),
        "chemistry_unresolved": (
            "chemistry_disposition",
            predecessor.CHEMISTRY_UNRESOLVED,
        ),
        "task_relevant": ("task_relevance_disposition", predecessor.TASK_RELEVANT),
        "task_not_relevant": (
            "task_relevance_disposition",
            predecessor.TASK_NOT_RELEVANT,
        ),
        "task_unresolved": (
            "task_relevance_disposition",
            predecessor.TASK_UNRESOLVED,
        ),
        "training_include": ("training_use_disposition", generic.TRAINING_INCLUDE),
        "training_exclude": ("training_use_disposition", generic.TRAINING_EXCLUDE),
        "training_not_applicable": (
            "training_use_disposition",
            generic.TRAINING_NOT_APPLICABLE,
        ),
        "training_unresolved": (
            "training_use_disposition",
            predecessor.TRAINING_UNRESOLVED,
        ),
    }
    return {
        name: {
            row["canonical_event_id"]
            for row in rows
            if row[field] == value
        }
        for name, (field, value) in definitions.items()
    }


def validate_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
    computation: object,
    *,
    predecessor_computation: predecessor.Cumulative1000CurrentGlobalReadinessComputationV1
    | None = None,
) -> bool:
    """Fail closed unless the refreshed rows, summary, and provenance are exact."""

    if type(computation) is not predecessor.Cumulative1000CurrentGlobalReadinessComputationV1:
        _fail("COMPUTATION_TYPE_INVALID")
    rows = computation.rows
    summary = computation.summary
    bindings = computation.semantic_source_bindings
    if (
        type(rows) is not tuple
        or len(rows) != 1000
        or any(type(row) is not dict or tuple(row) != CENSUS_COLUMNS_V1 for row in rows)
    ):
        _fail("CENSUS_EXACT1000_ROW_SCHEMA_INVALID")
    if type(summary) is not dict:
        _fail("SUMMARY_TYPE_INVALID")
    if type(bindings) is not tuple or not bindings:
        _fail("SEMANTIC_SOURCE_BINDINGS_INVALID")

    root = Path(__file__).resolve().parents[2]
    frozen = (
        predecessor.compute_covapie_cumulative1000_current_global_readiness_census_v1(
            root
        )
        if predecessor_computation is None
        else predecessor_computation
    )
    if type(frozen) is not predecessor.Cumulative1000CurrentGlobalReadinessComputationV1:
        _fail("PREDECESSOR_COMPUTATION_TYPE_INVALID")
    _assert_predecessor_onl_state_v1(frozen)

    seen: set[str] = set()
    ranks: list[int] = []
    for row in rows:
        event_id = row["canonical_event_id"]
        if not event_id or event_id in seen:
            _fail("CENSUS_EVENT_ID_EMPTY_OR_DUPLICATE")
        seen.add(event_id)
        try:
            ranks.append(int(row["scaleup_rank"]))
        except ValueError as error:
            raise Cumulative1000CurrentGlobalReadinessCensusWithONLError(
                f"{ERROR_TOKEN}:CENSUS_RANK_INVALID:{event_id}"
            ) from error
    if ranks != list(range(1, 1001)):
        _fail("CENSUS_RANK_GAP_OR_ORDER_INVALID")
    if seen != {row["canonical_event_id"] for row in frozen.rows}:
        _fail("CENSUS_EVENT_SET_IDENTITY_INVALID")

    frozen_by_event = {row["canonical_event_id"]: row for row in frozen.rows}
    refreshed_by_event = {row["canonical_event_id"]: row for row in rows}
    changed = {
        event_id
        for event_id in seen
        if refreshed_by_event[event_id] != frozen_by_event[event_id]
    }
    onl_set = set(ONL_EXACT9_EVENT_IDS_V1)
    if changed != onl_set or len(changed) != 9:
        _fail("PREDECESSOR_DELTA_NOT_EXACT_ONL9")
    for event_id in seen - onl_set:
        if refreshed_by_event[event_id] != frozen_by_event[event_id]:
            _fail("NON_ONL_ROW_CHANGED:" + event_id)

    expected_changed_fields = {
        "current_global_status",
        "current_review_status",
        "human_review_completed",
        "human_review_authority_source",
        "chemistry_disposition",
        "chemistry_authority_source",
        "task_relevance_disposition",
        "task_relevance_authority_source",
        "training_use_disposition",
        "human_training_excluded",
        "reactive_pair_sample_authoritative",
        "role_partition_sample_authoritative",
        "role_profile",
        "canonical_mask_structural_labels_available",
        "structurally_applicable_task_ids_json",
        "training_materialization_allowed_current_source",
        "positive_authority_source",
    }
    expected_onl = {
        "current_global_status": generic.COMPLETED_HUMAN_POSITIVE,
        "priority_review_in_scope": "true",
        "review_unit_id": ONL_REVIEW_UNIT_ID_V1,
        "current_review_status": generic.COMPLETED_HUMAN_POSITIVE,
        "human_review_completed": "true",
        "human_review_authority_source": ONL_FORMAL_DECISION_SOURCE,
        "chemistry_disposition": predecessor.CHEMISTRY_POSITIVE,
        "chemistry_authority_source": ONL_EVENT_MATRIX_SOURCE,
        "task_relevance_disposition": predecessor.TASK_RELEVANT,
        "task_relevance_authority_source": ONL_EVENT_MATRIX_SOURCE,
        "training_use_disposition": generic.TRAINING_EXCLUDE,
        "human_training_excluded": "true",
        "reactive_pair_sample_authoritative": "true",
        "reactive_pair_training_target_available": "false",
        "role_partition_sample_authoritative": "true",
        "role_profile": predecessor.DIRECT_PROFILE,
        "canonical_mask_structural_labels_available": "true",
        "structurally_applicable_task_ids_json": ONL_DIRECT_TASK_IDS_CELL_V1,
        "post_geometry_sample_authoritative": "false",
        "post_geometry_training_target_available": "false",
        "pre_geometry_authoritative": "false",
        "pre_geometry_training_target_available": "false",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "formal_split_authoritative": "false",
        "formal_split": "",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "training_materialization_allowed_current_source": "false",
        "positive_authority_source": ONL_EVENT_MATRIX_SOURCE,
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    }
    for event_id in ONL_EXACT9_EVENT_IDS_V1:
        before = frozen_by_event[event_id]
        after = refreshed_by_event[event_id]
        changed_fields = {
            field for field in CENSUS_COLUMNS_V1 if before[field] != after[field]
        }
        if changed_fields != expected_changed_fields:
            _fail("ONL_CHANGED_FIELD_SET_INVALID:" + event_id)
        if not changed_fields <= _AUTHORIZED_ONL_OVERLAY_FIELDS_V1:
            _fail("ONL_UNAUTHORIZED_FIELD_CHANGED:" + event_id)
        if any(before[field] != after[field] for field in _STRUCTURAL_IDENTITY_FIELDS_V1):
            _fail("ONL_STRUCTURAL_EVIDENCE_CHANGED:" + event_id)
        if any(after[field] != value for field, value in expected_onl.items()):
            _fail("ONL_REFRESHED_SEMANTICS_INVALID:" + event_id)

    previous_sets = _sets_for_algebra_v1(frozen.rows)
    current_sets = _sets_for_algebra_v1(rows)
    if previous_sets["chemistry_positive"] & onl_set:
        _fail("ONL_PREDECESSOR_POSITIVE_INTERSECTION_NOT_EMPTY")
    exact_algebra = (
        current_sets["chemistry_positive"]
        == previous_sets["chemistry_positive"] | onl_set
        and current_sets["chemistry_unresolved"]
        == previous_sets["chemistry_unresolved"] - onl_set
        and current_sets["task_relevant"]
        == previous_sets["task_relevant"] | onl_set
        and current_sets["task_unresolved"]
        == previous_sets["task_unresolved"] - onl_set
        and current_sets["training_exclude"]
        == previous_sets["training_exclude"] | onl_set
        and current_sets["training_unresolved"]
        == previous_sets["training_unresolved"] - onl_set
        and current_sets["chemistry_not_established"]
        == previous_sets["chemistry_not_established"]
        and current_sets["task_not_relevant"] == previous_sets["task_not_relevant"]
        and current_sets["training_not_applicable"]
        == previous_sets["training_not_applicable"]
        and current_sets["training_include"] == previous_sets["training_include"]
    )
    if not exact_algebra:
        _fail("ONL_EXACT_SET_ALGEBRA_INVALID")

    expected_dispositions = {
        "chemistry": Counter(
            {
                predecessor.CHEMISTRY_POSITIVE: 58,
                predecessor.CHEMISTRY_NOT_ESTABLISHED: 86,
                predecessor.CHEMISTRY_UNRESOLVED: 856,
            }
        ),
        "task": Counter(
            {
                predecessor.TASK_RELEVANT: 59,
                predecessor.TASK_NOT_RELEVANT: 86,
                predecessor.TASK_UNRESOLVED: 855,
            }
        ),
        "training": Counter(
            {
                generic.TRAINING_INCLUDE: 29,
                generic.TRAINING_EXCLUDE: 29,
                generic.TRAINING_NOT_APPLICABLE: 86,
                predecessor.TRAINING_UNRESOLVED: 856,
            }
        ),
    }
    if Counter(row["chemistry_disposition"] for row in rows) != expected_dispositions[
        "chemistry"
    ]:
        _fail("CENSUS_CHEMISTRY_DISTRIBUTION_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != expected_dispositions[
        "task"
    ]:
        _fail("CENSUS_TASK_DISTRIBUTION_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != expected_dispositions[
        "training"
    ]:
        _fail("CENSUS_TRAINING_DISTRIBUTION_INVALID")
    if Counter(row["current_global_status"] for row in rows) != Counter(
        _EXPECTED_GLOBAL_STATUS_COUNTS_V1
    ):
        _fail("CENSUS_EXACT11_DISTRIBUTION_INVALID")
    for field, expected in _EXPECTED_BOOLEAN_COUNTS_V1.items():
        if sum(row[field] == "true" for row in rows) != expected:
            _fail("CENSUS_BOOLEAN_COUNT_INVALID:" + field)
    if Counter(
        row["role_profile"]
        for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    ) != Counter({predecessor.STRICT_PROFILE: 31, predecessor.DIRECT_PROFILE: 27}):
        _fail("CENSUS_ROLE_PROFILE_DISTRIBUTION_INVALID")

    for row in rows:
        event_id = row["canonical_event_id"]
        if row["role_partition_sample_authoritative"] == "true":
            expected_task_ids = (
                [0, 1, 2, 3, 4]
                if row["role_profile"] == predecessor.STRICT_PROFILE
                else [0, 3, 4]
                if row["role_profile"] == predecessor.DIRECT_PROFILE
                else None
            )
            try:
                task_ids = json.loads(row["structurally_applicable_task_ids_json"])
            except json.JSONDecodeError as error:
                raise Cumulative1000CurrentGlobalReadinessCensusWithONLError(
                    f"{ERROR_TOKEN}:ROLE_TASK_IDS_JSON_INVALID:{event_id}"
                ) from error
            if expected_task_ids is None or task_ids != expected_task_ids or 3 not in task_ids:
                _fail("ROLE_EXACT5_APPLICABILITY_INVALID:" + event_id)
        elif (
            row["role_profile"] != predecessor.ROLE_NOT_ESTABLISHED
            or row["canonical_mask_structural_labels_available"] != "false"
            or row["structurally_applicable_task_ids_json"] != "null"
        ):
            _fail("ROLELESS_ROW_FALSE_APPLICABILITY_NOT_UNKNOWN:" + event_id)
        if row["reactive_pair_sample_authoritative"] == "true" and row[
            "chemistry_disposition"
        ] != predecessor.CHEMISTRY_POSITIVE:
            _fail("PAIR_AUTHORITY_WITHOUT_POSITIVE_CHEMISTRY:" + event_id)
        if row["reactive_pair_training_target_available"] == "true" and row[
            "reactive_pair_sample_authoritative"
        ] != "true":
            _fail("PAIR_TARGET_WITHOUT_SAMPLE_AUTHORITY:" + event_id)
        if row["pre_geometry_authoritative"] != "false" or row[
            "pre_geometry_training_target_available"
        ] != "false":
            _fail("POST_TO_PRE_OR_PRE_ZERO_FILL_DETECTED:" + event_id)
        if row["training_use_include"] != (
            "true" if row["training_use_disposition"] == generic.TRAINING_INCLUDE else "false"
        ):
            _fail("TRAINING_USE_INCLUDE_BOOLEAN_INVALID:" + event_id)

    reconciliation = _validate_onl_reconciliation_v1(root)
    expected_top = _top_pending_review_units_v1(root, reconciliation)
    if summary != _build_summary_v1(rows, expected_top):
        _fail("SUMMARY_NOT_EXACTLY_DERIVED_FROM_REFRESHED_ROWS_AND_FULL_QUEUE")

    identities: set[tuple[str, str]] = set()
    for binding in bindings:
        if type(binding) is not dict or set(binding) != {
            "artifact_role",
            "path",
            "path_namespace",
            "byte_count",
            "sha256",
        }:
            _fail("SEMANTIC_SOURCE_BINDING_SCHEMA_INVALID")
        path = binding["path"]
        namespace = binding["path_namespace"]
        if (
            type(path) is not str
            or not path
            or type(namespace) is not str
            or namespace not in {"repository_relative", "repository_parent_relative"}
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
            or type(binding["artifact_role"]) is not str
            or not binding["artifact_role"]
            or type(binding["byte_count"]) is not int
            or binding["byte_count"] <= 0
            or type(binding["sha256"]) is not str
            or not _SHA_PATTERN.fullmatch(binding["sha256"])
        ):
            _fail("SEMANTIC_SOURCE_BINDING_VALUE_INVALID")
        identity = (namespace, path)
        if identity in identities:
            _fail("SEMANTIC_SOURCE_BINDING_DUPLICATE")
        identities.add(identity)
    frozen_identities = {
        (str(binding["path_namespace"]), str(binding["path"]))
        for binding in frozen.semantic_source_bindings
    }
    if not frozen_identities <= identities:
        _fail("PREDECESSOR_SEMANTIC_BINDINGS_NOT_PRESERVED")
    for role, relative, namespace, byte_count, sha256 in _ADDITIVE_SOURCE_SPECS_V1:
        expected = {
            "artifact_role": role,
            "path": relative.as_posix(),
            "path_namespace": namespace,
            "byte_count": byte_count,
            "sha256": sha256,
        }
        matches = [
            binding
            for binding in bindings
            if binding["path_namespace"] == namespace
            and binding["path"] == relative.as_posix()
        ]
        if matches != [expected]:
            _fail("ADDITIVE_SEMANTIC_SOURCE_BINDING_INVALID:" + role)

    if _sha256(_csv_bytes(rows)) != _EXPECTED_REFRESHED_CENSUS_SHA256_V1:
        _fail("REFRESHED_CENSUS_EXACT_SHA256_INVALID")
    if _sha256(_json_bytes(summary)) != _EXPECTED_REFRESHED_SUMMARY_SHA256_V1:
        _fail("REFRESHED_SUMMARY_EXACT_SHA256_INVALID")
    if _sha256(
        _canonical_json(list(bindings)).encode("utf-8")
    ) != _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1:
        _fail("REFRESHED_SEMANTIC_BINDINGS_EXACT_SHA256_INVALID")
    return True


def _validate_text_payload(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("OUTPUT_UTF8_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithONLError(
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


def build_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1(
    repo_root: Path,
) -> dict[str, bytes]:
    """Build the deterministic Exact3 outputs without repository writes."""

    root = repo_root.resolve()
    computation = compute_covapie_cumulative1000_current_global_readiness_census_with_onl_v1(
        root
    )
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
        "candidate_inventory": {
            "exact_file_count": 7,
            "paths": list(EXACT7_PATHS_V1),
        },
        "candidate_contract_bindings": _candidate_contract_bindings_v1(root),
        "semantic_source_bindings": list(computation.semantic_source_bindings),
        "derived_projection_contract_digests": {
            "refreshed_census_sha256": _EXPECTED_REFRESHED_CENSUS_SHA256_V1,
            "refreshed_summary_sha256": _EXPECTED_REFRESHED_SUMMARY_SHA256_V1,
            "semantic_source_bindings_sha256": (
                _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1
            ),
            "authority_created": False,
        },
        "output_inventory": {
            "exact_output_count": 3,
            "paths": [
                (OUTPUT_DIRECTORY_RELATIVE / CENSUS_FILE).as_posix(),
                (OUTPUT_DIRECTORY_RELATIVE / SUMMARY_FILE).as_posix(),
                (OUTPUT_DIRECTORY_RELATIVE / MANIFEST_FILE).as_posix(),
            ],
        },
        "output_bindings_excluding_manifest_self": output_bindings,
        "manifest_self_binding": {
            "path": (OUTPUT_DIRECTORY_RELATIVE / MANIFEST_FILE).as_posix(),
            "sha256_recorded_inside_self": False,
            "policy": "MANIFEST_SELF_SHA256_PROHIBITED",
        },
        "determinism_contract": {
            "utf8": True,
            "lf_only": True,
            "single_final_lf": True,
            "timestamps_recorded": False,
            "machine_absolute_paths_recorded": False,
            "live_git_state_recorded": False,
        },
        "authority_boundary": computation.summary["authority_boundary"],
    }
    manifest_payload = _json_bytes(manifest)
    _validate_text_payload(manifest_payload, MANIFEST_FILE)
    manifest_text = manifest_payload.decode("utf-8").lower()
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
        if token in manifest_text:
            _fail("MANIFEST_LIFECYCLE_FIELD_FORBIDDEN")
    manifest_path = (OUTPUT_DIRECTORY_RELATIVE / MANIFEST_FILE).as_posix()
    if any(binding["path"] == manifest_path for binding in output_bindings):
        _fail("MANIFEST_SELF_HASH_PROHIBITION_VIOLATED")
    return {
        CENSUS_FILE: census_payload,
        SUMMARY_FILE: summary_payload,
        MANIFEST_FILE: manifest_payload,
    }


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except OSError as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise Cumulative1000CurrentGlobalReadinessCensusWithONLError(
            f"{ERROR_TOKEN}:OUTPUT_WRITE_FAILED:{path.name}"
        ) from error


def materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1(
    repo_root: Path,
    output_directory: Path | None = None,
) -> dict[str, bytes]:
    """Write only the Exact3 outputs after complete source validation."""

    root = repo_root.resolve()
    output = (
        root / OUTPUT_DIRECTORY_RELATIVE
        if output_directory is None
        else output_directory.resolve()
    )
    try:
        output.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithONLError(
            f"{ERROR_TOKEN}:OUTPUT_DIRECTORY_CREATE_FAILED"
        ) from error
    artifacts = build_covapie_cumulative1000_current_global_readiness_artifacts_with_onl_v1(
        root
    )
    existing = {path.name for path in output.iterdir() if path.is_file()}
    unexpected = existing - set(artifacts)
    if unexpected:
        _fail("OUTPUT_DIRECTORY_UNEXPECTED_FILE:" + sorted(unexpected)[0])
    for filename in (CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE):
        _atomic_write(output / filename, artifacts[filename])
    return artifacts
