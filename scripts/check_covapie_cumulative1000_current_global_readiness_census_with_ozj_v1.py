#!/usr/bin/env python3
"""Independent fail-closed checker for the cumulative1000 OZJ refresh V1."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_completed_human_decision_reconciliation_with_ozj_v1 as reconciliation  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_cht_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_cumulative1000_current_global_readiness_census_with_ozj_v1 as subject  # noqa: E402
from covalent_ext import covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402


FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part",
)
MAX_FILE_BYTES = 1024 * 1024
EXPECTED_CENSUS_SHA256 = "1d73fe9702988244006063ab522b3e8222837879c6f00d8deac032a54db2f9b6"
EXPECTED_SUMMARY_SHA256 = "d6b249101eaec5e50d6d9585a05c9de0485bcea24d4d4143444429ab97408f56"
EXPECTED_BINDINGS_SHA256 = "4a3f68cff1a479a230dd694ac0a5964439c725ced89bf95702573fefcf438773"
EXPECTED_OZJ_EVENT_IDS = (
    "COVAPIE_CYS_SG_EVENT_V1:4CL8:A:CYS:168-:SG:E:OZJ:CAF",
    "COVAPIE_CYS_SG_EVENT_V1:4CL8:B:CYS:168-:SG:I:OZJ:CAF",
    "COVAPIE_CYS_SG_EVENT_V1:4CL8:C:CYS:168-:SG:L:OZJ:CAF",
    "COVAPIE_CYS_SG_EVENT_V1:4CL8:D:CYS:168-:SG:O:OZJ:CAF",
)
EXPECTED_CHANGED_FIELDS = frozenset(
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
    }
)
EXPECTED_OZJ_STRUCTURAL_CELLS = {
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
EXPECTED_BOOLEAN_COUNTS = {
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
    "reactive_pair_sample_authoritative": 104,
    "reactive_pair_training_target_available": 41,
    "role_partition_sample_authoritative": 104,
    "canonical_mask_structural_labels_available": 104,
    "post_geometry_sample_authoritative": 21,
    "post_geometry_training_target_available": 17,
    "pre_geometry_authoritative": 0,
    "pre_geometry_training_target_available": 0,
    "training_use_include": 40,
    "future_training_admission_candidate": 23,
    "formal_training_admitted": 5,
    "current_runtime_model_usable": 17,
}

FROZEN_BINDINGS = (
    (
        "PREDECESSOR_CHT_CENSUS_OWNER",
        "src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_cht_v1.py",
        "repository_relative", 63414,
        "e478b41dca9555bda1caab2cacd3160f3b0cc98c744d50f2eb46a915fccb6f14",
    ),
    (
        "PREDECESSOR_CHT_MATERIALIZED_CENSUS",
        "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_cht_v1/covapie_cumulative1000_current_global_readiness_census_with_cht_v1.csv",
        "repository_relative", 523894,
        "b51bff3d31d910fa4990a1482e0d3b05364fed86a9cf503de833ddf8851f6384",
    ),
    (
        "PREDECESSOR_CHT_MATERIALIZED_SUMMARY",
        "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_cht_v1/covapie_cumulative1000_current_global_readiness_summary_with_cht_v1.json",
        "repository_relative", 15828,
        "b2130b1f0b9cf36455f1bf00e6e5c32e9a4ef250f18bb25f7a902af67c79e0b3",
    ),
    (
        "PREDECESSOR_CHT_MATERIALIZED_MANIFEST",
        "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_cht_v1/covapie_cumulative1000_current_global_readiness_manifest_with_cht_v1.json",
        "repository_relative", 38794,
        "168f2a713aa9b0ee6904f414330518342ca553495d17340d94ad9df1f8bc1f33",
    ),
    (
        "OZJ_RECONCILIATION_SUCCESSOR",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_with_ozj_v1.py",
        "repository_relative", 16102,
        "d021e64fa6af1da41246d0618e3a38f8d079c0100e74d7ff4aec80f395d843f0",
    ),
    (
        "OZJ_INGESTION_OWNER",
        "src/covalent_ext/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1.py",
        "repository_relative", 106888,
        "abb80e28e1e139c3515a01c53468530a815c5554b94053afb607053d14a84deb",
    ),
    (
        "OZJ_EVENT_TASK_LABEL_AVAILABILITY",
        "data/derived/covalent_small/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1/covapie_ozj_event_task_label_availability_v1.csv",
        "repository_relative", 9031,
        "b039dbde52e2fe6a46866cdce0a378fc6dcc942e4a552845ce664fd80f1009d3",
    ),
    (
        "OZJ_FORMAL_HUMAN_DECISION",
        "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/OZJ_COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450/formal-human-decision-v1/ozj_formal_human_decision_v1.json",
        "repository_parent_relative", 28914,
        "0b14271a4541e69d768e28b6433c87b8b22c21505f6e3bdf075bb94381c3c606",
    ),
)
SEMANTIC_ADDITIVE_BINDINGS = tuple(
    item
    for item in FROZEN_BINDINGS
    if item[0] != "PREDECESSOR_CHT_MATERIALIZED_MANIFEST"
)
FROZEN_INGESTION_OUTPUTS = {
    ingestion.SNAPSHOT: (
        31404,
        "3458c3559963b09f69495ffe8cf43511a1e84b7de5ad0c84279ccdcd100a4b25",
    ),
    ingestion.MATRIX: (
        9031,
        "b039dbde52e2fe6a46866cdce0a378fc6dcc942e4a552845ce664fd80f1009d3",
    ),
    ingestion.SUMMARY: (
        4803,
        "305bb814c97a450e8dc95961433daf1e9aca942537469153a89d7e322c6c3214",
    ),
    ingestion.MANIFEST: (
        18554,
        "ca1e305920afd724c138ed572764bd3147039345034ebd172dfb1e274a4a1468",
    ),
}


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    )


def _read(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("NOT_REGULAR_FILE:" + label)
    return path.read_bytes()


def _validate_text(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF8_BOM_FORBIDDEN:" + label)
    text = payload.decode("utf-8")
    if "\x00" in text or "\r" in text:
        raise ValueError("TEXT_INVARIANT_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("FINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        raise ValueError("TRAILING_WHITESPACE:" + label)


def _parse_census(payload: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != subject.CENSUS_COLUMNS_V1:
        raise ValueError("CENSUS_HEADER_INVALID")
    rows = [dict(row) for row in reader]
    if len(rows) != 1000 or any(
        tuple(row) != subject.CENSUS_COLUMNS_V1 for row in rows
    ):
        raise ValueError("CENSUS_NOT_EXACT1000_SCHEMA")
    return rows


def verify_exact7_inventory_v1(root: Path) -> list[dict[str, object]]:
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    if not output.is_dir() or output.is_symlink():
        raise ValueError("OUTPUT_DIRECTORY_MISSING_OR_INVALID")
    if sorted(path.name for path in output.iterdir() if path.is_file()) != sorted(
        (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    ):
        raise ValueError("OUTPUT_DIRECTORY_NOT_EXACT3")
    bindings: list[dict[str, object]] = []
    for relative in subject.EXACT7_PATHS_V1:
        path = root / relative
        payload = _read(path, "EXACT7:" + relative)
        _validate_text(payload, relative)
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode not in {0o644, 0o664} or mode & 0o111:
            raise ValueError("EXACT7_MODE_UNSAFE:" + relative)
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("EXACT7_FORBIDDEN_SUFFIX:" + relative)
        if len(payload) > MAX_FILE_BYTES:
            raise ValueError("EXACT7_FILE_EXCEEDS_1_MIB:" + relative)
        bindings.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "sha256": _sha(payload),
                "mode": f"{mode:04o}",
            }
        )
    return bindings


def verify_frozen_bindings_v1(root: Path) -> list[dict[str, object]]:
    verified: list[dict[str, object]] = []
    for role, relative, namespace, byte_count, sha256 in FROZEN_BINDINGS:
        path = root / relative if namespace == "repository_relative" else root.parent / relative
        payload = _read(path, role)
        if len(payload) != byte_count or _sha(payload) != sha256:
            raise ValueError("FROZEN_BINDING_INVALID:" + role)
        verified.append(
            {
                "artifact_role": role,
                "path": relative,
                "path_namespace": namespace,
                "byte_count": byte_count,
                "sha256": sha256,
            }
        )
    built = ingestion.build_artifacts_v1(root)
    for filename, (byte_count, sha256) in FROZEN_INGESTION_OUTPUTS.items():
        path = root / ingestion.OUTPUT_ROOT_RELATIVE / filename
        payload = _read(path, "OZJ_INGESTION_OUTPUT:" + filename)
        if len(payload) != byte_count or _sha(payload) != sha256:
            raise ValueError("OZJ_INGESTION_OUTPUT_BINDING_INVALID:" + filename)
        if built[filename] != payload:
            raise ValueError("OZJ_INGESTION_OUTPUT_NOT_SOURCE_DERIVED:" + filename)
    formal = json.loads(
        _read(
            root.parent / ingestion.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
            "OZJ_FORMAL_DECISION",
        )
    )
    if formal.get("schema_version") != "covapie_ozj_exact4_formal_human_decision_v1":
        raise ValueError("OZJ_FORMAL_SCHEMA_INVALID")
    return verified


def independently_verify_matrix_v1(root: Path) -> list[dict[str, str]]:
    payload = _read(root / subject.OZJ_EVENT_MATRIX_RELATIVE, "OZJ_MATRIX")
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    rows = [dict(row) for row in reader]
    if tuple(reader.fieldnames or ()) != ingestion.MATRIX_HEADER:
        raise ValueError("OZJ_MATRIX_HEADER_INVALID")
    if len(rows) != 4 or tuple(row["canonical_event_id"] for row in rows) != EXPECTED_OZJ_EVENT_IDS:
        raise ValueError("OZJ_MATRIX_NOT_EXACT4")
    if [int(row["scaleup_rank"]) for row in rows] != [670, 671, 672, 673]:
        raise ValueError("OZJ_MATRIX_RANKS_INVALID")
    if Counter(row["pdb_id"] for row in rows) != Counter({"4CL8": 4}):
        raise ValueError("OZJ_MATRIX_PDB_COUNTS_INVALID")
    expected = {
        "cys_residue_id": "CYS:168-",
        "human_task_relevance_decision": "RELEVANT",
        "chemistry_known_positive": "true",
        "negative_chemistry": "false",
        "task_domain_negative": "false",
        "reactive_pair_human_authoritative": "true",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "CAF",
        "ligand_reactive_atom_element": "C",
        "role_partition_human_authoritative": "true",
        "selected_role_candidate_index_0based": "1",
        "role_profile": "STRICT_LINKER_PRESENT_V1",
        "warhead_atoms_json": "[\"CAF\",\"OAD\"]",
        "linker_atoms_json": "[\"CAG\",\"CAH\",\"CAI\",\"CAJ\",\"CAP\",\"CAQ\"]",
        "scaffold_atoms_json": "[\"C2\",\"C4\",\"C5\",\"C6\",\"CAE\",\"CAR\",\"CAS\",\"N1\",\"N3\",\"NAA\",\"NAB\",\"NAC\",\"NAM\"]",
        "global_canonical_task_count": "5",
        "strict_profile_applicable_task_ids_json": "[0,1,2,3,4]",
        "formal_event_training_use_decision": "INCLUDE",
        "training_use_allowed": "true",
        "training_use_include": "true",
        "human_training_excluded": "false",
        "formal_future_training_admission_candidate": "null",
        "formal_future_training_admission_candidate_status": (
            "DEFERRED_TO_DOWNSTREAM_INGESTION_AND_CENSUS"
        ),
        "candidate_for_future_training_admission": "true",
        "future_training_admission_status": (
            "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"
        ),
        "future_training_candidate_derived_by_ingestion": "true",
        "future_training_candidate_is_training_admission": "false",
        "training_admitted": "false",
        "training_admission_created": "false",
        "training_materialization_allowed_now": "false",
        "current_runtime_model_usable": "false",
        "source_CAF_OAD_bond_order": "DOUB",
        "explicit_SG_CAF_connection_available": "true",
        "complete_POST_adduct_topology_authority_available": "false",
        "PRE_topology_authority_available": "false",
        "PRE_geometry_authority_available": "false",
        "POST_source_evidence_available": "true",
        "POST_geometry_training_label_available_now": "false",
        "formal_split_authority_created": "false",
        "tensor_target_created": "false",
        "parameter_update_authorization": "false",
    }
    names = [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
        "scaffold_only", "scaffold_plus_linker_plus_warhead",
    ]
    for row in rows:
        if any(row[field] != value for field, value in expected.items()):
            raise ValueError("OZJ_MATRIX_SEMANTICS_INVALID:" + row["canonical_event_id"])
        tasks = json.loads(row["canonical_task_applicability_json"])
        if (
            [item["task_id"] for item in tasks] != [0, 1, 2, 3, 4]
            or [item["semantic_long_name"] for item in tasks] != names
            or [item["display_alias"] for item in tasks] != ["A", "B", "B2", "B3", "C"]
            or [item["task_id"] for item in tasks if item["structurally_applicable"]]
            != [0, 1, 2, 3, 4]
        ):
            raise ValueError("OZJ_MATRIX_EXACT5_INVALID")
    return rows


def independently_verify_delta_v1(
    root: Path, rows: list[dict[str, str]]
) -> dict[str, object]:
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_cht_v1(
        root
    )
    before = {row["canonical_event_id"]: row for row in frozen.rows}
    after = {row["canonical_event_id"]: row for row in rows}
    if tuple(int(row["scaleup_rank"]) for row in rows) != tuple(range(1, 1001)):
        raise ValueError("ROW_ORDER_OR_RANK_INVALID")
    if set(before) != set(after):
        raise ValueError("EVENT_SET_IDENTITY_INVALID")
    ozj = set(EXPECTED_OZJ_EVENT_IDS)
    if [int(before[event_id]["scaleup_rank"]) for event_id in EXPECTED_OZJ_EVENT_IDS] != [
        670, 671, 672, 673,
    ]:
        raise ValueError("PREDECESSOR_OZJ_IDENTITY_INVALID")
    expected_prior = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false",
        "human_review_authority_source": subject.PRIORITY_QUEUE_RELATIVE.as_posix(),
        "chemistry_disposition": "UNRESOLVED",
        "chemistry_authority_source": "",
        "task_relevance_disposition": "UNRESOLVED",
        "task_relevance_authority_source": "",
        "training_use_disposition": "UNRESOLVED",
        "human_training_excluded": "false",
        "reactive_pair_sample_authoritative": "false",
        "role_partition_sample_authoritative": "false",
        "role_profile": "NOT_ESTABLISHED",
        "canonical_mask_structural_labels_available": "false",
        "structurally_applicable_task_ids_json": "null",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "formal_split_authoritative": "false",
        "formal_split": "",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
        "training_materialization_allowed_current_source": "",
        "positive_authority_source": "",
    }
    if any(
        any(before[event_id][field] != value for field, value in expected_prior.items())
        for event_id in ozj
    ):
        raise ValueError("PREDECESSOR_OZJ_STATE_INVALID")
    changed = {event_id for event_id in before if before[event_id] != after[event_id]}
    if changed != ozj:
        raise ValueError("DELTA_NOT_EXACT_OZJ_EXACT4")
    if any(before[event_id] != after[event_id] for event_id in set(before) - ozj):
        raise ValueError("NON_OZJ_ROW_DRIFT")
    for event_id in ozj:
        changed_fields = {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event_id][field] != after[event_id][field]
        }
        if changed_fields != EXPECTED_CHANGED_FIELDS:
            raise ValueError("OZJ_CHANGED_FIELD_SET_INVALID:" + event_id)
        row = after[event_id]
        expected_after = {
            "current_global_status": "COMPLETED_HUMAN_POSITIVE",
            "current_review_status": "COMPLETED_HUMAN_POSITIVE",
            "human_review_completed": "true",
            "human_review_authority_source": subject.OZJ_FORMAL_DECISION_SOURCE,
            "chemistry_disposition": "POSITIVE",
            "chemistry_authority_source": subject.OZJ_EVENT_MATRIX_SOURCE,
            "positive_authority_source": subject.OZJ_EVENT_MATRIX_SOURCE,
            "task_relevance_disposition": "RELEVANT",
            "task_relevance_authority_source": subject.OZJ_EVENT_MATRIX_SOURCE,
            "training_use_disposition": "INCLUDE",
            "human_training_excluded": "false",
            "training_use_include": "true",
            "future_training_admission_candidate": "true",
            "reactive_pair_sample_authoritative": "true",
            "reactive_pair_training_target_available": "false",
            "role_partition_sample_authoritative": "true",
            "role_profile": "STRICT_LINKER_PRESENT_V1",
            "canonical_mask_structural_labels_available": "true",
            "structurally_applicable_task_ids_json": "[0,1,2,3,4]",
            "post_geometry_sample_authoritative": "false",
            "post_geometry_training_target_available": "false",
            "pre_geometry_authoritative": "false",
            "pre_geometry_training_target_available": "false",
            "formal_split_authoritative": "false",
            "formal_split": "",
            "formal_training_admitted": "false",
            "current_runtime_model_usable": "false",
            "training_materialization_allowed_current_source": "false",
        }
        if any(row[field] != value for field, value in expected_after.items()):
            raise ValueError("OZJ_SEMANTICS_INVALID:" + event_id)
        if any(row[field] != value for field, value in EXPECTED_OZJ_STRUCTURAL_CELLS.items()):
            raise ValueError("OZJ_STRUCTURAL_COVERAGE_INVALID:" + event_id)
    return {
        "changed_event_count": 4,
        "unchanged_event_count": 996,
        "changed_fields": sorted(EXPECTED_CHANGED_FIELDS),
    }


def independently_verify_counts_v1(
    rows: list[dict[str, str]], summary: dict[str, object]
) -> None:
    if summary["refresh_delta"] != {
        "frozen_predecessor_positive_count": 100,
        "ozj_exact4_delta_count": 4,
        "refreshed_positive_count": 104,
        "frozen_predecessor_training_include_count": 36,
        "refreshed_training_include_count": 40,
        "frozen_predecessor_training_exclude_count": 64,
        "refreshed_training_exclude_count": 64,
        "frozen_predecessor_future_candidate_count": 19,
        "refreshed_future_candidate_count": 23,
        "changed_event_count": 4,
        "unchanged_event_count": 996,
        "derived_refresh_not_new_authority": True,
    }:
        raise ValueError("REFRESH_DELTA_INVALID")
    if Counter(row["current_global_status"] for row in rows) != Counter(
        {
            "CURRENTLY_UNREVIEWED": 227,
            "CURRENTLY_IN_PROGRESS": 0,
            "COMPLETED_HUMAN_POSITIVE": 87,
            "COMPLETED_HUMAN_NEGATIVE": 54,
            "COMPLETED_PARTIAL_AUTHORITY": 1,
            "CURRENT_RUNTIME_MODEL_USABLE": 17,
            "PUBLISHED_EXACT_AUTO_NEGATIVE": 32,
            "LEAKAGE_EXISTING_GROUP_CONFLICT": 369,
            "STRUCTURAL_EVIDENCE_INCOMPLETE": 133,
            "QUARANTINE_REPRESENTATION_GAP": 78,
            "REJECTED_FEATURE_INCOMPATIBLE": 2,
        }
    ):
        raise ValueError("GLOBAL_STATUS_COUNTS_INVALID")
    if Counter(row["chemistry_disposition"] for row in rows) != Counter(
        {"POSITIVE": 104, "NOT_ESTABLISHED": 86, "UNRESOLVED": 810}
    ):
        raise ValueError("CHEMISTRY_COUNTS_INVALID")
    if Counter(row["task_relevance_disposition"] for row in rows) != Counter(
        {"RELEVANT": 105, "NOT_RELEVANT": 86, "UNRESOLVED": 809}
    ):
        raise ValueError("TASK_COUNTS_INVALID")
    if Counter(row["training_use_disposition"] for row in rows) != Counter(
        {
            "INCLUDE": 40, "EXCLUDE_FROM_TRAINING_ONLY": 64,
            "NOT_APPLICABLE": 86, "UNRESOLVED": 810,
        }
    ):
        raise ValueError("TRAINING_COUNTS_INVALID")
    for field, expected in EXPECTED_BOOLEAN_COUNTS.items():
        if sum(row[field] == "true" for row in rows) != expected:
            raise ValueError("BOOLEAN_COUNT_INVALID:" + field)
    if sum(row["human_training_excluded"] == "true" for row in rows) != 64:
        raise ValueError("HUMAN_EXCLUSION_COUNT_INVALID")
    if summary["structural"] != {  # type: ignore[index]
        "raw_structure_available_count": 997,
        "exact_cys_sg_event_recovered_count": 867,
        "explicit_covalent_evidence_count": 867,
        "distance_only_event_inference_used_count": 0,
        "full_coordinate_post_evidence_available_count": 867,
        "ccd_graph_complete_count": 865,
        "feature_compatible_count": 865,
        "structural_processing_success_count": 865,
        "post_geometry_source_evidence_available_count": 867,
        "representation_gap_count": 78,
        "feature_incompatible_count": 2,
    }:
        raise ValueError("STRUCTURAL_SUMMARY_INVALID")
    if summary["geometry"] != {  # type: ignore[index]
        "POST_source_evidence_available_count": 867,
        "POST_sample_authoritative_count": 21,
        "POST_training_target_available_count": 17,
        "PRE_source_evidence_available_count": 0,
        "PRE_sample_authoritative_count": 0,
        "PRE_training_target_available_count": 0,
        "PRE_is_v1_hard_requirement": False,
        "POST_to_PRE_promotion_performed": False,
        "PRE_zero_fill_performed": False,
    }:
        raise ValueError("GEOMETRY_COUNTS_INVALID")
    chemistry = summary["chemistry"]  # type: ignore[assignment]
    if chemistry["positive_source_composition"] != {
        "CURRENT_RUNTIME": 17, "FFQ": 8, "POA": 16, "G3H": 8,
        "ONL": 9, "PRF": 8, "2VS": 8, "1F8": 8, "YUN": 7,
        "NEQ": 6, "CHT": 5, "OZJ": 4,
    } or chemistry["positive_authority_collision_count"] != 0:
        raise ValueError("POSITIVE_SOURCE_COMPOSITION_INVALID")
    pair = summary["reactive_pair"]  # type: ignore[assignment]
    if (
        pair["raw_structural_pair_evidence_count"] != 865
        or pair["sample_level_authoritative_pair_count"] != 104
        or pair["positive_without_sample_pair_authority_count"] != 0
        or pair["published_model_bound_target_constructible_count"] != 41
        or pair["current_runtime_bound_target_count"] != 17
        or pair["ozj_sample_authority_contribution_count"] != 4
        or pair["ozj_model_bound_target_contribution_count"] != 0
    ):
        raise ValueError("PAIR_SUMMARY_INVALID")
    if summary["role"] != {  # type: ignore[index]
        "role_partition_sample_authoritative_count": 104,
        "role_profile_counts": {
            "STRICT_LINKER_PRESENT_V1": 48,
            "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": 56,
            "other": 0,
        },
        "canonical_mask_structural_labels_available_count": 104,
        "all_five_structurally_applicable_count": 48,
        "direct_profile_A_B3_C_count": 56,
        "unknown_role_row_count": 896,
        "unknown_role_rows_are_not_false_applicability": True,
    }:
        raise ValueError("ROLE_SUMMARY_INVALID")
    exact5 = summary["canonical_exact5"]  # type: ignore[assignment]
    if (
        exact5["task_count"] != 5
        or [task["semantic_name"] for task in exact5["tasks"]] != [
            "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
            "scaffold_only", "scaffold_plus_linker_plus_warhead",
        ]
        or [
            task["structurally_applicable_authoritative_role_count"]
            for task in exact5["tasks"]
        ] != [104, 48, 48, 104, 104]
        or exact5["B3_present"] is not True
        or exact5["sixth_task_present"] is not False
    ):
        raise ValueError("EXACT5_COUNTS_INVALID")
    if summary["human_review"] != {  # type: ignore[index]
        "priority_review_population_event_count": 338,
        "review_unit_count": 131,
        "completed_event_count": 111,
        "completed_unit_count": 15,
        "completed_positive_event_count": 87,
        "completed_positive_unit_count": 11,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "unreviewed_event_count": 227,
        "unreviewed_unit_count": 116,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "pending_event_count": 227,
        "current_pending_review_unit_count": 116,
    }:
        raise ValueError("HUMAN_REVIEW_SUMMARY_INVALID")
    expected_blockers = {
        "non_exclusive_counts_must_not_be_summed": True,
        "chemistry_unresolved": {"all_1000": 810},
        "pair_authority_absent": {"all_1000": 896, "within_positive_104": 0},
        "role_authority_absent": {"all_1000": 896, "within_positive_104": 0},
        "human_training_exclusion": {"within_positive_104": 64},
        "missing_split_authority": {
            "within_positive_104": 63, "within_include_40": 15,
        },
        "missing_tensor_integration": {
            "within_positive_104": 63,
            "within_include_40": 11,
            "all_missing_are_training_excluded_population": False,
            "missing_source_composition": {
                "G3H": 8, "ONL": 9, "PRF": 8, "2VS": 8, "1F8": 8,
                "YUN": 7, "NEQ": 6, "CHT": 5, "OZJ": 4,
            },
        },
        "missing_POST_training_authority": {
            "within_positive_104": 87, "within_include_40": 23,
        },
        "missing_training_admission": {
            "within_positive_104": 99, "within_include_40": 35,
        },
        "feature_semantics_pending": {"within_positive_104": 104},
    }
    if summary["blockers"] != expected_blockers:
        raise ValueError("BLOCKERS_INVALID")
    stage = summary["training_stage"]  # type: ignore[assignment]
    if (
        stage["training_use_include_count"] != 40
        or stage["future_training_admission_candidate_count"] != 23
        or stage["formal_training_admitted_count"] != 5
        or stage["current_runtime_model_usable_count"] != 17
        or stage["ready_for_formal_training_event_count"] != 0
        or stage["future_candidate_source_composition"]["OZJ"] != 4
    ):
        raise ValueError("TRAINING_STAGE_INVALID")


def independently_compute_top10_v1(
    root: Path, reconciled_rows: tuple[dict[str, str], ...]
) -> list[dict[str, object]]:
    payload = _read(root / subject.PRIORITY_QUEUE_RELATIVE, "PRIORITY_QUEUE")
    if len(payload) != 50116 or _sha(payload) != (
        "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"
    ):
        raise ValueError("PRIORITY_QUEUE_BINDING_INVALID")
    queue_rows = [
        dict(row)
        for row in csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    ]
    status_by_unit: dict[str, set[str]] = defaultdict(set)
    for row in reconciled_rows:
        status_by_unit[row["raw_review_unit_id"]].add(row["current_review_status"])
    candidates: list[tuple[int, int, str, dict[str, str], str]] = []
    for row in queue_rows:
        unit = row["review_unit_id"]
        statuses = status_by_unit.get(unit)
        if statuses is None or len(statuses) != 1:
            raise ValueError("QUEUE_UNIT_STATUS_INVALID:" + unit)
        status = next(iter(statuses))
        if status not in {"CURRENTLY_UNREVIEWED", "CURRENTLY_IN_PROGRESS"}:
            continue
        candidates.append(
            (-int(row["event_count"]), int(row["priority_rank"]), unit, row, status)
        )
    candidates.sort(key=lambda item: item[:3])
    if len(candidates) != 116:
        raise ValueError("PENDING_QUEUE_NOT_EXACT116")
    result: list[dict[str, object]] = []
    for rank, (_negative, _priority, unit, row, status) in enumerate(
        candidates[:10], 1
    ):
        result.append(
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
    return result


def verify_semantic_bindings_v1(
    root: Path, observed: tuple[dict[str, object], ...]
) -> None:
    frozen = predecessor.compute_covapie_cumulative1000_current_global_readiness_census_with_cht_v1(
        root
    )
    if len(frozen.semantic_source_bindings) != 88:
        raise ValueError("PREDECESSOR_SEMANTIC_BINDING_COUNT_NOT_88")
    if _sha(_canonical_json(list(frozen.semantic_source_bindings)).encode()) != (
        "93250ea26a28e2b98016a842dd869aa641f99a8e8068c4582f8347777a1ac725"
    ):
        raise ValueError("PREDECESSOR_SEMANTIC_BINDING_DIGEST_INVALID")
    by_identity = {
        (row["path_namespace"], row["path"]): dict(row)
        for row in frozen.semantic_source_bindings
    }
    prior_roles = {row["artifact_role"] for row in frozen.semantic_source_bindings}
    additive_roles: set[str] = set()
    for role, relative, namespace, byte_count, sha256 in SEMANTIC_ADDITIVE_BINDINGS:
        if role in prior_roles or role in additive_roles:
            raise ValueError("ADDITIVE_ROLE_COLLISION:" + role)
        additive_roles.add(role)
        row = {
            "artifact_role": role,
            "path": relative,
            "path_namespace": namespace,
            "byte_count": byte_count,
            "sha256": sha256,
        }
        identity = (namespace, relative)
        prior = by_identity.get(identity)
        if prior is not None and prior != row:
            raise ValueError("SEMANTIC_BINDING_CONFLICT:" + relative)
        by_identity[identity] = row
    expected = tuple(
        sorted(by_identity.values(), key=lambda row: (row["path_namespace"], row["path"]))
    )
    if observed != expected or len(observed) != 95:
        raise ValueError("SEMANTIC_BINDINGS_NOT_PREDECESSOR_PLUS_OZJ_INPUTS")
    predecessor_identities = {
        (row["path_namespace"], row["path"])
        for row in frozen.semantic_source_bindings
    }
    if tuple(
        row for row in observed
        if (row["path_namespace"], row["path"]) in predecessor_identities
    ) != frozen.semantic_source_bindings:
        raise ValueError("PREDECESSOR_BINDING_ORDER_CHANGED")


def verify_manifest_v1(artifacts: dict[str, bytes], fresh: object) -> None:
    manifest = json.loads(artifacts[subject.MANIFEST_FILE])
    if manifest["schema_version"] != subject.SCHEMA_VERSION or manifest["stage"] != subject.STAGE:
        raise ValueError("MANIFEST_SCHEMA_OR_STAGE_INVALID")
    if manifest["candidate_inventory"] != {
        "exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1),
    }:
        raise ValueError("MANIFEST_EXACT7_INVALID")
    if manifest["semantic_source_bindings"] != list(fresh.semantic_source_bindings):
        raise ValueError("MANIFEST_SEMANTIC_BINDINGS_INVALID")
    if manifest["derived_projection_contract_digests"] != {
        "refreshed_census_sha256": EXPECTED_CENSUS_SHA256,
        "refreshed_summary_sha256": EXPECTED_SUMMARY_SHA256,
        "semantic_source_bindings_sha256": EXPECTED_BINDINGS_SHA256,
        "authority_created": False,
    }:
        raise ValueError("MANIFEST_DERIVED_DIGESTS_INVALID")
    if manifest["manifest_self_binding"]["sha256_recorded_inside_self"] is not False:
        raise ValueError("MANIFEST_SELF_SHA_RECORDED")
    manifest_path = (subject.OUTPUT_DIRECTORY_RELATIVE / subject.MANIFEST_FILE).as_posix()
    if any(
        binding["path"] == manifest_path
        for binding in manifest["output_bindings_excluding_manifest_self"]
    ):
        raise ValueError("MANIFEST_SELF_HASHED")
    output_bindings = {
        binding["path"]: binding
        for binding in manifest["output_bindings_excluding_manifest_self"]
    }
    for filename in (subject.CENSUS_FILE, subject.SUMMARY_FILE):
        path = (subject.OUTPUT_DIRECTORY_RELATIVE / filename).as_posix()
        binding = output_bindings.get(path)
        if binding is None or binding["sha256"] != _sha(artifacts[filename]):
            raise ValueError("MANIFEST_OUTPUT_BINDING_INVALID:" + filename)
    candidate_bindings = {
        binding["path"]: binding for binding in manifest["candidate_contract_bindings"]
    }
    expected_paths = {
        subject.PRODUCTION_RELATIVE.as_posix(), subject.CHECKER_RELATIVE.as_posix(),
        subject.TEST_RELATIVE.as_posix(), subject.GUIDE_RELATIVE.as_posix(),
    }
    if set(candidate_bindings) != expected_paths:
        raise ValueError("MANIFEST_CANDIDATE_BINDINGS_INVALID")
    for relative, binding in candidate_bindings.items():
        payload = _read(ROOT / relative, "MANIFEST_CANDIDATE:" + relative)
        if binding["byte_count"] != len(payload) or binding["sha256"] != _sha(payload):
            raise ValueError("MANIFEST_CANDIDATE_BINDING_DRIFT:" + relative)


def _git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ("git", *args), cwd=root, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _classify_exact7_artifact_placement_v1(
    tracked_paths: Sequence[str], ordinary_untracked_paths: Sequence[str]
) -> str:
    expected = set(subject.EXACT7_PATHS_V1)
    tracked = list(tracked_paths)
    untracked = list(ordinary_untracked_paths)
    if len(expected) != 7 or len(subject.EXACT7_PATHS_V1) != 7:
        raise ValueError("EXACT7_INTERNAL_CONTRACT_INVALID")
    if len(set(tracked)) != len(tracked) or len(set(untracked)) != len(untracked):
        raise ValueError("EXACT7_ARTIFACT_PLACEMENT_DUPLICATE_PATH")
    if not tracked and len(untracked) == 7 and set(untracked) == expected:
        return "CANDIDATE_UNTRACKED"
    if len(tracked) == 7 and set(tracked) == expected and not untracked:
        return "TRACKED_CLEAN"
    raise ValueError("EXACT7_ARTIFACT_PLACEMENT_INVALID")


def verify_git_and_cache_safety_v1(root: Path) -> dict[str, object]:
    if _git(root, "diff", "--name-only"):
        raise ValueError("TRACKED_WORKTREE_MODIFICATION_PRESENT")
    if _git(root, "diff", "--cached", "--name-only"):
        raise ValueError("STAGED_CHANGE_PRESENT")
    tracked_exact7 = _git(root, "ls-files", "--", *subject.EXACT7_PATHS_V1)
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    if any(path.endswith(FORBIDDEN_SUFFIXES) for path in untracked):
        raise ValueError("UNTRACKED_FORBIDDEN_SUFFIX")
    placement = _classify_exact7_artifact_placement_v1(tracked_exact7, untracked)
    protected = (
        "data/raw/", "checkpoints/", "equivariant_diffusion/",
        "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py",
    )
    changed = set(_git(root, "diff", "--name-only")) | set(
        _git(root, "diff", "--cached", "--name-only")
    )
    if any(
        any(path == item.rstrip("/") or path.startswith(item) for item in protected)
        for path in changed
    ):
        raise ValueError("PROTECTED_SOURCE_DIFF_PRESENT")
    skip_roots = {".git", "data/raw", "checkpoints", "equivariant_diffusion"}
    cache_count = 0
    forbidden_ignored_count = 0
    for directory, names, files in os.walk(root):
        relative = Path(directory).relative_to(root).as_posix()
        names[:] = [
            name for name in names
            if (Path(relative) / name).as_posix().lstrip("./") not in skip_roots
            and name not in {".git", "__pycache__", ".pytest_cache"}
        ]
        for name in ("__pycache__", ".pytest_cache"):
            candidate = Path(directory) / name
            if candidate.is_dir() and any(candidate.iterdir()):
                cache_count += 1
        forbidden_ignored_count += sum(
            filename.endswith((".pyc", ".tmp", ".part")) for filename in files
        )
    if cache_count or forbidden_ignored_count:
        raise ValueError("CACHE_OR_TRANSIENT_FILE_PRESENT")
    return {
        "tracked_modification_count": 0,
        "staged_count": 0,
        "exact7_artifact_placement_profile": placement,
        "tracked_exact7_count": len(tracked_exact7),
        "ordinary_untracked_count": len(untracked),
        "cache_count": cache_count,
        "forbidden_transient_count": forbidden_ignored_count,
    }


def run_check_v1(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    exact7 = verify_exact7_inventory_v1(root)
    frozen = verify_frozen_bindings_v1(root)
    independently_verify_matrix_v1(root)
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    materialized = {
        name: _read(output / name, name)
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    for name, payload in materialized.items():
        _validate_text(payload, name)
    rows = _parse_census(materialized[subject.CENSUS_FILE])
    summary = json.loads(materialized[subject.SUMMARY_FILE])
    delta = independently_verify_delta_v1(root, rows)
    independently_verify_counts_v1(rows, summary)

    fresh = subject.compute_covapie_cumulative1000_current_global_readiness_census_with_ozj_v1(
        root
    )
    if not subject.validate_covapie_cumulative1000_current_global_readiness_census_with_ozj_v1(
        fresh
    ):
        raise ValueError("PUBLIC_VALIDATOR_DID_NOT_PASS")
    built = subject.build_covapie_cumulative1000_current_global_readiness_artifacts_with_ozj_v1(
        root
    )
    if materialized != built:
        raise ValueError("MATERIALIZED_OUTPUTS_NOT_FRESH_BUILD")
    if _sha(materialized[subject.CENSUS_FILE]) != EXPECTED_CENSUS_SHA256:
        raise ValueError("CENSUS_DERIVED_DIGEST_INVALID")
    if _sha(materialized[subject.SUMMARY_FILE]) != EXPECTED_SUMMARY_SHA256:
        raise ValueError("SUMMARY_DERIVED_DIGEST_INVALID")
    if _sha(_canonical_json(list(fresh.semantic_source_bindings)).encode()) != EXPECTED_BINDINGS_SHA256:
        raise ValueError("SEMANTIC_BINDINGS_DERIVED_DIGEST_INVALID")
    verify_semantic_bindings_v1(root, fresh.semantic_source_bindings)

    reconciled = reconciliation.reconcile_real_completed_human_decisions_with_ozj_v1(root)
    if reconciled.review_summary != {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 87,
        "completed_positive_unit_count": 11,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 111,
        "completed_total_unit_count": 15,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 227,
        "unreviewed_unit_count": 116,
    }:
        raise ValueError("RECONCILIATION_COUNTS_INVALID")
    expected_top = independently_compute_top10_v1(root, reconciled.reconciled_rows)
    if summary["top_pending_review_units_by_event_yield"] != expected_top:
        raise ValueError("FULL_QUEUE_DYNAMIC_TOP10_INVALID")
    if not (
        expected_top[0]["review_unit_id"] == "COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5"
        and expected_top[0]["ligand_component_ids"] == ["F24"]
        and expected_top[0]["pdb_ids"] == ["3V4X"]
        and expected_top[0]["event_count"] == 4
        and all(item["ligand_component_ids"] != ["OZJ"] for item in expected_top)
    ):
        raise ValueError("NEXT_PRIORITY_NOT_F24_EXACT4")
    verify_manifest_v1(materialized, fresh)

    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        one = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_ozj_v1(
            root, Path(first)
        )
        two = subject.materialize_covapie_cumulative1000_current_global_readiness_artifacts_with_ozj_v1(
            root, Path(second)
        )
        if one != two or one != built:
            raise ValueError("TWO_DIRECTORY_DETERMINISM_INVALID")

    boundary = summary["authority_boundary"]
    false_non_actions = (
        "new_human_authority_created", "new_chemistry_authority_created",
        "new_role_authority_created", "new_pair_authority_created",
        "new_reusable_authority_created", "tensor_integration_performed",
        "loader_modified", "batch_modified", "model_forward_performed",
        "auxiliary_head_executed", "loss_executed", "backward_performed",
        "optimizer_created", "optimizer_step_performed",
        "parameter_update_performed", "training_performed",
        "fine_tune_performed", "training_admission_created",
        "training_dataset_changed", "feature_semantics_audit_performed",
    )
    if (
        boundary["CURRENT_GLOBAL_RECONCILIATION_COMPLETE"] is not True
        or boundary["CURRENT_GLOBAL_READINESS_CENSUS_COMPLETE"] is not True
        or boundary["READY_FOR_NEXT_HIGH_YIELD_HUMAN_REVIEW_SELECTION"] is not True
        or boundary["READY_FOR_FORMAL_TRAINING"] is not False
        or boundary["HUMAN_REVIEW_DECISION_NOT_PERFORMED"] is not True
        or boundary["NEXT_RECOMMENDED_MAINLINE"] != "HIGH_YIELD_HUMAN_REVIEW_EXPANSION"
        or boundary["next_priority_review_unit"] != "COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5"
        or boundary["next_priority_review_ligand"] != "F24"
        or boundary["next_priority_review_event_count"] != 4
        or boundary["feature_semantics_status"] != "AUDIT_REQUIRED_LATER"
        or boundary["tensor_status"] != "NOT_STARTED"
        or boundary["training_admission_status"] != "NOT_STARTED"
        or boundary["training_status"] != "NOT_STARTED"
        or any(boundary[key] is not False for key in false_non_actions)
    ):
        raise ValueError("AUTHORITY_BOUNDARY_INVALID")
    safety = verify_git_and_cache_safety_v1(root)
    return {
        "candidate_file_count": len(exact7),
        "frozen_binding_count": len(frozen),
        "semantic_source_binding_count": len(fresh.semantic_source_bindings),
        **delta,
        **safety,
        "refreshed_positive_count": 104,
        "task_relevant_count": 105,
        "training_include_count": 40,
        "training_exclude_count": 64,
        "future_candidate_count": 23,
        "formal_training_admitted_count": 5,
        "current_runtime_model_usable_count": 17,
        "pending_review_unit_count": 116,
        "next_priority_review_unit": boundary["next_priority_review_unit"],
        "ready_for_formal_training": False,
    }


def main() -> int:
    result = run_check_v1(ROOT)
    if result["ready_for_formal_training"] is not False:
        raise ValueError("READY_FOR_FORMAL_TRAINING_MUST_BE_FALSE")
    print("COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_OZJ_V1_CHECK:PASS")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
