"""Additive cumulative1000 readiness census refresh for published SR2 Exact4.

This successor consumes the frozen with-GD1 census plus already-published SR2
ingestion and reconciliation authority. It deep-copies the predecessor rows and
overlays only the four frozen SR2 event IDs. It creates no new scientific,
training-admission, tensor, model, or training authority.
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

from . import covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1 as sr2_ingestion
from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import covapie_completed_human_decision_reconciliation_with_sr2_v1 as sr2_reconciliation
from . import covapie_cumulative1000_current_global_readiness_census_with_gd1_v1 as predecessor
from .covapie_source_binding_policy_v2 import (
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


__all__ = (
    "Cumulative1000CurrentGlobalReadinessCensusWithSR2Error",
    "compute_covapie_cumulative1000_current_global_readiness_census_with_sr2_v1",
    "validate_covapie_cumulative1000_current_global_readiness_census_with_sr2_v1",
    "build_covapie_cumulative1000_current_global_readiness_artifacts_with_sr2_v1",
    "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_sr2_v1",
)


SCHEMA_VERSION = "covapie_cumulative1000_current_global_readiness_census_with_sr2_v1"
STAGE = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_SR2_V1"
ERROR_TOKEN = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_SR2_V1_ERROR"

OUTPUT_DIRECTORY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_sr2_v1"
)
CENSUS_FILE = "covapie_cumulative1000_current_global_readiness_census_with_sr2_v1.csv"
SUMMARY_FILE = "covapie_cumulative1000_current_global_readiness_summary_with_sr2_v1.json"
MANIFEST_FILE = "covapie_cumulative1000_current_global_readiness_manifest_with_sr2_v1.json"

PRODUCTION_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_current_global_readiness_census_with_sr2_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_sr2_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_cumulative1000_current_global_readiness_census_with_sr2_v1.py"
)
GUIDE_RELATIVE = Path(
    "docs/covapie_cumulative1000_current_global_readiness_census_with_sr2_v1_guide.md"
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
SR2_EXACT4_EVENT_IDS_V1 = sr2_ingestion.EXPECTED_EVENT_IDS
SR2_EXACT4_RANKS_V1 = sr2_ingestion.EXPECTED_RANKS
SR2_REVIEW_UNIT_ID_V1 = sr2_ingestion.EXPECTED_REVIEW_UNIT_ID
SR2_DIRECT_TASK_IDS_CELL_V1 = "[0,3,4]"

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
SR2_RECONCILIATION_OWNER_RELATIVE = Path(
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_sr2_v1.py"
)
SR2_INGESTION_OWNER_RELATIVE = sr2_ingestion.SOURCE_RELATIVE
SR2_EVENT_MATRIX_RELATIVE = (
    sr2_ingestion.OUTPUT_ROOT_RELATIVE / sr2_ingestion.MATRIX
)
PRIORITY_QUEUE_RELATIVE = predecessor.PRIORITY_QUEUE_RELATIVE
SR2_EVENT_MATRIX_SOURCE = SR2_EVENT_MATRIX_RELATIVE.as_posix()
# The published ingestion owner validates this parent-relative provenance. This
# census records the provenance string but never directly reads or binds it.
SR2_HUMAN_DECISION_SOURCE = sr2_ingestion.FORMAL_DECISION_RELATIVE.as_posix()
NEXT_PENDING_REVIEW_UNIT_ID_V1 = "COVAPIE_BULK_REVIEW_UNIT_AAB4DCC7D3073222"
NEXT_PENDING_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:2J7Q:A:CYS:23-:SG:F:GVE:CB",
    "COVAPIE_CYS_SG_EVENT_V1:2J7Q:C:CYS:23-:SG:J:GVE:CB",
    "COVAPIE_CYS_SG_EVENT_V1:3KW5:A:CYS:90-:SG:C:GVE:CB",
    "COVAPIE_CYS_SG_EVENT_V1:5CRA:A:CYS:118-:SG:K:GVE:CB",
)

_EXPECTED_GLOBAL_STATUS_COUNTS_V1 = {
    generic.CURRENTLY_UNREVIEWED: 195,
    generic.CURRENTLY_IN_PROGRESS: 0,
    generic.COMPLETED_HUMAN_POSITIVE: 115,
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
_EXPECTED_BOOLEAN_COUNTS_V1.update(
    {
        "reactive_pair_sample_authoritative": 132,
        "role_partition_sample_authoritative": 132,
        "canonical_mask_structural_labels_available": 132,
        "human_training_excluded": 72,
        "training_use_include": 60,
        "future_training_admission_candidate": 43,
    }
)

# Frozen after the first source-derived build. These projection digests do not
# create human, scientific, or training authority.
_EXPECTED_REFRESHED_CENSUS_SHA256_V1: str | None = (
    "f1657449f758d2e2f6ebcd76c5dfc955fac2568edb2623809497a8a1b1ea6d81"
)
_EXPECTED_REFRESHED_SUMMARY_SHA256_V1: str | None = (
    "8768be268197532b77a444e64821e17d446898041e6a1039182522f28cb188d5"
)
_EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1: str | None = (
    "4b08eefe1524a6ce485ed5806905fdff7ccc61c3ec6a8d98ebf6e425a8f1070e"
)

_SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_STRUCTURAL_IDENTITY_FIELDS_V1 = predecessor._STRUCTURAL_IDENTITY_FIELDS_V1
_EXPECTED_AUTHORIZED_SR2_OVERLAY_FIELDS_V1 = frozenset(
    {
        "canonical_mask_structural_labels_available",
        "chemistry_authority_source",
        "chemistry_disposition",
        "current_global_status",
        "current_review_status",
        "human_review_authority_source",
        "human_review_completed",
        "positive_authority_source",
        "reactive_pair_sample_authoritative",
        "role_partition_sample_authoritative",
        "role_profile",
        "structurally_applicable_task_ids_json",
        "task_relevance_authority_source",
        "task_relevance_disposition",
        "training_materialization_allowed_current_source",
        "training_use_disposition",
        "training_use_include",
        "future_training_admission_candidate",
        "human_training_excluded",
    }
)
_AUTHORIZED_SR2_OVERLAY_FIELDS_V1 = _EXPECTED_AUTHORIZED_SR2_OVERLAY_FIELDS_V1
_EXPECTED_SR2_STRUCTURAL_CELLS_V1 = {
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
        "PREDECESSOR_WITH_GD1_CENSUS_OWNER",
        PREDECESSOR_OWNER_RELATIVE,
        "repository_relative",
        70328,
        "b2ae78b391f03427687e1c75c418347ea4d053e1a0a1c4a98bb6813d769a6e5b",
        False,
    ),
    (
        "PREDECESSOR_WITH_GD1_MATERIALIZED_CENSUS",
        PREDECESSOR_CENSUS_RELATIVE,
        "repository_relative",
        539590,
        "90b8038047e08b0c43537ec8738a46b741468ee7a66633a863f244039485264c",
        False,
    ),
    (
        "PREDECESSOR_WITH_GD1_MATERIALIZED_SUMMARY",
        PREDECESSOR_SUMMARY_RELATIVE,
        "repository_relative",
        18845,
        "6b96964f77321ffa07504d8a6c06b974ba6525bba2d5acb3bc3298c697d4058c",
        False,
    ),
    (
        "SR2_RECONCILIATION_OWNER",
        SR2_RECONCILIATION_OWNER_RELATIVE,
        "repository_relative",
        37793,
        "19401cb0aeec3c138aace9093b58dfd61386bd87395a1b53cf83164583ffbe93",
        False,
    ),
    (
        "SR2_INGESTION_OWNER",
        SR2_INGESTION_OWNER_RELATIVE,
        "repository_relative",
        97771,
        "c34e42ef8d4cd7fba6ca7d259e2c103f1a6e81d604f76a7581ba47ae7259c8a8",
        False,
    ),
    (
        "SR2_EVENT_TASK_LABEL_AVAILABILITY",
        SR2_EVENT_MATRIX_RELATIVE,
        "repository_relative",
        13548,
        "218df42c78f32a4598d034fcd94a2fb1c9a210a523516ffdfdee34a6010e305c",
        False,
    ),
)
_PREDECESSOR_MANIFEST_SPEC_V1 = (
    62352,
    "7d7a070b39268d2b2c6147387e516151de67cbfd67b65d69017852530d7fb78d",
    False,
)


class Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(ValueError):
    """Raised unless the additive SR2 refresh is exactly source-derived."""


def _fail(reason: str) -> NoReturn:
    raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
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
        raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
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
    for role, relative, namespace, byte_count, sha256, executable in _ADDITIVE_SOURCE_SPECS_V1:
        try:
            verify_bound_source_v2(
                path=_resolve_source(root, namespace, relative),
                expected_byte_count=byte_count,
                expected_sha256=sha256,
                label=role + ":" + relative.as_posix(),
                expected_executable=executable,
            )
        except SourceBindingPolicyV2Error as error:
            raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
                f"{ERROR_TOKEN}:BOUND_SOURCE_REJECTED:{role}"
            ) from error
        bindings.append(
            {
                "artifact_role": role,
                "path": relative.as_posix(),
                "path_namespace": namespace,
                "byte_count": byte_count,
                "sha256": sha256,
                "expected_executable": executable,
            }
        )
    try:
        verify_bound_source_v2(
            path=root / PREDECESSOR_MANIFEST_RELATIVE,
            expected_byte_count=_PREDECESSOR_MANIFEST_SPEC_V1[0],
            expected_sha256=_PREDECESSOR_MANIFEST_SPEC_V1[1],
            label="PREDECESSOR_WITH_GD1_MANIFEST:" + PREDECESSOR_MANIFEST_RELATIVE.as_posix(),
            expected_executable=_PREDECESSOR_MANIFEST_SPEC_V1[2],
        )
    except SourceBindingPolicyV2Error as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
            f"{ERROR_TOKEN}:PREDECESSOR_WITH_GD1_MANIFEST_BINDING_INVALID"
        ) from error
    return tuple(bindings)


def _validate_sr2_matrix_rows_v1(
    rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    normalized = tuple(dict(row) for row in rows)
    if (
        len(normalized) != 4
        or any(tuple(row) != sr2_ingestion.MATRIX_HEADER for row in normalized)
        or tuple(row["canonical_event_id"] for row in normalized)
        != SR2_EXACT4_EVENT_IDS_V1
        or tuple(int(row["scaleup_rank"]) for row in normalized)
        != SR2_EXACT4_RANKS_V1
        or len({row["canonical_event_id"] for row in normalized}) != 4
    ):
        _fail("SR2_EVENT_MATRIX_IDENTITY_NOT_EXACT4")
    expected_contexts = tuple(
        (str(item[2]), str(item[3]), "CYS:345-", str(item[4]), str(item[5]))
        for item in sr2_ingestion.EXPECTED_EVENTS
    )
    actual_contexts = tuple(
        (
            row["pdb_id"],
            row["protein_chain_or_asym"],
            row["cys_residue_id"],
            row["ligand_chain_or_asym"],
            row["selected_connection_id"],
        )
        for row in normalized
    )
    if actual_contexts != expected_contexts:
        _fail("SR2_EVENT_MATRIX_CONTEXTS_COLLAPSED_OR_DRIFTED")
    expected_cells = {
        "review_unit_id": SR2_REVIEW_UNIT_ID_V1,
        "model_number": "1",
        "ligand_component_id": "SR2",
        "human_review_completed": "true",
        "human_task_relevance_decision": generic.TASK_RELEVANT,
        "task_relevance_human_authoritative": "true",
        "task_relevance": generic.TASK_RELEVANT,
        "human_chemistry_decision": generic.CHEMISTRY_POSITIVE,
        "chemistry_known_positive": "true",
        "chemistry_human_authoritative": "true",
        "chemistry": generic.CHEMISTRY_POSITIVE,
        "negative_chemistry": "false",
        "task_domain_negative": "false",
        "reactive_pair_human_decision_available": "true",
        "reactive_pair_human_authoritative": "true",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C51",
        "reusable_pair_rule_created": "false",
        "cross_structure_regiochemistry_generalization": "false",
        "role_partition_human_decision_available": "true",
        "role_partition_human_authoritative": "true",
        "selected_candidate_index_0based": "15",
        "role_profile": base.DIRECT_PROFILE,
        "W_L_S_counts_json": "[9,0,18]",
        "global_canonical_task_count": "5",
        "B3_present": "true",
        "sixth_task": "false",
        "direct_profile_applicable_task_ids_json": SR2_DIRECT_TASK_IDS_CELL_V1,
        "task_applicability_determined": "true",
        "authoritative_task_labels_created": "false",
        "event_task_label_rows_materialized": "false",
        "formal_event_training_use_decision": generic.TRAINING_INCLUDE,
        "event_training_use_human_decision_available": "true",
        "training_use_allowed": "true",
        "human_training_excluded": "false",
        "candidate_for_future_training_admission": "true",
        "future_training_admission_candidate": "true",
        "future_training_admission_status": sr2_ingestion.FUTURE_STATUS,
        "training_admitted": "false",
        "formal_training_admitted": "false",
        "training_materialization_allowed_now": "false",
        "training_materialization_allowed": "false",
        "tensor_target_created": "false",
        "model_supervision_usable": "false",
        "training_mask_targets_available_now": "false",
        "current_runtime_model_usable": "false",
        "parameter_update_authorization": "false",
        "READY_FOR_TRAINING": "false",
        "supporting_PRE_source_graph_count_per_event": "1",
        "PRE_source_graph_present": "true",
        "PRE_source_graph_count_per_event": "1",
        "PRE_mapping_count_per_event": "0",
        "PRE_mapping_status": sr2_ingestion.PRE_MAPPING_STATUS,
        "PRE_status": sr2_ingestion.PRE_STATUS,
        "PRE_topology_authority": "false",
        "PRE_geometry_authority": "false",
        "PRE_coordinates_authority": "false",
        "PRE_reconstruction": "false",
        "POST_to_PRE_copy": "false",
        "PRE_zero_fill": "false",
        "POST_source_evidence_available": "true",
        "explicit_covalent_evidence": "true",
        "distance_only_inference": "false",
        "POST_geometry_training_authority": "false",
        "POST_geometry_training_target_created": "false",
        "POST_geometry_training_label_available_now": "false",
        "reusable_chemistry_authority": "false",
        "reusable_role_authority": "false",
        "reaction_family_authority": "false",
        "warhead_rule_authority": "false",
        "warhead_type_authority": "false",
        "reaction_family_training_class_target_available": "false",
        "warhead_rule_training_class_target_available": "false",
        "warhead_type_target_available": "false",
        "reusable_authority_label_available": "false",
        "authority_source": sr2_ingestion.AUTHORITY_SOURCE,
        "projection_of_frozen_formal_human_authority": "true",
        "new_human_authority_created_by_ingestion": "false",
        "metadata_only": "true",
        "dataset_mutated": "false",
        "training_dataset_changed": "false",
        "tensorization_performed": "false",
        "loader_modified": "false",
        "batch_modified": "false",
        "model_forward": "false",
        "loss": "false",
        "backward": "false",
        "optimizer": "false",
        "parameter_update": "false",
        "training": "false",
    }
    semantic_names = [item[1] for item in CANONICAL_EXACT5_V1]
    aliases = [item[2] for item in CANONICAL_EXACT5_V1]
    for row in normalized:
        event_id = row["canonical_event_id"]
        if any(row[key] != value for key, value in expected_cells.items()):
            _fail("SR2_EVENT_MATRIX_SEMANTICS_INVALID:" + event_id)
        try:
            applicability = json.loads(row["canonical_task_applicability_json"])
            warhead = json.loads(row["warhead_atoms_json"])
            linker = json.loads(row["linker_atoms_json"])
            scaffold = json.loads(row["scaffold_atoms_json"])
            boundary = json.loads(row["boundary_bonds_json"])
        except json.JSONDecodeError as error:
            raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
                f"{ERROR_TOKEN}:SR2_MATRIX_JSON_INVALID:{event_id}"
            ) from error
        if (
            len(applicability) != 5
            or [item["task_id"] for item in applicability] != list(range(5))
            or [item["semantic_long_name"] for item in applicability] != semantic_names
            or [item["display_alias"] for item in applicability] != aliases
            or [item["task_id"] for item in applicability if item["structurally_applicable"]]
            != [0, 3, 4]
            or any(item["role_profile"] != base.DIRECT_PROFILE for item in applicability)
            or applicability[3]["semantic_long_name"] != "scaffold_only"
            or warhead != list(sr2_ingestion.WARHEAD_ROLE)
            or linker != []
            or scaffold != list(sr2_ingestion.SCAFFOLD_ROLE)
            or boundary != list(sr2_ingestion.BOUNDARY_BONDS)
        ):
            _fail("SR2_EVENT_MATRIX_EXACT5_INVALID:" + event_id)
    return normalized


def _load_and_validate_sr2_event_matrix_v1(
    root: Path,
) -> tuple[dict[str, str], ...]:
    payload = _read_regular_file(root / SR2_EVENT_MATRIX_RELATIVE, "SR2_EVENT_MATRIX")
    if len(payload) != _ADDITIVE_SOURCE_SPECS_V1[5][3] or _sha256(payload) != _ADDITIVE_SOURCE_SPECS_V1[5][4]:
        _fail("SR2_EVENT_MATRIX_BINDING_INVALID")
    source_derived = sr2_ingestion.build_artifacts_v1(root)
    if source_derived[sr2_ingestion.MATRIX] != payload:
        _fail("SR2_EVENT_MATRIX_NOT_SOURCE_DERIVED")
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
            f"{ERROR_TOKEN}:SR2_EVENT_MATRIX_NOT_UTF8"
        ) from error
    if tuple(reader.fieldnames or ()) != sr2_ingestion.MATRIX_HEADER:
        _fail("SR2_EVENT_MATRIX_HEADER_INVALID")
    return _validate_sr2_matrix_rows_v1(tuple(dict(row) for row in reader))


def _validate_sr2_reconciliation_v1(root: Path) -> generic.ReconciliationResult:
    result = sr2_reconciliation.reconcile_real_completed_human_decisions_with_sr2_v1(root)
    if result.review_summary != {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 115,
        "completed_positive_unit_count": 18,
        "completed_negative_event_count": 28,
        "completed_negative_unit_count": 5,
        "completed_total_event_count": 143,
        "completed_total_unit_count": 23,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 195,
        "unreviewed_unit_count": 108,
    }:
        _fail("SR2_RECONCILIATION_SUMMARY_INVALID")
    facts = result.normalized_facts
    if (
        len(facts) != 119
        or len({fact.source_binding_path for fact in facts}) != 19
        or Counter(fact.training_disposition for fact in facts)
        != Counter(
            {
                generic.TRAINING_INCLUDE: 43,
                generic.TRAINING_EXCLUDE: 72,
                generic.TRAINING_NOT_APPLICABLE: 4,
            }
        )
    ):
        _fail("SR2_RECONCILIATION_EXACT19_119_INVALID")
    exact4 = set(SR2_EXACT4_EVENT_IDS_V1)
    rows = [row for row in result.reconciled_rows if row["canonical_event_id"] in exact4]
    exact4_facts = [fact for fact in facts if fact.canonical_event_id in exact4]
    if (
        len(rows) != 4
        or {row["canonical_event_id"] for row in rows} != exact4
        or any(row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE for row in rows)
        or len(exact4_facts) != 4
        or any(
            fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_INCLUDE
            or fact.human_training_excluded is not False
            for fact in exact4_facts
        )
    ):
        _fail("SR2_RECONCILIATION_EXACT4_INVALID")
    return result


def _assert_predecessor_sr2_state_v1(
    computation: base.Cumulative1000CurrentGlobalReadinessComputationV1,
) -> None:
    exact4 = set(SR2_EXACT4_EVENT_IDS_V1)
    rows = [row for row in computation.rows if row["canonical_event_id"] in exact4]
    if len(rows) != 4 or tuple(int(row["scaleup_rank"]) for row in rows) != SR2_EXACT4_RANKS_V1:
        _fail("PREDECESSOR_SR2_EXACT4_IDENTITY_INVALID")
    expected = {
        "current_global_status": generic.CURRENTLY_UNREVIEWED,
        "priority_review_in_scope": "true",
        "review_unit_id": SR2_REVIEW_UNIT_ID_V1,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "human_review_completed": "false",
        "human_review_authority_source": PRIORITY_QUEUE_RELATIVE.as_posix(),
        "chemistry_disposition": base.CHEMISTRY_UNRESOLVED,
        "chemistry_authority_source": "",
        "task_relevance_disposition": base.TASK_UNRESOLVED,
        "task_relevance_authority_source": "",
        "training_use_disposition": base.TRAINING_UNRESOLVED,
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
        "positive_authority_source": "",
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    }
    if any(any(row[key] != value for key, value in expected.items()) for row in rows):
        _fail("PREDECESSOR_SR2_STATE_INVALID")
    if any(
        any(row[field] != value for field, value in _EXPECTED_SR2_STRUCTURAL_CELLS_V1.items())
        for row in rows
    ):
        _fail("PREDECESSOR_SR2_STRUCTURAL_COVERAGE_INVALID")
    if (
        Counter(row["chemistry_disposition"] for row in computation.rows)[base.CHEMISTRY_POSITIVE] != 128
        or Counter(row["task_relevance_disposition"] for row in computation.rows)[base.TASK_RELEVANT] != 129
        or Counter(row["training_use_disposition"] for row in computation.rows)[generic.TRAINING_INCLUDE] != 56
        or Counter(row["training_use_disposition"] for row in computation.rows)[generic.TRAINING_EXCLUDE] != 72
        or sum(row["future_training_admission_candidate"] == "true" for row in computation.rows) != 39
    ):
        _fail("PREDECESSOR_GLOBAL_COUNTS_INVALID")


def _overlay_sr2_exact4_v1(
    predecessor_rows: Sequence[Mapping[str, str]],
    matrix_rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    matrix_by_event = {
        row["canonical_event_id"]: row
        for row in _validate_sr2_matrix_rows_v1(matrix_rows)
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
            or row["ligand_component_id"] != "SR2"
            or row["review_unit_id"] != SR2_REVIEW_UNIT_ID_V1
        ):
            _fail("SR2_MATRIX_PREDECESSOR_IDENTITY_MISMATCH:" + event_id)
        row.update(
            {
                "current_global_status": generic.COMPLETED_HUMAN_POSITIVE,
                "current_review_status": generic.COMPLETED_HUMAN_POSITIVE,
                "human_review_completed": "true",
                "human_review_authority_source": SR2_HUMAN_DECISION_SOURCE,
                "chemistry_disposition": base.CHEMISTRY_POSITIVE,
                "chemistry_authority_source": SR2_EVENT_MATRIX_SOURCE,
                "positive_authority_source": SR2_EVENT_MATRIX_SOURCE,
                "task_relevance_disposition": base.TASK_RELEVANT,
                "task_relevance_authority_source": SR2_EVENT_MATRIX_SOURCE,
                "training_use_disposition": generic.TRAINING_INCLUDE,
                "human_training_excluded": "false",
                "reactive_pair_sample_authoritative": "true",
                "role_partition_sample_authoritative": "true",
                "role_profile": base.DIRECT_PROFILE,
                "canonical_mask_structural_labels_available": "true",
                "structurally_applicable_task_ids_json": SR2_DIRECT_TASK_IDS_CELL_V1,
                "training_use_include": "true",
                "future_training_admission_candidate": "true",
                "training_materialization_allowed_current_source": "false",
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
            expected_sha256="a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2",
            label="FROZEN_PRIORITY_QUEUE:" + PRIORITY_QUEUE_RELATIVE.as_posix(),
            expected_executable=False,
        )
    except SourceBindingPolicyV2Error as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
            f"{ERROR_TOKEN}:PRIORITY_QUEUE_BINDING_INVALID"
        ) from error
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    queue_rows = [dict(row) for row in reader]
    if len(queue_rows) != 131 or len({row["priority_rank"] for row in queue_rows}) != 131:
        _fail("PRIORITY_QUEUE_IDENTITY_INVALID")
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
        candidates.append((-int(row["event_count"]), int(row["priority_rank"]), unit, row, status))
    candidates.sort(key=lambda item: item[:3])
    if len(candidates) != 108:
        _fail("CURRENT_PENDING_REVIEW_UNIT_COUNT_INVALID")
    if any(unit == SR2_REVIEW_UNIT_ID_V1 for _n, _p, unit, _row, _s in candidates):
        _fail("SR2_REVIEW_UNIT_STILL_PENDING")
    if not candidates or (len(candidates) > 1 and candidates[0][:3] == candidates[1][:3]):
        _fail("NEXT_PENDING_DERIVATION_FAILED")
    top: list[dict[str, object]] = []
    for rank, (_negative, _priority, unit, row, status) in enumerate(candidates[:10], 1):
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
                "current_review_status": status,
            }
        )
    expected_next = {
        "rank": 1,
        "raw_priority_rank": 23,
        "review_unit_id": NEXT_PENDING_REVIEW_UNIT_ID_V1,
        "event_count": 4,
        "pdb_ids": ["2J7Q", "3KW5", "5CRA"],
        "ligand_component_ids": ["GVE"],
        "full_coordinate_count": 4,
        "exact_pair_count": 4,
        "ccd_complete_count": 4,
        "post_source_evidence_count": 4,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
    }
    next_event_ids = tuple(
        row["canonical_event_id"]
        for row in reconciliation.reconciled_rows
        if row["raw_review_unit_id"] == NEXT_PENDING_REVIEW_UNIT_ID_V1
    )
    if not top or top[0] != expected_next or next_event_ids != NEXT_PENDING_EVENT_IDS_V1:
        _fail("NEXT_PENDING_SOURCE_DRIFT")
    return top


def _sets_for_algebra_v1(rows: Sequence[Mapping[str, str]]) -> dict[str, set[str]]:
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

    def count_true(field: str, population: Sequence[Mapping[str, str]] = rows) -> int:
        return sum(row[field] == "true" for row in population)

    chemistry_positive = event_set("chemistry_disposition", base.CHEMISTRY_POSITIVE)
    chemistry_negative = event_set("chemistry_disposition", base.CHEMISTRY_NEGATIVE)
    chemistry_not_established = event_set("chemistry_disposition", base.CHEMISTRY_NOT_ESTABLISHED)
    chemistry_unresolved = event_set("chemistry_disposition", base.CHEMISTRY_UNRESOLVED)
    task_relevant = event_set("task_relevance_disposition", base.TASK_RELEVANT)
    task_not_relevant = event_set("task_relevance_disposition", base.TASK_NOT_RELEVANT)
    task_unresolved = event_set("task_relevance_disposition", base.TASK_UNRESOLVED)
    training_include = event_set("training_use_disposition", generic.TRAINING_INCLUDE)
    training_exclude = event_set("training_use_disposition", generic.TRAINING_EXCLUDE)
    training_not_applicable = event_set("training_use_disposition", generic.TRAINING_NOT_APPLICABLE)
    training_unresolved = event_set("training_use_disposition", base.TRAINING_UNRESOLVED)
    positive_rows = [row for row in rows if row["canonical_event_id"] in chemistry_positive]
    include_rows = [row for row in rows if row["canonical_event_id"] in training_include]
    missing_tensor_rows = [
        row for row in positive_rows
        if row["reactive_pair_training_target_available"] == "false"
    ]

    summary["schema_version"] = SCHEMA_VERSION
    summary["stage"] = STAGE
    summary["refresh_delta"] = {
        "frozen_predecessor_positive_count": 128,
        "sr2_exact4_delta_count": 4,
        "refreshed_positive_count": len(chemistry_positive),
        "frozen_predecessor_training_include_count": 56,
        "refreshed_training_include_count": len(training_include),
        "frozen_predecessor_training_exclude_count": 72,
        "refreshed_training_exclude_count": len(training_exclude),
        "frozen_predecessor_future_candidate_count": 39,
        "refreshed_future_candidate_count": count_true("future_training_admission_candidate"),
        "changed_event_count": 4,
        "unchanged_event_count": 996,
        "derived_refresh_not_new_authority": True,
    }
    summary["global_status_distribution"]["counts"] = {
        status: Counter(row["current_global_status"] for row in rows)[status]
        for status in base.GLOBAL_STATUSES_V1
    }
    priority_rows = [row for row in rows if row["priority_review_in_scope"] == "true"]
    review_counts = Counter(row["current_review_status"] for row in priority_rows)
    units_by_status: dict[str, set[str]] = defaultdict(set)
    for row in priority_rows:
        units_by_status[row["current_review_status"]].add(row["review_unit_id"])
    completed_units = units_by_status[generic.COMPLETED_HUMAN_POSITIVE] | units_by_status[generic.COMPLETED_HUMAN_NEGATIVE]
    pending_units = units_by_status[generic.CURRENTLY_UNREVIEWED] | units_by_status[generic.CURRENTLY_IN_PROGRESS]
    summary["human_review"] = {
        "priority_review_population_event_count": len(priority_rows),
        "review_unit_count": len({row["review_unit_id"] for row in priority_rows}),
        "completed_event_count": review_counts[generic.COMPLETED_HUMAN_POSITIVE] + review_counts[generic.COMPLETED_HUMAN_NEGATIVE],
        "completed_unit_count": len(completed_units),
        "completed_positive_event_count": review_counts[generic.COMPLETED_HUMAN_POSITIVE],
        "completed_positive_unit_count": len(units_by_status[generic.COMPLETED_HUMAN_POSITIVE]),
        "completed_negative_event_count": review_counts[generic.COMPLETED_HUMAN_NEGATIVE],
        "completed_negative_unit_count": len(units_by_status[generic.COMPLETED_HUMAN_NEGATIVE]),
        "unreviewed_event_count": review_counts[generic.CURRENTLY_UNREVIEWED],
        "unreviewed_unit_count": len(units_by_status[generic.CURRENTLY_UNREVIEWED]),
        "in_progress_event_count": review_counts[generic.CURRENTLY_IN_PROGRESS],
        "in_progress_unit_count": len(units_by_status[generic.CURRENTLY_IN_PROGRESS]),
        "pending_event_count": review_counts[generic.CURRENTLY_UNREVIEWED] + review_counts[generic.CURRENTLY_IN_PROGRESS],
        "current_pending_review_unit_count": len(pending_units),
    }
    source_composition = dict(summary["chemistry"]["positive_source_composition"])
    source_composition["SR2"] = sum(
        row["positive_authority_source"] == SR2_EVENT_MATRIX_SOURCE for row in rows
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
            "raw_structural_pair_evidence_count": count_true("reactive_pair_raw_structural_evidence"),
            "sample_level_authoritative_pair_count": count_true("reactive_pair_sample_authoritative"),
            "published_model_bound_target_constructible_count": count_true("reactive_pair_training_target_available"),
            "current_runtime_bound_target_count": count_true("current_runtime_model_usable"),
            "sr2_sample_authority_contribution_count": 4,
            "sr2_training_target_contribution_count": 0,
            "positive_without_sample_pair_authority_count": sum(
                row["reactive_pair_sample_authoritative"] == "false" for row in positive_rows
            ),
        }
    )
    profile_counts = Counter(
        row["role_profile"] for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    )
    applicability_counts: Counter[int] = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability_counts.update(json.loads(row["structurally_applicable_task_ids_json"]))
    summary["role"].update(
        {
            "role_partition_sample_authoritative_count": count_true("role_partition_sample_authoritative"),
            "role_profile_counts": {
                base.STRICT_PROFILE: profile_counts[base.STRICT_PROFILE],
                base.DIRECT_PROFILE: profile_counts[base.DIRECT_PROFILE],
                "other": sum(value for profile, value in profile_counts.items() if profile not in {base.STRICT_PROFILE, base.DIRECT_PROFILE}),
            },
            "canonical_mask_structural_labels_available_count": count_true("canonical_mask_structural_labels_available"),
            "all_five_structurally_applicable_count": sum(row["structurally_applicable_task_ids_json"] == "[0,1,2,3,4]" for row in rows),
            "direct_profile_A_B3_C_count": sum(row["structurally_applicable_task_ids_json"] == "[0,3,4]" for row in rows),
            "unknown_role_row_count": sum(row["role_partition_sample_authoritative"] == "false" for row in rows),
        }
    )
    for task in summary["canonical_exact5"]["tasks"]:
        task["structurally_applicable_authoritative_role_count"] = applicability_counts[task["task_id"]]
    future_sources = dict(summary["training_stage"]["future_candidate_source_composition"])
    future_sources["SR2"] = sum(
        row["positive_authority_source"] == SR2_EVENT_MATRIX_SOURCE
        and row["future_training_admission_candidate"] == "true"
        for row in rows
    )
    summary["training_stage"].update(
        {
            "training_use_include_count": len(training_include),
            "future_training_admission_candidate_count": count_true("future_training_admission_candidate"),
            "future_candidate_source_composition": future_sources,
            "current_runtime_model_usable_count": count_true("current_runtime_model_usable"),
            "formal_training_admitted_count": count_true("formal_training_admitted"),
            "ready_for_formal_training_event_count": 0,
        }
    )
    missing_source_composition = dict(summary["blockers"]["missing_tensor_integration"]["missing_source_composition"])
    missing_source_composition["SR2"] = sum(
        row["positive_authority_source"] == SR2_EVENT_MATRIX_SOURCE
        for row in missing_tensor_rows
    )
    summary["blockers"] = {
        "non_exclusive_counts_must_not_be_summed": True,
        "chemistry_unresolved": {"all_1000": len(chemistry_unresolved)},
        "pair_authority_absent": {
            "all_1000": sum(row["reactive_pair_sample_authoritative"] == "false" for row in rows),
            "within_positive_132": sum(row["reactive_pair_sample_authoritative"] == "false" for row in positive_rows),
        },
        "role_authority_absent": {
            "all_1000": sum(row["role_partition_sample_authoritative"] == "false" for row in rows),
            "within_positive_132": sum(row["role_partition_sample_authoritative"] == "false" for row in positive_rows),
        },
        "human_training_exclusion": {
            "within_positive_132": sum(row["human_training_excluded"] == "true" for row in positive_rows)
        },
        "missing_split_authority": {
            "within_positive_132": sum(row["formal_split_authoritative"] == "false" for row in positive_rows),
            "within_include_60": sum(row["formal_split_authoritative"] == "false" for row in include_rows),
        },
        "missing_tensor_integration": {
            "within_positive_132": len(missing_tensor_rows),
            "within_include_60": sum(row["reactive_pair_training_target_available"] == "false" for row in include_rows),
            "all_missing_are_training_excluded_population": all(row["training_use_disposition"] == generic.TRAINING_EXCLUDE for row in missing_tensor_rows),
            "missing_source_composition": missing_source_composition,
        },
        "missing_POST_training_authority": {
            "within_positive_132": sum(row["post_geometry_training_target_available"] == "false" for row in positive_rows),
            "within_include_60": sum(row["post_geometry_training_target_available"] == "false" for row in include_rows),
        },
        "missing_training_admission": {
            "within_positive_132": sum(row["formal_training_admitted"] == "false" for row in positive_rows),
            "within_include_60": sum(row["formal_training_admitted"] == "false" for row in include_rows),
        },
        "feature_semantics_pending": {"within_positive_132": len(positive_rows)},
    }
    summary["top_pending_review_units_by_event_yield"] = top_pending
    next_pending = top_pending[0]
    boundary = summary["authority_boundary"]
    boundary.update(
        {
            "next_priority_review_unit": next_pending["review_unit_id"],
            "next_priority_review_ligand": next_pending["ligand_component_ids"][0] if len(next_pending["ligand_component_ids"]) == 1 else next_pending["ligand_component_ids"],
            "next_priority_review_event_count": next_pending["event_count"],
            "next_priority_review_current_pending_rank": next_pending["rank"],
            "next_priority_review_raw_priority_rank": next_pending["raw_priority_rank"],
            "next_review_started": False,
            "NEXT_REVIEW_STARTED": False,
            "SR2_REVIEW_COMPLETED": True,
            "CURRENT_GLOBAL_RECONCILIATION_COMPLETE": True,
            "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE": True,
            "CENSUS_REFRESH": True,
            "census_refreshed": True,
            "HUMAN_REVIEW_DECISION_NOT_PERFORMED": True,
            "READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION": True,
            "READY_FOR_GVE_REVIEW_PREPARATION": True,
            "GVE_REVIEW_STARTED": False,
            "engineered_surrogate_caveat_preserved": True,
            "SR2_formal_training_candidate": True,
            "PRE_mapping_incompatible": True,
            "READY_FOR_EXTERNAL_REVIEW": True,
            "new_exact_posix_source_mode_authority_introduced": False,
            "new_ambiguous_source_mode_authority_introduced": False,
            "SR2_CENSUS_SOURCE_BINDING_V2_CLEAN_FROM_BIRTH": True,
            "separate_SR2_census_V2_successor_required": False,
            "QUEUE_REFRESH": False,
            "priority_queue_file_modified": False,
            "priority_queue_file_created": False,
            "READY_FOR_TRAINING": False,
            "READY_FOR_FORMAL_TRAINING": False,
            "training_started": False,
            "TRAINING_STARTED": False,
            "training_materialization_allowed": False,
            "parameter_update_authorization": False,
            "future_candidate_is_not_training_admission": True,
            "minimal_seed_authority_created": False,
            "new_human_authority_created": False,
            "new_scientific_authority_created": False,
            "new_chemistry_authority_created": False,
            "new_pair_authority_created": False,
            "new_role_authority_created": False,
            "new_reusable_authority_created": False,
            "reaction_family_authority": False,
            "warhead_rule_authority": False,
            "warhead_type_authority": False,
            "reusable_chemistry_authority": False,
            "reusable_pair_authority": False,
            "reusable_role_authority": False,
            "post_geometry_training_authority_created": False,
            "pre_geometry_authority_created": False,
            "formal_decision_read_directly": False,
            "formal_decision_bound_directly": False,
            "formal_validator_executed": False,
            "Step12D": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        }
    )
    boundary.pop("CER_REVIEW_STARTED", None)
    boundary.pop("separate_CER_census_V2_successor_required", None)
    boundary.pop("CER_CENSUS_SOURCE_BINDING_V2_CLEAN_FROM_BIRTH", None)
    return summary


def _verify_predecessor_semantic_bindings_v1(
    root: Path,
    bindings: Sequence[Mapping[str, object]],
) -> None:
    payload = _read_regular_file(root / PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_WITH_GD1_MANIFEST")
    try:
        manifest = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
            f"{ERROR_TOKEN}:PREDECESSOR_MANIFEST_JSON_INVALID"
        ) from error
    manifested = manifest.get("semantic_source_bindings")
    if type(manifested) is not list or tuple(manifested) != tuple(bindings) or len(manifested) != 138:
        _fail("PREDECESSOR_SEMANTIC_BINDINGS_NOT_MANIFEST_DERIVED_EXACT138")
    digest = _sha256(_canonical_json(manifested).encode("utf-8"))
    if digest != predecessor._EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1:
        _fail("PREDECESSOR_SEMANTIC_BINDING_DIGEST_INVALID")


def _merge_semantic_bindings_v1(
    predecessor_bindings: Sequence[Mapping[str, object]],
    additive_bindings: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    return predecessor._merge_semantic_bindings_v1(predecessor_bindings, additive_bindings)


def compute_covapie_cumulative1000_current_global_readiness_census_with_sr2_v1(
    repo_root: Path,
) -> base.Cumulative1000CurrentGlobalReadinessComputationV1:
    """Compute the exact additive SR2 refresh entirely from frozen sources."""

    root = repo_root.resolve()
    additive_bindings = _verify_additive_sources(root)
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1(root)
    _assert_predecessor_sr2_state_v1(frozen)
    _verify_predecessor_semantic_bindings_v1(root, frozen.semantic_source_bindings)
    reconciliation = _validate_sr2_reconciliation_v1(root)
    matrix_rows = _load_and_validate_sr2_event_matrix_v1(root)
    rows = _overlay_sr2_exact4_v1(frozen.rows, matrix_rows)
    top_pending = _top_pending_review_units_v1(root, reconciliation)
    summary = _build_summary_v1(rows, top_pending)
    bindings = _merge_semantic_bindings_v1(frozen.semantic_source_bindings, additive_bindings)
    computation = base.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=rows,
        summary=summary,
        semantic_source_bindings=bindings,
    )
    validate_covapie_cumulative1000_current_global_readiness_census_with_sr2_v1(
        computation,
        predecessor_computation=frozen,
        reconciliation_result=reconciliation,
        matrix_rows=matrix_rows,
    )
    return computation


def validate_covapie_cumulative1000_current_global_readiness_census_with_sr2_v1(
    computation: object,
    *,
    predecessor_computation: base.Cumulative1000CurrentGlobalReadinessComputationV1 | None = None,
    reconciliation_result: generic.ReconciliationResult | None = None,
    matrix_rows: Sequence[Mapping[str, str]] | None = None,
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
        or len(CENSUS_COLUMNS_V1) != 47
        or CENSUS_COLUMNS_V1 != predecessor.CENSUS_COLUMNS_V1
        or any(type(row) is not dict or tuple(row) != CENSUS_COLUMNS_V1 for row in rows)
        or type(summary) is not dict
        or type(bindings) is not tuple
    ):
        _fail("CENSUS_SUMMARY_OR_BINDINGS_SCHEMA_INVALID")
    if (
        _AUTHORIZED_SR2_OVERLAY_FIELDS_V1
        != _EXPECTED_AUTHORIZED_SR2_OVERLAY_FIELDS_V1
        or len(_AUTHORIZED_SR2_OVERLAY_FIELDS_V1) != 19
    ):
        _fail("AUTHORIZED_SR2_OVERLAY_NOT_EXACT19")
    root = Path(__file__).resolve().parents[2]
    frozen = predecessor_computation or predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_gd1_v1(root)
    reconciliation = reconciliation_result or _validate_sr2_reconciliation_v1(root)
    validated_matrix = _validate_sr2_matrix_rows_v1(matrix_rows) if matrix_rows is not None else _load_and_validate_sr2_event_matrix_v1(root)
    if type(frozen) is not expected_type:
        _fail("PREDECESSOR_COMPUTATION_TYPE_INVALID")
    _assert_predecessor_sr2_state_v1(frozen)
    _verify_predecessor_semantic_bindings_v1(root, frozen.semantic_source_bindings)
    _validate_sr2_reconciliation_v1_result = reconciliation
    if _validate_sr2_reconciliation_v1_result.review_summary["completed_positive_event_count"] != 115:
        _fail("RECONCILIATION_RESULT_INVALID")
    _validate_sr2_matrix_rows_v1(validated_matrix)

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
            raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
                f"{ERROR_TOKEN}:CENSUS_RANK_INVALID:{event_id}"
            ) from error
    if ranks != list(range(1, 1001)):
        _fail("CENSUS_RANK_GAP_OR_ORDER_INVALID")
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in rows}
    exact4 = set(SR2_EXACT4_EVENT_IDS_V1)
    if set(before) != set(after):
        _fail("CENSUS_EVENT_SET_IDENTITY_INVALID")
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    if changed != exact4 or any(before[event_id] != after[event_id] for event_id in set(before) - exact4):
        _fail("PREDECESSOR_DELTA_NOT_EXACT_SR2_EXACT4")
    expected_after = {
        "current_global_status": generic.COMPLETED_HUMAN_POSITIVE,
        "priority_review_in_scope": "true",
        "review_unit_id": SR2_REVIEW_UNIT_ID_V1,
        "current_review_status": generic.COMPLETED_HUMAN_POSITIVE,
        "human_review_completed": "true",
        "human_review_authority_source": SR2_HUMAN_DECISION_SOURCE,
        "chemistry_disposition": base.CHEMISTRY_POSITIVE,
        "chemistry_authority_source": SR2_EVENT_MATRIX_SOURCE,
        "positive_authority_source": SR2_EVENT_MATRIX_SOURCE,
        "task_relevance_disposition": base.TASK_RELEVANT,
        "task_relevance_authority_source": SR2_EVENT_MATRIX_SOURCE,
        "training_use_disposition": generic.TRAINING_INCLUDE,
        "human_training_excluded": "false",
        "reactive_pair_sample_authoritative": "true",
        "reactive_pair_training_target_available": "false",
        "role_partition_sample_authoritative": "true",
        "role_profile": base.DIRECT_PROFILE,
        "canonical_mask_structural_labels_available": "true",
        "structurally_applicable_task_ids_json": SR2_DIRECT_TASK_IDS_CELL_V1,
        "post_geometry_sample_authoritative": "false",
        "post_geometry_training_target_available": "false",
        "pre_geometry_authoritative": "false",
        "pre_geometry_training_target_available": "false",
        "training_use_include": "true",
        "future_training_admission_candidate": "true",
        "formal_split_authoritative": "false",
        "formal_split": "",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "training_materialization_allowed_current_source": "false",
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    }
    for event_id in SR2_EXACT4_EVENT_IDS_V1:
        changed_fields = {field for field in CENSUS_COLUMNS_V1 if before[event_id][field] != after[event_id][field]}
        actual_changed_fields = _AUTHORIZED_SR2_OVERLAY_FIELDS_V1 - {
            "human_training_excluded"
        }
        if changed_fields != actual_changed_fields:
            _fail("SR2_CHANGED_FIELD_SET_INVALID:" + event_id)
        if any(before[event_id][field] != after[event_id][field] for field in _STRUCTURAL_IDENTITY_FIELDS_V1):
            _fail("SR2_STRUCTURAL_EVIDENCE_CHANGED:" + event_id)
        if any(after[event_id][field] != value for field, value in expected_after.items()):
            _fail("SR2_REFRESHED_SEMANTICS_INVALID:" + event_id)

    previous_sets = _sets_for_algebra_v1(frozen.rows)
    current_sets = _sets_for_algebra_v1(rows)
    if not (
        current_sets["chemistry_positive"] == previous_sets["chemistry_positive"] | exact4
        and current_sets["chemistry_unresolved"] == previous_sets["chemistry_unresolved"] - exact4
        and current_sets["task_relevant"] == previous_sets["task_relevant"] | exact4
        and current_sets["task_unresolved"] == previous_sets["task_unresolved"] - exact4
        and current_sets["training_include"] == previous_sets["training_include"] | exact4
        and current_sets["training_unresolved"] == previous_sets["training_unresolved"] - exact4
        and current_sets["chemistry_negative"] == previous_sets["chemistry_negative"]
        and current_sets["chemistry_not_established"] == previous_sets["chemistry_not_established"]
        and current_sets["task_not_relevant"] == previous_sets["task_not_relevant"]
        and current_sets["training_exclude"] == previous_sets["training_exclude"]
        and current_sets["training_not_applicable"] == previous_sets["training_not_applicable"]
        and current_sets["future_candidate"] == previous_sets["future_candidate"] | exact4
        and current_sets["formal_split"] == previous_sets["formal_split"]
        and current_sets["formal_admitted"] == previous_sets["formal_admitted"]
        and current_sets["runtime_usable"] == previous_sets["runtime_usable"]
    ):
        _fail("SR2_EXACT_SET_ALGEBRA_INVALID")
    if Counter(row["chemistry_disposition"] for row in rows) != Counter({"POSITIVE": 132, "NOT_ESTABLISHED": 90, "UNRESOLVED": 778}):
        _fail("CENSUS_CHEMISTRY_DISTRIBUTION_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter({"RELEVANT": 133, "NOT_RELEVANT": 90, "UNRESOLVED": 777}):
        _fail("CENSUS_TASK_DISTRIBUTION_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter({"INCLUDE": 60, "EXCLUDE_FROM_TRAINING_ONLY": 72, "NOT_APPLICABLE": 90, "UNRESOLVED": 778}):
        _fail("CENSUS_TRAINING_DISTRIBUTION_INVALID")
    if Counter(row["current_global_status"] for row in rows) != Counter(_EXPECTED_GLOBAL_STATUS_COUNTS_V1):
        _fail("CENSUS_EXACT11_DISTRIBUTION_INVALID")
    for field, expected in _EXPECTED_BOOLEAN_COUNTS_V1.items():
        if sum(row[field] == "true" for row in rows) != expected:
            _fail("CENSUS_BOOLEAN_COUNT_INVALID:" + field)
    if Counter(row["role_profile"] for row in rows if row["role_partition_sample_authoritative"] == "true") != Counter({base.STRICT_PROFILE: 52, base.DIRECT_PROFILE: 80}):
        _fail("CENSUS_ROLE_PROFILE_DISTRIBUTION_INVALID")
    applicability: Counter[int] = Counter()
    for row in rows:
        event_id = row["canonical_event_id"]
        if row["role_partition_sample_authoritative"] == "true":
            expected_ids = [0, 1, 2, 3, 4] if row["role_profile"] == base.STRICT_PROFILE else [0, 3, 4] if row["role_profile"] == base.DIRECT_PROFILE else None
            try:
                task_ids = json.loads(row["structurally_applicable_task_ids_json"])
            except json.JSONDecodeError as error:
                raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
                    f"{ERROR_TOKEN}:ROLE_TASK_IDS_JSON_INVALID:{event_id}"
                ) from error
            if task_ids != expected_ids or 3 not in task_ids:
                _fail("ROLE_EXACT5_APPLICABILITY_INVALID:" + event_id)
            applicability.update(task_ids)
        elif row["role_profile"] != base.ROLE_NOT_ESTABLISHED or row["canonical_mask_structural_labels_available"] != "false" or row["structurally_applicable_task_ids_json"] != "null":
            _fail("ROLELESS_ROW_FALSE_APPLICABILITY_NOT_UNKNOWN:" + event_id)
        if row["pre_geometry_authoritative"] != "false" or row["pre_geometry_training_target_available"] != "false":
            _fail("POST_TO_PRE_OR_PRE_ZERO_FILL_DETECTED:" + event_id)
    if applicability != Counter({0: 132, 1: 52, 2: 52, 3: 132, 4: 132}):
        _fail("CANONICAL_EXACT5_APPLICABILITY_COUNTS_INVALID")
    if len(CANONICAL_EXACT5_V1) != 5 or CANONICAL_EXACT5_V1[3][1:] != ("scaffold_only", "B3"):
        _fail("GLOBAL_CANONICAL_EXACT5_INVALID")

    expected_top = _top_pending_review_units_v1(root, reconciliation)
    if summary != _build_summary_v1(rows, expected_top):
        _fail("SUMMARY_NOT_EXACTLY_DERIVED_FROM_REFRESHED_ROWS_AND_FULL_QUEUE")
    geometry = summary["geometry"]
    if geometry != {
        "POST_sample_authoritative_count": 21,
        "POST_source_evidence_available_count": 867,
        "POST_to_PRE_promotion_performed": False,
        "POST_training_target_available_count": 17,
        "PRE_is_v1_hard_requirement": False,
        "PRE_sample_authoritative_count": 0,
        "PRE_source_evidence_available_count": 0,
        "PRE_training_target_available_count": 0,
        "PRE_zero_fill_performed": False,
    }:
        _fail("GLOBAL_PRE_POST_GEOMETRY_COUNTS_INVALID")

    identities: set[tuple[str, str]] = set()
    for binding in bindings:
        expected_keys = {"artifact_role", "path", "path_namespace", "byte_count", "sha256"}
        if "expected_executable" in binding:
            expected_keys.add("expected_executable")
        path = binding.get("path")
        namespace = binding.get("path_namespace")
        role = binding.get("artifact_role")
        if (
            type(binding) is not dict
            or set(binding) != expected_keys
            or type(path) is not str
            or not path
            or type(namespace) is not str
            or namespace not in {"repository_relative", "repository_parent_relative"}
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
            or type(role) is not str
            or not role
            or type(binding.get("byte_count")) is not int
            or binding["byte_count"] <= 0
            or type(binding.get("sha256")) is not str
            or not _SHA_PATTERN.fullmatch(binding["sha256"])
            or ("expected_executable" in binding and type(binding["expected_executable"]) is not bool)
        ):
            _fail("SEMANTIC_SOURCE_BINDING_INVALID")
        identity = (namespace, path)
        if identity in identities:
            _fail("SEMANTIC_SOURCE_BINDING_DUPLICATE")
        identities.add(identity)
    expected_bindings = _merge_semantic_bindings_v1(frozen.semantic_source_bindings, _verify_additive_sources(root))
    expected_count = len(frozen.semantic_source_bindings) + len(_ADDITIVE_SOURCE_SPECS_V1)
    if bindings != expected_bindings or len(bindings) != expected_count or expected_count != 144:
        _fail("SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6")
    if tuple(bindings[: len(frozen.semantic_source_bindings)]) != frozen.semantic_source_bindings:
        _fail("PREDECESSOR_SEMANTIC_BINDING_ORDER_CHANGED")

    census_digest = _sha256(_csv_bytes(rows))
    summary_digest = _sha256(_json_bytes(summary))
    bindings_digest = _sha256(_canonical_json(list(bindings)).encode("utf-8"))
    if _EXPECTED_REFRESHED_CENSUS_SHA256_V1 is not None and census_digest != _EXPECTED_REFRESHED_CENSUS_SHA256_V1:
        _fail("REFRESHED_CENSUS_EXACT_SHA256_INVALID")
    if _EXPECTED_REFRESHED_SUMMARY_SHA256_V1 is not None and summary_digest != _EXPECTED_REFRESHED_SUMMARY_SHA256_V1:
        _fail("REFRESHED_SUMMARY_EXACT_SHA256_INVALID")
    if _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1 is not None and bindings_digest != _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1:
        _fail("REFRESHED_SEMANTIC_BINDINGS_EXACT_SHA256_INVALID")
    return True


def _validate_text_payload(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("OUTPUT_UTF8_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
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
        result.append({"artifact_role": role, "path": relative.as_posix(), "byte_count": len(payload), "sha256": _sha256(payload)})
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
        {"artifact_role": "REFRESHED_CENSUS_CSV", "path": (OUTPUT_DIRECTORY_RELATIVE / CENSUS_FILE).as_posix(), "byte_count": len(census_payload), "sha256": _sha256(census_payload)},
        {"artifact_role": "REFRESHED_SUMMARY_JSON", "path": (OUTPUT_DIRECTORY_RELATIVE / SUMMARY_FILE).as_posix(), "byte_count": len(summary_payload), "sha256": _sha256(summary_payload)},
    ]
    predecessor_count = len(computation.semantic_source_bindings) - len(_ADDITIVE_SOURCE_SPECS_V1)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "candidate_inventory": {"exact_file_count": 7, "paths": list(EXACT7_PATHS_V1)},
        "candidate_contract_bindings": _candidate_contract_bindings_v1(root),
        "semantic_source_bindings": list(computation.semantic_source_bindings),
        "semantic_source_binding_count": len(computation.semantic_source_bindings),
        "predecessor_manifest_validation_binding": {
            "artifact_role": "PREDECESSOR_WITH_GD1_MANIFEST_VALIDATION_IDENTITY",
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
            "sha256": "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2",
            "expected_executable": False,
        },
        "derived_projection_contract_digests": {
            "refreshed_census_sha256": _EXPECTED_REFRESHED_CENSUS_SHA256_V1,
            "refreshed_summary_sha256": _EXPECTED_REFRESHED_SUMMARY_SHA256_V1,
            "semantic_source_bindings_sha256": _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1,
            "authority_created": False,
        },
        "output_inventory": {
            "exact_output_count": 3,
            "paths": [(OUTPUT_DIRECTORY_RELATIVE / name).as_posix() for name in (CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE)],
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
            "row_count": len(computation.rows),
            "column_count": len(CENSUS_COLUMNS_V1),
            "changed_event_count": len(SR2_EXACT4_EVENT_IDS_V1),
            "unchanged_event_count": len(computation.rows) - len(SR2_EXACT4_EVENT_IDS_V1),
            "authorized_overlay_field_count": len(_AUTHORIZED_SR2_OVERLAY_FIELDS_V1),
            "actual_changed_field_count_per_sr2_row": len(
                _AUTHORIZED_SR2_OVERLAY_FIELDS_V1
                - {"human_training_excluded"}
            ),
            "semantic_source_binding_count": len(computation.semantic_source_bindings),
            "predecessor_semantic_source_binding_count": predecessor_count,
            "additive_semantic_source_binding_count": len(_ADDITIVE_SOURCE_SPECS_V1),
            "semantic_identity_collision_count": 0,
            "source_role_collision_count": 0,
            "census_refreshed": True,
            "queue_refreshed": False,
            "next_review_started": False,
            "new_human_authority_created": False,
            "new_scientific_authority_created": False,
            "new_pair_authority_created": False,
            "new_role_authority_created": False,
            "formal_decision_read_directly": False,
            "formal_decision_bound_directly": False,
            "formal_validator_executed": False,
            "training_dataset_changed": False,
            "tensor_integration_performed": False,
            "training_started": False,
            "ready_for_training": False,
            "source_binding_v2_clean_from_birth": True,
            "new_numeric_POSIX_semantic_identity": False,
        },
        "authority_boundary": computation.summary["authority_boundary"],
    }
    manifest_payload = _json_bytes(manifest)
    _validate_text_payload(manifest_payload, MANIFEST_FILE)
    lowered = manifest_payload.decode("utf-8").lower()
    for token in ('"hostname"', '"pid"', '"timestamp"', '"head"', '"commit_subject"', '"ahead"', '"behind"', '"lifecycle_profile"'):
        if token in lowered:
            _fail("MANIFEST_LIFECYCLE_FIELD_FORBIDDEN")
    return {CENSUS_FILE: census_payload, SUMMARY_FILE: summary_payload, MANIFEST_FILE: manifest_payload}


def build_covapie_cumulative1000_current_global_readiness_artifacts_with_sr2_v1(
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
    computation = compute_covapie_cumulative1000_current_global_readiness_census_with_sr2_v1(root)
    return _build_artifacts_from_computation_v1(root, computation)


def _validate_materialization_destination_v1(target_root: Path) -> None:
    try:
        root_metadata = target_root.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
            f"{ERROR_TOKEN}:OUTPUT_ROOT_LSTAT_FAILED"
        ) from error
    if stat.S_ISLNK(root_metadata.st_mode):
        _fail("OUTPUT_ROOT_SYMLINK_FORBIDDEN")
    if not stat.S_ISDIR(root_metadata.st_mode):
        _fail("OUTPUT_ROOT_NOT_DIRECTORY")
    entries = tuple(target_root.iterdir())
    allowed = {CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE}
    unexpected = sorted(entry.name for entry in entries if entry.name not in allowed)
    if unexpected:
        _fail("OUTPUT_DIRECTORY_UNEXPECTED_ENTRY:" + unexpected[0])
    for entry in entries:
        metadata = entry.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("OUTPUT_ENTRY_NOT_REGULAR:" + entry.name)


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
            f"{ERROR_TOKEN}:OUTPUT_WRITE_FAILED:{path.name}"
        ) from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_sr2_v1(
    repo_root: Path,
    output_directory: Path | None = None,
) -> dict[str, bytes]:
    """Write only Exact3 after complete source and semantic validation."""

    root = repo_root.resolve()
    output = root / OUTPUT_DIRECTORY_RELATIVE if output_directory is None else Path(output_directory)
    _validate_materialization_destination_v1(output)
    artifacts = build_covapie_cumulative1000_current_global_readiness_artifacts_with_sr2_v1(root)
    try:
        output.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWithSR2Error(
            f"{ERROR_TOKEN}:OUTPUT_DIRECTORY_CREATE_FAILED"
        ) from error
    for filename in (CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE):
        _atomic_write(output / filename, artifacts[filename])
    return artifacts
