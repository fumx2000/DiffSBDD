"""Additive cumulative1000 readiness census successor for published 6OA Exact4.

This metadata-only owner consumes the published with-NWJ census, the published
6OA ingestion matrix, and the published with-6OA generic reconciliation.  It
deep-copies the frozen 1000 rows and overlays only the four exact 6OA event
identities.  The projection creates no new human, scientific, role, pair, mask,
geometry, tensor, admission, runtime, or training authority.
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

from . import covapie_6oa_completed_decision_ingestion_and_task_label_availability_v1 as ingestion
from . import covapie_completed_human_decision_reconciliation_v1 as generic
from . import covapie_completed_human_decision_reconciliation_with_6oa_v1 as reconciliation_owner
from . import covapie_cumulative1000_current_global_readiness_census_with_nwj_v1 as predecessor
from .covapie_source_binding_policy_v2 import SourceBindingPolicyV2Error, verify_bound_source_v2


__all__ = (
    "Cumulative1000CurrentGlobalReadinessCensusWith6OAError",
    "compute_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1",
    "validate_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1",
    "build_covapie_cumulative1000_current_global_readiness_artifacts_with_6oa_v1",
    "materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_6oa_v1",
)

SCHEMA_VERSION = "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1"
STAGE = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_6OA_V1"
ERROR_TOKEN = "COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_6OA_V1_ERROR"

OUTPUT_DIRECTORY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1"
)
CENSUS_FILE = "covapie_cumulative1000_current_global_readiness_census_with_6oa_v1.csv"
SUMMARY_FILE = "covapie_cumulative1000_current_global_readiness_summary_with_6oa_v1.json"
MANIFEST_FILE = "covapie_cumulative1000_current_global_readiness_manifest_with_6oa_v1.json"
PRODUCTION_RELATIVE = Path(
    "src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_6oa_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/check_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1.py"
)
TEST_RELATIVE = Path(
    "tests/test_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1.py"
)
GUIDE_RELATIVE = Path(
    "docs/covapie_cumulative1000_current_global_readiness_census_with_6oa_v1_guide.md"
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

SIX_OA_EXACT4_EVENT_IDS_V1 = ingestion.EXPECTED_EVENT_IDS
SIX_OA_EXACT4_RANKS_V1 = ingestion.EXPECTED_RANKS
SIX_OA_REVIEW_UNIT_ID_V1 = ingestion.EXPECTED_REVIEW_UNIT_ID
SIX_OA_HUMAN_DECISION_SOURCE = ingestion.FORMAL_DECISION_RELATIVE.as_posix()
SIX_OA_EVENT_MATRIX_RELATIVE = ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MATRIX
SIX_OA_EVENT_MATRIX_SOURCE = SIX_OA_EVENT_MATRIX_RELATIVE.as_posix()

PREDECESSOR_OWNER_RELATIVE = predecessor.PRODUCTION_RELATIVE
PREDECESSOR_CENSUS_RELATIVE = predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.CENSUS_FILE
PREDECESSOR_SUMMARY_RELATIVE = predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.SUMMARY_FILE
PREDECESSOR_MANIFEST_RELATIVE = predecessor.OUTPUT_DIRECTORY_RELATIVE / predecessor.MANIFEST_FILE
SIX_OA_RECONCILIATION_OWNER_RELATIVE = reconciliation_owner.SOURCE_RELATIVE
SIX_OA_RECONCILIATION_ARTIFACT_RELATIVE = reconciliation_owner.OUTPUT_RELATIVE
SIX_OA_INGESTION_OWNER_RELATIVE = ingestion.SOURCE_RELATIVE
PRIORITY_QUEUE_RELATIVE = predecessor.PRIORITY_QUEUE_RELATIVE

GVE_EXACT4_EVENT_IDS_V1 = predecessor.GVE_EXACT4_EVENT_IDS_V1
LCY_EXACT4_EVENT_IDS_V1 = predecessor.LCY_EXACT4_EVENT_IDS_V1
ZERO_D8_EXACT4_EVENT_IDS_V1 = predecessor.ZERO_D8_EXACT4_EVENT_IDS_V1
TP2_EXACT4_EVENT_IDS_V1 = predecessor.TP2_EXACT4_EVENT_IDS_V1
NEXT_PENDING_REVIEW_UNIT_ID_V1 = "COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4"
NEXT_PENDING_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:1F8M:A:CYS:191-:SG:F:PYR:CB",
    "COVAPIE_CYS_SG_EVENT_V1:1F8M:B:CYS:191-:SG:H:PYR:CB",
    "COVAPIE_CYS_SG_EVENT_V1:1F8M:C:CYS:191-:SG:J:PYR:CB",
    "COVAPIE_CYS_SG_EVENT_V1:1F8M:D:CYS:191-:SG:L:PYR:CB",
)

_AUTHORIZED_6OA_OVERLAY_FIELDS_V1 = frozenset(
    {
        "chemistry_authority_source",
        "chemistry_disposition",
        "current_global_status",
        "current_review_status",
        "future_training_admission_candidate",
        "human_review_authority_source",
        "human_review_completed",
        "human_training_excluded",
        "positive_authority_source",
        "reactive_pair_sample_authoritative",
        "task_relevance_authority_source",
        "task_relevance_disposition",
        "training_materialization_allowed_current_source",
        "training_use_disposition",
        "training_use_include",
        "role_partition_sample_authoritative",
        "role_profile",
        "canonical_mask_structural_labels_available",
        "structurally_applicable_task_ids_json",
    }
)
_AUTHORIZED_BUT_UNCHANGED_6OA_FIELDS_V1 = frozenset(
    {
        "future_training_admission_candidate",
        "human_training_excluded",
        "training_use_include",
    }
)
_ACTUAL_CHANGED_6OA_FIELDS_V1 = (
    _AUTHORIZED_6OA_OVERLAY_FIELDS_V1 - _AUTHORIZED_BUT_UNCHANGED_6OA_FIELDS_V1
)

_EXPECTED_GLOBAL_STATUS_COUNTS_V1 = dict(predecessor._EXPECTED_GLOBAL_STATUS_COUNTS_V1)
_EXPECTED_GLOBAL_STATUS_COUNTS_V1[generic.CURRENTLY_UNREVIEWED] = 167
_EXPECTED_GLOBAL_STATUS_COUNTS_V1[generic.COMPLETED_HUMAN_POSITIVE] = 123
_EXPECTED_GLOBAL_STATUS_COUNTS_V1[generic.COMPLETED_HUMAN_NEGATIVE] = 78
_EXPECTED_BOOLEAN_COUNTS_V1 = dict(predecessor._EXPECTED_BOOLEAN_COUNTS_V1)
_EXPECTED_BOOLEAN_COUNTS_V1.update(
    {
        "reactive_pair_sample_authoritative": 160,
        "role_partition_sample_authoritative": 152,
        "canonical_mask_structural_labels_available": 152,
        "human_training_excluded": 72,
        "training_use_include": 68,
        "future_training_admission_candidate": 51,
    }
)

_EXPECTED_REFRESHED_CENSUS_SHA256_V1: str | None = (
    "440bebc49aefd2a7b920063f5fca949f8f9930b76b6cca496bd8942b83d88a1b"
)
_EXPECTED_REFRESHED_SUMMARY_SHA256_V1: str | None = (
    "f3bbdae930e4115e0bf0a51119ad3c5863064cf1fa68670d2ea1e610983dccd8"
)
_EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1: str | None = (
    "1c0a356cecfeb47071e73b0506717e75a4ff652c9ee29bf165bae0bfc5cf06c0"
)

_SHA_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_ADDITIVE_SOURCE_SPECS_V1 = (
    (
        "PREDECESSOR_WITH_NWJ_CENSUS_OWNER", PREDECESSOR_OWNER_RELATIVE,
        "repository_relative", 75148,
        "aca86bfacf0811d3aca70a2c2d21e7ca8c1b2cb0382d847a03372339eec899a7", False,
    ),
    (
        "PREDECESSOR_WITH_NWJ_MATERIALIZED_CENSUS", PREDECESSOR_CENSUS_RELATIVE,
        "repository_relative", 553770,
        "5e527a258f8589677c71c5271f3d305540ace8d87e8b647282f02856fd356a9e", False,
    ),
    (
        "PREDECESSOR_WITH_NWJ_MATERIALIZED_SUMMARY", PREDECESSOR_SUMMARY_RELATIVE,
        "repository_relative", 21523,
        "a9dfa8d763c1a8c746f9ff9ec16d684a5dccfa581afd078090f2ab17a82c6bf4", False,
    ),
    (
        "6OA_RECONCILIATION_OWNER", SIX_OA_RECONCILIATION_OWNER_RELATIVE,
        "repository_relative", 38355,
        "bc9183796e973366b1edb6764ec79750d31d55685f366a855b5728c5f1316559", False,
    ),
    (
        "6OA_INGESTION_OWNER", SIX_OA_INGESTION_OWNER_RELATIVE,
        "repository_relative", 101282,
        "7cf21daa63459b7e6f2552ad0ba6371a88a39dfa7fa0aa1b1d9bbf448cbfaff4", False,
    ),
    (
        "6OA_EVENT_TASK_LABEL_AVAILABILITY", SIX_OA_EVENT_MATRIX_RELATIVE,
        "repository_relative", 9391,
        "1b74de80ea1cd1c9e030c9602a3b8925b523e826b67db9e21d07d2e7f856fcfa", False,
    ),
)
_PREDECESSOR_MANIFEST_SPEC_V1 = (
    81923,
    "504134d0e0a92b8ffe4147992b1c0869c5e2289eb9161d6b2bdf079f0a19911f",
    False,
)
_SIX_OA_RECONCILIATION_ARTIFACT_SPEC_V1 = (
    344196,
    "b050f0c49f4f7ce017b97051e80ac9bb4d2471198229ec4d79154486f29146e6",
    False,
)


class Cumulative1000CurrentGlobalReadinessCensusWith6OAError(ValueError):
    """Raised unless the 6OA successor is exactly source-derived."""


def _fail(reason: str) -> NoReturn:
    raise Cumulative1000CurrentGlobalReadinessCensusWith6OAError(f"{ERROR_TOKEN}:{reason}")


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
        raise Cumulative1000CurrentGlobalReadinessCensusWith6OAError(
            f"{ERROR_TOKEN}:SOURCE_READ_FAILED:{label}"
        ) from error


def _verify_bound(
    root: Path, role: str, relative: Path, namespace: str,
    byte_count: int, sha256: str, executable: bool,
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
        raise Cumulative1000CurrentGlobalReadinessCensusWith6OAError(
            f"{ERROR_TOKEN}:BOUND_SOURCE_REJECTED:{role}"
        ) from error


def _verify_additive_sources(root: Path) -> tuple[dict[str, object], ...]:
    bindings: list[dict[str, object]] = []
    for role, relative, namespace, byte_count, digest, executable in _ADDITIVE_SOURCE_SPECS_V1:
        _verify_bound(root, role, relative, namespace, byte_count, digest, executable)
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
    _verify_bound(
        root, "PREDECESSOR_WITH_NWJ_MANIFEST", PREDECESSOR_MANIFEST_RELATIVE,
        "repository_relative", *_PREDECESSOR_MANIFEST_SPEC_V1,
    )
    _verify_bound(
        root, "6OA_RECONCILIATION_ARTIFACT_VALIDATION_IDENTITY",
        SIX_OA_RECONCILIATION_ARTIFACT_RELATIVE, "repository_relative",
        *_SIX_OA_RECONCILIATION_ARTIFACT_SPEC_V1,
    )
    return tuple(bindings)


def _verify_predecessor_bindings(
    root: Path, bindings: Sequence[Mapping[str, object]],
) -> None:
    manifest = json.loads(
        _read_regular_file(root / PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_WITH_NWJ_MANIFEST")
    )
    manifested = manifest.get("semantic_source_bindings")
    digest = _sha256(_canonical_json(manifested).encode("utf-8"))
    if (
        type(manifested) is not list
        or tuple(manifested) != tuple(bindings)
        or len(manifested) != 180
        or digest != "f189c0e93cd30821f08e02205585ddd617c847816725a66cdb892de9dd34de70"
    ):
        _fail("PREDECESSOR_SEMANTIC_BINDINGS_NOT_MANIFEST_DERIVED_EXACT180")


def _validate_6oa_matrix_rows_v1(
    rows: Sequence[Mapping[str, str]],
) -> tuple[dict[str, str], ...]:
    normalized = tuple(dict(row) for row in rows)
    if (
        len(normalized) != 4
        or any(tuple(row) != ingestion.MATRIX_HEADER for row in normalized)
        or tuple(row["canonical_event_id"] for row in normalized) != SIX_OA_EXACT4_EVENT_IDS_V1
        or tuple(int(row["scaleup_rank"]) for row in normalized) != SIX_OA_EXACT4_RANKS_V1
        or len({row["canonical_event_id"] for row in normalized}) != 4
    ):
        _fail("6OA_EVENT_MATRIX_IDENTITY_NOT_EXACT4")
    expected_contexts = tuple(
        (str(item[2]), str(item[3]), str(item[4])) for item in ingestion.EXPECTED_EVENTS
    )
    actual_contexts = tuple(
        (row["protein_chain_or_asym"], row["ligand_chain_or_asym"], row["selected_connection_id"])
        for row in normalized
    )
    if actual_contexts != expected_contexts:
        _fail("6OA_EVENT_MATRIX_CONTEXT_DRIFT")
    actual_source_events = tuple(
        (
            row["canonical_event_id"], int(row["scaleup_rank"]),
            row["protein_chain_or_asym"], row["ligand_chain_or_asym"],
            row["selected_connection_id"], row["POST_distance_angstrom"],
            row["reported_POST_distance_angstrom"], row["geometry_outlier"] == "true",
        )
        for row in normalized
    )
    if actual_source_events != ingestion.EXPECTED_EVENTS:
        _fail("6OA_EVENT_MATRIX_FROZEN_EVENT_FIELDS_DRIFT")
    expected_cells = {
        "review_unit_id": SIX_OA_REVIEW_UNIT_ID_V1,
        "pdb_id": "4OU2",
        "ligand_component_id": "6OA",
        "completed_lane": ingestion.EXPECTED_COMPLETED_LANE,
        "legacy_completed_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
        "human_review_completed": "true",
        "source_formal_generation_domain_decision": ingestion.SOURCE_D2,
        "normalized_task_relevance_disposition": ingestion.NORMALIZED_TASK_RELEVANCE,
        "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
        "negative_chemistry": "false",
        "task_domain_negative": "true",
        "positive_generative_supervision_eligible": "false",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "C5",
        "pair_sample_authority": "true",
        "explicit_covalent_evidence": "true",
        "distance_only_inference": "false",
        "role_profile": ingestion.EXPECTED_ROLE_PROFILE,
        "role_sample_authority": "true",
        "warhead_atom_ids_json": _canonical_json(list(ingestion.WARHEAD_ATOMS)),
        "linker_atom_ids_json": _canonical_json(list(ingestion.LINKER_ATOMS)),
        "scaffold_atom_ids_json": _canonical_json(list(ingestion.SCAFFOLD_ATOMS)),
        "boundary_json": _canonical_json(ingestion.BOUNDARY),
        "minimal_seed_atom_ids_json": _canonical_json(list(ingestion.MINIMAL_SEED)),
        "primary_anchor": ingestion.PRIMARY_ANCHOR,
        "canonical_task_count": "5",
        "B3_present": "true",
        "sixth_task": "false",
        "structurally_applicable_task_ids_json": "[0,3,4]",
        "task_applicability_sample_authority": "true",
        "task_label_authority": "false",
        "authoritative_task_labels_created": "false",
        "event_task_label_rows_materialized": "false",
        "mask_tensor_targets_created": "false",
        "formal_event_training_use_decision": generic.TRAINING_NOT_APPLICABLE,
        "training_use_allowed": "false",
        "human_training_excluded": "false",
        "candidate_for_future_training_admission": "false",
        "future_training_admission_candidate": "false",
        "training_admitted": "false",
        "formal_training_admitted": "false",
        "training_materialization_allowed": "false",
        "tensor_target_created": "false",
        "model_supervision_usable": "false",
        "current_runtime_model_usable": "false",
        "POST_source_evidence_available": "true",
        "POST_geometry_training_authority": "false",
        "POST_geometry_training_target_created": "false",
        "supporting_adduct_source_graph_count": "0",
        "candidate_PRE_free_source_graph_count": "0",
        "mapping_count": "0",
        "PRE_source_mapping_status": ingestion.PRE_MAPPING_STATUS,
        "final_PRE_reaction_status": ingestion.PRE_STATUS,
        "PRE_authority": "false",
        "POST_to_PRE_copy": "false",
        "PRE_zero_fill": "false",
        "C5_O3_free_precursor_double_bond_authority": "false",
        "reusable_pair_authority": "false",
        "reusable_role_authority": "false",
        "reaction_family_authority": "false",
        "warhead_rule_authority": "false",
        "warhead_type_authority": "false",
        "parameter_update_authorization": "false",
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": "false",
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": "true",
        "READY_FOR_TRAINING": "false",
        "TRAINING_STARTED": "false",
    }
    semantic_names = [item[1] for item in CANONICAL_EXACT5_V1]
    aliases = [item[2] for item in CANONICAL_EXACT5_V1]
    for row in normalized:
        event_id = row["canonical_event_id"]
        if any(row[key] != value for key, value in expected_cells.items()):
            _fail("6OA_EVENT_MATRIX_SEMANTICS_INVALID:" + event_id)
        try:
            applicability = json.loads(row["canonical_task_applicability_json"])
        except json.JSONDecodeError as error:
            raise Cumulative1000CurrentGlobalReadinessCensusWith6OAError(
                f"{ERROR_TOKEN}:6OA_MATRIX_JSON_INVALID:{event_id}"
            ) from error
        if (
            len(applicability) != 5
            or [item["task_id"] for item in applicability] != list(range(5))
            or [item["semantic_long_name"] for item in applicability] != semantic_names
            or [item["display_alias"] for item in applicability] != aliases
            or [item["structurally_applicable"] for item in applicability]
            != [True, False, False, True, True]
            or applicability[3]["semantic_long_name"] != "scaffold_only"
            or json.loads(row["warhead_atom_ids_json"]) != list(ingestion.WARHEAD_ATOMS)
            or json.loads(row["linker_atom_ids_json"]) != []
            or json.loads(row["scaffold_atom_ids_json"]) != list(ingestion.SCAFFOLD_ATOMS)
            or json.loads(row["boundary_json"]) != ingestion.BOUNDARY
            or json.loads(row["minimal_seed_atom_ids_json"]) != list(ingestion.MINIMAL_SEED)
            or row["canonical_task_count"] != "5"
            or row["B3_present"] != "true"
            or row["sixth_task"] != "false"
        ):
            _fail("6OA_EVENT_MATRIX_EXACT5_BOUNDARY_INVALID:" + event_id)
    return normalized


def _load_and_validate_6oa_event_matrix_v1(root: Path) -> tuple[dict[str, str], ...]:
    payload = _read_regular_file(root / SIX_OA_EVENT_MATRIX_RELATIVE, "6OA_EVENT_MATRIX")
    if len(payload) != 9391 or _sha256(payload) != (
        "1b74de80ea1cd1c9e030c9602a3b8925b523e826b67db9e21d07d2e7f856fcfa"
    ):
        _fail("6OA_EVENT_MATRIX_BINDING_INVALID")
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWith6OAError(
            f"{ERROR_TOKEN}:6OA_EVENT_MATRIX_NOT_UTF8"
        ) from error
    if tuple(reader.fieldnames or ()) != ingestion.MATRIX_HEADER:
        _fail("6OA_EVENT_MATRIX_HEADER_INVALID")
    return _validate_6oa_matrix_rows_v1(tuple(dict(row) for row in reader))


def _validate_6oa_reconciliation_v1(root: Path) -> generic.ReconciliationResult:
    result = reconciliation_owner.reconcile_real_completed_human_decisions_with_6oa_v1(root)
    expected_summary = {
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
    if (
        result.review_summary != expected_summary
        or reconciliation_owner.SUCCESSOR_COVERAGE_SUMMARY != {
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
        or len(result.reconciled_rows) != 338
        or len(result.source_bindings) != 26
        or len(result.normalized_facts) != 147
        or len({binding.stable_identity for binding in result.source_bindings}) != 26
    ):
        _fail("6OA_RECONCILIATION_EXACT26_147_INVALID")
    target = set(SIX_OA_EXACT4_EVENT_IDS_V1)
    facts = [fact for fact in result.normalized_facts if fact.canonical_event_id in target]
    if len(facts) != 4 or any(
        fact.review_unit_id != SIX_OA_REVIEW_UNIT_ID_V1
        or fact.human_review_completed is not True
        or fact.legacy_completed_review_status != generic.COMPLETED_HUMAN_NEGATIVE
        or fact.task_relevance_disposition != generic.TASK_NOT_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_NOT_APPLICABLE
        or fact.human_training_excluded is not False
        or fact.source_binding_path != SIX_OA_HUMAN_DECISION_SOURCE
        for fact in facts
    ):
        _fail("6OA_RECONCILIATION_EXACT4_TASK_NEGATIVE_CHEMISTRY_POSITIVE_INVALID")
    target_rows = [row for row in result.reconciled_rows if row["canonical_event_id"] in target]
    if len(target_rows) != 4 or any(
        row["current_review_status"] != generic.COMPLETED_HUMAN_NEGATIVE
        for row in target_rows
    ):
        _fail("6OA_RECONCILIATION_TARGET_STATUS_INVALID")
    return result


def _assert_predecessor_6oa_state_v1(
    computation: base.Cumulative1000CurrentGlobalReadinessComputationV1, root: Path,
) -> None:
    if (
        len(computation.rows) != 1000
        or len(CENSUS_COLUMNS_V1) != 47
        or _csv_bytes(computation.rows)
        != _read_regular_file(root / PREDECESSOR_CENSUS_RELATIVE, "PREDECESSOR_CENSUS")
    ):
        _fail("PREDECESSOR_WITH_NWJ_CENSUS_IDENTITY_INVALID")
    target = set(SIX_OA_EXACT4_EVENT_IDS_V1)
    rows = [row for row in computation.rows if row["canonical_event_id"] in target]
    expected = {
        "ligand_component_id": "6OA",
        "current_global_status": generic.CURRENTLY_UNREVIEWED,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "human_review_completed": "false",
        "human_review_authority_source": PRIORITY_QUEUE_RELATIVE.as_posix(),
        "chemistry_disposition": base.CHEMISTRY_UNRESOLVED,
        "chemistry_authority_source": "",
        "task_relevance_disposition": base.TASK_UNRESOLVED,
        "task_relevance_authority_source": "",
        "training_use_disposition": base.TRAINING_UNRESOLVED,
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "role_profile": base.ROLE_NOT_ESTABLISHED,
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
        "human_training_excluded": "false",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "reactive_pair_training_target_available": "false",
        "formal_split_authoritative": "false",
        "formal_split": "",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "training_materialization_allowed_current_source": "",
        "positive_authority_source": "",
        "post_geometry_source_evidence_available": "true",
        "post_geometry_sample_authoritative": "false",
        "post_geometry_training_target_available": "false",
        "pre_geometry_authoritative": "false",
        "pre_geometry_training_target_available": "false",
        "feature_semantics_status": "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER",
    }
    if (
        len(rows) != 4
        or tuple(int(row["scaleup_rank"]) for row in rows) != SIX_OA_EXACT4_RANKS_V1
        or any(any(row[key] != value for key, value in expected.items()) for row in rows)
    ):
        _fail("PREDECESSOR_6OA_EXACT4_STATE_INVALID")


def _overlay_6oa_exact4_v1(
    predecessor_rows: Sequence[Mapping[str, str]],
    matrix_rows: Sequence[Mapping[str, str]],
    reconciliation: generic.ReconciliationResult,
) -> tuple[dict[str, str], ...]:
    matrix_by_event = {
        row["canonical_event_id"]: row for row in _validate_6oa_matrix_rows_v1(matrix_rows)
    }
    facts = {
        fact.canonical_event_id: fact
        for fact in reconciliation.normalized_facts
        if fact.canonical_event_id in matrix_by_event
    }
    if set(facts) != set(SIX_OA_EXACT4_EVENT_IDS_V1):
        _fail("6OA_RECONCILIATION_MATRIX_IDENTITY_MISMATCH")
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
            or row["review_unit_id"] != SIX_OA_REVIEW_UNIT_ID_V1
        ):
            _fail("6OA_MATRIX_PREDECESSOR_IDENTITY_MISMATCH:" + event_id)
        row.update(
            {
                "current_global_status": fact.legacy_completed_review_status,
                "current_review_status": fact.legacy_completed_review_status,
                "human_review_completed": "true",
                "human_review_authority_source": fact.source_binding_path,
                "chemistry_disposition": fact.chemistry_disposition,
                "chemistry_authority_source": SIX_OA_EVENT_MATRIX_SOURCE,
                "positive_authority_source": SIX_OA_EVENT_MATRIX_SOURCE,
                "task_relevance_disposition": fact.task_relevance_disposition,
                "task_relevance_authority_source": SIX_OA_EVENT_MATRIX_SOURCE,
                "training_use_disposition": fact.training_disposition,
                "human_training_excluded": matrix["human_training_excluded"],
                "reactive_pair_sample_authoritative": matrix["pair_sample_authority"],
                "role_partition_sample_authoritative": matrix["role_sample_authority"],
                "role_profile": matrix["role_profile"],
                "canonical_mask_structural_labels_available": matrix[
                    "task_applicability_sample_authority"
                ],
                "structurally_applicable_task_ids_json": matrix[
                    "structurally_applicable_task_ids_json"
                ],
                "training_use_include": matrix["training_use_allowed"],
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
    root: Path, reconciliation: generic.ReconciliationResult,
) -> list[dict[str, object]]:
    payload = _verify_bound(
        root, "FROZEN_PRIORITY_QUEUE", PRIORITY_QUEUE_RELATIVE, "repository_relative",
        50116, "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2", False,
    )
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    queue_rows = [dict(row) for row in reader]
    if len(queue_rows) != 131:
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
    if len(candidates) != 101 or any(
        unit == SIX_OA_REVIEW_UNIT_ID_V1 for _n, _p, unit, _row, _s in candidates
    ):
        _fail("CURRENT_PENDING_REVIEW_UNIT_SET_INVALID")
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
        "raw_priority_rank": 30,
        "review_unit_id": NEXT_PENDING_REVIEW_UNIT_ID_V1,
        "event_count": 4,
        "pdb_ids": ["1F8M"],
        "ligand_component_ids": ["PYR"],
        "full_coordinate_count": 4,
        "exact_pair_count": 4,
        "ccd_complete_count": 4,
        "post_source_evidence_count": 4,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
    }
    next_events = tuple(
        row["canonical_event_id"]
        for row in reconciliation.reconciled_rows
        if row["raw_review_unit_id"] == NEXT_PENDING_REVIEW_UNIT_ID_V1
    )
    if not top or top[0] != expected_next or next_events != NEXT_PENDING_EVENT_IDS_V1:
        _fail("NEXT_PENDING_SOURCE_DRIFT")
    return top


def _event_set(rows: Sequence[Mapping[str, str]], field: str, value: str) -> set[str]:
    return {row["canonical_event_id"] for row in rows if row[field] == value}


def _build_summary_v1(
    rows: Sequence[Mapping[str, str]], top_pending: list[dict[str, object]],
) -> dict[str, Any]:
    summary = deepcopy(predecessor._build_summary_v1(rows, top_pending))

    def disposition(values: set[str]) -> dict[str, object]:
        return {"count": len(values), "event_set_sha256": _event_set_sha256(values)}

    def count_true(field: str, population: Sequence[Mapping[str, str]] = rows) -> int:
        return sum(row[field] == "true" for row in population)

    chemistry_positive = _event_set(rows, "chemistry_disposition", base.CHEMISTRY_POSITIVE)
    chemistry_negative = _event_set(rows, "chemistry_disposition", base.CHEMISTRY_NEGATIVE)
    chemistry_not_established = _event_set(
        rows, "chemistry_disposition", base.CHEMISTRY_NOT_ESTABLISHED
    )
    chemistry_unresolved = _event_set(rows, "chemistry_disposition", base.CHEMISTRY_UNRESOLVED)
    task_relevant = _event_set(rows, "task_relevance_disposition", base.TASK_RELEVANT)
    task_not_relevant = _event_set(rows, "task_relevance_disposition", base.TASK_NOT_RELEVANT)
    task_unresolved = _event_set(rows, "task_relevance_disposition", base.TASK_UNRESOLVED)
    training_include = _event_set(rows, "training_use_disposition", generic.TRAINING_INCLUDE)
    training_exclude = _event_set(rows, "training_use_disposition", generic.TRAINING_EXCLUDE)
    training_not_applicable = _event_set(
        rows, "training_use_disposition", generic.TRAINING_NOT_APPLICABLE
    )
    training_unresolved = _event_set(rows, "training_use_disposition", base.TRAINING_UNRESOLVED)
    positive_rows = [row for row in rows if row["canonical_event_id"] in chemistry_positive]
    include_rows = [row for row in rows if row["canonical_event_id"] in training_include]
    missing_tensor_rows = [
        row for row in positive_rows if row["reactive_pair_training_target_available"] == "false"
    ]
    orthogonal = {
        row["canonical_event_id"]
        for row in rows
        if (
            row["task_relevance_disposition"], row["chemistry_disposition"],
            row["training_use_disposition"],
        ) == (
            generic.TASK_NOT_RELEVANT, generic.CHEMISTRY_POSITIVE,
            generic.TRAINING_NOT_APPLICABLE,
        )
    }

    summary["schema_version"] = SCHEMA_VERSION
    summary["stage"] = STAGE
    summary["refresh_delta"] = {
        "frozen_predecessor_positive_count": 156,
        "6OA_exact4_delta_count": 4,
        "refreshed_positive_count": len(chemistry_positive),
        "frozen_predecessor_training_include_count": 68,
        "refreshed_training_include_count": len(training_include),
        "frozen_predecessor_training_exclude_count": 72,
        "refreshed_training_exclude_count": len(training_exclude),
        "frozen_predecessor_future_candidate_count": 51,
        "refreshed_future_candidate_count": count_true("future_training_admission_candidate"),
        "changed_event_count": 4,
        "unchanged_event_count": 996,
        "derived_refresh_not_new_authority": True,
    }
    global_counts = Counter(row["current_global_status"] for row in rows)
    summary["global_status_distribution"]["counts"] = {
        status: global_counts[status] for status in base.GLOBAL_STATUSES_V1
    }
    priority_rows = [row for row in rows if row["priority_review_in_scope"] == "true"]
    review_counts = Counter(row["current_review_status"] for row in priority_rows)
    units_by_status: dict[str, set[str]] = defaultdict(set)
    for row in priority_rows:
        units_by_status[row["current_review_status"]].add(row["review_unit_id"])
    completed_units = (
        units_by_status[generic.COMPLETED_HUMAN_POSITIVE]
        | units_by_status[generic.COMPLETED_HUMAN_NEGATIVE]
    )
    pending_units = (
        units_by_status[generic.CURRENTLY_UNREVIEWED]
        | units_by_status[generic.CURRENTLY_IN_PROGRESS]
    )
    summary["human_review"] = {
        "priority_review_population_event_count": len(priority_rows),
        "review_unit_count": len({row["review_unit_id"] for row in priority_rows}),
        "completed_event_count": review_counts[generic.COMPLETED_HUMAN_POSITIVE]
        + review_counts[generic.COMPLETED_HUMAN_NEGATIVE],
        "completed_unit_count": len(completed_units),
        "completed_positive_event_count": review_counts[generic.COMPLETED_HUMAN_POSITIVE],
        "completed_positive_unit_count": len(units_by_status[generic.COMPLETED_HUMAN_POSITIVE]),
        "completed_negative_event_count": review_counts[generic.COMPLETED_HUMAN_NEGATIVE],
        "completed_negative_unit_count": len(units_by_status[generic.COMPLETED_HUMAN_NEGATIVE]),
        "unreviewed_event_count": review_counts[generic.CURRENTLY_UNREVIEWED],
        "unreviewed_unit_count": len(units_by_status[generic.CURRENTLY_UNREVIEWED]),
        "in_progress_event_count": review_counts[generic.CURRENTLY_IN_PROGRESS],
        "in_progress_unit_count": len(units_by_status[generic.CURRENTLY_IN_PROGRESS]),
        "pending_event_count": review_counts[generic.CURRENTLY_UNREVIEWED]
        + review_counts[generic.CURRENTLY_IN_PROGRESS],
        "current_pending_review_unit_count": len(pending_units),
    }
    source_composition = dict(summary["chemistry"]["positive_source_composition"])
    source_composition["6OA"] = sum(
        row["positive_authority_source"] == SIX_OA_EVENT_MATRIX_SOURCE for row in rows
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
            "sample_level_authoritative_pair_count": count_true(
                "reactive_pair_sample_authoritative"
            ),
            "6oa_sample_authority_contribution_count": sum(
                row["positive_authority_source"] == SIX_OA_EVENT_MATRIX_SOURCE
                and row["reactive_pair_sample_authoritative"] == "true" for row in rows
            ),
            "6oa_training_target_contribution_count": sum(
                row["positive_authority_source"] == SIX_OA_EVENT_MATRIX_SOURCE
                and row["reactive_pair_training_target_available"] == "true" for row in rows
            ),
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
            "role_partition_sample_authoritative_count": count_true(
                "role_partition_sample_authoritative"
            ),
            "role_profile_counts": {
                base.STRICT_PROFILE: profile_counts[base.STRICT_PROFILE],
                base.DIRECT_PROFILE: profile_counts[base.DIRECT_PROFILE],
                "other": sum(
                    value for profile, value in profile_counts.items()
                    if profile not in {base.STRICT_PROFILE, base.DIRECT_PROFILE}
                ),
            },
            "canonical_mask_structural_labels_available_count": count_true(
                "canonical_mask_structural_labels_available"
            ),
            "all_five_structurally_applicable_count": sum(
                row["structurally_applicable_task_ids_json"] == "[0,1,2,3,4]" for row in rows
            ),
            "direct_profile_A_B3_C_count": sum(
                row["structurally_applicable_task_ids_json"] == "[0,3,4]" for row in rows
            ),
            "unknown_role_row_count": sum(
                row["role_partition_sample_authoritative"] == "false" for row in rows
            ),
        }
    )
    for task in summary["canonical_exact5"]["tasks"]:
        task["structurally_applicable_authoritative_role_count"] = applicability_counts[
            task["task_id"]
        ]
    summary["orthogonal_task_negative_chemistry_positive"] = {
        "task_negative_chemistry_positive_population_count": len(orthogonal),
        "gve_orthogonal_population_count": len(set(GVE_EXACT4_EVENT_IDS_V1) & orthogonal),
        "lcy_orthogonal_population_count": len(set(LCY_EXACT4_EVENT_IDS_V1) & orthogonal),
        "0d8_orthogonal_population_count": len(set(ZERO_D8_EXACT4_EVENT_IDS_V1) & orthogonal),
        "tp2_orthogonal_population_count": len(set(TP2_EXACT4_EVENT_IDS_V1) & orthogonal),
        "6oa_orthogonal_population_count": len(set(SIX_OA_EXACT4_EVENT_IDS_V1) & orthogonal),
        "task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_plus_6oa_exact20": True,
    }
    summary["training_stage"].update(
        {
            "training_use_include_count": len(training_include),
            "future_training_admission_candidate_count": count_true(
                "future_training_admission_candidate"
            ),
            "current_runtime_model_usable_count": count_true("current_runtime_model_usable"),
            "formal_training_admitted_count": count_true("formal_training_admitted"),
            "ready_for_formal_training_event_count": 0,
        }
    )
    missing_source_composition = dict(
        summary["blockers"]["missing_tensor_integration"]["missing_source_composition"]
    )
    missing_source_composition["6OA"] = sum(
        row["positive_authority_source"] == SIX_OA_EVENT_MATRIX_SOURCE
        for row in missing_tensor_rows
    )
    summary["blockers"] = {
        "non_exclusive_counts_must_not_be_summed": True,
        "population_sizes": {
            "chemistry_positive_population_count": len(positive_rows),
            "training_include_population_count": len(include_rows),
        },
        "chemistry_unresolved": {"all_1000": len(chemistry_unresolved)},
        "pair_authority_absent": {
            "all_1000": sum(row["reactive_pair_sample_authoritative"] == "false" for row in rows),
            "within_chemistry_positive": sum(
                row["reactive_pair_sample_authoritative"] == "false" for row in positive_rows
            ),
        },
        "role_authority_absent": {
            "all_1000": sum(row["role_partition_sample_authoritative"] == "false" for row in rows),
            "within_chemistry_positive": sum(
                row["role_partition_sample_authoritative"] == "false" for row in positive_rows
            ),
        },
        "human_training_exclusion": {
            "within_chemistry_positive": sum(
                row["human_training_excluded"] == "true" for row in positive_rows
            )
        },
        "missing_split_authority": {
            "within_chemistry_positive": sum(
                row["formal_split_authoritative"] == "false" for row in positive_rows
            ),
            "within_training_include": sum(
                row["formal_split_authoritative"] == "false" for row in include_rows
            ),
        },
        "missing_tensor_integration": {
            "within_chemistry_positive": len(missing_tensor_rows),
            "within_training_include": sum(
                row["reactive_pair_training_target_available"] == "false" for row in include_rows
            ),
            "all_missing_are_training_excluded_population": all(
                row["training_use_disposition"] == generic.TRAINING_EXCLUDE
                for row in missing_tensor_rows
            ),
            "missing_source_composition": missing_source_composition,
        },
        "missing_POST_training_authority": {
            "within_chemistry_positive": sum(
                row["post_geometry_training_target_available"] == "false" for row in positive_rows
            ),
            "within_training_include": sum(
                row["post_geometry_training_target_available"] == "false" for row in include_rows
            ),
        },
        "missing_training_admission": {
            "within_chemistry_positive": sum(
                row["formal_training_admitted"] == "false" for row in positive_rows
            ),
            "within_training_include": sum(
                row["formal_training_admitted"] == "false" for row in include_rows
            ),
        },
        "feature_semantics_pending": {"within_chemistry_positive": len(positive_rows)},
    }
    summary["top_pending_review_units_by_event_yield"] = top_pending
    next_pending = top_pending[0]
    boundary = summary["authority_boundary"]
    boundary.update(
        {
            "next_priority_review_unit": next_pending["review_unit_id"],
            "next_priority_review_ligand": "PYR",
            "next_priority_review_pdb": "1F8M",
            "next_priority_review_event_count": next_pending["event_count"],
            "next_priority_review_current_pending_rank": next_pending["rank"],
            "next_priority_review_raw_priority_rank": next_pending["raw_priority_rank"],
            "6OA_REVIEW_COMPLETED": True,
            "6OA_RECONCILIATION_CONSUMED": True,
            "READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION": True,
            "READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_PREPARATION": True,
            "NEXT_REVIEW_STARTED": False,
            "next_review_started": False,
            "CURRENT_GLOBAL_RECONCILIATION_COMPLETE": True,
            "CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE": True,
            "CENSUS_REFRESH": True,
            "CENSUS_REFRESH_PERFORMED": True,
            "census_refreshed": True,
            "QUEUE_REFRESH": False,
            "QUEUE_REFRESH_PERFORMED": False,
            "PYR_REVIEW_STATE_CREATED": False,
            "priority_queue_file_modified": False,
            "priority_queue_file_created": False,
            "READY_FOR_EXTERNAL_REVIEW": True,
            "READY_FOR_TRAINING": False,
            "READY_FOR_FORMAL_TRAINING": False,
            "TRAINING_STARTED": False,
            "training_started": False,
            "new_human_authority_created": False,
            "new_scientific_authority_created": False,
            "new_chemistry_authority_created": False,
            "new_pair_authority_created": False,
            "new_role_authority_created": False,
            "new_reusable_authority_created": False,
            "NEW_HUMAN_AUTHORITY_CREATED": False,
            "NEW_SCIENTIFIC_AUTHORITY_CREATED": False,
            "NEW_CHEMISTRY_AUTHORITY_CREATED": False,
            "NEW_PAIR_AUTHORITY_CREATED": False,
            "NEW_ROLE_AUTHORITY_CREATED": False,
            "NEW_REUSABLE_AUTHORITY_CREATED": False,
            "TASK_LABEL_AUTHORITY": False,
            "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
            "MASK_TENSOR_TARGETS_CREATED": False,
            "FORMAL_TRAINING_ADMITTED": False,
            "TRAINING_ADMISSION_CREATED": False,
            "TRAINING_MATERIALIZATION_ALLOWED": False,
            "PARAMETER_UPDATE_AUTHORIZATION": False,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "STEP12D_STATUS": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
            "derived_refresh_not_new_authority": True,
            "formal_decision_read_directly": False,
            "formal_decision_bound_directly": False,
            "formal_validator_executed": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
            "feature_semantics_audit_performed": False,
            "6OA_CENSUS_SOURCE_BINDING_V2_CLEAN_FROM_BIRTH": True,
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
        len(merged) != 186
        or len(set(identities)) != 186
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
    root = repo_root.resolve()
    additive_bindings = _verify_additive_sources(root)
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_nwj_v1(root)
    _assert_predecessor_6oa_state_v1(frozen, root)
    _verify_predecessor_bindings(root, frozen.semantic_source_bindings)
    reconciliation = _validate_6oa_reconciliation_v1(root)
    matrix_rows = _load_and_validate_6oa_event_matrix_v1(root)
    rows = _overlay_6oa_exact4_v1(frozen.rows, matrix_rows, reconciliation)
    top_pending = _top_pending_review_units_v1(root, reconciliation)
    summary = _build_summary_v1(rows, top_pending)
    bindings = _merge_semantic_bindings_v1(frozen.semantic_source_bindings, additive_bindings)
    computation = base.Cumulative1000CurrentGlobalReadinessComputationV1(
        rows=rows, summary=summary, semantic_source_bindings=bindings
    )
    validate_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1(
        computation,
        repo_root=root,
        predecessor_computation=frozen,
        reconciliation_result=reconciliation,
        matrix_rows=matrix_rows,
    )
    return computation, frozen, reconciliation, matrix_rows


def compute_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1(
    repo_root: Path,
) -> base.Cumulative1000CurrentGlobalReadinessComputationV1:
    """Compute the additive 6OA successor entirely from frozen published sources."""

    return _compute_components_v1(repo_root)[0]


def _assert_no_stale_summary_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if (
                key == "within_positive_132"
                or "population_exactly_gve_plus_lcy_plus_0d8_exact12" in key
                or "population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_exact16" in key
                or re.fullmatch(r"within_(?:positive|include)_\d+", key)
            ):
                _fail("SUMMARY_POPULATION_CODED_STALE_KEY:" + key)
            _assert_no_stale_summary_keys(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_stale_summary_keys(item)


def validate_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1(
    computation: object,
    *,
    repo_root: Path | None = None,
    predecessor_computation: base.Cumulative1000CurrentGlobalReadinessComputationV1 | None = None,
    reconciliation_result: generic.ReconciliationResult | None = None,
    matrix_rows: Sequence[Mapping[str, str]] | None = None,
) -> bool:
    """Fail closed on every 6OA identity, authority, mask, and training boundary."""

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
        len(_AUTHORIZED_6OA_OVERLAY_FIELDS_V1) != 19
        or len(_AUTHORIZED_BUT_UNCHANGED_6OA_FIELDS_V1) != 3
        or len(_ACTUAL_CHANGED_6OA_FIELDS_V1) != 16
        or _AUTHORIZED_BUT_UNCHANGED_6OA_FIELDS_V1 - _AUTHORIZED_6OA_OVERLAY_FIELDS_V1
    ):
        _fail("AUTHORIZED_6OA_OVERLAY_CONTRACT_INVALID")

    root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    frozen = predecessor_computation or predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_nwj_v1(root)
    reconciliation = reconciliation_result or _validate_6oa_reconciliation_v1(root)
    validated_matrix = (
        _validate_6oa_matrix_rows_v1(matrix_rows)
        if matrix_rows is not None else _load_and_validate_6oa_event_matrix_v1(root)
    )
    _assert_predecessor_6oa_state_v1(frozen, root)
    _verify_predecessor_bindings(root, frozen.semantic_source_bindings)

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
            raise Cumulative1000CurrentGlobalReadinessCensusWith6OAError(
                f"{ERROR_TOKEN}:CENSUS_RANK_INVALID:{event_id}"
            ) from error
    if ranks != list(range(1, 1001)):
        _fail("CENSUS_RANK_GAP_OR_ORDER_INVALID")

    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in rows}
    exact4 = set(SIX_OA_EXACT4_EVENT_IDS_V1)
    if set(before) != set(after):
        _fail("CENSUS_EVENT_SET_IDENTITY_INVALID")
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    if changed != exact4 or any(
        before[event_id] != after[event_id] for event_id in set(before) - exact4
    ):
        _fail("PREDECESSOR_DELTA_NOT_EXACT_6OA_EXACT4")
    expected_after = {
        "current_global_status": generic.COMPLETED_HUMAN_NEGATIVE,
        "current_review_status": generic.COMPLETED_HUMAN_NEGATIVE,
        "human_review_completed": "true",
        "human_review_authority_source": SIX_OA_HUMAN_DECISION_SOURCE,
        "chemistry_disposition": generic.CHEMISTRY_POSITIVE,
        "chemistry_authority_source": SIX_OA_EVENT_MATRIX_SOURCE,
        "positive_authority_source": SIX_OA_EVENT_MATRIX_SOURCE,
        "task_relevance_disposition": generic.TASK_NOT_RELEVANT,
        "task_relevance_authority_source": SIX_OA_EVENT_MATRIX_SOURCE,
        "training_use_disposition": generic.TRAINING_NOT_APPLICABLE,
        "human_training_excluded": "false",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "training_materialization_allowed_current_source": "false",
        "reactive_pair_sample_authoritative": "true",
        "reactive_pair_training_target_available": "false",
        "role_partition_sample_authoritative": "true",
        "role_profile": base.DIRECT_PROFILE,
        "canonical_mask_structural_labels_available": "true",
        "structurally_applicable_task_ids_json": "[0,3,4]",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "post_geometry_sample_authoritative": "false",
        "post_geometry_training_target_available": "false",
        "pre_geometry_authoritative": "false",
        "pre_geometry_training_target_available": "false",
    }
    for event_id in SIX_OA_EXACT4_EVENT_IDS_V1:
        changed_fields = {
            field for field in CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        }
        unchanged_authorized = {
            field for field in _AUTHORIZED_6OA_OVERLAY_FIELDS_V1
            if before[event_id][field] == after[event_id][field]
        }
        if changed_fields != _ACTUAL_CHANGED_6OA_FIELDS_V1:
            _fail("6OA_CHANGED_FIELD_SET_NOT_EXACT16:" + event_id)
        if unchanged_authorized != _AUTHORIZED_BUT_UNCHANGED_6OA_FIELDS_V1:
            _fail("6OA_AUTHORIZED_BUT_UNCHANGED_SET_NOT_EXACT3:" + event_id)
        if any(after[event_id][field] != value for field, value in expected_after.items()):
            _fail("6OA_REFRESHED_SEMANTICS_INVALID:" + event_id)

    orthogonal = {
        row["canonical_event_id"] for row in rows
        if (
            row["task_relevance_disposition"], row["chemistry_disposition"],
            row["training_use_disposition"],
        ) == (
            generic.TASK_NOT_RELEVANT, generic.CHEMISTRY_POSITIVE,
            generic.TRAINING_NOT_APPLICABLE,
        )
    }
    expected_orthogonal = (
        set(GVE_EXACT4_EVENT_IDS_V1) | set(LCY_EXACT4_EVENT_IDS_V1)
        | set(ZERO_D8_EXACT4_EVENT_IDS_V1) | set(TP2_EXACT4_EVENT_IDS_V1)
        | exact4
    )
    if orthogonal != expected_orthogonal or len(orthogonal) != 20:
        _fail("TASK_NEGATIVE_CHEMISTRY_POSITIVE_POPULATION_NOT_EXACT20")
    legacy = {
        row["canonical_event_id"] for row in rows
        if (
            row["task_relevance_disposition"], row["chemistry_disposition"],
            row["training_use_disposition"],
        ) == (
            generic.TASK_NOT_RELEVANT, generic.CHEMISTRY_NOT_ESTABLISHED,
            generic.TRAINING_NOT_APPLICABLE,
        )
    }
    if len(legacy) != 90:
        _fail("LEGACY_TASK_NEGATIVE_POPULATION_NOT_EXACT90")
    matrix_by_event = {row["canonical_event_id"]: row for row in validated_matrix}
    for row in rows:
        event_id = row["canonical_event_id"]
        chemistry = row["chemistry_disposition"]
        task = row["task_relevance_disposition"]
        training = row["training_use_disposition"]
        if training == generic.TRAINING_EXCLUDE and chemistry != generic.CHEMISTRY_POSITIVE:
            _fail("TRAINING_EXCLUDE_WITHOUT_POSITIVE_CHEMISTRY:" + event_id)
        if task == generic.TASK_NOT_RELEVANT and training != generic.TRAINING_NOT_APPLICABLE:
            _fail("TASK_NOT_RELEVANT_TRAINING_INVALID:" + event_id)
        if event_id in exact4:
            matrix = matrix_by_event[event_id]
            if (
                matrix["chemistry_disposition"] != chemistry
                or matrix["source_formal_generation_domain_decision"] != "OUT_OF_DOMAIN"
                or matrix["normalized_task_relevance_disposition"] != task
                or task != generic.TASK_NOT_RELEVANT
                or matrix["role_profile"] != base.DIRECT_PROFILE
                or matrix["structurally_applicable_task_ids_json"] != "[0,3,4]"
            ):
                _fail("6OA_MATRIX_CENSUS_SEMANTIC_MISMATCH:" + event_id)

    if Counter(row["current_global_status"] for row in rows) != Counter(
        _EXPECTED_GLOBAL_STATUS_COUNTS_V1
    ):
        _fail("CENSUS_GLOBAL_STATUS_DISTRIBUTION_INVALID")
    if Counter(row["chemistry_disposition"] for row in rows) != Counter(
        {"POSITIVE": 160, "NOT_ESTABLISHED": 90, "UNRESOLVED": 750}
    ):
        _fail("CENSUS_CHEMISTRY_DISTRIBUTION_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter(
        {"RELEVANT": 141, "NOT_RELEVANT": 110, "UNRESOLVED": 749}
    ):
        _fail("CENSUS_TASK_DISTRIBUTION_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter(
        {
            "INCLUDE": 68, "EXCLUDE_FROM_TRAINING_ONLY": 72,
            "NOT_APPLICABLE": 110, "UNRESOLVED": 750,
        }
    ):
        _fail("CENSUS_TRAINING_DISTRIBUTION_INVALID")
    for field, expected in _EXPECTED_BOOLEAN_COUNTS_V1.items():
        if sum(row[field] == "true" for row in rows) != expected:
            _fail("CENSUS_BOOLEAN_COUNT_INVALID:" + field)
    profiles = Counter(
        row["role_profile"] for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    )
    if profiles != Counter({base.DIRECT_PROFILE: 96, base.STRICT_PROFILE: 56}):
        _fail("CENSUS_ROLE_PROFILE_DISTRIBUTION_INVALID")
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
    if applicability != Counter({0: 152, 1: 56, 2: 56, 3: 152, 4: 152}):
        _fail("CANONICAL_EXACT5_APPLICABILITY_COUNTS_INVALID")
    if (
        len(CANONICAL_EXACT5_V1) != 5
        or CANONICAL_EXACT5_V1[3][1:] != ("scaffold_only", "B3")
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_INVALID")
    geometry = {
        field: sum(row[field] == "true" for row in rows)
        for field in (
            "post_geometry_source_evidence_available",
            "post_geometry_sample_authoritative",
            "post_geometry_training_target_available",
            "pre_geometry_authoritative",
            "pre_geometry_training_target_available",
        )
    }
    if geometry != {
        "post_geometry_source_evidence_available": 867,
        "post_geometry_sample_authoritative": 21,
        "post_geometry_training_target_available": 17,
        "pre_geometry_authoritative": 0,
        "pre_geometry_training_target_available": 0,
    }:
        _fail("GLOBAL_PRE_POST_GEOMETRY_COUNTS_INVALID")

    expected_top = _top_pending_review_units_v1(root, reconciliation)
    if summary != _build_summary_v1(rows, expected_top):
        _fail("SUMMARY_NOT_EXACTLY_SOURCE_DERIVED")
    _assert_no_stale_summary_keys(summary)
    blockers = summary["blockers"]
    expected_blockers = {
        "pair_authority_absent": {"all_1000": 840, "within_chemistry_positive": 0},
        "role_authority_absent": {"all_1000": 848, "within_chemistry_positive": 8},
        "human_training_exclusion": {"within_chemistry_positive": 72},
        "missing_split_authority": {
            "within_chemistry_positive": 119, "within_training_include": 43,
        },
        "missing_POST_training_authority": {
            "within_chemistry_positive": 143, "within_training_include": 51,
        },
        "missing_training_admission": {
            "within_chemistry_positive": 155, "within_training_include": 63,
        },
        "feature_semantics_pending": {"within_chemistry_positive": 160},
    }
    if any(blockers[key] != value for key, value in expected_blockers.items()):
        _fail("SUMMARY_BLOCKER_COUNTS_INVALID")
    tensor = blockers["missing_tensor_integration"]
    if (
        blockers["chemistry_unresolved"] != {"all_1000": 750}
        or tensor["within_chemistry_positive"] != 119
        or tensor["within_training_include"] != 39
        or tensor["missing_source_composition"].get("6OA") != 4
        or summary["chemistry"]["positive_source_composition"].get("6OA") != 4
        or "6OA" in summary["training_stage"]["future_candidate_source_composition"]
        or summary["reactive_pair"]["6oa_sample_authority_contribution_count"] != 4
        or summary["reactive_pair"]["6oa_training_target_contribution_count"] != 0
    ):
        _fail("SUMMARY_6OA_SOURCE_COMPOSITION_INVALID")

    expected_bindings = _merge_semantic_bindings_v1(
        frozen.semantic_source_bindings, _verify_additive_sources(root)
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
        and bindings_digest != _EXPECTED_REFRESHED_SEMANTIC_SOURCE_BINDINGS_SHA256_V1
    ):
        _fail("REFRESHED_SEMANTIC_BINDINGS_EXACT_SHA256_INVALID")
    return True


def _validate_text_payload(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("OUTPUT_UTF8_BOM_FORBIDDEN:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWith6OAError(
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
    root: Path, computation: base.Cumulative1000CurrentGlobalReadinessComputationV1,
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
            "artifact_role": "PREDECESSOR_WITH_NWJ_MANIFEST_VALIDATION_IDENTITY",
            "path": PREDECESSOR_MANIFEST_RELATIVE.as_posix(),
            "path_namespace": "repository_relative",
            "byte_count": _PREDECESSOR_MANIFEST_SPEC_V1[0],
            "sha256": _PREDECESSOR_MANIFEST_SPEC_V1[1],
            "expected_executable": _PREDECESSOR_MANIFEST_SPEC_V1[2],
        },
        "6oa_reconciliation_artifact_validation_binding": {
            "artifact_role": "6OA_RECONCILIATION_ARTIFACT_VALIDATION_IDENTITY",
            "path": SIX_OA_RECONCILIATION_ARTIFACT_RELATIVE.as_posix(),
            "path_namespace": "repository_relative",
            "byte_count": _SIX_OA_RECONCILIATION_ARTIFACT_SPEC_V1[0],
            "sha256": _SIX_OA_RECONCILIATION_ARTIFACT_SPEC_V1[1],
            "expected_executable": _SIX_OA_RECONCILIATION_ARTIFACT_SPEC_V1[2],
            "computational_source": False,
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
            "changed_event_count": 4,
            "unchanged_event_count": 996,
            "authorized_overlay_field_count": 19,
            "authorized_but_unchanged_field_count": 3,
            "actual_changed_field_count_per_6oa_row": 16,
            "semantic_source_binding_count": 186,
            "predecessor_semantic_source_binding_count": 180,
            "additive_semantic_source_binding_count": 6,
            "semantic_identity_collision_count": 0,
            "source_role_collision_count": 0,
            "legacy_task_negative_count": 90,
            "gve_orthogonal_population_count": 4,
            "lcy_orthogonal_population_count": 4,
            "0d8_orthogonal_population_count": 4,
            "tp2_orthogonal_population_count": 4,
            "6oa_task_negative_chemistry_positive_population_count": 4,
            "task_negative_chemistry_positive_population_count": 20,
            "task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_plus_6oa_exact20": True,
            "global_task_negative_chemistry_positive_relaxation_allowed": False,
            "census_refreshed": True,
            "census_refresh_performed": True,
            "queue_refreshed": False,
            "next_review_started": False,
            "pyr_review_state_created": False,
            "6oa_reconciliation_consumed": True,
            "new_human_authority_created": False,
            "new_scientific_authority_created": False,
            "new_chemistry_authority_created": False,
            "new_pair_authority_created": False,
            "new_role_authority_created": False,
            "new_reusable_authority_created": False,
            "derived_refresh_not_new_authority": True,
            "formal_decision_read_directly": False,
            "formal_decision_bound_directly": False,
            "formal_validator_executed": False,
            "authoritative_task_labels_created_by_census": False,
            "event_task_label_rows_materialized_by_census": False,
            "training_mask_targets_created_by_census": False,
            "training_dataset_changed": False,
            "tensor_integration_performed": False,
            "training_started": False,
            "ready_for_training": False,
            "ready_for_formal_training": False,
            "source_binding_v2_clean_from_birth": True,
        },
        "authority_boundary": computation.summary["authority_boundary"],
    }
    manifest_payload = _json_bytes(manifest)
    _validate_text_payload(manifest_payload, MANIFEST_FILE)
    lowered = manifest_payload.decode("utf-8").lower()
    for token in (
        '"hostname"', '"pid"', '"timestamp"', '"head"', '"commit_subject"',
        '"ahead"', '"behind"', '"lifecycle_profile"',
    ):
        if token in lowered:
            _fail("MANIFEST_LIFECYCLE_FIELD_FORBIDDEN")
    return {
        CENSUS_FILE: census_payload,
        SUMMARY_FILE: summary_payload,
        MANIFEST_FILE: manifest_payload,
    }


def build_covapie_cumulative1000_current_global_readiness_artifacts_with_6oa_v1(
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
    computation = compute_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1(root)
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
        entry_metadata = entry.lstat()
        if stat.S_ISLNK(entry_metadata.st_mode) or not stat.S_ISREG(entry_metadata.st_mode):
            _fail("OUTPUT_ENTRY_NOT_REGULAR:" + entry.name)


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=path.name + ".", suffix=".tmp", dir=path.parent
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except OSError as error:
        raise Cumulative1000CurrentGlobalReadinessCensusWith6OAError(
            f"{ERROR_TOKEN}:OUTPUT_WRITE_FAILED:{path.name}"
        ) from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_6oa_v1(
    repo_root: Path, output_directory: Path | None = None,
) -> dict[str, bytes]:
    """Write only the authorized Exact3 files under the exact 6OA output root."""

    root = repo_root.resolve()
    output = root / OUTPUT_DIRECTORY_RELATIVE if output_directory is None else Path(output_directory)
    _validate_materialization_destination_v1(root, output)
    artifacts = build_covapie_cumulative1000_current_global_readiness_artifacts_with_6oa_v1(root)
    output.mkdir(parents=True, exist_ok=True)
    for filename in (CENSUS_FILE, SUMMARY_FILE, MANIFEST_FILE):
        _atomic_write(output / filename, artifacts[filename])
    return artifacts
