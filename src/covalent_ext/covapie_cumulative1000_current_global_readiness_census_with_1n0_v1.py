"""Additive cumulative1000 readiness census refresh for published 1N0 Exact4.

This successor consumes the frozen with-I12 census plus already-published 1N0
ingestion and reconciliation authority. It deep-copies the predecessor rows
and overlays only 1N0 Exact4. It creates no human, chemistry, pair, role,
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
import stat
import tempfile
from typing import Any, NoReturn

from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import covapie_completed_human_decision_reconciliation_with_1n0_v1 as one_n0_reconciliation
from . import covapie_cumulative1000_current_global_readiness_census_with_i12_v1 as predecessor
from . import covapie_1n0_completed_decision_ingestion_and_task_label_availability_v1 as one_n0_ingestion
from .covapie_source_binding_policy_v2 import (
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


__all__ = (
    "Cumulative1000CurrentGlobalReadinessCensusWith1N0Error",
    "compute_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1",
    "validate_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1",
    "build_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1",
    "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1",
)


SCHEMA_VERSION = "covapie_cumulative1000_current_global_readiness_census_with_1n0_v1"
STAGE = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_1N0_V1"
ERROR_TOKEN = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_1N0_V1_ERROR"

OUTPUT_DIRECTORY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_1n0_v1"
)
CENSUS_FILE = "covapie_cumulative1000_current_global_readiness_census_with_1n0_v1.csv"
SUMMARY_FILE = "covapie_cumulative1000_current_global_readiness_summary_with_1n0_v1.json"
MANIFEST_FILE = "covapie_cumulative1000_current_global_readiness_manifest_with_1n0_v1.json"

PRODUCTION_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_with_1n0_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1.py"
)
GUIDE_RELATIVE = Path(
    "docs/covapie_cumulative1000_current_global_readiness_census_with_1n0_v1_guide.md"
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
ONE_N0_EXACT4_EVENT_IDS_V1 = one_n0_ingestion.EXPECTED_EVENT_IDS
ONE_N0_EXACT4_RANKS_V1 = one_n0_ingestion.EXPECTED_RANKS
ONE_N0_REVIEW_UNIT_ID_V1 = one_n0_ingestion.EXPECTED_REVIEW_UNIT_ID
ONE_N0_EXCLUDED_RANKS_V1 = one_n0_ingestion.EXCLUDED_C2_RANKS
ONE_N0_EXCLUDED_REVIEW_UNIT_ID_V1 = "COVAPIE_BULK_REVIEW_UNIT_D60E67E860A87B24"

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
ONE_N0_RECONCILIATION_OWNER_RELATIVE = Path(
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_1n0_v1.py"
)
ONE_N0_INGESTION_OWNER_RELATIVE = one_n0_ingestion.SOURCE_RELATIVE
ONE_N0_EVENT_MATRIX_RELATIVE = one_n0_ingestion.OUTPUT_ROOT_RELATIVE / one_n0_ingestion.MATRIX
PRIORITY_QUEUE_RELATIVE = predecessor.PRIORITY_QUEUE_RELATIVE

ONE_N0_EVENT_MATRIX_SOURCE = ONE_N0_EVENT_MATRIX_RELATIVE.as_posix()
# The ingestion owner exposes and validates this provenance.  This successor
# records the relative provenance value but never reads or binds the formal file.
ONE_N0_HUMAN_DECISION_SOURCE = one_n0_ingestion.FORMAL_DECISION_RELATIVE.as_posix()

_EXPECTED_GLOBAL_STATUS_COUNTS_V1 = {
    generic.CURRENTLY_UNREVIEWED: 211,
    generic.CURRENTLY_IN_PROGRESS: 0,
    generic.COMPLETED_HUMAN_POSITIVE: 99,
    generic.COMPLETED_HUMAN_NEGATIVE: 58,
    generic.COMPLETED_PARTIAL_AUTHORITY: 1,
    generic.CURRENT_RUNTIME_MODEL_USABLE: 17,
    generic.PUBLISHED_EXACT_AUTO_NEGATIVE: 32,
    "LEAKAGE_EXISTING_GROUP_CONFLICT": 369,
    "STRUCTURAL_EVIDENCE_INCOMPLETE": 133,
    "QUARANTINE_REPRESENTATION_GAP": 78,
    "REJECTED_FEATURE_INCOMPATIBLE": 2,
}
_EXPECTED_BOOLEAN_COUNTS_V1 = dict(predecessor._EXPECTED_BOOLEAN_COUNTS_V1)

# Frozen only after the first fully source-derived build and semantic validation.
# These derived projection contract digests are never human/science authority.
_EXPECTED_REFRESHED_CENSUS_SHA256_V1: str | None = (
    "ac63ced99e77212e5952b41169369c5e5c77967f9409e2e1fec25f99808eaf35"
)
_EXPECTED_REFRESHED_SUMMARY_SHA256_V1: str | None = (
    "516ab4c1ed9196c2233695566be9976d8f9f8dc5b13bb88b364b15eee8d08459"
)
_EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1: str | None = (
    "b80ce311d66a6ef163921d67c4dde947f24e95f2aff9a5ceee0aec67ff9b8a46"
)

_SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_STRUCTURAL_IDENTITY_FIELDS_V1 = predecessor._STRUCTURAL_IDENTITY_FIELDS_V1
_AUTHORIZED_1N0_OVERLAY_FIELDS_V1 = frozenset(
    {
        "chemistry_authority_source",
        "chemistry_disposition",
        "current_global_status",
        "current_review_status",
        "human_review_authority_source",
        "human_review_completed",
        "task_relevance_authority_source",
        "task_relevance_disposition",
        "training_use_disposition",
    }
)
_EXPECTED_ONE_N0_STRUCTURAL_CELLS_V1 = {
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
        "PREDECESSOR_I12_CENSUS_OWNER",
        PREDECESSOR_OWNER_RELATIVE,
        "repository_relative",
        71565,
        "42b01060024cf4c92e19bf3804c6440522019082ab6ec5fda89f5b7258e243b4",
        False,
    ),
    (
        "PREDECESSOR_I12_MATERIALIZED_CENSUS",
        PREDECESSOR_CENSUS_RELATIVE,
        "repository_relative",
        532022,
        "f659b6c9d9475c94aa4bf2234053627d28a58d4b7f6ae424f49a18924c1ac3bf",
        False,
    ),
    (
        "PREDECESSOR_I12_MATERIALIZED_SUMMARY",
        PREDECESSOR_SUMMARY_RELATIVE,
        "repository_relative",
        17549,
        "76d91f101898d8ba6c46de69be866e1408cbb9e630562906a52435a18e31d6b1",
        False,
    ),
    (
        "ONE_N0_RECONCILIATION_OWNER",
        ONE_N0_RECONCILIATION_OWNER_RELATIVE,
        "repository_relative",
        24762,
        "86e722b46a1ad4c25c0c3c9c8de2f48461ff7153e2b6bbd7c901dfcd338e5af8",
        False,
    ),
    (
        "ONE_N0_INGESTION_OWNER",
        ONE_N0_INGESTION_OWNER_RELATIVE,
        "repository_relative",
        79080,
        "ce201de459400cd024c67428a39fb83dc665a3dfad0a73fb0f1cc12458db1bbd",
        False,
    ),
    (
        "ONE_N0_EVENT_TASK_LABEL_AVAILABILITY",
        ONE_N0_EVENT_MATRIX_RELATIVE,
        "repository_relative",
        7953,
        "75349801404461111e9d37658fa899ecfb7148ce760ce28d43e82a76f3347361",
        False,
    ),
)
_PREDECESSOR_MANIFEST_SPEC_V1 = (
    51041,
    "d22c388f7da5fecede11df15e3bc188196328e24009ad9363932bebc971da150",
    False,
)


class Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(ValueError):
    """Raised unless the additive ONE_N0 refresh is exactly source-derived."""


def _fail(reason: str) -> NoReturn:
    raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
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
        raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
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
    for (
        role,
        relative,
        namespace,
        byte_count,
        sha256,
        expected_executable,
    ) in _ADDITIVE_SOURCE_SPECS_V1:
        try:
            verify_bound_source_v2(
                path=_resolve_source(root, namespace, relative),
                expected_byte_count=byte_count,
                expected_sha256=sha256,
                label=role + ":" + relative.as_posix(),
                expected_executable=expected_executable,
            )
        except SourceBindingPolicyV2Error as error:
            raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
                f"{ERROR_TOKEN}:BOUND_SOURCE_REJECTED:{role}"
            ) from error
        bindings.append(
            {
                "artifact_role": role,
                "path": relative.as_posix(),
                "path_namespace": namespace,
                "byte_count": byte_count,
                "sha256": sha256,
                "expected_executable": expected_executable,
            }
        )
    try:
        verify_bound_source_v2(
            path=root / PREDECESSOR_MANIFEST_RELATIVE,
            expected_byte_count=_PREDECESSOR_MANIFEST_SPEC_V1[0],
            expected_sha256=_PREDECESSOR_MANIFEST_SPEC_V1[1],
            label="PREDECESSOR_I12_MANIFEST:" + PREDECESSOR_MANIFEST_RELATIVE.as_posix(),
            expected_executable=_PREDECESSOR_MANIFEST_SPEC_V1[2],
        )
    except SourceBindingPolicyV2Error as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
            f"{ERROR_TOKEN}:PREDECESSOR_I12_MANIFEST_BINDING_INVALID"
        ) from error
    return tuple(bindings)


def _validate_one_n0_matrix_rows_v1(
    rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    normalized = tuple(dict(row) for row in rows)
    if (
        len(normalized) != 4
        or any(tuple(row) != one_n0_ingestion.MATRIX_HEADER for row in normalized)
        or tuple(row["canonical_event_id"] for row in normalized)
        != ONE_N0_EXACT4_EVENT_IDS_V1
        or tuple(int(row["scaleup_rank"]) for row in normalized)
        != ONE_N0_EXACT4_RANKS_V1
        or len({row["canonical_event_id"] for row in normalized}) != 4
    ):
        _fail("ONE_N0_EVENT_MATRIX_IDENTITY_NOT_EXACT4")
    if Counter(row["pdb_id"] for row in normalized) != Counter(
        {"4JWS": 2, "4JWU": 1, "4JX1": 1}
    ):
        _fail("ONE_N0_EVENT_MATRIX_PDB_IDENTITY_INVALID")
    if {row["cys_residue_id"] for row in normalized} != {
        "CYS:73-",
        "CYS:19-",
    }:
        _fail("ONE_N0_EVENT_MATRIX_CYS_IDENTITY_INVALID")
    if tuple(
        (row["protein_chain_or_asym"], row["ligand_chain_or_asym"])
        for row in normalized
    ) != (("C", "G"), ("D", "J"), ("C", "G"), ("G", "U")):
        _fail("ONE_N0_EVENT_MATRIX_CONTEXTS_COLLAPSED_OR_DRIFTED")
    expected_cells = {
        "ligand_component_id": "1N0",
        "observed_protein_reactive_atom": "SG",
        "observed_ligand_reactive_atom": "C16",
        "explicit_covalent_evidence": "true",
        "raw_structural_reactive_pair_evidence": "true",
        "second_endpoint_present": "true",
        "second_endpoint_ligand_atom": "C2",
        "second_endpoint_is_target_event": "false",
        "human_task_relevance_decision": generic.TASK_NOT_RELEVANT,
        "task_relevance_human_authoritative": "true",
        "task_domain_negative": "true",
        "D2_human_choice": "UNRESOLVED",
        "D3_human_choice": "UNRESOLVED",
        "D4_human_choice": "UNRESOLVED",
        "D5_human_choice": "UNRESOLVED",
        "chemistry_human_authoritative": "false",
        "reactive_pair_human_decision_available": "false",
        "reactive_pair_human_authoritative": "false",
        "role_partition_human_decision_available": "false",
        "role_partition_human_authoritative": "false",
        "training_use_human_decision_available": "false",
        "training_only_exclusion_human_authoritative": "false",
        "legacy_completed_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
        "task_relevance_disposition": generic.TASK_NOT_RELEVANT,
        "chemistry_disposition": generic.CHEMISTRY_NOT_ESTABLISHED,
        "training_disposition": generic.TRAINING_NOT_APPLICABLE,
        "human_training_excluded": "false",
        "selected_role_candidate_index_0based": "null",
        "role_profile": "null",
        "warhead_atoms_json": "null",
        "linker_atoms_json": "null",
        "scaffold_atoms_json": "null",
        "boundary_bonds_json": "null",
        "sample_authoritative_applicable_task_ids_json": "null",
        "global_canonical_task_count": "5",
        "B3_present": "true",
        "sixth_task_present": "false",
        "chemistry_known_positive": "false",
        "negative_chemistry": "false",
        "sample_level_chemistry_positive_authority": "false",
        "sample_level_chemistry_negative_authority": "false",
        "chemical_warhead_human_authoritative": "false",
        "chemical_warhead_atoms_json": "null",
        "reaction_family_authority": "false",
        "warhead_family_authority": "false",
        "warhead_rule_authority": "false",
        "warhead_type_authority": "false",
        "reusable_chemistry_authority": "false",
        "POST_source_evidence_available": "true",
        "POST_sample_authority": "false",
        "POST_geometry_training_authority_available": "false",
        "POST_geometry_training_target_available_now": "false",
        "PRE_status": one_n0_ingestion.PRE_STATUS,
        "PRE_source_graph_mapping_count": "0",
        "PRE_topology_authority_available": "false",
        "PRE_geometry_authority_available": "false",
        "PRE_reconstruction_performed": "false",
        "PRE_mapping_repair_performed": "false",
        "POST_to_PRE_copy_performed": "false",
        "PRE_zero_fill_performed": "false",
        "training_use_allowed": "false",
        "training_use_include": "false",
        "candidate_for_future_training_admission": "false",
        "future_training_admission_candidate": "false",
        "training_admitted": "false",
        "training_admission_created": "false",
        "training_materialization_allowed_now": "false",
        "formal_split_authority_created": "false",
        "tensor_target_created": "false",
        "current_runtime_model_usable": "false",
        "parameter_update_authorization": "false",
        "ready_for_training": "false",
        "authority_source": one_n0_ingestion.AUTHORITY_SOURCE,
        "authority_scope": one_n0_ingestion.AUTHORITY_SCOPE,
        "authority_ingested": "true",
        "authority_created_by_this_ingestion": "false",
    }
    for row in normalized:
        event_id = row["canonical_event_id"]
        if any(row[key] != value for key, value in expected_cells.items()):
            _fail("ONE_N0_EVENT_MATRIX_SEMANTICS_INVALID:" + event_id)
        try:
            availability = json.loads(
                row["canonical_task_authority_availability_json"]
            )
        except json.JSONDecodeError as error:
            raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
                f"{ERROR_TOKEN}:ONE_N0_EXACT5_JSON_INVALID:{event_id}"
            ) from error
        if (
            len(availability) != 5
            or [item["task_id"] for item in availability] != list(range(5))
            or [item["semantic_long_name"] for item in availability]
            != [task[1] for task in one_n0_ingestion.CANONICAL_TASKS]
            or [item["display_alias"] for item in availability]
            != [task[2] for task in one_n0_ingestion.CANONICAL_TASKS]
            or any(
                item["authoritative_label_available"] is not False
                for item in availability
            )
            or availability[3]["semantic_long_name"] != "scaffold_only"
        ):
            _fail("ONE_N0_EVENT_MATRIX_EXACT5_INVALID:" + event_id)
    return normalized


def _load_and_validate_one_n0_event_matrix_v1(
    root: Path,
) -> tuple[dict[str, str], ...]:
    payload = _read_regular_file(root / ONE_N0_EVENT_MATRIX_RELATIVE, "ONE_N0_EVENT_MATRIX")
    if len(payload) != 7953 or _sha256(payload) != _ADDITIVE_SOURCE_SPECS_V1[5][4]:
        _fail("ONE_N0_EVENT_MATRIX_BINDING_INVALID")
    source_derived = one_n0_ingestion.build_artifacts_v1(root)
    if source_derived[one_n0_ingestion.MATRIX] != payload:
        _fail("ONE_N0_EVENT_MATRIX_NOT_SOURCE_DERIVED")
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
            f"{ERROR_TOKEN}:ONE_N0_EVENT_MATRIX_NOT_UTF8"
        ) from error
    if tuple(reader.fieldnames or ()) != one_n0_ingestion.MATRIX_HEADER:
        _fail("ONE_N0_EVENT_MATRIX_HEADER_INVALID")
    return _validate_one_n0_matrix_rows_v1(tuple(dict(row) for row in reader))


def _validate_one_n0_reconciliation_v1(root: Path) -> generic.ReconciliationResult:
    result = one_n0_reconciliation.reconcile_real_completed_human_decisions_with_1n0_v1(
        root
    )
    if result.review_summary != {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 99,
        "completed_positive_unit_count": 14,
        "completed_negative_event_count": 28,
        "completed_negative_unit_count": 5,
        "completed_total_event_count": 127,
        "completed_total_unit_count": 19,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 211,
        "unreviewed_unit_count": 112,
    }:
        _fail("ONE_N0_RECONCILIATION_SUMMARY_INVALID")
    if len(result.normalized_facts) != 103 or Counter(
        fact.training_disposition for fact in result.normalized_facts
    ) != Counter(
        {
            generic.TRAINING_INCLUDE: 31,
            generic.TRAINING_EXCLUDE: 68,
            generic.TRAINING_NOT_APPLICABLE: 4,
        }
    ):
        _fail("ONE_N0_RECONCILIATION_NORMALIZED_FACTS_INVALID")
    rows = [
        row
        for row in result.reconciled_rows
        if row["raw_review_unit_id"] == ONE_N0_REVIEW_UNIT_ID_V1
    ]
    if (
        len(rows) != 4
        or {row["canonical_event_id"] for row in rows}
        != set(ONE_N0_EXACT4_EVENT_IDS_V1)
        or any(
            row["current_review_status"] != generic.COMPLETED_HUMAN_NEGATIVE
            for row in rows
        )
    ):
        _fail("ONE_N0_RECONCILIATION_EXACT4_INVALID")
    facts = [
        fact
        for fact in result.normalized_facts
        if fact.canonical_event_id in set(ONE_N0_EXACT4_EVENT_IDS_V1)
    ]
    if len(facts) != 4 or any(
        fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_NOT_ESTABLISHED
        or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
        or fact.human_training_excluded is not False
        for fact in facts
    ):
        _fail("ONE_N0_RECONCILIATION_EXACT4_SEMANTICS_INVALID")
    return result


def _assert_predecessor_one_n0_state_v1(
    computation: base.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    one_n0_set = set(ONE_N0_EXACT4_EVENT_IDS_V1)
    rows = [
        row for row in computation.rows if row["canonical_event_id"] in one_n0_set
    ]
    if len(rows) != 4 or tuple(
        int(row["scaleup_rank"]) for row in rows
    ) != ONE_N0_EXACT4_RANKS_V1:
        _fail("PREDECESSOR_ONE_N0_EXACT4_IDENTITY_INVALID")
    expected = {
        "current_global_status": generic.CURRENTLY_UNREVIEWED,
        "priority_review_in_scope": "true",
        "review_unit_id": ONE_N0_REVIEW_UNIT_ID_V1,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "human_review_completed": "false",
        "human_review_authority_source": PRIORITY_QUEUE_RELATIVE.as_posix(),
        "chemistry_disposition": base.CHEMISTRY_UNRESOLVED,
        "chemistry_authority_source": "",
        "task_relevance_disposition": base.TASK_UNRESOLVED,
        "task_relevance_authority_source": "",
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
        "formal_split": "",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "training_materialization_allowed_current_source": "",
        "positive_authority_source": "",
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    }
    if any(any(row[key] != value for key, value in expected.items()) for row in rows):
        _fail("PREDECESSOR_ONE_N0_STATE_INVALID")
    if any(
        any(
            row[field] != value
            for field, value in _EXPECTED_ONE_N0_STRUCTURAL_CELLS_V1.items()
        )
        for row in rows
    ):
        _fail("PREDECESSOR_ONE_N0_STRUCTURAL_COVERAGE_INVALID")
    excluded = [
        row
        for row in computation.rows
        if int(row["scaleup_rank"]) in ONE_N0_EXCLUDED_RANKS_V1
    ]
    excluded_expected = {
        "ligand_component_id": "1N0",
        "review_unit_id": ONE_N0_EXCLUDED_REVIEW_UNIT_ID_V1,
        "current_global_status": generic.CURRENTLY_UNREVIEWED,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "human_review_completed": "false",
        "chemistry_disposition": base.CHEMISTRY_UNRESOLVED,
        "task_relevance_disposition": base.TASK_UNRESOLVED,
        "training_use_disposition": base.TRAINING_UNRESOLVED,
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "canonical_mask_structural_labels_available": "false",
    }
    if (
        len(excluded) != 2
        or tuple(int(row["scaleup_rank"]) for row in excluded)
        != ONE_N0_EXCLUDED_RANKS_V1
        or any(
            any(row[field] != value for field, value in excluded_expected.items())
            for row in excluded
        )
    ):
        _fail("PREDECESSOR_ONE_N0_EXCLUDED_C2_CONTROLS_INVALID")
    chemistry = Counter(row["chemistry_disposition"] for row in computation.rows)
    relevance = Counter(
        row["task_relevance_disposition"] for row in computation.rows
    )
    training = Counter(row["training_use_disposition"] for row in computation.rows)
    if chemistry[base.CHEMISTRY_POSITIVE] != 116:
        _fail("PREDECESSOR_POSITIVE_COUNT_NOT_116")
    if relevance[base.TASK_RELEVANT] != 117:
        _fail("PREDECESSOR_TASK_RELEVANT_COUNT_NOT_117")
    if training[generic.TRAINING_INCLUDE] != 48:
        _fail("PREDECESSOR_TRAINING_INCLUDE_COUNT_NOT_48")
    if training[generic.TRAINING_EXCLUDE] != 68:
        _fail("PREDECESSOR_TRAINING_EXCLUDE_COUNT_NOT_68")
    if sum(
        row["future_training_admission_candidate"] == "true"
        for row in computation.rows
    ) != 31:
        _fail("PREDECESSOR_FUTURE_CANDIDATE_COUNT_NOT_31")


def _overlay_one_n0_exact4_v1(
    predecessor_rows: Sequence[Mapping[str, str]],
    matrix_rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    validated_matrix = _validate_one_n0_matrix_rows_v1(matrix_rows)
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
            or row["ligand_component_id"] != "1N0"
            or row["review_unit_id"] != ONE_N0_REVIEW_UNIT_ID_V1
        ):
            _fail("ONE_N0_MATRIX_PREDECESSOR_IDENTITY_MISMATCH:" + event_id)
        row.update(
            {
                "current_global_status": generic.COMPLETED_HUMAN_NEGATIVE,
                "current_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
                "human_review_completed": "true",
                "human_review_authority_source": ONE_N0_HUMAN_DECISION_SOURCE,
                "chemistry_disposition": base.CHEMISTRY_NOT_ESTABLISHED,
                "chemistry_authority_source": ONE_N0_EVENT_MATRIX_SOURCE,
                "task_relevance_disposition": base.TASK_NOT_RELEVANT,
                "task_relevance_authority_source": ONE_N0_EVENT_MATRIX_SOURCE,
                "training_use_disposition": generic.TRAINING_NOT_APPLICABLE,
            }
        )
    return tuple(rows)


def _top_pending_review_units_v1(
    root: Path,
    reconciliation: generic.ReconciliationResult,
) -> list[dict[str, object]]:
    try:
        payload = verify_bound_source_v2(
            path=root / PRIORITY_QUEUE_RELATIVE,
            expected_byte_count=50116,
            expected_sha256=(
                "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"
            ),
            label="FROZEN_PRIORITY_QUEUE:" + PRIORITY_QUEUE_RELATIVE.as_posix(),
            expected_executable=False,
        )
    except SourceBindingPolicyV2Error as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
            f"{ERROR_TOKEN}:PRIORITY_QUEUE_BINDING_INVALID"
        ) from error
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
    if len(candidates) != 112:
        _fail("CURRENT_PENDING_REVIEW_UNIT_COUNT_INVALID")
    if not any(
        unit == ONE_N0_EXCLUDED_REVIEW_UNIT_ID_V1
        and status == generic.CURRENTLY_UNREVIEWED
        and json.loads(row["ligand_component_ids_json"]) == ["1N0"]
        and int(row["event_count"]) == 2
        for _negative, _priority, unit, row, status in candidates
    ):
        _fail("ONE_N0_EXCLUDED_C2_REVIEW_UNIT_NOT_PENDING")
    top: list[dict[str, object]] = []
    for rank, (_negative, _priority, unit, row, status) in enumerate(
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
                "post_source_evidence_count": int(
                    row["POST_geometry_available_event_count"]
                ),
                "current_review_status": status,
            }
        )
    first = top[0]
    if not (
        first["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_946339D19F961B4A"
        and first["raw_priority_rank"] == 19
        and first["event_count"] == 4
        and first["ligand_component_ids"] == ["CER"]
        and first["pdb_ids"] == ["1FJ8"]
        and first["full_coordinate_count"] == 4
        and first["exact_pair_count"] == 4
        and first["ccd_complete_count"] == 4
        and first["post_source_evidence_count"] == 4
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
    """Derive the 1N0 negative refresh summary without inventing authority."""

    summary = deepcopy(predecessor._build_summary_v1(rows, top_pending))
    global_counts = Counter(row["current_global_status"] for row in rows)
    chemistry_counts = Counter(row["chemistry_disposition"] for row in rows)
    task_counts = Counter(row["task_relevance_disposition"] for row in rows)
    training_counts = Counter(row["training_use_disposition"] for row in rows)

    summary["schema_version"] = SCHEMA_VERSION
    summary["stage"] = STAGE
    summary["refresh_delta"] = {
        "predecessor_currently_unreviewed_count": 215,
        "refreshed_currently_unreviewed_count": global_counts[
            generic.CURRENTLY_UNREVIEWED
        ],
        "predecessor_completed_human_negative_global_count": 54,
        "refreshed_completed_human_negative_global_count": global_counts[
            generic.COMPLETED_HUMAN_NEGATIVE
        ],
        "predecessor_chemistry_not_established_count": 86,
        "refreshed_chemistry_not_established_count": chemistry_counts[
            base.CHEMISTRY_NOT_ESTABLISHED
        ],
        "predecessor_task_not_relevant_count": 86,
        "refreshed_task_not_relevant_count": task_counts[base.TASK_NOT_RELEVANT],
        "predecessor_training_not_applicable_count": 86,
        "refreshed_training_not_applicable_count": training_counts[
            generic.TRAINING_NOT_APPLICABLE
        ],
        "one_n0_exact4_delta_count": 4,
        "changed_event_count": 4,
        "unchanged_event_count": 996,
        "derived_refresh_not_new_authority": True,
    }
    summary["global_status_distribution"]["counts"] = {
        status: global_counts[status] for status in base.GLOBAL_STATUSES_V1
    }

    priority_rows = [
        row for row in rows if row["priority_review_in_scope"] == "true"
    ]
    review_counts = Counter(row["current_review_status"] for row in priority_rows)
    review_units_by_status: dict[str, set[str]] = defaultdict(set)
    for row in priority_rows:
        review_units_by_status[row["current_review_status"]].add(
            row["review_unit_id"]
        )
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
    summary["top_pending_review_units_by_event_yield"] = top_pending
    summary["authority_boundary"].update(
        {
            "next_priority_review_unit": (
                "COVAPIE_BULK_REVIEW_UNIT_946339D19F961B4A"
            ),
            "next_priority_review_ligand": "CER",
            "next_priority_review_event_count": 4,
            "next_priority_review_current_pending_rank": 1,
            "next_priority_review_raw_priority_rank": 19,
            "next_review_started": False,
            "1N0_REVIEW_COMPLETED": True,
            "READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION": False,
            "new_exact_posix_source_mode_authority_introduced": False,
            "new_ambiguous_source_mode_authority_introduced": False,
            "ONE_N0_CENSUS_SOURCE_BINDING_V2_CLEAN_FROM_BIRTH": True,
            "separate_ONE_N0_census_V2_successor_required": False,
            "QUEUE_REFRESH": False,
            "READY_FOR_TRAINING": False,
            "READY_FOR_FORMAL_TRAINING": False,
            "training_started": False,
            "training_materialization_allowed": False,
            "parameter_update_authorization": False,
            "future_candidate_is_not_training_admission": True,
            "minimal_seed_authority_created": False,
            "post_geometry_training_authority_created": False,
            "pre_geometry_authority_created": False,
            "feature_semantics_audit_performed": False,
            "feature_semantics_status": "AUDIT_REQUIRED_LATER",
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
            "Step12D": (
                "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT"
            ),
        }
    )
    summary["authority_boundary"].pop(
        "FILESYSTEM_MODE_AUTHORITY_TECH_DEBT", None
    )
    summary["authority_boundary"].pop("NEXT_RECOMMENDED_MAINLINE", None)
    summary["authority_boundary"].pop("I12_REVIEW_COMPLETED", None)
    summary["authority_boundary"].pop(
        "I12_CENSUS_SOURCE_BINDING_V2_CLEAN_FROM_BIRTH", None
    )
    summary["authority_boundary"].pop(
        "separate_I12_census_V2_successor_required", None
    )
    return summary

def _merge_semantic_bindings_v1(
    predecessor_bindings: Sequence[Mapping[str, object]],
    additive_bindings: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    frozen = tuple(dict(item) for item in predecessor_bindings)
    additive = tuple(dict(item) for item in additive_bindings)
    identities = [
        (item["path_namespace"], item["path"])
        for item in (*frozen, *additive)
    ]
    if len(identities) != len(set(identities)):
        _fail("SEMANTIC_SOURCE_BINDING_DUPLICATE_DURING_APPEND")
    frozen_roles = {item["artifact_role"] for item in frozen}
    additive_roles = [item["artifact_role"] for item in additive]
    if (
        len(additive_roles) != len(set(additive_roles))
        or frozen_roles & set(additive_roles)
    ):
        _fail("SEMANTIC_SOURCE_BINDING_ROLE_DUPLICATE_DURING_APPEND")
    return (*frozen, *additive)


def _verify_predecessor_semantic_bindings_v1(
    bindings: Sequence[Mapping[str, object]],
) -> None:
    if len(bindings) != 114:
        _fail("PREDECESSOR_SEMANTIC_BINDING_COUNT_NOT_114")
    if (
        _sha256(_canonical_json(list(bindings)).encode("utf-8"))
        != "b5debd291eab69bfe5fdb6d0af719f377b8584eb459eb1c01742da57cec9f551"
    ):
        _fail("PREDECESSOR_SEMANTIC_BINDING_DIGEST_INVALID")


def compute_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1(
    repo_root: Path,
) -> base.Cumulative1000CurrentGlobalReadinessComputationV1:
    """Compute the exact additive 1N0 refresh entirely from frozen sources."""

    root = repo_root.resolve()
    additive_bindings = _verify_additive_sources(root)
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_i12_v1(
        root
    )
    _assert_predecessor_one_n0_state_v1(frozen)
    _verify_predecessor_semantic_bindings_v1(frozen.semantic_source_bindings)
    reconciliation = _validate_one_n0_reconciliation_v1(root)
    matrix_rows = _load_and_validate_one_n0_event_matrix_v1(root)
    rows = _overlay_one_n0_exact4_v1(frozen.rows, matrix_rows)
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
    validate_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1(
        computation, predecessor_computation=frozen
    )
    return computation


def validate_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1(
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
        predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_i12_v1(
            root
        )
        if predecessor_computation is None
        else predecessor_computation
    )
    if type(frozen) is not expected_type:
        _fail("PREDECESSOR_COMPUTATION_TYPE_INVALID")
    _assert_predecessor_one_n0_state_v1(frozen)
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
            raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
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
    one_n0_set = set(ONE_N0_EXACT4_EVENT_IDS_V1)
    if changed != one_n0_set or len(changed) != 4:
        _fail("PREDECESSOR_DELTA_NOT_EXACT_ONE_N0_EXACT4")
    if any(
        refreshed_by_event[event_id] != frozen_by_event[event_id]
        for event_id in seen - one_n0_set
    ):
        _fail("NON_ONE_N0_ROW_CHANGED")

    expected_one_n0 = {
        "current_global_status": generic.COMPLETED_HUMAN_NEGATIVE,
        "priority_review_in_scope": "true",
        "review_unit_id": ONE_N0_REVIEW_UNIT_ID_V1,
        "current_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
        "human_review_completed": "true",
        "human_review_authority_source": ONE_N0_HUMAN_DECISION_SOURCE,
        "chemistry_disposition": base.CHEMISTRY_NOT_ESTABLISHED,
        "chemistry_authority_source": ONE_N0_EVENT_MATRIX_SOURCE,
        "positive_authority_source": "",
        "task_relevance_disposition": base.TASK_NOT_RELEVANT,
        "task_relevance_authority_source": ONE_N0_EVENT_MATRIX_SOURCE,
        "training_use_disposition": generic.TRAINING_NOT_APPLICABLE,
        "human_training_excluded": "false",
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
        "formal_split": "",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "training_materialization_allowed_current_source": "",
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    }
    if (
        base.CHEMISTRY_NOT_ESTABLISHED == generic.CHEMISTRY_NEGATIVE
        or generic.CHEMISTRY_NOT_ESTABLISHED == generic.CHEMISTRY_NEGATIVE
    ):
        _fail("CHEMISTRY_NOT_ESTABLISHED_COLLAPSED_TO_NEGATIVE")
    for event_id in ONE_N0_EXACT4_EVENT_IDS_V1:
        before = frozen_by_event[event_id]
        after = refreshed_by_event[event_id]
        changed_fields = {
            field for field in CENSUS_COLUMNS_V1 if before[field] != after[field]
        }
        if changed_fields != _AUTHORIZED_1N0_OVERLAY_FIELDS_V1:
            _fail("ONE_N0_CHANGED_FIELD_SET_INVALID:" + event_id)
        if any(
            before[field] != after[field] for field in _STRUCTURAL_IDENTITY_FIELDS_V1
        ):
            _fail("ONE_N0_STRUCTURAL_EVIDENCE_CHANGED:" + event_id)
        if any(after[field] != value for field, value in expected_one_n0.items()):
            _fail("ONE_N0_REFRESHED_SEMANTICS_INVALID:" + event_id)

    for rank in ONE_N0_EXCLUDED_RANKS_V1:
        event_id = next(
            row["canonical_event_id"]
            for row in frozen.rows
            if int(row["scaleup_rank"]) == rank
        )
        if refreshed_by_event[event_id] != frozen_by_event[event_id]:
            _fail("ONE_N0_EXCLUDED_C2_NEGATIVE_CONTROL_CHANGED:" + str(rank))

    previous_sets = _sets_for_algebra_v1(frozen.rows)
    current_sets = _sets_for_algebra_v1(rows)
    if not (
        current_sets["chemistry_positive"]
        == previous_sets["chemistry_positive"]
        and current_sets["chemistry_unresolved"]
        == previous_sets["chemistry_unresolved"] - one_n0_set
        and current_sets["chemistry_not_established"]
        == previous_sets["chemistry_not_established"] | one_n0_set
        and current_sets["task_relevant"] == previous_sets["task_relevant"]
        and current_sets["task_unresolved"]
        == previous_sets["task_unresolved"] - one_n0_set
        and current_sets["task_not_relevant"]
        == previous_sets["task_not_relevant"] | one_n0_set
        and current_sets["training_include"]
        == previous_sets["training_include"]
        and current_sets["training_unresolved"]
        == previous_sets["training_unresolved"] - one_n0_set
        and current_sets["training_not_applicable"]
        == previous_sets["training_not_applicable"] | one_n0_set
        and current_sets["chemistry_negative"]
        == previous_sets["chemistry_negative"]
        and current_sets["training_exclude"] == previous_sets["training_exclude"]
        and current_sets["future_candidate"]
        == previous_sets["future_candidate"]
        and current_sets["formal_split"] == previous_sets["formal_split"]
        and current_sets["formal_admitted"] == previous_sets["formal_admitted"]
        and current_sets["runtime_usable"] == previous_sets["runtime_usable"]
    ):
        _fail("ONE_N0_EXACT_SET_ALGEBRA_INVALID")

    if Counter(row["chemistry_disposition"] for row in rows) != Counter(
        {"POSITIVE": 116, "NOT_ESTABLISHED": 90, "UNRESOLVED": 794}
    ):
        _fail("CENSUS_CHEMISTRY_DISTRIBUTION_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter(
        {"RELEVANT": 117, "NOT_RELEVANT": 90, "UNRESOLVED": 793}
    ):
        _fail("CENSUS_TASK_DISTRIBUTION_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter(
        {
            "INCLUDE": 48,
            "EXCLUDE_FROM_TRAINING_ONLY": 68,
            "NOT_APPLICABLE": 90,
            "UNRESOLVED": 794,
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
    if sum(row["human_training_excluded"] == "true" for row in rows) != 68:
        _fail("CENSUS_HUMAN_TRAINING_EXCLUSION_COUNT_INVALID")
    if Counter(
        row["role_profile"]
        for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    ) != Counter({base.STRICT_PROFILE: 52, base.DIRECT_PROFILE: 64}):
        _fail("CENSUS_ROLE_PROFILE_DISTRIBUTION_INVALID")

    applicability_counts: Counter[int] = Counter()

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
                raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
                    f"{ERROR_TOKEN}:ROLE_TASK_IDS_JSON_INVALID:{event_id}"
                ) from error
            if expected_task_ids is None or task_ids != expected_task_ids or 3 not in task_ids:
                _fail("ROLE_EXACT5_APPLICABILITY_INVALID:" + event_id)
            applicability_counts.update(task_ids)
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
    if applicability_counts != Counter({0: 116, 1: 52, 2: 52, 3: 116, 4: 116}):
        _fail("CANONICAL_EXACT5_APPLICABILITY_COUNTS_INVALID")
    if (
        len(CANONICAL_EXACT5_V1) != 5
        or CANONICAL_EXACT5_V1[3][1:] != ("scaffold_only", "B3")
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_INVALID")

    reconciliation = _validate_one_n0_reconciliation_v1(root)
    expected_top = _top_pending_review_units_v1(root, reconciliation)
    if summary != _build_summary_v1(rows, expected_top):
        _fail("SUMMARY_NOT_EXACTLY_DERIVED_FROM_REFRESHED_ROWS_AND_FULL_QUEUE")

    identities: set[tuple[str, str]] = set()
    additive_roles = {item[0] for item in _ADDITIVE_SOURCE_SPECS_V1}
    for binding in bindings:
        if type(binding) is not dict:
            _fail("SEMANTIC_SOURCE_BINDING_SCHEMA_INVALID")
        expected_keys = {
            "artifact_role",
            "path",
            "path_namespace",
            "byte_count",
            "sha256",
        }
        if "expected_executable" in binding:
            expected_keys.add("expected_executable")
        if (
            binding.get("artifact_role") in additive_roles
            and "expected_executable" not in binding
        ):
            _fail("ADDITIVE_SOURCE_EXECUTABLE_CLASS_MISSING")
        if set(binding) != expected_keys:
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
            or (
                "expected_executable" in binding
                and type(binding["expected_executable"]) is not bool
            )
        ):
            _fail("SEMANTIC_SOURCE_BINDING_VALUE_INVALID")
        identity = (namespace, path)
        if identity in identities:
            _fail("SEMANTIC_SOURCE_BINDING_DUPLICATE")
        identities.add(identity)
    predecessor_roles = {
        item["artifact_role"] for item in frozen.semantic_source_bindings
    }
    if (
        len(additive_roles) != len(_ADDITIVE_SOURCE_SPECS_V1)
        or additive_roles & predecessor_roles
    ):
        _fail("ADDITIVE_SEMANTIC_SOURCE_BINDING_ROLE_COLLISION")
    expected_bindings = _merge_semantic_bindings_v1(
        frozen.semantic_source_bindings, _verify_additive_sources(root)
    )
    if bindings != expected_bindings or len(bindings) != 120:
        _fail("SEMANTIC_SOURCE_BINDING_SET_NOT_EXACT_PREDECESSOR_PLUS_ADDITIVE")
    predecessor_identities = {
        (item["path_namespace"], item["path"])
        for item in frozen.semantic_source_bindings
    }
    filtered_predecessor = tuple(
        binding
        for binding in bindings
        if (binding["path_namespace"], binding["path"]) in predecessor_identities
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
        raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
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


def build_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
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
    computation = compute_covapie_cumulative1000_current_global_readiness_census_with_1n0_v1(
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
        "predecessor_manifest_validation_binding": {
            "artifact_role": "PREDECESSOR_I12_MANIFEST_VALIDATION_IDENTITY",
            "path": PREDECESSOR_MANIFEST_RELATIVE.as_posix(),
            "path_namespace": "repository_relative",
            "byte_count": _PREDECESSOR_MANIFEST_SPEC_V1[0],
            "sha256": _PREDECESSOR_MANIFEST_SPEC_V1[1],
            "expected_executable": _PREDECESSOR_MANIFEST_SPEC_V1[2],
        },
        "frozen_priority_queue_validation_binding": {
            "artifact_role": "CURRENT_FROZEN_PRIORITY_QUEUE",
            "path": PRIORITY_QUEUE_RELATIVE.as_posix(),
            "path_namespace": "repository_relative",
            "byte_count": 50116,
            "sha256": (
                "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"
            ),
            "expected_executable": False,
        },
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
        "refresh_contract": {
            "row_count": 1000,
            "column_count": 47,
            "changed_event_count": 4,
            "unchanged_event_count": 996,
            "changed_field_count_per_one_n0_row": 9,
            "semantic_source_binding_count": 120,
            "predecessor_semantic_source_binding_count": 114,
            "additive_semantic_source_binding_count": 6,
            "semantic_identity_collision_count": 0,
            "source_role_collision_count": 0,
            "queue_refreshed": False,
            "training_started": False,
            "ready_for_training": False,
            "source_binding_v2_clean_from_birth": True,
            "new_numeric_POSIX_semantic_identity": False,
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


def _validate_materialization_destination_v1(target_root: Path) -> None:
    """Reject every unsafe or contaminated destination before any write."""

    try:
        root_metadata = target_root.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
            f"{ERROR_TOKEN}:OUTPUT_ROOT_LSTAT_FAILED"
        ) from error
    if stat.S_ISLNK(root_metadata.st_mode):
        _fail("OUTPUT_ROOT_SYMLINK_FORBIDDEN")
    if not stat.S_ISDIR(root_metadata.st_mode):
        _fail("OUTPUT_ROOT_NOT_DIRECTORY")
    try:
        entries = tuple(target_root.iterdir())
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
            f"{ERROR_TOKEN}:OUTPUT_ROOT_INVENTORY_READ_FAILED"
        ) from error
    allowed = {CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE}
    unexpected = sorted(entry.name for entry in entries if entry.name not in allowed)
    if unexpected:
        _fail("OUTPUT_DIRECTORY_UNEXPECTED_ENTRY:" + unexpected[0])
    for entry in entries:
        try:
            metadata = entry.lstat()
        except OSError as error:
            raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
                f"{ERROR_TOKEN}:OUTPUT_ENTRY_LSTAT_FAILED:{entry.name}"
            ) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("OUTPUT_ENTRY_NOT_REGULAR:" + entry.name)


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=path.name + ".",
            suffix=".tmp",
            dir=path.parent,
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
            f"{ERROR_TOKEN}:OUTPUT_WRITE_FAILED:{path.name}"
        ) from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
    repo_root: Path,
    output_directory: Path | None = None,
) -> dict[str, bytes]:
    """Write only Exact3 after complete source and semantic validation."""

    root = repo_root.resolve()
    output = (
        root / OUTPUT_DIRECTORY_RELATIVE
        if output_directory is None
        else Path(output_directory)
    )
    _validate_materialization_destination_v1(output)
    artifacts = build_covapie_cumulative1000_current_global_readiness_artifacts_with_1n0_v1(
        root
    )
    try:
        output.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWith1N0Error(
            f"{ERROR_TOKEN}:OUTPUT_DIRECTORY_CREATE_FAILED"
        ) from error
    for filename in (CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE):
        _atomic_write(output / filename, artifacts[filename])
    return artifacts
