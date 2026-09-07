"""Append the published 6OA Exact4 to completed-decision reconciliation.

The 6OA ingestion owner remains the sole owner of the rich human decision.
This metadata-only successor independently validates the returned rich bound,
constructs generic Exact11 facts, appends one source to the published with-NWJ
chain, and calls the unchanged generic reconciler over the published historical
adapter.  It does not refresh a census or queue, materialize task labels or
masks, admit training, or train.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, NoReturn

from . import covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1 as ingestion
from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import covapie_completed_human_decision_reconciliation_with_nwj_v1 as predecessor_owner
from . import covapie_completed_human_decision_reconciliation_with_tp2_v1 as historical_adapter_owner


__all__ = (
    "CompletedDecisionReconciliationWith6OAError",
    "project_6oa_completed_decision_v1",
    "load_real_completed_decision_sources_with_6oa_v1",
    "reconcile_real_completed_human_decisions_with_6oa_v1",
    "build_artifact_v1",
    "materialize_artifact_v1",
    "check_materialized_v1",
)

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_6oa_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_completed_human_decision_reconciliation_with_6oa_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_completed_human_decision_reconciliation_with_6oa_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_completed_human_decision_reconciliation_with_6oa_v1"
)
OUTPUT_NAME = "covapie_completed_human_decision_reconciliation_with_6oa_v1.json"
OUTPUT_RELATIVE = OUTPUT_ROOT_RELATIVE / OUTPUT_NAME
EXACT4_PATHS = (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE, OUTPUT_RELATIVE)

ERROR_PREFIX = "COVAPIE_6OA_RECONCILIATION_V1_ERROR"
_HISTORICAL_PRIORITY_RANK = "29"
_FORMAL_BYTES = 33043
_FORMAL_SHA256 = "c79a0f03b0bb9847c190befd351c4c323e1243b10e30655c3b4f61c2f9034218"
_FORMAL_VALIDATOR_BYTES = 96246
_FORMAL_VALIDATOR_SHA256 = (
    "77800ac2056df2b0770967be15bb89c67d2be089d6c54180361f4922ee73731e"
)
_NORMALIZATION_MAPPING = "OUT_OF_DOMAIN_TO_NOT_RELEVANT"
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
    "completed_positive_event_count": 123,
    "completed_positive_unit_count": 20,
    "completed_negative_event_count": 44,
    "completed_negative_unit_count": 9,
    "completed_total_event_count": 167,
    "completed_total_unit_count": 29,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 171,
    "unreviewed_unit_count": 102,
}
_SUCCESSOR_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 123,
    "completed_positive_unit_count": 20,
    "completed_negative_event_count": 48,
    "completed_negative_unit_count": 10,
    "completed_total_event_count": 171,
    "completed_total_unit_count": 30,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 167,
    "unreviewed_unit_count": 101,
}
PREDECESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 143,
    "accepted_review_unit_count": 25,
    "stable_source_identity_count": 25,
    "remaining_unreviewed_chemistry_event_count": 195,
    "remaining_unreviewed_review_unit_upper_bound": 106,
    "decision_category_distribution": {
        "chemistry_positive": 99,
        "chemistry_negative": 20,
        "task_domain_negative": 24,
        "task_domain_positive": 0,
    },
    "label_ready_event_count": 16,
    "training_mask_target_count": 0,
    "training_authority": False,
}
SUCCESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 147,
    "accepted_review_unit_count": 26,
    "stable_source_identity_count": 26,
    "remaining_unreviewed_chemistry_event_count": 191,
    "remaining_unreviewed_review_unit_upper_bound": 105,
    "decision_category_distribution": {
        "chemistry_positive": 99,
        "chemistry_negative": 20,
        "task_domain_negative": 28,
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
        "pair_authority_scope",
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


class CompletedDecisionReconciliationWith6OAError(ValueError):
    """Raised when the exact additive 6OA contract cannot be proven."""


def _fail(token: str) -> NoReturn:
    raise CompletedDecisionReconciliationWith6OAError(f"{ERROR_PREFIX}:{token}")


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
    if any(type(observed.get(key)) is not type(expected_value) or observed.get(key) != expected_value for key, expected_value in expected.items()):
        _fail(token)
    return observed


def _expected_binding_v1(bound: Mapping[str, object]) -> generic.SourceBinding:
    record = _mapping(
        bound.get("formal_decision_binding"), "6OA_FORMAL_BINDING_NOT_OBJECT"
    )
    expected_record = {
        "path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        "path_namespace": "project_parent_relative",
        "byte_count": _FORMAL_BYTES,
        "SHA256": _FORMAL_SHA256,
        "semantic_source_identity": (
            "project_parent_relative:"
            + ingestion.FORMAL_DECISION_RELATIVE.as_posix()
            + "@"
            + _FORMAL_SHA256
        ),
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "6OA_FROZEN_FORMAL_HUMAN_DECISION",
        "validation_method": "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    }
    if record != expected_record:
        _fail("6OA_FORMAL_SOURCE_BINDING_INVALID")
    validator = _mapping(
        bound.get("formal_validator_binding"), "6OA_VALIDATOR_BINDING_NOT_OBJECT"
    )
    if validator != {
        "path": ingestion.FORMAL_VALIDATOR_RELATIVE.as_posix(),
        "path_namespace": "project_parent_relative",
        "byte_count": _FORMAL_VALIDATOR_BYTES,
        "SHA256": _FORMAL_VALIDATOR_SHA256,
        "semantic_source_identity": (
            "project_parent_relative:"
            + ingestion.FORMAL_VALIDATOR_RELATIVE.as_posix()
            + "@"
            + _FORMAL_VALIDATOR_SHA256
        ),
        "expected_path_class": "REGULAR_NON_SYMLINK",
        "expected_executable_class": "NON_EXECUTABLE",
        "source_role": "6OA_FROZEN_FORMAL_VALIDATOR",
        "validation_method": (
            "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
        ),
    }:
        _fail("6OA_FORMAL_VALIDATOR_PROVENANCE_BOUNDARY_INVALID")
    return generic.SourceBinding(
        source_path=ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        path_namespace="repository_parent_relative",
        byte_count=_FORMAL_BYTES,
        sha256=_FORMAL_SHA256,
        schema_version=ingestion.FORMAL_DECISION_SCHEMA,
        review_unit_id=ingestion.EXPECTED_REVIEW_UNIT_ID,
    )


def _validate_rich_6oa_boundary_v1(bound: Mapping[str, object]) -> None:
    """Independently prove rich 6OA facts as projection preconditions only."""

    formal = _mapping(bound.get("formal_document"), "6OA_FORMAL_NOT_OBJECT")
    _expect_fields(
        formal,
        {
            "schema_version": ingestion.FORMAL_DECISION_SCHEMA,
            "record_role": ingestion.FORMAL_RECORD_ROLE,
        },
        "6OA_FORMAL_ROOT_INVALID",
    )
    _expect_fields(
        formal.get("formal_state"),
        {
            "approved": True,
            "unsigned": False,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "human_review_completed": True,
            "formal_decision_created": True,
            "formal_sample_level_authority_created": True,
            "machine_generated_human_authorization": False,
        },
        "6OA_FORMAL_STATE_INVALID",
    )
    _expect_fields(
        formal.get("sample_identity"),
        {
            "PDB": "4OU2",
            "ligand_component_id": "6OA",
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "scope": ingestion.EXPECTED_SCOPE,
            "event_count": 4,
            "canonical_event_ids": list(ingestion.EXPECTED_EVENT_IDS),
            "scaleup_event_ranks": list(ingestion.EXPECTED_RANKS),
            "raw_priority_rank": 29,
            "ligand_wide_authority": False,
            "cross_sample_authority": False,
            "cross_structure_authority": False,
        },
        "6OA_FORMAL_IDENTITY_INVALID",
    )
    external = _expect_fields(
        formal.get("external_human_decision_input"),
        {
            "D1_observed_covalent_chemistry": "POSITIVE",
            "D2_task_generation_domain_relevance": "OUT_OF_DOMAIN",
            "D3_reactive_atom_pair_confirmation_or_revision": "CONFIRM_OBSERVED_PAIR",
            "D3_protein_reactive_atom": "SG",
            "D3_ligand_reactive_atom": "C5",
            "D3_observed_pair": "SG:C5",
            "D4_selected_candidate": ingestion.SELECTED_CANDIDATE,
            "D4_role_profile": ingestion.EXPECTED_ROLE_PROFILE,
            "D4_warhead_atoms": list(ingestion.WARHEAD_ATOMS),
            "D4_linker_atoms": [],
            "D4_scaffold_atoms": list(ingestion.SCAFFOLD_ATOMS),
            "D4_boundary": "C4--C5/SING",
            "D4_minimal_seed": list(ingestion.MINIMAL_SEED),
            "D4_primary_anchor": ingestion.PRIMARY_ANCHOR,
            "D5_applicable_task_ids": [0, 3, 4],
            "D6_later_training_use_disposition": "NOT_APPLICABLE",
        },
        "6OA_D1_D6_EXTERNAL_INPUT_INVALID",
    )
    if external.get("D2_task_generation_domain_relevance") == generic.TASK_NOT_RELEVANT:
        _fail("6OA_SOURCE_OUT_OF_DOMAIN_VALUE_LOST")

    decisions = _mapping(formal.get("formal_decisions"), "6OA_DECISIONS_INVALID")
    d1 = _mapping(decisions.get("D1_observed_covalent_chemistry"), "6OA_D1_INVALID")
    d2 = _mapping(decisions.get("D2_task_generation_domain_relevance"), "6OA_D2_INVALID")
    d3 = _mapping(decisions.get("D3_reactive_atom_pair_confirmation_or_revision"), "6OA_D3_INVALID")
    d4 = _mapping(decisions.get("D4_role_partition_and_minimal_seed"), "6OA_D4_INVALID")
    d5 = _mapping(decisions.get("D5_structural_task_applicability"), "6OA_D5_INVALID")
    d6 = _mapping(decisions.get("D6_later_training_use_disposition"), "6OA_D6_INVALID")
    if (
        d1.get("decision") != generic.CHEMISTRY_POSITIVE
        or d1.get("chemistry_human_authoritative_for_current_sample") is not True
        or d1.get("chemistry_negative") is not False
        or d2.get("decision") != "OUT_OF_DOMAIN"
        or d2.get("chemistry_positive_preserved") is not True
        or d2.get("task_relevance_human_authoritative_for_current_sample") is not True
        or d3.get("decision") != "CONFIRM_OBSERVED_PAIR"
        or d3.get("protein_reactive_atom") != "SG"
        or d3.get("ligand_reactive_atom") != "C5"
        or d3.get("observed_pair") != "SG:C5"
        or d3.get("reactive_pair_sample_authoritative") is not True
        or d3.get("reusable_pair_authority") is not False
        or d4.get("selected_candidate") != ingestion.SELECTED_CANDIDATE
        or d4.get("role_profile") != ingestion.EXPECTED_ROLE_PROFILE
        or d4.get("role_partition_sample_authoritative") is not True
        or d4.get("minimal_seed_sample_authoritative") is not True
        or d4.get("PRE_precursor_role_authority") is not False
        or d4.get("reusable_role_authority") is not False
        or d5.get("applicable_task_ids") != [0, 3, 4]
        or d5.get("task_applicability_sample_authoritative") is not True
        or d5.get("task_label_authority") is not False
        or d5.get("event_task_label_rows_materialized") is not False
        or d5.get("mask_tensor_targets_created") is not False
        or d6.get("decision") != generic.TRAINING_NOT_APPLICABLE
        or d6.get("consistent_with_D2") != "OUT_OF_DOMAIN"
        or d6.get("chemistry_negative") is not False
        or d6.get("formal_training_admitted") is not False
        or d6.get("training_admission_created") is not False
        or d6.get("training_materialization_allowed") is not False
        or d6.get("READY_FOR_TRAINING") is not False
        or d6.get("TRAINING_STARTED") is not False
    ):
        _fail("6OA_D1_D6_BOUNDARY_INVALID")

    role = _expect_fields(
        formal.get("selected_role_context"),
        {
            "candidate_id": ingestion.SELECTED_CANDIDATE,
            "formal_selected": True,
            "human_selected": True,
            "role_profile": ingestion.EXPECTED_ROLE_PROFILE,
            "warhead_atom_ids": list(ingestion.WARHEAD_ATOMS),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(ingestion.SCAFFOLD_ATOMS),
            "boundary": "C4--C5/SING",
            "task_ids": [0, 3, 4],
            "role_partition_sample_authoritative": True,
            "role_profile_sample_authoritative": True,
            "PRE_precursor_authority": False,
            "reusable_warhead_rule_authority": False,
        },
        "6OA_ROLE_BOUNDARY_INVALID",
    )
    _expect_fields(
        role.get("minimal_seed"),
        {
            "atom_ids": ["C3", "C4"],
            "primary_scaffold_side_anchor": "C4",
            "minimal_seed_sample_authoritative": True,
            "reusable_minimal_seed_authority": False,
        },
        "6OA_SEED_BOUNDARY_INVALID",
    )
    _expect_fields(
        role.get("published_runtime"),
        {
            "role_profile": ingestion.EXPECTED_ROLE_PROFILE,
            "role_runtime_valid": True,
            "role_runtime_reasons": [],
            "minimal_seed_runtime_valid": True,
            "minimal_seed_runtime_reasons": [],
            "derived_task_ids": [0, 3, 4],
            "derived_primary_anchor": "C4",
            "direct_boundary": {**ingestion.BOUNDARY, "boundary_valid": True},
            "task_runtime_valid": True,
        },
        "6OA_PUBLISHED_RUNTIME_INVALID",
    )
    exact5 = _expect_fields(
        formal.get("canonical_Exact5"),
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
        },
        "6OA_EXACT5_BOUNDARY_INVALID",
    )
    tasks = _list(exact5.get("tasks"), "6OA_EXACT5_TASKS_INVALID")
    if (
        len(tasks) != 5
        or [row.get("semantic_long_name") for row in tasks if type(row) is dict]
        != [row[1] for row in ingestion.CANONICAL_TASKS]
        or not any(type(row) is dict and row.get("semantic_long_name") == "scaffold_only" and row.get("display_alias") == "B3" for row in tasks)
    ):
        _fail("6OA_EXACT5_LONG_NAMES_OR_B3_INVALID")

    _expect_fields(
        formal.get("training_boundary"),
        {
            "out_of_domain": True,
            "chemistry_negative": False,
            "human_training_use_disposition": generic.TRAINING_NOT_APPLICABLE,
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
        "6OA_TRAINING_BOUNDARY_INVALID",
    )
    _expect_fields(
        formal.get("PRE_boundary"),
        {
            "source_mapping_count_per_event": 0,
            "PRE_source_mapping_status": ingestion.PRE_MAPPING_STATUS,
            "final_PRE_reaction_status": ingestion.PRE_STATUS,
            "PRE_authority": False,
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
            "2VS_substituted_for_6OA_PRE": False,
        },
        "6OA_PRE_BOUNDARY_INVALID",
    )
    geometry = _expect_fields(
        formal.get("geometry_boundary"),
        {
            "representation": "OBSERVED_POST",
            "distances_modified_or_averaged": False,
            "new_bond_order_inferred": False,
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
        },
        "6OA_GEOMETRY_BOUNDARY_INVALID",
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
        for event_id, rank, _protein, _ligand, _connection, exact, _reported, outlier in ingestion.EXPECTED_EVENTS
    ]
    if geometry.get("events") != expected_geometry:
        _fail("6OA_EXACT4_GEOMETRY_INVALID")
    _expect_fields(
        geometry.get("rank857_caveat"),
        {
            "scaleup_event_rank": 857,
            "exact_POST_distance_angstrom": 1.347977,
            "geometry_outlier": True,
            "distance_normalized": False,
            "distance_retained": True,
            "event_removed": False,
            "new_bond_order_inferred": False,
        },
        "6OA_RANK857_CAVEAT_INVALID",
    )
    reusable = _mapping(
        formal.get("reusable_authority_map"), "6OA_REUSABLE_BOUNDARY_INVALID"
    )
    if not reusable or any(value is not False for value in reusable.values()):
        _fail("6OA_REUSABLE_AUTHORITY_FORGED")
    _expect_fields(
        formal.get("readiness"),
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
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "6OA_READINESS_BOUNDARY_INVALID",
    )

    generic_bound = _expect_fields(
        bound.get("generic_Exact11_compatibility"),
        {
            "generic_exact11_compatibility_pass": True,
            "generic_fact_field_count": 11,
            "accepted_fact_count": 4,
            "completed_lane": ingestion.EXPECTED_COMPLETED_LANE,
            "source_formal_generation_domain_decision": "OUT_OF_DOMAIN",
            "normalized_task_relevance_disposition": generic.TASK_NOT_RELEVANT,
            "rich_fields_leaked": False,
            "NormalizedDecisionSource_constructed": True,
            "reconciliation_performed": False,
        },
        "6OA_GENERIC_COMPATIBILITY_BOUNDARY_INVALID",
    )
    compatibility_facts = _list(
        generic_bound.get("facts"), "6OA_GENERIC_COMPATIBILITY_FACTS_INVALID"
    )
    if len(compatibility_facts) != 4 or any(
        type(fact) is not dict or tuple(fact) != _GENERIC_FACT_FIELDS
        for fact in compatibility_facts
    ):
        _fail("6OA_GENERIC_COMPATIBILITY_NOT_EXACT4_EXACT11")
    census = _expect_fields(
        bound.get("current_census_boundary"),
        {
            "census_modified_by_ingestion": False,
            "6OA_event_count": 4,
            "raw_priority_rank": 29,
            "6OA_current_global_status": generic.CURRENTLY_UNREVIEWED,
        },
        "6OA_CURRENT_CENSUS_BOUNDARY_INVALID",
    )
    if not census:
        _fail("6OA_CURRENT_CENSUS_BOUNDARY_INVALID")
    _expected_binding_v1(bound)


def _projection_records_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    _validate_rich_6oa_boundary_v1(bound)
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
    if any(tuple(record) != _GENERIC_FACT_FIELDS for record in records):
        _fail("6OA_GENERIC_PROJECTION_NOT_EXACT11")
    return records


def _validate_projected_6oa_source_v1(
    source: generic.NormalizedDecisionSource,
    records: Sequence[Mapping[str, object]],
) -> None:
    if tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__) != _GENERIC_FACT_FIELDS:
        _fail("GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11")
    if len(source.facts) != 4 or len(records) != 4:
        _fail("6OA_SOURCE_PROJECTION_NOT_EXACT4")
    try:
        generic._validate_source_binding(source.binding)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWith6OAError(
            f"{ERROR_PREFIX}:6OA_GENERIC_SOURCE_BINDING_REJECTED:{error}"
        ) from error
    for fact, record in zip(source.facts, records, strict=True):
        actual = asdict(fact)
        if (
            tuple(fact.__dataclass_fields__) != _GENERIC_FACT_FIELDS
            or actual != dict(record)
            or set(actual) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(actual)
            or fact.legacy_completed_review_status != generic.COMPLETED_HUMAN_NEGATIVE
            or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
            or fact.human_training_excluded is not False
        ):
            _fail("6OA_GENERIC_PROJECTION_CLASSIFICATION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWith6OAError(
                f"{ERROR_PREFIX}:6OA_GENERIC_FACT_REJECTED:{error}"
            ) from error


def _project_bound_6oa_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    records = _projection_records_v1(bound)
    try:
        facts = tuple(
            generic.NormalizedCompletedDecisionFact(**dict(record))
            for record in records
        )
    except TypeError as error:
        raise CompletedDecisionReconciliationWith6OAError(
            f"{ERROR_PREFIX}:6OA_GENERIC_FACT_CONSTRUCTION_FAILED"
        ) from error
    source = generic.NormalizedDecisionSource(
        binding=_expected_binding_v1(bound), facts=facts
    )
    _validate_projected_6oa_source_v1(source, records)
    return source


def project_6oa_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load 6OA through its published API and construct generic Exact11 facts."""

    try:
        bound = ingestion.load_frozen_formal_decision_v1(Path(repo_root).resolve())
    except ingestion.SixOAIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWith6OAError(
            f"{ERROR_PREFIX}:6OA_INGESTION_OWNER_VALIDATION_FAILED:{error}"
        ) from error
    return _project_bound_6oa_v1(bound)


