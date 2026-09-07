#!/usr/bin/env python3
"""Independent fail-closed checker for the with-6OA readiness census V1."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_6oa_v1 as reconciliation,
)
from covalent_ext import (  # noqa: E402
    covapie_cumulative1000_current_global_readiness_census_with_6oa_v1 as subject,
)


BASELINE_COMMIT = "7806e77be114a1a7d103f46a6eed5e4c4a49e2b4"
EXPECTED_CENSUS_SHA256 = "440bebc49aefd2a7b920063f5fca949f8f9930b76b6cca496bd8942b83d88a1b"
EXPECTED_SUMMARY_SHA256 = "f3bbdae930e4115e0bf0a51119ad3c5863064cf1fa68670d2ea1e610983dccd8"
EXPECTED_BINDINGS_SHA256 = "1c0a356cecfeb47071e73b0506717e75a4ff652c9ee29bf165bae0bfc5cf06c0"
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".pyc", ".tmp", ".part",
)
PROTECTED_PREFIXES = (
    "data/raw/", "checkpoints/", "equivariant_diffusion/",
)
PROTECTED_FILES = {
    "dataset.py", "lightning_modules.py", "data/prepare_crossdocked.py",
}


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def _read(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("NOT_REGULAR_FILE:" + label)
    return path.read_bytes()


def _validate_text(payload: bytes, label: str) -> None:
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF8_BOM_FORBIDDEN:" + label)
    text = payload.decode("utf-8")
    if "\r" in text or "\x00" in text:
        raise ValueError("TEXT_ENCODING_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("FINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        raise ValueError("TRAILING_WHITESPACE:" + label)


def _parse_csv(payload: bytes, expected_header: Sequence[str]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    if tuple(reader.fieldnames or ()) != tuple(expected_header):
        raise ValueError("CSV_HEADER_INVALID")
    return [dict(row) for row in reader]


def _verify_materialized_output_bytes_v1(
    expected: Mapping[str, bytes], observed: Mapping[str, bytes],
) -> None:
    if dict(observed) != dict(expected):
        _checker_fail("MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED")


def _validate_output_inventory_names_v1(entry_names: Sequence[str]) -> None:
    expected = {
        subject.CENSUS_FILE,
        subject.SUMMARY_FILE,
        subject.MANIFEST_FILE,
    }
    if len(entry_names) != 3 or set(entry_names) != expected:
        _checker_fail("OUTPUT_DIRECTORY_NOT_EXACT3")


def _verify_frozen_payload_identity_v1(
    payload: bytes, *, byte_count: int, digest: str, token: str,
) -> None:
    if len(payload) != byte_count or _sha(payload) != digest:
        _checker_fail(token)


def verify_exact7_inventory_v1(root: Path) -> list[dict[str, object]]:
    output = root / subject.OUTPUT_DIRECTORY_RELATIVE
    try:
        metadata = output.lstat()
    except OSError as error:
        raise ValueError("OUTPUT_DIRECTORY_READ_FAILED") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("OUTPUT_DIRECTORY_NOT_REAL_DIRECTORY")
    _validate_output_inventory_names_v1(tuple(entry.name for entry in output.iterdir()))
    records: list[dict[str, object]] = []
    for relative in subject.EXACT7_PATHS_V1:
        path = root / relative
        payload = _read(path, relative)
        _validate_text(payload, relative)
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode not in {0o644, 0o664} or mode & 0o111:
            raise ValueError("CANDIDATE_FILESYSTEM_MODE_INVALID:" + relative)
        if len(payload) > 1024 * 1024:
            raise ValueError("CANDIDATE_FILE_EXCEEDS_1_MIB:" + relative)
        records.append(
            {"path": relative, "byte_count": len(payload), "sha256": _sha(payload), "mode": mode}
        )
    return records


def verify_frozen_bindings_v1(root: Path) -> None:
    for role, relative, namespace, byte_count, digest, _executable in subject._ADDITIVE_SOURCE_SPECS_V1:
        path = root / relative if namespace == "repository_relative" else root.parent / relative
        payload = _read(path, role)
        if len(payload) != byte_count or _sha(payload) != digest:
            raise ValueError("FROZEN_SOURCE_BINDING_INVALID:" + role)
    payload = _read(root / subject.PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_MANIFEST")
    expected_bytes, expected_digest, _ = subject._PREDECESSOR_MANIFEST_SPEC_V1
    if len(payload) != expected_bytes or _sha(payload) != expected_digest:
        raise ValueError("PREDECESSOR_MANIFEST_BINDING_INVALID")
    payload = _read(
        root / subject.SIX_OA_RECONCILIATION_ARTIFACT_RELATIVE,
        "6OA_RECONCILIATION_ARTIFACT",
    )
    expected_bytes, expected_digest, _ = subject._SIX_OA_RECONCILIATION_ARTIFACT_SPEC_V1
    if len(payload) != expected_bytes or _sha(payload) != expected_digest:
        raise ValueError("6OA_RECONCILIATION_ARTIFACT_BINDING_INVALID")
    queue = _read(root / subject.PRIORITY_QUEUE_RELATIVE, "FROZEN_PRIORITY_QUEUE")
    if len(queue) != 50116 or _sha(queue) != (
        "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2"
    ):
        raise ValueError("FROZEN_PRIORITY_QUEUE_BINDING_INVALID")


def independently_verify_delta_v1(
    predecessor_rows: Sequence[Mapping[str, str]],
    successor_rows: Sequence[Mapping[str, str]],
) -> dict[str, object]:
    if len(predecessor_rows) != 1000 or len(successor_rows) != 1000:
        raise ValueError("ROW_COUNT_NOT_EXACT1000")
    before = {row["canonical_event_id"]: row for row in predecessor_rows}
    after = {row["canonical_event_id"]: row for row in successor_rows}
    if set(before) != set(after):
        raise ValueError("EVENT_UNIVERSE_CHANGED")
    changed = {event for event in before if before[event] != after[event]}
    target = set(subject.SIX_OA_EXACT4_EVENT_IDS_V1)
    if changed != target:
        raise ValueError("CHANGED_EVENTS_NOT_6OA_EXACT4")
    field_sets = {
        event: {
            field for field in subject.CENSUS_COLUMNS_V1
            if before[event][field] != after[event][field]
        }
        for event in target
    }
    if any(fields != subject._ACTUAL_CHANGED_6OA_FIELDS_V1 for fields in field_sets.values()):
        raise ValueError("ACTUAL_CHANGED_FIELDS_NOT_EXACT16")
    if any(
        before[event] != after[event]
        for event in set(before) - target
    ):
        raise ValueError("NON_TARGET_ROW_CHANGED")
    expected_target = {
        "current_global_status": "COMPLETED_HUMAN_NEGATIVE",
        "current_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "human_review_completed": "true",
        "chemistry_disposition": "POSITIVE",
        "task_relevance_disposition": "NOT_RELEVANT",
        "training_use_disposition": "NOT_APPLICABLE",
        "training_materialization_allowed_current_source": "false",
        "reactive_pair_sample_authoritative": "true",
        "role_partition_sample_authoritative": "true",
        "role_profile": subject.base.DIRECT_PROFILE,
        "canonical_mask_structural_labels_available": "true",
        "structurally_applicable_task_ids_json": "[0,3,4]",
        "human_training_excluded": "false",
        "training_use_include": "false",
        "future_training_admission_candidate": "false",
        "formal_training_admitted": "false",
        "current_runtime_model_usable": "false",
    }
    if any(
        any(after[event][field] != value for field, value in expected_target.items())
        for event in target
    ):
        raise ValueError("6OA_EXACT4_PROJECTED_SEMANTICS_INVALID")
    return {
        "changed_event_count": len(changed),
        "unchanged_event_count": len(before) - len(changed),
        "actual_changed_fields": sorted(next(iter(field_sets.values()))),
    }


def independently_verify_counts_v1(rows: Sequence[Mapping[str, str]]) -> dict[str, object]:
    if len(rows) != 1000 or any(tuple(row) != subject.CENSUS_COLUMNS_V1 for row in rows):
        raise ValueError("CENSUS_SCHEMA_INVALID")
    expected = {
        "chemistry": Counter({"POSITIVE": 160, "NOT_ESTABLISHED": 90, "UNRESOLVED": 750}),
        "task": Counter({"RELEVANT": 141, "NOT_RELEVANT": 110, "UNRESOLVED": 749}),
        "training": Counter(
            {"INCLUDE": 68, "EXCLUDE_FROM_TRAINING_ONLY": 72, "NOT_APPLICABLE": 110, "UNRESOLVED": 750}
        ),
    }
    actual = {
        "chemistry": Counter(row["chemistry_disposition"] for row in rows),
        "task": Counter(row["task_relevance_disposition"] for row in rows),
        "training": Counter(row["training_use_disposition"] for row in rows),
    }
    if actual != expected:
        raise ValueError("GLOBAL_DISPOSITION_COUNTS_INVALID")
    global_status = Counter(row["current_global_status"] for row in rows)
    if global_status != Counter({
        "CURRENTLY_UNREVIEWED": 167,
        "CURRENTLY_IN_PROGRESS": 0,
        "COMPLETED_HUMAN_POSITIVE": 123,
        "COMPLETED_HUMAN_NEGATIVE": 78,
        "COMPLETED_PARTIAL_AUTHORITY": 1,
        "CURRENT_RUNTIME_MODEL_USABLE": 17,
        "PUBLISHED_EXACT_AUTO_NEGATIVE": 32,
        "LEAKAGE_EXISTING_GROUP_CONFLICT": 369,
        "STRUCTURAL_EVIDENCE_INCOMPLETE": 133,
        "QUARANTINE_REPRESENTATION_GAP": 78,
        "REJECTED_FEATURE_INCOMPATIBLE": 2,
    }):
        raise ValueError("GLOBAL_STATUS_COUNTS_INVALID")
    boolean_counts = {
        field: sum(row[field] == "true" for row in rows)
        for field in (
            "reactive_pair_sample_authoritative",
            "role_partition_sample_authoritative",
            "canonical_mask_structural_labels_available",
            "post_geometry_sample_authoritative",
            "post_geometry_source_evidence_available",
            "post_geometry_training_target_available",
            "pre_geometry_authoritative",
            "pre_geometry_training_target_available",
            "training_use_include",
            "future_training_admission_candidate",
            "formal_training_admitted",
            "current_runtime_model_usable",
            "human_training_excluded",
        )
    }
    if boolean_counts != {
        "reactive_pair_sample_authoritative": 160,
        "role_partition_sample_authoritative": 152,
        "canonical_mask_structural_labels_available": 152,
        "post_geometry_sample_authoritative": 21,
        "post_geometry_source_evidence_available": 867,
        "post_geometry_training_target_available": 17,
        "pre_geometry_authoritative": 0,
        "pre_geometry_training_target_available": 0,
        "training_use_include": 68,
        "future_training_admission_candidate": 51,
        "formal_training_admitted": 5,
        "current_runtime_model_usable": 17,
        "human_training_excluded": 72,
    }:
        raise ValueError("GLOBAL_AUTHORITY_COUNTS_INVALID")
    profiles = Counter(
        row["role_profile"] for row in rows
        if row["role_partition_sample_authoritative"] == "true"
    )
    if profiles != Counter({subject.base.DIRECT_PROFILE: 96, subject.base.STRICT_PROFILE: 56}):
        raise ValueError("ROLE_PROFILE_COUNTS_INVALID")
    applicability: Counter[int] = Counter()
    for row in rows:
        if row["role_partition_sample_authoritative"] == "true":
            applicability.update(json.loads(row["structurally_applicable_task_ids_json"]))
    if applicability != Counter({0: 152, 1: 56, 2: 56, 3: 152, 4: 152}):
        raise ValueError("EXACT5_APPLICABILITY_COUNTS_INVALID")
    orthogonal = {
        row["canonical_event_id"] for row in rows
        if (
            row["task_relevance_disposition"], row["chemistry_disposition"],
            row["training_use_disposition"],
        ) == ("NOT_RELEVANT", "POSITIVE", "NOT_APPLICABLE")
    }
    expected_orthogonal = (
        set(subject.GVE_EXACT4_EVENT_IDS_V1)
        | set(subject.LCY_EXACT4_EVENT_IDS_V1)
        | set(subject.ZERO_D8_EXACT4_EVENT_IDS_V1)
        | set(subject.TP2_EXACT4_EVENT_IDS_V1)
        | set(subject.SIX_OA_EXACT4_EVENT_IDS_V1)
    )
    if orthogonal != expected_orthogonal or len(orthogonal) != 20:
        raise ValueError("ORTHOGONAL_EXACT20_INVALID")
    return {**boolean_counts, "orthogonal_count": len(orthogonal)}


def independently_verify_6oa_publications_v1(
    root: Path, result, matrix: Sequence[Mapping[str, str]],
) -> dict[str, int]:
    target = set(subject.SIX_OA_EXACT4_EVENT_IDS_V1)
    facts = [fact for fact in result.normalized_facts if fact.canonical_event_id in target]
    matrix_rows = [row for row in matrix if row["canonical_event_id"] in target]
    predecessor_artifact = json.loads(
        _read(root / reconciliation.predecessor_owner.OUTPUT_RELATIVE, "NWJ_RECONCILIATION_ARTIFACT")
    )
    six_oa_artifact = json.loads(
        _read(
            root / subject.SIX_OA_RECONCILIATION_ARTIFACT_RELATIVE,
            "6OA_RECONCILIATION_ARTIFACT",
        )
    )
    changed_target = changed_non_target = 0
    for before, after in zip(
        predecessor_artifact["reconciled_rows"],
        six_oa_artifact["reconciled_rows"],
        strict=True,
    ):
        if before["canonical_event_id"] in target:
            changed_target += before != after
        else:
            changed_non_target += before != after
    generic_fields = set(reconciliation._GENERIC_FACT_FIELDS)
    expected_review = {
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
        len(result.source_bindings) != 26
        or len(result.normalized_facts) != 147
        or len(result.reconciled_rows) != 338
        or result.review_summary != expected_review
        or len(facts) != 4
        or any(
            fact.legacy_completed_review_status != "COMPLETED_HUMAN_NEGATIVE"
            or fact.task_relevance_disposition != "NOT_RELEVANT"
            or fact.chemistry_disposition != "POSITIVE"
            or fact.training_disposition != "NOT_APPLICABLE"
            or fact.human_training_excluded is not False
            for fact in facts
        )
        or len(matrix_rows) != 4
        or tuple(row["canonical_event_id"] for row in matrix_rows)
        != subject.SIX_OA_EXACT4_EVENT_IDS_V1
        or tuple(int(row["scaleup_rank"]) for row in matrix_rows)
        != subject.SIX_OA_EXACT4_RANKS_V1
        or (changed_target, changed_non_target) != (4, 0)
        or any(set(fact) != generic_fields for fact in six_oa_artifact["normalized_facts"])
        or any(len(row) != len(subject.ingestion.MATRIX_HEADER) for row in matrix_rows)
        or any(
            row["human_review_completed"] != "true"
            or row["source_formal_generation_domain_decision"] != "OUT_OF_DOMAIN"
            or row["normalized_task_relevance_disposition"] != "NOT_RELEVANT"
            or row["chemistry_disposition"] != "POSITIVE"
            or row["negative_chemistry"] != "false"
            or row["task_domain_negative"] != "true"
            or row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "C5"
            or row["pair_sample_authority"] != "true"
            or row["role_sample_authority"] != "true"
            or row["role_profile"] != subject.base.DIRECT_PROFILE
            or row["structurally_applicable_task_ids_json"] != "[0,3,4]"
            or row["B3_present"] != "true"
            or row["sixth_task"] != "false"
            or row["formal_event_training_use_decision"] != "NOT_APPLICABLE"
            or row["training_use_allowed"] != "false"
            or row["human_training_excluded"] != "false"
            or row["future_training_admission_candidate"] != "false"
            or row["task_label_authority"] != "false"
            or row["event_task_label_rows_materialized"] != "false"
            or row["mask_tensor_targets_created"] != "false"
            or row["formal_training_admitted"] != "false"
            or row["training_materialization_allowed"] != "false"
            or row["POST_source_evidence_available"] != "true"
            or row["POST_geometry_training_authority"] != "false"
            or row["POST_geometry_training_target_created"] != "false"
            or row["PRE_authority"] != "false"
            or row["READY_FOR_TRAINING"] != "false"
            or row["TRAINING_STARTED"] != "false"
            for row in matrix_rows
        )
        or [row["geometry_outlier"] for row in matrix_rows] != ["false", "false", "true", "false"]
    ):
        raise ValueError("6OA_MATRIX_RECONCILIATION_PUBLICATION_INVALID")
    return {
        "source_count": 26,
        "fact_count": 147,
        "reconciled_row_count": 338,
        "generic_fact_field_count": 11,
        "changed_target_rows": changed_target,
        "non_target_changed_rows": changed_non_target,
    }

def verify_manifest_v1(
    root: Path, manifest: Mapping[str, object], artifacts: Mapping[str, bytes],
) -> None:
    if manifest.get("candidate_inventory") != {
        "exact_file_count": 7, "paths": list(subject.EXACT7_PATHS_V1)
    }:
        raise ValueError("MANIFEST_EXACT7_INVALID")
    expected_contract = []
    for role, relative in (
        ("PRODUCTION_OWNER", subject.PRODUCTION_RELATIVE),
        ("CHECKER", subject.CHECKER_RELATIVE),
        ("TARGETED_TESTS", subject.TEST_RELATIVE),
        ("GUIDE", subject.GUIDE_RELATIVE),
    ):
        payload = _read(root / relative, role)
        expected_contract.append(
            {
                "artifact_role": role,
                "path": relative.as_posix(),
                "byte_count": len(payload),
                "sha256": _sha(payload),
            }
        )
    if manifest.get("candidate_contract_bindings") != expected_contract:
        raise ValueError("MANIFEST_DYNAMIC_CANDIDATE_BINDINGS_INVALID")
    if manifest.get("semantic_source_binding_count") != 186:
        raise ValueError("MANIFEST_BINDING_COUNT_INVALID")
    bindings = manifest.get("semantic_source_bindings")
    if type(bindings) is not list or len(bindings) != 186:
        raise ValueError("MANIFEST_BINDINGS_INVALID")
    if len({(item["path_namespace"], item["path"]) for item in bindings}) != 186:
        raise ValueError("MANIFEST_BINDING_IDENTITY_COLLISION")
    predecessor_roles = {item["artifact_role"] for item in bindings[:180]}
    additive_roles = [item["artifact_role"] for item in bindings[180:]]
    predecessor_manifest = json.loads(
        _read(root / subject.PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_MANIFEST")
    )
    if bindings[:180] != predecessor_manifest["semantic_source_bindings"]:
        raise ValueError("MANIFEST_PREDECESSOR_BINDING_PREFIX_CHANGED")
    if additive_roles != [item[0] for item in subject._ADDITIVE_SOURCE_SPECS_V1]:
        raise ValueError("MANIFEST_ADDITIVE_SOURCE_ROLES_INVALID")
    if len(additive_roles) != len(set(additive_roles)) or predecessor_roles & set(additive_roles):
        raise ValueError("MANIFEST_BINDING_ROLE_COLLISION")
    if _sha(_canonical_json(bindings).encode("utf-8")) != EXPECTED_BINDINGS_SHA256:
        raise ValueError("MANIFEST_BINDINGS_DIGEST_INVALID")
    output_bindings = manifest.get("output_bindings_excluding_manifest_self")
    if type(output_bindings) is not list or len(output_bindings) != 2:
        raise ValueError("MANIFEST_OUTPUT_BINDINGS_INVALID")
    for item in output_bindings:
        filename = Path(item["path"]).name
        if filename not in artifacts:
            raise ValueError("MANIFEST_OUTPUT_PATH_INVALID")
        payload = artifacts[filename]
        if item["byte_count"] != len(payload) or item["sha256"] != _sha(payload):
            raise ValueError("MANIFEST_OUTPUT_IDENTITY_INVALID")
    if manifest.get("manifest_self_SHA256_recorded") is not False:
        raise ValueError("MANIFEST_SELF_SHA_RECORDED")
    refresh = manifest.get("refresh_contract")
    if type(refresh) is not dict or any(
        refresh.get(key) != value
        for key, value in {
            "changed_event_count": 4,
            "unchanged_event_count": 996,
            "authorized_overlay_field_count": 19,
            "authorized_but_unchanged_field_count": 3,
            "actual_changed_field_count_per_6oa_row": 16,
            "semantic_source_binding_count": 186,
            "predecessor_semantic_source_binding_count": 180,
            "additive_semantic_source_binding_count": 6,
            "task_negative_chemistry_positive_population_count": 20,
            "queue_refreshed": False,
            "next_review_started": False,
            "pyr_review_state_created": False,
        }.items()
    ):
        raise ValueError("MANIFEST_REFRESH_CONTRACT_INVALID")
    if manifest.get("6oa_reconciliation_artifact_validation_binding") != {
        "artifact_role": "6OA_RECONCILIATION_ARTIFACT_VALIDATION_IDENTITY",
        "path": subject.SIX_OA_RECONCILIATION_ARTIFACT_RELATIVE.as_posix(),
        "path_namespace": "repository_relative",
        "byte_count": 344196,
        "sha256": "b050f0c49f4f7ce017b97051e80ac9bb4d2471198229ec4d79154486f29146e6",
        "expected_executable": False,
        "computational_source": False,
    }:
        raise ValueError("MANIFEST_6OA_RECONCILIATION_VALIDATION_BINDING_INVALID")
    lowered = artifacts[subject.MANIFEST_FILE].decode("utf-8").lower()
    for token in ('"timestamp"', '"hostname"', '"pid"', '"head"', '"ahead"', '"behind"'):
        if token in lowered:
            raise ValueError("MANIFEST_DYNAMIC_FIELD_PRESENT")


def independently_verify_next_pending_v1(
    root: Path, result, rows: Sequence[Mapping[str, str]],
) -> dict[str, object]:
    queue_payload = _read(root / subject.PRIORITY_QUEUE_RELATIVE, "FROZEN_PRIORITY_QUEUE")
    queue_reader = csv.DictReader(io.StringIO(queue_payload.decode("utf-8"), newline=""))
    queue = [dict(row) for row in queue_reader]
    if len(queue) != 131:
        raise ValueError("INDEPENDENT_PRIORITY_QUEUE_IDENTITY_INVALID")
    status_by_unit: dict[str, set[str]] = {}
    for row in result.reconciled_rows:
        status_by_unit.setdefault(row["raw_review_unit_id"], set()).add(row["current_review_status"])
    pending = []
    for row in queue:
        statuses = status_by_unit.get(row["review_unit_id"])
        if statuses is None or len(statuses) != 1:
            raise ValueError("INDEPENDENT_PENDING_STATUS_INVALID")
        status = next(iter(statuses))
        if status in {"CURRENTLY_UNREVIEWED", "CURRENTLY_IN_PROGRESS"}:
            pending.append((-int(row["event_count"]), int(row["priority_rank"]), row["review_unit_id"], row))
    pending.sort(key=lambda item: item[:3])
    if len(pending) != 101 or any(item[2] == subject.SIX_OA_REVIEW_UNIT_ID_V1 for item in pending):
        raise ValueError("INDEPENDENT_PENDING_SET_INVALID")
    _negative, raw_rank, unit, first = pending[0]
    census_by_event = {row["canonical_event_id"]: row for row in rows}
    if (
        raw_rank != 30
        or unit != subject.NEXT_PENDING_REVIEW_UNIT_ID_V1
        or int(first["event_count"]) != 4
        or json.loads(first["ligand_component_ids_json"]) != ["PYR"]
        or json.loads(first["pdb_ids_json"]) != ["1F8M"]
        or any(
            census_by_event[event]["current_review_status"] != "CURRENTLY_UNREVIEWED"
            for event in subject.NEXT_PENDING_EVENT_IDS_V1
        )
    ):
        raise ValueError("INDEPENDENT_NEXT_PENDING_PYR_INVALID")
    return {"review_unit_id": unit, "raw_priority_rank": raw_rank, "current_pending_rank": 1}


def _checker_fail(token: str) -> None:
    raise ValueError(subject.ERROR_TOKEN + ":" + token)


def _expect_tamper(name: str, expected_token: str, callable_) -> str:
    try:
        callable_()
    except ValueError as error:
        message = str(error)
        prefix = subject.ERROR_TOKEN + ":"
        if not message.startswith(prefix):
            raise ValueError("TAMPER_WRONG_ERROR_PREFIX:" + name) from error
        actual_token = message[len(prefix):].split(":", 1)[0]
        if actual_token != expected_token:
            raise ValueError(
                f"TAMPER_WRONG_SEMANTIC_TOKEN:{name}:{actual_token}:{expected_token}"
            ) from error
        return actual_token
    raise ValueError("TAMPER_ACCEPTED:" + name)


def check_semantic_probes_v1(
    root: Path, computation, frozen, result, matrix: Sequence[Mapping[str, str]],
) -> dict[str, str]:
    target = subject.SIX_OA_EXACT4_EVENT_IDS_V1[0]

    def mutate_row(event_id: str, **changes: str):
        rows = deepcopy(list(computation.rows))
        next(row for row in rows if row["canonical_event_id"] == event_id).update(changes)
        return replace(computation, rows=tuple(rows))

    def validate(candidate) -> None:
        subject.validate_covapie_cumulative1000_current_global_readiness_census_with_6oa_v1(
            candidate,
            repo_root=root,
            predecessor_computation=frozen,
            reconciliation_result=result,
            matrix_rows=matrix,
        )

    probes: dict[str, str] = {}
    row_probes = (
        ("wrong_6oa_event", target, {"canonical_event_id": target + ":TAMPER"}, "CENSUS_EVENT_SET_IDENTITY_INVALID"),
        ("duplicate_6oa_event", target, {"canonical_event_id": subject.SIX_OA_EXACT4_EVENT_IDS_V1[1]}, "CENSUS_EVENT_ID_EMPTY_OR_DUPLICATE"),
        ("fifth_non_6oa_row_changed", subject.LCY_EXACT4_EVENT_IDS_V1[0], {"current_review_status": "CURRENTLY_IN_PROGRESS"}, "PREDECESSOR_DELTA_NOT_EXACT_6OA_EXACT4"),
        ("6oa_stays_unreviewed", target, {"current_global_status": "CURRENTLY_UNREVIEWED", "current_review_status": "CURRENTLY_UNREVIEWED"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("6oa_becomes_human_positive", target, {"current_global_status": "COMPLETED_HUMAN_POSITIVE", "current_review_status": "COMPLETED_HUMAN_POSITIVE"}, "6OA_REFRESHED_SEMANTICS_INVALID"),
        ("chemistry_not_positive", target, {"chemistry_disposition": "NEGATIVE"}, "6OA_REFRESHED_SEMANTICS_INVALID"),
        ("task_not_not_relevant", target, {"task_relevance_disposition": "RELEVANT"}, "6OA_REFRESHED_SEMANTICS_INVALID"),
        ("training_not_not_applicable", target, {"training_use_disposition": "INCLUDE"}, "6OA_REFRESHED_SEMANTICS_INVALID"),
        ("human_training_excluded_true", target, {"human_training_excluded": "true"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("future_training_candidate_true", target, {"future_training_admission_candidate": "true"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("training_use_include_true", target, {"training_use_include": "true"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("pair_authority_false", target, {"reactive_pair_sample_authoritative": "false"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("role_authority_false", target, {"role_partition_sample_authoritative": "false"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("wrong_role_profile", target, {"role_profile": subject.base.STRICT_PROFILE}, "6OA_REFRESHED_SEMANTICS_INVALID"),
        ("wrong_task_ids", target, {"structurally_applicable_task_ids_json": "[0,1,2,3,4]"}, "6OA_REFRESHED_SEMANTICS_INVALID"),
        ("post_geometry_sample_authority_forged", target, {"post_geometry_sample_authoritative": "true"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("post_training_target_forged", target, {"post_geometry_training_target_available": "true"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("pre_authority_forged", target, {"pre_geometry_authoritative": "true"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("pre_training_target_forged", target, {"pre_geometry_training_target_available": "true"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("formal_training_admitted", target, {"formal_training_admitted": "true"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
        ("runtime_model_usable", target, {"current_runtime_model_usable": "true"}, "6OA_CHANGED_FIELD_SET_NOT_EXACT16"),
    )
    for name, event_id, changes, expected in row_probes:
        probes[name] = _expect_tamper(
            name,
            expected,
            lambda event_id=event_id, changes=changes: validate(
                mutate_row(event_id, **changes)
            ),
        )

    def matrix_probe(name: str, expected: str, changes: Mapping[str, str]) -> None:
        tampered = deepcopy(list(matrix))
        tampered[0].update(changes)
        probes[name] = _expect_tamper(
            name, expected, lambda: subject._validate_6oa_matrix_rows_v1(tampered)
        )

    matrix_probe("matrix_wrong_event", "6OA_EVENT_MATRIX_IDENTITY_NOT_EXACT4", {"canonical_event_id": target + ":TAMPER"})
    probes["matrix_missing_event"] = _expect_tamper(
        "matrix_missing_event",
        "6OA_EVENT_MATRIX_IDENTITY_NOT_EXACT4",
        lambda: subject._validate_6oa_matrix_rows_v1(matrix[:-1]),
    )
    duplicate_matrix = deepcopy(list(matrix))
    duplicate_matrix[-1] = deepcopy(duplicate_matrix[0])
    probes["matrix_duplicate_event"] = _expect_tamper(
        "matrix_duplicate_event",
        "6OA_EVENT_MATRIX_IDENTITY_NOT_EXACT4",
        lambda: subject._validate_6oa_matrix_rows_v1(duplicate_matrix),
    )
    matrix_probe("matrix_out_of_domain_changed", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"source_formal_generation_domain_decision": "IN_DOMAIN"})
    matrix_probe("matrix_normalization_changed", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"normalized_task_relevance_disposition": "RELEVANT"})
    matrix_probe("matrix_chemistry_negative", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"chemistry_disposition": "NEGATIVE"})
    matrix_probe("matrix_pair_false", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"pair_sample_authority": "false"})
    matrix_probe("matrix_role_false", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"role_sample_authority": "false"})
    matrix_probe("matrix_wrong_profile", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"role_profile": subject.base.STRICT_PROFILE})
    matrix_probe("matrix_wrong_task_ids", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"structurally_applicable_task_ids_json": "[0,4]"})
    matrix_probe("matrix_B3_missing", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"B3_present": "false"})
    matrix_probe("matrix_sixth_task", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"sixth_task": "true"})
    matrix_probe("matrix_post_authority_forged", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"POST_geometry_training_authority": "true"})
    matrix_probe("matrix_post_target_forged", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"POST_geometry_training_target_created": "true"})
    matrix_probe("matrix_PRE_authority_forged", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"PRE_authority": "true"})
    matrix_probe("task_label_authority_true", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"task_label_authority": "true"})
    matrix_probe("event_task_labels_materialized", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"event_task_label_rows_materialized": "true"})
    matrix_probe("mask_tensor_target_created", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"mask_tensor_targets_created": "true"})
    matrix_probe("training_materialization_allowed", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"training_materialization_allowed": "true"})
    matrix_probe("ready_for_training_true", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"READY_FOR_TRAINING": "true"})
    matrix_probe("training_started_true", "6OA_EVENT_MATRIX_SEMANTICS_INVALID", {"TRAINING_STARTED": "true"})

    summary_probes = (
        ("global_negative_not_plus4", ("global_status_distribution", "counts", "COMPLETED_HUMAN_NEGATIVE"), 77),
        ("global_unreviewed_not_minus4", ("global_status_distribution", "counts", "CURRENTLY_UNREVIEWED"), 168),
        ("human_negative_events_not_plus4", ("human_review", "completed_negative_event_count"), 47),
        ("chemistry_positive_not_plus4", ("chemistry", "POSITIVE", "count"), 159),
        ("task_not_relevant_not_plus4", ("task_relevance", "NOT_RELEVANT", "count"), 109),
        ("not_applicable_not_plus4", ("training_use", "NOT_APPLICABLE", "count"), 109),
        ("pair_count_not160", ("reactive_pair", "sample_level_authoritative_pair_count"), 159),
        ("role_count_not152", ("role", "role_partition_sample_authoritative_count"), 151),
    )
    for name, path, value in summary_probes:
        candidate = deepcopy(computation.summary)
        cursor = candidate
        for key in path[:-1]:
            cursor = cursor[key]
        cursor[path[-1]] = value
        probes[name] = _expect_tamper(
            name,
            "SUMMARY_NOT_EXACTLY_SOURCE_DERIVED",
            lambda candidate=candidate: validate(replace(computation, summary=candidate)),
        )

    candidate = deepcopy(computation.summary)
    orthogonal = candidate["orthogonal_task_negative_chemistry_positive"]
    orthogonal.pop(
        "task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_plus_6oa_exact20"
    )
    orthogonal["task_negative_chemistry_positive_population_exactly_gve_plus_lcy_plus_0d8_plus_tp2_exact16"] = True
    probes["stale_exact16_marker"] = _expect_tamper(
        "stale_exact16_marker",
        "SUMMARY_NOT_EXACTLY_SOURCE_DERIVED",
        lambda: validate(replace(computation, summary=candidate)),
    )
    for name, field, value in (
        ("next_pending_stays_6oa", "review_unit_id", subject.SIX_OA_REVIEW_UNIT_ID_V1),
        ("next_pending_skips_pyr", "review_unit_id", "COVAPIE_BULK_REVIEW_UNIT_FAKE"),
        ("wrong_pyr_raw_rank", "raw_priority_rank", 29),
    ):
        candidate = deepcopy(computation.summary)
        candidate["top_pending_review_units_by_event_yield"][0][field] = value
        probes[name] = _expect_tamper(
            name,
            "SUMMARY_NOT_EXACTLY_SOURCE_DERIVED",
            lambda candidate=candidate: validate(replace(computation, summary=candidate)),
        )
    for name, key in (
        ("next_review_started", "NEXT_REVIEW_STARTED"),
        ("queue_refresh_performed", "QUEUE_REFRESH_PERFORMED"),
        ("ready_for_training_boundary", "READY_FOR_TRAINING"),
        ("training_started_boundary", "TRAINING_STARTED"),
    ):
        candidate = deepcopy(computation.summary)
        candidate["authority_boundary"][key] = True
        probes[name] = _expect_tamper(
            name,
            "SUMMARY_NOT_EXACTLY_SOURCE_DERIVED",
            lambda candidate=candidate: validate(replace(computation, summary=candidate)),
        )

    bindings = list(deepcopy(computation.semantic_source_bindings))
    bindings[0]["sha256"] = "0" * 64
    probes["predecessor_binding_modified"] = _expect_tamper(
        "predecessor_binding_modified",
        "SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6",
        lambda: validate(replace(computation, semantic_source_bindings=tuple(bindings))),
    )
    bindings = list(deepcopy(computation.semantic_source_bindings))
    bindings[-1]["path"] = bindings[-2]["path"]
    probes["additive_source_duplicate"] = _expect_tamper(
        "additive_source_duplicate",
        "SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6",
        lambda: validate(replace(computation, semantic_source_bindings=tuple(bindings))),
    )
    bindings = list(deepcopy(computation.semantic_source_bindings[:-1]))
    probes["semantic_source_count_not186"] = _expect_tamper(
        "semantic_source_count_not186",
        "SEMANTIC_SOURCE_BINDING_SET_NOT_PREDECESSOR_PLUS_EXACT6",
        lambda: validate(replace(computation, semantic_source_bindings=tuple(bindings))),
    )
    matrix_payload = _read(root / subject.SIX_OA_EVENT_MATRIX_RELATIVE, "6OA_MATRIX")
    corrupted_matrix = bytearray(matrix_payload)
    corrupted_matrix[-2] ^= 1
    probes["matrix_drift"] = _expect_tamper(
        "matrix_drift",
        "6OA_EVENT_MATRIX_BINDING_INVALID",
        lambda: _verify_frozen_payload_identity_v1(
            bytes(corrupted_matrix),
            byte_count=9391,
            digest="1b74de80ea1cd1c9e030c9602a3b8925b523e826b67db9e21d07d2e7f856fcfa",
            token="6OA_EVENT_MATRIX_BINDING_INVALID",
        ),
    )
    reconciliation_payload = _read(
        root / subject.SIX_OA_RECONCILIATION_ARTIFACT_RELATIVE,
        "6OA_RECONCILIATION",
    )
    corrupted_reconciliation = bytearray(reconciliation_payload)
    corrupted_reconciliation[-2] ^= 1
    probes["reconciliation_artifact_drift"] = _expect_tamper(
        "reconciliation_artifact_drift",
        "6OA_RECONCILIATION_ARTIFACT_BINDING_INVALID",
        lambda: _verify_frozen_payload_identity_v1(
            bytes(corrupted_reconciliation),
            byte_count=344196,
            digest="b050f0c49f4f7ce017b97051e80ac9bb4d2471198229ec4d79154486f29146e6",
            token="6OA_RECONCILIATION_ARTIFACT_BINDING_INVALID",
        ),
    )
    probes["unexpected_eighth_file"] = _expect_tamper(
        "unexpected_eighth_file",
        "OUTPUT_DIRECTORY_NOT_EXACT3",
        lambda: _validate_output_inventory_names_v1(
            (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE, "debug.json")
        ),
    )
    fake_hash = "0" * 40
    exact = list(subject.EXACT7_PATHS_V1)
    good_index = [f"100644 {fake_hash} 0 {path}" for path in exact]
    for name, expected, lines in (
        ("tracked_git_mode_100755", "TRACKED_GIT_INDEX_MODE_INVALID", [good_index[0].replace("100644", "100755", 1), *good_index[1:]]),
        ("tracked_git_mode_120000", "TRACKED_GIT_INDEX_MODE_INVALID", [good_index[0].replace("100644", "120000", 1), *good_index[1:]]),
        ("non_zero_index_stage", "TRACKED_GIT_INDEX_STAGE_NOT_ZERO", [good_index[0].replace(" 0 ", " 1 ", 1), *good_index[1:]]),
        ("missing_index_path", "TRACKED_GIT_INDEX_PATH_SET_INVALID", good_index[:-1]),
        ("duplicate_index_path", "TRACKED_GIT_INDEX_PATH_DUPLICATE", [*good_index, good_index[0]]),
    ):
        probes[name] = _expect_tamper(
            name, expected, lambda lines=lines: _parse_git_index_entries_v1(lines, exact)
        )
    return probes

def _probe_materialized_raw_byte_rejection_v1(
    built_once: Mapping[str, bytes],
) -> str:
    observed = dict(built_once)
    original = observed[subject.CENSUS_FILE]
    corrupted = bytearray(original)
    corrupted[-2] ^= 1
    observed[subject.CENSUS_FILE] = bytes(corrupted)
    if observed[subject.CENSUS_FILE] == original:
        raise ValueError("RAW_BYTE_PROBE_MUTATION_NOT_APPLIED")
    return _expect_tamper(
        "raw_byte_corruption",
        "MATERIALIZED_OUTPUT_NOT_SOURCE_DERIVED",
        lambda: _verify_materialized_output_bytes_v1(built_once, observed),
    )


def _expect_failure(callable_) -> None:
    try:
        callable_()
    except ValueError:
        return
    raise ValueError("EXPECTED_VALUE_ERROR_NOT_RAISED")


def _parse_git_index_entries_v1(
    lines: Sequence[str], expected_paths: Sequence[str],
) -> list[dict[str, str]]:
    parsed: list[dict[str, str]] = []
    for line in lines:
        fields = line.split(maxsplit=3)
        if len(fields) != 4:
            _checker_fail("TRACKED_GIT_INDEX_RECORD_INVALID")
        mode, object_id, stage, path = fields
        if mode != "100644":
            _checker_fail("TRACKED_GIT_INDEX_MODE_INVALID")
        if stage != "0":
            _checker_fail("TRACKED_GIT_INDEX_STAGE_NOT_ZERO")
        parsed.append({"mode": mode, "object_id": object_id, "stage": stage, "path": path})
    observed = [item["path"] for item in parsed]
    if len(observed) != len(set(observed)):
        _checker_fail("TRACKED_GIT_INDEX_PATH_DUPLICATE")
    if sorted(observed) != sorted(expected_paths):
        _checker_fail("TRACKED_GIT_INDEX_PATH_SET_INVALID")
    return parsed


def _git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ("git", *args), cwd=root, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return [line for line in result.stdout.splitlines() if line]


def _classify_exact7_artifact_placement_v1(
    tracked: Sequence[str], untracked: Sequence[str],
) -> str:
    expected = set(subject.EXACT7_PATHS_V1)
    if not tracked and set(untracked) == expected and len(untracked) == 7:
        return "CANDIDATE_UNTRACKED"
    if set(tracked) == expected and len(tracked) == 7 and not untracked:
        return "TRACKED_CLEAN"
    raise ValueError("EXACT7_ARTIFACT_PLACEMENT_INVALID")


def _validate_history_scope_v1(changed_since_baseline: Sequence[str]) -> None:
    protected = sorted(
        path for path in changed_since_baseline
        if path in PROTECTED_FILES or path.startswith(PROTECTED_PREFIXES)
    )
    forbidden = sorted(
        path for path in changed_since_baseline
        if path.lower().endswith(FORBIDDEN_SUFFIXES)
    )
    if protected:
        raise ValueError("PROTECTED_HISTORY_PATH:" + protected[0])
    if forbidden:
        raise ValueError("FORBIDDEN_HISTORY_SUFFIX:" + forbidden[0])


def _classify_repository_lifecycle_v1(
    *, branch: str, placement: str, head: str, origin: str, ahead: int, behind: int,
    baseline_is_ancestor_of_head: bool, baseline_is_ancestor_of_origin: bool,
    origin_is_ancestor_of_head: bool, baseline_to_head_changed_paths: Sequence[str],
    tracked_modification_count: int = 0, staged_count: int = 0,
) -> str:
    expected = set(subject.EXACT7_PATHS_V1)
    changed = set(baseline_to_head_changed_paths)
    if branch != "main":
        raise ValueError("BRANCH_NOT_MAIN")
    if tracked_modification_count != 0 or staged_count != 0:
        raise ValueError("DIRTY_TRACKED_OR_STAGED_LIFECYCLE_INVALID")
    if placement == "CANDIDATE_UNTRACKED":
        if not (
            head == origin == BASELINE_COMMIT and ahead == behind == 0
            and baseline_is_ancestor_of_head and baseline_is_ancestor_of_origin
            and origin_is_ancestor_of_head and not changed
        ):
            raise ValueError("CANDIDATE_UNTRACKED_LIFECYCLE_INVALID")
        return placement
    if placement != "TRACKED_CLEAN":
        raise ValueError("LIFECYCLE_PLACEMENT_INVALID")
    _validate_history_scope_v1(tuple(changed))
    if (
        head == BASELINE_COMMIT or behind != 0 or ahead < 0
        or not baseline_is_ancestor_of_head or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head or not expected <= changed
    ):
        raise ValueError("TRACKED_CLEAN_LIFECYCLE_INVALID")
    if (ahead == 0) != (origin == head):
        raise ValueError("TRACKED_CLEAN_ORIGIN_RELATION_INVALID")
    return placement


def check_lifecycle_simulations_v1() -> dict[str, bool]:
    expected = list(subject.EXACT7_PATHS_V1)
    candidate = dict(
        branch="main", placement="CANDIDATE_UNTRACKED",
        head=BASELINE_COMMIT, origin=BASELINE_COMMIT,
        ahead=0, behind=0, baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True, origin_is_ancestor_of_head=True,
        baseline_to_head_changed_paths=[],
    )
    if _classify_repository_lifecycle_v1(**candidate) != "CANDIDATE_UNTRACKED":
        raise ValueError("CANDIDATE_SIMULATION_FAILED")
    tracked = dict(
        branch="main", placement="TRACKED_CLEAN",
        head="successor-head", origin=BASELINE_COMMIT,
        ahead=1, behind=0, baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True, origin_is_ancestor_of_head=True,
        baseline_to_head_changed_paths=expected,
    )
    if _classify_repository_lifecycle_v1(**tracked) != "TRACKED_CLEAN":
        raise ValueError("COMMITTED_UNPUSHED_SIMULATION_FAILED")
    pushed = {**tracked, "origin": "successor-head", "ahead": 0}
    _classify_repository_lifecycle_v1(**pushed)
    descendant = {**pushed, "head": "later-head", "origin": "later-head"}
    _classify_repository_lifecycle_v1(**descendant)
    invalid = (
        {"branch": "feature/test"},
        {"behind": 1},
        {"tracked_modification_count": 1},
        {"staged_count": 1},
        {"baseline_is_ancestor_of_head": False},
        {"baseline_is_ancestor_of_origin": False},
        {"origin_is_ancestor_of_head": False},
        {"baseline_to_head_changed_paths": expected[:-1]},
        {"head": "impossible-head", "origin": "other-head", "ahead": 0},
    )
    for update in invalid:
        _expect_failure(lambda update=update: _classify_repository_lifecycle_v1(**{**tracked, **update}))
    _expect_failure(lambda: _classify_exact7_artifact_placement_v1(expected[:3], expected[3:]))
    _expect_failure(lambda: _validate_history_scope_v1((*expected, "data/raw/tamper.cif")))
    _expect_failure(lambda: _validate_history_scope_v1((*expected, "artifacts/tamper.ckpt")))
    return {
        "branch_main_accepted": True,
        "branch_non_main_rejected": True,
        "candidate_untracked": True,
        "committed_unpushed": True,
        "pushed_successor": True,
        "later_clean_descendant": True,
        "mixed_tracking_rejected": True,
        "behind_rejected": True,
        "ancestry_failures_rejected": True,
        "missing_publication_history_rejected": True,
        "protected_history_rejected": True,
        "forbidden_history_rejected": True,
        "origin_relation_inconsistency_rejected": True,
    }


def _is_ancestor(root: Path, older: str, newer: str) -> bool:
    return subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer), cwd=root,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def verify_git_safety_v1(root: Path) -> dict[str, object]:
    tracked = _git(root, "ls-files", "--", *subject.EXACT7_PATHS_V1)
    tracked_stage = _git(root, "ls-files", "-s", "--", *subject.EXACT7_PATHS_V1)
    index_entries: list[dict[str, str]] = []
    if tracked:
        index_entries = _parse_git_index_entries_v1(
            tracked_stage, subject.EXACT7_PATHS_V1
        )
    all_untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    expected = set(subject.EXACT7_PATHS_V1)
    exact_untracked = [path for path in all_untracked if path in expected]
    placement = _classify_exact7_artifact_placement_v1(tracked, exact_untracked)
    if set(all_untracked) != set(exact_untracked):
        raise ValueError("ORDINARY_UNTRACKED_NOT_EXACT7")
    modified = _git(root, "diff", "--name-only")
    staged = _git(root, "diff", "--cached", "--name-only")
    if modified or staged:
        raise ValueError("TRACKED_OR_STAGED_DIRTY")
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")[0]
    head = _git(root, "rev-parse", "HEAD")[0]
    origin = _git(root, "rev-parse", "origin/main")[0]
    ahead, behind = map(int, _git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main")[0].split())
    changed = _git(root, "diff", "--name-only", BASELINE_COMMIT + "..HEAD")
    lifecycle = _classify_repository_lifecycle_v1(
        branch=branch, placement=placement, head=head, origin=origin,
        ahead=ahead, behind=behind,
        baseline_is_ancestor_of_head=_is_ancestor(root, BASELINE_COMMIT, "HEAD"),
        baseline_is_ancestor_of_origin=_is_ancestor(root, BASELINE_COMMIT, "origin/main"),
        origin_is_ancestor_of_head=_is_ancestor(root, "origin/main", "HEAD"),
        baseline_to_head_changed_paths=changed,
        tracked_modification_count=len(modified), staged_count=len(staged),
    )
    if any(path.endswith(FORBIDDEN_SUFFIXES) for path in all_untracked):
        raise ValueError("FORBIDDEN_UNTRACKED_SUFFIX")
    if any(
        path in PROTECTED_FILES or path.startswith(PROTECTED_PREFIXES)
        for path in (*modified, *staged, *all_untracked)
    ):
        raise ValueError("PROTECTED_SOURCE_DIRTY")
    tmp_part = [
        path for path in _git(root, "ls-files", "--others", "--exclude-standard")
        if path.endswith((".tmp", ".part"))
    ]
    if tmp_part:
        raise ValueError("TMP_OR_PART_PRESENT")
    return {
        "lifecycle": lifecycle,
        "tracked_modification_count": 0,
        "staged_count": 0,
        "ordinary_untracked_count": len(all_untracked),
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "forbidden_file_count": 0,
        "protected_source_diff_count": 0,
        "tmp_part_count": 0,
        "git_index_mode_checked": bool(tracked),
        "expected_git_publication_mode": "100644",
        "git_index_entries": index_entries,
    }


def run_check_v1(root: Path = ROOT) -> dict[str, object]:
    records = verify_exact7_inventory_v1(root)
    verify_frozen_bindings_v1(root)
    computation, frozen, result, matrix = subject._compute_components_v1(root)
    built_once = subject._build_artifacts_from_computation_v1(root, computation)
    built_twice = subject._build_artifacts_from_computation_v1(root, computation)
    if built_once != built_twice:
        raise ValueError("DOUBLE_BUILD_NOT_BYTE_IDENTICAL")
    materialized = {
        name: _read(root / subject.OUTPUT_DIRECTORY_RELATIVE / name, name)
        for name in (subject.CENSUS_FILE, subject.SUMMARY_FILE, subject.MANIFEST_FILE)
    }
    _verify_materialized_output_bytes_v1(built_once, materialized)
    if _sha(materialized[subject.CENSUS_FILE]) != EXPECTED_CENSUS_SHA256:
        raise ValueError("CENSUS_DIGEST_INVALID")
    if _sha(materialized[subject.SUMMARY_FILE]) != EXPECTED_SUMMARY_SHA256:
        raise ValueError("SUMMARY_DIGEST_INVALID")
    predecessor_rows = _parse_csv(
        _read(root / subject.PREDECESSOR_CENSUS_RELATIVE, "PREDECESSOR_CENSUS"),
        subject.CENSUS_COLUMNS_V1,
    )
    rows = _parse_csv(materialized[subject.CENSUS_FILE], subject.CENSUS_COLUMNS_V1)
    delta = independently_verify_delta_v1(predecessor_rows, rows)
    counts = independently_verify_counts_v1(rows)
    summary = json.loads(materialized[subject.SUMMARY_FILE])
    manifest = json.loads(materialized[subject.MANIFEST_FILE])
    if summary != computation.summary:
        raise ValueError("SUMMARY_NOT_COMPUTATION_EXACT")
    verify_manifest_v1(root, manifest, materialized)
    predecessor_manifest = json.loads(
        _read(root / subject.PREDECESSOR_MANIFEST_RELATIVE, "PREDECESSOR_MANIFEST")
    )
    if tuple(predecessor_manifest["semantic_source_bindings"]) != frozen.semantic_source_bindings:
        raise ValueError("PREDECESSOR_BINDING_PREFIX_NOT_MANIFEST_EXACT")
    publication = independently_verify_6oa_publications_v1(root, result, matrix)
    next_pending = independently_verify_next_pending_v1(root, result, rows)
    probes = check_semantic_probes_v1(root, computation, frozen, result, matrix)
    probes["raw_output_bytes"] = _probe_materialized_raw_byte_rejection_v1(built_once)
    lifecycle_simulations = check_lifecycle_simulations_v1()
    git = verify_git_safety_v1(root)
    boundary = summary["authority_boundary"]
    required_false = (
        "NEXT_REVIEW_STARTED", "QUEUE_REFRESH", "QUEUE_REFRESH_PERFORMED",
        "PYR_REVIEW_STATE_CREATED", "READY_FOR_TRAINING",
        "READY_FOR_FORMAL_TRAINING", "TRAINING_STARTED",
        "new_human_authority_created", "new_scientific_authority_created",
        "new_pair_authority_created", "new_role_authority_created",
        "TASK_LABEL_AUTHORITY", "EVENT_TASK_LABEL_ROWS_MATERIALIZED",
        "MASK_TENSOR_TARGETS_CREATED", "FORMAL_TRAINING_ADMITTED",
        "TRAINING_ADMISSION_CREATED", "TRAINING_MATERIALIZATION_ALLOWED",
        "PARAMETER_UPDATE_AUTHORIZATION", "FEATURE_SEMANTICS_AUDIT_PERFORMED",
    )
    if any(boundary[key] is not False for key in required_false):
        raise ValueError("AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    if (
        boundary["FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER"] is not True
        or boundary["FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING"] is not True
        or boundary["CENSUS_REFRESH_PERFORMED"] is not True
        or boundary["6OA_RECONCILIATION_CONSUMED"] is not True
        or boundary["STEP12D_STATUS"]
        != "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT"
    ):
        raise ValueError("FEATURE_SEMANTICS_AUDIT_WARNING_MISSING")
    return {
        "records": records,
        "delta": delta,
        "counts": counts,
        "6oa_publication": publication,
        "next_pending": next_pending,
        "semantic_probes": probes,
        "lifecycle_simulations": lifecycle_simulations,
        "git": git,
        "deterministic_double_build": True,
    }


def main() -> int:
    result = run_check_v1()
    print("COVAPIE_CUMULATIVE1000_CURRENT_GLOBAL_READINESS_CENSUS_WITH_6OA_V1_PASS=true")
    print("CENSUS_ROWS=1000")
    print("CENSUS_COLUMNS=47")
    print("6OA_OVERLAY_EVENT_COUNT=4")
    print("NON_6OA_CHANGED_ROW_COUNT=0")
    print("UNCHANGED_ROW_COUNT=996")
    print("AUTHORIZED_OVERLAY_FIELD_COUNT=19")
    print("AUTHORIZED_BUT_UNCHANGED_FIELD_COUNT=3")
    print("ACTUAL_CHANGED_FIELD_COUNT=16")
    print("CURRENTLY_UNREVIEWED=167")
    print("COMPLETED_HUMAN_NEGATIVE=78")
    print("COMPLETED_HUMAN_POSITIVE=123")
    print("HUMAN_COMPLETED_EVENT_COUNT=171")
    print("HUMAN_COMPLETED_UNIT_COUNT=30")
    print("HUMAN_COMPLETED_NEGATIVE_EVENT_COUNT=48")
    print("HUMAN_COMPLETED_NEGATIVE_UNIT_COUNT=10")
    print("CHEMISTRY_POSITIVE_COUNT=160")
    print("TASK_NOT_RELEVANT_COUNT=110")
    print("TRAINING_NOT_APPLICABLE_COUNT=110")
    print("REACTIVE_PAIR_SAMPLE_AUTHORITATIVE_COUNT=160")
    print("ROLE_PARTITION_SAMPLE_AUTHORITATIVE_COUNT=152")
    print("CANONICAL_MASK_STRUCTURAL_LABELS_AVAILABLE_COUNT=152")
    print("STRICT_PROFILE_COUNT=56")
    print("DIRECT_PROFILE_COUNT=96")
    print("CANONICAL_TASK_APPLICABILITY_COUNTS=[152,56,56,152,152]")
    print("ORTHOGONAL_TASK_NEGATIVE_CHEMISTRY_POSITIVE_COUNT=20")
    print("CANONICAL_EXACT5=true")
    print("B3_PRESENT=true")
    print("SIXTH_TASK=false")
    print("NEXT_PRIORITY_REVIEW_LIGAND=PYR")
    print("NEXT_PRIORITY_REVIEW_PDB=1F8M")
    print("NEXT_PRIORITY_REVIEW_RAW_PRIORITY_RANK=30")
    print("NEXT_PRIORITY_REVIEW_CURRENT_PENDING_RANK=1")
    print("NEXT_REVIEW_STARTED=false")
    print("NEXT_PRIORITY_REVIEW_UNIT=COVAPIE_BULK_REVIEW_UNIT_EB7468B0711B37A4")
    print("PREDECESSOR_SEMANTIC_SOURCE_BINDING_COUNT=180")
    print("SUCCESSOR_SEMANTIC_SOURCE_BINDING_COUNT=186")
    print("CENSUS_REFRESH_PERFORMED=true")
    print("QUEUE_REFRESH_PERFORMED=false")
    print("PYR_REVIEW_STATE_CREATED=false")
    print("TASK_LABEL_AUTHORITY=false")
    print("FORMAL_TRAINING_ADMITTED=false")
    print("TRAINING_STARTED=false")
    print("READY_FOR_TRAINING=false")
    print("READY_FOR_FORMAL_TRAINING=false")
    print("FEATURE_SEMANTICS_AUDIT_PERFORMED=false")
    print("FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING=true")
    print("GIT_INDEX_MODE_CHECKED=" + str(result["git"]["git_index_mode_checked"]).lower())
    print("LIFECYCLE=" + str(result["git"]["lifecycle"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
