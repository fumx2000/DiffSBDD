"""Append the published EI3 Exact3 to completed-decision reconciliation.

The EI3 ingestion owner remains the owner of the rich approved human decision.
This metadata-only successor validates the published no-write projection,
converts its formal binding to the generic repository-parent namespace, appends
one source to the published with-ME7 chain, and invokes the unchanged generic
reconciler over the same historical adapter.  It does not refresh census or
queue state, create task labels or tensors, admit training, update parameters,
or train.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import asdict
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, NoReturn

from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_me7_v1
    as predecessor_owner,
)
from covalent_ext import (
    covapie_completed_human_decision_reconciliation_with_tp2_v1
    as historical_adapter_owner,
)
from covalent_ext import (
    covapie_ei3_completed_decision_ingestion_and_task_label_availability_v1
    as ingestion,
)


__all__ = (
    "CompletedDecisionReconciliationWithEI3Error",
    "project_ei3_completed_decision_v1",
    "load_real_completed_decision_sources_with_ei3_v1",
    "reconcile_real_completed_human_decisions_with_ei3_v1",
    "build_artifact_v1",
    "materialize_artifact_v1",
    "check_materialized_v1",
)

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_ei3_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_completed_human_decision_reconciliation_with_ei3_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_completed_human_decision_reconciliation_with_ei3_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_completed_human_decision_reconciliation_with_ei3_v1"
)
OUTPUT_NAME = "covapie_completed_human_decision_reconciliation_with_ei3_v1.json"
OUTPUT_RELATIVE = OUTPUT_ROOT_RELATIVE / OUTPUT_NAME
EXACT4_PATHS = (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE, OUTPUT_RELATIVE)

ERROR_PREFIX = "COVAPIE_EI3_RECONCILIATION_V1_ERROR"
_HISTORICAL_PRIORITY_RANK = "33"
_FORMAL_BYTES = 68366
_FORMAL_SHA256 = "f0cf2e1703a327d2ace42bb0aba900e1f4a5ef46de96cc2c5f4acf93add2f5f7"
_FORMAL_VALIDATOR_BYTES = 69828
_FORMAL_VALIDATOR_SHA256 = (
    "90773895c5a74ffb65a7f59d50cfcc5766355d74b98e269ebc1848acf184ae9b"
)
_INGESTION_OUTPUT_BINDINGS = {
    ingestion.SNAPSHOT: (
        121827,
        "9ac803f7872500946824d7db7ccb0da1bd2e9fbda8a2705e61cf8c99817a7c9d",
    ),
    ingestion.MATRIX: (
        4847,
        "e5a80902f1b4ffc887b2f99d642cf82c6c6acb77c52f0a78ae1960282ec67238",
    ),
    ingestion.SUMMARY: (
        3204,
        "60710e40ff18e72ba2fa88008934912adecbd363509f82ce2616e7f24c353fb4",
    ),
    ingestion.MANIFEST: (
        31358,
        "e94eb5bc27405f2f2c522f4469ec0a2835a3c7a98c2f30e663604791d34dcb7b",
    ),
}
_PREDECESSOR_ARTIFACT_BYTES = 351626
_PREDECESSOR_ARTIFACT_SHA256 = (
    "287bb3e9e6ed954bd6f1bf72a4813713a73b74612d0cd2db640e2e57f593ae50"
)
_GENERIC_FACT_FIELDS = (
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
_SOURCE_BINDING_FIELDS = (
    "source_path",
    "path_namespace",
    "byte_count",
    "sha256",
    "schema_version",
    "review_unit_id",
)
_ARTIFACT_FIELDS = (
    "reconciled_rows",
    "source_bindings",
    "normalized_facts",
    "review_summary",
)
_PREDECESSOR_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 127,
    "completed_positive_unit_count": 21,
    "completed_negative_event_count": 51,
    "completed_negative_unit_count": 11,
    "completed_total_event_count": 178,
    "completed_total_unit_count": 32,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 160,
    "unreviewed_unit_count": 99,
}
_SUCCESSOR_REVIEW_SUMMARY = {
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
PREDECESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 154,
    "accepted_review_unit_count": 28,
    "stable_source_identity_count": 28,
    "remaining_unreviewed_chemistry_event_count": 184,
    "remaining_unreviewed_review_unit_upper_bound": 103,
    "decision_category_distribution": {
        "chemistry_positive": 103,
        "chemistry_negative": 20,
        "task_domain_negative": 31,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
SUCCESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 157,
    "accepted_review_unit_count": 29,
    "stable_source_identity_count": 29,
    "remaining_unreviewed_chemistry_event_count": 181,
    "remaining_unreviewed_review_unit_upper_bound": 102,
    "decision_category_distribution": {
        "chemistry_positive": 103,
        "chemistry_negative": 20,
        "task_domain_negative": 34,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
_FORBIDDEN_RICH_FACT_FIELDS = frozenset(
    {
        "completed_lane",
        "protein_reactive_atom",
        "ligand_reactive_atom",
        "reactive_pair",
        "observed_pair",
        "role_partition",
        "role_profile",
        "selected_candidate",
        "warhead_atoms",
        "linker_atoms",
        "scaffold_atoms",
        "W",
        "L",
        "S",
        "seed",
        "minimal_seed",
        "primary_anchor",
        "task_ids",
        "applicable_task_ids",
        "PRE",
        "POST",
        "geometry",
        "geometry_outlier",
        "training_target",
        "training_tensor",
        "training_mask_targets",
    }
)
_ALLOWED_RECONCILIATION_FIELDS = frozenset(
    {
        "current_review_status",
        "current_status_authority_sources_json",
        "calibration_eligible",
        "calibration_exclusion_reason",
    }
)


class CompletedDecisionReconciliationWithEI3Error(ValueError):
    """Raised when the exact additive EI3 contract cannot be proven."""


def _fail(token: str) -> NoReturn:
    raise CompletedDecisionReconciliationWithEI3Error(f"{ERROR_PREFIX}:{token}")


def _mapping(value: object, token: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        _fail(token)
    return value


def _list(value: object, token: str) -> list[Any]:
    if type(value) is not list:
        _fail(token)
    return value


def _expect_fields(
    value: object, expected: Mapping[str, object], token: str
) -> Mapping[str, Any]:
    observed = _mapping(value, token + ":NOT_OBJECT")
    if any(
        type(observed.get(key)) is not type(expected_value)
        or observed.get(key) != expected_value
        for key, expected_value in expected.items()
    ):
        _fail(token)
    return observed


def _expected_binding_v1(bound: Mapping[str, object]) -> generic.SourceBinding:
    path = ingestion.FORMAL_DECISION_RELATIVE.as_posix()
    record = _mapping(
        bound.get("formal_decision_binding"), "EI3_FORMAL_BINDING_NOT_OBJECT"
    )
    if record != {
        "path": path,
        "path_namespace": "project_parent_relative",
        "byte_count": _FORMAL_BYTES,
        "SHA256": _FORMAL_SHA256,
        "semantic_source_identity": (
            "project_parent_relative:" + path + "@" + _FORMAL_SHA256
        ),
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "EI3_FROZEN_FORMAL_HUMAN_DECISION",
        "validation_method": "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    }:
        _fail("EI3_FORMAL_SOURCE_BINDING_INVALID")
    validator_path = ingestion.FORMAL_VALIDATOR_RELATIVE.as_posix()
    validator = _mapping(
        bound.get("formal_validator_binding"), "EI3_VALIDATOR_BINDING_NOT_OBJECT"
    )
    if validator != {
        "path": validator_path,
        "path_namespace": "project_parent_relative",
        "byte_count": _FORMAL_VALIDATOR_BYTES,
        "SHA256": _FORMAL_VALIDATOR_SHA256,
        "semantic_source_identity": (
            "project_parent_relative:"
            + validator_path
            + "@"
            + _FORMAL_VALIDATOR_SHA256
        ),
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "EI3_FROZEN_FORMAL_VALIDATOR",
        "validation_method": (
            "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
        ),
    }:
        _fail("EI3_FORMAL_VALIDATOR_PROVENANCE_BOUNDARY_INVALID")
    binding = generic.SourceBinding(
        source_path=path,
        path_namespace="repository_parent_relative",
        byte_count=_FORMAL_BYTES,
        sha256=_FORMAL_SHA256,
        schema_version=ingestion.FORMAL_DECISION_SCHEMA,
        review_unit_id=ingestion.EXPECTED_REVIEW_UNIT_ID,
    )
    try:
        generic._validate_source_binding(binding)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithEI3Error(
            f"{ERROR_PREFIX}:EI3_GENERIC_SOURCE_BINDING_REJECTED:{error}"
        ) from error
    return binding


def _validate_published_ingestion_v1(
    repo_root: Path, bound: Mapping[str, object]
) -> None:
    """SHA-bind the published EI3 outputs and cross-check both JSON projections."""

    if tuple(ingestion.OUTPUT_FILENAMES) != tuple(_INGESTION_OUTPUT_BINDINGS):
        _fail("EI3_INGESTION_OUTPUT_NAME_CONTRACT_DRIFT")
    payloads: dict[str, bytes] = {}
    for name in ingestion.OUTPUT_FILENAMES:
        path = repo_root / ingestion.OUTPUT_ROOT_RELATIVE / name
        try:
            metadata, payload = path.lstat(), path.read_bytes()
        except OSError as error:
            raise CompletedDecisionReconciliationWithEI3Error(
                f"{ERROR_PREFIX}:EI3_PUBLISHED_OUTPUT_READ_FAILED:{name}"
            ) from error
        expected_size, expected_sha = _INGESTION_OUTPUT_BINDINGS[name]
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or len(payload) != expected_size
            or generic._sha256(payload) != expected_sha
        ):
            _fail("EI3_PUBLISHED_OUTPUT_IDENTITY_DRIFT:" + name)
        payloads[name] = payload
    try:
        snapshot = generic._strict_json_object(
            payloads[ingestion.SNAPSHOT], "EI3_PUBLISHED_SNAPSHOT"
        )
        manifest = generic._strict_json_object(
            payloads[ingestion.MANIFEST], "EI3_PUBLISHED_MANIFEST"
        )
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithEI3Error(
            f"{ERROR_PREFIX}:EI3_PUBLISHED_JSON_INVALID:{error}"
        ) from error
    expected = bound.get("generic_Exact11_compatibility")
    if (
        snapshot.get("generic_Exact11_compatibility") != expected
        or manifest.get("generic_Exact11_compatibility") != expected
        or snapshot.get("formal_source_binding")
        != bound.get("formal_decision_binding")
        or manifest.get("formal_source_binding")
        != bound.get("formal_decision_binding")
        or snapshot.get("formal_validator_binding")
        != bound.get("formal_validator_binding")
        or manifest.get("formal_validator_binding")
        != bound.get("formal_validator_binding")
    ):
        _fail("EI3_PUBLISHED_SNAPSHOT_MANIFEST_PROJECTION_DRIFT")
    events = _list(snapshot.get("events"), "EI3_PUBLISHED_EVENTS_NOT_LIST")
    if [row.get("canonical_event_id") for row in events if type(row) is dict] != list(
        ingestion.EXPECTED_EVENT_IDS
    ):
        _fail("EI3_PUBLISHED_EVENTS_NOT_EXACT3")


def _validate_rich_ei3_boundary_v1(bound: Mapping[str, object]) -> None:
    """Validate the EI3 fields that authorize the Exact11-only projection."""

    formal = _mapping(bound.get("formal_document"), "EI3_FORMAL_NOT_OBJECT")
    _expect_fields(
        formal,
        {
            "schema_version": ingestion.FORMAL_DECISION_SCHEMA,
            "stage": ingestion.FORMAL_STAGE,
            "record_role": ingestion.FORMAL_RECORD_ROLE,
        },
        "EI3_FORMAL_ROOT_INVALID",
    )
    _expect_fields(
        formal.get("sample_identity"),
        {
            "ligand_component_id": "EI3",
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "scope": ingestion.EXPECTED_SCOPE,
            "target_event_count": 3,
            "canonical_target_event_ids": list(ingestion.EXPECTED_EVENT_IDS),
            "scaleup_ranks": list(ingestion.EXPECTED_RANKS),
            "pdb_ids": list(ingestion.EXPECTED_PDB_IDS),
            "all_EI3_authority": False,
            "all_Savinase_authority": False,
            "other_structure_authority": False,
        },
        "EI3_FORMAL_IDENTITY_INVALID",
    )
    _expect_fields(
        formal.get("sample_level_authority"),
        {
            "approved": True,
            "human_review_completed": True,
            "human_decision_created": True,
            "formal_decision_created": True,
            "formal_sample_level_authority_created": True,
            "sample_chemistry_authority": True,
            "sample_task_domain_authority": True,
            "sample_observed_pair_authority": True,
            "sample_D6_disposition_authority": True,
            "role_partition_sample_authoritative": False,
            "minimal_seed_sample_authoritative": False,
            "task_applicability_sample_authoritative": False,
            "unsigned": False,
        },
        "EI3_APPROVAL_STATE_INVALID",
    )
    decisions = _mapping(formal.get("approved_D1_D6"), "EI3_D1_D6_NOT_OBJECT")
    # Spell out the real long semantic keys; no predecessor aliases are accepted.
    expected_decisions = {
        "D1_observed_covalent_chemistry": {
            "chemistry_positive": True,
            "decision": "POSITIVE",
            "human_answered": True,
            "human_approved": True,
            "scope": (
                "THREE_SOURCE_OBSERVATIONS_ONLY_NO_GENERAL_MECHANISM_OR_TRAINING_INFERENCE"
            ),
        },
        "D2_task_generation_domain_relevance": {
            "chemistry_negative": False,
            "chemistry_positive_preserved": True,
            "decision": "OUT_OF_DOMAIN",
            "human_answered": True,
            "human_approved": True,
            "scope": "CURRENT_UNIT_AND_CURRENT_PROJECT_TASK_DEFINITION_ONLY",
        },
        "D3_reactive_atom_pair_confirmation_or_revision": {
            "component_atom": "C1",
            "decision": "CONFIRM_OBSERVED_PAIR",
            "human_answered": True,
            "human_approved": True,
            "metal_context_connection_count_by_pdb": {
                "5ARB": 0,
                "5ARC": 0,
                "5ARD": 2,
            },
            "pair": "SG:C1",
            "protein_atom": "SG",
            "target_covalent_connection_count_by_pdb": {
                "5ARB": 1,
                "5ARC": 1,
                "5ARD": 1,
            },
        },
        "D4_role_partition_and_minimal_seed": {
            "decision": "CANNOT_DETERMINE",
            "human_answered": True,
            "human_approved": True,
            "role_candidate_count": 0,
            "selected_candidate_id": None,
        },
        "D5_structural_task_applicability": {
            "decision": "NOT_DETERMINABLE",
            "human_answered": True,
            "human_approved": True,
            "task_ids": None,
        },
        "D6_later_training_use_disposition": {
            "chemistry_negative": False,
            "decision": "NOT_APPLICABLE",
            "formal_training_admitted": False,
            "future_training_admission_candidate": False,
            "human_answered": True,
            "human_approved": True,
            "human_training_excluded": False,
        },
    }
    if decisions != expected_decisions:
        _fail("EI3_D1_D6_BOUNDARY_INVALID")

    roles = _expect_fields(
        formal.get("role_and_task_disposition"),
        {
            "D4_formally_answered": True,
            "D5_formally_answered": True,
            "role_candidate_count": 0,
            "role_partitions": None,
            "selected_candidate_id": None,
            "selected_role_candidate": None,
            "role_profile": None,
            "warhead_atom_ids": None,
            "linker_atom_ids": None,
            "scaffold_atom_ids": None,
            "minimal_seed": None,
            "minimal_seed_atom_ids": None,
            "primary_anchor": None,
            "applicable_task_ids": None,
            "role_runtime_executed": False,
            "combination_search_executed": False,
            "task_runtime_executed": False,
            "canonical_v1_task_count": 5,
            "B3_present": True,
            "sixth_task_created": False,
        },
        "EI3_NULL_ROLE_TASK_BOUNDARY_INVALID",
    )
    tasks = _list(roles.get("canonical_v1_tasks"), "EI3_EXACT5_TASKS_INVALID")
    if (
        len(tasks) != 5
        or [row.get("semantic_long_name") for row in tasks if type(row) is dict]
        != [row[1] for row in ingestion.CANONICAL_TASKS]
        or not any(
            type(row) is dict
            and row.get("semantic_long_name") == "scaffold_only"
            and row.get("display_alias") == "B3"
            for row in tasks
        )
    ):
        _fail("EI3_EXACT5_LONG_NAMES_OR_B3_INVALID")

    pre = _expect_fields(
        formal.get("PRE_boundary"),
        {
            "accurate_PRE_is_not_V1_global_hard_prerequisite": True,
            "accurate_PRE_required_before_training_feature_contract": False,
            "sample_cannot_determine_generalized_to_all_samples": False,
            "sample_role_task_or_training_conditions_satisfied": False,
        },
        "EI3_PRE_BOUNDARY_INVALID",
    )
    _expect_fields(
        pre.get("frozen_source_projection"),
        {
            "PRE_authority_created": False,
            "PRE_coordinates_created": False,
            "PRE_geometry_authoritative_count": 0,
            "PRE_source_graph_count_per_event": [0, 0, 0],
            "PRE_source_graph_mapping_count_per_event": [0, 0, 0],
            "PRE_source_graph_mapping_status_per_event": [
                ingestion.PRE_MAPPING_STATUS
            ]
            * 3,
            "PRE_status_per_event": [ingestion.PRE_STATUS] * 3,
            "PRE_topology_created": False,
            "PRE_zero_fill": False,
            "POST_to_PRE_copy": False,
        },
        "EI3_PRE_FROZEN_SOURCE_PROJECTION_INVALID",
    )
    non_created = _mapping(
        formal.get("non_created_authority"), "EI3_NON_CREATED_AUTHORITY_INVALID"
    )
    if any(
        non_created.get(key) is not False
        for key in (
            "TASK_LABEL_AUTHORITY",
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED",
            "MASK_TENSOR_TARGETS_CREATED",
            "TRAINING_ADMISSION_CREATED",
            "TRAINING_MATERIALIZATION_ALLOWED",
            "PARAMETER_UPDATE_AUTHORIZATION",
            "READY_FOR_TRAINING",
            "TRAINING_STARTED",
            "PRE_authority",
            "POST_geometry_training_authority",
            "reusable_authority_created",
        )
    ):
        _fail("EI3_NON_CREATED_AUTHORITY_INVALID")
    _expect_fields(
        formal.get("readiness"),
        {
            "AUTHORIZATION_COMPLETE": True,
            "HUMAN_REVIEW_COMPLETED": True,
            "FORMAL_TRAINING_ADMITTED": False,
            "TASK_LABEL_AUTHORITY": False,
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
            "MASK_TENSOR_TARGETS_CREATED": False,
            "TRAINING_MATERIALIZATION_ALLOWED": False,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
            "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
        },
        "EI3_READINESS_BOUNDARY_INVALID",
    )
    operations = _mapping(
        formal.get("operation_boundary"), "EI3_OPERATION_BOUNDARY_INVALID"
    )
    if any(
        operations.get(key) is not False
        for key in (
            "census_refresh_performed",
            "queue_refresh_performed",
            "reconciliation_performed",
            "task_label_materialization_performed",
            "mask_tensor_materialization_performed",
            "training_preparation_performed",
            "parameter_update_performed",
            "training_performed",
            "repository_modified",
            "commit_performed",
            "push_performed",
        )
    ):
        _fail("EI3_OPERATION_BOUNDARY_INVALID")

    schema = _expect_fields(
        bound.get("schema_preflight"),
        {
            "status": "PASS",
            "formal_schema": ingestion.FORMAL_DECISION_SCHEMA,
            "uses_sample_observed_pair_authority": True,
            "uses_ME7_sample_pair_authority": False,
            "uses_nested_PRE_frozen_source_projection": True,
            "uses_ME7_top_level_PRE_source_mapping_count_per_event": False,
        },
        "EI3_SCHEMA_PREFLIGHT_INVALID",
    )
    consumed = _list(schema.get("actual_consumed_paths"), "EI3_SCHEMA_PATHS_INVALID")
    required_paths = {
        "$.sample_identity.scaleup_ranks",
        "$.sample_level_authority.sample_observed_pair_authority",
        "$.approved_D1_D6.D1_observed_covalent_chemistry",
        "$.approved_D1_D6.D2_task_generation_domain_relevance",
        "$.approved_D1_D6.D3_reactive_atom_pair_confirmation_or_revision",
        "$.approved_D1_D6.D4_role_partition_and_minimal_seed",
        "$.approved_D1_D6.D5_structural_task_applicability",
        "$.approved_D1_D6.D6_later_training_use_disposition",
        "$.PRE_boundary.frozen_source_projection.PRE_source_graph_count_per_event",
    }
    if not required_paths <= set(consumed):
        _fail("EI3_SCHEMA_PATHS_INVALID")

    compatibility = _expect_fields(
        bound.get("generic_Exact11_compatibility"),
        {
            "generic_exact11_compatibility_pass": True,
            "generic_fact_field_count": 11,
            "generic_fact_fields": list(_GENERIC_FACT_FIELDS),
            "accepted_fact_count": 3,
            "completed_lane": ingestion.EXPECTED_COMPLETED_LANE,
            "source_formal_D2": "OUT_OF_DOMAIN",
            "normalized_task_relevance_disposition": generic.TASK_NOT_RELEVANT,
            "source_formal_D6": "NOT_APPLICABLE",
            "normalized_training_disposition": generic.TRAINING_NOT_APPLICABLE,
            "rich_fields_leaked": False,
            "NormalizedDecisionSource_constructed": True,
            "reconciliation_performed": False,
            "path_namespace_conversion": {
                "ingestion_binding_namespace": "project_parent_relative",
                "generic_binding_namespace": "repository_parent_relative",
                "stable_source_path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
                "strings_not_interchanged_without_explicit_conversion": True,
            },
        },
        "EI3_GENERIC_COMPATIBILITY_BOUNDARY_INVALID",
    )
    facts = _list(compatibility.get("facts"), "EI3_GENERIC_FACTS_INVALID")
    if len(facts) != 3 or any(
        type(fact) is not dict or tuple(fact) != _GENERIC_FACT_FIELDS
        for fact in facts
    ):
        _fail("EI3_GENERIC_COMPATIBILITY_NOT_EXACT3_EXACT11")

    _expect_fields(
        bound.get("current_census_and_queue_boundary"),
        {
            "EI3_event_count": 3,
            "EI3_current_global_status": generic.CURRENTLY_UNREVIEWED,
            "EI3_current_review_status": generic.CURRENTLY_UNREVIEWED,
            "EI3_human_review_completed": False,
            "EI3_structurally_applicable_task_ids": None,
            "EI3_current_pending_rank": 1,
            "EI3_raw_priority_rank": 33,
            "census_refresh_performed": False,
            "queue_refresh_performed": False,
            "historical_pending_state_is_expected_until_refresh": True,
        },
        "EI3_CURRENT_CENSUS_QUEUE_BOUNDARY_INVALID",
    )
    events = _list(bound.get("events"), "EI3_EVENTS_NOT_LIST")
    actual_triplets = [
        (row.get("canonical_event_id"), row.get("scaleup_rank"), row.get("pdb_id"))
        for row in events
        if type(row) is dict
    ]
    expected_triplets = list(
        zip(
            ingestion.EXPECTED_EVENT_IDS,
            ingestion.EXPECTED_RANKS,
            ingestion.EXPECTED_PDB_IDS,
            strict=True,
        )
    )
    if len(events) != 3 or actual_triplets != expected_triplets:
        _fail("EI3_TARGET_EVENT_IDENTITY_INVALID")
    context = _list(
        bound.get("metal_supporting_context"), "EI3_METAL_CONTEXT_NOT_LIST"
    )
    if (
        len(context) != 2
        or [row.get("connection_id") for row in context if type(row) is dict]
        != ["metalc8", "metalc9"]
        or any(
            type(row) is not dict
            or row.get("canonical_event_id") is not None
            or row.get("scaleup_rank") is not None
            or row.get("supporting_context_only") is not True
            or row.get("target_event") is not False
            or row.get("authority_created") is not False
            for row in context
        )
    ):
        _fail("EI3_METAL_CONTEXT_BOUNDARY_INVALID")
    _expected_binding_v1(bound)

def _projection_records_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    _validate_rich_ei3_boundary_v1(bound)
    binding = _expected_binding_v1(bound)
    records = tuple(
        {
            "canonical_event_id": event_id,
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "human_review_completed": True,
            "legacy_completed_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
            "task_relevance_disposition": generic.TASK_NOT_RELEVANT,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_NOT_APPLICABLE,
            "human_training_excluded": False,
            "source_decision_schema": ingestion.FORMAL_DECISION_SCHEMA,
            "source_decision_sha256": binding.sha256,
            "source_binding_path": binding.source_path,
        }
        for event_id in ingestion.EXPECTED_EVENT_IDS
    )
    compatibility = _mapping(
        bound.get("generic_Exact11_compatibility"), "EI3_GENERIC_FACTS_INVALID"
    )
    if (
        any(tuple(record) != _GENERIC_FACT_FIELDS for record in records)
        or compatibility.get("facts") != [dict(record) for record in records]
    ):
        _fail("EI3_GENERIC_PROJECTION_NOT_VALIDATED_EXACT3_EXACT11")
    return records


def _validate_projected_ei3_source_v1(
    source: generic.NormalizedDecisionSource,
    records: Sequence[Mapping[str, object]],
) -> None:
    if (
        tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__)
        != _GENERIC_FACT_FIELDS
    ):
        _fail("GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11")
    if len(source.facts) != 3 or len(records) != 3:
        _fail("EI3_SOURCE_PROJECTION_NOT_EXACT3")
    try:
        generic._validate_source_binding(source.binding)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithEI3Error(
            f"{ERROR_PREFIX}:EI3_GENERIC_SOURCE_BINDING_REJECTED:{error}"
        ) from error
    for fact, record in zip(source.facts, records, strict=True):
        actual = asdict(fact)
        if (
            tuple(fact.__dataclass_fields__) != _GENERIC_FACT_FIELDS
            or actual != dict(record)
            or set(actual) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(actual)
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
            or fact.human_training_excluded is not False
        ):
            _fail("EI3_GENERIC_PROJECTION_CLASSIFICATION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWithEI3Error(
                f"{ERROR_PREFIX}:EI3_GENERIC_FACT_REJECTED:{error}"
            ) from error


def _project_bound_ei3_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    records = _projection_records_v1(bound)
    try:
        facts = tuple(
            generic.NormalizedCompletedDecisionFact(**dict(record))
            for record in records
        )
    except TypeError as error:
        raise CompletedDecisionReconciliationWithEI3Error(
            f"{ERROR_PREFIX}:EI3_GENERIC_FACT_CONSTRUCTION_FAILED"
        ) from error
    source = generic.NormalizedDecisionSource(
        binding=_expected_binding_v1(bound), facts=facts
    )
    _validate_projected_ei3_source_v1(source, records)
    return source


def _load_bound_v1(repo_root: Path) -> Mapping[str, object]:
    root = Path(repo_root).resolve()
    try:
        bound = ingestion.load_frozen_formal_decision_v1(root)
    except ingestion.EI3IngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithEI3Error(
            f"{ERROR_PREFIX}:EI3_INGESTION_OWNER_VALIDATION_FAILED:{error}"
        ) from error
    _validate_published_ingestion_v1(root, bound)
    return bound


def project_ei3_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load EI3 through published no-write APIs and emit three Exact11 facts."""

    return _project_bound_ei3_v1(_load_bound_v1(repo_root))