def _validate_source_chain_v1(
    predecessor: Sequence[generic.NormalizedDecisionSource],
    successor: Sequence[generic.NormalizedDecisionSource],
    records: Sequence[Mapping[str, object]],
) -> None:
    before, after = tuple(predecessor), tuple(successor)
    before_facts = tuple(fact for source in before for fact in source.facts)
    after_facts = tuple(fact for source in after for fact in source.facts)
    if len(before) != 25 or len(before_facts) != 143:
        _fail("PREDECESSOR_WITH_NWJ_SOURCE_CHAIN_NOT_EXACT25_143")
    if len(after) != 26 or after[:-1] != before or len(after_facts) != 147:
        _fail("6OA_SOURCE_CHAIN_NOT_PREFIX_APPEND_EXACT26_147")
    _validate_projected_6oa_source_v1(after[-1], records)
    if after_facts[:143] != before_facts or after_facts[143:] != after[-1].facts:
        _fail("6OA_FACT_CHAIN_NOT_PREFIX_APPEND_EXACT143_PLUS4")
    before_events = [fact.canonical_event_id for fact in before_facts]
    after_events = [fact.canonical_event_id for fact in after_facts]
    if (
        any(event in set(before_events) for event in ingestion.EXPECTED_EVENT_IDS)
        or after_events[-4:] != list(ingestion.EXPECTED_EVENT_IDS)
        or len(set(before_events)) != 143
        or len(set(after_events)) != 147
    ):
        _fail("6OA_EVENT_PREFIX_OR_UNIQUENESS_INVALID")
    before_units = {source.binding.review_unit_id for source in before}
    before_ids = {source.binding.stable_identity for source in before}
    if (
        len(before_units) != 25
        or len(before_ids) != 25
        or len({source.binding.review_unit_id for source in after}) != 26
        or len({source.binding.stable_identity for source in after}) != 26
        or after[-1].binding.review_unit_id in before_units
        or after[-1].binding.stable_identity in before_ids
        or any(source.binding.path_namespace != "repository_parent_relative" for source in after)
    ):
        _fail("6OA_SOURCE_IDENTITY_NAMESPACE_OR_DUPLICATE_INVALID")


