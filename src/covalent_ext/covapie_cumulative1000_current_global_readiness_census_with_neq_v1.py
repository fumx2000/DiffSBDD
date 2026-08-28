"""Additive cumulative1000 readiness census refresh for published NEQ Exact6.

This successor consumes the frozen YUN-refreshed census plus already-published
NEQ ingestion and reconciliation authority. It deep-copies the predecessor
rows and overlays only NEQ Exact6. It creates no human, chemistry, pair, role,
split, tensor, reusable, training-admission, or training authority.
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
from typing import Any, NoReturn

from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import covapie_completed_human_decision_reconciliation_with_neq_v1 as neq_reconciliation
from . import covapie_cumulative1000_current_global_readiness_census_with_yun_v1 as predecessor
from . import covapie_neq_completed_decision_ingestion_and_task_label_availability_v1 as neq_ingestion


__all__ = (
    "Cumulative1000CurrentGlobalReadinessCensusWithNEQError",
    "compute_covapie_cumulative1000_current_global_readiness_census_with_neq_v1",
    "validate_covapie_cumulative1000_current_global_readiness_census_with_neq_v1",
    "build_covapie_cumulative1000_current_global_readiness_artifacts_with_neq_v1",
    "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_neq_v1",
)


SCHEMA_VERSION = "covapie_cumulative1000_current_global_readiness_census_with_neq_v1"
STAGE = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_NEQ_V1"
ERROR_TOKEN = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_NEQ_V1_ERROR"

OUTPUT_DIRECTORY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_neq_v1"
)
CENSUS_FILE = "covapie_cumulative1000_current_global_readiness_census_with_neq_v1.csv"
SUMMARY_FILE = "covapie_cumulative1000_current_global_readiness_summary_with_neq_v1.json"
MANIFEST_FILE = "covapie_cumulative1000_current_global_readiness_manifest_with_neq_v1.json"

PRODUCTION_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_with_neq_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_neq_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_cumulative1000_current_global_readiness_census_with_neq_v1.py"
)
GUIDE_RELATIVE = Path(
    "docs/covapie_cumulative1000_current_global_readiness_census_with_neq_v1_guide.md"
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
NEQ_EXACT6_EVENT_IDS_V1 = neq_ingestion.EXPECTED_EVENT_IDS
NEQ_EXACT6_RANKS_V1 = neq_ingestion.EXPECTED_RANKS
NEQ_REVIEW_UNIT_ID_V1 = neq_ingestion.EXPECTED_REVIEW_UNIT_ID
NEQ_DIRECT_TASK_IDS_CELL_V1 = "[0,3,4]"

PREDECESSOR_OWNER_RELATIVE = predecessor.PRODUCTION_RELATIVE
PREDECESSOR_CENSUS_RELATIVE = (
    predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.CENSUS_FILE
)
PREDECESSOR_SUMMARY_RELATIVE = (
    predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.SUMMARY_FILE
)
PREDECESSOR_MANIFEST_RELATIVE = (
    predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.MANIFEST_FILE
)
NEQ_RECONCILIATION_OWNER_RELATIVE = Path(
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_neq_v1.py"
)
NEQ_INGESTION_OWNER_RELATIVE = neq_ingestion.SOURCE_RELATIVE
NEQ_EVENT_MATRIX_RELATIVE = neq_ingestion.OUTPUT_ROOT_RELATIVE / neq_ingestion.MATRIX
NEQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = (
    neq_ingestion.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
)
PRIORITY_QUEUE_RELATIVE = predecessor.PRIORITY_QUEUE_RELATIVE

NEQ_EVENT_MATRIX_SOURCE = NEQ_EVENT_MATRIX_RELATIVE.as_posix()
NEQ_FORMAL_DECISION_SOURCE = (
    NEQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
)

_EXPECTED_GLOBAL_STATUS_COUNTS_V1 = {
    generic.CURRENTLY_UNREVIEWED: 236,
    generic.CURRENTLY_IN_PROGRESS: 0,
    generic.COMPLETED_HUMAN_POSITIVE: 78,
    generic.COMPLETED_HUMAN_NEGATIVE: 54,
    generic.COMPLETED_PARTIAL_AUTHORITY: 1,
    generic.CURRENT_RUNTIME_MODEL_USABLE: 17,
    generic.PUBLISHED_EXACT_AUTO_NEGATIVE: 32,
    "LEAKAGE_EXISTING_GROUP_CONFLICT": 369,
    "STRUCTURAL_EVIDENCE_INCOMPLETE": 133,
    "QUARANTINE_REPRESENTATION_GAP": 78,
    "REJECTED_FEATURE_INCOMPATIBLE": 2,
}
_EXPECTED_BOOLEAN_COUNTS_V1 = dict(predecessor._EXPECTED_BOOLEAN_COUNTS_V1)
_EXPECTED_BOOLEAN_COUNTS_V1.update(
    {
        "reactive_pair_sample_authoritative": 95,
        "role_partition_sample_authoritative": 95,
        "canonical_mask_structural_labels_available": 95,
        "training_use_include": 36,
        "future_training_admission_candidate": 19,
    }
)

# Frozen after the first fully source-derived build and semantic validation.
# These are derived projection contract digests, never authority.
_EXPECTED_REFRESHED_CENSUS_SHA256_V1 = (
    "8ffbb6df299321393b0aeba8945ed6a4de7f74ed659253d874494a7757e782f2"
)
_EXPECTED_REFRESHED_SUMMARY_SHA256_V1 = (
    "08f61b61014658a51be184285aae478989717f67808ef0fe8e0dc09d068312d9"
)
_EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1 = (
    "50073d65d856655a6235a7518cc31eb49ef3c1545cb36db948c9f325c5dd95d9"
)

_SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_STRUCTURAL_IDENTITY_FIELDS_V1 = predecessor._STRUCTURAL_IDENTITY_FIELDS_V1
_AUTHORIZED_NEQ_OVERLAY_FIELDS_V1 = frozenset(
    {
        "canonical_mask_structural_labels_available",
        "chemistry_authority_source",
        "chemistry_disposition",
        "current_global_status",
        "current_review_status",
        "human_review_authority_source",
        "human_review_completed",
        "human_training_excluded",
        "positive_authority_source",
        "reactive_pair_sample_authoritative",
        "role_partition_sample_authoritative",
        "role_profile",
        "structurally_applicable_task_ids_json",
        "task_relevance_authority_source",
        "task_relevance_disposition",
        "training_materialization_allowed_current_source",
        "training_use_disposition",
    }
)
_EXPECTED_NEQ_STRUCTURAL_CELLS_V1 = {
    "raw_structure_available": "true",
    "exact_cys_sg_event_recovered": "true",
    "explicit_covalent_evidence": "true",
    "distance_only_event_inference_used": "false",
    "full_coordinate_post_evidence_available": "true",
    "ccd_graph_complete": "true",
    "feature_compatible": "true",
    "structural_processing_success": "true",
    "post_geometry_source_evidence_available": "true",
    "representation_gap": "false",
    "feature_incompatible": "false",
    "reactive_pair_raw_structural_evidence": "true",
}

_ADDITIVE_SOURCE_SPECS_V1 = (
    (
        "PREDECESSOR_YUN_CENSUS_OWNER",
        PREDECESSOR_OWNER_RELATIVE,
        "repository_relative",
        62922,
        "c26608686cf293026a5a4f52de931fb2de169eb7462338656dd252abc5177624",
    ),
    (
        "PREDECESSOR_YUN_MATERIALIZED_CENSUS",
        PREDECESSOR_CENSUS_RELATIVE,
        "repository_relative",
        518137,
        "28eaa9833d69f191bf7eee91956588324ea1a3d145ebe5a99a31752a42e962e3",
    ),
    (
        "PREDECESSOR_YUN_MATERIALIZED_SUMMARY",
        PREDECESSOR_SUMMARY_RELATIVE,
        "repository_relative",
        15391,
        "084d264f874547544a6b674cc1672298d2ac4eb08f61d139aa654f975d1c5767",
    ),
    (
        "NEQ_RECONCILIATION_SUCCESSOR",
        NEQ_RECONCILIATION_OWNER_RELATIVE,
        "repository_relative",
        12649,
        "ed5502e047124c30a0c16cb5b93c12d676966c271e24173eea96cea27d7f2c98",
    ),
    (
        "NEQ_INGESTION_OWNER",
        NEQ_INGESTION_OWNER_RELATIVE,
        "repository_relative",
        96020,
        "dee80c8ce26e0be030d3063e8ab9831c1bc0650c6a2dc9798c3c21007faae290",
    ),
    (
        "NEQ_EVENT_TASK_LABEL_AVAILABILITY",
        NEQ_EVENT_MATRIX_RELATIVE,
        "repository_relative",
        11706,
        "b4b9a301440724464cb92f1b0f28ef1151b24b12eb3ec001a971dacda3632d4a",
    ),
    (
        "NEQ_FORMAL_HUMAN_DECISION",
        NEQ_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
        "repository_parent_relative",
        33908,
        "c5aa577f8b507b9bf6eb8d22207c8c11e3858ddd138c034d31d6f32d40b6c73c",
    ),
)
_PREDECESSOR_MANIFEST_SPEC_V1 = (
    33503,
    "a4ee67e647dd87eee1021ad496567df4e3664f47a3951837bb9ba41a91e8e58e",
)


class Cumulative1000CurrentGlobalReadinessCensusWithNEQError(ValueError):
    """Raised unless the additive NEQ refresh is exactly source-derived."""


def _fail(reason: str) -> NoReturn:
    raise Cumulative1000CurrentGlobalReadinessCensusWithNEQError(
        f"{ERROR_TOKEN}:{reason}"
    )


_sha256 = predecessor._sha256
_canonical_json = predecessor._canonical_json
_json_bytes = predecessor._json_bytes
_event_set_sha256 = predecessor._event_set_sha256
_csv_bytes = predecessor._csv_bytes


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        _fail("SOURCE_NOT_REGULAR_FILE:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithNEQError(
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
        payload = _read_regular_file(_resolve_source(root, namespace, relative), role)
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
    manifest = _read_regular_file(
        root / PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_YUN_MANIFEST"
    )
    if (
        len(manifest) != _PREDECESSOR_MANIFEST_SPEC_V1[0]
        or _sha256(manifest) != _PREDECESSOR_MANIFEST_SPEC_V1[1]
    ):
        _fail("PREDECESSOR_YUN_MANIFEST_BINDING_INVALID")
    return tuple(bindings)


def _validate_neq_matrix_rows_v1(
    rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    normalized = tuple(dict(row) for row in rows)
    if (
        len(normalized) != 6
        or tuple(row["canonical_event_id"] for row in normalized)
        != NEQ_EXACT6_EVENT_IDS_V1
        or tuple(int(row["scaleup_rank"]) for row in normalized)
        != NEQ_EXACT6_RANKS_V1
        or len({row["canonical_event_id"] for row in normalized}) != 6
    ):
        _fail("NEQ_EVENT_MATRIX_IDENTITY_NOT_EXACT6")
    if Counter(row["cys_residue_id"] for row in normalized) != Counter(
        {"CYS:22-": 3, "CYS:81-": 3}
    ):
        _fail("NEQ_EVENT_MATRIX_SITE_IDENTITY_NOT_3_PLUS_3")
    if {row["pdb_id"] for row in normalized} != {"3V61", "3V62"}:
        _fail("NEQ_EVENT_MATRIX_PDB_IDENTITY_INVALID")
    expected_cells = {
        "human_task_relevance_decision": generic.TASK_RELEVANT,
        "chemistry_known_positive": "true",
        "negative_chemistry": "false",
        "task_domain_negative": "false",
        "reactive_pair_human_decision_available": "true",
        "reactive_pair_human_authoritative": "true",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C3",
        "ligand_reactive_atom_element": "C",
        "role_partition_human_decision_available": "true",
        "role_partition_human_authoritative": "true",
        "selected_role_candidate_index_0based": "7",
        "role_profile": base.DIRECT_PROFILE,
        "global_canonical_task_count": "5",
        "direct_profile_applicable_task_ids_json": NEQ_DIRECT_TASK_IDS_CELL_V1,
        "formal_event_training_use_decision": generic.TRAINING_EXCLUDE,
        "event_training_use_human_decision_available": "true",
        "training_use_allowed": "false",
        "training_use_include": "false",
        "human_training_excluded": "true",
        "candidate_for_future_training_admission": "false",
        "future_training_admission_status": "",
        "training_admitted": "false",
        "training_materialization_allowed_now": "false",
        "current_runtime_model_usable": "false",
        "source_CCD_C2_C3_bond_order": "DOUB",
        "explicit_SG_C3_connection_available": "true",
        "complete_POST_adduct_topology_authority_available": "false",
        "PRE_geometry_authority_available": "false",
        "PRE_geometry_training_label_available_now": "false",
        "PRE_precursor_topology_authority_available": "false",
        "PRE_reconstruction_performed": "false",
        "POST_bond_order_reconstruction_performed": "false",
        "second_reconstructed_POST_graph_created": "false",
        "POST_source_evidence_available": "true",
        "POST_geometry_training_label_available_now": "false",
        "reaction_family_target_available": "false",
        "warhead_rule_target_available": "false",
        "warhead_type_target_available": "false",
        "reusable_chemistry_authority_available": "false",
        "reusable_pair_authority_available": "false",
        "reusable_role_authority_available": "false",
        "formal_split_authority_created": "false",
        "tensor_target_created": "false",
        "parameter_update_authorization": "false",
        "authority_source": neq_ingestion.AUTHORITY_SOURCE,
        "authority_scope": neq_ingestion.AUTHORITY_SCOPE,
        "authority_ingested": "true",
        "authority_created_by_this_ingestion": "false",
    }
    semantic_names = [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    aliases = ["A", "B", "B2", "B3", "C"]
    for row in normalized:
        event_id = row["canonical_event_id"]
        if any(row[key] != value for key, value in expected_cells.items()):
            _fail("NEQ_EVENT_MATRIX_SEMANTICS_INVALID:" + event_id)
        try:
            applicability = json.loads(row["canonical_task_applicability_json"])
        except json.JSONDecodeError as error:
            raise Cumulative1000CurrentGlobalReadinessCensusWithNEQError(
                f"{ERROR_TOKEN}:NEQ_EXACT5_JSON_INVALID:{event_id}"
            ) from error
        if (
            len(applicability) != 5
            or [item["task_id"] for item in applicability] != list(range(5))
            or [item["semantic_long_name"] for item in applicability]
            != semantic_names
            or [item["display_alias"] for item in applicability] != aliases
            or [
                item["task_id"]
                for item in applicability
                if item["structurally_applicable"]
            ]
            != [0, 3, 4]
            or applicability[3]["semantic_long_name"] != "scaffold_only"
        ):
            _fail("NEQ_EVENT_MATRIX_EXACT5_INVALID:" + event_id)
    return normalized


def _load_and_validate_neq_event_matrix_v1(
    root: Path,
) -> tuple[dict[str, str], ...]:
    payload = _read_regular_file(root / NEQ_EVENT_MATRIX_RELATIVE, "NEQ_EVENT_MATRIX")
    if len(payload) != 11706 or _sha256(payload) != _ADDITIVE_SOURCE_SPECS_V1[5][4]:
        _fail("NEQ_EVENT_MATRIX_BINDING_INVALID")
    source_derived = neq_ingestion.build_artifacts_v1(root)
    if source_derived[neq_ingestion.MATRIX] != payload:
        _fail("NEQ_EVENT_MATRIX_NOT_SOURCE_DERIVED")
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithNEQError(
            f"{ERROR_TOKEN}:NEQ_EVENT_MATRIX_NOT_UTF8"
        ) from error
    if tuple(reader.fieldnames or ()) != neq_ingestion.MATRIX_HEADER:
        _fail("NEQ_EVENT_MATRIX_HEADER_INVALID")
    return _validate_neq_matrix_rows_v1(tuple(dict(row) for row in reader))


def _validate_neq_reconciliation_v1(root: Path) -> generic.ReconciliationResult:
    result = neq_reconciliation.reconcile_real_completed_human_decisions_with_neq_v1(
        root
    )
    if result.review_summary != {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 78,
        "completed_positive_unit_count": 9,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 102,
        "completed_total_unit_count": 13,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 236,
        "unreviewed_unit_count": 118,
    }:
        _fail("NEQ_RECONCILIATION_SUMMARY_INVALID")
    if len(result.normalized_facts) != 78 or Counter(
        fact.training_disposition for fact in result.normalized_facts
    ) != Counter({generic.TRAINING_INCLUDE: 19, generic.TRAINING_EXCLUDE: 59}):
        _fail("NEQ_RECONCILIATION_NORMALIZED_FACTS_INVALID")
    rows = [
        row
        for row in result.reconciled_rows
        if row["raw_review_unit_id"] == NEQ_REVIEW_UNIT_ID_V1
    ]
    if (
        len(rows) != 6
        or {row["canonical_event_id"] for row in rows}
        != set(NEQ_EXACT6_EVENT_IDS_V1)
        or any(
            row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
            for row in rows
        )
    ):
        _fail("NEQ_RECONCILIATION_EXACT6_INVALID")
    return result


def _assert_predecessor_neq_state_v1(
    computation: base.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    neq_set = set(NEQ_EXACT6_EVENT_IDS_V1)
    rows = [
        row for row in computation.rows if row["canonical_event_id"] in neq_set
    ]
    if len(rows) != 6 or tuple(
        int(row["scaleup_rank"]) for row in rows
    ) != NEQ_EXACT6_RANKS_V1:
        _fail("PREDECESSOR_NEQ_EXACT6_IDENTITY_INVALID")
    expected = {
        "current_global_status": generic.CURRENTLY_UNREVIEWED,
        "priority_review_in_scope": "true",
        "review_unit_id": NEQ_REVIEW_UNIT_ID_V1,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "human_review_completed": "false",
        "chemistry_disposition": base.CHEMISTRY_UNRESOLVED,
        "task_relevance_disposition": base.TASK_UNRESOLVED,
        "training_use_disposition": base.TRAINING_UNRESOLVED,
        "human_training_excluded": "false",
        "reactive_pair_raw_structural_evidence": "true",
        "reactive_pair_sample_authoritative": "false",
        "reactive_pair_training_target_available": "false",
        "role_partition_sample_authoritative": "false",
        "role_profile": base.ROLE_NOT_ESTABLISHED,
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
        "post_geometry_sample_authoritative": "false",
        "post_geometry_training_target_available": "false",
        "pre_geometry_authoritative": "false",
        "pre_geometry_training_target_available": "false",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "formal_split_authoritative": "false",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
    }
    if any(any(row[key] != value for key, value in expected.items()) for row in rows):
        _fail("PREDECESSOR_NEQ_STATE_INVALID")
    if any(
        any(
            row[field] != value
            for field, value in _EXPECTED_NEQ_STRUCTURAL_CELLS_V1.items()
        )
        for row in rows
    ):
        _fail("PREDECESSOR_NEQ_STRUCTURAL_COVERAGE_INVALID")
    chemistry = Counter(row["chemistry_disposition"] for row in computation.rows)
    relevance = Counter(
        row["task_relevance_disposition"] for row in computation.rows
    )
    training = Counter(row["training_use_disposition"] for row in computation.rows)
    if chemistry[base.CHEMISTRY_POSITIVE] != 89:
        _fail("PREDECESSOR_POSITIVE_COUNT_NOT_89")
    if relevance[base.TASK_RELEVANT] != 90:
        _fail("PREDECESSOR_TASK_RELEVANT_COUNT_NOT_90")
    if training[generic.TRAINING_INCLUDE] != 36:
        _fail("PREDECESSOR_TRAINING_INCLUDE_COUNT_NOT_36")
    if training[generic.TRAINING_EXCLUDE] != 53:
        _fail("PREDECESSOR_TRAINING_EXCLUDE_COUNT_NOT_53")
    if sum(
        row["future_training_admission_candidate"] == "true"
        for row in computation.rows
    ) != 19:
        _fail("PREDECESSOR_FUTURE_CANDIDATE_COUNT_NOT_19")


def _overlay_neq_exact6_v1(
    predecessor_rows: Sequence[Mapping[str, str]],
    matrix_rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    validated_matrix = _validate_neq_matrix_rows_v1(matrix_rows)
    matrix_by_event = {
        row["canonical_event_id"]: row for row in validated_matrix
    }
    rows = deepcopy([dict(row) for row in predecessor_rows])
    for row in rows:
        event_id = row["canonical_event_id"]
        if event_id not in matrix_by_event:
            continue
        matrix = matrix_by_event[event_id]
        if (
            row["scaleup_rank"] != matrix["scaleup_rank"]
            or row["pdb_id"] != matrix["pdb_id"]
            or row["ligand_component_id"] != "NEQ"
            or row["review_unit_id"] != NEQ_REVIEW_UNIT_ID_V1
        ):
            _fail("NEQ_MATRIX_PREDECESSOR_IDENTITY_MISMATCH:" + event_id)
        row.update(
            {
                "current_global_status": generic.COMPLETED_HUMAN_POSITIVE,
                "current_review_status": generic.COMPLETED_HUMAN_POSITIVE,
                "human_review_completed": "true",
                "human_review_authority_source": NEQ_FORMAL_DECISION_SOURCE,
                "chemistry_disposition": base.CHEMISTRY_POSITIVE,
                "chemistry_authority_source": NEQ_EVENT_MATRIX_SOURCE,
                "positive_authority_source": NEQ_EVENT_MATRIX_SOURCE,
                "task_relevance_disposition": base.TASK_RELEVANT,
                "task_relevance_authority_source": NEQ_EVENT_MATRIX_SOURCE,
                "training_use_disposition": generic.TRAINING_EXCLUDE,
                "human_training_excluded": "true",
                "reactive_pair_sample_authoritative": "true",
                "reactive_pair_training_target_available": "false",
                "role_partition_sample_authoritative": "true",
                "role_profile": base.DIRECT_PROFILE,
                "canonical_mask_structural_labels_available": "true",
                "structurally_applicable_task_ids_json": NEQ_DIRECT_TASK_IDS_CELL_V1,
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
                "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
            }
        )
    return tuple(rows)


def _top_pending_review_units_v1(
    root: Path,
    reconciliation: generic.ReconciliationResult,
) -> list[dict[str, object]]:
    payload = _read_regular_file(root / PRIORITY_QUEUE_RELATIVE, "PRIORITY_QUEUE")
    if (
        len(payload) != 50116
        or _sha256(payload)
        != "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"
    ):
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
    if len(candidates) != 118:
        _fail("CURRENT_PENDING_REVIEW_UNIT_COUNT_INVALID")
    top: list[dict[str, object]] = []
    for rank, (_negative, _priority, unit, row, status) in enumerate(
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
    if not (
        first["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410"
        and first["event_count"] == 5
        and first["pdb_ids"] == ["4V3F", "5A2D"]
        and first["ligand_component_ids"] == ["CHT"]
        and first["current_review_status"] == generic.CURRENTLY_UNREVIEWED
    ):
        _fail("NEXT_PRIORITY_REVIEW_UNIT_INVALID")
    return top


def _sets_for_algebra_v1(
    rows: Sequence[Mapping[str, str]],
) -> dict[str, set[str]]:
    return predecessor._sets_for_algebra_v1(rows)


def _build_summary_v1(
    rows: Sequence[Mapping[str, str]],
    top_pending: list[dict[str, object]],
) -> dict[str, Any]:
    summary = deepcopy(predecessor._build_summary_v1(rows, top_pending))

    def event_set(field: str, value: str) -> set[str]:
        return {row["canonical_event_id"] for row in rows if row[field] == value}

    def disposition(values: set[str]) -> dict[str, object]:
        return {"count": len(values), "event_set_sha256": _event_set_sha256(values)}

    def count_true(
        field: str, population: Sequence[Mapping[str, str]] = rows
    ) -> int:
        return sum(row[field] == "true" for row in population)

    chemistry_positive = event_set("chemistry_disposition", base.CHEMISTRY_POSITIVE)
    chemistry_negative = event_set("chemistry_disposition", base.CHEMISTRY_NEGATIVE)
    chemistry_not_established = event_set(
        "chemistry_disposition", base.CHEMISTRY_NOT_ESTABLISHED
    )
    chemistry_unresolved = event_set(
        "chemistry_disposition", base.CHEMISTRY_UNRESOLVED
    )
    task_relevant = event_set("task_relevance_disposition", base.TASK_RELEVANT)
    task_not_relevant = event_set(
        "task_relevance_disposition", base.TASK_NOT_RELEVANT
    )
    task_unresolved = event_set("task_relevance_disposition", base.TASK_UNRESOLVED)
    training_include = event_set("training_use_disposition", generic.TRAINING_INCLUDE)
    training_exclude = event_set("training_use_disposition", generic.TRAINING_EXCLUDE)
    training_not_applicable = event_set(
        "training_use_disposition", generic.TRAINING_NOT_APPLICABLE
    )
    training_unresolved = event_set(
        "training_use_disposition", base.TRAINING_UNRESOLVED
    )
    positive_rows = [
        row for row in rows if row["canonical_event_id"] in chemistry_positive
    ]
    include_rows = [
        row for row in rows if row["canonical_event_id"] in training_include
    ]
    missing_tensor_rows = [
        row
        for row in positive_rows
        if row["reactive_pair_training_target_available"] == "false"
    ]

    summary["schema_version"] = SCHEMA_VERSION
    summary["stage"] = STAGE
    summary["refresh_delta"] = {
        "frozen_predecessor_positive_count": 89,
        "neq_exact6_delta_count": 6,
        "refreshed_positive_count": len(chemistry_positive),
        "frozen_predecessor_training_include_count": 36,
        "refreshed_training_include_count": len(training_include),
        "frozen_predecessor_training_exclude_count": 53,
        "refreshed_training_exclude_count": len(training_exclude),
        "frozen_predecessor_future_candidate_count": 19,
        "refreshed_future_candidate_count": count_true(
            "future_training_admission_candidate"
        ),
        "changed_event_count": 6,
        "unchanged_event_count": 994,
        "derived_refresh_not_new_authority": True,
    }
    global_counts = Counter(row["current_global_status"] for row in rows)
    summary["global_status_distribution"]["counts"] = {
        status: global_counts[status] for status in base.GLOBAL_STATUSES_V1
    }

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
    summary["human_review"] = {
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
    }
    source_composition = dict(summary["chemistry"]["positive_source_composition"])
    source_composition["NEQ"] = sum(
        row["positive_authority_source"] == NEQ_EVENT_MATRIX_SOURCE for row in rows
    )
    summary["chemistry"] = {
        "POSITIVE": disposition(chemistry_positive),
        "NEGATIVE": disposition(chemistry_negative),
        "NOT_ESTABLISHED": disposition(chemistry_not_established),
        "UNRESOLVED": disposition(chemistry_unresolved),
        "positive_source_composition": source_composition,
        "positive_authority_collision_count": 0,
    }
    summary["task_relevance"] = {
        "RELEVANT": disposition(task_relevant),
        "NOT_RELEVANT": disposition(task_not_relevant),
        "UNRESOLVED": disposition(task_unresolved),
    }
    summary["training_use"] = {
        "INCLUDE": disposition(training_include),
        "EXCLUDE_FROM_TRAINING_ONLY": disposition(training_exclude),
        "NOT_APPLICABLE": disposition(training_not_applicable),
        "UNRESOLVED": disposition(training_unresolved),
        "total_count": len(rows),
        "excluded_positive_is_not_chemistry_negative": True,
    }
    summary["reactive_pair"].update(
        {
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
            "neq_sample_authority_contribution_count": 6,
            "neq_model_bound_target_contribution_count": 0,
            "positive_without_sample_pair_authority_count": sum(
                row["reactive_pair_sample_authoritative"] == "false"
                for row in positive_rows
            ),
        }
    )
    profile_counts = Counter(
        row["role_profile"]
        for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    )
    applicability_counts: Counter[int] = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability_counts.update(
                json.loads(row["structurally_applicable_task_ids_json"])
            )
    summary["role"].update(
        {
            "role_partition_sample_authoritative_count": count_true(
                "role_partition_sample_authoritative"
            ),
            "role_profile_counts": {
                base.STRICT_PROFILE: profile_counts[base.STRICT_PROFILE],
                base.DIRECT_PROFILE: profile_counts[base.DIRECT_PROFILE],
                "other": sum(
                    value
                    for profile, value in profile_counts.items()
                    if profile not in {base.STRICT_PROFILE, base.DIRECT_PROFILE}
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
                row["role_partition_sample_authoritative"] == "false"
                for row in rows
            ),
        }
    )
    for task in summary["canonical_exact5"]["tasks"]:
        task["structurally_applicable_authoritative_role_count"] = (
            applicability_counts[task["task_id"]]
        )
    summary["training_stage"].update(
        {
            "training_use_include_count": len(training_include),
            "future_training_admission_candidate_count": count_true(
                "future_training_admission_candidate"
            ),
            "future_candidate_source_composition": {
                **summary["training_stage"]["future_candidate_source_composition"],
                "NEQ": 0,
            },
            "current_runtime_model_usable_count": count_true(
                "current_runtime_model_usable"
            ),
            "formal_training_admitted_count": count_true(
                "formal_training_admitted"
            ),
            "ready_for_formal_training_event_count": 0,
        }
    )
    summary["blockers"] = {
        "non_exclusive_counts_must_not_be_summed": True,
        "chemistry_unresolved": {"all_1000": len(chemistry_unresolved)},
        "pair_authority_absent": {
            "all_1000": sum(
                row["reactive_pair_sample_authoritative"] == "false" for row in rows
            ),
            "within_positive_95": sum(
                row["reactive_pair_sample_authoritative"] == "false"
                for row in positive_rows
            ),
        },
        "role_authority_absent": {
            "all_1000": sum(
                row["role_partition_sample_authoritative"] == "false" for row in rows
            ),
            "within_positive_95": sum(
                row["role_partition_sample_authoritative"] == "false"
                for row in positive_rows
            ),
        },
        "human_training_exclusion": {
            "within_positive_95": sum(
                row["human_training_excluded"] == "true" for row in positive_rows
            )
        },
        "missing_split_authority": {
            "within_positive_95": sum(
                row["formal_split_authoritative"] == "false"
                for row in positive_rows
            ),
            "within_include_36": sum(
                row["formal_split_authoritative"] == "false" for row in include_rows
            ),
        },
        "missing_tensor_integration": {
            "within_positive_95": len(missing_tensor_rows),
            "within_include_36": sum(
                row["reactive_pair_training_target_available"] == "false"
                for row in include_rows
            ),
            "all_missing_are_training_excluded_population": all(
                row["training_use_disposition"] == generic.TRAINING_EXCLUDE
                for row in missing_tensor_rows
            ),
            "missing_source_composition": {
                **summary["blockers"]["missing_tensor_integration"][
                    "missing_source_composition"
                ],
                "NEQ": sum(
                    row["positive_authority_source"] == NEQ_EVENT_MATRIX_SOURCE
                    for row in missing_tensor_rows
                ),
            },
        },
        "missing_POST_training_authority": {
            "within_positive_95": sum(
                row["post_geometry_training_target_available"] == "false"
                for row in positive_rows
            ),
            "within_include_36": sum(
                row["post_geometry_training_target_available"] == "false"
                for row in include_rows
            ),
        },
        "missing_training_admission": {
            "within_positive_95": sum(
                row["formal_training_admitted"] == "false" for row in positive_rows
            ),
            "within_include_36": sum(
                row["formal_training_admitted"] == "false" for row in include_rows
            ),
        },
        "feature_semantics_pending": {"within_positive_95": len(positive_rows)},
    }
    summary["top_pending_review_units_by_event_yield"] = top_pending
    summary["authority_boundary"].update(
        {
            "next_priority_review_unit": "COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410",
            "next_priority_review_ligand": "CHT",
            "next_priority_review_event_count": 5,
        }
    )
    return summary


def _merge_semantic_bindings_v1(
    predecessor_bindings: Sequence[Mapping[str, object]],
    additive_bindings: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    return predecessor._merge_semantic_bindings_v1(
        predecessor_bindings, additive_bindings
    )


def _verify_predecessor_semantic_bindings_v1(
    bindings: Sequence[Mapping[str, object]],
) -> None:
    if len(bindings) != 74:
        _fail("PREDECESSOR_SEMANTIC_BINDING_COUNT_NOT_74")
    if (
        _sha256(_canonical_json(list(bindings)).encode("utf-8"))
        != "07063135286c4756db628a79c9b668efa150ca89c68989b2ecb7b8d427ca94b2"
    ):
        _fail("PREDECESSOR_SEMANTIC_BINDING_DIGEST_INVALID")


def compute_covapie_cumulative1000_current_global_readiness_census_with_neq_v1(
    repo_root: Path,
) -> base.Cumulative1000CurrentGlobalReadinessComputationV1:
    """Compute the exact additive NEQ refresh entirely from frozen sources."""

    root = repo_root.resolve()
    additive_bindings = _verify_additive_sources(root)
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
        root
    )
    _assert_predecessor_neq_state_v1(frozen)
    _verify_predecessor_semantic_bindings_v1(frozen.semantic_source_bindings)
    reconciliation = _validate_neq_reconciliation_v1(root)
    matrix_rows = _load_and_validate_neq_event_matrix_v1(root)
    rows = _overlay_neq_exact6_v1(frozen.rows, matrix_rows)
    top_pending = _top_pending_review_units_v1(root, reconciliation)
    summary = _build_summary_v1(rows, top_pending)
    bindings = _merge_semantic_bindings_v1(
        frozen.semantic_source_bindings, additive_bindings
    )
    computation = base.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=rows,
        summary=summary,
        semantic_source_bindings=bindings,
    )
    validate_covapie_cumulative1000_current_global_readiness_census_with_neq_v1(
        computation, predecessor_computation=frozen
    )
    return computation


def validate_covapie_cumulative1000_current_global_readiness_census_with_neq_v1(
    computation: object,
    *,
    predecessor_computation: base.Cumulative1000CurrentGlobalReadinessComputationV1
    | None = None,
) -> bool:
    """Fail closed unless refreshed rows, summary, and provenance are exact."""

    expected_type = base.Cumulative1000CurrentGlobalReadinessComputationV1
    if type(computation) is not expected_type:
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
    if type(summary) is not dict or type(bindings) is not tuple or not bindings:
        _fail("SUMMARY_OR_BINDINGS_INVALID")

    root = Path(__file__).resolve().parents[2]
    frozen = (
        predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_yun_v1(
            root
        )
        if predecessor_computation is None
        else predecessor_computation
    )
    if type(frozen) is not expected_type:
        _fail("PREDECESSOR_COMPUTATION_TYPE_INVALID")
    _assert_predecessor_neq_state_v1(frozen)
    _verify_predecessor_semantic_bindings_v1(frozen.semantic_source_bindings)

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
            raise Cumulative1000CurrentGlobalReadinessCensusWithNEQError(
                f"{ERROR_TOKEN}:CENSUS_RANK_INVALID:{event_id}"
            ) from error
    if ranks != list(range(1, 1001)):
        _fail("CENSUS_RANK_GAP_OR_ORDER_INVALID")
    frozen_by_event = {row["canonical_event_id"]: row for row in frozen.rows}
    refreshed_by_event = {row["canonical_event_id"]: row for row in rows}
    if seen != set(frozen_by_event):
        _fail("CENSUS_EVENT_SET_IDENTITY_INVALID")
    changed = {
        event_id
        for event_id in seen
        if refreshed_by_event[event_id] != frozen_by_event[event_id]
    }
    neq_set = set(NEQ_EXACT6_EVENT_IDS_V1)
    if changed != neq_set or len(changed) != 6:
        _fail("PREDECESSOR_DELTA_NOT_EXACT_NEQ_EXACT6")
    if any(
        refreshed_by_event[event_id] != frozen_by_event[event_id]
        for event_id in seen - neq_set
    ):
        _fail("NON_NEQ_ROW_CHANGED")

    expected_neq = {
        "current_global_status": generic.COMPLETED_HUMAN_POSITIVE,
        "priority_review_in_scope": "true",
        "review_unit_id": NEQ_REVIEW_UNIT_ID_V1,
        "current_review_status": generic.COMPLETED_HUMAN_POSITIVE,
        "human_review_completed": "true",
        "human_review_authority_source": NEQ_FORMAL_DECISION_SOURCE,
        "chemistry_disposition": base.CHEMISTRY_POSITIVE,
        "chemistry_authority_source": NEQ_EVENT_MATRIX_SOURCE,
        "positive_authority_source": NEQ_EVENT_MATRIX_SOURCE,
        "task_relevance_disposition": base.TASK_RELEVANT,
        "task_relevance_authority_source": NEQ_EVENT_MATRIX_SOURCE,
        "training_use_disposition": generic.TRAINING_EXCLUDE,
        "human_training_excluded": "true",
        "reactive_pair_sample_authoritative": "true",
        "reactive_pair_training_target_available": "false",
        "role_partition_sample_authoritative": "true",
        "role_profile": base.DIRECT_PROFILE,
        "canonical_mask_structural_labels_available": "true",
        "structurally_applicable_task_ids_json": NEQ_DIRECT_TASK_IDS_CELL_V1,
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
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    }
    for event_id in NEQ_EXACT6_EVENT_IDS_V1:
        before = frozen_by_event[event_id]
        after = refreshed_by_event[event_id]
        changed_fields = {
            field for field in CENSUS_COLUMNS_V1 if before[field] != after[field]
        }
        if changed_fields != _AUTHORIZED_NEQ_OVERLAY_FIELDS_V1:
            _fail("NEQ_CHANGED_FIELD_SET_INVALID:" + event_id)
        if any(
            before[field] != after[field] for field in _STRUCTURAL_IDENTITY_FIELDS_V1
        ):
            _fail("NEQ_STRUCTURAL_EVIDENCE_CHANGED:" + event_id)
        if any(after[field] != value for field, value in expected_neq.items()):
            _fail("NEQ_REFRESHED_SEMANTICS_INVALID:" + event_id)

    previous_sets = _sets_for_algebra_v1(frozen.rows)
    current_sets = _sets_for_algebra_v1(rows)
    if previous_sets["chemistry_positive"] & neq_set:
        _fail("NEQ_PREDECESSOR_POSITIVE_INTERSECTION_NOT_EMPTY")
    if not (
        current_sets["chemistry_positive"]
        == previous_sets["chemistry_positive"] | neq_set
        and current_sets["chemistry_unresolved"]
        == previous_sets["chemistry_unresolved"] - neq_set
        and current_sets["task_relevant"] == previous_sets["task_relevant"] | neq_set
        and current_sets["task_unresolved"]
        == previous_sets["task_unresolved"] - neq_set
        and current_sets["training_exclude"]
        == previous_sets["training_exclude"] | neq_set
        and current_sets["training_unresolved"]
        == previous_sets["training_unresolved"] - neq_set
        and current_sets["chemistry_negative"]
        == previous_sets["chemistry_negative"]
        and current_sets["chemistry_not_established"]
        == previous_sets["chemistry_not_established"]
        and current_sets["task_not_relevant"] == previous_sets["task_not_relevant"]
        and current_sets["training_include"] == previous_sets["training_include"]
        and current_sets["training_not_applicable"]
        == previous_sets["training_not_applicable"]
        and current_sets["future_candidate"] == previous_sets["future_candidate"]
        and current_sets["formal_split"] == previous_sets["formal_split"]
        and current_sets["formal_admitted"] == previous_sets["formal_admitted"]
        and current_sets["runtime_usable"] == previous_sets["runtime_usable"]
    ):
        _fail("NEQ_EXACT_SET_ALGEBRA_INVALID")

    if Counter(row["chemistry_disposition"] for row in rows) != Counter(
        {"POSITIVE": 95, "NOT_ESTABLISHED": 86, "UNRESOLVED": 819}
    ):
        _fail("CENSUS_CHEMISTRY_DISTRIBUTION_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter(
        {"RELEVANT": 96, "NOT_RELEVANT": 86, "UNRESOLVED": 818}
    ):
        _fail("CENSUS_TASK_DISTRIBUTION_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter(
        {
            "INCLUDE": 36,
            "EXCLUDE_FROM_TRAINING_ONLY": 59,
            "NOT_APPLICABLE": 86,
            "UNRESOLVED": 819,
        }
    ):
        _fail("CENSUS_TRAINING_DISTRIBUTION_INVALID")
    if Counter(row["current_global_status"] for row in rows) != Counter(
        _EXPECTED_GLOBAL_STATUS_COUNTS_V1
    ):
        _fail("CENSUS_EXACT11_DISTRIBUTION_INVALID")
    for field, expected in _EXPECTED_BOOLEAN_COUNTS_V1.items():
        if sum(row[field] == "true" for row in rows) != expected:
            _fail("CENSUS_BOOLEAN_COUNT_INVALID:" + field)
    if sum(row["human_training_excluded"] == "true" for row in rows) != 59:
        _fail("CENSUS_HUMAN_TRAINING_EXCLUSION_COUNT_INVALID")
    if Counter(
        row["role_profile"]
        for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    ) != Counter({base.STRICT_PROFILE: 39, base.DIRECT_PROFILE: 56}):
        _fail("CENSUS_ROLE_PROFILE_DISTRIBUTION_INVALID")

    for row in rows:
        event_id = row["canonical_event_id"]
        if row["role_partition_sample_authoritative"] == "true":
            expected_task_ids = (
                [0, 1, 2, 3, 4]
                if row["role_profile"] == base.STRICT_PROFILE
                else [0, 3, 4]
                if row["role_profile"] == base.DIRECT_PROFILE
                else None
            )
            try:
                task_ids = json.loads(row["structurally_applicable_task_ids_json"])
            except json.JSONDecodeError as error:
                raise Cumulative1000CurrentGlobalReadinessCensusWithNEQError(
                    f"{ERROR_TOKEN}:ROLE_TASK_IDS_JSON_INVALID:{event_id}"
                ) from error
            if expected_task_ids is None or task_ids != expected_task_ids or 3 not in task_ids:
                _fail("ROLE_EXACT5_APPLICABILITY_INVALID:" + event_id)
        elif (
            row["role_profile"] != base.ROLE_NOT_ESTABLISHED
            or row["canonical_mask_structural_labels_available"] != "false"
            or row["structurally_applicable_task_ids_json"] != "null"
        ):
            _fail("ROLELESS_ROW_FALSE_APPLICABILITY_NOT_UNKNOWN:" + event_id)
        if (
            row["reactive_pair_sample_authoritative"] == "true"
            and row["chemistry_disposition"] != base.CHEMISTRY_POSITIVE
        ):
            _fail("PAIR_AUTHORITY_WITHOUT_POSITIVE_CHEMISTRY:" + event_id)
        if (
            row["reactive_pair_training_target_available"] == "true"
            and row["reactive_pair_sample_authoritative"] != "true"
        ):
            _fail("PAIR_TARGET_WITHOUT_SAMPLE_AUTHORITY:" + event_id)
        if (
            row["pre_geometry_authoritative"] != "false"
            or row["pre_geometry_training_target_available"] != "false"
        ):
            _fail("POST_TO_PRE_OR_PRE_ZERO_FILL_DETECTED:" + event_id)

    reconciliation = _validate_neq_reconciliation_v1(root)
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
        role = binding["artifact_role"]
        if (
            type(path) is not str
            or not path
            or type(namespace) is not str
            or namespace not in {"repository_relative", "repository_parent_relative"}
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
            or type(role) is not str
            or not role
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
    additive_roles = [item[0] for item in _ADDITIVE_SOURCE_SPECS_V1]
    predecessor_roles = {
        item["artifact_role"] for item in frozen.semantic_source_bindings
    }
    if (
        len(set(additive_roles)) != len(additive_roles)
        or set(additive_roles) & predecessor_roles
    ):
        _fail("ADDITIVE_SEMANTIC_SOURCE_BINDING_ROLE_COLLISION")
    expected_bindings = _merge_semantic_bindings_v1(
        frozen.semantic_source_bindings, _verify_additive_sources(root)
    )
    if bindings != expected_bindings or len(bindings) != 81:
        _fail("SEMANTIC_SOURCE_BINDING_SET_NOT_EXACT_PREDECESSOR_PLUS_ADDITIVE")
    filtered_predecessor = tuple(
        binding
        for binding in bindings
        if (binding["path_namespace"], binding["path"])
        in {
            (item["path_namespace"], item["path"])
            for item in frozen.semantic_source_bindings
        }
    )
    if filtered_predecessor != frozen.semantic_source_bindings:
        _fail("PREDECESSOR_SEMANTIC_BINDING_ORDER_CHANGED")

    census_digest = _sha256(_csv_bytes(rows))
    summary_digest = _sha256(_json_bytes(summary))
    bindings_digest = _sha256(_canonical_json(list(bindings)).encode("utf-8"))
    if (
        _EXPECTED_REFRESHED_CENSUS_SHA256_V1 is not None
        and census_digest != _EXPECTED_REFRESHED_CENSUS_SHA256_V1
    ):
        _fail("REFRESHED_CENSUS_EXACT_SHA256_INVALID")
    if (
        _EXPECTED_REFRESHED_SUMMARY_SHA256_V1 is not None
        and summary_digest != _EXPECTED_REFRESHED_SUMMARY_SHA256_V1
    ):
        _fail("REFRESHED_SUMMARY_EXACT_SHA256_INVALID")
    if (
        _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1 is not None
        and bindings_digest
        != _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1
    ):
        _fail("REFRESHED_SEMANTIC_BINDINGS_EXACT_SHA256_INVALID")
    return True


def _validate_text_payload(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("OUTPUT_UTF8_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithNEQError(
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


def build_covapie_cumulative1000_current_global_readiness_artifacts_with_neq_v1(
    repo_root: Path,
) -> dict[str, bytes]:
    """Build the deterministic Exact3 outputs without repository writes."""

    if None in (
        _EXPECTED_REFRESHED_CENSUS_SHA256_V1,
        _EXPECTED_REFRESHED_SUMMARY_SHA256_V1,
        _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1,
    ):
        _fail("DERIVED_PROJECTION_DIGESTS_NOT_FROZEN")
    root = repo_root.resolve()
    computation = compute_covapie_cumulative1000_current_global_readiness_census_with_neq_v1(
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
            "source_derived": True,
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
        raise Cumulative1000CurrentGlobalReadinessCensusWithNEQError(
            f"{ERROR_TOKEN}:OUTPUT_WRITE_FAILED:{path.name}"
        ) from error


def materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_neq_v1(
    repo_root: Path,
    output_directory: Path | None = None,
) -> dict[str, bytes]:
    """Write only Exact3 after complete source and semantic validation."""

    root = repo_root.resolve()
    output = (
        root / OUTPUT_DIRECTORY_RELATIVE
        if output_directory is None
        else output_directory.resolve()
    )
    try:
        output.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithNEQError(
            f"{ERROR_TOKEN}:OUTPUT_DIRECTORY_CREATE_FAILED"
        ) from error
    artifacts = build_covapie_cumulative1000_current_global_readiness_artifacts_with_neq_v1(
        root
    )
    existing = {path.name for path in output.iterdir() if path.is_file()}
    unexpected = existing - set(artifacts)
    if unexpected:
        _fail("OUTPUT_DIRECTORY_UNEXPECTED_FILE:" + sorted(unexpected)[0])
    for filename in (CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE):
        _atomic_write(output / filename, artifacts[filename])
    return artifacts