def _validate_source_chain_v1(
    predecessor: Sequence[generic.NormalizedDecisionSource],
    successor: Sequence[generic.NormalizedDecisionSource],
    records: Sequence[Mapping[str, object]],
) -> None:
    before, after = tuple(predecessor), tuple(successor)
    before_facts = tuple(fact for source in before for fact in source.facts)
    after_facts = tuple(fact for source in after for fact in source.facts)
    if len(before) != 28 or len(before_facts) != 154:
        _fail("PREDECESSOR_WITH_ME7_SOURCE_CHAIN_NOT_EXACT28_154")
    if len(after) != 29 or after[:-1] != before or len(after_facts) != 157:
        _fail("EI3_SOURCE_CHAIN_NOT_PREFIX_APPEND_EXACT29_157")
    _validate_projected_ei3_source_v1(after[-1], records)
    if after_facts[:154] != before_facts or after_facts[154:] != after[-1].facts:
        _fail("EI3_FACT_CHAIN_NOT_PREFIX_APPEND_EXACT154_PLUS3")
    before_events = [fact.canonical_event_id for fact in before_facts]
    after_events = [fact.canonical_event_id for fact in after_facts]
    target_events = set(ingestion.EXPECTED_EVENT_IDS)
    if (
        target_events & set(before_events)
        or after_events[-3:] != list(ingestion.EXPECTED_EVENT_IDS)
        or len(set(before_events)) != 154
        or len(set(after_events)) != 157
    ):
        _fail("EI3_EVENT_PREFIX_OR_UNIQUENESS_INVALID")
    before_units = {source.binding.review_unit_id for source in before}
    before_ids = {source.binding.stable_identity for source in before}
    if (
        len(before_units) != 28
        or len(before_ids) != 28
        or len({source.binding.review_unit_id for source in after}) != 29
        or len({source.binding.stable_identity for source in after}) != 29
        or after[-1].binding.review_unit_id in before_units
        or after[-1].binding.stable_identity in before_ids
        or any(
            source.binding.path_namespace != "repository_parent_relative"
            for source in after
        )
        or sum(
            source.binding.review_unit_id == ingestion.EXPECTED_REVIEW_UNIT_ID
            for source in after
        )
        != 1
    ):
        _fail("EI3_SOURCE_IDENTITY_NAMESPACE_OR_DUPLICATE_INVALID")


