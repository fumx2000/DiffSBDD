"""Append the published PYR Exact4 to completed-decision reconciliation.

The PYR ingestion owner remains the owner of the rich approved decision.  This
metadata-only successor checks the projection boundary, converts the formal
binding to the generic repository-parent namespace, appends one source to the
published with-6OA chain, and calls the unchanged generic reconciler over the
published historical adapter.  It does not refresh census/queue state, create
task labels or tensors, admit training, update parameters, or train.
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

from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import covapie_completed_human_decision_reconciliation_with_6oa_v1 as predecessor_owner
from . import covapie_completed_human_decision_reconciliation_with_tp2_v1 as historical_adapter_owner
from . import covapie_pyr_completed_decision_ingestion_and_task_label_availability_v1 as ingestion


__all__ = (
    "CompletedDecisionReconciliationWithPYRError",
    "project_pyr_completed_decision_v1",
    "load_real_completed_decision_sources_with_pyr_v1",
    "reconcile_real_completed_human_decisions_with_pyr_v1",
    "build_artifact_v1",
    "materialize_artifact_v1",
    "check_materialized_v1",
)

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_pyr_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_completed_human_decision_reconciliation_with_pyr_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_completed_human_decision_reconciliation_with_pyr_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_completed_human_decision_reconciliation_with_pyr_v1"
)
OUTPUT_NAME = "covapie_completed_human_decision_reconciliation_with_pyr_v1.json"
OUTPUT_RELATIVE = OUTPUT_ROOT_RELATIVE / OUTPUT_NAME
EXACT4_PATHS = (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE, OUTPUT_RELATIVE)

ERROR_PREFIX = "COVAPIE_PYR_RECONCILIATION_V1_ERROR"
_HISTORICAL_PRIORITY_RANK = "30"
_FORMAL_BYTES = 17975
_FORMAL_SHA256 = "58736b2b9dda6078e2e57495d698af110b13f42eec6668cbdb358820dfb66e2d"
_FORMAL_VALIDATOR_BYTES = 75613
_FORMAL_VALIDATOR_SHA256 = (
    "003a1e6f85616bc8d5f255bd2333f0b61ee0144afaed32a3e7ba64114cdc543c"
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
_SUCCESSOR_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 127,
    "completed_positive_unit_count": 21,
    "completed_negative_event_count": 48,
    "completed_negative_unit_count": 10,
    "completed_total_event_count": 175,
    "completed_total_unit_count": 31,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 163,
    "unreviewed_unit_count": 100,
}
PREDECESSOR_COVERAGE_SUMMARY = {
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
SUCCESSOR_COVERAGE_SUMMARY = {
    "accepted_fact_count": 151,
    "accepted_review_unit_count": 27,
    "stable_source_identity_count": 27,
    "remaining_unreviewed_chemistry_event_count": 187,
    "remaining_unreviewed_review_unit_upper_bound": 104,
    "decision_category_distribution": {
        "chemistry_positive": 103,
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
        "protein_reactive_atom",
        "ligand_reactive_atom",
        "reactive_pair",
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


class CompletedDecisionReconciliationWithPYRError(ValueError):
    """Raised when the exact additive PYR contract cannot be proven."""


def _fail(token: str) -> NoReturn:
    raise CompletedDecisionReconciliationWithPYRError(f"{ERROR_PREFIX}:{token}")


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
        bound.get("formal_decision_binding"), "PYR_FORMAL_BINDING_NOT_OBJECT"
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
        "source_role": "PYR_FROZEN_FORMAL_HUMAN_DECISION",
        "validation_method": "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
    }:
        _fail("PYR_FORMAL_SOURCE_BINDING_INVALID")
    validator_path = ingestion.FORMAL_VALIDATOR_RELATIVE.as_posix()
    validator = _mapping(
        bound.get("formal_validator_binding"), "PYR_VALIDATOR_BINDING_NOT_OBJECT"
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
        "source_role": "PYR_FROZEN_FORMAL_VALIDATOR",
        "validation_method": (
            "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED"
        ),
    }:
        _fail("PYR_FORMAL_VALIDATOR_PROVENANCE_BOUNDARY_INVALID")
    return generic.SourceBinding(
        source_path=path,
        path_namespace="repository_parent_relative",
        byte_count=_FORMAL_BYTES,
        sha256=_FORMAL_SHA256,
        schema_version=ingestion.FORMAL_DECISION_SCHEMA,
        review_unit_id=ingestion.EXPECTED_REVIEW_UNIT_ID,
    )


def _validate_rich_pyr_boundary_v1(bound: Mapping[str, object]) -> None:
    """Check only approved projection inputs and non-authority boundaries."""

    formal = _mapping(bound.get("formal_document"), "PYR_FORMAL_NOT_OBJECT")
    _expect_fields(
        formal,
        {
            "schema_version": ingestion.FORMAL_DECISION_SCHEMA,
            "record_role": ingestion.FORMAL_RECORD_ROLE,
        },
        "PYR_FORMAL_ROOT_INVALID",
    )
    _expect_fields(
        formal.get("sample_identity"),
        {
            "PDB": "1F8M",
            "ligand_component_id": "PYR",
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "scope": ingestion.EXPECTED_SCOPE,
            "event_count": 4,
            "canonical_event_ids": list(ingestion.EXPECTED_EVENT_IDS),
            "scaleup_event_ranks": list(ingestion.EXPECTED_RANKS),
            "ligand_wide_authority": False,
            "cross_structure_authority": False,
        },
        "PYR_FORMAL_IDENTITY_INVALID",
    )
    _expect_fields(
        formal.get("sample_level_authority"),
        {
            "approved": True,
            "human_review_completed": True,
            "human_decision_created": True,
            "formal_decision_created": True,
            "formal_sample_level_authority_created": True,
            "human_selected": True,
            "sample_chemistry_authority": True,
            "sample_task_relevance_authority": True,
            "sample_training_use_decision_authority": True,
            "unsigned": False,
        },
        "PYR_APPROVAL_STATE_INVALID",
    )
    decisions = _mapping(formal.get("approved_D1_D6"), "PYR_D1_D6_NOT_OBJECT")
    d1 = _mapping(decisions.get("D1_observed_covalent_chemistry"), "PYR_D1_INVALID")
    d2 = _mapping(decisions.get("D2_task_generation_domain_relevance"), "PYR_D2_INVALID")
    d3 = _mapping(decisions.get("D3_reactive_atom_pair"), "PYR_D3_INVALID")
    d4 = _mapping(decisions.get("D4_role_partition_and_minimal_seed"), "PYR_D4_INVALID")
    d5 = _mapping(decisions.get("D5_structural_task_applicability"), "PYR_D5_INVALID")
    d6 = _mapping(decisions.get("D6_later_training_use_disposition"), "PYR_D6_INVALID")
    if (
        d1 != {"decision": "POSITIVE", "human_approved": True}
        or d2 != {"decision": "IN_DOMAIN", "human_approved": True}
        or d3
        != {
            "component_atom": "CB",
            "decision": "CONFIRM_OBSERVED_PAIR",
            "human_approved": True,
            "pair": "SG:CB",
            "protein_atom": "SG",
        }
        or d4
        != {
            "decision": "PROVIDE_ROLE_PARTITION",
            "human_approved": True,
            "selected_candidate_id": ingestion.SELECTED_CANDIDATE,
        }
        or d5
        != {
            "decision": "PROVIDE_APPLICABLE_TASK_IDS",
            "human_approved": True,
            "selected_task_ids": [0, 3, 4],
        }
        or d6.get("decision") != "EXCLUDE"
        or d6.get("human_approved") is not True
        or d6.get("human_training_excluded") is not True
        or d6.get("D6_is_chemistry_negative") is not False
        or d6.get("D6_is_out_of_domain") is not False
        or d6.get("D6_is_formal_training_admission") is not False
        or d6.get("formal_training_admitted") is not False
        or d6.get("future_training_admission_candidate") is not False
    ):
        _fail("PYR_D1_D6_BOUNDARY_INVALID")

    non_created = _mapping(
        formal.get("non_created_authority"), "PYR_NON_CREATED_AUTHORITY_INVALID"
    )
    required_false = {
        "task_label_authority",
        "event_task_label_rows_materialized",
        "mask_tensor_targets_created",
        "formal_training_admitted",
        "training_admission_created",
        "training_materialization_allowed",
        "parameter_update_authorization",
        "reusable_authority_created",
        "PRE_authority",
        "POST_geometry_training_authority",
    }
    if any(non_created.get(key) is not False for key in required_false):
        _fail("PYR_NON_CREATED_AUTHORITY_INVALID")
    readiness = _expect_fields(
        formal.get("readiness"),
        {
            "AUTHORIZATION_COMPLETE": True,
            "HUMAN_REVIEW_COMPLETED": True,
            "FORMAL_TRAINING_ADMITTED": False,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
            "STEP12D_STATUS": (
                "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT"
            ),
        },
        "PYR_READINESS_BOUNDARY_INVALID",
    )
    if not readiness:
        _fail("PYR_READINESS_BOUNDARY_INVALID")
    operations = _expect_fields(
        formal.get("operation_boundary"),
        {
            "census_performed": False,
            "reconciliation_performed": False,
            "task_label_materialization_performed": False,
            "mask_tensor_materialization_performed": False,
            "training_preparation_performed": False,
            "parameter_update_performed": False,
            "network_acquisition_performed": False,
            "commit_performed": False,
            "push_performed": False,
        },
        "PYR_OPERATION_BOUNDARY_INVALID",
    )
    if not operations:
        _fail("PYR_OPERATION_BOUNDARY_INVALID")

    task_selection = _mapping(
        formal.get("selected_task_ids"), "PYR_TASK_SELECTION_INVALID"
    )
    exact5 = _expect_fields(
        task_selection.get("canonical_V1_contract"),
        {
            "task_count": 5,
            "B3_present": True,
            "sixth_task": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
        },
        "PYR_EXACT5_BOUNDARY_INVALID",
    )
    tasks = _list(exact5.get("tasks"), "PYR_EXACT5_TASKS_INVALID")
    if (
        task_selection.get("selected_task_ids") != [0, 3, 4]
        or task_selection.get("task_label_authority") is not False
        or len(tasks) != 5
        or [row.get("semantic_long_name") for row in tasks if type(row) is dict]
        != [row[1] for row in ingestion.CANONICAL_TASKS]
        or not any(
            type(row) is dict
            and row.get("semantic_long_name") == "scaffold_only"
            and row.get("display_alias") == "B3"
            for row in tasks
        )
    ):
        _fail("PYR_EXACT5_BOUNDARY_INVALID")

    compatibility = _expect_fields(
        bound.get("generic_Exact11_compatibility"),
        {
            "generic_exact11_compatibility_pass": True,
            "generic_fact_field_count": 11,
            "accepted_fact_count": 4,
            "source_formal_generation_domain_decision": "IN_DOMAIN",
            "normalized_task_relevance_disposition": generic.TASK_RELEVANT,
            "source_formal_training_use_decision": "EXCLUDE",
            "normalized_training_disposition": generic.TRAINING_EXCLUDE,
            "rich_fields_leaked": False,
            "NormalizedDecisionSource_constructed": True,
            "reconciliation_performed": False,
        },
        "PYR_GENERIC_COMPATIBILITY_BOUNDARY_INVALID",
    )
    facts = _list(compatibility.get("facts"), "PYR_GENERIC_FACTS_INVALID")
    if len(facts) != 4 or any(
        type(fact) is not dict or tuple(fact) != _GENERIC_FACT_FIELDS
        for fact in facts
    ):
        _fail("PYR_GENERIC_COMPATIBILITY_NOT_EXACT4_EXACT11")
    _expect_fields(
        bound.get("current_census_boundary"),
        {
            "census_modified_by_ingestion": False,
            "PYR_event_count": 4,
            "PYR_current_global_status": generic.CURRENTLY_UNREVIEWED,
            "PYR_current_review_status": generic.CURRENTLY_UNREVIEWED,
            "PYR_human_review_completed": False,
            "raw_priority_rank": 30,
        },
        "PYR_CURRENT_CENSUS_BOUNDARY_INVALID",
    )
    _expected_binding_v1(bound)


def _projection_records_v1(
    bound: Mapping[str, object],
) -> tuple[Mapping[str, Any], ...]:
    _validate_rich_pyr_boundary_v1(bound)
    binding = _expected_binding_v1(bound)
    records = tuple(
        {
            "canonical_event_id": event_id,
            "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
            "human_review_completed": True,
            "legacy_completed_review_status": generic.COMPLETED_HUMAN_POSITIVE,
            "task_relevance_disposition": generic.TASK_RELEVANT,
            "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_EXCLUDE,
            "human_training_excluded": True,
            "source_decision_schema": ingestion.FORMAL_DECISION_SCHEMA,
            "source_decision_sha256": binding.sha256,
            "source_binding_path": binding.source_path,
        }
        for event_id in ingestion.EXPECTED_EVENT_IDS
    )
    if any(tuple(record) != _GENERIC_FACT_FIELDS for record in records):
        _fail("PYR_GENERIC_PROJECTION_NOT_EXACT11")
    return records


def _validate_projected_pyr_source_v1(
    source: generic.NormalizedDecisionSource,
    records: Sequence[Mapping[str, object]],
) -> None:
    if (
        tuple(generic.NormalizedCompletedDecisionFact.__dataclass_fields__)
        != _GENERIC_FACT_FIELDS
    ):
        _fail("GENERIC_NORMALIZED_FACT_SCHEMA_NOT_EXACT11")
    if len(source.facts) != 4 or len(records) != 4:
        _fail("PYR_SOURCE_PROJECTION_NOT_EXACT4")
    try:
        generic._validate_source_binding(source.binding)
    except generic.CompletedDecisionReconciliationError as error:
        raise CompletedDecisionReconciliationWithPYRError(
            f"{ERROR_PREFIX}:PYR_GENERIC_SOURCE_BINDING_REJECTED:{error}"
        ) from error
    for fact, record in zip(source.facts, records, strict=True):
        actual = asdict(fact)
        if (
            tuple(fact.__dataclass_fields__) != _GENERIC_FACT_FIELDS
            or actual != dict(record)
            or set(actual) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(actual)
            or fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_EXCLUDE
            or fact.human_training_excluded is not True
        ):
            _fail("PYR_GENERIC_PROJECTION_CLASSIFICATION_INVALID")
        try:
            generic._validate_fact(fact, source.binding)
        except generic.CompletedDecisionReconciliationError as error:
            raise CompletedDecisionReconciliationWithPYRError(
                f"{ERROR_PREFIX}:PYR_GENERIC_FACT_REJECTED:{error}"
            ) from error


def _project_bound_pyr_v1(
    bound: Mapping[str, object],
) -> generic.NormalizedDecisionSource:
    records = _projection_records_v1(bound)
    try:
        facts = tuple(
            generic.NormalizedCompletedDecisionFact(**dict(record))
            for record in records
        )
    except TypeError as error:
        raise CompletedDecisionReconciliationWithPYRError(
            f"{ERROR_PREFIX}:PYR_GENERIC_FACT_CONSTRUCTION_FAILED"
        ) from error
    source = generic.NormalizedDecisionSource(
        binding=_expected_binding_v1(bound), facts=facts
    )
    _validate_projected_pyr_source_v1(source, records)
    return source


def _load_bound_v1(repo_root: Path) -> Mapping[str, object]:
    try:
        return ingestion.load_frozen_formal_decision_v1(Path(repo_root).resolve())
    except ingestion.PYRIngestionSafetyError as error:
        raise CompletedDecisionReconciliationWithPYRError(
            f"{ERROR_PREFIX}:PYR_INGESTION_OWNER_VALIDATION_FAILED:{error}"
        ) from error


def project_pyr_completed_decision_v1(
    *, repo_root: Path
) -> generic.NormalizedDecisionSource:
    """Load PYR through its published no-write API and emit Exact11 facts."""

    return _project_bound_pyr_v1(_load_bound_v1(repo_root))


def _validate_source_chain_v1(
    predecessor: Sequence[generic.NormalizedDecisionSource],
    successor: Sequence[generic.NormalizedDecisionSource],
    records: Sequence[Mapping[str, object]],
) -> None:
    before, after = tuple(predecessor), tuple(successor)
    before_facts = tuple(fact for source in before for fact in source.facts)
    after_facts = tuple(fact for source in after for fact in source.facts)
    if len(before) != 26 or len(before_facts) != 147:
        _fail("PREDECESSOR_WITH_6OA_SOURCE_CHAIN_NOT_EXACT26_147")
    if len(after) != 27 or after[:-1] != before or len(after_facts) != 151:
        _fail("PYR_SOURCE_CHAIN_NOT_PREFIX_APPEND_EXACT27_151")
    _validate_projected_pyr_source_v1(after[-1], records)
    if after_facts[:147] != before_facts or after_facts[147:] != after[-1].facts:
        _fail("PYR_FACT_CHAIN_NOT_PREFIX_APPEND_EXACT147_PLUS4")
    before_events = [fact.canonical_event_id for fact in before_facts]
    after_events = [fact.canonical_event_id for fact in after_facts]
    if (
        any(event in set(before_events) for event in ingestion.EXPECTED_EVENT_IDS)
        or after_events[-4:] != list(ingestion.EXPECTED_EVENT_IDS)
        or len(set(before_events)) != 147
        or len(set(after_events)) != 151
    ):
        _fail("PYR_EVENT_PREFIX_OR_UNIQUENESS_INVALID")
    before_units = {source.binding.review_unit_id for source in before}
    before_ids = {source.binding.stable_identity for source in before}
    if (
        len(before_units) != 26
        or len(before_ids) != 26
        or len({source.binding.review_unit_id for source in after}) != 27
        or len({source.binding.stable_identity for source in after}) != 27
        or after[-1].binding.review_unit_id in before_units
        or after[-1].binding.stable_identity in before_ids
        or any(
            source.binding.path_namespace != "repository_parent_relative"
            for source in after
        )
    ):
        _fail("PYR_SOURCE_IDENTITY_NAMESPACE_OR_DUPLICATE_INVALID")


def load_real_completed_decision_sources_with_pyr_v1(
    repo_root: Path,
) -> tuple[generic.NormalizedDecisionSource, ...]:
    root = Path(repo_root).resolve()
    before = predecessor_owner.load_real_completed_decision_sources_with_6oa_v1(root)
    bound = _load_bound_v1(root)
    records = _projection_records_v1(bound)
    after = (*before, _project_bound_pyr_v1(bound))
    _validate_source_chain_v1(before, after, records)
    return after


def _prove_pyr_predecessor_historical_state_v1(
    rows: Sequence[Mapping[str, str]],
) -> None:
    targets = [
        row
        for row in rows
        if row.get("canonical_event_id") in ingestion.EXPECTED_EVENT_IDS
    ]
    if (
        len(rows) != 338
        or len(targets) != 4
        or tuple(row["canonical_event_id"] for row in targets)
        != ingestion.EXPECTED_EVENT_IDS
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
        _fail("PYR_PREDECESSOR_HISTORICAL_STATE_INVALID")


def _validate_reconciliation_delta_v1(
    before: generic.ReconciliationResult,
    after: generic.ReconciliationResult,
) -> None:
    if before.review_summary != _PREDECESSOR_REVIEW_SUMMARY:
        _fail("PREDECESSOR_WITH_6OA_REVIEW_SUMMARY_INVALID")
    if after.review_summary != _SUCCESSOR_REVIEW_SUMMARY:
        _fail("PYR_RECONCILIATION_REVIEW_SUMMARY_INVALID")
    if len(before.normalized_facts) != 147 or len(after.normalized_facts) != 151:
        _fail("PYR_RECONCILIATION_FACT_COUNT_INVALID")
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
            or new["current_review_status"]
            != generic.COMPLETED_HUMAN_POSITIVE
            or new["current_status_authority_sources_json"]
            != generic._canonical_json(
                [ingestion.FORMAL_DECISION_RELATIVE.as_posix()]
            )
            or old["calibration_eligible"] != "true"
            or new["calibration_eligible"] != "false"
            or old["calibration_exclusion_reason"] != ""
            or new["calibration_exclusion_reason"]
            != generic.COMPLETED_HUMAN_POSITIVE
        ):
            _fail("PYR_TARGET_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (4, 0):
        _fail("PYR_RECONCILIATION_DELTA_NOT_EXACT4_AND_334")


def _validate_coverage_contract_v1(
    before_sources: Sequence[generic.NormalizedDecisionSource],
    after_sources: Sequence[generic.NormalizedDecisionSource],
) -> None:
    if (
        PREDECESSOR_COVERAGE_SUMMARY
        != predecessor_owner.SUCCESSOR_COVERAGE_SUMMARY
    ):
        _fail("PREDECESSOR_WITH_6OA_COVERAGE_DRIFT")
    before_facts = [fact for source in before_sources for fact in source.facts]
    after_facts = [fact for source in after_sources for fact in source.facts]
    if (
        len(before_facts) != PREDECESSOR_COVERAGE_SUMMARY["accepted_fact_count"]
        or len(after_facts) != SUCCESSOR_COVERAGE_SUMMARY["accepted_fact_count"]
        or after_facts[:147] != before_facts
        or after_facts[147:] != list(after_sources[-1].facts)
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
        or any(
            fact.legacy_completed_review_status
            != generic.COMPLETED_HUMAN_POSITIVE
            or fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_EXCLUDE
            or fact.human_training_excluded is not True
            for fact in after_facts[147:]
        )
        or SUCCESSOR_COVERAGE_SUMMARY["decision_category_distribution"][
            "chemistry_positive"
        ]
        - PREDECESSOR_COVERAGE_SUMMARY["decision_category_distribution"][
            "chemistry_positive"
        ]
        != 4
        or any(
            SUCCESSOR_COVERAGE_SUMMARY["decision_category_distribution"][key]
            != PREDECESSOR_COVERAGE_SUMMARY["decision_category_distribution"][key]
            for key in (
                "chemistry_negative",
                "task_domain_negative",
                "task_domain_positive",
            )
        )
        or SUCCESSOR_COVERAGE_SUMMARY["label_ready_event_count"] != 16
        or SUCCESSOR_COVERAGE_SUMMARY["training_mask_target_count"] != 0
        or SUCCESSOR_COVERAGE_SUMMARY["training_authority"] is not False
    ):
        _fail("PYR_COVERAGE_DELTA_INVALID")


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
        predecessor_owner.load_real_completed_decision_sources_with_6oa_v1(root)
    )
    adapted = historical_adapter_owner._adapt_historical_v1(root)
    _prove_pyr_predecessor_historical_state_v1(adapted)
    reproduced_before = generic.reconcile_completed_human_decisions_v1(
        adapted, before_sources
    )
    published_before = (
        predecessor_owner.reconcile_real_completed_human_decisions_with_6oa_v1(root)
    )
    if reproduced_before != published_before:
        _fail("PREDECESSOR_WITH_6OA_RESULT_NOT_REPRODUCED_FROM_ADAPTED_BASE")
    _prove_pyr_predecessor_historical_state_v1(reproduced_before.reconciled_rows)
    bound = _load_bound_v1(root)
    records = _projection_records_v1(bound)
    after_sources = (*before_sources, _project_bound_pyr_v1(bound))
    _validate_source_chain_v1(before_sources, after_sources, records)
    _validate_coverage_contract_v1(before_sources, after_sources)
    after_result = generic.reconcile_completed_human_decisions_v1(
        adapted, after_sources
    )
    _validate_reconciliation_delta_v1(reproduced_before, after_result)
    return before_sources, after_sources, reproduced_before, after_result


def reconcile_real_completed_human_decisions_with_pyr_v1(
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
    artifact = _mapping(value, "PYR_ARTIFACT_NOT_OBJECT")
    bindings = _list(artifact.get("source_bindings"), "PYR_BINDINGS_NOT_LIST")
    facts = _list(artifact.get("normalized_facts"), "PYR_FACTS_NOT_LIST")
    rows = _list(artifact.get("reconciled_rows"), "PYR_ROWS_NOT_LIST")
    predecessor_facts = [
        asdict(fact) for source in predecessor_sources for fact in source.facts
    ]
    if (
        tuple(artifact) != _ARTIFACT_FIELDS
        or len(bindings) != 27
        or len(facts) != 151
        or len(rows) != 338
        or bindings != [asdict(source.binding) for source in successor_sources]
        or any(
            type(item) is not dict or set(item) != set(_SOURCE_BINDING_FIELDS)
            for item in bindings
        )
        or facts
        != [asdict(fact) for source in successor_sources for fact in source.facts]
        or facts[:147] != predecessor_facts
        or facts[147:]
        != [asdict(fact) for fact in successor_sources[-1].facts]
        or any(
            type(item) is not dict
            or set(item) != set(_GENERIC_FACT_FIELDS)
            or _FORBIDDEN_RICH_FACT_FIELDS & set(item)
            for item in facts
        )
        or rows != [dict(row) for row in reconciliation.reconciled_rows]
        or artifact.get("review_summary") != reconciliation.review_summary
    ):
        _fail("PYR_ARTIFACT_CONTENT_OR_PREFIX_INVALID")


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
        _fail("PYR_ARTIFACT_DESTINATION_NOT_EXACT")
    parent = destination.parent
    if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
        _fail("PYR_ARTIFACT_PARENT_NOT_REAL_DIRECTORY")
    if parent.exists() and {item.name for item in parent.iterdir()} - {OUTPUT_NAME}:
        _fail("PYR_ARTIFACT_DIRECTORY_CONTAINS_EXTRA_FILE")


def materialize_artifact_v1(repo_root: Path) -> bytes:
    """Atomically write only the authorized reconciliation JSON."""

    root = Path(repo_root).resolve()
    destination = root / OUTPUT_RELATIVE
    _validate_destination_v1(root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = build_artifact_v1(root)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".covapie_pyr_reconciliation_", dir=destination.parent
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
        raise CompletedDecisionReconciliationWithPYRError(
            f"{ERROR_PREFIX}:PYR_MATERIALIZED_ARTIFACT_READ_FAILED"
        ) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_mode & 0o111
    ):
        _fail("PYR_MATERIALIZED_ARTIFACT_SECURITY_INVALID")
    first = build_artifact_v1(root)
    second = build_artifact_v1(root)
    if observed != first or first != second:
        _fail("PYR_MATERIALIZED_ARTIFACT_BYTES_MISMATCH")
    return {
        "status": "PASS",
        "artifact_count": 1,
        "source_count": 27,
        "accepted_fact_count": 151,
        "byte_identical_to_rebuild": True,
        "training_authority": False,
        "ready_for_training": False,
    }