def load_real_completed_decision_sources_with_6oa_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    root = Path(repo_root).resolve()
    before = predecessor_owner.load_real_completed_decision_sources_with_nwj_v1(root)
    try:
        bound = ingestion.load_frozen_formal_decision_v1(root)
    except ingestion.SixOAIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWith6OAError(
            f"{ERROR_PREFIX}:6OA_INGESTION_OWNER_VALIDATION_FAILED:{error}"
        ) from error
    records = _projection_records_v1(bound)
    after = (*before, _project_bound_6oa_v1(bound))
    _validate_source_chain_v1(before, after, records)
    return after


def _prove_6oa_predecessor_historical_state_v1(
    rows: Sequence[Mapping[str, str]],
) -> None:
    targets = [
        row for row in rows if row.get("canonical_event_id") in ingestion.EXPECTED_EVENT_IDS
    ]
    if (
        len(rows) != 338
        or len(targets) != 4
        or tuple(row["canonical_event_id"] for row in targets) != ingestion.EXPECTED_EVENT_IDS
        or any(
            row.get("raw_review_unit_id") != ingestion.EXPECTED_REVIEW_UNIT_ID
            or row.get("raw_priority_rank") != _HISTORICAL_PRIORITY_RANK
            or row.get("raw_unit_event_count") != "4"
            or row.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
            or row.get("calibration_eligible") != "true"
            or row.get("calibration_exclusion_reason") != ""
            for row in targets
        )
    ):
        _fail("6OA_PREDECESSOR_HISTORICAL_STATE_INVALID")