def load_real_completed_decision_sources_with_ei3_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    root = Path(repo_root).resolve()
    before = predecessor_owner.load_real_completed_decision_sources_with_me7_v1(root)
    bound = _load_bound_v1(root)
    records = _projection_records_v1(bound)
    after = (*before, _project_bound_ei3_v1(bound))
    _validate_source_chain_v1(before, after, records)
    return after


def _prove_ei3_predecessor_historical_state_v1(
    rows: Sequence[Mapping[str, str]],
) -> None:
    targets = [
        row
        for row in rows
        if row.get("canonical_event_id") in ingestion.EXPECTED_EVENT_IDS
    ]
    if (
        len(rows) != 338
        or len(targets) != 3
        or tuple(row["canonical_event_id"] for row in targets)
        != ingestion.EXPECTED_EVENT_IDS
        or any(
            row.get("raw_review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
            or row.get("raw_priority_rank") != _HISTORICAL_PRIORITY_RANK
            or row.get("raw_unit_event_count") != "3"
            or row.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
            or row.get("calibration_eligible") != "true"
            or row.get("calibration_exclusion_reason") != ""
            for row in targets
        )
    ):
        _fail("EI3_PREDECESSOR_HISTORICAL_STATE_INVALID")


def _validate_reconciliation_delta_v1(
    before: generic.ReconciliationResult,
    after: generic.ReconciliationResult,
    appended_facts: Sequence[generic.NormalizedCompletedDecisionFact],
) -> None:
    if before.review_summary != _PREDECESSOR_REVIEW_SUMMARY:
        _fail("PREDECESSOR_WITH_ME7_REVIEW_SUMMARY_INVALID")
    if after.review_summary != _SUCCESSOR_REVIEW_SUMMARY:
        _fail("EI3_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if len(before.normalized_facts) != 154 or len(after.normalized_facts) != 157:
        _fail("EI3_RECONCILIATION_FACT_COUNT_INVALID")
    expected_sorted_facts = tuple(
        sorted(
            (*before.normalized_facts, *appended_facts),
            key=lambda fact: (
                fact.canonical_event_id,
                fact.source_binding_path,
                fact.source_decision_sha256,
            ),
        )
    )
    if after.normalized_facts != expected_sorted_facts:
        _fail("EI3_GENERIC_SORTED_FACT_DOMAIN_INVALID")
    targets = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(before.reconciled_rows, after.reconciled_rows, strict=True):
        if old.get("canonical_event_id") not in targets:
            changed_non_target += old != new
            continue
        changed = {key for key in old if old[key] != new[key]}
        if (
            changed != _ALLOWED_RECONCILIATION_FIELDS
            or old["current_review_status"] != generic.CURRENTLY_UNREVIEWED
            or new["current_review_status"] != generic.COMPLETED_HUMAN_NEGATIVE
            or new["current_status_authority_sources_json"]
            != generic._canonical_json(
                [ingestion.FORMAL_DECISION_RELATIVE.as_posix()]
            )
            or old["calibration_eligible"] != "true"
            or new["calibration_eligible"] != "false"
            or old["calibration_exclusion_reason"] != ""
            or new["calibration_exclusion_reason"]
            != generic.COMPLETED_HUMAN_NEGATIVE
        ):
            _fail("EI3_TARGET_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (3, 0):
        _fail("EI3_RECONCILIATION_DELTA_NOT_EXACT3_AND_335")


def _validate_coverage_contract_v1(
    before_sources: Sequence[generic.NormalizedDecisionSource],
    after_sources: Sequence[generic.NormalizedDecisionSource],
) -> None:
    if PREDECESSOR_COVERAGE_SUMMARY != predecessor_owner.SUCCESSOR_COVERAGE_SUMMARY:
        _fail("PREDECESSOR_WITH_ME7_COVERAGE_DRIFT")
    before_facts = [fact for source in before_sources for fact in source.facts]
    after_facts = [fact for source in after_sources for fact in source.facts]
    before_distribution = PREDECESSOR_COVERAGE_SUMMARY[
        "decision_category_distribution"
    ]
    after_distribution = SUCCESSOR_COVERAGE_SUMMARY[
        "decision_category_distribution"
    ]
    if (
        len(before_facts) != 154
        or len(after_facts) != 157
        or after_facts[:154] != before_facts
        or after_facts[154:] != list(after_sources[-1].facts)
        or SUCCESSOR_COVERAGE_SUMMARY["accepted_review_unit_count"]
        != len(after_sources)
        or SUCCESSOR_COVERAGE_SUMMARY["stable_source_identity_count"]
        != len({source.binding.stable_identity for source in after_sources})
        or SUCCESSOR_COVERAGE_SUMMARY["remaining_unreviewed_chemistry_event_count"]
        != 338 - len(after_facts)
        or SUCCESSOR_COVERAGE_SUMMARY[
            "remaining_unreviewed_review_unit_upper_bound"
        ]
        != 131 - len(after_sources)
        or sum(before_distribution.values()) != len(before_facts)
        or sum(after_distribution.values()) != len(after_facts)
        or after_distribution["task_domain_negative"]
        - before_distribution["task_domain_negative"]
        != 3
        or any(
            after_distribution[key] != before_distribution[key]
            for key in (
                "chemistry_positive",
                "chemistry_negative",
                "task_domain_positive",
            )
        )
        or any(
            fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
            or fact.human_training_excluded is not False
            for fact in after_facts[154:]
        )
        or SUCCESSOR_COVERAGE_SUMMARY["label_ready_event_count"] != 16
        or SUCCESSOR_COVERAGE_SUMMARY["training_mask_target_count"] != 0
        or SUCCESSOR_COVERAGE_SUMMARY["training_authority"] is not False
    ):
        _fail("EI3_COVERAGE_DELTA_INVALID")


def _validate_published_predecessor_v1(
    repo_root: Path,
    sources: Sequence[generic.NormalizedDecisionSource],
    result: generic.ReconciliationResult,
) -> None:
    path = repo_root / predecessor_owner.OUTPUT_RELATIVE
    try:
        metadata, payload = path.lstat(), path.read_bytes()
    except OSError as error:
        raise CompletedDecisionReconciliationWithEI3Error(
            f"{ERROR_PREFIX}:PREDECESSOR_WITH_ME7_ARTIFACT_READ_FAILED"
        ) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or len(payload) != _PREDECESSOR_ARTIFACT_BYTES
        or generic._sha256(payload) != _PREDECESSOR_ARTIFACT_SHA256
    ):
        _fail("PREDECESSOR_WITH_ME7_ARTIFACT_IDENTITY_DRIFT")
    mapping = _artifact_mapping_v1(sources, result)
    expected = (
        json.dumps(mapping, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    if payload != expected:
        _fail("PREDECESSOR_WITH_ME7_ARTIFACT_NOT_REPRODUCED")


def _build_components_v1(
    repo_root: Path,
) -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
    generic.ReconciliationResult,
    generic.ReconciliationResult,
]:
    root = Path(repo_root).resolve()
    before_sources = (
        predecessor_owner.load_real_completed_decision_sources_with_me7_v1(root)
    )
    adapted = historical_adapter_owner._adapt_historical_v1(root)
    _prove_ei3_predecessor_historical_state_v1(adapted)
    reproduced_before = generic.reconcile_completed_human_decisions_v1(
        adapted, before_sources
    )
    _validate_published_predecessor_v1(root, before_sources, reproduced_before)
    _prove_ei3_predecessor_historical_state_v1(reproduced_before.reconciled_rows)
    bound = _load_bound_v1(root)
    records = _projection_records_v1(bound)
    after_sources = (*before_sources, _project_bound_ei3_v1(bound))
    _validate_source_chain_v1(before_sources, after_sources, records)
    _validate_coverage_contract_v1(before_sources, after_sources)
    after_result = generic.reconcile_completed_human_decisions_v1(
        adapted, after_sources
    )
    _validate_reconciliation_delta_v1(
        reproduced_before, after_result, after_sources[-1].facts
    )
    return before_sources, after_sources, reproduced_before, after_result


def reconcile_real_completed_human_decisions_with_ei3_v1(
    repo_root: Path,
) -> generic.ReconciliationResult:
    return _build_components_v1(repo_root)[-1]


def _artifact_mapping_v1(
    sources: Sequence[generic.NormalizedDecisionSource],
    reconciliation: generic.ReconciliationResult,
) -> dict[str, object]:
    return {
        "reconciled_rows": [dict(row) for row in reconciliation.reconciled_rows],
        "source_bindings": [asdict(source.binding) for source in sources],
        "normalized_facts": [
            asdict(fact) for source in sources for fact in source.facts
        ],
        "review_summary": dict(reconciliation.review_summary),
    }


def _validate_artifact_mapping_v1(
    value: object,
    *,
    predecessor_sources: Sequence[generic.NormalizedDecisionSource],
    successor_sources: Sequence[generic.NormalizedDecisionSource],
    reconciliation: generic.ReconciliationResult,
) -> None:
    artifact = _mapping(value, "EI3_ARTIFACT_NOT_OBJECT")
    bindings = _list(artifact.get("source_bindings"), "EI3_BINDINGS_NOT_LIST")
    facts = _list(artifact.get("normalized_facts"), "EI3_FACTS_NOT_LIST")
    rows = _list(artifact.get("reconciled_rows"), "EI3_ROWS_NOT_LIST")
    predecessor_facts = [
        asdict(fact) for source in predecessor_sources for fact in source.facts
    ]
    if (
        tuple(artifact) != _ARTIFACT_FIELDS
        or len(bindings) != 29
        or len(facts) != 157
        or len(rows) != 338
        or bindings != [asdict(source.binding) for source in successor_sources]
        or any(
            type(item) is not dict or tuple(item) != _SOURCE_BINDING_FIELDS
            for item in bindings
        )
        or facts
        != [asdict(fact) for source in successor_sources for fact in source.facts]
        or facts[:154] != predecessor_facts
        or facts[154:]
        != [asdict(fact) for fact in successor_sources[-1].facts]
        or any(
            type(item) is not dict
            or tuple(item) != _GENERIC_FACT_FIELDS
            or _FORBIDDEN_RICH_FACT_FIELDS & set(item)
            for item in facts
        )
        or rows != [dict(row) for row in reconciliation.reconciled_rows]
        or artifact.get("review_summary") != reconciliation.review_summary
    ):
        _fail("EI3_ARTIFACT_CONTENT_OR_PREFIX_INVALID")


def build_artifact_v1(repo_root: Path) -> bytes:
    """Build the sole deterministic reconciliation JSON without writing it."""

    before_sources, after_sources, _before, after = _build_components_v1(repo_root)
    mapping = _artifact_mapping_v1(after_sources, after)
    _validate_artifact_mapping_v1(
        mapping,
        predecessor_sources=before_sources,
        successor_sources=after_sources,
        reconciliation=after,
    )
    return (
        json.dumps(mapping, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def _validate_destination_v1(repo_root: Path, destination: Path) -> None:
    if destination.resolve() != (repo_root / OUTPUT_RELATIVE).resolve():
        _fail("EI3_ARTIFACT_DESTINATION_NOT_EXACT")
    parent = destination.parent
    if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
        _fail("EI3_ARTIFACT_PARENT_NOT_REAL_DIRECTORY")
    if parent.exists() and {item.name for item in parent.iterdir()} - {OUTPUT_NAME}:
        _fail("EI3_ARTIFACT_DIRECTORY_CONTAINS_EXTRA_FILE")


def materialize_artifact_v1(repo_root: Path) -> bytes:
    """Atomically write only the authorized reconciliation JSON."""

    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = build_artifact_v1(root)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".covapie_ei3_reconciliation_", dir=destination.parent
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, destination)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
    return payload


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    """Rebuild twice and compare the materialized artifact byte for byte."""

    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    try:
        metadata, observed = destination.lstat(), destination.read_bytes()
    except OSError as error:
        raise CompletedDecisionReconciliationWithEI3Error(
            f"{ERROR_PREFIX}:EI3_MATERIALIZED_ARTIFACT_READ_FAILED"
        ) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_mode & 0o111
    ):
        _fail("EI3_MATERIALIZED_ARTIFACT_SECURITY_INVALID")
    first = build_artifact_v1(root)
    second = build_artifact_v1(root)
    if observed != first or first != second:
        _fail("EI3_MATERIALIZED_ARTIFACT_BYTES_MISMATCH")
    return {
        "status": "PASS",
        "operation": "CHECK",
        "artifact_count": 1,
        "source_count": 29,
        "accepted_fact_count": 157,
        "changed_target_rows": 3,
        "non_target_changed_rows": 0,
        "unchanged_rows": 335,
        "byte_identical_to_rebuild": True,
        "double_build_byte_identical": True,
        "artifact_fact_order_domain": "SOURCE_CHAIN_FLATTEN",
        "generic_result_fact_order_domain": "GENERIC_CANONICAL_SORT",
        "predecessor_source_count": 28,
        "predecessor_accepted_fact_count": 154,
        "review_summary": dict(_SUCCESSOR_REVIEW_SUMMARY),
        "coverage_summary": dict(SUCCESSOR_COVERAGE_SUMMARY),
        "reconciliation_performed": True,
        "census_refresh_performed": False,
        "queue_refresh_performed": False,
        "next_review_started": False,
        "task_label_authority": False,
        "formal_training_admitted": False,
        "feature_semantics_audit_performed": False,
        "feature_semantics_audit_required_before_training": True,
        "step12d_is_only_smoke_legality_check": True,
        "training_authority": False,
        "ready_for_training": False,
        "training_started": False,
        "commit_performed": False,
        "push_performed": False,
    }


def _preflight_report_v1(repo_root: Path) -> dict[str, object]:
    before_sources, after_sources, before, after = _build_components_v1(repo_root)
    before_flat = tuple(fact for source in before_sources for fact in source.facts)
    after_flat = tuple(fact for source in after_sources for fact in source.facts)
    if (
        len(before_flat) != 154
        or len(after_flat) != 157
        or after_flat[:154] != before_flat
        or after_flat[154:] != after_sources[-1].facts
        or before.review_summary != _PREDECESSOR_REVIEW_SUMMARY
        or after.review_summary != _SUCCESSOR_REVIEW_SUMMARY
    ):
        _fail("EI3_PREFLIGHT_RESULT_INVALID")
    return {
        "status": "PASS",
        "operation": "PREFLIGHT",
        "predecessor_source_count": 28,
        "source_count": 29,
        "predecessor_accepted_fact_count": 154,
        "accepted_fact_count": 157,
        "changed_target_rows": 3,
        "non_target_changed_rows": 0,
        "unchanged_rows": 335,
        "source_chain_prefix_preserved": True,
        "artifact_fact_order_domain": "SOURCE_CHAIN_FLATTEN",
        "generic_result_fact_order_domain": "GENERIC_CANONICAL_SORT",
        "review_summary": dict(after.review_summary),
        "coverage_summary": dict(SUCCESSOR_COVERAGE_SUMMARY),
        "reconciliation_performed": True,
        "census_refresh_performed": False,
        "queue_refresh_performed": False,
        "task_label_authority": False,
        "formal_training_admitted": False,
        "ready_for_training": False,
        "training_started": False,
    }


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Build or verify the EI3 completed-decision reconciliation."
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--materialize", action="store_true")
    modes.add_argument("--preflight", action="store_true")
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    try:
        if arguments.preflight:
            report = _preflight_report_v1(root)
            marker = "COVAPIE_EI3_RECONCILIATION_V1_PREFLIGHT_PASS=true"
        elif arguments.materialize:
            payload = materialize_artifact_v1(root)
            report = {
                "status": "PASS",
                "operation": "MATERIALIZE",
                "artifact_count": 1,
                "artifact_bytes": len(payload),
                "artifact_sha256": generic._sha256(payload),
                "source_count": 29,
                "accepted_fact_count": 157,
                "reconciliation_performed": True,
                "census_refresh_performed": False,
                "queue_refresh_performed": False,
                "training_authority": False,
                "ready_for_training": False,
                "training_started": False,
            }
            marker = "COVAPIE_EI3_RECONCILIATION_V1_MATERIALIZE_PASS=true"
        else:
            report = check_materialized_v1(root)
            marker = "COVAPIE_EI3_RECONCILIATION_V1_CHECK_PASS=true"
    except CompletedDecisionReconciliationWithEI3Error as error:
        print(str(error), file=os.sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    print(marker)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