def _validate_reconciliation_delta_v1(
    before: generic.ReconciliationResult,
    after: generic.ReconciliationResult,
) -> None:
    if before.review_summary != _PREDECESSOR_REVIEW_SUMMARY:
        _fail("PREDECESSOR_WITH_NWJ_REVIEW_SUMMARY_INVALID")
    if after.review_summary != _SUCCESSOR_REVIEW_SUMMARY:
        _fail("6OA_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if len(before.normalized_facts) != 143 or len(after.normalized_facts) != 147:
        _fail("6OA_RECONCILIATION_FACT_COUNT_INVALID")
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
            != generic._canonical_json([ingestion.FORMAL_DECISION_RELATIVE.as_posix()])
            or old["calibration_eligible"] != "true"
            or new["calibration_eligible"] != "false"
            or old["calibration_exclusion_reason"] != ""
            or new["calibration_exclusion_reason"] != generic.COMPLETED_HUMAN_NEGATIVE
        ):
            _fail("6OA_TARGET_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (4, 0):
        _fail("6OA_RECONCILIATION_DELTA_NOT_EXACT4_AND_334")


def _build_components_v1(
    repo_root: Path,
) -> tuple[
    tuple[generic.NormalizedDecisionSource, ...],
    tuple[generic.NormalizedDecisionSource, ...],
    generic.ReconciliationResult,
    generic.ReconciliationResult,
]:
    root = Path(repo_root).resolve()
    before_sources = predecessor_owner.load_real_completed_decision_sources_with_nwj_v1(root)
    adapted = historical_adapter_owner._adapt_historical_v1(root)
    _prove_6oa_predecessor_historical_state_v1(adapted)
    reproduced_before = generic.reconcile_completed_human_decisions_v1(adapted, before_sources)
    published_before = predecessor_owner.reconcile_real_completed_human_decisions_with_nwj_v1(root)
    if reproduced_before != published_before:
        _fail("PREDECESSOR_WITH_NWJ_RESULT_NOT_REPRODUCED_FROM_ADAPTED_BASE")
    _prove_6oa_predecessor_historical_state_v1(reproduced_before.reconciled_rows)
    try:
        bound = ingestion.load_frozen_formal_decision_v1(root)
    except ingestion.SixOAIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWith6OAError(
            f"{ERROR_PREFIX}:6OA_INGESTION_OWNER_VALIDATION_FAILED:{error}"
        ) from error
    records = _projection_records_v1(bound)
    after_sources = (*before_sources, _project_bound_6oa_v1(bound))
    _validate_source_chain_v1(before_sources, after_sources, records)
    after_result = generic.reconcile_completed_human_decisions_v1(adapted, after_sources)
    _validate_reconciliation_delta_v1(reproduced_before, after_result)
    return before_sources, after_sources, reproduced_before, after_result


def reconcile_real_completed_human_decisions_with_6oa_v1(
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
        "normalized_facts": [asdict(fact) for source in sources for fact in source.facts],
        "review_summary": dict(reconciliation.review_summary),
    }


def _validate_artifact_mapping_v1(
    value: object,
    *,
    predecessor_sources: Sequence[generic.NormalizedDecisionSource],
    successor_sources: Sequence[generic.NormalizedDecisionSource],
    reconciliation: generic.ReconciliationResult,
) -> None:
    artifact = _mapping(value, "6OA_ARTIFACT_NOT_OBJECT")
    bindings = _list(artifact.get("source_bindings"), "6OA_BINDINGS_NOT_LIST")
    facts = _list(artifact.get("normalized_facts"), "6OA_FACTS_NOT_LIST")
    rows = _list(artifact.get("reconciled_rows"), "6OA_ROWS_NOT_LIST")
    predecessor_facts = [
        asdict(fact) for source in predecessor_sources for fact in source.facts
    ]
    if (
        tuple(artifact) != _ARTIFACT_FIELDS
        or len(bindings) != 26
        or len(facts) != 147
        or len(rows) != 338
        or bindings != [asdict(source.binding) for source in successor_sources]
        or any(type(item) is not dict or set(item) != set(_SOURCE_BINDING_FIELDS) for item in bindings)
        or facts != [asdict(fact) for source in successor_sources for fact in source.facts]
        or facts[:143] != predecessor_facts
        or facts[143:] != [asdict(fact) for fact in successor_sources[-1].facts]
        or any(
            type(item) is not dict
            or set(item) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(item)
            for item in facts
        )
        or rows != [dict(row) for row in reconciliation.reconciled_rows]
        or artifact.get("review_summary") != reconciliation.review_summary
    ):
        _fail("6OA_ARTIFACT_CONTENT_OR_PREFIX_INVALID")


def build_artifact_v1(repo_root: Path) -> bytes:
    """Build the sole deterministic reconciliation JSON without writing it."""

    before_sources, after_sources, _before_result, after_result = _build_components_v1(repo_root)
    mapping = _artifact_mapping_v1(after_sources, after_result)
    _validate_artifact_mapping_v1(
        mapping,
        predecessor_sources=before_sources,
        successor_sources=after_sources,
        reconciliation=after_result,
    )
    return (json.dumps(mapping, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _validate_destination_v1(repo_root: Path, destination: Path) -> None:
    if destination.resolve() != (repo_root / OUTPUT_RELATIVE).resolve():
        _fail("6OA_ARTIFACT_DESTINATION_NOT_EXACT")
    parent = destination.parent
    if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
        _fail("6OA_ARTIFACT_PARENT_NOT_REAL_DIRECTORY")
    if parent.exists() and {item.name for item in parent.iterdir()} - {OUTPUT_NAME}:
        _fail("6OA_ARTIFACT_DIRECTORY_CONTAINS_EXTRA_FILE")


def materialize_artifact_v1(repo_root: Path) -> bytes:
    """Atomically write only the authorized reconciliation JSON."""

    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = build_artifact_v1(root)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".covapie_6oa_reconciliation_", dir=destination.parent
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
    """Rebuild twice and compare the one materialized artifact byte for byte."""

    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    try:
        metadata, observed = destination.lstat(), destination.read_bytes()
    except OSError as error:
        raise CompletedDecisionReconciliationWith6OAError(
            f"{ERROR_PREFIX}:6OA_MATERIALIZED_ARTIFACT_READ_FAILED"
        ) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o111:
        _fail("6OA_MATERIALIZED_ARTIFACT_SECURITY_INVALID")
    first = build_artifact_v1(root)
    second = build_artifact_v1(root)
    if observed != first or first != second:
        _fail("6OA_MATERIALIZED_ARTIFACT_BYTES_MISMATCH")
    return {
        "status": "PASS",
        "artifact_count": 1,
        "source_count": 26,
        "accepted_fact_count": 147,
        "byte_identical_to_rebuild": True,
        "training_authority": False,
        "ready_for_training": False,
    }
